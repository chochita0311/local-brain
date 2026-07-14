import sqlite3
import tempfile
import unittest
from pathlib import Path

from localbrain.ingest.common import ParsedEvent, ParsedSession
from localbrain.ingest.scanner import _store_session


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class IngestPolicyTests(unittest.TestCase):
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
        self.source_id = self.connection.execute(
            "SELECT id FROM sources WHERE kind = 'codex'"
        ).fetchone()["id"]

    def tearDown(self):
        self.connection.close()
        self.path.unlink(missing_ok=True)

    def test_maintenance_session_keeps_metadata_without_events_or_search(self):
        event = ParsedEvent(
            event_id="maintenance-event",
            sequence=10,
            source_line=1,
            event_type="message",
            role="user",
            text="maintenance content",
        )
        parsed = ParsedSession(
            external_id="maintenance-session",
            source_path="/tmp/maintenance.jsonl",
            cwd_raw="/tmp",
            git_branch=None,
            title="LocalBrain maintenance",
            started_at="2026-07-13T02:00:00Z",
            ended_at="2026-07-13T02:01:00Z",
            last_event_at="2026-07-13T02:01:00Z",
            events=[event],
            session_class="maintenance",
            index_policy="metadata_only",
            maintenance_run_id="lb-123456789abc",
        )
        _store_session(self.connection, self.source_id, "codex", parsed)
        session = self.connection.execute("SELECT * FROM sessions").fetchone()
        self.assertEqual(session["session_class"], "maintenance")
        self.assertEqual(session["event_count"], 0)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM activity_events").fetchone()[0],
            0,
        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM search_index").fetchone()[0],
            0,
        )
