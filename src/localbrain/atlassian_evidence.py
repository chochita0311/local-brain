import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence
from urllib.parse import parse_qs, urlsplit

from .atlassian import (
    AtlassianContractError,
    NormalizedAtlassianUrl,
    create_or_reuse_atlassian_stub,
    normalize_atlassian_url,
)
from .ingest.common import (
    EVIDENCE_EXTRACTOR_VERSION,
    ParsedUrlEvidence,
    visible_url_evidence,
)
from .workstreams import utc_now


JIRA_PATH_PATTERN = re.compile(
    r"/(?:browse|issues)/([A-Z][A-Z0-9_]*-\d+)(?:/|$)",
    re.IGNORECASE,
)
CONFLUENCE_PAGE_PATTERN = re.compile(
    r"/(?:wiki/)?(?:spaces/[^/]+/)?pages/(\d+)(?:/|$)",
    re.IGNORECASE,
)
MAX_SOURCE_EVIDENCE = 500


@dataclass(frozen=True)
class RecognizedAtlassianItemUrl:
    source_instance_id: Optional[int]
    site_id: int
    service: str
    normalized: NormalizedAtlassianUrl
    observed_remote_id: Optional[str]
    observed_remote_key: Optional[str]


@contextmanager
def _atomic(connection: sqlite3.Connection, name: str):
    connection.execute("SAVEPOINT {}".format(name))
    try:
        yield
    except Exception:
        connection.execute("ROLLBACK TO {}".format(name))
        connection.execute("RELEASE {}".format(name))
        raise
    else:
        connection.execute("RELEASE {}".format(name))


def _hash_payload(value: object) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def session_evidence_source_fingerprint(
    *,
    source_id: int,
    source_path: str,
    size_bytes: int,
    mtime_ns: int,
) -> str:
    return _hash_payload(
        {
            "kind": "session",
            "source_id": source_id,
            "source_path": source_path,
            "size_bytes": size_bytes,
            "mtime_ns": mtime_ns,
        }
    )


def document_evidence_source_fingerprint(content_hash: str) -> str:
    return _hash_payload({"kind": "document", "content_hash": content_hash})


def configured_atlassian_site_fingerprint(
    connection: sqlite3.Connection,
) -> str:
    rows = connection.execute(
        """
        SELECT atlassian_sites.id AS site_id,
               scoped_sites.service,
               atlassian_sites.normalized_domain
        FROM atlassian_sites
        JOIN (
            SELECT atlassian_site_bindings.site_id,
                   external_source_instances.service
            FROM atlassian_site_bindings
            JOIN external_source_instances
              ON external_source_instances.id =
                 atlassian_site_bindings.source_instance_id
            WHERE external_source_instances.enabled = 1
            UNION
            SELECT site_id, service FROM atlassian_items
            UNION
            SELECT site_id, service FROM atlassian_spaces
        ) AS scoped_sites
          ON scoped_sites.site_id = atlassian_sites.id
        ORDER BY atlassian_sites.id, scoped_sites.service
        """
    ).fetchall()
    return _hash_payload([dict(row) for row in rows])


def _service_identity(
    normalized: NormalizedAtlassianUrl,
) -> Optional[tuple[str, Optional[str], Optional[str]]]:
    parsed = urlsplit(normalized.normalized_url)
    path = parsed.path or "/"
    query = parse_qs(parsed.query)

    jira_match = JIRA_PATH_PATTERN.search(path)
    jira_key = jira_match.group(1).upper() if jira_match else None
    if jira_key is None:
        for name in ("selectedIssue", "issueKey", "key"):
            values = query.get(name) or query.get(name.lower())
            if not values:
                continue
            candidate = values[0].strip().upper()
            if re.fullmatch(r"[A-Z][A-Z0-9_]*-\d+", candidate):
                jira_key = candidate
                break
    if jira_key is not None and "/rest/" not in path.lower():
        return "jira", None, jira_key

    page_match = CONFLUENCE_PAGE_PATTERN.search(path)
    page_id = page_match.group(1) if page_match else None
    if page_id is None:
        for name in ("pageId", "pageid"):
            values = query.get(name)
            if values and values[0].strip().isdigit():
                page_id = values[0].strip()
                break
    if page_id is not None and "/rest/" not in path.lower():
        return "confluence", page_id, None
    return None


