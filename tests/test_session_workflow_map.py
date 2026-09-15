import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

from starlette.requests import Request

from localbrain.main import app, show_session, show_session_workflow
from localbrain.workflow_focus import (
    workflow_focus_projection,
    workflow_session_is_eligible,
)
from localbrain.workflow_map import workflow_map_view


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "src/localbrain/schema.sql").read_text(encoding="utf-8")


class SessionWorkflowMapTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA)
        self.connection.execute(
            """
            INSERT INTO sources(id, kind, provider_kind, name, root_path)
            VALUES (1, 'codex', 'codex', 'Codex', '/synthetic/codex')
            """
        )
        self.connection.execute(
            """
            INSERT INTO workspaces(
                id, canonical_path, display_name, git_root, exists_now
            ) VALUES (1, '/synthetic/work', 'Synthetic Work', '/synthetic/repo', 1)
            """
        )
        self.connection.execute(
            "INSERT INTO workstreams(id, name) VALUES (1, 'Workflow Map')"
        )
        self.connection.execute(
            "INSERT INTO threads(id, workstream_id, title) VALUES (1, 1, 'Focus')"
        )
        self._session(10, "First intent", "2026-09-14T08:00:00Z", "main")
        self._session(11, "Current implementation", "2026-09-14T09:00:00Z", "main")
        self._session(12, "Alternative branch", "2026-09-14T10:00:00Z", "feature/map")
        for session_id in (10, 11, 12):
            self.connection.execute(
                """
                INSERT INTO thread_links(thread_id, entity_type, entity_id, linked_by)
                VALUES (1, 'session', ?, 'user')
                """,
                (str(session_id),),
            )

    def tearDown(self):
        self.connection.close()

    def _session(
        self,
        session_id,
        title,
        observed_at,
        branch,
        *,
        event_count=1,
        session_role="primary",
        parent_session_id=None,
        index_policy="full",
    ):
        self.connection.execute(
            """
            INSERT INTO sessions(
                id, source_id, workspace_id, external_id, source_path, cwd_raw,
                git_branch, title, started_at, last_event_at, event_count,
                session_class, session_role, parent_session_id, index_policy
            ) VALUES (?, 1, 1, ?, ?, '/synthetic/work', ?, ?, ?, ?, ?,
                      'work', ?, ?, ?)
            """,
            (
                session_id,
                "native-{}".format(session_id),
                "/synthetic/session-{}.jsonl".format(session_id),
                branch,
                title,
                observed_at,
                observed_at,
                event_count,
                session_role,
                parent_session_id,
                index_policy,
            ),
        )

    @staticmethod
    def _request(path):
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

    def test_eligibility_matches_activity_contract_without_mutation(self):
        self.assertTrue(workflow_session_is_eligible(self.connection, 11))
        self._session(20, "Metadata only", "2026-09-14T11:00:00Z", "main", event_count=0)
        self.assertFalse(workflow_session_is_eligible(self.connection, 20))
        self.connection.execute(
            """
            INSERT INTO activity_events(
                id, session_id, sequence, occurred_at, event_type, source_line
            ) VALUES ('activity-20', 20, 1, '2026-09-14T11:00:00Z', 'message', 1)
            """
        )
        before = self.connection.total_changes
        self.assertTrue(workflow_session_is_eligible(self.connection, 20))
        self.assertEqual(self.connection.total_changes, before)
        self.assertFalse(workflow_session_is_eligible(self.connection, 999))

    def test_presentation_adapter_retains_episode_relation_and_evidence_contract(self):
        projection = workflow_focus_projection(self.connection, 11)
        view = workflow_map_view(projection, 11)

        self.assertEqual(view["status"], "ready")
        self.assertEqual(view["selected_episode"]["session_id"], 11)
        self.assertEqual(len(view["episodes"]), 3)
        self.assertEqual(
            [relation["label"] for relation in view["relations"]],
            ["continues", "branches from"],
        )
        self.assertTrue(
            all(relation["reasons"] for relation in view["relations"])
        )
        self.assertTrue(
            all(
                relation["authority_label"] == "규칙 기반 후보"
                for relation in view["relations"]
            )
        )
        self.assertEqual(
            view["client_projection"]["selected_episode_key"],
            view["selected_episode"]["episode_key"],
        )
        self.assertNotIn("/synthetic/repo", str(view["client_projection"]))
        self.assertNotIn("native-11", str(view["client_projection"]))

    def test_ready_route_calls_one_projection_and_executes_zero_writes(self):
        statements = []
        self.connection.set_trace_callback(statements.append)
        before = self.connection.total_changes
        projection = workflow_focus_projection(self.connection, 11)
        statements.clear()

        with patch("localbrain.main.connect", return_value=self.connection), patch(
            "localbrain.main.workflow_focus_projection", return_value=projection
        ) as producer, patch(
            "localbrain.main.session_detail",
            side_effect=AssertionError("Workflow route must not query a fallback detail"),
        ):
            response = show_session_workflow(
                self._request("/sessions/11/workflow"), 11
            )

        producer.assert_called_once_with(self.connection, 11)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.connection.total_changes, before)
        self.assertFalse(
            any(
                statement.lstrip().upper().startswith(
                    ("INSERT", "UPDATE", "DELETE", "REPLACE")
                )
                for statement in statements
            )
        )
        html = response.body.decode("utf-8")
        for marker in (
            "SOURCE-BACKED WORKFLOW FOCUS",
            'data-workflow-map',
            'data-workflow-episode',
            'data-workflow-relation-trace',
            'data-workflow-fallback',
            'data-workflow-zoom-fit',
            "continues",
            "branches from",
            "규칙 기반 후보",
            "같은 Thread",
            "Session 대화 열기",
            "workflow-map.js",
        ):
            self.assertIn(marker, html)
        self.assertNotIn("/synthetic/session-", html)
        self.assertNotIn("native-", html)

    def test_unconnected_route_is_success_and_does_not_claim_completion(self):
        self.connection.execute("DELETE FROM thread_links")
        response = None
        with patch("localbrain.main.connect", return_value=self.connection):
            response = show_session_workflow(
                self._request("/sessions/11/workflow"), 11
            )
        html = response.body.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("연결 근거를 찾지 못했습니다", html)
        self.assertIn("완료된 업무라는 뜻은 아닙니다", html)
        self.assertIn("Current implementation", html)

    def test_typed_route_states_keep_bounded_local_destinations(self):
        self._session(
            20,
            "Ineligible child",
            "2026-09-14T11:00:00Z",
            "main",
            session_role="subsession",
            parent_session_id=10,
        )
        with patch("localbrain.main.connect", return_value=self.connection):
            missing = show_session_workflow(
                self._request("/sessions/999/workflow"), 999
            )
            ineligible = show_session_workflow(
                self._request("/sessions/20/workflow"), 20
            )
        self.assertEqual(missing.status_code, 404)
        self.assertIn('href="/sessions"', missing.body.decode("utf-8"))
        self.assertEqual(ineligible.status_code, 422)
        self.assertIn(
            'href="/sessions/20"', ineligible.body.decode("utf-8")
        )

        with patch(
            "localbrain.main.connect", return_value=self.connection
        ), patch(
            "localbrain.main.workflow_focus_projection",
            side_effect=RuntimeError("private failure payload"),
        ):
            failed = show_session_workflow(
                self._request("/sessions/11/workflow"), 11
            )
        failed_html = failed.body.decode("utf-8")
        self.assertEqual(failed.status_code, 500)
        self.assertIn("Session 원문은 그대로", failed_html)
        self.assertIn('href="/sessions/11"', failed_html)
        self.assertNotIn("private failure payload", failed_html)

    def test_session_detail_action_is_additive_and_failure_is_isolated(self):
        with patch("localbrain.main.connect", return_value=self.connection):
            response = show_session(self._request("/sessions/11"), 11)
        html = response.body.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn('href="/sessions/11/workflow"', html)
        self.assertIn("작업 흐름", html)
        self.assertIn("<h2>대화</h2>", html)
        self.assertIn("session-pin", html)

        with patch("localbrain.main.connect", return_value=self.connection), patch(
            "localbrain.main.workflow_session_is_eligible",
            side_effect=RuntimeError("synthetic predicate failure"),
        ):
            isolated = show_session(self._request("/sessions/11"), 11)
        isolated_html = isolated.body.decode("utf-8")
        self.assertEqual(isolated.status_code, 200)
        self.assertNotIn('href="/sessions/11/workflow"', isolated_html)
        self.assertIn("<h2>대화</h2>", isolated_html)


class SessionWorkflowMapStaticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = (ROOT / "src/localbrain/templates/session-workflow.html").read_text(
            encoding="utf-8"
        )
        cls.session = (ROOT / "src/localbrain/templates/session.html").read_text(
            encoding="utf-8"
        )
        cls.script = (ROOT / "src/localbrain/static/workflow-map.js").read_text(
            encoding="utf-8"
        )
        cls.styles = (ROOT / "src/localbrain/static/styles.css").read_text(
            encoding="utf-8"
        )

    def test_semantic_fallback_and_trace_exist_before_enhancement(self):
        for marker in (
            "data-workflow-fallback open",
            "workflow-lineage-episodes",
            "workflow-lineage-relations",
            "data-workflow-episode-trace",
            "data-workflow-relation-trace",
            "reason.identity",
            "evidence.admission_labels",
            "evidence.availability_label",
            'data-workflow-render-state="fallback"',
            'aria-busy="false"',
            "<noscript>",
        ):
            self.assertIn(marker, self.template)

    def test_controller_owns_fixed_layout_history_and_scroll_boundaries(self):
        for marker in (
            "buildWorkflowLayout",
            "workflowPath",
            "window.history.pushState",
            'window.addEventListener("popstate"',
            'window.addEventListener("resize"',
            "if (!workflowWheelOwnsZoom(event) || isNarrow()) return;",
            "event.preventDefault()",
            '{ passive: false }',
            "data-workflow-branch-toggle",
            "expandedBranches",
            "branchOwner",
            "data-workflow-relation",
            "failWorkflowMap",
            "window.matchMedia(\"(max-width: 920px)\")",
            "window.matchMedia(\"(max-width: 700px)\")",
        ):
            self.assertIn(marker, self.script)
        self.assertNotIn("Math.random", self.script)
        self.assertNotIn("forceSimulation", self.script)

    def test_map_uses_existing_semantic_system_and_approved_breakpoints(self):
        for marker in (
            "--workflow-node-width",
            "--workflow-trace-width: var(--rail-context-width);",
            ".workflow-layout",
            ".workflow-episode-card.is-selected",
            ".workflow-relation-edge.is-dimmed",
            ".workflow-map-viewport",
            "overscroll-behavior: contain;",
            "@media (max-width: 920px)",
            "@media (max-width: 700px)",
            "@media (prefers-reduced-motion: reduce)",
        ):
            self.assertIn(marker, self.styles)
        self.assertIn("workflow_available", self.session)
