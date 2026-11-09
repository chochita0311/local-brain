"""User-wide public model cache; private inference state stays with its app."""

from pathlib import Path

from localbrain.foundation.paths import hub_cache_root
from localbrain.foundation.validation import require


def registration_cache_root(value):
    """Explicit model selection wins; old registrations keep HF environment rules."""
    selected = value.get("cache_root")
    if selected is None:
        return hub_cache_root()
    require(isinstance(selected, str) and selected and Path(selected).is_absolute()
            and not any(ord(c) < 32 for c in selected), "INVALID_MODEL")
    return Path(selected).resolve()


def hub_repository(model_id, cache_root=None):
    parts = model_id.split("/") if isinstance(model_id, str) else []
    require(len(parts) == 2 and all(part and part not in {".", ".."}
            and all(c.isascii() and (c.isalnum() or c in "-_.") for c in part)
            for part in parts), "INVALID_MODEL")
    repository = Path(cache_root or hub_cache_root()).resolve() / ("models--" + "--".join(parts))
    require(repository.resolve() == repository, "INVALID_MODEL")
    return repository


def hub_snapshot(model_id, revision, relative, cache_root=None):
    require(isinstance(revision, str) and len(revision) == 40
            and all(c in "0123456789abcdef" for c in revision), "INVALID_MODEL")
    cache = Path(cache_root or hub_cache_root()).resolve()
    repository = hub_repository(model_id, cache)
    snapshot = repository / "snapshots" / revision
    require(relative == snapshot.relative_to(cache).as_posix()
            and snapshot.resolve() == snapshot and snapshot.is_dir(), "INVALID_MODEL")
    return snapshot, repository
