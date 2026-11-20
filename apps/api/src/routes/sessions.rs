use super::{bind, identifier, json_response, BodyLimit, Params, EMPTY};
use crate::{
    state::{database, immediate, AppState},
    transport::{self, RequestContext},
};
use axum::{http::StatusCode, response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{
    db,
    resources::related_context,
    search,
    sessions::{self, dashboard, reading, subagents},
    sources::profiles,
    unicode, BackendError, Result,
};
use serde_json::{json, Value};
use std::collections::BTreeSet;

fn query(request: &RequestContext, name: &str, default: &str) -> String {
    request
        .query
        .get(name)
        .cloned()
        .unwrap_or_else(|| default.into())
}
fn workspace(request: &RequestContext) -> Result<Option<i64>> {
    request
        .query
        .get("workspace")
        .map(|_| request.integer("workspace", 0))
        .transpose()
}
fn page_integer(value: &str) -> Option<i64> {
    let value = value.trim_matches(unicode::python_space);
    let (negative, value) = if let Some(value) = value.strip_prefix('-') {
        (true, value)
    } else {
        (false, value.strip_prefix('+').unwrap_or(value))
    };
    let mut previous = false;
    let mut result = 0i64;
    let mut digits = 0;
    for ch in value.chars() {
        if ch == '_' {
            if !previous {
                return None;
            }
            previous = false;
            continue;
        }
        let digit = profiles::decimal_integer(&ch.to_string())?;
        digits += 1;
        if digits > 4300 {
            return None;
        }
        result = result.saturating_mul(10).saturating_add(digit);
        previous = true;
    }
    (digits > 0 && previous).then_some(if negative { -result } else { result })
}
fn url(path: &str, pairs: &[(&str, String)]) -> String {
    if pairs.is_empty() {
        path.into()
    } else {
        format!("{path}?{}", search::urlencode(pairs))
    }
}
fn inventory(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let projects_page = request.path == "/projects";
    let display = if !projects_page && request.parameter("display") == "chart" {
        "chart"
    } else {
        "list"
    };
    let source = if projects_page {
        "all".into()
    } else {
        profiles::canonical_source_id(&query(request, "source", "all"))
    };
    let workspace = if projects_page {
        None
    } else {
        workspace(request)?
    };
    let requested = if projects_page {
        Some(1)
    } else {
        page_integer(&query(request, "page", "1"))
    };
    let (data, redirect) = database(&state.config, false, |conn| {
        let scopes = sessions::session_source_scopes(conn)?;
        let valid_source = source == "all"
            || scopes.iter().any(|scope| {
                scope["id"].as_i64().map(|id| id.to_string()).as_deref() == Some(&source)
            });
        let valid_workspace = workspace.is_none()
            || db::row(conn, "SELECT 1 FROM workspaces WHERE id=?", [workspace])?.is_some();
        if !valid_source || !valid_workspace {
            let mut pairs = vec![];
            if display == "chart" {
                pairs.push(("display", "chart".into()));
            }
            if valid_source && source != "all" {
                pairs.push(("source", source.clone()));
            }
            if valid_workspace {
                if let Some(workspace) = workspace {
                    pairs.push(("workspace", workspace.to_string()));
                }
            }
            return Ok((Value::Null, Some(url("/sessions", &pairs))));
        }
        let selected = (source != "all").then_some(source.as_str());
        let projects = sessions::project_activity(conn, selected)?;
        let page =
            sessions::session_inventory_page(conn, selected, workspace, requested.unwrap_or(1))?;
        if !projects_page
            && request.query.contains_key("page")
            && (requested.is_none_or(|page| page <= 0) || requested != page["page"].as_i64())
        {
            let mut pairs = vec![("page", page["page"].to_string())];
            if display == "chart" {
                pairs.push(("display", "chart".into()));
            }
            if let Some(selected) = selected {
                pairs.push(("source", selected.into()));
            }
            if let Some(workspace) = workspace {
                pairs.push(("workspace", workspace.to_string()));
            }
            return Ok((Value::Null, Some(url("/sessions", &pairs))));
        }
        let pinned = sessions::list_all_pinned_sessions(conn)?;
        let mut preference = json!({"hidden_projects":null,"available":true});
        if display == "chart" {
            match sessions::get_project_visibility(conn, &source, workspace) {
                Ok(hidden) => preference["hidden_projects"] = json!(hidden),
                Err(_) => preference["available"] = json!(false),
            }
        }
        let mut chart = if display == "chart" {
            sessions::session_chart_inventory(conn, &state.config, selected, workspace)?
        } else {
            vec![]
        };
        let metadata = profiles::profile_map(conn)?;
        for item in &mut chart {
            let key = item["source_id"].to_string();
            let profile = metadata.get(&key);
            item["color"] = profile
                .map(|profile| profile["color"].clone())
                .unwrap_or_else(|| json!("gray"));
            if let Some(profile) = profile {
                item["source_id"] = profile["id"].clone();
            }
        }
        let label = selected
            .and_then(|selected| {
                scopes.iter().find(|scope| {
                    scope["id"].as_i64().map(|id| id.to_string()).as_deref() == Some(selected)
                })
            })
            .map(|scope| scope["display_label"].clone())
            .unwrap_or_else(|| json!("전체"));
        let missing = projects
            .iter()
            .filter(|project| project["exists_now"] == 0)
            .count();
        let sync = request.parameter("sync");
        Ok((
            json!({"active_page":"sessions","selected_inventory":if projects_page{"projects"}else{"sessions"},"selected_display":display,"chart_project_preference":preference,"chart_sessions":chart,"page_title":if projects_page{"Projects"}else{"Sessions"},"selected_source":source,"selected_source_label":label,"selected_workspace":workspace,"stats":dashboard::dashboard_stats(conn,selected)?,"sessions":page["items"],"pagination":page,"pinned_sessions":pinned,"pinned_session_groups":sessions::group_pinned_sessions(&pinned,&state.config),"sources":dashboard::source_inventory(conn)?,"session_source_scopes":scopes,"projects":projects,"project_count":projects.len(),"missing_count":missing,"sync_outcome":(["complete","partial","failed"].contains(&sync).then_some(sync))}),
            None,
        ))
    })?;
    if let Some(location) = redirect {
        Ok(transport::redirect(&location))
    } else {
        state.render(request, "sessions.html", data, 200)
    }
}
fn navigation(
    conn: &rusqlite::Connection,
    request: &RequestContext,
) -> Result<(String, Option<i64>, String)> {
    let source = profiles::canonical_source_id(&query(request, "source", "all"));
    let valid = sessions::session_source_scopes(conn)?
        .iter()
        .any(|scope| scope["id"].as_i64().map(|id| id.to_string()).as_deref() == Some(&source));
    let source = if valid { source } else { "all".into() };
    let workspace = workspace(request)?;
    let workspace = if workspace.is_some()
        && db::row(conn, "SELECT 1 FROM workspaces WHERE id=?", [workspace])?.is_none()
    {
        None
    } else {
        workspace
    };
    let mut pairs = vec![];
    if source != "all" {
        pairs.push(("source", source.clone()));
    }
    if let Some(workspace) = workspace {
        pairs.push(("workspace", workspace.to_string()));
    }
    let query = if pairs.is_empty() {
        String::new()
    } else {
        format!("?{}", search::urlencode(&pairs))
    };
    Ok((source, workspace, query))
}
fn show(state: &AppState, request: &RequestContext, params: &Params, _: &[u8]) -> Result<Response> {
    let id = identifier(params, "session_id")?;
    let mut data = database(&state.config, false, |conn| {
        let session = sessions::session_detail(conn, id)?
            .ok_or_else(|| BackendError::not_found("Session not found"))?;
        let (source, workspace, navigation) = navigation(conn, request)?;
        let mut list = format!("/sessions{navigation}");
        if request.parameter("display") == "chart" {
            let mut pairs = vec![("display", "chart".into())];
            if source != "all" {
                pairs.push(("source", source.clone()));
            }
            if let Some(workspace) = workspace {
                pairs.push(("workspace", workspace.to_string()));
            }
            let page = query(request, "page", "1");
            if page.chars().all(unicode::python_digit)
                && page_integer(&page).is_some_and(|page| page > 1)
            {
                pairs.push(("page", page));
            }
            list = url("/sessions", &pairs);
        }
        let events =
            reading::conversation_event_views(&sessions::session_conversation_events(conn, id)?)?;
        let parent = sessions::session_parent(conn, id)?;
        let mut children = sessions::session_subsessions(conn, id)?;
        for child in &mut children {
            child["url"] = json!(format!("/sessions/{}{navigation}", child["id"]));
        }
        let mut related = Value::Null;
        let mut workflow = false;
        if session["session_role"] == "primary" {
            if !state.config.desktop {
                workflow = state
                    .services
                    .features
                    .workflow_eligible
                    .map(|eligible| eligible(conn, id))
                    .transpose()?
                    .unwrap_or(false);
            }
            related = related_context::session_related_context(conn, id)
                .unwrap_or_else(|_| related_context::session_related_context_error());
            if session["provider_kind"] == "claude" {
                let paths = children
                    .iter()
                    .filter_map(|child| child["source_path"].as_str())
                    .map(ToOwned::to_owned)
                    .collect::<BTreeSet<_>>();
                let external = children
                    .iter()
                    .filter_map(|child| child["external_id"].as_str())
                    .map(ToOwned::to_owned)
                    .collect::<BTreeSet<_>>();
                for mut child in subagents::list_subagents(
                    session["source_path"].as_str().unwrap(),
                    session["external_id"].as_str(),
                )
                .unwrap_or_default()
                {
                    if paths.contains(child["source_path"].as_str().unwrap())
                        || external.contains(child["external_id"].as_str().unwrap())
                    {
                        continue;
                    }
                    child["url"] = json!(format!(
                        "/sessions/{id}/subsessions/{}{navigation}",
                        search::quote(child["file_name"].as_str().unwrap())
                    ));
                    for key in ["source_id", "provider_kind", "source_name"] {
                        child[key] = session[key].clone();
                    }
                    children.push(child);
                }
            }
        }
        Ok(
            json!({"active_page":"sessions","short_session_id":sessions::session_id_prefix(conn,session["external_id"].as_str().unwrap())?,"session":session,"events":events,"parent":parent,"subsessions":children,"related_context":related,"selected_source":source,"selected_workspace":workspace,"navigation_query":navigation,"workflow_available":workflow,"session_list_url":list,"parent_url":parent.as_ref().map(|parent|format!("/sessions/{}{navigation}",parent["id"]))}),
        )
    })?;
    data["search_return"] = json!(request
        .query
        .get("search_return")
        .filter(|s| !s.is_empty())
        .map(|s| search::presentation::safe_return(s)));
    state.render(request, "session.html", data, 200)
}
fn child(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    _: &[u8],
) -> Result<Response> {
    let id = identifier(params, "session_id")?;
    let name = params.get("file_name").unwrap();
    let (session, children, source, workspace, navigation) =
        database(&state.config, false, |conn| {
            let session = sessions::session_detail(conn, id)?
                .filter(|session| {
                    session["provider_kind"] == "claude" && session["session_role"] == "primary"
                })
                .ok_or_else(|| BackendError::not_found("Parent session not found"))?;
            let (source, workspace, navigation) = navigation(conn, request)?;
            Ok((
                session,
                sessions::session_subsessions(conn, id)?,
                source,
                workspace,
                navigation,
            ))
        })?;
    let child = subagents::load_subagent(session["source_path"].as_str().unwrap(), name)?
        .filter(|child| child.parent_external_id.as_deref() == session["external_id"].as_str())
        .ok_or_else(|| BackendError::not_found("Subsession not found"))?;
    if let Some(normalized) = children.iter().find(|item| {
        item["source_path"] == child.source_path || item["external_id"] == child.external_id
    }) {
        return Ok(transport::redirect(&format!(
            "/sessions/{}{navigation}",
            normalized["id"]
        )));
    }
    let mut events = child
        .events
        .iter()
        .filter(|event| event.event_type == "message")
        .cloned()
        .collect::<Vec<_>>();
    events.sort_by_key(|event| event.sequence);
    let events = events
        .iter()
        .map(|event| serde_json::to_value(event).map_err(BackendError::from))
        .collect::<Result<Vec<_>>>()?;
    state.render(request,"subsession.html",json!({"active_page":"sessions","session":session,"subsession":child,"events":reading::conversation_event_views(&events)?,"event_count":child.events.len(),"file_name":name,"selected_source":source,"selected_workspace":workspace,"navigation_query":navigation,"session_list_url":format!("/sessions{navigation}"),"parent_url":format!("/sessions/{id}{navigation}")}),200)
}
fn legacy(_: &AppState, _: &RequestContext, params: &Params, _: &[u8]) -> Result<Response> {
    let mut response = transport::redirect(&format!(
        "/sessions/{}/subsessions/{}",
        identifier(params, "session_id")?,
        search::quote(params.get("file_name").unwrap())
    ));
    *response.status_mut() = StatusCode::PERMANENT_REDIRECT;
    Ok(response)
}
fn pin_destination(value: &str, id: i64, error: Option<&str>) -> String {
    let value = value.split('#').next().unwrap_or("");
    let (path, query) = value.split_once('?').unwrap_or((value, ""));
    let detail = path
        .strip_prefix("/sessions/")
        .is_some_and(|id| !id.is_empty() && id.chars().all(unicode::python_digit));
    let valid = path == "/sessions" || path == "/projects" || detail;
    let path = if valid { path } else { "/sessions" };
    let mut pairs = if valid {
        url::form_urlencoded::parse(query.as_bytes())
            .filter(|(key, _)| !["pin_error", "pin_session"].contains(&key.as_ref()))
            .map(|(key, value)| (key.into_owned(), value.into_owned()))
            .collect::<Vec<_>>()
    } else {
        vec![]
    };
    if let Some(error) = error {
        pairs.extend([
            ("pin_error".into(), error.into()),
            ("pin_session".into(), id.to_string()),
        ]);
    }
    let query = url::form_urlencoded::Serializer::new(String::new())
        .extend_pairs(pairs)
        .finish();
    format!(
        "{path}{}#session-pin-{id}",
        if query.is_empty() {
            String::new()
        } else {
            format!("?{query}")
        }
    )
}
fn pin(state: &AppState, _: &RequestContext, params: &Params, body: &[u8]) -> Result<Response> {
    let id = identifier(params, "session_id")?;
    let action = params.get("action").map(String::as_str).unwrap_or("pin");
    let body = String::from_utf8_lossy(&body[..body.len().min(4096)]);
    let destination = url::form_urlencoded::parse(body.as_bytes())
        .find(|(key, _)| key == "return_to")
        .map(|(_, value)| value.into_owned())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "/sessions".into());
    let result = database(&state.config, true, |conn| {
        if action == "unpin" {
            sessions::unpin_session(conn, id).map(|_| ())
        } else {
            sessions::pin_session(conn, id, None).map(|_| ())
        }
    });
    let error = match result {
        Ok(()) => None,
        Err(ref error) if error.code == "database" => Some("storage-unavailable"),
        Err(ref error) if error.code == "session-not-found" => Some("missing"),
        Err(_) => Some("ineligible"),
    };
    Ok(transport::redirect(&pin_destination(
        &destination,
        id,
        error,
    )))
}
fn pin_action(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    body: &[u8],
) -> Result<Response> {
    let mut params = params.clone();
    params.insert(
        "action".into(),
        if request.path.ends_with("/unpin") {
            "unpin"
        } else {
            "pin"
        }
        .into(),
    );
    pin(state, request, &params, body)
}
fn submission(request: &RequestContext, content_type: &str) -> Result<()> {
    if request
        .header("sec-fetch-site")
        .eq_ignore_ascii_case("cross-site")
        || (!request.header("origin").is_empty() && !request.same_origin())
    {
        return Err(BackendError::invalid(
            "origin",
            "Same-origin submission required",
        ));
    }
    if !request.content_type().eq_ignore_ascii_case(content_type) {
        return Err(BackendError::new(
            415,
            "encoding",
            if content_type == "application/json" {
                "JSON submission required"
            } else {
                "Form submission required"
            },
        ));
    }
    Ok(())
}
fn title(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    body: &[u8],
) -> Result<Response> {
    submission(request, "application/x-www-form-urlencoded")?;
    let invalid = || BackendError::invalid("form", "Invalid title submission");
    let text = std::str::from_utf8(body).map_err(|_| invalid())?;
    if !text.is_empty() && text.split('&').count() > 4 {
        return Err(invalid());
    }
    let pairs = url::form_urlencoded::parse(text.as_bytes()).collect::<Vec<_>>();
    let titles = pairs
        .iter()
        .filter(|(key, _)| key == "display_title")
        .collect::<Vec<_>>();
    if titles.len() != 1
        || pairs
            .iter()
            .any(|(key, _)| !["display_title", "return_to"].contains(&key.as_ref()))
    {
        return Err(invalid());
    }
    let id = identifier(params, "session_id")?;
    let saved = immediate(&state.config, |conn| {
        sessions::set_display_title(conn, id, &json!(titles[0].1))
    })
    .map_err(|error| {
        if error.code == "database" {
            BackendError::unavailable("제목을 저장하지 못했습니다. 다시 시도해 주세요.")
        } else if error.code == "session-not-found" {
            BackendError::not_found(error.code)
        } else {
            error
        }
    })?;
    if request.header("accept").contains("application/json") {
        return json_response(saved);
    }
    let destination = pairs
        .iter()
        .find(|(key, _)| key == "return_to")
        .map(|(_, value)| value.as_ref())
        .unwrap_or("/sessions");
    let destination = pin_destination(destination, id, None);
    Ok(transport::redirect(&format!(
        "{}#session-title-{id}",
        destination.split('#').next().unwrap()
    )))
}
fn visibility(
    state: &AppState,
    request: &RequestContext,
    _: &Params,
    body: &[u8],
) -> Result<Response> {
    submission(request, "application/json")?;
    let invalid = || BackendError::invalid("project-visibility", "Invalid Project preferences");
    let payload = transport::json_object(body, 400, "Invalid Project preferences")
        .map_err(|error| error.0)?;
    if payload
        .as_object()
        .unwrap()
        .keys()
        .any(|key| !["hidden_projects", "only_if_missing"].contains(&key.as_str()))
    {
        return Err(invalid());
    }
    let keys =
        sessions::validate_hidden_projects(&payload["hidden_projects"]).map_err(|_| invalid())?;
    let missing = payload
        .get("only_if_missing")
        .cloned()
        .unwrap_or(json!(false))
        .as_bool()
        .ok_or_else(invalid)?;
    let source = profiles::canonical_source_id(&query(request, "source", "all"));
    let workspace = workspace(request)?;
    let hidden = database(&state.config, true, |conn| {
        if source != "all"
            && !sessions::session_source_scopes(conn)?.iter().any(|item| {
                item["id"].as_i64().map(|id| id.to_string()).as_deref() == Some(&source)
            })
        {
            return Err(BackendError::invalid("scope", "Invalid source scope"));
        }
        if workspace.is_some()
            && db::row(conn, "SELECT 1 FROM workspaces WHERE id=?", [workspace])?.is_none()
        {
            return Err(BackendError::invalid("scope", "Invalid workspace scope"));
        }
        sessions::set_project_visibility(conn, &source, workspace, &json!(keys), missing)
    })
    .map_err(|error| {
        if error.code == "database" || error.code == "project-visibility" {
            BackendError::unavailable("Project preferences unavailable")
        } else {
            error
        }
    })?;
    json_response(json!({"hidden_projects":hidden}))
}
fn activity(state: &AppState, _: &RequestContext, params: &Params, _: &[u8]) -> Result<Response> {
    json_response(
        database(&state.config, false, |conn| {
            sessions::session_chart_activity(conn, identifier(params, "session_id")?)
        })?
        .ok_or_else(|| BackendError::not_found("Session not found"))?,
    )
}
pub fn install(mut router: Router<AppState>) -> Router<AppState> {
    for (path, handler) in [
        ("/sessions", inventory as super::Handler),
        ("/projects", inventory),
        ("/sessions/{session_id}", show),
        ("/sessions/{session_id}/chart-activity", activity),
        ("/sessions/{session_id}/subsessions/{file_name}", child),
        ("/sessions/{session_id}/subagents/{file_name}", legacy),
    ] {
        router = bind(router, path, MethodFilter::GET, handler, EMPTY);
    }
    for path in ["/sessions/{session_id}/pin", "/sessions/{session_id}/unpin"] {
        router = bind(
            router,
            path,
            MethodFilter::POST,
            pin_action,
            BodyLimit {
                status: 413,
                bytes: 160 * 1024,
                message: "Form is too large",
            },
        );
    }
    router = bind(
        router,
        "/sessions/{session_id}/title",
        MethodFilter::POST,
        title,
        BodyLimit {
            status: 413,
            bytes: 16_384,
            message: "Title submission is too large",
        },
    );
    bind(
        router,
        "/sessions/chart/project-visibility",
        MethodFilter::PUT,
        visibility,
        BodyLimit {
            status: 413,
            bytes: 65_536,
            message: "Project preferences are too large",
        },
    )
}
