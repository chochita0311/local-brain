"""Usage table identity, attribution and historical constraint migrations."""

import re
import sqlite3
from pathlib import Path
from localbrain.persistence.migrations.support import (
    SCHEMA_PATH,
    _ensure_migration_backup,
    _quote_identifier,
    _table_sql,
)


USAGE_ATTRIBUTION_VALUES = ("git_root", "workspace_path", "unassigned")


USAGE_ATTRIBUTION_BACKUP_SUFFIX = "-pre-usage-attribution-check-v1.bak"


USAGE_ATTRIBUTION_CHECK = (
    "CHECK(attribution_basis IN ('git_root', 'workspace_path', 'unassigned'))"
)


USAGE_ATTRIBUTION_CHECK_PATTERN = re.compile(
    r"CHECK\s*\(\s*attribution_basis\s+IN\s*\(\s*'git_root'\s*,\s*"
    r"'workspace_path'\s*,\s*'unassigned'\s*\)\s*\)",
    flags=re.IGNORECASE,
)


USAGE_RECORDS_TABLE = "usage_records"


LEGACY_USAGE_FACTS_TABLE = "usage_facts"


LEGACY_USAGE_FACT_INDEXES = (
    "idx_usage_facts_session_time",
    "idx_usage_facts_source_time",
    "idx_usage_facts_model_time",
)


def _usage_contract_table(connection: sqlite3.Connection):
    canonical_exists = _table_sql(connection, USAGE_RECORDS_TABLE) is not None
    legacy_exists = _table_sql(connection, LEGACY_USAGE_FACTS_TABLE) is not None
    if canonical_exists and legacy_exists:
        raise RuntimeError(
            "Usage Record migration refused coexisting usage_records and "
            "legacy usage_facts tables"
        )
    if canonical_exists:
        return USAGE_RECORDS_TABLE
    if legacy_exists:
        return LEGACY_USAGE_FACTS_TABLE
    return None


def _migrate_legacy_usage_table_name(connection: sqlite3.Connection) -> bool:
    table = _usage_contract_table(connection)
    if table != LEGACY_USAGE_FACTS_TABLE:
        return False

    connection.execute("SAVEPOINT usage_record_table_rename")
    try:
        connection.execute("ALTER TABLE usage_facts RENAME TO usage_records")
        for index in LEGACY_USAGE_FACT_INDEXES:
            connection.execute("DROP INDEX IF EXISTS {}".format(index))
        _ensure_usage_record_indexes(connection)
        if _table_sql(connection, LEGACY_USAGE_FACTS_TABLE) is not None:
            raise RuntimeError("Usage Record migration left the legacy table behind")
        if _table_sql(connection, USAGE_RECORDS_TABLE) is None:
            raise RuntimeError("Usage Record migration did not create the canonical table")
        if connection.execute("PRAGMA foreign_key_check(usage_records)").fetchall():
            raise RuntimeError("Usage Record migration foreign key check failed")
        connection.execute("RELEASE SAVEPOINT usage_record_table_rename")
    except Exception:
        connection.execute("ROLLBACK TO SAVEPOINT usage_record_table_rename")
        connection.execute("RELEASE SAVEPOINT usage_record_table_rename")
        raise
    return True


def _usage_attribution_check_exists(
    connection: sqlite3.Connection, table: str = USAGE_RECORDS_TABLE
) -> bool:
    table_sql = _table_sql(connection, table)
    return bool(table_sql and USAGE_ATTRIBUTION_CHECK_PATTERN.search(table_sql))


def _usage_attribution_backup_path(database_path: Path) -> Path:
    return database_path.with_name(
        database_path.name + USAGE_ATTRIBUTION_BACKUP_SUFFIX
    )


def _ensure_usage_attribution_backup(
    connection: sqlite3.Connection, database_path: Path
) -> Path:
    backup_path = _usage_attribution_backup_path(database_path)
    return _ensure_migration_backup(connection, backup_path)


def _usage_attribution_repair_sql(table_sql: str, target_table: str) -> str:
    if USAGE_ATTRIBUTION_CHECK_PATTERN.search(table_sql):
        raise RuntimeError("Usage attribution CHECK already exists")

    column_pattern = re.compile(
        r"(\battribution_basis\s+TEXT\s+NOT\s+NULL\s+DEFAULT\s+'unassigned')",
        flags=re.IGNORECASE,
    )
    repaired_sql, replacements = column_pattern.subn(
        r"\1 " + USAGE_ATTRIBUTION_CHECK,
        table_sql,
        count=1,
    )
    if replacements != 1:
        raise RuntimeError(
            "Usage attribution migration found an unexpected column definition"
        )

    table_pattern = re.compile(
        r"^\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
        r"(?:\"usage_records\"|`usage_records`|\[usage_records\]|usage_records)"
        r"(?=\s|\()",
        flags=re.IGNORECASE,
    )
    repaired_sql, replacements = table_pattern.subn(
        "CREATE TABLE " + _quote_identifier(target_table), repaired_sql, count=1
    )
    if replacements != 1:
        raise RuntimeError(
            "Usage attribution migration found an unexpected table definition"
        )
    return repaired_sql


