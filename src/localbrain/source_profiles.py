"""Shared presentation keyed by the local source primary key."""

from .value_registry import display_value_label

PALETTE = {color: display_value_label("source.profile-color", color)
           for color in ("green", "blue", "orange", "yellow", "red", "gray")}
MAX_SOURCE_ID = 2**53 - 1


def valid_source_id(value):
    return type(value) is int and 0 < value <= MAX_SOURCE_ID


def default_color(provider):
    return {"codex": "green", "claude": "orange"}.get(provider, "gray")



def profiles(connection):
    return [dict(row) for row in connection.execute(
        "SELECT id,provider_kind,name,root_path,profile_color,profile_position "
        "FROM sources WHERE provider_kind IN ('codex','claude') "
        "ORDER BY profile_position,id"
    )]


def profile_map(connection):
    """One page snapshot keyed only by the serialized source primary key."""
    return {str(row["id"]): {
        "id": row["id"], "name": row["name"], "provider_kind": row["provider_kind"],
        "color": row["profile_color"] or default_color(row["provider_kind"]),
    } for row in profiles(connection)}


def canonical_source_id(reference):
    """Validate a URL scope; profile names and former aliases are not IDs."""
    value = str(reference)
    if value == "all":
        return value
    if value.isdecimal() and valid_source_id(int(value)):
        return str(int(value))
    return "invalid"
