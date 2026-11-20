use crate::backend::{clock, references, BackendError, Result};
use chrono::{DateTime, Utc};
use localbrain_models::Cancellation;
use rusqlite::{
    hooks::{AuthAction, AuthContext, Authorization},
    Connection, OpenFlags,
};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{
    fs::{self, File, OpenOptions},
    io::{Read, Write},
    os::unix::fs::{MetadataExt, OpenOptionsExt},
    path::{Path, PathBuf},
    sync::atomic::Ordering,
    time::{Duration, Instant},
};
pub(super) fn failure(code: &str) -> BackendError {
    BackendError::invalid(code, code)
}
pub(super) fn require(value: bool, code: &str) -> Result<()> {
    if value {
        Ok(())
    } else {
        Err(failure(code))
    }
}
pub(super) fn check_cancel(cancel: &Cancellation) -> Result<()> {
    require(!cancel.load(Ordering::Acquire), "SIMULATION_INTERRUPTED")
}
pub(super) fn digest(value: &Value) -> String {
    references::hash_payload(value)
}
pub(super) fn sha(value: &str) -> String {
    format!("{:x}", Sha256::digest(value.as_bytes()))
}
pub(super) fn timestamp(value: &str) -> Result<clock::ParsedTimestamp> {
    require(value.chars().count() <= 80, "INVALID_TIME")?;
    let parsed = clock::parse_iso_datetime(&value.replace('Z', "+00:00"))
        .filter(|value| value.offset_micros.is_some() && value.utc().is_some())
        .ok_or_else(|| failure("INVALID_TIME"))?;
    Ok(parsed)
}
pub(super) fn utc(value: &str) -> Result<DateTime<Utc>> {
    Ok(timestamp(value)?.utc().unwrap())
}
pub(super) fn safe_file(path: &Path) -> Result<fs::Metadata> {
    let info = match fs::symlink_metadata(path) {
        Ok(info) => info,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            return Err(failure("UNOWNED_OUTPUT"))
        }
        Err(error) => return Err(error.into()),
    };
    require(
        info.is_file()
            && info.uid() == unsafe { libc::getuid() }
            && info.mode() & 0o077 == 0
            && info.nlink() == 1,
        "UNOWNED_OUTPUT",
    )?;
    Ok(info)
}
pub(super) fn read_json(path: &Path, limit: u64) -> Result<Value> {
    let before = safe_file(path)?;
    require(before.size() <= limit, "UNOWNED_OUTPUT")?;
    let mut file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)?;
    let after = file.metadata()?;
    require(
        (before.dev(), before.ino()) == (after.dev(), after.ino()),
        "UNOWNED_OUTPUT",
    )?;
    let mut bytes = Vec::new();
    Read::by_ref(&mut file)
        .take(limit + 1)
        .read_to_end(&mut bytes)?;
    require(bytes.len() as u64 <= limit, "UNOWNED_OUTPUT")?;
    serde_json::from_slice(&bytes).map_err(|_| failure("INVALID_INPUT"))
}
pub(super) fn atomic_json(path: &Path, value: &Value) -> Result<()> {
    stage_json(path, value)?.publish()
}

