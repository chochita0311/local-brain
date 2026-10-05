"""LocalBrain-owned setup for pinned public models; no private input arguments."""

import fcntl
import hashlib
import importlib.util
import json
import os
import stat
from contextlib import contextmanager
from pathlib import Path

from .config import settings
from .model_cache import hub_cache_root, hub_repository, hub_snapshot
from .runtime_storage import private_directory
from .session_simulation import atomic_json, read_json
from .session_simulation_model import verified_assets
from .work_context_model import install as install_context, verify as verify_context
from .work_reconstruction import ExperimentError, require


from .model_catalog import (EMBEDDING_SCHEMA, EMBEDDING_ID, EMBEDDING_REVISION,
                            EMBEDDING_FINGERPRINT, EMBEDDING_ASSETS, MODELS, RUNTIME_MODULES)


def model_root(key, data_dir=None):
    require(key in MODELS, "INVALID_MODEL")
    data = Path(data_dir or settings.data_dir).expanduser().resolve()
    legacy = data / MODELS[key]["slug"]
    canonical = data / "models" / MODELS[key]["slug"]
    # Existing LocalBrain installations keep their owner and location.
    return legacy if legacy.exists() and not canonical.exists() else canonical


def runtime_missing():
    return [name for name in RUNTIME_MODULES if importlib.util.find_spec(name) is None]


@contextmanager
def embedding_installation(root):
    root = Path(root)
    require(root.is_absolute() and not root.is_symlink(), "INVALID_MODEL_ROOT")
    private_directory(root.parent)
    marker = {"owner": EMBEDDING_SCHEMA, "model": EMBEDDING_ID, "revision": EMBEDDING_REVISION}
    if not root.exists():
        root.mkdir(mode=0o700)
        atomic_json(root / "owner.json", marker)
    info = root.stat()
    require(info.st_uid == os.getuid() and stat.S_ISDIR(info.st_mode) and not info.st_mode & 0o077,
            "UNOWNED_MODEL")
    require(read_json(root / "owner.json") == marker and {p.name for p in root.iterdir()}
            <= {"owner.json", "install.lock", "model.json", "model.json.pending"}, "UNOWNED_MODEL")
    fd = os.open(root / "install.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        require(os.fstat(fd).st_nlink == 1 and os.fstat(fd).st_uid == os.getuid(), "UNOWNED_MODEL")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ExperimentError("MODEL_BUSY") from None
        pending = root / "model.json.pending"
        if pending.exists() or pending.is_symlink():
            info = pending.lstat()
            require(not pending.is_symlink() and stat.S_ISREG(info.st_mode)
                    and info.st_uid == os.getuid() and info.st_nlink == 1
                    and not info.st_mode & 0o077, "UNOWNED_MODEL")
            pending.unlink()
        yield root
    finally:
        os.close(fd)


def embedding_inventory(snapshot, repository):
    names = {p.relative_to(snapshot).as_posix() for p in snapshot.rglob("*") if p.is_file()}
    require(set(EMBEDDING_ASSETS) <= names and not names - set(EMBEDDING_ASSETS)
            - {"README.md", "LICENSE", "LICENSE.txt", ".gitattributes"}, "INVALID_MODEL")
    files = []
    for name in sorted(EMBEDDING_ASSETS):
        path = snapshot / name
        require(path.is_file() and repository in path.resolve().parents, "INVALID_MODEL")
        hasher = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
        files.append({"path": name, "size": path.stat().st_size, "sha256": hasher.hexdigest()})
    fingerprint = hashlib.sha256((json.dumps(files, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()).hexdigest()
    require(fingerprint == EMBEDDING_FINGERPRINT, "MODEL_ASSETS_CHANGED")
    return files


def install_embedding(root, *, local_only=False):
    os.environ.update(HF_HUB_DISABLE_TELEMETRY="1", DO_NOT_TRACK="1",
                      HF_HUB_DISABLE_IMPLICIT_TOKEN="1", HF_HUB_DISABLE_XET="1")
    with embedding_installation(root) as root:
        if (root / "model.json").exists():
            return verified_assets(root / "model.json")
        cache, repository = hub_cache_root(), hub_repository(EMBEDDING_ID)
        snapshot = repository / "snapshots" / EMBEDDING_REVISION
        for path in repository.rglob("*"):
            require(repository in path.resolve().parents, "INVALID_MODEL")
        if not snapshot.is_dir() or not all((snapshot / name).is_file() for name in EMBEDDING_ASSETS):
            require(not local_only, "MODEL_NOT_CACHED")
            from huggingface_hub import snapshot_download
            snapshot = Path(snapshot_download(repo_id=EMBEDDING_ID, revision=EMBEDDING_REVISION,
                            cache_dir=cache, allow_patterns=list(EMBEDDING_ASSETS),
                            endpoint="https://huggingface.co", token=False, max_workers=3)).resolve()
        relative = (repository / "snapshots" / EMBEDDING_REVISION).relative_to(cache).as_posix()
        expected, repository = hub_snapshot(EMBEDDING_ID, EMBEDDING_REVISION, relative)
        require(snapshot == expected, "INVALID_MODEL")
        files = embedding_inventory(snapshot, repository)
        atomic_json(root / "model.json", {"schema": EMBEDDING_SCHEMA, "model_id": EMBEDDING_ID,
                    "requested_revision": EMBEDDING_REVISION, "resolved_revision": EMBEDDING_REVISION,
                    "fingerprint": EMBEDDING_FINGERPRINT, "snapshot": relative, "files": files})
        return snapshot, {"model_id": EMBEDDING_ID, "resolved_revision": EMBEDDING_REVISION,
                          "fingerprint": EMBEDDING_FINGERPRINT}


def install_model(key, *, local_only=False):
    root = model_root(key)
    private_directory(settings.data_dir)
    private_directory(root.parent)
    if key == "embedding":
        return install_embedding(root, local_only=local_only)
    return install_context(root, MODELS[key]["id"], local_only=local_only)


def verify_model(key):
    root = model_root(key)
    if key == "embedding":
        # Verification holds the same metadata lock as installation.
        require(root.exists(), "MODEL_NOT_INSTALLED")
        with embedding_installation(root):
            return verified_assets(root / "model.json")
    return verify_context(root, MODELS[key]["id"])


def model_status():
    missing = runtime_missing()
    return {"runtime": "READY" if not missing else "LOCAL_MODELS_EXTRA_REQUIRED",
            "missing_modules": missing,
            "models": [{"key": key, "model_id": spec["id"], "purpose": spec["purpose"],
                        "state": "PRESENT_UNVERIFIED" if (model_root(key) / "model.json").is_file() else "NOT_INSTALLED"}
                       for key, spec in MODELS.items()]}
