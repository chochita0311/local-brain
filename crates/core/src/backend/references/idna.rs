//! IDNA2003 compatibility for existing resource identities. This intentionally
//! differs from a web browser's modern URL-host normalization.
use super::nameprep_tables::*;
use unicode_normalization::UnicodeNormalization;
fn contains(ranges: &[(u32, u32)], ch: char) -> bool {
    let point = ch as u32;
    let index = ranges.partition_point(|(start, _)| *start <= point);
    index > 0 && ranges[index - 1].1 >= point
}
fn normalize32(value: &str) -> String {
    let mut out = String::new();
    let mut segment = String::new();
    for ch in value.chars() {
        if contains(UNASSIGNED, ch) {
            out.extend(segment.nfkc());
            segment.clear();
            out.push(ch);
        } else {
            match ch as u32 {
                194664 => segment.push('𡍪'),
                194676 => segment.push('弳'),
                194847 => segment.push('䎫'),
                194911 => segment.push('窮'),
                195007 => segment.push('䵗'),
                _ => segment.push(ch),
            }
        }
    }
    out.extend(segment.nfkc());
    out
}
fn nameprep(value: &str) -> Option<String> {
    let mut mapped = String::new();
    for ch in value.chars() {
        match MAPPING.binary_search_by_key(&(ch as u32), |(point, _)| *point) {
            Ok(index) => mapped.push_str(MAPPING[index].1),
            Err(_) => mapped.push(ch),
        }
    }
    let value = normalize32(&mapped);
    if value.chars().any(|ch| contains(PROHIBITED, ch)) {
        return None;
    }
    if value.chars().any(|ch| contains(RANDAL, ch))
        && (value.chars().any(|ch| contains(LCAT, ch))
            || !value.chars().next().is_some_and(|ch| contains(RANDAL, ch))
            || !value.chars().last().is_some_and(|ch| contains(RANDAL, ch)))
    {
        return None;
    }
    Some(value)
}
fn adapt(mut delta: u64, points: u64, first: bool) -> u64 {
    delta = if first { delta / 700 } else { delta / 2 };
    delta += delta / points;
    let mut k = 0;
    while delta > 455 {
        delta /= 35;
        k += 36;
    }
    k + 36 * delta / (delta + 38)
}
fn digit(value: u64) -> Option<char> {
    match value {
        0..=25 => char::from_u32(b'a' as u32 + value as u32),
        26..=35 => char::from_u32(b'0' as u32 + (value - 26) as u32),
        _ => None,
    }
}
fn punycode(value: &str) -> Option<String> {
    let points = value.chars().map(|ch| ch as u64).collect::<Vec<_>>();
    let mut out = value.chars().filter(char::is_ascii).collect::<String>();
    let basic = out.len() as u64;
    let mut handled = basic;
    if basic > 0 {
        out.push('-');
    }
    let (mut n, mut delta, mut bias) = (128_u64, 0_u64, 72_u64);
    while handled < points.len() as u64 {
        let next = *points.iter().filter(|point| **point >= n).min()?;
        delta = delta.checked_add((next - n).checked_mul(handled + 1)?)?;
        n = next;
        for point in &points {
            if *point < n {
                delta = delta.checked_add(1)?;
            }
            if *point == n {
                let mut q = delta;
                let mut k = 36;
                loop {
                    let threshold = if k <= bias {
                        1
                    } else if k >= bias + 26 {
                        26
                    } else {
                        k - bias
                    };
                    if q < threshold {
                        break;
                    }
                    out.push(digit(threshold + (q - threshold) % (36 - threshold))?);
                    q = (q - threshold) / (36 - threshold);
                    k += 36;
                }
                out.push(digit(q)?);
                bias = adapt(delta, handled + 1, handled == basic);
                delta = 0;
                handled += 1;
            }
        }
        delta = delta.checked_add(1)?;
        n += 1;
    }
    Some(out)
}
fn label(value: &str) -> Option<String> {
    if value.is_ascii() {
        return (!value.is_empty() && value.len() < 64).then(|| value.to_string());
    }
    let value = nameprep(value)?;
    let value = if value.is_ascii() {
        value
    } else {
        if value.starts_with("xn--") {
            return None;
        }
        format!("xn--{}", punycode(&value)?)
    };
    (!value.is_empty() && value.len() < 64).then_some(value)
}
pub fn ascii(value: &str) -> Option<String> {
    let value = value.replace(['\u{3002}', '\u{ff0e}', '\u{ff61}'], ".");
    let mut parts = value.split('.').collect::<Vec<_>>();
    let trailing = parts.last() == Some(&"");
    if trailing {
        parts.pop();
    }
    let labels = parts.into_iter().map(label).collect::<Option<Vec<_>>>()?;
    let mut result = labels.join(".");
    if trailing {
        result.push('.');
    }
    Some(result.to_ascii_lowercase())
}
