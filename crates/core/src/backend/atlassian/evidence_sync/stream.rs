//! Incremental persisted-body scanner; chunk boundaries never change locations.
use crate::backend::{references::trim_url_token, unicode};
use serde::Serialize;
use std::collections::VecDeque;
pub const MAX_URL_CODE_POINTS: usize = 8_000;
#[derive(Debug, Serialize)]
pub struct DocumentUrl {
    pub observed_url: Option<String>,
    pub source_line: i64,
    pub url_ordinal: i64,
}
#[derive(Debug, Serialize)]
pub struct DocumentScan {
    pub candidates: Vec<DocumentUrl>,
    pub url_overflow: usize,
    pub key_only_count: usize,
}
#[derive(Default)]
pub struct DocumentStreamScanner {
    candidates: Vec<DocumentUrl>,
    url_count: usize,
    key_only_count: usize,
    line: i64,
    line_url_ordinal: i64,
    recent: VecDeque<char>,
    key_chars: String,
    key_length: usize,
    key_too_long: bool,
    in_url: bool,
    url_chars: String,
    url_length: usize,
    url_too_long: bool,
    url_line: i64,
    url_ordinal: i64,
    after_carriage_return: bool,
}
impl DocumentStreamScanner {
    pub fn new() -> Self {
        Self {
            line: 1,
            ..Self::default()
        }
    }
    pub fn feed(&mut self, text: &str) {
        for ch in text.chars() {
            if self.in_url {
                if unicode::python_space(ch) || "<>'\"`".contains(ch) {
                    self.finish_url();
                    self.feed_plain(ch);
                } else if self.url_length < MAX_URL_CODE_POINTS {
                    self.url_chars.push(ch);
                    self.url_length += 1;
                } else {
                    self.url_too_long = true;
                }
                continue;
            }
            self.feed_plain(ch);
        }
    }
    pub fn finish(mut self) -> DocumentScan {
        if self.in_url {
            self.finish_url();
        }
        self.finish_key();
        DocumentScan {
            candidates: self.candidates,
            url_overflow: self.url_count.saturating_sub(super::MAX_SOURCE_EVIDENCE),
            key_only_count: self.key_only_count,
        }
    }
    fn feed_plain(&mut self, ch: char) {
        let key_ch = ch.is_ascii_alphanumeric()
            || "_-".contains(ch)
            || matches!(ch, '\u{130}' | '\u{131}' | '\u{17f}' | '\u{212a}');
        if key_ch {
            if self.key_length < MAX_URL_CODE_POINTS {
                self.key_chars.push(ch);
                self.key_length += 1;
            } else {
                self.key_too_long = true;
            }
        } else {
            self.finish_key();
        }
        if unicode::python_space(ch) || "<>'\"`".contains(ch) {
            self.recent.clear();
        } else {
            self.recent.push_back(ch);
            if self.recent.len() > 8 {
                self.recent.pop_front();
            }
        }
        let suffix = |prefix: &str| {
            self.recent.len() >= prefix.len()
                && self
                    .recent
                    .iter()
                    .rev()
                    .zip(prefix.chars().rev())
                    .all(|(a, b)| a.to_ascii_lowercase() == b)
        };
        let prefix = if suffix("https://") {
            Some(8)
        } else if suffix("http://") {
            Some(7)
        } else {
            None
        };
        if let Some(length) = prefix {
            self.in_url = true;
            self.url_chars = self
                .recent
                .iter()
                .copied()
                .skip(self.recent.len() - length)
                .collect();
            self.url_length = length;
            self.url_too_long = false;
            self.url_line = self.line;
            self.line_url_ordinal += 1;
            self.url_ordinal = self.line_url_ordinal;
            self.recent.clear();
        }
        match ch {
            '\r' => {
                self.line += 1;
                self.line_url_ordinal = 0;
                self.recent.clear();
                self.after_carriage_return = true;
            }
            '\n' => {
                if !self.after_carriage_return {
                    self.line += 1;
                }
                self.line_url_ordinal = 0;
                self.recent.clear();
                self.after_carriage_return = false;
            }
            '\u{b}' | '\u{c}' | '\u{1c}'..='\u{1e}' | '\u{85}' | '\u{2028}' | '\u{2029}' => {
                self.line += 1;
                self.line_url_ordinal = 0;
                self.recent.clear();
                self.after_carriage_return = false;
            }
            _ => self.after_carriage_return = false,
        }
    }
    fn finish_key(&mut self) {
        if self.key_length > 0 && !self.key_too_long {
            let chars = self.key_chars.chars().collect::<Vec<_>>();
            let letter = |ch: char| {
                ch.is_ascii_alphabetic()
                    || matches!(ch, '\u{130}' | '\u{131}' | '\u{17f}' | '\u{212a}')
            };
            if let Some(index) = chars.iter().rposition(|ch| *ch == '-') {
                if index > 0
                    && index + 1 < chars.len()
                    && letter(chars[0])
                    && chars[1..index]
                        .iter()
                        .all(|ch| letter(*ch) || ch.is_ascii_digit() || *ch == '_')
                    && chars[index + 1..].iter().all(char::is_ascii_digit)
                {
                    self.key_only_count += 1;
                }
            }
        }
        self.key_chars.clear();
        self.key_length = 0;
        self.key_too_long = false;
    }
    fn finish_url(&mut self) {
        self.url_count += 1;
        if self.url_count <= super::MAX_SOURCE_EVIDENCE {
            let observed = (!self.url_too_long)
                .then(|| trim_url_token(&self.url_chars))
                .filter(|s| !s.is_empty());
            self.candidates.push(DocumentUrl {
                observed_url: observed,
                source_line: self.url_line,
                url_ordinal: self.url_ordinal,
            });
        }
        self.in_url = false;
        self.url_chars.clear();
        self.url_length = 0;
        self.url_too_long = false;
    }
}
