import codecs
import re
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator, Optional

from .atlassian import (
    NormalizedAtlassianUrl,
    create_or_reuse_atlassian_stub,
    register_atlassian_site,
)
from .atlassian_evidence import (
    MAX_SOURCE_EVIDENCE,
    RecognizedAtlassianItemUrl,
    StrictAtlassianItemUrl,
    atlassian_evidence_key,
    configured_atlassian_sync_scope_snapshot,
    document_evidence_source_fingerprint,
    record_document_evidence_scan,
)
from .atlassian_locators import AtlassianLocatorResult, describe_atlassian_url
from .atlassian_structure_references import (
    StructureReferenceIdentityCollision,
    ensure_structure_reference,
    insert_or_reuse_structure_reference_evidence,
    project_structure_reference_search,
    remove_obsolete_document_structure_evidence,
)
from .ingest.common import (
    EVIDENCE_EXTRACTOR_VERSION,
    REFERENCE_EXTRACTOR_VERSION,
    ParsedUrlEvidence,
    trim_url_token,
)
from .workstreams import utc_now


SOURCE_BATCH_SIZE = 100
DOCUMENT_CHUNK_BYTES = 64 * 1024
MAX_URL_CODE_POINTS = 8_000
_SYNC_LOCK = threading.Lock()
_JIRA_KEY = re.compile(r"[A-Z][A-Z0-9_]*-\d+", re.IGNORECASE)
_KEY_CHARACTER = re.compile(r"[A-Z0-9_-]", re.IGNORECASE)
_CANDIDATE_SKIP_KEYS = (
    "key_only",
    "unsafe_url",
    "unsupported_locator",
    "unconfigured_domain",
    "ambiguous_site",
    "invalid_location",
)
_SKIP_REASON_CODES = {
    "unsafe_url": "unsafe-url",
    "unsupported_locator": "unsupported-locator",
    "unconfigured_domain": "unconfigured-domain",
    "ambiguous_site": "ambiguous-site",
    "invalid_location": "invalid-location",
}
SOURCE_REASON_CODES = frozenset(
    {
        "ineligible-session",
        "disabled-document",
        "session-projection-missing",
        "session-projection-stale",
        "session-projection-error",
        "session-projection-partial",
        "context-unavailable",
        "document-url-limit",
        "unsafe-url",
        "unsupported-locator",
        "unconfigured-domain",
        "ambiguous-site",
        "invalid-location",
        "reconciliation-error",
        "identity-collision",
    }
)


@dataclass(frozen=True)
class _DocumentUrl:
    observed_url: Optional[str]
    source_line: int
    url_ordinal: int


@dataclass(frozen=True)
class _DocumentScan:
    candidates: tuple[_DocumentUrl, ...]
    url_overflow: int
    key_only_count: int


@dataclass
class _SourceResult:
    kind: str
    local_id: int
    outcome: str
    reason_codes: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(
        default_factory=lambda: {
            "urls": 0,
            "new_items": 0,
            "reused_items": 0,
            "new_evidence": 0,
            "reused_evidence": 0,
            "removed_evidence": 0,
            "new_structure_references": 0,
            "reused_structure_references": 0,
            "new_structure_evidence": 0,
            "reused_structure_evidence": 0,
            "removed_structure_evidence": 0,
            "site_only": 0,
            "skipped": 0,
        }
    )
    candidate_skips: dict[str, int] = field(
        default_factory=lambda: {key: 0 for key in _CANDIDATE_SKIP_KEYS}
    )
    scope_limits: dict[str, int] = field(
        default_factory=lambda: {
            "session_projection_sources": 0,
            "session_reference_overflow": 0,
            "document_url_overflow": 0,
        }
    )
    admitted_urls: set[str] = field(default_factory=set)
    new_item_ids: set[int] = field(default_factory=set)
    reused_item_ids: set[int] = field(default_factory=set)
    new_structure_reference_ids: set[int] = field(default_factory=set)
    reused_structure_reference_ids: set[int] = field(default_factory=set)
    new_structure_evidence_keys: set[str] = field(default_factory=set)
    reused_structure_evidence_keys: set[str] = field(default_factory=set)
    removed_structure_evidence_keys: set[str] = field(default_factory=set)
    affected_structure_reference_ids: set[int] = field(default_factory=set)
    seen_evidence: set[str] = field(default_factory=set)
    seen_session_locations: set[tuple] = field(default_factory=set)
    site_scope_updates: dict[tuple[str, str], int] = field(
        default_factory=dict
    )
    domain_site_updates: dict[str, int] = field(default_factory=dict)

    def add_reason(self, code: str) -> None:
        if code not in SOURCE_REASON_CODES:
            raise ValueError("Unsupported Atlassian Sync reason code")
        if code not in self.reason_codes:
            self.reason_codes.append(code)

    def add_skip(self, bucket: str) -> None:
        self.candidate_skips[bucket] += 1
        if bucket != "key_only":
            self.add_reason(_SKIP_REASON_CODES[bucket])

    def finish_counts(self) -> None:
        self.counts["urls"] = len(self.admitted_urls)
        self.counts["new_items"] = len(self.new_item_ids)
        self.counts["reused_items"] = len(
            self.reused_item_ids - self.new_item_ids
        )
        self.counts["new_structure_references"] = len(
            self.new_structure_reference_ids
        )
        self.counts["reused_structure_references"] = len(
            self.reused_structure_reference_ids
            - self.new_structure_reference_ids
        )
        self.counts["new_structure_evidence"] = len(
            self.new_structure_evidence_keys
        )
        self.counts["reused_structure_evidence"] = len(
            self.reused_structure_evidence_keys
            - self.new_structure_evidence_keys
        )
        self.counts["removed_structure_evidence"] = len(
            self.removed_structure_evidence_keys
        )
        self.counts["skipped"] = sum(self.candidate_skips.values())

    def public(self) -> dict:
        self.finish_counts()
        return {
            "kind": self.kind,
            "local_id": self.local_id,
            "outcome": self.outcome,
            "counts": dict(self.counts),
            "reason_codes": list(self.reason_codes),
        }


