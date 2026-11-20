use crate::backend::{db, now, BackendError, Result};
use rusqlite::{params, params_from_iter, types::Value as SqlValue, Connection};
use rust_decimal::{Decimal, RoundingStrategy};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{str::FromStr, sync::OnceLock};

pub const DEFAULT_SNAPSHOT: &str = "ccusage-20.0.14-litellm-20260718";
pub const UNAVAILABLE_SNAPSHOT: &str = "official-price-unavailable-20260925-v1";
pub const OFFICIAL_CALCULATOR: &str = "localbrain-usage-cost-v3-official-dated-tier";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedUsageRecord {
    pub usage_record_id: String,
    pub source_record_id: String,
    pub source_line: i64,
    pub occurred_at: Option<String>,
    pub raw_model: Option<String>,
    pub input_tokens: Option<serde_json::Number>,
    pub output_tokens: Option<serde_json::Number>,
    pub cache_write_tokens: Option<serde_json::Number>,
    pub cache_read_tokens: Option<serde_json::Number>,
    pub reasoning_tokens: Option<serde_json::Number>,
    pub source_total_tokens: Option<serde_json::Number>,
    pub total_tokens: Option<serde_json::Number>,
    pub total_semantics: String,
    #[serde(default = "direct")]
    pub aggregation_scope: String,
    #[serde(default = "complete")]
    pub capability_state: String,
    #[serde(default = "object")]
    pub capability: Value,
    pub normalized_model: Option<String>,
    pub price_snapshot_id: Option<String>,
}
fn direct() -> String {
    "direct".into()
}
fn complete() -> String {
    "complete".into()
}
fn object() -> Value {
    json!({})
}

