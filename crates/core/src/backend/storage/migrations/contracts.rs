use super::{revisions, support::*};
use crate::backend::{db, Result};
use regex::Regex;
use rusqlite::{types::Value, Connection};
use std::collections::BTreeSet;
const CLASS: &str =
    r"(?i)CHECK\s*\(\s*session_class\s+IN\s*\(\s*'work'\s*,\s*'maintenance'\s*\)\s*\)";
const POLICY: &str =
    r"(?i)CHECK\s*\(\s*index_policy\s+IN\s*\(\s*'full'\s*,\s*'metadata_only'\s*\)\s*\)";
const SHAPE: &str = r"(?i)CHECK\s*\(\s*maintenance_run_id\s+IS\s+NULL\s+OR\s*\(\s*session_class\s*=\s*'maintenance'\s+AND\s+session_role\s*=\s*'primary'\s+AND\s+index_policy\s*=\s*'metadata_only'\s*\)\s*\)";
const ATTRIBUTION: &str = r"(?i)CHECK\s*\(\s*attribution_basis\s+IN\s*\(\s*'git_root'\s*,\s*'workspace_path'\s*,\s*'unassigned'\s*\)\s*\)";
fn matches(pattern: &str, value: &str) -> bool {
    Regex::new(pattern)
        .expect("fixed migration expression")
        .is_match(value)
}
pub fn source_identity_current(connection: &Connection) -> Result<bool> {
    let contract = contract(connection, "sources")?;
    Ok(contract
        .get("provider_kind")
        .is_some_and(|column| int(&column[1]) != 0)
        && !contract.contains_key("kind"))
}
pub fn display_title_current(connection: &Connection) -> Result<bool> {
    let info = info(connection, "sessions")?;
    let title = info.iter().position(|row| text(&row[1]) == "title");
    let display = info.iter().position(|row| text(&row[1]) == "display_title");
    Ok(title.zip(display).is_some_and(|(title, display)| {
        display == title + 1
            && info[display][2..]
                == [
                    Value::Text("TEXT".into()),
                    Value::Integer(0),
                    Value::Null,
                    Value::Integer(0),
                ]
    }))
}
pub fn session_contract_current(connection: &Connection) -> Result<bool> {
    let Some(sql) = sql(connection, "sessions")? else {
        return Ok(false);
    };
    if [CLASS, POLICY, SHAPE]
        .iter()
        .any(|pattern| !matches(pattern, &sql))
    {
        return Ok(false);
    }
    let fk = db::rows(connection, "PRAGMA foreign_key_list(sessions)", [])?
        .iter()
        .any(|row| {
            row["from"] == "maintenance_run_id"
                && row["table"] == "maintenance_runs"
                && row["to"] == "id"
                && row["on_delete"]
                    .as_str()
                    .is_some_and(|value| value.eq_ignore_ascii_case("SET NULL"))
        });
    Ok(fk && unique_columns(connection, "sessions")?.contains(&vec!["maintenance_run_id".into()]))
}
pub fn maintenance_fk_current(connection: &Connection) -> Result<bool> {
    let rows = db::rows(connection, "PRAGMA foreign_key_list(maintenance_runs)", [])?
        .into_iter()
        .filter(|row| row["from"] == "workstream_id")
        .collect::<Vec<_>>();
    Ok(rows.len() == 1
        && rows[0]["table"] == "workstreams"
        && rows[0]["to"] == "id"
        && rows[0]["on_update"]
            .as_str()
            .is_some_and(|value| value.eq_ignore_ascii_case("NO ACTION"))
        && rows[0]["on_delete"]
            .as_str()
            .is_some_and(|value| value.eq_ignore_ascii_case("SET NULL")))
}
pub fn site_access_current(connection: &Connection) -> Result<bool> {
    let source = contract(connection, "atlassian_sites")?;
    if source
        .get("source_instance_id")
        .is_none_or(|column| int(&column[1]) != 0)
    {
        return Ok(false);
    }
    Ok(
        db::rows(connection, "PRAGMA foreign_key_list(atlassian_sites)", [])?
            .iter()
            .any(|row| {
                row["from"] == "source_instance_id"
                    && row["table"] == "external_source_instances"
                    && row["to"] == "id"
                    && row["on_delete"]
                        .as_str()
                        .is_some_and(|value| value.eq_ignore_ascii_case("SET NULL"))
            }),
    )
}
pub fn usage_table(connection: &Connection) -> Result<Option<String>> {
    let current = exists(connection, "usage_records")?;
    let legacy = exists(connection, "usage_facts")?;
    if current && legacy {
        return Err(fail(
            "Usage Record migration refused coexisting usage_records and legacy usage_facts tables",
        ));
    }
    Ok(if current {
        Some("usage_records".into())
    } else if legacy {
        Some("usage_facts".into())
    } else {
        None
    })
}
pub fn attribution_current(connection: &Connection, table: &str) -> Result<bool> {
    Ok(sql(connection, table)?.is_some_and(|sql| matches(ATTRIBUTION, &sql)))
}
pub fn migration_contracts_current(connection: &Connection) -> Result<bool> {
    Ok(source_identity_current(connection)?
        && site_access_current(connection)?
        && !unique_columns(connection, "external_resources")?.contains(&vec!["url".into()])
        && maintenance_fk_current(connection)?
        && session_contract_current(connection)?
        && display_title_current(connection)?
        && usage_table(connection)?.as_deref() == Some("usage_records")
        && attribution_current(connection, "usage_records")?
        && revisions::current(connection)?
        && super::resources::current(connection)?)
}

