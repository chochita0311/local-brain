use crate::backend::{BackendError, Result};
use serde_json::Value;
use std::sync::Arc;
#[derive(Clone, Default)]
pub struct ScanControl {
    pub cancelled: Option<Arc<dyn Fn() -> bool + Send + Sync>>,
    pub progress: Option<Arc<dyn Fn(Value) + Send + Sync>>,
}
impl ScanControl {
    pub fn check(&self) -> Result<()> {
        if self.cancelled.as_ref().is_some_and(|callback| callback()) {
            Err(BackendError::new(409, "interrupted", "Source scan stopped"))
        } else {
            Ok(())
        }
    }
    pub fn emit(&self, value: Value) {
        if let Some(callback) = &self.progress {
            let _ = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| callback(value)));
        }
    }
}
