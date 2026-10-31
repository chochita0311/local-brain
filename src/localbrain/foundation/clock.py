"""Existing UTC clocks and bounded timezone-aware timestamp decoding."""

from datetime import datetime, timezone

from localbrain.foundation.validation import ExperimentError, require


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    require(isinstance(value, str) and len(value) <= 80)
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(result.tzinfo is not None)
        return result
    except (ValueError, OverflowError):
        raise ExperimentError("INVALID_TIME") from None


def now():
    return datetime.now(timezone.utc)
