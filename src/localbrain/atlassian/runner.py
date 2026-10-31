"""Approved external read execution and atomic Atlassian result application."""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Optional

from localbrain.foundation.agent_cli import runner_executable
from localbrain.foundation.clock import utc_now
from localbrain.maintenance import service as runtime
from localbrain.maintenance.streams import _structured_result, _consume_stderr
from localbrain.atlassian.refresh import apply_atlassian_refresh_result, is_atlassian_refresh_manifest
from localbrain.atlassian.sync import (
    MODEL_RESULT_SCHEMA, ExternalReadExecutor, ExternalSyncError,
    assemble_external_sync_result, build_external_sync_prompt,
    collect_external_sync_evidence, load_external_sync_manifest,
)

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
        runtime._finalize_failed_run(
            run_id,
            "External synchronization requires an approved read executor.",
            runner=runner,
        )
        return
    with runtime.connect() as connection:
        manifest, dispatches = load_external_sync_manifest(connection, run)
    run_root = Path(run["manifest_path"]).parent
    evidence_path = run_root / "evidence.json"
    started_at = utc_now()
    runtime._update_run(
        run_id,
        status="running",
        pid=None,
        started_at=started_at,
        error=None,
    )

    def on_call(call_log: List[dict]) -> None:
        runtime._update_run(
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
        runtime._finalize_failed_run(
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
    runtime._processes[run_id] = process
    runtime._update_run(run_id, pid=process.pid)
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
    with runtime.connect() as connection:
        current = runtime.get_run(connection, run_id)
    if current and current["status"] in {"cancelling", "cancelled"}:
        runtime._finalize_run(
            run_id,
            "cancelled",
            runner=runner,
            pid=None,
        )
        return
    if return_code != 0:
        runtime._finalize_failed_run(
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
    with runtime.transaction() as connection:
        if is_atlassian_refresh_manifest(manifest):
            apply_atlassian_refresh_result(
                connection,
                manifest=manifest,
                result=result,
            )
        runtime._update_run_row(
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
    runtime._sync_native_runner_sessions(runner)


async def _execute_run(
    run_id: str,
    external_executor: Optional[ExternalReadExecutor] = None,
) -> None:
    process = None
    runner = "claude"
    try:
        with runtime.connect() as connection:
            run = runtime.get_run(connection, run_id)
        if not run:
            return
        runner = run["runner"]
        await _execute_external_sync_run(run_id, run, external_executor)
    except asyncio.CancelledError:
        if process and process.returncode is None:
            process.terminate()
            await process.wait()
        runtime._finalize_run(run_id, "cancelled", runner=runner, pid=None)
        raise
    except Exception as exc:
        runtime._finalize_failed_run(run_id, str(exc), runner=runner)
    finally:
        runtime._processes.pop(run_id, None)


def start_run(run_id: str, external_executor: Optional[ExternalReadExecutor] = None) -> None:
    runtime.start_run(run_id, _execute_run(run_id, external_executor))
