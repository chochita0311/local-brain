"""Local chooser admission, cancellation and recovery without real user files."""

import asyncio
import json
import subprocess
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI, HTTPException, Request

from localbrain.app import picker as local_picker
from localbrain.app.settings import install_settings_routes


class LocalPickerTests(unittest.TestCase):
    def setUp(self):
        platform = patch.object(local_picker.sys, "platform", "darwin")
        platform.start()
        self.addCleanup(platform.stop)

    def test_file_and_folder_return_exact_local_selection(self):
        for directory in (True, False):
            with self.subTest(directory=directory):
                path = "/Users/<example>/문서/Space and ' quotes\nline"
                with patch.object(local_picker.subprocess, "run", return_value=SimpleNamespace(
                        stdout=json.dumps({"path": path}))) as run:
                    self.assertEqual(local_picker.choose_local_path(directory), path)
                args, options = run.call_args
                self.assertEqual(args[0][-1], "directory" if directory else "file")
                self.assertEqual(args[0][0], "/usr/bin/osascript")
                self.assertNotIn(path, args[0])
                self.assertNotIn("shell", options)
                self.assertEqual(options["timeout"], 300)

    def test_cancel_is_empty_selection(self):
        with patch.object(local_picker.subprocess, "run", return_value=SimpleNamespace(stdout='{"path":null}')):
            self.assertIsNone(local_picker.choose_local_path(True))

    def test_errors_do_not_expose_process_output_and_release_chooser(self):
        failures = [
            (subprocess.TimeoutExpired("chooser", 300), 408),
            (subprocess.CalledProcessError(1, "chooser", stderr="private process output"), 503),
            (OSError("private process output"), 503),
        ]
        for failure, status in failures:
            with self.subTest(failure=type(failure).__name__), patch.object(local_picker.subprocess, "run",
                    side_effect=[failure, SimpleNamespace(stdout='{"path":null}')]):
                with self.assertRaises(HTTPException) as caught:
                    local_picker.choose_local_path(True)
                self.assertEqual(caught.exception.status_code, status)
                self.assertNotIn("private process output", caught.exception.detail)
                self.assertIsNone(local_picker.choose_local_path(True))

    def test_invalid_process_results_fail_without_persisting(self):
        for output in ('bad JSON', '{}', '[]', '{"path":42}', '{"path":"relative/path"}', '{"path":"/bad\\u0000path"}'):
            with self.subTest(output=output), patch.object(local_picker.subprocess, "run",
                    return_value=SimpleNamespace(stdout=output)):
                with self.assertRaises(HTTPException) as caught:
                    local_picker.choose_local_path(True)
                self.assertEqual(caught.exception.status_code, 503)

    def test_concurrent_request_does_not_open_another_dialog(self):
        entered, release = threading.Event(), threading.Event()
        results = []
        def chooser(*args, **kwargs):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("test did not release chooser")
            return SimpleNamespace(stdout='{"path":null}')
        with patch.object(local_picker.subprocess, "run", side_effect=chooser) as run:
            first = threading.Thread(target=lambda: results.append(local_picker.choose_local_path(True)))
            first.start()
            try:
                self.assertTrue(entered.wait(5))
                with self.assertRaises(HTTPException) as caught:
                    local_picker.choose_local_path(False)
                self.assertEqual(caught.exception.status_code, 409)
                self.assertEqual(run.call_count, 1)
            finally:
                release.set()
                first.join(5)
            self.assertFalse(first.is_alive())
            self.assertEqual(results, [None])

    def test_non_macos_does_not_start_a_process(self):
        with patch.object(local_picker.sys, "platform", "linux"), patch.object(local_picker.subprocess, "run") as run:
            with self.assertRaises(HTTPException) as caught:
                local_picker.choose_local_path(True)
            self.assertEqual(caught.exception.status_code, 501)
            run.assert_not_called()


class LocalPickerRouteTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        install_settings_routes(app, None)
        route = next(route for route in app.routes if route.path == "/api/settings/choose-path")
        self.assertEqual(route.methods, {"POST"})
        self.endpoint = route.endpoint

    def call(self, value=None, headers=None, host="127.0.0.1:18773", raw=None):
        body = raw if raw is not None else json.dumps({"directory": True} if value is None else value).encode()
        headers = {"host": host, "origin": "http://127.0.0.1:18773", "content-type": "application/json", **(headers or {})}
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        scope = {"type": "http", "scheme": "http", "method": "POST", "path": "/api/settings/choose-path",
                 "query_string": b"", "headers": [(key.encode(), value.encode()) for key, value in headers.items()]}
        return asyncio.run(self.endpoint(Request(scope, receive)))

    def test_valid_boolean_is_forwarded_and_cancel_stays_null(self):
        for directory, selected in ((True, "/Users/<example>/.codex"), (False, None)):
            with patch.object(local_picker, "choose_local_path", return_value=selected) as chooser:
                self.assertEqual(self.call({"directory": directory}), {"path": selected})
                chooser.assert_called_once_with(directory)

    def test_origin_and_request_shape_fail_before_opening_dialog(self):
        cases = [
            ({"headers": {"origin": ""}}, 403),
            ({"headers": {"origin": "null"}}, 403),
            ({"headers": {"origin": "https://example.invalid"}}, 403),
            ({"headers": {"origin": "http://127.0.0.1:18774"}}, 403),
            ({"headers": {"sec-fetch-site": "cross-site"}}, 403),
            ({"host": "example.invalid", "headers": {"origin": "http://example.invalid"}}, 403),
            ({"headers": {"content-type": "text/plain"}}, 415),
            ({"value": {}}, 422),
            ({"value": {"directory": "true"}}, 422),
            ({"value": {"directory": 1}}, 422),
            ({"value": {"directory": True, "script": "untrusted"}}, 422),
            ({"raw": b'[]'}, 422),
            ({"raw": b'{'}, 422),
            ({"raw": b'x' * 65537}, 413),
        ]
        for arguments, status in cases:
            with self.subTest(arguments=arguments), patch.object(local_picker, "choose_local_path") as chooser:
                with self.assertRaises(HTTPException) as caught:
                    self.call(**arguments)
                self.assertEqual(caught.exception.status_code, status)
                chooser.assert_not_called()


if __name__ == "__main__":
    unittest.main()
