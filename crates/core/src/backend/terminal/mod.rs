//! Native application adapter for the independent terminal manager.
pub mod presentation;
pub mod shell;

use super::{preferences, Config};
use crate::{files, Error, Request, Result};
use serde_json::{json, Value};
use std::{collections::BTreeMap, path::PathBuf};

pub fn environment() -> BTreeMap<String, String> {
    crate::process::runtime_environment()
}
#[derive(Clone)]
pub struct TerminalService {
    pub context: crate::Context,
    pub root: PathBuf,
}
impl TerminalService {
    pub fn new(config: &Config) -> Result<Self> {
        let context = preferences::context(config).map_err(|_| Error::identity())?;
        let scope = files::digest(context.data_dir.to_string_lossy().as_bytes());
        let root = context.cache_dir.join(format!("terminal-{}", &scope[..10]));
        Ok(Self { context, root })
    }
    pub fn request(&self, operation: &str, arguments: Value) -> Result<Vec<u8>> {
        files::private_location(&self.context.data_dir, &self.context.home_dir)?;
        if !operation.starts_with("settings.") {
            files::private_location(&self.context.cache_dir, &self.context.home_dir)?;
            files::location(&self.root)?;
        }
        let bytes=serde_json::to_vec(&json!({"wire":1,"id":uuid::Uuid::new_v4().simple().to_string(),"context":self.context,"operation":operation,"arguments":arguments})).map_err(|_|Error::invalid())?;
        if bytes.len() > crate::MAX_REQUEST {
            return Err(Error::terminal("invalid", "요청이 너무 큽니다."));
        }
        Ok(bytes)
    }
    pub fn call(&self, operation: &str, arguments: Value) -> Result<Value> {
        Request::parse(&self.request(operation, arguments)?)?.control()
    }
    pub fn list(&self) -> Result<Value> {
        self.call("terminal.list", json!({}))
    }
    pub fn rpc(&self, method: &str, params: Value, generation: Option<&str>) -> Result<Value> {
        self.call(
            "manager.rpc",
            json!({"method":method,"params":params,"generation":generation}),
        )
    }
}
pub fn runtime_executable() -> Result<PathBuf> {
    let mut candidates = vec![];
    if let Some(explicit) =
        std::env::var_os("LOCALBRAIN_TERMINAL_RUNTIME").filter(|value| !value.is_empty())
    {
        let path = PathBuf::from(explicit);
        if path.is_absolute() {
            candidates.push(path);
        }
    } else if let Some(payload) = crate::payload::Payload::source()? {
        candidates.push(payload.root.join("bin/localbrain-runtime"));
    } else if let Ok(executable) = std::env::current_exe() {
        if let Some(parent) = executable.parent() {
            candidates.push(parent.join("localbrain-runtime"));
            if parent.file_name().is_some_and(|name| name == "deps") {
                if let Some(parent) = parent.parent() {
                    candidates.push(parent.join("localbrain-runtime"));
                }
            }
        }
    }
    candidates
        .into_iter()
        .find(|path| files::absolute_executable(path))
        .ok_or_else(|| {
            Error::terminal(
                "setup_required",
                "터미널 Rust 실행 파일이 필요합니다. 터미널 runtime을 빌드해 주세요.",
            )
        })
}
pub fn maintain_cache(config: &Config) -> Value {
    fn retire(config: &Config) -> Result<Value> {
        let service = TerminalService::new(config)?;
        let preview = service.call("runtime.retire", json!({"preview":true}))?;
        if preview["state"] == "absent" {
            return Ok(json!({"removed_bytes":0,"protected":[]}));
        }
        let candidates = preview["receipt"]["candidates"]
            .as_array()
            .ok_or_else(Error::invalid)?;
        let ids = candidates
            .iter()
            .map(|entry| entry["payloadId"].clone())
            .collect::<Vec<_>>();
        fn size(path: &std::path::Path) -> u64 {
            let Ok(info) = std::fs::symlink_metadata(path) else {
                return 0;
            };
            if info.is_file() {
                info.len()
            } else if info.is_dir() {
                std::fs::read_dir(path)
                    .map(|entries| {
                        entries
                            .filter_map(std::result::Result::ok)
                            .map(|entry| size(&entry.path()))
                            .sum()
                    })
                    .unwrap_or(0)
            } else {
                0
            }
        }
        let bytes = ids
            .iter()
            .filter_map(Value::as_str)
            .map(|id| size(&service.root.join("payloads").join(id)))
            .sum::<u64>();
        if !ids.is_empty() {
            service.call(
                "runtime.retire",
                json!({"preview":false,"expectedReceipt":preview["receipt"],"payloadIds":ids}),
            )?;
        }
        let protected = preview["protected"]
            .as_array()
            .ok_or_else(Error::invalid)?
            .iter()
            .map(|entry| json!({"feature":"terminal","reason":entry["reason"]}))
            .collect::<Vec<_>>();
        Ok(json!({"removed_bytes":bytes,"protected":protected}))
    }
    retire(config).unwrap_or_else(|_|json!({"removed_bytes":0,"protected":[{"feature":"terminal","reason":"in_use_or_unknown"}]}))
}
