use super::super::common::{first, nonempty, stable_id, truth};
use crate::backend::{
    usage::{select_snapshot, ParsedUsageRecord},
    Result,
};
use serde_json::{json, Map, Number, Value};
use std::{cmp::Ordering, collections::HashMap};

pub(super) const CODEX_IDENTITY: &str =
    "codex-last-token-usage-v7-fast-context-tier-response-message-fallback-guardian-spark-price";
type Count = String;
fn count(value: &Value) -> Option<Count> {
    let n = value.as_number()?.to_string();
    if n == "-0" {
        return Some("0".into());
    }
    (!n.is_empty() && n.bytes().all(|c| c.is_ascii_digit())).then_some(n)
}
fn compare(a: &str, b: &str) -> Ordering {
    a.len().cmp(&b.len()).then_with(|| a.cmp(b))
}
fn add(a: &str, b: &str) -> String {
    let mut a = a.bytes().rev();
    let mut b = b.bytes().rev();
    let mut digits = vec![];
    let mut carry = 0;
    loop {
        let x = a.next();
        let y = b.next();
        if x.is_none() && y.is_none() && carry == 0 {
            break;
        }
        let n = x.map(|c| c - b'0').unwrap_or(0) + y.map(|c| c - b'0').unwrap_or(0) + carry;
        digits.push(b'0' + n % 10);
        carry = n / 10;
    }
    digits.reverse();
    String::from_utf8(digits).unwrap()
}
fn subtract(a: &str, b: &str) -> String {
    let mut b = b.bytes().rev();
    let mut digits = vec![];
    let mut borrow = 0i16;
    for a in a.bytes().rev() {
        let mut n = (a - b'0') as i16 - b.next().map(|c| c - b'0').unwrap_or(0) as i16 - borrow;
        borrow = if n < 0 {
            n += 10;
            1
        } else {
            0
        };
        digits.push(b'0' + n as u8);
    }
    while digits.len() > 1 && digits.last() == Some(&b'0') {
        digits.pop();
    }
    digits.reverse();
    String::from_utf8(digits).unwrap()
}
fn sum(values: &[&Option<Count>]) -> Option<Count> {
    let mut result = String::from("0");
    for value in values {
        result = add(&result, value.as_deref()?);
    }
    Some(result)
}
fn number(value: Option<Count>) -> Option<Number> {
    value.map(|v| v.parse().expect("canonical integer"))
}
fn context(value: Option<Count>) -> Option<i128> {
    value.map(|v| v.parse().unwrap_or(i128::MAX))
}
fn required(usage: &Value, cap: &mut Map<String, Value>, name: &str) -> (Option<Count>, bool) {
    if usage.get(name).is_none() {
        cap.insert(name.into(), json!("missing"));
        return (None, false);
    }
    let value = count(&usage[name]);
    cap.insert(
        name.into(),
        json!(if value.is_some() {
            "available"
        } else {
            "malformed"
        }),
    );
    let bad = value.is_none();
    (value, bad)
}
pub(super) fn claude(
    source: &super::super::source_json::SourceJson,
    external: &str,
    line: i64,
    timestamp: Option<String>,
    record: &Value,
) -> Result<Option<ParsedUsageRecord>> {
    let message = &record["message"];
    let usage = &message["usage"];
    if !usage.is_object() {
        return Ok(None);
    }
    let raw_model = nonempty(&message["model"]);
    let mut cap = Map::new();
    let (input, mut malformed) = required(usage, &mut cap, "input_tokens");
    let (output, bad) = required(usage, &mut cap, "output_tokens");
    malformed |= bad;
    let nested = &usage["cache_creation"];
    let (nested_total, one_hour) = if nested.is_object() {
        let hour = count(nested.get("ephemeral_1h_input_tokens").unwrap_or(&json!(0)));
        let five = count(nested.get("ephemeral_5m_input_tokens").unwrap_or(&json!(0)));
        let total = sum(&[&hour, &five]);
        (total, hour.filter(|_| five.is_some()))
    } else {
        (None, None)
    };
    let aggregate = usage
        .get("cache_creation_input_tokens")
        .filter(|v| !v.is_null());
    let aggregate_number = aggregate.and_then(count);
    let integer_like = aggregate.and_then(|v| match v {
        Value::Bool(v) => Some(if *v { "1" } else { "0" }.into()),
        _ => count(v),
    });
    let zero = aggregate.is_some_and(|v| v.as_f64() == Some(0.0) || v == false);
    let (write, write_source) = match aggregate {
        None if nested.is_object() => (nested_total.clone(), "nested_breakdown"),
        None => (Some("0".into()), "default_zero"),
        Some(_) if zero && nested_total.as_deref().is_some_and(|n| n != "0") => {
            (nested_total.clone(), "nested_preferred_over_zero_aggregate")
        }
        Some(_)
            if integer_like
                .as_ref()
                .zip(nested_total.as_ref())
                .is_some_and(|(a, b)| a != b) =>
        {
            (aggregate_number, "aggregate_breakdown_mismatch")
        }
        _ => (aggregate_number, "aggregate"),
    };
    cap.insert("cache_write_source".into(), json!(write_source));
    cap.insert(
        "cache_write_tokens".into(),
        json!(if write.is_some() {
            "available"
        } else {
            "malformed"
        }),
    );
    malformed |= write.is_none();
    if let Some(hour) = one_hour {
        cap.insert("cache_write_1h_tokens".into(), json!(number(Some(hour))));
    }
    let read = count(usage.get("cache_read_input_tokens").unwrap_or(&json!(0)));
    cap.insert(
        "cache_read_tokens".into(),
        json!(if read.is_some() {
            "available"
        } else {
            "malformed"
        }),
    );
    malformed |= read.is_none();
    let source_total = if usage.get("total_tokens").is_some() {
        let v = count(&usage["total_tokens"]);
        cap.insert(
            "source_total_tokens".into(),
            json!(if v.is_some() {
                "available"
            } else {
                "malformed"
            }),
        );
        malformed |= v.is_none();
        v
    } else {
        cap.insert("source_total_tokens".into(), json!("not_reported"));
        None
    };
    cap.insert(
        "model".into(),
        json!(if raw_model.is_some() {
            "available"
        } else {
            "missing"
        }),
    );
    cap.insert("reasoning_tokens".into(), json!("not_separately_reported"));
    let identity = first(&[&message["id"], &record["uuid"]]);
    let identity = if truth(identity) {
        source.python_string(identity)
    } else {
        stable_id(&["claude-usage-line", external, &line.to_string()])
    };
    let snapshot = select_snapshot(
        "claude",
        raw_model.as_deref(),
        timestamp.as_deref(),
        "standard",
        None,
    );
    let total = sum(&[&input, &output, &write, &read]);
    let state = if malformed {
        "malformed"
    } else if raw_model.is_none() || input.is_none() || output.is_none() {
        "partial"
    } else {
        "complete"
    };
    Ok(Some(ParsedUsageRecord{usage_record_id:stable_id(&["claude-usage",external,&identity]),source_record_id:identity,source_line:line,occurred_at:timestamp,raw_model,input_tokens:number(input),output_tokens:number(output),cache_write_tokens:number(write),cache_read_tokens:number(read),reasoning_tokens:None,source_total_tokens:number(source_total),total_tokens:number(total),total_semantics:"normalized_non_cached_input_plus_output_plus_cache_write_plus_cache_read;reasoning_not_separately_reported".into(),aggregation_scope:"direct".into(),capability_state:state.into(),capability:Value::Object(cap),normalized_model:None,price_snapshot_id:Some(snapshot)}))
}
pub(super) fn update_previous(previous: &mut HashMap<String, Count>, payload: &Value) {
    let cumulative = &payload["info"]["total_token_usage"];
    if !cumulative.is_object() {
        return;
    }
    for name in [
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "reasoning_output_tokens",
        "total_tokens",
    ] {
        if let Some(v) = count(&cumulative[name]) {
            previous.insert(name.into(), v);
        }
    }
}
pub(super) fn model(value: &Value) -> Option<String> {
    nonempty(&value["model"])
        .or_else(|| nonempty(&value["model_name"]))
        .or_else(|| nonempty(&value["metadata"]["model"]))
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
pub(super) fn codex(
    external: &str,
    line: i64,
    timestamp: Option<String>,
    payload: &Value,
    turn: Option<&str>,
    raw_model: Option<String>,
    previous: &HashMap<String, Count>,
    tier: &str,
    tier_source: &str,
) -> Result<Option<ParsedUsageRecord>> {
    let info = &payload["info"];
    let (usage, usage_source) = if info["last_token_usage"].is_object() {
        (&info["last_token_usage"], "last_token_usage")
    } else if info["total_token_usage"].is_object() {
        (&info["total_token_usage"], "cumulative_delta")
    } else {
        return Ok(None);
    };
    let mut cap = Map::new();
    let mut malformed = false;
    let mut reset = false;
    let mut component = |name: &str| -> Option<Count> {
        if usage.get(name).is_none() {
            cap.insert(name.into(), json!("missing"));
            return None;
        }
        let Some(value) = count(&usage[name]) else {
            cap.insert(name.into(), json!("malformed"));
            malformed = true;
            return None;
        };
        let (value, state) = if usage_source == "last_token_usage" {
            (value, "direct_event")
        } else {
            let prior = previous.get(name).map(String::as_str).unwrap_or("0");
            if compare(&value, prior) == Ordering::Less {
                reset = true;
                (value, "cumulative_reset")
            } else {
                (subtract(&value, prior), "cumulative_delta")
            }
        };
        cap.insert(name.into(), json!(state));
        Some(value)
    };
    let source_input = component("input_tokens");
    let output = component("output_tokens");
    let read = component("cached_input_tokens");
    let reasoning = component("reasoning_output_tokens");
    let source_total = component("total_tokens");
    if !malformed
        && [&source_input, &output, &read, &reasoning, &source_total]
            .iter()
            .all(|v| v.as_deref().is_none_or(|n| n == "0"))
    {
        return Ok(None);
    }
    let input = match source_input.as_deref().zip(read.as_deref()) {
        Some((a, b)) if compare(b, a) != Ordering::Greater => Some(subtract(a, b)),
        Some(_) => {
            malformed = true;
            cap.insert(
                "input_tokens".into(),
                json!("malformed_cache_exceeds_input"),
            );
            None
        }
        None => None,
    };
    let (normalized_model, resolution) = match raw_model.as_deref() {
        None => ("gpt-5".into(), "missing_source_fallback"),
        Some("codex-auto-review") => {
            let date = timestamp
                .as_deref()
                .unwrap_or("")
                .chars()
                .take(10)
                .collect::<String>();
            let versions = [
                ("2026-04-23", "gpt-5.5"),
                ("2026-03-05", "gpt-5.4"),
                ("2026-02-05", "gpt-5.3-codex"),
                ("2025-12-11", "gpt-5.2-codex"),
                ("2025-11-13", "gpt-5.1-codex"),
                ("2025-09-15", "gpt-5-codex"),
                ("2025-08-07", "gpt-5"),
            ];
            match versions.iter().find(|(d, _)| date.as_str() >= *d) {
                Some((_, m)) => (m.to_string(), "dated_auto_review_fallback"),
                None => ("gpt-5".into(), "dated_auto_review_fallback_before_snapshot"),
            }
        }
        Some(v) => (v.to_owned(), "source"),
    };
    for (k, v) in [
        ("cache_write_tokens", "not_supported"),
        (
            "model",
            if raw_model.is_some() {
                "available"
            } else {
                "missing"
            },
        ),
        ("usage_source", usage_source),
        ("model_resolution", resolution),
        ("service_tier", tier),
        ("service_tier_source", tier_source),
    ] {
        cap.insert(k.into(), json!(v));
    }
    let total = sum(&[&input, &output, &read]);
    if reasoning
        .as_deref()
        .zip(output.as_deref())
        .is_some_and(|(a, b)| compare(a, b) == Ordering::Greater)
    {
        malformed = true;
        cap.insert(
            "reasoning_output_tokens".into(),
            json!("malformed_exceeds_output"),
        );
    }
    if let Some((a, b)) = source_total.as_ref().zip(total.as_ref()) {
        cap.insert(
            "source_total_consistency".into(),
            json!(if a == b { "matches" } else { "mismatch" }),
        );
    }
    let state = if malformed {
        "malformed"
    } else if reset
        || raw_model.is_none()
        || cap.get("source_total_consistency") == Some(&json!("mismatch"))
        || [&input, &output, &read, &reasoning]
            .iter()
            .any(|v| v.is_none())
    {
        "partial"
    } else {
        "complete"
    };
    let identity = stable_id(&[
        "codex-usage-record",
        CODEX_IDENTITY,
        external,
        turn.unwrap_or("unscoped"),
        &line.to_string(),
    ]);
    let snapshot = select_snapshot(
        "codex",
        Some(&normalized_model),
        timestamp.as_deref(),
        tier,
        context(sum(&[&input, &read])),
    );
    Ok(Some(ParsedUsageRecord{usage_record_id:stable_id(&["codex-usage",CODEX_IDENTITY,external,&identity]),source_record_id:identity,source_line:line,occurred_at:timestamp,raw_model,input_tokens:number(input),output_tokens:number(output),cache_write_tokens:None,cache_read_tokens:number(read),reasoning_tokens:number(reasoning),source_total_tokens:number(source_total),total_tokens:number(total),total_semantics:format!("{usage_source};source_input_includes_cache_read;normalized_non_cached_input_plus_output_plus_cache_read;reasoning_subset_of_output"),aggregation_scope:"direct".into(),capability_state:state.into(),capability:Value::Object(cap),normalized_model:Some(normalized_model),price_snapshot_id:Some(snapshot)}))
}
