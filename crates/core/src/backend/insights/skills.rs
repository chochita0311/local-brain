//! Historical skill observations are ranked once per source/native session.
use crate::backend::{
    db,
    ingest::{CLAUDE_SESSION_REVISION, CODEX_SESSION_REVISION},
    Result,
};
use rusqlite::Connection;
use serde_json::{json, Value};
pub fn skill_insights_data(connection: &Connection) -> Result<Value> {
    let grouped=db::rows(connection,"WITH reference_sessions AS (SELECT skill_group_key, MIN(skill_name) AS skill_name, MAX(julianday(occurred_at)) AS occurred_at FROM skill_observations WHERE state='observed' GROUP BY source_id,external_session_id,skill_group_key) SELECT skill_group_key,MIN(skill_name) AS skill_name,COUNT(*) AS use_count,strftime('%Y-%m-%dT%H:%M:%SZ',MAX(occurred_at)) AS last_used_at FROM reference_sessions GROUP BY skill_group_key ORDER BY use_count DESC,skill_group_key ASC",[])?;
    let ranking=grouped.iter().enumerate().map(|(index,row)|json!({"rank":index+1,"name":row["skill_name"],"use_count":row["use_count"],"last_used_at":row["last_used_at"]})).collect::<Vec<_>>();
    let coverage=db::row(connection,"SELECT COUNT(*) AS file_count,SUM(CASE WHEN source_files.status='ok' AND source_files.presence_state='PRESENT' AND ((sources.provider_kind='claude' AND source_files.session_contract_version=?) OR (sources.provider_kind='codex' AND source_files.session_contract_version=?)) THEN 1 ELSE 0 END) AS current_file_count FROM source_files JOIN sources ON sources.id=source_files.source_id WHERE sources.provider_kind IN ('claude','codex')",[CLAUDE_SESSION_REVISION,CODEX_SESSION_REVISION])?.unwrap();
    let count = coverage["file_count"].as_i64().unwrap_or(0);
    let current = coverage["current_file_count"].as_i64().unwrap_or(0);
    Ok(
        json!({"ranking":ranking,"top":ranking.first(),"coverage":{"file_count":count,"current_file_count":current,"state":if count==0{"not_scanned"}else if current<count{"partial"}else{"current"}}}),
    )
}
