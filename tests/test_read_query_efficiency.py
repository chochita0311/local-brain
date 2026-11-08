import sqlite3
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from localbrain.atlassian import browse
from localbrain.ingest.sync.session_store import _store_session
from localbrain.search.keyword import keyword_search
from localbrain.sessions.activity import parse_timestamp
from localbrain.sessions.queries import session_chart_inventory
from localbrain.usage.queries import _usage_rows, normalize_usage_scope, usage_dashboard_data
from natural_search_fixtures import fixture
from test_usage_dashboard import parsed_session, usage_record
import test_atlassian_browse as atlassian_fixture


class ReadQueryEfficiencyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="localbrain-query-efficiency-")
        self.addCleanup(temporary.cleanup)
        self.config = fixture(temporary.name)
        self.connection = sqlite3.connect(self.config.database_path)
        self.connection.row_factory = sqlite3.Row
        self.addCleanup(self.connection.close)

    def test_keyword_owner_join_preserves_root_guard_order_and_post_admission_limit(self):
        c = self.connection
        c.execute("DELETE FROM search_index")
        c.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (3,'codex','Moved source','/synthetic/moved')")
        for number in range(100, 190):
            source = 3 if number < 160 else 1
            c.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title) VALUES (?,?,?,?,?)",
                      (number, source, str(number), f"/synthetic/{number}.jsonl", "needle"))
            c.execute("INSERT INTO search_index VALUES ('session',?,'codex','needle','needle','/synthetic')", (str(number),))
        c.execute("UPDATE sessions SET session_role='subsession' WHERE id=160")
        c.execute("UPDATE sessions SET session_class='maintenance' WHERE id=161")
        statements = []
        c.set_trace_callback(statements.append)
        roots = {1: str(self.config.codex_root), 3: "/synthetic/old-root"}
        with patch("localbrain.search.keyword.registered_session_roots", return_value=roots):
            results = keyword_search(c, "needle", scope="sessions", limit=5, config=self.config)
        self.assertEqual([row["entity_id"] for row in results], [str(n) for n in range(162, 167)])
        self.assertTrue(all(row["source_id"] == 1 for row in results))
        self.assertTrue(all("owner_root" not in row and "owner_source_id" not in row for row in results))
        self.assertEqual(len([sql for sql in statements if sql.lstrip().upper().startswith("SELECT")]), 1)

    def test_chart_batches_only_undated_sessions_and_compares_parsed_instants(self):
        c = self.connection
        for ident in range(100, 1300):
            c.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title,started_at,last_event_at) VALUES (?,1,?,?,?,'bad',NULL)",
                      (ident, str(ident), f"/synthetic/{ident}.jsonl", f"Session {ident}"))
            times = (None, "invalid") if ident == 1299 else ("2026-01-01T01:00:00+02:00", "2025-12-31T23:30:00Z")
            for sequence, timestamp in enumerate(times):
                c.execute("INSERT INTO activity_events(id,session_id,sequence,occurred_at,event_type,source_line,text) VALUES (?,?,?,?, 'message',1,?)",
                          (f"{ident}-{sequence}", ident, sequence, timestamp, "unused synthetic body " * 50))
        statements = []
        c.set_trace_callback(statements.append)
        result = session_chart_inventory(c, source_id="1")
        self.assertEqual(len([sql for sql in statements if sql.lstrip().upper().startswith("SELECT")]), 4)
        item = next(row for row in result if row["id"] == 100)
        self.assertEqual(item["first_observed_at"], "2025-12-31T23:00:00+00:00")
        self.assertEqual(item["observed_at"], "2025-12-31T23:30:00+00:00")
        self.assertEqual(item["time_source"], "event")
        missing = next(row for row in result if row["id"] == 1299)
        self.assertEqual([missing[key] for key in ("first_observed_at", "observed_at", "time_source")], [None, None, None])
        statements.clear()
        self.assertEqual(session_chart_inventory(c, workspace_id=9999), [])
        self.assertEqual(len(statements), 1)

    def test_usage_partitions_preserve_order_exact_cost_offsets_and_untimed_counts(self):
        timestamps = [None, "", "invalid", "2026-02-30T12:00:00Z", "12:34:56",
                      " 2026-07-18T09:00:00Z ", "2026-07-18T09:00:00Z",
                      "2026-07-19T00:30:00+14:00", "2026-07-17T23:30:00-12:00",
                      "2026-W29-6T09:00:00Z", "20260718T090000Z",
                      "2026-08-01T00:00:00Z", "2026-07-17T00:00:00Z",
                      "2026-07-19T00:00:00Z", "2026-07-18T00:00:00+23:59"]
        c = self.connection
        costs = ("10000000000000000000000000000", "0.0000000000000000000000000001", "-10000000000000000000000000000")
        for number, timestamp in enumerate(timestamps):
            ident = f"edge-{number}"
            _store_session(c, 1, parsed_session(ident, [usage_record(ident, timestamp)]))
            c.execute("UPDATE usage_records SET calculation_state='priced', estimated_cost_usd=? WHERE source_record_id=?", (costs[number % 3], ident))
        before = c.total_changes
        full = list(_usage_rows(c, "all"))
        for zone in ("UTC", "Asia/Seoul", "America/New_York"):
            options = dict(from_value="2026-07-18", to_value="2026-07-18", timezone_name=zone, today=date(2026, 7, 18))
            scope = normalize_usage_scope(c, **options)
            expected = [(row, parse_timestamp(row["occurred_at"])) for row in full]
            selected = [(row, at) for row, at in expected if at is not None and scope["start_utc"] <= at < scope["end_utc"]]
            candidates = list(_usage_rows(c, "all", start_utc=scope["start_utc"], end_utc=scope["end_utc"], visible_only=True, include_unusual=True))
            selected_ids = [row["id"] for row in candidates if (at := parse_timestamp(row["occurred_at"])) is not None and scope["start_utc"] <= at < scope["end_utc"]]
            self.assertEqual(selected_ids, [row["id"] for row, _ in selected])
            total = Decimal(0)
            for row, _ in selected:
                total += Decimal(row["estimated_cost_usd"])
            for mode in ("source", "model", "project"):
                data = usage_dashboard_data(c, visible_only=True, breakdown=mode, **options)
                self.assertEqual(data["aggregate"]["usage_record_count"], len(selected))
                self.assertEqual(data["aggregate"]["estimated_cost"], total)
                untimed = sum(at is None for _, at in expected)
                self.assertIn(f"{untimed} usage records have no usable occurrence time and are excluded from history.", data["limitations"])
        self.assertEqual(c.total_changes, before)

    def test_atlassian_detail_matches_full_loading_and_projects_one_item(self):
        case = atlassian_fixture.AtlassianBrowseTests()
        case.setUp()
        self.addCleanup(case.tearDown)
        c = case.connection
        full_loader = browse._item_rows
        for item in full_loader(c):
            ident = item["id"]
            with patch.object(browse, "_item_rows", side_effect=lambda connection, **kwargs: full_loader(connection)):
                expected = browse.atlassian_item_detail(c, ident)
            with patch.object(browse, "project_atlassian_item_container", wraps=browse.project_atlassian_item_container) as project:
                actual = browse.atlassian_item_detail(c, ident)
            self.assertEqual(actual, expected)
            self.assertEqual(project.call_count, 1)
        self.assertIsNone(browse.atlassian_item_detail(c, 999999))
        self.assertIsNone(browse.atlassian_item_detail(c, 2**100))
        self.assertIsNone(browse.atlassian_item_detail(c, -(2**100)))
