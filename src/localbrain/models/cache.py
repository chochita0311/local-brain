"""User-wide public model cache; private inference state stays with its app."""

from localbrain.foundation.paths import hub_cache_root
from localbrain.foundation.validation import require


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
