import sqlite3


def source_inventory(connection: sqlite3.Connection):
    return connection.execute(
        """
        SELECT sources.id, sources.provider_kind, sources.name,
               sources.root_path,
               sources.last_scanned_at, sources.last_scan_success_at,
               sources.last_scan_status, sources.last_scan_error,
               COUNT(DISTINCT source_files.id) AS file_count,
               COUNT(DISTINCT CASE WHEN sessions.session_class = 'work'
                                      AND sessions.session_role = 'primary'
                     THEN sessions.id END) AS session_count,
               COUNT(DISTINCT CASE
                     WHEN context_documents.context_root_id IS NULL
                       OR context_roots.enabled = 1
                     THEN context_documents.id END) AS document_count,
               COUNT(DISTINCT CASE WHEN source_files.status != 'ok'
                     THEN source_files.id END) AS error_count
        FROM sources
        LEFT JOIN source_files ON source_files.source_id = sources.id
        LEFT JOIN sessions ON sessions.source_id = sources.id
        LEFT JOIN context_documents ON context_documents.source_id = sources.id
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        GROUP BY sources.id
        ORDER BY sources.profile_position, sources.id
        """
    ).fetchall()
