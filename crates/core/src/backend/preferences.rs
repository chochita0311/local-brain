//! Application preferences use the native transaction engine in this process.
use super::{storage, BackendError, Config, Result};
use crate::preferences::{native_call_with_options, NativeOptions};
use serde_json::{json, Value};
use std::os::fd::{AsFd, BorrowedFd};

pub fn context(config: &Config) -> Result<crate::Context> {
    Ok(crate::Context {
        data_dir: storage::files::resolve(&storage::files::expand(&config.data_dir, config))?,
        cache_dir: storage::files::resolve(&storage::files::expand(&config.cache_dir, config))?,
        home_dir: storage::files::resolve(&config.home_dir)?,
    })
}
fn call(
    config: &Config,
    operation: &str,
    arguments: Value,
    lease: Option<BorrowedFd<'_>>,
) -> Result<Value> {
    let context = context(config)?;
    let original = storage::files::expand(&config.data_dir, config);
    let original = if original.is_absolute() {
        original
    } else {
        std::env::current_dir()?.join(original)
    };
    let options = NativeOptions {
        package_root: config
            .installation_root
            .as_ref()
            .map(|p| storage::files::resolve(p))
            .transpose()?,
        original_data_dir: Some(original),
        ..NativeOptions::default()
    };
    native_call_with_options(
        operation,
        &context,
        &config.timezone_name,
        arguments,
        lease,
        &options,
    )
    .map_err(|error| {
        if error.kind == "preferences" {
            BackendError::new(409, error.code, error.message)
        } else if error.kind == "terminal" {
            BackendError::new(400, error.code, error.message)
        } else if error.kind == "io" && !["published", "unknown"].contains(&error.commit.as_str()) {
            BackendError::new(500, error.code, error.message)
        } else {
            BackendError::unavailable(
                if ["published", "unknown"].contains(&error.commit.as_str()) {
                    "설정 저장 결과를 확인할 수 없습니다. 설정을 다시 불러온 뒤 확인해 주세요."
                } else {
                    "로컬 설정을 처리하지 못했습니다. LocalBrain 실행 상태를 확인해 주세요."
                },
            )
        }
    })
}
pub fn defaults(config: &Config) -> Result<Value> {
    call(config, "common.defaults", json!({}), None)
}
pub fn read_preferences(config: &Config) -> Result<Value> {
    call(config, "common.read", json!({}), None)
}
pub fn effective_preferences(config: &Config) -> Result<Value> {
    Ok(read_preferences(config)?["effective"].clone())
}
pub fn presentation_preferences(config: &Config) -> Result<Value> {
    match effective_preferences(config) {
        Err(error) if error.status == 409 => defaults(config),
        other => other,
    }
}
pub fn save_preferences(config: &Config, changes: &Value, revision: &Value) -> Result<Value> {
    call(config, "common.preflight", json!({"changes":changes}), None)?;
    let result = {
        let guard = storage::operation_lock(config, "settings")?;
        call(
            config,
            "common.save",
            json!({"changes":changes,"revision":revision}),
            Some(guard.as_fd()),
        )
    };
    // Re-read after releasing the operation lease. Even failed publication has
    // an explicit caller-visible outcome; a readback never retries the write.
    if let Err(error) = result {
        let _ = read_preferences(config);
        return Err(error);
    }
    read_preferences(config)
}
pub fn terminal_read(config: &Config) -> Result<Value> {
    call(config, "terminal.read", json!({}), None)
}
pub fn terminal_launch(config: &Config) -> Result<Value> {
    call(config, "terminal.launch", json!({}), None)
}
pub fn terminal_launch_with_cwd(config: &Config, cwd: Option<&Value>) -> Result<Value> {
    call(
        config,
        "terminal.launch",
        cwd.map(|cwd| json!({"cwdOverride":cwd}))
            .unwrap_or_else(|| json!({})),
        None,
    )
}
pub fn terminal_save(config: &Config, changes: &Value, revision: &Value) -> Result<Value> {
    let guard = storage::operation_lock(config, "settings").map_err(|error| {
        if error.status == 409 {
            BackendError::conflict("설정을 저장하는 중입니다. 잠시 후 다시 시도해 주세요.")
        } else {
            error
        }
    })?;
    let mut arguments = changes
        .as_object()
        .cloned()
        .ok_or_else(|| BackendError::invalid("terminal-settings", "설정 요청을 확인해 주세요."))?;
    arguments.insert("revision".into(), revision.clone());
    call(
        config,
        "terminal.save",
        Value::Object(arguments),
        Some(guard.as_fd()),
    )
}
