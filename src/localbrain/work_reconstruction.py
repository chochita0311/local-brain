"""Bounded experimental goal extraction. No source access or production state."""

from __future__ import annotations

import hashlib
import itertools
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime


VERSION = "localbrain.work-reconstruction.v1"
MAX_SESSIONS = 60
MAX_RECORDS = 12_060
MAX_TEXT = 2_500_000
MAX_REFERENCES = 12_000
MAX_PAIRS = 4_096


class ExperimentError(ValueError):
    """Only fixed, non-identifying diagnostics cross the command boundary."""


def require(condition, code="INVALID_INPUT"):
    if not condition:
        raise ExperimentError(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def key(prefix, *values):
    return prefix + ":" + digest(values)


def normalized(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split()).strip(" .!?。")


def timestamp(value):
    require(isinstance(value, str) and len(value) <= 80)
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(result.tzinfo is not None)
        return result
    except (ValueError, OverflowError):
        raise ExperimentError("INVALID_TIME") from None


def bounded_list(value, limit):
    require(isinstance(value, list) and len(value) <= limit, "INPUT_LIMIT")
    return value


def identifier(value):
    require(isinstance(value, str) and 0 < len(value) <= 500)
    return value


def eligible(row):
    return (row.get("session_class"), row.get("session_role"), row.get("index_policy")) == ("work", "primary", "full")


def validate_snapshot(data):
    require(isinstance(data, dict) and data.get("version") == 1)
    require(set(data) <= {"version", "name", "sessions", "records", "artifacts", "references", "coverage", "organization_links"})
    identifier(data.get("name"))
    sessions = bounded_list(data.get("sessions"), MAX_SESSIONS)
    ids = []
    for session in sessions:
        require(isinstance(session, dict) and set(session) <= {
            "id", "source_key", "external_id", "session_class", "session_role", "index_policy",
            "event_count", "title", "workspace_id", "ended_at", "has_activity_events", "has_usage_records"})
        sid = session.get("id")
        require(type(sid) is int and sid > 0)
        identifier(session.get("source_key")); identifier(session.get("external_id"))
        require(type(session.get("event_count")) is int and session["event_count"] >= 0)
        require(session.get("title") is None or isinstance(session["title"], str) and len(session["title"]) <= 500)
        ids.append(sid)
    require(len(ids) == len(set(ids)))
    require(len({s["source_key"] for s in sessions}) <= 8, "INPUT_LIMIT")
    records = bounded_list(data.get("records"), MAX_RECORDS)
    seen, totals, counts, kinds = set(), Counter(), Counter(), Counter()
    for record in records:
        require(isinstance(record, dict) and set(record) <= {
            "key", "kind", "session_id", "role", "offset", "at", "text"})
        rid = identifier(record.get("key"))
        require(rid not in seen); seen.add(rid)
        kind = record.get("kind")
        require(kind in {"session", "document", "item", "organization"})
        role = record.get("role")
        require(role in ({"user", "assistant"} if kind == "session" else {"document", "owner"}))
        require(type(record.get("offset")) is int and record["offset"] >= 0)
        require(isinstance(record.get("text"), str))
        limit = 4000 if kind == "session" else 2000 if kind == "organization" else 8000
        require(len(record["text"]) <= limit, "INPUT_LIMIT")
        if record.get("at") is not None:
            timestamp(record["at"])
        if kind == "session":
            require(record.get("session_id") in ids)
            totals[record["session_id"]] += len(record["text"])
            counts[record["session_id"]] += 1
        else:
            require(record.get("session_id") is None)
        kinds[kind] += 1
    require(all(n <= 32000 for n in totals.values()) and all(n <= 200 for n in counts.values()), "INPUT_LIMIT")
    require(all(kinds[k] <= 20 for k in ("document", "item", "organization")), "INPUT_LIMIT")
    require(sum(len(r["text"]) for r in records) <= MAX_TEXT, "INPUT_LIMIT")
    for artifact in bounded_list(data.get("artifacts"), 2000):
        require(isinstance(artifact, dict) and set(artifact) <= {
            "kind", "source_scope", "source_identity", "title", "identity_state", "enabled",
            "is_container", "availability", "freshness"})
    for reference in bounded_list(data.get("references"), MAX_REFERENCES):
        require(isinstance(reference, dict) and set(reference) <= {
            "episode_key", "artifact_key", "reference_identity", "evidence_kind", "read_outcome", "observed_at"})
    bounded_list(data.get("organization_links"), 200)
    coverage = data.get("coverage")
    require(isinstance(coverage, dict) and type(coverage.get("complete")) is bool)
    require(type(coverage.get("unexamined")) is int and coverage["unexamined"] >= 0)
    require(not coverage["complete"] or coverage["unexamined"] == 0)
    return data


_ACTIONS = {
    "reduce": ("reduce", "lower", "decrease"),
    "increase": ("increase", "raise", "expand"),
    "improve": ("improve", "optimize", "optimise"),
    "fix": ("fix", "repair", "resolve"),
    "add": ("add", "introduce"), "remove": ("remove", "delete", "retire"),
    "replace": ("replace",), "enable": ("enable",), "disable": ("disable",),
}
_VERBS = {word: action for action, words in _ACTIONS.items() for word in words}
_ENGLISH = re.compile(
    r"(?:^|\bto\s+)(?:please\s+)?(?P<verb>" + "|".join(_VERBS) + r")\s+(?P<subject>.+)", re.I)
_PREFIX = re.compile(r"^(?:(?:our|the)\s+(?:goal|objective|aim)\s+is\s+(?:to\s+)?|"
                     r"(?:we|i)\s+(?:need|want|aim)\s+to\s+|goal\s*:\s*|please\s+)", re.I)
_KOREAN = re.compile(
    r"(?P<subject>.+?)(?:을|를)\s*(?P<verb>줄이|늘리|개선하|최적화하|수정하|고치|추가하|제거하|삭제하|교체하|활성화하|비활성화하)")
_KVERBS = {"줄이": "reduce", "늘리": "increase", "개선하": "improve", "최적화하": "improve",
           "수정하": "fix", "고치": "fix", "추가하": "add", "제거하": "remove", "삭제하": "remove",
           "교체하": "replace", "활성화하": "enable", "비활성화하": "disable"}
_PHASES = [("investigation", r"investigat|diagnos|조사|분석"),
           ("implementation", r"implement|build|구현"),
           ("verification", r"verif|test|검증|테스트")]


def statements(record):
    # Decimal punctuation is not a sentence boundary. Offsets always refer to
    # the admitted source, never a normalized or reconstructed copy of its text.
    cursor = 0
    ends = [m.end() for m in re.finditer(r"\n|[!?。]|\.(?=\s|$)", record["text"])]
    if not ends or ends[-1] != len(record["text"]):
        ends.append(len(record["text"]))
    for finish in ends:
        segment = record["text"][cursor:finish]
        raw = segment.strip()
        if not raw:
            cursor = finish
            continue
        start = record["offset"] + cursor + len(segment) - len(segment.lstrip())
        end = record["offset"] + cursor + len(segment.rstrip())
        cursor = finish
        yield raw, start, end


def extract(record):
    found, missing = [], []
    for raw, start, end in statements(record):
        location = {"record_key": record["key"], "start": start, "end": end}
        # An equal-length source edit is new evidence, not an old correction's
        # target. Appending text elsewhere leaves this exact claim unchanged.
        sid = key("statement", record["key"], start, end, raw)
        text = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+|#{1,6}\s+)", "", raw.strip(" .!?。"))
        if re.search(r"\b(?:do not|don't|not to|never)\b|하지\s*말|않", text, re.I):
            missing.append({**location, "reason": "unsupported-negation"}); continue
        completion = None
        complete = re.search(r"\s+(?:until|so that|완료\s*조건\s*:)\s+(.+)$", text, re.I)
        if complete:
            completion = normalized(complete.group(1))
            text = text[:complete.start()]
        outcome = raw if re.match(r"(?:completed|done|완료)\s*:", text, re.I) else None
        text = re.sub(r"^(?:completed|done|완료)\s*:\s*", "", text, flags=re.I)
        text = _PREFIX.sub("", text)
        english = _ENGLISH.search(text)
        korean = _KOREAN.search(text)
        if english:
            change, subject = _VERBS[english["verb"].lower()], normalized(english["subject"])
        elif korean:
            change, subject = _KVERBS[korean["verb"]], normalized(korean["subject"])
        else:
            missing.append({**location, "reason": "unsupported-goal"}); continue
        if not subject or len(subject) > 300 or re.search(r"https?://|[{}]", subject):
            missing.append({**location, "reason": "unsupported-subject"}); continue
        phase = next((name for name, pattern in _PHASES if re.search(pattern, raw, re.I)), "activity")
        found.append({"statement_key": sid, **location, "session_id": record.get("session_id"),
                      "source_kind": record["kind"], "role": record["role"], "observed_at": record.get("at"),
                      "subject": subject, "change": change, "completion": completion,
                      "outcome": outcome,
                      "phase": phase, "wording": raw, "wording_authority": "observed", "authority": "inferred",
                      "field_evidence": {field: {**location, "authority": "observed"}
                                         for field in ("subject", "change", "phase", "completion", "outcome")
                                         if field not in {"completion", "outcome"} or
                                         (field == "completion" and completion is not None) or
                                         (field == "outcome" and outcome is not None)}})
    return found, missing


def _flow(identity, values, user_label=None):
    members = sorted(values, key=lambda m: m["statement_key"])
    first = members[0]
    result = {"flow_id": identity, "subject": first["subject"], "change": first["change"],
              "completion": next((m["completion"] for m in members if m["completion"]), None),
              "label": first["change"] + " " + first["subject"], "user_label": user_label,
              "authority": "inferred", "lifecycle": "unknown", "members": members}
    result["revision"] = digest(result)
    return result


def reconstruct(data, corrections=(), include_organization=True):
    validate_snapshot(data)
    accepted = {s["id"] for s in data["sessions"] if eligible(s)}
    claims, unassigned = [], []
    coverage = dict(data["coverage"])
    for record in sorted(data["records"], key=lambda r: r["key"]):
        if record["kind"] == "organization" and not include_organization:
            continue
        if record["kind"] == "session" and record["session_id"] not in accepted:
            coverage["complete"] = False; coverage["unexamined"] += 1
            unassigned.append({"record_key": record["key"], "reason": "ineligible-session"}); continue
        extracted, unknown = extract(record)
        claims.extend(extracted); unassigned.extend(unknown)
    by_goal, buckets = defaultdict(list), defaultdict(list)
    for claim in claims:
        by_goal[(claim["subject"], claim["change"])].append(claim)
    for (subject, action), values in sorted(by_goal.items()):
        completions = {v["completion"] for v in values if v["completion"]}
        for claim in values:
            completion = claim["completion"]
            if completion is None and len(completions) > 1:
                unassigned.append({"record_key": claim["record_key"], "start": claim["start"],
                                   "end": claim["end"], "reason": "ambiguous-completion"})
                continue
            completion = completion or next(iter(completions), None)
            buckets[key("flow", subject, action, completion)].append(claim)
    require(isinstance(corrections, (list, tuple)) and len(corrections) <= 100)
    correction_rows, used, labels, correction_ids = [], set(), {}, set()
    lookup = {m["statement_key"]: m for values in buckets.values() for m in values}
    for correction in corrections:
        require(isinstance(correction, dict) and set(correction) <= {"id", "statement_keys", "label"})
        cid = identifier(correction.get("id"))
        require(cid not in correction_ids); correction_ids.add(cid)
        targets = bounded_list(correction.get("statement_keys"), MAX_RECORDS)
        require(len(targets) == len(set(targets)) and all(isinstance(k, str) for k in targets))
        require(not (used & set(targets))); used.update(targets)
        label = correction.get("label")
        require(label is None or isinstance(label, str) and 0 < len(label) <= 500)
        active = [lookup[k] for k in targets if k in lookup]
        identity = key("correction-flow", cid)
        for values in buckets.values():
            values[:] = [v for v in values if v["statement_key"] not in targets]
        buckets[identity] = [{**m, "authority": "user-corrected"} for m in active]
        labels[identity] = label
        correction_rows.append({"id": cid, "statement_keys": sorted(targets), "label": label,
                                "active_count": len(active)})
    flows = [_flow(k, values, labels.get(k)) for k, values in sorted(buckets.items()) if values]
    return {"version": VERSION, "flows": flows, "unassigned": sorted(unassigned, key=lambda x: (x["record_key"], x.get("start", 0))),
            "coverage": coverage, "corrections": sorted(correction_rows, key=lambda c: c["id"]),
            "routine_confirmations": 0}


def metadata_view(data):
    validate_snapshot(data)
    accepted = {s["id"] for s in data["sessions"] if eligible(s)}
    selected = [r for r in data["records"] if r["kind"] == "session"]
    excluded = sum(r["session_id"] not in accepted for r in selected)
    coverage = dict(data["coverage"])
    if excluded:
        coverage["complete"] = False
        coverage["unexamined"] += excluded
    return {"version": 1, "name": data["name"], "sessions": data["sessions"],
            "artifacts": data["artifacts"], "references": data["references"],
            "record_spans": [{"record_key": r["key"], "session_id": r["session_id"],
                              "start": r["offset"], "end": r["offset"] + len(r["text"])}
                             for r in selected if r["session_id"] in accepted],
            "coverage": coverage}


def metadata_baseline(data, include_organization=True):
    require(isinstance(data, dict) and set(data) == {
        "version", "name", "sessions", "artifacts", "references", "record_spans", "coverage"})
    require(data["version"] == 1)
    bounded_list(data["sessions"], MAX_SESSIONS); bounded_list(data["artifacts"], 2000)
    bounded_list(data["references"], MAX_REFERENCES); bounded_list(data["record_spans"], MAX_RECORDS)
    for span in data["record_spans"]:
        require(isinstance(span, dict) and set(span) == {"record_key", "session_id", "start", "end"})
        identifier(span["record_key"])
        require(type(span["start"]) is int and type(span["end"]) is int and 0 <= span["start"] <= span["end"])
    # Import only on explicit experiment invocation; no app startup/config.
    from .workstream_candidates import (
        candidate_artifact_from_record, candidate_reference_from_record,
        candidate_session_from_record, normalize_workstream_candidates,
    )
    artifacts = [candidate_artifact_from_record(a) for a in data["artifacts"]]
    valid_artifacts = {a.artifact_key for a in artifacts if a.enabled and not a.is_container
                       and a.identity_state == "resolved" and a.availability != "missing"}
    sessions = {candidate_session_from_record(s).episode_key: s for s in data["sessions"] if eligible(s)}
    refs = [candidate_reference_from_record(r) for r in data["references"]]
    by_session = defaultdict(set)
    for ref in refs:
        if ref.supports_membership and ref.episode_key in sessions and ref.artifact_key in valid_artifacts:
            by_session[ref.episode_key].add(ref.artifact_key)
    # Enumerate artifact combinations globally, but retain only pairs supported
    # by two Sessions. Input limits bound work; output overflow fails, not clips.
    by_artifact = defaultdict(set)
    for sid, items in by_session.items():
        for item in items:
            by_artifact[item].add(sid)
    pairs = []
    for left, right in itertools.combinations(sorted(by_artifact), 2):
        if len(by_artifact[left] & by_artifact[right]) >= 2:
            pairs.append((left, right))
            require(len(pairs) <= MAX_PAIRS, "BASELINE_LIMIT")
    flows = []
    # One pair per normalization call is within both the 200 pair and 2,000
    # membership caps even at the maximum admitted 60 Sessions.
    for pair in pairs:
        candidate = normalize_workstream_candidates(data["artifacts"], data["sessions"], data["references"], [pair])
        for group in candidate.candidates:
            session_ids = {m.session.session_id for m in group.members}
            members = []
            for span in data["record_spans"]:
                if span["session_id"] in session_ids and span["end"] > span["start"]:
                    members.append({**span, "statement_key": key("statement", span["record_key"], span["start"], span["end"])})
            flows.append({"flow_id": group.candidate_key, "subject": None, "change": None,
                          "completion": None, "label": None, "members": members, "revision": group.membership_revision})
    return {"version": VERSION, "flows": flows, "coverage": dict(data["coverage"]),
            "unassigned": [], "routine_confirmations": 0, "corrections": []}
