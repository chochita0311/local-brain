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


if __name__ == "__main__":
    unittest.main()
