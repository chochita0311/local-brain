import sqlite3
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path
from unittest.mock import patch

from localbrain.config import Settings
from localbrain.db import (
    INDEX_POLICY_CHECK_PATTERN,
    MAINTENANCE_SESSION_SHAPE_CHECK_PATTERN,
    SESSION_CLASS_CHECK_PATTERN,
    USAGE_ATTRIBUTION_CHECK_PATTERN,
    _maintenance_session_contract_backup_path,
    _maintenance_session_contract_exists,
    _maintenance_workstream_fk_backup_path,
    _maintenance_workstream_fk_exists,
    _migrate_legacy_usage_table_name,
    _migrate_schema_indexes,
    _repair_maintenance_session_contract,
    _repair_maintenance_workstream_fk,
    _run_compatible_migrations,
    _usage_attribution_backup_path,
    init_db,
)
from localbrain.ingest.common import ParsedEvent


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


def schema_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return connection


def legacy_session_schema() -> str:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    current = """    session_class TEXT NOT NULL DEFAULT 'work'
        CHECK(session_class IN ('work', 'maintenance')),
    session_role TEXT NOT NULL DEFAULT 'primary'
        CHECK(session_role IN ('primary', 'subsession')),
    parent_external_id TEXT,
    parent_session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    index_policy TEXT NOT NULL DEFAULT 'full'
        CHECK(index_policy IN ('full', 'metadata_only')),
    maintenance_run_id TEXT UNIQUE
        REFERENCES maintenance_runs(id) ON DELETE SET NULL,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(
        maintenance_run_id IS NULL
        OR (
            session_class = 'maintenance'
            AND session_role = 'primary'
            AND index_policy = 'metadata_only'
        )
    ),
"""
    legacy = """    session_class TEXT NOT NULL DEFAULT 'work',
    session_role TEXT NOT NULL DEFAULT 'primary'
        CHECK(session_role IN ('primary', 'subsession')),
    parent_external_id TEXT,
    parent_session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    index_policy TEXT NOT NULL DEFAULT 'full',
    maintenance_run_id TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
"""
    if current not in schema:
        raise AssertionError("Session schema fixture no longer matches canonical DDL")
    return schema.replace(current, legacy, 1)


