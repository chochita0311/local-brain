import hashlib
import inspect
import json
import re
import shutil
import uuid
from pathlib import Path
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
)
from urllib.parse import urlsplit

from .config import settings
from .external_access import (
    READ_POLICY_VERSION,
    ExternalAccessError,
    ToolDispatch,
    authorize_external_read,
    capability_state,
)
from .workstreams import utc_now


EXTERNAL_SYNC_TASK = "external_source_sync"
MANIFEST_SCHEMA = "localbrain.external-sync-manifest.v1"
RESULT_SCHEMA_VERSION = "localbrain.external-sync-result.v1"
MODEL_RESULT_SCHEMA_VERSION = "localbrain.external-sync-model-result.v1"

RUNNERS = {"claude", "codex"}
SCOPE_KINDS = {"item", "space", "thread", "workstream", "all_known"}
LOCATOR_KINDS = {"url", "remote_id", "source_root", "local_ref"}
COVERAGE_VALUES = {"metadata", "content", "hierarchy"}
OUTCOMES = {
    "resolved",
    "unchanged",
    "changed",
    "unavailable",
    "not_found",
    "error",
}
SUCCESS_OUTCOMES = {"resolved", "unchanged", "changed"}
SOURCE_KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ERROR_CODE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
MAX_TARGETS = 500
MAX_CALL_BUDGET = 200
MAX_ARGUMENT_BYTES = 32_768
MAX_FACT_BYTES = 2_000_000
CONTENT_OPERATIONS = {"jira.read_description", "confluence.read_page"}
SAFE_PROVIDER_ERROR_MESSAGES = {
    "unavailable": "External source is unavailable.",
    "not_found": "Selected external resource was not found.",
    "error": "Approved external read failed.",
}


MODEL_RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "schema": {
            "type": "string",
            "enum": [MODEL_RESULT_SCHEMA_VERSION],
        },
        "run_id": {"type": "string"},
        "summary": {"type": "string", "maxLength": 2000},
    },
    "required": ["schema", "run_id", "summary"],
}


class ExternalSyncError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


ExternalReadExecutor = Callable[
    [ToolDispatch],
    Union[Mapping[str, Any], Awaitable[Mapping[str, Any]]],
]


def _fail(code: str, message: str) -> None:
    raise ExternalSyncError(code, message)


def _exact_keys(
    value: Mapping[str, Any],
    *,
    required: Iterable[str],
    optional: Iterable[str] = (),
    label: str,
    code: str = "invalid-manifest",
) -> None:
    if not isinstance(value, Mapping):
        _fail(code, "{} must be an object".format(label))
    required_keys = set(required)
    allowed = required_keys | set(optional)
    missing = required_keys - set(value)
    extra = set(value) - allowed
    if missing:
        _fail(
            code,
            "{} is missing: {}".format(label, ", ".join(sorted(missing))),
        )
    if extra:
        _fail(
            code,
            "{} has unsupported fields".format(label),
        )


def _text(
    value: Any,
    label: str,
    *,
    maximum: int,
    pattern: Optional[re.Pattern] = None,
    code: str = "invalid-manifest",
) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(code, "{} must be a non-empty string".format(label))
    normalized = value.strip()
    if len(normalized) > maximum:
        _fail(
            code,
            "{} exceeds {} characters".format(label, maximum),
        )
    if pattern is not None and not pattern.fullmatch(normalized):
        _fail(code, "{} has an invalid shape".format(label))
    return normalized


def _optional_text(
    value: Any,
    label: str,
    maximum: int,
    *,
    code: str = "invalid-manifest",
) -> Optional[str]:
    if value is None:
        return None
    return _text(value, label, maximum=maximum, code=code)


def _json_size(
    value: Any,
    label: str,
    maximum: int,
    *,
    code: str = "invalid-manifest",
) -> int:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError):
        _fail(code, "{} must be JSON serializable".format(label))
    if len(encoded) > maximum:
        _fail(
            code,
            "{} exceeds {} bytes".format(label, maximum),
        )
    return len(encoded)


