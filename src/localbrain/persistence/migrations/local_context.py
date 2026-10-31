"""Adopt already indexed legacy documents into explicit Context roots."""

import sqlite3
from pathlib import Path


def _migrate_context_roots(connection: sqlite3.Connection, config) -> None:
    root = config.context_root.expanduser()
    root = root.resolve() if root.exists() else root
    root_rows = connection.execute(
        "SELECT id FROM context_roots LIMIT 1"
    ).fetchone()
    # Only migrate already-indexed documents. A developer's conventional folder
    # is not consent to register sources on a fresh Mac.
    has_legacy_documents = connection.execute("SELECT 1 FROM context_documents LIMIT 1").fetchone()
    if not root_rows and root.is_dir() and has_legacy_documents:
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
