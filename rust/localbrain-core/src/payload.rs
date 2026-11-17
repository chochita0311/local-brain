use crate::{fields, files, Context, Error, Result};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::BTreeSet;
use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt};
use std::path::{Component, Path, PathBuf};

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Entry {
    pub path: String,
    pub sha256: String,
    pub size: u64,
    pub mode: String,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Manifest {
    pub schema: u64,
    pub target: String,
    pub minimum_os: String,
    pub manager_protocol: u64,
    pub host_protocol: u64,
    pub helper_protocol: u64,
    pub checkpoint_version: String,
    pub unicode_version: String,
    pub node: Value,
    pub core: Value,
    pub engine: Value,
    pub provenance: Value,
    pub runtime_lock_sha256: String,
    pub files: Vec<Entry>,
    pub payload_id: String,
}
pub fn hex_id(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}
fn payload_error() -> Error {
    Error::terminal(
        "setup_required",
        "터미널 실행 구성요소의 버전과 무결성을 확인할 수 없습니다.",
    )
}
fn relative(value: &str) -> bool {
    !value.is_empty()
        && !value.contains('\\')
        && !value.contains('\0')
        && !value.starts_with('/')
        && !value.ends_with('/')
        && value
            .split('/')
            .all(|p| !p.is_empty() && p != "." && p != "..")
}
fn safe_file(root: &Path, name: &str) -> Result<PathBuf> {
    if !relative(name) {
        return Err(payload_error());
    }
    let mut path = root.to_path_buf();
    for component in Path::new(name).components() {
        if !matches!(component, Component::Normal(_)) {
            return Err(payload_error());
        }
        path.push(component);
        if fs::symlink_metadata(&path)
            .map_err(|_| payload_error())?
            .file_type()
            .is_symlink()
        {
            return Err(payload_error());
        }
    }
    Ok(path)
}
pub fn manifest_id(raw: &Value) -> Result<String> {
    let mut body = raw.clone();
    body.as_object_mut()
        .ok_or_else(payload_error)?
        .remove("payloadId");
    // serde_json's default map is recursively key sorted; no preserve_order feature.
    Ok(files::digest(
        &serde_json::to_vec(&body).map_err(|_| payload_error())?,
    ))
}
#[derive(Clone)]
pub struct Payload {
    pub root: PathBuf,
    pub manifest: Manifest,
}
impl Payload {
    pub fn load(root: &Path, private: bool) -> Result<Self> {
        Self::inspect_bytes(root, private, true)
    }
    // Polling inspects the manifest and exact tree shape. Full byte verification
    // occurs before installation/execution and retirement, not on every UI poll.
    pub fn inspect(root: &Path, private: bool) -> Result<Self> {
        Self::inspect_bytes(root, private, false)
    }
    fn inspect_bytes(root: &Path, private: bool, verify: bool) -> Result<Self> {
        if private {
            files::location(root)?;
        }
        let metadata = fs::symlink_metadata(root).map_err(|_| payload_error())?;
        if !metadata.is_dir()
            || metadata.file_type().is_symlink()
            || (private && (metadata.uid() != files::uid() || metadata.mode() & 0o077 != 0))
        {
            return Err(payload_error());
        }
        let path = safe_file(root, "manifest.json")?;
        let file = OpenOptions::new()
            .read(true)
            .custom_flags(libc::O_NOFOLLOW)
            .open(path)
            .map_err(|_| payload_error())?;
        let info = file.metadata().map_err(|_| payload_error())?;
        if !info.is_file()
            || info.nlink() != 1
            || info.len() > 2 * 1024 * 1024
            || (private && !files::regular(&info, true))
        {
            return Err(payload_error());
        }
        let mut bytes = Vec::new();
        file.take(2 * 1024 * 1024 + 1)
            .read_to_end(&mut bytes)
            .map_err(|_| payload_error())?;
        let raw: Value = serde_json::from_slice(&bytes).map_err(|_| payload_error())?;
        let manifest: Manifest =
            serde_json::from_value(raw.clone()).map_err(|_| payload_error())?;
        if manifest.schema != 1
            || manifest.target != "aarch64-apple-darwin"
            || manifest.minimum_os != "14.0"
            || manifest.manager_protocol != 2
            || manifest.host_protocol != 1
            || manifest.helper_protocol != 1
            || manifest.checkpoint_version != "xterm6-v3"
            || manifest.unicode_version != "11"
            || !hex_id(&manifest.payload_id)
            || manifest_id(&raw)? != manifest.payload_id
            || !hex_id(&manifest.runtime_lock_sha256)
            || manifest.files.is_empty()
            || manifest.files.len() > 10000
        {
            return Err(payload_error());
        }
        fields(
            &manifest.node,
            &["version", "abi", "napi", "platform", "arch"],
        )?;
        if manifest.node
            != json!({"version":"24.15.0","abi":137,"napi":10,"platform":"darwin","arch":"arm64"})
        {
            return Err(payload_error());
        }
        fields(&manifest.core, &["version", "rustVersion"])?;
        if manifest.core.get("version").and_then(Value::as_str) != Some(env!("CARGO_PKG_VERSION"))
            || manifest
                .core
                .get("rustVersion")
                .and_then(Value::as_str)
                .is_none()
        {
            return Err(payload_error());
        }
        if manifest.engine
            != json!({"nodePty":"1.1.0","headless":"6.0.0","serialize":"0.14.0","unicode11":"0.9.0"})
        {
            return Err(payload_error());
        }
        fields(
            &manifest.provenance,
            &[
                "sourceCommit",
                "inputSha256",
                "nodeArchiveSha256",
                "signing",
            ],
        )?;
        if !manifest
            .provenance
            .get("sourceCommit")
            .and_then(Value::as_str)
            .is_some_and(|s| s.len() == 40 && s.bytes().all(|c| c.is_ascii_hexdigit()))
            || !["inputSha256", "nodeArchiveSha256"].iter().all(|k| {
                manifest
                    .provenance
                    .get(k)
                    .and_then(Value::as_str)
                    .is_some_and(hex_id)
            })
            || manifest.provenance.get("signing").and_then(Value::as_str) != Some("ad-hoc")
        {
            return Err(payload_error());
        }
        let mut names = BTreeSet::new();
        let mut previous = "";
        for entry in &manifest.files {
            if entry.path.as_str() <= previous
                || entry.path == "manifest.json"
                || !relative(&entry.path)
                || !hex_id(&entry.sha256)
                || !matches!(entry.mode.as_str(), "0600" | "0700")
                || entry.size > 512 * 1024 * 1024
            {
                return Err(payload_error());
            }
            previous = &entry.path;
            names.insert(entry.path.clone());
            let path = safe_file(root, &entry.path)?;
            let info = fs::symlink_metadata(&path).map_err(|_| payload_error())?;
            if !info.is_file()
                || info.nlink() != 1
                || info.len() != entry.size
                || (private
                    && (!files::regular(&info, true)
                        || info.mode() & 0o777
                            != u32::from_str_radix(&entry.mode, 8).map_err(|_| payload_error())?))
                || (verify && files::file_digest(&path)? != entry.sha256)
            {
                return Err(payload_error());
            }
        }
        for required in [
            "bin/node",
            "bin/localbrain-runtime",
            "manager/manager.cjs",
            "manager/status.cjs",
            "engine/package-lock.json",
            "engine/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper",
        ] {
            if !names.contains(required) {
                return Err(payload_error());
            }
        }
        if files::file_digest(&root.join("engine/package-lock.json"))?
            != manifest.runtime_lock_sha256
        {
            return Err(payload_error());
        }
        let actual = tree_files(root, private)?;
        names.insert("manifest.json".into());
        if actual != names {
            return Err(payload_error());
        }
        Ok(Self {
            root: root.to_path_buf(),
            manifest,
        })
    }
    pub fn source() -> Result<Option<Self>> {
        if let Some(root) = std::env::var_os("LOCALBRAIN_TERMINAL_BUNDLE") {
            let root = PathBuf::from(root);
            if !root.is_absolute() {
                return Err(payload_error());
            }
            return Self::inspect(&root, false).map(Some);
        }
        let exe = std::env::current_exe().map_err(|_| payload_error())?;
        let root = exe
            .parent()
            .and_then(Path::parent)
            .ok_or_else(payload_error)?;
        if root.join("manifest.json").is_file() {
            Self::inspect(root, false).map(Some)
        } else {
            Ok(None)
        }
    }
    pub fn prepare(&self, runtime: &Path) -> Result<Self> {
        let verified = Self::load(&self.root, false)?;
        if verified.manifest.payload_id != self.manifest.payload_id {
            return Err(payload_error());
        }
        let folder = runtime.join("payloads");
        files::private_dir(&folder)?;
        let destination = folder.join(&self.manifest.payload_id);
        if destination.exists() {
            let cached = Self::load(&destination, true)?;
            if cached.manifest.payload_id != self.manifest.payload_id {
                return Err(payload_error());
            }
            return Ok(cached);
        }
        let staging = runtime.join("staging");
        files::private_dir(&staging)?;
        let temporary = staging.join(files::random_id()?);
        files::private_dir(&temporary)?;
        let result = (|| {
            for entry in &self.manifest.files {
                let source = safe_file(&self.root, &entry.path)?;
                let target = temporary.join(&entry.path);
                fs::DirBuilder::new()
                    .recursive(true)
                    .mode(0o700)
                    .create(target.parent().ok_or_else(payload_error)?)
                    .map_err(|_| payload_error())?;
                let input = OpenOptions::new()
                    .read(true)
                    .custom_flags(libc::O_NOFOLLOW)
                    .open(source)
                    .map_err(|_| payload_error())?;
                let mut output = OpenOptions::new()
                    .create_new(true)
                    .write(true)
                    .mode(u32::from_str_radix(&entry.mode, 8).map_err(|_| payload_error())?)
                    .open(&target)
                    .map_err(|_| payload_error())?;
                let copied = std::io::copy(&mut input.take(entry.size + 1), &mut output)
                    .map_err(|_| payload_error())?;
                if copied != entry.size {
                    return Err(payload_error());
                }
                output
                    .flush()
                    .and_then(|_| output.sync_all())
                    .map_err(|_| payload_error())?;
            }
            files::atomic_json(
                &temporary.join("manifest.json"),
                &serde_json::to_value(&self.manifest).map_err(|_| payload_error())?,
            )?;
            let _ = Self::load(&temporary, true)?;
            fs::rename(&temporary, &destination).map_err(|_| payload_error())?;
            std::fs::File::open(&folder)
                .and_then(|f| f.sync_all())
                .map_err(|_| payload_error())?;
            Self::load(&destination, true)
        })();
        if temporary.exists() {
            let _ = fs::remove_dir_all(&temporary);
        }
        result
    }
}
fn tree_files(root: &Path, private: bool) -> Result<BTreeSet<String>> {
    fn visit(root: &Path, path: &Path, private: bool, out: &mut BTreeSet<String>) -> Result<()> {
        for item in fs::read_dir(path).map_err(|_| payload_error())? {
            let item = item.map_err(|_| payload_error())?;
            let info = fs::symlink_metadata(item.path()).map_err(|_| payload_error())?;
            if info.file_type().is_symlink() {
                return Err(payload_error());
            }
            if info.is_dir() {
                if private && (info.uid() != files::uid() || info.mode() & 0o777 != 0o700) {
                    return Err(payload_error());
                }
                visit(root, &item.path(), private, out)?;
            } else if info.is_file() {
                out.insert(
                    item.path()
                        .strip_prefix(root)
                        .map_err(|_| payload_error())?
                        .to_str()
                        .ok_or_else(payload_error)?
                        .to_string(),
                );
            } else {
                return Err(payload_error());
            }
        }
        Ok(())
    }
    let mut out = BTreeSet::new();
    visit(root, root, private, &mut out)?;
    Ok(out)
}
pub fn scope(context: &Context) -> String {
    files::digest(
        format!(
            "{}\0{}",
            context.data_dir.display(),
            context.cache_dir.display()
        )
        .as_bytes(),
    )
}
pub fn selected(runtime: &Path, scope: &str) -> Result<Option<Payload>> {
    let Some(value) = files::read_json(&runtime.join("selection.json"), 4096)? else {
        return Ok(None);
    };
    fields(&value, &["schema", "scopeHash", "payloadId"])?;
    if value.get("schema").and_then(Value::as_u64) != Some(1)
        || value.get("scopeHash").and_then(Value::as_str) != Some(scope)
    {
        return Err(Error::identity());
    }
    let id = value
        .get("payloadId")
        .and_then(Value::as_str)
        .filter(|s| hex_id(s))
        .ok_or_else(Error::identity)?;
    let cached = Payload::inspect(&runtime.join("payloads").join(id), true)?;
    if cached.manifest.payload_id != id {
        return Err(payload_error());
    }
    Ok(Some(cached))
}
pub fn lease(runtime: &Path, id: &str, exclusive: bool, create: bool) -> Result<files::Lock> {
    if !hex_id(id) {
        return Err(Error::identity());
    }
    files::Lock::acquire(
        &runtime.join("leases").join(format!("{id}.lock")),
        exclusive,
        create,
    )
}
/// A cached helper protects its own image without needing the app, Python or request input.
pub fn execution_lease() -> Result<Option<files::Lock>> {
    let exe = std::env::current_exe().map_err(|_| Error::identity())?;
    let Some(payload) = exe.parent().and_then(Path::parent) else {
        return Ok(None);
    };
    let Some(payloads) = payload.parent() else {
        return Ok(None);
    };
    if payloads.file_name().is_none_or(|s| s != "payloads") {
        return Ok(None);
    }
    let root = payloads.parent().ok_or_else(Error::identity)?;
    files::location(root)?;
    let id = payload
        .file_name()
        .and_then(|s| s.to_str())
        .filter(|s| hex_id(s))
        .ok_or_else(Error::identity)?;
    lease(root, id, false, false).map(Some)
}
fn tree_receipt(root: &Path, expected_id: &str) -> Result<Value> {
    let payload = Payload::load(root, true)?;
    if payload.manifest.payload_id != expected_id {
        return Err(Error::identity());
    }
    let manifest_hash = files::file_digest(&root.join("manifest.json"))?;
    let mut records = payload.manifest.files.clone();
    records.push(Entry {
        path: "manifest.json".into(),
        sha256: manifest_hash.clone(),
        size: fs::symlink_metadata(root.join("manifest.json"))
            .map_err(|_| Error::identity())?
            .len(),
        mode: "0600".into(),
    });
    records.sort_by(|a, b| a.path.cmp(&b.path));
    let records = serde_json::to_value(&records).map_err(|_| Error::identity())?;
    let tree_hash = files::digest(&serde_json::to_vec(&records).map_err(|_| Error::identity())?);
    Ok(json!({"payloadId":expected_id,"manifestHash":manifest_hash,"treeHash":tree_hash}))
}

pub fn retire(runtime: &Path, scope_hash: &str, args: &Value, stopped: bool) -> Result<Value> {
    fields(args, &["preview", "expectedReceipt", "payloadIds"])?;
    let preview = args
        .get("preview")
        .and_then(Value::as_bool)
        .ok_or_else(Error::invalid)?;
    if preview && args.as_object().is_some_and(|o| o.len() != 1) {
        return Err(Error::invalid());
    }
    if !stopped {
        return Err(Error::terminal(
            "busy",
            "서비스와 작업을 먼저 종료해 주세요.",
        ));
    }
    let folder = runtime.join("payloads");
    let selected = selected(runtime, scope_hash)?.map(|p| p.manifest.payload_id);
    let mut candidates = Vec::new();
    let mut protected = Vec::new();
    if folder.exists() {
        for item in fs::read_dir(&folder).map_err(|_| Error::identity())? {
            let item = item.map_err(|_| Error::identity())?;
            let id = item
                .file_name()
                .into_string()
                .map_err(|_| Error::identity())?;
            if !hex_id(&id) {
                return Err(Error::identity());
            }
            let loss_path = runtime.join("losses").join(format!("{id}.json"));
            let reason = if fs::symlink_metadata(&loss_path).is_ok() {
                Some(
                    if files::read_json(&loss_path, 16384)
                        .ok()
                        .flatten()
                        .is_some_and(|v| {
                            v["schema"] == 1
                                && v["scopeHash"] == scope_hash
                                && v["identity"]["build"] == id
                        })
                    {
                        "unclean"
                    } else {
                        "unknown"
                    },
                )
            } else {
                match lease(runtime, &id, true, false) {
                    Ok(_lease) => None,
                    Err(e) if e.code == "busy" => Some("in_use"),
                    Err(_) => Some("unknown"),
                }
            };
            if let Some(reason) = reason {
                protected.push(json!({"payloadId":id,"reason":reason}));
                continue;
            }
            candidates.push(tree_receipt(&item.path(), &id)?);
        }
    }
    candidates.sort_by_key(|v| v["payloadId"].as_str().unwrap_or("").to_owned());
    protected.sort_by_key(|v| v["payloadId"].as_str().unwrap_or("").to_owned());
    let receipt = json!({"scopeHash":scope_hash,"cleanStopped":true,"selectedPayloadId":selected,"candidates":candidates});
    if preview {
        return Ok(json!({"state":"stopped","receipt":receipt,"protected":protected}));
    }
    let expected = args.get("expectedReceipt").ok_or_else(Error::invalid)?;
    fields(
        expected,
        &[
            "scopeHash",
            "cleanStopped",
            "selectedPayloadId",
            "candidates",
        ],
    )?;
    if expected
        .get("scopeHash")
        .and_then(Value::as_str)
        .is_none_or(|s| !hex_id(s))
        || expected.get("cleanStopped").and_then(Value::as_bool) != Some(true)
        || !expected
            .get("selectedPayloadId")
            .is_some_and(|v| v.is_null() || v.as_str().is_some_and(hex_id))
    {
        return Err(Error::invalid());
    }
    let entries = expected
        .get("candidates")
        .and_then(Value::as_array)
        .ok_or_else(Error::invalid)?;
    let mut previous = "";
    for entry in entries {
        fields(entry, &["payloadId", "manifestHash", "treeHash"])?;
        if !["payloadId", "manifestHash", "treeHash"]
            .iter()
            .all(|key| entry.get(key).and_then(Value::as_str).is_some_and(hex_id))
        {
            return Err(Error::invalid());
        }
        let id = entry["payloadId"].as_str().ok_or_else(Error::invalid)?;
        if id <= previous {
            return Err(Error::invalid());
        }
        previous = id;
    }
    let ids = args
        .get("payloadIds")
        .and_then(Value::as_array)
        .ok_or_else(Error::invalid)?;
    let mut seen = BTreeSet::new();
    let mut locks = Vec::new();
    for value in ids {
        let id = value
            .as_str()
            .filter(|s| hex_id(s))
            .ok_or_else(Error::invalid)?;
        if !seen.insert(id) {
            return Err(Error::invalid());
        }
        if let Some(entry) = protected
            .iter()
            .find(|v| v["payloadId"].as_str() == Some(id))
        {
            return Err(if entry["reason"] == "in_use" {
                Error::terminal("busy", "구성요소가 사용 중입니다.")
            } else {
                Error::identity()
            });
        }
        if !candidates
            .iter()
            .any(|v| v["payloadId"].as_str() == Some(id))
        {
            return Err(Error::invalid());
        }
        if std::env::current_exe()
            .map_err(|_| Error::identity())?
            .starts_with(folder.join(id))
        {
            return Err(Error::terminal(
                "busy",
                "실행 중인 관리 구성요소는 정리할 수 없습니다.",
            ));
        }
        locks.push(lease(runtime, id, true, false)?);
    }
    if expected != &receipt {
        return Err(Error::terminal("conflict", "정리 대상이 변경되었습니다."));
    }
    // Recheck complete signed bytes while all target use leases and control.lock
    // remain held. No later app/control invocation can enter the selected image.
    for id in &seen {
        let current = tree_receipt(&folder.join(id), id)?;
        if !candidates.contains(&current) {
            return Err(Error::terminal("conflict", "정리 대상이 변경되었습니다."));
        }
        if fs::symlink_metadata(runtime.join("losses").join(format!("{id}.json"))).is_ok() {
            return Err(Error::identity());
        }
    }
    if selected.as_deref().is_some_and(|id| seen.contains(id)) {
        files::owned_remove_file(&runtime.join("selection.json"))?;
        files::owned_remove_file(&runtime.join("localbrain-terminal"))?;
    }
    for id in &seen {
        fs::remove_dir_all(folder.join(id)).map_err(|_| Error::identity())?;
    }
    Ok(json!({"retired":seen,"scopeHash":scope_hash}))
}
