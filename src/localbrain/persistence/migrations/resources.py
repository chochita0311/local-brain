"""Shared resource identity and external metadata schema migrations.

Preserving migration from feature-bound references to shared resource IDs."""

import hashlib
import os
import re
import sqlite3
from pathlib import Path
from localbrain.persistence.migrations.support import (
    SCHEMA_PATH,
    _ensure_migration_backup,
    _quote_identifier,
    _table_sql,
    _unique_index_columns,
)
from localbrain.resources.catalog import (
    bind_document,
    bind_entity,
    bind_external_link,
    bind_local_path,
    url_resource,
)


EXTERNAL_RESOURCE_URL_SCOPE_BACKUP_SUFFIX = (
    "-pre-external-resource-url-scope-v1.bak"
)


def _external_resource_url_unique_exists(
    connection: sqlite3.Connection,
) -> bool:
    return ["url"] in _unique_index_columns(connection, "external_resources")


def _external_resource_url_scope_backup_path(database_path: Path) -> Path:
    return database_path.with_name(
        database_path.name + EXTERNAL_RESOURCE_URL_SCOPE_BACKUP_SUFFIX
    )


def _ensure_external_resource_url_scope_backup(
    connection: sqlite3.Connection, database_path: Path
) -> Path:
    backup_path = _external_resource_url_scope_backup_path(database_path)
    return _ensure_migration_backup(connection, backup_path)


def _expected_external_resource_columns() -> list:
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        return [
            tuple(row)
            for row in reference.execute("PRAGMA table_info(external_resources)")
        ]
    finally:
        reference.close()


def _canonical_external_resources_sql() -> str:
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        row = reference.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = 'external_resources'"
        ).fetchone()
        if not row or not row[0]:
            raise RuntimeError("Canonical External Resource schema is unavailable")
        return row[0]
    finally:
        reference.close()


def _external_relation_snapshots(connection: sqlite3.Connection) -> dict:
    snapshots = {}
    for table, order_by in (
        ("workstream_links", "id"),
        ("thread_links", "id"),
        ("checkpoint_resource_refs", "id"),
    ):
        if not _table_sql(connection, table):
            continue
        snapshots[table] = [
            tuple(row)
            for row in connection.execute(
                "SELECT * FROM {} WHERE entity_type = 'external' ORDER BY {}".format(
                    _quote_identifier(table), order_by
                )
            )
        ]
    return snapshots


