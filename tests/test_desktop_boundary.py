"""Synthetic middleware contracts; WKWebView redirect behavior is checked separately."""

import asyncio
import json
import os
import tempfile
import unittest
from http.cookies import SimpleCookie
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from localbrain import edition
from localbrain.preferences import read_preferences, save_preferences


class DesktopBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.config = SimpleNamespace(data_dir=Path(temporary.name), timezone_name="UTC")
        self.token = "synthetic-per-launch-token"
        values = {key: value for key, value in os.environ.items() if not key.startswith("LOCALBRAIN_")}
        environment = patch.dict(os.environ, {**values, "LOCALBRAIN_DESKTOP_TOKEN": self.token}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        desktop = patch.object(edition, "DESKTOP", True)
        desktop.start()
        self.addCleanup(desktop.stop)
        app = FastAPI()
        edition.install_boundary(app, self.config)
        self.dispatch = app.user_middleware[0].kwargs["dispatch"]

    def request(self, path, method="GET", headers=None):
        url = urlsplit("http://127.0.0.1:18770" + path if path.startswith("/") else path)
        scope = {
            "type": "http", "method": method, "scheme": url.scheme,
            "path": url.path, "query_string": url.query.encode(),
            "server": (url.hostname, url.port or 80),
            "headers": [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()],
        }
        async def admitted(request):
            return JSONResponse({"ready": True})
        return asyncio.run(self.dispatch(Request(scope), admitted))

    def start(self):
        return self.request("/desktop/start?token=" + self.token)

    def authenticated(self, **headers):
        return {"Cookie": "localbrain-desktop=" + self.token, **headers}

    def test_handshake_cookie_allows_native_top_level_redirect(self):
        response = self.start()
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/onboarding")
        cookie = response.headers["set-cookie"].lower()
        self.assertIn("samesite=lax", cookie)
        self.assertIn("httponly", cookie)
        self.assertIn("path=/", cookie)
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertIn("no-store", response.headers["cache-control"])
        self.assertEqual(self.request("/onboarding", headers=self.authenticated()).status_code, 200)

    def test_handshake_replaces_cookie_from_previous_launch(self):
        stale = {"Cookie": "localbrain-desktop=previous-launch"}
        self.assertEqual(self.request("/sessions", headers=stale).status_code, 401)
        response = self.request("/desktop/start?token=" + self.token, headers=stale)
        cookies = SimpleCookie(response.headers["set-cookie"])
        self.assertEqual(cookies["localbrain-desktop"].value, self.token)
        self.assertEqual(self.request("/sessions", headers=self.authenticated()).status_code, 200)

    def test_completed_setup_uses_saved_startup_screen(self):
        current = read_preferences(self.config)
        save_preferences({"onboarding_completed": True, "startup_screen": "context"}, current["revision"], self.config)
        self.assertEqual(self.start().headers["location"], "/context")

    def test_missing_or_wrong_token_stays_unauthorized_with_utf8_error(self):
        for path in ("/sessions", "/desktop/start", "/desktop/start?token=wrong"):
            response = self.request(path)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.headers["content-type"], "application/json; charset=utf-8")
            self.assertEqual(json.loads(response.body)["detail"], "앱 창에서 열어 주세요.")
            self.assertNotIn("set-cookie", response.headers)

    def test_lax_cookie_does_not_admit_cross_origin_mutation(self):
        for headers in ({"Origin": "https://example.invalid"}, {"Sec-Fetch-Site": "cross-site"},
                        {"Origin": "http://127.0.0.1:18771"}):
            response = self.request("/api/settings/preferences", "POST", self.authenticated(**headers))
            self.assertEqual(response.status_code, 403)
        response = self.request("/api/settings/preferences", "POST", self.authenticated(Origin="http://127.0.0.1:18770"))
        self.assertEqual(response.status_code, 200)

    def test_product_and_loopback_boundaries_still_apply(self):
        self.assertEqual(self.request("/workstreams", headers=self.authenticated()).status_code, 404)
        self.assertEqual(self.request("http://example.invalid/sessions", headers=self.authenticated()).status_code, 403)


if __name__ == "__main__":
    unittest.main()
