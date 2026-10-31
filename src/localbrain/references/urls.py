"""Pure URL interpretation and stable reference identities, with no registration lookup."""

import hashlib
import json
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

from .atlassian import atlassian_locator_identity, describe_atlassian_url
from .contracts import UrlLocator


@dataclass(frozen=True)
class ParsedUrl:
    normalized_url: str
    target_key: str
    observed_identity: str
    locator: Optional[UrlLocator] = None


def parse_url(value: str) -> Optional[ParsedUrl]:
    """Classify known URL forms, reject unsafe forms, then admit generic HTTP(S).

    Provider grammar and identity versions live here rather than in optional
    feature packages. Parsing never consults registered sites or items.
    """
    locator = describe_atlassian_url(value)
    if locator.kind in {"item", "structure", "site"}:
        identity = atlassian_locator_identity(locator)
        assert identity is not None
        assert locator.safe_locator_url is not None
        return ParsedUrl(
            normalized_url=locator.safe_locator_url,
            target_key="url:{}".format(_hash_payload(identity)),
            observed_identity=_locator_observed_identity(locator),
            locator=locator,
        )
    if locator.kind == "unsafe":
        return None
    normalized_url = safe_generic_url(value)
    if normalized_url is None:
        return None
    return ParsedUrl(
        normalized_url=normalized_url,
        target_key="url:{}".format(_hash_payload(normalized_url)),
        observed_identity=safe_url_identity(normalized_url),
    )


def trim_url_token(value: str) -> str:
    candidate = value.rstrip(".,;:!?")
    opening_for = {")": "(", "]": "[", "}": "{"}
    openings = set(opening_for.values())
    stack = []
    for index, character in enumerate(candidate):
        if character in openings:
            stack.append(character)
            continue
        expected = opening_for.get(character)
        if expected is None:
            continue
        if stack and stack[-1] == expected:
            stack.pop()
            continue
        return candidate[:index].rstrip(".,;:!?")
    return candidate


def safe_generic_url(value: str) -> Optional[str]:
    try:
        parsed = urlsplit(trim_url_token(value.strip()))
        port = parsed.port
    except (TypeError, ValueError):
        return None
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname
    if (
        scheme not in {"http", "https"}
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    hostname = hostname.lower().rstrip(".")
    if not hostname or any(ord(character) < 32 for character in hostname):
        return None
    netloc = hostname
    if ":" in hostname and not hostname.startswith("["):
        netloc = "[{}]".format(hostname)
    if port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        netloc += ":{}".format(port)
    path = parsed.path or "/"
    if any(ord(character) < 32 for character in path):
        return None
    normalized = urlunsplit((scheme, netloc, path, "", ""))
    return normalized if len(normalized) <= 8000 else None


def safe_url_identity(normalized_url: str) -> str:
    parsed = urlsplit(normalized_url)
    value = parsed.netloc + (parsed.path or "/")
    return value[:500]


def _locator_observed_identity(locator: UrlLocator) -> str:
    identity = locator.item_identity or locator.reference_identity
    value = "{} · {}".format(locator.normalized_domain, locator.family)
    if identity:
        value += ":{}".format(identity)
    return value[:500]


def _hash_payload(value: object) -> str:
    serialized = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