pub(super) struct PendingJson {
    path: PathBuf,
    destination: PathBuf,
    dev: u64,
    ino: u64,
}
impl PendingJson {
    pub(super) fn publish(self) -> Result<()> {
        fs::rename(&self.path, &self.destination)?;
        Ok(())
    }
}
impl Drop for PendingJson {
    fn drop(&mut self) {
        if fs::symlink_metadata(&self.path)
            .is_ok_and(|info| info.is_file() && info.dev() == self.dev && info.ino() == self.ino)
        {
            let _ = fs::remove_file(&self.path);
        }
    }
}
pub(super) fn stage_json(path: &Path, value: &Value) -> Result<PendingJson> {
    let pending = path.with_file_name(format!(
        "{}.pending",
        path.file_name().unwrap().to_string_lossy()
    ));
    require(pending.symlink_metadata().is_err(), "UNOWNED_OUTPUT")?;
    if path.symlink_metadata().is_ok() {
        safe_file(path)?;
    }
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(&pending)?;
    let info = file.metadata()?;
    let pending = PendingJson {
        path: pending,
        destination: path.to_owned(),
        dev: info.dev(),
        ino: info.ino(),
    };
    file.write_all(serde_json::to_string(value)?.as_bytes())?;
    file.flush()?;
    file.sync_all()?;
    Ok(pending)
}
pub(super) fn read_only_database(path: &Path, timeout: Duration) -> Result<Connection> {
    read_only_database_with_cancellation(path, timeout, None)
}
pub(super) fn read_only_database_with_cancellation(
    path: &Path,
    timeout: Duration,
    cancel: Option<&Cancellation>,
) -> Result<Connection> {
    require(
        path.is_absolute() && !path.is_symlink() && path.is_file(),
        "INVALID_DATABASE",
    )?;
    let connection = Connection::open_with_flags(
        fs::canonicalize(path)?,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )
    .map_err(|_| failure("DATABASE_UNAVAILABLE"))?;
    connection.busy_timeout(Duration::from_secs(1))?;
    connection.execute_batch("PRAGMA query_only=ON; PRAGMA temp_store=MEMORY")?;
    connection.authorizer(Some(|context: AuthContext<'_>| {
        if matches!(
            context.action,
            AuthAction::Select
                | AuthAction::Read { .. }
                | AuthAction::Function { .. }
                | AuthAction::Transaction { .. }
                | AuthAction::Recursive
        ) {
            Authorization::Allow
        } else {
            Authorization::Deny
        }
    }));
    let deadline = Instant::now() + timeout;
    let cancel = cancel.cloned();
    connection.progress_handler(
        1000,
        Some(move || {
            Instant::now() > deadline
                || cancel
                    .as_ref()
                    .is_some_and(|token| token.load(Ordering::Acquire))
        }),
    );
    connection.execute_batch("BEGIN")?;
    Ok(connection)
}
pub(super) fn lock(file: &File, operation: i32) -> Result<()> {
    if unsafe {
        libc::flock(
            std::os::fd::AsRawFd::as_raw_fd(file),
            operation | libc::LOCK_NB,
        )
    } != 0
    {
        return Err(failure("SIMULATION_BUSY"));
    }
    Ok(())
}
pub(super) fn signature(path: &Path) -> Option<(u64, u64, u64, i64, i64, i64, i64)> {
    fs::metadata(path).ok().map(|info| {
        (
            info.dev(),
            info.ino(),
            info.size(),
            info.mtime(),
            info.mtime_nsec(),
            info.ctime(),
            info.ctime_nsec(),
        )
    })
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn source_connection_enforces_authorizer_query_only_and_progress_deadline() {
        let root = tempfile::tempdir().unwrap();
        let path = root.path().join("source.db");
        let source = Connection::open(&path).unwrap();
        source
            .execute_batch(
                "CREATE TABLE evidence(value TEXT); INSERT INTO evidence VALUES ('keep')",
            )
            .unwrap();
        drop(source);
        let connection = read_only_database(&path, Duration::from_secs(1)).unwrap();
        assert_eq!(
            connection
                .query_row("SELECT value FROM evidence", [], |row| row
                    .get::<_, String>(0))
                .unwrap(),
            "keep"
        );
        for statement in [
            "UPDATE evidence SET value='changed'",
            "CREATE TABLE extra(value)",
            "CREATE TEMP TABLE extra(value)",
            "ATTACH DATABASE ':memory:' AS extra",
            "PRAGMA writable_schema=ON",
        ] {
            assert!(connection.execute_batch(statement).is_err(), "{statement}");
        }
        drop(connection);
        let limited = read_only_database(&path, Duration::ZERO).unwrap();
        assert!(limited.query_row("WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n WHERE x<1000000) SELECT SUM(x) FROM n",[],|row|row.get::<_,i64>(0)).is_err());
        assert_eq!(
            Connection::open(&path)
                .unwrap()
                .query_row("SELECT value FROM evidence", [], |row| row
                    .get::<_, String>(0))
                .unwrap(),
            "keep"
        );
    }
}
