import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain import db
from localbrain.config import Settings
from localbrain.source_revision_migration import (
    BACKUP_SUFFIX,
    LEGACY_REVISIONS,
    REVISION_CHECK,
    migrate_session_revisions,
    prepare_session_revision_migration,
    session_revision_contract_current,
)


SCHEMA = (Path(__file__).parents[1] / "src/localbrain/schema.sql").read_text()


def legacy_connection(path=":memory:", factory=sqlite3.Connection):
    connection = sqlite3.connect(str(path), factory=factory)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA.replace(
        "session_contract_version INTEGER " + REVISION_CHECK,
        "session_contract_version TEXT",
    ))
    connection.execute(
        "CREATE INDEX idx_source_files_session ON source_files(session_id, path)"
    )
    connection.executemany(
        "INSERT INTO sources(id,provider_kind,name,root_path) VALUES (?,?,?,?)",
        [(1, "codex", "Personal", "/synthetic/personal"),
         (2, "claude", "Team", "/synthetic/team"),
         (3, "local_context", "Notes", "/synthetic/notes")],
    )
    connection.execute(
        "INSERT INTO sessions(id,source_id,external_id,source_path,title) "
        "VALUES (9,1,'synthetic','/synthetic/personal/a.jsonl','Keep title')"
    )
    return connection


def insert_file(connection, revision, source=1, number=1):
    connection.execute(
        "INSERT INTO source_files(id,source_id,session_id,path,size_bytes,mtime_ns,"
        "last_scanned_at,status,error,session_contract_version,usage_contract_version,"
        "reference_contract_version) VALUES (?,?,9,?,123,456,'fixed','error','keep',?,'usage','reference')",
        (number, source, "/synthetic/file-{}".format(number), revision),
    )


def ddl_connection(schema, revision="codex-session-v12-empty-page-controls"):
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(schema)
    connection.execute(
        "INSERT INTO sources(id,provider_kind,name,root_path) "
        "VALUES (1,'codex','Synthetic','/synthetic')"
    )
    connection.execute(
        "INSERT INTO source_files(source_id,path,size_bytes,mtime_ns,"
        "last_scanned_at,session_contract_version) VALUES (1,'/synthetic/file',0,0,'fixed',?)",
        (revision,),
    )
    return connection


