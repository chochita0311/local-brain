"""Explicit, local storage moves and retirement of owned derived results."""

import fcntl
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from .config import cache_directory, development_directory
from .runtime_storage import (
    StorageError, inactive_files, private_directory, validate_runtime_directory,
)
from .work_reconstruction import ExperimentError


def _json(path, limit=8 * 1024 * 1024):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or info.st_size > limit:
        raise StorageError("UNOWNED_STORAGE")
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise StorageError("UNOWNED_STORAGE")
    return value


def _tree(folder):
    entries = [folder, *folder.rglob("*")]
    stamps = []
    for path in entries:
        info = path.lstat()
        if info.st_uid != os.getuid() or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
            raise StorageError("UNOWNED_STORAGE")
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise StorageError("UNOWNED_STORAGE")
        stamps.append((path, info))
    return stamps


def _unchanged(stamps):
    for path, before in stamps:
        after = path.lstat()
        if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_mode, after.st_nlink) != (
                before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_mode, before.st_nlink):
            raise StorageError("STORAGE_CHANGED")


def _inactive(stamps):
    # Keep each lsof invocation below the platform's argument-size limit.
    batch, size = [], 0
    for path, _ in stamps:
        if batch and size + len(os.fsencode(path)) > 48000:
            if not inactive_files(batch):
                return False
            batch, size = [], 0
        batch.append(path)
        size += len(os.fsencode(path)) + 1
    return not batch or inactive_files(batch)


def _model_owner(folder, key):
    from .model_catalog import EMBEDDING_ID, EMBEDDING_REVISION, EMBEDDING_SCHEMA, MODELS
    from .work_context_model import HUB_MANIFEST_OWNER, OWNER, model_spec
    marker = _json(folder / "owner.json", 8192)
    manifest = _json(folder / "model.json")
    names = {p.name for p in folder.iterdir()}
    if not names <= {"owner.json", "model.json", "install.lock"}:
        return False  # Preserve app-local installations and unfinished downloads.
    if key == "embedding":
        return (marker == {"owner": EMBEDDING_SCHEMA, "model": EMBEDDING_ID, "revision": EMBEDDING_REVISION}
                and manifest.get("schema") == EMBEDDING_SCHEMA
                and manifest.get("model_id") == EMBEDDING_ID
                and manifest.get("resolved_revision") == EMBEDDING_REVISION)
    spec = model_spec(MODELS[key]["id"])
    return (marker == {"owner": OWNER, "model": spec["id"], "revision": spec["revision"]}
            and manifest.get("owner") == HUB_MANIFEST_OWNER
            and manifest.get("model_id") == spec["id"] and manifest.get("revision") == spec["revision"])


def migrate_storage(config, *, apply=False, include_development=False):
    """Move recognized state atomically on one filesystem; never merge copies.

    The caller stops the application and development jobs before applying.
    Development archives require the separate explicit inclusion option.
    """
    data = validate_runtime_directory(config.data_dir)
    cache = validate_runtime_directory(cache_directory(config))
    development = validate_runtime_directory(development_directory(config))
    if cache == data or development == data or cache == development or any(
            a in b.parents for a, b in ((data, cache), (cache, data), (data, development),
                                        (development, data), (cache, development), (development, cache))):
        raise StorageError("STORAGE_ROOTS_OVERLAP")
    result = {"eligible_directories": 0, "eligible_bytes": 0,
              "moved_directories": 0, "moved_bytes": 0, "preserved_directories": 0}
    if not data.exists():
        return result
    candidates = [(data / "session-simulation", cache / "session-simulation", "simulation"),
                  (data / "auto-work-preview", cache / "auto-work-preview", "preview")]
    from .model_catalog import MODELS
    candidates.extend((data / spec["slug"], data / "models" / spec["slug"], "model:" + key)
                      for key, spec in MODELS.items())
    if include_development:
        candidates.extend((p, development / p.name, "development") for p in sorted(data.iterdir())
                          if p.name == "personal-insight-evaluations"
                          or p.name.startswith(("work-context-", "work-role-", "source-claim-")))
    moves = []
    for source, target, kind in candidates:
        if not source.exists() and not source.is_symlink():
            continue
        try:
            stamps = _tree(source)
            if not source.is_dir():
                raise StorageError("UNOWNED_STORAGE")
            if kind == "simulation":
                from .session_simulation import FILES, OWNER
                owned = _json(source / "owner.json", 8192).get("owner") == OWNER
                owned = owned and {p.name for p in source.iterdir()} <= FILES
            elif kind == "preview":
                names = {p.name for p in source.iterdir()}
                owned = names <= {"current.json", "preview.lock"}
                if "current.json" in names:
                    owned = owned and _json(source / "current.json").get("owner") == "localbrain.auto-work-preview.v1"
                else:
                    owned = owned and names == {"preview.lock"} and (source / "preview.lock").stat().st_size == 0
            elif kind.startswith("model:"):
                owned = _model_owner(source, kind.split(":", 1)[1])
            else:
                owned = source.name == "personal-insight-evaluations"
                if not owned:
                    from .work_context_evaluation import FILES, OWNER
                    owned = (_json(source / "owner.json", 8192).get("owner") == OWNER
                             and {p.name for p in source.iterdir()} <= FILES)
            if not owned:
                raise StorageError("UNOWNED_STORAGE")
        except (OSError, ValueError, StorageError):
            result["preserved_directories"] += 1
            continue
        validate_runtime_directory(target)
        if target.exists() or target.is_symlink():
            raise StorageError("STORAGE_DESTINATION_EXISTS")
        ancestor = next(p for p in target.parents if p.exists())
        if source.stat().st_dev != ancestor.stat().st_dev:
            raise StorageError("STORAGE_MOVE_CROSS_DEVICE")
        size = sum(info.st_size for _, info in stamps if stat.S_ISREG(info.st_mode))
        moves.append((source, target, stamps, size))
        result["eligible_directories"] += 1
        result["eligible_bytes"] += size
    if apply:
        if any(not _inactive(stamps) for _, _, stamps, _ in moves):
            raise StorageError("STORAGE_BUSY_OR_UNAVAILABLE")
        for _, _, stamps, _ in moves:
            _unchanged(stamps)
        for source, target, stamps, size in moves:
            private_directory(target.parent)
            _unchanged(stamps)
            if target.exists() or target.is_symlink():
                raise StorageError("STORAGE_DESTINATION_EXISTS")
            source.rename(target)
            for old, info in stamps:
                moved = target / old.relative_to(source)
                moved.chmod(0o700 if stat.S_ISDIR(info.st_mode) else 0o600)
            result["moved_directories"] += 1
            result["moved_bytes"] += size
    return result


