import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.config import Settings
from localbrain.session_sources import (
    load_session_source_settings,
    reconcile_session_source_settings,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class SessionSourceSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.data_dir = self.root / "runtime"
        self.claude_root = self.root / "claude"
        self.codex_root = self.root / "codex"
        self.claude_root.mkdir()
        self.codex_root.mkdir()
        self.settings = self._settings()
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    def tearDown(self):
        self.connection.close()
        self.temporary.cleanup()

    def _settings(self, **overrides):
        values = {
            "data_dir": self.data_dir,
            "database_path": self.data_dir / "localbrain.db",
            "context_root": self.root / "context",
            "claude_root": self.claude_root,
            "codex_root": self.codex_root,
            "mcp_call_budget": 20,
            "timezone_name": "UTC",
            "session_sources_path": self.data_dir / "session-sources.toml",
        }
        values.update(overrides)
        return Settings(**values)

    def _write(self, value: str):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings.session_sources_path.write_text(value, encoding="utf-8")

    def test_missing_file_bootstraps_three_peers_atomically_and_privately(self):
        result = load_session_source_settings(self.settings)

        self.assertTrue(result.bootstrapped)
        self.assertFalse(result.file_error)
        self.assertEqual(
            [(entry.source_key, entry.provider_kind) for entry in result.entries],
            [("claude", "claude"), ("codex", "codex"), ("codex-company", "codex")],
        )
        self.assertEqual(result.entries[0].root, self.claude_root)
        self.assertEqual(result.entries[1].root, self.codex_root)
        self.assertEqual(
            result.entries[2].root, Path.home() / ".codex-company" / "sessions"
        )
        self.assertEqual(
            self.settings.session_sources_path.stat().st_mode & 0o777, 0o600
        )
        self.assertFalse(list(self.data_dir.glob(".session-sources-*.tmp")))

    def test_established_file_wins_over_later_legacy_root_values(self):
        first = load_session_source_settings(self.settings)
        original = self.settings.session_sources_path.read_bytes()
        changed = self._settings(
            claude_root=self.root / "changed-claude",
            codex_root=self.root / "changed-codex",
        )

        second = load_session_source_settings(changed)

        self.assertFalse(second.bootstrapped)
        self.assertEqual(self.settings.session_sources_path.read_bytes(), original)
        self.assertEqual(second.entries[0].root, first.entries[0].root)
        self.assertEqual(second.entries[1].root, first.entries[1].root)

    def test_malformed_file_and_duplicate_keys_cannot_mutate_registry(self):
        self.connection.execute(
            """
            INSERT INTO sources(kind, provider_kind, name, root_path)
            VALUES ('codex', 'codex', 'Codex', '/retained/codex')
            """
        )
        self._write("schema_version = 1\nschema_version = 1\n")

        loaded = load_session_source_settings(self.settings)
        reconciled = reconcile_session_source_settings(self.connection, loaded)

        self.assertTrue(loaded.file_error)
        self.assertEqual(loaded.diagnostics[0].code, "invalid_toml")
        self.assertFalse(reconciled.registrations)
        self.assertEqual(
            dict(self.connection.execute("SELECT * FROM sources").fetchone())["root_path"],
            "/retained/codex",
        )

    def test_entry_errors_do_not_block_independent_unavailable_registration(self):
        missing = self.root / "missing-company"
        invalid_file = self.root / "not-a-directory"
        invalid_file.write_text("x", encoding="utf-8")
        self._write(
            """schema_version = 1

[[session_sources]]
source_key = "codex-company"
display_label = "Codex Company"
provider_kind = "codex"
root = "{}"

[[session_sources]]
source_key = "bad-provider"
display_label = "Bad"
provider_kind = "gemini"
root = "{}"

[[session_sources]]
source_key = "bad-file"
display_label = "Bad File"
provider_kind = "codex"
root = "{}"
""".format(missing, self.root / "other", invalid_file)
        )

        loaded = load_session_source_settings(self.settings)
        reconciled = reconcile_session_source_settings(self.connection, loaded)

        self.assertFalse(loaded.file_error)
        self.assertEqual([entry.source_key for entry in loaded.entries], ["codex-company"])
        self.assertEqual(loaded.entries[0].availability, "unavailable")
        self.assertEqual(
            [item.code for item in loaded.diagnostics],
            ["unsupported_provider", "root_not_directory"],
        )
        self.assertEqual(reconciled.registrations[0].status, "unavailable")
        row = self.connection.execute(
            "SELECT kind, provider_kind, root_path FROM sources"
        ).fetchone()
        self.assertEqual(
            dict(row),
            {
                "kind": "codex-company",
                "provider_kind": "codex",
                "root_path": str(missing),
            },
        )

    def test_duplicate_source_key_is_file_error_and_duplicate_root_rejects_both(self):
        duplicate_key = """schema_version = 1
[[session_sources]]
source_key = "codex"
display_label = "One"
provider_kind = "codex"
root = "/one"
[[session_sources]]
source_key = "codex"
display_label = "Two"
provider_kind = "codex"
root = "/two"
"""
        self._write(duplicate_key)
        keyed = load_session_source_settings(self.settings)
        self.assertTrue(keyed.file_error)
        self.assertEqual(keyed.diagnostics[0].code, "duplicate_source_key")

        self._write(
            """schema_version = 1
[[session_sources]]
source_key = "codex"
display_label = "Codex"
provider_kind = "codex"
root = "shared"
[[session_sources]]
source_key = "codex-company"
display_label = "Company"
provider_kind = "codex"
root = "shared"
"""
        )
        rooted = load_session_source_settings(self.settings)
        self.assertFalse(rooted.file_error)
        self.assertFalse(rooted.entries)
        self.assertEqual(
            [(item.source_key, item.code) for item in rooted.diagnostics],
            [("codex", "duplicate_root"), ("codex-company", "duplicate_root")],
        )

    def test_unreadable_root_is_an_entry_local_error(self):
        unreadable = self.root / "unreadable"
        unreadable.mkdir()
        self._write(
            """schema_version = 1
[[session_sources]]
source_key = "codex-company"
display_label = "Codex Company"
provider_kind = "codex"
root = "{}"
""".format(unreadable)
        )

        with patch("localbrain.session_sources.os.access", return_value=False):
            loaded = load_session_source_settings(self.settings)

        self.assertFalse(loaded.file_error)
        self.assertFalse(loaded.entries)
        self.assertEqual(loaded.diagnostics[0].code, "root_unreadable")

    def test_provider_root_and_omission_conflicts_preserve_existing_data(self):
        claude_id = self.connection.execute(
            """
            INSERT INTO sources(kind, provider_kind, name, root_path)
            VALUES ('claude', 'claude', 'Claude', '/retained/claude')
            """
        ).lastrowid
        codex_id = self.connection.execute(
            """
            INSERT INTO sources(kind, provider_kind, name, root_path)
            VALUES ('codex', 'codex', 'Codex', '/retained/codex')
            """
        ).lastrowid
        self.connection.execute(
            """
            INSERT INTO sessions(source_id, external_id, source_path, title)
            VALUES (?, 'retained-session', '/retained/codex/session.jsonl', 'Retained')
            """,
            (codex_id,),
        )
        self._write(
            """schema_version = 1
[[session_sources]]
source_key = "codex"
display_label = "Changed Codex"
provider_kind = "codex"
root = "/mistyped/codex"
[[session_sources]]
source_key = "claude"
display_label = "Wrong Claude"
provider_kind = "codex"
root = "/retained/claude"
"""
        )

        reconciled = reconcile_session_source_settings(
            self.connection, load_session_source_settings(self.settings)
        )

        self.assertEqual(
            [(item.source_key, item.status) for item in reconciled.registrations],
            [("codex", "root_change_conflict"), ("claude", "identity_conflict")],
        )
        rows = self.connection.execute(
            "SELECT id, kind, provider_kind, name, root_path FROM sources ORDER BY id"
        ).fetchall()
        self.assertEqual(rows[0]["id"], claude_id)
        self.assertEqual(rows[0]["name"], "Claude")
        self.assertEqual(rows[1]["id"], codex_id)
        self.assertEqual(rows[1]["root_path"], "/retained/codex")
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 1
        )

        self._write("schema_version = 1\nsession_sources = []\n")
        omitted = reconcile_session_source_settings(
            self.connection, load_session_source_settings(self.settings)
        )
        self.assertEqual(
            [(item.source_key, item.status) for item in omitted.registrations],
            [("claude", "config_missing"), ("codex", "config_missing")],
        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 1
        )

    def test_root_change_without_descendants_updates_same_source_id(self):
        source_id = self.connection.execute(
            """
            INSERT INTO sources(kind, provider_kind, name, root_path)
            VALUES ('codex-company', 'codex', 'Old', '/old')
            """
        ).lastrowid
        new_root = self.root / "new-company"
        new_root.mkdir()
        self._write(
            """schema_version = 1
[[session_sources]]
source_key = "codex-company"
display_label = "Codex Company"
provider_kind = "codex"
root = "{}"
""".format(new_root)
        )

        reconciled = reconcile_session_source_settings(
            self.connection, load_session_source_settings(self.settings)
        )

        self.assertEqual(reconciled.registrations[0].source_id, source_id)
        self.assertEqual(reconciled.registrations[0].status, "ready")
        row = self.connection.execute(
            "SELECT name, root_path FROM sources WHERE id = ?", (source_id,)
        ).fetchone()
        self.assertEqual(dict(row), {"name": "Codex Company", "root_path": str(new_root)})


if __name__ == "__main__":
    unittest.main()
