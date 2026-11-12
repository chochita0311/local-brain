"""Synthetic launch defaults and the shared private preference transaction."""
import json
import os
import sys
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from jinja2 import Environment, FileSystemLoader

from localbrain.foundation.preferences import PreferencesError, read_preferences, save_preferences
from localbrain.terminal.runtime import PACKAGE
from localbrain.terminal.settings import launch_parameters, read_launch_settings, save_launch_settings
from localbrain.terminal.web import install_routes


class TerminalSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lb-td-", dir="/private/tmp" if sys.platform == "darwin" else None)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        self.config = SimpleNamespace(data_dir=self.root / "data", cache_dir=self.root / "cache", timezone_name="UTC")
        self.path = self.config.data_dir / "settings.toml"
        self.env = mock.patch.dict(os.environ, {"HOME": str(self.home), "SHELL": "/bin/sh"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def save(self, cwd=None, shell="/bin/sh", revision=None):
        return save_launch_settings(self.config, str(cwd or self.project), shell,
                                    revision or read_launch_settings(self.config)["revision"])

    def test_read_missing_defaults_does_not_create_files_or_service(self):
        actual = read_launch_settings(self.config)
        self.assertEqual(actual["cwd"], str(self.home))
        self.assertEqual(actual["shell"], "")
        self.assertEqual(actual["default_shell"], "/bin/sh")
        self.assertFalse(self.path.exists())
        self.assertFalse(self.config.cache_dir.exists())

    def test_exact_folder_and_shell_paths_are_preserved(self):
        sibling = self.root / "project with spaces "
        sibling.mkdir()
        executable = self.root / "shell "
        executable.symlink_to("/bin/sh")
        result = self.save(sibling, shell=str(executable))
        self.assertEqual(result["cwd"], str(sibling))
        self.assertEqual(result["shell"], str(executable))
        self.assertEqual(launch_parameters(self.config), {"cwd": str(sibling), "shell": str(executable)})

    def test_save_private_section_preserves_common_and_unknown_values(self):
        self.path.parent.mkdir()
        self.path.write_text('schema_version = 1\ntimezone = "Asia/Seoul"\nfuture = "keep"\n[terminal]\nfuture_terminal = 17\n')
        self.save()
        saved = read_preferences(self.config)
        self.assertEqual(saved["effective"]["timezone"], "Asia/Seoul")
        self.assertEqual(saved["raw"]["future"], "keep")
        self.assertEqual(saved["raw"]["terminal"], {"cwd": str(self.project), "shell": "/bin/sh", "future_terminal": 17})
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertFalse(self.config.cache_dir.exists())

    def test_both_settings_consumers_preserve_sections_and_reject_stale_revision(self):
        original = read_launch_settings(self.config)
        self.save(revision=original["revision"])
        with self.assertRaises(PreferencesError):
            save_preferences({"timezone": "UTC"}, original["revision"], self.config)
        current = read_preferences(self.config)
        save_preferences({"timezone": "Asia/Seoul"}, current["revision"], self.config)
        with self.assertRaises(PreferencesError):
            self.save(revision=current["revision"])
        self.assertEqual(read_launch_settings(self.config)["cwd"], str(self.project))
        self.assertEqual(read_preferences(self.config)["effective"]["timezone"], "Asia/Seoul")

    def test_blank_defaults_use_home_and_current_shell(self):
        saved = save_launch_settings(self.config, "", "", read_launch_settings(self.config)["revision"])
        self.assertEqual(saved["cwd"], str(self.home))
        self.assertEqual(saved["shell"], "")
        self.assertEqual(launch_parameters(self.config), {"cwd": str(self.home), "shell": "/bin/sh"})

    def test_bad_paths_and_types_preserve_last_saved_file(self):
        self.save()
        before = self.path.read_bytes()
        text = self.root / "not-executable"
        text.write_text("synthetic")
        invalid = [("relative", "/bin/sh"), (str(self.root / "missing"), "/bin/sh"),
                   (str(text), "/bin/sh"), (str(self.project), str(self.project)),
                   (str(self.project), str(text)), (str(self.project), "/bin/sh -l"),
                   ([], "/bin/sh"), (str(self.project), True), ("x\0y", "/bin/sh"),
                   ("~localbrain-no-such-user/", "/bin/sh")]
        for cwd, shell in invalid:
            with self.subTest(cwd=cwd, shell=shell), self.assertRaises(PreferencesError):
                save_launch_settings(self.config, cwd, shell, read_launch_settings(self.config)["revision"])
            self.assertEqual(self.path.read_bytes(), before)

    def test_deleted_default_can_be_read_for_repair_but_cannot_start_service(self):
        self.save()
        self.project.rmdir()
        self.assertEqual(read_launch_settings(self.config)["cwd"], str(self.project))
        with self.assertRaises(PreferencesError):
            launch_parameters(self.config)
        self.assertFalse(self.config.cache_dir.exists())

    def test_launch_snapshot_stays_fixed_when_preferences_change(self):
        self.save()
        first = launch_parameters(self.config)
        self.save(self.home)
        self.assertEqual(first, {"cwd": str(self.project), "shell": "/bin/sh"})
        self.assertEqual(launch_parameters(self.config), {"cwd": str(self.home), "shell": "/bin/sh"})

    def test_malformed_section_is_not_overwritten(self):
        self.path.parent.mkdir()
        self.path.write_text('schema_version = 1\nterminal = "future-format"\n')
        before = self.path.read_bytes()
        with self.assertRaises(PreferencesError):
            read_launch_settings(self.config)
        self.assertEqual(self.path.read_bytes(), before)

    def test_web_settings_need_no_manager_and_mutation_requires_origin(self):
        app = FastAPI()
        install_routes(app, None, self.config)
        app.state.terminal_factory = lambda: self.fail("settings must not construct or start a manager")
        client = TestClient(app, base_url="http://127.0.0.1:8138")
        loaded = client.get("/api/terminal/settings")
        self.assertEqual(loaded.status_code, 200)
        body = {"cwd": str(self.project), "shell": "/bin/sh", "revision": loaded.json()["revision"]}
        self.assertEqual(client.post("/api/terminal/settings", json=body).status_code, 403)
        self.assertEqual(client.post("/api/terminal/settings", json=body,
                                    headers={"origin": "https://127.0.0.1:8138"}).status_code, 403)
        response = client.post("/api/terminal/settings", json=body,
                               headers={"origin": "http://127.0.0.1:8138"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["cwd"], str(self.project))
        self.assertEqual(response.json()["preferences"]["revision"], response.json()["revision"])
        self.assertEqual(response.json()["preferences"]["saved"], read_preferences(self.config)["saved"])
        self.assertNotIn("raw", response.json()["preferences"])
        self.assertEqual(client.get("/api/terminal/settings?launch=true").json(),
                         {"cwd": str(self.project), "shell": "/bin/sh"})
        self.assertFalse(self.config.cache_dir.exists())
        self.assertEqual(client.post("/api/terminal/settings", json=body,
                                    headers={"origin": "http://127.0.0.1:8138"}).status_code, 409)
        self.project.rmdir()
        self.assertEqual(client.get("/api/terminal/settings").status_code, 200)
        self.assertEqual(client.get("/api/terminal/settings?launch=true").status_code, 409)
        self.assertFalse(self.config.cache_dir.exists())

    def test_settings_routes_absent_without_feature(self):
        from localbrain.app.application import create_app
        app = create_app(feature_packages=())
        paths = {route.path for route in app.routes}
        self.assertNotIn("/api/terminal/settings", paths)
        self.assertNotIn("/terminal", paths)

    def test_settings_pane_only_renders_when_terminal_is_available(self):
        template = Environment(loader=FileSystemLoader(PACKAGE.parent / "templates")).get_template("_settings.html")
        for available in (False, True):
            with self.subTest(available=available):
                html = template.render(terminal_available=available,
                                       preferences={"startup_screen": "sessions", "timezone": "UTC"})
                self.assertEqual('data-settings-tab="terminal"' in html, available)
                self.assertEqual('data-terminal-settings-form' in html, available)
                self.assertIn('data-general-form', html)
