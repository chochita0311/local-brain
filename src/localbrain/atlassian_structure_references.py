import hashlib
import json
import sqlite3
import unicodedata
from typing import Iterable, Mapping, Optional

from .atlassian_evidence import normalize_atlassian_structural_scope
from .atlassian_locators import AtlassianLocatorResult
from .ingest.common import EVIDENCE_EXTRACTOR_VERSION, REFERENCE_EXTRACTOR_VERSION
from .workstreams import utc_now


REFERENCE_AUTHORITY_COPY = (
    "Session/Local Context에서 URL 구조만 확인했습니다. "
    "Jira 링크/Wiki 문서·등록된 Project/Space·원격 조회 결과가 아닙니다."
)
REFERENCE_FAMILY_LABELS = {
    "jira_project": "Jira Project 참조",
    "jira_board": "Jira 보드 참조",
    "jira_filter": "Jira 필터 참조",
    "jira_dashboard": "Jira 대시보드 참조",
    "jira_service_portal": "Jira 서비스 포털 참조",
    "jira_service_project": "Jira 서비스 Project 참조",
    "confluence_space": "Wiki Space 참조",
}
MAX_REFERENCE_EVIDENCE_PREVIEW = 5
REFERENCE_PREVIEW_FIELDS = (
    "id",
    "site_id",
    "service",
    "reference_kind",
    "reference_identity",
    "normalized_domain",
    "entity_kind",
    "entity_id",
    "stable_key",
    "family_label",
    "display_title",
    "canonical_url",
    "canonical_safe_locator",
    "alias_total",
    "evidence_total",
    "lifecycle",
    "availability",
    "provenance",
    "container_kind",
    "container_label",
    "container_service",
    "container_cue",
    "container_structural_scope",
)


class StructureReferenceIdentityCollision(RuntimeError):
    pass


def structure_reference_family_label(reference_kind: str) -> str:
    try:
        return REFERENCE_FAMILY_LABELS[reference_kind]
    except KeyError as exc:
        raise ValueError("Unsupported Atlassian structure reference kind") from exc


def _reference_row(
    connection: sqlite3.Connection, reference_id: int
) -> Optional[sqlite3.Row]:
    return connection.execute(
        """
        SELECT atlassian_structure_references.*,
               atlassian_sites.normalized_domain,
               atlassian_sites.display_name AS site_name,
               (
                   SELECT safe_locator_url
                   FROM atlassian_structure_reference_urls
                   WHERE reference_id = atlassian_structure_references.id
                     AND url_role = 'canonical'
                   ORDER BY id
                   LIMIT 1
               ) AS canonical_url
        FROM atlassian_structure_references
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_structure_references.site_id
        WHERE atlassian_structure_references.id = ?
        """,
        (reference_id,),
    ).fetchone()


def ensure_structure_reference(
    connection: sqlite3.Connection,
    *,
    site_id: int,
    locator: AtlassianLocatorResult,
    observed_at: Optional[str] = None,
) -> dict:
    if (
        locator.kind != "structure"
        or locator.service is None
        or locator.reference_kind is None
        or locator.reference_identity is None
        or locator.safe_locator_url is None
        or locator.normalized_domain is None
    ):
        raise ValueError("A complete structure locator is required")
    site = connection.execute(
        "SELECT normalized_domain FROM atlassian_sites WHERE id = ?",
        (site_id,),
    ).fetchone()
    if site is None or site["normalized_domain"] != locator.normalized_domain:
        raise ValueError("Structure locator Site does not match its domain")

    reference = connection.execute(
        """
        SELECT id
        FROM atlassian_structure_references
        WHERE site_id = ? AND service = ? AND reference_kind = ?
          AND reference_identity = ?
        """,
        (
            site_id,
            locator.service,
            locator.reference_kind,
            locator.reference_identity,
        ),
    ).fetchone()
    now = observed_at or utc_now()
    created_reference = reference is None
    if reference is None:
        reference_id = int(
            connection.execute(
                """
                INSERT INTO atlassian_structure_references(
                    site_id, service, reference_kind, reference_identity,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    site_id,
                    locator.service,
                    locator.reference_kind,
                    locator.reference_identity,
                    now,
                    now,
                ),
            ).lastrowid
        )
    else:
        reference_id = int(reference["id"])

    url = connection.execute(
        """
        SELECT id, reference_id, url_role
        FROM atlassian_structure_reference_urls
        WHERE site_id = ? AND safe_locator_url = ?
        """,
        (site_id, locator.safe_locator_url),
    ).fetchone()
    if url is not None and int(url["reference_id"]) != reference_id:
        raise StructureReferenceIdentityCollision(
            "Safe locator belongs to a different structure reference"
        )

    created_url = url is None
    if url is None:
        has_canonical = connection.execute(
            """
            SELECT 1 FROM atlassian_structure_reference_urls
            WHERE reference_id = ? AND url_role = 'canonical'
            """,
            (reference_id,),
        ).fetchone()
        url_role = "alias" if has_canonical else "canonical"
        url_id = int(
            connection.execute(
                """
                INSERT INTO atlassian_structure_reference_urls(
                    reference_id, site_id, url_role, safe_locator_url,
                    first_observed_at, last_observed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    reference_id,
                    site_id,
                    url_role,
                    locator.safe_locator_url,
                    now,
                    now,
                ),
            ).lastrowid
        )
        if not created_reference:
            touch_structure_reference(connection, reference_id, changed_at=now)
    else:
        url_id = int(url["id"])
        url_role = str(url["url_role"])

    return {
        "reference_id": reference_id,
        "url_id": url_id,
        "url_role": url_role,
        "created_reference": created_reference,
        "created_url": created_url,
    }


