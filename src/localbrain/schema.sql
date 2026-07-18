PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    root_path TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_scanned_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_files (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    last_scanned_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ok',
    error TEXT,
    UNIQUE(source_id, path)
);

CREATE TABLE IF NOT EXISTS workspaces (
    id INTEGER PRIMARY KEY,
    canonical_path TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    git_root TEXT,
    exists_now INTEGER NOT NULL DEFAULT 0,
    last_activity_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS context_roots (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'folder',
    readable INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'ready',
    error TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_scanned_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    workspace_id INTEGER REFERENCES workspaces(id) ON DELETE SET NULL,
    external_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    cwd_raw TEXT,
    git_branch TEXT,
    title TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    last_event_at TEXT,
    event_count INTEGER NOT NULL DEFAULT 0,
    user_message_count INTEGER NOT NULL DEFAULT 0,
    assistant_message_count INTEGER NOT NULL DEFAULT 0,
    session_class TEXT NOT NULL DEFAULT 'work',
    session_role TEXT NOT NULL DEFAULT 'primary'
        CHECK(session_role IN ('primary', 'subsession')),
    parent_external_id TEXT,
    parent_session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    index_policy TEXT NOT NULL DEFAULT 'full',
    maintenance_run_id TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, external_id)
);

CREATE TABLE IF NOT EXISTS activity_events (
    id TEXT PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    occurred_at TEXT,
    event_type TEXT NOT NULL,
    role TEXT,
    text TEXT,
    tool_name TEXT,
    source_line INTEGER NOT NULL,
    metadata_json TEXT,
    UNIQUE(session_id, sequence, event_type, source_line)
);

CREATE TABLE IF NOT EXISTS context_documents (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    context_root_id INTEGER REFERENCES context_roots(id) ON DELETE SET NULL,
    workspace_id INTEGER REFERENCES workspaces(id) ON DELETE SET NULL,
    path TEXT NOT NULL UNIQUE,
    relative_path TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'text/markdown',
    size_bytes INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workstreams (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active',
    summary TEXT,
    last_activity_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workstream_links (
    id INTEGER PRIMARY KEY,
    workstream_id INTEGER NOT NULL REFERENCES workstreams(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    relation_type TEXT NOT NULL DEFAULT 'related-to',
    confidence REAL,
    linked_by TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workstream_id, entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS threads (
    id INTEGER PRIMARY KEY,
    workstream_id INTEGER NOT NULL REFERENCES workstreams(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    summary TEXT,
    current_goal TEXT,
    next_action TEXT,
    last_activity_at TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workstream_id, title)
);

CREATE TABLE IF NOT EXISTS thread_links (
    id INTEGER PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    relation_type TEXT NOT NULL DEFAULT 'related-to',
    confidence REAL,
    linked_by TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(thread_id, entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS external_resources (
    id INTEGER PRIMARY KEY,
    resource_type TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    summary TEXT,
    source_role TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS local_resources (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    resource_type TEXT NOT NULL DEFAULT 'path',
    title TEXT NOT NULL,
    summary TEXT,
    exists_now INTEGER NOT NULL DEFAULT 0,
    discovered_by TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suggestions (
    id INTEGER PRIMARY KEY,
    suggestion_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    rationale TEXT,
    payload_json TEXT,
    fingerprint TEXT NOT NULL UNIQUE,
    origin_run_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    confidence REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS maintenance_runs (
    id TEXT PRIMARY KEY,
    workstream_id INTEGER REFERENCES workstreams(id) ON DELETE SET NULL,
    task_type TEXT,
    runner TEXT NOT NULL DEFAULT 'claude',
    cwd TEXT,
    status TEXT NOT NULL DEFAULT 'prepared',
    pid INTEGER,
    started_at TEXT,
    completed_at TEXT,
    source_snapshot_json TEXT,
    manifest_path TEXT,
    prompt_path TEXT,
    stream_path TEXT,
    result_path TEXT,
    stderr_path TEXT,
    structured_result_json TEXT,
    suggestions_created INTEGER NOT NULL DEFAULT 0,
    refresh_suggestions INTEGER NOT NULL DEFAULT 0,
    mcp_call_budget INTEGER NOT NULL DEFAULT 20,
    mcp_calls_used INTEGER NOT NULL DEFAULT 0,
    mcp_tool_calls_json TEXT,
    mcp_budget_exceeded INTEGER NOT NULL DEFAULT 0,
    summary TEXT,
    error TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY,
    workstream_id INTEGER NOT NULL REFERENCES workstreams(id) ON DELETE CASCADE,
    current_goal TEXT,
    confirmed_facts TEXT,
    recent_decisions TEXT,
    open_questions TEXT,
    next_actions TEXT,
    files_to_open TEXT,
    confirmed_at TEXT,
    based_on_activity_at TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS checkpoint_resource_refs (
    id INTEGER PRIMARY KEY,
    checkpoint_id INTEGER NOT NULL REFERENCES checkpoints(id) ON DELETE CASCADE,
    thread_id INTEGER REFERENCES threads(id) ON DELETE SET NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    relation_type TEXT NOT NULL DEFAULT 'evidence',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(checkpoint_id, thread_id, entity_type, entity_id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    entity_type UNINDEXED,
    entity_id UNINDEXED,
    source_kind UNINDEXED,
    title,
    body,
    path,
    tokenize = 'unicode61'
);

CREATE INDEX IF NOT EXISTS idx_sessions_last_event
    ON sessions(last_event_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_workspace
    ON sessions(workspace_id, last_event_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_session_sequence
    ON activity_events(session_id, sequence);
CREATE INDEX IF NOT EXISTS idx_documents_mtime
    ON context_documents(mtime_ns DESC);
CREATE INDEX IF NOT EXISTS idx_local_resources_path
    ON local_resources(path);
CREATE INDEX IF NOT EXISTS idx_threads_workstream
    ON threads(workstream_id, status, position);
CREATE INDEX IF NOT EXISTS idx_thread_links_entity
    ON thread_links(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_workstream_links_entity
    ON workstream_links(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_target
    ON suggestions(target_type, target_id, status);
CREATE INDEX IF NOT EXISTS idx_checkpoint_resource_refs
    ON checkpoint_resource_refs(checkpoint_id, thread_id);
