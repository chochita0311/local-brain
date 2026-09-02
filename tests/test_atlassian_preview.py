import json
import sqlite3
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from localbrain.atlassian import (
    apply_atlassian_target_result,
    create_or_reuse_atlassian_stub,
    normalize_atlassian_url,
)
from localbrain.atlassian_browse import (
    AtlassianBrowseError,
    atlassian_item_preview,
    normalize_browse_filters,
    normalize_browse_structure,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


def target_result(*, metadata, content):
    return {
        "target_id": "synthetic-preview-target",
        "locator": {
            "kind": "url",
            "value": "https://jira.preview.test/browse/PREVIEW-1",
        },
        "outcome": "changed",
        "requests": [
            {
                "request_id": "synthetic-preview-request",
                "logical_operation": "jira.read_description",
                "outcome": "changed",
                "identity": {
                    "remote_id": "remote-preview-1",
                    "remote_key": "PREVIEW-1",
                },
                "metadata": metadata,
                "content": content,
                "remote_version": "7",
                "remote_updated_at": "2026-08-28T12:00:00Z",
                "content_hash": None,
                "error": None,
            }
        ],
    }


class AtlassianPreviewTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.source_id = int(
            self.connection.execute(
                """
                INSERT INTO external_source_instances(
                    instance_key, provider_kind, service, display_name
                ) VALUES ('preview-jira', 'mcp_gateway', 'jira',
                          'Preview Jira')
                """
            ).lastrowid
        )
        item = create_or_reuse_atlassian_stub(
            self.connection,
            source_instance_id=self.source_id,
            url="https://jira.preview.test/browse/PREVIEW-1",
            title="Preview local title",
            coverage="indexed",
            observed_at="2026-08-28T10:00:00Z",
        )
        self.item_id = int(item["external_resource_id"])
        self.site_id = int(item["site_id"])
        apply_atlassian_target_result(
            self.connection,
            self.item_id,
            target_result(
                metadata={
                    "summary": "Preview remote title",
                    "details": {"phrase": "metadata exact phrase"},
                },
                content="Exact body phrase " + ("🙂" * 1_300),
            ),
            checked_at="2026-08-28T12:30:00Z",
            source_format="plain_text",
        )
        self.connection.execute(
            """
            INSERT INTO atlassian_item_local_state(
                external_resource_id, note, updated_at
            ) VALUES (?, ?, '2026-08-28T12:31:00Z')
            """,
            (self.item_id, "Local exact note phrase " + ("界" * 700)),
        )
        alias = normalize_atlassian_url(
            "https://jira.preview.test/issues/?key=ALIAS-1"
        )
        self.connection.execute(
            """
            INSERT INTO atlassian_item_urls(
                external_resource_id, site_id, url_role, observed_url,
                normalized_url, first_observed_at, last_observed_at
            ) VALUES (?, ?, 'alias', ?, ?,
                      '2026-08-28T12:32:00Z', '2026-08-28T12:32:00Z')
            """,
            (
                self.item_id,
                self.site_id,
                alias.observed_url,
                alias.normalized_url,
            ),
        )
        self.alias_url = alias.observed_url
        self.topic_id = self._classification(
            "topic", "Preview Topic", "preview topic"
        )
        self.tag_id = self._classification("tag", "Preview Tag", "preview tag")
        self.workstream_id = int(
            self.connection.execute(
                "INSERT INTO workstreams(name) VALUES ('Preview workstream')"
            ).lastrowid
        )
        self.connection.execute(
            """
            INSERT INTO workstream_links(
                workstream_id, entity_type, entity_id, relation_type
            ) VALUES (?, 'external', ?, 'related-to')
            """,
            (self.workstream_id, str(self.item_id)),
        )

    def tearDown(self):
        self.connection.close()

    def _classification(self, kind, name, normalized_name):
        classification_id = int(
            self.connection.execute(
                """
                INSERT INTO atlassian_classifications(
                    kind, name, normalized_name
                ) VALUES (?, ?, ?)
                """,
                (kind, name, normalized_name),
            ).lastrowid
        )
        self.connection.execute(
            """
            INSERT INTO atlassian_item_classifications(
                external_resource_id, classification_id
            ) VALUES (?, ?)
            """,
            (self.item_id, classification_id),
        )
        return classification_id

    def _refresh_run(self, run_id, created_at, target_ids):
        manifest = {
            "targets": [{"target_id": target_id} for target_id in target_ids]
        }
        self.connection.execute(
            """
            INSERT INTO maintenance_runs(
                id, task_type, runner, status, source_snapshot_json, created_at
            ) VALUES (?, 'external_source_sync', 'codex', 'completed', ?, ?)
            """,
            (run_id, json.dumps(manifest), created_at),
        )
        self.connection.execute(
            """
            INSERT INTO external_sync_runs(
                maintenance_run_id, source_instance_id, source_kind, service,
                requested_scope_kind, selected_target_count,
                manifest_schema_version, read_policy_version
            ) VALUES (?, ?, 'atlassian', 'jira', 'item', ?,
                      'synthetic-v1', 'synthetic-v1')
            """,
            (run_id, self.source_id, len(target_ids)),
        )

    def test_structure_normalization_is_targeted_and_shared_with_preview(self):
        space_id = int(
            self.connection.execute(
                """
                INSERT INTO atlassian_spaces(
                    site_id, source_instance_id, service, remote_id,
                    space_key, name, canonical_url, coverage
                ) VALUES (?, ?, 'jira', 'targeted-project', 'TARGETED',
                          'Targeted Project',
                          'https://jira.preview.test/projects/TARGETED',
                          'selected-content')
                """,
                (self.site_id, self.source_id),
            ).lastrowid
        )
        filters = normalize_browse_filters(
            {"service": "jira", "space_id": space_id}
        )
        self.assertIsNone(filters["site_id"])
        statements = []
        self.connection.set_trace_callback(statements.append)
        try:
            with patch(
                "localbrain.atlassian_browse._item_rows",
                side_effect=AssertionError("broad item rows"),
            ):
                normalized = normalize_browse_structure(
                    self.connection, filters
                )
        finally:
            self.connection.set_trace_callback(None)
        self.assertIsNone(filters["site_id"])
        self.assertEqual(normalized["site_id"], self.site_id)
        sql = [" ".join(statement.lower().split()) for statement in statements]
        space_reads = [
            statement
            for statement in sql
            if " from atlassian_spaces" in statement
        ]
        item_reads = [
            statement
            for statement in sql
            if " from atlassian_items" in statement
        ]
        self.assertEqual(len(space_reads), 1)
        self.assertIn("where id =", space_reads[0])
        self.assertEqual(len(item_reads), 1)
        self.assertIn("where site_id =", item_reads[0])
        self.assertIn("select distinct service", item_reads[0])

        with self.assertRaisesRegex(
            AtlassianBrowseError,
            "Space is unavailable for the selected service",
        ):
            normalize_browse_structure(
                self.connection,
                normalize_browse_filters(
                    {"service": "confluence", "space_id": space_id}
                ),
            )
        with self.assertRaisesRegex(
            AtlassianBrowseError,
            "Site is unavailable for the selected service",
        ):
            normalize_browse_structure(
                self.connection,
                normalize_browse_filters(
                    {"service": "confluence", "site_id": self.site_id}
                ),
            )

        self.connection.execute(
            """
            UPDATE atlassian_items SET space_id = ?
            WHERE external_resource_id = ?
            """,
            (space_id, self.item_id),
        )
        self.assertTrue(
            atlassian_item_preview(
                self.connection,
                self.item_id,
                {"service": "jira", "space_id": space_id},
            )["eligible"]
        )

    def test_exact_query_and_every_inventory_filter_define_eligibility(self):
        for query in (
            "remote-preview-1",
            "Preview remote title",
            "metadata exact phrase",
            "Exact body phrase",
            "Local exact note phrase",
            "Preview Topic",
            "Preview Tag",
            self.alias_url,
        ):
            with self.subTest(query=query):
                self.assertTrue(
                    atlassian_item_preview(
                        self.connection, self.item_id, {"q": query}
                    )["eligible"]
                )
        self.assertFalse(
            atlassian_item_preview(
                self.connection,
                self.item_id,
                {"q": "body Exact phrase"},
            )["eligible"]
        )

        current_freshness = atlassian_item_preview(
            self.connection, self.item_id
        )["freshness"]
        filters = {
            "service": "jira",
            "source_instance_id": self.source_id,
            "site_id": self.site_id,
            "item_type": "jira_issue",
            "coverage": "indexed",
            "freshness": current_freshness,
            "attention": "normal",
            "topic_id": self.topic_id,
            "tag_id": self.tag_id,
            "workstream_id": self.workstream_id,
        }
        self.assertTrue(
            atlassian_item_preview(
                self.connection, self.item_id, filters
            )["eligible"]
        )
        other_freshness = next(
            value
            for value in ("unknown", "current", "due", "stale", "unavailable")
            if value != current_freshness
        )
        mismatches = {
            "service": "confluence",
            "source_instance_id": self.source_id + 100,
            "site_id": self.site_id + 100,
            "space_id": 999,
            "item_type": "confluence_page",
            "coverage": "metadata",
            "freshness": other_freshness,
            "attention": "ignored",
            "topic_id": self.topic_id + 100,
            "tag_id": self.tag_id + 100,
            "workstream_id": self.workstream_id + 100,
        }
        for field, value in mismatches.items():
            with self.subTest(field=field):
                self.assertFalse(
                    atlassian_item_preview(
                        self.connection, self.item_id, {field: value}
                    )["eligible"]
                )

        structural = {
            "site_id": self.site_id,
            "structural_scope": "url:jira:PREVIEW",
        }
        structural_preview = atlassian_item_preview(
            self.connection, self.item_id, structural
        )
        self.assertTrue(structural_preview["eligible"])
        self.assertEqual(
            (
                structural_preview["container_kind"],
                structural_preview["container_label"],
                structural_preview["container_service"],
                structural_preview["container_structural_scope"],
            ),
            ("url", "PREVIEW", "jira", "url:jira:PREVIEW"),
        )
        self.assertFalse(
            atlassian_item_preview(
                self.connection,
                self.item_id,
                {
                    "site_id": self.site_id,
                    "structural_scope": "unclassified",
                },
            )["eligible"]
        )
        space_id = int(
            self.connection.execute(
                """
                INSERT INTO atlassian_spaces(
                    site_id, source_instance_id, service, remote_id,
                    space_key, name, canonical_url, coverage
                ) VALUES (?, ?, 'jira', 'preview-project', 'PREVIEW',
                          'Preview Project',
                          'https://jira.preview.test/projects/PREVIEW',
                          'selected-content')
                """,
                (self.site_id, self.source_id),
            ).lastrowid
        )
        self.connection.execute(
            """
            UPDATE atlassian_items SET space_id = ?
            WHERE external_resource_id = ?
            """,
            (space_id, self.item_id),
        )
        self.assertFalse(
            atlassian_item_preview(
                self.connection, self.item_id, structural
            )["eligible"]
        )
        self.assertTrue(
            atlassian_item_preview(
                self.connection, self.item_id, {"space_id": space_id}
            )["eligible"]
        )

        self.connection.execute(
            """
            UPDATE atlassian_items SET attention = 'archived'
            WHERE external_resource_id = ?
            """,
            (self.item_id,),
        )
        self.assertFalse(
            atlassian_item_preview(self.connection, self.item_id)["eligible"]
        )
        self.assertTrue(
            atlassian_item_preview(
                self.connection, self.item_id, {"attention": "all"}
            )["eligible"]
        )
        self.assertTrue(
            atlassian_item_preview(
                self.connection, self.item_id, {"attention": "archived"}
            )["eligible"]
        )

    def test_projection_caps_and_orders_every_bounded_group(self):
        long_key = "a" * 120
        long_child = "b" * 60
        metadata = {
            "title": "Excluded title",
            "summary": "Excluded summary",
            "a.b": {
                "slash\\key": [True, False, None, {}, [], 12.5, "z" * 300]
            },
            long_key: {long_child: "short"},
            "array": [1],
            "array[0]": 2,
            **{"field_{:02d}".format(i): "value-{}".format(i) for i in range(14)},
        }
        self.connection.execute(
            """
            UPDATE atlassian_item_remote_state SET metadata_json = ?
            WHERE external_resource_id = ?
            """,
            (json.dumps(metadata), self.item_id),
        )
        for index in range(34):
            self._classification(
                "topic",
                "Topic {:02d}".format(index),
                "topic-{:02d}".format(index),
            )
            self._classification(
                "tag",
                "Tag {:02d}".format(index),
                "tag-{:02d}".format(index),
            )

        source_id = int(
            self.connection.execute(
                """
                INSERT INTO sources(kind, name, root_path)
                VALUES ('preview-evidence', 'Preview evidence',
                        '/synthetic/preview')
                """
            ).lastrowid
        )
        session_id = int(
            self.connection.execute(
                """
                INSERT INTO sessions(
                    source_id, external_id, source_path, title,
                    session_class, session_role, index_policy
                ) VALUES (?, 'preview-session', '/synthetic/preview.jsonl',
                          'Preview evidence session', 'work', 'primary', 'full')
                """,
                (source_id,),
            ).lastrowid
        )
        for index in range(1, 8):
            observed_at = "2026-08-28T12:{:02d}:00Z".format(index)
            self.connection.execute(
                """
                INSERT INTO atlassian_item_evidence(
                    external_resource_id, session_id, source_path,
                    source_channel, source_event_id, source_line, url_ordinal,
                    observed_url, normalized_url, observed_at,
                    extractor_version, evidence_key,
                    first_observed_at, last_observed_at
                ) VALUES (?, ?, '/synthetic/preview.jsonl', 'visible_text',
                          ?, ?, ?, ?, ?, ?, 'synthetic-v1', ?, ?, ?)
                """,
                (
                    self.item_id,
                    session_id,
                    "event-{}".format(index),
                    index,
                    index,
                    "https://jira.preview.test/browse/PREVIEW-1",
                    "https://jira.preview.test/browse/PREVIEW-1",
                    observed_at,
                    "{:064x}".format(index),
                    observed_at,
                    observed_at,
                ),
            )

        organization_names = ["Preview workstream"]
        for index in range(6):
            name = "Organization {:02d}".format(5 - index)
            organization_names.append(name)
            workstream_id = int(
                self.connection.execute(
                    "INSERT INTO workstreams(name) VALUES (?)", (name,)
                ).lastrowid
            )
            if index % 2:
                thread_id = int(
                    self.connection.execute(
                        """
                        INSERT INTO threads(workstream_id, title, position)
                        VALUES (?, ?, ?)
                        """,
                        (workstream_id, "Thread {}".format(index), index),
                    ).lastrowid
                )
                self.connection.execute(
                    """
                    INSERT INTO thread_links(
                        thread_id, entity_type, entity_id, relation_type
                    ) VALUES (?, 'external', ?, 'evidence')
                    """,
                    (thread_id, str(self.item_id)),
                )
            else:
                self.connection.execute(
                    """
                    INSERT INTO workstream_links(
                        workstream_id, entity_type, entity_id, relation_type
                    ) VALUES (?, 'external', ?, 'evidence')
                    """,
                    (workstream_id, str(self.item_id)),
                )

        preview = atlassian_item_preview(self.connection, self.item_id)
        self.assertTrue(preview["eligible"])
        self.assertEqual(preview["remote_id"], "remote-preview-1")
        self.assertEqual(preview["remote_version"], "7")
        self.assertEqual(preview["last_attempted_at"], "2026-08-28T12:30:00Z")
        self.assertEqual(preview["last_successful_at"], "2026-08-28T12:30:00Z")

        self.assertEqual(len(preview["metadata_summary"]), 12)
        self.assertEqual(preview["metadata_summary_total"], 21)
        self.assertTrue(preview["metadata_summary_truncated"])
        paths = [item["path"] for item in preview["metadata_summary"]]
        self.assertEqual(paths, sorted(paths))
        self.assertIn(r"a\.b.slash\\key[0]", paths)
        self.assertIn(r"a\.b.slash\\key[1]", paths)
        self.assertIn(r"a\.b.slash\\key[5]", paths)
        self.assertIn(r"a\.b.slash\\key[6]", paths)
        self.assertIn("array[0]", paths)
        self.assertIn(r"array\[0\]", paths)
        self.assertNotIn(r"a\.b.slash\\key[2]", paths)
        self.assertNotIn(r"a\.b.slash\\key[3]", paths)
        self.assertNotIn(r"a\.b.slash\\key[4]", paths)
        self.assertNotIn("title", paths)
        self.assertNotIn("summary", paths)
        values = {item["path"]: item["value"] for item in preview["metadata_summary"]}
        self.assertEqual(values[r"a\.b.slash\\key[0]"], "true")
        self.assertEqual(values[r"a\.b.slash\\key[1]"], "false")
        self.assertEqual(values[r"a\.b.slash\\key[5]"], "12.5")
        self.assertEqual(values["array[0]"], "1")
        self.assertEqual(values[r"array\[0\]"], "2")
        long_entry = next(
            item for item in preview["metadata_summary"] if item["path_truncated"]
        )
        self.assertEqual(len(long_entry["path"]), 160)
        self.assertTrue(long_entry["path"].endswith("…"))
        self.assertFalse(long_entry["value_truncated"])
        long_value_entry = next(
            item
            for item in preview["metadata_summary"]
            if item["path"] == r"a\.b.slash\\key[6]"
        )
        self.assertFalse(long_value_entry["path_truncated"])
        self.assertEqual(len(long_value_entry["value"]), 240)
        self.assertTrue(long_value_entry["value"].endswith("…"))
        self.assertTrue(long_value_entry["value_truncated"])

        self.assertEqual(len(preview["content_excerpt"]), 1_200)
        self.assertEqual(preview["content_excerpt"].count("…"), 1)
        self.assertTrue(preview["content_truncated"])
        self.assertEqual(len(preview["note_excerpt"]), 600)
        self.assertEqual(preview["note_excerpt"].count("…"), 1)
        self.assertTrue(preview["note_truncated"])
        preview["content_excerpt"].encode("utf-8")

        for key in ("topics", "tags"):
            with self.subTest(key=key):
                self.assertEqual(preview[key]["total"], 35)
                self.assertEqual(len(preview[key]["items"]), 30)
                self.assertTrue(preview[key]["truncated"])
                order = [
                    (item["normalized_name"], item["id"])
                    for item in preview[key]["items"]
                ]
                self.assertEqual(order, sorted(order))

        self.assertEqual(preview["evidence"]["total"], 7)
        self.assertEqual(len(preview["evidence"]["items"]), 5)
        self.assertTrue(preview["evidence"]["truncated"])
        self.assertEqual(
            [item["source_line"] for item in preview["evidence"]["items"]],
            [7, 6, 5, 4, 3],
        )
        self.assertEqual(preview["organization"]["total"], 7)
        self.assertEqual(len(preview["organization"]["items"]), 5)
        self.assertTrue(preview["organization"]["truncated"])
        self.assertEqual(
            [
                item["workstream_name"]
                for item in preview["organization"]["items"]
            ],
            sorted(organization_names)[:5],
        )

    def test_missing_and_ineligible_items_avoid_expensive_or_broad_reads(self):
        statements = []
        before_changes = self.connection.total_changes
        self.connection.set_trace_callback(statements.append)
        forbidden = (
            "_item_rows",
            "_classification_maps",
            "_workstream_membership_map",
            "_item_url_map",
            "browse_inventory",
            "atlassian_item_detail",
        )
        try:
            with ExitStack() as stack:
                for symbol in forbidden:
                    stack.enter_context(
                        patch(
                            "localbrain.atlassian_browse.{}".format(symbol),
                            side_effect=AssertionError(symbol),
                        )
                    )
                eligible = atlassian_item_preview(
                    self.connection,
                    self.item_id,
                    {"q": "PREVIEW-1"},
                )
                self.assertTrue(eligible["eligible"])
                self.assertIsNone(
                    atlassian_item_preview(self.connection, self.item_id + 99_999)
                )
        finally:
            self.connection.set_trace_callback(None)
        self.assertEqual(self.connection.total_changes, before_changes)

        normalized = [" ".join(statement.lower().split()) for statement in statements]
        for statement in normalized:
            if " from atlassian_items" in statement:
                self.assertIn(
                    "where atlassian_items.external_resource_id =", statement
                )
            if " from atlassian_item_classifications" in statement:
                self.assertIn(
                    "atlassian_item_classifications.external_resource_id =",
                    statement,
                )
            if " from atlassian_item_evidence" in statement:
                self.assertIn(
                    "atlassian_item_evidence.external_resource_id =", statement
                )
            if (
                " from workstream_links" in statement
                or " from thread_links" in statement
            ):
                self.assertIn("entity_id =", statement)
        joined = "\n".join(normalized)
        for forbidden_read in (
            "source_body",
            "normalized_document_json",
            "activity_events",
            "source_files",
            "search_index",
            "external_source_capabilities",
        ):
            self.assertNotIn(forbidden_read, joined)

        ineligible_statements = []
        self.connection.set_trace_callback(ineligible_statements.append)
        try:
            ineligible = atlassian_item_preview(
                self.connection,
                self.item_id,
                {"service": "confluence"},
            )
        finally:
            self.connection.set_trace_callback(None)
        self.assertFalse(ineligible["eligible"])
        self.assertNotIn("evidence", ineligible)
        self.assertNotIn("organization", ineligible)
        self.assertNotIn("recent_refresh_run", ineligible)
        ineligible_sql = "\n".join(ineligible_statements).lower()
        self.assertNotIn("atlassian_item_evidence", ineligible_sql)
        self.assertNotIn("maintenance_runs", ineligible_sql)
        self.assertNotIn("workstream_links", ineligible_sql)
        self.assertNotIn("ranked_classifications", ineligible_sql)

        unmatched_statements = []
        self.connection.set_trace_callback(unmatched_statements.append)
        try:
            unmatched = atlassian_item_preview(
                self.connection,
                self.item_id,
                {"q": "not present anywhere"},
            )
        finally:
            self.connection.set_trace_callback(None)
        self.assertFalse(unmatched["eligible"])
        unmatched_sql = "\n".join(unmatched_statements).lower()
        self.assertIn("atlassian_item_classifications", unmatched_sql)
        self.assertNotIn("ranked_classifications", unmatched_sql)
        self.assertNotIn("atlassian_item_evidence", unmatched_sql)
        self.assertNotIn("maintenance_runs", unmatched_sql)
        self.assertNotIn("workstream_links", unmatched_sql)

    def test_query_eligibility_projects_only_bounded_content_and_note(self):
        self.connection.execute(
            """
            UPDATE atlassian_item_content
            SET normalized_text = ?
            WHERE external_resource_id = ?
            """,
            ("prefix " + ("body " * 300) + "deep content phrase", self.item_id),
        )
        self.connection.execute(
            """
            UPDATE atlassian_item_local_state
            SET note = ?
            WHERE external_resource_id = ?
            """,
            ("prefix " + ("note " * 180) + "deep note phrase", self.item_id),
        )
        statements = []
        self.connection.set_trace_callback(statements.append)
        try:
            content_match = atlassian_item_preview(
                self.connection, self.item_id, {"q": "deep content phrase"}
            )
            note_match = atlassian_item_preview(
                self.connection, self.item_id, {"q": "deep note phrase"}
            )
        finally:
            self.connection.set_trace_callback(None)

        self.assertTrue(content_match["eligible"])
        self.assertNotIn("deep content phrase", content_match["content_excerpt"])
        self.assertTrue(content_match["content_truncated"])
        self.assertTrue(note_match["eligible"])
        self.assertNotIn("deep note phrase", note_match["note_excerpt"])
        self.assertTrue(note_match["note_truncated"])
        sql = "\n".join(" ".join(value.lower().split()) for value in statements)
        self.assertIn(
            "localbrain_atlassian_exact_phrase( "
            "atlassian_item_content.normalized_text )",
            sql,
        )
        self.assertIn(
            "localbrain_atlassian_exact_phrase( "
            "atlassian_item_local_state.note )",
            sql,
        )
        self.assertIn(
            "substr( atlassian_item_content.normalized_text, 1, 1201 )",
            sql,
        )
        self.assertIn(
            "substr( atlassian_item_local_state.note, 1, 601 )",
            sql,
        )
        self.assertNotIn(
            "atlassian_item_content.normalized_text as normalized_text",
            sql,
        )
        self.assertNotIn(
            "atlassian_item_local_state.note as note",
            sql,
        )

    def test_refresh_history_is_explicitly_limited_to_latest_200_global_runs(self):
        target_id = "atlassian-item-{}".format(self.item_id)
        base = datetime(2026, 8, 20, tzinfo=timezone.utc)
        self._refresh_run(
            "lb-preview-old-match",
            (base - timedelta(minutes=1)).isoformat(),
            [target_id],
        )
        for index in range(200):
            self._refresh_run(
                "lb-preview-unrelated-{:03d}".format(index),
                (base + timedelta(minutes=index)).isoformat(),
                ["atlassian-item-unrelated-{}".format(index)],
            )
        self.connection.execute(
            """
            UPDATE maintenance_runs SET source_snapshot_json = '[]'
            WHERE id = 'lb-preview-unrelated-199'
            """
        )

        absent = atlassian_item_preview(self.connection, self.item_id)
        self.assertIsNone(absent["recent_refresh_run"])
        self.assertEqual(absent["history_scope"], "recent-200")
        self.assertFalse(absent["history_complete"])
        self.assertEqual(
            absent["history_absence"], "not found in recent history"
        )

        tied_at = (base + timedelta(minutes=300)).isoformat()
        self._refresh_run("lb-preview-a-match", tied_at, [target_id])
        self._refresh_run("lb-preview-z-match", tied_at, [target_id])
        present = atlassian_item_preview(self.connection, self.item_id)
        self.assertEqual(
            present["recent_refresh_run"]["id"], "lb-preview-z-match"
        )
        self.assertNotIn(
            "source_snapshot_json", present["recent_refresh_run"]
        )
        self.assertIsNone(present["history_absence"])
        self.assertEqual(present["history_scope"], "recent-200")
        self.assertFalse(present["history_complete"])


if __name__ == "__main__":
    unittest.main()