def touch_structure_reference_url(
    connection: sqlite3.Connection,
    *,
    reference_id: int,
    safe_locator_url: str,
    observed_at: Optional[str] = None,
) -> None:
    now = observed_at or utc_now()
    connection.execute(
        """
        UPDATE atlassian_structure_reference_urls
        SET last_observed_at = ?
        WHERE reference_id = ? AND safe_locator_url = ?
          AND last_observed_at != ?
        """,
        (now, reference_id, safe_locator_url, now),
    )


def touch_structure_reference(
    connection: sqlite3.Connection,
    reference_id: int,
    *,
    changed_at: Optional[str] = None,
) -> None:
    now = changed_at or utc_now()
    connection.execute(
        """
        UPDATE atlassian_structure_references
        SET updated_at = ?
        WHERE id = ? AND updated_at != ?
        """,
        (now, reference_id, now),
    )


def structure_reference_evidence_key(
    *,
    reference_id: int,
    session_id: Optional[int],
    source_path: Optional[str],
    source_event_id: Optional[str],
    document_id: Optional[int],
    source_channel: str,
    source_line: int,
    url_ordinal: int,
    safe_locator_url: str,
    container_hint: Optional[str],
    extractor_version: str = EVIDENCE_EXTRACTOR_VERSION,
) -> str:
    payload = [
        "atlassian-structure-reference-evidence",
        reference_id,
        "session" if session_id is not None else "document",
        session_id,
        source_path,
        source_event_id,
        document_id,
        source_channel,
        source_line,
        url_ordinal,
        safe_locator_url,
        container_hint,
        extractor_version,
    ]
    encoded = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def insert_or_reuse_structure_reference_evidence(
    connection: sqlite3.Connection,
    *,
    reference_id: int,
    safe_locator_url: str,
    container_hint: Optional[str],
    source_line: int,
    url_ordinal: int,
    source_channel: str,
    session_id: Optional[int] = None,
    source_path: Optional[str] = None,
    source_event_id: Optional[str] = None,
    document_id: Optional[int] = None,
    observed_at: Optional[str] = None,
    refresh_existing: bool = False,
) -> dict:
    evidence_key = structure_reference_evidence_key(
        reference_id=reference_id,
        session_id=session_id,
        source_path=source_path,
        source_event_id=source_event_id,
        document_id=document_id,
        source_channel=source_channel,
        source_line=source_line,
        url_ordinal=url_ordinal,
        safe_locator_url=safe_locator_url,
        container_hint=container_hint,
    )
    existing = connection.execute(
        """
        SELECT id FROM atlassian_structure_reference_evidence
        WHERE evidence_key = ?
        """,
        (evidence_key,),
    ).fetchone()
    now = utc_now()
    if existing is not None:
        if refresh_existing:
            connection.execute(
                """
                UPDATE atlassian_structure_reference_evidence
                SET observed_at = ?, extractor_version = ?,
                    last_observed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    observed_at,
                    EVIDENCE_EXTRACTOR_VERSION,
                    now,
                    now,
                    int(existing["id"]),
                ),
            )
            touch_structure_reference_url(
                connection,
                reference_id=reference_id,
                safe_locator_url=safe_locator_url,
                observed_at=now,
            )
            touch_structure_reference(connection, reference_id, changed_at=now)
        return {"evidence_key": evidence_key, "created": False}

    connection.execute(
        """
        INSERT INTO atlassian_structure_reference_evidence(
            reference_id, session_id, source_path, document_id,
            source_channel, source_event_id, source_line, url_ordinal,
            safe_locator_url, container_hint, observed_at,
            extractor_version, evidence_key, first_observed_at,
            last_observed_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            reference_id,
            session_id,
            source_path,
            document_id,
            source_channel,
            source_event_id,
            source_line,
            url_ordinal,
            safe_locator_url,
            container_hint,
            observed_at,
            EVIDENCE_EXTRACTOR_VERSION,
            evidence_key,
            now,
            now,
            now,
        ),
    )
    touch_structure_reference_url(
        connection,
        reference_id=reference_id,
        safe_locator_url=safe_locator_url,
        observed_at=now,
    )
    touch_structure_reference(connection, reference_id, changed_at=now)
    return {"evidence_key": evidence_key, "created": True}


