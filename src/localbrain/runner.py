import asyncio
import hashlib
import json
import logging
import os
import shlex
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from .config import settings
from .atlassian_refresh import (
    apply_atlassian_refresh_result,
    is_atlassian_refresh_manifest,
)
from .db import connect, transaction
from .external_sync import (
    EXTERNAL_SYNC_TASK,
    MODEL_RESULT_SCHEMA,
    ExternalReadExecutor,
    ExternalSyncError,
    assemble_external_sync_result,
    build_external_sync_prompt,
    collect_external_sync_evidence,
    load_external_sync_manifest,
)
from .ingest.scanner import scan_claude_sessions, scan_codex_sessions
from .retrieval import build_candidate_bundle, write_candidate_evidence
from .workstreams import get_workstream, utc_now


TASK_DEFINITIONS = {
    "organize_resources": {
        "label": "자원 연결 정리",
        "description": "LocalBrain 후보를 검토하고 MCP로 누락된 외부 근거를 보충합니다.",
        "instruction": (
            "LocalBrain이 추린 세션, 문서, 프로젝트와 evidence를 먼저 검토하고 Thread별 "
            "연결을 정리하라. 그 뒤 필요한 Jira, Slack, Wiki, Git 근거만 MCP로 보충하라."
        ),
    },
    "checkpoint_draft": {
        "label": "Checkpoint 초안",
        "description": "확정된 근거를 바탕으로 현재 목표와 다음 행동 초안을 만듭니다.",
        "instruction": (
            "연결된 근거와 최근 활동을 바탕으로 현재 목표, 확정 사실, 최근 결정, "
            "열린 질문, 다음 행동과 다시 열 파일의 초안을 작성하라."
        ),
    },
    "priority_review": {
        "label": "우선순위 검토",
        "description": "활성 Thread의 진행 상태와 지금 처리할 순서를 검토합니다.",
        "instruction": (
            "활성 또는 중단된 Thread를 비교해 우선순위, 선행 조건, 위험과 다음 행동을 제안하라."
        ),
    },
}


RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "resource_suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "target_thread_id": {"type": ["integer", "null"]},
                    "resource_type": {
                        "type": "string",
                        "enum": [
                            "local_path",
                            "session",
                            "document",
                            "project",
                            "jira",
                            "wiki",
                            "slack",
                            "git",
                            "url",
                        ],
                    },
                    "locator": {"type": "string"},
                    "title": {"type": "string"},
                    "relation_type": {"type": "string"},
                    "rationale": {"type": "string"},
                    "evidence": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": [
                    "target_thread_id",
                    "resource_type",
                    "locator",
                    "title",
                    "relation_type",
                    "rationale",
                    "evidence",
                    "confidence",
                ],
            },
        },
        "checkpoint_draft": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "current_goal": {"type": "string"},
                "confirmed_facts": {"type": "string"},
                "recent_decisions": {"type": "string"},
                "open_questions": {"type": "string"},
                "next_actions": {"type": "string"},
                "files_to_open": {"type": "string"},
            },
            "required": [
                "current_goal",
                "confirmed_facts",
                "recent_decisions",
                "open_questions",
                "next_actions",
                "files_to_open",
            ],
        },
        "priority_review": {"type": "string"},
    },
    "required": [
        "summary",
        "resource_suggestions",
        "checkpoint_draft",
        "priority_review",
    ],
}


_tasks: Dict[str, asyncio.Task] = {}
_processes: Dict[str, asyncio.subprocess.Process] = {}
logger = logging.getLogger(__name__)


def runner_command_args(executable: str = "claude") -> List[str]:
    return [
        executable,
        "--print",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        "plan",
        "--json-schema",
        json.dumps(RESULT_SCHEMA, ensure_ascii=True, separators=(",", ":")),
    ]


def runner_command_preview() -> str:
    return shlex.join(runner_command_args())


def runner_executable(runner: str = "claude") -> Optional[str]:
    if runner not in {"claude", "codex"}:
        return None
    configured = os.environ.get(
        "LOCALBRAIN_CLAUDE_BIN" if runner == "claude" else "LOCALBRAIN_CODEX_BIN"
    )
    if configured:
        path = Path(configured).expanduser()
        return str(path) if path.is_file() else None
    return shutil.which(runner)


def external_runner_command_args(
    runner: str,
    executable: str,
    run_root: Path,
) -> List[str]:
    if runner == "claude":
        return [
            executable,
            "--print",
            "--output-format",
            "stream-json",
            "--verbose",
            "--permission-mode",
            "plan",
            "--tools",
            "",
            "--strict-mcp-config",
            "--mcp-config",
            str(run_root / "empty-mcp.json"),
            "--json-schema",
            json.dumps(
                MODEL_RESULT_SCHEMA,
                ensure_ascii=True,
                separators=(",", ":"),
            ),
        ]
    if runner == "codex":
        return [
            executable,
            "exec",
            "--json",
            "--ignore-user-config",
            "--ignore-rules",
            "-c",
            'default_permissions="external-sync"',
            "-c",
            'permissions.external-sync.filesystem={":minimal"="read",'
            '":workspace_roots"={"."="read"}}',
            "-c",
            "permissions.external-sync.network.enabled=false",
            "-c",
            'web_search="disabled"',
            "-c",
            'shell_environment_policy.inherit="none"',
            "--skip-git-repo-check",
            "-C",
            str(run_root),
            "--output-schema",
            str(run_root / "model-result-schema.json"),
            "--output-last-message",
            str(run_root / "model-result.json"),
            "-",
        ]
    raise ValueError("Unsupported external sync runner")


