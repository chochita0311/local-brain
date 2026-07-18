import re
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


ROOT = Path(__file__).parents[1]
STYLES = ROOT / "src" / "localbrain" / "static" / "styles.css"
SCRIPT = ROOT / "src" / "localbrain" / "static" / "app.js"
BASE = ROOT / "src" / "localbrain" / "templates" / "base.html"
CONTEXT = ROOT / "src" / "localbrain" / "templates" / "context.html"
SESSIONS = ROOT / "src" / "localbrain" / "templates" / "sessions.html"
SESSION_DETAIL = ROOT / "src" / "localbrain" / "templates" / "session.html"
SUBAGENT_DETAIL = ROOT / "src" / "localbrain" / "templates" / "subagent.html"


class UiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.styles = STYLES.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.base = BASE.read_text(encoding="utf-8")
        cls.context = CONTEXT.read_text(encoding="utf-8")
        cls.sessions = SESSIONS.read_text(encoding="utf-8")
        cls.session_detail = SESSION_DETAIL.read_text(encoding="utf-8")
        cls.subagent_detail = SUBAGENT_DETAIL.read_text(encoding="utf-8")

    def test_component_rules_do_not_use_raw_colors(self):
        token_end = self.styles.index("\n}\n\n* { box-sizing")
        component_rules = self.styles[token_end:]
        self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", component_rules))
        self.assertIsNone(re.search(r"rgba?\(", component_rules))

    def test_component_rules_consume_semantic_design_roles(self):
        token_end = self.styles.index("\n}\n\n* { box-sizing")
        component_rules = self.styles[token_end:]
        primitive_reference = re.compile(
            r"var\(--(?:color-[^)]+|font-[^)]+|size-[^)]+|weight-[^)]+|"
            r"line-[^)]+|space-\d+|radius-\d+|radius-full|stroke-[^)]+|"
            r"shadow-[^)]+|duration-[^)]+|ease-[^)]+|opacity-[^)]+)\)"
        )
        raw_spacing = re.compile(
            r"(?<![-\w])(?:margin|padding|gap|top|right|bottom|left)"
            r"(?:-[a-z]+)?\s*:[^;}]*?\b-?\d+px\b"
        )
        self.assertIsNone(primitive_reference.search(component_rules))
        self.assertIsNone(raw_spacing.search(component_rules))

        for property_name in (
            "font-size",
            "font-weight",
            "font-family",
            "line-height",
            "border-radius",
            "box-shadow",
        ):
            values = re.findall(
                rf"{property_name}\s*:\s*([^;}}]+)", component_rules
            )
            for value in values:
                self.assertTrue(
                    value.strip().startswith(("var(", "inherit", "none")),
                    f"{property_name} uses a non-semantic value: {value}",
                )
        self.assertIsNone(re.search(r"(?:transition|animation)[^;]*\b\d+m?s\b", component_rules))

    def test_semantic_foundation_includes_provenance_and_responsive_contracts(self):
        for token in (
            "--surface-source-claude",
            "--surface-source-codex",
            "--text-source-claude",
            "--text-source-codex",
            "--shell-sidebar-width: 220px",
            "--shell-sidebar-width-compact: 188px",
            "--breakpoint-compact: 920px",
            "--breakpoint-narrow: 700px",
            "--viewport-min-width: 320px",
        ):
            self.assertIn(token, self.styles)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.styles)

    def test_status_families_remain_semantically_distinct(self):
        expected_rules = (
            ".source-status.pending { color: var(--text-info);",
            ".source-status.missing { color: var(--text-warning);",
            ".status-badge.blocked { color: var(--text-danger);",
            ".run-status.running { color: var(--text-brand);",
            ".run-status.completed { color: var(--text-success);",
            ".run-status.failed { color: var(--text-danger);",
            ".result-type.claude { color: var(--text-source-claude);",
            ".result-type.codex { color: var(--text-source-codex);",
        )
        for rule in expected_rules:
            self.assertIn(rule, self.styles)

    def test_shared_shell_exposes_keyboard_and_current_location_contracts(self):
        self.assertIn('class="skip-link" href="#main-content"', self.base)
        self.assertIn('id="main-content" tabindex="-1"', self.base)
        self.assertIn('aria-current="page"', self.base)
        self.assertIn('data-toast-region aria-live="polite"', self.base)

    def test_interaction_feedback_is_bounded_and_run_polling_is_active_only(self):
        self.assertNotIn("window.alert", self.script)
        self.assertIn("function showNotice", self.script)
        self.assertIn(
            'const activeStatuses = new Set(["queued", "running", "cancelling"]);',
            self.script,
        )

    def test_context_preview_updates_without_rebuilding_the_source_tree(self):
        for marker in (
            "data-context-explorer",
            "data-context-source-id",
            "data-context-document-link",
            "data-context-preview",
            "data-context-preview-status",
            'aria-current="page"',
        ):
            self.assertIn(marker, self.context)

        for behavior in (
            'treePane.addEventListener("click"',
            "new DOMParser()",
            "currentPreview.replaceWith(adoptedPreview)",
            "window.history.pushState",
            'window.addEventListener("popstate"',
            "AbortController",
            'link.setAttribute("aria-current", "page")',
            "selectedLink.focus({ preventScroll: true })",
        ):
            self.assertIn(behavior, self.script)

        self.assertIn(
            ".source-tree-document > a { height: auto; min-height: var(--control-min-height-touch); }",
            self.styles,
        )

    def test_sessions_and_projects_share_one_navigation_destination(self):
        self.assertNotIn('<span>Projects</span>', self.base)
        self.assertIn('href="/sessions"', self.base)
        for marker in (
            "data-inventory-switch",
            'data-inventory-view="sessions"',
            'data-inventory-view="projects"',
            'data-inventory-panel="sessions"',
            'data-inventory-panel="projects"',
            'aria-current="page"',
        ):
            self.assertIn(marker, self.sessions)

        for behavior in (
            'inventorySwitch.addEventListener("click"',
            "window.history.pushState",
            'window.addEventListener("popstate"',
            "panel.hidden = panel.dataset.inventoryPanel !== selectedInventory",
        ):
            self.assertIn(behavior, self.script)

        self.assertIn("syncInventoryIndicator", self.script)
        self.assertIn('"--inventory-indicator-left"', self.script)
        self.assertIn('"--inventory-indicator-width"', self.script)
        self.assertIn(
            "transition: left var(--motion-standard-duration) var(--motion-ease), width var(--motion-standard-duration) var(--motion-ease);",
            self.styles,
        )

    def test_sessions_toolbar_matches_inventory_family_and_syncs_session_sources(self):
        for marker in (
            'class="section-toolbar inventory-toolbar"',
            'id="session-sync-button" class="primary-button"',
            'class="session-sync-form"',
            'action="/sessions/sync?view={{ inventory_mode }}',
            '<span class="button-idle">동기화</span>',
            'id="session-sync-result"',
        ):
            self.assertIn(marker, self.sessions)

        self.assertLess(
            self.sessions.index('class="heading-copy"'),
            self.sessions.index('class="section-toolbar inventory-toolbar"'),
        )
        self.assertIn(".segmented-control a,\n.inventory-switch a", self.styles)
        self.assertIn('document.querySelector("#session-sync-button")', self.script)
        self.assertIn('"/api/sessions/sync"', self.script)
        self.assertIn("const eventTarget = button.form || button;", self.script)
        self.assertIn('eventTarget.addEventListener(eventName', self.script)

    def test_sessions_sidebar_shows_only_session_sources_without_database_path(self):
        environment = Environment(loader=FileSystemLoader(ROOT / "src/localbrain/templates"))
        environment.globals["url_for"] = (
            lambda name, path: "/static{}".format(path)
        )
        html = environment.get_template("sessions.html").render(
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
            documents=[],
            sources=[
                {"kind": "claude", "name": "Claude Code", "session_count": 3},
                {"kind": "codex", "name": "Codex", "session_count": 4},
                {"kind": "context", "name": "Local Contexts", "document_count": 9},
            ],
            pagination={
                "total": 0,
                "page": 1,
                "total_pages": 1,
                "page_items": [1],
                "previous_page": None,
                "next_page": None,
            },
        )

        source_status_start = html.index(
            '<section class="side-section source-status-section">'
        )
        source_status_end = html.index("</section>", source_status_start)
        source_status = html[source_status_start:source_status_end]

        self.assertIn("Claude Code", source_status)
        self.assertIn("Codex", source_status)
        self.assertNotIn("Local Contexts", source_status)
        self.assertNotIn("DB:", html)
        self.assertNotIn("database-note", html)

    def test_static_assets_use_a_runtime_cache_version(self):
        self.assertEqual(self.base.count("asset_version | default('dev')"), 3)

    def test_sessions_template_tolerates_a_pre_restart_route_context(self):
        environment = Environment(loader=FileSystemLoader(ROOT / "src/localbrain/templates"))
        environment.globals["url_for"] = (
            lambda name, path: "/static{}".format(path)
        )
        html = environment.get_template("sessions.html").render(
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
            documents=[],
            sources=[],
            database_path="/tmp/synthetic.db",
        )

        self.assertIn('data-selected="sessions"', html)
        self.assertRegex(
            html, r'<section data-inventory-panel="sessions"\s*>'
        )
        self.assertNotIn('class="session-pagination"', html)

    def test_session_pagination_renders_number_links_and_ellipses(self):
        environment = Environment(loader=FileSystemLoader(ROOT / "src/localbrain/templates"))
        environment.globals["url_for"] = (
            lambda name, path: "/static{}".format(path)
        )
        html = environment.get_template("sessions.html").render(
            active_page="sessions",
            selected_source="all",
            selected_workspace=None,
            stats={
                "sessions": 200,
                "events": 0,
                "active_workspaces": 0,
                "missing_workspaces": 0,
            },
            sessions=[],
            documents=[],
            sources=[],
            database_path="/tmp/synthetic.db",
            pagination={
                "total": 200,
                "page": 5,
                "total_pages": 10,
                "page_items": [1, None, 4, 5, 6, None, 10],
                "compact_page_items": [1, None, 5, None, 10],
                "previous_page": 4,
                "next_page": 6,
            },
        )

        self.assertEqual(html.count('class="session-page-ellipsis"'), 4)
        self.assertIn('href="/sessions?page=10"', html)
        self.assertIn('class="session-page-number current" aria-current="page"', html)
        self.assertIn('aria-label="10페이지"', html)
        self.assertIn('class="session-page-numbers wide"', html)
        self.assertIn('class="session-page-numbers compact"', html)

    def test_session_pagination_tolerates_a_pre_restart_page_model(self):
        environment = Environment(loader=FileSystemLoader(ROOT / "src/localbrain/templates"))
        environment.globals["url_for"] = (
            lambda name, path: "/static{}".format(path)
        )
        html = environment.get_template("sessions.html").render(
            active_page="sessions",
            selected_source="all",
            selected_workspace=None,
            stats={
                "sessions": 15,
                "events": 0,
                "active_workspaces": 0,
                "missing_workspaces": 0,
            },
            sessions=[],
            documents=[],
            sources=[],
            database_path="/tmp/synthetic.db",
            pagination={
                "total": 15,
                "page": 1,
                "total_pages": 1,
                "page_items": [1],
                "previous_page": None,
                "next_page": None,
            },
        )

        self.assertEqual(html.count('class="session-page-numbers'), 2)
        self.assertEqual(html.count('aria-current="page"'), 4)

    def test_session_inventory_separates_parent_links_and_child_disclosure(self):
        for marker in (
            'class="session-row-link"',
            "data-subsession-menu",
            "data-subsession-trigger",
            "data-subsession-dropdown",
            "data-subsession-link",
            'aria-expanded="false"',
            'aria-label="세션 페이지"',
            'aria-label="페이지 선택"',
            "pagination.page_items",
            "pagination.compact_page_items",
            "pagination.previous_page",
            "pagination.next_page",
        ):
            self.assertIn(marker, self.sessions)
        self.assertNotIn('<a class="session-row"', self.sessions)
        self.assertNotIn("{{ session.source_name }}", self.sessions)

        for behavior in (
            'trigger.addEventListener("click"',
            "closeSubsessionMenus",
            'document.addEventListener("click"',
            'document.addEventListener("keydown"',
            'event.key !== "Escape"',
            "restoreFocus: true",
        ):
            self.assertIn(behavior, self.script)

        self.assertIn(".subsession-dropdown[hidden] { display: none; }", self.styles)
        self.assertIn("overflow: hidden;", self.styles)
        self.assertIn(".subsession-dropdown-list {", self.styles)
        self.assertIn("overflow-y: auto;", self.styles)
        self.assertIn(".session-row:hover .subsession-trigger", self.styles)
        self.assertIn(".session-pagination-actions", self.styles)
        self.assertIn(".session-page-numbers", self.styles)
        self.assertIn(".session-page-numbers.wide", self.styles)
        self.assertIn(".session-page-numbers.compact", self.styles)
        self.assertIn(".session-pagination .page-previous", self.styles)
        self.assertIn(".session-pagination .page-next", self.styles)

    def test_session_details_render_conversations_without_tool_rows(self):
        for template in (self.session_detail, self.subagent_detail):
            self.assertNotIn("event.event_type == 'tool_call'", template)
            self.assertIn("도구 활동은 원본 이벤트", template)
            self.assertIn("표시할 대화 메시지가 없습니다.", template)

        for marker in (
            "parent",
            "상위 Session으로 돌아가기",
            "subagent.url",
            "이 Session의 직접 하위 실행",
            "원본 이벤트",
        ):
            self.assertIn(marker, self.session_detail)


if __name__ == "__main__":
    unittest.main()
