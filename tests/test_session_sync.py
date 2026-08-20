import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.config import Settings
from localbrain import db
from localbrain.ingest import scanner
from localbrain.main import scan_sources_page, sync_session_sources, sync_sessions_page
from localbrain.queries import session_detail, session_subsessions


class SessionSyncTests(unittest.TestCase):
    def _settings(self, root: Path) -> Settings:
        data_dir = root / "runtime"
        source_roots = {
            "claude": root / "claude",
            "codex": root / "codex",
            "codex-company": root / "codex-company",
        }
        for source_root in source_roots.values():
            source_root.mkdir(parents=True)
        data_dir.mkdir()
        (data_dir / "session-sources.toml").write_text(
            """schema_version = 1
[[session_sources]]
source_key = "claude"
display_label = "Claude Code"
provider_kind = "claude"
root = "{claude}"
[[session_sources]]
source_key = "codex"
display_label = "Codex"
provider_kind = "codex"
root = "{codex}"
[[session_sources]]
source_key = "codex-company"
display_label = "Codex Company"
provider_kind = "codex"
root = "{company}"
""".format(
                claude=source_roots["claude"],
                codex=source_roots["codex"],
                company=source_roots["codex-company"],
            ),
            encoding="utf-8",
        )
        return Settings(
            data_dir=data_dir,
            database_path=data_dir / "localbrain.db",
            context_root=root / "context",
            claude_root=source_roots["claude"],
            codex_root=source_roots["codex"],
            mcp_call_budget=20,
            timezone_name="UTC",
            session_sources_path=data_dir / "session-sources.toml",
        )

    def _write_codex_session(self, path: Path, external_id: str, message: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                json.dumps(record)
                for record in (
                    {
                        "type": "session_meta",
                        "timestamp": "2026-08-02T01:00:00Z",
                        "payload": {"id": external_id, "cwd": "/tmp/project"},
                    },
                    {
                        "type": "event_msg",
                        "timestamp": "2026-08-02T01:01:00Z",
                        "payload": {"type": "user_message", "message": message},
                    },
                    {
                        "type": "event_msg",
                        "timestamp": "2026-08-02T01:02:00Z",
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
                )
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_claude_session(self, path: Path, external_id: str, message: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "type": "user",
                    "sessionId": external_id,
                    "timestamp": "2026-08-02T01:00:00Z",
                    "cwd": "/tmp/project",
                    "message": {"content": message},
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_codex_guardian(
        self, path: Path, external_id: str, parent_external_id: str
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                json.dumps(record)
                for record in (
                    {
                        "type": "session_meta",
                        "timestamp": "2026-08-20T01:00:00Z",
                        "payload": {
                            "id": external_id,
                            "cwd": "/tmp/project",
                            "source": {"subagent": {"other": "guardian"}},
                            "parent_thread_id": parent_external_id,
                        },
                    },
                    {
                        "type": "turn_context",
                        "timestamp": "2026-08-20T01:00:01Z",
                        "payload": {
                            "turn_id": "guardian-turn",
                            "model": "gpt-5.6-sol",
                        },
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
                )
            )
            + "\n",
            encoding="utf-8",
        )

    def test_session_scan_report_dispatches_all_three_configured_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            settings = self._settings(Path(temporary))
            with patch.object(db, "settings", settings), patch.object(
                scanner, "settings", settings
            ), patch.object(
                scanner,
                "_scan_session_source",
                side_effect=((2, 3, 0), (1, 4, 0), (5, 6, 0)),
            ) as scan_source, patch.object(
                scanner, "_scan_context_documents"
            ) as scan_context:
                report = scanner.scan_session_sources()

        self.assertEqual(report["outcome"], "complete")
        self.assertEqual(
            [item["source_key"] for item in report["sources"]],
            ["claude", "codex", "codex-company"],
        )
        self.assertEqual(report["summary"]["imported"], 8)
        self.assertEqual(report["summary"]["unchanged"], 13)
        self.assertEqual(set(report), {"outcome", "summary", "sources"})
        self.assertEqual(
            set(report["sources"][0]),
            {
                "source_key",
                "display_label",
                "provider_kind",
                "root",
                "status",
                "imported",
                "unchanged",
                "failed_files",
                "eligible_sessions",
                "tracked_files",
                "last_attempt_at",
                "last_success_at",
                "error_code",
                "error_message",
                "retained_data",
            },
        )
        self.assertEqual(scan_source.call_count, 3)
        self.assertEqual(
            [call.kwargs["provider_kind"] for call in scan_source.call_args_list],
            ["claude", "codex", "codex"],
        )
        scan_context.assert_not_called()

    def test_codex_guardian_repair_keeps_usage_and_suppresses_work_surfaces(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = self._settings(root)
            parent_path = settings.codex_root / "2026" / "08" / "parent.jsonl"
            guardian_path = settings.codex_root / "2026" / "08" / "guardian.jsonl"
            self._write_codex_session(parent_path, "codex-parent", "Primary work")
            self._write_codex_guardian(
                guardian_path, "codex-guardian", "codex-parent"
            )

            with patch.object(db, "settings", settings), patch.object(
                scanner, "settings", settings
            ):
                db.init_db()
                with db.connect() as connection:
                    source_id = scanner._upsert_source(
                        connection,
                        "codex",
                        "codex",
                        "Codex",
                        settings.codex_root,
                    )
                    parsed_guardian = scanner.parse_codex_session(guardian_path)
                    parsed_guardian.session_class = "work"
                    parsed_guardian.index_policy = "full"
                    parsed_guardian.title = "Approval history prompt"
                    guardian_id = scanner._store_session(
                        connection,
                        source_id,
                        "codex",
                        parsed_guardian,
                        usage_contract_version="codex-legacy-guardian-work-v1",
                        provider_kind="codex",
                    )
                    scanner._record_source_file(
                        connection,
                        source_id,
                        guardian_path,
                        usage_contract_version="codex-legacy-guardian-work-v1",
                        session_id=guardian_id,
                    )
                    connection.commit()

                report = scanner.scan_session_sources()

                with db.connect() as connection:
                    rows = {
                        row["external_id"]: row
                        for row in connection.execute(
                            """
                            SELECT sessions.id AS id, external_id, title, session_class,
                                   session_role, parent_session_id, index_policy,
                                   event_count, user_message_count,
                                   assistant_message_count
                            FROM sessions
                            JOIN sources ON sources.id = sessions.source_id
                            WHERE sources.kind = 'codex'
                            ORDER BY sessions.external_id
                            """
                        ).fetchall()
                    }
                    parent = rows["codex-parent"]
                    guardian = rows["codex-guardian"]
                    guardian_event_count = connection.execute(
                        "SELECT COUNT(*) FROM activity_events WHERE session_id = ?",
                        (guardian["id"],),
                    ).fetchone()[0]
                    guardian_usage_count = connection.execute(
                        "SELECT COUNT(*) FROM usage_records WHERE session_id = ?",
                        (guardian["id"],),
                    ).fetchone()[0]
                    guardian_search_count = connection.execute(
                        """
                        SELECT COUNT(*) FROM search_index
                        WHERE entity_type = 'session' AND entity_id = ?
                        """,
                        (str(guardian["id"]),),
                    ).fetchone()[0]
                    visible_children = session_subsessions(connection, parent["id"])
                    guardian_detail = session_detail(connection, guardian["id"])

        codex_report = next(
            item for item in report["sources"] if item["source_key"] == "codex"
        )
        self.assertEqual(codex_report["status"], "completed")
        self.assertEqual(guardian["title"], "Codex guardian")
        self.assertEqual(guardian["session_class"], "maintenance")
        self.assertEqual(guardian["session_role"], "subsession")
        self.assertEqual(guardian["parent_session_id"], parent["id"])
        self.assertEqual(guardian["index_policy"], "metadata_only")
        self.assertEqual(
            (
                guardian["event_count"],
                guardian["user_message_count"],
                guardian["assistant_message_count"],
            ),
            (0, 0, 0),
        )
        self.assertEqual(guardian_event_count, 0)
        self.assertEqual(guardian_usage_count, 1)
        self.assertEqual(guardian_search_count, 0)
        self.assertEqual(visible_children, [])
        self.assertIsNone(guardian_detail)

    def test_claude_scan_excludes_nested_workflow_journal_and_reconciles_false_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = self._settings(root)
            project_root = root / "claude" / "synthetic-project"
            primary_path = project_root / "primary-one.jsonl"
            child_path = (
                project_root
                / "primary-one"
                / "subagents"
                / "agent-child.jsonl"
            )
            journal_path = (
                project_root
                / "primary-one"
                / "subagents"
                / "workflows"
                / "wf-synthetic"
                / "journal.jsonl"
            )
            self._write_claude_session(primary_path, "primary-one", "Primary")
            self._write_claude_session(child_path, "native-child", "Child")
            journal_path.parent.mkdir(parents=True)
            journal_path.write_text(
                "\n".join(
                    json.dumps(record)
                    for record in (
                        {"type": "started", "agentId": "agent-a", "key": "one"},
                        {"type": "result", "agentId": "agent-a", "key": "one"},
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            with patch.object(db, "settings", settings), patch.object(
                scanner, "settings", settings
            ):
                db.init_db()
                with db.connect() as connection:
                    scanner._scan_session_source(
                        connection,
                        "claude",
                        "Claude Code",
                        settings.claude_root,
                        scanner.parse_claude_session,
                        scanner.CLAUDE_USAGE_CONTRACT_VERSION,
                        provider_kind="claude",
                    )
                    parsed_journal = scanner.parse_claude_session(journal_path)
                    scanner._store_session(
                        connection,
                        connection.execute(
                            "SELECT id FROM sources WHERE kind = 'claude'"
                        ).fetchone()["id"],
                        "claude",
                        parsed_journal,
                        usage_contract_version=scanner.CLAUDE_USAGE_CONTRACT_VERSION,
                        provider_kind="claude",
                    )
                    scanner._record_source_file(
                        connection,
                        connection.execute(
                            "SELECT id FROM sources WHERE kind = 'claude'"
                        ).fetchone()["id"],
                        journal_path,
                        usage_contract_version=scanner.CLAUDE_USAGE_CONTRACT_VERSION,
                    )
                    legacy_false_session = connection.execute(
                        """
                        SELECT sessions.id
                        FROM sessions
                        JOIN sources ON sources.id = sessions.source_id
                        WHERE sources.kind = 'claude'
                          AND sessions.source_path = ?
                          AND sessions.session_role = 'primary'
                        """,
                        (str(journal_path),),
                    ).fetchone()
                    connection.commit()

                report = scanner.scan_session_sources()
                with db.connect() as connection:
                    sessions = connection.execute(
                        """
                        SELECT sessions.external_id, sessions.session_role,
                               sessions.parent_external_id
                        FROM sessions
                        JOIN sources ON sources.id = sessions.source_id
                        WHERE sources.kind = 'claude'
                        ORDER BY sessions.external_id
                        """
                    ).fetchall()
                    tracked_paths = connection.execute(
                        """
                        SELECT source_files.path
                        FROM source_files
                        JOIN sources ON sources.id = source_files.source_id
                        WHERE sources.kind = 'claude'
                        ORDER BY source_files.path
                        """
                    ).fetchall()
                journal_preserved = journal_path.exists()

        self.assertIsNotNone(legacy_false_session)
        self.assertTrue(journal_preserved)
        self.assertEqual(
            [tuple(row) for row in sessions],
            [
                ("agent-child", "subsession", "primary-one"),
                ("primary-one", "primary", None),
            ],
        )
        self.assertEqual(
            {row["path"] for row in tracked_paths},
            {str(child_path), str(primary_path)},
        )
        claude = next(
            source for source in report["sources"] if source["source_key"] == "claude"
        )
        self.assertEqual(claude["status"], "completed")
        self.assertEqual(claude["eligible_sessions"], 1)
        self.assertEqual(claude["tracked_files"], 2)

    def test_sync_removes_empty_stub_and_reimports_after_meaningful_growth(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = self._settings(root)
            project_root = root / "claude" / "synthetic-project"
            meaningful_path = project_root / "meaningful.jsonl"
            empty_path = project_root / "empty-stub.jsonl"
            self._write_claude_session(
                meaningful_path, "meaningful-session", "Meaningful"
            )
            empty_path.parent.mkdir(parents=True, exist_ok=True)
            empty_path.write_text(
                "\n".join(
                    json.dumps(record)
                    for record in (
                        {
                            "type": "ai-title",
                            "sessionId": "empty-stub",
                            "aiTitle": "Metadata only",
                        },
                        {
                            "type": "agent-name",
                            "sessionId": "empty-stub",
                            "agentName": "synthetic-agent",
                        },
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            original_empty_bytes = empty_path.read_bytes()

            with patch.object(db, "settings", settings), patch.object(
                scanner, "settings", settings
            ):
                db.init_db()
                with db.connect() as connection:
                    source_id = scanner._upsert_source(
                        connection,
                        "claude",
                        "claude",
                        "Claude Code",
                        settings.claude_root,
                    )
                    parsed_empty = scanner.parse_claude_session(empty_path)
                    legacy_session_id = scanner._store_session(
                        connection,
                        source_id,
                        "claude",
                        parsed_empty,
                        usage_contract_version=scanner.CLAUDE_USAGE_CONTRACT_VERSION,
                        provider_kind="claude",
                    )
                    scanner._record_source_file(
                        connection,
                        source_id,
                        empty_path,
                        usage_contract_version=scanner.CLAUDE_USAGE_CONTRACT_VERSION,
                    )
                    connection.execute(
                        """
                        INSERT INTO session_pins(session_id, pinned_at)
                        VALUES (?, '2026-08-03T00:00:00Z')
                        """,
                        (legacy_session_id,),
                    )
                    connection.commit()

                first = scanner.scan_session_sources()
                with db.connect() as connection:
                    first_sessions = connection.execute(
                        """
                        SELECT sessions.external_id
                        FROM sessions
                        JOIN sources ON sources.id = sessions.source_id
                        WHERE sources.kind = 'claude'
                        ORDER BY sessions.external_id
                        """
                    ).fetchall()
                    first_tracked = connection.execute(
                        """
                        SELECT source_files.path
                        FROM source_files
                        JOIN sources ON sources.id = source_files.source_id
                        WHERE sources.kind = 'claude'
                        ORDER BY source_files.path
                        """
                    ).fetchall()
                    first_pins = connection.execute(
                        "SELECT COUNT(*) FROM session_pins"
                    ).fetchone()[0]
                    first_search = connection.execute(
                        """
                        SELECT COUNT(*) FROM search_index
                        WHERE entity_type = 'session' AND entity_id = ?
                        """,
                        (str(legacy_session_id),),
                    ).fetchone()[0]
                empty_preserved_after_cleanup = (
                    empty_path.read_bytes() == original_empty_bytes
                )

                second = scanner.scan_session_sources()
                with db.connect() as connection:
                    repeated_stub_count = connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM sessions
                        JOIN sources ON sources.id = sessions.source_id
                        WHERE sources.kind = 'claude'
                          AND sessions.external_id = 'empty-stub'
                        """
                    ).fetchone()[0]
                    repeated_stub_file_count = connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM source_files
                        JOIN sources ON sources.id = source_files.source_id
                        WHERE sources.kind = 'claude'
                          AND source_files.path = ?
                        """,
                        (str(empty_path),),
                    ).fetchone()[0]

                with empty_path.open("a", encoding="utf-8") as stream:
                    stream.write(
                        json.dumps(
                            {
                                "type": "user",
                                "sessionId": "empty-stub",
                                "timestamp": "2026-08-03T00:01:00Z",
                                "cwd": "/tmp/project",
                                "message": {"content": "Now meaningful"},
                            }
                        )
                        + "\n"
                    )
                third = scanner.scan_session_sources()
                with db.connect() as connection:
                    restored = connection.execute(
                        """
                        SELECT sessions.event_count
                        FROM sessions
                        JOIN sources ON sources.id = sessions.source_id
                        WHERE sources.kind = 'claude'
                          AND sessions.external_id = 'empty-stub'
                        """
                    ).fetchone()
                    restored_file_count = connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM source_files
                        JOIN sources ON sources.id = source_files.source_id
                        WHERE sources.kind = 'claude'
                          AND source_files.path = ?
                        """,
                        (str(empty_path),),
                    ).fetchone()[0]
                empty_exists_after_reimport = empty_path.exists()

        self.assertEqual(
            [row["external_id"] for row in first_sessions],
            ["meaningful-session"],
        )
        self.assertEqual(
            [row["path"] for row in first_tracked],
            [str(meaningful_path)],
        )
        self.assertEqual(first_pins, 0)
        self.assertEqual(first_search, 0)
        self.assertTrue(empty_preserved_after_cleanup)
        self.assertTrue(empty_exists_after_reimport)
        self.assertEqual(repeated_stub_count, 0)
        self.assertEqual(repeated_stub_file_count, 0)
        self.assertEqual(restored["event_count"], 1)
        self.assertEqual(restored_file_count, 1)

        first_claude = next(
            source for source in first["sources"] if source["source_key"] == "claude"
        )
        second_claude = next(
            source for source in second["sources"] if source["source_key"] == "claude"
        )
        third_claude = next(
            source for source in third["sources"] if source["source_key"] == "claude"
        )
        self.assertEqual(
            (first_claude["eligible_sessions"], first_claude["tracked_files"]),
            (1, 1),
        )
        self.assertEqual(
            (second_claude["eligible_sessions"], second_claude["tracked_files"]),
            (1, 1),
        )
        self.assertEqual(
            (third_claude["eligible_sessions"], third_claude["tracked_files"]),
            (2, 2),
        )

    def test_empty_candidate_preserves_meaningful_shared_native_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = self._settings(root)
            project_root = root / "claude" / "synthetic-project"
            meaningful_path = project_root / "a-meaningful.jsonl"
            empty_path = project_root / "z-empty.jsonl"
            self._write_claude_session(
                meaningful_path, "shared-session", "Meaningful"
            )
            empty_path.parent.mkdir(parents=True, exist_ok=True)
            empty_path.write_text(
                json.dumps(
                    {
                        "type": "ai-title",
                        "sessionId": "shared-session",
                        "aiTitle": "Metadata only sibling",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            with patch.object(db, "settings", settings), patch.object(
                scanner, "settings", settings
            ):
                db.init_db()
                with db.connect() as connection:
                    source_id = scanner._upsert_source(
                        connection,
                        "claude",
                        "claude",
                        "Claude Code",
                        settings.claude_root,
                    )
                    legacy_session_id = scanner._store_session(
                        connection,
                        source_id,
                        "claude",
                        scanner.parse_claude_session(empty_path),
                        usage_contract_version=scanner.CLAUDE_USAGE_CONTRACT_VERSION,
                        provider_kind="claude",
                    )
                    scanner._record_source_file(
                        connection,
                        source_id,
                        empty_path,
                        usage_contract_version=scanner.CLAUDE_USAGE_CONTRACT_VERSION,
                    )
                    connection.execute(
                        """
                        INSERT INTO session_pins(session_id, pinned_at)
                        VALUES (?, '2026-08-03T00:00:00Z')
                        """,
                        (legacy_session_id,),
                    )
                    connection.commit()

                report = scanner.scan_session_sources()
                with db.connect() as connection:
                    shared = connection.execute(
                        """
                        SELECT sessions.id, sessions.event_count,
                               sessions.source_path
                        FROM sessions
                        JOIN sources ON sources.id = sessions.source_id
                        WHERE sources.kind = 'claude'
                          AND sessions.external_id = 'shared-session'
                        """
                    ).fetchone()
                    pin_count = connection.execute(
                        "SELECT COUNT(*) FROM session_pins WHERE session_id = ?",
                        (legacy_session_id,),
                    ).fetchone()[0]
                    empty_tracking = connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM source_files
                        WHERE source_id = ? AND path = ?
                        """,
                        (source_id, str(empty_path)),
                    ).fetchone()[0]
                empty_source_preserved = empty_path.exists()

        self.assertEqual(shared["id"], legacy_session_id)
        self.assertEqual(shared["event_count"], 1)
        self.assertEqual(shared["source_path"], str(meaningful_path))
        self.assertEqual(pin_count, 1)
        self.assertEqual(empty_tracking, 0)
        self.assertTrue(empty_source_preserved)
        claude = next(
            source for source in report["sources"] if source["source_key"] == "claude"
        )
        self.assertEqual(
            (claude["eligible_sessions"], claude["tracked_files"]),
            (1, 1),
        )

    def test_same_codex_native_id_and_stale_deletion_are_source_scoped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = self._settings(root)
            personal_file = root / "codex" / "personal.jsonl"
            company_file = root / "codex-company" / "company.jsonl"
            self._write_codex_session(
                personal_file,
                "shared-native-id",
                "Personal https://personal.example.test/reference",
            )
            self._write_codex_session(
                company_file,
                "shared-native-id",
                "Company https://company.example.test/reference",
            )
            with patch.object(db, "settings", settings), patch.object(
                scanner, "settings", settings
            ):
                first = scanner.scan_session_sources()
                with db.connect() as connection:
                    rows = connection.execute(
                        """
                        SELECT sources.kind, sessions.id
                        FROM sessions JOIN sources ON sources.id = sessions.source_id
                        WHERE sessions.external_id = 'shared-native-id'
                        ORDER BY sources.kind
                        """
                    ).fetchall()
                    scan_errors = connection.execute(
                        "SELECT path, error FROM source_files WHERE status = 'error'"
                    ).fetchall()
                    references = connection.execute(
                        """
                        SELECT sources.kind,
                               session_reference_evidence.normalized_url
                        FROM session_reference_evidence
                        JOIN sessions
                          ON sessions.id = session_reference_evidence.session_id
                        JOIN sources ON sources.id = sessions.source_id
                        ORDER BY sources.kind
                        """
                    ).fetchall()
                    self.assertEqual(
                        connection.execute("SELECT COUNT(*) FROM activity_events").fetchone()[0],
                        2,
                    )
                    self.assertEqual(
                        connection.execute("SELECT COUNT(*) FROM usage_records").fetchone()[0],
                        2,
                    )
                    self.assertEqual([row["kind"] for row in rows], ["codex", "codex-company"])
                    self.assertEqual(
                        [
                            (row["kind"], row["normalized_url"])
                            for row in references
                        ],
                        [
                            ("codex", "https://personal.example.test/reference"),
                            ("codex-company", "https://company.example.test/reference"),
                        ],
                    )
                    connection.executemany(
                        "INSERT INTO session_pins(session_id, pinned_at) VALUES (?, '2026-08-02T01:02:00Z')",
                        [(row["id"],) for row in rows],
                    )
                    connection.commit()

                personal_file.unlink()
                second = scanner.scan_session_sources()
                with db.connect() as connection:
                    retained = connection.execute(
                        """
                        SELECT sources.kind, sessions.id
                        FROM sessions JOIN sources ON sources.id = sessions.source_id
                        WHERE sessions.external_id = 'shared-native-id'
                        """
                    ).fetchall()
                    pins = connection.execute(
                        """
                        SELECT sources.kind
                        FROM session_pins
                        JOIN sessions ON sessions.id = session_pins.session_id
                        JOIN sources ON sources.id = sessions.source_id
                        """
                    ).fetchall()

        self.assertEqual(first["outcome"], "complete", (first, [dict(row) for row in scan_errors]))
        self.assertEqual([row["kind"] for row in retained], ["codex-company"])
        self.assertEqual([row["kind"] for row in pins], ["codex-company"])
        outcomes = {item["source_key"]: item for item in second["sources"]}
        self.assertEqual(outcomes["codex"]["status"], "empty")
        self.assertEqual(outcomes["codex-company"]["status"], "completed")

    def test_unavailable_root_preserves_prior_session_and_other_sources_commit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = self._settings(root)
            personal_file = root / "codex" / "personal.jsonl"
            company_file = root / "codex-company" / "company.jsonl"
            self._write_codex_session(personal_file, "personal-one", "Personal")
            self._write_codex_session(company_file, "company-one", "Company")
            with patch.object(db, "settings", settings), patch.object(
                scanner, "settings", settings
            ):
                scanner.scan_session_sources()
                company_file.unlink()
                (root / "codex-company").rmdir()
                self._write_codex_session(
                    root / "codex" / "personal-two.jsonl", "personal-two", "New"
                )

                report = scanner.scan_session_sources()
                with db.connect() as connection:
                    sessions = connection.execute(
                        """
                        SELECT sources.kind, sessions.external_id
                        FROM sessions JOIN sources ON sources.id = sessions.source_id
                        ORDER BY sources.kind, sessions.external_id
                        """
                    ).fetchall()
                    company_health = connection.execute(
                        """
                        SELECT last_scan_status, last_scan_error
                        FROM sources WHERE kind = 'codex-company'
                        """
                    ).fetchone()

        self.assertEqual(report["outcome"], "partial")
        self.assertEqual(
            [(row["kind"], row["external_id"]) for row in sessions],
            [
                ("codex", "personal-one"),
                ("codex", "personal-two"),
                ("codex-company", "company-one"),
            ],
        )
        outcomes = {item["source_key"]: item for item in report["sources"]}
        self.assertEqual(outcomes["codex-company"]["status"], "unavailable")
        self.assertTrue(outcomes["codex-company"]["retained_data"])
        self.assertEqual(company_health["last_scan_status"], "unavailable")
        self.assertIn("retained", company_health["last_scan_error"])

    def test_malformed_settings_preserve_registered_source_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = self._settings(root)
            self._write_codex_session(
                root / "codex-company" / "company.jsonl",
                "company-one",
                "Company",
            )
            with patch.object(db, "settings", settings), patch.object(
                scanner, "settings", settings
            ):
                scanner.scan_session_sources()
                settings.session_sources_path.write_text(
                    "schema_version = 1\n[[session_sources]\n",
                    encoding="utf-8",
                )
                report = scanner.scan_session_sources()
                with db.connect() as connection:
                    retained = connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM sessions
                        JOIN sources ON sources.id = sessions.source_id
                        WHERE sources.kind = 'codex-company'
                          AND sessions.external_id = 'company-one'
                        """
                    ).fetchone()[0]

        self.assertEqual(report["outcome"], "failed")
        self.assertEqual(retained, 1)
        self.assertTrue(report["sources"])
        for source in report["sources"]:
            self.assertEqual(source["status"], "configuration_error")
            self.assertTrue(source["retained_data"])
            self.assertIn("not synchronized", source["error_message"])
            self.assertIn("retained", source["error_message"])
            self.assertLessEqual(len(source["error_message"]), 500)

    def test_wider_scan_keeps_session_results_when_context_scan_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            settings = self._settings(Path(temporary))
            with patch.object(db, "settings", settings), patch.object(
                scanner, "settings", settings
            ), patch.object(
                scanner,
                "_scan_context_documents",
                side_effect=RuntimeError("private context detail"),
            ):
                report = scanner.scan_all()

        self.assertEqual(report["outcome"], "partial")
        self.assertEqual(
            [source["source_key"] for source in report["sources"]],
            ["claude", "codex", "codex-company", "context"],
        )
        context = report["sources"][-1]
        self.assertEqual(context["status"], "scan_failed")
        self.assertNotIn("private context", context["error_message"])
        self.assertTrue(context["retained_data"])

    def test_unexpected_source_failure_rolls_back_only_that_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = self._settings(root)
            self._write_codex_session(
                root / "codex" / "personal-one.jsonl", "personal-one", "Personal"
            )
            self._write_codex_session(
                root / "codex-company" / "company-one.jsonl", "company-one", "Company"
            )
            with patch.object(db, "settings", settings), patch.object(
                scanner, "settings", settings
            ):
                scanner.scan_session_sources()
                self._write_codex_session(
                    root / "codex" / "personal-two.jsonl", "personal-two", "New"
                )
                original_scan = scanner._scan_session_source

                def fail_company(connection, source_key, *args, **kwargs):
                    if source_key == "codex-company":
                        connection.execute(
                            """
                            DELETE FROM sessions WHERE source_id = (
                                SELECT id FROM sources WHERE kind = 'codex-company'
                            )
                            """
                        )
                        raise RuntimeError("private parser payload must not leak")
                    return original_scan(connection, source_key, *args, **kwargs)

                with patch.object(
                    scanner, "_scan_session_source", side_effect=fail_company
                ):
                    report = scanner.scan_session_sources()
                with db.connect() as connection:
                    sessions = connection.execute(
                        """
                        SELECT sources.kind, sessions.external_id
                        FROM sessions JOIN sources ON sources.id = sessions.source_id
                        ORDER BY sources.kind, sessions.external_id
                        """
                    ).fetchall()

        self.assertEqual(report["outcome"], "partial")
        self.assertEqual(
            [(row["kind"], row["external_id"]) for row in sessions],
            [
                ("codex", "personal-one"),
                ("codex", "personal-two"),
                ("codex-company", "company-one"),
            ],
        )
        outcomes = {item["source_key"]: item for item in report["sources"]}
        self.assertEqual(outcomes["codex-company"]["status"], "scan_failed")
        self.assertNotIn("private parser", outcomes["codex-company"]["error_message"])
        self.assertTrue(outcomes["codex-company"]["retained_data"])

    def test_sessions_sync_endpoint_uses_session_only_scanner(self):
        expected = {
            "outcome": "complete",
            "summary": {"source_count": 0},
            "sources": [],
        }
        with patch("localbrain.main.scan_session_sources", return_value=expected):
            self.assertEqual(
                sync_session_sources(),
                {"ok": True, "report": expected},
            )

    def test_sessions_sync_form_fallback_preserves_inventory_scope(self):
        with patch(
            "localbrain.main.scan_session_sources",
            return_value={
                "outcome": "partial",
                "summary": {},
                "sources": [{"source_key": "codex"}],
            },
        ) as scan_sources:
            projects = sync_sessions_page(view="projects")
            sessions = sync_sessions_page(
                view="sessions", source="codex", workspace=7, page=3
            )

        self.assertEqual(projects.status_code, 303)
        self.assertEqual(projects.headers["location"], "/projects?sync=partial")
        self.assertEqual(sessions.status_code, 303)
        self.assertEqual(
            sessions.headers["location"],
            "/sessions?sync=partial&source=codex&workspace=7&page=3",
        )
        self.assertEqual(scan_sources.call_count, 2)

    def test_sources_scan_form_fallback_reports_aggregate_outcome(self):
        with patch(
            "localbrain.main.scan_all",
            return_value={"outcome": "failed", "summary": {}, "sources": []},
        ) as scan_everything:
            response = scan_sources_page()

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/sources?sync=failed")
        scan_everything.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
