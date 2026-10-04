import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from localbrain.db import _migrate_skill_observation_contract
from localbrain.ingest.claude import parse_claude_session
from localbrain.ingest.codex import parse_codex_session
from localbrain.ingest.skill_usage import SkillReferenceMatcher
from localbrain.skill_observations import skill_insights_data, store_skill_observations


SCHEMA = Path(__file__).parents[1] / "src/localbrain/schema.sql"


def body(name):
    return "---\nname: {}\ndescription: Synthetic instructions\n---\n# Instructions\n".format(name)


def call(native_id, command, tool="exec_command"):
    return {"type": "response_item", "timestamp": "2026-10-02T00:00:00Z", "payload": {
        "type": "custom_tool_call" if tool == "exec" else "function_call",
        "call_id": native_id, "name": tool,
        "input" if tool == "exec" else "arguments": command if tool == "exec" else json.dumps({"cmd": command}),
    }}


def output(native_id, value, custom=False):
    return {"type": "response_item", "payload": {
        "type": "custom_tool_call_output" if custom else "function_call_output",
        "call_id": native_id, "output": value,
    }}


def shell_output(name, code=0):
    return "Process exited with code {}\nOutput:\n{}".format(code, body(name))


def turn(native_id):
    return {"type": "turn_context", "payload": {"turn_id": native_id}}


def context(native_id, name, turn_id=None):
    payload = {"type": "message", "role": "user", "id": native_id,
               "content": [{"type": "input_text", "text":
                   "<skill>\n<name>{}</name>\n<path>/synthetic/{}/SKILL.md</path>\n</skill>".format(name, name)}]}
    if turn_id:
        payload["internal_chat_message_metadata_passthrough"] = {"turn_id": turn_id}
    return {"type": "response_item", "timestamp": "2026-10-02T00:00:00Z", "payload": payload}


class AutomaticSkillLoadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="localbrain-skill-test-")
        self.root = Path(self.temporary.name)
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA.read_text(encoding="utf-8"))

    def tearDown(self):
        self.connection.close()
        self.temporary.cleanup()

    def parse(self, records, provider="codex", filename="session.jsonl"):
        path = self.root / filename
        if provider == "codex":
            records = [{"type": "session_meta", "payload": {"id": "synthetic-session"}}] + records
        path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
        return (parse_codex_session if provider == "codex" else parse_claude_session)(path)

    def store(self, parsed, provider="codex", source="codex"):
        return store_skill_observations(self.connection, source_key=source, provider_kind=provider, parsed=parsed)

    def test_context_counts_once_while_later_reads_remain_evidence(self):
        records = [turn("request-1"), context("load-1", "review-skill"),
                   call("read-1", "sed -n '1,30p' /synthetic/review-skill/SKILL.md"),
                   output("read-1", shell_output("review-skill")),
                   call("read-2", "cat /synthetic/review-skill/SKILL.md"),
                   output("read-2", shell_output("review-skill"))]
        parsed = self.parse(records)
        self.assertEqual(self.store(parsed), 3)
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
        self.assertEqual(self.store(parsed), 0)
        records.extend([turn("request-2"), call("read-3", "head -40 /synthetic/review-skill/SKILL.md"),
                        output("read-3", shell_output("review-skill"))])
        self.assertEqual(self.store(self.parse(records)), 1)
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
        self.assertEqual(self.store(self.parse(records, filename="moved.jsonl")), 0)
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)

    def test_backfill_enriches_old_identity_without_replacing_or_reviving_evidence(self):
        parsed = self.parse([turn("request-1"), context("load-1", "review-skill")])
        old = parsed.skill_observations[0]
        from dataclasses import replace
        parsed.skill_observations = [replace(old, request_key=None)]
        self.store(parsed)
        before = dict(self.connection.execute("SELECT * FROM skill_observations").fetchone())
        parsed.skill_observations = [old]
        self.assertEqual(self.store(parsed), 0)
        after = dict(self.connection.execute("SELECT * FROM skill_observations").fetchone())
        self.assertEqual({k: v for k, v in after.items() if k != "request_key"},
                         {k: v for k, v in before.items() if k != "request_key"})
        self.assertTrue(after["request_key"])
        self.connection.execute("UPDATE skill_observations SET state='corrected'")
        self.store(parsed)
        self.assertIsNone(skill_insights_data(self.connection)["top"])

    def test_nested_exec_matches_completed_reads_and_multiple_skills(self):
        script = 'const r = await Promise.allSettled([tools.exec_command({cmd:"cat /synthetic/first/SKILL.md"}), tools.exec_command({cmd:\'cat /synthetic/second/SKILL.md\'})]); r.forEach(text);'
        result = [{"type": "input_text", "text": "Script completed\nOutput:\n"},
                  {"type": "input_text", "text": json.dumps({"i": 1, "value": {"exit_code": 0, "output": body("second")}})},
                  {"type": "input_text", "text": json.dumps({"i": 0, "value": {"exit_code": 0, "output": body("first")}})}]
        parsed = self.parse([turn("request-1"), call("multi-read", script, tool="exec"),
                             output("multi-read", result, custom=True)])
        self.assertEqual(self.store(parsed), 2)
        self.assertEqual([(row["name"], row["use_count"]) for row in skill_insights_data(self.connection)["ranking"]], [("first", 1), ("second", 1)])
        self.assertEqual(self.store(parsed), 0)

    def test_nested_failure_pending_or_wrong_returned_name_are_not_loads(self):
        script = 'text(await tools.exec_command({cmd:"cat /synthetic/review-skill/SKILL.md"}));'
        variants = [
            [{"type": "input_text", "text": "Script completed"}, {"type": "input_text", "text": json.dumps({"exit_code": 1, "output": body("review-skill")})}],
            [{"type": "input_text", "text": "Script running with cell ID pending"}],
            [{"type": "input_text", "text": json.dumps({"exit_code": None, "session_id": 9, "output": body("review-skill")})}],
            [{"type": "input_text", "text": json.dumps({"exit_code": 0, "output": body("another-skill")})}],
        ]
        for value in variants:
            with self.subTest(value=value):
                parsed = self.parse([call("read", script, tool="exec"), output("read", value, custom=True)])
                self.assertEqual(parsed.skill_observations, [])

    def test_search_edits_dynamic_commands_and_quoted_examples_are_excluded(self):
        commands = ["rg name /synthetic/review-skill/SKILL.md",
                    "sed -i 's/a/b/' /synthetic/review-skill/SKILL.md",
                    "cat $ROOT/review-skill/SKILL.md",
                    "cat <<'EXAMPLE'\ncat /synthetic/review-skill/SKILL.md\nEXAMPLE",
                    "printf /synthetic/review-skill/SKILL.md"]
        for command in commands:
            parsed = self.parse([call("read", command), output("read", shell_output("review-skill"))])
            self.assertEqual(parsed.skill_observations, [], command)
        scripts = ['const example = "tools.exec_command({cmd:\\"cat /synthetic/review-skill/SKILL.md\\"})";',
                   'tools.exec_command({cmd:`cat ${root}/review-skill/SKILL.md`});',
                   'tools.exec_command({cmd:"cat /synthetic/review-skill/SKILL.md" + extra});']
        for script in scripts:
            parsed = self.parse([call("read", script, tool="exec"),
                                 output("read", [{"type": "input_text", "text": "Script completed"},
                                                 {"type": "input_text", "text": body("review-skill")}], custom=True)])
            self.assertEqual(parsed.skill_observations, [], script)

    def test_bare_completed_exec_and_numbered_read_output_are_supported(self):
        numbered = "\n".join("{}\t{}".format(i, line) for i, line in enumerate(body("review-skill").splitlines(), 1))
        parsed = self.parse([call("read", 'text((await tools.exec_command({cmd:"nl -ba /synthetic/review-skill/SKILL.md"})).output);', tool="exec"),
                             output("read", [{"type": "input_text", "text": "Script completed"},
                                             {"type": "input_text", "text": numbered}], custom=True)])
        self.assertEqual(len(parsed.skill_observations), 1)

    def test_missing_native_call_identity_and_uncompleted_calls_do_not_count(self):
        pending = call("pending", "cat /synthetic/review-skill/SKILL.md")
        no_id = call(None, "cat /synthetic/review-skill/SKILL.md")
        self.assertEqual(self.parse([pending, no_id, output(None, shell_output("review-skill"))]).skill_observations, [])

    def test_claude_read_and_skill_call_share_request_and_tool_results_do_not_start_one(self):
        records = [
            {"type": "user", "uuid": "user-1", "message": {"content": "Use the review instructions"}},
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "load", "name": "Skill", "input": {"skill": "review-skill"}},
                {"type": "tool_use", "id": "read", "name": "Read", "input": {"file_path": "/synthetic/review-skill/SKILL.md"}},
            ]}},
            {"type": "user", "uuid": "result-1", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "read", "content": body("review-skill")},
            ]}},
        ]
        parsed = self.parse(records, provider="claude")
        self.assertEqual(self.store(parsed, provider="claude", source="claude"), 2)
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
        self.assertEqual(len({item.request_key for item in parsed.skill_observations}), 1)
        records[2]["message"]["content"][0]["is_error"] = True
        self.assertEqual(len(self.parse(records, provider="claude").skill_observations), 1)

    def test_request_provenance_survives_session_counting_and_source_boundaries(self):
        user = lambda text: {"type": "event_msg", "payload": {"type": "user_message", "message": text}}
        records = [user("First request"), call("read-1", "cat /synthetic/review-skill/SKILL.md"),
                   output("read-1", shell_output("review-skill")), user("Second request"),
                   call("read-2", "cat /synthetic/review-skill/SKILL.md"), output("read-2", shell_output("review-skill"))]
        parsed = self.parse(records)
        self.store(parsed)
        self.assertEqual(len({item.request_key for item in parsed.skill_observations}), 2)
        self.store(parsed, source="codex-company")
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 2)

    def test_claude_missing_user_uuid_uses_its_own_request_fallback(self):
        records = []
        for index in (1, 2):
            user = {"type": "user", "message": {"content": "Request {}".format(index)}}
            if index == 1:
                user["uuid"] = "known-request"
            records.extend([user,
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "read-{}".format(index), "name": "Read", "input": {"file_path": "/synthetic/review-skill/SKILL.md"}}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "read-{}".format(index), "content": body("review-skill")}]}},
            ])
        self.store(self.parse(records, provider="claude"), provider="claude", source="claude")
        self.assertEqual(self.connection.execute("SELECT COUNT(DISTINCT request_key) FROM skill_observations").fetchone()[0], 2)

    def test_unknown_scope_retains_native_events_and_maintenance_is_excluded(self):
        records = [call("read-1", "cat /synthetic/review-skill/SKILL.md"), output("read-1", shell_output("review-skill")),
                   call("read-2", "cat /synthetic/review-skill/SKILL.md"), output("read-2", shell_output("review-skill"))]
        parsed = self.parse(records)
        self.assertTrue(all(item.request_key is None for item in parsed.skill_observations))
        self.store(parsed)
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
        parsed.session_class = "maintenance"
        self.store(parsed)
        self.assertIsNone(skill_insights_data(self.connection)["top"])

    def test_named_references_are_independent_of_language_and_use_wording(self):
        messages = [
            ("user", "$review-skill"),
            ("assistant", "review-skill은 참고만 했습니다."),
            ("assistant", "Do not use REVIEW-SKILL."),
            ("assistant", "À propos de review-skill."),
            ("assistant", "review-skillについて相談します。"),
            ("assistant", "```text\nreview-skill\n```"),
        ]
        records = [context("load", "review-skill")]
        records.extend({"type": "response_item", "payload": {
            "type": "message", "role": role, "id": "message-{}".format(index),
            "content": [{"type": "input_text" if role == "user" else "output_text", "text": text}],
        }} for index, (role, text) in enumerate(messages))
        parsed = self.parse(records)
        mentions = [item for item in parsed.skill_observations if item.signal_kind == "codex_skill_mention"]
        self.assertEqual({item.native_event_id for item in mentions},
                         {"mention:message-{}".format(index) for index in range(len(messages))})
        self.store(parsed)
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)

    def test_catalogs_tool_outputs_and_unknown_identifiers_are_not_mentions(self):
        records = [context("load", "review-skill")]
        for index, (role, text) in enumerate([
            ("developer", "Available skills: review-skill"),
            ("user", "# AGENTS.md instructions for /synthetic\n<INSTRUCTIONS>\nreview-skill\n</INSTRUCTIONS>"),
            ("user", "<environment_context>review-skill</environment_context>"),
            ("assistant", "unknown-skill and review-skill-extra"),
        ]):
            records.append({"type": "response_item", "payload": {
                "type": "message", "role": role, "id": "message-{}".format(index),
                "content": [{"type": "input_text", "text": text}],
            }})
        records.append(output("unrelated-tool", "review-skill"))
        parsed = self.parse(records)
        self.assertEqual([item.signal_kind for item in parsed.skill_observations], ["codex_skill_context"])
        # Installed names are not guessed in a Session with no identity evidence.
        self.assertEqual(self.parse(records[1:]).skill_observations, [])

    def test_plugin_aliases_require_unambiguous_source_identity(self):
        matcher = SkillReferenceMatcher(["sample:review-skill"])
        self.assertEqual(matcher.match("$review-skill 또는 sample:review-skill"), {"sample:review-skill"})
        matcher = SkillReferenceMatcher(["sample:review-skill", "other:review-skill"])
        self.assertEqual(matcher.match("review-skill"), set())
        self.assertEqual(matcher.match("sample:review-skill / other:review-skill"),
                         {"sample:review-skill", "other:review-skill"})

    def test_completed_native_script_records_identify_execution_arguments(self):
        records = [context("load", "review-skill")]
        commands = [
            ("run", "PYTHONDONTWRITEBYTECODE=1 python3 /synthetic/review-skill/scripts/validate.py", "completed", 0),
            ("failed", "python3 /synthetic/review-skill/scripts/validate.py", "failed", 1),
            ("read", "sed -n '1,30p' /synthetic/review-skill/scripts/validate.py", "completed", 0),
            ("example", "printf 'python3 /synthetic/review-skill/scripts/validate.py'", "completed", 0),
            ("pending", "python3 /synthetic/review-skill/scripts/validate.py", "in_progress", None),
            ("other", "python3 /synthetic/other/scripts/validate.py", "completed", 0),
        ]
        for identity, command, status, exit_code in commands:
            records.append({"type": "event_msg", "payload": {"type": "item_completed", "item": {
                "type": "CommandExecution", "id": identity, "command": ["/bin/zsh", "-lc", command],
                "cwd": "/synthetic", "status": status, "exit_code": exit_code,
            }}})
        parsed = self.parse(records)
        scripts = [item for item in parsed.skill_observations if item.signal_kind == "codex_skill_script"]
        self.assertEqual({item.native_event_id for item in scripts}, {"script:run", "script:failed"})
        self.store(parsed)
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)

    def test_heredoc_examples_and_dynamic_paths_are_not_script_executions(self):
        for command in [
            "cat <<'EXAMPLE'\npython3 /synthetic/review-skill/scripts/validate.py\nEXAMPLE",
            "python3 $ROOT/review-skill/scripts/validate.py",
            "python3 -c 'print(\"/synthetic/review-skill/scripts/validate.py\")'",
        ]:
            records = [context("load", "review-skill"), {"type": "event_msg", "payload": {
                "type": "item_completed", "item": {"type": "CommandExecution", "id": "example",
                    "command": ["/bin/zsh", "-lc", command], "status": "completed", "exit_code": 0},
            }}]
            self.assertEqual([item.signal_kind for item in self.parse(records).skill_observations],
                             ["codex_skill_context"], command)

    def test_claude_completed_bash_and_conversation_share_read_identity(self):
        records = [
            {"type": "user", "uuid": "request", "message": {"content": "Inspect the instructions"}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "read",
                "name": "Read", "input": {"file_path": "/synthetic/review-skill/SKILL.md"}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "read",
                "content": body("review-skill")}]}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "run",
                "name": "Bash", "input": {"command": "python3 /synthetic/review-skill/scripts/validate.py"}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "run", "content": "ok"}]}},
            {"type": "assistant", "uuid": "message", "message": {"content": "review-skillについて説明します。"}},
        ]
        parsed = self.parse(records, provider="claude")
        self.assertEqual({item.signal_kind for item in parsed.skill_observations},
                         {"claude_skill_read", "claude_skill_script", "claude_skill_mention"})
        self.store(parsed, provider="claude", source="claude")
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
        records[4]["message"]["content"][0]["is_error"] = True
        self.assertNotIn("claude_skill_script", {item.signal_kind for item in self.parse(records, provider="claude").skill_observations})

    def test_corrected_historical_declaration_is_not_reintroduced_as_mention(self):
        parsed = self.parse([context("load", "review-skill"), {"type": "response_item", "payload": {
            "type": "message", "role": "assistant", "id": "message",
            "content": [{"type": "output_text", "text": "review-skill"}],
        }}])
        mention = next(item for item in parsed.skill_observations if item.signal_kind == "codex_skill_mention")
        parsed.skill_observations = [replace(mention, native_event_id="declaration:message",
                                           signal_kind="codex_skill_declaration")]
        self.store(parsed)
        self.connection.execute("UPDATE skill_observations SET state='corrected'")
        parsed.skill_observations = [mention]
        self.assertEqual(self.store(parsed), 0)
        self.assertIsNone(skill_insights_data(self.connection)["top"])

    def test_new_native_session_adds_one_for_overlapping_evidence(self):
        parsed = self.parse([turn("one"), context("load", "review-skill"),
            call("read", "cat /synthetic/review-skill/SKILL.md"), output("read", shell_output("review-skill")),
            turn("two"), context("load-again", "review-skill")])
        self.store(parsed)
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
        parsed.external_id = "another-session"
        self.store(parsed)
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 2)

    def test_compatible_migration_retains_rows_states_times_ids_and_indexes(self):
        old_schema = SCHEMA.read_text(encoding="utf-8").replace(
            "'claude_skill_tool', 'codex_skill_context',\n            'claude_skill_read', 'codex_skill_read',\n            'claude_skill_declaration', 'codex_skill_declaration',\n            'claude_skill_mention', 'codex_skill_mention',\n            'claude_skill_script', 'codex_skill_script'",
            "'claude_skill_tool', 'codex_skill_context'",
        ).replace("    request_key TEXT CHECK(request_key IS NULL OR length(request_key) BETWEEN 1 AND 160),\n", "")
        old = sqlite3.connect(":memory:")
        old.row_factory = sqlite3.Row
        old.executescript(old_schema)
        old.execute("INSERT INTO skill_observations(id,source_key,provider_kind,external_session_id,native_event_id,skill_name,skill_group_key,signal_kind,source_line,state,recorded_at) VALUES ('old-id','codex','codex','gone','load','review-skill','review-skill','codex_skill_context',1,'corrected','2026-09-01')")
        before = dict(old.execute("SELECT * FROM skill_observations").fetchone())
        _migrate_skill_observation_contract(old)
        _migrate_skill_observation_contract(old)
        after = dict(old.execute("SELECT * FROM skill_observations").fetchone())
        self.assertIsNone(after.pop("request_key"))
        self.assertEqual(after, before)
        self.assertEqual(old.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name='skill_observations' AND sql IS NOT NULL").fetchone()[0], 2)
        old.execute("INSERT INTO skill_observations(id,source_key,provider_kind,external_session_id,native_event_id,skill_name,skill_group_key,signal_kind,source_line,request_key) VALUES ('read-id','codex','codex','gone','read','review-skill','review-skill','codex_skill_read',2,'request')")
        self.assertEqual(old.execute("PRAGMA quick_check").fetchone()[0], "ok")
        old.close()
