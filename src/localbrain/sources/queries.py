import sqlite3


def source_inventory(connection: sqlite3.Connection):
    return connection.execute(
        """
        WITH file_counts AS (
            SELECT source_id, COUNT(*) AS file_count,
                   COUNT(CASE WHEN status != 'ok' THEN 1 END) AS error_count
            FROM source_files
            GROUP BY source_id
        ), session_counts AS (
            SELECT source_id, COUNT(*) AS session_count
            FROM sessions
            WHERE session_class = 'work' AND session_role = 'primary'
            GROUP BY source_id
        ), document_counts AS (
            SELECT context_documents.source_id, COUNT(*) AS document_count
            FROM context_documents
            LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
            WHERE context_documents.context_root_id IS NULL OR context_roots.enabled = 1
            GROUP BY context_documents.source_id
        )
        SELECT sources.id, sources.provider_kind, sources.name,
               sources.root_path,
               sources.last_scanned_at, sources.last_scan_success_at,
               sources.last_scan_status, sources.last_scan_error,
               COALESCE(file_counts.file_count, 0) AS file_count,
               COALESCE(session_counts.session_count, 0) AS session_count,
               COALESCE(document_counts.document_count, 0) AS document_count,
               COALESCE(file_counts.error_count, 0) AS error_count
        FROM sources
        LEFT JOIN file_counts ON file_counts.source_id = sources.id
        LEFT JOIN session_counts ON session_counts.source_id = sources.id
        LEFT JOIN document_counts ON document_counts.source_id = sources.id
        ORDER BY sources.profile_position, sources.id
        """
    ).fetchall()
