"""Synthetic storage totals distinguish retained bytes from missing evidence."""

import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from localbrain.app.storage.accounting import directory_size, volume_status
from localbrain.app.storage.recovery import storage_status


class StorageAccountingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_logical_bytes_deduplicate_hardlinks_and_skip_nested_symlinks(self):
        folder = self.root / "data"; folder.mkdir()
        original = folder / "record"; original.write_bytes(b"12345")
        os.link(original, folder / "same-record")
        outside = self.root / "outside"; outside.mkdir()
        (outside / "private-original").write_bytes(b"should not be counted")
        (folder / "external").symlink_to(outside, target_is_directory=True)
        (folder / "shortcut").symlink_to(original)
        self.assertEqual(directory_size(folder), {"bytes": 5, "state": "complete"})
        selected = self.root / "configured-link"; selected.symlink_to(folder, target_is_directory=True)
        self.assertEqual(directory_size(selected), {"bytes": 5, "state": "complete"})
        self.assertEqual((outside / "private-original").read_bytes(), b"should not be counted")

    def test_missing_unreadable_and_partial_are_distinct(self):
        self.assertEqual(directory_size(self.root / "future"), {"bytes": 0, "state": "missing"})
        with patch.object(Path, "stat", side_effect=PermissionError("synthetic")):
            self.assertEqual(directory_size(self.root), {"bytes": None, "state": "unavailable"})
        (self.root / "readable").write_bytes(b"123")
        def partial_walk(root, *, followlinks, onerror):
            onerror(PermissionError("synthetic inaccessible subdirectory"))
            yield str(root), [], ["readable"]
        with patch("localbrain.app.storage.accounting.os.walk", partial_walk):
            self.assertEqual(directory_size(self.root), {"bytes": 3, "state": "partial"})

    def test_future_location_uses_existing_volume_and_denial_is_not_zero(self):
        with patch("localbrain.app.storage.accounting.shutil.disk_usage", return_value=SimpleNamespace(free=1234)) as usage:
            result = volume_status(self.root / "future" / "nested")
        self.assertEqual(result["free_bytes"], 1234)
        self.assertEqual(result["id"], str(self.root.stat().st_dev))
        usage.assert_called_once_with(self.root)
        with patch("localbrain.app.storage.accounting.shutil.disk_usage", side_effect=PermissionError("synthetic")):
            self.assertEqual(volume_status(self.root), {"id": None, "free_bytes": None, "state": "unavailable"})

    def test_status_preserves_overrides_and_per_location_volumes(self):
        config = SimpleNamespace(data_dir=self.root / "data", cache_dir=self.root / "private-cache")
        model = self.root / "shared-hub"
        def inspect(path):
            different = path == model
            return {"bytes": None if different else 8, "state": "unavailable" if different else "complete",
                    "volume": {"id": "models" if different else "app", "free_bytes": 20 if different else 10, "state": "complete"}}
        with patch("localbrain.foundation.paths.hub_cache_root", return_value=model), patch("localbrain.app.storage.recovery.location_status", side_effect=inspect):
            result = storage_status(config)
        self.assertEqual(result["models"], str(model))
        self.assertEqual(result["cache"], str(config.cache_dir))
        self.assertIsNone(result["models_bytes"])
        self.assertEqual(result["locations"]["data"]["volume"]["free_bytes"], 10)
        self.assertEqual(result["locations"]["models"]["volume"]["free_bytes"], 20)
        self.assertFalse(config.data_dir.exists())


if __name__ == "__main__":
    unittest.main()
