import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from localbrain.queries import session_chart_activity, session_chart_inventory
from localbrain.session_chart_preferences import (
    get_project_visibility,
    set_project_visibility,
    validate_hidden_projects,
)


SCHEMA = Path(__file__).resolve().parents[1] / "src/localbrain/schema.sql"


def connection_for(path=":memory:"):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    return connection


class SessionChartPreferenceTests(unittest.TestCase):
    def setUp(self):
        self.connection = connection_for()
        self.addCleanup(self.connection.close)

    def test_absent_and_explicit_all_selected_remain_distinct(self):
        self.assertIsNone(get_project_visibility(self.connection, "all", None))
        self.assertEqual(set_project_visibility(self.connection, "all", None, []), [])
        self.assertEqual(get_project_visibility(self.connection, "all", None), [])

    def test_scope_and_missing_folder_keys_are_retained_independently(self):
        set_project_visibility(self.connection, "all", None, ["", "/demo/absent"])
        set_project_visibility(self.connection, "1", 7, ["/demo/other"])
        self.assertEqual(get_project_visibility(self.connection, "all", None), ["", "/demo/absent"])
        self.assertEqual(get_project_visibility(self.connection, "1", 7), ["/demo/other"])
        self.assertIsNone(get_project_visibility(self.connection, "codex", None))
        self.assertIsNone(get_project_visibility(self.connection, "all", 7))

    def test_migration_cannot_replace_an_explicit_empty_database_choice(self):
        set_project_visibility(self.connection, "all", None, [])
        actual = set_project_visibility(self.connection, "all", None, ["/demo/legacy"], only_if_missing=True)
        self.assertEqual(actual, [])
        self.assertEqual(get_project_visibility(self.connection, "all", None), [])

    def test_migration_creates_only_the_absent_scope(self):
        self.assertEqual(set_project_visibility(self.connection, "all", None, ["/demo/legacy"], only_if_missing=True), ["/demo/legacy"])
        self.assertEqual(set_project_visibility(self.connection, "all", None, ["/demo/stale"], only_if_missing=True), ["/demo/legacy"])
        self.assertEqual(set_project_visibility(self.connection, "all", None, []), [])

    def test_caller_transaction_owns_commit_and_rollback(self):
        set_project_visibility(self.connection, "all", None, ["/demo/pending"])
        self.connection.rollback()
        self.assertIsNone(get_project_visibility(self.connection, "all", None))
        set_project_visibility(self.connection, "all", None, ["/demo/saved"])
        self.connection.commit()
        self.connection.rollback()
        self.assertEqual(get_project_visibility(self.connection, "all", None), ["/demo/saved"])

    def test_committed_choice_survives_a_new_database_connection(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = str(Path(temporary) / "synthetic.sqlite")
            with connection_for(path) as first:
                set_project_visibility(first, "all", None, ["/demo/saved"])
            first.close()
            second = connection_for(path)
            try:
                self.assertEqual(get_project_visibility(second, "all", None), ["/demo/saved"])
            finally:
                second.close()

    def test_validation_normalizes_without_changing_folder_identity(self):
        self.assertEqual(validate_hidden_projects(["/demo/B", "", "/demo/A", "/demo/B"]), ["", "/demo/A", "/demo/B"])
        self.assertEqual(validate_hidden_projects(["/demo/a/../b"]), ["/demo/a/../b"])
        for value in (None, {}, "folder", [True], [1], ["x" * 4097], ["x"] * 2001, [str(i) + "한" * 4090 for i in range(6)]):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError):
                    validate_hidden_projects(value)

    def test_corrupt_saved_payload_is_reported_as_invalid(self):
        self.connection.execute("INSERT INTO session_chart_preferences VALUES ('all', '', '{}', '2026-01-01')")
        with self.assertRaises(ValueError):
            get_project_visibility(self.connection, "all", None)


