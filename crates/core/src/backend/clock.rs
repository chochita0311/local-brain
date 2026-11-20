//! Source timestamps use Python 3.11's ISO calendar and microsecond contract.
use super::{BackendError, Result};
use chrono::{DateTime, Datelike, Duration, NaiveDate, NaiveDateTime, Timelike, Utc, Weekday};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ParsedTimestamp {
    pub local: NaiveDateTime,
    pub offset_micros: Option<i64>,
}

fn decimal(value: &str) -> Option<u32> {
    (!value.is_empty() && value.bytes().all(|b| b.is_ascii_digit()))
        .then(|| value.parse().ok())
        .flatten()
}

pub fn parse_date(value: &str) -> Option<NaiveDate> {
    let bytes = value.as_bytes();
    if !value.is_ascii() {
        return None;
    }
    let year = decimal(value.get(..4)?)? as i32;
    if !(1..=9999).contains(&year) {
        return None;
    }
    if value.len() == 10 && bytes[4] == b'-' && bytes[7] == b'-' {
        return NaiveDate::from_ymd_opt(year, decimal(&value[5..7])?, decimal(&value[8..])?);
    }
    if value.len() == 8 && bytes[4] != b'-' && bytes[4] != b'W' {
        return NaiveDate::from_ymd_opt(year, decimal(&value[4..6])?, decimal(&value[6..])?);
    }
    let rest = value.get(4..)?.strip_prefix('-').unwrap_or(&value[4..]);
    let rest = rest.strip_prefix('W')?;
    let week = decimal(rest.get(..2)?)?;
    let day = match rest.get(2..)? {
        "" => 1,
        s => decimal(s.strip_prefix('-').unwrap_or(s))?,
    };
    let weekday = match day {
        1 => Weekday::Mon,
        2 => Weekday::Tue,
        3 => Weekday::Wed,
        4 => Weekday::Thu,
        5 => Weekday::Fri,
        6 => Weekday::Sat,
        7 => Weekday::Sun,
        _ => return None,
    };
    // Extended and basic ISO week components cannot be mixed.
    if value.as_bytes().get(4) == Some(&b'-') {
        if !matches!(value.len(), 8 | 10) || (value.len() == 10 && value.as_bytes()[8] != b'-') {
            return None;
        }
    } else if !matches!(value.len(), 7 | 8) {
        return None;
    }
    NaiveDate::from_isoywd_opt(year, week, weekday).filter(|day| (1..=9999).contains(&day.year()))
}

fn parse_clock(value: &str, offset: bool, zone_follows: bool) -> Option<(u32, u32, u32, u32)> {
    // CPython3.11 stops the clock at a following zone marker. Its legacy
    // scanner also admits a final extra character there; ordinary strict ISO
    // parsers lose valid historical source timestamps at that boundary.
    let bytes = value.as_bytes();
    let mut fields = [0u32; 4];
    let mut cursor = 0;
    let mut separators = false;
    let finish = |fields: [u32; 4]| {
        if !offset && (fields[0] > 23 || fields[1] > 59 || fields[2] > 59) {
            None
        } else {
            Some((fields[0], fields[1], fields[2], fields[3]))
        }
    };
    for component in 0..3 {
        let pair = bytes.get(cursor..cursor + 2)?;
        if !pair.iter().all(u8::is_ascii_digit) {
            return None;
        }
        fields[component] = u32::from(pair[0] - b'0') * 10 + u32::from(pair[1] - b'0');
        cursor += 2;
        let next = bytes
            .get(cursor)
            .copied()
            .unwrap_or(if zone_follows { b'Z' } else { 0 });
        cursor += 1;
        if component == 0 {
            separators = next == b':';
        }
        if cursor >= bytes.len() {
            return if zone_follows || next == 0 {
                finish(fields)
            } else {
                None
            };
        }
        if separators && next == b':' {
            continue;
        }
        if next == b'.' || next == b',' {
            break;
        }
        if separators {
            return None;
        }
        cursor -= 1;
    }
    let length = (bytes.len() - cursor).min(6);
    if length == 0 {
        return None;
    }
    for byte in &bytes[cursor..cursor + length] {
        if !byte.is_ascii_digit() {
            return None;
        }
        fields[3] = fields[3] * 10 + u32::from(*byte - b'0');
    }
    fields[3] *= 10u32.pow(6 - length as u32);
    cursor += length;
    while bytes.get(cursor).is_some_and(u8::is_ascii_digit) {
        cursor += 1;
    }
    if cursor < bytes.len() && !zone_follows {
        return None;
    }
    finish(fields)
}

