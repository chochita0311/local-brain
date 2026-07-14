import sqlite3
import tempfile
import unittest
from pathlib import Path

from localbrain.workstreams import (
    add_link,
    create_checkpoint,
    create_thread,
    create_workstream,
    dashboard_overview,
    generate_suggestions,
    get_workstream,
    resolve_suggestion,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class WorkstreamTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.path = Path(handle.name)
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp')"
        )
        self.connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('claude', 'Claude', '/tmp/claude')"
        )
        source_id = self.connection.execute(
            "SELECT id FROM sources WHERE kind = 'codex'"
        ).fetchone()["id"]
        self.connection.execute(
            "INSERT INTO workspaces(canonical_path, display_name) VALUES ('/tmp/sample-project', 'sample-project')"
        )
        workspace_id = self.connection.execute(
            "SELECT id FROM workspaces WHERE display_name = 'sample-project'"
        ).fetchone()["id"]
        for external_id, title in (("one", "샘플 검색 필터 개선"), ("two", "샘플 내보내기")):
            self.connection.execute(
                """
                INSERT INTO sessions(
                    source_id, workspace_id, external_id, source_path, title,
                    last_event_at
                ) VALUES (?, ?, ?, ?, ?, '2026-07-13T02:00:00Z')
                """,
                (source_id, workspace_id, external_id, "/tmp/" + external_id, title),
            )
        claude_source_id = self.connection.execute(
            "SELECT id FROM sources WHERE kind = 'claude'"
        ).fetchone()["id"]
        self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, workspace_id, external_id, source_path, title,
                last_event_at
            ) VALUES (?, ?, 'claude-one', '/tmp/claude/one',
                      '샘플 검색 필터 설정', '2026-07-13T03:00:00Z')
            """,
            (claude_source_id, workspace_id),
        )
        self.connection.commit()

    def tearDown(self):
        self.connection.close()
        self.path.unlink(missing_ok=True)

    def test_workstream_thread_checkpoint_and_links(self):
        workstream_id = create_workstream(
            self.connection, "검색 경험 개선", "기능 개발"
        )
        thread_id = create_thread(
            self.connection, workstream_id, "검색 필터 개선", None, "로그인 연결", "설정 확인"
        )
        session_id = self.connection.execute(
            "SELECT id FROM sessions WHERE external_id = 'one'"
        ).fetchone()["id"]
        add_link(
            self.connection, "thread", thread_id, "session", str(session_id), "evidence"
        )
        create_checkpoint(
            self.connection,
            workstream_id,
            "검색 필터 완료",
            "설정 확인",
            None,
            None,
            "테스트",
            None,
        )
        item = get_workstream(self.connection, workstream_id)
        self.assertEqual(item["threads"][0]["links"][0]["title"], "샘플 검색 필터 개선")
        self.assertEqual(item["checkpoint"]["version"], 1)
        self.assertEqual(item["checkpoint"]["resource_count"], 1)
        self.assertEqual(item["checkpoint"]["resources"][0]["thread_id"], thread_id)
        self.assertEqual(dashboard_overview(self.connection)["metrics"]["active_threads"], 1)

    def test_suggestions_remain_pending(self):
        workstream_id = create_workstream(
            self.connection, "검색 경험 개선", "검색 기능"
        )
        create_thread(
            self.connection, workstream_id, "검색 필터 개선", None, "샘플 검색 필터", None
        )
        created = generate_suggestions(self.connection, workstream_id)
        item = get_workstream(self.connection, workstream_id)
        self.assertGreater(created, 0)
        self.assertGreater(len(item["suggestions"]), 0)
        labels = {suggestion["resource_label"] for suggestion in item["suggestions"]}
        self.assertIn("Claude Session", labels)
        self.assertIn("Codex Session", labels)
        self.assertEqual(item["links"], [])
        suggestion_id = item["suggestions"][0]["id"]
        resolve_suggestion(self.connection, suggestion_id, "reject")
        item = get_workstream(self.connection, workstream_id)
        self.assertEqual(len(item["excluded_suggestions"]), 1)
        self.assertNotIn(
            suggestion_id, {suggestion["id"] for suggestion in item["suggestions"]}
        )
        resolve_suggestion(self.connection, suggestion_id, "restore")
        item = get_workstream(self.connection, workstream_id)
        self.assertIn(
            suggestion_id, {suggestion["id"] for suggestion in item["suggestions"]}
        )
        self.assertEqual(item["excluded_suggestions"], [])
