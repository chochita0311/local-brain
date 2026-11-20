use serde::Serialize;
use serde_json::Value;

pub type Result<T> = std::result::Result<T, BackendError>;

#[derive(Debug, Clone, Serialize)]
pub struct BackendError {
    pub status: u16,
    pub code: String,
    pub message: String,
    pub details: Option<Box<Value>>,
}

impl BackendError {
    pub fn new(status: u16, code: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            status,
            code: code.into(),
            message: message.into(),
            details: None,
        }
    }
    pub fn invalid(code: impl Into<String>, message: impl Into<String>) -> Self {
        Self::new(400, code, message)
    }
    pub fn conflict(message: impl Into<String>) -> Self {
        Self::new(409, "conflict", message)
    }
    pub fn not_found(message: impl Into<String>) -> Self {
        Self::new(404, "not_found", message)
    }
    pub fn unavailable(message: impl Into<String>) -> Self {
        Self::new(503, "unavailable", message)
    }
    pub fn with_details(mut self, details: Value) -> Self {
        self.details = Some(Box::new(details));
        self
    }
    pub fn detail(&self) -> Value {
        self.details
            .as_deref()
            .cloned()
            .unwrap_or_else(|| Value::String(self.message.clone()))
    }
}

impl std::fmt::Display for BackendError {
    fn fmt(&self, output: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        output.write_str(&self.message)
    }
}
impl std::error::Error for BackendError {}
impl From<std::io::Error> for BackendError {
    fn from(error: std::io::Error) -> Self {
        Self::new(500, "io", error.to_string())
    }
}
impl From<rusqlite::Error> for BackendError {
    fn from(error: rusqlite::Error) -> Self {
        Self::new(500, "database", error.to_string())
    }
}
impl From<serde_json::Error> for BackendError {
    fn from(error: serde_json::Error) -> Self {
        Self::invalid("json", error.to_string())
    }
}
impl From<crate::preferences::Fault> for BackendError {
    fn from(error: crate::preferences::Fault) -> Self {
        let status = match error.kind.as_str() {
            "preferences" => 409,
            "terminal" => 400,
            _ => 503,
        };
        Self::new(status, error.code, error.message)
    }
}
