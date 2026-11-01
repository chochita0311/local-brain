"""Retained history is independent from native original availability."""

import sqlite3
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import test_compressed_sessions as compressed_fixtures
from localbrain.ingest.contracts import CODEX_SESSION_REVISION, CODEX_USAGE_CONTRACT_VERSION
from localbrain.ingest.contracts import CLAUDE_SESSION_REVISION, CLAUDE_USAGE_CONTRACT_VERSION
from localbrain.ingest.providers.codex import parse_codex_session
from localbrain.ingest.providers.claude import parse_claude_session
from localbrain.ingest.sync.sessions import _scan_session_source, _session_paths
from localbrain.sessions.pins import pin_session, unpin_session
from localbrain.sessions.queries import session_detail, session_conversation_events
from localbrain.persistence.migrations.compatible import _run_compatible_migrations
from localbrain.ingest import scanner
from localbrain.persistence import db
import test_session_sync as sync_fixtures


class RetainedSessionTests(unittest.TestCase):
    def setUp(self):
        fixture = compressed_fixtures.CompressedSessionTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.connection = fixture.connection
        self.root = fixture.sources["personal"][1]

    def scan(self, *, force=False, revision=CODEX_SESSION_REVISION,
             usage=CODEX_USAGE_CONTRACT_VERSION, parser=parse_codex_session):
        source_id, root = self.fixture.sources["personal"]
        return _scan_session_source(
            self.connection, source_id, "Personal", root, parser, usage,
            force=force, provider_kind="codex", session_contract_version=revision,
        )

    def data(self):
        return {table: self.fixture.rows(table) for table in (
            "sessions", "activity_events", "session_pins", "session_reference_evidence",
            "search_index",
        )}

    def file(self, path):
        return self.connection.execute("SELECT * FROM source_files WHERE path=?", (str(path),)).fetchone()

    def test_missing_keeps_readable_detail_usage_references_and_pin_edits_on_return(self):
        path = self.fixture.write(self.root / "original.jsonl")
        self.assertEqual(self.scan(), (1, 0, 0))
        identity = self.connection.execute("SELECT id FROM sessions").fetchone()[0]
        pin_session(self.connection, identity)
        self.connection.execute("UPDATE usage_records SET project_key='path:/synthetic/frozen'")
        data, usage = self.data(), self.fixture.frozen_usage()
        versions = tuple(self.file(path)[key] for key in (
            "session_contract_version", "usage_contract_version", "reference_contract_version"))
        path.unlink()
        for forced in (False, True):
            self.assertEqual(self.scan(force=forced), (0, 0, 0))
            self.assertEqual(self.data(), data)
            self.assertEqual(self.fixture.frozen_usage(), usage)
            self.assertEqual(self.file(path)["presence_state"], "MISSING")
            self.assertEqual(tuple(self.file(path)[key] for key in (
                "session_contract_version", "usage_contract_version", "reference_contract_version")), versions)
            self.assertIsNotNone(session_detail(self.connection, identity))
            self.assertTrue(session_conversation_events(self.connection, identity))
        self.assertTrue(unpin_session(self.connection, identity))
        pin_session(self.connection, identity)
        changed_pin = self.fixture.rows("session_pins")
        self.fixture.write(path)
        self.assertEqual(self.scan(), (1, 0, 0))
        self.assertEqual(self.fixture.rows("session_pins"), changed_pin)
        self.assertEqual(self.fixture.frozen_usage(), usage)
        self.assertEqual(self.file(path)["presence_state"], "PRESENT")
        self.assertEqual(self.scan(), (0, 1, 0))

    def test_unavailable_root_and_failed_file_inspection_mean_unknown_not_missing(self):
        path = self.fixture.write(self.root / "original.jsonl")
        self.scan()
        before = self.data()
        moved = self.root.with_name("unavailable")
        self.root.rename(moved)
        self.assertEqual(self.scan(), (0, 0, 0))
        self.assertEqual(self.file(path)["presence_state"], "UNKNOWN")
        self.assertTrue(self.file(path)["presence_error"])
        self.assertEqual(self.data(), before)
        moved.rename(self.root)
        original_stat = Path.stat
        def denied(candidate, *args, **kwargs):
            if candidate == path:
                raise PermissionError("synthetic permission")
            return original_stat(candidate, *args, **kwargs)
        with patch("localbrain.ingest.sync.sessions._session_paths", return_value=[]), patch.object(Path, "stat", denied):
            self.assertEqual(self.scan(), (0, 0, 0))
        self.assertEqual(self.file(path)["presence_state"], "UNKNOWN")
        self.assertEqual(self.data(), before)

    def test_directory_walk_does_not_silently_skip_unreadable_subdirectories(self):
        def incomplete(root, onerror):
            yield str(root), ["private"], []
            onerror(PermissionError("synthetic directory failure"))
        with patch("localbrain.ingest.sync.sessions.os.walk", incomplete):
            with self.assertRaises(PermissionError):
                list(_session_paths(self.root, None, "codex"))

    def test_present_parse_error_is_independent_from_presence(self):
        path = self.fixture.write(self.root / "original.jsonl")
        self.scan()
        before = self.data()
        def bad_parser(path):
            raise ValueError("synthetic parse failure")
        self.assertEqual(self.scan(force=True, parser=bad_parser), (0, 0, 1))
        self.assertEqual(self.file(path)["presence_state"], "PRESENT")
        self.assertEqual(self.file(path)["status"], "error")
        self.assertEqual(self.file(path)["error"], "synthetic parse failure")
        self.assertEqual(self.data(), before)

    def test_upgrade_repairs_available_input_without_erasing_absent_usage_or_repeating(self):
        absent = self.fixture.write(self.root / "absent.jsonl")
        present = self.fixture.write(self.root / "present.jsonl", self.fixture.records("second-native"))
        self.scan()
        absent_id = self.file(absent)["session_id"]
        self.connection.execute("UPDATE source_files SET session_contract_version=1,usage_contract_version='old'")
        self.connection.execute("UPDATE usage_records SET normalizer_version='old'")
        before = [dict(row) for row in self.connection.execute(
            "SELECT * FROM usage_records WHERE session_id=?", (absent_id,))]
        absent.unlink()
        self.assertEqual(self.scan(), (1, 0, 0))
        self.assertEqual([dict(row) for row in self.connection.execute(
            "SELECT * FROM usage_records WHERE session_id=?", (absent_id,))], before)
        self.assertEqual(self.file(absent)["session_contract_version"], 1)
        self.assertEqual(self.file(absent)["usage_contract_version"], "old")
        self.assertEqual(self.file(present)["session_contract_version"], CODEX_SESSION_REVISION)
        self.assertEqual(self.scan(), (0, 1, 0))

    def test_missing_sibling_preserves_its_usage_and_reference_evidence_during_repair(self):
        first = self.fixture.write(self.root / "part1.jsonl")
        records = self.fixture.records()
        records.insert(1, {"type": "synthetic_padding", "payload": {}})
        records[3]["payload"]["message"] = "Another https://docs.example.test/other"
        self.fixture.write(self.root / "part2.jsonl", records)
        self.scan()
        usage = self.fixture.frozen_usage()
        resources = {r[0] for r in self.connection.execute("SELECT resource_id FROM session_reference_evidence")}
        self.assertEqual(len(usage), 2)
        self.assertEqual(len(resources), 2)
        first.unlink()
        self.connection.execute("UPDATE source_files SET usage_contract_version='old'")
        self.assertEqual(self.scan(), (1, 0, 0))
        self.assertEqual(self.fixture.frozen_usage(), usage)
        self.assertEqual({r[0] for r in self.connection.execute("SELECT resource_id FROM session_reference_evidence")}, resources)

    def test_return_under_new_filename_keeps_native_session_and_frozen_usage_identity(self):
        path = self.fixture.write(self.root / "original.jsonl")
        self.scan()
        identity = self.file(path)["session_id"]
        pin_session(self.connection, identity)
        usage = self.fixture.frozen_usage()
        path.unlink()
        self.scan()
        self.fixture.write(self.root / "returned.jsonl.zst")
        self.assertEqual(self.scan(), (1, 0, 0))
        self.assertEqual(self.connection.execute("SELECT id FROM sessions").fetchall()[0][0], identity)
        self.assertEqual(self.connection.execute("SELECT count(*) FROM sessions").fetchone()[0], 1)
        self.assertEqual(self.connection.execute("SELECT session_id FROM session_pins").fetchone()[0], identity)
        self.assertEqual(self.fixture.frozen_usage(), usage)

    def test_available_sibling_cannot_erase_conversation_from_missing_original(self):
        sibling_records = self.fixture.records()
        sibling_records[2]["payload"]["message"] = "Available sibling"
        self.fixture.write(self.root / "a-sibling.jsonl", sibling_records)
        original_records = self.fixture.records()
        original_records[2]["payload"]["message"] = "Preserve this stored original conversation"
        original = self.fixture.write(self.root / "z-original.jsonl", original_records)
        self.scan()
        identity = self.file(original)["session_id"]
        before = [dict(row) for row in session_conversation_events(self.connection, identity)]
        self.assertIn("Preserve this", before[0]["text"])
        original.unlink()
        for forced in (False, True):
            self.scan(force=forced)
            self.assertEqual([dict(row) for row in session_conversation_events(self.connection, identity)], before)
        self.assertEqual(session_detail(self.connection, identity)["source_presence_state"], "PRESENT")

    def test_presence_enum_is_bounded_and_does_not_change_existing_scan_columns(self):
        path = self.fixture.write(self.root / "original.jsonl")
        self.scan()
        self.assertEqual(self.file(path)["presence_state"], "PRESENT")
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute("UPDATE source_files SET presence_state='error'")

    def test_additive_migration_keeps_existing_content_and_defaults_presence_to_unknown(self):
        schema = (Path(__file__).parents[1] / "src/localbrain/schema.sql").read_text()
        legacy = "\n".join(line for line in schema.splitlines()
                           if not any(column in line for column in (
                               "presence_state", "presence_checked_at", "presence_error")))
        with sqlite3.connect(":memory:") as connection:
            connection.row_factory = sqlite3.Row
            connection.executescript(legacy)
            connection.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'codex','Personal','/synthetic')")
            connection.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title) VALUES (7,1,'native','/synthetic/a.jsonl','Preserve')")
            connection.execute("INSERT INTO session_pins(session_id,pinned_at) VALUES (7,'fixed')")
            connection.execute("INSERT INTO source_files(source_id,session_id,path,size_bytes,mtime_ns,last_scanned_at,status,error,session_contract_version) VALUES (1,7,'/synthetic/a.jsonl',10,20,'fixed','error','keep reason',14)")
            before = dict(connection.execute("SELECT * FROM source_files").fetchone())
            _run_compatible_migrations(connection, include_data_migrations=False)
            row = dict(connection.execute("SELECT * FROM source_files").fetchone())
            self.assertEqual({key:row[key] for key in before}, before)
            self.assertEqual(row["presence_state"], "UNKNOWN")
            self.assertIsNone(row["presence_checked_at"])
            self.assertEqual(connection.execute("SELECT session_id FROM session_pins").fetchone()[0], 7)
            _run_compatible_migrations(connection, include_data_migrations=False)
            self.assertEqual(dict(connection.execute("SELECT * FROM source_files").fetchone()), row)

    def test_availability_reads_do_not_inspect_originals_and_preserve_old_versions(self):
        path = self.fixture.write(self.root / "original.jsonl")
        self.scan()
        identity = self.file(path)["session_id"]
        path.unlink()
        self.scan()
        with patch.object(Path, "stat", side_effect=AssertionError("availability read opened filesystem")):
            row = session_detail(self.connection, identity)
            self.assertEqual(row["source_presence_state"], "MISSING")
            self.assertIsNotNone(row["source_presence_checked_at"])
            self.assertTrue(session_conversation_events(self.connection, identity))

    def test_interrupted_source_preserves_history_and_records_unknown_inspection(self):
        fixture = sync_fixtures.SessionSyncTests()
        settings = fixture._settings(self.fixture.root / "interrupted")
        fixture._write_codex_session(settings.codex_root / "original.jsonl", "native", "Keep conversation")
        with patch.object(db, "settings", settings), patch.object(scanner, "settings", settings):
            scanner.scan_session_sources()
            original_scan = scanner.sessions._scan_session_source
            def interrupted(connection, source_id, *args, **kwargs):
                if source_id == 2:
                    raise InterruptedError("synthetic cancellation")
                return original_scan(connection, source_id, *args, **kwargs)
            with patch.object(scanner.sessions, "_scan_session_source", interrupted):
                with self.assertRaises(InterruptedError):
                    scanner.scan_session_sources()
            with db.connect() as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM sessions").fetchone()[0], 1)
                self.assertEqual(connection.execute("SELECT text FROM activity_events WHERE event_type='message'").fetchone()[0], "Keep conversation")
                self.assertEqual(connection.execute("SELECT presence_state FROM source_files WHERE source_id=2").fetchone()[0], "UNKNOWN")

    def test_missing_legacy_session_without_file_mapping_gets_presence_without_reparse(self):
        for missing_row in (False, True):
            with self.subTest(no_file_row=missing_row):
                path = self.fixture.write(self.root / ('legacy-'+str(missing_row)+'.jsonl'),
                                          self.fixture.records('legacy-'+str(missing_row)))
                self.scan()
                identity = self.file(path)["session_id"]
                if missing_row:
                    self.connection.execute("DELETE FROM source_files WHERE path=?", (str(path),))
                else:
                    self.connection.execute("UPDATE source_files SET session_id=NULL WHERE path=?", (str(path),))
                path.unlink()
                self.scan()
                self.assertEqual(self.file(path)["session_id"], identity)
                self.assertEqual(session_detail(self.connection, identity)["source_presence_state"], "MISSING")
                self.assertTrue(session_conversation_events(self.connection, identity))
                if missing_row:
                    self.assertIsNone(self.file(path)["session_contract_version"])

    def test_claude_missing_original_keeps_conversation_pin_and_usage_on_forced_scan_and_return(self):
        root = self.fixture.root / "claude"
        root.mkdir()
        source_id = self.connection.execute(
            "INSERT INTO sources(provider_kind,name,root_path) VALUES ('claude','Claude',?)", (str(root),)
        ).lastrowid
        records = [
            {"type":"user","uuid":"user-native","sessionId":"claude-native",
             "timestamp":"2026-06-28T01:00:00Z","cwd":"/synthetic/project",
             "message":{"role":"user","content":"Retain Claude conversation"}},
            {"type":"assistant","uuid":"assistant-native","sessionId":"claude-native",
             "timestamp":"2026-06-28T01:00:01Z",
             "message":{"id":"request-native","role":"assistant","model":"claude-sonnet-4-5",
                        "content":[{"type":"text","text":"Stored reply"}],
                        "usage":{"input_tokens":1000,"output_tokens":100}}},
        ]
        path=root/'session.jsonl'
        raw=''.join(json.dumps(row)+'\n' for row in records)
        path.write_text(raw)
        def scan(force=False):
            return _scan_session_source(self.connection,source_id,'Claude',root,
                parse_claude_session,CLAUDE_USAGE_CONTRACT_VERSION,force=force,
                provider_kind='claude',path_filter=scanner._is_claude_session_candidate,
                session_contract_version=CLAUDE_SESSION_REVISION)
        self.assertEqual(scan(),(1,0,0))
        identity=self.file(path)["session_id"]
        pin_session(self.connection,identity)
        before=self.data();usage=self.fixture.frozen_usage()
        self.assertTrue(usage)
        path.unlink()
        self.assertEqual(scan(force=True),(0,0,0))
        self.assertEqual(self.data(),before)
        self.assertEqual(self.fixture.frozen_usage(),usage)
        self.assertEqual(session_detail(self.connection,identity)["source_presence_state"],"MISSING")
        path.write_text(raw)
        self.assertEqual(scan(),(1,0,0))
        self.assertEqual(self.file(path)["session_id"],identity)
        self.assertEqual(self.fixture.frozen_usage(),usage)
        self.assertEqual(self.fixture.rows('session_pins'),before['session_pins'])
