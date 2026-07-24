import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.config import Settings
from localbrain.db import (
    _external_resource_url_scope_backup_path,
    _external_resource_url_unique_exists,
    _repair_external_resource_url_scope,
    init_db,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


def legacy_schema() -> str:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    current = """CREATE TABLE IF NOT EXISTS external_resources (
    id INTEGER PRIMARY KEY,
    resource_type TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    summary TEXT,
    source_role TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);"""
    legacy = current.replace("url TEXT NOT NULL,", "url TEXT NOT NULL UNIQUE,")
    if current not in schema:
        raise AssertionError("External Resource fixture no longer matches DDL")
    return schema.replace(current, legacy, 1)


def pre_registration_space_schema() -> str:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    for fragment in (
        "    canonical_url TEXT NOT NULL,\n",
        "    coverage TEXT NOT NULL\n"
        "        CHECK(coverage IN ('selected-content', 'full-content')),\n",
        ",\n    CHECK(length(canonical_url) > 0)",
    ):
        if fragment not in schema:
            raise AssertionError(
                "Atlassian Space fixture no longer matches canonical DDL"
            )
        schema = schema.replace(fragment, "", 1)
    return schema


def legacy_connection(path=":memory:"):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(legacy_schema())
    return connection


def add_resource_graph(connection):
    connection.execute(
        "INSERT INTO workstreams(id, name) VALUES (1, 'Synthetic')"
    )
    connection.execute(
        """
        INSERT INTO threads(id, workstream_id, title)
        VALUES (1, 1, 'Synthetic thread')
        """
    )
    connection.execute(
        """
        INSERT INTO external_resources(
            id, resource_type, title, url, summary, source_role,
            created_at, updated_at
        ) VALUES (
            41, 'jira', 'One', 'https://jira.example.test/browse/SYN-1',
            'Local', 'primary', 'created', 'updated'
        )
        """
    )
    connection.execute(
        """
        INSERT INTO workstream_links(
            id, workstream_id, entity_type, entity_id, relation_type
        ) VALUES (1, 1, 'external', '41', 'evidence')
        """
    )
    connection.execute(
        """
        INSERT INTO thread_links(
            id, thread_id, entity_type, entity_id, relation_type
        ) VALUES (1, 1, 'external', '41', 'related-to')
        """
    )
    connection.execute(
        "INSERT INTO checkpoints(id, workstream_id) VALUES (1, 1)"
    )
    connection.execute(
        """
        INSERT INTO checkpoint_resource_refs(
            id, checkpoint_id, thread_id, entity_type, entity_id, relation_type
        ) VALUES (1, 1, 1, 'external', '41', 'evidence')
        """
    )


class ExternalResourceUrlScopeMigrationTests(unittest.TestCase):
    def test_repair_preserves_exact_rows_and_polymorphic_relations(self):
        connection = legacy_connection()
        self.addCleanup(connection.close)
        add_resource_graph(connection)
        before_resource = tuple(
            connection.execute(
                "SELECT * FROM external_resources WHERE id = 41"
            ).fetchone()
        )
        before_links = {
            table: [
                tuple(row)
                for row in connection.execute(
                    "SELECT * FROM {} ORDER BY id".format(table)
                )
            ]
            for table in (
                "workstream_links",
                "thread_links",
                "checkpoint_resource_refs",
            )
        }
        self.assertTrue(_external_resource_url_unique_exists(connection))
        self.assertTrue(_repair_external_resource_url_scope(connection))
        self.assertFalse(_external_resource_url_unique_exists(connection))
        self.assertEqual(
            tuple(
                connection.execute(
                    "SELECT * FROM external_resources WHERE id = 41"
                ).fetchone()
            ),
            before_resource,
        )
        for table, rows in before_links.items():
            self.assertEqual(
                [
                    tuple(row)
                    for row in connection.execute(
                        "SELECT * FROM {} ORDER BY id".format(table)
                    )
                ],
                rows,
            )
        connection.execute(
            """
            INSERT INTO external_resources(
                id, resource_type, title, url
            ) VALUES (
                42, 'wiki', 'Same URL is now legal',
                'https://jira.example.test/browse/SYN-1'
            )
            """
        )
        self.assertEqual(
            connection.execute(
                """
                SELECT COUNT(*) FROM external_resources
                WHERE url = 'https://jira.example.test/browse/SYN-1'
                """
            ).fetchone()[0],
            2,
        )
        self.assertFalse(_repair_external_resource_url_scope(connection))
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_unexpected_shape_and_legacy_target_abort_before_mutation(self):
        unexpected = legacy_connection()
        unexpected.execute(
            "ALTER TABLE external_resources ADD COLUMN private_extension TEXT"
        )
        before_sql = unexpected.execute(
            """
            SELECT sql FROM sqlite_master
            WHERE type = 'table' AND name = 'external_resources'
            """
        ).fetchone()[0]
        with self.assertRaisesRegex(RuntimeError, "unexpected table shape"):
            _repair_external_resource_url_scope(unexpected)
        self.assertEqual(
            unexpected.execute(
                """
                SELECT sql FROM sqlite_master
                WHERE type = 'table' AND name = 'external_resources'
                """
            ).fetchone()[0],
            before_sql,
        )
        unexpected.close()

        unexpected_index = legacy_connection()
        unexpected_index.execute(
            """
            CREATE INDEX idx_external_resources_private
            ON external_resources(title)
            """
        )
        with self.assertRaisesRegex(RuntimeError, "unexpected explicit index"):
            _repair_external_resource_url_scope(unexpected_index)
        self.assertTrue(_external_resource_url_unique_exists(unexpected_index))
        unexpected_index.close()

        collision = legacy_connection()
        collision.execute(
            "CREATE TABLE external_resources__url_scope_legacy(id INTEGER)"
        )
        with self.assertRaisesRegex(RuntimeError, "target already exists"):
            _repair_external_resource_url_scope(collision)
        self.assertTrue(_external_resource_url_unique_exists(collision))
        collision.close()

    def test_file_startup_creates_non_overwriting_valid_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            database_path = data_dir / "localbrain.db"
            connection = legacy_connection(str(database_path))
            add_resource_graph(connection)
            connection.commit()
            connection.close()
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
                backup_path = _external_resource_url_scope_backup_path(
                    database_path
                )
                self.assertTrue(backup_path.is_file())
                backup_bytes = backup_path.read_bytes()
                init_db()
                self.assertEqual(backup_path.read_bytes(), backup_bytes)

            backup = sqlite3.connect(str(backup_path))
            backup.row_factory = sqlite3.Row
            self.assertEqual(backup.execute("PRAGMA quick_check").fetchone()[0], "ok")
            self.assertTrue(_external_resource_url_unique_exists(backup))
            self.assertEqual(
                backup.execute(
                    "SELECT id FROM external_resources"
                ).fetchone()[0],
                41,
            )
            backup.close()

            upgraded = sqlite3.connect(str(database_path))
            upgraded.row_factory = sqlite3.Row
            upgraded.execute("PRAGMA foreign_keys = ON")
            self.assertFalse(_external_resource_url_unique_exists(upgraded))
            self.assertEqual(
                upgraded.execute(
                    "SELECT id FROM external_resources"
                ).fetchone()[0],
                41,
            )
            self.assertEqual(upgraded.execute("PRAGMA foreign_key_check").fetchall(), [])
            upgraded.close()

    def test_startup_adds_space_url_and_service_default_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            database_path = data_dir / "localbrain.db"
            connection = sqlite3.connect(str(database_path))
            connection.executescript(pre_registration_space_schema())
            source_id = connection.execute(
                """
                INSERT INTO external_source_instances(
                    instance_key, provider_kind, service, display_name, config_ref
                ) VALUES ('wiki-source', 'mcp_gateway', 'confluence',
                          'Synthetic Wiki', 'wiki')
                """
            ).lastrowid
            site_id = connection.execute(
                """
                INSERT INTO atlassian_sites(
                    source_instance_id, normalized_domain, canonical_base_url
                ) VALUES (?, 'wiki.example.test', 'https://wiki.example.test')
                """,
                (source_id,),
            ).lastrowid
            connection.execute(
                """
                INSERT INTO atlassian_spaces(
                    site_id, service, space_key, name
                ) VALUES (?, 'confluence', 'TEAM', 'Team')
                """,
                (site_id,),
            )
            connection.commit()
            connection.close()

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
            row = upgraded.execute(
                "SELECT canonical_url, coverage FROM atlassian_spaces"
            ).fetchone()
            self.assertEqual(
                tuple(row),
                (
                    "https://wiki.example.test/spaces/TEAM/overview",
                    "full-content",
                ),
            )
            self.assertEqual(
                upgraded.execute("PRAGMA foreign_key_check").fetchall(), []
            )
            upgraded.close()
