use super::validation::{
    choice, failure, hash, key, local_route, text, CONFIDENCE_VALUES, OUTCOME_VALUES,
    QUESTION_DEPTHS, SELECTION_SIGNALS,
};
use super::{validate_packet, MAX_PACKET_BYTES};
use crate::backend::{clock, db, unicode::splitlines, Result};
use chrono::{DateTime, Days, NaiveDate, Utc};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet, HashSet};
fn value_labels(family: &str) -> Value {
    crate::backend::value_registry::value_family(family).expect("compiled learning family")
        ["presentation"]["labels"]
        .clone()
}

fn string(value: &Value) -> &str {
    value.as_str().unwrap_or("")
}
fn id(value: &Value) -> i64 {
    value.as_i64().unwrap_or(0)
}
fn truth(value: &Value) -> bool {
    value
        .as_bool()
        .unwrap_or_else(|| value.as_i64().is_some_and(|value| value != 0))
}
fn stamp(now: DateTime<Utc>) -> String {
    clock::stamp(now)
}

pub fn local_day(timestamp: &str, timezone_name: &str) -> Result<NaiveDate> {
    let parsed = clock::parse_timestamp(timestamp)
        .ok_or_else(|| failure("학습 기록의 시각을 확인할 수 없습니다."))?;
    day_at(parsed, timezone_name)
}
fn day_at(now: DateTime<Utc>, timezone_name: &str) -> Result<NaiveDate> {
    clock::local_day(now, timezone_name)
        .map_err(|_| failure("학습에 사용할 시간대를 확인해 주세요."))
}
pub fn today(timezone_name: &str) -> Result<NaiveDate> {
    day_at(Utc::now(), timezone_name)
}

