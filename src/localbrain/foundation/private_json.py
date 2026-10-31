"""Owner-only JSON files with the existing pending-file publication contract."""

import json
import os
import stat

from localbrain.foundation.validation import require


def _safe_file(path):
    require(not path.is_symlink() and path.is_file(), "UNOWNED_OUTPUT")
    info = path.stat()
    require(info.st_uid == os.getuid() and not info.st_mode & 0o077
            and info.st_nlink == 1, "UNOWNED_OUTPUT")


def read_json(path):
    _safe_file(path)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path, value):
    pending = path.with_name(path.name + ".pending")
    require(not pending.exists() and not pending.is_symlink(), "UNOWNED_OUTPUT")
    if path.exists() or path.is_symlink():
        _safe_file(path)
    try:
        fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(pending, path)
    finally:
        if pending.exists() and not pending.is_symlink():
            pending.unlink()
