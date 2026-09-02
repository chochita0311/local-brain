import hashlib
import re
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from localbrain.atlassian import register_atlassian_site
from localbrain.atlassian_browse import atlassian_structure_reference_preview
from localbrain.atlassian_locators import describe_atlassian_url
from localbrain.atlassian_structure_references import (
    StructureReferenceIdentityCollision,
    ensure_structure_reference,
    insert_or_reuse_structure_reference_evidence,
    project_structure_reference_search,
    remove_obsolete_document_structure_evidence,
    structure_reference_preview,
)
from localbrain.db import (
    _validate_preexisting_structure_reference_contract,
    _validate_structure_reference_contract,
    init_db,
)
from localbrain.config import Settings
from localbrain.ingest.common import EVIDENCE_EXTRACTOR_VERSION, ParsedSession
from localbrain.ingest.scanner import (
    _remove_context_source_documents,
    _remove_empty_session_candidates,
    _remove_stale_sessions,
    scan_context_root,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


def pre_structure_reference_schema() -> str:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    names = (
        "atlassian_structure_references",
        "atlassian_structure_reference_urls",
        "atlassian_structure_reference_evidence",
    )
    indexes = (
        "idx_atlassian_structure_references_site",
        "idx_atlassian_structure_reference_urls_reference",
        "idx_atlassian_structure_reference_urls_canonical",
        "idx_atlassian_structure_reference_evidence_reference",
        "idx_atlassian_structure_reference_evidence_session",
        "idx_atlassian_structure_reference_evidence_document",
    )
    for name in names:
        schema, count = re.subn(
            r"CREATE TABLE IF NOT EXISTS {} \(.*?\n\);\n\n".format(
                re.escape(name)
            ),
            "",
            schema,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise AssertionError("Structure table fixture drifted: {}".format(name))
    for name in indexes:
        schema, count = re.subn(
            r"CREATE (?:UNIQUE )?INDEX IF NOT EXISTS {}\n.*?;\n".format(
                re.escape(name)
            ),
            "",
            schema,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise AssertionError("Structure index fixture drifted: {}".format(name))
    return schema


class AtlassianStructureReferenceTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.site = register_atlassian_site(
            self.connection, base_url="https://jira.structure.test"
        )
        self.source_id = int(
            self.connection.execute(
                """
                INSERT INTO sources(kind, provider_kind, name, root_path)
                VALUES ('context', 'context', 'Context', '/synthetic/context')
                """
            ).lastrowid
        )
        self.root_id = int(
            self.connection.execute(
                """
                INSERT INTO context_roots(path, label)
                VALUES ('/synthetic/context', 'Synthetic Context')
                """
            ).lastrowid
        )

    def tearDown(self):
        self.connection.close()

    def _document(self, name):
        body = "synthetic"
        return int(
            self.connection.execute(
                """
                INSERT INTO context_documents(
                    source_id, context_root_id, path, relative_path, title,
                    body, size_bytes, mtime_ns, content_hash
                ) VALUES (?, ?, ?, ?, 'Synthetic', ?, ?, 1, ?)
                """,
                (
                    self.source_id,
                    self.root_id,
                    "/synthetic/context/{}".format(name),
                    name,
                    body,
                    len(body),
                    hashlib.sha256(body.encode()).hexdigest(),
                ),
            ).lastrowid
        )

    def _reference(self, url, *, observed_at="2026-09-01T00:00:00Z"):
        locator = describe_atlassian_url(url)
        self.assertEqual(locator.kind, "structure")
        return locator, ensure_structure_reference(
            self.connection,
            site_id=int(self.site["id"]),
            locator=locator,
            observed_at=observed_at,
        )

    def _evidence(self, target, locator, document_id, *, line, refresh=False):
        return insert_or_reuse_structure_reference_evidence(
            self.connection,
            reference_id=target["reference_id"],
            safe_locator_url=locator.safe_locator_url,
            container_hint=locator.container_hint,
            document_id=document_id,
            source_line=line,
            url_ordinal=1,
            source_channel="visible_text",
            observed_at="2026-09-01T00:00:00Z",
            refresh_existing=refresh,
        )

    def _session(self, name):
        source_path = "/synthetic/sessions/{}.jsonl".format(name)
        session_id = int(
            self.connection.execute(
                """
                INSERT INTO sessions(source_id, external_id, source_path, title)
                VALUES (?, ?, ?, ?)
                """,
                (self.source_id, name, source_path, name),
            ).lastrowid
        )
        self.connection.execute(
            """
            INSERT INTO source_files(
                source_id, session_id, path, size_bytes, mtime_ns,
                last_scanned_at
            ) VALUES (?, ?, ?, 1, 1, '2026-09-01T00:00:00Z')
            """,
            (self.source_id, session_id, source_path),
        )
        return session_id, source_path

    def _session_evidence(self, target, locator, session_id, source_path):
        insert_or_reuse_structure_reference_evidence(
            self.connection,
            reference_id=target["reference_id"],
            safe_locator_url=locator.safe_locator_url,
            container_hint=locator.container_hint,
            session_id=session_id,
            source_path=source_path,
            source_event_id="event-1",
            source_line=1,
            url_ordinal=1,
            source_channel="visible_text",
            observed_at="2026-09-01T00:00:00Z",
        )

    def _assert_archived_after_owner_delete(self, reference_id):
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*)
                FROM atlassian_structure_reference_evidence
                WHERE reference_id = ?
                """,
                (reference_id,),
            ).fetchone()[0],
            0,
        )
        reference = structure_reference_preview(
            self.connection, reference_id
        )
        self.assertIsNotNone(reference)
        self.assertEqual(reference["lifecycle"], "archived")
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
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*)
                FROM atlassian_structure_reference_urls
                WHERE reference_id = ?
                """,
                (reference_id,),
            ).fetchone()[0],
            1,
        )

    def test_schema_has_exact_additive_owners_constraints_and_indexes(self):
        _validate_preexisting_structure_reference_contract(self.connection)
        _validate_structure_reference_contract(self.connection)
        tables = {
            row["name"]
            for row in self.connection.execute(
                """
                SELECT name FROM sqlite_schema
                WHERE type = 'table'
                  AND name LIKE 'atlassian_structure_reference%'
                """
            )
        }
        self.assertEqual(
            tables,
            {
                "atlassian_structure_references",
                "atlassian_structure_reference_urls",
                "atlassian_structure_reference_evidence",
            },
        )
        self.assertEqual(self.connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(
            [
                row["name"]
                for row in self.connection.execute(
                    """
                    PRAGMA index_info(
                        'idx_atlassian_structure_reference_evidence_session'
                    )
                    """
                ).fetchall()
            ],
            [
                "session_id",
                "source_path",
                "source_event_id",
                "source_line",
                "url_ordinal",
            ],
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO atlassian_structure_references(
                    site_id, service, reference_kind, reference_identity
                ) VALUES (?, 'confluence', 'jira_board', '17')
                """,
                (self.site["id"],),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO atlassian_structure_references(
                    site_id, service, reference_kind, reference_identity
                ) VALUES (?, 'jira', 'jira_board', ?)
                """,
                (self.site["id"], "x" * 301),
            )

    def test_preexisting_partial_owner_fails_closed(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        try:
            connection.execute(
                "CREATE TABLE atlassian_structure_references(id INTEGER PRIMARY KEY)"
            )
            with self.assertRaisesRegex(RuntimeError, "partial"):
                _validate_preexisting_structure_reference_contract(connection)
        finally:
            connection.close()

    def test_compatible_file_startup_adds_owner_without_rewriting_site(self):
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            database_path = data_dir / "localbrain.db"
            connection = sqlite3.connect(str(database_path))
            connection.executescript(pre_structure_reference_schema())
            site_id = int(
                connection.execute(
                    """
                    INSERT INTO atlassian_sites(
                        normalized_domain, canonical_base_url, display_name
                    ) VALUES ('preserved.example.test',
                              'https://preserved.example.test',
                              'Preserved Site')
                    """
                ).lastrowid
            )
            before = tuple(
                connection.execute(
                    """
                    SELECT id, normalized_domain, canonical_base_url,
                           display_name
                    FROM atlassian_sites WHERE id = ?
                    """,
                    (site_id,),
                ).fetchone()
            )
            connection.commit()
            connection.close()
            settings = Settings(
                data_dir=data_dir,
                database_path=database_path,
                context_root=data_dir / "context",
                claude_root=data_dir / "claude",
                codex_root=data_dir / "codex",
                mcp_call_budget=20,
            )

            with patch("localbrain.db.settings", settings):
                init_db()
                init_db()

            upgraded = sqlite3.connect(str(database_path))
            try:
                after = tuple(
                    upgraded.execute(
                        """
                        SELECT id, normalized_domain, canonical_base_url,
                               display_name
                        FROM atlassian_sites WHERE id = ?
                        """,
                        (site_id,),
                    ).fetchone()
                )
                self.assertEqual(after, before)
                self.assertEqual(
                    {
                        row[0]
                        for row in upgraded.execute(
                            """
                            SELECT name FROM sqlite_schema
                            WHERE type = 'table'
                              AND name LIKE 'atlassian_structure_reference%'
                            """
                        ).fetchall()
                    },
                    {
                        "atlassian_structure_references",
                        "atlassian_structure_reference_urls",
                        "atlassian_structure_reference_evidence",
                    },
                )
                self.assertEqual(
                    upgraded.execute("PRAGMA foreign_key_check").fetchall(),
                    [],
                )
            finally:
                upgraded.close()

    def test_identity_alias_hint_consensus_archive_and_reactivation(self):
        first_locator, first = self._reference(
            "https://jira.structure.test/secure/RapidBoard.jspa?"
            "rapidView=17&projectKey=PAY"
        )
        alias_locator, alias = self._reference(
            "https://jira.structure.test/secure/RapidBoard.jspa?rapidView=17"
        )
        self.assertTrue(first["created_reference"])
        self.assertEqual(first["url_role"], "canonical")
        self.assertFalse(alias["created_reference"])
        self.assertEqual(alias["url_role"], "alias")
        self.assertEqual(first["reference_id"], alias["reference_id"])

        document_one = self._document("one.md")
        document_two = self._document("two.md")
        first_evidence = self._evidence(
            first, first_locator, document_one, line=1
        )
        self._evidence(alias, alias_locator, document_two, line=1)
        projected = structure_reference_preview(
            self.connection, first["reference_id"]
        )
        self.assertEqual(projected["container_label"], "PAY")
        self.assertEqual(projected["availability"], "available")
        self.assertEqual(projected["evidence"]["total"], 2)
        self.assertEqual(projected["alias_total"], 1)

        conflicting_locator, conflicting = self._reference(
            "https://jira.structure.test/secure/RapidBoard.jspa?"
            "rapidView=17&projectKey=CHECKOUT"
        )
        self._evidence(
            conflicting, conflicting_locator, document_two, line=2
        )
        projected = structure_reference_preview(
            self.connection, first["reference_id"]
        )
        self.assertEqual(projected["container_kind"], "unclassified")

        retained = {first_evidence["evidence_key"]}
        removed = remove_obsolete_document_structure_evidence(
            self.connection,
            document_id=document_two,
            retained_keys=(),
        )
        self.assertEqual(len(removed["evidence_keys"]), 2)
        projected = structure_reference_preview(
            self.connection, first["reference_id"]
        )
        self.assertEqual(projected["container_label"], "PAY")

        remove_obsolete_document_structure_evidence(
            self.connection,
            document_id=document_one,
            retained_keys=(),
        )
        projected = structure_reference_preview(
            self.connection, first["reference_id"]
        )
        self.assertEqual(projected["lifecycle"], "archived")
        self.assertEqual(projected["availability"], "archived")
        self.assertEqual(projected["canonical_url"], first_locator.safe_locator_url)
        self.assertFalse(project_structure_reference_search(self.connection, first["reference_id"]))

        reactivated = self._evidence(
            first, first_locator, document_one, line=1
        )
        self.assertEqual(reactivated["evidence_key"], first_evidence["evidence_key"])
        self.assertTrue(reactivated["created"])
        self.assertTrue(project_structure_reference_search(self.connection, first["reference_id"]))
        self.assertEqual(
            self.connection.execute(
                """
                SELECT COUNT(*) FROM search_index
                WHERE entity_type = 'atlassian_structure_reference'
                """
            ).fetchone()[0],
            1,
        )

    def test_safe_url_collision_fails_without_reassignment(self):
        locator, first = self._reference(
            "https://jira.structure.test/secure/RapidBoard.jspa?rapidView=17"
        )
        conflicting = replace(locator, reference_identity="18")
        with self.assertRaises(StructureReferenceIdentityCollision):
            ensure_structure_reference(
                self.connection,
                site_id=int(self.site["id"]),
                locator=conflicting,
            )
        owner = self.connection.execute(
            """
            SELECT reference_id FROM atlassian_structure_reference_urls
            WHERE safe_locator_url = ?
            """,
            (locator.safe_locator_url,),
        ).fetchone()
        self.assertEqual(int(owner["reference_id"]), first["reference_id"])

    def test_evidence_v4_and_exact_repeat_are_read_only(self):
        locator, target = self._reference(
            "https://jira.structure.test/projects/PAY"
        )
        document_id = self._document("repeat.md")
        first = self._evidence(target, locator, document_id, line=1)
        changes = self.connection.total_changes
        second = self._evidence(target, locator, document_id, line=1)
        self.assertEqual(second, {"evidence_key": first["evidence_key"], "created": False})
        self.assertEqual(self.connection.total_changes, changes)
        row = self.connection.execute(
            """
            SELECT extractor_version
            FROM atlassian_structure_reference_evidence
            WHERE evidence_key = ?
            """,
            (first["evidence_key"],),
        ).fetchone()
        self.assertEqual(row["extractor_version"], "localbrain.atlassian-evidence.v4")
        self.assertEqual(EVIDENCE_EXTRACTOR_VERSION, "localbrain.atlassian-evidence.v4")

    def test_preview_is_target_bounded_and_caps_newest_five_evidence_rows(self):
        locator, target = self._reference(
            "https://jira.structure.test/secure/RapidBoard.jspa?"
            "rapidView=17&projectKey=PAY"
        )
        document_ids = []
        for index in range(7):
            document_id = self._document("bounded-{}.md".format(index))
            document_ids.append(document_id)
            insert_or_reuse_structure_reference_evidence(
                self.connection,
                reference_id=target["reference_id"],
                safe_locator_url=locator.safe_locator_url,
                container_hint=locator.container_hint,
                document_id=document_id,
                source_line=index + 1,
                url_ordinal=1,
                source_channel="visible_text",
                observed_at="2026-09-01T00:00:{:02d}Z".format(index),
            )
        statements = []
        self.connection.set_trace_callback(statements.append)

        preview = atlassian_structure_reference_preview(
            self.connection, target["reference_id"], {}
        )
        missing = atlassian_structure_reference_preview(
            self.connection, 9_999_999, {}
        )
        self.connection.set_trace_callback(None)

        self.assertIsNone(missing)
        self.assertEqual(preview["evidence"]["total"], 7)
        self.assertTrue(preview["evidence"]["truncated"])
        self.assertTrue(
            {
                "site_name",
                "created_at",
                "updated_at",
                "hint_count",
                "consensus_hint",
                "url_total",
            }.isdisjoint(preview)
        )
        self.assertNotIn("id", preview["evidence"]["items"][0])
        self.assertEqual(
            [row["local_id"] for row in preview["evidence"]["items"]],
            list(reversed(document_ids[-5:])),
        )
        sql = "\n".join(statements).lower()
        self.assertNotIn("group by reference_id", sql)
        self.assertNotIn("atlassian_item_classifications", sql)
        self.assertNotIn("workstream_links", sql)
        self.assertNotIn("atlassian_item_remote_state", sql)

    def test_stale_session_removal_reprojects_cascaded_structure_evidence(self):
        locator, target = self._reference(
            "https://jira.structure.test/secure/RapidBoard.jspa?rapidView=81"
        )
        session_id, source_path = self._session("stale-structure")
        self._session_evidence(target, locator, session_id, source_path)
        project_structure_reference_search(
            self.connection, target["reference_id"]
        )

        _remove_stale_sessions(self.connection, self.source_id, [])

        self.assertIsNone(
            self.connection.execute(
                "SELECT id FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        )
        self._assert_archived_after_owner_delete(target["reference_id"])

    def test_empty_session_removal_reprojects_cascaded_structure_evidence(self):
        locator, target = self._reference(
            "https://jira.structure.test/secure/RapidBoard.jspa?rapidView=82"
        )
        session_id, source_path = self._session("empty-structure")
        self._session_evidence(target, locator, session_id, source_path)
        project_structure_reference_search(
            self.connection, target["reference_id"]
        )
        parsed = ParsedSession(
            external_id="empty-structure",
            source_path=source_path,
            cwd_raw=None,
            git_branch=None,
            title="Empty structure",
            started_at=None,
            ended_at=None,
            last_event_at=None,
            events=[],
        )

        _remove_empty_session_candidates(
            self.connection,
            self.source_id,
            [(Path(source_path), parsed)],
        )

        self.assertIsNone(
            self.connection.execute(
                "SELECT id FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        )
        self._assert_archived_after_owner_delete(target["reference_id"])

    def test_file_document_removal_reprojects_cascaded_structure_evidence(self):
        locator, target = self._reference(
            "https://jira.structure.test/secure/RapidBoard.jspa?rapidView=83"
        )
        document_id = self._document("removed-file.md")
        self._evidence(target, locator, document_id, line=1)
        project_structure_reference_search(
            self.connection, target["reference_id"]
        )

        _remove_context_source_documents(
            self.connection, self.root_id, set()
        )

        self.assertIsNone(
            self.connection.execute(
                "SELECT id FROM context_documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        )
        self._assert_archived_after_owner_delete(target["reference_id"])

    def test_folder_document_removal_reprojects_cascaded_structure_evidence(self):
        locator, target = self._reference(
            "https://jira.structure.test/secure/RapidBoard.jspa?rapidView=84"
        )
        with tempfile.TemporaryDirectory() as directory:
            root_id = int(
                self.connection.execute(
                    """
                    INSERT INTO context_roots(path, label)
                    VALUES (?, 'Folder structure')
                    """,
                    (directory,),
                ).lastrowid
            )
            missing_path = str(Path(directory) / "removed.md")
            document_id = int(
                self.connection.execute(
                    """
                    INSERT INTO context_documents(
                        source_id, context_root_id, path, relative_path, title,
                        body, size_bytes, mtime_ns, content_hash
                    ) VALUES (?, ?, ?, 'removed.md', 'Removed', 'body',
                              4, 1, ?)
                    """,
                    (
                        self.source_id,
                        root_id,
                        missing_path,
                        hashlib.sha256(b"body").hexdigest(),
                    ),
                ).lastrowid
            )
            self._evidence(target, locator, document_id, line=1)
            project_structure_reference_search(
                self.connection, target["reference_id"]
            )

            self.assertEqual(
                scan_context_root(self.connection, root_id, force=False),
                (0, 0, 0),
            )

        self.assertIsNone(
            self.connection.execute(
                "SELECT id FROM context_documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        )
        self._assert_archived_after_owner_delete(target["reference_id"])


if __name__ == "__main__":
    unittest.main()
