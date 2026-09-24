import asyncio
import copy
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from starlette.requests import Request

from auto_work_fixtures import seed
from localbrain import auto_work
from localbrain import main as web
from localbrain.work_reconstruction import ExperimentError, reconstruct
from localbrain.work_reconstruction_preparation import prepare_current


def direct_worker(operation, args):
    return {"prepare": prepare_current, "text": reconstruct}[operation](*args), {}


class AutoWorkTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="localbrain-auto-work-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.database = self.root / "localbrain.db"
        seed(self.database)
        self.now = datetime.now(timezone.utc)
        self.settings = SimpleNamespace(database_path=self.database, data_dir=self.root)
        self.target = self.root / auto_work.DIRECTORY / auto_work.FILENAME

    def prepare(self):
        with patch.object(auto_work, "supervise", side_effect=direct_worker):
            auto_work.prepare_preview(self.database, self.root, now=self.now)

    def view(self, **kwargs):
        return auto_work.preview_page(self.database, self.root, **kwargs)

    def change(self, sql):
        with sqlite3.connect(self.database) as connection:
            connection.execute(sql)

    def request(self, *, method="GET", query=b"", origin=None, host="127.0.0.1", site=None, body=b""):
        headers = []
        if origin is not None:
            headers.append((b"origin", origin.encode()))
        if site is not None:
            headers.append((b"sec-fetch-site", site.encode()))
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        return Request({"type": "http", "method": method, "path": "/auto-work",
                        "query_string": query, "headers": headers, "scheme": "http",
                        "server": (host, 8016), "app": web.app}, receive=receive)

    def render(self, query=b""):
        with patch.object(web, "settings", self.settings):
            return web.auto_work_page(self.request(query=b"mode=sample&" + query))

    def test_preparation_and_browse_preserve_database_and_have_no_quality_claim(self):
        before = self.database.read_bytes()
        self.prepare()
        with patch.object(auto_work, "supervise", side_effect=AssertionError("GET must not analyze")):
            view = self.view()
        self.assertEqual(view["state"], "ready")
        self.assertEqual(view["group_count"], 18)
        self.assertEqual(view["unassigned_count"], 17)
        self.assertEqual(self.database.read_bytes(), before)
        raw = self.target.read_text()
        for forbidden in ("source_path", "root_path", "external_id", "private_quality", "source_body", "/synthetic"):
            self.assertNotIn(forbidden, raw)
        self.assertEqual(self.target.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.target.parent.stat().st_mode & 0o777, 0o700)

    def test_all_groups_and_exact_evidence_are_reachable(self):
        self.prepare()
        first, second = self.view(), self.view(page=2)
        groups = first["groups"] + second["groups"]
        self.assertEqual(len({g["id"] for g in groups}), first["group_count"])
        shared = next(g for g in groups if g["title"] == "검색 응답 · 개선")
        selected = self.view(page=2, flow=shared["id"])
        self.assertEqual(selected["selected"]["sessions"], 16)
        self.assertEqual(len(selected["evidence"]), 16)
        self.assertTrue(all(e["wording"] == "검색 응답을 개선하자." for e in selected["evidence"]))
        self.assertEqual(selected["evidence"][0]["href"], "/sessions/1")
        self.assertEqual(selected["evidence"][0]["start"], 0)

    def test_all_unassigned_pages_and_empty_groups_remain_honest(self):
        self.change("UPDATE activity_events SET text='관찰 문장.\n다른 관찰 문장.'")
        self.prepare()
        first = self.view(view="unassigned")
        second = self.view(view="unassigned", evidence_page=2)
        self.assertEqual(first["group_count"], 0)
        self.assertEqual(first["evidence_total"], 32)
        self.assertEqual(len(first["evidence"]) + len(second["evidence"]), 32)
        self.assertIn("작업이 없다는 뜻은 아닙니다", self.render().body.decode())

    def test_query_normalization_and_missing_selection(self):
        self.prepare()
        for page in ("bad", "-1", "0", "9" * 5000):
            self.assertEqual(self.view(page=page)["page"], 1)
        self.assertEqual(self.view(page=999)["page"], 2)
        self.assertEqual(self.view(view="invalid")["mode"], "flows")
        missing = self.view(flow="not-a-current-flow")
        self.assertTrue(missing["selection_missing"])
        self.assertIsNone(missing["selected"])

    def test_changed_revoked_or_deleted_source_fails_closed(self):
        self.prepare()
        for sql, restore in (
            ("UPDATE activity_events SET text='Changed evidence.' WHERE session_id=1",
             "UPDATE activity_events SET text='검색 응답을 개선하자.\nFix parser 1.\n관찰만 있고 구체적인 목표는 아직 없다.' WHERE session_id=1"),
            ("UPDATE sessions SET index_policy='metadata_only' WHERE id=1", "UPDATE sessions SET index_policy='full' WHERE id=1"),
        ):
            self.change(sql)
            result = self.view()
            self.assertEqual(result["state"], "stale")
            self.assertNotIn("groups", result)
            self.change(restore)
        self.change("DELETE FROM activity_events WHERE session_id=1")
        self.assertEqual(self.view()["state"], "stale")

    def test_expiry_removes_only_owned_result_without_analysis(self):
        self.prepare()
        other = self.target.parent / "unrelated.txt"
        other.write_text("synthetic unrelated owner")
        with patch.object(auto_work, "load_snapshots") as load:
            result = self.view(now=self.now + timedelta(days=8))
            load.assert_not_called()
        self.assertEqual(result["state"], "expired")
        self.assertFalse(self.target.exists())
        self.assertTrue(other.exists())

    def test_missing_preview_does_not_create_or_analyze(self):
        with patch.object(auto_work, "supervise") as run, patch.object(auto_work, "load_snapshots") as load:
            self.assertEqual(self.view()["state"], "missing")
            run.assert_not_called(); load.assert_not_called()
        self.assertFalse(self.target.parent.exists())

    def test_malformed_unknown_or_oversize_file_is_not_overwritten(self):
        self.prepare()
        original = self.target.read_bytes()
        for raw in (b'{"owner":"someone-else"}', b'not json', b' ' * (auto_work.MAX_BYTES + 1)):
            self.target.write_bytes(raw)
            self.assertEqual(self.view()["state"], "error")
            with patch.object(auto_work, "supervise") as run, self.assertRaises(Exception):
                auto_work.prepare_preview(self.database, self.root)
            run.assert_not_called()
            self.assertEqual(self.target.read_bytes(), raw)
        self.target.write_bytes(original)

    def test_symlink_and_world_readable_output_are_rejected(self):
        self.prepare()
        target = self.target.parent / "other.json"
        self.target.rename(target)
        self.target.symlink_to(target)
        self.assertEqual(self.view()["state"], "error")
        with self.assertRaises(OSError):
            self.prepare()
        self.target.unlink()
        target.rename(self.target)
        self.target.chmod(0o644)
        self.assertEqual(self.view()["state"], "error")

    def test_busy_and_failed_refresh_preserve_previous_complete_result(self):
        self.prepare()
        before = self.target.read_bytes()
        with auto_work._lock(self.target.parent):
            with self.assertRaisesRegex(ExperimentError, "PREVIEW_BUSY"):
                self.prepare()
        with patch.object(auto_work.os, "replace", side_effect=OSError("synthetic failure")):
            with self.assertRaises(OSError):
                self.prepare()
        self.assertEqual(self.target.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.target.parent.iterdir()), ["current.json", "preview.lock"])

    def test_fabricated_span_or_wording_is_not_rendered(self):
        self.prepare()
        original = json.loads(self.target.read_text())
        for field, replacement in (("wording", "invented"), ("record_key", "foreign-record"), ("start", -1)):
            value = copy.deepcopy(original)
            value["output"]["flows"][0]["members"][0][field] = replacement
            self.target.write_text(json.dumps(value))
            self.assertEqual(self.view()["state"], "error")

    def test_sidebar_placement_active_state_no_store_and_literal_text(self):
        self.prepare()
        response = self.render(b"view=unassigned")
        body = response.body.decode()
        self.assertLess(body.index('href="/auto-work"'), body.index('href="/workstreams"'))
        self.assertIn('href="/auto-work" aria-current="page"', body)
        self.assertIn('href="/sessions/1"', body)
        self.assertIn("&lt;script&gt;alert", body)
        self.assertNotIn("<script>alert", body)
        self.assertIn("품질 미평가", body)
        self.assertEqual(response.headers["cache-control"], "no-store, private")
        self.assertNotIn('data-api-form', body)

    def test_old_process_template_capability_guard(self):
        self.prepare()
        with patch.dict(web.templates.env.globals, {"auto_work_available": False}):
            body = self.render().body.decode()
        self.assertNotIn('class="lnb-item active" href="/auto-work"', body)
        self.assertIn('href="/workstreams"', body)

    def test_cross_site_or_remote_host_is_rejected_before_data_read(self):
        for request in (self.request(host="example.test"), self.request(site="cross-site")):
            with patch.object(web, "preview_page") as load, self.assertRaises(web.HTTPException):
                web.auto_work_page(request)
            load.assert_not_called()

    def test_refresh_requires_exact_origin_and_no_input(self):
        requests = [self.request(method="POST"), self.request(method="POST", origin="https://example.test"),
                    self.request(method="POST", origin="http://127.0.0.1:8016", body=b"database=foreign"),
                    self.request(method="POST", origin="http://127.0.0.1:8016", site="cross-site")]
        for request in requests:
            with patch.object(web, "_refresh_auto_work") as refresh, self.assertRaises(web.HTTPException):
                asyncio.run(web.auto_work_refresh(request))
            refresh.assert_not_called()

    def test_refresh_redirects_with_fixed_success_busy_failure_notice(self):
        for outcome in ("updated", "busy", "failed"):
            with patch.object(web, "_refresh_auto_work", return_value=outcome):
                response = asyncio.run(web.auto_work_refresh(self.request(method="POST", origin="http://127.0.0.1:8016")))
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/auto-work?mode=sample&notice=" + outcome)

    def test_refresh_subprocess_is_explicit_and_quiet(self):
        with patch.object(web, "settings", self.settings), patch.object(web.subprocess, "run") as run:
            run.return_value.returncode = 3
            self.assertEqual(web._refresh_auto_work(), "busy")
            args, kwargs = run.call_args
            self.assertIn(str(self.database), args[0])
            self.assertEqual(kwargs["stdout"], subprocess.DEVNULL)
            self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
            run.side_effect = subprocess.TimeoutExpired("synthetic", 300)
            self.assertEqual(web._refresh_auto_work(), "failed")

    def test_real_supervised_cli_and_repeat_replacement(self):
        command = [sys.executable, "-B", "-m", "localbrain.auto_work", "--database", str(self.database), "--data-dir", str(self.root)]
        before = self.database.read_bytes()
        for _ in range(2):
            result = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(result.stdout, "AUTO_WORK_PREVIEW_READY\n")
            self.assertEqual(result.stderr, "")
        self.assertEqual(before, self.database.read_bytes())
        self.assertEqual(self.view()["state"], "ready")
        invalid = subprocess.run(command + ["--unknown", "synthetic-private-input"], capture_output=True, text=True, timeout=20)
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(invalid.stdout, "AUTO_WORK_PREVIEW_FAILED\n")
        self.assertEqual(invalid.stderr, "")

    def test_related_document_and_item_destinations_and_revocation(self):
        at = "2026-01-01T09:00:00Z"
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO context_roots(id,path,label) VALUES (1,'/synthetic/docs','Synthetic')")
            connection.execute("""INSERT INTO context_documents(id,source_id,context_root_id,path,relative_path,title,
                body,size_bytes,mtime_ns,content_hash,imported_at)
                VALUES (1,1,1,'/synthetic/docs/goal.md','goal.md','Synthetic document','Improve indexing.',17,1,?,?)""", ("1" * 64, at))
            connection.execute("INSERT INTO external_resources(id,resource_type,title,url) VALUES (1,'wiki','Synthetic wiki','https://example.test/wiki/42')")
            connection.execute("INSERT INTO atlassian_sites(id,normalized_domain,canonical_base_url) VALUES (1,'example.test','https://example.test')")
            connection.execute("""INSERT INTO atlassian_items(external_resource_id,site_id,service,item_type,coverage,remote_id)
                VALUES (1,1,'confluence','confluence_page','indexed','42')""")
            connection.execute("""INSERT INTO atlassian_item_content(external_resource_id,source_format,source_body,source_hash,
                normalized_document_json,normalized_text,normalizer_version,applied_at)
                VALUES (1,'plain_text','Synthetic unadmitted raw payload',?,'{}','Reduce latency.','synthetic',?)""", ("2" * 64, at))
            for number, kind, document, item in ((1, "context_document", 1, None), (2, "atlassian_item", None, 1)):
                identity = "synthetic-reference-{}".format(number)
                connection.execute("""INSERT INTO session_reference_evidence(session_id,source_path,source_line,evidence_ordinal,
                    target_kind,target_key,context_document_id,external_resource_id,evidence_kind,observed_identity,
                    normalized_url,observed_at,extractor_version,evidence_key,first_observed_at,last_observed_at)
                    VALUES (1,'/synthetic/source',1,?,?,?,?,?,'user_mention',?,?,?,'synthetic',?,?,?)""",
                    (number, kind, identity, document, item, identity,
                     "https://example.test/wiki/42" if item else None, at, str(number) * 64, at, at))
        self.prepare()
        groups = self.view()["groups"] + self.view(page=2)["groups"]
        destinations = []
        for title in ("indexing · 개선", "latency · 줄이기"):
            group = next(g for g in groups if g["title"] == title)
            destinations.append(self.view(flow=group["id"])["evidence"][0]["href"])
        self.assertEqual(destinations, ["/documents/1", "/atlassian/items/1"])
        self.assertNotIn("unadmitted raw payload", self.target.read_text())
        self.change("UPDATE context_roots SET enabled=0")
        self.assertEqual(self.view()["state"], "stale")
        self.change("UPDATE context_roots SET enabled=1")
        self.change("UPDATE atlassian_items SET coverage='reference'")
        self.assertEqual(self.view()["state"], "stale")

    def test_assistant_wording_is_not_user_confirmation(self):
        self.change("UPDATE activity_events SET role='assistant' WHERE session_id=1")
        self.prepare()
        group = next(g for g in self.view()["groups"] if g["title"] == "parser 1 · 수정")
        view = self.view(flow=group["id"])
        self.assertEqual(view["evidence"][0]["role"], "어시스턴트의 발언")
        self.assertEqual(view["evidence"][0]["wording"], "Fix parser 1.")


if __name__ == "__main__":
    unittest.main()
