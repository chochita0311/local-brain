"""Optional Atlassian evidence maintenance on the ingestion transaction."""

from .evidence import (
    clear_context_root_evidence, document_evidence_source_fingerprint,
    evidence_scan_is_current, reconcile_document_evidence,
    reconcile_session_evidence, session_evidence_source_fingerprint,
)
from .structure_references import project_structure_reference_search


class AtlassianIngestion:
    def document_is_current(self, connection, document_id, content_hash):
        return evidence_scan_is_current(
            connection, document_id=document_id,
            source_fingerprint=document_evidence_source_fingerprint(content_hash),
        )

    def document_indexed(self, connection, document_id, content_hash, body):
        reconcile_document_evidence(
            connection, document_id=document_id,
            source_fingerprint=document_evidence_source_fingerprint(content_hash), body=body,
        )

    def _session_fingerprint(self, source_id, source_path, size_bytes, mtime_ns):
        return session_evidence_source_fingerprint(
            source_id=source_id, source_path=source_path,
            size_bytes=size_bytes, mtime_ns=mtime_ns,
        )

    def session_is_current(self, connection, *, session_id, **source):
        return evidence_scan_is_current(
            connection, session_id=session_id, source_path=source["source_path"],
            source_fingerprint=self._session_fingerprint(**source),
        )

    def session_indexed(self, connection, *, session_id, candidates, **source):
        reconcile_session_evidence(
            connection, session_id=session_id, source_path=source["source_path"],
            source_fingerprint=self._session_fingerprint(**source), candidates=candidates,
        )

    def before_owner_deleted(self, connection, *, session_id, document_id):
        column = "session_id" if session_id is not None else "document_id"
        return tuple(row[0] for row in connection.execute(
            "SELECT DISTINCT reference_id FROM atlassian_structure_reference_evidence WHERE " + column + " = ? ORDER BY reference_id",
            (session_id if session_id is not None else document_id,),
        ))

    def after_owner_deleted(self, connection, snapshot):
        for reference_id in snapshot:
            project_structure_reference_search(connection, reference_id)

    def session_sources_pruned(self, connection, source_id, valid_paths):
        rows = connection.execute(
            """SELECT atlassian_evidence_scans.id, atlassian_evidence_scans.session_id,
                      atlassian_evidence_scans.source_path
            FROM atlassian_evidence_scans
            JOIN sessions ON sessions.id = atlassian_evidence_scans.session_id
            WHERE sessions.source_id = ?""", (source_id,),
        ).fetchall()
        for row in rows:
            if row["source_path"] not in valid_paths:
                self._clear_source(connection, row)

    def empty_session_source(self, connection, source_id, source_path):
        rows = connection.execute(
            """SELECT atlassian_evidence_scans.id, atlassian_evidence_scans.session_id,
                      atlassian_evidence_scans.source_path
            FROM atlassian_evidence_scans
            JOIN sessions ON sessions.id = atlassian_evidence_scans.session_id
            WHERE sessions.source_id = ? AND atlassian_evidence_scans.source_path = ?""",
            (source_id, source_path),
        ).fetchall()
        for row in rows:
            self._clear_source(connection, row)

    def _clear_source(self, connection, row):
        connection.execute(
            "DELETE FROM atlassian_item_evidence WHERE session_id = ? AND source_path = ?",
            (row["session_id"], row["source_path"]),
        )
        connection.execute("DELETE FROM atlassian_evidence_scans WHERE id = ?", (row["id"],))

    def context_root_removed(self, connection, root_id):
        clear_context_root_evidence(connection, root_id)
