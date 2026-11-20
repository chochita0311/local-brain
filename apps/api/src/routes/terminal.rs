use super::{bind, json_response, BodyLimit, Params, EMPTY};
use crate::{
    boundary,
    state::AppState,
    transport::{self, RequestContext},
};
use axum::{
    extract::{
        ws::{CloseFrame, Message, WebSocket, WebSocketUpgrade},
        Path, Request, State,
    },
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::{any, MethodFilter},
    Json, Router,
};
use futures_util::{SinkExt, StreamExt};
use localbrain_core::backend::{
    preferences,
    terminal::{self, presentation, shell, TerminalService},
    terminal_workspaces, BackendError, Result,
};
use serde_json::{json, Value};
use std::{collections::BTreeMap, process::Stdio, time::Duration};
use tokio::io::{AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader};

const LIMIT: BodyLimit = BodyLimit {
    status: 413,
    bytes: 128 * 1024,
    message: "요청이 너무 큽니다.",
};
fn body(request: &RequestContext, bytes: &[u8]) -> Result<Value> {
    if !request.same_origin() {
        return Err(BackendError::new(
            403,
            "origin",
            "같은 LocalBrain 화면에서 요청해 주세요.",
        ));
    }
    if request.content_type() != "application/json" {
        return Err(BackendError::new(
            415,
            "encoding",
            "JSON 요청이 필요합니다.",
        ));
    }
    transport::json_object(bytes, 400, "요청 형식이 올바르지 않습니다.").map_err(|error| error.0)
}
#[expect(
    clippy::result_large_err,
    reason = "Keeps the framework Response at the Terminal transport boundary."
)]
fn control<T>(result: localbrain_core::Result<T>) -> std::result::Result<T, Response> {
    result.map_err(|error| {
        if error.kind == "preferences" {
            return transport::error(409, &error.message).into_response();
        }
        let status = if ["busy", "stopping", "not_owner", "conflict"].contains(&error.code.as_str())
        {
            409
        } else if [
            "unavailable",
            "setup_required",
            "start_failed",
            "protocol",
            "disconnected",
        ]
        .contains(&error.code.as_str())
        {
            503
        } else {
            400
        };
        (
            StatusCode::from_u16(status).unwrap(),
            Json(json!({"error":{"code":error.code,"message":error.message}})),
        )
            .into_response()
    })
}
fn perform(result: localbrain_core::Result<Value>) -> Result<Response> {
    Ok(match control(result) {
        Ok(value) => Json(value).into_response(),
        Err(response) => response,
    })
}
fn expected(body: &Value) -> Result<Value> {
    let value = &body["expected"];
    if !exact(value, &["generation", "terminals"])
        || (!value["generation"].is_null() && !value["generation"].is_string())
        || !value["terminals"]
            .as_array()
            .is_some_and(|terms| terms.len() <= 32 && terms.iter().all(Value::is_string))
    {
        return Err(BackendError::invalid(
            "expected",
            "종료할 범위를 다시 확인해 주세요.",
        ));
    }
    Ok(value.clone())
}
fn exact(value: &Value, keys: &[&str]) -> bool {
    value.as_object().is_some_and(|map| {
        map.len() == keys.len() && map.keys().all(|key| keys.contains(&key.as_str()))
    })
}
fn membership(state: &mut Value, spaces: &Value) {
    let mut owners = BTreeMap::new();
    if let Some(items) = spaces["items"].as_array() {
        for item in items {
            if let Some(tabs) = item["tabs"].as_array() {
                for tab in tabs {
                    if let Some(id) = tab.as_str() {
                        owners.insert(id.to_owned(), item["id"].clone());
                    }
                }
            }
        }
    }
    if let Some(tabs) = state["tabs"].as_array_mut() {
        for tab in tabs {
            tab["workspaceId"] = owners
                .get(tab["id"].as_str().unwrap_or(""))
                .cloned()
                .unwrap_or(Value::Null);
        }
    }
}
fn page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    state.render(
        request,
        "terminal.html",
        json!({"active_page":"terminal"}),
        200,
    )
}
fn state(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let service = match control(TerminalService::new(&state.config)) {
        Ok(value) => value,
        Err(response) => return Ok(response),
    };
    let mut value = match control(service.list()) {
        Ok(value) => value,
        Err(response) => return Ok(response),
    };
    value["dependencies"] = match control(service.call("service.dependencies", json!({}))) {
        Ok(value) => value,
        Err(response) => return Ok(response),
    };
    value["defaultCwd"] = json!(state.config.home_dir);
    let spaces = terminal_workspaces::read_workspaces(&state.config, &value);
    membership(&mut value, &spaces);
    value["workspaces"] = spaces;
    value["presentation"] = if let (Some(generation), Some(tabs)) =
        (value["generation"].as_str(), value["tabs"].as_array())
    {
        presentation::load_order(&service.root, generation, tabs)
    } else {
        json!({"order":[]})
    };
    json_response(value)
}
fn workspaces(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    bytes: &[u8],
) -> Result<Response> {
    let mut value = body(request, bytes)?;
    let action = params["action"].as_str();
    let allowed: &[&str] = match action {
        "create" => &["name", "cwd"],
        "update" => &["id", "name", "cwd"],
        "remove" => &["id"],
        "move" => &["id", "tabId", "generation"],
        "reconcile" => &["generation"],
        _ => {
            return Err(BackendError::invalid(
                "workspace",
                "작업공간 요청을 확인해 주세요.",
            ))
        }
    };
    if !exact(&value, allowed) {
        return Err(BackendError::invalid(
            "workspace",
            "작업공간 요청을 확인해 주세요.",
        ));
    }
    if value.get("name").is_some_and(|name| {
        !name.as_str().is_some_and(|name| {
            !name
                .trim_matches(localbrain_core::backend::unicode::python_space)
                .is_empty()
                && name.chars().count() <= 120
        })
    }) {
        return Err(BackendError::invalid(
            "name",
            "작업공간 이름은 1~120자로 입력해 주세요.",
        ));
    }
    if let Some(cwd) = value.get("cwd") {
        let cwd = cwd
            .as_str()
            .ok_or_else(|| BackendError::invalid("cwd", "기본 폴더를 확인해 주세요."))?;
        if !cwd.is_empty() {
            value["cwd"] = preferences::terminal_launch_with_cwd(&state.config, Some(&json!(cwd)))?
                ["cwd"]
                .clone();
        }
    }
    let service = match control(TerminalService::new(&state.config)) {
        Ok(value) => value,
        Err(response) => return Ok(response),
    };
    let mut terminal_error = None;
    let result = terminal_workspaces::change_workspaces(
        &state.config,
        || {
            service.list().map_err(|error| {
                terminal_error = Some(error.clone());
                BackendError::unavailable(error.message)
            })
        },
        action,
        &value,
    );
    if let Some(error) = terminal_error {
        return perform(Err(error));
    }
    json_response(result?)
}
fn order(state: &AppState, request: &RequestContext, _: &Params, bytes: &[u8]) -> Result<Response> {
    let body = body(request, bytes)?;
    if !exact(&body, &["generation", "order"]) || !body["generation"].is_string() {
        return Err(BackendError::invalid(
            "view-order",
            "탭 이동 요청을 확인해 주세요.",
        ));
    }
    let service = match control(TerminalService::new(&state.config)) {
        Ok(value) => value,
        Err(response) => return Ok(response),
    };
    let mut value = match control(service.list()) {
        Ok(value) => value,
        Err(response) => return Ok(response),
    };
    if value["running"] != true || body["generation"] != value["generation"] {
        return Err(BackendError::conflict(
            "터미널 서비스가 바뀌었습니다. 다시 이동해 주세요.",
        ));
    }
    let spaces = terminal_workspaces::read_workspaces(&state.config, &value);
    membership(&mut value, &spaces);
    json_response(presentation::save_order(
        &service.root,
        value["generation"].as_str().unwrap(),
        value["tabs"]
            .as_array()
            .ok_or_else(|| BackendError::unavailable("터미널 상태를 확인하지 못했습니다."))?,
        &body["order"],
    )?)
}
fn settings(
    state: &AppState,
    request: &RequestContext,
    _: &Params,
    bytes: &[u8],
) -> Result<Response> {
    let value = if request.method == axum::http::Method::GET {
        let launch = request
            .query
            .get("launch")
            .map(|value| match value.to_lowercase().as_str() {
                "1" | "true" | "on" | "yes" => Ok(true),
                "0" | "false" | "off" | "no" => Ok(false),
                _ => Err(BackendError::new(
                    422,
                    "query",
                    "Invalid query parameter: launch",
                )),
            })
            .transpose()?
            .unwrap_or(false);
        if launch {
            preferences::terminal_launch_with_cwd(
                &state.config,
                request.query.get("cwd").map(|cwd| json!(cwd)).as_ref(),
            )?
        } else {
            preferences::terminal_read(&state.config)?
        }
    } else {
        let value = body(request, bytes)?;
        if !exact(&value, &["cwd", "shell", "revision"]) || !value["revision"].is_string() {
            return Err(BackendError::invalid(
                "terminal-settings",
                "터미널 설정 요청을 확인해 주세요.",
            ));
        }
        preferences::terminal_save(
            &state.config,
            &json!({"cwd":value["cwd"],"shell":value["shell"]}),
            &value["revision"],
        )?
    };
    json_response(value)
}
fn action(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    bytes: &[u8],
) -> Result<Response> {
    let mut value = body(request, bytes)?;
    let service = match control(TerminalService::new(&state.config)) {
        Ok(value) => value,
        Err(response) => return Ok(response),
    };
    if request.path == "/api/terminal/install" {
        return perform(service.call("service.install", json!({})));
    }
    if request.path.starts_with("/api/terminal/service/") {
        let action = params["action"].as_str();
        if !["start", "stop", "restart"].contains(&action) {
            return Err(BackendError::not_found("Not Found"));
        }
        let force = value
            .get("force")
            .cloned()
            .unwrap_or(json!(false))
            .as_bool()
            .ok_or_else(|| BackendError::invalid("force", "강제 종료 옵션을 확인해 주세요."))?;
        let args = if action == "start" {
            json!({})
        } else {
            json!({"force":force,"expected":expected(&value)?})
        };
        return perform(service.call(&format!("service.{action}"), args));
    }
    if request.path == "/api/terminal/terminals" {
        if value.as_object().unwrap().keys().any(|key| {
            ![
                "key",
                "cwd",
                "shell",
                "cols",
                "rows",
                "tabId",
                "direction",
                "workspaceId",
            ]
            .contains(&key.as_str())
        }) {
            return Err(BackendError::invalid(
                "terminal-create",
                "알 수 없는 생성 옵션입니다.",
            ));
        }
        let workspace = value
            .as_object_mut()
            .unwrap()
            .remove("workspaceId")
            .unwrap_or(Value::Null);
        if !workspace.is_null() {
            let current = match control(service.list()) {
                Ok(value) => value,
                Err(response) => return Ok(response),
            };
            let spaces = terminal_workspaces::read_workspaces(&state.config, &current);
            let item = spaces["items"]
                .as_array()
                .and_then(|items| items.iter().find(|item| item["id"] == workspace));
            if item.is_none_or(|item| {
                !value["tabId"].is_null()
                    && value["tabId"] != ""
                    && !item["tabs"]
                        .as_array()
                        .is_some_and(|tabs| tabs.contains(&value["tabId"]))
            }) {
                return Err(BackendError::conflict(
                    "작업공간의 탭 목록이 바뀌었습니다. 다시 확인해 주세요.",
                ));
            }
        }
        let mut requested = value.get("shell").cloned().unwrap_or(json!(""));
        if requested == "" {
            requested = json!(std::env::var("SHELL")
                .ok()
                .filter(|shell| !shell.is_empty())
                .unwrap_or_else(|| "/bin/zsh".into()));
        }
        value["shell"] = shell::integrated_shell(&state.config, &requested)?;
        let mut result = match control(service.call("terminal.create", value)) {
            Ok(value) => value,
            Err(response) => return Ok(response),
        };
        if !result["tabId"].is_null() && result["tabId"] != "" {
            let spaces = terminal_workspaces::change_workspaces(
                &state.config,
                || {
                    service
                        .list()
                        .map_err(|error| BackendError::unavailable(error.message))
                },
                "attach",
                &json!({"id":workspace,"tabId":result["tabId"],"generation":result["generation"]}),
            );
            match spaces {
                Ok(spaces) => result["workspaces"] = spaces,
                Err(_) => {
                    result["workspaceError"] = json!(
                    "터미널은 열렸지만 작업공간을 저장하지 못했습니다. 목록을 다시 확인해 주세요."
                )
                }
            }
        }
        return json_response(result);
    }
    if let Some(tab) = params.get("tab_id") {
        let action = params["action"].as_str();
        if !["hide", "show", "rename", "stop"].contains(&action) {
            return Err(BackendError::not_found("Not Found"));
        }
        let mut args = json!({"id":tab,"action":action,"name":value["name"]});
        if action == "stop" {
            args["expected"] = expected(&value)?;
        }
        return perform(service.rpc("tab", args, None));
    }
    let force = value
        .get("force")
        .cloned()
        .unwrap_or(json!(false))
        .as_bool()
        .ok_or_else(|| BackendError::invalid("force", "Bad Request"))?;
    if let Some(id) = params.get("terminal_id") {
        let generation = value
            .get("generation")
            .filter(|value| !value.is_null())
            .map(|value| {
                value
                    .as_str()
                    .filter(|value| {
                        value.len() == 32
                            && value
                                .bytes()
                                .all(|ch| ch.is_ascii_digit() || (b'a'..=b'f').contains(&ch))
                    })
                    .ok_or_else(|| {
                        BackendError::invalid("generation", "터미널 서비스를 다시 확인해 주세요.")
                    })
            })
            .transpose()?;
        perform(service.rpc("stop", json!({"id":id,"force":force}), generation))
    } else {
        perform(service.rpc(
            "stop",
            json!({"all":true,"force":force,"expected":expected(&value)?}),
            None,
        ))
    }
}

