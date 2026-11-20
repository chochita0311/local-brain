//! Session reference persistence statements.
pub const ELIGIBLE_DOCUMENT_ROWS: &str = r#"
SELECT context_documents.id, context_documents.path,
       context_documents.relative_path, context_documents.title,
       context_documents.workspace_id, context_documents.context_root_id
FROM context_documents
JOIN context_roots
  ON context_roots.id = context_documents.context_root_id
WHERE context_roots.enabled = 1
  AND context_roots.readable = 1
  AND context_roots.status = 'ready'
"#;

pub const RESOLVE_MARKDOWN_0: &str = r#"
SELECT DISTINCT r.id, r.locator
            FROM session_reference_evidence e
            JOIN reference_resources r ON r.id=e.resource_id
            WHERE e.session_id=? AND e.source_path=?
              AND e.source_event_id IS ? AND e.source_line=?
              AND e.evidence_ordinal=? AND e.observed_identity=?
              AND r.kind='path'
"#;

pub const RESOLVE_MARKDOWN_1: &str = r#"
SELECT identity_key FROM reference_resources WHERE id = ?
"#;

pub const SOURCE_SET_FINGERPRINT: &str = r#"
SELECT path, size_bytes, mtime_ns
FROM source_files
WHERE session_id = ? AND path != ?
ORDER BY path
"#;

pub const RECORDED_SOURCE_SET_FINGERPRINT: &str = r#"
SELECT path, size_bytes, mtime_ns
FROM source_files
WHERE session_id = ?
  AND status = 'ok'
  AND reference_contract_version = ?
ORDER BY path
"#;

pub const RECORD_SCAN: &str = r#"
INSERT INTO session_reference_scans(
    session_id, source_fingerprint, extractor_version, status,
    observed_target_count, retained_target_count,
    error_code, error_message, scanned_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(session_id) DO UPDATE SET
    source_fingerprint = excluded.source_fingerprint,
    extractor_version = excluded.extractor_version,
    status = excluded.status,
    observed_target_count = excluded.observed_target_count,
    retained_target_count = excluded.retained_target_count,
    error_code = excluded.error_code,
    error_message = excluded.error_message,
    scanned_at = excluded.scanned_at,
    updated_at = excluded.updated_at
"#;

pub const SESSION_REFERENCE_SCAN_IS_CURRENT_0: &str = r#"
SELECT * FROM session_reference_scans WHERE session_id = ?
"#;

pub const SESSION_REFERENCE_SCAN_IS_CURRENT_1: &str = r#"
SELECT 1
FROM source_files
WHERE session_id = ?
  AND status = 'ok'
  AND reference_contract_version = ?
LIMIT 1
"#;

pub const RECONCILE_SESSION_REFERENCES_0: &str = r#"
SELECT id, source_id, workspace_id, cwd_raw,
       session_class, session_role, index_policy
FROM sessions WHERE id = ?
"#;

pub const RECONCILE_SESSION_REFERENCES_1: &str = r#"
DELETE FROM session_reference_evidence WHERE session_id = ?
"#;

pub const RECONCILE_SESSION_REFERENCES_2: &str = r#"
DELETE FROM session_reference_scans WHERE session_id = ?
"#;

pub const RECONCILE_SESSION_REFERENCES_3: &str = r#"
SELECT evidence_key, first_observed_at
FROM session_reference_evidence
WHERE session_id = ? AND source_path = ?
"#;

pub const RECONCILE_SESSION_REFERENCES_4: &str = r#"
DELETE FROM session_reference_evidence
WHERE session_id = ? AND source_path = ?
"#;

pub const RECONCILE_SESSION_REFERENCES_5: &str = r#"
INSERT INTO session_reference_evidence(
    session_id, source_path, source_event_id, source_line,
    evidence_ordinal, resource_id, target_key,
    evidence_kind, read_outcome, observed_identity,
    normalized_url, tool_name, tool_call_id, observed_at,
    extractor_version, evidence_key,
    first_observed_at, last_observed_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(evidence_key) DO UPDATE SET
    observed_identity = excluded.observed_identity,
    normalized_url = excluded.normalized_url,
    observed_at = excluded.observed_at,
    last_observed_at = excluded.last_observed_at,
    updated_at = excluded.updated_at
"#;

pub const FINALIZE_SESSION_REFERENCES_0: &str = r#"
SELECT id, target_key, evidence_kind, read_outcome,
       source_path, source_event_id, source_line,
       evidence_ordinal, tool_call_id
FROM session_reference_evidence
WHERE session_id = ?
"#;

pub const FINALIZE_SESSION_REFERENCES_1: &str = r#"
DELETE FROM session_reference_evidence
WHERE session_id = ? AND target_key NOT IN ({})
"#;

pub const FINALIZE_SESSION_REFERENCES_2: &str = r#"
DELETE FROM session_reference_evidence WHERE session_id = ?
"#;

pub const FINALIZE_SESSION_REFERENCES_3: &str = r#"
DELETE FROM session_reference_evidence WHERE id IN ({})
"#;

pub const FINALIZE_SESSION_REFERENCES_4: &str = r#"
SELECT COUNT(DISTINCT target_key)
FROM session_reference_evidence WHERE session_id = ?
"#;

pub const CLEAR_SESSION_REFERENCE_SOURCE_0: &str = r#"
DELETE FROM session_reference_evidence
WHERE session_id = ? AND source_path = ?
"#;

pub const CLEAR_SESSION_REFERENCE_SOURCE_1: &str = r#"
DELETE FROM session_reference_scans WHERE session_id = ?
"#;

pub const MARK_SESSION_REFERENCE_ERROR: &str = r#"
SELECT * FROM session_reference_scans WHERE session_id = ?
"#;

pub const SESSION_REFERENCE_PROJECTION_0: &str = r#"
SELECT * FROM session_reference_scans WHERE session_id = ?
"#;

pub const SESSION_REFERENCE_PROJECTION_1: &str = r#"
SELECT session_reference_evidence.*,
       reference_resources.kind AS resource_kind,
       reference_resources.locator, reference_resources.product,
       context_documents.id AS context_document_id,
       context_documents.relative_path,
       context_roots.enabled AS document_enabled,
       context_roots.readable AS document_readable,
       context_roots.status AS document_status
FROM session_reference_evidence
JOIN reference_resources
  ON reference_resources.id = session_reference_evidence.resource_id
LEFT JOIN resource_documents
  ON resource_documents.resource_id = reference_resources.id
LEFT JOIN context_documents
  ON context_documents.id = resource_documents.document_id
LEFT JOIN context_roots
  ON context_roots.id = context_documents.context_root_id
WHERE session_reference_evidence.session_id = ?
ORDER BY session_reference_evidence.target_key,
         session_reference_evidence.source_line,
         session_reference_evidence.evidence_ordinal
"#;
