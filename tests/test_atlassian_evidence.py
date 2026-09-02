import sqlite3
import tempfile
import unittest
from pathlib import Path

from localbrain.atlassian import (
    create_or_reuse_atlassian_stub,
    register_atlassian_site,
)
from localbrain.atlassian_evidence import (
    atlassian_url_container_hint,
    configured_atlassian_site_fingerprint,
    document_evidence_source_fingerprint,
    evidence_scan_is_current,
    normalize_atlassian_structural_scope,
    recognize_configured_atlassian_item_url,
    recognize_strict_atlassian_item_url,
    reconcile_document_evidence,
    reconcile_session_evidence,
)
from localbrain.contexts import add_context_root, remove_context_root
from localbrain.ingest.scanner import scan_context_root
from localbrain.ingest.common import EVIDENCE_EXTRACTOR_VERSION, ParsedUrlEvidence


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class AtlassianEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.source_id = int(
            self.connection.execute(
                """
                INSERT INTO sources(kind, name, root_path)
                VALUES ('codex', 'Codex', '/tmp')
                """
            ).lastrowid
        )
        self.jira_instance = self._source_instance("jira-main", "jira")
        self.confluence_instance = self._source_instance(
            "wiki-main", "confluence"
        )
        register_atlassian_site(
            self.connection,
            source_instance_id=self.jira_instance,
            base_url="https://jira.example.test",
        )
        register_atlassian_site(
            self.connection,
            source_instance_id=self.confluence_instance,
            base_url="https://wiki.example.test",
        )

    def tearDown(self):
        self.connection.close()

    def _source_instance(self, key, service):
        return int(
            self.connection.execute(
                """
                INSERT INTO external_source_instances(
                    instance_key, provider_kind, service, display_name
                ) VALUES (?, 'mcp_gateway', ?, ?)
                """,
                (key, service, key),
            ).lastrowid
        )

    def _session(self, *, session_class="work", session_role="primary"):
        return int(
            self.connection.execute(
                """
                INSERT INTO sessions(
                    source_id, external_id, source_path, title,
                    session_class, session_role, index_policy
                ) VALUES (?, ?, ?, 'Synthetic', ?, ?, ?)
                """,
                (
                    self.source_id,
                    "session-{}-{}".format(session_class, session_role),
                    "/tmp/{}-{}.jsonl".format(session_class, session_role),
                    session_class,
                    session_role,
                    "full" if session_class == "work" else "metadata_only",
                ),
            ).lastrowid
        )

    def _candidate(
        self,
        url="https://jira.example.test/browse/SYN-12",
        *,
        line=4,
        channel="visible_text",
    ):
        return ParsedUrlEvidence(
            observed_url=url,
            source_line=line,
            url_ordinal=1,
            source_channel=channel,
            source_event_id="event-{}".format(line),
            observed_at="2026-07-23T00:00:00Z",
        )

    def test_recognizer_requires_item_url_and_one_domain_site(self):
        jira = recognize_configured_atlassian_item_url(
            self.connection, "https://jira.example.test/browse/SYN-12"
        )
        page = recognize_configured_atlassian_item_url(
            self.connection,
            "https://wiki.example.test/wiki/spaces/SYN/pages/77/Page",
        )

        self.assertEqual(jira.service, "jira")
        self.assertEqual(jira.observed_remote_key, "SYN-12")
        self.assertEqual(page.service, "confluence")
        self.assertEqual(page.observed_remote_id, "77")
        jira_key_at_limit = "A{}-1".format("B" * 297)
        page_id_at_limit = "7" * 300
        self.assertEqual(len(jira_key_at_limit), 300)
        self.assertIsNotNone(
            recognize_configured_atlassian_item_url(
                self.connection,
                "https://jira.example.test/browse/{}".format(
                    jira_key_at_limit
                ),
            )
        )
        self.assertIsNotNone(
            recognize_configured_atlassian_item_url(
                self.connection,
                "https://wiki.example.test/wiki/pages/{}/Page".format(
                    page_id_at_limit
                ),
            )
        )
        self.assertIsNone(
            recognize_configured_atlassian_item_url(
                self.connection,
                "https://jira.example.test/browse/A{}-1".format("B" * 298),
            )
        )
        self.assertIsNone(
            recognize_configured_atlassian_item_url(
                self.connection,
                "https://wiki.example.test/wiki/pages/{}/Page".format(
                    "7" * 301
                ),
            )
        )
        bounded_query = recognize_configured_atlassian_item_url(
            self.connection,
            "https://jira.example.test/browse/SYN-12?q={}".format(
                "한" * 900
            ),
        )
        self.assertIsNotNone(bounded_query)
        self.assertEqual(
            bounded_query.normalized.normalized_url,
            "https://jira.example.test/browse/SYN-12",
        )
        self.assertIsNone(
            recognize_configured_atlassian_item_url(
                self.connection, "https://jira.example.test/projects/SYN"
            )
        )
        self.assertIsNone(
            recognize_configured_atlassian_item_url(
                self.connection, "https://unknown.example.test/browse/SYN-12"
            )
        )

        duplicate_instance = self._source_instance("jira-duplicate", "jira")
        register_atlassian_site(
            self.connection,
            source_instance_id=duplicate_instance,
            base_url="https://jira.example.test",
        )
        shared_site = recognize_configured_atlassian_item_url(
            self.connection, "https://jira.example.test/browse/SYN-12"
        )
        self.assertIsNotNone(shared_site)
        self.assertIsNone(shared_site.source_instance_id)

    def test_strict_url_container_hints_are_stable_service_specific_and_bounded(self):
        jira = recognize_strict_atlassian_item_url(
            "https://new.example.test/issues/abc_2-17"
        )
        self.assertIsNotNone(jira.recognized)
        self.assertEqual(jira.recognized.service, "jira")
        self.assertEqual(
            jira.recognized.container_structural_scope,
            "url:jira:ABC_2",
        )
        wiki = atlassian_url_container_hint(
            "https://new.example.test/wiki/spaces/%EF%BC%B4%EF%BC%A5%EF%BC%A1%EF%BC%AD/pages/77/Guide"
        )
        self.assertEqual(
            wiki,
            {
                "structural_scope": "url:confluence:TEAM",
                "label": "TEAM",
                "service": "confluence",
            },
        )
        for url in (
            "https://new.example.test/wiki/pages/77/Guide",
            "https://new.example.test/wiki/viewpage.action?pageId=77",
            "https://new.example.test/wiki/spaces/%2E/pages/77/Guide",
            "https://new.example.test/wiki/spaces/%2E%2E/pages/77/Guide",
            "https://new.example.test/wiki/spaces/A%2FB/pages/77/Guide",
            "https://new.example.test/wiki/spaces/A%5CB/pages/77/Guide",
            "https://new.example.test/wiki/spaces/A%00B/pages/77/Guide",
            "https://new.example.test/wiki/spaces/{}/pages/77/Guide".format(
                "A" * 301
            ),
        ):
            with self.subTest(url=url):
                self.assertIsNone(atlassian_url_container_hint(url))

        self.assertEqual(
            normalize_atlassian_structural_scope("url:jira:project_1"),
            "url:jira:PROJECT_1",
        )
        self.assertEqual(
            normalize_atlassian_structural_scope(
                "url:confluence:" + ("A" * 300)
            ),
            "url:confluence:" + ("A" * 300),
        )
        for value in (
            "url:jira:" + ("A" * 301),
            "url:confluence:",
            "url:confluence:.",
            "url:confluence:..",
            "url:confluence:A/B",
            "url:confluence:A\\B",
            "url:confluence:A\x00B",
            "url:confluence:" + ("A" * 301),
        ):
            with self.subTest(value=value):
                self.assertIsNone(
                    normalize_atlassian_structural_scope(value)
                )

    def test_evidence_consumer_admits_only_locator_items_without_dml(self):
        aliases = (
            (
                "https://jira.example.test/jira/software/c/projects/SYN/issues/SYN-44",
                "jira",
                "https://jira.example.test/browse/SYN-44",
            ),
            (
                "https://wiki.example.test/confluence/pages/00077/Guide",
                "confluence",
                "https://wiki.example.test/confluence/pages/viewpage.action?pageId=77",
            ),
        )
        before = self.connection.total_changes
        for url, service, safe_url in aliases:
            with self.subTest(url=url):
                result = recognize_strict_atlassian_item_url(url)
                self.assertIsNotNone(result.recognized)
                self.assertEqual(result.recognized.service, service)
                self.assertEqual(result.normalized_url, safe_url)

        rejected = (
            (
                "https://jira.example.test/secure/RapidBoard.jspa?rapidView=17",
                "unsupported-locator",
            ),
            ("https://jira.example.test/issues", "unsupported-locator"),
            (
                "https://wiki.example.test/wiki/spaces/TEAM",
                "unsupported-locator",
            ),
            (
                "https://jira.example.test/browse?issueKey=SYN-44",
                "unsupported-locator",
            ),
            (
                "https://jira.example.test/browse/SYN-44?selectedIssue=%ZZ",
                "unsafe-url",
            ),
        )
        for url, reason in rejected:
            with self.subTest(url=url):
                result = recognize_strict_atlassian_item_url(url)
                self.assertIsNone(result.recognized)
                self.assertEqual(result.reason_code, reason)
        self.assertEqual(self.connection.total_changes, before)

    def test_local_only_registered_site_participates_in_local_evidence(self):
        item = create_or_reuse_atlassian_stub(
            self.connection,
            service="jira",
            url="https://local.example.test/browse/LOCAL-7",
            title="LOCAL-7",
        )
        recognized = recognize_configured_atlassian_item_url(
            self.connection,
            "https://local.example.test/browse/LOCAL-7",
        )
        self.assertIsNotNone(recognized)
        self.assertIsNone(recognized.source_instance_id)

        session_id = self._session()
        count = reconcile_session_evidence(
            self.connection,
            session_id=session_id,
            source_path="/tmp/work-primary.jsonl",
            source_fingerprint="9" * 64,
            candidates=[
                self._candidate(
                    "https://local.example.test/browse/LOCAL-7"
                )
            ],
        )
        self.assertEqual(count, 1)
        self.assertEqual(
            self.connection.execute(
                "SELECT external_resource_id FROM atlassian_item_evidence"
            ).fetchone()[0],
            item["external_resource_id"],
        )

    def test_session_reconciliation_is_idempotent_and_removal_keeps_item(self):
        session_id = self._session()
        fingerprint = "a" * 64

        first_count = reconcile_session_evidence(
            self.connection,
            session_id=session_id,
            source_path="/tmp/work-primary.jsonl",
            source_fingerprint=fingerprint,
            candidates=[self._candidate()],
        )
        evidence = self.connection.execute(
            "SELECT * FROM atlassian_item_evidence"
        ).fetchone()
        resource_id = int(evidence["external_resource_id"])
        first_evidence_id = int(evidence["id"])

        second_count = reconcile_session_evidence(
            self.connection,
            session_id=session_id,
            source_path="/tmp/work-primary.jsonl",
            source_fingerprint=fingerprint,
            candidates=[self._candidate()],
        )

        self.assertEqual((first_count, second_count), (1, 1))
        self.assertEqual(
            self.connection.execute(
                "SELECT id FROM atlassian_item_evidence"
            ).fetchone()["id"],
            first_evidence_id,
        )
        self.assertTrue(
            evidence_scan_is_current(
                self.connection,
                session_id=session_id,
                source_path="/tmp/work-primary.jsonl",
                source_fingerprint=fingerprint,
            )
        )

        reconcile_session_evidence(
            self.connection,
            session_id=session_id,
            source_path="/tmp/work-primary.jsonl",
            source_fingerprint="b" * 64,
            candidates=[],
        )

        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_evidence"
            ).fetchone()[0],
            0,
        )
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM atlassian_items
                WHERE external_resource_id = ?
                """,
                (resource_id,),
            ).fetchone()[0],
            1,
        )

    def test_key_only_unknown_and_maintenance_sources_create_nothing(self):
        maintenance_id = self._session(session_class="maintenance")
        work_id = self._session(session_role="subsession")

        for session_id in (maintenance_id, work_id):
            reconcile_session_evidence(
                self.connection,
                session_id=session_id,
                source_path=(
                    "/tmp/maintenance-primary.jsonl"
                    if session_id == maintenance_id
                    else "/tmp/work-subsession.jsonl"
                ),
                source_fingerprint="c" * 64,
                candidates=[
                    self._candidate(
                        "https://jira.example.test/browse/SYN-13"
                    )
                ],
            )
            self.assertTrue(
                evidence_scan_is_current(
                    self.connection,
                    session_id=session_id,
                    source_path=(
                        "/tmp/maintenance-primary.jsonl"
                        if session_id == maintenance_id
                        else "/tmp/work-subsession.jsonl"
                    ),
                    source_fingerprint="c" * 64,
                )
            )

        primary = self._session()
        reconcile_session_evidence(
            self.connection,
            session_id=primary,
            source_path="/tmp/work-primary.jsonl",
            source_fingerprint="d" * 64,
            candidates=[
                self._candidate("https://unknown.example.test/browse/SYN-13")
            ],
        )

        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_items"
            ).fetchone()[0],
            0,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM atlassian_item_evidence"
            ).fetchone()[0],
            0,
        )

    def test_document_lines_reconcile_without_storing_excerpt(self):
        context_source = int(
            self.connection.execute(
                """
                INSERT INTO sources(kind, name, root_path)
                VALUES ('context', 'Context', '/tmp/context')
                """
            ).lastrowid
        )
        root_id = int(
            self.connection.execute(
                """
                INSERT INTO context_roots(path, label)
                VALUES ('/tmp/context', 'Context')
                """
            ).lastrowid
        )
        body = (
            "SYN-12 is only a key\n"
            "Read https://wiki.example.test/wiki/spaces/SYN/pages/77/Page\n"
        )
        content_hash = "e" * 64
        document_id = int(
            self.connection.execute(
                """
                INSERT INTO context_documents(
                    source_id, context_root_id, path, relative_path, title,
                    body, size_bytes, mtime_ns, content_hash
                ) VALUES (?, ?, '/tmp/context/note.md', 'note.md', 'Note',
                          ?, ?, 1, ?)
                """,
                (
                    context_source,
                    root_id,
                    body,
                    len(body.encode("utf-8")),
                    content_hash,
                ),
            ).lastrowid
        )
        fingerprint = document_evidence_source_fingerprint(content_hash)

        reconcile_document_evidence(
            self.connection,
            document_id=document_id,
            source_fingerprint=fingerprint,
            body=body,
        )

        evidence = self.connection.execute(
            "SELECT * FROM atlassian_item_evidence"
        ).fetchone()
        self.assertEqual(evidence["document_id"], document_id)
        self.assertEqual(evidence["source_line"], 2)
        self.assertIsNone(evidence["source_event_id"])
        self.assertNotIn(
            "excerpt",
            {
                row["name"]
                for row in self.connection.execute(
                    "PRAGMA table_info(atlassian_item_evidence)"
                )
            },
        )

    def test_site_configuration_change_invalidates_scan_without_remote_io(self):
        session_id = self._session()
        fingerprint = "f" * 64
        reconcile_session_evidence(
            self.connection,
            session_id=session_id,
            source_path="/tmp/work-primary.jsonl",
            source_fingerprint=fingerprint,
            candidates=[],
        )
        before = configured_atlassian_site_fingerprint(self.connection)
        self.assertTrue(
            evidence_scan_is_current(
                self.connection,
                session_id=session_id,
                source_path="/tmp/work-primary.jsonl",
                source_fingerprint=fingerprint,
            )
        )

        register_atlassian_site(
            self.connection,
            source_instance_id=self.jira_instance,
            base_url="https://jira-second.example.test",
        )

        self.assertNotEqual(
            before, configured_atlassian_site_fingerprint(self.connection)
        )
        self.assertFalse(
            evidence_scan_is_current(
                self.connection,
                session_id=session_id,
                source_path="/tmp/work-primary.jsonl",
                source_fingerprint=fingerprint,
            )
        )

    def test_context_scanner_skips_current_evidence_and_reconciles_changes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "context"
            root.mkdir()
            note = root / "note.md"
            note.write_text(
                "https://jira.example.test/browse/SYN-22\n",
                encoding="utf-8",
            )
            root_id = add_context_root(self.connection, str(root))

            self.assertEqual(
                scan_context_root(self.connection, root_id, force=True),
                (1, 0, 0),
            )
            self.assertEqual(
                scan_context_root(self.connection, root_id, force=False),
                (0, 1, 0),
            )
            self.assertEqual(
                EVIDENCE_EXTRACTOR_VERSION,
                "localbrain.atlassian-evidence.v4",
            )
            self.connection.execute(
                """
                UPDATE atlassian_evidence_scans
                SET extractor_version = 'localbrain.atlassian-evidence.v2'
                """
            )
            self.assertEqual(
                scan_context_root(self.connection, root_id, force=False),
                (1, 0, 0),
            )
            self.assertEqual(
                self.connection.execute(
                    "SELECT extractor_version FROM atlassian_evidence_scans"
                ).fetchone()[0],
                EVIDENCE_EXTRACTOR_VERSION,
            )
            statements = []
            self.connection.set_trace_callback(statements.append)
            self.assertEqual(
                scan_context_root(self.connection, root_id, force=False),
                (0, 1, 0),
            )
            self.connection.set_trace_callback(None)
            identity_writes = [
                statement
                for statement in statements
                if statement.lstrip().split(None, 1)[0].upper()
                in {"INSERT", "UPDATE", "DELETE", "REPLACE"}
                and any(
                    table in statement.lower()
                    for table in (
                        "atlassian_item_evidence",
                        "atlassian_item_urls",
                        "atlassian_items",
                        "atlassian_evidence_scans",
                    )
                )
            ]
            self.assertEqual(identity_writes, [])
            resource_id = int(
                self.connection.execute(
                    "SELECT external_resource_id FROM atlassian_item_evidence"
                ).fetchone()[0]
            )

            register_atlassian_site(
                self.connection,
                source_instance_id=self.jira_instance,
                base_url="https://another.example.test",
            )
            self.assertEqual(
                scan_context_root(self.connection, root_id, force=False),
                (1, 0, 0),
            )

            note.write_text("SYN-22 without a URL\n", encoding="utf-8")
            self.assertEqual(
                scan_context_root(self.connection, root_id, force=False),
                (1, 0, 0),
            )
            self.assertEqual(
                self.connection.execute(
                    "SELECT COUNT(*) FROM atlassian_item_evidence"
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                self.connection.execute(
                    """
                    SELECT COUNT(*) FROM atlassian_items
                    WHERE external_resource_id = ?
                    """,
                    (resource_id,),
                ).fetchone()[0],
                1,
            )

            note.write_text(
                "https://jira.example.test/browse/SYN-22\n",
                encoding="utf-8",
            )
            self.assertEqual(
                scan_context_root(self.connection, root_id, force=False),
                (1, 0, 0),
            )
            self.assertEqual(
                self.connection.execute(
                    "SELECT COUNT(*) FROM atlassian_item_evidence"
                ).fetchone()[0],
                1,
            )
            remove_context_root(self.connection, root_id)
            self.assertEqual(
                self.connection.execute(
                    "SELECT COUNT(*) FROM atlassian_item_evidence"
                ).fetchone()[0],
                0,
            )


if __name__ == "__main__":
    unittest.main()
