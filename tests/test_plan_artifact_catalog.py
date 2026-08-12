import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build-plan-artifact-catalog.py"
SPEC = importlib.util.spec_from_file_location("plan_artifact_catalog", SCRIPT)
catalog = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(catalog)


class PlanArtifactCatalogTests(unittest.TestCase):
    def test_catalog_is_deterministic_and_links_every_non_template_artifact(self):
        first = catalog.render(ROOT)
        self.assertEqual(first, catalog.render(ROOT))

        for _, directory in catalog.ARTIFACT_DIRS:
            for path in (ROOT / "docs/plans" / directory).glob("*.md"):
                if not path.name.startswith("template-"):
                    self.assertIn(
                        f"({path.relative_to(ROOT / 'docs/plans').as_posix()})", first
                    )

    def test_catalog_rejects_an_artifact_without_h1(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for _, artifact_dir in catalog.ARTIFACT_DIRS:
                (root / "docs/plans" / artifact_dir).mkdir(parents=True)
            (root / "docs/plans/prd/prd-0000-invalid.md").write_text(
                "## Missing title\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(catalog.CatalogError, "has no H1"):
                catalog.render(root)


if __name__ == "__main__":
    unittest.main()
