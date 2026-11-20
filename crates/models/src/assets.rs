//! Public allowlisted installation and independently verified offline assets.
use crate::catalog::{
    ModelKey, ModelSpec, EMBEDDING_SCHEMA, GENERATION_HUB_OWNER, GENERATION_OWNER,
};
use crate::{check_cancel, require, Cancellation, ModelError, Result};
use reqwest::blocking::Client;
use reqwest::header::{CONTENT_RANGE, ETAG, RANGE};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeSet, HashSet};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
#[cfg(unix)]
use std::os::unix::{
    fs::{symlink, DirBuilderExt, MetadataExt, OpenOptionsExt},
    io::AsRawFd,
};
use std::path::{Component, Path, PathBuf};
use std::time::Duration;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FileRecord {
    pub path: String,
    pub size: u64,
    pub sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ModelIdentity {
    pub model_id: String,
    pub resolved_revision: String,
    pub fingerprint: String,
}

/// Can only be constructed by full verification. It grants no network capability.
#[derive(Debug, Clone)]
pub struct VerifiedModel {
    pub(crate) key: ModelKey,
    pub(crate) snapshot: PathBuf,
    pub(crate) boundary: PathBuf,
    pub(crate) identity: ModelIdentity,
    pub(crate) files: Vec<FileRecord>,
    pub(crate) selection: Option<ManifestSelection>,
}
#[derive(Debug, Clone)]
pub(crate) struct ManifestSelection {
    path: PathBuf,
    sha256: String,
}
impl VerifiedModel {
    pub fn key(&self) -> ModelKey {
        self.key
    }
    pub fn snapshot(&self) -> &Path {
        &self.snapshot
    }
    pub fn identity(&self) -> &ModelIdentity {
        &self.identity
    }
    pub fn files(&self) -> &[FileRecord] {
        &self.files
    }
    /// The exact explicit registration selected by this grant; cache-only
    /// verification has no registration and does not invent one.
    pub fn manifest_path(&self) -> Option<&Path> {
        self.selection
            .as_ref()
            .map(|selection| selection.path.as_path())
    }
    fn reverify_selection(&self, cancel: &Cancellation) -> Result<()> {
        check_cancel(cancel)?;
        if let Some(selection) = &self.selection {
            let bytes = selected_manifest_bytes(&selection.path)?;
            require(
                sha256(&bytes) == selection.sha256,
                "MODEL_REGISTRATION_CHANGED",
                "selected model manifest changed since verification",
            )?;
        }
        Ok(())
    }
    pub fn weight_files(&self) -> Vec<PathBuf> {
        self.files
            .iter()
            .filter(|x| x.path.ends_with(".safetensors"))
            .map(|x| self.snapshot.join(&x.path))
            .collect()
    }
    /// Check again before lazy model loading; verification does not freeze files.
    pub fn reverify(&self, cancel: &Cancellation) -> Result<()> {
        self.reverify_selection(cancel)?;
        let expected = self.files.iter().map(|file| file.path.clone()).collect();
        validate_snapshot_names(&self.snapshot, &self.boundary, &expected)?;
        let files = self
            .files
            .iter()
            .map(|record| revalidate_record(&self.snapshot, &self.boundary, record, cancel))
            .collect::<Result<Vec<_>>>()?;
        require(
            files == self.files
                && inventory_fingerprint(&files, self.key == ModelKey::Embedding)?
                    == self.identity.fingerprint,
            "MODEL_ASSETS_CHANGED",
            "assets changed since verification",
        )
    }
    /// Revalidate only the assets consumed by OfflineTokenizer. This does not
    /// claim that weights remain verified or replace reverify() before loading.
    pub(crate) fn reverify_tokenizer(&self, cancel: &Cancellation) -> Result<()> {
        self.reverify_selection(cancel)?;
        within(&self.snapshot, &self.boundary)?;
        for name in ["tokenizer.json", "tokenizer_config.json"] {
            let record = self
                .files
                .iter()
                .find(|record| record.path == name)
                .ok_or_else(|| {
                    ModelError::new("INVALID_MODEL", "verified tokenizer asset record missing")
                })?;
            revalidate_record(&self.snapshot, &self.boundary, record, cancel)?;
        }
        Ok(())
    }
}

fn revalidate_record(
    snapshot: &Path,
    boundary: &Path,
    record: &FileRecord,
    cancel: &Cancellation,
) -> Result<FileRecord> {
    check_cancel(cancel)?;
    require(
        safe_relative(&record.path),
        "INVALID_MODEL",
        "unsafe verified asset record",
    )?;
    let path = snapshot.join(&record.path);
    within(&path, boundary)?;
    let (size, hash) = hash_file(&path, cancel)?;
    require(
        size == record.size && hash == record.sha256,
        "MODEL_ASSETS_CHANGED",
        "assets changed since verification",
    )?;
    Ok(FileRecord {
        path: record.path.clone(),
        size,
        sha256: hash,
    })
}

/// Synthetic sealed-record fixture for crate-internal lifetime tests only. It
/// does not assert a catalog identity and is absent from production builds.
#[cfg(test)]
pub(crate) fn fixture_verified(snapshot: &Path, names: &[&str]) -> VerifiedModel {
    let cancel = crate::cancellation();
    let mut names = names.to_vec();
    names.sort_unstable();
    let files = names
        .into_iter()
        .map(|name| {
            let (size, sha256) = hash_file(&snapshot.join(name), &cancel).unwrap();
            FileRecord {
                path: name.into(),
                size,
                sha256,
            }
        })
        .collect::<Vec<_>>();
    let fingerprint = inventory_fingerprint(&files, true).unwrap();
    VerifiedModel {
        key: ModelKey::Embedding,
        snapshot: snapshot.into(),
        boundary: snapshot.parent().unwrap().into(),
        identity: ModelIdentity {
            model_id: "Synthetic/Embedding".into(),
            resolved_revision: "0".repeat(40),
            fingerprint,
        },
        files,
        selection: None,
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelStatus {
    pub key: ModelKey,
    pub model_id: String,
    pub revision: String,
    pub purpose: String,
    pub state: String,
    pub registered: bool,
    pub cached: bool,
    pub experiment_suspended: bool,
}

pub fn model_root(key: ModelKey, data_dir: &Path) -> PathBuf {
    let spec = key.spec();
    let legacy = data_dir.join(spec.slug);
    let canonical = data_dir.join("models").join(spec.slug);
    if legacy.exists() && !canonical.exists() {
        legacy
    } else {
        canonical
    }
}

/// File-presence information only: no JSON parsing, hashing, tokenizer, weights or HTTP.
pub fn model_status(data_dir: &Path, cache_root: &Path) -> Vec<ModelStatus> {
    ModelKey::ALL
        .into_iter()
        .map(|key| {
            let spec = key.spec();
            let root = model_root(key, data_dir);
            let registered = root.join("model.json").is_file();
            let snapshot = cache_root.join(spec.snapshot_relative());
            let cached = spec.assets.iter().all(|name| snapshot.join(name).is_file());
            ModelStatus {
                key,
                model_id: spec.id.into(),
                revision: spec.revision.into(),
                purpose: spec.purpose.into(),
                state: if registered {
                    "PRESENT_UNVERIFIED"
                } else {
                    "NOT_INSTALLED"
                }
                .into(),
                registered,
                cached,
                experiment_suspended: spec.experiment_suspended(),
            }
        })
        .collect()
}

#[derive(Debug, Clone)]
pub struct InstallOptions {
    pub model: ModelKey,
    pub registration_root: PathBuf,
    pub cache_root: PathBuf,
    pub offline: bool,
    /// Explicit cache selection may replace a registration, never its original assets.
    pub replace_cache: bool,
    pub expected_registration_revision: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstallProgress {
    pub phase: String,
    pub file: Option<String>,
    pub downloaded_bytes: u64,
    pub total_bytes: Option<u64>,
}

pub fn registration_revision(root: &Path) -> Result<String> {
    let path = root.join("model.json");
    require(
        !path.is_symlink(),
        "INVALID_MODEL",
        "registration cannot be a symlink",
    )?;
    match fs::read(&path) {
        Ok(bytes) => Ok(sha256(&bytes)),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(sha256(b"")),
        Err(e) => Err(e.into()),
    }
}

/// Does not accept arbitrary URLs, repositories, file names, credentials or private input.
pub fn install(
    options: &InstallOptions,
    cancel: &Cancellation,
    progress: impl FnMut(InstallProgress),
) -> Result<VerifiedModel> {
    install_with_transfer_admission(options, cancel, progress, || Ok(()))
}

/// Admit a command-owned transfer directory only when a missing public asset
/// actually needs transport, after acquiring the registration lease. Native
/// HTTPS does not initialize or use the historical Python/Xet client.
pub fn install_with_transfer_admission(
    options: &InstallOptions,
    cancel: &Cancellation,
    mut progress: impl FnMut(InstallProgress),
    admission: impl FnOnce() -> Result<()>,
) -> Result<VerifiedModel> {
    check_cancel(cancel)?;
    let spec = options.model.spec();
    let root = absolute_path(&options.registration_root)?;
    let cache = absolute_path(&options.cache_root)?;
    require(
        !cache.starts_with(&root) && !root.starts_with(&cache),
        "INVALID_MODEL_ROOT",
        "cache and registration must be separate",
    )?;
    let _lock = RegistrationLock::acquire(&root, spec, true)?;
    check_revision(&root, options.expected_registration_revision.as_deref())?;
    if root.join("model.json").is_file() && !options.replace_cache {
        return verify_unlocked(&root, &cache, options.model, cancel);
    }
    let previous = if root.join("model.json").is_file() {
        let value = read_owned_json(&root.join("model.json"))?;
        verify_manifest_identity(&value, spec)?;
        value
    } else {
        json!({})
    };
    ensure_directory(&cache)?;
    let repository = cache.join(format!("models--{}", spec.id.replace('/', "--")));
    ensure_directory(&repository)?;
    ensure_directory(&repository.join("snapshots"))?;
    let snapshot = repository.join("snapshots").join(spec.revision);
    ensure_directory(&snapshot)?;
    let mut client = None;
    let mut admission = Some(admission);
    for name in spec.assets {
        check_cancel(cancel)?;
        let destination = snapshot.join(name);
        if destination.is_file() {
            within(&destination, &repository)?;
            continue;
        }
        require(
            !destination.exists() && !destination.is_symlink(),
            "INVALID_MODEL",
            "invalid cached asset",
        )?;
        require(
            !options.offline,
            "MODEL_NOT_CACHED",
            "pinned public files are missing from the selected local cache",
        )?;
        if client.is_none() {
            admission.take().expect("first public transport")()?;
            client = Some(public_client()?);
        }
        progress(InstallProgress {
            phase: "downloading".into(),
            file: Some((*name).into()),
            downloaded_bytes: 0,
            total_bytes: None,
        });
        download_file(
            client.as_ref().unwrap(),
            spec,
            name,
            &repository,
            &destination,
            cancel,
            &mut progress,
        )?;
    }
    progress(InstallProgress {
        phase: "verifying".into(),
        file: None,
        downloaded_bytes: 0,
        total_bytes: None,
    });
    let files = inventory(&snapshot, &repository, spec, cancel)?;
    let fingerprint = inventory_fingerprint(&files, spec.key == ModelKey::Embedding)?;
    let mut manifest = previous;
    let object = manifest
        .as_object_mut()
        .ok_or_else(|| ModelError::new("INVALID_MODEL", "registration must be an object"))?;
    if spec.key == ModelKey::Embedding {
        object.insert("schema".into(), json!(EMBEDDING_SCHEMA));
        object.insert("requested_revision".into(), json!(spec.revision));
        object.insert("resolved_revision".into(), json!(spec.revision));
    } else {
        object.insert("owner".into(), json!(GENERATION_HUB_OWNER));
        object.insert("revision".into(), json!(spec.revision));
        object.insert(
            "installed_at".into(),
            json!(chrono::Utc::now().to_rfc3339()),
        );
    }
    object.insert("model_id".into(), json!(spec.id));
    object.insert("snapshot".into(), json!(spec.snapshot_relative()));
    object.insert("cache_root".into(), json!(cache));
    object.insert("fingerprint".into(), json!(fingerprint));
    object.insert("files".into(), serde_json::to_value(&files)?);
    check_cancel(cancel)?;
    check_revision(&root, options.expected_registration_revision.as_deref())?;
    atomic_json(&root.join("model.json"), &manifest)?;
    Ok(VerifiedModel {
        key: spec.key,
        snapshot,
        boundary: repository,
        files,
        selection: Some(ManifestSelection {
            path: root.join("model.json"),
            sha256: sha256((serde_json::to_string_pretty(&manifest)? + "\n").as_bytes()),
        }),
        identity: ModelIdentity {
            model_id: spec.id.into(),
            resolved_revision: spec.revision.into(),
            fingerprint,
        },
    })
}

pub fn verify_model(
    root: &Path,
    default_cache_root: &Path,
    key: ModelKey,
    cancel: &Cancellation,
) -> Result<VerifiedModel> {
    check_cancel(cancel)?;
    let root = absolute_path(root)?;
    require(
        root.is_dir(),
        "MODEL_NOT_INSTALLED",
        "model registration is missing",
    )?;
    let _lock = RegistrationLock::acquire(&root, key.spec(), false)?;
    verify_unlocked(&root, default_cache_root, key, cancel)
}

/// Verify one explicitly named absolute regular manifest. No discovery, owner
/// creation, lock, copy, registration or network operation is performed.
pub fn verify_manifest(
    manifest: &Path,
    default_cache_root: &Path,
    key: ModelKey,
    cancel: &Cancellation,
) -> Result<VerifiedModel> {
    check_cancel(cancel)?;
    verify_manifest_unlocked(manifest, default_cache_root, key, cancel)
}

/// Independently inspect pinned cached assets without creating registration,
/// directories, lock files, network clients or model weights in memory.
pub fn verify_cached(
    key: ModelKey,
    cache_root: &Path,
    cancel: &Cancellation,
) -> Result<VerifiedModel> {
    check_cancel(cancel)?;
    let cache = absolute_path(cache_root)?;
    let spec = key.spec();
    let boundary = cache.join(format!("models--{}", spec.id.replace('/', "--")));
    let snapshot = cache.join(spec.snapshot_relative());
    require(
        boundary.is_dir() && !boundary.is_symlink() && snapshot.is_dir() && !snapshot.is_symlink(),
        "MODEL_NOT_CACHED",
        "pinned cached snapshot is missing",
    )?;
    within(&snapshot, &boundary)?;
    let files = inventory(&snapshot, &boundary, spec, cancel)?;
    let fingerprint = inventory_fingerprint(&files, key == ModelKey::Embedding)?;
    Ok(VerifiedModel {
        key,
        snapshot,
        boundary,
        files,
        selection: None,
        identity: ModelIdentity {
            model_id: spec.id.into(),
            resolved_revision: spec.revision.into(),
            fingerprint,
        },
    })
}

fn verify_unlocked(
    root: &Path,
    default_cache_root: &Path,
    key: ModelKey,
    cancel: &Cancellation,
) -> Result<VerifiedModel> {
    verify_manifest_unlocked(&root.join("model.json"), default_cache_root, key, cancel)
}

fn selected_manifest_bytes(path: &Path) -> Result<Vec<u8>> {
    require(
        path.is_absolute() && path.is_file() && !path.is_symlink(),
        "INVALID_MODEL",
        "model manifest must be an absolute regular non-symlink file",
    )?;
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(unix)]
    options.custom_flags(libc::O_NOFOLLOW);
    let file = options.open(path)?;
    require(
        file.metadata()?.is_file(),
        "INVALID_MODEL",
        "model manifest must be a regular file",
    )?;
    let mut bytes = Vec::new();
    file.take(32 * 1024 * 1024 + 1).read_to_end(&mut bytes)?;
    require(
        bytes.len() <= 32 * 1024 * 1024,
        "INVALID_MODEL",
        "model manifest exceeds its bound",
    )?;
    Ok(bytes)
}
fn verify_manifest_unlocked(
    manifest_path: &Path,
    default_cache_root: &Path,
    key: ModelKey,
    cancel: &Cancellation,
) -> Result<VerifiedModel> {
    let bytes = selected_manifest_bytes(manifest_path)?;
    let selection = ManifestSelection {
        path: manifest_path.into(),
        sha256: sha256(&bytes),
    };
    let manifest: Value = serde_json::from_slice(&bytes)?;
    let root = manifest_path
        .parent()
        .ok_or_else(|| ModelError::new("INVALID_MODEL", "manifest parent is missing"))?;
    let spec = key.spec();
    verify_manifest_identity(&manifest, spec)?;
    let relative = manifest
        .get("snapshot")
        .and_then(Value::as_str)
        .ok_or_else(|| ModelError::new("INVALID_MODEL", "snapshot missing"))?;
    require(
        safe_relative(relative),
        "INVALID_MODEL",
        "unsafe snapshot path",
    )?;
    let legacy = manifest.get("schema").and_then(Value::as_str)
        == Some("foundry.semantic-model/v1")
        || manifest.get("owner").and_then(Value::as_str) == Some(GENERATION_OWNER);
    let (snapshot, boundary) = if legacy {
        let boundary = if key == ModelKey::Embedding {
            root.parent()
                .and_then(Path::parent)
                .ok_or_else(|| ModelError::new("INVALID_MODEL", "invalid legacy registration"))?
                .canonicalize()?
        } else {
            root.to_path_buf()
        };
        let snapshot = boundary.join(relative);
        require(
            snapshot.file_name().and_then(|x| x.to_str()) == Some(spec.revision),
            "INVALID_MODEL",
            "legacy revision mismatch",
        )?;
        (snapshot, boundary)
    } else {
        require(
            relative == spec.snapshot_relative(),
            "INVALID_MODEL",
            "snapshot does not match pinned revision",
        )?;
        let cache = if let Some(value) = manifest.get("cache_root") {
            absolute_path(Path::new(value.as_str().ok_or_else(|| {
                ModelError::new("INVALID_MODEL", "cache_root must be a path")
            })?))?
        } else {
            absolute_path(default_cache_root)?
        };
        let repository = cache.join(format!("models--{}", spec.id.replace('/', "--")));
        require(
            !repository.is_symlink(),
            "INVALID_MODEL",
            "repository cannot be a symlink",
        )?;
        (cache.join(relative), repository)
    };
    require(
        snapshot.is_dir() && !snapshot.is_symlink(),
        "INVALID_MODEL",
        "snapshot must be a local directory",
    )?;
    within(&snapshot, &boundary)?;
    let files = inventory(&snapshot, &boundary, spec, cancel)?;
    let fingerprint = inventory_fingerprint(&files, key == ModelKey::Embedding)?;
    require(
        manifest.get("files") == Some(&serde_json::to_value(&files)?)
            && manifest.get("fingerprint").and_then(Value::as_str) == Some(&fingerprint),
        "MODEL_ASSETS_CHANGED",
        "registered asset inventory or fingerprint changed",
    )?;
    let verified = VerifiedModel {
        key,
        snapshot,
        boundary,
        files,
        selection: Some(selection),
        identity: ModelIdentity {
            model_id: spec.id.into(),
            resolved_revision: spec.revision.into(),
            fingerprint,
        },
    };
    verified.reverify_selection(cancel)?;
    Ok(verified)
}

fn verify_manifest_identity(value: &Value, spec: ModelSpec) -> Result<()> {
    let registered = if spec.key == ModelKey::Embedding {
        matches!(
            value.get("schema").and_then(Value::as_str),
            Some(EMBEDDING_SCHEMA | "foundry.semantic-model/v1" | "foundry.semantic-model/v2")
        ) && value.get("resolved_revision").and_then(Value::as_str) == Some(spec.revision)
            && value.get("fingerprint").and_then(Value::as_str) == spec.aggregate
    } else {
        matches!(
            value.get("owner").and_then(Value::as_str),
            Some(GENERATION_OWNER | GENERATION_HUB_OWNER)
        ) && value.get("revision").and_then(Value::as_str) == Some(spec.revision)
    };
    require(
        registered && value.get("model_id").and_then(Value::as_str) == Some(spec.id),
        "INVALID_MODEL",
        "registration does not identify the pinned model",
    )
}

pub fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

/// Python-compatible sorted compact value digest, used by existing generation records.
pub fn value_digest(value: &Value) -> Result<String> {
    Ok(sha256(
        serde_json::to_string(&sorted_json(value))
            .map_err(ModelError::from)?
            .as_bytes(),
    ))
}

fn sorted_json(value: &Value) -> Value {
    match value {
        Value::Array(xs) => Value::Array(xs.iter().map(sorted_json).collect()),
        Value::Object(map) => {
            let mut keys: Vec<_> = map.keys().collect();
            keys.sort();
            Value::Object(
                keys.into_iter()
                    .map(|key| (key.clone(), sorted_json(&map[key])))
                    .collect(),
            )
        }
        x => x.clone(),
    }
}

fn inventory_fingerprint(files: &[FileRecord], embedding: bool) -> Result<String> {
    let value = sorted_json(&serde_json::to_value(files)?);
    if embedding {
        Ok(sha256(
            (serde_json::to_string_pretty(&value)? + "\n").as_bytes(),
        ))
    } else {
        value_digest(&value)
    }
}

fn inventory(
    snapshot: &Path,
    boundary: &Path,
    spec: ModelSpec,
    cancel: &Cancellation,
) -> Result<Vec<FileRecord>> {
    let expected: BTreeSet<_> = spec.assets.iter().map(|x| (*x).to_string()).collect();
    validate_snapshot_names(snapshot, boundary, &expected)?;
    let mut files = Vec::with_capacity(expected.len());
    for name in expected {
        check_cancel(cancel)?;
        let path = snapshot.join(&name);
        within(&path, boundary)?;
        let (size, hash) = hash_file(&path, cancel)?;
        if let Some(expected) = spec.pinned_hash(&name) {
            require(
                hash == expected,
                "MODEL_ASSETS_CHANGED",
                "pinned asset hash mismatch",
            )?;
        }
        files.push(FileRecord {
            path: name,
            size,
            sha256: hash,
        });
    }
    if let Some(expected) = spec.aggregate {
        require(
            inventory_fingerprint(&files, true)? == expected,
            "MODEL_ASSETS_CHANGED",
            "pinned aggregate hash mismatch",
        )?;
    }
    let config = read_json(&snapshot.join("config.json"))?;
    require(
        config.get("model_type").and_then(Value::as_str) == Some("qwen3")
            && config.get("auto_map").is_none(),
        "INVALID_MODEL",
        "only native Qwen3 config without remote code is supported",
    )?;
    if spec.key != ModelKey::Embedding {
        let index = read_json(&snapshot.join("model.safetensors.index.json"))?;
        let weights = index
            .get("weight_map")
            .and_then(Value::as_object)
            .ok_or_else(|| ModelError::new("INVALID_MODEL", "weight_map missing"))?;
        let shards: BTreeSet<_> = weights.values().filter_map(Value::as_str).collect();
        require(
            weights.values().all(Value::is_string)
                && shards
                    == spec
                        .assets
                        .iter()
                        .copied()
                        .filter(|x| x.ends_with(".safetensors"))
                        .collect(),
            "INVALID_MODEL",
            "weight index references unexpected shards",
        )?;
    }
    Ok(files)
}

fn validate_snapshot_names(
    snapshot: &Path,
    boundary: &Path,
    expected: &BTreeSet<String>,
) -> Result<()> {
    require(snapshot.is_dir(), "INVALID_MODEL", "snapshot missing")?;
    within(snapshot, boundary)?;
    let names = snapshot_files(snapshot, snapshot, boundary)?;
    let harmless: HashSet<_> = ["README.md", "LICENSE", "LICENSE.txt", ".gitattributes"]
        .into_iter()
        .collect();
    require(
        expected.is_subset(&names)
            && names
                .difference(expected)
                .all(|x| harmless.contains(x.as_str())),
        "INVALID_MODEL",
        "snapshot contains missing or unexpected files",
    )?;
    Ok(())
}

fn snapshot_files(path: &Path, snapshot: &Path, boundary: &Path) -> Result<BTreeSet<String>> {
    let mut names = BTreeSet::new();
    for entry in fs::read_dir(path)? {
        let entry = entry?;
        let child = entry.path();
        let metadata = fs::symlink_metadata(&child)?;
        within(&child, boundary)?;
        if metadata.is_dir() {
            names.extend(snapshot_files(&child, snapshot, boundary)?);
        } else {
            require(
                child.is_file(),
                "INVALID_MODEL",
                "snapshot contains a non-file asset",
            )?;
            names.insert(
                child
                    .strip_prefix(snapshot)
                    .map_err(|_| ModelError::new("INVALID_MODEL", "invalid asset path"))?
                    .to_string_lossy()
                    .replace('\\', "/"),
            );
        }
    }
    Ok(names)
}

fn hash_file(path: &Path, cancel: &Cancellation) -> Result<(u64, String)> {
    let mut file = File::open(path)?;
    let before = file.metadata()?;
    require(
        before.is_file(),
        "INVALID_MODEL",
        "asset must be a regular file",
    )?;
    let mut digest = Sha256::new();
    let mut buffer = vec![0u8; 1024 * 1024];
    let mut size = 0;
    loop {
        check_cancel(cancel)?;
        let count = file.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        digest.update(&buffer[..count]);
        size += count as u64;
    }
    require(
        size == before.len() && file.metadata()?.modified()? == before.modified()?,
        "MODEL_ASSETS_CHANGED",
        "asset changed during hashing",
    )?;
    Ok((size, format!("{:x}", digest.finalize())))
}

fn public_client() -> Result<Client> {
    Client::builder()
        .https_only(true)
        .no_proxy()
        .connect_timeout(Duration::from_secs(20))
        .timeout(Duration::from_secs(30))
        .redirect(reqwest::redirect::Policy::limited(10))
        .user_agent("LocalBrain-native-model-install/1")
        .build()
        .map_err(|e| ModelError::new("MODEL_DOWNLOAD", e.to_string()))
}

fn download_file(
    client: &Client,
    spec: ModelSpec,
    name: &str,
    repository: &Path,
    destination: &Path,
    cancel: &Cancellation,
    progress: &mut impl FnMut(InstallProgress),
) -> Result<()> {
    let blobs = repository.join("blobs");
    ensure_directory(&blobs)?;
    // This stable name is owned by this installer. Other consumers' incomplete files are untouched.
    let staging = blobs.join(format!(
        ".localbrain-{}-{}.incomplete",
        spec.revision,
        sha256(name.as_bytes())
    ));
    let _download_lock = FileLock::acquire(&blobs.join(format!(
        ".localbrain-{}-{}.lock",
        spec.revision,
        sha256(name.as_bytes())
    )))?;
    let mut file = private_file(&staging, true)?;
    let offset = file.metadata()?.len();
    let url = format!(
        "https://huggingface.co/{}/resolve/{}/{}",
        spec.id, spec.revision, name
    );
    check_cancel(cancel)?;
    let mut request = client.get(&url).header("Accept-Encoding", "identity");
    if offset > 0 {
        request = request.header(RANGE, format!("bytes={offset}-"));
    }
    let mut response = request
        .send()
        .map_err(|e| ModelError::new("MODEL_DOWNLOAD", e.to_string()))?;
    if offset > 0 && response.status() == reqwest::StatusCode::RANGE_NOT_SATISFIABLE {
        // A crash may leave a complete staging body before its final rename.
        // A server refusal must not leave that file permanently unresumable.
        check_cancel(cancel)?;
        response = client
            .get(&url)
            .header("Accept-Encoding", "identity")
            .send()
            .map_err(|e| ModelError::new("MODEL_DOWNLOAD", e.to_string()))?;
    }
    let downloaded = prepare_transfer(
        &mut file,
        offset,
        response.status().as_u16(),
        response
            .headers()
            .get(CONTENT_RANGE)
            .and_then(|x| x.to_str().ok()),
    )?;
    let etag = response
        .headers()
        .get("x-linked-etag")
        .or_else(|| response.headers().get(ETAG))
        .and_then(|x| x.to_str().ok())
        .map(|x| x.trim_matches('"').to_string());
    let total = response.content_length().map(|x| x + downloaded);
    copy_transfer(
        &mut response,
        &mut file,
        name,
        downloaded,
        total,
        cancel,
        progress,
    )?;
    drop(file);
    let (_, hash) = hash_file(&staging, cancel)?;
    if let Some(expected) = spec.pinned_hash(name) {
        if hash != expected {
            fs::remove_file(&staging)?;
            return Err(ModelError::new(
                "MODEL_ASSETS_CHANGED",
                "downloaded asset hash mismatch",
            ));
        }
    }
    // HF Git objects use 40-char ETags; LFS objects use SHA-256. Never use arbitrary header text as a path.
    let blob_name = etag
        .filter(|x| (x.len() == 40 || x.len() == 64) && x.bytes().all(|c| c.is_ascii_hexdigit()))
        .unwrap_or_else(|| hash.clone());
    if blob_name.len() == 64 {
        require(
            blob_name == hash,
            "MODEL_ASSETS_CHANGED",
            "LFS content does not match its ETag",
        )?;
    }
    let blob = blobs.join(blob_name);
    if blob.exists() || blob.is_symlink() {
        within(&blob, repository)?;
        let (_, existing_hash) = hash_file(&blob, cancel)?;
        require(
            existing_hash == hash,
            "MODEL_ASSETS_CHANGED",
            "existing shared blob differs",
        )?;
        fs::remove_file(&staging)?;
    } else {
        fs::rename(&staging, &blob)?;
    }
    if let Some(parent) = destination.parent() {
        ensure_directory(parent)?;
    }
    check_cancel(cancel)?;
    #[cfg(unix)]
    {
        let depth = destination
            .parent()
            .unwrap()
            .strip_prefix(repository)
            .unwrap()
            .components()
            .count();
        let mut relative = PathBuf::new();
        for _ in 0..depth {
            relative.push("..");
        }
        relative.push("blobs");
        relative.push(blob.file_name().unwrap());
        match symlink(relative, destination) {
            Ok(()) => {}
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => {
                within(destination, repository)?;
                require(
                    hash_file(destination, cancel)?.1 == hash,
                    "MODEL_ASSETS_CHANGED",
                    "concurrent cache update differs",
                )?;
            }
            Err(e) => return Err(e.into()),
        }
    }
    #[cfg(not(unix))]
    {
        fs::copy(&blob, destination)?;
    }
    Ok(())
}

fn prepare_transfer(
    file: &mut File,
    offset: u64,
    status: u16,
    content_range: Option<&str>,
) -> Result<u64> {
    if offset > 0 && status == 206 {
        let valid = content_range
            .and_then(|value| value.strip_prefix("bytes "))
            .and_then(|value| value.split_once('/'))
            .and_then(|(range, total)| {
                let (start, end) = range.split_once('-')?;
                let (start, end) = (start.parse::<u64>().ok()?, end.parse::<u64>().ok()?);
                let valid_total =
                    total == "*" || total.parse::<u64>().is_ok_and(|total| end < total);
                Some(start == offset && end >= start && valid_total)
            })
            .unwrap_or(false);
        require(
            valid,
            "MODEL_DOWNLOAD",
            "server returned an invalid resume range",
        )?;
        require(
            file.metadata()?.len() == offset,
            "MODEL_ASSETS_CHANGED",
            "staging size changed before resume",
        )?;
        file.seek(SeekFrom::End(0))?;
        Ok(offset)
    } else {
        require(
            status == 200,
            "MODEL_DOWNLOAD",
            "public model server refused the file",
        )?;
        file.set_len(0)?;
        file.seek(SeekFrom::Start(0))?;
        Ok(0)
    }
}

fn copy_transfer(
    body: &mut impl Read,
    file: &mut File,
    name: &str,
    mut downloaded: u64,
    total: Option<u64>,
    cancel: &Cancellation,
    progress: &mut impl FnMut(InstallProgress),
) -> Result<()> {
    let mut buffer = vec![0u8; 1024 * 1024];
    loop {
        check_cancel(cancel)?;
        let count = body
            .read(&mut buffer)
            .map_err(|e| ModelError::new("MODEL_DOWNLOAD", e.to_string()))?;
        if count == 0 {
            break;
        }
        file.write_all(&buffer[..count])?;
        downloaded += count as u64;
        progress(InstallProgress {
            phase: "downloading".into(),
            file: Some(name.into()),
            downloaded_bytes: downloaded,
            total_bytes: total,
        });
    }
    file.sync_all()?;
    require(
        total.is_none_or(|total| total == downloaded),
        "MODEL_DOWNLOAD",
        "download ended before expected size",
    )
}

fn safe_relative(value: &str) -> bool {
    !value.is_empty()
        && !value.chars().any(char::is_control)
        && Path::new(value)
            .components()
            .all(|x| matches!(x, Component::Normal(_)))
}

fn absolute_path(path: &Path) -> Result<PathBuf> {
    require(
        path.is_absolute()
            && !path.to_string_lossy().chars().any(char::is_control)
            && !path
                .components()
                .any(|x| matches!(x, Component::ParentDir | Component::CurDir)),
        "INVALID_MODEL_ROOT",
        "absolute normalized path required",
    )?;
    require(
        !path.is_symlink(),
        "INVALID_MODEL_ROOT",
        "model root cannot be a symlink",
    )?;
    let mut existing = path;
    let mut missing = Vec::new();
    while !existing.exists() {
        missing.push(
            existing
                .file_name()
                .ok_or_else(|| ModelError::new("INVALID_MODEL_ROOT", "invalid path"))?
                .to_owned(),
        );
        existing = existing
            .parent()
            .ok_or_else(|| ModelError::new("INVALID_MODEL_ROOT", "invalid parent"))?;
    }
    let mut resolved = existing.canonicalize()?;
    for name in missing.into_iter().rev() {
        resolved.push(name);
    }
    Ok(resolved)
}

fn within(path: &Path, boundary: &Path) -> Result<()> {
    let target = path.canonicalize()?;
    let root = boundary.canonicalize()?;
    require(
        target.starts_with(&root),
        "INVALID_MODEL",
        "asset escapes its model repository",
    )
}

fn ensure_directory(path: &Path) -> Result<()> {
    if path.exists() || path.is_symlink() {
        require(
            path.is_dir() && !path.is_symlink(),
            "INVALID_MODEL_ROOT",
            "directory path contains a symlink or non-directory",
        )?;
    } else {
        if let Some(parent) = path.parent() {
            ensure_directory(parent)?;
        }
        let mut builder = fs::DirBuilder::new();
        #[cfg(unix)]
        builder.mode(0o700);
        match builder.create(path) {
            Ok(()) => {}
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => {
                require(
                    path.is_dir() && !path.is_symlink(),
                    "INVALID_MODEL_ROOT",
                    "concurrent directory changed",
                )?;
            }
            Err(e) => return Err(e.into()),
        }
    }
    Ok(())
}

fn private_file(path: &Path, create: bool) -> Result<File> {
    let mut options = OpenOptions::new();
    options.read(true).write(true).create(create);
    #[cfg(unix)]
    options.mode(0o600).custom_flags(libc::O_NOFOLLOW);
    let file = options.open(path)?;
    let info = file.metadata()?;
    require(
        info.is_file(),
        "UNOWNED_MODEL",
        "owned file must be regular",
    )?;
    #[cfg(unix)]
    require(
        info.uid() == unsafe { libc::geteuid() } && info.nlink() == 1 && info.mode() & 0o077 == 0,
        "UNOWNED_MODEL",
        "owned file permissions or ownership differ",
    )?;
    Ok(file)
}

struct FileLock(File);
impl FileLock {
    fn acquire(path: &Path) -> Result<Self> {
        let file = private_file(path, true)?;
        #[cfg(unix)]
        if unsafe { libc::flock(file.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } != 0 {
            let error = std::io::Error::last_os_error();
            return Err(ModelError::new(
                if error.kind() == std::io::ErrorKind::WouldBlock {
                    "MODEL_BUSY"
                } else {
                    "MODEL_IO"
                },
                error.to_string(),
            ));
        }
        Ok(Self(file))
    }
}
impl Drop for FileLock {
    fn drop(&mut self) {
        #[cfg(unix)]
        unsafe {
            libc::flock(self.0.as_raw_fd(), libc::LOCK_UN);
        }
    }
}
struct RegistrationLock {
    _lock: FileLock,
}
impl RegistrationLock {
    fn acquire(root: &Path, spec: ModelSpec, create: bool) -> Result<Self> {
        let marker = json!({"owner": if spec.key == ModelKey::Embedding { EMBEDDING_SCHEMA } else { GENERATION_OWNER }, "model": spec.id, "revision": spec.revision});
        if !root.exists() {
            require(create, "MODEL_NOT_INSTALLED", "model registration missing")?;
            ensure_directory(root.parent().ok_or_else(|| {
                ModelError::new("INVALID_MODEL_ROOT", "registration parent missing")
            })?)?;
            let mut builder = fs::DirBuilder::new();
            #[cfg(unix)]
            builder.mode(0o700);
            builder.create(root)?;
            atomic_json(&root.join("owner.json"), &marker)?;
        }
        require(
            root.is_dir() && !root.is_symlink(),
            "UNOWNED_MODEL",
            "registration must be an owned directory",
        )?;
        #[cfg(unix)]
        {
            let info = root.metadata()?;
            require(
                info.uid() == unsafe { libc::geteuid() } && info.mode() & 0o077 == 0,
                "UNOWNED_MODEL",
                "registration permissions or ownership differ",
            )?;
        }
        require(
            read_owned_json(&root.join("owner.json"))? == marker,
            "UNOWNED_MODEL",
            "registration owner differs",
        )?;
        for entry in fs::read_dir(root)? {
            require(
                matches!(
                    entry?.file_name().to_str(),
                    Some(
                        "owner.json"
                            | "install.lock"
                            | "cache"
                            | "model.json"
                            | "model.json.pending"
                    )
                ),
                "UNOWNED_MODEL",
                "registration contains unrelated data",
            )?;
        }
        let lock = FileLock::acquire(&root.join("install.lock"))?;
        let pending = root.join("model.json.pending");
        if pending.exists() || pending.is_symlink() {
            drop(private_file(&pending, false)?);
            fs::remove_file(pending)?;
        }
        Ok(Self { _lock: lock })
    }
}

fn check_revision(root: &Path, expected: Option<&str>) -> Result<()> {
    if let Some(expected) = expected {
        require(
            registration_revision(root)? == expected,
            "MODEL_REGISTRATION_CHANGED",
            "registration was changed by another action",
        )?;
    }
    Ok(())
}

fn read_json(path: &Path) -> Result<Value> {
    require(
        path.is_file(),
        "INVALID_MODEL",
        "metadata must be a regular local file",
    )?;
    let size = path.metadata()?.len();
    require(
        size <= 32 * 1024 * 1024,
        "INVALID_MODEL",
        "metadata exceeds its bound",
    )?;
    Ok(serde_json::from_reader(File::open(path)?)?)
}

fn read_owned_json(path: &Path) -> Result<Value> {
    require(
        !path.is_symlink(),
        "INVALID_MODEL",
        "registration metadata cannot be a symlink",
    )?;
    read_json(path)
}

fn atomic_json(path: &Path, value: &Value) -> Result<()> {
    let pending = path.with_file_name(format!(
        "{}.pending",
        path.file_name().unwrap().to_string_lossy()
    ));
    let mut options = OpenOptions::new();
    options.write(true).create_new(true);
    #[cfg(unix)]
    options.mode(0o600).custom_flags(libc::O_NOFOLLOW);
    let mut file = options.open(&pending)?;
    let result = (|| -> Result<()> {
        file.write_all((serde_json::to_string_pretty(value)? + "\n").as_bytes())?;
        file.sync_all()?;
        fs::rename(&pending, path)?;
        File::open(path.parent().unwrap())?.sync_all()?;
        Ok(())
    })();
    if result.is_err() {
        let _ = fs::remove_file(pending);
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn transfer_admission_runs_under_registration_lease_before_any_network_client() {
        let directory = tempfile::tempdir().unwrap();
        let root = directory.path().join("registration");
        let mut options = InstallOptions {
            model: ModelKey::Generation4b,
            registration_root: root.clone(),
            cache_root: directory.path().join("hub"),
            offline: false,
            replace_cache: false,
            expected_registration_revision: None,
        };
        let called = std::cell::Cell::new(false);
        let cancel = crate::cancellation();
        let error = install_with_transfer_admission(
            &options,
            &cancel,
            |_| panic!("no transport progress before admission"),
            || {
                called.set(true);
                assert!(root.join("install.lock").is_file());
                assert!(root.join("owner.json").is_file());
                Err(ModelError::new("SYNTHETIC_TRANSFER_REFUSAL", "synthetic"))
            },
        )
        .unwrap_err();
        assert!(called.get());
        assert_eq!(error.code, "SYNTHETIC_TRANSFER_REFUSAL");
        assert!(!root.join("model.json").exists());
        options.offline = true;
        called.set(false);
        let error = install_with_transfer_admission(
            &options,
            &cancel,
            |_| {},
            || {
                called.set(true);
                Ok(())
            },
        )
        .unwrap_err();
        assert_eq!(error.code, "MODEL_NOT_CACHED");
        assert!(!called.get());
    }
    const FIXTURE: ModelSpec = ModelSpec {
        key: ModelKey::Embedding,
        id: "Synthetic/Test",
        revision: "0000000000000000000000000000000000000000",
        slug: "synthetic",
        purpose: "test",
        assets: &["config.json", "model.safetensors"],
        hashes: &[(
            "model.safetensors",
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )],
        aggregate: None,
    };

    #[test]
    fn hash_inventory_detects_changed_weights_and_unexpected_files() {
        let dir = tempfile::tempdir().unwrap();
        let snapshot = dir.path().join("snapshot");
        fs::create_dir(&snapshot).unwrap();
        fs::write(snapshot.join("config.json"), b"{\"model_type\":\"qwen3\"}").unwrap();
        fs::write(snapshot.join("model.safetensors"), b"abc").unwrap();
        let cancel = crate::cancellation();
        let files = inventory(&snapshot, dir.path(), FIXTURE, &cancel).unwrap();
        assert_eq!(files[1].sha256, FIXTURE.hashes[0].1);
        fs::write(snapshot.join("model.safetensors"), b"abd").unwrap();
        assert_eq!(
            inventory(&snapshot, dir.path(), FIXTURE, &cancel)
                .unwrap_err()
                .code,
            "MODEL_ASSETS_CHANGED"
        );
        fs::write(snapshot.join("model.safetensors"), b"abc").unwrap();
        fs::write(snapshot.join("private.txt"), b"synthetic").unwrap();
        assert_eq!(
            inventory(&snapshot, dir.path(), FIXTURE, &cancel)
                .unwrap_err()
                .code,
            "INVALID_MODEL"
        );
    }
    #[test]
    fn compact_digest_retains_unicode_and_sorts_recursive_keys() {
        let value = json!({"z":[{"b":1,"a":"한글"}],"a":2});
        assert_eq!(
            value_digest(&value).unwrap(),
            sha256("{\"a\":2,\"z\":[{\"a\":\"한글\",\"b\":1}]}".as_bytes())
        );
        let files = vec![FileRecord {
            path: "x".into(),
            size: 3,
            sha256: "hash".into(),
        }];
        let exact =
            "[\n  {\n    \"path\": \"x\",\n    \"sha256\": \"hash\",\n    \"size\": 3\n  }\n]\n";
        assert_eq!(
            inventory_fingerprint(&files, true).unwrap(),
            sha256(exact.as_bytes())
        );
    }
    #[cfg(unix)]
    #[test]
    fn shared_cache_links_are_confined_to_the_model_repository() {
        let dir = tempfile::tempdir().unwrap();
        let repo = dir.path().join("repo");
        let snapshot = repo.join("snapshots/rev");
        fs::create_dir_all(&snapshot).unwrap();
        fs::create_dir(repo.join("blobs")).unwrap();
        fs::write(repo.join("blobs/config"), b"{\"model_type\":\"qwen3\"}").unwrap();
        symlink("../../blobs/config", snapshot.join("config.json")).unwrap();
        fs::write(snapshot.join("model.safetensors"), b"abc").unwrap();
        assert!(inventory(&snapshot, &repo, FIXTURE, &crate::cancellation()).is_ok());
        fs::remove_file(snapshot.join("model.safetensors")).unwrap();
        fs::write(dir.path().join("outside"), b"abc").unwrap();
        symlink(
            dir.path().join("outside"),
            snapshot.join("model.safetensors"),
        )
        .unwrap();
        assert_eq!(
            inventory(&snapshot, &repo, FIXTURE, &crate::cancellation())
                .unwrap_err()
                .code,
            "INVALID_MODEL"
        );
    }
    #[test]
    fn same_registration_has_one_worker_and_optimistic_revision() {
        let dir = tempfile::tempdir().unwrap();
        let root = dir.path().join("registered");
        let lock = RegistrationLock::acquire(&root, ModelKey::Embedding.spec(), true).unwrap();
        assert_eq!(
            RegistrationLock::acquire(&root, ModelKey::Embedding.spec(), false)
                .err()
                .unwrap()
                .code,
            "MODEL_BUSY"
        );
        assert!(check_revision(&root, Some(&sha256(b""))).is_ok());
        atomic_json(&root.join("model.json"), &json!({"synthetic":true})).unwrap();
        assert_eq!(
            check_revision(&root, Some(&sha256(b""))).unwrap_err().code,
            "MODEL_REGISTRATION_CHANGED"
        );
        drop(lock);
        assert!(RegistrationLock::acquire(&root, ModelKey::Embedding.spec(), false).is_ok());
    }
    #[test]
    fn cancellation_interrupts_asset_hashing() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("synthetic");
        fs::write(&path, b"abc").unwrap();
        let cancel = crate::cancellation();
        cancel.store(true, std::sync::atomic::Ordering::Release);
        assert_eq!(
            hash_file(&path, &cancel).unwrap_err().code,
            "MODEL_CANCELLED"
        );
    }
    #[test]
    fn cancelled_transfer_resumes_without_duplicate_or_missing_bytes() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("owned.incomplete");
        let source: Vec<u8> = (0..2 * 1024 * 1024 + 13).map(|i| (i % 251) as u8).collect();
        let cancel = crate::cancellation();
        let mut file = private_file(&path, true).unwrap();
        let error = copy_transfer(
            &mut std::io::Cursor::new(&source),
            &mut file,
            "synthetic",
            0,
            Some(source.len() as u64),
            &cancel,
            &mut |_| cancel.store(true, std::sync::atomic::Ordering::Release),
        )
        .unwrap_err();
        assert_eq!(error.code, "MODEL_CANCELLED");
        let offset = file.metadata().unwrap().len();
        assert!(offset > 0 && offset < source.len() as u64);
        cancel.store(false, std::sync::atomic::Ordering::Release);
        let range = format!("bytes {offset}-{}/{}", source.len() - 1, source.len());
        let downloaded = prepare_transfer(&mut file, offset, 206, Some(&range)).unwrap();
        copy_transfer(
            &mut std::io::Cursor::new(&source[offset as usize..]),
            &mut file,
            "synthetic",
            downloaded,
            Some(source.len() as u64),
            &cancel,
            &mut |_| {},
        )
        .unwrap();
        drop(file);
        assert_eq!(fs::read(path).unwrap(), source);
    }
    #[test]
    fn resume_requires_matching_range_and_restarts_when_range_is_ignored() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("owned.incomplete");
        let mut file = private_file(&path, true).unwrap();
        file.write_all(b"partial").unwrap();
        assert_eq!(
            prepare_transfer(&mut file, 7, 206, Some("bytes 0-10/11"))
                .unwrap_err()
                .code,
            "MODEL_DOWNLOAD"
        );
        assert_eq!(file.metadata().unwrap().len(), 7);
        assert_eq!(prepare_transfer(&mut file, 7, 200, None).unwrap(), 0);
        file.write_all(b"complete").unwrap();
        drop(file);
        assert_eq!(fs::read(path).unwrap(), b"complete");
    }
    #[test]
    fn explicit_manifest_filename_never_reads_or_creates_default_registration() {
        let dir = tempfile::tempdir().unwrap();
        let custom = dir.path().join("selected-experiment.json");
        let decoy = dir.path().join("model.json");
        let cache = dir.path().join("no-cache");
        fs::write(&custom, b"{}").unwrap();
        fs::write(&decoy, b"invalid decoy JSON").unwrap();
        let error = verify_manifest(&custom, &cache, ModelKey::Embedding, &crate::cancellation())
            .unwrap_err();
        assert_eq!(
            error.detail,
            "registration does not identify the pinned model"
        );
        assert_eq!(fs::read(&custom).unwrap(), b"{}");
        assert_eq!(fs::read(&decoy).unwrap(), b"invalid decoy JSON");
        assert!(!cache.exists());
        assert!(!dir.path().join("owner.json").exists());
        assert!(!dir.path().join("install.lock").exists());
        assert_eq!(fs::read_dir(dir.path()).unwrap().count(), 2);
        assert_eq!(
            verify_manifest(
                Path::new("relative.json"),
                &cache,
                ModelKey::Embedding,
                &crate::cancellation()
            )
            .unwrap_err()
            .code,
            "INVALID_MODEL"
        );
    }
    #[test]
    fn custom_legacy_manifest_keeps_original_three_parent_anchor() {
        let dir = tempfile::tempdir().unwrap();
        let data = dir.path().join("data");
        let registration = data.join("models/custom");
        fs::create_dir_all(&registration).unwrap();
        let spec = ModelKey::Embedding.spec();
        let relative = format!("public/snapshots/{}", spec.revision);
        fs::create_dir_all(data.join(&relative)).unwrap();
        let manifest = registration.join("any-selected-name.json");
        fs::write(&manifest,serde_json::to_vec(&json!({"schema":"foundry.semantic-model/v1","model_id":spec.id,"resolved_revision":spec.revision,"fingerprint":spec.aggregate,"snapshot":relative,"files":[]})).unwrap()).unwrap();
        let error = verify_manifest(
            &manifest,
            &dir.path().join("unused"),
            ModelKey::Embedding,
            &crate::cancellation(),
        )
        .unwrap_err();
        // Reaching inventory proves selection used data/, not the custom file's
        // directory or an invented model.json. No fake weights are admitted.
        assert_eq!(
            error.detail,
            "snapshot contains missing or unexpected files"
        );
        assert!(!registration.join("model.json").exists());
        assert!(!registration.join("owner.json").exists());
    }
    #[test]
    fn sealed_grant_retains_and_revalidates_exact_selected_manifest() {
        let dir = tempfile::tempdir().unwrap();
        let snapshot = dir.path().join("snapshot");
        fs::create_dir(&snapshot).unwrap();
        fs::write(snapshot.join("config.json"), br#"{"model_type":"qwen3"}"#).unwrap();
        fs::write(snapshot.join("model.safetensors"), b"abc").unwrap();
        let selected = dir.path().join("custom-choice.json");
        let bytes = br#"{"synthetic_selection":true}"#;
        fs::write(&selected, bytes).unwrap();
        let mut verified = fixture_verified(&snapshot, &["config.json", "model.safetensors"]);
        assert!(verified.manifest_path().is_none());
        verified.selection = Some(ManifestSelection {
            path: selected.clone(),
            sha256: sha256(bytes),
        });
        let cancel = crate::cancellation();
        verified.reverify(&cancel).unwrap();
        assert_eq!(verified.manifest_path(), Some(selected.as_path()));
        fs::write(&selected, b"changed selection").unwrap();
        assert_eq!(
            verified.reverify(&cancel).unwrap_err().code,
            "MODEL_REGISTRATION_CHANGED"
        );
        assert_eq!(
            verified.reverify_tokenizer(&cancel).unwrap_err().code,
            "MODEL_REGISTRATION_CHANGED"
        );
    }
    #[cfg(unix)]
    #[test]
    fn explicit_manifest_symlinks_and_cancelled_access_are_refused() {
        let dir = tempfile::tempdir().unwrap();
        let original = dir.path().join("original.json");
        let alias = dir.path().join("alias.json");
        fs::write(&original, b"{}").unwrap();
        symlink(&original, &alias).unwrap();
        assert_eq!(
            verify_manifest(
                &alias,
                dir.path(),
                ModelKey::Embedding,
                &crate::cancellation()
            )
            .unwrap_err()
            .code,
            "INVALID_MODEL"
        );
        let cancel = crate::cancellation();
        cancel.store(true, std::sync::atomic::Ordering::Release);
        assert_eq!(
            verify_manifest(
                &dir.path().join("missing.json"),
                dir.path(),
                ModelKey::Embedding,
                &cancel
            )
            .unwrap_err()
            .code,
            "MODEL_CANCELLED"
        );
        assert_eq!(fs::read_dir(dir.path()).unwrap().count(), 2);
    }
}