def task_choices() -> List[dict]:
    return [
        {
            "value": key,
            "label": value["label"],
            "description": value["description"],
            "instruction": value["instruction"],
        }
        for key, value in TASK_DEFINITIONS.items()
    ]


def _resource_manifest(connection, link: dict) -> Optional[dict]:
    entity_type = link["entity_type"]
    entity_id = str(link.get("resource_id") or link.get("entity_id"))
    base = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "relation_type": link.get("relation_type"),
        "title": link.get("title"),
    }
    if entity_type == "session":
        row = connection.execute(
            """
            SELECT sessions.title, sessions.source_path, sessions.cwd_raw,
                   sessions.git_branch,
                   sessions.last_event_at, sources.kind AS source_kind
            FROM sessions JOIN sources ON sources.id = sessions.source_id
            WHERE sessions.id = ? AND sessions.session_class = 'work'
              AND sessions.session_role = 'primary'
            """,
            (entity_id,),
        ).fetchone()
    elif entity_type == "document":
        row = connection.execute(
            "SELECT title, path, relative_path FROM context_documents WHERE id = ?",
            (entity_id,),
        ).fetchone()
    elif entity_type == "project":
        row = connection.execute(
            """
            SELECT display_name AS title, canonical_path, git_root,
                   exists_now, last_activity_at
            FROM workspaces WHERE id = ?
            """,
            (entity_id,),
        ).fetchone()
    elif entity_type == "external":
        row = connection.execute(
            """
            SELECT title, resource_type, url, summary, source_role
            FROM external_resources WHERE id = ?
            """,
            (entity_id,),
        ).fetchone()
    else:
        row = connection.execute(
            """
            SELECT title, resource_type, path, summary, exists_now, discovered_by
            FROM local_resources WHERE id = ?
            """,
            (entity_id,),
        ).fetchone()
    if entity_type == "session" and not row:
        return None
    if row:
        base.update(dict(row))
    return base


def _resource_manifests(connection, links: List[dict]) -> List[dict]:
    resources = []
    for link in links:
        resource = _resource_manifest(connection, link)
        if resource is not None:
            resources.append(resource)
    return resources


def _pending_suggestion_manifest(suggestion: dict) -> dict:
    try:
        payload = json.loads(suggestion.get("payload_json") or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "id": suggestion["id"],
        "suggestion_type": suggestion["suggestion_type"],
        "target_type": suggestion["target_type"],
        "target_id": suggestion["target_id"],
        "title": suggestion["title"],
        "description": suggestion.get("description"),
        "rationale": suggestion.get("rationale"),
        "payload": payload,
        "origin_run_id": suggestion.get("origin_run_id"),
    }


def _previous_analysis(
    connection, workstream_id: int, task_type: str, fingerprint: str
) -> Optional[dict]:
    rows = connection.execute(
        """
        SELECT id, completed_at, source_snapshot_json, structured_result_json
        FROM maintenance_runs
        WHERE workstream_id = ? AND task_type = ? AND status = 'completed'
          AND structured_result_json IS NOT NULL
        ORDER BY completed_at DESC LIMIT 8
        """,
        (workstream_id, task_type),
    ).fetchall()
    for row in rows:
        try:
            snapshot = json.loads(row["source_snapshot_json"] or "{}")
            previous_fingerprint = snapshot.get("retrieval", {}).get("fingerprint")
            result = json.loads(row["structured_result_json"] or "{}")
        except json.JSONDecodeError:
            continue
        if previous_fingerprint == fingerprint:
            return {
                "local_candidate_snapshot_unchanged": True,
                "run_id": row["id"],
                "completed_at": row["completed_at"],
                "structured_result": result,
            }
    return None


def build_manifest(
    connection,
    workstream_id: int,
    run_id: str,
    task_type: str = "organize_resources",
    candidate_bundle: Optional[dict] = None,
    refresh_suggestions: bool = False,
) -> dict:
    workstream = get_workstream(connection, workstream_id)
    if not workstream:
        raise LookupError("Workstream not found")
    candidates = candidate_bundle or build_candidate_bundle(connection, workstream)
    previous_analysis = _previous_analysis(
        connection, workstream_id, task_type, candidates["fingerprint"]
    )
    return {
        "schema": "localbrain.maintenance-context.v2",
        "run_id": run_id,
        "generated_at": utc_now(),
        "execution_root": str(Path.home()),
        "workstream": {
            "id": workstream["id"],
            "name": workstream["name"],
            "status": workstream["status"],
            "summary": workstream.get("summary"),
            "checkpoint": workstream.get("checkpoint"),
            "resources": _resource_manifests(connection, workstream["links"]),
        },
        "threads": [
            {
                "id": thread["id"],
                "title": thread["title"],
                "status": thread["status"],
                "summary": thread.get("summary"),
                "current_goal": thread.get("current_goal"),
                "next_action": thread.get("next_action"),
                "resources": _resource_manifests(connection, thread["links"]),
            }
            for thread in workstream["threads"]
        ],
        "retrieval": {
            "policy": candidates["policy"],
            "fingerprint": candidates["fingerprint"],
            "counts": candidates["counts"],
            "evidence_root": candidates.get("evidence_root"),
        },
        "candidate_resources": candidates["candidate_resources"],
        "thread_resource_matches": candidates["thread_resource_matches"],
        "pending_suggestions": [
            _pending_suggestion_manifest(suggestion)
            for suggestion in workstream["suggestions"]
        ],
        "suggestion_refresh": {
            "enabled": refresh_suggestions,
            "behavior": (
                "Replace pending Claude Run suggestions after this run succeeds. "
                "Rejected and accepted suggestions keep their status."
                if refresh_suggestions
                else "Merge this run's output with pending suggestions."
            ),
        },
        "previous_analysis": previous_analysis,
        "external_discovery": {
            "mode": "mcp-gap-fill-only",
            "requested_sources": ["jira", "slack", "wiki", "git"],
            "mcp_call_budget": settings.mcp_call_budget,
            "budget_scope": "this maintenance run",
            "enforcement": "prompt-and-stream-audit",
            "cache_rule": (
                "Do not re-query connected resources, pending suggestions, or unchanged "
                "previous analysis unless freshness is material to the task."
            ),
        },
    }


