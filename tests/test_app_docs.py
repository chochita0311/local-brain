"""Bundled guide routes and their opt-in link authority use no personal data."""

from html.parser import HTMLParser
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from localbrain.app import docs as app_docs
from localbrain.rendering.markdown import render_markdown


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if "id" in attrs:
            self.ids.add(attrs["id"])


class AppDocsTests(unittest.TestCase):
    def setUp(self):
        package = Path(app_docs.__file__).parents[1]
        self.app = FastAPI()
        self.app.mount("/static", StaticFiles(directory=package / "static"), name="static")
        self.preferences = SimpleNamespace(timezone="UTC", onboarding_completed=False)
        self.templates = Jinja2Templates(directory=package / "templates")
        self.templates.env.globals.update(
            local_preferences=lambda: self.preferences,
            desktop_edition=True,
            auto_work_available=False,
            asset_version="synthetic-test",
            app_version="0.0.1",
        )
        app_docs.install_routes(self.app, self.templates)
        self.home_endpoint = next(route.endpoint for route in self.app.routes if route.path == "/help")
        self.endpoint = next(route.endpoint for route in self.app.routes if route.path == "/help/{slug}")

    def page(self, slug="", query=b""):
        request = Request({
            "type": "http", "scheme": "http", "method": "GET",
            "server": ("127.0.0.1", 18789), "client": ("127.0.0.1", 1),
            "path": "/help" + ("/" + slug if slug else ""),
            "query_string": query, "headers": [], "root_path": "",
            "app": self.app, "router": self.app.router,
        })
        return self.endpoint(request, slug) if slug else self.home_endpoint(request)

    def test_every_bundled_guide_has_live_internal_and_fragment_links(self):
        self.assertEqual(
            {p.name for p in app_docs.CONTENT_ROOT.glob("*.md")},
            {guide.filename for guide in app_docs.GUIDES},
        )
        for guide in app_docs.GUIDES:
            with self.subTest(guide=guide.slug):
                response = self.page(guide.slug)
                self.assertEqual(response.status_code, 200)
                html = response.body.decode()
                self.assertIn('lang="en"', html)
                self.assertIn('<h1 id="guide-title">' + guide.title, html)
                self.assertIn('href="' + guide.href + '" aria-current="page"', html)
                self.assertNotIn('href="/help/troubleshooting"', html)
                self.assertNotIn('>Open settings</button>', html)
                self.assertNotIn('For LocalBrain v', html)
                self.assertNotIn('data-reference-state="no-source"', html)
                self.assertNotIn('data-reference-state="missing"', html)
                parsed = Anchors()
                parsed.feed(html)
                for href in parsed.links:
                    if href.startswith("#"):
                        self.assertIn(href[1:], parsed.ids)
                    else:
                        base, separator, fragment = href.partition("#")
                        if base.startswith("https://"):
                            self.assertIn(base, {
                                "https://docs.cloud.google.com/sdk/docs/install-sdk",
                                "https://docs.cloud.google.com/sdk/docs/authenticate",
                            })
                            continue
                        self.assertIn(base, app_docs.APP_DOC_ROUTES | {"/"})
                        if separator:
                            target = Anchors()
                            target.feed(self.page(base.removeprefix("/help/")).body.decode())
                            self.assertIn(fragment, target.ids)
                self.assertNotIn(str(app_docs.CONTENT_ROOT), html)

    def test_docs_remains_readable_before_setup_without_completing_it(self):
        response = self.page()
        html = response.body.decode()
        self.assertNotIn('data-onboarding="true"', html)
        self.assertNotIn('class="app-shell" inert', html)
        self.assertLess(html.index('href="/help"'), html.index("data-settings-open"))
        self.assertIn("Read the getting started guide", html)
        self.assertFalse(self.preferences.onboarding_completed)

    def test_home_query_cannot_select_another_guide(self):
        response = self.page(query=b"slug=settings")
        self.assertIn('<h1 id="guide-title">Getting started', response.body.decode())

    def test_unknown_name_cannot_select_or_read_a_file(self):
        for slug in ("unknown", "troubleshooting", "../schema", "/etc/passwd", "settings.md"):
            with self.subTest(slug=slug), patch.object(Path, "read_text", side_effect=AssertionError("unexpected file read")):
                response = self.page(slug)
                self.assertEqual(response.status_code, 404)
                self.assertIn("Guide not found", response.body.decode())

    def test_missing_or_empty_packaged_body_is_bounded_unavailable(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(app_docs, "CONTENT_ROOT", Path(directory)):
            response = self.page("settings")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn(directory, response.body.decode())
            (Path(directory) / "settings.md").write_text("")
            self.assertEqual(self.page("settings").status_code, 503)
            (Path(directory) / "settings.md").write_text(" \n\t")
            self.assertEqual(self.page("settings").status_code, 503)

    def test_first_party_links_do_not_change_default_source_markdown_rules(self):
        source = "[Settings](/settings) [Guide](/help/search) [API](/api/settings) [Work](/workstreams) [Escape](//example.invalid)"
        normal = str(render_markdown(source).html)
        self.assertNotIn('href="/settings"', normal)
        routes = {"/settings", "/help/search", "/api/settings", "/workstreams", "//example.invalid"}
        admitted = str(render_markdown(source, app_doc_routes=routes).html)
        self.assertIn('href="/settings"', admitted)
        self.assertIn('href="/help/search"', admitted)
        for rejected in ("/api/settings", "/workstreams", "//example.invalid"):
            self.assertNotIn('href="' + rejected + '"', admitted)
        self.assertEqual(str(render_markdown(source).html), normal)


if __name__ == "__main__":
    unittest.main()
