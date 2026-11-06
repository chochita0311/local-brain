"""Explicit feature set shared by web and CLI composition, not a user setting."""

KNOWN_FEATURE_PACKAGES = frozenset({
    "atlassian", "workstreams", "workflow", "auto_work", "context_search", "google_drive",
})

# Delivery availability is tracked in docs/plans/project/feature-availability.md.
DEFAULT_FEATURE_PACKAGES = KNOWN_FEATURE_PACKAGES - {"context_search", "google_drive"}


def available_feature_packages(selected, *, desktop):
    """Validate assembly input before applying the distributed desktop boundary.

    Desktop has no optional product packages. Excluding them here also excludes
    their callbacks and startup work; route middleware alone cannot do that.
    """
    selected = frozenset(selected)
    if not selected <= KNOWN_FEATURE_PACKAGES:
        raise ValueError("Unknown application feature package")
    return frozenset() if desktop else selected
