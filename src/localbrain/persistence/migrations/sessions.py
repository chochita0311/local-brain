"""Session ownership, skill evidence and activity schema migrations."""

import re
import sqlite3
from pathlib import Path
from localbrain.persistence.migrations.support import (
    SCHEMA_PATH,
    _column_names,
    _ensure_migration_backup,
    _quote_identifier,
    _table_sql,
)


MAINTENANCE_SESSION_CONTRACT_BACKUP_SUFFIX = (
    "-pre-maintenance-session-contract-v1.bak"
)


SESSION_CLASS_CHECK_PATTERN = re.compile(
    r"CHECK\s*\(\s*session_class\s+IN\s*\(\s*'work'\s*,\s*'maintenance'\s*\)\s*\)",
    flags=re.IGNORECASE,
)


INDEX_POLICY_CHECK_PATTERN = re.compile(
    r"CHECK\s*\(\s*index_policy\s+IN\s*\(\s*'full'\s*,\s*'metadata_only'\s*\)\s*\)",
    flags=re.IGNORECASE,
)


MAINTENANCE_SESSION_SHAPE_CHECK_PATTERN = re.compile(
    r"CHECK\s*\(\s*maintenance_run_id\s+IS\s+NULL\s+OR\s*\(\s*"
    r"session_class\s*=\s*'maintenance'\s+AND\s+session_role\s*=\s*'primary'\s+"
    r"AND\s+index_policy\s*=\s*'metadata_only'\s*\)\s*\)",
    flags=re.IGNORECASE,
)


def _migrate_skill_observation_contract(connection: sqlite3.Connection) -> None:
    """Atomically retain the ledger while extending its bounded evidence kinds."""
    table = "skill_observations"
    old_sql = _table_sql(connection, table)
    if not old_sql or (all(signal in old_sql for signal in (
        "codex_skill_read", "claude_skill_read",
        "codex_skill_declaration", "claude_skill_declaration",
        "codex_skill_mention", "claude_skill_mention",
        "codex_skill_script", "claude_skill_script",
    )) and "request_key" in old_sql):
        return
    columns = _column_names(connection, table)
    expected = {
        "id", "source_id", "provider_kind", "external_session_id", "native_event_id",
        "skill_name", "skill_group_key", "skill_locator", "signal_kind", "source_line",
        "occurred_at", "state", "recorded_at", "request_key",
    }
    if not columns.issubset(expected) or not expected.difference({"request_key"}).issubset(columns):
        raise RuntimeError("Skill observation upgrade found an unexpected table shape")
    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='trigger' AND tbl_name=?", (table,)
    ).fetchone():
        raise RuntimeError("Skill observation upgrade found an unexpected trigger")
    temporary = "skill_observations_read_upgrade"
    if _table_sql(connection, temporary):
        raise RuntimeError("Skill observation upgrade target already exists")
    indexes = [row["sql"] for row in connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL",
        (table,),
    )]
    fresh_sql = re.search(
        r"CREATE TABLE IF NOT EXISTS skill_observations \([\s\S]*?\n\);",
        SCHEMA_PATH.read_text(encoding="utf-8"),
    ).group()
    retained = ", ".join(sorted(columns))
    connection.execute("SAVEPOINT skill_observation_upgrade")
    try:
        connection.execute(fresh_sql.replace(table, temporary, 1))
        connection.execute("INSERT INTO {} ({}) SELECT {} FROM {}".format(
            temporary, retained, retained, table
        ))
        for before, after in ((table, temporary), (temporary, table)):
            if connection.execute("SELECT {} FROM {} EXCEPT SELECT {} FROM {}".format(
                retained, before, retained, after
            )).fetchone():
                raise RuntimeError("Skill observation upgrade changed retained evidence")
        connection.execute("DROP TABLE " + table)
        connection.execute("ALTER TABLE " + temporary + " RENAME TO " + table)
        for index_sql in indexes:
            connection.execute(index_sql)
        connection.execute("RELEASE skill_observation_upgrade")
    except Exception:
        connection.execute("ROLLBACK TO skill_observation_upgrade")
        connection.execute("RELEASE skill_observation_upgrade")
        raise


def _maintenance_session_contract_exists(connection: sqlite3.Connection) -> bool:
    table_sql = _table_sql(connection, "sessions")
    if not table_sql:
        return False
    if not all(
        pattern.search(table_sql)
        for pattern in (
            SESSION_CLASS_CHECK_PATTERN,
            INDEX_POLICY_CHECK_PATTERN,
            MAINTENANCE_SESSION_SHAPE_CHECK_PATTERN,
        )
    ):
        return False
    foreign_key = any(
        row["from"] == "maintenance_run_id"
        and row["table"] == "maintenance_runs"
        and row["to"] == "id"
        and row["on_delete"].upper() == "SET NULL"
        for row in connection.execute("PRAGMA foreign_key_list(sessions)")
    )
    if not foreign_key:
        return False
    return any(
        bool(index["unique"])
        and [
            row["name"]
            for row in connection.execute(
                "PRAGMA index_info({})".format(_quote_identifier(index["name"]))
            )
        ]
        == ["maintenance_run_id"]
        for index in connection.execute("PRAGMA index_list(sessions)")
    )


def _maintenance_session_contract_backup_path(database_path: Path) -> Path:
    return database_path.with_name(
        database_path.name + MAINTENANCE_SESSION_CONTRACT_BACKUP_SUFFIX
    )


def _ensure_maintenance_session_contract_backup(
    connection: sqlite3.Connection, database_path: Path
) -> Path:
    backup_path = _maintenance_session_contract_backup_path(database_path)
    return _ensure_migration_backup(connection, backup_path)


