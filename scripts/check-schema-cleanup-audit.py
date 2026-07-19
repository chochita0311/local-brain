#!/usr/bin/env python3
"""Validate and render the FEAT-0029 schema cleanup decision ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "src/localbrain/schema-presentation.json"
DEFAULT_DECISIONS = ROOT / "docs/plans/evaluation/audit-0029-schema-decisions.json"
DEFAULT_LEDGER = ROOT / "docs/plans/evaluation/audit-0029-schema-object-ledger.md"
VALID_DECISIONS = {"keep", "change", "remove", "defer"}
VALID_RISKS = {"low", "medium", "high"}
CANDIDATE_FIELDS = {
    "disposition",
    "defect",
    "desired_contract",
    "objects",
    "consumers",
    "dependency",
    "preservation",
    "rollback_or_recovery",
    "verification",
    "risk",
}


class AuditError(RuntimeError):
    pass


def _no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AuditError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_object
        )
    except (OSError, json.JSONDecodeError) as error:
        raise AuditError(f"cannot read {path.relative_to(ROOT)}: {error}") from error
    if not isinstance(value, dict):
        raise AuditError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def physical_relation_id(relation: dict[str, Any]) -> str:
    source_columns = ",".join(relation["source_columns"])
    target_columns = ",".join(relation["target_columns"])
    return (
        f'{relation["source_table"]}({source_columns})->'
        f'{relation["target_table"]}({target_columns})'
    )


def application_relation_id(relation: dict[str, Any]) -> str:
    return (
        f'{relation["source_table"]}->{relation["target_table"]}'
        f' [{relation["label"]}]'
    )


def _validate_decision(
    object_id: str,
    decision: dict[str, Any],
    candidates: dict[str, Any],
    defers: dict[str, Any],
) -> None:
    disposition = decision.get("decision")
    if disposition not in VALID_DECISIONS:
        raise AuditError(f"{object_id}: invalid decision {disposition!r}")
    if decision.get("risk") not in VALID_RISKS:
        raise AuditError(f"{object_id}: invalid or missing risk")
    if not isinstance(decision.get("rationale"), str) or not decision["rationale"].strip():
        raise AuditError(f"{object_id}: missing rationale")
    if disposition in {"change", "remove"}:
        candidate = decision.get("candidate")
        if candidate not in candidates:
            raise AuditError(f"{object_id}: missing candidate group")
    elif "candidate" in decision:
        raise AuditError(f"{object_id}: candidate is valid only for change/remove")
    if disposition == "defer":
        defer = decision.get("defer")
        if defer not in defers:
            raise AuditError(f"{object_id}: missing defer group")
    elif "defer" in decision:
        raise AuditError(f"{object_id}: defer group is valid only for defer")


def _resolve_objects(
    manifest: dict[str, Any], decisions: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    candidates = decisions.get("candidate_groups", {})
    defers = decisions.get("defer_groups", {})
    defaults = decisions.get("decision_defaults", {})
    table_decisions = decisions.get("table_decisions", {})
    column_overrides = decisions.get("column_overrides", {})
    index_overrides = decisions.get("index_overrides", {})
    physical_overrides = decisions.get("physical_relation_overrides", {})
    application_overrides = decisions.get("application_relation_overrides", {})

    tables = manifest.get("tables", [])
    table_by_id = {table["id"]: table for table in tables}
    if len(table_by_id) != len(tables):
        raise AuditError("manifest contains duplicate table IDs")
    if set(table_decisions) != set(table_by_id):
        missing = sorted(set(table_by_id) - set(table_decisions))
        extra = sorted(set(table_decisions) - set(table_by_id))
        raise AuditError(f"table decision parity failed; missing={missing}, extra={extra}")

    column_ids = {
        f'{table["id"]}.{column["name"]}'
        for table in tables
        for column in table["columns"]
    }
    index_ids = {
        f'{table["id"]}.{index["name"]}'
        for table in tables
        for index in table["indexes"]
    }
    physical_ids = {
        physical_relation_id(relation)
        for relation in manifest["relationships"]["physical"]
    }
    application_ids = {
        application_relation_id(relation)
        for relation in manifest["relationships"]["application"]
    }
    for label, overrides, valid_ids in (
        ("column", column_overrides, column_ids),
        ("index", index_overrides, index_ids),
        ("physical relation", physical_overrides, physical_ids),
        ("application relation", application_overrides, application_ids),
    ):
        extra = sorted(set(overrides) - valid_ids)
        if extra:
            raise AuditError(f"unknown {label} overrides: {extra}")

    resolved: list[dict[str, Any]] = []
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for table in tables:
        table_id = table["id"]
        evidence_by_id[table_id] = table
        decision = table_decisions[table_id]
        _validate_decision(f"table:{table_id}", decision, candidates, defers)
        resolved.append(
            {
                "kind": "table",
                "id": table_id,
                "table": table_id,
                "subject": table["subject_id"],
                **decision,
            }
        )
        for column in table["columns"]:
            column_id = f'{table_id}.{column["name"]}'
            decision = column_overrides.get(column_id, defaults.get("column"))
            if not isinstance(decision, dict):
                raise AuditError(f"column:{column_id}: missing decision/default")
            _validate_decision(f"column:{column_id}", decision, candidates, defers)
            resolved.append(
                {
                    "kind": "column",
                    "id": column_id,
                    "table": table_id,
                    "subject": table["subject_id"],
                    "contract": column["semantic_contract"],
                    **decision,
                }
            )
        for index in table["indexes"]:
            index_id = f'{table_id}.{index["name"]}'
            decision = index_overrides.get(index_id, defaults.get("index"))
            if not isinstance(decision, dict):
                raise AuditError(f"index:{index_id}: missing decision/default")
            _validate_decision(f"index:{index_id}", decision, candidates, defers)
            resolved.append(
                {
                    "kind": "index",
                    "id": index_id,
                    "table": table_id,
                    "subject": table["subject_id"],
                    "contract": ", ".join(
                        column["name"] + (" DESC" if column["descending"] else "")
                        for column in index["columns"]
                    ),
                    **decision,
                }
            )

    for relation in manifest["relationships"]["physical"]:
        relation_id = physical_relation_id(relation)
        table_id = relation["source_table"]
        decision = physical_overrides.get(
            relation_id, defaults.get("physical_relation")
        )
        if not isinstance(decision, dict):
            raise AuditError(f"physical_relation:{relation_id}: missing decision/default")
        _validate_decision(
            f"physical_relation:{relation_id}", decision, candidates, defers
        )
        resolved.append(
            {
                "kind": "physical relation",
                "id": relation_id,
                "table": table_id,
                "subject": table_by_id[table_id]["subject_id"],
                "contract": f'{relation["enforcement"]}; ON DELETE {relation["on_delete"]}',
                **decision,
            }
        )

    for relation in manifest["relationships"]["application"]:
        relation_id = application_relation_id(relation)
        table_id = relation["source_table"]
        decision = application_overrides.get(
            relation_id, defaults.get("application_relation")
        )
        if not isinstance(decision, dict):
            raise AuditError(f"application_relation:{relation_id}: missing decision/default")
        _validate_decision(
            f"application_relation:{relation_id}", decision, candidates, defers
        )
        resolved.append(
            {
                "kind": "application relation",
                "id": relation_id,
                "table": table_id,
                "subject": table_by_id[table_id]["subject_id"],
                "contract": relation["label"],
                **decision,
            }
        )

    identities = [(item["kind"], item["id"]) for item in resolved]
    if len(identities) != len(set(identities)):
        raise AuditError("resolved ledger contains duplicate object identities")
    return resolved, evidence_by_id


def _validate_contract(
    manifest_path: Path,
    manifest: dict[str, Any],
    decisions: dict[str, Any],
    resolved: list[dict[str, Any]],
    evidence_by_id: dict[str, dict[str, Any]],
) -> None:
    if decisions.get("schema") != "localbrain.schema-cleanup-audit.v1":
        raise AuditError("unsupported cleanup audit schema")
    if decisions.get("review_status") not in {"owner-review-required", "complete"}:
        raise AuditError("audit review_status must be owner-review-required or complete")
    manifest_contract = decisions.get("manifest", {})
    if manifest_contract.get("path") != str(manifest_path.relative_to(ROOT)):
        raise AuditError("configured manifest path does not match invocation")
    if file_sha256(manifest_path) != manifest_contract.get("sha256"):
        raise AuditError("presentation manifest digest changed; refresh the audit deliberately")
    if manifest.get("schema") != "localbrain.schema-presentation.v1":
        raise AuditError("unsupported schema presentation manifest")

    expected = manifest_contract.get("expected", {})
    actual = Counter(item["kind"] for item in resolved)
    expected_by_kind = {
        "table": expected.get("tables"),
        "column": expected.get("columns"),
        "index": expected.get("indexes"),
        "physical relation": expected.get("physical_relations"),
        "application relation": expected.get("application_relations"),
    }
    if dict(actual) != expected_by_kind:
        raise AuditError(
            f"resolved object counts changed; actual={dict(actual)}, expected={expected_by_kind}"
        )

    candidates = decisions.get("candidate_groups", {})
    for candidate_id, candidate in candidates.items():
        missing = sorted(CANDIDATE_FIELDS - set(candidate))
        if missing:
            raise AuditError(f"candidate {candidate_id}: missing fields {missing}")
        if candidate["disposition"] not in {"change", "remove"}:
            raise AuditError(f"candidate {candidate_id}: invalid disposition")
        if candidate["risk"] not in VALID_RISKS:
            raise AuditError(f"candidate {candidate_id}: invalid risk")
        for field in CANDIDATE_FIELDS - {"objects", "consumers"}:
            if not isinstance(candidate[field], str) or not candidate[field].strip():
                raise AuditError(f"candidate {candidate_id}: empty {field}")
        for field in ("objects", "consumers"):
            if not isinstance(candidate[field], list) or not candidate[field]:
                raise AuditError(f"candidate {candidate_id}: empty {field}")
    used_candidates = {
        item["candidate"] for item in resolved if item["decision"] in {"change", "remove"}
    }
    if used_candidates != set(candidates):
        raise AuditError(
            "candidate usage parity failed; "
            f"unused={sorted(set(candidates) - used_candidates)}, "
            f"unknown={sorted(used_candidates - set(candidates))}"
        )

    defers = decisions.get("defer_groups", {})
    for defer_id, defer in defers.items():
        if set(defer) != {"blocker", "backlog_anchor", "risk"}:
            raise AuditError(f"defer {defer_id}: invalid field set")
        if defer["risk"] not in VALID_RISKS:
            raise AuditError(f"defer {defer_id}: invalid risk")
        anchor = defer["backlog_anchor"]
        backlog = ROOT / "docs/plans/project/backlog.md"
        if f'<a id="{anchor}"></a>' not in backlog.read_text(encoding="utf-8"):
            raise AuditError(f"defer {defer_id}: missing canonical backlog anchor {anchor}")
    used_defers = {item["defer"] for item in resolved if item["decision"] == "defer"}
    if used_defers != set(defers):
        raise AuditError("defer group usage parity failed")

    test_evidence = decisions.get("test_evidence", {})
    if set(test_evidence) != set(evidence_by_id):
        raise AuditError("test evidence must cover every table exactly once")
    for table_id, paths in test_evidence.items():
        if not paths:
            raise AuditError(f"{table_id}: empty test evidence")
        for path in paths:
            candidate = ROOT / path
            if not candidate.is_file() or not path.startswith("tests/"):
                raise AuditError(f"{table_id}: invalid test evidence {path}")

    required_dimensions = {
        "unused_fields",
        "duplicated_facts",
        "wrong_ownership",
        "polymorphic_referential_gaps",
        "identifier_inconsistencies",
        "missing_or_redundant_indexes",
        "timestamp_inconsistency",
        "status_and_type_constraints",
        "stable_data_in_json",
        "deletion_behavior",
        "fresh_vs_compatible_drift",
    }
    dimensions = decisions.get("audit_dimensions", {})
    if set(dimensions) != required_dimensions or any(not value for value in dimensions.values()):
        raise AuditError("all required audit dimensions need non-empty findings")

    for source in manifest["baseline"]["sources"]:
        path = ROOT / source["path"]
        if file_sha256(path) != source["sha256"]:
            raise AuditError(f"manifest source digest is stale: {source['path']}")


def _runtime_references(table_id: str) -> list[str]:
    pattern = re.compile(rf"\b{re.escape(table_id)}\b")
    paths = []
    for path in sorted((ROOT / "src/localbrain").rglob("*.py")):
        if pattern.search(path.read_text(encoding="utf-8")):
            paths.append(str(path.relative_to(ROOT)))
    return paths


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _anchor(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def render_ledger(
    manifest: dict[str, Any],
    decisions: dict[str, Any],
    resolved: list[dict[str, Any]],
    evidence_by_id: dict[str, dict[str, Any]],
) -> str:
    disposition_counts = Counter(item["decision"] for item in resolved)
    kind_counts = Counter(item["kind"] for item in resolved)
    lines = [
        "# FEAT-0029 Resolved Schema Object Ledger",
        "",
        "This file is generated by `scripts/check-schema-cleanup-audit.py`. Edit the JSON decision source, not this ledger.",
        "",
        "## Boundary And Result",
        "",
        f"- Manifest: `{decisions['manifest']['path']}` (`{decisions['manifest']['sha256']}`)",
        f"- Decision source: `docs/plans/evaluation/audit-0029-schema-decisions.json`",
        (
            f"- Review state: `{decisions['review_status']}`; this ledger authorizes no migration."
            if decisions["review_status"] == "owner-review-required"
            else "- Review state: `complete`; active migration candidates are closed and residual deferrals still require separate owner approval."
        ),
        f"- Resolved objects: {len(resolved)} = {kind_counts['table']} tables + {kind_counts['column']} columns + {kind_counts['index']} explicit named indexes + {kind_counts['physical relation']} physical relations + {kind_counts['application relation']} application relations.",
        f"- Dispositions: keep {disposition_counts['keep']}, change {disposition_counts['change']}, remove {disposition_counts['remove']}, defer {disposition_counts['defer']}.",
        "- SQLite FTS shadow tables and implicit uniqueness autoindexes are implementation-owned consequences, not independent application objects. Their effects are audited through the owning virtual table/UNIQUE constraint and redundant-index findings.",
        "- Every child row inherits the complete evidence register of its `Evidence` table, while retaining an object-specific contract and rationale here.",
        "",
        "## Candidate Decision Groups",
        "",
    ]
    for candidate_id, candidate in decisions["candidate_groups"].items():
        lines.extend(
            [
                f"### {candidate_id}",
                "",
                f"- Disposition / risk: `{candidate['disposition']}` / `{candidate['risk']}`",
                f"- Defect: {candidate['defect']}",
                f"- Desired contract: {candidate['desired_contract']}",
                f"- Objects: {', '.join(f'`{item}`' for item in candidate['objects'])}",
                f"- Consumers: {'; '.join(candidate['consumers'])}",
                f"- Dependency: {candidate['dependency']}",
                f"- Preservation: {candidate['preservation']}",
                f"- Rollback or recovery: {candidate['rollback_or_recovery']}",
                f"- Verification: {candidate['verification']}",
                "",
            ]
        )

    if not decisions["candidate_groups"]:
        lines.extend(["No active change or remove candidate remains.", ""])

    lines.extend(["## Deferred Decision Groups", ""])
    for defer_id, defer in decisions["defer_groups"].items():
        lines.extend(
            [
                f"### {defer_id}",
                "",
                f"- Risk: `{defer['risk']}`",
                f"- Blocker: {defer['blocker']}",
                f"- Canonical backlog: [`{defer['backlog_anchor']}`](../project/backlog.md#{defer['backlog_anchor']})",
                "",
            ]
        )

    kind_order = ("table", "column", "index", "physical relation", "application relation")
    for kind in kind_order:
        lines.extend([f"## {kind.title()} Decisions", ""])
        lines.append("| Object | Decision | Risk | Evidence | Candidate / defer | Contract and rationale |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for item in (entry for entry in resolved if entry["kind"] == kind):
            route = item.get("candidate") or item.get("defer") or "—"
            contract = item.get("contract")
            detail = f"{contract} — {item['rationale']}" if contract else item["rationale"]
            evidence_link = f"[E-{item['table']}](#evidence-{_anchor(item['table'])})"
            lines.append(
                "| `{}` | `{}` | `{}` | {} | `{}` | {} |".format(
                    _md(item["id"]),
                    item["decision"],
                    item["risk"],
                    evidence_link,
                    route,
                    _md(detail),
                )
            )
        lines.append("")

    lines.extend(["## Evidence Register", ""])
    test_evidence = decisions["test_evidence"]
    for table_id, table in evidence_by_id.items():
        semantics = table["semantics"]
        runtime_refs = _runtime_references(table_id)
        lines.extend(
            [
                f"### Evidence: {table_id}",
                "",
                f'<a id="evidence-{_anchor(table_id)}"></a>',
                "",
                f"- Subject owner: `{table['subject_id']}`; current semantic owner: `{table['semantic_document']}`.",
                f"- Fresh / compatible source: {semantics['schema_ownership']}",
                f"- Purpose and authority: {semantics['purpose_and_authority']}",
                f"- Producers: {semantics['producers']}",
                f"- Consumers: {semantics['consumers']}",
                f"- Lifecycle: {semantics['class']} — {semantics['lifecycle_contract']}",
                f"- Rebuildability: `{semantics['rebuildability']}` — {semantics['recovery_path']}",
                f"- Deletion effect: {semantics['deletion_effect']}",
                "- Runtime references inspected: "
                + ", ".join(f"`{path}`" for path in runtime_refs)
                + ".",
                "- Synthetic tests inspected: "
                + ", ".join(f"`{path}`" for path in test_evidence[table_id])
                + ".",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    decisions_path = args.decisions.resolve()
    ledger_path = args.ledger.resolve()
    try:
        manifest = load_json(manifest_path)
        decisions = load_json(decisions_path)
        resolved, evidence_by_id = _resolve_objects(manifest, decisions)
        _validate_contract(
            manifest_path, manifest, decisions, resolved, evidence_by_id
        )
        rendered = render_ledger(manifest, decisions, resolved, evidence_by_id)
        if args.check:
            if not ledger_path.is_file() or ledger_path.read_text(encoding="utf-8") != rendered:
                raise AuditError(
                    f"{ledger_path.relative_to(ROOT)} is missing or stale; run the writer"
                )
        else:
            ledger_path.write_text(rendered, encoding="utf-8")
    except (AuditError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"schema cleanup audit failed: {error}", file=sys.stderr)
        return 1

    mode = "current" if args.check else "written"
    counts = Counter(item["decision"] for item in resolved)
    print(
        f"schema cleanup audit {mode}: {len(resolved)} objects; "
        + ", ".join(f"{key}={counts[key]}" for key in ("keep", "change", "remove", "defer"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
