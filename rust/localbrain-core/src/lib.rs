//! Shared terminal control; no WebView, HTTP server, database or TOML writer.
pub mod files;
pub mod payload;
pub mod process;
pub mod service;
pub mod settings;
pub mod stream;

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::path::PathBuf;

pub const HOST_PROTOCOL: u64 = 1;
pub const MANAGER_PROTOCOL: u64 = 2;
pub const MAX_REQUEST: usize = 128 * 1024;
pub const MAX_REPLY: usize = 2 * 1024 * 1024 + 4096;

#[derive(Debug, Serialize, Clone)]
pub struct Error {
    pub kind: &'static str,
    pub code: String,
    pub message: String,
}
pub type Result<T> = std::result::Result<T, Error>;
impl Error {
    pub fn terminal(code: &str, message: &str) -> Self {
        Self {
            kind: "terminal",
            code: code.into(),
            message: message.into(),
        }
    }
    pub fn preferences(message: &str) -> Self {
        Self {
            kind: "preferences",
            code: "invalid".into(),
            message: message.into(),
        }
    }
    pub fn invalid() -> Self {
        Self::terminal("invalid", "요청 형식을 확인해 주세요.")
    }
    pub fn identity() -> Self {
        Self::terminal(
            "identity",
            "서비스 식별 정보와 소유자를 확인할 수 없습니다.",
        )
    }
    pub fn unavailable() -> Self {
        Self::terminal("unavailable", "백그라운드 서비스에 연결할 수 없습니다.")
    }
}
impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.message)
    }
}
impl std::error::Error for Error {}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Context {
    pub data_dir: PathBuf,
    pub cache_dir: PathBuf,
    pub home_dir: PathBuf,
}
impl Context {
    pub fn validate(&self) -> Result<()> {
        for path in [&self.data_dir, &self.cache_dir, &self.home_dir] {
            if !path.is_absolute()
                || path.to_str().is_none()
                || path.as_os_str().as_encoded_bytes().contains(&0)
                || path
                    .components()
                    .any(|p| matches!(p, std::path::Component::ParentDir))
            {
                return Err(Error::invalid());
            }
        }
        Ok(())
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub wire: u64,
    pub id: String,
    pub context: Context,
    pub operation: String,
    pub arguments: Value,
}
impl Request {
    pub fn parse(bytes: &[u8]) -> Result<Self> {
        if bytes.len() > MAX_REQUEST {
            return Err(Error::invalid());
        }
        let raw: Value = serde_json::from_slice(bytes).map_err(|_| Error::invalid())?;
        if raw.get("wire").and_then(Value::as_u64) != Some(HOST_PROTOCOL) {
            return Err(Error::invalid());
        }
        let request: Self = serde_json::from_value(raw).map_err(|_| Error::invalid())?;
        if request.id.is_empty() || request.id.len() > 128 || !request.arguments.is_object() {
            return Err(Error::invalid());
        }
        request.context.validate()?;
        let allowed: &[&str] = match request.operation.as_str() {
            "service.status"
            | "service.dependencies"
            | "terminal.list"
            | "service.install"
            | "service.start" => &[],
            "service.stop" | "service.restart" => &["force", "expected"],
            "terminal.create" => &["key", "cwd", "shell", "cols", "rows", "tabId", "direction"],
            "terminal.stop" => &["id", "all", "force", "expected"],
            "tab.action" => &["id", "action", "name", "expected", "force"],
            "manager.rpc" => &["method", "params", "generation"],
            "settings.read" => &["revision", "section"],
            "settings.launch" => &["revision", "section", "cwdOverride"],
            "settings.prepare" => &["revision", "section", "cwd", "shell"],
            "terminal.stream" => &["id", "unicodeVersion", "checkpointVersion"],
            "runtime.retire" => &["preview", "expectedReceipt", "payloadIds"],
            _ => return Err(Error::invalid()),
        };
        fields(&request.arguments, allowed)?;
        Ok(request)
    }
    pub fn control(&self) -> Result<Value> {
        if self.operation.starts_with("settings.") {
            return settings::execute(&self.context, &self.operation, &self.arguments);
        }
        let service = service::Service::new(self.context.clone())?;
        let _lease = if self.operation == "runtime.retire" {
            None
        } else {
            service.use_payload()?
        };
        service.execute(&self.operation, &self.arguments)
    }
    pub fn response(&self) -> Value {
        match self.control() {
            Ok(value) => json!({"wire":HOST_PROTOCOL,"id":self.id,"ok":true,"result":value}),
            Err(error) => json!({"wire":HOST_PROTOCOL,"id":self.id,"ok":false,"error":error}),
        }
    }
}

pub fn fields(value: &Value, allowed: &[&str]) -> Result<()> {
    let object = value.as_object().ok_or_else(Error::invalid)?;
    if object.keys().any(|key| !allowed.contains(&key.as_str())) {
        return Err(Error::invalid());
    }
    Ok(())
}
pub fn boolean(value: &Value, key: &str) -> Result<bool> {
    match value.get(key) {
        None => Ok(false),
        Some(v) => v.as_bool().ok_or_else(Error::invalid),
    }
}
pub fn string<'a>(value: &'a Value, key: &str) -> Result<&'a str> {
    value
        .get(key)
        .and_then(Value::as_str)
        .ok_or_else(Error::invalid)
}
