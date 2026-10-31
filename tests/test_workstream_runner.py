"""Feature execution keeps the shared Run lifecycle and atomic review queue."""

import asyncio
import json
import sqlite3
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import AsyncMock, patch

from localbrain.maintenance import service as runtime
from localbrain.workstreams import runner


class Stream:
    def __init__(self, lines):
        self.lines = iter(lines)

    async def readline(self):
        return next(self.lines, b"")


class Process:
    pid = 43210
    returncode = None

    def __init__(self, result):
        self.stdin = self
        self.stdout = Stream([(json.dumps({"type": "result", "structured_output": result}) + "\n").encode()])
        self.stderr = Stream([])

    def write(self, value):
        self.prompt = value

    async def drain(self):
        pass

    def close(self):
        pass

    async def wait(self):
        self.returncode = 0
        return 0


class WorkstreamExecutionTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.connection = sqlite3.connect(self.root / "test.db")
        self.addCleanup(self.connection.close)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript((Path(__file__).parents[1] / "src/localbrain/schema.sql").read_text())
        self.connection.execute("INSERT INTO workstreams(id,name) VALUES (1,'Synthetic')")
        self.run_id = runner.prepare_run(self.connection, 1, "organize_resources", run_root=self.root / "runs",
                                        refresh_suggestions=True)
        self.connection.execute("""INSERT INTO suggestions(suggestion_type,target_type,target_id,title,
            payload_json,fingerprint,origin_run_id,status) VALUES
            ('resource_link','workstream',1,'Retain on failure','{}','synthetic-previous','previous-run','pending')""")
        self.connection.commit()
        self.stack.enter_context(patch.object(runtime, "connect", return_value=self.connection))
        self.stack.enter_context(patch.object(runtime, "transaction", self.transaction))
        self.stack.enter_context(patch.object(runtime, "_sync_native_claude_sessions", return_value=True))
        self.stack.enter_context(patch.object(runner, "runner_executable", return_value="/synthetic/claude"))

    @contextmanager
    def transaction(self):
        try:
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def execute(self):
        result = {"summary": "Synthetic result", "resource_suggestions": [
            {"resource_type": "url", "locator": "https://example.test/reference", "title": "Evidence"}]}
        with patch.object(runner.asyncio, "create_subprocess_exec", AsyncMock(return_value=Process(result))):
            async def run():
                runner.start_run(self.run_id)
                await runtime._tasks[self.run_id]
                await asyncio.sleep(0)
            asyncio.run(run())
        self.assertNotIn(self.run_id, runtime._tasks)
        self.assertNotIn(self.run_id, runtime._processes)
        return runtime.get_run(self.connection, self.run_id)

    def test_feature_submits_its_execution_and_commits_suggestions_with_completion(self):
        row = self.execute()
        self.assertEqual(row["status"], "completed")
        self.assertEqual(row["suggestions_created"], 1)
        self.assertEqual(self.connection.execute("SELECT status FROM suggestions WHERE fingerprint='synthetic-previous'").fetchone()[0], "superseded")
        self.assertEqual(self.connection.execute("SELECT count(*) FROM suggestions WHERE origin_run_id=? AND status='pending'", (self.run_id,)).fetchone()[0], 1)

    def test_application_failure_rolls_back_queue_before_failed_terminal_state(self):
        original = runner.persist_structured_suggestions
        def fail_after_write(*args):
            original(*args)
            raise RuntimeError("Synthetic result application failed")
        with patch.object(runner, "persist_structured_suggestions", side_effect=fail_after_write):
            row = self.execute()
        self.assertEqual(row["status"], "failed")
        self.assertIn("Synthetic result application failed", row["error"])
        self.assertEqual(self.connection.execute("SELECT status FROM suggestions WHERE fingerprint='synthetic-previous'").fetchone()[0], "pending")
        self.assertEqual(self.connection.execute("SELECT count(*) FROM suggestions WHERE origin_run_id=?", (self.run_id,)).fetchone()[0], 0)
