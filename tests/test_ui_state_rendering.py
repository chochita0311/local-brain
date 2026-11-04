"""Synthetic witnesses for first-state values, recovery and Run output meaning."""

import html
import re
import sqlite3
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from starlette.requests import Request

from localbrain.maintenance import web as maintenance_web
from test_ui_contract import template_environment


ROOT = Path(__file__).parents[1]


class UiStateRenderingTests(unittest.TestCase):
    def setUp(self):
        self.preferences = {
            "startup_screen": "context", "timezone": "Europe/Paris",
            "session_sync_enabled": False, "session_sync_minutes": 40,
            "context_sync_enabled": True, "context_sync_minutes": 90,
            "onboarding_completed": True,
        }
        self.env = template_environment()
        self.env.autoescape = True
        self.env.globals.update(local_preferences=lambda: self.preferences, app_version="0.0.1")
        self.request = Request({"type": "http", "scheme": "http", "server": ("127.0.0.1", 8000),
                                "path": "/settings", "query_string": b"", "headers": []})

    def render(self, name, context=None):
        return self.env.get_template(name).render({"request": self.request, **(context or {})})

    def test_initial_settings_show_resolved_custom_preferences_but_lock_actions(self):
        rendered = self.render("settings.html")
        for name, value in (("startup_screen", "context"), ("timezone", "Europe/Paris"),
                            ("session_sync_choice", "off"), ("context_sync_choice", "90")):
            self.assertRegex(rendered, rf'<input\b[^>]*name="{name}"[^>]*value="{value}"')
        self.assertIn('data-select-value>Local Context</span>', rendered)
        self.assertIn('data-select-value>Europe/Paris</span>', rendered)
        self.assertIn('data-select-value>끄기</span>', rendered)
        self.assertIn('data-select-value>90분</span>', rendered)
        buttons = re.findall(r'<button\b[^>]*data-model-action[^>]*>', rendered)
        self.assertEqual(len(buttons), 4)
        self.assertTrue(all(re.search(r'\bdisabled\b', button) for button in buttons))

    def test_setup_recovery_exists_before_scripts_and_preserves_explicit_url_scope(self):
        request = Request({"type": "http", "scheme": "http", "server": ("127.0.0.1", 8000),
                           "path": "/sessions", "query_string": b"setup=1&source=2", "headers": []})
        rendered = self.render("settings.html", {"request": request})
        self.assertIn('class="app-shell" inert', rendered)
        self.assertIn('data-settings-startup', rendered)
        self.assertIn('href="http://127.0.0.1:8000/sessions?setup=1&amp;source=2"', rendered)
        self.assertIn('다시 불러오기</a>', rendered)
        self.assertNotIn('data-settings-startup', self.render("settings.html"))

    def test_initial_and_polled_run_output_distinguish_each_lifecycle_without_reexecution(self):
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.row_factory = sqlite3.Row
        connection.executescript((ROOT / "src/localbrain/schema.sql").read_text())
        connection.execute("INSERT INTO workstreams(id,name) VALUES (1,'Synthetic work')")
        connection.execute("""INSERT INTO maintenance_runs(id,workstream_id,task_type,status)
                              VALUES ('synthetic',1,'organize_resources','queued')""")
        templates = SimpleNamespace(TemplateResponse=lambda request, name, context: self.render(name, context))
        for status in ("prepared", "queued", "running", "cancelling", "completed", "partial", "failed", "cancelled", "interrupted"):
            with self.subTest(status=status), patch.object(maintenance_web, "connect", return_value=connection), \
                    patch.object(maintenance_web, "templates", templates):
                connection.execute("UPDATE maintenance_runs SET status=?", (status,))
                snapshot = maintenance_web.api_run_status("synthetic")["run"]
                rendered = maintenance_web.show_run(self.request, "synthetic")
                output = html.unescape(re.search(r'<pre[^>]*data-run-output[^>]*>(.*?)</pre>', rendered, re.S)[1])
                self.assertEqual(snapshot["output"], "")
                self.assertEqual(output, snapshot["output_placeholder"])
                self.assertEqual("준비" in output, status == "queued")
                self.assertEqual(connection.execute("SELECT status FROM maintenance_runs").fetchone()[0], status)

    def test_real_run_output_is_literal_and_never_replaced_by_empty_placeholder(self):
        output = "A synthetic result <not HTML>\n\nnext line"
        rendered = self.render("run.html", {"run": {"id": "synthetic", "status": "completed"},
                                           "candidate_counts": {}, "output": output,
                                           "output_placeholder": "표시할 실행 출력이 없습니다."})
        content = html.unescape(re.search(r'<pre[^>]*data-run-output[^>]*>(.*?)</pre>', rendered, re.S)[1])
        self.assertEqual(content, output)
        self.assertIn('data-output-empty="false"', rendered)
