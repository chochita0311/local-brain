"""Fresh-process synthetic probe used by package-absence and runtime checks."""

import asyncio
import contextlib
import gc
import hashlib
import importlib.abc
import io
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlsplit
from unittest.mock import patch


def main():
    default_delivery = sys.argv[1] == "defaults"
    omitted = {"context_search", "google_drive"} if default_delivery else set(json.loads(sys.argv[1]))
    if os.environ.get("LOCALBRAIN_EDITION") == "desktop":
        omitted |= {"atlassian", "workstreams", "workflow", "auto_work", "context_search", "google_drive"}
    blocked = {"localbrain." + name for name in omitted}
    if {"atlassian", "workstreams"} <= omitted:
        blocked.add("localbrain.maintenance")

    class Boundary(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if any(fullname == name or fullname.startswith(name + ".") for name in blocked):
                raise AssertionError("Excluded implementation imported: " + fullname)

    sys.meta_path.insert(0, Boundary())
    from localbrain.app.application import create_app
    from localbrain.foundation.config import cache_directory, settings
    from localbrain.foundation.files import private_database, private_directory
    from localbrain.foundation.paths import hub_cache_root
    from localbrain.foundation.preferences import read_preferences, save_preferences
    from localbrain.ingest.extensions import observe_ingestion
    from localbrain.ingest.scanner import scan_context_root, scan_session_sources
    from localbrain.local_context.service import add_context_root
    from localbrain.persistence.db import connect, init_db, transaction
    from localbrain.sources.settings import source_inventory, update_source

    settings.codex_root.mkdir(parents=True)
    settings.context_root.mkdir(parents=True)
    (settings.context_root / "example.md").write_text("# Synthetic document\nAssembly context evidence.")
    records = [
        {"type": "session_meta", "timestamp": "2026-10-30T01:00:00Z",
         "payload": {"id": "synthetic-assembly", "cwd": "/synthetic/project"}},
        {"type": "event_msg", "timestamp": "2026-10-30T01:01:00Z",
         "payload": {"type": "user_message", "message":
                     "Synthetic assembly https://example.test/wiki/spaces/DEMO/pages/123"}},
        {"type": "event_msg", "timestamp": "2026-10-30T01:02:00Z",
         "payload": {"type": "token_count", "info": {"last_token_usage": {
             "input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 5,
             "reasoning_output_tokens": 1, "total_tokens": 15}}}},
    ]
    (settings.codex_root / "example.jsonl").write_text(
        "\n".join(json.dumps(row) for row in records) + "\n")
    init_db()
    inventory = source_inventory(settings)
    update_source({"revision": inventory["revision"], "provider_kind": "codex",
                   "display_label": "Synthetic", "root": str(settings.codex_root),
                   "agent_home": str(settings.codex_root.parent)}, settings)
    prefs = read_preferences(settings)
    save_preferences({"session_sync_enabled": False, "context_sync_enabled": False},
                     prefs["revision"], settings)
    with transaction() as connection:
        connection.execute("""INSERT INTO maintenance_runs(id,task_type,status,stream_path)
            VALUES ('synthetic-stale-run','organize_resources','running','/synthetic/stream'),
                   ('synthetic-non-task',NULL,'running','/synthetic/stream'),
                   ('synthetic-no-stream','organize_resources','running',NULL)""")

    def seed_old_caches(base):
        for name, contents in {
            "session-simulation": {
                "owner.json": json.dumps({"owner": "localbrain.session-simulation.v1", "database": "a" * 64,
                                          "expires_at": "2000-01-01T00:00:00+00:00"}),
                "writer.lock": "", "state.sqlite3": "synthetic old vectors", "progress.json": "{}",
            },
            # An omitted feature must not need to decode even malformed old state.
            "auto-work-preview": {"preview.lock": "", "current.json": "synthetic opaque preview"},
        }.items():
            folder = private_directory(base / name)
            for filename, value in contents.items():
                path = folder / filename
                path.write_text(value)
                path.chmod(0o600)

    def old_cache_snapshot():
        return {str(path): (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode)
                for base in (cache_directory(settings), settings.data_dir)
                for name in ("session-simulation", "auto-work-preview")
                for path in (base / name).iterdir()}

    for base in (cache_directory(settings), settings.data_dir):
        seed_old_caches(base)
    old_caches = old_cache_snapshot()

    retained = {}
    if default_delivery:
        drive = private_directory(settings.data_dir / "google-drive") / "sync.sqlite3"
        with sqlite3.connect(drive) as connection:
            connection.executescript("CREATE TABLE state(key TEXT PRIMARY KEY,value TEXT NOT NULL);"
                                     "CREATE TABLE items(namespace TEXT,key TEXT,value TEXT,PRIMARY KEY(namespace,key));"
                                     "PRAGMA user_version=1;")
            connection.executemany("INSERT INTO state VALUES (?,?)", [
                ("connections", json.dumps([{"id": "synthetic", "root_id": "synthetic-root"}])),
                ("jobs:synthetic", json.dumps({"upload": {"selected": True, "auto": True,
                                                        "interval": 15, "sources": [1]}})),
            ])
        copy = private_directory(settings.data_dir / "external-sources/google-drive/synthetic/peer") / "example.md"
        copy.write_text("# Retained synthetic Drive copy\n")
        retained = {path: path.read_bytes() for path in (drive, copy)}

    packages = {"atlassian", "workstreams", "workflow", "auto_work", "context_search", "google_drive"}
    app = create_app() if default_delivery else create_app(feature_packages=packages - omitted)

    if os.environ.get("LOCALBRAIN_EDITION") == "desktop":
        assert not app.state.feature_packages
        assert app.state.task_runner is app.state.maintain_feature_cache is None
        assert getattr(app.state, "document_memberships", None) is None
        assert getattr(app.state, "session_workflow_available", None) is None

    async def request(url, method="GET", body=b"", content_type="application/x-www-form-urlencoded"):
        parsed = urlsplit(url)
        output = []
        received = False

        async def receive():
            nonlocal received
            if received:
                return {"type": "http.disconnect"}
            received = True
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            output.append(message)

        await app({"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
                   "method": method, "path": parsed.path, "raw_path": parsed.path.encode(),
                   "query_string": parsed.query.encode(), "scheme": "http",
                   "headers": [(b"host", b"127.0.0.1"), (b"content-type", content_type.encode()),
                               (b"authorization", b"Bearer synthetic-assembly-token")],
                   "server": ("127.0.0.1", 8000), "client": ("127.0.0.1", 1234)}, receive, send)
        start = next(item for item in output if item["type"] == "http.response.start")
        text = b"".join(item.get("body", b"") for item in output).decode()
        for path in (settings.data_dir, settings.cache_dir, settings.development_dir,
                     settings.codex_root, settings.context_root, hub_cache_root()):
            text = text.replace(str(path), "<" + path.name + ">")
        text = re.sub(r'(/static/[^"<>]*\?v=)\d+', r'\1<asset-version>', text)
        if parsed.path == "/api/settings/storage":
            value = json.loads(text)
            value.pop("free_bytes")
            text = json.dumps(value, sort_keys=True)
        return start["status"], text, [(k.decode(), v.decode()) for k, v in start["headers"]
                                     if k != b"content-length"]

    async def run():
        report = {"responses": {}, "routes": [
            (r.path, sorted(r.methods), r.name) for r in app.routes if hasattr(r, "methods")]}
        async with app.router.lifespan_context(app):
            if default_delivery:
                assert app.state.context_search is app.state.google_drive is None
                assert app.state.context_search_factory is app.state.google_drive_factory is None
                assert not settings.development_dir.exists()
                for url, method in (("/context-search", "GET"), ("/api/context-search/status", "GET"),
                                    ("/api/context-search/answer", "POST"), ("/api/context-search/unload", "POST"),
                                    ("/api/settings/google-drive", "GET"), ("/api/settings/google-drive/connections", "POST"),
                                    ("/api/settings/google-drive/synthetic/jobs/upload/run", "POST"),
                                    ("/api/settings/model/4b/install", "POST"), ("/api/settings/model/8b/cancel", "POST")):
                    assert (await request(url, method, b"{}", "application/json"))[0] == 404, url
                positive = {**app.state.model_setup.status(), "generation_models": [
                    {"key": "4b", "available": True, "registered": True},
                    {"key": "8b", "available": True, "cached": True},
                ]}
                with patch.object(app.state.model_setup, "status", return_value=positive):
                    status, body, _ = await request("/api/settings")
                    assert status == 200 and json.loads(body)["model"]["generation_models"] == []
                for url in ("/sessions", "/settings", "/help", "/help/settings", "/help/search"):
                    status, body, _ = await request(url)
                    assert status == 200
                    assert "Context Search" not in body and "Google Drive" not in body, (
                        url, [(term, body[max(0, body.find(term) - 80):body.find(term) + 120])
                              for term in ("Context Search", "Google Drive") if term in body])
                    assert "data-generation-model=" not in body and "google-drive.js" not in body, url
                assert (await request("/api/settings/model/cancel", "POST", b"{}", "application/json"))[0] == 200
            with observe_ingestion(app.state.ingestion_observers):
                scan_report = scan_session_sources(force=True)
                with transaction() as connection:
                    root_id = add_context_root(connection, str(settings.context_root))
                    scan_context_root(connection, root_id, force=True)
            with connect() as connection:
                session = connection.execute("SELECT id FROM sessions WHERE external_id='synthetic-assembly'").fetchone()
                assert session is not None, scan_report
                session_id = session[0]
                assert connection.execute("SELECT count(*) FROM context_documents").fetchone()[0] == 1
                assert connection.execute("SELECT count(*) FROM session_reference_evidence").fetchone()[0] > 0
                assert connection.execute("SELECT count(*) FROM usage_records").fetchone()[0] > 0
                stale = connection.execute("SELECT status FROM maintenance_runs WHERE id='synthetic-stale-run'").fetchone()[0]
                from localbrain.app.edition import DESKTOP
                expected = "interrupted" if not DESKTOP and not {"atlassian", "workstreams"} <= omitted else "running"
                assert stale == expected, (stale, expected)
                assert [r[0] for r in connection.execute(
                    "SELECT status FROM maintenance_runs WHERE id IN ('synthetic-non-task','synthetic-no-stream')")] == ["running", "running"]
            for url in ("/api/health", "/sessions", "/sessions/" + str(session_id), "/context",
                        "/sessions-dashboard", "/natural-search?mode=keyword&q=synthetic",
                        "/natural-search?mode=ai&q=synthetic", "/settings", "/api/settings/storage", "/openapi.json"):
                status, body, headers = await request(url)
                expected_status = 404 if DESKTOP and url == "/openapi.json" else 200
                assert status == expected_status, (url, status, body[:300])
                if "mode=keyword" in url:
                    assert "Synthetic" in body
                if url == "/sessions":
                    for feature, href in (("atlassian", "/atlassian"), ("workstreams", "/workstreams"),
                                          ("context_search", "/context-search"), ("auto_work", "/auto-work")):
                        if feature in omitted:
                            assert 'href="' + href + '"' not in body, feature
                report["responses"][url] = {"status": status, "headers": headers,
                    "body_sha256": hashlib.sha256(body.encode()).hexdigest()}
            if DESKTOP:
                for url in ("/sources", "/schema", "/workstreams", "/sessions/1/workflow",
                            "/atlassian", "/auto-work", "/sessions-dashboard/insights"):
                    assert (await request(url))[0] == 404, url
                status, _, headers = await request("/search?q=synthetic+text")
                assert status == 303 and ("location", "/natural-search?q=synthetic+text") in headers
                for url in ("/sessions", "/sessions?display=chart", "/documents/1"):
                    status, body, _ = await request(url)
                    assert status == 200, (url, status)
                    assert 'href="/sources"' not in body and 'href="/workstreams/' not in body
            for action in ("prepare", "cancel"):
                method = "request_prepare" if action == "prepare" else "cancel"
                with patch.object(app.state.natural_search, method) as operation:
                    assert (await request("/natural-search/" + action, "POST", b"q=first&q=last"))[0] == 303
                    operation.assert_called_once_with()
                assert (await request("/natural-search/" + action, "POST", b"{}", "application/json"))[0] == 422
            from localbrain.natural_search import index
            from localbrain.natural_search.source import digest
            with index.writer(settings) as folder:
                building = folder / "building.sqlite3"
                private_database(building)
                with contextlib.closing(sqlite3.connect(building)) as cache, cache:
                    cache.executescript(index.SCHEMA)
                    index.set_meta(cache, owner=index.OWNER, binding=digest(str(settings.database_path.resolve())))
            status, body, _ = await request("/api/settings/cache/clear", "POST")
            assert status == 200 and json.loads(body)["removed_bytes"] > 0, (status, body)
            assert not building.exists()
            assert (await request("/natural-search?mode=keyword&q=synthetic"))[0] == 200
            if "auto_work" in omitted:
                assert old_cache_snapshot() == old_caches
            with connect() as connection:
                assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                assert not connection.execute("PRAGMA foreign_key_check").fetchall()
                ddl = [tuple(r) for r in connection.execute(
                    "SELECT type,name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")]
                report["schema_sha256"] = hashlib.sha256(json.dumps(ddl).encode()).hexdigest()
        assert not any(name == block or name.startswith(block + ".")
                       for name in sys.modules for block in blocked)
        assert all(path.read_bytes() == content for path, content in retained.items())
        return report

    report = asyncio.run(run())
    if omitted & {"auto_work", "atlassian"}:
        from localbrain import cli
        from localbrain.app import features
        gc.collect()  # Close unreachable sqlite contexts before the offline CLI's busy-file check.
        with patch.object(features, "DEFAULT_FEATURE_PACKAGES", frozenset(packages - omitted)):
            commands = []
            if "auto_work" in omitted:
                commands.extend(["storage", *args] for args in
                                (("status",), ("migrate",), ("migrate", "--apply"), ("cleanup",), ("cleanup", "--apply")))
                help_output = io.StringIO()
                with contextlib.redirect_stdout(help_output):
                    try:
                        cli.main(["--help"])
                    except SystemExit as result:
                        assert result.code == 0
                assert "simulate" not in help_output.getvalue()
            if "atlassian" in omitted:
                commands.append(["scan"])
            for args in commands:
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    status = cli.main(args)
                assert status == 0, (args, output.getvalue())
                result = json.loads(output.getvalue())
                if args[:2] == ["storage", "migrate"]:
                    assert result["eligible_directories"] == result["moved_directories"] == 0
                if args[:2] == ["storage", "cleanup"]:
                    assert "derived_cache" not in result
                if "auto_work" in omitted:
                    assert old_cache_snapshot() == old_caches
        assert not any(name == block or name.startswith(block + ".")
                       for name in sys.modules for block in blocked)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(report, sort_keys=True))
    print(json.dumps({"omitted": sorted(omitted), "requests": len(report["responses"]), "integrity": "ok"}))


if __name__ == "__main__":
    main()
