use super::{BackendError, Result};
use std::{
    collections::BTreeSet,
    env,
    path::{Path, PathBuf},
};

#[derive(Debug, Clone)]
pub struct Config {
    pub home_dir: PathBuf,
    pub data_dir: PathBuf,
    pub database_path: PathBuf,
    pub session_sources_path: Option<PathBuf>,
    pub cache_dir: PathBuf,
    pub development_dir: PathBuf,
    pub context_root: PathBuf,
    pub claude_root: PathBuf,
    pub codex_root: PathBuf,
    pub claude_bin: Option<PathBuf>,
    pub codex_bin: Option<PathBuf>,
    pub gcloud_path: Option<PathBuf>,
    pub web_root: PathBuf,
    pub installation_root: Option<PathBuf>,
    pub hf_home: PathBuf,
    pub hf_hub_cache: PathBuf,
    pub mcp_call_budget: serde_json::Number,
    pub timezone_name: String,
    pub desktop: bool,
    pub feature_packages: BTreeSet<String>,
}

fn configured(name: &str, fallback: PathBuf, home: &Path) -> Result<PathBuf> {
    let value = env::var_os(name).map(PathBuf::from).unwrap_or(fallback);
    let Some(text) = value.to_str() else {
        return Ok(value);
    };
    let Some(tail) = text.strip_prefix('~') else {
        return Ok(value);
    };
    let (user, rest) = tail.split_once('/').unwrap_or((tail, ""));
    let base = if user.is_empty() {
        home.to_owned()
    } else {
        let Some((directory, _)) = crate::settings::account(Some(user)) else {
            return Err(BackendError::invalid(
                "config",
                format!("Cannot resolve home directory in {name}"),
            ));
        };
        PathBuf::from(directory)
    };
    Ok(base.join(rest.trim_start_matches('/')))
}
fn call_budget(raw: Option<&str>) -> serde_json::Number {
    let Some(number) = raw.and_then(super::unicode::integer_literal) else {
        return 20.into();
    };
    if number.starts_with('-') {
        return 0.into();
    }
    // Preserve Python's integer width. SQLite conversion is checked when a Run
    // is persisted, so configuration/read paths never clamp a user's budget.
    serde_json::Number::from_string_unchecked(number)
}

impl Config {
    pub fn from_env() -> Result<Self> {
        let home = env::var_os("HOME")
            .map(PathBuf::from)
            .or_else(|| crate::settings::account(None).map(|account| PathBuf::from(account.0)))
            .ok_or_else(|| {
                BackendError::invalid(
                    "config",
                    "Cannot resolve the process account home directory",
                )
            })?;
        let default_data = home.join("Library/Application Support/LocalBrain");
        let data = configured("LOCALBRAIN_DATA_DIR", default_data.clone(), &home)?;
        let mut result = Self::for_data_dir(&data);
        result.home_dir = home.clone();
        result.session_sources_path = Some(data.join("session-sources.toml"));
        result.cache_dir = configured(
            "LOCALBRAIN_CACHE_DIR",
            if data == default_data {
                home.join("Library/Caches/LocalBrain")
            } else {
                sibling(&data, "-cache")
            },
            &home,
        )?;
        result.development_dir = configured(
            "LOCALBRAIN_DEVELOPMENT_DIR",
            if data == default_data {
                home.join("Library/Application Support/LocalBrain-Development")
            } else {
                sibling(&data, "-development")
            },
            &home,
        )?;
        result.context_root = configured(
            "LOCALBRAIN_CONTEXT_ROOT",
            home.join("Projects/context"),
            &home,
        )?;
        result.claude_root = configured(
            "LOCALBRAIN_CLAUDE_ROOT",
            home.join(".claude/projects"),
            &home,
        )?;
        result.codex_root =
            configured("LOCALBRAIN_CODEX_ROOT", home.join(".codex/sessions"), &home)?;
        result.claude_bin = env::var_os("LOCALBRAIN_CLAUDE_BIN")
            .filter(|value| !value.is_empty())
            .map(PathBuf::from);
        result.codex_bin = env::var_os("LOCALBRAIN_CODEX_BIN")
            .filter(|value| !value.is_empty())
            .map(PathBuf::from);
        result.gcloud_path = env::var_os("LOCALBRAIN_GCLOUD_PATH")
            .filter(|value| !value.is_empty())
            .map(PathBuf::from);
        result.hf_home = configured(
            "HF_HOME",
            configured("XDG_CACHE_HOME", home.join(".cache"), &home)?.join("huggingface"),
            &home,
        )?;
        result.hf_hub_cache = configured(
            "HF_HUB_CACHE",
            configured("HUGGINGFACE_HUB_CACHE", result.hf_home.join("hub"), &home)?,
            &home,
        )?;
        result.mcp_call_budget =
            call_budget(env::var("LOCALBRAIN_MCP_CALL_BUDGET").ok().as_deref());
        result.timezone_name = system_timezone();
        result.desktop = env::var("LOCALBRAIN_EDITION").as_deref() == Ok("desktop");
        result.feature_packages = default_features(result.desktop);
        result.web_root = discover_web_root();
        result.installation_root = installation_boundary(&result.web_root);
        Ok(result)
    }

