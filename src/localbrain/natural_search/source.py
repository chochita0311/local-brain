"""Read normalized sources without modifying or expanding their admission policy."""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from localbrain.foundation.config import cache_directory, development_directory


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


@contextmanager
def source_connection(database):
    connection = sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    try:
        yield connection
    finally:
        connection.close()


@dataclass
class Source:
    key: str
    kind: str
    entity_id: int
    title: str
    path: str
    source_kind: str
    timestamp: str
    blocks: list
    source_id: Optional[int] = None

    @property
    def revision(self):
        return digest(self.__dict__)

    def metadata(self):
        return {key: value for key, value in self.__dict__.items() if key != "blocks"}


def _private_derived(path, config):
    candidate = Path(path).expanduser().resolve()
    roots = [config.data_dir, cache_directory(config), development_directory(config)]
    from localbrain.foundation.paths import hub_cache_root
    roots.append(hub_cache_root())
    return any(candidate == Path(root).resolve() or Path(root).resolve() in candidate.parents for root in roots)


def read_sources(config, keys=None):
    """A consistent snapshot. `keys` narrows current-result validation, never indexing."""
    from localbrain.sources.settings import registered_session_roots
    registered = registered_session_roots(config)
    selected = set(keys) if keys is not None else None
    values = []
    empty_sessions, empty_documents, excluded_runtime_documents = 0, 0, 0
    with source_connection(config.database_path) as connection:
        connection.execute("BEGIN")
        sessions = connection.execute("""
            SELECT s.*, o.provider_kind AS source_kind, o.root_path AS registered_root FROM sessions s JOIN sources o ON o.id=s.source_id
            WHERE s.session_class='work' AND s.session_role='primary' AND s.index_policy='full'
            ORDER BY s.id
        """).fetchall()
        for row in sessions:
            if registered.get(row["source_id"]) != row["registered_root"]:
                continue
            key = "session:" + str(row["id"])
            if selected is not None and key not in selected:
                continue
            blocks = [dict(event) for event in connection.execute("""
                SELECT id, role, text, sequence, source_line FROM activity_events
                WHERE session_id=? AND event_type='message' AND role IN ('user','assistant')
                  AND length(text)>0 ORDER BY sequence, source_line, id
            """, (row["id"],))]
            if not blocks:
                empty_sessions += 1
                continue
            values.append(Source(key, "session", row["id"], row["title"],
                                 row["cwd_raw"] or row["source_path"], row["source_kind"],
                                 row["last_event_at"] or row["ended_at"] or row["started_at"] or "", blocks, source_id=row["source_id"]))
        documents = connection.execute("""
            SELECT d.*, o.provider_kind AS source_kind FROM context_documents d
            JOIN context_roots r ON r.id=d.context_root_id JOIN sources o ON o.id=d.source_id
            WHERE r.enabled=1 AND r.readable=1 ORDER BY d.id
        """)
        for row in documents:
            key = "document:" + str(row["id"])
            if selected is not None and key not in selected:
                continue
            if _private_derived(row["path"], config):
                excluded_runtime_documents += 1
                continue
            if not row["body"]:
                empty_documents += 1
                continue
            from datetime import datetime, timezone
            timestamp = datetime.fromtimestamp(row["mtime_ns"] / 1e9, timezone.utc).isoformat()
            values.append(Source(key, "document", row["id"], row["title"], row["path"],
                                 row["source_kind"], timestamp,
                                 [{"id": str(row["id"]), "role": "document", "text": row["body"],
                                   "sequence": 0, "source_line": 1}], source_id=row["source_id"]))
        unavailable = connection.execute(
            "SELECT count(*) FROM context_roots WHERE enabled=1 AND readable=0").fetchone()[0]
        excluded = connection.execute("""SELECT count(*) FROM sessions WHERE
            session_class!='work' OR session_role!='primary' OR index_policy!='full'""").fetchone()[0]
    return values, {"eligible_parents": len(values), "excluded_sessions": excluded,
                    "unreadable_context_roots": unavailable, "empty_sessions": empty_sessions,
                    "empty_documents": empty_documents, "excluded_runtime_documents": excluded_runtime_documents}
