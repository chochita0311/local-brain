use super::{common::path_text, IngestionObserver};
use crate::backend::{db, now, BackendError, Config, Result};
use rusqlite::{params, Connection};
use serde_json::Value;
use std::{
    fs,
    os::unix::fs::MetadataExt,
    path::{Path, PathBuf},
};
pub(crate) fn mtime(info: &fs::Metadata) -> Result<i64> {
    info.mtime()
        .checked_mul(1_000_000_000)
        .and_then(|n| n.checked_add(info.mtime_nsec()))
        .ok_or_else(|| {
            BackendError::invalid("mtime", "Source timestamp exceeds SQLite integer range")
        })
}
pub(crate) fn upsert_source(
    db: &Connection,
    id: Option<i64>,
    provider: &str,
    name: &str,
    root: &Path,
) -> Result<i64> {
    let root = path_text(root)?;
    if let Some(id) = id {
        let kind: Option<String> =
            db::row(db, "SELECT provider_kind FROM sources WHERE id=?", [id])?
                .and_then(|v| v["provider_kind"].as_str().map(Into::into));
        if kind.as_deref() != Some(provider) {
            return Err(BackendError::invalid(
                "source",
                "Source ID is not registered with this provider",
            ));
        }
        db.execute(
            "UPDATE sources SET name=?,root_path=? WHERE id=?",
            params![name, root, id],
        )?;
        Ok(id)
    } else {
        db.execute(
            "INSERT INTO sources(provider_kind,name,root_path) VALUES(?,?,?)",
            params![provider, name, root],
        )?;
        Ok(db.last_insert_rowid())
    }
}
pub fn check_session_revision(db: &Connection, source: i64, revision: i64) -> Result<()> {
    if revision <= 0 {
        return Err(BackendError::conflict(
            "A positive numeric Session revision is required.",
        ));
    }
    for value in db::rows(db,"SELECT DISTINCT session_contract_version FROM source_files WHERE source_id=? AND session_contract_version IS NOT NULL",[source])?{let stored=value["session_contract_version"].as_i64().filter(|n|*n>0).ok_or_else(||BackendError::conflict("This source has an unsupported Session revision."))?;if stored>revision{return Err(BackendError::conflict(format!("This source was processed by a newer Session parser ({stored} > {revision}). Update LocalBrain before synchronizing it.")));}}
    Ok(())
}
pub(crate) fn current(
    row: Option<&Value>,
    info: &fs::Metadata,
    session: Option<i64>,
    usage: Option<&str>,
    reference: Option<&str>,
) -> Result<bool> {
    Ok(row.is_some_and(|r| {
        r["size_bytes"].as_u64() == Some(info.len())
            && r["mtime_ns"].as_i64() == mtime(info).ok()
            && r["status"] == "ok"
            && session.is_none_or(|v| r["session_contract_version"].as_i64() == Some(v))
            && usage.is_none_or(|v| r["usage_contract_version"] == v)
            && reference.is_none_or(|v| r["reference_contract_version"] == v)
    }))
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
pub(crate) fn record_file(
    db: &Connection,
    source: i64,
    path: &Path,
    status: &str,
    error: Option<&str>,
    session_id: Option<i64>,
    revisions: (Option<i64>, Option<&str>, Option<&str>),
    scanned: Option<(i64, i64)>,
) -> Result<()> {
    let info = fs::metadata(path)?;
    let (size, time) = scanned.unwrap_or((
        i64::try_from(info.len()).map_err(|_| {
            BackendError::invalid("source_size", "Source size exceeds SQLite integer range")
        })?,
        mtime(&info)?,
    ));
    db.execute("INSERT INTO source_files(source_id,session_id,path,size_bytes,mtime_ns,last_scanned_at,status,error,usage_contract_version,reference_contract_version,session_contract_version) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(source_id,path) DO UPDATE SET session_id=COALESCE(excluded.session_id,source_files.session_id),size_bytes=excluded.size_bytes,mtime_ns=excluded.mtime_ns,last_scanned_at=excluded.last_scanned_at,status=excluded.status,error=excluded.error,usage_contract_version=COALESCE(excluded.usage_contract_version,source_files.usage_contract_version),reference_contract_version=COALESCE(excluded.reference_contract_version,source_files.reference_contract_version),session_contract_version=COALESCE(excluded.session_contract_version,source_files.session_contract_version)",params![source,session_id,path_text(path)?,size,time,now(),status,error,revisions.1,revisions.2,revisions.0])?;
    Ok(())
}
pub(crate) fn replace_search(
    db: &Connection,
    kind: &str,
    id: &str,
    provider: &str,
    title: &str,
    body: &str,
    path: &str,
) -> Result<()> {
    db.execute(
        "DELETE FROM search_index WHERE entity_type=? AND entity_id=?",
        params![kind, id],
    )?;
    db.execute("INSERT INTO search_index(entity_type,entity_id,source_kind,title,body,path) VALUES(?,?,?,?,?,?)",params![kind,id,provider,title,body,path])?;
    Ok(())
}
pub(crate) fn delete_owner(
    db: &Connection,
    session: Option<i64>,
    document: Option<i64>,
    observer: &dyn IngestionObserver,
) -> Result<()> {
    if session.is_some() == document.is_some() {
        return Err(BackendError::invalid(
            "owner",
            "Exactly one source owner is required",
        ));
    }
    let snapshot = observer.before_owner_deleted(db, session, document)?;
    if let Some(id) = session {
        db.execute("DELETE FROM sessions WHERE id=?", [id])?;
    } else {
        db.execute(
            "DELETE FROM context_documents WHERE id=?",
            [document.unwrap()],
        )?;
    }
    observer.after_owner_deleted(db, snapshot)
}
fn exists(path: &Path) -> std::io::Result<bool> {
    match fs::metadata(path) {
        Ok(_) => Ok(true),
        Err(e) if matches!(e.raw_os_error(), Some(libc::ENOENT | libc::ENOTDIR)) => Ok(false),
        Err(e) => Err(e),
    }
}
fn git_root(path: &Path, home: &Path) -> std::io::Result<Option<PathBuf>> {
    if !exists(path)? {
        return Ok(None);
    }
    let current = if fs::metadata(path)?.is_dir() {
        path
    } else {
        path.parent().unwrap_or(path)
    };
    for parent in current.ancestors() {
        if exists(&parent.join(".git"))? {
            return fs::canonicalize(parent).map(Some);
        }
        if parent == home {
            break;
        }
    }
    Ok(None)
}
pub(crate) fn expand(path: &str, config: &Config) -> Result<PathBuf> {
    let expanded = crate::backend::storage::files::expand(Path::new(path), config);
    if path.starts_with('~')
        && !path.starts_with("~/")
        && path != "~"
        && expanded == Path::new(path)
    {
        return Err(BackendError::invalid(
            "context_path",
            "Could not determine home directory.",
        ));
    }
    let text = path_text(&expanded)?;
    let root = if text.starts_with("//") && !text.starts_with("///") {
        "//"
    } else if text.starts_with('/') {
        "/"
    } else {
        ""
    };
    let parts = text
        .split('/')
        .filter(|s| !s.is_empty() && *s != ".")
        .collect::<Vec<_>>()
        .join("/");
    let result = format!("{root}{parts}");
    Ok(PathBuf::from(if result.is_empty() { "." } else { &result }))
}
pub(crate) fn workspace(
    db: &Connection,
    config: &Config,
    cwd: Option<&str>,
    time: Option<&str>,
) -> Result<Option<i64>> {
    let Some(cwd) = cwd.filter(|s| !s.is_empty()) else {
        return Ok(None);
    };
    let path = expand(cwd, config)?;
    let present = path.exists();
    let canonical = if present {
        fs::canonicalize(&path)?
    } else {
        path.clone()
    };
    let git = git_root(&path, &config.home_dir).ok().flatten();
    let display = canonical
        .strip_prefix(&config.home_dir)
        .ok()
        .map(|p| {
            if p.as_os_str().is_empty() {
                "~".into()
            } else {
                format!("~/{}", p.display())
            }
        })
        .unwrap_or(path_text(&canonical)?);
    db.execute("INSERT INTO workspaces(canonical_path,display_name,git_root,exists_now,last_activity_at,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(canonical_path) DO UPDATE SET display_name=excluded.display_name,git_root=excluded.git_root,exists_now=excluded.exists_now,last_activity_at=CASE WHEN workspaces.last_activity_at IS NULL THEN excluded.last_activity_at WHEN excluded.last_activity_at>workspaces.last_activity_at THEN excluded.last_activity_at ELSE workspaces.last_activity_at END,updated_at=excluded.updated_at",params![path_text(&canonical)?,display,git.as_deref().map(path_text).transpose()?,present,time,now()])?;
    Ok(Some(db.query_row(
        "SELECT id FROM workspaces WHERE canonical_path=?",
        [path_text(&canonical)?],
        |r| r.get(0),
    )?))
}
pub(crate) fn refresh_workspaces(db: &Connection, config: &Config, source: i64) -> Result<()> {
    for row in db::rows(db,"SELECT id,canonical_path,exists_now,git_root FROM workspaces WHERE EXISTS(SELECT 1 FROM sessions WHERE sessions.workspace_id=workspaces.id AND sessions.source_id=?)",[source])?{let path=Path::new(row["canonical_path"].as_str().unwrap());let observed=(||->std::io::Result<_>{let present=exists(path)?;let git=if present{git_root(path,&config.home_dir)?}else{None};Ok((present,git))})();let Ok((present,git))=observed else{continue;};let git=git.as_deref().map(path_text).transpose()?;if row["exists_now"].as_i64()!=Some(i64::from(present))||row["git_root"].as_str()!=git.as_deref(){db.execute("UPDATE workspaces SET exists_now=?,git_root=?,updated_at=? WHERE id=?",params![present,git,now(),row["id"].as_i64()])?;}}
    Ok(())
}
