//! Usage read models retain frozen snapshot amounts and first-observation attribution.
use super::decimal::Decimal;
use crate::backend::{
    clock, db, search::urlencode, sources::profiles::canonical_source_id, unicode, BackendError,
    Result,
};
use chrono::{DateTime, Datelike, Duration, NaiveDate, NaiveDateTime, Timelike, Utc};
use jiff::tz::TimeZone;
use rusqlite::{params_from_iter, Connection};
use rust_decimal::RoundingStrategy;
use serde_json::{json, Map, Number, Value};
use std::{
    borrow::Cow,
    collections::{BTreeMap, BTreeSet, HashMap},
    str::FromStr,
};

pub const PROJECTION_FORMULA_VERSION: &str = "calendar-elapsed-v1";
const ZERO_SNAPSHOT: &str = "(sources.provider_kind='codex' AND usage_records.total_semantics LIKE 'last_token_usage;%' AND usage_records.input_tokens=0 AND usage_records.output_tokens=0 AND usage_records.cache_write_tokens IS NULL AND usage_records.cache_read_tokens=0 AND usage_records.reasoning_tokens=0 AND usage_records.total_tokens=0 AND usage_records.source_total_tokens>0)";

#[derive(Debug, Clone)]
pub struct UsageOptions {
    pub view: String,
    pub source: String,
    pub metric: String,
    pub breakdown: String,
    pub from_value: Option<String>,
    pub to_value: Option<String>,
    pub timezone_name: String,
    pub today: Option<NaiveDate>,
    pub now: Option<DateTime<Utc>>,
    pub visible_only: bool,
}
impl Default for UsageOptions {
    fn default() -> Self {
        Self {
            view: "daily".into(),
            source: "all".into(),
            metric: "cost".into(),
            breakdown: "source".into(),
            from_value: None,
            to_value: None,
            timezone_name: "UTC".into(),
            today: None,
            now: None,
            visible_only: false,
        }
    }
}
#[derive(Debug, Clone)]
pub struct UsageScope {
    pub view: String,
    pub source: String,
    pub source_label: String,
    pub source_options: Vec<Value>,
    pub metric: String,
    pub breakdown: String,
    pub from_date: NaiveDate,
    pub to_date: NaiveDate,
    pub input_from: String,
    pub input_to: String,
    pub custom: bool,
    pub validation_message: Option<String>,
    pub timezone: String,
    pub start_utc: DateTime<Utc>,
    pub end_utc: DateTime<Utc>,
}
impl UsageScope {
    pub fn as_json(&self) -> Value {
        json!({"view":self.view,"source":self.source,"source_label":self.source_label,"source_options":self.source_options,"metric":self.metric,"breakdown":self.breakdown,"from_date":self.from_date.to_string(),"to_date":self.to_date.to_string(),"from_iso":self.from_date.to_string(),"to_iso":self.to_date.to_string(),"input_from":self.input_from,"input_to":self.input_to,"custom":self.custom,"validation_message":self.validation_message,"timezone":self.timezone,"start_utc":clock::isoformat(self.start_utc),"end_utc":clock::isoformat(self.end_utc),"period_label":format!("{} – {} · {}",self.from_date,self.to_date,self.timezone)})
    }
}
fn amount_error() -> BackendError {
    BackendError::invalid("usage", "Usage amount exceeds supported decimal range")
}
fn dec(text: &str) -> Result<Decimal> {
    Decimal::from_str(text).map_err(|_| amount_error())
}
fn add(a: Decimal, b: Decimal) -> Result<Decimal> {
    a.checked_add(b).ok_or_else(amount_error)
}
fn div(a: Decimal, b: Decimal) -> Result<Decimal> {
    a.checked_div(b).ok_or_else(amount_error)
}
fn mul(a: Decimal, b: Decimal) -> Result<Decimal> {
    a.checked_mul(b).ok_or_else(amount_error)
}
fn dj(value: Decimal) -> Value {
    Value::Number(Number::from_str(&value.to_string()).expect("finite Decimal is a JSON number"))
}
fn optional_decimal(value: Option<Decimal>) -> Value {
    value.map(dj).unwrap_or(Value::Null)
}
fn ij(value: i128) -> Value {
    Value::Number(Number::from_str(&value.to_string()).expect("integer is a JSON number"))
}
fn text<'a>(row: &'a Value, key: &str) -> Option<&'a str> {
    row[key].as_str()
}
fn nonempty<'a>(row: &'a Value, key: &str) -> Option<&'a str> {
    text(row, key).filter(|v| !v.is_empty())
}
fn key(value: &Value) -> String {
    key_text(value).into_owned()
}
fn key_text(value: &Value) -> Cow<'_, str> {
    match value {
        Value::String(value) => Cow::Borrowed(value),
        Value::Number(value) => Cow::Borrowed(value.as_str()),
        _ => Cow::Owned(value.to_string()),
    }
}
fn insert_key(values: &mut BTreeSet<String>, value: &Value) {
    let key = key_text(value);
    if !values.contains(key.as_ref()) {
        values.insert(key.into_owned());
    }
}
fn number(row: &Value, key: &str) -> Result<Option<i128>> {
    match &row[key] {
        Value::Null => Ok(None),
        Value::Number(number) => number
            .as_str()
            .parse()
            .map(Some)
            .map_err(|_| amount_error()),
        _ => Err(amount_error()),
    }
}
fn cost(row: &Value) -> Result<Option<Decimal>> {
    if row["calculation_state"] == "priced" && !row["estimated_cost_usd"].is_null() {
        dec(&key_text(&row["estimated_cost_usd"])).map(Some)
    } else {
        Ok(None)
    }
}
fn local_time(at: DateTime<Utc>, zone: &str) -> Result<NaiveDateTime> {
    let zone = jiff::tz::TimeZone::get(zone)
        .map_err(|e| BackendError::invalid("timezone", e.to_string()))?;
    let timestamp = jiff::Timestamp::from_microsecond(at.timestamp_micros())
        .map_err(|e| BackendError::invalid("timestamp", e.to_string()))?;
    let civil = timestamp.to_zoned(zone).datetime();
    NaiveDate::from_ymd_opt(
        civil.year() as i32,
        civil.month() as u32,
        civil.day() as u32,
    )
    .and_then(|date| {
        date.and_hms_micro_opt(
            civil.hour() as u32,
            civil.minute() as u32,
            civil.second() as u32,
            civil.subsec_nanosecond() as u32 / 1000,
        )
    })
    .ok_or_else(|| BackendError::invalid("timestamp", "Date outside supported calendar"))
}
fn local_instant(local: NaiveDateTime, zone: &str) -> Result<DateTime<Utc>> {
    let zone = jiff::tz::TimeZone::get(zone)
        .map_err(|e| BackendError::invalid("timezone", e.to_string()))?;
    let civil = jiff::civil::date(local.year() as i16, local.month() as i8, local.day() as i8).at(
        local.hour() as i8,
        local.minute() as i8,
        local.second() as i8,
        local.nanosecond() as i32,
    );
    let instant = civil
        .to_zoned(zone)
        .map_err(|e| BackendError::invalid("timestamp", e.to_string()))?
        .timestamp();
    DateTime::from_timestamp(instant.as_second(), instant.subsec_nanosecond() as u32)
        .ok_or_else(|| BackendError::invalid("timestamp", "Date outside supported calendar"))
}
fn eligible(source: &str) -> (String, Vec<String>) {
    let mut params = vec!["<synthetic>".into()];
    let filter = if source != "all" {
        params.push(source.into());
        "AND sources.id=?"
    } else {
        ""
    };
    (format!("sources.provider_kind IN ('claude','codex') AND NOT (sources.provider_kind='claude' AND COALESCE(usage_records.raw_model,'')=?) AND NOT {ZERO_SNAPSHOT} {filter}"),params)
}
fn earliest_date(connection: &Connection, source: &str, zone: &str) -> Result<Option<NaiveDate>> {
    let (condition, params) = eligible(source);
    let mut earliest: Option<DateTime<Utc>> = None;
    db::scan(connection,&format!("SELECT usage_records.occurred_at FROM usage_records JOIN sources ON sources.id=usage_records.source_id WHERE usage_records.occurred_at IS NOT NULL AND {condition} ORDER BY usage_records.occurred_at"),params_from_iter(params),|row|{
        let raw=text(&row,"occurred_at").unwrap_or_default();
        if let Some(at)=earliest { if raw.get(..10).and_then(clock::parse_date).is_some_and(|day|day>at.date_naive()+Duration::days(1)){return Ok(false);} }
        if let Some(at)=clock::parse_timestamp(raw){earliest=Some(earliest.map_or(at,|previous|previous.min(at)));}Ok(true)
    })?;
    earliest.map(|at| clock::local_day(at, zone)).transpose()
}
pub fn normalize_usage_scope(
    connection: &Connection,
    options: &UsageOptions,
) -> Result<UsageScope> {
    let view = if ["daily", "weekly", "monthly", "cumulative"].contains(&options.view.as_str()) {
        options.view.as_str()
    } else {
        "daily"
    };
    let source_options=db::rows(connection,"SELECT id,provider_kind,name FROM sources WHERE provider_kind IN ('claude','codex') ORDER BY profile_position,id",[])?.into_iter().map(|row|json!({"value":key(&row["id"]),"label":row["name"],"provider_kind":row["provider_kind"]})).collect::<Vec<_>>();
    let canonical = canonical_source_id(&options.source);
    let selected = source_options.iter().find(|row| row["value"] == canonical);
    let source = selected.map(|_| canonical).unwrap_or_else(|| "all".into());
    let source_label = selected
        .and_then(|row| row["label"].as_str())
        .unwrap_or("All")
        .to_owned();
    let metric = if ["tokens", "cost"].contains(&options.metric.as_str()) {
        options.metric.as_str()
    } else {
        "cost"
    };
    let breakdown = if ["source", "model", "project"].contains(&options.breakdown.as_str()) {
        options.breakdown.as_str()
    } else {
        "source"
    };
    let current_day = options.today.map(Ok).unwrap_or_else(|| {
        clock::local_day(options.now.unwrap_or_else(Utc::now), &options.timezone_name)
    })?;
    let parsed = options
        .from_value
        .as_deref()
        .and_then(clock::parse_date)
        .zip(options.to_value.as_deref().and_then(clock::parse_date))
        .filter(|(from, to)| from <= to);
    let custom = parsed.is_some();
    let validation_message=(!custom && (options.from_value.as_ref().is_some_and(|v|!v.is_empty())||options.to_value.as_ref().is_some_and(|v|!v.is_empty()))).then(||"Custom dates require a valid inclusive From and To pair. The selected view's default range is shown instead.".into());
    let (from_date, to_date) = if let Some(pair) = parsed {
        pair
    } else {
        let start = match view {
            "daily" => current_day - Duration::days(29),
            "weekly" => {
                current_day
                    - Duration::days(i64::from(current_day.weekday().num_days_from_monday()) + 77)
            }
            _ => earliest_date(connection, &source, &options.timezone_name)?.unwrap_or(current_day),
        };
        (start, current_day)
    };
    let start_utc = clock::calendar_day_bounds(from_date, &options.timezone_name)?.0;
    let end_utc = clock::calendar_day_bounds(to_date, &options.timezone_name)?.1;
    Ok(UsageScope {
        view: view.into(),
        source,
        source_label,
        source_options,
        metric: metric.into(),
        breakdown: breakdown.into(),
        from_date,
        to_date,
        input_from: options.from_value.clone().unwrap_or_default(),
        input_to: options.to_value.clone().unwrap_or_default(),
        custom,
        validation_message,
        timezone: options.timezone_name.clone(),
        start_utc,
        end_utc,
    })
}