@dataclass
class _ActionSiteRegistry:
    scope: dict[tuple[str, str], tuple[int, ...]]
    source_instances: dict[tuple[int, str], Optional[int]]
    domain_sites: dict[str, tuple[int, ...]]

    def publish(self, result: _SourceResult) -> None:
        for key, site_id in result.site_scope_updates.items():
            self.scope[key] = (site_id,)
        for domain, site_id in result.domain_site_updates.items():
            self.domain_sites[domain] = (site_id,)


class _DocumentUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class _ResolvedCandidate:
    kind: str
    locator: AtlassianLocatorResult
    item: Optional[RecognizedAtlassianItemUrl] = None
    site_id: Optional[int] = None


class _DocumentStreamScanner:
    def __init__(self) -> None:
        self.candidates: list[_DocumentUrl] = []
        self.url_count = 0
        self.key_only_count = 0
        self.line = 1
        self.line_url_ordinal = 0
        self.recent = ""
        self.key_chars: list[str] = []
        self.key_too_long = False
        self.in_url = False
        self.url_chars: list[str] = []
        self.url_too_long = False
        self.url_line = 1
        self.url_ordinal = 1
        self.after_carriage_return = False

    def feed(self, text: str) -> None:
        for character in text:
            if self.in_url:
                if character.isspace() or character in "<>'\"`":
                    self._finish_url()
                    self._feed_plain(character)
                else:
                    if len(self.url_chars) < MAX_URL_CODE_POINTS:
                        self.url_chars.append(character)
                    else:
                        self.url_too_long = True
                continue
            self._feed_plain(character)

    def finish(self) -> _DocumentScan:
        if self.in_url:
            self._finish_url()
        self._finish_key()
        return _DocumentScan(
            candidates=tuple(self.candidates),
            url_overflow=max(0, self.url_count - MAX_SOURCE_EVIDENCE),
            key_only_count=self.key_only_count,
        )

    def _feed_plain(self, character: str) -> None:
        if _KEY_CHARACTER.fullmatch(character):
            if len(self.key_chars) < MAX_URL_CODE_POINTS:
                self.key_chars.append(character)
            else:
                self.key_too_long = True
        else:
            self._finish_key()

        if character.isspace() or character in "<>'\"`":
            self.recent = ""
        else:
            self.recent = (self.recent + character)[-8:]

        lowered = self.recent.lower()
        prefix = None
        if lowered.endswith("https://"):
            prefix = self.recent[-8:]
        elif lowered.endswith("http://"):
            prefix = self.recent[-7:]
        if prefix is not None:
            self.in_url = True
            self.url_chars = list(prefix)
            self.url_too_long = False
            self.url_line = self.line
            self.line_url_ordinal += 1
            self.url_ordinal = self.line_url_ordinal
            self.recent = ""

        if character == "\r":
            self.line += 1
            self.line_url_ordinal = 0
            self.recent = ""
            self.after_carriage_return = True
        elif character == "\n":
            if not self.after_carriage_return:
                self.line += 1
            self.line_url_ordinal = 0
            self.recent = ""
            self.after_carriage_return = False
        elif character in {"\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"}:
            self.line += 1
            self.line_url_ordinal = 0
            self.recent = ""
            self.after_carriage_return = False
        else:
            self.after_carriage_return = False

    def _finish_key(self) -> None:
        if self.key_chars and not self.key_too_long:
            value = "".join(self.key_chars)
            if _JIRA_KEY.fullmatch(value):
                self.key_only_count += 1
        self.key_chars = []
        self.key_too_long = False

    def _finish_url(self) -> None:
        self.url_count += 1
        if self.url_count <= MAX_SOURCE_EVIDENCE:
            observed_url = None
            if not self.url_too_long:
                observed_url = trim_url_token("".join(self.url_chars)) or None
            self.candidates.append(
                _DocumentUrl(
                    observed_url=observed_url,
                    source_line=self.url_line,
                    url_ordinal=self.url_ordinal,
                )
            )
        self.in_url = False
        self.url_chars = []
        self.url_too_long = False


@contextmanager
def _atomic_source(connection: sqlite3.Connection):
    connection.execute("SAVEPOINT atlassian_local_evidence_source")
    try:
        yield
    except Exception:
        connection.execute("ROLLBACK TO atlassian_local_evidence_source")
        connection.execute("RELEASE atlassian_local_evidence_source")
        raise
    else:
        connection.execute("RELEASE atlassian_local_evidence_source")