pub fn parse_iso_datetime(value: &str) -> Option<ParsedTimestamp> {
    // Prefer the longest complete date. The single following Unicode character
    // is the source's date/time separator, as admitted by datetime.fromisoformat.
    let (date, end) = [10usize, 8, 7]
        .into_iter()
        .filter(|end| value.is_char_boundary(*end))
        .find_map(|end| parse_date(value.get(..end)?).map(|date| (date, end)))?;
    if value.len() == end {
        return Some(ParsedTimestamp {
            local: date.and_hms_opt(0, 0, 0)?,
            offset_micros: None,
        });
    }
    let remainder = value.get(end..)?;
    let separator = remainder.chars().next()?;
    let time = remainder.get(separator.len_utf8()..)?;
    if time.is_empty() {
        return None;
    }
    let zone_at = time.find(['+', '-', 'Z']);
    let (time, offset_micros) = if let Some(index) = zone_at {
        let zone = &time[index..];
        let offset = if zone == "Z" {
            0
        } else {
            let (hour, minute, second, micros) = parse_clock(zone.get(1..)?, true, false)?;
            let seconds = i64::from(hour) * 3600 + i64::from(minute) * 60 + i64::from(second);
            let total = if seconds == 0 {
                0
            } else {
                seconds * 1_000_000 + i64::from(micros)
            };
            if total >= 86_400_000_000 {
                return None;
            }
            if zone.starts_with('-') {
                -total
            } else {
                total
            }
        };
        (&time[..index], Some(offset))
    } else {
        (time, None)
    };
    let (hour, minute, second, micros) = parse_clock(time, false, zone_at.is_some())?;
    Some(ParsedTimestamp {
        local: date.and_hms_micro_opt(hour, minute, second, micros)?,
        offset_micros,
    })
}

impl ParsedTimestamp {
    pub fn utc(self) -> Option<DateTime<Utc>> {
        let naive = self
            .local
            .checked_sub_signed(Duration::microseconds(self.offset_micros.unwrap_or(0)))?;
        (1..=9999).contains(&naive.year()).then(|| naive.and_utc())
    }
    pub fn isoformat(self) -> String {
        let mut result = naive_isoformat(self.local);
        if let Some(offset) = self.offset_micros {
            let sign = if offset < 0 { '-' } else { '+' };
            let offset = offset.unsigned_abs();
            let seconds = offset / 1_000_000;
            result.push_str(&format!(
                "{sign}{:02}:{:02}",
                seconds / 3600,
                (seconds / 60) % 60
            ));
            if seconds % 60 != 0 || offset % 1_000_000 != 0 {
                result.push_str(&format!(":{:02}", seconds % 60));
            }
            if offset % 1_000_000 != 0 {
                result.push_str(&format!(".{:06}", offset % 1_000_000));
            }
        }
        result
    }
}

pub fn parse_timestamp(value: &str) -> Option<DateTime<Utc>> {
    parse_iso_datetime(value.trim_matches(super::unicode::python_space))
        .and_then(ParsedTimestamp::utc)
}
pub fn naive_isoformat(value: NaiveDateTime) -> String {
    let mut result = value.format("%Y-%m-%dT%H:%M:%S").to_string();
    if value.nanosecond() / 1000 != 0 {
        result.push_str(&format!(".{:06}", value.nanosecond() / 1000));
    }
    result
}
pub fn isoformat(value: DateTime<Utc>) -> String {
    format!("{}+00:00", naive_isoformat(value.naive_utc()))
}
pub fn stamp(value: DateTime<Utc>) -> String {
    value.to_rfc3339_opts(chrono::SecondsFormat::Micros, false)
}
pub fn local_day(value: DateTime<Utc>, timezone_name: &str) -> Result<NaiveDate> {
    let zone = jiff::tz::TimeZone::get(timezone_name)
        .map_err(|e| BackendError::invalid("timezone", e.to_string()))?;
    local_day_in_zone(value, &zone)
}
pub(crate) fn local_day_in_zone(
    value: DateTime<Utc>,
    zone: &jiff::tz::TimeZone,
) -> Result<NaiveDate> {
    let timestamp = jiff::Timestamp::from_microsecond(value.timestamp_micros())
        .map_err(|e| BackendError::invalid("timestamp", e.to_string()))?;
    let date = zone.to_datetime(timestamp).date();
    NaiveDate::from_ymd_opt(date.year().into(), date.month() as u32, date.day() as u32)
        .ok_or_else(|| BackendError::invalid("timestamp", "Date outside supported calendar"))
}
pub fn calendar_day_bounds(
    day: NaiveDate,
    timezone_name: &str,
) -> Result<(DateTime<Utc>, DateTime<Utc>)> {
    let zone = jiff::tz::TimeZone::get(timezone_name)
        .map_err(|e| BackendError::invalid("timezone", e.to_string()))?;
    let boundary = |day: NaiveDate| -> Result<DateTime<Utc>> {
        let local =
            jiff::civil::date(day.year() as i16, day.month() as i8, day.day() as i8).at(0, 0, 0, 0);
        // Python ZoneInfo uses fold=0: earlier instant at an overlap, pre-gap
        // offset at a nonexistent midnight (the later compatible instant).
        let timestamp = local
            .to_zoned(zone.clone())
            .map_err(|e| BackendError::invalid("timestamp", e.to_string()))?
            .timestamp();
        DateTime::from_timestamp(timestamp.as_second(), timestamp.subsec_nanosecond() as u32)
            .ok_or_else(|| BackendError::invalid("timestamp", "Date outside supported calendar"))
    };
    Ok((
        boundary(day)?,
        boundary(day.succ_opt().ok_or_else(|| {
            BackendError::invalid("timestamp", "Date outside supported calendar")
        })?)?,
    ))
}
pub fn calendar_week_bounds(
    day: NaiveDate,
    timezone_name: &str,
) -> Result<(DateTime<Utc>, DateTime<Utc>)> {
    let monday = day - Duration::days(i64::from(day.weekday().num_days_from_monday()));
    Ok((
        calendar_day_bounds(monday, timezone_name)?.0,
        calendar_day_bounds(monday + Duration::days(7), timezone_name)?.0,
    ))
}
