//! Optional observer: only caller-owned ingestion transactions, no remote I/O.
use super::{common::id, evidence, structure_references};
use crate::backend::{
    db,
    ingest::{IngestionObserver, ParsedUrlEvidence, SessionObservation},
    Result,
};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::collections::BTreeSet;
#[derive(Debug, Default)]
pub struct AtlassianIngestion;
impl AtlassianIngestion {
    pub const fn new() -> Self {
        Self
    }
}
fn clear_source(db: &Connection, row: &Value) -> Result<()> {
    db.execute(
        "DELETE FROM atlassian_item_evidence WHERE session_id=? AND source_path=?",
        params![id(&row["session_id"])?, row["source_path"].as_str()],
    )?;
    db.execute(
        "DELETE FROM atlassian_evidence_scans WHERE id=?",
        [id(&row["id"])?],
    )?;
    Ok(())
}
impl IngestionObserver for AtlassianIngestion {
    fn document_is_current(&self, db: &Connection, document: i64, hash: &str) -> Result<bool> {
        evidence::evidence_scan_is_current(
            db,
            &evidence::document_evidence_source_fingerprint(hash)?,
            None,
            None,
            Some(document),
        )
    }
    fn document_indexed(
        &self,
        db: &Connection,
        document: i64,
        hash: &str,
        body: &str,
    ) -> Result<()> {
        evidence::reconcile_document_evidence(
            db,
            document,
            &evidence::document_evidence_source_fingerprint(hash)?,
            body,
        )?;
        Ok(())
    }
    fn session_is_current(&self, db: &Connection, source: &SessionObservation<'_>) -> Result<bool> {
        evidence::evidence_scan_is_current(
            db,
            &evidence::session_evidence_source_fingerprint(
                source.source_id,
                source.source_path,
                source.size_bytes,
                source.mtime_ns,
            )?,
            Some(source.session_id),
            Some(source.source_path),
            None,
        )
    }
    fn session_indexed(
        &self,
        db: &Connection,
        source: &SessionObservation<'_>,
        candidates: &[ParsedUrlEvidence],
    ) -> Result<()> {
        evidence::reconcile_session_evidence(
            db,
            source.session_id,
            source.source_path,
            &evidence::session_evidence_source_fingerprint(
                source.source_id,
                source.source_path,
                source.size_bytes,
                source.mtime_ns,
            )?,
            candidates,
        )?;
        Ok(())
    }
    fn before_owner_deleted(
        &self,
        db: &Connection,
        session: Option<i64>,
        document: Option<i64>,
    ) -> Result<Value> {
        let (column, key) = if session.is_some() {
            ("session_id", session)
        } else {
            ("document_id", document)
        };
        let rows=db::rows(db,&format!("SELECT DISTINCT reference_id FROM atlassian_structure_reference_evidence WHERE {column}=? ORDER BY reference_id"),[key])?;
        Ok(json!(rows
            .iter()
            .map(|r| id(&r["reference_id"]))
            .collect::<Result<Vec<_>>>()?))
    }
    fn after_owner_deleted(&self, db: &Connection, snapshot: Value) -> Result<()> {
        if let Some(rows) = snapshot.as_array() {
            for reference in rows {
                structure_references::project_structure_reference_search(db, id(reference)?)?;
            }
        }
        Ok(())
    }
    fn session_sources_pruned(
        &self,
        db: &Connection,
        source: i64,
        valid: &BTreeSet<String>,
    ) -> Result<()> {
        let rows=db::rows(db,"SELECT atlassian_evidence_scans.id,atlassian_evidence_scans.session_id,atlassian_evidence_scans.source_path FROM atlassian_evidence_scans JOIN sessions ON sessions.id=atlassian_evidence_scans.session_id WHERE sessions.source_id=?",[source])?;
        for row in rows {
            if !row["source_path"]
                .as_str()
                .is_some_and(|path| valid.contains(path))
            {
                clear_source(db, &row)?;
            }
        }
        Ok(())
    }
    fn empty_session_source(&self, db: &Connection, source: i64, path: &str) -> Result<()> {
        for row in db::rows(db,"SELECT atlassian_evidence_scans.id,atlassian_evidence_scans.session_id,atlassian_evidence_scans.source_path FROM atlassian_evidence_scans JOIN sessions ON sessions.id=atlassian_evidence_scans.session_id WHERE sessions.source_id=? AND atlassian_evidence_scans.source_path=?",params![source,path])?{clear_source(db,&row)?;}
        Ok(())
    }
    fn context_root_removed(&self, db: &Connection, root: i64) -> Result<()> {
        evidence::clear_context_root_evidence(db, root)
    }
}
