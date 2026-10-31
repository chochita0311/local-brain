"""First-run settings persistence through the real shared application lifecycle."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from localbrain.foundation.config import _system_timezone_name


class PreferencesStartupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="localbrain-preferences-startup-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def start_backend(self, data, edition):
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith("LOCALBRAIN_")}
        environment.update({
            "LOCALBRAIN_EDITION": edition,
            "LOCALBRAIN_DATA_DIR": str(data),
            "LOCALBRAIN_CACHE_DIR": str(data.parent / "cache"),
            "LOCALBRAIN_DEVELOPMENT_DIR": str(data.parent / "development"),
            "LOCALBRAIN_CONTEXT_ROOT": str(data.parent / "context"),
            "LOCALBRAIN_CLAUDE_ROOT": str(data.parent / "claude"),
            "LOCALBRAIN_CODEX_ROOT": str(data.parent / "codex"),
            "LOCALBRAIN_STARTUP_SCREEN": "context",
            "LOCALBRAIN_TIMEZONE": "invalid-old-value",
            "LOCALBRAIN_SESSION_SYNC_ENABLED": "false",
            "LOCALBRAIN_SESSION_SYNC_MINUTES": "60",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        })
        code = "import asyncio, json\nfrom localbrain.main import app\nfrom localbrain.app.lifecycle import lifespan\nfrom localbrain.foundation.preferences import PreferencesError, read_preferences\n\nasync def run():\n    async with lifespan(app):\n        try:\n            result = {'preferences': read_preferences(), 'error': None}\n        except PreferencesError as error:\n            result = {'preferences': None, 'error': str(error)}\n        result['sync'] = app.state.session_sync.status()\n        result['context_sync'] = app.state.context_sync.status()\n        print(json.dumps(result), flush=True)\nasyncio.run(run())\n"
        result = subprocess.run([sys.executable, "-c", code], env=environment,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_first_start_creates_defaults_and_restarts_preserve_saved_values(self):
        expected = {"startup_screen": "sessions", "timezone": _system_timezone_name(),
                    "session_sync_enabled": True, "session_sync_minutes": 10,
                    "context_sync_enabled": True, "context_sync_minutes": 30,
                    "onboarding_completed": False}
        for edition in ("web", "desktop"):
            with self.subTest(edition=edition):
                data = self.root / edition / "data"
                path = data / "settings.toml"
                self.assertFalse(data.exists())
                result = self.start_backend(data, edition)
                self.assertIsNone(result["error"])
                self.assertTrue(path.is_file())
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(data.stat().st_mode & 0o777, 0o700)
                self.assertEqual(result["preferences"]["saved"], expected)
                self.assertEqual(result["preferences"]["effective"], expected)
                self.assertEqual(result["preferences"]["raw"], {"schema_version": 1, **expected})
                self.assertEqual(set(result["preferences"]["source"].values()), {"saved"})
                self.assertEqual(result["sync"]["minutes"], 10)
                self.assertTrue(result["sync"]["enabled"])
                self.assertEqual(result["context_sync"]["minutes"], 30)
                self.assertTrue(result["context_sync"]["enabled"])

                content, modified = path.read_bytes(), path.stat().st_mtime_ns
                self.assertEqual(self.start_backend(data, edition)["preferences"], result["preferences"])
                self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), (content, modified))

                path.write_text('schema_version = 1\nstartup_screen = "sessions-dashboard"\n'
                                'timezone = "UTC"\nsession_sync_minutes = 30\n'
                                'session_sync_enabled = false\nonboarding_completed = true\n'
                                'future_note = "keep"\n')
                content, modified = path.read_bytes(), path.stat().st_mtime_ns
                result = self.start_backend(data, edition)
                saved = {**expected, "startup_screen": "sessions-dashboard", "timezone": "UTC",
                         "session_sync_minutes": 30, "session_sync_enabled": False,
                         "onboarding_completed": True}
                self.assertEqual(result["preferences"]["effective"], saved)
                self.assertEqual(result["preferences"]["raw"]["future_note"], "keep")
                self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), (content, modified))
                self.assertEqual(result["sync"]["minutes"], 30)
                self.assertFalse(result["sync"]["enabled"])

    def test_startup_preserves_partial_malformed_and_future_files(self):
        for edition in ("web", "desktop"):
            for name, content in (("partial", 'schema_version = 1\nsession_sync_minutes = 30\n'),
                                  ("malformed", 'bad ['), ("future", 'schema_version = 2\n')):
                with self.subTest(edition=edition, file=name):
                    data = self.root / edition / name / "data"
                    data.mkdir(parents=True)
                    path = data / "settings.toml"
                    path.write_text(content)
                    modified = path.stat().st_mtime_ns
                    result = self.start_backend(data, edition)
                    self.assertEqual((path.read_text(), path.stat().st_mtime_ns), (content, modified))
                    if name == "partial":
                        self.assertIsNone(result["error"])
                        self.assertEqual(result["preferences"]["effective"]["session_sync_minutes"], 30)
                        self.assertEqual(result["preferences"]["effective"]["startup_screen"], "sessions")
                        self.assertEqual(result["preferences"]["source"]["startup_screen"], "default")
                        self.assertEqual(result["preferences"]["source"]["session_sync_minutes"], "saved")
                    else:
                        self.assertIsNone(result["preferences"])
                        self.assertTrue(result["error"])


if __name__ == "__main__":
    unittest.main()
