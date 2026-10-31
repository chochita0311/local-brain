"""Convert known Session-result tokens without rewriting derived Session data."""

import sqlite3
from pathlib import Path
from localbrain.foundation.files import private_database
from localbrain.foundation.paths import package_root


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


def _ddl_tokens(sql):
    """Separate SQLite comments/quoted values from active DDL words and symbols.

    This recognizes the bounded table contract below, not arbitrary equivalent
    SQL expressions. Comments are whitespace; literals keep case and escapes.
    """
    tokens = []
    index = 0
    while index < len(sql):
        char = sql[index]
        if char in " \t\n\r\f\ufeff":
            index += 1
        elif sql.startswith("--", index):
            end = sql.find("\n", index + 2)
            index = len(sql) if end < 0 else end + 1
        elif sql.startswith("/*", index):
            end = sql.find("*/", index + 2)
            index = len(sql) if end < 0 else end + 2
        elif char in "'\"`[":
            end_quote = "]" if char == "[" else char
            value = []
            index += 1
            while index < len(sql):
                if sql[index] == end_quote:
                    index += 1
                    if end_quote != "]" and index < len(sql) and sql[index] == end_quote:
                        value.append(end_quote)
                        index += 1
                        continue
                    break
                value.append(sql[index])
                index += 1
            else:
                raise RuntimeError("Unrecognized source-file DDL; Session migration stopped")
            text = "".join(value)
            tokens.append(("string", text) if char == "'" else ("identifier", text.lower()))
        elif char.isalpha() or char == "_" or ord(char) >= 128:
            start = index
            index += 1
            while index < len(sql) and (
                sql[index].isalnum() or sql[index] in "_$" or ord(sql[index]) >= 128
            ):
                index += 1
            tokens.append(("word", sql[start:index].lower()))
        else:
            tokens.append(("symbol", char))
            index += 1
    return tokens


_REVISION_CHECK_TOKENS = _ddl_tokens(REVISION_CHECK)


def _revision_checks(tokens):
    """Return whether each real top-level CHECK is the known revision rule."""
    checks = []
    depth = index = 0
    while index < len(tokens):
        token = tokens[index]
        if (depth == 1 and token == ("word", "check")
                and tokens[index + 1:index + 2] == [("symbol", "(")]):
            start = index
            index += 2
            check_depth = 1
            while index < len(tokens) and check_depth:
                if tokens[index] == ("symbol", "("):
                    check_depth += 1
                elif tokens[index] == ("symbol", ")"):
                    check_depth -= 1
                index += 1
            check = [
                ("word", value) if kind == "identifier" and value in
                {"session_contract_version", "typeof"} else (kind, value)
                for kind, value in tokens[start:index]
            ]
            checks.append(check_depth == 0 and check == _REVISION_CHECK_TOKENS)
            continue
        if token == ("symbol", "("):
            depth += 1
        elif token == ("symbol", ")"):
            depth -= 1
        index += 1
    return checks


def _table_info(connection):
    return connection.execute("PRAGMA table_info(source_files)").fetchall()


def _validate_source_file_shape(connection, target):
    """Refuse unknown constraints instead of silently removing them in a rebuild."""
    def columns(table):
        return {row["name"]: (row["type"].upper(), row["notnull"],
                              row["dflt_value"], row["pk"], row["hidden"])
                for row in connection.execute("PRAGMA table_xinfo(" + table + ")")}

    original, expected = columns("source_files"), columns(target)
    revision = original.get("session_contract_version")
    if revision and revision[0] in {"TEXT", "INTEGER"}:
        original["session_contract_version"] = ("INTEGER", *revision[1:])
    if original != expected:
        raise RuntimeError("Unexpected source-file columns; Session migration stopped")

    # The supported schema has no incoming FKs. DROP could otherwise cascade
    # into an unrecognized child table before the replacement is renamed.
    for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        table = row["name"].replace('"', '""')
        if any(foreign["table"].lower() == "source_files" for foreign in
               connection.execute('PRAGMA foreign_key_list("' + table + '")')):
            raise RuntimeError("Unexpected source-file references; Session migration stopped")

    def foreign_keys(table):
        fields = ("table", "from", "to", "on_update", "on_delete", "match")
        return sorted(tuple(row[field] for field in fields) for row in
                      connection.execute("PRAGMA foreign_key_list(" + table + ")"))

    def implicit_uniques(table):
        result = []
        for index in connection.execute("PRAGMA index_list(" + table + ")"):
            if index["origin"] not in {"u", "pk"}:
                continue
            # The name comes from SQLite, and quoting handles unusual legacy names.
            name = index["name"].replace('"', '""')
            keys = [(row["name"], row["desc"], row["coll"]) for row in
                    connection.execute('PRAGMA index_xinfo("' + name + '")')
                    if row["key"]]
            result.append((index["unique"], index["partial"], tuple(keys)))
        return sorted(result)

    sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='source_files'"
    ).fetchone()["sql"]
    tokens = _ddl_tokens(sql)
    unsupported_words = {"without", "deferrable", "collate", "autoincrement", "strict"}
    if (foreign_keys("source_files") != foreign_keys(target)
            or implicit_uniques("source_files") != implicit_uniques(target)
            or not all(_revision_checks(tokens))
            or any(kind == "word" and value in unsupported_words for kind, value in tokens)
            or any(tokens[index:index + 2] == [("word", "on"), ("word", "conflict")]
                   for index in range(len(tokens)))):
        raise RuntimeError("Unexpected source-file constraints; Session migration stopped")


def session_revision_contract_current(connection):
    info = {row["name"]: row for row in _table_info(connection)}
    revision = info.get("session_contract_version")
    if revision is None or revision["type"].upper() != "INTEGER":
        return False
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='source_files'"
    ).fetchone()
    return bool(row and any(_revision_checks(_ddl_tokens(row["sql"]))))


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
    schema = (package_root() / "schema.sql").read_text()
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
        _validate_source_file_shape(connection, table)
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
