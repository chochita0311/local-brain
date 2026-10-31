"""Source registry identity and configuration schema history.

One-time upgrade from profile aliases to the existing source primary key.

Old names are read only while upgrading. No alias lookup, replacement identifier,
or mapping table survives the transaction.
"""

import base64
import hashlib
import json
import re
import sqlite3
from contextlib import nullcontext
from pathlib import Path
from localbrain.foundation.preferences import PreferencesError, atomic_private_write, tomllib
from localbrain.persistence.migrations.support import (
    SCHEMA_PATH,
    _ensure_migration_backup,
    _table_sql,
)
from localbrain.sources.registry import session_sources_text


SOURCE_PROVIDER_IDENTITY_BACKUP_SUFFIX = "-pre-source-primary-key-v1.bak"


def _source_provider_identity_contract_exists(
    connection: sqlite3.Connection,
) -> bool:
    if not _table_sql(connection, "sources"):
        return False
    columns = {
        row["name"]: row
        for row in connection.execute("PRAGMA table_info(sources)")
    }
    provider = columns.get("provider_kind")
    return bool(
        provider
        and provider["notnull"]
        and "kind" not in columns
    )


def _source_provider_identity_backup_path(database_path: Path) -> Path:
    return database_path.with_name(
        database_path.name + SOURCE_PROVIDER_IDENTITY_BACKUP_SUFFIX
    )


def _ensure_source_provider_identity_backup(
    connection: sqlite3.Connection, database_path: Path
) -> Path:
    backup_path = _source_provider_identity_backup_path(database_path)
    return _ensure_migration_backup(connection, backup_path)


def _repair_source_provider_identity_contract(connection: sqlite3.Connection, config) -> bool:
    return migrate_registry(connection, config, SCHEMA_PATH.read_text(encoding="utf-8"))


def _columns(connection, table):
    return [row["name"] for row in connection.execute("PRAGMA table_info(" + table + ")")]


