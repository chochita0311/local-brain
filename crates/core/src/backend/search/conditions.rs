use super::pattern;
use crate::backend::{clock, Result};
use chrono::{DateTime, Datelike, Duration, NaiveDate, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
#[derive(Default, Debug, Clone, Serialize, Deserialize)]
pub struct Conditions {
    pub kind: String,
    pub start: String,
    pub end: String,
    pub exclude: Vec<String>,
    pub labels: Vec<String>,
    pub notices: Vec<String>,
}
impl Conditions {
    pub fn matches(&self, metadata: &Value) -> bool {
        if !self.kind.is_empty() && metadata["kind"] != self.kind {
            return false;
        }
        if !self.start.is_empty() {
            let Some(stamp) = metadata["timestamp"]
                .as_str()
                .and_then(clock::parse_timestamp)
            else {
                return false;
            };
            let (Some(start), Some(end)) = (
                clock::parse_timestamp(&self.start),
                clock::parse_timestamp(&self.end),
            ) else {
                return false;
            };
            if stamp < start || stamp >= end {
                return false;
            }
        }
        true
    }
}
fn is_match(pattern_: &str, value: &str) -> bool {
    pattern(pattern_).is_match(value).unwrap_or(false)
}
fn local_iso(stamp: DateTime<Utc>, timezone: &str) -> Result<String> {
    let zone = jiff::tz::TimeZone::get(timezone).map_err(|_| super::failure("INVALID_TIMEZONE"))?;
    let timestamp = jiff::Timestamp::from_microsecond(stamp.timestamp_micros())
        .map_err(|_| super::failure("INVALID_SEARCH_DATE"))?;
    let offset = timestamp.to_zoned(zone).offset().seconds();
    let fixed =
        chrono::FixedOffset::east_opt(offset).ok_or_else(|| super::failure("INVALID_TIMEZONE"))?;
    Ok(stamp
        .with_timezone(&fixed)
        .to_rfc3339_opts(chrono::SecondsFormat::AutoSi, false))
}
pub fn interpret(query: &str, timezone: &str, now: Option<DateTime<Utc>>) -> Result<Conditions> {
    let mut result = Conditions::default();
    let literal = pattern(r#"[“"「]([^”"」]+)[”"」](?:\s*문구)?(?:는|은|를|을)?\s*(?:제외|빼고)"#);
    let remaining = literal.replace_all(query, "");
    let remaining = pattern(r#"[“"「'].*?[”"」']"#)
        .replace_all(&remaining, " ")
        .into_owned();
    let mut kinds = Vec::new();
    for (name, kind) in [("세션", "session"), ("문서", "document")] {
        if is_match(
            &format!(r"{name}(?:만\b|(?:을|를)?(?:\s*(?:보여|찾아|검색|알려)|\s*$))"),
            &remaining,
        ) {
            kinds.push(kind);
        }
    }
    let ambiguous = is_match(r"말고|아니[고라]|제외|빼고", &remaining);
    let negation = is_match(
        r"(?:세션|문서)(?:만|은|는|을|를)?\s*(?:말고|아니|제외|빼고)",
        &remaining,
    );
    if kinds.len() == 1 && !negation {
        result.kind = kinds[0].into();
        result.labels.push(
            if result.kind == "session" {
                "세션"
            } else {
                "Local Context 문서"
            }
            .into(),
        );
    }
    let periods_pattern =
        pattern(r"(?<![가-힣A-Za-z0-9_])(?:오늘|어제|이번\s*주|지난\s*주|이번\s*달|지난\s*달)");
    let mut periods = Vec::new();
    let mut uncertain = false;
    for found in periods_pattern.find_iter(&remaining) {
        let found = found.map_err(|_| super::failure("INVALID_SEARCH_QUERY"))?;
        periods.push(
            found
                .as_str()
                .chars()
                .filter(|ch| !crate::backend::unicode::python_space(*ch))
                .collect::<String>(),
        );
        let tail = &remaining[found.end()..];
        if !is_match(r"^(?:$|[\s,.!?]|(?:에|의|만|동안)(?:\s|$))", tail)
            || is_match(r"^\s*(?:이후|이전|부터|까지|쯤|정도|전후|말)", tail)
            || is_match(
                r"^(?:은|는|을|를)?\s*(?:(?:자료|작업|세션|문서)(?:은|는|을|를)?\s*)?(?:말고|아니|제외|빼고)",
                tail,
            )
        {
            uncertain = true;
        }
    }
    if !periods.is_empty() && periods.iter().all(|period| period == &periods[0]) && !uncertain {
        let today = clock::local_day(now.unwrap_or_else(Utc::now), timezone)?;
        let (start, end) = match periods[0].as_str() {
            "오늘" => (today, today + Duration::days(1)),
            "어제" => (today - Duration::days(1), today),
            "이번주" | "지난주" => {
                let monday = today - Duration::days(today.weekday().num_days_from_monday() as i64);
                let start = if periods[0] == "지난주" {
                    monday - Duration::days(7)
                } else {
                    monday
                };
                (start, start + Duration::days(7))
            }
            _ => {
                let first = NaiveDate::from_ymd_opt(today.year(), today.month(), 1).unwrap();
                if periods[0] == "지난달" {
                    let last = first - Duration::days(1);
                    (
                        NaiveDate::from_ymd_opt(last.year(), last.month(), 1).unwrap(),
                        first,
                    )
                } else {
                    let next = (first + Duration::days(31)).with_day(1).unwrap();
                    (first, next)
                }
            }
        };
        result.start = local_iso(clock::calendar_day_bounds(start, timezone)?.0, timezone)?;
        result.end = local_iso(clock::calendar_day_bounds(end, timezone)?.0, timezone)?;
        result.labels.push(format!(
            "{start} ≤ 날짜 < {end} ({timezone}, 세션 마지막 활동·문서 수정일)"
        ));
    } else if !periods.is_empty() {
        result
            .notices
            .push("기간 해석이 모호해 날짜 범위를 제한하지 않았습니다.".into());
    }
    for captures in literal.captures_iter(query) {
        let captures = captures.map_err(|_| super::failure("INVALID_SEARCH_QUERY"))?;
        let value = captures.get(1).unwrap().as_str().to_string();
        result.labels.push(format!("원문 문구 “{value}” 제외"));
        result.exclude.push(value);
    }
    if ambiguous {
        result.notices.push("제외 조건의 의미가 모호해 후보를 넓게 유지했습니다. 문구를 명확히 제외하려면 따옴표로 지정해 주세요.".into());
    }
    if kinds.len() > 1 || negation {
        result
            .notices
            .push("자료 종류를 하나로 제한하지 않았습니다.".into());
    }
    Ok(result)
}
pub fn focus_query(query: &str) -> String {
    let text = query.trim_matches(crate::backend::unicode::python_space);
    if is_match(
        r#"(?i)["'“”「」]|말고|아니|제외|빼고|않|없는|없이|못|\b(?:not|without|except|excluding)\b"#,
        text,
    ) {
        return text.into();
    }
    let mut value=pattern(r"^(?:(?:내가|제가|우리가|저희가)\s+)?(?:(?:최근에|예전에|이전에|전에)\s+)?(?:(?:작업하던|진행하던|검토하던)\s+)?").replace(text,"").into_owned();
    for rule in [
        r"\s*(?:찾아(?:줘|주세요|줄래요?|봐)|보여(?:줘|주세요|줄래요?)|검색해(?:줘|주세요)|알려(?:줘|주세요))[.!?~\s]*$",
        r"\s+(?:세션|문서|자료|기록|내용)(?:들)?(?:만|을|를)?$",
        r"\s*(?:(?:과|와|에)\s+)?(?:관련(?:된|한)?|관한)$",
        r"(?i)^(?:find|show|search for)\s+(?:(?:me|my)\s+)?(?:(?:work|sessions?|documents?|records?)\s+(?:about|on|related to)\s+)?",
    ] {
        value = pattern(rule).replace(&value, "").into_owned();
    }
    let value = value.trim_matches(crate::backend::unicode::python_space);
    if value.is_empty() {
        text.into()
    } else {
        value.into()
    }
}
