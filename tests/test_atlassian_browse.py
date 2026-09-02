import asyncio
import html
import json
import re
import sqlite3
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, quote_plus, urlsplit

from fastapi import HTTPException
from starlette.requests import Request

from localbrain.atlassian import (
    apply_atlassian_target_result,
    bind_atlassian_remote_identity,
    create_or_reuse_atlassian_stub,
    register_atlassian_site,
    register_atlassian_space,
)
from localbrain.atlassian_browse import (
    AtlassianBrowseError,
    atlassian_item_detail,
    atlassian_item_preview,
    atlassian_search_results,
    atlassian_structure_reference_detail,
    browse_inventory,
    update_atlassian_local_state,
)
from localbrain.atlassian_locators import describe_atlassian_url
from localbrain.atlassian_structure_references import (
    ensure_structure_reference,
    insert_or_reuse_structure_reference_evidence,
    project_structure_reference_search,
)
from localbrain.main import (
    _atlassian_inventory_return_path,
    app,
    atlassian_add_local_link,
    atlassian_item_page,
    atlassian_page,
    atlassian_reference_page,
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

    def _request(
        self,
        method="GET",
        path="/atlassian",
        body="",
        headers=None,
        query_string="",
    ):
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

        request_headers = (
            [(b"content-type", b"application/x-www-form-urlencoded")]
            if method == "POST"
            else []
        )
        request_headers.extend(
            (str(key).lower().encode("ascii"), str(value).encode("utf-8"))
            for key, value in (headers or {}).items()
        )
        return Request(
            {
                "type": "http",
                "app": app,
                "method": method,
                "path": path,
                "headers": request_headers,
                "query_string": query_string.encode("utf-8"),
                "server": ("test", 80),
                "client": ("test", 1),
                "scheme": "http",
            },
            receive,
        )

    def _page(self, **overrides):
        headers = overrides.pop("_headers", None)
        query_string = overrides.pop("_query_string", "")
        values = {
            "view": "all",
            "mode": "browse",
            "method": "url",
            "q": "",
            "source_instance_id": None,
            "site_id": None,
            "space_id": None,
            "structural_scope": None,
            "item_type": None,
            "coverage": None,
            "freshness": None,
            "attention": None,
            "topic_id": None,
            "tag_id": None,
            "workstream_id": None,
            "notice": None,
            "catalog_run": None,
            "item": None,
            "reference": None,
        }
        values.update(overrides)
        with patch("localbrain.main.connect", return_value=self.connection):
            return atlassian_page(
                self._request(
                    headers=headers, query_string=query_string
                ),
                **values,
            )

    def _structure_reference(self, url):
        locator = describe_atlassian_url(url)
        self.assertEqual(locator.kind, "structure")
        site = self.connection.execute(
            "SELECT id FROM atlassian_sites WHERE normalized_domain = ?",
            (locator.normalized_domain,),
        ).fetchone()
        if site is None:
            site_id = int(
                register_atlassian_site(
                    self.connection,
                    base_url=locator.canonical_base_url,
                )["id"]
            )
        else:
            site_id = int(site["id"])
        source_id = int(
            self.connection.execute(
                """
                INSERT INTO sources(kind, name, root_path)
                VALUES ('context', 'Structure fixture', '/synthetic/structure')
                """
            ).lastrowid
        )
        root_id = int(
            self.connection.execute(
                """
                INSERT INTO context_roots(path, label)
                VALUES ('/synthetic/structure', 'Structure fixture')
                """
            ).lastrowid
        )
        document_id = int(
            self.connection.execute(
                """
                INSERT INTO context_documents(
                    source_id, context_root_id, path, relative_path, title,
                    body, size_bytes, mtime_ns, content_hash
                ) VALUES (?, ?, '/synthetic/structure/reference.md',
                          'reference.md', 'Structure fixture', ?, ?, 1, ?)
                """,
                (source_id, root_id, url, len(url), "a" * 64),
            ).lastrowid
        )
        target = ensure_structure_reference(
            self.connection,
            site_id=site_id,
            locator=locator,
            observed_at="2026-09-01T00:00:00Z",
        )
        insert_or_reuse_structure_reference_evidence(
            self.connection,
            reference_id=target["reference_id"],
            safe_locator_url=locator.safe_locator_url,
            container_hint=locator.container_hint,
            document_id=document_id,
            source_line=1,
            url_ordinal=1,
            source_channel="visible_text",
            observed_at="2026-09-01T00:00:00Z",
        )
        project_structure_reference_search(
            self.connection, target["reference_id"]
        )
        return int(target["reference_id"]), site_id, document_id

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

    def test_exact_browse_matches_complete_identity_and_normalized_alias_url(self):
        bind_atlassian_remote_identity(
            self.connection,
            self.reference["external_resource_id"],
            remote_id="Remote-Case-9",
            remote_key="CASE-9",
            canonical_url="https://jira.primary.test/issues/?key=CASE-9",
            confirmed_at="2026-08-29T00:00:00Z",
        )
        identity_queries = (
            "case-9",
            "REMOTE-CASE-9",
            "https://jira.primary.test/issues/?key=CASE-9",
            "https://JIRA.PRIMARY.TEST:443/browse/SAME-1/#ignored",
        )
        for query in identity_queries:
            with self.subTest(query=query):
                result = browse_inventory(
                    self.connection,
                    {"q": query, "attention": "all"},
                )
                self.assertEqual(
                    [item["id"] for item in result["items"]],
                    [self.reference["external_resource_id"]],
                )
                self.assertEqual(
                    result["items"][0]["exact_match"]["role"],
                    "identity",
                )
                self.assertEqual(
                    result["items"][0]["exact_match"]["rank"], 0
                )

        partial = browse_inventory(
            self.connection, {"q": "Remote", "attention": "all"}
        )["items"]
        self.assertNotIn(
            self.reference["external_resource_id"],
            {item["id"] for item in partial},
        )
        with self.assertRaisesRegex(
            AtlassianBrowseError, "HTTP\(S\) query URL is invalid"
        ):
            browse_inventory(self.connection, {"q": "https://[invalid"})

    def test_exact_browse_requires_contiguous_tokens_in_one_owned_value(self):
        contiguous = browse_inventory(
            self.connection, {"q": "REMOTE body", "attention": "all"}
        )
        self.assertEqual(
            [item["id"] for item in contiguous["items"]],
            [self.indexed["external_resource_id"]],
        )
        self.assertEqual(
            contiguous["items"][0]["exact_match"]["role"], "content"
        )
        self.assertEqual(
            browse_inventory(
                self.connection,
                {"q": "remote phrase", "attention": "all"},
            )["items"],
            [],
        )

        self.connection.execute(
            "UPDATE external_resources SET title = ? WHERE id = ?",
            ("Cross Alpha", self.reference["external_resource_id"]),
        )
        update_atlassian_local_state(
            self.connection,
            self.reference["external_resource_id"],
            note="Beta memory",
            attention="normal",
        )
        self.assertEqual(
            browse_inventory(
                self.connection,
                {"q": "Alpha Beta", "attention": "all"},
            )["items"],
            [],
        )
        self.assertEqual(
            browse_inventory(
                self.connection,
                {"q": "metadata Open", "attention": "all"},
            )["items"],
            [],
        )
        metadata = browse_inventory(
            self.connection, {"q": "OPEN", "attention": "all"}
        )
        self.assertEqual(
            [item["id"] for item in metadata["items"]],
            [self.metadata["external_resource_id"]],
        )
        self.assertEqual(
            metadata["items"][0]["exact_match"]["role"], "metadata"
        )
        self.connection.execute(
            "UPDATE external_resources SET title = ? WHERE id = ?",
            ("Café ＡＰＩ guide", self.reference["external_resource_id"]),
        )
        self.assertEqual(
            browse_inventory(
                self.connection, {"q": "CAFÉ API", "attention": "all"}
            )["items"][0]["id"],
            self.reference["external_resource_id"],
        )
        self.assertNotIn(
            self.reference["external_resource_id"],
            {
                item["id"]
                for item in browse_inventory(
                    self.connection,
                    {"q": "CAFE API", "attention": "all"},
                )["items"]
            },
        )

    def test_unavailable_remote_body_is_not_an_exact_query_owner(self):
        item_id = self.indexed["external_resource_id"]
        self.connection.execute(
            """
            UPDATE atlassian_item_remote_state
            SET last_outcome = 'unavailable',
                last_error_code = 'synthetic-unavailable'
            WHERE external_resource_id = ?
            """,
            (item_id,),
        )
        self.connection.execute(
            """
            INSERT INTO atlassian_item_local_state(
                external_resource_id, note
            ) VALUES (?, 'Available local memory phrase')
            """,
            (item_id,),
        )

        remote_body = browse_inventory(
            self.connection, {"q": "Indexed remote body phrase"}
        )
        self.assertEqual(remote_body["matching_count"], 0)
        self.assertFalse(
            atlassian_item_preview(
                self.connection,
                item_id,
                {"q": "Indexed remote body phrase"},
            )["eligible"]
        )
        local_note = browse_inventory(
            self.connection, {"q": "Available local memory phrase"}
        )
        self.assertEqual(
            [item["id"] for item in local_note["items"]],
            [item_id],
        )
        self.assertTrue(
            atlassian_item_preview(
                self.connection,
                item_id,
                {"q": "Available local memory phrase"},
            )["eligible"]
        )

    def test_exact_browse_ranks_identity_title_other_then_stable_id(self):
        bind_atlassian_remote_identity(
            self.connection,
            self.reference["external_resource_id"],
            remote_id="rank-identity",
            remote_key="RANK",
            confirmed_at="2026-08-29T00:00:00Z",
        )
        self.connection.execute(
            "UPDATE external_resources SET title = 'Rank' WHERE id = ?",
            (self.metadata["external_resource_id"],),
        )
        update_atlassian_local_state(
            self.connection,
            self.indexed["external_resource_id"],
            note="Rank",
            attention="normal",
        )
        ranked = browse_inventory(
            self.connection, {"q": "rank", "attention": "all"}
        )["items"]
        self.assertEqual(
            [item["id"] for item in ranked],
            [
                self.reference["external_resource_id"],
                self.metadata["external_resource_id"],
                self.indexed["external_resource_id"],
            ],
        )
        self.assertEqual(
            [item["exact_match"]["rank"] for item in ranked], [0, 1, 2]
        )

        self.connection.execute(
            "UPDATE external_resources SET title = 'Stable tie' WHERE id IN (?, ?)",
            (
                self.metadata["external_resource_id"],
                self.indexed["external_resource_id"],
            ),
        )
        tied = browse_inventory(
            self.connection, {"q": "stable tie", "attention": "all"}
        )["items"]
        self.assertEqual(
            [item["id"] for item in tied],
            sorted(
                [
                    self.metadata["external_resource_id"],
                    self.indexed["external_resource_id"],
                ]
            ),
        )

    def test_exact_browse_combines_services_unclassified_and_filters(self):
        wiki_source = self._source(
            "confluence-primary", "confluence", "Primary Wiki"
        )
        wiki = self._item(
            wiki_source,
            "https://wiki.primary.test/spaces/TEAM/pages/12345/Shared",
            "Shared retrieval phrase",
            "reference",
        )
        self.connection.execute(
            "UPDATE external_resources SET title = ? WHERE id = ?",
            ("Shared retrieval phrase", self.reference["external_resource_id"]),
        )
        space_id = int(
            self.connection.execute(
                """
                INSERT INTO atlassian_spaces(
                    site_id, source_instance_id, service, remote_id,
                    space_key, name, canonical_url, coverage
                )
                SELECT site_id, source_instance_id, service, 'space-1',
                       'TEAM', 'Synthetic project',
                       'https://jira.primary.test/projects/TEAM',
                       'selected-content'
                FROM atlassian_items
                WHERE external_resource_id = ?
                """,
                (self.reference["external_resource_id"],),
            ).lastrowid
        )
        self.connection.execute(
            "UPDATE atlassian_items SET space_id = ? WHERE external_resource_id = ?",
            (space_id, self.reference["external_resource_id"]),
        )

        combined = browse_inventory(
            self.connection,
            {"q": "shared retrieval", "attention": "all"},
        )["items"]
        self.assertEqual(
            {item["service"] for item in combined}, {"jira", "confluence"}
        )
        wiki_only = browse_inventory(
            self.connection,
            {
                "q": "shared retrieval",
                "service": "confluence",
                "site_id": wiki["site_id"],
                "structural_scope": "url:confluence:TEAM",
                "attention": "all",
            },
        )["items"]
        self.assertEqual(
            [item["id"] for item in wiki_only],
            [wiki["external_resource_id"]],
        )
        jira_space = browse_inventory(
            self.connection,
            {
                "q": "shared retrieval",
                "service": "jira",
                "space_id": space_id,
                "attention": "all",
            },
        )["items"]
        self.assertEqual(
            [item["id"] for item in jira_space],
            [self.reference["external_resource_id"]],
        )
        with self.assertRaisesRegex(
            AtlassianBrowseError,
            "space_id and structural_scope cannot be combined",
        ):
            browse_inventory(
                self.connection,
                {
                    "space_id": space_id,
                    "structural_scope": "unclassified",
                },
            )
        with self.assertRaisesRegex(
            AtlassianBrowseError,
            "structural_scope requires site_id",
        ):
            browse_inventory(
                self.connection,
                {
                    "service": "confluence",
                    "structural_scope": "unclassified",
                },
            )

    def test_explorer_hierarchy_uses_same_eligible_population_as_list(self):
        wiki_source = self._source(
            "confluence-explorer", "confluence", "Explorer Wiki"
        )
        wiki = self._item(
            wiki_source,
            "https://wiki.explorer.test/spaces/TEAM/pages/44/Guide",
            "Explorer guide",
            "reference",
        )
        jira_site_id = int(
            self.connection.execute(
                """
                SELECT site_id FROM atlassian_items
                WHERE external_resource_id = ?
                """,
                (self.reference["external_resource_id"],),
            ).fetchone()["site_id"]
        )
        jira_space_id = int(
            self.connection.execute(
                """
                INSERT INTO atlassian_spaces(
                    site_id, source_instance_id, service, remote_id,
                    space_key, name, canonical_url, coverage
                ) VALUES (?, ?, 'jira', 'explorer-space', 'EXP',
                          'Explorer Project',
                          'https://jira.primary.test/projects/EXP',
                          'selected-content')
                """,
                (jira_site_id, self.jira_source),
            ).lastrowid
        )
        self.connection.execute(
            """
            UPDATE atlassian_items SET space_id = ?
            WHERE external_resource_id = ?
            """,
            (jira_space_id, self.reference["external_resource_id"]),
        )
        update_atlassian_local_state(
            self.connection,
            self.metadata["external_resource_id"],
            note="",
            attention="archived",
        )

        combined = browse_inventory(self.connection)
        self.assertEqual(combined["eligible_count"], 3)
        self.assertEqual(combined["hierarchy"]["eligible_count"], 3)
        primary_site = next(
            site
            for site in combined["hierarchy"]["sites"]
            if site["id"] == jira_site_id
        )
        self.assertEqual(primary_site["count"], 2)
        self.assertEqual(primary_site["name"], "jira.primary.test")
        self.assertEqual(
            {
                (container["kind"], container["name"]): container["count"]
                for container in primary_site["containers"]
            },
            {("space", "Explorer Project"): 1, ("url", "IDX"): 1},
        )

        selected_space = browse_inventory(
            self.connection,
            {"service": "jira", "site_id": jira_site_id, "space_id": jira_space_id},
        )
        self.assertEqual(selected_space["matching_count"], 1)
        self.assertEqual(
            selected_space["matching_count"],
            next(
                container["count"]
                for container in selected_space["hierarchy"]["sites"][0][
                    "containers"
                ]
                if container["id"] == jira_space_id
            ),
        )
        selected_url_container = browse_inventory(
            self.connection,
            {
                "service": "jira",
                "site_id": jira_site_id,
                "structural_scope": "url:jira:IDX",
            },
        )
        self.assertEqual(selected_url_container["matching_count"], 1)
        self.assertEqual(
            selected_url_container["matching_count"],
            next(
                container["count"]
                for container in selected_url_container["hierarchy"]["sites"][0][
                    "containers"
                ]
                if container["structural_scope"] == "url:jira:IDX"
            ),
        )
        self.assertEqual(
            [item["id"] for item in selected_url_container["items"]],
            [self.indexed["external_resource_id"]],
        )

        filtered = browse_inventory(
            self.connection, {"coverage": "reference"}
        )
        self.assertEqual(filtered["eligible_count"], 2)
        self.assertEqual(filtered["active_filter_count"], 1)
        self.assertTrue(filtered["has_advanced_filters"])
        self.assertEqual(
            {item["id"] for item in filtered["items"]},
            {
                self.reference["external_resource_id"],
                wiki["external_resource_id"],
            },
        )

    def test_url_container_precedence_unknown_and_all_child_state_are_canonical(self):
        wiki_source = self._source(
            "confluence-containers", "confluence", "Container Wiki"
        )
        persisted = self._item(
            wiki_source,
            "https://containers.test/wiki/spaces/PAYMENTS/pages/1/Guide",
            "Persisted container guide",
            "reference",
        )
        hinted = self._item(
            wiki_source,
            "https://containers.test/wiki/spaces/CHECKOUT/pages/2/Guide",
            "URL container guide",
            "reference",
        )
        unknown = self._item(
            wiki_source,
            "https://containers.test/wiki/pages/3/Guide",
            "Unknown container guide",
            "reference",
        )
        site_id = int(persisted["site_id"])
        space = register_atlassian_space(
            self.connection,
            site_id=site_id,
            source_instance_id=wiki_source,
            service="confluence",
            name="Persisted Space",
            space_key="PAYMENTS",
            canonical_url="https://containers.test/wiki/spaces/PAYMENTS",
        )
        self.connection.execute(
            """
            UPDATE atlassian_items SET space_id = ?
            WHERE external_resource_id = ?
            """,
            (space["id"], persisted["external_resource_id"]),
        )

        inventory = browse_inventory(
            self.connection,
            {"site_id": site_id, "attention": "all"},
        )

        by_id = {item["id"]: item for item in inventory["items"]}
        self.assertEqual(
            (
                by_id[persisted["external_resource_id"]]["container_kind"],
                by_id[persisted["external_resource_id"]]["container_label"],
                by_id[persisted["external_resource_id"]][
                    "container_structural_scope"
                ],
            ),
            ("space", "Persisted Space", None),
        )
        self.assertEqual(
            (
                by_id[hinted["external_resource_id"]]["container_kind"],
                by_id[hinted["external_resource_id"]]["container_label"],
                by_id[hinted["external_resource_id"]][
                    "container_structural_scope"
                ],
            ),
            ("url", "CHECKOUT", "url:confluence:CHECKOUT"),
        )
        self.assertEqual(
            (
                by_id[unknown["external_resource_id"]]["container_kind"],
                by_id[unknown["external_resource_id"]]["container_label"],
                by_id[unknown["external_resource_id"]][
                    "container_structural_scope"
                ],
            ),
            ("unclassified", "소속 미확인", "unclassified"),
        )
        global_result = next(
            result
            for result in search(
                self.connection,
                "URL container guide",
                source_scope="all",
                atlassian_filters={"site_id": site_id},
            )
            if result["entity_id"]
            == str(hinted["external_resource_id"])
        )
        self.assertEqual(
            (
                global_result["container_kind"],
                global_result["container_label"],
                global_result["container_service"],
            ),
            ("url", "CHECKOUT", "confluence"),
        )
        containers = inventory["hierarchy"]["sites"][0]["containers"]
        self.assertEqual(containers[-1]["kind"], "unclassified")
        self.assertEqual(
            {container["count"] for container in containers}, {1}
        )

        all_child = browse_inventory(
            self.connection,
            {
                "site_id": site_id,
                "structural_scope": "url:confluence:CHECKOUT",
                "attention": "all",
            },
        )
        self.assertIsNone(all_child["filters"]["service"])
        self.assertEqual(
            [item["id"] for item in all_child["items"]],
            [hinted["external_resource_id"]],
        )
        empty_projection = browse_inventory(
            self.connection,
            {
                "q": "does not match",
                "site_id": site_id,
                "structural_scope": "url:confluence:CHECKOUT",
                "attention": "all",
            },
        )
        self.assertEqual(empty_projection["matching_count"], 0)
        selected = next(
            container
            for container in empty_projection["hierarchy"]["sites"][0][
                "containers"
            ]
            if container["structural_scope"]
            == "url:confluence:CHECKOUT"
        )
        self.assertEqual(selected["count"], 0)
        self.assertTrue(
            empty_projection["active_structure"]["empty_selected_structure"]
        )
        with self.assertRaisesRegex(
            AtlassianBrowseError,
            "URL container is unavailable for the selected service",
        ):
            browse_inventory(
                self.connection,
                {
                    "service": "jira",
                    "site_id": site_id,
                    "structural_scope": "url:confluence:CHECKOUT",
                },
            )
        with self.assertRaisesRegex(
            AtlassianBrowseError,
            "Structural scope is unavailable for the selected Site",
        ):
            browse_inventory(
                self.connection,
                {
                    "site_id": site_id,
                    "structural_scope": "url:confluence:FORGED",
                },
            )
        self.connection.commit()
        with self.assertRaises(HTTPException) as forged_partial:
            self._page(
                view="all",
                site_id=site_id,
                structural_scope="url:confluence:FORGED",
                item=str(hinted["external_resource_id"]),
                _headers={
                    "X-LocalBrain-Partial": "atlassian-item-preview"
                },
            )
        self.assertEqual(forged_partial.exception.status_code, 400)

        page = html.unescape(
            self._page(
                view="all",
                site_id=site_id,
                structural_scope="url:confluence:CHECKOUT",
            ).body.decode("utf-8")
        )
        self.assertIn(
            "/atlassian?view=all&site_id={}&structural_scope=url%3Aconfluence%3ACHECKOUT".format(
                site_id
            ),
            page,
        )
        with self.assertRaises(HTTPException) as repeated:
            self._page(
                view="all",
                site_id=site_id,
                structural_scope="url:confluence:CHECKOUT",
                _query_string=(
                    "view=all&site_id={}&structural_scope="
                    "url%3Aconfluence%3ACHECKOUT&structural_scope=unclassified"
                ).format(site_id),
            )
        self.assertEqual(repeated.exception.status_code, 400)

    def test_only_canonical_url_owns_container_grouping(self):
        item = self._item(
            self.jira_source,
            "https://jira.primary.test/secure/Generic.jspa?id=42",
            "Canonical grouping owner",
            "reference",
        )
        external_resource_id = int(item["external_resource_id"])
        site_id = int(item["site_id"])
        alias_url = "https://jira.primary.test/browse/ALIAS-42"
        self.connection.execute(
            """
            INSERT INTO atlassian_item_urls(
                external_resource_id, site_id, url_role, observed_url,
                normalized_url, first_observed_at, last_observed_at
            ) VALUES (?, ?, 'alias', ?, ?, ?, ?)
            """,
            (
                external_resource_id,
                site_id,
                alias_url,
                alias_url,
                "2026-09-01T00:00:00Z",
                "2026-09-01T00:00:00Z",
            ),
        )
        source_id = int(
            self.connection.execute(
                """
                INSERT INTO sources(kind, name, root_path)
                VALUES ('codex', 'Canonical owner source',
                        '/synthetic/canonical-owner')
                """
            ).lastrowid
        )
        session_id = int(
            self.connection.execute(
                """
                INSERT INTO sessions(
                    source_id, external_id, source_path, title,
                    session_class, session_role, index_policy
                ) VALUES (?, 'canonical-owner',
                          '/synthetic/canonical-owner/session.jsonl',
                          'Canonical owner session', 'work', 'primary',
                          'full')
                """,
                (source_id,),
            ).lastrowid
        )
        evidence_url = "https://jira.primary.test/browse/EVIDENCE-42"
        self.connection.execute(
            """
            INSERT INTO atlassian_item_evidence(
                external_resource_id, session_id, source_path,
                source_channel, source_event_id, source_line, url_ordinal,
                observed_url, normalized_url, extractor_version,
                evidence_key, first_observed_at, last_observed_at
            ) VALUES (?, ?, '/synthetic/canonical-owner/session.jsonl',
                      'visible_text', 'event-1', 1, 1, ?, ?,
                      'synthetic-v1', ?, ?, ?)
            """,
            (
                external_resource_id,
                session_id,
                evidence_url,
                evidence_url,
                "c" * 64,
                "2026-09-01T00:00:00Z",
                "2026-09-01T00:00:00Z",
            ),
        )

        inventory = browse_inventory(
            self.connection,
            {"site_id": site_id, "attention": "all"},
        )

        projected = next(
            row
            for row in inventory["items"]
            if row["id"] == external_resource_id
        )
        self.assertEqual(
            (
                projected["container_kind"],
                projected["container_label"],
                projected["container_structural_scope"],
            ),
            ("unclassified", "소속 미확인", "unclassified"),
        )
        structural_scopes = {
            container["structural_scope"]
            for container in inventory["hierarchy"]["sites"][0][
                "containers"
            ]
        }
        self.assertNotIn("url:jira:ALIAS", structural_scopes)
        self.assertNotIn("url:jira:EVIDENCE", structural_scopes)

    def test_exact_browse_bounds_query_excerpt_and_performs_no_write(self):
        long_note = "prefix " * 60 + "bounded phrase" + " suffix" * 60
        update_atlassian_local_state(
            self.connection,
            self.reference["external_resource_id"],
            note=long_note,
            attention="normal",
        )
        before = self.connection.total_changes
        result = browse_inventory(
            self.connection, {"q": "bounded phrase", "attention": "all"}
        )
        self.assertEqual(self.connection.total_changes, before)
        self.assertLessEqual(
            len(result["items"][0]["exact_match"]["excerpt"]), 240
        )
        with self.assertRaisesRegex(
            AtlassianBrowseError, "Query has no searchable words"
        ):
            browse_inventory(self.connection, {"q": "---"})
        with self.assertRaisesRegex(
            AtlassianBrowseError, "Query supports at most 12 words"
        ):
            browse_inventory(
                self.connection,
                {"q": " ".join("word{}".format(i) for i in range(13))},
            )

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
        bind_atlassian_remote_identity(
            self.connection,
            self.reference["external_resource_id"],
            remote_id="primary-1",
            remote_key="SAME-1",
            confirmed_at="2026-08-29T00:00:00Z",
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
        self.assertEqual(
            (
                detail["container_kind"],
                detail["container_label"],
                detail["container_service"],
                detail["container_structural_scope"],
            ),
            ("url", "IDX", "jira", "url:jira:IDX"),
        )
        self.assertEqual(detail["evidence"][0]["session_id"], session_id)
        self.assertEqual(
            detail["memberships"][0]["workstream_id"], workstream_id
        )
        self.assertEqual(detail["latest_refresh_run"]["id"], run_id)
        self.assertNotIn("source_snapshot_json", detail["latest_refresh_run"])

    def test_explorer_route_defaults_to_all_and_owns_one_local_query(self):
        wiki_source = self._source(
            "confluence-route", "confluence", "Route Wiki"
        )
        wiki = self._item(
            wiki_source,
            "https://wiki.route.test/spaces/TEAM/pages/77/Route-Guide",
            "Route Wiki guide",
            "reference",
        )
        with patch(
            "localbrain.main.registration_inventory",
            side_effect=AssertionError("Browse must not load setup inventory"),
        ), patch(
            "localbrain.main.registration_sites",
            side_effect=AssertionError("Browse must not load setup sites"),
        ), patch(
            "localbrain.main.registered_scope_overview",
            side_effect=AssertionError("Browse must not load setup scopes"),
        ):
            response = self._page()
        rendered = response.body.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="selected" href="/atlassian?view=all"', rendered)
        self.assertIn("Primary local title", rendered)
        self.assertIn("Route Wiki guide", rendered)
        self.assertIn(
            'id="atlassian-item-{}"'.format(wiki["external_resource_id"]),
            rendered,
        )
        self.assertEqual(rendered.count('type="search"'), 1)
        self.assertNotIn('id="global-query"', rendered)
        self.assertIn('class="global-search-reserve"', rendered)
        self.assertIn('class="atlassian-filter-disclosure"', rendered)
        for retained in (
            "coverage",
            "freshness",
            "attention",
            "topic_id",
            "tag_id",
            "workstream_id",
        ):
            self.assertIn('select name="{}"'.format(retained), rendered)
        for removed in (
            "source_instance_id",
            "site_id",
            "space_id",
            "item_type",
        ):
            self.assertNotIn('select name="{}"'.format(removed), rendered)

        wiki_only = self._page(view="wiki").body.decode("utf-8")
        self.assertIn("Route Wiki guide", wiki_only)
        self.assertNotIn("Primary local title", wiki_only)
        invalid = self._page(view="unsupported").body.decode("utf-8")
        self.assertIn('class="selected" href="/atlassian?view=all"', invalid)

    def test_selected_item_full_page_and_partial_share_one_preview_contract(self):
        item_id = self.reference["external_resource_id"]
        selected = self._page(view="jira", item=str(item_id))
        rendered = html.unescape(selected.body.decode("utf-8"))

        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.headers["vary"], "X-LocalBrain-Partial")
        self.assertIn('data-preview-state="selected"', rendered)
        self.assertIn('data-selected-id="{}"'.format(item_id), rendered)
        self.assertIn(
            'data-atlassian-item-id="{}" aria-current="true"'.format(
                item_id
            ),
            rendered,
        )
        self.assertIn(
            'data-atlassian-selection-url="/atlassian?view=jira&item={}"'.format(
                item_id
            ),
            rendered,
        )
        self.assertIn("REMOTE FACTS · LAST KNOWN", rendered)
        self.assertIn("Canonical URL", rendered)
        self.assertIn(
            "https://jira.primary.test/browse/SAME-1",
            rendered,
        )
        self.assertIn("LOCAL ONLY", rendered)
        self.assertIn("FOUND IN · LOCAL EVIDENCE", rendered)
        self.assertIn("REFRESH HISTORY", rendered)
        self.assertNotIn('name="note"', rendered)

        with patch(
            "localbrain.main.browse_inventory",
            side_effect=AssertionError("partial must not load broad inventory"),
        ):
            partial = self._page(
                view="jira",
                item=str(item_id),
                _headers={"X-LocalBrain-Partial": "atlassian-item-preview"},
            )
        partial_html = html.unescape(partial.body.decode("utf-8"))
        self.assertEqual(partial.status_code, 200)
        self.assertIn('data-preview-state="selected"', partial_html)
        self.assertNotIn("atlassian-explorer-layout", partial_html)
        self.assertNotIn("Find an Atlassian item", partial_html)

        out_of_scope = self._page(
            view="wiki",
            item=str(item_id),
            _headers={"X-LocalBrain-Partial": "atlassian-item-preview"},
        ).body.decode("utf-8")
        self.assertIn('data-preview-state="out_of_scope"', out_of_scope)
        self.assertIn("OUTSIDE CURRENT VIEW", out_of_scope)
        missing = self._page(
            view="jira",
            item="9223372036854775807",
            _headers={"X-LocalBrain-Partial": "atlassian-item-preview"},
        ).body.decode("utf-8")
        self.assertIn('data-preview-state="missing"', missing)

    def test_selected_urls_preserve_supported_diagnostic_filters(self):
        item_id = self.reference["external_resource_id"]
        selected = self._page(
            view="jira",
            source_instance_id=self.jira_source,
            item_type="jira_issue",
            item=str(item_id),
        )
        rendered = html.unescape(selected.body.decode("utf-8"))
        selected_url = (
            "/atlassian?view=jira&source_instance_id={}&item_type=jira_issue&item={}"
        ).format(self.jira_source, item_id)
        clear_url = (
            "/atlassian?view=jira&source_instance_id={}&item_type=jira_issue"
        ).format(self.jira_source)
        self.assertIn(
            'data-atlassian-selection-url="{}"'.format(selected_url),
            rendered,
        )
        self.assertIn('href="{}"'.format(clear_url), rendered)

        partial = self._page(
            view="jira",
            source_instance_id=self.jira_source,
            item_type="jira_issue",
            item=str(item_id),
            _headers={"X-LocalBrain-Partial": "atlassian-item-preview"},
        )
        self.assertIn(
            'data-preview-state="selected"', partial.body.decode("utf-8")
        )
        out_of_scope = self._page(
            view="jira",
            source_instance_id=self.jira_source,
            item_type="confluence_page",
            item=str(item_id),
            _headers={"X-LocalBrain-Partial": "atlassian-item-preview"},
        )
        self.assertIn(
            'data-preview-state="out_of_scope"',
            out_of_scope.body.decode("utf-8"),
        )

    def test_preview_clear_and_invalid_selection_keep_server_fallbacks(self):
        with patch(
            "localbrain.main.browse_inventory",
            side_effect=AssertionError("clear partial must not load inventory"),
        ), patch(
            "localbrain.main.atlassian_item_preview",
            side_effect=AssertionError("clear partial must not read an Item"),
        ):
            cleared = self._page(
                view="jira",
                _headers={"X-LocalBrain-Partial": "atlassian-item-preview"},
            )
        cleared_html = cleared.body.decode("utf-8")
        self.assertIn('data-preview-state="empty"', cleared_html)
        self.assertIn("링크, 문서 또는 구조 참조를 선택하세요", cleared_html)

        for invalid in ("0", "-1", "1.5", "９", "9" * 20):
            with self.subTest(item=invalid), self.assertRaises(HTTPException) as raised:
                self._page(view="jira", item=invalid)
            self.assertEqual(raised.exception.status_code, 400)
        legacy = self._page(view="jira", mode="setup", item="1")
        self.assertEqual(legacy.status_code, 303)
        self.assertTrue(
            legacy.headers["location"].startswith(
                "/atlassian/add?return_to="
            )
        )

    def test_explicit_space_injects_only_current_zero_projection_branch(self):
        site_id = int(self.reference["site_id"])
        space = register_atlassian_space(
            self.connection,
            site_id=site_id,
            source_instance_id=self.jira_source,
            service="jira",
            name="Selected Empty Project",
            space_key="EMPTY",
            canonical_url="https://jira.primary.test/projects/EMPTY",
        )
        filters = {
            "service": "jira",
            "site_id": site_id,
            "space_id": space["id"],
        }
        physical_empty = browse_inventory(self.connection, filters)
        site = next(
            value
            for value in physical_empty["hierarchy"]["sites"]
            if value["id"] == site_id
        )
        selected = next(
            value
            for value in site["containers"]
            if value["id"] == space["id"]
        )
        self.assertEqual(selected["count"], 0)
        self.assertEqual(physical_empty["matching_count"], 0)
        self.assertTrue(
            physical_empty["active_structure"]["empty_registered_space"]
        )
        self.assertIn(
            "Selected Empty Project",
            physical_empty["active_structure"]["label"],
        )

        root = browse_inventory(self.connection, {"service": "jira"})
        root_space_ids = {
            value["id"]
            for owner in root["hierarchy"]["sites"]
            for value in owner["containers"]
            if value["kind"] == "space"
        }
        self.assertNotIn(space["id"], root_space_ids)

        bind_atlassian_remote_identity(
            self.connection,
            self.reference["external_resource_id"],
            remote_id="selected-empty-1",
            remote_key="SAME-1",
            space_id=space["id"],
        )
        update_atlassian_local_state(
            self.connection,
            self.reference["external_resource_id"],
            note="",
            attention="archived",
        )
        archived_only = browse_inventory(self.connection, filters)
        self.assertEqual(archived_only["matching_count"], 0)
        self.assertTrue(
            archived_only["active_structure"]["empty_registered_space"]
        )
        included = browse_inventory(
            self.connection, {**filters, "attention": "archived"}
        )
        self.assertEqual(included["matching_count"], 1)
        self.assertFalse(
            included["active_structure"].get("empty_registered_space", False)
        )
        filtered = browse_inventory(
            self.connection,
            {**filters, "attention": "all", "q": "does not match"},
        )
        self.assertEqual(filtered["matching_count"], 0)
        self.assertTrue(
            filtered["active_structure"]["empty_registered_space"]
        )

        rendered = self._page(
            view="jira", site_id=site_id, space_id=space["id"]
        ).body.decode("utf-8")
        self.assertIn("data-atlassian-selected-zero-space", rendered)
        self.assertIn("remote 링크를 자동으로 발견하거나 동기화하지 않습니다", rendered)

    def test_all_hierarchy_uses_one_domain_branch_for_a_shared_site(self):
        shared_site_id = int(
            self.connection.execute(
                """
                SELECT site_id FROM atlassian_items
                WHERE external_resource_id = ?
                """,
                (self.reference["external_resource_id"],),
            ).fetchone()["site_id"]
        )
        wiki_source = self._source(
            "confluence-shared-site", "confluence", "Shared Site Wiki"
        )
        wiki = self._item(
            wiki_source,
            "https://jira.primary.test/spaces/TEAM/pages/77/Shared-Guide",
            "Shared Site guide",
            "reference",
        )
        self.assertEqual(wiki["site_id"], shared_site_id)

        combined = browse_inventory(self.connection)
        nodes = [
            site
            for site in combined["hierarchy"]["sites"]
            if site["id"] == shared_site_id
        ]
        self.assertEqual(len(nodes), 1)
        shared_node = nodes[0]
        self.assertEqual(shared_node["name"], "jira.primary.test")
        self.assertEqual(shared_node["count"], 3)
        self.assertEqual(
            {container["service"] for container in shared_node["containers"]},
            {"jira", "confluence"},
        )
        self.assertEqual(
            browse_inventory(
                self.connection,
                {"service": "jira", "site_id": shared_site_id},
            )["matching_count"],
            2,
        )
        self.assertEqual(
            browse_inventory(
                self.connection,
                {"service": "confluence", "site_id": shared_site_id},
            )["matching_count"],
            1,
        )

        rendered = html.unescape(self._page().body.decode("utf-8"))
        self.assertIn(
            "/atlassian?view=all&site_id={}".format(shared_site_id),
            rendered,
        )
        self.assertNotIn(
            "/atlassian?view=jira&site_id={}".format(shared_site_id),
            rendered,
        )
        self.assertNotIn(
            "/atlassian?view=wiki&site_id={}".format(shared_site_id),
            rendered,
        )
        combined_site = browse_inventory(
            self.connection, {"site_id": shared_site_id}
        )
        self.assertEqual(combined_site["matching_count"], 3)
        global_site_search = atlassian_search_results(
            self.connection,
            "Shared Site guide",
            {"site_id": shared_site_id},
        )
        self.assertEqual(
            [result["entity_id"] for result in global_site_search],
            [str(wiki["external_resource_id"])],
        )
        combined_route = self._page(site_id=shared_site_id)
        self.assertEqual(combined_route.status_code, 200)

    def test_structure_rejects_a_different_service_without_breaking_search(self):
        wiki_source = self._source(
            "confluence-only-scope", "confluence", "Wiki-only scope"
        )
        wiki = self._item(
            wiki_source,
            "https://wiki-only.test/spaces/ONLY/pages/91/Wiki-Only-Guide",
            "Wiki-only guide",
            "reference",
        )
        wiki_space = register_atlassian_space(
            self.connection,
            site_id=wiki["site_id"],
            source_instance_id=wiki_source,
            service="confluence",
            name="Wiki-only Space",
            remote_id="wiki-only-space",
            space_key="ONLY",
            canonical_url="https://wiki-only.test/spaces/ONLY/overview",
            coverage="selected-content",
        )
        self.connection.execute(
            """
            UPDATE atlassian_items SET space_id = ?
            WHERE external_resource_id = ?
            """,
            (wiki_space["id"], wiki["external_resource_id"]),
        )

        search_results = atlassian_search_results(
            self.connection,
            "Wiki-only guide",
            {"space_id": wiki_space["id"]},
        )
        self.assertEqual(
            [result["entity_id"] for result in search_results],
            [str(wiki["external_resource_id"])],
        )
        for values, message in (
            (
                {"service": "jira", "site_id": wiki["site_id"]},
                "Site is unavailable for the selected service",
            ),
            (
                {"service": "jira", "space_id": wiki_space["id"]},
                "Space is unavailable for the selected service",
            ),
        ):
            with self.subTest(values=values), self.assertRaisesRegex(
                AtlassianBrowseError, message
            ):
                browse_inventory(self.connection, values)
        valid = browse_inventory(
            self.connection,
            {
                "service": "confluence",
                "space_id": wiki_space["id"],
            },
        )
        self.assertEqual(valid["matching_count"], 1)
        self.assertEqual(valid["active_structure"]["kind"], "space")
        with self.assertRaises(HTTPException) as invalid_route:
            self._page(view="jira", site_id=wiki["site_id"])
        self.assertEqual(invalid_route.exception.status_code, 400)

    def test_site_service_owner_includes_a_persisted_empty_space(self):
        wiki_source = self._source(
            "confluence-empty-scope", "confluence", "Empty Wiki scope"
        )
        wiki_site = register_atlassian_site(
            self.connection,
            source_instance_id=wiki_source,
            base_url="https://wiki-empty.test",
        )
        wiki_space = register_atlassian_space(
            self.connection,
            site_id=wiki_site["id"],
            source_instance_id=wiki_source,
            service="confluence",
            name="Empty Wiki Space",
            remote_id="empty-wiki-space",
            space_key="EMPTY",
            canonical_url="https://wiki-empty.test/spaces/EMPTY/overview",
            coverage="selected-content",
        )
        with self.assertRaisesRegex(
            AtlassianBrowseError,
            "Site is unavailable for the selected service",
        ):
            browse_inventory(
                self.connection,
                {"service": "jira", "site_id": wiki_site["id"]},
            )
        valid = browse_inventory(
            self.connection,
            {"service": "confluence", "space_id": wiki_space["id"]},
        )
        self.assertEqual(valid["matching_count"], 0)
        self.assertEqual(valid["active_structure"]["kind"], "space")

    def test_explorer_urls_preserve_state_and_detail_return_is_local(self):
        site_id = int(
            self.connection.execute(
                """
                SELECT site_id FROM atlassian_items
                WHERE external_resource_id = ?
                """,
                (self.reference["external_resource_id"],),
            ).fetchone()["site_id"]
        )
        space_id = int(
            self.connection.execute(
                """
                INSERT INTO atlassian_spaces(
                    site_id, source_instance_id, service, remote_id,
                    space_key, name, canonical_url, coverage
                ) VALUES (?, ?, 'jira', 'route-space', 'ROUTE',
                          'Route Project',
                          'https://jira.primary.test/projects/ROUTE',
                          'selected-content')
                """,
                (site_id, self.jira_source),
            ).lastrowid
        )
        self.connection.execute(
            """
            UPDATE atlassian_items SET space_id = ?
            WHERE external_resource_id = ?
            """,
            (space_id, self.reference["external_resource_id"]),
        )
        response = self._page(
            view="jira",
            q="Primary local title",
            site_id=site_id,
            space_id=space_id,
            coverage="reference",
        )
        rendered = html.unescape(response.body.decode("utf-8"))
        self.assertIn(
            "/atlassian?view=jira&q=Primary+local+title&coverage=reference",
            rendered,
        )
        row_match = re.search(
            r'id="atlassian-item-{}" href="([^"]+)"'.format(
                self.reference["external_resource_id"]
            ),
            rendered,
        )
        self.assertIsNotNone(row_match)
        detail_url = html.unescape(row_match.group(1))
        detail_query = parse_qs(urlsplit(detail_url).query)
        self.assertEqual(
            detail_query["return_to"],
            [
                "/atlassian?view=jira&q=Primary+local+title&site_id={}&space_id={}&coverage=reference&item={}".format(
                    site_id,
                    space_id,
                    self.reference["external_resource_id"],
                )
            ],
        )

        with patch("localbrain.main.connect", return_value=self.connection):
            detail = atlassian_item_page(
                self._request(
                    path="/atlassian/items/{}".format(
                        self.reference["external_resource_id"]
                    )
                ),
                self.reference["external_resource_id"],
                notice=None,
                return_to=detail_query["return_to"][0],
            )
            unsafe = atlassian_item_page(
                self._request(
                    path="/atlassian/items/{}".format(
                        self.reference["external_resource_id"]
                    )
                ),
                self.reference["external_resource_id"],
                notice=None,
                return_to="https://outside.invalid/atlassian",
            )
            canonical_space_return = atlassian_item_page(
                self._request(
                    path="/atlassian/items/{}".format(
                        self.reference["external_resource_id"]
                    )
                ),
                self.reference["external_resource_id"],
                notice=None,
                return_to="/atlassian?view=jira&space_id={}&item={}".format(
                    space_id,
                    self.reference["external_resource_id"],
                ),
            )
            wrong_service_return = atlassian_item_page(
                self._request(
                    path="/atlassian/items/{}".format(
                        self.reference["external_resource_id"]
                    )
                ),
                self.reference["external_resource_id"],
                notice=None,
                return_to="/atlassian?view=wiki&site_id={}&item={}".format(
                    site_id,
                    self.reference["external_resource_id"],
                ),
            )
            all_site_return = atlassian_item_page(
                self._request(
                    path="/atlassian/items/{}".format(
                        self.reference["external_resource_id"]
                    )
                ),
                self.reference["external_resource_id"],
                notice=None,
                return_to="/atlassian?view=all&site_id={}".format(site_id),
            )
            all_space_return = atlassian_item_page(
                self._request(
                    path="/atlassian/items/{}".format(
                        self.reference["external_resource_id"]
                    )
                ),
                self.reference["external_resource_id"],
                notice=None,
                return_to="/atlassian?view=all&space_id={}".format(space_id),
            )
            invalid_structure_returns = [
                atlassian_item_page(
                    self._request(
                        path="/atlassian/items/{}".format(
                            self.reference["external_resource_id"]
                        )
                    ),
                    self.reference["external_resource_id"],
                    notice=None,
                    return_to=return_to,
                )
                for return_to in (
                    "/atlassian?view=all&site_id={}&structural_scope=unclassified".format(
                        site_id
                    ),
                    "/atlassian?view=all&site_id={}&structural_scope=url:jira:SAME&structural_scope=unclassified".format(
                        site_id
                    ),
                    "/atlassian?view=jira&site_id={}".format("9" * 100),
                )
            ]
        detail_html = html.unescape(detail.body.decode("utf-8"))
        self.assertIn(
            'href="{}"'.format(detail_query["return_to"][0]), detail_html
        )
        self.assertIn(
            'class="context-back-link" href="/atlassian"',
            unsafe.body.decode("utf-8"),
        )
        self.assertIn(
            'class="context-back-link" href="/atlassian?view=jira&amp;site_id={}&amp;space_id={}&amp;item={}"'.format(
                site_id,
                space_id,
                self.reference["external_resource_id"],
            ),
            canonical_space_return.body.decode("utf-8"),
        )
        self.assertIn(
            'class="context-back-link" href="/atlassian?view=all&amp;site_id={}"'.format(
                site_id
            ),
            all_site_return.body.decode("utf-8"),
        )
        self.assertIn(
            'class="context-back-link" href="/atlassian?view=all&amp;site_id={}&amp;space_id={}"'.format(
                site_id, space_id
            ),
            all_space_return.body.decode("utf-8"),
        )
        self.assertIn(
            'class="context-back-link" href="/atlassian"',
            wrong_service_return.body.decode("utf-8"),
        )
        for invalid_structure_return in invalid_structure_returns:
            self.assertIn(
                'class="context-back-link" href="/atlassian"',
                invalid_structure_return.body.decode("utf-8"),
            )

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
        self.assertIn("LOCAL EXACT SEARCH", browse.body.decode("utf-8"))
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

    def test_local_edit_validation_preserves_selected_explorer_return(self):
        item_id = self.reference["external_resource_id"]
        return_to = "/atlassian?view=jira&item={}".format(item_id)
        encoded_return = quote_plus(return_to)
        with patch(
            "localbrain.main.transaction",
            side_effect=lambda: self._transaction(),
        ), patch("localbrain.main.connect", return_value=self.connection):
            invalid_topic = asyncio.run(
                atlassian_update_local(
                    self._request(
                        "POST",
                        "/atlassian/items/{}/local".format(item_id),
                        "topic_id=invalid&return_to={}".format(encoded_return),
                    ),
                    item_id,
                )
            )
            invalid_link = asyncio.run(
                atlassian_add_local_link(
                    self._request(
                        "POST",
                        "/atlassian/items/{}/links".format(item_id),
                        "target=invalid&return_to={}".format(encoded_return),
                    ),
                    item_id,
                )
            )

        expected_back = (
            'class="context-back-link" '
            'href="/atlassian?view=jira&amp;item={}"'.format(item_id)
        )
        self.assertEqual(invalid_topic.status_code, 422)
        self.assertIn(expected_back, invalid_topic.body.decode("utf-8"))
        self.assertEqual(invalid_link.status_code, 422)
        self.assertIn(expected_back, invalid_link.body.decode("utf-8"))

    def test_reference_only_group_has_split_counts_and_survives_direct_reload(self):
        reference_id, site_id, _document_id = self._structure_reference(
            "https://jira.structure-only.test/secure/RapidBoard.jspa?"
            "rapidView=37746&projectKey=JPDI"
        )
        inventory = browse_inventory(
            self.connection,
            {
                "site_id": site_id,
                "structural_scope": "url:jira:JPDI",
            },
        )

        self.assertEqual(inventory["eligible_item_count"], 3)
        self.assertEqual(inventory["eligible_reference_count"], 1)
        self.assertEqual(inventory["matching_item_count"], 0)
        self.assertEqual(inventory["matching_reference_count"], 1)
        self.assertEqual(
            [entry["stable_key"] for entry in inventory["entries"]],
            ["reference:{}".format(reference_id)],
        )
        site = next(
            value
            for value in inventory["hierarchy"]["sites"]
            if value["id"] == site_id
        )
        self.assertEqual(
            (site["item_count"], site["reference_count"], site["count"]),
            (0, 1, 1),
        )
        child = site["containers"][0]
        self.assertEqual(child["structural_scope"], "url:jira:JPDI")
        self.assertEqual(
            (child["item_count"], child["reference_count"], child["count"]),
            (0, 1, 1),
        )

        response = self._page(
            site_id=site_id,
            structural_scope="url:jira:JPDI",
            reference=str(reference_id),
        )
        rendered = response.body.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn('data-selection-kind="reference"', rendered)
        self.assertIn(
            'data-selected-key="reference:{}"'.format(reference_id),
            rendered,
        )
        self.assertIn("Jira 보드 참조", rendered)

    def test_reference_selection_states_partial_direct_and_strict_state(self):
        reference_id, site_id, document_id = self._structure_reference(
            "https://jira.primary.test/secure/RapidBoard.jspa?"
            "rapidView=37746&projectKey=JPDI"
        )
        partial = self._page(
            site_id=site_id,
            structural_scope="url:jira:JPDI",
            reference=str(reference_id),
            _headers={
                "X-LocalBrain-Partial": "atlassian-selection-preview"
            },
        )
        self.assertEqual(partial.status_code, 200)
        self.assertIn(
            'data-preview-state="selected"',
            partial.body.decode("utf-8"),
        )

        out_of_scope = self._page(
            reference=str(reference_id), coverage="indexed"
        )
        self.assertIn(
            'data-preview-state="out_of_scope"',
            out_of_scope.body.decode("utf-8"),
        )
        missing = self._page(reference="999999")
        self.assertIn(
            'data-preview-state="missing"',
            missing.body.decode("utf-8"),
        )

        with patch("localbrain.main.connect", return_value=self.connection):
            direct = atlassian_reference_page(
                self._request(
                    path="/atlassian/references/{}".format(reference_id)
                ),
                reference_id,
                return_to=(
                    "/atlassian?view=jira&site_id={}&"
                    "structural_scope=url%3Ajira%3AJPDI&reference={}"
                ).format(site_id, reference_id),
            )
        self.assertEqual(direct.status_code, 200)
        self.assertIn("LOCAL STRUCTURE ONLY", direct.body.decode("utf-8"))

        self.connection.execute(
            """
            DELETE FROM atlassian_structure_reference_evidence
            WHERE document_id = ?
            """,
            (document_id,),
        )
        project_structure_reference_search(self.connection, reference_id)
        archived = self._page(reference=str(reference_id))
        self.assertIn(
            'data-preview-state="archived"',
            archived.body.decode("utf-8"),
        )
        with patch("localbrain.main.connect", return_value=self.connection):
            archived_direct = atlassian_reference_page(
                self._request(
                    path="/atlassian/references/{}".format(reference_id)
                ),
                reference_id,
            )
        self.assertEqual(archived_direct.status_code, 200)
        self.assertIn("보관됨", archived_direct.body.decode("utf-8"))

        changes_before_missing = self.connection.total_changes
        with patch("localbrain.main.connect", return_value=self.connection):
            missing_direct = atlassian_reference_page(
                self._request(path="/atlassian/references/999999"),
                999999,
                return_to="/atlassian?view=jira",
            )
            unsafe_return = atlassian_reference_page(
                self._request(path="/atlassian/references/999998"),
                999998,
                return_to="https://outside.invalid/atlassian",
            )
        self.assertEqual(missing_direct.status_code, 404)
        missing_html = html.unescape(missing_direct.body.decode("utf-8"))
        self.assertIn("이 구조 참조를 찾을 수 없습니다", missing_html)
        self.assertIn('href="/atlassian?view=jira"', missing_html)
        self.assertEqual(unsafe_return.status_code, 404)
        unsafe_html = html.unescape(unsafe_return.body.decode("utf-8"))
        self.assertIn('href="/atlassian"', unsafe_html)
        self.assertNotIn("outside.invalid", unsafe_html)
        self.assertEqual(self.connection.total_changes, changes_before_missing)

        with self.assertRaises(HTTPException) as both:
            self._page(
                item=str(self.reference["external_resource_id"]),
                reference=str(reference_id),
            )
        self.assertEqual(both.exception.status_code, 400)
        with self.assertRaises(HTTPException) as repeated:
            self._page(
                reference=str(reference_id),
                _query_string="reference=1&reference=2",
            )
        self.assertEqual(repeated.exception.status_code, 400)

    def test_reference_search_and_post_sync_return_canonicalization(self):
        reference_id, site_id, document_id = self._structure_reference(
            "https://jira.primary.test/secure/RapidBoard.jspa?"
            "rapidView=37746&projectKey=JPDI"
        )
        result = search(
            self.connection, "37746", source_scope="atlassian"
        )[0]
        self.assertEqual(
            result["entity_type"], "atlassian_structure_reference"
        )
        self.assertEqual(result["source_kind"], "atlassian:jira")
        self.assertEqual(result["reference_kind"], "jira_board")
        self.assertEqual(result["container_label"], "JPDI")
        exact_url = browse_inventory(
            self.connection,
            {
                "q": (
                    "https://jira.primary.test/secure/RapidBoard.jspa?"
                    "rapidView=37746&projectKey=JPDI"
                )
            },
        )["references"][0]
        self.assertEqual(exact_url["exact_match"]["role"], "url")

        stale = (
            "/atlassian?view=jira&site_id={}&"
            "structural_scope=unclassified&q=37746&reference={}"
        ).format(site_id, reference_id)
        canonical = _atlassian_inventory_return_path(
            stale, self.connection, post_sync=True
        )
        parsed = parse_qs(urlsplit(canonical).query)
        self.assertEqual(parsed["reference"], [str(reference_id)])
        self.assertEqual(parsed["site_id"], [str(site_id)])
        self.assertEqual(
            parsed["structural_scope"], ["url:jira:JPDI"]
        )
        self.assertEqual(parsed["q"], ["37746"])

        self.connection.execute(
            """
            DELETE FROM atlassian_structure_reference_evidence
            WHERE document_id = ?
            """,
            (document_id,),
        )
        archived = _atlassian_inventory_return_path(
            canonical, self.connection, post_sync=True
        )
        parsed_archived = parse_qs(urlsplit(archived).query)
        self.assertEqual(parsed_archived["reference"], [str(reference_id)])
        self.assertNotIn("site_id", parsed_archived)
        self.assertNotIn("structural_scope", parsed_archived)

        self.assertEqual(
            _atlassian_inventory_return_path(
                "/atlassian?view=wiki&reference={}".format(reference_id),
                self.connection,
                post_sync=True,
            ),
            "/atlassian",
        )


if __name__ == "__main__":
    unittest.main()
