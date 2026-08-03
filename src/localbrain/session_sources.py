"""Private local AI Session-source configuration and safe registration."""

from __future__ import annotations

import json
import os
import re
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


SESSION_SOURCE_SCHEMA_VERSION = 1
SESSION_SOURCES_FILENAME = "session-sources.toml"
SUPPORTED_SESSION_PROVIDERS = frozenset({"claude", "codex"})
SOURCE_KEY_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SOURCE_KEY_LENGTH = 64
MAX_DISPLAY_LABEL_LENGTH = 160
MAX_ROOT_LENGTH = 4096
MAX_DIAGNOSTIC_LENGTH = 360
ENTRY_FIELDS = frozenset(
    {"source_key", "display_label", "provider_kind", "root"}
)


@dataclass(frozen=True)
class SessionSourceDiagnostic:
    code: str
    message: str
    settings_path: str
    source_key: Optional[str] = None


@dataclass(frozen=True)
class SessionSourceEntry:
    source_key: str
    display_label: str
    provider_kind: str
    root: Path
    availability: str


@dataclass(frozen=True)
class SessionSourceSettingsResult:
    settings_path: Path
    entries: Tuple[SessionSourceEntry, ...]
    diagnostics: Tuple[SessionSourceDiagnostic, ...]
    declared_source_keys: Tuple[str, ...]
    bootstrapped: bool = False
    file_error: bool = False


@dataclass(frozen=True)
class SessionSourceRegistration:
    source_key: str
    provider_kind: str
    display_label: str
    root: str
    status: str
    source_id: Optional[int] = None


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
    path: Path, code: str, message: str, source_key: Optional[str] = None
) -> SessionSourceDiagnostic:
    return SessionSourceDiagnostic(
        code=code,
        message=_bounded_message(message),
        settings_path=str(path),
        source_key=source_key,
    )


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _bootstrap_text(settings: Settings) -> str:
    entries = (
        ("claude", "Claude Code", "claude", settings.claude_root),
        ("codex", "Codex", "codex", settings.codex_root),
        (
            "codex-company",
            "Codex Company",
            "codex",
            Path.home() / ".codex-company" / "sessions",
        ),
    )
    lines = ["schema_version = 1", ""]
    for source_key, display_label, provider_kind, root in entries:
        lines.extend(
            [
                "[[session_sources]]",
                "source_key = {}".format(_toml_string(source_key)),
                "display_label = {}".format(_toml_string(display_label)),
                "provider_kind = {}".format(_toml_string(provider_kind)),
                "root = {}".format(_toml_string(str(root.expanduser()))),
                "",
            ]
        )
    return "\n".join(lines)


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
        declared_source_keys=(),
        bootstrapped=bootstrapped,
        file_error=True,
    )


def _normalized_root(path: Path, raw_root: str) -> Path:
    root = Path(raw_root).expanduser()
    if not root.is_absolute():
        root = path.parent / root
    return Path(os.path.abspath(str(root)))


