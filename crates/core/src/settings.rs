use crate::{fields, files, string, Context, Error, Result};
use serde_json::{json, Value};
use std::ffi::{CStr, CString};
use std::io::Read;
use std::os::unix::fs::OpenOptionsExt;
use std::path::{Path, PathBuf};

pub(crate) fn account(name: Option<&str>) -> Option<(String, String)> {
    let name = name.and_then(|s| CString::new(s).ok());
    let suggested = unsafe { libc::sysconf(libc::_SC_GETPW_R_SIZE_MAX) };
    let mut capacity = usize::try_from(suggested)
        .ok()
        .filter(|n| *n > 0)
        .unwrap_or(16 * 1024);
    loop {
        let mut buffer = vec![0u8; capacity];
        let mut record = std::mem::MaybeUninit::<libc::passwd>::uninit();
        let mut found = std::ptr::null_mut();
        // The native host serves concurrent requests. Reentrant lookups keep
        // both the record and its strings in this call's owned buffer.
        let status = unsafe {
            match name {
                Some(ref s) => libc::getpwnam_r(
                    s.as_ptr(),
                    record.as_mut_ptr(),
                    buffer.as_mut_ptr().cast(),
                    buffer.len(),
                    &mut found,
                ),
                None => libc::getpwuid_r(
                    libc::getuid(),
                    record.as_mut_ptr(),
                    buffer.as_mut_ptr().cast(),
                    buffer.len(),
                    &mut found,
                ),
            }
        };
        if status == libc::ERANGE {
            capacity = capacity.checked_mul(2)?;
            continue;
        }
        if status != 0 || found.is_null() {
            return None;
        }
        let record = unsafe { record.assume_init() };
        if record.pw_dir.is_null() || record.pw_shell.is_null() {
            return None;
        }
        return unsafe {
            Some((
                CStr::from_ptr(record.pw_dir).to_str().ok()?.into(),
                CStr::from_ptr(record.pw_shell).to_str().ok()?.into(),
            ))
        };
    }
}
fn default_shell() -> String {
    std::env::var("SHELL")
        .ok()
        .filter(|s| !s.is_empty())
        .or_else(|| account(None).map(|a| a.1).filter(|s| !s.is_empty()))
        .unwrap_or_else(|| "/bin/zsh".into())
}
fn atom(section: &Value, key: &str, default: &str) -> Result<String> {
    let value = section
        .get(key)
        .ok_or_else(|| Error::preferences("터미널 설정 형식을 확인해 주세요."))?;
    fields(value, &["kind", "value"])?;
    match value.get("kind").and_then(Value::as_str) {
        Some("missing") if value.get("value").is_none() => Ok(default.into()),
        Some("string") => value
            .get("value")
            .and_then(Value::as_str)
            .filter(|v| v.chars().count() <= 4096)
            .map(str::to_owned)
            .ok_or_else(|| Error::preferences("터미널 작업 폴더와 셸은 경로로 입력해 주세요.")),
        _ => Err(Error::preferences(
            "터미널 작업 폴더와 셸은 경로로 입력해 주세요.",
        )),
    }
}
fn expand(value: &str, home: &Path) -> Result<PathBuf> {
    if value.chars().count() > 4096 || value.contains('\0') {
        return Err(Error::preferences("작업 폴더와 셸은 경로로 입력해 주세요."));
    }
    let expanded = if let Some(tail) = value.strip_prefix('~') {
        let (user, rest) = tail.split_once('/').unwrap_or((tail, ""));
        let base = if user.is_empty() {
            home.to_string_lossy().into_owned()
        } else {
            account(Some(user))
                .map(|a| a.0)
                .ok_or_else(|| Error::preferences("작업 폴더와 셸의 경로를 확인해 주세요."))?
        };
        if rest.is_empty() {
            base
        } else {
            format!("{base}/{rest}")
        }
    } else {
        value.into()
    };
    // Match pathlib lexical normalization, preserving .. and significant spaces.
    let root = if expanded.starts_with("//") && !expanded.starts_with("///") {
        "//"
    } else if expanded.starts_with('/') {
        "/"
    } else {
        ""
    };
    let parts: Vec<_> = expanded
        .split('/')
        .filter(|s| !s.is_empty() && *s != ".")
        .collect();
    Ok(PathBuf::from(format!("{root}{}", parts.join("/"))))
}
fn paths(context: &Context, cwd: &str, shell: &str) -> Result<(String, String)> {
    let folder = expand(if cwd.is_empty() { "~" } else { cwd }, &context.home_dir)?;
    let executable = expand(
        if shell.is_empty() {
            default_shell()
        } else {
            shell.into()
        }
        .as_str(),
        &context.home_dir,
    )?;
    if !files::accessible_directory(&folder) {
        return Err(Error::preferences(
            "작업 폴더에 접근할 수 없습니다. 경로를 확인해 주세요.",
        ));
    }
    if !files::absolute_executable(&executable) {
        return Err(Error::preferences(
            "실행 가능한 셸 파일을 선택해 주세요. 예: /bin/zsh",
        ));
    }
    Ok((
        folder.to_string_lossy().into_owned(),
        executable.to_string_lossy().into_owned(),
    ))
}
pub fn execute(context: &Context, operation: &str, args: &Value) -> Result<Value> {
    fields(
        args,
        &["revision", "section", "cwd", "shell", "cwdOverride"],
    )?;
    files::private_location(&context.data_dir, &context.home_dir)?;
    let revision = string(args, "revision")?;
    let file = context.data_dir.join("settings.toml");
    let bytes = match std::fs::symlink_metadata(&file) {
        Ok(info) if files::regular(&info, false) => {
            let input = std::fs::OpenOptions::new()
                .read(true)
                .custom_flags(libc::O_NOFOLLOW)
                .open(&file)
                .map_err(|_| Error::identity())?;
            let info = input.metadata().map_err(|_| Error::identity())?;
            if !files::regular(&info, false) || info.len() > 8 * 1024 * 1024 {
                return Err(Error::identity());
            }
            let mut bytes = Vec::new();
            input
                .take(8 * 1024 * 1024 + 1)
                .read_to_end(&mut bytes)
                .map_err(|_| Error::identity())?;
            if bytes.len() > 8 * 1024 * 1024 {
                return Err(Error::identity());
            }
            bytes
        }
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Vec::new(),
        _ => return Err(Error::identity()),
    };
    if files::digest(&bytes) != revision {
        return Err(Error::preferences(
            "다른 창에서 설정이 변경되었습니다. 다시 불러온 뒤 저장해 주세요.",
        ));
    }
    let section = args.get("section").ok_or_else(Error::invalid)?;
    fields(section, &["kind", "cwd", "shell"])?;
    if !matches!(
        section.get("kind").and_then(Value::as_str),
        Some("missing" | "table")
    ) {
        return Err(Error::preferences("터미널 설정 형식을 확인해 주세요."));
    }
    let cwd = atom(section, "cwd", &context.home_dir.to_string_lossy())?;
    let shell = atom(section, "shell", "")?;
    match operation {
        "settings.read" => {
            fields(args, &["revision", "section"])?;
            Ok(json!({"cwd":cwd,"shell":shell,"default_shell":default_shell(),"revision":revision}))
        }
        "settings.launch" => {
            fields(args, &["revision", "section", "cwdOverride"])?;
            let actual = match args.get("cwdOverride") {
                None => cwd.as_str(),
                Some(v) => v.as_str().ok_or_else(Error::invalid)?,
            };
            let (cwd, shell) = paths(context, actual, &shell)?;
            Ok(json!({"cwd":cwd,"shell":shell}))
        }
        "settings.prepare" => {
            fields(args, &["revision", "section", "cwd", "shell"])?;
            let raw_shell = args
                .get("shell")
                .and_then(Value::as_str)
                .ok_or_else(|| Error::preferences("작업 폴더와 셸은 경로로 입력해 주세요."))?;
            let cwd = args
                .get("cwd")
                .and_then(Value::as_str)
                .ok_or_else(|| Error::preferences("작업 폴더와 셸은 경로로 입력해 주세요."))?;
            let (cwd, shell) = paths(context, cwd, raw_shell)?;
            Ok(
                json!({"revision":revision,"scopeHash":files::digest(format!("{}\0{}",context.data_dir.display(),context.cache_dir.display()).as_bytes()),"patch":{"cwd":cwd,"shell":if raw_shell.is_empty(){""}else{&shell}}}),
            )
        }
        _ => Err(Error::invalid()),
    }
}

#[cfg(test)]
mod account_tests {
    use super::{account, default_shell};
    use std::sync::Barrier;

    #[test]
    fn concurrent_account_lookups_keep_owned_home_and_default_shell_results() {
        let expected = account(None).expect("test process must have an OS account");
        let expected_shell = default_shell();
        let unknown = format!(
            "localbrain-missing-account-{}",
            crate::files::random_id().unwrap()
        );
        assert!(account(Some(&unknown)).is_none());
        let start = Barrier::new(8);
        std::thread::scope(|scope| {
            for _ in 0..8 {
                let expected = &expected;
                let expected_shell = &expected_shell;
                let unknown = &unknown;
                let start = &start;
                scope.spawn(move || {
                    start.wait();
                    for _ in 0..64 {
                        assert!(account(Some(unknown)).is_none());
                        assert_eq!(account(None).as_ref(), Some(expected));
                        assert_eq!(&default_shell(), expected_shell);
                    }
                });
            }
        });
    }
}
