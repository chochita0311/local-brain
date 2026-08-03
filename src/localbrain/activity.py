import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import DefaultDict, Iterable, List, Optional, Tuple
from zoneinfo import ZoneInfo

from .config import settings


ACTIVITY_GAP = timedelta(minutes=30)


@dataclass(frozen=True)
class ActivitySegment:
    start: datetime
    end: datetime
    session_id: Optional[int] = None

    @property
    def seconds(self) -> int:
        return max(0, int((self.end - self.start).total_seconds()))


def parse_timestamp(value: object) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_activity_segments(
    timestamps: Iterable[datetime], session_id: Optional[int] = None
) -> List[ActivitySegment]:
    ordered = sorted(
        timestamp.astimezone(timezone.utc)
        for timestamp in timestamps
        if timestamp.tzinfo is not None
    )
    if not ordered:
        return []
    segments: List[ActivitySegment] = []
    start = previous = ordered[0]
    for current in ordered[1:]:
        if current - previous <= ACTIVITY_GAP:
            previous = current
            continue
        segments.append(ActivitySegment(start, previous, session_id))
        start = previous = current
    segments.append(ActivitySegment(start, previous, session_id))
    return segments


def clip_segment(
    segment: ActivitySegment,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Optional[ActivitySegment]:
    if start is not None and start.tzinfo is None:
        raise ValueError("activity range start must be timezone-aware")
    if end is not None and end.tzinfo is None:
        raise ValueError("activity range end must be timezone-aware")
    clipped_start = max(segment.start, start.astimezone(timezone.utc)) if start else segment.start
    clipped_end = min(segment.end, end.astimezone(timezone.utc)) if end else segment.end
    if clipped_end < clipped_start:
        return None
    if end is not None and clipped_start >= end.astimezone(timezone.utc):
        return None
    return ActivitySegment(clipped_start, clipped_end, segment.session_id)


def merge_activity_segments(
    segments: Iterable[ActivitySegment],
) -> List[ActivitySegment]:
    ordered = sorted(segments, key=lambda segment: (segment.start, segment.end))
    merged: List[ActivitySegment] = []
    for segment in ordered:
        if not merged or segment.start > merged[-1].end:
            merged.append(ActivitySegment(segment.start, segment.end))
            continue
        previous = merged[-1]
        merged[-1] = ActivitySegment(previous.start, max(previous.end, segment.end))
    return merged


def activity_summary_from_events(
    events: Iterable[Tuple[int, object]],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> dict:
    grouped: DefaultDict[int, List[datetime]] = defaultdict(list)
    for session_id, value in events:
        parsed = value if isinstance(value, datetime) else parse_timestamp(value)
        if parsed is None or parsed.tzinfo is None:
            continue
        grouped[int(session_id)].append(parsed.astimezone(timezone.utc))

    segments: List[ActivitySegment] = []
    spans: List[ActivitySegment] = []
    for session_id, timestamps in grouped.items():
        ordered = sorted(timestamps)
        segment_span = ActivitySegment(ordered[0], ordered[-1], session_id)
        clipped_span = clip_segment(segment_span, start, end)
        if clipped_span:
            spans.append(clipped_span)
        for segment in build_activity_segments(ordered, session_id):
            clipped = clip_segment(segment, start, end)
            if clipped:
                segments.append(clipped)

    merged = merge_activity_segments(segments)
    return {
        "observed_session_span_seconds": sum(span.seconds for span in spans),
        "estimated_active_seconds": sum(segment.seconds for segment in merged),
        "longest_active_segment_seconds": max(
            (segment.seconds for segment in merged), default=0
        ),
        "session_count": len({span.session_id for span in spans}),
        "activity_segment_count": len(segments),
        "merged_segment_count": len(merged),
        "segments": merged,
    }


def activity_summary(
    connection: sqlite3.Connection,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    source_kind: Optional[str] = None,
) -> dict:
    params = []
    source_filter = ""
    if source_kind:
        source_filter = "AND sources.kind = ?"
        params.append(source_kind)
    rows = connection.execute(
        """
        SELECT activity_events.session_id, activity_events.occurred_at
        FROM activity_events
        JOIN sessions ON sessions.id = activity_events.session_id
        JOIN sources ON sources.id = sessions.source_id
        WHERE activity_events.occurred_at IS NOT NULL
        {source_filter}
        ORDER BY activity_events.session_id, activity_events.occurred_at,
                 activity_events.sequence
        """.format(source_filter=source_filter),
        tuple(params),
    ).fetchall()
    return activity_summary_from_events(
        ((row["session_id"], row["occurred_at"]) for row in rows),
        start=start,
        end=end,
    )


def calendar_day_bounds(
    local_day: date, timezone_name: Optional[str] = None
) -> Tuple[datetime, datetime]:
    zone = ZoneInfo(timezone_name or settings.timezone_name)
    start = datetime.combine(local_day, time.min, tzinfo=zone)
    return start.astimezone(timezone.utc), (start + timedelta(days=1)).astimezone(timezone.utc)


def calendar_week_bounds(
    local_day: date, timezone_name: Optional[str] = None
) -> Tuple[datetime, datetime]:
    monday = local_day - timedelta(days=local_day.weekday())
    start, _ = calendar_day_bounds(monday, timezone_name)
    next_start, _ = calendar_day_bounds(monday + timedelta(days=7), timezone_name)
    return start, next_start
