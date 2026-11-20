//! Literal metadata keeps Jinja's sorted, ASCII, indent=2 JSON presentation.
//! Serialize the original numbers before the template engine narrows its values.
use localbrain_core::backend::{json, Result};
use serde_json::Value;

pub(super) fn render(value: &Value) -> Result<String> {
    let source = json::canonical(value)?;
    let mut output = String::new();
    let mut input = source.chars().peekable();
    let (mut quoted, mut escaped, mut depth, mut previous) = (false, false, 0usize, None);
    while let Some(ch) = input.next() {
        if quoted {
            if escaped {
                output.push(ch);
                escaped = false;
            } else {
                match ch {
                    '\\' => {
                        output.push(ch);
                        escaped = true;
                    }
                    '"' => {
                        output.push(ch);
                        quoted = false;
                    }
                    '<' | '>' | '&' | '\'' => {
                        use std::fmt::Write;
                        write!(output, "\\u{:04x}", ch as u32).unwrap();
                    }
                    ch if !ch.is_ascii() => {
                        use std::fmt::Write;
                        for code in ch.encode_utf16(&mut [0; 2]) {
                            write!(output, "\\u{code:04x}").unwrap();
                        }
                    }
                    _ => output.push(ch),
                }
            }
        } else {
            match ch {
                '"' => {
                    quoted = true;
                    output.push(ch);
                }
                '{' | '[' => {
                    output.push(ch);
                    depth += 1;
                    if input.peek().copied() != Some(if ch == '{' { '}' } else { ']' }) {
                        newline(&mut output, depth);
                    }
                }
                '}' | ']' => {
                    depth -= 1;
                    if previous != Some(if ch == '}' { '{' } else { '[' }) {
                        newline(&mut output, depth);
                    }
                    output.push(ch);
                }
                ',' => {
                    output.push(ch);
                    newline(&mut output, depth);
                }
                ':' => output.push_str(": "),
                _ => output.push(ch),
            }
        }
        previous = Some(ch);
    }
    Ok(output)
}

fn newline(output: &mut String, depth: usize) {
    output.push('\n');
    output.extend(std::iter::repeat_n(' ', depth * 2));
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn complete_metadata_json_matches_frozen_jinja_without_losing_values() {
        let cases: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/native-metadata-json.json"
        ))
        .unwrap();
        for case in cases.as_array().unwrap() {
            let value = json::decode(case["input"].as_str().unwrap()).unwrap();
            assert_eq!(render(&value).unwrap(), case["expected"].as_str().unwrap());
        }
    }
}