fn comma(value: &str) -> String {
    let (whole, fraction) = value
        .split_once('.')
        .map_or((value, None), |(a, b)| (a, Some(b)));
    let (sign, digits) = whole.strip_prefix('-').map_or(("", whole), |v| ("-", v));
    let mut result = String::from(sign);
    for (index, ch) in digits.chars().enumerate() {
        if index > 0 && (digits.len() - index) % 3 == 0 {
            result.push(',');
        }
        result.push(ch);
    }
    if let Some(fraction) = fraction {
        result.push('.');
        result.push_str(fraction);
    }
    result
}
fn fixed(value: Decimal, digits: u32) -> String {
    format!(
        "{:.*}",
        digits as usize,
        value.round_dp_with_strategy(digits, RoundingStrategy::MidpointNearestEven)
    )
}
fn format_tokens(value: Option<i128>) -> Result<String> {
    let Some(value) = value else {
        return Ok("Unavailable".into());
    };
    for (divisor, suffix) in [(1_000_000_000i128, "B"), (1_000_000, "M"), (1000, "K")] {
        if value.unsigned_abs() >= divisor as u128 {
            let scaled = div(dec(&value.to_string())?, dec(&divisor.to_string())?)?;
            let digits = if scaled < Decimal::ten() { 2 } else { 1 };
            return Ok(format!(
                "{}{suffix}",
                fixed(scaled, digits)
                    .trim_end_matches('0')
                    .trim_end_matches('.')
            ));
        }
    }
    Ok(comma(&value.to_string()))
}
pub(crate) fn format_cost(value: Option<Decimal>) -> String {
    value
        .map(|value| {
            format!(
                "${}",
                comma(&fixed(
                    value.clone(),
                    if value < Decimal::new(1, 2) { 4 } else { 2 }
                ))
            )
        })
        .unwrap_or_else(|| "Unavailable".into())
}
fn format_bar(value: Decimal, metric: &str) -> Result<String> {
    let prefix = if metric == "cost" { "$" } else { "" };
    if metric == "cost" && value > Decimal::zero() && value < Decimal::one() {
        return Ok("<$1".into());
    }
    let units = [
        (1_000_000_000_000i64, "T"),
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1000, "K"),
    ];
    for (index, (divisor, suffix)) in units.iter().enumerate() {
        if value >= Decimal::from(*divisor) {
            let rounded = div(value, Decimal::from(*divisor))?
                .round_dp_with_strategy(0, RoundingStrategy::MidpointAwayFromZero);
            if rounded >= Decimal::from(1000) && index > 0 {
                return Ok(format!("{prefix}1{}", units[index - 1].1));
            }
            return Ok(format!("{prefix}{}{suffix}", comma(&fixed(rounded, 0))));
        }
    }
    let rounded = value.round_dp_with_strategy(0, RoundingStrategy::MidpointAwayFromZero);
    Ok(if rounded >= Decimal::from(1000) {
        format!("{prefix}1K")
    } else {
        format!("{prefix}{}", comma(&fixed(rounded, 0)))
    })
}
fn record_count(value: u64, modifier: &str) -> String {
    format!(
        "{} {}usage record{}",
        comma(&value.to_string()),
        if modifier.is_empty() {
            String::new()
        } else {
            format!("{modifier} ")
        },
        if value == 1 { "" } else { "s" }
    )
}
fn format_duration(seconds: i64) -> String {
    let seconds = seconds.max(0);
    if seconds >= 3600 {
        format!("{}h {}m", seconds / 3600, seconds % 3600 / 60)
    } else {
        format!("{}m", seconds / 60)
    }
}

