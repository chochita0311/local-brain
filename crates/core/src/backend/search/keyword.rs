use super::{source::private_derived, urlencode};
use crate::backend::{db, models, sources, Config, Result};
use rusqlite::{params_from_iter, types::Value as SqlValue, Connection};
use serde_json::Value;
pub fn fts_expression(query: &str) -> String {
    query
        .split(|ch: char| {
            !crate::backend::unicode::python_alnum(ch) && !['_', '.', '-'].contains(&ch)
        })
        .filter(|part| !part.is_empty())
        .take(12)
        .map(|word| format!("\"{}\"", word.replace('"', "\"\"")))
        .collect::<Vec<_>>()
        .join(" AND ")
}
pub fn keyword_search(
    connection: &Connection,
    query: &str,
    scope: &str,
    limit: usize,
    config: &Config,
) -> Result<Vec<Value>> {
    let expression = fts_expression(query);
    if expression.is_empty() {
        return Ok(vec![]);
    }
    let roots = sources::registered_session_roots(config)?;
    let keys = roots.keys().copied().collect::<Vec<_>>();
    let marks = if keys.is_empty() {
        "NULL".into()
    } else {
        vec!["?"; keys.len()].join(",")
    };
    let mut clauses = Vec::new();
    let mut params = vec![SqlValue::Text(expression)];
    if ["all", "sessions"].contains(&scope) {
        clauses.push(format!("(entity_type='session' AND EXISTS (SELECT 1 FROM sessions s JOIN sources o ON o.id=s.source_id WHERE s.id=entity_id AND s.session_class='work' AND s.session_role='primary' AND s.index_policy='full' AND o.id IN ({marks})))"));
        params.extend(keys.iter().copied().map(SqlValue::Integer));
    }
    if ["all", "documents"].contains(&scope) {
        clauses.push("(entity_type='document' AND EXISTS (SELECT 1 FROM context_documents d JOIN context_roots r ON r.id=d.context_root_id WHERE d.id=entity_id AND r.enabled=1 AND r.readable=1))".into());
    }
    if clauses.is_empty() {
        return Ok(vec![]);
    }
    let selected = if ["all", "documents"].contains(&scope) {
        models::folder_status(config)?["path"]
            .as_str()
            .map(std::path::PathBuf::from)
    } else {
        None
    };
    let sql=format!("SELECT entity_type,entity_id,source_kind,search_index.title,path,snippet(search_index,4,'[[',']]',' ... ',26) AS excerpt,bm25(search_index) AS score,owner.id AS owner_source_id,owner.root_path AS owner_root FROM search_index LEFT JOIN sessions AS owner_session ON entity_type='session' AND owner_session.id=entity_id LEFT JOIN sources AS owner ON owner.id=owner_session.source_id WHERE search_index MATCH ? AND ({}) ORDER BY score",clauses.join(" OR "));
    let mut results = Vec::new();
    db::scan(connection, &sql, params_from_iter(params), |mut item| {
        let path = item["path"].as_str().unwrap_or("");
        if item["entity_type"] == "document"
            && !path.starts_with("apple-notes://")
            && private_derived(path, config, selected.as_deref())?
        {
            return Ok(true);
        }
        let id = item["owner_source_id"].as_i64();
        if item["entity_type"] == "session" {
            if id.is_none()
                || roots.get(&id.unwrap()).map(String::as_str) != item["owner_root"].as_str()
            {
                return Ok(true);
            }
            item["source_id"] = id.into();
        }
        item.as_object_mut().unwrap().remove("owner_source_id");
        item.as_object_mut().unwrap().remove("owner_root");
        let entity = item["entity_id"]
            .as_str()
            .map(str::to_owned)
            .unwrap_or_else(|| item["entity_id"].to_string());
        let kind = item["entity_type"].as_str().unwrap();
        let anchor = format!("natural-result-{kind}-{entity}");
        let return_to = format!(
            "/natural-search?{}#{anchor}",
            urlencode(&[("q", query.into()), ("mode", "keyword".into())])
        );
        let url = format!(
            "/{}/{entity}?{}",
            if kind == "session" {
                "sessions"
            } else {
                "documents"
            },
            urlencode(&[("search_return", return_to)])
        );
        item["url"] = url.into();
        item["anchor"] = anchor.into();
        results.push(item);
        Ok(results.len() < limit)
    })?;
    Ok(results)
}

/// Deprecated `/search` keeps its historical population. Registration and private
/// path admission belong to natural keyword search above, not this legacy route.
pub fn legacy_search(
    connection: &Connection,
    query: &str,
    scope: &str,
    filters: &Value,
    limit: i64,
) -> Result<Vec<Value>> {
    let expression = fts_expression(query);
    if expression.is_empty() {
        return Ok(vec![]);
    }
    let mut results = Vec::new();
    if scope != "atlassian" {
        let entity_filter = match scope {
            "sessions" => "AND entity_type = 'session'",
            "documents" => "AND entity_type = 'document'",
            _ => "AND entity_type IN ('session', 'document')",
        };
        results.extend(db::rows(connection,&format!(r#"
                SELECT entity_type, entity_id, source_kind, title, path,
                       CASE WHEN entity_type='session' THEN (SELECT source_id FROM sessions WHERE id=entity_id)
                            WHEN entity_type='document' THEN (SELECT source_id FROM context_documents WHERE id=entity_id) END AS source_id,
                       snippet(search_index, 4, '[[', ']]', ' ... ', 26) AS excerpt,
                       bm25(search_index) AS score
                FROM search_index
                WHERE search_index MATCH ?
                  {entity_filter}
                ORDER BY score
                LIMIT ?
                "#),rusqlite::params![expression,limit])?);
    }
    if !["sessions", "documents"].contains(&scope) {
        results.extend(crate::backend::atlassian::browse::atlassian_search_results(
            connection, query, filters, limit,
        )?);
    }
    let text = |value: &Value, key: &str| value[key].as_str().unwrap_or("").to_owned();
    results.sort_by(|a, b| {
        a["score"]
            .as_f64()
            .unwrap_or(0.0)
            .total_cmp(&b["score"].as_f64().unwrap_or(0.0))
            .then_with(|| text(a, "title").cmp(&text(b, "title")))
            .then_with(|| text(a, "entity_type").cmp(&text(b, "entity_type")))
            .then_with(|| text(a, "entity_id").cmp(&text(b, "entity_id")))
    });
    let length = if limit >= 0 {
        usize::try_from(limit).unwrap_or(usize::MAX)
    } else {
        results
            .len()
            .saturating_sub(limit.unsigned_abs().try_into().unwrap_or(usize::MAX))
    };
    results.truncate(length);
    Ok(results)
}
