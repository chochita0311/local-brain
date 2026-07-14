import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from localbrain.runner import (
    _extract_text,
    _extract_tool_uses,
    _is_mcp_tool,
    _structured_result,
    persist_structured_suggestions,
    prepare_run,
    render_structured_result,
    supersede_runner_suggestions,
)
from localbrain.workstreams import resolve_suggestion


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class RunnerTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.db_path = Path(handle.name)
        self.run_root = Path(tempfile.mkdtemp())
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.connection.execute(
            "INSERT INTO workstreams(name, summary) VALUES ('샘플 플랫폼 유지보수', '범위 정리')"
        )
        self.connection.execute(
            "INSERT INTO threads(workstream_id, title, current_goal) VALUES (1, '검색 필터 개선', '인증 흐름 확인')"
        )
        self.connection.commit()

    def tearDown(self):
        self.connection.close()
        for path in sorted(self.run_root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            else:
                path.rmdir()
        self.run_root.rmdir()
        self.db_path.unlink(missing_ok=True)

    def test_prepare_run_writes_reference_manifest_and_prompt(self):
        run_id = prepare_run(
            self.connection,
            1,
            "organize_resources",
            "검색 필터 관련 자원을 우선 확인",
            self.run_root,
            refresh_suggestions=True,
        )
        run = self.connection.execute(
            "SELECT * FROM maintenance_runs WHERE id = ?", (run_id,)
        ).fetchone()
        manifest = json.loads(Path(run["manifest_path"]).read_text(encoding="utf-8"))
        prompt = Path(run["prompt_path"]).read_text(encoding="utf-8")
        self.assertEqual(run["status"], "queued")
        self.assertEqual(run["refresh_suggestions"], 1)
        self.assertEqual(run["cwd"], str(Path.home()))
        self.assertEqual(manifest["workstream"]["name"], "샘플 플랫폼 유지보수")
        self.assertEqual(manifest["threads"][0]["title"], "검색 필터 개선")
        self.assertEqual(manifest["schema"], "localbrain.maintenance-context.v2")
        self.assertIn("candidate_resources", manifest)
        self.assertIn("thread_resource_matches", manifest)
        self.assertTrue(manifest["suggestion_refresh"]["enabled"])
        self.assertEqual(manifest["retrieval"]["policy"]["candidate_count_limit"], None)
        self.assertEqual(
            run["mcp_call_budget"],
            manifest["external_discovery"]["mcp_call_budget"],
        )
        self.assertIn("[MODE: maintenance]", prompt)
        self.assertIn("검색 필터 관련 자원을 우선 확인", prompt)
        self.assertIn("MCP", prompt)
        self.assertIn("제안 갱신 모드", prompt)

    def test_extracts_assistant_and_final_result_text(self):
        self.assertEqual(
            _extract_text(
                {
                    "type": "assistant",
                    "message": {"content": [{"type": "text", "text": "진행 중"}]},
                }
            ),
            "진행 중",
        )
        self.assertEqual(
            _extract_text({"type": "result", "result": "최종 결과"}), "최종 결과"
        )
        tool_uses = _extract_tool_uses(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "id": "one", "name": "Read"},
                        {
                            "type": "tool_use",
                            "id": "two",
                            "name": "mcp__gateway__searchSlack",
                        },
                    ]
                },
            }
        )
        self.assertEqual(len(tool_uses), 2)
        self.assertFalse(_is_mcp_tool(tool_uses[0]["name"]))
        self.assertTrue(_is_mcp_tool(tool_uses[1]["name"]))

    def test_unchanged_local_candidates_reuse_previous_analysis(self):
        first_run_id = prepare_run(
            self.connection, 1, "organize_resources", run_root=self.run_root
        )
        self.connection.execute(
            """
            UPDATE maintenance_runs
            SET status = 'completed', completed_at = '2026-07-14T01:00:00Z',
                structured_result_json = ?
            WHERE id = ?
            """,
            (
                json.dumps(
                    {
                        "summary": "이전 분석",
                        "resource_suggestions": [],
                        "checkpoint_draft": {},
                        "priority_review": "",
                    }
                ),
                first_run_id,
            ),
        )
        second_run_id = prepare_run(
            self.connection, 1, "organize_resources", run_root=self.run_root
        )
        second_run = self.connection.execute(
            "SELECT manifest_path FROM maintenance_runs WHERE id = ?", (second_run_id,)
        ).fetchone()
        manifest = json.loads(
            Path(second_run["manifest_path"]).read_text(encoding="utf-8")
        )
        self.assertTrue(
            manifest["previous_analysis"]["local_candidate_snapshot_unchanged"]
        )
        self.assertEqual(manifest["previous_analysis"]["run_id"], first_run_id)

    def test_structured_run_creates_reviewable_thread_resource(self):
        result = {
            "summary": "검색 필터 관련 로컬 자원을 확인했습니다.",
            "resource_suggestions": [
                {
                    "target_thread_id": 1,
                    "resource_type": "local_path",
                    "locator": str(self.run_root),
                    "title": "검색 필터 context",
                    "relation_type": "evidence",
                    "rationale": "인증 흐름 문서가 있는 경로",
                    "evidence": "manifest의 검색 필터 목표와 일치",
                    "confidence": 0.9,
                }
            ],
            "checkpoint_draft": {
                "current_goal": "인증 흐름 확인",
                "confirmed_facts": "관련 경로를 확인함",
                "recent_decisions": "",
                "open_questions": "",
                "next_actions": "설정 파일 검토",
                "files_to_open": str(self.run_root),
            },
            "priority_review": "검색 필터를 먼저 검토합니다.",
        }
        count = persist_structured_suggestions(
            self.connection, "lb-test", 1, result
        )
        self.assertEqual(count, 2)
        resource_suggestion = self.connection.execute(
            "SELECT * FROM suggestions WHERE suggestion_type = 'resource_link'"
        ).fetchone()
        self.assertEqual(resource_suggestion["target_type"], "thread")
        resolve_suggestion(self.connection, resource_suggestion["id"], "accept")
        linked = self.connection.execute(
            """
            SELECT local_resources.path
            FROM thread_links
            JOIN local_resources ON local_resources.id = thread_links.entity_id
            WHERE thread_links.thread_id = 1 AND thread_links.entity_type = 'local'
            """
        ).fetchone()
        self.assertEqual(linked["path"], str(self.run_root.resolve()))
        rendered = render_structured_result(result)
        self.assertIn("검색 필터 context", rendered)
        self.assertEqual(
            _structured_result({"structured_output": result})["summary"],
            result["summary"],
        )

    def test_refresh_replaces_pending_but_preserves_rejected_suggestions(self):
        result = {
            "resource_suggestions": [
                {
                    "target_thread_id": 1,
                    "resource_type": "jira",
                    "locator": "https://jira.example.test/browse/DEMO-1",
                    "title": "DEMO-1",
                    "relation_type": "evidence",
                    "rationale": "검색 필터 작업 티켓",
                    "evidence": "Jira에서 확인",
                    "confidence": 0.8,
                }
            ],
            "checkpoint_draft": {},
        }
        self.assertEqual(
            persist_structured_suggestions(self.connection, "lb-old", 1, result), 1
        )
        self.assertEqual(supersede_runner_suggestions(self.connection, 1), 1)
        self.assertEqual(
            persist_structured_suggestions(self.connection, "lb-new", 1, result), 1
        )
        suggestion = self.connection.execute(
            "SELECT * FROM suggestions WHERE suggestion_type = 'resource_link'"
        ).fetchone()
        self.assertEqual(suggestion["status"], "pending")
        self.assertEqual(suggestion["origin_run_id"], "lb-new")

        resolve_suggestion(self.connection, suggestion["id"], "reject")
        self.assertEqual(supersede_runner_suggestions(self.connection, 1), 0)
        self.assertEqual(
            persist_structured_suggestions(self.connection, "lb-next", 1, result), 0
        )
        suggestion = self.connection.execute(
            "SELECT * FROM suggestions WHERE id = ?", (suggestion["id"],)
        ).fetchone()
        self.assertEqual(suggestion["status"], "rejected")
        self.assertEqual(suggestion["origin_run_id"], "lb-next")
        resolve_suggestion(self.connection, suggestion["id"], "restore")
        status = self.connection.execute(
            "SELECT status FROM suggestions WHERE id = ?", (suggestion["id"],)
        ).fetchone()["status"]
        self.assertEqual(status, "pending")
