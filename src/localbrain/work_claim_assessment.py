"""Frozen-reference scoring. Reference data is never part of end-to-end prompts."""

from . import work_state as state
from .work_claims import Anchors, legacy_units, records_for


def _core(text):
    return text.strip(" \t\n.,!?;:。！？")


def extraction_checks(case, extracted):
    reference = case["reference"]["extraction"]
    expected, actual = reference["claims"], extracted["wire"]["claims"]
    matches, contexts, times = {}, True, True
    # Deliberately refuse ambiguous annotation alignment; do not optimize the
    # matching to whichever downstream target assignment gives a higher score.
    for c in actual:
        candidates = [e for e in expected if e["role"] == c["role"]
                      and e["span"]["message"] == c["span"]["message"]
                      and e["span"]["occurrence"] == c["span"]["occurrence"]
                      and _core(e["span"]["quote"]) in _core(c["span"]["quote"])]
        if len(candidates) == 1:
            e = candidates[0]
            matches[c["id"]] = e["id"]
            contexts &= all(any(s["message"] == a["message"] and _core(s["quote"]) in _core(a["quote"])
                                for a in c["context"]) for s in e["context"])
            times &= c["time"] == e["time"]
    no_work = all(any(e["message"] == a["message"] and _core(e["quote"]) in _core(a["quote"])
                     for a in extracted["wire"]["no_work"]) for e in reference["no_work"])
    pool = Anchors(records_for(case))
    expected_anchors = [pool.values[pool.span(c["span"])] for c in expected]
    ignored = [pool.values[pool.span(s)] for s in extracted["wire"]["no_work"]]
    false_no_work = any(a["record"] == b["record"] and a["start"] < b["end"] and b["start"] < a["end"]
                        for a in expected_anchors for b in ignored)
    complete = set(matches.values()) == {c["id"] for c in expected}
    pure = len(matches) == len(actual) and len(set(matches.values())) == len(matches)
    return {"claim_coverage": complete, "claim_purity": pure, "context": contexts,
            "effective_time": times, "no_work_coverage": no_work, "no_false_no_work": not false_no_work}, matches


def binding_checks(case, extracted, bound):
    ref = case["reference"]["binding"]
    extraction, claim_map = extraction_checks(case, extracted)
    expected_claims = {c["id"]: c for c in case["reference"]["extraction"]["claims"]}
    p, wire = bound["packet"], bound["wire"]
    anchors = state._index(p["anchors"])
    actual_targets = state._index(p["targets"])
    target_map = {}
    for alias, key in bound["target_aliases"].items():
        t = actual_targets[key]
        candidates = []
        for expected in ref["targets"]:
            label = expected["label"]
            if label not in expected_claims:
                continue
            span = expected_claims[label]["span"]
            if expected["kind"] == t["kind"] and any(anchors[a]["record"] == span["message"]
                    and _core(span["quote"]) in _core(anchors[a]["quote"]) for a in t["anchors"]):
                candidates.append(expected["id"])
        if len(candidates) == 1:
            target_map[alias] = candidates[0]
    targets_ok = (len(target_map) == len(wire["targets"]) == len(ref["targets"])
                  and set(target_map.values()) == {t["id"] for t in ref["targets"]})
    expected_targets = {t["id"]: t for t in ref["targets"]}
    hierarchy = all(t["id"] in target_map and (
        None if t["parent"] is None else target_map.get(t["parent"], "missing")) ==
        expected_targets[target_map[t["id"]]]["parent"] for t in wire["targets"])

    def binding_signature(b, cm, tm):
        return (cm.get(b["claim"], "missing"), tm.get(b["target"], "missing"), b["relation"],
                b["disposition"], b["continuation"] is not None)
    ec = {k: k for k in expected_claims}
    et = {k: k for k in expected_targets}
    expected_bindings = {binding_signature(b, ec, et) for b in ref["bindings"]}
    actual_bindings = {binding_signature(b, claim_map, target_map) for b in wire["bindings"]}

    def effect_signature(e, cm, tm):
        return (e["kind"], cm.get(e["obligation"], "missing"),
                None if e["fulfillment"] is None else cm.get(e["fulfillment"], "missing"),
                tm.get(e["target"], "missing"), e["disposition"])
    effect_map = {}
    for e in wire["effects"]:
        candidates = [r for r in ref["effects"] if effect_signature(e, claim_map, target_map) == effect_signature(r, ec, et)]
        if len(candidates) == 1:
            effect_map[e["id"]] = candidates[0]["id"]
    effects_ok = len(effect_map) == len(wire["effects"]) == len(ref["effects"]) and len(set(effect_map.values())) == len(effect_map)
    endpoint_map = {**claim_map, **effect_map}
    expected_links = {(l["before"], l["after"], l["kind"], l["disposition"]) for l in ref["links"]}
    actual_links = {(endpoint_map.get(l["before"], "missing"), endpoint_map.get(l["after"], "missing"),
                    l["kind"], l["disposition"]) for l in wire["links"]}
    target_keys = {bound["target_aliases"][a]: e for a, e in target_map.items()}
    states = {target_keys.get(t["id"], "missing:" + t["id"]): t["state"] for t in bound["projection"]["targets"]}
    pair_ok = (bound["pair"] is None if ref["pair"] is None else
               bound["pair"] is not None and bound["pair"]["relation"] == ref["pair"]["relation"])
    safe_terminal = all(value not in {"completed", "cancelled"} or
                        case["reference"]["states"].get(key) == value for key, value in states.items())
    safe_continuation = (not bound["pair"] or bound["pair"]["relation"] != "continues" or
                         (ref["pair"] is not None and ref["pair"]["relation"] == "continues"))
    return {**extraction, "target_discovery": targets_ok, "target_hierarchy": hierarchy,
            "bindings": actual_bindings == expected_bindings and len(wire["bindings"]) == len(ref["bindings"]),
            "effects": effects_ok, "links": actual_links == expected_links and len(wire["links"]) == len(ref["links"]),
            "reported_state": states == case["reference"]["states"], "pair": pair_ok,
            "safe_terminal_scope": safe_terminal, "safe_continuation": safe_continuation}


def legacy_checks(case, bound, assess):
    if "expect" not in case:
        return {}
    result = bound["pair"] if case["kind"] == "relate" else legacy_units(bound)
    return {"legacy_" + k: v for k, v in assess(case, result).items()}


def gates(rows):
    """No denominator dropping or claim-level pseudo sample multiplication."""
    result = {}
    for split in sorted({r["split"] for r in rows}):
        result[split] = {}
        cohort = [r for r in rows if r["split"] == split]
        for stage in ("extraction", "conditioned", "end_to_end"):
            if stage != "end_to_end" and split == "holdout":
                continue
            relevant = [r for r in cohort if stage in r]
            negative = [r for r in relevant if r["negative"]]
            positive = [r for r in relevant if not r["negative"]]
            passed = lambda r: bool(r[stage]) and all(r[stage].values())
            n, p = sum(passed(r) for r in negative), sum(passed(r) for r in positive)
            safety = all(value for r in relevant for key, value in r[stage].items() if key.startswith("safe_"))
            result[split][stage] = {"negative_passed": n, "negative_total": len(negative),
                "positive_passed": p, "positive_total": len(positive),
                "safety_passed": safety,
                "passed": bool(negative and positive) and safety and n == len(negative) and p * 5 >= len(positive) * 4}
    return result
