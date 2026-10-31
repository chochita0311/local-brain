"""Stable reference identities, independent of optional feature registrations.

Bindings retain existing document/bookmark/link IDs and their metadata. Removing
one of those rows removes only its binding, never the shared reference identity.
"""

import hashlib
import os
import sqlite3
from typing import Optional

from localbrain.references.urls import ParsedUrl, parse_url


def _upsert(connection, *, identity_key, kind, locator, product=None, remote_key=None):
    connection.execute(
        """
        INSERT INTO reference_resources(identity_key, kind, locator, product, remote_key)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(identity_key) DO NOTHING
        """,
        (identity_key, kind, locator, product, remote_key),
    )
    return int(connection.execute(
        "SELECT id FROM reference_resources WHERE identity_key = ?", (identity_key,)
    ).fetchone()[0])


def url_resource(connection: sqlite3.Connection, value: str) -> Optional[int]:
    parsed = parse_url(value)
    return parsed_url_resource(connection, parsed) if parsed else None


def parsed_url_resource(connection: sqlite3.Connection, parsed: ParsedUrl) -> int:
    locator = parsed.locator
    return _upsert(
        connection, identity_key=parsed.target_key, kind="url",
        locator=parsed.normalized_url,
        product=locator.service if locator else None,
        remote_key=locator.item_identity if locator and locator.kind == "item" else None,
    )


def path_resource(connection: sqlite3.Connection, value: str) -> int:
    # Notes have provider-owned locators, not filesystem paths. Do not resolve
    # symlinks or read the filesystem while establishing a reference identity.
    kind = "note" if value.startswith("apple-notes:") else "path"
    locator = value if kind == "note" else os.path.abspath(os.path.normpath(os.path.expanduser(value)))
    key = kind + ":" + hashlib.sha256(locator.encode("utf-8")).hexdigest()
    return _upsert(connection, identity_key=key, kind=kind, locator=locator)


def bind_document(connection: sqlite3.Connection, document_id: int) -> int:
    row = connection.execute("SELECT path FROM context_documents WHERE id = ?", (document_id,)).fetchone()
    if row is None:
        raise LookupError("Context Document not found")
    resource_id = path_resource(connection, row["path"])
    connection.execute(
        """INSERT INTO resource_documents(document_id, resource_id) VALUES (?, ?)
        ON CONFLICT(document_id) DO UPDATE SET resource_id = excluded.resource_id""",
        (document_id, resource_id),
    )
    return resource_id


def bind_local_path(connection: sqlite3.Connection, local_resource_id: int) -> int:
    row = connection.execute("SELECT path FROM local_resources WHERE id = ?", (local_resource_id,)).fetchone()
    if row is None:
        raise LookupError("Local resource not found")
    resource_id = path_resource(connection, row["path"])
    connection.execute(
        """INSERT INTO resource_local_paths(local_resource_id, resource_id) VALUES (?, ?)
        ON CONFLICT(local_resource_id) DO UPDATE SET resource_id = excluded.resource_id""",
        (local_resource_id, resource_id),
    )
    return resource_id


def bind_external_link(connection: sqlite3.Connection, external_resource_id: int) -> Optional[int]:
    row = connection.execute("SELECT url FROM external_resources WHERE id = ?", (external_resource_id,)).fetchone()
    if row is None:
        raise LookupError("External resource not found")
    resource_id = url_resource(connection, row["url"])
    if resource_id is None:
        # Preserve legacy metadata, but do not promote an unsafe locator into
        # a navigable shared reference or retain an obsolete binding.
        connection.execute("DELETE FROM resource_external_links WHERE external_resource_id = ?", (external_resource_id,))
        return None
    connection.execute(
        """INSERT INTO resource_external_links(external_resource_id, resource_id) VALUES (?, ?)
        ON CONFLICT(external_resource_id) DO UPDATE SET resource_id = excluded.resource_id""",
        (external_resource_id, resource_id),
    )
    return resource_id


def bind_entity(connection: sqlite3.Connection, entity_type: str, entity_id: str) -> Optional[int]:
    binder = {"document": bind_document, "local": bind_local_path, "external": bind_external_link}.get(entity_type)
    return binder(connection, int(entity_id)) if binder else None


def resource_by_hint(connection: sqlite3.Connection, reference_kind: str, value: str):
    product = {"jira_key": "jira", "confluence_page_id": "confluence"}.get(reference_kind)
    if product is None:
        return None
    rows = connection.execute(
        """SELECT * FROM reference_resources
        WHERE kind = 'url' AND product = ? AND UPPER(remote_key) = UPPER(?)
        ORDER BY id LIMIT 2""", (product, value),
    ).fetchall()
    return rows[0] if len(rows) == 1 else None
