use crate::state::database;
use chrono::{NaiveDate, Utc};
use localbrain_core::backend::{
    clock, preferences,
    storage::files,
    usage::{usage_dashboard_data, UsageOptions},
    Config, Result,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{fs, os::unix::fs::MetadataExt, path::Path, sync::Mutex, time::SystemTime};

const CACHE_FILE: &str = "sessions-dashboard.json";
const CACHE_VERSION: u32 = 1;
const CACHE_LIMIT: u64 = 4 * 1024 * 1024;

#[derive(Serialize, Deserialize, PartialEq, Eq)]
struct FileRevision {
    device: u64,
    inode: u64,
    created: Option<SystemTime>,
    len: u64,
    modified: (i64, i64),
}

impl FileRevision {
    fn read(path: &Path) -> std::io::Result<Self> {
        let file = fs::metadata(path)?;
        Ok(Self {
            device: file.dev(),
            inode: file.ino(),
            created: file.created().ok(),
            len: file.len(),
            modified: (file.mtime(), file.mtime_nsec()),
        })
    }

    fn same_file(&self, other: &Self) -> bool {
        (self.device, self.inode, self.created) == (other.device, other.inode, other.created)
    }
}

#[derive(Serialize, Deserialize, PartialEq, Eq)]
struct DatabaseRevision {
    main: FileRevision,
    wal: Option<FileRevision>,
}

impl DatabaseRevision {
    fn read(path: &Path) -> Result<Self> {
        let mut wal = path.as_os_str().to_owned();
        wal.push("-wal");
        Ok(Self {
            main: FileRevision::read(path)?,
            wal: match FileRevision::read(Path::new(&wal)) {
                Ok(file) => Some(file),
                Err(error) if error.kind() == std::io::ErrorKind::NotFound => None,
                Err(error) => return Err(error.into()),
            },
        })
    }
}

#[derive(Serialize, Deserialize)]
struct Snapshot {
    version: u32,
    timezone: String,
    day: NaiveDate,
    database: DatabaseRevision,
    stable: bool,
    usage: Value,
}

impl Snapshot {
    fn load(
        config: &Config,
        timezone: &str,
        day: NaiveDate,
        database: &DatabaseRevision,
    ) -> Option<Self> {
        let directory = files::validate_runtime_directory(&config.cache_dir, config).ok()?;
        let value = files::read_owned_json(&directory.join(CACHE_FILE), CACHE_LIMIT).ok()?;
        let snapshot: Self = serde_json::from_value(value).ok()?;
        (snapshot.version == CACHE_VERSION
            && snapshot.timezone == timezone
            && snapshot.day == day
            && snapshot.database.main.same_file(&database.main)
            && snapshot.usage["scope"].is_object()
            && snapshot.usage["controls"].is_object()
            && snapshot.usage["summary"].is_array()
            && snapshot.usage["history"].is_array()
            && snapshot.usage["breakdown"].is_object())
        .then_some(snapshot)
    }

    fn is_current(&self, database: &DatabaseRevision) -> bool {
        self.stable && self.database == *database
    }

    fn save(&self, config: &Config) -> Result<()> {
        let encoded = serde_json::to_vec(self)?;
        if encoded.len() as u64 <= CACHE_LIMIT {
            let directory = files::private_directory(&config.cache_dir, config)?;
            let path = directory.join(CACHE_FILE);
            match fs::symlink_metadata(&path) {
                Ok(_) => {
                    files::owned_file(&path)?;
                }
                Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
                Err(error) => return Err(error.into()),
            }
            files::atomic_write(&path, &encoded)?;
        }
        Ok(())
    }
}

#[derive(Default)]
pub(crate) struct UsageDashboardCache {
    writer: Mutex<()>,
}

impl UsageDashboardCache {
    pub(crate) fn is_default(options: &UsageOptions) -> bool {
        options.view == "daily"
            && options.source == "all"
            && options.metric == "cost"
            && options.breakdown == "source"
            && options.from_value.as_deref().unwrap_or_default().is_empty()
            && options.to_value.as_deref().unwrap_or_default().is_empty()
    }

    pub(crate) fn preview(
        config: &Config,
        options: &UsageOptions,
    ) -> Result<Option<(Value, bool)>> {
        let day = clock::local_day(Utc::now(), &options.timezone_name)?;
        let revision = DatabaseRevision::read(&config.database_path)?;
        Ok(
            Snapshot::load(config, &options.timezone_name, day, &revision).map(|snapshot| {
                let needs_refresh = !snapshot.is_current(&revision);
                (snapshot.usage, needs_refresh)
            }),
        )
    }

    pub(crate) fn refresh(&self, config: &Config, mut options: UsageOptions) -> Result<Value> {
        let _writer = self
            .writer
            .lock()
            .unwrap_or_else(|error| error.into_inner());
        let day = clock::local_day(Utc::now(), &options.timezone_name)?;
        let revision = DatabaseRevision::read(&config.database_path)?;
        if let Some(snapshot) = Snapshot::load(config, &options.timezone_name, day, &revision) {
            if snapshot.is_current(&revision) {
                return Ok(snapshot.usage);
            }
        }
        options.today = Some(day);
        let usage = database(config, false, |connection| {
            let transaction = connection.unchecked_transaction()?;
            let usage = usage_dashboard_data(&transaction, &options)?;
            transaction.commit()?;
            Ok(usage)
        })?;
        if let Ok(after) = DatabaseRevision::read(&config.database_path) {
            if revision.main.same_file(&after.main) {
                // A write during the read leaves a usable summary that will
                // be refreshed again on the next access.
                let snapshot = Snapshot {
                    version: CACHE_VERSION,
                    timezone: options.timezone_name,
                    day,
                    stable: revision == after,
                    database: revision,
                    usage,
                };
                let _ = snapshot.save(config);
                return Ok(snapshot.usage);
            }
        }
        Ok(usage)
    }

    pub(crate) fn refresh_after_sync(&self, config: &Config) -> Result<()> {
        let preferences = preferences::effective_preferences(config)?;
        self.refresh(
            config,
            UsageOptions {
                timezone_name: preferences["timezone"]
                    .as_str()
                    .unwrap_or(&config.timezone_name)
                    .into(),
                visible_only: true,
                ..UsageOptions::default()
            },
        )?;
        Ok(())
    }
}
