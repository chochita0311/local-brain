import sqlite3
import tempfile
import unittest
from pathlib import Path

from localbrain.ingest.common import ParsedEvent, ParsedSession
from localbrain.ingest.scanner import _store_session, _upsert_source


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
            "INSERT INTO sources(kind, provider_kind, name, root_path) "
            "VALUES ('codex', 'codex', 'Codex', '/tmp')"
        )
        self.source_id = self.connection.execute(
            "SELECT id FROM sources WHERE kind = 'codex'"
        ).fetchone()["id"]

    def tearDown(self):
        self.connection.close()
        self.path.unlink(missing_ok=True)

    def test_source_key_is_stable_and_cannot_change_provider(self):
        source_id = _upsert_source(
            self.connection,
            "codex-company",
            "codex",
            "Codex Company",
            Path("/tmp/codex-company"),
        )
        updated_id = _upsert_source(
            self.connection,
            "codex-company",
            "codex",
            "Company Codex",
            Path("/tmp/company-codex"),
        )
        self.assertEqual(source_id, updated_id)
        row = self.connection.execute(
            "SELECT provider_kind, name, root_path FROM sources WHERE id = ?",
            (source_id,),
        ).fetchone()
        self.assertEqual(row["provider_kind"], "codex")
        self.assertEqual(row["name"], "Company Codex")
        self.assertEqual(row["root_path"], "/tmp/company-codex")

        with self.assertRaisesRegex(ValueError, "already bound to provider 'codex'"):
            _upsert_source(
                self.connection,
                "codex-company",
                "claude",
                "Wrong Provider",
                Path("/tmp/wrong-provider"),
            )
        unchanged = self.connection.execute(
            "SELECT provider_kind, name, root_path FROM sources WHERE id = ?",
            (source_id,),
        ).fetchone()
        self.assertEqual(dict(unchanged), dict(row))

    def test_same_external_id_is_isolated_by_source_key(self):
        company_source_id = _upsert_source(
            self.connection,
            "codex-company",
            "codex",
            "Codex Company",
            Path("/tmp/codex-company"),
        )

        def parsed(source_path: str) -> ParsedSession:
            return ParsedSession(
                external_id="shared-session-id",
                source_path=source_path,
                cwd_raw="/tmp",
                git_branch=None,
                title="Shared identity",
                started_at="2026-08-02T00:00:00Z",
                ended_at="2026-08-02T00:01:00Z",
                last_event_at="2026-08-02T00:01:00Z",
                events=[],
            )

        _store_session(
            self.connection,
            self.source_id,
            "codex",
            parsed("/tmp/codex/shared.jsonl"),
            provider_kind="codex",
        )
        _store_session(
            self.connection,
            company_source_id,
            "codex-company",
            parsed("/tmp/codex-company/shared.jsonl"),
            provider_kind="codex",
        )
        rows = self.connection.execute(
            """
            SELECT sources.kind, sources.provider_kind, sessions.external_id
            FROM sessions
            JOIN sources ON sources.id = sessions.source_id
            WHERE sessions.external_id = 'shared-session-id'
            ORDER BY sources.kind
            """
        ).fetchall()
        self.assertEqual(
            [dict(row) for row in rows],
            [
                {
                    "kind": "codex",
                    "provider_kind": "codex",
                    "external_id": "shared-session-id",
                },
                {
                    "kind": "codex-company",
                    "provider_kind": "codex",
                    "external_id": "shared-session-id",
                },
            ],
        )

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
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM maintenance_runs").fetchone()[0],
            0,
        )
        self.assertIsNone(session["maintenance_run_id"])

    def test_registered_marker_cannot_link_two_sessions_to_one_run(self):
        run_id = "lb-123456789abc"
        self.connection.execute(
            "INSERT INTO maintenance_runs(id, status) VALUES (?, 'prepared')", (run_id,)
        )

        def marker_session(external_id: str) -> ParsedSession:
            return ParsedSession(
                external_id=external_id,
                source_path="/tmp/{}.jsonl".format(external_id),
                cwd_raw="/tmp",
                git_branch=None,
                title="LocalBrain maintenance",
                started_at="2026-07-19T00:00:00Z",
                ended_at="2026-07-19T00:01:00Z",
                last_event_at="2026-07-19T00:01:00Z",
                events=[],
                session_class="maintenance",
                index_policy="metadata_only",
                maintenance_run_id=run_id,
            )

        _store_session(
            self.connection,
            self.source_id,
            "codex",
            marker_session("maintenance-one"),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            _store_session(
                self.connection,
                self.source_id,
                "codex",
                marker_session("maintenance-two"),
            )
