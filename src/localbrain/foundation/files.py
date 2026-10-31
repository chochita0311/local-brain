"""Private filesystem boundaries, permissions and inactive-file checks."""

import json
import os
import stat
import subprocess
from pathlib import Path

from localbrain.foundation.paths import package_boundary


class StorageError(RuntimeError):
    pass


def validate_runtime_directory(path):
    """Resolve a private location without creating or changing any files."""
    path = Path(path).expanduser().absolute()
    if path.is_symlink():
        raise StorageError("INVALID_RUNTIME_DIRECTORY")
    path = path.resolve()
    from localbrain.foundation.paths import hub_cache_root
    public_cache = hub_cache_root()
    if path == public_cache or public_cache in path.parents or path in public_cache.parents:
        raise StorageError("PRIVATE_STORAGE_OVERLAPS_PUBLIC_MODEL_CACHE")
    package_root = package_boundary()
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


def read_owned_json(path, limit=8 * 1024 * 1024):
    """Require an owned, singly-linked regular file containing bounded JSON."""
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or info.st_size > limit:
        raise StorageError("UNOWNED_STORAGE")
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise StorageError("UNOWNED_STORAGE")
    return value


def owned_tree(folder):
    """Snapshot only owned directories and singly-linked regular files."""
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


def ensure_tree_unchanged(stamps):
    for path, before in stamps:
        after = path.lstat()
        if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_mode, after.st_nlink) != (
                before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_mode, before.st_nlink):
            raise StorageError("STORAGE_CHANGED")


def tree_is_inactive(stamps):
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
