//! Immutable zsh shims preserve the user's startup scope and ZDOTDIR state.
use crate::{
    backend::{storage, BackendError, Config, Result},
    files,
};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    os::unix::fs::{MetadataExt, PermissionsExt},
    path::Path,
};
fn failure(message: &str) -> BackendError {
    BackendError::conflict(message)
}
fn quote(value: &str) -> String {
    if !value.is_empty()
        && value
            .bytes()
            .all(|ch| ch.is_ascii_alphanumeric() || b"_@%+=:,./-".contains(&ch))
    {
        value.into()
    } else {
        format!("'{}'", value.replace('\'', "'\"'\"'"))
    }
}
fn ascii_json(value: &str) -> String {
    let encoded = serde_json::to_string(value).unwrap();
    let mut out = String::new();
    for ch in encoded.chars() {
        if ch as u32 >= 0x7f {
            for point in ch.encode_utf16(&mut [0; 2]) {
                out.push_str(&format!("\\u{point:04x}"));
            }
        } else {
            out.push(ch);
        }
    }
    out
}
fn templates(shell: &str) -> BTreeMap<String, String> {
    let templates: BTreeMap<String, String> =
        serde_json::from_str(include_str!("zsh-templates.json")).expect("bundled zsh templates");
    templates
        .into_iter()
        .map(|(name, template)| (name, template.replace("@LOCALBRAIN_SHELL@", &quote(shell))))
        .collect()
}
fn directory(path: &Path) -> Result<()> {
    let info = std::fs::symlink_metadata(path)?;
    if !info.is_dir() || info.uid() != unsafe { libc::getuid() } || info.mode() & 0o077 != 0 {
        return Err(failure("셸 연동 저장 위치를 확인해 주세요."));
    }
    Ok(())
}
fn regular(path: &Path, mode: u32) -> Result<()> {
    let info = std::fs::symlink_metadata(path)?;
    if !info.is_file()
        || info.uid() != unsafe { libc::getuid() }
        || info.nlink() != 1
        || info.mode() & 0o7777 != mode
    {
        return Err(failure("셸 연동 파일의 소유권과 권한을 확인해 주세요."));
    }
    Ok(())
}
pub fn verify(root: &Path) -> Result<()> {
    directory(
        root.parent()
            .ok_or_else(|| failure("셸 연동 저장 위치를 확인해 주세요."))?,
    )?;
    directory(root)?;
    let manifest = root.join("manifest.json");
    regular(&manifest, 0o600)?;
    let value = files::read_json(&manifest, 16 * 1024)
        .map_err(|_| failure("셸 연동 파일을 확인해 주세요."))?
        .ok_or_else(|| failure("셸 연동 파일을 확인해 주세요."))?;
    let expected = [
        "launcher",
        "hooks.zsh",
        ".zshenv",
        ".zprofile",
        ".zshrc",
        ".zlogin",
    ];
    if !value.as_object().is_some_and(|map| {
        map.len() == 3
            && map
                .keys()
                .all(|key| ["schema", "shell", "files"].contains(&key.as_str()))
    }) || value["schema"].as_i64() != Some(1)
        || !value["shell"]
            .as_str()
            .is_some_and(|shell| Path::new(shell).is_absolute())
        || !value["files"].as_object().is_some_and(|map| {
            map.len() == expected.len() && map.keys().all(|key| expected.contains(&key.as_str()))
        })
    {
        return Err(failure("셸 연동 파일을 확인해 주세요."));
    }
    for (name, digest) in value["files"].as_object().unwrap() {
        let path = root.join(name);
        regular(&path, if name == "launcher" { 0o700 } else { 0o600 })?;
        if files::digest(&std::fs::read(path)?) != digest.as_str().unwrap_or("") {
            return Err(failure(
                "셸 연동 파일이 변경되었습니다. 새 터미널 생성을 멈췄습니다.",
            ));
        }
    }
    Ok(())
}
pub fn integrated_shell(config: &Config, shell: &Value) -> Result<Value> {
    let Some(shell) = shell.as_str() else {
        return Ok(shell.clone());
    };
    let executable = Path::new(shell);
    let name = executable
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("");
    if !["zsh", "launcher"].contains(&name) {
        return Ok(json!(shell));
    }
    let family = storage::files::validate_runtime_directory(&config.data_dir, config)
        .map_err(|_| failure("셸 연동 저장 위치를 확인해 주세요."))?
        .join("terminal-shell");
    if name == "launcher"
        && executable
            .ancestors()
            .skip(1)
            .any(|parent| parent == family)
    {
        verify(executable.parent().unwrap())?;
        return Ok(json!(shell));
    }
    if name != "zsh" || !files::absolute_executable(executable) {
        return Ok(json!(shell));
    }
    let templates = templates(shell);
    let canonical = format!(
        "{{{}}}",
        templates
            .iter()
            .map(|(name, value)| format!("{}: {}", ascii_json(name), ascii_json(value)))
            .collect::<Vec<_>>()
            .join(", ")
    );
    let root = family.join(format!(
        "zsh-{}",
        &files::digest(canonical.as_bytes())[..24]
    ));
    let _lock = storage::operation_lock(config, "terminal-shell")
        .map_err(|_| failure("다른 로컬 작업이 저장 중입니다. 잠시 후 다시 시도해 주세요."))?;
    storage::files::private_directory(&config.data_dir, config)
        .map_err(|_| failure("셸 연동 저장 위치를 확인해 주세요."))?;
    for path in [&family, &root] {
        match std::fs::DirBuilder::new().mode(0o700).create(path) {
            Ok(()) => {}
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(error) => return Err(error.into()),
        }
        directory(path)?;
    }
    if std::fs::symlink_metadata(root.join("manifest.json")).is_ok() {
        verify(&root)?;
        return Ok(json!(root.join("launcher")));
    }
    let mut hashes = BTreeMap::new();
    for (name, template) in templates {
        let path = root.join(&name);
        let content = template.replace("@SHIM@", &quote(&root.to_string_lossy()));
        match std::fs::symlink_metadata(&path) {
            Ok(info) => {
                if !info.is_file()
                    || info.uid() != unsafe { libc::getuid() }
                    || info.nlink() != 1
                    || info.mode() & 0o077 != 0
                    || std::fs::read(&path)? != content.as_bytes()
                {
                    return Err(failure("완료되지 않은 셸 연동 파일을 확인해 주세요."));
                }
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                files::atomic_bytes(&path, content.as_bytes(), 0o600)
                    .map_err(|error| failure(&error.message))?
            }
            Err(error) => return Err(error.into()),
        }
        std::fs::set_permissions(
            &path,
            std::fs::Permissions::from_mode(if name == "launcher" { 0o700 } else { 0o600 }),
        )?;
        hashes.insert(name, files::digest(content.as_bytes()));
    }
    files::atomic_json(
        &root.join("manifest.json"),
        &json!({"schema":1,"shell":shell,"files":hashes}),
    )
    .map_err(|error| failure(&error.message))?;
    verify(&root)?;
    Ok(json!(root.join("launcher")))
}
use std::os::unix::fs::DirBuilderExt;
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn immutable_shim_identity_matches_frozen_python_unicode_and_shell_quoting() {
        let cases: Vec<Value> = serde_json::from_str(include_str!(
            "../../../tests/fixtures/native-zsh-identity.json"
        ))
        .unwrap();
        for case in cases {
            let templates = templates(case["shell"].as_str().unwrap());
            let canonical = format!(
                "{{{}}}",
                templates
                    .iter()
                    .map(|(name, value)| format!("{}: {}", ascii_json(name), ascii_json(value)))
                    .collect::<Vec<_>>()
                    .join(", ")
            );
            assert_eq!(
                &files::digest(canonical.as_bytes())[..24],
                case["identity"].as_str().unwrap(),
                "{}",
                case["shell"]
            );
        }
    }
}
