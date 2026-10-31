import sqlite3
from pathlib import Path
from typing import Optional
from localbrain.foundation.clock import utc_now
from localbrain.foundation.text import _clean
from localbrain.resources.catalog import bind_external_link, bind_local_path


RESOURCE_TYPES = {"jira", "wiki", "slack", "git", "document", "url"}


def create_external_resource(
    connection: sqlite3.Connection,
    resource_type: str,
    title: str,
    url: str,
    summary: Optional[str],
    source_role: Optional[str],
) -> int:
    if resource_type not in RESOURCE_TYPES:
        raise ValueError("Unsupported resource type")
    now = utc_now()
    normalized_url = url.strip()
    existing = connection.execute(
        """
        SELECT id FROM external_resources
        WHERE url = ?
        ORDER BY id
        LIMIT 1
        """,
        (normalized_url,),
    ).fetchone()
    if existing:
        resource_id = int(existing["id"])
        connection.execute(
            """
            UPDATE external_resources
            SET resource_type = ?, title = ?, summary = ?, source_role = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                resource_type,
                title.strip(),
                _clean(summary),
                _clean(source_role),
                now,
                resource_id,
            ),
        )
        bind_external_link(connection, resource_id)
        return resource_id
    cursor = connection.execute(
        """
        INSERT INTO external_resources(
            resource_type, title, url, summary, source_role, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            resource_type,
            title.strip(),
            normalized_url,
            _clean(summary),
            _clean(source_role),
            now,
        ),
    )
    resource_id = int(cursor.lastrowid)
    bind_external_link(connection, resource_id)
    return resource_id


def create_local_resource(
    connection: sqlite3.Connection,
    path: str,
    title: Optional[str],
    summary: Optional[str],
    discovered_by: str = "user",
) -> int:
    candidate = Path(path).expanduser()
    exists_now = candidate.exists()
    canonical = str(candidate.resolve()) if exists_now else str(candidate)
    if exists_now and candidate.is_dir() and (candidate / ".git").exists():
        resource_type = "repository"
    elif exists_now and candidate.is_dir():
        resource_type = "directory"
    elif exists_now and candidate.is_file():
        resource_type = "file"
    else:
        resource_type = "path"
    now = utc_now()
    connection.execute(
        """
        INSERT INTO local_resources(
            path, resource_type, title, summary, exists_now, discovered_by, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            resource_type = excluded.resource_type,
            title = excluded.title,
            summary = COALESCE(excluded.summary, local_resources.summary),
            exists_now = excluded.exists_now,
            discovered_by = excluded.discovered_by,
            updated_at = excluded.updated_at
        """,
        (
            canonical,
            resource_type,
            _clean(title) or candidate.name or canonical,
            _clean(summary),
            int(exists_now),
            discovered_by,
            now,
        ),
    )
    resource_id = int(connection.execute(
        "SELECT id FROM local_resources WHERE path = ?", (canonical,)
    ).fetchone()["id"])
    bind_local_path(connection, resource_id)
    return resource_id


def local_resource_detail(
    connection: sqlite3.Connection, resource_id: int
) -> Optional[dict]:
    row = connection.execute(
        "SELECT * FROM local_resources WHERE id = ?", (resource_id,)
    ).fetchone()
    return dict(row) if row else None
