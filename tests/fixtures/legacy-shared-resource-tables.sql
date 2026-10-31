-- Pre-REFACTOR-0005 DDL retained to verify the preserving migration.

CREATE TABLE IF NOT EXISTS session_reference_evidence (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL
        REFERENCES sessions(id) ON DELETE CASCADE,
    source_path TEXT NOT NULL,
    source_event_id TEXT,
    source_line INTEGER NOT NULL CHECK(source_line > 0),
    evidence_ordinal INTEGER NOT NULL CHECK(evidence_ordinal > 0),
    target_kind TEXT NOT NULL
        CHECK(target_kind IN ('url', 'context_document', 'atlassian_item')),
    target_key TEXT NOT NULL,
    context_document_id INTEGER
        REFERENCES context_documents(id) ON DELETE CASCADE,
    external_resource_id INTEGER
        REFERENCES atlassian_items(external_resource_id) ON DELETE CASCADE,
    evidence_kind TEXT NOT NULL
        CHECK(
            evidence_kind IN (
                'user_mention',
                'assistant_mention',
                'tool_result',
                'resource_read'
            )
        ),
    read_outcome TEXT
        CHECK(read_outcome IS NULL OR read_outcome IN ('success', 'failure')),
    observed_identity TEXT NOT NULL,
    normalized_url TEXT,
    tool_name TEXT,
    tool_call_id TEXT,
    observed_at TEXT,
    extractor_version TEXT NOT NULL,
    evidence_key TEXT NOT NULL UNIQUE,
    first_observed_at TEXT NOT NULL,
    last_observed_at TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(length(source_path) > 0 AND length(source_path) <= 8000),
    CHECK(
        source_event_id IS NULL
        OR (length(source_event_id) > 0 AND length(source_event_id) <= 1000)
    ),
    CHECK(length(target_key) > 0 AND length(target_key) <= 300),
    CHECK(length(observed_identity) > 0 AND length(observed_identity) <= 500),
    CHECK(
        normalized_url IS NULL
        OR (length(normalized_url) > 0 AND length(normalized_url) <= 8000)
    ),
    CHECK(tool_name IS NULL OR (length(tool_name) > 0 AND length(tool_name) <= 200)),
    CHECK(
        tool_call_id IS NULL
        OR (length(tool_call_id) > 0 AND length(tool_call_id) <= 500)
    ),
    CHECK(length(extractor_version) > 0 AND length(extractor_version) <= 80),
    CHECK(length(evidence_key) = 64),
    CHECK(
        (
            target_kind = 'url'
            AND context_document_id IS NULL
            AND external_resource_id IS NULL
            AND normalized_url IS NOT NULL
        )
        OR (
            target_kind = 'context_document'
            AND context_document_id IS NOT NULL
            AND external_resource_id IS NULL
            AND normalized_url IS NULL
        )
        OR (
            target_kind = 'atlassian_item'
            AND context_document_id IS NULL
            AND external_resource_id IS NOT NULL
            AND normalized_url IS NOT NULL
        )
    ),
    CHECK(
        (
            evidence_kind IN ('user_mention', 'assistant_mention')
            AND read_outcome IS NULL
            AND tool_name IS NULL
            AND tool_call_id IS NULL
        )
        OR (
            evidence_kind = 'tool_result'
            AND read_outcome IS NULL
            AND tool_name IS NOT NULL
            AND tool_call_id IS NOT NULL
        )
        OR (
            evidence_kind = 'resource_read'
            AND read_outcome IS NOT NULL
            AND tool_name IS NOT NULL
            AND tool_call_id IS NOT NULL
        )
    )
);

CREATE TABLE IF NOT EXISTS atlassian_item_content (
    external_resource_id INTEGER PRIMARY KEY
        REFERENCES atlassian_items(external_resource_id) ON DELETE CASCADE,
    source_format TEXT NOT NULL
        CHECK(
            source_format IN (
                'jira_adf',
                'confluence_adf',
                'confluence_html',
                'confluence_markdown',
                'plain_text'
            )
        ),
    source_body TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    normalized_document_json TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    normalizer_version TEXT NOT NULL,
    normalization_warning TEXT,
    remote_version TEXT,
    remote_updated_at TEXT,
    applied_at TEXT NOT NULL,
    search_projection_hash TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(length(source_hash) = 64),
    CHECK(search_projection_hash IS NULL OR length(search_projection_hash) = 64)
);

CREATE TABLE IF NOT EXISTS atlassian_item_local_state (
    external_resource_id INTEGER PRIMARY KEY
        REFERENCES atlassian_items(external_resource_id) ON DELETE CASCADE,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(length(note) <= 50000)
);