/// Open the ordinary indexed partition first, including its initial SQLite
/// step, before exceptional cursors. At most four rows are prefetched; all
/// partitions share the original read snapshot and remain disjoint.
fn scan_usage(
    connection: &Connection,
    scope: &UsageScope,
    visible: bool,
    mut visitor: impl FnMut(&mut Value) -> Result<()>,
) -> Result<()> {
    let (condition, params) = eligible(&scope.source);
    let columns = if visible {
        "usage_records.id,usage_records.occurred_at,usage_records.session_id,usage_records.source_id,usage_records.raw_model,usage_records.model_name,usage_records.total_tokens,usage_records.estimated_cost_usd,usage_records.calculation_state,usage_records.project_key,usage_records.project_name_snapshot,sources.provider_kind,sources.name AS source_name,sessions.session_class,sessions.session_role,NULL AS current_workspace_id"
    } else {
        "usage_records.*,sources.provider_kind,sources.name AS source_name,sessions.session_class,sessions.session_role,sessions.title AS session_title,usage_price_snapshots.label AS price_snapshot_label,current_workspace.id AS current_workspace_id,current_workspace.exists_now AS current_workspace_exists"
    };
    let joins = if visible {
        ""
    } else {
        "LEFT JOIN usage_price_snapshots ON usage_price_snapshots.id=usage_records.price_snapshot_id LEFT JOIN workspaces AS current_workspace ON current_workspace.id=usage_records.workspace_id_snapshot"
    };
    let mut windows: Vec<(String, Vec<String>)> = Vec::new();
    if visible {
        let lower = (scope.start_utc.date_naive() - Duration::days(1)).to_string();
        let upper = (scope.end_utc.date_naive() + Duration::days(2)).to_string();
        let unusual="(usage_records.occurred_at IS NULL OR strftime('%s',usage_records.occurred_at) IS NULL OR usage_records.occurred_at!=trim(usage_records.occurred_at) OR date(substr(usage_records.occurred_at,1,10),'+0 days')!=substr(usage_records.occurred_at,1,10))";
        windows.push((
            "usage_records.occurred_at>=? AND usage_records.occurred_at<?".into(),
            vec![lower.clone(), upper.clone()],
        ));
        windows.push(("usage_records.occurred_at IS NULL".into(), vec![]));
        windows.push((
            format!("usage_records.occurred_at<? AND {unusual}"),
            vec![lower],
        ));
        windows.push((
            format!("usage_records.occurred_at>=? AND {unusual}"),
            vec![upper],
        ));
    } else {
        windows.push(("1".into(), vec![]));
    }
    let mut statements=windows.iter().map(|(window,_)|connection.prepare(&format!("SELECT {columns} FROM usage_records JOIN sources ON sources.id=usage_records.source_id JOIN sessions ON sessions.id=usage_records.session_id {joins} WHERE {condition} AND ({window}) ORDER BY usage_records.occurred_at,usage_records.id"))).collect::<std::result::Result<Vec<_>,_>>()?;
    let decoder = db::RowDecoder::new(&statements[0]);
    let mut cursors = Vec::new();
    for (statement, (_, window_params)) in statements.iter_mut().zip(&windows) {
        let mut cursor = statement.query(params_from_iter(params.iter().chain(window_params)))?;
        let first = cursor.next()?.map(|row| decoder.decode(row)).transpose()?;
        cursors.push((cursor, first));
    }
    let order = if visible { vec![1, 2, 0, 3] } else { vec![0] };
    for index in order {
        let (cursor, first) = &mut cursors[index];
        let mut values = first.take().unwrap_or_default();
        if !values.is_null() {
            visitor(&mut values)?;
        }
        while let Some(row) = cursor.next()? {
            decoder.decode_into(row, &mut values)?;
            visitor(&mut values)?;
        }
    }
    Ok(())
}
fn has_usage(connection: &Connection, source: &str) -> Result<bool> {
    let (condition, params) = eligible(source);
    Ok(db::row(connection,&format!("SELECT 1 FROM usage_records JOIN sources ON sources.id=usage_records.source_id JOIN sessions ON sessions.id=usage_records.session_id WHERE {condition} LIMIT 1"),params_from_iter(params))?.is_some())
}

