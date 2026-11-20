use super::support::*;
use crate::backend::{db, Config, Result};
use rusqlite::{params_from_iter, types::Value, Connection};
use std::collections::{BTreeMap, BTreeSet};

pub const CHECK:&str="CHECK(session_contract_version IS NULL OR (typeof(session_contract_version) = 'integer' AND session_contract_version > 0))";
pub type Token = (String, String);
pub fn tokens(sql: &str) -> Result<Vec<Token>> {
    let chars: Vec<char> = sql.chars().collect();
    let mut result = Vec::new();
    let mut index = 0;
    while index < chars.len() {
        let ch = chars[index];
        if ch.is_whitespace() || ch == '\u{feff}' {
            index += 1;
        } else if ch == '-' && chars.get(index + 1) == Some(&'-') {
            index += 2;
            while index < chars.len() && chars[index] != '\n' {
                index += 1;
            }
        } else if ch == '/' && chars.get(index + 1) == Some(&'*') {
            index += 2;
            while index < chars.len()
                && !(chars[index] == '*' && chars.get(index + 1) == Some(&'/'))
            {
                index += 1;
            }
            index = (index + 2).min(chars.len());
        } else if ['\'', '"', '`', '['].contains(&ch) {
            let end = if ch == '[' { ']' } else { ch };
            index += 1;
            let mut value = String::new();
            let mut closed = false;
            while index < chars.len() {
                if chars[index] == end {
                    index += 1;
                    if end != ']' && chars.get(index) == Some(&end) {
                        value.push(end);
                        index += 1;
                        continue;
                    }
                    closed = true;
                    break;
                }
                value.push(chars[index]);
                index += 1;
            }
            if !closed {
                return Err(fail(
                    "Unrecognized source-file DDL; Session migration stopped",
                ));
            }
            result.push((
                if ch == '\'' { "string" } else { "identifier" }.into(),
                if ch == '\'' {
                    value
                } else {
                    value.to_lowercase()
                },
            ));
        } else if ch.is_alphabetic() || ch == '_' || (ch as u32) >= 128 {
            let start = index;
            index += 1;
            while index < chars.len()
                && (chars[index].is_alphanumeric()
                    || ['_', '$'].contains(&chars[index])
                    || (chars[index] as u32) >= 128)
            {
                index += 1;
            }
            result.push((
                "word".into(),
                chars[start..index]
                    .iter()
                    .collect::<String>()
                    .to_lowercase(),
            ));
        } else {
            result.push(("symbol".into(), ch.to_string()));
            index += 1;
        }
    }
    Ok(result)
}
fn token(token: &Token, kind: &str, value: &str) -> bool {
    token.0 == kind && token.1 == value
}
fn checks(input: &[Token]) -> Result<Vec<bool>> {
    let expected = tokens(CHECK)?;
    let presence = tokens("CHECK(presence_state IN ('PRESENT','MISSING','UNKNOWN'))")?;
    let mut result = Vec::new();
    let mut depth = 0;
    let mut index = 0;
    while index < input.len() {
        if depth == 1
            && token(&input[index], "word", "check")
            && input
                .get(index + 1)
                .is_some_and(|token_| token(token_, "symbol", "("))
        {
            let start = index;
            index += 2;
            let mut check_depth = 1;
            while index < input.len() && check_depth != 0 {
                if token(&input[index], "symbol", "(") {
                    check_depth += 1;
                } else if token(&input[index], "symbol", ")") {
                    check_depth -= 1;
                }
                index += 1;
            }
            let check: Vec<_> = input[start..index]
                .iter()
                .map(|(kind, value)| {
                    (
                        if kind == "identifier"
                            && ["session_contract_version", "presence_state", "typeof"]
                                .contains(&value.as_str())
                        {
                            "word".into()
                        } else {
                            kind.clone()
                        },
                        value.clone(),
                    )
                })
                .collect();
            if check != presence {
                result.push(check_depth == 0 && check == expected);
            }
            continue;
        }
        if token(&input[index], "symbol", "(") {
            depth += 1;
        } else if token(&input[index], "symbol", ")") {
            depth -= 1;
        }
        index += 1;
    }
    Ok(result)
}
pub fn current(connection: &Connection) -> Result<bool> {
    let columns = info(connection, "source_files")?;
    let Some(revision) = columns
        .iter()
        .find(|row| text(&row[1]) == "session_contract_version")
    else {
        return Ok(false);
    };
    if !text(&revision[2]).eq_ignore_ascii_case("INTEGER") {
        return Ok(false);
    }
    Ok(sql(connection, "source_files")?.is_some_and(|sql| {
        checks(&tokens(&sql).unwrap_or_default())
            .unwrap_or_default()
            .into_iter()
            .any(|value| value)
    }))
}
fn legacy_revision(provider: &str, value: &str) -> Option<i64> {
    match (provider, value) {
        ("codex", "codex-session-v3-response-message-fallback-user-prompt-guardian") => Some(3),
        (
            "codex",
            "codex-session-v4-response-message-fallback-user-prompt-guardian-skill-observations",
        ) => Some(4),
        ("codex", "codex-session-v8-skill-reference-sessions") => Some(8),
        ("codex", "codex-session-v11-question-replies-and-context-blocks") => Some(11),
        ("codex", "codex-session-v12-empty-page-controls") => Some(12),
        ("claude", "claude-session-v1") => Some(1),
        ("claude", "claude-session-v2-skill-observations") => Some(2),
        ("claude", "claude-session-v6-skill-reference-sessions") => Some(6),
        ("claude", "claude-session-v7-message-phases") => Some(7),
        _ => None,
    }
}
fn converted(connection: &Connection) -> Result<Vec<Vec<Value>>> {
    let columns = columns(connection, "source_files")?;
    let Some(index) = columns
        .iter()
        .position(|column| column == "session_contract_version")
    else {
        return Ok(vec![]);
    };
    let provider = if has(connection, "sources", "provider_kind")? {
        "provider_kind"
    } else {
        "kind"
    };
    let rows=values(connection,&format!("SELECT f.*,s.{provider} AS revision_provider FROM source_files f LEFT JOIN sources s ON s.id=f.source_id ORDER BY f.id"))?;
    rows.into_iter().map(|mut row|{let provider=row.pop().unwrap_or(Value::Null);let provider=if text(&provider)=="codex-company"{"codex"}else{text(&provider)};row[index]=match &row[index]{Value::Null=>Value::Null,Value::Integer(value) if *value>0=>Value::Integer(*value),Value::Text(value)=>legacy_revision(provider,value).map(Value::Integer).ok_or_else(||fail("Unrecognized Session revision; migration stopped without replacing results"))?,_=>return Err(fail("Unrecognized Session revision; migration stopped without replacing results"))};Ok(row)}).collect()
}
pub fn prepare(connection: &Connection, config: &Config) -> Result<()> {
    if !exists(connection, "source_files")? {
        return Ok(());
    }
    converted(connection)?;
    if !current(connection)? && config.database_path.is_file() {
        backup(connection, config, "-pre-session-revision-v1.bak")?;
    }
    Ok(())
}
fn xcontract(connection: &Connection, table: &str) -> Result<BTreeMap<String, Vec<Value>>> {
    Ok(
        values(connection, &format!("PRAGMA table_xinfo({})", quote(table)))?
            .into_iter()
            .map(|mut row| {
                if let Value::Text(value) = &mut row[2] {
                    *value = value.to_uppercase();
                }
                (text(&row[1]).into(), row[2..].to_vec())
            })
            .collect(),
    )
}
fn foreign(connection: &Connection, table: &str) -> Result<Vec<String>> {
    let mut result = db::rows(
        connection,
        &format!("PRAGMA foreign_key_list({})", quote(table)),
        [],
    )?
    .iter()
    .map(|row| {
        ["table", "from", "to", "on_update", "on_delete", "match"]
            .iter()
            .map(|key| row[*key].to_string())
            .collect::<Vec<_>>()
            .join("|")
    })
    .collect::<Vec<_>>();
    result.sort();
    Ok(result)
}
fn uniques(connection: &Connection, table: &str) -> Result<Vec<String>> {
    let mut result = Vec::new();
    for row in db::rows(
        connection,
        &format!("PRAGMA index_list({})", quote(table)),
        [],
    )? {
        if ![Some("u"), Some("pk")].contains(&row["origin"].as_str()) {
            continue;
        }
        let keys = db::rows(
            connection,
            &format!(
                "PRAGMA index_xinfo({})",
                quote(row["name"].as_str().unwrap_or(""))
            ),
            [],
        )?
        .into_iter()
        .filter(|row| row["key"].as_i64() == Some(1))
        .map(|row| json_keys(&row, &["name", "desc", "coll"]))
        .collect::<Vec<_>>();
        result.push(format!("{}|{}|{:?}", row["unique"], row["partial"], keys));
    }
    result.sort();
    Ok(result)
}
fn json_keys(value: &serde_json::Value, keys: &[&str]) -> String {
    keys.iter()
        .map(|key| value[*key].to_string())
        .collect::<Vec<_>>()
        .join("|")
}
fn validate_shape(connection: &Connection, target: &str) -> Result<()> {
    let mut original = xcontract(connection, "source_files")?;
    let expected = xcontract(connection, target)?;
    if let Some(revision) = original.get_mut("session_contract_version") {
        if ["TEXT", "INTEGER"].contains(&text(&revision[0])) {
            revision[0] = Value::Text("INTEGER".into());
        }
    }
    if original != expected {
        return Err(fail(
            "Unexpected source-file columns; Session migration stopped",
        ));
    }
    for table in db::rows(
        connection,
        "SELECT name FROM sqlite_master WHERE type='table'",
        [],
    )? {
        if db::rows(
            connection,
            &format!(
                "PRAGMA foreign_key_list({})",
                quote(table["name"].as_str().unwrap_or(""))
            ),
            [],
        )?
        .iter()
        .any(|row| {
            row["table"]
                .as_str()
                .is_some_and(|value| value.eq_ignore_ascii_case("source_files"))
        }) {
            return Err(fail(
                "Unexpected source-file references; Session migration stopped",
            ));
        }
    }
    let sql = sql(connection, "source_files")?.unwrap_or_default();
    let input = tokens(&sql)?;
    let unsupported: BTreeSet<&str> = [
        "without",
        "deferrable",
        "collate",
        "autoincrement",
        "strict",
    ]
    .into_iter()
    .collect();
    if foreign(connection, "source_files")? != foreign(connection, target)?
        || uniques(connection, "source_files")? != uniques(connection, target)?
        || checks(&input)?.iter().any(|value| !*value)
        || input
            .iter()
            .any(|(kind, value)| kind == "word" && unsupported.contains(value.as_str()))
        || input
            .windows(2)
            .any(|window| token(&window[0], "word", "on") && token(&window[1], "word", "conflict"))
    {
        return Err(fail(
            "Unexpected source-file constraints; Session migration stopped",
        ));
    }
    Ok(())
}
pub fn migrate(connection: &Connection) -> Result<()> {
    if current(connection)? {
        return Ok(());
    }
    let rows = converted(connection)?;
    let target = "source_files_numeric_revision";
    if exists(connection, target)? {
        return Err(fail("Session revision migration target already exists"));
    }
    let indexes = objects(connection, "index", "source_files")?;
    triggers_absent(
        connection,
        "source_files",
        "Unexpected source-file trigger; Session migration stopped",
    )?;
    savepoint(connection, "session_numeric_revision", || {
        connection.execute_batch(&ddl("source_files")?.replacen(
            "source_files (",
            &format!("{target} ("),
            1,
        ))?;
        validate_shape(connection, target)?;
        let columns = columns(connection, "source_files")?;
        if column_set(connection, "source_files")? != column_set(connection, target)? {
            return Err(fail(
                "Unexpected source-file shape; Session migration stopped",
            ));
        }
        let statement = format!(
            "INSERT INTO {target} ({}) VALUES ({})",
            columns.join(","),
            vec!["?"; columns.len()].join(",")
        );
        for row in rows {
            connection.execute(&statement, params_from_iter(row))?;
        }
        connection.execute_batch(&format!(
            "DROP TABLE source_files; ALTER TABLE {target} RENAME TO source_files"
        ))?;
        for index in indexes {
            connection.execute_batch(&index)?;
        }
        foreign_check(connection, Some("source_files"))?;
        if !current(connection)? {
            return Err(fail(
                "Session revision migration did not restore its contract",
            ));
        }
        Ok(())
    })
}

pub fn clauses(sql: &str) -> Result<Vec<Vec<Token>>> {
    let input = tokens(sql)?;
    let start = input
        .iter()
        .position(|token_| token(token_, "symbol", "("))
        .ok_or_else(|| fail("Session migration found an incomplete table definition"))?
        + 1;
    let mut depth = 1;
    let mut result = Vec::new();
    let mut clause = Vec::new();
    for (index, token_) in input.iter().enumerate().skip(start) {
        if token(token_, "symbol", "(") {
            depth += 1;
        } else if token(token_, "symbol", ")") {
            depth -= 1;
        }
        if depth == 0 {
            result.push(clause);
            if input[index + 1..]
                .iter()
                .any(|token_| !token(token_, "symbol", ";"))
            {
                return Err(fail("Session migration found unsupported table options"));
            }
            return Ok(result);
        }
        if depth == 1 && token(token_, "symbol", ",") {
            result.push(std::mem::take(&mut clause));
        } else {
            clause.push(token_.clone());
        }
    }
    Err(fail(
        "Session migration found an incomplete table definition",
    ))
}