pub(super) fn sorted_value(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<_> = map.keys().collect();
            keys.sort();
            Value::Object(
                keys.into_iter()
                    .map(|key| (key.clone(), sorted_value(&map[key])))
                    .collect(),
            )
        }
        Value::Array(values) => Value::Array(values.iter().map(sorted_value).collect()),
        value => value.clone(),
    }
}
pub fn canonical_json(value: &Value) -> Result<String> {
    Ok(serde_json::to_string(&sorted_value(value))?)
}
fn python_json_size(value: &Value) -> Result<usize> {
    let compact = serde_json::to_string(value)?;
    let mut size = compact.len();
    let (mut quoted, mut escape) = (false, false);
    for ch in compact.chars() {
        if quoted {
            if escape {
                escape = false;
            } else if ch == '\\' {
                escape = true;
            } else if ch == '"' {
                quoted = false;
            }
        } else if ch == '"' {
            quoted = true;
        } else if matches!(ch, ',' | ':') {
            size += 1;
        }
    }
    Ok(size)
}
pub fn import_packet(connection: &Connection, raw: &Value, timezone_name: &str) -> Result<Value> {
    import_packet_at(connection, raw, timezone_name, Utc::now())
}
/// All input/source validation precedes writes. The caller owns the transaction.
pub fn import_packet_at(
    connection: &Connection,
    raw: &Value,
    timezone_name: &str,
    now: DateTime<Utc>,
) -> Result<Value> {
    let lessons = validate_packet(raw, day_at(now, timezone_name)?)?;
    if python_json_size(raw)? > MAX_PACKET_BYTES {
        return Err(failure("패킷은 2 MiB 이하여야 합니다."));
    }
    for lesson in &lessons {
        for source in lesson["sources"].as_array().unwrap() {
            let url = string(&source["url"]);
            if source["kind"] == "work"
                && !url.is_empty()
                && !local_source_available(connection, url)?
            {
                return Err(failure("source.url: 업무 원문을 찾을 수 없습니다. 주소를 비우고 원래 위치를 locator에 남겨 주세요."));
            }
        }
    }
    let mut inserted = 0;
    for lesson in &lessons {
        let content = canonical_json(lesson)?;
        let revision = hash(&content);
        inserted+=connection.execute("INSERT INTO learning_lessons (lesson_key,revision,title,packet_json,created_at) VALUES (?,?,?,?,?) ON CONFLICT(lesson_key,revision) DO NOTHING",
            params![string(&lesson["key"]),revision,string(&lesson["title"]),content,stamp(now)])?;
    }
    Ok(json!({"inserted":inserted,"unchanged":lessons.len()-inserted}))
}
fn local_source_available(connection: &Connection, url: &str) -> Result<bool> {
    if !local_route(url) {
        return Ok(false);
    }
    let parts: Vec<_> = url.split('/').collect();
    if parts[2].len() > 18 {
        return Ok(false);
    }
    let Ok(identifier) = parts[2].parse::<i64>() else {
        return Ok(false);
    };
    let sql = if parts[1] == "sessions" {
        "SELECT 1 FROM sessions WHERE id=?"
    } else {
        "SELECT 1 FROM context_documents WHERE id=?"
    };
    Ok(db::row(connection, sql, [identifier])?.is_some())
}
fn normalized_lesson(mut row: Value) -> Result<Value> {
    let packet: Value = serde_json::from_str(string(&row["packet_json"]))?;
    let Some(packet) = packet.as_object() else {
        return Err(failure("보존된 수업 내용을 확인할 수 없습니다."));
    };
    row.as_object_mut().unwrap().extend(packet.clone());
    Ok(row)
}
pub fn lesson_by_id(connection: &Connection, lesson_id: i64) -> Result<Value> {
    if lesson_id <= 0 {
        return Err(failure(
            "수업을 찾을 수 없습니다. 학습 목록에서 다시 선택해 주세요.",
        ));
    }
    let row = db::row(
        connection,
        "SELECT * FROM learning_lessons WHERE id=?",
        [lesson_id],
    )?
    .ok_or_else(|| failure("수업을 찾을 수 없습니다. 학습 목록에서 다시 선택해 주세요."))?;
    normalized_lesson(row)
}
pub fn attempts_for(connection: &Connection, lesson_id: i64) -> Result<Vec<Value>> {
    db::rows(
        connection,
        "SELECT * FROM learning_attempts WHERE lesson_id=? ORDER BY submitted_at,id",
        [lesson_id],
    )
}
pub fn completed_days(
    attempts: &[Value],
    timezone_name: &str,
    before: Option<NaiveDate>,
) -> Result<BTreeMap<NaiveDate, Value>> {
    let mut ordered: Vec<_> = attempts.iter().collect();
    ordered.sort_by_key(|attempt| (string(&attempt["assessed_at"]), id(&attempt["id"])));
    let mut result = BTreeMap::new();
    for attempt in ordered {
        if attempt["outcome"] == "pending" {
            continue;
        }
        let day = local_day(string(&attempt["assessed_at"]), timezone_name)?;
        if before.is_none_or(|before| day < before) {
            result.insert(day, attempt.clone());
        }
    }
    Ok(result)
}
pub fn schedule(
    attempts: &[Value],
    timezone_name: &str,
    before: Option<NaiveDate>,
) -> Result<Value> {
    let days = completed_days(attempts, timezone_name, before)?;
    let mut streak = 0;
    let mut due = None;
    for (day, attempt) in &days {
        let interval = if attempt["outcome"] == "recalled" && !truth(&attempt["hint_used"]) {
            streak += 1;
            [3, 7, 21][streak.min(3) - 1]
        } else {
            streak = 0;
            1
        };
        due = day.checked_add_days(Days::new(interval));
    }
    Ok(json!({"due":due.map(|day|day.to_string()),"days":days.len()}))
}
fn feedback_aware(lesson: &Value, attempts: &[Value], timezone_name: &str) -> Result<Vec<Value>> {
    if lesson.get("scene").is_none() {
        return Ok(attempts.to_vec());
    }
    let mut ordered = attempts.to_vec();
    ordered.sort_by(|a, b| {
        (string(&a["submitted_at"]), id(&a["id"])).cmp(&(string(&b["submitted_at"]), id(&b["id"])))
    });
    let mut exposed = HashSet::new();
    let mut result = Vec::new();
    for mut attempt in ordered {
        let question = lesson["questions"]
            .as_array()
            .unwrap()
            .iter()
            .find(|q| q["id"] == attempt["question_id"])
            .ok_or_else(|| failure("보존된 질문과 답변 기록이 일치하지 않습니다."))?;
        let key = (
            local_day(string(&attempt["submitted_at"]), timezone_name)?,
            string(&question["concept_id"]).to_string(),
        );
        let assisted = exposed.contains(&key);
        attempt["feedback_assisted"] = assisted.into();
        attempt["hint_used"] = json!(i64::from(truth(&attempt["hint_used"]) || assisted));
        exposed.insert(key);
        result.push(attempt);
    }
    Ok(result)
}
fn next_question(
    lesson: &Value,
    attempts: &[Value],
    timezone_name: &str,
    current: NaiveDate,
) -> Result<Value> {
    let questions = lesson["questions"]
        .as_array()
        .ok_or_else(|| failure("보존된 질문을 확인할 수 없습니다."))?;
    if questions.is_empty() {
        return Err(failure("보존된 질문을 확인할 수 없습니다."));
    }
    if lesson.get("scene").is_none() {
        return Ok(questions
            [completed_days(attempts, timezone_name, Some(current))?.len() % questions.len()]
        .clone());
    }
    let mut previous = Vec::new();
    for attempt in feedback_aware(lesson, attempts, timezone_name)? {
        if attempt["outcome"] != "pending"
            && local_day(string(&attempt["assessed_at"]), timezone_name)? < current
            && local_day(string(&attempt["submitted_at"]), timezone_name)? < current
        {
            previous.push(attempt);
        }
    }
    let mut concepts = Vec::new();
    for question in questions {
        let concept = string(&question["concept_id"]);
        if !concepts.contains(&concept) {
            concepts.push(concept);
        }
    }
    let mut selected = concepts[0];
    let mut minimum = usize::MAX;
    for concept in concepts {
        let mut days = BTreeSet::new();
        for attempt in &previous {
            if questions
                .iter()
                .any(|q| q["id"] == attempt["question_id"] && q["concept_id"] == concept)
            {
                days.insert(local_day(string(&attempt["submitted_at"]), timezone_name)?);
            }
        }
        if days.len() < minimum {
            minimum = days.len();
            selected = concept;
        }
    }
    let candidates: Vec<_> = questions
        .iter()
        .filter(|q| q["concept_id"] == selected)
        .collect();
    let mut depth = "understand";
    for level in QUESTION_DEPTHS {
        let at_level: BTreeSet<_> = candidates
            .iter()
            .filter(|q| q["depth"] == level)
            .map(|q| string(&q["id"]))
            .collect();
        if at_level.is_empty() {
            continue;
        }
        depth = level;
        let mut by_day = BTreeMap::new();
        let mut ordered: Vec<_> = previous.iter().collect();
        ordered.sort_by(|a, b| {
            (string(&a["assessed_at"]), id(&a["id"]))
                .cmp(&(string(&b["assessed_at"]), id(&b["id"])))
        });
        for attempt in ordered {
            if at_level.contains(string(&attempt["question_id"])) {
                by_day.insert(
                    local_day(string(&attempt["submitted_at"]), timezone_name)?,
                    attempt,
                );
            }
        }
        let mut streak = 0;
        for attempt in by_day.values() {
            streak = if attempt["outcome"] == "recalled" && !truth(&attempt["hint_used"]) {
                streak + 1
            } else {
                0
            };
        }
        if streak < 2 {
            break;
        }
    }
    let mut chosen = None;
    let mut earliest = NaiveDate::MAX;
    for question in candidates.into_iter().filter(|q| q["depth"] == depth) {
        let mut last = NaiveDate::MIN;
        for attempt in &previous {
            if attempt["question_id"] == question["id"] {
                last = last.max(local_day(string(&attempt["submitted_at"]), timezone_name)?);
            }
        }
        if chosen.is_none() || last < earliest {
            chosen = Some(question.clone());
            earliest = last;
        }
    }
    chosen.ok_or_else(|| failure("보존된 질문의 학습 단계를 확인할 수 없습니다."))
}
pub fn library(connection: &Connection, timezone_name: &str) -> Result<Vec<Value>> {
    library_at(connection, timezone_name, Utc::now())
}
pub fn library_at(
    connection: &Connection,
    timezone_name: &str,
    now: DateTime<Utc>,
) -> Result<Vec<Value>> {
    let current = day_at(now, timezone_name)?;
    let rows=db::rows(connection,
        "SELECT l.*,COALESCE(v.hidden,0) AS hidden,v.snoozed_until FROM learning_lessons l LEFT JOIN learning_visibility v ON v.lesson_key=l.lesson_key WHERE l.id IN (SELECT MAX(id) FROM learning_lessons GROUP BY lesson_key) ORDER BY l.id",[])?;
    let mut result = Vec::new();
    for row in rows {
        let mut lesson = normalized_lesson(row)?;
        let attempts = attempts_for(connection, id(&lesson["id"]))?;
        let effective = feedback_aware(&lesson, &attempts, timezone_name)?;
        lesson["before_today"] = schedule(&effective, timezone_name, Some(current))?;
        lesson["schedule"] = schedule(&effective, timezone_name, None)?;
        let prior = completed_days(&effective, timezone_name, Some(current))?;
        lesson["last_prior_assessment"] = prior
            .last_key_value()
            .map_or(Value::Null, |(_, attempt)| attempt.clone());
        let mut prior_pending = None;
        for attempt in &attempts {
            if local_day(string(&attempt["submitted_at"]), timezone_name)? < current
                && (attempt["outcome"] == "pending"
                    || local_day(string(&attempt["assessed_at"]), timezone_name)? >= current)
            {
                prior_pending = Some(attempt.clone());
                break;
            }
        }
        lesson["prior_pending"] = prior_pending.unwrap_or(Value::Null);
        lesson["done_today"] = completed_days(&attempts, timezone_name, None)?
            .contains_key(&current)
            .into();
        lesson["snoozed"] = (!lesson["snoozed_until"].is_null()
            && string(&lesson["snoozed_until"]) > current.to_string().as_str())
        .into();
        let mut pending = attempts
            .iter()
            .find(|attempt| attempt["outcome"] == "pending");
        lesson["pending"] = pending.map_or(Value::Null, |attempt| attempt["id"].clone());
        if lesson.get("scene").is_some() && pending.is_none() {
            for attempt in attempts.iter().rev() {
                if attempt["outcome"] != "pending"
                    && local_day(string(&attempt["assessed_at"]), timezone_name)? == current
                {
                    pending = Some(attempt);
                    break;
                }
            }
        }
        lesson["question"] = if let Some(attempt) = pending {
            lesson["questions"]
                .as_array()
                .unwrap()
                .iter()
                .find(|q| q["id"] == attempt["question_id"])
                .cloned()
                .ok_or_else(|| failure("보존된 질문과 답변 기록이 일치하지 않습니다."))?
        } else {
            next_question(&lesson, &attempts, timezone_name, current)?
        };
        result.push(lesson);
    }
    Ok(result)
}
pub fn daily_selection(connection: &Connection, timezone_name: &str) -> Result<Value> {
    daily_selection_at(connection, timezone_name, Utc::now())
}
pub fn daily_selection_at(
    connection: &Connection,
    timezone_name: &str,
    now: DateTime<Utc>,
) -> Result<Value> {
    let lessons = library_at(connection, timezone_name, now)?;
    let current = day_at(now, timezone_name)?.to_string();
    let eligible: Vec<_> = lessons
        .iter()
        .filter(|lesson| !truth(&lesson["hidden"]) && !truth(&lesson["snoozed"]))
        .collect();
    let mut pending: Vec<_> = eligible
        .iter()
        .copied()
        .filter(|lesson| !lesson["prior_pending"].is_null())
        .collect();
    pending.sort_by(|a, b| {
        (string(&a["prior_pending"]["submitted_at"]), id(&a["id"]))
            .cmp(&(string(&b["prior_pending"]["submitted_at"]), id(&b["id"])))
    });
    let mut due: Vec<_> = eligible
        .iter()
        .copied()
        .filter(|lesson| {
            !lesson["before_today"]["due"].is_null()
                && string(&lesson["before_today"]["due"]) <= current.as_str()
        })
        .collect();
    let review_key = |lesson: &Value| {
        let last = &lesson["last_prior_assessment"];
        let help = !last.is_null() && (last["outcome"] != "recalled" || truth(&last["hint_used"]));
        (
            !help,
            string(&lesson["before_today"]["due"]).to_string(),
            id(&lesson["id"]),
        )
    };
    due.sort_by_key(|lesson| review_key(lesson));
    let mut new: Vec<_> = eligible
        .iter()
        .copied()
        .filter(|lesson| lesson["before_today"]["due"].is_null())
        .collect();
    new.sort_by_key(|lesson| {
        let signal = SELECTION_SIGNALS
            .iter()
            .position(|signal| lesson["selection"]["signal"] == *signal)
            .unwrap_or(3);
        (
            signal,
            std::cmp::Reverse(string(&lesson["scene"]["occurred_on"]).to_string()),
            id(&lesson["id"]),
        )
    });
    let review = !pending.is_empty() || !due.is_empty();
    let chosen = if !pending.is_empty() {
        pending.first().copied()
    } else if !due.is_empty() {
        due.first().copied()
    } else {
        new.first().copied()
    };
    let selected: Vec<_> = chosen.into_iter().cloned().collect();
    Ok(
        json!({"new_lessons":if review{Vec::new()}else{selected.clone()},"reviews":if review{selected.clone()}else{Vec::new()},
        "selected_lessons":selected,"has_lessons":!lessons.is_empty(),"all_done":chosen.is_some_and(|lesson|truth(&lesson["done_today"])),"day":current}),
    )
}

