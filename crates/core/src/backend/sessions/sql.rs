//! SQL shared by Session read and user-owned metadata services.

pub const RECENT_SESSIONS: &str = r#"
SELECT
    sessions.*,

    sources.provider_kind,
    sources.name AS source_name,
    workspaces.display_name AS workspace_name,
    workspaces.canonical_path AS workspace_path,
    workspaces.git_root,
    workspaces.exists_now
FROM sessions
JOIN sources ON sources.id = sessions.source_id
LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
{where}
ORDER BY COALESCE(sessions.last_event_at, sessions.started_at) DESC
LIMIT ?
"#;

pub const SESSION_INVENTORY_PAGE_0: &str = r#"
SELECT COUNT(*) AS count
FROM sessions
JOIN sources ON sources.id = sessions.source_id
WHERE {where}
"#;

pub const SESSION_INVENTORY_PAGE_1: &str = r#"
SELECT
    sessions.*,

    sources.provider_kind,
    sources.name AS source_name,
    workspaces.display_name AS workspace_name,
    workspaces.canonical_path AS workspace_path,
    workspaces.git_root,
    workspaces.exists_now,
    {source_presence},
    session_pins.pinned_at
FROM sessions
JOIN sources ON sources.id = sessions.source_id
LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
LEFT JOIN session_pins ON session_pins.session_id = sessions.id
WHERE {where}
ORDER BY COALESCE(sessions.last_event_at, sessions.started_at) DESC,
         sessions.id DESC
LIMIT ? OFFSET ?
"#;

pub const SESSION_INVENTORY_PAGE_2: &str = r#"
SELECT children.*, {source_presence},
       sources.provider_kind,
       sources.name AS source_name,
       workspaces.display_name AS workspace_name,
       workspaces.canonical_path AS workspace_path,
       workspaces.exists_now
FROM sessions AS children
JOIN sessions AS parents ON parents.id = children.parent_session_id
JOIN sources ON sources.id = children.source_id
LEFT JOIN workspaces ON workspaces.id = children.workspace_id
WHERE children.parent_session_id IN ({placeholders})
  AND children.session_class = 'work'
  AND children.session_role = 'subsession'
  AND parents.session_class = 'work'
  AND parents.session_role = 'primary'
  AND parents.source_id = children.source_id
ORDER BY children.parent_session_id,
         COALESCE(children.last_event_at, children.started_at) DESC,
         children.id DESC
"#;

pub const SESSION_CHART_INVENTORY: &str = r#"
SELECT sessions.id, sessions.source_id, COALESCE(sessions.display_title, sessions.title) AS title, sessions.started_at,
       sessions.last_event_at, sessions.cwd_raw, sessions.git_branch,
        sources.provider_kind,
       sources.name AS source_name
FROM sessions JOIN sources ON sources.id = sessions.source_id
WHERE {where}
ORDER BY sessions.id
"#;

pub const SESSION_CHART_ACTIVITY_0: &str = r#"
SELECT id, started_at, last_event_at FROM sessions
WHERE id = ? AND session_class = 'work' AND session_role = 'primary'
"#;

pub const SESSION_CHART_ACTIVITY_1: &str = r#"
SELECT occurred_at FROM activity_events WHERE session_id = ?
"#;

pub const PROJECT_ACTIVITY: &str = r#"
WITH session_activity AS (
    SELECT sessions.workspace_id,
           COUNT(*) AS session_count,
           COALESCE(SUM(sessions.event_count), 0) AS event_count,
           MAX(sessions.last_event_at) AS last_activity_at,
           COUNT(DISTINCT sessions.source_id) AS source_count
    FROM sessions
    JOIN sources ON sources.id = sessions.source_id
    WHERE sessions.workspace_id IS NOT NULL
      AND sessions.session_class = 'work'
      AND sessions.session_role = 'primary'
      {source_condition}
    GROUP BY sessions.workspace_id
)
SELECT workspaces.id, workspaces.display_name, workspaces.canonical_path,
       workspaces.git_root, workspaces.exists_now,
       COALESCE(session_activity.session_count, 0) AS session_count,
       (SELECT COUNT(*) FROM context_documents
        LEFT JOIN context_roots
          ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.workspace_id = workspaces.id
          AND (context_documents.context_root_id IS NULL
               OR context_roots.enabled = 1)) AS document_count,
       COALESCE(session_activity.event_count, 0) AS event_count,
       session_activity.last_activity_at,
       COALESCE(session_activity.source_count, 0) AS source_count
FROM workspaces
JOIN session_activity
  ON session_activity.workspace_id = workspaces.id
ORDER BY session_activity.last_activity_at DESC, workspaces.display_name
"#;

pub const SESSION_SOURCE_SCOPES: &str = r#"
SELECT sources.id,
       sources.profile_color AS color, sources.provider_kind, sources.name AS display_label,
       COUNT(CASE WHEN sessions.session_class = 'work'
                        AND sessions.session_role = 'primary'
                  THEN 1 END) AS eligible_session_count
