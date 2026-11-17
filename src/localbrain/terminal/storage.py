"""Generic cache cleanup delegates immutable terminal retirement to its Rust owner."""
from .core import TerminalError, TerminalService


def maintain_cache(config):
    control = TerminalService(config)
    try:
        preview = control.call("runtime.retire", {"preview": True})
        if preview["state"] == "absent":
            return {"removed_bytes": 0, "protected": []}
        candidates = preview["receipt"]["candidates"]
        ids = [entry["payloadId"] for entry in candidates]
        # Byte accounting is advisory; Rust alone verifies identities and deletes.
        size = sum(path.stat().st_size for id in ids for path in (control.root / "payloads" / id).rglob("*")
                   if path.is_file() and not path.is_symlink())
        if ids:
            control.call("runtime.retire", {"preview": False, "expectedReceipt": preview["receipt"], "payloadIds": ids})
        return {"removed_bytes": size, "protected": [{"feature": "terminal", "reason": entry["reason"]} for entry in preview["protected"]]}
    except (TerminalError, OSError, KeyError, TypeError):
        # An unavailable runtime is protected while other eligible caches can clear.
        return {"removed_bytes": 0, "protected": [{"feature": "terminal", "reason": "in_use_or_unknown"}]}
