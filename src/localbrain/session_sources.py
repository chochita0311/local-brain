"""Private local AI Session-source configuration and safe registration."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import tomllib
except ImportError:  # pragma: no cover - exercised by the supported Python 3.9 CI
    import tomli as tomllib

from .config import Settings
from .source_profiles import PALETTE, default_color, valid_source_id


SESSION_SOURCE_SCHEMA_VERSION = 2
SESSION_SOURCES_FILENAME = "session-sources.toml"
SUPPORTED_SESSION_PROVIDERS = frozenset({"claude", "codex"})
MAX_DISPLAY_LABEL_LENGTH = 160
MAX_ROOT_LENGTH = 4096
MAX_DIAGNOSTIC_LENGTH = 360
ENTRY_FIELDS = frozenset(
    {"source_id", "display_label", "provider_kind", "root", "agent_home", "enabled", "color"}
)


@dataclass(frozen=True)
class SessionSourceDiagnostic:
    code: str
    message: str
    settings_path: str
    source_id: Optional[int] = None


@dataclass(frozen=True)
class SessionSourceEntry:
    source_id: int
    display_label: str
    provider_kind: str
    root: Path
    availability: str
    agent_home: Optional[Path] = None
    enabled: bool = True
    color: Optional[str] = None


@dataclass(frozen=True)
class SessionSourceSettingsResult:
    settings_path: Path
    entries: Tuple[SessionSourceEntry, ...]
    diagnostics: Tuple[SessionSourceDiagnostic, ...]
    declared_source_ids: Tuple[int, ...]
    bootstrapped: bool = False
    file_error: bool = False
    schema_version: int = 2


@dataclass(frozen=True)
class SessionSourceRegistration:
    source_id: int
    provider_kind: str
    display_label: str
    root: str
    status: str


@dataclass(frozen=True)
class SessionSourceRegistryResult:
    settings: SessionSourceSettingsResult
    registrations: Tuple[SessionSourceRegistration, ...]
    diagnostics: Tuple[SessionSourceDiagnostic, ...]


def session_sources_path(settings: Settings) -> Path:
    return settings.session_sources_path or settings.data_dir / SESSION_SOURCES_FILENAME


def _bounded_message(value: str) -> str:
    clean = " ".join(value.split())
    if len(clean) <= MAX_DIAGNOSTIC_LENGTH:
        return clean
    return clean[: MAX_DIAGNOSTIC_LENGTH - 1].rstrip() + "…"


def _diagnostic(
    path: Path, code: str, message: str, source_id: Optional[int] = None
) -> SessionSourceDiagnostic:
    return SessionSourceDiagnostic(
        code=code,
        message=_bounded_message(message),
        settings_path=str(path),
        source_id=source_id,
    )


def session_sources_text(entries) -> str:
    """Keep profile fields readable without changing values or display order."""
    from .preferences import toml_text

    fields = ("source_id", "provider_kind", "display_label", "root", "color", "agent_home", "enabled")
    ordered = []
    for entry in entries:
        values = {key: entry[key] for key in fields if key in entry}
        values.update(entry)
        ordered.append(values)
    return toml_text({"schema_version": SESSION_SOURCE_SCHEMA_VERSION, "session_sources": ordered})


def _bootstrap_text(settings: Settings) -> str:
    # Migrate known registrations, never discover/register someone's folders as
    # a side effect of starting a fresh installation.
    entries = []
    if settings.database_path.exists():
        with sqlite3.connect(settings.database_path) as connection:
            if connection.execute("SELECT 1 FROM sqlite_master WHERE name='sources'").fetchone():
                columns = {row[1] for row in connection.execute("PRAGMA table_info(sources)")}
                color = "profile_color" if "profile_color" in columns else "NULL"
                order = "profile_position,id" if "profile_position" in columns else "id"
                entries = connection.execute("SELECT id,name,provider_kind,root_path," + color + " FROM sources "
                                             "WHERE provider_kind IN ('claude','codex') ORDER BY " + order).fetchall()
    return session_sources_text([
        dict(source_id=source_id, provider_kind=provider_kind, display_label=display_label,
             root=str(Path(root).expanduser()), color=color or default_color(provider_kind))
        for source_id, display_label, provider_kind, root, color in entries
    ])


def _write_bootstrap(path: Path, settings: Settings) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False
    encoded = _bootstrap_text(settings).encode("utf-8")
    temporary_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".session-sources-", suffix=".tmp",
            dir=str(path.parent), delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            os.chmod(handle.name, 0o600)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            return False
        os.replace(str(temporary_path), str(path))
        temporary_path = None
        return True
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def _file_error(
    path: Path, code: str, message: str, *, bootstrapped: bool = False
) -> SessionSourceSettingsResult:
    return SessionSourceSettingsResult(
        settings_path=path,
        entries=(),
        diagnostics=(_diagnostic(path, code, message),),
        declared_source_ids=(),
        bootstrapped=bootstrapped,
        file_error=True,
    )


def _normalized_root(path: Path, raw_root: str) -> Path:
    root = Path(raw_root).expanduser()
    if not root.is_absolute():
        root = path.parent / root
    return Path(os.path.abspath(str(root)))


def load_session_source_settings(settings: Settings) -> SessionSourceSettingsResult:
    path = session_sources_path(settings)
    try:
        bootstrapped = _write_bootstrap(path, settings)
    except OSError as error:
        return _file_error(path, "bootstrap_failed", str(error))

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _file_error(path, "settings_missing", "Session source settings file is missing.")
    except UnicodeError:
        return _file_error(path, "invalid_encoding", "Session source settings must be UTF-8.", bootstrapped=bootstrapped)
    except tomllib.TOMLDecodeError as error:
        return _file_error(path, "invalid_toml", str(error), bootstrapped=bootstrapped)
    except OSError as error:
        return _file_error(path, "settings_unreadable", str(error), bootstrapped=bootstrapped)

    if set(raw) != {"schema_version", "session_sources"}:
        return _file_error(
            path,
            "invalid_schema",
            "Expected only schema_version and session_sources at the top level.",
            bootstrapped=bootstrapped,
        )
    version = raw.get("schema_version")
    if type(version) is not int or version != SESSION_SOURCE_SCHEMA_VERSION:
        return _file_error(
            path,
            "unsupported_schema_version",
            "Session source schema_version must be 2; older files need the startup upgrade.",
            bootstrapped=bootstrapped,
        )
    raw_entries = raw.get("session_sources")
    if not isinstance(raw_entries, list):
        return _file_error(
            path,
            "invalid_schema",
            "session_sources must be an array of tables.",
            bootstrapped=bootstrapped,
        )

    def identity(value):
        source_id = value.get("source_id")
        return source_id if valid_source_id(source_id) else None

    declared_keys = tuple(
        key for key in (identity(item) for item in raw_entries if isinstance(item, dict))
        if key is not None
    )
    duplicate_keys = sorted(
        key for key in set(declared_keys) if declared_keys.count(key) > 1
    )
    if duplicate_keys:
        return _file_error(
            path,
            "duplicate_source_id",
            "Duplicate profile identities: {}.".format(", ".join(map(str, duplicate_keys))),
            bootstrapped=bootstrapped,
        )

    diagnostics = []
    candidates = []
    for index, value in enumerate(raw_entries, start=1):
        if not isinstance(value, dict):
            diagnostics.append(
                _diagnostic(path, "invalid_entry", "Entry {} must be a TOML table.".format(index))
            )
            continue
        source_id = identity(value)
        fields = ENTRY_FIELDS
        if not (fields - {"agent_home", "enabled", "color"}) <= set(value) or not set(value) <= fields:
            diagnostics.append(
                _diagnostic(
                    path,
                    "invalid_entry_schema",
                    "Entry {} has missing or unsupported profile fields.".format(index),
                    source_id,
                )
            )
            continue
        if source_id is None:
            diagnostics.append(_diagnostic(path, "invalid_source_id", "source_id must be a positive safe integer."))
            continue
        display_label = value["display_label"]
        provider_kind = value["provider_kind"]
        color = value.get("color")
        if color is not None and (not isinstance(color, str) or color not in PALETTE):
            diagnostics.append(_diagnostic(path, "invalid_color", "Choose a supported profile color.", source_id))
            continue
        raw_root = value["root"]
        enabled = value.get("enabled", True)
        if not isinstance(enabled, bool):
            diagnostics.append(_diagnostic(path, "invalid_enabled", "enabled must be a boolean.", source_id))
            continue
        agent_home = value.get("agent_home")
        if agent_home is not None and (not isinstance(agent_home, str) or not agent_home.strip() or len(agent_home) > MAX_ROOT_LENGTH):
            diagnostics.append(_diagnostic(path, "invalid_agent_home", "agent_home must be a nonempty path.", source_id))
            continue
        if not isinstance(display_label, str) or not display_label.strip() or len(display_label.strip()) > MAX_DISPLAY_LABEL_LENGTH:
            diagnostics.append(_diagnostic(path, "invalid_display_label", "display_label must contain 1 to 160 characters.", source_id))
            continue
        if not isinstance(provider_kind, str) or provider_kind not in SUPPORTED_SESSION_PROVIDERS:
            diagnostics.append(_diagnostic(path, "unsupported_provider", "provider_kind must be claude or codex.", source_id))
            continue
        if not isinstance(raw_root, str) or not raw_root.strip() or len(raw_root) > MAX_ROOT_LENGTH:
            diagnostics.append(_diagnostic(path, "invalid_root", "root must contain 1 to 4096 characters.", source_id))
            continue
        root = _normalized_root(path, raw_root.strip())
        if enabled and root.exists() and not root.is_dir():
            diagnostics.append(_diagnostic(path, "root_not_directory", "Configured root is not a directory.", source_id))
            continue
        if enabled and root.exists() and not os.access(str(root), os.R_OK | os.X_OK):
            diagnostics.append(_diagnostic(path, "root_unreadable", "Configured root is not readable.", source_id))
            continue
        candidates.append(
            SessionSourceEntry(
                source_id=source_id,
                display_label=display_label.strip(),
                provider_kind=provider_kind,
                root=root,
                availability="ready" if root.is_dir() else "unavailable",
                agent_home=_normalized_root(path, agent_home) if agent_home else None,
                enabled=enabled,
                color=color,
            )
        )

    roots: Dict[str, list] = {}
    for entry in candidates:
        if not entry.enabled:
            continue
        roots.setdefault(str(entry.root), []).append(entry.source_id)
    duplicate_roots = {
        root: keys for root, keys in roots.items() if len(keys) > 1
    }
    invalid_root_keys = {key for keys in duplicate_roots.values() for key in keys}
    for index, entry in enumerate(candidates):
        root = entry.root.resolve()
        for other in candidates[index + 1:]:
            other_root = other.root.resolve()
            if (entry.enabled and other.enabled and entry.root != other.root
                    and (root == other_root or root in other_root.parents or other_root in root.parents)):
                invalid_root_keys.update((entry.source_id, other.source_id))
                for key in (entry.source_id, other.source_id):
                    diagnostics.append(_diagnostic(path, "overlapping_root", "Session profile folders must not overlap.", key))
    for root, keys in sorted(duplicate_roots.items()):
        for key in keys:
            diagnostics.append(
                _diagnostic(
                    path,
                    "duplicate_root",
                    "Configured root is also assigned to: {}.".format(
                        ", ".join(str(other) for other in keys if other != key)
                    ),
                    key,
                )
            )
    entries = tuple(
        entry for entry in candidates if entry.source_id not in invalid_root_keys
    )
    return SessionSourceSettingsResult(
        settings_path=path,
        entries=entries,
        diagnostics=tuple(diagnostics),
        declared_source_ids=declared_keys,
        bootstrapped=bootstrapped,
        file_error=False,
        schema_version=version,
    )


def _source_has_descendants(connection: sqlite3.Connection, source_id: int) -> bool:
    for table in ("source_files", "sessions", "usage_records", "context_documents"):
        if connection.execute(
            "SELECT 1 FROM {} WHERE source_id = ? LIMIT 1".format(table),
            (source_id,),
        ).fetchone():
            return True
    return False


def reconcile_session_source_settings(
    connection: sqlite3.Connection, result: SessionSourceSettingsResult
) -> SessionSourceRegistryResult:
    if result.file_error:
        return SessionSourceRegistryResult(result, (), result.diagnostics)

    registrations = []
    diagnostics = list(result.diagnostics)
    for position, entry in enumerate(result.entries):
        existing = connection.execute(
            "SELECT id,provider_kind,name,root_path,profile_color FROM sources WHERE id = ?",
            (entry.source_id,),
        ).fetchone()
        if existing is None:
            cursor = connection.execute(
                "INSERT INTO sources(id,provider_kind,name,root_path,profile_color,profile_position) VALUES (?,?,?,?,?,?)",
                (entry.source_id, entry.provider_kind, entry.display_label, str(entry.root),
                 entry.color or default_color(entry.provider_kind), position),
            )
            registrations.append(
                SessionSourceRegistration(
                    entry.source_id, entry.provider_kind, entry.display_label,
                    str(entry.root), entry.availability
                )
            )
            continue
        source_id = int(existing["id"])
        if existing["provider_kind"] != entry.provider_kind:
            diagnostics.append(_diagnostic(result.settings_path, "identity_conflict", "The existing source ID is bound to another provider.", entry.source_id))
            registrations.append(SessionSourceRegistration(entry.source_id, existing["provider_kind"], existing["name"], existing["root_path"], "identity_conflict"))
            continue
        if existing["root_path"] != str(entry.root) and _source_has_descendants(connection, source_id):
            diagnostics.append(_diagnostic(result.settings_path, "root_change_conflict", "The configured root cannot change while the source owns imported data.", entry.source_id))
            registrations.append(SessionSourceRegistration(entry.source_id, entry.provider_kind, existing["name"], existing["root_path"], "root_change_conflict"))
            continue
        connection.execute(
            "UPDATE sources SET name=?,root_path=?,profile_color=?,profile_position=? WHERE id=?",
            (entry.display_label, str(entry.root), entry.color or default_color(entry.provider_kind),
             position, source_id),
        )
        registrations.append(SessionSourceRegistration(source_id, entry.provider_kind, entry.display_label, str(entry.root), entry.availability))

    declared = set(result.declared_source_ids)
    retained = connection.execute(
        """
        SELECT id, provider_kind, name, root_path
        FROM sources
        WHERE provider_kind IN ('claude', 'codex')
        ORDER BY id
        """
    ).fetchall()
    represented = {item.source_id for item in registrations}
    for existing in retained:
        key = existing["id"]
        if key in declared or key in represented:
            continue
        connection.execute("UPDATE sources SET profile_position=2147483647 WHERE id=?", (existing["id"],))
        diagnostics.append(_diagnostic(result.settings_path, "config_missing", "The retained source is omitted from the settings file; its data was preserved.", key))
        registrations.append(SessionSourceRegistration(key, existing["provider_kind"], existing["name"], existing["root_path"], "config_missing"))

    return SessionSourceRegistryResult(
        settings=result,
        registrations=tuple(registrations),
        diagnostics=tuple(diagnostics),
    )


def load_and_reconcile_session_sources(
    connection: sqlite3.Connection, settings: Settings
) -> SessionSourceRegistryResult:
    return reconcile_session_source_settings(
        connection, load_session_source_settings(settings)
    )