def build_prompt(
    run_id: str,
    task_type: str,
    manifest_path: Path,
    extra_instruction: Optional[str] = None,
    refresh_suggestions: bool = False,
) -> str:
    if task_type not in TASK_DEFINITIONS:
        raise ValueError("Unsupported task type")
    extra = (extra_instruction or "").strip()
    extra_block = "\n\n추가 요청:\n{}".format(extra) if extra else ""
    refresh_instruction = (
        "- 이 실행은 제안 갱신 모드다. 기존 pending_suggestions를 참고하되 현재 근거로 다시 "
        "판단해 유지할 항목도 결과에 포함하라. 성공 후 결과에 없는 기존 Claude 제안은 교체된다."
        if refresh_suggestions
        else "- 이 실행의 결과는 현재 pending_suggestions와 병합된다. 중복 후보를 만들지 마라."
    )
    return """[LOCALBRAIN_RUN: {run_id}]
[MODE: maintenance]

너는 LocalBrain의 Workstream 유지관리 Task Runner다. 이 실행은 일반 개발 세션이
아니며, 기존 자원을 복제하지 않고 변경점과 연결 후보만 정리해야 한다.

실행 원칙:
- 이 작업은 읽기 전용이다. 파일, Git, 티켓, 문서, Slack 등 외부 자원을 수정하지 마라.
- 먼저 manifest의 candidate_resources와 thread_resource_matches를 검토하라. 이는 LocalBrain이
  SQLite/FTS로 계산한 로컬 후보이며 후보 수와 evidence 수에는 하드 제한이 없다.
- candidate_resources의 Session은 `session_class=work`, `session_role=primary`만 포함한다.
  maintenance Session, subsession, 현재 또는 이전 Claude Run과 그 subagent 실행을 후보 근거나
  새 자원으로 다시 포함하지 마라.
- evidence 본문은 각 candidate의 evidence_path에 분리되어 있다. 관계 판단에 필요한 자원의
  evidence만 열고 같은 파일을 반복해서 읽지 마라.
- 로컬 세션과 문서를 다시 광범위하게 탐색하지 마라. 후보에 명백한 공백이 있을 때만 해당
  경로를 추가 탐색하고, 결과 rationale에 탐색 이유를 남겨라.
- main agent가 전체 판단을 유지하고 subagent는 광범위한 탐색이 필요할 때만 사용하라.
- 추측은 확정 사실과 구분하고 모든 제안에 파일 경로, LocalBrain ID 또는 URL 근거를 붙여라.
- 구체적인 자원은 가장 관련 있는 Thread에 우선 배정하라. 여러 Thread가 공동으로 사용하는
  자원만 target_thread_id를 null로 두어 Workstream 공통 자원으로 제안하라.
- 이미 manifest에 연결된 자원을 중복 제안하지 마라.
- session, document, project는 LocalBrain의 숫자 ID를 locator 문자열로 사용하라.
- Slack/Jira/Wiki/Git은 다시 열 수 있는 URL을 locator로 사용하고, 확인한 메시지나 판단
  근거는 evidence에 요약하라.
- MCP는 로컬 후보에서 해결되지 않은 외부 공백을 채울 때만 사용하고 이 Run에서 최대
  {mcp_call_budget}회 호출하라. 동일 검색과 동일 자원 조회를 반복하지 마라.
- previous_analysis는 후보 근거가 아니라 동일한 로컬 후보 snapshot의 이전 분석 cache다.
  local_candidate_snapshot_unchanged가 true이면 이전 판단을 재사용하고, 변경되었거나 stale
  여부가 중요한 외부 근거만 다시 확인하라.
{refresh_instruction}

Context manifest:
{manifest_path}

실행 작업:
{task_instruction}{extra_block}

결과는 제공된 JSON Schema를 따르는 한국어 구조화 데이터로 반환하라. Checkpoint를
제안할 근거가 부족한 필드는 빈 문자열로 두고, 발견한 자원이 없으면 resource_suggestions를
빈 배열로 반환하라.
""".format(
        run_id=run_id,
        manifest_path=manifest_path,
        task_instruction=TASK_DEFINITIONS[task_type]["instruction"],
        extra_block=extra_block,
        mcp_call_budget=settings.mcp_call_budget,
        refresh_instruction=refresh_instruction,
    )


