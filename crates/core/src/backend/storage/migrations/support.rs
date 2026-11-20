use crate::backend::{db, storage::files, BackendError, Config, Result};
use rusqlite::{types::Value, Connection, OptionalExtension};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    os::unix::fs::PermissionsExt,
    path::Path,
};
pub fn fail(message: &str) -> BackendError {
    BackendError::conflict(message)
}
pub fn quote(value: &str) -> String {
    format!("\"{}\"", value.replace('"', "\"\""))
}
pub fn sql(connection: &Connection, table: &str) -> Result<Option<String>> {
    Ok(connection
        .query_row(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            [table],
            |row| row.get(0),
        )
        .optional()?)
}
pub fn exists(connection: &Connection, table: &str) -> Result<bool> {
    Ok(sql(connection, table)?.is_some())
}
pub fn values(connection: &Connection, query: &str) -> Result<Vec<Vec<Value>>> {
    let mut statement = connection.prepare(query)?;
    let count = statement.column_count();
    let mut cursor = statement.query([])?;
    let mut result = Vec::new();
    while let Some(row) = cursor.next()? {
        result.push(
            (0..count)
                .map(|index| row.get(index))
                .collect::<rusqlite::Result<_>>()?,
        );
    }
    Ok(result)
}
pub fn info(connection: &Connection, table: &str) -> Result<Vec<Vec<Value>>> {
    values(connection, &format!("PRAGMA table_info({})", quote(table)))
}
pub fn text(value: &Value) -> &str {
    match value {
        Value::Text(value) => value,
        _ => "",
    }
}
pub fn int(value: &Value) -> i64 {
    match value {
        Value::Integer(value) => *value,
        _ => 0,
    }
}
pub fn columns(connection: &Connection, table: &str) -> Result<Vec<String>> {
    Ok(info(connection, table)?
        .iter()
        .map(|row| text(&row[1]).into())
        .collect())
}
pub fn column_set(connection: &Connection, table: &str) -> Result<BTreeSet<String>> {
    Ok(columns(connection, table)?.into_iter().collect())
}
pub fn contract(connection: &Connection, table: &str) -> Result<BTreeMap<String, Vec<Value>>> {
    Ok(info(connection, table)?
        .into_iter()
        .map(|row| (text(&row[1]).to_owned(), row[2..].to_vec()))
        .collect())
}
pub fn has(connection: &Connection, table: &str, column: &str) -> Result<bool> {
    Ok(columns(connection, table)?
        .iter()
        .any(|name| name == column))
}
pub fn ensure(
    connection: &Connection,
    table: &str,
    column: &str,
    definition: &str,
) -> Result<bool> {
    if has(connection, table, column)? {
        return Ok(false);
    }
    connection.execute_batch(&format!(
        "ALTER TABLE {} ADD COLUMN {} {}",
        quote(table),
        quote(column),
        definition
    ))?;
    Ok(true)
}
pub fn drop_column(connection: &Connection, table: &str, column: &str) -> Result<bool> {
    if !has(connection, table, column)? {
        return Ok(false);
    }
    connection.execute_batch(&format!(
        "ALTER TABLE {} DROP COLUMN {}",
        quote(table),
        quote(column)
    ))?;
    Ok(true)
}
pub fn canonical() -> Result<Connection> {
    let connection = Connection::open_in_memory()?;
    connection.execute_batch(db::SCHEMA)?;
    Ok(connection)
}
pub fn ddl(table: &str) -> Result<String> {
    let prefix = format!("CREATE TABLE IF NOT EXISTS {table} (");
    let start = db::SCHEMA
        .find(&prefix)
        .ok_or_else(|| fail(&format!("Missing schema contract: {table}")))?;
    let end = db::SCHEMA[start..]
        .find("\n);")
        .ok_or_else(|| fail("Incomplete canonical table contract"))?;
    Ok(db::SCHEMA[start..start + end + 3].into())
}
pub fn objects(connection: &Connection, kind: &str, table: &str) -> Result<Vec<String>> {
    Ok(db::rows(connection,"SELECT sql FROM sqlite_master WHERE type=? AND tbl_name=? AND sql IS NOT NULL ORDER BY name",[kind,table])?.iter().filter_map(|row|row["sql"].as_str().map(str::to_owned)).collect())
}
pub fn triggers_absent(connection: &Connection, table: &str, message: &str) -> Result<()> {
    if !objects(connection, "trigger", table)?.is_empty() {
        return Err(fail(message));
    }
    Ok(())
}
pub fn unique_columns(connection: &Connection, table: &str) -> Result<Vec<Vec<String>>> {
    let mut result = Vec::new();
    for index in db::rows(
        connection,
        &format!("PRAGMA index_list({})", quote(table)),
        [],
    )? {
        if index["unique"].as_i64().unwrap_or(0) != 0 {
            result.push(
                db::rows(
                    connection,
                    &format!(
                        "PRAGMA index_info({})",
                        quote(index["name"].as_str().unwrap_or(""))
                    ),
                    [],
                )?
                .iter()
                .filter_map(|column| column["name"].as_str().map(str::to_owned))
                .collect(),
            );
        }
    }
    Ok(result)
}
pub fn quick_check(connection: &Connection) -> Result<()> {
    if values(connection, "PRAGMA quick_check")? != vec![vec![Value::Text("ok".into())]] {
        return Err(fail("Schema migration backup failed quick_check"));
    }
    Ok(())
}
pub fn foreign_check(connection: &Connection, table: Option<&str>) -> Result<()> {
    let query = table.map_or_else(
        || "PRAGMA foreign_key_check".into(),
        |table| format!("PRAGMA foreign_key_check({})", quote(table)),
    );
    if !values(connection, &query)?.is_empty() {
        return Err(fail("Schema migration foreign key check failed"));
    }
    Ok(())
}
pub fn backup(connection: &Connection, config: &Config, suffix: &str) -> Result<()> {
    let path = Path::new(&format!("{}{suffix}", config.database_path.display())).to_owned();
    if fs::symlink_metadata(&path).is_ok() {
        files::owned_file(&path)?;
        return quick_check(&Connection::open(&path)?);
    }
    files::private_database(&path, config)?;
    let outcome = (|| {
        let mut target = Connection::open(&path)?;
        let backup = rusqlite::backup::Backup::new(connection, &mut target)?;
        backup.run_to_completion(128, std::time::Duration::from_millis(10), None)?;
        drop(backup);
        target.close().map_err(|(_, error)| error)?;
        fs::set_permissions(&path, fs::Permissions::from_mode(0o600))?;
        quick_check(&Connection::open(&path)?)
    })();
    if outcome.is_err() {
        let _ = fs::remove_file(&path);
    }
    outcome
}
pub fn savepoint<T>(
    connection: &Connection,
    name: &str,
    body: impl FnOnce() -> Result<T>,
) -> Result<T> {
    connection.execute_batch(&format!("SAVEPOINT {name}"))?;
    match body() {
        Ok(value) => {
            connection.execute_batch(&format!("RELEASE {name}"))?;
            Ok(value)
        }
        Err(error) => {
            let _ = connection.execute_batch(&format!("ROLLBACK TO {name}; RELEASE {name}"));
            Err(error)
        }
    }
}

