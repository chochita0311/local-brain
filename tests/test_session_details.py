import sqlite3
import unittest
from pathlib import Path

from localbrain.queries import (
    session_conversation_events,
    session_events,
    session_parent,
    session_subsessions,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class SessionDetailTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp/codex')"
        )
        self.parent = self._session("parent", "primary", event_count=4)
        self.child = self._session(
            "child", "subsession", parent_external_id="parent", parent_id=self.parent
        )
        self.grandchild = self._session(
            "grandchild",
            "subsession",
            parent_external_id="child",
            parent_id=self.child,
        )
        self.tool_only = self._session("tool-only", "primary", event_count=1)
        self.connection.executemany(
            """
            INSERT INTO activity_events(
                id, session_id, sequence, occurred_at, event_type, role,
                text, tool_name, source_line
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    "message-user",
                    self.parent,
                    10,
                    "2026-07-17T00:00:00Z",
                    "message",
                    "user",
                    "Bash와 exec 결과를 대화로 설명해줘",
                    None,
                    1,
                ),
                (
                    "tool-bash",
                    self.parent,
                    11,
                    "2026-07-17T00:00:01Z",
                    "tool_call",
                    "assistant",
                    None,
                    "Bash",
                    1,
                ),
                (
                    "message-assistant",
                    self.parent,
                    20,
                    "2026-07-17T00:01:00Z",
                    "message",
                    "assistant",
                    "Write 도구를 사용하지 않고 답했습니다.",
                    None,
                    2,
                ),
                (
                    "tool-write",
                    self.parent,
                    21,
                    "2026-07-17T00:01:01Z",
                    "tool_call",
                    "assistant",
                    None,
                    "Write",
                    2,
                ),
                (
                    "tool-only-event",
                    self.tool_only,
                    10,
                    "2026-07-17T00:02:00Z",
                    "tool_call",
                    "assistant",
                    None,
                    "exec",
                    1,
                ),
            ),
        )

    def tearDown(self):
        self.connection.close()

    def _session(
        self,
        external_id,
        role,
        parent_external_id=None,
        parent_id=None,
        event_count=0,
    ):
        return self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, external_id, source_path, title, event_count,
                session_role, parent_external_id, parent_session_id
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                external_id,
                "/tmp/{}.jsonl".format(external_id),
                external_id,
                event_count,
                role,
                parent_external_id,
                parent_id,
            ),
        ).lastrowid

    def test_conversation_filter_preserves_raw_events_and_message_text(self):
        conversation = session_conversation_events(self.connection, self.parent)
        raw = session_events(self.connection, self.parent)

        self.assertEqual([row["role"] for row in conversation], ["user", "assistant"])
        self.assertEqual(
            [row["text"] for row in conversation],
            [
                "Bash와 exec 결과를 대화로 설명해줘",
                "Write 도구를 사용하지 않고 답했습니다.",
            ],
        )
        self.assertEqual(len(raw), 4)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM activity_events WHERE session_id = ?",
                (self.parent,),
            ).fetchone()[0],
            4,
        )

    def test_tool_only_session_has_an_empty_conversation_without_data_loss(self):
        self.assertEqual(
            session_conversation_events(self.connection, self.tool_only), []
        )
        self.assertEqual(len(session_events(self.connection, self.tool_only)), 1)

    def test_parent_and_child_queries_stop_at_one_direct_depth(self):
        self.assertEqual(session_parent(self.connection, self.child)["id"], self.parent)
        self.assertIsNone(session_parent(self.connection, self.grandchild))
        self.assertEqual(
            [row["id"] for row in session_subsessions(self.connection, self.parent)],
            [self.child],
        )
        self.assertEqual(session_subsessions(self.connection, self.child), [])


if __name__ == "__main__":
    unittest.main()