#[derive(Default)]
struct Aggregate {
    count: u64,
    tokens: i128,
    covered: u64,
    cost: Decimal,
    priced: u64,
    sessions: BTreeSet<String>,
    days: BTreeSet<NaiveDate>,
    states: Map<String, Value>,
    scopes: Map<String, Value>,
    capabilities: Map<String, Value>,
    attribution: Map<String, Value>,
}
fn increment(map: &mut Map<String, Value>, key: &str) {
    let n = map.get(key).and_then(Value::as_u64).unwrap_or(0) + 1;
    map.insert(key.into(), n.into());
}
impl Aggregate {
    fn add(
        &mut self,
        row: &Value,
        day: NaiveDate,
        details: bool,
    ) -> Result<(Option<i128>, Option<Decimal>)> {
        self.count += 1;
        let tokens = number(row, "total_tokens")?;
        if let Some(tokens) = tokens {
            self.tokens = self.tokens.checked_add(tokens).ok_or_else(amount_error)?;
            self.covered += 1;
        }
        let cost = cost(row)?;
        if let Some(value) = &cost {
            self.cost = add(self.cost.clone(), value.clone())?;
            self.priced += 1;
        }
        if row["session_class"] == "work" && row["session_role"] == "primary" {
            insert_key(&mut self.sessions, &row["session_id"]);
        }
        self.days.insert(day);
        if details {
            increment(
                &mut self.states,
                text(row, "calculation_state").unwrap_or_default(),
            );
            increment(
                &mut self.scopes,
                text(row, "aggregation_scope").unwrap_or_default(),
            );
            increment(
                &mut self.capabilities,
                text(row, "capability_state").unwrap_or_default(),
            );
            increment(
                &mut self.attribution,
                text(row, "attribution_basis").unwrap_or_default(),
            );
        }
        Ok((tokens, cost))
    }
    fn total_tokens(&self) -> Option<i128> {
        (self.covered > 0).then_some(self.tokens)
    }
    fn estimated_cost(&self) -> Option<Decimal> {
        (self.priced > 0).then(|| self.cost.clone())
    }
    fn as_json(&self) -> Value {
        json!({"usage_record_count":self.count,"total_tokens":self.total_tokens().map(ij),"token_covered_record_count":self.covered,"estimated_cost":optional_decimal(self.estimated_cost()),"priced_record_count":self.priced,"session_count":self.sessions.len(),"active_days":self.days.len(),"calculation_states":self.states,"aggregation_scopes":self.scopes,"capability_states":self.capabilities,"attribution_bases":self.attribution})
    }
}
fn bucket_start(day: NaiveDate, view: &str) -> NaiveDate {
    match view {
        "weekly" => day - Duration::days(i64::from(day.weekday().num_days_from_monday())),
        "monthly" | "cumulative" => day.with_day(1).unwrap(),
        _ => day,
    }
}
fn next_bucket(day: NaiveDate, view: &str) -> Result<NaiveDate> {
    match view {
        "weekly" => day.checked_add_signed(Duration::days(7)),
        "monthly" | "cumulative" => NaiveDate::from_ymd_opt(
            if day.month() == 12 {
                day.year() + 1
            } else {
                day.year()
            },
            if day.month() == 12 {
                1
            } else {
                day.month() + 1
            },
            1,
        ),
        _ => day.succ_opt(),
    }
    .ok_or_else(|| BackendError::invalid("usage", "Date outside supported calendar"))
}
fn history(buckets: &BTreeMap<NaiveDate, Decimal>, scope: &UsageScope) -> Result<Vec<Value>> {
    let mut current = bucket_start(scope.from_date, &scope.view);
    let mut last = bucket_start(scope.to_date, &scope.view);
    let positive = buckets
        .iter()
        .filter(|(_, v)| **v > Decimal::zero())
        .map(|(day, _)| *day)
        .collect::<Vec<_>>();
    if let (Some(first), Some(end)) = (positive.first(), positive.last()) {
        current = current.max(*first);
        last = last.min(*end);
    }
    let mut pairs = Vec::new();
    let mut running = Decimal::zero();
    while current <= last {
        let mut value = buckets.get(&current).cloned().unwrap_or_default();
        if scope.view == "cumulative" {
            running = add(running, value)?;
            value = running.clone();
        }
        pairs.push((current, value));
        if current == last {
            break;
        }
        current = next_bucket(current, &scope.view)?;
    }
    let maximum = pairs
        .iter()
        .map(|(_, v)| v.clone())
        .max()
        .unwrap_or_default();
    pairs.iter().enumerate().map(|(index,(day,value))|{
        let bar=if maximum==Decimal::zero()||*value==Decimal::zero(){0}else{mul(div(value.clone(),maximum.clone())?,Decimal::from(100))?.round_dp_with_strategy(0,RoundingStrategy::MidpointNearestEven).to_string().parse::<i64>().map_err(|_|amount_error())?.max(4)};
        let label=if matches!(scope.view.as_str(),"monthly"|"cumulative"){day.format("%Y-%m").to_string()}else{day.format("%m/%d").to_string()};
        let show=if scope.view=="daily"{index==0||index+1==pairs.len()||[1,15].contains(&day.day())}else{index%(pairs.len()/6).max(1)==0||index+1==pairs.len()};
        Ok(json!({"date":day.to_string(),"value":dj(value.clone()),"bar_percent":bar,"value_label":if scope.metric=="tokens"{format_tokens(Some(value.trunc().to_string().parse().map_err(|_|amount_error())?))?}else{format_cost(Some(value.clone()))},"bar_label":format_bar(value.clone(),&scope.metric)?,"label":label,"show_label":show}))
    }).collect()
}
struct Group {
    key: String,
    label: String,
    source_id: Value,
    provider: Value,
    tokens: i128,
    covered: u64,
    cost: Decimal,
    priced: u64,
    count: u64,
    raw_models: BTreeSet<String>,
    sessions: BTreeSet<String>,
    latest: DateTime<Utc>,
    workspace: Value,
}
#[derive(Default)]
struct Dashboard {
    aggregate: Aggregate,
    buckets: BTreeMap<NaiveDate, Decimal>,
    groups: Vec<Group>,
    group_indices: HashMap<String, usize>,
    compatible: Decimal,
    has_compatible: bool,
}
impl Dashboard {
    fn add(
        &mut self,
        row: &Value,
        at: DateTime<Utc>,
        zone: &TimeZone,
        scope: &UsageScope,
        details: bool,
    ) -> Result<()> {
        let day = clock::local_day_in_zone(at, zone)?;
        let (tokens, cost) = self.aggregate.add(row, day, details)?;
        let value = if scope.metric == "tokens" {
            tokens.map(|tokens| dec(&tokens.to_string())).transpose()?
        } else {
            cost.clone()
        };
        if let Some(value) = value.clone() {
            let day = bucket_start(day, &scope.view);
            let entry = self.buckets.entry(day).or_default();
            *entry = add(entry.clone(), value)?;
        }
        if scope.breakdown == "project" && row["session_class"] != "work" {
            return Ok(());
        }
        let (group_key, label) = match scope.breakdown.as_str() {
            "source" => (
                key_text(&row["source_id"]),
                text(row, "source_name").unwrap_or_default(),
            ),
            "model" => {
                let identity = nonempty(row, "model_name").or_else(|| nonempty(row, "raw_model"));
                (
                    Cow::Borrowed(identity.unwrap_or("unknown-model")),
                    identity.unwrap_or("Unknown model"),
                )
            }
            _ => {
                let project = nonempty(row, "project_key");
                (
                    Cow::Borrowed(project.unwrap_or("unassigned")),
                    if project.is_some() {
                        nonempty(row, "project_name_snapshot").unwrap_or("Attributed project")
                    } else {
                        "프로젝트 미지정"
                    },
                )
            }
        };
        let index = if let Some(&index) = self.group_indices.get(group_key.as_ref()) {
            index
        } else {
            let index = self.groups.len();
            self.group_indices.insert(group_key.to_string(), index);
            self.groups.push(Group {
                key: group_key.into_owned(),
                label: label.into(),
                source_id: if scope.breakdown == "source" {
                    row["source_id"].clone()
                } else {
                    Value::Null
                },
                provider: if scope.breakdown == "source" {
                    row["provider_kind"].clone()
                } else {
                    Value::Null
                },
                tokens: 0,
                covered: 0,
                cost: Decimal::zero(),
                priced: 0,
                count: 0,
                raw_models: BTreeSet::new(),
                sessions: BTreeSet::new(),
                latest: at,
                workspace: row["current_workspace_id"].clone(),
            });
            index
        };
        let group = &mut self.groups[index];
        group.count += 1;
        if let Some(tokens) = tokens {
            group.tokens = group.tokens.checked_add(tokens).ok_or_else(amount_error)?;
            group.covered += 1;
        }
        if let Some(cost) = cost {
            group.cost = add(group.cost.clone(), cost)?;
            group.priced += 1;
        }
        if let Some(value) = value {
            self.compatible = add(self.compatible.clone(), value)?;
            self.has_compatible = true;
        }
        if let Some(raw) = nonempty(row, "raw_model") {
            if !group.raw_models.contains(raw) {
                group.raw_models.insert(raw.into());
            }
        }
        if row["session_class"] == "work" && row["session_role"] == "primary" {
            insert_key(&mut group.sessions, &row["session_id"]);
        }
        group.latest = group.latest.max(at);
        Ok(())
    }
    fn breakdown(&self, scope: &UsageScope) -> Result<Value> {
        let mut items = Vec::new();
        for group in &self.groups {
            let tokens = (group.covered > 0).then_some(group.tokens);
            let cost = (group.priced > 0).then(|| group.cost.clone());
            let metric = if scope.metric == "tokens" {
                tokens.map(|v| dec(&v.to_string())).transpose()?
            } else {
                cost.clone()
            };
            let share = if self.has_compatible && self.compatible != Decimal::zero() {
                metric
                    .clone()
                    .map(|v| mul(div(v, self.compatible.clone())?, Decimal::from(100)))
                    .transpose()?
            } else {
                None
            };
            let evidence = if scope.breakdown == "source" {
                Some((
                    format!("/sessions?{}", urlencode(&[("source", group.key.clone())])),
                    "Browse source Sessions",
                ))
            } else if scope.breakdown == "project"
                && !group.workspace.is_null()
                && group.workspace != 0
            {
                Some((
                    format!(
                        "/sessions?{}",
                        urlencode(&[("workspace", key(&group.workspace))])
                    ),
                    "Browse current Project Sessions",
                ))
            } else if group.sessions.len() == 1 {
                Some((
                    format!("/sessions/{}", group.sessions.first().unwrap()),
                    "Open Session evidence",
                ))
            } else {
                None
            };
            let note = if evidence.is_some() {
                None
            } else if scope.breakdown == "model" {
                Some(if group.sessions.is_empty() {
                    "No primary work Session in this model group."
                } else {
                    "Usage spans multiple primary Sessions."
                })
            } else {
                Some("Aggregated usage has no exact current inventory filter.")
            };
            let item = json!({"key":group.key,"label":group.label,"source_id":group.source_id,"provider_kind":group.provider,"tokens":tokens.map(ij),"tokens_label":format_tokens(tokens)?,"estimated_cost":optional_decimal(cost.clone()),"cost_label":format_cost(cost),"session_count":group.sessions.len(),"usage_record_count":group.count,"token_covered_record_count":group.covered,"priced_record_count":group.priced,"share":optional_decimal(share.clone()),"share_label":share.map(|v|format!("{}%",fixed(v,1))).unwrap_or_else(||"Unavailable".into()),"last_activity_at":clock::isoformat(group.latest),"raw_models":group.raw_models,"metric_value":optional_decimal(metric.clone()),"evidence_url":evidence.as_ref().map(|v|&v.0),"evidence_label":evidence.map(|v|v.1),"evidence_note":note});
            items.push((metric, unicode::lowercase(&group.label), item));
        }
        items.sort_by(|a, b| {
            a.0.is_none()
                .cmp(&b.0.is_none())
                .then_with(|| b.0.as_ref().cmp(&a.0.as_ref()))
                .then_with(|| a.1.cmp(&b.1))
        });
        let items = items.into_iter().map(|(_, _, v)| v).collect::<Vec<_>>();
        let split = items.len().min(8);
        let (title, subtitle) = match scope.breakdown.as_str() {
            "source" => ("By source", "Source provenance"),
            "model" => ("By model", "Normalized model with raw identity"),
            _ => ("By Project", "First-observation Project snapshot"),
        };
        Ok(
            json!({"mode":scope.breakdown,"title":title,"subtitle":subtitle,"rows":items,"primary_rows":items[..split],"overflow_rows":items[split..],"compatible_total_label":if self.has_compatible{if scope.metric=="tokens"{format_tokens(Some(self.compatible.trunc().to_string().parse().map_err(|_|amount_error())?))?}else{format_cost(Some(self.compatible.clone()))}}else{"Unavailable".into()}}),
        )
    }
}

