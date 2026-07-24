import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from .config import settings


SCHEMA_PATH = Path(__file__).with_name("schema.sql")
USAGE_ATTRIBUTION_VALUES = ("git_root", "workspace_path", "unassigned")
USAGE_ATTRIBUTION_BACKUP_SUFFIX = "-pre-usage-attribution-check-v1.bak"
MAINTENANCE_SESSION_CONTRACT_BACKUP_SUFFIX = (
    "-pre-maintenance-session-contract-v1.bak"
)
MAINTENANCE_WORKSTREAM_FK_BACKUP_SUFFIX = (
    "-pre-maintenance-workstream-fk-v1.bak"
)
EXTERNAL_RESOURCE_URL_SCOPE_BACKUP_SUFFIX = (
    "-pre-external-resource-url-scope-v1.bak"
)
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


def connect() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(settings.database_path), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


def init_db() -> None:
    with connect() as connection:
        external_resource_url_scope_needs_repair = bool(
            _table_sql(connection, "external_resources")
            and _external_resource_url_unique_exists(connection)
        )
        if external_resource_url_scope_needs_repair:
            _ensure_external_resource_url_scope_backup(
                connection, settings.database_path
            )
        usage_contract_table = _usage_contract_table(connection)
        usage_contract_exists = usage_contract_table is not None
        maintenance_workstream_fk_needs_repair = bool(
            _table_sql(connection, "maintenance_runs")
            and not _maintenance_workstream_fk_exists(connection)
        )
        if maintenance_workstream_fk_needs_repair:
            _ensure_maintenance_workstream_fk_backup(
                connection, settings.database_path
            )
        session_contract_needs_repair = bool(
            _table_sql(connection, "sessions")
            and not _maintenance_session_contract_exists(connection)
        )
        if session_contract_needs_repair:
            _ensure_maintenance_session_contract_backup(
                connection, settings.database_path
            )
        if usage_contract_exists and not _usage_attribution_check_exists(
            connection, usage_contract_table
        ):
            _ensure_usage_attribution_backup(connection, settings.database_path)
        _migrate_legacy_usage_table_name(connection)
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _run_compatible_migrations(connection)
        from .usage import ensure_default_price_snapshot

        ensure_default_price_snapshot(connection)
        if not usage_contract_exists:
            connection.execute(
                """
                UPDATE source_files
                SET status = 'stale'
                WHERE source_id IN (
                    SELECT id FROM sources WHERE kind IN ('claude', 'codex')
                )
                """
            )


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


def _quick_check_database(database_path: Path) -> None:
    connection = sqlite3.connect(str(database_path))
    try:
        results = [row[0] for row in connection.execute("PRAGMA quick_check")]
    finally:
        connection.close()
    if results != ["ok"]:
        raise RuntimeError("Schema migration backup failed quick_check")


def _ensure_usage_attribution_backup(
    connection: sqlite3.Connection, database_path: Path
) -> Path:
    backup_path = _usage_attribution_backup_path(database_path)
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


def _quote_identifier(value: str) -> str:
    return '"{}"'.format(value.replace('"', '""'))


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


def _index_key_columns(
    connection: sqlite3.Connection, index: str
) -> list[str]:
    return [
        row["name"]
        for row in connection.execute('PRAGMA index_xinfo("{}")'.format(index))
        if row["key"] and row["name"] is not None
    ]


