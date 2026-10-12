"""User-owned Chart visibility, independent of browsers and Session ingestion."""

import json
import sqlite3
from typing import List, Optional

from .workstreams import utc_now


def validate_hidden_projects(value: object) -> List[str]:
    """Admit bounded folder identities, including an empty missing-folder key."""
    if not isinstance(value, list) or len(value) > 2000:
        raise ValueError("Hidden projects must be a bounded list")
    if any(not isinstance(key, str) or len(key) > 4096 for key in value):
        raise ValueError("Invalid Project identity")
    keys = sorted(set(value))
    encoded = json.dumps(keys, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > 60_000:
        raise ValueError("Project preferences are too large")
    return keys


def get_project_visibility(
    connection: sqlite3.Connection, source: str, workspace: Optional[int]
) -> Optional[List[str]]:
    """None means absent; an empty list is an authoritative all-selected choice."""
    row = connection.execute(
        """
        SELECT hidden_projects_json
        FROM session_chart_preferences
        WHERE source_scope = ? AND workspace_scope = ?
        """,
        (source, str(workspace) if workspace is not None else ""),
    ).fetchone()
    return validate_hidden_projects(json.loads(row["hidden_projects_json"])) if row else None


def set_project_visibility(
    connection: sqlite3.Connection,
    source: str,
    workspace: Optional[int],
    hidden_projects: List[str],
    *,
    only_if_missing: bool = False,
) -> List[str]:
    """Write within the caller's transaction; migration never replaces a DB row."""
    keys = validate_hidden_projects(hidden_projects)
    conflict = "DO NOTHING" if only_if_missing else (
        "DO UPDATE SET hidden_projects_json = excluded.hidden_projects_json, "
        "updated_at = excluded.updated_at"
    )
    connection.execute(
        """
        INSERT INTO session_chart_preferences
            (source_scope, workspace_scope, hidden_projects_json, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(source_scope, workspace_scope) {}
        """.format(conflict),
        (
            source,
            str(workspace) if workspace is not None else "",
            json.dumps(keys, ensure_ascii=False, separators=(",", ":")),
            utc_now(),
        ),
    )
    return get_project_visibility(connection, source, workspace)
