"""Run state, task/process tracking, cancellation and interrupted-run recovery.

Feature executors supply their coroutine; this module does not choose a task or
import its implementation. Existing ledger/schema contracts remain unchanged.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict

from localbrain.foundation.clock import utc_now
from localbrain.persistence.db import connect, transaction
from localbrain.ingest.scanner import scan_claude_sessions, scan_codex_sessions

_tasks: Dict[str, asyncio.Task] = {}
_processes: Dict[str, asyncio.subprocess.Process] = {}
logger = logging.getLogger(__name__)

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


def start_run(run_id: str, execution) -> None:
    """Track the coroutine supplied by the feature that prepared this Run."""
    task = asyncio.create_task(execution)
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
