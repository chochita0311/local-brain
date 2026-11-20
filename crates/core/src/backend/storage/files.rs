use crate::backend::{BackendError, Config, Result};
use serde_json::Value;
use std::{
    fs::{self, File, OpenOptions},
    io::Write,
    os::{
        fd::AsRawFd,
        unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt, PermissionsExt},
    },
    path::{Component, Path, PathBuf},
    process::{Command, Stdio},
    time::{Duration, Instant},
};

pub fn failure(code: &str) -> BackendError {
    BackendError::conflict(code)
}

/// Resolve absent suffixes too, preserving the system's symlink semantics.
pub fn resolve(path: &Path) -> Result<PathBuf> {
    let absolute = if path.is_absolute() {
        path.to_owned()
    } else {
        std::env::current_dir()?.join(path)
    };
    if let Ok(resolved) = fs::canonicalize(&absolute) {
        return Ok(resolved);
    }
    let mut current = PathBuf::new();
    for component in absolute.components() {
        match component {
            Component::ParentDir => {
                current.pop();
            }
            Component::CurDir => {}
            part => {
                current.push(part.as_os_str());
                match fs::canonicalize(&current) {
                    Ok(canonical) => current = canonical,
                    Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
                    Err(error) => return Err(error.into()),
                }
            }
        }
    }
    Ok(current)
}

pub fn expand(path: &Path, config: &Config) -> PathBuf {
    let Some(text) = path.to_str().and_then(|text| text.strip_prefix('~')) else {
        return path.to_owned();
    };
    let (user, suffix) = text.split_once('/').unwrap_or((text, ""));
    let suffix = suffix.trim_start_matches('/');
    let root = if user.is_empty() {
        Some(config.home_dir.clone())
    } else {
        account_home(user)
    };
    root.map(|root| {
        if suffix.is_empty() {
            root
        } else {
            root.join(suffix)
        }
    })
    .unwrap_or_else(|| path.to_owned())
}
fn account_home(user: &str) -> Option<PathBuf> {
    use std::ffi::{CStr, CString};
    let user = CString::new(user).ok()?;
    let suggested = unsafe { libc::sysconf(libc::_SC_GETPW_R_SIZE_MAX) };
    let mut capacity = usize::try_from(suggested)
        .ok()
        .filter(|value| *value > 0)
        .unwrap_or(16 * 1024);
    loop {
        let mut buffer = vec![0_u8; capacity];
        let mut record = std::mem::MaybeUninit::<libc::passwd>::uninit();
        let mut found = std::ptr::null_mut();
        let status = unsafe {
            libc::getpwnam_r(
                user.as_ptr(),
                record.as_mut_ptr(),
                buffer.as_mut_ptr().cast(),
                buffer.len(),
                &mut found,
            )
        };
        if status == libc::ERANGE {
            capacity = capacity.checked_mul(2)?;
            continue;
        }
        if status != 0 || found.is_null() {
            return None;
        }
        let record = unsafe { record.assume_init() };
        if record.pw_dir.is_null() {
            return None;
        }
        return unsafe { CStr::from_ptr(record.pw_dir) }
            .to_str()
            .ok()
            .map(PathBuf::from);
    }
}

pub fn overlap(left: &Path, right: &Path) -> bool {
    left.starts_with(right) || right.starts_with(left)
}

/// POSIX normpath/abspath, including the significant exactly-two-slash root.
pub fn lexical_absolute(path: &Path) -> Result<PathBuf> {
    let absolute = if path.is_absolute() {
        path.to_owned()
    } else {
        std::env::current_dir()?.join(path)
    };
    let text = absolute
        .to_str()
        .ok_or_else(|| failure("Path is not valid UTF-8"))?;
    let prefix = if text.starts_with("//") && !text.starts_with("///") {
        "//"
    } else {
        "/"
    };
    let mut parts = Vec::new();
    for part in text.split('/') {
        match part {
            "" | "." => {}
            ".." => {
                parts.pop();
            }
            part => parts.push(part),
        }
    }
    Ok(PathBuf::from(format!("{prefix}{}", parts.join("/"))))
}

pub fn validate_runtime_directory(path: &Path, config: &Config) -> Result<PathBuf> {
    let path = expand(path, config);
    if fs::symlink_metadata(&path).is_ok_and(|info| info.file_type().is_symlink()) {
        return Err(failure("INVALID_RUNTIME_DIRECTORY"));
    }
    let path = resolve(&path)?;
    let public_cache = resolve(&config.hf_hub_cache)?;
    if overlap(&path, &public_cache) {
        return Err(failure("PRIVATE_STORAGE_OVERLAPS_PUBLIC_MODEL_CACHE"));
    }
    if let Some(root) = &config.installation_root {
        if path.starts_with(resolve(root)?) {
            return Err(failure("INVALID_RUNTIME_DIRECTORY"));
        }
    }
    // A packaged web root is inside the installation boundary; never write there.
    if config.web_root.is_absolute() && path.starts_with(resolve(&config.web_root)?) {
        return Err(failure("INVALID_RUNTIME_DIRECTORY"));
    }
    if path.ancestors().any(|parent| parent.join(".git").exists()) {
        return Err(failure("RUNTIME_DIRECTORY_IN_REPOSITORY"));
    }
    if let Ok(info) = fs::metadata(&path) {
        if !info.is_dir() || info.uid() != unsafe { libc::getuid() } {
            return Err(failure("UNOWNED_RUNTIME_DIRECTORY"));
        }
    }
    Ok(path)
}

