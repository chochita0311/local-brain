use super::{bind, json_response, Params, EMPTY, SETTINGS};
use crate::{
    state::{database, AppState},
    transport::{self, ApiError, RequestContext},
};
use axum::{
    body::{Body, HttpBody},
    extract::{Request, State},
    response::{IntoResponse, Response},
    routing::{post, MethodFilter},
    Json, Router,
};
use localbrain_core::backend::{
    contexts, preferences, search, sessions, sources, storage, BackendError, Result,
};
use serde_json::{json, Value};
use std::{
    io::Read,
    os::unix::fs::OpenOptionsExt,
    process::{Command, Stdio},
    sync::Mutex,
    time::{Duration, Instant},
};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

fn payload(bytes: &[u8]) -> Result<Value> {
    transport::json_object(bytes, 422, "설정 요청 형식을 확인해 주세요.").map_err(|error| error.0)
}
fn exact(value: &Value, keys: &[&str]) -> bool {
    value.as_object().is_some_and(|map| {
        map.len() == keys.len() && map.keys().all(|key| keys.contains(&key.as_str()))
    })
}
fn model_status(state: &AppState) -> Result<Value> {
    let mut status = state.services.models.status()?;
    if !state.config.feature("context_search") {
        status["generation_models"] = json!([]);
        status["generation_runtime_missing"] = json!([]);
    }
    Ok(status)
}
fn cutoff(state: &AppState) -> Value {
    search::index::search_settings(&state.config).unwrap_or_else(|_|json!({"cutoff":null,"default_cutoff":search::Profile::default().cutoff,"revision":null,"error":"검색 관련도 설정을 읽지 못했습니다. 다시 확인해 주세요."}))
}
fn home(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    body: &[u8],
) -> Result<Response> {
    if state.config.desktop {
        let prefs = preferences::effective_preferences(&state.config)?;
        return Ok(transport::redirect(
            &if prefs["onboarding_completed"] == true {
                format!(
                    "/{}",
                    prefs["startup_screen"]
                        .as_str()
                        .unwrap_or("sessions-dashboard")
                )
            } else {
                "/onboarding".into()
            },
        ));
    }
    super::learning::home(state, request, params, body)
}
fn page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    state.render(
        request,
        "settings.html",
        json!({"active_page":"settings"}),
        200,
    )
}
fn onboarding(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    match preferences::read_preferences(&state.config) {
        Ok(value) => Ok(transport::redirect(&format!(
            "/{}?setup=1",
            value["effective"]["startup_screen"]
                .as_str()
                .unwrap_or("sessions-dashboard")
        ))),
        Err(error) if error.status == 409 => Ok(transport::redirect("/settings")),
        Err(error) => Err(error),
    }
}
fn settings(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let mut errors = Vec::new();
    let prefs = match preferences::read_preferences(&state.config) {
        Ok(mut value) => {
            value.as_object_mut().unwrap().remove("raw");
            value
        }
        Err(error) if error.status == 409 => {
            errors.push(error.message);
            Value::Null
        }
        Err(error) => return Err(error),
    };
    let source_inventory = match sources::settings::source_inventory(&state.config) {
        Ok(mut value) => {
            if let Some(sources) = value["sources"].as_array_mut() {
                for source in sources {
                    source["display_path"] = json!(sessions::home_relative_path(
                        source["root_path"].as_str().unwrap_or(""),
                        &state.config
                    ));
                }
            }
            value
        }
        Err(error) if error.status == 409 => {
            errors.push(error.message);
            Value::Null
        }
        Err(error) => return Err(error),
    };
    let contexts = database(&state.config, false, |db| {
        contexts::service::list_context_sources(db, &state.config)
    })?;
    let mut candidates = sources::settings::candidates(&state.config)?;
    for candidate in candidates.as_array_mut().unwrap() {
        candidate["display_home"] = json!(sessions::home_relative_path(
            candidate["agent_home"].as_str().unwrap_or(""),
            &state.config
        ));
    }
    json_response(
        json!({"preferences":prefs,"session_sources":source_inventory,"context_sources":contexts,"candidates":candidates,"errors":errors,"desktop":state.config.desktop,"sync":state.services.session_sync.status()?,"context_sync":state.services.context_sync.status()?,"model":model_status(state)?,"search_settings":cutoff(state)}),
    )
}
fn get_cutoff(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    json_response(cutoff(state))
}
fn update_cutoff(
    state: &AppState,
    _: &RequestContext,
    _: &Params,
    body: &[u8],
) -> Result<Response> {
    let value = payload(body)?;
    if !exact(&value, &["cutoff", "revision"]) {
        return Err(BackendError::new(
            422,
            "search-settings",
            "검색 관련도 요청을 확인해 주세요.",
        ));
    }
    match search::index::update_cutoff(&state.config, &value["cutoff"], &value["revision"]) {
        Ok(value) => json_response(value),
        Err(error) => Err(match error.code.as_str() {
            "INVALID_SEARCH_CUTOFF" => BackendError::new(
                422,
                "search-settings",
                "최소 관련도는 0부터 1 사이의 숫자로 입력해 주세요.",
            ),
            "SEARCH_SETTINGS_CHANGED" => {
                BackendError::conflict("검색 설정이 변경되었습니다. 다시 확인한 뒤 저장해 주세요.")
            }
            _ if error.code == "io" => {
                BackendError::unavailable("검색 관련도를 저장하지 못했습니다. 다시 시도해 주세요.")
            }
            _ => BackendError::conflict("검색 관련도 설정을 읽지 못했습니다. 다시 확인해 주세요."),
        }),
    }
}
fn save_preferences(
    state: &AppState,
    _: &RequestContext,
    _: &Params,
    body: &[u8],
) -> Result<Response> {
    let value = payload(body)?;
    let mut result =
        preferences::save_preferences(&state.config, &value["changes"], &value["revision"])?;
    result.as_object_mut().unwrap().remove("raw");
    state.services.session_sync.changed();
    state.services.context_sync.changed();
    json_response(result)
}
fn save_sources(state: &AppState, _: &RequestContext, _: &Params, body: &[u8]) -> Result<Response> {
    let result = sources::settings::update_source(&state.config, &payload(body)?)?;
    state.services.session_sync.changed();
    json_response(result)
}
fn model_action(
    state: &AppState,
    _: &RequestContext,
    params: &Params,
    _: &[u8],
) -> Result<Response> {
    match params.get("action").map(String::as_str) {
        Some("install") => state.services.models.start("embedding", None, None)?,
        Some("cancel") => state.services.models.cancel()?,
        Some("prepare") => state.services.search.request_prepare()?,
        Some("disable") => {
            let _lease = storage::operation_lock(&state.config, "search-settings")?;
            let (_, profile) = search::index::read_settings(&state.config)?;
            search::index::save_settings(&state.config, profile, false)?;
            state.services.search.cancel();
        }
        _ => return Err(BackendError::not_found("Not Found")),
    }
    json_response(model_status(state)?)
}
fn generation_action(
    state: &AppState,
    _: &RequestContext,
    params: &Params,
    _: &[u8],
) -> Result<Response> {
    let key = params.get("key").map(String::as_str).unwrap_or("");
    let action = params.get("action").map(String::as_str).unwrap_or("");
    if !state.config.feature("context_search")
        || !["4b", "8b"].contains(&key)
        || !["install", "cancel"].contains(&action)
    {
        return Err(BackendError::not_found("Not Found"));
    }
    if action == "install" {
        state.services.models.start(key, None, None)?;
    } else if state.services.models.status()?["active_key"] == key {
        state.services.models.cancel()?;
    }
    json_response(state.services.models.status()?)
}
fn model_folder(
    state: &AppState,
    _: &RequestContext,
    params: &Params,
    body: &[u8],
) -> Result<Response> {
    let action = params.get("action").map(String::as_str).unwrap_or("");
    if !["check", "apply", "download"].contains(&action) {
        return Err(BackendError::not_found("Not Found"));
    }
    let value = payload(body)?;
    if !exact(
        &value,
        if action == "check" {
            &["path"]
        } else {
            &["path", "revision"]
        },
    ) {
        return Err(BackendError::new(
            422,
            "model-folder",
            "모델 폴더 요청을 확인해 주세요.",
        ));
    }
    match action {
        "check" => json_response(state.services.models.check_folder(&value["path"])?),
        "apply" => json_response(
            state
                .services
                .models
                .use_folder(&value["path"], value["revision"].as_str().unwrap_or(""))?,
        ),
        _ => {
            state.services.models.start(
                "embedding",
                Some(&value["path"]),
                value["revision"].as_str(),
            )?;
            json_response(model_status(state)?)
        }
    }
}
fn storage_status(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let mut status = storage::storage_status(&state.config)?;
    let paths = status["locations"]
        .as_object()
        .map(|locations| locations.keys().cloned().collect::<Vec<_>>())
        .or_else(|| {
            status["locations"].as_array().map(|items| {
                items
                    .iter()
                    .filter_map(|v| v.as_str().map(ToOwned::to_owned))
                    .collect()
            })
        })
        .unwrap_or_default();
    status["display_paths"] = json!(paths
        .iter()
        .map(|key| (
            key.clone(),
            sessions::home_relative_path(status[key].as_str().unwrap_or(""), &state.config)
        ))
        .collect::<std::collections::BTreeMap<_, _>>());
    json_response(status)
}
fn backup(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let artifact = storage::create_backup(&state.config)?;
    let file = tokio::fs::File::from_std(std::fs::File::open(&artifact.archive)?);
    let size = std::fs::metadata(&artifact.archive)?.len();
    let stream =
        futures_util::stream::try_unfold((file, artifact), |(mut file, artifact)| async move {
            let mut bytes = vec![0; 64 * 1024];
            let read = file.read(&mut bytes).await?;
            if read == 0 {
                Ok::<_, std::io::Error>(None)
            } else {
                bytes.truncate(read);
                Ok(Some((bytes, (file, artifact))))
            }
        });
    let mut response = Body::from_stream(stream).into_response();
    response
        .headers_mut()
        .insert("content-type", "application/zip".parse().unwrap());
    response.headers_mut().insert(
        "content-disposition",
        "attachment; filename=\"LocalBrain-backup.zip\""
            .parse()
            .unwrap(),
    );
    response
        .headers_mut()
        .insert("content-length", size.to_string().parse().unwrap());
    Ok(response)
}
fn export_backup(
    state: &AppState,
    _: &RequestContext,
    _: &Params,
    body: &[u8],
) -> Result<Response> {
    json_response(storage::recovery::export_backup(
        &state.config,
        &payload(body)?,
    )?)
}
fn clear_cache(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let _lease = storage::operation_lock(&state.config, "cache-cleanup")?;
    let stopped = state.services.search.stop();
    let result = stopped.and_then(|()| {
        let mut result = storage::recovery::clear_owned_cache(&state.config)?;
        let features = crate::state::maintain_included_caches(&state.config)?;
        result["removed_bytes"] = json!(
            result["removed_bytes"].as_u64().unwrap_or(0)
                + features["removed_bytes"].as_u64().unwrap_or(0)
        );
        if features["protected"]
            .as_array()
            .is_some_and(|items| !items.is_empty())
        {
            result["protected"] = features["protected"].clone();
        }
        Ok(result)
    });
    let restarted = state.services.search.start();
    match (result, restarted) {
        (Ok(value), Ok(())) => json_response(value),
        (Err(error), _) => Err(error),
        (Ok(_), Err(error)) => Err(error),
    }
}
async fn restore(State(state): State<AppState>, request: Request) -> Response {
    if request
        .headers()
        .get("x-localbrain-confirm")
        .and_then(|v| v.to_str().ok())
        != Some("replace-after-restart")
    {
        return transport::error(422, "복원 후 재시작을 확인해 주세요.").into_response();
    }
    let work = match tempfile::Builder::new()
        .prefix("restore-upload-")
        .tempdir_in(&state.config.data_dir)
    {
        Ok(work) => work,
        Err(error) => return ApiError(error.into()).into_response(),
    };
    let path = work.path().join("backup.zip");
    let stdfile = match std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&path)
    {
        Ok(file) => file,
        Err(error) => return ApiError(error.into()).into_response(),
    };
    let mut file = tokio::fs::File::from_std(stdfile);
    let mut body = request.into_body();
    let mut size = 0u64;
    while let Some(frame) =
        futures_util::future::poll_fn(|context| std::pin::Pin::new(&mut body).poll_frame(context))
            .await
    {
        let frame = match frame {
            Ok(frame) => frame,
            Err(_) => {
                return transport::error(400, "백업 업로드를 읽지 못했습니다.").into_response()
            }
        };
        if let Some(bytes) = frame.data_ref() {
            size = size.saturating_add(bytes.len() as u64);
            if size > storage::recovery::MAX_BACKUP_BYTES {
                return transport::error(413, "백업 크기 한도 10GB를 넘었습니다.").into_response();
            }
            if let Err(error) = file.write_all(bytes).await {
                return ApiError(error.into()).into_response();
            }
        }
    }
    if let Err(error) = file.flush().await {
        return ApiError(error.into()).into_response();
    }
    drop(file);
    let result = state
        .blocking(move |state| {
            let result = storage::recovery::stage_restore(&state.config, &path);
            drop(work);
            result
        })
        .await;
    match result {
        Ok(value) => Json(value).into_response(),
        Err(error) => error.into_response(),
    }
}
const CHOOSER:&str=concat!("ObjC.import('AppKit');\n", "function run(args) { const app=$.NSApplication.sharedApplication; app.setActivationPolicy($.NSApplicationActivationPolicyAccessory); const panel=$.NSOpenPanel.openPanel; const directory=args[0]==='directory'; panel.canChooseDirectories=directory; panel.canChooseFiles=!directory; panel.allowsMultipleSelection=false; panel.canCreateDirectories=false; panel.showsHiddenFiles=true; panel.title=directory?'LocalBrain — 폴더 선택':'LocalBrain — 파일 선택'; panel.directoryURL=$.NSURL.fileURLWithPath($.NSHomeDirectory()); app.activateIgnoringOtherApps(true); const response=panel.runModal; if(response===$.NSModalResponseCancel)return JSON.stringify({path:null}); if(response!==$.NSModalResponseOK)throw new Error('File chooser did not complete'); return JSON.stringify({path:ObjC.unwrap(panel.URL.path)}); }");
fn choose_path(
    _: &AppState,
    request: &RequestContext,
    _: &Params,
    body: &[u8],
) -> Result<Response> {
    if !request.same_origin() || request.header("sec-fetch-site") == "cross-site" {
        return Err(BackendError::new(
            403,
            "origin",
            "같은 앱 화면에서 요청해 주세요.",
        ));
    }
    if request.content_type() != "application/json" {
        return Err(BackendError::new(
            415,
            "encoding",
            "설정 요청 형식을 확인해 주세요.",
        ));
    }
    let value = payload(body)?;
    if !exact(&value, &["directory"]) || !value["directory"].is_boolean() {
        return Err(BackendError::new(
            422,
            "picker",
            "파일 또는 폴더 선택을 지정해 주세요.",
        ));
    }
    if !cfg!(target_os = "macos") {
        return Err(BackendError::new(
            501,
            "picker",
            "이 환경에서는 선택창을 열 수 없습니다. 경로를 직접 입력해 주세요.",
        ));
    }
    static LOCK: Mutex<()> = Mutex::new(());
    let _guard = LOCK
        .try_lock()
        .map_err(|_| BackendError::conflict("열려 있는 파일·폴더 선택창을 먼저 닫아 주세요."))?;
    let failure = || {
        BackendError::unavailable(
            "파일·폴더 선택창을 열지 못했습니다. 다시 시도하거나 경로를 직접 입력해 주세요.",
        )
    };
    let mut child = Command::new("/usr/bin/osascript")
        .args([
            "-l",
            "JavaScript",
            "-e",
            CHOOSER,
            if value["directory"] == true {
                "directory"
            } else {
                "file"
            },
        ])
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|_| failure())?;
    let start = Instant::now();
    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                if !status.success() {
                    return Err(failure());
                }
                break;
            }
            Err(_) => {
                let _ = child.kill();
                let _ = child.wait();
                return Err(failure());
            }
            _ => {}
        }
        if start.elapsed() > Duration::from_secs(300) {
            let _ = child.kill();
            let _ = child.wait();
            return Err(BackendError::new(
                408,
                "picker",
                "선택 시간이 만료되었습니다. 찾아보기를 다시 눌러 주세요.",
            ));
        }
        std::thread::sleep(Duration::from_millis(100));
    }
    let mut output = String::new();
    child
        .stdout
        .take()
        .unwrap()
        .take(65_537)
        .read_to_string(&mut output)
        .map_err(|_| failure())?;
    let value: Value = serde_json::from_str(&output).map_err(|_| failure())?;
    let path = value
        .get("path")
        .filter(|value| {
            value.is_null()
                || value
                    .as_str()
                    .is_some_and(|s| s.starts_with('/') && !s.contains('\0'))
        })
        .ok_or_else(failure)?;
    json_response(json!({"path":path}))
}
pub fn install(mut router: Router<AppState>) -> Router<AppState> {
    for (path, handler) in [
        ("/", home as super::Handler),
        ("/settings", page),
        ("/onboarding", onboarding),
        ("/api/settings", settings),
        ("/api/settings/search", get_cutoff),
        ("/api/settings/storage", storage_status),
    ] {
        router = bind(router, path, MethodFilter::GET, handler, EMPTY);
    }
    router = bind(
        router,
        "/api/settings/preferences",
        MethodFilter::PATCH,
        save_preferences,
        SETTINGS,
    );
    for (path, handler) in [
        ("/api/settings/search", update_cutoff as super::Handler),
        ("/api/settings/session-sources", save_sources),
        ("/api/settings/choose-path", choose_path),
        ("/api/settings/model/{action}", model_action),
        ("/api/settings/model-folder/{action}", model_folder),
        ("/api/settings/model/{key}/{action}", generation_action),
        ("/api/settings/backup", backup),
        ("/api/settings/backup/export", export_backup),
        ("/api/settings/cache/clear", clear_cache),
    ] {
        router = bind(router, path, MethodFilter::POST, handler, SETTINGS);
    }
    router.route("/api/settings/restore", post(restore))
}
