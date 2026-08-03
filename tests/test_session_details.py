import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.ingest.common import ParsedEvent, ParsedSession
from localbrain.queries import (
    session_conversation_events,
    session_events,
    session_parent,
    session_subsessions,
)
from localbrain.session_reading import conversation_event_view, conversation_event_views
from localbrain.subagents import list_subagents


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

    def test_conversation_views_render_eligible_roles_without_mutating_events(self):
        conversation = session_conversation_events(self.connection, self.parent)
        original_rows = [dict(row) for row in conversation]
        views = conversation_event_views(conversation)

        self.assertEqual(
            [view["text"] for view in views],
            [row["text"] for row in original_rows],
        )
        self.assertEqual([view["sequence"] for view in views], [10, 20])
        self.assertTrue(all(view["render_state"] == "ready" for view in views))
        self.assertIn(
            "<p>Bash와 exec 결과를 대화로 설명해줘</p>",
            views[0]["rendered_body"],
        )
        self.assertEqual([dict(row) for row in conversation], original_rows)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM activity_events WHERE session_id = ?",
                (self.parent,),
            ).fetchone()[0],
            4,
        )

    def test_lazy_and_no_source_message_rendering_share_the_safe_contract(self):
        event = ParsedEvent(
            event_id="lazy-message",
            sequence=7,
            source_line=3,
            event_type="message",
            occurred_at="2026-07-17T00:03:00Z",
            role="assistant",
            text=(
                "# 응답\n\n[[note]] [relative](guide.md) "
                "[external](https://example.test/read) "
                "[unsafe](javascript:alert(1))"
            ),
        )
        view = conversation_event_view(event)

        self.assertEqual(view["text"], event.text)
        self.assertEqual(view["sequence"], 7)
        self.assertEqual(
            view["rendered_body"].count('data-reference-state="no-source"'),
            2,
        )
        self.assertIn('rel="noopener noreferrer external"', view["rendered_body"])
        self.assertNotIn('href="javascript:', view["rendered_body"])

    def test_lazy_subsession_summary_counts_user_messages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "parent.jsonl"
            subagent_root = Path(temp_dir) / "parent" / "subagents"
            subagent_root.mkdir(parents=True)
            child_path = subagent_root / "agent-child.jsonl"
            child_path.touch()
            parsed = ParsedSession(
                external_id="agent-child",
                source_path=str(child_path),
                cwd_raw=None,
                git_branch=None,
                title="Lazy child",
                started_at=None,
                ended_at=None,
                last_event_at="2026-07-17T00:03:00Z",
                parent_external_id="parent",
                session_role="subsession",
                events=[
                    ParsedEvent("user-1", 1, 1, "message", role="user"),
                    ParsedEvent("tool-1", 2, 2, "tool_call", role="assistant"),
                    ParsedEvent("assistant-1", 3, 3, "message", role="assistant"),
                    ParsedEvent("user-2", 4, 4, "message", role="user"),
                ],
            )

            with patch("localbrain.subagents.parse_claude_session", return_value=parsed):
                items = list_subagents(str(source_path), "parent")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["user_message_count"], 2)
        self.assertEqual(items[0]["event_count"], 4)

    def test_non_eligible_role_stays_plain_and_renderer_failure_is_local(self):
        structural = ParsedEvent(
            event_id="structural",
            sequence=1,
            source_line=1,
            event_type="message",
            role="system",
            text="# Do not render",
        )
        plain = conversation_event_view(structural)
        self.assertNotIn("rendered_body", plain)
        self.assertEqual(plain["text"], "# Do not render")

        eligible = ParsedEvent(
            event_id="fallback",
            sequence=2,
            source_line=2,
            event_type="message",
            role="user",
            text="<unsafe>",
        )
        with patch(
            "localbrain.markdown._MARKDOWN.render",
            side_effect=ValueError("synthetic"),
        ):
            fallback = conversation_event_view(eligible)
        self.assertEqual(fallback["render_state"], "fallback")
        self.assertIn("&lt;unsafe&gt;", fallback["rendered_body"])
        self.assertNotIn("synthetic", fallback["rendered_body"])

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
