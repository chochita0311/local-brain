"""User-wide public model cache; private inference state stays with its app."""

import os
from pathlib import Path

from .work_reconstruction import require


def hub_cache_root():
    home = os.environ.get("HF_HOME") or str(
        Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "huggingface")
    return Path(os.environ.get("HF_HUB_CACHE") or os.environ.get("HUGGINGFACE_HUB_CACHE")
                or str(Path(home) / "hub")).expanduser().resolve()


def hub_repository(model_id):
    parts = model_id.split("/") if isinstance(model_id, str) else []
    require(len(parts) == 2 and all(part and part not in {".", ".."}
            and all(c.isascii() and (c.isalnum() or c in "-_.") for c in part)
            for part in parts), "INVALID_MODEL")
    repository = hub_cache_root() / ("models--" + "--".join(parts))
    require(repository.resolve() == repository, "INVALID_MODEL")
    return repository


def hub_snapshot(model_id, revision, relative):
    require(isinstance(revision, str) and len(revision) == 40
            and all(c in "0123456789abcdef" for c in revision), "INVALID_MODEL")
    repository = hub_repository(model_id)
    snapshot = repository / "snapshots" / revision
    require(relative == snapshot.relative_to(hub_cache_root()).as_posix()
            and snapshot.resolve() == snapshot and snapshot.is_dir(), "INVALID_MODEL")
    return snapshot, repository