def _migrate_schema_indexes(connection: sqlite3.Connection) -> None:
    redundant_indexes = (
        (
            "activity_events",
            "idx_events_session_sequence",
            ["session_id", "sequence"],
        ),
        ("local_resources", "idx_local_resources_path", ["path"]),
        (
            "checkpoint_resource_refs",
            "idx_checkpoint_resource_refs",
            ["checkpoint_id", "thread_id"],
        ),
    )
    indexes_to_drop = []
    for table, index, required_prefix in redundant_indexes:
        indexes = connection.execute(
            'PRAGMA index_list("{}")'.format(table)
        ).fetchall()
        if index not in {row["name"] for row in indexes}:
            continue
        covered = any(
            row["origin"] == "u"
            and _index_key_columns(connection, row["name"])[
                : len(required_prefix)
            ]
            == required_prefix
            for row in indexes
        )
        if not covered:
            raise RuntimeError(
                "Cannot remove {}: required UNIQUE index coverage is missing".format(
                    index
                )
            )
        indexes_to_drop.append(index)

    for index in indexes_to_drop:
        connection.execute('DROP INDEX "{}"'.format(index))

    for definition in (
        "CREATE INDEX IF NOT EXISTS idx_checkpoints_workstream_version "
        "ON checkpoints(workstream_id, version DESC)",
        "CREATE INDEX IF NOT EXISTS idx_documents_source "
        "ON context_documents(source_id)",
        "CREATE INDEX IF NOT EXISTS idx_documents_workspace "
        "ON context_documents(workspace_id, mtime_ns DESC)",
    ):
        connection.execute(definition)


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


