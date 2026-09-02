import asyncio
import json
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import ANY, patch
from urllib.parse import parse_qs, urlencode, urlsplit

from starlette.requests import Request

from localbrain.atlassian import (
    AtlassianContractError,
    register_atlassian_site,
    register_atlassian_space,
)
from localbrain.atlassian_registration import (
    AtlassianRegistrationError,
    prepare_space_catalog_run,
    recognize_registration_url,
    register_atlassian_site_access,
    register_atlassian_url,
    register_space_catalog_candidate,
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
    atlassian_add_page,
    atlassian_connections_page,
    atlassian_discover_spaces,
    atlassian_page,
    atlassian_register,
    atlassian_register_access,
    atlassian_register_space_candidate,
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

    def _form_request(
        self,
        body: str,
        *,
        path: str = "/atlassian/register",
        headers=None,
    ) -> Request:
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
                "path": path,
                "headers": [
                    (
                        b"content-type",
                        b"application/x-www-form-urlencoded",
                    ),
                    *[
                        (
                            str(key).lower().encode("ascii"),
                            str(value).encode("utf-8"),
                        )
                        for key, value in (headers or {}).items()
                    ],
                ],
                "query_string": b"",
                "server": ("test", 80),
                "client": ("test", 1),
                "scheme": "http",
            },
            receive,
        )

    def _get_request(self, path: str = "/atlassian") -> Request:
        parsed = urlsplit(path)
        return Request(
            {
                "type": "http",
                "app": app,
                "method": "GET",
                "path": parsed.path,
                "headers": [],
                "query_string": parsed.query.encode("utf-8"),
                "server": ("test", 80),
                "client": ("test", 1),
                "scheme": "http",
            }
        )

    def _explorer_get(self, location: str):
        query = parse_qs(urlsplit(location).query)
        value = lambda name, default=None: query.get(name, [default])[0]
        optional_int = lambda name: (
            int(value(name)) if value(name) not in (None, "") else None
        )
        with patch("localbrain.main.connect", return_value=self.connection):
            return atlassian_page(
                self._get_request(location),
                view=value("view", "all"),
                mode="browse",
                method="url",
                q=value("q", ""),
                source_instance_id=optional_int("source_instance_id"),
                site_id=optional_int("site_id"),
                space_id=optional_int("space_id"),
                structural_scope=value("structural_scope"),
                item_type=value("item_type"),
                coverage=value("coverage"),
                freshness=value("freshness"),
                attention=value("attention"),
                topic_id=optional_int("topic_id"),
                tag_id=optional_int("tag_id"),
                workstream_id=optional_int("workstream_id"),
                notice=value("notice"),
                catalog_run=value("catalog_run"),
                item=value("item"),
                sync_receipt=value("sync_receipt"),
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

    def test_shared_locator_keeps_add_owner_url_and_rejects_new_structure_kinds(self):
        alias = recognize_registration_url(
            "https://jira.example.test/issues/SYN-12?token=local"
        )
        self.assertEqual(alias.kind, "item")
        self.assertEqual(alias.remote_key, "SYN-12")
        self.assertEqual(
            alias.normalized_url,
            "https://jira.example.test/issues/SYN-12?token=local",
        )
        query_item = recognize_registration_url(
            "https://jira.example.test/secure/RapidBoard.jspa"
            "?rapidView=17&selectedIssue=SYN-12"
        )
        self.assertEqual((query_item.kind, query_item.remote_key), ("item", "SYN-12"))

        before = self.connection.total_changes
        unsupported = (
            "https://jira.example.test/secure/RapidBoard.jspa?rapidView=17",
            "https://jira.example.test/issues?filter=9",
            "https://jira.example.test/secure/Dashboard.jspa?selectPageId=4",
            "https://jira.example.test/servicedesk/customer/portal/3",
            "https://jira.example.test/browse?issueKey=SYN-12",
        )
        for url in unsupported:
            with self.subTest(url=url):
                with self.assertRaises(AtlassianRegistrationError) as raised:
                    register_atlassian_url(self.connection, url=url)
                self.assertEqual(raised.exception.code, "unsupported-url")
        self.assertEqual(self.connection.total_changes, before)

    def test_direct_registration_is_local_idempotent_and_defaults_spaces(self):
        item = register_atlassian_url(
            self.connection,
            url="https://jira.example.test/browse/SYN-12",
        )
        repeated = register_atlassian_url(
            self.connection,
            url="https://JIRA.example.test:443/browse/SYN-12/",
            service="confluence",
        )
        unconfirmed_alias = register_atlassian_url(
            self.connection,
            url="https://jira.example.test/issues/SYN-12",
        )
        jira_space = register_atlassian_url(
            self.connection,
            url="https://jira.example.test/projects/SYN",
        )
        repeated_jira_space = register_atlassian_url(
            self.connection,
            url="https://JIRA.example.test:443/projects/SYN/",
        )
        confluence_space = register_atlassian_url(
            self.connection,
            url="https://wiki.example.test/spaces/TEAM/overview",
        )
        confluence_page = register_atlassian_url(
            self.connection,
            url=(
                "https://wiki.example.test/spaces/TEAM/pages/"
                "12345/Quarterly-Roadmap"
            ),
        )
        self.assertTrue(item["created"])
        self.assertFalse(repeated["created"])
        self.assertEqual(item["id"], repeated["id"])
        self.assertTrue(unconfirmed_alias["created"])
        self.assertNotEqual(item["id"], unconfirmed_alias["id"])
        self.assertFalse(repeated_jira_space["created"])
        self.assertEqual(jira_space["id"], repeated_jira_space["id"])
        self.assertEqual(item["service"], "jira")
        self.assertEqual(item["site_id"], self.jira_site["id"])
        self.assertIsNone(item["space_id"])
        self.assertEqual(item["attention"], "normal")
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_items WHERE service = 'jira'"
            ).fetchone()[0],
            2,
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

        with self.assertRaises(AtlassianRegistrationError) as space_alias:
            register_atlassian_url(
                self.connection,
                url="https://wiki.example.test/display/TEAM",
            )
        self.assertEqual(space_alias.exception.code, "space-url-conflict")
        retained_space = self.connection.execute(
            "SELECT canonical_url FROM atlassian_spaces WHERE id = ?",
            (confluence_space["id"],),
        ).fetchone()
        self.assertEqual(
            retained_space["canonical_url"],
            "https://wiki.example.test/spaces/TEAM/overview",
        )

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
        with self.assertRaises(AtlassianRegistrationError) as tampered:
            register_space_catalog_candidate(
                self.connection,
                run_id=run_id,
                candidate_key="TAMPERED",
            )
        self.assertEqual(tampered.exception.code, "candidate-not-found")
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_spaces"
            ).fetchone()[0],
            0,
        )
        registered = register_space_catalog_candidate(
            self.connection,
            run_id=run_id,
            candidate_key="SYN",
        )
        self.assertTrue(registered["created"])
        self.assertEqual(registered["site_id"], self.jira_site["id"])
        inventory = registration_inventory(self.connection, "jira")
        self.assertEqual(len(inventory["spaces"]), 1)
        self.assertEqual(inventory["spaces"][0]["space_key"], "SYN")

    def test_catalog_candidate_rejects_a_deleted_run_source_without_writes(self):
        record_capability_observation(
            self.connection,
            self.jira_source["id"],
            availability="available",
            operations=("jira.search_metadata",),
            schema_fingerprint="b" * 64,
        )
        run_id = prepare_space_catalog_run(
            self.connection,
            site_id=self.jira_site["id"],
            runner="claude",
            run_root=Path(self.temporary.name),
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
                                "project": {
                                    "id": "gone-1",
                                    "key": "GONE",
                                    "name": "Gone source",
                                }
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
        self.connection.execute(
            "DELETE FROM external_source_instances WHERE id = ?",
            (self.jira_source["id"],),
        )
        with self.assertRaises(AtlassianRegistrationError) as missing:
            register_space_catalog_candidate(
                self.connection,
                run_id=run_id,
                candidate_key="GONE",
            )
        self.assertEqual(missing.exception.code, "candidate-not-found")
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_spaces"
            ).fetchone()[0],
            0,
        )

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

    def test_registration_helper_rolls_back_site_on_late_failure(self):
        before = {
            table: self.connection.execute(
                "SELECT COUNT(*) FROM {}".format(table)
            ).fetchone()[0]
            for table in (
                "atlassian_sites",
                "atlassian_spaces",
                "atlassian_items",
                "external_resources",
                "external_source_instances",
                "atlassian_site_bindings",
                "maintenance_runs",
            )
        }
        with patch(
            "localbrain.atlassian_registration.create_or_reuse_atlassian_stub",
            side_effect=AtlassianContractError(
                "synthetic-late-failure", "synthetic late failure"
            ),
        ), self.assertRaises(AtlassianRegistrationError):
            register_atlassian_url(
                self.connection,
                url="https://fresh.example.test/browse/FRESH-1",
            )
        after = {
            table: self.connection.execute(
                "SELECT COUNT(*) FROM {}".format(table)
            ).fetchone()[0]
            for table in before
        }
        self.assertEqual(after, before)

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
            partial = asyncio.run(
                atlassian_register(
                    self._form_request(
                        "url=SYN-12&return_to=%2Fatlassian%3Fmode%3Dsetup",
                        headers={
                            "X-LocalBrain-Partial": "atlassian-add"
                        },
                    )
                )
            )
            partial_html = partial.body.decode("utf-8")
            self.assertEqual(partial.status_code, 422)
            self.assertEqual(partial.headers["vary"], "X-LocalBrain-Partial")
            self.assertIn("data-atlassian-add-content", partial_html)
            self.assertNotIn("workspace-header", partial_html)
            self.assertIn(
                'value="/atlassian#atlassian-add-action"', partial_html
            )
            success = asyncio.run(
                atlassian_register(
                    self._form_request(
                        "service=confluence&url=https%3A%2F%2Fjira.example.test"
                        "%2Fbrowse%2FSYN-12"
                    )
                )
            )
        self.assertEqual(success.status_code, 303)
        destination = urlsplit(success.headers["location"])
        query = parse_qs(destination.query)
        self.assertEqual(destination.path, "/atlassian")
        self.assertEqual(query["view"], ["jira"])
        self.assertEqual(query["structural_scope"], ["url:jira:SYN"])
        self.assertEqual(query["notice"], ["item-created"])
        self.assertIn("item", query)
        self.assertNotIn("mode", query)
        self.assertEqual(self._explorer_get(success.headers["location"]).status_code, 200)
        item_id = int(query["item"][0])
        self.connection.execute(
            "UPDATE atlassian_items SET attention = 'archived' "
            "WHERE external_resource_id = ?",
            (item_id,),
        )
        with patch(
            "localbrain.main.transaction", side_effect=self._transaction
        ), patch("localbrain.main.connect", return_value=self.connection):
            reused = asyncio.run(
                atlassian_register(
                    self._form_request(
                        "url=https%3A%2F%2Fjira.example.test"
                        "%2Fbrowse%2FSYN-12"
                    )
                )
            )
            space = asyncio.run(
                atlassian_register(
                    self._form_request(
                        "url=https%3A%2F%2Fjira.example.test"
                        "%2Fprojects%2FNEW"
                    )
                )
            )
        reused_query = parse_qs(urlsplit(reused.headers["location"]).query)
        self.assertEqual(reused_query["attention"], ["archived"])
        self.assertEqual(reused_query["notice"], ["item-reused"])
        self.assertEqual(
            reused_query["structural_scope"], ["url:jira:SYN"]
        )
        self.assertEqual(self._explorer_get(reused.headers["location"]).status_code, 200)
        registered_space = register_atlassian_space(
            self.connection,
            site_id=int(query["site_id"][0]),
            source_instance_id=self.jira_source["id"],
            service="jira",
            name="Persisted Project",
            space_key="SYN",
            canonical_url="https://jira.example.test/projects/SYN",
        )
        self.connection.execute(
            "UPDATE atlassian_items SET space_id = ? WHERE external_resource_id = ?",
            (registered_space["id"], item_id),
        )
        with patch(
            "localbrain.main.transaction", side_effect=self._transaction
        ), patch("localbrain.main.connect", return_value=self.connection):
            contained = asyncio.run(
                atlassian_register(
                    self._form_request(
                        "url=https%3A%2F%2Fjira.example.test"
                        "%2Fbrowse%2FSYN-12"
                    )
                )
            )
        contained_query = parse_qs(
            urlsplit(contained.headers["location"]).query
        )
        self.assertEqual(
            contained_query["space_id"], [str(registered_space["id"])]
        )
        self.assertNotIn("structural_scope", contained_query)
        self.assertEqual(contained_query["attention"], ["archived"])
        self.assertEqual(
            self._explorer_get(contained.headers["location"]).status_code,
            200,
        )
        space_query = parse_qs(urlsplit(space.headers["location"]).query)
        self.assertEqual(space_query["view"], ["jira"])
        self.assertIn("site_id", space_query)
        self.assertIn("space_id", space_query)
        self.assertNotIn("item", space_query)
        self.assertEqual(space_query["notice"], ["space-created"])

    def test_add_accepts_an_encoded_multibyte_url_at_the_unicode_limit(self):
        prefix = "https://wiki.example.test/spaces/SYN/pages/900000/"
        url = prefix + ("가" * (8000 - len(prefix)))
        body = urlencode(
            {"url": url, "return_to": "/atlassian?view=all"}
        )
        self.assertEqual(len(url), 8000)
        self.assertGreater(len(body.encode("utf-8")), 32_768)
        with patch(
            "localbrain.main.transaction", side_effect=self._transaction
        ), patch("localbrain.main.connect", return_value=self.connection):
            response = asyncio.run(
                atlassian_register(self._form_request(body))
            )
        self.assertEqual(response.status_code, 303)
        query = parse_qs(urlsplit(response.headers["location"]).query)
        self.assertEqual(query["view"], ["wiki"])
        self.assertEqual(query["notice"], ["item-created"])
        self.assertEqual(
            query["structural_scope"], ["url:confluence:SYN"]
        )
        self.assertEqual(self._explorer_get(response.headers["location"]).status_code, 200)
        item_id = int(query["item"][0])
        stored_title = self.connection.execute(
            "SELECT title FROM external_resources WHERE id = ?", (item_id,)
        ).fetchone()["title"]
        self.assertEqual(len(stored_title), 500)

    def test_add_loose_wiki_page_handoff_uses_unclassified_scope(self):
        body = urlencode(
            {
                "url": "https://wiki.example.test/wiki/pages/456/Loose",
                "return_to": "/atlassian?view=all",
            }
        )
        with patch(
            "localbrain.main.transaction", side_effect=self._transaction
        ), patch("localbrain.main.connect", return_value=self.connection):
            response = asyncio.run(
                atlassian_register(self._form_request(body))
            )

        query = parse_qs(urlsplit(response.headers["location"]).query)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(query["view"], ["wiki"])
        self.assertEqual(query["structural_scope"], ["unclassified"])
        self.assertEqual(
            self._explorer_get(response.headers["location"]).status_code,
            200,
        )

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
            add_page = atlassian_add_page(
                self._get_request("/atlassian/add"),
                return_to="https://outside.example/steal",
            )
            add_html = add_page.body.decode("utf-8")
            self.assertIn('action="/atlassian/register"', add_html)
            self.assertEqual(add_html.count('name="url"'), 1)
            self.assertNotIn('name="service"', add_html)
            self.assertNotIn("first.example.test", add_html)
            self.assertIn(
                'name="return_to" value="/atlassian#atlassian-add-action"',
                add_html,
            )

            connections = atlassian_connections_page(
                self._get_request("/atlassian/connections"),
                view="jira",
            )
            connections_html = connections.body.decode("utf-8")
            self.assertIn("first.example.test", connections_html)
            self.assertIn("원격 접근 설정", connections_html)
            self.assertIn('action="/atlassian/access"', connections_html)
            self.assertNotIn('action="/atlassian/register"', connections_html)
            self.assertNotIn('name="target_domain"', connections_html)
            self.assertNotIn('name="source_name"', connections_html)
            self.assertNotIn('name="site_name"', connections_html)
            self.assertNotIn('name="title"', connections_html)
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
                        "service=confluence&enabled=1"
                    ),
                    source["id"],
                    source["site_id"],
                )
            )
            mismatched_edit = asyncio.run(
                atlassian_update_connection(
                    self._form_request("enabled=1"),
                    source["id"],
                    self.confluence_site["id"],
                )
            )
            oversized_edit = asyncio.run(
                atlassian_update_connection(
                    self._form_request("enabled=1"),
                    10**100,
                    10**100,
                )
            )
        self.assertEqual(edited.status_code, 303)
        self.assertIn(
            "notice=connection-updated", edited.headers["location"]
        )
        self.assertIn("view=jira", edited.headers["location"])
        self.assertEqual(mismatched_edit.status_code, 422)
        mismatched_html = mismatched_edit.body.decode("utf-8")
        self.assertIn("data-atlassian-connections", mismatched_html)
        self.assertIn("data-atlassian-form-error", mismatched_html)
        self.assertIn(
            "The selected Source Instance/Site does not exist",
            mismatched_html,
        )
        self.assertEqual(oversized_edit.status_code, 422)
        self.assertIn(
            "Connection path is invalid",
            oversized_edit.body.decode("utf-8"),
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

    def test_connections_views_are_canonical_and_isolated(self):
        with patch("localbrain.main.connect", return_value=self.connection):
            for view in ("jira", "wiki"):
                with self.subTest(view=view):
                    response = atlassian_connections_page(
                        self._get_request("/atlassian/connections"),
                        view=view,
                    )
                    self.assertEqual(response.status_code, 200)
                    rendered = response.body.decode("utf-8")
                    self.assertIn("data-atlassian-connections", rendered)
                    self.assertNotIn("data-atlassian-explorer", rendered)
                    self.assertNotIn('action="/atlassian/register"', rendered)
            redirects = {
                None: "view=jira",
                "all": "view=jira",
                "unsupported": "view=jira",
                "confluence": "view=wiki",
            }
            for view, expected in redirects.items():
                with self.subTest(redirect=view):
                    response = atlassian_connections_page(
                        self._get_request("/atlassian/connections"),
                        view=view,
                    )
                    self.assertEqual(response.status_code, 303)
                    self.assertIn(expected, response.headers["location"])

    def test_connections_scope_uses_only_site_space_and_item_aggregate_reads(self):
        statements = []
        self.connection.set_trace_callback(statements.append)
        try:
            with patch(
                "localbrain.main.connect", return_value=self.connection
            ):
                response = atlassian_connections_page(
                    self._get_request("/atlassian/connections"),
                    view="jira",
                )
        finally:
            self.connection.set_trace_callback(None)
        self.assertEqual(response.status_code, 200)
        normalized = [" ".join(value.lower().split()) for value in statements]
        item_reads = [
            value for value in normalized if "from atlassian_items" in value
        ]
        self.assertEqual(len(item_reads), 1)
        self.assertIn("count(*)", item_reads[0])
        self.assertIn("group by site_id", item_reads[0])
        for forbidden in (
            "atlassian_item_urls",
            "atlassian_item_content",
            "atlassian_item_local_state",
            "atlassian_item_evidence",
            "external_resources",
            "workstream_links",
            "thread_links",
        ):
            self.assertFalse(
                any(forbidden in statement for statement in normalized),
                forbidden,
            )

    def test_discovery_derives_binding_authority_before_run_work(self):
        jira_binding = self.connection.execute(
            "SELECT id FROM atlassian_site_bindings WHERE site_id = ?",
            (self.jira_site["id"],),
        ).fetchone()["id"]
        mismatched = self._form_request(
            "site_id={}&binding_id={}&runner=claude".format(
                self.confluence_site["id"], jira_binding
            ),
            path="/atlassian/spaces/discover",
        )
        with patch(
            "localbrain.main.transaction", side_effect=self._transaction
        ), patch(
            "localbrain.main.connect", return_value=self.connection
        ), patch(
            "localbrain.main.prepare_space_catalog_run"
        ) as prepare, patch(
            "localbrain.main.runner_executable"
        ) as executable:
            response = asyncio.run(atlassian_discover_spaces(mismatched))
        self.assertEqual(response.status_code, 422)
        self.assertIn("현재 Site", response.body.decode("utf-8"))
        prepare.assert_not_called()
        executable.assert_not_called()
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM maintenance_runs"
            ).fetchone()[0],
            0,
        )

        prior_executor = getattr(app.state, "external_read_executor", None)
        app.state.external_read_executor = object()
        try:
            valid = self._form_request(
                "site_id={}&binding_id={}&runner=codex"
                "&service=confluence&target_domain=evil.example".format(
                    self.jira_site["id"], jira_binding
                ),
                path="/atlassian/spaces/discover",
            )
            with patch(
                "localbrain.main.transaction", side_effect=self._transaction
            ), patch(
                "localbrain.main.connect", return_value=self.connection
            ), patch(
                "localbrain.main.runner_executable", return_value=True
            ), patch(
                "localbrain.main.prepare_space_catalog_run",
                return_value="lb-synthetic-catalog",
            ) as prepare, patch("localbrain.main.start_run") as start:
                response = asyncio.run(atlassian_discover_spaces(valid))
        finally:
            app.state.external_read_executor = prior_executor
        self.assertEqual(response.status_code, 303)
        self.assertIn("view=jira", response.headers["location"])
        kwargs = prepare.call_args.kwargs
        self.assertEqual(kwargs["site_id"], self.jira_site["id"])
        self.assertEqual(kwargs["source_instance_id"], self.jira_source["id"])
        self.assertEqual(kwargs["target_domain"], "jira.example.test")
        self.assertEqual(kwargs["runner"], "codex")
        start.assert_called_once_with("lb-synthetic-catalog", ANY)

    def test_candidate_post_uses_only_run_owned_identity(self):
        request = self._form_request(
            "catalog_run=lb-run-owned&candidate_key=SAFE"
            "&service=confluence&site_id=999&name=Tampered"
            "&remote_id=bad&source_instance_id=999",
            path="/atlassian/spaces/register",
        )
        result = {
            "kind": "space",
            "created": True,
            "id": 41,
            "site_id": self.jira_site["id"],
            "service": "jira",
        }
        with patch(
            "localbrain.main.transaction", side_effect=self._transaction
        ), patch(
            "localbrain.main.register_space_catalog_candidate",
            return_value=result,
        ) as register:
            response = asyncio.run(
                atlassian_register_space_candidate(request)
            )
        register.assert_called_once_with(
            self.connection,
            run_id="lb-run-owned",
            candidate_key="SAFE",
        )
        self.assertEqual(response.status_code, 303)
        query = parse_qs(urlsplit(response.headers["location"]).query)
        self.assertEqual(query["view"], ["jira"])
        self.assertEqual(query["site_id"], [str(self.jira_site["id"])])
        self.assertEqual(query["space_id"], ["41"])


if __name__ == "__main__":
    unittest.main()
