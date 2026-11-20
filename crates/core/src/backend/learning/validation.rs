use super::diff::unified_diff;
use crate::backend::{
    unicode::{lowercase, python_space, splitlines},
    BackendError, Result,
};
use chrono::NaiveDate;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use unicode_normalization::UnicodeNormalization;
pub const MAX_PACKET_BYTES: usize = 2 * 1024 * 1024;
pub(super) const CONFIDENCE_VALUES: &[&str] = &["low", "medium", "high"];
pub(super) const OUTCOME_VALUES: &[&str] = &["pending", "read", "again", "partial", "recalled"];
pub(super) const SOURCE_KINDS: &[&str] = &["work", "official"];
pub(super) const QUESTION_KINDS: &[&str] = &["recall", "apply"];
pub(super) const VERSION_STATUSES: &[&str] = &["matched", "unverified"];
pub(super) const REVIEWER_ROLES: &[&str] = &["owner", "assistant", "unspecified"];
pub(super) const SCENE_KINDS: &[&str] = &["command", "diff"];
pub(super) const SCENE_ORIGINS: &[&str] = &["source", "synthetic"];
pub(super) const EXECUTION_STATES: &[&str] = &["suggested", "reported", "executed", "observed"];
pub(super) const GIT_STATES: &[&str] = &["committed", "staged", "unstaged", "mixed"];
pub(super) const QUESTION_DEPTHS: [&str; 3] = ["understand", "predict", "transfer"];
pub(super) const SELECTION_SIGNALS: [&str; 4] = ["requested", "recurring", "recent", "general"];
pub(super) fn failure(message: impl Into<String>) -> BackendError {
    BackendError::new(422, "learning", message)
}
fn object<'a>(
    value: &'a Value,
    required: &[&str],
    optional: &[&str],
    field: &str,
) -> Result<&'a Map<String, Value>> {
    value
        .as_object()
        .filter(|map| {
            required.iter().all(|key| map.contains_key(*key))
                && map
                    .keys()
                    .all(|key| required.contains(&key.as_str()) || optional.contains(&key.as_str()))
        })
        .ok_or_else(|| {
            failure(format!(
                "{field}: 필수 항목 또는 지원하는 항목을 확인해 주세요."
            ))
        })
}
pub(super) fn text(value: &Value, field: &str, limit: usize, empty: bool) -> Result<String> {
    value
        .as_str()
        .filter(|text| {
            text.chars().count() <= limit
                && (empty || !text.trim_matches(python_space).is_empty())
                && !text.contains('\0')
        })
        .map(|text| text.trim_matches(python_space).to_string())
        .ok_or_else(|| failure(format!("{field}: 텍스트 길이와 내용을 확인해 주세요.")))
}
fn literal(value: &Value, field: &str, limit: usize, empty: bool) -> Result<String> {
    text(value, field, limit, empty)?;
    Ok(value.as_str().unwrap().into())
}
pub(super) fn key(value: &Value, field: &str) -> Result<String> {
    value
        .as_str()
        .filter(|text| {
            (1..=80).contains(&text.len())
                && text.as_bytes()[0].is_ascii_alphanumeric()
                && text
                    .bytes()
                    .all(|ch| ch.is_ascii_alphanumeric() || ch == b'-')
        })
        .map(str::to_string)
        .ok_or_else(|| {
            failure(format!(
                "{field}: 영문·숫자·하이픈으로 된 1–80자 식별자가 필요합니다."
            ))
        })
}
pub(super) fn choice(value: &Value, values: &[&str], field: &str) -> Result<String> {
    value
        .as_str()
        .filter(|value| values.contains(value))
        .map(str::to_string)
        .ok_or_else(|| failure(format!("{field}: 지원하는 값을 선택해 주세요.")))
}
fn list<'a>(value: &'a Value, field: &str, min: usize, max: usize) -> Result<&'a Vec<Value>> {
    value
        .as_array()
        .filter(|items| (min..=max).contains(&items.len()))
        .ok_or_else(|| failure(format!("{field}: 항목 수를 확인해 주세요.")))
}
fn day(value: &Value, field: &str, current: NaiveDate) -> Result<String> {
    let value = text(value, field, 10, false)?;
    let date = NaiveDate::parse_from_str(&value, "%Y-%m-%d")
        .map_err(|_| failure(format!("{field}: YYYY-MM-DD 날짜가 필요합니다.")))?;
    if date.to_string() != value || date > current {
        return Err(failure(format!("{field}: 미래가 아닌 날짜가 필요합니다.")));
    }
    Ok(value)
}
pub(super) fn hash(text: &str) -> String {
    format!("{:x}", Sha256::digest(text.as_bytes()))
}

