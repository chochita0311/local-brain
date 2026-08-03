PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL UNIQUE,
    provider_kind TEXT NOT NULL DEFAULT 'unknown'
        CHECK(length(trim(provider_kind)) BETWEEN 1 AND 64),
    name TEXT NOT NULL,
    root_path TEXT NOT NULL,
    last_scanned_at TEXT,
    last_scan_success_at TEXT,
    last_scan_status TEXT CHECK(last_scan_status IN (
        'completed', 'empty', 'unavailable', 'configuration_error', 'scan_failed'
    )),
    last_scan_error TEXT CHECK(
        last_scan_error IS NULL OR length(last_scan_error) <= 500
    ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_files (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    last_scanned_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ok',
    error TEXT,
    usage_contract_version TEXT,
    reference_contract_version TEXT,
    UNIQUE(source_id, path)
);

CREATE TABLE IF NOT EXISTS external_source_instances (
    id INTEGER PRIMARY KEY,
    instance_key TEXT NOT NULL UNIQUE,
    provider_kind TEXT NOT NULL
        CHECK(provider_kind IN ('mcp_gateway', 'atlassian_cloud')),
    service TEXT NOT NULL
        CHECK(service IN ('jira', 'confluence')),
    display_name TEXT NOT NULL,
    config_ref TEXT,
    enabled INTEGER NOT NULL DEFAULT 1
        CHECK(enabled IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS external_source_capabilities (
    source_instance_id INTEGER PRIMARY KEY
        REFERENCES external_source_instances(id) ON DELETE CASCADE,
    policy_version TEXT NOT NULL,
    schema_fingerprint TEXT,
    availability TEXT NOT NULL
        CHECK(
            availability IN (
                'available',
                'unavailable',
                'unauthorized',
                'error'
            )
        ),
    capability_json TEXT NOT NULL,
    error_code TEXT,
    error_message TEXT CHECK(
        error_message IS NULL OR length(error_message) <= 500
    ),
    checked_at TEXT NOT NULL,
    invalidated_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
    session_class TEXT NOT NULL DEFAULT 'work'
        CHECK(session_class IN ('work', 'maintenance')),
    session_role TEXT NOT NULL DEFAULT 'primary'
        CHECK(session_role IN ('primary', 'subsession')),
    parent_external_id TEXT,
    parent_session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    index_policy TEXT NOT NULL DEFAULT 'full'
        CHECK(index_policy IN ('full', 'metadata_only')),
    maintenance_run_id TEXT UNIQUE
        REFERENCES maintenance_runs(id) ON DELETE SET NULL,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(
        maintenance_run_id IS NULL
        OR (
            session_class = 'maintenance'
            AND session_role = 'primary'
            AND index_policy = 'metadata_only'
        )
    ),
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
    UNIQUE(session_id, sequence, event_type, source_line)
);

CREATE TABLE IF NOT EXISTS session_pins (
    session_id INTEGER PRIMARY KEY
        REFERENCES sessions(id) ON DELETE CASCADE,
    pinned_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_reference_scans (
    session_id INTEGER PRIMARY KEY
        REFERENCES sessions(id) ON DELETE CASCADE,
    source_fingerprint TEXT NOT NULL,
    extractor_version TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK(status IN ('ok', 'partial', 'error')),
    observed_target_count INTEGER NOT NULL DEFAULT 0
        CHECK(observed_target_count >= 0),
    retained_target_count INTEGER NOT NULL DEFAULT 0
        CHECK(retained_target_count >= 0 AND retained_target_count <= 100),
    error_code TEXT,
    error_message TEXT
        CHECK(error_message IS NULL OR length(error_message) <= 500),
    scanned_at TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(length(source_fingerprint) = 64),
    CHECK(length(extractor_version) > 0 AND length(extractor_version) <= 80),
    CHECK(retained_target_count <= observed_target_count),
    CHECK(
        (status = 'ok' AND retained_target_count = observed_target_count)
        OR (
            status = 'partial'
            AND retained_target_count = 100
            AND observed_target_count > retained_target_count
        )
        OR status = 'error'
    ),
    CHECK(
        (status = 'error' AND error_code IS NOT NULL)
        OR (
            status IN ('ok', 'partial')
            AND error_code IS NULL
            AND error_message IS NULL
        )
    ),
    CHECK(
        error_code IS NULL
        OR (length(error_code) > 0 AND length(error_code) <= 80)
    )
);

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

CREATE TABLE IF NOT EXISTS usage_price_snapshots (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    calculator_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_model_prices (
    snapshot_id TEXT NOT NULL REFERENCES usage_price_snapshots(id) ON DELETE RESTRICT,
    model_name TEXT NOT NULL,
    input_usd_per_million TEXT NOT NULL,
    output_usd_per_million TEXT NOT NULL,
    cache_write_usd_per_million TEXT,
    cache_read_usd_per_million TEXT,
    long_context_threshold_tokens INTEGER
        CHECK(long_context_threshold_tokens IS NULL OR long_context_threshold_tokens > 0),
    long_context_input_usd_per_million TEXT,
    long_context_output_usd_per_million TEXT,
    long_context_cache_write_usd_per_million TEXT,
    long_context_cache_read_usd_per_million TEXT,
    PRIMARY KEY(snapshot_id, model_name)
);

CREATE TABLE IF NOT EXISTS usage_records (
    id TEXT PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    source_record_id TEXT NOT NULL,
    source_line INTEGER NOT NULL,
    occurred_at TEXT,
    raw_model TEXT,
    model_name TEXT,
    input_tokens INTEGER CHECK(input_tokens IS NULL OR input_tokens >= 0),
    output_tokens INTEGER CHECK(output_tokens IS NULL OR output_tokens >= 0),
    cache_write_tokens INTEGER CHECK(cache_write_tokens IS NULL OR cache_write_tokens >= 0),
    cache_read_tokens INTEGER CHECK(cache_read_tokens IS NULL OR cache_read_tokens >= 0),
    reasoning_tokens INTEGER CHECK(reasoning_tokens IS NULL OR reasoning_tokens >= 0),
    source_total_tokens INTEGER CHECK(source_total_tokens IS NULL OR source_total_tokens >= 0),
    total_tokens INTEGER CHECK(total_tokens IS NULL OR total_tokens >= 0),
    total_semantics TEXT NOT NULL,
    aggregation_scope TEXT NOT NULL DEFAULT 'direct'
        CHECK(aggregation_scope IN ('direct', 'includes_children')),
    capability_state TEXT NOT NULL
        CHECK(capability_state IN ('complete', 'partial', 'malformed')),
    capability_json TEXT NOT NULL,
    calculation_state TEXT NOT NULL
        CHECK(calculation_state IN ('priced', 'unpriced', 'partial', 'failed')),
    estimated_cost_usd TEXT,
    price_snapshot_id TEXT NOT NULL
        REFERENCES usage_price_snapshots(id) ON DELETE RESTRICT,
    calculator_version TEXT NOT NULL,
    normalizer_version TEXT NOT NULL DEFAULT 'legacy-v1',
    calculated_at TEXT NOT NULL,
    workspace_id_snapshot INTEGER,
    project_key TEXT,
    project_name_snapshot TEXT,
    project_path_snapshot TEXT,
    project_git_root_snapshot TEXT,
    attribution_basis TEXT NOT NULL DEFAULT 'unassigned'
        CHECK(attribution_basis IN ('git_root', 'workspace_path', 'unassigned')),
    attributed_at TEXT NOT NULL,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(
        (calculation_state = 'priced' AND estimated_cost_usd IS NOT NULL)
        OR (calculation_state != 'priced' AND estimated_cost_usd IS NULL)
    ),
    UNIQUE(source_id, session_id, source_record_id)
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
    url TEXT NOT NULL,
    summary TEXT,
    source_role TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS atlassian_sites (
    id INTEGER PRIMARY KEY,
    source_instance_id INTEGER
        REFERENCES external_source_instances(id) ON DELETE SET NULL,
    normalized_domain TEXT NOT NULL,
    display_name TEXT,
    remote_site_id TEXT,
    canonical_base_url TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_instance_id, normalized_domain),
    UNIQUE(source_instance_id, remote_site_id),
    CHECK(length(normalized_domain) > 0),
    CHECK(remote_site_id IS NULL OR length(remote_site_id) > 0)
);

CREATE TABLE IF NOT EXISTS atlassian_site_bindings (
    id INTEGER PRIMARY KEY,
    site_id INTEGER NOT NULL
        REFERENCES atlassian_sites(id) ON DELETE CASCADE,
    source_instance_id INTEGER NOT NULL
        REFERENCES external_source_instances(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site_id, source_instance_id)
);

CREATE TABLE IF NOT EXISTS atlassian_spaces (
    id INTEGER PRIMARY KEY,
    site_id INTEGER NOT NULL
        REFERENCES atlassian_sites(id) ON DELETE RESTRICT,
    source_instance_id INTEGER
        REFERENCES external_source_instances(id) ON DELETE SET NULL,
    service TEXT NOT NULL
        CHECK(service IN ('jira', 'confluence')),
    remote_id TEXT,
    space_key TEXT,
    name TEXT NOT NULL,
    canonical_url TEXT NOT NULL,
    coverage TEXT NOT NULL
        CHECK(coverage IN ('selected-content', 'full-content')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site_id, service, remote_id),
    UNIQUE(site_id, service, space_key),
    CHECK(remote_id IS NOT NULL OR space_key IS NOT NULL),
    CHECK(remote_id IS NULL OR length(remote_id) > 0),
    CHECK(space_key IS NULL OR length(space_key) > 0),
    CHECK(length(canonical_url) > 0)
);

CREATE TABLE IF NOT EXISTS atlassian_items (
    external_resource_id INTEGER PRIMARY KEY
        REFERENCES external_resources(id) ON DELETE CASCADE,
    site_id INTEGER NOT NULL
        REFERENCES atlassian_sites(id) ON DELETE RESTRICT,
    source_instance_id INTEGER
        REFERENCES external_source_instances(id) ON DELETE SET NULL,
    space_id INTEGER
        REFERENCES atlassian_spaces(id) ON DELETE SET NULL,
    service TEXT NOT NULL
        CHECK(service IN ('jira', 'confluence')),
    item_type TEXT NOT NULL
        CHECK(item_type IN ('jira_issue', 'confluence_page')),
    remote_id TEXT,
    remote_key TEXT,
    coverage TEXT NOT NULL DEFAULT 'reference'
        CHECK(coverage IN ('reference', 'metadata', 'indexed')),
    attention TEXT NOT NULL DEFAULT 'normal'
        CHECK(attention IN ('normal', 'pinned', 'ignored', 'archived')),
    confirmed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(external_resource_id, site_id),
    UNIQUE(site_id, service, remote_id),
    UNIQUE(site_id, service, remote_key),
    CHECK(
        (service = 'jira' AND item_type = 'jira_issue')
        OR
        (service = 'confluence' AND item_type = 'confluence_page')
    ),
    CHECK(remote_id IS NULL OR length(remote_id) > 0),
    CHECK(remote_key IS NULL OR length(remote_key) > 0)
);

CREATE TABLE IF NOT EXISTS atlassian_item_urls (
    id INTEGER PRIMARY KEY,
    external_resource_id INTEGER NOT NULL,
    site_id INTEGER NOT NULL,
    url_role TEXT NOT NULL
        CHECK(url_role IN ('canonical', 'alias')),
    observed_url TEXT NOT NULL,
    normalized_url TEXT NOT NULL,
    first_observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(external_resource_id, site_id)
        REFERENCES atlassian_items(external_resource_id, site_id)
        ON DELETE CASCADE,
    UNIQUE(site_id, normalized_url),
    CHECK(length(observed_url) > 0),
    CHECK(length(normalized_url) > 0)
);

CREATE TABLE IF NOT EXISTS atlassian_item_remote_state (
    external_resource_id INTEGER PRIMARY KEY
        REFERENCES atlassian_items(external_resource_id) ON DELETE CASCADE,
    metadata_schema_version TEXT NOT NULL DEFAULT 'localbrain.atlassian-metadata.v1',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    remote_version TEXT,
    remote_updated_at TEXT,
    last_attempted_at TEXT,
    last_successful_at TEXT,
    last_confirmed_at TEXT,
    last_outcome TEXT
        CHECK(
            last_outcome IS NULL
            OR last_outcome IN (
                'resolved',
                'unchanged',
                'changed',
                'unavailable',
                'not_found',
                'error'
            )
        ),
    last_error_code TEXT,
    known_changed INTEGER NOT NULL DEFAULT 0
        CHECK(known_changed IN (0, 1)),
    projection_stale INTEGER NOT NULL DEFAULT 0
        CHECK(projection_stale IN (0, 1)),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(
        (
            last_outcome IN ('unavailable', 'not_found', 'error')
            AND last_error_code IS NOT NULL
        )
        OR
        (
            (
                last_outcome IS NULL
                OR last_outcome IN ('resolved', 'unchanged', 'changed')
            )
            AND last_error_code IS NULL
        )
    ),
    CHECK(
        last_error_code IS NULL
        OR (length(last_error_code) > 0 AND length(last_error_code) <= 80)
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

CREATE TABLE IF NOT EXISTS atlassian_classifications (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL
        CHECK(kind IN ('topic', 'tag')),
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kind, normalized_name),
    CHECK(length(name) > 0 AND length(name) <= 160),
    CHECK(length(normalized_name) > 0 AND length(normalized_name) <= 320),
    CHECK(description IS NULL OR length(description) <= 4000),
    CHECK(kind = 'topic' OR description IS NULL)
);

CREATE TABLE IF NOT EXISTS atlassian_item_classifications (
    external_resource_id INTEGER NOT NULL
        REFERENCES atlassian_items(external_resource_id) ON DELETE CASCADE,
    classification_id INTEGER NOT NULL
        REFERENCES atlassian_classifications(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(external_resource_id, classification_id)
);

CREATE TABLE IF NOT EXISTS atlassian_evidence_scans (
    id INTEGER PRIMARY KEY,
    session_id INTEGER
        REFERENCES sessions(id) ON DELETE CASCADE,
    source_path TEXT,
    document_id INTEGER UNIQUE
        REFERENCES context_documents(id) ON DELETE CASCADE,
    source_fingerprint TEXT NOT NULL,
    site_fingerprint TEXT NOT NULL,
    extractor_version TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK(status IN ('ok', 'error')),
    error_code TEXT,
    error_message TEXT
        CHECK(error_message IS NULL OR length(error_message) <= 500),
    scanned_at TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(length(source_fingerprint) = 64),
    CHECK(length(site_fingerprint) = 64),
    CHECK(
        (
            session_id IS NOT NULL
            AND source_path IS NOT NULL
            AND document_id IS NULL
        )
        OR (
            session_id IS NULL
            AND source_path IS NULL
            AND document_id IS NOT NULL
        )
    ),
    CHECK(source_path IS NULL OR length(source_path) <= 8000),
    CHECK(
        (status = 'error' AND error_code IS NOT NULL)
        OR (status = 'ok' AND error_code IS NULL AND error_message IS NULL)
    ),
    CHECK(
        error_code IS NULL
        OR (length(error_code) > 0 AND length(error_code) <= 80)
    ),
    UNIQUE(session_id, source_path)
);

CREATE TABLE IF NOT EXISTS atlassian_item_evidence (
    id INTEGER PRIMARY KEY,
    external_resource_id INTEGER NOT NULL
        REFERENCES atlassian_items(external_resource_id) ON DELETE CASCADE,
    session_id INTEGER
        REFERENCES sessions(id) ON DELETE CASCADE,
    source_path TEXT,
    document_id INTEGER
        REFERENCES context_documents(id) ON DELETE CASCADE,
    source_channel TEXT NOT NULL
        CHECK(source_channel IN ('visible_text', 'approved_tool_result')),
    source_event_id TEXT,
    source_line INTEGER NOT NULL CHECK(source_line > 0),
    url_ordinal INTEGER NOT NULL CHECK(url_ordinal > 0),
    observed_url TEXT NOT NULL,
    normalized_url TEXT NOT NULL,
    observed_remote_id TEXT,
    observed_title TEXT,
    observed_at TEXT,
    extractor_version TEXT NOT NULL,
    evidence_key TEXT NOT NULL UNIQUE,
    first_observed_at TEXT NOT NULL,
    last_observed_at TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(
        (
            session_id IS NOT NULL
            AND source_path IS NOT NULL
            AND document_id IS NULL
            AND source_event_id IS NOT NULL
        )
        OR (
            session_id IS NULL
            AND source_path IS NULL
            AND document_id IS NOT NULL
            AND source_event_id IS NULL
        )
    ),
    CHECK(source_path IS NULL OR length(source_path) <= 8000),
    CHECK(length(observed_url) > 0 AND length(observed_url) <= 8000),
    CHECK(length(normalized_url) > 0 AND length(normalized_url) <= 8000),
    CHECK(
        observed_remote_id IS NULL OR length(observed_remote_id) <= 300
    ),
    CHECK(observed_title IS NULL OR length(observed_title) <= 500),
    CHECK(length(evidence_key) = 64)
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

CREATE TABLE IF NOT EXISTS external_sync_runs (
    maintenance_run_id TEXT PRIMARY KEY
        REFERENCES maintenance_runs(id) ON DELETE CASCADE,
    source_instance_id INTEGER
        REFERENCES external_source_instances(id) ON DELETE SET NULL,
    source_kind TEXT NOT NULL,
    service TEXT NOT NULL,
    requested_scope_kind TEXT NOT NULL
        CHECK(
            requested_scope_kind IN (
                'item',
                'space',
                'thread',
                'workstream',
                'all_known'
            )
        ),
    selected_target_count INTEGER NOT NULL
        CHECK(selected_target_count >= 0),
    manifest_schema_version TEXT NOT NULL,
    read_policy_version TEXT NOT NULL,
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
CREATE INDEX IF NOT EXISTS idx_session_reference_evidence_session
    ON session_reference_evidence(
        session_id,
        target_kind,
        target_key,
        evidence_kind,
        source_line,
        evidence_ordinal
    );
CREATE INDEX IF NOT EXISTS idx_session_reference_evidence_document
    ON session_reference_evidence(context_document_id, session_id);
CREATE INDEX IF NOT EXISTS idx_session_reference_evidence_atlassian
    ON session_reference_evidence(external_resource_id, session_id);
CREATE INDEX IF NOT EXISTS idx_usage_records_session_time
    ON usage_records(session_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_usage_records_source_time
    ON usage_records(source_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_usage_records_model_time
    ON usage_records(model_name, occurred_at);
CREATE INDEX IF NOT EXISTS idx_documents_mtime
    ON context_documents(mtime_ns DESC);
CREATE INDEX IF NOT EXISTS idx_documents_source
    ON context_documents(source_id);
CREATE INDEX IF NOT EXISTS idx_documents_workspace
    ON context_documents(workspace_id, mtime_ns DESC);
CREATE INDEX IF NOT EXISTS idx_threads_workstream
    ON threads(workstream_id, status, position);
CREATE INDEX IF NOT EXISTS idx_thread_links_entity
    ON thread_links(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_workstream_links_entity
    ON workstream_links(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_target
    ON suggestions(target_type, target_id, status);
CREATE INDEX IF NOT EXISTS idx_checkpoints_workstream_version
    ON checkpoints(workstream_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_external_sync_runs_source_instance
    ON external_sync_runs(source_instance_id, maintenance_run_id);
CREATE INDEX IF NOT EXISTS idx_external_sync_runs_scope
    ON external_sync_runs(requested_scope_kind, maintenance_run_id);
CREATE INDEX IF NOT EXISTS idx_atlassian_sites_source
    ON atlassian_sites(source_instance_id, normalized_domain);
CREATE INDEX IF NOT EXISTS idx_atlassian_site_bindings_source
    ON atlassian_site_bindings(source_instance_id, site_id);
CREATE INDEX IF NOT EXISTS idx_atlassian_spaces_site
    ON atlassian_spaces(site_id, service, name);
CREATE INDEX IF NOT EXISTS idx_atlassian_items_site
    ON atlassian_items(site_id, service, coverage);
CREATE INDEX IF NOT EXISTS idx_atlassian_items_space
    ON atlassian_items(space_id, service);
CREATE INDEX IF NOT EXISTS idx_atlassian_item_urls_item
    ON atlassian_item_urls(external_resource_id, url_role);
CREATE UNIQUE INDEX IF NOT EXISTS idx_atlassian_item_urls_canonical
    ON atlassian_item_urls(external_resource_id)
    WHERE url_role = 'canonical';
CREATE INDEX IF NOT EXISTS idx_atlassian_remote_state_check
    ON atlassian_item_remote_state(last_successful_at, last_outcome);
CREATE INDEX IF NOT EXISTS idx_atlassian_item_classifications_classification
    ON atlassian_item_classifications(classification_id, external_resource_id);
CREATE INDEX IF NOT EXISTS idx_atlassian_evidence_item
    ON atlassian_item_evidence(external_resource_id, last_observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_atlassian_evidence_session
    ON atlassian_item_evidence(session_id, source_line, url_ordinal);
CREATE INDEX IF NOT EXISTS idx_atlassian_evidence_document
    ON atlassian_item_evidence(document_id, source_line, url_ordinal);