const STRUCTURE_TABLES: [&str; 3] = [
    "atlassian_structure_references",
    "atlassian_structure_reference_urls",
    "atlassian_structure_reference_evidence",
];
const STRUCTURE_INDEXES: [&str; 6] = [
    "idx_atlassian_structure_references_site",
    "idx_atlassian_structure_reference_urls_reference",
    "idx_atlassian_structure_reference_urls_canonical",
    "idx_atlassian_structure_reference_evidence_reference",
    "idx_atlassian_structure_reference_evidence_session",
    "idx_atlassian_structure_reference_evidence_document",
];
fn object_sql(connection: &Connection, kind: &str, name: &str) -> Result<String> {
    Ok(db::row(
        connection,
        "SELECT sql FROM sqlite_master WHERE type=? AND name=?",
        [kind, name],
    )?
    .and_then(|row| {
        row["sql"]
            .as_str()
            .map(|sql| sql.split_whitespace().collect::<Vec<_>>().join(" "))
    })
    .unwrap_or_default())
}
fn signature(connection: &Connection, kind: &str, name: &str) -> Result<String> {
    let pragmas = if kind == "table" {
        vec![
            format!("PRAGMA table_info({})", quote(name)),
            format!("PRAGMA foreign_key_list({})", quote(name)),
        ]
    } else {
        vec![format!("PRAGMA index_xinfo({})", quote(name))]
    };
    let mut result = object_sql(connection, kind, name)?;
    for query in pragmas {
        let mut rows = values(connection, &query)?;
        if query.contains("foreign_key_list") {
            rows.sort_by_key(|row| format!("{row:?}"));
        }
        result.push_str(&format!("{rows:?}"));
    }
    Ok(result)
}
pub fn validate_structure(connection: &Connection, preexisting: bool) -> Result<()> {
    let present = STRUCTURE_TABLES
        .iter()
        .filter(|table| exists(connection, table).unwrap_or(false))
        .count();
    if preexisting && present == 0 {
        return Ok(());
    }
    if present != 3 {
        return Err(fail(
            "Unexpected partial Atlassian Structure Reference schema",
        ));
    }
    let reference = canonical()?;
    for table in STRUCTURE_TABLES {
        if signature(connection, "table", table)? != signature(&reference, "table", table)? {
            return Err(fail(if preexisting {
                "Unexpected Atlassian Structure Reference table contract"
            } else {
                "Canonical Atlassian Structure Reference tables are unavailable"
            }));
        }
    }
    for index in STRUCTURE_INDEXES {
        if preexisting && object_sql(connection, "index", index)?.is_empty() {
            continue;
        }
        if signature(connection, "index", index)? != signature(&reference, "index", index)? {
            return Err(fail(if preexisting {
                "Unexpected Atlassian Structure Reference index contract"
            } else {
                "Canonical Atlassian Structure Reference indexes are unavailable"
            }));
        }
    }
    Ok(())
}

