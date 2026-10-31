"""Explicit storage moves with cache ownership supplied by included features."""

import stat
from functools import partial

from localbrain.foundation.config import cache_directory, development_directory
from localbrain.foundation.files import (
    StorageError, ensure_tree_unchanged, owned_tree, private_directory,
    read_owned_json, tree_is_inactive, validate_runtime_directory,
)


def _model_owner(folder, key):
    from localbrain.models.catalog import EMBEDDING_ID, EMBEDDING_REVISION, EMBEDDING_SCHEMA, MODELS
    from localbrain.models.generation import HUB_MANIFEST_OWNER, OWNER, model_spec
    marker = read_owned_json(folder / "owner.json", 8192)
    manifest = read_owned_json(folder / "model.json")
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


def _development_owner(source):
    owned = source.name == "personal-insight-evaluations"
    if not owned:
        # This historical on-disk format remains recognizable after experiments
        # are removed. Migration must not load their inference implementation.
        owned = (read_owned_json(source / "owner.json", 8192).get("owner")
                 == "localbrain.work-context-evaluation.v1"
                 and {p.name for p in source.iterdir()}
                 <= {"owner.json", "writer.lock", "progress.json", "report.json"})
    return owned


def migrate_storage(config, *, apply=False, include_development=False, cache_owners=None):
    """Move recognized state atomically on one filesystem; never merge copies.

    The caller stops the application and development jobs before applying.
    Development archives require the separate explicit inclusion option.
    Only explicitly supplied feature caches are inspected; other caches stay put.
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
    candidates = [(data / name, cache / name, owner)
                  for name, owner in (cache_owners or {}).items()]
    from localbrain.models.catalog import MODELS
    candidates.extend((data / spec["slug"], data / "models" / spec["slug"], partial(_model_owner, key=key))
                      for key, spec in MODELS.items())
    if include_development:
        candidates.extend((p, development / p.name, _development_owner) for p in sorted(data.iterdir())
                          if p.name == "personal-insight-evaluations"
                          or p.name.startswith(("work-context-", "work-role-", "source-claim-")))
    moves = []
    for source, target, owner in candidates:
        if not source.exists() and not source.is_symlink():
            continue
        try:
            stamps = owned_tree(source)
            if not source.is_dir():
                raise StorageError("UNOWNED_STORAGE")
            owned = owner(source)
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
        if any(not tree_is_inactive(stamps) for _, _, stamps, _ in moves):
            raise StorageError("STORAGE_BUSY_OR_UNAVAILABLE")
        for _, _, stamps, _ in moves:
            ensure_tree_unchanged(stamps)
        for source, target, stamps, size in moves:
            private_directory(target.parent)
            ensure_tree_unchanged(stamps)
            if target.exists() or target.is_symlink():
                raise StorageError("STORAGE_DESTINATION_EXISTS")
            source.rename(target)
            for old, info in stamps:
                moved = target / old.relative_to(source)
                moved.chmod(0o700 if stat.S_ISDIR(info.st_mode) else 0o600)
            result["moved_directories"] += 1
            result["moved_bytes"] += size
    return result
