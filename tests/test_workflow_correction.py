import asyncio
import json
import sqlite3
import unittest
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

from starlette.requests import Request

from localbrain.main import app, correct_session_workflow, show_session_workflow
from localbrain.value_registry import ValueRegistryError
from localbrain.workflow_assertions import workflow_boundary_key
from localbrain.workflow_correction import (
    MAX_WORKFLOW_CORRECTION_FORM_BYTES,
    WorkflowCorrectionRequestError,
    parse_workflow_correction_form,
    reject_cross_site_workflow_correction,
)
from localbrain.workflow_focus import workflow_focus_projection
from localbrain.workflow_map import workflow_map_view


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "src/localbrain/schema.sql").read_text(encoding="utf-8")


class WorkflowCorrectionParserTests(unittest.TestCase):
    def _parse(self, values):
        return parse_workflow_correction_form(
            "application/x-www-form-urlencoded; charset=UTF-8",
            urlencode(values).encode("ascii"),
        )

    def test_exact_relation_close_reopen_and_undo_shapes(self):
        episode_a = "session:" + "a" * 64
        episode_b = "session:" + "b" * 64
        revision = "workflow-revision:" + "c" * 64
        relation = self._parse(
            {
                "action": "same-flow",
                "source_episode_key": episode_a,
                "target_episode_key": episode_b,
                "expected_active_assertion_id": "7",
                "expected_revision": revision,
            }
        )
        self.assertEqual(relation.expected_active_assertion_id, 7)
        close = self._parse(
            {
                "action": "close",
                "source_episode_key": episode_a,
                "close_reason": "completed",
                "note": "",
                "expected_revision": revision,
            }
        )
        self.assertIsNone(close.note)
        reopen = self._parse(
            {
                "action": "reopen",
                "source_episode_key": episode_a,
                "expected_active_assertion_id": "8",
                "expected_revision": revision,
            }
        )
        self.assertEqual(reopen.action, "reopen")
        undo = self._parse(
            {
                "action": "undo",
                "assertion_id": "9",
                "expected_revision": revision,
            }
        )
        self.assertEqual(undo.assertion_id, 9)

    def test_malformed_oversized_unknown_repeated_and_wrong_shape_fail_closed(self):
        revision = "workflow-revision:" + "c" * 64
        episode = "session:" + "a" * 64
        cases = (
            ("text/plain", b"action=undo"),
            ("application/x-www-form-urlencoded", b"action=%ZZ"),
            (
                "application/x-www-form-urlencoded",
                b"action=undo&action=undo&assertion_id=1&expected_revision="
                + revision.encode("ascii"),
            ),
            (
                "application/x-www-form-urlencoded",
                urlencode(
                    {
                        "action": "reopen",
                        "source_episode_key": episode,
                        "expected_revision": revision,
                    }
                ).encode("ascii"),
            ),
            (
                "application/x-www-form-urlencoded",
                urlencode(
                    {
                        "action": "undo",
                        "assertion_id": "1",
                        "expected_revision": revision,
                        "unknown": "value",
                    }
                ).encode("ascii"),
            ),
            (
                "application/x-www-form-urlencoded",
                b"x=" + b"a" * MAX_WORKFLOW_CORRECTION_FORM_BYTES,
            ),
        )
        for content_type, body in cases:
            with self.subTest(body=body[:30]), self.assertRaises(
                WorkflowCorrectionRequestError
            ):
                parse_workflow_correction_form(content_type, body)

    def test_cross_site_fetch_metadata_is_rejected(self):
        with self.assertRaises(WorkflowCorrectionRequestError) as caught:
            reject_cross_site_workflow_correction("cross-site")
        self.assertEqual(caught.exception.status_code, 400)
        reject_cross_site_workflow_correction("same-origin")
        reject_cross_site_workflow_correction(None)


