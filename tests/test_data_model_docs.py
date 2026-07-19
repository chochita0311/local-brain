import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DataModelDocsTests(unittest.TestCase):
    def test_effective_schema_and_owner_docs_remain_in_sync(self):
        result = subprocess.run(
            [sys.executable, "scripts/check-data-model-docs.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
