import re
import sqlite3
import unittest
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from localbrain.usage_queries import usage_dashboard_data


ROOT = Path(__file__).parents[1]
STYLES = ROOT / "src" / "localbrain" / "static" / "styles.css"
SCRIPT = ROOT / "src" / "localbrain" / "static" / "app.js"
BASE = ROOT / "src" / "localbrain" / "templates" / "base.html"
DASHBOARD = ROOT / "src" / "localbrain" / "templates" / "dashboard.html"
CONTEXT = ROOT / "src" / "localbrain" / "templates" / "context.html"
SESSIONS = ROOT / "src" / "localbrain" / "templates" / "sessions.html"
SESSION_DETAIL = ROOT / "src" / "localbrain" / "templates" / "session.html"
SUBAGENT_DETAIL = ROOT / "src" / "localbrain" / "templates" / "subagent.html"
SESSIONS_DASHBOARD = ROOT / "src" / "localbrain" / "templates" / "sessions_dashboard.html"
SCHEMA_EXPLORER = ROOT / "src" / "localbrain" / "templates" / "schema.html"
WORKSTREAM = ROOT / "src" / "localbrain" / "templates" / "workstream.html"
MAIN = ROOT / "src" / "localbrain" / "main.py"
SCHEMA_SCRIPT = ROOT / "src" / "localbrain" / "static" / "schema-explorer.js"
SCHEMA = ROOT / "src" / "localbrain" / "schema.sql"


class UiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.styles = STYLES.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.base = BASE.read_text(encoding="utf-8")
        cls.dashboard = DASHBOARD.read_text(encoding="utf-8")
        cls.context = CONTEXT.read_text(encoding="utf-8")
        cls.sessions = SESSIONS.read_text(encoding="utf-8")
        cls.session_detail = SESSION_DETAIL.read_text(encoding="utf-8")
        cls.subagent_detail = SUBAGENT_DETAIL.read_text(encoding="utf-8")
        cls.sessions_dashboard = SESSIONS_DASHBOARD.read_text(encoding="utf-8")
        cls.schema_explorer = SCHEMA_EXPLORER.read_text(encoding="utf-8")
        cls.workstream = WORKSTREAM.read_text(encoding="utf-8")
        cls.main = MAIN.read_text(encoding="utf-8")
        cls.schema_script = SCHEMA_SCRIPT.read_text(encoding="utf-8")

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

    def test_task_runner_shows_base_request_and_exact_command_contract(self):
        for marker in (
            "data-task-run-form",
            "data-runner-task-select",
            'data-base-request="{{ task.instruction }}"',
            "data-runner-base-request-text",
            "기본 요청",
            "실제 명령",
            "{{ runner_command }}",
            "stdin으로 전달됩니다",
            "sessions · work/primary only",
        ):
            self.assertIn(marker, self.workstream)
        for behavior in (
            'document.querySelectorAll("[data-task-run-form]")',
            'taskSelect.addEventListener("change", syncBaseRequest)',
            "taskSelect.selectedOptions[0]?.dataset.baseRequest",
        ):
            self.assertIn(behavior, self.script)
        for style in (
            ".runner-base-request { grid-column: 1 / -1;",
            ".runner-request-copy p {",
            ".runner-command-preview pre { max-width: 100%;",
            "overflow-x: auto;",
        ):
            self.assertIn(style, self.styles)

    def test_marker_creation_ui_and_api_are_removed(self):
        for content in (self.dashboard, self.workstream, self.script, self.main):
            self.assertNotIn("data-maintenance-run", content)
            self.assertNotIn("data-copy-marker", content)
            self.assertNotIn("/api/maintenance-runs", content)
            self.assertNotIn("실행 마커 생성", content)

    def test_schema_extends_the_shell_and_explorer_family_without_custom_system(self):
        sources_position = self.base.index(">07</span><span>Sources</span>")
        schema_position = self.base.index(">08</span><span>Schema</span>")
        self.assertLess(sources_position, schema_position)
        self.assertIn("active_page == 'schema'", self.base)
        self.assertIn('href="/schema"', self.base)

        for marker in (
            "data-schema-explorer",
            'data-schema-focus="page"',
            'data-schema-focus="area"',
            'data-schema-focus="table"',
            "data-schema-link",
            'aria-current="page"',
            'data-localbrain-mermaid="owned"',
            "data-localbrain-mermaid-source",
            "data-schema-source-json",
            "data-schema-diagram-fallback",
            "schema-table-title",
            "schema-contract-grid",
            "schema-column-list",
            "schema-relation-groups",
            "schema-explorer.js",
            "asset_version",
        ):
            self.assertIn(marker, self.schema_explorer)

        for behavior in (
            "AbortController",
            "new DOMParser()",
            "outgoing.replaceWith(adopted)",
            "window.history.pushState",
            'window.addEventListener("popstate"',
            "schemaFocusTarget",
            'destination.searchParams.has("table")',
            "focus({ preventScroll: true })",
            'scrollIntoView({ block: "start", inline: "nearest" })',
            "window.location.assign(destination.href)",
            "await import(adapterUrl)",
            "JSON.parse(source.textContent)",
            "renderLocalBrainMermaid",
        ):
            self.assertIn(behavior, self.schema_script)

        for responsive_rule in (
            ".schema-layout { grid-template-columns: 1fr; }",
            ".schema-subject-links { grid-template-columns: repeat(2, minmax(0, 1fr)); }",
            ".schema-subject-links, .schema-table-links, .schema-contract-grid, .schema-relation-groups { grid-template-columns: 1fr; }",
        ):
            self.assertIn(responsive_rule, self.styles)

    def test_usage_dashboard_keeps_one_summary_and_history_family(self):
        for marker in (
            'class="overview-metrics usage-summary"',
            'class="analysis-panel usage-history-panel"',
            'name="view"',
            'name="source"',
            'name="metric"',
            'name="from"',
            'name="to"',
            'aria-current="page"',
            'usage.history_has_values',
            'usage.limitations',
            'aria-label="Usage breakdown"',
            'class="analysis-panel usage-breakdown-panel"',
            'class="analysis-panel usage-trust-panel"',
            'usage.breakdown.primary_rows',
            'usage.breakdown.overflow_rows',
            'usage.freshness.sources',
            'How estimated cost is calculated',
        ):
            self.assertIn(marker, self.sessions_dashboard)
        self.assertNotIn("Projected month end", self.sessions_dashboard)
        self.assertNotIn("usage.projection", self.sessions_dashboard)
        self.assertNotIn("Allocation", self.sessions_dashboard)
        self.assertNotIn("budget", self.sessions_dashboard.lower())
        self.assertNotIn("quota", self.sessions_dashboard.lower())

        for copy in (
            "usage record{% if item.usage_record_count != 1 %}s{% endif %} priced",
            "selected usage record{% if source.selected_usage_record_count != 1 %}s{% endif %}",
            "Selected usage records",
            "each usage record is first observed",
        ):
            self.assertIn(copy, self.sessions_dashboard)
        self.assertNotIn("usage facts", self.sessions_dashboard.lower())
        self.assertNotIn("facts priced", self.sessions_dashboard.lower())
        self.assertNotIn("each fact", self.sessions_dashboard.lower())
        self.assertIn(".usage-summary { grid-template-columns: 1fr; }", self.styles)
        self.assertIn(
            ".usage-summary .overview-metric:last-child { border-bottom: var(--border-width-none); }",
            self.styles,
        )

    def test_usage_dashboard_does_not_render_month_end_projection(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
        usage = usage_dashboard_data(
            connection,
            metric="cost",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        environment = Environment(loader=FileSystemLoader(ROOT / "src/localbrain/templates"))
        environment.globals["url_for"] = lambda name, path: "/static{}".format(path)
        html = environment.get_template("sessions_dashboard.html").render(
            active_page="sessions-dashboard",
            usage=usage,
        )
        connection.close()

        self.assertTrue(usage["projection"]["visible"])
        self.assertNotIn("Projected month end", html)
        self.assertNotIn("usage-projection-context", html)

    def test_usage_dashboard_renders_empty_state_from_its_read_model(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
        usage = usage_dashboard_data(
            connection, timezone_name="UTC", today=date(2026, 7, 18)
        )
        environment = Environment(loader=FileSystemLoader(ROOT / "src/localbrain/templates"))
        environment.globals["url_for"] = lambda name, path: "/static{}".format(path)
        html = environment.get_template("sessions_dashboard.html").render(
            active_page="sessions-dashboard",
            usage=usage,
        )
        connection.close()

        self.assertIn("No usage indexed", html)
        self.assertIn("2026-06-19 – 2026-07-18", html)
        self.assertEqual(html.count('class="overview-metric unavailable"'), 2)
        self.assertIn('/sessions-dashboard?view=weekly&source=all&metric=tokens', html)
        self.assertIn('aria-current="page"', html)

    def test_usage_dashboard_scope_switches_replace_only_the_dashboard(self):
        for marker in (
            "data-usage-dashboard",
            "data-usage-dashboard-status",
            "data-usage-scope-link",
            'data-usage-control="metric"',
            'data-usage-control="breakdown"',
        ):
            self.assertIn(marker, self.sessions_dashboard)

        for behavior in (
            "currentUsageDashboard",
            'headers: { "X-Requested-With": "LocalBrain-Usage-Dashboard" }',
            "new DOMParser()",
            "outgoingDashboard.replaceWith(adoptedDashboard)",
            "window.history.pushState",
            'window.addEventListener("popstate"',
            "AbortController",
            "restoreUsageScroll(scrollY)",
            "focus({ preventScroll: true })",
            "window.location.assign(destination.href)",
        ):
            self.assertIn(behavior, self.script)

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