def _empty_report(status: str = "complete") -> dict:
    return {
        "status": status,
        "sources": {
            "considered": 0,
            "eligible": 0,
            "scanned": 0,
            "partial": 0,
            "unavailable": 0,
            "failed": 0,
            "excluded": 0,
        },
        "items": {"new": 0, "reused": 0},
        "evidence": {"new": 0, "reused": 0, "removed": 0},
        "structure_references": {"new": 0, "reused": 0},
        "structure_evidence": {"new": 0, "reused": 0, "removed": 0},
        "site_only": 0,
        "candidate_skips": {key: 0 for key in _CANDIDATE_SKIP_KEYS},
        "scope_limits": {
            "session_projection_sources": 0,
            "session_reference_overflow": 0,
            "document_url_overflow": 0,
        },
        "source_outcomes": [],
    }


def busy_atlassian_local_evidence_report() -> dict:
    return _empty_report("busy")


def _source_failure(
    kind: str, local_id: int, reason: str = "reconciliation-error"
) -> _SourceResult:
    result = _SourceResult(kind, local_id, "failed")
    result.add_reason(reason)
    return result


def _read_document_scan(
    connection: sqlite3.Connection, document_id: int
) -> _DocumentScan:
    decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
    scanner = _DocumentStreamScanner()
    offset = 1
    while True:
        row = connection.execute(
            """
            SELECT substr(CAST(body AS BLOB), ?, ?) AS body_chunk
            FROM context_documents
            WHERE id = ?
            """,
            (offset, DOCUMENT_CHUNK_BYTES, document_id),
        ).fetchone()
        if row is None:
            raise _DocumentUnavailable("Document disappeared during Sync")
        chunk = row["body_chunk"]
        if chunk is None:
            chunk = b""
        if not isinstance(chunk, bytes):
            chunk = bytes(chunk)
        if chunk:
            scanner.feed(decoder.decode(chunk, final=False))
            offset += len(chunk)
        if len(chunk) < DOCUMENT_CHUNK_BYTES:
            break
    scanner.feed(decoder.decode(b"", final=True))
    return scanner.finish()


def _current_document(connection: sqlite3.Connection, document_id: int):
    return connection.execute(
        """
        SELECT context_documents.id, context_documents.content_hash,
               context_documents.context_root_id,
               context_roots.enabled, context_roots.readable,
               context_roots.status
        FROM context_documents
        LEFT JOIN context_roots
          ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.id = ?
        """,
        (document_id,),
    ).fetchone()


def _document_scan_is_current(
    connection: sqlite3.Connection,
    *,
    document_id: int,
    source_fingerprint: str,
    site_fingerprint: str,
) -> bool:
    row = connection.execute(
        """
        SELECT source_fingerprint, site_fingerprint, extractor_version, status
        FROM atlassian_evidence_scans
        WHERE document_id = ?
        """,
        (document_id,),
    ).fetchone()
    return bool(
        row is not None
        and row["status"] == "ok"
        and row["source_fingerprint"] == source_fingerprint
        and row["extractor_version"] == EVIDENCE_EXTRACTOR_VERSION
    )


def _valid_session_location(row: sqlite3.Row) -> bool:
    return bool(
        row["source_path"]
        and len(str(row["source_path"])) <= 8_000
        and row["source_event_id"]
        and len(str(row["source_event_id"])) <= 1_000
        and isinstance(row["source_line"], int)
        and int(row["source_line"]) > 0
        and isinstance(row["evidence_ordinal"], int)
        and int(row["evidence_ordinal"]) > 0
    )


def _recognized_for_site(
    locator: StrictAtlassianItemUrl, site_id: int
) -> RecognizedAtlassianItemUrl:
    return RecognizedAtlassianItemUrl(
        source_instance_id=None,
        site_id=site_id,
        service=locator.service,
        normalized=locator.normalized,
        observed_remote_id=locator.observed_remote_id,
        observed_remote_key=locator.observed_remote_key,
        container_structural_scope=locator.container_structural_scope,
        container_label=locator.container_label,
    )


def _resolve_site_id(
    connection: sqlite3.Connection,
    *,
    normalized_domain: str,
    service: str,
    canonical_base_url: str,
    registry: _ActionSiteRegistry,
    result: _SourceResult,
) -> Optional[int]:
    domain = normalized_domain
    key = (domain, service)
    if domain in result.domain_site_updates:
        site_id = result.domain_site_updates[domain]
    else:
        domain_sites = tuple(
            dict.fromkeys(registry.domain_sites.get(domain, ()))
        )
        service_sites = tuple(dict.fromkeys(registry.scope.get(key, ())))
        if key in result.site_scope_updates:
            service_sites = (result.site_scope_updates[key],)
        if len(service_sites) > 1:
            result.add_skip("ambiguous_site")
            return None
        if service_sites:
            site_id = int(service_sites[0])
        elif len(domain_sites) == 1:
            site_id = int(domain_sites[0])
        elif len(domain_sites) > 1:
            result.add_skip("ambiguous_site")
            return None
        else:
            site = register_atlassian_site(
                connection,
                base_url=canonical_base_url,
            )
            site_id = int(site["id"])
            result.domain_site_updates[domain] = site_id
    result.site_scope_updates[key] = site_id
    return site_id