def recognize_configured_atlassian_item_url(
    connection: sqlite3.Connection, url: str
) -> Optional[RecognizedAtlassianItemUrl]:
    try:
        normalized = normalize_atlassian_url(url)
    except AtlassianContractError:
        return None
    identity = _service_identity(normalized)
    if identity is None:
        return None
    service, remote_id, remote_key = identity
    rows = connection.execute(
        """
        SELECT DISTINCT atlassian_sites.id AS site_id
        FROM atlassian_sites
        JOIN (
            SELECT atlassian_site_bindings.site_id,
                   external_source_instances.service
            FROM atlassian_site_bindings
            JOIN external_source_instances
              ON external_source_instances.id =
                 atlassian_site_bindings.source_instance_id
            WHERE external_source_instances.enabled = 1
            UNION
            SELECT site_id, service FROM atlassian_items
            UNION
            SELECT site_id, service FROM atlassian_spaces
        ) AS scoped_sites
          ON scoped_sites.site_id = atlassian_sites.id
        WHERE atlassian_sites.normalized_domain = ?
          AND scoped_sites.service = ?
        ORDER BY atlassian_sites.id
        """,
        (normalized.normalized_domain, service),
    ).fetchall()
    if len(rows) != 1:
        return None
    row = rows[0]
    access_rows = connection.execute(
        """
        SELECT external_source_instances.id
        FROM atlassian_site_bindings
        JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_site_bindings.source_instance_id
        WHERE atlassian_site_bindings.site_id = ?
          AND external_source_instances.service = ?
          AND external_source_instances.enabled = 1
        ORDER BY external_source_instances.id
        """,
        (row["site_id"], service),
    ).fetchall()
    return RecognizedAtlassianItemUrl(
        source_instance_id=(
            int(access_rows[0]["id"]) if len(access_rows) == 1 else None
        ),
        site_id=int(row["site_id"]),
        service=service,
        normalized=normalized,
        observed_remote_id=remote_id,
        observed_remote_key=remote_key,
    )


def document_url_evidence(body: str) -> list[ParsedUrlEvidence]:
    evidence = []
    for line_number, line in enumerate((body or "").splitlines(), start=1):
        evidence.extend(
            visible_url_evidence(line, source_line=line_number)
        )
        if len(evidence) >= MAX_SOURCE_EVIDENCE:
            return evidence[:MAX_SOURCE_EVIDENCE]
    return evidence


def _scan_row(
    connection: sqlite3.Connection,
    *,
    session_id: Optional[int] = None,
    source_path: Optional[str] = None,
    document_id: Optional[int] = None,
):
    if (session_id is None) == (document_id is None):
        raise ValueError("Evidence scan requires exactly one source")
    if session_id is not None:
        if not source_path:
            raise ValueError("Session evidence scan requires source_path")
        return connection.execute(
            """
            SELECT * FROM atlassian_evidence_scans
            WHERE session_id = ? AND source_path = ?
            """,
            (session_id, source_path),
        ).fetchone()
    column = "document_id"
    value = document_id
    return connection.execute(
        "SELECT * FROM atlassian_evidence_scans WHERE {} = ?".format(column),
        (value,),
    ).fetchone()


def evidence_scan_is_current(
    connection: sqlite3.Connection,
    *,
    source_fingerprint: str,
    session_id: Optional[int] = None,
    source_path: Optional[str] = None,
    document_id: Optional[int] = None,
) -> bool:
    row = _scan_row(
        connection,
        session_id=session_id,
        source_path=source_path,
        document_id=document_id,
    )
    if not row:
        return False
    return bool(
        row["status"] == "ok"
        and row["source_fingerprint"] == source_fingerprint
        and row["site_fingerprint"]
        == configured_atlassian_site_fingerprint(connection)
        and row["extractor_version"] == EVIDENCE_EXTRACTOR_VERSION
    )


