"""Independent experimental assessment; answer keys never reach extraction."""

from __future__ import annotations

from collections import Counter, defaultdict

from .work_reconstruction import (
    VERSION, bounded_list, digest, identifier, metadata_baseline, metadata_view, normalized,
    reconstruct, require, validate_snapshot,
)


def ratio(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator}


def inside(member, span):
    return (member["record_key"] == span["record_key"] and
            member["start"] >= span["start"] and member["end"] <= span["end"])


def validate_expectations(expected, data=None):
    require(isinstance(expected, dict) and expected.get("version") == 1)
    require(set(expected) <= {"version", "snapshot_digest", "groups", "negative", "unresolved"})
    groups = bounded_list(expected.get("groups"), 100)
    require(type(expected.get("unresolved")) is int and expected["unresolved"] >= 0)
    ids = set()
    records = {r["key"]: r for r in data["records"]} if data is not None else None
    for group in groups:
        require(isinstance(group, dict) and set(group) <= {"key", "subject", "change", "completion", "members", "acceptable_labels"})
        gid = identifier(group.get("key")); require(gid not in ids); ids.add(gid)
        identifier(group.get("subject")); identifier(group.get("change"))
        require(group.get("completion") is None or isinstance(group["completion"], str))
        labels = group.get("acceptable_labels")
        require(labels is None or isinstance(labels, list) and len(labels) <= 20 and
                all(isinstance(label, str) and 0 < len(label) <= 500 for label in labels))
        bounded_list(group.get("members"), 12060)
    negative = bounded_list(expected.get("negative"), 12060)
    for spans in [g["members"] for g in groups] + [negative]:
        unique = set()
        for span in spans:
            require(isinstance(span, dict) and set(span) == {"record_key", "start", "end"})
            identifier(span["record_key"])
            require(type(span["start"]) is int and type(span["end"]) is int and 0 <= span["start"] < span["end"])
            value = (span["record_key"], span["start"], span["end"])
            require(value not in unique); unique.add(value)
            if records is not None:
                row = records.get(span["record_key"])
                require(row is not None and row["offset"] <= span["start"] < span["end"] <= row["offset"] + len(row["text"]))
    positives = defaultdict(list)
    for group in groups:
        for span in group["members"]:
            positives[span["record_key"]].append(span)
    for span in negative:
        require(not any(max(span["start"], other["start"]) < min(span["end"], other["end"])
                        for other in positives[span["record_key"]]), "CONTRADICTORY_EXPECTATIONS")
    if data is not None:
        require(expected.get("snapshot_digest") == digest(data), "SNAPSHOT_CHANGED")
    return expected