def _validate_locator(value: Any) -> dict:
    _exact_keys(
        value,
        required=("kind", "value"),
        label="target.locator",
    )
    kind = _text(value["kind"], "target.locator.kind", maximum=32)
    if kind not in LOCATOR_KINDS:
        _fail("invalid-manifest", "unsupported target locator kind")
    locator = _text(value["value"], "target.locator.value", maximum=4000)
    if kind == "url":
        parsed = urlsplit(locator)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            _fail("invalid-manifest", "URL locators must use HTTP or HTTPS")
    return {"kind": kind, "value": locator}


def _validate_known(value: Any) -> dict:
    if value is None:
        return {
            "remote_version": None,
            "remote_updated_at": None,
            "content_hash": None,
        }
    _exact_keys(
        value,
        required=(),
        optional=("remote_version", "remote_updated_at", "content_hash"),
        label="target.known",
    )
    content_hash = value.get("content_hash")
    if content_hash is not None:
        content_hash = _text(
            content_hash,
            "target.known.content_hash",
            maximum=64,
            pattern=HASH_PATTERN,
        )
    return {
        "remote_version": _optional_text(
            value.get("remote_version"), "target.known.remote_version", 300
        ),
        "remote_updated_at": _optional_text(
            value.get("remote_updated_at"),
            "target.known.remote_updated_at",
            100,
        ),
        "content_hash": content_hash,
    }


def _validate_coverage(value: Any) -> List[str]:
    if (
        not isinstance(value, list)
        or not value
        or len(value) > len(COVERAGE_VALUES)
    ):
        _fail(
            "invalid-manifest",
            "target.coverage must be a non-empty bounded list",
        )
    coverage = []
    for item in value:
        if item not in COVERAGE_VALUES:
            _fail("invalid-manifest", "unsupported target coverage")
        if item not in coverage:
            coverage.append(item)
    return coverage


def _validate_field_allowlist(value: Any) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 100:
        _fail("invalid-manifest", "field_allowlist must be a bounded list")
    fields = []
    for item in value:
        field = _text(item, "field_allowlist item", maximum=120)
        if field not in fields:
            fields.append(field)
    return fields