def prepare_run(
    connection,
    workstream_id: int,
    task_type: str,
    extra_instruction: Optional[str] = None,
    run_root: Optional[Path] = None,
    refresh_suggestions: bool = False,
) -> str:
    if task_type not in TASK_DEFINITIONS:
        raise ValueError("Unsupported task type")
    run_id = "lb-{}".format(uuid.uuid4().hex[:12])
    root = (run_root or (settings.data_dir / "runs")) / run_id
    root.mkdir(parents=True, exist_ok=False)
    workstream = get_workstream(connection, workstream_id)
    if not workstream:
        raise LookupError("Workstream not found")
    candidates = write_candidate_evidence(
        build_candidate_bundle(connection, workstream), root
    )
    manifest = build_manifest(
        connection,
        workstream_id,
        run_id,
        task_type,
        candidates,
        refresh_suggestions,
    )
    manifest_path = root / "manifest.json"
    prompt_path = root / "prompt.md"
    stream_path = root / "stream.jsonl"
    result_path = root / "result.md"
    stderr_path = root / "stderr.log"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    prompt_path.write_text(
        build_prompt(
            run_id,
            task_type,
            manifest_path,
            extra_instruction,
            refresh_suggestions,
        ),
        encoding="utf-8",
    )
    now = utc_now()
    connection.execute(
        """
        INSERT INTO maintenance_runs(
            id, workstream_id, task_type, runner, cwd, status,
            source_snapshot_json, manifest_path, prompt_path, stream_path,
            result_path, stderr_path, refresh_suggestions, mcp_call_budget, updated_at
        ) VALUES (?, ?, ?, 'claude', ?, 'queued', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            workstream_id,
            task_type,
            str(Path.home()),
            json.dumps(manifest, ensure_ascii=False),
            str(manifest_path),
            str(prompt_path),
            str(stream_path),
            str(result_path),
            str(stderr_path),
            int(refresh_suggestions),
            settings.mcp_call_budget,
            now,
        ),
    )
    return run_id


def list_runs(connection, workstream_id: int, limit: int = 12):
    return connection.execute(
        """
        SELECT maintenance_runs.*, workstreams.name AS workstream_name
        FROM maintenance_runs
        LEFT JOIN workstreams ON workstreams.id = maintenance_runs.workstream_id
        WHERE maintenance_runs.workstream_id = ?
          AND maintenance_runs.task_type IS NOT NULL
        ORDER BY maintenance_runs.created_at DESC
        LIMIT ?
        """,
        (workstream_id, limit),
    ).fetchall()


def get_run(connection, run_id: str):
    return connection.execute(
        """
        SELECT maintenance_runs.*, workstreams.name AS workstream_name
        FROM maintenance_runs
        LEFT JOIN workstreams ON workstreams.id = maintenance_runs.workstream_id
        WHERE maintenance_runs.id = ?
        """,
        (run_id,),
    ).fetchone()


def read_run_output(run) -> str:
    if not run:
        return ""
    result_path = run["result_path"]
    if result_path and Path(result_path).is_file():
        return Path(result_path).read_text(encoding="utf-8", errors="replace")
    stderr_path = run["stderr_path"]
    if stderr_path and Path(stderr_path).is_file():
        return Path(stderr_path).read_text(encoding="utf-8", errors="replace")
    return ""


def reconcile_interrupted_runs() -> int:
    with transaction() as connection:
        now = utc_now()
        rows = connection.execute(
            """
            SELECT id, runner FROM maintenance_runs
            WHERE status IN ('queued', 'running', 'cancelling')
              AND task_type IS NOT NULL AND stream_path IS NOT NULL
            """
        ).fetchall()
        for row in rows:
            _update_run_row(
                connection,
                row["id"],
                status="interrupted",
                pid=None,
                completed_at=now,
                error="LocalBrain restarted while the run was active.",
            )
        count = len(rows)
    for runner in sorted({row["runner"] for row in rows}):
        _sync_native_runner_sessions(runner)
    return count


def start_run(
    run_id: str,
    external_executor: Optional[ExternalReadExecutor] = None,
) -> None:
    task = asyncio.create_task(_execute_run(run_id, external_executor))
    _tasks[run_id] = task
    task.add_done_callback(lambda _task: _tasks.pop(run_id, None))


def _update_run_row(connection, run_id: str, **values) -> None:
    if not values:
        return
    values["updated_at"] = utc_now()
    assignments = ", ".join("{} = ?".format(key) for key in values)
    connection.execute(
        "UPDATE maintenance_runs SET {} WHERE id = ?".format(assignments),
        tuple(values.values()) + (run_id,),
    )


def _update_run(run_id: str, **values) -> None:
    if not values:
        return
    with transaction() as connection:
        _update_run_row(connection, run_id, **values)


def _sync_native_claude_sessions() -> bool:
    try:
        scan_claude_sessions()
    except Exception:
        logger.exception("Claude Session synchronization failed after a Task Runner run")
        return False
    return True


def _sync_native_codex_sessions() -> bool:
    try:
        scan_codex_sessions()
    except Exception:
        logger.exception("Codex Session synchronization failed after a Task Runner run")
        return False
    return True


def _sync_native_runner_sessions(runner: str) -> bool:
    if runner == "codex":
        return _sync_native_codex_sessions()
    return _sync_native_claude_sessions()


def _finalize_run(
    run_id: str,
    status: str,
    *,
    runner: str = "claude",
    **values,
) -> None:
    completed_at = values.pop("completed_at", None) or utc_now()
    with transaction() as connection:
        _update_run_row(
            connection,
            run_id,
            status=status,
            completed_at=completed_at,
            **values,
        )
    _sync_native_runner_sessions(runner)


def _finalize_failed_run(
    run_id: str,
    error: str,
    *,
    runner: str = "claude",
) -> None:
    try:
        _finalize_run(
            run_id,
            "failed",
            runner=runner,
            pid=None,
            error=error[-4000:],
        )
    except Exception as finalization_error:
        _update_run(
            run_id,
            status="failed",
            pid=None,
            completed_at=utc_now(),
            error=("{} · Run finalization failed: {}".format(error, finalization_error))[
                -4000:
            ],
        )


def _extract_text(event: dict) -> Optional[str]:
    if event.get("type") == "assistant":
        message = event.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            chunks = [
                item.get("text", "").strip()
                for item in content
                if isinstance(item, dict)
                and item.get("type") == "text"
                and isinstance(item.get("text"), str)
                and item.get("text", "").strip()
            ]
            return "\n\n".join(chunks) or None
    if event.get("type") == "result" and isinstance(event.get("result"), str):
        return event["result"].strip() or None
    return None


def _extract_tool_uses(event: dict) -> List[dict]:
    if event.get("type") != "assistant":
        return []
    message = event.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return []
    return [
        {"id": item.get("id"), "name": item.get("name")}
        for item in content
        if isinstance(item, dict)
        and item.get("type") == "tool_use"
        and isinstance(item.get("name"), str)
    ]


def _is_mcp_tool(name: str) -> bool:
    lowered = name.lower()
    return lowered.startswith("mcp__") or lowered.startswith("mcp_")


def _structured_result(event: Optional[dict]) -> Optional[dict]:
    if not event:
        return None
    value = event.get("structured_output")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    result = event.get("result")
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def render_structured_result(result: dict) -> str:
    lines = ["# 실행 결과", "", result.get("summary") or "요약이 없습니다."]
    suggestions = result.get("resource_suggestions") or []
    lines.extend(["", "## 자원 연결 제안"])
    if suggestions:
        for item in suggestions:
            target = (
                "Thread #{}".format(item.get("target_thread_id"))
                if item.get("target_thread_id") is not None
                else "Workstream 공통"
            )
            lines.extend(
                [
                    "",
                    "- **{}** · {} · {}".format(
                        item.get("title") or item.get("locator"),
                        item.get("resource_type"),
                        target,
                    ),
                    "  - 위치: `{}`".format(item.get("locator") or "-"),
                    "  - 근거: {}".format(item.get("evidence") or item.get("rationale") or "-"),
                ]
            )
    else:
        lines.append("")
        lines.append("발견된 자원 연결 제안이 없습니다.")

    draft = result.get("checkpoint_draft") or {}
    lines.extend(["", "## Checkpoint 초안"])
    labels = (
        ("current_goal", "현재 목표"),
        ("confirmed_facts", "확정 사실"),
        ("recent_decisions", "최근 결정"),
        ("open_questions", "열린 질문"),
        ("next_actions", "다음 행동"),
        ("files_to_open", "다시 열 파일"),
    )
    populated = False
    for key, label in labels:
        value = (draft.get(key) or "").strip()
        if value:
            populated = True
            lines.extend(["", "### {}".format(label), value])
    if not populated:
        lines.extend(["", "Checkpoint 변경 제안이 없습니다."])
    lines.extend(["", "## 우선순위 검토", "", result.get("priority_review") or "검토 내용이 없습니다."])
    return "\n".join(lines).strip() + "\n"


def persist_structured_suggestions(
    connection, run_id: str, workstream_id: int, result: dict
) -> int:
    valid_threads = {
        row["id"]
        for row in connection.execute(
            "SELECT id FROM threads WHERE workstream_id = ?", (workstream_id,)
        ).fetchall()
    }
    created = 0
    for item in result.get("resource_suggestions") or []:
        locator = str(item.get("locator") or "").strip()
        resource_type = str(item.get("resource_type") or "").strip()
        if not locator or resource_type not in {
            "local_path", "session", "document", "project", "jira", "wiki",
            "slack", "git", "url",
        }:
            continue
        thread_id = item.get("target_thread_id")
        if thread_id is None:
            target_type, target_id = "workstream", workstream_id
        elif thread_id in valid_threads:
            target_type, target_id = "thread", int(thread_id)
        else:
            continue
        normalized_locator = (
            str(Path(locator).expanduser()) if resource_type == "local_path" else locator
        )
        fingerprint = hashlib.sha256(
            "runner-resource:{}:{}:{}:{}".format(
                target_type, target_id, resource_type, normalized_locator.lower()
            ).encode("utf-8")
        ).hexdigest()
        payload = {
            "resource_type": resource_type,
            "locator": normalized_locator,
            "title": (item.get("title") or normalized_locator).strip(),
            "relation_type": (item.get("relation_type") or "related-to").strip(),
            "rationale": (item.get("rationale") or "").strip(),
            "evidence": (item.get("evidence") or "").strip(),
        }
        confidence = max(0.0, min(1.0, float(item.get("confidence") or 0)))
        rationale = payload["rationale"]
        if payload["evidence"] and payload["evidence"] != rationale:
            rationale = "{} · 근거: {}".format(
                rationale or "연결 근거", payload["evidence"]
            )
        connection.execute(
            """
            INSERT INTO suggestions(
                suggestion_type, target_type, target_id, title, description,
                rationale, payload_json, fingerprint, origin_run_id, confidence
            ) VALUES ('resource_link', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                rationale = excluded.rationale,
                payload_json = excluded.payload_json,
                origin_run_id = excluded.origin_run_id,
                confidence = excluded.confidence,
                status = CASE
                    WHEN suggestions.status IN ('accepted', 'rejected')
                    THEN suggestions.status ELSE 'pending' END,
                resolved_at = CASE
                    WHEN suggestions.status IN ('accepted', 'rejected')
                    THEN suggestions.resolved_at ELSE NULL END
            """,
            (
                target_type,
                target_id,
                payload["title"],
                normalized_locator,
                rationale,
                json.dumps(payload, ensure_ascii=False),
                fingerprint,
                run_id,
                confidence,
            ),
        )
        current = connection.execute(
            "SELECT status, origin_run_id FROM suggestions WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone()
        created += int(
            current and current["status"] == "pending"
            and current["origin_run_id"] == run_id
        )

    checkpoint = result.get("checkpoint_draft") or {}
    checkpoint = {
        key: str(checkpoint.get(key) or "").strip()
        for key in (
            "current_goal", "confirmed_facts", "recent_decisions",
            "open_questions", "next_actions", "files_to_open",
        )
    }
    if any(checkpoint.values()):
        encoded = json.dumps(checkpoint, ensure_ascii=False, sort_keys=True)
        fingerprint = hashlib.sha256(
            "runner-checkpoint:{}:{}".format(workstream_id, encoded).encode("utf-8")
        ).hexdigest()
        connection.execute(
            """
            INSERT INTO suggestions(
                suggestion_type, target_type, target_id, title, description,
                rationale, payload_json, fingerprint, origin_run_id, confidence
            ) VALUES ('checkpoint_draft', 'workstream', ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                rationale = excluded.rationale,
                payload_json = excluded.payload_json,
                origin_run_id = excluded.origin_run_id,
                confidence = excluded.confidence,
                status = CASE
                    WHEN suggestions.status IN ('accepted', 'rejected')
                    THEN suggestions.status ELSE 'pending' END,
                resolved_at = CASE
                    WHEN suggestions.status IN ('accepted', 'rejected')
                    THEN suggestions.resolved_at ELSE NULL END
            """,
            (
                workstream_id,
                "Checkpoint 초안",
                checkpoint.get("current_goal"),
                "Claude Task Runner가 연결 자원과 최근 상태를 바탕으로 작성했습니다.",
                json.dumps(checkpoint, ensure_ascii=False),
                fingerprint,
                run_id,
                0.7,
            ),
        )
        current = connection.execute(
            "SELECT status, origin_run_id FROM suggestions WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone()
        created += int(
            current and current["status"] == "pending"
            and current["origin_run_id"] == run_id
        )
    return created


def supersede_runner_suggestions(
    connection, workstream_id: int
) -> int:
    now = utc_now()
    cursor = connection.execute(
        """
        UPDATE suggestions
        SET status = 'superseded', resolved_at = ?
        WHERE status = 'pending' AND origin_run_id IS NOT NULL
          AND ((target_type = 'workstream' AND target_id = ?)
               OR (target_type = 'thread' AND target_id IN
                   (SELECT id FROM threads WHERE workstream_id = ?)))
        """,
        (now, workstream_id, workstream_id),
    )
    return cursor.rowcount


async def _consume_stdout(
    run_id: str,
    stream,
    stream_path: Path,
    result_path: Path,
    mcp_call_budget: int,
):
    chunks: List[str] = []
    final_event = None
    mcp_calls: List[dict] = []
    seen_tool_uses = set()
    with stream_path.open("a", encoding="utf-8") as raw:
        while True:
            line = await stream.readline()
            if not line:
                break
            decoded = line.decode("utf-8", errors="replace").rstrip("\n")
            raw.write(decoded + "\n")
            raw.flush()
            try:
                event = json.loads(decoded)
            except json.JSONDecodeError:
                continue
            for tool_use in _extract_tool_uses(event):
                identity = tool_use.get("id") or "{}:{}".format(
                    tool_use.get("name"), len(seen_tool_uses)
                )
                if identity in seen_tool_uses:
                    continue
                seen_tool_uses.add(identity)
                if not _is_mcp_tool(tool_use["name"]):
                    continue
                mcp_calls.append(tool_use)
                _update_run(
                    run_id,
                    mcp_calls_used=len(mcp_calls),
                    mcp_tool_calls_json=json.dumps(mcp_calls, ensure_ascii=False),
                    mcp_budget_exceeded=int(len(mcp_calls) > mcp_call_budget),
                )
            text = _extract_text(event)
            if event.get("type") == "result":
                final_event = event
                if text:
                    chunks = [text]
            elif text and text not in chunks:
                chunks.append(text)
            if chunks:
                result_path.write_text("\n\n".join(chunks), encoding="utf-8")
    return final_event, "\n\n".join(chunks), mcp_calls


async def _consume_stderr(stream, stderr_path: Path) -> str:
    chunks = []
    with stderr_path.open("a", encoding="utf-8") as output:
        while True:
            line = await stream.readline()
            if not line:
                break
            decoded = line.decode("utf-8", errors="replace")
            output.write(decoded)
            output.flush()
            chunks.append(decoded)
    return "".join(chunks)


async def _consume_external_stdout(stream, stream_path: Path):
    final_event = None
    with stream_path.open("a", encoding="utf-8") as raw:
        while True:
            line = await stream.readline()
            if not line:
                break
            decoded = line.decode("utf-8", errors="replace").rstrip("\n")
            raw.write(decoded + "\n")
            raw.flush()
            try:
                event = json.loads(decoded)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "result":
                final_event = event
    return final_event


def _external_model_result(run, final_event) -> Optional[dict]:
    if run["runner"] == "claude":
        return _structured_result(final_event)
    model_result_path = Path(run["manifest_path"]).parent / "model-result.json"
    if not model_result_path.is_file():
        return None
    try:
        value = json.loads(model_result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def render_external_sync_result(result: dict) -> str:
    lines = [
        "# External synchronization result",
        "",
        result.get("summary") or "No runner summary was provided.",
        "",
        "## Targets",
    ]
    for target in result.get("targets") or []:
        lines.append(
            "- `{}`: `{}`".format(target["target_id"], target["outcome"])
        )
    return "\n".join(lines).strip() + "\n"


async def _execute_external_sync_run(
    run_id: str,
    run,
    executor: Optional[ExternalReadExecutor],
) -> None:
    runner = run["runner"]
    if executor is None:
        _finalize_failed_run(
            run_id,
            "External synchronization requires an approved read executor.",
            runner=runner,
        )
        return
    with connect() as connection:
        manifest, dispatches = load_external_sync_manifest(connection, run)
    run_root = Path(run["manifest_path"]).parent
    evidence_path = run_root / "evidence.json"
    started_at = utc_now()
    _update_run(
        run_id,
        status="running",
        pid=None,
        started_at=started_at,
        error=None,
    )

    def on_call(call_log: List[dict]) -> None:
        _update_run(
            run_id,
            mcp_calls_used=len(call_log),
            mcp_tool_calls_json=json.dumps(call_log, ensure_ascii=False),
            mcp_budget_exceeded=int(
                len(call_log) > (run["mcp_call_budget"] or 0)
            ),
        )

    target_results, call_log = await collect_external_sync_evidence(
        manifest,
        dispatches,
        executor,
        on_call=on_call,
    )
    evidence = {
        "schema": "localbrain.external-sync-evidence.v1",
        "run_id": run_id,
        "targets": target_results,
    }
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    executable = runner_executable(runner)
    if not executable:
        _finalize_failed_run(
            run_id,
            "{} executable was not found.".format(runner.capitalize()),
            runner=runner,
        )
        return
    prompt = build_external_sync_prompt(
        run_id,
        Path(run["manifest_path"]),
        evidence_path,
        manifest=manifest,
        evidence=evidence,
    )
    Path(run["prompt_path"]).write_text(prompt, encoding="utf-8")
    process = await asyncio.create_subprocess_exec(
        *external_runner_command_args(runner, executable, run_root),
        cwd=str(run_root),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, "LOCALBRAIN_RUN_ID": run_id},
    )
    _processes[run_id] = process
    _update_run(run_id, pid=process.pid)
    process.stdin.write(prompt.encode("utf-8"))
    await process.stdin.drain()
    process.stdin.close()
    stdout_task = asyncio.create_task(
        _consume_external_stdout(process.stdout, Path(run["stream_path"]))
    )
    stderr_task = asyncio.create_task(
        _consume_stderr(process.stderr, Path(run["stderr_path"]))
    )
    return_code = await process.wait()
    final_event, stderr = await asyncio.gather(stdout_task, stderr_task)
    with connect() as connection:
        current = get_run(connection, run_id)
    if current and current["status"] in {"cancelling", "cancelled"}:
        _finalize_run(
            run_id,
            "cancelled",
            runner=runner,
            pid=None,
        )
        return
    if return_code != 0:
        _finalize_failed_run(
            run_id,
            (
                "{} external synchronization process failed with exit code {}. "
                "See the private stderr artifact."
            ).format(runner.capitalize(), return_code),
            runner=runner,
        )
        return
    model_result = _external_model_result(run, final_event)
    if model_result is None:
        raise ExternalSyncError(
            "invalid-model-result",
            "External synchronization runner returned no structured result.",
        )
    result = assemble_external_sync_result(
        manifest,
        target_results,
        model_result,
    )
    output = render_external_sync_result(result)
    Path(run["result_path"]).write_text(output, encoding="utf-8")
    with transaction() as connection:
        if is_atlassian_refresh_manifest(manifest):
            apply_atlassian_refresh_result(
                connection,
                manifest=manifest,
                result=result,
            )
        _update_run_row(
            connection,
            run_id,
            status=result["status"],
            pid=None,
            completed_at=utc_now(),
            summary=(result["summary"] or output)[:2000],
            structured_result_json=json.dumps(result, ensure_ascii=False),
            mcp_calls_used=len(call_log),
            mcp_tool_calls_json=json.dumps(call_log, ensure_ascii=False),
            mcp_budget_exceeded=int(
                len(call_log) > (run["mcp_call_budget"] or 0)
            ),
        )
    _sync_native_runner_sessions(runner)


async def _execute_run(
    run_id: str,
    external_executor: Optional[ExternalReadExecutor] = None,
) -> None:
    process = None
    runner = "claude"
    try:
        with connect() as connection:
            run = get_run(connection, run_id)
        if not run:
            return
        runner = run["runner"]
        if run["task_type"] == EXTERNAL_SYNC_TASK:
            await _execute_external_sync_run(run_id, run, external_executor)
            return
        executable = runner_executable()
        if not executable:
            _finalize_failed_run(run_id, "Claude executable was not found.")
            return
        prompt = Path(run["prompt_path"]).read_text(encoding="utf-8")
        process = await asyncio.create_subprocess_exec(
            *runner_command_args(executable),
            cwd=run["cwd"],
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "LOCALBRAIN_RUN_ID": run_id},
        )
        _processes[run_id] = process
        started_at = utc_now()
        with transaction() as connection:
            _update_run_row(
                connection,
                run_id,
                status="running",
                pid=process.pid,
                started_at=started_at,
                error=None,
            )
        process.stdin.write(prompt.encode("utf-8"))
        await process.stdin.drain()
        process.stdin.close()

        stdout_task = asyncio.create_task(
            _consume_stdout(
                run_id,
                process.stdout,
                Path(run["stream_path"]),
                Path(run["result_path"]),
                run["mcp_call_budget"] or 0,
            )
        )
        stderr_task = asyncio.create_task(
            _consume_stderr(process.stderr, Path(run["stderr_path"]))
        )
        return_code = await process.wait()
        (final_event, output, mcp_calls), stderr = await asyncio.gather(
            stdout_task, stderr_task
        )
        with connect() as connection:
            current = get_run(connection, run_id)
        if current and current["status"] in {"cancelling", "cancelled"}:
            _finalize_run(run_id, "cancelled", pid=None)
        elif return_code == 0:
            structured = _structured_result(final_event)
            suggestions_created = 0
            if structured:
                output = render_structured_result(structured)
                Path(run["result_path"]).write_text(output, encoding="utf-8")
            completed_at = utc_now()
            with transaction() as connection:
                if structured:
                    if run["refresh_suggestions"]:
                        supersede_runner_suggestions(
                            connection, run["workstream_id"]
                        )
                    suggestions_created = persist_structured_suggestions(
                        connection, run_id, run["workstream_id"], structured
                    )
                _update_run_row(
                    connection,
                    run_id,
                    status="completed",
                    pid=None,
                    completed_at=completed_at,
                    summary=output[:2000] or None,
                    structured_result_json=(
                        json.dumps(structured, ensure_ascii=False) if structured else None
                    ),
                    suggestions_created=suggestions_created,
                    mcp_calls_used=len(mcp_calls),
                    mcp_tool_calls_json=json.dumps(mcp_calls, ensure_ascii=False),
                    mcp_budget_exceeded=int(
                        len(mcp_calls) > (run["mcp_call_budget"] or 0)
                    ),
                )
            _sync_native_claude_sessions()
        else:
            _finalize_failed_run(
                run_id,
                (
                    stderr.strip()
                    or "Claude exited with code {}".format(return_code)
                )[-4000:],
            )
    except asyncio.CancelledError:
        if process and process.returncode is None:
            process.terminate()
            await process.wait()
        _finalize_run(run_id, "cancelled", runner=runner, pid=None)
        raise
    except Exception as exc:
        _finalize_failed_run(run_id, str(exc), runner=runner)
    finally:
        _processes.pop(run_id, None)


async def cancel_run(run_id: str) -> bool:
    with connect() as connection:
        run = get_run(connection, run_id)
    if not run or run["status"] not in {"queued", "running", "cancelling"}:
        return False
    _update_run(run_id, status="cancelling")
    process = _processes.get(run_id)
    if process and process.returncode is None:
        process.terminate()
        return True
    task = _tasks.get(run_id)
    if task and not task.done():
        task.cancel()
        return True
    _finalize_run(run_id, "cancelled", runner=run["runner"], pid=None)
    return True


async def shutdown_runs() -> None:
    active_ids = list(_processes)
    for run_id in active_ids:
        process = _processes.get(run_id)
        if process and process.returncode is None:
            process.terminate()
    if active_ids:
        await asyncio.gather(
            *(process.wait() for process in list(_processes.values())),
            return_exceptions=True,
        )
        now = utc_now()
        with transaction() as connection:
            for run_id in active_ids:
                _update_run_row(
                    connection,
                    run_id,
                    status="interrupted",
                    pid=None,
                    completed_at=now,
                    error="LocalBrain stopped during the run.",
                )
        with connect() as connection:
            runners = {
                row["runner"]
                for row in connection.execute(
                    "SELECT runner FROM maintenance_runs WHERE id IN ({})".format(
                        ",".join("?" for _ in active_ids)
                    ),
                    active_ids,
                ).fetchall()
            }
        for runner in sorted(runners):
            _sync_native_runner_sessions(runner)
