import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence
from urllib.parse import urlsplit, urlunsplit

from .atlassian import create_or_reuse_atlassian_stub
from .atlassian_evidence import recognize_configured_atlassian_item_url
from .ingest.common import ParsedReferenceCandidate, REFERENCE_EXTRACTOR_VERSION
from .workstreams import utc_now


MAX_REFERENCE_TARGETS = 100
MAX_EVIDENCE_PER_TARGET = 50
MAX_REFERENCE_CANDIDATES = 5_000


class SessionReferenceError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedReferenceEvidence:
    source_path: str
    source_event_id: Optional[str]
    source_line: int
    evidence_ordinal: int
    target_kind: str
    target_key: str
    context_document_id: Optional[int]
    external_resource_id: Optional[int]
    evidence_kind: str
    read_outcome: Optional[str]
    observed_identity: str
    normalized_url: Optional[str]
    tool_name: Optional[str]
    tool_call_id: Optional[str]
    observed_at: Optional[str]


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
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _safe_generic_url(value: str) -> Optional[str]:
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except (TypeError, ValueError):
        return None
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname
    if (
        scheme not in {"http", "https"}
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    hostname = hostname.lower().rstrip(".")
    if not hostname or any(ord(character) < 32 for character in hostname):
        return None
    netloc = hostname
    if ":" in hostname and not hostname.startswith("["):
        netloc = "[{}]".format(hostname)
    if port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        netloc += ":{}".format(port)
    path = parsed.path or "/"
    if any(ord(character) < 32 for character in path):
        return None
    normalized = urlunsplit((scheme, netloc, path, "", ""))
    return normalized if len(normalized) <= 8000 else None


def _safe_url_identity(normalized_url: str) -> str:
    parsed = urlsplit(normalized_url)
    value = parsed.netloc + (parsed.path or "/")
    return value[:500]


def _eligible_document_rows(
    connection: sqlite3.Connection, *, workspace_id: Optional[int] = None
) -> list[sqlite3.Row]:
    query = """
        SELECT context_documents.id, context_documents.path,
               context_documents.relative_path, context_documents.title,
               context_documents.workspace_id, context_documents.context_root_id
        FROM context_documents
        JOIN context_roots
          ON context_roots.id = context_documents.context_root_id
        WHERE context_roots.enabled = 1
          AND context_roots.readable = 1
          AND context_roots.status = 'ready'
    """
    values = ()
    if workspace_id is not None:
        query += " AND context_documents.workspace_id = ?"
        values = (workspace_id,)
    query += " ORDER BY context_documents.id"
    return connection.execute(query, values).fetchall()


def _resolve_markdown(
    connection: sqlite3.Connection,
    *,
    candidate: ParsedReferenceCandidate,
    session: sqlite3.Row,
    source_path: str,
) -> Optional[ResolvedReferenceEvidence]:
    reference = candidate.reference.strip()
    if not reference.lower().endswith(".md"):
        return None
    path = Path(reference)
    rows: list[sqlite3.Row]
    if path.is_absolute():
        normalized_path = os.path.abspath(os.path.normpath(reference))
        rows = [
            row
            for row in _eligible_document_rows(connection)
            if os.path.abspath(os.path.normpath(row["path"])) == normalized_path
        ]
    elif "/" in reference or reference.startswith("."):
        if not session["cwd_raw"]:
            return None
        normalized_path = os.path.abspath(
            os.path.normpath(os.path.join(session["cwd_raw"], reference))
        )
        rows = [
            row
            for row in _eligible_document_rows(connection)
            if os.path.abspath(os.path.normpath(row["path"])) == normalized_path
        ]
    else:
        if session["workspace_id"] is None:
            return None
        rows = [
            row
            for row in _eligible_document_rows(
                connection, workspace_id=int(session["workspace_id"])
            )
            if Path(row["path"]).name == reference
        ]
    if len(rows) != 1:
        return None
    document = rows[0]
    observed_identity = (
        reference if not path.is_absolute() else Path(reference).name
    )[:500]
    return ResolvedReferenceEvidence(
        source_path=source_path,
        source_event_id=candidate.source_event_id,
        source_line=candidate.source_line,
        evidence_ordinal=candidate.evidence_ordinal,
        target_kind="context_document",
        target_key="document:{}".format(document["id"]),
        context_document_id=int(document["id"]),
        external_resource_id=None,
        evidence_kind=candidate.evidence_kind,
        read_outcome=candidate.read_outcome,
        observed_identity=observed_identity,
        normalized_url=None,
        tool_name=candidate.tool_name,
        tool_call_id=candidate.tool_call_id,
        observed_at=candidate.observed_at,
    )


def _configured_item_by_hint(
    connection: sqlite3.Connection, reference_kind: str, reference: str
) -> Optional[sqlite3.Row]:
    if reference_kind == "jira_key":
        rows = connection.execute(
            """
            SELECT atlassian_items.external_resource_id,
                   atlassian_items.remote_key, atlassian_items.remote_id,
                   atlassian_items.service, external_resources.url
            FROM atlassian_items
            JOIN external_resources
              ON external_resources.id = atlassian_items.external_resource_id
            WHERE atlassian_items.service = 'jira'
              AND UPPER(atlassian_items.remote_key) = UPPER(?)
            ORDER BY atlassian_items.external_resource_id
            """,
            (reference,),
        ).fetchall()
    elif reference_kind == "confluence_page_id":
        rows = connection.execute(
            """
            SELECT atlassian_items.external_resource_id,
                   atlassian_items.remote_key, atlassian_items.remote_id,
                   atlassian_items.service, external_resources.url
            FROM atlassian_items
            JOIN external_resources
              ON external_resources.id = atlassian_items.external_resource_id
            WHERE atlassian_items.service = 'confluence'
              AND atlassian_items.remote_id = ?
            ORDER BY atlassian_items.external_resource_id
            """,
            (reference,),
        ).fetchall()
    else:
        return None
    return rows[0] if len(rows) == 1 else None


def _resolved_item(
    *,
    candidate: ParsedReferenceCandidate,
    source_path: str,
    external_resource_id: int,
    normalized_url: str,
    observed_identity: str,
) -> ResolvedReferenceEvidence:
    return ResolvedReferenceEvidence(
        source_path=source_path,
        source_event_id=candidate.source_event_id,
        source_line=candidate.source_line,
        evidence_ordinal=candidate.evidence_ordinal,
        target_kind="atlassian_item",
        target_key="atlassian:{}".format(external_resource_id),
        context_document_id=None,
        external_resource_id=external_resource_id,
        evidence_kind=candidate.evidence_kind,
        read_outcome=candidate.read_outcome,
        observed_identity=observed_identity[:500],
        normalized_url=normalized_url,
        tool_name=candidate.tool_name,
        tool_call_id=candidate.tool_call_id,
        observed_at=candidate.observed_at,
    )


def _resolve_url(
    connection: sqlite3.Connection,
    *,
    candidate: ParsedReferenceCandidate,
    source_path: str,
) -> Optional[ResolvedReferenceEvidence]:
    recognized = recognize_configured_atlassian_item_url(
        connection, candidate.reference
    )
    if recognized is not None:
        hint_kind = (
            "jira_key" if recognized.observed_remote_key else "confluence_page_id"
        )
        hint_value = recognized.observed_remote_key or recognized.observed_remote_id
        configured = (
            _configured_item_by_hint(connection, hint_kind, hint_value)
            if hint_value
            else None
        )
        if configured is not None:
            normalized_url = _safe_generic_url(configured["url"])
            if normalized_url is None:
                return None
            return _resolved_item(
                candidate=candidate,
                source_path=source_path,
                external_resource_id=int(configured["external_resource_id"]),
                normalized_url=normalized_url,
                observed_identity=(
                    configured["remote_key"]
                    or configured["remote_id"]
                    or _safe_url_identity(normalized_url)
                ),
            )
        safe_identity_url = _safe_generic_url(candidate.reference)
        if recognized.observed_remote_key:
            parsed = urlsplit(recognized.normalized.normalized_url)
            safe_identity_url = urlunsplit(
                (
                    parsed.scheme,
                    parsed.netloc,
                    "/browse/{}".format(recognized.observed_remote_key),
                    "",
                    "",
                )
            )
        elif recognized.observed_remote_id and safe_identity_url:
            parsed = urlsplit(safe_identity_url)
            if recognized.observed_remote_id not in parsed.path.split("/"):
                safe_identity_url = urlunsplit(
                    (
                        parsed.scheme,
                        parsed.netloc,
                        "/wiki/pages/{}".format(recognized.observed_remote_id),
                        "",
                        "",
                    )
                )
        if safe_identity_url is None:
            return None
        item = create_or_reuse_atlassian_stub(
            connection,
            source_instance_id=recognized.source_instance_id,
            service=recognized.service,
            site_id=recognized.site_id,
            url=safe_identity_url,
            observed_at=candidate.observed_at or utc_now(),
        )
        external_resource_id = int(item["external_resource_id"])
        identity = (
            recognized.observed_remote_key
            or recognized.observed_remote_id
            or _safe_url_identity(safe_identity_url)
        )
        return _resolved_item(
            candidate=candidate,
            source_path=source_path,
            external_resource_id=external_resource_id,
            normalized_url=safe_identity_url,
            observed_identity=identity,
        )

    normalized_url = _safe_generic_url(candidate.reference)
    if normalized_url is None:
        return None
    return ResolvedReferenceEvidence(
        source_path=source_path,
        source_event_id=candidate.source_event_id,
        source_line=candidate.source_line,
        evidence_ordinal=candidate.evidence_ordinal,
        target_kind="url",
        target_key="url:{}".format(_hash_payload(normalized_url)),
        context_document_id=None,
        external_resource_id=None,
        evidence_kind=candidate.evidence_kind,
        read_outcome=candidate.read_outcome,
        observed_identity=_safe_url_identity(normalized_url),
        normalized_url=normalized_url,
        tool_name=candidate.tool_name,
        tool_call_id=candidate.tool_call_id,
        observed_at=candidate.observed_at,
    )


def _resolve_candidate(
    connection: sqlite3.Connection,
    *,
    candidate: ParsedReferenceCandidate,
    session: sqlite3.Row,
    source_path: str,
) -> Optional[ResolvedReferenceEvidence]:
    if candidate.reference_kind == "markdown":
        return _resolve_markdown(
            connection,
            candidate=candidate,
            session=session,
            source_path=source_path,
        )
    if candidate.reference_kind == "url":
        return _resolve_url(
            connection, candidate=candidate, source_path=source_path
        )
    item = _configured_item_by_hint(
        connection, candidate.reference_kind, candidate.reference
    )
    if item is None:
        return None
    normalized_url = _safe_generic_url(item["url"])
    if normalized_url is None:
        return None
    identity = item["remote_key"] or item["remote_id"] or _safe_url_identity(
        normalized_url
    )
    return _resolved_item(
        candidate=candidate,
        source_path=source_path,
        external_resource_id=int(item["external_resource_id"]),
        normalized_url=normalized_url,
        observed_identity=identity,
    )


def _evidence_rank(kind: str, outcome: Optional[str]) -> int:
    if kind == "resource_read" and outcome == "success":
        return 0
    if kind == "resource_read" and outcome == "failure":
        return 1
    if kind == "tool_result":
        return 2
    if kind == "user_mention":
        return 3
    return 4


def _evidence_key(session_id: int, evidence: ResolvedReferenceEvidence) -> str:
    native_location = (
        "call:" + evidence.tool_call_id
        if evidence.evidence_kind == "resource_read" and evidence.tool_call_id
        else "event:" + evidence.source_event_id
        if evidence.source_event_id
        else "line:{}:{}".format(evidence.source_path, evidence.source_line)
    )
    location = "path:{}|{}".format(evidence.source_path, native_location)
    return _hash_payload(
        {
            "session_id": session_id,
            "location": location,
            "target_key": evidence.target_key,
            "evidence_kind": evidence.evidence_kind,
            "read_outcome": evidence.read_outcome,
            "extractor_version": REFERENCE_EXTRACTOR_VERSION,
        }
    )


def _source_set_fingerprint(
    connection: sqlite3.Connection,
    *,
    session_id: int,
    current_path: str,
    current_size_bytes: int,
    current_mtime_ns: int,
) -> str:
    rows = connection.execute(
        """
        SELECT path, size_bytes, mtime_ns
        FROM source_files
        WHERE session_id = ? AND path != ?
        ORDER BY path
        """,
        (session_id, current_path),
    ).fetchall()
    values = [
        {"path": row["path"], "size_bytes": row["size_bytes"], "mtime_ns": row["mtime_ns"]}
        for row in rows
    ]
    values.append(
        {
            "path": current_path,
            "size_bytes": current_size_bytes,
            "mtime_ns": current_mtime_ns,
        }
    )
    values.sort(key=lambda item: item["path"])
    return _hash_payload(values)


def _recorded_source_set_fingerprint(
    connection: sqlite3.Connection, session_id: int
) -> str:
    rows = connection.execute(
        """
        SELECT path, size_bytes, mtime_ns
        FROM source_files
        WHERE session_id = ?
          AND status = 'ok'
          AND reference_contract_version = ?
        ORDER BY path
        """,
        (session_id, REFERENCE_EXTRACTOR_VERSION),
    ).fetchall()
    return _hash_payload(
        [
            {
                "path": row["path"],
                "size_bytes": row["size_bytes"],
                "mtime_ns": row["mtime_ns"],
            }
            for row in rows
        ]
    )


def _record_scan(
    connection: sqlite3.Connection,
    *,
    session_id: int,
    source_fingerprint: str,
    status: str,
    observed_target_count: int,
    retained_target_count: int,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    now = utc_now()
    connection.execute(
        """
        INSERT INTO session_reference_scans(
            session_id, source_fingerprint, extractor_version, status,
            observed_target_count, retained_target_count,
            error_code, error_message, scanned_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            source_fingerprint = excluded.source_fingerprint,
            extractor_version = excluded.extractor_version,
            status = excluded.status,
            observed_target_count = excluded.observed_target_count,
            retained_target_count = excluded.retained_target_count,
            error_code = excluded.error_code,
            error_message = excluded.error_message,
            scanned_at = excluded.scanned_at,
            updated_at = excluded.updated_at
        """,
        (
            session_id,
            source_fingerprint,
            REFERENCE_EXTRACTOR_VERSION,
            status,
            observed_target_count,
            retained_target_count,
            error_code,
            error_message[:500] if error_message else None,
            now,
            now,
        ),
    )


def session_reference_scan_is_current(
    connection: sqlite3.Connection, session_id: int
) -> bool:
    scan = connection.execute(
        "SELECT * FROM session_reference_scans WHERE session_id = ?", (session_id,)
    ).fetchone()
    if (
        not scan
        or scan["status"] not in {"ok", "partial"}
        or scan["extractor_version"] != REFERENCE_EXTRACTOR_VERSION
    ):
        return False
    rows = connection.execute(
        """
        SELECT 1
        FROM source_files
        WHERE session_id = ?
          AND status = 'ok'
          AND reference_contract_version = ?
        LIMIT 1
        """,
        (session_id, REFERENCE_EXTRACTOR_VERSION),
    ).fetchall()
    if not rows:
        return False
    fingerprint = _recorded_source_set_fingerprint(connection, session_id)
    return scan["source_fingerprint"] == fingerprint


def reconcile_session_references(
    connection: sqlite3.Connection,
    *,
    session_id: int,
    source_path: str,
    source_size_bytes: int,
    source_mtime_ns: int,
    candidates: Sequence[ParsedReferenceCandidate],
    finalize: bool = True,
) -> int:
    session = connection.execute(
        """
        SELECT id, source_id, workspace_id, cwd_raw,
               session_class, session_role, index_policy
        FROM sessions WHERE id = ?
        """,
        (session_id,),
    ).fetchone()
    if not session:
        raise SessionReferenceError("Session not found")
    fingerprint = _source_set_fingerprint(
        connection,
        session_id=session_id,
        current_path=source_path,
        current_size_bytes=source_size_bytes,
        current_mtime_ns=source_mtime_ns,
    )
    if (
        session["session_class"] != "work"
        or session["session_role"] != "primary"
        or session["index_policy"] != "full"
    ):
        connection.execute(
            "DELETE FROM session_reference_evidence WHERE session_id = ?",
            (session_id,),
        )
        connection.execute(
            "DELETE FROM session_reference_scans WHERE session_id = ?",
            (session_id,),
        )
        return 0

    try:
        with _atomic(connection, "session_reference_reconciliation"):
            resolved = []
            seen_locations = set()
            for candidate in candidates[:MAX_REFERENCE_CANDIDATES]:
                item = _resolve_candidate(
                    connection,
                    candidate=candidate,
                    session=session,
                    source_path=source_path,
                )
                if item is None:
                    continue
                location_key = _evidence_key(session_id, item)
                if location_key in seen_locations:
                    continue
                seen_locations.add(location_key)
                resolved.append((location_key, item))

            prior_first_observed = {
                row["evidence_key"]: row["first_observed_at"]
                for row in connection.execute(
                    """
                    SELECT evidence_key, first_observed_at
                    FROM session_reference_evidence
                    WHERE session_id = ? AND source_path = ?
                    """,
                    (session_id, source_path),
                ).fetchall()
            }
            connection.execute(
                """
                DELETE FROM session_reference_evidence
                WHERE session_id = ? AND source_path = ?
                """,
                (session_id, source_path),
            )
            now = utc_now()
            for evidence_key, item in resolved:
                connection.execute(
                    """
                    INSERT INTO session_reference_evidence(
                        session_id, source_path, source_event_id, source_line,
                        evidence_ordinal, target_kind, target_key,
                        context_document_id, external_resource_id,
                        evidence_kind, read_outcome, observed_identity,
                        normalized_url, tool_name, tool_call_id, observed_at,
                        extractor_version, evidence_key,
                        first_observed_at, last_observed_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(evidence_key) DO UPDATE SET
                        observed_identity = excluded.observed_identity,
                        normalized_url = excluded.normalized_url,
                        observed_at = excluded.observed_at,
                        last_observed_at = excluded.last_observed_at,
                        updated_at = excluded.updated_at
                    """,
                    (
                        session_id,
                        item.source_path,
                        item.source_event_id,
                        item.source_line,
                        item.evidence_ordinal,
                        item.target_kind,
                        item.target_key,
                        item.context_document_id,
                        item.external_resource_id,
                        item.evidence_kind,
                        item.read_outcome,
                        item.observed_identity,
                        item.normalized_url,
                        item.tool_name,
                        item.tool_call_id,
                        item.observed_at,
                        REFERENCE_EXTRACTOR_VERSION,
                        evidence_key,
                        prior_first_observed.get(evidence_key, now),
                        now,
                        now,
                    ),
                )

        if finalize:
            return finalize_session_references(
                connection,
                session_id,
                source_fingerprint=fingerprint,
            )
    except Exception as error:
        prior = connection.execute(
            "SELECT * FROM session_reference_scans WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        observed = int(prior["observed_target_count"]) if prior else 0
        retained = int(prior["retained_target_count"]) if prior else 0
        _record_scan(
            connection,
            session_id=session_id,
            source_fingerprint=fingerprint,
            status="error",
            observed_target_count=observed,
            retained_target_count=retained,
            error_code="reference-reconciliation-error",
            error_message=str(error),
        )
        raise SessionReferenceError(str(error)) from error
    return len(resolved)


def finalize_session_references(
    connection: sqlite3.Connection,
    session_id: int,
    *,
    source_fingerprint: Optional[str] = None,
) -> int:
    fingerprint = source_fingerprint or _recorded_source_set_fingerprint(
        connection, session_id
    )
    try:
        with _atomic(connection, "session_reference_finalization"):
            rows = connection.execute(
                """
                SELECT id, target_key, evidence_kind, read_outcome,
                       source_path, source_event_id, source_line,
                       evidence_ordinal, tool_call_id
                FROM session_reference_evidence
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchall()
            target_ranks = {}
            for row in rows:
                rank = _evidence_rank(row["evidence_kind"], row["read_outcome"])
                target_ranks[row["target_key"]] = min(
                    rank, target_ranks.get(row["target_key"], rank)
                )
            ordered_targets = sorted(
                target_ranks, key=lambda key: (target_ranks[key], key)
            )
            observed_total = len(ordered_targets)
            retained_keys = set(ordered_targets[:MAX_REFERENCE_TARGETS])

            if retained_keys:
                placeholders = ",".join("?" for _ in retained_keys)
                connection.execute(
                    """
                    DELETE FROM session_reference_evidence
                    WHERE session_id = ? AND target_key NOT IN ({})
                    """.format(placeholders),
                    (session_id,) + tuple(sorted(retained_keys)),
                )
            else:
                connection.execute(
                    "DELETE FROM session_reference_evidence WHERE session_id = ?",
                    (session_id,),
                )

            retained_rows = [
                row for row in rows if row["target_key"] in retained_keys
            ]
            by_target = {}
            for row in retained_rows:
                by_target.setdefault(row["target_key"], []).append(row)
            excess_ids = []
            for target_rows in by_target.values():
                ordered = sorted(
                    target_rows,
                    key=lambda row: (
                        _evidence_rank(row["evidence_kind"], row["read_outcome"]),
                        row["source_path"],
                        row["source_event_id"] or "",
                        row["source_line"],
                        row["evidence_ordinal"],
                        row["tool_call_id"] or "",
                        row["id"],
                    ),
                )
                excess_ids.extend(
                    row["id"] for row in ordered[MAX_EVIDENCE_PER_TARGET:]
                )
            if excess_ids:
                placeholders = ",".join("?" for _ in excess_ids)
                connection.execute(
                    "DELETE FROM session_reference_evidence WHERE id IN ({})".format(
                        placeholders
                    ),
                    tuple(excess_ids),
                )
            retained_total = connection.execute(
                """
                SELECT COUNT(DISTINCT target_key)
                FROM session_reference_evidence WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()[0]
            _record_scan(
                connection,
                session_id=session_id,
                source_fingerprint=fingerprint,
                status=(
                    "partial"
                    if observed_total > MAX_REFERENCE_TARGETS
                    else "ok"
                ),
                observed_target_count=observed_total,
                retained_target_count=int(retained_total),
            )
    except Exception as error:
        prior = connection.execute(
            "SELECT * FROM session_reference_scans WHERE session_id = ?", (session_id,)
        ).fetchone()
        _record_scan(
            connection,
            session_id=session_id,
            source_fingerprint=fingerprint,
            status="error",
            observed_target_count=(
                int(prior["observed_target_count"]) if prior else 0
            ),
            retained_target_count=(
                int(prior["retained_target_count"]) if prior else 0
            ),
            error_code="reference-finalization-error",
            error_message=str(error),
        )
        raise SessionReferenceError(str(error)) from error
    return int(retained_total)


def clear_session_reference_source(
    connection: sqlite3.Connection, *, session_id: int, source_path: str
) -> None:
    connection.execute(
        """
        DELETE FROM session_reference_evidence
        WHERE session_id = ? AND source_path = ?
        """,
        (session_id, source_path),
    )
    connection.execute(
        "DELETE FROM session_reference_scans WHERE session_id = ?", (session_id,)
    )


def mark_session_reference_error(
    connection: sqlite3.Connection,
    *,
    session_id: int,
    error_message: str,
) -> None:
    prior = connection.execute(
        "SELECT * FROM session_reference_scans WHERE session_id = ?", (session_id,)
    ).fetchone()
    _record_scan(
        connection,
        session_id=session_id,
        source_fingerprint=_recorded_source_set_fingerprint(connection, session_id),
        status="error",
        observed_target_count=(
            int(prior["observed_target_count"]) if prior else 0
        ),
        retained_target_count=(
            int(prior["retained_target_count"]) if prior else 0
        ),
        error_code="reference-source-error",
        error_message=error_message,
    )


def _location_count(rows: Iterable[sqlite3.Row]) -> int:
    locations = set()
    for row in rows:
        if row["evidence_kind"] == "resource_read" and row["tool_call_id"]:
            locations.add("call:" + row["tool_call_id"])
        elif row["source_event_id"]:
            locations.add("event:" + row["source_event_id"])
        else:
            locations.add("line:{}:{}".format(row["source_path"], row["source_line"]))
    return len(locations)


def session_reference_projection(
    connection: sqlite3.Connection, session_id: int
) -> dict:
    scan = connection.execute(
        "SELECT * FROM session_reference_scans WHERE session_id = ?", (session_id,)
    ).fetchone()
    rows = connection.execute(
        """
        SELECT session_reference_evidence.*,
               context_documents.context_root_id,
               external_resources.resource_type
        FROM session_reference_evidence
        LEFT JOIN context_documents
          ON context_documents.id = session_reference_evidence.context_document_id
        LEFT JOIN external_resources
          ON external_resources.id = session_reference_evidence.external_resource_id
        WHERE session_reference_evidence.session_id = ?
        ORDER BY session_reference_evidence.target_key,
                 session_reference_evidence.source_line,
                 session_reference_evidence.evidence_ordinal
        """,
        (session_id,),
    ).fetchall()
    grouped = {}
    for row in rows:
        grouped.setdefault(row["target_key"], []).append(row)

    items = []
    for target_rows in grouped.values():
        target_rows = sorted(
            target_rows,
            key=lambda row: (
                _evidence_rank(row["evidence_kind"], row["read_outcome"]),
                row["source_path"],
                row["source_line"],
                row["evidence_ordinal"],
            ),
        )
        strongest = target_rows[0]
        successful = [
            row
            for row in target_rows
            if row["evidence_kind"] == "resource_read"
            and row["read_outcome"] == "success"
        ]
        failed = [
            row
            for row in target_rows
            if row["evidence_kind"] == "resource_read"
            and row["read_outcome"] == "failure"
        ]
        evidence = []
        if successful:
            evidence.append(
                {"kind": "resource_read", "outcome": "success", "count": _location_count(successful)}
            )
        elif failed:
            evidence.append(
                {"kind": "resource_read", "outcome": "failure", "count": _location_count(failed)}
            )
        for kind in ("tool_result", "user_mention", "assistant_mention"):
            matching = [row for row in target_rows if row["evidence_kind"] == kind]
            if matching:
                evidence.append(
                    {"kind": kind, "outcome": None, "count": _location_count(matching)}
                )
        if strongest["target_kind"] == "context_document":
            destination = (
                "/documents/{}".format(strongest["context_document_id"])
                if strongest["context_root_id"] is not None
                else None
            )
        elif strongest["target_kind"] == "atlassian_item":
            destination = "/atlassian/items/{}".format(
                strongest["external_resource_id"]
            )
        else:
            destination = strongest["normalized_url"]
        items.append(
            {
                "target_key": strongest["target_key"],
                "target_kind": strongest["target_kind"],
                "context_document_id": strongest["context_document_id"],
                "external_resource_id": strongest["external_resource_id"],
                "identity": strongest["observed_identity"],
                "destination": destination,
                "evidence": evidence,
                "rank": _evidence_rank(
                    evidence[0]["kind"], evidence[0]["outcome"]
                ) if evidence else 5,
                "_sort_key": (
                    strongest["source_path"],
                    strongest["source_line"],
                    strongest["evidence_ordinal"],
                    strongest["target_key"],
                ),
            }
        )
    items.sort(key=lambda item: (item["rank"], item["_sort_key"]))
    for item in items:
        item.pop("_sort_key")
    return {
        "state": scan["status"] if scan else "ok",
        "observed_total": int(scan["observed_target_count"]) if scan else len(items),
        "retained_total": len(items),
        "partial": bool(scan and scan["status"] == "partial"),
        "stale": bool(scan and scan["status"] == "error"),
        "items": items,
    }
