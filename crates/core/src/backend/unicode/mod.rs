//! Python3.11/Unicode14 text semantics for persisted document anchors.
use std::{collections::HashMap, sync::LazyLock};
use unicode_general_category::{get_general_category, GeneralCategory as C};

pub fn python_decimal(ch: char) -> bool {
    get_general_category(ch) == C::DecimalNumber
}

/// Numeric value of a Unicode14 decimal digit (Python's decimal input class).
pub fn decimal_value(ch: char) -> Option<u8> {
    if !python_decimal(ch) {
        return None;
    }
    let mut start = ch as u32;
    while start > 0 && char::from_u32(start - 1).is_some_and(python_decimal) {
        start -= 1;
    }
    Some(((ch as u32 - start) % 10) as u8)
}
/// Parse decimal digits without a sign or whitespace, within SQLite's ID range.
pub fn decimal_integer(value: &str) -> Option<i64> {
    if value.is_empty() {
        return None;
    }
    value.chars().try_fold(0_i64, |value, ch| {
        value
            .checked_mul(10)?
            .checked_add(i64::from(decimal_value(ch)?))
    })
}
/// Python3.11 int(string, 10), including Unicode14 digits and separators.
/// The return is canonical text so callers retain arbitrary integer width.
pub fn integer_literal(value: &str) -> Option<String> {
    let raw = value.trim_matches(char::is_whitespace);
    let negative = raw.starts_with('-');
    let raw = raw
        .strip_prefix('+')
        .or_else(|| raw.strip_prefix('-'))
        .unwrap_or(raw);
    if raw.is_empty() {
        return None;
    }
    let mut digits = String::new();
    if negative {
        digits.push('-');
    }
    let mut count = 0;
    let mut previous = false;
    for ch in raw.chars() {
        if ch == '_' {
            if !previous {
                return None;
            }
            previous = false;
        } else {
            digits.push(char::from(b'0' + decimal_value(ch)?));
            count += 1;
            if count > 4300 {
                return None;
            }
            previous = true;
        }
    }
    if !previous {
        return None;
    }
    num_bigint::BigInt::parse_bytes(digits.as_bytes(), 10).map(|number| number.to_string())
}

