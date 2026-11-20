//! Outer transactions: each Session registration commits independently; Contexts
//! retain their grouped transaction. All mutations use the common operation lease.
use super::{sessions, storage, IngestionObserver, ScanControl};
use crate::backend::storage as operations;
use crate::backend::{
    contexts, db, now,
    sources::{
        registry::{self, Registration},
        settings,
    },
    BackendError, Config, Result,
};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::Path,
};
fn transaction<T>(config: &Config, action: impl FnOnce(&Connection) -> Result<T>) -> Result<T> {
    let db = db::connect(config)?;
    db.execute_batch("BEGIN IMMEDIATE")?;
    match action(&db) {
        Ok(value) => {
            db.execute_batch("COMMIT")?;
            Ok(value)
        }
        Err(error) => {
            let _ = db.execute_batch("ROLLBACK");
            Err(error)
        }
    }
}
fn success(status: &str) -> bool {
    ["completed", "empty"].contains(&status)
}
fn counts(db: &Connection, id: i64) -> Result<(i64, i64)> {
    Ok(db.query_row("SELECT(SELECT count(*) FROM sessions WHERE source_id=? AND session_class='work' AND session_role='primary'),(SELECT count(*) FROM source_files WHERE source_id=?)",params![id,id],|r|Ok((r.get(0)?,r.get(1)?)))?)
}
fn health(
    db: &Connection,
    id: i64,
    status: &str,
    attempt: &str,
    error: Option<&str>,
) -> Result<()> {
    if success(status) {
        db.execute("UPDATE sources SET last_scanned_at=?,last_scan_success_at=?,last_scan_status=?,last_scan_error=NULL WHERE id=?",params![attempt,attempt,status,id])?;
    } else {
        db.execute(
            "UPDATE sources SET last_scanned_at=?,last_scan_status=?,last_scan_error=? WHERE id=?",
            params![
                attempt,
                status,
                error.map(|s| s.chars().take(500).collect::<String>()),
                id
            ],
        )?;
    }
    Ok(())
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
fn report(
    registration: &Registration,
    status: &str,
    values: (i64, i64, i64),
    counts: (i64, i64),
    attempt: &str,
    last: Option<&str>,
    code: Option<&str>,
    error: Option<&str>,
) -> Value {
    json!({"source_id":registration.source_id,"display_label":registration.display_label,"provider_kind":registration.provider_kind,"root":registration.root,"status":status,"imported":values.0,"unchanged":values.1,"failed_files":values.2,"eligible_sessions":counts.0,"tracked_files":counts.1,"last_attempt_at":attempt,"last_success_at":last,"error_code":code,"error_message":error,"retained_data":!success(status)})
}
pub fn aggregate(sources: Vec<Value>) -> Value {
    let completed = sources
        .iter()
        .filter(|s| s["status"].as_str().is_some_and(success))
        .count();
    let outcome = if completed == sources.len() {
        "complete"
    } else if completed > 0 {
        "partial"
    } else {
        "failed"
    };
    json!({"outcome":outcome,"summary":{"source_count":sources.len(),"completed_sources":completed,"attention_sources":sources.len()-completed,"imported":sources.iter().filter_map(|r|r["imported"].as_i64()).sum::<i64>(),"unchanged":sources.iter().filter_map(|r|r["unchanged"].as_i64()).sum::<i64>(),"failed_files":sources.iter().filter_map(|r|r["failed_files"].as_i64()).sum::<i64>()},"sources":sources})
}
fn failure(
    config: &Config,
    r: &Registration,
    status: &str,
    attempt: &str,
    code: &str,
    message: &str,
    mark_unknown: bool,
) -> Result<Value> {
    transaction(config, |db| {
        let row = db::row(
            db,
            "SELECT last_scan_success_at FROM sources WHERE id=?",
            [r.source_id],
        )?;
        if mark_unknown {
            sessions::unknown(db, r.source_id, message)?;
        }
        let counts = counts(db, r.source_id)?;
        health(db, r.source_id, status, attempt, Some(message))?;
        Ok(report(
            r,
            status,
            (0, 0, 0),
            counts,
            attempt,
            row.as_ref()
                .and_then(|v| v["last_scan_success_at"].as_str()),
            Some(code),
            Some(message),
        ))
    })
}
fn registered(
    config: &Config,
    r: &Registration,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
) -> Result<Value> {
    let attempt = now();
    let Some((revision, _)) = sessions::provider_contract(&r.provider_kind) else {
        return failure(config,r,"configuration_error",&attempt,"provider","This source was not synchronized because its configuration needs attention; existing data was retained.",false);
    };
    if r.status == "unavailable" {
        return transaction(config, |db| {
            if storage::check_session_revision(db, r.source_id, revision).is_ok() {
                sessions::unknown(db,r.source_id,"This source root is unavailable; it was not synchronized and existing data was retained.")?;
            }
            let prior = db::row(
                db,
                "SELECT last_scan_success_at FROM sources WHERE id=?",
                [r.source_id],
            )?;
            let counts = counts(db, r.source_id)?;
            let message="This source root is unavailable; it was not synchronized and existing data was retained.";
            health(db, r.source_id, "unavailable", &attempt, Some(message))?;
            Ok(report(
                r,
                "unavailable",
                (0, 0, 0),
                counts,
                &attempt,
                prior
                    .as_ref()
                    .and_then(|v| v["last_scan_success_at"].as_str()),
                Some("root_unavailable"),
                Some(message),
            ))
        });
    }
    let result = transaction(config, |db| {
        let values = sessions::scan_source(
            db,
            config,
            r.source_id,
            &r.provider_kind,
            &r.display_label,
            Path::new(&r.root),
            force,
            control,
            observer,
        )?;
        let counts = counts(db, r.source_id)?;
        let present: i64 = db.query_row(
            "SELECT count(*) FROM source_files WHERE source_id=? AND presence_state='PRESENT'",
            [r.source_id],
            |row| row.get(0),
        )?;
        let status = if values.2 > 0 {
            "scan_failed"
        } else if present == 0 {
            "empty"
        } else {
            "completed"
        };
        let message = (values.2 > 0).then(|| {
            format!(
                "{} files could not be processed; existing data for those files was retained.",
                values.2
            )
        });
        let prior = db::row(
            db,
            "SELECT last_scan_success_at FROM sources WHERE id=?",
            [r.source_id],
        )?;
        health(db, r.source_id, status, &attempt, message.as_deref())?;
        control.check()?;
        Ok(report(
            r,
            status,
            values,
            counts,
            &attempt,
            if success(status) {
                Some(attempt.as_str())
            } else {
                prior
                    .as_ref()
                    .and_then(|v| v["last_scan_success_at"].as_str())
            },
            (values.2 > 0).then_some("file_scan_failed"),
            message.as_deref(),
        ))
    });
    match result {
        Ok(v) => Ok(v),
        Err(error) if error.code == "interrupted" => {
            transaction(config, |db| {
                if storage::check_session_revision(db, r.source_id, revision).is_ok() {
                    sessions::unknown(
                        db,
                        r.source_id,
                        "Original inspection was interrupted; stored history was retained.",
                    )?;
                }
                Ok(())
            })?;
            Err(error)
        }
        Err(error) => {
            let is_revision = error.code == "conflict" && error.message.contains("Session");
            let message = if is_revision {
                error.to_string()
            } else {
                format!(
                    "{} Session files could not be synchronized; existing data was retained.",
                    if r.provider_kind == "claude" {
                        "Claude"
                    } else {
                        "Codex"
                    }
                )
            };
            failure(
                config,
                r,
                "scan_failed",
                &attempt,
                if is_revision {
                    "session_revision_unsupported"
                } else {
                    "source_scan_failed"
                },
                &message,
                !is_revision,
            )
        }
    }
}
pub fn scan_session_sources(
    config: &Config,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
) -> Result<Value> {
    scan_selected_session_sources(config, force, control, observer, None)
}
fn scan_selected_session_sources(
    config: &Config,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
    selected_provider: Option<&str>,
) -> Result<Value> {
    let _lease = operations::operation_lock(config, "session-sync")?;
    control.check()?;
    db::initialize(config)?;
    settings::migrate_source_settings(config)?;
    let registry = transaction(config, |db| {
        registry::load_and_reconcile_session_sources(db, config)
    })?;
    let setup_connection = db::connect(config)?;
    let scan_observer = observer.session_scan(&setup_connection)?;
    drop(setup_connection);
    let observer = scan_observer.as_deref().unwrap_or(observer);
    let mut registrations = registry.registrations;
    let represented = registrations
        .iter()
        .map(|r| r.source_id)
        .collect::<BTreeSet<_>>();
    let diagnostics = registry
        .diagnostics
        .iter()
        .filter_map(|d| d.source_id.map(|id| (id, d)))
        .filter(|(id, _)| !represented.contains(id))
        .collect::<BTreeMap<_, _>>();
    let mut reports = vec![];
    if registry.settings.file_error {
        let connection = db::connect(config)?;
        registrations=db::rows(&connection,"SELECT id,provider_kind,name,root_path FROM sources WHERE provider_kind IN('claude','codex') ORDER BY id",[])?.into_iter().map(|row|Registration{source_id:row["id"].as_i64().unwrap(),provider_kind:row["provider_kind"].as_str().unwrap().into(),display_label:row["name"].as_str().unwrap().into(),root:row["root_path"].as_str().unwrap().into(),status:"configuration_error".into()}).collect();
        if registrations.is_empty() {
            let diagnostic = registry.diagnostics.first();
            reports.push(json!({"source_id":null,"display_label":"Session source settings","provider_kind":"unknown","root":registry.settings.settings_path,"status":"configuration_error","imported":0,"unchanged":0,"failed_files":0,"eligible_sessions":0,"tracked_files":0,"last_attempt_at":now(),"last_success_at":null,"error_code":diagnostic.map(|d|d.code.as_str()).unwrap_or("configuration_error"),"error_message":diagnostic.map(|d|format!("{} Session sources were not synchronized; existing data was retained.",d.message)),"retained_data":true}));
        }
    } else {
        let connection = db::connect(config)?;
        for id in diagnostics.keys() {
            if registrations.iter().any(|r| r.source_id == *id) {
                continue;
            }
            let row = db::row(&connection, "SELECT * FROM sources WHERE id=?", [id])?;
            registrations.push(Registration {
                source_id: *id,
                provider_kind: row
                    .as_ref()
                    .and_then(|r| r["provider_kind"].as_str())
                    .unwrap_or("unknown")
                    .into(),
                display_label: row
                    .as_ref()
                    .and_then(|r| r["name"].as_str())
                    .map(Into::into)
                    .unwrap_or_else(|| id.to_string()),
                root: row
                    .as_ref()
                    .and_then(|r| r["root_path"].as_str())
                    .unwrap_or("")
                    .into(),
                status: "configuration_error".into(),
            });
        }
        let order = &registry.settings.declared_source_ids;
        registrations.sort_by_key(|r| {
            order
                .iter()
                .position(|id| *id == r.source_id)
                .unwrap_or(order.len())
        });
    }
    let disabled = registry
        .settings
        .entries
        .iter()
        .filter(|e| !e.enabled)
        .map(|e| e.source_id)
        .collect::<BTreeSet<_>>();
    registrations.retain(|r| {
        !disabled.contains(&r.source_id)
            && selected_provider.is_none_or(|provider| r.provider_kind == provider)
    });
    control.emit(json!({"type":"sync_started","source_count":registrations.len()}));
    for (index, r) in registrations.iter().enumerate() {
        control.check()?;
        control.emit(json!({"type":"source_started","source_id":r.source_id,"display_label":r.display_label,"source_index":index+1,"source_count":registrations.len()}));
        let diagnostic = if registry.settings.file_error {
            registry.diagnostics.first()
        } else {
            diagnostics.get(&r.source_id).copied()
        };
        let result = if diagnostic.is_some()
            || !["ready", "unavailable"].contains(&r.status.as_str())
        {
            let message=diagnostic.map(|d|format!("{} This source was not synchronized; existing data was retained.",d.message)).unwrap_or_else(||"This source was not synchronized because its configuration needs attention; existing data was retained.".into());
            failure(
                config,
                r,
                "configuration_error",
                &now(),
                diagnostic.map(|d| d.code.as_str()).unwrap_or(&r.status),
                &message.chars().take(500).collect::<String>(),
                false,
            )?
        } else {
            registered(config, r, force, control, observer)?
        };
        control.emit(json!({"type":"source_result","source_id":result["source_id"],"display_label":result["display_label"],"status":result["status"],"imported":result["imported"],"unchanged":result["unchanged"],"failed_files":result["failed_files"]}));
        reports.push(result);
    }
    let report = aggregate(reports);
    control.emit(
        json!({"type":"sync_complete","outcome":report["outcome"],"summary":report["summary"]}),
    );
    Ok(report)
}
fn scan_provider_sessions(
    config: &Config,
    provider: &str,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
) -> Result<Value> {
    let report = scan_selected_session_sources(config, force, control, observer, Some(provider))?;
    let summary = &report["summary"];
    Ok(
        json!({"imported":summary["imported"],"skipped":summary["unchanged"],"failed":summary["failed_files"]}),
    )
}
pub fn scan_claude_sessions(
    config: &Config,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
) -> Result<Value> {
    scan_provider_sessions(config, "claude", force, control, observer)
}
pub fn scan_codex_sessions(
    config: &Config,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
) -> Result<Value> {
    scan_provider_sessions(config, "codex", force, control, observer)
}
pub fn scan_all(
    config: &Config,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
) -> Result<Value> {
    // Keep the reentrant operation lease across both existing coordinators so
    // another writer cannot interleave between Session and Context collection.
    let _lease = operations::operation_lock(config, "scan-all")?;
    let sessions = scan_session_sources(config, force, control, observer)?;
    let contexts = scan_context_sources(config, force, control, observer)?;
    let mut sources = sessions["sources"].as_array().cloned().unwrap_or_default();
    sources.extend(
        contexts["sources"]
            .as_array()
            .into_iter()
            .flatten()
            .cloned(),
    );
    Ok(aggregate(sources))
}
pub fn scan_context_sources(
    config: &Config,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
) -> Result<Value> {
    scan_context_sources_with_reader(
        config,
        force,
        control,
        observer,
        &contexts::scan::NativeContextReader,
    )
}
pub fn scan_context_sources_with_reader(
    config: &Config,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
    reader: &dyn contexts::scan::ContextReader,
) -> Result<Value> {
    let _lease = operations::operation_lock(config, "context-sync")?;
    control.check()?;
    db::initialize(config)?;
    let attempt = now();
    let registration = Registration {
        source_id: 0,
        provider_kind: "context".into(),
        display_label: "Local Contexts".into(),
        root: config.context_root.display().to_string(),
        status: "ready".into(),
    };
    let result = transaction(config, |db| {
        let values =
            contexts::scan::scan_documents(db, config, force, None, control, observer, reader)?;
        let source=db::row(db,"SELECT id,last_scan_success_at FROM sources WHERE provider_kind='context' ORDER BY id LIMIT 1",[])?.ok_or_else(||BackendError::new(500,"source","Context source is unavailable"))?;
        let mut r = registration.clone();
        r.source_id = source["id"].as_i64().unwrap();
        let counts = counts(db, r.source_id)?;
        let status = if values.2 > 0 {
            "scan_failed"
        } else if counts.1 == 0 {
            "empty"
        } else {
            "completed"
        };
        let message =
            (values.2 > 0).then(|| format!("{} Context files could not be processed.", values.2));
        health(db, r.source_id, status, &attempt, message.as_deref())?;
        control.check()?;
        Ok(report(
            &r,
            status,
            values,
            (0, counts.1),
            &attempt,
            if success(status) {
                Some(attempt.as_str())
            } else {
                source["last_scan_success_at"].as_str()
            },
            (values.2 > 0).then_some("file_scan_failed"),
            message.as_deref(),
        ))
    });
    let item = match result {
        Ok(v) => v,
        Err(error) if error.code == "interrupted" => return Err(error),
        Err(_) => {
            let mut r = registration;
            let connection = db::connect(config)?;
            if let Some(row) = db::row(
                &connection,
                "SELECT id FROM sources WHERE provider_kind='context' ORDER BY id LIMIT 1",
                [],
            )? {
                r.source_id = row["id"].as_i64().unwrap();
            }
            failure(
                config,
                &r,
                "scan_failed",
                &attempt,
                "source_scan_failed",
                "Local Context files could not be scanned; existing data was retained.",
                false,
            )?
        }
    };
    let report = aggregate(vec![item]);
    control.emit(json!({"type":"sync_complete","report":report}));
    Ok(report)
}
pub fn scan_context_root(
    connection: &Connection,
    config: &Config,
    root: i64,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
) -> Result<Value> {
    let (a, b, c) = contexts::scan::scan_documents(
        connection,
        config,
        force,
        Some(root),
        control,
        observer,
        &contexts::scan::NativeContextReader,
    )?;
    Ok(json!([a, b, c]))
}
pub fn sync_sessions(
    config: &Config,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
) -> Result<Value> {
    scan_session_sources(config, force, control, observer)
}
pub fn sync_contexts(
    config: &Config,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
) -> Result<Value> {
    scan_context_sources(config, force, control, observer)
}
