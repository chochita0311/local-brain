import asyncio
import sqlite3
import unittest
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlencode
from unittest.mock import patch

from starlette.requests import Request

from localbrain.main import app, pin_session_page, unpin_session_page
from localbrain.db import _run_compatible_migrations
from localbrain.session_pins import (
    SessionPinError,
    group_pinned_sessions,
    is_session_pinned,
    list_all_pinned_sessions,
    list_pinned_sessions,
    pin_session,
    unpin_session,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "src/localbrain/schema.sql"
PIN_DDL = """CREATE TABLE IF NOT EXISTS session_pins (
    session_id INTEGER PRIMARY KEY
        REFERENCES sessions(id) ON DELETE CASCADE,
    pinned_at TEXT NOT NULL
);

"""


def schema_connection(*, include_pin_table: bool = True) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    if not include_pin_table:
        if PIN_DDL not in schema:
            raise AssertionError("Session pin schema fixture no longer matches canonical DDL")
        schema = schema.replace(PIN_DDL, "", 1)
    connection.executescript(schema)
    return connection


def seed_sessions(connection: sqlite3.Connection) -> dict[str, int]:
    source_id = connection.execute(
        """
        INSERT INTO sources(kind, name, root_path)
        VALUES ('claude', 'Claude', '/synthetic/claude')
        """
    ).lastrowid
    workspace_id = connection.execute(
        """
        INSERT INTO workspaces(
            canonical_path, display_name, git_root, exists_now
        ) VALUES ('/synthetic/work', 'Synthetic Work', '/synthetic/work', 1)
        """
    ).lastrowid
    rows = {}
    for external_id, title, session_class, session_role in (
        ("primary-a", "Primary A", "work", "primary"),
        ("primary-b", "Primary B", "work", "primary"),
        ("child", "Child", "work", "subsession"),
        ("maintenance", "Maintenance", "maintenance", "primary"),
    ):
        rows[external_id] = connection.execute(
            """
            INSERT INTO sessions(
                source_id, workspace_id, external_id, source_path, cwd_raw,
                title, started_at, last_event_at, git_branch, session_class,
                session_role, index_policy
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                workspace_id,
                external_id,
                f"/synthetic/{external_id}.jsonl",
                "/synthetic/work",
                title,
                "2026-07-24T01:00:00+00:00",
                "2026-07-24T02:00:00+00:00",
                "feature/pins" if session_class == "work" else None,
                session_class,
                session_role,
                "metadata_only" if session_class == "maintenance" else "full",
            ),
        ).lastrowid
    return rows


class SessionPinSchemaTests(unittest.TestCase):
    def test_fresh_schema_uses_row_presence_and_session_cascade(self):
        connection = schema_connection()
        columns = {
            row["name"]: row
            for row in connection.execute("PRAGMA table_info(session_pins)")
        }
        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(session_pins)"
        ).fetchall()

        self.assertEqual(set(columns), {"session_id", "pinned_at"})
        self.assertEqual(columns["session_id"]["pk"], 1)
        self.assertEqual(columns["pinned_at"]["notnull"], 1)
        self.assertEqual(len(foreign_keys), 1)
        self.assertEqual(foreign_keys[0]["table"], "sessions")
        self.assertEqual(foreign_keys[0]["on_delete"], "CASCADE")
        connection.close()

    def test_compatible_startup_creates_table_without_changing_sessions(self):
        connection = schema_connection(include_pin_table=False)
        rows = seed_sessions(connection)
        before = [
            tuple(row)
            for row in connection.execute("SELECT * FROM sessions ORDER BY id")
        ]

        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _run_compatible_migrations(connection, include_data_migrations=False)

        after = [
            tuple(row)
            for row in connection.execute("SELECT * FROM sessions ORDER BY id")
        ]
        self.assertEqual(before, after)
        self.assertEqual(
            connection.execute(
                "SELECT COUNT(*) FROM session_pins"
            ).fetchone()[0],
            0,
        )
        self.assertIn(rows["primary-a"], [row[0] for row in after])
        connection.close()


class SessionPinOperationTests(unittest.TestCase):
    def setUp(self):
        self.connection = schema_connection()
        self.rows = seed_sessions(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_pin_is_idempotent_and_unpin_then_repin_gets_new_time(self):
        session_id = self.rows["primary-a"]
        first = pin_session(
            self.connection,
            session_id,
            pinned_at="2026-07-24T03:00:00+00:00",
        )
        repeated = pin_session(
            self.connection,
            session_id,
            pinned_at="2026-07-24T04:00:00+00:00",
        )

        self.assertEqual(first["pinned_at"], "2026-07-24T03:00:00+00:00")
        self.assertEqual(repeated["pinned_at"], first["pinned_at"])
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM session_pins WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0],
            1,
        )
        self.assertTrue(is_session_pinned(self.connection, session_id))
        self.assertTrue(unpin_session(self.connection, session_id))
        self.assertFalse(unpin_session(self.connection, session_id))
        self.assertFalse(is_session_pinned(self.connection, session_id))

        repinned = pin_session(
            self.connection,
            session_id,
            pinned_at="2026-07-24T05:00:00+00:00",
        )
        self.assertEqual(repinned["pinned_at"], "2026-07-24T05:00:00+00:00")

    def test_missing_maintenance_and_subsession_are_rejected(self):
        cases = (
            (999999, "session-not-found"),
            (self.rows["maintenance"], "maintenance-session-ineligible"),
            (self.rows["child"], "subsession-ineligible"),
        )
        for session_id, code in cases:
            with self.subTest(code=code), self.assertRaises(SessionPinError) as raised:
                pin_session(self.connection, session_id)
            self.assertEqual(raised.exception.code, code)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM session_pins").fetchone()[0],
            0,
        )

    def test_pinned_list_orders_by_displayed_activity_and_contains_orientation(self):
        self.connection.execute(
            """
            UPDATE sessions
            SET started_at = '2026-07-25T02:00:00+00:00',
                last_event_at = NULL
            WHERE id = ?
            """,
            (self.rows["primary-a"],),
        )
        pin_session(
            self.connection,
            self.rows["primary-a"],
            pinned_at="2026-07-24T03:00:00+00:00",
        )
        pin_session(
            self.connection,
            self.rows["primary-b"],
            pinned_at="2026-07-24T04:00:00+00:00",
        )

        rows = list_pinned_sessions(self.connection)

        self.assertEqual(
            [row["id"] for row in rows],
            [self.rows["primary-a"], self.rows["primary-b"]],
        )
        self.assertIsNone(rows[0]["last_event_at"])
        self.assertEqual(rows[0]["started_at"], "2026-07-25T02:00:00+00:00")
        self.assertEqual(rows[0]["source_kind"], "claude")
        self.assertEqual(rows[0]["git_branch"], "feature/pins")
        self.assertEqual(rows[0]["workspace_name"], "Synthetic Work")
        self.assertEqual(rows[0]["workspace_path"], "/synthetic/work")
        self.assertEqual(rows[0]["workspace_git_root"], "/synthetic/work")
        self.assertEqual(rows[0]["workspace_exists_now"], 1)
        with self.assertRaisesRegex(SessionPinError, "between 1 and 100"):
            list_pinned_sessions(self.connection, limit=0)

    def test_groups_git_projects_first_then_alphabetically_and_keeps_inner_activity_order(self):
        source_id = self.connection.execute(
            "SELECT id FROM sources WHERE kind = 'claude'"
        ).fetchone()[0]

        def workspace(name, *, git):
            path = "/synthetic/{}".format(name.replace("/", "-"))
            return self.connection.execute(
                """
                INSERT INTO workspaces(
                    canonical_path, display_name, git_root, exists_now
                ) VALUES (?, ?, ?, 1)
                """,
                (path, name, path if git else None),
            ).lastrowid

        def pinned(workspace_id, external_id, activity):
            session_id = self.connection.execute(
                """
                INSERT INTO sessions(
                    source_id, workspace_id, external_id, source_path, cwd_raw,
                    title, started_at, last_event_at, git_branch
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    workspace_id,
                    external_id,
                    "/synthetic/{}.jsonl".format(external_id),
                    "/synthetic/{}".format(external_id),
                    external_id,
                    "2026-07-20T01:00:00+00:00",
                    activity,
                    "feature/{}".format(external_id),
                ),
            ).lastrowid
            pin_session(
                self.connection,
                session_id,
                pinned_at="2026-07-24T03:00:00+00:00",
            )
            return session_id

        alpha_workspace = workspace("alpha", git=True)
        bravo_workspace = workspace("Bravo", git=True)
        folder_workspace = workspace("folder/reference-notes", git=False)
        alpha_old = pinned(
            alpha_workspace, "alpha-old", "2026-07-22T02:00:00+00:00"
        )
        bravo = pinned(
            bravo_workspace, "bravo", "2026-07-28T02:00:00+00:00"
        )
        alpha_new = pinned(
            alpha_workspace, "alpha-new", "2026-07-29T02:00:00+00:00"
        )
        folder = pinned(
            folder_workspace, "folder", "2026-07-30T02:00:00+00:00"
        )

        groups = group_pinned_sessions(list_all_pinned_sessions(self.connection))

        self.assertEqual(
            [group["workspace_name"] for group in groups],
            ["alpha", "Bravo", "folder/reference-notes"],
        )
        self.assertEqual(
            [row["id"] for row in groups[0]["sessions"]],
            [alpha_new, alpha_old],
        )
        self.assertEqual([row["id"] for row in groups[1]["sessions"]], [bravo])
        self.assertEqual(
            [row["id"] for row in groups[2]["sessions"]], [folder]
        )
        self.assertTrue(groups[0]["is_git"])
        self.assertFalse(groups[2]["is_git"])

    def test_all_pinned_list_has_no_silent_product_cap(self):
        source_id = self.connection.execute(
            "SELECT id FROM sources WHERE kind = 'claude'"
        ).fetchone()[0]
        workspace_id = self.connection.execute(
            "SELECT id FROM workspaces WHERE canonical_path = '/synthetic/work'"
        ).fetchone()[0]
        for number in range(101):
            session_id = self.connection.execute(
                """
                INSERT INTO sessions(
                    source_id, workspace_id, external_id, source_path, cwd_raw,
                    title, started_at, last_event_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    workspace_id,
                    "bulk-{}".format(number),
                    "/synthetic/bulk-{}.jsonl".format(number),
                    "/synthetic/work",
                    "Bulk {}".format(number),
                    "2026-07-24T01:00:00+00:00",
                    "2026-07-24T02:00:00+00:00",
                ),
            ).lastrowid
            pin_session(
                self.connection,
                session_id,
                pinned_at="2026-07-24T03:{:02d}:00+00:00".format(number % 60),
            )

        rows = list_all_pinned_sessions(self.connection)

        self.assertEqual(len(rows), 101)
        self.assertGreaterEqual(rows[0]["pinned_at"], rows[-1]["pinned_at"])

    def test_normal_update_preserves_pin_and_session_delete_cascades(self):
        session_id = self.rows["primary-a"]
        pin_session(
            self.connection,
            session_id,
            pinned_at="2026-07-24T03:00:00+00:00",
        )

        self.connection.execute(
            """
            UPDATE sessions
            SET title = 'Updated from stable source identity',
                imported_at = '2026-07-24T06:00:00+00:00'
            WHERE id = ?
            """,
            (session_id,),
        )
        self.assertTrue(is_session_pinned(self.connection, session_id))

        self.connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.assertFalse(is_session_pinned(self.connection, session_id))


class SessionPinRouteTests(unittest.TestCase):
    def setUp(self):
        self.connection = schema_connection()
        self.rows = seed_sessions(self.connection)

    def tearDown(self):
        self.connection.close()

    @contextmanager
    def _transaction(self):
        yield self.connection

    @staticmethod
    def _request(path: str, values: dict) -> Request:
        body = urlencode(values).encode("utf-8")
        delivered = False

        async def receive():
            nonlocal delivered
            if delivered:
                return {"type": "http.disconnect"}
            delivered = True
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }

        return Request(
            {
                "type": "http",
                "app": app,
                "method": "POST",
                "path": path,
                "headers": [
                    (b"content-type", b"application/x-www-form-urlencoded")
                ],
                "query_string": b"",
                "server": ("test", 80),
                "client": ("test", 1),
                "scheme": "http",
            },
            receive,
        )

    def test_pin_and_unpin_preserve_inventory_scope_and_focus_target(self):
        session_id = self.rows["primary-a"]
        return_to = "/sessions?source=codex&workspace=7&page=3"
        with patch("localbrain.main.transaction", self._transaction):
            pinned = asyncio.run(
                pin_session_page(
                    self._request(
                        "/sessions/{}/pin".format(session_id),
                        {"return_to": return_to},
                    ),
                    session_id,
                )
            )
            unpinned = asyncio.run(
                unpin_session_page(
                    self._request(
                        "/sessions/{}/unpin".format(session_id),
                        {"return_to": return_to},
                    ),
                    session_id,
                )
            )

        expected = (
            "/sessions?source=codex&workspace=7&page=3"
            "#session-pin-{}".format(session_id)
        )
        self.assertEqual(pinned.status_code, 303)
        self.assertEqual(pinned.headers["location"], expected)
        self.assertEqual(unpinned.headers["location"], expected)
        self.assertFalse(is_session_pinned(self.connection, session_id))

    def test_pin_rejects_missing_session_and_external_return_destination(self):
        missing_id = 999999
        with patch("localbrain.main.transaction", self._transaction):
            response = asyncio.run(
                pin_session_page(
                    self._request(
                        "/sessions/{}/pin".format(missing_id),
                        {
                            "return_to": (
                                "https://outside.example/sessions/1"
                                "?source=private"
                            )
                        },
                    ),
                    missing_id,
                )
            )

        self.assertEqual(
            response.headers["location"],
            "/sessions?pin_error=missing&pin_session=999999"
            "#session-pin-999999",
        )


if __name__ == "__main__":
    unittest.main()
