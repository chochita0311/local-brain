//! Snapshot and inventory SQL for read-only dashboard projections.

pub const DASHBOARD_STATS_0: &str = r#"
SELECT COUNT(*) AS count FROM sessions WHERE session_class = 'work' AND session_role = 'primary'{source_condition}
"#;

pub const DASHBOARD_STATS_1: &str = r#"
SELECT COUNT(*) AS count
FROM activity_events
JOIN sessions ON sessions.id = activity_events.session_id
WHERE sessions.session_class = 'work'
  AND sessions.session_role = 'primary'
{source_condition}
"#;

pub const DASHBOARD_STATS_2: &str = r#"
SELECT COUNT(*) AS count
FROM context_documents
LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
WHERE context_documents.context_root_id IS NULL OR context_roots.enabled = 1
"#;

pub const DASHBOARD_STATS_3: &str = r#"
SELECT COUNT(*) AS count FROM workspaces
"#;

pub const DASHBOARD_STATS_4: &str = r#"
SELECT COUNT(*) AS count
FROM workspaces
WHERE exists_now = 0
  AND EXISTS (
      SELECT 1 FROM sessions
      WHERE sessions.workspace_id = workspaces.id
        AND sessions.session_class = 'work'
        AND sessions.session_role = 'primary'
{source_condition})
"#;

pub const DASHBOARD_STATS_5: &str = r#"
SELECT COUNT(*) AS count FROM sessions
WHERE session_class = 'work'
  AND session_role = 'primary'
  AND datetime(last_event_at) >= datetime('now', '-7 days')
{source_condition}
"#;

pub const DASHBOARD_STATS_6: &str = r#"
SELECT COUNT(DISTINCT workspace_id) AS count FROM sessions
WHERE workspace_id IS NOT NULL
  AND session_class = 'work'
  AND session_role = 'primary'
  AND datetime(last_event_at) >= datetime('now', '-7 days')
{source_condition}
"#;

pub const DASHBOARD_STATS_7: &str = r#"
WITH ordered AS (
    SELECT workspace_id,
           LAG(workspace_id) OVER (ORDER BY last_event_at) AS previous_workspace
    FROM sessions
    WHERE workspace_id IS NOT NULL
      AND session_class = 'work'
      AND session_role = 'primary'
      AND datetime(last_event_at) >= datetime('now', '-7 days')
{source_condition}
)
SELECT COUNT(*) AS count
FROM ordered
WHERE previous_workspace IS NOT NULL
  AND workspace_id != previous_workspace
"#;

pub const DAILY_ACTIVITY: &str = r#"
WITH RECURSIVE dates(day, position) AS (
    SELECT date('now', ?), 1
    UNION ALL
    SELECT date(day, '+1 day'), position + 1
    FROM dates
    WHERE position < ?
), activity AS (
    SELECT date(last_event_at) AS day, COUNT(*) AS session_count
    FROM sessions
    WHERE last_event_at IS NOT NULL AND session_class = 'work'
      AND session_role = 'primary'
    GROUP BY date(last_event_at)
)
SELECT dates.day, COALESCE(activity.session_count, 0) AS session_count
FROM dates
LEFT JOIN activity ON activity.day = dates.day
ORDER BY dates.day
"#;

pub const SOURCE_ACTIVITY: &str = r#"
SELECT sources.id, sources.provider_kind, sources.name,
       COUNT(DISTINCT sessions.id) AS session_count,
       COUNT(activity_events.id) AS event_count,
       MAX(sessions.last_event_at) AS last_activity_at
FROM sources
LEFT JOIN sessions ON sessions.source_id = sources.id
    AND sessions.session_class = 'work'
    AND sessions.session_role = 'primary'
LEFT JOIN activity_events ON activity_events.session_id = sessions.id
WHERE sources.provider_kind IN ('claude', 'codex')
GROUP BY sources.id
ORDER BY event_count DESC
"#;

pub const TOP_TOOLS: &str = r#"
SELECT tool_name, COUNT(*) AS use_count
FROM activity_events
JOIN sessions ON sessions.id = activity_events.session_id
WHERE event_type = 'tool_call' AND tool_name IS NOT NULL
  AND sessions.session_class = 'work'
  AND sessions.session_role = 'primary'
GROUP BY tool_name
ORDER BY use_count DESC, tool_name
LIMIT ?
"#;

pub const TOP_WORKSPACE_ACTIVITY: &str = r#"
SELECT workspaces.id, workspaces.display_name, workspaces.canonical_path,
       workspaces.git_root, workspaces.exists_now,
       COUNT(sessions.id) AS session_count,
       COALESCE(SUM(sessions.event_count), 0) AS event_count,
       MAX(sessions.last_event_at) AS last_activity_at
FROM workspaces
JOIN sessions ON sessions.workspace_id = workspaces.id
    AND sessions.session_class = 'work'
    AND sessions.session_role = 'primary'
GROUP BY workspaces.id
ORDER BY session_count DESC, last_activity_at DESC
LIMIT ?
"#;

pub const SOURCE_INVENTORY: &str = r#"
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
"#;
