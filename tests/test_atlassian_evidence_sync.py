import hashlib
import json
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.atlassian import (
    create_or_reuse_atlassian_stub,
    normalize_atlassian_url,
    register_atlassian_site,
)
from localbrain.atlassian_evidence_sync import (
    SOURCE_REASON_CODES,
    _DocumentStreamScanner,
    _SYNC_LOCK,
    sync_atlassian_local_evidence,
)
from localbrain.atlassian_evidence import (
    configured_atlassian_site_fingerprint,
    document_evidence_source_fingerprint,
    evidence_scan_is_current,
    reconcile_document_evidence,
)
from localbrain.atlassian_browse import browse_inventory
from localbrain.ingest.common import (
    EVIDENCE_EXTRACTOR_VERSION,
    REFERENCE_EXTRACTOR_VERSION,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class AtlassianEvidenceSyncTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.session_source_id = self._source("codex", "/synthetic/sessions")
        self.context_source_id = self._source("context", "/synthetic/context")
        self.root_id = int(
            self.connection.execute(
                """
                INSERT INTO context_roots(path, label)
                VALUES ('/synthetic/context', 'Synthetic Context')
                """
            ).lastrowid
        )
        self.jira_instance_id = int(
            self.connection.execute(
                """
                INSERT INTO external_source_instances(
                    instance_key, provider_kind, service, display_name
                ) VALUES ('synthetic-jira', 'mcp_gateway', 'jira', 'Jira')
                """
            ).lastrowid
        )
        self.site = register_atlassian_site(
            self.connection,
            source_instance_id=self.jira_instance_id,
            base_url="https://jira.example.test",
        )

    def tearDown(self):
        self.connection.close()

    def _source(self, kind, root_path):
        return int(
            self.connection.execute(
                "INSERT INTO sources(kind, name, root_path) VALUES (?, ?, ?)",
                (kind, kind.title(), root_path),
            ).lastrowid
        )

    def _assert_reason_vocabulary(self, report):
        for outcome in report["source_outcomes"]:
            self.assertTrue(
                set(outcome["reason_codes"]).issubset(SOURCE_REASON_CODES)
            )

    def _session(
        self,
        name,
        *,
        session_class="work",
        session_role="primary",
        index_policy="full",
    ):
        return int(
            self.connection.execute(
                """
                INSERT INTO sessions(
                    source_id, external_id, source_path, title,
                    session_class, session_role, index_policy
                ) VALUES (?, ?, ?, 'Synthetic Session', ?, ?, ?)
                """,
                (
                    self.session_source_id,
                    name,
                    "/synthetic/{}.jsonl".format(name),
                    session_class,
                    session_role,
                    index_policy,
                ),
            ).lastrowid
        )

    def _reference_scan(
        self,
        session_id,
        *,
        status="ok",
        observed=1,
        retained=1,
        extractor_version=REFERENCE_EXTRACTOR_VERSION,
    ):
        self.connection.execute(
            """
            INSERT INTO session_reference_scans(
                session_id, source_fingerprint, extractor_version, status,
                observed_target_count, retained_target_count,
                error_code, error_message, scanned_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL,
                      '2026-08-29T00:00:00Z', '2026-08-29T00:00:00Z')
            """,
            (
                session_id,
                hashlib.sha256(str(session_id).encode("ascii")).hexdigest(),
                extractor_version,
                status,
                observed,
                retained,
            ),
        )

    def _reference(
        self,
        session_id,
        url,
        *,
        line=1,
        ordinal=1,
        evidence_kind="user_mention",
        target_kind="url",
    ):
        normalized_url = url if target_kind == "url" else None
        external_resource_id = None
        target_key = "url:{}".format(hashlib.sha256(url.encode()).hexdigest())
        if target_kind == "atlassian_item":
            row = self.connection.execute(
                "SELECT external_resource_id FROM atlassian_items ORDER BY 1 LIMIT 1"
            ).fetchone()
            external_resource_id = int(row[0])
            target_key = "atlassian:{}".format(external_resource_id)
        evidence_key = hashlib.sha256(
            "{}:{}:{}:{}".format(
                session_id, line, ordinal, evidence_kind
            ).encode("utf-8")
        ).hexdigest()
        tool_name = None
        tool_call_id = None
        read_outcome = None
        if evidence_kind in {"tool_result", "resource_read"}:
            tool_name = "synthetic.tool"
            tool_call_id = "call-{}-{}".format(session_id, line)
        if evidence_kind == "resource_read":
            read_outcome = "success"
        self.connection.execute(
            """
            INSERT INTO session_reference_evidence(
                session_id, source_path, source_event_id, source_line,
                evidence_ordinal, target_kind, target_key,
                external_resource_id, evidence_kind, read_outcome,
                observed_identity, normalized_url, tool_name, tool_call_id,
                extractor_version, evidence_key,
                first_observed_at, last_observed_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'retained identity', ?, ?, ?, ?, ?,
                      '2026-08-29T00:00:00Z', '2026-08-29T00:00:00Z',
                      '2026-08-29T00:00:00Z')
            """,
            (
                session_id,
                "/synthetic/{}.jsonl".format(session_id),
                "event-{}-{}".format(session_id, line),
                line,
                ordinal,
                target_kind,
                target_key,
                external_resource_id,
                evidence_kind,
                read_outcome,
                normalized_url,
                tool_name,
                tool_call_id,
                REFERENCE_EXTRACTOR_VERSION,
                evidence_key,
            ),
        )

    def _document(self, name, body, *, content_hash=None):
        encoded = body.encode("utf-8")
        return int(
            self.connection.execute(
                """
                INSERT INTO context_documents(
                    source_id, context_root_id, path, relative_path, title,
                    body, size_bytes, mtime_ns, content_hash
                ) VALUES (?, ?, ?, ?, 'Private synthetic title', ?, ?, 1, ?)
                """,
                (
                    self.context_source_id,
                    self.root_id,
                    "/synthetic/context/{}".format(name),
                    name,
                    body,
                    len(encoded),
                    content_hash or hashlib.sha256(encoded).hexdigest(),
                ),
            ).lastrowid
        )

    def test_document_stream_scanner_builds_flat_url_candidates(self):
        scanner = _DocumentStreamScanner()
        scanner.feed(
            "prefix https://jira.example.test/browse/SYN-1 "
            "https://jira.example.test/browse/SYN-2\n"
        )

        scan = scanner.finish()

        self.assertEqual(
            [
                (candidate.observed_url, candidate.source_line, candidate.url_ordinal)
                for candidate in scan.candidates
            ],
            [
                ("https://jira.example.test/browse/SYN-1", 1, 1),
                ("https://jira.example.test/browse/SYN-2", 1, 2),
            ],
        )
        self.assertEqual(scan.url_overflow, 0)

    def test_empty_registry_session_and_document_create_one_site_links_without_spaces_or_bindings(self):
        self.connection.execute("DELETE FROM atlassian_sites")
        session_id = self._session("empty-registry")
        self._reference_scan(session_id)
        self._reference(
            session_id,
            "https://shared.empty.test/browse/EMPTY-1",
        )
        document_body = (
            "https://shared.empty.test/wiki/spaces/ＴＥＡＭ/pages/77/Guide\n"
        )
        document_hash = hashlib.sha256(document_body.encode("utf-8")).hexdigest()
        document_id = self._document(
            "empty-registry.md",
            document_body,
            content_hash=document_hash,
        )
        statements = []
        self.connection.set_trace_callback(statements.append)

        first = sync_atlassian_local_evidence(self.connection)
        self.connection.set_trace_callback(None)

        self.assertEqual(first["status"], "complete")
        self.assertEqual(first["items"], {"new": 2, "reused": 0})
        self.assertEqual(first["evidence"], {"new": 2, "reused": 0, "removed": 0})
        sites = self.connection.execute(
            "SELECT id, normalized_domain FROM atlassian_sites"
        ).fetchall()
        self.assertEqual(
            [(row["normalized_domain"]) for row in sites],
            ["shared.empty.test"],
        )
        rows = self.connection.execute(
            """
            SELECT atlassian_items.service, atlassian_items.site_id,
                   atlassian_items.space_id,
                   atlassian_items.source_instance_id,
                   atlassian_item_urls.normalized_url
            FROM atlassian_items
            JOIN atlassian_item_urls
              ON atlassian_item_urls.external_resource_id =
                 atlassian_items.external_resource_id
             AND atlassian_item_urls.url_role = 'canonical'
            ORDER BY atlassian_items.service
            """
        ).fetchall()
        self.assertEqual({row["service"] for row in rows}, {"jira", "confluence"})
        self.assertEqual({int(row["site_id"]) for row in rows}, {int(sites[0]["id"])})
        self.assertTrue(all(row["space_id"] is None for row in rows))
        self.assertTrue(all(row["source_instance_id"] is None for row in rows))
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM atlassian_spaces").fetchone()[0],
            0,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_site_bindings"
            ).fetchone()[0],
            0,
        )
        writes = [
            " ".join(statement.lower().split())
            for statement in statements
            if statement.lstrip().split(None, 1)[0].upper()
            in {"INSERT", "UPDATE", "DELETE", "REPLACE"}
        ]
        self.assertFalse(
            any("atlassian_spaces" in statement for statement in writes)
        )
        self.assertFalse(
            any(
                "atlassian_items" in statement and "space_id" in statement
                for statement in writes
            )
        )
        self.assertFalse(
            any("atlassian_site_bindings" in statement for statement in writes)
        )
        inventory = browse_inventory(self.connection, {"attention": "all"})
        self.assertEqual(inventory["matching_count"], 2)
        self.assertEqual(inventory["hierarchy"]["eligible_count"], 2)
        self.assertEqual(len(inventory["hierarchy"]["sites"]), 1)
        self.assertEqual(
            {
                container["structural_scope"]
                for container in inventory["hierarchy"]["sites"][0]["containers"]
            },
            {"url:jira:EMPTY", "url:confluence:TEAM"},
        )

        source_fingerprint = document_evidence_source_fingerprint(document_hash)
        self.assertFalse(
            evidence_scan_is_current(
                self.connection,
                document_id=document_id,
                source_fingerprint=source_fingerprint,
            )
        )
        reconcile_document_evidence(
            self.connection,
            document_id=document_id,
            source_fingerprint=source_fingerprint,
            body=document_body,
        )
        self.assertTrue(
            evidence_scan_is_current(
                self.connection,
                document_id=document_id,
                source_fingerprint=source_fingerprint,
            )
        )
        graph = {
            table: self.connection.execute(
                "SELECT COUNT(*) FROM {}".format(table)
            ).fetchone()[0]
            for table in (
                "atlassian_sites",
                "atlassian_items",
                "atlassian_item_urls",
                "atlassian_item_evidence",
                "atlassian_spaces",
                "atlassian_site_bindings",
            )
        }
        before_repeat = self.connection.total_changes

        repeat = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(repeat["items"], {"new": 0, "reused": 2})
        self.assertEqual(repeat["evidence"], {"new": 0, "reused": 2, "removed": 0})
        self.assertEqual(self.connection.total_changes, before_repeat)
        self.assertEqual(
            graph,
            {
                table: self.connection.execute(
                    "SELECT COUNT(*) FROM {}".format(table)
                ).fetchone()[0]
                for table in graph
            },
        )
        self.assertTrue(
            evidence_scan_is_current(
                self.connection,
                document_id=document_id,
                source_fingerprint=source_fingerprint,
            )
        )

    def test_same_source_duplicate_and_later_source_reuse_one_local_link(self):
        self.connection.execute("DELETE FROM atlassian_sites")
        url = "https://reuse.empty.test/browse/REUSE-1"
        session_id = self._session("same-source-duplicate")
        self._reference_scan(session_id, observed=2, retained=2)
        self._reference(session_id, url, line=1, ordinal=1)
        self._reference(session_id, url, line=2, ordinal=1)
        self._document("later-reuse.md", url + "\n")

        report = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(report["items"], {"new": 1, "reused": 0})
        self.assertEqual(report["evidence"], {"new": 3, "reused": 0, "removed": 0})
        self.assertEqual(
            report["source_outcomes"][0]["counts"]["new_items"], 1
        )
        self.assertEqual(
            report["source_outcomes"][1]["counts"]["reused_items"], 1
        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM atlassian_sites").fetchone()[0],
            1,
        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM atlassian_items").fetchone()[0],
            1,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_evidence"
            ).fetchone()[0],
            3,
        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM atlassian_spaces").fetchone()[0],
            0,
        )

    def test_failed_source_rolls_back_unpublished_site_before_peer_retries(self):
        self.connection.execute("DELETE FROM atlassian_sites")
        failed_id = self._document(
            "first-fails.md",
            "https://rollback.empty.test/browse/ROLL-1\n",
        )
        peer_id = self._document(
            "peer-retries.md",
            "https://rollback.empty.test/browse/ROLL-2\n",
        )
        from localbrain import atlassian_evidence_sync as sync_module

        original_register = sync_module.register_atlassian_site
        calls = 0

        def fail_after_first_site_write(connection, **kwargs):
            nonlocal calls
            calls += 1
            site = original_register(connection, **kwargs)
            if calls == 1:
                raise RuntimeError("synthetic source-local rollback")
            return site

        with patch.object(
            sync_module,
            "register_atlassian_site",
            side_effect=fail_after_first_site_write,
        ):
            report = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(report["status"], "partial")
        outcomes = {
            row["local_id"]: row for row in report["source_outcomes"]
        }
        self.assertEqual(outcomes[failed_id]["outcome"], "failed")
        self.assertEqual(outcomes[peer_id]["outcome"], "complete")
        self.assertEqual(calls, 2)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM atlassian_sites").fetchone()[0],
            1,
        )

        urls = [
            row[0]
            for row in self.connection.execute(
                "SELECT normalized_url FROM atlassian_item_urls"
            )
        ]
        self.assertEqual(
            urls,
            ["https://rollback.empty.test/browse/ROLL-2"],
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_evidence WHERE document_id = ?",
                (failed_id,),
            ).fetchone()[0],
            0,
        )

    def test_frozen_service_site_wins_over_same_domain_cross_service_site(self):
        wiki_instance_id = int(
            self.connection.execute(
                """
                INSERT INTO external_source_instances(
                    instance_key, provider_kind, service, display_name
                ) VALUES ('same-domain-wiki', 'mcp_gateway',
                          'confluence', 'Same-domain Wiki')
                """
            ).lastrowid
        )
        wiki_site_id = int(
            self.connection.execute(
                """
                INSERT INTO atlassian_sites(
                    source_instance_id, normalized_domain,
                    canonical_base_url
                ) VALUES (?, 'jira.example.test',
                          'https://jira.example.test')
                """,
                (wiki_instance_id,),
            ).lastrowid
        )
        self.connection.execute(
            """
            INSERT INTO atlassian_site_bindings(site_id, source_instance_id)
            VALUES (?, ?)
            """,
            (wiki_site_id, wiki_instance_id),
        )
        self._document(
            "mapped-jira.md",
            "https://jira.example.test/browse/MAPPED-1\n",
        )

        report = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(report["candidate_skips"]["ambiguous_site"], 0)
        row = self.connection.execute(
            """
            SELECT atlassian_items.site_id,
                   atlassian_items.source_instance_id
            FROM atlassian_items
            JOIN atlassian_item_urls
              ON atlassian_item_urls.external_resource_id =
                 atlassian_items.external_resource_id
            WHERE atlassian_item_urls.url_role = 'canonical'
              AND atlassian_item_urls.normalized_url =
                  'https://jira.example.test/browse/MAPPED-1'
            """
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(int(row["site_id"]), int(self.site["id"]))
        self.assertEqual(
            int(row["source_instance_id"]), self.jira_instance_id
        )

    def test_same_domain_multi_site_without_service_mapping_is_ambiguous(self):
        for suffix in ("one", "two"):
            self.connection.execute(
                """
                INSERT INTO atlassian_sites(
                    normalized_domain, display_name, canonical_base_url
                ) VALUES ('unmapped.multi.test', ?,
                          'https://unmapped.multi.test')
                """,
                ("Unmapped {}".format(suffix),),
            )
        self._document(
            "unmapped-multi.md",
            "https://unmapped.multi.test/browse/AMB-1\n",
        )

        report = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(report["candidate_skips"]["ambiguous_site"], 1)
        self.assertEqual(report["items"], {"new": 0, "reused": 0})
        self.assertIsNone(
            self.connection.execute(
                """
                SELECT atlassian_items.external_resource_id
                FROM atlassian_items
                JOIN atlassian_sites
                  ON atlassian_sites.id = atlassian_items.site_id
                WHERE atlassian_sites.normalized_domain =
                      'unmapped.multi.test'
                """
            ).fetchone()
        )

    def test_document_currentness_ignores_site_fingerprint_only_change(self):
        self.assertEqual(
            EVIDENCE_EXTRACTOR_VERSION,
            "localbrain.atlassian-evidence.v4",
        )
        document_id = self._document(
            "stable-site-fingerprint.md",
            "https://jira.example.test/browse/STABLE-1\n",
        )
        first = sync_atlassian_local_evidence(self.connection)
        self.assertEqual(first["items"], {"new": 1, "reused": 0})
        scan = self.connection.execute(
            """
            SELECT site_fingerprint, extractor_version
            FROM atlassian_evidence_scans
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchone()
        self.assertEqual(
            scan["extractor_version"], EVIDENCE_EXTRACTOR_VERSION
        )
        original_site_fingerprint = str(scan["site_fingerprint"])

        extra_instance_id = int(
            self.connection.execute(
                """
                INSERT INTO external_source_instances(
                    instance_key, provider_kind, service, display_name
                ) VALUES ('fingerprint-only', 'mcp_gateway', 'jira',
                          'Fingerprint only')
                """
            ).lastrowid
        )
        register_atlassian_site(
            self.connection,
            source_instance_id=extra_instance_id,
            base_url="https://fingerprint-only.example.test",
        )
        self.assertNotEqual(
            configured_atlassian_site_fingerprint(self.connection),
            original_site_fingerprint,
        )
        before_repeat = self.connection.total_changes
        statements = []
        self.connection.set_trace_callback(statements.append)

        repeat = sync_atlassian_local_evidence(self.connection)

        self.connection.set_trace_callback(None)
        self.assertEqual(repeat["items"], {"new": 0, "reused": 1})
        self.assertEqual(self.connection.total_changes, before_repeat)
        writes = [
            statement
            for statement in statements
            if statement.lstrip().split(None, 1)[0].upper()
            in {"INSERT", "UPDATE", "DELETE", "REPLACE"}
        ]
        self.assertEqual(writes, [])
        unchanged_scan = self.connection.execute(
            """
            SELECT site_fingerprint, extractor_version
            FROM atlassian_evidence_scans
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchone()
        self.assertEqual(
            (
                unchanged_scan["site_fingerprint"],
                unchanged_scan["extractor_version"],
            ),
            (original_site_fingerprint, EVIDENCE_EXTRACTOR_VERSION),
        )

    def test_persisted_session_and_document_sources_report_separate_units(self):
        session_id = self._session("primary")
        self._reference_scan(session_id, observed=3, retained=3)
        session_url = "https://jira.example.test/browse/SYN-1"
        self._reference(session_id, session_url, line=2)
        self._reference(
            session_id,
            session_url,
            line=3,
            ordinal=2,
            evidence_kind="tool_result",
        )
        self._reference(
            session_id,
            session_url,
            line=4,
            ordinal=3,
            evidence_kind="resource_read",
        )
        document_id = self._document(
            "evidence.md",
            "SYN-99 is key only\n"
            "https://jira.example.test/browse/DOC-2\n"
            "https://jira.example.test/projects/SYN\n"
            "https://jira.example.test/projects/SYN\n"
            "https://unknown.example.test/browse/NOPE-1\n"
            "https://jira.example.test:99999/browse/NOPE-2\n",
        )

        report = sync_atlassian_local_evidence(self.connection)

        self._assert_reason_vocabulary(report)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(
            report["sources"],
            {
                "considered": 2,
                "eligible": 2,
                "scanned": 2,
                "partial": 0,
                "unavailable": 0,
                "failed": 0,
                "excluded": 0,
            },
        )
        self.assertEqual(report["items"], {"new": 3, "reused": 0})
        self.assertEqual(
            report["evidence"], {"new": 4, "reused": 0, "removed": 0}
        )
        self.assertEqual(
            report["structure_references"], {"new": 1, "reused": 0}
        )
        self.assertEqual(
            report["structure_evidence"],
            {"new": 2, "reused": 0, "removed": 0},
        )
        self.assertEqual(report["site_only"], 0)
        self.assertEqual(
            report["candidate_skips"],
            {
                "key_only": 1,
                "unsafe_url": 1,
                "unsupported_locator": 0,
                "unconfigured_domain": 0,
                "ambiguous_site": 0,
                "invalid_location": 0,
            },
        )
        self.assertEqual(
            report["scope_limits"],
            {
                "session_projection_sources": 1,
                "session_reference_overflow": 0,
                "document_url_overflow": 0,
            },
        )
        self.assertEqual(
            [row["local_id"] for row in report["source_outcomes"]],
            [session_id, document_id],
        )
        session_outcome = report["source_outcomes"][0]
        self.assertEqual(session_outcome["counts"]["urls"], 1)
        self.assertEqual(session_outcome["counts"]["new_evidence"], 2)
        document_outcome = report["source_outcomes"][1]
        self.assertEqual(document_outcome["counts"]["skipped"], 2)
        self.assertEqual(
            document_outcome["counts"]["new_structure_references"], 1
        )
        self.assertEqual(
            document_outcome["counts"]["new_structure_evidence"], 2
        )
        serialized = json.dumps(report)
        self.assertNotIn("/synthetic", serialized)
        self.assertNotIn("jira.example.test", serialized)
        self.assertNotIn("Private synthetic title", serialized)
        channels = {
            row[0]
            for row in self.connection.execute(
                "SELECT source_channel FROM atlassian_item_evidence WHERE session_id = ?",
                (session_id,),
            )
        }
        self.assertEqual(channels, {"visible_text", "approved_tool_result"})

    def test_session_reconciliation_is_merge_only_and_repeat_has_no_write(self):
        session_id = self._session("repeat")
        self._reference_scan(session_id)
        url = "https://jira.example.test/browse/SYN-2"
        self._reference(session_id, url)
        first = sync_atlassian_local_evidence(self.connection)
        evidence_id = int(
            self.connection.execute(
                "SELECT id FROM atlassian_item_evidence"
            ).fetchone()[0]
        )
        self.connection.execute(
            """
            UPDATE atlassian_item_evidence
            SET observed_url = ?, observed_title = 'Richer title'
            WHERE id = ?
            """,
            (url + "?original=1", evidence_id),
        )
        external_resource_id = int(
            self.connection.execute(
                "SELECT external_resource_id FROM atlassian_item_evidence WHERE id = ?",
                (evidence_id,),
            ).fetchone()[0]
        )
        richer_item_url = url + "?richer-owner=1"
        stable_item_url_observed_at = "1997-01-01T00:00:00Z"
        self.connection.execute(
            """
            UPDATE atlassian_item_urls
            SET observed_url = ?, last_observed_at = ?
            WHERE external_resource_id = ?
            """,
            (
                richer_item_url,
                stable_item_url_observed_at,
                external_resource_id,
            ),
        )
        before = self.connection.total_changes

        second = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(first["items"], {"new": 1, "reused": 0})
        self.assertEqual(second["items"], {"new": 0, "reused": 1})
        self.assertEqual(second["evidence"]["reused"], 1)
        self.assertEqual(self.connection.total_changes, before)
        evidence = self.connection.execute(
            "SELECT observed_url, observed_title FROM atlassian_item_evidence"
        ).fetchone()
        self.assertEqual(
            tuple(evidence), (url + "?original=1", "Richer title")
        )
        item_url = self.connection.execute(
            """
            SELECT observed_url, last_observed_at
            FROM atlassian_item_urls
            WHERE external_resource_id = ?
            """,
            (external_resource_id,),
        ).fetchone()
        self.assertEqual(
            tuple(item_url),
            (richer_item_url, stable_item_url_observed_at),
        )
        self.connection.execute(
            "DELETE FROM session_reference_evidence WHERE session_id = ?",
            (session_id,),
        )
        sync_atlassian_local_evidence(self.connection)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_evidence"
            ).fetchone()[0],
            1,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_evidence_scans WHERE session_id IS NOT NULL"
            ).fetchone()[0],
            0,
        )

    def test_session_partial_unavailable_and_excluded_do_not_read_raw_sources(self):
        partial_id = self._session("partial")
        self._reference_scan(partial_id, status="partial", observed=105, retained=100)
        self._reference(
            partial_id, "https://jira.example.test/browse/PART-1"
        )
        unavailable_id = self._session("unavailable")
        stale_id = self._session("stale")
        self._reference_scan(stale_id, extractor_version="stale-reference.v0")
        error_id = self._session("error")
        self._reference_scan(error_id)
        self.connection.execute(
            """
            UPDATE session_reference_scans
            SET status = 'error', error_code = 'synthetic-error'
            WHERE session_id = ?
            """,
            (error_id,),
        )
        excluded_id = self._session(
            "maintenance",
            session_class="maintenance",
            index_policy="metadata_only",
        )
        statements = []
        self.connection.set_trace_callback(statements.append)

        report = sync_atlassian_local_evidence(self.connection)

        self._assert_reason_vocabulary(report)
        self.connection.set_trace_callback(None)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(
            report["sources"],
            {
                "considered": 5,
                "eligible": 4,
                "scanned": 1,
                "partial": 1,
                "unavailable": 3,
                "failed": 0,
                "excluded": 1,
            },
        )
        self.assertEqual(
            report["scope_limits"],
            {
                "session_projection_sources": 1,
                "session_reference_overflow": 5,
                "document_url_overflow": 0,
            },
        )
        outcomes = {
            row["local_id"]: (row["outcome"], row["reason_codes"])
            for row in report["source_outcomes"]
        }
        self.assertEqual(outcomes[partial_id][0], "partial")
        self.assertEqual(
            outcomes[unavailable_id],
            ("unavailable", ["session-projection-missing"]),
        )
        self.assertEqual(
            outcomes[stale_id],
            ("unavailable", ["session-projection-stale"]),
        )
        self.assertEqual(
            outcomes[error_id],
            ("unavailable", ["session-projection-error"]),
        )
        self.assertEqual(outcomes[excluded_id][0], "excluded")
        sql = "\n".join(statements).lower()
        self.assertNotIn("source_files", sql)
        self.assertNotIn("activity_events", sql)

    def test_invalid_locations_and_ambiguous_sites_are_distinct_skips(self):
        ambiguous_site_id = int(
            self.connection.execute(
                """
                INSERT INTO atlassian_sites(
                    normalized_domain, canonical_base_url
                ) VALUES ('jira.example.test', 'https://jira.example.test')
                """
            ).lastrowid
        )
        self.connection.execute(
            """
            INSERT INTO atlassian_spaces(
                site_id, service, remote_id, name, canonical_url, coverage
            ) VALUES (?, 'jira', 'ambiguous-space', 'Ambiguous',
                      'https://jira.example.test/projects/AMB',
                      'selected-content')
            """,
            (ambiguous_site_id,),
        )
        session_id = self._session("invalid-location")
        self._reference_scan(session_id)
        self._reference(
            session_id, "https://jira.example.test/browse/INVALID-1"
        )
        self.connection.execute(
            """
            UPDATE session_reference_evidence
            SET source_event_id = NULL
            WHERE session_id = ?
            """,
            (session_id,),
        )
        self._document(
            "ambiguous.md",
            "https://jira.example.test/browse/AMB-1\n",
        )

        report = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["candidate_skips"]["invalid_location"], 1)
        self.assertEqual(report["candidate_skips"]["ambiguous_site"], 1)
        self.assertEqual(report["items"], {"new": 0, "reused": 0})
        self._assert_reason_vocabulary(report)

    def test_overlong_remote_identities_are_unsupported_for_both_source_kinds(self):
        jira_key = "A{}-1".format("B" * 298)
        confluence_page_id = "7" * 301
        self.assertGreater(len(jira_key), 300)
        self.assertGreater(len(confluence_page_id), 300)
        urls = (
            "https://jira.example.test/browse/{}".format(jira_key),
            "https://jira.example.test/wiki/pages/{}/Page".format(
                confluence_page_id
            ),
        )
        session_id = self._session("overlong-identities")
        self._reference_scan(session_id, observed=2, retained=2)
        for ordinal, url in enumerate(urls, start=1):
            self._reference(
                session_id,
                url,
                line=ordinal,
                ordinal=ordinal,
            )
        document_id = self._document(
            "overlong-identities.md", "\n".join(urls) + "\n"
        )

        report = sync_atlassian_local_evidence(self.connection)

        self._assert_reason_vocabulary(report)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["sources"]["failed"], 0)
        self.assertEqual(report["candidate_skips"]["unsupported_locator"], 4)
        self.assertEqual(report["items"], {"new": 0, "reused": 0})
        self.assertEqual(
            report["evidence"], {"new": 0, "reused": 0, "removed": 0}
        )
        outcomes = {
            (row["kind"], row["local_id"]): row
            for row in report["source_outcomes"]
        }
        for kind, local_id in (
            ("session", session_id),
            ("document", document_id),
        ):
            outcome = outcomes[(kind, local_id)]
            self.assertEqual(outcome["outcome"], "complete")
            self.assertEqual(outcome["counts"]["skipped"], 2)
            self.assertEqual(
                outcome["reason_codes"], ["unsupported-locator"]
            )

    def test_structure_and_site_locators_create_reference_and_report_site_only(self):
        urls = (
            "https://structure.empty.test/secure/RapidBoard.jspa?rapidView=17",
            "https://structure.empty.test/secure/RapidBoard.jspa",
        )
        session_id = self._session("structure-only")
        self._reference_scan(session_id, observed=2, retained=2)
        for index, url in enumerate(urls, 1):
            self._reference(session_id, url, line=index, ordinal=1)
        document_id = self._document(
            "structure-only.md", "\n".join(urls) + "\n"
        )
        before = {
            table: self.connection.execute(
                "SELECT COUNT(*) FROM {}".format(table)
            ).fetchone()[0]
            for table in (
                "atlassian_sites",
                "atlassian_spaces",
                "atlassian_items",
                "atlassian_item_urls",
                "atlassian_item_evidence",
            )
        }

        report = sync_atlassian_local_evidence(self.connection)

        self._assert_reason_vocabulary(report)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["candidate_skips"]["unsupported_locator"], 0)
        self.assertEqual(report["items"], {"new": 0, "reused": 0})
        self.assertEqual(
            report["evidence"], {"new": 0, "reused": 0, "removed": 0}
        )
        self.assertEqual(report["structure_references"], {"new": 1, "reused": 0})
        self.assertEqual(
            report["structure_evidence"],
            {"new": 2, "reused": 0, "removed": 0},
        )
        self.assertEqual(report["site_only"], 2)
        outcomes = {
            (row["kind"], row["local_id"]): row
            for row in report["source_outcomes"]
        }
        for key in (("session", session_id), ("document", document_id)):
            self.assertEqual(outcomes[key]["outcome"], "complete")
            self.assertEqual(outcomes[key]["reason_codes"], [])
            self.assertEqual(outcomes[key]["counts"]["site_only"], 1)
        after = {
            table: self.connection.execute(
                "SELECT COUNT(*) FROM {}".format(table)
            ).fetchone()[0]
            for table in before
        }
        self.assertEqual(after["atlassian_sites"], before["atlassian_sites"] + 1)
        for table in (
            "atlassian_spaces",
            "atlassian_items",
            "atlassian_item_urls",
            "atlassian_item_evidence",
        ):
            self.assertEqual(after[table], before[table])
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_structure_references"
            ).fetchone()[0],
            1,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_structure_reference_evidence"
            ).fetchone()[0],
            2,
        )

    def test_document_structure_replace_archive_reactivate_and_repeat_zero_dml(self):
        first_url = (
            "https://jira.example.test/secure/RapidBoard.jspa?"
            "rapidView=37746&projectKey=JPDI"
        )
        document_id = self._document("structure-lifecycle.md", first_url)

        first = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(first["structure_references"], {"new": 1, "reused": 0})
        self.assertEqual(
            first["structure_evidence"],
            {"new": 1, "reused": 0, "removed": 0},
        )
        reference_id = int(
            self.connection.execute(
                "SELECT id FROM atlassian_structure_references"
            ).fetchone()[0]
        )
        before_repeat = self.connection.total_changes
        repeated = sync_atlassian_local_evidence(self.connection)
        self.assertEqual(self.connection.total_changes, before_repeat)
        self.assertEqual(
            repeated["structure_references"], {"new": 0, "reused": 1}
        )
        self.assertEqual(
            repeated["structure_evidence"],
            {"new": 0, "reused": 1, "removed": 0},
        )

        empty_body = "No retained Atlassian locator\n"
        self.connection.execute(
            """
            UPDATE context_documents
            SET body = ?, size_bytes = ?, mtime_ns = mtime_ns + 1,
                content_hash = ?
            WHERE id = ?
            """,
            (
                empty_body,
                len(empty_body.encode("utf-8")),
                hashlib.sha256(empty_body.encode("utf-8")).hexdigest(),
                document_id,
            ),
        )
        removed = sync_atlassian_local_evidence(self.connection)
        self.assertEqual(
            removed["structure_evidence"],
            {"new": 0, "reused": 0, "removed": 1},
        )
        self.assertEqual(browse_inventory(self.connection)["references"], [])
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM search_index
                WHERE entity_type = 'atlassian_structure_reference'
                  AND entity_id = ?
                """,
                (str(reference_id),),
            ).fetchone()[0],
            0,
        )

        alias_url = (
            "https://jira.example.test/jira/software/projects/JPDI/"
            "boards/37746"
        )
        self.connection.execute(
            """
            UPDATE context_documents
            SET body = ?, size_bytes = ?, mtime_ns = mtime_ns + 1,
                content_hash = ?
            WHERE id = ?
            """,
            (
                alias_url,
                len(alias_url.encode("utf-8")),
                hashlib.sha256(alias_url.encode("utf-8")).hexdigest(),
                document_id,
            ),
        )
        reactivated = sync_atlassian_local_evidence(self.connection)
        self.assertEqual(
            reactivated["structure_references"], {"new": 0, "reused": 1}
        )
        self.assertEqual(
            reactivated["structure_evidence"],
            {"new": 1, "reused": 0, "removed": 0},
        )
        self.assertEqual(
            [int(row[0]) for row in self.connection.execute(
                "SELECT id FROM atlassian_structure_references"
            ).fetchall()],
            [reference_id],
        )
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM atlassian_structure_reference_urls
                WHERE reference_id = ?
                """,
                (reference_id,),
            ).fetchone()[0],
            2,
        )
        self.assertEqual(
            browse_inventory(self.connection)["references"][0]["lifecycle"],
            "active",
        )

        self.connection.execute(
            "UPDATE context_roots SET enabled = 0 WHERE id = ?",
            (self.root_id,),
        )
        unavailable = browse_inventory(self.connection)["references"][0]
        self.assertEqual(unavailable["availability"], "unavailable")

    def test_structure_identity_collision_fails_one_source_without_reassignment(self):
        owner_url = "https://jira.example.test/projects/OWNER"
        collision_url = "https://jira.example.test/projects/COLLIDE"
        document_id = self._document("owner.md", owner_url)
        sync_atlassian_local_evidence(self.connection)
        owner_id = int(
            self.connection.execute(
                "SELECT id FROM atlassian_structure_references"
            ).fetchone()[0]
        )
        self.connection.execute(
            """
            INSERT INTO atlassian_structure_reference_urls(
                reference_id, site_id, url_role, safe_locator_url,
                first_observed_at, last_observed_at
            ) VALUES (?, ?, 'alias', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (owner_id, self.site["id"], collision_url),
        )
        self.connection.execute(
            """
            UPDATE context_documents
            SET body = ?, size_bytes = ?, mtime_ns = mtime_ns + 1,
                content_hash = ?
            WHERE id = ?
            """,
            (
                collision_url,
                len(collision_url),
                hashlib.sha256(collision_url.encode("utf-8")).hexdigest(),
                document_id,
            ),
        )

        report = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["sources"]["failed"], 1)
        self.assertEqual(
            report["source_outcomes"][0]["reason_codes"],
            ["identity-collision"],
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_structure_references"
            ).fetchone()[0],
            1,
        )
        self.assertEqual(
            self.connection.execute(
                """
                SELECT reference_id FROM atlassian_structure_reference_urls
                WHERE safe_locator_url = ?
                """,
                (collision_url,),
            ).fetchone()[0],
            owner_id,
        )

    def test_safe_locator_drops_arbitrary_query_without_losing_document_provenance(self):
        url = "https://jira.example.test/browse/UNICODE-1?q={}".format(
            "한" * 900
        )
        self.assertLessEqual(len(url), 8_000)
        self.assertGreater(
            len(normalize_atlassian_url(url).normalized_url), 8_000
        )
        session_id = self._session("expanded-url")
        self._reference_scan(session_id)
        safe_url = "https://jira.example.test/browse/UNICODE-1"
        self._reference(session_id, safe_url)
        document_id = self._document("expanded-url.md", url + "\n")

        report = sync_atlassian_local_evidence(self.connection)

        self._assert_reason_vocabulary(report)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["sources"]["failed"], 0)
        self.assertEqual(report["candidate_skips"]["unsafe_url"], 0)
        self.assertEqual(report["items"], {"new": 1, "reused": 0})
        self.assertEqual(
            report["evidence"], {"new": 2, "reused": 0, "removed": 0}
        )
        rows = self.connection.execute(
            """
            SELECT session_id, document_id, observed_url, normalized_url
            FROM atlassian_item_evidence
            WHERE session_id = ? OR document_id = ?
            ORDER BY session_id IS NULL, id
            """,
            (session_id, document_id),
        ).fetchall()
        self.assertEqual(rows[0]["observed_url"], safe_url)
        self.assertEqual(rows[0]["normalized_url"], safe_url)
        self.assertEqual(rows[1]["observed_url"], url)
        self.assertEqual(rows[1]["normalized_url"], safe_url)

    def test_source_snapshot_batches_do_not_cap_later_ids(self):
        for index in range(205):
            self._session(
                "excluded-{}".format(index),
                session_class="maintenance",
                index_policy="metadata_only",
            )
        from localbrain import atlassian_evidence_sync as sync_module

        original_batches = sync_module._source_id_batches
        batch_sizes = []

        def observe_batches(source_ids):
            for batch in original_batches(source_ids):
                batch_sizes.append(len(batch))
                yield batch

        statements = []
        self.connection.set_trace_callback(statements.append)
        with patch.object(
            sync_module,
            "_source_id_batches",
            side_effect=observe_batches,
        ):
            report = sync_atlassian_local_evidence(self.connection)

        self.connection.set_trace_callback(None)
        self.assertEqual(report["sources"]["considered"], 205)
        self.assertEqual(report["sources"]["excluded"], 205)
        self.assertEqual(len(report["source_outcomes"]), 205)
        self.assertEqual(
            [outcome["local_id"] for outcome in report["source_outcomes"]],
            sorted(outcome["local_id"] for outcome in report["source_outcomes"]),
        )
        session_snapshots = [
            statement
            for statement in statements
            if "SELECT id FROM sessions WHERE id > 0 AND id <=" in statement
        ]
        self.assertEqual(len(session_snapshots), 1)
        self.assertEqual(batch_sizes, [100, 100, 5])

    def test_start_snapshot_retains_deleted_later_source_and_excludes_insert(self):
        document_ids = [
            self._document(
                "snapshot-{}.md".format(index),
                "No Atlassian URL\n",
            )
            for index in range(1, 102)
        ]
        from localbrain import atlassian_evidence_sync as sync_module

        original = sync_module._process_document
        inserted_ids = []

        def mutate_after_first_batch(
            connection,
            document_id,
            registry,
            site_fingerprint,
        ):
            result = original(
                connection,
                document_id,
                registry,
                site_fingerprint,
            )
            if document_id == document_ids[99]:
                inserted_ids.append(
                    self._document(
                        "inserted-after-start.md",
                        "No Atlassian URL\n",
                    )
                )
                connection.execute(
                    "DELETE FROM context_documents WHERE id = ?",
                    (document_ids[100],),
                )
            return result

        with patch.object(
            sync_module,
            "_process_document",
            side_effect=mutate_after_first_batch,
        ):
            report = sync_atlassian_local_evidence(self.connection)

        self._assert_reason_vocabulary(report)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(
            report["sources"],
            {
                "considered": 101,
                "eligible": 101,
                "scanned": 100,
                "partial": 0,
                "unavailable": 1,
                "failed": 0,
                "excluded": 0,
            },
        )
        outcomes = {
            (row["kind"], row["local_id"]): row
            for row in report["source_outcomes"]
        }
        deleted = outcomes[("document", document_ids[100])]
        self.assertEqual(deleted["outcome"], "unavailable")
        self.assertEqual(deleted["reason_codes"], ["context-unavailable"])
        self.assertEqual(len(inserted_ids), 1)
        self.assertGreater(inserted_ids[0], document_ids[100])
        self.assertNotIn(("document", inserted_ids[0]), outcomes)

    def test_document_scan_is_chunked_caps_first_500_and_advances_scan(self):
        lines = [
            "{} https://jira.example.test/browse/DOC-{}".format(
                "한" * 70, index
            )
            for index in range(1, 502)
        ]
        body = "\n".join(lines)
        self.assertGreater(len(body.encode("utf-8")), 64 * 1024)
        document_id = self._document("large.md", body)
        statements = []
        self.connection.set_trace_callback(statements.append)

        report = sync_atlassian_local_evidence(self.connection)

        self._assert_reason_vocabulary(report)
        self.connection.set_trace_callback(None)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["items"], {"new": 500, "reused": 0})
        self.assertEqual(report["evidence"]["new"], 500)
        self.assertEqual(report["scope_limits"]["document_url_overflow"], 1)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_evidence WHERE document_id = ?",
                (document_id,),
            ).fetchone()[0],
            500,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT MAX(source_line) FROM atlassian_item_evidence WHERE document_id = ?",
                (document_id,),
            ).fetchone()[0],
            500,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT status FROM atlassian_evidence_scans WHERE document_id = ?",
                (document_id,),
            ).fetchone()[0],
            "ok",
        )
        selects = [
            statement.lower()
            for statement in statements
            if statement.lstrip().lower().startswith("select")
        ]
        body_reads = [
            statement
            for statement in selects
            if "body" in statement and "from context_documents" in statement
        ]
        self.assertTrue(body_reads)
        self.assertTrue(
            all("substr(cast(body as blob)" in statement for statement in body_reads)
        )
        repeat_statements = []
        self.connection.set_trace_callback(repeat_statements.append)
        repeat = sync_atlassian_local_evidence(self.connection)
        self.connection.set_trace_callback(None)
        self.assertEqual(repeat["items"], {"new": 0, "reused": 500})
        self.assertEqual(repeat["evidence"]["reused"], 500)
        writes = [
            statement
            for statement in repeat_statements
            if statement.lstrip().split(None, 1)[0].upper()
            in {"INSERT", "UPDATE", "DELETE", "REPLACE"}
        ]
        self.assertEqual(writes, [])

    def test_changed_document_refreshes_same_key_observation_then_repeat_is_read_only(self):
        first_url = (
            "HTTPS://JIRA.EXAMPLE.TEST/browse/OBS-1?second=2&first=1"
        )
        second_url = (
            "https://jira.example.test/browse/OBS-1?first=1&second=2"
        )
        document_id = self._document("observation.md", first_url + "\n")
        sync_atlassian_local_evidence(self.connection)
        initial_evidence = self.connection.execute(
            """
            SELECT id, external_resource_id, normalized_url
            FROM atlassian_item_evidence
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchone()
        evidence_id = int(initial_evidence["id"])
        external_resource_id = int(initial_evidence["external_resource_id"])
        item_url = self.connection.execute(
            """
            SELECT id, observed_url, first_observed_at, last_observed_at,
                   url_role
            FROM atlassian_item_urls
            WHERE external_resource_id = ? AND normalized_url = ?
            """,
            (external_resource_id, initial_evidence["normalized_url"]),
        ).fetchone()
        item_url_id = int(item_url["id"])
        stable_url_first_observed = str(item_url["first_observed_at"])
        stable_url_role = str(item_url["url_role"])
        stale_url_observed_at = "1997-01-01T00:00:00Z"
        self.connection.execute(
            """
            UPDATE atlassian_item_urls
            SET observed_url = ?, last_observed_at = ?
            WHERE id = ?
            """,
            (first_url, stale_url_observed_at, item_url_id),
        )
        item_snapshot = tuple(
            self.connection.execute(
                "SELECT * FROM atlassian_items WHERE external_resource_id = ?",
                (external_resource_id,),
            ).fetchone()
        )
        remote_state = self.connection.execute(
            """
            SELECT * FROM atlassian_item_remote_state
            WHERE external_resource_id = ?
            """,
            (external_resource_id,),
        ).fetchone()
        remote_state_snapshot = (
            tuple(remote_state) if remote_state is not None else None
        )
        stable_first_observed = "1998-01-01T00:00:00Z"
        self.connection.execute(
            """
            UPDATE atlassian_item_evidence
            SET observed_remote_id = 'stale-observation',
                observed_at = '1999-01-01T00:00:00Z',
                extractor_version = 'stale-extractor.v0',
                first_observed_at = ?,
                last_observed_at = '2000-01-01T00:00:00Z',
                updated_at = '2000-01-01T00:00:00Z'
            WHERE id = ?
            """,
            (stable_first_observed, evidence_id),
        )
        encoded = (second_url + "\n").encode("utf-8")
        self.connection.execute(
            """
            UPDATE context_documents
            SET body = ?, size_bytes = ?, content_hash = ?
            WHERE id = ?
            """,
            (
                second_url + "\n",
                len(encoded),
                hashlib.sha256(encoded).hexdigest(),
                document_id,
            ),
        )

        refreshed_at = "2026-08-29T12:34:56Z"
        with patch(
            "localbrain.atlassian_evidence_sync.utc_now",
            return_value=refreshed_at,
        ):
            changed = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(changed["evidence"]["reused"], 1)
        refreshed = self.connection.execute(
            """
            SELECT id, observed_url, observed_remote_id, observed_at,
                   extractor_version, first_observed_at,
                   last_observed_at, updated_at
            FROM atlassian_item_evidence
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchone()
        self.assertEqual(refreshed["id"], evidence_id)
        self.assertEqual(refreshed["observed_url"], second_url)
        self.assertIsNone(refreshed["observed_remote_id"])
        self.assertIsNone(refreshed["observed_at"])
        self.assertEqual(
            refreshed["extractor_version"], EVIDENCE_EXTRACTOR_VERSION
        )
        self.assertEqual(refreshed["first_observed_at"], stable_first_observed)
        self.assertEqual(refreshed["last_observed_at"], refreshed_at)
        self.assertEqual(refreshed["last_observed_at"], refreshed["updated_at"])
        refreshed_item_url = self.connection.execute(
            """
            SELECT id, external_resource_id, observed_url, first_observed_at,
                   last_observed_at, url_role
            FROM atlassian_item_urls
            WHERE id = ?
            """,
            (item_url_id,),
        ).fetchone()
        self.assertEqual(
            refreshed_item_url["external_resource_id"], external_resource_id
        )
        self.assertEqual(refreshed_item_url["observed_url"], second_url)
        self.assertEqual(
            refreshed_item_url["first_observed_at"],
            stable_url_first_observed,
        )
        self.assertEqual(refreshed_item_url["last_observed_at"], refreshed_at)
        self.assertEqual(refreshed_item_url["url_role"], stable_url_role)
        self.assertEqual(
            tuple(
                self.connection.execute(
                    "SELECT * FROM atlassian_items WHERE external_resource_id = ?",
                    (external_resource_id,),
                ).fetchone()
            ),
            item_snapshot,
        )
        remote_state = self.connection.execute(
            """
            SELECT * FROM atlassian_item_remote_state
            WHERE external_resource_id = ?
            """,
            (external_resource_id,),
        ).fetchone()
        self.assertEqual(
            tuple(remote_state) if remote_state is not None else None,
            remote_state_snapshot,
        )
        snapshot = tuple(refreshed)
        item_url_snapshot = tuple(refreshed_item_url)
        statements = []
        self.connection.set_trace_callback(statements.append)

        with patch(
            "localbrain.atlassian_evidence_sync.utc_now",
            return_value="2026-08-29T13:34:56Z",
        ):
            repeat = sync_atlassian_local_evidence(self.connection)

        self.connection.set_trace_callback(None)
        self.assertEqual(repeat["evidence"]["reused"], 1)
        self.assertEqual(
            tuple(
                self.connection.execute(
                    """
                    SELECT id, observed_url, observed_remote_id, observed_at,
                           extractor_version, first_observed_at,
                           last_observed_at, updated_at
                    FROM atlassian_item_evidence
                    WHERE document_id = ?
                    """,
                    (document_id,),
                ).fetchone()
            ),
            snapshot,
        )
        self.assertEqual(
            tuple(
                self.connection.execute(
                    """
                    SELECT id, external_resource_id, observed_url,
                           first_observed_at, last_observed_at, url_role
                    FROM atlassian_item_urls
                    WHERE id = ?
                    """,
                    (item_url_id,),
                ).fetchone()
            ),
            item_url_snapshot,
        )
        writes = [
            statement
            for statement in statements
            if statement.lstrip().split(None, 1)[0].upper()
            in {"INSERT", "UPDATE", "DELETE", "REPLACE"}
        ]
        self.assertEqual(writes, [])

    def test_document_lifecycle_and_source_failure_preserve_prior_evidence(self):
        retained_id = self._document(
            "retained.md", "https://jira.example.test/browse/KEEP-1\n"
        )
        peer_id = self._document(
            "peer.md", "https://jira.example.test/browse/PEER-1\n"
        )
        sync_atlassian_local_evidence(self.connection)
        self.connection.execute(
            "UPDATE context_roots SET enabled = 0 WHERE id = ?",
            (self.root_id,),
        )
        disabled = sync_atlassian_local_evidence(self.connection)
        self.assertEqual(disabled["sources"]["excluded"], 2)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_evidence"
            ).fetchone()[0],
            2,
        )
        self.connection.execute(
            "UPDATE context_roots SET enabled = 1, readable = 0 WHERE id = ?",
            (self.root_id,),
        )
        unavailable = sync_atlassian_local_evidence(self.connection)
        self.assertEqual(unavailable["status"], "partial")
        self.assertEqual(unavailable["sources"]["unavailable"], 2)

        self.connection.execute(
            "UPDATE context_roots SET readable = 1, status = 'ready' WHERE id = ?",
            (self.root_id,),
        )
        peer_body = "https://jira.example.test/browse/PEER-2\n"
        self.connection.execute(
            """
            UPDATE context_documents
            SET body = ?, size_bytes = ?, content_hash = ?
            WHERE id = ?
            """,
            (
                peer_body,
                len(peer_body.encode()),
                hashlib.sha256(peer_body.encode()).hexdigest(),
                peer_id,
            ),
        )

        from localbrain import atlassian_evidence_sync as sync_module

        original = sync_module._read_document_scan

        def fail_one(connection, document_id):
            if document_id == retained_id:
                raise RuntimeError("synthetic private error")
            return original(connection, document_id)

        with patch.object(sync_module, "_read_document_scan", side_effect=fail_one):
            isolated = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(isolated["status"], "partial")
        self.assertEqual(isolated["sources"]["failed"], 1)
        self.assertEqual(isolated["sources"]["scanned"], 1)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_evidence WHERE document_id = ?",
                (retained_id,),
            ).fetchone()[0],
            1,
        )
        peer_url = self.connection.execute(
            """
            SELECT normalized_url FROM atlassian_item_evidence
            WHERE document_id = ?
            """,
            (peer_id,),
        ).fetchone()[0]
        self.assertTrue(peer_url.endswith("/browse/PEER-2"))
        self.assertNotIn("synthetic private error", json.dumps(isolated))

    def test_nonblocking_single_flight_returns_busy_without_writes(self):
        before = self.connection.total_changes
        self.assertTrue(_SYNC_LOCK.acquire(blocking=False))
        try:
            report = sync_atlassian_local_evidence(self.connection)
            self._assert_reason_vocabulary(report)
        finally:
            _SYNC_LOCK.release()
        self.assertEqual(report["status"], "busy")
        self.assertEqual(report["sources"]["considered"], 0)
        self.assertEqual(self.connection.total_changes, before)

    def test_zero_and_all_failed_statuses_are_distinct(self):
        before = self.connection.total_changes
        zero = sync_atlassian_local_evidence(self.connection)
        self.assertEqual(zero["status"], "complete")
        self.assertEqual(zero["sources"]["considered"], 0)
        self.assertEqual(self.connection.total_changes, before)

        document_id = self._document(
            "failed.md", "https://jira.example.test/browse/FAIL-1\n"
        )
        with patch(
            "localbrain.atlassian_evidence_sync._read_document_scan",
            side_effect=RuntimeError("synthetic bounded failure"),
        ):
            failed = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(failed["status"], "failed")
        self.assertEqual(
            failed["sources"],
            {
                "considered": 1,
                "eligible": 1,
                "scanned": 0,
                "partial": 0,
                "unavailable": 0,
                "failed": 1,
                "excluded": 0,
            },
        )
        self.assertEqual(
            failed["source_outcomes"],
            [
                {
                    "kind": "document",
                    "local_id": document_id,
                    "outcome": "failed",
                    "counts": {
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
                    },
                    "reason_codes": ["reconciliation-error"],
                }
            ],
        )

    def test_same_line_session_ordinals_remain_distinct_locations(self):
        session_id = self._session("same-line")
        self._reference_scan(session_id, observed=1, retained=1)
        url = "https://jira.example.test/browse/SAME-1"
        self._reference(session_id, url, line=8, ordinal=1)
        self._reference(session_id, url, line=8, ordinal=2)

        report = sync_atlassian_local_evidence(self.connection)

        self.assertEqual(report["evidence"]["new"], 2)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(DISTINCT url_ordinal) FROM atlassian_item_evidence"
            ).fetchone()[0],
            2,
        )

    def test_frozen_binding_choice_attaches_only_one_compatible_source(self):
        existing = create_or_reuse_atlassian_stub(
            self.connection,
            service="jira",
            site_id=self.site["id"],
            url="https://jira.example.test/browse/EXIST-1",
        )
        zero_site = register_atlassian_site(
            self.connection, base_url="https://zero.example.test"
        )
        self.connection.execute(
            """
            INSERT INTO atlassian_spaces(
                site_id, service, remote_id, name, canonical_url, coverage
            ) VALUES (?, 'jira', 'zero-space', 'Zero',
                      'https://zero.example.test/projects/ZERO',
                      'selected-content')
            """,
            (zero_site["id"],),
        )
        multi_source_id = int(
            self.connection.execute(
                """
                INSERT INTO external_source_instances(
                    instance_key, provider_kind, service, display_name
                ) VALUES ('multi-one', 'mcp_gateway', 'jira', 'Multi one')
                """
            ).lastrowid
        )
        multi_site = register_atlassian_site(
            self.connection,
            source_instance_id=multi_source_id,
            base_url="https://multi.example.test",
        )
        second_multi_source_id = int(
            self.connection.execute(
                """
                INSERT INTO external_source_instances(
                    instance_key, provider_kind, service, display_name
                ) VALUES ('multi-two', 'mcp_gateway', 'jira', 'Multi two')
                """
            ).lastrowid
        )
        self.connection.execute(
            """
            INSERT INTO atlassian_site_bindings(site_id, source_instance_id)
            VALUES (?, ?)
            """,
            (multi_site["id"], second_multi_source_id),
        )
        self._document(
            "bindings.md",
            "https://jira.example.test/browse/EXIST-1\n"
            "https://jira.example.test/browse/NEW-1\n"
            "https://zero.example.test/browse/ZERO-1\n"
            "https://multi.example.test/browse/MULTI-1\n",
        )

        from localbrain import atlassian_evidence_sync as sync_module

        original_snapshot = sync_module.configured_atlassian_sync_scope_snapshot

        def disable_after_snapshot(connection):
            snapshot = original_snapshot(connection)
            connection.execute(
                "UPDATE external_source_instances SET enabled = 0 WHERE id = ?",
                (self.jira_instance_id,),
            )
            return snapshot

        with patch.object(
            sync_module,
            "configured_atlassian_sync_scope_snapshot",
            side_effect=disable_after_snapshot,
        ):
            sync_atlassian_local_evidence(self.connection)

        rows = {
            row["normalized_domain"] + row["normalized_url"].split("/browse")[1]: row[
                "source_instance_id"
            ]
            for row in self.connection.execute(
                """
                SELECT atlassian_sites.normalized_domain,
                       atlassian_item_urls.normalized_url,
                       atlassian_items.source_instance_id
                FROM atlassian_items
                JOIN atlassian_sites
                  ON atlassian_sites.id = atlassian_items.site_id
                JOIN atlassian_item_urls
                  ON atlassian_item_urls.external_resource_id =
                     atlassian_items.external_resource_id
                WHERE atlassian_item_urls.url_role = 'canonical'
                """
            )
        }
        self.assertIsNone(rows["jira.example.test/EXIST-1"])
        self.assertEqual(
            rows["jira.example.test/NEW-1"], self.jira_instance_id
        )
        self.assertIsNone(rows["zero.example.test/ZERO-1"])
        self.assertIsNone(rows["multi.example.test/MULTI-1"])
        self.assertEqual(existing["source_instance_id"], None)

    def test_committed_peer_survives_later_action_fatal(self):
        session_id = self._session("commit-peer")
        self._reference_scan(session_id)
        self._reference(
            session_id, "https://jira.example.test/browse/COMMIT-1"
        )
        self._document("later.md", "No URL\n")
        from localbrain import atlassian_evidence_sync as sync_module

        original = sync_module._source_id_batches
        batch_calls = 0

        def fail_after_sessions(source_ids):
            nonlocal batch_calls
            batch_calls += 1
            if batch_calls == 2:
                raise RuntimeError("synthetic later fatal")
            return original(source_ids)

        statements = []
        self.connection.set_trace_callback(statements.append)
        with patch.object(
            sync_module,
            "_source_id_batches",
            side_effect=fail_after_sessions,
        ):
            report = sync_atlassian_local_evidence(self.connection)
        self.connection.set_trace_callback(None)
        self.connection.rollback()

        self.assertEqual(report["status"], "failed")
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_evidence"
            ).fetchone()[0],
            1,
        )
        self.assertTrue(
            any(statement.strip().upper() == "COMMIT" for statement in statements)
        )


if __name__ == "__main__":
    unittest.main()