def build_external_sync_manifest(
    connection,
    *,
    run_id: str,
    runner: str,
    source_instance_id: Optional[int],
    source_kind: str,
    scope_kind: str,
    targets: Iterable[Mapping[str, Any]],
    call_budget: Optional[int] = None,
) -> Tuple[dict, Dict[str, ToolDispatch]]:
    if runner not in RUNNERS:
        _fail("unsupported-runner", "runner must be claude or codex")
    source_kind = _text(
        source_kind, "source_kind", maximum=64, pattern=SOURCE_KIND_PATTERN
    )
    if scope_kind not in SCOPE_KINDS:
        _fail("invalid-manifest", "unsupported external sync scope")
    if source_instance_id is not None and (
        isinstance(source_instance_id, bool)
        or not isinstance(source_instance_id, int)
    ):
        _fail(
            "invalid-manifest",
            "source_instance_id must be an integer or null",
        )
    if call_budget is None:
        call_budget = settings.mcp_call_budget
    if (
        isinstance(call_budget, bool)
        or not isinstance(call_budget, int)
        or not 1 <= call_budget <= MAX_CALL_BUDGET
    ):
        _fail(
            "invalid-manifest",
            "call_budget must be between 1 and {}".format(MAX_CALL_BUDGET),
        )
    raw_targets = list(targets)
    if not 1 <= len(raw_targets) <= MAX_TARGETS:
        _fail(
            "invalid-manifest",
            "targets must contain between 1 and {}".format(MAX_TARGETS),
        )

    normalized_targets = []
    dispatches: Dict[str, ToolDispatch] = {}
    seen_target_ids = set()
    request_count = 0
    source_states: Dict[int, dict] = {}
    selected_source_ids = set()
    selected_services = set()
    for raw_target in raw_targets:
        _exact_keys(
            raw_target,
            required=("target_id", "locator", "coverage", "requests"),
            optional=("known", "field_allowlist", "source_instance_id"),
            label="target",
        )
        target_source_id = raw_target.get(
            "source_instance_id", source_instance_id
        )
        if (
            isinstance(target_source_id, bool)
            or not isinstance(target_source_id, int)
        ):
            _fail(
                "invalid-manifest",
                "each target requires a Source Instance",
            )
        if (
            source_instance_id is not None
            and target_source_id != source_instance_id
        ):
            _fail(
                "source-instance-mismatch",
                "single-source targets cannot change Source Instance",
            )
        state = source_states.get(target_source_id)
        if state is None:
            state = capability_state(connection, target_source_id)
            if state["state"] != "current":
                _fail(
                    "capability-not-current",
                    "Source Instance capability state is {}".format(
                        state["state"]
                    ),
                )
            if state["provider_kind"] in {
                "mcp_gateway",
                "atlassian_cloud",
            } and source_kind != "atlassian":
                _fail(
                    "source-kind-mismatch",
                    "the selected Source Instance requires source_kind atlassian",
                )
            source_states[target_source_id] = state
        selected_source_ids.add(target_source_id)
        selected_services.add(state["service"])
        target_id = _text(
            raw_target["target_id"],
            "target.target_id",
            maximum=128,
            pattern=IDENTIFIER_PATTERN,
        )
        if target_id in seen_target_ids:
            _fail("invalid-manifest", "target_id must be unique")
        seen_target_ids.add(target_id)
        coverage = _validate_coverage(raw_target["coverage"])
        field_allowlist = _validate_field_allowlist(
            raw_target.get("field_allowlist")
        )
        if "metadata" in coverage and not field_allowlist:
            _fail(
                "invalid-manifest",
                "metadata coverage requires an explicit field_allowlist",
            )
        raw_requests = raw_target["requests"]
        if not isinstance(raw_requests, list) or not raw_requests:
            _fail(
                "invalid-manifest",
                "target.requests must be a non-empty list",
            )
        requests = []
        seen_request_ids = set()
        for raw_request in raw_requests:
            _exact_keys(
                raw_request,
                required=("request_id", "logical_operation", "arguments"),
                label="target.request",
            )
            request_id = _text(
                raw_request["request_id"],
                "target.request.request_id",
                maximum=128,
                pattern=IDENTIFIER_PATTERN,
            )
            if request_id in seen_request_ids or request_id in dispatches:
                _fail("invalid-manifest", "request_id must be globally unique")
            seen_request_ids.add(request_id)
            operation = _text(
                raw_request["logical_operation"],
                "target.request.logical_operation",
                maximum=160,
            )
            if operation.startswith("capability."):
                _fail(
                    "operation-not-allowed",
                    "capability inspection is not an external sync request",
                )
            arguments = raw_request["arguments"]
            if not isinstance(arguments, Mapping):
                _fail(
                    "invalid-manifest",
                    "target.request.arguments must be an object",
                )
            _json_size(arguments, "target.request.arguments", MAX_ARGUMENT_BYTES)
            request_fields = arguments.get("fields")
            if operation == "jira.search_metadata":
                if not isinstance(request_fields, list) or not request_fields:
                    _fail(
                        "invalid-manifest",
                        "Jira metadata requests require explicit selected fields",
                    )
                if any(field not in field_allowlist for field in request_fields):
                    _fail(
                        "invalid-manifest",
                        "Jira metadata request fields exceed the target allowlist",
                    )
            try:
                dispatch = authorize_external_read(
                    connection,
                    target_source_id,
                    operation,
                    arguments,
                )
            except ExternalAccessError as exc:
                raise ExternalSyncError(exc.code, str(exc)) from exc
            dispatches[request_id] = dispatch
            requests.append(
                {
                    "request_id": request_id,
                    "logical_operation": operation,
                    "arguments": dict(arguments),
                }
            )
            request_count += 1
        normalized_target = {
            "target_id": target_id,
            "locator": _validate_locator(raw_target["locator"]),
            "coverage": coverage,
            "field_allowlist": field_allowlist,
            "known": _validate_known(raw_target.get("known")),
            "requests": requests,
        }
        if source_instance_id is None:
            normalized_target["source_instance_id"] = target_source_id
        normalized_targets.append(normalized_target)
    if request_count > call_budget:
        _fail(
            "call-budget-exceeded",
            "selected requests exceed the external sync call budget",
        )
    mixed_source = source_instance_id is None
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "run_id": _text(
            run_id, "run_id", maximum=128, pattern=IDENTIFIER_PATTERN
        ),
        "generated_at": utc_now(),
        "runner": runner,
        "source": {
            "kind": source_kind,
            "instance_id": (
                None
                if mixed_source
                else next(iter(selected_source_ids))
            ),
            "service": (
                next(iter(selected_services))
                if len(selected_services) == 1
                else "mixed"
            ),
        },
        "scope": {"kind": scope_kind},
        "read_policy_version": READ_POLICY_VERSION,
        "call_budget": call_budget,
        "targets": normalized_targets,
    }
    return manifest, dispatches


