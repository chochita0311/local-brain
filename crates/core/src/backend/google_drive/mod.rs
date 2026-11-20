//! Suspended optional Drive integration; every authentication/read/write is explicit.
pub mod api;
pub mod auth;
pub mod engine;
pub mod policy;
pub mod service;
pub mod store;
use crate::backend::{BackendError, Result};
use serde_json::{json, Value};
pub use service::{start_service, DriveService};
pub use store::Store;
pub fn error(code: &str, message: &str, retryable: bool) -> BackendError {
    BackendError::new(422, code, message).with_details(json!({"retryable":retryable}))
}
pub fn retryable(error: &BackendError) -> bool {
    error
        .details
        .as_ref()
        .is_some_and(|v| v["retryable"] == true)
}
pub(crate) fn require(ok: bool, code: &str, message: &str) -> Result<()> {
    if ok {
        Ok(())
    } else {
        Err(error(code, message, false))
    }
}
pub(crate) fn text<'a>(v: &'a Value, key: &str) -> &'a str {
    v[key].as_str().unwrap_or("")
}
pub(crate) fn array(v: &Value) -> &[Value] {
    v.as_array().map(Vec::as_slice).unwrap_or(&[])
}
pub(crate) fn number(v: &Value) -> Option<u64> {
    v.as_u64()
        .or_else(|| v.as_str().and_then(|s| s.parse().ok()))
}
