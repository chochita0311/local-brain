//! Provider-native capture and synchronization. Original files stay read-only.
pub(crate) mod common;
mod contracts;
mod control;
mod evidence;
mod observers;
mod providers;
pub mod scanner;
mod session_store;
pub mod sessions;
mod skills;
mod source_json;
pub(crate) mod storage;
pub mod sync_service;
pub use contracts::*;
pub use control::ScanControl;
pub use evidence::{visible_url_evidence, REFERENCE_VERSION, URL_EVIDENCE_VERSION};
pub use observers::{IngestionObserver, NoObservers, SessionObservation};
pub use providers::parse_session;
pub use scanner::{
    scan_all, scan_claude_sessions, scan_codex_sessions, scan_context_root, scan_context_sources,
    scan_context_sources_with_reader, scan_session_sources, sync_contexts, sync_sessions,
};
pub use storage::check_session_revision;
pub use sync_service::{
    ContextSyncService, SessionSyncService, SourcePredicate, SourceSyncService, SyncKind,
    SyncScanner,
};
