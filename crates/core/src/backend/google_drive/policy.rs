//! Value, calendar and filesystem boundaries shared by both sync directions.
use super::{error, require, text};
use crate::backend::{unicode, Result};
use chrono::{DateTime, Timelike, Utc};
use serde_json::{json, Map, Value};
use std::os::unix::fs::{MetadataExt, PermissionsExt};
use std::{
    collections::BTreeSet,
    fs,
    path::{Path, PathBuf},
};
use unicode_normalization::UnicodeNormalization;
pub const MAX_FILE_BYTES: u64 = 100_000_000;
pub const PUBLISH_WORKERS: usize = 8;
pub const INTERVALS: [i64; 7] = [15, 30, 60, 180, 360, 720, 1440];
pub const FOLDER: &str = "application/vnd.google-apps.folder";
pub const SCOPE: &str = "https://www.googleapis.com/auth/drive";
pub fn root_url(value: &str) -> Result<(String, String)> {
    let invalid = || {
        error(
            "invalid_url",
            "전체 Google Drive 폴더 URL을 입력해 주세요.",
            false,
        )
    };
    let cleaned = value
        .trim_start_matches(|c: char| c <= '\u{20}')
        .replace(['\t', '\r', '\n'], "");
    let (scheme, rest) = cleaned.split_once("://").ok_or_else(invalid)?;
    let end = rest.find(['/', '?', '#']).unwrap_or(rest.len());
    if !scheme.eq_ignore_ascii_case("https") || &rest[..end] != "drive.google.com" {
        return Err(invalid());
    }
    let tail = rest[end..].split('#').next().unwrap_or("");
    let (path, query) = tail.split_once('?').unwrap_or((tail, ""));
    let regex =
        crate::backend::search::pattern(r"\A/drive/(?:u/\d+/)?folders/([A-Za-z0-9_-]+)/*\z");
    let capture = regex
        .captures(path)
        .map_err(|_| invalid())?
        .ok_or_else(invalid)?;
    let key = url::form_urlencoded::parse(query.as_bytes())
        .find(|(key, value)| key == "resourcekey" && !value.is_empty())
        .map(|(_, v)| v.into_owned())
        .unwrap_or_default();
    if !key.is_empty() && !identifier(&key) {
        return Err(invalid());
    }
    Ok((capture[1].into(), key))
}
pub fn identifier(value: &str) -> bool {
    !value.is_empty()
        && value
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || c == b'_' || c == b'-')
}
pub fn safe_name(value: &str) -> Result<&str> {
    require(
        !value.is_empty()
            && !matches!(value, "." | "..")
            && !value
                .chars()
                .any(|c| (c as u32) < 32 || "/\\\x7f".contains(c))
            && value.trim_end_matches([' ', '.']) == value,
        "unsafe_path",
        "안전한 파일·폴더 이름으로 처리할 수 없습니다.",
    )?;
    Ok(value)
}
pub fn name_key(value: &str) -> Result<String> {
    Ok(unicode::casefold(
        &safe_name(value)?.nfc().collect::<String>(),
    ))
}
pub fn interval(value: &Value) -> Result<i64> {
    let value = value.as_i64().filter(|n| INTERVALS.contains(n));
    require(
        value.is_some(),
        "invalid_interval",
        "지원하는 동기화 주기를 선택해 주세요.",
    )?;
    Ok(value.unwrap())
}
pub fn next_slot(now: DateTime<Utc>, minutes: i64, zone: &str) -> Result<DateTime<Utc>> {
    interval(&json!(minutes))?;
    let tz = jiff::tz::TimeZone::get(zone).map_err(|_| {
        error(
            "clock",
            "시간대의 다음 실행 시각을 계산하지 못했습니다.",
            false,
        )
    })?;
    let mut at =
        now.with_second(0).unwrap().with_nanosecond(0).unwrap() + chrono::Duration::minutes(1);
    for _ in 0..3 * 1440 {
        let local = jiff::Timestamp::from_second(at.timestamp())
            .map_err(|_| {
                error(
                    "clock",
                    "시간대의 다음 실행 시각을 계산하지 못했습니다.",
                    false,
                )
            })?
            .to_zoned(tz.clone());
        if (i64::from(local.hour()) * 60 + i64::from(local.minute())) % minutes == 0 {
            return Ok(at);
        }
        at += chrono::Duration::minutes(1)
    }
    Err(error(
        "clock",
        "시간대의 다음 실행 시각을 계산하지 못했습니다.",
        false,
    ))
}
pub fn stamp(meta: &fs::Metadata) -> Value {
    json!([
        meta.dev(),
        meta.ino(),
        meta.size(),
        meta.mtime() as i128 * 1_000_000_000 + meta.mtime_nsec() as i128,
        meta.ctime() as i128 * 1_000_000_000 + meta.ctime_nsec() as i128
    ])
}
pub fn is_symlink(path: &Path) -> bool {
    fs::symlink_metadata(path).is_ok_and(|m| m.file_type().is_symlink())
}
pub fn private_dir(path: &Path) -> Result<PathBuf> {
    let mut missing = Vec::new();
    for part in path.ancestors() {
        require(
            !is_symlink(part),
            "unsafe_path",
            "저장 경로의 심볼릭 링크를 처리할 수 없습니다.",
        )?;
        if !part.exists() {
            missing.push(part)
        }
    }
    for part in missing.into_iter().rev() {
        match fs::create_dir(part) {
            Ok(()) => {}
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(e) => return Err(e.into()),
        }
        fs::set_permissions(part, fs::Permissions::from_mode(0o700))?;
    }
    require(path.is_dir(), "unsafe_path", "저장 폴더를 확인해 주세요.")?;
    fs::set_permissions(path, fs::Permissions::from_mode(0o700))?;
    Ok(path.into())
}
pub fn local_path(root: &Path, relative: &str) -> Result<PathBuf> {
    require(
        !is_symlink(root),
        "unsafe_path",
        "수신 폴더의 링크를 처리할 수 없습니다.",
    )?;
    let mut current = root.to_owned();
    for part in relative.split('/') {
        current.push(safe_name(part)?);
        require(
            !is_symlink(&current),
            "unsafe_path",
            "수신 경로의 링크를 처리할 수 없습니다.",
        )?
    }
    Ok(current)
}
pub fn local_inventory(
    sources: &[Value],
    cancelled: &dyn Fn() -> bool,
) -> Result<(Map<String, Value>, Vec<Value>)> {
    let (mut entries, mut errors, mut roots) = (Map::new(), Vec::new(), BTreeSet::new());
    for source in sources {
        let path = Path::new(text(source, "path"));
        let prefix = path.file_name().and_then(|s| s.to_str()).ok_or_else(|| {
            error(
                "unsafe_path",
                "안전한 파일·폴더 이름으로 처리할 수 없습니다.",
                false,
            )
        })?;
        safe_name(prefix)?;
        require(
            roots.insert(name_key(prefix)?),
            "duplicate_path",
            "선택한 항목의 최상위 이름이 겹칩니다. 이름을 구분해 주세요.",
        )?;
        let source_id = source["id"]
            .as_str()
            .map(str::to_owned)
            .unwrap_or_else(|| source["id"].to_string());
        let mut pending = vec![(path.to_owned(), prefix.to_owned())];
        while let Some((path, relative)) = pending.pop() {
            if cancelled() {
                return Err(error("cancelled", "동기화를 중단했습니다.", false));
            }
            let info = fs::symlink_metadata(&path).map_err(|_| {
                error(
                    "local_read",
                    "선택한 로컬 항목을 모두 읽지 못했습니다. 기존 사본을 보존합니다.",
                    false,
                )
            })?;
            let kind = if info.is_dir() { "folder" } else { "file" };
            let message = if !info.is_dir() && !info.is_file() {
                Some("링크·특수 파일은 동기화하지 않습니다.")
            } else if kind == "file" && info.len() > MAX_FILE_BYTES {
                Some("앱의 파일당 100MB 제한을 초과합니다. 기존 사본은 보존합니다.")
            } else {
                None
            };
            let key = format!("{source_id}:{relative}");
            let birth = info
                .created()
                .ok()
                .map(|t| match t.duration_since(std::time::UNIX_EPOCH) {
                    Ok(d) => serde_json::to_string(&d.as_secs_f64()).unwrap(),
                    Err(e) => serde_json::to_string(&(-e.duration().as_secs_f64())).unwrap(),
                })
                .unwrap_or_default();
            entries.insert(key.clone(),json!({"key":key,"source_id":source_id,"path":relative,"local":path,"kind":kind,"size":info.len(),"stamp":stamp(&info),"identity":format!("{}:{}:{}",info.dev(),info.ino(),if cfg!(target_os="macos"){birth}else{String::new()}),"error":message}));
            if let Some(message) = message {
                errors.push(json!({"path":relative,"message":message}))
            } else if kind == "folder" {
                let children = fs::read_dir(&path)
                    .and_then(|e| e.collect::<std::io::Result<Vec<_>>>())
                    .map_err(|_| {
                        error(
                            "local_read",
                            "선택한 로컬 항목을 모두 읽지 못했습니다. 기존 사본을 보존합니다.",
                            false,
                        )
                    })?;
                let mut names = BTreeSet::new();
                for child in children {
                    let name = child
                        .file_name()
                        .to_str()
                        .ok_or_else(|| {
                            error(
                                "unsafe_path",
                                "안전한 파일·폴더 이름으로 처리할 수 없습니다.",
                                false,
                            )
                        })?
                        .to_owned();
                    require(
                        names.insert(name_key(&name)?),
                        "duplicate_path",
                        "파일 이름이 대소문자·문자 정규화 기준으로 겹칩니다.",
                    )?;
                    pending.push((child.path(), format!("{relative}/{name}")));
                }
            }
        }
    }
    Ok((entries, errors))
}
