pub use crate::backend::usage::ParsedUsageRecord;
use serde::{Deserialize, Serialize};
use serde_json::Value;

pub const CODEX_SESSION_REVISION: i64 = 15;
pub const CLAUDE_SESSION_REVISION: i64 = 8;
pub const CODEX_USAGE_CONTRACT_VERSION: &str =
    "codex-last-token-usage-v8-official-dated-service-tier";
pub const CLAUDE_USAGE_CONTRACT_VERSION: &str = "claude-message-usage-v3-official-pricing";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ParsedEvent {
    pub event_id: String,
    pub sequence: i64,
    pub source_line: i64,
    pub event_type: String,
    pub occurred_at: Option<String>,
    pub role: Option<String>,
    pub text: Option<String>,
    pub tool_name: Option<String>,
    pub message_phase: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ParsedUrlEvidence {
    pub observed_url: String,
    pub source_line: i64,
    pub url_ordinal: i64,
    pub source_channel: String,
    pub source_event_id: Option<String>,
    pub observed_at: Option<String>,
    pub observed_remote_id: Option<String>,
    pub observed_title: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ParsedReferenceCandidate {
    pub reference_kind: String,
    pub reference: String,
    pub evidence_kind: String,
    pub source_line: i64,
    pub evidence_ordinal: i64,
    pub source_event_id: Option<String>,
    pub observed_at: Option<String>,
    pub tool_name: Option<String>,
    pub tool_call_id: Option<String>,
    pub read_outcome: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ParsedSkillObservation {
    pub native_event_id: String,
    pub skill_name: String,
    pub signal_kind: String,
    pub source_line: i64,
    pub occurred_at: Option<String>,
    pub skill_locator: Option<String>,
    pub request_key: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ApprovedResourceCall {
    pub tool_name: String,
    pub tool_call_id: String,
    pub target_hints: Vec<(String, String)>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedSession {
    pub external_id: String,
    pub source_path: String,
    pub cwd_raw: Option<String>,
    pub git_branch: Option<String>,
    pub title: String,
    pub started_at: Option<String>,
    pub ended_at: Option<String>,
    pub last_event_at: Option<String>,
    pub events: Vec<ParsedEvent>,
    pub skipped_lines: i64,
    pub session_class: String,
    pub index_policy: String,
    pub maintenance_run_id: Option<String>,
    pub session_role: String,
    pub parent_external_id: Option<String>,
    pub usage_records: Vec<ParsedUsageRecord>,
    pub skill_observations: Vec<ParsedSkillObservation>,
    pub url_evidence: Vec<ParsedUrlEvidence>,
    pub reference_candidates: Vec<ParsedReferenceCandidate>,
}
impl ParsedSession {
    pub fn meaningful(&self) -> bool {
        !self.events.is_empty()
            || !self.usage_records.is_empty()
            || !self.skill_observations.is_empty()
    }
    pub(crate) fn empty(path: &std::path::Path, external_id: String) -> Self {
        Self {
            title: external_id.clone(),
            external_id,
            source_path: path.to_str().expect("validated source Unicode").into(),
            cwd_raw: None,
            git_branch: None,
            started_at: None,
            ended_at: None,
            last_event_at: None,
            events: vec![],
            skipped_lines: 0,
            session_class: "work".into(),
            index_policy: "full".into(),
            maintenance_run_id: None,
            session_role: "primary".into(),
            parent_external_id: None,
            usage_records: vec![],
            skill_observations: vec![],
            url_evidence: vec![],
            reference_candidates: vec![],
        }
    }
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ScanDelta {
    pub sessions: Vec<String>,
    pub documents: Vec<i64>,
    pub indexed_documents: Vec<(i64, String)>,
    pub deleted_sessions: Vec<String>,
    pub deleted_documents: Vec<i64>,
    pub sources_pruned: Vec<(i64, Vec<String>)>,
    pub warnings: Vec<Value>,
}
