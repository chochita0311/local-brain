use super::{
    arguments::{invalid, Arguments},
    CommandResult,
};
use localbrain_core::backend::{auto_work, storage, Config, Result};
use rusqlite::{Connection, OpenFlags};
use serde_json::json;
pub fn run(config: &Config, raw: &[String]) -> CommandResult {
    let args = Arguments::parse(raw, &["--apply", "--include-development"], &[])?;
    args.count(1, 1)?;
    match args.positional(0)? {
        "status" => {
            if args.flag("--apply") || args.flag("--include-development") {
                return Err(invalid("unrecognized status option"));
            }
            super::print(&storage::storage_status(config)?);
            Ok(0)
        }
        "migrate" => {
            let owners = config
                .feature("auto_work")
                .then(auto_work::cache::legacy_cache_owners);
            match storage::migrate_storage(
                config,
                args.flag("--apply"),
                args.flag("--include-development"),
                owners.as_ref(),
            ) {
                Ok(value) => {
                    super::print(&value);
                    Ok(0)
                }
                Err(error) => {
                    println!(
                        "{}",
                        if error.code.starts_with("STORAGE_") {
                            error.code.as_str()
                        } else {
                            "STORAGE_MIGRATION_FAILED"
                        }
                    );
                    Ok(2)
                }
            }
        }
        "cleanup" => {
            if args.flag("--include-development") {
                return Err(invalid("unrecognized cleanup option"));
            }
            let database =
                storage::files::resolve(&storage::files::expand(&config.database_path, config))?;
            let mut group = vec![];
            for path in [
                database.clone(),
                database.with_file_name(format!(
                    "{}-wal",
                    database.file_name().unwrap_or_default().to_string_lossy()
                )),
                database.with_file_name(format!(
                    "{}-shm",
                    database.file_name().unwrap_or_default().to_string_lossy()
                )),
            ] {
                if path.exists() {
                    group.push(path);
                }
            }
            if !database.is_file()
                || !storage::files::inactive_files(&group)
                || group.iter().any(|path| {
                    path.file_name()
                        .unwrap_or_default()
                        .to_string_lossy()
                        .ends_with("-wal")
                        && path.metadata().is_ok_and(|info| info.len() > 0)
                })
            {
                println!("DATABASE_UNAVAILABLE_OR_BUSY");
                return Ok(2);
            }
            let result = (|| -> Result<_> {
                let mut uri = url::Url::from_file_path(&database)
                    .map_err(|_| invalid("invalid database path"))?;
                uri.set_query(Some("mode=ro&immutable=1"));
                let connection = Connection::open_with_flags(
                    uri.as_str(),
                    OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_URI,
                )?;
                let mut result = json!({"migration_backups":storage::maintain_migration_backups(&database,&connection,args.flag("--apply"),None)?});
                drop(connection);
                if config.feature("auto_work") {
                    result["derived_cache"] = auto_work::cache::maintain_cache(
                        config,
                        &config.cache_dir,
                        args.flag("--apply"),
                        None,
                    )?;
                }
                Ok(result)
            })();
            match result {
                Ok(value) => {
                    super::print(&value);
                    Ok(0)
                }
                Err(_) => {
                    println!("STORAGE_CLEANUP_FAILED");
                    Ok(2)
                }
            }
        }
        _ => Err(invalid("invalid storage command")),
    }
}
