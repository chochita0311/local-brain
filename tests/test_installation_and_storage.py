"""Synthetic standalone setup, cache reuse, and bounded recovery lifecycle."""

import hashlib
import fcntl
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from localbrain.model_installation import (
    EMBEDDING_ASSETS, EMBEDDING_ID, EMBEDDING_REVISION, install_embedding, model_root,
)
from localbrain.runtime_storage import (
    MIGRATION_BACKUP_SUFFIXES, StorageError, maintain_migration_backups,
    private_database, private_directory,
)
from localbrain.storage_layout import maintain_derived_cache, migrate_storage
from localbrain.session_simulation_model import verified_assets


class InstallationStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="localbrain-install-test-", dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.database = self.root / "data" / "localbrain.db"
        private_database(self.database)
        self.connection = sqlite3.connect(self.database)
        self.connection.row_factory = sqlite3.Row
        self.addCleanup(self.connection.close)

    def backup(self, suffix_index, age_days=0):
        path = self.database.with_name(self.database.name + MIGRATION_BACKUP_SUFFIXES[suffix_index])
        path.write_bytes(b"synthetic recovery copy")
        modified = time.time() - age_days * 86400
        os.utime(path, (modified, modified))
        return path

    def maintain(self, **kwargs):
        with patch("localbrain.db.migration_contracts_current", return_value=True):
            return maintain_migration_backups(self.database, self.connection, **kwargs)

    def test_private_runtime_permissions(self):
        self.assertEqual(self.database.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.database.stat().st_mode & 0o777, 0o600)

    def test_runtime_inside_any_git_worktree_is_rejected(self):
        repo = self.root / "unrelated-repository"
        repo.mkdir()
        (repo / ".git").write_text("gitdir: /synthetic")
        with self.assertRaisesRegex(StorageError, "IN_REPOSITORY"):
            private_database(repo / "data" / "localbrain.db")
        self.assertFalse((repo / "data").exists())

    def test_symlink_runtime_root_and_hardlink_database_are_rejected(self):
        link = self.root / "link"
        link.symlink_to(self.database.parent, target_is_directory=True)
        with self.assertRaises(StorageError):
            private_directory(link)
        second = self.root / "duplicate.db"
        os.link(self.database, second)
        with self.assertRaisesRegex(StorageError, "UNOWNED_DATABASE"):
            private_database(self.database)

    def test_retirement_keeps_only_newest_recent_copy(self):
        older = self.backup(0, 2)
        newest = self.backup(1, 1)
        result = self.maintain()
        self.assertFalse(older.exists())
        self.assertTrue(newest.exists())
        self.assertTrue(self.database.exists())
        self.assertEqual(result["removed_files"], 1)

    def test_expired_copy_and_its_empty_helpers_are_removed(self):
        backup = self.backup(0, 8)
        wal, shm = Path(str(backup) + "-wal"), Path(str(backup) + "-shm")
        wal.write_bytes(b"")
        shm.write_bytes(b"synthetic helper")
        result = self.maintain()
        self.assertFalse(any(path.exists() for path in (backup, wal, shm)))
        self.assertEqual(result["removed_files"], 3)

    def test_preview_does_not_delete(self):
        backup = self.backup(0, 30)
        result = self.maintain(apply=False)
        self.assertTrue(backup.exists())
        self.assertEqual(result["eligible_files"], 1)
        self.assertEqual(result["removed_files"], 0)

    def test_open_nonempty_wal_unknown_and_linked_copies_are_preserved(self):
        open_copy = self.backup(0, 30)
        wal_copy = self.backup(1, 30)
        Path(str(wal_copy) + "-wal").write_bytes(b"pending transaction")
        linked_copy = self.backup(2, 30)
        os.link(linked_copy, self.root / "external-copy")
        unknown = self.database.with_name("manual-backup.db")
        unknown.write_bytes(b"synthetic manual backup")
        with open_copy.open("rb"):
            self.maintain()
        self.assertTrue(all(path.exists() for path in (open_copy, wal_copy, linked_copy, unknown)))

    def test_uncertain_activity_or_incomplete_migrations_preserve_recovery(self):
        backup = self.backup(0, 30)
        with patch("localbrain.runtime_storage.inactive_files", return_value=False):
            self.maintain()
        self.assertTrue(backup.exists())
        with patch("localbrain.db.migration_contracts_current", return_value=False):
            maintain_migration_backups(self.database, self.connection)
        self.assertTrue(backup.exists())

    def test_legacy_metadata_is_reused_and_new_paths_are_grouped(self):
        data = self.root / "app"
        self.assertEqual(model_root("4b", data), data / "models" / "qwen3-4b")
        legacy = data / "qwen3-4b"
        legacy.mkdir(parents=True)
        self.assertEqual(model_root("4b", data), legacy)

    def test_owned_embedding_setup_is_offline_and_relocatable(self):
        hub = self.root / "public-hub"
        snapshot = hub / ("models--" + EMBEDDING_ID.replace("/", "--")) / "snapshots" / EMBEDDING_REVISION
        snapshot.mkdir(parents=True)
        files = []
        for name in sorted(EMBEDDING_ASSETS):
            path = snapshot / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic public asset")
            files.append({"path": name, "size": path.stat().st_size,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        fingerprint = hashlib.sha256((json.dumps(files, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()).hexdigest()
        metadata = self.root / "app-models" / "embedding"
        with patch.dict(os.environ, {"HF_HUB_CACHE": str(hub)}), \
             patch("localbrain.model_installation.EMBEDDING_FINGERPRINT", fingerprint), \
             patch("localbrain.session_simulation_model.EMBEDDING_FINGERPRINT", fingerprint):
            with patch.dict(sys.modules, {"huggingface_hub": None}):
                install_embedding(metadata, local_only=True)
                install_embedding(metadata, local_only=True)
            self.assertEqual({p.name for p in metadata.iterdir()}, {"owner.json", "install.lock", "model.json"})
            manifest = json.loads((metadata / "model.json").read_text())
            self.assertEqual(manifest["schema"], "localbrain.semantic-model/v1")
            self.assertFalse(Path(manifest["snapshot"]).is_absolute())
            moved = self.root / "moved-public-hub"
            hub.rename(moved)
            os.environ["HF_HUB_CACHE"] = str(moved)
            self.assertEqual(verified_assets(metadata / "model.json")[1]["fingerprint"], fingerprint)

    def test_doctor_reads_no_sources_and_creates_no_runtime_state(self):
        target = self.root / "uninitialized"
        result = subprocess.run([sys.executable, "-B", "-m", "localbrain.cli", "doctor"],
                                env={**os.environ, "LOCALBRAIN_DATA_DIR": str(target)},
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)["platform"], "Darwin")
        self.assertFalse(target.exists())
        self.assertNotIn(str(self.root), result.stdout)


class StorageLayoutTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="localbrain-layout-test-", dir="/private/tmp")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.config = SimpleNamespace(data_dir=self.root / "data", cache_dir=self.root / "cache",
                                      development_dir=self.root / "development")
        private_directory(self.config.data_dir)
        self.now = datetime(2050, 1, 1, tzinfo=timezone.utc)
        self.database = self.config.data_dir / "localbrain.db"
        self.database.write_bytes(b"synthetic primary database")

    def write(self, path, content):
        path.write_bytes(content)
        path.chmod(0o600)

    def simulation(self, base, *, expired=True):
        from localbrain.session_simulation import OWNER
        private_directory(base)
        folder = private_directory(base / "session-simulation")
        expires = self.now + timedelta(days=-1 if expired else 1)
        self.write(folder / "owner.json", json.dumps({"owner": OWNER, "database": "a" * 64,
                                                     "expires_at": expires.isoformat()}).encode())
        self.write(folder / "writer.lock", b"")
        self.write(folder / "state.sqlite3", b"synthetic private vectors")
        self.write(folder / "progress.json", b'{"state":"complete"}')
        return folder

    def development(self):
        from localbrain.work_context_evaluation import OWNER
        folder = private_directory(self.config.data_dir / "work-context-synthetic-development")
        self.write(folder / "owner.json", json.dumps({"owner": OWNER}).encode())
        self.write(folder / "report.json", b'{"synthetic":true}')
        return folder

    def test_preview_and_apply_preserve_content_modification_times_and_primary_data(self):
        source = self.simulation(self.config.data_dir)
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in source.iterdir()}
        preview = migrate_storage(self.config)
        self.assertEqual(preview["eligible_directories"], 1)
        self.assertEqual(preview["moved_directories"], 0)
        self.assertFalse(self.config.cache_dir.exists())
        self.assertFalse(self.config.development_dir.exists())
        result = migrate_storage(self.config, apply=True)
        self.assertEqual(result["moved_directories"], 1)
        self.assertFalse(source.exists())
        destination = self.config.cache_dir / source.name
        for name, expected in before.items():
            path = destination / name
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), expected)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(destination.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.database.read_bytes(), b"synthetic primary database")
        self.assertEqual(migrate_storage(self.config, apply=True)["moved_directories"], 0)

    def test_development_archive_requires_explicit_inclusion(self):
        source = self.development()
        self.assertEqual(migrate_storage(self.config, apply=True)["moved_directories"], 0)
        self.assertTrue(source.exists())
        self.assertFalse(self.config.development_dir.exists())
        result = migrate_storage(self.config, apply=True, include_development=True)
        self.assertEqual(result["moved_directories"], 1)
        self.assertEqual((self.config.development_dir / source.name / "report.json").read_bytes(),
                         b'{"synthetic":true}')

    def test_destination_collision_refuses_all_moves_before_mutation(self):
        source = self.simulation(self.config.data_dir)
        development = self.development()
        private_directory(self.config.cache_dir / source.name)
        with self.assertRaisesRegex(StorageError, "DESTINATION_EXISTS"):
            migrate_storage(self.config, apply=True, include_development=True)
        self.assertTrue(source.exists())
        self.assertTrue(development.exists())
        self.assertFalse(self.config.development_dir.exists())

    def test_busy_or_changed_sources_refuse_migration(self):
        source = self.simulation(self.config.data_dir)
        with patch("localbrain.storage_layout._inactive", return_value=False):
            with self.assertRaisesRegex(StorageError, "BUSY"):
                migrate_storage(self.config, apply=True)
        with patch("localbrain.storage_layout._unchanged", side_effect=StorageError("STORAGE_CHANGED")):
            with self.assertRaisesRegex(StorageError, "CHANGED"):
                migrate_storage(self.config, apply=True)
        self.assertTrue(source.exists())
        self.assertFalse(self.config.cache_dir.exists())

    def test_unknown_files_linked_files_and_symlink_folders_are_preserved(self):
        source = self.simulation(self.config.data_dir)
        self.write(source / "unknown.txt", b"synthetic unknown content")
        self.assertEqual(migrate_storage(self.config, apply=True)["preserved_directories"], 1)
        (source / "unknown.txt").unlink()
        os.link(source / "state.sqlite3", self.root / "linked-state")
        self.assertEqual(migrate_storage(self.config, apply=True)["preserved_directories"], 1)
        (self.root / "linked-state").unlink()
        preview = self.config.data_dir / "auto-work-preview"
        preview.symlink_to(source, target_is_directory=True)
        result = migrate_storage(self.config)
        self.assertEqual(result["preserved_directories"], 1)
        self.assertEqual(result["eligible_directories"], 1)
        self.assertTrue(source.exists())

    def test_overlap_and_git_or_public_cache_destinations_are_rejected(self):
        self.config.cache_dir = self.config.data_dir
        with self.assertRaisesRegex(StorageError, "ROOTS_OVERLAP"):
            migrate_storage(self.config)
        repository = self.root / "synthetic-repository"
        repository.mkdir()
        (repository / ".git").write_text("gitdir: /synthetic")
        self.config.cache_dir = repository / "cache"
        with self.assertRaisesRegex(StorageError, "IN_REPOSITORY"):
            migrate_storage(self.config)
        self.assertFalse(self.config.cache_dir.exists())
        public = self.root / "public-models"
        self.config.cache_dir = public / "private-cache"
        with patch.dict(os.environ, {"HF_HUB_CACHE": str(public)}):
            with self.assertRaisesRegex(StorageError, "OVERLAPS_PUBLIC_MODEL_CACHE"):
                migrate_storage(self.config)
        self.assertFalse(public.exists())

    def test_expired_results_retire_after_preview_and_keep_markers_and_locks(self):
        folder = self.simulation(self.config.cache_dir)
        preview = maintain_derived_cache(self.config.cache_dir, apply=False, at=self.now)
        self.assertEqual(preview["eligible_files"], 2)
        self.assertEqual(preview["removed_files"], 0)
        self.assertTrue((folder / "state.sqlite3").exists())
        result = maintain_derived_cache(self.config.cache_dir, at=self.now)
        self.assertEqual(result["removed_files"], 2)
        self.assertEqual({p.name for p in folder.iterdir()}, {"owner.json", "writer.lock"})
        self.assertEqual(self.database.read_bytes(), b"synthetic primary database")

    def test_unexpired_unknown_and_malformed_cache_is_preserved(self):
        folder = self.simulation(self.config.cache_dir, expired=False)
        self.assertEqual(maintain_derived_cache(self.config.cache_dir, at=self.now)["removed_files"], 0)
        marker = json.loads((folder / "owner.json").read_text())
        marker["expires_at"] = (self.now - timedelta(days=1)).isoformat()
        for field, value in (("expires_at", "invalid"), ("expires_at", "2049-01-01"),
                             ("database", "z" * 64)):
            with self.subTest(field=field, value=value):
                changed = {**marker, field: value}
                self.write(folder / "owner.json", json.dumps(changed).encode())
                result = maintain_derived_cache(self.config.cache_dir, at=self.now)
                self.assertEqual(result["preserved_directories"], 1)
                self.assertTrue((folder / "state.sqlite3").exists())
        self.write(folder / "owner.json", json.dumps(marker).encode())
        self.write(folder / "unknown.txt", b"synthetic unknown content")
        self.assertEqual(maintain_derived_cache(self.config.cache_dir, at=self.now)["removed_files"], 0)
        self.assertTrue((folder / "unknown.txt").exists())

    def test_writer_lock_and_open_readers_preserve_expired_cache(self):
        folder = self.simulation(self.config.cache_dir)
        with (folder / "state.sqlite3").open("rb"):
            self.assertEqual(maintain_derived_cache(self.config.cache_dir, at=self.now)["removed_files"], 0)
        with (folder / "writer.lock").open("r+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch("localbrain.storage_layout.inactive_files", return_value=True):
                self.assertEqual(maintain_derived_cache(self.config.cache_dir, at=self.now)["removed_files"], 0)
        self.assertTrue((folder / "state.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
