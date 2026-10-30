"""Convert known Session-result tokens without rewriting derived Session data."""

import sqlite3
from pathlib import Path

from .runtime_storage import private_database


BACKUP_SUFFIX = "-pre-session-revision-v1.bak"
REVISION_CHECK = (
    "CHECK(session_contract_version IS NULL OR "
    "(typeof(session_contract_version) = 'integer' AND session_contract_version > 0))"
)
LEGACY_REVISIONS = {
    "codex": {
        "codex-session-v3-response-message-fallback-user-prompt-guardian": 3,
        "codex-session-v4-response-message-fallback-user-prompt-guardian-skill-observations": 4,
        "codex-session-v8-skill-reference-sessions": 8,
        "codex-session-v11-question-replies-and-context-blocks": 11,
        "codex-session-v12-empty-page-controls": 12,
    },
    "claude": {
        "claude-session-v1": 1,
        "claude-session-v2-skill-observations": 2,
        "claude-session-v6-skill-reference-sessions": 6,
        "claude-session-v7-message-phases": 7,
    },
}


def _table_info(connection):
    return connection.execute("PRAGMA table_info(source_files)").fetchall()


def session_revision_contract_current(connection):
    info = {row["name"]: row for row in _table_info(connection)}
    revision = info.get("session_contract_version")
    if revision is None or revision["type"].upper() != "INTEGER":
        return False
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='source_files'"
    ).fetchone()
    normalized = "".join(row["sql"].lower().split()) if row else ""
    return "".join(REVISION_CHECK.lower().split()) in normalized


def _converted_rows(connection):
    columns = {row["name"] for row in _table_info(connection)}
    if "session_contract_version" not in columns:
        return []
    source_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(sources)")
    }
    provider_column = "provider_kind" if "provider_kind" in source_columns else "kind"
    rows = connection.execute(
        "SELECT f.*, s.{} AS revision_provider FROM source_files f "
        "LEFT JOIN sources s ON s.id=f.source_id ORDER BY f.id".format(provider_column)
    ).fetchall()
    converted = []
    for row in rows:
        values = dict(row)
        provider = values.pop("revision_provider")
        if provider == "codex-company":
            provider = "codex"
        value = values["session_contract_version"]
        if value is None:
            revision = None
        elif type(value) is int and value > 0:
            revision = value
        elif isinstance(value, str) and value in LEGACY_REVISIONS.get(provider, {}):
            revision = LEGACY_REVISIONS[provider][value]
        else:
            raise RuntimeError(
                "Unrecognized Session revision; migration stopped without replacing results"
            )
        values["session_contract_version"] = revision
        converted.append(values)
    return converted


def prepare_session_revision_migration(connection, database_path):
    """Validate legacy values before startup mutations and retain a recovery copy."""
    info = _table_info(connection)
    if not info:
        return
    _converted_rows(connection)
    if session_revision_contract_current(connection):
        return
    path = Path(database_path)
    if not path.is_file():
        return
    backup = path.with_name(path.name + BACKUP_SUFFIX)
    if not backup.exists():
        private_database(backup)
        try:
            with sqlite3.connect(str(backup)) as target:
                connection.backup(target)
        except Exception:
            backup.unlink(missing_ok=True)
            raise
    with sqlite3.connect(str(backup)) as target:
        if target.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise RuntimeError("Session revision migration backup is not valid")


def migrate_session_revisions(connection):
    if session_revision_contract_current(connection):
        return
    rows = _converted_rows(connection)
    schema = Path(__file__).with_name("schema.sql").read_text()
    start = schema.index("CREATE TABLE IF NOT EXISTS source_files (")
    definition = schema[start : schema.index("\n);", start) + 3]
    table = "source_files_numeric_revision"
    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE name=?", (table,)
    ).fetchone():
        raise RuntimeError("Session revision migration target already exists")
    indexes = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='source_files' "
        "AND sql IS NOT NULL ORDER BY name"
    ).fetchall()
    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='trigger' AND tbl_name='source_files'"
    ).fetchone():
        raise RuntimeError("Unexpected source-file trigger; Session migration stopped")
    connection.execute("SAVEPOINT session_numeric_revision")
    try:
        connection.execute(definition.replace("source_files (", table + " (", 1))
        columns = [row["name"] for row in _table_info(connection)]
        expected = [
            row["name"] for row in connection.execute("PRAGMA table_info(" + table + ")")
        ]
        if set(columns) != set(expected):
            raise RuntimeError("Unexpected source-file shape; Session migration stopped")
        names = ",".join(columns)
        connection.executemany(
            "INSERT INTO {} ({}) VALUES ({})".format(
                table, names, ",".join("?" for _ in columns)
            ),
            [[row[column] for column in columns] for row in rows],
        )
        connection.execute("DROP TABLE source_files")
        connection.execute("ALTER TABLE " + table + " RENAME TO source_files")
        for index in indexes:
            connection.execute(index["sql"])
        if connection.execute("PRAGMA foreign_key_check(source_files)").fetchall():
            raise RuntimeError("Session revision migration foreign key check failed")
        if not session_revision_contract_current(connection):
            raise RuntimeError("Session revision migration did not restore its contract")
        connection.execute("RELEASE session_numeric_revision")
    except Exception:
        connection.execute("ROLLBACK TO session_numeric_revision")
        connection.execute("RELEASE session_numeric_revision")
        raise
