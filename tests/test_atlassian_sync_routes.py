import asyncio
import json
import sqlite3
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, quote_plus, urlsplit

from fastapi import HTTPException
from starlette.requests import Request

from localbrain.main import (
    ATLASSIAN_SYNC_PARTIAL,
    _ATLASSIAN_SYNC_RECEIPTS,
    _ATLASSIAN_SYNC_RECEIPT_LOCK,
    _atlassian_page_context,
    _store_atlassian_sync_receipt,
    _verified_atlassian_sync_report,
    app,
    atlassian_sync,
    templates,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


def _report(status="complete"):
    return {
        "status": status,
        "sources": {
            "considered": 0,
            "eligible": 0,
            "scanned": 0,
            "partial": 0,
            "unavailable": 0,
            "failed": 0,
            "excluded": 0,
        },
        "items": {"new": 0, "reused": 0},
        "evidence": {"new": 0, "reused": 0, "removed": 0},
        "structure_references": {"new": 0, "reused": 0},
        "structure_evidence": {"new": 0, "reused": 0, "removed": 0},
        "site_only": 0,
        "candidate_skips": {
            "key_only": 0,
            "unsafe_url": 0,
            "unsupported_locator": 0,
            "unconfigured_domain": 0,
            "ambiguous_site": 0,
            "invalid_location": 0,
        },
        "scope_limits": {
            "session_projection_sources": 0,
            "session_reference_overflow": 0,
            "document_url_overflow": 0,
        },
        "source_outcomes": [],
    }


class AtlassianSyncRouteTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        with _ATLASSIAN_SYNC_RECEIPT_LOCK:
            _ATLASSIAN_SYNC_RECEIPTS.clear()

    def tearDown(self):
        with _ATLASSIAN_SYNC_RECEIPT_LOCK:
            _ATLASSIAN_SYNC_RECEIPTS.clear()
        self.connection.close()

    def _request(
        self,
        body,
        *,
        enhanced=False,
        content_type="application/x-www-form-urlencoded",
    ):
        delivered = False

        async def receive():
            nonlocal delivered
            if delivered:
                return {"type": "http.disconnect"}
            delivered = True
            return {
                "type": "http.request",
                "body": body.encode("utf-8"),
                "more_body": False,
            }

        headers = [(b"content-type", content_type.encode("ascii"))]
        if enhanced:
            headers.append(
                (b"x-localbrain-partial", ATLASSIAN_SYNC_PARTIAL.encode())
            )
        return Request(
            {
                "type": "http",
                "app": app,
                "method": "POST",
                "path": "/atlassian/sync",
                "headers": headers,
                "query_string": b"",
                "server": ("test", 80),
                "client": ("test", 1),
                "scheme": "http",
            },
            receive,
        )

    def _get_request(self):
        return Request(
            {
                "type": "http",
                "app": app,
                "method": "GET",
                "path": "/atlassian",
                "headers": [],
                "query_string": b"",
                "server": ("test", 80),
                "client": ("test", 1),
                "scheme": "http",
            }
        )

    def test_enhanced_post_returns_wrapped_report_and_busy_uses_409(self):
        complete = _report()
        request = self._request("return_to=%2Fatlassian", enhanced=True)
        with patch("localbrain.main.connect", return_value=self.connection), patch(
            "localbrain.main._execute_atlassian_evidence_sync",
            return_value=complete,
        ) as execute:
            response = asyncio.run(atlassian_sync(request))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.body),
            {"report": complete, "return_to": "/atlassian?view=all"},
        )
        self.assertEqual(response.headers["vary"], "X-LocalBrain-Partial")
        execute.assert_called_once_with()

        busy = _report("busy")
        request = self._request("return_to=%2Fatlassian", enhanced=True)
        with patch("localbrain.main.connect", return_value=self.connection), patch(
            "localbrain.main._execute_atlassian_evidence_sync",
            return_value=busy,
        ):
            response = asyncio.run(atlassian_sync(request))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            json.loads(response.body),
            {"report": busy, "return_to": "/atlassian?view=all"},
        )

        failed = _report("failed")
        request = self._request("return_to=%2Fatlassian", enhanced=True)
        with patch("localbrain.main.connect", return_value=self.connection), patch(
            "localbrain.main._execute_atlassian_evidence_sync",
            return_value=failed,
        ):
            response = asyncio.run(atlassian_sync(request))
        self.assertEqual(response.status_code, 200)

    def test_strict_form_rejects_unknown_repeated_and_oversized_before_work(self):
        invalid_bodies = (
            "return_to=%2Fatlassian&unknown=1",
            "return_to=%2Fatlassian&return_to=%2Fatlassian%3Fview%3Djira",
            "unknown=1",
            "return_to=%FF",
            "return_to=" + ("x" * 8_300),
        )
        for body in invalid_bodies:
            with self.subTest(body_length=len(body)), patch(
                "localbrain.main._execute_atlassian_evidence_sync"
            ) as execute:
                response = asyncio.run(
                    atlassian_sync(self._request(body, enhanced=True))
                )
                self.assertEqual(response.status_code, 422)
                self.assertEqual(
                    json.loads(response.body)["detail"]["code"],
                    "invalid-form",
                )
                execute.assert_not_called()

        with patch(
            "localbrain.main._execute_atlassian_evidence_sync"
        ) as execute, self.assertRaises(HTTPException) as raised:
            asyncio.run(
                atlassian_sync(
                    self._request(
                        "return_to=%2Fatlassian&return_to=%2Fatlassian"
                    )
                )
            )
        self.assertEqual(raised.exception.status_code, 422)
        execute.assert_not_called()

        with patch(
            "localbrain.main._execute_atlassian_evidence_sync"
        ) as execute:
            response = asyncio.run(
                atlassian_sync(
                    self._request(
                        "return_to=%2Fatlassian",
                        enhanced=True,
                        content_type="application/x-www-form-urlencoded-invalid",
                    )
                )
            )
        self.assertEqual(response.status_code, 422)
        execute.assert_not_called()

    def test_ordinary_post_redirects_to_bound_receipt_and_result_anchor(self):
        report = _report("partial")
        report["sources"]["considered"] = 2
        token = "A" * 32
        return_to = "/atlassian?view=jira&q=alpha"
        body = "return_to={}".format(quote_plus(return_to))
        with patch("localbrain.main.connect", return_value=self.connection), patch(
            "localbrain.main._execute_atlassian_evidence_sync",
            return_value=report,
        ), patch("localbrain.main.secrets.token_urlsafe", return_value=token):
            response = asyncio.run(atlassian_sync(self._request(body)))

        self.assertEqual(response.status_code, 303)
        location = response.headers["location"]
        parsed = urlsplit(location)
        self.assertEqual(parsed.path, "/atlassian")
        self.assertEqual(parsed.fragment, "atlassian-sync-result")
        self.assertEqual(parse_qs(parsed.query)["sync_receipt"], [token])
        self.assertEqual(
            _verified_atlassian_sync_report(token, return_to), report
        )
        self.assertIsNone(
            _verified_atlassian_sync_report(token, "/atlassian")
        )

        context = _atlassian_page_context(
            self.connection,
            request=self._get_request(),
            selected_view="jira",
            browse_values={"q": "alpha"},
            sync_receipt=token,
        )
        self.assertEqual(context["sync_return_to"], return_to)
        self.assertEqual(context["sync_report"], report)
        idle = _atlassian_page_context(
            self.connection,
            request=self._get_request(),
            selected_view="jira",
            browse_values={"q": "alpha"},
            sync_receipt="malformed",
        )
        self.assertIsNone(idle["sync_report"])

    def test_no_script_receipt_renders_item_counts_and_zero_guidance(self):
        idle = _atlassian_page_context(
            self.connection,
            request=self._get_request(),
            selected_view="all",
        )
        return_to = idle["sync_return_to"]
        changed_report = _report()
        changed_report["items"] = {"new": 3, "reused": 4}
        changed_report["structure_references"] = {"new": 2, "reused": 5}
        changed_report["structure_evidence"] = {
            "new": 6,
            "reused": 7,
            "removed": 1,
        }
        changed_report["site_only"] = 8
        changed_token = _store_atlassian_sync_receipt(
            changed_report, return_to
        )
        changed_context = _atlassian_page_context(
            self.connection,
            request=self._get_request(),
            selected_view="all",
            sync_receipt=changed_token,
        )

        changed_html = templates.TemplateResponse(
            "atlassian.html", changed_context
        ).body.decode("utf-8")

        self.assertIn("새 링크/문서 3", changed_html)
        self.assertIn("기존 링크/문서 4", changed_html)
        self.assertIn("새 구조 참조 2", changed_html)
        self.assertIn("기존 구조 참조 5", changed_html)
        self.assertIn("도메인/서비스만 확인 8", changed_html)
        self.assertIn("구조 근거 새 6개 · 기존 7개 · 정리 1개", changed_html)
        self.assertNotIn("새로 반영할 로컬 근거가 없습니다.", changed_html)

        zero_token = _store_atlassian_sync_receipt(_report(), return_to)
        zero_context = _atlassian_page_context(
            self.connection,
            request=self._get_request(),
            selected_view="all",
            sync_receipt=zero_token,
        )
        zero_html = templates.TemplateResponse(
            "atlassian.html", zero_context
        ).body.decode("utf-8")
        self.assertIn("새 링크/문서 0", zero_html)
        self.assertIn("기존 링크/문서 0", zero_html)
        self.assertIn("새로 반영할 로컬 근거가 없습니다.", zero_html)

    def test_external_return_is_sanitized_before_and_after_work(self):
        token = "B" * 32
        body = "return_to={}".format(
            quote_plus("https://outside.example.test/atlassian")
        )
        with patch("localbrain.main.connect", return_value=self.connection), patch(
            "localbrain.main._execute_atlassian_evidence_sync",
            return_value=_report(),
        ), patch("localbrain.main.secrets.token_urlsafe", return_value=token):
            response = asyncio.run(atlassian_sync(self._request(body)))
        parsed = urlsplit(response.headers["location"])
        self.assertEqual(parsed.path, "/atlassian")
        query = parse_qs(parsed.query)
        self.assertEqual(query["view"], ["all"])
        self.assertEqual(query["sync_receipt"], [token])

    def test_receipts_are_bounded_immutable_and_expire_without_consumption(self):
        tokens = ["{:032d}".format(index) for index in range(33)]
        source_report = _report()
        with patch(
            "localbrain.main.secrets.token_urlsafe", side_effect=tokens
        ), patch("localbrain.main.time.monotonic", return_value=100.0):
            for _index in range(33):
                last = _store_atlassian_sync_receipt(
                    source_report, "/atlassian"
                )
        source_report["status"] = "failed"
        self.assertEqual(len(_ATLASSIAN_SYNC_RECEIPTS), 32)
        self.assertIsNone(
            _verified_atlassian_sync_report(tokens[0], "/atlassian")
        )
        with patch("localbrain.main.time.monotonic", return_value=399.0):
            self.assertEqual(
                _verified_atlassian_sync_report(last, "/atlassian")["status"],
                "complete",
            )
            self.assertIsNotNone(
                _verified_atlassian_sync_report(last, "/atlassian")
            )
        with patch("localbrain.main.time.monotonic", return_value=400.0):
            self.assertIsNone(
                _verified_atlassian_sync_report(last, "/atlassian")
            )

    def test_sync_action_runs_off_event_loop_on_its_own_worker(self):
        started = threading.Event()
        release = threading.Event()
        worker_threads = []
        event_loop_thread = threading.get_ident()

        class WorkerConnection:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        worker_connection = WorkerConnection()
        connection_threads = []

        def connect_for_thread():
            thread_id = threading.get_ident()
            connection_threads.append(thread_id)
            if thread_id == event_loop_thread:
                return self.connection
            return worker_connection

        def slow_action(connection):
            self.assertIs(connection, worker_connection)
            worker_threads.append(threading.get_ident())
            started.set()
            release.wait(timeout=2)
            return _report()

        async def scenario():
            request = self._request("return_to=%2Fatlassian", enhanced=True)
            task = asyncio.create_task(atlassian_sync(request))
            for _index in range(500):
                if started.is_set():
                    break
                await asyncio.sleep(0.001)
            self.assertTrue(started.is_set())
            await asyncio.sleep(0)
            release.set()
            return await task

        with patch("localbrain.main.connect", side_effect=connect_for_thread), patch(
            "localbrain.main.sync_atlassian_local_evidence",
            side_effect=slow_action,
        ):
            try:
                response = asyncio.run(scenario())
            finally:
                release.set()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(worker_threads), 1)
        self.assertNotEqual(worker_threads[0], event_loop_thread)
        self.assertIn(worker_threads[0], connection_threads)
        self.assertTrue(worker_connection.closed)


if __name__ == "__main__":
    unittest.main()
