import json
import sqlite3
import unittest
from datetime import datetime, timezone
from pathlib import Path

from localbrain.atlassian import (
    AtlassianContractError,
    apply_atlassian_target_result,
    atlassian_item_state,
    bind_atlassian_remote_identity,
    create_or_reuse_atlassian_stub,
    derive_atlassian_freshness,
    normalize_atlassian_content,
    normalize_atlassian_url,
    purge_atlassian_item,
    rebuild_atlassian_search_index,
    register_atlassian_site,
    register_atlassian_space,
    set_atlassian_item_axes,
)
from localbrain.queries import search


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


def request_result(
    *,
    outcome="changed",
    identity=None,
    metadata=None,
    content=None,
    remote_version="2",
    remote_updated_at="2026-07-23T00:00:00Z",
    error=None,
):
    result = {
        "request_id": "request-1",
        "logical_operation": "jira.read_description",
        "outcome": outcome,
        "identity": identity or {},
        "metadata": metadata or {},
        "content": content,
        "remote_version": remote_version,
        "remote_updated_at": remote_updated_at,
        "content_hash": None,
        "error": error,
    }
    return {
        "target_id": "target-1",
        "locator": {
            "kind": "url",
            "value": "https://jira.example.test/browse/SYN-1",
        },
        "outcome": outcome,
        "requests": [result],
    }


class AtlassianContractTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.jira_source = self._source("jira-source", "jira")
        self.confluence_source = self._source(
            "confluence-source", "confluence"
        )

    def tearDown(self):
        self.connection.close()

    def _source(self, key, service):
        cursor = self.connection.execute(
            """
            INSERT INTO external_source_instances(
                instance_key, provider_kind, service, display_name
            ) VALUES (?, 'mcp_gateway', ?, ?)
            """,
            (key, service, key),
        )
        return int(cursor.lastrowid)

    def _jira_stub(self, **overrides):
        values = {
            "source_instance_id": self.jira_source,
            "url": "https://jira.example.test/browse/SYN-1",
            "title": "Local title",
        }
        values.update(overrides)
        return create_or_reuse_atlassian_stub(self.connection, **values)

    def test_url_normalization_and_site_scoped_stub_reuse(self):
        normalized = normalize_atlassian_url(
            "HTTPS://JIRA.Example.Test:443/browse/SYN-1/?b=2&a=1#section"
        )
        self.assertEqual(normalized.normalized_domain, "jira.example.test")
        self.assertEqual(
            normalized.normalized_url,
            "https://jira.example.test/browse/SYN-1?a=1&b=2",
        )
        first = self._jira_stub(
            url="https://jira.example.test/browse/SYN-1?a=1&b=2"
        )
        repeated = self._jira_stub(
            url="https://JIRA.example.test:443/browse/SYN-1/?b=2&a=1#latest"
        )
        self.assertEqual(
            first["external_resource_id"], repeated["external_resource_id"]
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM external_resources"
            ).fetchone()[0],
            1,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_urls"
            ).fetchone()[0],
            1,
        )

        other_source = self._source("jira-source-two", "jira")
        same_domain_item = create_or_reuse_atlassian_stub(
            self.connection,
            source_instance_id=other_source,
            url="https://jira.example.test/browse/SYN-1?a=1&b=2",
            title="Separate source",
        )
        self.assertEqual(
            first["external_resource_id"],
            same_domain_item["external_resource_id"],
        )
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM atlassian_site_bindings
                WHERE site_id = ?
                """,
                (first["site_id"],),
            ).fetchone()[0],
            2,
        )

    def test_one_source_instance_can_own_multiple_site_domains(self):
        first = register_atlassian_site(
            self.connection,
            source_instance_id=self.jira_source,
            base_url="https://jira-a.example.test",
            remote_site_id="site-a",
        )
        second = register_atlassian_site(
            self.connection,
            source_instance_id=self.jira_source,
            base_url="https://jira-b.example.test",
            remote_site_id="site-b",
        )
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM atlassian_sites
                WHERE source_instance_id = ?
                """,
                (self.jira_source,),
            ).fetchone()[0],
            2,
        )
        first_item = create_or_reuse_atlassian_stub(
            self.connection,
            source_instance_id=self.jira_source,
            url="https://jira-a.example.test/browse/SAME-1",
        )
        second_item = create_or_reuse_atlassian_stub(
            self.connection,
            source_instance_id=self.jira_source,
            url="https://jira-b.example.test/browse/SAME-1",
        )
        bind_atlassian_remote_identity(
            self.connection,
            first_item["external_resource_id"],
            remote_id="same-remote",
            remote_key="SAME-1",
        )
        bind_atlassian_remote_identity(
            self.connection,
            second_item["external_resource_id"],
            remote_id="same-remote",
            remote_key="SAME-1",
        )
        self.assertNotEqual(
            first_item["external_resource_id"],
            second_item["external_resource_id"],
        )

    def test_strict_one_to_one_extension_and_in_place_remote_binding(self):
        resource = self.connection.execute(
            """
            INSERT INTO external_resources(
                resource_type, title, url, summary, source_role
            ) VALUES (
                'jira', 'User title', 'https://jira.example.test/browse/SYN-2',
                'User note', 'primary'
            )
            """
        )
        resource_id = int(resource.lastrowid)
        self.connection.execute(
            "INSERT INTO workstreams(id, name) VALUES (1, 'Synthetic')"
        )
        self.connection.execute(
            """
            INSERT INTO workstream_links(
                workstream_id, entity_type, entity_id, relation_type
            ) VALUES (1, 'external', ?, 'evidence')
            """,
            (str(resource_id),),
        )
        stub = self._jira_stub(
            url="https://jira.example.test/browse/SYN-2",
            title=None,
            external_resource_id=resource_id,
        )
        bound = bind_atlassian_remote_identity(
            self.connection,
            resource_id,
            remote_id="remote-2",
            remote_key="SYN-2",
            canonical_url="https://jira.example.test/issues/?key=SYN-2",
            confirmed_at="2026-07-23T00:00:00Z",
        )
        self.assertEqual(stub["external_resource_id"], resource_id)
        self.assertEqual(bound["external_resource_id"], resource_id)
        self.assertEqual(bound["remote_id"], "remote-2")
        self.assertEqual(
            self.connection.execute(
                """
                SELECT entity_id FROM workstream_links
                WHERE workstream_id = 1
                """
            ).fetchone()[0],
            str(resource_id),
        )
        local = self.connection.execute(
            "SELECT title, summary, source_role, url FROM external_resources WHERE id = ?",
            (resource_id,),
        ).fetchone()
        self.assertEqual(
            tuple(local),
            (
                "User title",
                "User note",
                "primary",
                "https://jira.example.test/browse/SYN-2",
            ),
        )
        urls = self.connection.execute(
            """
            SELECT url_role, normalized_url FROM atlassian_item_urls
            WHERE external_resource_id = ? ORDER BY url_role
            """,
            (resource_id,),
        ).fetchall()
        self.assertEqual([row["url_role"] for row in urls], ["alias", "canonical"])
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_items WHERE external_resource_id = ?",
                (resource_id,),
            ).fetchone()[0],
            1,
        )

    def test_manual_external_resource_is_reused_without_caller_supplied_id(self):
        resource_id = int(
            self.connection.execute(
                """
                INSERT INTO external_resources(
                    resource_type, title, url, summary
                ) VALUES (
                    'jira', 'Manual',
                    'https://JIRA.example.test:443/browse/SYN-9/#local',
                    'Keep locally'
                )
                """
            ).lastrowid
        )
        stub = self._jira_stub(
            url="https://jira.example.test/browse/SYN-9",
            title="Remote placeholder",
        )
        self.assertEqual(stub["external_resource_id"], resource_id)
        self.assertEqual(
            tuple(
                self.connection.execute(
                    """
                    SELECT title, summary FROM external_resources WHERE id = ?
                    """,
                    (resource_id,),
                ).fetchone()
            ),
            ("Manual", "Keep locally"),
        )

    def test_remote_and_url_collisions_fail_before_mutation(self):
        first = self._jira_stub()
        second = self._jira_stub(
            url="https://jira.example.test/browse/SYN-2",
            title="Second",
        )
        bind_atlassian_remote_identity(
            self.connection,
            first["external_resource_id"],
            remote_id="same-remote",
            remote_key="SYN-1",
        )
        before = dict(
            self.connection.execute(
                """
                SELECT remote_id, remote_key, confirmed_at
                FROM atlassian_items WHERE external_resource_id = ?
                """,
                (second["external_resource_id"],),
            ).fetchone()
        )
        with self.assertRaisesRegex(
            AtlassianContractError, "already bound to another Item"
        ):
            bind_atlassian_remote_identity(
                self.connection,
                second["external_resource_id"],
                remote_id="same-remote",
                remote_key="SYN-2",
                canonical_url="https://jira.example.test/browse/SYN-1",
            )
        after = dict(
            self.connection.execute(
                """
                SELECT remote_id, remote_key, confirmed_at
                FROM atlassian_items WHERE external_resource_id = ?
                """,
                (second["external_resource_id"],),
            ).fetchone()
        )
        self.assertEqual(after, before)
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM atlassian_item_urls
                WHERE external_resource_id = ?
                """,
                (second["external_resource_id"],),
            ).fetchone()[0],
            1,
        )

    def test_space_must_stay_inside_site_and_service(self):
        stub = self._jira_stub()
        site_id = stub["site_id"]
        space = register_atlassian_space(
            self.connection,
            site_id=site_id,
            name="Synthetic project",
            remote_id="project-1",
            space_key="SYN",
        )
        bound = bind_atlassian_remote_identity(
            self.connection,
            stub["external_resource_id"],
            remote_id="issue-1",
            remote_key="SYN-1",
            space_id=space["id"],
        )
        self.assertEqual(bound["space_id"], space["id"])

        other_site = register_atlassian_site(
            self.connection,
            source_instance_id=self.jira_source,
            base_url="https://other-jira.example.test",
        )
        other_space = register_atlassian_space(
            self.connection,
            site_id=other_site["id"],
            name="Other",
            space_key="OTH",
        )
        with self.assertRaisesRegex(
            AtlassianContractError, "does not belong"
        ):
            bind_atlassian_remote_identity(
                self.connection,
                stub["external_resource_id"],
                remote_id="issue-1",
                space_id=other_space["id"],
            )

    def test_freshness_is_derived_and_due_is_not_stale(self):
        now = datetime(2026, 7, 23, tzinfo=timezone.utc)
        self.assertEqual(
            derive_atlassian_freshness("jira", None, now=now), "unknown"
        )
        self.assertEqual(
            derive_atlassian_freshness(
                "jira",
                {
                    "last_successful_at": "2026-07-16T00:00:01Z",
                    "last_outcome": "unchanged",
                    "known_changed": 0,
                    "projection_stale": 0,
                },
                now=now,
            ),
            "current",
        )
        self.assertEqual(
            derive_atlassian_freshness(
                "jira",
                {
                    "last_successful_at": "2026-07-16T00:00:00Z",
                    "last_outcome": "unchanged",
                    "known_changed": 0,
                    "projection_stale": 0,
                },
                now=now,
            ),
            "due",
        )
        self.assertEqual(
            derive_atlassian_freshness(
                "confluence",
                {
                    "last_successful_at": "2026-06-23T00:00:00Z",
                    "last_outcome": "unchanged",
                    "known_changed": 0,
                    "projection_stale": 0,
                },
                now=now,
            ),
            "due",
        )
        self.assertEqual(
            derive_atlassian_freshness(
                "jira",
                {
                    "last_successful_at": "2026-07-22T00:00:00Z",
                    "last_outcome": "changed",
                    "known_changed": 1,
                    "projection_stale": 0,
                },
                now=now,
            ),
            "stale",
        )
        self.assertEqual(
            derive_atlassian_freshness(
                "jira",
                {
                    "last_successful_at": "2026-07-22T00:00:00Z",
                    "last_outcome": "unavailable",
                    "known_changed": 1,
                    "projection_stale": 1,
                },
                now=now,
            ),
            "unavailable",
        )

    def test_result_application_is_hash_gated_and_retains_last_known_data(self):
        stub = self._jira_stub(coverage="indexed")
        item_id = stub["external_resource_id"]
        checked_at = (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Remote detail"}],
                }
            ],
        }
        changed = request_result(
            identity={
                "remote_id": "issue-1",
                "remote_key": "SYN-1",
                "canonical_url": "https://jira.example.test/browse/SYN-1",
            },
            metadata={"summary": "Remote summary", "status": "Open"},
            content={"format": "jira_adf", "body": adf},
        )
        state = apply_atlassian_target_result(
            self.connection,
            item_id,
            changed,
            checked_at=checked_at,
        )
        self.assertEqual(state["freshness"], "current")
        local = self.connection.execute(
            "SELECT title FROM external_resources WHERE id = ?", (item_id,)
        ).fetchone()[0]
        self.assertEqual(local, "Local title")
        content_before = dict(
            self.connection.execute(
                """
                SELECT source_hash, normalized_text, applied_at, updated_at,
                       search_projection_hash
                FROM atlassian_item_content
                WHERE external_resource_id = ?
                """,
                (item_id,),
            ).fetchone()
        )
        search_before = dict(
            self.connection.execute(
                """
                SELECT rowid, title, body, path
                FROM search_index
                WHERE entity_type = 'atlassian_item' AND entity_id = ?
                """,
                (str(item_id),),
            ).fetchone()
        )
        self.assertEqual(search_before["title"], "Remote summary")
        self.assertIn("Remote detail", search_before["body"])

        unchanged = request_result(
            outcome="unchanged",
            identity={
                "remote_id": "issue-1",
                "remote_key": "SYN-1",
                "canonical_url": "https://jira.example.test/browse/SYN-1",
            },
            metadata={"summary": "Remote summary", "status": "Open"},
            content={"format": "jira_adf", "body": adf},
        )
        apply_atlassian_target_result(
            self.connection,
            item_id,
            unchanged,
            checked_at=checked_at,
        )
        content_after = dict(
            self.connection.execute(
                """
                SELECT source_hash, normalized_text, applied_at, updated_at,
                       search_projection_hash
                FROM atlassian_item_content
                WHERE external_resource_id = ?
                """,
                (item_id,),
            ).fetchone()
        )
        search_after = dict(
            self.connection.execute(
                """
                SELECT rowid, title, body, path
                FROM search_index
                WHERE entity_type = 'atlassian_item' AND entity_id = ?
                """,
                (str(item_id),),
            ).fetchone()
        )
        self.assertEqual(content_after, content_before)
        self.assertEqual(search_after, search_before)

        failure = request_result(
            outcome="unavailable",
            content=None,
            remote_version=None,
            remote_updated_at=None,
            error={"code": "synthetic-unavailable", "message": "ignored"},
        )
        unavailable = apply_atlassian_target_result(
            self.connection,
            item_id,
            failure,
            checked_at=checked_at,
        )
        self.assertEqual(unavailable["freshness"], "unavailable")
        self.assertEqual(
            dict(
                self.connection.execute(
                    """
                    SELECT source_hash, normalized_text, applied_at, updated_at,
                           search_projection_hash
                    FROM atlassian_item_content
                    WHERE external_resource_id = ?
                    """,
                    (item_id,),
                ).fetchone()
            ),
            content_before,
        )
        self.assertEqual(
            dict(
                self.connection.execute(
                    """
                    SELECT rowid, title, body, path
                    FROM search_index
                    WHERE entity_type = 'atlassian_item' AND entity_id = ?
                    """,
                    (str(item_id),),
                ).fetchone()
            ),
            search_before,
        )

    def test_known_remote_change_without_body_is_stale(self):
        stub = self._jira_stub(coverage="indexed")
        state = apply_atlassian_target_result(
            self.connection,
            stub["external_resource_id"],
            request_result(
                content=None,
                identity={"remote_id": "issue-1"},
                metadata={"summary": "Changed"},
            ),
            checked_at="2026-07-23T00:00:00Z",
        )
        self.assertEqual(state["freshness"], "stale")
        self.assertEqual(state["remote_state"]["known_changed"], 1)
        self.assertEqual(state["remote_state"]["projection_stale"], 1)

    def test_partial_metadata_refresh_merges_and_first_success_requires_identity(self):
        stub = self._jira_stub(coverage="metadata")
        item_id = stub["external_resource_id"]
        with self.assertRaisesRegex(
            AtlassianContractError, "requires a remote ID"
        ):
            apply_atlassian_target_result(
                self.connection,
                item_id,
                request_result(
                    identity={},
                    metadata={"summary": "Cannot confirm alone"},
                    content=None,
                ),
                checked_at="2026-07-23T00:00:00Z",
            )
        apply_atlassian_target_result(
            self.connection,
            item_id,
            request_result(
                identity={"remote_id": "issue-1"},
                metadata={"summary": "Original", "status": "Open"},
                content=None,
            ),
            checked_at="2026-07-23T01:00:00Z",
        )
        apply_atlassian_target_result(
            self.connection,
            item_id,
            request_result(
                outcome="unchanged",
                identity={},
                metadata={"status": "Closed"},
                content=None,
            ),
            checked_at="2026-07-23T02:00:00Z",
        )
        metadata = json.loads(
            self.connection.execute(
                """
                SELECT metadata_json FROM atlassian_item_remote_state
                WHERE external_resource_id = ?
                """,
                (item_id,),
            ).fetchone()[0]
        )
        self.assertEqual(
            metadata, {"status": "Closed", "summary": "Original"}
        )

    def test_coverage_gates_projection_and_rebuild_is_deterministic(self):
        stub = self._jira_stub(coverage="indexed")
        item_id = stub["external_resource_id"]
        apply_atlassian_target_result(
            self.connection,
            item_id,
            request_result(
                identity={"remote_id": "issue-1"},
                metadata={"summary": "Searchable synthetic"},
                content="Search body",
            ),
            checked_at="2026-07-23T00:00:00Z",
            source_format="plain_text",
        )
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM search_index
                WHERE entity_type = 'atlassian_item'
                """
            ).fetchone()[0],
            3,
        )
        search_results = search(self.connection, "Searchable")
        self.assertEqual(len(search_results), 1)
        self.assertEqual(
            search_results[0]["entity_type"], "atlassian_item"
        )
        self.assertIn("metadata", search_results[0]["match_roles"])
        set_atlassian_item_axes(
            self.connection, item_id, coverage="metadata"
        )
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM search_index
                WHERE entity_type = 'atlassian_item'
                """
            ).fetchone()[0],
            2,
        )
        self.assertIsNone(
            self.connection.execute(
                """
                SELECT source_hash FROM atlassian_item_content
                WHERE external_resource_id = ?
                """,
                (item_id,),
            ).fetchone()
        )
        set_atlassian_item_axes(
            self.connection, item_id, coverage="indexed"
        )
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM search_index
                WHERE entity_type = 'atlassian_item'
                """
            ).fetchone()[0],
            2,
        )
        apply_atlassian_target_result(
            self.connection,
            item_id,
            request_result(
                outcome="changed",
                identity={},
                metadata={"summary": "Searchable synthetic"},
                content="Search body",
                remote_version="3",
            ),
            checked_at="2026-07-24T00:00:00Z",
            source_format="plain_text",
        )
        first = [
            tuple(row)
            for row in self.connection.execute(
                """
                SELECT entity_type, entity_id, source_kind, title, body, path
                FROM search_index WHERE entity_type = 'atlassian_item'
                """
            )
        ]
        self.assertEqual(rebuild_atlassian_search_index(self.connection), 1)
        second = [
            tuple(row)
            for row in self.connection.execute(
                """
                SELECT entity_type, entity_id, source_kind, title, body, path
                FROM search_index WHERE entity_type = 'atlassian_item'
                """
            )
        ]
        self.assertEqual(first, second)

    def test_coverage_rejects_remote_facts_outside_persistence_intent(self):
        reference = self._jira_stub()
        with self.assertRaisesRegex(
            AtlassianContractError, "cannot store remote metadata"
        ):
            apply_atlassian_target_result(
                self.connection,
                reference["external_resource_id"],
                request_result(
                    identity={"remote_id": "issue-reference"},
                    metadata={"summary": "Not eligible"},
                    content=None,
                ),
            )
        self.assertIsNone(
            self.connection.execute(
                """
                SELECT remote_id FROM atlassian_items
                WHERE external_resource_id = ?
                """,
                (reference["external_resource_id"],),
            ).fetchone()[0]
        )

        metadata = self._jira_stub(
            url="https://jira.example.test/browse/SYN-META",
            coverage="metadata",
        )
        with self.assertRaisesRegex(
            AtlassianContractError, "Only indexed coverage"
        ):
            apply_atlassian_target_result(
                self.connection,
                metadata["external_resource_id"],
                request_result(
                    identity={"remote_id": "issue-metadata"},
                    metadata={"summary": "Eligible metadata"},
                    content="Ineligible body",
                ),
                source_format="plain_text",
            )

    def test_remote_body_cannot_cross_metadata_boundary(self):
        stub = self._jira_stub()
        before = self.connection.total_changes
        with self.assertRaisesRegex(
            AtlassianContractError, "cannot be stored as metadata"
        ):
            apply_atlassian_target_result(
                self.connection,
                stub["external_resource_id"],
                request_result(
                    identity={"remote_id": "issue-1"},
                    metadata={"description": "must stay content"},
                    content=None,
                ),
                checked_at="2026-07-23T00:00:00Z",
            )
        self.assertGreaterEqual(self.connection.total_changes, before)
        item = self.connection.execute(
            """
            SELECT remote_id, confirmed_at FROM atlassian_items
            WHERE external_resource_id = ?
            """,
            (stub["external_resource_id"],),
        ).fetchone()
        self.assertEqual(tuple(item), (None, None))
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_remote_state"
            ).fetchone()[0],
            0,
        )
        with self.assertRaisesRegex(
            AtlassianContractError, "cannot be stored as metadata"
        ):
            apply_atlassian_target_result(
                self.connection,
                stub["external_resource_id"],
                request_result(
                    identity={"remote_id": "issue-1"},
                    metadata={
                        "rendered": {
                            "body": "nested body must stay content"
                        }
                    },
                    content=None,
                ),
                checked_at="2026-07-23T00:00:00Z",
            )

    def test_explicit_purge_cleans_polymorphic_links_and_projection(self):
        stub = self._jira_stub(coverage="indexed")
        item_id = stub["external_resource_id"]
        site_id = stub["site_id"]
        self.connection.execute(
            "INSERT INTO workstreams(id, name) VALUES (1, 'Synthetic purge')"
        )
        self.connection.execute(
            """
            INSERT INTO workstream_links(
                workstream_id, entity_type, entity_id
            ) VALUES (1, 'external', ?)
            """,
            (str(item_id),),
        )
        apply_atlassian_target_result(
            self.connection,
            item_id,
            request_result(
                identity={"remote_id": "issue-1"},
                content="Synthetic",
            ),
            source_format="plain_text",
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "DELETE FROM atlassian_sites WHERE id = ?", (site_id,)
            )
        result = purge_atlassian_item(self.connection, item_id)
        self.assertEqual(result["workstream_links"], 1)
        self.assertEqual(result["search_rows"], 2)
        for table in (
            "atlassian_items",
            "atlassian_item_urls",
            "atlassian_item_remote_state",
            "atlassian_item_content",
        ):
            self.assertEqual(
                self.connection.execute(
                    "SELECT COUNT(*) FROM {}".format(table)
                ).fetchone()[0],
                0,
            )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_sites WHERE id = ?", (site_id,)
            ).fetchone()[0],
            1,
        )
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM search_index
                WHERE entity_type = 'atlassian_item'
                """
            ).fetchone()[0],
            0,
        )

    def test_remote_state_constraint_requires_bounded_failure_code(self):
        stub = self._jira_stub()
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO atlassian_item_remote_state(
                    external_resource_id, last_outcome
                ) VALUES (?, 'unavailable')
                """,
                (stub["external_resource_id"],),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO atlassian_item_remote_state(
                    external_resource_id, last_outcome, last_error_code
                ) VALUES (?, 'error', ?)
                """,
                (stub["external_resource_id"], "x" * 81),
            )

    def test_confluence_page_content_uses_same_contract(self):
        stub = create_or_reuse_atlassian_stub(
            self.connection,
            source_instance_id=self.confluence_source,
            url="https://wiki.example.test/spaces/SYN/pages/100/Page",
            coverage="indexed",
            title="Local page",
        )
        result = request_result(
            identity={
                "remote_id": "100",
                "canonical_url": (
                    "https://wiki.example.test/spaces/SYN/pages/100/Page"
                ),
            },
            metadata={"title": "Remote page", "labels": ["synthetic"]},
            content={
                "format": "storage",
                "body": "<h1>Remote heading</h1><p>Page body</p>",
            },
            remote_version="7",
        )
        result["requests"][0]["logical_operation"] = "confluence.read_page"
        state = apply_atlassian_target_result(
            self.connection,
            stub["external_resource_id"],
            result,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )
        self.assertEqual(state["service"], "confluence")
        self.assertEqual(state["freshness"], "current")
        row = self.connection.execute(
            """
            SELECT source_format, normalized_text
            FROM atlassian_item_content
            WHERE external_resource_id = ?
            """,
            (stub["external_resource_id"],),
        ).fetchone()
        self.assertEqual(row["source_format"], "confluence_html")
        self.assertIn("Page body", row["normalized_text"])


class AtlassianNormalizationTests(unittest.TestCase):
    def test_adf_is_deterministic_and_unknown_nodes_keep_known_text(self):
        value = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "mystery",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "Preserved text"}
                            ],
                        }
                    ],
                }
            ],
        }
        first = normalize_atlassian_content("jira_adf", value)
        second = normalize_atlassian_content("jira_adf", value)
        self.assertEqual(first, second)
        self.assertIn("Preserved text", first.normalized_text)
        self.assertIn("unsupported ADF node", first.warning)
        self.assertEqual(
            json.loads(first.normalized_document_json)["schema"],
            "localbrain.atlassian-normalized.v1",
        )

    def test_html_ignores_active_content_and_markdown_ignores_raw_html(self):
        html = normalize_atlassian_content(
            "confluence_html",
            "<h1>Visible</h1><script>privateCall()</script><p>Body</p>",
        )
        self.assertIn("Visible", html.normalized_text)
        self.assertIn("Body", html.normalized_text)
        self.assertNotIn("privateCall", html.normalized_text)
        self.assertIn("ignored active HTML tag", html.warning)

        markdown = normalize_atlassian_content(
            "confluence_markdown",
            "# Heading\n\nVisible **body**\n\n<script>hidden</script>",
        )
        self.assertIn("Heading", markdown.normalized_text)
        self.assertIn("Visible", markdown.normalized_text)
        self.assertNotIn("hidden", markdown.normalized_text)
        self.assertIn("ignored HTML block", markdown.warning)
