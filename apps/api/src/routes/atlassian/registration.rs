use super::{explorer, form_route, integer, invalid, navigation as nav, optional, text};
use crate::{
    routes::{bind, identifier, Params, EMPTY},
    state::{database, AppState},
    transport::{self, RequestContext},
};
use axum::{response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{
    atlassian::{evidence, registration as catalog},
    db, maintenance, BackendError, Result,
};
use rusqlite::Connection;
use serde_json::{json, Value};
fn add_context(return_to: &str, form: &Value, error: Option<&str>) -> Value {
    json!({"active_page":"atlassian","page_title":"Add Atlassian URL · LocalBrain","return_to":return_to,"form_state":form,"form_error":error})
}
fn connections_context(
    state: &AppState,
    conn: &Connection,
    view: &str,
    notice: Option<&str>,
    catalog_run: Option<&str>,
) -> Result<Value> {
    let view = nav::connections_view(view);
    let service = nav::service(view);
    let service = service.as_str().unwrap();
    let scopes = catalog::registered_scope_overview(conn, service)?;
    let count: usize = scopes
        .iter()
        .map(|scope| scope["spaces"].as_array().map_or(0, Vec::len))
        .sum();
    let (catalog, catalog_error) = if let Some(run) =
        catalog_run.filter(|run| !run.is_empty() && run.chars().count() <= 300)
    {
        match catalog::space_catalog_candidates(conn, run, Some(service)) {
            Ok(value) => (value, Value::Null),
            Err(error) if error.status < 500 => (Value::Null, json!(error.message)),
            Err(error) => return Err(error),
        }
    } else {
        (Value::Null, Value::Null)
    };
    Ok(
        json!({"active_page":"atlassian","page_title":"Atlassian Connections · LocalBrain","selected_view":view,"selected_service":service,"registered_scopes":scopes,"registered_scope_space_count":count,"sites":catalog::registration_sites(conn,service)?,"notice":nav::notice(notice),"catalog":catalog,"catalog_error":catalog_error,"catalog_run":catalog_run.unwrap_or("").chars().take(300).collect::<String>(),"external_executor_ready":state.services.features.external_executor.is_some(),"access_form_state":{},"access_error":null,"connection_form_state":{},"connection_error":null,"connection_error_binding_id":null,"discovery_form_state":{},"discovery_error":null,"candidate_form_state":{},"candidate_error":null}),
    )
}
fn handoff(result: &Value) -> String {
    let view = nav::view_for_service(text(result, "service"));
    let notice = format!(
        "{}-{}",
        text(result, "kind"),
        if result["created"] == true {
            "created"
        } else {
            "reused"
        }
    );
    let mut overrides = vec![("site_id", result["site_id"].clone())];
    if result["kind"] == "item" {
        overrides.push(("item", result["id"].clone()));
        overrides.push(("notice", json!(notice)));
        if !result["space_id"].is_null() {
            overrides.push(("space_id", result["space_id"].clone()));
        } else {
            let hint = evidence::atlassian_url_container_hint(result["canonical_url"].as_str());
            overrides.push((
                "structural_scope",
                hint.map(|hint| hint["structural_scope"].clone())
                    .unwrap_or(json!("unclassified")),
            ));
        }
        if result["attention"] == "archived" {
            overrides.push(("attention", json!("archived")));
        }
    } else {
        overrides.push(("space_id", result["id"].clone()));
        overrides.push(("notice", json!(notice)));
    }
    nav::browse_url(view, &json!({}), &overrides)
}
fn add(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let return_to = database(&state.config, false, |conn| {
        explorer::add_return_path(conn, request.query.get("return_to").map(String::as_str))
    })?;
    state.render(
        request,
        "atlassian-add.html",
        add_context(&return_to, &json!({}), None),
        200,
    )
}
fn connections(
    state: &AppState,
    request: &RequestContext,
    _: &Params,
    _: &[u8],
) -> Result<Response> {
    let raw = localbrain_core::backend::unicode::lowercase(
        request
            .parameter("view")
            .trim_matches(localbrain_core::backend::unicode::python_space),
    );
    if !["jira", "wiki"].contains(&raw.as_str()) {
        return Ok(transport::redirect(&nav::connections_url(
            &raw,
            request.query.get("notice").map(String::as_str),
            request.query.get("catalog_run").map(String::as_str),
            None,
        )));
    }
    let context = database(&state.config, false, |conn| {
        connections_context(
            state,
            conn,
            &raw,
            request.query.get("notice").map(String::as_str),
            request.query.get("catalog_run").map(String::as_str),
        )
    })?;
    state.render(request, "atlassian-connections.html", context, 200)
}
fn preview(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let url = request.parameter("url");
    if !(1..=8000).contains(&url.chars().count()) {
        return Err(BackendError::new(422, "query", "URL length is invalid"));
    }
    match database(&state.config, false, |conn| {
        catalog::registration_preview(conn, &json!({"url":url}))
    }) {
        Ok(value) => crate::routes::json_response(value),
        Err(error) if error.status < 500 => {
            let mut response = crate::routes::json_response(
                json!({"detail":{"code":error.code,"message":error.message}}),
            )?;
            *response.status_mut() = axum::http::StatusCode::UNPROCESSABLE_ENTITY;
            Ok(response)
        }
        Err(error) => Err(error),
    }
}
fn register(
    state: &AppState,
    request: &RequestContext,
    _: &Params,
    form: Result<Value>,
) -> Result<Response> {
    let mut fields = json!({});
    let mut return_to = "/atlassian#atlassian-add-action".into();
    let result = (|| {
        fields = form?;
        return_to = database(&state.config, false, |conn| {
            explorer::add_return_path(conn, optional(&fields, "return_to"))
        })?;
        database(&state.config, true, |conn| {
            catalog::register_atlassian_url(conn, &json!({"url":text(&fields,"url")}))
        })
    })();
    match result {
        Ok(value) => Ok(transport::redirect(&handoff(&value))),
        Err(error) if error.status < 500 => {
            let partial = request.header("x-localbrain-partial") == "atlassian-add";
            let mut response = state.render(
                request,
                if partial {
                    "_atlassian-add-form.html"
                } else {
                    "atlassian-add.html"
                },
                add_context(
                    &return_to,
                    &json!({"url":text(&fields,"url")}),
                    Some(&error.message),
                ),
                422,
            )?;
            if partial {
                response
                    .headers_mut()
                    .insert("vary", "X-LocalBrain-Partial".parse().unwrap());
            }
            Ok(response)
        }
        Err(error) => Err(error),
    }
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
fn connection_error(
    state: &AppState,
    request: &RequestContext,
    view: &str,
    form: &Value,
    kind: &str,
    error: &BackendError,
    catalog_run: Option<&str>,
    binding: Option<i64>,
) -> Result<Response> {
    if error.status >= 500 {
        return Err(error.clone());
    }
    let mut context = database(&state.config, false, |conn| {
        connections_context(state, conn, view, None, catalog_run)
    })?;
    context[format!("{kind}_form_state")] = form.clone();
    context[format!("{kind}_error")] = json!(error.message);
    context["connection_error_binding_id"] = json!(binding);
    state.render(request, "atlassian-connections.html", context, 422)
}
fn access(
    state: &AppState,
    request: &RequestContext,
    _: &Params,
    form: Result<Value>,
) -> Result<Response> {
    let mut fields = json!({});
    let result = (|| {
        fields = form?;
        let service = text(&fields, "service");
        if !["jira", "confluence"].contains(&service) {
            return Err(BackendError::invalid(
                "invalid-service",
                "Atlassian service is invalid",
            ));
        }
        let site = integer(optional(&fields, "site_id"), "Site")?.ok_or_else(|| {
            BackendError::invalid("site-required", "접근 경로를 연결할 Site를 선택하세요.")
        })?;
        database(&state.config, true, |conn| {
            catalog::register_atlassian_site_access(
                conn,
                &json!({"site_id":site,"service":service,"provider_kind":text(&fields,"provider_kind"),"config_ref":text(&fields,"config_ref")}),
            )
        })
    })();
    match result {
        Ok(value) => Ok(transport::redirect(&nav::connections_url(
            nav::view_for_service(text(&fields, "service")),
            Some(if value["binding_created"] == true {
                "connection-created"
            } else {
                "connection-updated"
            }),
            None,
            Some(&format!("atlassian-connection-{}", value["binding_id"])),
        ))),
        Err(error) => connection_error(
            state,
            request,
            nav::view_for_service(text(&fields, "service")),
            &fields,
            "access",
            &error,
            None,
            None,
        ),
    }
}
fn update(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    form: Result<Value>,
) -> Result<Response> {
    let source = identifier(params, "source_instance_id")?;
    let site = identifier(params, "site_id")?;
    let mut fields = json!({});
    let result = (|| {
        if source < 1 || site < 1 {
            return Err(invalid("Connection path is invalid"));
        }
        fields = form?;
        database(&state.config, true, |conn| {
            catalog::update_atlassian_connection(
                conn,
                &json!({"source_instance_id":source,"site_id":site,"enabled":text(&fields,"enabled")=="1","config_ref":optional(&fields,"config_ref").filter(|value|!value.is_empty())}),
            )
        })
    })();
    match result {
        Ok(value) => Ok(transport::redirect(&nav::connections_url(
            nav::view_for_service(text(&value, "service")),
            Some("connection-updated"),
            None,
            Some(&format!("atlassian-connection-{}", value["binding_id"])),
        ))),
        Err(error) => {
            let authority = if source >= 1 && site >= 1 {
                database(&state.config, false, |conn| {
                    db::row(conn,"SELECT external_source_instances.service,atlassian_site_bindings.id AS binding_id FROM external_source_instances LEFT JOIN atlassian_site_bindings ON atlassian_site_bindings.source_instance_id=external_source_instances.id AND atlassian_site_bindings.site_id=? WHERE external_source_instances.id=?",rusqlite::params![site,source])
                })?
            } else {
                None
            };
            let authority = authority.unwrap_or(Value::Null);
            connection_error(
                state,
                request,
                nav::view_for_service(text(&authority, "service")),
                &fields,
                "connection",
                &error,
                None,
                authority["binding_id"].as_i64(),
            )
        }
    }
}
fn candidate(
    state: &AppState,
    request: &RequestContext,
    _: &Params,
    form: Result<Value>,
) -> Result<Response> {
    let mut fields = json!({});
    let result = (|| {
        fields = form?;
        let run = text(&fields, "catalog_run");
        if run.is_empty() || run.chars().count() > 300 {
            return Err(BackendError::invalid(
                "catalog-required",
                "Space candidate has no catalog Run",
            ));
        }
        database(&state.config, true, |conn| {
            catalog::register_space_catalog_candidate(
                conn,
                &json!({"run_id":run,"candidate_key":text(&fields,"candidate_key")}),
            )
        })
    })();
    match result {
        Ok(value) => Ok(transport::redirect(&handoff(&value))),
        Err(error) => {
            let run = text(&fields, "catalog_run")
                .chars()
                .take(300)
                .collect::<String>();
            let authority = database(&state.config, false, |conn| {
                db::row(
                    conn,
                    "SELECT service FROM external_sync_runs WHERE maintenance_run_id=?",
                    [&run],
                )
            })?
            .unwrap_or(Value::Null);
            connection_error(
                state,
                request,
                nav::view_for_service(text(&authority, "service")),
                &fields,
                "candidate",
                &error,
                Some(&run),
                None,
            )
        }
    }
}
fn discover(
    state: &AppState,
    request: &RequestContext,
    _: &Params,
    form: Result<Value>,
) -> Result<Response> {
    let mut fields = json!({});
    let mut service = "jira".to_owned();
    let result = (|| {
        fields = form?;
        let site = integer(optional(&fields, "site_id"), "Site")?
            .ok_or_else(|| BackendError::invalid("site-required", "조회할 Site를 선택하세요."))?;
        let binding =
            integer(optional(&fields, "binding_id"), "Access binding")?.ok_or_else(|| {
                BackendError::invalid(
                    "binding-required",
                    "조회에 사용할 MCP 접근 경로를 선택하세요.",
                )
            })?;
        let runner = optional(&fields, "runner").unwrap_or("claude");
        if !["claude", "codex"].contains(&runner) {
            return Err(BackendError::invalid(
                "invalid-runner",
                "Maintenance runner is invalid",
            ));
        }
        let run = database(&state.config, true, |conn| {
            let row=db::row(conn,"SELECT atlassian_site_bindings.site_id,external_source_instances.id AS source_instance_id,external_source_instances.service,atlassian_sites.normalized_domain FROM atlassian_site_bindings JOIN external_source_instances ON external_source_instances.id=atlassian_site_bindings.source_instance_id JOIN atlassian_sites ON atlassian_sites.id=atlassian_site_bindings.site_id WHERE atlassian_site_bindings.id=? AND atlassian_site_bindings.site_id=?",rusqlite::params![binding,site])?.ok_or_else(||BackendError::invalid("binding-mismatch","선택한 MCP 접근 경로가 현재 Site에 속하지 않습니다."))?;
            service = text(&row, "service").into();
            if state.services.features.external_executor.is_none() {
                return Err(BackendError::invalid(
                    "executor-unavailable",
                    "Approved host-side read executor is not connected",
                ));
            }
            if maintenance::runner_executable(&state.config, runner).is_none() {
                return Err(BackendError::invalid(
                    "runner-unavailable",
                    format!(
                        "{} runner is unavailable",
                        if runner == "claude" {
                            "Claude"
                        } else {
                            "Codex"
                        }
                    ),
                ));
            }
            catalog::prepare_space_catalog_run(
                conn,
                &state.config,
                &json!({"site_id":site,"source_instance_id":row["source_instance_id"],"target_domain":row["normalized_domain"],"runner":runner}),
                None,
            )
        })?;
        super::refresh::start(state, &run)?;
        Ok(run)
    })();
    match result {
        Ok(run) => Ok(transport::redirect(&nav::connections_url(
            nav::view_for_service(&service),
            Some("catalog-started"),
            Some(&run),
            Some("atlassian-catalog-results"),
        ))),
        Err(error) => {
            let raw = text(&fields, "binding_id");
            let id =
                (!raw.is_empty() && raw.len() <= 19 && raw.bytes().all(|ch| ch.is_ascii_digit()))
                    .then(|| raw.parse::<i64>().ok())
                    .flatten()
                    .unwrap_or(-1);
            let authority=database(&state.config,false,|conn|db::row(conn,"SELECT external_source_instances.service FROM atlassian_site_bindings JOIN external_source_instances ON external_source_instances.id=atlassian_site_bindings.source_instance_id WHERE atlassian_site_bindings.id=?",[id]))?.unwrap_or(Value::Null);
            connection_error(
                state,
                request,
                nav::view_for_service(text(&authority, "service")),
                &fields,
                "discovery",
                &error,
                None,
                None,
            )
        }
    }
}
pub fn install(mut router: Router<AppState>) -> Router<AppState> {
    for (path, handler) in [
        ("/atlassian/add", add as crate::routes::Handler),
        ("/atlassian/connections", connections),
        ("/api/atlassian/registration-preview", preview),
    ] {
        router = bind(router, path, MethodFilter::GET, handler, EMPTY);
    }
    for (path, handler) in [
        ("/atlassian/register", register as super::FormHandler),
        ("/atlassian/access", access),
        (
            "/atlassian/connections/{source_instance_id}/sites/{site_id}",
            update,
        ),
        ("/atlassian/spaces/register", candidate),
        ("/atlassian/spaces/discover", discover),
    ] {
        router = form_route(router, path, handler);
    }
    router
}