def _resolve_local_site(
    connection: sqlite3.Connection,
    locator: StrictAtlassianItemUrl,
    registry: _ActionSiteRegistry,
    result: _SourceResult,
) -> Optional[RecognizedAtlassianItemUrl]:
    site_id = _resolve_site_id(
        connection,
        normalized_domain=locator.normalized.normalized_domain,
        service=locator.service,
        canonical_base_url=locator.normalized.canonical_base_url,
        registry=registry,
        result=result,
    )
    if site_id is None:
        return None
    return _recognized_for_site(locator, site_id)


def _item_for_target(
    connection: sqlite3.Connection,
    recognized: RecognizedAtlassianItemUrl,
    observed_url: str,
    observed_at: Optional[str],
    source_instances,
    *,
    refresh_existing_url_observation: bool = False,
) -> tuple[int, bool]:
    existing = connection.execute(
        """
        SELECT id, external_resource_id
        FROM atlassian_item_urls
        WHERE site_id = ? AND normalized_url = ?
        """,
        (recognized.site_id, recognized.normalized.normalized_url),
    ).fetchone()
    if existing is not None:
        if refresh_existing_url_observation:
            connection.execute(
                """
                UPDATE atlassian_item_urls
                SET observed_url = ?, last_observed_at = ?
                WHERE id = ?
                """,
                (
                    observed_url,
                    observed_at or utc_now(),
                    int(existing["id"]),
                ),
            )
        return int(existing["external_resource_id"]), False
    observation_time = observed_at or utc_now()
    item = create_or_reuse_atlassian_stub(
        connection,
        source_instance_id=None,
        service=recognized.service,
        site_id=recognized.site_id,
        url=recognized.normalized.normalized_url,
        observed_at=observation_time,
    )
    external_resource_id = int(item["external_resource_id"])
    if observed_url != recognized.normalized.normalized_url:
        connection.execute(
            """
            UPDATE atlassian_item_urls
            SET observed_url = ?, last_observed_at = ?
            WHERE external_resource_id = ? AND site_id = ?
              AND normalized_url = ?
            """,
            (
                observed_url,
                observation_time,
                external_resource_id,
                recognized.site_id,
                recognized.normalized.normalized_url,
            ),
        )
    frozen_source_instance_id = source_instances.get(
        (recognized.site_id, recognized.service)
    )
    if frozen_source_instance_id is not None:
        connection.execute(
            """
            UPDATE atlassian_items
            SET source_instance_id = ?
            WHERE external_resource_id = ?
              AND source_instance_id IS NULL
            """,
            (frozen_source_instance_id, external_resource_id),
        )
    return external_resource_id, True


def _insert_or_reuse_evidence(
    connection: sqlite3.Connection,
    *,
    result: _SourceResult,
    external_resource_id: int,
    recognized: RecognizedAtlassianItemUrl,
    observed_url: str,
    source_line: int,
    url_ordinal: int,
    source_channel: str,
    session_id: Optional[int] = None,
    source_path: Optional[str] = None,
    source_event_id: Optional[str] = None,
    document_id: Optional[int] = None,
    observed_at: Optional[str] = None,
    refresh_existing: bool = False,
) -> str:
    candidate = ParsedUrlEvidence(
        observed_url=observed_url,
        source_line=source_line,
        url_ordinal=url_ordinal,
        source_channel=source_channel,
        source_event_id=source_event_id,
        observed_at=observed_at,
        observed_remote_id=recognized.observed_remote_id,
    )
    evidence_key = atlassian_evidence_key(
        external_resource_id=external_resource_id,
        session_id=session_id,
        source_path=source_path,
        document_id=document_id,
        candidate=candidate,
        normalized_url=recognized.normalized.normalized_url,
        extractor_version=EVIDENCE_EXTRACTOR_VERSION,
    )
    if session_id is not None:
        session_location = (
            external_resource_id,
            session_id,
            source_path,
            source_event_id,
            source_line,
            url_ordinal,
            recognized.normalized.normalized_url,
            source_channel,
        )
        if session_location in result.seen_session_locations:
            return evidence_key
        result.seen_session_locations.add(session_location)
    if evidence_key in result.seen_evidence:
        return evidence_key

    if session_id is not None:
        existing = connection.execute(
            """
            SELECT evidence_key
            FROM atlassian_item_evidence
            WHERE external_resource_id = ?
              AND session_id = ?
              AND source_path = ?
              AND source_event_id = ?
              AND source_line = ?
              AND url_ordinal = ?
              AND normalized_url = ?
              AND source_channel = ?
            ORDER BY id
            LIMIT 1
            """,
            (
                external_resource_id,
                session_id,
                source_path,
                source_event_id,
                source_line,
                url_ordinal,
                recognized.normalized.normalized_url,
                source_channel,
            ),
        ).fetchone()
    else:
        existing = connection.execute(
            """
            SELECT evidence_key
            FROM atlassian_item_evidence
            WHERE evidence_key = ?
            """,
            (evidence_key,),
        ).fetchone()
    if existing is not None:
        existing_key = str(existing["evidence_key"])
        if refresh_existing:
            now = utc_now()
            connection.execute(
                """
                UPDATE atlassian_item_evidence
                SET observed_url = ?, observed_remote_id = ?,
                    observed_at = ?, extractor_version = ?,
                    last_observed_at = ?, updated_at = ?
                WHERE evidence_key = ?
                """,
                (
                    observed_url,
                    recognized.observed_remote_id,
                    observed_at,
                    EVIDENCE_EXTRACTOR_VERSION,
                    now,
                    now,
                    existing_key,
                ),
            )
        result.seen_evidence.add(evidence_key)
        result.seen_evidence.add(existing_key)
        result.counts["reused_evidence"] += 1
        return existing_key

    now = utc_now()
    connection.execute(
        """
        INSERT INTO atlassian_item_evidence(
            external_resource_id, session_id, source_path, document_id,
            source_channel, source_event_id, source_line, url_ordinal,
            observed_url, normalized_url, observed_remote_id,
            observed_title, observed_at, extractor_version, evidence_key,
            first_observed_at, last_observed_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?)
        """,
        (
            external_resource_id,
            session_id,
            source_path,
            document_id,
            source_channel,
            source_event_id,
            source_line,
            url_ordinal,
            observed_url,
            recognized.normalized.normalized_url,
            recognized.observed_remote_id,
            observed_at,
            EVIDENCE_EXTRACTOR_VERSION,
            evidence_key,
            now,
            now,
            now,
        ),
    )
    result.seen_evidence.add(evidence_key)
    result.counts["new_evidence"] += 1
    return evidence_key


