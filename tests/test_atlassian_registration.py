import asyncio
import json
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from starlette.requests import Request

from localbrain.atlassian import register_atlassian_site
from localbrain.atlassian_registration import (
    AtlassianRegistrationError,
    prepare_space_catalog_run,
    recognize_registration_url,
    register_atlassian_site_access,
    register_atlassian_url,
    register_space_candidate,
    registered_scope_overview,
    registration_inventory,
    registration_preview,
    space_catalog_candidates,
    update_atlassian_connection,
)
from localbrain.external_access import (
    record_capability_observation,
    register_source_instance,
)
from localbrain.main import (
    app,
    atlassian_page,
    atlassian_register,
    atlassian_register_access,
    atlassian_registration_preview,
    atlassian_update_connection,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class AtlassianRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.jira_source = register_source_instance(
            self.connection,
            instance_key="synthetic-jira",
            provider_kind="mcp_gateway",
            service="jira",
            display_name="Synthetic Jira",
            config_ref="synthetic-jira",
        )
        self.jira_site = register_atlassian_site(
            self.connection,
            source_instance_id=self.jira_source["id"],
            base_url="https://jira.example.test",
        )
        self.confluence_source = register_source_instance(
            self.connection,
            instance_key="synthetic-wiki",
            provider_kind="mcp_gateway",
            service="confluence",
            display_name="Synthetic Wiki",
            config_ref="synthetic-wiki",
        )
        self.confluence_site = register_atlassian_site(
            self.connection,
            source_instance_id=self.confluence_source["id"],
            base_url="https://wiki.example.test",
        )

    def tearDown(self):
        self.connection.close()
        self.temporary.cleanup()

    @contextmanager
    def _transaction(self):
        self.connection.execute("SAVEPOINT registration_web_test")
        try:
            yield self.connection
        except Exception:
            self.connection.execute("ROLLBACK TO registration_web_test")
            self.connection.execute("RELEASE registration_web_test")
            raise
        else:
            self.connection.execute("RELEASE registration_web_test")

    def _form_request(self, body: str) -> Request:
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
                "method": "POST",
                "path": "/atlassian/register",
                "headers": [
                    (
                        b"content-type",
                        b"application/x-www-form-urlencoded",
                    )
                ],
                "query_string": b"",
                "server": ("test", 80),
                "client": ("test", 1),
                "scheme": "http",
            },
            receive,
        )

    def _get_request(self, path: str = "/atlassian") -> Request:
        return Request(
            {
                "type": "http",
                "app": app,
                "method": "GET",
                "path": path,
                "headers": [],
                "query_string": b"",
                "server": ("test", 80),
                "client": ("test", 1),
                "scheme": "http",
            }
        )

    def test_strict_url_recognition_rejects_key_only_and_service_mismatch(self):
        issue = recognize_registration_url(
            "https://jira.example.test/browse/SYN-12"
        )
        project = recognize_registration_url(
            "https://jira.example.test/projects/SYN"
        )
        page = recognize_registration_url(
            "https://wiki.example.test/spaces/TEAM/pages/12345/Title"
        )
        space = recognize_registration_url(
            "https://wiki.example.test/spaces/TEAM/overview"
        )
        self.assertEqual(
            (issue.service, issue.kind, issue.remote_key),
            ("jira", "item", "SYN-12"),
        )
        self.assertEqual(
            (project.service, project.kind, project.space_key),
            ("jira", "space", "SYN"),
        )
        self.assertEqual(
            (page.service, page.kind, page.remote_id, page.space_key),
            ("confluence", "item", "12345", "TEAM"),
        )
        self.assertEqual(
            (space.service, space.kind, space.space_key),
            ("confluence", "space", "TEAM"),
        )
        for invalid in ("SYN-12", "https://jira.example.test/rest/api/issue/SYN-12"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(AtlassianRegistrationError):
                    recognize_registration_url(invalid)
        with self.assertRaises(AtlassianRegistrationError) as mismatch:
            recognize_registration_url(
                "https://jira.example.test/browse/SYN-12",
                expected_service="confluence",
            )
        self.assertEqual(mismatch.exception.code, "service-mismatch")

    def test_direct_registration_is_local_idempotent_and_defaults_spaces(self):
        item = register_atlassian_url(
            self.connection,
            url="https://jira.example.test/browse/SYN-12",
            service="jira",
        )
        repeated = register_atlassian_url(
            self.connection,
            url="https://JIRA.example.test:443/browse/SYN-12/",
            service="jira",
        )
        jira_space = register_atlassian_url(
            self.connection,
            url="https://jira.example.test/projects/SYN",
            service="jira",
        )
        confluence_space = register_atlassian_url(
            self.connection,
            url="https://wiki.example.test/spaces/TEAM/overview",
            service="confluence",
        )
        confluence_page = register_atlassian_url(
            self.connection,
            url=(
                "https://wiki.example.test/spaces/TEAM/pages/"
                "12345/Quarterly-Roadmap"
            ),
            service="confluence",
        )
        self.assertTrue(item["created"])
        self.assertFalse(repeated["created"])
        self.assertEqual(item["id"], repeated["id"])
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_items WHERE service = 'jira'"
            ).fetchone()[0],
            1,
        )
        spaces = {
            row["id"]: dict(row)
            for row in self.connection.execute(
                "SELECT * FROM atlassian_spaces ORDER BY id"
            )
        }
        self.assertEqual(spaces[jira_space["id"]]["coverage"], "selected-content")
        self.assertEqual(
            spaces[confluence_space["id"]]["coverage"], "full-content"
        )
        self.assertEqual(
            spaces[jira_space["id"]]["canonical_url"],
            "https://jira.example.test/projects/SYN",
        )
        titles = {
            row["id"]: row["title"]
            for row in self.connection.execute(
                "SELECT id, title FROM external_resources"
            )
        }
        self.assertEqual(titles[item["id"]], "SYN-12")
        self.assertEqual(titles[confluence_page["id"]], "Quarterly Roadmap")

    def test_registered_scope_groups_connections_by_domain_and_deduplicates_spaces(self):
        official_source = register_source_instance(
            self.connection,
            instance_key="synthetic-jira-official",
            provider_kind="atlassian_cloud",
            service="jira",
            display_name="Synthetic Jira Official",
            config_ref="00000000-0000-4000-8000-000000000001",
        )
        official_site = register_atlassian_site(
            self.connection,
            source_instance_id=official_source["id"],
            base_url="https://jira.example.test",
        )
        first = register_atlassian_url(
            self.connection,
            url="https://jira.example.test/projects/SYN",
            service="jira",
            site_id=self.jira_site["id"],
        )
        second = register_atlassian_url(
            self.connection,
            url="https://jira.example.test/projects/SYN",
            service="jira",
            site_id=official_site["id"],
        )
        self.assertEqual(first["id"], second["id"])

        overview = registered_scope_overview(self.connection, "jira")

        self.assertEqual(len(overview), 1)
        self.assertEqual(
            overview[0]["normalized_domain"], "jira.example.test"
        )
        self.assertEqual(len(overview[0]["connections"]), 2)
        self.assertEqual(len(overview[0]["spaces"]), 1)
        self.assertEqual(overview[0]["spaces"][0]["space_key"], "SYN")
        self.assertNotIn("candidates", overview[0])
        self.assertNotIn("evidence", overview[0])

    def test_catalog_target_and_connection_domain_must_match(self):
        with self.assertRaises(AtlassianRegistrationError) as mismatch:
            prepare_space_catalog_run(
                self.connection,
                site_id=self.jira_site["id"],
                target_domain="other.example.test",
            )
        self.assertEqual(
            mismatch.exception.code, "target-connection-mismatch"
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM maintenance_runs"
            ).fetchone()[0],
            0,
        )

    def test_local_registration_and_access_edit_keep_generated_identity(self):
        preview = registration_preview(
            self.connection,
            url="https://new.example.test/browse/NEW-12",
            expected_service="jira",
        )
        self.assertEqual(preview["normalized_domain"], "new.example.test")
        self.assertEqual(preview["identifier"], "NEW-12")
        self.assertNotIn("requires_connection", preview)
        self.assertNotIn("matches", preview)
        self.assertNotIn("suggested_site_name", preview)

        item = register_atlassian_url(
            self.connection,
            url="https://new.example.test/browse/NEW-12",
            service="jira",
        )
        site = self.connection.execute(
            """
            SELECT atlassian_sites.*
            FROM atlassian_sites
            JOIN atlassian_items
              ON atlassian_items.site_id = atlassian_sites.id
            WHERE atlassian_items.external_resource_id = ?
            """,
            (item["id"],),
        ).fetchone()
        with self.assertRaises(AtlassianRegistrationError):
            register_atlassian_site_access(
                self.connection,
                site_id=site["id"],
                service="jira",
                provider_kind="atlassian_cloud",
                config_ref="",
            )
        created = register_atlassian_site_access(
            self.connection,
            site_id=site["id"],
            service="jira",
            provider_kind="atlassian_cloud",
            config_ref="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1",
        )
        source = self.connection.execute(
            """
            SELECT * FROM external_source_instances
            WHERE id = ?
            """,
            (created["source_instance_id"],),
        ).fetchone()
        self.assertEqual(source["provider_kind"], "atlassian_cloud")
        self.assertEqual(
            source["config_ref"],
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1",
        )
        generated_source_name = source["display_name"]
        self.assertIsNone(site["display_name"])
        updated = update_atlassian_connection(
            self.connection,
            source_instance_id=created["source_instance_id"],
            site_id=site["id"],
            enabled=False,
        )
        self.assertFalse(updated["enabled"])
        self.assertTrue(updated["config_bound"])
        source = self.connection.execute(
            """
            SELECT * FROM external_source_instances
            WHERE id = ?
            """,
            (created["source_instance_id"],),
        ).fetchone()
        self.assertEqual(source["display_name"], generated_source_name)
        self.assertEqual(
            source["config_ref"],
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1",
        )
        with self.assertRaises(AtlassianRegistrationError):
            update_atlassian_connection(
                self.connection,
                source_instance_id=created["source_instance_id"],
                site_id=site["id"],
                enabled=True,
                config_ref="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2",
            )
        preserved = self.connection.execute(
            """
            SELECT display_name, config_ref, enabled
            FROM external_source_instances WHERE id = ?
            """,
            (created["source_instance_id"],),
        ).fetchone()
        self.assertEqual(preserved["display_name"], generated_source_name)
        self.assertEqual(
            preserved["config_ref"],
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1",
        )
        self.assertEqual(preserved["enabled"], 0)

    def test_same_domain_reuses_site_and_item_across_access_bindings(self):
        second_source = register_source_instance(
            self.connection,
            instance_key="synthetic-jira-two",
            provider_kind="mcp_gateway",
            service="jira",
            display_name="Synthetic Jira Two",
            config_ref="synthetic-jira-two",
        )
        second_site = register_atlassian_site(
            self.connection,
            source_instance_id=second_source["id"],
            base_url="https://jira.example.test",
        )
        first = register_atlassian_url(
            self.connection,
            url="https://jira.example.test/browse/SYN-15",
            service="jira",
            site_id=self.jira_site["id"],
        )
        second = register_atlassian_url(
            self.connection,
            url="https://jira.example.test/browse/SYN-15",
            service="jira",
            site_id=second_site["id"],
        )
        self.assertEqual(self.jira_site["id"], second_site["id"])
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM atlassian_site_bindings
                WHERE site_id = ?
                """,
                (self.jira_site["id"],),
            ).fetchone()[0],
            2,
        )

    def test_space_catalog_is_one_call_partial_and_requires_confirmation(self):
        record_capability_observation(
            self.connection,
            self.jira_source["id"],
            availability="available",
            operations=("jira.search_metadata",),
            schema_fingerprint="a" * 64,
        )
        run_id = prepare_space_catalog_run(
            self.connection,
            site_id=self.jira_site["id"],
            runner="claude",
            run_root=Path(self.temporary.name),
        )
        run = self.connection.execute(
            "SELECT * FROM maintenance_runs WHERE id = ?", (run_id,)
        ).fetchone()
        manifest = json.loads(
            Path(run["manifest_path"]).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["call_budget"], 1)
        self.assertEqual(manifest["scope"]["kind"], "space")
        self.assertEqual(len(manifest["targets"]), 1)
        request = manifest["targets"][0]["requests"][0]
        self.assertEqual(request["logical_operation"], "jira.search_metadata")
        self.assertEqual(request["arguments"]["fields"], ["project"])
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_spaces"
            ).fetchone()[0],
            0,
        )
        structured = {
            "targets": [
                {
                    "target_id": "space-catalog-site-{}".format(
                        self.jira_site["id"]
                    ),
                    "requests": [
                        {
                            "metadata": {
                                "project": [
                                    {"id": "100", "key": "SYN", "name": "Synthetic"},
                                    {"id": "100", "key": "SYN", "name": "Synthetic"},
                                    {"id": "200", "key": "OPS", "name": "Operations"},
                                ]
                            }
                        }
                    ],
                }
            ]
        }
        self.connection.execute(
            """
            UPDATE maintenance_runs
            SET status = 'partial', structured_result_json = ?
            WHERE id = ?
            """,
            (json.dumps(structured), run_id),
        )
        result = space_catalog_candidates(self.connection, run_id, "jira")
        self.assertTrue(result["partial"])
        self.assertEqual(result["site_id"], self.jira_site["id"])
        self.assertEqual(
            [candidate["key"] for candidate in result["candidates"]],
            ["SYN", "OPS"],
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_spaces"
            ).fetchone()[0],
            0,
        )
        registered = register_space_candidate(
            self.connection,
            site_id=result["site_id"],
            service="jira",
            space_key=result["candidates"][0]["key"],
            remote_id=result["candidates"][0]["remote_id"],
            name=result["candidates"][0]["name"],
        )
        self.assertTrue(registered["created"])
        inventory = registration_inventory(self.connection, "jira")
        self.assertEqual(len(inventory["spaces"]), 1)
        self.assertEqual(inventory["spaces"][0]["space_key"], "SYN")

    def test_unknown_capability_does_not_create_a_catalog_run(self):
        with self.assertRaises(AtlassianRegistrationError) as unavailable:
            prepare_space_catalog_run(
                self.connection,
                site_id=self.jira_site["id"],
                run_root=Path(self.temporary.name),
            )
        self.assertEqual(unavailable.exception.code, "capability-not-current")
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM maintenance_runs"
            ).fetchone()[0],
            0,
        )

    def test_no_script_registration_route_preserves_errors_and_redirects_success(self):
        with patch(
            "localbrain.main.transaction", side_effect=self._transaction
        ), patch("localbrain.main.connect", return_value=self.connection):
            invalid = asyncio.run(
                atlassian_register(
                    self._form_request("service=jira&url=SYN-12")
                )
            )
            self.assertEqual(invalid.status_code, 422)
            self.assertIn("SYN-12", invalid.body.decode("utf-8"))
            self.assertEqual(
                self.connection.execute(
                    "SELECT COUNT(*) FROM external_resources"
                ).fetchone()[0],
                0,
            )
            success = asyncio.run(
                atlassian_register(
                    self._form_request(
                        "service=jira&url=https%3A%2F%2Fjira.example.test"
                        "%2Fbrowse%2FSYN-12"
                    )
                )
            )
        self.assertEqual(success.status_code, 303)
        self.assertIn(
            "/atlassian?view=jira&mode=setup&method=url&notice=item-created",
            success.headers["location"],
        )
        self.assertIn("#atlassian-item-", success.headers["location"])

    def test_no_script_local_registration_and_separate_access_routes(self):
        with patch(
            "localbrain.main.transaction", side_effect=self._transaction
        ), patch("localbrain.main.connect", return_value=self.connection):
            preview = atlassian_registration_preview(
                url="https://first.example.test/browse/FIRST-9",
                service="jira",
            )
            self.assertEqual(preview["identifier"], "FIRST-9")
            self.assertNotIn("requires_connection", preview)
            created = asyncio.run(
                atlassian_register(
                    self._form_request(
                        "service=jira&url=https%3A%2F%2Ffirst.example.test"
                        "%2Fbrowse%2FFIRST-9"
                    )
                )
            )
            self.assertEqual(created.status_code, 303)
            self.assertIn(
                "notice=item-created", created.headers["location"]
            )
            self.assertEqual(
                self.connection.execute(
                    "SELECT COUNT(*) FROM external_source_instances"
                ).fetchone()[0],
                2,
            )
            site = self.connection.execute(
                """
                SELECT id
                FROM atlassian_sites
                WHERE atlassian_sites.normalized_domain =
                      'first.example.test'
                """
            ).fetchone()
            self.assertEqual(
                self.connection.execute(
                    """
                    SELECT external_resources.title
                    FROM external_resources
                    JOIN atlassian_items
                      ON atlassian_items.external_resource_id =
                         external_resources.id
                    JOIN atlassian_sites
                      ON atlassian_sites.id = atlassian_items.site_id
                    WHERE atlassian_sites.normalized_domain =
                          'first.example.test'
                    """
                ).fetchone()[0],
                "FIRST-9",
            )
            page = atlassian_page(
                self._get_request(),
                view="jira",
                mode="setup",
                method="url",
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
            html = page.body.decode("utf-8")
            self.assertLess(
                html.index('action="/atlassian/register"'),
                html.index('action="/atlassian/access"'),
            )
            self.assertIn("first.example.test", html)
            self.assertIn("원격 접근 설정", html)
            self.assertNotIn('name="source_name"', html)
            self.assertNotIn('name="site_name"', html)
            self.assertNotIn('name="title"', html)
            access = asyncio.run(
                atlassian_register_access(
                    self._form_request(
                        (
                            "service=jira"
                            "&site_id={}"
                            "&provider_kind=atlassian_cloud"
                            "&config_ref=aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"
                        ).format(site["id"])
                    )
                )
            )
            self.assertEqual(access.status_code, 303)
            self.assertIn(
                "notice=connection-created", access.headers["location"]
            )
            source = self.connection.execute(
                """
                SELECT external_source_instances.id,
                       atlassian_site_bindings.site_id
                FROM external_source_instances
                JOIN atlassian_site_bindings
                  ON atlassian_site_bindings.source_instance_id =
                     external_source_instances.id
                WHERE atlassian_site_bindings.site_id = ?
                  AND external_source_instances.provider_kind =
                      'atlassian_cloud'
                """,
                (site["id"],),
            ).fetchone()
            edited = asyncio.run(
                atlassian_update_connection(
                    self._form_request(
                        "service=jira&enabled=1"
                    ),
                    source["id"],
                    source["site_id"],
                )
            )
        self.assertEqual(edited.status_code, 303)
        self.assertIn(
            "notice=connection-updated", edited.headers["location"]
        )
        saved = self.connection.execute(
            """
            SELECT display_name, config_ref
            FROM external_source_instances WHERE id = ?
            """,
            (source["id"],),
        ).fetchone()
        self.assertEqual(
            saved["display_name"],
            "공식 Atlassian MCP · first.example.test",
        )
        self.assertEqual(
            saved["config_ref"],
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1",
        )


if __name__ == "__main__":
    unittest.main()
