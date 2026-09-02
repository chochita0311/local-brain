import json
import sqlite3
import tempfile
import unittest
import asyncio
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

from starlette.requests import Request
from localbrain.atlassian import (
    create_or_reuse_atlassian_stub,
    register_atlassian_space,
    set_atlassian_item_axes,
)
from localbrain.atlassian_refresh import (
    AtlassianRefreshError,
    apply_atlassian_refresh_result,
    prepare_atlassian_refresh_run,
    refresh_preview,
)
from localbrain.external_access import (
    record_capability_observation,
    register_source_instance,
)
from localbrain.external_sync import RESULT_SCHEMA_VERSION
from localbrain.external_sync import MODEL_RESULT_SCHEMA_VERSION
from localbrain.main import (
    app,
    atlassian_refresh_page,
    atlassian_start_refresh,
)
from localbrain.runner import _execute_run


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class _FakeStream:
    def __init__(self, lines):
        self.lines = [
            line if isinstance(line, bytes) else line.encode("utf-8")
            for line in lines
        ]

    async def readline(self):
        return self.lines.pop(0) if self.lines else b""


class _FakeStdin:
    def write(self, _value):
        return None

    async def drain(self):
        return None

    def close(self):
        return None


class _FakeProcess:
    def __init__(self, lines):
        self.pid = 43210
        self.stdin = _FakeStdin()
        self.stdout = _FakeStream(lines)
        self.stderr = _FakeStream([])
        self.returncode = None

    async def wait(self):
        self.returncode = 0
        return 0


class AtlassianRefreshTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.run_root = Path(tempfile.mkdtemp())
        self.jira_source = self._source(
            "refresh-jira",
            "jira",
            ("jira.search_metadata", "jira.read_description"),
        )
        self.wiki_source = self._source(
            "refresh-wiki",
            "confluence",
            ("confluence.search_pages", "confluence.read_page"),
        )
        self.jira_item = self._item(
            self.jira_source,
            "https://jira.refresh.test/browse/REF-1",
            "Jira refresh item",
            "indexed",
        )
        self.wiki_item = self._item(
            self.wiki_source,
            "https://wiki.refresh.test/spaces/TEAM/pages/901/Refresh",
            "Wiki refresh item",
            "metadata",
        )

    def tearDown(self):
        self.connection.close()
        for path in sorted(self.run_root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            else:
                path.rmdir()
        self.run_root.rmdir()

    def _source(self, key, service, operations):
        source = register_source_instance(
            self.connection,
            instance_key=key,
            provider_kind="mcp_gateway",
            service=service,
            display_name=key,
            config_ref=service,
        )
        record_capability_observation(
            self.connection,
            source["id"],
            availability="available",
            operations=operations,
            schema_fingerprint=("a" if service == "jira" else "b") * 64,
        )
        return source

    def _item(self, source, url, title, coverage):
        item = create_or_reuse_atlassian_stub(
            self.connection,
            source_instance_id=source["id"],
            url=url,
            title=title,
        )
        set_atlassian_item_axes(
            self.connection,
            item["external_resource_id"],
            coverage=coverage,
        )
        return item

    def _target_result(
        self,
        target,
        *,
        outcome="resolved",
        metadata=None,
        content=None,
        identity=None,
        error=None,
    ):
        requests = []
        for request in target["requests"]:
            request_content = (
                content
                if request["logical_operation"]
                in {"jira.read_description", "confluence.read_page"}
                else None
            )
            requests.append(
                {
                    "request_id": request["request_id"],
                    "logical_operation": request["logical_operation"],
                    "outcome": outcome,
                    "identity": identity or {},
                    "metadata": metadata or {},
                    "content": request_content,
                    "remote_version": "2",
                    "remote_updated_at": "2026-07-23T00:00:00Z",
                    "content_hash": None,
                    "error": error,
                }
            )
        return {
            "target_id": target["target_id"],
            "locator": target["locator"],
            "outcome": outcome,
            "requests": requests,
        }

    @contextmanager
    def _transaction(self):
        self.connection.execute("SAVEPOINT refresh_web_test")
        try:
            yield self.connection
        except Exception:
            self.connection.execute("ROLLBACK TO refresh_web_test")
            self.connection.execute("RELEASE refresh_web_test")
            raise
        else:
            self.connection.execute("RELEASE refresh_web_test")

    def _request(self, method="GET", body=""):
        delivered = False

        async def receive():
            nonlocal delivered
            if delivered:
                return {"type": "http.disconnect"}
            delivered = True
            return {
                "type": "http.request",
                "body": body.encode("utf-8"),
                "more_body": False,
            }

        return Request(
            {
                "type": "http",
                "app": app,
                "method": method,
                "path": "/atlassian/refresh",
                "headers": (
                    [
                        (
                            b"content-type",
                            b"application/x-www-form-urlencoded",
                        )
                    ]
                    if method == "POST"
                    else []
                ),
                "query_string": b"",
                "server": ("test", 80),
                "client": ("test", 1),
                "scheme": "http",
            },
            receive,
        )

    def test_scope_preview_deduplicates_workstream_and_uses_freshness_defaults(self):
        workstream_id = self.connection.execute(
            "INSERT INTO workstreams(name) VALUES ('Refresh scope')"
        ).lastrowid
        thread_id = self.connection.execute(
            """
            INSERT INTO threads(workstream_id, title)
            VALUES (?, 'Mapped thread')
            """,
            (workstream_id,),
        ).lastrowid
        self.connection.execute(
            """
            INSERT INTO workstream_links(
                workstream_id, entity_type, entity_id, relation_type
            ) VALUES (?, 'external', ?, 'reference')
            """,
            (workstream_id, str(self.jira_item["external_resource_id"])),
        )
        for item_id in (
            self.jira_item["external_resource_id"],
            self.wiki_item["external_resource_id"],
        ):
            self.connection.execute(
                """
                INSERT INTO thread_links(
                    thread_id, entity_type, entity_id, relation_type
                ) VALUES (?, 'external', ?, 'reference')
                """,
                (thread_id, str(item_id)),
            )

        workstream = refresh_preview(
            self.connection,
            scope_kind="workstream",
            scope_id=workstream_id,
        )
        thread = refresh_preview(
            self.connection,
            scope_kind="thread",
            scope_id=thread_id,
        )

        self.assertEqual(
            [item["id"] for item in workstream["items"]],
            [
                self.jira_item["external_resource_id"],
                self.wiki_item["external_resource_id"],
            ],
        )
        self.assertEqual(workstream["selected_count"], 2)
        self.assertEqual(workstream["selected_calls"], 3)
        self.assertEqual(thread["target_count"], 2)
        self.assertTrue(all(item["freshness"] == "unknown" for item in thread["items"]))

    def test_refresh_projects_url_containers_and_persisted_space_precedence(self):
        initial = refresh_preview(
            self.connection,
            scope_kind="all_known",
            scope_id=None,
        )
        by_id = {item["id"]: item for item in initial["items"]}
        self.assertEqual(
            (
                by_id[self.jira_item["external_resource_id"]]["container_kind"],
                by_id[self.jira_item["external_resource_id"]]["container_label"],
                by_id[self.jira_item["external_resource_id"]]["container_service"],
                by_id[self.jira_item["external_resource_id"]]["container_cue"],
            ),
            ("url", "REF", "jira", "Jira · URL 기준"),
        )
        self.assertEqual(
            (
                by_id[self.wiki_item["external_resource_id"]]["container_kind"],
                by_id[self.wiki_item["external_resource_id"]]["container_label"],
                by_id[self.wiki_item["external_resource_id"]]["container_service"],
                by_id[self.wiki_item["external_resource_id"]]["container_cue"],
            ),
            ("url", "TEAM", "confluence", "Wiki · URL 기준"),
        )

        space = register_atlassian_space(
            self.connection,
            site_id=self.wiki_item["site_id"],
            source_instance_id=self.wiki_source["id"],
            service="confluence",
            name="Persisted Wiki Space",
            space_key="TEAM",
            canonical_url="https://wiki.refresh.test/spaces/TEAM",
        )
        self.connection.execute(
            "UPDATE atlassian_items SET space_id = ? WHERE external_resource_id = ?",
            (space["id"], self.wiki_item["external_resource_id"]),
        )

        projected = refresh_preview(
            self.connection,
            scope_kind="item",
            scope_id=self.wiki_item["external_resource_id"],
        )["items"][0]
        self.assertEqual(
            (
                projected["container_kind"],
                projected["container_label"],
                projected["container_structural_scope"],
                projected["space_name"],
            ),
            ("space", "Persisted Wiki Space", None, "Persisted Wiki Space"),
        )

    def test_mixed_source_selection_prepares_one_run_and_keeps_single_source_compatibility(self):
        item_ids = [
            self.jira_item["external_resource_id"],
            self.wiki_item["external_resource_id"],
        ]
        run_id = prepare_atlassian_refresh_run(
            self.connection,
            scope_kind="all_known",
            scope_id=None,
            selected_item_ids=item_ids,
            runner="codex",
            run_root=self.run_root,
        )
        row = self.connection.execute(
            "SELECT * FROM external_sync_runs WHERE maintenance_run_id = ?",
            (run_id,),
        ).fetchone()
        manifest = json.loads(
            self.connection.execute(
                "SELECT source_snapshot_json FROM maintenance_runs WHERE id = ?",
                (run_id,),
            ).fetchone()[0]
        )

        self.assertIsNone(row["source_instance_id"])
        self.assertEqual(row["service"], "mixed")
        self.assertEqual(row["selected_target_count"], 2)
        self.assertEqual(
            {target["source_instance_id"] for target in manifest["targets"]},
            {self.jira_source["id"], self.wiki_source["id"]},
        )
        self.assertEqual(manifest["call_budget"], 20)

        single_id = prepare_atlassian_refresh_run(
            self.connection,
            scope_kind="item",
            scope_id=self.jira_item["external_resource_id"],
            selected_item_ids=[self.jira_item["external_resource_id"]],
            run_root=self.run_root,
        )
        single = json.loads(
            self.connection.execute(
                "SELECT source_snapshot_json FROM maintenance_runs WHERE id = ?",
                (single_id,),
            ).fetchone()[0]
        )
        self.assertEqual(
            single["source"]["instance_id"], self.jira_source["id"]
        )
        self.assertNotIn("source_instance_id", single["targets"][0])

    def test_default_selection_and_twenty_read_batch_are_enforced_locally(self):
        current = self._item(
            self.jira_source,
            "https://jira.refresh.test/browse/REF-20",
            "Current item",
            "indexed",
        )
        due = self._item(
            self.jira_source,
            "https://jira.refresh.test/browse/REF-21",
            "Due item",
            "indexed",
        )
        unavailable = self._item(
            self.jira_source,
            "https://jira.refresh.test/browse/REF-22",
            "Unavailable item",
            "metadata",
        )
        for item, checked_at, outcome in (
            (current, "2099-01-01T00:00:00Z", "unchanged"),
            (due, "2020-01-01T00:00:00Z", "unchanged"),
            (unavailable, "2026-07-23T00:00:00Z", "unavailable"),
        ):
            self.connection.execute(
                """
                INSERT INTO atlassian_item_remote_state(
                    external_resource_id, last_attempted_at,
                    last_successful_at, last_outcome, last_error_code
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item["external_resource_id"],
                    checked_at,
                    checked_at if outcome == "unchanged" else None,
                    outcome,
                    None if outcome == "unchanged" else "unavailable",
                ),
            )

        preview = refresh_preview(
            self.connection,
            scope_kind="all_known",
            scope_id=None,
        )
        selection = {
            item["title"]: item["selected"] for item in preview["items"]
        }
        self.assertFalse(selection["Current item"])
        self.assertTrue(selection["Due item"])
        self.assertTrue(selection["Unavailable item"])

        selected_ids = [self.jira_item["external_resource_id"]]
        for suffix in range(30, 40):
            item = self._item(
                self.jira_source,
                "https://jira.refresh.test/browse/REF-{}".format(suffix),
                "Budget item {}".format(suffix),
                "indexed",
            )
            selected_ids.append(item["external_resource_id"])
        with self.assertRaisesRegex(
            AtlassianRefreshError, "20-call refresh batch"
        ):
            prepare_atlassian_refresh_run(
                self.connection,
                scope_kind="all_known",
                scope_id=None,
                selected_item_ids=selected_ids,
                run_root=self.run_root,
            )

    def test_reference_application_strips_remote_metadata_and_binds_identity(self):
        reference = self._item(
            self.jira_source,
            "https://jira.refresh.test/browse/REF-2",
            "Reference only",
            "reference",
        )
        run_id = prepare_atlassian_refresh_run(
            self.connection,
            scope_kind="item",
            scope_id=reference["external_resource_id"],
            selected_item_ids=[reference["external_resource_id"]],
            run_root=self.run_root,
        )
        manifest = json.loads(
            self.connection.execute(
                "SELECT source_snapshot_json FROM maintenance_runs WHERE id = ?",
                (run_id,),
            ).fetchone()[0]
        )
        target = manifest["targets"][0]
        result = {
            "schema": RESULT_SCHEMA_VERSION,
            "run_id": run_id,
            "source": manifest["source"],
            "scope": manifest["scope"],
            "read_policy_version": manifest["read_policy_version"],
            "status": "completed",
            "targets": [
                self._target_result(
                    target,
                    metadata={"key": "REF-2"},
                    identity={
                        "remote_id": "2002",
                        "remote_key": "REF-2",
                    },
                )
            ],
            "summary": "Synthetic reference check",
        }

        applied = apply_atlassian_refresh_result(
            self.connection,
            manifest=manifest,
            result=result,
            checked_at="2026-07-23T01:00:00Z",
        )
        state = self.connection.execute(
            """
            SELECT atlassian_items.remote_id,
                   atlassian_item_remote_state.metadata_json,
                   atlassian_item_remote_state.last_outcome
            FROM atlassian_items
            JOIN atlassian_item_remote_state
              ON atlassian_item_remote_state.external_resource_id =
                 atlassian_items.external_resource_id
            WHERE atlassian_items.external_resource_id = ?
            """,
            (reference["external_resource_id"],),
        ).fetchone()

        self.assertEqual(applied["applied_items"], 1)
        self.assertEqual(state["remote_id"], "2002")
        self.assertEqual(json.loads(state["metadata_json"]), {})
        self.assertEqual(state["last_outcome"], "resolved")

    def test_invalid_target_mapping_rolls_back_before_item_mutation(self):
        run_id = prepare_atlassian_refresh_run(
            self.connection,
            scope_kind="all_known",
            scope_id=None,
            selected_item_ids=[
                self.jira_item["external_resource_id"],
                self.wiki_item["external_resource_id"],
            ],
            run_root=self.run_root,
        )
        manifest = json.loads(
            self.connection.execute(
                "SELECT source_snapshot_json FROM maintenance_runs WHERE id = ?",
                (run_id,),
            ).fetchone()[0]
        )
        targets = [
            self._target_result(
                manifest["targets"][0],
                identity={"remote_id": "3001", "remote_key": "REF-1"},
                metadata={"key": "REF-1"},
                content={"type": "doc", "content": []},
            ),
            self._target_result(
                manifest["targets"][1],
                identity={"remote_id": "901"},
                metadata={"title": "Wiki"},
            ),
        ]
        targets[1]["locator"] = {
            "kind": "url",
            "value": "https://wiki.refresh.test/wrong",
        }
        result = {
            "schema": RESULT_SCHEMA_VERSION,
            "run_id": run_id,
            "targets": targets,
        }

        with self.assertRaisesRegex(
            AtlassianRefreshError, "locator changed"
        ):
            apply_atlassian_refresh_result(
                self.connection,
                manifest=manifest,
                result=result,
            )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_remote_state"
            ).fetchone()[0],
            0,
        )

    def test_runner_completion_applies_validated_refresh_result_atomically(self):
        run_id = prepare_atlassian_refresh_run(
            self.connection,
            scope_kind="item",
            scope_id=self.jira_item["external_resource_id"],
            selected_item_ids=[self.jira_item["external_resource_id"]],
            run_root=self.run_root,
        )
        model_result = {
            "schema": MODEL_RESULT_SCHEMA_VERSION,
            "run_id": run_id,
            "summary": "Synthetic refresh completed",
        }

        async def executor(dispatch):
            if dispatch.logical_operation == "jira.search_metadata":
                return {
                    "outcome": "changed",
                    "identity": {
                        "remote_id": "4001",
                        "remote_key": "REF-1",
                    },
                    "metadata": {
                        "key": "REF-1",
                        "summary": "Confirmed synthetic summary",
                    },
                    "remote_version": "4",
                    "remote_updated_at": "2026-07-23T03:00:00Z",
                }
            return {
                "outcome": "changed",
                "identity": {
                    "remote_id": "4001",
                    "remote_key": "REF-1",
                },
                "content": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Synthetic Jira description",
                                }
                            ],
                        }
                    ],
                },
                "remote_version": "4",
                "remote_updated_at": "2026-07-23T03:00:00Z",
            }

        async def create_process(*_arguments, **_kwargs):
            return _FakeProcess(
                [
                    json.dumps(
                        {
                            "type": "result",
                            "structured_output": model_result,
                        }
                    )
                    + "\n"
                ]
            )

        with patch(
            "localbrain.runner.connect", return_value=self.connection
        ), patch(
            "localbrain.runner.transaction",
            side_effect=lambda: self._transaction(),
        ), patch(
            "localbrain.runner.runner_executable",
            return_value="/synthetic/claude",
        ), patch(
            "localbrain.runner.asyncio.create_subprocess_exec",
            side_effect=create_process,
        ), patch(
            "localbrain.runner._sync_native_runner_sessions",
            return_value=True,
        ):
            asyncio.run(_execute_run(run_id, executor))

        run = self.connection.execute(
            "SELECT * FROM maintenance_runs WHERE id = ?", (run_id,)
        ).fetchone()
        item = self.connection.execute(
            """
            SELECT atlassian_items.remote_id,
                   atlassian_item_remote_state.last_outcome,
                   atlassian_item_content.normalized_text
            FROM atlassian_items
            JOIN atlassian_item_remote_state
              ON atlassian_item_remote_state.external_resource_id =
                 atlassian_items.external_resource_id
            JOIN atlassian_item_content
              ON atlassian_item_content.external_resource_id =
                 atlassian_items.external_resource_id
            WHERE atlassian_items.external_resource_id = ?
            """,
            (self.jira_item["external_resource_id"],),
        ).fetchone()

        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["mcp_calls_used"], 2)
        self.assertEqual(item["remote_id"], "4001")
        self.assertEqual(item["last_outcome"], "changed")
        self.assertEqual(
            item["normalized_text"], "Synthetic Jira description"
        )

    def test_confluence_space_catalog_is_one_explicit_page_and_creates_stale_indexed_stubs(self):
        site_id = self.wiki_item["site_id"]
        space = register_atlassian_space(
            self.connection,
            site_id=site_id,
            name="Team space",
            space_key="TEAM",
            canonical_url="https://wiki.refresh.test/spaces/TEAM/overview",
        )
        self.connection.execute(
            """
            UPDATE atlassian_items SET space_id = ?
            WHERE external_resource_id = ?
            """,
            (space["id"], self.wiki_item["external_resource_id"]),
        )
        preview = refresh_preview(
            self.connection,
            scope_kind="space",
            scope_id=space["id"],
            page=2,
        )
        self.assertEqual(preview["catalog"]["limit"], 200)
        self.assertTrue(preview["catalog"]["selected"])

        run_id = prepare_atlassian_refresh_run(
            self.connection,
            scope_kind="space",
            scope_id=space["id"],
            selected_item_ids=[],
            include_catalog=True,
            page=2,
            run_root=self.run_root,
        )
        manifest = json.loads(
            self.connection.execute(
                "SELECT source_snapshot_json FROM maintenance_runs WHERE id = ?",
                (run_id,),
            ).fetchone()[0]
        )
        target = manifest["targets"][0]
        self.assertEqual(target["requests"][0]["arguments"]["offset"], 200)
        result = {
            "schema": RESULT_SCHEMA_VERSION,
            "run_id": run_id,
            "targets": [
                self._target_result(
                    target,
                    outcome="changed",
                    metadata={
                        "pages": [
                            {
                                "id": "902",
                                "title": "New synthetic page",
                            }
                        ]
                    },
                )
            ],
        }
        applied = apply_atlassian_refresh_result(
            self.connection,
            manifest=manifest,
            result=result,
            checked_at="2026-07-23T02:00:00Z",
        )
        row = self.connection.execute(
            """
            SELECT atlassian_items.coverage,
                   atlassian_items.space_id,
                   atlassian_item_remote_state.projection_stale
            FROM atlassian_items
            JOIN atlassian_item_remote_state
              ON atlassian_item_remote_state.external_resource_id =
                 atlassian_items.external_resource_id
            WHERE atlassian_items.remote_id = '902'
            """
        ).fetchone()

        self.assertEqual(applied["cataloged_items"], 1)
        self.assertEqual(row["coverage"], "indexed")
        self.assertEqual(row["space_id"], space["id"])
        self.assertEqual(row["projection_stale"], 1)

    def test_no_script_preview_is_local_and_unavailable_start_preserves_selection(self):
        prior_executor = app.state.external_read_executor
        app.state.external_read_executor = None
        return_to = "/atlassian?view=jira&item={}".format(
            self.jira_item["external_resource_id"]
        )
        try:
            with patch(
                "localbrain.main.connect", return_value=self.connection
            ):
                preview_response = atlassian_refresh_page(
                    self._request(),
                    scope="all_known",
                    scope_id=None,
                    page=1,
                    retry=None,
                    run_id=None,
                    return_to=return_to,
                )
                failed_response = asyncio.run(
                    atlassian_start_refresh(
                        self._request(
                            "POST",
                            urlencode(
                                {
                                    "scope": "all_known",
                                    "item_id": self.jira_item[
                                        "external_resource_id"
                                    ],
                                    "runner": "claude",
                                    "return_to": return_to,
                                }
                            ),
                        )
                    )
                )
        finally:
            app.state.external_read_executor = prior_executor

        self.assertEqual(preview_response.status_code, 200)
        preview_body = preview_response.body.decode("utf-8")
        self.assertIn("LOCAL PREVIEW", preview_body)
        self.assertIn("알려진 모든 Atlassian 링크/문서", preview_body)
        self.assertIn(
            'href="/atlassian?view=jira&amp;item={}"'.format(
                self.jira_item["external_resource_id"]
            ),
            preview_body,
        )
        self.assertIn(
            'name="return_to" value="/atlassian?view=jira&amp;item={}"'.format(
                self.jira_item["external_resource_id"]
            ),
            preview_body,
        )
        self.assertEqual(failed_response.status_code, 422)
        failed_body = failed_response.body.decode("utf-8")
        self.assertIn("host-side read executor", failed_body)
        self.assertIn(
            'value="{}"'.format(self.jira_item["external_resource_id"]),
            failed_body,
        )
        self.assertIn(
            'name="return_to" value="/atlassian?view=jira&amp;item={}"'.format(
                self.jira_item["external_resource_id"]
            ),
            failed_body,
        )
