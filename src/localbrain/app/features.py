"""Explicit feature set shared by web and CLI composition, not a user setting."""

KNOWN_FEATURE_PACKAGES = frozenset({
    "atlassian", "workstreams", "workflow", "auto_work", "context_search", "google_drive",
})

# Delivery availability is tracked in docs/plans/project/feature-availability.md.
DEFAULT_FEATURE_PACKAGES = KNOWN_FEATURE_PACKAGES - {"context_search", "google_drive"}
