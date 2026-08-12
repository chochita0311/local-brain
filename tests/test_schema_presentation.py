import json
import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import schema_presentation_builder as builder  # noqa: E402
from localbrain.schema_presentation import (  # noqa: E402
    SCHEMA_PRESENTATION_PATH,
    load_schema_presentation,
)


class SchemaPresentationBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = builder.build_manifest(ROOT)

    def test_manifest_has_complete_versioned_baseline(self):
        manifest = self.manifest

        self.assertEqual(manifest["schema"], "localbrain.schema-presentation.v1")
        self.assertIs(manifest["derived"], True)
        self.assertEqual(len(manifest["subjects"]), 9)
        self.assertEqual(len(manifest["tables"]), 39)
        self.assertEqual(
            sum(len(table["columns"]) for table in manifest["tables"]), 426
        )
        self.assertEqual(
            sum(len(table["indexes"]) for table in manifest["tables"]), 38
        )
        self.assertEqual(len(manifest["relationships"]["physical"]), 49)
        self.assertEqual(len(manifest["relationships"]["application"]), 24)

        owned = [
            table_id
            for subject in manifest["subjects"]
            for table_id in subject["table_ids"]
        ]
        table_ids = [table["id"] for table in manifest["tables"]]
        self.assertEqual(owned, table_ids)
        self.assertEqual(len(set(owned)), 39)

        required_semantics = {
            "purpose_and_authority",
            "lifecycle_contract",
            "class",
            "rebuildability",
            "class_contract",
            "producers",
            "consumers",
            "deletion_effect",
            "recovery_path",
            "schema_ownership",
            "documented_constraints",
        }
        for table in manifest["tables"]:
            self.assertTrue(table["columns"], table["id"])
            self.assertTrue(
                required_semantics.issubset(table["semantics"]), table["id"]
            )

    def test_manifest_is_byte_deterministic(self):
        self.assertEqual(builder.manifest_bytes(ROOT), builder.manifest_bytes(ROOT))

    def test_generation_uses_only_in_memory_sqlite_and_skips_data_migrations(self):
        real_connect = sqlite3.connect
        with mock.patch.object(
            builder.sqlite3, "connect", side_effect=real_connect
        ) as connect_mock, mock.patch(
            "localbrain.db._migrate_context_roots",
            side_effect=AssertionError("data migration must stay disabled"),
        ):
            builder.build_manifest(ROOT)

        connect_mock.assert_called_once_with(":memory:")

    def test_mermaid_definitions_are_exact_document_transformations(self):
        entry_path = ROOT / "docs/policies/project/data-model.md"
        entry = entry_path.read_text(encoding="utf-8")
        self.assertEqual(
            self.manifest["global"]["mermaid"],
            builder.mermaid(entry, str(entry_path.relative_to(ROOT))),
        )

        for subject in self.manifest["subjects"]:
            document = (ROOT / subject["document"]).read_text(encoding="utf-8")
            self.assertEqual(
                subject["mermaid"],
                builder.mermaid(document, subject["document"]),
            )

    def test_missing_semantic_field_fails_with_owner_and_table(self):
        entry = (ROOT / "docs/policies/project/data-model.md").read_text(
            encoding="utf-8"
        )
        lifecycle = builder.parse_lifecycle(entry)
        subject = builder.parse_subjects(entry)[0]
        table = subject["table_ids"][0]
        document = (ROOT / subject["document"]).read_text(encoding="utf-8")
        malformed = re.sub(r"^- Lifecycle: .+\n", "", document, count=1, flags=re.M)

        with self.assertRaisesRegex(
            builder.PresentationBuildError,
            rf"{re.escape(subject['document'])}: {table} missing Lifecycle",
        ):
            builder.parse_table_semantics(
                malformed, subject["document"], table, lifecycle[table]
            )

    def test_wrapped_semantic_and_constraint_fields_preserve_continuations(self):
        document = """# Subject

### `sample_table`

- Purpose and authority: first purpose line
  continues with authority detail.
- Lifecycle: durable local state
- Producers: first producer
  and second producer.
- Consumers: one consumer
- Relations and deletion: retained on delete
- Recovery: restore from source
- DDL ownership: `schema.sql` owns the table

| Column | Contract |
| --- | --- |
| `id` | Stable identity. |

Constraints: first constraint
  and a second constraint.
"""
        lifecycle = {
            "class": "Durable",
            "rebuildability": "not-rebuildable",
            "class_contract": "Preserve local state.",
        }

        semantics = builder.parse_table_semantics(
            document, "docs/example.md", "sample_table", lifecycle
        )

        self.assertEqual(
            semantics["purpose_and_authority"],
            "first purpose line continues with authority detail.",
        )
        self.assertEqual(
            semantics["producers"], "first producer and second producer."
        )
        self.assertEqual(
            semantics["documented_constraints"],
            "first constraint and a second constraint.",
        )

    def test_check_rejects_missing_and_stale_outputs(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            builder, "validate_mermaid"
        ):
            output = Path(directory) / "schema-presentation.json"
            with self.assertRaisesRegex(
                builder.PresentationBuildError, "presentation is missing"
            ):
                builder.check_manifest(output, ROOT)

            output.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(
                builder.PresentationBuildError, "presentation is stale"
            ):
                builder.check_manifest(output, ROOT)

    def test_serialized_manifest_excludes_runtime_and_network_values(self):
        serialized = builder.manifest_bytes(ROOT).decode("utf-8")
        self.assertNotIn("/Users/", serialized)
        self.assertNotIn("http://", serialized)
        self.assertNotIn("https://", serialized)
        for source in self.manifest["baseline"]["sources"]:
            self.assertFalse(Path(source["path"]).is_absolute(), source["path"])


class SchemaPresentationLoaderTests(unittest.TestCase):
    def test_packaged_manifest_loads(self):
        result = load_schema_presentation()

        self.assertTrue(result.available)
        self.assertIsNone(result.error_code)
        self.assertEqual(
            result.manifest["schema"], "localbrain.schema-presentation.v1"
        )

    def test_missing_manifest_is_bounded_unavailable_state(self):
        with tempfile.TemporaryDirectory() as directory:
            result = load_schema_presentation(Path(directory) / "missing.json")

        self.assertFalse(result.available)
        self.assertIsNone(result.manifest)
        self.assertEqual(result.error_code, "manifest-unavailable")

    def test_malformed_or_wrong_version_manifest_is_bounded_invalid_state(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "schema-presentation.json"
            output.write_text("not-json", encoding="utf-8")
            malformed = load_schema_presentation(output)

            document = json.loads(SCHEMA_PRESENTATION_PATH.read_text(encoding="utf-8"))
            document["schema"] = "localbrain.schema-presentation.v2"
            output.write_text(json.dumps(document), encoding="utf-8")
            wrong_version = load_schema_presentation(output)

            document = json.loads(SCHEMA_PRESENTATION_PATH.read_text(encoding="utf-8"))
            del document["global"]
            output.write_text(json.dumps(document), encoding="utf-8")
            missing_required_shape = load_schema_presentation(output)

            document = json.loads(SCHEMA_PRESENTATION_PATH.read_text(encoding="utf-8"))
            document["subjects"][0]["table_ids"].pop()
            output.write_text(json.dumps(document), encoding="utf-8")
            invalid_ownership = load_schema_presentation(output)

        for result in (
            malformed,
            wrong_version,
            missing_required_shape,
            invalid_ownership,
        ):
            self.assertFalse(result.available)
            self.assertIsNone(result.manifest)
            self.assertEqual(result.error_code, "manifest-invalid")


if __name__ == "__main__":
    unittest.main()