def _strict_item_from_locator(
    locator: AtlassianLocatorResult, observed_url: str
) -> StrictAtlassianItemUrl:
    assert locator.kind == "item"
    assert locator.service is not None
    assert locator.normalized_domain is not None
    assert locator.canonical_base_url is not None
    assert locator.safe_locator_url is not None
    assert locator.item_identity is not None
    return StrictAtlassianItemUrl(
        service=locator.service,
        normalized=NormalizedAtlassianUrl(
            observed_url=observed_url.strip(),
            normalized_url=locator.safe_locator_url,
            normalized_domain=locator.normalized_domain,
            canonical_base_url=locator.canonical_base_url,
        ),
        observed_remote_id=(
            locator.item_identity
            if locator.item_identity_kind == "confluence_page"
            else None
        ),
        observed_remote_key=(
            locator.item_identity
            if locator.item_identity_kind == "jira_issue"
            else None
        ),
        container_structural_scope=None,
        container_label=None,
    )


def _recognize_candidate(
    *,
    result: _SourceResult,
    observed_url: Optional[str],
    connection: sqlite3.Connection,
    registry: _ActionSiteRegistry,
) -> Optional[_ResolvedCandidate]:
    if observed_url is None:
        result.add_skip("unsafe_url")
        return None
    locator = describe_atlassian_url(observed_url)
    if locator.kind in {"unsafe", "unsupported"}:
        bucket = (
            "unsafe_url" if locator.kind == "unsafe" else "unsupported_locator"
        )
        result.add_skip(bucket)
        return None
    assert locator.safe_locator_url is not None
    result.admitted_urls.add(locator.safe_locator_url)
    if locator.kind == "site":
        result.counts["site_only"] += 1
        return _ResolvedCandidate("site", locator)
    if locator.kind == "structure":
        assert locator.normalized_domain is not None
        assert locator.service is not None
        assert locator.canonical_base_url is not None
        site_id = _resolve_site_id(
            connection,
            normalized_domain=locator.normalized_domain,
            service=locator.service,
            canonical_base_url=locator.canonical_base_url,
            registry=registry,
            result=result,
        )
        if site_id is None:
            return None
        return _ResolvedCandidate("structure", locator, site_id=site_id)
    strict_item = _strict_item_from_locator(locator, observed_url)
    recognized = _resolve_local_site(connection, strict_item, registry, result)
    if recognized is None:
        return None
    return _ResolvedCandidate("item", locator, item=recognized)


def _record_structure_candidate(
    connection: sqlite3.Connection,
    *,
    result: _SourceResult,
    candidate: _ResolvedCandidate,
    source_line: int,
    url_ordinal: int,
    source_channel: str,
    session_id: Optional[int] = None,
    source_path: Optional[str] = None,
    source_event_id: Optional[str] = None,
    document_id: Optional[int] = None,
    observed_at: Optional[str] = None,
    refresh_existing: bool = False,
) -> str:
    assert candidate.kind == "structure"
    assert candidate.site_id is not None
    locator = candidate.locator
    target = ensure_structure_reference(
        connection,
        site_id=candidate.site_id,
        locator=locator,
        observed_at=observed_at,
    )
    reference_id = int(target["reference_id"])
    if target["created_reference"]:
        result.new_structure_reference_ids.add(reference_id)
    else:
        result.reused_structure_reference_ids.add(reference_id)
    evidence = insert_or_reuse_structure_reference_evidence(
        connection,
        reference_id=reference_id,
        safe_locator_url=str(locator.safe_locator_url),
        container_hint=locator.container_hint,
        session_id=session_id,
        source_path=source_path,
        source_event_id=source_event_id,
        document_id=document_id,
        source_line=source_line,
        url_ordinal=url_ordinal,
        source_channel=source_channel,
        observed_at=observed_at,
        refresh_existing=refresh_existing,
    )
    evidence_key = str(evidence["evidence_key"])
    if evidence["created"]:
        result.new_structure_evidence_keys.add(evidence_key)
    else:
        result.reused_structure_evidence_keys.add(evidence_key)
    result.affected_structure_reference_ids.add(reference_id)
    return evidence_key