pub fn python_alnum(ch: char) -> bool {
    matches!(
        get_general_category(ch),
        C::UppercaseLetter
            | C::LowercaseLetter
            | C::TitlecaseLetter
            | C::ModifierLetter
            | C::OtherLetter
            | C::DecimalNumber
            | C::LetterNumber
            | C::OtherNumber
    )
}
/// Python3.11 str.isprintable under Unicode14; only ASCIIspace is printable
/// among separator categories. The category dependency is pinned to UCD14.
pub fn python_printable(ch: char) -> bool {
    ch == ' '
        || !matches!(
            get_general_category(ch),
            C::Control
                | C::Format
                | C::Unassigned
                | C::PrivateUse
                | C::Surrogate
                | C::SpaceSeparator
                | C::LineSeparator
                | C::ParagraphSeparator
        )
}
static DIGITS: LazyLock<Vec<(u32, u32)>> = LazyLock::new(|| {
    let mut ranges: Vec<_> = include_str!("unicode14-digits.txt")
        .lines()
        .filter_map(|line| {
            let (range, kind) = line.split('#').next()?.split_once(';')?;
            if !matches!(kind.trim(), "Digit" | "Decimal") {
                return None;
            }
            let range = range.trim();
            let (start, end) = range.split_once("..").unwrap_or((range, range));
            Some((
                u32::from_str_radix(start, 16).ok()?,
                u32::from_str_radix(end, 16).ok()?,
            ))
        })
        .collect();
    ranges.sort_unstable();
    ranges
});
/// Python3.11 str.isdigit: Unicode14 Numeric_Type Decimal or Digit.
/// Unlike isalnum/isnumeric, Roman numerals and fractions are excluded.
pub fn python_digit(ch: char) -> bool {
    let codepoint = ch as u32;
    let index = DIGITS.partition_point(|(start, _)| *start <= codepoint);
    index > 0 && codepoint <= DIGITS[index - 1].1
}
pub fn python_space(ch: char) -> bool {
    matches!(
        ch,
        '\t' | '\n' | '\u{000b}' | '\u{000c}' | '\r' | '\u{001c}'..='\u{001f}' | '\u{0085}'
    ) || matches!(
        get_general_category(ch),
        C::SpaceSeparator | C::LineSeparator | C::ParagraphSeparator
    )
}
static CASEFOLD: LazyLock<HashMap<char, String>> = LazyLock::new(|| {
    include_str!("unicode14-casefold.txt")
        .lines()
        .filter_map(|line| {
            let mut fields = line.split('#').next()?.split(';').map(str::trim);
            let ch = char::from_u32(u32::from_str_radix(fields.next()?, 16).ok()?)?;
            let status = fields.next()?;
            if !matches!(status, "C" | "F") {
                return None;
            }
            let mapped = fields
                .next()?
                .split_whitespace()
                .map(|code| char::from_u32(u32::from_str_radix(code, 16).unwrap()).unwrap())
                .collect();
            Some((ch, mapped))
        })
        .collect()
});
pub fn casefold(value: &str) -> String {
    value
        .chars()
        .map(|ch| CASEFOLD.get(&ch).cloned().unwrap_or_else(|| ch.to_string()))
        .collect()
}
static UPPERCASE: LazyLock<HashMap<char, String>> = LazyLock::new(|| {
    include_str!("unicode14-uppercase.txt")
        .lines()
        .filter_map(|line| {
            let (from, to) = line.split('#').next()?.split_once(';')?;
            let ch = char::from_u32(u32::from_str_radix(from, 16).ok()?)?;
            let mapped = to
                .split_whitespace()
                .map(|code| char::from_u32(u32::from_str_radix(code, 16).unwrap()).unwrap())
                .collect();
            Some((ch, mapped))
        })
        .collect()
});
/// Python3.11 default full uppercase, including expansions such as ß -> SS.
pub fn uppercase(value: &str) -> String {
    value
        .chars()
        .map(|ch| {
            UPPERCASE
                .get(&ch)
                .cloned()
                .unwrap_or_else(|| ch.to_string())
        })
        .collect()
}
static TITLECASE: LazyLock<HashMap<char, String>> = LazyLock::new(|| {
    include_str!("unicode14-titlecase.txt")
        .lines()
        .filter_map(|line| {
            let (from, to) = line.split('#').next()?.split_once(';')?;
            Some((
                char::from_u32(u32::from_str_radix(from, 16).ok()?)?,
                to.split_whitespace()
                    .map(|code| char::from_u32(u32::from_str_radix(code, 16).unwrap()).unwrap())
                    .collect(),
            ))
        })
        .collect()
});
static CASING: LazyLock<Vec<(u32, u32, bool)>> = LazyLock::new(|| {
    include_str!("unicode14-derived.txt")
        .lines()
        .filter_map(|line| {
            let (range, kind) = line.split('#').next()?.split_once(';')?;
            let kind = kind.trim();
            if !matches!(kind, "Cased" | "Case_Ignorable") {
                return None;
            }
            let range = range.trim();
            let (start, end) = range.split_once("..").unwrap_or((range, range));
            Some((
                u32::from_str_radix(start, 16).ok()?,
                u32::from_str_radix(end, 16).ok()?,
                kind == "Cased",
            ))
        })
        .collect()
});
fn casing(ch: char, cased: bool) -> bool {
    CASING
        .iter()
        .any(|(start, end, kind)| *kind == cased && (*start..=*end).contains(&(ch as u32)))
}
static LOWERCASE: LazyLock<HashMap<char, String>> = LazyLock::new(|| {
    // Filtered simple lower mappings from UnicodeData14 plus unconditional full
    // mappings from SpecialCasing14. Conditional default Final_Sigma is below.
    let mut mappings: HashMap<char, String> = include_str!("unicode14-data.txt")
        .lines()
        .filter_map(|line| {
            let (from, to) = line.split_once(';')?;
            Some((
                char::from_u32(u32::from_str_radix(from, 16).ok()?)?,
                char::from_u32(u32::from_str_radix(to, 16).ok()?)?.to_string(),
            ))
        })
        .collect();
    for line in include_str!("unicode14-special-casing.txt").lines() {
        let fields: Vec<_> = line
            .split('#')
            .next()
            .unwrap_or("")
            .split(';')
            .map(str::trim)
            .collect();
        if fields.len() < 5 || !fields[4].is_empty() {
            continue;
        }
        let Ok(code) = u32::from_str_radix(fields[0], 16) else {
            continue;
        };
        let Some(ch) = char::from_u32(code) else {
            continue;
        };
        let lower = fields[1]
            .split_whitespace()
            .map(|code| char::from_u32(u32::from_str_radix(code, 16).unwrap()).unwrap())
            .collect();
        mappings.insert(ch, lower);
    }
    mappings
});
fn final_sigma(chars: &[char], index: usize) -> bool {
    let before = chars[..index]
        .iter()
        .rev()
        .copied()
        .find(|ch| !casing(*ch, false))
        .is_some_and(|ch| casing(ch, true));
    let after = chars[index + 1..]
        .iter()
        .copied()
        .find(|ch| !casing(*ch, false))
        .is_some_and(|ch| casing(ch, true));
    before && !after
}
pub fn lowercase(value: &str) -> String {
    let chars: Vec<_> = value.chars().collect();
    let mut result = String::new();
    for (index, ch) in chars.iter().copied().enumerate() {
        if ch == 'Σ' {
            result.push(if final_sigma(&chars, index) {
                'ς'
            } else {
                'σ'
            });
        } else if let Some(mapped) = LOWERCASE.get(&ch) {
            result.push_str(mapped);
        } else {
            result.push(ch);
        }
    }
    result
}

