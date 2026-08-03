import re
import sqlite3
import unittest
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from localbrain.usage_queries import usage_dashboard_data
from localbrain.value_registry import display_value_label, visible_value_help


ROOT = Path(__file__).parents[1]
STYLES = ROOT / "src" / "localbrain" / "static" / "styles.css"
SCRIPT = ROOT / "src" / "localbrain" / "static" / "app.js"
BASE = ROOT / "src" / "localbrain" / "templates" / "base.html"
DASHBOARD = ROOT / "src" / "localbrain" / "templates" / "dashboard.html"
CONTEXT = ROOT / "src" / "localbrain" / "templates" / "context.html"
CONTEXT_TREE = ROOT / "src" / "localbrain" / "templates" / "_context_tree.html"
DOCUMENT = ROOT / "src" / "localbrain" / "templates" / "document.html"
SESSIONS = ROOT / "src" / "localbrain" / "templates" / "sessions.html"
SOURCES = ROOT / "src" / "localbrain" / "templates" / "sources.html"
SESSION_DETAIL = ROOT / "src" / "localbrain" / "templates" / "session.html"
SUBSESSION_DETAIL = ROOT / "src" / "localbrain" / "templates" / "subsession.html"
SOURCE_CUE = ROOT / "src" / "localbrain" / "templates" / "_source_cue.html"
CONVERSATION = ROOT / "src" / "localbrain" / "templates" / "_conversation.html"
SESSIONS_DASHBOARD = ROOT / "src" / "localbrain" / "templates" / "sessions_dashboard.html"
SCHEMA_EXPLORER = ROOT / "src" / "localbrain" / "templates" / "schema.html"
WORKSTREAM = ROOT / "src" / "localbrain" / "templates" / "workstream.html"
MAIN = ROOT / "src" / "localbrain" / "main.py"
SCHEMA_SCRIPT = ROOT / "src" / "localbrain" / "static" / "schema-explorer.js"
SCHEMA = ROOT / "src" / "localbrain" / "schema.sql"
ATLASSIAN = ROOT / "src" / "localbrain" / "templates" / "atlassian.html"
ATLASSIAN_SCRIPT = ROOT / "src" / "localbrain" / "static" / "atlassian.js"
ATLASSIAN_REFRESH = (
    ROOT / "src" / "localbrain" / "templates" / "atlassian-refresh.html"
)
ATLASSIAN_REFRESH_SCRIPT = (
    ROOT / "src" / "localbrain" / "static" / "atlassian-refresh.js"
)
ATLASSIAN_ITEM = (
    ROOT / "src" / "localbrain" / "templates" / "atlassian-item.html"
)
SEARCH = ROOT / "src" / "localbrain" / "templates" / "search.html"


def template_environment(path=ROOT / "src/localbrain/templates"):
    environment = Environment(loader=FileSystemLoader(path))
    environment.globals["url_for"] = (
        lambda name, path: "/static{}".format(path)
    )
    environment.globals["value_label"] = display_value_label
    environment.globals["value_help"] = visible_value_help
    return environment


class UiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.styles = STYLES.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.base = BASE.read_text(encoding="utf-8")
        cls.dashboard = DASHBOARD.read_text(encoding="utf-8")
        cls.context_tree = CONTEXT_TREE.read_text(encoding="utf-8")
        cls.context = CONTEXT.read_text(encoding="utf-8") + cls.context_tree
        cls.document = DOCUMENT.read_text(encoding="utf-8") + cls.context_tree
        cls.sessions = SESSIONS.read_text(encoding="utf-8")
        cls.sources = SOURCES.read_text(encoding="utf-8")
        cls.conversation = CONVERSATION.read_text(encoding="utf-8")
        cls.session_detail = (
            SESSION_DETAIL.read_text(encoding="utf-8") + cls.conversation
        )
        cls.subsession_detail = (
            SUBSESSION_DETAIL.read_text(encoding="utf-8") + cls.conversation
        )
        cls.source_cue = SOURCE_CUE.read_text(encoding="utf-8")
        cls.sessions_dashboard = SESSIONS_DASHBOARD.read_text(encoding="utf-8")
        cls.schema_explorer = SCHEMA_EXPLORER.read_text(encoding="utf-8")
        cls.workstream = WORKSTREAM.read_text(encoding="utf-8")
        cls.main = MAIN.read_text(encoding="utf-8")
        cls.schema_script = SCHEMA_SCRIPT.read_text(encoding="utf-8")
        cls.atlassian = ATLASSIAN.read_text(encoding="utf-8")
        cls.atlassian_script = ATLASSIAN_SCRIPT.read_text(encoding="utf-8")
        cls.atlassian_refresh = ATLASSIAN_REFRESH.read_text(encoding="utf-8")
        cls.atlassian_refresh_script = ATLASSIAN_REFRESH_SCRIPT.read_text(
            encoding="utf-8"
        )
        cls.atlassian_item = ATLASSIAN_ITEM.read_text(encoding="utf-8")
        cls.search = SEARCH.read_text(encoding="utf-8")

    def test_component_rules_do_not_use_raw_colors(self):
        token_end = self.styles.index("\n}\n\n* { box-sizing")
        component_rules = self.styles[token_end:]
        self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", component_rules))
        self.assertIsNone(re.search(r"rgba?\(", component_rules))

    def test_native_selects_share_one_disclosure_geometry(self):
        for token in (
            "--select-disclosure-size: var(--space-12);",
            "--select-disclosure-inset: var(--space-12);",
            "--select-text-reserve: calc(var(--select-disclosure-size) + var(--select-disclosure-inset) + var(--space-control-gap));",
        ):
            self.assertIn(token, self.styles)
        self.assertEqual(self.styles.count("select:not([multiple]) {"), 1)
        for rule in (
            "padding-right: var(--select-text-reserve);",
            "background-position: right var(--select-disclosure-inset) center;",
            "background-size: var(--select-disclosure-size) var(--select-disclosure-size);",
        ):
            self.assertIn(rule, self.styles)
        for surface in (self.atlassian, self.workstream, self.search):
            self.assertIn("<select", surface)

    def test_atlassian_local_add_keeps_only_actionable_url_preview(self):
        for removed_copy in (
            "티켓 또는 프로젝트",
            "Site와 표시 이름은 URL에서 정해지며",
            "등록하거나 선택한 티켓과 Page만 관리합니다",
            "HTTP(S) Item 또는 Space URL만 허용됩니다.",
            'value_help("atlassian-space.coverage")',
        ):
            self.assertNotIn(removed_copy, self.atlassian)
        self.assertIn("data-atlassian-url-preview", self.atlassian)

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
            "--surface-code-reading",
            "--text-code-keyword",
            "--text-code-string",
            "--text-code-attribute",
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

    def test_local_contexts_follows_sessions_in_visible_and_keyboard_order(self):
        destinations = (
            ("04", "Sessions", "/sessions", "sessions"),
            ("05", "Local Contexts", "/context", "context"),
            ("06", "Atlassian", "/atlassian", "atlassian"),
            ("07", "Sources", "/sources", "sources"),
            ("08", "Schema", "/schema", "schema"),
        )
        positions = []
        for number, label, href, active_page in destinations:
            marker = ">{}</span><span>{}</span>".format(number, label)
            positions.append(self.base.index(marker))
            self.assertIn('href="{}"'.format(href), self.base)
            self.assertIn("active_page == '{}'".format(active_page), self.base)
        self.assertEqual(positions, sorted(positions))

        environment = template_environment(BASE.parent)
        environment.globals["url_for"] = lambda name, path: path
        template = environment.get_template("base.html")
        for _, label, href, active_page in destinations:
            with self.subTest(active_page=active_page):
                html = template.render(
                    active_page=active_page,
                    asset_version="synthetic",
                )
                current = re.findall(
                    r'<a class="lnb-item active" href="([^"]+)" aria-current="page">',
                    html,
                )
                self.assertEqual(current, [href])
                self.assertIn("<span>{}</span>".format(label), html)

        narrow_navigation = self.styles[
            self.styles.index("@media (max-width: 700px)") :
        ]
        self.assertIn(
            ".lnb-nav { display: flex; gap: var(--space-compact); overflow-x: auto;",
            narrow_navigation,
        )
        self.assertIn(".lnb-item { flex: 0 0 auto;", narrow_navigation)

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
            "기본 작업 Session만",
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

    def test_atlassian_registration_extends_inventory_without_hidden_refresh(self):
        for marker in (
            "data-atlassian-registration",
            'action="/atlassian/register"',
            'action="/atlassian/spaces/discover"',
            'action="/atlassian/spaces/register"',
            "원격 조회 없음",
            "원격 read 1회",
            "일부 후보",
            ">Browser</a>",
            ">Add</a>",
            "등록된 Atlassian 범위",
            "LocalBrain DB에 확정 저장된 Site와 Space만",
            "URL로 추가",
            "연결해서 찾기",
            'name="target_domain"',
            "조회할 Site",
            "사용할 MCP 연결",
            "실행 주체",
            "MCP 접근 관리",
            "data-atlassian-url-preview",
            'action="/atlassian/access"',
            'value_label("external-source.provider"',
            'value_label("atlassian-space.coverage"',
            "원격 접근 설정",
            "atlassian.js",
        ):
            self.assertIn(marker, self.atlassian)
        for retired_copy in (
            "Source Instance / Site",
            "Source Instance는 LocalBrain이 사용할 MCP 연결",
            "Add / discover",
            'name="source_name"',
            'name="site_name"',
            'name="title"',
        ):
            self.assertNotIn(retired_copy, self.atlassian)
        for selected_toggle in (
            """class="{% if selected_view == 'jira' %}selected{% endif %}" """,
            """class="{% if selected_view == 'confluence' %}selected{% endif %}" """,
            """class="{% if selected_mode == 'browse' %}selected{% endif %}" """,
            """class="{% if selected_mode == 'setup' %}selected{% endif %}" """,
        ):
            self.assertIn(selected_toggle, self.atlassian)
        self.assertNotIn(
            """class="{% if selected_view == 'jira' %}active{% endif %}" """,
            self.atlassian,
        )
        for ordinary_behavior in (
            "window.location.hash",
            "focus({ preventScroll: true })",
            "scrollIntoView({ block: \"center\" })",
        ):
            self.assertIn(ordinary_behavior, self.atlassian_script)
        self.assertIn(
            'new Set(["queued", "running", "cancelling"])',
            self.atlassian_script,
        )
        self.assertIn(
            "window.setTimeout(poll, 1500)",
            self.atlassian_script,
        )
        self.assertNotIn("/atlassian/spaces/discover", self.atlassian_script)
        for preview_behavior in (
            "/api/atlassian/registration-preview",
            "syncDiscoveryConnections()",
            "option.dataset.domain !== targetDomain",
        ):
            self.assertIn(preview_behavior, self.atlassian_script)
        for connection_style in (
            ".atlassian-scope-overview, .atlassian-add-flow, .atlassian-connection-management {",
            ".atlassian-add-header {",
            ".atlassian-scope-domain {",
            ".atlassian-connection-management > summary {",
            ".atlassian-connection-row > summary {",
            ".atlassian-url-preview.warning {",
            ".atlassian-add-columns {",
            ".atlassian-access-method {",
        ):
            self.assertIn(connection_style, self.styles)
        for responsive_rule in (
            ".atlassian-add-columns { grid-template-columns: 1fr; }",
            ".atlassian-candidate-row, .atlassian-record { grid-template-columns: 1fr; }",
            ".atlassian-record-meta { justify-items: start; text-align: left; }",
        ):
            self.assertIn(responsive_rule, self.styles)

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
            'data-localbrain-mermaid-layout="elk"',
            "data-localbrain-mermaid-source",
            "data-schema-layout-status",
            "data-schema-source-json",
            "data-schema-diagram-fallback",
            "data-schema-diagram-viewport",
            "data-schema-zoom-controls",
            "data-schema-zoom-out",
            "data-schema-zoom-reset",
            "data-schema-zoom-in",
            "data-schema-zoom-fit",
            "Ctrl/Cmd + 휠",
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
            "data-schema-layout-state",
            'result.layout === "dagre"',
            "setupSchemaDiagramZoom",
            "schemaZoomFromWheel",
            "schemaAnchoredScroll",
            "if (!event.ctrlKey && !event.metaKey) return;",
            "event.preventDefault()",
            '{ passive: false }',
            "rendered.style.width",
            "rendered.style.minWidth",
        ):
            self.assertIn(behavior, self.schema_script)

        for responsive_rule in (
            ".schema-layout { grid-template-columns: 1fr; }",
            ".schema-subject-links { grid-template-columns: repeat(2, minmax(0, 1fr)); }",
            ".schema-subject-links, .schema-table-links, .schema-contract-grid, .schema-relation-groups { grid-template-columns: 1fr; }",
            ".schema-panel-actions { width: 100%; justify-items: start; }",
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

    def test_usage_dashboard_source_identity_is_registry_driven_and_readable(self):
        for marker in (
            "{% for control in usage.controls.sources %}",
            "{{ control.label }}",
            "usage.scope.source_label",
            "source.provider_kind",
            'value_label("source.scan-status", source.scan_status)',
            "source.scan_error",
        ):
            self.assertIn(marker, self.sessions_dashboard)
        self.assertNotIn("control.value == 'all' else", self.sessions_dashboard)
        self.assertIn(
            ".usage-source-control { max-width: 100%; overflow-x: auto;",
            self.styles,
        )
        self.assertIn(".usage-source-control a { flex: 0 0 auto; }", self.styles)

    def test_usage_dashboard_renders_company_scope_and_retained_source_health(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
        connection.execute(
            """
            INSERT INTO sources(
                kind, provider_kind, name, root_path, last_scanned_at,
                last_scan_success_at, last_scan_status, last_scan_error
            ) VALUES (
                'codex-company', 'codex', 'Codex Company', '/synthetic/company',
                '2026-07-18T10:00:00Z', '2026-07-01T08:00:00Z',
                'unavailable',
                'This source was not synchronized; existing data was retained.'
            )
            """
        )
        usage = usage_dashboard_data(
            connection,
            source="codex-company",
            timezone_name="UTC",
            today=date(2026, 7, 18),
        )
        html = template_environment().get_template(
            "sessions_dashboard.html"
        ).render(active_page="sessions-dashboard", usage=usage)
        connection.close()

        self.assertIn('data-usage-value="codex-company"', html)
        self.assertIn(">Codex Company</a>", html)
        self.assertIn("DAILY · CODEX COMPANY", html)
        self.assertIn('class="source-indicator codex"', html)
        self.assertIn("Latest source result · 경로 확인 필요", html)
        self.assertIn("existing data was retained", html)

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
        environment = template_environment()
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
        environment = template_environment()
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
            '[data-usage-control="source"][aria-current="page"]',
            "[source, metric, breakdown]",
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
            "data-context-split",
            "data-context-pane-separator",
            'role="separator"',
            'aria-orientation="vertical"',
            'aria-controls="context-source-tree context-markdown-preview"',
            "data-markdown-body",
            "selected_document.rendered_body",
            "selected_document.render_properties",
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
            'paneSeparator.addEventListener("pointerdown"',
            'paneSeparator.addEventListener("pointermove"',
            'paneSeparator.addEventListener("keydown"',
            "setPointerCapture",
            "releasePointerCapture",
            'Math.max(160, Math.floor(bodyWidth * 0.35))',
            'Math.max(180, Math.floor(bodyWidth * 0.42))',
            'explorerBody.style.setProperty("--context-tree-width"',
            'explorerBody.style.removeProperty("--context-tree-width")',
            'window.matchMedia("(max-width: 700px)")',
            '"ArrowLeft", "ArrowRight"',
            "contextExplorer.addEventListener(\"click\"",
            "markdown-reference-internal[href^='/documents/']",
            "scrollPreviewFragment(destination)",
            "data-context-folder-source-link",
            'const sourceScrollKey = "localbrain:context-source-window-scroll"',
            "savedSourceScroll?.href === window.location.href",
            "restoreSourceScroll",
            "Storage denial must not block ordinary source-link navigation.",
        ):
            self.assertIn(behavior, self.script)

        context_script = self.script[
            self.script.index("const contextExplorer") : self.script.index(
                'document.querySelectorAll("[data-task-run-form]")'
            )
        ]
        self.assertNotIn("localStorage", context_script)
        self.assertNotIn("visibilitychange", context_script)
        self.assertNotIn("blur", context_script)
        splitter_script = context_script[
            context_script.index("if (explorerBody && paneSeparator)") :
            context_script.index("const documentLinks")
        ]
        self.assertNotIn("sessionStorage", splitter_script)
        self.assertNotIn("localStorage", splitter_script)
        self.assertIn("data-context-folder-source-link", self.context)
        for redundant_family in (
            "context-root.source-type",
            "context-root.readable",
            "context-root.enabled",
        ):
            self.assertNotIn(
                'value_label("{}"'.format(redundant_family),
                self.context,
            )
        self.assertEqual(
            self.context.count('value_label("context-root.status"'),
            1,
        )
        self.assertNotIn("depth == 0 or node.contains_selected", self.context_tree)
        self.assertIn("if node.contains_selected", self.context_tree)
        self.assertIn(
            ".context-root-add { margin-top: var(--space-control-gap); padding-top: var(--space-control-gap); }",
            self.styles,
        )
        self.assertIn(
            ".files-group { padding-top: var(--space-card); border-top: var(--border-width-control) solid var(--border-subtle); }",
            self.styles,
        )
        self.assertIn(".markdown-body {", self.styles)
        self.assertIn(".markdown-code-block {", self.styles)
        self.assertIn(".markdown-table-scroll {", self.styles)
        self.assertIn(".markdown-body table {", self.styles)
        self.assertIn("background: var(--surface-code-reading);", self.styles)
        self.assertIn("color: var(--text-code-keyword);", self.styles)
        self.assertIn(".context-pane-separator { display: none; }", self.styles)
        self.assertIn(
            ".source-tree-document > a { height: auto; min-height: var(--control-min-height-touch); }",
            self.styles,
        )

    def test_full_document_reader_reuses_context_tree_and_markdown_contracts(self):
        for marker in (
            "data-document-reader",
            "data-document-reader-source-id",
            "data-document-reader-tree",
            "data-document-reader-link",
            "data-document-reader-return",
            "data-context-href",
            "data-document-reader-content",
            "data-document-reader-status",
            "data-markdown-body",
            "document.rendered_body",
            "document.render_properties",
            'aria-current="page"',
        ):
            self.assertIn(marker, self.document)

        for behavior in (
            'const documentReader = document.querySelector("[data-document-reader]")',
            'treePane.addEventListener("click"',
            'documentReader.addEventListener("click"',
            'headers: { "X-Requested-With": "LocalBrain-Document-Reader" }',
            "new DOMParser()",
            "currentContent.replaceWith(adoptedContent)",
            "window.history.pushState",
            'window.addEventListener("popstate"',
            "AbortController",
            "selectedLink.focus({ preventScroll: true })",
            "scrollReaderDestination(destination)",
            "window.location.assign(destination.href)",
        ):
            self.assertIn(behavior, self.script)

        for rule in (
            ".document-reader.has-context-tree .document-reader-layout {",
            ".document-reader-tree {",
            ".document-reading-content {",
            ".document-reading-body {",
            ".document-reading-empty {",
            ".document-reader.has-context-tree .document-reader-layout { grid-template-columns: 1fr; }",
        ):
            self.assertIn(rule, self.styles)

        self.assertNotIn("| safe", self.document)

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

    def test_sync_report_and_source_inventory_expose_bounded_per_source_health(self):
        for marker in (
            "const scanStatusLabels",
            "function renderScanReport",
            "source.display_label || source.source_key",
            "source.error_message",
            "기존 데이터는 유지됩니다",
        ):
            self.assertIn(marker, self.script)
        for marker in (
            'action="/sources/scan"',
            'id="scan-button" class="primary-button" type="submit"',
            'class="source-health-times"',
            "Last attempt",
            "Last success",
            "Tracked files",
            "Eligible Sessions",
            'class="source-health-error"',
        ):
            self.assertIn(marker, self.sources)
        self.assertIn(
            ".scan-source-result { grid-template-columns: 1fr; }",
            self.styles,
        )
        self.assertIn(
            ".source-cards { grid-template-columns: 1fr; }",
            self.styles,
        )

        html = template_environment().get_template("sources.html").render(
            active_page="sources",
            sync_outcome="partial",
            database_path="/tmp/synthetic.db",
            sources=[
                {
                    "id": 1,
                    "kind": "claude",
                    "provider_kind": "claude",
                    "name": "Claude Code",
                    "root_path": "/synthetic/claude",
                    "last_scanned_at": "2026-08-02T00:00:00Z",
                    "last_scan_success_at": "2026-08-01T00:00:00Z",
                    "last_scan_status": "completed",
                    "last_scan_error": None,
                    "file_count": 3,
                    "session_count": 2,
                    "document_count": 0,
                },
                {
                    "id": 2,
                    "kind": "codex-company",
                    "provider_kind": "codex",
                    "name": "Codex Company",
                    "root_path": "/synthetic/a/very/long/company/source/root",
                    "last_scanned_at": "2026-08-02T01:00:00Z",
                    "last_scan_success_at": "2026-08-01T01:00:00Z",
                    "last_scan_status": "unavailable",
                    "last_scan_error": "This source was not synchronized; existing data was retained.",
                    "file_count": 4,
                    "session_count": 5,
                    "document_count": 0,
                },
            ],
        )
        self.assertIn("일부 로컬 소스에 확인이 필요합니다.", html)
        self.assertIn("Claude Code", html)
        self.assertIn("Codex Company", html)
        self.assertIn("경로 확인 필요", html)
        self.assertIn("existing data was retained", html)

    def test_sync_fallback_notices_keep_complete_partial_and_failed_distinct(self):
        environment = template_environment()
        common = {
            "active_page": "sessions",
            "selected_source": "all",
            "selected_workspace": None,
            "stats": {
                "sessions": 0,
                "events": 0,
                "active_workspaces": 0,
                "missing_workspaces": 0,
            },
            "sessions": [],
            "sources": [],
            "pagination": {
                "total": 0,
                "page": 1,
                "total_pages": 1,
                "page_items": [1],
                "previous_page": None,
                "next_page": None,
            },
        }
        partial = environment.get_template("sessions.html").render(
            sync_outcome="partial", **common
        )
        failed = environment.get_template("sessions.html").render(
            sync_outcome="failed", **common
        )
        self.assertIn("일부 Session 소스에 확인이 필요합니다.", partial)
        self.assertIn('role="alert"', partial)
        self.assertIn("Session 소스를 동기화하지 못했습니다.", failed)

    def test_sessions_sidebar_shows_only_session_sources_without_database_path(self):
        environment = template_environment()
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
                {"kind": "claude", "provider_kind": "claude", "name": "Claude Code", "session_count": 3, "last_scan_status": "completed"},
                {"kind": "codex", "provider_kind": "codex", "name": "Codex", "session_count": 4, "last_scan_status": "completed"},
                {"kind": "context", "provider_kind": "context", "name": "Local Contexts", "document_count": 9, "last_scan_status": "completed"},
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
        environment = template_environment()
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
        environment = template_environment()
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
        self.assertIn(
            ".session-page-number:not(.current):hover { color: var(--text-primary); background: var(--surface-subtle); }",
            self.styles,
        )
        current_page_rule = self.styles[
            self.styles.index(".session-page-number.current {"):
            self.styles.index(".session-page-separator {")
        ]
        self.assertIn("font-weight: var(--type-bold);", current_page_rule)
        self.assertNotIn("background:", current_page_rule)

    def test_session_pagination_tolerates_a_pre_restart_page_model(self):
        environment = template_environment()
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
        self.assertNotIn('class="session-provenance"', self.sessions)
        self.assertIn(
            '<span class="sr-only">{{ session.source_name }} ·',
            self.sessions,
        )
        self.assertIn("{{ child.source_name }} · 질문", self.sessions)

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

    def test_session_source_scopes_keep_compact_accessible_inventory_provenance(self):
        for marker in (
            "{% for source_scope in source_scope_items %}",
            "source_scope.source_key",
            "source_scope.display_label",
            'class="session-source {{ session.source_kind }}"',
            '<span class="sr-only">{{ session.source_name }} ·',
            'class="pinned-session-source {{ pinned_session.source_kind }}"',
            '<span class="sr-only">{{ pinned_session.source_name }}</span>',
            "child.source_name",
        ):
            self.assertIn(marker, self.sessions)
        for marker in (
            "{% macro source_cue(source_kind, provider_kind, display_label)",
            "source_kind == 'codex-company'",
            "'CC'",
            "source_kind == 'codex'",
            "'CX'",
            "provider_kind == 'claude'",
            "'CL'",
        ):
            self.assertIn(marker, self.source_cue)
        self.assertNotIn('class="session-provenance"', self.sessions)
        self.assertNotIn('class="pinned-session-provenance"', self.sessions)
        self.assertNotIn('href="/sessions?source=claude"', self.sessions)
        self.assertNotIn('href="/sessions?source=codex"', self.sessions)
        self.assertIn(
            ".session-source-control { max-width: 100%; overflow-x: auto;",
            self.styles,
        )
        self.assertIn(".session-source-control a { flex: 0 0 auto; }", self.styles)
        for marker in (
            "--surface-source-codex-company: var(--color-blue-100);",
            "--text-source-codex-company: var(--color-blue-600);",
            "--border-source-codex-company: var(--color-blue-600);",
            ".session-source.codex-company {",
            ".pinned-session-source.codex-company {",
        ):
            self.assertIn(marker, self.styles)

    def test_session_details_render_conversations_without_tool_rows(self):
        for template in (self.session_detail, self.subsession_detail):
            self.assertNotIn("event.event_type == 'tool_call'", template)
            self.assertIn("도구 활동은 원본 이벤트", template)
            self.assertIn("표시할 대화 메시지가 없습니다.", template)

        for marker in (
            "parent",
            "상위 Session으로 돌아가기",
            "subsession.url",
            "원본 이벤트",
        ):
            self.assertIn(marker, self.session_detail)

        self.assertNotIn(
            '<p class="eyebrow">{{ session.source_name or value_label("source.kind", session.source_kind) }}',
            self.session_detail,
        )
        self.assertIn(
            '<span class="sr-only">{{ session.source_name or value_label("source.kind", session.source_kind) }} ·',
            self.session_detail,
        )
        self.assertIn(
            '{% if parent %}<p class="eyebrow">{{ value_label("session.role", "subsession") | upper }}</p>{% endif %}',
            self.session_detail,
        )
        self.assertNotIn("{{ subsession.source_name }} · {{ subsession.external_id }}", self.session_detail)
        self.assertIn("<small>{{ subsession.external_id }}</small>", self.session_detail)
        self.assertNotIn("{{ session.source_name | upper }}", self.subsession_detail)
        self.assertIn(
            '<p class="eyebrow">{{ value_label("session.role", "subsession") | upper }} · LAZY VIEW</p>',
            self.subsession_detail,
        )
        self.assertNotIn(
            "이 Session의 직접 하위 Session",
            self.session_detail,
        )
        self.assertNotIn(
            "{{ subsession.external_id }} · 원본 이벤트",
            self.session_detail,
        )
        question_count = self.session_detail.index(
            'class="subsession-question-count"'
        )
        event_count = self.session_detail.index(
            'class="subsession-event-count"'
        )
        event_time = self.session_detail.index(
            '<time datetime="{{ subsession.last_event_at }}"'
        )
        self.assertLess(question_count, event_count)
        self.assertLess(event_count, event_time)
        self.assertIn(
            ".subsession-question-count, .subsession-event-count { justify-self: start; text-align: left; white-space: nowrap; }",
            self.styles,
        )
        self.assertIn(
            "grid-template-columns: 38px minmax(0, 1fr) calc(var(--control-min-height) + var(--space-panel)) calc(var(--control-min-height) + var(--space-card) + var(--space-card)) 100px;",
            self.styles,
        )
        self.assertIn(".subsession-question-count { grid-column: 2; }", self.styles)

        for template in (self.session_detail, self.subsession_detail):
            self.assertNotIn("Subagent", template)
            self.assertNotIn("Subagents", template)
            self.assertIn("Subsession", template)

        self.assertIn('/sessions/{session_id}/subsessions/{file_name}', self.main)
        self.assertIn('/sessions/{session_id}/subagents/{file_name}', self.main)
        self.assertIn("redirect_legacy_subagent_route", self.main)

    def test_session_detail_source_cues_use_stable_source_identity(self):
        for template in (self.sessions, self.session_detail, self.subsession_detail):
            self.assertIn(
                '{% from "_source_cue.html" import source_cue %}',
                template,
            )
        for marker in (
            'class="session-source large {{ session.source_kind }}"',
            "source_cue(session.source_kind, session.provider_kind, session.source_name)",
            'class="session-source {{ subsession.source_kind }}"',
            "source_cue(subsession.source_kind, subsession.provider_kind, subsession.source_name)",
        ):
            self.assertIn(marker, self.session_detail)
        for marker in (
            'class="session-source large {{ session.source_kind }}"',
            "source_cue(session.source_kind, session.provider_kind, session.source_name)",
        ):
            self.assertIn(marker, self.subsession_detail)
        self.assertNotIn(
            'class="session-source large {{ session.provider_kind }}"',
            self.session_detail + self.subsession_detail,
        )

    def test_session_conversations_use_shared_markdown_without_source_guessing(self):
        for template in (self.session_detail, self.subsession_detail):
            self.assertIn('from "_conversation.html" import conversation_message', template)
            self.assertIn("event.rendered_body", template)
            self.assertIn("event.render_properties", template)
            self.assertIn('class="event-text markdown-body"', template)
            self.assertIn("data-conversation-markdown", template)
            self.assertIn('<div class="event-text">{{ event.text }}</div>', template)
            self.assertNotIn("| safe", template)

        for marker in (
            "conversation_event_views(",
            "session_conversation_events(connection, session_id)",
            "event.event_type == \"message\"",
        ):
            self.assertIn(marker, self.main)

        for rule in (
            ".conversation-markdown-properties {",
            ".event-text.markdown-body {",
            ".event-text.markdown-body > pre { max-width: 100%; overflow-x: auto; }",
            "span.markdown-math { display: inline-block; vertical-align: middle; }",
            "white-space: normal;",
            ".event-text.markdown-body h1 { font-size: var(--type-title-size);",
            ".event-text.markdown-body h2 { font-size: var(--type-body-size);",
        ):
            self.assertIn(rule, self.styles)

    def test_atlassian_refresh_is_an_explicit_local_preview_and_one_run_handoff(self):
        for marker in (
            "EXPLICIT REMOTE REFRESH",
            "LOCAL PREVIEW",
            "preview는 원격 조회 없음",
            'name="item_id"',
            'name="include_catalog"',
            "예상 remote reads",
            "1 maintenance Run",
            "host-side read executor",
            "실패한",
        ):
            self.assertIn(marker, self.atlassian_refresh)
        for contextual in (
            "/atlassian/refresh?scope=all_known",
            "/atlassian/refresh?scope=space",
            "/atlassian/refresh?scope=item",
        ):
            self.assertIn(contextual, self.atlassian)
        self.assertIn(
            "/atlassian/refresh?scope=workstream", self.workstream
        )
        self.assertIn("/atlassian/refresh?scope=thread", self.workstream)
        for behavior in (
            "[data-refresh-item]",
            "requestCount",
            "calls > budget",
            "/api/runs/",
            'window.location.reload()',
        ):
            self.assertIn(behavior, self.atlassian_refresh_script)
        for rule in (
            ".atlassian-refresh-summary {",
            ".atlassian-refresh-row {",
            ".atlassian-refresh-submit {",
            ".atlassian-refresh-outcomes {",
        ):
            self.assertIn(rule, self.styles)

    def test_atlassian_knowledge_browse_keeps_source_regions_separate(self):
        for marker in (
            "LOCAL KNOWLEDGE BASE",
            'name="source_instance_id"',
            'name="coverage"',
            'name="freshness"',
            'name="attention"',
            'name="topic_id"',
            'name="tag_id"',
            'name="workstream_id"',
            "/atlassian/items/{{ item.id }}",
            'target="_blank" rel="noreferrer"',
        ):
            self.assertIn(marker, self.atlassian)
        for marker in (
            "REMOTE FACTS · LAST KNOWN",
            "LOCAL ONLY",
            "LOCAL EVIDENCE",
            "REFRESH STATE",
            'name="note"',
            'name="new_topic_name"',
            'name="tags"',
            'action="/atlassian/items/{{ item.id }}/links"',
        ):
            self.assertIn(marker, self.atlassian_item)
        for marker in (
            "Atlassian 필터",
            "result.match_roles",
            "/atlassian/items/{{ result.entity_id }}",
            "result.normalized_domain",
        ):
            self.assertIn(marker, self.search)
        for marker in (
            ".atlassian-filter-form {",
            ".atlassian-knowledge-row {",
            ".atlassian-detail-grid {",
            ".atlassian-fact-grid {",
            ".atlassian-local-form {",
            ".atlassian-evidence-row, .atlassian-run-summary {",
        ):
            self.assertIn(marker, self.styles)


if __name__ == "__main__":
    unittest.main()
