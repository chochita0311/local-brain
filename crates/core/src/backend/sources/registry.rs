use super::profiles::{default_color, valid_color, valid_source_id};
use crate::backend::{db, storage::files, Config, Result};
use rusqlite::Connection;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
};

pub const SESSION_SOURCE_SCHEMA_VERSION: i64 = 2;

pub trait PythonText {
    fn py_trim(&self) -> &str;
}
impl PythonText for str {
    fn py_trim(&self) -> &str {
        self.trim_matches(crate::backend::unicode::python_space)
    }
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Diagnostic {
    pub code: String,
    pub message: String,
    pub settings_path: String,
    pub source_id: Option<i64>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Entry {
    pub source_id: i64,
    pub display_label: String,
    pub provider_kind: String,
    pub root: PathBuf,
    pub availability: String,
    pub agent_home: Option<PathBuf>,
    pub enabled: bool,
    pub color: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SettingsResult {
    pub settings_path: PathBuf,
    pub entries: Vec<Entry>,
    pub diagnostics: Vec<Diagnostic>,
    pub declared_source_ids: Vec<i64>,
    pub bootstrapped: bool,
    pub file_error: bool,
    pub schema_version: i64,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Registration {
    pub source_id: i64,
    pub provider_kind: String,
    pub display_label: String,
    pub root: String,
    pub status: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegistryResult {
    pub settings: SettingsResult,
    pub registrations: Vec<Registration>,
    pub diagnostics: Vec<Diagnostic>,
}

pub fn session_sources_path(config: &Config) -> PathBuf {
    config
        .session_sources_path
        .clone()
        .unwrap_or_else(|| config.data_dir.join("session-sources.toml"))
}
pub fn diagnostic(path: &Path, code: &str, message: &str, source_id: Option<i64>) -> Diagnostic {
    let bounded = message
        .split(crate::backend::unicode::python_space)
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>()
        .join(" ");
    let message = if bounded.chars().count() > 360 {
        format!(
            "{}…",
            bounded.chars().take(359).collect::<String>().trim_end()
        )
    } else {
        bounded
    };
    Diagnostic {
        code: code.into(),
        message,
        settings_path: path.to_string_lossy().into_owned(),
        source_id,
    }
}
fn file_error(path: PathBuf, code: &str, message: &str, bootstrapped: bool) -> SettingsResult {
    let diagnostics = vec![diagnostic(&path, code, message, None)];
    SettingsResult {
        settings_path: path,
        entries: vec![],
        diagnostics,
        declared_source_ids: vec![],
        bootstrapped,
        file_error: true,
        schema_version: 2,
    }
}
pub fn session_sources_text(entries: &[Value]) -> Result<String> {
    // The document encoder is shared with preferences; identity/schema admission
    // stays here, and this field order remains the human-editable file contract.
    let ordered = entries
        .iter()
        .map(|entry| {
            let mut object = serde_json::Map::new();
            for key in [
                "source_id",
                "provider_kind",
                "display_label",
                "root",
                "color",
                "agent_home",
                "enabled",
            ] {
                if let Some(value) = entry.get(key) {
                    object.insert(key.into(), value.clone());
                }
            }
            if let Some(values) = entry.as_object() {
                for (key, value) in values {
                    object.insert(key.clone(), value.clone());
                }
            }
            Value::Object(object)
        })
        .collect::<Vec<_>>();
    Ok(crate::preferences::encode_toml_document(
        json!({"schema_version":2,"session_sources":ordered}),
    )?)
}
pub fn decode(text: &str) -> Result<Value> {
    Ok(crate::preferences::decode_toml_document(text)?)
}
pub(super) fn decode_for_validation(text: &str) -> Result<Value> {
    Ok(crate::preferences::decode_toml_for_validation(text)?)
}

fn bootstrap(config: &Config, path: &Path) -> Result<bool> {
    if path.exists() {
        return Ok(false);
    }
    let mut entries = Vec::new();
    if config.database_path.exists() {
        let connection = Connection::open(&config.database_path)?;
        if db::row(
            &connection,
            "SELECT 1 FROM sqlite_master WHERE name='sources'",
            [],
        )?
        .is_some()
        {
            let columns = db::rows(&connection, "PRAGMA table_info(sources)", [])?;
            let has = |name: &str| columns.iter().any(|row| row["name"] == name);
            let color = if has("profile_color") {
                "profile_color"
            } else {
                "NULL AS profile_color"
            };
            let order = if has("profile_position") {
                "profile_position,id"
            } else {
                "id"
            };
            for row in db::rows(&connection,&format!("SELECT id,name,provider_kind,root_path,{color} FROM sources WHERE provider_kind IN ('claude','codex') ORDER BY {order}"),[])? {
                entries.push(json!({"source_id":row["id"],"provider_kind":row["provider_kind"],"display_label":row["name"],"root":files::expand(Path::new(row["root_path"].as_str().unwrap_or("")),config),"color":row["profile_color"].as_str().unwrap_or_else(||default_color(row["provider_kind"].as_str().unwrap_or("")))}));
            }
        }
    }
    let text = session_sources_text(&entries)?;
    let parent = path.parent().unwrap_or(Path::new("."));
    fs::create_dir_all(parent)?;
    let mut temporary = tempfile::NamedTempFile::new_in(parent)?;
    use std::io::Write;
    use std::os::unix::fs::PermissionsExt;
    temporary
        .as_file()
        .set_permissions(fs::Permissions::from_mode(0o600))?;
    temporary.write_all(text.as_bytes())?;
    temporary.as_file().sync_all()?;
    match temporary.persist_noclobber(path) {
        Ok(_) => Ok(true),
        Err(error) if error.error.kind() == std::io::ErrorKind::AlreadyExists => Ok(false),
        Err(error) => Err(error.error.into()),
    }
}

pub fn normalized_root(path: &Path, raw: &str, config: &Config) -> Result<PathBuf> {
    let expanded = files::expand(Path::new(raw), config);
    let absolute = if expanded.is_absolute() {
        expanded
    } else {
        path.parent().unwrap_or(Path::new(".")).join(expanded)
    };
    files::lexical_absolute(&absolute)
}
pub fn readable_directory(path: &Path) -> bool {
    use std::os::unix::ffi::OsStrExt;
    path.is_dir()
        && std::ffi::CString::new(path.as_os_str().as_bytes())
            .is_ok_and(|path| unsafe { libc::access(path.as_ptr(), libc::R_OK | libc::X_OK) } == 0)
}

pub fn load_session_source_settings(config: &Config) -> Result<SettingsResult> {
    let path = session_sources_path(config);
    let bootstrapped = match bootstrap(config, &path) {
        Ok(value) => value,
        Err(error) => return Ok(file_error(path, "bootstrap_failed", &error.message, false)),
    };
    let bytes = match fs::read(&path) {
        Ok(bytes) => bytes,
        Err(error) => {
            return Ok(file_error(
                path,
                if error.kind() == std::io::ErrorKind::NotFound {
                    "settings_missing"
                } else {
                    "settings_unreadable"
                },
                &error.to_string(),
                bootstrapped,
            ))
        }
    };
    let text = match std::str::from_utf8(&bytes) {
        Ok(value) => value,
        Err(_) => {
            return Ok(file_error(
                path,
                "invalid_encoding",
                "Session source settings must be UTF-8.",
                bootstrapped,
            ))
        }
    };
    let raw = match decode_for_validation(text) {
        Ok(value) => value,
        Err(error) => {
            return Ok(file_error(
                path,
                "invalid_toml",
                &error.message,
                bootstrapped,
            ))
        }
    };
    if raw.as_object().is_none_or(|object| {
        object.len() != 2
            || !object.contains_key("schema_version")
            || !object.contains_key("session_sources")
    }) {
        return Ok(file_error(
            path,
            "invalid_schema",
            "Expected only schema_version and session_sources at the top level.",
            bootstrapped,
        ));
    }
    if raw["schema_version"].as_i64() != Some(2) {
        return Ok(file_error(
            path,
            "unsupported_schema_version",
            "Session source schema_version must be 2; older files need the startup upgrade.",
            bootstrapped,
        ));
    }
    let Some(raw_entries) = raw["session_sources"].as_array() else {
        return Ok(file_error(
            path,
            "invalid_schema",
            "session_sources must be an array of tables.",
            bootstrapped,
        ));
    };
    let declared: Vec<i64> = raw_entries
        .iter()
        .filter(|&entry| valid_source_id(&entry["source_id"]))
        .map(|entry| entry["source_id"].as_i64().unwrap())
        .collect();
    let duplicates: BTreeSet<i64> = declared
        .iter()
        .copied()
        .filter(|id| declared.iter().filter(|other| *other == id).count() > 1)
        .collect();
    if !duplicates.is_empty() {
        return Ok(file_error(
            path,
            "duplicate_source_id",
            &format!(
                "Duplicate profile identities: {}.",
                duplicates
                    .iter()
                    .map(ToString::to_string)
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            bootstrapped,
        ));
    }
    let mut diagnostics = Vec::new();
    let mut candidates = Vec::new();
    for (index, value) in raw_entries.iter().enumerate() {
        let id = value["source_id"]
            .as_i64()
            .filter(|_| valid_source_id(&value["source_id"]));
        let mut reject =
            |code: &str, message: &str| diagnostics.push(diagnostic(&path, code, message, id));
        let Some(object) = value.as_object() else {
            reject(
                "invalid_entry",
                &format!("Entry {} must be a TOML table.", index + 1),
            );
            continue;
        };
        if ["source_id", "display_label", "provider_kind", "root"]
            .iter()
            .any(|key| !object.contains_key(*key))
            || object.keys().any(|key| {
                ![
                    "source_id",
                    "display_label",
                    "provider_kind",
                    "root",
                    "agent_home",
                    "enabled",
                    "color",
                ]
                .contains(&key.as_str())
            })
        {
            reject(
                "invalid_entry_schema",
                &format!(
                    "Entry {} has missing or unsupported profile fields.",
                    index + 1
                ),
            );
            continue;
        }
        let Some(id) = id else {
            reject(
                "invalid_source_id",
                "source_id must be a positive safe integer.",
            );
            continue;
        };
        if value
            .get("color")
            .is_some_and(|value| value.as_str().is_none_or(|color| !valid_color(color)))
        {
            reject("invalid_color", "Choose a supported profile color.");
            continue;
        }
        let enabled = value.get("enabled").unwrap_or(&Value::Bool(true)).as_bool();
        let Some(enabled) = enabled else {
            reject("invalid_enabled", "enabled must be a boolean.");
            continue;
        };
        if value.get("agent_home").is_some_and(|value| {
            value
                .as_str()
                .is_none_or(|value| value.py_trim().is_empty() || value.chars().count() > 4096)
        }) {
            reject("invalid_agent_home", "agent_home must be a nonempty path.");
            continue;
        }
        let label = value["display_label"]
            .as_str()
            .filter(|value| !value.py_trim().is_empty() && value.py_trim().chars().count() <= 160);
        let Some(label) = label else {
            reject(
                "invalid_display_label",
                "display_label must contain 1 to 160 characters.",
            );
            continue;
        };
        let provider = value["provider_kind"]
            .as_str()
            .filter(|value| ["codex", "claude"].contains(value));
        let Some(provider) = provider else {
            reject(
                "unsupported_provider",
                "provider_kind must be claude or codex.",
            );
            continue;
        };
        let root = value["root"]
            .as_str()
            .filter(|value| !value.py_trim().is_empty() && value.chars().count() <= 4096);
        let Some(root) = root else {
            reject("invalid_root", "root must contain 1 to 4096 characters.");
            continue;
        };
        let root = normalized_root(&path, root.py_trim(), config)?;
        if enabled && root.exists() && !root.is_dir() {
            reject("root_not_directory", "Configured root is not a directory.");
            continue;
        }
        if enabled && root.exists() && !readable_directory(&root) {
            reject("root_unreadable", "Configured root is not readable.");
            continue;
        }
        candidates.push(Entry {
            source_id: id,
            display_label: label.py_trim().into(),
            provider_kind: provider.into(),
            availability: if root.is_dir() {
                "ready"
            } else {
                "unavailable"
            }
            .into(),
            root,
            agent_home: value["agent_home"]
                .as_str()
                .map(|value| normalized_root(&path, value, config))
                .transpose()?,
            enabled,
            color: value["color"].as_str().map(str::to_owned),
        });
    }
    let mut roots: BTreeMap<PathBuf, Vec<i64>> = BTreeMap::new();
    for entry in candidates.iter().filter(|entry| entry.enabled) {
        roots
            .entry(entry.root.clone())
            .or_default()
            .push(entry.source_id);
    }
    let mut invalid = BTreeSet::new();
    for (index, entry) in candidates.iter().enumerate() {
        let root = files::resolve(&entry.root)?;
        for other in &candidates[index + 1..] {
            let other_root = files::resolve(&other.root)?;
            if entry.enabled
                && other.enabled
                && entry.root != other.root
                && files::overlap(&root, &other_root)
            {
                for id in [entry.source_id, other.source_id] {
                    invalid.insert(id);
                    diagnostics.push(diagnostic(
                        &path,
                        "overlapping_root",
                        "Session profile folders must not overlap.",
                        Some(id),
                    ));
                }
            }
        }
    }
    for keys in roots.values().filter(|keys| keys.len() > 1) {
        for id in keys {
            invalid.insert(*id);
            diagnostics.push(diagnostic(
                &path,
                "duplicate_root",
                &format!(
                    "Configured root is also assigned to: {}.",
                    keys.iter()
                        .filter(|other| *other != id)
                        .map(ToString::to_string)
                        .collect::<Vec<_>>()
                        .join(", ")
                ),
                Some(*id),
            ));
        }
    }
    Ok(SettingsResult {
        settings_path: path,
        entries: candidates
            .into_iter()
            .filter(|entry| !invalid.contains(&entry.source_id))
            .collect(),
        diagnostics,
        declared_source_ids: declared,
        bootstrapped,
        file_error: false,
        schema_version: 2,
    })
}

pub fn reconcile_session_source_settings(
    connection: &Connection,
    result: SettingsResult,
) -> Result<RegistryResult> {
    if result.file_error {
        return Ok(RegistryResult {
            diagnostics: result.diagnostics.clone(),
            settings: result,
            registrations: vec![],
        });
    }
    let mut diagnostics = result.diagnostics.clone();
    let mut registrations = Vec::new();
    for (position, entry) in result.entries.iter().enumerate() {
        let root = entry.root.to_string_lossy();
        let color = entry
            .color
            .as_deref()
            .unwrap_or_else(|| default_color(&entry.provider_kind));
        let existing = db::row(
            connection,
            "SELECT id,provider_kind,name,root_path,profile_color FROM sources WHERE id=?",
            [entry.source_id],
        )?;
        if let Some(existing) = existing {
            let code = if existing["provider_kind"] != entry.provider_kind {
                Some((
                    "identity_conflict",
                    "The existing source ID is bound to another provider.",
                ))
            } else if existing["root_path"] != root.as_ref()
                && source_has_descendants(connection, entry.source_id)?
            {
                Some((
                    "root_change_conflict",
                    "The configured root cannot change while the source owns imported data.",
                ))
            } else {
                None
            };
            if let Some((code, message)) = code {
                diagnostics.push(diagnostic(
                    &result.settings_path,
                    code,
                    message,
                    Some(entry.source_id),
                ));
                registrations.push(Registration {
                    source_id: entry.source_id,
                    provider_kind: existing["provider_kind"].as_str().unwrap_or("").into(),
                    display_label: existing["name"].as_str().unwrap_or("").into(),
                    root: existing["root_path"].as_str().unwrap_or("").into(),
                    status: code.into(),
                });
                continue;
            }
            connection.execute("UPDATE sources SET name=?,root_path=?,profile_color=?,profile_position=? WHERE id=?",rusqlite::params![entry.display_label,root,color,position,entry.source_id])?;
        } else {
            connection.execute("INSERT INTO sources(id,provider_kind,name,root_path,profile_color,profile_position) VALUES (?,?,?,?,?,?)",rusqlite::params![entry.source_id,entry.provider_kind,entry.display_label,root,color,position])?;
        }
        registrations.push(Registration {
            source_id: entry.source_id,
            provider_kind: entry.provider_kind.clone(),
            display_label: entry.display_label.clone(),
            root: root.into_owned(),
            status: entry.availability.clone(),
        });
    }
    for existing in db::rows(connection,"SELECT id,provider_kind,name,root_path FROM sources WHERE provider_kind IN ('claude','codex') ORDER BY id",[])?{let id=existing["id"].as_i64().unwrap();if result.declared_source_ids.contains(&id)||registrations.iter().any(|item|item.source_id==id){continue;}connection.execute("UPDATE sources SET profile_position=2147483647 WHERE id=?",[id])?;diagnostics.push(diagnostic(&result.settings_path,"config_missing","The retained source is omitted from the settings file; its data was preserved.",Some(id)));registrations.push(Registration{source_id:id,provider_kind:existing["provider_kind"].as_str().unwrap_or("").into(),display_label:existing["name"].as_str().unwrap_or("").into(),root:existing["root_path"].as_str().unwrap_or("").into(),status:"config_missing".into()});}
    Ok(RegistryResult {
        settings: result,
        registrations,
        diagnostics,
    })
}
fn source_has_descendants(connection: &Connection, id: i64) -> Result<bool> {
    for table in [
        "source_files",
        "sessions",
        "usage_records",
        "context_documents",
    ] {
        if db::row(
            connection,
            &format!("SELECT 1 FROM {table} WHERE source_id=? LIMIT 1"),
            [id],
        )?
        .is_some()
        {
            return Ok(true);
        }
    }
    Ok(false)
}
pub fn load_and_reconcile_session_sources(
    connection: &Connection,
    config: &Config,
) -> Result<RegistryResult> {
    reconcile_session_source_settings(connection, load_session_source_settings(config)?)
}
pub fn registered_session_roots(config: &Config) -> Result<BTreeMap<i64, String>> {
    let result = load_session_source_settings(config)?;
    Ok(result
        .entries
        .into_iter()
        .filter(|entry| entry.enabled && entry.availability == "ready")
        .map(|entry| (entry.source_id, entry.root.to_string_lossy().into_owned()))
        .collect())
}
