//! SQLite entry points. Initialization upgrades named contracts in place.
use super::{storage, BackendError, Config, Result};
use rusqlite::{types::ValueRef, Connection, Params};
use serde_json::{Map, Value};

pub const SCHEMA: &str = include_str!("../../resources/schema.sql");

pub fn connect(config: &Config) -> Result<Connection> {
    storage::files::private_database(&config.database_path, config)?;
    let connection = Connection::open(&config.database_path)?;
    connection.busy_timeout(std::time::Duration::from_secs(30))?;
    connection.pragma_update(None, "foreign_keys", "ON")?;
    Ok(connection)
}

pub fn initialize(config: &Config) -> Result<()> {
    let connection = connect(config)?;
    storage::migrations::initialize(&connection, config)
}

/// Build tools inspect the actual effective schema through a fresh synthetic
/// database. They never import a retired backend or open application data.
pub fn effective_schema_sql() -> Result<Vec<String>> {
    let temporary = tempfile::Builder::new()
        .prefix("localbrain-schema-")
        .tempdir()?;
    let config = Config::for_data_dir(temporary.path().join("data"));
    initialize(&config)?;
    let connection = connect(&config)?;
    let mut statement=connection.prepare("SELECT sql FROM sqlite_schema WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' AND name NOT IN (SELECT name FROM pragma_table_list WHERE type='shadow') ORDER BY CASE type WHEN 'table' THEN 0 WHEN 'index' THEN 1 WHEN 'view' THEN 2 ELSE 3 END,rowid")?;
    let result = statement
        .query_map([], |row| row.get::<_, String>(0))?
        .collect::<std::result::Result<Vec<_>, _>>()?;
    Ok(result)
}

pub fn rows<P: Params>(connection: &Connection, sql: &str, params: P) -> Result<Vec<Value>> {
    let mut result = Vec::new();
    scan(connection, sql, params, |row| {
        result.push(row);
        Ok(true)
    })?;
    Ok(result)
}

/// Read a bounded cursor without materializing every matching row. Returning
/// false ends the scan before SQLite reads or decodes the next row.
pub fn scan<P: Params>(
    connection: &Connection,
    sql: &str,
    params: P,
    mut visitor: impl FnMut(Value) -> Result<bool>,
) -> Result<()> {
    let mut statement = connection.prepare(sql)?;
    let decoder = RowDecoder::new(&statement);
    let mut cursor = statement.query(params)?;
    while let Some(row) = cursor.next()? {
        if !visitor(decoder.decode(row)?)? {
            break;
        }
    }
    Ok(())
}

/// A prepared cursor's names and first matching columns stay fixed while rows
/// stream. Shared by partitioned dashboard reads that must retain all cursors.
pub(crate) struct RowDecoder {
    names: Vec<String>,
    indices: Vec<usize>,
}
impl RowDecoder {
    pub(crate) fn new(statement: &rusqlite::Statement<'_>) -> Self {
        let names: Vec<String> = statement
            .column_names()
            .iter()
            .map(|name| (*name).into())
            .collect();
        let mut unique_names = Vec::with_capacity(names.len());
        let mut indices = Vec::with_capacity(names.len());
        for (index, name) in names.iter().enumerate() {
            if names[..index].contains(name) {
                continue;
            }
            unique_names.push(name.clone());
            indices.push(
                names[..index]
                    .iter()
                    .position(|previous| {
                        previous == name
                            || (previous.is_ascii()
                                && name.is_ascii()
                                && previous.eq_ignore_ascii_case(name))
                    })
                    .unwrap_or(index),
            );
        }
        Self {
            names: unique_names,
            indices,
        }
    }
    pub(crate) fn decode(&self, row: &rusqlite::Row<'_>) -> Result<Value> {
        let mut value = Value::Null;
        self.decode_into(row, &mut value)?;
        Ok(value)
    }

    /// Reuse one decoder's field layout and string buffers while streaming.
    /// Callers may take the decoded row, leaving null for the next read.
    pub(crate) fn decode_into(&self, row: &rusqlite::Row<'_>, values: &mut Value) -> Result<()> {
        if values.is_null() {
            *values = Value::Object(
                self.names
                    .iter()
                    .map(|name| (name.clone(), Value::Null))
                    .collect::<Map<_, _>>(),
            );
        }
        let fields = values.as_object_mut().unwrap();
        for (field, &index) in fields.values_mut().zip(&self.indices) {
            *field = match row.get_ref(index)? {
                ValueRef::Null => Value::Null,
                ValueRef::Integer(value) => value.into(),
                ValueRef::Real(value) => {
                    Value::Number(serde_json::Number::from_f64(value).ok_or_else(|| {
                        BackendError::new(500, "database", "SQLite returned a non-finite number")
                    })?)
                }
                ValueRef::Text(value) => {
                    let value = std::str::from_utf8(value)
                        .map_err(|error| BackendError::new(500, "database", error.to_string()))?;
                    if let Value::String(buffer) = field {
                        buffer.clear();
                        buffer.push_str(value);
                        continue;
                    }
                    value.into()
                }
                ValueRef::Blob(value) => {
                    Value::Array(value.iter().copied().map(Value::from).collect())
                }
            };
        }
        Ok(())
    }
}

pub fn row<P: Params>(connection: &Connection, sql: &str, params: P) -> Result<Option<Value>> {
    let mut result = None;
    scan(connection, sql, params, |row| {
        result = Some(row);
        Ok(false)
    })?;
    Ok(result)
}
