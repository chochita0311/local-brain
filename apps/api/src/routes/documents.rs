use super::{bind, identifier, json_response, BodyLimit, Params, EMPTY};
use crate::{
    state::{database, immediate, AppState},
    transport::{self, RequestContext},
};
use axum::{response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{
    contexts, db,
    ingest::{self, ScanControl},
    search, storage, BackendError, Result,
};
use serde_json::json;
fn optional_id(request: &RequestContext, key: &str) -> Result<Option<i64>> {
    if request.query.contains_key(key) {
        Ok(Some(request.integer(key, 0)?))
    } else {
        Ok(None)
    }
}
fn page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let root = optional_id(request, "root")?;
    let document = optional_id(request, "document")?;
    let data = database(&state.config, false, |conn| {
        let sources = contexts::service::list_context_sources(conn, &state.config)?;
        let selected = sources
            .iter()
            .find(|source| source["id"].as_i64() == root)
            .or(sources.first())
            .cloned();
        let mut doc = if let Some(id) = document.filter(|id| *id != 0) {
            contexts::queries::document_detail(conn, id)?
        } else {
            None
        };
        if doc
            .as_ref()
            .zip(selected.as_ref())
            .is_some_and(|(doc, source)| doc["context_root_id"] != source["id"])
        {
            doc = None;
        }
        if selected
            .as_ref()
            .is_some_and(|source| source["source_type"] == "file")
            && doc.is_none()
        {
            if let Some(first) = db::row(
                conn,
                "SELECT id FROM context_documents WHERE context_root_id = ? LIMIT 1",
                [selected.as_ref().unwrap()["id"].as_i64()],
            )? {
                doc = contexts::queries::document_detail(conn, first["id"].as_i64().unwrap())?;
            }
        }
        let doc = doc
            .as_ref()
            .map(|doc| contexts::service::context_document_preview(conn, doc))
            .transpose()?;
        let tree = if let Some(selected) = &selected {
            contexts::service::context_source_tree(
                conn,
                selected["id"].as_i64().unwrap(),
                doc.as_ref().and_then(|doc| doc["id"].as_i64()),
            )?
        } else {
            vec![]
        };
        let folders = sources
            .iter()
            .filter(|source| {
                matches!(
                    source["source_type"].as_str(),
                    Some("folder" | "apple_notes")
                )
            })
            .cloned()
            .collect::<Vec<_>>();
        let files = sources
            .iter()
            .filter(|source| source["source_type"] == "file")
            .cloned()
            .collect::<Vec<_>>();
        Ok(
            json!({"active_page":"context","selected_source":selected,"selected_document":doc,"tree":tree,"folders":folders,"files":files,"has_apple_notes":sources.iter().any(|source|source["source_type"]=="apple_notes"),"document_count":sources.iter().filter_map(|source|source["document_count"].as_i64()).sum::<i64>(),"source_count":sources.len(),"total_bytes":sources.iter().filter_map(|source|source["total_bytes"].as_i64()).sum::<i64>()}),
        )
    })?;
    state.render(request, "context.html", data, 200)
}
fn show(state: &AppState, request: &RequestContext, params: &Params, _: &[u8]) -> Result<Response> {
    let id = identifier(params, "document_id")?;
    let mut reader = database(&state.config, false, |conn| {
        let document = contexts::queries::document_detail(conn, id)?
            .ok_or_else(|| BackendError::not_found("Document not found"))?;
        let mut reader = contexts::service::context_document_reader(conn, &document)?;
        reader["memberships"] = json!(
            if let Some(memberships) = state.services.features.memberships {
                memberships(conn, "document", id)?
            } else {
                vec![]
            }
        );
        Ok(reader)
    })?;
    reader["active_page"] = json!("context");
    reader["search_return"] = json!(request
        .query
        .get("search_return")
        .filter(|value| !value.is_empty())
        .map(|value| search::presentation::safe_return(value)));
    state.render(request, "document.html", reader, 200)
}
fn add_source(
    state: &AppState,
    _: &RequestContext,
    params: &Params,
    body: &[u8],
) -> Result<Response> {
    let kind = params.get("kind").map(String::as_str).unwrap_or("folder");
    let payload = if kind == "apple_notes" {
        json!({})
    } else {
        transport::json_object(body, 422, "Invalid request body").map_err(|error| error.0)?
    };
    let path = if kind == "apple_notes" {
        ""
    } else {
        payload["path"]
            .as_str()
            .filter(|path| (1..=4000).contains(&path.chars().count()))
            .ok_or_else(|| {
                BackendError::new(
                    422,
                    "path",
                    "Path must contain between 1 and 4000 characters",
                )
            })?
    };
    let _lease = storage::operation_lock(&state.config, "context-settings")?;
    let (id, report) = database(&state.config, true, |conn| {
        let id = match kind {
            "file" => contexts::service::add_context_file(conn, &state.config, path)?,
            "apple_notes" => contexts::service::add_apple_notes_source(conn)?,
            _ => contexts::service::add_context_root(conn, &state.config, path)?,
        };
        let report = ingest::scan_context_root(
            conn,
            &state.config,
            id,
            true,
            &ScanControl::default(),
            state.services.observer.as_ref(),
        )?;
        Ok((id, report))
    })?;
    json_response(
        json!({"ok":true,"id":id,"report":{"imported":report[0],"skipped":report[1],"failed":report[2]},"redirect":format!("/context?root={id}")}),
    )
}
fn folder(state: &AppState, request: &RequestContext, _: &Params, body: &[u8]) -> Result<Response> {
    add_source(
        state,
        request,
        &Params::from([("kind".into(), "folder".into())]),
        body,
    )
}
fn file(state: &AppState, request: &RequestContext, _: &Params, body: &[u8]) -> Result<Response> {
    add_source(
        state,
        request,
        &Params::from([("kind".into(), "file".into())]),
        body,
    )
}
fn notes(state: &AppState, request: &RequestContext, _: &Params, body: &[u8]) -> Result<Response> {
    add_source(
        state,
        request,
        &Params::from([("kind".into(), "apple_notes".into())]),
        body,
    )
}
fn reorder(state: &AppState, _: &RequestContext, _: &Params, body: &[u8]) -> Result<Response> {
    let payload =
        transport::json_object(body, 422, "Invalid request body").map_err(|error| error.0)?;
    let ids = |key: &str| {
        payload[key]
            .as_array()
            .filter(|items| items.len() <= 10000)
            .ok_or_else(|| BackendError::new(422, "order", "Invalid source identifiers"))
            .and_then(|items| {
                items
                    .iter()
                    .map(|item| {
                        item.as_i64().ok_or_else(|| {
                            BackendError::new(422, "order", "Invalid source identifier")
                        })
                    })
                    .collect::<Result<Vec<_>>>()
            })
    };
    let sources = ids("source_ids")?;
    let expected = ids("expected_source_ids")?;
    let _lease = storage::operation_lock(&state.config, "context-settings")?;
    immediate(&state.config, |conn| {
        contexts::service::reorder_context_sources(conn, &sources, &expected)
    })?;
    json_response(json!({"ok":true}))
}
fn remove(state: &AppState, _: &RequestContext, params: &Params, _: &[u8]) -> Result<Response> {
    let id = identifier(
        params,
        if params.contains_key("root_id") {
            "root_id"
        } else {
            "source_id"
        },
    )?;
    let _lease = storage::operation_lock(&state.config, "context-settings")?;
    database(&state.config, true, |conn| {
        contexts::service::remove_context_root(conn, id, state.services.observer.as_ref())
    })?;
    json_response(json!({"ok":true}))
}
pub fn install(mut router: Router<AppState>) -> Router<AppState> {
    let limit = BodyLimit {
        status: 413,
        bytes: 2 * 1024 * 1024,
        message: "Request body is too large",
    };
    for (path, handler) in [
        ("/context", page as super::Handler),
        ("/documents/{document_id}", show),
    ] {
        router = bind(router, path, MethodFilter::GET, handler, EMPTY);
    }
    for (path, handler) in [
        ("/api/context-roots", folder as super::Handler),
        ("/api/context-files", file),
        ("/api/context-sources/apple-notes", notes),
        ("/api/context-sources/order", reorder),
    ] {
        router = bind(router, path, MethodFilter::POST, handler, limit);
    }
    for path in [
        "/api/context-roots/{root_id}",
        "/api/context-sources/{source_id}",
    ] {
        router = bind(router, path, MethodFilter::DELETE, remove, limit);
    }
    router
}
