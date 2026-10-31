"""Auto Work's legacy cache ownership and expired-result retirement policy."""

import fcntl
import os
import stat
from datetime import datetime, timezone

from localbrain.foundation.files import (
    StorageError, ensure_tree_unchanged, owned_tree, read_owned_json,
    tree_is_inactive, validate_runtime_directory,
)
from localbrain.foundation.validation import ExperimentError


def _simulation_cache_owned(folder):
    from .simulation import FILES, OWNER
    owned = read_owned_json(folder / "owner.json", 8192).get("owner") == OWNER
    return owned and {p.name for p in folder.iterdir()} <= FILES


def _preview_cache_owned(folder):
    names = {p.name for p in folder.iterdir()}
    owned = names <= {"current.json", "preview.lock"}
    if "current.json" in names:
        owned = owned and read_owned_json(folder / "current.json").get("owner") == "localbrain.auto-work-preview.v1"
    else:
        owned = owned and names == {"preview.lock"} and (folder / "preview.lock").stat().st_size == 0
    return owned


LEGACY_CACHE_OWNERS = {
    "session-simulation": _simulation_cache_owned,
    "auto-work-preview": _preview_cache_owned,
}


def maintain_cache(cache_dir, *, apply=True, at=None):
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
            stamps = owned_tree(folder)
            if name == "session-simulation":
                from .simulation import FILES, OWNER
                lock, marker, owner = "writer.lock", "owner.json", OWNER
                known = FILES
                retained = {lock, marker}
            else:
                lock, marker, owner = "preview.lock", "current.json", "localbrain.auto-work-preview.v1"
                known, retained = {lock, marker}, {lock}
            if not {p.name for p in folder.iterdir()} <= known or not tree_is_inactive(stamps):
                raise StorageError("STORAGE_BUSY_OR_UNAVAILABLE")
            descriptor = os.open(folder / lock, os.O_RDWR | os.O_NOFOLLOW)
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            ensure_tree_unchanged(stamps)
            if name == "auto-work-preview":
                from .preview import _read
                value = _read(folder / marker)
            else:
                value = read_owned_json(folder / marker, 8192)
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
                ensure_tree_unchanged(stamps)
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
