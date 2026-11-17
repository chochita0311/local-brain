"""Explicit feature set shared by web and CLI composition, not a user setting."""
import sys

KNOWN_FEATURE_PACKAGES = frozenset({
    "atlassian", "workstreams", "workflow", "auto_work", "context_search", "google_drive", "terminal",
})

# Delivery availability is tracked in docs/plans/project/feature-availability.md.
DEFAULT_FEATURE_PACKAGES = KNOWN_FEATURE_PACKAGES - {"context_search", "google_drive"}


def available_feature_packages(selected, *, desktop):
    """Validate assembly input before applying the distributed desktop boundary.

    Desktop admits terminal only. Other optional callbacks and startup work stay
    excluded; route middleware alone cannot provide that assembly boundary.
    """
    selected = frozenset(selected)
    if not selected <= KNOWN_FEATURE_PACKAGES:
        raise ValueError("Unknown application feature package")
    if desktop:
        return selected & {"terminal"} if sys.platform == "darwin" else frozenset()
    return selected if sys.platform == "darwin" else selected - {"terminal"}
