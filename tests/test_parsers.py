import json
import tempfile
import unittest
from pathlib import Path

from localbrain.ingest.claude import parse_claude_session
from localbrain.ingest.codex import parse_codex_session
from localbrain.ingest.common import (
    visible_reference_candidates,
    visible_url_evidence,
)


class ParserTests(unittest.TestCase):
    def _write_jsonl(self, records):
        temporary = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w")
        with temporary:
            for record in records:
                temporary.write(json.dumps(record) + "\n")
        return Path(temporary.name)

    def test_visible_url_boundary_excludes_markdown_close_and_korean_postposition(self):
        target = (
            "https://chat.example.test/archives/"
            "SYNTHETIC/p1234567890123456"
        )
        text = "관련 대화는 [{}]({})와 다음 자료를 참고하세요.".format(
            "Slack", target
        )

        references = visible_reference_candidates(
            text, role="user", source_line=1
        )
        evidence = visible_url_evidence(text, source_line=1)

        self.assertEqual(
            [item.reference for item in references if item.reference_kind == "url"],
            [target],
        )
        self.assertEqual([item.observed_url for item in evidence], [target])

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

    def test_claude_parser_normalizes_completed_and_tool_responses(self):
        path = self._write_jsonl([
            {"type": "user", "sessionId": "claude-phases", "message": {
                "content": "첫 질문", "stop_reason": "end_turn",
            }},
            {"type": "assistant", "message": {
                "id": "tool-message", "stop_reason": "tool_use", "content": [
                    {"type": "text", "text": "파일을 확인하겠습니다."},
                    {"type": "tool_use", "id": "read-1", "name": "Read", "input": {}},
                ],
            }},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "read-1", "content": "도구 결과"},
            ]}},
            {"type": "assistant", "message": {
                "id": "final-one", "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "첫 질문에 대한 답변"}],
            }},
            {"type": "user", "message": {"content": "다음 질문"}},
            {"type": "assistant", "message": {
                "id": "final-two", "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "다음 질문에 대한 답변"}],
            }},
        ])
        parsed = parse_claude_session(path)
        self.assertEqual(
            [(event.role, event.text, event.message_phase) for event in parsed.events
             if event.event_type == "message"],
            [
                ("user", "첫 질문", None),
                ("assistant", "파일을 확인하겠습니다.", "commentary"),
                ("assistant", "첫 질문에 대한 답변", "final_answer"),
                ("user", "다음 질문", None),
                ("assistant", "다음 질문에 대한 답변", "final_answer"),
            ],
        )
        tools = [event for event in parsed.events if event.event_type == "tool_call"]
        self.assertEqual(len(tools), 1)
        self.assertIsNone(tools[0].message_phase)

    def test_claude_phase_shares_terminal_signal_only_with_same_native_message(self):
        path = self._write_jsonl([
            {"type": "assistant", "message": {
                "id": "completed", "stop_reason": None,
                "content": [{"type": "text", "text": "답변 본문"}],
            }},
            {"type": "assistant", "message": {
                "id": "completed", "stop_reason": "end_turn",
                "content": [{"type": "thinking", "thinking": "비공개 추론"}],
            }},
            {"type": "assistant", "message": {
                "id": "working", "stop_reason": None,
                "content": [{"type": "text", "text": "중간 설명"}],
            }},
            {"type": "assistant", "message": {
                "id": "working", "stop_reason": "tool_use",
                "content": [{"type": "tool_use", "id": "read-2", "name": "Read"}],
            }},
            {"type": "assistant", "message": {
                "id": "unmarked", "content": [{"type": "text", "text": "완료했습니다"}],
            }},
            {"type": "assistant", "isMeta": True, "message": {
                "id": "unmarked", "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "메타 안내"}],
            }},
            {"type": "user", "message": {"content": "다음 질문"}},
        ])
        parsed = parse_claude_session(path)
        self.assertEqual(
            [(event.text, event.message_phase) for event in parsed.events
             if event.event_type == "message"],
            [
                ("답변 본문", "final_answer"),
                ("중간 설명", "commentary"),
                ("완료했습니다", None),
                ("다음 질문", None),
            ],
        )

    def test_claude_phase_does_not_mark_unknown_truncated_or_error_responses_final(self):
        for reason in (
            None, "max_tokens", "pause_turn", "stop_sequence", "refusal",
            "model_context_window_exceeded", "future_reason", [], {}, True,
        ):
            with self.subTest(reason=reason):
                path = self._write_jsonl([{"type": "assistant", "message": {
                    "id": "incomplete", "stop_reason": reason,
                    "content": [{"type": "text", "text": "완료했습니다"}],
                }}])
                self.assertIsNone(parse_claude_session(path).events[0].message_phase)

        for error_field in ("isApiErrorMessage", "error"):
            with self.subTest(error_field=error_field):
                path = self._write_jsonl([{
                    "type": "assistant", error_field: True, "message": {
                        "id": "failed", "stop_reason": "end_turn",
                        "content": [{"type": "text", "text": "오류 응답"}],
                    },
                }])
                self.assertIsNone(parse_claude_session(path).events[0].message_phase)

        for other_content in (
            [{"type": "tool_use", "name": "Read"}],
            [{"type": "server_tool_use", "name": "web_search"}],
            [{"type": "thinking", "thinking": "추가 생성"}],
        ):
            with self.subTest(other_content=other_content):
                path = self._write_jsonl([
                    {"type": "assistant", "message": {
                        "id": "conflicting", "stop_reason": "end_turn",
                        "content": [{"type": "text", "text": "완료처럼 보이는 답변"}],
                    }},
                    {"type": "assistant", "message": {
                        "id": "conflicting", "stop_reason": "tool_use",
                        "content": other_content,
                    }},
                ])
                self.assertIsNone(parse_claude_session(path).events[0].message_phase)

        path = self._write_jsonl([{"type": "assistant", "message": {
            "id": "mixed", "stop_reason": "end_turn", "content": [
                {"type": "text", "text": "도구 실행 전 설명"},
                {"type": "tool_use", "name": "Read"},
            ],
        }}])
        self.assertIsNone(parse_claude_session(path).events[0].message_phase)

    def test_claude_phase_without_native_id_stays_local_to_its_source_record(self):
        path = self._write_jsonl([
            {"type": "assistant", "message": {
                "stop_reason": "end_turn", "content": "완료된 답변",
            }},
            {"type": "assistant", "message": {"content": "아직 응답 중"}},
            {"type": "assistant", "message": {
                "id": [], "stop_reason": "end_turn", "content": "다른 완료 답변",
            }},
            {"type": "assistant", "message": {
                "id": {}, "content": "종료 여부가 없는 답변",
            }},
            {"type": "assistant", "message": "구형 텍스트 응답"},
        ])
        parsed = parse_claude_session(path)
        self.assertEqual(
            [event.message_phase for event in parsed.events],
            ["final_answer", None, "final_answer", None, None],
        )

    def test_claude_subsession_phases_match_primary_session(self):
        records = [
            {"type": "user", "sessionId": "parent-session", "message": {"content": "질문"}},
            {"type": "assistant", "message": {
                "id": "tool", "stop_reason": "tool_use", "content": [
                    {"type": "text", "text": "확인 중"},
                    {"type": "tool_use", "name": "Read"},
                ],
            }},
            {"type": "assistant", "message": {
                "id": "answer", "stop_reason": "end_turn", "content": [
                    {"type": "text", "text": "확인 결과"},
                ],
            }},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            primary = root / "parent-session.jsonl"
            child = root / "parent-session" / "subagents" / "agent-synthetic.jsonl"
            child.parent.mkdir(parents=True)
            body = "\n".join(json.dumps(record) for record in records) + "\n"
            primary.write_text(body)
            child.write_text(body)
            main = parse_claude_session(primary)
            sub = parse_claude_session(child)
        self.assertEqual(sub.session_role, "subsession")
        self.assertEqual(sub.parent_external_id, main.external_id)
        self.assertEqual(
            [(event.event_type, event.role, event.text, event.message_phase)
             for event in main.events],
            [(event.event_type, event.role, event.text, event.message_phase)
             for event in sub.events],
        )
        self.assertEqual(main.events[-1].message_phase, "final_answer")

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
                    "payload": {
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {"type": "output_text", "text": "구현했습니다"}
                        ],
                    },
                },
            ]
        )
        parsed = parse_codex_session(path)
        self.assertEqual(parsed.external_id, "codex-1")
        self.assertEqual(parsed.cwd_raw, "/tmp/project")
        self.assertEqual(parsed.title, "구현해줘")
        self.assertEqual(len(parsed.events), 2)
        self.assertEqual(
            [event.text for event in parsed.events], ["구현해줘", "구현했습니다"]
        )

    def test_codex_parser_falls_back_to_response_messages_by_turn(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-08-11T05:32:15Z",
                    "payload": {
                        "id": "codex-response-only",
                        "cwd": "/tmp/project",
                        "source": "cli",
                        "thread_source": "user",
                    },
                },
                {
                    "type": "turn_context",
                    "timestamp": "2026-08-11T05:32:16Z",
                    "payload": {"turn_id": "turn-one"},
                },
                {
                    "type": "response_item",
                    "timestamp": "2026-08-11T05:32:17Z",
                    "payload": {
                        "id": "injected-context",
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    "<environment_context>\n"
                                    "주입된 실행 컨텍스트\n"
                                    "</environment_context>"
                                ),
                            }
                        ],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-one"
                        },
                    },
                },
                {
                    "type": "response_item",
                    "timestamp": "2026-08-11T05:32:18Z",
                    "payload": {
                        "id": "visible-user-message",
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "새 형식 질문 https://example.test/item",
                            }
                        ],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-one"
                        },
                    },
                },
                {
                    "type": "response_item",
                    "timestamp": "2026-08-11T05:32:19Z",
                    "payload": {
                        "id": "visible-assistant-message",
                        "type": "message",
                        "role": "assistant",
                        "phase": "final_answer",
                        "content": [
                            {"type": "output_text", "text": "새 형식 답변"}
                        ],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-one"
                        },
                    },
                },
            ]
        )

        parsed = parse_codex_session(path)

        self.assertEqual(parsed.session_role, "primary")
        self.assertEqual(parsed.title, "새 형식 질문 https://example.test/item")
        self.assertEqual(
            [(event.role, event.text) for event in parsed.events],
            [
                ("user", "새 형식 질문 https://example.test/item"),
                ("assistant", "새 형식 답변"),
            ],
        )
        self.assertEqual(
            [item.observed_url for item in parsed.url_evidence],
            ["https://example.test/item"],
        )

    @staticmethod
    def _codex_response_message(role, text, turn_id=None):
        payload = {
            "type": "message",
            "role": role,
            "content": [{
                "type": "input_text" if role == "user" else "output_text",
                "text": text,
            }],
        }
        if turn_id is not None:
            payload["internal_chat_message_metadata_passthrough"] = {
                "turn_id": turn_id
            }
        return {"type": "response_item", "payload": payload}

    @staticmethod
    def _codex_question_reply(items):
        return (
            "<send_user_message_question_reply>\n"
            + json.dumps(items, ensure_ascii=False)
            + "\n</send_user_message_question_reply>"
        )

    def test_codex_question_reply_retains_questions_answers_and_batch_order(self):
        wrapper = self._codex_question_reply([
            {"question": "어떤 범위를 반영할까요?\n두 번째 줄",
             "answer": '문서 "A"를 확인해요.\nhttps://answer.example.test/item',
             "questionItemId": json.dumps(["request_user_input_async", "private-call", 0])},
            {"question": "다음 단계는?", "answer": "- 첫 작업\n- 다음 작업"},
        ])
        path = self._write_jsonl([
            self._codex_response_message("user", "원래 질문", "turn-one"),
            self._codex_response_message("user", wrapper, "turn-one"),
            {"type": "response_item", "payload": {
                "type": "message", "role": "assistant", "phase": "final_answer",
                "content": [{"type": "output_text", "text": "확인했습니다"}],
            }},
        ])
        before = path.read_bytes()
        parsed = parse_codex_session(path)
        self.assertEqual(parsed.title, "원래 질문")
        self.assertEqual(parsed.events[1].text, (
            '> 어떤 범위를 반영할까요?\n> 두 번째 줄\n\n'
            '문서 "A"를 확인해요.\nhttps://answer.example.test/item\n\n'
            '> 다음 단계는?\n\n- 첫 작업\n- 다음 작업'
        ))
        self.assertEqual(parsed.events[-1].message_phase, "final_answer")
        self.assertNotIn("questionItemId", parsed.events[1].text)
        self.assertNotIn("private-call", parsed.events[1].text)
        self.assertEqual([item.observed_url for item in parsed.url_evidence],
                         ["https://answer.example.test/item"])
        self.assertEqual(path.read_bytes(), before)

    def test_codex_question_reply_deduplication_is_normalized_and_turn_scoped(self):
        wrapper = self._codex_question_reply([{
            "answer": "진행", "question": "진행할까요?", "questionItemId": "internal",
        }])
        pretty = "<send_user_message_question_reply>\n" + json.dumps(
            [{"questionItemId": "internal", "question": "진행할까요?", "answer": "진행"}],
            ensure_ascii=False, indent=2,
        ) + "\n</send_user_message_question_reply>"
        parsed = parse_codex_session(self._write_jsonl([
            {"type": "turn_context", "payload": {"turn_id": "one"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": wrapper}},
            self._codex_response_message("user", pretty, "one"),
            self._codex_response_message("user", self._codex_question_reply([
                {"question": "다른 질문인가요?", "answer": "진행"},
            ]), "one"),
            {"type": "turn_context", "payload": {"turn_id": "two"}},
            self._codex_response_message("user", wrapper, "two"),
        ]))
        self.assertEqual([event.text for event in parsed.events], [
            "> 진행할까요?\n\n진행", "> 다른 질문인가요?\n\n진행", "> 진행할까요?\n\n진행",
        ])
        self.assertEqual([event.source_line for event in parsed.events], [2, 4, 6])

    def test_codex_question_reply_preserves_malformed_unknown_and_quoted_content(self):
        for body in (
            "not JSON", "[]", "{}", "[null]", '[{"answer": []}]',
            '[{"answer": ""}]', '[{"answer": "예", "question": null}]',
            '[{"answer": "예", "newHumanField": "고유 내용"}]',
            '[{"answer": "첫 값", "answer": "두 번째 값"}]',
            '[{"answer": "첫 답변"}, {"answer": null}]',
        ):
            text = "<send_user_message_question_reply>\n" + body + "\n</send_user_message_question_reply>"
            with self.subTest(body=body):
                parsed = parse_codex_session(self._write_jsonl([
                    self._codex_response_message("user", text),
                ]))
                self.assertEqual(parsed.events[0].text, text)
        wrapper = self._codex_question_reply([{"question": "질문", "answer": "답변"}])
        fence = chr(96) * 3
        for role, text in (
            ("assistant", wrapper),
            ("user", "이 표현을 확인해 주세요.\n" + wrapper),
            ("user", wrapper + "\n이것은 예시입니다."),
            ("user", fence + "xml\n" + wrapper + "\n" + fence),
            ("user", "> " + wrapper.replace("\n", "\n> ")),
            ("user", "<dependency>실제 XML 코드</dependency>"),
        ):
            with self.subTest(role=role, text=text):
                parsed = parse_codex_session(self._write_jsonl([
                    self._codex_response_message(role, text),
                ]))
                self.assertEqual(parsed.events[0].text, text)

    def test_codex_question_reply_answer_is_not_reclassified_as_generated_context(self):
        answer = "<environment_context>이 문자열을 그대로 사용해 주세요.</environment_context>"
        parsed = parse_codex_session(self._write_jsonl([
            self._codex_response_message("user", self._codex_question_reply([{"answer": answer}])),
        ]))
        self.assertEqual([event.text for event in parsed.events], [answer])

    def test_codex_mixed_user_blocks_filter_context_and_keep_actual_input(self):
        contexts = [
            "<recommended_plugins>\n"
            "Here is a list of plugins that are available but not installed.\n"
            "- Plugin https://hidden.example.test/plugin\n</recommended_plugins>",
            "# AGENTS.md instructions\n<INSTRUCTIONS>\n"
            "지침 https://hidden.example.test/agents\n</INSTRUCTIONS>",
            "<environment_context>https://hidden.example.test/environment</environment_context>",
        ]
        prompt = "실제 첫 질문 https://visible.example.test/prompt"
        for values, expected in (
            ([contexts[0], prompt, contexts[1], "추가 조건", contexts[2]], prompt + "\n\n추가 조건"),
            (contexts + [prompt], prompt),
        ):
            with self.subTest(values=values):
                parsed = parse_codex_session(self._write_jsonl([{
                    "type": "response_item", "payload": {
                        "type": "message", "role": "user",
                        "content": [{"type": "input_text", "text": value} for value in values],
                    },
                }]))
                self.assertEqual([event.text for event in parsed.events], [expected])
                self.assertEqual(parsed.title, " ".join(expected.split()))
                self.assertEqual([item.observed_url for item in parsed.url_evidence],
                                 ["https://visible.example.test/prompt"])
                self.assertEqual([item.reference for item in parsed.reference_candidates],
                                 ["https://visible.example.test/prompt"])
        parsed = parse_codex_session(self._write_jsonl([
            {"type": "response_item", "payload": {
                "type": "message", "role": "user",
                "content": [{"type": "input_text", "text": value} for value in contexts],
            }},
            self._codex_response_message("user", prompt),
        ]))
        self.assertEqual(len(parsed.events), 1)
        self.assertEqual(parsed.title, prompt)

    def test_codex_context_filter_is_specific_and_applies_to_both_native_formats(self):
        contexts = [
            "<recommended_plugins>\n"
            "Here is a list of plugins that are available but not installed.\n</recommended_plugins>",
            '<codex_internal_context source="daemon_recovery">\n'
            "The server restarted.\n</codex_internal_context>",
            "<turn_aborted>\nThe user interrupted the previous turn on purpose.\n</turn_aborted>",
        ]
        for context in contexts:
            for source in ("legacy", "response"):
                with self.subTest(context=context, source=source):
                    record = (
                        {"type": "event_msg", "payload": {"type": "user_message", "message": context}}
                        if source == "legacy"
                        else self._codex_response_message("user", context)
                    )
                    parsed = parse_codex_session(self._write_jsonl([
                        record, self._codex_response_message("user", "실제 질문"),
                    ]))
                    self.assertEqual([event.text for event in parsed.events], ["실제 질문"])
        fence = chr(96) * 3
        for literal in (
            "<recommended_plugins>사용자가 작성한 XML 예시</recommended_plugins>",
            "<turn_aborted>직접 입력한 설명</turn_aborted>",
            fence + "xml\n" + contexts[0] + "\n" + fence,
            "앞 문장\n" + contexts[1],
            '<image name="sample">이미지에 대한 질문</image>',
        ):
            parsed = parse_codex_session(self._write_jsonl([
                self._codex_response_message("user", literal),
            ]))
            self.assertEqual(parsed.events[0].text, literal)

    def test_codex_parser_preserves_all_user_messages_within_a_turn(self):
        prompt = "첫 질문 https://visible.example.test/first"
        reply = (
            '<send_user_message_question_reply>\n'
            '[{"answer":"진행 https://visible.example.test/reply"}]\n'
            '</send_user_message_question_reply>'
        )
        messages = [
            ("user", prompt),
            ("user", "추가 조건"),
            ("assistant", "확인이 필요합니다"),
            ("user", reply),
            ("assistant", "진행하겠습니다"),
            ("user", "추가 조건"),
        ]
        for turn_source in ("metadata", "context", "unscoped"):
            with self.subTest(turn_source=turn_source):
                records = [{
                    "type": "session_meta",
                    "payload": {"id": "codex-multiple-inputs"},
                }]
                if turn_source != "unscoped":
                    records.append({
                        "type": "turn_context",
                        "payload": {"turn_id": "turn-one"},
                    })
                records.extend(
                    self._codex_response_message(
                        role, text,
                        "turn-one" if turn_source == "metadata" else None,
                    )
                    for role, text in messages
                )
                parsed = parse_codex_session(self._write_jsonl(records))
                self.assertEqual(parsed.title, prompt)
                self.assertEqual(
                    [(event.role, event.text) for event in parsed.events],
                    [(role, "진행 https://visible.example.test/reply" if text == reply else text)
                     for role, text in messages]
                )
                self.assertEqual(
                    [item.observed_url for item in parsed.url_evidence],
                    [
                        "https://visible.example.test/first",
                        "https://visible.example.test/reply",
                    ],
                )
                self.assertEqual(
                    [item.reference for item in parsed.reference_candidates],
                    [
                        "https://visible.example.test/first",
                        "https://visible.example.test/reply",
                    ],
                )
                lines = [event.source_line for event in parsed.events]
                self.assertEqual(lines, sorted(set(lines)))

    def test_codex_parser_excludes_generated_context_between_user_messages(self):
        hidden_url = "https://injected.example.test/item"
        contexts = [
            "# AGENTS.md instructions for /synthetic\n<INSTRUCTIONS>\n"
            + hidden_url + "\n</INSTRUCTIONS>",
            "# AGENTS.md instructions\n\n<INSTRUCTIONS>\n"
            + hidden_url + "\n</INSTRUCTIONS>",
            "# AGENTS.md instructions\n<INSTRUCTIONS>\n"
            + hidden_url + "\n</INSTRUCTIONS>\n"
            "<environment_context>synthetic</environment_context>",
            "<environment_context>" + hidden_url + "</environment_context>",
            "<skill>\n<name>synthetic-review</name>\n"
            "<path>/synthetic/SKILL.md</path>\n" + hidden_url + "\n</skill>",
        ]
        for context in contexts:
            with self.subTest(context=context.splitlines()[0]):
                message = self._codex_response_message
                records = [
                    {"type": "turn_context", "payload": {"turn_id": "turn-one"}},
                    message("user", context),
                    message("user", "첫 질문"),
                    message("user", context),
                    message("assistant", "확인할까요?"),
                    message("user", "진행해줘"),
                    message("user", context),
                ]
                parsed = parse_codex_session(self._write_jsonl(records))
                self.assertEqual(parsed.title, "첫 질문")
                self.assertEqual(
                    [(event.role, event.text) for event in parsed.events],
                    [("user", "첫 질문"), ("assistant", "확인할까요?"),
                     ("user", "진행해줘")],
                )
                self.assertEqual(parsed.url_evidence, [])
                self.assertEqual(parsed.reference_candidates, [])

    def test_codex_parser_preserves_generated_context_lookalikes(self):
        messages = [
            "# AGENTS.md instructions에 관해 설명해줘",
            "# AGENTS.md instructions\n<INSTRUCTIONS>\n미완성 내용",
            "<environment_context>라는 태그를 설명해줘",
            "<skill>\n<name>synthetic</name>\n설명해줘",
        ]
        records = [
            {"type": "turn_context", "payload": {"turn_id": "turn-one"}},
            *(self._codex_response_message("user", text) for text in messages),
        ]
        parsed = parse_codex_session(self._write_jsonl(records))
        self.assertEqual([event.text for event in parsed.events], messages)

    def test_codex_parser_preserves_repeated_text_across_distinct_turns(self):
        message = self._codex_response_message
        records = [
            {"type": "turn_context", "payload": {"turn_id": "response-turn"}},
            message("user", "같은 질문"),
            message("assistant", "같은 답변"),
            {"type": "turn_context", "payload": {"turn_id": "legacy-turn"}},
            {"type": "event_msg", "payload": {
                "type": "user_message", "message": "같은 질문",
            }},
            message("user", "같은 질문"),
            {"type": "event_msg", "payload": {
                "type": "agent_message", "message": "같은 답변",
            }},
            message("assistant", "같은 답변"),
            {"type": "turn_context", "payload": {"turn_id": "another-turn"}},
            message("user", "같은 질문"),
            message("assistant", "같은 답변"),
        ]
        parsed = parse_codex_session(self._write_jsonl(records))
        self.assertEqual(
            [(event.role, event.text) for event in parsed.events],
            [("user", "같은 질문"), ("assistant", "같은 답변")] * 3,
        )

    def test_codex_parser_preserves_reply_in_turn_with_legacy_user_message(self):
        message = self._codex_response_message
        records = [
            {"type": "turn_context", "payload": {"turn_id": "turn-one"}},
            {"type": "event_msg", "payload": {
                "type": "user_message", "message": "첫 질문",
            }},
            message("user", "첫 질문"),
            message("assistant", "확인할까요?"),
            message("user", "진행해줘"),
            message("assistant", "진행했습니다"),
        ]
        parsed = parse_codex_session(self._write_jsonl(records))
        self.assertEqual(
            [(event.role, event.text) for event in parsed.events],
            [("user", "첫 질문"), ("assistant", "확인할까요?"),
             ("user", "진행해줘"), ("assistant", "진행했습니다")],
        )

    def test_codex_parser_deduplicates_legacy_messages_without_turn_metadata(self):
        for legacy_turn, response_turn in (
            (None, "turn-one"), ("turn-one", None), (None, None),
        ):
            with self.subTest(legacy_turn=legacy_turn, response_turn=response_turn):
                records = [
                    self._codex_response_message("user", "첫 질문", response_turn),
                    self._codex_response_message("assistant", "답변", response_turn),
                ]
                if legacy_turn is not None:
                    records.append({
                        "type": "turn_context", "payload": {"turn_id": legacy_turn},
                    })
                records.extend([
                    {"type": "event_msg", "payload": {
                        "type": "user_message", "message": "첫 질문",
                    }},
                    {"type": "event_msg", "payload": {
                        "type": "agent_message", "message": "답변",
                    }},
                ])
                parsed = parse_codex_session(self._write_jsonl(records))
                self.assertEqual(
                    [(event.role, event.text) for event in parsed.events],
                    [("user", "첫 질문"), ("assistant", "답변")],
                )

    def test_codex_parser_retains_only_explicit_assistant_message_phases(self):
        messages = [
            ("user", "final_answer", "작업 요청", None),
            ("assistant", "commentary", "완료라는 표현을 검토합니다", "commentary"),
            ("assistant", "final_answer", "사용자 확인이 필요합니다", "final_answer"),
            ("assistant", None, "완료했습니다", None),
            ("assistant", "future_phase", "새 형식", None),
            ("assistant", ["final_answer"], "잘못된 메타데이터", None),
        ]
        records = []
        for role, phase, text, expected in messages:
            record = self._codex_response_message(role, text, "turn-one")
            record["payload"]["phase"] = phase
            records.append(record)
        parsed = parse_codex_session(self._write_jsonl(records))
        self.assertEqual(
            [(event.role, event.text, event.message_phase) for event in parsed.events],
            [(role, text, expected) for role, phase, text, expected in messages],
        )
        self.assertEqual(len({event.event_id for event in parsed.events}), len(messages))

    def test_codex_parser_backfills_phase_from_unique_legacy_counterpart(self):
        for turn_id in (None, "turn-one"):
            with self.subTest(turn_id=turn_id):
                records = []
                if turn_id is not None:
                    records.append({"type": "turn_context", "payload": {"turn_id": turn_id}})
                for phase, text in (("commentary", "진행 설명"), ("final_answer", "응답 본문")):
                    record = self._codex_response_message("assistant", text, turn_id)
                    record["payload"]["phase"] = phase
                    records.extend([record, {"type": "event_msg", "payload": {
                        "type": "agent_message", "message": text,
                    }}])
                parsed = parse_codex_session(self._write_jsonl(records))
                self.assertEqual(
                    [(event.text, event.message_phase) for event in parsed.events],
                    [("진행 설명", "commentary"), ("응답 본문", "final_answer")],
                )
                self.assertTrue(all(event.source_line % 2 == (1 if turn_id else 0)
                                    for event in parsed.events))

    def test_codex_parser_does_not_guess_phase_for_ambiguous_legacy_messages(self):
        for legacy_count, response_phases, expected in (
            (2, ["final_answer"], [None, None]),
            (1, ["commentary", "final_answer"], [None]),
        ):
            with self.subTest(legacy_count=legacy_count, response_phases=response_phases):
                records = [{"type": "turn_context", "payload": {"turn_id": "turn-one"}}]
                records.extend({"type": "event_msg", "payload": {
                    "type": "agent_message", "message": "같은 응답",
                }} for _ in range(legacy_count))
                for phase in response_phases:
                    response = self._codex_response_message("assistant", "같은 응답", "turn-one")
                    response["payload"]["phase"] = phase
                    records.append(response)
                parsed = parse_codex_session(self._write_jsonl(records))
                self.assertEqual([event.message_phase for event in parsed.events], expected)

    def test_codex_parser_keeps_phase_scoped_to_turn_and_preserves_native_phase(self):
        records = []
        for turn_id, native_phase, response_phase in (
            ("turn-one", None, "final_answer"),
            ("turn-two", None, "commentary"),
            ("turn-three", "commentary", "final_answer"),
        ):
            records.extend([
                {"type": "turn_context", "payload": {"turn_id": turn_id}},
                {"type": "event_msg", "payload": {
                    "type": "agent_message", "message": "같은 응답", "phase": native_phase,
                }},
            ])
            response = self._codex_response_message("assistant", "같은 응답", turn_id)
            response["payload"]["phase"] = response_phase
            records.append(response)
        parsed = parse_codex_session(self._write_jsonl(records))
        self.assertEqual([event.message_phase for event in parsed.events],
                         ["final_answer", "commentary", "commentary"])

    def test_codex_parser_keeps_prompt_before_expanded_skill_context(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "payload": {"id": "codex-skill-prompt", "source": "cli"},
                },
                {"type": "turn_context", "payload": {"turn_id": "turn-skill"}},
                {
                    "type": "response_item",
                    "payload": {
                        "id": "visible-user-message",
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    "$synthetic-review 결과를 대조해줘 "
                                    "https://visible.example.test/item"
                                ),
                            }
                        ],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-skill"
                        },
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "id": "expanded-skill-context",
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    "<skill>\n<name>synthetic-review</name>\n"
                                    "<path>/synthetic/SKILL.md</path>\n"
                                    "Do not surface https://injected.example.test/item\n"
                                    "</skill>"
                                ),
                            }
                        ],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-skill"
                        },
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "id": "visible-assistant-message",
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {"type": "output_text", "text": "검토했습니다"}
                        ],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-skill"
                        },
                    },
                },
            ]
        )

        parsed = parse_codex_session(path)

        self.assertEqual(
            parsed.title,
            "$synthetic-review 결과를 대조해줘 https://visible.example.test/item",
        )
        self.assertEqual(
            [(event.role, event.text) for event in parsed.events],
            [
                (
                    "user",
                    "$synthetic-review 결과를 대조해줘 "
                    "https://visible.example.test/item",
                ),
                ("assistant", "검토했습니다"),
            ],
        )
        self.assertEqual(
            [item.observed_url for item in parsed.url_evidence],
            ["https://visible.example.test/item"],
        )

    def test_codex_parser_fills_only_missing_event_message_role(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "payload": {
                        "id": "codex-partial-events",
                        "source": {"subagent": {"other": "worker"}},
                        "parent_thread_id": "codex-parent",
                    },
                },
                {
                    "type": "turn_context",
                    "payload": {"turn_id": "turn-one"},
                },
                {
                    "type": "response_item",
                    "payload": {
                        "id": "response-user",
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "작업 지시"}],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-one"
                        },
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "id": "response-assistant",
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {"type": "output_text", "text": "중복될 응답"}
                        ],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-one"
                        },
                    },
                },
                {
                    "type": "event_msg",
                    "payload": {"type": "agent_message", "message": "기존 응답"},
                },
            ]
        )

        parsed = parse_codex_session(path)

        self.assertEqual(parsed.session_role, "subsession")
        self.assertEqual(parsed.title, "작업 지시")
        self.assertEqual(
            [(event.role, event.text) for event in parsed.events],
            [("user", "작업 지시"), ("assistant", "기존 응답")],
        )

    def test_codex_parser_preserves_response_only_turn_before_legacy_turn(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "payload": {"id": "codex-mixed-format", "source": "cli"},
                },
                {"type": "turn_context", "payload": {"turn_id": "turn-new"}},
                {
                    "type": "response_item",
                    "payload": {
                        "id": "new-user",
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "먼저 한 질문"}],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-new"
                        },
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "id": "new-assistant",
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "먼저 한 답변"}],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-new"
                        },
                    },
                },
                {"type": "turn_context", "payload": {"turn_id": "turn-legacy"}},
                {
                    "type": "response_item",
                    "payload": {
                        "id": "legacy-user-response",
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "나중 질문"}],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-legacy"
                        },
                    },
                },
                {
                    "type": "event_msg",
                    "payload": {"type": "user_message", "message": "나중 질문"},
                },
                {
                    "type": "response_item",
                    "payload": {
                        "id": "legacy-assistant-response",
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {"type": "output_text", "text": "나중 답변"}
                        ],
                        "internal_chat_message_metadata_passthrough": {
                            "turn_id": "turn-legacy"
                        },
                    },
                },
                {
                    "type": "event_msg",
                    "payload": {"type": "agent_message", "message": "나중 답변"},
                },
            ]
        )

        parsed = parse_codex_session(path)

        self.assertEqual(parsed.title, "먼저 한 질문")
        self.assertEqual(
            [(event.role, event.text) for event in parsed.events],
            [
                ("user", "먼저 한 질문"),
                ("assistant", "먼저 한 답변"),
                ("user", "나중 질문"),
                ("assistant", "나중 답변"),
            ],
        )

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
                        "source": {"subagent": {"other": "guardian"}},
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
        self.assertEqual(parsed.session_class, "work")
        self.assertEqual(parsed.index_policy, "full")

    def test_codex_guardian_is_metadata_only_maintenance_subsession(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-08-20T01:00:00Z",
                    "payload": {
                        "id": "codex-guardian",
                        "cwd": "/tmp/project",
                        "source": {"subagent": {"other": "guardian"}},
                        "parent_thread_id": "codex-parent",
                    },
                },
                {
                    "type": "turn_context",
                    "timestamp": "2026-08-20T01:00:01Z",
                    "payload": {"turn_id": "guardian-turn", "model": "gpt-5.6-sol"},
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-08-20T01:00:02Z",
                    "payload": {
                        "type": "user_message",
                        "message": "The following is the Codex agent history whose request action you are assessing.",
                    },
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-08-20T01:00:03Z",
                    "payload": {
                        "type": "agent_message",
                        "message": '{"outcome":"allow"}',
                    },
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-08-20T01:00:04Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "last_token_usage": {
                                "input_tokens": 10,
                                "cached_input_tokens": 2,
                                "output_tokens": 5,
                                "reasoning_output_tokens": 1,
                                "total_tokens": 15,
                            }
                        },
                    },
                },
            ]
        )

        parsed = parse_codex_session(path)

        self.assertEqual(parsed.session_role, "subsession")
        self.assertEqual(parsed.parent_external_id, "codex-parent")
        self.assertEqual(parsed.session_class, "maintenance")
        self.assertEqual(parsed.index_policy, "metadata_only")
        self.assertIsNone(parsed.maintenance_run_id)
        self.assertEqual(parsed.title, "Codex guardian")
        self.assertEqual(len(parsed.events), 2)
        self.assertEqual(len(parsed.usage_records), 1)

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

    def test_claude_reference_candidates_preserve_role_and_read_truth(self):
        path = self._write_jsonl(
            [
                {
                    "type": "user",
                    "uuid": "user-event",
                    "sessionId": "claude-references",
                    "message": {
                        "content": "See docs/guide.md and https://example.test/path?q=1"
                    },
                },
                {
                    "type": "assistant",
                    "uuid": "assistant-event",
                    "sessionId": "claude-references",
                    "message": {
                        "content": [
                            {"type": "text", "text": "Also README.md"},
                            {
                                "type": "tool_use",
                                "id": "call-success",
                                "name": "atlassian.searchJiraIssuesUsingJql",
                                "input": {"jql": 'key = "SYN-62"'},
                            },
                            {
                                "type": "tool_use",
                                "id": "call-failed",
                                "name": "atlassian.searchJiraIssuesUsingJql",
                                "input": {"jql": "key = SYN-63"},
                            },
                            {
                                "type": "tool_use",
                                "id": "call-missing",
                                "name": "atlassian.searchJiraIssuesUsingJql",
                                "input": {"jql": "key = SYN-64"},
                            },
                            {
                                "type": "tool_use",
                                "id": "call-malformed",
                                "name": "atlassian.searchJiraIssuesUsingJql",
                                "input": {"jql": "key = SYN-65"},
                            },
                        ]
                    },
                },
                {
                    "type": "user",
                    "uuid": "result-event",
                    "sessionId": "claude-references",
                    "message": {
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": "call-success",
                                "content": {
                                    "issues": [
                                        {
                                            "url": "https://jira.example.test/browse/SYN-62"
                                        }
                                    ]
                                },
                            },
                            {
                                "type": "tool_result",
                                "tool_use_id": "call-failed",
                                "is_error": True,
                                "content": {"error": "denied"},
                            },
                            {
                                "type": "tool_result",
                                "tool_use_id": "call-malformed",
                                "content": "opaque unstructured output",
                            },
                        ]
                    },
                },
            ]
        )

        parsed = parse_claude_session(path)
        visible = {
            (item.reference_kind, item.reference, item.evidence_kind)
            for item in parsed.reference_candidates
            if item.evidence_kind.endswith("mention")
        }
        reads = {
            (item.reference, item.read_outcome, item.tool_call_id)
            for item in parsed.reference_candidates
            if item.evidence_kind == "resource_read"
        }

        self.assertIn(("markdown", "docs/guide.md", "user_mention"), visible)
        self.assertIn(("url", "https://example.test/path?q=1", "user_mention"), visible)
        self.assertIn(("markdown", "README.md", "assistant_mention"), visible)
        self.assertIn(("SYN-62", "success", "call-success"), reads)
        self.assertIn(("SYN-63", "failure", "call-failed"), reads)
        self.assertNotIn("call-missing", {item[2] for item in reads})
        self.assertNotIn("call-malformed", {item[2] for item in reads})

    def test_codex_reference_candidates_match_call_result_identity(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "payload": {"id": "codex-references", "cwd": "/workspace"},
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "call_id": "call-success",
                        "name": "mcp_gateway.gateway_dispatch",
                        "arguments": json.dumps(
                            {
                                "capability": "jira__searchIssuesByJql",
                                "arguments": {"jql": 'key = "SYN-62"'},
                            }
                        ),
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call_output",
                        "id": "result-success",
                        "call_id": "call-success",
                        "output": json.dumps(
                            {
                                "issues": [
                                    {
                                        "url": "https://jira.example.test/browse/SYN-62"
                                    }
                                ]
                            }
                        ),
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "call_id": "call-failed",
                        "name": "mcp_gateway.gateway_dispatch",
                        "arguments": json.dumps(
                            {
                                "capability": "jira__searchIssuesByJql",
                                "arguments": {"jql": "key = SYN-63"},
                            }
                        ),
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call_output",
                        "id": "result-failed",
                        "call_id": "call-failed",
                        "output": {"status": "error", "error": "denied"},
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "call_id": "call-malformed",
                        "name": "mcp_gateway.gateway_dispatch",
                        "arguments": json.dumps(
                            {
                                "capability": "jira__searchIssuesByJql",
                                "arguments": {"jql": "key = SYN-65"},
                            }
                        ),
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call_output",
                        "call_id": "call-malformed",
                        "output": "opaque unstructured output",
                    },
                },
            ]
        )

        parsed = parse_codex_session(path)
        reads = {
            (item.reference, item.read_outcome, item.tool_call_id)
            for item in parsed.reference_candidates
            if item.evidence_kind == "resource_read"
        }

        self.assertIn(("SYN-62", "success", "call-success"), reads)
        self.assertIn(("SYN-63", "failure", "call-failed"), reads)
        self.assertNotIn("call-malformed", {item[2] for item in reads})
        self.assertEqual(
            {
                item.source_event_id
                for item in parsed.reference_candidates
                if item.tool_call_id == "call-success"
            },
            {"result-success"},
        )


if __name__ == "__main__":
    unittest.main()