def _run_compatible_migrations(
    connection: sqlite3.Connection, *, include_data_migrations: bool = True
) -> None:
    # The local index is rebuildable, but user-curated workstreams are not. Keep
    # upgrades additive so both kinds of data survive normal application updates.
    session_contract_changed = any(
        (
            _ensure_column(connection, "sessions", "git_branch", "TEXT"),
            _ensure_column(
                connection,
                "sessions",
                "session_role",
                "TEXT NOT NULL DEFAULT 'primary' "
                "CHECK(session_role IN ('primary', 'subsession'))",
            ),
            _ensure_column(connection, "sessions", "parent_external_id", "TEXT"),
            _ensure_column(
                connection,
                "sessions",
                "parent_session_id",
                "INTEGER REFERENCES sessions(id) ON DELETE SET NULL",
            ),
            _ensure_column(
                connection, "sessions", "session_class", "TEXT NOT NULL DEFAULT 'work'"
            ),
            _ensure_column(
                connection, "sessions", "index_policy", "TEXT NOT NULL DEFAULT 'full'"
            ),
            _ensure_column(connection, "sessions", "maintenance_run_id", "TEXT"),
        )
    )
    usage_normalizer_contract_changed = _ensure_column(
        connection, "source_files", "usage_contract_version", "TEXT"
    )
    atlassian_space_url_added = _ensure_column(
        connection,
        "atlassian_spaces",
        "canonical_url",
        "TEXT NOT NULL DEFAULT ''",
    )
    atlassian_space_coverage_added = _ensure_column(
        connection,
        "atlassian_spaces",
        "coverage",
        "TEXT NOT NULL DEFAULT 'selected-content'",
    )
    _drop_column(connection, "workspaces", "git_branch")

    for table, column, definition in (
        (
            "context_documents",
            "context_root_id",
            "INTEGER REFERENCES context_roots(id) ON DELETE SET NULL",
        ),
        (
            "context_documents",
            "content_type",
            "TEXT NOT NULL DEFAULT 'text/markdown'",
        ),
        ("context_roots", "source_type", "TEXT NOT NULL DEFAULT 'folder'"),
        ("context_roots", "readable", "INTEGER NOT NULL DEFAULT 1"),
        ("context_roots", "status", "TEXT NOT NULL DEFAULT 'ready'"),
        ("context_roots", "error", "TEXT"),
        ("workstream_links", "relation_type", "TEXT NOT NULL DEFAULT 'related-to'"),
        ("checkpoints", "based_on_activity_at", "TEXT"),
        ("checkpoints", "version", "INTEGER NOT NULL DEFAULT 1"),
        ("checkpoints", "updated_at", "TEXT"),
        ("maintenance_runs", "workstream_id", "INTEGER"),
        ("maintenance_runs", "task_type", "TEXT"),
        ("maintenance_runs", "runner", "TEXT NOT NULL DEFAULT 'claude'"),
        ("maintenance_runs", "cwd", "TEXT"),
        ("maintenance_runs", "pid", "INTEGER"),
        ("maintenance_runs", "manifest_path", "TEXT"),
        ("maintenance_runs", "prompt_path", "TEXT"),
        ("maintenance_runs", "stream_path", "TEXT"),
        ("maintenance_runs", "result_path", "TEXT"),
        ("maintenance_runs", "stderr_path", "TEXT"),
        ("maintenance_runs", "structured_result_json", "TEXT"),
        ("maintenance_runs", "suggestions_created", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "refresh_suggestions", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "mcp_call_budget", "INTEGER NOT NULL DEFAULT 20"),
        ("maintenance_runs", "mcp_calls_used", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "mcp_tool_calls_json", "TEXT"),
        ("maintenance_runs", "mcp_budget_exceeded", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "error", "TEXT"),
        ("maintenance_runs", "updated_at", "TEXT"),
        ("suggestions", "origin_run_id", "TEXT"),
        ("usage_records", "workspace_id_snapshot", "INTEGER"),
        ("usage_records", "project_key", "TEXT"),
        ("usage_records", "project_name_snapshot", "TEXT"),
        ("usage_records", "project_path_snapshot", "TEXT"),
        ("usage_records", "project_git_root_snapshot", "TEXT"),
        (
            "usage_records",
            "normalizer_version",
            "TEXT NOT NULL DEFAULT 'legacy-v1'",
        ),
        (
            "usage_model_prices",
            "long_context_threshold_tokens",
            "INTEGER CHECK(long_context_threshold_tokens IS NULL OR long_context_threshold_tokens > 0)",
        ),
        ("usage_model_prices", "long_context_input_usd_per_million", "TEXT"),
        ("usage_model_prices", "long_context_output_usd_per_million", "TEXT"),
        (
            "usage_model_prices",
            "long_context_cache_write_usd_per_million",
            "TEXT",
        ),
        (
            "usage_model_prices",
            "long_context_cache_read_usd_per_million",
            "TEXT",
        ),
    ):
        _ensure_column(connection, table, column, definition)

    _ensure_column(
        connection,
        "usage_records",
        "attribution_basis",
        "TEXT NOT NULL DEFAULT 'unassigned'",
    )
    usage_attributed_at_added = _ensure_column(
        connection, "usage_records", "attributed_at", "TEXT"
    )

    if include_data_migrations:
        if atlassian_space_url_added:
            connection.execute(
                """
                UPDATE atlassian_spaces
                SET canonical_url = (
                    SELECT atlassian_sites.canonical_base_url ||
                           CASE atlassian_spaces.service
                               WHEN 'jira' THEN '/projects/'
                               ELSE '/spaces/'
                           END ||
                           COALESCE(
                               atlassian_spaces.space_key,
                               atlassian_spaces.remote_id
                           ) ||
                           CASE atlassian_spaces.service
                               WHEN 'confluence' THEN '/overview'
                               ELSE ''
                           END
                    FROM atlassian_sites
                    WHERE atlassian_sites.id = atlassian_spaces.site_id
                )
                WHERE canonical_url = ''
                """
            )
        if atlassian_space_coverage_added:
            connection.execute(
                """
                UPDATE atlassian_spaces
                SET coverage = 'full-content'
                WHERE service = 'confluence'
                """
            )
        if session_contract_changed or usage_normalizer_contract_changed:
            connection.execute(
                """
                UPDATE source_files
                SET status = 'stale'
                WHERE source_id IN (
                    SELECT id FROM sources WHERE kind IN ('claude', 'codex')
                )
                """
            )

        connection.execute(
            "UPDATE checkpoints SET updated_at = COALESCE(updated_at, created_at)"
        )
        connection.execute(
            "UPDATE maintenance_runs SET updated_at = COALESCE(updated_at, created_at)"
        )
        if usage_attributed_at_added:
            connection.execute(
                """
                UPDATE usage_records
                SET attributed_at = imported_at
                WHERE attributed_at IS NULL
                """
            )
        _migrate_context_roots(connection)
        _repair_external_resource_url_scope(connection)
        _repair_usage_attribution_check(connection)
        _repair_maintenance_workstream_fk(connection)
        _repair_maintenance_session_contract(connection)

    _remove_unused_activity_event_metadata(connection)
    _migrate_schema_indexes(connection)

    connection.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_class
            ON sessions(session_class, last_event_at DESC);
        CREATE INDEX IF NOT EXISTS idx_sessions_role
            ON sessions(session_role, last_event_at DESC);
        CREATE INDEX IF NOT EXISTS idx_sessions_parent
            ON sessions(parent_session_id, last_event_at DESC);
        CREATE INDEX IF NOT EXISTS idx_threads_workstream
            ON threads(workstream_id, status, position);
        CREATE INDEX IF NOT EXISTS idx_thread_links_entity
            ON thread_links(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_workstream_links_entity
            ON workstream_links(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_suggestions_target
            ON suggestions(target_type, target_id, status);
        CREATE INDEX IF NOT EXISTS idx_maintenance_runs_workstream
            ON maintenance_runs(workstream_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_maintenance_runs_status
            ON maintenance_runs(status, updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_external_sync_runs_source_instance
            ON external_sync_runs(source_instance_id, maintenance_run_id);
        CREATE INDEX IF NOT EXISTS idx_external_sync_runs_scope
            ON external_sync_runs(requested_scope_kind, maintenance_run_id);
        CREATE INDEX IF NOT EXISTS idx_atlassian_sites_source
            ON atlassian_sites(source_instance_id, normalized_domain);
        CREATE INDEX IF NOT EXISTS idx_atlassian_spaces_site
            ON atlassian_spaces(site_id, service, name);
        CREATE INDEX IF NOT EXISTS idx_atlassian_items_site
            ON atlassian_items(site_id, service, coverage);
        CREATE INDEX IF NOT EXISTS idx_atlassian_items_space
            ON atlassian_items(space_id, service);
        CREATE INDEX IF NOT EXISTS idx_atlassian_item_urls_item
            ON atlassian_item_urls(external_resource_id, url_role);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_atlassian_item_urls_canonical
            ON atlassian_item_urls(external_resource_id)
            WHERE url_role = 'canonical';
        CREATE INDEX IF NOT EXISTS idx_atlassian_remote_state_check
            ON atlassian_item_remote_state(last_successful_at, last_outcome);
        CREATE INDEX IF NOT EXISTS idx_atlassian_item_classifications_classification
            ON atlassian_item_classifications(
                classification_id, external_resource_id
            );
        CREATE INDEX IF NOT EXISTS idx_suggestions_origin_run
            ON suggestions(origin_run_id, status);
        CREATE INDEX IF NOT EXISTS idx_documents_context_root
            ON context_documents(context_root_id, mtime_ns DESC);
        """
    )


def _migrate_context_roots(connection: sqlite3.Connection) -> None:
    root = settings.context_root.expanduser()
    root = root.resolve() if root.exists() else root
    root_rows = connection.execute(
        "SELECT id FROM context_roots LIMIT 1"
    ).fetchone()
    if not root_rows and root.is_dir():
        children = sorted(
            child for child in root.iterdir()
            if child.is_dir() and not child.name.startswith(".")
            and any(child.rglob("*.md"))
        )
        candidates = children or ([root] if any(root.glob("*.md")) else [])
        for candidate in candidates:
            connection.execute(
                "INSERT OR IGNORE INTO context_roots(path, label) VALUES (?, ?)",
                (str(candidate.resolve()), candidate.name or str(candidate)),
            )

    unassigned = connection.execute(
        "SELECT id, path FROM context_documents WHERE context_root_id IS NULL"
    ).fetchall()
    roots = connection.execute(
        "SELECT id, path FROM context_roots ORDER BY length(path) DESC"
    ).fetchall()
    for document in unassigned:
        document_path = Path(document["path"])
        for context_root in roots:
            root_path = Path(context_root["path"])
            try:
                relative_path = document_path.relative_to(root_path)
            except ValueError:
                continue
            connection.execute(
                """
                UPDATE context_documents
                SET context_root_id = ?, relative_path = ?
                WHERE id = ?
                """,
                (context_root["id"], str(relative_path), document["id"]),
            )
            break


@contextmanager
def transaction() -> Generator[sqlite3.Connection, None, None]:
    connection = connect()
    try:
        connection.execute("BEGIN")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
