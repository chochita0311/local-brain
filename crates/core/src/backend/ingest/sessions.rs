use super::{
    common::path_text, evidence::REFERENCE_VERSION, providers::parse_with_control, session_store,
    storage, IngestionObserver, ScanControl, SessionObservation, CLAUDE_SESSION_REVISION,
    CLAUDE_USAGE_CONTRACT_VERSION, CODEX_SESSION_REVISION, CODEX_USAGE_CONTRACT_VERSION,
};
use crate::backend::{db, now, usage, BackendError, Config, Result};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet, HashMap, HashSet},
    fs,
    path::{Path, PathBuf},
};
pub fn provider_contract(provider: &str) -> Option<(i64, &'static str)> {
    match provider {
        "codex" => Some((CODEX_SESSION_REVISION, CODEX_USAGE_CONTRACT_VERSION)),
        "claude" => Some((CLAUDE_SESSION_REVISION, CLAUDE_USAGE_CONTRACT_VERSION)),
        _ => None,
    }
}
pub fn claude_candidate(root: &Path, path: &Path) -> bool {
    let Ok(relative) = path.strip_prefix(root) else {
        return false;
    };
    let parents = relative.parent().unwrap_or(Path::new(""));
    !parents.components().any(|c| c.as_os_str() == "subagents")
        || path
            .parent()
            .and_then(Path::file_name)
            .is_some_and(|s| s == "subagents")
}
pub fn session_paths(root: &Path, provider: &str, control: &ScanControl) -> Result<Vec<PathBuf>> {
    let mut paths = vec![];
    for entry in walkdir::WalkDir::new(root).follow_links(false) {
        control.check()?;
        let entry = entry.map_err(|e| BackendError::new(500, "source_walk", e.to_string()))?;
        if entry.depth() == 0 {
            continue;
        }
        let path = entry.path();
        let name = entry.file_name().to_str().ok_or_else(|| {
            BackendError::invalid("source_unicode", "Source path is not valid Unicode")
        })?;
        if name.ends_with(".jsonl") {
        } else if provider == "codex" && name.ends_with(".jsonl.zst") {
            match fs::metadata(path.with_extension("")) {
                Ok(info) if info.is_file() => continue,
                Err(error) if error.kind() != std::io::ErrorKind::NotFound => {
                    return Err(error.into())
                }
                _ => {}
            }
        } else {
            continue;
        }
        if fs::metadata(path)?.is_file() && (provider != "claude" || claude_candidate(root, path)) {
            paths.push(path.to_owned());
        }
    }
    paths.sort();
    Ok(paths)
}
pub(super) fn presence(
    db: &Connection,
    source: i64,
    path: &str,
    state: &str,
    error: Option<&str>,
) -> Result<()> {
    db.execute("UPDATE source_files SET presence_state=?,presence_checked_at=?,presence_error=? WHERE source_id=? AND path=?",params![state,now(),error.map(|s|s.chars().take(500).collect::<String>()),source,path])?;
    Ok(())
}
pub(super) fn unknown(db: &Connection, source: i64, error: &str) -> Result<()> {
    db.execute("UPDATE source_files SET presence_state='UNKNOWN',presence_checked_at=?,presence_error=? WHERE source_id=? AND session_id IS NOT NULL",params![now(),error.chars().take(500).collect::<String>(),source])?;
    Ok(())
}
fn replacements(
    db: &Connection,
    source: i64,
    selected: &BTreeSet<String>,
) -> Result<BTreeMap<String, Value>> {
    let mut out: BTreeMap<String, Value> = BTreeMap::new();
    for row in db::rows(db,"SELECT id AS session_id,external_id,source_path AS path FROM sessions WHERE source_id=? UNION SELECT files.session_id,sessions.external_id,files.path FROM source_files AS files JOIN sessions ON sessions.id=files.session_id WHERE files.source_id=?",params![source,source])?{let prior=row["path"].as_str().unwrap();if selected.contains(prior){continue;}let replacement=if let Some(s)=prior.strip_suffix(".jsonl.zst"){format!("{s}.jsonl")}else if prior.ends_with(".jsonl"){format!("{prior}.zst")}else{continue;};if selected.contains(&replacement){if out.get(&replacement).is_some_and(|v|v["session_id"]!=row["session_id"]){return Err(BackendError::conflict("Session container has conflicting prior owners"));}out.insert(replacement,row);}}
    Ok(out)
}
fn observe(
    db: &Connection,
    source: i64,
    root: &Path,
    provider: &str,
    selected: &BTreeSet<String>,
    replaced: &BTreeSet<String>,
    control: &ScanControl,
) -> Result<(BTreeSet<String>, BTreeSet<i64>)> {
    let accounting=db::rows(db,"SELECT id,source_path FROM sessions WHERE source_id=? AND session_class='maintenance' AND index_policy='metadata_only' AND external_id IN(SELECT 'localbrain-insight:'||id FROM personal_insight_runs)",[source])?;
    let mut retained = BTreeSet::new();
    let mut sessions = BTreeSet::new();
    for row in db::rows(db,"SELECT path,session_id FROM source_files WHERE source_id=? UNION SELECT source_path,id FROM sessions WHERE source_id=?",params![source,source])?{control.check()?;let path=row["path"].as_str().unwrap();let id=row["session_id"].as_i64();if accounting.iter().any(|r|r["id"].as_i64()==id||r["source_path"]==path){continue;}
if selected.contains(path){presence(db,source,path,"PRESENT",None)?;continue;}
if !(path.ends_with(".jsonl")||provider=="codex"&&path.ends_with(".jsonl.zst")){continue;}let original=Path::new(path);let outside=!original.starts_with(root);if !outside&&provider=="claude"&&!claude_candidate(root,original){continue;}let(state,error):(&str,Option<String>)=if outside{("UNKNOWN",Some("The original path is outside the current source root.".into()))}else{match fs::metadata(original){Ok(info)=>(if info.is_file(){"PRESENT"}else{"MISSING"},None),Err(e)if matches!(e.raw_os_error(),Some(libc::ENOENT|libc::ENOTDIR))=>("MISSING",None),Err(_)=>("UNKNOWN",Some("Original presence could not be checked: OSError".into()))}};
 if let Some(id)=id{db.execute("INSERT INTO source_files(source_id,session_id,path,size_bytes,mtime_ns,last_scanned_at,status) SELECT source_id,id,source_path,0,0,imported_at,'stale' FROM sessions WHERE id=? AND source_path=? ON CONFLICT(source_id,path) DO UPDATE SET session_id=COALESCE(source_files.session_id,excluded.session_id)",params![id,path])?;}
 presence(db,source,path,state,error.as_deref())?;if !replaced.contains(path){retained.insert(path.into());if let Some(id)=id{sessions.insert(id);}}}
    Ok((retained, sessions))
}

