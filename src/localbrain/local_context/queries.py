import sqlite3
from typing import Optional


def recent_documents(connection: sqlite3.Connection, limit: int = 8):
    return connection.execute(
        """
        SELECT context_documents.id, context_documents.title,
               context_documents.relative_path, context_documents.path,
               context_documents.mtime_ns
        FROM context_documents
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.context_root_id IS NULL OR context_roots.enabled = 1
        ORDER BY mtime_ns DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def context_documents(
    connection: sqlite3.Connection, root_id: Optional[int] = None, limit: int = 240
):
    if root_id is not None:
        return connection.execute(
            """
            SELECT context_documents.id, context_documents.title,
                   context_documents.relative_path, context_documents.path,
                   context_documents.size_bytes, context_documents.mtime_ns,
                   context_roots.label AS root_label,
                   context_roots.path AS root_path
            FROM context_documents
            JOIN context_roots ON context_roots.id = context_documents.context_root_id
            WHERE context_roots.enabled = 1 AND context_roots.id = ?
            ORDER BY context_documents.mtime_ns DESC
            LIMIT ?
            """,
            (root_id, limit),
        ).fetchall()
    return connection.execute(
        """
        SELECT context_documents.id, context_documents.title,
               context_documents.relative_path, context_documents.path,
               context_documents.size_bytes, context_documents.mtime_ns,
               context_roots.label AS root_label,
               context_roots.path AS root_path
        FROM context_documents
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.context_root_id IS NULL OR context_roots.enabled = 1
        ORDER BY context_documents.mtime_ns DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def document_detail(connection: sqlite3.Connection, document_id: int):
    return connection.execute(
        """
        SELECT context_documents.*, sources.name AS source_name,
               workspaces.display_name AS workspace_name,
               context_roots.label AS context_root_label,
               context_roots.path AS context_root_path
        FROM context_documents
        JOIN sources ON sources.id = context_documents.source_id
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        LEFT JOIN workspaces ON workspaces.id = context_documents.workspace_id
        WHERE context_documents.id = ?
        """,
        (document_id,),
    ).fetchone()
