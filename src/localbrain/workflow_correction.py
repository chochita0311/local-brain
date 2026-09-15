"""Strict local request contract for one Workflow Focus correction."""

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qsl

from .workflow_projection import CLOSURE_REASONS


WORKFLOW_CORRECTION_PARTIAL = "workflow-correction"
MAX_WORKFLOW_CORRECTION_FORM_BYTES = 16 * 1024
MAX_WORKFLOW_CORRECTION_FIELDS = 8
MAX_SQLITE_INTEGER = 9_223_372_036_854_775_807

WORKFLOW_CORRECTION_ACTIONS = frozenset(
    {"same-flow", "split-here", "merge-into", "close", "reopen", "undo"}
)
WORKFLOW_CORRECTION_FIELDS = frozenset(
    {
        "action",
        "source_episode_key",
        "target_episode_key",
        "close_reason",
        "note",
        "assertion_id",
        "expected_active_assertion_id",
        "expected_revision",
    }
)

_EPISODE_KEY = re.compile(r"^session:[0-9a-f]{64}$")
_REVISION = re.compile(r"^workflow-revision:[0-9a-f]{64}$")
_BAD_PERCENT_ESCAPE = re.compile(rb"%(?![0-9A-Fa-f]{2})")


class WorkflowCorrectionRequestError(ValueError):
    """Bounded transport or request-shape rejection."""

    def __init__(self, code: str, message: str, *, status_code: int):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class WorkflowCorrectionRequest:
    action: str
    expected_revision: str
    source_episode_key: Optional[str] = None
    target_episode_key: Optional[str] = None
    close_reason: Optional[str] = None
    note: Optional[str] = None
    assertion_id: Optional[int] = None
    expected_active_assertion_id: Optional[int] = None


def _reject(code: str, message: str, status_code: int = 422) -> None:
    raise WorkflowCorrectionRequestError(
        code, message, status_code=status_code
    )


def reject_cross_site_workflow_correction(fetch_site: Optional[str]) -> None:
    """Reject an explicitly cross-site browser submission before body parsing."""
    if isinstance(fetch_site, str) and fetch_site.strip().lower() == "cross-site":
        _reject(
            "cross-site-request",
            "Cross-site workflow corrections are not accepted.",
            400,
        )


def _positive_integer(value: str, field: str) -> int:
    if not re.fullmatch(r"[1-9][0-9]*", value):
        _reject("invalid-request", "{} must be a positive integer.".format(field))
    parsed = int(value)
    if parsed > MAX_SQLITE_INTEGER:
        _reject("invalid-request", "{} is outside the supported range.".format(field))
    return parsed


def _episode_key(value: Optional[str], field: str) -> str:
    if value is None or not _EPISODE_KEY.fullmatch(value):
        _reject("invalid-request", "{} must be a stable Episode key.".format(field))
    return value


def _optional_integer(values: dict, field: str) -> Optional[int]:
    value = values.get(field)
    return _positive_integer(value, field) if value is not None else None


def _require_exact_fields(values: dict, required: set, optional: set = None) -> None:
    optional = optional or set()
    actual = set(values)
    if not required.issubset(actual) or not actual.issubset(required | optional):
        _reject("invalid-request", "The correction fields do not match the action.")


def parse_workflow_correction_form(
    content_type: Optional[str], body: bytes
) -> WorkflowCorrectionRequest:
    """Parse an exact, bounded urlencoded correction outside a transaction."""
    media_type = str(content_type or "").split(";", 1)[0].strip().lower()
    if media_type != "application/x-www-form-urlencoded":
        _reject("invalid-form", "Form encoding is unsupported.", 400)
    if not isinstance(body, bytes) or len(body) > MAX_WORKFLOW_CORRECTION_FORM_BYTES:
        _reject("invalid-form", "Form is too large.", 400)
    if not body or _BAD_PERCENT_ESCAPE.search(body):
        _reject("invalid-form", "Form data is invalid.", 400)
    try:
        decoded = body.decode("ascii")
        pairs = parse_qsl(
            decoded,
            keep_blank_values=True,
            strict_parsing=True,
            encoding="utf-8",
            errors="strict",
            max_num_fields=MAX_WORKFLOW_CORRECTION_FIELDS,
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise WorkflowCorrectionRequestError(
            "invalid-form", "Form data is invalid.", status_code=400
        ) from exc

    values = {}
    for key, value in pairs:
        if key not in WORKFLOW_CORRECTION_FIELDS:
            _reject("invalid-request", "The form contains an unknown field.")
        if key in values:
            _reject("invalid-request", "The form contains a repeated field.")
        if not value and key != "note":
            _reject("invalid-request", "Correction fields cannot be blank.")
        values[key] = value

    action = values.get("action")
    revision = values.get("expected_revision")
    if action not in WORKFLOW_CORRECTION_ACTIONS:
        _reject("invalid-action", "The workflow correction action is unsupported.")
    if revision is None or not _REVISION.fullmatch(revision):
        _reject("invalid-request", "A stable workflow revision is required.")

    if action == "undo":
        _require_exact_fields(values, {"action", "assertion_id", "expected_revision"})
        return WorkflowCorrectionRequest(
            action=action,
            assertion_id=_positive_integer(values["assertion_id"], "assertion_id"),
            expected_revision=revision,
        )

    source_key = _episode_key(values.get("source_episode_key"), "source_episode_key")
    expected_active = _optional_integer(values, "expected_active_assertion_id")
    common = {"action", "source_episode_key", "expected_revision"}
    optional_active = {"expected_active_assertion_id"}

    if action in {"same-flow", "split-here", "merge-into"}:
        _require_exact_fields(
            values,
            common | {"target_episode_key"},
            optional_active,
        )
        return WorkflowCorrectionRequest(
            action=action,
            source_episode_key=source_key,
            target_episode_key=_episode_key(
                values.get("target_episode_key"), "target_episode_key"
            ),
            expected_active_assertion_id=expected_active,
            expected_revision=revision,
        )

    if action == "close":
        _require_exact_fields(
            values,
            common | {"close_reason"},
            optional_active | {"note"},
        )
        if values["close_reason"] not in CLOSURE_REASONS:
            _reject("invalid-close-reason", "The close reason is unsupported.")
        note = values.get("note") or None
        if note is not None and len(note) > 1_000:
            _reject("invalid-note", "The correction note is too long.")
        return WorkflowCorrectionRequest(
            action=action,
            source_episode_key=source_key,
            close_reason=values["close_reason"],
            note=note,
            expected_active_assertion_id=expected_active,
            expected_revision=revision,
        )

    _require_exact_fields(values, common | {"expected_active_assertion_id"})
    return WorkflowCorrectionRequest(
        action=action,
        source_episode_key=source_key,
        expected_active_assertion_id=expected_active,
        expected_revision=revision,
    )
