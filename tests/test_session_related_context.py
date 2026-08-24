import sqlite3
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from starlette.requests import Request

from localbrain.ingest.common import ParsedReferenceCandidate
from localbrain.main import app, show_session
from localbrain.session_context import (
    EVIDENCE_LABELS,
    RELATED_CONTEXT_LIMIT,
    session_related_context,
)
from localbrain.session_references import reconcile_session_references


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "src/localbrain/schema.sql"


class SessionRelatedContextTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.connection.executescript(
            """
            INSERT INTO sources(id, kind, provider_kind, name, root_path)
            VALUES
                (1, 'codex', 'codex', 'Codex', '/synthetic/codex'),
                (2, 'context', 'context', 'Local Context', '/synthetic/context');

            INSERT INTO workspaces(id, canonical_path, display_name, exists_now)
            VALUES
                (1, '/synthetic/work', 'Synthetic Work', 1),
                (2, '/synthetic/other', 'Other Work', 1);

            INSERT INTO context_roots(id, path, label, enabled)
            VALUES
                (1, '/synthetic/context', 'Synthetic Context', 1),
                (2, '/synthetic/disabled', 'Disabled Context', 0);

            INSERT INTO sessions(
                id, source_id, workspace_id, external_id, source_path, cwd_raw,
                title, started_at, last_event_at, session_class, session_role
            ) VALUES (
                10, 1, 1, 'session-a', '/synthetic/session-a.jsonl',
                '/synthetic/work', 'Session A',
                '2026-07-24T01:00:00+00:00',
                '2026-07-24T02:00:00+00:00', 'work', 'primary'
            );

            INSERT INTO atlassian_sites(
                id, normalized_domain, display_name, canonical_base_url
            ) VALUES (
                30, 'jira.example.test', 'Synthetic Jira',
                'https://jira.example.test'
            );
            INSERT INTO external_resources(id, resource_type, title, url)
            VALUES (
                40, 'jira_issue', 'Shared bootstrap title',
                'https://jira.example.test/browse/SYN-62'
            );
            INSERT INTO atlassian_items(
                external_resource_id, site_id, service, item_type, remote_key
            ) VALUES (40, 30, 'jira', 'jira_issue', 'SYN-62');
            INSERT INTO atlassian_item_urls(
                external_resource_id, site_id, url_role, observed_url,
                normalized_url
            ) VALUES (
                40, 30, 'canonical',
                'https://jira.example.test/browse/SYN-62',
                'https://jira.example.test/browse/SYN-62'
            );
            """
        )

    def tearDown(self):
        self.connection.close()

    def _candidate(
        self,
        reference: str,
        *,
        reference_kind: str = "url",
        evidence_kind: str = "user_mention",
        line: int = 1,
        ordinal: int = 1,
        event: str = "event-1",
        outcome=None,
        tool_name=None,
        call_id=None,
        observed_at=None,
    ) -> ParsedReferenceCandidate:
        return ParsedReferenceCandidate(
            reference_kind=reference_kind,
            reference=reference,
            evidence_kind=evidence_kind,
            source_line=line,
            evidence_ordinal=ordinal,
            source_event_id=event,
            tool_name=tool_name,
            tool_call_id=call_id,
            read_outcome=outcome,
            observed_at=observed_at,
        )

    def _reconcile(self, candidates) -> None:
        reconcile_session_references(
            self.connection,
            session_id=10,
            source_path="/synthetic/session-a.jsonl",
            source_size_bytes=100,
            source_mtime_ns=200,
            candidates=candidates,
        )

    def _document(
        self,
        title: str,
        *,
        workspace_id: int = 1,
        root_id: int = 1,
        number: int,
    ) -> int:
        slug = "document-{:03d}".format(number)
        return self.connection.execute(
            """
            INSERT INTO context_documents(
                source_id, context_root_id, workspace_id, path, relative_path,
                title, body, size_bytes, mtime_ns, content_hash
            ) VALUES (2, ?, ?, ?, ?, ?, 'synthetic body', 14, ?, ?)
            """,
            (
                root_id,
                workspace_id,
                "/synthetic/context/{}.md".format(slug),
                "{}.md".format(slug),
                title,
                number + 1,
                "{:064x}".format(number + 1),
            ),
        ).lastrowid

    def _external(self, title: str, url: str) -> int:
        return self.connection.execute(
            """
            INSERT INTO external_resources(resource_type, title, url)
            VALUES ('url', ?, ?)
            """,
            (title, url),
        ).lastrowid

    def _link(
        self,
        table: str,
        scope_column: str,
        scope_id: int,
        entity_type: str,
        entity_id: int,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO {}({}, entity_type, entity_id)
            VALUES (?, ?, ?)
            """.format(table, scope_column),
            (scope_id, entity_type, str(entity_id)),
        )

    def _work(self) -> tuple[int, int]:
        workstream_id = self.connection.execute(
            "INSERT INTO workstreams(name) VALUES ('Synthetic Workstream')"
        ).lastrowid
        thread_id = self.connection.execute(
            """
            INSERT INTO threads(workstream_id, title)
            VALUES (?, 'Synthetic Thread')
            """,
            (workstream_id,),
        ).lastrowid
        self._link(
            "thread_links", "thread_id", thread_id, "session", 10
        )
        return workstream_id, thread_id

    @staticmethod
    def _group(view: dict, key: str) -> dict:
        return next(group for group in view["groups"] if group["key"] == key)

    def test_direct_session_evidence_is_primary_and_uses_observed_identity(self):
        workstream_id, _ = self._work()
        self._link(
            "workstream_links", "workstream_id", workstream_id, "external", 40
        )
        target = "https://jira.example.test/browse/SYN-62"
        self._reconcile(
            [
                self._candidate(target, line=1, event="user-1"),
                self._candidate(
                    target,
                    evidence_kind="assistant_mention",
                    line=2,
                    event="assistant-1",
                ),
                self._candidate(
                    "SYN-62",
                    reference_kind="jira_key",
                    evidence_kind="resource_read",
                    outcome="failure",
                    tool_name="jira__get_issue",
                    call_id="call-failed",
                    line=3,
                    event="result-failed",
                ),
                self._candidate(
                    target,
                    evidence_kind="tool_result",
                    tool_name="jira__get_issue",
                    call_id="call-success",
                    line=4,
                    event="result-success",
                ),
                self._candidate(
                    "SYN-62",
                    reference_kind="jira_key",
                    evidence_kind="resource_read",
                    outcome="success",
                    tool_name="jira__get_issue",
                    call_id="call-success",
                    line=4,
                    event="result-success",
                ),
            ]
        )

        view = session_related_context(self.connection, 10, 1)
        direct = self._group(view, "direct")
        organization = self._group(view, "organization")
        item = direct["items"][0]

        self.assertEqual(view["state"], "ready")
        self.assertEqual(item["identity"], "SYN-62")
        self.assertNotEqual(item["identity"], "Shared bootstrap title")
        self.assertEqual(item["href"], "/atlassian/items/40")
        self.assertEqual(
            [evidence["label"] for evidence in item["evidence"]],
            [
                "MCP 조회",
                "도구 결과에서 확인",
                "사용자 메시지에서 언급",
                "Agent 응답에서 언급",
            ],
        )
        self.assertNotIn("MCP 조회 실패", [e["label"] for e in item["evidence"]])
        self.assertEqual(item["organization"][0]["kind"], "workstream")
        self.assertEqual(organization["items"], [])

    def test_failure_only_read_remains_truthful(self):
        self._reconcile(
            [
                self._candidate(
                    "SYN-62",
                    reference_kind="jira_key",
                    evidence_kind="resource_read",
                    outcome="failure",
                    tool_name="jira__get_issue",
                    call_id="call-failed",
                    line=1,
                    event="result-failed",
                )
            ]
        )

        direct = self._group(
            session_related_context(self.connection, 10), "direct"
        )

        self.assertEqual(
            [evidence["label"] for evidence in direct["items"][0]["evidence"]],
            ["MCP 조회 실패"],
        )

    def test_generic_url_deduplicates_query_variant_under_direct_group(self):
        workstream_id, _ = self._work()
        resource_id = self._external(
            "Shared URL title",
            "https://example.test/reference?private=value#section",
        )
        self._link(
            "workstream_links",
            "workstream_id",
            workstream_id,
            "external",
            resource_id,
        )
        self._reconcile(
            [
                self._candidate(
                    "https://example.test/reference?other=value#different"
                )
            ]
        )

        view = session_related_context(self.connection, 10)
        direct = self._group(view, "direct")
        organization = self._group(view, "organization")

        self.assertEqual(direct["items"][0]["href"], "https://example.test/reference")
        self.assertEqual(len(direct["items"][0]["organization"]), 1)
        self.assertEqual(organization["items"], [])
        self.assertEqual(organization["total"], 0)

    def test_generic_url_projection_repairs_legacy_sentence_suffix(self):
        target = (
            "https://chat.example.test/archives/"
            "SYNTHETIC/p1234567890123456"
        )
        self._reconcile([self._candidate(target)])
        self.connection.execute(
            """
            UPDATE session_reference_evidence
            SET observed_identity = ?, normalized_url = ?
            WHERE session_id = 10 AND target_kind = 'url'
            """,
            (target.removeprefix("https://") + ")와", target + ")와"),
        )

        direct = self._group(
            session_related_context(self.connection, 10), "direct"
        )
        item = direct["items"][0]

        self.assertEqual(item["href"], target)
        self.assertEqual(item["identity"], target.removeprefix("https://"))
        self.assertNotIn(")와", item["identity"])

    def test_material_kinds_are_alphabetic_and_direct_items_follow_first_occurrence(self):
        self._document("Synthetic Guide", number=1)
        self._reconcile(
            [
                self._candidate(
                    "https://newer.example.test/reference",
                    evidence_kind="resource_read",
                    outcome="success",
                    tool_name="approved__read",
                    call_id="call-newer",
                    line=2,
                    event="newer-read",
                    observed_at="2026-07-24T03:00:00+00:00",
                ),
                self._candidate(
                    "/synthetic/context/document-001.md",
                    reference_kind="markdown",
                    line=3,
                    event="markdown",
                    observed_at="2026-07-24T02:00:00+00:00",
                ),
                self._candidate(
                    "SYN-62",
                    reference_kind="jira_key",
                    line=4,
                    event="jira",
                    observed_at="2026-07-24T04:00:00+00:00",
                ),
                self._candidate(
                    "https://older.example.test/reference",
                    line=20,
                    event="older-mention",
                    observed_at="2026-07-24T01:00:00+00:00",
                ),
            ]
        )

        direct = self._group(
            session_related_context(self.connection, 10), "direct"
        )

        self.assertEqual(
            [section["label"] for section in direct["initial_sections"]],
            ["JIRA", "MARKDOWN", "URL"],
        )
        url_section = direct["initial_sections"][2]
        self.assertEqual(
            [item["href"] for item in url_section["rows"]],
            [
                "https://older.example.test/reference",
                "https://newer.example.test/reference",
            ],
        )

    def test_only_explicit_organization_links_are_candidates(self):
        linked_id = self._document("Explicit Document", number=1)
        workspace_only_id = self._document("Workspace Only", number=2)
        other_workspace_id = self._document(
            "Other Workspace", workspace_id=2, number=3
        )
        disabled_id = self._document(
            "Disabled Document", root_id=2, number=4
        )
        workstream_id, thread_id = self._work()
        self._link(
            "thread_links", "thread_id", thread_id, "document", linked_id
        )
        self._link(
            "workstream_links",
            "workstream_id",
            workstream_id,
            "document",
            other_workspace_id,
        )
        self._link(
            "workstream_links",
            "workstream_id",
            workstream_id,
            "document",
            disabled_id,
        )
        self._link(
            "thread_links", "thread_id", thread_id, "external", 999999
        )

        view = session_related_context(self.connection, 10, 1)
        organization = self._group(view, "organization")
        keys = {item["target_key"] for item in organization["items"]}

        self.assertEqual(view["state"], "partial")
        self.assertIn("document:{}".format(linked_id), keys)
        self.assertIn("document:{}".format(other_workspace_id), keys)
        self.assertNotIn("document:{}".format(workspace_only_id), keys)
        self.assertNotIn("document:{}".format(disabled_id), keys)
        self.assertEqual(
            organization["items"][0]["organization"][0]["kind"], "thread"
        )
        self.assertEqual(
            organization["notices"],
            ["대상을 찾을 수 없는 연결 2개는 표시하지 않았습니다."],
        )

    def test_same_workspace_without_evidence_or_membership_is_empty(self):
        self._document("Workspace Only", number=1)
        self._document("Recent Other Workspace", workspace_id=2, number=2)

        view = session_related_context(self.connection, 10, 1)

        self.assertEqual(view["state"], "empty")
        self.assertEqual(view["item_count"], 0)
        self.assertEqual(
            [group["total"] for group in view["groups"]], [0, 0]
        )

    def test_groups_show_up_to_one_hundred_items_by_default(self):
        direct_candidates = [
            self._candidate(
                "https://direct.example.test/{:02d}".format(number),
                line=number + 1,
                event="direct-{}".format(number),
            )
            for number in range(12)
        ]
        self._reconcile(direct_candidates)
        workstream_id, _ = self._work()
        for number in range(13):
            resource_id = self._external(
                "Organization {:02d}".format(number),
                "https://organization.example.test/{:02d}".format(number),
            )
            self._link(
                "workstream_links",
                "workstream_id",
                workstream_id,
                "external",
                resource_id,
            )

        view = session_related_context(self.connection, 10)
        direct = self._group(view, "direct")
        organization = self._group(view, "organization")

        self.assertEqual(RELATED_CONTEXT_LIMIT, 100)
        self.assertEqual(
            (direct["total"], len(direct["initial_items"]), direct["overflow_count"]),
            (12, 12, 0),
        )
        self.assertEqual(
            (
                organization["total"],
                len(organization["initial_items"]),
                organization["overflow_count"],
            ),
            (13, 13, 0),
        )

    def test_direct_safety_boundary_reports_observed_total(self):
        self._reconcile(
            [
                self._candidate(
                    "https://reference.example.test/{:03d}".format(number),
                    line=number + 1,
                    event="reference-{}".format(number),
                )
                for number in range(101)
            ]
        )

        direct = self._group(
            session_related_context(self.connection, 10), "direct"
        )

        self.assertTrue(direct["partial"])
        self.assertEqual((direct["total"], len(direct["items"])), (101, 100))
        self.assertEqual(
            direct["notices"], ["총 101개 중 100개까지 확인했습니다."]
        )

    def test_unsafe_and_missing_organization_targets_remain_explicit(self):
        workstream_id, _ = self._work()
        unsafe_id = self._external(
            "Unsafe Destination", "javascript:alert(1)"
        )
        local_id = self.connection.execute(
            """
            INSERT INTO local_resources(path, resource_type, title, exists_now)
            VALUES ('/synthetic/missing', 'path', 'Missing Local Path', 0)
            """
        ).lastrowid
        self._link(
            "workstream_links",
            "workstream_id",
            workstream_id,
            "external",
            unsafe_id,
        )
        self._link(
            "workstream_links",
            "workstream_id",
            workstream_id,
            "local",
            local_id,
        )

        organization = self._group(
            session_related_context(self.connection, 10), "organization"
        )
        items = {item["target_key"]: item for item in organization["items"]}

        self.assertIsNone(items["external:{}".format(unsafe_id)]["href"])
        self.assertEqual(
            items["external:{}".format(unsafe_id)]["availability_label"],
            "열 수 없음",
        )
        self.assertEqual(
            items["local:{}".format(local_id)]["availability_label"],
            "경로 없음",
        )
        self.assertTrue(organization["partial"])

    def test_projection_does_not_open_session_or_document_files(self):
        self._reconcile(
            [self._candidate("https://example.test/reference")]
        )

        with patch.object(Path, "open", side_effect=AssertionError("file read")):
            view = session_related_context(self.connection, 10, 1)

        self.assertEqual(view["item_count"], 1)

    @contextmanager
    def _connection(self):
        yield self.connection

    @staticmethod
    def _request(session_id: int = 10) -> Request:
        path = "/sessions/{}".format(session_id)
        return Request(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": path,
                "raw_path": path.encode("utf-8"),
                "query_string": b"",
                "headers": [],
                "client": ("test", 50000),
                "server": ("test", 80),
                "root_path": "",
                "app": app,
                "router": app.router,
            }
        )

    def test_local_query_error_does_not_block_conversation_surface(self):
        with patch("localbrain.main.connect", self._connection), patch(
            "localbrain.main.session_related_context",
            side_effect=RuntimeError("synthetic projection failure"),
        ):
            response = show_session(self._request(), 10)

        html = response.body.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("관련 자료를 불러오지 못했습니다", html)
        self.assertIn("Session 대화는 계속 읽을 수 있습니다", html)
        self.assertIn("<h2>대화</h2>", html)

    def test_detail_route_renders_each_alphabetic_kind_heading_once(self):
        self._document("Synthetic Guide", number=1)
        self._reconcile(
            [
                self._candidate(
                    "https://reference.example.test/path",
                    observed_at="2026-07-24T01:00:00+00:00",
                ),
                self._candidate(
                    "/synthetic/context/document-001.md",
                    reference_kind="markdown",
                    line=2,
                    event="markdown",
                    observed_at="2026-07-24T02:00:00+00:00",
                ),
                self._candidate(
                    "SYN-62",
                    reference_kind="jira_key",
                    line=3,
                    event="jira",
                    observed_at="2026-07-24T03:00:00+00:00",
                ),
            ]
        )
        with patch("localbrain.main.connect", self._connection):
            response = show_session(self._request(), 10)

        html = response.body.decode("utf-8")
        markers = [">JIRA</h4>", ">MARKDOWN</h4>", ">URL</h4>"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual([html.count(marker) for marker in markers], [1, 1, 1])
        self.assertLess(html.index(markers[0]), html.index(markers[1]))
        self.assertLess(html.index(markers[1]), html.index(markers[2]))
        self.assertNotIn("<span>Jira</span>", html)
        self.assertNotIn("<span>Markdown</span>", html)
        self.assertNotIn("<span>URL</span>", html)
        self.assertIn(
            '<h3 id="related-material-group-organization">연결된 작업</h3>',
            html,
        )
        self.assertIn('<span aria-label="총 0개">0</span>', html)

    def test_persisted_subsession_detail_has_no_related_materials_rail(self):
        self.connection.execute(
            """
            INSERT INTO sessions(
                id, source_id, workspace_id, external_id, source_path, cwd_raw,
                title, session_class, session_role, parent_session_id
            ) VALUES (
                11, 1, 1, 'session-child', '/synthetic/child.jsonl',
                '/synthetic/work', 'Child Session', 'work', 'subsession', 10
            )
            """
        )
        with patch("localbrain.main.connect", self._connection):
            response = show_session(self._request(11), 11)

        self.assertNotIn(
            'class="session-related-context"', response.body.decode("utf-8")
        )


class SessionRelatedContextUiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session_template = (
            ROOT / "src/localbrain/templates/session.html"
        ).read_text(encoding="utf-8")
        cls.related_template = (
            ROOT / "src/localbrain/templates/_session_related_context.html"
        ).read_text(encoding="utf-8")
        cls.styles = (
            ROOT / "src/localbrain/static/styles.css"
        ).read_text(encoding="utf-8")
        cls.projection = (
            ROOT / "src/localbrain/session_context.py"
        ).read_text(encoding="utf-8")

    def test_compact_dom_order_matches_identity_materials_conversation(self):
        orientation = self.session_template.index(
            'class="session-detail-orientation"'
        )
        related = self.session_template.index(
            '{% include "_session_related_context.html" %}'
        )
        timeline = self.session_template.index('class="timeline-section"')

        self.assertLess(orientation, related)
        self.assertLess(related, timeline)
        self.assertIn(
            ".session-detail-layout.has-related-context .session-related-context { position: static; grid-column: 1; grid-row: 2; max-height: none; }",
            self.styles,
        )
        self.assertIn(
            ".session-detail-layout.has-related-context .timeline-section { grid-column: 1; grid-row: 3; }",
            self.styles,
        )

    def test_rail_uses_approved_groups_evidence_and_native_disclosure(self):
        for marker in (
            "관련 자료",
            "group.label",
            "group.total",
            "section.label",
            "item.identity",
            "item.detail",
            "evidence.label",
            'rel="noopener noreferrer external"',
            '<details class="related-material-disclosure">',
            "group.overflow_count",
            "접기",
            "같은 경로나 최근 문서를 대신 표시하지 않습니다.",
        ):
            self.assertIn(marker, self.related_template)
        for label in EVIDENCE_LABELS.values():
            self.assertIn(label, self.projection)
        self.assertNotIn("대화에서 보기", self.related_template)
        self.assertNotIn("related_context.item_count", self.related_template)
        self.assertNotIn("item.kind_label", self.related_template)
        self.assertNotIn("same-workspace", self.projection)
        self.assertNotIn("_workspace_document_candidates", self.projection)
        self.assertIn("RELATED_CONTEXT_LIMIT = 100", self.projection)
        self.assertIn("group.initial_sections is defined", self.related_template)
        self.assertIn(
            "group['items'] | groupby('kind_label', case_sensitive=false)",
            self.related_template,
        )
        self.assertNotIn("if group.items", self.related_template)
        self.assertIn("group.key == 'organization'", self.related_template)
        self.assertIn(
            ".related-material-disclosure[open] summary { order: 2;",
            self.styles,
        )
        self.assertIn(
            ".related-material-disclosure[open] { display: flex; flex-direction: column; }",
            self.styles,
        )
        disclosure = self.related_template.split(
            '<details class="related-material-disclosure">', 1
        )[1].split("</details>", 1)[0]
        self.assertLess(
            disclosure.index('class="related-material-additional"'),
            disclosure.index("<summary>"),
        )

    def test_rail_preserves_tokens_focus_containment_and_responsive_flow(self):
        self.assertIn("position: sticky;", self.styles)
        self.assertIn("var(--rail-context-width)", self.styles)
        self.assertIn('class="session-related-context-scroll"', self.related_template)
        self.assertIn(
            "max-height: calc(100vh - var(--shell-sticky-offset) - var(--space-section));",
            self.styles,
        )
        self.assertIn("overflow-y: auto;", self.styles)
        self.assertIn("overscroll-behavior: contain;", self.styles)
        self.assertIn("padding-right: var(--space-card);", self.styles)
        self.assertIn("scrollbar-gutter: stable;", self.styles)
        self.assertIn(
            ".session-detail-layout.has-related-context .session-related-context { position: static; grid-column: 1; grid-row: 2; max-height: none; }",
            self.styles,
        )
        self.assertIn(
            ".session-related-context-scroll { overflow-y: visible; padding-right: var(--space-none); overscroll-behavior: auto; scrollbar-gutter: auto; }",
            self.styles,
        )
        self.assertIn(
            ".related-material-item > strong,\n.related-material-detail,\n.related-material-organization { overflow-wrap: anywhere; }",
            self.styles,
        )
        self.assertIn(
            ".related-material-group-heading h3 { margin: var(--space-none); font-size: var(--type-body-small-size); }",
            self.styles,
        )
        self.assertIn(
            ".related-material-kind-section:not(:last-child) { margin-bottom: var(--space-card); padding-bottom: var(--space-row-block); border-bottom: var(--border-width-focus) solid var(--border-subtle); }",
            self.styles,
        )
        item_rule = self.styles.split(".related-material-item {", 1)[1].split(
            "}", 1
        )[0]
        self.assertNotIn("border", item_rule)
        self.assertNotIn(".related-material-item:last-child", self.styles)
        self.assertIn(
            ".related-material-item > strong { font-size: var(--type-label-size); font-weight: var(--type-semibold); }",
            self.styles,
        )
        self.assertIn(
            ":where(a, button, input, select, textarea, summary):focus-visible",
            self.styles,
        )
        self.assertIn("min-height: var(--control-min-height-touch)", self.styles)
        self.assertIn("color: var(--text-link)", self.styles)
        self.assertIn("background: var(--surface-default)", self.styles)


if __name__ == "__main__":
    unittest.main()
