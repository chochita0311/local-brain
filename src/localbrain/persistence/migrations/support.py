"""Schema inspection and preserving backup primitives shared by migrations."""

import sqlite3
from pathlib import Path
from localbrain.foundation.paths import package_root


SCHEMA_PATH = package_root() / "schema.sql"


def _column_names(connection: sqlite3.Connection, table: str) -> set:
    return {row["name"] for row in connection.execute("PRAGMA table_info(" + table + ")")}


def _ensure_column(
    connection: sqlite3.Connection, table: str, column: str, definition: str
) -> bool:
    if column in _column_names(connection, table):
        return False
    connection.execute(
        "ALTER TABLE {} ADD COLUMN {} {}".format(table, column, definition)
    )
    return True


def _drop_column(connection: sqlite3.Connection, table: str, column: str) -> bool:
    if column not in _column_names(connection, table):
        return False
    connection.execute("ALTER TABLE {} DROP COLUMN {}".format(table, column))
    return True


def _table_sql(connection: sqlite3.Connection, table: str):
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row["sql"] if row else None


def _normalized_schema_sql(value) -> str:
    return " ".join(str(value or "").split())


def _schema_object_sql(
    connection: sqlite3.Connection, object_type: str, name: str
):
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = ? AND name = ?",
        (object_type, name),
    ).fetchone()
    return _normalized_schema_sql(row["sql"] if row else None)


def _table_contract_signature(
    connection: sqlite3.Connection, table: str
) -> tuple:
    return (
        _schema_object_sql(connection, "table", table),
        tuple(
            tuple(row)
            for row in connection.execute(
                'PRAGMA table_info("{}")'.format(table)
            )
        ),
        tuple(
            sorted(
                tuple(row)
                for row in connection.execute(
                    'PRAGMA foreign_key_list("{}")'.format(table)
                )
            )
        ),
    )


def _index_contract_signature(
    connection: sqlite3.Connection, index: str
) -> tuple:
    return (
        _schema_object_sql(connection, "index", index),
        tuple(
            tuple(row)
            for row in connection.execute(
                'PRAGMA index_xinfo("{}")'.format(index)
            )
        ),
    )


def _unique_index_columns(
    connection: sqlite3.Connection, table: str
) -> list[list[str]]:
    return [
        [
            column["name"]
            for column in connection.execute(
                "PRAGMA index_info({})".format(_quote_identifier(index["name"]))
            )
        ]
        for index in connection.execute(
            "PRAGMA index_list({})".format(_quote_identifier(table))
        )
        if bool(index["unique"])
    ]


def _quote_identifier(value: str) -> str:
    return '"{}"'.format(value.replace('"', '""'))


def _quick_check_database(database_path: Path) -> None:
    connection = sqlite3.connect(str(database_path))
    try:
        results = [row[0] for row in connection.execute("PRAGMA quick_check")]
    finally:
        connection.close()
    if results != ["ok"]:
        raise RuntimeError("Schema migration backup failed quick_check")


def _ensure_migration_backup(connection: sqlite3.Connection, backup_path: Path) -> Path:
    if backup_path.exists():
        _quick_check_database(backup_path)
        return backup_path

    backup_connection = sqlite3.connect(str(backup_path))
    try:
        connection.backup(backup_connection)
    except Exception:
        backup_connection.close()
        backup_path.unlink(missing_ok=True)
        raise
    else:
        backup_connection.close()
    try:
        _quick_check_database(backup_path)
    except Exception:
        backup_path.unlink(missing_ok=True)
        raise
    return backup_path
