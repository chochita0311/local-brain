//! Local previews and explicit, bounded remote refresh composition/application.
mod queries;
use super::{access, browse, catalog, common::*, registration, sync};
use crate::backend::{db, json as codec, BackendError, Config, Result};
use num_bigint::BigInt;
use rusqlite::{params, params_from_iter, Connection};
use serde_json::{json, Map, Number, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::Path,
};
pub const SCOPE_KINDS: &[&str] = &["item", "space", "thread", "workstream", "all_known"];
pub const DEFAULT_SELECTED_FRESHNESS: &[&str] = &["unknown", "due", "stale", "unavailable"];
pub const PRODUCT_CALL_BUDGET: i64 = 20;
pub const CONFLUENCE_CATALOG_LIMIT: usize = 200;
const ITEM_TARGET_PATTERN: &str = r"\Aatlassian-item-([1-9][0-9]*)\z";
const CATALOG_TARGET_PATTERN: &str = r"\Aatlassian-space-catalog-([1-9][0-9]*)-([1-9][0-9]*)\z";
const JIRA_METADATA_FIELDS: &[&str] = &[
    "key",
    "summary",
    "status",
    "issuetype",
    "priority",
    "labels",
    "components",
    "assignee",
    "reporter",
    "created",
    "updated",
    "resolution",
    "project",
    "parent",
];
const CONFLUENCE_METADATA_FIELDS: &[&str] = &["title", "space", "version", "labels", "ancestors"];
fn integer(value: &Value, label: &str) -> Result<Number> {
    let number = python_integer(value, label, true)?;
    if BigInt::parse_bytes(number.to_string().as_bytes(), 10).unwrap() < BigInt::from(1) {
        return Err(fail(
            "invalid-input",
            format!("{label} is outside the supported range"),
        ));
    }
    Ok(number)
}
fn scope_identity(db: &Connection, kind: &str, scope: &Value) -> Result<Value> {
    if !SCOPE_KINDS.contains(&kind) {
        return Err(fail("invalid-scope", "Unsupported Atlassian refresh scope"));
    }
    if kind == "all_known" {
        return Ok(
            json!({"kind":kind,"id":null,"label":"알려진 모든 Atlassian 링크/문서","return_to":"/atlassian"}),
        );
    }
    let number = integer(scope, "scope_id")?;
    let id = sql_integer(&number)?;
    let query = match kind {
        "item" => queries::SCOPE_ITEM,
        "space" => queries::SCOPE_SPACE,
        "thread" => queries::SCOPE_THREAD,
        _ => queries::SCOPE_WORKSTREAM,
    };
    let row = db::row(db, query, [id])?.ok_or_else(|| {
        fail(
            "scope-not-found",
            "The selected refresh scope was not found",
        )
    })?;
    let back = match kind {
        "thread" => format!("/workstreams/{}", python_string(&row["workstream_id"])),
        "workstream" => format!("/workstreams/{number}"),
        _ => "/atlassian".into(),
    };
    Ok(json!({"kind":kind,"id":number,"label":row["title"],"return_to":back}))
}
fn scope_ids(db: &Connection, kind: &str, scope: &Value) -> Result<Vec<i64>> {
    let rows = match kind {
        "item" => return Ok(vec![sql_integer(&integer(scope, "scope_id")?)?]),
        "space" => db::rows(
            db,
            queries::IDS_SPACE,
            [sql_integer(&integer(scope, "scope_id")?)?],
        )?,
        "thread" => db::rows(
            db,
            queries::IDS_THREAD,
            [sql_integer(&integer(scope, "scope_id")?)?],
        )?,
        "workstream" => {
            let id = sql_integer(&integer(scope, "scope_id")?)?;
            db::rows(db, queries::IDS_WORKSTREAM, params![id, id])?
        }
        _ => db::rows(db, queries::IDS_ALL, [])?,
    };
    rows.iter()
        .map(|r| id(&r["external_resource_id"]))
        .collect()
}
fn resolve_access(db: &Connection, site: i64, service: &str) -> Result<Option<Value>> {
    match catalog::resolve_atlassian_site_access(db, site, service, None, true) {
        Ok(value) => Ok(value),
        Err(e) if e.status == 400 => Ok(None),
        Err(e) => Err(e),
    }
}
fn capability(db: &Connection, source: i64) -> Result<String> {
    match access::capability_state(db, source) {
        Ok(state) => Ok(python_string(&state["state"])),
        Err(e) if e.status == 400 => Ok("error".into()),
        Err(e) => Err(e),
    }
}
fn item_rows(db: &Connection, ids: &[i64]) -> Result<Vec<Value>> {
    let mut normalized = vec![];
    for id in ids {
        if !normalized.contains(id) {
            normalized.push(*id);
        }
    }
    if normalized.is_empty() {
        return Ok(vec![]);
    }
    let rows = db::rows(
        db,
        &queries::ITEMS.replace("{}", &vec!["?"; normalized.len()].join(",")),
        params_from_iter(normalized.iter()),
    )?;
    let mut by_id = rows
        .into_iter()
        .map(|row| Ok((id(&row["id"])?, row)))
        .collect::<Result<BTreeMap<_, _>>>()?;
    if by_id.keys().copied().collect::<BTreeSet<_>>() != normalized.iter().copied().collect() {
        return Err(fail(
            "item-not-found",
            "선택한 Atlassian 링크/문서를 찾지 못했습니다",
        ));
    }
    let mut cache = BTreeMap::new();
    let mut items = vec![];
    for id_value in normalized {
        let mut item = by_id.remove(&id_value).unwrap();
        if item["source_instance_id"].is_null() {
            if let Some(access) =
                resolve_access(db, id(&item["site_id"])?, item["service"].as_str().unwrap())?
            {
                item["source_instance_id"] = access["id"].clone();
                item["source_name"] = access["display_name"].clone();
                item["source_enabled"] = access["enabled"].clone();
            }
        }
        let state = if item["source_instance_id"].is_null() {
            "unbound".into()
        } else {
            let source = id(&item["source_instance_id"])?;
            if let std::collections::btree_map::Entry::Vacant(entry) = cache.entry(source) {
                entry.insert(capability(db, source)?);
            }
            cache[&source].clone()
        };
        item["capability_state"] = json!(state);
        item["freshness"] = json!(catalog::derive_atlassian_freshness(
            item["service"].as_str().unwrap(),
            Some(&item),
            None
        )?);
        item["request_count"] = json!(
            if item["service"] == "jira" && item["coverage"] == "indexed" {
                2
            } else {
                1
            }
        );
        item["selectable"] = json!(
            !item["source_instance_id"].is_null()
                && truth(&item["source_enabled"])
                && state == "current"
                && truth(&item["canonical_url"])
        );
        items.push(browse::project_atlassian_item_container(&item)?);
    }
    Ok(items)
}
pub fn refresh_preview(db: &Connection, v: &Value) -> Result<Value> {
    let kind = v["scope_kind"].as_str().unwrap_or("");
    let scope = scope_identity(db, kind, &v["scope_id"])?;
    let page = integer(v.get("page").unwrap_or(&json!(1)), "page")?;
    let mut items = item_rows(db, &scope_ids(db, kind, &v["scope_id"])?)?;
    let selected = if v["selected_ids"].is_null() {
        None
    } else {
        Some(
            v["selected_ids"]
                .as_array()
                .ok_or_else(|| fail("invalid-input", "selected_ids must be iterable"))?
                .iter()
                .map(|n| python_integer(n, "selected_ids", false).map(Value::Number))
                .collect::<Result<Vec<_>>>()?,
        )
    };
    let mut calls = 0;
    for item in &mut items {
        let wants = selected
            .as_ref()
            .map(|ids| ids.contains(&item["id"]))
            .unwrap_or_else(|| {
                item["freshness"]
                    .as_str()
                    .is_some_and(|s| DEFAULT_SELECTED_FRESHNESS.contains(&s))
            });
        let count = id(&item["request_count"])?;
        let fits = calls + count <= PRODUCT_CALL_BUDGET;
        let selected = truth(&item["selectable"]) && wants && fits;
        item["selected"] = json!(selected);
        item["overflow"] = json!(truth(&item["selectable"]) && wants && !fits);
        if selected {
            calls += count;
        }
    }
    let mut catalog = Value::Null;
    if kind == "space" {
        let mut space = required_row(
            db,
            queries::PREVIEW_SPACE,
            [id(&scope["id"])?],
            "scope-not-found",
            "The selected Space was not found",
        )?;
        if space["source_instance_id"].is_null() {
            if let Some(access) = resolve_access(
                db,
                id(&space["site_id"])?,
                space["service"].as_str().unwrap(),
            )? {
                space["source_instance_id"] = access["id"].clone();
                space["source_name"] = access["display_name"].clone();
                space["enabled"] = access["enabled"].clone();
            }
        }
        if space["service"] == "confluence" {
            let state = if space["source_instance_id"].is_null() {
                "unbound".into()
            } else {
                capability(db, id(&space["source_instance_id"])?)?
            };
            let selectable = !space["source_instance_id"].is_null()
                && truth(&space["enabled"])
                && state == "current";
            let selected = selectable && calls < PRODUCT_CALL_BUDGET;
            catalog = json!({"space_id":space["id"],"space_key":space["space_key"],"coverage":space["coverage"],"page":page,"limit":CONFLUENCE_CATALOG_LIMIT,"request_count":1,"capability_state":state,"selectable":selectable,"selected":selected});
            if selected {
                calls += 1;
            }
        }
    }
    Ok(
        json!({"scope":scope,"target_count":items.len(),"selected_count":items.iter().filter(|i|i["selected"]==true).count(),"items":items,"catalog":catalog,"selected_calls":calls,"call_budget":PRODUCT_CALL_BUDGET,"page":page}),
    )
}
fn first<'a>(value: &'a Value, keys: &[&str]) -> &'a Value {
    keys.iter()
        .map(|key| &value[*key])
        .find(|v| truth(v))
        .unwrap_or(&Value::Null)
}
pub fn build_item_refresh_target(item: &Value) -> Result<Value> {
    let item_id = python_integer(&item["id"], "id", false)?;
    let service = item["service"].as_str().unwrap_or("");
    let coverage = item["coverage"].as_str().unwrap_or("");
    let observed = registration::recognize_registration_url(
        item["canonical_url"].as_str().unwrap_or(""),
        Some(service),
    )?;
    let mut requests = vec![];
    let (target_coverage, fields);
    if service == "jira" {
        let key = if truth(&item["remote_key"]) {
            item["remote_key"].as_str()
        } else {
            observed.remote_key.as_deref()
        }
        .filter(|s| !s.is_empty())
        .ok_or_else(|| {
            fail(
                "missing-item-locator",
                "Jira refresh requires a stored issue key",
            )
        })?;
        fields = if coverage == "reference" {
            vec!["key"]
        } else {
            JIRA_METADATA_FIELDS.to_vec()
        };
        requests.push(json!({"request_id":format!("atlassian-item-{item_id}-metadata"),"logical_operation":"jira.search_metadata","arguments":{"jql":format!("key = \"{key}\""),"fields":fields,"limit":1}}));
        target_coverage = if coverage == "indexed" {
            requests.push(json!({"request_id":format!("atlassian-item-{item_id}-content"),"logical_operation":"jira.read_description","arguments":{"issue_key":key}}));
            vec!["metadata", "content"]
        } else {
            vec!["metadata"]
        };
    } else {
        let page = if truth(&item["remote_id"]) {
            item["remote_id"].as_str()
        } else {
            observed.remote_id.as_deref()
        }
        .filter(|s| !s.is_empty())
        .ok_or_else(|| {
            fail(
                "missing-item-locator",
                "Confluence refresh requires a stored Page ID",
            )
        })?;
        fields = CONFLUENCE_METADATA_FIELDS.to_vec();
        target_coverage = if coverage == "indexed" {
            requests.push(json!({"request_id":format!("atlassian-item-{item_id}-content"),"logical_operation":"confluence.read_page","arguments":{"page_id":page}}));
            vec!["metadata", "content", "hierarchy"]
        } else {
            requests.push(json!({"request_id":format!("atlassian-item-{item_id}-metadata"),"logical_operation":"confluence.search_pages","arguments":{"cql":format!("id = \"{page}\" AND type = page"),"limit":1}}));
            vec!["metadata"]
        };
    }
    Ok(
        json!({"target_id":format!("atlassian-item-{item_id}"),"source_instance_id":python_integer(&item["source_instance_id"],"source_instance_id",false)?,"locator":{"kind":"url","value":item["canonical_url"]},"coverage":target_coverage,"field_allowlist":fields,"known":{"remote_version":item["remote_version"],"remote_updated_at":item["remote_updated_at"],"content_hash":item["content_hash"]},"requests":requests}),
    )
}
fn catalog_target(db: &Connection, catalog: &Value) -> Result<Value> {
    let mut space = required_row(
        db,
        queries::CATALOG_SPACE,
        [id(&catalog["space_id"])?],
        "scope-not-found",
        "Confluence Space was not found",
    )?;
    if space["source_instance_id"].is_null() {
        let access =
            resolve_access(db, id(&space["site_id"])?, "confluence")?.ok_or_else(|| {
                fail(
                    "source-instance-unbound",
                    "Confluence Space has no unambiguous access binding",
                )
            })?;
        space["source_instance_id"] = access["id"].clone();
    }
    let page = python_integer(&catalog["page"], "page", false)?;
    let offset = (BigInt::parse_bytes(page.to_string().as_bytes(), 10).unwrap() - BigInt::from(1))
        * BigInt::from(CONFLUENCE_CATALOG_LIMIT);
    let offset = Number::from_string_unchecked(offset.to_string());
    let target = format!(
        "atlassian-space-catalog-{}-{page}",
        python_string(&space["id"])
    );
    Ok(
        json!({"target_id":target,"source_instance_id":space["source_instance_id"],"locator":{"kind":"source_root","value":space["canonical_url"]},"coverage":["metadata"],"field_allowlist":["pages","next_page","complete"],"known":{},"requests":[{"request_id":target,"logical_operation":"confluence.search_pages","arguments":{"cql":format!("space = \"{}\" AND type = page",python_string(&space["space_key"])),"limit":CONFLUENCE_CATALOG_LIMIT,"offset":offset}}]}),
    )
}
pub fn prepare_atlassian_refresh_run(
    db: &Connection,
    config: &Config,
    v: &Value,
    run_root: Option<&Path>,
) -> Result<String> {
    let raw = v["selected_item_ids"]
        .as_array()
        .ok_or_else(|| fail("invalid-input", "selected_item_ids must be iterable"))?;
    let mut selected = vec![];
    for value in raw {
        let value = Value::Number(python_integer(value, "selected_item_ids", false)?);
        if !selected.contains(&value) {
            selected.push(value);
        }
    }
    let kind = v["scope_kind"].as_str().unwrap_or("");
    let preview = refresh_preview(
        db,
        &json!({"scope_kind":kind,"scope_id":v["scope_id"],"page":v.get("page").cloned().unwrap_or(json!(1)),"selected_ids":selected}),
    )?;
    let items = preview["items"].as_array().unwrap();
    if selected
        .iter()
        .any(|id| !items.iter().any(|i| i["id"] == *id))
    {
        return Err(fail(
            "selection-outside-scope",
            "선택한 링크/문서가 Refresh 범위를 벗어났습니다",
        ));
    }
    let mut targets = vec![];
    let mut calls = 0;
    for id in &selected {
        let item = items.iter().find(|i| i["id"] == *id).unwrap();
        if !truth(&item["selectable"]) {
            return Err(fail(
                "target-unavailable",
                "선택한 링크/문서를 현재 연결 상태로 Refresh할 수 없습니다",
            ));
        }
        let target = build_item_refresh_target(item)?;
        calls += target["requests"].as_array().unwrap().len();
        targets.push(target);
    }
    if truth(&v["include_catalog"]) {
        if preview["catalog"].is_null() || !truth(&preview["catalog"]["selectable"]) {
            return Err(fail(
                "catalog-unavailable",
                "The selected Space catalog cannot be refreshed",
            ));
        }
        targets.push(catalog_target(db, &preview["catalog"])?);
        calls += 1;
    }
    if targets.is_empty() {
        return Err(fail(
            "empty-selection",
            "Select at least one refresh target",
        ));
    }
    if calls > PRODUCT_CALL_BUDGET as usize {
        return Err(fail(
            "call-budget-exceeded",
            "Selected targets exceed the 20-call refresh batch",
        ));
    }
    let sources = targets
        .iter()
        .map(|t| id(&t["source_instance_id"]))
        .collect::<Result<BTreeSet<_>>>()?;
    let source = if sources.len() == 1 {
        sources.first().copied()
    } else {
        None
    };
    sync::prepare_external_sync_run(
        db,
        config,
        &json!({"runner":v["runner"].as_str().unwrap_or("claude"),"source_instance_id":source,"source_kind":"atlassian","scope_kind":kind,"targets":targets,"workstream_id":if kind=="workstream"{v["scope_id"].clone()}else{Value::Null},"call_budget":PRODUCT_CALL_BUDGET}),
        run_root,
    )
}
fn application_item(db: &Connection, item: i64) -> Result<Value> {
    let mut row = required_row(
        db,
        queries::APPLICATION_ITEM,
        [item],
        "item-not-found",
        "Refresh result Item was not found",
    )?;
    if row["source_instance_id"].is_null() {
        if let Some(access) =
            resolve_access(db, id(&row["site_id"])?, row["service"].as_str().unwrap())?
        {
            row["source_instance_id"] = access["id"].clone();
        }
    }
    Ok(row)
}
fn reference_safe_result(value: &Value) -> Result<Value> {
    let mut value = value.clone();
    let requests = value["requests"]
        .as_array_mut()
        .ok_or_else(|| fail("invalid-result", "Refresh requests are invalid"))?;
    for request in requests {
        request["metadata"] = json!({});
        request["content"] = Value::Null;
        request["content_hash"] = Value::Null;
    }
    Ok(value)
}
fn apply_catalog(
    db: &Connection,
    target_id: &str,
    target_result: &Value,
    target: &Value,
    checked: &str,
    source: &Value,
) -> Result<i64> {
    let pattern = regex::Regex::new(CATALOG_TARGET_PATTERN).unwrap();
    let captures = pattern
        .captures(target_id)
        .ok_or_else(|| fail("invalid-target", "Catalog target identity is invalid"))?;
    let space_id = sql_integer(
        &integer_text(&captures[1])
            .ok_or_else(|| fail("invalid-target", "Catalog target identity is invalid"))?,
    )?;
    let mut space = required_row(
        db,
        queries::APPLY_SPACE,
        [space_id],
        "scope-not-found",
        "Catalog Space was not found",
    )?;
    if space["source_instance_id"].is_null() {
        let access =
            resolve_access(db, id(&space["site_id"])?, "confluence")?.ok_or_else(|| {
                fail(
                    "source-instance-unbound",
                    "Catalog Space has no unambiguous access binding",
                )
            })?;
        space["source_instance_id"] = access["id"].clone();
    }
    if target.get("source_instance_id").unwrap_or(source) != &space["source_instance_id"] {
        return Err(fail(
            "source-instance-mismatch",
            "Catalog target Source Instance changed",
        ));
    }
    if !["resolved", "unchanged", "changed"]
        .contains(&target_result["outcome"].as_str().unwrap_or(""))
    {
        return Ok(0);
    }
    let mut pages = vec![];
    if let Some(requests) = target_result["requests"].as_array() {
        for request in requests {
            if let Some(values) = request["metadata"]["pages"].as_array() {
                pages.extend(
                    values
                        .iter()
                        .take(CONFLUENCE_CATALOG_LIMIT)
                        .filter(|p| p.is_object()),
                );
            }
        }
    }
    pages.truncate(CONFLUENCE_CATALOG_LIMIT);
    let mut created = 0;
    for page in pages {
        let page_id = first(page, &["id", "remote_id"]);
        if !(page_id.is_string() || page_id.is_boolean() || is_integer(page_id))
            || trim(&python_string(page_id)).is_empty()
        {
            continue;
        }
        let page_id = trim(&python_string(page_id)).to_owned();
        let title = first(page, &["title", "name"]);
        let title = title
            .as_str()
            .map(trim)
            .filter(|s| !s.is_empty())
            .map(ToOwned::to_owned)
            .unwrap_or_else(|| format!("Confluence Page {page_id}"));
        let raw_url = first(page, &["url", "canonical_url"]);
        let url = raw_url
            .as_str()
            .filter(|s| !trim(s).is_empty())
            .map(ToOwned::to_owned)
            .unwrap_or_else(|| {
                format!(
                    "{}/spaces/{}/pages/{page_id}",
                    space["canonical_base_url"]
                        .as_str()
                        .unwrap()
                        .trim_end_matches('/'),
                    python_string(&space["space_key"])
                )
            });
        let normalized = match catalog::normalize_atlassian_url(&url) {
            Ok(value) => value,
            Err(error) if error.status == 400 => continue,
            Err(error) => return Err(error),
        };
        let existing = db::row(
            db,
            queries::APPLY_EXISTING,
            params![id(&space["site_id"])?, normalized.normalized_url],
        )?;
        let item = catalog::create_or_reuse_atlassian_stub(
            db,
            &json!({"source_instance_id":space["source_instance_id"],"url":normalized.normalized_url,"title":title.chars().take(500).collect::<String>()}),
        )?;
        if item["site_id"] != space["site_id"] {
            return Err(fail(
                "site-mismatch",
                "Catalog Page resolved outside the registered Space Site",
            ));
        }
        let item = id(&item["external_resource_id"])?;
        db.execute(
            "UPDATE atlassian_items SET space_id=?,updated_at=? WHERE external_resource_id=?",
            params![space_id, checked, item],
        )?;
        catalog::bind_atlassian_remote_identity(
            db,
            item,
            &json!({"remote_id":page_id,"canonical_url":normalized.normalized_url,"space_id":space_id,"confirmed_at":checked}),
        )?;
        if existing.is_none() {
            catalog::set_atlassian_item_axes(db, item, &json!({"coverage":"indexed"}))?;
            db.execute("INSERT INTO atlassian_item_remote_state(external_resource_id,metadata_json,projection_stale,updated_at) VALUES (?,'{}',1,?) ON CONFLICT(external_resource_id) DO UPDATE SET projection_stale=1,updated_at=excluded.updated_at",params![item,checked])?;
            created += 1;
        }
    }
    Ok(created)
}
pub fn apply_atlassian_refresh_result(
    db: &Connection,
    manifest: &Value,
    result: &Value,
    checked_at: Option<&str>,
) -> Result<Value> {
    if result["schema"] != sync::RESULT_SCHEMA_VERSION {
        return Err(fail(
            "invalid-result",
            "External sync result schema is unsupported",
        ));
    }
    if result["run_id"] != manifest["run_id"] {
        return Err(fail(
            "invalid-result",
            "Refresh result Run ID does not match",
        ));
    }
    let mut manifest_targets = Map::new();
    if let Some(targets) = manifest["targets"].as_array() {
        for target in targets {
            let key = target["target_id"]
                .as_str()
                .ok_or_else(|| fail("invalid-result", "Refresh manifest targets are invalid"))?;
            manifest_targets.insert(key.into(), target.clone());
        }
    }
    let results = result["targets"]
        .as_array()
        .ok_or_else(|| fail("invalid-result", "Refresh result targets are invalid"))?;
    let mut by_id = BTreeMap::new();
    for target in results {
        let key = target["target_id"]
            .as_str()
            .ok_or_else(|| fail("invalid-result", "Refresh result target mapping is invalid"))?;
        if by_id.contains_key(key) || !manifest_targets.contains_key(key) {
            return Err(fail(
                "invalid-result",
                "Refresh result target mapping is invalid",
            ));
        }
        if target["locator"] != manifest_targets[key]["locator"] {
            return Err(fail("invalid-result", "Refresh result locator changed"));
        }
        by_id.insert(key, target);
    }
    if by_id.len() != manifest_targets.len() {
        return Err(fail(
            "invalid-result",
            "Refresh result target set is incomplete",
        ));
    }
    let timestamp = checked_at
        .filter(|s| !s.is_empty())
        .map(ToOwned::to_owned)
        .unwrap_or_else(now);
    atomic(db, "atlassian_refresh_apply", || {
        let mut applied = 0;
        let mut cataloged = 0;
        let item_pattern = regex::Regex::new(ITEM_TARGET_PATTERN).unwrap();
        let catalog_pattern = regex::Regex::new(CATALOG_TARGET_PATTERN).unwrap();
        for (key, target) in manifest_targets {
            let target_result = by_id[key.as_str()];
            if let Some(found) = item_pattern.captures(&key) {
                let item = sql_integer(&integer_text(&found[1]).ok_or_else(|| {
                    fail("invalid-target", "Refresh target type is unsupported")
                })?)?;
                let row = application_item(db, item)?;
                if target
                    .get("source_instance_id")
                    .unwrap_or(&manifest["source"]["instance_id"])
                    != &row["source_instance_id"]
                {
                    return Err(fail(
                        "source-instance-mismatch",
                        "Refresh target Source Instance changed",
                    ));
                }
                if target["locator"]["value"] != row["canonical_url"] {
                    return Err(fail(
                        "locator-mismatch",
                        "Refresh target canonical URL changed",
                    ));
                }
                let safe = if row["coverage"] == "reference" {
                    reference_safe_result(target_result)?
                } else {
                    target_result.clone()
                };
                catalog::apply_atlassian_target_result(db, item, &safe, Some(&timestamp), None)?;
                applied += 1;
            } else if catalog_pattern.is_match(&key) {
                cataloged += apply_catalog(
                    db,
                    &key,
                    target_result,
                    &target,
                    &timestamp,
                    &manifest["source"]["instance_id"],
                )?;
            } else {
                return Err(fail("invalid-target", "Refresh target type is unsupported"));
            }
        }
        Ok(json!({"applied_items":applied,"cataloged_items":cataloged,"checked_at":timestamp}))
    })
}
pub fn is_atlassian_refresh_manifest(manifest: &Value) -> bool {
    manifest["targets"].as_array().is_some_and(|targets| {
        !targets.is_empty()
            && targets.iter().all(|t| {
                t.is_object()
                    && t["target_id"].as_str().is_some_and(|s| {
                        matches(ITEM_TARGET_PATTERN, s) || matches(CATALOG_TARGET_PATTERN, s)
                    })
            })
    })
}
pub fn refresh_run_result(db: &Connection, run: &str) -> Result<Option<Value>> {
    let Some(row) = db::row(db, queries::RUN_RESULT, [run])? else {
        return Ok(None);
    };
    let mut targets = vec![];
    let mut source_scope = None;
    if truth(&row["structured_result_json"]) {
        let text = row["structured_result_json"].as_str().unwrap_or("");
        let scope = codec::Scope::for_document(text);
        let payload = match scope.parse(text) {
            Ok(value) => value,
            Err(error) if error.is_io() => {
                return Err(BackendError::new(500, "json_scalar", error.to_string()))
            }
            Err(_) => json!({}),
        };
        if !payload.is_object() {
            return Err(BackendError::new(
                500,
                "invalid-result",
                "Stored refresh result is not an object",
            ));
        }
        let pattern = regex::Regex::new(ITEM_TARGET_PATTERN).unwrap();
        if let Some(values) = payload["targets"].as_array() {
            for target in values {
                let matched = target["target_id"]
                    .as_str()
                    .and_then(|id| pattern.captures(id));
                let item = matched.and_then(|m| integer_text(&m[1]));
                let mut value = json!({"target_id":null,"item_id":item,"outcome":null});
                value["target_id"] = target["target_id"].clone();
                value["outcome"] = target["outcome"].clone();
                targets.push(value);
            }
        }
        source_scope = Some(scope);
    }
    let retry = targets
        .iter()
        .filter(|t| {
            !t["item_id"].is_null()
                && ["unavailable", "not_found", "error"]
                    .contains(&t["outcome"].as_str().unwrap_or(""))
        })
        .map(|t| t["item_id"].clone())
        .collect::<Vec<_>>();
    let mut value = json!({"run_id":run,"status":row["status"],"scope_kind":row["requested_scope_kind"],"service":row["service"],"targets":[],"retry_item_ids":[]});
    value["targets"] = Value::Array(targets);
    value["retry_item_ids"] = Value::Array(retry);
    if let Some(scope) = source_scope {
        scope.materialized(&value)?;
    }
    Ok(Some(value))
}