def _process_session(
    connection: sqlite3.Connection,
    session_id: int,
    registry: _ActionSiteRegistry,
) -> _SourceResult:
    with _atomic_source(connection):
        session = connection.execute(
            """
            SELECT id, session_class, session_role, index_policy
            FROM sessions WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
        if session is None:
            result = _SourceResult("session", session_id, "unavailable")
            result.add_reason("session-projection-missing")
            return result
        if (
            session["session_class"] != "work"
            or session["session_role"] != "primary"
            or session["index_policy"] != "full"
        ):
            result = _SourceResult("session", session_id, "excluded")
            result.add_reason("ineligible-session")
            return result

        scan = connection.execute(
            """
            SELECT status, extractor_version, observed_target_count,
                   retained_target_count
            FROM session_reference_scans
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
        if scan is None:
            result = _SourceResult("session", session_id, "unavailable")
            result.add_reason("session-projection-missing")
            return result
        if scan["extractor_version"] != REFERENCE_EXTRACTOR_VERSION:
            result = _SourceResult("session", session_id, "unavailable")
            result.add_reason("session-projection-stale")
            return result
        if scan["status"] == "error":
            result = _SourceResult("session", session_id, "unavailable")
            result.add_reason("session-projection-error")
            return result

        partial = scan["status"] == "partial"
        result = _SourceResult(
            "session", session_id, "partial" if partial else "complete"
        )
        result.scope_limits["session_projection_sources"] = 1
        if partial:
            result.add_reason("session-projection-partial")
            result.scope_limits["session_reference_overflow"] = max(
                0,
                int(scan["observed_target_count"])
                - int(scan["retained_target_count"]),
            )

        rows = connection.execute(
            """
            SELECT source_path, source_event_id, source_line,
                   evidence_ordinal, normalized_url, evidence_kind,
                   observed_at, target_key
            FROM session_reference_evidence
            WHERE session_id = ?
              AND target_kind = 'url'
              AND normalized_url IS NOT NULL
              AND evidence_kind IN (
                  'user_mention', 'assistant_mention', 'tool_result'
              )
            ORDER BY target_key, source_path, source_event_id,
                     source_line, evidence_ordinal, id
            """,
            (session_id,),
        ).fetchall()
        for row in rows:
            observed_url = str(row["normalized_url"] or "")
            if not _valid_session_location(row):
                result.add_skip("invalid_location")
                continue
            candidate = _recognize_candidate(
                connection=connection,
                result=result,
                observed_url=observed_url,
                registry=registry,
            )
            if candidate is None or candidate.kind == "site":
                continue
            if candidate.kind == "structure":
                _record_structure_candidate(
                    connection,
                    result=result,
                    candidate=candidate,
                    session_id=session_id,
                    source_path=str(row["source_path"]),
                    source_event_id=str(row["source_event_id"]),
                    source_line=int(row["source_line"]),
                    url_ordinal=int(row["evidence_ordinal"]),
                    source_channel=(
                        "approved_tool_result"
                        if row["evidence_kind"] == "tool_result"
                        else "visible_text"
                    ),
                    observed_at=row["observed_at"],
                )
                continue
            recognized = candidate.item
            assert recognized is not None
            external_resource_id, created = _item_for_target(
                connection,
                recognized,
                observed_url,
                row["observed_at"],
                registry.source_instances,
            )
            if created:
                result.new_item_ids.add(external_resource_id)
            else:
                result.reused_item_ids.add(external_resource_id)
            _insert_or_reuse_evidence(
                connection,
                result=result,
                external_resource_id=external_resource_id,
                recognized=recognized,
                observed_url=recognized.normalized.normalized_url,
                session_id=session_id,
                source_path=str(row["source_path"]),
                source_event_id=str(row["source_event_id"]),
                source_line=int(row["source_line"]),
                url_ordinal=int(row["evidence_ordinal"]),
                source_channel=(
                    "approved_tool_result"
                    if row["evidence_kind"] == "tool_result"
                    else "visible_text"
                ),
                observed_at=row["observed_at"],
            )
        for reference_id in sorted(result.affected_structure_reference_ids):
            project_structure_reference_search(connection, reference_id)
        result.finish_counts()
        return result


def _process_document(
    connection: sqlite3.Connection,
    document_id: int,
    registry: _ActionSiteRegistry,
    site_fingerprint: str,
) -> _SourceResult:
    try:
        with _atomic_source(connection):
            document = _current_document(connection, document_id)
            if document is None:
                raise _DocumentUnavailable("Document no longer exists")
            if document["context_root_id"] is None:
                raise _DocumentUnavailable("Document root is unavailable")
            if not bool(document["enabled"]):
                result = _SourceResult("document", document_id, "excluded")
                result.add_reason("disabled-document")
                return result
            if not bool(document["readable"]) or document["status"] != "ready":
                raise _DocumentUnavailable("Document root is unavailable")

            content_hash = str(document["content_hash"])
            source_fingerprint = document_evidence_source_fingerprint(
                content_hash
            )
            scan_was_current = _document_scan_is_current(
                connection,
                document_id=document_id,
                source_fingerprint=source_fingerprint,
                site_fingerprint=site_fingerprint,
            )
            scan = _read_document_scan(connection, document_id)
            current = _current_document(connection, document_id)
            if (
                current is None
                or current["context_root_id"] is None
                or not bool(current["enabled"])
                or not bool(current["readable"])
                or current["status"] != "ready"
                or str(current["content_hash"]) != content_hash
            ):
                raise _DocumentUnavailable("Document changed during Sync")

            result = _SourceResult(
                "document",
                document_id,
                "partial" if scan.url_overflow else "complete",
            )
            if scan.url_overflow:
                result.add_reason("document-url-limit")
                result.scope_limits["document_url_overflow"] = scan.url_overflow
            result.candidate_skips["key_only"] = scan.key_only_count

            retained_keys: set[str] = set()
            retained_structure_keys: set[str] = set()
            document_observed_at = utc_now()
            for candidate in scan.candidates:
                resolved = _recognize_candidate(
                    connection=connection,
                    result=result,
                    observed_url=candidate.observed_url,
                    registry=registry,
                )
                if resolved is None or resolved.kind == "site":
                    continue
                assert candidate.observed_url is not None
                if resolved.kind == "structure":
                    retained_structure_keys.add(
                        _record_structure_candidate(
                            connection,
                            result=result,
                            candidate=resolved,
                            document_id=document_id,
                            source_line=candidate.source_line,
                            url_ordinal=candidate.url_ordinal,
                            source_channel="visible_text",
                            observed_at=document_observed_at,
                            refresh_existing=not scan_was_current,
                        )
                    )
                    continue
                recognized = resolved.item
                assert recognized is not None
                external_resource_id, created = _item_for_target(
                    connection,
                    recognized,
                    candidate.observed_url,
                    document_observed_at,
                    registry.source_instances,
                    refresh_existing_url_observation=not scan_was_current,
                )
                if created:
                    result.new_item_ids.add(external_resource_id)
                else:
                    result.reused_item_ids.add(external_resource_id)
                retained_keys.add(
                    _insert_or_reuse_evidence(
                        connection,
                        result=result,
                        external_resource_id=external_resource_id,
                        recognized=recognized,
                        observed_url=candidate.observed_url,
                        document_id=document_id,
                        source_line=candidate.source_line,
                        url_ordinal=candidate.url_ordinal,
                        source_channel="visible_text",
                        refresh_existing=not scan_was_current,
                    )
                )

            if retained_keys:
                placeholders = ",".join("?" for _ in retained_keys)
                predicate = (
                    "document_id = ? AND evidence_key NOT IN ({})".format(
                        placeholders
                    )
                )
                values = (document_id,) + tuple(sorted(retained_keys))
            else:
                predicate = "document_id = ?"
                values = (document_id,)
            removed = int(
                connection.execute(
                    "SELECT COUNT(*) FROM atlassian_item_evidence WHERE "
                    + predicate,
                    values,
                ).fetchone()[0]
            )
            if removed:
                connection.execute(
                    "DELETE FROM atlassian_item_evidence WHERE " + predicate,
                    values,
                )
            result.counts["removed_evidence"] = removed
            removed_structure = remove_obsolete_document_structure_evidence(
                connection,
                document_id=document_id,
                retained_keys=retained_structure_keys,
            )
            result.removed_structure_evidence_keys.update(
                removed_structure["evidence_keys"]
            )
            result.affected_structure_reference_ids.update(
                removed_structure["reference_ids"]
            )
            for reference_id in sorted(
                result.affected_structure_reference_ids
            ):
                project_structure_reference_search(connection, reference_id)
            if not scan_was_current:
                record_document_evidence_scan(
                    connection,
                    document_id=document_id,
                    source_fingerprint=source_fingerprint,
                    site_fingerprint=site_fingerprint,
                    extractor_version=EVIDENCE_EXTRACTOR_VERSION,
                )
            result.finish_counts()
            return result
    except _DocumentUnavailable:
        result = _SourceResult("document", document_id, "unavailable")
        result.add_reason("context-unavailable")
        return result


class _ActionReport:
    def __init__(self) -> None:
        self.report = _empty_report()
        self.new_item_ids: set[int] = set()
        self.reused_item_ids: set[int] = set()
        self.new_structure_reference_ids: set[int] = set()
        self.reused_structure_reference_ids: set[int] = set()
        self.new_structure_evidence_keys: set[str] = set()
        self.reused_structure_evidence_keys: set[str] = set()
        self.removed_structure_evidence_keys: set[str] = set()

    def add(self, result: _SourceResult) -> None:
        result.finish_counts()
        sources = self.report["sources"]
        sources["considered"] += 1
        if result.outcome == "excluded":
            sources["excluded"] += 1
        else:
            sources["eligible"] += 1
        if result.outcome in {"complete", "partial"}:
            sources["scanned"] += 1
        if result.outcome == "partial":
            sources["partial"] += 1
        elif result.outcome == "unavailable":
            sources["unavailable"] += 1
        elif result.outcome == "failed":
            sources["failed"] += 1

        self.new_item_ids.update(result.new_item_ids)
        self.reused_item_ids.update(result.reused_item_ids)
        self.new_structure_reference_ids.update(
            result.new_structure_reference_ids
        )
        self.reused_structure_reference_ids.update(
            result.reused_structure_reference_ids
        )
        self.new_structure_evidence_keys.update(
            result.new_structure_evidence_keys
        )
        self.reused_structure_evidence_keys.update(
            result.reused_structure_evidence_keys
        )
        self.removed_structure_evidence_keys.update(
            result.removed_structure_evidence_keys
        )
        for key, value in result.candidate_skips.items():
            self.report["candidate_skips"][key] += value
        for key, value in result.scope_limits.items():
            self.report["scope_limits"][key] += value
        self.report["evidence"]["new"] += result.counts["new_evidence"]
        self.report["evidence"]["reused"] += result.counts[
            "reused_evidence"
        ]
        self.report["evidence"]["removed"] += result.counts[
            "removed_evidence"
        ]
        self.report["site_only"] += result.counts["site_only"]
        self.report["source_outcomes"].append(result.public())

    def finish(self) -> dict:
        self.report["items"]["new"] = len(self.new_item_ids)
        self.report["items"]["reused"] = len(
            self.reused_item_ids - self.new_item_ids
        )
        self.report["structure_references"]["new"] = len(
            self.new_structure_reference_ids
        )
        self.report["structure_references"]["reused"] = len(
            self.reused_structure_reference_ids
            - self.new_structure_reference_ids
        )
        self.report["structure_evidence"]["new"] = len(
            self.new_structure_evidence_keys
        )
        self.report["structure_evidence"]["reused"] = len(
            self.reused_structure_evidence_keys
            - self.new_structure_evidence_keys
        )
        self.report["structure_evidence"]["removed"] = len(
            self.removed_structure_evidence_keys
        )
        sources = self.report["sources"]
        if sources["failed"] and not sources["scanned"]:
            self.report["status"] = "failed"
        elif sources["partial"] or sources["unavailable"] or sources["failed"]:
            self.report["status"] = "partial"
        else:
            self.report["status"] = "complete"
        return self.report


def _commit_source_result(
    connection: sqlite3.Connection,
    result: _SourceResult,
    registry: _ActionSiteRegistry,
) -> _SourceResult:
    try:
        connection.commit()
    except Exception:
        connection.rollback()
        return _source_failure(result.kind, result.local_id)
    registry.publish(result)
    return result


def _source_ids(
    connection: sqlite3.Connection,
    table: str,
    *,
    maximum_id: int,
) -> tuple[int, ...]:
    if table not in {"sessions", "context_documents"}:
        raise ValueError("Unsupported Sync source table")
    if maximum_id <= 0:
        return ()
    cursor = connection.execute(
        "SELECT id FROM {} WHERE id > 0 AND id <= ? ORDER BY id".format(
            table
        ),
        (maximum_id,),
    )
    source_ids: list[int] = []
    while True:
        rows = cursor.fetchmany(SOURCE_BATCH_SIZE)
        if not rows:
            return tuple(source_ids)
        source_ids.extend(int(row["id"]) for row in rows)


def _source_id_batches(
    source_ids: tuple[int, ...],
) -> Iterator[tuple[int, ...]]:
    for offset in range(0, len(source_ids), SOURCE_BATCH_SIZE):
        yield source_ids[offset : offset + SOURCE_BATCH_SIZE]


def sync_atlassian_local_evidence(connection: sqlite3.Connection) -> dict:
    if not _SYNC_LOCK.acquire(blocking=False):
        return busy_atlassian_local_evidence_report()
    action = _ActionReport()
    try:
        (
            scope,
            source_instances,
            site_fingerprint,
            domain_sites,
        ) = configured_atlassian_sync_scope_snapshot(connection)
        registry = _ActionSiteRegistry(
            scope=dict(scope),
            source_instances=dict(source_instances),
            domain_sites=dict(domain_sites),
        )
        with _atomic_source(connection):
            maximum_session_id = int(
                connection.execute(
                    "SELECT COALESCE(MAX(id), 0) FROM sessions"
                ).fetchone()[0]
            )
            maximum_document_id = int(
                connection.execute(
                    "SELECT COALESCE(MAX(id), 0) FROM context_documents"
                ).fetchone()[0]
            )
            session_ids = _source_ids(
                connection,
                "sessions",
                maximum_id=maximum_session_id,
            )
            document_ids = _source_ids(
                connection,
                "context_documents",
                maximum_id=maximum_document_id,
            )

        for source_ids in _source_id_batches(session_ids):
            for session_id in source_ids:
                try:
                    result = _process_session(
                        connection,
                        session_id,
                        registry,
                    )
                except StructureReferenceIdentityCollision:
                    result = _source_failure(
                        "session", session_id, "identity-collision"
                    )
                except Exception:
                    result = _source_failure("session", session_id)
                action.add(
                    _commit_source_result(connection, result, registry)
                )

        for source_ids in _source_id_batches(document_ids):
            for document_id in source_ids:
                try:
                    result = _process_document(
                        connection,
                        document_id,
                        registry,
                        site_fingerprint,
                    )
                except StructureReferenceIdentityCollision:
                    result = _source_failure(
                        "document", document_id, "identity-collision"
                    )
                except Exception:
                    result = _source_failure("document", document_id)
                action.add(
                    _commit_source_result(connection, result, registry)
                )
        return action.finish()
    except Exception:
        connection.rollback()
        report = action.finish()
        report["status"] = "failed"
        return report
    finally:
        _SYNC_LOCK.release()
