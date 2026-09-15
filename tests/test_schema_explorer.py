import json
import unittest
from pathlib import Path
from unittest import mock

from starlette.requests import Request

from localbrain.main import app, schema_page
from localbrain.schema_explorer import (
    INVALID_AREA_MESSAGE,
    INVALID_TABLE_MESSAGE,
    TABLE_REQUIRES_AREA_MESSAGE,
    build_schema_explorer_view,
)
from localbrain.schema_presentation import SchemaPresentationLoad


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "src/localbrain/schema-presentation.json"


class SchemaExplorerViewModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_global_state_exposes_complete_baseline_and_subject_order(self):
        view = build_schema_explorer_view(self.manifest)

        self.assertTrue(view["available"])
        self.assertEqual(view["mode"], "global")
        self.assertEqual(view["baseline"]["object_count"], 43)
        self.assertEqual(view["baseline"]["physical_foreign_key_count"], 57)
        self.assertEqual(len(view["subjects"]), 10)
        self.assertEqual(
            [subject["id"] for subject in view["subjects"]],
            [subject["id"] for subject in self.manifest["subjects"]],
        )
        self.assertEqual(view["diagram"], self.manifest["global"]["mermaid"])

    def test_every_area_and_owned_table_has_canonical_state(self):
        tables = {table["id"]: table for table in self.manifest["tables"]}
        for subject in self.manifest["subjects"]:
            area_view = build_schema_explorer_view(
                self.manifest, area=subject["id"]
            )
            self.assertEqual(area_view["mode"], "area")
            self.assertEqual(area_view["selected_subject"]["id"], subject["id"])
            self.assertEqual(
                [table["id"] for table in area_view["area_tables"]],
                subject["table_ids"],
            )
            self.assertEqual(area_view["diagram"], subject["mermaid"])

            for table_id in subject["table_ids"]:
                table_view = build_schema_explorer_view(
                    self.manifest, area=subject["id"], table=table_id
                )
                self.assertEqual(table_view["mode"], "table")
                self.assertEqual(table_view["selected_table"], tables[table_id])
                self.assertTrue(
                    next(
                        item for item in table_view["area_tables"]
                        if item["id"] == table_id
                    )["current"]
                )
                for relation in (
                    table_view["relationships"]["physical"]
                    + table_view["relationships"]["application"]
                ):
                    self.assertIn(
                        table_id,
                        {relation["source_table"], relation["target_table"]},
                    )

    def test_invalid_query_state_is_bounded_and_does_not_echo_input(self):
        invalid_area = build_schema_explorer_view(
            self.manifest, area="not-a-real-area", table="private-query-value"
        )
        self.assertEqual(invalid_area["mode"], "global")
        self.assertEqual(invalid_area["notice"]["message"], INVALID_AREA_MESSAGE)
        self.assertNotIn("not-a-real-area", str(invalid_area))
        self.assertNotIn("private-query-value", str(invalid_area))

        subject = self.manifest["subjects"][0]
        other_subject = self.manifest["subjects"][1]
        invalid_table = build_schema_explorer_view(
            self.manifest,
            area=subject["id"],
            table=other_subject["table_ids"][0],
        )
        self.assertEqual(invalid_table["mode"], "area")
        self.assertIsNone(invalid_table["selected_table"])
        self.assertEqual(invalid_table["notice"]["message"], INVALID_TABLE_MESSAGE)

        missing_area = build_schema_explorer_view(self.manifest, table="sessions")
        self.assertEqual(
            missing_area["notice"]["message"], TABLE_REQUIRES_AREA_MESSAGE
        )


class SchemaExplorerRouteTests(unittest.TestCase):
    @staticmethod
    def request(query_string: bytes = b"") -> Request:
        return Request(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": "/schema",
                "raw_path": b"/schema",
                "query_string": query_string,
                "headers": [],
                "client": ("test", 50000),
                "server": ("test", 80),
                "root_path": "",
                "app": app,
                "router": app.router,
            }
        )

    def test_route_consumes_package_without_database_access(self):
        with mock.patch(
            "localbrain.main.connect",
            side_effect=AssertionError("Schema must not open the runtime database"),
        ):
            response = schema_page(self.request())

        self.assertEqual(response.status_code, 200)
        html = response.body.decode("utf-8")
        self.assertNotIn("/Users/", html)
        self.assertIn('href="/schema" aria-current="page"', html)
        self.assertIn('data-localbrain-mermaid="owned"', html)
        self.assertIn('data-localbrain-mermaid-layout="elk"', html)
        self.assertIn('data-localbrain-mermaid-source', html)
        self.assertIn('data-schema-layout-status', html)
        self.assertIn('data-schema-link', html)
        self.assertIn('data-schema-diagram-viewport', html)
        self.assertIn('data-schema-zoom-controls', html)
        self.assertIn('data-schema-zoom-out', html)
        self.assertIn('data-schema-zoom-reset', html)
        self.assertIn('data-schema-zoom-in', html)
        self.assertIn('data-schema-zoom-fit', html)
        self.assertIn('Ctrl/Cmd + 휠', html)

    def test_route_renders_canonical_table_detail_and_bounded_invalid_state(self):
        response = schema_page(
            self.request(b"area=source-registry-and-scans&table=sources"),
            area="source-registry-and-scans",
            table="sources",
        )
        html = response.body.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn('href="/schema?area=source-registry-and-scans"', html)
        self.assertIn(
            'href="/schema?area=source-registry-and-scans&amp;table=sources"', html
        )
        self.assertIn(
            'id="schema-table-title" tabindex="-1" data-schema-focus="table"><code>sources</code>',
            html,
        )
        self.assertIn("Purpose", html)
        self.assertIn("Columns", html)
        self.assertIn("Keys and constraints", html)
        self.assertIn("Explicit indexes", html)
        self.assertIn("Relationships", html)

        invalid = schema_page(
            self.request(b"area=private-query-value&table=another-private-value"),
            area="private-query-value",
            table="another-private-value",
        ).body.decode("utf-8")
        self.assertIn('data-schema-notice="invalid-area"', invalid)
        self.assertNotIn("private-query-value", invalid)
        self.assertNotIn("another-private-value", invalid)

    def test_route_returns_bounded_unavailable_state(self):
        with mock.patch(
            "localbrain.schema_explorer.load_schema_presentation",
            return_value=SchemaPresentationLoad(
                available=False, error_code="manifest-unavailable"
            ),
        ):
            response = schema_page(self.request())

        self.assertEqual(response.status_code, 200)
        html = response.body.decode("utf-8")
        self.assertIn("manifest-unavailable", html)
        self.assertNotIn("sqlite", html.lower())


if __name__ == "__main__":
    unittest.main()