pub fn migrate_skill(connection: &Connection) -> Result<()> {
    let table = "skill_observations";
    let Some(sql) = sql(connection, table)? else {
        return Ok(());
    };
    if [
        "codex_skill_read",
        "claude_skill_read",
        "codex_skill_declaration",
        "claude_skill_declaration",
        "codex_skill_mention",
        "claude_skill_mention",
        "codex_skill_script",
        "claude_skill_script",
        "request_key",
    ]
    .iter()
    .all(|value| sql.contains(value))
    {
        return Ok(());
    }
    let columns = column_set(connection, table)?;
    let expected: BTreeSet<String> = [
        "id",
        "source_id",
        "provider_kind",
        "external_session_id",
        "native_event_id",
        "skill_name",
        "skill_group_key",
        "skill_locator",
        "signal_kind",
        "source_line",
        "occurred_at",
        "state",
        "recorded_at",
        "request_key",
    ]
    .into_iter()
    .map(str::to_owned)
    .collect();
    if !columns.is_subset(&expected)
        || expected
            .iter()
            .filter(|name| name.as_str() != "request_key")
            .any(|name| !columns.contains(name))
    {
        return Err(fail(
            "Skill observation upgrade found an unexpected table shape",
        ));
    }
    triggers_absent(
        connection,
        table,
        "Skill observation upgrade found an unexpected trigger",
    )?;
    let target = "skill_observations_read_upgrade";
    if exists(connection, target)? {
        return Err(fail("Skill observation upgrade target already exists"));
    }
    let indexes = objects(connection, "index", table)?;
    let retained = columns
        .iter()
        .map(|name| quote(name))
        .collect::<Vec<_>>()
        .join(",");
    savepoint(connection, "skill_observation_upgrade", || {
        connection.execute_batch(&ddl(table)?.replacen(table, target, 1))?;
        connection.execute_batch(&format!(
            "INSERT INTO {target} ({retained}) SELECT {retained} FROM {table}"
        ))?;
        for (before, after) in [(table, target), (target, table)] {
            if !values(
                connection,
                &format!("SELECT {retained} FROM {before} EXCEPT SELECT {retained} FROM {after}"),
            )?
            .is_empty()
            {
                return Err(fail("Skill observation upgrade changed retained evidence"));
            }
        }
        connection.execute_batch(&format!(
            "DROP TABLE {table}; ALTER TABLE {target} RENAME TO {table}"
        ))?;
        for index in indexes {
            connection.execute_batch(&index)?;
        }
        Ok(())
    })
}

