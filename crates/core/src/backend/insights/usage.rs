//! Observed analysis usage is retained independently of report success.
use super::{invalid, required, text, truth};
use crate::backend::{
    db, json as codec, storage,
    usage::{self, decimal::Decimal, ParsedUsageRecord},
    Config, Result,
};
use rusqlite::{params, Connection};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::{
    fs::File,
    io::{BufRead, BufReader},
    path::Path,
    str::FromStr,
};
pub const NORMALIZER_VERSION: &str = "personal-insight-cli-usage-v1";
pub const SESSION_PREFIX: &str = "localbrain-insight:";
fn parse(text: &str) -> Result<Value> {
    Ok(codec::Scope::for_document(text).parse(text)?)
}
pub fn insight_usage_cost(connection: &Connection, run_id: &str) -> Result<Option<Value>> {
    let Some(mut row)=db::row(connection,"SELECT usage.calculation_state,usage.estimated_cost_usd,usage.price_snapshot_id,prices.label AS price_label FROM usage_records AS usage LEFT JOIN usage_price_snapshots AS prices ON prices.id=usage.price_snapshot_id WHERE usage.source_record_id=? AND usage.normalizer_version=?",params![run_id,NORMALIZER_VERSION])?else{return Ok(None);};
    let cost = if row["calculation_state"] == "priced" && !row["estimated_cost_usd"].is_null() {
        Some(
            Decimal::from_str(required(&row, "estimated_cost_usd")?)
                .map_err(|_| invalid("invalid stored insight cost"))?,
        )
    } else {
        None
    };
    row["cost_label"] = match cost {
        Some(cost) if cost > Decimal::zero() && cost < Decimal::new(1, 4) => json!("<$0.0001"),
        Some(cost) => json!(usage::format_cost(Some(cost))),
        None => Value::Null,
    };
    Ok(Some(row))
}
pub fn insight_usage_source(
    connection: &Connection,
    config: &Config,
    options: &Value,
) -> Result<Value> {
    let root = storage::files::resolve(
        &storage::files::expand(Path::new(required(options, "codex_home")?), config)
            .join("sessions"),
    )?;
    let selected = options.get("usage_source_id").filter(|value| truth(value));
    let mut matches = vec![];
    for row in db::rows(
        connection,
        "SELECT id,root_path FROM sources WHERE provider_kind='codex'",
        [],
    )? {
        let registered = storage::files::resolve(&storage::files::expand(
            Path::new(required(&row, "root_path")?),
            config,
        ))?;
        if root == registered
            && selected.is_none_or(|id| {
                row["id"] == *id
                    || id.as_bool().is_some_and(|id| row["id"] == i64::from(id))
                    || id.as_f64().is_some_and(|id| {
                        row["id"]
                            .as_i64()
                            .is_some_and(|n| id == n as f64 && id as i64 == n)
                    })
            })
        {
            matches.push(row);
        }
    }
    if matches.len() != 1 {
        return Err(invalid("분석 프로필의 비용 집계 Source를 확인할 수 없습니다. Sources에서 해당 Codex 홈을 등록해 주세요."));
    }
    Ok(matches.remove(0))
}
/// A pure observation normalizer, also used when recovering retained streams.
pub fn usage_record(
    run: &Value,
    observed: &Value,
    options: &Value,
    occurred_at: &str,
    source_line: i64,
) -> Result<ParsedUsageRecord> {
    let mut components = Map::new();
    let mut malformed = false;
    let mut component = |key: &str| -> Option<i64> {
        let Some(value) = observed.get(key) else {
            components.insert(key.into(), json!("missing"));
            return None;
        };
        let value = value.as_i64().filter(|n| *n >= 0);
        components.insert(
            key.into(),
            json!(if value.is_some() {
                "available"
            } else {
                "malformed"
            }),
        );
        malformed |= value.is_none();
        value
    };
    let inclusive = component("input_tokens");
    let cached = component("cached_input_tokens");
    let output = component("output_tokens");
    let reasoning = component("reasoning_output_tokens");
    let input = match (inclusive, cached) {
        (Some(input), Some(cached)) if cached > input => {
            malformed = true;
            components.insert(
                "cached_input_tokens".into(),
                json!("malformed_exceeds_input"),
            );
            None
        }
        (Some(input), Some(cached)) => Some(input - cached),
        _ => None,
    };
    if reasoning
        .zip(output)
        .is_some_and(|(reasoning, output)| reasoning > output)
    {
        malformed = true;
        components.insert(
            "reasoning_output_tokens".into(),
            json!("malformed_exceeds_output"),
        );
    }
    let total = if let (Some(input), Some(output)) = (inclusive, output) {
        match input.checked_add(output) {
            Some(total) => Some(total),
            None => {
                malformed = true;
                None
            }
        }
    } else {
        None
    };
    let raw_model = run["resolved_model"]
        .as_str()
        .filter(|s| !s.is_empty())
        .unwrap_or(required(run, "model")?)
        .to_owned();
    let model = usage::normalize_model(Some(&raw_model));
    let tier = options
        .get("service_tier")
        .map(|value| value.as_str().unwrap_or(""))
        .unwrap_or("standard");
    let id = required(run, "id")?;
    for (key, value) in [
        ("usage_source", json!("codex_exec_turn_completed")),
        (
            "usage_evidence",
            json!(if source_line != 0 {
                "run_stream"
            } else {
                "retained_run_usage_json"
            }),
        ),
        ("context_scope", json!("turn_total")),
        (
            "model_resolution",
            json!(if run["resolved_model"]
                .as_str()
                .is_some_and(|s| !s.is_empty())
            {
                "observed"
            } else {
                "selected_unverified"
            }),
        ),
        (
            "service_tier",
            options
                .get("service_tier")
                .cloned()
                .unwrap_or_else(|| json!("standard")),
        ),
        (
            "service_tier_source",
            json!(if options.get("service_tier").is_some() {
                "frozen_run_setting"
            } else {
                "unmarked_default_assumption"
            }),
        ),
        ("cache_write_tokens", json!("not_supported")),
        ("insight_run_id", json!(id)),
    ] {
        components.insert(key.into(), value);
    }
    Ok(ParsedUsageRecord{usage_record_id:format!("{:x}",Sha256::digest(format!("personal-insight-usage\u{1f}{id}").as_bytes())),source_record_id:id.into(),source_line,occurred_at:Some(occurred_at.into()),raw_model:Some(raw_model),normalized_model:model.clone(),input_tokens:input.map(Into::into),output_tokens:output.map(Into::into),cache_write_tokens:None,cache_read_tokens:cached.map(Into::into),reasoning_tokens:reasoning.map(Into::into),source_total_tokens:None,total_tokens:total.map(Into::into),total_semantics:"codex_exec_turn_total;source_input_includes_cache_read;normalized_non_cached_input_plus_output_plus_cache_read;reasoning_subset_of_output".into(),aggregation_scope:"direct".into(),capability_state:if malformed{"malformed"}else if [input,cached,output,reasoning].contains(&None){"partial"}else{"complete"}.into(),capability:Value::Object(components),price_snapshot_id:Some(usage::select_snapshot("codex",model.as_deref(),Some(occurred_at),tier,inclusive.map(i128::from)))})
}
/// The caller owns its transaction, including the independently retained Run.
pub fn store_insight_usage(
    connection: &Connection,
    config: &Config,
    run: &Value,
    observed: &Value,
    observed_at: &str,
    source_line: i64,
) -> Result<()> {
    let options = parse(required(run, "settings_json")?)?;
    let source = insight_usage_source(connection, config, &options)?;
    let source_id = source["id"].as_i64().unwrap();
    let id = required(run, "id")?;
    let mut record = usage_record(run, observed, &options, observed_at, source_line)?;
    if let Some(existing)=db::row(connection,"SELECT occurred_at,price_snapshot_id FROM usage_records WHERE source_id=? AND source_record_id=? AND normalizer_version=?",params![source_id,id,NORMALIZER_VERSION])?{record.occurred_at=existing["occurred_at"].as_str().map(str::to_owned);record.price_snapshot_id=existing["price_snapshot_id"].as_str().map(str::to_owned);}
    let external = format!("{SESSION_PREFIX}{id}");
    let stream = required(run, "stream_path")?;
    let cwd = Path::new(stream).parent().unwrap_or(Path::new("."));
    connection.execute("INSERT INTO sessions(source_id,external_id,source_path,cwd_raw,title,started_at,ended_at,last_event_at,session_class,session_role,index_policy) VALUES (?,?,?,?,'Insights analysis',?,?,?,'maintenance','primary','metadata_only') ON CONFLICT(source_id,external_id) DO UPDATE SET ended_at=excluded.ended_at,last_event_at=excluded.last_event_at",params![source_id,external,stream,cwd.to_string_lossy(),text(&run["started_at"],required(run,"created_at")?),text(&run["completed_at"],observed_at),record.occurred_at])?;
    let session_id = connection.query_row(
        "SELECT id FROM sessions WHERE source_id=? AND external_id=?",
        params![source_id, external],
        |row| row.get::<_, i64>(0),
    )?;
    usage::store_usage_records(
        connection,
        source_id,
        session_id,
        &[record],
        None,
        NORMALIZER_VERSION,
    )?;
    connection.execute("UPDATE personal_insight_runs SET usage_json=?,resolved_model=COALESCE(?,resolved_model) WHERE id=?",params![codec::canonical(observed)?,run["resolved_model"].as_str(),id])?;
    Ok(())
}
pub fn recover_insight_usage(connection: &Connection, config: &Config) -> Result<usize> {
    let mut recovered = 0;
    for mut run in db::rows(
        connection,
        "SELECT * FROM personal_insight_runs WHERE status NOT IN ('queued','running')",
        [],
    )? {
        let id = required(&run, "id")?.to_owned();
        if db::row(
            connection,
            "SELECT 1 FROM usage_records WHERE source_record_id=? AND normalizer_version=?",
            params![id, NORMALIZER_VERSION],
        )?
        .is_some()
        {
            continue;
        }
        let result = (|| -> Result<bool> {
            let mut usage = run["usage_json"]
                .as_str()
                .filter(|s| !s.is_empty())
                .map(parse)
                .transpose()?;
            let mut source_line = 0;
            if !usage.as_ref().is_some_and(Value::is_object) {
                let path = Path::new(required(&run, "stream_path")?);
                if !path.is_file() {
                    return Ok(false);
                }
                let mut reader = BufReader::new(File::open(path)?);
                let mut line = vec![];
                let mut number = 0;
                while reader.read_until(b'\n', &mut line)? > 0 {
                    number += 1;
                    let decoded = String::from_utf8_lossy(&line);
                    if let Ok(event) = parse(&decoded) {
                        if event.is_object() {
                            if event["model"].is_string() {
                                run["resolved_model"] = event["model"].clone();
                            }
                            if event["type"] == "turn.completed" && event["usage"].is_object() {
                                usage = Some(event["usage"].clone());
                                source_line = number;
                            }
                        }
                    }
                    line.clear();
                }
            }
            let Some(usage) = usage.filter(Value::is_object) else {
                return Ok(false);
            };
            connection.execute_batch("SAVEPOINT insight_usage_recovery")?;
            let stored = store_insight_usage(
                connection,
                config,
                &run,
                &usage,
                text(
                    &run["completed_at"],
                    text(&run["started_at"], required(&run, "created_at")?),
                ),
                source_line,
            );
            if stored.is_err() {
                connection.execute_batch("ROLLBACK TO insight_usage_recovery")?;
            }
            connection.execute_batch("RELEASE insight_usage_recovery")?;
            stored?;
            Ok(true)
        })();
        match result {
            Ok(true) => recovered += 1,
            Ok(false) => {}
            Err(error) if error.code == "database" => return Err(error),
            Err(_) => { /* Retain the Run and its unavailable observation for later repair. */ }
        }
    }
    Ok(recovered)
}