def remove_obsolete_document_structure_evidence(
    connection: sqlite3.Connection,
    *,
    document_id: int,
    retained_keys: Iterable[str],
) -> dict:
    retained = tuple(sorted(set(retained_keys)))
    if retained:
        placeholders = ",".join("?" for _ in retained)
        predicate = "document_id = ? AND evidence_key NOT IN ({})".format(
            placeholders
        )
        values = (document_id,) + retained
    else:
        predicate = "document_id = ?"
        values = (document_id,)
    rows = connection.execute(
        """
        SELECT evidence_key, reference_id
        FROM atlassian_structure_reference_evidence
        WHERE {}
        ORDER BY id
        """.format(predicate),
        values,
    ).fetchall()
    if rows:
        connection.execute(
            "DELETE FROM atlassian_structure_reference_evidence WHERE "
            + predicate,
            values,
        )
        now = utc_now()
        for reference_id in sorted({int(row["reference_id"]) for row in rows}):
            touch_structure_reference(
                connection, reference_id, changed_at=now
            )
    return {
        "evidence_keys": {str(row["evidence_key"]) for row in rows},
        "reference_ids": {int(row["reference_id"]) for row in rows},
    }


def _available_evidence_map(
    connection: sqlite3.Connection,
    reference_id: Optional[int] = None,
) -> dict[int, int]:
    rows = connection.execute(
        """
        SELECT evidence.id, evidence.reference_id
        FROM atlassian_structure_reference_evidence AS evidence
        JOIN sessions ON sessions.id = evidence.session_id
        JOIN session_reference_scans
          ON session_reference_scans.session_id = sessions.id
        WHERE evidence.session_id IS NOT NULL
          AND sessions.session_class = 'work'
          AND sessions.session_role = 'primary'
          AND sessions.index_policy = 'full'
          AND session_reference_scans.extractor_version = ?
          AND session_reference_scans.status IN ('ok', 'partial')
          AND (? IS NULL OR evidence.reference_id = ?)
          AND EXISTS (
              SELECT 1
              FROM session_reference_evidence AS projected
              WHERE projected.session_id = evidence.session_id
                AND projected.source_path = evidence.source_path
                AND projected.source_event_id = evidence.source_event_id
                AND projected.source_line = evidence.source_line
                AND projected.evidence_ordinal = evidence.url_ordinal
                AND projected.target_kind = 'url'
                AND projected.normalized_url = evidence.safe_locator_url
                AND projected.extractor_version = ?
                AND (
                    (
                        evidence.source_channel = 'approved_tool_result'
                        AND projected.evidence_kind = 'tool_result'
                    )
                    OR (
                        evidence.source_channel = 'visible_text'
                        AND projected.evidence_kind IN (
                            'user_mention', 'assistant_mention'
                        )
                    )
                )
          )
        UNION
        SELECT evidence.id, evidence.reference_id
        FROM atlassian_structure_reference_evidence AS evidence
        JOIN context_documents
          ON context_documents.id = evidence.document_id
        JOIN context_roots
          ON context_roots.id = context_documents.context_root_id
        WHERE evidence.document_id IS NOT NULL
          AND context_roots.enabled = 1
          AND context_roots.readable = 1
          AND context_roots.status = 'ready'
          AND (? IS NULL OR evidence.reference_id = ?)
        """,
        (
            REFERENCE_EXTRACTOR_VERSION,
            reference_id,
            reference_id,
            REFERENCE_EXTRACTOR_VERSION,
            reference_id,
            reference_id,
        ),
    ).fetchall()
    return {
        int(row["id"]): int(row["reference_id"])
        for row in rows
    }


