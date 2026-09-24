"""Pure projection of supplied synthetic claims; no extraction or durable authority.

Source wording, its interpretation, target binding and reported state are distinct.
Literal validation never certifies semantic entailment. See the source-claims-and-
work-state contract; no application/DB/model consumer is registered here.
"""

import hashlib
import json
import re
from datetime import datetime, timezone


VERSION = "localbrain.source-claim-state.v1"
PRODUCER = "synthetic-supplied.v1"
MODEL_VERSION = "localbrain.source-claim-state.v2"
LIMITS = {"records": 128, "anchors": 512, "claims": 256, "targets": 64,
          "bindings": 512, "links": 512, "coverage": 512, "gaps": 128}
DISPOSITIONS = {"supported", "unresolved", "contradicted"}
STATUSES = {"pending", "completed", "cancelled"}
GAP_REASONS = {"source-removed", "source-revised", "binding-withdrawn",
               "unresolved-identity", "unresolved-time", "unresolved-content"}


class WorkStateError(ValueError):
    """A fixed, content-free contract diagnostic."""


def _require(condition, code="INVALID_PACKET"):
    if not condition:
        raise WorkStateError(code)


def _shape(value, fields):
    _require(type(value) is dict and set(value) == set(fields.split()))


def _text(value, limit=128):
    _require(type(value) is str and 0 < len(value) <= limit and bool(value.strip()))
    return value


def _enum(value, choices):
    _require(type(value) is str and value in choices)
    return value


def _integer(value):
    _require(type(value) is int and value >= 0)
    return value


def _refs(value, owner=None, nonempty=False):
    _require(type(value) is list and int(nonempty) <= len(value) <= 32)
    for item in value:
        _text(item)
    _require(len(set(value)) == len(value), "DUPLICATE_REFERENCE")
    if owner is not None:
        _require(all(item in owner for item in value), "MISSING_REFERENCE")
    return sorted(value)


