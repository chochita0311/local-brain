"""Independently authored synthetic outcomes; never imported by the extractor."""

import copy


def session(number):
    return {"id": number, "source_key": "synthetic", "external_id": str(number),
            "session_class": "work", "session_role": "primary", "index_policy": "full",
            "event_count": 1}


def record(key, text, number=1, **overrides):
    result = {"key": key, "kind": "session", "session_id": number, "role": "user",
              "offset": 0, "at": "2030-01-01T00:00:00Z", "text": text}
    result.update(overrides)
    return result


def snapshot(records, **overrides):
    ids = sorted({r["session_id"] for r in records if r.get("session_id")})
    value = {"version": 1, "name": "synthetic", "sessions": [session(n) for n in ids],
             "records": records, "artifacts": [], "references": [],
             "coverage": {"complete": True, "unexamined": 0}, "organization_links": []}
    value.update(overrides)
    return value


def member(row, start=0, end=None):
    return {"record_key": row["key"], "start": row["offset"] + start,
            "end": row["offset"] + (len(row["text"]) if end is None else end)}


def goal(key, subject, change, rows, **overrides):
    result = {"key": key, "subject": subject, "change": change, "completion": None,
              "members": [member(r) for r in rows],
              "acceptable_labels": [change + " " + subject]}
    result.update(overrides)
    return result


# Preauthored linguistic expectations use multiple phrasings, not only prompts
# following one template. They are contract witnesses, not blinded quality data.
LANGUAGE_CASES = [
    ("Please reduce checkout latency.", "checkout latency", "reduce"),
    ("Our goal is to reduce checkout latency.", "checkout latency", "reduce"),
    ("Investigate timeouts to reduce checkout latency.", "checkout latency", "reduce"),
    ("Implement tracing to reduce checkout latency.", "checkout latency", "reduce"),
    ("Verify the patch to reduce checkout latency.", "checkout latency", "reduce"),
    ("Our objective is to lower checkout latency.", "checkout latency", "reduce"),
    ("We want to improve session synchronization.", "session synchronization", "improve"),
    ("세션 동기화를 개선하자.", "세션 동기화", "improve"),
    ("체크아웃 지연을 줄이기 위해 병목을 조사한다.", "체크아웃 지연", "reduce"),
    ("캐시 용량을 늘리자.", "캐시 용량", "increase"),
    ("캐시 용량을 줄이자.", "캐시 용량", "reduce"),
    ("오래된 인덱스를 제거하자.", "오래된 인덱스", "remove"),
    ("Enable audit logging.", "audit logging", "enable"),
    ("Disable audit logging.", "audit logging", "disable"),
]


def long_history():
    rows = [record("long-{}".format(i), [
        "Investigate retries to improve session synchronization.",
        "Implement batching to improve session synchronization.",
        "Verify recovery to improve session synchronization.",
    ][i % 3], i + 1) for i in range(30)]
    goals = [goal("synchronization", "session synchronization", "improve", rows)]
    for i, subject in enumerate(("checkout latency", "search accuracy", "schema validation",
                                 "backup integrity", "source discovery", "rendering speed",
                                 "error recovery", "document parsing", "cache efficiency")):
        added = [record("peer-{}-{}".format(i, j), "Improve {}.".format(subject),
                        31 + i * 2 + j) for j in range(2)]
        rows.extend(added)
        goals.append(goal("peer-{}".format(i), subject, "improve", added))
    return snapshot(rows), {"version": 1, "groups": goals, "negative": [], "unresolved": 0}


def bind_expectations(data, expected):
    # Hashing is transport integrity only; no extractor or scoring helper
    # determines the expected outcome or membership.
    import hashlib
    import json
    result = copy.deepcopy(expected)
    result["snapshot_digest"] = hashlib.sha256(json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode("utf-8")).hexdigest()
    return result
