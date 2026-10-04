import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from localbrain.config import Settings
from localbrain.db import init_db
from localbrain.ingest import scanner
from localbrain.ingest.claude import parse_claude_session
from localbrain.ingest.codex import (
    CODEX_SESSION_CONTRACT_VERSION,
    CODEX_USAGE_CONTRACT_VERSION,
    parse_codex_session,
)
from localbrain.ingest.common import ParsedSession, ParsedSkillObservation
from localbrain.skill_observations import (
    correct_skill_observation,
    skill_insights_data,
    store_skill_observations,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


def parsed_session(external_id, *event_ids):
    return ParsedSession(
        external_id=external_id,
        source_path="/synthetic/{}.jsonl".format(external_id),
        cwd_raw=None,
        git_branch=None,
        title=external_id,
        started_at=None,
        ended_at=None,
        last_event_at=None,
        events=[],
        skill_observations=[
            ParsedSkillObservation(
                native_event_id=event_id,
                skill_name="Review Skill",
                signal_kind="codex_skill_context",
                source_line=index,
            )
            for index, event_id in enumerate(event_ids, start=1)
        ],
    )


class SkillObservationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.connection.execute(
            "INSERT INTO sources(kind, provider_kind, name, root_path) "
            "VALUES ('codex', 'codex', 'Codex', '/synthetic')"
        )
        source_id = self.connection.execute(
            "SELECT id FROM sources WHERE kind = 'codex'"
        ).fetchone()["id"]
        self.connection.execute(
            "INSERT INTO sessions(source_id, external_id, source_path, title) "
            "VALUES (?, 'old-session', '/synthetic/old-session.jsonl', 'Old session')",
            (source_id,),
        )

    def tearDown(self):
        self.connection.close()

    def test_resumed_and_new_sessions_add_only_new_events_and_survive_deletion(self):
        old = parsed_session("old-session", "event-1")
        self.assertEqual(
            store_skill_observations(
                self.connection, source_key="codex", provider_kind="codex", parsed=old
            ),
            1,
        )
        self.assertEqual(
            store_skill_observations(
                self.connection, source_key="codex", provider_kind="codex", parsed=old
            ),
            0,
        )
        old.source_path = "/synthetic/moved/old-session.jsonl"
        self.assertEqual(
            store_skill_observations(
                self.connection, source_key="codex", provider_kind="codex", parsed=old
            ),
            0,
        )
        resumed = parsed_session("old-session", "event-1", "event-2")
        self.assertEqual(
            store_skill_observations(
                self.connection,
                source_key="codex",
                provider_kind="codex",
                parsed=resumed,
            ),
            1,
        )
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
        renamed = parsed_session("old-session", "event-1")
        renamed.skill_observations[0] = ParsedSkillObservation(
            native_event_id="event-1",
            skill_name="Other Skill",
            signal_kind="codex_skill_context",
            source_line=1,
        )
        self.assertEqual(
            store_skill_observations(
                self.connection,
                source_key="codex",
                provider_kind="codex",
                parsed=renamed,
            ),
            0,
        )
        self.assertEqual(len(skill_insights_data(self.connection)["ranking"]), 1)

        self.connection.execute("DELETE FROM sessions WHERE external_id = 'old-session'")
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
        self.assertEqual(
            store_skill_observations(
                self.connection,
                source_key="codex",
                provider_kind="codex",
                parsed=resumed,
            ),
            0,
        )

        new = parsed_session("new-session", "event-1")
        self.assertEqual(
            store_skill_observations(
                self.connection, source_key="codex", provider_kind="codex", parsed=new
            ),
            1,
        )
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 2)

    def test_claude_and_codex_parsers_admit_explicit_signals_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            claude_path = root / "claude.jsonl"
            claude_path.write_text(
                json.dumps({
                    "type": "assistant",
                    "sessionId": "claude-synthetic",
                    "timestamp": "2026-09-01T01:00:00Z",
                    "message": {"content": [
                        {"type": "tool_use", "id": "toolu-skill", "name": "Skill",
                         "input": {"skill": "Review Skill"}},
                        {"type": "tool_use", "id": "toolu-read", "name": "Read",
                         "input": {"file_path": "/synthetic/SKILL.md"}},
                        {"type": "tool_use", "name": "Skill",
                         "input": {"skill": "Missing ID"}},
                    ]},
                }) + "\n",
                encoding="utf-8",
            )
            codex_path = root / "codex.jsonl"
            codex_path.write_text(
                "\n".join(json.dumps(record) for record in (
                    {"type": "session_meta", "payload": {
                        "id": "codex-synthetic", "cwd": "/synthetic"}},
                    {"type": "response_item", "timestamp": "2026-09-02T02:00:00Z",
                     "payload": {"type": "message", "role": "user", "id": "msg-skill",
                                 "content": [{"type": "input_text", "text":
                                              "<skill>\n<name>Review Skill</name>\n"
                                              "<path>/synthetic/SKILL.md</path>\n</skill>"}]}},
                    {"type": "response_item", "payload": {
                        "type": "message", "role": "user", "id": "msg-mention",
                        "content": [{"type": "input_text", "text":
                                     "Please read /synthetic/SKILL.md"}]}},
                    {"type": "response_item", "payload": {
                        "type": "message", "role": "user",
                        "content": [{"type": "input_text", "text":
                                     "<skill>\n<name>Missing ID</name>\n"
                                     "<path>/synthetic/SKILL.md</path>\n</skill>"}]}},
                )) + "\n",
                encoding="utf-8",
            )
            claude = parse_claude_session(claude_path)
            codex = parse_codex_session(codex_path)

        self.assertEqual(
            [(item.native_event_id, item.skill_name, item.signal_kind)
             for item in claude.skill_observations],
            [("toolu-skill", "Review Skill", "claude_skill_tool")],
        )
        self.assertEqual(
            [(item.native_event_id, item.skill_name, item.signal_kind)
             for item in codex.skill_observations],
            [("msg-skill", "Review Skill", "codex_skill_context")],
        )

    def test_ranking_combines_names_across_sources_and_keeps_last_event_time(self):
        first = parsed_session("old-session", "event-1")
        first.skill_observations[0] = replace(
            first.skill_observations[0], occurred_at="2026-09-01T01:00:00Z"
        )
        second = parsed_session("company-session", "event-2")
        second.skill_observations[0] = replace(
            second.skill_observations[0], skill_name=" review skill ",
            occurred_at="2026-09-02T02:00:00Z",
        )
        third = parsed_session("claude-session", "toolu-1")
        third.skill_observations[0] = replace(
            third.skill_observations[0], skill_name="REVIEW SKILL",
            signal_kind="claude_skill_tool", occurred_at="2026-09-01T03:00:00Z",
        )
        store_skill_observations(
            self.connection, source_key="codex", provider_kind="codex", parsed=first
        )
        store_skill_observations(
            self.connection, source_key="codex-company", provider_kind="codex",
            parsed=second,
        )
        store_skill_observations(
            self.connection, source_key="claude", provider_kind="claude", parsed=third
        )

        ranking = skill_insights_data(self.connection)["ranking"]
        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0]["use_count"], 3)
        self.assertEqual(ranking[0]["last_used_at"], "2026-09-02T02:00:00Z")
        self.assertEqual(
            {row[0] for row in self.connection.execute(
                "SELECT source_key FROM skill_observations")},
            {"codex", "codex-company", "claude"},
        )

    def test_equal_counts_use_stable_name_order_and_keep_missing_time_unknown(self):
        alpha = parsed_session("alpha-session", "event-1")
        alpha.skill_observations[0] = replace(
            alpha.skill_observations[0], skill_name="Alpha", occurred_at=None
        )
        zulu = parsed_session("zulu-session", "event-1")
        zulu.skill_observations[0] = replace(
            zulu.skill_observations[0], skill_name="Zulu",
            occurred_at="2026-09-01T01:00:00Z",
        )
        for parsed in (zulu, alpha):
            store_skill_observations(
                self.connection, source_key="codex", provider_kind="codex",
                parsed=parsed,
            )
        ranking = skill_insights_data(self.connection)["ranking"]
        self.assertEqual([row["name"] for row in ranking], ["Alpha", "Zulu"])
        self.assertIsNone(ranking[0]["last_used_at"])

    def test_maintenance_is_excluded_and_coverage_tracks_contract_repair(self):
        child = parsed_session("work-child", "child-event")
        child.session_role = "subsession"
        self.assertEqual(store_skill_observations(
            self.connection, source_key="codex", provider_kind="codex",
            parsed=child,
        ), 1)
        child.session_class = "maintenance"
        self.assertEqual(store_skill_observations(
            self.connection, source_key="codex", provider_kind="codex",
            parsed=child,
        ), 0)
        self.assertEqual(self.connection.execute(
            "SELECT state FROM skill_observations WHERE native_event_id = 'child-event'"
        ).fetchone()["state"], "corrected")
        maintenance = parsed_session("maintenance", "event-1")
        maintenance.session_class = "maintenance"
        self.assertEqual(store_skill_observations(
            self.connection, source_key="codex", provider_kind="codex",
            parsed=maintenance,
        ), 0)
        self.assertIsNone(skill_insights_data(self.connection)["top"])
        self.assertEqual(skill_insights_data(self.connection)["coverage"]["state"],
                         "not_scanned")

        source_id = self.connection.execute(
            "SELECT id FROM sources WHERE kind = 'codex'"
        ).fetchone()["id"]
        for path, version in (("/synthetic/current", CODEX_SESSION_CONTRACT_VERSION),
                              ("/synthetic/old", "old-version")):
            self.connection.execute(
                """INSERT INTO source_files(source_id, path, size_bytes, mtime_ns,
                   last_scanned_at, status, session_contract_version)
                   VALUES (?, ?, 1, 1, '2026-09-02T00:00:00Z', 'ok', ?)""",
                (source_id, path, version),
            )
        self.assertEqual(skill_insights_data(self.connection)["coverage"], {
            "file_count": 2, "current_file_count": 1, "state": "partial",
        })
        self.connection.execute(
            "UPDATE source_files SET session_contract_version = 'old-version'"
        )
        self.assertEqual(skill_insights_data(self.connection)["coverage"], {
            "file_count": 2, "current_file_count": 0, "state": "partial",
        })
        self.connection.execute(
            "UPDATE source_files SET session_contract_version = ?",
            (CODEX_SESSION_CONTRACT_VERSION,),
        )
        self.assertEqual(skill_insights_data(self.connection)["coverage"]["state"],
                         "current")

    def test_source_scan_adds_only_appended_skill_loads_and_retains_removed_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "synthetic.jsonl"
            records = [
                {"type": "session_meta", "timestamp": "2026-09-01T00:00:00Z",
                 "payload": {"id": "synthetic-session", "cwd": "/synthetic"}},
                {"type": "response_item", "timestamp": "2026-09-01T00:01:00Z",
                 "payload": {"type": "message", "role": "user", "id": "skill-1",
                             "content": [{"type": "input_text", "text":
                                          "<skill>\n<name>Review Skill</name>\n"
                                          "<path>/synthetic/SKILL.md</path>\n</skill>"}]}},
            ]

            def write_records():
                path.write_text("\n".join(json.dumps(item) for item in records) + "\n",
                                encoding="utf-8")

            def scan():
                return scanner._scan_session_source(
                    self.connection, "codex", "Codex", root,
                    parse_codex_session, CODEX_USAGE_CONTRACT_VERSION,
                    provider_kind="codex",
                    session_contract_version=CODEX_SESSION_CONTRACT_VERSION,
                )

            write_records()
            self.assertEqual(scan()[2], 0)
            self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
            self.assertEqual(scan()[2], 0)
            self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
            records.append({
                "type": "response_item", "timestamp": "2026-09-02T00:01:00Z",
                "payload": {"type": "message", "role": "user", "id": "skill-2",
                            "content": [{"type": "input_text", "text":
                                         "<skill>\n<name>Review Skill</name>\n"
                                         "<path>/synthetic/SKILL.md</path>\n</skill>"}]},
            })
            write_records()
            self.assertEqual(scan()[2], 0)
            self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
            path.unlink()
            self.assertEqual(scan()[2], 0)
            self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
            self.assertEqual(skill_insights_data(self.connection)["coverage"]["state"],
                             "not_scanned")

    def test_compatible_startup_adds_skill_table_without_losing_sessions(self):
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            database_path = data_dir / "localbrain.db"
            legacy = sqlite3.connect(database_path)
            legacy.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            legacy.execute("DROP TABLE skill_observations")
            legacy.execute(
                "INSERT INTO sources(kind, provider_kind, name, root_path) "
                "VALUES ('codex', 'codex', 'Codex', '/synthetic')"
            )
            legacy.execute(
                "INSERT INTO sessions(source_id, external_id, source_path, title) "
                "VALUES (1, 'retained', '/synthetic/retained.jsonl', 'Retained')"
            )
            legacy.commit()
            legacy.close()

            settings = Settings(
                data_dir=data_dir,
                database_path=database_path,
                context_root=data_dir / "context",
                claude_root=data_dir / "claude",
                codex_root=data_dir / "codex",
                mcp_call_budget=20,
            )
            with patch("localbrain.db.settings", settings):
                init_db()
                init_db()

            upgraded = sqlite3.connect(database_path)
            try:
                self.assertEqual(upgraded.execute(
                    "SELECT external_id FROM sessions"
                ).fetchall(), [("retained",)])
                self.assertEqual(upgraded.execute(
                    "SELECT COUNT(*) FROM skill_observations"
                ).fetchone()[0], 0)
                self.assertEqual(upgraded.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='index' "
                    "AND name='idx_skill_observations_group'"
                ).fetchone()[0], 1)
            finally:
                upgraded.close()

    def test_targeted_correction_invalidates_only_proven_native_event(self):
        old = parsed_session("old-session", "event-1", "event-2")
        store_skill_observations(
            self.connection, source_key="codex", provider_kind="codex", parsed=old
        )
        self.connection.execute("DELETE FROM sessions WHERE external_id = 'old-session'")
        self.assertEqual(correct_skill_observation(
            self.connection, source_key="codex", external_session_id="old-session",
            native_event_id="not-present",
        ), 0)
        self.assertEqual(correct_skill_observation(
            self.connection, source_key="codex", external_session_id="old-session",
            native_event_id="event-1",
        ), 1)
        self.assertEqual(correct_skill_observation(
            self.connection, source_key="codex", external_session_id="old-session",
            native_event_id="event-1",
        ), 0)
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)
        self.assertEqual(store_skill_observations(
            self.connection, source_key="codex", provider_kind="codex", parsed=old
        ), 0)
        self.assertEqual(skill_insights_data(self.connection)["top"]["use_count"], 1)


if __name__ == "__main__":
    unittest.main()
