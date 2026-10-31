"""Synthetic contracts for independent schedules and incremental Context reads."""

import json
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from localbrain.ingest.sync import contexts, storage
from localbrain.persistence import db
from localbrain.foundation.config import Settings
from localbrain.local_context.service import add_context_root, add_apple_notes_source
from localbrain.sources.context_sync import ContextSyncService
from localbrain.ingest import scanner
from localbrain.foundation.operations import operation_lock
from localbrain.foundation.preferences import PreferencesError, read_preferences, save_preferences
from localbrain.sources.session_sync import SessionSyncService


class ContextSyncTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="localbrain-context-sync-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        data = self.root / "data"
        data.mkdir()
        self.config = Settings(data, data / "localbrain.db", self.root / "unused",
                               self.root / "claude", self.root / "codex", 20, "UTC",
                               session_sources_path=data / "session-sources.toml",
                               cache_dir=self.root / "cache")
        for module in (db, scanner):
            mock = patch.object(module, "settings", self.config)
            mock.start()
            self.addCleanup(mock.stop)
        db.init_db()
        self.docs = self.root / "documents"
        self.docs.mkdir()
        self.document = self.docs / "example.md"
        self.document.write_text("# Example\nInitial synthetic content\n")
        with db.transaction() as connection:
            self.root_id = add_context_root(connection, str(self.docs))

    def save(self, **changes):
        return save_preferences(changes, read_preferences(self.config)["revision"], self.config)

    def test_old_file_preserved_and_context_values_are_independent(self):
        path = self.config.data_dir / "settings.toml"
        old = 'schema_version = 1\nsession_sync_enabled = false\nsession_sync_minutes = 45\nfuture_key = "keep"\n'
        path.write_text(old)
        state = read_preferences(self.config)
        self.assertEqual(path.read_text(), old)
        self.assertTrue(state["saved"]["context_sync_enabled"])
        self.assertEqual(state["saved"]["context_sync_minutes"], 30)
        self.assertEqual(state["source"]["context_sync_minutes"], "default")
        for minutes in (10, 20, 30, 60, 45, 1440):
            self.save(context_sync_minutes=minutes)
            self.save(context_sync_enabled=False)
            state = self.save(context_sync_enabled=True)
            self.assertEqual(state["saved"]["context_sync_minutes"], minutes)
            self.assertEqual(state["saved"]["session_sync_minutes"], 45)
            self.assertFalse(state["saved"]["session_sync_enabled"])
            self.assertEqual(state["raw"]["future_key"], "keep")
        before = path.read_bytes()
        for value in (True, None, "30", 9, 1441, 20.5):
            with self.assertRaises(PreferencesError):
                self.save(context_sync_minutes=value)
            self.assertEqual(path.read_bytes(), before)
        with self.assertRaises(PreferencesError):
            self.save(context_sync_enabled=1)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_domain_clocks_and_other_backend_completion_are_independent(self):
        self.save(session_sync_minutes=10, context_sync_minutes=30)
        sessions, contexts = Mock(return_value={"outcome": "complete"}), Mock(return_value={"outcome": "complete"})
        session = SessionSyncService(self.config, sessions)
        context = ContextSyncService(self.config, contexts)
        session._write({"completed_at": 1000})
        context._write({"completed_at": 1000})
        with patch("localbrain.sources.sync.time.time", return_value=1600):
            session._collect(False)
            context._collect(False)
            self.assertEqual(sessions.call_count, 1)
            self.assertEqual(contexts.call_count, 0)
            self.assertEqual(context.status()["next_at"], 2800)
        with patch("localbrain.sources.sync.time.time", return_value=2800):
            context._collect(False)
            ContextSyncService(self.config, contexts)._collect(False)
            self.assertEqual(contexts.call_count, 1)
            self.assertEqual(context.status()["next_at"], 4600)
        self.save(context_sync_enabled=False)
        with patch("localbrain.sources.sync.time.time", return_value=10000):
            context._collect(False)
            self.assertEqual(contexts.call_count, 1)
            self.assertIsNone(context.status()["next_at"])
        self.assertEqual(json.loads((self.config.data_dir / "session-sync-state.json").read_text())["completed_at"], 1600)

    def test_busy_context_writer_does_not_discard_manual_session_request(self):
        held, release = threading.Event(), threading.Event()
        def owner():
            with operation_lock(self.config, "context-sync"):
                held.set()
                release.wait(5)
        thread = threading.Thread(target=owner)
        thread.start()
        self.assertTrue(held.wait(2))
        service = SessionSyncService(self.config, Mock(return_value={"outcome": "complete"}))
        service._request.set()
        try:
            with patch.object(service, "_has_sources", return_value=True), patch.object(service._wake, "wait", side_effect=lambda _: service._stop.set()):
                service._loop()
            self.assertTrue(service._request.is_set())
            service.scanner.assert_not_called()
        finally:
            release.set()
            thread.join(2)
        service._stop.clear()
        service._collect(True)
        self.assertFalse(service._request.is_set())
        self.assertEqual(service.scanner.call_count, 1)

    def test_context_scan_is_incremental_and_never_scans_sessions(self):
        with patch.object(scanner, "_scan_session_sources", side_effect=AssertionError("Session scan forbidden")):
            first = scanner.scan_context_sources()
            self.assertEqual(first["summary"]["imported"], 1)
            with db.connect() as connection:
                identity = connection.execute("SELECT id FROM context_documents").fetchone()[0]
            self.assertEqual(scanner.scan_context_sources()["summary"]["imported"], 0)
            self.document.write_text("# Example\nChanged synthetic content with more text\n")
            self.assertEqual(scanner.scan_context_sources()["summary"]["imported"], 1)
            with db.connect() as connection:
                row = connection.execute("SELECT id, body FROM context_documents").fetchone()
                self.assertEqual(row["id"], identity)
                self.assertIn("Changed", row["body"])
            self.document.unlink()
            scanner.scan_context_sources()
            with db.connect() as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM search_index WHERE entity_type='document'").fetchone()[0], 0)
            self.assertFalse(self.document.exists())

    def test_cancel_rolls_back_partial_source_and_retains_originals(self):
        second = self.docs / "second.md"
        second.write_text("# Second\nSynthetic\n")
        originals = [p.read_bytes() for p in (self.document, second)]
        stop = threading.Event()
        record = storage._record_source_file
        def processed(*args, **kwargs):
            result = record(*args, **kwargs)
            stop.set()
            return result
        with patch.object(storage, "_record_source_file", side_effect=processed):
            with self.assertRaises(InterruptedError):
                scanner.scan_context_sources(cancelled=stop.is_set)
        with db.connect() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM context_documents").fetchone()[0], 0)
        self.assertEqual([p.read_bytes() for p in (self.document, second)], originals)
        self.assertEqual(scanner.scan_context_sources()["summary"]["imported"], 2)

    def test_disabled_and_missing_sources_do_not_hide_partial_failure(self):
        with db.transaction() as connection:
            connection.execute("UPDATE context_roots SET enabled=0 WHERE id=?", (self.root_id,))
        service = ContextSyncService(self.config, scanner.scan_context_sources)
        self.assertFalse(service._has_sources())
        self.assertIsNone(service.status()["next_at"])
        with db.transaction() as connection:
            connection.execute("UPDATE context_roots SET enabled=1 WHERE id=?", (self.root_id,))
            missing = self.root / "missing"
            missing.mkdir()
            missing_id = add_context_root(connection, str(missing))
        missing.rmdir()
        report = scanner.scan_context_sources()
        self.assertNotEqual(report["outcome"], "complete")
        self.assertEqual(report["summary"]["imported"], 1)
        with db.connect() as connection:
            self.assertEqual(connection.execute("SELECT status FROM context_roots WHERE id=?", (missing_id,)).fetchone()[0], "missing")

    def test_notes_process_is_canceled_without_real_notes_access(self):
        with db.transaction() as connection:
            add_apple_notes_source(connection)
        stop = threading.Event()
        process = Mock()
        def pending(**kwargs):
            stop.set()
            process.communicate.side_effect = None
            process.communicate.return_value = ("", "")
            raise subprocess.TimeoutExpired("synthetic-reader", .5)
        process.communicate.side_effect = pending
        context = Mock()
        context.__enter__ = Mock(return_value=process)
        context.__exit__ = Mock(return_value=False)
        with patch.object(contexts.subprocess, "Popen", return_value=context):
            with self.assertRaises(InterruptedError):
                scanner.scan_context_sources(cancelled=stop.is_set)
        process.kill.assert_called_once()

    def test_notes_timeout_reports_total_limit_and_stops_reader(self):
        process = Mock()
        process.communicate.side_effect = [subprocess.TimeoutExpired("synthetic-reader", .5), ("", "")]
        context = Mock()
        context.__enter__ = Mock(return_value=process)
        context.__exit__ = Mock(return_value=False)
        with patch.object(contexts.subprocess, "Popen", return_value=context), patch.object(contexts.time, "monotonic", side_effect=[0, 120]):
            with self.assertRaisesRegex(TimeoutError, "120 seconds"):
                contexts._scan_apple_notes(None, 1, None)
        process.kill.assert_called_once()


if __name__ == "__main__":
    unittest.main()