FROM sources
LEFT JOIN sessions ON sessions.source_id = sources.id
WHERE sources.provider_kind != 'context'
GROUP BY sources.id
ORDER BY sources.profile_position, sources.id
"#;

pub const SESSION_ID_PREFIX: &str = r#"
SELECT DISTINCT external_id FROM sessions
WHERE substr(external_id, 1, ?) = ? AND external_id != ?
"#;

pub const SESSION_DETAIL: &str = r#"
SELECT sessions.*, {source_presence},
       sources.provider_kind, sources.name AS source_name,
       workspaces.display_name AS workspace_name,
       workspaces.canonical_path AS workspace_path,
       workspaces.git_root, workspaces.exists_now,
       session_pins.pinned_at
FROM sessions
JOIN sources ON sources.id = sessions.source_id
LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
LEFT JOIN session_pins ON session_pins.session_id = sessions.id
LEFT JOIN sessions AS parent_sessions
  ON parent_sessions.id = sessions.parent_session_id
WHERE sessions.id = ?
  AND sessions.session_class = 'work'
  AND (
    sessions.session_role = 'primary'
    OR (
      sessions.session_role = 'subsession'
      AND parent_sessions.session_role = 'primary'
      AND parent_sessions.source_id = sessions.source_id
    )
  )
"#;

pub const SESSION_EVENTS: &str = r#"
SELECT * FROM activity_events
WHERE session_id = ?
ORDER BY sequence
LIMIT ?
"#;

pub const SESSION_CONVERSATION_EVENTS: &str = r#"
SELECT * FROM activity_events
WHERE session_id = ? AND event_type = 'message'
ORDER BY sequence, id
"#;

pub const SESSION_PARENT: &str = r#"
SELECT parents.*,
       sources.provider_kind,
       sources.name AS source_name,
       workspaces.display_name AS workspace_name,
       workspaces.canonical_path AS workspace_path,
       workspaces.git_root, workspaces.exists_now
FROM sessions AS children
JOIN sessions AS parents ON parents.id = children.parent_session_id
JOIN sources ON sources.id = parents.source_id
LEFT JOIN workspaces ON workspaces.id = parents.workspace_id
WHERE children.id = ?
  AND children.session_class = 'work'
  AND children.session_role = 'subsession'
  AND parents.session_class = 'work'
  AND parents.session_role = 'primary'
  AND parents.source_id = children.source_id
"#;

pub const SESSION_SUBSESSIONS: &str = r#"
SELECT children.*, {source_presence},
       sources.provider_kind,
       sources.name AS source_name,
       workspaces.display_name AS workspace_name,
       workspaces.canonical_path AS workspace_path,
       workspaces.git_root, workspaces.exists_now
FROM sessions AS parents
JOIN sessions AS children ON children.parent_session_id = parents.id
JOIN sources ON sources.id = children.source_id
LEFT JOIN workspaces ON workspaces.id = children.workspace_id
WHERE parents.id = ?
  AND parents.session_class = 'work'
  AND parents.session_role = 'primary'
  AND children.session_class = 'work'
  AND children.session_role = 'subsession'
  AND children.source_id = parents.source_id
ORDER BY COALESCE(children.last_event_at, children.started_at) DESC,
         children.id DESC
"#;

pub const ELIGIBLE_SESSION: &str = r#"
SELECT id, session_class, session_role
FROM sessions
WHERE id = ?
"#;

pub const PIN_SESSION_0: &str = r#"
INSERT INTO session_pins(session_id, pinned_at)
VALUES (?, ?)
ON CONFLICT(session_id) DO NOTHING
"#;

pub const PIN_SESSION_1: &str = r#"
SELECT session_id, pinned_at FROM session_pins WHERE session_id = ?
"#;

pub const UNPIN_SESSION: &str = r#"
DELETE FROM session_pins WHERE session_id = ?
"#;

pub const IS_SESSION_PINNED: &str = r#"
SELECT 1 FROM session_pins WHERE session_id = ?
"#;

pub const PINNED_SESSION_SELECT: &str = r#"
SELECT
    sessions.id,
    sessions.source_id,
    sessions.title,
    sessions.display_title,
    sessions.last_event_at,
    sessions.started_at,
    sessions.cwd_raw,
    sessions.source_path,
    sessions.git_branch,
    sessions.workspace_id,
    {source_presence},
    sources.provider_kind,
    sources.name AS source_name,
    workspaces.display_name AS workspace_name,
    workspaces.canonical_path AS workspace_path,
    workspaces.git_root AS workspace_git_root,
    workspaces.exists_now AS workspace_exists_now,
    session_pins.pinned_at
FROM session_pins
JOIN sessions ON sessions.id = session_pins.session_id
JOIN sources ON sources.id = sessions.source_id
LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
WHERE sessions.session_class = 'work'
  AND sessions.session_role = 'primary'
ORDER BY
    COALESCE(sessions.last_event_at, sessions.started_at) DESC,
    session_pins.pinned_at DESC,
    sessions.id DESC
"#;

pub const SOURCE_PRESENCE: &str = r#"
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
"#;
