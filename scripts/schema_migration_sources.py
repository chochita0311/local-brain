"""Fingerprint the complete compatible-schema implementation after package splits."""

import hashlib
import json


def migration_source_files(root):
    persistence = root / "src/localbrain/persistence"
    paths = [persistence / "db.py", persistence / "bootstrap.py"]
    paths.extend(sorted((persistence / "migrations").glob("*.py")))
    return [{"path": path.relative_to(root).as_posix(),
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in paths]


def migration_source_digest(root):
    manifest = migration_source_files(root)
    return hashlib.sha256(json.dumps(
        manifest, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
