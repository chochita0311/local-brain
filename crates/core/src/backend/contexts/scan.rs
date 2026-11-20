//! Context collection shares its caller's transaction and explicit adapters.
use crate::backend::ingest::{
    common::{path_text, python_string, truth, PythonText},
    storage, IngestionObserver, ScanControl,
};
use crate::backend::{clock, db, now, resources, BackendError, Config, Result};
use chrono::Timelike;

use rusqlite::{params, Connection};
use serde_json::Value;
use std::{
    collections::BTreeSet,
    fs,
    io::Read,
    path::{Path, PathBuf},
    process::{Command, Stdio},
    thread,
    time::{Duration, Instant},
};

pub trait ContextReader: Send + Sync {
    fn apple_notes(&self, control: &ScanControl) -> Result<Value>;
    fn spotlight_pdf(&self, path: &Path, control: &ScanControl) -> Result<Option<String>>;
}
pub struct NativeContextReader;
fn command(
    program: &str,
    args: &[&str],
    seconds: u64,
    control: &ScanControl,
) -> Result<(bool, String, String)> {
    let mut child = Command::new(program)
        .args(args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;
    let stdout = child.stdout.take().unwrap();
    let stderr = child.stderr.take().unwrap();
    let out = thread::spawn(move || {
        let mut bytes = vec![];
        let result = std::io::BufReader::new(stdout).read_to_end(&mut bytes);
        result.map(|_| bytes)
    });
    let err = thread::spawn(move || {
        let mut bytes = vec![];
        let result = std::io::BufReader::new(stderr).read_to_end(&mut bytes);
        result.map(|_| bytes)
    });
    let deadline = Instant::now() + Duration::from_secs(seconds);
    let status = loop {
        if let Err(error) = control.check() {
            let _ = child.kill();
            let _ = child.wait();
            let _ = out.join();
            let _ = err.join();
            return Err(error);
        }
        if Instant::now() >= deadline {
            let _ = child.kill();
            let _ = child.wait();
            let _ = out.join();
            let _ = err.join();
            return Err(BackendError::new(
                500,
                "source_timeout",
                if seconds == 120 {
                    "Apple Notes could not be read within 120 seconds"
                } else {
                    "Context reader timed out"
                },
            ));
        }
        match child.try_wait() {
            Ok(Some(status)) => break status,
            Ok(None) => thread::sleep(Duration::from_millis(50)),
            Err(error) => {
                let _ = child.kill();
                let _ = child.wait();
                let _ = out.join();
                let _ = err.join();
                return Err(error.into());
            }
        }
    };
    let out = out
        .join()
        .map_err(|_| BackendError::new(500, "source_reader", "Context output reader stopped"))??;
    let err = err
        .join()
        .map_err(|_| BackendError::new(500, "source_reader", "Context error reader stopped"))??;
    let decode = |bytes: Vec<u8>| {
        String::from_utf8(bytes).map_err(|_| {
            BackendError::invalid("source_unicode", "Context reader output is not valid UTF-8")
        })
    };
    Ok((status.success(), decode(out)?, decode(err)?))
}
impl ContextReader for NativeContextReader {
    fn apple_notes(&self, control: &ScanControl) -> Result<Value> {
        let (ok, stdout, stderr) = command(
            "/usr/bin/osascript",
            &["-l", "JavaScript", "-e", APPLE_NOTES_SCRIPT],
            120,
            control,
        )?;
        if !ok {
            return Err(BackendError::new(
                500,
                "apple_notes",
                if stderr.py_trim().is_empty() {
                    "Apple Notes could not be read".into()
                } else {
                    stderr.py_trim().to_owned()
                },
            ));
        }
        Ok(serde_json::from_str(if stdout.is_empty() {
            "[]"
        } else {
            &stdout
        })?)
    }
    fn spotlight_pdf(&self, path: &Path, control: &ScanControl) -> Result<Option<String>> {
        let (ok, out, _) = command(
            "/usr/bin/mdls",
            &["-raw", "-name", "kMDItemTextContent", &path_text(path)?],
            30,
            control,
        )?;
        let body = out.py_trim();
        Ok((ok && !body.is_empty() && body != "(null)").then(|| body.to_owned()))
    }
}
pub fn plain_text(value: &str) -> Result<String> {
    crate::backend::html::plaintext(value)
}
fn title(path: &Path, body: &str) -> String {
    for line in crate::backend::unicode::splitlines(body) {
        let s = line.py_trim();
        if let Some(s) = s.strip_prefix("# ") {
            return s.py_trim().into();
        }
    }
    path.file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("")
        .replace(['-', '_'], " ")
}
fn mtime_activity(info: &fs::Metadata) -> Result<String> {
    let n = storage::mtime(info)?;
    let timestamp =
        n.div_euclid(1_000_000_000) as f64 + n.rem_euclid(1_000_000_000) as f64 / 1_000_000_000.0;
    let seconds = timestamp.floor();
    let micros = ((timestamp - seconds) * 1_000_000.0).round_ties_even() as i64;
    let value = chrono::DateTime::from_timestamp(
        seconds as i64 + micros.div_euclid(1_000_000),
        (micros.rem_euclid(1_000_000) * 1000) as u32,
    )
    .ok_or_else(|| {
        BackendError::invalid(
            "mtime",
            "Context modification timestamp is outside calendar range",
        )
    })?;
    Ok(clock::isoformat(value))
}
fn remove_missing(
    connection: &Connection,
    root: i64,
    valid: &BTreeSet<String>,
    observer: &dyn IngestionObserver,
    source: Option<i64>,
) -> Result<()> {
    for row in db::rows(
        connection,
        "SELECT id,path FROM context_documents WHERE context_root_id=?",
        [root],
    )? {
        let path = row["path"].as_str().unwrap();
        if valid.contains(path) {
            continue;
        }
        let id = row["id"].as_i64().unwrap();
        connection.execute(
            "DELETE FROM search_index WHERE entity_type='document' AND entity_id=?",
            [id.to_string()],
        )?;
        storage::delete_owner(connection, None, Some(id), observer)?;
        if let Some(source) = source {
            connection.execute(
                "DELETE FROM source_files WHERE source_id=? AND path=?",
                params![source, path],
            )?;
        }
    }
    Ok(())
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
fn upsert(
    connection: &Connection,
    config: &Config,
    source: i64,
    root: i64,
    path: &str,
    relative: &str,
    title: &str,
    body: &str,
    size: i64,
    mtime: i64,
    content: Option<&str>,
    workspace: Option<i64>,
) -> Result<i64> {
    let hash = crate::files::digest(body.as_bytes());
    // Folder ingestion retains the existing default/content type on conflict;
    // individual file and Notes ingestion explicitly refreshes content_type.
    let (sql, with_type) = if content.is_some() {
        ("INSERT INTO context_documents(source_id,context_root_id,workspace_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash,imported_at,content_type) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET source_id=excluded.source_id,context_root_id=excluded.context_root_id,workspace_id=excluded.workspace_id,relative_path=excluded.relative_path,title=excluded.title,body=excluded.body,size_bytes=excluded.size_bytes,mtime_ns=excluded.mtime_ns,content_hash=excluded.content_hash,imported_at=excluded.imported_at,content_type=excluded.content_type",true)
    } else {
        ("INSERT INTO context_documents(source_id,context_root_id,workspace_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash,imported_at) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET source_id=excluded.source_id,context_root_id=excluded.context_root_id,workspace_id=excluded.workspace_id,relative_path=excluded.relative_path,title=excluded.title,body=excluded.body,size_bytes=excluded.size_bytes,mtime_ns=excluded.mtime_ns,content_hash=excluded.content_hash,imported_at=excluded.imported_at",false)
    };
    let mut values = vec![
        source.into(),
        root.into(),
        workspace.map_or(rusqlite::types::Value::Null, Into::into),
        path.to_owned().into(),
        relative.to_owned().into(),
        title.to_owned().into(),
        body.to_owned().into(),
        size.into(),
        mtime.into(),
        hash.into(),
        now().into(),
    ];
    if with_type {
        values.push(content.unwrap().to_owned().into());
    }
    connection.execute(sql, rusqlite::params_from_iter(values))?;
    let id: i64 = connection.query_row(
        "SELECT id FROM context_documents WHERE path=?",
        [path],
        |r| r.get(0),
    )?;
    storage::replace_search(
        connection,
        "document",
        &id.to_string(),
        "context",
        title,
        body,
        path,
    )?;
    resources::bind_document(connection, id, config)?;
    Ok(id)
}
fn current(
    connection: &Connection,
    source: i64,
    path: &Path,
    root: i64,
    observer: &dyn IngestionObserver,
) -> Result<bool> {
    let info = fs::metadata(path)?;
    let tracked = db::row(
        connection,
        "SELECT * FROM source_files WHERE source_id=? AND path=?",
        params![source, path_text(path)?],
    )?;
    if !storage::current(tracked.as_ref(), &info, None, None, None)? {
        return Ok(false);
    }
    let row = db::row(
        connection,
        "SELECT id,content_hash FROM context_documents WHERE context_root_id=? AND path=?",
        params![root, path_text(path)?],
    )?;
    match row {
        Some(r) => observer.document_is_current(
            connection,
            r["id"].as_i64().unwrap(),
            r["content_hash"].as_str().unwrap_or(""),
        ),
        None => Ok(false),
    }
}
fn state(
    connection: &Connection,
    root: i64,
    readable: bool,
    status: &str,
    error: Option<&str>,
) -> Result<()> {
    connection.execute("UPDATE context_roots SET readable=?,status=?,error=?,last_scanned_at=?,updated_at=? WHERE id=?",params![readable,status,error,now(),now(),root])?;
    Ok(())
}
const TEXT_EXT: &[&str] = &[
    "cfg",
    "conf",
    "csv",
    "html",
    "ini",
    "java",
    "js",
    "json",
    "kt",
    "log",
    "md",
    "properties",
    "py",
    "rst",
    "sh",
    "sql",
    "toml",
    "ts",
    "txt",
    "xml",
    "yaml",
    "yml",
];
fn read_file(
    path: &Path,
    reader: &dyn ContextReader,
    control: &ScanControl,
) -> Result<(Option<String>, Option<String>, Option<String>)> {
    let extension = path
        .extension()
        .and_then(|s| s.to_str())
        .unwrap_or("")
        .to_ascii_lowercase();
    let media = super::mime::guess(path.file_name().and_then(|s| s.to_str()).unwrap_or(""));
    if TEXT_EXT.contains(&extension.as_str())
        || media.as_deref().is_some_and(|m| m.starts_with("text/"))
    {
        let bytes = fs::read(path)?;
        let body = String::from_utf8_lossy(&bytes)
            .replace("\r\n", "\n")
            .replace('\r', "\n");
        return Ok((
            Some(body),
            Some(if extension == "md" {
                "text/markdown".into()
            } else {
                media.unwrap_or_else(|| "text/plain".into())
            }),
            None,
        ));
    }
    if extension == "pdf" {
        return match reader.spotlight_pdf(path, control)? {
            Some(body) => Ok((Some(body), Some("application/pdf+text".into()), None)),
            None => Ok((
                None,
                None,
                Some("PDF text is not available from the local Spotlight index".into()),
            )),
        };
    }
    Ok((
        None,
        None,
        Some("Unsupported or unreadable file type".into()),
    ))
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
fn single_file(
    connection: &Connection,
    config: &Config,
    source: i64,
    row: &Value,
    force: bool,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
    reader: &dyn ContextReader,
) -> Result<(i64, i64, i64)> {
    let root = row["id"].as_i64().unwrap();
    let path = Path::new(row["path"].as_str().unwrap());
    if !path.is_file() {
        return Err(BackendError::invalid(
            "context_path",
            format!("Context file does not exist: {}", path.display()),
        ));
    }
    if !force && current(connection, source, path, root, observer)? {
        return Ok((0, 1, 0));
    }
    let (body, content, error) = read_file(path, reader, control)?;
    let (Some(body), Some(content)) = (body, content) else {
        remove_missing(connection, root, &BTreeSet::new(), observer, None)?;
        state(connection, root, false, "unreadable", error.as_deref())?;
        return Ok((0, 0, 0));
    };
    let info = fs::metadata(path)?;
    let title = if path
        .extension()
        .and_then(|s| s.to_str())
        .is_some_and(|s| s.eq_ignore_ascii_case("md"))
    {
        title(path, &body)
    } else {
        path.file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("")
            .into()
    };
    let workspace = storage::workspace(
        connection,
        config,
        path.parent().and_then(Path::to_str),
        Some(&mtime_activity(&info)?),
    )?;
    let id = upsert(
        connection,
        config,
        source,
        root,
        &path_text(path)?,
        path.file_name().and_then(|s| s.to_str()).unwrap_or(""),
        &title,
        &body,
        info.len() as i64,
        storage::mtime(&info)?,
        Some(&content),
        workspace,
    )?;
    observer.document_indexed(
        connection,
        id,
        &crate::files::digest(body.as_bytes()),
        &body,
    )?;
    storage::record_file(
        connection,
        source,
        path,
        "ok",
        None,
        None,
        (None, None, None),
        None,
    )?;
    state(connection, root, true, "ready", None)?;
    Ok((1, 0, 0))
}
fn virtual_component(value: &str) -> String {
    let s = value
        .replace('/', "_")
        .split(crate::backend::unicode::python_space)
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join(" ");
    if s.is_empty() {
        "Untitled".into()
    } else {
        s
    }
}
fn encode_component(value: &str) -> String {
    let mut out = String::new();
    for b in value.bytes() {
        if b.is_ascii_alphanumeric() || b"_.-~".contains(&b) {
            out.push(b as char);
        } else {
            out.push_str(&format!("%{b:02X}"));
        }
    }
    out
}
/// Notes uses Python's OS-local naive timestamp rule, independently of the
/// presentation timezone. No request changes the process timezone/environment.
pub fn notes_timestamp_ns(value: &Value) -> Result<i64> {
    let modified = python_string(value).replace('Z', "+00:00");
    let Some(parsed) = clock::parse_iso_datetime(&modified) else {
        return Ok(0);
    };
    let seconds = if let Some(offset) = parsed.offset_micros {
        // Python divides two integers here. Decimal parsing preserves that
        // correctly rounded ratio even beyond the exact-f64 integer range.
        let micros = parsed.local.and_utc().timestamp_micros() - offset;
        let absolute = micros.unsigned_abs();
        format!(
            "{}{}.{:06}",
            if micros < 0 { "-" } else { "" },
            absolute / 1_000_000,
            absolute % 1_000_000
        )
        .parse::<f64>()
        .expect("bounded decimal timestamp")
    } else {
        let Some(whole) = naive_system_timestamp(parsed.local.and_utc().timestamp()) else {
            return Ok(0);
        };
        whole as f64 + parsed.local.nanosecond() as f64 / 1_000_000_000.0
    };
    let mtime = seconds * 1_000_000_000.0;
    if !mtime.is_finite()
        || !(-9_223_372_036_854_775_808.0..9_223_372_036_854_775_808.0).contains(&mtime)
    {
        return Err(BackendError::invalid(
            "mtime",
            "Notes timestamp exceeds SQLite integer range",
        ));
    }
    Ok(mtime as i64)
}
fn system_local_seconds(seconds: i64) -> Option<i64> {
    let value: libc::time_t = seconds;
    let mut out = std::mem::MaybeUninit::<libc::tm>::uninit();
    // localtime_r writes caller-owned storage and is the same reentrant OS
    // calendar conversion used by CPython. Read it only after a success result.
    if unsafe { libc::localtime_r(&value, out.as_mut_ptr()) }.is_null() {
        return None;
    }
    let out = unsafe { out.assume_init() };
    let year = out.tm_year.checked_add(1900)?;
    if !(1..=9999).contains(&year) {
        return None;
    }
    let day = chrono::NaiveDate::from_ymd_opt(
        year,
        u32::try_from(out.tm_mon + 1).ok()?,
        u32::try_from(out.tm_mday).ok()?,
    )?;
    Some(
        day.and_hms_opt(0, 0, 0)?.and_utc().timestamp()
            + i64::from(out.tm_hour) * 3600
            + i64::from(out.tm_min) * 60
            + i64::from(out.tm_sec),
    )
}
fn naive_system_timestamp(t: i64) -> Option<i64> {
    // CPython3.11's fold=0 local_to_seconds solver: preserve overlap/gap choice
    // and the ValueError->zero boundary when an OS conversion reaches year0 or
    // year10000. A timezone library's narrower instant range loses this stage.
    let a = system_local_seconds(t)? - t;
    let u1 = t - a;
    let t1 = system_local_seconds(u1)?;
    let b = if t1 == t {
        let u2 = u1 - 86_400;
        let b = system_local_seconds(u2)? - u2;
        if a == b {
            return Some(u1);
        }
        b
    } else {
        t1 - u1
    };
    let u2 = t - b;
    let t2 = system_local_seconds(u2)?;
    Some(if t2 == t {
        u2
    } else if t1 == t {
        u1
    } else {
        u1.max(u2)
    })
}
fn notes(
    connection: &Connection,
    config: &Config,
    source: i64,
    row: &Value,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
    reader: &dyn ContextReader,
) -> Result<(i64, i64, i64)> {
    let root = row["id"].as_i64().unwrap();
    let notes = reader.apple_notes(control)?;
    let array = notes.as_array().ok_or_else(|| {
        BackendError::invalid("apple_notes", "Apple Notes returned an invalid note list")
    })?;
    let mut valid = BTreeSet::new();
    let mut imported = 0;
    for note in array {
        control.check()?;
        let id = if truth(&note["id"]) {
            python_string(&note["id"])
        } else {
            String::new()
        };
        let id = id.py_trim();
        if id.is_empty() {
            continue;
        }
        let path = format!("apple-notes://note/{}", encode_component(id));
        valid.insert(path.clone());
        let title = if truth(&note["title"]) {
            python_string(&note["title"]).py_trim().to_owned()
        } else {
            "Untitled Note".into()
        };
        let account = if truth(&note["account"]) {
            python_string(&note["account"])
        } else {
            "Notes".into()
        };
        let mut components = vec![virtual_component(&account)];
        if let Some(folders) = note["folders"].as_array() {
            components.extend(folders.iter().map(|v| virtual_component(&python_string(v))));
        }
        components.push(format!(
            "{} [{}].note",
            virtual_component(&title),
            &crate::files::digest(id.as_bytes())[..8]
        ));
        let relative = components.join("/");
        let mtime = notes_timestamp_ns(&note["modified_at"])?;
        let body = crate::backend::html::plaintext(&if truth(&note["body"]) {
            python_string(&note["body"])
        } else {
            String::new()
        })?;
        let document = upsert(
            connection,
            config,
            source,
            root,
            &path,
            &relative,
            &title,
            &body,
            body.len() as i64,
            mtime,
            Some("application/x-apple-note"),
            None,
        )?;
        let hash = crate::files::digest(body.as_bytes());
        if !observer.document_is_current(connection, document, &hash)? {
            observer.document_indexed(connection, document, &hash, &body)?;
        }
        imported += 1;
    }
    remove_missing(connection, root, &valid, observer, None)?;
    state(connection, root, true, "ready", None)?;
    Ok((imported, 0, 0))
}
const IGNORE: &[&str] = &[
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
    "vendor",
];
pub fn context_paths(root: &Path, control: &ScanControl) -> Result<Vec<PathBuf>> {
    let mut dirs = vec![root.to_owned()];
    let mut paths = vec![];
    while let Some(dir) = dirs.pop() {
        control.check()?;
        let entries = match fs::read_dir(&dir) {
            Ok(entries) => entries.collect::<std::io::Result<Vec<_>>>()?,
            Err(error) if error.kind() == std::io::ErrorKind::PermissionDenied => continue,
            Err(error) => return Err(error.into()),
        };
        for entry in entries {
            control.check()?;
            let name = entry.file_name();
            let name = name.to_str().ok_or_else(|| {
                BackendError::invalid("context_unicode", "Context path is not valid Unicode")
            })?;
            if name.starts_with('.') || IGNORE.contains(&name) {
                continue;
            }
            let path = entry.path();
            if name.ends_with(".md") {
                paths.push(path.clone());
            }
            match entry.file_type() {
                Ok(kind) if kind.is_dir() => dirs.push(path),
                Err(e)
                    if !matches!(
                        e.raw_os_error(),
                        Some(
                            libc::ENOENT | libc::ENOTDIR | libc::EBADF | libc::ELOOP | libc::EACCES
                        )
                    ) =>
                {
                    return Err(e.into())
                }
                _ => {}
            }
        }
    }
    paths.sort();
    Ok(paths)
}
pub fn scan_documents(
    connection: &Connection,
    config: &Config,
    force: bool,
    root: Option<i64>,
    control: &ScanControl,
    observer: &dyn IngestionObserver,
    reader: &dyn ContextReader,
) -> Result<(i64, i64, i64)> {
    let source = db::row(
        connection,
        "SELECT id FROM sources WHERE provider_kind='context' ORDER BY id LIMIT 1",
        [],
    )?
    .and_then(|r| r["id"].as_i64());
    let source = storage::upsert_source(
        connection,
        source,
        "context",
        "Local Contexts",
        &config.context_root,
    )?;
    let roots = if let Some(root) = root {
        db::rows(
            connection,
            "SELECT * FROM context_roots WHERE enabled=1 AND id=? ORDER BY path",
            [root],
        )?
    } else {
        db::rows(
            connection,
            "SELECT * FROM context_roots WHERE enabled=1 ORDER BY path",
            [],
        )?
    };
    if root.is_some() && roots.is_empty() {
        return Err(BackendError::not_found("Local Context root not found"));
    }
    let (mut imported, mut skipped, mut failed) = (0, 0, 0);
    for row in roots {
        control.check()?;
        let root = row["id"].as_i64().unwrap();
        if matches!(row["source_type"].as_str(), Some("file" | "apple_notes")) {
            let result = if row["source_type"] == "file" {
                single_file(
                    connection, config, source, &row, force, control, observer, reader,
                )
            } else {
                notes(connection, config, source, &row, control, observer, reader)
            };
            match result {
                Ok((a, b, c)) => {
                    imported += a;
                    skipped += b;
                    failed += c;
                }
                Err(e) if e.code == "interrupted" => return Err(e),
                Err(e) => {
                    failed += 1;
                    let message = e
                        .to_string()
                        .chars()
                        .rev()
                        .take(2000)
                        .collect::<String>()
                        .chars()
                        .rev()
                        .collect::<String>();
                    state(connection, root, false, "error", Some(&message))?;
                }
            }
            continue;
        }
        let path = Path::new(row["path"].as_str().unwrap());
        if !path.is_dir() {
            failed += 1;
            state(
                connection,
                root,
                false,
                "missing",
                Some("Folder does not exist"),
            )?;
            continue;
        }
        let paths = context_paths(path, control)?;
        let valid = paths
            .iter()
            .map(|p| path_text(p))
            .collect::<Result<BTreeSet<_>>>()?;
        remove_missing(connection, root, &valid, observer, Some(source))?;
        for file in paths {
            control.check()?;
            if !force && current(connection, source, &file, root, observer)? {
                skipped += 1;
                continue;
            }
            let result = (|| -> Result<()> {
                let body = String::from_utf8_lossy(&fs::read(&file)?)
                    .replace("\r\n", "\n")
                    .replace('\r', "\n");
                let info = fs::metadata(&file)?;
                let relative = path_text(file.strip_prefix(path).map_err(|_| {
                    BackendError::invalid("context_path", "Context path escaped its root")
                })?)?;
                let title = title(&file, &body);
                let workspace = storage::workspace(
                    connection,
                    config,
                    file.parent().and_then(Path::to_str),
                    Some(&mtime_activity(&info)?),
                )?;
                let id = upsert(
                    connection,
                    config,
                    source,
                    root,
                    &path_text(&file)?,
                    &relative,
                    &title,
                    &body,
                    info.len() as i64,
                    storage::mtime(&info)?,
                    None,
                    workspace,
                )?;
                observer.document_indexed(
                    connection,
                    id,
                    &crate::files::digest(body.as_bytes()),
                    &body,
                )?;
                storage::record_file(
                    connection,
                    source,
                    &file,
                    "ok",
                    None,
                    None,
                    (None, None, None),
                    None,
                )?;
                Ok(())
            })();
            match result {
                Ok(()) => imported += 1,
                Err(error) => {
                    storage::record_file(
                        connection,
                        source,
                        &file,
                        "error",
                        Some(&error.to_string()),
                        None,
                        (None, None, None),
                        None,
                    )?;
                    failed += 1;
                }
            }
        }
        state(connection, root, true, "ready", None)?;
    }
    connection.execute(
        "UPDATE sources SET last_scanned_at=? WHERE id=?",
        params![now(), source],
    )?;
    Ok((imported, skipped, failed))
}

const APPLE_NOTES_SCRIPT: &str = r####"
const Notes = Application('Notes');
const results = [];

function text(value) {
  return value === undefined || value === null ? '' : String(value);
}

function visitFolder(accountName, folder, parentNames) {
  const folderName = text(folder.name()) || 'Notes';
  const folderNames = parentNames.concat([folderName]);
  const notes = folder.notes();
  notes.forEach((note) => {
    let body = '';
    try { body = text(note.plaintext()); }
    catch (_error) {
      try { body = text(note.body()); } catch (_ignored) { body = ''; }
    }
    let modifiedAt = null;
    try { modifiedAt = new Date(note.modificationDate()).toISOString(); }
    catch (_error) { modifiedAt = null; }
    results.push({
      id: text(note.id()),
      account: accountName,
      folders: folderNames,
      title: text(note.name()) || 'Untitled Note',
      body: body,
      modified_at: modifiedAt,
    });
  });
  try {
    folder.folders().forEach((child) => visitFolder(accountName, child, folderNames));
  } catch (_error) {}
}

Notes.accounts().forEach((account) => {
  const accountName = text(account.name()) || 'Notes';
  account.folders().forEach((folder) => visitFolder(accountName, folder, []));
});
JSON.stringify(results);
"####;