fn source(raw: &Value, current: NaiveDate, literal_text: bool) -> Result<Value> {
    object(
        raw,
        &[
            "id",
            "kind",
            "title",
            "locator",
            "checked_on",
            "version",
            "snapshot",
        ],
        &["url"],
        "source",
    )?;
    let kind = choice(&raw["kind"], SOURCE_KINDS, "source.kind")?;
    let mut result = json!({"id":key(&raw["id"],"source.id")?,"kind":kind});
    for (field, limit) in [
        ("title", 240),
        ("locator", 2000),
        ("version", 240),
        ("snapshot", 12000),
    ] {
        result[field] = text(&raw[field], &format!("source.{field}"), limit, false)?.into();
    }
    result["checked_on"] = day(&raw["checked_on"], "source.checked_on", current)?.into();
    let url = text(
        raw.get("url").unwrap_or(&json!("")),
        "source.url",
        2000,
        true,
    )?;
    if kind == "official" {
        let valid = official_url(&url);
        if !valid {
            return Err(failure("source.url: 공식 자료의 HTTPS 주소가 필요합니다."));
        }
    } else if !url.is_empty() && !local_route(&url) {
        return Err(failure(
            "source.url: 업무 자료는 로컬 세션·문서 주소만 연결할 수 있습니다.",
        ));
    }
    result["url"] = url.into();
    if literal_text {
        result["snapshot"] = literal(&raw["snapshot"], "source.snapshot", 12000, false)?.into();
    }
    result["snapshot_sha256"] = hash(result["snapshot"].as_str().unwrap()).into();
    Ok(result)
}
fn official_url(value: &str) -> bool {
    if value.chars().any(|ch| python_space(ch) || (ch as u32) < 32) || value.contains('\\') {
        return false;
    }
    let Some((scheme, rest)) = value.split_once("://") else {
        return false;
    };
    if !scheme.eq_ignore_ascii_case("https") {
        return false;
    }
    let authority = rest.split(['/', '?', '#']).next().unwrap_or("");
    if authority.is_empty() {
        return false;
    }
    // Match urlsplit's delimiter-normalization guard without URL parser repair
    // (WHATWG parsing would silently admit `https:///host`).
    let normalized = authority
        .replace(['@', ':', '#', '?'], "")
        .nfkc()
        .collect::<String>();
    if normalized.chars().any(|ch| "/?#@:".contains(ch)) {
        return false;
    }
    let host_port = if let Some((credentials, host)) = authority.rsplit_once('@') {
        let (user, password) = credentials.split_once(':').unwrap_or((credentials, ""));
        if !user.is_empty() || !password.is_empty() {
            return false;
        }
        host
    } else {
        authority
    };
    let (host, port) = if let Some(host) = host_port.strip_prefix('[') {
        let Some((host, tail)) = host.split_once(']') else {
            return false;
        };
        let valid = if let Some(version) = host.strip_prefix('v') {
            version.split_once('.').is_some_and(|(version, address)| {
                !version.is_empty()
                    && version.bytes().all(|ch| ch.is_ascii_hexdigit())
                    && !address.is_empty()
            })
        } else {
            let (address, zone) = host
                .split_once('%')
                .map_or((host, None), |(address, zone)| (address, Some(zone)));
            address.parse::<std::net::Ipv6Addr>().is_ok()
                && zone.is_none_or(|zone| !zone.is_empty() && !zone.contains('%'))
        };
        if !valid {
            return false;
        }
        let port = if tail.is_empty() {
            None
        } else {
            let Some(port) = tail.strip_prefix(':') else {
                return false;
            };
            Some(port)
        };
        (host, port)
    } else {
        if host_port.contains(['[', ']']) {
            return false;
        }
        let mut pieces = host_port.split(':');
        let host = pieces.next().unwrap_or("");
        let port = pieces.next();
        if pieces.next().is_some() {
            return false;
        }
        (host, port)
    };
    !host.is_empty()
        && port.is_none_or(|port| {
            port.is_empty()
                || (port.bytes().all(|ch| ch.is_ascii_digit()) && port.parse::<u16>() == Ok(443))
        })
}
pub(super) fn local_route(value: &str) -> bool {
    let Some(tail) = value
        .strip_prefix("/sessions/")
        .or_else(|| value.strip_prefix("/documents/"))
    else {
        return false;
    };
    !tail.is_empty() && tail.as_bytes()[0] != b'0' && tail.bytes().all(|ch| ch.is_ascii_digit())
}
fn fixed_hash(value: &str) -> bool {
    matches!(value.len(), 40 | 64)
        && value
            .bytes()
            .all(|ch| ch.is_ascii_digit() || (b'a'..=b'f').contains(&ch))
}
fn scene(raw: &Value, sources: &[Value], current: NaiveDate) -> Result<Value> {
    let kind = choice(&raw["kind"], SCENE_KINDS, "scene.kind")?;
    let mut required = vec![
        "kind",
        "source_id",
        "origin",
        "title",
        "language",
        "context",
        "conditions",
        "captured_at",
        "occurred_on",
    ];
    required.extend(if kind == "command" {
        vec!["code", "execution", "output"]
    } else {
        vec![
            "repo",
            "path",
            "before_ref",
            "after_ref",
            "git_state",
            "before",
            "after",
        ]
    });
    object(raw, &required, &[], "scene")?;
    let source_id = key(&raw["source_id"], "scene.source_id")?;
    if !sources
        .iter()
        .any(|source| source["id"] == source_id && source["kind"] == "work")
    {
        return Err(failure(
            "scene.source_id: 수업 안의 업무 근거를 연결해 주세요.",
        ));
    }
    let origin = choice(&raw["origin"], SCENE_ORIGINS, "scene.origin")?;
    let mut result = json!({"kind":kind,"source_id":source_id,"origin":origin});
    for (field, limit) in [
        ("title", 240),
        ("language", 80),
        ("context", 8000),
        ("conditions", 8000),
    ] {
        result[field] = text(&raw[field], &format!("scene.{field}"), limit, false)?.into();
    }
    result["occurred_on"] = if raw["occurred_on"].is_null() {
        Value::Null
    } else {
        day(&raw["occurred_on"], "scene.occurred_on", current)?.into()
    };
    let stamp = text(&raw["captured_at"], "scene.captured_at", 64, false)?;
    let parsed = crate::backend::clock::parse_iso_datetime(&stamp)
        .ok_or_else(|| failure("scene.captured_at: 시간대가 포함된 ISO 시각이 필요합니다."))?;
    if parsed.offset_micros.is_none() || parsed.local.date() > current {
        return Err(failure(
            "scene.captured_at: 미래가 아닌 시간대 포함 시각이 필요합니다.",
        ));
    }
    result["captured_at"] = parsed.isoformat().into();
    if kind == "command" {
        result["code"] = literal(&raw["code"], "scene.code", 48000, false)?.into();
        result["execution"] =
            choice(&raw["execution"], EXECUTION_STATES, "scene.execution")?.into();
        result["output"] = literal(&raw["output"], "scene.output", 48000, true)?.into();
        if result["execution"] == "observed"
            && result["output"]
                .as_str()
                .unwrap()
                .trim_matches(python_space)
                .is_empty()
        {
            return Err(failure(
                "scene.output: 결과 확인 상태에는 관측 자료가 필요합니다.",
            ));
        }
        if origin == "synthetic" && (result["execution"] != "suggested" || result["output"] != "") {
            return Err(failure(
                "scene.execution: 가상 명령은 실행·관측 기록으로 가져올 수 없습니다.",
            ));
        }
    } else {
        for field in ["repo", "path", "before_ref", "after_ref"] {
            let value = text(&raw[field], &format!("scene.{field}"), 2000, false)?;
            if value.chars().any(|ch| (ch as u32) < 32) {
                return Err(failure(format!(
                    "scene.{field}: 한 줄의 식별자가 필요합니다."
                )));
            }
            result[field] = value.into();
        }
        let state = choice(&raw["git_state"], GIT_STATES, "scene.git_state")?;
        result["git_state"] = state.clone().into();
        if origin == "synthetic"
            && !(result["repo"] == "synthetic"
                || result["repo"].as_str().unwrap().starts_with("synthetic:"))
        {
            return Err(failure(
                "scene.repo: 가상 예시는 synthetic 식별자를 사용해 주세요.",
            ));
        }
        for field in ["before", "after"] {
            let body = literal(&raw[field], &format!("scene.{field}"), 96000, true)?;
            let fingerprint = hash(&body);
            result[field] = body.into();
            result[format!("{field}_sha256")] = fingerprint.clone().into();
            let reference = result[format!("{field}_ref")].as_str().unwrap();
            let valid = if origin == "synthetic" {
                reference.starts_with("synthetic:")
            } else {
                fixed_hash(reference)
                    || (state != "committed" && reference == format!("sha256:{fingerprint}"))
            };
            if !valid {
                return Err(failure(format!(
                    "scene.{field}_ref: 고정 commit 또는 해당 내용의 SHA-256이 필요합니다."
                )));
            }
        }
        if origin == "source"
            && state != "committed"
            && !["before_ref", "after_ref"]
                .iter()
                .any(|field| result[*field].as_str().unwrap().starts_with("sha256:"))
        {
            return Err(failure(
                "scene: 미커밋 변경에는 작업 트리 또는 index 내용의 SHA-256이 필요합니다.",
            ));
        }
        if result["before"] == result["after"] {
            return Err(failure(
                "scene: 변경 전후 내용이 같아 diff를 만들 수 없습니다.",
            ));
        }
        result["code"] = unified_diff(
            result["before"].as_str().unwrap(),
            result["after"].as_str().unwrap(),
            result["path"].as_str().unwrap(),
        )
        .into();
    }
    result["code_sha256"] = hash(result["code"].as_str().unwrap()).into();
    Ok(result)
}
fn references(value: &Value, field: &str, sources: &[Value]) -> Result<Vec<String>> {
    let refs = list(value, field, 1, 12)?
        .iter()
        .map(|value| key(value, field))
        .collect::<Result<Vec<_>>>()?;
    if refs.iter().collect::<BTreeSet<_>>().len() != refs.len()
        || refs
            .iter()
            .any(|id| !sources.iter().any(|source| source["id"] == *id))
        || !refs.iter().any(|id| {
            sources
                .iter()
                .any(|source| source["id"] == *id && source["kind"] == "official")
        })
    {
        return Err(failure(format!(
            "{field}: 수업 안의 공식 근거를 연결해 주세요."
        )));
    }
    Ok(refs)
}
fn article(raw: &Value, scene: &Value, sources: &[Value]) -> Result<Value> {
    object(
        raw,
        &["intro", "code_range", "sections", "takeaway", "source_ids"],
        &[],
        "article",
    )?;
    let refs = references(&raw["source_ids"], "article.source_ids", sources)?;
    if !refs.iter().any(|id| scene["source_id"] == *id) {
        return Err(failure(
            "article.source_ids: 글의 실제 작업 근거를 연결해 주세요.",
        ));
    }
    let range = list(&raw["code_range"], "article.code_range", 2, 2)?;
    let bounds = range[0]
        .as_u64()
        .zip(range[1].as_u64())
        .filter(|(start, end)| {
            *start >= 1
                && start <= end
                && *end <= splitlines(scene["code"].as_str().unwrap()).len() as u64
                && end - start < 24
        });
    if bounds.is_none() {
        return Err(failure(
            "article.code_range: 원본 안에서 최대 24줄의 연속 구간을 선택해 주세요.",
        ));
    }
    let mut sections = Vec::new();
    let mut ids = BTreeSet::new();
    for section in list(&raw["sections"], "article.sections", 2, 5)? {
        object(
            section,
            &["id", "title", "body", "source_ids"],
            &[],
            "article.section",
        )?;
        let id = key(&section["id"], "article.section.id")?;
        if !ids.insert(id.clone()) {
            return Err(failure(
                "article.section.id: 글 안에서 고유한 식별자가 필요합니다.",
            ));
        }
        let section_refs = references(
            &section["source_ids"],
            "article.section.source_ids",
            sources,
        )?;
        if section_refs.iter().any(|id| !refs.contains(id)) {
            return Err(failure(
                "article.section.source_ids: 글의 전체 출처 목록에도 근거를 포함해 주세요.",
            ));
        }
        sections.push(json!({"id":id,"title":text(&section["title"],"article.section.title",160,false)?,"body":text(&section["body"],"article.section.body",6000,false)?,"source_ids":section_refs}));
    }
    Ok(
        json!({"intro":text(&raw["intro"],"article.intro",1600,false)?,"code_range":range,"sections":sections,"takeaway":text(&raw["takeaway"],"article.takeaway",800,false)?,"source_ids":refs}),
    )
}

