import asyncio
import json
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

from fastapi import HTTPException
from starlette.requests import Request

from localbrain.app.edition import _ALLOWED
from localbrain.foundation.config import Settings
from localbrain.ingest.sync.session_store import _store_session
from localbrain.persistence.bootstrap import initialize_database
from localbrain.persistence.migrations.sessions import (
    SESSION_DISPLAY_TITLE_BACKUP_SUFFIX, _repair_maintenance_session_contract,
    _session_display_title_current,
)
from localbrain.sessions.pins import list_all_pinned_sessions
from localbrain.sessions.queries import session_chart_inventory
from localbrain.sessions.titles import SessionTitleError, set_display_title
from localbrain.sessions.web import save_session_title
from test_activity_attribution import parsed_session, usage_record
from test_session_pins import seed_sessions


SCHEMA = (Path(__file__).parents[1] / "src/localbrain/schema.sql").read_text()


class SessionTitleTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:", check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA)
        self.addCleanup(self.connection.close)
        self.ids = seed_sessions(self.connection)
        self.session_id = self.ids["primary-a"]

    def test_override_clear_and_sync_preserve_source_and_user_ownership(self):
        connection, ident = self.connection, self.session_id
        before = dict(connection.execute("SELECT * FROM sessions WHERE id=?", (ident,)).fetchone())
        saved = set_display_title(connection, ident, "  내 작업 제목  ")
        self.assertEqual(saved["display_title"], "내 작업 제목")
        after = dict(connection.execute("SELECT * FROM sessions WHERE id=?", (ident,)).fetchone())
        self.assertEqual(after, {**before, "display_title": "내 작업 제목"})
        source = parsed_session("primary-a", "/synthetic/work", [usage_record("first")])
        _store_session(connection, before["source_id"], replace(source, title="Changed source title"))
        row = connection.execute("SELECT * FROM sessions WHERE id=?", (ident,)).fetchone()
        self.assertEqual((row["title"], row["display_title"]), ("Changed source title", "내 작업 제목"))
        self.assertEqual(set_display_title(connection, ident, "  ")["effective_title"], "Changed source title")
        self.assertIsNone(connection.execute("SELECT display_title FROM sessions WHERE id=?", (ident,)).fetchone()[0])

    def test_validation_and_ineligible_sessions_never_mutate(self):
        before = list(self.connection.iterdump())
        for value in (None, 42, "x" * 501, "a\nb", "a\tb", "a\u2028b"):
            with self.subTest(value=repr(value)), self.assertRaises(SessionTitleError):
                set_display_title(self.connection, self.session_id, value)
        for ident in (self.ids["child"], self.ids["maintenance"], 999999):
            with self.assertRaises(SessionTitleError):
                set_display_title(self.connection, ident, "Override")
        self.assertEqual(list(self.connection.iterdump()), before)

    def test_pins_and_chart_present_override_without_changing_source_title(self):
        self.connection.execute("INSERT INTO session_pins VALUES (?, 'fixed')", (self.session_id,))
        set_display_title(self.connection, self.session_id, "Override")
        pin = list_all_pinned_sessions(self.connection)[0]
        self.assertEqual((pin["title"], pin["display_title"]), ("Primary A", "Override"))
        chart = session_chart_inventory(self.connection)
        self.assertEqual(next(row["title"] for row in chart if row["id"] == self.session_id), "Override")

    def request(self, value="Alias", *, origin="http://127.0.0.1:8000", accept="application/json", return_to="/sessions?page=2&source=1"):
        body = urlencode({"display_title": value, "return_to": return_to}).encode()
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        return Request({"type": "http", "method": "POST", "scheme": "http",
                        "path": f"/sessions/{self.session_id}/title", "query_string": b"",
                        "server": ("127.0.0.1", 8000), "headers": [
                            (b"host", b"127.0.0.1:8000"),
                            (b"content-type", b"application/x-www-form-urlencoded"),
                            (b"origin", origin.encode()), (b"accept", accept.encode())]}, receive)

    def test_local_post_json_progressive_return_and_storage_failure(self):
        @contextmanager
        def transaction(**kwargs):
            yield self.connection
        with patch("localbrain.sessions.web.transaction", transaction):
            response = asyncio.run(save_session_title(self.request(), self.session_id))
            self.assertEqual(json.loads(response.body)["effective_title"], "Alias")
            response = asyncio.run(save_session_title(self.request("", accept="text/html"), self.session_id))
            self.assertEqual(response.headers["location"], f"/sessions?page=2&source=1#session-title-{self.session_id}")
            response = asyncio.run(save_session_title(self.request(accept="text/html", return_to="https://example.invalid"), self.session_id))
            self.assertEqual(response.headers["location"], f"/sessions#session-title-{self.session_id}")
            with self.assertRaises(HTTPException) as error:
                asyncio.run(save_session_title(self.request(origin="http://example.invalid"), self.session_id))
            self.assertEqual(error.exception.status_code, 400)
        with patch("localbrain.sessions.web.transaction", side_effect=sqlite3.OperationalError("unavailable")):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(save_session_title(self.request(), self.session_id))
            self.assertEqual(error.exception.status_code, 503)
        self.assertTrue(_ALLOWED.fullmatch(f"/sessions/{self.session_id}/title"))