def _available_reference_ids(connection: sqlite3.Connection) -> set[int]:
    return set(_available_evidence_map(connection).values())


def _container_projection(service: str, hint: Optional[str]) -> dict:
    if hint is not None:
        scope = normalize_atlassian_structural_scope(
            "url:{}:{}".format(service, hint)
        )
        if scope is not None:
            return {
                "container_kind": "url",
                "container_label": hint,
                "container_service": service,
                "container_cue": "{} · URL 기준".format(
                    "Jira" if service == "jira" else "Wiki"
                ),
                "container_structural_scope": scope,
            }
    return {
        "container_kind": "unclassified",
        "container_label": "소속 미확인",
        "container_service": None,
        "container_cue": None,
        "container_structural_scope": "unclassified",
    }


def structure_reference_rows(
    connection: sqlite3.Connection,
    *,
    include_archived: bool = True,
    reference_id: Optional[int] = None,
) -> list[dict]:
    available_ids = (
        set(_available_evidence_map(connection, reference_id).values())
        if reference_id is not None
        else _available_reference_ids(connection)
    )
    rows = connection.execute(
        """
        SELECT structure_refs.id, structure_refs.site_id, structure_refs.service,
               structure_refs.reference_kind, structure_refs.reference_identity,
               structure_refs.created_at, structure_refs.updated_at,
               sites.normalized_domain, sites.display_name AS site_name,
               (
                   SELECT safe_locator_url
                   FROM atlassian_structure_reference_urls
                   WHERE reference_id = structure_refs.id
                     AND url_role = 'canonical'
                   ORDER BY id
                   LIMIT 1
               ) AS canonical_url,
               (
                   SELECT COUNT(*)
                   FROM atlassian_structure_reference_evidence
                   WHERE reference_id = structure_refs.id
               ) AS evidence_total,
               (
                   SELECT COUNT(DISTINCT container_hint)
                   FROM atlassian_structure_reference_evidence
                   WHERE reference_id = structure_refs.id
               ) AS hint_count,
               (
                   SELECT MIN(container_hint)
                   FROM atlassian_structure_reference_evidence
                   WHERE reference_id = structure_refs.id
               ) AS consensus_hint,
               (
                   SELECT COUNT(*)
                   FROM atlassian_structure_reference_urls
                   WHERE reference_id = structure_refs.id
               ) AS url_total
        FROM atlassian_structure_references AS structure_refs
        JOIN atlassian_sites AS sites ON sites.id = structure_refs.site_id
        WHERE (? IS NULL OR structure_refs.id = ?)
        ORDER BY structure_refs.id
        """,
        (reference_id, reference_id),
    ).fetchall()
    values = []
    for source in rows:
        row = dict(source)
        evidence_total = int(row["evidence_total"])
        lifecycle = "archived" if evidence_total == 0 else "active"
        if lifecycle == "archived" and not include_archived:
            continue
        availability = (
            "archived"
            if lifecycle == "archived"
            else (
                "available"
                if int(row["id"]) in available_ids
                else "unavailable"
            )
        )
        consensus_hint = (
            row["consensus_hint"] if int(row["hint_count"]) == 1 else None
        )
        row.update(
            {
                "entity_kind": "reference",
                "entity_id": int(row["id"]),
                "stable_key": "reference:{}".format(row["id"]),
                "family_label": structure_reference_family_label(
                    str(row["reference_kind"])
                ),
                "display_title": row["reference_identity"],
                "canonical_safe_locator": row["canonical_url"],
                "alias_total": max(0, int(row["url_total"]) - 1),
                "evidence_total": evidence_total,
                "lifecycle": lifecycle,
                "availability": availability,
                "provenance": "URL 기준 · Local evidence",
                **_container_projection(str(row["service"]), consensus_hint),
            }
        )
        values.append(row)
    return values


