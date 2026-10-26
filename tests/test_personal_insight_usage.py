import asyncio
from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from starlette.requests import Request

from localbrain.main import app, _session_insights_response
from localbrain.personal_insight_evidence import build_insight_evidence_manifest
from localbrain.ingest.codex import CODEX_USAGE_CONTRACT_VERSION, parse_codex_session
from localbrain.ingest.scanner import _scan_session_source
from localbrain.personal_insight_runs import _execute, get_insight_run, reconcile_interrupted_insight_runs
from localbrain.personal_insight_usage import (
    insight_usage_cost, insight_usage_source, recover_insight_usage, store_insight_usage,
)
from localbrain.queries import session_detail, session_inventory_page
from localbrain.usage import reconcile_usage_record_contract
from localbrain.usage_queries import usage_dashboard_data


SCHEMA = Path(__file__).parents[1] / "src/localbrain/schema.sql"
NOW = "2026-09-28T12:00:00+00:00"
USAGE = {"input_tokens": 1000, "cached_input_tokens": 800, "output_tokens": 100, "reasoning_output_tokens": 40}


class PersonalInsightUsageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="localbrain-insight-usage-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.connection = sqlite3.connect(":memory:")
        self.addCleanup(self.connection.close)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA.read_text())
        self.home = self.root / "codex-company"
        self.home.mkdir()
        self.source_id = self.connection.execute(
            "INSERT INTO sources(provider_kind, name, root_path) VALUES ('codex', 'Company', ?)",
            (str(self.home / "sessions"),),
        ).lastrowid
        self.connection.execute(
            "INSERT INTO sources(provider_kind, name, root_path) VALUES ('codex', 'Personal', ?)",
            (str(self.root / "personal/sessions"),),
        )
        self.sequence = 0

    def run_row(self, status="completed", model="gpt-6-astra", legacy=False):
        self.sequence += 1
        run_id = "ins-{:016x}".format(self.sequence)
        root = self.root / "personal-insight-runs" / run_id
        root.mkdir(parents=True)
        options = {"codex_home": str(self.home)}
        if not legacy:
            options.update(service_tier="standard", usage_source_id=self.source_id)
        values = {
            "id": run_id, "mode": "discover", "status": status, "runner": "codex",
            "model": model, "settings_json": json.dumps(options),
            "guide_version": "synthetic", "evidence_version": "synthetic",
            "coverage_json": "{}", "created_at": NOW, "updated_at": NOW,
            "started_at": NOW, "completed_at": NOW if status != "queued" else None,
            **{key + "_path": str(root / name) for key, name in (
                ("evidence", "evidence.json"), ("prompt", "prompt.md"),
                ("response", "response.json"), ("report", "report.md"),
                ("stream", "stream.jsonl"), ("stderr", "stderr.log"),
            )},
        }
        self.connection.execute(
            "INSERT INTO personal_insight_runs({}) VALUES ({})".format(
                ",".join(values), ",".join("?" for _ in values)
            ), tuple(values.values()),
        )
        return get_insight_run(self.connection, run_id)

    def dashboard(self, **kwargs):
        return usage_dashboard_data(
            self.connection, today=date(2026, 9, 28), now=datetime(2026, 9, 28, 13, tzinfo=timezone.utc),
            **kwargs,
        )

    def test_analysis_cost_in_all_and_exact_source_but_no_work_session(self):
        run = self.run_row()
        store_insight_usage(self.connection, run, USAGE, observed_at=NOW)
        row = self.connection.execute("SELECT * FROM usage_records").fetchone()
        self.assertEqual((row["input_tokens"], row["cache_read_tokens"], row["output_tokens"], row["total_tokens"]), (200, 800, 100, 1100))
        self.assertEqual(Decimal(row["estimated_cost_usd"]), Decimal("0.0078"))
        for visible_only in (True, False):
            for source in ("all", "codex-company"):
                data = self.dashboard(source=source, visible_only=visible_only)
                self.assertEqual(data["aggregate"]["estimated_cost"], Decimal("0.0078"))
                self.assertEqual(data["aggregate"]["session_count"], 0)
                self.assertTrue(data["history_has_values"])
        self.assertFalse(self.dashboard(source="2")["has_usage"])
        self.assertEqual(row["attribution_basis"], "unassigned")
        self.assertIsNone(row["workspace_id_snapshot"])
        for visible_only in (True, False):
            project = self.dashboard(breakdown="project", visible_only=visible_only)
            self.assertEqual(project["breakdown"]["rows"], [])
            self.assertEqual(project["breakdown"]["compatible_total_label"], "Unavailable")
            self.assertEqual(project["aggregate"]["total_tokens"], 1100)
            self.assertTrue(project["history_has_values"])
        self.assertEqual(session_inventory_page(self.connection)["total"], 0)
        self.assertIsNone(session_detail(self.connection, row["session_id"]))
        for table in ("activity_events", "search_index", "workspaces", "source_files"):
            self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM " + table).fetchone()[0], 0)
        manifest = build_insight_evidence_manifest(
            self.connection, mode="discover", question=None,
            requested_at=datetime(2026, 9, 28, 13, tzinfo=timezone.utc), timezone="UTC",
        )
        self.assertEqual(manifest["coverage"]["eligible_sessions"], 0)
        self.assertEqual(manifest["sessions"], [])

    def test_replay_and_native_repair_preserve_one_charge_and_new_run_adds_usage(self):
        run = self.run_row()
        store_insight_usage(self.connection, run, USAGE, observed_at=NOW)
        before = dict(self.connection.execute("SELECT * FROM usage_records").fetchone())
        store_insight_usage(self.connection, run, USAGE, observed_at="2026-10-01T12:00:00Z")
        after = dict(self.connection.execute("SELECT * FROM usage_records").fetchone())
        for key in ("id", "occurred_at", "price_snapshot_id", "calculated_at", "attributed_at"):
            self.assertEqual(before[key], after[key])
        reconcile_usage_record_contract(self.connection, self.source_id, [])
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM usage_records").fetchone()[0], 1)
        native_root = self.home / "sessions"
        native_root.mkdir()
        _scan_session_source(
            self.connection, self.source_id, "Company", native_root,
            parse_codex_session, CODEX_USAGE_CONTRACT_VERSION, provider_kind="codex",
        )
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM usage_records").fetchone()[0], 1)
        store_insight_usage(self.connection, self.run_row(), USAGE, observed_at=NOW)
        self.assertEqual(self.dashboard()["aggregate"]["estimated_cost"], Decimal("0.0156"))

    def test_project_excludes_assigned_and_unassigned_analysis_without_reassigning_usage(self):
        internal_run = self.run_row()
        unknown_run = self.run_row()
        assigned_run = self.run_row()
        for run in (internal_run, unknown_run, assigned_run):
            store_insight_usage(self.connection, run, USAGE, observed_at=NOW)
        # Work classification admits unknown work; a frozen Project key alone
        # must not admit Maintenance accounting into Project composition.
        self.connection.execute(
            "UPDATE sessions SET external_id = 'localbrain-insight:no-owner', session_class = 'work' "
            "WHERE external_id = ?", ("localbrain-insight:" + unknown_run["id"],),
        )
        self.connection.execute(
            "UPDATE usage_records SET project_key = 'path:/tmp/original', "
            "project_name_snapshot = 'Original project', project_path_snapshot = '/tmp/original', "
            "attribution_basis = 'workspace_path' WHERE source_record_id = ?",
            (assigned_run["id"],),
        )
        before = [dict(row) for row in self.connection.execute("SELECT * FROM usage_records ORDER BY id")]
        changes = self.connection.total_changes
        for visible_only in (True, False):
            for metric in ("tokens", "cost"):
                with self.subTest(visible_only=visible_only, metric=metric):
                    project = self.dashboard(breakdown="project", metric=metric, visible_only=visible_only)
                    groups = {row["key"]: row for row in project["breakdown"]["rows"]}
                    self.assertEqual(set(groups), {"unassigned"})
                    self.assertEqual(groups["unassigned"]["label"], "프로젝트 미지정")
                    self.assertEqual(groups["unassigned"]["session_count"], 1)
                    self.assertEqual(project["aggregate"]["total_tokens"], 3300)
                    self.assertEqual(project["aggregate"]["estimated_cost"], Decimal("0.0234"))
                    for group in groups.values():
                        self.assertEqual(group["tokens"], 1100)
                        self.assertEqual(group["estimated_cost"], Decimal("0.0078"))
                        self.assertEqual(group["share_label"], "100.0%")
                    for mode in ("source", "model"):
                        other = self.dashboard(breakdown=mode, metric=metric, visible_only=visible_only)
                        self.assertEqual(project["aggregate"], other["aggregate"])
                        self.assertEqual(project["history"], other["history"])
                        self.assertEqual(len(other["breakdown"]["rows"]), 1)
                        self.assertEqual(other["breakdown"]["rows"][0]["tokens"], 3300)
        self.assertEqual(changes, self.connection.total_changes)
        self.assertEqual(before, [dict(row) for row in self.connection.execute("SELECT * FROM usage_records ORDER BY id")])

    def test_project_admission_uses_work_class_independent_of_owner_or_index_policy(self):
        run = self.run_row()
        store_insight_usage(self.connection, run, USAGE, observed_at=NOW)
        for external_id, session_class, index_policy in (
            ("ordinary-session", "maintenance", "metadata_only"),
            ("localbrain-insight:missing-owner", "maintenance", "metadata_only"),
            ("localbrain-insight:" + run["id"], "work", "metadata_only"),
            ("ordinary-session", "work", "full"),
            ("localbrain-insight:" + run["id"], "maintenance", "full"),
        ):
            with self.subTest(external_id=external_id, session_class=session_class, index_policy=index_policy):
                self.connection.execute(
                    "UPDATE sessions SET external_id = ?, session_class = ?, index_policy = ?",
                    (external_id, session_class, index_policy),
                )
                for visible_only in (True, False):
                    groups = self.dashboard(breakdown="project", visible_only=visible_only)["breakdown"]["rows"]
                    if session_class == "work":
                        self.assertEqual(len(groups), 1)
                        self.assertEqual((groups[0]["key"], groups[0]["label"]), ("unassigned", "프로젝트 미지정"))
                    else:
                        self.assertEqual(groups, [])

    def test_detail_reads_stored_estimates_and_distinguishes_unavailable_states(self):
        cases = (
            (USAGE, "gpt-6-astra", "completed", "추정 비용 $0.0078", "비용 계산됨"),
            ({key: 0 for key in USAGE}, "gpt-6-astra", "completed", "추정 비용 $0.0000", "비용 계산됨"),
            ({**USAGE, "input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0},
             "gpt-6-astra", "completed", "추정 비용 &lt;$0.0001", "비용 계산됨"),
            (USAGE, "synthetic-unknown", "failed", "추정 비용 미산정", "가격 정보 없음"),
            ({"input_tokens": 1000, "output_tokens": 100}, "gpt-6-astra", "completed", "추정 비용 미산정", "일부만 계산됨"),
            ({**USAGE, "input_tokens": True}, "gpt-6-astra", "failed", "추정 비용 미산정", "계산 실패"),
            (None, "gpt-6-astra", "failed", "추정 비용 미산정", "기록 없음"),
            (None, "gpt-6-astra", "queued", "추정 비용 미산정", "수신 대기"),
        )
        @contextmanager
        def connection():
            yield self.connection

        coverage = {"selected_sessions": 0, "selected_excerpts": 0, "eligible_sessions": 0,
                    "eligible_messages": 0, "selected_undated_messages": 0, "sources": {}}
        for usage, model, status, amount_text, state_text in cases:
            with self.subTest(model=model, status=status, state=state_text):
                run = self.run_row(status=status, model=model)
                self.connection.execute("UPDATE personal_insight_runs SET coverage_json = ? WHERE id = ?",
                                        (json.dumps(coverage), run["id"]))
                if usage is not None:
                    store_insight_usage(self.connection, run, {**usage, "total_cost_usd": 9.99}, observed_at=NOW)
                changes = self.connection.total_changes
                request = Request({"type": "http", "method": "GET", "query_string": b"", "headers": [],
                                   "path": "/sessions-dashboard/insights", "root_path": "", "scheme": "http",
                                   "server": ("testserver", 80), "app": app, "router": app.router})
                with patch("localbrain.main.connect", connection), patch("localbrain.main.insight_runner_choices", return_value=[]), patch(
                    "localbrain.main.prepare_insight_run", side_effect=AssertionError("GET must not execute analysis")
                ):
                    response = _session_insights_response(request, selected_id=run["id"])
                html = response.body.decode()
                self.assertIn(amount_text, html)
                self.assertIn(state_text, html)
                self.assertIn("실제 청구액이 아닙니다", html)
                if usage is not None:
                    self.assertIn("실행기 보고 비용 $9.99", html)
                    self.assertIn("적용 가격표", html)
                if usage == USAGE and model == "gpt-6-astra":
                    stored = insight_usage_cost(self.connection, run["id"])
                    self.assertEqual(stored["estimated_cost_usd"], "0.007800000000")
                    self.assertIn(stored["price_label"], html)
                self.assertEqual(changes, self.connection.total_changes)

    def test_missing_malformed_unknown_model_and_aggregate_context_are_not_zero_priced(self):
        cases = (
            ({"input_tokens": 1000, "output_tokens": 100}, "gpt-6-astra", "partial"),
            ({**USAGE, "input_tokens": True}, "gpt-6-astra", "failed"),
            ({**USAGE, "cached_input_tokens": 1001}, "gpt-6-astra", "failed"),
            (USAGE, "synthetic-unknown-model", "unpriced"),
            ({**USAGE, "input_tokens": 300_000}, "gpt-6-astra", "partial"),
        )
        for usage, model, state in cases:
            with self.subTest(state=state, usage=usage):
                run = self.run_row(model=model)
                store_insight_usage(self.connection, run, usage, observed_at=NOW)
                row = self.connection.execute("SELECT * FROM usage_records WHERE source_record_id = ?", (run["id"],)).fetchone()
                self.assertEqual(row["calculation_state"], state)
                self.assertIsNone(row["estimated_cost_usd"])

    def test_recovery_of_legacy_summary_and_failed_stream_is_idempotent(self):
        for status in ("completed", "failed", "cancelled", "interrupted"):
            run = self.run_row(status=status, legacy=True)
            if status == "completed":
                self.connection.execute("UPDATE personal_insight_runs SET usage_json = ? WHERE id = ?", (json.dumps(USAGE), run["id"]))
            else:
                Path(run["stream_path"]).write_text("malformed\n[]\n" + json.dumps({"type": "turn.completed", "usage": USAGE}) + "\n")
        self.run_row(status="failed")  # Missing evidence must not invent zero usage.
        self.assertEqual(recover_insight_usage(self.connection), 4)
        self.assertEqual(recover_insight_usage(self.connection), 0)
        self.assertEqual(self.dashboard()["aggregate"]["estimated_cost"], Decimal("0.0312"))
        row = self.connection.execute("SELECT capability_json FROM usage_records LIMIT 1").fetchone()
        self.assertEqual(json.loads(row["capability_json"])["service_tier_source"], "unmarked_default_assumption")

    def test_source_resolution_refuses_wrong_or_ambiguous_home(self):
        with self.assertRaises(ValueError):
            insight_usage_source(self.connection, {"codex_home": str(self.root / "missing")})
        retained = self.root / "retained"
        retained.mkdir()
        (self.home / "sessions").symlink_to(retained, target_is_directory=True)
        self.assertEqual(insight_usage_source(self.connection, {"codex_home": str(self.home)})["id"], self.source_id)
        self.connection.execute(
            "INSERT INTO sources(provider_kind, name, root_path) VALUES ('codex', 'Duplicate', ?)",
            (str(self.home / "sessions"),),
        )
        with self.assertRaises(ValueError):
            insight_usage_source(self.connection, {"codex_home": str(self.home)})
        self.assertEqual(insight_usage_source(self.connection, {"codex_home": str(self.home), "usage_source_id": self.source_id})["id"], self.source_id)

    def test_startup_interrupts_and_recovers_emitted_usage_without_model_execution(self):
        run = self.run_row(status="running")
        Path(run["stream_path"]).write_text(json.dumps({"type": "turn.completed", "usage": USAGE}) + "\n")

        @contextmanager
        def transaction():
            yield self.connection

        with patch("localbrain.personal_insight_runs.transaction", transaction), patch(
            "localbrain.personal_insight_runs.asyncio.create_subprocess_exec"
        ) as model:
            reconcile_interrupted_insight_runs()
            reconcile_interrupted_insight_runs()
            model.assert_not_called()
        self.assertEqual(get_insight_run(self.connection, run["id"])["status"], "interrupted")
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM usage_records").fetchone()[0], 1)

    def test_failed_report_and_cancelled_process_keep_observed_usage(self):
        @contextmanager
        def connection_context():
            yield self.connection

        class Process:
            def __init__(self, blocked):
                self.pid = 123
                self.returncode = None
                self.blocked = blocked
                self.stdin = SimpleNamespace(write=lambda _: None, drain=self.drain, close=lambda: None)
                self.stdout = asyncio.StreamReader()
                self.stdout.feed_data((json.dumps({"type": "turn.completed", "usage": USAGE}) + "\n").encode())
                self.stdout.feed_eof()
                self.stderr = asyncio.StreamReader()
                self.stderr.feed_eof()
                self.stopped = asyncio.Event()

            async def drain(self):
                pass

            async def wait(self):
                if self.blocked:
                    await self.stopped.wait()
                self.returncode = 0
                return 0

            def terminate(self):
                self.returncode = -15
                self.stopped.set()

        async def exercise():
            for cancelled in (False, True):
                run = self.run_row(status="queued")
                Path(run["prompt_path"]).write_text("Synthetic analysis")
                Path(run["evidence_path"]).write_text("{}")
                process = Process(cancelled)

                async def start_process(*args, **kwargs):
                    self.assertEqual(kwargs["cwd"], str(Path(run["stream_path"]).parent))
                    return process

                with patch("localbrain.personal_insight_runs.connect", connection_context), patch(
                    "localbrain.personal_insight_runs.transaction", connection_context
                ), patch("localbrain.personal_insight_runs.settings", SimpleNamespace(data_dir=self.root)), patch(
                    "localbrain.personal_insight_runs.runner_executable", return_value="/synthetic/codex"
                ), patch("localbrain.personal_insight_runs._runner_args", return_value=["/synthetic/codex"]), patch(
                    "localbrain.personal_insight_runs.asyncio.create_subprocess_exec", start_process
                ), patch("localbrain.personal_insight_runs._validate_result", side_effect=ValueError("Invalid report")), patch(
                    "localbrain.personal_insight_runs._shutting_down", False
                ):
                    task = asyncio.create_task(_execute(run["id"]))
                    if cancelled:
                        for _ in range(100):
                            if get_insight_run(self.connection, run["id"])["usage_json"]:
                                break
                            await asyncio.sleep(0)
                        self.assertIsNotNone(get_insight_run(self.connection, run["id"])["usage_json"])
                        task.cancel()
                        with self.assertRaises(asyncio.CancelledError):
                            await task
                    else:
                        await task
                saved = get_insight_run(self.connection, run["id"])
                self.assertEqual(saved["status"], "cancelled" if cancelled else "failed")
                self.assertEqual(json.loads(saved["usage_json"]), USAGE)
                self.assertIsNotNone(self.connection.execute("SELECT estimated_cost_usd FROM usage_records WHERE source_record_id = ?", (run["id"],)).fetchone()[0])

        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()