pub fn validate_packet(raw: &Value, current_day: NaiveDate) -> Result<Vec<Value>> {
    object(raw, &["version", "lessons"], &[], "packet")?;
    let version = raw["version"]
        .as_u64()
        .filter(|value| matches!(value, 1 | 2))
        .ok_or_else(|| failure("packet.version: 지원하는 판본은 1과 2입니다."))?;
    let v2 = version == 2;
    let mut lessons = Vec::new();
    let mut keys = BTreeSet::new();
    for item in list(&raw["lessons"], "lessons", 1, 30)? {
        let mut required = vec![
            "key",
            "title",
            "topic",
            "why",
            "explanation",
            "version_status",
            "applicability",
            "sources",
            "questions",
        ];
        if v2 {
            required.extend(["scene", "selection", "authorship"]);
        }
        object(
            item,
            &required,
            if v2 {
                &["reviewed_by", "article"]
            } else {
                &["reviewed_by"]
            },
            "lesson",
        )?;
        let lesson_key = key(&item["key"], "lesson.key")?;
        if !keys.insert(lesson_key.clone()) {
            return Err(failure(
                "lesson.key: 한 패킷에 같은 식별자가 중복되었습니다.",
            ));
        }
        let mut lesson = json!({"key":lesson_key,"reviewed_by":choice(item.get("reviewed_by").unwrap_or(&json!("unspecified")),REVIEWER_ROLES,"reviewed_by")?});
        for (field, limit) in [
            ("title", 240),
            ("topic", 120),
            ("why", 2000),
            ("explanation", 12000),
            ("applicability", 2000),
        ] {
            lesson[field] = text(&item[field], &format!("lesson.{field}"), limit, false)?.into();
        }
        lesson["version_status"] =
            choice(&item["version_status"], VERSION_STATUSES, "version_status")?.into();
        let sources = list(&item["sources"], "sources", 2, 12)?
            .iter()
            .map(|raw| source(raw, current_day, v2))
            .collect::<Result<Vec<_>>>()?;
        let source_ids: BTreeSet<_> = sources
            .iter()
            .map(|source| source["id"].as_str().unwrap())
            .collect();
        if source_ids.len() != sources.len()
            || !sources.iter().any(|source| source["kind"] == "work")
            || !sources.iter().any(|source| source["kind"] == "official")
        {
            return Err(failure(
                "sources: 고유한 식별자와 업무·공식 자료가 모두 필요합니다.",
            ));
        }
        if lesson["version_status"] == "matched"
            && sources.iter().any(|source| {
                source["kind"] == "official"
                    && lowercase(source["version"].as_str().unwrap()) == "unknown"
            })
        {
            return Err(failure(
                "version_status: 적용 버전을 모르면 unverified로 기록해 주세요.",
            ));
        }
        lesson["sources"] = json!(sources);
        if v2 {
            lesson["packet_version"] = json!(2);
            lesson["scene"] = scene(&item["scene"], &sources, current_day)?;
            if let Some(raw) = item.get("article") {
                lesson["article"] = article(raw, &lesson["scene"], &sources)?;
            }
            let selection = &item["selection"];
            object(selection, &["signal", "reason"], &[], "selection")?;
            lesson["selection"] = json!({"signal":choice(&selection["signal"],&SELECTION_SIGNALS,"selection.signal")?,"reason":text(&selection["reason"],"selection.reason",2000,false)?});
            let authored = &item["authorship"];
            object(
                authored,
                &["author", "method", "reviewer", "authored_on"],
                &[],
                "authorship",
            )?;
            lesson["authorship"] = json!({"author":choice(&authored["author"],&["owner","assistant"],"authorship.author")?,"method":choice(&authored["method"],&["manual"],"authorship.method")?,
                "reviewer":choice(&authored["reviewer"],&["owner","assistant"],"authorship.reviewer")?,"authored_on":day(&authored["authored_on"],"authorship.authored_on",current_day)?});
            if lesson["authorship"]["reviewer"] != lesson["reviewed_by"] {
                return Err(failure(
                    "authorship.reviewer: 수업의 검토 주체와 일치해야 합니다.",
                ));
            }
        }
        let mut questions = Vec::new();
        let mut question_ids = BTreeSet::new();
        for question in list(&item["questions"], "questions", 1, 12)? {
            let mut required = vec!["id", "kind", "prompt", "hint", "answer", "source_ids"];
            if v2 {
                required.extend(["concept_id", "depth", "focus_lines", "rationale", "rubric"]);
            }
            object(question, &required, &[], "question")?;
            let id = key(&question["id"], "question.id")?;
            if !question_ids.insert(id.clone()) {
                return Err(failure(
                    "question.id: 한 수업 안에 중복된 식별자가 있습니다.",
                ));
            }
            let mut q =
                json!({"id":id,"kind":choice(&question["kind"],QUESTION_KINDS,"question.kind")?});
            for field in ["prompt", "hint", "answer"] {
                q[field] =
                    text(&question[field], &format!("question.{field}"), 8000, false)?.into();
            }
            q["source_ids"] = json!(references(
                &question["source_ids"],
                "question.source_ids",
                &sources
            )?);
            if v2 {
                q["concept_id"] = key(&question["concept_id"], "question.concept_id")?.into();
                q["depth"] = choice(&question["depth"], &QUESTION_DEPTHS, "question.depth")?.into();
                q["rationale"] =
                    text(&question["rationale"], "question.rationale", 2000, false)?.into();
                let lines = list(&question["focus_lines"], "question.focus_lines", 1, 24)?;
                let count = splitlines(lesson["scene"]["code"].as_str().unwrap()).len() as u64;
                if lines
                    .iter()
                    .any(|line| line.as_u64().is_none_or(|line| line < 1 || line > count))
                {
                    return Err(failure(
                        "question.focus_lines: 보존된 코드의 발췌 줄 번호가 필요합니다.",
                    ));
                }
                if lines
                    .iter()
                    .map(|line| line.as_u64().unwrap())
                    .collect::<BTreeSet<_>>()
                    .len()
                    != lines.len()
                {
                    return Err(failure("question.focus_lines: 중복된 줄 번호가 있습니다."));
                }
                q["focus_lines"] = json!(lines);
                q["rubric"] = json!(list(&question["rubric"], "question.rubric", 1, 8)?
                    .iter()
                    .map(|value| text(value, "question.rubric", 2000, false))
                    .collect::<Result<Vec<_>>>()?);
                if !q["source_ids"]
                    .as_array()
                    .unwrap()
                    .contains(&lesson["scene"]["source_id"])
                {
                    return Err(failure(
                        "question.source_ids: 질문에서 실제 코드·명령의 업무 근거를 연결해 주세요.",
                    ));
                }
            }
            questions.push(q);
        }
        if v2
            && questions
                .iter()
                .map(|q| q["concept_id"].as_str().unwrap())
                .collect::<BTreeSet<_>>()
                != questions
                    .iter()
                    .filter(|q| q["depth"] == "understand")
                    .map(|q| q["concept_id"].as_str().unwrap())
                    .collect()
        {
            return Err(failure(
                "questions: 각 개념에 역할·흐름을 이해하는 질문이 필요합니다.",
            ));
        }
        lesson["questions"] = json!(questions);
        lessons.push(lesson);
    }
    Ok(lessons)
}
