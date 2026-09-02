import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from starlette.requests import Request

from localbrain.value_registry import display_value_label, visible_value_help


ROOT = Path(__file__).resolve().parents[1]


class SessionPinUiTests(unittest.TestCase):
    @staticmethod
    def _environment() -> Environment:
        environment = Environment(
            loader=FileSystemLoader(ROOT / "src/localbrain/templates")
        )
        environment.globals["url_for"] = (
            lambda name, path: "/static{}".format(path)
        )
        environment.globals["value_label"] = display_value_label
        environment.globals["value_help"] = visible_value_help
        return environment

    @staticmethod
    def _request(path: str = "/sessions", query: bytes = b"") -> Request:
        return Request(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": path,
                "raw_path": path.encode("utf-8"),
                "query_string": query,
                "headers": [],
                "client": ("test", 50000),
                "server": ("test", 80),
                "root_path": "",
            }
        )

    @staticmethod
    def _session(session_id: int, *, pinned: bool, children: list) -> dict:
        return {
            "id": session_id,
            "title": "Pinned session" if pinned else "Ordinary session",
            "source_kind": "codex" if pinned else "claude",
            "provider_kind": "codex" if pinned else "claude",
            "source_name": "Codex" if pinned else "Claude",
            "session_role": "primary",
            "workspace_path": "/synthetic/work",
            "cwd_raw": "/synthetic/work",
            "exists_now": 1,
            "git_branch": "feature/pins",
            "user_message_count": 3,
            "event_count": 8,
            "last_event_at": "2026-07-24T04:00:00+00:00",
            "started_at": "2026-07-24T03:00:00+00:00",
            "pinned_at": "2026-07-24T05:00:00+00:00" if pinned else None,
            "subsessions": children,
        }

    def test_inventory_replaces_recent_context_and_separates_controls(self):
        environment = self._environment()
        child = self._session(3, pinned=False, children=[])
        child["session_role"] = "subsession"
        company_session = {
            **self._session(4, pinned=False, children=[]),
            "title": "Company session",
            "source_kind": "codex-company",
            "provider_kind": "codex",
            "source_name": "Codex Company",
            "git_branch": None,
        }
        sessions = [
            self._session(1, pinned=True, children=[child]),
            company_session,
            self._session(2, pinned=False, children=[]),
        ]
        response = environment.get_template("sessions.html").render(
            request=self._request(
                query=b"source=codex&workspace=7&page=3"
            ),
            active_page="sessions",
            selected_source="codex",
            selected_source_label="Codex",
            selected_workspace=7,
            stats={
                "sessions": 3,
                "events": 24,
                "active_workspaces": 1,
                "missing_workspaces": 0,
            },
            sessions=sessions,
            pinned_sessions=[
                {
                    **sessions[0],
                    "workspace_name": "Synthetic Work",
                },
                {
                    **company_session,
                    "workspace_name": "Company Work",
                    "pinned_at": "2026-07-24T06:00:00+00:00",
                },
            ],
            pinned_session_groups=[
                {
                    "workspace_name": "Company Work",
                    "workspace_path": "/synthetic/company",
                    "sessions": [
                        {
                            **company_session,
                            "workspace_name": "Company Work",
                            "pinned_at": "2026-07-24T06:00:00+00:00",
                        }
                    ],
                },
                {
                    "workspace_name": "Synthetic Work",
                    "workspace_path": "/synthetic/work",
                    "sessions": [
                        {
                            **sessions[0],
                            "workspace_name": "Synthetic Work",
                        }
                    ],
                },
            ],
            sources=[],
            session_source_scopes=[
                {"source_key": "claude", "display_label": "Claude"},
                {"source_key": "codex", "display_label": "Codex"},
                {
                    "source_key": "codex-company",
                    "display_label": "Codex Company",
                },
            ],
            projects=[],
            pagination={
                "total": 3,
                "page": 3,
                "total_pages": 3,
                "page_items": [1, 2, 3],
                "compact_page_items": [1, 2, 3],
                "previous_page": 2,
                "next_page": None,
            },
        )

        self.assertIn("Pinned Sessions", response)
        self.assertLess(response.index(">전체</a>"), response.index(">Claude</a>"))
        self.assertLess(response.index(">Claude</a>"), response.index(">Codex</a>"))
        self.assertLess(
            response.index(">Codex</a>"), response.index(">Codex Company</a>")
        )
        self.assertIn(
            'href="/sessions?source=codex-company&workspace=7"', response
        )
        self.assertNotIn("source=codex-company&workspace=7&page=", response)
        self.assertNotIn("최근 컨텍스트", response)
        self.assertNotIn('href="/documents/', response)
        self.assertIn('action="/sessions/1/unpin"', response)
        self.assertIn('aria-label="핀 해제"', response)
        self.assertIn('aria-pressed="true"', response)
        self.assertIn('action="/sessions/2/pin"', response)
        self.assertIn('aria-label="핀 고정"', response)
        self.assertIn(
            'value="/sessions?source=codex&workspace=7&page=3"',
            response,
        )
        pinned_panel = response[
            response.index("data-pinned-sessions-panel"):
            response.index("source-status-section")
        ]
        self.assertIn("Codex", pinned_panel)
        self.assertIn('class="pinned-session-source codex"', pinned_panel)
        self.assertIn('<span aria-hidden="true">CX</span>', pinned_panel)
        self.assertIn('<span class="sr-only">Codex</span>', pinned_panel)
        self.assertIn('class="pinned-session-source codex-company"', pinned_panel)
        self.assertIn('<span aria-hidden="true">CC</span>', pinned_panel)
        self.assertIn('<span class="sr-only">Codex Company</span>', pinned_panel)
        self.assertNotIn('class="pinned-session-provenance"', pinned_panel)
        self.assertIn('class="pinned-session-list-content"', pinned_panel)
        self.assertEqual(pinned_panel.count('class="pinned-session-group"'), 2)
        self.assertLess(
            pinned_panel.index(">Company Work</h3>"),
            pinned_panel.index(">Synthetic Work</h3>"),
        )
        self.assertEqual(pinned_panel.count("Company Work"), 1)
        self.assertEqual(pinned_panel.count("Synthetic Work"), 1)
        self.assertIn(
            '<span class="pinned-session-branch" title="feature/pins">feature/pins</span>',
            pinned_panel,
        )
        company_group = pinned_panel[
            pinned_panel.index(">Company Work</h3>"):
            pinned_panel.index(">Synthetic Work</h3>")
        ]
        self.assertNotIn("pinned-session-branch", company_group)
        self.assertIn("data-local-time", pinned_panel)

        first_row = response[
            response.index('<div class="session-row">'):
            response.index('<div class="session-row">', response.index('<div class="session-row">') + 1)
        ]
        link_end = first_row.index("</a>")
        self.assertGreater(first_row.index('class="session-utility-layer"'), link_end)
        self.assertGreater(first_row.index("data-session-pin-form"), link_end)
        self.assertGreater(first_row.index("data-subsession-menu"), link_end)
        self.assertIn("질문 3 · 이벤트 8", first_row)
        self.assertIn('class="session-source codex"', first_row)
        self.assertIn('<span aria-hidden="true">CX</span>', first_row)
        self.assertIn('<span class="sr-only">Codex ·', first_row)
        self.assertNotIn('class="session-provenance"', first_row)
        self.assertNotIn("Subsession · 질문", first_row)
        self.assertLess(first_row.index("질문 3"), first_row.index("이벤트 8"))
        self.assertLess(first_row.index("이벤트 8"), first_row.index("session-time"))
        self.assertLess(first_row.index("session-time"), first_row.index("data-session-pin-form"))

        company_row_start = response.index(
            '<div class="session-row">',
            response.index('<div class="session-row">') + 1,
        )
        company_row_end = response.index(
            '<div class="session-row">', company_row_start + 1
        )
        company_row = response[company_row_start:company_row_end]
        self.assertIn('class="session-source codex-company"', company_row)
        self.assertIn('<span aria-hidden="true">CC</span>', company_row)
        self.assertIn('<span class="sr-only">Codex Company ·', company_row)
        self.assertNotIn('class="session-provenance"', company_row)
        self.assertIn('class="session-source claude"', response)
        self.assertIn('<span aria-hidden="true">CL</span>', response)

    def test_empty_panel_never_falls_back_to_recent_documents(self):
        environment = self._environment()
        response = environment.get_template("sessions.html").render(
            request=self._request(),
            active_page="sessions",
            selected_source="all",
            selected_workspace=None,
            stats={
                "sessions": 0,
                "events": 0,
                "active_workspaces": 0,
                "missing_workspaces": 0,
            },
            sessions=[],
            pinned_sessions=[],
            pinned_session_groups=[],
            sources=[],
            projects=[],
        )

        self.assertIn("고정한 Session이 없습니다", response)
        self.assertIn("목록이나 상세 화면의 핀 버튼", response)
        self.assertNotIn("최근 컨텍스트", response)

    def test_pre_restart_route_context_keeps_existing_pins_visible(self):
        environment = self._environment()
        pinned_session = self._session(1, pinned=True, children=[])
        response = environment.get_template("sessions.html").render(
            request=self._request(),
            active_page="sessions",
            selected_source="all",
            selected_workspace=None,
            stats={
                "sessions": 1,
                "events": 8,
                "active_workspaces": 1,
                "missing_workspaces": 0,
            },
            sessions=[pinned_session],
            pinned_sessions=[pinned_session],
            sources=[],
            projects=[],
        )

        pinned_panel = response[
            response.index("data-pinned-sessions-panel"):
            response.index("source-status-section")
        ]
        self.assertIn("Pinned session", pinned_panel)
        self.assertIn("feature/pins", pinned_panel)
        self.assertNotIn("고정한 Session이 없습니다", pinned_panel)

    def test_storage_error_stays_adjacent_to_truthful_control_state(self):
        environment = self._environment()
        template = environment.from_string(
            """
            {% from "_session_pin.html" import session_pin_control with context %}
            {{ session_pin_control(session, '/sessions', 'inventory') }}
            """
        )

        response = template.render(
            request=self._request(
                query=b"pin_error=storage-unavailable&pin_session=1"
            ),
            session=self._session(1, pinned=False, children=[]),
        )

        self.assertIn('aria-pressed="false"', response)
        self.assertIn('aria-describedby="session-pin-error-1"', response)
        self.assertIn('class="session-pin-inline-error" role="alert"', response)
        self.assertIn("현재 상태는 변경되지 않았습니다", response)

    def test_pin_visual_and_enhancement_preserve_geometry_and_scroll(self):
        styles = (ROOT / "src/localbrain/static/styles.css").read_text(
            encoding="utf-8"
        )
        script = (ROOT / "src/localbrain/static/app.js").read_text(
            encoding="utf-8"
        )

        pin_rule = styles[
            styles.index(".session-pin-button {"):
            styles.index(".session-pin-button svg")
        ]
        utility_rule = styles[
            styles.index(".session-utility-upper {"):
            styles.index(".session-time {")
        ]
        self.assertIn(
            "calc(var(--control-min-height) + var(--space-panel))",
            utility_rule,
        )
        self.assertIn(
            "calc(var(--control-min-height) + var(--space-card) + var(--space-card))",
            utility_rule,
        )
        self.assertIn(
            ".session-utility-upper > span { justify-self: start; text-align: left;",
            utility_rule,
        )
        self.assertIn(
            "border: var(--border-width-control) solid transparent;",
            pin_rule,
        )
        self.assertIn("background: transparent;", pin_rule)
        self.assertIn("width: var(--control-min-height);", pin_rule)
        self.assertIn("height: var(--control-min-height);", pin_rule)
        row_hover_rule = styles[
            styles.index(".session-row:hover,"):
            styles.index(".session-row-link {")
        ]
        self.assertIn("background: var(--surface-subtle);", row_hover_rule)
        pressed_rule = styles[
            styles.index('.session-pin-button[aria-pressed="true"] {'):
            styles.index(
                '.session-pin-button[aria-pressed="true"] .session-pin-shape'
            )
        ]
        hover_rule = styles[
            styles.index(
                '.session-pin-button:not([aria-pressed="true"]):hover {'
            ):
            styles.index(".session-pin-button:focus-visible")
        ]
        self.assertIn(
            '.session-pin-button:not([aria-pressed="true"]):hover',
            hover_rule,
        )
        self.assertNotIn("border-color", pressed_rule)
        self.assertNotIn("background:", pressed_rule)
        self.assertNotIn("border-color", hover_rule)
        self.assertNotIn("background:", hover_rule)

        self.assertIn(
            'event.target.closest?.("[data-session-pin-form]")',
            script,
        )
        self.assertIn("const windowScrollY = window.scrollY;", script)
        self.assertIn(
            'document.querySelector(".pinned-session-list")?.scrollTop',
            script,
        )
        self.assertIn("window.scrollTo(0, windowScrollY);", script)
        self.assertIn("adoptedControl?.focus({ preventScroll: true });", script)

    def test_pinned_session_scroll_content_owns_desktop_end_inset(self):
        styles = (ROOT / "src/localbrain/static/styles.css").read_text(
            encoding="utf-8"
        )

        list_rule = styles.split(".pinned-session-list {", 1)[1].split("}", 1)[0]
        self.assertNotIn("padding", list_rule)
        self.assertIn(
            ".pinned-session-list-content { padding-right: var(--space-section); }",
            styles,
        )
        self.assertIn(
            ".pinned-session-list-content { padding-right: var(--space-none); }",
            styles,
        )
        self.assertIn(".pinned-session-group-heading {", styles)
        self.assertIn(".pinned-session-group-items > a {", styles)


if __name__ == "__main__":
    unittest.main()