def maintain_derived_cache(cache_dir, *, apply=True, at=None):
    """Retire expired known results, preserving markers, locks and unknown files."""
    root = validate_runtime_directory(cache_dir)
    now = at or datetime.now(timezone.utc)
    result = {"eligible_files": 0, "eligible_bytes": 0, "removed_files": 0,
              "removed_bytes": 0, "preserved_directories": 0}
    for name in ("session-simulation", "auto-work-preview"):
        folder = root / name
        if not folder.exists() and not folder.is_symlink():
            continue
        descriptor = None
        try:
            stamps = _tree(folder)
            if name == "session-simulation":
                from .session_simulation import FILES, OWNER
                lock, marker, owner = "writer.lock", "owner.json", OWNER
                known = FILES
                retained = {lock, marker}
            else:
                lock, marker, owner = "preview.lock", "current.json", "localbrain.auto-work-preview.v1"
                known, retained = {lock, marker}, {lock}
            if not {p.name for p in folder.iterdir()} <= known or not _inactive(stamps):
                raise StorageError("STORAGE_BUSY_OR_UNAVAILABLE")
            descriptor = os.open(folder / lock, os.O_RDWR | os.O_NOFOLLOW)
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            _unchanged(stamps)
            if name == "auto-work-preview":
                from .auto_work import _read
                value = _read(folder / marker)
            else:
                value = _json(folder / marker, 8192)
                binding = value.get("database")
                if (set(value) != {"owner", "database", "expires_at"}
                        or not isinstance(binding, str) or len(binding) != 64
                        or any(character not in "0123456789abcdef" for character in binding)):
                    raise StorageError("UNOWNED_STORAGE")
            if not isinstance(value.get("expires_at"), str):
                raise StorageError("UNOWNED_STORAGE")
            expires = datetime.fromisoformat(value["expires_at"].replace("Z", "+00:00"))
            if value.get("owner") != owner or expires.tzinfo is None:
                raise StorageError("UNOWNED_STORAGE")
            if expires > now:
                continue
            retired = [(p, info) for p, info in stamps if p != folder and p.name not in retained]
            if any(not stat.S_ISREG(info.st_mode) for _, info in retired):
                raise StorageError("UNOWNED_STORAGE")
            size = sum(info.st_size for _, info in retired)
            result["eligible_files"] += len(retired)
            result["eligible_bytes"] += size
            if apply:
                _unchanged(stamps)
                for path, _ in retired:
                    path.unlink()
                result["removed_files"] += len(retired)
                result["removed_bytes"] += size
        except (OSError, ValueError, KeyError, TypeError, StorageError, ExperimentError):
            result["preserved_directories"] += 1
        finally:
            if descriptor is not None:
                os.close(descriptor)
    return result
