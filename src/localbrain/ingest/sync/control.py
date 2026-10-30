"""Shared cooperative scan cancellation and safe progress delivery."""

from contextvars import ContextVar
from typing import Any, Callable, Dict, Optional


ScanProgressCallback = Callable[[Dict[str, Any]], None]


def _emit_scan_progress(
    progress: Optional[ScanProgressCallback], event: Dict[str, Any]
) -> None:
    if progress is None:
        return
    try:
        progress(event)
    except Exception:
        return


_SCAN_CANCELLED = ContextVar("localbrain_scan_cancelled", default=None)


def _check_scan_cancelled():
    callback = _SCAN_CANCELLED.get()
    if callback and callback():
        raise InterruptedError("Source scan stopped")
