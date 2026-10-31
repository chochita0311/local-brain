from typing import Optional


def _clean(value: Optional[str]) -> Optional[str]:
    return (value or "").strip() or None
