//! Shared application services used directly by the native HTTP and CLI hosts.
pub mod atlassian;
pub mod auto_work;
pub mod clock;
pub mod config;
pub mod context_search;
pub mod contexts;
pub mod db;
pub mod error;
pub mod google_drive;
pub mod html;
pub mod ingest;
pub mod insights;
pub mod integrations;
pub mod json;
pub mod learning;
pub mod maintenance;
pub mod models;
pub mod preferences;
pub mod references;
pub mod rendering;
pub mod resources;
pub mod schema;
pub mod search;
pub mod sessions;
pub mod sources;
pub mod storage;
pub mod terminal;
pub mod terminal_workspaces;
pub mod unicode;
pub mod usage;
pub mod value_registry;
pub mod workflow;
pub mod workstreams;
pub mod yaml;

pub use config::Config;
pub use error::{BackendError, Result};

/// Python admitted deeply nested JSON on a much smaller interpreter stack.
/// Native serde Value cloning uses recursive Rust frames, so data-processing
/// workers reserve a larger virtual stack without adding a thread per request.
pub const WORKER_STACK_BYTES: usize = 32 * 1024 * 1024;
pub fn worker_thread(name: impl Into<String>) -> std::thread::Builder {
    std::thread::Builder::new()
        .name(name.into())
        .stack_size(WORKER_STACK_BYTES)
}

pub fn now() -> String {
    chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Micros, false)
}