/// Python3.11 str.title, including full title expansions, uncased word
/// boundaries, and the same default Final_Sigma lower context as str.lower.
pub fn titlecase(value: &str) -> String {
    let chars: Vec<_> = value.chars().collect();
    let mut previous_cased = false;
    let mut result = String::new();
    for (index, ch) in chars.iter().copied().enumerate() {
        if !previous_cased {
            if let Some(mapped) = TITLECASE.get(&ch) {
                result.push_str(mapped);
            } else {
                result.push(ch);
            }
        } else if ch == 'Σ' {
            result.push(if final_sigma(&chars, index) {
                'ς'
            } else {
                'σ'
            });
        } else if let Some(mapped) = LOWERCASE.get(&ch) {
            result.push_str(mapped);
        } else {
            result.push(ch);
        }
        previous_cased = casing(ch, true);
    }
    result
}

/// Python str.splitlines, including CR, NEL and Unicode paragraph boundaries.
pub fn splitlines(value: &str) -> Vec<&str> {
    split_lines(value, false)
}
pub fn splitlines_keepends(value: &str) -> Vec<&str> {
    split_lines(value, true)
}
fn split_lines(value: &str, keepends: bool) -> Vec<&str> {
    let mut result = Vec::new();
    let mut start = 0;
    let mut chars = value.char_indices().peekable();
    while let Some((index, ch)) = chars.next() {
        if matches!(
            ch,
            '\n' | '\r' | '\u{000b}' | '\u{000c}' | '\u{001c}'
                ..='\u{001e}' | '\u{0085}' | '\u{2028}' | '\u{2029}'
        ) {
            let mut end = index + ch.len_utf8();
            if ch == '\r' && chars.peek().is_some_and(|(_, ch)| *ch == '\n') {
                end = chars.next().unwrap().0 + 1;
            }
            result.push(&value[start..if keepends { end } else { index }]);
            start = end;
        }
    }
    if start < value.len() {
        result.push(&value[start..]);
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn frozen_case_and_python_word_rules() {
        assert_eq!(casefold("Straße İ Σςσ ﬃ"), "strasse i\u{0307} σσσ ffi");
        assert_eq!(lowercase("ΟΣ ΟΣΑ ΟΣ' ΟΣ'Α İ"), "ος οσα ος' οσ'α i\u{0307}");
        assert!(!python_alnum('\u{0301}'));
        assert!(python_alnum('Ⅷ'));
        assert!(python_alnum('²'));
        assert!(python_space('\u{001c}'));
        assert!(!python_space('\u{200b}'));
    }
    #[test]
    fn line_boundaries_match_python() {
        assert_eq!(
            splitlines("a\r\nb\rc\u{0085}d\u{2028}"),
            vec!["a", "b", "c", "d"]
        );
        assert_eq!(
            splitlines_keepends("a\r\nb\u{0085}"),
            vec!["a\r\n", "b\u{0085}"]
        );
        assert!(splitlines("").is_empty());
        assert_eq!(splitlines("\n"), vec![""]);
    }
    #[test]
    fn digit_class_matches_exhaustive_python311_unicode14_probe() {
        use sha2::{Digest, Sha256};
        let mut digest = Sha256::new();
        let mut count = 0;
        for codepoint in 0u32..0x110000 {
            if char::from_u32(codepoint).is_some_and(python_digit) {
                count += 1;
                digest.update(codepoint.to_le_bytes());
            }
        }
        assert_eq!(count, 788);
        assert_eq!(
            format!("{:x}", digest.finalize()),
            "9ef93de029e9422725df299644013fba93206a15e8d213ef1360d1118b52f43e"
        );
        for ch in ['0', '²', '①', '\u{1d7d8}'] {
            assert!(python_digit(ch));
        }
        for ch in ['⑩', 'Ⅷ', '½'] {
            assert!(!python_digit(ch));
        }
    }
    #[test]
    fn uppercase_matches_exhaustive_python311_unicode14_probe() {
        use sha2::{Digest, Sha256};
        let mut digest = Sha256::new();
        let mut count = 0;
        for cp in 0u32..0x110000 {
            let Some(ch) = char::from_u32(cp) else {
                continue;
            };
            let original = ch.to_string();
            let upper = uppercase(&original);
            if upper != original {
                count += 1;
                digest.update(cp.to_le_bytes());
                digest.update((upper.len() as u32).to_le_bytes());
                digest.update(upper.as_bytes());
            }
        }
        assert_eq!(count, 1525);
        assert_eq!(
            format!("{:x}", digest.finalize()),
            "bb7702551e78225e2bf87bc3c5719b0c0d14031e82629bd82be89d1949c40da2"
        );
        assert_eq!(uppercase("Straße ﬃ ı ᾀ σς"), "STRASSE FFI I ἈΙ ΣΣ");
        assert_eq!(uppercase("ß-7"), "SS-7");
        // Unicode15/16 additions remain unassigned under the frozen contract.
        assert_eq!(uppercase("\u{1c8a}\u{a7cd}"), "\u{1c8a}\u{a7cd}");
    }
    #[test]
    fn printable_matches_exhaustive_python311_unicode14_probe() {
        use sha2::{Digest, Sha256};
        assert_eq!(unicode_general_category::UNICODE_VERSION, (14, 0, 0));
        let mut digest = Sha256::new();
        let mut count = 0;
        for cp in 0u32..0x110000 {
            if char::from_u32(cp).is_some_and(python_printable) {
                count += 1;
                digest.update(cp.to_le_bytes());
            }
        }
        assert_eq!(count, 144516);
        assert_eq!(
            format!("{:x}", digest.finalize()),
            "5a01e63ac06f40669780bb62eefc907b55c176a706671d6df10e8607a55cd193"
        );
        assert!(python_printable(' '));
        assert!(python_printable('가'));
        for ch in ['\n', '\u{a0}', '\u{e000}', '\u{1c8a}'] {
            assert!(!python_printable(ch));
        }
    }
    #[test]
    fn full_title_mapping_and_context_match_python311_unicode14() {
        use sha2::{Digest, Sha256};
        let mut entries: Vec<_> = TITLECASE.keys().copied().collect();
        entries.sort();
        let mut digest = Sha256::new();
        for ch in &entries {
            let result = titlecase(&ch.to_string());
            digest.update((*ch as u32).to_le_bytes());
            digest.update((result.len() as u32).to_le_bytes());
            digest.update(result.as_bytes());
        }
        assert_eq!(entries.len(), 1452);
        assert_eq!(
            format!("{:x}", digest.finalize()),
            "3a31b7e5e43b56f667f8b8eb04957d085d6c9a8b5136e0054cdf6bd61b91c041"
        );
        for (source, expected) in [
            ("some new family", "Some New Family"),
            ("ΟΣ ΟΣΑ", "Ος Οσα"),
            ("a\u{301}b", "A\u{301}B"),
            ("they're", "They'Re"),
            ("ß ﬃ ǳ", "Ss Ffi ǲ"),
            ("\u{1c8a}", "\u{1c8a}"),
        ] {
            assert_eq!(titlecase(source), expected);
        }
    }
}
