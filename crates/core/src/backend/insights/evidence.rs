//! Bounded read-only source evidence. Selection never executes an analyzer.
use super::{invalid, text};
use crate::backend::{clock, db, unicode, Result};
use chrono::{DateTime, Datelike, NaiveDate, Utc};
use rusqlite::{params, params_from_iter, types::Value as SqlValue, Connection};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, VecDeque};

pub const MANIFEST_VERSION: &str = "personal-insight-evidence-v2";
pub const MAX_SESSIONS: usize = 100;
pub const MAX_EXCERPTS: usize = 300;
pub const MAX_EXCERPT_CHARS: usize = 600;
pub const MAX_TOTAL_CHARS: usize = 120_000;
pub const MAX_QUESTION_CHARS: usize = 2_000;
pub const MAX_SEARCH_TERMS: usize = 16;
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceRequest {
    pub mode: String,
    pub requested_at: DateTime<Utc>,
    pub question: Option<String>,
    pub source_ids: Option<Vec<i64>>,
    pub date_from: Option<String>,
    pub date_to: Option<String>,
    pub timezone: String,
}
impl EvidenceRequest {
    pub fn new(mode: impl Into<String>, requested_at: DateTime<Utc>) -> Self {
        Self {
            mode: mode.into(),
            requested_at,
            question: None,
            source_ids: None,
            date_from: None,
            date_to: None,
            timezone: "Asia/Seoul".into(),
        }
    }
}
pub(super) fn utc_text(value: DateTime<Utc>) -> String {
    clock::isoformat(value).replace("+00:00", "Z")
}
fn strict_date(value: Option<&str>, name: &str) -> Result<Option<NaiveDate>> {
    let Some(value) = value else {
        return Ok(None);
    };
    let chars = value.chars().collect::<Vec<_>>();
    if chars.len() != 10
        || chars[4] != '-'
        || chars[7] != '-'
        || chars.iter().enumerate().any(|(i, c)| {
            i != 4
                && i != 7
                && unicode_general_category::get_general_category(*c)
                    != unicode_general_category::GeneralCategory::DecimalNumber
        })
    {
        return Err(invalid(&format!("{name} must be YYYY-MM-DD")));
    }
    clock::parse_date(value)
        .filter(|date| date.year() >= 1 && value.is_ascii())
        .map(Some)
        .ok_or_else(|| invalid(&format!("{name} must be a valid date")))
}
fn terms(value: &str) -> Vec<String> {
    let mut seen = BTreeSet::new();
    value
        .split(|ch| !unicode::python_alnum(ch))
        .filter(|word| !word.is_empty())
        .map(unicode::casefold)
        .filter(|word| seen.insert(word.clone()))
        .collect()
}
fn event_time(value: &Value) -> Option<DateTime<Utc>> {
    // The frozen evidence parser does not strip surrounding whitespace.
    value
        .as_str()
        .filter(|s| !s.is_empty())
        .and_then(|s| clock::parse_iso_datetime(&s.replace('Z', "+00:00")))
        .and_then(|t| t.utc())
}
fn event_conditions(
    requested: &str,
    start: Option<&str>,
    end: Option<&str>,
) -> (String, Vec<SqlValue>) {
    let mut sql="e.event_type='message' AND e.role IN ('user','assistant') AND e.text IS NOT NULL AND length(trim(e.text))>0 AND (julianday(e.occurred_at) IS NULL OR julianday(e.occurred_at)<=julianday(?))".to_owned();
    let mut params = vec![SqlValue::Text(requested.into())];
    for (value, condition) in [
        (start, " AND julianday(e.occurred_at)>=julianday(?)"),
        (end, " AND julianday(e.occurred_at)<julianday(?)"),
    ] {
        if let Some(value) = value {
            sql.push_str(condition);
            params.push(SqlValue::Text(value.into()));
        }
    }
    (sql, params)
}
fn eligible_sessions(
    connection: &Connection,
    sources: &[i64],
    conditions: &str,
    params: &[SqlValue],
) -> Result<Vec<Value>> {
    if sources.is_empty() {
        return Ok(vec![]);
    }
    let placeholders = vec!["?"; sources.len()].join(",");
    let mut all = sources
        .iter()
        .map(|n| SqlValue::Integer(*n))
        .collect::<Vec<_>>();
    all.extend_from_slice(params);
    db::rows(connection,&format!("SELECT s.id AS session_id,src.id AS source_id,src.provider_kind,COUNT(e.id) AS message_count,SUM(CASE WHEN julianday(e.occurred_at) IS NULL THEN 1 ELSE 0 END) AS unknown_time_count,strftime('%Y-%m-%dT%H:%M:%SZ',MAX(julianday(e.occurred_at))) AS latest_event_at FROM sessions AS s JOIN sources AS src ON src.id=s.source_id JOIN activity_events AS e ON e.session_id=s.id WHERE s.session_class='work' AND s.session_role='primary' AND s.index_policy='full' AND src.provider_kind IN ('claude','codex') AND src.id IN ({placeholders}) AND {conditions} GROUP BY s.id,src.id,src.provider_kind ORDER BY s.id"),params_from_iter(all))
}
fn spread_order(rows: impl IntoIterator<Item = Value>, zone: &str) -> Result<Vec<Value>> {
    let mut buckets: BTreeMap<(i64, String), Vec<Value>> = BTreeMap::new();
    for row in rows {
        let month = match event_time(&row["latest_event_at"]) {
            Some(time) => clock::local_day(time, zone)?.format("%Y-%m").to_string(),
            None => "unknown".into(),
        };
        buckets
            .entry((row["source_id"].as_i64().unwrap(), month))
            .or_default()
            .push(row);
    }
    let mut keys = buckets.keys().cloned().collect::<Vec<_>>();
    keys.sort_by(|a, b| (b.1 != "unknown", &b.1, b.0).cmp(&(a.1 != "unknown", &a.1, a.0)));
    let mut buckets = buckets
        .into_iter()
        .map(|(key, mut rows)| {
            rows.sort_by(|a, b| {
                text(&b["latest_event_at"], "")
                    .cmp(text(&a["latest_event_at"], ""))
                    .then_with(|| a["session_id"].as_i64().cmp(&b["session_id"].as_i64()))
            });
            (key, VecDeque::from(rows))
        })
        .collect::<BTreeMap<_, _>>();
    let mut ordered = vec![];
    loop {
        let mut added = false;
        for key in &keys {
            if let Some(row) = buckets.get_mut(key).unwrap().pop_front() {
                ordered.push(row);
                added = true;
            }
        }
        if !added {
            break;
        }
    }
    Ok(ordered)
}
fn decimal_identity(value: &str) -> Result<Option<i64>> {
    if value.is_empty() || !value.chars().all(unicode::python_digit) {
        return Ok(None);
    }
    let mut n = 0i64;
    for c in value.chars() {
        if unicode_general_category::get_general_category(c)
            != unicode_general_category::GeneralCategory::DecimalNumber
        {
            return Err(invalid("invalid numeric search entity identity"));
        }
        let mut start = c as u32;
        while start > 0
            && char::from_u32(start - 1).is_some_and(|c| {
                unicode_general_category::get_general_category(c)
                    == unicode_general_category::GeneralCategory::DecimalNumber
            })
        {
            start -= 1;
        }
        n = n
            .checked_mul(10)
            .and_then(|n| n.checked_add(i64::from((c as u32 - start) % 10)))
            .ok_or_else(|| invalid("search entity identity exceeds supported integer range"))?;
    }
    Ok(Some(n))
}
fn fts_ranked(connection: &Connection, terms: &[String]) -> Result<Vec<i64>> {
    if terms.is_empty() {
        return Ok(vec![]);
    }
    let expression = terms
        .iter()
        .map(|word| format!("body:\"{word}\""))
        .collect::<Vec<_>>()
        .join(" OR ");
    let mut ranked = vec![];
    let mut seen = BTreeSet::new();
    for row in db::rows(connection,"SELECT entity_id,bm25(search_index) AS fts_score FROM search_index WHERE search_index MATCH ? AND entity_type='session' ORDER BY fts_score,entity_id",[expression])?{if let Some(id)=decimal_identity(text(&row["entity_id"],""))?{if seen.insert(id){ranked.push(id);}}}
    Ok(ranked)
}
#[derive(Clone)]
struct Picked {
    event: Value,
    overlap: BTreeSet<String>,
}
fn pick_events(
    connection: &Connection,
    session: &Value,
    conditions: &str,
    event_params: &[SqlValue],
    search: &BTreeSet<String>,
) -> Result<Vec<Picked>> {
    let mut params = vec![SqlValue::Integer(session["session_id"].as_i64().unwrap())];
    params.extend_from_slice(event_params);
    let mut statement=connection.prepare(&format!("SELECT e.id,e.sequence,e.occurred_at,e.role,e.text FROM activity_events AS e WHERE e.session_id=? AND {conditions} ORDER BY e.sequence,e.id"))?;
    let mut rows = statement.query(params_from_iter(params))?;
    let count = session["message_count"].as_u64().unwrap_or(0) as usize;
    let positions = [0, count / 2, count.saturating_sub(1)];
    let mut spread = vec![];
    let mut ranked: Vec<Picked> = vec![];
    let mut index = 0;
    while let Some(row) = rows.next()? {
        let body: String = row.get(4)?;
        let event = json!({"id":row.get::<_,String>(0)?,"sequence":row.get::<_,i64>(1)?,"occurred_at":row.get::<_,Option<String>>(2)?,"role":row.get::<_,String>(3)?,"text":body,"message_index":index});
        if positions.contains(&index) {
            spread.push(Picked {
                event: event.clone(),
                overlap: BTreeSet::new(),
            });
        }
        if !search.is_empty() {
            let words = terms(text(&event["text"], ""))
                .into_iter()
                .collect::<BTreeSet<_>>();
            let overlap = search
                .intersection(&words)
                .cloned()
                .collect::<BTreeSet<_>>();
            if !overlap.is_empty() {
                ranked.push(Picked { event, overlap });
                ranked.sort_by(|a, b| {
                    b.overlap
                        .len()
                        .cmp(&a.overlap.len())
                        .then_with(|| (a.event["role"] != "user").cmp(&(b.event["role"] != "user")))
                        .then_with(|| {
                            a.event["sequence"]
                                .as_i64()
                                .cmp(&b.event["sequence"].as_i64())
                        })
                        .then_with(|| text(&a.event["id"], "").cmp(text(&b.event["id"], "")))
                });
                ranked.truncate(3);
            }
        }
        index += 1;
    }
    Ok(if ranked.is_empty() { spread } else { ranked })
}
fn excerpt(body: &str, matched: &BTreeSet<String>, available: usize) -> (String, usize, usize) {
    let chars = body.chars().collect::<Vec<_>>();
    let mut start = 0;
    if !matched.is_empty() {
        let folded = unicode::casefold(body);
        if let Some(position) = matched
            .iter()
            .filter_map(|term| folded.find(term).map(|byte| folded[..byte].chars().count()))
            .min()
        {
            let mut original = 0;
            let mut consumed = 0;
            while original < chars.len() {
                let width = unicode::casefold(&chars[original].to_string())
                    .chars()
                    .count();
                if consumed + width > position {
                    break;
                }
                consumed += width;
                original += 1;
            }
            start = original.saturating_sub(120);
        }
    }
    let end = chars
        .len()
        .min(start + MAX_EXCERPT_CHARS)
        .min(start + available);
    (chars[start..end].iter().collect(), start, end)
}
pub fn build_insight_evidence_manifest(
    connection: &Connection,
    request: &EvidenceRequest,
) -> Result<Value> {
    if !["ask", "discover"].contains(&request.mode.as_str()) {
        return Err(invalid("mode must be ask or discover"));
    }
    clock::local_day(request.requested_at, &request.timezone)
        .map_err(|_| invalid("timezone must be an IANA timezone"))?;
    let first = strict_date(request.date_from.as_deref(), "date_from")?;
    let last = strict_date(request.date_to.as_deref(), "date_to")?;
    if first.zip(last).is_some_and(|(a, b)| a > b) {
        return Err(invalid("date_from must not be after date_to"));
    }
    let question = if request.mode == "ask" {
        let question = request
            .question
            .as_deref()
            .map(|s| s.trim_matches(unicode::python_space))
            .filter(|s| !s.is_empty())
            .ok_or_else(|| invalid("ask requires a question"))?;
        if question.chars().count() > MAX_QUESTION_CHARS {
            return Err(invalid("question exceeds 2,000 characters"));
        }
        Some(question.to_owned())
    } else {
        if request.question.is_some() {
            return Err(invalid("discover does not accept a question"));
        }
        None
    };
    let requested_sources = if let Some(sources) = &request.source_ids {
        if sources.is_empty() || sources.iter().any(|n| *n <= 0) {
            return Err(invalid("source_ids must be nonempty positive source IDs"));
        }
        Some(
            sources
                .iter()
                .copied()
                .collect::<BTreeSet<_>>()
                .into_iter()
                .collect::<Vec<_>>(),
        )
    } else {
        None
    };
    let frozen = utc_text(request.requested_at);
    let start = first
        .map(|day| {
            clock::calendar_day_bounds(day, &request.timezone).map(|(start, _)| utc_text(start))
        })
        .transpose()?;
    let end = last
        .map(|day| clock::calendar_day_bounds(day, &request.timezone).map(|(_, end)| utc_text(end)))
        .transpose()?;
    let (conditions, event_params) = event_conditions(&frozen, start.as_deref(), end.as_deref());
    let search = question
        .as_deref()
        .map(terms)
        .unwrap_or_default()
        .into_iter()
        .take(MAX_SEARCH_TERMS)
        .collect::<Vec<_>>();
    connection.execute_batch("SAVEPOINT personal_insight_evidence_read")?;
    let result = (|| {
        let registry=db::rows(connection,"SELECT id,provider_kind FROM sources WHERE provider_kind IN ('claude','codex') ORDER BY id",[])?.into_iter().map(|v|(v["id"].as_i64().unwrap(),text(&v["provider_kind"],"").to_owned())).collect::<BTreeMap<_,_>>();
        let sources = requested_sources.unwrap_or_else(|| registry.keys().copied().collect());
        if sources.iter().any(|id| !registry.contains_key(id)) {
            return Err(invalid(
                "source_ids contains an unknown Claude/Codex source",
            ));
        }
        let eligible = eligible_sessions(connection, &sources, &conditions, &event_params)?;
        let undated = if (first.is_some() || last.is_some()) && !sources.is_empty() {
            connection.query_row(&format!("SELECT COUNT(*) FROM sessions AS s JOIN sources AS src ON src.id=s.source_id JOIN activity_events AS e ON e.session_id=s.id WHERE s.session_class='work' AND s.session_role='primary' AND s.index_policy='full' AND src.provider_kind IN ('claude','codex') AND src.id IN ({}) AND e.event_type='message' AND e.role IN ('user','assistant') AND e.text IS NOT NULL AND length(trim(e.text))>0 AND julianday(e.occurred_at) IS NULL",vec!["?";sources.len()].join(",")),params_from_iter(&sources),|row|row.get::<_,i64>(0))?
        } else {
            0
        };
        let by_id = eligible
            .iter()
            .map(|v| (v["session_id"].as_i64().unwrap(), v.clone()))
            .collect::<BTreeMap<_, _>>();
        let mut source_coverage:BTreeMap<i64,Value>=sources.iter().map(|id|(*id,json!({"provider_kind":registry[id],"eligible_sessions":0,"eligible_messages":0,"selected_sessions":0,"selected_excerpts":0,"selected_undated_messages":0,"selected_first_at":null,"selected_last_at":null}))).collect();
        for row in &eligible {
            let coverage = source_coverage
                .get_mut(&row["source_id"].as_i64().unwrap())
                .unwrap();
            increment(coverage, "eligible_sessions", 1);
            increment(
                coverage,
                "eligible_messages",
                row["message_count"].as_i64().unwrap(),
            );
        }
        let ranked = if request.mode == "ask" {
            fts_ranked(connection, &search)?
                .into_iter()
                .filter(|id| by_id.contains_key(id))
                .collect::<Vec<_>>()
        } else {
            vec![]
        };
        let mut candidates = ranked
            .iter()
            .take(70)
            .map(|id| by_id[id].clone())
            .collect::<Vec<_>>();
        let already = candidates
            .iter()
            .map(|v| v["session_id"].as_i64().unwrap())
            .collect::<BTreeSet<_>>();
        let fill = spread_order(
            eligible
                .iter()
                .filter(|v| !already.contains(&v["session_id"].as_i64().unwrap()))
                .cloned(),
            &request.timezone,
        )?;
        candidates.extend(fill.into_iter().take(MAX_SESSIONS - candidates.len()));
        let search = search.into_iter().collect::<BTreeSet<_>>();
        let mut included = vec![];
        let mut selected_excerpts = 0;
        let mut total_chars = 0;
        let mut lexical = 0;
        let mut times = vec![];
        let mut source_times: BTreeMap<i64, Vec<DateTime<Utc>>> = BTreeMap::new();
        let mut unknown_selected = 0;
        let mut truncated = 0;
        for session in candidates {
            if selected_excerpts >= MAX_EXCERPTS || total_chars >= MAX_TOTAL_CHARS {
                break;
            }
            let id = session["session_id"].as_i64().unwrap();
            let source = session["source_id"].as_i64().unwrap();
            let mut chosen =
                pick_events(connection, &session, &conditions, &event_params, &search)?;
            chosen.sort_by(|a, b| {
                a.event["sequence"]
                    .as_i64()
                    .cmp(&b.event["sequence"].as_i64())
                    .then_with(|| text(&a.event["id"], "").cmp(text(&b.event["id"], "")))
            });
            let mut events = vec![];
            for picked in chosen {
                if selected_excerpts >= MAX_EXCERPTS || total_chars >= MAX_TOTAL_CHARS {
                    break;
                }
                let event = picked.event;
                let body = text(&event["text"], "");
                let (sample, start, end) =
                    excerpt(body, &picked.overlap, MAX_TOTAL_CHARS - total_chars);
                if sample.is_empty() {
                    break;
                }
                if let Some(time) = event_time(&event["occurred_at"]) {
                    times.push(time);
                    source_times.entry(source).or_default().push(time);
                } else {
                    unknown_selected += 1;
                    increment(
                        source_coverage.get_mut(&source).unwrap(),
                        "selected_undated_messages",
                        1,
                    );
                }
                let length = body.chars().count();
                let sample_len = sample.chars().count();
                truncated += usize::from(start != 0 || end != length);
                events.push(json!({"source_id":source,"provider_kind":session["provider_kind"],"session_id":id,"event_id":event["id"],"sequence":event["sequence"],"message_index":event["message_index"],"role":event["role"],"occurred_at":event["occurred_at"],"text_revision":format!("{:x}",Sha256::digest(body.as_bytes())),"text_length":length,"excerpt":sample,"excerpt_start":start,"excerpt_end":end,"selection_basis":if picked.overlap.is_empty(){"spread"}else{"lexical"},"session_url":format!("/sessions/{id}")}));
                selected_excerpts += 1;
                total_chars += sample_len;
                lexical += usize::from(!picked.overlap.is_empty());
            }
            if !events.is_empty() {
                increment(
                    source_coverage.get_mut(&source).unwrap(),
                    "selected_sessions",
                    1,
                );
                increment(
                    source_coverage.get_mut(&source).unwrap(),
                    "selected_excerpts",
                    events.len() as i64,
                );
                included.push(json!({"source_id":source,"provider_kind":session["provider_kind"],"session_id":id,"session_url":format!("/sessions/{id}"),"events":events,"message_count":session["message_count"]}));
            }
        }
        for (source, times) in &source_times {
            let row = source_coverage.get_mut(source).unwrap();
            row["selected_first_at"] = json!(times.iter().min().copied().map(utc_text));
            row["selected_last_at"] = json!(times.iter().max().copied().map(utc_text));
        }
        let eligible_messages = eligible
            .iter()
            .map(|v| v["message_count"].as_u64().unwrap())
            .sum::<u64>();
        let mut omissions = vec![];
        if eligible.is_empty() {
            omissions.push("no_eligible_messages");
        }
        if eligible.len() > included.len() {
            omissions.push("session_sample_limit");
        }
        if eligible_messages > selected_excerpts as u64 {
            omissions.push("message_sample_limit");
        }
        if total_chars >= MAX_TOTAL_CHARS {
            omissions.push("character_limit");
        }
        if request.mode == "ask" && ranked.is_empty() {
            omissions.push("no_indexed_lexical_match");
        }
        if request.mode == "ask" && !ranked.is_empty() && lexical == 0 {
            omissions.push("no_selected_message_lexical_match");
        }
        if undated > 0 {
            omissions.push("undated_messages_excluded_by_date_scope");
        }
        Ok(
            json!({"version":MANIFEST_VERSION,"generated_at":frozen,"scope":{"mode":request.mode,"question":question,"source_ids":sources,"date_from":request.date_from,"date_to":request.date_to,"timezone":request.timezone,"event_from_utc":start,"event_to_exclusive_utc":end,"requested_at":frozen},"selection":{"method":if request.mode=="ask"{"fts70_plus_source_month_spread_v1"}else{"source_month_spread_v1"},"indexed_session_count":ranked.len(),"lexical_excerpt_count":lexical,"lexical_match_state":if request.mode!="ask"{"not_applicable"}else if lexical>0{"matched"}else{"none"}},"coverage":{"eligible_sessions":eligible.len(),"eligible_messages":eligible_messages,"selected_sessions":included.len(),"selected_excerpts":selected_excerpts,"excerpt_characters":total_chars,"truncated_excerpts":truncated,"eligible_undated_messages":eligible.iter().map(|v|v["unknown_time_count"].as_i64().unwrap_or(0)).sum::<i64>(),"undated_messages_excluded":undated,"selected_undated_messages":unknown_selected,"selected_first_at":times.iter().min().copied().map(utc_text),"selected_last_at":times.iter().max().copied().map(utc_text),"sources":source_coverage,"omission_reasons":omissions},"sessions":included}),
        )
    })();
    connection.execute_batch("RELEASE SAVEPOINT personal_insight_evidence_read")?;
    result
}
fn increment(row: &mut Value, key: &str, amount: i64) {
    row[key] = json!(row[key].as_i64().unwrap_or(0) + amount);
}
pub fn resolve_insight_evidence_reference(
    connection: &Connection,
    reference: &Value,
) -> Result<Value> {
    if !reference.is_object()
        || [
            "provider_kind",
            "session_id",
            "event_id",
            "sequence",
            "role",
            "occurred_at",
            "text_revision",
        ]
        .iter()
        .any(|key| reference.get(*key).is_none())
    {
        return Err(invalid("reference is missing required fields"));
    }
    let id = reference["session_id"]
        .as_i64()
        .filter(|v| *v > 0)
        .ok_or_else(|| invalid("reference has an invalid session_id"))?;
    let event = crate::backend::usage::sql_value(&reference["event_id"])?;
    let row=db::row(connection,"SELECT s.id AS session_id,s.session_class,s.session_role,s.index_policy,src.id AS source_id,src.provider_kind,e.id AS event_id,e.event_type,e.sequence,e.role,e.occurred_at,e.text FROM sessions AS s JOIN sources AS src ON src.id=s.source_id LEFT JOIN activity_events AS e ON e.session_id=s.id AND e.id=? WHERE s.id=?",params![event,id])?;
    let Some(row) = row else {
        return Ok(json!({"status":"unavailable","session_url":null}));
    };
    let destination = format!("/sessions/{id}");
    if row["event_id"].is_null() {
        return Ok(json!({"status":"unavailable","session_url":destination}));
    }
    let digest = format!("{:x}", Sha256::digest(text(&row["text"], "").as_bytes()));
    let same = row["session_class"] == "work"
        && row["session_role"] == "primary"
        && row["index_policy"] == "full"
        && reference
            .get("source_id")
            .is_none_or(|value| *value == row["source_id"])
        && row["provider_kind"] == reference["provider_kind"]
        && row["event_type"] == "message"
        && ["user", "assistant"].contains(&text(&row["role"], ""))
        && row["role"] == reference["role"]
        && row["sequence"] == reference["sequence"]
        && row["occurred_at"] == reference["occurred_at"]
        && reference["text_revision"] == digest;
    Ok(json!({"status":if same{"current"}else{"stale"},"session_url":destination}))
}
