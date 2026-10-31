import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.resources.catalog import bind_external_link
from localbrain.references.urls import parse_url
from localbrain.ingest.sync import sessions
from localbrain.ingest.contracts import ParsedReferenceCandidate
from localbrain.ingest.evidence.reference_candidates import REFERENCE_EXTRACTOR_VERSION
from localbrain.sessions import references as session_references
from localbrain.ingest import scanner
from localbrain.sessions.references import (
    SessionReferenceError,
    SessionReferenceLookupCache,
    finalize_session_references,
    reconcile_session_references,
    session_reference_projection,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = (ROOT / "src/localbrain/schema.sql").read_text(encoding="utf-8")


class SessionReferenceTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_SQL)
        self.connection.executescript(
            """
            INSERT INTO sources(id, provider_kind, name, root_path) VALUES (1, 'codex', 'Codex', '/sessions'), (2, 'context', 'Context', '/workspace');

            INSERT INTO workspaces(id, canonical_path, display_name, exists_now)
            VALUES (1, '/workspace', 'workspace', 1);

            INSERT INTO context_roots(id, path, label)
            VALUES (1, '/workspace', 'Workspace');

            INSERT INTO sessions(
                id, source_id, workspace_id, external_id, source_path,
                cwd_raw, title
            ) VALUES (
                10, 1, 1, 'session-10', '/sessions/a.jsonl',
                '/workspace', 'Synthetic session'
            );

            INSERT INTO context_documents(
                id, source_id, context_root_id, workspace_id, path,
                relative_path, title, body, size_bytes, mtime_ns, content_hash
            ) VALUES
                (20, 2, 1, 1, '/workspace/docs/guide.md',
                 'docs/guide.md', 'Guide', '', 0, 1, 'guide-hash'),
                (21, 2, 1, 1, '/workspace/README.md',
                 'README.md', 'Readme', '', 0, 1, 'readme-hash'),
                (22, 2, 1, 1, '/workspace/one/notes.md',
                 'one/notes.md', 'Notes one', '', 0, 1, 'notes-one-hash'),
                (23, 2, 1, 1, '/workspace/two/notes.md',
                 'two/notes.md', 'Notes two', '', 0, 1, 'notes-two-hash');

            INSERT INTO atlassian_sites(
                id, normalized_domain, display_name, canonical_base_url
            ) VALUES (
                30, 'jira.example.test', 'Synthetic Jira',
                'https://jira.example.test'
            );
            INSERT INTO external_resources(id, resource_type, title, url)
            VALUES (
                40, 'jira_issue', 'SYN-62',
                'https://jira.example.test/browse/SYN-62'
            );
            INSERT INTO atlassian_items(
                external_resource_id, site_id, service, item_type, remote_key
            ) VALUES (40, 30, 'jira', 'jira_issue', 'SYN-62');
            INSERT INTO atlassian_item_urls(
                external_resource_id, site_id, url_role, observed_url,
                normalized_url
            ) VALUES (
                40, 30, 'canonical',
                'https://jira.example.test/browse/SYN-62',
                'https://jira.example.test/browse/SYN-62'
            );
            """
        )

        bind_external_link(self.connection, 40)

    def tearDown(self):
        self.connection.close()

    def _candidate(
        self,
        reference,
        *,
        reference_kind="url",
        evidence_kind="user_mention",
        line=1,
        ordinal=1,
        event="event-1",
        outcome=None,
        tool_name=None,
        call_id=None,
    ):
        return ParsedReferenceCandidate(
            reference_kind=reference_kind,
            reference=reference,
            evidence_kind=evidence_kind,
            source_line=line,
            evidence_ordinal=ordinal,
            source_event_id=event,
            tool_name=tool_name,
            tool_call_id=call_id,
            read_outcome=outcome,
        )

    def _reconcile(
        self, candidates, path="/sessions/a.jsonl", finalize=True,
    ):
        return reconcile_session_references(
            self.connection,
            session_id=10,
            source_path=path,
            source_size_bytes=100,
            source_mtime_ns=200,
            candidates=candidates,
            finalize=finalize,
        )

    def _evidence(self):
        return self.connection.execute("""
            SELECT e.*, r.kind AS target_kind, r.product,
                   d.document_id AS context_document_id
            FROM session_reference_evidence e
            JOIN reference_resources r ON r.id = e.resource_id
            LEFT JOIN resource_documents d ON d.resource_id = r.id
            ORDER BY e.source_line, e.id
        """).fetchall()

    def test_url_resolution_needs_no_database_tables(self):
        values = (
            "https://example.test/browse/SYN-62?theme=dark",
            "https://example.test/issues/SYN-62#comment",
            "https://example.test/wiki/pages/viewpage.action?pageId=123&view=full",
            "https://example.test/wiki/spaces/TEAM/pages/123/title",
            "https://example.test/other?q=discarded",
        )
        parsed = [parse_url(value) for value in values]
        self.assertTrue(all(parsed))
        self.assertEqual(parsed[0].target_key, parsed[1].target_key)
        self.assertEqual(parsed[2].target_key, parsed[3].target_key)
        self.assertEqual(parsed[4].normalized_url, "https://example.test/other")

    def test_registration_removal_keeps_reference_identity_and_evidence(self):
        candidates = [self._candidate("https://jira.example.test/browse/SYN-62")]
        self._reconcile(candidates)
        before = dict(self._evidence()[0])
        self.connection.execute("DELETE FROM atlassian_items")
        self.connection.execute("DELETE FROM atlassian_sites")
        self._reconcile(candidates)
        after = dict(self._evidence()[0])
        self.assertEqual(after["resource_id"], before["resource_id"])
        self.assertEqual(after["target_key"], before["target_key"])
        self.assertEqual(after["observed_identity"], before["observed_identity"])
        self.assertEqual(after["product"], "jira")

    def test_unsafe_urls_are_rejected_and_markdown_reuses_the_document(self):
        self._reconcile([
            self._candidate("https://" + "account:value" + "@example.test/browse/SYN-62"),
            self._candidate("/workspace/docs/guide.md", reference_kind="markdown", line=2),
        ])
        rows = self._evidence()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["context_document_id"], 20)

    def test_catalog_failure_uses_caller_savepoint_and_preserves_prior_evidence(self):
        candidates = [self._candidate("https://jira.example.test/browse/SYN-62")]
        self._reconcile(candidates)
        prior = [tuple(row) for row in self.connection.execute(
            "SELECT * FROM session_reference_evidence ORDER BY id"
        )]
        self.connection.commit()
        self.connection.execute("UPDATE sessions SET title = 'Caller pending change' WHERE id = 10")

        def failing_resolver(connection, parsed):
            self.assertIs(connection, self.connection)
            connection.execute("UPDATE sessions SET title = 'Adapter change' WHERE id = 10")
            raise RuntimeError("synthetic resolver failure")

        with patch.object(session_references, "parsed_url_resource", failing_resolver), self.assertRaisesRegex(SessionReferenceError, "synthetic resolver failure") as raised:
            self._reconcile(candidates)
        self.assertIsInstance(raised.exception.__cause__, RuntimeError)
        self.assertTrue(self.connection.in_transaction)
        self.assertEqual(self.connection.execute(
            "SELECT title FROM sessions WHERE id = 10"
        ).fetchone()[0], "Caller pending change")
        self.assertEqual([tuple(row) for row in self.connection.execute(
            "SELECT * FROM session_reference_evidence ORDER BY id"
        )], prior)
        scan = self.connection.execute("SELECT * FROM session_reference_scans").fetchone()
        self.assertEqual(scan["status"], "error")
        self.assertEqual(scan["error_code"], "reference-reconciliation-error")

    def test_core_ingestion_classifies_urls_without_optional_registration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "registered-links.jsonl"
            source.write_text("\n".join(json.dumps(record) for record in (
                {"type": "session_meta", "payload": {"id": "registered-links", "cwd": "/workspace"}},
                {"type": "event_msg", "payload": {
                    "type": "user_message", "message": " ".join((
                        "https://jira.example.test/browse/SYN-62",
                        "https://jira.example.test/browse/SYN-63",
                        "https://unregistered.example.test/wiki/pages/viewpage.action?pageId=123",
                    )),
                }},
            )) + "\n", encoding="utf-8")
            self.connection.execute("DELETE FROM sessions")
            self.connection.execute("UPDATE sources SET root_path = ? WHERE id = 1", (str(root),))
            report = sessions._scan_session_source(
                self.connection, 1, "Synthetic Codex", root,
                scanner.parse_codex_session, scanner.CODEX_USAGE_CONTRACT_VERSION,
                provider_kind="codex",
            )
            self.assertEqual(report, (1, 0, 0))
            rows = self._evidence()
            self.assertEqual([row["target_kind"] for row in rows], ["url", "url", "url"])
            self.assertEqual([row["product"] for row in rows], ["jira", "jira", "confluence"])
            self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM atlassian_items").fetchone()[0], 1)
            self.assertEqual(rows[2]["normalized_url"], "https://unregistered.example.test/wiki/pages/viewpage.action?pageId=123")

    def test_safe_url_and_exact_markdown_resolution(self):
        candidates = [
            self._candidate(
                "https://Example.Test:443/path?q=sample#fragment",
                line=1,
                ordinal=1,
            ),
            self._candidate(
                "https://" + "account:value" + "@example.test/path",
                line=2,
                ordinal=1,
                event="event-2",
            ),
            self._candidate(
                "/workspace/docs/guide.md",
                reference_kind="markdown",
                line=3,
                event="event-3",
            ),
            self._candidate(
                "docs/guide.md",
                reference_kind="markdown",
                line=4,
                event="event-4",
            ),
            self._candidate(
                "README.md",
                reference_kind="markdown",
                line=5,
                event="event-5",
            ),
            self._candidate(
                "notes.md",
                reference_kind="markdown",
                line=6,
                event="event-6",
            ),
            self._candidate(
                "missing.md",
                reference_kind="markdown",
                line=7,
                event="event-7",
            ),
        ]

        self._reconcile(candidates)
        rows = self._evidence()

        self.assertEqual(len(rows), 4)
        self.assertEqual(
            {row["context_document_id"] for row in rows if row["target_kind"] == "path"},
            {20, 21},
        )
        self.assertEqual(
            [row["normalized_url"] for row in rows if row["target_kind"] == "url"],
            ["https://example.test/path"],
        )

    def test_read_outcome_projection_prefers_success_and_counts_calls(self):
        target = "https://jira.example.test/browse/SYN-62?opaque=discarded"
        candidates = [
            self._candidate(target, line=1),
            self._candidate(
                "SYN-62",
                reference_kind="jira_key",
                evidence_kind="resource_read",
                outcome="failure",
                tool_name="jira__searchIssuesByJql",
                call_id="call-failed",
                line=2,
                event="result-failed",
            ),
            self._candidate(
                target,
                evidence_kind="tool_result",
                tool_name="jira__searchIssuesByJql",
                call_id="call-success",
                line=3,
                event="result-success",
            ),
            self._candidate(
                "SYN-62",
                reference_kind="jira_key",
                evidence_kind="resource_read",
                outcome="success",
                tool_name="jira__searchIssuesByJql",
                call_id="call-success",
                line=3,
                event="result-success",
            ),
        ]

        self._reconcile(candidates)
        projection = session_reference_projection(self.connection, 10)

        self.assertEqual(projection["retained_total"], 1)
        item = projection["items"][0]
        self.assertEqual(item["target_kind"], "url")
        self.assertEqual(item["destination"], "https://jira.example.test/browse/SYN-62")
        self.assertEqual(
            item["evidence"],
            [
                {"kind": "resource_read", "outcome": "success", "count": 1},
                {"kind": "tool_result", "outcome": None, "count": 1},
                {"kind": "user_mention", "outcome": None, "count": 1},
            ],
        )

    def test_semantic_atlassian_locator_projection_groups_safe_variants(self):
        candidates = [
            self._candidate(
                "https://jirap.example.test/secure/RapidBoard.jspa"
                "?projectKey=JPDI&rapidView=37746&layout=compact",
                line=1,
                ordinal=1,
            ),
            self._candidate(
                "https://jirap.example.test/secure/RapidBoard.jspa"
                "?rapidView=37746&projectKey=OTHER&theme=wide",
                line=2,
                ordinal=1,
                event="event-2",
            ),
        ]

        before = {
            table: self.connection.execute(
                "SELECT COUNT(*) FROM {}".format(table)
            ).fetchone()[0]
            for table in (
                "atlassian_sites",
                "atlassian_spaces",
                "atlassian_items",
                "atlassian_item_urls",
            )
        }
        self._reconcile(candidates)
        rows = self._evidence()

        expected_key = (
            "url:a42aa269be59f4c54139e2dfb761c018ec228978aa1ecbd0428e2065b7b6d9b5"
        )
        self.assertEqual({row["target_key"] for row in rows}, {expected_key})
        self.assertEqual({row["target_kind"] for row in rows}, {"url"})
        self.assertEqual(
            [row["normalized_url"] for row in rows],
            [
                "https://jirap.example.test/secure/RapidBoard.jspa"
                "?rapidView=37746&projectKey=JPDI",
                "https://jirap.example.test/secure/RapidBoard.jspa"
                "?rapidView=37746&projectKey=OTHER",
            ],
        )
        self.assertEqual(
            session_reference_projection(self.connection, 10)["retained_total"],
            1,
        )
        self.assertEqual(
            {
                table: self.connection.execute(
                    "SELECT COUNT(*) FROM {}".format(table)
                ).fetchone()[0]
                for table in before
            },
            before,
        )

    def test_unconfigured_item_aliases_group_without_atlassian_dml(self):
        self._reconcile(
            [
                self._candidate(
                    "https://new.example.test/issues/new-1?theme=compact",
                    line=1,
                ),
                self._candidate(
                    "https://new.example.test/browse/NEW-1",
                    line=2,
                    event="event-2",
                ),
            ]
        )
        rows = self._evidence()

        self.assertEqual(len({row["target_key"] for row in rows}), 1)
        self.assertEqual({row["target_kind"] for row in rows}, {"url"})
        self.assertEqual(
            {row["normalized_url"] for row in rows},
            {"https://new.example.test/browse/NEW-1"},
        )
        self.assertTrue(all(row["product"] == "jira" for row in rows))
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_items"
            ).fetchone()[0],
            1,
        )

    def test_configured_item_resolution_is_site_scoped_and_exact_url_first(self):
        self.connection.executescript(
            """
            UPDATE atlassian_items SET remote_key = NULL
            WHERE external_resource_id = 40;
            INSERT INTO external_resources(id, resource_type, title, url)
            VALUES (
                41, 'jira_issue', 'SYN-62 identity owner',
                'https://jira.example.test/browse/OTHER-1'
            );
            INSERT INTO atlassian_items(
                external_resource_id, site_id, service, item_type, remote_key
            ) VALUES (41, 30, 'jira', 'jira_issue', 'SYN-62');
            INSERT INTO atlassian_item_urls(
                external_resource_id, site_id, url_role, observed_url,
                normalized_url
            ) VALUES (
                41, 30, 'canonical',
                'https://jira.example.test/browse/OTHER-1',
                'https://jira.example.test/browse/OTHER-1'
            );
            INSERT INTO atlassian_sites(
                id, normalized_domain, display_name, canonical_base_url
            ) VALUES (
                31, 'other.example.test', 'Other Jira',
                'https://other.example.test'
            );
            INSERT INTO external_resources(id, resource_type, title, url)
            VALUES (
                42, 'jira_issue', 'SYN-62 other domain',
                'https://other.example.test/browse/SYN-62'
            );
            INSERT INTO atlassian_items(
                external_resource_id, site_id, service, item_type, remote_key
            ) VALUES (42, 31, 'jira', 'jira_issue', 'SYN-62');
            INSERT INTO atlassian_item_urls(
                external_resource_id, site_id, url_role, observed_url,
                normalized_url
            ) VALUES (
                42, 31, 'canonical',
                'https://other.example.test/browse/SYN-62',
                'https://other.example.test/browse/SYN-62'
            );
            """
        )
        self._reconcile(
            [
                self._candidate(
                    "https://jira.example.test/browse/SYN-62",
                    line=1,
                ),
                self._candidate(
                    "https://unconfigured.example.test/browse/SYN-62",
                    line=2,
                    event="event-2",
                ),
            ]
        )
        rows = self._evidence()

        self.assertEqual(
            [(row["source_line"], row["target_kind"], row["product"]) for row in rows],
            [(1, "url", "jira"), (2, "url", "jira")],
        )

    def test_configured_alias_does_not_override_url_identity(self):
        self.connection.executescript(
            """
            UPDATE external_resources
            SET url = 'https://jira.example.test/browse/SYN-62?view=compact'
            WHERE id = 40;
            UPDATE atlassian_items SET remote_key = NULL
            WHERE external_resource_id = 40;
            UPDATE atlassian_item_urls
            SET observed_url =
                    'https://jira.example.test/browse/SYN-62?view=compact',
                normalized_url =
                    'https://jira.example.test/browse/SYN-62?view=compact'
            WHERE external_resource_id = 40;

            INSERT INTO external_resources(id, resource_type, title, url)
            VALUES (
                41, 'jira_issue', 'SYN-62 semantic owner',
                'https://jira.example.test/browse/SYN-62'
            );
            INSERT INTO atlassian_items(
                external_resource_id, site_id, service, item_type, remote_key
            ) VALUES (41, 30, 'jira', 'jira_issue', 'SYN-62');
            INSERT INTO atlassian_item_urls(
                external_resource_id, site_id, url_role, observed_url,
                normalized_url
            ) VALUES (
                41, 30, 'canonical',
                'https://jira.example.test/browse/SYN-62',
                'https://jira.example.test/browse/SYN-62'
            );
            """
        )

        self._reconcile(
            [
                self._candidate(
                    "https://jira.example.test/browse/SYN-62?view=compact"
                )
            ]
        )
        row = self._evidence()[0]

        self.assertEqual(
            (row["target_kind"], row["product"], row["normalized_url"]),
            (
                "url",
                "jira",
                "https://jira.example.test/browse/SYN-62",
            ),
        )

    def test_configured_confluence_page_keeps_safe_identity_query(self):
        self.connection.executescript(
            """
            INSERT INTO atlassian_sites(
                id, normalized_domain, display_name, canonical_base_url
            ) VALUES (
                31, 'wiki.example.test', 'Synthetic Wiki',
                'https://wiki.example.test'
            );
            INSERT INTO external_resources(id, resource_type, title, url)
            VALUES (
                41, 'confluence_page', 'Synthetic Page',
                'https://wiki.example.test/wiki/pages/viewpage.action?pageId=123'
            );
            INSERT INTO atlassian_items(
                external_resource_id, site_id, service, item_type, remote_id
            ) VALUES (41, 31, 'confluence', 'confluence_page', '123');
            INSERT INTO atlassian_item_urls(
                external_resource_id, site_id, url_role, observed_url,
                normalized_url
            ) VALUES (
                41, 31, 'canonical',
                'https://wiki.example.test/wiki/pages/viewpage.action?pageId=123',
                'https://wiki.example.test/wiki/pages/viewpage.action?pageId=123'
            );
            """
        )

        self._reconcile(
            [
                self._candidate(
                    "https://wiki.example.test/wiki/pages/viewpage.action?pageId=123"
                )
            ]
        )
        row = self._evidence()[0]

        self.assertEqual(
            (row["target_kind"], row["product"], row["normalized_url"]),
            (
                "url",
                "confluence",
                "https://wiki.example.test/wiki/pages/viewpage.action?pageId=123",
            ),
        )

    def test_repeat_reconciliation_does_not_inflate_evidence(self):
        candidates = [self._candidate("https://example.test/reference")]
        self._reconcile(candidates)
        before = self.connection.execute(
            "SELECT COUNT(*) FROM session_reference_evidence"
        ).fetchone()[0]

        self._reconcile(candidates)
        after = self.connection.execute(
            "SELECT COUNT(*) FROM session_reference_evidence"
        ).fetchone()[0]

        self.assertEqual((before, after), (1, 1))
        self.assertEqual(
            session_reference_projection(self.connection, 10)["items"][0]["evidence"][0]["count"],
            1,
        )

    def test_document_lookup_cache_is_built_once_and_preserves_resolution(self):
        candidates = [
            self._candidate(
                "/workspace/docs/guide.md",
                reference_kind="markdown",
                line=1,
            ),
            self._candidate(
                "README.md",
                reference_kind="markdown",
                line=2,
                event="event-2",
            ),
            self._candidate(
                "notes.md",
                reference_kind="markdown",
                line=3,
                event="event-3",
            ),
        ]
        cache = SessionReferenceLookupCache()
        with patch(
            "localbrain.sessions.references._eligible_document_rows",
            wraps=session_references._eligible_document_rows,
        ) as eligible_rows:
            self._reconcile(candidates)
            uncached = [
                tuple(row)
                for row in self.connection.execute(
                    "SELECT target_key, observed_identity FROM session_reference_evidence ORDER BY target_key"
                ).fetchall()
            ]
            reconcile_session_references(
                self.connection,
                session_id=10,
                source_path="/sessions/a.jsonl",
                source_size_bytes=100,
                source_mtime_ns=200,
                candidates=candidates,
                lookup=cache.get(self.connection),
                    )
            cached = [
                tuple(row)
                for row in self.connection.execute(
                    "SELECT target_key, observed_identity FROM session_reference_evidence ORDER BY target_key"
                ).fetchall()
            ]
            cache.get(self.connection)

        self.assertEqual(cached, uncached)
        self.assertEqual(eligible_rows.call_count, 4)

    def test_multi_file_finalization_applies_one_session_target_bound(self):
        first = [
            self._candidate(
                "https://one.example.test/{}".format(index),
                line=index + 1,
                event="one-{}".format(index),
            )
            for index in range(60)
        ]
        second = [
            self._candidate(
                "https://two.example.test/{}".format(index),
                line=index + 1,
                event="two-{}".format(index),
            )
            for index in range(60)
        ]
        self._reconcile(first, path="/sessions/a.jsonl", finalize=False)
        self._reconcile(second, path="/sessions/b.jsonl", finalize=False)
        self.connection.executemany(
            """
            INSERT INTO source_files(
                source_id, session_id, path, size_bytes, mtime_ns,
                last_scanned_at, reference_contract_version
            ) VALUES (1, 10, ?, 100, 200, 'now', ?)
            """,
            (
                ("/sessions/a.jsonl", REFERENCE_EXTRACTOR_VERSION),
                ("/sessions/b.jsonl", REFERENCE_EXTRACTOR_VERSION),
            ),
        )

        retained = finalize_session_references(self.connection, 10)
        scan = self.connection.execute(
            "SELECT * FROM session_reference_scans WHERE session_id = 10"
        ).fetchone()

        self.assertEqual(retained, 100)
        self.assertEqual(scan["status"], "partial")
        self.assertEqual(scan["observed_target_count"], 120)
        self.assertEqual(scan["retained_target_count"], 100)

    def test_target_and_evidence_bounds_prefer_completed_reads(self):
        mention_targets = [
            self._candidate(
                "https://mention.example.test/{}".format(index),
                line=index + 1,
                event="mention-{}".format(index),
            )
            for index in range(100)
        ]
        repeated_read = [
            self._candidate(
                "SYN-62",
                reference_kind="jira_key",
                evidence_kind="resource_read",
                outcome="success",
                tool_name="jira__searchIssuesByJql",
                call_id="read-{}".format(index),
                line=200 + index,
                event="result-{}".format(index),
            )
            for index in range(51)
        ]

        self._reconcile(mention_targets + repeated_read)
        scan = self.connection.execute(
            "SELECT * FROM session_reference_scans WHERE session_id = 10"
        ).fetchone()
        read_rows = self.connection.execute(
            """
            SELECT COUNT(*) FROM session_reference_evidence
            WHERE target_key = ?
            """,
            (parse_url("https://jira.example.test/browse/SYN-62").target_key,),
        ).fetchone()[0]

        self.assertEqual(
            (scan["status"], scan["observed_target_count"], scan["retained_target_count"]),
            ("partial", 101, 100),
        )
        self.assertEqual(read_rows, 50)
        self.assertIn(
            parse_url("https://jira.example.test/browse/SYN-62").target_key,
            {
                item["target_key"]
                for item in session_reference_projection(self.connection, 10)["items"]
            },
        )

    def test_ineligible_sessions_do_not_retain_reference_evidence(self):
        self._reconcile([self._candidate("https://example.test/keep")])
        self.connection.execute(
            """
            UPDATE sessions
            SET session_role = 'subsession'
            WHERE id = 10
            """
        )

        self._reconcile([self._candidate("https://example.test/drop")])

        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM session_reference_evidence"
            ).fetchone()[0],
            0,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM session_reference_scans"
            ).fetchone()[0],
            0,
        )

    def test_projection_does_not_open_source_files(self):
        self._reconcile([self._candidate("https://example.test/reference")])

        with patch("pathlib.Path.open", side_effect=AssertionError("unexpected file read")):
            projection = session_reference_projection(self.connection, 10)

        self.assertEqual(projection["retained_total"], 1)

    def test_scanner_maps_multi_file_session_repairs_partial_and_reconciles_deletion(self):
        def write_session(path, urls):
            path.write_text(
                "\n".join(
                    json.dumps(record)
                    for record in (
                        {
                            "type": "session_meta",
                            "payload": {
                                "id": "shared-native-session",
                                "cwd": "/workspace",
                            },
                        },
                        {
                            "type": "event_msg",
                            "payload": {
                                "type": "user_message",
                                "message": " ".join(urls),
                            },
                        },
                    )
                )
                + "\n",
                encoding="utf-8",
            )

        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary)
            first_path = source_root / "a.jsonl"
            second_path = source_root / "b.jsonl"
            first_urls = [
                "https://one.example.test/{}".format(index)
                for index in range(55)
            ]
            second_urls = [
                "https://two.example.test/{}".format(index)
                for index in range(55)
            ]
            write_session(first_path, first_urls)
            write_session(second_path, second_urls)

            connection = sqlite3.connect(":memory:")
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(SCHEMA_SQL)
            connection.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'codex','Company',?)", (str(source_root),))
            try:
                first_report = sessions._scan_session_source(
                    connection,
                    1,
                    "Codex Company",
                    source_root,
                    scanner.parse_codex_session,
                    scanner.CODEX_USAGE_CONTRACT_VERSION,
                    provider_kind="codex",
                )
                session = connection.execute(
                    "SELECT id, source_path FROM sessions"
                ).fetchone()
                mappings = connection.execute(
                    """
                    SELECT path, session_id, reference_contract_version
                    FROM source_files ORDER BY path
                    """
                ).fetchall()
                scan = connection.execute(
                    "SELECT * FROM session_reference_scans"
                ).fetchone()

                self.assertEqual(first_report, (2, 0, 0))
                self.assertEqual({row["session_id"] for row in mappings}, {session["id"]})
                self.assertEqual(
                    {row["reference_contract_version"] for row in mappings},
                    {REFERENCE_EXTRACTOR_VERSION},
                )
                self.assertEqual(
                    (scan["status"], scan["observed_target_count"], scan["retained_target_count"]),
                    ("partial", 110, 100),
                )

                write_session(first_path, first_urls[:-1])
                second_report = sessions._scan_session_source(
                    connection,
                    1,
                    "Codex Company",
                    source_root,
                    scanner.parse_codex_session,
                    scanner.CODEX_USAGE_CONTRACT_VERSION,
                    provider_kind="codex",
                )
                scan = connection.execute(
                    "SELECT * FROM session_reference_scans"
                ).fetchone()
                self.assertEqual(second_report, (2, 0, 0))
                self.assertEqual(
                    (scan["status"], scan["observed_target_count"]),
                    ("partial", 109),
                )

                second_path.unlink()
                delete_sibling_report = sessions._scan_session_source(
                    connection,
                    1,
                    "Codex Company",
                    source_root,
                    scanner.parse_codex_session,
                    scanner.CODEX_USAGE_CONTRACT_VERSION,
                    provider_kind="codex",
                )
                self.assertEqual(delete_sibling_report, (1, 0, 0))
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0],
                    1,
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT observed_target_count FROM session_reference_scans"
                    ).fetchone()[0],
                    54,
                )

                first_path.unlink()
                sessions._scan_session_source(
                    connection,
                    1,
                    "Codex Company",
                    source_root,
                    scanner.parse_codex_session,
                    scanner.CODEX_USAGE_CONTRACT_VERSION,
                    provider_kind="codex",
                )
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0],
                    0,
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT COUNT(*) FROM session_reference_evidence"
                    ).fetchone()[0],
                    0,
                )
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
