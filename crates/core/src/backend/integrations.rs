//! Composition keeps required Session projections separate from optional packages.
use super::{
    ingest::{IngestionObserver, ParsedSession, ParsedUrlEvidence, SessionObservation},
    sessions::{references, skills},
    Config, Result,
};
use rusqlite::Connection;
use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    sync::{Arc, Mutex},
};

pub struct ApplicationIngestion {
    config: Config,
    optional: Vec<Arc<dyn IngestionObserver>>,
    lookup: Option<Mutex<Option<references::SessionReferenceLookup>>>,
}
impl ApplicationIngestion {
    pub fn new(config: Config, optional: Vec<Arc<dyn IngestionObserver>>) -> Self {
        Self {
            config,
            optional,
            lookup: None,
        }
    }
}
impl IngestionObserver for ApplicationIngestion {
    fn session_scan(&self, db: &Connection) -> Result<Option<Box<dyn IngestionObserver>>> {
        let optional = self
            .optional
            .iter()
            .map(|observer| {
                observer
                    .session_scan(db)
                    .map(|child| child.map(Arc::from).unwrap_or_else(|| observer.clone()))
            })
            .collect::<Result<Vec<Arc<dyn IngestionObserver>>>>()?;
        Ok(Some(Box::new(Self {
            config: self.config.clone(),
            optional,
            lookup: Some(Mutex::new(None)),
        })))
    }
    fn document_is_current(&self, db: &Connection, id: i64, hash: &str) -> Result<bool> {
        for observer in &self.optional {
            if !observer.document_is_current(db, id, hash)? {
                return Ok(false);
            }
        }
        Ok(true)
    }
    fn document_indexed(&self, db: &Connection, id: i64, hash: &str, body: &str) -> Result<()> {
        for observer in &self.optional {
            observer.document_indexed(db, id, hash, body)?;
        }
        Ok(())
    }
    fn session_is_current(&self, db: &Connection, source: &SessionObservation<'_>) -> Result<bool> {
        for observer in &self.optional {
            if !observer.session_is_current(db, source)? {
                return Ok(false);
            }
        }
        Ok(true)
    }
    fn session_indexed(
        &self,
        db: &Connection,
        source: &SessionObservation<'_>,
        candidates: &[ParsedUrlEvidence],
    ) -> Result<()> {
        for observer in &self.optional {
            observer.session_indexed(db, source, candidates)?;
        }
        Ok(())
    }
    fn before_owner_deleted(
        &self,
        db: &Connection,
        session: Option<i64>,
        document: Option<i64>,
    ) -> Result<Value> {
        Ok(json!(self
            .optional
            .iter()
            .map(|observer| observer.before_owner_deleted(db, session, document))
            .collect::<Result<Vec<_>>>()?))
    }
    fn after_owner_deleted(&self, db: &Connection, snapshot: Value) -> Result<()> {
        for (observer, snapshot) in self
            .optional
            .iter()
            .zip(snapshot.as_array().into_iter().flatten())
        {
            observer.after_owner_deleted(db, snapshot.clone())?;
        }
        Ok(())
    }
    fn session_sources_pruned(
        &self,
        db: &Connection,
        source: i64,
        valid: &BTreeSet<String>,
    ) -> Result<()> {
        for observer in &self.optional {
            observer.session_sources_pruned(db, source, valid)?;
        }
        Ok(())
    }
    fn empty_session_source(&self, db: &Connection, source: i64, path: &str) -> Result<()> {
        for observer in &self.optional {
            observer.empty_session_source(db, source, path)?;
        }
        Ok(())
    }
    fn context_root_removed(&self, db: &Connection, root: i64) -> Result<()> {
        for observer in &self.optional {
            observer.context_root_removed(db, root)?;
        }
        Ok(())
    }
    fn reference_is_current(&self, db: &Connection, session: i64) -> Result<bool> {
        references::session_reference_scan_is_current(db, session)
    }
    fn reconcile_references(
        &self,
        db: &Connection,
        source: &SessionObservation<'_>,
        parsed: &ParsedSession,
    ) -> Result<()> {
        let mut lookup = self
            .lookup
            .as_ref()
            .map(|cache| {
                cache.lock().map_err(|_| {
                    super::BackendError::unavailable("Session reference lookup interrupted")
                })
            })
            .transpose()?;
        if let Some(cache) = lookup.as_mut() {
            if cache.is_none() {
                **cache = Some(references::build_session_reference_lookup(db)?);
            }
        }
        let lookup = lookup.as_ref().and_then(|cache| cache.as_ref());
        references::reconcile_session_references(
            db,
            &self.config,
            source.session_id,
            source.source_path,
            source.size_bytes,
            source.mtime_ns,
            &parsed.reference_candidates,
            false,
            lookup,
        )?;
        Ok(())
    }
    fn finalize_references(&self, db: &Connection, session: i64) -> Result<()> {
        references::finalize_session_references(db, session, None)?;
        Ok(())
    }
    fn reference_error(&self, db: &Connection, session: i64, error: &str) -> Result<()> {
        references::mark_session_reference_error(db, session, error)
    }
    fn clear_reference_source(&self, db: &Connection, session: i64, path: &str) -> Result<()> {
        references::clear_session_reference_source(db, session, path)
    }
    fn store_skills(
        &self,
        db: &Connection,
        source: i64,
        provider: &str,
        parsed: &ParsedSession,
    ) -> Result<()> {
        skills::store_skill_observations(db, source, provider, parsed)?;
        Ok(())
    }
}