#[derive(Debug, Clone, Deserialize)]
struct PriceSpec {
    snapshot_id: String,
    provider: String,
    model: String,
    service_tier: String,
    effective_on: String,
    input_rate: String,
    long_context_threshold: Option<i64>,
    long_input_rate: Option<String>,
    spec_kind: String,
}
#[derive(Deserialize)]
struct Catalog {
    snapshots: Vec<Value>,
    prices: Vec<Value>,
    specs: Vec<PriceSpec>,
}
fn catalog() -> &'static Catalog {
    static CATALOG: OnceLock<Catalog> = OnceLock::new();
    CATALOG.get_or_init(|| {
        serde_json::from_str(include_str!("../../../resources/usage-prices.json"))
            .expect("validated built-in Usage price catalog")
    })
}
fn decimal(value: &str) -> Result<Decimal> {
    Decimal::from_str(value)
        .map_err(|_| BackendError::invalid("price", "Invalid frozen Usage price"))
}
pub fn sql_value(value: &Value) -> Result<SqlValue> {
    Ok(match value {
        Value::Null => SqlValue::Null,
        Value::Bool(v) => SqlValue::Integer(i64::from(*v)),
        Value::String(v) => SqlValue::Text(v.clone()),
        Value::Number(v) => {
            if let Some(n) = v.as_i64() {
                SqlValue::Integer(n)
            } else if v.is_f64() {
                SqlValue::Real(v.as_f64().ok_or_else(|| {
                    BackendError::invalid("number", "Number exceeds SQLite storage range")
                })?)
            } else {
                return Err(BackendError::invalid(
                    "integer",
                    "Integer exceeds SQLite storage range",
                ));
            }
        }
        _ => SqlValue::Text(serde_json::to_string(value)?),
    })
}
fn insert_rows(connection: &Connection, table: &str, records: &[Value]) -> Result<()> {
    for record in records {
        let row = record
            .as_object()
            .ok_or_else(|| BackendError::invalid("catalog", "Invalid built-in price row"))?;
        let columns: Vec<_> = row.keys().map(|s| format!("\"{s}\"")).collect();
        let placeholders = vec!["?"; columns.len()].join(",");
        let sql = format!(
            "INSERT OR IGNORE INTO {table}({}) VALUES ({placeholders})",
            columns.join(",")
        );
        let values: Vec<_> = row.values().map(sql_value).collect::<Result<_>>()?;
        connection.execute(&sql, params_from_iter(values))?;
    }
    Ok(())
}
pub fn ensure_price_snapshots(connection: &Connection) -> Result<()> {
    insert_rows(connection, "usage_price_snapshots", &catalog().snapshots)?;
    insert_rows(connection, "usage_model_prices", &catalog().prices)
}
pub fn normalize_model(raw: Option<&str>) -> Option<String> {
    let value = raw?.trim();
    if value.is_empty() {
        return None;
    }
    Some(
        value
            .strip_prefix("anthropic/")
            .or_else(|| value.strip_prefix("openai/"))
            .unwrap_or(value)
            .into(),
    )
}
pub fn token_number_i128(value: &serde_json::Number) -> i128 {
    value.to_string().parse().unwrap_or_else(|_| {
        if value.to_string().starts_with('-') {
            i128::MIN
        } else {
            i128::MAX
        }
    })
}
pub fn context_tokens(
    input: Option<&serde_json::Number>,
    cache: Option<&serde_json::Number>,
) -> Option<i128> {
    input
        .zip(cache)
        .map(|(a, b)| token_number_i128(a).saturating_add(token_number_i128(b)))
}
pub fn select_snapshot(
    provider: &str,
    model: Option<&str>,
    occurred_at: Option<&str>,
    tier: &str,
    context_tokens: Option<i128>,
) -> String {
    let (Some(model), Some(occurred_at)) = (model, occurred_at) else {
        return UNAVAILABLE_SNAPSHOT.into();
    };
    if occurred_at.len() < 10 || !occurred_at.is_char_boundary(10) {
        return UNAVAILABLE_SNAPSHOT.into();
    }
    let model = if provider == "claude" {
        model.strip_prefix("anthropic/").unwrap_or(model)
    } else if provider == "codex" {
        model.strip_prefix("openai/").unwrap_or(model)
    } else {
        model
    };
    let selected = catalog()
        .specs
        .iter()
        .filter(|s| {
            s.spec_kind != "fast_long_proxy"
                && s.provider == provider
                && s.model == model
                && s.service_tier == tier
                && s.effective_on.as_str() <= &occurred_at[..10]
        })
        .max_by_key(|s| &s.effective_on);
    let Some(selected) = selected else {
        return UNAVAILABLE_SNAPSHOT.into();
    };
    if context_tokens
        .zip(selected.long_context_threshold)
        .is_some_and(|(n, limit)| n > i128::from(limit))
        && selected.long_input_rate.is_none()
    {
        if let Some(proxy) = catalog().specs.iter().find(|s| {
            s.spec_kind == "fast_long_proxy"
                && s.model == selected.model
                && s.effective_on == selected.effective_on
                && s.service_tier == selected.service_tier
        }) {
            return proxy.snapshot_id.clone();
        }
    }
    selected.snapshot_id.clone()
}
fn selected_rate<'a>(
    row: &'a Value,
    short: &str,
    long: &str,
    long_context: bool,
) -> Option<&'a str> {
    row[if long_context { long } else { short }].as_str()
}
pub fn calculate_estimated_cost(
    record: &ParsedUsageRecord,
    price: Option<&Value>,
) -> Result<(String, Option<String>)> {
    let empty = |state: &str| Ok((state.to_owned(), None));
    if record.capability_state == "malformed" {
        return empty("failed");
    }
    let Some(price) = price else {
        return empty("unpriced");
    };
    let (Some(input), Some(output)) = (record.input_tokens.as_ref(), record.output_tokens.as_ref())
    else {
        return empty("partial");
    };
    let threshold = price["long_context_threshold_tokens"].as_i64();
    if threshold.is_some() && record.cache_read_tokens.is_none() {
        return empty("partial");
    }
    let context = token_number_i128(input).saturating_add(
        record
            .cache_read_tokens
            .as_ref()
            .map(token_number_i128)
            .unwrap_or(0),
    );
    let long = threshold.is_some_and(|n| context > i128::from(n));
    if long && record.capability["context_scope"] == "turn_total" {
        return empty("partial");
    }
    let Some(input_rate) = selected_rate(
        price,
        "input_usd_per_million",
        "long_context_input_usd_per_million",
        long,
    ) else {
        return empty("partial");
    };
    let Some(output_rate) = selected_rate(
        price,
        "output_usd_per_million",
        "long_context_output_usd_per_million",
        long,
    ) else {
        return empty("partial");
    };
    let mut components = vec![
        (input.clone(), input_rate.to_owned()),
        (output.clone(), output_rate.to_owned()),
    ];
    let one_hour = match record.capability.get("cache_write_1h_tokens") {
        None => 0,
        Some(v) => match v.as_i64() {
            Some(n) if n >= 0 => n,
            _ => return empty("partial"),
        },
    };
    let mut writes = record.cache_write_tokens.clone();
    if one_hour != 0 {
        if writes
            .as_ref()
            .is_none_or(|n| token_number_i128(n) < i128::from(one_hour))
        {
            return empty("partial");
        }
        let spec = catalog().specs.iter().find(|s| {
            s.spec_kind == "official"
                && s.provider == "claude"
                && price["snapshot_id"] == s.snapshot_id
        });
        let Some(spec) = spec else {
            return empty("partial");
        };
        components.push((
            one_hour.into(),
            (decimal(&spec.input_rate)? * Decimal::TWO).to_string(),
        ));
        writes = writes.map(|n| {
            let number = token_number_i128(&n) - i128::from(one_hour);
            serde_json::Number::from_str(&number.to_string()).expect("integer arithmetic")
        });
    }
    for (tokens, base, long_rate) in [
        (
            writes,
            "cache_write_usd_per_million",
            "long_context_cache_write_usd_per_million",
        ),
        (
            record.cache_read_tokens.clone(),
            "cache_read_usd_per_million",
            "long_context_cache_read_usd_per_million",
        ),
    ] {
        let rate = selected_rate(price, base, long_rate, long);
        if long && !price[base].is_null() && rate.is_none() {
            return empty("partial");
        }
        let Some(rate) = rate else {
            continue;
        };
        let Some(tokens) = tokens else {
            return empty("partial");
        };
        components.push((tokens, rate.into()));
    }
    let mut amount = Decimal::ZERO;
    for (tokens, rate) in components {
        let component = decimal(&tokens.to_string())?
            .checked_mul(decimal(&rate)?)
            .and_then(|v| v.checked_div(Decimal::from(1_000_000)))
            .ok_or_else(|| {
                BackendError::invalid("price", "Usage amount exceeds supported decimal range")
            })?;
        amount = amount.checked_add(component).ok_or_else(|| {
            BackendError::invalid("price", "Usage amount exceeds supported decimal range")
        })?;
    }
    let rounded = amount.round_dp_with_strategy(12, RoundingStrategy::MidpointNearestEven);
    Ok(("priced".into(), Some(format!("{rounded:.12}"))))
}
fn from_stored(row: &Value, capability: Value) -> Result<ParsedUsageRecord> {
    let mut value = row.clone();
    let map = value
        .as_object_mut()
        .ok_or_else(|| BackendError::invalid("usage", "Invalid Usage record"))?;
    map.insert("usage_record_id".into(), row["id"].clone());
    map.insert("capability".into(), capability);
    map.entry("total_semantics").or_insert(json!("unknown"));
    serde_json::from_value(value).map_err(Into::into)
}
fn price_row(connection: &Connection, snapshot: &str, model: &str) -> Result<Option<Value>> {
    db::row(
        connection,
        "SELECT * FROM usage_model_prices WHERE snapshot_id=? AND model_name=?",
        params![snapshot, model],
    )
}
pub fn initialize_prices(connection: &Connection) -> Result<()> {
    ensure_price_snapshots(connection)?;
    for model in ["gpt-5.3-codex-spark", "gpt-6.1-sol", "gpt-6.1-terra"] {
        let rows=db::rows(connection,"SELECT usage_records.* FROM usage_records JOIN sources ON sources.id=usage_records.source_id WHERE sources.provider_kind='codex' AND usage_records.model_name=? AND usage_records.calculation_state='unpriced' AND usage_records.price_snapshot_id=?",params![model,UNAVAILABLE_SNAPSHOT])?;
        for row in rows {
            let Ok(capability) =
                serde_json::from_str::<Value>(row["capability_json"].as_str().unwrap_or("{}"))
            else {
                continue;
            };
            let Some(tier) = capability["service_tier"]
                .as_str()
                .filter(|s| ["standard", "fast"].contains(s))
            else {
                continue;
            };
            let context = row["input_tokens"]
                .as_i64()
                .zip(row["cache_read_tokens"].as_i64())
                .map(|(a, b)| i128::from(a) + i128::from(b));
            let snapshot = select_snapshot(
                "codex",
                Some(model),
                row["occurred_at"].as_str(),
                tier,
                context,
            );
            if snapshot == UNAVAILABLE_SNAPSHOT {
                continue;
            }
            let price = price_row(connection, &snapshot, model)?.ok_or_else(|| {
                BackendError::new(500, "price", "Selected Codex price snapshot is unavailable")
            })?;
            let (state, cost) =
                calculate_estimated_cost(&from_stored(&row, capability)?, Some(&price))?;
            if state == "priced" {
                connection.execute("UPDATE usage_records SET calculation_state='priced',estimated_cost_usd=?,price_snapshot_id=?,calculator_version=?,calculated_at=? WHERE id=? AND model_name=? AND calculation_state='unpriced' AND price_snapshot_id=?",params![cost,snapshot,OFFICIAL_CALCULATOR,now(),row["id"].as_str(),model,UNAVAILABLE_SNAPSHOT])?;
            }
        }
    }
    // Only the previously approved missing historical Fast tier is repaired.
    // Already priced observations and their immutable attribution remain intact.
    let rows=db::rows(connection,"SELECT usage_records.* FROM usage_records JOIN sources ON sources.id=usage_records.source_id WHERE sources.provider_kind='codex' AND usage_records.calculation_state='partial'",[])?;
    for row in rows {
        let Some(current) = catalog().specs.iter().find(|s| {
            s.spec_kind == "official"
                && s.provider == "codex"
                && s.service_tier == "fast"
                && s.long_input_rate.is_none()
                && row["price_snapshot_id"] == s.snapshot_id
                && catalog().specs.iter().any(|p| {
                    p.spec_kind == "fast_long_proxy"
                        && p.model == s.model
                        && p.effective_on == s.effective_on
                })
        }) else {
            continue;
        };
        let Ok(capability) =
            serde_json::from_str::<Value>(row["capability_json"].as_str().unwrap_or("{}"))
        else {
            continue;
        };
        if capability["service_tier"] != "fast" {
            continue;
        }
        let Some(context) = row["input_tokens"]
            .as_i64()
            .zip(row["cache_read_tokens"].as_i64())
            .map(|(a, b)| i128::from(a) + i128::from(b))
        else {
            continue;
        };
        let previous = select_snapshot(
            "codex",
            Some(&current.model),
            row["occurred_at"].as_str(),
            "fast",
            None,
        );
        if previous != current.snapshot_id {
            continue;
        }
        let snapshot = select_snapshot(
            "codex",
            Some(&current.model),
            row["occurred_at"].as_str(),
            "fast",
            Some(context),
        );
        if !catalog()
            .specs
            .iter()
            .any(|s| s.spec_kind == "fast_long_proxy" && s.snapshot_id == snapshot)
        {
            continue;
        }
        let price = price_row(connection, &snapshot, &current.model)?.ok_or_else(|| {
            BackendError::new(
                500,
                "price",
                "Fast long-context proxy price snapshot is unavailable",
            )
        })?;
        let (state, cost) =
            calculate_estimated_cost(&from_stored(&row, capability)?, Some(&price))?;
        if state == "priced" {
            connection.execute("UPDATE usage_records SET calculation_state='priced',estimated_cost_usd=?,price_snapshot_id=?,calculator_version=?,calculated_at=? WHERE id=? AND calculation_state='partial' AND price_snapshot_id=?",params![cost,snapshot,OFFICIAL_CALCULATOR,now(),row["id"].as_str(),previous])?;
        }
    }
    Ok(())
}

