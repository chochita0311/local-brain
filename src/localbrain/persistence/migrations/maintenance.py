"""Maintenance Run organization relationship schema history."""

import re
import sqlite3
from pathlib import Path
from localbrain.persistence.migrations.support import (
    SCHEMA_PATH,
    _ensure_migration_backup,
    _quote_identifier,
    _table_sql,
)


MAINTENANCE_WORKSTREAM_FK_BACKUP_SUFFIX = (
    "-pre-maintenance-workstream-fk-v1.bak"
)


def _maintenance_workstream_fk_exists(connection: sqlite3.Connection) -> bool:
    if not _table_sql(connection, "maintenance_runs"):
        return False
    matching = [
        row
        for row in connection.execute("PRAGMA foreign_key_list(maintenance_runs)")
        if row["from"] == "workstream_id"
    ]
    return len(matching) == 1 and all(
        (
            matching[0]["table"] == "workstreams",
            matching[0]["to"] == "id",
            matching[0]["on_update"].upper() == "NO ACTION",
            matching[0]["on_delete"].upper() == "SET NULL",
        )
    )


def _maintenance_workstream_fk_backup_path(database_path: Path) -> Path:
    return database_path.with_name(
        database_path.name + MAINTENANCE_WORKSTREAM_FK_BACKUP_SUFFIX
    )


def _ensure_maintenance_workstream_fk_backup(
    connection: sqlite3.Connection, database_path: Path
) -> Path:
    backup_path = _maintenance_workstream_fk_backup_path(database_path)
    return _ensure_migration_backup(connection, backup_path)


def _expected_maintenance_run_columns() -> dict:
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        return {
            row[1]: tuple(row[2:])
            for row in reference.execute("PRAGMA table_info(maintenance_runs)")
        }
    finally:
        reference.close()


def _maintenance_workstream_repair_sql(table_sql: str) -> str:
    table_pattern = re.compile(
        r"^\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
        r"(?:\"maintenance_runs\"|`maintenance_runs`|\[maintenance_runs\]|maintenance_runs)"
        r"(?=\s|\()",
        flags=re.IGNORECASE,
    )
    if not table_pattern.search(table_sql):
        raise RuntimeError(
            "Maintenance Workstream FK migration found an unexpected table definition"
        )
    column_pattern = re.compile(
        r"((?:\"workstream_id\"|`workstream_id`|\[workstream_id\]|workstream_id)"
        r"\s+INTEGER)(\s*)(?=,|\))",
        flags=re.IGNORECASE,
    )
    repaired_sql, replacements = column_pattern.subn(
        r"\1 REFERENCES workstreams(id) ON DELETE SET NULL\2",
        table_sql,
        count=1,
    )
    if replacements != 1:
        raise RuntimeError(
            "Maintenance Workstream FK migration found an unexpected column definition"
        )
    return repaired_sql


def _repair_maintenance_workstream_fk(connection: sqlite3.Connection) -> bool:
    table_sql = _table_sql(connection, "maintenance_runs")
    if not table_sql or _maintenance_workstream_fk_exists(connection):
        return False

    source_info = [
        tuple(row) for row in connection.execute("PRAGMA table_info(maintenance_runs)")
    ]
    source_contract = {row[1]: tuple(row[2:]) for row in source_info}
    expected_contract = _expected_maintenance_run_columns()
    if set(source_contract) != set(expected_contract):
        raise RuntimeError(
            "Maintenance Workstream FK migration found an unexpected table shape"
        )
    for column, expected in expected_contract.items():
        actual = source_contract[column]
        allowed = {expected}
        if column == "updated_at":
            allowed.add(("TEXT", 0, None, 0))
        if actual not in allowed:
            raise RuntimeError(
                "Maintenance Workstream FK migration found an unexpected {} contract".format(
                    column
                )
            )

    orphan_count = connection.execute(
        "SELECT COUNT(*) FROM maintenance_runs "
        "LEFT JOIN workstreams ON workstreams.id = maintenance_runs.workstream_id "
        "WHERE maintenance_runs.workstream_id IS NOT NULL AND workstreams.id IS NULL"
    ).fetchone()[0]
    if orphan_count:
        raise RuntimeError(
            "Maintenance Workstream FK migration refused {} orphan row(s)".format(
                orphan_count
            )
        )

    legacy_table = "maintenance_runs__workstream_fk_legacy"
    if _table_sql(connection, legacy_table):
        raise RuntimeError("Maintenance Workstream FK migration target already exists")
    repaired_sql = _maintenance_workstream_repair_sql(table_sql)
    columns = [row[1] for row in source_info]
    column_list = ", ".join(_quote_identifier(column) for column in columns)
    before_rows = [
        tuple(row)
        for row in connection.execute(
            "SELECT {} FROM maintenance_runs ORDER BY id".format(column_list)
        )
    ]
    before_session_links = [
        tuple(row)
        for row in connection.execute(
            "SELECT id, maintenance_run_id FROM sessions "
            "WHERE maintenance_run_id IS NOT NULL ORDER BY id"
        )
    ]
    before_suggestion_links = [
        tuple(row)
        for row in connection.execute(
            "SELECT id, origin_run_id FROM suggestions "
            "WHERE origin_run_id IS NOT NULL ORDER BY id"
        )
    ]

    foreign_keys_enabled = bool(connection.execute("PRAGMA foreign_keys").fetchone()[0])
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("PRAGMA legacy_alter_table = ON")
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "ALTER TABLE maintenance_runs RENAME TO {}".format(
                _quote_identifier(legacy_table)
            )
        )
        connection.execute(repaired_sql)
        connection.execute(
            "INSERT INTO maintenance_runs ({columns}) "
            "SELECT {columns} FROM {legacy}".format(
                columns=column_list, legacy=_quote_identifier(legacy_table)
            )
        )
        target_info = [
            tuple(row)
            for row in connection.execute("PRAGMA table_info(maintenance_runs)")
        ]
        if target_info != source_info:
            raise RuntimeError(
                "Maintenance Workstream FK migration would change column metadata"
            )
        after_rows = [
            tuple(row)
            for row in connection.execute(
                "SELECT {} FROM maintenance_runs ORDER BY id".format(column_list)
            )
        ]
        if after_rows != before_rows:
            raise RuntimeError(
                "Maintenance Workstream FK migration changed Maintenance Run rows"
            )
        connection.execute("DROP TABLE {}".format(_quote_identifier(legacy_table)))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA legacy_alter_table = OFF")
        connection.execute(
            "PRAGMA foreign_keys = {}".format("ON" if foreign_keys_enabled else "OFF")
        )

    if not _maintenance_workstream_fk_exists(connection):
        raise RuntimeError(
            "Maintenance Workstream FK migration did not restore the contract"
        )
    after_session_links = [
        tuple(row)
        for row in connection.execute(
            "SELECT id, maintenance_run_id FROM sessions "
            "WHERE maintenance_run_id IS NOT NULL ORDER BY id"
        )
    ]
    after_suggestion_links = [
        tuple(row)
        for row in connection.execute(
            "SELECT id, origin_run_id FROM suggestions "
            "WHERE origin_run_id IS NOT NULL ORDER BY id"
        )
    ]
    if after_session_links != before_session_links:
        raise RuntimeError(
            "Maintenance Workstream FK migration changed Session Run links"
        )
    if after_suggestion_links != before_suggestion_links:
        raise RuntimeError(
            "Maintenance Workstream FK migration changed Suggestion Run links"
        )
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("Maintenance Workstream FK migration foreign key check failed")
    return True
