import asyncio
import json
import sqlite3
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from starlette.requests import Request

from localbrain.atlassian import (
    apply_atlassian_target_result,
    create_or_reuse_atlassian_stub,
)
from localbrain.atlassian_browse import (
    atlassian_item_detail,
    atlassian_search_results,
    browse_inventory,
    update_atlassian_local_state,
)
from localbrain.main import (
    app,
    atlassian_item_page,
    atlassian_page,
    atlassian_update_local,
)
from localbrain.queries import search
from localbrain.workstreams import add_link


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


def target_result(
    *,
    remote_id,
    remote_key,
    metadata=None,
    content=None,
    outcome="changed",
):
    return {
        "target_id": "synthetic-target",
        "locator": {
            "kind": "url",
            "value": "https://synthetic.invalid",
        },
        "outcome": outcome,
        "requests": [
            {
                "request_id": "synthetic-request",
                "logical_operation": "jira.read_description",
                "outcome": outcome,
                "identity": {
                    "remote_id": remote_id,
                    "remote_key": remote_key,
                },
                "metadata": metadata or {},
                "content": content,
                "remote_version": "2",
                "remote_updated_at": "2026-07-23T00:00:00Z",
                "content_hash": None,
                "error": None,
            }
        ],
    }


class AtlassianBrowseTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.jira_source = self._source(
            "jira-primary", "jira", "Primary Jira"
        )
        self.jira_other = self._source(
            "jira-secondary", "jira", "Secondary Jira"
        )
        self.reference = self._item(
            self.jira_source,
            "https://jira.primary.test/browse/SAME-1",
            "Primary local title",
            "reference",
        )
        self.metadata = self._item(
            self.jira_other,
            "https://jira.secondary.test/browse/SAME-1",
            "Secondary local title",
            "metadata",
        )
        apply_atlassian_target_result(
            self.connection,
            self.metadata["external_resource_id"],
            target_result(
                remote_id="secondary-1",
                remote_key="SAME-1",
                metadata={
                    "summary": "Secondary confirmed metadata",
                    "status": "Open",
                },
            ),
            checked_at="2026-07-23T00:00:00Z",
        )
        self.indexed = self._item(
            self.jira_source,
            "https://jira.primary.test/browse/IDX-2",
            "Indexed local title",
            "indexed",
        )
        apply_atlassian_target_result(
            self.connection,
            self.indexed["external_resource_id"],
            target_result(
                remote_id="primary-2",
                remote_key="IDX-2",
                metadata={"summary": "Indexed confirmed metadata"},
                content="Indexed remote body phrase",
            ),
            checked_at="2026-07-23T00:00:00Z",
            source_format="plain_text",
        )

    def tearDown(self):
        self.connection.close()

    def _source(self, key, service, display_name):
        return int(
            self.connection.execute(
                """
                INSERT INTO external_source_instances(
                    instance_key, provider_kind, service, display_name
                ) VALUES (?, 'mcp_gateway', ?, ?)
                """,
                (key, service, display_name),
            ).lastrowid
        )

    def _item(self, source_id, url, title, coverage):
        return create_or_reuse_atlassian_stub(
            self.connection,
            source_instance_id=source_id,
            url=url,
            title=title,
            coverage=coverage,
        )

    @contextmanager
    def _transaction(self):
        self.connection.execute("SAVEPOINT browse_route")
        try:
            yield self.connection
        except Exception:
            self.connection.execute("ROLLBACK TO browse_route")
            self.connection.execute("RELEASE browse_route")
            raise
        else:
            self.connection.execute("RELEASE browse_route")

    def _request(self, method="GET", path="/atlassian", body=""):
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
                "path": path,
                "headers": (
                    [(b"content-type", b"application/x-www-form-urlencoded")]
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

    def test_role_separated_fts_indexes_identity_metadata_content_and_local(self):
        roles = {
            row["source_kind"]
            for row in self.connection.execute(
                """
                SELECT source_kind FROM search_index
                WHERE entity_type = 'atlassian_item' AND entity_id = ?
                """,
                (str(self.indexed["external_resource_id"]),),
            )
        }
        self.assertEqual(
            roles,
            {
                "atlassian:jira:identity",
                "atlassian:jira:metadata",
                "atlassian:jira:content",
            },
        )
        metadata_roles = {
            row["source_kind"]
            for row in self.connection.execute(
                """
                SELECT source_kind FROM search_index
                WHERE entity_type = 'atlassian_item' AND entity_id = ?
                """,
                (str(self.metadata["external_resource_id"]),),
            )
        }
        self.assertEqual(
            metadata_roles,
            {"atlassian:jira:identity", "atlassian:jira:metadata"},
        )
        self.assertEqual(
            atlassian_search_results(
                self.connection, "remote body phrase"
            )[0]["entity_id"],
            str(self.indexed["external_resource_id"]),
        )
        self.assertEqual(
            atlassian_search_results(
                self.connection, "Secondary confirmed"
            )[0]["entity_id"],
            str(self.metadata["external_resource_id"]),
        )

        update_atlassian_local_state(
            self.connection,
            self.reference["external_resource_id"],
            note="Private local memory phrase",
            attention="pinned",
            tags="memory, Personal",
            new_topic_name="Knowledge base",
            new_topic_description="Local-only grouping",
        )
        local = atlassian_search_results(
            self.connection, "Private local memory"
        )
        self.assertEqual(
            local[0]["entity_id"],
            str(self.reference["external_resource_id"]),
        )
        self.assertEqual(local[0]["item_type"], "jira_issue")
        self.assertIn("local", local[0]["match_roles"])

    def test_filters_keep_same_key_sources_distinct_and_recover_archived(self):
        workstream_id = self.connection.execute(
            "INSERT INTO workstreams(name) VALUES ('Synthetic work')"
        ).lastrowid
        add_link(
            self.connection,
            "workstream",
            workstream_id,
            "external",
            str(self.reference["external_resource_id"]),
        )
        update_atlassian_local_state(
            self.connection,
            self.reference["external_resource_id"],
            note="",
            attention="archived",
            tags="Boundary",
            new_topic_name="Source boundary",
        )
        default = browse_inventory(
            self.connection, {"service": "jira", "q": "SAME-1"}
        )
        self.assertEqual(
            [item["id"] for item in default["items"]],
            [self.metadata["external_resource_id"]],
        )
        archived = browse_inventory(
            self.connection,
            {
                "service": "jira",
                "q": "SAME-1",
                "attention": "archived",
                "source_instance_id": self.jira_source,
                "workstream_id": workstream_id,
            },
        )
        self.assertEqual(
            [item["id"] for item in archived["items"]],
            [self.reference["external_resource_id"]],
        )
        same_key = browse_inventory(
            self.connection,
            {
                "service": "jira",
                "q": "SAME-1",
                "attention": "all",
            },
        )
        self.assertEqual(len(same_key["items"]), 2)
        self.assertEqual(
            {item["normalized_domain"] for item in same_key["items"]},
            {"jira.primary.test", "jira.secondary.test"},
        )

    def test_classifications_are_casefolded_reusable_and_survive_remote_failure(self):
        first = update_atlassian_local_state(
            self.connection,
            self.metadata["external_resource_id"],
            note="Owned locally",
            attention="normal",
            tags="API, api",
            new_topic_name="Platform",
            new_topic_description="Reusable topic",
        )
        topic_id = first["topics"][0]["id"]
        second = update_atlassian_local_state(
            self.connection,
            self.indexed["external_resource_id"],
            note="",
            attention="ignored",
            topic_ids=[topic_id],
            tags="Api",
        )
        self.assertEqual(second["topics"][0]["id"], topic_id)
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM atlassian_classifications
                WHERE kind = 'tag' AND normalized_name = 'api'
                """
            ).fetchone()[0],
            1,
        )

        apply_atlassian_target_result(
            self.connection,
            self.metadata["external_resource_id"],
            {
                "target_id": "synthetic-target",
                "locator": {"kind": "url", "value": "https://synthetic.invalid"},
                "outcome": "unavailable",
                "requests": [
                    {
                        "request_id": "synthetic-request",
                        "logical_operation": "jira.search_metadata",
                        "outcome": "unavailable",
                        "identity": {},
                        "metadata": {},
                        "content": None,
                        "remote_version": None,
                        "remote_updated_at": None,
                        "content_hash": None,
                        "error": {
                            "code": "unavailable",
                            "message": "Synthetic",
                        },
                    }
                ],
            },
            checked_at="2026-07-24T00:00:00Z",
        )
        retained = atlassian_item_detail(
            self.connection, self.metadata["external_resource_id"]
        )
        self.assertEqual(retained["note"], "Owned locally")
        self.assertEqual(retained["topics"][0]["name"], "Platform")
        self.assertEqual(retained["freshness"], "unavailable")

    def test_detail_separates_evidence_membership_and_latest_refresh(self):
        workstream_id = self.connection.execute(
            "INSERT INTO workstreams(name) VALUES ('Detail work')"
        ).lastrowid
        add_link(
            self.connection,
            "workstream",
            workstream_id,
            "external",
            str(self.indexed["external_resource_id"]),
        )
        source_id = self.connection.execute(
            """
            INSERT INTO sources(kind, name, root_path)
            VALUES ('codex', 'Codex', '/synthetic/codex')
            """
        ).lastrowid
        session_id = self.connection.execute(
            """
            INSERT INTO sessions(
                source_id, external_id, source_path, title, session_class,
                session_role, index_policy
            ) VALUES (?, 'detail-session', '/synthetic/session.jsonl',
                      'Evidence session',
                      'work', 'primary', 'full')
            """,
            (source_id,),
        ).lastrowid
        self.connection.execute(
            """
            INSERT INTO atlassian_item_evidence(
                external_resource_id, session_id, source_path,
                source_channel, source_event_id, source_line, url_ordinal,
                observed_url, normalized_url, extractor_version,
                evidence_key, first_observed_at, last_observed_at
            ) VALUES (?, ?, '/synthetic/session.jsonl', 'visible_text',
                      'event-1', 1, 1, ?, ?, 'synthetic-v1', ?, ?, ?)
            """,
            (
                self.indexed["external_resource_id"],
                session_id,
                "https://jira.primary.test/browse/IDX-2",
                "https://jira.primary.test/browse/IDX-2",
                "a" * 64,
                "2026-07-23T00:00:00Z",
                "2026-07-23T00:00:00Z",
            ),
        )
        run_id = "lb-synthetic-detail"
        manifest = {
            "targets": [
                {
                    "target_id": "atlassian-item-{}".format(
                        self.indexed["external_resource_id"]
                    )
                }
            ]
        }
        self.connection.execute(
            """
            INSERT INTO maintenance_runs(
                id, task_type, runner, status, source_snapshot_json
            ) VALUES (?, 'external_source_sync', 'codex', 'completed', ?)
            """,
            (run_id, json.dumps(manifest)),
        )
        self.connection.execute(
            """
            INSERT INTO external_sync_runs(
                maintenance_run_id, source_instance_id, source_kind,
                service, requested_scope_kind, selected_target_count,
                manifest_schema_version, read_policy_version
            ) VALUES (?, ?, 'atlassian', 'jira', 'item', 1,
                      'synthetic', 'synthetic')
            """,
            (run_id, self.jira_source),
        )
        detail = atlassian_item_detail(
            self.connection, self.indexed["external_resource_id"]
        )
        self.assertEqual(detail["evidence"][0]["session_id"], session_id)
        self.assertEqual(
            detail["memberships"][0]["workstream_id"], workstream_id
        )
        self.assertEqual(detail["latest_refresh_run"]["id"], run_id)
        self.assertNotIn("source_snapshot_json", detail["latest_refresh_run"])

    def test_no_script_browse_detail_and_local_post_use_only_local_state(self):
        prior_executor = app.state.external_read_executor
        app.state.external_read_executor = None
        try:
            with patch(
                "localbrain.main.connect", return_value=self.connection
            ):
                browse = atlassian_page(
                    self._request(),
                    view="jira",
                    mode="browse",
                    q="",
                    source_instance_id=None,
                    site_id=None,
                    space_id=None,
                    item_type=None,
                    coverage=None,
                    freshness=None,
                    attention=None,
                    topic_id=None,
                    tag_id=None,
                    workstream_id=None,
                    notice=None,
                    catalog_run=None,
                )
                detail = atlassian_item_page(
                    self._request(
                        path="/atlassian/items/{}".format(
                            self.reference["external_resource_id"]
                        )
                    ),
                    self.reference["external_resource_id"],
                    notice=None,
                )
            with patch(
                "localbrain.main.transaction",
                side_effect=lambda: self._transaction(),
            ):
                updated = asyncio.run(
                    atlassian_update_local(
                        self._request(
                            "POST",
                            "/atlassian/items/{}/local".format(
                                self.reference["external_resource_id"]
                            ),
                            "attention=pinned&note=No-script+note&"
                            "tags=local%2Cmemory&new_topic_name=Manual",
                        ),
                        self.reference["external_resource_id"],
                    )
                )
        finally:
            app.state.external_read_executor = prior_executor

        self.assertEqual(browse.status_code, 200)
        self.assertIn("LOCAL KNOWLEDGE BASE", browse.body.decode("utf-8"))
        self.assertEqual(detail.status_code, 200)
        self.assertIn("REMOTE FACTS", detail.body.decode("utf-8"))
        self.assertIn("LOCAL ONLY", detail.body.decode("utf-8"))
        self.assertEqual(updated.status_code, 303)
        saved = atlassian_item_detail(
            self.connection, self.reference["external_resource_id"]
        )
        self.assertEqual(saved["note"], "No-script note")
        self.assertEqual(saved["attention"], "pinned")
        self.assertEqual(saved["topics"][0]["name"], "Manual")
        self.assertEqual(
            search(self.connection, "No-script", source_scope="atlassian")[0][
                "entity_type"
            ],
            "atlassian_item",
        )


if __name__ == "__main__":
    unittest.main()