def _evidence_rows(
    connection: sqlite3.Connection, reference_id: int
) -> tuple[list[dict], int]:
    total = int(
        connection.execute(
            """
            SELECT COUNT(*)
            FROM atlassian_structure_reference_evidence
            WHERE reference_id = ?
            """,
            (reference_id,),
        ).fetchone()[0]
    )
    available_evidence_ids = set(
        _available_evidence_map(connection, reference_id)
    )
    rows = connection.execute(
        """
        SELECT id,
               CASE WHEN session_id IS NOT NULL THEN 'session'
                    ELSE 'document' END AS source_kind,
               COALESCE(session_id, document_id) AS local_id,
               source_channel, source_line, url_ordinal,
               safe_locator_url, container_hint,
               substr(observed_at, 1, 80) AS observed_at,
               substr(last_observed_at, 1, 80) AS last_observed_at
        FROM atlassian_structure_reference_evidence
        WHERE reference_id = ?
        ORDER BY COALESCE(observed_at, last_observed_at) DESC, id DESC
        LIMIT ?
        """,
        (reference_id, MAX_REFERENCE_EVIDENCE_PREVIEW),
    ).fetchall()
    return (
        [
            {
                "source_kind": row["source_kind"],
                "local_id": int(row["local_id"]),
                "source_channel": row["source_channel"],
                "source_line": int(row["source_line"]),
                "url_ordinal": int(row["url_ordinal"]),
                "safe_locator_url": row["safe_locator_url"],
                "container_hint": row["container_hint"],
                "observed_at": row["observed_at"],
                "last_observed_at": row["last_observed_at"],
                "source_available": int(row["id"]) in available_evidence_ids,
            }
            for row in rows
        ],
        total,
    )


def structure_reference_preview(
    connection: sqlite3.Connection, reference_id: int
) -> Optional[dict]:
    values = structure_reference_rows(
        connection, include_archived=True, reference_id=reference_id
    )
    reference = next(
        (row for row in values if int(row["id"]) == reference_id), None
    )
    if reference is None:
        return None
    evidence_items, evidence_total = _evidence_rows(connection, reference_id)
    return {
        **{
            field: reference[field]
            for field in REFERENCE_PREVIEW_FIELDS
        },
        "authority_copy": REFERENCE_AUTHORITY_COPY,
        "evidence": {
            "items": evidence_items,
            "total": evidence_total,
            "truncated": evidence_total > len(evidence_items),
        },
    }


def structure_reference_detail(
    connection: sqlite3.Connection, reference_id: int
) -> Optional[dict]:
    return structure_reference_preview(connection, reference_id)


def project_structure_reference_search(
    connection: sqlite3.Connection, reference_id: int
) -> bool:
    reference = structure_reference_preview(connection, reference_id)
    current = [
        dict(row)
        for row in connection.execute(
            """
            SELECT entity_type, entity_id, source_kind, title, body, path
            FROM search_index
            WHERE entity_type = 'atlassian_structure_reference'
              AND entity_id = ?
            ORDER BY source_kind, title, body, path
            """,
            (str(reference_id),),
        ).fetchall()
    ]
    desired = []
    if reference is not None and reference["lifecycle"] != "archived":
        urls = [
            str(row["safe_locator_url"])
            for row in connection.execute(
                """
                SELECT safe_locator_url
                FROM atlassian_structure_reference_urls
                WHERE reference_id = ?
                ORDER BY CASE url_role WHEN 'canonical' THEN 0 ELSE 1 END, id
                """,
                (reference_id,),
            ).fetchall()
        ]
        desired = [
            {
                "entity_type": "atlassian_structure_reference",
                "entity_id": str(reference_id),
                "source_kind": "atlassian:{}".format(reference["service"]),
                "title": reference["family_label"],
                "body": "\n".join(
                    [str(reference["reference_identity"]), *urls]
                ),
                "path": str(reference["canonical_url"]),
            }
        ]
    if current == desired:
        return False
    connection.execute(
        """
        DELETE FROM search_index
        WHERE entity_type = 'atlassian_structure_reference' AND entity_id = ?
        """,
        (str(reference_id),),
    )
    if desired:
        connection.executemany(
            """
            INSERT INTO search_index(
                entity_type, entity_id, source_kind, title, body, path
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    value["entity_type"],
                    value["entity_id"],
                    value["source_kind"],
                    value["title"],
                    value["body"],
                    value["path"],
                )
                for value in desired
            ],
        )
    return True


def rebuild_structure_reference_search_index(
    connection: sqlite3.Connection,
) -> int:
    reference_ids = [
        int(row["id"])
        for row in connection.execute(
            "SELECT id FROM atlassian_structure_references ORDER BY id"
        ).fetchall()
    ]
    connection.execute(
        "DELETE FROM search_index WHERE entity_type = 'atlassian_structure_reference'"
    )
    return sum(
        bool(project_structure_reference_search(connection, reference_id))
        for reference_id in reference_ids
    )


def normalized_reference_search_value(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).casefold()