class WorkflowCorrectionRouteTests(unittest.TestCase):
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
            ) VALUES (1, '/synthetic/work', 'Synthetic', '/synthetic/repo', 1)
            """
        )
        self.connection.execute(
            "INSERT INTO workstreams(id, name) VALUES (1, 'Workflow')"
        )
        self.connection.execute(
            "INSERT INTO threads(id, workstream_id, title) VALUES (1, 1, 'Flow')"
        )
        self._session(10, "Start", "2026-09-14T08:00:00Z", "main")
        self._session(11, "Current", "2026-09-14T09:00:00Z", "main")
        self._session(12, "Branch tip", "2026-09-14T10:00:00Z", "feature/map")
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

    def _session(self, session_id, title, observed_at, branch):
        self.connection.execute(
            """
            INSERT INTO sessions(
                id, source_id, workspace_id, external_id, source_path, cwd_raw,
                git_branch, title, started_at, last_event_at, event_count,
                session_class, session_role, index_policy
            ) VALUES (?, 1, 1, ?, ?, '/synthetic/work', ?, ?, ?, ?, 1,
                      'work', 'primary', 'full')
            """,
            (
                session_id,
                "native-{}".format(session_id),
                "/synthetic/session-{}.jsonl".format(session_id),
                branch,
                title,
                observed_at,
                observed_at,
            ),
        )

    @contextmanager
    def _transaction(self):
        self.connection.execute("SAVEPOINT correction_route")
        try:
            yield self.connection
        except Exception:
            self.connection.execute("ROLLBACK TO SAVEPOINT correction_route")
            self.connection.execute("RELEASE SAVEPOINT correction_route")
            raise
        else:
            self.connection.execute("RELEASE SAVEPOINT correction_route")

    def _request(self, values, *, enhanced=True, fetch_site="same-origin"):
        body = urlencode(values).encode("utf-8")
        delivered = False

        async def receive():
            nonlocal delivered
            if delivered:
                return {"type": "http.disconnect"}
            delivered = True
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }

        headers = [(b"content-type", b"application/x-www-form-urlencoded")]
        if enhanced:
            headers.append((b"x-localbrain-partial", b"workflow-correction"))
        if fetch_site:
            headers.append((b"sec-fetch-site", fetch_site.encode("ascii")))
        return Request(
            {
                "type": "http",
                "app": app,
                "method": "POST",
                "path": "/sessions/11/workflow/corrections",
                "headers": headers,
                "query_string": b"",
                "server": ("test", 80),
                "client": ("test", 1),
                "scheme": "http",
            },
            receive,
        )

    def _projection(self):
        return workflow_focus_projection(self.connection, 11)

    def _episode_key(self, projection, session_id):
        return next(
            item.episode.episode_key
            for item in projection.episodes
            if item.episode.session_id == session_id
        )

    def _post(self, values, *, enhanced=True, fetch_site="same-origin"):
        with patch("localbrain.main.transaction", self._transaction), patch(
            "localbrain.main.connect", return_value=self.connection
        ):
            return asyncio.run(
                correct_session_workflow(
                    self._request(
                        values, enhanced=enhanced, fetch_site=fetch_site
                    ),
                    11,
                )
            )

    def test_enhanced_route_maps_all_actions_and_undo_to_append_only_domain(self):
        projection = self._projection()
        keys = {
            session_id: self._episode_key(projection, session_id)
            for session_id in (10, 11, 12)
        }

        def post(action, **values):
            current = self._projection()
            request_values = {
                "action": action,
                "expected_revision": current.assertion_revision,
                **values,
            }
            response = self._post(request_values)
            self.assertEqual(response.status_code, 200)
            payload = json.loads(response.body)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(
                response.headers["vary"], "X-LocalBrain-Partial"
            )
            self.assertNotIn("note", payload)
            return payload

        close = post(
            "close",
            source_episode_key=keys[12],
            close_reason="completed",
            note="local-only note",
        )
        self.assertEqual(close["boundary"]["kind"], "lifecycle")
        active_id = self.connection.execute(
            "SELECT MAX(id) FROM workflow_assertions"
        ).fetchone()[0]
        post(
            "reopen",
            source_episode_key=keys[12],
            expected_active_assertion_id=str(active_id),
        )
        active_id = self.connection.execute(
            "SELECT MAX(id) FROM workflow_assertions"
        ).fetchone()[0]
        undone = post("undo", assertion_id=str(active_id))
        self.assertEqual(undone["code"], "workflow-undone")

        relation_values = {
            "source_episode_key": keys[11],
            "target_episode_key": keys[12],
        }
        post("same-flow", **relation_values)
        active_id = self.connection.execute(
            "SELECT MAX(id) FROM workflow_assertions"
        ).fetchone()[0]
        post(
            "split-here",
            **relation_values,
            expected_active_assertion_id=str(active_id),
        )
        active_id = self.connection.execute(
            "SELECT MAX(id) FROM workflow_assertions"
        ).fetchone()[0]
        merged = post(
            "merge-into",
            **relation_values,
            expected_active_assertion_id=str(active_id),
        )
        self.assertRegex(
            merged["boundary"]["relation_id"],
            r"^workflow-relation-[0-9a-f]{64}$",
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM workflow_assertions"
            ).fetchone()[0],
            6,
        )

    def test_stale_conflict_rolls_back_and_returns_fixed_recovery(self):
        projection = self._projection()
        source = self._episode_key(projection, 11)
        target = self._episode_key(projection, 12)
        response = self._post(
            {
                "action": "same-flow",
                "source_episode_key": source,
                "target_episode_key": target,
                "expected_revision": "workflow-revision:" + "0" * 64,
            }
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            json.loads(response.body),
            {
                "status": "error",
                "code": "conflict",
                "message": "작업 흐름이 달라졌습니다. 새로 고친 뒤 다시 확인해 주세요.",
                "reload_url": "/sessions/11/workflow",
            },
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM workflow_assertions"
            ).fetchone()[0],
            0,
        )

    def test_cross_site_and_malformed_requests_never_open_transaction(self):
        projection = self._projection()
        values = {
            "action": "close",
            "source_episode_key": self._episode_key(projection, 12),
            "close_reason": "completed",
            "expected_revision": projection.assertion_revision,
        }
        with patch(
            "localbrain.main.transaction",
            side_effect=AssertionError("transaction must not open"),
        ):
            response = asyncio.run(
                correct_session_workflow(
                    self._request(values, fetch_site="cross-site"), 11
                )
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.body)["code"], "cross-site-request")

        malformed = dict(values)
        malformed["unknown"] = "value"
        with patch(
            "localbrain.main.transaction",
            side_effect=AssertionError("transaction must not open"),
        ):
            response = asyncio.run(
                correct_session_workflow(self._request(malformed), 11)
            )
        self.assertEqual(response.status_code, 422)

    def test_no_script_success_redirect_and_fixed_get_feedback(self):
        projection = self._projection()
        response = self._post(
            {
                "action": "close",
                "source_episode_key": self._episode_key(projection, 12),
                "close_reason": "completed",
                "note": "",
                "expected_revision": projection.assertion_revision,
            },
            enhanced=False,
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "/sessions/11/workflow?workflow_result=corrected#workflow-correction-feedback",
        )
        with patch("localbrain.main.connect", return_value=self.connection):
            page = show_session_workflow(
                Request(
                    {
                        "type": "http",
                        "app": app,
                        "method": "GET",
                        "path": "/sessions/11/workflow",
                        "headers": [],
                        "query_string": b"workflow_result=corrected",
                        "server": ("test", 80),
                        "client": ("test", 1),
                        "scheme": "http",
                    }
                ),
                11,
                workflow_result="corrected",
            )
        self.assertIn(
            "작업 흐름 경계를 사용자 확인으로 반영했습니다.",
            page.body.decode("utf-8"),
        )

    def test_unexpected_failure_rolls_back_and_never_exposes_exception(self):
        projection = self._projection()
        values = {
            "action": "close",
            "source_episode_key": self._episode_key(projection, 12),
            "close_reason": "completed",
            "expected_revision": projection.assertion_revision,
        }

        def fail_after_write(connection, _projection, **_values):
            connection.execute("UPDATE sessions SET title = 'mutated' WHERE id = 12")
            raise RuntimeError("private source path and note")

        with patch("localbrain.main.transaction", self._transaction), patch(
            "localbrain.main.connect", return_value=self.connection
        ), patch(
            "localbrain.main.apply_workflow_assertion",
            side_effect=fail_after_write,
        ):
            response = asyncio.run(
                correct_session_workflow(self._request(values), 11)
            )
        self.assertEqual(response.status_code, 500)
        payload = json.loads(response.body)
        self.assertEqual(payload["code"], "correction-failed")
        self.assertNotIn("private source path", str(payload))
        self.assertEqual(
            self.connection.execute(
                "SELECT title FROM sessions WHERE id = 12"
            ).fetchone()[0],
            "Branch tip",
        )

    def test_no_script_conflict_renders_current_map_without_reflecting_input(self):
        projection = self._projection()
        response = self._post(
            {
                "action": "close",
                "source_episode_key": self._episode_key(projection, 12),
                "close_reason": "completed",
                "note": "PRIVATE-MARKER",
                "expected_revision": "workflow-revision:" + "0" * 64,
            },
            enhanced=False,
        )
        html = response.body.decode("utf-8")
        self.assertEqual(response.status_code, 409)
        self.assertIn("작업 흐름이 달라졌습니다", html)
        self.assertIn("data-workflow-map", html)
        self.assertNotIn("PRIVATE-MARKER", html)

    def test_presentation_actions_assertion_cue_and_candidate_reasons_are_exact(self):
        projection = self._projection()
        view = workflow_map_view(projection, 11)
        branch = next(item for item in view["relations"] if item["kind"] == "branches-from")
        self.assertEqual(
            [item["action"] for item in branch["correction_actions"]],
            ["same-flow", "merge-into"],
        )
        tip = next(item for item in view["episodes"] if item["session_id"] == 12)
        self.assertEqual(
            [item["action"] for item in tip["correction_actions"]], ["close"]
        )

        response = self._post(
            {
                "action": "same-flow",
                "source_episode_key": branch["source_episode_key"],
                "target_episode_key": branch["target_episode_key"],
                "expected_revision": projection.assertion_revision,
            }
        )
        self.assertEqual(response.status_code, 200)
        corrected = workflow_map_view(self._projection(), 11)
        relation = next(
            item
            for item in corrected["relations"]
            if item["source_episode_key"] == branch["source_episode_key"]
            and item["target_episode_key"] == branch["target_episode_key"]
        )
        self.assertTrue(relation["user_confirmed"])
        self.assertEqual(relation["active_assertion"]["resolution"], "applied")
        self.assertTrue(relation["base_reasons"])
        self.assertEqual(
            [item["action"] for item in relation["correction_actions"]],
            ["split-here", "merge-into", "undo"],
        )
        self.assertEqual(
            relation["correction_actions"][0]["before_meaning_label"], "이어짐"
        )
        self.assertEqual(
            relation["correction_actions"][0]["after_authority_label"],
            "사용자 확인",
        )

    def test_absent_relation_assertion_stays_on_episode_and_unknown_value_fails_closed(self):
        projection = self._projection()
        source = self._episode_key(projection, 11)
        target = self._episode_key(projection, 12)
        pair = (source, target)
        effective = tuple(
            relation
            for relation in projection.relations
            if (relation.source_episode_key, relation.target_episode_key) != pair
        )
        summary = {
            "id": 41,
            "boundary_key": workflow_boundary_key("relation", source, target),
            "boundary_version": 2,
            "boundary_kind": "relation",
            "assertion_kind": "same-flow",
            "is_undo": True,
            "source_episode_key": source,
            "target_episode_key": target,
            "before_meaning": "relation:continues",
            "after_meaning": "relation:absent",
            "before_closure_reason": None,
            "after_closure_reason": None,
            "note": None,
            "authority": "user-confirmed",
            "contract_version": "localbrain.workflow-assertion.v1",
            "supersedes_assertion_id": 40,
            "created_at": "2026-09-14T12:00:00+00:00",
            "resolution": "applied",
            "resolution_reason": None,
            "base_relation": None,
            "restored_assertion_id": None,
        }
        detached_projection = replace(
            projection,
            relations=effective,
            base_relations=projection.relations,
            assertions=(summary,),
            assertion_revision="workflow-revision:" + "d" * 64,
            assertion_overlay_version="localbrain.workflow-assertion-overlay.v1",
        )
        view = workflow_map_view(detached_projection, 11)
        owner = next(item for item in view["episodes"] if item["episode_key"] == source)
        self.assertEqual(owner["detached_relation_assertions"][0]["id"], 41)
        self.assertEqual(
            owner["detached_relation_assertions"][0]["undo_action"]["action"],
            "undo",
        )

        invalid = dict(summary)
        invalid["assertion_kind"] = "future-action"
        with self.assertRaises(ValueRegistryError):
            workflow_map_view(
                replace(detached_projection, assertions=(invalid,)), 11
            )


class WorkflowCorrectionStaticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = (ROOT / "src/localbrain/templates/session-workflow.html").read_text(
            encoding="utf-8"
        )
        cls.partial = (ROOT / "src/localbrain/templates/_workflow_correction.html").read_text(
            encoding="utf-8"
        )
        cls.script = (ROOT / "src/localbrain/static/workflow-map.js").read_text(
            encoding="utf-8"
        )

    def test_trace_and_no_script_fallback_share_preview_forms(self):
        for marker in (
            "correction_action(action, workflow",
            "현재 사용자 확인",
            "원래 후보 근거",
            "detached_relation_assertions",
            "data-workflow-correction-feedback",
        ):
            self.assertIn(marker, self.template)
        for marker in (
            'method="post"',
            "data-workflow-correction-form",
            "expected_revision",
            "before_meaning_label",
            "after_meaning_label",
            'maxlength="1000"',
            "data-workflow-correction-cancel",
        ):
            self.assertIn(marker, self.partial)

    def test_controller_uses_one_shot_bounded_restore_and_in_place_failure(self):
        for marker in (
            "sanitizeWorkflowRestorationSnapshot",
            "consumeWorkflowRestorationSnapshot",
            "storeWorkflowRestorationSnapshot",
            "window.sessionStorage",
            "const restorationSnapshot = correctionSnapshot();",
            "window.location.reload()",
            'headers: { "X-LocalBrain-Partial": "workflow-correction" }',
            "fieldset.disabled = true",
            "fieldset.disabled = false",
            "showCorrectionFailure",
            "openDisclosureKeys",
            "traceScrollTop",
            "outerScrollY",
        ):
            self.assertIn(marker, self.script)
        self.assertLess(
            self.script.index("const restorationSnapshot = correctionSnapshot();"),
            self.script.index("fieldset.disabled = true"),
        )
