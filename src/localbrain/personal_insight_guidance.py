"""Versioned, product-neutral guidance and finding values for personal insights."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .personal_insight_evidence import MANIFEST_VERSION


CORE_VERSION = "personal-improvement-core-v2"
PLAYBOOK_VERSION = "v1"
REPORT_VERSION = "personal-improvement-report-v2"
GUIDE_ROOT = Path(__file__).with_name("personal_insight_guides")
MAX_SELECTED_PLAYBOOKS = 4

PLAYBOOKS = (
    ("task_framing", ("goal", "audience", "scope", "brief", "목표", "결과물", "요구사항", "범위")),
    ("request_feedback", ("prompt", "answer", "format", "feedback", "질문", "답변", "형식", "수정")),
    ("context_recovery", ("context", "resume", "handoff", "맥락", "이전", "기억", "재개", "인수")),
    ("repeatable_procedure", ("repeat", "routine", "automation", "반복", "자동화", "템플릿", "절차", "스크립트")),
    ("learning_explanation", ("why", "explain", "understand", "왜", "설명", "이해", "개념", "배우")),
    ("verification_rework", ("verify", "test", "wrong", "검증", "확인", "오류", "틀렸", "재작업")),
    ("information_access", ("search", "source", "lookup", "검색", "자료", "출처", "문서", "접근")),
    ("decision_memory", ("decision", "choice", "decide", "결정", "선택", "근거", "판단")),
    ("task_fit_effort", ("cost", "token", "slow", "비용", "토큰", "시간", "모델", "효율")),
    ("personal_value", ("priority", "value", "outcome", "우선순위", "목적", "성과", "가치")),
    ("assistant_configuration", ("skill", "harness", "agents.md", "설정", "스킬", "에이전트")),
)
PLAYBOOK_IDS = tuple(item[0] for item in PLAYBOOKS)
FALLBACK_IDS = (
    "task_framing", "request_feedback", "learning_explanation", "personal_value"
)

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


def _resource(path: Path) -> tuple[str, str]:
    content = path.read_text(encoding="utf-8")
    return content, sha256(content.encode("utf-8")).hexdigest()


def _routing_text(manifest: dict) -> tuple[str, str]:
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
    excerpts = []
    for session in manifest.get("sessions", []):
        for event in session.get("events", []):
            if event.get("role") == "user" and isinstance(event.get("excerpt"), str):
                excerpts.append(event["excerpt"])
    return (question or "").casefold(), "\n".join(excerpts).casefold()


def select_playbooks(manifest: dict) -> tuple[list[str], str]:
    """Use bounded lexical routing, not an inference that a pattern exists."""
    question, excerpts = _routing_text(manifest)
    question_matches = []
    excerpt_matches = []
    for index, (playbook_id, cues) in enumerate(PLAYBOOKS):
        question_hits = sum(cue in question for cue in cues)
        excerpt_hits = sum(cue in excerpts for cue in cues)
        if question_hits:
            question_matches.append((-question_hits, -excerpt_hits, index, playbook_id))
        elif excerpt_hits:
            excerpt_matches.append((-excerpt_hits, index, playbook_id))
    selected = [item[-1] for item in sorted(question_matches)]
    selected.extend(item[-1] for item in sorted(excerpt_matches))
    selected = selected[:MAX_SELECTED_PLAYBOOKS]
    reason = "question_priority_then_user_excerpts" if question_matches else "user_excerpts"
    if not selected:
        selected = list(FALLBACK_IDS)
        reason = "broad_fallback_no_lexical_cue"
    return selected, reason


def build_guide_bundle(manifest: dict) -> dict[str, Any]:
    selected, reason = select_playbooks(manifest)
    core, core_digest = _resource(GUIDE_ROOT / "core-v2.md")
    playbooks = []
    for playbook_id in selected:
        content, digest = _resource(
            GUIDE_ROOT / "playbooks" / f"{playbook_id}-v1.md"
        )
        playbooks.append({
            "id": playbook_id,
            "version": PLAYBOOK_VERSION,
            "sha256": digest,
            "content": content,
        })
    return {
        "core_version": CORE_VERSION,
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


def result_schema(selected_ids: list[str]) -> dict[str, Any]:
    if not selected_ids or any(item not in PLAYBOOK_IDS for item in selected_ids):
        raise ValueError("result schema requires selected playbooks")
    handoff = {
        "type": "object", "additionalProperties": False,
        "properties": {name: _string_property() for name in HANDOFF_FIELDS},
        "required": list(HANDOFF_FIELDS),
    }
    finding_properties = {name: _string_property() for name in FINDING_FIELDS}
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
    properties = {name: _string_property() for name in RESULT_FIELDS}
    properties.update({
        "result_version": {"type": "string", "enum": [REPORT_VERSION]},
        "outcome": {"type": "string", "enum": ["findings", "no_actionable_finding", "needs_evidence"]},
        "findings": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "properties": finding_properties, "required": list(FINDING_FIELDS),
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
            "required": list(REQUEST_FIELDS),
        },
    })
    return {
        "type": "object", "additionalProperties": False,
        "properties": properties, "required": list(RESULT_FIELDS),
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


def validate_guided_result(value: Any, manifest: dict, bundle: dict) -> dict:
    """Return a strict, locally identified report value from one model result."""
    if not isinstance(value, dict) or set(value) != set(RESULT_FIELDS):
        raise ValueError("invalid personal improvement result fields")
    if value["result_version"] != REPORT_VERSION:
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
    if outcome == "no_actionable_finding":
        _required_text(value["no_finding_reason"], maximum=8000, field="no_finding_reason")

    lookup = {
        f"{event['source_key']}:{event['event_id']}": session["session_id"]
        for session in manifest["sessions"] for event in session["events"]
    }
    selected_ids = {item["id"] for item in bundle["playbooks"]}
    request = value["additional_evidence"]
    if not isinstance(request, dict) or set(request) != set(REQUEST_FIELDS):
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
    elif request != {"kind": "none", "question": "", "evidence_ids": []}:
        raise ValueError("only a needs-evidence outcome may request more evidence")

    identified = []
    for index, finding in enumerate(findings, 1):
        if not isinstance(finding, dict) or set(finding) != set(FINDING_FIELDS):
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
