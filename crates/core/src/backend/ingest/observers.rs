//! Explicit observers share the caller transaction and never commit or fetch.
use super::{ParsedSession, ParsedUrlEvidence};
use crate::backend::Result;
use rusqlite::Connection;
use serde_json::{json, Value};
use std::collections::BTreeSet;
#[derive(Debug, Clone)]
pub struct SessionObservation<'a> {
    pub source_id: i64,
    pub session_id: i64,
    pub source_path: &'a str,
    pub size_bytes: i64,
    pub mtime_ns: i64,
}
pub trait IngestionObserver: Send + Sync {
    fn session_scan(&self, _db: &Connection) -> Result<Option<Box<dyn IngestionObserver>>> {
        Ok(None)
    }
    fn document_is_current(&self, _db: &Connection, _id: i64, _hash: &str) -> Result<bool> {
        Ok(true)
    }
    fn document_indexed(&self, _db: &Connection, _id: i64, _hash: &str, _body: &str) -> Result<()> {
        Ok(())
    }
    fn session_is_current(
        &self,
        _db: &Connection,
        _source: &SessionObservation<'_>,
    ) -> Result<bool> {
        Ok(true)
    }
    fn session_indexed(
        &self,
        _db: &Connection,
        _source: &SessionObservation<'_>,
        _candidates: &[ParsedUrlEvidence],
    ) -> Result<()> {
        Ok(())
    }
    fn before_owner_deleted(
        &self,
        _db: &Connection,
        _session: Option<i64>,
        _document: Option<i64>,
    ) -> Result<Value> {
        Ok(json!(null))
    }
    fn after_owner_deleted(&self, _db: &Connection, _snapshot: Value) -> Result<()> {
        Ok(())
    }
    fn session_sources_pruned(
        &self,
        _db: &Connection,
        _source: i64,
        _valid: &BTreeSet<String>,
    ) -> Result<()> {
        Ok(())
    }
    fn empty_session_source(&self, _db: &Connection, _source: i64, _path: &str) -> Result<()> {
        Ok(())
    }
    fn context_root_removed(&self, _db: &Connection, _root: i64) -> Result<()> {
        Ok(())
    }
    // These core projections retain their existing source-local savepoint/currentness
    // owners. The host supplies their implementation explicitly at composition.
    fn reference_is_current(&self, _db: &Connection, _session: i64) -> Result<bool> {
        Ok(false)
    }
    fn reconcile_references(
        &self,
        _db: &Connection,
        _source: &SessionObservation<'_>,
        _parsed: &ParsedSession,
    ) -> Result<()> {
        Ok(())
    }
    fn finalize_references(&self, _db: &Connection, _session: i64) -> Result<()> {
        Ok(())
    }
    fn reference_error(&self, _db: &Connection, _session: i64, _error: &str) -> Result<()> {
        Ok(())
    }
    fn clear_reference_source(&self, _db: &Connection, _session: i64, _path: &str) -> Result<()> {
        Ok(())
    }
    fn store_skills(
        &self,
        _db: &Connection,
        _source: i64,
        _provider: &str,
        _parsed: &ParsedSession,
    ) -> Result<()> {
        Ok(())
    }
}
pub struct NoObservers;
impl IngestionObserver for NoObservers {}
