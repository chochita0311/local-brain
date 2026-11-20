use super::super::common::*;
use super::{
    contract::*,
    input::{format_sql, load_snapshots, validate_manifest, value_id},
    sql,
};
use crate::backend::{clock, db, Result};
use chrono::{DateTime, Utc};
use rusqlite::{params, params_from_iter, Connection, OptionalExtension};
use serde_json::{json, Value};
use std::{collections::BTreeSet, path::Path, time::Duration};
#[derive(Clone)]
struct Dated {
    row: Value,
    at: DateTime<Utc>,
}
#[derive(Clone)]
struct Selected {
    choice: Value,
    at: DateTime<Utc>,
    session: Value,
    workstream: Value,
}
fn spread<T: Clone>(rows: &[T], count: usize) -> Vec<T> {
    if rows.len() <= count {
        rows.to_vec()
    } else {
        (0..count)
            .map(|index| rows[index * (rows.len() - 1) / (count - 1)].clone())
            .collect()
    }
}
fn dated(
    rows: Vec<Value>,
    through: DateTime<Utc>,
    omissions: &mut Vec<Option<DateTime<Utc>>>,
) -> Vec<Dated> {
    let mut result = Vec::new();
    for row in rows {
        let Some(at) = row["at"].as_str().and_then(|value| utc(value).ok()) else {
            omissions.push(None);
            continue;
        };
        if at <= through {
            result.push(Dated { row, at });
        }
    }
    result.sort_by(|a, b| {
        a.at.cmp(&b.at)
            .then_with(|| {
                a.row["table"]
                    .as_str()
                    .unwrap_or_default()
                    .cmp(b.row["table"].as_str().unwrap_or_default())
            })
            .then_with(|| value_id(&a.row["id"]).cmp(&value_id(&b.row["id"])))
    });
    result
}
fn prefix(
    connection: &Connection,
    row: &Dated,
    table: &str,
    column: &str,
    identity: &str,
    maximum: i64,
    omissions: &mut Vec<Option<DateTime<Utc>>>,
) -> Result<Option<Selected>> {
    let size = int(&row.row["size"]).unwrap_or(0);
    if size <= 0 {
        return Ok(None);
    }
    let count = size.min(maximum);
    let text = connection
        .query_row(
            &format_sql(sql::PREPARATION_PREFIX_0, &[column, table, identity]),
            params![count, crate::backend::usage::sql_value(&row.row["id"])?],
            |row| row.get::<_, String>(0),
        )
        .optional()?
        .ok_or_else(|| failure("SOURCE_CHANGED"))?;
    require(text.chars().count() == count as usize, "SOURCE_CHANGED")?;
    if size > count {
        omissions.push(Some(row.at));
    }
    let mut choice = json!({"id":row.row["id"],"start":0,"end":count,"sha256":sha(&text)});
    if row.row.get("table").is_some() {
        choice["table"] = row.row["table"].clone();
    }
    Ok(Some(Selected {
        choice,
        at: row.at,
        session: row.row["session_id"].clone(),
        workstream: row.row["workstream_id"].clone(),
    }))
}
fn take(rows: &[Dated], count: usize, omissions: &mut Vec<Option<DateTime<Utc>>>) -> Vec<Dated> {
    let selected = spread(rows, count);
    let ids = selected
        .iter()
        .map(|value| {
            (
                value.row["table"].as_str().unwrap_or_default(),
                value_id(&value.row["id"]),
            )
        })
        .collect::<BTreeSet<_>>();
    for row in rows {
        if !ids.contains(&(
            row.row["table"].as_str().unwrap_or_default(),
            value_id(&row.row["id"]),
        )) {
            omissions.push(Some(row.at));
        }
    }
    selected
}
pub fn prepare_current(
    database: &Path,
    through: &str,
    owner: &str,
    expires_at: &str,
) -> Result<Value> {
    let cutoff = utc(through)?;
    identifier(&json!(owner))?;
    require(utc(expires_at)? > cutoff, "INVALID_EXPIRY")?;
    let mut omissions = Vec::new();
    let source = read_only_database(database, Duration::from_secs(120))?;
    let population = dated(
        db::rows(&source, sql::PREPARATION_PREPARE_CURRENT_0, [through])?,
        cutoff,
        &mut omissions,
    );
    require(!population.is_empty(), "NO_ELIGIBLE_INPUT")?;
    let sources = population
        .iter()
        .map(|row| int(&row.row["source_id"]).unwrap())
        .collect::<BTreeSet<_>>();
    require(sources.len() <= 8, "INPUT_LIMIT")?;
    let selected = spread(&population, 60);
    let session_ids = selected
        .iter()
        .map(|row| int(&row.row["id"]).unwrap())
        .collect::<Vec<_>>();
    let marks = vec!["?"; session_ids.len()].join(",");
    let mut events = Vec::new();
    let mut documents = Vec::new();
    let mut items = Vec::new();
    let mut organization = Vec::new();
    for session in &selected {
        let rows = dated(
            db::rows(
                &source,
                sql::PREPARATION_PREPARE_CURRENT_1,
                [int(&session.row["id"]).unwrap()],
            )?,
            cutoff,
            &mut omissions,
        );
        for row in take(&rows, 32, &mut omissions) {
            if let Some(value) = prefix(
                &source,
                &row,
                "activity_events",
                "text",
                "id",
                1000,
                &mut omissions,
            )? {
                events.push(value);
            }
        }
    }
    let mut params = session_ids
        .iter()
        .map(|id| rusqlite::types::Value::Integer(*id))
        .collect::<Vec<_>>();
    params.push(through.to_owned().into());
    let rows = dated(
        db::rows(
            &source,
            &format_sql(sql::PREPARATION_PREPARE_CURRENT_2, &[&marks]),
            params_from_iter(&params),
        )?,
        cutoff,
        &mut omissions,
    );
    for row in take(&rows, 20, &mut omissions) {
        if let Some(value) = prefix(
            &source,
            &row,
            "context_documents",
            "body",
            "id",
            8000,
            &mut omissions,
        )? {
            documents.push(value);
        }
    }
    let rows = dated(
        db::rows(
            &source,
            &format_sql(sql::PREPARATION_PREPARE_CURRENT_3, &[&marks]),
            params_from_iter(&params),
        )?,
        cutoff,
        &mut omissions,
    );
    for row in take(&rows, 20, &mut omissions) {
        if let Some(value) = prefix(
            &source,
            &row,
            "external_resource_content",
            "normalized_text",
            "external_resource_id",
            8000,
            &mut omissions,
        )? {
            items.push(value);
        }
    }
    let links = dated(
        db::rows(
            &source,
            &format_sql(sql::PREPARATION_PREPARE_CURRENT_4, &[&marks]),
            params_from_iter(session_ids.iter().map(i64::to_string)),
        )?,
        cutoff,
        &mut omissions,
    );
    let links = take(&links, 200, &mut omissions);
    let owners = links
        .iter()
        .map(|row| int(&row.row["workstream_id"]).unwrap())
        .collect::<BTreeSet<_>>();
    let mut owner_rows = Vec::new();
    if !owners.is_empty() {
        let owner_marks = vec!["?"; owners.len()].join(",");
        for (table, column, owner_column) in [
            ("workstreams", "summary", "id"),
            ("threads", "current_goal", "workstream_id"),
            ("checkpoints", "current_goal", "workstream_id"),
        ] {
            let query = format_sql(
                sql::PREPARATION_PREPARE_CURRENT_5,
                &[column, owner_column, table, owner_column, &owner_marks],
            );
            for mut row in db::rows(&source, &query, params_from_iter(&owners))? {
                row["table"] = table.into();
                owner_rows.push(row);
            }
        }
    }
    let rows = dated(owner_rows, cutoff, &mut omissions);
    for row in take(&rows, 20, &mut omissions) {
        let table = string(&row.row["table"])?;
        let column = if table == "workstreams" {
            "summary"
        } else {
            "current_goal"
        };
        if let Some(value) = prefix(&source, &row, table, column, "id", 2000, &mut omissions)? {
            organization.push(value);
        }
    }
    let start = population
        .iter()
        .map(|row| row.at)
        .chain(
            documents
                .iter()
                .chain(&items)
                .chain(&organization)
                .map(|row| row.at),
        )
        .chain(links.iter().map(|row| row.at))
        .min()
        .unwrap();
    let cutoffs = BTreeSet::from([
        selected[(selected.len() - 1) / 3].at,
        selected[2 * (selected.len() - 1) / 3].at,
        cutoff,
    ]);
    let mut snapshots = Vec::new();
    for (index, at) in cutoffs.into_iter().enumerate() {
        let ids = selected
            .iter()
            .filter(|row| row.at <= at)
            .map(|row| int(&row.row["id"]).unwrap())
            .collect::<BTreeSet<_>>();
        let current_owners = organization
            .iter()
            .filter(|row| row.at <= at)
            .collect::<Vec<_>>();
        let owner_ids = current_owners
            .iter()
            .filter_map(|row| int(&row.workstream))
            .collect::<BTreeSet<_>>();
        let missing = omissions
            .iter()
            .filter(|omission| omission.is_none_or(|time| time <= at))
            .count();
        snapshots.push(json!({"name":format!("observation-{}",index+1),"as_of":clock::isoformat(at),"session_ids":selected.iter().filter_map(|row|{let id=int(&row.row["id"]).unwrap();ids.contains(&id).then_some(id)}).collect::<Vec<_>>(),"events":events.iter().filter(|row|row.at<=at&&int(&row.session).is_some_and(|id|ids.contains(&id))).map(|row|row.choice.clone()).collect::<Vec<_>>(),"documents":documents.iter().filter(|row|row.at<=at).map(|row|row.choice.clone()).collect::<Vec<_>>(),"items":items.iter().filter(|row|row.at<=at).map(|row|row.choice.clone()).collect::<Vec<_>>(),"organization":current_owners.iter().map(|row|row.choice.clone()).collect::<Vec<_>>(),"organization_links":links.iter().filter(|row|row.at<=at&&value_id(&row.row["session_id"]).parse::<i64>().is_ok_and(|id|ids.contains(&id))&&int(&row.row["workstream_id"]).is_some_and(|id|owner_ids.contains(&id))).map(|row|row.row["id"].clone()).collect::<Vec<_>>(),"coverage":{"complete":missing==0,"unexamined":missing}}));
    }
    drop(source);
    let manifest = json!({"version":1,"source_ids":sources,"start":clock::isoformat(start),"end":through,"owner":owner,"expires_at":expires_at,"snapshots":snapshots});
    validate_manifest(&manifest)?;
    let snapshots = load_snapshots(database, &manifest)?;
    Ok(
        json!({"manifest":manifest,"snapshots":snapshots,"preparation":{"version":"localbrain.chronological-spread.v1","eligible_sessions":population.len(),"selected_sessions":selected.len(),"outside_sample_sessions":population.len()-selected.len(),"omitted_or_truncated_records":omissions.len()}}),
    )
}
