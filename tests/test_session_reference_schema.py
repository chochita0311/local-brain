import sqlite3
import unittest
from pathlib import Path

from localbrain.db import _run_compatible_migrations


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = (ROOT / "src/localbrain/schema.sql").read_text(encoding="utf-8")


class SessionReferenceSchemaTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_SQL)
        self.connection.executescript(
            """
            INSERT INTO sources(id, kind, provider_kind, name, root_path)
            VALUES (1, 'codex', 'codex', 'Codex', '/synthetic/codex');

            INSERT INTO sessions(
                id, source_id, external_id, source_path, title
            ) VALUES (
                10, 1, 'session-10', '/synthetic/session-10.jsonl', 'Synthetic'
            );

            INSERT INTO context_documents(
                id, source_id, path, relative_path, title, body,
                size_bytes, mtime_ns, content_hash
            ) VALUES (
                20, 1, '/synthetic/context/notes.md', 'notes.md', 'Notes', '',
                0, 1, 'document-hash'
            );
            """
        )

    def tearDown(self):
        self.connection.close()

    def _insert_evidence(self, **overrides):
        values = {
            "session_id": 10,
            "source_path": "/synthetic/session-10.jsonl",
            "source_event_id": "event-1",
            "source_line": 1,
            "evidence_ordinal": 1,
            "target_kind": "url",
            "target_key": "url:" + "a" * 64,
            "context_document_id": None,
            "external_resource_id": None,
            "evidence_kind": "user_mention",
            "read_outcome": None,
            "observed_identity": "example.test/path",
            "normalized_url": "https://example.test/path",
            "tool_name": None,
            "tool_call_id": None,
            "observed_at": "2026-08-03T00:00:00+00:00",
            "extractor_version": "session-reference-v1",
            "evidence_key": "b" * 64,
            "first_observed_at": "2026-08-03T00:00:01+00:00",
            "last_observed_at": "2026-08-03T00:00:01+00:00",
        }
        values.update(overrides)
        columns = ", ".join(values)
        placeholders = ", ".join("?" for _ in values)
        return self.connection.execute(
            f"INSERT INTO session_reference_evidence({columns}) "
            f"VALUES ({placeholders})",
            tuple(values.values()),
        ).lastrowid

    def test_fresh_schema_has_owned_tables_foreign_keys_and_indexes(self):
        tables = {
            row[0]
            for row in self.connection.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table'"
            )
        }
        self.assertIn("session_reference_scans", tables)
        self.assertIn("session_reference_evidence", tables)

        foreign_targets = {
            row["table"]
            for row in self.connection.execute(
                "PRAGMA foreign_key_list(session_reference_evidence)"
            )
        }
        self.assertEqual(
            foreign_targets,
            {"sessions", "context_documents", "atlassian_items"},
        )
        indexes = {
            row["name"]
            for row in self.connection.execute(
                "PRAGMA index_list(session_reference_evidence)"
            )
        }
        self.assertTrue(
            {
                "idx_session_reference_evidence_session",
                "idx_session_reference_evidence_document",
                "idx_session_reference_evidence_atlassian",
            }.issubset(indexes)
        )

    def test_scan_state_enforces_complete_partial_and_error_shapes(self):
        self.connection.execute(
            """
            INSERT INTO session_reference_scans(
                session_id, source_fingerprint, extractor_version, status,
                observed_target_count, retained_target_count, scanned_at
            ) VALUES (?, ?, ?, 'ok', 4, 4, ?)
            """,
            (10, "a" * 64, "session-reference-v1", "2026-08-03T00:00:00Z"),
        )
        self.connection.execute("DELETE FROM session_reference_scans")
        self.connection.execute(
            """
            INSERT INTO session_reference_scans(
                session_id, source_fingerprint, extractor_version, status,
                observed_target_count, retained_target_count, scanned_at
            ) VALUES (?, ?, ?, 'partial', 101, 100, ?)
            """,
            (10, "b" * 64, "session-reference-v1", "2026-08-03T00:00:00Z"),
        )
        self.connection.execute("DELETE FROM session_reference_scans")
        self.connection.execute(
            """
            INSERT INTO session_reference_scans(
                session_id, source_fingerprint, extractor_version, status,
                observed_target_count, retained_target_count,
                error_code, error_message, scanned_at
            ) VALUES (?, ?, ?, 'error', 4, 4, 'parse-error', 'bounded', ?)
            """,
            (10, "c" * 64, "session-reference-v1", "2026-08-03T00:00:00Z"),
        )

        invalid_statements = (
            """
            INSERT OR REPLACE INTO session_reference_scans(
                session_id, source_fingerprint, extractor_version, status,
                observed_target_count, retained_target_count, scanned_at
            ) VALUES (10, '{hash}', 'v1', 'ok', 5, 4, 'now')
            """.format(hash="d" * 64),
            """
            INSERT OR REPLACE INTO session_reference_scans(
                session_id, source_fingerprint, extractor_version, status,
                observed_target_count, retained_target_count, scanned_at
            ) VALUES (10, '{hash}', 'v1', 'partial', 101, 99, 'now')
            """.format(hash="e" * 64),
            """
            INSERT OR REPLACE INTO session_reference_scans(
                session_id, source_fingerprint, extractor_version, status,
                observed_target_count, retained_target_count, scanned_at
            ) VALUES (10, '{hash}', 'v1', 'error', 0, 0, 'now')
            """.format(hash="f" * 64),
        )
        for statement in invalid_statements:
            with self.assertRaises(sqlite3.IntegrityError):
                self.connection.execute(statement)

    def test_evidence_enforces_target_and_read_truth_shapes(self):
        self._insert_evidence()
        self._insert_evidence(
            source_event_id="event-2",
            source_line=2,
            target_kind="context_document",
            target_key="document:20",
            context_document_id=20,
            observed_identity="notes.md",
            normalized_url=None,
            evidence_kind="assistant_mention",
            evidence_key="c" * 64,
        )
        self._insert_evidence(
            source_event_id="event-3",
            source_line=3,
            evidence_kind="resource_read",
            read_outcome="failure",
            tool_name="mcp__jira__get_issue",
            tool_call_id="call-3",
            evidence_key="d" * 64,
        )

        invalid_rows = (
            {"context_document_id": 20, "evidence_key": "e" * 64},
            {"read_outcome": "success", "evidence_key": "f" * 64},
            {
                "evidence_kind": "resource_read",
                "read_outcome": "success",
                "tool_name": None,
                "tool_call_id": None,
                "evidence_key": "1" * 64,
            },
        )
        for row in invalid_rows:
            with self.assertRaises(sqlite3.IntegrityError):
                self._insert_evidence(**row)

    def test_session_and_target_deletion_remove_only_derived_evidence(self):
        self.connection.execute(
            """
            INSERT INTO session_reference_scans(
                session_id, source_fingerprint, extractor_version, status,
                observed_target_count, retained_target_count, scanned_at
            ) VALUES (10, ?, 'v1', 'ok', 1, 1, 'now')
            """,
            ("a" * 64,),
        )
        self._insert_evidence(
            target_kind="context_document",
            target_key="document:20",
            context_document_id=20,
            observed_identity="notes.md",
            normalized_url=None,
        )

        self.connection.execute("DELETE FROM context_documents WHERE id = 20")
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM session_reference_evidence"
            ).fetchone()[0],
            0,
        )
        self.assertIsNotNone(
            self.connection.execute("SELECT id FROM sessions WHERE id = 10").fetchone()
        )

        self._insert_evidence(evidence_key="c" * 64)
        self.connection.execute("DELETE FROM sessions WHERE id = 10")
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM session_reference_scans"
            ).fetchone()[0],
            0,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM session_reference_evidence"
            ).fetchone()[0],
            0,
        )

    def test_idempotent_schema_adds_contract_without_changing_existing_session(self):
        self.connection.execute("DROP TABLE session_reference_evidence")
        self.connection.execute("DROP TABLE session_reference_scans")
        before = dict(
            self.connection.execute("SELECT * FROM sessions WHERE id = 10").fetchone()
        )

        self.connection.executescript(SCHEMA_SQL)

        after = dict(
            self.connection.execute("SELECT * FROM sessions WHERE id = 10").fetchone()
        )
        self.assertEqual(after, before)
        self.assertEqual(
            self.connection.execute("PRAGMA foreign_key_check").fetchall(), []
        )

    def test_compatible_startup_adds_source_mapping_and_version_without_rewriting_rows(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        legacy_schema = SCHEMA_SQL.replace(
            "    session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,\n",
            "",
            1,
        ).replace(
            "    reference_contract_version TEXT,\n",
            "",
            1,
        ).replace(
            "    session_contract_version TEXT,\n",
            "",
            1,
        )
        connection.executescript(legacy_schema)
        connection.executescript(
            """
            INSERT INTO sources(id, kind, provider_kind, name, root_path)
            VALUES (1, 'codex', 'codex', 'Codex', '/synthetic');
            INSERT INTO sessions(id, source_id, external_id, source_path, title)
            VALUES (10, 1, 'session-10', '/synthetic/session.jsonl', 'Session');
            INSERT INTO source_files(
                id, source_id, path, size_bytes, mtime_ns,
                last_scanned_at, usage_contract_version
            ) VALUES (
                20, 1, '/synthetic/session.jsonl', 10, 20,
                '2026-08-03T00:00:00Z', 'usage-v1'
            );
            """
        )
        before = dict(connection.execute("SELECT * FROM source_files").fetchone())
        connection.executescript(SCHEMA_SQL)

        _run_compatible_migrations(connection, include_data_migrations=False)
        after = dict(connection.execute("SELECT * FROM source_files").fetchone())

        self.assertEqual(
            {key: after[key] for key in before},
            before,
        )
        self.assertIsNone(after["session_id"])
        self.assertIsNone(after["reference_contract_version"])
        self.assertIsNone(after["session_contract_version"])
        self.assertIn(
            "idx_source_files_session",
            {
                row["name"]
                for row in connection.execute("PRAGMA index_list(source_files)")
            },
        )
        self.assertIn(
            ("session_id", "sessions", "id", "SET NULL"),
            {
                (row["from"], row["table"], row["to"], row["on_delete"])
                for row in connection.execute(
                    "PRAGMA foreign_key_list(source_files)"
                )
            },
        )
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        connection.close()


if __name__ == "__main__":
    unittest.main()
