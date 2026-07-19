import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from localbrain.db import _run_compatible_migrations


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "src/localbrain/schema.sql"
MANIFEST = ROOT / "src/localbrain/schema-presentation.json"


def fresh_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    _run_compatible_migrations(connection, include_data_migrations=False)
    return connection


def index_columns(connection: sqlite3.Connection, table: str, index: str) -> list[str]:
    return [
        row["name"]
        for row in connection.execute(f"PRAGMA index_xinfo('{index}')")
        if row["key"]
    ]


class SchemaCleanupAuditTests(unittest.TestCase):
    def test_audit_checker_and_resolved_ledger_are_current(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/check-schema-cleanup-audit.py"),
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("328 objects", result.stdout)
        self.assertIn("keep=273, change=0, remove=0, defer=55", result.stdout)

    def test_manifest_inventory_matches_audit_boundary(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["tables"]), 21)
        self.assertEqual(sum(len(table["columns"]) for table in manifest["tables"]), 244)
        self.assertEqual(sum(len(table["indexes"]) for table in manifest["tables"]), 20)
        self.assertEqual(len(manifest["relationships"]["physical"]), 20)
        self.assertEqual(len(manifest["relationships"]["application"]), 23)

    def test_audit_checker_rejects_coverage_and_safety_drift(self):
        source = json.loads(
            (ROOT / "docs/plans/evaluation/audit-0029-schema-decisions.json").read_text(
                encoding="utf-8"
            )
        )
        mutations = {
            "missing table decision": lambda value: value["table_decisions"].pop(
                "sources"
            ),
            "wrong object count": lambda value: value["manifest"]["expected"].update(
                {"columns": 243}
            ),
            "incomplete candidate safety": lambda value: (
                value["table_decisions"]["maintenance_runs"].update(
                    {
                        "decision": "change",
                        "candidate": "incomplete-candidate",
                    }
                ),
                value["candidate_groups"].update(
                    {
                        "incomplete-candidate": {
                            "disposition": "change",
                            "risk": "high",
                        }
                    }
                ),
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(drift=label), tempfile.TemporaryDirectory() as temporary:
                value = json.loads(json.dumps(source))
                mutate(value)
                decision_path = Path(temporary) / "decisions.json"
                ledger_path = Path(temporary) / "ledger.md"
                decision_path.write_text(json.dumps(value), encoding="utf-8")
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts/check-schema-cleanup-audit.py"),
                        "--decisions",
                        str(decision_path),
                        "--ledger",
                        str(ledger_path),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("schema cleanup audit failed", result.stderr)

    def test_removed_indexes_leave_required_unique_autoindex_coverage(self):
        connection = fresh_connection()
        cases = (
            (
                "activity_events",
                "idx_events_session_sequence",
                ["session_id", "sequence"],
            ),
            ("local_resources", "idx_local_resources_path", ["path"]),
            (
                "checkpoint_resource_refs",
                "idx_checkpoint_resource_refs",
                ["checkpoint_id", "thread_id"],
            ),
        )
        for table, explicit_index, prefix in cases:
            with self.subTest(table=table):
                indexes = connection.execute(f"PRAGMA index_list('{table}')").fetchall()
                self.assertNotIn(explicit_index, {row["name"] for row in indexes})
                unique_autoindexes = [
                    row["name"] for row in indexes if row["origin"] == "u"
                ]
                self.assertTrue(
                    any(
                        index_columns(connection, table, index)[: len(prefix)] == prefix
                        for index in unique_autoindexes
                    )
                )

    def test_added_indexes_support_current_query_prefixes(self):
        connection = fresh_connection()
        additions = (
            (
                "idx_checkpoints_workstream_version",
                "SELECT * FROM checkpoints WHERE workstream_id = ? ORDER BY version DESC LIMIT 1",
            ),
            (
                "idx_documents_source",
                "SELECT * FROM context_documents WHERE source_id = ?",
            ),
            (
                "idx_documents_workspace",
                "SELECT * FROM context_documents WHERE workspace_id = ? ORDER BY mtime_ns DESC",
            ),
        )
        for name, query in additions:
            with self.subTest(index=name):
                plan = " ".join(
                    row["detail"]
                    for row in connection.execute("EXPLAIN QUERY PLAN " + query, (1,))
                )
                self.assertIn(name, plan)

    def test_schema_only_additions_leave_data_repairs_disabled(self):
        connection = fresh_connection()
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("DROP INDEX idx_maintenance_runs_workstream")
        connection.execute("DROP INDEX idx_maintenance_runs_status")
        for table, column in (
            ("usage_records", "attribution_basis"),
            ("usage_records", "attributed_at"),
            ("checkpoints", "updated_at"),
            ("maintenance_runs", "workstream_id"),
            ("maintenance_runs", "updated_at"),
        ):
            connection.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
        _run_compatible_migrations(connection, include_data_migrations=False)

        usage_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usage_records'"
        ).fetchone()["sql"]
        self.assertNotIn("attribution_basis IN", usage_sql)
        usage_columns = {
            row["name"]: row for row in connection.execute("PRAGMA table_info('usage_records')")
        }
        self.assertEqual(usage_columns["attributed_at"]["notnull"], 0)

        checkpoint_columns = {
            row["name"]: row for row in connection.execute("PRAGMA table_info('checkpoints')")
        }
        self.assertEqual(checkpoint_columns["updated_at"]["notnull"], 0)
        self.assertIsNone(checkpoint_columns["updated_at"]["dflt_value"])

        maintenance_columns = {
            row["name"]: row
            for row in connection.execute("PRAGMA table_info('maintenance_runs')")
        }
        self.assertEqual(maintenance_columns["updated_at"]["notnull"], 0)
        self.assertIsNone(maintenance_columns["updated_at"]["dflt_value"])
        workstream_foreign_keys = [
            row
            for row in connection.execute("PRAGMA foreign_key_list('maintenance_runs')")
            if row["from"] == "workstream_id"
        ]
        self.assertEqual(workstream_foreign_keys, [])


if __name__ == "__main__":
    unittest.main()
