"""Private runtime paths and bounded, inactive migration recovery copies."""

import os
import stat
import subprocess
import time
from pathlib import Path


class StorageError(RuntimeError):
    pass


MIGRATION_BACKUP_SUFFIXES = (
    "-pre-usage-attribution-check-v1.bak",
    "-pre-usage-record-rename-v1.bak",
    "-pre-maintenance-session-contract-v1.bak",
    "-pre-maintenance-workstream-fk-v1.bak",
    "-pre-external-resource-url-scope-v1.bak",
    "-pre-atlassian-site-access-v1.bak",
    "-pre-source-provider-identity-v1.bak",
)
BACKUP_RETENTION_DAYS = 7


def validate_runtime_directory(path):
    """Resolve a private location without creating or changing any files."""
    path = Path(path).expanduser().absolute()
    if path.is_symlink():
        raise StorageError("INVALID_RUNTIME_DIRECTORY")
    path = path.resolve()
    from .model_cache import hub_cache_root
    public_cache = hub_cache_root()
    if path == public_cache or public_cache in path.parents or path in public_cache.parents:
        raise StorageError("PRIVATE_STORAGE_OVERLAPS_PUBLIC_MODEL_CACHE")
    package_root = Path(__file__).resolve().parents[2]
    if path == package_root or package_root in path.parents:
        raise StorageError("INVALID_RUNTIME_DIRECTORY")
    if any((parent / ".git").exists() for parent in (path, *path.parents)):
        raise StorageError("RUNTIME_DIRECTORY_IN_REPOSITORY")
    if path.exists() and (not path.is_dir() or path.stat().st_uid != os.getuid()):
        raise StorageError("UNOWNED_RUNTIME_DIRECTORY")
    return path


def private_directory(path):
    """Create owner-only state outside source trees and Git worktrees."""
    path = validate_runtime_directory(path)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise StorageError("UNOWNED_RUNTIME_DIRECTORY")
    if info.st_mode & 0o077:
        path.chmod(0o700)
    return path


def private_database(path):
    path = Path(path)
    private_directory(path.parent)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise StorageError("UNOWNED_DATABASE")
        os.fchmod(fd, 0o600)
    finally:
        os.close(fd)


def inactive_files(paths):
    """On supported macOS, uncertain or open files are preserved."""
    try:
        result = subprocess.run(["/usr/sbin/lsof", "-t", "--", *map(str, paths)],
                                capture_output=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 1 and not result.stdout and not result.stderr


def migration_backups(database):
    database = Path(database)
    result = []
    for suffix in MIGRATION_BACKUP_SUFFIXES:
        path = database.with_name(database.name + suffix)
        if not path.exists() or path.is_symlink():
            continue
        group = [path] + [p for p in (Path(str(path) + "-wal"), Path(str(path) + "-shm"))
                          if p.exists() or p.is_symlink()]
        if any(p.is_symlink() or not p.is_file() or p.stat().st_uid != os.getuid()
               or p.stat().st_nlink != 1 for p in group):
            continue
        # A nonempty WAL may be needed to recover the copy. Never discard it.
        if any(p.name.endswith("-wal") and p.stat().st_size for p in group):
            continue
        result.append((path.stat().st_mtime, group))
    return sorted(result, key=lambda item: item[0], reverse=True)


def maintain_migration_backups(database, connection, *, apply=True, current_time=None):
    """After successful initialization, keep one recovery copy for seven days."""
    backups = migration_backups(database)
    result = {"eligible_files": 0, "eligible_bytes": 0, "removed_files": 0,
              "removed_bytes": 0, "preserved_backups": 0}
    if not backups:
        return result
    # These copies are retired only after all current migration contracts hold.
    from .db import migration_contracts_current
    if not migration_contracts_current(connection):
        result["preserved_backups"] = len(backups)
        return result
    if [row[0] for row in connection.execute("PRAGMA quick_check")] != ["ok"]:
        raise StorageError("DATABASE_CHECK_FAILED")
    cutoff = (time.time() if current_time is None else current_time) - BACKUP_RETENTION_DAYS * 86400
    for index, (modified, group) in enumerate(backups):
        if (index == 0 and modified >= cutoff) or not inactive_files(group):
            result["preserved_backups"] += 1
            continue
        stamps = [(p, p.stat()) for p in group]
        size = sum(info.st_size for _, info in stamps)
        result["eligible_files"] += len(group)
        result["eligible_bytes"] += size
        if apply:
            if any(p.is_symlink() or (p.stat().st_dev, p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns)
                   != (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) for p, info in stamps):
                raise StorageError("BACKUP_CHANGED")
            # Remove the complete inactive group; never touch the live DB sidecars.
            for path, _ in reversed(stamps):
                path.unlink()
            result["removed_files"] += len(group)
            result["removed_bytes"] += size
    return result


def storage_status(data_dir, *, cache_dir=None, development_dir=None):
    """Aggregate storage facts; no source paths, filenames or content in output."""
    root = Path(data_dir)
    categories = {"database": 0, "migration_backups": 0, "simulation": 0,
                  "saved_runs": 0, "development_evidence": 0, "model_metadata": 0, "other": 0}
    categories["preview"] = 0
    roots = [(root, None)]
    if cache_dir is not None and Path(cache_dir) != root:
        roots.append((Path(cache_dir), "cache"))
    if development_dir is not None and Path(development_dir) != root:
        roots.append((Path(development_dir), "development"))
    backup_names = {"localbrain.db" + suffix for suffix in MIGRATION_BACKUP_SUFFIXES}
    seen = set()
    for location, kind in roots:
        for path in location.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            info = path.stat()
            identity = (info.st_dev, info.st_ino)
            if identity in seen:
                continue
            seen.add(identity)
            top = path.relative_to(location).parts[0]
            if kind == "development":
                category = "development_evidence"
            elif top in {"localbrain.db", "localbrain.db-wal", "localbrain.db-shm"} and kind is None:
                category = "database"
            elif any(top == name or top in {name + "-wal", name + "-shm"} for name in backup_names) and kind is None:
                category = "migration_backups"
            elif top == "session-simulation":
                category = "simulation"
            elif top == "auto-work-preview":
                category = "preview"
            elif top in {"runs", "personal-insight-runs"} and kind is None:
                category = "saved_runs"
            elif top == "personal-insight-evaluations" or top.startswith(("work-context-", "work-role-", "source-claim-")):
                category = "development_evidence"
            elif top == "models" or top in {"qwen3-4b", "qwen3-8b", "qwen3-embedding-0-6b"}:
                category = "model_metadata"
            else:
                category = "other"
            categories[category] += info.st_size
    return {"bytes": categories, "total_bytes": sum(categories.values())}
