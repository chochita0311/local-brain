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
            yield

    app = create_app()
    app.router.lifespan_context = synthetic_lifespan

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