pub fn repair_session(connection: &Connection) -> Result<()> {
    if (session_contract_current(connection)? && display_title_current(connection)?)
        || !exists(connection, "sessions")?
    {
        return Ok(());
    }
    let source = contract(connection, "sessions")?;
    let reference = canonical()?;
    let mut expected = contract(&reference, "sessions")?;
    if !source.contains_key("display_title") {
        expected.remove("display_title");
    }
    if source != expected {
        return Err(fail(
            "Maintenance Session migration found an unexpected Session table shape",
        ));
    }
    let canonical = sql(&reference, "sessions")?
        .ok_or_else(|| fail("Canonical Session schema is unavailable"))?;
    let mut allowed = revisions::clauses(&canonical)?;
    for pattern in [CLASS, POLICY] {
        let removed = Regex::new(pattern).unwrap().replace_all(&canonical, "");
        allowed.extend(revisions::clauses(&removed)?);
    }
    allowed.push(revisions::tokens("maintenance_run_id TEXT")?);
    let clauses = revisions::clauses(&sql(connection, "sessions")?.unwrap())?;
    if clauses.iter().any(|clause| !allowed.contains(clause))
        || !clauses.contains(&revisions::tokens("UNIQUE(source_id, external_id)")?)
    {
        return Err(fail(
            "Session migration found unexpected Session constraints",
        ));
    }
    let checks=[("session_class","SELECT COUNT(*) FROM sessions WHERE session_class IS NULL OR session_class NOT IN ('work','maintenance')"),("index_policy","SELECT COUNT(*) FROM sessions WHERE index_policy IS NULL OR index_policy NOT IN ('full','metadata_only')"),("duplicate_run","SELECT COUNT(*) FROM (SELECT maintenance_run_id FROM sessions WHERE maintenance_run_id IS NOT NULL GROUP BY maintenance_run_id HAVING COUNT(*)>1)"),("orphan_run","SELECT COUNT(*) FROM sessions LEFT JOIN maintenance_runs ON maintenance_runs.id=sessions.maintenance_run_id WHERE sessions.maintenance_run_id IS NOT NULL AND maintenance_runs.id IS NULL"),("link_shape","SELECT COUNT(*) FROM sessions WHERE maintenance_run_id IS NOT NULL AND NOT (session_class='maintenance' AND session_role='primary' AND index_policy='metadata_only')")];
    let mut invalid = Vec::new();
    for (name, query) in checks {
        let count: i64 = connection.query_row(query, [], |row| row.get(0))?;
        if count != 0 {
            invalid.push(format!("{name}={count}"));
        }
    }
    if !invalid.is_empty() {
        invalid.sort();
        return Err(fail(&format!(
            "Maintenance Session migration refused invalid rows: {}",
            invalid.join(", ")
        )));
    }
    triggers_absent(
        connection,
        "sessions",
        "Session migration found an unexpected trigger",
    )?;
    let columns = columns(&reference, "sessions")?
        .into_iter()
        .filter(|column| source.contains_key(column))
        .collect::<Vec<_>>();
    rebuild(
        connection,
        "sessions",
        "sessions__maintenance_contract_legacy",
        &canonical,
        &columns,
        true,
    )?;
    if !session_contract_current(connection)? {
        return Err(fail(
            "Maintenance Session migration did not restore the contract",
        ));
    }
    foreign_check(connection, None)
}
pub fn repair_maintenance(connection: &Connection) -> Result<()> {
    let Some(sql) = sql(connection, "maintenance_runs")? else {
        return Ok(());
    };
    if maintenance_fk_current(connection)? {
        return Ok(());
    }
    let source = contract(connection, "maintenance_runs")?;
    let expected = contract(&canonical()?, "maintenance_runs")?;
    if source.keys().ne(expected.keys()) {
        return Err(fail(
            "Maintenance Workstream FK migration found an unexpected table shape",
        ));
    }
    for (column, actual) in &source {
        if actual != &expected[column]
            && !(column == "updated_at"
                && *actual
                    == vec![
                        Value::Text("TEXT".into()),
                        Value::Integer(0),
                        Value::Null,
                        Value::Integer(0),
                    ])
        {
            return Err(fail(&format!(
                "Maintenance Workstream FK migration found an unexpected {column} contract"
            )));
        }
    }
    let count:i64=connection.query_row("SELECT COUNT(*) FROM maintenance_runs LEFT JOIN workstreams ON workstreams.id=maintenance_runs.workstream_id WHERE maintenance_runs.workstream_id IS NOT NULL AND workstreams.id IS NULL",[],|row|row.get(0))?;
    if count != 0 {
        return Err(fail(&format!(
            "Maintenance Workstream FK migration refused {count} orphan row(s)"
        )));
    }
    let pattern=Regex::new(r#"(?i)((?:"workstream_id"|`workstream_id`|\[workstream_id\]|workstream_id)\s+INTEGER)(\s*)([,\)])"#).unwrap();
    if !pattern.is_match(&sql) {
        return Err(fail(
            "Maintenance Workstream FK migration found an unexpected column definition",
        ));
    }
    let repaired = pattern
        .replacen(
            &sql,
            1,
            "${1} REFERENCES workstreams(id) ON DELETE SET NULL${2}${3}",
        )
        .into_owned();
    let before = info(connection, "maintenance_runs")?;
    let sessions=values(connection,"SELECT id,maintenance_run_id FROM sessions WHERE maintenance_run_id IS NOT NULL ORDER BY id")?;
    let suggestions = values(
        connection,
        "SELECT id,origin_run_id FROM suggestions WHERE origin_run_id IS NOT NULL ORDER BY id",
    )?;
    rebuild(
        connection,
        "maintenance_runs",
        "maintenance_runs__workstream_fk_legacy",
        &repaired,
        &columns(connection, "maintenance_runs")?,
        true,
    )?;
    if info(connection,"maintenance_runs")?!=before||values(connection,"SELECT id,maintenance_run_id FROM sessions WHERE maintenance_run_id IS NOT NULL ORDER BY id")?!=sessions||values(connection,"SELECT id,origin_run_id FROM suggestions WHERE origin_run_id IS NOT NULL ORDER BY id")?!=suggestions{return Err(fail("Maintenance Workstream FK migration changed retained metadata or links"));}
    if !maintenance_fk_current(connection)? {
        return Err(fail(
            "Maintenance Workstream FK migration did not restore the contract",
        ));
    }
    foreign_check(connection, None)
}
pub fn repair_site(connection: &Connection) -> Result<()> {
    if site_access_current(connection)? || !exists(connection, "atlassian_sites")? {
        return Ok(());
    }
    let expected = [
        "id",
        "source_instance_id",
        "normalized_domain",
        "display_name",
        "remote_site_id",
        "canonical_base_url",
        "created_at",
        "updated_at",
    ];
    let columns = columns(connection, "atlassian_sites")?;
    if columns != expected {
        return Err(fail(
            "Atlassian Site access migration found an unexpected table shape",
        ));
    }
    rebuild(
        connection,
        "atlassian_sites",
        "atlassian_sites__required_access_legacy",
        &ddl("atlassian_sites")?,
        &columns,
        true,
    )?;
    if !site_access_current(connection)? {
        return Err(fail(
            "Atlassian Site access migration did not restore the contract",
        ));
    }
    foreign_check(connection, None)
}
pub fn rename_usage(connection: &Connection) -> Result<()> {
    if usage_table(connection)?.as_deref() != Some("usage_facts") {
        return Ok(());
    }
    savepoint(connection, "usage_record_table_rename", || {
        connection.execute_batch("ALTER TABLE usage_facts RENAME TO usage_records; DROP INDEX IF EXISTS idx_usage_facts_session_time; DROP INDEX IF EXISTS idx_usage_facts_source_time; DROP INDEX IF EXISTS idx_usage_facts_model_time")?;
        usage_indexes(connection)?;
        foreign_check(connection, Some("usage_records"))
    })
}
pub fn usage_indexes(connection: &Connection) -> Result<()> {
    connection.execute_batch("CREATE INDEX IF NOT EXISTS idx_usage_records_session_time ON usage_records(session_id,occurred_at); CREATE INDEX IF NOT EXISTS idx_usage_records_source_time ON usage_records(source_id,occurred_at); CREATE INDEX IF NOT EXISTS idx_usage_records_model_time ON usage_records(model_name,occurred_at)")?;
    Ok(())
}
pub fn repair_attribution(connection: &Connection) -> Result<()> {
    let Some(sql) = sql(connection, "usage_records")? else {
        return Ok(());
    };
    if attribution_current(connection, "usage_records")? {
        return Ok(());
    }
    let invalid:i64=connection.query_row("SELECT COUNT(*) FROM usage_records WHERE attribution_basis IS NULL OR attribution_basis NOT IN ('git_root','workspace_path','unassigned')",[],|row|row.get(0))?;
    if invalid != 0 {
        return Err(fail(&format!(
            "Usage attribution migration refused {invalid} invalid row(s)"
        )));
    }
    if column_set(connection, "usage_records")? != column_set(&canonical()?, "usage_records")? {
        return Err(fail(
            "Usage attribution migration found an unexpected table shape",
        ));
    }
    let pattern =
        Regex::new(r"(?i)(\battribution_basis\s+TEXT\s+NOT\s+NULL\s+DEFAULT\s+'unassigned')")
            .unwrap();
    if !pattern.is_match(&sql) {
        return Err(fail(
            "Usage attribution migration found an unexpected column definition",
        ));
    }
    let repaired = pattern
        .replacen(
            &sql,
            1,
            "${1} CHECK(attribution_basis IN ('git_root', 'workspace_path', 'unassigned'))",
        )
        .into_owned();
    let target = "usage_records__attribution_check_repair";
    let table_pattern=Regex::new(r#"(?i)^\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:"usage_records"|`usage_records`|\[usage_records\]|usage_records)"#).unwrap();
    if !table_pattern.is_match(&repaired) {
        return Err(fail(
            "Usage attribution migration found an unexpected table definition",
        ));
    }
    let repaired = table_pattern
        .replacen(&repaired, 1, format!("CREATE TABLE {}", quote(target)))
        .into_owned();
    if exists(connection, target)? {
        return Err(fail("Usage attribution migration target already exists"));
    }
    let source = info(connection, "usage_records")?;
    let columns = columns(connection, "usage_records")?
        .iter()
        .map(|column| quote(column))
        .collect::<Vec<_>>()
        .join(",");
    savepoint(connection, "usage_attribution_check_repair", || {
        connection.execute_batch(&repaired)?;
        if info(connection, target)? != source {
            return Err(fail(
                "Usage attribution migration would change column metadata",
            ));
        }
        connection.execute_batch(&format!(
            "INSERT INTO {target} ({columns}) SELECT {columns} FROM usage_records"
        ))?;
        for (before, after) in [("usage_records", target), (target, "usage_records")] {
            if !values(
                connection,
                &format!("SELECT {columns} FROM {before} EXCEPT SELECT {columns} FROM {after}"),
            )?
            .is_empty()
            {
                return Err(fail("Usage attribution migration row values changed"));
            }
        }
        connection.execute_batch(&format!(
            "DROP TABLE usage_records; ALTER TABLE {target} RENAME TO usage_records"
        ))?;
        usage_indexes(connection)?;
        foreign_check(connection, Some("usage_records"))
    })
}