def _record_scan(
    connection: sqlite3.Connection,
    *,
    source_fingerprint: str,
    site_fingerprint: str,
    status: str,
    session_id: Optional[int] = None,
    source_path: Optional[str] = None,
    document_id: Optional[int] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    existing = _scan_row(
        connection,
        session_id=session_id,
        source_path=source_path,
        document_id=document_id,
    )
    now = utc_now()
    values = (
        source_fingerprint,
        site_fingerprint,
        EVIDENCE_EXTRACTOR_VERSION,
        status,
        error_code,
        error_message[:500] if error_message else None,
        now,
        now,
    )
    if existing:
        connection.execute(
            """
            UPDATE atlassian_evidence_scans
            SET source_fingerprint = ?, site_fingerprint = ?,
                extractor_version = ?, status = ?, error_code = ?,
                error_message = ?, scanned_at = ?, updated_at = ?
            WHERE id = ?
            """,
            values + (existing["id"],),
        )
        return
    connection.execute(
        """
        INSERT INTO atlassian_evidence_scans(
            session_id, source_path, document_id,
            source_fingerprint, site_fingerprint,
            extractor_version, status, error_code, error_message,
            scanned_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (session_id, source_path, document_id) + values,
    )


def _source_predicate(
    session_id: Optional[int],
    source_path: Optional[str],
    document_id: Optional[int],
) -> tuple[str, tuple]:
    if (session_id is None) == (document_id is None):
        raise ValueError("Evidence requires exactly one source")
    if session_id is not None:
        if not source_path:
            raise ValueError("Session evidence requires source_path")
        return "session_id = ? AND source_path = ?", (session_id, source_path)
    assert document_id is not None
    return "document_id = ?", (document_id,)


def _evidence_key(
    *,
    external_resource_id: int,
    session_id: Optional[int],
    source_path: Optional[str],
    document_id: Optional[int],
    candidate: ParsedUrlEvidence,
    normalized_url: str,
) -> str:
    return _hash_payload(
        {
            "external_resource_id": external_resource_id,
            "session_id": session_id,
            "source_path": source_path,
            "document_id": document_id,
            "source_channel": candidate.source_channel,
            "source_event_id": candidate.source_event_id,
            "source_line": candidate.source_line,
            "url_ordinal": candidate.url_ordinal,
            "normalized_url": normalized_url,
            "extractor_version": EVIDENCE_EXTRACTOR_VERSION,
        }
    )


def _reconcile_source_evidence(
    connection: sqlite3.Connection,
    *,
    source_fingerprint: str,
    candidates: Sequence[ParsedUrlEvidence],
    session_id: Optional[int] = None,
    source_path: Optional[str] = None,
    document_id: Optional[int] = None,
) -> int:
    predicate, predicate_values = _source_predicate(
        session_id, source_path, document_id
    )
    site_fingerprint = configured_atlassian_site_fingerprint(connection)
    now = utc_now()
    evidence_keys = []
    try:
        with _atomic(connection, "atlassian_evidence_reconciliation"):
            for candidate in candidates[:MAX_SOURCE_EVIDENCE]:
                recognized = recognize_configured_atlassian_item_url(
                    connection, candidate.observed_url
                )
                if recognized is None:
                    continue
                item = create_or_reuse_atlassian_stub(
                    connection,
                    source_instance_id=recognized.source_instance_id,
                    service=recognized.service,
                    site_id=recognized.site_id,
                    url=candidate.observed_url,
                    observed_at=candidate.observed_at or now,
                )
                external_resource_id = int(item["external_resource_id"])
                evidence_key = _evidence_key(
                    external_resource_id=external_resource_id,
                    session_id=session_id,
                    source_path=source_path,
                    document_id=document_id,
                    candidate=candidate,
                    normalized_url=recognized.normalized.normalized_url,
                )
                evidence_keys.append(evidence_key)
                observed_remote_id = (
                    candidate.observed_remote_id
                    or recognized.observed_remote_id
                )
                connection.execute(
                    """
                    INSERT INTO atlassian_item_evidence(
                        external_resource_id, session_id, source_path, document_id,
                        source_channel, source_event_id, source_line,
                        url_ordinal, observed_url, normalized_url,
                        observed_remote_id, observed_title, observed_at,
                        extractor_version, evidence_key,
                        first_observed_at, last_observed_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(evidence_key) DO UPDATE SET
                        observed_url = excluded.observed_url,
                        observed_remote_id = excluded.observed_remote_id,
                        observed_title = excluded.observed_title,
                        observed_at = excluded.observed_at,
                        last_observed_at = excluded.last_observed_at,
                        updated_at = excluded.updated_at
                    """,
                    (
                        external_resource_id,
                        session_id,
                        source_path,
                        document_id,
                        candidate.source_channel,
                        candidate.source_event_id,
                        candidate.source_line,
                        candidate.url_ordinal,
                        candidate.observed_url,
                        recognized.normalized.normalized_url,
                        observed_remote_id,
                        candidate.observed_title,
                        candidate.observed_at,
                        EVIDENCE_EXTRACTOR_VERSION,
                        evidence_key,
                        now,
                        now,
                        now,
                    ),
                )
            if evidence_keys:
                placeholders = ",".join("?" for _ in evidence_keys)
                connection.execute(
                    """
                    DELETE FROM atlassian_item_evidence
                    WHERE {} AND evidence_key NOT IN ({})
                    """.format(predicate, placeholders),
                    predicate_values + tuple(evidence_keys),
                )
            else:
                connection.execute(
                    "DELETE FROM atlassian_item_evidence WHERE {}".format(
                        predicate
                    ),
                    predicate_values,
                )
            _record_scan(
                connection,
                session_id=session_id,
                source_path=source_path,
                document_id=document_id,
                source_fingerprint=source_fingerprint,
                site_fingerprint=site_fingerprint,
                status="ok",
            )
    except Exception as exc:
        _record_scan(
            connection,
            session_id=session_id,
            source_path=source_path,
            document_id=document_id,
            source_fingerprint=source_fingerprint,
            site_fingerprint=site_fingerprint,
            status="error",
            error_code=(
                exc.code
                if isinstance(exc, AtlassianContractError)
                else "evidence-reconciliation-error"
            ),
            error_message=str(exc),
        )
        return 0
    return len(evidence_keys)


def reconcile_session_evidence(
    connection: sqlite3.Connection,
    *,
    session_id: int,
    source_path: str,
    source_fingerprint: str,
    candidates: Sequence[ParsedUrlEvidence],
) -> int:
    session = connection.execute(
        """
        SELECT session_class, session_role, index_policy
        FROM sessions WHERE id = ?
        """,
        (session_id,),
    ).fetchone()
    if not session:
        raise LookupError("Session not found")
    if (
        session["session_class"] != "work"
        or session["session_role"] != "primary"
        or session["index_policy"] != "full"
    ):
        connection.execute(
            """
            DELETE FROM atlassian_item_evidence
            WHERE session_id = ? AND source_path = ?
            """,
            (session_id, source_path),
        )
        connection.execute(
            """
            DELETE FROM atlassian_evidence_scans
            WHERE session_id = ? AND source_path = ?
            """,
            (session_id, source_path),
        )
        _record_scan(
            connection,
            session_id=session_id,
            source_path=source_path,
            source_fingerprint=source_fingerprint,
            site_fingerprint=configured_atlassian_site_fingerprint(connection),
            status="ok",
        )
        return 0
    return _reconcile_source_evidence(
        connection,
        session_id=session_id,
        source_path=source_path,
        source_fingerprint=source_fingerprint,
        candidates=candidates,
    )


def reconcile_document_evidence(
    connection: sqlite3.Connection,
    *,
    document_id: int,
    source_fingerprint: str,
    body: str,
) -> int:
    document = connection.execute(
        """
        SELECT context_documents.id
        FROM context_documents
        JOIN context_roots
          ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.id = ?
          AND context_roots.enabled = 1
        """,
        (document_id,),
    ).fetchone()
    if not document:
        clear_document_evidence(connection, document_id)
        return 0
    return _reconcile_source_evidence(
        connection,
        document_id=document_id,
        source_fingerprint=source_fingerprint,
        candidates=document_url_evidence(body),
    )


def clear_document_evidence(
    connection: sqlite3.Connection, document_id: int
) -> None:
    connection.execute(
        "DELETE FROM atlassian_item_evidence WHERE document_id = ?",
        (document_id,),
    )
    connection.execute(
        "DELETE FROM atlassian_evidence_scans WHERE document_id = ?",
        (document_id,),
    )


def clear_context_root_evidence(
    connection: sqlite3.Connection, context_root_id: int
) -> None:
    rows = connection.execute(
        "SELECT id FROM context_documents WHERE context_root_id = ?",
        (context_root_id,),
    ).fetchall()
    for row in rows:
        clear_document_evidence(connection, int(row["id"]))