def legacy_session_connection(path: str = ":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(legacy_session_schema())
    return connection


def legacy_maintenance_run_schema() -> str:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    current = """CREATE TABLE IF NOT EXISTS maintenance_runs (
    id TEXT PRIMARY KEY,
    workstream_id INTEGER REFERENCES workstreams(id) ON DELETE SET NULL,
    task_type TEXT,
    runner TEXT NOT NULL DEFAULT 'claude',
    cwd TEXT,
    status TEXT NOT NULL DEFAULT 'prepared',
    pid INTEGER,
    started_at TEXT,
    completed_at TEXT,
    source_snapshot_json TEXT,
    manifest_path TEXT,
    prompt_path TEXT,
    stream_path TEXT,
    result_path TEXT,
    stderr_path TEXT,
    structured_result_json TEXT,
    suggestions_created INTEGER NOT NULL DEFAULT 0,
    refresh_suggestions INTEGER NOT NULL DEFAULT 0,
    mcp_call_budget INTEGER NOT NULL DEFAULT 20,
    mcp_calls_used INTEGER NOT NULL DEFAULT 0,
    mcp_tool_calls_json TEXT,
    mcp_budget_exceeded INTEGER NOT NULL DEFAULT 0,
    summary TEXT,
    error TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);"""
    legacy = """CREATE TABLE IF NOT EXISTS maintenance_runs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'prepared',
    started_at TEXT,
    completed_at TEXT,
    source_snapshot_json TEXT,
    summary TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);"""
    if current not in schema:
        raise AssertionError("Maintenance Run fixture no longer matches canonical DDL")
    return schema.replace(current, legacy, 1)


def legacy_maintenance_run_connection(path: str = ":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(legacy_maintenance_run_schema())
    return connection


def index_shape(connection: sqlite3.Connection, index: str):
    return [
        (row["name"], bool(row["desc"]))
        for row in connection.execute(f'PRAGMA index_xinfo("{index}")')
        if row["key"] and row["name"] is not None
    ]


def make_legacy_usage_table(
    connection: sqlite3.Connection, *, nullable_basis: bool = False
) -> None:
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("ALTER TABLE usage_records DROP COLUMN attribution_basis")
    connection.execute("ALTER TABLE usage_records DROP COLUMN attributed_at")
    connection.execute(
        "ALTER TABLE usage_records ADD COLUMN attribution_basis "
        + (
            "TEXT DEFAULT 'unassigned'"
            if nullable_basis
            else "TEXT NOT NULL DEFAULT 'unassigned'"
        )
    )
    connection.execute("ALTER TABLE usage_records ADD COLUMN attributed_at TEXT")
    connection.execute("PRAGMA foreign_keys = ON")


def insert_usage_record(
    connection: sqlite3.Connection,
    *,
    basis: str = "git_root",
    attributed_at: str = "2026-07-19T00:00:03+00:00",
) -> None:
    connection.executescript(
        """
        INSERT INTO sources(kind, name, root_path)
            VALUES ('codex', 'Codex', '/synthetic/codex');
        INSERT INTO sessions(source_id, external_id, source_path, title)
            VALUES (1, 'session-1', '/synthetic/session.jsonl', 'Synthetic');
        INSERT INTO usage_price_snapshots(
            id, label, source_ref, calculator_version, created_at
        ) VALUES (
            'price-1', 'Synthetic', 'synthetic', 'calculator-v1',
            '2026-07-19T00:00:00+00:00'
        );
        """
    )
    connection.execute(
        """
        INSERT INTO usage_records(
            id, source_id, session_id, source_record_id, source_line,
            occurred_at, raw_model, model_name, input_tokens, output_tokens,
            cache_write_tokens, cache_read_tokens, reasoning_tokens,
            source_total_tokens, total_tokens, total_semantics,
            aggregation_scope, capability_state, capability_json,
            calculation_state, estimated_cost_usd, price_snapshot_id,
            calculator_version, normalizer_version, calculated_at,
            workspace_id_snapshot, project_key, project_name_snapshot,
            project_path_snapshot, project_git_root_snapshot, imported_at,
            attribution_basis, attributed_at
        ) VALUES (
            'record-1', 1, 1, 'record-1', 7,
            '2026-07-19T00:00:00+00:00', 'raw-model', 'model', 10, 5,
            2, 3, 1, 21, 21, 'direct-total',
            'direct', 'complete', '{"contract":"synthetic"}',
            'priced', '0.000100000000', 'price-1',
            'calculator-v1', 'normalizer-v1', '2026-07-19T00:00:01+00:00',
            NULL, 'project:synthetic', 'Synthetic Project',
            '/synthetic/project', '/synthetic/project',
            '2026-07-19T00:00:02+00:00', ?, ?
        )
        """,
        (basis, attributed_at),
    )


def rename_usage_table_to_legacy(connection: sqlite3.Connection) -> None:
    for index in (
        "idx_usage_records_session_time",
        "idx_usage_records_source_time",
        "idx_usage_records_model_time",
    ):
        connection.execute("DROP INDEX {}".format(index))
    connection.execute("ALTER TABLE usage_records RENAME TO usage_facts")
    connection.executescript(
        """
        CREATE INDEX idx_usage_facts_session_time
            ON usage_facts(session_id, occurred_at);
        CREATE INDEX idx_usage_facts_source_time
            ON usage_facts(source_id, occurred_at);
        CREATE INDEX idx_usage_facts_model_time
            ON usage_facts(model_name, occurred_at);
        """
    )


class MaintenanceSessionContractMigrationTests(unittest.TestCase):
    def test_fresh_contract_enforces_values_relation_cardinality_and_shape(self):
        connection = schema_connection()
        connection.execute(
            "INSERT INTO sources(kind, name, root_path) "
            "VALUES ('claude', 'Claude', '/synthetic/claude')"
        )
        connection.execute(
            "INSERT INTO maintenance_runs(id, status) VALUES ('lb-111111111111', 'prepared')"
        )
        connection.execute(
            "INSERT INTO maintenance_runs(id, status) VALUES ('lb-222222222222', 'prepared')"
        )
        table_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'sessions'"
        ).fetchone()[0]
        self.assertRegex(table_sql, SESSION_CLASS_CHECK_PATTERN)
        self.assertRegex(table_sql, INDEX_POLICY_CHECK_PATTERN)
        self.assertRegex(table_sql, MAINTENANCE_SESSION_SHAPE_CHECK_PATTERN)
        self.assertTrue(_maintenance_session_contract_exists(connection))

        for column, value in (
            ("session_class", "unknown"),
            ("index_policy", "unknown"),
        ):
            with self.subTest(column=column), self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO sessions("
                    "source_id, external_id, source_path, title, {}"
                    ") VALUES (1, ?, '/synthetic/invalid.jsonl', 'Invalid', ?)".format(
                        column
                    ),
                    ("invalid-{}".format(column), value),
                )

        connection.execute(
            """
            INSERT INTO sessions(
                source_id, external_id, source_path, title, session_class,
                session_role, index_policy, maintenance_run_id
            ) VALUES (
                1, 'maintenance-1', '/synthetic/run.jsonl', 'Run',
                'maintenance', 'primary', 'metadata_only', 'lb-111111111111'
            )
            """
        )
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO sessions(
                    source_id, external_id, source_path, title, session_class,
                    session_role, index_policy, maintenance_run_id
                ) VALUES (
                    1, 'maintenance-2', '/synthetic/run-2.jsonl', 'Duplicate',
                    'maintenance', 'primary', 'metadata_only', 'lb-111111111111'
                )
                """
            )
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO sessions(
                    source_id, external_id, source_path, title, session_class,
                    session_role, index_policy, maintenance_run_id
                ) VALUES (
                    1, 'bad-shape', '/synthetic/bad-shape.jsonl', 'Bad shape',
                    'work', 'primary', 'full', 'lb-222222222222'
                )
                """
            )
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO sessions(
                    source_id, external_id, source_path, title, session_class,
                    session_role, index_policy, maintenance_run_id
                ) VALUES (
                    1, 'orphan', '/synthetic/orphan.jsonl', 'Orphan',
                    'maintenance', 'primary', 'metadata_only', 'lb-333333333333'
                )
                """
            )
        connection.close()


class MaintenanceWorkstreamFKMigrationTests(unittest.TestCase):
    def _complete_legacy_connection(self) -> sqlite3.Connection:
        connection = legacy_maintenance_run_connection()
        _run_compatible_migrations(connection, include_data_migrations=False)
        self.assertFalse(_maintenance_workstream_fk_exists(connection))
        return connection

    def test_fresh_contract_sets_only_workstream_association_to_null(self):
        connection = schema_connection()
        self.addCleanup(connection.close)
        self.assertTrue(_maintenance_workstream_fk_exists(connection))
        connection.execute("INSERT INTO workstreams(id, name) VALUES (1, 'Owner')")
        connection.execute(
            "INSERT INTO maintenance_runs(id, workstream_id, status) "
            "VALUES ('lb-111111111111', 1, 'completed')"
        )
        connection.execute("DELETE FROM workstreams WHERE id = 1")
        row = connection.execute(
            "SELECT id, workstream_id, status FROM maintenance_runs"
        ).fetchone()
        self.assertEqual(tuple(row), ("lb-111111111111", None, "completed"))

    def test_compatible_repair_preserves_runs_and_dependent_references(self):
        connection = self._complete_legacy_connection()
        self.addCleanup(connection.close)
        connection.execute("INSERT INTO workstreams(id, name) VALUES (1, 'Owner')")
        connection.execute(
            """
            INSERT INTO maintenance_runs(
                id, workstream_id, task_type, runner, cwd, status, pid,
                started_at, completed_at, source_snapshot_json, manifest_path,
                prompt_path, stream_path, result_path, stderr_path,
                structured_result_json, suggestions_created,
                refresh_suggestions, mcp_call_budget, mcp_calls_used,
                mcp_tool_calls_json, mcp_budget_exceeded, summary, error,
                updated_at, created_at
            ) VALUES (
                'lb-222222222222', 1, 'organize_resources', 'claude',
                '/synthetic', 'completed', 42, 'start', 'end', '{"source":1}',
                '/manifest', '/prompt', '/stream', '/result', '/stderr',
                '{"result":1}', 2, 1, 20, 3, '["mcp"]', 0,
                'summary', NULL, NULL, 'created'
            )
            """
        )
        connection.execute(
            "INSERT INTO maintenance_runs(id, workstream_id, status) "
            "VALUES ('lb-222222222223', NULL, 'prepared')"
        )
        connection.execute(
            "INSERT INTO sources(kind, name, root_path) "
            "VALUES ('claude', 'Claude', '/synthetic')"
        )
        connection.execute(
            """
            INSERT INTO sessions(
                source_id, external_id, source_path, title, session_class,
                session_role, index_policy, maintenance_run_id
            ) VALUES (
                1, 'native-maintenance', '/synthetic/session.jsonl', 'Native',
                'maintenance', 'primary', 'metadata_only', 'lb-222222222222'
            )
            """
        )
        connection.execute(
            """
            INSERT INTO suggestions(
                suggestion_type, target_type, target_id, title, fingerprint,
                origin_run_id, status
            ) VALUES (
                'checkpoint_draft', 'workstream', 1, 'Draft', 'fingerprint',
                'lb-222222222222', 'pending'
            )
            """
        )
        before_rows = [
            tuple(row) for row in connection.execute("SELECT * FROM maintenance_runs")
        ]
        before_info = [
            tuple(row)
            for row in connection.execute("PRAGMA table_info(maintenance_runs)")
        ]

        self.assertTrue(_repair_maintenance_workstream_fk(connection))

        self.assertEqual(
            [tuple(row) for row in connection.execute("SELECT * FROM maintenance_runs")],
            before_rows,
        )
        self.assertEqual(
            [tuple(row) for row in connection.execute("PRAGMA table_info(maintenance_runs)")],
            before_info,
        )
        self.assertTrue(_maintenance_workstream_fk_exists(connection))
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(
            connection.execute(
                "SELECT maintenance_run_id FROM sessions"
            ).fetchone()[0],
            "lb-222222222222",
        )
        self.assertEqual(
            connection.execute("SELECT origin_run_id FROM suggestions").fetchone()[0],
            "lb-222222222222",
        )
        self.assertFalse(_repair_maintenance_workstream_fk(connection))

        connection.execute("DELETE FROM workstreams WHERE id = 1")
        run = connection.execute(
            "SELECT workstream_id, manifest_path, status FROM maintenance_runs "
            "WHERE id = 'lb-222222222222'"
        ).fetchone()
        self.assertEqual(tuple(run), (None, "/manifest", "completed"))
        self.assertIsNone(
            connection.execute(
                "SELECT workstream_id FROM maintenance_runs "
                "WHERE id = 'lb-222222222223'"
            ).fetchone()[0]
        )
        self.assertEqual(
            connection.execute(
                "SELECT maintenance_run_id FROM sessions"
            ).fetchone()[0],
            "lb-222222222222",
        )
        self.assertEqual(
            connection.execute("SELECT origin_run_id FROM suggestions").fetchone()[0],
            "lb-222222222222",
        )

    def test_orphan_and_unexpected_shape_abort_without_mutation(self):
        orphan = self._complete_legacy_connection()
        orphan.execute(
            "INSERT INTO maintenance_runs(id, workstream_id) "
            "VALUES ('lb-333333333333', 999)"
        )
        before_sql = orphan.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='maintenance_runs'"
        ).fetchone()[0]
        before_rows = [tuple(row) for row in orphan.execute("SELECT * FROM maintenance_runs")]
        with self.assertRaisesRegex(RuntimeError, "refused 1 orphan row"):
            _repair_maintenance_workstream_fk(orphan)
        self.assertEqual(
            orphan.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='maintenance_runs'"
            ).fetchone()[0],
            before_sql,
        )
        self.assertEqual(
            [tuple(row) for row in orphan.execute("SELECT * FROM maintenance_runs")],
            before_rows,
        )
        orphan.close()

        unexpected = self._complete_legacy_connection()
        unexpected.execute(
            "ALTER TABLE maintenance_runs ADD COLUMN private_extension TEXT"
        )
        before_sql = unexpected.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='maintenance_runs'"
        ).fetchone()[0]
        with self.assertRaisesRegex(RuntimeError, "unexpected table shape"):
            _repair_maintenance_workstream_fk(unexpected)
        self.assertEqual(
            unexpected.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='maintenance_runs'"
            ).fetchone()[0],
            before_sql,
        )
        unexpected.close()

        collision = self._complete_legacy_connection()
        collision.execute(
            "CREATE TABLE maintenance_runs__workstream_fk_legacy(id TEXT)"
        )
        before_sql = collision.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='maintenance_runs'"
        ).fetchone()[0]
        with self.assertRaisesRegex(RuntimeError, "target already exists"):
            _repair_maintenance_workstream_fk(collision)
        self.assertEqual(
            collision.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='maintenance_runs'"
            ).fetchone()[0],
            before_sql,
        )
        self.assertIsNotNone(
            collision.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' "
                "AND name='maintenance_runs__workstream_fk_legacy'"
            ).fetchone()
        )
        collision.close()

    def test_file_upgrade_creates_non_overwriting_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            database_path = data_dir / "localbrain.db"
            legacy = legacy_maintenance_run_connection(str(database_path))
            legacy.execute("INSERT INTO workstreams(id, name) VALUES (1, 'Owner')")
            legacy.execute(
                "INSERT INTO maintenance_runs(id, status, summary) "
                "VALUES ('lb-444444444444', 'completed', 'preserve')"
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
                backup_path = _maintenance_workstream_fk_backup_path(database_path)
                self.assertTrue(backup_path.is_file())
                backup_bytes = backup_path.read_bytes()
                init_db()
                self.assertEqual(backup_path.read_bytes(), backup_bytes)

            backup = sqlite3.connect(str(backup_path))
            self.assertEqual(backup.execute("PRAGMA quick_check").fetchone()[0], "ok")
            self.assertEqual(
                backup.execute("PRAGMA foreign_key_list(maintenance_runs)").fetchall(),
                [],
            )
            backup.close()

            upgraded = sqlite3.connect(str(database_path))
            upgraded.row_factory = sqlite3.Row
            upgraded.execute("PRAGMA foreign_keys = ON")
            self.assertTrue(_maintenance_workstream_fk_exists(upgraded))
            self.assertEqual(
                tuple(
                    upgraded.execute(
                        "SELECT id, status, summary FROM maintenance_runs"
                    ).fetchone()
                ),
                ("lb-444444444444", "completed", "preserve"),
            )
            self.assertEqual(upgraded.execute("PRAGMA foreign_key_check").fetchall(), [])
            upgraded.close()


class MaintenanceSessionCompatibleMigrationTests(unittest.TestCase):
    def test_compatible_repair_preserves_sessions_children_and_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            database_path = data_dir / "localbrain.db"
            legacy = legacy_session_connection(str(database_path))
            insert_usage_record(legacy)
            legacy.execute(
                "INSERT INTO activity_events("
                "id, session_id, sequence, event_type, source_line"
                ") VALUES ('event-1', 1, 1, 'message', 1)"
            )
            legacy.execute(
                "INSERT INTO maintenance_runs(id, status) "
                "VALUES ('lb-111111111111', 'prepared')"
            )
            legacy.execute(
                """
                INSERT INTO sessions(
                    source_id, external_id, source_path, title, session_class,
                    session_role, index_policy, maintenance_run_id
                ) VALUES (
                    1, 'maintenance-1', '/synthetic/run.jsonl', 'Run',
                    'maintenance', 'primary', 'metadata_only', 'lb-111111111111'
                )
                """
            )
            legacy.commit()
            before = {
                table: [tuple(row) for row in legacy.execute("SELECT * FROM " + table)]
                for table in ("sessions", "activity_events", "usage_records")
            }
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
                backup_path = _maintenance_session_contract_backup_path(database_path)
                self.assertTrue(backup_path.is_file())
                backup_bytes = backup_path.read_bytes()
                init_db()
                self.assertEqual(backup_path.read_bytes(), backup_bytes)

            backup = sqlite3.connect(str(backup_path))
            backup_sql = backup.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'sessions'"
            ).fetchone()[0]
            self.assertNotRegex(backup_sql, SESSION_CLASS_CHECK_PATTERN)
            self.assertEqual(backup.execute("PRAGMA quick_check").fetchone()[0], "ok")
            backup.close()

            upgraded = sqlite3.connect(str(database_path))
            upgraded.row_factory = sqlite3.Row
            upgraded.execute("PRAGMA foreign_keys = ON")
            after = {
                table: [tuple(row) for row in upgraded.execute("SELECT * FROM " + table)]
                for table in ("sessions", "activity_events", "usage_records")
            }
            self.assertEqual(after, before)
            self.assertTrue(_maintenance_session_contract_exists(upgraded))
            self.assertEqual(upgraded.execute("PRAGMA foreign_key_check").fetchall(), [])
            upgraded.close()

    def test_invalid_legacy_values_and_relations_abort_before_rebuild(self):
        cases = {
            "session_class": (
                "INSERT INTO sessions(source_id, external_id, source_path, title, session_class) "
                "VALUES (1, 'invalid', '/synthetic/invalid', 'Invalid', 'other')",
                "session_class=1",
            ),
            "index_policy": (
                "INSERT INTO sessions(source_id, external_id, source_path, title, index_policy) "
                "VALUES (1, 'invalid', '/synthetic/invalid', 'Invalid', 'other')",
                "index_policy=1",
            ),
            "orphan_run": (
                "INSERT INTO sessions(source_id, external_id, source_path, title, "
                "session_class, index_policy, maintenance_run_id) VALUES ("
                "1, 'invalid', '/synthetic/invalid', 'Invalid', "
                "'maintenance', 'metadata_only', 'lb-333333333333')",
                "orphan_run=1",
            ),
        }
        for name, (statement, error) in cases.items():
            with self.subTest(name=name):
                connection = legacy_session_connection()
                connection.execute(
                    "INSERT INTO sources(kind, name, root_path) "
                    "VALUES ('claude', 'Claude', '/synthetic/claude')"
                )
                connection.execute(statement)
                before_sql = connection.execute(
                    "SELECT sql FROM sqlite_master WHERE name = 'sessions'"
                ).fetchone()[0]
                before_rows = [tuple(row) for row in connection.execute("SELECT * FROM sessions")]
                with self.assertRaisesRegex(RuntimeError, error):
                    _repair_maintenance_session_contract(connection)
                self.assertEqual(
                    connection.execute(
                        "SELECT sql FROM sqlite_master WHERE name = 'sessions'"
                    ).fetchone()[0],
                    before_sql,
                )
                self.assertEqual(
                    [tuple(row) for row in connection.execute("SELECT * FROM sessions")],
                    before_rows,
                )
                connection.close()


class UsageRecordTableNameMigrationTests(unittest.TestCase):
    def test_fresh_schema_uses_only_canonical_table_and_indexes(self):
        connection = schema_connection()
        objects = {
            (row["type"], row["name"])
            for row in connection.execute(
                "SELECT type, name FROM sqlite_master WHERE sql IS NOT NULL"
            )
        }
        self.assertIn(("table", "usage_records"), objects)
        self.assertNotIn(("table", "usage_facts"), objects)
        for index in (
            "idx_usage_records_session_time",
            "idx_usage_records_source_time",
            "idx_usage_records_model_time",
        ):
            self.assertIn(("index", index), objects)
        self.assertFalse(
            any(name.startswith("idx_usage_facts_") for _, name in objects)
        )
        self.assertFalse(_migrate_legacy_usage_table_name(connection))
        connection.close()

    def test_legacy_table_is_renamed_in_place_with_exact_rows_and_shape(self):
        connection = schema_connection()
        insert_usage_record(connection)
        before_rows = [tuple(row) for row in connection.execute("SELECT * FROM usage_records")]
        before_info = [
            tuple(row) for row in connection.execute("PRAGMA table_info(usage_records)")
        ]
        rename_usage_table_to_legacy(connection)

        self.assertTrue(_migrate_legacy_usage_table_name(connection))

        after_rows = [tuple(row) for row in connection.execute("SELECT * FROM usage_records")]
        after_info = [
            tuple(row) for row in connection.execute("PRAGMA table_info(usage_records)")
        ]
        objects = {
            (row["type"], row["name"])
            for row in connection.execute(
                "SELECT type, name FROM sqlite_master WHERE sql IS NOT NULL"
            )
        }
        self.assertEqual(after_rows, before_rows)
        self.assertEqual(after_info, before_info)
        self.assertNotIn(("table", "usage_facts"), objects)
        self.assertIn(("table", "usage_records"), objects)
        for index in (
            "idx_usage_records_session_time",
            "idx_usage_records_source_time",
            "idx_usage_records_model_time",
        ):
            self.assertIn(("index", index), objects)
        self.assertFalse(
            any(name.startswith("idx_usage_facts_") for _, name in objects)
        )
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertFalse(_migrate_legacy_usage_table_name(connection))
        self.assertEqual(
            [tuple(row) for row in connection.execute("SELECT * FROM usage_records")],
            before_rows,
        )
        connection.close()

    def test_coexisting_legacy_and_canonical_tables_fail_before_mutation(self):
        connection = schema_connection()
        connection.execute(
            "CREATE TABLE usage_facts AS SELECT * FROM usage_records WHERE 0"
        )
        before = [
            tuple(row)
            for row in connection.execute(
                "SELECT type, name, sql FROM sqlite_master "
                "WHERE name IN ('usage_facts', 'usage_records') ORDER BY name"
            )
        ]

        with self.assertRaisesRegex(RuntimeError, "refused coexisting"):
            _migrate_legacy_usage_table_name(connection)

        after = [
            tuple(row)
            for row in connection.execute(
                "SELECT type, name, sql FROM sqlite_master "
                "WHERE name IN ('usage_facts', 'usage_records') ORDER BY name"
            )
        ]
        self.assertEqual(after, before)
        connection.close()

    def test_file_startup_renames_legacy_table_before_check_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            database_path = data_dir / "localbrain.db"
            legacy = sqlite3.connect(str(database_path))
            legacy.row_factory = sqlite3.Row
            legacy.execute("PRAGMA foreign_keys = ON")
            legacy.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            make_legacy_usage_table(legacy)
            insert_usage_record(legacy)
            before_rows = [
                tuple(row) for row in legacy.execute("SELECT * FROM usage_records")
            ]
            before_info = [
                tuple(row) for row in legacy.execute("PRAGMA table_info(usage_records)")
            ]
            rename_usage_table_to_legacy(legacy)
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

            upgraded = sqlite3.connect(str(database_path))
            upgraded.row_factory = sqlite3.Row
            objects = {
                (row["type"], row["name"])
                for row in upgraded.execute(
                    "SELECT type, name FROM sqlite_master WHERE sql IS NOT NULL"
                )
            }
            after_rows = [
                tuple(row) for row in upgraded.execute("SELECT * FROM usage_records")
            ]
            after_info = [
                tuple(row) for row in upgraded.execute("PRAGMA table_info(usage_records)")
            ]
            table_sql = upgraded.execute(
                "SELECT sql FROM sqlite_master "
                "WHERE type = 'table' AND name = 'usage_records'"
            ).fetchone()[0]
            self.assertEqual(after_rows, before_rows)
            self.assertEqual(after_info, before_info)
            self.assertNotIn(("table", "usage_facts"), objects)
            self.assertIn(("table", "usage_records"), objects)
            self.assertRegex(table_sql, USAGE_ATTRIBUTION_CHECK_PATTERN)
            self.assertEqual(upgraded.execute("PRAGMA foreign_key_check").fetchall(), [])
            upgraded.close()

            backup = sqlite3.connect(str(_usage_attribution_backup_path(database_path)))
            backup_tables = {
                row[0]
                for row in backup.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            self.assertIn("usage_facts", backup_tables)
            self.assertNotIn("usage_records", backup_tables)
            self.assertEqual(backup.execute("PRAGMA quick_check").fetchone()[0], "ok")
            backup.close()


class SchemaIndexMigrationTests(unittest.TestCase):
    redundant = {
        "idx_events_session_sequence",
        "idx_local_resources_path",
        "idx_checkpoint_resource_refs",
    }
    additions = {
        "idx_checkpoints_workstream_version": [
            ("workstream_id", False),
            ("version", True),
        ],
        "idx_documents_source": [("source_id", False)],
        "idx_documents_workspace": [
            ("workspace_id", False),
            ("mtime_ns", True),
        ],
    }

    def test_fresh_schema_has_only_the_approved_index_set(self):
        connection = schema_connection()
        names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND sql IS NOT NULL"
            )
        }
        self.assertTrue(self.redundant.isdisjoint(names))
        self.assertTrue(set(self.additions).issubset(names))
        for name, shape in self.additions.items():
            self.assertEqual(index_shape(connection, name), shape)
        connection.close()


class ActivityEventMetadataMigrationTests(unittest.TestCase):
    retained_columns = (
        "id",
        "session_id",
        "sequence",
        "occurred_at",
        "event_type",
        "role",
        "text",
        "tool_name",
        "source_line",
    )

    def _legacy_connection(self, metadata=None):
        connection = schema_connection()
        connection.execute("ALTER TABLE activity_events ADD COLUMN metadata_json TEXT")
        connection.executescript(
            """
            INSERT INTO sources(kind, name, root_path)
                VALUES ('codex', 'Codex', '/synthetic/codex');
            INSERT INTO sessions(source_id, external_id, source_path, title)
                VALUES (1, 'session-1', '/synthetic/session.jsonl', 'Synthetic');
            """
        )
        connection.execute(
            """
            INSERT INTO activity_events(
                id, session_id, sequence, occurred_at, event_type, role,
                text, tool_name, source_line, metadata_json
            ) VALUES (
                'event-1', 1, 10, '2026-07-19T00:00:00+00:00',
                'message', 'user', 'Synthetic message', NULL, 1, ?
            )
            """,
            (metadata,),
        )
        return connection

    def test_fresh_contract_omits_unused_metadata(self):
        connection = schema_connection()
        self.assertNotIn("metadata_json", {
            row["name"] for row in connection.execute("PRAGMA table_info(activity_events)")
        })
        self.assertNotIn("metadata", {field.name for field in fields(ParsedEvent)})
        connection.close()

    def test_all_null_legacy_column_is_removed_without_changing_retained_values(self):
        connection = self._legacy_connection()
        column_list = ", ".join(self.retained_columns)
        before_rows = [
            tuple(row)
            for row in connection.execute(
                "SELECT {} FROM activity_events ORDER BY id".format(column_list)
            )
        ]

        _run_compatible_migrations(connection)

        after_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(activity_events)")
        }
        after_rows = [
            tuple(row)
            for row in connection.execute(
                "SELECT {} FROM activity_events ORDER BY id".format(column_list)
            )
        ]
        self.assertNotIn("metadata_json", after_columns)
        self.assertEqual(after_rows, before_rows)
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])

        _run_compatible_migrations(connection)
        self.assertEqual(
            [
                tuple(row)
                for row in connection.execute(
                    "SELECT {} FROM activity_events ORDER BY id".format(column_list)
                )
            ],
            before_rows,
        )
        connection.close()

    def test_non_null_legacy_metadata_aborts_before_schema_mutation(self):
        connection = self._legacy_connection('{"synthetic":true}')
        before_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'activity_events'"
        ).fetchone()[0]
        before_rows = [tuple(row) for row in connection.execute("SELECT * FROM activity_events")]

        with self.assertRaisesRegex(RuntimeError, "refused 1 non-null row"):
            _run_compatible_migrations(connection)

        after_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'activity_events'"
        ).fetchone()[0]
        after_rows = [tuple(row) for row in connection.execute("SELECT * FROM activity_events")]
        self.assertEqual(after_sql, before_sql)
        self.assertEqual(after_rows, before_rows)
        connection.close()


class UsageAttributionCheckMigrationTests(unittest.TestCase):
    def test_valid_legacy_rows_and_column_metadata_are_preserved_exactly(self):
        connection = schema_connection()
        make_legacy_usage_table(connection)
        insert_usage_record(connection, attributed_at=None)
        before_rows = [tuple(row) for row in connection.execute("SELECT * FROM usage_records")]
        before_info = [
            tuple(row) for row in connection.execute("PRAGMA table_info(usage_records)")
        ]

        _run_compatible_migrations(connection)

        after_rows = [tuple(row) for row in connection.execute("SELECT * FROM usage_records")]
        after_info = [
            tuple(row) for row in connection.execute("PRAGMA table_info(usage_records)")
        ]
        table_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usage_records'"
        ).fetchone()[0]
        self.assertEqual(after_rows, before_rows)
        self.assertEqual(after_info, before_info)
        self.assertRegex(table_sql, USAGE_ATTRIBUTION_CHECK_PATTERN)
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        for name in (
            "idx_usage_records_session_time",
            "idx_usage_records_source_time",
            "idx_usage_records_model_time",
        ):
            self.assertIsNotNone(
                connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = ?",
                    (name,),
                ).fetchone()
            )
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE usage_records SET attribution_basis = 'unknown' WHERE id = 'record-1'"
            )

        _run_compatible_migrations(connection)
        self.assertEqual(
            [tuple(row) for row in connection.execute("SELECT * FROM usage_records")],
            before_rows,
        )
        connection.close()

    def test_invalid_legacy_value_aborts_without_changing_table_or_rows(self):
        connection = schema_connection()
        make_legacy_usage_table(connection)
        insert_usage_record(connection, basis="unknown")
        before_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usage_records'"
        ).fetchone()[0]
        before_rows = [tuple(row) for row in connection.execute("SELECT * FROM usage_records")]

        with self.assertRaisesRegex(RuntimeError, "refused 1 invalid row"):
            _run_compatible_migrations(connection)

        after_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usage_records'"
        ).fetchone()[0]
        after_rows = [tuple(row) for row in connection.execute("SELECT * FROM usage_records")]
        self.assertEqual(after_sql, before_sql)
        self.assertEqual(after_rows, before_rows)
        self.assertNotRegex(after_sql, USAGE_ATTRIBUTION_CHECK_PATTERN)
        connection.close()

    def test_null_legacy_value_aborts_without_coercion(self):
        connection = schema_connection()
        make_legacy_usage_table(connection, nullable_basis=True)
        insert_usage_record(connection, basis=None)
        before_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usage_records'"
        ).fetchone()[0]
        before_rows = [tuple(row) for row in connection.execute("SELECT * FROM usage_records")]

        with self.assertRaisesRegex(RuntimeError, "refused 1 invalid row"):
            _run_compatible_migrations(connection)

        after_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usage_records'"
        ).fetchone()[0]
        after_rows = [tuple(row) for row in connection.execute("SELECT * FROM usage_records")]
        self.assertEqual(after_sql, before_sql)
        self.assertEqual(after_rows, before_rows)
        self.assertNotRegex(after_sql, USAGE_ATTRIBUTION_CHECK_PATTERN)
        connection.close()

    def test_unexpected_legacy_shape_aborts_without_changing_table_or_rows(self):
        connection = schema_connection()
        make_legacy_usage_table(connection)
        connection.execute("ALTER TABLE usage_records ADD COLUMN private_extension TEXT")
        insert_usage_record(connection)
        before_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usage_records'"
        ).fetchone()[0]
        before_rows = [tuple(row) for row in connection.execute("SELECT * FROM usage_records")]

        with self.assertRaisesRegex(RuntimeError, "unexpected table shape"):
            _run_compatible_migrations(connection)

        after_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usage_records'"
        ).fetchone()[0]
        after_rows = [tuple(row) for row in connection.execute("SELECT * FROM usage_records")]
        self.assertEqual(after_sql, before_sql)
        self.assertEqual(after_rows, before_rows)
        self.assertNotRegex(after_sql, USAGE_ATTRIBUTION_CHECK_PATTERN)
        connection.close()

    def test_file_upgrade_creates_and_preserves_a_valid_pre_migration_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            database_path = data_dir / "localbrain.db"
            legacy = sqlite3.connect(str(database_path))
            legacy.row_factory = sqlite3.Row
            legacy.execute("PRAGMA foreign_keys = ON")
            legacy.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            make_legacy_usage_table(legacy)
            insert_usage_record(legacy)
            legacy.commit()
            before_rows = [
                tuple(row) for row in legacy.execute("SELECT * FROM usage_records")
            ]
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
                backup_path = _usage_attribution_backup_path(database_path)
                self.assertTrue(backup_path.is_file())
                backup_bytes = backup_path.read_bytes()
                init_db()
                self.assertEqual(backup_path.read_bytes(), backup_bytes)

            backup = sqlite3.connect(str(backup_path))
            backup.row_factory = sqlite3.Row
            backup_sql = backup.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usage_records'"
            ).fetchone()[0]
            backup_rows = [
                tuple(row) for row in backup.execute("SELECT * FROM usage_records")
            ]
            self.assertEqual(backup.execute("PRAGMA quick_check").fetchone()[0], "ok")
            self.assertNotRegex(backup_sql, USAGE_ATTRIBUTION_CHECK_PATTERN)
            self.assertEqual(backup_rows, before_rows)
            backup.close()

            upgraded = sqlite3.connect(str(database_path))
            upgraded.row_factory = sqlite3.Row
            upgraded_sql = upgraded.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usage_records'"
            ).fetchone()[0]
            upgraded_rows = [
                tuple(row) for row in upgraded.execute("SELECT * FROM usage_records")
            ]
            self.assertRegex(upgraded_sql, USAGE_ATTRIBUTION_CHECK_PATTERN)
            self.assertEqual(upgraded_rows, before_rows)
            upgraded.close()


class SchemaIndexCompatibleMigrationTests(unittest.TestCase):
    redundant = SchemaIndexMigrationTests.redundant
    additions = SchemaIndexMigrationTests.additions

    def test_compatible_index_migration_preserves_rows_and_is_idempotent(self):
        connection = schema_connection()
        for name in self.additions:
            connection.execute(f'DROP INDEX "{name}"')
        connection.executescript(
            """
            CREATE INDEX idx_events_session_sequence
                ON activity_events(session_id, sequence);
            CREATE INDEX idx_local_resources_path
                ON local_resources(path);
            CREATE INDEX idx_checkpoint_resource_refs
                ON checkpoint_resource_refs(checkpoint_id, thread_id);
            INSERT INTO sources(kind, name, root_path)
                VALUES ('codex', 'Codex', '/synthetic/codex');
            INSERT INTO workspaces(display_name, canonical_path)
                VALUES ('Synthetic', '/synthetic/workspace');
            INSERT INTO sessions(source_id, external_id, source_path, title)
                VALUES (1, 'session-1', '/synthetic/session.jsonl', 'Synthetic');
            INSERT INTO activity_events(
                id, session_id, sequence, event_type, source_line
            ) VALUES ('event-1', 1, 1, 'message', 1);
            INSERT INTO workstreams(name) VALUES ('Synthetic Workstream');
            INSERT INTO checkpoints(workstream_id, current_goal, version)
                VALUES (1, 'Preserve rows', 1);
            INSERT INTO local_resources(path, title)
                VALUES ('/synthetic/resource', 'Synthetic Resource');
            INSERT INTO checkpoint_resource_refs(
                checkpoint_id, entity_type, entity_id
            ) VALUES (1, 'local_resource', '1');
            INSERT INTO context_documents(
                source_id, workspace_id, path, relative_path, title, body,
                size_bytes, mtime_ns, content_hash
            ) VALUES (
                1, 1, '/synthetic/document.md', 'document.md', 'Document',
                'Synthetic body', 14, 100, 'synthetic-hash'
            );
            """
        )
        tables = (
            "activity_events",
            "local_resources",
            "checkpoint_resource_refs",
            "checkpoints",
            "context_documents",
        )
        before = {
            table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table}")]
            for table in tables
        }

        _run_compatible_migrations(connection, include_data_migrations=False)
        _run_compatible_migrations(connection, include_data_migrations=False)

        after = {
            table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table}")]
            for table in tables
        }
        self.assertEqual(after, before)
        names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND sql IS NOT NULL"
            )
        }
        self.assertTrue(self.redundant.isdisjoint(names))
        self.assertTrue(set(self.additions).issubset(names))
        connection.close()

    def test_redundant_drop_fails_before_mutation_without_unique_coverage(self):
        connection = schema_connection()
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.executescript(
            """
            ALTER TABLE local_resources RENAME TO local_resources_legacy;
            CREATE TABLE local_resources (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL,
                resource_type TEXT NOT NULL DEFAULT 'path',
                title TEXT NOT NULL,
                summary TEXT,
                exists_now INTEGER NOT NULL DEFAULT 0,
                discovered_by TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO local_resources SELECT * FROM local_resources_legacy;
            DROP TABLE local_resources_legacy;
            CREATE INDEX idx_local_resources_path ON local_resources(path);
            CREATE INDEX idx_events_session_sequence
                ON activity_events(session_id, sequence);
            CREATE INDEX idx_checkpoint_resource_refs
                ON checkpoint_resource_refs(checkpoint_id, thread_id);
            """
        )

        with self.assertRaisesRegex(RuntimeError, "UNIQUE index coverage is missing"):
            _migrate_schema_indexes(connection)

        names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND sql IS NOT NULL"
            )
        }
        self.assertTrue(self.redundant.issubset(names))
        connection.close()

    def test_added_indexes_support_the_current_query_prefixes(self):
        connection = schema_connection()
        cases = (
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
        for name, query in cases:
            with self.subTest(index=name):
                plan = " ".join(
                    row["detail"]
                    for row in connection.execute(
                        "EXPLAIN QUERY PLAN " + query, (1,)
                    )
                )
                self.assertIn(name, plan)
        connection.close()


if __name__ == "__main__":
    unittest.main()