fn freshness(connection: &Connection, source: &str) -> Result<Value> {
    let filter = if source == "all" {
        ""
    } else {
        "AND sources.id=?"
    };
    let params = if source == "all" {
        vec![]
    } else {
        vec![source]
    };
    let rows=db::rows(connection,&format!("SELECT sources.id,sources.provider_kind,sources.name,sources.last_scanned_at AS last_attempt_at,sources.last_scan_success_at,sources.last_scan_status,sources.last_scan_error,MAX(CASE WHEN source_files.status='ok' THEN source_files.last_scanned_at END) AS last_healthy_file_at,SUM(CASE WHEN source_files.status='stale' THEN 1 ELSE 0 END) AS stale_count,SUM(CASE WHEN source_files.status='error' THEN 1 ELSE 0 END) AS error_count FROM sources LEFT JOIN source_files ON source_files.source_id=sources.id WHERE sources.provider_kind IN ('claude','codex') {filter} GROUP BY sources.id,sources.provider_kind,sources.name,sources.last_scanned_at,sources.last_scan_success_at,sources.last_scan_status,sources.last_scan_error ORDER BY sources.id"),params_from_iter(params))?;
    let mut sources = Vec::new();
    let mut errors = 0;
    let mut stale = 0;
    let mut successes = Vec::new();
    let mut attempts = Vec::new();
    let mut any_error = false;
    let mut any_stale = false;
    for row in rows {
        let error_count = row["error_count"].as_u64().unwrap_or(0);
        let stale_count = row["stale_count"].as_u64().unwrap_or(0);
        errors += error_count;
        stale += stale_count;
        let scan = text(&row, "last_scan_status").unwrap_or_default();
        let status = if ["unavailable", "configuration_error", "scan_failed"].contains(&scan)
            || error_count > 0
        {
            "error"
        } else if stale_count > 0 {
            "stale"
        } else if ["completed", "empty"].contains(&scan)
            || nonempty(&row, "last_attempt_at").is_some()
        {
            "current"
        } else {
            "not_synchronized"
        };
        any_error |= status == "error";
        any_stale |= status == "stale";
        let successful = nonempty(&row, "last_scan_success_at").or_else(|| {
            if status == "current" {
                nonempty(&row, "last_attempt_at")
            } else {
                nonempty(&row, "last_healthy_file_at")
            }
        });
        if let Some(value) = successful {
            successes.push(value.to_owned());
        }
        if let Some(value) = nonempty(&row, "last_attempt_at") {
            attempts.push(value.to_owned());
        }
        sources.push(json!({"id":row["id"],"provider_kind":row["provider_kind"],"name":row["name"],"status":status,"scan_status":row["last_scan_status"],"scan_error":row["last_scan_error"],"last_attempt_at":row["last_attempt_at"],"last_successful_at":successful,"stale_count":stale_count,"error_count":error_count}));
    }
    Ok(
        json!({"status":if any_error{"error"}else if any_stale{"stale"}else if !successes.is_empty(){"current"}else{"not_synchronized"},"last_synchronized_at":successes.into_iter().max(),"last_attempt_at":attempts.into_iter().max(),"stale_count":stale,"error_count":errors,"sources":sources}),
    )
}

