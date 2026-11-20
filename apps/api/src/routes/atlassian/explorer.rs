//! Existing read-first Explorer and explicit persisted local-evidence Sync.
use super::navigation as nav;
use crate::{
    routes::{bind, Params, EMPTY},
    state::{database, AppState},
    transport::{self, ApiError, RequestContext},
};
use axum::{
    extract::{Request, State},
    response::{IntoResponse, Response},
    routing::{post, MethodFilter},
    Router,
};
use localbrain_core::backend::{
    atlassian::{browse, evidence_sync},
    search, BackendError, Result,
};
use rusqlite::Connection;
use serde_json::{json, Value};
use std::collections::BTreeMap;
const PARTIAL: &str = "X-LocalBrain-Partial";
const SYNC_PARTIAL: &str = "atlassian-local-evidence-sync";
fn invalid_selection() -> BackendError {
    BackendError::new(
        400,
        "invalid-selection",
        "Atlassian 선택은 한 번에 하나만 지정할 수 있습니다.",
    )
}
fn is_browse_error(error: &BackendError) -> bool {
    ["invalid-filter", "invalid-query", "invalid-selection"].contains(&error.code.as_str())
}
#[cfg(test)]
fn value<'a>(value: &'a Value, key: &str) -> &'a str {
    value[key].as_str().unwrap_or("")
}
pub(super) fn fields(request: &RequestContext) -> Result<Value> {
    let mut values = json!({});
    for field in nav::BROWSE_FIELDS {
        values[*field] = request
            .query
            .get(*field)
            .map(|v| json!(v))
            .unwrap_or(Value::Null);
    }
    if request.parameter("q").chars().count() > 300 {
        return Err(BackendError::new(
            422,
            "query",
            "Query exceeds 300 characters",
        ));
    }
    for field in [
        "source_instance_id",
        "site_id",
        "space_id",
        "topic_id",
        "tag_id",
        "workstream_id",
    ] {
        if let Some(raw) = request.query.get(field) {
            values[field] = typed_query_integer(raw, field)?;
        }
    }
    Ok(values)
}
// FastAPI/Pydantic integer query grammar differs from the domain's int(value):
// HTTP accepts ASCII integral decimal suffixes; Unicode decimal digits stay a
// domain-only admission. Big positive integers retain lexical identity until
// Browse's explicit SQLite-range refusal.
fn http_integer(raw: &str) -> Option<String> {
    let raw = raw.trim();
    let negative = raw.starts_with('-');
    let unsigned = raw.strip_prefix(['+', '-']).unwrap_or(raw);
    let (integer, fraction) = unsigned
        .split_once('.')
        .map(|(i, f)| (i, Some(f)))
        .unwrap_or((unsigned, None));
    if fraction.is_some_and(|f| f.is_empty() || !f.bytes().all(|b| b == b'0'))
        || integer.is_empty()
        || integer
            .split('_')
            .any(|p| p.is_empty() || !p.bytes().all(|b| b.is_ascii_digit()))
    {
        return None;
    }
    let digits = integer.replace('_', "");
    if digits.len() > 4300 {
        return None;
    }
    let digits = digits.trim_start_matches('0');
    if digits.is_empty() {
        Some("0".into())
    } else {
        Some(format!("{}{digits}", if negative { "-" } else { "" }))
    }
}
fn typed_query_integer(raw: &str, field: &str) -> Result<Value> {
    let invalid = || BackendError::new(422, "query", format!("Invalid query parameter: {field}"));
    let digits = http_integer(raw)
        .filter(|s| s != "0" && !s.starts_with('-'))
        .ok_or_else(invalid)?;
    Ok(match digits.parse::<i64>() {
        Ok(value) => json!(value),
        Err(_) => json!(digits),
    })
}
fn path_integer(params: &Params, field: &str) -> Result<String> {
    params
        .get(field)
        .and_then(|raw| http_integer(raw))
        .ok_or_else(|| BackendError::new(422, "path", format!("Invalid path parameter: {field}")))
}
fn normalize_filters(db: &Connection, view: &str, values: &Value) -> Result<Value> {
    let mut values = values.clone();
    values["service"] = nav::service(view);
    browse::normalize_browse_structure(db, &browse::normalize_browse_filters(&values)?)
}
pub(super) fn inventory_return_path(
    db: &Connection,
    value: Option<&str>,
    post_sync: bool,
) -> Result<String> {
    let Some(input) = value.filter(|v| !v.is_empty() && v.chars().count() <= 4000) else {
        return Ok("/atlassian".into());
    };
    let Some((path, query)) = nav::relative_parts(input) else {
        return Ok("/atlassian".into());
    };
    if path != "/atlassian" || nav::repeated_state(&query) {
        return Ok("/atlassian".into());
    }
    let raw = url::form_urlencoded::parse(query.as_bytes())
        .map(|(k, v)| (k.into_owned(), v.into_owned()))
        .collect::<BTreeMap<_, _>>();
    let view = nav::normalize_view(raw.get("view").map(String::as_str).unwrap_or("all"));
    let mut values = json!({});
    for field in nav::BROWSE_FIELDS {
        values[*field] = raw.get(*field).map(|v| json!(v)).unwrap_or(Value::Null);
    }
    let result = (|| -> Result<String> {
        let mut filters = normalize_filters(db, &view, &values)?;
        let item = nav::selection(raw.get("item").map(String::as_str), false)?;
        let reference = nav::selection(raw.get("reference").map(String::as_str), true)?;
        if item.is_some() && reference.is_some() {
            return Err(invalid_selection());
        }
        if !(post_sync && reference.is_some()) {
            browse::validate_browse_structural_scope(db, &filters)?;
        }
        if let Some(reference) = reference.filter(|_| post_sync) {
            let Some(reference) = browse::atlassian_structure_reference_detail(db, reference)?
            else {
                return Ok("/atlassian".into());
            };
            let expected = nav::service(&view);
            if !expected.is_null() && reference["service"] != expected {
                return Ok("/atlassian".into());
            }
            filters["space_id"] = Value::Null;
            if reference["lifecycle"] == "archived" {
                filters["site_id"] = Value::Null;
                filters["structural_scope"] = Value::Null;
            } else {
                filters["site_id"] = reference["site_id"].clone();
                filters["structural_scope"] = reference["container_structural_scope"].clone();
            }
        }
        Ok(nav::browse_url(
            &view,
            &filters,
            &[("item", json!(item)), ("reference", json!(reference))],
        ))
    })();
    match result {
        Err(error) if is_browse_error(&error) => Ok("/atlassian".into()),
        other => other,
    }
}
pub(super) fn add_return_path(db: &Connection, value: Option<&str>) -> Result<String> {
    let fallback = "/atlassian#atlassian-add-action";
    let Some((path, query)) = nav::relative_parts(value.unwrap_or("")) else {
        return Ok(fallback.into());
    };
    if path != "/atlassian"
        || url::form_urlencoded::parse(query.as_bytes())
            .any(|(key, _)| key != "view" && !nav::EXPLORER_FIELDS.contains(&key.as_ref()))
    {
        return Ok(fallback.into());
    }
    Ok(format!(
        "{}#atlassian-add-action",
        inventory_return_path(db, value, false)?
    ))
}
fn preview_context(
    db: &Connection,
    view: &str,
    filters: &Value,
    item: Option<i64>,
    reference: Option<i64>,
) -> Result<Value> {
    let clear = nav::browse_url(
        view,
        filters,
        &[("item", Value::Null), ("reference", Value::Null)],
    );
    let kind = if item.is_some() {
        Some("item")
    } else {
        reference.map(|_| "reference")
    };
    let selected = item.or(reference);
    let mut context = json!({"state":"empty","selection_kind":kind,"selected_key":kind.zip(selected).map(|(kind,id)|format!("{kind}:{id}")),"selected_id":selected,"item":null,"reference":null,"entry":null,"clear_url":clear,"selected_url":null,"detail_url":null,"refresh_url":null,"document_title":"Atlassian · LocalBrain"});
    let Some(selected) = selected else {
        return Ok(context);
    };
    let mut values = filters.clone();
    values["service"] = nav::service(&nav::normalize_view(view));
    let is_reference = reference.is_some();
    let selected_url = nav::browse_url(
        view,
        filters,
        &[
            (
                "item",
                if is_reference {
                    Value::Null
                } else {
                    json!(selected)
                },
            ),
            (
                "reference",
                if is_reference {
                    json!(selected)
                } else {
                    Value::Null
                },
            ),
        ],
    );
    let record = if is_reference {
        browse::atlassian_structure_reference_preview(db, selected, &values)?
    } else {
        browse::atlassian_item_preview(db, selected, &values)?
    };
    let exists = record.is_some();
    let record = record.unwrap_or(Value::Null);
    context["state"] = json!(if !exists {
        "missing"
    } else if is_reference && record["lifecycle"] == "archived" {
        "archived"
    } else if record["eligible"] == true {
        "selected"
    } else {
        "out_of_scope"
    });
    context[if is_reference { "reference" } else { "item" }] = record.clone();
    context["entry"] = record.clone();
    context["selected_url"] = json!(selected_url);
    context["detail_url"] = if exists {
        json!(format!(
            "/atlassian/{}/{selected}?{}",
            if is_reference { "references" } else { "items" },
            search::urlencode(&[("return_to", selected_url.clone())])
        ))
    } else {
        Value::Null
    };
    context["document_title"] = if exists {
        json!(format!(
            "{} · Atlassian · LocalBrain",
            nav::scalar(&record["display_title"])
        ))
    } else {
        json!(if is_reference {
            "Atlassian 구조 참조를 찾지 못함 · LocalBrain"
        } else {
            "Atlassian 링크/문서를 찾지 못함 · LocalBrain"
        })
    };
    if !is_reference && exists {
        context["refresh_url"] = json!(format!(
            "/atlassian/refresh?{}",
            search::urlencode(&[
                ("scope", "item".into()),
                ("id", selected.to_string()),
                ("return_to", selected_url)
            ])
        ));
    }
    Ok(context)
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
fn page_context(
    state: &AppState,
    db: &Connection,
    view: &str,
    values: &Value,
    item: Option<i64>,
    reference: Option<i64>,
    notice: Option<&str>,
    receipt: Option<&str>,
) -> Result<Value> {
    let mut filters = values.clone();
    filters["service"] = nav::service(view);
    let mut inventory = browse::browse_inventory(db, &filters)?;
    let explorer_urls = nav::explorer_urls(&mut inventory, view);
    let filters = inventory["filters"].clone();
    let return_url = nav::browse_url(view, &filters, &[]);
    let mut updated = BTreeMap::new();
    for entry in inventory["entries"].as_array_mut().unwrap() {
        let is_ref = entry["entity_kind"] == "reference";
        let selected_url = nav::browse_url(
            view,
            &filters,
            &[
                (
                    "item",
                    if is_ref {
                        Value::Null
                    } else {
                        entry["id"].clone()
                    },
                ),
                (
                    "reference",
                    if is_ref {
                        entry["id"].clone()
                    } else {
                        Value::Null
                    },
                ),
            ],
        );
        entry["selection_url"] = json!(selected_url);
        entry["detail_url"] = json!(format!(
            "/atlassian/{}/{}?{}",
            if is_ref { "references" } else { "items" },
            entry["id"],
            search::urlencode(&[("return_to", selected_url)])
        ));
        entry["selected"] = json!(entry["id"].as_i64() == if is_ref { reference } else { item });
        updated.insert((is_ref, entry["id"].as_i64().unwrap()), entry.clone());
    }
    for (field, is_ref) in [("items", false), ("references", true)] {
        for entry in inventory[field].as_array_mut().unwrap() {
            if let Some(updated) = updated.get(&(is_ref, entry["id"].as_i64().unwrap())) {
                *entry = updated.clone();
            }
        }
    }
    let mut preview = preview_context(db, view, &filters, item, reference)?;
    if preview["state"] == "selected"
        && !inventory["entries"]
            .as_array()
            .unwrap()
            .iter()
            .any(|entry| entry["selected"] == true)
    {
        preview["state"] = json!("out_of_scope");
        preview["entry"]["eligible"] = json!(false);
        let key = if reference.is_some() {
            "reference"
        } else {
            "item"
        };
        preview[key]["eligible"] = json!(false);
    }
    let sync_return = nav::browse_url(
        view,
        &filters,
        &[("item", json!(item)), ("reference", json!(reference))],
    );
    let add_return = add_return_path(db, Some(&sync_return))?;
    let sync_report = state
        .atlassian_sync_receipts
        .as_ref()
        .and_then(|store| store.report(receipt, &sync_return));
    let mut context = json!({"active_page":"atlassian","selected_view":view,"browse":null,"explorer_urls":explorer_urls,"return_url":return_url,"preview":null,"page_title":preview["document_title"],"item_count":inventory["known_count"],"notice":nav::notice(notice),"add_return_to":add_return,"add_url":format!("/atlassian/add?{}",search::urlencode(&[("return_to",add_return)])),"connections_url":nav::connections_url(if view=="all"{"jira"}else{view},None,None,None),"add_form_state":{},"add_form_error":null,"sync_return_to":sync_return,"sync_report":sync_report});
    context["browse"] = inventory;
    context["preview"] = preview;
    Ok(context)
}
fn vary(mut response: Response) -> Response {
    response
        .headers_mut()
        .insert("vary", PARTIAL.parse().unwrap());
    response
}
fn page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    if nav::repeated_state(request.uri.query().unwrap_or("")) {
        return Err(BackendError::new(
            400,
            "invalid-state",
            "Explorer state fields must not be repeated",
        ));
    }
    let values = fields(request)?;
    if request.parameter("mode") == "setup" {
        if request.parameter("method") == "connected" {
            return Ok(transport::redirect(&nav::connections_url(
                request.parameter("view"),
                request.query.get("notice").map(String::as_str),
                request.query.get("catalog_run").map(String::as_str),
                None,
            )));
        }
        let mut pairs = vec![(
            "view",
            request
                .query
                .get("view")
                .cloned()
                .unwrap_or_else(|| "all".into()),
        )];
        for key in nav::EXPLORER_FIELDS {
            if let Some(value) = request.query.get(*key).filter(|s| !s.is_empty()) {
                pairs.push((*key, value.clone()));
            }
        }
        let candidate = format!("/atlassian?{}", search::urlencode(&pairs));
        let target = database(&state.config, false, |db| {
            add_return_path(db, Some(&candidate))
        })?;
        return Ok(transport::redirect(&format!(
            "/atlassian/add?{}",
            search::urlencode(&[("return_to", target)])
        )));
    }
    let view = nav::normalize_view(
        request
            .query
            .get("view")
            .map(String::as_str)
            .unwrap_or("all"),
    );
    let item = nav::selection(request.query.get("item").map(String::as_str), false)?;
    let reference = nav::selection(request.query.get("reference").map(String::as_str), true)?;
    if item.is_some() && reference.is_some() {
        return Err(invalid_selection());
    }
    database(&state.config, false, |db| {
        if ["atlassian-selection-preview", "atlassian-item-preview"]
            .contains(&request.header(PARTIAL))
        {
            let filters = normalize_filters(db, &view, &values)?;
            browse::validate_browse_structural_scope(db, &filters)?;
            let preview = preview_context(db, &view, &filters, item, reference)?;
            let mut context = json!({});
            context["preview"] = preview;
            return Ok(vary(state.render(
                request,
                "_atlassian-item-preview.html",
                context,
                200,
            )?));
        }
        let context = page_context(
            state,
            db,
            &view,
            &values,
            item,
            reference,
            request.query.get("notice").map(String::as_str),
            request.query.get("sync_receipt").map(String::as_str),
        )?;
        Ok(vary(state.render(
            request,
            "atlassian.html",
            context,
            200,
        )?))
    })
}
pub(super) fn item_context(
    db: &Connection,
    resource: i64,
    return_to: Option<&str>,
    notice: Option<&str>,
) -> Result<Value> {
    let item = browse::atlassian_item_detail(db, resource)?
        .ok_or_else(|| BackendError::not_found("Atlassian 링크/문서를 찾을 수 없습니다"))?;
    let safe = inventory_return_path(db, return_to, false)?;
    let notice = match notice {
        Some("local-saved") => Some("로컬 메모와 분류를 저장했습니다."),
        Some("linked") => Some("기존 Workstream 관계를 추가했습니다."),
        Some("unlinked") => Some("로컬 Workstream 관계를 제거했습니다."),
        _ => None,
    };
    let mut context = json!({"active_page":"atlassian","item":null,"return_to":safe,"refresh_url":format!("/atlassian/refresh?{}",search::urlencode(&[("scope","item".into()),("id",resource.to_string()),("return_to",safe)])),"notice":notice,"form_error":null});
    context["item"] = item;
    Ok(context)
}
fn item_page(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    _: &[u8],
) -> Result<Response> {
    let resource = path_integer(params, "item_id")?
        .parse::<i64>()
        .map_err(|_| BackendError::not_found("Atlassian 링크/문서를 찾을 수 없습니다"))?;
    let context = database(&state.config, false, |db| {
        item_context(
            db,
            resource,
            request.query.get("return_to").map(String::as_str),
            request.query.get("notice").map(String::as_str),
        )
    })?;
    state.render(request, "atlassian-item.html", context, 200)
}
fn reference_page(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    _: &[u8],
) -> Result<Response> {
    let reference = path_integer(params, "reference_id")?
        .parse::<i64>()
        .map_err(|_| {
            BackendError::new(
                500,
                "database",
                "Python int too large to convert to SQLite INTEGER",
            )
        })?;
    let (reference, safe) = database(&state.config, false, |db| {
        Ok((
            browse::atlassian_structure_reference_detail(db, reference)?,
            inventory_return_path(
                db,
                request.query.get("return_to").map(String::as_str),
                false,
            )?,
        ))
    })?;
    let exists = reference.is_some();
    state.render(
        request,
        if exists {
            "atlassian-reference.html"
        } else {
            "atlassian-reference-missing.html"
        },
        json!({"active_page":"atlassian","reference":reference,"return_to":safe}),
        if exists { 200 } else { 404 },
    )
}
fn form_error(message: &str) -> BackendError {
    BackendError::new(422, "invalid-form", message)
        .with_details(json!({"code":"invalid-form","message":message}))
}
fn sync_form(request: &RequestContext, bytes: Option<&[u8]>) -> Result<String> {
    if !request
        .content_type()
        .eq_ignore_ascii_case("application/x-www-form-urlencoded")
    {
        return Err(form_error("Form encoding is unsupported"));
    }
    let bytes = bytes.ok_or_else(|| form_error("Form is too large"))?;
    let text = std::str::from_utf8(bytes).map_err(|_| form_error("Form data is invalid"))?;
    transport::form(bytes, 2, &Default::default(), None, true, true)
        .map_err(|_| form_error("Form data is invalid"))?;
    let pairs = url::form_urlencoded::parse(text.as_bytes()).collect::<Vec<_>>();
    if pairs.len() != 1 || pairs[0].0 != "return_to" {
        return Err(form_error("Sync requires exactly one return_to field"));
    }
    if pairs[0].1.chars().count() > 4000 {
        return Err(form_error("return_to is too large"));
    }
    Ok(pairs[0].1.to_string())
}
fn synchronize(
    state: &AppState,
    request: &RequestContext,
    bytes: Option<&[u8]>,
) -> Result<Response> {
    let enhanced = request.header(PARTIAL) == SYNC_PARTIAL;
    let requested = match sync_form(request, bytes) {
        Ok(value) => value,
        Err(error) => {
            return if enhanced {
                Ok(vary(ApiError(error).into_response()))
            } else {
                Err(error)
            }
        }
    };
    let safe = database(&state.config, false, |db| {
        inventory_return_path(db, Some(&requested), false)
    })?;
    let report = database(
        &state.config,
        false,
        evidence_sync::sync_atlassian_local_evidence,
    )?;
    let safe = database(&state.config, false, |db| {
        inventory_return_path(db, Some(&safe), true)
    })?;
    if enhanced {
        let status = if report["status"] == "busy" { 409 } else { 200 };
        let mut response = crate::routes::json_response(json!({"report":report,"return_to":safe}))?;
        *response.status_mut() = axum::http::StatusCode::from_u16(status).unwrap();
        return Ok(vary(response));
    }
    let receipt = state
        .atlassian_sync_receipts
        .as_ref()
        .ok_or_else(|| BackendError::unavailable("Atlassian Sync receipts unavailable"))?
        .store(&report, &safe)?;
    Ok(transport::redirect(&nav::receipt_url(&safe, &receipt)))
}
async fn sync(State(state): State<AppState>, request: Request) -> Response {
    let context = match RequestContext::new(
        request.method().clone(),
        request.headers().clone(),
        request.uri().clone(),
    ) {
        Ok(value) => value,
        Err(error) => return ApiError(error).into_response(),
    };
    let bytes = transport::bounded_body(request.into_body(), 8192)
        .await
        .ok();
    match state
        .blocking(move |state| synchronize(&state, &context, bytes.as_deref()))
        .await
    {
        Ok(response) => response,
        Err(error) => error.into_response(),
    }
}
pub fn install(mut router: Router<AppState>) -> Router<AppState> {
    router = bind(router, "/atlassian", MethodFilter::GET, page, EMPTY);
    router = bind(
        router,
        "/atlassian/items/{item_id}",
        MethodFilter::GET,
        item_page,
        EMPTY,
    );
    router = bind(
        router,
        "/atlassian/references/{reference_id}",
        MethodFilter::GET,
        reference_page,
        EMPTY,
    );
    router.route("/atlassian/sync", post(sync))
}