class SessionRevisionMigrationTests(unittest.TestCase):
    def test_commented_unsupported_checks_are_refused_without_losing_the_rule(self):
        legacy = SCHEMA.replace("session_contract_version INTEGER " + REVISION_CHECK,
                                "session_contract_version TEXT")
        for comment in ("/* synthetic rule */", "-- synthetic rule\n", "\ufeff"):
            schema = legacy.replace("UNIQUE(source_id, path)",
                                    "UNIQUE(source_id, path), CHECK " + comment +
                                    " (status <> 'archived')", 1)
            with self.subTest(comment=comment), ddl_connection(schema) as connection:
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("UPDATE source_files SET status='archived'")
                before = list(connection.iterdump())
                with self.assertRaisesRegex(RuntimeError, "Unexpected source-file constraints"):
                    migrate_session_revisions(connection)
                self.assertEqual(list(connection.iterdump()), before)
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("UPDATE source_files SET status='archived'")

    def test_commented_conflict_policy_is_refused_and_duplicates_remain_ignored(self):
        legacy = SCHEMA.replace("session_contract_version INTEGER " + REVISION_CHECK,
                                "session_contract_version TEXT")
        duplicate = (
            "INSERT INTO source_files(source_id,path,size_bytes,mtime_ns,last_scanned_at) "
            "VALUES (1,'/synthetic/file',0,0,'fixed')"
        )
        for comment in ("/* synthetic policy */", "-- synthetic policy\n", "\ufeff"):
            schema = legacy.replace("UNIQUE(source_id, path)",
                                    "UNIQUE(source_id, path) ON " + comment + " CONFLICT IGNORE", 1)
            with self.subTest(comment=comment), ddl_connection(schema) as connection:
                connection.execute(duplicate)
                before = list(connection.iterdump())
                with self.assertRaisesRegex(RuntimeError, "Unexpected source-file constraints"):
                    migrate_session_revisions(connection)
                connection.execute(duplicate)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM source_files").fetchone()[0], 1)
                self.assertEqual(list(connection.iterdump()), before)

    def test_strict_with_trailing_comment_is_refused_without_losing_storage_checks(self):
        legacy = SCHEMA.replace("session_contract_version INTEGER " + REVISION_CHECK,
                                "session_contract_version TEXT")
        for suffix in ("STRICT /* synthetic mode */", "STRICT -- synthetic mode\n", "\ufeffSTRICT"):
            schema = legacy.replace("UNIQUE(source_id, path)\n);",
                                    "UNIQUE(source_id, path)\n) " + suffix + ";", 1)
            with self.subTest(suffix=suffix), ddl_connection(schema) as connection:
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("UPDATE source_files SET size_bytes='not-an-integer'")
                before = list(connection.iterdump())
                with self.assertRaisesRegex(RuntimeError, "Unexpected source-file constraints"):
                    migrate_session_revisions(connection)
                self.assertEqual(list(connection.iterdump()), before)
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("UPDATE source_files SET size_bytes='not-an-integer'")

    def test_revision_check_only_in_comment_is_not_current_and_gets_real_constraint(self):
        for fake_check in ("/* " + REVISION_CHECK + " */", "-- " + REVISION_CHECK + "\n"):
            schema = SCHEMA.replace("session_contract_version INTEGER " + REVISION_CHECK,
                                    "session_contract_version INTEGER " + fake_check)
            with self.subTest(comment=fake_check), ddl_connection(schema) as connection:
                self.assertFalse(session_revision_contract_current(connection))
                migrate_session_revisions(connection)
                self.assertTrue(session_revision_contract_current(connection))
                self.assertEqual(tuple(connection.execute(
                    "SELECT session_contract_version,typeof(session_contract_version) FROM source_files"
                ).fetchone()), (12, "integer"))
                for invalid in ("arbitrary-text", 0, -1):
                    with self.assertRaises(sqlite3.IntegrityError):
                        connection.execute("UPDATE source_files SET session_contract_version=?", (invalid,))

    def test_quoted_check_text_cannot_establish_revision_contract(self):
        base = SCHEMA.replace("session_contract_version INTEGER " + REVISION_CHECK,
                              "session_contract_version INTEGER")
        quoted_identifier = base.replace(
            "UNIQUE(source_id, path)",
            'CONSTRAINT "' + REVISION_CHECK + '" UNIQUE(source_id, path)', 1,
        )
        quoted_string = base.replace("error TEXT,", "error TEXT DEFAULT '" +
                                     REVISION_CHECK.replace("'", "''") + "',", 1)
        for schema in (quoted_identifier, quoted_string):
            with self.subTest(schema=schema[:40]), ddl_connection(schema) as connection:
                self.assertFalse(session_revision_contract_current(connection))
        with ddl_connection(quoted_identifier) as connection:
            migrate_session_revisions(connection)
            self.assertTrue(session_revision_contract_current(connection))
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE source_files SET session_contract_version='arbitrary-text'")

    def test_real_check_accepts_comments_identifier_quotes_and_preserves_literal_case(self):
        check = (
            'cHeCk /* CHECK(fake) STRICT */ \ufeff("session_contract_version" IS NULL OR '
            '(typeof([session_contract_version]) = \'integer\' -- ON CONFLICT IGNORE\n'
            'AND `session_contract_version` > 0))'
        )
        with ddl_connection(SCHEMA.replace(REVISION_CHECK, check), revision=12) as connection:
            self.assertTrue(session_revision_contract_current(connection))
            before = list(connection.iterdump())
            migrate_session_revisions(connection)
            self.assertEqual(list(connection.iterdump()), before)
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE source_files SET session_contract_version='not-integer'")
        wrong_case = REVISION_CHECK.replace("'integer'", "'INTEGER'")
        with ddl_connection(SCHEMA.replace(REVISION_CHECK, wrong_case), revision=None) as connection:
            self.assertFalse(session_revision_contract_current(connection))
            before = list(connection.iterdump())
            with self.assertRaisesRegex(RuntimeError, "Unexpected source-file constraints"):
                migrate_session_revisions(connection)
            self.assertEqual(list(connection.iterdump()), before)

    def test_modifier_names_inside_quoted_identifiers_are_not_active_keywords(self):
        legacy = SCHEMA.replace("session_contract_version INTEGER " + REVISION_CHECK,
                                "session_contract_version TEXT")
        for name in ('"STRICT"', '`ON CONFLICT`', '[WITHOUT ROWID]', '"COLLATE ""quoted"""', 'name\ufeffSTRICT'):
            schema = legacy.replace("UNIQUE(source_id, path)",
                                    "CONSTRAINT " + name + " UNIQUE(source_id, path)", 1)
            with self.subTest(name=name), ddl_connection(schema) as connection:
                migrate_session_revisions(connection)
                self.assertTrue(session_revision_contract_current(connection))
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("UPDATE source_files SET session_contract_version='not-integer'")

    def test_known_tokens_preserve_every_other_field_indexes_and_foreign_keys(self):
        with legacy_connection() as connection:
            expected_revisions = []
            for source, provider in ((1, "codex"), (2, "claude")):
                for token, revision in LEGACY_REVISIONS[provider].items():
                    insert_file(connection, token, source, len(expected_revisions) + 1)
                    expected_revisions.append(revision)
            insert_file(connection, None, 3, len(expected_revisions) + 1)
            expected_revisions.append(None)
            before = [dict(row) for row in connection.execute("SELECT * FROM source_files ORDER BY id")]
            indexes = [tuple(row) for row in connection.execute("PRAGMA index_list(source_files)")]
            foreign_keys = [tuple(row) for row in connection.execute("PRAGMA foreign_key_list(source_files)")]
            migrate_session_revisions(connection)
            after = [dict(row) for row in connection.execute("SELECT * FROM source_files ORDER BY id")]
            for row, revision in zip(before, expected_revisions):
                row["session_contract_version"] = revision
            self.assertEqual(after, before)
            self.assertEqual([tuple(row) for row in connection.execute("PRAGMA index_list(source_files)")], indexes)
            self.assertEqual([tuple(row) for row in connection.execute("PRAGMA foreign_key_list(source_files)")], foreign_keys)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertTrue(session_revision_contract_current(connection))
            migrate_session_revisions(connection)
            self.assertEqual([dict(row) for row in connection.execute("SELECT * FROM source_files ORDER BY id")], after)
            self.assertEqual(connection.execute("SELECT title FROM sessions WHERE id=9").fetchone()[0], "Keep title")

    def test_fresh_schema_accepts_null_and_positive_integers_and_rejects_invalid_storage(self):
        with sqlite3.connect(":memory:") as connection:
            connection.row_factory = sqlite3.Row
            connection.executescript(SCHEMA)
            connection.execute("INSERT INTO sources(id,name,root_path) VALUES (1,'Synthetic','/synthetic')")
            self.assertTrue(session_revision_contract_current(connection))
            for revision in (None, 1, 13):
                connection.execute("DELETE FROM source_files")
                connection.execute(
                    "INSERT INTO source_files(source_id,path,size_bytes,mtime_ns,last_scanned_at,session_contract_version) "
                    "VALUES (1,'/synthetic',0,0,'fixed',?)", (revision,),
                )
                stored = connection.execute("SELECT session_contract_version FROM source_files").fetchone()[0]
                self.assertEqual(stored, revision)
            for invalid in (0, -1, 1.5, "codex-session-v12-empty-page-controls", b"12"):
                with self.subTest(invalid=invalid), self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("UPDATE source_files SET session_contract_version=?", (invalid,))

    def test_unknown_or_provider_mismatched_tokens_fail_without_mutation(self):
        for token in ("codex-session-v999-future", "claude-session-v7-message-phases", "12"):
            with self.subTest(token=token), legacy_connection() as connection:
                insert_file(connection, token)
                before = list(connection.iterdump())
                with self.assertRaisesRegex(RuntimeError, "Unrecognized Session revision"):
                    prepare_session_revision_migration(connection, ":memory:")
                self.assertEqual(list(connection.iterdump()), before)
                with self.assertRaisesRegex(RuntimeError, "Unrecognized Session revision"):
                    migrate_session_revisions(connection)
                self.assertEqual(list(connection.iterdump()), before)

    def test_unexpected_trigger_rolls_back_and_preserves_original_table(self):
        with legacy_connection() as connection:
            insert_file(connection, "codex-session-v12-empty-page-controls")
            connection.execute("CREATE TRIGGER keep_source_files AFTER UPDATE ON source_files BEGIN SELECT 1; END")
            before = list(connection.iterdump())
            with self.assertRaisesRegex(RuntimeError, "Unexpected source-file trigger"):
                migrate_session_revisions(connection)
            self.assertEqual(list(connection.iterdump()), before)

    def test_unrecognized_same_column_constraints_and_affinities_are_not_discarded(self):
        legacy = SCHEMA.replace("session_contract_version INTEGER " + REVISION_CHECK,
                                "session_contract_version TEXT")
        variants = (
            legacy.replace("UNIQUE(source_id, path)", "UNIQUE(source_id, path), UNIQUE(path)", 1),
            legacy.replace("session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL",
                           "session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE", 1),
            legacy.replace("size_bytes INTEGER NOT NULL", "size_bytes TEXT NOT NULL", 1),
            legacy.replace("size_bytes INTEGER NOT NULL", "size_bytes INTEGER NOT NULL CHECK(size_bytes > 0)", 1),
            legacy.replace("session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL",
                           "session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED", 1),
        )
        for schema in variants:
            with self.subTest(schema=schema[:40]), sqlite3.connect(":memory:") as connection:
                connection.row_factory = sqlite3.Row
                connection.executescript(schema)
                before = list(connection.iterdump())
                with self.assertRaisesRegex(RuntimeError, "Unexpected source-file"):
                    migrate_session_revisions(connection)
                self.assertEqual(list(connection.iterdump()), before)

    def test_failure_after_old_table_drop_rolls_back_all_rows_and_schema(self):
        class InterruptedConnection(sqlite3.Connection):
            interrupt = False

            def execute(self, sql, *args, **kwargs):
                if self.interrupt and sql.startswith("ALTER TABLE source_files_numeric_revision RENAME"):
                    raise sqlite3.OperationalError("synthetic interruption")
                return super().execute(sql, *args, **kwargs)

        with legacy_connection(factory=InterruptedConnection) as connection:
            insert_file(connection, "codex-session-v12-empty-page-controls")
            connection.commit()
            before = list(connection.iterdump())
            connection.interrupt = True
            with self.assertRaisesRegex(sqlite3.OperationalError, "synthetic interruption"):
                migrate_session_revisions(connection)
            self.assertEqual(list(connection.iterdump()), before)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_unknown_incoming_foreign_key_cannot_cascade_away_child_data(self):
        for target in ("source_files", "SOURCE_FILES", "Source_Files"):
            with legacy_connection() as connection:
                insert_file(connection, "codex-session-v12-empty-page-controls")
                connection.execute("CREATE TABLE synthetic_child(file_id INTEGER REFERENCES {}(id) ON DELETE CASCADE)".format(target))
                connection.execute("INSERT INTO synthetic_child VALUES (1)")
                before = list(connection.iterdump())
                with self.assertRaisesRegex(RuntimeError, "Unexpected source-file references"):
                    migrate_session_revisions(connection)
                self.assertEqual(list(connection.iterdump()), before)

    def test_startup_migrates_with_valid_original_backup_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "localbrain.db"
            connection = legacy_connection(path)
            insert_file(connection, "codex-session-v12-empty-page-controls")
            connection.commit()
            connection.close()
            settings = Settings(data_dir=path.parent, database_path=path,
                                context_root=path.parent / "context",
                                claude_root=path.parent / "claude",
                                codex_root=path.parent / "codex",
                                mcp_call_budget=20, timezone_name="UTC")
            with patch.object(db, "settings", settings):
                db.init_db()
                backup = path.with_name(path.name + BACKUP_SUFFIX)
                self.assertTrue(backup.is_file())
                with sqlite3.connect(str(backup)) as original:
                    self.assertEqual(original.execute("PRAGMA quick_check").fetchall(), [("ok",)])
                    self.assertEqual(original.execute("SELECT session_contract_version FROM source_files").fetchone()[0], "codex-session-v12-empty-page-controls")
                stamp = backup.stat().st_mtime_ns
                db.init_db()
                self.assertEqual(backup.stat().st_mtime_ns, stamp)
                with db.connect() as current:
                    self.assertEqual(current.execute("SELECT session_contract_version FROM source_files").fetchone()[0], 12)
                    self.assertTrue(db.migration_contracts_current(current))

    def test_future_numeric_revision_survives_constraint_rebuild(self):
        with sqlite3.connect(":memory:") as connection:
            connection.row_factory = sqlite3.Row
            connection.executescript(SCHEMA.replace("INTEGER " + REVISION_CHECK, "INTEGER"))
            connection.execute("INSERT INTO sources(id,name,root_path) VALUES (1,'Synthetic','/synthetic')")
            connection.execute("INSERT INTO source_files(source_id,path,size_bytes,mtime_ns,last_scanned_at,session_contract_version) VALUES (1,'/synthetic',0,0,'fixed',13)")
            migrate_session_revisions(connection)
            self.assertEqual(connection.execute("SELECT session_contract_version FROM source_files").fetchone()[0], 13)
            self.assertTrue(session_revision_contract_current(connection))