def upgrade_config(connection, config):
    """Upgrade a valid v1 file in the caller's transaction; return rollback data."""
    path = config.session_sources_path or config.data_dir / "session-sources.toml"
    if not path.exists():
        return None
    before = path.read_bytes()
    try:
        raw = tomllib.loads(before.decode("utf-8"))
    except (ValueError, UnicodeError):
        return None  # The ordinary reader reports the preserved invalid file.
    if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        return None
    if set(raw) != {"schema_version", "session_sources"} or not isinstance(raw["session_sources"], list):
        raise PreferencesError("기존 세션 소스 설정 형식을 확인해 주세요. 파일은 보존했습니다.")
    has_alias = "kind" in _columns(connection, "sources")
    rows = [dict(row) for row in connection.execute("SELECT * FROM sources ORDER BY id")]
    by_alias = {row["kind"]: row for row in rows} if has_alias else {}
    entries, seen, roots = [], set(), []
    allowed = {"source_key", "provider_kind", "display_label", "root", "agent_home", "enabled"}
    for old in raw["session_sources"]:
        if not isinstance(old, dict) or not allowed - {"agent_home", "enabled"} <= set(old) or not set(old) <= allowed:
            raise PreferencesError("기존 프로필 항목을 확인해 주세요. 파일은 보존했습니다.")
        key, provider, label, root_value = (old[k] for k in ("source_key", "provider_kind", "display_label", "root"))
        if (not isinstance(key, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key)
                or len(key) > 64 or key in seen or not isinstance(provider, str) or provider not in {"codex", "claude"}
                or not isinstance(label, str) or not 1 <= len(label.strip()) <= 160
                or not isinstance(root_value, str) or not 1 <= len(root_value.strip()) <= 4096
                or type(old.get("enabled", True)) is not bool
                or not isinstance(old.get("agent_home", ""), str) or len(old.get("agent_home", "")) > 4096
                or ("agent_home" in old and not old["agent_home"].strip())):
            raise PreferencesError("기존 프로필 ID·도구·이름·경로를 확인해 주세요. 파일은 보존했습니다.")
        seen.add(key)
        root = Path(root_value).expanduser()
        if not root.is_absolute():
            root = path.parent / root
        root = root.resolve()
        if old.get("enabled", True):
            if any(root == other or root in other.parents or other in root.parents for other in roots):
                raise PreferencesError("기존 세션 소스 경로가 겹칩니다. 파일은 보존했습니다.")
            roots.append(root)
        row = by_alias.get(key)
        if not has_alias:
            matches = [r for r in rows if r["provider_kind"] == provider and Path(r["root_path"]).expanduser().resolve() == root]
            if len(matches) > 1:
                raise PreferencesError("기존 경로의 프로필을 하나로 확인할 수 없습니다.")
            row = matches[0] if matches else None
        if row and (row.get("provider_kind", row.get("kind")) != provider or Path(row["root_path"]).expanduser().resolve() != root):
            raise PreferencesError("기존 프로필의 도구·경로가 일치하지 않습니다. 파일은 보존했습니다.")
        if row is None:
            fields, values = ["provider_kind", "name", "root_path"], [provider, label.strip(), str(root)]
            if has_alias:
                fields.insert(0, "kind"); values.insert(0, key)
            cursor = connection.execute("INSERT INTO sources(" + ",".join(fields) + ") VALUES (" + ",".join("?" for _ in values) + ")", values)
            row = {"id": cursor.lastrowid, "profile_color": None}
        entry = {k: v for k, v in old.items() if k != "source_key"}
        entry.update(source_id=row["id"], color=row.get("profile_color") or
                     ("blue" if key == "codex-company" else "orange" if provider == "claude" else "green"))
        entries.append(entry)
    entries.sort(key=lambda entry: entry["source_id"])
    after = session_sources_text(entries).encode()
    if path.read_bytes() != before:
        raise PreferencesError("이전 중 설정 파일이 변경되었습니다. 현재 파일을 보존했습니다.")
    recovery = (path, before, after)
    try:
        atomic_private_write(path, after)
    except Exception:
        restore_config(recovery)
        raise
    return recovery


def restore_config(recovery):
    if recovery is None:
        return
    path, before, after = recovery
    current = path.read_bytes()
    if current == before:
        return
    if current != after:
        raise PreferencesError("이전 중 설정이 별도로 변경되었습니다. 현재 파일을 보존했습니다.")
    atomic_private_write(path, before)


def _table_definition(schema, table):
    return re.search(r"CREATE TABLE IF NOT EXISTS " + table + r" \([\s\S]*?\n\);", schema).group()


