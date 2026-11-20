//! Local retrieval from already collected, explicitly registered sources.
pub mod conditions;
pub mod index;
pub mod keyword;
pub mod model;
pub mod molecules;
pub mod presentation;
pub mod retrieval;
mod service;
pub mod source;
mod unicode_patterns;
use crate::backend::{BackendError, Result};
pub use model::{Encoder, NativeEncoder};
pub use molecules::{Profile, SearchTokenizer};
use serde_json::Value;
pub use service::SearchService;
pub fn refresh_after_scan(
    config: &crate::backend::Config,
    cancel: &localbrain_models::Cancellation,
) -> Result<Option<Value>> {
    SearchService::refresh_after_scan(config, cancel)
}
pub fn failure(code: &str) -> BackendError {
    BackendError::invalid(code, code)
}
fn check_cancel(cancel: &localbrain_models::Cancellation) -> Result<()> {
    if cancel.load(std::sync::atomic::Ordering::Acquire) {
        return Err(failure("SEARCH_INTERRUPTED"));
    }
    Ok(())
}
pub fn digest(value: &Value) -> Result<String> {
    localbrain_models::assets::value_digest(value).map_err(crate::backend::models::failure)
}
pub const SPACE: &str = r"[\t\n\x0B\x0C\r\x1C-\x20\x85\u{A0}\u{1680}\u{2000}-\u{200A}\u{2028}\u{2029}\u{202F}\u{205F}\u{3000}]";
pub fn pattern(value: &str) -> fancy_regex::Regex {
    use std::sync::{LazyLock, Mutex};
    static PATTERNS: LazyLock<Mutex<std::collections::BTreeMap<String, fancy_regex::Regex>>> =
        LazyLock::new(Default::default);
    let mut patterns = PATTERNS.lock().unwrap_or_else(|error| error.into_inner());
    patterns
        .entry(value.to_string())
        .or_insert_with(|| {
            let word = format!("(?-i:{})", unicode_patterns::WORD);
            let boundary = format!("(?:(?<={word})(?!{word})|(?<!{word})(?={word}))");
            let expanded = value
                .replace(r"\s", SPACE)
                .replace(r"\d", unicode_patterns::DECIMAL)
                .replace(r"\b", &boundary);
            fancy_regex::Regex::new(&expanded).expect("fixed search grammar")
        })
        .clone()
}
pub fn urlencode(pairs: &[(&str, String)]) -> String {
    pairs
        .iter()
        .map(|(key, value)| {
            format!(
                "{}={}",
                quote(key).replace("%20", "+"),
                quote(value).replace("%20", "+")
            )
        })
        .collect::<Vec<_>>()
        .join("&")
}

pub fn quote(value: &str) -> String {
    let mut result = String::new();
    for byte in value.bytes() {
        if byte.is_ascii_alphanumeric() || b"_.-~".contains(&byte) {
            result.push(byte as char)
        } else {
            result.push_str(&format!("%{byte:02X}"));
        }
    }
    result
}
