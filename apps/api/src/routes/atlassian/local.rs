use super::{explorer, form_route, integer, invalid, optional, text};
use crate::{
    routes::{identifier, Params},
    state::{database, AppState},
    transport::{self, RequestContext},
};
use axum::{response::Response, Router};
use localbrain_core::backend::{
    atlassian::browse, db, search, unicode, workstreams, BackendError, Result,
};
use serde_json::{json, Value};
fn item_redirect(id: i64, notice: &str, return_to: &str) -> Response {
    transport::redirect(&format!(
        "/atlassian/items/{id}?{}#local-organization",
        search::urlencode(&[("notice", notice.into()), ("return_to", return_to.into())])
    ))
}
fn change(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    form: Result<Value>,
) -> Result<Response> {
    let id = identifier(params, "item_id")?;
    let mut fields = json!({});
    let mut return_to = "/atlassian".into();
    let local = request.path.ends_with("/local");
    let remove = params.contains_key("link_id");
    let result = (|| {
        fields = form?;
        database(&state.config, true, |conn| {
            return_to =
                explorer::inventory_return_path(conn, optional(&fields, "return_to"), false)?;
            if local {
                let topics = fields["topic_id"]
                    .as_array()
                    .map(Vec::as_slice)
                    .unwrap_or(&[])
                    .iter()
                    .map(|value| integer(value.as_str(), "Topic"))
                    .collect::<Result<Vec<_>>>()?
                    .into_iter()
                    .flatten()
                    .collect::<Vec<_>>();
                browse::update_atlassian_local_state(
                    conn,
                    id,
                    &json!({"note":text(&fields,"note"),"attention":optional(&fields,"attention").unwrap_or("normal"),"topic_ids":topics,"tags":text(&fields,"tags"),"new_topic_name":text(&fields,"new_topic_name"),"new_topic_description":text(&fields,"new_topic_description")}),
                )?;
            } else {
                if browse::atlassian_item_detail(conn, id)?.is_none() {
                    return Err(BackendError::invalid(
                        "item-not-found",
                        "Atlassian 링크/문서를 찾을 수 없습니다",
                    ));
                }
                if remove {
                    let kind = &params["scope_type"];
                    let scope = identifier(params, "scope_id")?;
                    let link = identifier(params, "link_id")?;
                    let table = match kind.as_str() {
                        "workstream" => Some(("workstream_links", "workstream_id")),
                        "thread" => Some(("thread_links", "thread_id")),
                        _ => None,
                    };
                    let exists = if let Some((table, column)) = table {
                        db::row(conn,&format!("SELECT 1 FROM {table} WHERE id=? AND {column}=? AND entity_type='external' AND entity_id=?"),rusqlite::params![link,scope,id.to_string()])?.is_some()
                    } else {
                        false
                    };
                    if !exists {
                        return Err(BackendError::invalid(
                            "link-not-found",
                            "The selected local relation was not found",
                        ));
                    }
                    workstreams::remove_link(conn, kind, scope, link)?;
                } else {
                    let (kind, raw) = text(&fields, "target").split_once(':').ok_or_else(|| {
                        invalid("not enough values to unpack (expected 2, got 1)")
                    })?;
                    let scope = integer(Some(raw), "Link target")?;
                    if !["workstream", "thread"].contains(&kind) || scope.is_none() {
                        return Err(BackendError::invalid(
                            "invalid-link",
                            "Select a Workstream or Thread",
                        ));
                    }
                    workstreams::add_link(
                        conn,
                        &state.config,
                        kind,
                        scope.unwrap(),
                        "external",
                        &id.to_string(),
                        "reference",
                        "user",
                        None,
                    )?;
                }
            }
            Ok(())
        })
    })();
    match result {
        Ok(()) => Ok(item_redirect(
            id,
            if local {
                "local-saved"
            } else if remove {
                "unlinked"
            } else {
                "linked"
            },
            &return_to,
        )),
        Err(error) if error.status < 500 => {
            let mut context = database(&state.config, false, |conn| {
                explorer::item_context(conn, id, Some(&return_to), None)
            })?;
            context["form_error"] = json!(error.message);
            if local {
                let item = &mut context["item"];
                item["note"] =
                    json!(optional(&fields, "note").unwrap_or(item["note"].as_str().unwrap_or("")));
                if let Some(attention) = optional(&fields, "attention") {
                    item["attention"] = json!(attention);
                }
                item["selected_topic_ids"] = json!(fields["topic_id"]
                    .as_array()
                    .map(Vec::as_slice)
                    .unwrap_or(&[])
                    .iter()
                    .filter_map(|value| integer(value.as_str(), "Topic").ok().flatten())
                    .collect::<std::collections::BTreeSet<_>>());
                item["tags"] = json!(text(&fields, "tags")
                    .split(',')
                    .map(|value| value.trim_matches(unicode::python_space))
                    .filter(|value| !value.is_empty())
                    .map(|value| json!({"name":value}))
                    .collect::<Vec<_>>());
            }
            state.render(request, "atlassian-item.html", context, 422)
        }
        Err(error) => Err(error),
    }
}
pub fn install(mut router: Router<AppState>, workstreams: bool) -> Router<AppState> {
    router = form_route(router, "/atlassian/items/{item_id}/local", change);
    if workstreams {
        router = form_route(router, "/atlassian/items/{item_id}/links", change);
        router = form_route(
            router,
            "/atlassian/items/{item_id}/links/{scope_type}/{scope_id}/{link_id}",
            change,
        );
    }
    router
}
