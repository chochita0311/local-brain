"""Versioned, product-neutral guidance and finding values for personal insights."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .personal_insight_evidence import MANIFEST_VERSION


CORE_VERSION = "personal-improvement-core-v8"
REPORT_VERSION = "personal-improvement-report-v3"
LEGACY_REPORT_VERSION = "personal-improvement-report-v2"
REPORT_VERSIONS = {
    "personal-improvement-core-v2": LEGACY_REPORT_VERSION,
    "personal-improvement-core-v3": LEGACY_REPORT_VERSION,
    "personal-improvement-core-v4": REPORT_VERSION,
    "personal-improvement-core-v5": REPORT_VERSION,
    "personal-improvement-core-v6": REPORT_VERSION,
    "personal-improvement-core-v7": REPORT_VERSION,
    CORE_VERSION: REPORT_VERSION,
}
GUIDE_ROOT = Path(__file__).with_name("personal_insight_guides")

PLAYBOOK_IDS = (
    "task_framing", "request_feedback", "context_recovery", "repeatable_procedure",
    "learning_explanation", "verification_rework", "information_access", "decision_memory",
    "task_fit_effort", "personal_value", "assistant_configuration",
)
PLAYBOOK_VERSIONS = {item: "v4" if item == "request_feedback" else "v1" for item in PLAYBOOK_IDS}

HANDOFF_FIELDS = (
    "goal", "proposed_change", "scope", "constraints", "first_steps", "success_check"
)
FINDING_FIELDS = (
    "title", "type_id", "owner_goal", "pattern_scope", "observation",
    "evidence_ids", "counterevidence_ids", "counterexample_status", "counterexample_check", "alternative",
    "coverage_limit", "action", "benefit_hypothesis", "effort_or_tradeoff",
    "follow_up", "handoff", "outcome_state",
)
RESULT_FIELDS = (
    "result_version", "title", "summary", "outcome", "findings",
    "no_finding_reason", "additional_evidence", "limits",
)
REQUEST_FIELDS = ("kind", "question", "evidence_ids")


class SuppliedMessageRequestError(ValueError):
    """The model requested a message that was already supplied in full."""


def _resource(path: Path) -> tuple[str, str]:
    content = path.read_text(encoding="utf-8")
    return content, sha256(content.encode("utf-8")).hexdigest()


def _validate_manifest_scope(manifest: dict) -> None:
    scope = manifest.get("scope")
    if manifest.get("version") != MANIFEST_VERSION or not isinstance(scope, dict):
        raise ValueError("unsupported evidence manifest for improvement guidance")
    mode = scope.get("mode")
    if mode not in {"ask", "discover"}:
        raise ValueError("unsupported improvement analysis mode")
    question = scope.get("question")
    if mode == "ask" and (not isinstance(question, str) or not question.strip()):
        raise ValueError("ask guidance requires a question")
    if mode == "discover" and question is not None:
        raise ValueError("discover guidance does not accept a question")


def select_playbooks(manifest: dict) -> tuple[list[str], str]:
    """Admit the bounded catalogue; quoted vocabulary must not exclude a type."""
    _validate_manifest_scope(manifest)
    return list(PLAYBOOK_IDS), "owner_goal_and_observed_friction"


def build_guide_bundle(manifest: dict) -> dict[str, Any]:
    selected, reason = select_playbooks(manifest)
    core, core_digest = _resource(GUIDE_ROOT / "core-v8.md")
    playbooks = []
    for playbook_id in selected:
        version = PLAYBOOK_VERSIONS[playbook_id]
        content, digest = _resource(GUIDE_ROOT / "playbooks" / f"{playbook_id}-{version}.md")
        playbooks.append({
            "id": playbook_id,
            "version": version,
            "sha256": digest,
            "content": content,
        })
    return {
        "core_version": CORE_VERSION,
        "report_version": REPORT_VERSION,
        "core_sha256": core_digest,
        "core": core,
        "playbooks": playbooks,
        "route_reason": reason,
    }


def guide_text(bundle: dict) -> str:
    sections = [bundle["core"]]
    sections.extend(playbook["content"] for playbook in bundle["playbooks"])
    return "\n\n".join(section.strip() for section in sections) + "\n"


def _string_property() -> dict[str, Any]:
    return {"type": "string"}


def report_version_for_guide(bundle: dict) -> str:
    version = REPORT_VERSIONS.get(bundle.get("core_version"))
    if version is None or bundle.get("report_version", version) != version:
        raise ValueError("unsupported or mismatched personal improvement guide/report version")
    return version


def result_schema(selected_ids: list[str], *, report_version: str = REPORT_VERSION) -> dict[str, Any]:
    if not selected_ids or any(item not in PLAYBOOK_IDS for item in selected_ids):
        raise ValueError("result schema requires selected playbooks")
    if report_version not in {REPORT_VERSION, LEGACY_REPORT_VERSION}:
        raise ValueError("unsupported personal improvement report schema")
    current = report_version == REPORT_VERSION
    finding_fields = FINDING_FIELDS + (("type_reason",) if current else ())
    result_fields = RESULT_FIELDS + (("selection_reason", "selection_evidence_ids") if current else ())
    request_fields = REQUEST_FIELDS + (("message_requests",) if current else ())
    handoff = {
        "type": "object", "additionalProperties": False,
        "properties": {name: _string_property() for name in HANDOFF_FIELDS},
        "required": list(HANDOFF_FIELDS),
    }
    finding_properties = {name: _string_property() for name in finding_fields}
    finding_properties.update({
        "title": _string_property(),
        "type_id": {"type": "string", "enum": selected_ids},
        "pattern_scope": {"type": "string", "enum": ["single_observation", "recurring_pattern"]},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
        "counterevidence_ids": {"type": "array", "items": {"type": "string"}},
        "counterexample_status": {"type": "string", "enum": ["observed", "not_observed", "not_available"]},
        "handoff": handoff,
        "outcome_state": {"type": "string", "enum": ["not_confirmed"]},
    })
    properties = {name: _string_property() for name in result_fields}
    properties.update({
        "result_version": {"type": "string", "enum": [report_version]},
        "outcome": {"type": "string", "enum": ["findings", "no_actionable_finding", "needs_evidence"]},
        "findings": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "properties": finding_properties, "required": list(finding_fields),
            },
        },
        "additional_evidence": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "kind": {"type": "string", "enum": [
                    "none", "conversation_neighbors", "independent_session",
                    "owner_goal", "outcome",
                ]},
                "question": _string_property(),
                "evidence_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": list(request_fields),
        },
    })
    if current:
        properties["selection_evidence_ids"] = {"type": "array", "items": {"type": "string"}}
        properties["additional_evidence"]["properties"]["message_requests"] = {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "anchor_evidence_id": {"type": "string"},
                    "message_index": {"type": "integer"},
                },
                "required": ["anchor_evidence_id", "message_index"],
            },
        }
    return {
        "type": "object", "additionalProperties": False,
        "properties": properties, "required": list(result_fields),
    }


def _required_text(value: Any, *, maximum: int, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{field} must be nonempty bounded text")
    return value


def _references(value: Any, lookup: dict[str, int], *, maximum: int, field: str) -> list[str]:
    if (
        not isinstance(value, list) or len(value) > maximum
        or any(not isinstance(item, str) or item not in lookup for item in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError(f"{field} must cite unique selected evidence IDs")
    return value


def _validate_message_requests(request: dict, manifest: dict) -> None:
    targets = request["message_requests"]
    if not isinstance(targets, list) or len(targets) > 5:
        raise ValueError("message requests must be a bounded list")
    if request["kind"] != "conversation_neighbors":
        if targets:
            raise ValueError("only conversation requests may target messages")
        return
    if not targets:
        raise ValueError("conversation requests must identify missing messages")
    anchors = {
        f"{event['source_key']}:{event['event_id']}": (session, event)
        for session in manifest["sessions"] for event in session["events"]
    }
    seen = set()
    for target in targets:
        if not isinstance(target, dict) or set(target) != {"anchor_evidence_id", "message_index"}:
            raise ValueError("invalid conversation message target")
        ref, index = target["anchor_evidence_id"], target["message_index"]
        if not isinstance(ref, str) or ref not in request["evidence_ids"]:
            raise ValueError("message target must use an admitted request anchor")
        session, anchor = anchors[ref]
        count = session.get("message_count")
        if (
            type(count) is not int or type(index) is not int or not 0 <= index < count
            or type(anchor.get("message_index")) is not int
            or not 0 <= anchor["message_index"] < count
        ):
            raise ValueError("message target must fall within the frozen positioned scope")
        identity = (session["session_id"], index)
        if identity in seen:
            raise ValueError("duplicate conversation message target")
        seen.add(identity)
        for event in session["events"]:
            if event.get("message_index") != index:
                continue
            if event.get("excerpt_start") == 0 and len(event["excerpt"]) == event.get("text_length"):
                raise SuppliedMessageRequestError("requested message was already supplied in full")


def validate_guided_result(value: Any, manifest: dict, bundle: dict) -> dict:
    """Return a strict, locally identified report value from one model result."""
    version = report_version_for_guide(bundle)
    current = version == REPORT_VERSION
    finding_fields = FINDING_FIELDS + (("type_reason",) if current else ())
    result_fields = RESULT_FIELDS + (("selection_reason", "selection_evidence_ids") if current else ())
    request_fields = REQUEST_FIELDS + (("message_requests",) if current else ())
    if not isinstance(value, dict) or set(value) != set(result_fields):
        raise ValueError("invalid personal improvement result fields")
    if value["result_version"] != version:
        raise ValueError("unsupported personal improvement result version")
    for field in ("title", "summary", "limits"):
        _required_text(value[field], maximum=8000, field=field)
    if not isinstance(value["no_finding_reason"], str) or len(value["no_finding_reason"]) > 8000:
        raise ValueError("invalid no-finding reason")
    outcome = value["outcome"]
    findings = value["findings"]
    if outcome not in {"findings", "no_actionable_finding", "needs_evidence"}:
        raise ValueError("invalid improvement outcome")
    if not isinstance(findings, list) or len(findings) > 3:
        raise ValueError("invalid improvement finding count")
    if (outcome == "findings") != bool(findings):
        raise ValueError("finding count does not match improvement outcome")
    if outcome == "no_actionable_finding" or (current and outcome == "needs_evidence"):
        _required_text(value["no_finding_reason"], maximum=8000, field="no_finding_reason")

    lookup = {
        f"{event['source_key']}:{event['event_id']}": session["session_id"]
        for session in manifest["sessions"] for event in session["events"]
    }
    selected_ids = {item["id"] for item in bundle["playbooks"]}
    if current:
        _required_text(value["selection_reason"], maximum=2000, field="selection_reason")
        _references(value["selection_evidence_ids"], lookup, maximum=5, field="selection_evidence_ids")
        if outcome in {"findings", "needs_evidence"} and not value["selection_evidence_ids"]:
            raise ValueError("a selected candidate must cite its evidence")
    request = value["additional_evidence"]
    if not isinstance(request, dict) or set(request) != set(request_fields):
        raise ValueError("invalid additional evidence request")
    if request["kind"] not in {
        "none", "conversation_neighbors", "independent_session", "owner_goal", "outcome"
    }:
        raise ValueError("invalid additional evidence kind")
    if not isinstance(request["question"], str) or len(request["question"]) > 1000:
        raise ValueError("invalid additional evidence question")
    _references(request["evidence_ids"], lookup, maximum=5, field="additional_evidence")
    if outcome == "needs_evidence":
        if request["kind"] == "none" or not request["question"].strip():
            raise ValueError("an evidence request needs a bounded question")
    elif request != {"kind": "none", "question": "", "evidence_ids": [], **({"message_requests": []} if current else {})}:
        raise ValueError("only a needs-evidence outcome may request more evidence")
    if current:
        _validate_message_requests(request, manifest)

    identified = []
    for index, finding in enumerate(findings, 1):
        if not isinstance(finding, dict) or set(finding) != set(finding_fields):
            raise ValueError("invalid improvement finding fields")
        if finding["type_id"] not in selected_ids:
            raise ValueError("finding type was not selected for this Run")
        if finding["pattern_scope"] not in {"single_observation", "recurring_pattern"}:
            raise ValueError("invalid finding scope")
        if finding["outcome_state"] != "not_confirmed":
            raise ValueError("owner outcome was not confirmed by this Run")
        for field in FINDING_FIELDS:
            if field in {
                "type_id", "pattern_scope", "evidence_ids", "counterevidence_ids",
                "counterexample_status", "handoff", "outcome_state",
            }:
                continue
            _required_text(finding[field], maximum=160 if field == "title" else 4000, field=field)
        if current:
            _required_text(finding["type_reason"], maximum=1000, field="type_reason")
        evidence_ids = _references(finding["evidence_ids"], lookup, maximum=12, field="evidence_ids")
        if not evidence_ids:
            raise ValueError("finding must cite selected evidence")
        counter_ids = _references(
            finding["counterevidence_ids"], lookup, maximum=12, field="counterevidence_ids"
        )
        if set(evidence_ids).intersection(counter_ids):
            raise ValueError("supporting and counterevidence IDs must be distinct")
        counter_status = finding["counterexample_status"]
        if counter_status not in {"observed", "not_observed", "not_available"}:
            raise ValueError("invalid counterexample status")
        if (counter_status == "observed") != bool(counter_ids):
            raise ValueError("counterexample status does not match citations")
        if finding["pattern_scope"] == "recurring_pattern":
            if len({lookup[ref] for ref in evidence_ids}) < 2:
                raise ValueError("recurrence needs distinct Sessions")
        handoff = finding["handoff"]
        if not isinstance(handoff, dict) or set(handoff) != set(HANDOFF_FIELDS):
            raise ValueError("invalid work-session handoff")
        for field in HANDOFF_FIELDS:
            _required_text(handoff[field], maximum=1000, field=f"handoff.{field}")
        fingerprint = json.dumps(finding, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        finding_id = sha256(f"{index}:{fingerprint}".encode("utf-8")).hexdigest()[:16]
        identified.append({**finding, "finding_id": finding_id})

    return {
        **value,
        "findings": identified,
        "guide": {
            "core_version": bundle["core_version"],
            "core_sha256": bundle["core_sha256"],
            "playbooks": [
                {key: item[key] for key in ("id", "version", "sha256")}
                for item in bundle["playbooks"]
            ],
        },
    }