#[cfg(test)]
#[path = "../../../../../crates/core/tests/native_atlassian_support/mod.rs"]
mod proof_support;
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn explorer_contexts_and_return_canonicalizers_match_complete_frozen_browser_calls() {
        let root = tempfile::tempdir_in("/private/tmp").unwrap();
        let config = localbrain_core::backend::Config::for_data_dir(root.path().join("data"));
        std::fs::create_dir_all(&config.home_dir).unwrap();
        let bindings = crate::state::FeatureBindings::for_config(&config).unwrap();
        let state =
            AppState::initialize(config, "synthetic-explorer-token".into(), bindings).unwrap();
        let cases: Vec<Value> = serde_json::from_str(include_str!(
            "../../../tests/fixtures/native-atlassian-explorer.json"
        ))
        .unwrap();
        assert_eq!(cases.len(), 39);
        proof_support::replay(&cases, |db, operation, values| match operation {
            "_atlassian_inventory_return_path" => Ok(json!(inventory_return_path(
                db,
                values["value"].as_str(),
                values["post_sync"].as_bool().unwrap_or(false)
            )?)),
            "_atlassian_add_return_path" => {
                Ok(json!(add_return_path(db, values["value"].as_str())?))
            }
            "_atlassian_preview_context" => preview_context(
                db,
                value(values, "selected_view"),
                &values["filters"],
                values["selected_item_id"].as_i64(),
                values["selected_reference_id"].as_i64(),
            ),
            "_atlassian_page_context" => page_context(
                &state,
                db,
                value(values, "selected_view"),
                &values["browse_values"],
                values["selected_item_id"].as_i64(),
                values["selected_reference_id"].as_i64(),
                values["notice"].as_str(),
                values["sync_receipt"].as_str(),
            ),
            _ => panic!("unknown explorer fixture {operation}"),
        });
        state.services.stop().unwrap();
    }
}