const ATTRIBUTION: [&str; 7] = [
    "workspace_id_snapshot",
    "project_key",
    "project_name_snapshot",
    "project_path_snapshot",
    "project_git_root_snapshot",
    "attribution_basis",
    "attributed_at",
];

fn attribution(connection: &Connection, workspace: Option<i64>) -> Result<Value> {
    let row = match workspace {
        Some(id) => db::row(
            connection,
            "SELECT id,display_name,canonical_path,git_root FROM workspaces WHERE id=?",
            [id],
        )?,
        None => None,
    };
    let Some(row) = row else {
        return Ok(
            json!({"workspace_id_snapshot":null,"project_key":null,"project_name_snapshot":null,"project_path_snapshot":null,"project_git_root_snapshot":null,"attribution_basis":"unassigned"}),
        );
    };
    let git = row["git_root"].as_str().filter(|v| !v.is_empty());
    let path = git.or_else(|| row["canonical_path"].as_str()).unwrap_or("");
    Ok(
        json!({"workspace_id_snapshot":row["id"],"project_key":format!("{}:{path}",if git.is_some(){"git"}else{"path"}),"project_name_snapshot":row["display_name"],"project_path_snapshot":row["canonical_path"],"project_git_root_snapshot":row["git_root"],"attribution_basis":if git.is_some(){"git_root"}else{"workspace_path"}}),
    )
}

