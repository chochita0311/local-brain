//! Suspended optional local document chat. No dialogue or evidence is persisted.
pub mod engine;
mod service;
pub mod tools;
mod worker;
use crate::backend::{BackendError, Result};
use serde_json::Value;
pub use service::{ContextSearchJob, ContextSearchService};
pub use worker::context_search_worker;
pub(crate) fn error(code: &str, message: &str) -> BackendError {
    BackendError::new(422, code, message)
}
pub(crate) fn require(ok: bool, message: &str) -> Result<()> {
    if ok {
        Ok(())
    } else {
        Err(error("TOOL", message))
    }
}
pub(crate) fn chars(value: &str, n: usize) -> String {
    value.chars().take(n).collect()
}
/// Python's non-ASCII JSON text with its default separators, used in model context.
pub(crate) fn dumps(value: &Value) -> Result<String> {
    let compact = crate::backend::json::encode_http(value)?;
    let mut out = String::new();
    let (mut quoted, mut escaped) = (false, false);
    for c in compact.chars() {
        out.push(c);
        if quoted {
            if escaped {
                escaped = false
            } else if c == '\\' {
                escaped = true
            } else if c == '"' {
                quoted = false
            }
        } else if c == '"' {
            quoted = true
        } else if c == ',' || c == ':' {
            out.push(' ')
        }
    }
    Ok(out)
}