const INPUT_FAILED: &str =
    "입력이 일부만 전달되었을 수 있습니다. 다시 연결한 뒤 Ctrl+C로 입력을 취소하고 확인해 주세요.";
async fn stream_socket(
    mut socket: WebSocket,
    state: AppState,
    context: RequestContext,
    id: String,
    allowed: bool,
) {
    if !allowed {
        let _ = socket
            .send(Message::Close(Some(CloseFrame {
                code: 1008,
                reason: "".into(),
            })))
            .await;
        return;
    }
    let prepared=state.blocking(move|state|->Result<_>{
        let service=TerminalService::new(&state.config).map_err(|error|BackendError::unavailable(error.message))?;
        let frame=service.request("terminal.stream",json!({"id":id,"unicodeVersion":context.query.get("unicode").map(String::as_str).unwrap_or("6"),"checkpointVersion":context.query.get("checkpoint")})).map_err(|error|BackendError::invalid(error.code,error.message))?;
        Ok((terminal::runtime_executable().map_err(|error|BackendError::unavailable(error.message))?,frame,terminal::environment()))
    }).await;
    let (executable, mut frame, environment) = match prepared {
        Ok(value) => value,
        Err(error) => {
            let _ = socket
                .send(Message::Text(
                    json!({"type":"error","message":error.0.message})
                        .to_string()
                        .into(),
                ))
                .await;
            let _ = socket.close().await;
            return;
        }
    };
    let mut child = match tokio::process::Command::new(executable)
        .arg("stream")
        .env_clear()
        .envs(environment)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .kill_on_drop(true)
        .spawn()
    {
        Ok(child) => child,
        Err(_) => {
            let _ = socket
                .send(Message::Text(
                    json!({"type":"error","message":"연결이 끊겼습니다."})
                        .to_string()
                        .into(),
                ))
                .await;
            let _ = socket.close().await;
            return;
        }
    };
    let mut input = child.stdin.take().unwrap();
    let mut output = BufReader::new(child.stdout.take().unwrap());
    frame.push(b'\n');
    if !matches!(
        tokio::time::timeout(Duration::from_secs(15), input.write_all(&frame)).await,
        Ok(Ok(()))
    ) {
        drop(input);
        let _ = child.kill().await;
        let _ = socket
            .send(Message::Text(
                json!({"type":"error","message":"터미널 연결이 끊겼습니다."})
                    .to_string()
                    .into(),
            ))
            .await;
        let _ = socket.close().await;
        return;
    }
    let (mut sender, mut receiver) = socket.split();
    let mut failed_input = false;
    let (result, output_ended) = {
        let send = &mut sender;
        let output_task = async {
            loop {
                let mut line = vec![];
                let count = (&mut output)
                    .take((2 * 1024 * 1024 + 2) as u64)
                    .read_until(b'\n', &mut line)
                    .await
                    .map_err(|_| "터미널 연결이 끊겼습니다.")?;
                if count == 0 {
                    return Ok(false);
                }
                if line.len() > 2 * 1024 * 1024 + 1 || !line.ends_with(b"\n") {
                    return Err("출력 응답을 확인할 수 없습니다.");
                }
                let value: Value =
                    serde_json::from_slice(&line).map_err(|_| "출력 응답을 확인할 수 없습니다.")?;
                if !value.is_object()
                    || !value["type"]
                        .as_str()
                        .is_some_and(|kind| ["output", "control", "error"].contains(&kind))
                {
                    return Err("출력 응답을 확인할 수 없습니다.");
                }
                send.send(Message::Text(value.to_string().into()))
                    .await
                    .map_err(|_| "연결이 끊겼습니다.")?;
                if value["code"]
                    .as_str()
                    .is_some_and(|code| ["input_busy", "input_failed"].contains(&code))
                {
                    return Ok(true);
                }
            }
        };
        let input_task = async {
            while let Some(message) = receiver.next().await {
                let message = message.map_err(|_| "연결이 끊겼습니다.")?;
                let Message::Text(raw) = message else {
                    match message {
                        Message::Close(_) => return Ok(false),
                        Message::Ping(_) | Message::Pong(_) => continue,
                        _ => return Err("입력 형식이 올바르지 않습니다."),
                    }
                };
                if raw.len() > 128 * 1024 {
                    return Err("입력 형식이나 크기를 확인해 주세요.");
                }
                let value: Value =
                    serde_json::from_str(&raw).map_err(|_| "입력 형식이 올바르지 않습니다.")?;
                if !value.is_object() {
                    return Err("입력 형식이 올바르지 않습니다.");
                }
                let mut bytes =
                    serde_json::to_vec(&value).map_err(|_| "입력 형식이 올바르지 않습니다.")?;
                bytes.push(b'\n');
                if !matches!(
                    tokio::time::timeout(Duration::from_secs(15), input.write_all(&bytes)).await,
                    Ok(Ok(()))
                ) {
                    return Err("연결이 끊겼습니다.");
                }
            }
            Ok(false)
        };
        tokio::select! {
            result = output_task => (result, result == Ok(false)),
            result = input_task => (result, false),
            _ = state.shutdown.wait() => (Ok(false), false),
        }
    };
    match result {
        Ok(failed) => failed_input = failed,
        Err(message) => {
            let _ = sender
                .send(Message::Text(
                    json!({"type":"error","message":message}).to_string().into(),
                ))
                .await;
        }
    }
    // ChildStdin has no user-space write queue: dropping it discards an
    // interrupted write future instead of flushing unsent paste on detach.
    drop(input);
    match tokio::time::timeout(Duration::from_secs(10), child.wait()).await {
        Ok(Ok(status)) if status.code() == Some(75) && !failed_input => {
            failed_input = true;
            let _ = sender
                .send(Message::Text(
                    json!({"type":"error","code":"input_failed","message":INPUT_FAILED})
                        .to_string()
                        .into(),
                ))
                .await;
        }
        Ok(Ok(status)) if output_ended && !status.success() && status.code() != Some(75) => {
            let _ = sender
                .send(Message::Text(
                    json!({"type":"error","message":"터미널 연결이 끊겼습니다."})
                        .to_string()
                        .into(),
                ))
                .await;
        }
        Err(_) => {
            let _ = child.kill().await;
            let _ = child.wait().await;
        }
        _ => {}
    }
    let _ = sender
        .send(Message::Close(Some(CloseFrame {
            code: if failed_input { 1013 } else { 1000 },
            reason: "".into(),
        })))
        .await;
}
async fn stream(
    State(state): State<AppState>,
    Path(id): Path<String>,
    upgrade: std::result::Result<
        WebSocketUpgrade,
        axum::extract::ws::rejection::WebSocketUpgradeRejection,
    >,
    request: Request,
) -> Response {
    let upgrade = match upgrade {
        Ok(upgrade) => upgrade,
        Err(_) => return transport::ApiError(BackendError::not_found("Not Found")).into_response(),
    };
    let context = match RequestContext::new(
        request.method().clone(),
        request.headers().clone(),
        request.uri().clone(),
    ) {
        Ok(context) => context,
        Err(error) => return transport::ApiError(error).into_response(),
    };
    let allowed = context.same_origin()
        && (!state.config.desktop
            || (context.hostname == "127.0.0.1"
                && boundary::authorized(&context, &state.token, false)));
    upgrade
        .max_message_size(128 * 1024 + 1)
        .on_upgrade(move |socket| stream_socket(socket, state, context, id, allowed))
}
pub fn install(mut router: Router<AppState>) -> Router<AppState> {
    for (path, handler) in [
        ("/terminal", page as super::Handler),
        ("/api/terminal", state),
        ("/api/terminal/settings", settings),
    ] {
        router = bind(router, path, MethodFilter::GET, handler, EMPTY);
    }
    for (path, handler) in [
        ("/api/terminal/settings", settings as super::Handler),
        ("/api/terminal/workspaces/{action}", workspaces),
        ("/api/terminal/view-order", order),
        ("/api/terminal/install", action),
        ("/api/terminal/service/{action}", action),
        ("/api/terminal/terminals", action),
        ("/api/terminal/stop", action),
        ("/api/terminal/terminals/{terminal_id}/stop", action),
        ("/api/terminal/tabs/{tab_id}/{action}", action),
    ] {
        router = bind(router, path, MethodFilter::POST, handler, LIMIT);
    }
    router.route("/api/terminal/terminals/{terminal_id}/stream", any(stream))
}
