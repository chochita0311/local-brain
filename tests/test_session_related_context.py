import sqlite3
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from starlette.requests import Request

from localbrain.atlassian import (
    create_or_reuse_atlassian_stub,
    register_atlassian_site,
)
from localbrain.external_access import register_source_instance
from localbrain.main import app, show_session
from localbrain.session_context import (
    RELATED_CONTEXT_LIMIT,
    session_related_context,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "src/localbrain/schema.sql"


class SessionRelatedContextTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.session_source_id = self.connection.execute(
            """
            INSERT INTO sources(kind, name, root_path)
            VALUES ('codex', 'Codex', '/synthetic/codex')
            """
        ).lastrowid
        self.context_source_id = self.connection.execute(
            """
            INSERT INTO sources(kind, name, root_path)
            VALUES ('context', 'Local Context', '/synthetic/context')
            """
        ).lastrowid
        self.workspace_id = self.connection.execute(
            """
            INSERT INTO workspaces(
                canonical_path, display_name, git_root, exists_now
            ) VALUES ('/synthetic/work', 'Synthetic Work', '/synthetic/work', 1)
            """
        ).lastrowid
        self.other_workspace_id = self.connection.execute(
            """
            INSERT INTO workspaces(
                canonical_path, display_name, exists_now
            ) VALUES ('/synthetic/other', 'Other Work', 1)
            """
        ).lastrowid
        self.enabled_root_id = self.connection.execute(
            """
            INSERT INTO context_roots(path, label, enabled)
            VALUES ('/synthetic/context', 'Synthetic Context', 1)
            """
        ).lastrowid
        self.disabled_root_id = self.connection.execute(
            """
            INSERT INTO context_roots(path, label, enabled)
            VALUES ('/synthetic/disabled', 'Disabled Context', 0)
            """
        ).lastrowid
        self.session_id = self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, workspace_id, external_id, source_path, cwd_raw,
                title, started_at, last_event_at, session_class, session_role
            ) VALUES (?, ?, 'session-a', '/synthetic/session-a.jsonl',
                      '/synthetic/work', 'Session A',
                      '2026-07-24T01:00:00+00:00',
                      '2026-07-24T02:00:00+00:00', 'work', 'primary')
            """,
            (self.session_source_id, self.workspace_id),
        ).lastrowid

    def tearDown(self):
        self.connection.close()

    def _document(
        self,
        title: str,
        *,
        workspace_id: int,
        root_id: int,
        mtime_ns: int,
    ) -> int:
        return self.connection.execute(
            """
            INSERT INTO context_documents(
                source_id, context_root_id, workspace_id, path, relative_path,
                title, body, size_bytes, mtime_ns, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, 'synthetic body', 14, ?, ?)
            """,
            (
                self.context_source_id,
                root_id,
                workspace_id,
                "/synthetic/{}/{}.md".format(root_id, title.lower().replace(" ", "-")),
                "{}.md".format(title.lower().replace(" ", "-")),
                title,
                mtime_ns,
                "{:064x}".format(mtime_ns),
            ),
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

    def _atlassian_item(self) -> int:
        source = register_source_instance(
            self.connection,
            instance_key="synthetic-related-jira",
            provider_kind="mcp_gateway",
            service="jira",
            display_name="Synthetic Jira",
            config_ref="synthetic-related-jira",
        )
        register_atlassian_site(
            self.connection,
            source_instance_id=source["id"],
            base_url="https://jira.example.test",
            display_name="Synthetic Jira Site",
        )
        item = create_or_reuse_atlassian_stub(
            self.connection,
            source_instance_id=source["id"],
            url="https://jira.example.test/browse/REL-1",
            title="Referenced Jira Item",
        )
        item_id = int(item["external_resource_id"])
        self.connection.execute(
            """
            INSERT INTO atlassian_item_evidence(
                external_resource_id, session_id, source_path,
                source_channel, source_event_id, source_line, url_ordinal,
                observed_url, normalized_url, observed_title,
                extractor_version, evidence_key,
                first_observed_at, last_observed_at
            ) VALUES (?, ?, '/synthetic/session-a.jsonl', 'visible_text',
                      'event-1', 1, 1, ?, ?, 'Referenced Jira Item',
                      'synthetic-v1', ?, ?, ?)
            """,
            (
                item_id,
                self.session_id,
                "https://jira.example.test/browse/REL-1",
                "https://jira.example.test/browse/REL-1",
                "a" * 64,
                "2026-07-24T02:00:00+00:00",
                "2026-07-24T02:00:00+00:00",
            ),
        )
        return item_id

    def test_projection_uses_only_approved_reasons_and_deduplicates(self):
        related_document_id = self._document(
            "Related Document",
            workspace_id=self.workspace_id,
            root_id=self.enabled_root_id,
            mtime_ns=10,
        )
        workspace_document_id = self._document(
            "Workspace Only",
            workspace_id=self.workspace_id,
            root_id=self.enabled_root_id,
            mtime_ns=20,
        )
        unrelated_recent_id = self._document(
            "Recent But Unrelated",
            workspace_id=self.other_workspace_id,
            root_id=self.enabled_root_id,
            mtime_ns=999999999999,
        )
        disabled_id = self._document(
            "Disabled Document",
            workspace_id=self.workspace_id,
            root_id=self.disabled_root_id,
            mtime_ns=30,
        )
        workstream_id = self.connection.execute(
            "INSERT INTO workstreams(name) VALUES ('Related Work')"
        ).lastrowid
        thread_id = self.connection.execute(
            """
            INSERT INTO threads(workstream_id, title)
            VALUES (?, 'Related Thread')
            """,
            (workstream_id,),
        ).lastrowid
        self._link(
            "thread_links", "thread_id", thread_id, "session", self.session_id
        )
        self._link(
            "thread_links",
            "thread_id",
            thread_id,
            "document",
            related_document_id,
        )
        local_id = self.connection.execute(
            """
            INSERT INTO local_resources(
                path, resource_type, title, exists_now
            ) VALUES ('/synthetic/missing', 'path', 'Missing Local Path', 0)
            """
        ).lastrowid
        self._link("thread_links", "thread_id", thread_id, "local", local_id)
        external_id = self.connection.execute(
            """
            INSERT INTO external_resources(resource_type, title, url)
            VALUES ('url', 'Related External', 'https://example.test/context')
            """
        ).lastrowid
        self._link(
            "workstream_links",
            "workstream_id",
            workstream_id,
            "external",
            external_id,
        )
        self._link(
            "thread_links", "thread_id", thread_id, "external", 999999
        )
        item_id = self._atlassian_item()
        self._link(
            "workstream_links",
            "workstream_id",
            workstream_id,
            "external",
            item_id,
        )

        view = session_related_context(
            self.connection, self.session_id, self.workspace_id
        )
        repeated = session_related_context(
            self.connection, self.session_id, self.workspace_id
        )

        self.assertEqual(view, repeated)
        self.assertEqual(view["state"], "partial")
        self.assertEqual(view["unavailable_count"], 1)
        self.assertEqual(view["visible_unavailable_count"], 1)
        items = {item["target_key"]: item for item in view["items"]}
        self.assertNotIn("document:{}".format(unrelated_recent_id), items)
        self.assertNotIn("document:{}".format(disabled_id), items)
        self.assertIn("document:{}".format(workspace_document_id), items)
        self.assertEqual(
            [reason["code"] for reason in items["external:{}".format(item_id)]["reasons"]],
            ["session-reference", "same-workstream"],
        )
        self.assertEqual(
            [
                reason["code"]
                for reason in items[
                    "document:{}".format(related_document_id)
                ]["reasons"]
            ],
            ["same-thread", "same-workstream", "same-workspace"],
        )
        self.assertEqual(
            items["local:{}".format(local_id)]["availability_label"],
            "경로 없음",
        )
        self.assertTrue(items["external:{}".format(external_id)]["external"])
        self.assertEqual(view["items"][0]["target_key"], "external:{}".format(item_id))

    def test_total_limit_is_deterministic_and_reports_overflow(self):
        for number in range(RELATED_CONTEXT_LIMIT + 5):
            self._document(
                "Document {:02d}".format(number),
                workspace_id=self.workspace_id,
                root_id=self.enabled_root_id,
                mtime_ns=number + 1,
            )

        view = session_related_context(
            self.connection, self.session_id, self.workspace_id
        )

        self.assertEqual(len(view["items"]), RELATED_CONTEXT_LIMIT)
        self.assertEqual(view["overflow_count"], 5)
        self.assertEqual(view["state"], "partial")
        self.assertEqual(
            [item["title"] for item in view["items"]],
            ["Document {:02d}".format(number) for number in range(12)],
        )

    def test_global_recency_alone_returns_empty(self):
        self._document(
            "Recent Other Workspace",
            workspace_id=self.other_workspace_id,
            root_id=self.enabled_root_id,
            mtime_ns=999999999999,
        )

        view = session_related_context(
            self.connection, self.session_id, self.workspace_id
        )

        self.assertEqual(view["state"], "empty")
        self.assertEqual(view["items"], [])

    def test_unsafe_external_destination_remains_visible_but_inactive(self):
        workstream_id = self.connection.execute(
            "INSERT INTO workstreams(name) VALUES ('Unsafe Destination Work')"
        ).lastrowid
        self._link(
            "workstream_links",
            "workstream_id",
            workstream_id,
            "session",
            self.session_id,
        )
        resource_id = self.connection.execute(
            """
            INSERT INTO external_resources(resource_type, title, url)
            VALUES ('url', 'Unsafe Destination', 'javascript:alert(1)')
            """
        ).lastrowid
        self._link(
            "workstream_links",
            "workstream_id",
            workstream_id,
            "external",
            resource_id,
        )

        view = session_related_context(
            self.connection, self.session_id, self.workspace_id
        )
        item = view["items"][0]

        self.assertEqual(item["title"], "Unsafe Destination")
        self.assertIsNone(item["href"])
        self.assertEqual(item["availability"], "unavailable")
        self.assertEqual(item["availability_label"], "열 수 없음")
        self.assertEqual(view["state"], "partial")

    @contextmanager
    def _connection(self):
        yield self.connection

    @staticmethod
    def _request() -> Request:
        return Request(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": "/sessions/1",
                "raw_path": b"/sessions/1",
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
            side_effect=sqlite3.OperationalError("synthetic failure"),
        ):
            response = show_session(self._request(), self.session_id)

        html = response.body.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("관련 컨텍스트를 불러오지 못했습니다", html)
        self.assertIn("Session 대화는 계속 읽을 수 있습니다", html)
        self.assertIn("<h2>대화</h2>", html)


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

    def test_compact_dom_order_matches_identity_context_conversation(self):
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
            ".session-detail-layout.has-related-context .session-related-context { position: static; grid-column: 1; grid-row: 2; }",
            self.styles,
        )
        self.assertIn(
            ".session-detail-layout.has-related-context .timeline-section { grid-column: 1; grid-row: 3; }",
            self.styles,
        )

    def test_rail_keeps_reasons_provenance_and_owned_destinations(self):
        for marker in (
            "Related Context",
            "현재 로컬 연결 기준",
            "item.resource_label",
            "item.provenance",
            "item.detail",
            "item.reasons",
            'rel="noopener noreferrer external"',
            "최근 문서나 추측한 항목은 대신 표시하지 않습니다.",
        ):
            self.assertIn(marker, self.related_template)
        self.assertNotIn("/documents/{{ document.id }}", self.related_template)
        self.assertIn("position: sticky;", self.styles)
        self.assertIn("var(--rail-context-width)", self.styles)


if __name__ == "__main__":
    unittest.main()