    pub fn for_data_dir(path: impl Into<PathBuf>) -> Self {
        let data = path.into();
        let parent = data.parent().unwrap_or(Path::new("."));
        Self {
            home_dir: parent.join("home"),
            database_path: data.join("localbrain.db"),
            session_sources_path: None,
            cache_dir: sibling(&data, "-cache"),
            development_dir: sibling(&data, "-development"),
            context_root: parent.join("context"),
            claude_root: parent.join("claude"),
            codex_root: parent.join("codex"),
            claude_bin: None,
            codex_bin: None,
            gcloud_path: None,
            web_root: discover_web_root(),
            installation_root: None,
            hf_home: parent.join("hub-home"),
            hf_hub_cache: parent.join("hub-home/hub"),
            data_dir: data,
            mcp_call_budget: 20.into(),
            timezone_name: "UTC".into(),
            desktop: false,
            feature_packages: default_features(false),
        }
    }

    pub fn with_features(mut self, selected: impl IntoIterator<Item = String>) -> Result<Self> {
        let known = [
            "atlassian",
            "workstreams",
            "workflow",
            "auto_work",
            "context_search",
            "google_drive",
            "terminal",
        ];
        let selected: BTreeSet<String> = selected.into_iter().collect();
        if selected.iter().any(|v| !known.contains(&v.as_str())) {
            return Err(BackendError::invalid(
                "feature",
                "Unknown application feature package",
            ));
        }
        self.feature_packages = selected
            .into_iter()
            .filter(|v| {
                (!self.desktop || v == "terminal") && (cfg!(target_os = "macos") || v != "terminal")
            })
            .collect();
        Ok(self)
    }

    pub fn feature(&self, name: &str) -> bool {
        self.feature_packages.contains(name)
    }
    pub fn terminal_context(&self) -> crate::Context {
        crate::Context {
            data_dir: self.data_dir.clone(),
            cache_dir: self.cache_dir.clone(),
            home_dir: self.home_dir.clone(),
        }
    }
}

fn sibling(path: &Path, suffix: &str) -> PathBuf {
    path.with_file_name(format!(
        "{}{suffix}",
        path.file_name().unwrap_or_default().to_string_lossy()
    ))
}
fn default_features(desktop: bool) -> BTreeSet<String> {
    [
        "atlassian",
        "workstreams",
        "workflow",
        "auto_work",
        "terminal",
    ]
    .into_iter()
    .filter(|name| {
        (!desktop || *name == "terminal") && (cfg!(target_os = "macos") || *name != "terminal")
    })
    .map(str::to_owned)
    .collect()
}
fn system_timezone() -> String {
    std::fs::canonicalize("/etc/localtime")
        .ok()
        .and_then(|p| {
            p.to_str()
                .and_then(|s| s.split_once("/zoneinfo/").map(|(_, v)| v.to_owned()))
        })
        .unwrap_or_else(|| "UTC".into())
}
fn discover_web_root() -> PathBuf {
    if let Some(path) = env::var_os("LOCALBRAIN_WEB_ROOT") {
        return PathBuf::from(path);
    }
    if let Ok(executable) = env::current_exe() {
        if let Some(parent) = executable.parent() {
            for relative in ["../web", "../share/localbrain/web", "web"] {
                let path = parent.join(relative);
                if path.join("templates/base.html").is_file() {
                    return path;
                }
            }
        }
        if let Some(source) = executable.ancestors().find(|root| {
            root.join("Cargo.toml").is_file()
                && root.join("crates").is_dir()
                && root.join("apps/web/templates/base.html").is_file()
                && executable.starts_with(root.join("target"))
        }) {
            return source.join("apps/web");
        }
    }
    PathBuf::from("apps/web")
}

fn installation_boundary(web_root: &Path) -> Option<PathBuf> {
    if let Ok(executable) = env::current_exe().and_then(std::fs::canonicalize) {
        if let Some(app) = executable
            .ancestors()
            .find(|p| p.extension().is_some_and(|s| s == "app"))
        {
            return Some(app.to_owned());
        }
        if let Some(bin) = executable
            .parent()
            .filter(|p| p.file_name().is_some_and(|name| name == "bin"))
        {
            if let Some(bundle) = bin
                .parent()
                .filter(|p| p.join("web/templates/base.html").is_file())
            {
                return Some(bundle.to_owned());
            }
        }
        if let Some(source) = executable.ancestors().find(|p| {
            p.join("Cargo.toml").is_file()
                && p.join("crates").is_dir()
                && p.join("apps/web").is_dir()
        }) {
            return Some(source.to_owned());
        }
    }
    let web = std::fs::canonicalize(web_root).ok()?;
    if let Some(source) = web.ancestors().find(|p| {
        p.join("Cargo.toml").is_file() && p.join("crates").is_dir() && p.join("apps/web").is_dir()
    }) {
        return Some(source.to_owned());
    }
    if web.ends_with("share/localbrain/web") {
        return web.ancestors().nth(3).map(Path::to_owned);
    }
    Some(web)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn mcp_budget_preserves_python_integer_width_and_input_grammar() {
        for (raw, expected) in [
            (None, "20"),
            (Some("  +4_294_967_296 "), "4294967296"),
            (Some("١٢_٣"), "123"),
            (Some("-999999999999999999999999999999999999"), "0"),
            (Some("1__0"), "20"),
            (Some("²"), "20"),
            (Some("+_2"), "20"),
        ] {
            assert_eq!(call_budget(raw).to_string(), expected, "{raw:?}");
        }
        let large = "9".repeat(100);
        assert_eq!(call_budget(Some(&large)).to_string(), large);
        assert_eq!(call_budget(Some(&"9".repeat(4301))).to_string(), "20");
    }
}