def _replace_table(connection, schema, table, rows):
    """FKs are disabled by the enclosing migration; IDs and child FKs stay fixed."""
    temporary = table + "__pk_upgrade"
    if _columns(connection, temporary):
        raise RuntimeError("An unfinished source identity upgrade table already exists")
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='trigger' AND tbl_name=?", (table,)).fetchone():
        raise RuntimeError("Source identity upgrade found an unexpected trigger")
    indexes = [row[0] for row in connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL", (table,))]
    connection.execute(_table_definition(schema, table).replace(table, temporary, 1))
    columns = set(_columns(connection, temporary))
    removed = {"sources": {"kind", "enabled"}, "skill_observations": {"source_key"}}.get(table, set())
    if set(_columns(connection, table)) - columns - removed:
        raise RuntimeError("Source identity upgrade found unexpected columns; database preserved")
    for row in rows:
        values = {key: value for key, value in row.items() if key in columns}
        connection.execute('INSERT INTO "' + temporary + '" (' + ','.join('"' + key + '"' for key in values) +
                           ') VALUES (' + ','.join('?' for _ in values) + ')', tuple(values.values()))
    connection.execute('DROP TABLE "' + table + '"')
    connection.execute('ALTER TABLE "' + temporary + '" RENAME TO "' + table + '"')
    for statement in indexes:
        if table == "skill_observations":
            statement = statement.replace("source_key", "source_id")
        connection.execute(statement)


def _episode_key(source, external):
    parts = (str(source).encode(), external.encode())
    return "session:" + hashlib.sha256(b"".join(len(p).to_bytes(8, "big") + p for p in parts)).hexdigest()


def _recover_reconnect(connection, config):
    """Finish an interrupted old reconnect before removing its alias column."""
    journal = config.data_dir / "source-reconnect.json"
    if not journal.exists():
        return
    value = json.loads(journal.read_text(encoding="utf-8"))
    path = config.session_sources_path or config.data_dir / "session-sources.toml"
    current = path.read_bytes()
    original = base64.b64decode(value["before"], validate=True)
    if current != original and hashlib.sha256(current).hexdigest() != value["after_sha256"]:
        raise PreferencesError("중단된 소스 재연결 후 설정이 변경되었습니다. 파일과 복구 기록을 보존했습니다.")
    if "source_id" in value:
        row = connection.execute("SELECT root_path FROM sources WHERE id=?", (value["source_id"],)).fetchone()
    else:
        row = connection.execute("SELECT root_path FROM sources WHERE kind=?", (value["source_key"],)).fetchone()
    if not row or row["root_path"] != value["new_root"]:
        atomic_private_write(path, original)
    journal.unlink()


def _upgrade_sync_health(config, aliases, recoveries):
    """Preserve completion clocks while updating cached per-source reports."""
    for domain in ("session", "context"):
        path = config.data_dir / (domain + "-sync-state.json")
        if not path.exists():
            continue
        before = path.read_bytes()
        try:
            value = json.loads(before)
        except (ValueError, UnicodeError):
            continue  # The scheduler already ignores malformed rebuildable state.
        report = value.get("report") if isinstance(value, dict) else None
        rows = report.get("sources") if isinstance(report, dict) else None
        if not isinstance(rows, list):
            continue
        changed = False
        for row in rows:
            if isinstance(row, dict) and "source_key" in row:
                key = row.pop("source_key")
                row["source_id"] = aliases.get(key) if isinstance(key, str) else None
                changed = True
        if changed:
            after = json.dumps(value, ensure_ascii=False).encode()
            if path.read_bytes() != before:
                raise PreferencesError("이전 중 동기화 상태가 변경되었습니다. 현재 파일을 보존했습니다.")
            recoveries.append((path, before, after))
            atomic_private_write(path, after)


def migrate_registry(connection, config, schema):
    """Remove the old identity and migrate its structured dependents atomically."""
    if "kind" not in _columns(connection, "sources"):
        return False
    from localbrain.foundation.operations import operation_lock
    recoveries = []
    database_file = connection.execute("PRAGMA database_list").fetchone()[2]
    owns_config = bool(database_file and Path(database_file).resolve() == config.database_path.resolve())
    with operation_lock(config, "source-primary-key-upgrade") if owns_config else nullcontext():
        if "kind" not in _columns(connection, "sources"):
            return False
        connection.commit()
        if owns_config:
            _recover_reconnect(connection, config)
        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        connection.execute("PRAGMA foreign_keys=OFF")
        try:
            connection.execute("BEGIN IMMEDIATE")
            # Supply the provider column for installations predating that split.
            if "provider_kind" not in _columns(connection, "sources"):
                connection.execute("ALTER TABLE sources ADD COLUMN provider_kind TEXT NOT NULL DEFAULT 'unknown'")
                connection.execute("UPDATE sources SET provider_kind=kind")
            recovery = upgrade_config(connection, config) if owns_config else None
            if recovery is not None:
                recoveries.append(recovery)
            sources = [dict(row) for row in connection.execute("SELECT * FROM sources ORDER BY id")]
            aliases = {row["kind"]: row["id"] for row in sources}
            if owns_config:
                _upgrade_sync_health(config, aliases, recoveries)
            if "source_key" in _columns(connection, "skill_observations"):
                skills = [dict(row) for row in connection.execute("SELECT * FROM skill_observations")]
                for row in skills:
                    if row["source_key"] not in aliases:
                        raise RuntimeError("Skill evidence refers to an unknown source")
                    row["source_id"] = aliases[row.pop("source_key")]
                _replace_table(connection, schema, "skill_observations", skills)
            if _columns(connection, "session_chart_preferences"):
                preferences = [dict(row) for row in connection.execute("SELECT * FROM session_chart_preferences")]
                for row in preferences:
                    scope = row["source_scope"]
                    if (scope in aliases and scope.isdecimal() and int(scope) in aliases.values()
                            and aliases[scope] != int(scope)):
                        raise RuntimeError("An old chart alias conflicts with a numeric source ID; preferences preserved")
                    row["source_scope"] = str(aliases.get(scope, scope))
                _replace_table(connection, schema, "session_chart_preferences", preferences)
            if _columns(connection, "workflow_assertions"):
                episodes = {_episode_key(row["kind"], row["external_id"]): _episode_key(row["source_id"], row["external_id"])
                            for row in connection.execute("SELECT sessions.source_id,sessions.external_id,sources.kind FROM sessions JOIN sources ON sources.id=sessions.source_id")}
                assertions = [dict(row) for row in connection.execute("SELECT * FROM workflow_assertions")]
                for row in assertions:
                    for field in ("source_episode_key", "target_episode_key"):
                        row[field] = episodes.get(row[field], row[field])
                    parts = [row["boundary_kind"], row["source_episode_key"]]
                    if row["boundary_kind"] == "relation":
                        parts.append(row["target_episode_key"])
                    row["boundary_key"] = hashlib.sha256(b"".join(len(p.encode()).to_bytes(8, "big") + p.encode() for p in parts)).hexdigest()
                _replace_table(connection, schema, "workflow_assertions", assertions)
            if _columns(connection, "personal_insight_runs"):
                for row in connection.execute("SELECT id,settings_json FROM personal_insight_runs").fetchall():
                    value = json.loads(row["settings_json"])
                    if "usage_source_key" in value:
                        key = value.pop("usage_source_key")
                        if key not in aliases:
                            raise RuntimeError("Analysis usage refers to an unknown source")
                        value["usage_source_id"] = aliases[key]
                        connection.execute("UPDATE personal_insight_runs SET settings_json=? WHERE id=?", (json.dumps(value, ensure_ascii=False), row["id"]))
            if _columns(connection, "search_index"):
                # The owning entity is authoritative even if an old alias happens
                # to equal another profile's provider name.
                for entity_type, table in (("session", "sessions"), ("document", "context_documents")):
                    connection.execute("UPDATE search_index SET source_kind=COALESCE(("
                        "SELECT sources.provider_kind FROM " + table + " AS entity "
                        "JOIN sources ON sources.id=entity.source_id "
                        "WHERE CAST(entity.id AS TEXT)=search_index.entity_id),source_kind) "
                        "WHERE entity_type=?", (entity_type,))
            for row in sources:
                row.pop("kind")
            _replace_table(connection, schema, "sources", sources)
            if connection.execute("PRAGMA foreign_key_check").fetchone():
                raise RuntimeError("Source primary-key upgrade failed its foreign-key check")
            connection.commit()
        except Exception:
            connection.rollback()
            restoration_error = None
            for recovery in reversed(recoveries):
                try:
                    restore_config(recovery)
                except Exception as error:
                    restoration_error = error
            if restoration_error is not None:
                raise restoration_error
            raise
        finally:
            connection.execute("PRAGMA foreign_keys=" + ("ON" if foreign_keys else "OFF"))
    return True
