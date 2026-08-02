import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.config import Settings
from localbrain.db import (
    _atlassian_site_access_backup_path,
    _atlassian_site_access_contract_exists,
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


def required_site_access_schema() -> str:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    current_site_source = """    source_instance_id INTEGER
        REFERENCES external_source_instances(id) ON DELETE SET NULL,
"""
    legacy_site_source = """    source_instance_id INTEGER NOT NULL
        REFERENCES external_source_instances(id) ON DELETE RESTRICT,
"""
    binding_table = """CREATE TABLE IF NOT EXISTS atlassian_site_bindings (
    id INTEGER PRIMARY KEY,
    site_id INTEGER NOT NULL
        REFERENCES atlassian_sites(id) ON DELETE CASCADE,
    source_instance_id INTEGER NOT NULL
        REFERENCES external_source_instances(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site_id, source_instance_id)
);

"""
    optional_access_column = """    source_instance_id INTEGER
        REFERENCES external_source_instances(id) ON DELETE SET NULL,
"""
    binding_index = """CREATE INDEX IF NOT EXISTS idx_atlassian_site_bindings_source
    ON atlassian_site_bindings(source_instance_id, site_id);
"""
    for fragment in (
        current_site_source,
        binding_table,
        binding_index,
    ):
        if fragment not in schema:
            raise AssertionError(
                "Atlassian optional-access fixture no longer matches canonical DDL"
            )
    schema = schema.replace(current_site_source, legacy_site_source, 1)
    schema = schema.replace(binding_table, "", 1)
    schema = schema.replace(optional_access_column, "", 2)
    return schema.replace(binding_index, "", 1)


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


class AtlassianSiteAccessMigrationTests(unittest.TestCase):
    def test_file_upgrade_preserves_local_graph_and_backfills_access(self):
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            database_path = data_dir / "localbrain.db"
            connection = sqlite3.connect(str(database_path))
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(required_site_access_schema())
            source_id = connection.execute(
                """
                INSERT INTO external_source_instances(
                    instance_key, provider_kind, service, display_name, config_ref
                ) VALUES (
                    'jira-source', 'mcp_gateway', 'jira',
                    'Synthetic Jira', 'jira-approved'
                )
                """
            ).lastrowid
            site_id = connection.execute(
                """
                INSERT INTO atlassian_sites(
                    source_instance_id, normalized_domain, display_name,
                    canonical_base_url
                ) VALUES (?, 'jira.example.test', 'Synthetic Site',
                          'https://jira.example.test')
                """,
                (source_id,),
            ).lastrowid
            space_id = connection.execute(
                """
                INSERT INTO atlassian_spaces(
                    site_id, service, space_key, name, canonical_url, coverage
                ) VALUES (
                    ?, 'jira', 'SYN', 'Synthetic Project',
                    'https://jira.example.test/jira/software/projects/SYN',
                    'selected-content'
                )
                """,
                (site_id,),
            ).lastrowid
            resource_id = connection.execute(
                """
                INSERT INTO external_resources(
                    resource_type, title, url, summary
                ) VALUES (
                    'jira', 'SYN-1',
                    'https://jira.example.test/browse/SYN-1',
                    'Preserved local summary'
                )
                """
            ).lastrowid
            connection.execute(
                """
                INSERT INTO atlassian_items(
                    external_resource_id, site_id, space_id, service,
                    item_type, remote_key, coverage
                ) VALUES (?, ?, ?, 'jira', 'jira_issue', 'SYN-1', 'reference')
                """,
                (resource_id, site_id, space_id),
            )
            connection.execute(
                """
                INSERT INTO atlassian_item_local_state(
                    external_resource_id, note
                ) VALUES (?, 'Preserved local note')
                """,
                (resource_id,),
            )
            before_site = tuple(
                connection.execute(
                    "SELECT * FROM atlassian_sites WHERE id = ?", (site_id,)
                ).fetchone()
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
                backup_path = _atlassian_site_access_backup_path(database_path)
                self.assertTrue(backup_path.is_file())
                backup_bytes = backup_path.read_bytes()
                init_db()
                self.assertEqual(backup_path.read_bytes(), backup_bytes)

            backup = sqlite3.connect(str(backup_path))
            backup.row_factory = sqlite3.Row
            self.assertFalse(_atlassian_site_access_contract_exists(backup))
            self.assertEqual(backup.execute("PRAGMA quick_check").fetchone()[0], "ok")
            backup.close()

            upgraded = sqlite3.connect(str(database_path))
            upgraded.row_factory = sqlite3.Row
            upgraded.execute("PRAGMA foreign_keys = ON")
            self.assertTrue(_atlassian_site_access_contract_exists(upgraded))
            self.assertEqual(
                tuple(
                    upgraded.execute(
                        "SELECT * FROM atlassian_sites WHERE id = ?", (site_id,)
                    ).fetchone()
                ),
                before_site,
            )
            self.assertEqual(
                tuple(
                    upgraded.execute(
                        """
                        SELECT site_id, source_instance_id
                        FROM atlassian_site_bindings
                        """
                    ).fetchone()
                ),
                (site_id, source_id),
            )
            self.assertEqual(
                upgraded.execute(
                    "SELECT source_instance_id FROM atlassian_spaces WHERE id = ?",
                    (space_id,),
                ).fetchone()[0],
                source_id,
            )
            self.assertEqual(
                upgraded.execute(
                    """
                    SELECT source_instance_id
                    FROM atlassian_items
                    WHERE external_resource_id = ?
                    """,
                    (resource_id,),
                ).fetchone()[0],
                source_id,
            )
            self.assertEqual(
                upgraded.execute(
                    """
                    SELECT note FROM atlassian_item_local_state
                    WHERE external_resource_id = ?
                    """,
                    (resource_id,),
                ).fetchone()[0],
                "Preserved local note",
            )
            self.assertEqual(upgraded.execute("PRAGMA foreign_key_check").fetchall(), [])

            upgraded.execute(
                "DELETE FROM external_source_instances WHERE id = ?", (source_id,)
            )
            self.assertIsNone(
                upgraded.execute(
                    "SELECT source_instance_id FROM atlassian_sites WHERE id = ?",
                    (site_id,),
                ).fetchone()[0]
            )
            self.assertIsNone(
                upgraded.execute(
                    "SELECT source_instance_id FROM atlassian_spaces WHERE id = ?",
                    (space_id,),
                ).fetchone()[0]
            )
            self.assertIsNone(
                upgraded.execute(
                    """
                    SELECT source_instance_id FROM atlassian_items
                    WHERE external_resource_id = ?
                    """,
                    (resource_id,),
                ).fetchone()[0]
            )
            self.assertEqual(
                upgraded.execute(
                    "SELECT COUNT(*) FROM atlassian_site_bindings"
                ).fetchone()[0],
                0,
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
