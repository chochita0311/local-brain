import sqlite3
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from localbrain.ingest.common import ParsedSession, ParsedUsageFact
from localbrain.ingest.scanner import _store_session
from localbrain.usage_queries import normalize_usage_scope, usage_dashboard_data


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


def usage_fact(identity, occurred_at, model="gpt-5.5"):
    return ParsedUsageFact(
        fact_id="fact-{}".format(identity),
        source_record_id=identity,
        source_line=1,
        occurred_at=occurred_at,
        raw_model=model,
        input_tokens=100,
        output_tokens=50,
        cache_write_tokens=0 if model.startswith("claude-") else None,
        cache_read_tokens=20,
        reasoning_tokens=10,
        source_total_tokens=170,
        total_tokens=170,
        total_semantics="reasoning_subset_of_output",
    )


def synthetic_usage_fact(identity, occurred_at):
    return ParsedUsageFact(
        fact_id="fact-{}".format(identity),
        source_record_id=identity,
        source_line=1,
        occurred_at=occurred_at,
        raw_model="<synthetic>",
        input_tokens=0,
        output_tokens=0,
        cache_write_tokens=0,
        cache_read_tokens=0,
        reasoning_tokens=None,
        source_total_tokens=0,
        total_tokens=0,
        total_semantics="synthetic_non_usage_message",
    )


def parsed_session(
    identity,
    facts,
    session_class="work",
    session_role="primary",
):
    first_time = facts[0].occurred_at if facts else None
    return ParsedSession(
        external_id=identity,
        source_path="/tmp/{}.jsonl".format(identity),
        cwd_raw=None,
        git_branch=None,
        title=identity,
        started_at=first_time,
        ended_at=first_time,
        last_event_at=first_time,
        events=[],
        session_class=session_class,
        index_policy="metadata_only" if session_class == "maintenance" else "full",
        session_role=session_role,
        usage_facts=list(facts),
    )


class UsageDashboardTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.claude_id = self.connection.execute(
            """
            INSERT INTO sources(kind, name, root_path, last_scanned_at)
            VALUES ('claude', 'Claude', '/tmp/claude', '2026-07-18T08:00:00Z')
            """
        ).lastrowid
        self.codex_id = self.connection.execute(
            """
            INSERT INTO sources(kind, name, root_path, last_scanned_at)
            VALUES ('codex', 'Codex', '/tmp/codex', '2026-07-18T09:00:00Z')
            """
        ).lastrowid

    def tearDown(self):
        self.connection.close()

    def _seed_usage(self):
        _store_session(
            self.connection,
            self.claude_id,
            "claude",
            parsed_session(
                "claude-primary",
                [
                    usage_fact(
                        "claude-primary",
                        "2026-07-01T10:00:00Z",
                        "claude-sonnet-4-6",
                    )
                ],
            ),
        )
        _store_session(
            self.connection,
            self.codex_id,
            "codex",
            parsed_session(
                "codex-primary",
                [
                    usage_fact("codex-primary", "2026-07-18T09:00:00Z"),
                    usage_fact(
                        "codex-unpriced", "2026-07-18T09:10:00Z", "future-model"
                    ),
                ],
            ),
        )
        _store_session(
            self.connection,
            self.codex_id,
            "codex",
            parsed_session(
                "codex-maintenance",
                [usage_fact("codex-maintenance", "2026-07-18T11:00:00Z")],
                session_class="maintenance",
                session_role="subsession",
            ),
        )
        codex_session = self.connection.execute(
            "SELECT id FROM sessions WHERE external_id = 'codex-primary'"
        ).fetchone()[0]
        self.connection.executemany(
            """
            INSERT INTO activity_events(
                id, session_id, sequence, occurred_at, event_type, source_line
            ) VALUES (?, ?, ?, ?, 'message', ?)
            """,
            [
                ("activity-1", codex_session, 10, "2026-07-18T09:00:00Z", 1),
                ("activity-2", codex_session, 20, "2026-07-18T09:20:00Z", 2),
            ],
        )

    def test_default_summary_includes_all_direct_usage_but_counts_primary_work(self):
        self._seed_usage()
        result = usage_dashboard_data(
            self.connection, timezone_name="UTC", today=date(2026, 7, 18)
        )

        self.assertEqual(result["scope"]["from_iso"], "2026-06-19")
        self.assertEqual(result["scope"]["to_iso"], "2026-07-18")
        self.assertEqual(len(result["history"]), 30)
        self.assertEqual(result["aggregate"]["total_tokens"], 680)
        self.assertEqual(result["aggregate"]["session_count"], 2)
        self.assertEqual(result["aggregate"]["active_days"], 2)
        self.assertEqual(result["activity"]["estimated_active_seconds"], 1200)
        self.assertEqual(result["aggregate"]["priced_fact_count"], 3)
        self.assertEqual(result["summary"][0]["value"], "$0.0051")
        self.assertEqual(result["summary"][1]["value"], "680")
        self.assertTrue(any("3 of 4" in item for item in result["limitations"]))
        self.assertEqual(result["breakdown"]["mode"], "source")
        self.assertEqual(
            [(row["label"], row["tokens"]) for row in result["breakdown"]["rows"]],
            [("Codex", 510), ("Claude", 170)],
        )
        self.assertEqual(result["breakdown"]["rows"][0]["share_label"], "75.0%")

    def test_claude_synthetic_facts_stay_stored_but_are_excluded_from_dashboard(self):
        _store_session(
            self.connection,
            self.claude_id,
            "claude",
            parsed_session(
                "synthetic-primary",
                [synthetic_usage_fact("synthetic-primary", "2026-06-01T09:00:00Z")],
            ),
        )
        _store_session(
            self.connection,
            self.claude_id,
            "claude",
            parsed_session(
                "haiku-subsession",
                [
                    usage_fact(
                        "haiku-subsession",
                        "2026-07-02T07:20:00Z",
                        "claude-haiku-4-5-20251001",
                    )
                ],
                session_role="subsession",
            ),
        )

        stored_synthetic = self.connection.execute(
            "SELECT COUNT(*) FROM usage_facts WHERE raw_model = '<synthetic>'"
        ).fetchone()[0]
        result = usage_dashboard_data(
            self.connection,
            view="cumulative",
            breakdown="model",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )

        self.assertEqual(stored_synthetic, 1)
        self.assertEqual(result["scope"]["from_iso"], "2026-07-02")
        self.assertEqual(result["aggregate"]["fact_count"], 1)
        self.assertEqual(result["aggregate"]["total_tokens"], 170)
        self.assertEqual(result["aggregate"]["session_count"], 0)
        self.assertEqual(
            [row["label"] for row in result["breakdown"]["rows"]],
            ["claude-haiku-4-5-20251001"],
        )
        self.assertEqual(result["breakdown"]["rows"][0]["priced_fact_count"], 1)

    def test_weekly_cumulative_custom_and_source_scopes_are_deterministic(self):
        self._seed_usage()
        weekly = usage_dashboard_data(
            self.connection,
            view="weekly",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertEqual(weekly["scope"]["from_iso"], "2026-04-27")
        self.assertEqual(len(weekly["history"]), 12)

        cumulative = usage_dashboard_data(
            self.connection,
            view="cumulative",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertEqual(cumulative["scope"]["from_iso"], "2026-07-01")
        self.assertEqual(len(cumulative["history"]), 1)
        self.assertEqual(int(cumulative["history"][0]["value"]), 680)

        custom = usage_dashboard_data(
            self.connection,
            from_value="2026-07-01",
            to_value="2026-07-10",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertTrue(custom["scope"]["custom"])
        self.assertEqual(custom["aggregate"]["total_tokens"], 170)
        self.assertEqual(custom["aggregate"]["session_count"], 1)

        claude = usage_dashboard_data(
            self.connection,
            source="claude",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertEqual(claude["aggregate"]["total_tokens"], 170)
        self.assertEqual(claude["freshness"]["status"], "current")

    def test_invalid_custom_pair_falls_back_without_losing_other_scope(self):
        self._seed_usage()
        result = normalize_usage_scope(
            self.connection,
            view="weekly",
            source="codex",
            metric="cost",
            breakdown="model",
            from_value="2026-07-18",
            to_value="2026-07-01",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertFalse(result["custom"])
        self.assertEqual(result["view"], "weekly")
        self.assertEqual(result["source"], "codex")
        self.assertEqual(result["metric"], "cost")
        self.assertEqual(result["breakdown"], "model")
        self.assertEqual(result["from_iso"], "2026-04-27")
        self.assertIsNotNone(result["validation_message"])

    def test_empty_and_unpriced_cost_states_never_render_as_zero_cost(self):
        empty = usage_dashboard_data(
            self.connection,
            metric="cost",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertFalse(empty["has_usage"])
        self.assertEqual(empty["summary"][0]["value"], "Unavailable")

        _store_session(
            self.connection,
            self.codex_id,
            "codex",
            parsed_session(
                "future",
                [usage_fact("future", "2026-07-18T09:00:00Z", "future-model")],
            ),
        )
        unpriced = usage_dashboard_data(
            self.connection,
            metric="cost",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertEqual(unpriced["summary"][0]["value"], "Unavailable")
        self.assertEqual(unpriced["history"][0]["value_label"], "$0.0000")
        self.assertTrue(any("0 of 1" in item for item in unpriced["limitations"]))

    def test_model_and_project_breakdowns_preserve_raw_and_snapshot_identity(self):
        self._seed_usage()
        _store_session(
            self.connection,
            self.codex_id,
            "codex",
            parsed_session(
                "aliased-model",
                [
                    usage_fact(
                        "aliased-model",
                        "2026-07-18T12:00:00Z",
                        "openai/gpt-5.5",
                    )
                ],
            ),
        )
        model = usage_dashboard_data(
            self.connection,
            breakdown="model",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        gpt = next(row for row in model["breakdown"]["rows"] if row["label"] == "gpt-5.5")
        self.assertIn("openai/gpt-5.5", gpt["raw_models"])
        self.assertIn("breakdown=model", model["controls"]["breakdowns"][1]["url"])

        workspace_id = self.connection.execute(
            """
            INSERT INTO workspaces(canonical_path, display_name, exists_now)
            VALUES ('/tmp/current', 'Current name', 1)
            """
        ).lastrowid
        self.connection.execute(
            """
            UPDATE usage_facts
            SET workspace_id_snapshot = ?, project_key = 'path:/tmp/original',
                project_name_snapshot = 'Original name',
                project_path_snapshot = '/tmp/original',
                attribution_basis = 'workspace_path'
            WHERE id = 'fact-claude-primary'
            """,
            (workspace_id,),
        )
        self.connection.execute(
            "UPDATE workspaces SET display_name = 'Later rename' WHERE id = ?",
            (workspace_id,),
        )
        project = usage_dashboard_data(
            self.connection,
            breakdown="project",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        labels = [row["label"] for row in project["breakdown"]["rows"]]
        self.assertIn("Original name", labels)
        self.assertIn("Unassigned", labels)
        snapshot = next(
            row for row in project["breakdown"]["rows"] if row["label"] == "Original name"
        )
        self.assertEqual(snapshot["evidence_url"], "/sessions?workspace={}".format(workspace_id))
        self.assertNotIn("Later rename", labels)

    def test_breakdown_cardinality_is_bounded_and_source_errors_retain_usage(self):
        self._seed_usage()
        for index in range(10):
            _store_session(
                self.connection,
                self.codex_id,
                "codex",
                parsed_session(
                    "model-{}".format(index),
                    [
                        usage_fact(
                            "model-{}".format(index),
                            "2026-07-18T12:{:02d}:00Z".format(index),
                            "future-model-{}".format(index),
                        )
                    ],
                ),
            )
        self.connection.executemany(
            """
            INSERT INTO source_files(
                source_id, path, size_bytes, mtime_ns, last_scanned_at, status, error
            ) VALUES (?, ?, 1, 1, ?, ?, ?)
            """,
            [
                (
                    self.codex_id,
                    "/tmp/codex/healthy.jsonl",
                    "2026-07-17T09:00:00Z",
                    "ok",
                    None,
                ),
                (
                    self.codex_id,
                    "/tmp/codex/failed.jsonl",
                    "2026-07-18T09:00:00Z",
                    "error",
                    "synthetic parse failure",
                ),
            ],
        )
        result = usage_dashboard_data(
            self.connection,
            source="codex",
            metric="cost",
            breakdown="model",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertEqual(len(result["breakdown"]["primary_rows"]), 8)
        self.assertGreater(len(result["breakdown"]["overflow_rows"]), 0)
        self.assertTrue(result["has_usage"])
        self.assertEqual(result["freshness"]["status"], "error")
        codex = result["freshness"]["sources"][0]
        self.assertEqual(codex["last_successful_at"], "2026-07-17T09:00:00Z")
        self.assertEqual(codex["error_count"], 1)
        self.assertEqual(result["projection"]["status"], "stale")

    def test_current_month_projection_is_formula_versioned_partial_and_source_scoped(self):
        self._seed_usage()
        result = usage_dashboard_data(
            self.connection,
            metric="cost",
            timezone_name="UTC",
            today=date(2026, 7, 18),
            now=datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc),
        )
        projection = result["projection"]
        self.assertTrue(projection["visible"])
        self.assertEqual(projection["formula_version"], "calendar-elapsed-v1")
        self.assertEqual(projection["input_label"], "$0.0051")
        self.assertEqual(projection["value_label"], "$0.0090")
        self.assertEqual(projection["coverage_state"], "partial")
        self.assertEqual(projection["status"], "partial")
        self.assertEqual(projection["complete_days"], 17)

        claude = usage_dashboard_data(
            self.connection,
            source="claude",
            metric="cost",
            timezone_name="UTC",
            today=date(2026, 7, 18),
            now=datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc),
        )["projection"]
        self.assertEqual(claude["input_label"], "$0.0011")
        self.assertEqual(claude["coverage_state"], "complete")

    def test_projection_visibility_threshold_and_unavailable_states_are_distinct(self):
        self._seed_usage()
        tokens = usage_dashboard_data(
            self.connection,
            metric="tokens",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertFalse(tokens["projection"]["visible"])

        historical = usage_dashboard_data(
            self.connection,
            metric="cost",
            from_value="2026-07-01",
            to_value="2026-07-10",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertFalse(historical["projection"]["visible"])

        early = usage_dashboard_data(
            self.connection,
            metric="cost",
            timezone_name="UTC",
            today=date(2026, 7, 3),
        )
        self.assertTrue(early["projection"]["visible"])
        self.assertEqual(early["projection"]["status"], "insufficient_history")

        empty_connection = sqlite3.connect(":memory:")
        empty_connection.row_factory = sqlite3.Row
        empty_connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        empty = usage_dashboard_data(
            empty_connection,
            metric="cost",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertEqual(empty["projection"]["status"], "no_usage")
        empty_connection.close()

        unpriced_connection = sqlite3.connect(":memory:")
        unpriced_connection.row_factory = sqlite3.Row
        unpriced_connection.execute("PRAGMA foreign_keys = ON")
        unpriced_connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        source_id = unpriced_connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp')"
        ).lastrowid
        _store_session(
            unpriced_connection,
            source_id,
            "codex",
            parsed_session(
                "only-unpriced",
                [
                    usage_fact(
                        "only-unpriced",
                        "2026-07-18T09:00:00Z",
                        "future-model",
                    )
                ],
            ),
        )
        unpriced = usage_dashboard_data(
            unpriced_connection,
            metric="cost",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        self.assertEqual(unpriced["projection"]["status"], "unavailable")
        self.assertEqual(unpriced["projection"]["value_label"], "Unavailable")
        unpriced_connection.close()


if __name__ == "__main__":
    unittest.main()
