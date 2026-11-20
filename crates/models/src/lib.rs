//! Local pinned model assets and native inference. No Python runtime.
//!
//! Discovery only checks local metadata. Installation is an explicit, public-file
//! operation; inference receives verified local assets and cannot download them.

pub mod assets;
pub mod catalog;
pub mod embedding;
pub mod generation;
mod qwen3_batch;
#[cfg(test)]
mod test_support;
pub mod tokenizer;

use serde::{Deserialize, Serialize};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};

pub type Cancellation = Arc<AtomicBool>;
pub type Result<T> = std::result::Result<T, ModelError>;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ModelError {
    pub code: String,
    pub detail: String,
}

impl ModelError {
    pub fn new(code: &str, detail: impl Into<String>) -> Self {
        Self {
            code: code.into(),
            detail: detail.into(),
        }
    }
}

impl std::fmt::Display for ModelError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.code, self.detail)
    }
}
impl std::error::Error for ModelError {}
impl From<std::io::Error> for ModelError {
    fn from(value: std::io::Error) -> Self {
        Self::new("MODEL_IO", value.to_string())
    }
}
impl From<serde_json::Error> for ModelError {
    fn from(value: serde_json::Error) -> Self {
        Self::new("INVALID_MODEL", value.to_string())
    }
}
impl From<candle_core::Error> for ModelError {
    fn from(value: candle_core::Error) -> Self {
        Self::new("MODEL_INFERENCE", value.to_string())
    }
}

pub fn cancellation() -> Cancellation {
    Arc::new(AtomicBool::new(false))
}

pub(crate) fn check_cancel(cancel: &Cancellation) -> Result<()> {
    if cancel.load(Ordering::Acquire) {
        Err(ModelError::new("MODEL_CANCELLED", "operation cancelled"))
    } else {
        Ok(())
    }
}

pub(crate) fn require(condition: bool, code: &str, detail: &str) -> Result<()> {
    if condition {
        Ok(())
    } else {
        Err(ModelError::new(code, detail))
    }
}
