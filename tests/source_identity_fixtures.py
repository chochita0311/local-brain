"""Frozen pre-PK-only registry shape for migration tests; synthetic rows only."""
import hashlib

SOURCES_V1 = """CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL UNIQUE,
    provider_kind TEXT NOT NULL DEFAULT 'unknown'
        CHECK(length(trim(provider_kind)) BETWEEN 1 AND 64),
    name TEXT NOT NULL,
    root_path TEXT NOT NULL,
    profile_color TEXT CHECK(profile_color IN ('green','blue','orange','yellow','red','gray')),
    profile_position INTEGER NOT NULL DEFAULT 2147483647 CHECK(profile_position >= 0),
    last_scanned_at TEXT,
    last_scan_success_at TEXT,
    last_scan_status TEXT CHECK(last_scan_status IN (
        'completed', 'empty', 'unavailable', 'configuration_error', 'scan_failed'
    )),
    last_scan_error TEXT CHECK(
        last_scan_error IS NULL OR length(last_scan_error) <= 500
    ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);"""

SKILL_OBSERVATIONS_V1 = """CREATE TABLE IF NOT EXISTS skill_observations (
    id TEXT PRIMARY KEY,
    source_key TEXT NOT NULL,
    provider_kind TEXT NOT NULL
        CHECK(provider_kind IN ('claude', 'codex')),
    external_session_id TEXT NOT NULL,
    native_event_id TEXT NOT NULL,
    skill_name TEXT NOT NULL CHECK(length(trim(skill_name)) BETWEEN 1 AND 160),
    skill_group_key TEXT NOT NULL CHECK(length(skill_group_key) > 0),
    skill_locator TEXT CHECK(
        skill_locator IS NULL OR length(skill_locator) BETWEEN 1 AND 4096
    ),
    signal_kind TEXT NOT NULL CHECK(
        signal_kind IN (
            'claude_skill_tool', 'codex_skill_context',
            'claude_skill_read', 'codex_skill_read',
            'claude_skill_declaration', 'codex_skill_declaration',
            'claude_skill_mention', 'codex_skill_mention',
            'claude_skill_script', 'codex_skill_script'
        )
    ),
    source_line INTEGER NOT NULL CHECK(source_line > 0),
    occurred_at TEXT,
    request_key TEXT CHECK(request_key IS NULL OR length(request_key) BETWEEN 1 AND 160),
    state TEXT NOT NULL DEFAULT 'observed'
        CHECK(state IN ('observed', 'corrected')),
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_key, external_session_id, native_event_id, skill_group_key)
);"""

def legacy_registry(connection, aliases):
    """Downgrade only a test fixture, including aliases and unrelated opaque IDs."""
    connection.commit()
    connection.execute("PRAGMA foreign_keys=OFF")
    try:
        connection.execute("BEGIN")
        for table, definition in (("skill_observations", SKILL_OBSERVATIONS_V1), ("sources", SOURCES_V1)):
            rows = [dict(row) for row in connection.execute("SELECT * FROM " + table)]
            connection.execute(definition.replace(table, table + "_fixture", 1))
            for row in rows:
                if table == "sources":
                    row["kind"] = aliases[row["id"]]
                else:
                    row["source_key"] = aliases[row.pop("source_id")]
                connection.execute("INSERT INTO " + table + "_fixture (" + ",".join(row) + ") VALUES (" + ",".join("?" for _ in row) + ")", tuple(row.values()))
            connection.execute("DROP TABLE " + table)
            connection.execute("ALTER TABLE " + table + "_fixture RENAME TO " + table)
        for table in ("activity_events", "usage_records"):
            for row in connection.execute("SELECT id FROM " + table).fetchall():
                changed = hashlib.sha256(("old-record:" + row["id"]).encode()).hexdigest()
                connection.execute("UPDATE " + table + " SET id=? WHERE id=?", (changed, row["id"]))
        for source_id, alias in aliases.items():
            connection.execute("UPDATE session_chart_preferences SET source_scope=? WHERE source_scope=?", (alias, str(source_id)))
        connection.commit()
    finally:
        connection.rollback()
        connection.execute("PRAGMA foreign_keys=ON")
