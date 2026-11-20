//! Explicit local registration and optional connected catalog composition.
mod locator;
mod queries;
use super::{access, catalog, common::*, sync};
use crate::backend::{db, json as codec, unicode, Config, Result};
use locator::{bootstrap_title, bounded, instance_key_base};
pub use locator::{recognize_registration_url, RegistrationLocator};
use rusqlite::{params, Connection};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, path::Path};
pub const CATALOG_MAX_CANDIDATES: usize = 200;
pub fn provider_label(kind: &str) -> &str {
    match kind {
        "atlassian_cloud" => "공식 Atlassian MCP",
        "mcp_gateway" => "회사 MCP Gateway",
        _ => kind,
    }
}
fn service(value: &str) -> Result<()> {
    if !catalog::SERVICES.contains(&value) {
        return Err(fail("invalid-service", "Unsupported Atlassian service"));
    }
    Ok(())
}
pub fn registration_sites(db: &Connection, service_name: &str) -> Result<Vec<Value>> {
    service(service_name)?;
    let mut rows = db::rows(db, queries::SITES, [service_name])?;
    for item in &mut rows {
        let state = match access::capability_state(db, id(&item["source_instance_id"])?) {
            Ok(state) => state,
            Err(error) if error.status == 400 => json!({"state":"error","checked_at":null}),
            Err(error) => return Err(error),
        };
        item["capability_state"] = state["state"].clone();
        item["capability_availability"] = state["availability"].clone();
        item["capability_checked_at"] = state["checked_at"].clone();
        item["provider_label"] = json!(provider_label(item["provider_kind"].as_str().unwrap()));
    }
    Ok(rows)
}
pub fn registration_preview(_db: &Connection, v: &Value) -> Result<Value> {
    let url = v["url"]
        .as_str()
        .ok_or_else(|| fail("invalid-url", "Atlassian URL is invalid"))?;
    let locator = recognize_registration_url(url, v["expected_service"].as_str())?;
    Ok(
        json!({"service":locator.service,"kind":locator.kind,"normalized_url":locator.normalized_url,"normalized_domain":locator.normalized_domain,"identifier":locator.remote_key.or(locator.remote_id).or(locator.space_key)}),
    )
}
fn new_instance_key(
    db: &Connection,
    provider: &str,
    service: &str,
    domain: &str,
    reference: Option<&str>,
) -> Result<String> {
    let base = instance_key_base(provider, service, domain);
    let compatible = |value: &Value| {
        value["provider_kind"] == provider
            && value["service"] == service
            && value["config_ref"] == json!(reference)
    };
    let get = |key: &str| {
        db::row(db,"SELECT provider_kind,service,config_ref FROM external_source_instances WHERE instance_key=?",[key])
    };
    if get(&base)?.as_ref().is_none_or(compatible) {
        return Ok(base);
    }
    let hash = format!(
        "{:x}",
        Sha256::digest(
            format!(
                "{provider}|{service}|{domain}|{}",
                reference.filter(|s| !s.is_empty()).unwrap_or("unbound")
            )
            .as_bytes()
        )
    );
    let candidate = format!(
        "{}-{}",
        base.chars()
            .take(119)
            .collect::<String>()
            .trim_end_matches('-'),
        &hash[..8]
    );
    if get(&candidate)?.as_ref().is_some_and(|v| !compatible(v)) {
        return Err(fail(
            "source-key-collision",
            "A compatible local Source Instance key could not be generated",
        ));
    }
    Ok(candidate)
}
pub fn register_atlassian_site_access(db: &Connection, v: &Value) -> Result<Value> {
    let name = v["service"].as_str().unwrap_or("");
    service(name)?;
    let provider = v["provider_kind"].as_str().unwrap_or("");
    if !["atlassian_cloud", "mcp_gateway"].contains(&provider) {
        return Err(fail(
            "invalid-provider",
            "Select an official Atlassian MCP or company MCP Gateway access path",
        ));
    }
    let reference = bounded(&v["config_ref"], "config_ref", 300, false)?.unwrap();
    let site = id(&v["site_id"])?;
    let row = required_row(
        db,
        "SELECT * FROM atlassian_sites WHERE id=?",
        [site],
        "site-not-found",
        "Atlassian Site does not exist",
    )?;
    let existing=db::rows(db,"SELECT * FROM external_source_instances WHERE provider_kind=? AND service=? AND config_ref=? ORDER BY id",params![provider,name,reference])?;
    if existing.len() > 1 {
        return Err(fail(
            "ambiguous-source",
            "More than one Source Instance owns this access reference",
        ));
    }
    atomic(db, "atlassian_site_access_setup", || {
        let created = existing.is_empty();
        let source = if let Some(source) = existing.first() {
            if !truth(&source["enabled"]) {
                return Err(fail(
                    "source-instance-disabled",
                    "The matching access path is disabled",
                ));
            }
            source.clone()
        } else {
            let domain = row["normalized_domain"].as_str().unwrap();
            let key = new_instance_key(db, provider, name, domain, Some(&reference))?;
            access::register_source_instance(
                db,
                &json!({"instance_key":key,"provider_kind":provider,"service":name,"display_name":format!("{} · {domain}",provider_label(provider)),"config_ref":reference}),
            )?
        };
        let source = id(&source["id"])?;
        let before = db::row(
            db,
            "SELECT id FROM atlassian_site_bindings WHERE site_id=? AND source_instance_id=?",
            params![site, source],
        )?;
        let binding = catalog::bind_atlassian_site_access(db, site, source)?;
        for table in ["atlassian_items", "atlassian_spaces"] {
            db.execute(&format!("UPDATE {table} SET source_instance_id=?,updated_at=? WHERE site_id=? AND service=? AND source_instance_id IS NULL AND NOT EXISTS (SELECT 1 FROM atlassian_site_bindings AS other_binding JOIN external_source_instances AS other_source ON other_source.id=other_binding.source_instance_id WHERE other_binding.site_id=? AND other_source.service=? AND other_binding.source_instance_id!=?)"),params![source,now(),site,name,site,name,source])?;
        }
        Ok(
            json!({"binding_id":binding["binding_id"],"site_id":site,"source_instance_id":source,"source_created":created,"binding_created":before.is_none(),"service":name}),
        )
    })
}
pub fn update_atlassian_connection(db: &Connection, v: &Value) -> Result<Value> {
    let source = id(&v["source_instance_id"])?;
    let site = id(&v["site_id"])?;
    let row = required_row(
        db,
        queries::CONNECTION,
        params![source, site],
        "connection-not-found",
        "The selected Source Instance/Site does not exist",
    )?;
    let reference = bounded(&v["config_ref"], "config_ref", 300, true)?;
    atomic(db, "atlassian_connection_edit", || {
        let mut current = row["config_ref"].clone();
        if !current.is_null() && reference.as_ref().is_some_and(|s| current != *s) {
            return Err(fail(
                "source-instance-identity-conflict",
                "A bound connection reference cannot be changed",
            ));
        }
        if current.is_null() {
            if let Some(reference) = reference.as_deref() {
                current = access::bind_source_instance_config_ref(db, source, &json!(reference))?
                    ["config_ref"]
                    .clone();
            }
        }
        let source = access::register_source_instance(
            db,
            &json!({"instance_key":row["instance_key"],"provider_kind":row["provider_kind"],"service":row["service"],"display_name":row["display_name"],"config_ref":current,"enabled":v["enabled"]}),
        )?;
        let site = required_row(
            db,
            "SELECT * FROM atlassian_sites WHERE id=?",
            [site],
            "site-not-found",
            "Atlassian Site does not exist",
        )?;
        Ok(
            json!({"source_instance_id":source["id"],"binding_id":row["binding_id"],"site_id":site["id"],"service":source["service"],"enabled":truth(&source["enabled"]),"config_bound":!source["config_ref"].is_null()}),
        )
    })
}
pub fn resolve_registration_site(
    db: &Connection,
    locator: &RegistrationLocator,
    site: Option<i64>,
) -> Result<Value> {
    let mut rows=db::rows(db,"SELECT atlassian_sites.* FROM atlassian_sites WHERE atlassian_sites.normalized_domain=? ORDER BY atlassian_sites.id",[&locator.normalized_domain])?;
    let mut row = if let Some(site) = site {
        let mut selected = rows.into_iter().filter(|r| r["id"] == site);
        let row = selected
            .next()
            .ok_or_else(|| fail("site-mismatch", "The selected Site does not own this URL"))?;
        if selected.next().is_some() {
            return Err(fail(
                "site-mismatch",
                "The selected Site does not own this URL",
            ));
        }
        row
    } else if rows.is_empty() {
        catalog::register_atlassian_site(db, &json!({"base_url":locator.normalized_url}))?
    } else {
        rows.remove(0)
    };
    row["service"] = json!(locator.service);
    Ok(row)
}
pub fn register_atlassian_url(db: &Connection, v: &Value) -> Result<Value> {
    let locator = recognize_registration_url(v["url"].as_str().unwrap_or(""), None)?;
    let title = bounded(&v["title"], "title", 500, true)?
        .unwrap_or_else(|| bootstrap_title(&locator).chars().take(500).collect());
    let site = if v["site_id"].is_null() {
        None
    } else {
        Some(id(&v["site_id"])?)
    };
    atomic(db, "atlassian_url_registration", || {
        let site = resolve_registration_site(db, &locator, site)?;
        let site_id = id(&site["id"])?;
        if locator.kind == "item" {
            let before=db::row(db,"SELECT atlassian_items.external_resource_id FROM atlassian_item_urls JOIN atlassian_items ON atlassian_items.external_resource_id=atlassian_item_urls.external_resource_id WHERE atlassian_item_urls.site_id=? AND atlassian_item_urls.normalized_url=?",params![site_id,locator.normalized_url])?;
            let item = catalog::create_or_reuse_atlassian_stub(
                db,
                &json!({"source_instance_id":v["source_instance_id"],"url":locator.normalized_url,"service":locator.service,"site_id":site_id,"title":title}),
            )?;
            Ok(
                json!({"kind":"item","created":before.is_none(),"id":item["external_resource_id"],"site_id":item["site_id"],"space_id":item["space_id"],"attention":item["attention"],"service":locator.service,"canonical_url":locator.normalized_url}),
            )
        } else {
            let existing=db::row(db,"SELECT id,canonical_url FROM atlassian_spaces WHERE site_id=? AND service=? AND space_key=?",params![site_id,locator.service,locator.space_key])?;
            if existing
                .as_ref()
                .is_some_and(|r| r["canonical_url"] != locator.normalized_url)
            {
                return Err(fail(
                    "space-url-conflict",
                    "This Space key is already registered from a different URL",
                ));
            }
            let space = catalog::register_atlassian_space(
                db,
                &json!({"site_id":site_id,"service":locator.service,"source_instance_id":v["source_instance_id"],"name":title,"space_key":locator.space_key,"canonical_url":locator.normalized_url}),
            )?;
            Ok(
                json!({"kind":"space","created":existing.is_none(),"id":space["id"],"site_id":space["site_id"],"service":locator.service}),
            )
        }
    })
}
pub fn registration_inventory(db: &Connection, name: &str) -> Result<Value> {
    let mut items = db::rows(db, queries::INVENTORY_ITEMS, [name])?;
    for item in &mut items {
        item["freshness"] = json!(catalog::derive_atlassian_freshness(name, Some(item), None)?);
    }
    Ok(json!({"items":items,"spaces":db::rows(db,queries::INVENTORY_SPACES,[name])?}))
}
pub fn registered_scope_overview(db: &Connection, name: &str) -> Result<Vec<Value>> {
    service(name)?;
    let connections = registration_sites(db, name)?;
    let rows = db::rows(db, queries::SCOPE_SITES, params![name, name, name])?;
    let spaces = db::rows(db, queries::SCOPE_SPACES, [name])?;
    let mut groups: BTreeMap<i64, Value> = BTreeMap::new();
    for row in rows {
        groups.insert(id(&row["site_id"])?,json!({"site_id":row["site_id"],"normalized_domain":row["normalized_domain"],"display_name":if truth(&row["display_name"]){&row["display_name"]}else{&row["normalized_domain"]},"connections":[],"spaces":[],"item_count":row["item_count"]}));
    }
    for (kind, rows) in [("connections", connections), ("spaces", spaces)] {
        for row in rows {
            if let Some(group) = groups.get_mut(&id(&row["site_id"])?) {
                group[kind].as_array_mut().unwrap().push(row);
            }
        }
    }
    let mut groups = groups.into_values().collect::<Vec<_>>();
    groups.sort_by_key(|r| {
        (
            unicode::lowercase(&python_string(&r["display_name"])),
            python_string(&r["normalized_domain"]),
            r["site_id"].as_i64(),
        )
    });
    Ok(groups)
}
pub fn prepare_space_catalog_run(
    db: &Connection,
    config: &Config,
    v: &Value,
    run_root: Option<&Path>,
) -> Result<String> {
    let site = id(&v["site_id"])?;
    let source = v["source_instance_id"].as_i64();
    let sites = db::rows(db, queries::CATALOG_SITE, params![site, source, source])?;
    if sites.is_empty() {
        return Err(fail(
            "site-not-found",
            "The selected Atlassian Site is unavailable",
        ));
    }
    if sites.len() > 1 {
        return Err(fail(
            "ambiguous-source",
            "Select one access binding for this Atlassian Site",
        ));
    }
    let site = &sites[0];
    if !v["target_domain"].is_null()
        && unicode::lowercase(trim(v["target_domain"].as_str().unwrap_or("")))
            != site["normalized_domain"]
    {
        return Err(fail(
            "target-connection-mismatch",
            "선택한 MCP 연결은 조회 대상 Site에 속하지 않습니다.",
        ));
    }
    let state = access::capability_state(db, id(&site["source_instance_id"])?)?;
    if state["state"] != "current" {
        return Err(fail(
            "capability-not-current",
            format!(
                "The Source Instance read capability is {}",
                python_string(&state["state"])
            ),
        ));
    }
    let jira = site["service"] == "jira";
    let operation = if jira {
        "jira.search_metadata"
    } else {
        "confluence.search_pages"
    };
    let args = if jira {
        json!({"jql":"project is not EMPTY ORDER BY project","fields":["project"],"limit":100})
    } else {
        json!({"cql":"type = page","limit":200})
    };
    let site_id = id(&site["id"])?;
    sync::prepare_external_sync_run(
        db,
        config,
        &json!({"runner":v["runner"].as_str().unwrap_or("claude"),"source_instance_id":site["source_instance_id"],"source_kind":"atlassian","scope_kind":"space","targets":[{"target_id":format!("space-catalog-site-{site_id}"),"locator":{"kind":"source_root","value":site["canonical_base_url"]},"coverage":["metadata"],"field_allowlist":[if jira{"project"}else{"space"}],"known":{},"requests":[{"request_id":format!("space-catalog-request-{site_id}"),"logical_operation":operation,"arguments":args}]}],"call_budget":1}),
        run_root,
    )
}
pub fn register_space_candidate(db: &Connection, v: &Value) -> Result<Value> {
    let key = bounded(&v["space_key"], "space_key", 300, false)?.unwrap();
    let title = bounded(&v["name"], "name", 500, false)?.unwrap();
    let remote = bounded(&v["remote_id"], "remote_id", 300, true)?;
    let site = id(&v["site_id"])?;
    let service = v["service"].as_str().unwrap_or("");
    let source = v["source_instance_id"].as_i64();
    let sites = db::rows(
        db,
        queries::CANDIDATE_SITE,
        params![site, service, source, source],
    )?;
    if sites.len() != 1 {
        return Err(fail(
            "site-mismatch",
            "The selected Site access binding is unavailable or ambiguous",
        ));
    }
    let site = &sites[0];
    let url = format!(
        "{}{}{key}{}",
        site["canonical_base_url"]
            .as_str()
            .unwrap()
            .trim_end_matches('/'),
        if service == "jira" {
            "/projects/"
        } else {
            "/spaces/"
        },
        if service == "jira" { "" } else { "/overview" }
    );
    let existing = db::row(
        db,
        queries::CANDIDATE_EXISTING,
        params![id(&site["id"])?, service, key],
    )?;
    let space = catalog::register_atlassian_space(
        db,
        &json!({"site_id":site["id"],"service":service,"source_instance_id":site["source_instance_id"],"name":title,"remote_id":remote,"space_key":key,"canonical_url":url}),
    )?;
    Ok(
        json!({"kind":"space","created":existing.is_none(),"id":space["id"],"site_id":space["site_id"],"service":service}),
    )
}
pub fn space_catalog_candidates(
    db: &Connection,
    run_id: &str,
    selected_service: Option<&str>,
) -> Result<Value> {
    let row = db::row(db, queries::CATALOG_RUN, [run_id])?
        .filter(|r| selected_service.is_none_or(|s| r["service"] == s))
        .ok_or_else(|| fail("catalog-not-found", "Space discovery Run was not found"))?;
    let service = python_string(&row["service"]);
    let mut result = json!({"run_id":run_id,"status":row["status"],"partial":true,"service":service,"site_id":null,"source_instance_id":row["source_instance_id"],"candidates":[]});
    if !truth(&row["structured_result_json"]) {
        return Ok(result);
    }
    let raw = row["structured_result_json"].as_str().unwrap_or("");
    let scope = codec::Scope::for_document(raw);
    let payload = scope.parse(raw).map_err(|error| {
        if error.is_io() {
            crate::backend::BackendError::new(500, "json_scalar", error.to_string())
        } else {
            fail("catalog-invalid", "Space discovery result is invalid")
        }
    })?;
    if !payload.is_object() {
        return Err(crate::backend::BackendError::new(
            500,
            "catalog-invalid",
            "Stored Space discovery result is not an object",
        ));
    }
    let mut candidates = Map::new();
    let field = if service == "jira" {
        "project"
    } else {
        "space"
    };
    if let Some(targets) = payload["targets"].as_array() {
        for target in targets {
            if let Some(raw) = target["target_id"]
                .as_str()
                .and_then(|s| s.strip_prefix("space-catalog-site-"))
            {
                if let Some(site) = integer_text(raw) {
                    result["site_id"] = Value::Number(site);
                }
            }
            if let Some(requests) = target["requests"].as_array() {
                for request in requests {
                    let Some(metadata) = request["metadata"].as_object() else {
                        continue;
                    };
                    let raw = metadata.get(field).unwrap_or(&Value::Null);
                    let objects = if raw.is_object() {
                        vec![raw]
                    } else {
                        raw.as_array()
                            .map(|v| {
                                v.iter()
                                    .take(CATALOG_MAX_CANDIDATES)
                                    .filter(|v| v.is_object())
                                    .collect()
                            })
                            .unwrap_or_default()
                    };
                    for raw in objects {
                        let first = |keys: &[&str]| {
                            keys.iter()
                                .map(|k| &raw[*k])
                                .find(|v| truth(v))
                                .unwrap_or(&Value::Null)
                        };
                        let key = first(&["key", "space_key"]);
                        let remote = first(&["id", "remote_id"]);
                        let name = first(&["name", "title", "key", "space_key", "id", "remote_id"]);
                        let Some(name) = name.as_str().map(trim).filter(|s| !s.is_empty()) else {
                            continue;
                        };
                        let Some(key) = key.as_str().map(trim).filter(|s| !s.is_empty()) else {
                            continue;
                        };
                        candidates.entry(key.to_owned()).or_insert_with(||json!({"key":key,"remote_id":if remote.is_null(){Value::Null}else{json!(trim(&scope.python_string(remote)))},"name":name.chars().take(500).collect::<String>()}));
                    }
                }
            }
        }
    }
    result["candidates"] = json!(candidates
        .into_values()
        .take(CATALOG_MAX_CANDIDATES)
        .collect::<Vec<_>>());
    scope.materialized(&result)?;
    Ok(result)
}
pub fn register_space_catalog_candidate(db: &Connection, v: &Value) -> Result<Value> {
    let key = bounded(&v["candidate_key"], "candidate_key", 300, false)?.unwrap();
    let run = v["run_id"].as_str().unwrap_or("");
    let catalog = space_catalog_candidates(db, run, None)?;
    let candidates = catalog["candidates"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|c| c["key"] == key)
        .collect::<Vec<_>>();
    let site = catalog["site_id"].as_i64().unwrap_or(0);
    let source = catalog["source_instance_id"].as_i64().unwrap_or(0);
    if candidates.len() != 1 || site < 1 || source < 1 {
        return Err(fail(
            "candidate-not-found",
            "The selected Space candidate is no longer available",
        ));
    }
    let candidate = candidates[0];
    register_space_candidate(
        db,
        &json!({"site_id":site,"service":catalog["service"],"source_instance_id":source,"space_key":candidate["key"],"name":candidate["name"],"remote_id":candidate["remote_id"]}),
    )
}
