import json
import re
import sqlite3
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import schema_presentation_builder as builder  # noqa: E402
from schema_migration_sources import migration_source_digest, migration_source_files


class SchemaPresentationBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = builder.build_manifest(ROOT)

    def test_manifest_has_complete_versioned_baseline(self):
        manifest = self.manifest

        self.assertEqual(manifest["schema"], "localbrain.schema-presentation.v1")
        self.assertIs(manifest["derived"], True)
        self.assertEqual(len(manifest["subjects"]), 11)
        self.assertEqual(len(manifest["tables"]), 53)
        self.assertEqual(
            sum(len(table["columns"]) for table in manifest["tables"]), 560
        )
        self.assertEqual(
            sum(len(table["indexes"]) for table in manifest["tables"]), 51
        )
        self.assertEqual(len(manifest["relationships"]["physical"]), 66)
        self.assertEqual(len(manifest["relationships"]["application"]), 29)

        owned = [
            table_id
            for subject in manifest["subjects"]
            for table_id in subject["table_ids"]
        ]
        table_ids = [table["id"] for table in manifest["tables"]]
        self.assertEqual(owned, table_ids)
        self.assertEqual(len(set(owned)), 53)
        self.assertTrue({"personal_insight_runs", "skill_observations", "session_chart_preferences"}.issubset(owned))

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

    def test_domain_migration_change_is_fingerprinted_without_entrypoint_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            owner = Path("crates/core/src/backend")
            (root / owner / "storage").mkdir(parents=True)
            shutil.copyfile(ROOT / owner / "db.rs", root / owner / "db.rs")
            shutil.copyfile(ROOT / owner / "storage/migrations.rs", root / owner / "storage/migrations.rs")
            shutil.copytree(ROOT / owner / "storage/migrations", root / owner / "storage/migrations")
            before = migration_source_digest(root)
            entrypoint = (root / owner / "db.rs").read_bytes()
            migration = root / owner / "storage/migrations/resources.rs"
            migration.write_text(migration.read_text() + "\n// Synthetic migration revision\n")
            self.assertNotEqual(migration_source_digest(root), before)
            self.assertEqual((root / owner / "db.rs").read_bytes(), entrypoint)
            self.assertIn(str(owner / "storage/migrations/resources.rs"),
                          {row["path"] for row in migration_source_files(root)})

    def test_generation_rehydrates_native_disposable_schema_in_memory(self):
        statements = builder.effective_schema_sql(ROOT)
        real_connect = sqlite3.connect
        with mock.patch.object(builder, "effective_schema_sql", return_value=statements) as native, \
                mock.patch.object(builder.sqlite3, "connect", side_effect=real_connect) as connection:
            builder.build_manifest(ROOT)
        native.assert_called_once_with(ROOT)
        connection.assert_called_once_with(":memory:")

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

    def test_serialized_manifest_excludes_runtime_values_and_unreviewed_urls(self):
        serialized = builder.manifest_bytes(ROOT).decode("utf-8")
        self.assertNotIn("/Users/", serialized)
        self.assertNotIn("http://", serialized)
        # Reviewed public citations in code-owned semantics are provenance, not runtime URLs.
        public_citations = {
            "https://developers.openai.com/api/docs/pricing",
            "https://openai.com/api-fast-mode/",
            "https://platform.claude.com/docs/en/about-claude/pricing",
            "https://github.com/ccusage/ccusage/blob/v20.0.17/rust/crates/ccusage/src/pricing.rs",
            "https://developers.openai.com/api/docs/models/gpt-6.1-sol",
            "https://developers.openai.com/api/docs/models/gpt-6.1-terra",
            "https://developers.openai.com/api/docs/changelog",
        }
        self.assertEqual(set(re.findall(r'https://[^\s)"\\]+', serialized)), public_citations)
        for source in self.manifest["baseline"]["sources"]:
            self.assertFalse(Path(source["path"]).is_absolute(), source["path"])


if __name__ == "__main__":
    unittest.main()