/// Rebuild while all incoming identities remain fixed. The legacy ALTER mode
/// preserves child FK targets; snapshots and the FK check validate publication.
pub fn rebuild(
    connection: &Connection,
    table: &str,
    legacy: &str,
    definition: &str,
    retained: &[String],
    keep_indexes: bool,
) -> Result<()> {
    triggers_absent(
        connection,
        table,
        "Schema migration found an unexpected trigger",
    )?;
    if exists(connection, legacy)? {
        return Err(fail("Schema migration target already exists"));
    }
    let columns = retained
        .iter()
        .map(|value| quote(value))
        .collect::<Vec<_>>()
        .join(",");
    let before = values(
        connection,
        &format!("SELECT {columns} FROM {} ORDER BY id", quote(table)),
    )?;
    let indexes = if keep_indexes {
        objects(connection, "index", table)?
    } else {
        vec![]
    };
    let foreign: i64 = connection.query_row("PRAGMA foreign_keys", [], |row| row.get(0))?;
    if !connection.is_autocommit() {
        connection.execute_batch("COMMIT")?;
    }
    connection
        .execute_batch("PRAGMA foreign_keys=OFF; PRAGMA legacy_alter_table=ON; BEGIN IMMEDIATE")?;
    let result = (|| {
        connection.execute_batch(&format!(
            "ALTER TABLE {} RENAME TO {}",
            quote(table),
            quote(legacy)
        ))?;
        connection.execute_batch(definition)?;
        connection.execute_batch(&format!(
            "INSERT INTO {} ({columns}) SELECT {columns} FROM {}",
            quote(table),
            quote(legacy)
        ))?;
        if values(
            connection,
            &format!("SELECT {columns} FROM {} ORDER BY id", quote(table)),
        )? != before
        {
            return Err(fail("Schema migration changed retained rows"));
        }
        connection.execute_batch(&format!("DROP TABLE {}", quote(legacy)))?;
        for index in indexes {
            connection.execute_batch(&index)?;
        }
        foreign_check(connection, None)?;
        connection.execute_batch("COMMIT")?;
        Ok(())
    })();
    if result.is_err() {
        let _ = connection.execute_batch("ROLLBACK");
    }
    connection.execute_batch(&format!(
        "PRAGMA legacy_alter_table=OFF; PRAGMA foreign_keys={}",
        if foreign != 0 { "ON" } else { "OFF" }
    ))?;
    result
}
