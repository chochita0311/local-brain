use crate::backend::{clock, db, Result};
use chrono::{DateTime, Duration, Utc};
pub use clock::{calendar_day_bounds, calendar_week_bounds, parse_timestamp};
use rusqlite::{params_from_iter, Connection};
use serde_json::{json, Value};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ActivitySegment {
    pub start: DateTime<Utc>,
    pub end: DateTime<Utc>,
    pub session_id: Option<i64>,
}
impl ActivitySegment {
    pub fn seconds(&self) -> i64 {
        0.max((self.end - self.start).num_seconds())
    }
}
pub fn build_activity_segments(
    mut timestamps: Vec<DateTime<Utc>>,
    session_id: Option<i64>,
) -> Vec<ActivitySegment> {
    timestamps.sort();
    let Some(first) = timestamps.first().copied() else {
        return Vec::new();
    };
    let mut start = first;
    let mut previous = first;
    let mut result = Vec::new();
    for current in timestamps.into_iter().skip(1) {
        if current - previous <= Duration::minutes(30) {
            previous = current;
        } else {
            result.push(ActivitySegment {
                start,
                end: previous,
                session_id,
            });
            start = current;
            previous = current;
        }
    }
    result.push(ActivitySegment {
        start,
        end: previous,
        session_id,
    });
    result
}
pub fn clip_segment(
    segment: ActivitySegment,
    start: Option<DateTime<Utc>>,
    end: Option<DateTime<Utc>>,
) -> Option<ActivitySegment> {
    let first = start.map_or(segment.start, |v| v.max(segment.start));
    let last = end.map_or(segment.end, |v| v.min(segment.end));
    if last < first || end.is_some_and(|end| first >= end) {
        None
    } else {
        Some(ActivitySegment {
            start: first,
            end: last,
            session_id: segment.session_id,
        })
    }
}
pub fn merge_activity_segments(mut segments: Vec<ActivitySegment>) -> Vec<ActivitySegment> {
    segments.sort_by_key(|s| (s.start, s.end));
    let mut result: Vec<ActivitySegment> = Vec::new();
    for segment in segments {
        if let Some(previous) = result
            .last_mut()
            .filter(|previous| segment.start <= previous.end)
        {
            previous.end = previous.end.max(segment.end);
        } else {
            result.push(ActivitySegment {
                session_id: None,
                ..segment
            });
        }
    }
    result
}
pub fn activity_summary_from_events(
    events: impl IntoIterator<Item = (i64, Option<DateTime<Utc>>)>,
    start: Option<DateTime<Utc>>,
    end: Option<DateTime<Utc>>,
) -> Value {
    let mut grouped: BTreeMap<i64, Vec<DateTime<Utc>>> = BTreeMap::new();
    for (id, at) in events {
        if let Some(at) = at {
            grouped.entry(id).or_default().push(at);
        }
    }
    let mut segments = Vec::new();
    let mut spans = Vec::new();
    for (id, mut times) in grouped {
        times.sort();
        let span = ActivitySegment {
            start: times[0],
            end: *times.last().unwrap(),
            session_id: Some(id),
        };
        if let Some(span) = clip_segment(span, start, end) {
            spans.push(span);
        }
        segments.extend(
            build_activity_segments(times, Some(id))
                .into_iter()
                .filter_map(|s| clip_segment(s, start, end)),
        );
    }
    let count = segments.len();
    let merged = merge_activity_segments(segments);
    json!({"observed_session_span_seconds":spans.iter().map(ActivitySegment::seconds).sum::<i64>(),"estimated_active_seconds":merged.iter().map(ActivitySegment::seconds).sum::<i64>(),"longest_active_segment_seconds":merged.iter().map(ActivitySegment::seconds).max().unwrap_or(0),"session_count":spans.len(),"activity_segment_count":count,"merged_segment_count":merged.len(),"segments":merged.iter().map(|s|json!({"start":clock::isoformat(s.start),"end":clock::isoformat(s.end),"session_id":s.session_id})).collect::<Vec<_>>()})
}
pub fn activity_summary(
    conn: &Connection,
    start: Option<DateTime<Utc>>,
    end: Option<DateTime<Utc>>,
    source: Option<&str>,
) -> Result<Value> {
    let source = source.filter(|s| !s.is_empty());
    let filter = if source.is_some() {
        "AND sources.id = ?"
    } else {
        ""
    };
    let rows=db::rows(conn,&format!("SELECT activity_events.session_id, activity_events.occurred_at FROM activity_events JOIN sessions ON sessions.id = activity_events.session_id JOIN sources ON sources.id = sessions.source_id WHERE activity_events.occurred_at IS NOT NULL {filter} ORDER BY activity_events.session_id, activity_events.occurred_at, activity_events.sequence"),params_from_iter(source))?;
    Ok(activity_summary_from_events(
        rows.iter().map(|row| {
            (
                row["session_id"].as_i64().unwrap(),
                row["occurred_at"].as_str().and_then(parse_timestamp),
            )
        }),
        start,
        end,
    ))
}
