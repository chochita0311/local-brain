"""URL shape descriptions without registration, storage or feature state."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UrlLocator:
    kind: str
    service: Optional[str] = None
    family: Optional[str] = None
    normalized_domain: Optional[str] = None
    canonical_base_url: Optional[str] = None
    safe_locator_url: Optional[str] = None
    item_identity_kind: Optional[str] = None
    item_identity: Optional[str] = None
    reference_kind: Optional[str] = None
    reference_identity: Optional[str] = None
    container_hint: Optional[str] = None
    reason: Optional[str] = None