def _expected_usage_record_columns() -> set[str]:
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        return {
            row[1] for row in reference.execute("PRAGMA table_info(usage_records)")
        }
    finally:
        reference.close()


def _ensure_usage_record_indexes(connection: sqlite3.Connection) -> None:
    for definition in (
        "CREATE INDEX IF NOT EXISTS idx_usage_records_session_time "
        "ON usage_records(session_id, occurred_at)",
        "CREATE INDEX IF NOT EXISTS idx_usage_records_source_time "
        "ON usage_records(source_id, occurred_at)",
        "CREATE INDEX IF NOT EXISTS idx_usage_records_model_time "
        "ON usage_records(model_name, occurred_at)",
    ):
        connection.execute(definition)


def _repair_usage_attribution_check(connection: sqlite3.Connection) -> bool:
    table_sql = _table_sql(connection, "usage_records")
    if not table_sql or USAGE_ATTRIBUTION_CHECK_PATTERN.search(table_sql):
        return False

    invalid_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM usage_records
        WHERE attribution_basis IS NULL
           OR attribution_basis NOT IN (?, ?, ?)
        """,
        USAGE_ATTRIBUTION_VALUES,
    ).fetchone()[0]
    if invalid_count:
        raise RuntimeError(
            "Usage attribution migration refused {} invalid row(s)".format(
                invalid_count
            )
        )

    target_table = "usage_records__attribution_check_repair"
    if _table_sql(connection, target_table):
        raise RuntimeError("Usage attribution migration target already exists")
    repaired_sql = _usage_attribution_repair_sql(table_sql, target_table)
    source_info = [tuple(row) for row in connection.execute("PRAGMA table_info(usage_records)")]
    columns = [row[1] for row in source_info]
    if set(columns) != _expected_usage_record_columns():
        raise RuntimeError("Usage attribution migration found an unexpected table shape")
    column_list = ", ".join(_quote_identifier(column) for column in columns)
    quoted_target = _quote_identifier(target_table)

    connection.execute("SAVEPOINT usage_attribution_check_repair")
    try:
        connection.execute(repaired_sql)
        target_info = [
            tuple(row)
            for row in connection.execute(
                "PRAGMA table_info({})".format(quoted_target)
            )
        ]
        if target_info != source_info:
            raise RuntimeError(
                "Usage attribution migration would change column metadata"
            )

        connection.execute(
            "INSERT INTO {target} ({columns}) "
            "SELECT {columns} FROM usage_records".format(
                target=quoted_target, columns=column_list
            )
        )
        source_count = connection.execute(
            "SELECT COUNT(*) FROM usage_records"
        ).fetchone()[0]
        target_count = connection.execute(
            "SELECT COUNT(*) FROM {}".format(quoted_target)
        ).fetchone()[0]
        if target_count != source_count:
            raise RuntimeError("Usage attribution migration row count changed")

        missing_ids = connection.execute(
            "SELECT COUNT(*) FROM usage_records AS source "
            "LEFT JOIN {target} AS target ON target.id = source.id "
            "WHERE target.id IS NULL".format(target=quoted_target)
        ).fetchone()[0]
        extra_ids = connection.execute(
            "SELECT COUNT(*) FROM {target} AS target "
            "LEFT JOIN usage_records AS source ON source.id = target.id "
            "WHERE source.id IS NULL".format(target=quoted_target)
        ).fetchone()[0]
        if missing_ids or extra_ids:
            raise RuntimeError("Usage attribution migration Record IDs changed")

        source_difference = connection.execute(
            "SELECT EXISTS(SELECT {columns} FROM usage_records "
            "EXCEPT SELECT {columns} FROM {target})".format(
                columns=column_list, target=quoted_target
            )
        ).fetchone()[0]
        target_difference = connection.execute(
            "SELECT EXISTS(SELECT {columns} FROM {target} "
            "EXCEPT SELECT {columns} FROM usage_records)".format(
                columns=column_list, target=quoted_target
            )
        ).fetchone()[0]
        if source_difference or target_difference:
            raise RuntimeError("Usage attribution migration row values changed")

        connection.execute("DROP TABLE usage_records")
        connection.execute(
            "ALTER TABLE {} RENAME TO usage_records".format(quoted_target)
        )
        _ensure_usage_record_indexes(connection)
        if connection.execute("PRAGMA foreign_key_check(usage_records)").fetchall():
            raise RuntimeError("Usage attribution migration foreign key check failed")
        connection.execute("RELEASE SAVEPOINT usage_attribution_check_repair")
    except Exception:
        connection.execute("ROLLBACK TO SAVEPOINT usage_attribution_check_repair")
        connection.execute("RELEASE SAVEPOINT usage_attribution_check_repair")
        raise
    return True
