"""Database-only Session original availability, independent from scan success."""


def source_presence_columns(session_alias="sessions"):
    # Aliases are fixed query-owned identifiers, never request input. A Session
    # can have several native files, including replacement representations.
    return """
        (SELECT CASE
           WHEN MAX(files.presence_state='PRESENT')=1 THEN 'PRESENT'
           WHEN COUNT(*)>0 AND MIN(files.presence_state='MISSING')=1 THEN 'MISSING'
           ELSE 'UNKNOWN' END
         FROM source_files AS files WHERE files.session_id={session}.id)
            AS source_presence_state,
        (SELECT MAX(files.presence_checked_at) FROM source_files AS files
         WHERE files.session_id={session}.id) AS source_presence_checked_at,
        COALESCE(
          (SELECT files.presence_error FROM source_files AS files
           WHERE files.session_id={session}.id AND files.presence_error IS NOT NULL
           ORDER BY files.presence_checked_at DESC,files.id DESC LIMIT 1),
          CASE WHEN sources.last_scan_status IN ('unavailable','scan_failed')
               THEN sources.last_scan_error END) AS source_presence_error
    """.format(session=session_alias)
