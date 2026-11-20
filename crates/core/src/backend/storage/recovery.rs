use super::{files, operation_lock};
use crate::backend::{db, BackendError, Config, Result};
use rusqlite::{Connection, OpenFlags};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, File, OpenOptions as FsOpenOptions},
    io::{Read, Write},
    os::{
        fd::{AsFd, BorrowedFd},
        unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt, PermissionsExt},
    },
    path::{Path, PathBuf},
};
use zip::{write::SimpleFileOptions, ZipArchive, ZipWriter};
pub const MAX_BACKUP_BYTES: u64 = 10 * 1024 * 1024 * 1024;
const FILES: [&str; 5] = [
    "localbrain.db",
    "settings.toml",
    "session-sources.toml",
    "natural-search.json",
    "terminal-workspaces.json",
];
const SLUGS: [&str; 3] = ["qwen3-embedding-0-6b", "qwen3-4b", "qwen3-8b"];
fn invalid() -> BackendError {
    BackendError::conflict("유효한 LocalBrain 백업이 아닙니다. 현재 데이터는 바꾸지 않았습니다.")
}
fn mkdir(path: &Path) -> Result<()> {
    fs::DirBuilder::new()
        .recursive(true)
        .mode(0o700)
        .create(path)?;
    Ok(())
}
fn private_copy(source: &Path, destination: &Path) -> Result<()> {
    let parent = destination.parent().ok_or_else(invalid)?;
    mkdir(parent)?;
    let mut temporary = tempfile::Builder::new()
        .prefix(".recovery-")
        .tempfile_in(parent)?;
    temporary
        .as_file()
        .set_permissions(fs::Permissions::from_mode(0o600))?;
    std::io::copy(&mut File::open(source)?, &mut temporary)?;
    temporary.as_file().sync_all()?;
    temporary
        .persist(destination)
        .map_err(|error| error.error)?;
    File::open(parent)?.sync_all()?;
    Ok(())
}
fn digest(path: &Path) -> Result<String> {
    let mut source = File::open(path)?;
    let mut digest = Sha256::new();
    let mut buffer = vec![0; 1024 * 1024];
    loop {
        let length = source.read(&mut buffer)?;
        if length == 0 {
            break;
        }
        digest.update(&buffer[..length]);
    }
    Ok(format!("{:x}", digest.finalize()))
}
fn schema_digest() -> String {
    format!("{:x}", Sha256::digest(db::SCHEMA.as_bytes()))
}
fn identity(config: &Config) -> Result<String> {
    let path = config.data_dir.join("installation-id");
    if !path.exists() {
        files::atomic_write(&path, uuid::Uuid::new_v4().to_string().as_bytes())?;
    }
    Ok(fs::read_to_string(path)?.trim().into())
}
fn allowed(name: &str) -> bool {
    if FILES.contains(&name) {
        return true;
    }
    let parts = name.split('/').collect::<Vec<_>>();
    match parts.as_slice() {
        ["models", slug, name] => {
            SLUGS.contains(slug) && ["owner.json", "model.json"].contains(name)
        }
        [slug, name] => SLUGS.contains(slug) && ["owner.json", "model.json"].contains(name),
        _ => false,
    }
}
fn names(config: &Config) -> Vec<String> {
    let mut result = FILES
        .iter()
        .filter(|name| config.data_dir.join(name).is_file())
        .map(|name| name.to_string())
        .collect::<Vec<_>>();
    for slug in SLUGS {
        for root in [format!("models/{slug}"), slug.into()] {
            for name in ["owner.json", "model.json"] {
                let name = format!("{root}/{name}");
                if config.data_dir.join(&name).is_file() {
                    result.push(name);
                }
            }
        }
    }
    result.sort();
    result
}
pub struct BackupArtifact {
    pub work: tempfile::TempDir,
    pub archive: PathBuf,
}
pub fn create_backup(config: &Config) -> Result<BackupArtifact> {
    let _lock = operation_lock(config, "backup")?;
    let identity = identity(config)?;
    let work = tempfile::Builder::new()
        .prefix("backup-")
        .tempdir_in(&config.data_dir)?;
    let mut hashes = BTreeMap::new();
    for name in names(config) {
        let source = config.data_dir.join(&name);
        let target = work.path().join(&name);
        let mut ancestor = source.parent();
        while let Some(parent) = ancestor {
            if parent == config.data_dir {
                break;
            }
            if fs::symlink_metadata(parent)?.file_type().is_symlink() {
                return Err(BackendError::conflict(
                    "앱이 소유하지 않은 파일이 있어 백업을 중단했습니다.",
                ));
            }
            ancestor = parent.parent();
        }
        let info = fs::symlink_metadata(&source)?;
        if info.file_type().is_symlink() || info.uid() != unsafe { libc::getuid() } {
            return Err(BackendError::conflict(
                "앱이 소유하지 않은 파일이 있어 백업을 중단했습니다.",
            ));
        }
        mkdir(target.parent().ok_or_else(invalid)?)?;
        if name == "localbrain.db" {
            let original = Connection::open(&source)?;
            let mut snapshot = Connection::open(&target)?;
            let backup = rusqlite::backup::Backup::new(&original, &mut snapshot)?;
            backup.run_to_completion(128, std::time::Duration::from_millis(10), None)?;
        } else {
            fs::copy(&source, &target)?;
        }
        fs::set_permissions(&target, fs::Permissions::from_mode(0o600))?;
        hashes.insert(name, digest(&target)?);
    }
    let manifest = json!({"owner":"localbrain.backup.v1","installation":identity,"created_at":crate::backend::now(),"app_schema":schema_digest(),"files":hashes});
    let archive = work.path().join("LocalBrain-backup.zip");
    let file = FsOpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&archive)?;
    let mut bundle = ZipWriter::new(file);
    let options = SimpleFileOptions::default()
        .compression_method(zip::CompressionMethod::Deflated)
        .unix_permissions(0o600);
    bundle
        .start_file("manifest.json", options)
        .map_err(|_| invalid())?;
    bundle.write_all(&serde_json::to_vec(&manifest)?)?;
    for name in hashes.keys() {
        bundle.start_file(name, options).map_err(|_| invalid())?;
        std::io::copy(&mut File::open(work.path().join(name))?, &mut bundle)?;
    }
    bundle.finish().map_err(|_| invalid())?.sync_all()?;
    Ok(BackupArtifact { work, archive })
}
pub fn validate_backup(
    archive: &Path,
    target: &Path,
    config: &Config,
) -> Result<BTreeMap<String, String>> {
    let attempt = (|| {
        let mut bundle = ZipArchive::new(File::open(archive)?).map_err(|_| invalid())?;
        if bundle.len() > 100 {
            return Err(invalid());
        }
        let mut names = BTreeSet::new();
        let mut size = 0_u64;
        for index in 0..bundle.len() {
            let item = bundle.by_index(index).map_err(|_| invalid())?;
            let name = item.name().to_string();
            if !names.insert(name.clone())
                || (name != "manifest.json" && !allowed(&name))
                || item.is_dir()
                || item
                    .unix_mode()
                    .is_some_and(|mode| mode & libc::S_IFMT as u32 == libc::S_IFLNK as u32)
            {
                return Err(invalid());
            }
            size = size.checked_add(item.size()).ok_or_else(invalid)?;
            if size > MAX_BACKUP_BYTES {
                return Err(invalid());
            }
            if name == "manifest.json" && item.size() > 65536 {
                return Err(invalid());
            }
        }
        let manifest: Value = {
            let mut item = bundle.by_name("manifest.json").map_err(|_| invalid())?;
            let mut bytes = Vec::new();
            item.read_to_end(&mut bytes)?;
            serde_json::from_slice(&bytes)?
        };
        if manifest["owner"] != "localbrain.backup.v1"
            || manifest["installation"] != identity(config)?
        {
            return Err(BackendError::conflict(
                "이 Mac의 현재 LocalBrain에서 만든 백업만 복원할 수 있습니다.",
            ));
        }
        if manifest["app_schema"] != schema_digest() {
            return Err(BackendError::conflict("현재 앱과 데이터베이스 스키마가 다른 백업입니다. 원래 버전에서 복원해 주세요. 현재 데이터는 보존했습니다."));
        }
        let hashes = manifest["files"]
            .as_object()
            .ok_or_else(invalid)?
            .iter()
            .map(|(name, value)| {
                value
                    .as_str()
                    .map(|value| (name.clone(), value.to_string()))
                    .ok_or_else(invalid)
            })
            .collect::<Result<BTreeMap<_, _>>>()?;
        names.remove("manifest.json");
        if hashes.keys().cloned().collect::<BTreeSet<_>>() != names
            || !hashes.contains_key("localbrain.db")
        {
            return Err(invalid());
        }
        mkdir(target)?;
        for (name, expected) in &hashes {
            let path = target.join(name);
            mkdir(path.parent().ok_or_else(invalid)?)?;
            let mut output = FsOpenOptions::new()
                .create(true)
                .truncate(true)
                .write(true)
                .mode(0o600)
                .custom_flags(libc::O_NOFOLLOW)
                .open(&path)?;
            let mut input = bundle.by_name(name).map_err(|_| invalid())?;
            std::io::copy(&mut input, &mut output)?;
            output.set_permissions(fs::Permissions::from_mode(0o600))?;
            if digest(&path)? != *expected {
                return Err(invalid());
            }
        }
        let database = Connection::open(target.join("localbrain.db"))?;
        let check: String = database.query_row("PRAGMA integrity_check", [], |row| row.get(0))?;
        if check != "ok" {
            return Err(invalid());
        }
        for table in ["sessions", "sources", "context_roots"] {
            if db::row(
                &database,
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                [table],
            )?
            .is_none()
            {
                return Err(invalid());
            }
        }
        if db::row(&database, "PRAGMA foreign_key_check", [])?.is_some() {
            return Err(invalid());
        }
        drop(database);
        for (name, versions) in [
            ("settings.toml", &[1][..]),
            ("session-sources.toml", &[1, 2]),
        ] {
            let path = target.join(name);
            if path.exists() {
                let version = crate::preferences::toml_schema_version(&fs::read_to_string(path)?)?;
                if !version.is_some_and(|version| versions.contains(&version)) {
                    return Err(invalid());
                }
            }
        }
        let workspaces = target.join("terminal-workspaces.json");
        if workspaces.exists() {
            if fs::metadata(&workspaces)?.len() > 2 * 1024 * 1024 {
                return Err(invalid());
            }
            let value: Value = serde_json::from_slice(&fs::read(workspaces)?)?;
            crate::backend::terminal_workspaces::validate_document(&value)
                .map_err(|_| invalid())?;
        }
        Ok(hashes)
    })();
    attempt.map_err(|error: BackendError| {
        if error.message.starts_with("이 Mac") || error.message.starts_with("현재 앱과") {
            error
        } else {
            invalid()
        }
    })
}
pub struct BackendStorageLease {
    file: File,
}
impl AsFd for BackendStorageLease {
    fn as_fd(&self) -> BorrowedFd<'_> {
        self.file.as_fd()
    }
}
pub fn backend_storage_lease(config: &Config) -> Result<BackendStorageLease> {
    files::private_directory(&config.data_dir, config)?;
    let file = FsOpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(config.data_dir.join("backend.lock"))?;
    let pending = config.data_dir.join("restore-pending.zip");
    if pending.exists() {
        files::lock(&file, libc::LOCK_EX | libc::LOCK_NB).map_err(|_| {
            BackendError::conflict(
                "복원을 위해 다른 LocalBrain 앱과 웹 서버를 종료한 후 다시 실행해 주세요.",
            )
        })?;
        apply_restore(&pending, config)?;
    }
    files::lock(&file, libc::LOCK_SH)?;
    Ok(BackendStorageLease { file })
}
fn apply_restore(archive: &Path, config: &Config) -> Result<()> {
    let _lock = operation_lock(config, "restore")?;
    let recovery = config.data_dir.join("recovery");
    mkdir(&recovery)?;
    let journal = recovery.join("active.json");
    if journal.exists() {
        let previous: Value = serde_json::from_slice(&fs::read(&journal)?)?;
        for name in previous["targets"].as_array().ok_or_else(invalid)? {
            let name = name
                .as_str()
                .filter(|name| allowed(name))
                .ok_or_else(invalid)?;
            let saved = recovery.join("before").join(name);
            let destination = config.data_dir.join(name);
            if saved.exists() {
                private_copy(&saved, &destination)?;
            } else if destination.exists() {
                fs::remove_file(destination)?;
            }
        }
        fs::remove_file(journal)?;
        return Err(BackendError::conflict(
            "중단된 복원 전의 상태로 되돌렸습니다. 앱을 다시 실행해 주세요.",
        ));
    }
    let staged = tempfile::Builder::new()
        .prefix("restore-")
        .tempdir_in(&config.data_dir)?;
    let incoming = validate_backup(archive, staged.path(), config)?;
    let before = recovery.join("before");
    if before.exists() {
        fs::rename(
            &before,
            recovery.join(format!(
                "before-{}",
                &uuid::Uuid::new_v4().simple().to_string()[..12]
            )),
        )?;
    }
    mkdir(&before)?;
    let targets = names(config)
        .into_iter()
        .chain(incoming.keys().cloned())
        .collect::<BTreeSet<_>>();
    let connection = Connection::open(&config.database_path)?;
    let busy: i64 =
        connection.query_row("PRAGMA wal_checkpoint(TRUNCATE)", [], |row| row.get(0))?;
    if busy != 0 {
        return Err(BackendError::conflict(
            "데이터베이스가 사용 중입니다. 다른 실행을 종료해 주세요.",
        ));
    }
    drop(connection);
    for name in &targets {
        let source = config.data_dir.join(name);
        if source.exists() {
            private_copy(&source, &before.join(name))?;
        }
    }
    files::atomic_write(&journal, &serde_json::to_vec(&json!({"targets":targets}))?)?;
    let published = (|| {
        for name in &targets {
            let destination = config.data_dir.join(name);
            if incoming.contains_key(name) {
                private_copy(&staged.path().join(name), &destination)?;
            } else if destination.exists() {
                fs::remove_file(destination)?;
            }
        }
        fs::remove_file(&journal)?;
        fs::remove_file(archive)?;
        Ok::<_, BackendError>(())
    })();
    published.map_err(|_| {
        BackendError::conflict("복원을 마치지 못했습니다. 다음 실행에서 복원 전 상태로 되돌립니다.")
    })
}
pub fn stage_restore(config: &Config, archive: &Path) -> Result<Value> {
    if fs::metadata(archive)?.len() > MAX_BACKUP_BYTES {
        return Err(BackendError::new(
            413,
            "backup_size",
            "백업 크기 한도 10GB를 넘었습니다.",
        ));
    }
    let temporary = tempfile::Builder::new()
        .prefix("restore-upload-")
        .tempdir_in(&config.data_dir)?;
    let validated = temporary.path().join("validated");
    validate_backup(archive, &validated, config)?;
    let _lock = operation_lock(config, "restore-stage")?;
    private_copy(archive, &config.data_dir.join("restore-pending.zip"))?;
    Ok(json!({"restart_required":true}))
}
pub fn export_backup(config: &Config, payload: &Value) -> Result<Value> {
    let raw = payload["path"]
        .as_str()
        .filter(|path| !path.is_empty() && path.chars().count() <= 4096)
        .ok_or_else(|| BackendError::conflict("백업을 저장할 파일을 선택해 주세요."))?;
    let target = files::expand(Path::new(raw), config);
    if !target.is_absolute()
        || !target
            .extension()
            .is_some_and(|extension| extension.eq_ignore_ascii_case("zip"))
        || fs::symlink_metadata(&target).is_ok_and(|info| info.file_type().is_symlink())
        || !target.parent().is_some_and(Path::is_dir)
    {
        return Err(BackendError::conflict(
            "저장할 ZIP 파일의 전체 경로를 확인해 주세요.",
        ));
    }
    let backup = create_backup(config)?;
    private_copy(&backup.archive, &target)?;
    Ok(json!({"saved":true}))
}
/// The service host stops its search worker before this call and restarts it on
/// every result, including a cleanup refusal. Included feature cleanup is added
/// by that host under the same reentrant operation lease.
pub fn clear_owned_cache(config: &Config) -> Result<Value> {
    let _lease = operation_lock(config, "cache-cleanup")?;
    let path = config.cache_dir.join("natural-search");
    if !path.exists() {
        return Ok(json!({"removed_bytes":0}));
    }
    let lock = FsOpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path.join("writer.lock"))?;
    let info = lock.metadata()?;
    if info.nlink() != 1 || info.uid() != unsafe { libc::getuid() } {
        return Err(BackendError::conflict("UNOWNED_SEARCH_LOCK"));
    }
    files::lock(&lock, libc::LOCK_EX | libc::LOCK_NB)
        .map_err(|_| BackendError::conflict("SEARCH_BUSY"))?;
    let stamps = files::owned_tree(&path)?;
    let known = [
        "writer.lock",
        "index.sqlite3",
        "index.sqlite3-wal",
        "index.sqlite3-shm",
        "status.json",
        "building.sqlite3",
        "building.sqlite3-wal",
        "building.sqlite3-shm",
    ];
    if stamps.iter().any(|stamp| {
        stamp.path != path
            && (!stamp
                .path
                .file_name()
                .is_some_and(|name| known.iter().any(|known| name == *known))
                || stamp.path.parent() != Some(&path))
    }) {
        return Err(BackendError::conflict(
            "알 수 없는 파일이 있어 검색 캐시를 보존했습니다.",
        ));
    }
    for name in ["index.sqlite3", "building.sqlite3"] {
        let index = path.join(name);
        if !index.exists() {
            continue;
        }
        let valid = (|| {
            let connection = Connection::open_with_flags(index, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
            let rows = db::rows(&connection, "SELECT key,value FROM meta", [])?;
            let metadata = rows
                .iter()
                .map(|row| {
                    Ok((
                        row["key"].as_str().unwrap_or("").to_string(),
                        serde_json::from_str::<Value>(row["value"].as_str().unwrap_or(""))?,
                    ))
                })
                .collect::<Result<BTreeMap<_, _>>>()?;
            let binding = format!(
                "{:x}",
                Sha256::digest(serde_json::to_vec(
                    &files::resolve(&config.database_path)?
                        .to_string_lossy()
                        .as_ref()
                )?)
            );
            Ok::<_, BackendError>(
                metadata.get("owner") == Some(&json!("localbrain.natural-search.v1"))
                    && metadata.get("binding") == Some(&json!(binding)),
            )
        })();
        if !matches!(valid, Ok(true)) {
            return Err(BackendError::conflict(
                "검색 캐시 소유 정보를 확인하지 못해 파일을 보존했습니다.",
            ));
        }
    }
    let files = stamps
        .into_iter()
        .filter(|stamp| {
            stamp.path != path
                && !stamp
                    .path
                    .file_name()
                    .is_some_and(|name| name == "owner.json" || name == "writer.lock")
        })
        .collect::<Vec<_>>();
    if !files::tree_is_inactive(&files) {
        return Err(BackendError::conflict(
            "검색 캐시가 사용 중입니다. 다른 실행을 종료해 주세요.",
        ));
    }
    let mut removed = 0;
    for stamp in files {
        if stamp.info.is_file() {
            removed += stamp.info.len();
            fs::remove_file(stamp.path)?;
        }
    }
    Ok(json!({"removed_bytes":removed}))
}