def _repair_external_resource_url_scope(
    connection: sqlite3.Connection,
) -> bool:
    if not _table_sql(connection, "external_resources"):
        return False
    if not _external_resource_url_unique_exists(connection):
        return False

    source_info = [
        tuple(row)
        for row in connection.execute("PRAGMA table_info(external_resources)")
    ]
    expected_info = _expected_external_resource_columns()
    if source_info != expected_info:
        raise RuntimeError(
            "External Resource URL migration found an unexpected table shape"
        )
    indexes = list(connection.execute("PRAGMA index_list(external_resources)"))
    if any(index["origin"] != "u" for index in indexes):
        raise RuntimeError(
            "External Resource URL migration found an unexpected explicit index"
        )
    if _unique_index_columns(connection, "external_resources") != [["url"]]:
        raise RuntimeError(
            "External Resource URL migration found unexpected uniqueness"
        )
    trigger_count = connection.execute(
        """
        SELECT COUNT(*) FROM sqlite_master
        WHERE type = 'trigger' AND tbl_name = 'external_resources'
        """
    ).fetchone()[0]
    if trigger_count:
        raise RuntimeError(
            "External Resource URL migration found an unexpected trigger"
        )

    legacy_table = "external_resources__url_scope_legacy"
    if _table_sql(connection, legacy_table):
        raise RuntimeError("External Resource URL migration target already exists")

    columns = [row[1] for row in source_info]
    column_list = ", ".join(_quote_identifier(column) for column in columns)
    before_rows = [
        tuple(row)
        for row in connection.execute(
            "SELECT {} FROM external_resources ORDER BY id".format(column_list)
        )
    ]
    before_relations = _external_relation_snapshots(connection)
    canonical_sql = _canonical_external_resources_sql()
    foreign_keys_enabled = bool(connection.execute("PRAGMA foreign_keys").fetchone()[0])

    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("PRAGMA legacy_alter_table = ON")
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "ALTER TABLE external_resources RENAME TO {}".format(
                _quote_identifier(legacy_table)
            )
        )
        connection.execute(canonical_sql)
        connection.execute(
            "INSERT INTO external_resources ({columns}) "
            "SELECT {columns} FROM {legacy}".format(
                columns=column_list, legacy=_quote_identifier(legacy_table)
            )
        )
        after_rows = [
            tuple(row)
            for row in connection.execute(
                "SELECT {} FROM external_resources ORDER BY id".format(column_list)
            )
        ]
        if after_rows != before_rows:
            raise RuntimeError(
                "External Resource URL migration changed External Resource rows"
            )
        if _external_relation_snapshots(connection) != before_relations:
            raise RuntimeError(
                "External Resource URL migration changed Resource relations"
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

    if _external_resource_url_unique_exists(connection):
        raise RuntimeError(
            "External Resource URL migration did not remove global uniqueness"
        )
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("External Resource URL migration foreign key check failed")
    return True


BACKUP_SUFFIX = "-pre-shared-resources-v1.bak"
RESOURCE_TABLES = (
    "reference_resources", "resource_documents", "resource_local_paths",
    "resource_external_links",
)
EXTERNAL_PAYLOAD_TABLES = (
    ("atlassian_item_content", "external_resource_content"),
    ("atlassian_item_local_state", "external_resource_notes"),
)


def _exists(connection, table):
    return connection.execute(
        "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def _columns(connection, table):
    return [row[1] for row in connection.execute('PRAGMA table_info("{}")'.format(table))]


def shared_resource_contract_current(connection):
    if not all(_exists(connection, table) for table in RESOURCE_TABLES):
        return False
    if any(_exists(connection, old) for old, _ in EXTERNAL_PAYLOAD_TABLES):
        return False
    if not _exists(connection, "session_reference_evidence") or any(not _exists(connection, new) for _, new in EXTERNAL_PAYLOAD_TABLES):
        return False
    for table in ("workstream_links", "thread_links"):
        if _exists(connection, table) and "resource_id" not in _columns(connection, table):
            return False
    targets = {row[2] for row in connection.execute("PRAGMA foreign_key_list(session_reference_evidence)")}
    payload_targets = [{row[2] for row in connection.execute("PRAGMA foreign_key_list(" + table + ")")} for _, table in EXTERNAL_PAYLOAD_TABLES]
    return targets == {"sessions", "reference_resources"} and all(t == {"external_resources"} for t in payload_targets)


def shared_resource_migration_required(connection):
    return _exists(connection, "sessions") and not shared_resource_contract_current(connection)


def ensure_shared_resource_backup(connection, database_path):
    path = Path(str(database_path) + BACKUP_SUFFIX)
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("Invalid shared-resource recovery copy")
    else:
        target = sqlite3.connect(str(path))
        try:
            os.chmod(path, 0o600)
            connection.backup(target)
        except Exception:
            target.close()
            path.unlink(missing_ok=True)
            raise
        else:
            target.close()
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as check:
        if check.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("Shared-resource recovery copy failed quick_check")
    return path


def _ddl(table):
    match = re.search(
        r"CREATE TABLE IF NOT EXISTS " + re.escape(table) + r" \(.*?\n\);",
        SCHEMA_PATH.read_text(encoding="utf-8"), re.S,
    )
    if match is None:
        raise RuntimeError("Missing shared-resource schema contract: " + table)
    return match.group(0)


def _legacy_resource(connection, row):
    if row["target_kind"] == "context_document":
        return bind_document(connection, row["context_document_id"])
    resource_id = url_resource(connection, row["normalized_url"])
    if resource_id is not None:
        return resource_id
    # An unsafe legacy destination remains evidence, but never becomes an
    # active link. Its original value and observation are preserved verbatim.
    locator = row["normalized_url"]
    identity = "unavailable-url:" + hashlib.sha256(locator.encode("utf-8")).hexdigest()
    connection.execute(
        "INSERT OR IGNORE INTO reference_resources(identity_key, kind, locator) VALUES (?, 'url', ?)",
        (identity, locator),
    )
    return int(connection.execute("SELECT id FROM reference_resources WHERE identity_key = ?", (identity,)).fetchone()[0])


def _migrate_evidence(connection):
    if not _exists(connection, "session_reference_evidence"):
        return
    if "resource_id" in _columns(connection, "session_reference_evidence"):
        return
    rows = [dict(row) for row in connection.execute("SELECT * FROM session_reference_evidence ORDER BY id")]
    old_totals = {}
    for row in rows:
        old_totals.setdefault(row["session_id"], set()).add(row["target_key"])
    connection.execute("ALTER TABLE session_reference_evidence RENAME TO legacy_session_reference_evidence")
    connection.execute(_ddl("session_reference_evidence"))
    columns = _columns(connection, "session_reference_evidence")
    statement = "INSERT INTO session_reference_evidence ({}) VALUES ({})".format(
        ", ".join(columns), ", ".join("?" for _ in columns),
    )
    for row in rows:
        resource_id = _legacy_resource(connection, row)
        row["resource_id"] = resource_id
        row["target_key"] = connection.execute(
            "SELECT identity_key FROM reference_resources WHERE id = ?", (resource_id,)
        ).fetchone()[0]
        connection.execute(statement, [row[column] for column in columns])
    if connection.execute("SELECT COUNT(*) FROM session_reference_evidence").fetchone()[0] != len(rows):
        raise RuntimeError("Session reference migration lost evidence")
    connection.execute("DROP TABLE legacy_session_reference_evidence")
    for session_id in old_totals:
        retained = connection.execute(
            "SELECT COUNT(DISTINCT target_key) FROM session_reference_evidence WHERE session_id = ?", (session_id,)
        ).fetchone()[0]
        # Fully observed sets can be recounted exactly. A bounded partial set
        # keeps its old observation total and is marked stale until rescanned.
        connection.execute(
            """UPDATE session_reference_scans
            SET retained_target_count = ?,
                observed_target_count = CASE WHEN status = 'ok' THEN ? ELSE MAX(observed_target_count, ?) END,
                error_code = CASE WHEN status = 'partial' THEN 'resource-identity-migration' ELSE error_code END,
                error_message = CASE WHEN status = 'partial' THEN 'Reference identities changed; rescan required' ELSE error_message END,
                status = CASE WHEN status = 'partial' THEN 'error' ELSE status END
            WHERE session_id = ?""", (retained, retained, retained, session_id),
        )


def _migrate_payload(connection, old, new):
    if not _exists(connection, old):
        return
    connection.execute(_ddl(new))
    old_columns = _columns(connection, old)
    if old_columns != _columns(connection, new):
        raise RuntimeError("Unrecognized external content contract; original content preserved")
    columns = ", ".join(old_columns)
    connection.execute("INSERT OR IGNORE INTO {new} ({columns}) SELECT {columns} FROM {old}".format(columns=columns, old=old, new=new))
    unmatched = connection.execute(
        "SELECT {columns} FROM {old} EXCEPT SELECT {columns} FROM {new}".format(columns=columns, old=old, new=new)
    ).fetchone()
    if unmatched is not None:
        raise RuntimeError("Conflicting external content; original content preserved")
    connection.execute("DROP TABLE " + old)


def _migrate_content(connection):
    for old, new in EXTERNAL_PAYLOAD_TABLES:
        _migrate_payload(connection, old, new)


def migrate_shared_resources(connection):
    """Run on the caller connection; all changes roll back together on error."""
    if shared_resource_contract_current(connection):
        return False
    connection.execute("SAVEPOINT shared_resource_migration")
    try:
        for table in RESOURCE_TABLES:
            connection.execute(_ddl(table))
        for table, binder in (
            ("context_documents", bind_document), ("local_resources", bind_local_path),
            ("external_resources", bind_external_link),
        ):
            if _exists(connection, table):
                for row in connection.execute("SELECT id FROM " + table + " ORDER BY id").fetchall():
                    binder(connection, row[0])
        for table in ("workstream_links", "thread_links"):
            if not _exists(connection, table):
                continue
            if "resource_id" not in _columns(connection, table):
                connection.execute("ALTER TABLE " + table + " ADD COLUMN resource_id INTEGER REFERENCES reference_resources(id) ON DELETE RESTRICT")
            for row in connection.execute("SELECT id, entity_type, entity_id FROM " + table).fetchall():
                try:
                    resource_id = bind_entity(connection, row["entity_type"], row["entity_id"])
                except (ValueError, LookupError):
                    continue  # Retain unresolved historical organization links.
                connection.execute("UPDATE " + table + " SET resource_id = ? WHERE id = ?", (resource_id, row["id"]))
        _migrate_evidence(connection)
        _migrate_content(connection)
        for table in RESOURCE_TABLES + ("session_reference_evidence", "external_resource_content", "external_resource_notes"):
            if _exists(connection, table) and connection.execute('PRAGMA foreign_key_check("{}")'.format(table)).fetchone():
                raise RuntimeError("Shared-resource migration failed foreign_key_check: " + table)
    except Exception:
        connection.execute("ROLLBACK TO shared_resource_migration")
        connection.execute("RELEASE shared_resource_migration")
        raise
    connection.execute("RELEASE shared_resource_migration")
    return True
