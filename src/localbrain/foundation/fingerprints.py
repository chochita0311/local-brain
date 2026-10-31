"""Canonical value fingerprints and the separate UTF-8 text digest."""

import hashlib
import json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def key(prefix, *values):
    return prefix + ":" + digest(values)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