def score(output, expected):
    validate_expectations(expected)
    groups = expected["groups"]
    matches, flow_errors, matched_members = defaultdict(list), Counter(), defaultdict(set)
    wrong = unknown = total = incompatible_merges = 0
    flow_ids = set()
    for flow in output["flows"]:
        require(flow["flow_id"] not in flow_ids, "DUPLICATE_OUTPUT"); flow_ids.add(flow["flow_id"])
        unique_members = set()
        compatible = [g for g in groups if normalized(g["subject"]) == flow.get("subject") and
                      g["change"] == flow.get("change") and
                      (normalized(g["completion"]) if g.get("completion") else None) == flow.get("completion")]
        support = Counter()
        wrong_owners = set()
        for member in flow["members"]:
            identity = (member["record_key"], member["start"], member["end"])
            require(identity not in unique_members, "DUPLICATE_OUTPUT"); unique_members.add(identity)
            total += 1
            owners = {g["key"] for g in groups if any(inside(member, s) for s in g["members"])}
            supported = owners & {g["key"] for g in compatible}
            if supported:
                for owner in supported:
                    support[owner] += 1
                    matched_members[owner].add((member["record_key"], member["start"], member["end"]))
            elif owners or any(inside(member, s) for s in expected["negative"]):
                wrong += 1; flow_errors[flow["flow_id"]] += 1
                wrong_owners.update(owners)
            else:
                unknown += 1; flow_errors[flow["flow_id"]] += 1
        # A mixed incompatible group cannot count as two recovered outcomes.
        if len(support) == 1:
            matches[next(iter(support))].append(flow)
        if support and wrong_owners - set(support):
            incompatible_merges += 1
    recovered = [g for g in groups if matches[g["key"]] and matched_members[g["key"]]]
    excess = sum(max(0, len(matches[g["key"]]) - 1) for g in groups)
    known_ids = {f["flow_id"] for values in matches.values() for f in values}
    unsupported = sum(f["flow_id"] not in known_ids for f in output["flows"])
    correction_free = unassessed_labels = 0
    for group in recovered:
        flows = matches[group["key"]]
        labels = group.get("acceptable_labels")
        if labels is None:
            unassessed_labels += 1
        elif len(flows) == 1 and not flow_errors[flows[0]["flow_id"]] and flows[0].get("label") in labels:
            # Missing expected contribution is a required assignment correction.
            members = flows[0]["members"]
            if all(any(inside(m, span) for m in members) for span in group["members"]):
                correction_free += 1
    coverage = output["coverage"]["complete"] and not expected["unresolved"] and not unknown and not unassessed_labels
    gates = {
        "goal_coverage": bool(groups) and len(recovered) * 100 >= len(groups) * 80,
        "incorrect_membership": total > 0 and wrong * 100 <= total * 10,
        "fragmentation": bool(recovered) and (excess + unsupported) * 10 <= len(recovered),
        "incompatible_outcomes": incompatible_merges == 0,
        "correction_free": bool(recovered) and correction_free * 100 >= len(recovered) * 90,
        "routine_intervention": output["routine_confirmations"] == 0,
    }
    return {"goal_coverage": ratio(len(recovered), len(groups)), "incorrect_membership": ratio(wrong, total),
            "correction_free": ratio(correction_free, len(recovered)), "excess_groups": excess,
            "unsupported_groups": unsupported, "actual_groups": len(output["flows"]),
            "incompatible_outcome_merges": incompatible_merges,
            "unassessed_assignments": unknown, "unassessed_corrections": unassessed_labels,
            "unresolved_expectations": expected["unresolved"], "gates": gates,
            "coverage": "complete" if coverage else "partial",
            "quality": "insufficient" if not coverage or not groups or not total else
                       "pass" if all(gates.values()) else "fail"}


def stability(before, after):
    old_ids = {f["flow_id"] for f in before["flows"]}
    new_ids = {f["flow_id"] for f in after["flows"]}
    def assignments(value):
        return {(m["statement_key"], f["flow_id"]) for f in value["flows"] for m in f["members"]}
    old, new = assignments(before), assignments(after)
    old_labels = {f["flow_id"]: f.get("label") for f in before["flows"]}
    new_labels = {f["flow_id"]: f.get("label") for f in after["flows"]}
    return {"identities": ratio(len(old_ids & new_ids), len(old_ids)),
            "assignments": ratio(len(old & new), len(old)),
            "removed_identities": len(old_ids - new_ids), "added_identities": len(new_ids - old_ids),
            "label_changes": sum(old_labels[i] != new_labels[i] for i in old_ids & new_ids)}


def compare_snapshot(data, expectations):
    validate_snapshot(data); validate_expectations(expectations, data)
    text = reconstruct(data)
    baseline = metadata_baseline(metadata_view(data))
    no_org = reconstruct(data, include_organization=False)
    baseline_no_org = metadata_baseline(metadata_view(data), include_organization=False)
    return {"version": VERSION, "snapshot_digest": digest(data), "expectations_digest": digest(expectations),
            "text": text, "metadata": baseline, "text_without_organization": no_org,
            "metadata_without_organization": baseline_no_org, "text_scores": score(text, expectations),
            "metadata_scores": score(baseline, expectations), "text_without_organization_scores": score(no_org, expectations),
            "metadata_without_organization_scores": score(baseline_no_org, expectations),
            "deterministic": text == reconstruct(data), "viability": "unverified"}