def external_sync_projection(manifest: Mapping[str, Any]) -> dict:
    return {
        "maintenance_run_id": manifest["run_id"],
        "source_instance_id": manifest["source"]["instance_id"],
        "source_kind": manifest["source"]["kind"],
        "service": manifest["source"]["service"],
        "requested_scope_kind": manifest["scope"]["kind"],
        "selected_target_count": len(manifest["targets"]),
        "manifest_schema_version": manifest["schema"],
        "read_policy_version": manifest["read_policy_version"],
    }


def build_external_sync_prompt(
    run_id: str,
    manifest_path: Path,
    evidence_path: Path,
    *,
    manifest: Optional[Mapping[str, Any]] = None,
    evidence: Optional[Mapping[str, Any]] = None,
) -> str:
    inline_payload = ""
    if manifest is not None and evidence is not None:
        inline_payload = "\n\nValidated input:\n" + json.dumps(
            {"manifest": manifest, "evidence": evidence},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    return """[LOCALBRAIN_RUN: {run_id}]
[MODE: maintenance]

You are LocalBrain's external synchronization maintenance runner. This is not
an ordinary work session.

Rules:
- Read only the selected manifest and host-validated evidence files below.
- Do not call MCP, Gateway, network, shell, Git, ticket, email, or chat tools.
- Do not invent or rewrite remote identity, metadata, content, timestamps,
  versions, hashes, outcomes, or provider errors.
- Return only a short summary of the already validated target outcomes.

Manifest: {manifest_path}
Evidence: {evidence_path}

Return the exact JSON schema supplied by LocalBrain. Use schema
`{model_schema}` and run_id `{run_id}`.
{inline_payload}
""".format(
        run_id=run_id,
        manifest_path=manifest_path,
        evidence_path=evidence_path,
        model_schema=MODEL_RESULT_SCHEMA_VERSION,
        inline_payload=inline_payload,
    )


def prepare_external_sync_run(
    connection,
    *,
    runner: str,
    source_instance_id: Optional[int],
    source_kind: str,
    scope_kind: str,
    targets: Iterable[Mapping[str, Any]],
    workstream_id: Optional[int] = None,
    call_budget: Optional[int] = None,
    run_root: Optional[Path] = None,
) -> str:
    run_id = "lb-{}".format(uuid.uuid4().hex[:12])
    manifest, _dispatches = build_external_sync_manifest(
        connection,
        run_id=run_id,
        runner=runner,
        source_instance_id=source_instance_id,
        source_kind=source_kind,
        scope_kind=scope_kind,
        targets=targets,
        call_budget=call_budget,
    )
    projection = external_sync_projection(manifest)
    root = (run_root or (settings.data_dir / "runs")) / run_id
    root.mkdir(parents=True, exist_ok=False)
    manifest_path = root / "manifest.json"
    prompt_path = root / "prompt.md"
    stream_path = root / "stream.jsonl"
    result_path = root / "result.md"
    stderr_path = root / "stderr.log"
    evidence_path = root / "evidence.json"
    model_schema_path = root / "model-result-schema.json"
    model_result_path = root / "model-result.json"
    empty_mcp_path = root / "empty-mcp.json"
    try:
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        prompt_path.write_text(
            build_external_sync_prompt(run_id, manifest_path, evidence_path),
            encoding="utf-8",
        )
        model_schema_path.write_text(
            json.dumps(
                MODEL_RESULT_SCHEMA,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        empty_mcp_path.write_text(
            '{"mcpServers":{}}\n',
            encoding="utf-8",
        )
        now = utc_now()
        connection.execute("SAVEPOINT external_sync_prepare")
        try:
            connection.execute(
                """
                INSERT INTO maintenance_runs(
                    id, workstream_id, task_type, runner, cwd, status,
                    source_snapshot_json, manifest_path, prompt_path,
                    stream_path, result_path, stderr_path,
                    refresh_suggestions, mcp_call_budget, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'queued', ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    run_id,
                    workstream_id,
                    EXTERNAL_SYNC_TASK,
                    runner,
                    str(root),
                    json.dumps(manifest, ensure_ascii=False),
                    str(manifest_path),
                    str(prompt_path),
                    str(stream_path),
                    str(result_path),
                    str(stderr_path),
                    manifest["call_budget"],
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO external_sync_runs(
                    maintenance_run_id, source_instance_id, source_kind,
                    service, requested_scope_kind, selected_target_count,
                    manifest_schema_version, read_policy_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    projection["maintenance_run_id"],
                    projection["source_instance_id"],
                    projection["source_kind"],
                    projection["service"],
                    projection["requested_scope_kind"],
                    projection["selected_target_count"],
                    projection["manifest_schema_version"],
                    projection["read_policy_version"],
                ),
            )
        except Exception:
            connection.execute("ROLLBACK TO external_sync_prepare")
            connection.execute("RELEASE external_sync_prepare")
            raise
        connection.execute("RELEASE external_sync_prepare")
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
    # These paths are deterministic children of the private Run root and do not
    # need provider-specific columns in the common ledger.
    assert model_result_path.parent == root
    return run_id


def load_external_sync_manifest(
    connection, run: Mapping[str, Any]
) -> Tuple[dict, Dict[str, ToolDispatch]]:
    if run["task_type"] != EXTERNAL_SYNC_TASK:
        _fail("not-external-sync", "Run is not an external synchronization")
    try:
        stored = json.loads(run["source_snapshot_json"] or "{}")
    except json.JSONDecodeError as exc:
        raise ExternalSyncError(
            "invalid-manifest", "stored external sync manifest is invalid"
        ) from exc
    try:
        artifact = json.loads(
            Path(run["manifest_path"]).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ExternalSyncError(
            "invalid-manifest", "external sync manifest artifact is invalid"
        ) from exc
    if artifact != stored:
        _fail(
            "external-sync-manifest-mismatch",
            "stored external sync manifest does not match its artifact",
        )
    manifest, dispatches = build_external_sync_manifest(
        connection,
        run_id=stored.get("run_id"),
        runner=stored.get("runner"),
        source_instance_id=stored.get("source", {}).get("instance_id"),
        source_kind=stored.get("source", {}).get("kind"),
        scope_kind=stored.get("scope", {}).get("kind"),
        targets=stored.get("targets", []),
        call_budget=stored.get("call_budget"),
    )
    manifest["generated_at"] = _text(
        stored.get("generated_at"),
        "generated_at",
        maximum=100,
    )
    if manifest != stored:
        _fail(
            "external-sync-manifest-mismatch",
            "stored external sync manifest is not canonical for the current contract",
        )
    projection = external_sync_projection(manifest)
    row = connection.execute(
        "SELECT * FROM external_sync_runs WHERE maintenance_run_id = ?",
        (run["id"],),
    ).fetchone()
    if not row:
        _fail(
            "external-sync-envelope-missing",
            "external synchronization has no query envelope",
        )
    for key, expected in projection.items():
        if row[key] != expected:
            _fail(
                "external-sync-envelope-mismatch",
                "external synchronization query envelope does not match manifest",
            )
    return manifest, dispatches


def _validate_fact_object(value: Any, label: str) -> dict:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        _fail("invalid-provider-result", "{} must be an object".format(label))
    normalized = dict(value)
    _json_size(
        normalized,
        label,
        MAX_FACT_BYTES,
        code="invalid-provider-result",
    )
    return normalized


def validate_provider_result(
    value: Mapping[str, Any],
    *,
    request: Mapping[str, Any],
    coverage: Iterable[str],
    field_allowlist: Iterable[str],
) -> dict:
    _exact_keys(
        value,
        required=("outcome",),
        optional=(
            "identity",
            "metadata",
            "content",
            "remote_version",
            "remote_updated_at",
            "error",
        ),
        label="provider result",
        code="invalid-provider-result",
    )
    outcome = value["outcome"]
    if outcome not in OUTCOMES:
        _fail("invalid-provider-result", "unsupported provider outcome")
    identity = _validate_fact_object(value.get("identity"), "identity")
    metadata = _validate_fact_object(value.get("metadata"), "metadata")
    if metadata and "metadata" not in coverage:
        _fail(
            "invalid-provider-result",
            "provider metadata was returned for a target without metadata coverage",
        )
    allowed_fields = set(field_allowlist)
    if not set(metadata).issubset(allowed_fields):
        _fail(
            "invalid-provider-result",
            "provider metadata contains a field outside the manifest allowlist",
        )
    content = value.get("content")
    if content is not None and "content" not in coverage:
        _fail(
            "invalid-provider-result",
            "provider content was returned for a target without content coverage",
        )
    if (
        content is not None
        and request["logical_operation"] not in CONTENT_OPERATIONS
    ):
        _fail(
            "invalid-provider-result",
            "provider content was returned by a non-content operation",
        )
    _json_size(
        content,
        "content",
        MAX_FACT_BYTES,
        code="invalid-provider-result",
    )
    error = value.get("error")
    if error is not None:
        _exact_keys(
            error,
            required=("code",),
            optional=("message",),
            label="provider result error",
            code="invalid-provider-result",
        )
        error = {
            "code": _text(
                error["code"],
                "provider result error code",
                maximum=80,
                pattern=ERROR_CODE_PATTERN,
                code="invalid-provider-result",
            ),
            "message": SAFE_PROVIDER_ERROR_MESSAGES.get(
                outcome, "Approved external read failed."
            ),
        }
    if outcome in SUCCESS_OUTCOMES and error is not None:
        _fail(
            "invalid-provider-result",
            "successful provider outcomes cannot include an error",
        )
    if outcome not in SUCCESS_OUTCOMES and error is None:
        _fail(
            "invalid-provider-result",
            "unsuccessful provider outcomes require a bounded error",
        )
    content_hash = None
    if content is not None:
        canonical = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        content_hash = hashlib.sha256(canonical).hexdigest()
    return {
        "request_id": request["request_id"],
        "logical_operation": request["logical_operation"],
        "outcome": outcome,
        "identity": identity,
        "metadata": metadata,
        "content": content,
        "remote_version": _optional_text(
            value.get("remote_version"),
            "remote_version",
            300,
            code="invalid-provider-result",
        ),
        "remote_updated_at": _optional_text(
            value.get("remote_updated_at"),
            "remote_updated_at",
            100,
            code="invalid-provider-result",
        ),
        "content_hash": content_hash,
        "error": error,
    }


def aggregate_target_outcome(request_results: Iterable[Mapping[str, Any]]) -> str:
    outcomes = [result["outcome"] for result in request_results]
    if "error" in outcomes:
        return "error"
    if "unavailable" in outcomes:
        return "unavailable" if all(
            outcome == "unavailable" for outcome in outcomes
        ) else "error"
    if "not_found" in outcomes:
        return "not_found" if all(
            outcome == "not_found" for outcome in outcomes
        ) else "error"
    if "changed" in outcomes:
        return "changed"
    if "resolved" in outcomes:
        return "resolved"
    if outcomes and all(outcome == "unchanged" for outcome in outcomes):
        return "unchanged"
    return "error"


def derive_run_status(target_results: Iterable[Mapping[str, Any]]) -> str:
    outcomes = [target["outcome"] for target in target_results]
    success_count = sum(outcome in SUCCESS_OUTCOMES for outcome in outcomes)
    if success_count == len(outcomes) and outcomes:
        return "completed"
    if success_count:
        return "partial"
    return "failed"


async def collect_external_sync_evidence(
    manifest: Mapping[str, Any],
    dispatches: Mapping[str, ToolDispatch],
    executor: ExternalReadExecutor,
    *,
    on_call: Optional[Callable[[List[dict]], None]] = None,
) -> Tuple[List[dict], List[dict]]:
    target_results = []
    call_log: List[dict] = []
    for target in manifest["targets"]:
        request_results = []
        for request in target["requests"]:
            request_id = request["request_id"]
            dispatch = dispatches[request_id]
            call_entry = {
                "request_id": request_id,
                "target_id": target["target_id"],
                "logical_operation": dispatch.logical_operation,
                "tool_name": dispatch.tool_name,
                "outcome": "running",
            }
            call_log.append(call_entry)
            if on_call is not None:
                on_call(call_log)
            try:
                raw_result = executor(dispatch)
                if inspect.isawaitable(raw_result):
                    raw_result = await raw_result
                validated = validate_provider_result(
                    raw_result,
                    request=request,
                    coverage=target["coverage"],
                    field_allowlist=target["field_allowlist"],
                )
            except ExternalSyncError:
                call_entry["outcome"] = "invalid"
                if on_call is not None:
                    on_call(call_log)
                raise
            except Exception as exc:
                call_entry["outcome"] = "error"
                if on_call is not None:
                    on_call(call_log)
                raise ExternalSyncError(
                    "provider-execution-failed",
                    "Approved external read executor failed.",
                ) from exc
            call_entry["outcome"] = validated["outcome"]
            if on_call is not None:
                on_call(call_log)
            request_results.append(validated)
        target_results.append(
            {
                "target_id": target["target_id"],
                "locator": target["locator"],
                "outcome": aggregate_target_outcome(request_results),
                "requests": request_results,
            }
        )
    return target_results, call_log


def validate_model_result(value: Any, run_id: str) -> dict:
    _exact_keys(
        value,
        required=("schema", "run_id", "summary"),
        label="model result",
        code="invalid-model-result",
    )
    if value["schema"] != MODEL_RESULT_SCHEMA_VERSION:
        _fail("invalid-model-result", "model result schema is unsupported")
    if value["run_id"] != run_id:
        _fail("invalid-model-result", "model result Run ID does not match")
    summary = value["summary"]
    if not isinstance(summary, str) or len(summary) > 2000:
        _fail("invalid-model-result", "model summary is invalid")
    return {
        "schema": MODEL_RESULT_SCHEMA_VERSION,
        "run_id": run_id,
        "summary": summary.strip(),
    }


def assemble_external_sync_result(
    manifest: Mapping[str, Any],
    target_results: List[dict],
    model_result: Mapping[str, Any],
) -> dict:
    validated_model = validate_model_result(model_result, manifest["run_id"])
    return {
        "schema": RESULT_SCHEMA_VERSION,
        "run_id": manifest["run_id"],
        "source": dict(manifest["source"]),
        "scope": dict(manifest["scope"]),
        "read_policy_version": manifest["read_policy_version"],
        "status": derive_run_status(target_results),
        "targets": target_results,
        "summary": validated_model["summary"],
    }