#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
pub fn scan_source(
    db: &Connection,
    config: &Config,
    source: i64,
    provider: &str,
    label: &str,
    root: &Path,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
) -> Result<(i64, i64, i64)> {
    let (revision, usage_version) = provider_contract(provider)
        .ok_or_else(|| BackendError::invalid("provider", "Unsupported Session provider"))?;
    storage::check_session_revision(db, source, revision)?;
    storage::upsert_source(db, Some(source), provider, label, root)?;
    storage::refresh_workspaces(db, config, source)?;
    if !root.exists() {
        unknown(db, source, "The source root is unavailable.")?;
        return Ok((0, 0, 0));
    }
    let paths = session_paths(root, provider, control)?;
    let selected = paths
        .iter()
        .map(|p| path_text(p))
        .collect::<Result<BTreeSet<_>>>()?;
    let replacements = if provider == "codex" {
        replacements(db, source, &selected)?
    } else {
        BTreeMap::new()
    };
    let mut prior = replacements
        .values()
        .map(|r| r["path"].as_str().unwrap().to_owned())
        .collect::<BTreeSet<_>>();
    let (missing, retained_ids) = observe(db, source, root, provider, &selected, &prior, control)?;
    let files = db::rows(db, "SELECT * FROM source_files WHERE source_id=?", [source])?;
    let current_files = files
        .iter()
        .filter(|r| selected.contains(r["path"].as_str().unwrap()))
        .collect::<Vec<_>>();
    let session_repair = current_files
        .iter()
        .any(|r| r["session_contract_version"].as_i64() != Some(revision));
    let usage_repair = current_files
        .iter()
        .any(|r| r["usage_contract_version"] != usage_version);
    let reference_repair = current_files
        .iter()
        .any(|r| r["reference_contract_version"] != REFERENCE_VERSION);
    let repair = session_repair || usage_repair || reference_repair;
    let eligibility = session_store::eligibility_repair(db, source)?;
    let kinds = [
        ("session", session_repair),
        ("usage", usage_repair),
        ("reference", reference_repair),
    ]
    .into_iter()
    .filter_map(|(kind, needed)| needed.then_some(kind))
    .collect::<Vec<_>>();
    control.emit(json!({"type":"source_plan","source_id":source,"display_label":label,"mode":if force{"forced"}else if repair{"contract_repair"}else{"incremental"},"repair_kinds":kinds,"total_files":paths.len()}));
    if repair {
        db.execute_batch("SAVEPOINT source_contract_repair")?;
    }
    let valid = selected
        .union(&prior)
        .cloned()
        .chain(missing.iter().cloned())
        .collect();
    session_store::prune(db, source, &valid, observer)?;
    let tracked = db::rows(db, "SELECT * FROM source_files WHERE source_id=?", [source])?
        .into_iter()
        .map(|r| (r["path"].as_str().unwrap().to_owned(), r))
        .collect::<HashMap<_, _>>();
    let mut forced = BTreeSet::new();
    if !repair {
        let mut dirty = BTreeSet::new();
        let mut unmapped = false;
        for path in &paths {
            let name = path_text(path)?;
            let row = tracked.get(&name);
            if row.and_then(|r| r["session_id"].as_i64()).is_none() {
                unmapped = true;
                continue;
            }
            let info = fs::metadata(path)?;
            if !storage::current(row, &info, None, None, Some(REFERENCE_VERSION))? {
                dirty.insert(row.unwrap()["session_id"].as_i64().unwrap());
            }
        }
        let partial=db::rows(db,"SELECT session_reference_scans.session_id FROM session_reference_scans JOIN sessions ON sessions.id=session_reference_scans.session_id WHERE sessions.source_id=? AND session_reference_scans.status='partial'",[source])?.into_iter().filter_map(|r|r["session_id"].as_i64()).filter(|id|unmapped||dirty.contains(id)).collect::<BTreeSet<_>>();
        forced.extend(
            tracked
                .iter()
                .filter(|(_, r)| {
                    r["session_id"]
                        .as_i64()
                        .is_some_and(|id| partial.contains(&id))
                })
                .map(|(path, _)| path.clone()),
        );
    }
    let (mut imported, mut skipped, mut failed) = (0, 0, 0);
    let mut expected = BTreeSet::new();
    let mut repair_errors = vec![];
    let mut empty = vec![];
    let mut finalize = BTreeSet::new();
    let mut reference_errors = BTreeMap::new();
    let interval = (paths.len().div_ceil(20)).max(1);
    for (index, path) in paths.iter().enumerate() {
        control.check()?;
        let name = path_text(path)?;
        let info = fs::metadata(path)?;
        let row = tracked.get(&name);
        let mapped = row.and_then(|r| r["session_id"].as_i64());
        let native = storage::current(row, &info, None, None, None)?;
        let size = i64::try_from(info.len()).map_err(|_| {
            BackendError::invalid("source_size", "Source size exceeds SQLite integer range")
        })?;
        let mtime = storage::mtime(&info)?;
        let mut current_id = mapped;
        let observation = |id| SessionObservation {
            source_id: source,
            session_id: id,
            source_path: &name,
            size_bytes: size,
            mtime_ns: mtime,
        };
        let reference_current = if let Some(id) = mapped {
            observer.reference_is_current(db, id)?
        } else {
            false
        };
        let extension_current = if let Some(id) = mapped {
            observer.session_is_current(db, &observation(id))?
        } else {
            false
        };
        if !force
            && !repair
            && !eligibility
            && !forced.contains(&name)
            && storage::current(
                row,
                &info,
                Some(revision),
                Some(usage_version),
                Some(REFERENCE_VERSION),
            )?
            && reference_current
            && extension_current
        {
            skipped += 1;
        } else {
            let refresh_session =
                force || eligibility || session_repair || !native || mapped.is_none();
            let refresh_usage = force || usage_repair || !native || mapped.is_none();
            let refresh_reference = force
                || session_repair
                || reference_repair
                || !native
                || mapped.is_none()
                || forced.contains(&name)
                || !reference_current;
            let refresh_extension = force
                || session_repair
                || reference_repair
                || !native
                || mapped.is_none()
                || !extension_current;
            let result = (|| -> Result<()> {
                let parsed = parse_with_control(provider, path, control)?.ok_or_else(|| {
                    BackendError::invalid("parser", "Native Session parser returned no result")
                })?;
                control.check()?;
                let replacement = replacements.get(&name);
                if replacement.is_some_and(|r| r["external_id"] != parsed.external_id) {
                    return Err(BackendError::conflict(
                        "Session container identity differs from its prior owner",
                    ));
                }
                if !parsed.meaningful() {
                    if let Some(replacement) = replacement {
                        db.execute(
                            "UPDATE sessions SET source_path=? WHERE id=?",
                            params![name, replacement["session_id"].as_i64()],
                        )?;
                        let old = replacement["path"].as_str().unwrap();
                        prior.remove(old);
                        empty.push((old.into(), parsed.clone()));
                    }
                    empty.push((name.clone(), parsed));
                    return Ok(());
                }
                let id = if refresh_session {
                    let owner = db::row(
                        db,
                        "SELECT id FROM sessions WHERE source_id=? AND external_id=?",
                        params![source, parsed.external_id],
                    )?
                    .and_then(|r| r["id"].as_i64());
                    session_store::store(
                        db,
                        config,
                        source,
                        provider,
                        &parsed,
                        usage_version,
                        refresh_usage,
                        owner.is_some_and(|id| retained_ids.contains(&id)),
                    )?
                } else {
                    let session = db::row(
                        db,
                        "SELECT id,workspace_id FROM sessions WHERE id=? AND source_id=?",
                        params![mapped, source],
                    )?
                    .ok_or_else(|| BackendError::conflict("Mapped Session is unavailable"))?;
                    let id = session["id"].as_i64().unwrap();
                    if refresh_usage {
                        usage::store_usage_records(
                            db,
                            source,
                            id,
                            &parsed.usage_records,
                            session["workspace_id"].as_i64(),
                            usage_version,
                        )?;
                    }
                    id
                };
                current_id = Some(id);
                observer.store_skills(db, source, provider, &parsed)?;
                if refresh_extension {
                    observer.session_indexed(db, &observation(id), &parsed.url_evidence)?;
                }
                if refresh_reference {
                    observer.reconcile_references(db, &observation(id), &parsed)?;
                }
                storage::record_file(
                    db,
                    source,
                    path,
                    "ok",
                    None,
                    Some(id),
                    (Some(revision), Some(usage_version), Some(REFERENCE_VERSION)),
                    Some((size, mtime)),
                )?;
                presence(db, source, &name, "PRESENT", None)?;
                if let Some(replacement) = replacement {
                    prior.remove(replacement["path"].as_str().unwrap());
                }
                if refresh_reference {
                    finalize.insert(id);
                }
                if usage_repair {
                    let native = parsed
                        .usage_records
                        .iter()
                        .map(|r| r.source_record_id.as_str())
                        .collect::<HashSet<_>>();
                    for record in db::rows(
                        db,
                        "SELECT id,source_record_id FROM usage_records WHERE session_id=?",
                        [id],
                    )? {
                        if record["source_record_id"]
                            .as_str()
                            .is_some_and(|s| native.contains(s))
                        {
                            expected.insert(record["id"].as_str().unwrap().to_owned());
                        }
                    }
                }
                imported += 1;
                Ok(())
            })();
            if let Err(error) = result {
                if error.code == "interrupted" {
                    return Err(error);
                }
                let id = current_id.or_else(|| {
                    replacements
                        .get(&name)
                        .and_then(|r| r["session_id"].as_i64())
                });
                if let Some(id) = id {
                    reference_errors.insert(id, error.to_string());
                }
                if repair {
                    repair_errors.push((path.clone(), error.to_string()));
                } else {
                    storage::record_file(
                        db,
                        source,
                        path,
                        "error",
                        Some(&error.to_string()),
                        None,
                        (None, None, None),
                        None,
                    )?;
                    presence(db, source, &name, "PRESENT", None)?;
                }
                failed += 1;
            }
        }
        if index + 1 == paths.len() || (index + 1) % interval == 0 {
            control.emit(json!({"type":"source_progress","source_id":source,"display_label":label,"processed_files":index+1,"total_files":paths.len(),"imported":imported,"unchanged":skipped,"failed_files":failed}));
        }
    }
    if !(replacements.is_empty() || repair && failed > 0) {
        let valid = selected
            .union(&prior)
            .cloned()
            .chain(missing.iter().cloned())
            .collect();
        session_store::prune(db, source, &valid, observer)?;
    }
    for id in finalize {
        if reference_errors.contains_key(&id) {
            continue;
        }
        if let Err(error) = observer.finalize_references(db, id) {
            reference_errors.insert(id, error.to_string());
            failed += 1;
            for row in db::rows(
                db,
                "SELECT path FROM source_files WHERE session_id=? ORDER BY path",
                [id],
            )? {
                if repair {
                    repair_errors.push((
                        PathBuf::from(row["path"].as_str().unwrap()),
                        error.to_string(),
                    ));
                } else {
                    db.execute(
                        "UPDATE source_files SET status='error',error=? WHERE session_id=?",
                        params![error.to_string(), id],
                    )?;
                }
            }
        }
    }
    if repair && failed > 0 {
        db.execute_batch("ROLLBACK TO source_contract_repair;RELEASE source_contract_repair")?;
        imported = 0;
        empty.clear();
        for (path, error) in repair_errors {
            storage::record_file(
                db,
                source,
                &path,
                "error",
                Some(&error),
                None,
                (None, None, None),
                None,
            )?;
            presence(db, source, &path_text(&path)?, "PRESENT", None)?;
        }
    } else if repair {
        let result = (|| -> Result<()> {
            if usage_repair {
                for row in db::rows(
                    db,
                    "SELECT id,session_id FROM usage_records WHERE source_id=?",
                    [source],
                )? {
                    if row["session_id"]
                        .as_i64()
                        .is_some_and(|id| retained_ids.contains(&id))
                    {
                        expected.insert(row["id"].as_str().unwrap().into());
                    }
                }
                usage::reconcile_usage_record_contract(
                    db,
                    source,
                    &expected.into_iter().collect::<Vec<_>>(),
                )?;
            }
            db.execute_batch("RELEASE source_contract_repair")?;
            Ok(())
        })();
        if let Err(error) = result {
            db.execute_batch("ROLLBACK TO source_contract_repair;RELEASE source_contract_repair")?;
            return Err(error);
        }
    }
    for (id, error) in reference_errors {
        if db.query_row(
            "SELECT EXISTS(SELECT 1 FROM sessions WHERE id=?)",
            [id],
            |r| r.get::<_, bool>(0),
        )? {
            observer.reference_error(db, id, &error)?;
        }
    }
    session_store::remove_empty(db, source, &empty, observer)?;
    session_store::parents(db, source, provider)?;
    db.execute("UPDATE skill_observations SET state='corrected' WHERE source_id=? AND state='observed' AND external_session_id IN(SELECT external_id FROM sessions WHERE source_id=? AND session_class='maintenance')",params![source,source])?;
    db.execute(
        "UPDATE sources SET last_scanned_at=? WHERE id=?",
        params![now(), source],
    )?;
    Ok((imported, skipped, failed))
}
