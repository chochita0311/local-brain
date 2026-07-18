import sqlite3
import unittest
from pathlib import Path

from localbrain.db import _run_compatible_migrations
from localbrain.ingest.common import ParsedEvent, ParsedSession
from localbrain.ingest.scanner import _reconcile_session_parents, _store_session
from localbrain.queries import (
    daily_activity,
    dashboard_stats,
    project_activity,
    recent_sessions,
    session_detail,
    source_activity,
    top_tools,
    top_workspace_activity,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


def connection_for(schema: str) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(schema)
    return connection


def legacy_schema() -> str:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    schema = schema.replace("    git_branch TEXT,\n", "", 1)
    schema = schema.replace("    git_root TEXT,\n", "    git_root TEXT,\n    git_branch TEXT,\n", 1)
    schema = schema.replace(
        "    session_role TEXT NOT NULL DEFAULT 'primary'\n"
        "        CHECK(session_role IN ('primary', 'subsession')),\n"
        "    parent_external_id TEXT,\n"
        "    parent_session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,\n",
        "",
    )
    return schema


def parsed_session(
    external_id: str,
    role: str = "primary",
    parent_external_id: str = None,
) -> ParsedSession:
    return ParsedSession(
        external_id=external_id,
        source_path="/tmp/{}.jsonl".format(external_id),
        cwd_raw="/tmp",
        git_branch="feature/{}".format(external_id),
        title=external_id,
        started_at="2026-07-17T00:00:00Z",
        ended_at="2026-07-17T00:01:00Z",
        last_event_at="2026-07-17T00:01:00Z",
        events=[
            ParsedEvent(
                event_id="event-{}".format(external_id),
                sequence=10,
                source_line=1,
                event_type="message",
                role="user",
                text="shared contract evidence",
            ),
            ParsedEvent(
                event_id="tool-{}".format(external_id),
                sequence=20,
                source_line=2,
                event_type="tool_call",
                role="assistant",
                text="tool evidence",
                tool_name="Read",
            ),
        ],
        session_role=role,
        parent_external_id=parent_external_id,
    )


class SessionContractTests(unittest.TestCase):
    def test_compatible_migration_preserves_workspace_identity_and_stales_sources(self):
        connection = connection_for(legacy_schema())
        self.addCleanup(connection.close)
        source_id = connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp')"
        ).lastrowid
        connection.execute(
            """
            INSERT INTO source_files(
                source_id, path, size_bytes, mtime_ns, last_scanned_at, status
            ) VALUES (?, '/tmp/session.jsonl', 1, 1, '2026-07-17', 'ok')
            """,
            (source_id,),
        )
        workspace_id = connection.execute(
            """
            INSERT INTO workspaces(canonical_path, display_name, git_root, git_branch)
            VALUES ('/tmp/project', 'project', '/tmp/project', 'stale-branch')
            """
        ).lastrowid
        connection.execute(
            "INSERT INTO workstreams(name) VALUES ('Schema migration')"
        )
        connection.execute(
            "INSERT INTO context_roots(path, label) VALUES ('/tmp/context', 'context')"
        )
        connection.execute(
            """
            INSERT INTO workstream_links(workstream_id, entity_type, entity_id)
            VALUES (1, 'project', ?)
            """,
            (str(workspace_id),),
        )
        _run_compatible_migrations(connection)

        workspace_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(workspaces)")
        }
        session_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(sessions)")
        }
        self.assertNotIn("git_branch", workspace_columns)
        self.assertTrue(
            {"git_branch", "session_role", "parent_external_id", "parent_session_id"}
            <= session_columns
        )
        self.assertEqual(
            connection.execute("SELECT id FROM workspaces").fetchone()["id"],
            workspace_id,
        )
        self.assertEqual(
            connection.execute("SELECT entity_id FROM workstream_links").fetchone()[
                "entity_id"
            ],
            str(workspace_id),
        )
        self.assertEqual(
            connection.execute("SELECT status FROM source_files").fetchone()["status"],
            "stale",
        )

    def test_parent_reconciliation_and_primary_consumers(self):
        connection = connection_for(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.addCleanup(connection.close)
        source_id = connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp')"
        ).lastrowid
        _store_session(
            connection,
            source_id,
            "codex",
            parsed_session("child", "subsession", "parent"),
        )
        _store_session(connection, source_id, "codex", parsed_session("parent"))
        _store_session(
            connection,
            source_id,
            "codex",
            parsed_session("grandchild", "subsession", "child"),
        )
        _reconcile_session_parents(connection, source_id, "codex")

        rows = {
            row["external_id"]: row
            for row in connection.execute(
                """
                SELECT id, external_id, session_role, parent_external_id,
                       parent_session_id, git_branch
                FROM sessions
                """
            )
        }
        self.assertEqual(rows["child"]["parent_session_id"], rows["parent"]["id"])
        self.assertEqual(
            rows["grandchild"]["parent_session_id"], rows["child"]["id"]
        )
        self.assertEqual(rows["child"]["git_branch"], "feature/child")
        self.assertEqual([row["external_id"] for row in recent_sessions(connection)], ["parent"])
        self.assertEqual(dashboard_stats(connection)["sessions"], 1)
        self.assertEqual(dashboard_stats(connection)["events"], 2)
        self.assertEqual(sum(row["session_count"] for row in daily_activity(connection)), 1)
        self.assertEqual(source_activity(connection)[0]["session_count"], 1)
        self.assertEqual(source_activity(connection)[0]["event_count"], 2)
        self.assertEqual(top_tools(connection)[0]["use_count"], 1)
        self.assertEqual(top_workspace_activity(connection)[0]["session_count"], 1)
        self.assertEqual(project_activity(connection)[0]["session_count"], 1)
        self.assertIsNotNone(session_detail(connection, rows["parent"]["id"]))
        self.assertIsNotNone(session_detail(connection, rows["child"]["id"]))
        self.assertIsNone(session_detail(connection, rows["grandchild"]["id"]))
        search_ids = {
            row["entity_id"]
            for row in connection.execute(
                "SELECT entity_id FROM search_index WHERE entity_type = 'session'"
            )
        }
        self.assertEqual(search_ids, {str(rows["parent"]["id"])})

        connection.execute("DELETE FROM sessions WHERE id = ?", (rows["parent"]["id"],))
        child = connection.execute(
            """
            SELECT session_role, parent_external_id, parent_session_id
            FROM sessions WHERE external_id = 'child'
            """
        ).fetchone()
        self.assertEqual(child["session_role"], "subsession")
        self.assertEqual(child["parent_external_id"], "parent")
        self.assertIsNone(child["parent_session_id"])

    def test_cycles_and_missing_parents_remain_unresolved(self):
        connection = connection_for(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.addCleanup(connection.close)
        source_id = connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp')"
        ).lastrowid
        for item in (
            parsed_session("cycle-a", "subsession", "cycle-b"),
            parsed_session("cycle-b", "subsession", "cycle-a"),
            parsed_session("missing", "subsession", "not-imported"),
        ):
            _store_session(connection, source_id, "codex", item)
        _reconcile_session_parents(connection, source_id, "codex")
        rows = connection.execute(
            "SELECT session_role, parent_session_id FROM sessions"
        ).fetchall()
        self.assertTrue(all(row["session_role"] == "subsession" for row in rows))
        self.assertTrue(all(row["parent_session_id"] is None for row in rows))
        self.assertEqual(recent_sessions(connection), [])
        session_ids = connection.execute("SELECT id FROM sessions").fetchall()
        self.assertTrue(
            all(session_detail(connection, row["id"]) is None for row in session_ids)
        )

    def test_existing_primary_reclassifies_without_losing_identity_or_links(self):
        connection = connection_for(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.addCleanup(connection.close)
        source_id = connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp')"
        ).lastrowid
        _store_session(connection, source_id, "codex", parsed_session("parent"))
        _store_session(connection, source_id, "codex", parsed_session("child"))
        original_id = connection.execute(
            "SELECT id FROM sessions WHERE external_id = 'child'"
        ).fetchone()["id"]
        self.assertIsNotNone(
            connection.execute(
                """
                SELECT 1 FROM search_index
                WHERE entity_type = 'session' AND entity_id = ?
                """,
                (str(original_id),),
            ).fetchone()
        )
        workstream_id = connection.execute(
            "INSERT INTO workstreams(name) VALUES ('Existing link')"
        ).lastrowid
        connection.execute(
            """
            INSERT INTO workstream_links(workstream_id, entity_type, entity_id)
            VALUES (?, 'session', ?)
            """,
            (workstream_id, str(original_id)),
        )

        _store_session(
            connection,
            source_id,
            "codex",
            parsed_session("child", "subsession", "parent"),
        )
        _reconcile_session_parents(connection, source_id, "codex")

        child = connection.execute(
            """
            SELECT id, session_role, parent_session_id
            FROM sessions WHERE external_id = 'child'
            """
        ).fetchone()
        parent_id = connection.execute(
            "SELECT id FROM sessions WHERE external_id = 'parent'"
        ).fetchone()["id"]
        self.assertEqual(child["id"], original_id)
        self.assertEqual(child["session_role"], "subsession")
        self.assertEqual(child["parent_session_id"], parent_id)
        self.assertIsNone(
            connection.execute(
                """
                SELECT 1 FROM search_index
                WHERE entity_type = 'session' AND entity_id = ?
                """,
                (str(original_id),),
            ).fetchone()
        )
        self.assertEqual(
            connection.execute(
                "SELECT entity_id FROM workstream_links WHERE workstream_id = ?",
                (workstream_id,),
            ).fetchone()["entity_id"],
            str(original_id),
        )
        self.assertEqual(
            [row["external_id"] for row in recent_sessions(connection)], ["parent"]
        )
        self.assertEqual(dashboard_stats(connection)["sessions"], 1)


if __name__ == "__main__":
    unittest.main()