def _expected_session_columns() -> list:
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        return [tuple(row) for row in reference.execute("PRAGMA table_info(sessions)")]
    finally:
        reference.close()


def _canonical_sessions_sql() -> str:
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        row = reference.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'sessions'"
        ).fetchone()
        if not row or not row[0]:
            raise RuntimeError("Canonical Session schema is unavailable")
        return row[0]
    finally:
        reference.close()


def _repair_maintenance_session_contract(connection: sqlite3.Connection) -> bool:
    if _maintenance_session_contract_exists(connection):
        return False
    if not _table_sql(connection, "sessions"):
        return False

    source_info = [
        tuple(row) for row in connection.execute("PRAGMA table_info(sessions)")
    ]
    expected_info = _expected_session_columns()
    source_contract = {row[1]: row[2:] for row in source_info}
    expected_contract = {row[1]: row[2:] for row in expected_info}
    if source_contract != expected_contract or len(source_info) != len(expected_info):
        raise RuntimeError(
            "Maintenance Session migration found an unexpected Session table shape"
        )

    invalid_class_count = connection.execute(
        "SELECT COUNT(*) FROM sessions "
        "WHERE session_class IS NULL OR session_class NOT IN ('work', 'maintenance')"
    ).fetchone()[0]
    invalid_policy_count = connection.execute(
        "SELECT COUNT(*) FROM sessions "
        "WHERE index_policy IS NULL OR index_policy NOT IN ('full', 'metadata_only')"
    ).fetchone()[0]
    duplicate_run_count = connection.execute(
        "SELECT COUNT(*) FROM ("
        "SELECT maintenance_run_id FROM sessions "
        "WHERE maintenance_run_id IS NOT NULL GROUP BY maintenance_run_id "
        "HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    orphan_run_count = connection.execute(
        "SELECT COUNT(*) FROM sessions "
        "LEFT JOIN maintenance_runs ON maintenance_runs.id = sessions.maintenance_run_id "
        "WHERE sessions.maintenance_run_id IS NOT NULL AND maintenance_runs.id IS NULL"
    ).fetchone()[0]
    invalid_link_shape_count = connection.execute(
        "SELECT COUNT(*) FROM sessions WHERE maintenance_run_id IS NOT NULL "
        "AND NOT (session_class = 'maintenance' AND session_role = 'primary' "
        "AND index_policy = 'metadata_only')"
    ).fetchone()[0]
    invalid_counts = {
        "session_class": invalid_class_count,
        "index_policy": invalid_policy_count,
        "duplicate_run": duplicate_run_count,
        "orphan_run": orphan_run_count,
        "link_shape": invalid_link_shape_count,
    }
    invalid_counts = {key: value for key, value in invalid_counts.items() if value}
    if invalid_counts:
        raise RuntimeError(
            "Maintenance Session migration refused invalid rows: {}".format(
                ", ".join(
                    "{}={}".format(key, value)
                    for key, value in sorted(invalid_counts.items())
                )
            )
        )

    columns = [row[1] for row in expected_info]
    column_list = ", ".join(_quote_identifier(column) for column in columns)
    before_rows = [
        tuple(row)
        for row in connection.execute(
            "SELECT {} FROM sessions ORDER BY id".format(column_list)
        )
    ]
    canonical_sql = _canonical_sessions_sql()
    legacy_table = "sessions__maintenance_contract_legacy"
    if _table_sql(connection, legacy_table):
        raise RuntimeError("Maintenance Session migration target already exists")

    foreign_keys_enabled = bool(connection.execute("PRAGMA foreign_keys").fetchone()[0])
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("PRAGMA legacy_alter_table = ON")
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "ALTER TABLE sessions RENAME TO {}".format(
                _quote_identifier(legacy_table)
            )
        )
        connection.execute(canonical_sql)
        connection.execute(
            "INSERT INTO sessions ({columns}) SELECT {columns} FROM {legacy}".format(
                columns=column_list, legacy=_quote_identifier(legacy_table)
            )
        )
        target_info = [
            tuple(row) for row in connection.execute("PRAGMA table_info(sessions)")
        ]
        if target_info != expected_info:
            raise RuntimeError(
                "Maintenance Session migration would change column metadata"
            )
        after_rows = [
            tuple(row)
            for row in connection.execute(
                "SELECT {} FROM sessions ORDER BY id".format(column_list)
            )
        ]
        if after_rows != before_rows:
            raise RuntimeError("Maintenance Session migration changed Session rows")
        connection.execute(
            "DROP TABLE {}".format(_quote_identifier(legacy_table))
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA legacy_alter_table = OFF")
        connection.execute(
            "PRAGMA foreign_keys = {}".format("ON" if foreign_keys_enabled else "OFF")
        )

    if not _maintenance_session_contract_exists(connection):
        raise RuntimeError("Maintenance Session migration did not restore the contract")
    foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_errors:
        raise RuntimeError("Maintenance Session migration foreign key check failed")
    return True


def _remove_unused_activity_event_metadata(
    connection: sqlite3.Connection,
) -> bool:
    if "metadata_json" not in _column_names(connection, "activity_events"):
        return False
    non_null_count = connection.execute(
        "SELECT COUNT(*) FROM activity_events WHERE metadata_json IS NOT NULL"
    ).fetchone()[0]
    if non_null_count:
        raise RuntimeError(
            "Activity Event metadata removal refused {} non-null row(s)".format(
                non_null_count
            )
        )
    connection.execute("ALTER TABLE activity_events DROP COLUMN metadata_json")
    return True
