use super::{bind, identifier, json_response, payload, BodyLimit, Params, EMPTY, FORM};
use crate::{
    state::{database, AppState},
    templates,
    transport::{self, RequestContext},
};
use axum::{http::Method, response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{
    db, maintenance, resources, workstreams as work, BackendError, Result,
};
use serde_json::{json, Value};

// The six fields allow up to 64,000 Unicode characters. A supplementary
// character can take twelve bytes as an escaped JSON surrogate pair.
const CHECKPOINT_BODY: BodyLimit = BodyLimit {
    status: 413,
    bytes: 768 * 1024,
    message: "체크포인트 내용이 너무 깁니다.",
};
fn body(bytes: &[u8]) -> Result<Value> {
    transport::json_object(bytes, 422, "Invalid request body").map_err(|error| error.0)
}
fn text<'a>(body: &'a Value, key: &str, max: usize) -> Result<Option<&'a str>> {
    payload::string(body, key, 0, max, true)
}
fn unique(error: BackendError, kind: &str) -> BackendError {
    if error.code == "database" && error.message.contains("UNIQUE constraint failed") {
        BackendError::conflict(if kind == "Workstream" {
            "같은 이름의 Workstream이 있습니다."
        } else {
            "같은 제목의 Thread가 있습니다."
        })
    } else {
        error
    }
}
fn list(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    state.render(request,"workstreams.html",json!({"active_page":"workstreams","workstreams":database(&state.config,false,|conn|work::list_workstreams(conn,false))?}),200)
}
fn show(state: &AppState, request: &RequestContext, params: &Params, _: &[u8]) -> Result<Response> {
    let id = identifier(params, "workstream_id")?;
    let (workstream, resources, runs) = database(&state.config, false, |conn| {
        Ok((
            work::get_workstream(conn, id)?
                .ok_or_else(|| BackendError::not_found("Workstream not found"))?,
            work::picker_resources(conn)?,
            work::list_runs(conn, id, 12)?,
        ))
    })?;
    state.render(request,"workstream.html",json!({"active_page":"workstreams","workstream":workstream,"resources":resources,"runs":runs,"task_choices":work::task_choices(),"runner_available":maintenance::runner_executable(&state.config,"claude").is_some(),"runner_command":work::runner_command_preview(),"runner_cwd":state.config.home_dir,"runner_mcp_budget":state.config.mcp_call_budget}),200)
}
fn workstream(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    bytes: &[u8],
) -> Result<Response> {
    let value = body(bytes)?;
    let name = payload::required(&value, "name", 1, 160)?;
    let summary = text(&value, "summary", 2000)?;
    if request.method == Method::PUT {
        let status = payload::required(&value, "status", 0, 32)?;
        database(&state.config, true, |conn| {
            work::update_workstream(
                conn,
                identifier(params, "workstream_id")?,
                name,
                status,
                summary,
            )
        })
        .map_err(|error| unique(error, "Workstream"))?;
        json_response(json!({"ok":true}))
    } else {
        let id = database(&state.config, true, |conn| {
            work::create_workstream(conn, name, summary)
        })
        .map_err(|error| unique(error, "Workstream"))?;
        json_response(json!({"ok":true,"id":id,"redirect":format!("/workstreams/{id}")}))
    }
}
fn thread(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    bytes: &[u8],
) -> Result<Response> {
    let mut value = body(bytes)?;
    payload::required(&value, "title", 1, 180)?;
    for key in ["summary", "current_goal", "next_action"] {
        let field = text(&value, key, 2000)?.map(ToOwned::to_owned);
        value[key] = json!(field);
    }
    if request.method == Method::PUT {
        payload::required(&value, "status", 0, 32)?;
        database(&state.config, true, |conn| {
            work::update_thread(conn, identifier(params, "thread_id")?, &value)
        })
        .map_err(|error| unique(error, "Thread"))?;
        json_response(json!({"ok":true}))
    } else {
        let id = database(&state.config, true, |conn| {
            work::create_thread(conn, identifier(params, "workstream_id")?, &value)
        })
        .map_err(|error| unique(error, "Thread"))?;
        json_response(json!({"ok":true,"id":id}))
    }
}
fn checkpoint(
    state: &AppState,
    _: &RequestContext,
    params: &Params,
    bytes: &[u8],
) -> Result<Response> {
    let mut value = body(bytes)?;
    for key in [
        "current_goal",
        "confirmed_facts",
        "recent_decisions",
        "open_questions",
        "next_actions",
        "files_to_open",
    ] {
        value[key] = json!(text(
            &value,
            key,
            if key == "current_goal" { 4000 } else { 12000 }
        )?);
    }
    let id = database(&state.config, true, |conn| {
        work::create_checkpoint(conn, identifier(params, "workstream_id")?, &value)
    })?;
    json_response(json!({"ok":true,"id":id}))
}
fn link(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    bytes: &[u8],
) -> Result<Response> {
    if request.method == Method::DELETE {
        database(&state.config, true, |conn| {
            work::remove_link(
                conn,
                &params["scope_type"],
                identifier(params, "scope_id")?,
                identifier(params, "link_id")?,
            )
        })?;
        return json_response(json!({"ok":true}));
    }
    let mut value = body(bytes)?;
    if !value.as_object().unwrap().contains_key("relation_type") {
        value["relation_type"] = json!("related-to");
    }
    let id = database(&state.config, true, |conn| {
        work::add_link(
            conn,
            &state.config,
            payload::required(&value, "scope_type", 0, usize::MAX)?,
            payload::integer(&value, "scope_id")?,
            payload::required(&value, "entity_type", 0, usize::MAX)?,
            payload::required(&value, "entity_id", 0, usize::MAX)?,
            payload::required(&value, "relation_type", 1, 80)?,
            "user",
            None,
        )
    })?;
    json_response(json!({"ok":true,"id":id}))
}
fn resource(
    state: &AppState,
    request: &RequestContext,
    _: &Params,
    bytes: &[u8],
) -> Result<Response> {
    let value = body(bytes)?;
    let scope = payload::required(&value, "scope_type", 0, usize::MAX)?;
    let scope_id = payload::integer(&value, "scope_id")?;
    let relation = value
        .get("relation_type")
        .map(|_| payload::required(&value, "relation_type", 1, 80))
        .transpose()?
        .unwrap_or("reference");
    let local = request.path == "/api/local-resources";
    let id = database(&state.config, true, |conn| {
        let id = if local {
            resources::create_local_resource(
                conn,
                &state.config,
                payload::required(&value, "path", 1, 4000)?,
                text(&value, "title", 240)?,
                text(&value, "summary", 4000)?,
                "user",
            )?
        } else {
            resources::create_external_resource(
                conn,
                payload::required(&value, "resource_type", 0, usize::MAX)?,
                payload::required(&value, "title", 1, 240)?,
                payload::required(&value, "url", 1, 2000)?,
                text(&value, "summary", 4000)?,
                text(&value, "source_role", 160)?,
            )?
        };
        work::add_link(
            conn,
            &state.config,
            scope,
            scope_id,
            if local { "local" } else { "external" },
            &id.to_string(),
            relation,
            "user",
            None,
        )?;
        Ok(id)
    })?;
    json_response(json!({"ok":true,"id":id}))
}
fn suggestions(
    state: &AppState,
    _: &RequestContext,
    params: &Params,
    _: &[u8],
) -> Result<Response> {
    if params.contains_key("suggestion_id") {
        database(&state.config, true, |conn| {
            work::resolve_suggestion(
                conn,
                &state.config,
                identifier(params, "suggestion_id")?,
                &params["action"],
            )
        })?;
        json_response(json!({"ok":true}))
    } else {
        let created = database(&state.config, true, |conn| {
            work::generate_suggestions(conn, identifier(params, "workstream_id")?)
        })?;
        json_response(json!({"ok":true,"created":created}))
    }
}
fn start(state: &AppState, _: &RequestContext, params: &Params, bytes: &[u8]) -> Result<Response> {
    if maintenance::runner_executable(&state.config, "claude").is_none() {
        return Err(BackendError::unavailable("Claude CLI를 찾을 수 없습니다."));
    }
    let value = body(bytes)?;
    let task = value
        .get("task_type")
        .map(|_| payload::required(&value, "task_type", 0, 80))
        .transpose()?
        .unwrap_or("organize_resources");
    let instruction = text(&value, "instruction", 4000)?;
    let refresh = payload::boolean(&value, "refresh_suggestions", false)?;
    let id = identifier(params, "workstream_id")?;
    let run = database(&state.config, true, |conn| {
        if db::row(conn,"SELECT id FROM maintenance_runs WHERE workstream_id=? AND status IN ('queued','running','cancelling') LIMIT 1",[id])?.is_some(){return Err(BackendError::invalid("run","이 Workstream에서 이미 실행 중인 작업이 있습니다."));}
        work::prepare_run(conn, &state.config, id, task, instruction, None, refresh)
    })?;
    work::start_run(
        state
            .services
            .tasks
            .as_ref()
            .ok_or_else(|| BackendError::unavailable("Task runtime is unavailable"))?,
        &run,
    )?;
    json_response(json!({"ok":true,"run_id":run,"redirect":format!("/runs/{run}")}))
}
fn run(state: &AppState, request: &RequestContext, params: &Params, _: &[u8]) -> Result<Response> {
    let id = &params["run_id"];
    if request.method == Method::POST {
        let cancelled = state
            .services
            .tasks
            .as_ref()
            .ok_or_else(|| BackendError::unavailable("Task runtime is unavailable"))?
            .cancel(id)?;
        if !cancelled {
            return Err(BackendError::conflict(
                "중지할 수 있는 실행 상태가 아닙니다.",
            ));
        }
        return json_response(json!({"ok":true}));
    }
    let mut run = database(&state.config, false, |conn| maintenance::get_run(conn, id))?
        .filter(|run| {
            run["task_type"]
                .as_str()
                .is_some_and(|task| !task.is_empty())
        })
        .ok_or_else(|| BackendError::not_found("Run not found"))?;
    let output = maintenance::read_run_output(&run)?;
    let placeholder = maintenance::run_output_placeholder(run["status"].as_str().unwrap_or(""));
    if request.path.starts_with("/api/") {
        run["output"] = json!(output);
        run["output_placeholder"] = json!(placeholder);
        run["status_label"] = json!(templates::value_label(
            "maintenance.status",
            run["status"].clone()
        ));
        json_response(json!({"ok":true,"run":run}))
    } else {
        let manifest: Value =
            serde_json::from_str(run["source_snapshot_json"].as_str().unwrap_or("{}"))
                .unwrap_or_else(|_| json!({}));
        state.render(request,"run.html",json!({"active_page":"workstreams","run":run,"output":output,"output_placeholder":placeholder,"candidate_counts":manifest["retrieval"]["counts"].as_object().cloned().unwrap_or_default()}),200)
    }
}
fn local_resource(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    _: &[u8],
) -> Result<Response> {
    let id = identifier(params, "resource_id")?;
    let (resource, memberships) = database(&state.config, false, |conn| {
        Ok((
            resources::local_resource_detail(conn, id)?
                .ok_or_else(|| BackendError::not_found("Local resource not found"))?,
            state
                .services
                .features
                .memberships
                .map(|reader| reader(conn, "local", id))
                .transpose()?
                .unwrap_or_default(),
        ))
    })?;
    state.render(
        request,
        "local_resource.html",
        json!({"active_page":"context","resource":resource,"memberships":memberships}),
        200,
    )
}
pub fn install(mut router: Router<AppState>, workstreams: bool, tasks: bool) -> Router<AppState> {
    router = bind(
        router,
        "/local-resources/{resource_id}",
        MethodFilter::GET,
        local_resource,
        EMPTY,
    );
    if tasks {
        for path in ["/runs/{run_id}", "/api/runs/{run_id}"] {
            router = bind(router, path, MethodFilter::GET, run, EMPTY);
        }
        router = bind(
            router,
            "/api/runs/{run_id}/cancel",
            MethodFilter::POST,
            run,
            FORM,
        );
    }
    if !workstreams {
        return router;
    }
    for (path, handler) in [
        ("/workstreams", list as super::Handler),
        ("/workstreams/{workstream_id}", show),
    ] {
        router = bind(router, path, MethodFilter::GET, handler, EMPTY);
    }
    router = bind(
        router,
        "/api/workstreams/{workstream_id}/checkpoints",
        MethodFilter::POST,
        checkpoint,
        CHECKPOINT_BODY,
    );
    for (path, method, handler) in [
        (
            "/api/workstreams",
            MethodFilter::POST,
            workstream as super::Handler,
        ),
        (
            "/api/workstreams/{workstream_id}",
            MethodFilter::PUT,
            workstream,
        ),
        (
            "/api/workstreams/{workstream_id}/threads",
            MethodFilter::POST,
            thread,
        ),
        ("/api/threads/{thread_id}", MethodFilter::PUT, thread),
        ("/api/links", MethodFilter::POST, link),
        (
            "/api/links/{scope_type}/{scope_id}/{link_id}",
            MethodFilter::DELETE,
            link,
        ),
        ("/api/local-resources", MethodFilter::POST, resource),
        ("/api/external-resources", MethodFilter::POST, resource),
        (
            "/api/workstreams/{workstream_id}/suggestions",
            MethodFilter::POST,
            suggestions,
        ),
        (
            "/api/suggestions/{suggestion_id}/{action}",
            MethodFilter::POST,
            suggestions,
        ),
        (
            "/api/workstreams/{workstream_id}/runs",
            MethodFilter::POST,
            start,
        ),
    ] {
        router = bind(router, path, method, handler, FORM);
    }
    router
}
