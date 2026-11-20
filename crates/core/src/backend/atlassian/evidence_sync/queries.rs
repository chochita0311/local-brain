//! Stable local source queries; persisted evidence alone owns this action.
pub const CURRENT_DOCUMENT: &str = r#"
        SELECT context_documents.id, context_documents.content_hash,
               context_documents.context_root_id,
               context_roots.enabled, context_roots.readable,
               context_roots.status
        FROM context_documents
        LEFT JOIN context_roots
          ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.id = ?
        "#;
pub const DOCUMENT_CURRENT_SCAN: &str = r#"
        SELECT source_fingerprint, site_fingerprint, extractor_version, status
        FROM atlassian_evidence_scans
        WHERE document_id = ?
        "#;
pub const SESSION: &str = r#"
            SELECT id, session_class, session_role, index_policy
            FROM sessions WHERE id = ?
            "#;
pub const SESSION_SCAN: &str = r#"
            SELECT status, extractor_version, observed_target_count,
                   retained_target_count
            FROM session_reference_scans
            WHERE session_id = ?
            "#;
pub const SESSION_EVIDENCE: &str = r#"
            SELECT source_path, source_event_id, source_line,
                   evidence_ordinal, normalized_url, evidence_kind,
                   observed_at, target_key
            FROM session_reference_evidence
            WHERE session_id = ?
              AND normalized_url IS NOT NULL
              AND evidence_kind IN (
                  'user_mention', 'assistant_mention', 'tool_result'
              )
            ORDER BY target_key, source_path, source_event_id,
                     source_line, evidence_ordinal, id
            "#;