class SessionTitleMigrationTests(unittest.TestCase):
    def test_upgrade_backup_order_relations_snapshots_indexes_and_repeat(self):
        for appended in (False, True):
            with self.subTest(appended=appended), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                config = Settings(root, root / "localbrain.db", root / "context", root / "claude", root / "codex", 20)
                connection = sqlite3.connect(config.database_path)
                connection.row_factory = sqlite3.Row
                connection.executescript(SCHEMA.replace("    display_title TEXT,\n", "", 1))
                ids = seed_sessions(connection)
                ident = ids["primary-a"]
                connection.execute("UPDATE sessions SET parent_session_id=? WHERE id=?", (ident, ids["child"]))
                connection.execute("INSERT INTO session_pins VALUES (?, 'fixed')", (ident,))
                connection.execute("CREATE INDEX title_test_index ON sessions(title)")
                source = parsed_session("primary-a", "/synthetic/work", [usage_record("migration")])
                source_id = connection.execute("SELECT source_id FROM sessions WHERE id=?", (ident,)).fetchone()[0]
                _store_session(connection, source_id, source)
                if appended:
                    connection.execute("ALTER TABLE sessions ADD COLUMN display_title TEXT")
                    connection.execute("UPDATE sessions SET display_title='Keep override' WHERE id=?", (ident,))
                tables = ("sessions", "activity_events", "usage_records", "session_pins")
                before = {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1")] for table in tables}
                connection.commit()
                initialize_database(connection, config)
                connection = sqlite3.connect(config.database_path)
                connection.row_factory = sqlite3.Row
                connection.execute("PRAGMA foreign_keys=ON")
                self.assertTrue(_session_display_title_current(connection))
                for table in tables:
                    after = [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1")]
                    expected = [{"display_title": None, **row} for row in before[table]] if table == "sessions" else before[table]
                    self.assertEqual(after, expected)
                self.assertIsNotNone(connection.execute("SELECT 1 FROM sqlite_master WHERE name='title_test_index'").fetchone())
                self.assertFalse(connection.execute("PRAGMA foreign_key_check").fetchall())
                backup = config.database_path.with_name(config.database_path.name + SESSION_DISPLAY_TITLE_BACKUP_SUFFIX)
                self.assertTrue(backup.is_file())
                backup_bytes = backup.read_bytes()
                statements = []
                connection.set_trace_callback(statements.append)
                initialize_database(connection, config)
                self.assertEqual(backup.read_bytes(), backup_bytes)
                self.assertFalse(any("ALTER TABLE sessions RENAME" in sql for sql in statements))

    def test_unexpected_shape_or_trigger_refuses_before_rebuild(self):
        for extra in ("ALTER TABLE sessions ADD COLUMN surprise TEXT", "CREATE TRIGGER title_test AFTER UPDATE ON sessions BEGIN SELECT 1; END"):
            with self.subTest(extra=extra), sqlite3.connect(":memory:") as connection:
                connection.row_factory = sqlite3.Row
                connection.executescript(SCHEMA.replace("    display_title TEXT,\n", "", 1))
                seed_sessions(connection)
                connection.execute(extra)
                before = list(connection.iterdump())
                with self.assertRaises(RuntimeError):
                    _repair_maintenance_session_contract(connection)
                self.assertEqual(list(connection.iterdump()), before)

    def test_fresh_schema_has_nullable_title_immediately_after_original(self):
        with sqlite3.connect(":memory:") as connection:
            connection.executescript(SCHEMA)
            self.assertTrue(_session_display_title_current(connection))
            connection.row_factory = sqlite3.Row
            self.assertFalse(_repair_maintenance_session_contract(connection))

    def test_unknown_constraints_are_preserved_by_refusing_the_upgrade(self):
        legacy = SCHEMA.replace("    display_title TEXT,\n", "", 1)
        variants = (
            legacy.replace("UNIQUE(source_id, external_id)", "UNIQUE(source_id, external_id), CHECK(length(title)>0)", 1),
            legacy.replace("workspace_id INTEGER REFERENCES workspaces(id) ON DELETE SET NULL", "workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE", 1),
            legacy.replace("    title TEXT NOT NULL,", "    title TEXT NOT NULL COLLATE NOCASE,", 1),
        )
        for schema in variants:
            with self.subTest(schema=schema[-40:]), sqlite3.connect(":memory:") as connection:
                connection.row_factory = sqlite3.Row
                connection.executescript(schema)
                seed_sessions(connection)
                before = list(connection.iterdump())
                with self.assertRaisesRegex(RuntimeError, "unexpected Session constraints"):
                    _repair_maintenance_session_contract(connection)
                self.assertEqual(list(connection.iterdump()), before)

    def test_copy_failure_rolls_back_table_data_indexes_and_fk_setting(self):
        class FailingCopy(sqlite3.Connection):
            def execute(self, sql, *args, **kwargs):
                if sql.startswith("INSERT INTO sessions (") and "SELECT" in sql:
                    raise sqlite3.OperationalError("synthetic copy failure")
                return super().execute(sql, *args, **kwargs)
        with sqlite3.connect(":memory:", factory=FailingCopy) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            connection.executescript(SCHEMA.replace("    display_title TEXT,\n", "", 1))
            seed_sessions(connection)
            connection.commit()
            before = list(connection.iterdump())
            with self.assertRaisesRegex(sqlite3.OperationalError, "synthetic copy failure"):
                _repair_maintenance_session_contract(connection)
            self.assertEqual(list(connection.iterdump()), before)
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
