use crate::{Error, Result};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::os::fd::AsRawFd;
use std::os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::{Path, PathBuf};

pub fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
pub fn file_digest(path: &Path) -> Result<String> {
    let mut file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)
        .map_err(|_| Error::identity())?;
    let mut hash = Sha256::new();
    let mut buffer = [0; 65536];
    loop {
        let count = file.read(&mut buffer).map_err(|_| Error::identity())?;
        if count == 0 {
            break;
        }
        hash.update(&buffer[..count]);
    }
    Ok(format!("{:x}", hash.finalize()))
}
pub fn uid() -> u32 {
    unsafe { libc::getuid() }
}
pub fn regular(info: &fs::Metadata, private: bool) -> bool {
    info.is_file()
        && info.uid() == uid()
        && info.nlink() == 1
        && (!private || info.mode() & 0o077 == 0)
}
pub fn location(path: &Path) -> Result<()> {
    if !path.is_absolute() || resolved(path)?.as_os_str() != path.as_os_str() {
        return Err(Error::identity());
    }
    for parent in path.ancestors() {
        if parent.join(".git").exists() {
            return Err(Error::identity());
        }
        if let Ok(info) = fs::symlink_metadata(parent) {
            if info.file_type().is_symlink() {
                return Err(Error::identity());
            }
        }
    }
    if let Ok(info) = fs::symlink_metadata(path) {
        if !info.is_dir() || info.uid() != uid() {
            return Err(Error::identity());
        }
    }
    Ok(())
}

/// Resolve an existing ancestor without creating the missing suffix.
pub fn resolved(path: &Path) -> Result<PathBuf> {
    let mut ancestor = path;
    let mut suffix = Vec::new();
    loop {
        match fs::canonicalize(ancestor) {
            Ok(mut base) => {
                for part in suffix.iter().rev() {
                    base.push(part);
                }
                return Ok(base);
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                suffix.push(ancestor.file_name().ok_or_else(Error::identity)?.to_owned());
                ancestor = ancestor.parent().ok_or_else(Error::identity)?;
            }
            Err(_) => return Err(Error::identity()),
        }
    }
}

