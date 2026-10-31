"""First-use entry and shared wizard contracts; no real sources or downloads."""

from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from jinja2 import Environment, FileSystemLoader

from localbrain.foundation.preferences import PreferencesError
from localbrain.app.settings import install_settings_routes


ROOT = Path(__file__).parents[1]
TEMPLATES = ROOT / "src/localbrain/templates"


class OnboardingTests(unittest.TestCase):
    def test_entry_uses_each_saved_startup_surface(self):
        app = FastAPI()
        install_settings_routes(app, None)
        entry = next(route.endpoint for route in app.routes if route.path == "/onboarding")
        for screen in ("sessions", "sessions-dashboard", "context"):
            with self.subTest(screen=screen), patch("localbrain.app.settings.read_preferences",
                    return_value={"effective": {"startup_screen": screen}}):
                response = entry(None)
                self.assertEqual(response.status_code, 303)
                self.assertEqual(response.headers["location"], "/" + screen + "?setup=1")

    def test_invalid_preferences_keep_settings_recovery_available(self):
        app = FastAPI()
        install_settings_routes(app, None)
        entry = next(route.endpoint for route in app.routes if route.path == "/onboarding")
        with patch("localbrain.app.settings.read_preferences", side_effect=PreferencesError("invalid")):
            self.assertEqual(entry(None).headers["location"], "/settings")

    def render_shell(self, *, desktop, completed, page="sessions", setup=False):
        environment = Environment(loader=FileSystemLoader(TEMPLATES))
        environment.globals.update(
            url_for=lambda name, path: "/static" + path,
            local_preferences=lambda: {"timezone": "UTC", "onboarding_completed": completed},
        )
        return environment.get_template("base.html").render(
            desktop_edition=desktop, active_page=page,
            request=SimpleNamespace(query_params={"setup": "1"} if setup else {}),
        )

    def test_incomplete_desktop_shell_is_isolated_before_script_load(self):
        for page in ("sessions", "sessions-dashboard", "context"):
            html = self.render_shell(desktop=True, completed=False, page=page)
            self.assertIn('data-onboarding="true"', html)
            self.assertIn('<div class="app-shell" inert>', html)
            self.assertIn('href="#main-content" inert', html)

    def test_web_and_completed_desktop_keep_ordinary_entry(self):
        for desktop, completed in ((False, False), (False, True), (True, True)):
            html = self.render_shell(desktop=desktop, completed=completed)
            self.assertNotIn('data-onboarding="true"', html)
            self.assertNotIn('class="app-shell" inert', html)

    def test_explicit_web_entry_opens_wizard_but_settings_recovery_does_not(self):
        html = self.render_shell(desktop=False, completed=True, setup=True)
        self.assertIn('data-onboarding="true"', html)
        html = self.render_shell(desktop=True, completed=False, page="settings")
        self.assertNotIn('data-onboarding="true"', html)

    def test_wizard_reuses_one_set_of_source_context_and_model_controls(self):
        html = (TEMPLATES / "_settings.html").read_text()
        self.assertFalse((TEMPLATES / "onboarding.html").exists())
        for marker in ("<form data-source-form ", "<form data-context-form ", 'data-model-action="install"'):
            self.assertEqual(html.count(marker), 1)
        for step in ("welcome", "sessions", "context", "search"):
            self.assertIn('data-onboarding-step="' + step + '"', html)
        for action in ("back", "next", "skip", "retry"):
            self.assertIn("data-onboarding-" + action, html)
        self.assertIn('aria-label="시작 설정 단계"', html)

    def test_step_transitions_keep_explicit_saves_and_optional_models(self):
        script = (ROOT / "src/localbrain/static/settings.js").read_text()
        next_action = script.split("$('[data-onboarding-next]').addEventListener", 1)[1].split("async function pollModel", 1)[0]
        self.assertIn("hasPendingSource() && !await saveSource()", next_action)
        self.assertIn("contextForm.elements.path.value.trim() && !await saveContext()", next_action)
        self.assertNotIn("/api/settings/model/", next_action)
        skip_action = script.split("$('[data-onboarding-skip]').addEventListener", 1)[1].split("$('[data-onboarding-next]').addEventListener", 1)[0]
        self.assertNotIn("saveSource", skip_action)
        self.assertNotIn("saveContext", skip_action)
        self.assertIn("if (!sourceForm.reportValidity()) return false", script)
        self.assertIn("if (!contextForm.reportValidity()) return false", script)
        self.assertIn("return !previous.registered ||", script)

    def test_completion_confirms_persistence_before_unblocking_main(self):
        script = (ROOT / "src/localbrain/static/settings.js").read_text()
        finish = script.split("async function finishOnboarding()", 1)[1].split("$('[data-onboarding-back]')", 1)[0]
        self.assertIn("revision: current.preferences.revision, changes: {onboarding_completed: true}", finish)
        self.assertIn("if (!confirmed?.saved.onboarding_completed) throw error", finish)
        self.assertLess(finish.index("state.preferences = confirmed"), finish.index("onboarding = false"))
        self.assertIn("document.querySelector('.app-shell').inert = false", finish)
        self.assertIn("location.replace('/' + state.preferences.effective.startup_screen)", finish)


if __name__ == "__main__":
    unittest.main()