fn python_json(value: &Value) -> Result<String> {
    fn sorted(value: &Value) -> Value {
        match value {
            Value::Object(map) => {
                let mut keys: Vec<_> = map.keys().collect();
                keys.sort();
                let mut output = serde_json::Map::new();
                for key in keys {
                    output.insert(key.clone(), sorted(&map[key]));
                }
                Value::Object(output)
            }
            Value::Array(items) => Value::Array(items.iter().map(sorted).collect()),
            other => other.clone(),
        }
    }
    let compact = serde_json::to_string(&sorted(value))?;
    let mut result = String::new();
    let mut quoted = false;
    let mut escaped = false;
    for ch in compact.chars() {
        result.push(ch);
        if quoted {
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '"' {
                quoted = false;
            }
        } else if ch == '"' {
            quoted = true;
        } else if ch == ',' || ch == ':' {
            result.push(' ');
        }
    }
    Ok(result)
}

/// Reconcile observations while preserving their frozen pricing and attribution.
pub fn store_usage_records(
    connection: &Connection,
    source_id: i64,
    session_id: i64,
    records: &[ParsedUsageRecord],
    workspace_id: Option<i64>,
    normalizer: &str,
) -> Result<()> {
    ensure_price_snapshots(connection)?;
    let existing = db::rows(
        connection,
        "SELECT * FROM usage_records WHERE session_id=? ORDER BY source_line,id",
        [session_id],
    )?;
    let by_id: std::collections::HashMap<_, _> = existing
        .iter()
        .filter_map(|r| r["id"].as_str().map(|id| (id, r)))
        .collect();
    let by_native: std::collections::HashMap<_, _> = existing
        .iter()
        .filter_map(|r| r["source_record_id"].as_str().map(|id| (id, r)))
        .collect();
    let changed = !existing.is_empty()
        && existing
            .iter()
            .any(|r| r["normalizer_version"] != normalizer);
    let mut records: Vec<_> = records.iter().collect();
    records.sort_by(|a, b| {
        (a.source_line, &a.usage_record_id).cmp(&(b.source_line, &b.usage_record_id))
    });
    connection.execute_batch("SAVEPOINT usage_record_reconcile")?;
    let apply = (|| -> Result<()> {
        let mut workspace_snapshot = None;
        let columns = [
            "id",
            "source_id",
            "session_id",
            "source_record_id",
            "source_line",
            "occurred_at",
            "raw_model",
            "model_name",
            "input_tokens",
            "output_tokens",
            "cache_write_tokens",
            "cache_read_tokens",
            "reasoning_tokens",
            "source_total_tokens",
            "total_tokens",
            "total_semantics",
            "aggregation_scope",
            "capability_state",
            "capability_json",
            "calculation_state",
            "estimated_cost_usd",
            "price_snapshot_id",
            "calculator_version",
            "normalizer_version",
            "calculated_at",
            "workspace_id_snapshot",
            "project_key",
            "project_name_snapshot",
            "project_path_snapshot",
            "project_git_root_snapshot",
            "attribution_basis",
            "attributed_at",
            "imported_at",
        ];
        let updates: Vec<_> = columns
            .iter()
            .filter(|key| {
                !["id", "source_id", "session_id"].contains(key) && !ATTRIBUTION.contains(key)
            })
            .map(|key| format!("{key}=excluded.{key}"))
            .collect();
        let sql = format!(
            "INSERT INTO usage_records({}) VALUES ({}) ON CONFLICT(id) DO UPDATE SET {}",
            columns.join(","),
            vec!["?"; columns.len()].join(","),
            updates.join(",")
        );
        let mut statement = connection.prepare(&sql)?;
        for record in records {
            let record_id = by_native
                .get(record.source_record_id.as_str())
                .and_then(|r| r["id"].as_str())
                .map(str::to_owned)
                .unwrap_or_else(|| {
                    crate::files::digest(
                        format!(
                            "source-usage\u{1f}{source_id}\u{1f}{}",
                            record.usage_record_id
                        )
                        .as_bytes(),
                    )
                });
            let old = by_id.get(record_id.as_str()).copied();
            if old.is_some_and(|r| r["capability_state"] != "malformed")
                && record.capability_state == "malformed"
            {
                continue;
            }
            let reference = old.or_else(|| {
                if changed {
                    existing
                        .iter()
                        .filter(|r| {
                            r["source_line"]
                                .as_i64()
                                .is_some_and(|n| n <= record.source_line)
                        })
                        .max_by(|a, b| {
                            (a["source_line"].as_i64(), a["id"].as_str())
                                .cmp(&(b["source_line"].as_i64(), b["id"].as_str()))
                        })
                        .or_else(|| existing.first())
                } else {
                    None
                }
            });
            let snapshot = record
                .price_snapshot_id
                .as_deref()
                .filter(|s| !s.is_empty())
                .or_else(|| {
                    reference
                        .and_then(|r| r["price_snapshot_id"].as_str())
                        .filter(|s| !s.is_empty())
                })
                .unwrap_or(DEFAULT_SNAPSHOT);
            let model = normalize_model(
                record
                    .normalized_model
                    .as_deref()
                    .filter(|s| !s.is_empty())
                    .or(record.raw_model.as_deref()),
            );
            let price = match &model {
                Some(model) => price_row(connection, snapshot, model)?,
                None => None,
            };
            let calculator = db::row(
                connection,
                "SELECT calculator_version FROM usage_price_snapshots WHERE id=?",
                [snapshot],
            )?
            .and_then(|v| v["calculator_version"].as_str().map(str::to_owned))
            .unwrap_or_else(|| "localbrain-usage-cost-v1".into());
            let (state, cost) = calculate_estimated_cost(record, price.as_ref())?;
            let mut values = json!({"id":record_id,"source_id":source_id,"session_id":session_id,"source_record_id":record.source_record_id,"source_line":record.source_line,"occurred_at":record.occurred_at,"raw_model":record.raw_model,"model_name":model,"input_tokens":record.input_tokens,"output_tokens":record.output_tokens,"cache_write_tokens":record.cache_write_tokens,"cache_read_tokens":record.cache_read_tokens,"reasoning_tokens":record.reasoning_tokens,"source_total_tokens":record.source_total_tokens,"total_tokens":record.total_tokens,"total_semantics":record.total_semantics,"aggregation_scope":record.aggregation_scope,"capability_state":record.capability_state,"capability_json":python_json(&record.capability)?,"calculation_state":state,"estimated_cost_usd":cost,"price_snapshot_id":snapshot,"calculator_version":calculator,"normalizer_version":normalizer});
            let attribution = if let Some(reference) = reference {
                reference
            } else {
                if workspace_snapshot.is_none() {
                    workspace_snapshot = Some(attribution(connection, workspace_id)?);
                }
                workspace_snapshot.as_ref().unwrap()
            };
            for key in ATTRIBUTION {
                values[key] = attribution[key].clone();
            }
            if reference.is_none() {
                values["attributed_at"] = json!(now());
            }
            let unchanged = old.is_some_and(|old| {
                [
                    "normalizer_version",
                    "calculator_version",
                    "price_snapshot_id",
                    "calculation_state",
                    "estimated_cost_usd",
                    "raw_model",
                    "input_tokens",
                    "output_tokens",
                    "cache_write_tokens",
                    "cache_read_tokens",
                    "reasoning_tokens",
                    "source_total_tokens",
                    "total_tokens",
                ]
                .iter()
                .all(|key| old[*key] == values[*key])
            });
            values["calculated_at"] = if unchanged {
                old.unwrap()["calculated_at"].clone()
            } else {
                json!(now())
            };
            values["imported_at"] = json!(now());
            let sql_values: Vec<_> = columns
                .iter()
                .map(|key| sql_value(&values[*key]))
                .collect::<Result<_>>()?;
            statement.execute(params_from_iter(sql_values))?;
        }
        Ok(())
    })();
    if let Err(error) = apply {
        connection
            .execute_batch("ROLLBACK TO usage_record_reconcile; RELEASE usage_record_reconcile")?;
        return Err(error);
    }
    connection.execute_batch("RELEASE usage_record_reconcile")?;
    Ok(())
}

