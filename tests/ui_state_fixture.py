"""Opt-in browser QA backend with synthetic data and no collection or model work."""

import json
import os
import socket
import sys
from contextlib import asynccontextmanager
from pathlib import Path


def main():
    root = Path(sys.argv[1]).resolve()
    repository = Path(__file__).resolve().parents[1]
    if root.exists() or root == repository or repository in root.parents:
        raise SystemExit("A new task-owned runtime directory outside the repository is required")
    root.mkdir(parents=True, mode=0o700)
    for key in tuple(os.environ):
        if key.startswith("LOCALBRAIN_"):
            del os.environ[key]
    os.environ.update({
        "LOCALBRAIN_DATA_DIR": str(root / "data"),
        "LOCALBRAIN_CACHE_DIR": str(root / "cache"),
        "LOCALBRAIN_DEVELOPMENT_DIR": str(root / "development"),
        "LOCALBRAIN_CONTEXT_ROOT": str(root / "context"),
        "LOCALBRAIN_CLAUDE_ROOT": str(root / "claude"),
        "LOCALBRAIN_CODEX_ROOT": str(root / "codex/sessions"),
        "HF_HOME": str(root / "hub"), "HF_HUB_CACHE": str(root / "hub/cache"),
        "HUGGINGFACE_HUB_CACHE": str(root / "hub/cache"),
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
    })
    if len(sys.argv) > 2 and sys.argv[2] == "desktop":
        os.environ.update(LOCALBRAIN_EDITION="desktop", LOCALBRAIN_DESKTOP_TOKEN="synthetic-qa-token")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repository / "src"))
    from localbrain.foundation.preferences import toml_text
    data, source = root / "data", root / "codex/sessions"
    data.mkdir(mode=0o700)
    source.mkdir(parents=True)
    (data / "settings.toml").write_text(toml_text({
        "schema_version": 1, "onboarding_completed": True, "startup_screen": "context",
        "timezone": "Europe/Paris", "session_sync_enabled": False, "session_sync_minutes": 40,
        "context_sync_enabled": False, "context_sync_minutes": 90,
    }))
    (data / "session-sources.toml").write_text(toml_text({"schema_version": 2, "session_sources": [{
        "source_id": 1, "provider_kind": "codex", "display_label": "Synthetic QA",
        "root": str(source), "agent_home": str(root / "codex"), "color": "green",
    }]}))
    import localbrain.app.settings as settings_routes
    settings_routes.candidates = lambda: []
    from localbrain.app.application import create_app
    from localbrain.app.lifecycle import lifespan
    from localbrain.persistence.db import connect
    from localbrain.sessions.pins import pin_session

    @asynccontextmanager
    async def synthetic_lifespan(app):
        async with lifespan(app):
            workspace = root / "workspaces" / ("long-synthetic-path-" * 9)
            workspace.mkdir(parents=True)
            with connect() as connection:
                connection.execute("INSERT INTO workspaces(id,canonical_path,display_name,exists_now) VALUES (1,?,'Synthetic QA',1)", (str(workspace),))
                path = source / "qa.jsonl"
                path.write_text("{}\n")
                connection.execute("""INSERT INTO sessions(id,source_id,workspace_id,external_id,source_path,title,cwd_raw,started_at,last_event_at)
                    VALUES (1,1,1,'synthetic-ui-qa',?,'Synthetic QA Session',?,'2026-11-01T00:00:00Z','2026-11-01T00:00:00Z')""", (str(path), str(workspace)))
                pin_session(connection, 1)
                connection.execute("INSERT INTO workstreams(id,name) VALUES (1,'Synthetic QA')")
                for status in ("queued", "completed", "failed"):
                    connection.execute("""INSERT INTO maintenance_runs(id,workstream_id,task_type,status,started_at,result_path)
                        VALUES (?,1,'organize_resources',?,'2026-11-01T00:00:00Z',?)""",
                        ("qa-" + status, status, str(root / "missing-result")))
                connection.commit()
            if (len(sys.argv) > 2 and sys.argv[2] == "desktop") or (len(sys.argv) > 3 and sys.argv[3] == "navigation"):
                from localbrain.local_context.service import add_context_root
                from localbrain.ingest.scanner import scan_context_root
                from localbrain.persistence.db import transaction
                document_root = root / "context"
                document_root.mkdir()
                (document_root / "example.md").write_text("# Synthetic linked document\nTrial reader evidence.")
                with transaction() as connection:
                    context_id = add_context_root(connection, str(document_root))
                    scan_context_root(connection, context_id, force=True)
                    document_id = connection.execute("SELECT id FROM context_documents").fetchone()[0]
                    connection.execute("INSERT INTO workstream_links(workstream_id,entity_type,entity_id) VALUES (1,'document',?)", (str(document_id),))
            if len(sys.argv) > 3 and sys.argv[3] == "navigation":
                from localbrain.ingest.scanner import scan_session_sources
                for name in ("example.md", "second.md", "third.md"):
                    (document_root / name).write_text("# Synthetic " + name + "\n\n" + "\n\n".join("Paragraph %d: synthetic navigation evidence with enough text to scroll." % i for i in range(120)))
                with transaction() as connection:
                    scan_context_root(connection, context_id, force=True)
                records = [{"type": "session_meta", "timestamp": "2026-11-01T00:00:00Z", "payload": {"id": "synthetic-ui-qa", "cwd": str(workspace)}}]
                records += [{"type": "event_msg", "timestamp": "2026-11-01T00:01:00Z", "payload": {"type": "user_message", "message": "Synthetic message %d: " % i + ("navigation evidence " * 20)}} for i in range(45)]
                path.write_text("\n".join(json.dumps(value) for value in records) + "\n")
                scan_session_sources(force=True)
                with connect() as connection:
                    for i in range(2, 36):
                        connection.execute("""INSERT INTO sessions(id,source_id,workspace_id,external_id,source_path,title,cwd_raw,started_at,last_event_at)
                          VALUES (?,1,1,?,?,?,?,'2026-11-01T00:00:00Z','2026-11-01T00:00:00Z')""", (i, "synthetic-navigation-"+str(i), str(source/("retained-"+str(i)+".jsonl")), "Synthetic navigation Session "+str(i), str(workspace)))
                    other_workspace = root / "second-project"
                    other_workspace.mkdir()
                    other_id = connection.execute("INSERT INTO workspaces(canonical_path,display_name,exists_now) VALUES (?,'Second synthetic Project',1)", (str(other_workspace),)).lastrowid
                    connection.execute("UPDATE sessions SET workspace_id=?,cwd_raw=? WHERE id=35", (other_id, str(other_workspace)))
                    connection.commit()
                if len(sys.argv) > 2 and sys.argv[2] == "web":
                    from localbrain.atlassian.catalog import create_or_reuse_atlassian_stub
                    with connect() as connection:
                        external_source = connection.execute("INSERT INTO external_source_instances(instance_key,provider_kind,service,display_name) VALUES ('toolbar-qa-jira','mcp_gateway','jira','Synthetic Jira')").lastrowid
                        create_or_reuse_atlassian_stub(connection, source_instance_id=external_source, url="https://jira.example.test/browse/QA-1", title="Synthetic toolbar issue", coverage="indexed", observed_at="2026-11-01T00:00:00Z")
                        connection.commit()
            yield

    app = create_app()
    app.router.lifespan_context = synthetic_lifespan

    @app.middleware("http")
    async def delayed_history(request, call_next):
        import asyncio
        if request.url.path == "/help" and request.query_params.get("navigation_delay") == "1":
            while (root / "hold-navigation").exists():
                await asyncio.sleep(0.03)
        return await call_next(request)

    @app.get("/__qa__/fixture")
    def marker():
        return {"fixture": "synthetic-ui-states-v1"}

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    (root / "port.json").write_text(json.dumps({"port": listener.getsockname()[1]}))
    import uvicorn
    uvicorn.Server(uvicorn.Config(app, log_level="warning")).run(sockets=[listener])


if __name__ == "__main__":
    main()
