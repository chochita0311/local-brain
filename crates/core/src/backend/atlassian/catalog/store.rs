use super::super::common::*;
use super::{
    normalize_atlassian_url, projection, NormalizedAtlassianUrl, ATTENTION_VALUES, COVERAGE_VALUES,
    SERVICES,
};
use crate::backend::{db, resources, Result};
use rusqlite::{params, Connection};
use serde_json::{json, Value};

pub(super) fn source_instance(connection: &Connection, id: i64) -> Result<Value> {
    let row = required_row(
        connection,
        "SELECT id,service,enabled FROM external_source_instances WHERE id=?",
        [id],
        "source-instance-not-found",
        "Source Instance does not exist",
    )?;
    if !truth(&row["enabled"]) {
        return Err(fail(
            "source-instance-disabled",
            "Source Instance is disabled",
        ));
    }
    Ok(row)
}
pub(super) fn optional_id(value: &Value) -> Result<Option<i64>> {
    if value.is_null() {
        Ok(None)
    } else {
        id(value).map(Some)
    }
}
pub(super) fn checked_time(value: &Value) -> Result<String> {
    if truth(value) {
        value
            .as_str()
            .map(ToOwned::to_owned)
            .ok_or_else(|| fail("invalid-timestamp", "Timestamp must be ISO-8601"))
    } else {
        Ok(now())
    }
}
fn collision(error: rusqlite::Error, code: &str, message: &str) -> crate::backend::BackendError {
    if matches!(&error,rusqlite::Error::SqliteFailure(error,_) if error.code==rusqlite::ErrorCode::ConstraintViolation)
    {
        fail(code, message)
    } else {
        error.into()
    }
}
pub fn register_atlassian_site(connection: &Connection, values: &Value) -> Result<Value> {
    let source = optional_id(&values["source_instance_id"])?;
    if let Some(id) = source {
        source_instance(connection, id)?;
    }
    let normalized = normalize_atlassian_url(
        values["base_url"]
            .as_str()
            .ok_or_else(|| fail("invalid-input", "url must be a non-empty string"))?,
    )?;
    let display = optional_text(
        &values["display_name"],
        "display_name",
        300,
        "invalid-input",
    )?;
    let remote = optional_text(
        &values["remote_site_id"],
        "remote_site_id",
        300,
        "invalid-input",
    )?;
    let timestamp = now();
    let site = atomic(connection, "atlassian_site_registration", || {
        let row=db::row(connection,"SELECT * FROM atlassian_sites WHERE normalized_domain=? ORDER BY CASE WHEN source_instance_id=? THEN 0 ELSE 1 END,id LIMIT 1",params![normalized.normalized_domain,source])?;
        let site = if let Some(row) = row {
            let site = id(&row["id"])?;
            if remote.as_ref().is_some_and(|remote| {
                !row["remote_site_id"].is_null() && row["remote_site_id"] != *remote
            }) {
                return Err(fail(
                    "site-identity-conflict",
                    "Site is already bound to a different remote identity",
                ));
            }
            if let Some(remote) = remote.as_deref() {
                if db::row(
                    connection,
                    "SELECT id FROM atlassian_sites WHERE remote_site_id=? AND id!=?",
                    params![remote, site],
                )?
                .is_some()
                {
                    return Err(fail(
                        "site-identity-collision",
                        "Remote Site identity is already bound",
                    ));
                }
            }
            connection.execute("UPDATE atlassian_sites SET display_name=COALESCE(?,display_name),remote_site_id=COALESCE(?,remote_site_id),updated_at=? WHERE id=?",params![display,remote,timestamp,site])?;
            site
        } else {
            connection.execute("INSERT INTO atlassian_sites(source_instance_id,normalized_domain,display_name,remote_site_id,canonical_base_url,updated_at) VALUES (?,?,?,?,?,?)",params![source,normalized.normalized_domain,display,remote,normalized.canonical_base_url,timestamp]).map_err(|e|collision(e,"site-identity-collision","Site identity collides with an existing Atlassian domain"))?;
            connection.last_insert_rowid()
        };
        if let Some(source) = source {
            connection.execute("INSERT OR IGNORE INTO atlassian_site_bindings(site_id,source_instance_id) VALUES (?,?)",params![site,source])?;
            connection.execute("UPDATE atlassian_sites SET source_instance_id=COALESCE(source_instance_id,?),updated_at=? WHERE id=?",params![source,timestamp,site])?;
        }
        Ok(site)
    })?;
    required_row(
        connection,
        "SELECT * FROM atlassian_sites WHERE id=?",
        [site],
        "site-not-found",
        "Atlassian Site does not exist",
    )
}
pub fn bind_atlassian_site_access(
    connection: &Connection,
    site: i64,
    source: i64,
) -> Result<Value> {
    let instance = source_instance(connection, source)?;
    required_row(
        connection,
        "SELECT id FROM atlassian_sites WHERE id=?",
        [site],
        "site-not-found",
        "Atlassian Site does not exist",
    )?;
    atomic(connection, "atlassian_site_access_binding", || {
        connection.execute("INSERT OR IGNORE INTO atlassian_site_bindings(site_id,source_instance_id) VALUES (?,?)",params![site,source])?;
        connection.execute("UPDATE atlassian_sites SET source_instance_id=COALESCE(source_instance_id,?),updated_at=? WHERE id=?",params![source,now(),site])?;
        Ok(())
    })?;
    let mut row=required_row(connection,"SELECT atlassian_site_bindings.id AS binding_id,atlassian_site_bindings.site_id,external_source_instances.* FROM atlassian_site_bindings JOIN external_source_instances ON external_source_instances.id=atlassian_site_bindings.source_instance_id WHERE atlassian_site_bindings.site_id=? AND atlassian_site_bindings.source_instance_id=?",params![site,source],"site-not-found","Atlassian Site does not exist")?;
    row["service"] = instance["service"].clone();
    Ok(row)
}
pub fn resolve_atlassian_site_access(
    connection: &Connection,
    site: i64,
    service: &str,
    source: Option<i64>,
    enabled_only: bool,
) -> Result<Option<Value>> {
    if !SERVICES.contains(&service) {
        return Err(fail("invalid-service", "Unsupported Atlassian service"));
    }
    let mut rows=db::rows(connection,"SELECT atlassian_site_bindings.id AS binding_id,atlassian_site_bindings.site_id,external_source_instances.* FROM atlassian_site_bindings JOIN external_source_instances ON external_source_instances.id=atlassian_site_bindings.source_instance_id WHERE atlassian_site_bindings.site_id=? AND external_source_instances.service=? AND (? IS NULL OR external_source_instances.id=?) AND (?=0 OR external_source_instances.enabled=1) ORDER BY external_source_instances.id",params![site,service,source,source,enabled_only])?;
    if rows.len() > 1 {
        return Err(fail(
            "ambiguous-site-access",
            "More than one compatible Site access binding exists",
        ));
    }
    Ok(rows.pop())
}
pub fn register_atlassian_space(connection: &Connection, values: &Value) -> Result<Value> {
    let site = id(&values["site_id"])?;
    let selected = required_row(
        connection,
        "SELECT id,normalized_domain,canonical_base_url FROM atlassian_sites WHERE id=?",
        [site],
        "site-not-found",
        "Atlassian Site does not exist",
    )?;
    let source = optional_id(&values["source_instance_id"])?;
    let mut service = values["service"].as_str().map(ToOwned::to_owned);
    if let Some(source) = source {
        let instance = source_instance(connection, source)?;
        if service
            .as_ref()
            .is_some_and(|service| instance["service"] != *service)
        {
            return Err(fail(
                "service-mismatch",
                "Source Instance service does not match the Space",
            ));
        }
        service = instance["service"].as_str().map(ToOwned::to_owned);
        bind_atlassian_site_access(connection, site, source)?;
    }
    if service.is_none() {
        let rows=db::rows(connection,"SELECT DISTINCT external_source_instances.service FROM atlassian_site_bindings JOIN external_source_instances ON external_source_instances.id=atlassian_site_bindings.source_instance_id WHERE atlassian_site_bindings.site_id=? AND external_source_instances.enabled=1 ORDER BY external_source_instances.service",[site])?;
        if rows.len() != 1 {
            return Err(fail(
                "service-required",
                "Space service must be explicit without one unambiguous binding",
            ));
        }
        service = rows[0]["service"].as_str().map(ToOwned::to_owned);
    }
    let service = service.unwrap_or_default();
    if !SERVICES.contains(&service.as_str()) {
        return Err(fail("invalid-service", "Unsupported Atlassian service"));
    }
    let name = text(&values["name"], "name", 500, "invalid-input")?;
    let remote = optional_text(&values["remote_id"], "remote_id", 300, "invalid-input")?;
    let key = optional_text(&values["space_key"], "space_key", 300, "invalid-input")?;
    if remote.is_none() && key.is_none() {
        return Err(fail(
            "invalid-space-identity",
            "Space requires a remote ID or space key",
        ));
    }
    let coverage = values["coverage"].as_str();
    if !values["coverage"].is_null()
        && !coverage.is_some_and(|s| ["selected-content", "full-content"].contains(&s))
    {
        return Err(fail(
            "invalid-space-coverage",
            "Unsupported Atlassian Space coverage",
        ));
    }
    let generated = format!(
        "{}{}{}{}",
        selected["canonical_base_url"]
            .as_str()
            .unwrap()
            .trim_end_matches('/'),
        if service == "jira" {
            "/projects/"
        } else {
            "/spaces/"
        },
        key.as_deref().or(remote.as_deref()).unwrap(),
        if service == "jira" { "" } else { "/overview" }
    );
    let url = if values["canonical_url"].is_null() {
        generated.as_str()
    } else {
        values["canonical_url"]
            .as_str()
            .ok_or_else(|| fail("invalid-input", "url must be a non-empty string"))?
    };
    let normalized = normalize_atlassian_url(url)?;
    if selected["normalized_domain"] != normalized.normalized_domain {
        return Err(fail(
            "space-site-mismatch",
            "Space URL does not belong to the selected Atlassian Site",
        ));
    }
    let row=db::row(connection,"SELECT * FROM atlassian_spaces WHERE site_id=? AND service=? AND ((? IS NOT NULL AND remote_id=?) OR (? IS NOT NULL AND space_key=?)) ORDER BY id LIMIT 1",params![site,service,remote,remote,key,key])?;
    let timestamp = now();
    let space = atomic(connection, "atlassian_space_registration", || {
        if let Some(row) = row {
            if remote
                .as_ref()
                .is_some_and(|v| !row["remote_id"].is_null() && row["remote_id"] != *v)
                || key
                    .as_ref()
                    .is_some_and(|v| !row["space_key"].is_null() && row["space_key"] != *v)
            {
                return Err(fail(
                    "space-identity-conflict",
                    "Space identifiers resolve to conflicting rows",
                ));
            }
            let space = id(&row["id"])?;
            connection.execute("UPDATE atlassian_spaces SET source_instance_id=COALESCE(source_instance_id,?),remote_id=COALESCE(remote_id,?),space_key=COALESCE(space_key,?),name=?,canonical_url=?,coverage=COALESCE(?,coverage),updated_at=? WHERE id=?",params![source,remote,key,name,normalized.normalized_url,coverage,timestamp,space])?;
            Ok(space)
        } else {
            connection.execute("INSERT INTO atlassian_spaces(site_id,source_instance_id,service,remote_id,space_key,name,canonical_url,coverage,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",params![site,source,service,remote,key,name,normalized.normalized_url,coverage.unwrap_or(if service=="jira"{"selected-content"}else{"full-content"}),timestamp]).map_err(|e|collision(e,"space-identity-collision","Space identity is already bound inside the Site"))?;
            Ok(connection.last_insert_rowid())
        }
    })?;
    required_row(
        connection,
        "SELECT * FROM atlassian_spaces WHERE id=?",
        [space],
        "space-not-found",
        "Atlassian Space does not exist",
    )
}
fn source_site(
    connection: &Connection,
    source: i64,
    url: &NormalizedAtlassianUrl,
) -> Result<Value> {
    if let Some(row)=db::row(connection,"SELECT atlassian_sites.* FROM atlassian_sites JOIN atlassian_site_bindings ON atlassian_site_bindings.site_id=atlassian_sites.id WHERE atlassian_site_bindings.source_instance_id=? AND atlassian_sites.normalized_domain=? ORDER BY atlassian_sites.id LIMIT 1",params![source,url.normalized_domain])?{return Ok(row);}
    register_atlassian_site(
        connection,
        &json!({"source_instance_id":source,"base_url":url.canonical_base_url}),
    )
}
fn unbound_resource(
    connection: &Connection,
    url: &NormalizedAtlassianUrl,
    service: &str,
) -> Result<Option<i64>> {
    let rows=db::rows(connection,"SELECT external_resources.id,external_resources.url FROM external_resources LEFT JOIN atlassian_items ON atlassian_items.external_resource_id=external_resources.id WHERE external_resources.resource_type=? AND atlassian_items.external_resource_id IS NULL ORDER BY external_resources.id",[if service=="jira"{"jira"}else{"wiki"}])?;
    let mut matches = vec![];
    for row in rows {
        if row["url"]
            .as_str()
            .and_then(|s| normalize_atlassian_url(s).ok())
            .is_some_and(|v| v.normalized_url == url.normalized_url)
        {
            matches.push(id(&row["id"])?);
        }
    }
    if matches.len() > 1 {
        return Err(fail(
            "ambiguous-local-resource",
            "More than one unbound External Resource matches this URL",
        ));
    }
    Ok(matches.pop())
}
pub(super) fn item_row(connection: &Connection, resource: i64) -> Result<Value> {
    required_row(connection,"SELECT atlassian_items.*,atlassian_sites.normalized_domain FROM atlassian_items JOIN atlassian_sites ON atlassian_sites.id=atlassian_items.site_id WHERE atlassian_items.external_resource_id=?",[resource],"item-not-found","Atlassian Item does not exist")
}
fn set_canonical(
    connection: &Connection,
    resource: i64,
    site: i64,
    url: &NormalizedAtlassianUrl,
    at: &str,
) -> Result<()> {
    if db::row(connection,"SELECT external_resource_id FROM atlassian_item_urls WHERE site_id=? AND normalized_url=? AND external_resource_id!=?",params![site,url.normalized_url,resource])?.is_some(){return Err(fail("url-identity-collision","Normalized URL is already bound to another Item in this Site"));}
    let existing=db::row(connection,"SELECT id FROM atlassian_item_urls WHERE site_id=? AND normalized_url=? AND external_resource_id=?",params![site,url.normalized_url,resource])?;
    connection.execute("UPDATE atlassian_item_urls SET url_role='alias' WHERE external_resource_id=? AND url_role='canonical'",[resource])?;
    if let Some(row) = existing {
        connection.execute("UPDATE atlassian_item_urls SET url_role='canonical',observed_url=?,last_observed_at=? WHERE id=?",params![url.observed_url,at,id(&row["id"])?])?;
    } else {
        connection.execute("INSERT INTO atlassian_item_urls(external_resource_id,site_id,url_role,observed_url,normalized_url,first_observed_at,last_observed_at) VALUES (?,?,'canonical',?,?,?,?)",params![resource,site,url.observed_url,url.normalized_url,at,at])?;
    }
    Ok(())
}
pub fn create_or_reuse_atlassian_stub(connection: &Connection, values: &Value) -> Result<Value> {
    let url = normalize_atlassian_url(
        values["url"]
            .as_str()
            .ok_or_else(|| fail("invalid-input", "url must be a non-empty string"))?,
    )?;
    let source = optional_id(&values["source_instance_id"])?;
    let mut service = values["service"].as_str().map(ToOwned::to_owned);
    if let Some(source) = source {
        let instance = source_instance(connection, source)?;
        if service.as_ref().is_some_and(|v| instance["service"] != *v) {
            return Err(fail(
                "service-mismatch",
                "Source Instance service does not match the Item",
            ));
        }
        service = instance["service"].as_str().map(ToOwned::to_owned);
    }
    let service = service
        .filter(|s| SERVICES.contains(&s.as_str()))
        .ok_or_else(|| {
            fail(
                "service-required",
                "Item service is required without an access binding",
            )
        })?;
    let coverage = values
        .get("coverage")
        .cloned()
        .unwrap_or(json!("reference"));
    let coverage = coverage
        .as_str()
        .filter(|s| COVERAGE_VALUES.contains(s))
        .ok_or_else(|| fail("invalid-coverage", "Unsupported Atlassian coverage"))?;
    let attention = values.get("attention").cloned().unwrap_or(json!("normal"));
    let attention = attention
        .as_str()
        .filter(|s| ATTENTION_VALUES.contains(s))
        .ok_or_else(|| fail("invalid-attention", "Unsupported Atlassian attention"))?;
    let title = optional_text(&values["title"], "title", 500, "invalid-input")?;
    let timestamp = checked_time(&values["observed_at"])?;
    let selected_site = optional_id(&values["site_id"])?;
    let requested_resource = optional_id(&values["external_resource_id"])?;
    atomic(connection, "atlassian_stub_registration", || {
        let site = if let Some(site) = selected_site {
            let selected = db::row(
                connection,
                "SELECT * FROM atlassian_sites WHERE id=?",
                [site],
            )?
            .filter(|r| r["normalized_domain"] == url.normalized_domain)
            .ok_or_else(|| {
                fail(
                    "site-domain-mismatch",
                    "Item URL does not belong to the selected Site",
                )
            })?;
            if let Some(source) = source {
                bind_atlassian_site_access(connection, site, source)?;
            }
            selected
        } else if let Some(source) = source {
            source_site(connection, source, &url)?
        } else {
            register_atlassian_site(connection, &json!({"base_url":url.canonical_base_url}))?
        };
        let site = id(&site["id"])?;
        if let Some(existing)=db::row(connection,"SELECT external_resource_id FROM atlassian_item_urls WHERE site_id=? AND normalized_url=?",params![site,url.normalized_url])?{
            let resource=id(&existing["external_resource_id"])?;if requested_resource.is_some_and(|r|r!=resource){return Err(fail("url-identity-collision","URL is already bound to another local Resource"));}
            connection.execute("UPDATE atlassian_item_urls SET observed_url=?,last_observed_at=? WHERE site_id=? AND normalized_url=?",params![url.observed_url,timestamp,site,url.normalized_url])?;resources::bind_external_link(connection,resource)?;return item_row(connection,resource);
        }
        let resource = if requested_resource.is_some() {
            requested_resource
        } else {
            unbound_resource(connection, &url, &service)?
        };
        let (resource, bound) = if let Some(resource) = resource {
            required_row(
                connection,
                "SELECT id FROM external_resources WHERE id=?",
                [resource],
                "resource-not-found",
                "External Resource does not exist",
            )?;
            let bound=db::row(connection,"SELECT external_resource_id,site_id,source_instance_id,service FROM atlassian_items WHERE external_resource_id=?",[resource])?;
            if bound
                .as_ref()
                .is_some_and(|b| b["site_id"] != site || b["service"] != service)
            {
                return Err(fail(
                    "resource-already-bound",
                    "External Resource is already bound to another Atlassian Item",
                ));
            }
            (resource, bound)
        } else {
            connection.execute("INSERT INTO external_resources(resource_type,title,url,source_role,updated_at) VALUES (?,?,?,'remote-reference',?)",params![if service=="jira"{"jira"}else{"wiki"},title.as_deref().unwrap_or(&url.normalized_url),url.observed_url,timestamp])?;
            (connection.last_insert_rowid(), None)
        };
        resources::bind_external_link(connection, resource)?;
        match &bound {
            None => {
                connection.execute("INSERT INTO atlassian_items(external_resource_id,site_id,source_instance_id,service,item_type,coverage,attention,updated_at) VALUES (?,?,?,?,?,?,?,?)",params![resource,site,source,service,if service=="jira"{"jira_issue"}else{"confluence_page"},coverage,attention,timestamp])?;
            }
            Some(bound) if source.is_some() && bound["source_instance_id"].is_null() => {
                connection.execute("UPDATE atlassian_items SET source_instance_id=?,updated_at=? WHERE external_resource_id=?",params![source,timestamp,resource])?;
            }
            Some(_) => {}
        }
        set_canonical(connection, resource, site, &url, &timestamp)?;
        projection::project_internal(connection, resource, &timestamp)?;
        item_row(connection, resource)
    })
}
pub fn bind_atlassian_remote_identity(
    connection: &Connection,
    resource: i64,
    values: &Value,
) -> Result<Value> {
    let item = item_row(connection, resource)?;
    let remote = text(&values["remote_id"], "remote_id", 300, "invalid-input")?;
    let key = optional_text(&values["remote_key"], "remote_key", 300, "invalid-input")?;
    let timestamp = checked_time(&values["confirmed_at"])?;
    let url = if values["canonical_url"].is_null() {
        None
    } else {
        Some(normalize_atlassian_url(
            values["canonical_url"]
                .as_str()
                .ok_or_else(|| fail("invalid-input", "url must be a non-empty string"))?,
        )?)
    };
    if url
        .as_ref()
        .is_some_and(|url| item["normalized_domain"] != url.normalized_domain)
    {
        return Err(fail(
            "site-domain-mismatch",
            "Canonical URL belongs to a different Site domain",
        ));
    }
    let space = optional_id(&values["space_id"])?;
    if let Some(space) = space {
        let row = db::row(
            connection,
            "SELECT site_id,service FROM atlassian_spaces WHERE id=?",
            [space],
        )?;
        if row
            .as_ref()
            .is_none_or(|r| r["site_id"] != item["site_id"] || r["service"] != item["service"])
        {
            return Err(fail(
                "space-boundary-mismatch",
                "Space does not belong to the Item Site and service",
            ));
        }
    }
    atomic(connection, "atlassian_remote_binding", || {
        let current = required_row(
            connection,
            "SELECT remote_id,remote_key FROM atlassian_items WHERE external_resource_id=?",
            [resource],
            "item-not-found",
            "Atlassian Item does not exist",
        )?;
        if !current["remote_id"].is_null() && current["remote_id"] != remote {
            return Err(fail(
                "remote-identity-conflict",
                "Item is already bound to a different remote ID",
            ));
        }
        if key
            .as_ref()
            .is_some_and(|v| !current["remote_key"].is_null() && current["remote_key"] != *v)
        {
            return Err(fail(
                "remote-key-conflict",
                "Item is already bound to a different remote key",
            ));
        }
        let site = id(&item["site_id"])?;
        let service = item["service"].as_str().unwrap();
        if db::row(connection,"SELECT external_resource_id FROM atlassian_items WHERE site_id=? AND service=? AND remote_id=? AND external_resource_id!=?",params![site,service,remote,resource])?.is_some(){return Err(fail("remote-identity-collision","Remote identity is already bound to another Item"));}
        if let Some(key) = key.as_deref() {
            if db::row(connection,"SELECT external_resource_id FROM atlassian_items WHERE site_id=? AND service=? AND remote_key=? AND external_resource_id!=?",params![site,service,key,resource])?.is_some(){return Err(fail("remote-key-collision","Remote key is already bound to another Item"));}
        }
        if let Some(url) = &url {
            set_canonical(connection, resource, site, url, &timestamp)?;
        }
        connection.execute("UPDATE atlassian_items SET remote_id=?,remote_key=COALESCE(?,remote_key),space_id=COALESCE(?,space_id),confirmed_at=COALESCE(confirmed_at,?),updated_at=? WHERE external_resource_id=?",params![remote,key,space,timestamp,timestamp,resource])?;
        Ok(())
    })?;
    item_row(connection, resource)
}
pub fn set_atlassian_item_axes(
    connection: &Connection,
    resource: i64,
    values: &Value,
) -> Result<Value> {
    item_row(connection, resource)?;
    let coverage = values["coverage"].as_str();
    let attention = values["attention"].as_str();
    if !values["coverage"].is_null() && !coverage.is_some_and(|s| COVERAGE_VALUES.contains(&s)) {
        return Err(fail("invalid-coverage", "Unsupported Atlassian coverage"));
    }
    if !values["attention"].is_null() && !attention.is_some_and(|s| ATTENTION_VALUES.contains(&s)) {
        return Err(fail("invalid-attention", "Unsupported Atlassian attention"));
    }
    let timestamp = checked_time(&values["changed_at"])?;
    atomic(connection, "atlassian_item_axes", || {
        connection.execute("UPDATE atlassian_items SET coverage=COALESCE(?,coverage),attention=COALESCE(?,attention),updated_at=? WHERE external_resource_id=?",params![coverage,attention,timestamp,resource])?;
        if coverage.is_some_and(|s| s != "indexed") {
            connection.execute(
                "DELETE FROM search_index WHERE entity_type='atlassian_item' AND entity_id=?",
                [resource.to_string()],
            )?;
            connection.execute(
                "DELETE FROM external_resource_content WHERE external_resource_id=?",
                [resource],
            )?;
            if coverage == Some("reference") {
                connection.execute("UPDATE atlassian_item_remote_state SET metadata_json='{}',known_changed=0,projection_stale=0,updated_at=? WHERE external_resource_id=?",params![timestamp,resource])?;
            } else {
                connection.execute("UPDATE atlassian_item_remote_state SET known_changed=0,projection_stale=0,updated_at=? WHERE external_resource_id=?",params![timestamp,resource])?;
            }
        }
        if coverage.is_some() {
            projection::project_internal(connection, resource, &timestamp)?;
        }
        Ok(())
    })?;
    item_row(connection, resource)
}
pub fn purge_atlassian_item(connection: &Connection, resource: i64) -> Result<Value> {
    item_row(connection, resource)?;
    atomic(connection, "atlassian_item_purge", || {
        let mut result = json!({"external_resource_id":resource});
        let entity = resource.to_string();
        for (key, table, kind) in [
            ("workstream_links", "workstream_links", "external"),
            ("thread_links", "thread_links", "external"),
            (
                "checkpoint_resource_refs",
                "checkpoint_resource_refs",
                "external",
            ),
            ("search_rows", "search_index", "atlassian_item"),
        ] {
            let count = connection.execute(
                &format!("DELETE FROM {table} WHERE entity_type=? AND entity_id=?"),
                params![kind, entity],
            )?;
            result[key] = json!(count);
        }
        if connection.execute("DELETE FROM external_resources WHERE id=?", [resource])? != 1 {
            return Err(fail(
                "purge-failed",
                "Atlassian Item purge did not remove its External Resource",
            ));
        }
        Ok(result)
    })
}