pub fn reconcile_usage_record_contract(
    connection: &Connection,
    source_id: i64,
    expected: &[String],
) -> Result<()> {
    connection.execute_batch("CREATE TEMP TABLE IF NOT EXISTS expected_usage_record_ids(id TEXT PRIMARY KEY); DELETE FROM expected_usage_record_ids")?;
    for id in expected {
        connection.execute(
            "INSERT OR IGNORE INTO expected_usage_record_ids(id) VALUES (?)",
            [id],
        )?;
    }
    connection.execute("DELETE FROM usage_records WHERE source_id=? AND id NOT IN (SELECT id FROM expected_usage_record_ids) AND session_id NOT IN (SELECT sessions.id FROM sessions WHERE sessions.source_id=? AND sessions.session_class='maintenance' AND sessions.index_policy='metadata_only' AND sessions.external_id IN (SELECT 'localbrain-insight:' || id FROM personal_insight_runs))",[source_id,source_id])?;
    connection.execute("DELETE FROM expected_usage_record_ids", [])?;
    Ok(())
}

pub fn price_existing_incomplete_astra_records(connection: &Connection) -> Result<usize> {
    repair_incomplete(
        connection,
        "gpt-6-astra",
        "ccusage-codex-fast-context-tier-astra-codex-fields-20260924",
        &[
            "ccusage-20.0.17-codex-fast-context-tier-20260718",
            "ccusage-codex-fast-context-tier-astra-20260924",
        ],
    )
}
pub fn price_existing_incomplete_sol_records(connection: &Connection) -> Result<usize> {
    repair_incomplete(
        connection,
        "gpt-6-sol",
        "ccusage-codex-fast-context-tier-sol-codex-fields-20260924",
        &["ccusage-20.0.17-codex-fast-context-tier-20260718"],
    )
}
fn repair_incomplete(
    connection: &Connection,
    model: &str,
    target: &str,
    eligible: &[&str],
) -> Result<usize> {
    let price = price_row(connection, target, model)?.ok_or_else(|| {
        BackendError::new(
            500,
            "price",
            format!("{model} price snapshot is unavailable"),
        )
    })?;
    let rows=db::rows(connection,"SELECT usage_records.* FROM usage_records JOIN sources ON sources.id=usage_records.source_id WHERE sources.provider_kind='codex' AND usage_records.model_name=? AND usage_records.calculation_state IN ('unpriced','partial')",[model])?;
    let mut count = 0;
    for row in rows {
        if !eligible.contains(&row["price_snapshot_id"].as_str().unwrap_or("")) {
            continue;
        }
        let (state, cost) = calculate_estimated_cost(&from_stored(&row, json!({}))?, Some(&price))?;
        count+=connection.execute("UPDATE usage_records SET calculation_state=?,estimated_cost_usd=?,price_snapshot_id=?,calculator_version='localbrain-usage-cost-v2-context-tier',calculated_at=? WHERE id=? AND model_name=? AND calculation_state IN ('unpriced','partial') AND price_snapshot_id=?",params![state,cost,target,now(),row["id"].as_str(),model,row["price_snapshot_id"].as_str()])?;
    }
    Ok(count)
}