def _time(value):
    if value is None:
        return None
    _require(type(value) is str and len(value) <= 40 and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", value), "INVALID_TIME")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except (ValueError, OverflowError):
        raise WorkStateError("INVALID_TIME") from None


def _instant(value):
    return datetime.fromisoformat(value) if value is not None else None


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _digest(value):
    try:
        return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()
    except (UnicodeError, ValueError, RecursionError):
        raise WorkStateError("INVALID_PACKET") from None


def text_revision(text):
    """Content revision, not work status or a whole-corpus generation."""
    _text(text, 200000)
    try:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    except UnicodeError:
        raise WorkStateError("INVALID_TEXT") from None


def anchor_key(record, start, end):
    """Stable source-native span identity; local packet aliases are irrelevant."""
    _require(type(record) is dict)
    values = [_text(record.get(k)) for k in ("source", "session", "native_id", "revision", "role", "speaker")]
    _integer(start); _integer(end)
    _require(start < end, "INVALID_ANCHOR")
    return "anchor:" + _digest([VERSION, *values, start, end])


def _effective(value):
    _shape(value, "mode start end evidence")
    mode = _enum(value["mode"], {"assertion", "explicit", "unknown"})
    evidence = _refs(value["evidence"])
    start, end = _time(value["start"]), _time(value["end"])
    if mode == "explicit":
        _require(start is not None and end is not None and _instant(start) <= _instant(end)
                 and evidence, "INVALID_TIME")
    else:
        _require(start is None and end is None and not evidence, "INVALID_TIME")
    return {"mode": mode, "start": start, "end": end, "evidence": evidence}


def _claim_value(claim):
    _require(type(claim) is dict)
    _shape({k: v for k, v in claim.items() if k != "id"},
           "kind focus context meaning status effective")
    value = {**claim, "context": _refs(claim["context"]), "effective": _effective(claim["effective"])}
    value.pop("id", None)
    for field in ("kind", "focus"):
        _text(value[field])
    _text(value["meaning"], 1000)
    _require(value["status"] is None or type(value["status"]) is str)
    return value


def claim_key(claim):
    """The unchanged v1 synthetic interpretation identity."""
    return "claim:" + _digest([VERSION, PRODUCER, _claim_value(claim)])


def _producer(value):
    _shape(value, "kind model revision assets runtime generation extraction binding adapter")
    _require(value["kind"] == "local-model", "INVALID_PRODUCER")
    for field in value:
        _text(value[field], 256)
    for field in ("assets", "runtime", "generation", "extraction", "binding"):
        _require(re.fullmatch(r"[0-9a-f]{64}", value[field]) is not None, "INVALID_PRODUCER")
    return dict(value)


def _origin(value):
    _shape(value, "basis intent premises")
    _enum(value["basis"], {"source", "opens-obligation", "fulfills-obligation"})
    _require(value["intent"] is None or (type(value["intent"]) is str and value["intent"] in {"goal", "step"}))
    _refs(value["premises"])
    if value["basis"] == "source":
        _require(not value["premises"], "INVALID_DERIVATION")
    else:
        _require(value["intent"] is None and len(value["premises"]) == (
            1 if value["basis"] == "opens-obligation" else 2), "INVALID_DERIVATION")
    return {**value, "premises": list(value["premises"])}


def model_claim_key(claim, producer, interpretation):
    """Model-aware identity; native anchors deliberately retain their v1 keys."""
    return "claim:" + _digest([MODEL_VERSION, _producer(producer),
                               _claim_value(claim), _origin(interpretation)])


def model_edge_key(edge, producer, kind):
    _enum(kind, {"binding", "link"})
    value = {k: v for k, v in edge.items() if k != "id"}
    value["evidence"] = _refs(value.get("evidence"), nonempty=True)
    if kind == "binding" and value.get("continuation") is not None:
        proof = value["continuation"]
        _shape(proof, "left right_link")
        value["continuation"] = {**proof, "left": _refs(proof["left"], nonempty=True)}
    return kind + ":" + _digest([MODEL_VERSION, _producer(producer), value])


def _bounded_copy(packet):
    # Reject depth, cycles, unsupported types and large collections before JSON
    # serialization. The visit cap also bounds multiply aliased Python inputs.
    queue, count = [(packet, 0)], 0
    while queue:
        value, depth = queue.pop()
        count += 1
        _require(depth <= 12 and count <= 40000, "PACKET_LIMIT")
        if type(value) is dict:
            _require(len(value) <= 32 and all(type(k) is str and len(k) <= 128 for k in value), "INVALID_PACKET")
            queue.extend((v, depth + 1) for v in value.values())
        elif type(value) is list:
            _require(len(value) <= 512, "PACKET_LIMIT")
            queue.extend((v, depth + 1) for v in value)
        elif type(value) is str:
            _require(len(value) <= 200000, "PACKET_LIMIT")
        else:
            _require(value is None or type(value) in (bool, int), "INVALID_PACKET")
            if type(value) is int:
                _require(abs(value) <= 2 ** 63 - 1, "INVALID_PACKET")
    try:
        raw = _json(packet)
        _require(len(raw.encode("utf-8")) <= 2000000, "PACKET_LIMIT")
        return json.loads(raw)
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, WorkStateError):
            raise
        raise WorkStateError("INVALID_PACKET") from None


def _index(items):
    result = {}
    for item in items:
        _require(type(item) is dict)
        key = _text(item.get("id"))
        _require(key not in result, "DUPLICATE_ID")
        result[key] = item
    return result