pub fn reader(
    connection: &Connection,
    lesson_id: i64,
    timezone_name: &str,
    attempt_id: Option<i64>,
    question_id: Option<&str>,
) -> Result<Value> {
    reader_at(
        connection,
        lesson_id,
        timezone_name,
        attempt_id,
        question_id,
        Utc::now(),
    )
}
pub fn reader_at(
    connection: &Connection,
    lesson_id: i64,
    timezone_name: &str,
    attempt_id: Option<i64>,
    question_id: Option<&str>,
    now: DateTime<Utc>,
) -> Result<Value> {
    let mut lesson = lesson_by_id(connection, lesson_id)?;
    for source in lesson["sources"].as_array_mut().unwrap() {
        source["available"] = if source["kind"] == "work" && !string(&source["url"]).is_empty() {
            local_source_available(connection, string(&source["url"]))?
        } else {
            true
        }
        .into();
    }
    let attempts = attempts_for(connection, lesson_id)?;
    let current = day_at(now, timezone_name)?;
    let mut attempt = if let Some(identifier) = attempt_id {
        attempts
            .iter()
            .find(|attempt| id(&attempt["id"]) == identifier)
    } else {
        attempts
            .iter()
            .find(|attempt| attempt["outcome"] == "pending")
    };
    if question_id.is_some() && attempt_id.is_none() {
        attempt = None;
    } else if lesson.get("scene").is_some() && attempt_id.is_none() && attempt.is_none() {
        for saved in attempts.iter().rev() {
            if saved["outcome"] != "pending"
                && local_day(string(&saved["assessed_at"]), timezone_name)? == current
            {
                attempt = Some(saved);
                break;
            }
        }
    }
    if attempt_id.is_some() && attempt.is_none() {
        return Err(failure("이 수업의 답변 기록을 찾을 수 없습니다."));
    }
    let questions = lesson["questions"].as_array().unwrap();
    let question = if let Some(attempt) = attempt {
        questions
            .iter()
            .find(|question| question["id"] == attempt["question_id"])
            .cloned()
            .ok_or_else(|| failure("보존된 질문과 답변 기록이 일치하지 않습니다."))?
    } else if let Some(identifier) = question_id {
        questions
            .iter()
            .find(|question| question["id"] == identifier)
            .cloned()
            .ok_or_else(|| {
                failure("이 수업의 질문을 찾을 수 없습니다. 학습 목록에서 다시 열어 주세요.")
            })?
    } else {
        next_question(&lesson, &attempts, timezone_name, current)?
    };
    let effective = feedback_aware(&lesson, &attempts, timezone_name)?;
    let assisted = attempt.is_some_and(|attempt| {
        effective.iter().any(|effective| {
            effective["id"] == attempt["id"] && truth(&effective["feedback_assisted"])
        })
    });
    let latest = db::row(
        connection,
        "SELECT MAX(id) AS id FROM learning_lessons WHERE lesson_key=?",
        [string(&lesson["key"])],
    )?
    .unwrap()["id"]
        .clone();
    let old = db::rows(
        connection,
        "SELECT id,created_at FROM learning_lessons WHERE lesson_key=? AND id!=? ORDER BY id DESC",
        params![string(&lesson["key"]), lesson_id],
    )?;
    let mut due = false;
    for source in lesson["sources"].as_array().unwrap() {
        let checked = NaiveDate::parse_from_str(string(&source["checked_on"]), "%Y-%m-%d")
            .map_err(|_| failure("보존된 출처 날짜를 확인할 수 없습니다."))?;
        due |= (current - checked).num_days() > 90;
    }
    let practice: Vec<_> = questions
        .iter()
        .filter(|q| q["id"] != question["id"])
        .cloned()
        .collect();
    let scene_lines = splitlines(string(&lesson["scene"]["code"]));
    Ok(
        json!({"lesson":lesson,"question":question,"attempt":attempt,"history":attempts.iter().rev().take(10).cloned().collect::<Vec<_>>(),"other_revisions":old,
        "latest_id":latest,"schedule":schedule(&effective,timezone_name,None)?,"feedback_assisted":assisted,"practice_questions":practice,"scene_lines":scene_lines,
        "source_review_due":due,"confidence_labels":value_labels("learning.confidence"),
        "outcome_labels":value_labels("learning.outcome")}),
    )
}
pub fn submit_attempt(connection: &Connection, lesson_id: i64, fields: &Value) -> Result<i64> {
    submit_attempt_at(connection, lesson_id, fields, Utc::now())
}
pub fn submit_attempt_at(
    connection: &Connection,
    lesson_id: i64,
    fields: &Value,
    now: DateTime<Utc>,
) -> Result<i64> {
    let lesson = lesson_by_id(connection, lesson_id)?;
    let question = key(&fields["question_id"], "질문")?;
    if !lesson["questions"]
        .as_array()
        .unwrap()
        .iter()
        .any(|q| q["id"] == question)
    {
        return Err(failure("이 수업의 질문을 다시 선택해 주세요."));
    }
    let submission = key(&fields["submission_key"], "제출 식별자")?;
    let action = choice(&fields["action"], &["answer", "read"], "학습 방식")?;
    let (answer, confidence, hint, outcome) = if action == "read" {
        (String::new(), None, 0, "read")
    } else {
        let answer = text(
            fields.get("answer").unwrap_or(&json!("")),
            "답변",
            8000,
            false,
        )?;
        let confidence = choice(&fields["confidence"], CONFIDENCE_VALUES, "확신 정도")?;
        let hint = if fields["from_note"] == "1" {
            "1".into()
        } else {
            choice(
                fields.get("hint_used").unwrap_or(&json!("0")),
                &["0", "1"],
                "힌트",
            )?
        };
        (answer, Some(confidence), i64::from(hint == "1"), "pending")
    };
    if let Some(existing) = db::row(
        connection,
        "SELECT * FROM learning_attempts WHERE submission_key=?",
        [&submission],
    )? {
        if id(&existing["lesson_id"]) != lesson_id
            || existing["question_id"] != question
            || existing["answer"] != answer
            || existing["confidence"] != json!(confidence)
            || id(&existing["hint_used"]) != hint
            || (existing["outcome"] == "read") != (action == "read")
        {
            return Err(failure(
                "이미 사용한 제출입니다. 수업을 다시 열어 새 답변을 작성해 주세요.",
            ));
        }
        return Ok(id(&existing["id"]));
    }
    let now = stamp(now);
    connection.execute("INSERT INTO learning_attempts (lesson_id,question_id,submission_key,answer,confidence,hint_used,outcome,submitted_at,assessed_at) VALUES (?,?,?,?,?,?,?,?,?)",
        params![lesson_id,question,submission,answer,confidence,hint,outcome,now,if action=="read"{Some(now.clone())}else{None}])?;
    Ok(connection.last_insert_rowid())
}
pub fn assess_attempt(
    connection: &Connection,
    lesson_id: i64,
    attempt_id: i64,
    outcome: &str,
) -> Result<()> {
    assess_attempt_at(connection, lesson_id, attempt_id, outcome, Utc::now())
}
pub fn assess_attempt_at(
    connection: &Connection,
    lesson_id: i64,
    attempt_id: i64,
    outcome: &str,
    now: DateTime<Utc>,
) -> Result<()> {
    lesson_by_id(connection, lesson_id)?;
    choice(&json!(outcome), &OUTCOME_VALUES[2..], "자기 평가")?;
    let row = db::row(
        connection,
        "SELECT * FROM learning_attempts WHERE id=? AND lesson_id=?",
        params![attempt_id, lesson_id],
    )?
    .ok_or_else(|| failure("답변을 먼저 저장해 주세요."))?;
    if row["outcome"] == outcome {
        return Ok(());
    }
    if row["outcome"] != "pending" {
        return Err(failure(
            "이미 마친 자기 평가입니다. 기록을 확인하거나 다음 복습에서 다시 답해 주세요.",
        ));
    }
    if connection.execute(
        "UPDATE learning_attempts SET outcome=?,assessed_at=? WHERE id=? AND outcome='pending'",
        params![outcome, stamp(now), attempt_id],
    )? == 0
    {
        return Err(failure(
            "다른 화면에서 자기 평가가 변경되었습니다. 기록을 다시 확인해 주세요.",
        ));
    }
    Ok(())
}
pub fn set_visibility(
    connection: &Connection,
    lesson_id: i64,
    action: &str,
    timezone_name: &str,
) -> Result<()> {
    set_visibility_at(connection, lesson_id, action, timezone_name, Utc::now())
}
pub fn set_visibility_at(
    connection: &Connection,
    lesson_id: i64,
    action: &str,
    timezone_name: &str,
    now: DateTime<Utc>,
) -> Result<()> {
    let lesson = lesson_by_id(connection, lesson_id)?;
    choice(&json!(action), &["snooze", "hide", "restore"], "목록 표시")?;
    let until = if action == "snooze" {
        Some(
            day_at(now, timezone_name)?
                .checked_add_days(Days::new(1))
                .ok_or_else(|| failure("학습 날짜 범위를 확인해 주세요."))?
                .to_string(),
        )
    } else {
        None
    };
    connection.execute("INSERT INTO learning_visibility (lesson_key,hidden,snoozed_until,updated_at) VALUES (?,?,?,?) ON CONFLICT(lesson_key) DO UPDATE SET hidden=excluded.hidden,snoozed_until=excluded.snoozed_until,updated_at=excluded.updated_at",
        params![string(&lesson["key"]),i64::from(action=="hide"),until,stamp(now)])?;
    Ok(())
}
