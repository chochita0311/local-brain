import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from .config import settings


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(settings.database_path), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


def init_db() -> None:
    with connect() as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _run_compatible_migrations(connection)


def _column_names(connection: sqlite3.Connection, table: str) -> set:
    return {row["name"] for row in connection.execute("PRAGMA table_info(" + table + ")")}


def _ensure_column(
    connection: sqlite3.Connection, table: str, column: str, definition: str
) -> None:
    if column in _column_names(connection, table):
        return
    connection.execute(
        "ALTER TABLE {} ADD COLUMN {} {}".format(table, column, definition)
    )


def _run_compatible_migrations(connection: sqlite3.Connection) -> None:
    # The local index is rebuildable, but user-curated workstreams are not. Keep
    # upgrades additive so both kinds of data survive normal application updates.
    for table, column, definition in (
        ("sessions", "session_class", "TEXT NOT NULL DEFAULT 'work'"),
        ("sessions", "index_policy", "TEXT NOT NULL DEFAULT 'full'"),
        ("sessions", "maintenance_run_id", "TEXT"),
        (
            "context_documents",
            "context_root_id",
            "INTEGER REFERENCES context_roots(id) ON DELETE SET NULL",
        ),
        (
            "context_documents",
            "content_type",
            "TEXT NOT NULL DEFAULT 'text/markdown'",
        ),
        ("context_roots", "source_type", "TEXT NOT NULL DEFAULT 'folder'"),
        ("context_roots", "readable", "INTEGER NOT NULL DEFAULT 1"),
        ("context_roots", "status", "TEXT NOT NULL DEFAULT 'ready'"),
        ("context_roots", "error", "TEXT"),
        ("workstream_links", "relation_type", "TEXT NOT NULL DEFAULT 'related-to'"),
        ("checkpoints", "based_on_activity_at", "TEXT"),
        ("checkpoints", "version", "INTEGER NOT NULL DEFAULT 1"),
        ("checkpoints", "updated_at", "TEXT"),
        ("maintenance_runs", "workstream_id", "INTEGER"),
        ("maintenance_runs", "task_type", "TEXT"),
        ("maintenance_runs", "runner", "TEXT NOT NULL DEFAULT 'claude'"),
        ("maintenance_runs", "cwd", "TEXT"),
        ("maintenance_runs", "pid", "INTEGER"),
        ("maintenance_runs", "manifest_path", "TEXT"),
        ("maintenance_runs", "prompt_path", "TEXT"),
        ("maintenance_runs", "stream_path", "TEXT"),
        ("maintenance_runs", "result_path", "TEXT"),
        ("maintenance_runs", "stderr_path", "TEXT"),
        ("maintenance_runs", "structured_result_json", "TEXT"),
        ("maintenance_runs", "suggestions_created", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "refresh_suggestions", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "mcp_call_budget", "INTEGER NOT NULL DEFAULT 20"),
        ("maintenance_runs", "mcp_calls_used", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "mcp_tool_calls_json", "TEXT"),
        ("maintenance_runs", "mcp_budget_exceeded", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "error", "TEXT"),
        ("maintenance_runs", "updated_at", "TEXT"),
        ("suggestions", "origin_run_id", "TEXT"),
    ):
        _ensure_column(connection, table, column, definition)

    connection.execute(
        "UPDATE checkpoints SET updated_at = COALESCE(updated_at, created_at)"
    )
    connection.execute(
        "UPDATE maintenance_runs SET updated_at = COALESCE(updated_at, created_at)"
    )
    _migrate_context_roots(connection)

    connection.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_class
            ON sessions(session_class, last_event_at DESC);
        CREATE INDEX IF NOT EXISTS idx_threads_workstream
            ON threads(workstream_id, status, position);
        CREATE INDEX IF NOT EXISTS idx_thread_links_entity
            ON thread_links(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_workstream_links_entity
            ON workstream_links(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_suggestions_target
            ON suggestions(target_type, target_id, status);
        CREATE INDEX IF NOT EXISTS idx_maintenance_runs_workstream
            ON maintenance_runs(workstream_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_maintenance_runs_status
            ON maintenance_runs(status, updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_suggestions_origin_run
            ON suggestions(origin_run_id, status);
        CREATE INDEX IF NOT EXISTS idx_checkpoint_resource_refs
            ON checkpoint_resource_refs(checkpoint_id, thread_id);
        CREATE INDEX IF NOT EXISTS idx_documents_context_root
            ON context_documents(context_root_id, mtime_ns DESC);
        """
    )


def _migrate_context_roots(connection: sqlite3.Connection) -> None:
    root = settings.context_root.expanduser()
    root = root.resolve() if root.exists() else root
    root_rows = connection.execute(
        "SELECT id FROM context_roots LIMIT 1"
    ).fetchone()
    if not root_rows and root.is_dir():
        children = sorted(
            child for child in root.iterdir()
            if child.is_dir() and not child.name.startswith(".")
            and any(child.rglob("*.md"))
        )
        candidates = children or ([root] if any(root.glob("*.md")) else [])
        for candidate in candidates:
            connection.execute(
                "INSERT OR IGNORE INTO context_roots(path, label) VALUES (?, ?)",
                (str(candidate.resolve()), candidate.name or str(candidate)),
            )

    unassigned = connection.execute(
        "SELECT id, path FROM context_documents WHERE context_root_id IS NULL"
    ).fetchall()
    roots = connection.execute(
        "SELECT id, path FROM context_roots ORDER BY length(path) DESC"
    ).fetchall()
    for document in unassigned:
        document_path = Path(document["path"])
        for context_root in roots:
            root_path = Path(context_root["path"])
            try:
                relative_path = document_path.relative_to(root_path)
            except ValueError:
                continue
            connection.execute(
                """
                UPDATE context_documents
                SET context_root_id = ?, relative_path = ?
                WHERE id = ?
                """,
                (context_root["id"], str(relative_path), document["id"]),
            )
            break


@contextmanager
def transaction() -> Generator[sqlite3.Connection, None, None]:
    connection = connect()
    try:
        connection.execute("BEGIN")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
