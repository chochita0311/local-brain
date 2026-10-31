"""Optional implementations can be absent during real app startup and requests."""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi import Request

from localbrain.app.forms import FormError, MAX_FORM_BYTES, bounded_urlencoded_form


ROOT = Path(__file__).resolve().parents[1]


class FormContractTests(unittest.TestCase):
    def decode(self, body, content_type="application/x-www-form-urlencoded", **kwargs):
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        request = Request({"type": "http", "headers": [(b"content-type", content_type.encode())]}, receive)
        return asyncio.run(bounded_urlencoded_form(request, **kwargs))

    def test_blank_last_value_and_feature_selected_multi_fields(self):
        body = b"q=first&q=&item_id=1&item_id=2&topic_id=3&topic_id=4"
        self.assertEqual(self.decode(body), {"q": "", "item_id": "2", "topic_id": "4"})
        self.assertEqual(self.decode(body, multiple_fields={"item_id", "topic_id"}),
                         {"q": "", "item_id": ["1", "2"], "topic_id": ["3", "4"]})
        self.assertEqual(self.decode(b"q=%ED%95%9C%EA%B8%80", " Application/X-WWW-Form-Urlencoded ; charset=utf-8"), {"q": "한글"})

    def test_inclusive_size_and_field_limits(self):
        self.assertEqual(len(self.decode(b"q=" + b"a" * (MAX_FORM_BYTES - 2))["q"]), MAX_FORM_BYTES - 2)
        self.assertEqual(len(self.decode(b"&".join(b"f%d=x" % n for n in range(128)))), 128)
        for body in (b"q=" + b"a" * (MAX_FORM_BYTES - 1), b"&".join(b"f%d=x" % n for n in range(129))):
            with self.assertRaises(FormError):
                self.decode(body)

    def test_encoding_and_invalid_utf8_keep_form_error_contract(self):
        for body, content_type, message in ((b"{}", "application/json", "Form encoding is unsupported"),
                                           (b"q=\xff", "application/x-www-form-urlencoded", "Form data is invalid")):
            with self.assertRaisesRegex(FormError, message) as error:
                self.decode(body, content_type)
            self.assertEqual(error.exception.code, "invalid-form")


class FeatureAssemblyTests(unittest.TestCase):
    def test_each_optional_package_and_all_optional_packages_can_be_absent(self):
        features = ("atlassian", "workstreams", "workflow", "auto_work", "context_search")
        for edition in ("web", "desktop"):
            for omitted in [(name,) for name in features] + [features]:
                with self.subTest(edition=edition, omitted=omitted), tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(ROOT / "src"),
                           "LOCALBRAIN_EDITION": edition, "LOCALBRAIN_DESKTOP_TOKEN": "synthetic-assembly-token",
                           "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_HUB_CACHE": str(root / "hub"),
                           **{"LOCALBRAIN_" + key: str(root / path) for key, path in (
                               ("DATA_DIR", "data"), ("CACHE_DIR", "cache"), ("DEVELOPMENT_DIR", "development"),
                               ("CONTEXT_ROOT", "context"), ("CLAUDE_ROOT", "missing-claude"), ("CODEX_ROOT", "codex/sessions"))}}
                    result = subprocess.run([sys.executable, str(ROOT / "tests/feature_assembly_probe.py"), json.dumps(omitted)],
                                            cwd=ROOT, env=env, text=True, capture_output=True, timeout=45)
                    self.assertEqual(result.returncode, 0, result.stderr)