pub fn current_month_projection(
    rows: &[(Value, DateTime<Utc>)],
    scope: &UsageScope,
    calculated_at: DateTime<Utc>,
    freshness: &Value,
) -> Result<Value> {
    let local = local_time(calculated_at, &scope.timezone)?;
    let day = local.date();
    let visible = scope.metric == "cost" && scope.from_date <= day && day <= scope.to_date;
    let mut base = json!({"visible":visible,"formula_version":PROJECTION_FORMULA_VERSION,"calculated_at":clock::isoformat(calculated_at),"source":scope.source,"month":day.format("%Y-%m").to_string(),"projected_cost":null,"value_label":"Unavailable","input_mtd_cost":null,"input_label":"Unavailable","elapsed_fraction":null,"complete_days":day.day()-1,"usage_record_count":0,"priced_record_count":0,"coverage_state":"unavailable","status":"not_applicable","reason":null});
    if !visible {
        return Ok(base);
    }
    let mut aggregate = Aggregate::default();
    let zone = TimeZone::get(&scope.timezone)
        .map_err(|error| BackendError::invalid("timezone", error.to_string()))?;
    for (row, at) in rows {
        aggregate.add(row, clock::local_day_in_zone(*at, &zone)?, true)?;
    }
    base["input_mtd_cost"] = optional_decimal(aggregate.estimated_cost());
    base["input_label"] = format_cost(aggregate.estimated_cost()).into();
    base["usage_record_count"] = aggregate.count.into();
    base["priced_record_count"] = aggregate.priced.into();
    let state = if day.day() < 4 {
        Some((
            "insufficient_history",
            "Available after three complete local-calendar days.",
        ))
    } else if aggregate.count == 0 {
        Some((
            "no_usage",
            "No current-month usage is available for this source scope.",
        ))
    } else if aggregate.priced == 0 {
        Some((
            "unavailable",
            "Current-month usage has no compatible snapshot-priced cost.",
        ))
    } else {
        None
    };
    if let Some((status, reason)) = state {
        base["status"] = status.into();
        base["reason"] = reason.into();
        return Ok(base);
    }
    // Same-ZoneInfo subtraction in the original contract uses wall-calendar
    // time, so a DST transition does not change this month-length denominator.
    let start = day.with_day(1).unwrap().and_hms_opt(0, 0, 0).unwrap();
    let end = next_bucket(day.with_day(1).unwrap(), "monthly")?
        .and_hms_opt(0, 0, 0)
        .unwrap();
    let calculate = || -> Result<(Decimal, Decimal)> {
        let elapsed = Decimal::from(
            (local - start)
                .num_microseconds()
                .ok_or_else(amount_error)?,
        );
        let full = Decimal::from((end - start).num_microseconds().ok_or_else(amount_error)?);
        if elapsed <= Decimal::zero() || full <= Decimal::zero() {
            return Err(amount_error());
        }
        let fraction = div(elapsed, full)?;
        Ok((fraction.clone(), div(aggregate.cost, fraction)?))
    };
    let Ok((fraction, projected)) = calculate() else {
        base["status"] = "failed".into();
        base["reason"] = "Month-end trend could not be calculated.".into();
        return Ok(base);
    };
    let partial = aggregate.priced != aggregate.count;
    base["projected_cost"] = dj(projected.clone());
    base["value_label"] = format_cost(Some(projected)).into();
    base["elapsed_fraction"] = fixed(fraction, 6).into();
    base["coverage_state"] = if partial { "partial" } else { "complete" }.into();
    base["status"] = if ["stale", "error"].contains(&text(freshness, "status").unwrap_or_default())
    {
        "stale"
    } else if partial {
        "partial"
    } else {
        "current"
    }
    .into();
    base["reason"] = if partial {
        "Uses compatible priced usage records only."
    } else {
        "Directional estimate from current-month compatible usage."
    }
    .into();
    Ok(base)
}
fn scope_url(scope: &UsageScope, field: &str, value: &str) -> String {
    let mut values = vec![
        ("view", scope.view.clone()),
        ("source", scope.source.clone()),
        ("metric", scope.metric.clone()),
        ("breakdown", scope.breakdown.clone()),
    ];
    if scope.custom {
        values.push(("from", scope.from_date.to_string()));
        values.push(("to", scope.to_date.to_string()));
    }
    if let Some((_, current)) = values.iter_mut().find(|(key, _)| *key == field) {
        *current = value.into();
    }
    values.retain(|(key, value)| !(*key == "breakdown" && value == "source"));
    format!("/sessions-dashboard?{}", urlencode(&values))
}
fn controls(scope: &UsageScope) -> Value {
    let list = |field: &str, options: &[(&str, &str)]| {
        options.iter().map(|(value,label)|json!({"value":value,"label":label,"url":scope_url(scope,field,value)})).collect::<Vec<_>>()
    };
    let mut sources = vec![
        json!({"value":"all","label":"All","provider_kind":null,"url":scope_url(scope,"source","all")}),
    ];
    sources.extend(scope.source_options.iter().map(|option| {
        let mut option = option.clone();
        option["url"] =
            scope_url(scope, "source", text(&option, "value").unwrap_or_default()).into();
        option
    }));
    json!({"views":list("view",&[("daily","Daily"),("weekly","Weekly"),("monthly","Monthly")]),"sources":sources,"metrics":list("metric",&[("cost","Cost"),("tokens","Tokens")]),"breakdowns":list("breakdown",&[("source","Source"),("model","Model"),("project","Project")])})
}
pub fn usage_dashboard_data(connection: &Connection, options: &UsageOptions) -> Result<Value> {
    let scope = normalize_usage_scope(connection, options)?;
    let zone = TimeZone::get(&scope.timezone)
        .map_err(|error| BackendError::invalid("timezone", error.to_string()))?;
    let mut dashboard = Dashboard::default();
    let mut untimed = 0u64;
    let mut all_rows = Vec::new();
    let mut selected_rows = Vec::new();
    scan_usage(connection, &scope, options.visible_only, |row| {
        let at = text(row, "occurred_at").and_then(clock::parse_timestamp);
        if let Some(at) = at {
            if scope.start_utc <= at && at < scope.end_utc {
                dashboard.add(row, at, &zone, &scope, !options.visible_only)?;
                if !options.visible_only {
                    selected_rows.push((row.clone(), at));
                }
            }
        } else {
            untimed += 1;
        }
        if !options.visible_only {
            all_rows.push((row.take(), at));
        }
        Ok(())
    })?;
    let aggregate = &dashboard.aggregate;
    let mut activity = Value::Null;
    let mut month_to_date = Value::Null;
    let mut fresh = Value::Null;
    let mut projection = Value::Null;
    let mut snapshots = BTreeSet::new();
    let mut last_calculated = None;
    if !options.visible_only {
        activity = crate::backend::sessions::activity::activity_summary(
            connection,
            Some(scope.start_utc),
            Some(scope.end_utc),
            if scope.source == "all" {
                None
            } else {
                Some(&scope.source)
            },
        )?;
        let moment = if let Some(now) = options.now {
            now
        } else if let Some(today) = options.today {
            local_instant(today.and_hms_opt(12, 0, 0).unwrap(), &scope.timezone)?
        } else {
            Utc::now()
        };
        let current_day = options
            .today
            .map(Ok)
            .unwrap_or_else(|| clock::local_day(moment, &scope.timezone))?;
        let month_start =
            clock::calendar_day_bounds(current_day.with_day(1).unwrap(), &scope.timezone)?.0;
        let month_end = moment + Duration::microseconds(1);
        let month_rows = all_rows
            .iter()
            .filter_map(|(row, at)| {
                at.filter(|at| month_start <= *at && *at < month_end)
                    .map(|at| (row.clone(), at))
            })
            .collect::<Vec<_>>();
        let mut month = Aggregate::default();
        for (row, at) in &month_rows {
            month.add(row, clock::local_day_in_zone(*at, &zone)?, true)?;
        }
        month_to_date = month.as_json();
        month_to_date["tokens_label"] = format_tokens(month.total_tokens())?.into();
        month_to_date["cost_label"] = format_cost(month.estimated_cost()).into();
        fresh = freshness(connection, &scope.source)?;
        let mut counts: HashMap<String, u64> = HashMap::new();
        for (row, _) in &selected_rows {
            *counts.entry(key(&row["source_id"])).or_default() += 1;
            if let Some(label) = nonempty(row, "price_snapshot_label") {
                snapshots.insert(label.to_owned());
            }
            if let Some(value) = nonempty(row, "calculated_at") {
                last_calculated = Some(
                    last_calculated
                        .map_or(value.to_owned(), |old: String| old.max(value.to_owned())),
                );
            }
        }
        for row in fresh["sources"]
            .as_array_mut()
            .expect("freshness sources array")
        {
            row["selected_usage_record_count"] =
                counts.get(&key(&row["id"])).copied().unwrap_or(0).into();
        }
        projection = current_month_projection(&month_rows, &scope, moment, &fresh)?;
    }
    let mut limitations = Vec::new();
    if untimed > 0 {
        limitations.push(format!(
            "{} {} no usable occurrence time and {} excluded from history.",
            record_count(untimed, ""),
            if untimed == 1 { "has" } else { "have" },
            if untimed == 1 { "is" } else { "are" }
        ));
    }
    if aggregate.count > 0 && aggregate.covered < aggregate.count {
        limitations.push(format!(
            "Token totals cover {} of {}.",
            comma(&aggregate.covered.to_string()),
            record_count(aggregate.count, "selected")
        ));
    }
    let summary = json!([
        {"label":"Cost","value":format_cost(aggregate.estimated_cost()),"detail":format!("{} of {} priced · trend estimate",comma(&aggregate.priced.to_string()),record_count(aggregate.count,"")),"state":if aggregate.priced==0{"unavailable"}else{"default"}},
        {"label":"Total tokens","value":format_tokens(aggregate.total_tokens())?,"detail":record_count(aggregate.count,""),"state":if aggregate.covered==0{"unavailable"}else{"default"}},
        {"label":"Primary work Sessions","value":comma(&aggregate.sessions.len().to_string()),"detail":"usage-linked primary work Sessions; excludes maintenance and subsessions","state":"default"},
        {"label":"Active days","value":comma(&aggregate.days.len().to_string()),"detail":if activity.is_null(){String::new()}else{format!("{} est. active · longest segment {}",format_duration(activity["estimated_active_seconds"].as_i64().unwrap_or(0)),format_duration(activity["longest_active_segment_seconds"].as_i64().unwrap_or(0)))},"state":"default"}
    ]);
    let has_source_usage = if options.visible_only {
        aggregate.count > 0 || has_usage(connection, &scope.source)?
    } else {
        !all_rows.is_empty()
    };
    let title = match (scope.view.as_str(), scope.metric.as_str()) {
        ("cumulative", "cost") => "Cumulative cost",
        ("cumulative", _) => "Cumulative tokens",
        ("monthly", "cost") => "Monthly cost",
        ("monthly", _) => "Monthly tokens",
        (_, "cost") => "Cost history",
        _ => "Token history",
    };
    Ok(
        json!({"scope":scope.as_json(),"controls":controls(&scope),"summary":summary,"aggregate":aggregate.as_json(),"month_to_date":month_to_date,"activity":activity,"history":history(&dashboard.buckets,&scope)?,"history_has_values":if scope.metric=="tokens"{aggregate.covered>0}else{aggregate.priced>0},"history_title":title,"history_unit":if scope.metric=="cost"{"USD"}else{"normalized tokens"},"freshness":fresh,"projection":projection,"breakdown":dashboard.breakdown(&scope)?,"last_calculated_at":last_calculated,"snapshot_labels":snapshots,"limitations":limitations,"has_usage":aggregate.count>0,"empty_kind":if has_source_usage{"filtered"}else{"source"}}),
    )
}