def _reach(nodes, edges):
    """Deterministic DAG transitive closure with no recursion or wall clock."""
    children, indegree = {n: set() for n in nodes}, {n: 0 for n in nodes}
    for first, last in set(edges):
        _require(first in children and last in children, "MISSING_REFERENCE")
        children[first].add(last)
        indegree[last] += 1
    ready, order = sorted(n for n in nodes if indegree[n] == 0), []
    while ready:
        node = ready.pop()
        order.append(node)
        for child in sorted(children[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    _require(len(order) == len(nodes), "CYCLIC_REFERENCE")
    reach = {n: set() for n in nodes}
    for node in reversed(order):
        for child in children[node]:
            reach[node].add(child)
            reach[node].update(reach[child])
    return reach, order


def _validate(packet, *, version=VERSION, producer=None, origins=None):
    p = _bounded_copy(packet)
    _shape(p, "version snapshot records anchors claims targets bindings links coverage gaps")
    _require(p["version"] == version, "VERSION_MISMATCH")
    _shape(p["snapshot"], "id cutoff_at complete")
    _text(p["snapshot"]["id"])
    p["snapshot"]["cutoff_at"] = _time(p["snapshot"]["cutoff_at"])
    _require(type(p["snapshot"]["complete"]) is bool)
    for name, limit in LIMITS.items():
        _require(type(p[name]) is list and len(p[name]) <= limit, "PACKET_LIMIT")
    indexes = {name: _index(p[name]) for name in LIMITS if name != "coverage"}
    records, anchors, claims, targets = (indexes[n] for n in ("records", "anchors", "claims", "targets"))
    native, sequences, total = set(), set(), 0
    for r in records.values():
        _shape(r, "id source session native_id revision text role speaker sequence asserted_at ingested_at")
        for name in ("source", "session", "native_id", "speaker"):
            _text(r[name])
        _enum(r["role"], {"user", "assistant"})
        _integer(r["sequence"])
        _require(r["revision"] == text_revision(r["text"]), "REVISION_MISMATCH")
        total += len(r["text"])
        key = (r["source"], r["session"], r["native_id"])
        seq = (r["source"], r["session"], r["sequence"])
        _require(key not in native and seq not in sequences, "DUPLICATE_SOURCE")
        native.add(key); sequences.add(seq)
        r["asserted_at"], r["ingested_at"] = _time(r["asserted_at"]), _time(r["ingested_at"])
    _require(total <= 200000, "PACKET_LIMIT")
    for a in anchors.values():
        _shape(a, "id record start end quote")
        _text(a["record"])
        _require(a["record"] in records, "MISSING_REFERENCE")
        r = records[a["record"]]
        _integer(a["start"]); _integer(a["end"]); _text(a["quote"], 4000)
        _require(a["start"] < a["end"] <= len(r["text"])
                 and r["text"][a["start"]:a["end"]] == a["quote"], "INVALID_ANCHOR")
        _require(a["id"] == anchor_key(r, a["start"], a["end"]), "IDENTITY_MISMATCH")
    for c in claims.values():
        _shape(c, "id kind focus context meaning status effective")
        _enum(c["kind"], {"intention", "action", "outcome", "state", "retraction"})
        _text(c["focus"]); _text(c["meaning"], 1000)
        _require(c["focus"] in anchors, "MISSING_REFERENCE")
        c["context"] = _refs(c["context"], anchors)
        _require(c["focus"] not in c["context"], "DUPLICATE_REFERENCE")
        if c["kind"] == "state":
            _enum(c["status"], STATUSES)
        else:
            _require(c["status"] is None, "INVALID_STATUS")
        c["effective"] = _effective(c["effective"])
        _require(set(c["effective"]["evidence"]) <= {c["focus"], *c["context"]}, "INVALID_TIME_EVIDENCE")
        expected_id = claim_key(c) if origins is None else model_claim_key(c, producer, origins[c["id"]])
        _require(c["id"] == expected_id, "IDENTITY_MISMATCH")
    for t in targets.values():
        _shape(t, "id kind parent label anchors")
        _enum(t["kind"], {"effort", "step", "occurrence"}); _text(t["label"], 1000)
        t["anchors"] = _refs(t["anchors"], anchors, True)
        if t["parent"] is not None:
            _text(t["parent"])
            _require(t["parent"] in targets, "MISSING_REFERENCE")
    _reach(targets, [(t["parent"], t["id"]) for t in targets.values() if t["parent"] is not None])
    direct = {}
    for b in indexes["bindings"].values():
        _shape(b, "id claim target relation disposition evidence continuation")
        _text(b["claim"]); _text(b["target"])
        _require(b["claim"] in claims and b["target"] in targets, "MISSING_REFERENCE")
        _enum(b["relation"], {"same-target", "contributes", "related"})
        _enum(b["disposition"], DISPOSITIONS)
        b["evidence"] = _refs(b["evidence"], anchors, True)
        c, t = claims[b["claim"]], targets[b["target"]]
        _require(c["focus"] in b["evidence"] and set(t["anchors"]) & set(b["evidence"]), "INVALID_BINDING_EVIDENCE")
        origin = records[anchors[c["focus"]]["record"]]
        side = (origin["source"], origin["session"])
        cross = any((records[anchors[a]["record"]]["source"], records[anchors[a]["record"]]["session"]) != side for a in t["anchors"])
        if b["continuation"] is not None:
            proof = b["continuation"]
            _shape(proof, "left right_link")
            proof["left"] = _refs(proof["left"], anchors, True)
            _text(proof["right_link"])
            _require(set(proof["left"]) <= set(t["anchors"]) & set(b["evidence"])
                     and proof["right_link"] in b["evidence"], "INVALID_CONTINUATION")
            right = records[anchors[proof["right_link"]]["record"]]
            _require((right["source"], right["session"]) == side, "INVALID_CONTINUATION")
            if cross:
                _require(any((records[anchors[a]["record"]]["source"],
                              records[anchors[a]["record"]]["session"]) != side
                             for a in proof["left"]), "INVALID_CONTINUATION")
        if b["relation"] == "same-target" and b["disposition"] == "supported":
            _require(not cross or b["continuation"] is not None, "MISSING_CONTINUATION")
            _require(c["id"] not in direct, "AMBIGUOUS_BINDING")
            direct[c["id"]] = t["id"]
    for link in indexes["links"].values():
        _shape(link, "id before after kind disposition evidence")
        _text(link["before"]); _text(link["after"])
        _require(link["before"] in claims and link["after"] in claims, "MISSING_REFERENCE")
        _enum(link["kind"], {"before", "reopens", "corrects", "retracts"})
        _enum(link["disposition"], DISPOSITIONS)
        link["evidence"] = _refs(link["evidence"], anchors, True)
        first, last = claims[link["before"]], claims[link["after"]]
        _require({first["focus"], last["focus"]} <= set(link["evidence"]), "INVALID_LINK_EVIDENCE")
        if link["kind"] == "reopens":
            _require(first["status"] in {"completed", "cancelled"} and last["status"] == "pending", "INVALID_TRANSITION")
        if link["kind"] == "retracts":
            _require(last["kind"] == "retraction", "INVALID_TRANSITION")
    _reach(claims, [(v["before"], v["after"]) for v in p["links"]])
    covered = {key: [] for key in records}
    accounted = set()
    for segment in p["coverage"]:
        _shape(segment, "record start end disposition claims")
        _text(segment["record"])
        _require(segment["record"] in records, "MISSING_REFERENCE")
        _integer(segment["start"]); _integer(segment["end"])
        _require(segment["start"] < segment["end"] <= len(records[segment["record"]]["text"]), "INVALID_COVERAGE")
        _enum(segment["disposition"], {"claims", "no-work", "unresolved"})
        segment["claims"] = _refs(segment["claims"], claims)
        expected = {c["id"] for c in claims.values() if anchors[c["focus"]]["record"] == segment["record"]
                    and segment["start"] <= anchors[c["focus"]]["start"] < anchors[c["focus"]]["end"] <= segment["end"]}
        _require(set(segment["claims"]) == expected and bool(expected) == (segment["disposition"] == "claims"), "INVALID_COVERAGE")
        accounted.update(expected)
        covered[segment["record"]].append((segment["start"], segment["end"]))
    _require(accounted == set(claims), "INVALID_COVERAGE")
    for key, intervals in covered.items():
        cursor = 0
        for start, end in sorted(intervals):
            _require(start == cursor, "INVALID_COVERAGE")
            cursor = end
        _require(cursor == len(records[key]["text"]), "INVALID_COVERAGE")
    for gap in p["gaps"]:
        _shape(gap, "id reason targets obsolete_ids")
        _enum(gap["reason"], GAP_REASONS)
        gap["targets"] = _refs(gap["targets"], targets)
        gap["obsolete_ids"] = _refs(gap["obsolete_ids"])
    for name in LIMITS:
        p[name].sort(key=_json)
    return p, indexes


def _record(claim, records, anchors):
    return records[anchors[claim["focus"]]["record"]]


def _interval(claim, records, anchors):
    effective = claim["effective"]
    if effective["mode"] == "explicit":
        return _instant(effective["start"]), _instant(effective["end"])
    at = _record(claim, records, anchors)["asserted_at"] if effective["mode"] == "assertion" else None
    return _instant(at), _instant(at)


def _natural_order(first, last, records, anchors):
    a, b = _interval(first, records, anchors), _interval(last, records, anchors)
    date_order = -1 if a[1] and b[0] and a[1] < b[0] else 1 if b[1] and a[0] and b[1] < a[0] else 0
    left, right = _record(first, records, anchors), _record(last, records, anchors)
    sequence_order = 0
    if first["effective"]["mode"] == last["effective"]["mode"] == "assertion" and (
            left["source"], left["session"]) == (right["source"], right["session"]):
        sequence_order = -1 if left["sequence"] < right["sequence"] else 1 if left["sequence"] > right["sequence"] else 0
    if date_order and sequence_order and date_order != sequence_order:
        return None
    return date_order or sequence_order


def _project_target(target, bound, bindings, claims, records, anchors, links, cutoff, qualifications):
    ids = sorted(bound)
    edges, trace, issues, corrections, reopens = set(), [], set(qualifications), [], set()
    natural_conflict = False
    order_basis = set()
    for i, first in enumerate(ids):
        for last in ids[i + 1:]:
            order = _natural_order(claims[first], claims[last], records, anchors)
            if order is None:
                natural_conflict = True
            elif order:
                edges.add((first, last) if order == -1 else (last, first))
                left, right = (_record(claims[c], records, anchors) for c in (first, last))
                if claims[first]["effective"]["mode"] == claims[last]["effective"]["mode"] == "assertion" and (
                        left["source"], left["session"]) == (right["source"], right["session"]) and left["sequence"] != right["sequence"]:
                    order_basis.add("source-sequence")
                a, b = _interval(claims[first], records, anchors), _interval(claims[last], records, anchors)
                if (a[1] and b[0] and a[1] < b[0]) or (b[1] and a[0] and b[1] < a[0]):
                    order_basis.add("claim-time")
    for link in links:
        a, b = link["before"], link["after"]
        if a not in bound or b not in bound:
            continue
        applied = link["disposition"] == "supported"
        order = _natural_order(claims[a], claims[b], records, anchors)
        if not applied:
            issues.add("unresolved-link")
        elif order in (None, 1):
            applied = False
            natural_conflict = True
        start, _ = _interval(claims[b], records, anchors)
        if applied and cutoff and start and start > cutoff and link["kind"] != "before":
            applied = False
            issues.add("future-effective-state")
        if applied:
            if link["kind"] in {"corrects", "retracts"}:
                left, right = (_record(claims[c], records, anchors) for c in (a, b))
                if (left["source"], left["speaker"]) != (right["source"], right["speaker"]):
                    issues.add("cross-speaker-dispute")
                    applied = False
                else:
                    corrections.append((a, b))
            elif link["kind"] == "reopens":
                reopens.add((a, b))
            if applied:
                edges.add((a, b))
                order_basis.add("explicit-link")
        trace.append({"id": link["id"], "kind": link["kind"], "before": a, "after": b,
                      "applied": applied, "evidence": link["evidence"]})
    try:
        chronology, order = _reach(ids, edges)
    except WorkStateError:
        natural_conflict = True
        chronology, order = _reach(ids, [])
    if natural_conflict:
        issues.add("chronology-conflict")
        # No invented ordering when source dates and links disagree.
        chronology, order = _reach(ids, [])
        corrections, reopens = [], set()
        for item in trace:
            item["applied"] = False
    successors = {n: set() for n in ids}
    for a, b in corrections:
        successors[a].add(b)
    active = {}
    for node in reversed(order):
        active[node] = not any(active[c] for c in successors[node])
    states = []
    for key in ids:
        c = claims[key]
        start, _ = _interval(c, records, anchors)
        if active[key] and c["kind"] == "state":
            if cutoff and start and start > cutoff:
                issues.add("future-effective-state")
            else:
                states.append(key)
    transitions = []
    for a in states:
        for b in states:
            if b not in chronology[a]:
                continue
            first, last = claims[a]["status"], claims[b]["status"]
            if first == last or first == "pending" or (a, b) in reopens:
                transitions.append((a, b))
    reach, _ = _reach(states, transitions)
    frontier = sorted(key for key in states if not reach[key])
    meanings = {claims[key]["status"] for key in frontier}
    status = "unknown" if not meanings else next(iter(meanings)) if len(meanings) == 1 else "conflicted"
    if len(meanings) > 1:
        issues.add("conflicting-reports")
        if any(b not in chronology[a] and a not in chronology[b] for a in frontier for b in frontier if a != b):
            issues.add("unresolved-order")
        else:
            issues.add("unsupported-transition")
    return {**target, "state": status, "authority": "source-reported", "qualified": bool(issues),
            "qualifications": sorted(issues), "claims": ids, "frontier": frontier,
            "order_basis": sorted(order_basis), "order_withheld": natural_conflict,
            "displaced": sorted(n for n in ids if not active[n]),
            "bindings": sorted(bindings), "links": sorted(trace, key=lambda x: x["id"])}


def project_work_state(packet):
    """Return reported state for supplied semantics, never inferred source truth."""
    p, indexes = _validate(packet)
    return _project_validated(p, indexes)


def project_model_work_state(packet):
    """Validate v2 lineage/effects, then use exactly the v1 state algorithm."""
    p = _bounded_copy(packet)
    _shape(p, "version snapshot records anchors claims targets bindings links coverage gaps producer interpretations")
    _require(p["version"] == MODEL_VERSION, "VERSION_MISMATCH")
    producer = _producer(p.pop("producer"))
    annotations = p.pop("interpretations")
    _require(type(annotations) is list and len(annotations) <= LIMITS["claims"], "PACKET_LIMIT")
    origins = {}
    for item in annotations:
        _shape(item, "claim basis intent premises")
        key = _text(item["claim"])
        _require(key not in origins, "DUPLICATE_ID")
        origins[key] = _origin({k: v for k, v in item.items() if k != "claim"})
    _require(type(p["claims"]) is list, "INVALID_PACKET")
    claims = _index(p["claims"])
    _require(set(origins) == set(claims), "MISSING_INTERPRETATION")
    p, indexes = _validate(p, version=MODEL_VERSION, producer=producer, origins=origins)
    claims, targets = indexes["claims"], indexes["targets"]
    direct = {b["claim"]: b["target"] for b in p["bindings"]
              if b["relation"] == "same-target" and b["disposition"] == "supported"}
    for name, kind in (("bindings", "binding"), ("links", "link")):
        for edge in p[name]:
            _require(edge["id"] == model_edge_key(edge, producer, kind), "IDENTITY_MISMATCH")
    for key, origin in origins.items():
        c = claims[key]
        if origin["basis"] == "source":
            _require((c["kind"] == "intention") == (origin["intent"] is not None), "INVALID_DERIVATION")
            continue
        _refs(origin["premises"], claims, True)
        premises = [claims[n] for n in origin["premises"]]
        _require(all(origins[n]["basis"] == "source" for n in origin["premises"]), "INVALID_DERIVATION")
        first, focus = premises[0], premises[-1]
        is_step = first["kind"] == "intention" and origins[first["id"]]["intent"] == "step"
        opening = origin["basis"] == "opens-obligation"
        _require(is_step or (not opening and first["kind"] == "state" and first["status"] == "pending"),
                 "INVALID_DERIVATION")
        _require(opening or focus["kind"] in {"action", "outcome"}, "INVALID_DERIVATION")
        _require(c["kind"] == "state" and c["status"] == ("pending" if opening else "completed")
                 and c["focus"] == focus["focus"] and c["effective"] == focus["effective"], "INVALID_DERIVATION")
        support = {a for claim in premises for a in [claim["focus"], *claim["context"]]}
        _require(support <= {c["focus"], *c["context"]}, "INVALID_DERIVATION")
        target = direct.get(key)
        _require(target is not None and targets[target]["kind"] in {"step", "occurrence"}
                 and all(direct.get(n) == target for n in origin["premises"]), "INVALID_DERIVATION")
    return _project_validated(p, indexes, version=MODEL_VERSION, producer=producer, origins=origins)


def _project_validated(p, indexes, *, version=VERSION, producer=PRODUCER, origins=None):
    records, anchors, all_claims, all_targets = (indexes[n] for n in ("records", "anchors", "claims", "targets"))
    cutoff = _instant(p["snapshot"]["cutoff_at"])
    visible_records = {k for k, r in records.items() if not cutoff or (
        r["asserted_at"] is not None and _instant(r["asserted_at"]) <= cutoff)}
    visible_anchors = {k for k, a in anchors.items() if a["record"] in visible_records}
    claims = {k: c for k, c in all_claims.items() if {c["focus"], *c["context"]} <= visible_anchors}
    targets = {k: t for k, t in all_targets.items() if set(t["anchors"]) <= visible_anchors}
    bindings = [b for b in p["bindings"] if b["claim"] in claims and b["target"] in targets
                and set(b["evidence"]) <= visible_anchors]
    links = [v for v in p["links"] if v["before"] in claims and v["after"] in claims
             and set(v["evidence"]) <= visible_anchors]
    bound = {k: set() for k in targets}
    binding_ids, reasons = {k: set() for k in targets}, {k: set() for k in targets}
    global_reasons = set()
    if not p["snapshot"]["complete"]:
        global_reasons.add("incomplete-snapshot")
    if cutoff and any(r["asserted_at"] is None for r in records.values()):
        global_reasons.add("unknown-cutoff-time")
    if any(c["focus"] in visible_anchors and c["id"] not in claims for c in all_claims.values()):
        global_reasons.add("withheld-interpretation")
    for gap in p["gaps"]:
        if gap["targets"]:
            for key in set(gap["targets"]) & set(targets):
                reasons[key].add(gap["reason"])
        else:
            global_reasons.add(gap["reason"])
    for s in p["coverage"]:
        if s["record"] in visible_records and s["disposition"] == "unresolved":
            global_reasons.add("unresolved-content")
    for b in bindings:
        binding_ids[b["target"]].add(b["id"])
        if b["relation"] == "same-target" and b["disposition"] == "supported":
            bound[b["target"]].add(b["claim"])
        elif b["disposition"] != "supported" and claims[b["claim"]]["kind"] == "state":
            reasons[b["target"]].add("unresolved-binding")
    assigned = set().union(*bound.values()) if bound else set()
    unassigned = sorted(set(claims) - assigned)
    if any(claims[c]["kind"] == "state" for c in unassigned):
        global_reasons.add("unbound-state")
    if any(claims[c]["kind"] == "retraction" for c in unassigned):
        global_reasons.add("unbound-retraction")
    direct_targets = {c: target for target, members in bound.items() for c in members}
    for link in links:
        if link["kind"] != "before" and (link["before"] not in direct_targets
                or link["after"] not in direct_targets
                or direct_targets[link["before"]] != direct_targets[link["after"]]):
            affected = {direct_targets[c] for c in (link["before"], link["after"]) if c in direct_targets}
            for target in affected:
                reasons[target].add("unresolved-link-scope")
            if not affected:
                global_reasons.add("unresolved-link-scope")
    # Withheld bindings/links must not silently leave an apparently complete view.
    for b in p["bindings"]:
        if b not in bindings and b["claim"] in claims and b["target"] in targets:
            reasons[b["target"]].add("withheld-binding")
    for link in p["links"]:
        if link not in links and link["before"] in claims and link["after"] in claims:
            global_reasons.add("withheld-link")
    views = []
    for key in sorted(targets):
        target = {**targets[key]}
        if target["parent"] is not None and target["parent"] not in targets:
            target["parent"] = None
            reasons[key].add("unresolved-parent")
        views.append(_project_target(target, bound[key], binding_ids[key], claims, records,
                                     anchors, links, cutoff, reasons[key] | global_reasons))
    history = []
    for key in sorted(claims):
        c = claims[key]
        r = _record(c, records, anchors)
        history.append({**c, "role": r["role"], "speaker": r["speaker"],
                        "asserted_at": r["asserted_at"], "authority": "source-attributed",
                        "producer": producer})
        if origins is not None:
            history[-1]["interpretation"] = origins[key]
            if origins[key]["basis"] != "source":
                history[-1]["authority"] = "model-inferred"
    source_anchors = [{**anchors[a], "source": records[anchors[a]["record"]]["source"],
                       "session": records[anchors[a]["record"]]["session"],
                       "native_id": records[anchors[a]["record"]]["native_id"],
                       "role": records[anchors[a]["record"]]["role"],
                       "speaker": records[anchors[a]["record"]]["speaker"],
                       "sequence": records[anchors[a]["record"]]["sequence"],
                       "asserted_at": records[anchors[a]["record"]]["asserted_at"],
                       "revision": records[anchors[a]["record"]]["revision"]} for a in sorted(visible_anchors)]
    semantic = {**p, "records": sorted(({k: v for k, v in r.items() if k != "ingested_at"}
                                       for r in records.values()), key=_json)}
    if origins is not None:
        semantic.update(producer=producer, interpretations=origins)
    result = {"version": version, "producer": producer, "snapshot": p["snapshot"],
              "authority": "source-reported", "model_admission": False, "input_digest": _digest(semantic),
              "targets": views, "history": history, "anchors": source_anchors,
              "unassigned_claims": unassigned, "bindings": bindings, "links": links, "gaps": p["gaps"],
              "coverage": {"records": len(records), "visible_records": len(visible_records),
                           "withheld_records": len(records) - len(visible_records),
                           "withheld_claims": len(all_claims) - len(claims),
                           "withheld_targets": len(all_targets) - len(targets),
                           "segments": [s for s in p["coverage"] if s["record"] in visible_records],
                           "qualifications": sorted(global_reasons)}}
    # A visible coverage segment can reference a claim withheld due to later context.
    for segment in result["coverage"]["segments"]:
        hidden = set(segment["claims"]) - set(claims)
        segment["claims"] = sorted(set(segment["claims"]) & set(claims))
        segment["withheld_claim_count"] = len(hidden)
    result["digest"] = _digest(result)
    return result