pub fn private_directory(path: &Path, config: &Config) -> Result<PathBuf> {
    let path = validate_runtime_directory(path, config)?;
    let mut builder = fs::DirBuilder::new();
    builder.recursive(true).mode(0o700).create(&path)?;
    let info = fs::metadata(&path)?;
    if !info.is_dir() || info.uid() != unsafe { libc::getuid() } {
        return Err(failure("UNOWNED_RUNTIME_DIRECTORY"));
    }
    if info.mode() & 0o077 != 0 {
        fs::set_permissions(&path, fs::Permissions::from_mode(0o700))?;
    }
    Ok(path)
}

pub fn owned_file(path: &Path) -> Result<fs::Metadata> {
    let info = fs::symlink_metadata(path)?;
    if !info.is_file() || info.uid() != unsafe { libc::getuid() } || info.nlink() != 1 {
        return Err(failure("UNOWNED_STORAGE"));
    }
    Ok(info)
}

pub fn private_database(path: &Path, config: &Config) -> Result<()> {
    private_directory(path.parent().unwrap_or(Path::new(".")), config)?;
    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)?;
    let info = file.metadata()?;
    if !info.is_file() || info.uid() != unsafe { libc::getuid() } || info.nlink() != 1 {
        return Err(failure("UNOWNED_DATABASE"));
    }
    file.set_permissions(fs::Permissions::from_mode(0o600))?;
    Ok(())
}

pub fn atomic_write(path: &Path, content: &[u8]) -> Result<()> {
    let parent = path.parent().unwrap_or(Path::new("."));
    fs::DirBuilder::new()
        .recursive(true)
        .mode(0o700)
        .create(parent)?;
    if fs::symlink_metadata(path).is_ok_and(|info| info.file_type().is_symlink()) {
        return Err(BackendError::conflict(
            "설정 파일의 심볼릭 링크는 저장 대상으로 사용할 수 없습니다.",
        ));
    }
    let mut temporary = tempfile::Builder::new()
        .prefix(".localbrain-")
        .tempfile_in(parent)?;
    temporary
        .as_file()
        .set_permissions(fs::Permissions::from_mode(0o600))?;
    temporary.write_all(content)?;
    crate::files::sync_posix(temporary.as_file())?;
    temporary.persist(path).map_err(|error| error.error)?;
    File::open(parent).and_then(|file| crate::files::sync_posix(&file))?;
    Ok(())
}

pub fn read_owned_json(path: &Path, limit: u64) -> Result<Value> {
    if owned_file(path)?.len() > limit {
        return Err(failure("UNOWNED_STORAGE"));
    }
    let value: Value = serde_json::from_slice(&fs::read(path)?)?;
    if !value.is_object() {
        return Err(failure("UNOWNED_STORAGE"));
    }
    Ok(value)
}

#[derive(Clone)]
pub struct Stamp {
    pub path: PathBuf,
    pub info: fs::Metadata,
}

pub fn owned_tree(root: &Path) -> Result<Vec<Stamp>> {
    let mut result = Vec::new();
    for entry in walkdir::WalkDir::new(root).follow_links(false) {
        let entry = entry.map_err(|_| failure("UNOWNED_STORAGE"))?;
        let info = fs::symlink_metadata(entry.path())?;
        if info.uid() != unsafe { libc::getuid() }
            || (!info.is_dir() && !info.is_file())
            || (info.is_file() && info.nlink() != 1)
        {
            return Err(failure("UNOWNED_STORAGE"));
        }
        result.push(Stamp {
            path: entry.path().to_owned(),
            info,
        });
    }
    Ok(result)
}

pub fn ensure_unchanged(stamps: &[Stamp]) -> Result<()> {
    for stamp in stamps {
        let info = fs::symlink_metadata(&stamp.path)?;
        let old = &stamp.info;
        if (
            info.dev(),
            info.ino(),
            info.len(),
            info.mtime(),
            info.mtime_nsec(),
            info.mode(),
            info.nlink(),
        ) != (
            old.dev(),
            old.ino(),
            old.len(),
            old.mtime(),
            old.mtime_nsec(),
            old.mode(),
            old.nlink(),
        ) {
            return Err(failure("STORAGE_CHANGED"));
        }
    }
    Ok(())
}

pub fn inactive_files(paths: &[PathBuf]) -> bool {
    let Ok(mut child) = Command::new("/usr/sbin/lsof")
        .args(["-t", "--"])
        .args(paths)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    else {
        return false;
    };
    let start = Instant::now();
    loop {
        match child.try_wait() {
            Ok(Some(_)) => {
                return child.wait_with_output().is_ok_and(|result| {
                    result.status.code() == Some(1)
                        && result.stdout.is_empty()
                        && result.stderr.is_empty()
                })
            }
            Ok(None) if start.elapsed() < Duration::from_secs(10) => {
                std::thread::sleep(Duration::from_millis(20))
            }
            _ => {
                let _ = child.kill();
                let _ = child.wait();
                return false;
            }
        }
    }
}

pub fn tree_is_inactive(stamps: &[Stamp]) -> bool {
    let mut paths = Vec::new();
    let mut size = 0;
    for stamp in stamps {
        let length = stamp.path.as_os_str().len() + 1;
        if !paths.is_empty() && size + length > 48_000 {
            if !inactive_files(&paths) {
                return false;
            }
            paths.clear();
            size = 0;
        }
        paths.push(stamp.path.clone());
        size += length;
    }
    paths.is_empty() || inactive_files(&paths)
}

pub fn lock(file: &File, flags: i32) -> std::io::Result<()> {
    if unsafe { libc::flock(file.as_raw_fd(), flags) } == 0 {
        Ok(())
    } else {
        Err(std::io::Error::last_os_error())
    }
}
