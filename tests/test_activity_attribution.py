import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from localbrain.activity import (
    activity_summary,
    activity_summary_from_events,
    calendar_day_bounds,
    calendar_week_bounds,
)
from localbrain.db import _run_compatible_migrations
from localbrain.ingest.common import ParsedSession, ParsedUsageFact
from localbrain.ingest.scanner import _store_session


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


def usage_fact(identity: str, occurred_at: str = "2026-07-18T00:00:00Z"):
    return ParsedUsageFact(
        fact_id="fact-{}".format(identity),
        source_record_id=identity,
        source_line=1,
        occurred_at=occurred_at,
        raw_model="gpt-5.5",
        input_tokens=100,
        output_tokens=50,
        cache_write_tokens=None,
        cache_read_tokens=20,
        reasoning_tokens=10,
        source_total_tokens=170,
        total_tokens=170,
        total_semantics="reasoning_subset_of_output",
    )


def parsed_session(external_id: str, cwd: str, facts):
    return ParsedSession(
        external_id=external_id,
        source_path="/tmp/{}.jsonl".format(external_id),
        cwd_raw=cwd,
        git_branch=None,
        title=external_id,
        started_at="2026-07-18T00:00:00Z",
        ended_at="2026-07-18T00:05:00Z",
        last_event_at="2026-07-18T00:05:00Z",
        events=[],
        usage_facts=list(facts),
    )


class ActivityAttributionTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.source_id = self.connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp')"
        ).lastrowid

    def tearDown(self):
        self.connection.close()

    def test_late_git_discovery_changes_only_new_fact_attribution(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory) / "project"
            project.mkdir()
            first = usage_fact("first")
            _store_session(
                self.connection,
                self.source_id,
                "codex",
                parsed_session("session", str(project), [first]),
            )
            first_snapshot = self.connection.execute(
                """
                SELECT project_key, project_path_snapshot,
                       project_git_root_snapshot, attribution_basis, attributed_at
                FROM usage_facts WHERE id = 'fact-first'
                """
            ).fetchone()
            self.assertEqual(first_snapshot["attribution_basis"], "workspace_path")
            self.assertEqual(
                first_snapshot["project_key"], "path:{}".format(project.resolve())
            )
            self.assertIsNone(first_snapshot["project_git_root_snapshot"])

            (project / ".git").mkdir()
            second = usage_fact("second", "2026-07-18T00:02:00Z")
            _store_session(
                self.connection,
                self.source_id,
                "codex",
                parsed_session("session", str(project), [first, second]),
            )
            rows = {
                row["id"]: row
                for row in self.connection.execute(
                    """
                    SELECT id, project_key, project_git_root_snapshot,
                           attribution_basis, attributed_at
                    FROM usage_facts ORDER BY id
                    """
                )
            }
            self.assertEqual(rows["fact-first"]["project_key"], first_snapshot["project_key"])
            self.assertEqual(
                rows["fact-first"]["attributed_at"], first_snapshot["attributed_at"]
            )
            self.assertEqual(rows["fact-second"]["attribution_basis"], "git_root")
            self.assertEqual(
                rows["fact-second"]["project_key"], "git:{}".format(project.resolve())
            )

            (project / ".git").rmdir()
            third = usage_fact("third", "2026-07-18T00:03:00Z")
            _store_session(
                self.connection,
                self.source_id,
                "codex",
                parsed_session("session", str(project), [first, second, third]),
            )
            rows = {
                row["id"]: row
                for row in self.connection.execute(
                    "SELECT id, project_key, attribution_basis FROM usage_facts"
                )
            }
            self.assertEqual(rows["fact-second"]["attribution_basis"], "git_root")
            self.assertEqual(rows["fact-third"]["attribution_basis"], "workspace_path")
            current_git_root = self.connection.execute(
                "SELECT git_root FROM workspaces"
            ).fetchone()[0]
            self.assertIsNone(current_git_root)

    def test_unassigned_fact_is_not_reconciled_when_path_arrives_later(self):
        first = usage_fact("unassigned")
        _store_session(
            self.connection,
            self.source_id,
            "codex",
            parsed_session("unassigned-session", None, [first]),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            second = usage_fact("assigned", "2026-07-18T00:02:00Z")
            _store_session(
                self.connection,
                self.source_id,
                "codex",
                parsed_session(
                    "unassigned-session", temporary_directory, [first, second]
                ),
            )
        rows = {
            row["id"]: row
            for row in self.connection.execute(
                "SELECT id, project_key, attribution_basis FROM usage_facts"
            )
        }
        self.assertEqual(rows["fact-unassigned"]["attribution_basis"], "unassigned")
        self.assertIsNone(rows["fact-unassigned"]["project_key"])
        self.assertEqual(rows["fact-assigned"]["attribution_basis"], "workspace_path")

    def test_exact_gap_threshold_and_incomplete_session_use_last_event(self):
        summary = activity_summary_from_events(
            [
                (1, "2026-07-18T09:00:00Z"),
                (1, "2026-07-18T09:30:00Z"),
                (1, "2026-07-18T10:00:01Z"),
                (2, "2026-07-18T11:00:00Z"),
                (2, "2026-07-18T11:05:00Z"),
                (3, "not-a-time"),
            ]
        )
        self.assertEqual(summary["observed_session_span_seconds"], 3901)
        self.assertEqual(summary["estimated_active_seconds"], 2100)
        self.assertEqual(summary["longest_active_segment_seconds"], 1800)
        self.assertEqual(summary["activity_segment_count"], 3)
        self.assertEqual(summary["session_count"], 2)

    def test_concurrent_sessions_merge_before_active_time_total(self):
        summary = activity_summary_from_events(
            [
                (1, "2026-07-18T09:00:00Z"),
                (1, "2026-07-18T09:20:00Z"),
                (2, "2026-07-18T09:10:00Z"),
                (2, "2026-07-18T09:30:00Z"),
            ]
        )
        self.assertEqual(summary["observed_session_span_seconds"], 2400)
        self.assertEqual(summary["estimated_active_seconds"], 1800)
        self.assertEqual(summary["longest_active_segment_seconds"], 1800)
        self.assertEqual(summary["merged_segment_count"], 1)

    def test_range_clipping_and_local_calendar_boundaries_are_deterministic(self):
        summary = activity_summary_from_events(
            [
                (1, "2026-07-18T09:00:00Z"),
                (1, "2026-07-18T09:20:00Z"),
                (2, "2026-07-18T09:10:00Z"),
                (2, "2026-07-18T09:30:00Z"),
            ],
            start=datetime(2026, 7, 18, 9, 10, tzinfo=timezone.utc),
            end=datetime(2026, 7, 18, 9, 25, tzinfo=timezone.utc),
        )
        self.assertEqual(summary["observed_session_span_seconds"], 1500)
        self.assertEqual(summary["estimated_active_seconds"], 900)

        day_start, day_end = calendar_day_bounds(
            date(2026, 7, 18), "Asia/Seoul"
        )
        self.assertEqual(day_start, datetime(2026, 7, 17, 15, tzinfo=timezone.utc))
        self.assertEqual(day_end, datetime(2026, 7, 18, 15, tzinfo=timezone.utc))
        week_start, week_end = calendar_week_bounds(
            date(2026, 7, 18), "Asia/Seoul"
        )
        self.assertEqual(week_start, datetime(2026, 7, 12, 15, tzinfo=timezone.utc))
        self.assertEqual(week_end, datetime(2026, 7, 19, 15, tzinfo=timezone.utc))
        self.assertEqual(
            day_start.astimezone(ZoneInfo("Asia/Seoul")).date(), date(2026, 7, 18)
        )

    def test_database_activity_summary_uses_normalized_events(self):
        session_id = self.connection.execute(
            """
            INSERT INTO sessions(source_id, external_id, source_path, title)
            VALUES (?, 'activity-session', '/tmp/activity.jsonl', 'activity')
            """,
            (self.source_id,),
        ).lastrowid
        self.connection.executemany(
            """
            INSERT INTO activity_events(
                id, session_id, sequence, occurred_at, event_type, source_line
            ) VALUES (?, ?, ?, ?, 'message', ?)
            """,
            [
                ("event-1", session_id, 10, "2026-07-18T09:00:00Z", 1),
                ("event-2", session_id, 20, "2026-07-18T09:10:00Z", 2),
            ],
        )
        summary = activity_summary(self.connection)
        self.assertEqual(summary["estimated_active_seconds"], 600)
        self.assertEqual(summary["observed_session_span_seconds"], 600)

    def test_legacy_usage_fact_migrates_to_stable_unassigned_attribution(self):
        attribution_block = """    workspace_id_snapshot INTEGER,
    project_key TEXT,
    project_name_snapshot TEXT,
    project_path_snapshot TEXT,
    project_git_root_snapshot TEXT,
    attribution_basis TEXT NOT NULL DEFAULT 'unassigned'
        CHECK(attribution_basis IN ('git_root', 'workspace_path', 'unassigned')),
    attributed_at TEXT NOT NULL,
"""
        schema = SCHEMA_PATH.read_text(encoding="utf-8").replace(
            attribution_block, ""
        )
        legacy = sqlite3.connect(":memory:")
        legacy.row_factory = sqlite3.Row
        legacy.execute("PRAGMA foreign_keys = ON")
        legacy.executescript(schema)
        legacy.execute(
            """
            INSERT INTO usage_price_snapshots(
                id, label, source_ref, calculator_version, created_at
            ) VALUES ('legacy-price', 'legacy', 'synthetic', 'v1', '2026-07-17')
            """
        )
        source_id = legacy.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp')"
        ).lastrowid
        session_id = legacy.execute(
            """
            INSERT INTO sessions(source_id, external_id, source_path, title)
            VALUES (?, 'legacy', '/tmp/legacy.jsonl', 'legacy')
            """,
            (source_id,),
        ).lastrowid
        legacy.execute(
            """
            INSERT INTO usage_facts(
                id, source_id, session_id, source_record_id, source_line,
                total_semantics, aggregation_scope, capability_state,
                capability_json, calculation_state, estimated_cost_usd,
                price_snapshot_id, calculator_version, calculated_at, imported_at
            ) VALUES (
                'legacy-fact', ?, ?, 'legacy-record', 1,
                'legacy', 'direct', 'complete', '{}', 'priced', '0.01',
                'legacy-price', 'v1', '2026-07-17T01:00:00Z', '2026-07-17T01:00:00Z'
            )
            """,
            (source_id, session_id),
        )
        _run_compatible_migrations(legacy)
        row = legacy.execute(
            """
            SELECT attribution_basis, attributed_at, project_key
            FROM usage_facts WHERE id = 'legacy-fact'
            """
        ).fetchone()
        self.assertEqual(row["attribution_basis"], "unassigned")
        self.assertEqual(row["attributed_at"], "2026-07-17T01:00:00Z")
        self.assertIsNone(row["project_key"])
        legacy.close()


if __name__ == "__main__":
    unittest.main()
