import copy
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import data_model_value_registry as checker  # noqa: E402
from localbrain.value_registry import (  # noqa: E402
    ValueRegistryError,
    display_value_label,
    load_value_registry,
    validate_value_registry,
    visible_value_label,
    visible_value_help,
)


class ValueRegistryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_value_registry()

    def test_registry_covers_nine_subjects_and_current_required_inventories(self):
        self.assertEqual(len(self.registry["subjects"]), 9)
        self.assertEqual(len(self.registry["families"]), 59)
        self.assertFalse(checker.validate_registry(ROOT, self.registry))
        self.assertFalse(checker.check_documents(ROOT))
        self.assertFalse(
            [
                (family["id"], consumer["path"])
                for family in self.registry["families"]
                for consumer in family.get("visible_consumers", [])
                if consumer["state"] != "registry-backed"
            ]
        )

    def test_logical_labels_are_complete_and_internal_values_stay_hidden(self):
        source_type = next(
            family
            for family in self.registry["families"]
            if family["id"] == "context-root.source-type"
        )
        self.assertEqual(source_type["presentation"]["mode"], "logical-label")
        self.assertEqual(source_type["visible_consumers"], [])
        self.assertEqual(
            visible_value_label("atlassian-space.coverage", "selected-content"),
            "선택한 항목만",
        )
        self.assertEqual(
            visible_value_label("external-capability.availability", None),
            "확인 전",
        )
        with self.assertRaisesRegex(ValueRegistryError, "not visible"):
            visible_value_label("session.index-policy", "full")
        self.assertEqual(
            visible_value_label(
                "atlassian-space.coverage",
                "raw-future-token",
                fallback="unknown",
            ),
            "범위 알 수 없음",
        )
        self.assertEqual(
            display_value_label("workspace.exists-now", "unexpected"),
            "표시할 수 없음",
        )
        self.assertEqual(
            visible_value_help("atlassian-space.coverage"),
            "",
        )

    def test_schema_value_drift_is_named(self):
        changed = copy.deepcopy(self.registry)
        family = next(
            item
            for item in changed["families"]
            if item["id"] == "atlassian-space.coverage"
        )
        family["values"].append("future-coverage")
        family["presentation"]["labels"]["future-coverage"] = "새 범위"

        errors = checker.validate_registry(ROOT, changed)

        self.assertTrue(
            any(
                "atlassian-space.coverage differs from atlassian_spaces.coverage"
                in error
                for error in errors
            ),
            errors,
        )

    def test_incomplete_mapping_and_raw_consumer_fallback_fail(self):
        incomplete = copy.deepcopy(self.registry)
        family = next(
            item for item in incomplete["families"] if item["id"] == "source.kind"
        )
        del family["presentation"]["labels"]["context"]
        with self.assertRaisesRegex(ValueRegistryError, "do not cover"):
            validate_value_registry(incomplete)

        raw_consumer = copy.deepcopy(self.registry)
        family = next(
            item for item in raw_consumer["families"] if item["id"] == "source.kind"
        )
        family["visible_consumers"][0]["state"] = "registry-backed"
        family["visible_consumers"][0]["path"] = "README.md"
        errors = checker.validate_registry(ROOT, raw_consumer)
        self.assertTrue(
            any("registry-backed consumer lacks a value_label marker" in error for error in errors),
            errors,
        )

    def test_ordinary_templates_do_not_restore_known_raw_token_output(self):
        template_root = ROOT / "src/localbrain/templates"
        documents = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(template_root.glob("*.html"))
        )
        for raw_expression in (
            r">\s*\{\{\s*workstream\.status\s*\}\}\s*<",
            r">\s*\{\{\s*thread\.status\s*\}\}\s*<",
            r">\s*\{\{\s*run\.status\s*\}\}\s*<",
            r">\s*\{\{\s*run\.runner\s*\}\}\s*<",
            r">\s*\{\{\s*item\.coverage\s*\}\}\s*<",
            r">\s*\{\{\s*item\.freshness\s*\}\}\s*<",
            r">\s*\{\{\s*item\.attention\s*\}\}\s*<",
            r">\s*\{\{\s*target\.outcome\s*\}\}\s*<",
            r">\s*\{\{\s*resource\.resource_type\s*\}\}\s*<",
            r">\s*\{\{\s*source\.status\s*\|\s*replace",
        ):
            self.assertIsNone(re.search(raw_expression, documents))
        self.assertNotIn("status.textContent = current.status;", (
            ROOT / "src/localbrain/static/app.js"
        ).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
