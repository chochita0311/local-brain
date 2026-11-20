//! Early native worker dispatch. Parent EOF interrupts model loading and decoding.
use super::{
    engine::{answer, validate_request},
    error,
};
use crate::backend::{models, Config, Result};
use localbrain_models::{
    catalog::ModelKey,
    embedding::DevicePreference,
    generation::{Decoding, GenerationSettings, LocalGenerator},
};
use serde_json::{json, Value};
use std::{
    io::{BufRead, BufReader, Read, Write},
    path::PathBuf,
    sync::mpsc,
};
fn emit(value: Value) -> Result<()> {
    let mut stdout = std::io::stdout().lock();
    writeln!(stdout, "{}", crate::backend::json::encode_http(&value)?)?;
    stdout.flush()?;
    Ok(())
}
pub fn context_search_worker() -> i32 {
    let (sender, requests) = mpsc::sync_channel(1);
    let owner = crate::backend::worker_thread("context-search-owner").spawn(move || {
        let mut reader = BufReader::new(std::io::stdin());
        loop {
            let mut raw = Vec::new();
            match Read::by_ref(&mut reader)
                .take(262145)
                .read_until(b'\n', &mut raw)
            {
                Ok(n) if n > 0 && n <= 262144 && raw.last() == Some(&b'\n') => {
                    let Ok(value) = std::str::from_utf8(&raw)
                        .map_err(|_| ())
                        .and_then(|s| crate::backend::json::decode(s).map_err(|_| ()))
                    else {
                        break;
                    };
                    if sender.send(value).is_err() {
                        break;
                    }
                }
                _ => break,
            }
        }
        unsafe {
            libc::kill(libc::getpid(), libc::SIGTERM);
        }
    });
    if owner.is_err() {
        return 2;
    }
    let mut generator: Option<LocalGenerator> = None;
    let mut selected: Option<String> = None;
    let mut configuration: Option<Config> = None;
    let cancel = localbrain_models::cancellation();
    while let Ok(request) = requests.recv() {
        if request["type"] == "configure" {
            let configured = (|| -> Result<Config> {
                if configuration.is_some()
                    || !matches!(request["model"].as_str(), Some("4b" | "8b"))
                {
                    return Err(error("INPUT", "모델 선택을 확인해 주세요."));
                }
                let path = |key: &str| {
                    request["config"][key]
                        .as_str()
                        .filter(|p| std::path::Path::new(p).is_absolute())
                        .map(PathBuf::from)
                        .ok_or_else(|| error("INPUT", "모델 선택을 확인해 주세요."))
                };
                let mut config = Config::for_data_dir(path("data_dir")?);
                config.home_dir = path("home_dir")?;
                config.hf_hub_cache = path("hf_hub_cache")?;
                Ok(config)
            })();
            match configured {
                Ok(config) => {
                    configuration = Some(config);
                    selected = request["model"].as_str().map(str::to_owned);
                }
                Err(_) => {
                    let _ = emit(json!({"type":"error","code":"INPUT"}));
                    return 2;
                }
            }
            continue;
        }
        let result = (|| -> Result<Value> {
            let (key, history) = validate_request(
                &json!({"model":request["model"],"messages":request["messages"]}),
            )?;
            if selected.as_ref().is_some_and(|selected| selected != &key) {
                return Err(error("INPUT", "모델 선택을 확인해 주세요."));
            }
            if generator.is_none() {
                emit(json!({"type":"status","phase":"loading"}))?;
                let config = configuration
                    .as_ref()
                    .ok_or_else(|| error("INPUT", "모델 선택을 확인해 주세요."))?;
                let model = if key == "4b" {
                    ModelKey::Generation4b
                } else {
                    ModelKey::Generation8b
                };
                let verified = models::verify_model(config, model, &cancel).or_else(|e| {
                    if !models::model_root(config, model)?
                        .join("model.json")
                        .is_file()
                    {
                        models::install_model(config, model, true, None, None, &cancel, |_| {})
                    } else {
                        Err(e)
                    }
                })?;
                let settings =
                    GenerationSettings::new(false, Decoding::Greedy, None, Some(1024), 90)
                        .map_err(models::failure)?;
                generator = Some(
                    LocalGenerator::new(verified, DevicePreference::Auto, settings)
                        .map_err(models::failure)?,
                );
            }
            let sources = request["sources"]
                .as_array()
                .ok_or_else(|| error("INPUT", "자료 범위를 확인해 주세요."))?;
            answer(
                generator.as_mut().unwrap(),
                sources,
                &history,
                emit,
                &cancel,
            )
        })();
        match result {
            Ok(value) => {
                if emit(value).is_err() {
                    return 2;
                }
            }
            Err(e) => {
                let code = if [
                    "INPUT",
                    "PROTOCOL",
                    "BUDGET",
                    "CONTEXT_TOO_LARGE",
                    "OUTPUT_TRUNCATED",
                    "MODEL_NOT_CACHED",
                    "MODEL_ASSETS_CHANGED",
                    "INVALID_MODEL",
                    "MODEL_BUSY",
                ]
                .contains(&e.code.as_str())
                {
                    e.code.as_str()
                } else {
                    "MODEL_FAILED"
                };
                if emit(json!({"type":"error","code":code})).is_err() {
                    return 2;
                }
            }
        }
    }
    0
}
