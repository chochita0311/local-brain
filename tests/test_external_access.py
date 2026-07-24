import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from localbrain.db import init_db
from localbrain.external_access import (
    CAPABILITY_SCHEMA,
    READ_POLICY_VERSION,
    ExternalAccessError,
    authorize_external_read,
    bind_source_instance_config_ref,
    capability_state,
    invalidate_capability_observation,
    known_policy_operations,
    policy_manifest,
    record_capability_observation,
    register_source_instance,
    set_source_instance_enabled,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"
SYNTHETIC_CLOUD_ID = "00000000-0000-4000-8000-000000000001"


class ExternalAccessTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    def tearDown(self):
        self.connection.close()

    def register(
        self,
        instance_key="gateway-jira-primary",
        provider_kind="mcp_gateway",
        service="jira",
        config_ref=None,
    ):
        return register_source_instance(
            self.connection,
            instance_key=instance_key,
            provider_kind=provider_kind,
            service=service,
            display_name="Synthetic source",
            config_ref=config_ref,
        )

    def observe(self, source_instance_id, operations, availability="available"):
        return record_capability_observation(
            self.connection,
            source_instance_id,
            availability=availability,
            operations=operations,
            schema_fingerprint=(
                hashlib.sha256(b"synthetic-schema").hexdigest()
                if availability == "available"
                else None
            ),
            checked_at="2026-07-23T00:00:00Z",
            error_code=("synthetic-error" if availability != "available" else None),
        )

    def test_registration_is_stable_and_identity_changes_fail(self):
        first = self.register()
        second = register_source_instance(
            self.connection,
            instance_key="gateway-jira-primary",
            provider_kind="mcp_gateway",
            service="jira",
            display_name="Renamed synthetic source",
        )
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(second["display_name"], "Renamed synthetic source")

        with self.assertRaisesRegex(
            ExternalAccessError, "cannot change provider, service, or config_ref"
        ):
            register_source_instance(
                self.connection,
                instance_key="gateway-jira-primary",
                provider_kind="atlassian_cloud",
                service="jira",
                display_name="Conflicting source",
                config_ref=SYNTHETIC_CLOUD_ID,
            )

    def test_all_approved_provider_service_pairs_are_representable(self):
        pairs = (
            ("mcp_gateway", "jira"),
            ("mcp_gateway", "confluence"),
            ("atlassian_cloud", "jira"),
            ("atlassian_cloud", "confluence"),
        )
        for index, (provider_kind, service) in enumerate(pairs):
            row = self.register(
                instance_key=f"synthetic-{index}",
                provider_kind=provider_kind,
                service=service,
                config_ref=(
                    SYNTHETIC_CLOUD_ID
                    if provider_kind == "atlassian_cloud"
                    else None
                ),
            )
            self.assertEqual(row["provider_kind"], provider_kind)
            self.assertEqual(row["service"], service)
            self.assertTrue(known_policy_operations(provider_kind, service))

    def test_observation_is_separate_replaceable_and_cascades(self):
        instance = self.register()
        state = self.observe(instance["id"], ("jira.search_metadata",))
        self.assertEqual(state["state"], "current")
        self.assertEqual(state["effective_operations"], ("jira.search_metadata",))

        replaced = record_capability_observation(
            self.connection,
            instance["id"],
            availability="unavailable",
            checked_at="2026-07-23T01:00:00Z",
            error_code="synthetic-unavailable",
        )
        self.assertEqual(replaced["state"], "unavailable")
        self.assertEqual(replaced["effective_operations"], ())
        self.assertEqual(
            replaced["error_message"], "External capability is unavailable."
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM external_source_capabilities"
            ).fetchone()[0],
            1,
        )

        self.connection.execute(
            "DELETE FROM external_source_instances WHERE id = ?", (instance["id"],)
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM external_source_capabilities"
            ).fetchone()[0],
            0,
        )

    def test_unknown_stale_unavailable_unauthorized_error_and_disabled_fail_closed(self):
        instance = self.register()
        self.assertEqual(capability_state(self.connection, instance["id"])["state"], "unknown")
        states = ("unavailable", "unauthorized", "error")
        for availability in states:
            state = self.observe(instance["id"], (), availability=availability)
            self.assertEqual(state["state"], availability)
            with self.assertRaises(ExternalAccessError) as denied:
                authorize_external_read(
                    self.connection,
                    instance["id"],
                    "jira.search_metadata",
                    {"jql": "project = SYNTHETIC"},
                )
            self.assertEqual(denied.exception.code, "capability-not-current")

        self.observe(instance["id"], ("jira.search_metadata",))
        stale = invalidate_capability_observation(
            self.connection,
            instance["id"],
            invalidated_at="2026-07-23T02:00:00Z",
        )
        self.assertEqual(stale["state"], "stale")

        self.observe(instance["id"], ("jira.search_metadata",))
        disabled = set_source_instance_enabled(
            self.connection, instance["id"], False
        )
        self.assertFalse(disabled["enabled"])
        self.assertEqual(
            capability_state(self.connection, instance["id"])["state"], "disabled"
        )

    def test_policy_version_mismatch_is_stale(self):
        instance = self.register()
        self.observe(instance["id"], ("jira.search_metadata",))
        self.connection.execute(
            """
            UPDATE external_source_capabilities
            SET policy_version = 'obsolete-policy'
            WHERE source_instance_id = ?
            """,
            (instance["id"],),
        )
        self.assertEqual(
            capability_state(self.connection, instance["id"])["state"], "stale"
        )

    def test_static_capability_inspection_bootstraps_unknown_and_stale_instances(self):
        instance = self.register()
        listed = authorize_external_read(
            self.connection,
            instance["id"],
            "capability.list_tools",
            {},
        )
        self.assertEqual(listed.tool_name, "mcp_gateway.gateway_list")
        self.assertEqual(listed.arguments, {"kind": "tool", "server": "jira"})

        self.observe(instance["id"], ("jira.search_metadata",))
        invalidate_capability_observation(self.connection, instance["id"])
        described = authorize_external_read(
            self.connection,
            instance["id"],
            "capability.describe_tools",
            {"names": ["jira__searchIssuesByJql", "jira__createIssue"]},
        )
        self.assertEqual(described.tool_name, "mcp_gateway.gateway_describe")
        self.assertEqual(
            described.arguments["items"],
            [
                {"kind": "tool", "name": "jira__searchIssuesByJql"},
                {"kind": "tool", "name": "jira__createIssue"},
            ],
        )

        set_source_instance_enabled(self.connection, instance["id"], False)
        with self.assertRaises(ExternalAccessError) as denied:
            authorize_external_read(
                self.connection,
                instance["id"],
                "capability.list_tools",
                {},
            )
        self.assertEqual(denied.exception.code, "capability-not-current")

    def test_gateway_jira_dispatch_is_nested_and_field_bounded(self):
        instance = self.register()
        self.observe(
            instance["id"],
            (
                "jira.search_metadata",
                "jira.read_description",
                "jira.read_project",
            ),
        )
        dispatch = authorize_external_read(
            self.connection,
            instance["id"],
            "jira.search_metadata",
            {
                "jql": "project = SYNTHETIC ORDER BY updated DESC",
                "fields": ["key", "summary", "status", "updated"],
                "limit": 25,
            },
        )
        self.assertEqual(dispatch.tool_name, "mcp_gateway.gateway_dispatch")
        self.assertEqual(dispatch.arguments["method"], "tools/call")
        self.assertEqual(dispatch.arguments["name"], "jira__searchIssuesByJql")
        self.assertEqual(
            dispatch.arguments["arguments"]["fields"],
            "key,summary,status,updated",
        )
        self.assertEqual(dispatch.policy_version, READ_POLICY_VERSION)

        description = authorize_external_read(
            self.connection,
            instance["id"],
            "jira.read_description",
            {"issue_key": "syn-12"},
        )
        self.assertEqual(
            description.arguments["arguments"]["fields"],
            "key,description,updated",
        )
        self.assertNotIn("comment", description.arguments["arguments"]["fields"])

        with self.assertRaises(ExternalAccessError) as denied:
            authorize_external_read(
                self.connection,
                instance["id"],
                "jira.search_metadata",
                {"jql": 'comment ~ "sensitive phrase"'},
            )
        self.assertEqual(denied.exception.code, "field-not-allowed")

    def test_cloud_jira_dispatch_injects_config_and_rejects_overbroad_fields(self):
        instance = self.register(
            instance_key="cloud-jira-primary",
            provider_kind="atlassian_cloud",
            service="jira",
            config_ref=SYNTHETIC_CLOUD_ID,
        )
        self.observe(instance["id"], ("jira.search_metadata",))
        dispatch = authorize_external_read(
            self.connection,
            instance["id"],
            "jira.search_metadata",
            {
                "jql": "project = SYNTHETIC",
                "fields": ["key", "summary"],
            },
        )
        self.assertEqual(
            dispatch.tool_name, "atlassian.searchJiraIssuesUsingJql"
        )
        self.assertEqual(dispatch.arguments["cloudId"], SYNTHETIC_CLOUD_ID)
        self.assertEqual(dispatch.arguments["searchResultMode"], "issues")

        with self.assertRaises(ExternalAccessError) as denied:
            authorize_external_read(
                self.connection,
                instance["id"],
                "jira.search_metadata",
                {
                    "jql": "project = SYNTHETIC",
                    "fields": ["key", "comment"],
                },
            )
        self.assertEqual(denied.exception.code, "field-not-allowed")

    def test_confluence_policy_requires_regular_pages_and_fixed_expands(self):
        gateway = self.register(
            instance_key="gateway-wiki-primary",
            provider_kind="mcp_gateway",
            service="confluence",
        )
        self.observe(
            gateway["id"],
            (
                "confluence.search_pages",
                "confluence.read_page",
                "confluence.list_children",
            ),
        )
        search = authorize_external_read(
            self.connection,
            gateway["id"],
            "confluence.search_pages",
            {"cql": 'space = "SYN" AND type = page', "limit": 20},
        )
        self.assertEqual(search.arguments["name"], "wiki__searchWiki")
        self.assertEqual(
            search.arguments["arguments"]["expand"],
            "title,excerpt,space.key,version",
        )
        self.assertTrue(
            search.arguments["arguments"]["cql"].endswith("AND type = page")
        )
        page = authorize_external_read(
            self.connection,
            gateway["id"],
            "confluence.read_page",
            {"page_id": "12345"},
        )
        self.assertEqual(page.arguments["name"], "wiki__getPageById")
        self.assertNotIn("comment", page.arguments["arguments"]["expand"])
        self.assertNotIn("attachment", page.arguments["arguments"]["expand"])

        with self.assertRaises(ExternalAccessError) as denied:
            authorize_external_read(
                self.connection,
                gateway["id"],
                "confluence.search_pages",
                {"cql": 'space = "SYN" AND type = comment'},
            )
        self.assertEqual(denied.exception.code, "content-type-not-allowed")

    def test_official_confluence_unavailable_is_retained_without_authority(self):
        cloud = self.register(
            instance_key="cloud-confluence-primary",
            provider_kind="atlassian_cloud",
            service="confluence",
            config_ref=SYNTHETIC_CLOUD_ID,
        )
        state = self.observe(cloud["id"], (), availability="unavailable")
        self.assertEqual(state["state"], "unavailable")
        self.assertEqual(state["effective_operations"], ())
        with self.assertRaises(ExternalAccessError):
            authorize_external_read(
                self.connection,
                cloud["id"],
                "confluence.read_page",
                {"page_id": "12345"},
            )

    def test_observation_cannot_grant_unknown_or_write_operations(self):
        instance = self.register()
        for operation in (
            "jira.create_issue",
            "jira.transition_issue",
            "jira.add_comment",
            "arbitrary.tool",
        ):
            with self.assertRaises(ExternalAccessError) as denied:
                self.observe(instance["id"], (operation,))
            self.assertEqual(denied.exception.code, "operation-not-allowed")

        self.observe(instance["id"], ("jira.search_metadata",))
        with self.assertRaises(ExternalAccessError) as denied:
            authorize_external_read(
                self.connection,
                instance["id"],
                "jira.create_issue",
                {"summary": "Must not dispatch"},
            )
        self.assertEqual(denied.exception.code, "operation-not-allowed")

    def test_config_reference_shape_rejects_arbitrary_opaque_material(self):
        with self.assertRaises(ExternalAccessError) as denied:
            self.register(
                instance_key="cloud-jira-invalid-ref",
                provider_kind="atlassian_cloud",
                service="jira",
                config_ref="not-a-cloud-reference",
            )
        self.assertEqual(denied.exception.code, "invalid-config-ref")

        with self.assertRaises(ExternalAccessError) as site_denied:
            self.register(
                instance_key="cloud-jira-site",
                provider_kind="atlassian_cloud",
                service="jira",
                config_ref="https://synthetic.invalid/",
            )
        self.assertEqual(site_denied.exception.code, "invalid-config-ref")

    def test_unbound_cloud_instance_can_bind_cloud_id_once(self):
        instance = self.register(
            instance_key="cloud-jira-to-bind",
            provider_kind="atlassian_cloud",
            service="jira",
        )
        inspection = authorize_external_read(
            self.connection,
            instance["id"],
            "capability.inspect_resources",
            {},
        )
        self.assertEqual(
            inspection.tool_name, "atlassian.getAccessibleAtlassianResources"
        )
        self.observe(instance["id"], ("jira.search_metadata",))

        bound = bind_source_instance_config_ref(
            self.connection,
            instance["id"],
            "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAA1",
        )
        self.assertEqual(bound["id"], instance["id"])
        self.assertEqual(
            bound["config_ref"], "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"
        )
        self.assertEqual(
            capability_state(self.connection, instance["id"])["state"], "stale"
        )

        with self.assertRaises(ExternalAccessError) as denied:
            bind_source_instance_config_ref(
                self.connection,
                instance["id"],
                "00000000-0000-4000-8000-000000000002",
            )
        self.assertEqual(
            denied.exception.code, "source-instance-identity-conflict"
        )

    def test_capability_payload_is_canonical_and_contains_no_provider_payload(self):
        instance = self.register()
        self.observe(
            instance["id"],
            ("jira.read_project", "jira.search_metadata"),
        )
        row = self.connection.execute(
            """
            SELECT capability_json FROM external_source_capabilities
            WHERE source_instance_id = ?
            """,
            (instance["id"],),
        ).fetchone()
        payload = json.loads(row["capability_json"])
        self.assertEqual(payload["schema"], CAPABILITY_SCHEMA)
        self.assertEqual(
            payload["operations"],
            ["jira.read_project", "jira.search_metadata"],
        )
        self.assertEqual(
            row["capability_json"],
            json.dumps(
                payload,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

        self.connection.execute(
            """
            UPDATE external_source_capabilities
            SET capability_json = ?
            WHERE source_instance_id = ?
            """,
            (
                json.dumps(
                    {
                        "schema": CAPABILITY_SCHEMA,
                        "operations": ["jira.search_metadata"],
                        "opaque_payload": {"must": "not be accepted"},
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                instance["id"],
            ),
        )
        self.assertEqual(
            capability_state(self.connection, instance["id"])["state"], "error"
        )

        self.observe(instance["id"], ("jira.search_metadata",))
        self.connection.execute(
            """
            UPDATE external_source_capabilities
            SET schema_fingerprint = NULL
            WHERE source_instance_id = ?
            """,
            (instance["id"],),
        )
        self.assertEqual(
            capability_state(self.connection, instance["id"])["state"], "error"
        )

    def test_failure_observation_stores_only_generated_bounded_error_evidence(self):
        instance = self.register()
        state = record_capability_observation(
            self.connection,
            instance["id"],
            availability="error",
            error_code="schema-invalid",
            checked_at="2026-07-23T00:00:00Z",
        )
        self.assertEqual(state["error_code"], "schema-invalid")
        self.assertEqual(
            state["error_message"], "External capability inspection failed."
        )

        with self.assertRaises(ExternalAccessError) as denied:
            record_capability_observation(
                self.connection,
                instance["id"],
                availability="error",
                error_code="invalid code with spaces",
            )
        self.assertEqual(denied.exception.code, "invalid-error-code")

    def test_policy_manifest_contains_only_known_read_targets(self):
        manifest = policy_manifest()
        self.assertEqual(manifest["version"], READ_POLICY_VERSION)
        targets = {
            operation["gateway_target"] or operation["tool_name"]
            for provider in manifest["providers"]
            for operation in provider["operations"]
        }
        forbidden_fragments = (
            "create",
            "update",
            "delete",
            "comment",
            "transition",
            "assign",
            "attachment",
            "linkissues",
            "logwork",
        )
        for target in targets:
            lowered = target.lower()
            self.assertFalse(
                any(fragment in lowered for fragment in forbidden_fragments),
                target,
            )

    def test_missing_cloud_config_ref_fails_before_dispatch(self):
        instance = self.register(
            instance_key="cloud-jira-unbound",
            provider_kind="atlassian_cloud",
            service="jira",
        )
        self.observe(instance["id"], ("jira.search_metadata",))
        with self.assertRaises(ExternalAccessError) as denied:
            authorize_external_read(
                self.connection,
                instance["id"],
                "jira.search_metadata",
                {"jql": "project = SYNTHETIC"},
            )
        self.assertEqual(denied.exception.code, "missing-config-ref")

    def test_direct_config_ref_corruption_fails_before_dispatch(self):
        instance = self.register(
            instance_key="cloud-jira-corrupt-ref",
            provider_kind="atlassian_cloud",
            service="jira",
            config_ref=SYNTHETIC_CLOUD_ID,
        )
        self.observe(instance["id"], ("jira.search_metadata",))
        self.connection.execute(
            """
            UPDATE external_source_instances
            SET config_ref = 'not-a-cloud-reference'
            WHERE id = ?
            """,
            (instance["id"],),
        )
        with self.assertRaises(ExternalAccessError) as denied:
            authorize_external_read(
                self.connection,
                instance["id"],
                "jira.search_metadata",
                {"jql": "project = SYNTHETIC"},
            )
        self.assertEqual(denied.exception.code, "invalid-config-ref")

    def test_schema_constraints_reject_invalid_direct_rows(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO external_source_instances(
                    instance_key, provider_kind, service, display_name
                ) VALUES ('bad-provider', 'unknown', 'jira', 'Synthetic')
                """
            )
        instance = self.register()
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO external_source_capabilities(
                    source_instance_id, policy_version, availability,
                    capability_json, checked_at
                ) VALUES (?, ?, 'invented', '{}', '2026-07-23T00:00:00Z')
                """,
                (instance["id"], READ_POLICY_VERSION),
            )

    def test_normal_startup_adds_tables_without_rewriting_existing_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            database_path = data_dir / "localbrain.db"
            legacy = sqlite3.connect(str(database_path))
            legacy.execute(
                """
                CREATE TABLE external_resources (
                    id INTEGER PRIMARY KEY,
                    resource_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    summary TEXT,
                    source_role TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            legacy.execute(
                """
                INSERT INTO external_resources(
                    id, resource_type, title, url
                ) VALUES (77, 'jira', 'Synthetic existing resource',
                          'https://synthetic.invalid/browse/SYN-77')
                """
            )
            legacy.commit()
            legacy.close()

            synthetic_settings = SimpleNamespace(
                data_dir=data_dir,
                database_path=database_path,
                context_root=data_dir / "context",
            )
            with patch("localbrain.db.settings", synthetic_settings):
                init_db()
                init_db()

            upgraded = sqlite3.connect(str(database_path))
            try:
                tables = {
                    row[0]
                    for row in upgraded.execute(
                        "SELECT name FROM sqlite_schema WHERE type = 'table'"
                    )
                }
                self.assertIn("external_source_instances", tables)
                self.assertIn("external_source_capabilities", tables)
                self.assertEqual(
                    upgraded.execute(
                        "SELECT id, title FROM external_resources WHERE id = 77"
                    ).fetchone(),
                    (77, "Synthetic existing resource"),
                )
                foreign_keys = upgraded.execute(
                    "PRAGMA foreign_key_list(external_source_capabilities)"
                ).fetchall()
                self.assertEqual(
                    [(row[2], row[3], row[4], row[6]) for row in foreign_keys],
                    [
                        (
                            "external_source_instances",
                            "source_instance_id",
                            "id",
                            "CASCADE",
                        )
                    ],
                )
            finally:
                upgraded.close()