def _entry_identity(raw: Dict[str, Any]) -> Optional[str]:
    value = raw.get("source_key")
    return value.strip() if isinstance(value, str) and value.strip() else None


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
    if raw.get("schema_version") != SESSION_SOURCE_SCHEMA_VERSION:
        return _file_error(
            path,
            "unsupported_schema_version",
            "Supported session source schema_version is 1.",
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

    declared_keys = tuple(
        key for key in (_entry_identity(item) for item in raw_entries if isinstance(item, dict))
        if key is not None
    )
    duplicate_keys = sorted(
        key for key in set(declared_keys) if declared_keys.count(key) > 1
    )
    if duplicate_keys:
        return _file_error(
            path,
            "duplicate_source_key",
            "Duplicate source_key values: {}.".format(", ".join(duplicate_keys)),
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
        source_key = _entry_identity(value)
        if set(value) != ENTRY_FIELDS:
            diagnostics.append(
                _diagnostic(
                    path,
                    "invalid_entry_schema",
                    "Entry {} must contain exactly source_key, display_label, provider_kind, and root.".format(index),
                    source_key,
                )
            )
            continue
        if (
            source_key is None
            or len(source_key) > MAX_SOURCE_KEY_LENGTH
            or not SOURCE_KEY_PATTERN.fullmatch(source_key)
        ):
            diagnostics.append(
                _diagnostic(path, "invalid_source_key", "Entry {} has an invalid source_key.".format(index), source_key)
            )
            continue
        display_label = value["display_label"]
        provider_kind = value["provider_kind"]
        raw_root = value["root"]
        if not isinstance(display_label, str) or not display_label.strip() or len(display_label.strip()) > MAX_DISPLAY_LABEL_LENGTH:
            diagnostics.append(_diagnostic(path, "invalid_display_label", "display_label must contain 1 to 160 characters.", source_key))
            continue
        if not isinstance(provider_kind, str) or provider_kind not in SUPPORTED_SESSION_PROVIDERS:
            diagnostics.append(_diagnostic(path, "unsupported_provider", "provider_kind must be claude or codex.", source_key))
            continue
        if not isinstance(raw_root, str) or not raw_root.strip() or len(raw_root) > MAX_ROOT_LENGTH:
            diagnostics.append(_diagnostic(path, "invalid_root", "root must contain 1 to 4096 characters.", source_key))
            continue
        root = _normalized_root(path, raw_root.strip())
        if root.exists() and not root.is_dir():
            diagnostics.append(_diagnostic(path, "root_not_directory", "Configured root is not a directory.", source_key))
            continue
        if root.exists() and not os.access(str(root), os.R_OK | os.X_OK):
            diagnostics.append(_diagnostic(path, "root_unreadable", "Configured root is not readable.", source_key))
            continue
        candidates.append(
            SessionSourceEntry(
                source_key=source_key,
                display_label=display_label.strip(),
                provider_kind=provider_kind,
                root=root,
                availability="ready" if root.is_dir() else "unavailable",
            )
        )

    roots: Dict[str, list] = {}
    for entry in candidates:
        roots.setdefault(str(entry.root), []).append(entry.source_key)
    duplicate_roots = {
        root: keys for root, keys in roots.items() if len(keys) > 1
    }
    invalid_root_keys = {key for keys in duplicate_roots.values() for key in keys}
    for root, keys in sorted(duplicate_roots.items()):
        for key in keys:
            diagnostics.append(
                _diagnostic(
                    path,
                    "duplicate_root",
                    "Configured root is also assigned to: {}.".format(
                        ", ".join(other for other in keys if other != key)
                    ),
                    key,
                )
            )
    entries = tuple(
        entry for entry in candidates if entry.source_key not in invalid_root_keys
    )
    return SessionSourceSettingsResult(
        settings_path=path,
        entries=entries,
        diagnostics=tuple(diagnostics),
        declared_source_keys=declared_keys,
        bootstrapped=bootstrapped,
        file_error=False,
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
    for entry in result.entries:
        existing = connection.execute(
            "SELECT id, provider_kind, name, root_path FROM sources WHERE kind = ?",
            (entry.source_key,),
        ).fetchone()
        if existing is None:
            cursor = connection.execute(
                """
                INSERT INTO sources(kind, provider_kind, name, root_path)
                VALUES (?, ?, ?, ?)
                """,
                (entry.source_key, entry.provider_kind, entry.display_label, str(entry.root)),
            )
            registrations.append(
                SessionSourceRegistration(
                    entry.source_key, entry.provider_kind, entry.display_label,
                    str(entry.root), entry.availability, int(cursor.lastrowid)
                )
            )
            continue
        source_id = int(existing["id"])
        if existing["provider_kind"] != entry.provider_kind:
            diagnostics.append(_diagnostic(result.settings_path, "identity_conflict", "The existing source key is bound to another provider.", entry.source_key))
            registrations.append(SessionSourceRegistration(entry.source_key, existing["provider_kind"], existing["name"], existing["root_path"], "identity_conflict", source_id))
            continue
        if existing["root_path"] != str(entry.root) and _source_has_descendants(connection, source_id):
            diagnostics.append(_diagnostic(result.settings_path, "root_change_conflict", "The configured root cannot change while the source owns imported data.", entry.source_key))
            registrations.append(SessionSourceRegistration(entry.source_key, entry.provider_kind, existing["name"], existing["root_path"], "root_change_conflict", source_id))
            continue
        connection.execute(
            "UPDATE sources SET name = ?, root_path = ? WHERE id = ?",
            (entry.display_label, str(entry.root), source_id),
        )
        registrations.append(SessionSourceRegistration(entry.source_key, entry.provider_kind, entry.display_label, str(entry.root), entry.availability, source_id))

    declared = set(result.declared_source_keys)
    retained = connection.execute(
        """
        SELECT id, kind, provider_kind, name, root_path
        FROM sources
        WHERE provider_kind IN ('claude', 'codex')
        ORDER BY id
        """
    ).fetchall()
    represented = {item.source_key for item in registrations}
    for existing in retained:
        key = existing["kind"]
        if key in declared or key in represented:
            continue
        diagnostics.append(_diagnostic(result.settings_path, "config_missing", "The retained source is omitted from the settings file; its data was preserved.", key))
        registrations.append(SessionSourceRegistration(key, existing["provider_kind"], existing["name"], existing["root_path"], "config_missing", int(existing["id"])))

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
