import json
import tempfile
import unittest
from pathlib import Path

from localbrain.ingest.claude import parse_claude_session
from localbrain.ingest.codex import parse_codex_session


class ParserTests(unittest.TestCase):
    def _write_jsonl(self, records):
        temporary = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w")
        with temporary:
            for record in records:
                temporary.write(json.dumps(record) + "\n")
        return Path(temporary.name)

    def test_claude_parser_extracts_messages_and_tools(self):
        path = self._write_jsonl(
            [
                {
                    "type": "user",
                    "sessionId": "claude-1",
                    "timestamp": "2026-07-13T00:59:00Z",
                    "isMeta": True,
                    "message": {"content": "메타 안내"},
                },
                {
                    "type": "user",
                    "sessionId": "claude-1",
                    "timestamp": "2026-07-13T01:00:00Z",
                    "cwd": "/tmp/project",
                    "gitBranch": "main",
                    "message": {"content": "첫 질문"},
                },
                {
                    "type": "assistant",
                    "sessionId": "claude-1",
                    "timestamp": "2026-07-13T01:01:00Z",
                    "message": {
                        "content": [
                            {"type": "text", "text": "답변"},
                            {"type": "tool_use", "name": "Read", "input": {}},
                        ]
                    },
                },
            ]
        )
        parsed = parse_claude_session(path)
        self.assertEqual(parsed.external_id, "claude-1")
        self.assertEqual(parsed.title, "첫 질문")
        self.assertEqual(parsed.cwd_raw, "/tmp/project")
        self.assertEqual(parsed.git_branch, "main")
        self.assertEqual(parsed.session_role, "primary")
        self.assertEqual([event.event_type for event in parsed.events], ["message", "message", "tool_call"])

    def test_codex_parser_avoids_duplicate_response_messages(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-07-13T02:00:00Z",
                    "payload": {"id": "codex-1", "cwd": "/tmp/project"},
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-13T02:01:00Z",
                    "payload": {"type": "user_message", "message": "구현해줘"},
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-13T02:02:00Z",
                    "payload": {"type": "agent_message", "message": "구현했습니다"},
                },
                {
                    "type": "session_meta",
                    "timestamp": "2026-07-12T02:00:00Z",
                    "payload": {"id": "embedded-old-session", "cwd": "/tmp/old"},
                },
                {
                    "type": "response_item",
                    "timestamp": "2026-07-13T02:03:00Z",
                    "payload": {"type": "message", "role": "assistant", "content": []},
                },
            ]
        )
        parsed = parse_codex_session(path)
        self.assertEqual(parsed.external_id, "codex-1")
        self.assertEqual(parsed.cwd_raw, "/tmp/project")
        self.assertEqual(parsed.title, "구현해줘")
        self.assertEqual(len(parsed.events), 2)

    def test_codex_primary_metadata_owns_parent_and_branch(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-07-13T02:00:00Z",
                    "payload": {
                        "id": "codex-child",
                        "cwd": "/tmp/project",
                        "source": {"subagent": {"kind": "worker"}},
                        "parent_thread_id": "codex-parent",
                        "git": {"branch": " feature/session-ui "},
                    },
                },
                {
                    "type": "session_meta",
                    "timestamp": "2026-07-12T02:00:00Z",
                    "payload": {
                        "id": "embedded-old-session",
                        "parent_thread_id": "wrong-parent",
                        "git": {"branch": "wrong-branch"},
                    },
                },
            ]
        )
        parsed = parse_codex_session(path)
        self.assertEqual(parsed.external_id, "codex-child")
        self.assertEqual(parsed.session_role, "subsession")
        self.assertEqual(parsed.parent_external_id, "codex-parent")
        self.assertEqual(parsed.git_branch, "feature/session-ui")

    def test_claude_subagent_path_produces_parent_identity(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            parent_root = Path(temporary_directory) / "claude-parent"
            subagent_root = parent_root / "subagents"
            subagent_root.mkdir(parents=True)
            path = subagent_root / "agent-child.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "type": "assistant",
                        "sessionId": "claude-child",
                        "message": {"content": "정리 결과"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            parsed = parse_claude_session(path)
        self.assertEqual(parsed.session_role, "subsession")
        self.assertEqual(parsed.external_id, "agent-child")
        self.assertEqual(parsed.parent_external_id, "claude-parent")

    def test_maintenance_marker_changes_index_policy(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-07-13T02:00:00Z",
                    "payload": {"id": "maintenance-1", "cwd": "/tmp"},
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-13T02:01:00Z",
                    "payload": {
                        "type": "user_message",
                        "message": "[LOCALBRAIN_RUN: lb-123456789abc]\n[MODE: maintenance]\n정리해줘",
                    },
                },
            ]
        )
        parsed = parse_codex_session(path)
        self.assertEqual(parsed.session_class, "maintenance")
        self.assertEqual(parsed.index_policy, "metadata_only")
        self.assertEqual(parsed.maintenance_run_id, "lb-123456789abc")
        self.assertEqual(parsed.title, "LocalBrain maintenance · lb-123456789abc")

    def test_maintenance_marker_mentioned_mid_session_stays_work(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "payload": {"id": "ordinary", "cwd": "/tmp"},
                },
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "user_message",
                        "message": "테스트 문자열 [MODE: maintenance]와 lb-test를 구현해줘",
                    },
                },
            ]
        )
        parsed = parse_codex_session(path)
        self.assertEqual(parsed.session_class, "work")

    def test_claude_parser_keeps_only_visible_and_approved_result_url_evidence(self):
        path = self._write_jsonl(
            [
                {
                    "type": "user",
                    "sessionId": "claude-evidence",
                    "message": {
                        "content": "See https://jira.example.test/browse/SYN-7 and SYN-8"
                    },
                },
                {
                    "type": "assistant",
                    "sessionId": "claude-evidence",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "approved-call",
                                "name": "atlassian.searchJiraIssuesUsingJql",
                                "input": {"jql": "key = SYN-9"},
                            },
                            {
                                "type": "tool_use",
                                "id": "unapproved-call",
                                "name": "Read",
                                "input": {},
                            },
                        ]
                    },
                },
                {
                    "type": "user",
                    "sessionId": "claude-evidence",
                    "sourceToolAssistantUUID": "assistant-1",
                    "message": {
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": "approved-call",
                                "content": json.dumps(
                                    {
                                        "issues": [
                                            {
                                                "url": "https://jira.example.test/browse/SYN-9",
                                                "id": "9009",
                                                "summary": "Synthetic issue",
                                                "description": "must not be retained",
                                            }
                                        ]
                                    }
                                ),
                            },
                            {
                                "type": "tool_result",
                                "tool_use_id": "unapproved-call",
                                "content": json.dumps(
                                    {
                                        "url": "https://jira.example.test/browse/NOPE-1"
                                    }
                                ),
                            },
                        ]
                    },
                },
            ]
        )

        parsed = parse_claude_session(path)

        self.assertEqual(
            [item.observed_url for item in parsed.url_evidence],
            [
                "https://jira.example.test/browse/SYN-7",
                "https://jira.example.test/browse/SYN-9",
            ],
        )
        self.assertEqual(parsed.url_evidence[1].source_channel, "approved_tool_result")
        self.assertEqual(parsed.url_evidence[1].observed_remote_id, "9009")
        self.assertEqual(parsed.url_evidence[1].observed_title, "Synthetic issue")
        self.assertNotIn("description", parsed.url_evidence[1].__dict__)

    def test_codex_parser_associates_result_with_approved_call_id(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "payload": {"id": "codex-evidence", "cwd": "/tmp"},
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "call_id": "call-1",
                        "name": "mcp_gateway.gateway_dispatch",
                        "arguments": json.dumps(
                            {"capability": "wiki__getPageById"}
                        ),
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call_output",
                        "call_id": "call-1",
                        "output": json.dumps(
                            {
                                "page": {
                                    "webUrl": "https://wiki.example.test/wiki/spaces/SYN/pages/12/Page",
                                    "pageId": "12",
                                    "title": "Synthetic page",
                                    "body": "must not be retained",
                                }
                            }
                        ),
                    },
                },
            ]
        )

        parsed = parse_codex_session(path)

        self.assertEqual(len(parsed.url_evidence), 1)
        self.assertEqual(
            parsed.url_evidence[0].observed_url,
            "https://wiki.example.test/wiki/spaces/SYN/pages/12/Page",
        )
        self.assertEqual(parsed.url_evidence[0].observed_remote_id, "12")
        self.assertEqual(parsed.url_evidence[0].observed_title, "Synthetic page")


if __name__ == "__main__":
    unittest.main()