pub fn private_location(path: &Path, home: &Path) -> Result<()> {
    location(path)?;
    let env = |key| {
        std::env::var_os(key)
            .filter(|value| !value.is_empty())
            .map(PathBuf::from)
    };
    let hub_home = env("HF_HOME").unwrap_or_else(|| {
        env("XDG_CACHE_HOME")
            .unwrap_or_else(|| home.join(".cache"))
            .join("huggingface")
    });
    let public = env("HF_HUB_CACHE")
        .or_else(|| env("HUGGINGFACE_HUB_CACHE"))
        .unwrap_or_else(|| hub_home.join("hub"));
    let public = if let Ok(rest) = public.strip_prefix("~") {
        home.join(rest)
    } else {
        public
    };
    let public = if public.is_absolute() {
        public
    } else {
        std::env::current_dir()
            .map_err(|_| Error::identity())?
            .join(public)
    };
    let public = resolved(&public)?;
    if path.starts_with(&public) || public.starts_with(path) {
        return Err(Error::identity());
    }
    Ok(())
}
pub fn private_dir(path: &Path) -> Result<()> {
    location(path)?;
    fs::DirBuilder::new()
        .recursive(true)
        .mode(0o700)
        .create(path)
        .map_err(|_| Error::identity())?;
    fs::set_permissions(path, fs::Permissions::from_mode(0o700)).map_err(|_| Error::identity())
}
pub fn read_json(path: &Path, limit: usize) -> Result<Option<Value>> {
    location(path.parent().ok_or_else(Error::identity)?)?;
    let file = match OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)
    {
        Ok(file) => file,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(_) => return Err(Error::identity()),
    };
    let info = file.metadata().map_err(|_| Error::identity())?;
    if !regular(&info, true) || info.len() > limit as u64 {
        return Err(Error::identity());
    }
    let mut bytes = Vec::new();
    file.take(limit as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| Error::identity())?;
    if bytes.len() > limit {
        return Err(Error::identity());
    }
    serde_json::from_slice(&bytes)
        .map(Some)
        .map_err(|_| Error::identity())
}
pub fn random_id() -> Result<String> {
    let mut bytes = [0u8; 16];
    File::open("/dev/urandom")
        .and_then(|mut f| f.read_exact(&mut bytes))
        .map_err(|_| Error::unavailable())?;
    Ok(bytes.iter().map(|b| format!("{b:02x}")).collect())
}
pub fn atomic_bytes(path: &Path, bytes: &[u8], mode: u32) -> Result<()> {
    location(path.parent().ok_or_else(Error::identity)?)?;
    if let Ok(info) = fs::symlink_metadata(path) {
        if !regular(&info, true) {
            return Err(Error::identity());
        }
    }
    let parent = path.parent().ok_or_else(Error::identity)?;
    let temporary = parent.join(format!(".publish-{}", random_id()?));
    let result = (|| {
        let mut file = OpenOptions::new()
            .create_new(true)
            .write(true)
            .mode(mode)
            .custom_flags(libc::O_NOFOLLOW)
            .open(&temporary)
            .map_err(|_| Error::identity())?;
        file.write_all(bytes)
            .and_then(|_| file.sync_all())
            .map_err(|_| Error::identity())?;
        fs::rename(&temporary, path).map_err(|_| Error::identity())?;
        File::open(parent)
            .and_then(|f| f.sync_all())
            .map_err(|_| Error::identity())
    })();
    if temporary.exists() {
        let _ = fs::remove_file(temporary);
    }
    result
}
pub fn atomic_json(path: &Path, value: &Value) -> Result<()> {
    let mut bytes = serde_json::to_vec(value).map_err(|_| Error::invalid())?;
    bytes.push(b'\n');
    atomic_bytes(path, &bytes, 0o600)
}
pub struct Lock {
    _file: File,
}
impl Lock {
    pub fn acquire(path: &Path, exclusive: bool, create: bool) -> Result<Self> {
        location(path.parent().ok_or_else(Error::identity)?)?;
        let mut options = OpenOptions::new();
        options
            .read(true)
            .write(true)
            .custom_flags(libc::O_NOFOLLOW)
            .mode(0o600);
        if create {
            options.create(true);
        }
        let file = options.open(path).map_err(|_| Error::identity())?;
        if !regular(&file.metadata().map_err(|_| Error::identity())?, true) {
            return Err(Error::identity());
        }
        let operation = (if exclusive {
            libc::LOCK_EX
        } else {
            libc::LOCK_SH
        }) | libc::LOCK_NB;
        if unsafe { libc::flock(file.as_raw_fd(), operation) } != 0 {
            return Err(Error::terminal("busy", "다른 서비스 작업이 진행 중입니다."));
        }
        Ok(Self { _file: file })
    }
}
pub fn owned_remove_file(path: &Path) -> Result<()> {
    match fs::symlink_metadata(path) {
        Ok(info) if regular(&info, true) => fs::remove_file(path).map_err(|_| Error::identity()),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(()),
        _ => Err(Error::identity()),
    }
}
pub fn absolute_executable(path: &Path) -> bool {
    use std::ffi::CString;
    path.is_absolute()
        && path.is_file()
        && CString::new(path.as_os_str().as_encoded_bytes())
            .is_ok_and(|s| unsafe { libc::access(s.as_ptr(), libc::X_OK) == 0 })
}
pub fn accessible_directory(path: &Path) -> bool {
    use std::ffi::CString;
    path.is_absolute()
        && path.is_dir()
        && CString::new(path.as_os_str().as_encoded_bytes())
            .is_ok_and(|s| unsafe { libc::access(s.as_ptr(), libc::X_OK) == 0 })
}
