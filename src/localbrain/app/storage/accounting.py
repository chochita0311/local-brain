"""Read-only, per-location logical file sizes and filesystem capacity."""

import os
from pathlib import Path
import shutil
import stat


def directory_size(root):
    root = Path(root)
    try:
        info = root.stat()
    except FileNotFoundError:
        return {"bytes": 0, "state": "missing"}
    except OSError:
        return {"bytes": None, "state": "unavailable"}
    if not stat.S_ISDIR(info.st_mode):
        return {"bytes": None, "state": "unavailable"}
    size, seen, errors = 0, set(), []
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=errors.append):
        dirs[:] = [name for name in dirs if not (Path(parent) / name).is_symlink()]
        for name in files:
            path = Path(parent) / name
            try:
                info = path.lstat()
            except OSError as error:
                errors.append(error)
                continue
            if not stat.S_ISREG(info.st_mode):
                continue
            identity = (info.st_dev, info.st_ino) if info.st_ino else path
            if identity not in seen:
                size += info.st_size
                seen.add(identity)
    return {"bytes": size, "state": "partial" if errors else "complete"}


def volume_status(root):
    """A future directory consumes its nearest existing ancestor's volume."""
    candidate = Path(root)
    while True:
        try:
            info = candidate.stat()
            usage = shutil.disk_usage(candidate)
        except FileNotFoundError:
            if candidate == candidate.parent:
                break
            candidate = candidate.parent
            continue
        except OSError:
            break
        return {"id": str(info.st_dev), "free_bytes": usage.free, "state": "complete"}
    return {"id": None, "free_bytes": None, "state": "unavailable"}


def location_status(root):
    return {**directory_size(root), "volume": volume_status(root)}