class SessionChartObservationTests(unittest.TestCase):
    def setUp(self):
        self.connection = connection_for()
        self.addCleanup(self.connection.close)
        self.connection.execute("INSERT INTO sources(id, name, root_path, provider_kind) VALUES (1, 'Synthetic Codex', '/demo/input', 'codex')")
        self.connection.execute("INSERT INTO sources(id, name, root_path, provider_kind) VALUES (2, 'Synthetic Company', '/demo/company', 'codex')")
        self.connection.execute("INSERT INTO workspaces(id,canonical_path,display_name) VALUES (7,'/demo/registered','Synthetic Workspace')")

    def session(self, number, *, source=1, workspace=None, folder="/demo/project", branch="main", started="2026-01-01T00:00:00Z", latest="2026-01-02T00:00:00Z", session_class="work", role="primary"):
        self.connection.execute(
            "INSERT INTO sessions(id,source_id,workspace_id,external_id,source_path,title,cwd_raw,git_branch,started_at,last_event_at,session_class,session_role) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (number, source, workspace, str(number), "/demo/input/session-{}.jsonl".format(number), "Synthetic {}".format(number), folder, branch, started, latest, session_class, role),
        )

    def event(self, session_id, sequence, at):
        self.connection.execute(
            "INSERT INTO activity_events(id,session_id,sequence,occurred_at,event_type,source_line,text) VALUES (?,?,?,?,?,?,?)",
            ("event-{}-{}".format(session_id, sequence), session_id, sequence, at, "message", sequence, "Synthetic body is not chart metadata."),
        )

    def test_inventory_covers_all_ages_and_pages_with_exact_source_workspace_scope(self):
        for number in range(1, 22):
            self.session(number, workspace=7, started="2010-01-01T00:00:00Z")
        self.session(22, source=2)
        self.session(23, role="subsession")
        self.session(24, session_class="maintenance")
        self.assertEqual(len(session_chart_inventory(self.connection)), 22)
        self.assertEqual(len(session_chart_inventory(self.connection, "1", 7)), 21)
        self.assertEqual([item["id"] for item in session_chart_inventory(self.connection, "2")], [22])

    def test_folder_normalization_is_lexical_and_raw_head_is_preserved(self):
        self.session(1, folder="~/Projects/alpha/../beta", branch="HEAD")
        with mock.patch("localbrain.queries.Path.home", return_value=Path("/demo/home")), mock.patch("localbrain.queries.Path.resolve", side_effect=AssertionError("filesystem resolution is not chart identity")):
            item = session_chart_inventory(self.connection)[0]
        self.assertEqual(item["project_key"], "/demo/home/Projects/beta")
        self.assertEqual(item["project_name"], "beta")
        self.assertEqual(item["project_path"], "~/Projects/beta")
        self.assertEqual(item["cwd_raw"], "~/Projects/alpha/../beta")
        self.assertEqual(item["git_branch"], "HEAD")

    def test_metadata_time_wins_and_only_undated_metadata_uses_events(self):
        self.session(1)
        self.event(1, 1, "2000-01-01T00:00:00Z")
        self.session(2, started="invalid", latest=None)
        self.event(2, 1, "2026-03-01T00:00:00Z")
        self.event(2, 2, "2026-02-01T00:00:00Z")
        self.session(3, folder=None, started=None, latest=None)
        items = {item["id"]: item for item in session_chart_inventory(self.connection)}
        self.assertTrue(items[1]["first_observed_at"].startswith("2026-01-01"))
        self.assertEqual(items[1]["time_source"], "metadata")
        self.assertTrue(items[2]["first_observed_at"].startswith("2026-02-01"))
        self.assertTrue(items[2]["observed_at"].startswith("2026-03-01"))
        self.assertEqual(items[2]["time_source"], "event")
        self.assertIsNone(items[3]["observed_at"])
        self.assertIsNone(items[3]["time_source"])
        self.assertEqual(items[3]["project_key"], "")

    def test_activity_preserves_occurrences_and_counts_without_event_text(self):
        self.session(1)
        self.event(1, 1, "2026-01-02T00:00:00Z")
        self.event(1, 2, "2026-01-02T00:00:00Z")
        self.event(1, 3, "invalid")
        result = session_chart_activity(self.connection, 1)
        self.assertEqual(result["session_id"], 1)
        self.assertEqual(len(result["timestamps"]), 2)
        self.assertEqual(result["timestamps"][0], result["timestamps"][1])
        self.assertEqual(result["total_events"], 3)
        self.assertEqual(result["undated_events"], 1)
        self.assertEqual({entry["field"] for entry in result["metadata_times"]}, {"started_at", "last_event_at"})
        self.assertNotIn("Synthetic body", str(result))

    def test_activity_excludes_children_maintenance_and_missing_sessions(self):
        self.session(1, role="subsession")
        self.session(2, session_class="maintenance")
        for number in (1, 2, 99):
            self.assertIsNone(session_chart_activity(self.connection, number))
