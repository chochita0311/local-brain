"""Atlassian catalog schema history, independent of optional feature code."""

import sqlite3
from pathlib import Path
from localbrain.persistence.migrations.support import (
    SCHEMA_PATH,
    _ensure_migration_backup,
    _index_contract_signature,
    _quote_identifier,
    _schema_object_sql,
    _table_contract_signature,
    _table_sql,
)


ATLASSIAN_SITE_ACCESS_BACKUP_SUFFIX = "-pre-atlassian-site-access-v1.bak"


STRUCTURE_REFERENCE_TABLES = (
    "atlassian_structure_references",
    "atlassian_structure_reference_urls",
    "atlassian_structure_reference_evidence",
)


STRUCTURE_REFERENCE_INDEXES = (
    "idx_atlassian_structure_references_site",
    "idx_atlassian_structure_reference_urls_reference",
    "idx_atlassian_structure_reference_urls_canonical",
    "idx_atlassian_structure_reference_evidence_reference",
    "idx_atlassian_structure_reference_evidence_session",
    "idx_atlassian_structure_reference_evidence_document",
)


def _canonical_structure_reference_contract() -> tuple[dict, dict]:
    reference = sqlite3.connect(":memory:")
    reference.row_factory = sqlite3.Row
    try:
        reference.execute("PRAGMA foreign_keys = ON")
        reference.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        tables = {
            table: _table_contract_signature(reference, table)
            for table in STRUCTURE_REFERENCE_TABLES
        }
        indexes = {
            index: _index_contract_signature(reference, index)
            for index in STRUCTURE_REFERENCE_INDEXES
        }
        return tables, indexes
    finally:
        reference.close()


def _validate_preexisting_structure_reference_contract(
    connection: sqlite3.Connection,
) -> None:
    present = {
        table for table in STRUCTURE_REFERENCE_TABLES if _table_sql(connection, table)
    }
    if not present:
        return
    if present != set(STRUCTURE_REFERENCE_TABLES):
        raise RuntimeError(
            "Unexpected partial Atlassian Structure Reference schema"
        )
    canonical_tables, canonical_indexes = (
        _canonical_structure_reference_contract()
    )
    if any(
        _table_contract_signature(connection, table) != canonical_tables[table]
        for table in STRUCTURE_REFERENCE_TABLES
    ):
        raise RuntimeError(
            "Unexpected Atlassian Structure Reference table contract"
        )
    if any(
        _schema_object_sql(connection, "index", index)
        and _index_contract_signature(connection, index)
        != canonical_indexes[index]
        for index in STRUCTURE_REFERENCE_INDEXES
    ):
        raise RuntimeError(
            "Unexpected Atlassian Structure Reference index contract"
        )


def _validate_structure_reference_contract(
    connection: sqlite3.Connection,
) -> None:
    canonical_tables, canonical_indexes = (
        _canonical_structure_reference_contract()
    )
    if any(
        _table_contract_signature(connection, table) != canonical_tables[table]
        for table in STRUCTURE_REFERENCE_TABLES
    ):
        raise RuntimeError(
            "Canonical Atlassian Structure Reference tables are unavailable"
        )
    if any(
        _index_contract_signature(connection, index)
        != canonical_indexes[index]
        for index in STRUCTURE_REFERENCE_INDEXES
    ):
        raise RuntimeError(
            "Canonical Atlassian Structure Reference indexes are unavailable"
        )


def _atlassian_site_access_contract_exists(
    connection: sqlite3.Connection,
) -> bool:
    if not _table_sql(connection, "atlassian_sites"):
        return False
    source_column = next(
        (
            row
            for row in connection.execute(
                "PRAGMA table_info(atlassian_sites)"
            )
            if row["name"] == "source_instance_id"
        ),
        None,
    )
    if source_column is None or bool(source_column["notnull"]):
        return False
    return any(
        row["from"] == "source_instance_id"
        and row["table"] == "external_source_instances"
        and row["to"] == "id"
        and row["on_delete"].upper() == "SET NULL"
        for row in connection.execute(
            "PRAGMA foreign_key_list(atlassian_sites)"
        )
    )


def _atlassian_site_access_backup_path(database_path: Path) -> Path:
    return database_path.with_name(
        database_path.name + ATLASSIAN_SITE_ACCESS_BACKUP_SUFFIX
    )


def _ensure_atlassian_site_access_backup(
    connection: sqlite3.Connection, database_path: Path
) -> Path:
    backup_path = _atlassian_site_access_backup_path(database_path)
    return _ensure_migration_backup(connection, backup_path)


def _canonical_atlassian_sites_sql() -> str:
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        row = reference.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = 'atlassian_sites'"
        ).fetchone()
        if not row or not row[0]:
            raise RuntimeError("Canonical Atlassian Site schema is unavailable")
        return row[0]
    finally:
        reference.close()


def _repair_atlassian_site_access_contract(
    connection: sqlite3.Connection,
) -> bool:
    if _atlassian_site_access_contract_exists(connection):
        return False
    if not _table_sql(connection, "atlassian_sites"):
        return False
    source_info = [
        tuple(row)
        for row in connection.execute("PRAGMA table_info(atlassian_sites)")
    ]
    columns = [row[1] for row in source_info]
    expected_columns = [
        "id",
        "source_instance_id",
        "normalized_domain",
        "display_name",
        "remote_site_id",
        "canonical_base_url",
        "created_at",
        "updated_at",
    ]
    if columns != expected_columns:
        raise RuntimeError(
            "Atlassian Site access migration found an unexpected table shape"
        )
    legacy_table = "atlassian_sites__required_access_legacy"
    if _table_sql(connection, legacy_table):
        raise RuntimeError(
            "Atlassian Site access migration target already exists"
        )
    column_list = ", ".join(_quote_identifier(column) for column in columns)
    before_rows = [
        tuple(row)
        for row in connection.execute(
            "SELECT {} FROM atlassian_sites ORDER BY id".format(column_list)
        )
    ]
    canonical_sql = _canonical_atlassian_sites_sql()
    foreign_keys_enabled = bool(
        connection.execute("PRAGMA foreign_keys").fetchone()[0]
    )
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("PRAGMA legacy_alter_table = ON")
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "ALTER TABLE atlassian_sites RENAME TO {}".format(
                _quote_identifier(legacy_table)
            )
        )
        connection.execute(canonical_sql)
        connection.execute(
            "INSERT INTO atlassian_sites ({columns}) "
            "SELECT {columns} FROM {legacy}".format(
                columns=column_list,
                legacy=_quote_identifier(legacy_table),
            )
        )
        after_rows = [
            tuple(row)
            for row in connection.execute(
                "SELECT {} FROM atlassian_sites ORDER BY id".format(
                    column_list
                )
            )
        ]
        if after_rows != before_rows:
            raise RuntimeError(
                "Atlassian Site access migration changed retained Site rows"
            )
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
            "PRAGMA foreign_keys = {}".format(
                "ON" if foreign_keys_enabled else "OFF"
            )
        )
    if not _atlassian_site_access_contract_exists(connection):
        raise RuntimeError(
            "Atlassian Site access migration did not restore the contract"
        )
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError(
            "Atlassian Site access migration foreign key check failed"
        )
    return True
