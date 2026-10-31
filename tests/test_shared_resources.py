import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.foundation.config import Settings
from localbrain.ingest.contracts import ParsedReferenceCandidate
from localbrain.ingest.extensions import document_indexed, observe_ingestion
from localbrain.ingest.sync.contexts import _upsert_context_document
from localbrain.persistence.db import init_db
from localbrain.persistence.migrations.resources import (
    BACKUP_SUFFIX, RESOURCE_TABLES, migrate_shared_resources,
    shared_resource_contract_current,
)
from localbrain.resources.catalog import (
    bind_document, bind_local_path,
    resource_by_hint, url_resource,
)
from localbrain.resources.store import create_local_resource
from localbrain.sessions.references import reconcile_session_references, session_reference_projection
from localbrain.workstreams.service import add_link


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "src/localbrain/schema.sql").read_text()


def legacy_schema():
    schema = SCHEMA
    old = (ROOT / "tests/fixtures/legacy-shared-resource-tables.sql").read_text()
    for name in (*RESOURCE_TABLES, "session_reference_evidence", "external_resource_content", "external_resource_notes"):
        schema, count = re.subn(r"CREATE TABLE IF NOT EXISTS " + name + r" \(.*?\n\);\n", "", schema, flags=re.S)
        if count != 1:
            raise AssertionError("Legacy fixture drift: " + name)
    schema = schema.replace("    resource_id INTEGER REFERENCES reference_resources(id) ON DELETE RESTRICT,\n", "")
    schema = re.sub(r"CREATE INDEX IF NOT EXISTS idx_session_reference_evidence_\w+\n.*?;\n", "", schema, flags=re.S)
    return old + "\n" + schema


def connection_for(schema=SCHEMA, path=":memory:"):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(schema)
    connection.executescript("""
        INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'context','Synthetic','/synthetic');
        INSERT INTO context_roots(id,path,label) VALUES (1,'/synthetic','Synthetic');
        INSERT INTO sessions(id,source_id,external_id,source_path,title)
        VALUES (10,1,'s1','/synthetic/s1.jsonl','Session 1'), (11,1,'s2','/synthetic/s2.jsonl','Session 2');
        INSERT INTO context_documents(id,source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash)
        VALUES (20,1,1,'/synthetic/guide.md','guide.md','Guide','Synthetic body',14,1,'hash');
        INSERT INTO local_resources(id,path,resource_type,title,summary,discovered_by)
        VALUES (30,'/synthetic/guide.md','file','Manual label','Manual note','user');
        INSERT INTO external_resources(id,resource_type,title,url,summary,source_role)
        VALUES (40,'jira_issue','Manual issue','https://jira.example.test/browse/SYN-1','Preserve note','user');
        INSERT INTO atlassian_sites(id,normalized_domain,canonical_base_url)
        VALUES (50,'jira.example.test','https://jira.example.test');
        INSERT INTO atlassian_items(external_resource_id,site_id,service,item_type,remote_key)
        VALUES (40,50,'jira','jira_issue','SYN-1');
        INSERT INTO workstreams(id,name,summary) VALUES (60,'Pilot','Manual work note');
        INSERT INTO workstream_links(id,workstream_id,entity_type,entity_id,relation_type,confidence,linked_by)
        VALUES (70,60,'local','30','reference',0.8,'user'), (71,60,'document','20','evidence',1,'user');
    """)
    return connection


def references(connection, session_id=10, values=None):
    values = values or [("url", "https://jira.example.test/browse/SYN-1")]
    candidates = [ParsedReferenceCandidate(
        reference_kind=kind, reference=value, evidence_kind="user_mention",
        source_event_id="event-" + str(line), source_line=line, evidence_ordinal=1,
    ) for line, (kind, value) in enumerate(values, 1)]
    return reconcile_session_references(
        connection, session_id=session_id, source_path="/synthetic/s{}.jsonl".format(session_id),
        source_size_bytes=100, source_mtime_ns=1, candidates=candidates,
    )


class SharedResourceTests(unittest.TestCase):
    def setUp(self):
        self.connection = connection_for()
        self.addCleanup(self.connection.close)

    def test_document_and_bookmark_share_identity_without_overwriting_metadata(self):
        c = self.connection
        before = tuple(c.execute("SELECT * FROM local_resources WHERE id=30").fetchone())
        resource_id = bind_document(c, 20)
        self.assertEqual(bind_local_path(c, 30), resource_id)
        self.assertEqual(tuple(c.execute("SELECT * FROM local_resources WHERE id=30").fetchone()), before)
        add_link(c, "workstream", 60, "document", "20", "evidence")
        add_link(c, "workstream", 60, "local", "30", "reference")
        self.assertEqual([tuple(r) for r in c.execute("SELECT id,resource_id FROM workstream_links ORDER BY id")], [(70, resource_id), (71, resource_id)])
        c.execute("DELETE FROM workstreams WHERE id=60")
        self.assertIsNotNone(c.execute("SELECT id FROM reference_resources WHERE id=?", (resource_id,)).fetchone())
        self.assertEqual(c.execute("SELECT summary FROM local_resources WHERE id=30").fetchone()[0], "Manual note")
        self.assertEqual(c.execute("SELECT body FROM context_documents WHERE id=20").fetchone()[0], "Synthetic body")

    def test_sessions_share_urls_without_registration_or_cross_domain_merging(self):
        c = self.connection
        c.execute("DELETE FROM atlassian_items")
        c.execute("DELETE FROM atlassian_sites")
        cloud = "https://cloud.example.test/wiki/spaces/TEAM/pages/123"
        legacy = "https://cloud.example.test/wiki/pages/viewpage.action?pageId=123"
        references(c, 10, [("url", cloud)])
        references(c, 11, [("url", legacy)])
        rows = c.execute("SELECT DISTINCT resource_id FROM session_reference_evidence").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(c.execute("SELECT product FROM reference_resources WHERE id=?", rows[0]).fetchone()[0], "confluence")
        other = url_resource(c, "https://other.example.test/wiki/spaces/TEAM/pages/123")
        self.assertNotEqual(other, rows[0][0])
        self.assertIsNone(resource_by_hint(c, "confluence_page_id", "123"))

    def test_removed_document_keeps_evidence_and_reindex_restores_destination(self):
        c = self.connection
        references(c, values=[("markdown", "/synthetic/guide.md")])
        before = tuple(c.execute("SELECT * FROM session_reference_evidence").fetchone())
        c.execute("DELETE FROM context_documents WHERE id=20")
        self.assertEqual(tuple(c.execute("SELECT * FROM session_reference_evidence").fetchone()), before)
        references(c, values=[("markdown", "/synthetic/guide.md")])
        self.assertEqual(c.execute("SELECT COUNT(*) FROM session_reference_evidence").fetchone()[0], 1)
        self.assertIsNone(session_reference_projection(c, 10)["items"][0]["destination"])
        document_id = _upsert_context_document(c, 1, 1, "/synthetic/guide.md", "guide.md", "New title", "New body", 8, 2, "markdown")
        self.assertNotEqual(document_id, 20)
        with patch.object(Path, "read_text", side_effect=AssertionError("Projection must not read files")):
            item = session_reference_projection(c, 10)["items"][0]
        self.assertEqual(item["destination"], "/documents/{}".format(document_id))
        self.assertEqual(item["resource_id"], c.execute("SELECT resource_id FROM session_reference_evidence").fetchone()[0])

    def test_hint_resolution_is_independent_of_candidate_order(self):
        c = self.connection
        references(c, values=[("jira_key", "SYN-1"), ("url", "https://jira.example.test/browse/SYN-1")])
        self.assertEqual(c.execute("SELECT COUNT(*) FROM session_reference_evidence").fetchone()[0], 2)
        references(c, values=[("url", "https://jira.example.test/browse/SYN-1"), ("jira_key", "SYN-1"), ("url", "https://other.example.test/browse/SYN-1")])
        self.assertEqual([r[0] for r in c.execute("SELECT source_line FROM session_reference_evidence ORDER BY source_line")], [1, 3])

    def test_path_registration_does_not_import_unregistered_files(self):
        c = self.connection
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "unregistered.md"
            path.write_text("Synthetic unregistered content")
            with patch.object(Path, "read_text", side_effect=AssertionError("No automatic import")):
                local_id = create_local_resource(c, str(path), "Bookmark", "Keep")
                references(c, values=[("markdown", str(path))])
            self.assertIsNotNone(c.execute("SELECT resource_id FROM resource_local_paths WHERE local_resource_id=?", (local_id,)).fetchone())
            self.assertEqual(c.execute("SELECT COUNT(*) FROM context_documents").fetchone()[0], 1)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM session_reference_evidence").fetchone()[0], 0)

    def test_optional_table_removal_does_not_block_core_reads_or_writes(self):
        c = self.connection
        c.commit()
        c.execute("PRAGMA foreign_keys=OFF")
        names = [r[0] for r in c.execute("SELECT name FROM sqlite_schema WHERE type='table'")]
        for name in names:
            if name.startswith("atlassian_") or name in {"workstreams", "workstream_links", "threads", "thread_links"}:
                c.execute('DROP TABLE "' + name + '"')
        c.execute("PRAGMA foreign_keys=ON")
        with observe_ingestion(()):
            document_id = _upsert_context_document(c, 1, 1, "/synthetic/guide.md", "guide.md", "Guide", "Updated", 7, 2, "markdown")
            document_indexed(c, document_id, "updated", "Updated")
            references(c, values=[("markdown", "/synthetic/guide.md"), ("url", "https://jira.example.test/browse/SYN-1")])
            from localbrain.local_context.service import context_document_reader
            from localbrain.local_context.queries import document_detail
            reader = context_document_reader(c, document_detail(c, document_id))
            from localbrain.ingest.scanner import scan_context_root
            from localbrain.local_context.service import add_context_root
            with tempfile.TemporaryDirectory() as root:
                (Path(root) / "second.md").write_text("# Second\nSynthetic text")
                root_id = add_context_root(c, root)
                self.assertEqual(scan_context_root(c, root_id, force=True), (1, 0, 0))
                self.assertEqual(scan_context_root(c, root_id, force=False), (0, 1, 0))
        self.assertTrue(reader)
        self.assertEqual(len(session_reference_projection(c, 10)["items"]), 2)

    def test_core_imports_do_not_require_optional_packages(self):
        script = """
import importlib.abc, sys
class BlockOptional(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == 'localbrain.' + name or fullname.startswith('localbrain.' + name + '.')
               for name in ('atlassian','workstreams','auto_work','workflow','natural_search')):
            raise AssertionError('Optional import: ' + fullname)
sys.meta_path.insert(0, BlockOptional())
from localbrain.ingest.scanner import scan_context_root, scan_session_sources
from localbrain.local_context.service import context_document_reader
from localbrain.sessions.references import session_reference_projection
from localbrain.resources.store import create_local_resource
from localbrain.local_context.web import show_document
from localbrain.resources.web import show_local_resource
"""
        result = subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_observers_are_scoped_and_share_the_caller_transaction(self):
        c = self.connection
        class FailingObserver:
            def document_indexed(self, connection, document_id, content_hash, body):
                connection.execute("UPDATE local_resources SET summary='temporary' WHERE id=30")
                raise RuntimeError("observer failure")
        c.commit()
        with self.assertRaisesRegex(RuntimeError, "observer failure"):
            with c, observe_ingestion((FailingObserver(),)):
                document_indexed(c, 20, "hash", "body")
        document_indexed(c, 20, "hash", "body")
        self.assertEqual(c.execute("SELECT summary FROM local_resources WHERE id=30").fetchone()[0], "Manual note")


class SharedResourceMigrationTests(unittest.TestCase):
    def seed_legacy(self, path=":memory:"):
        c = connection_for(legacy_schema(), path)
        c.execute("""INSERT INTO atlassian_item_content(external_resource_id,source_format,source_body,source_hash,
            normalized_document_json,normalized_text,normalizer_version,applied_at)
            VALUES (40,'plain_text','Preserved body',?,'{}','Preserved body','synthetic','2026-01-01')""", ("a" * 64,))
        c.execute("INSERT INTO atlassian_item_local_state(external_resource_id,note) VALUES (40,'Preserve user note')")
        for ident, kind, key, document, external, locator in (
            (1, "context_document", "document:20", 20, None, None),
            (2, "atlassian_item", "atlassian:40", None, 40, "https://jira.example.test/browse/SYN-1"),
            (3, "url", "url:" + "c" * 64, None, None, "https://jira.example.test/issues/SYN-1"),
        ):
            c.execute("""INSERT INTO session_reference_evidence(id,session_id,source_path,source_event_id,source_line,
                evidence_ordinal,target_kind,target_key,context_document_id,external_resource_id,evidence_kind,
                observed_identity,normalized_url,extractor_version,evidence_key,first_observed_at,last_observed_at)
                VALUES (?,10,'/synthetic/s1.jsonl','event',?,1,?,?,?,?,'user_mention','Original observation',?,'v3',?,'first','last')""",
                (ident, ident, kind, key, document, external, locator, str(ident) * 64))
        c.execute("""INSERT INTO session_reference_scans(session_id,source_fingerprint,extractor_version,status,
            observed_target_count,retained_target_count,scanned_at) VALUES (10,?,'v3','ok',3,3,'before')""", ("a" * 64,))
        c.commit()
        return c

    def test_migration_preserves_ids_notes_evidence_and_content_and_is_repeatable(self):
        c = self.seed_legacy()
        self.addCleanup(c.close)
        snapshots = {t: [dict(r) for r in c.execute("SELECT * FROM " + t)] for t in (
            "context_documents", "local_resources", "external_resources", "workstreams", "workstream_links", "session_reference_evidence",
        )}
        body = tuple(c.execute("SELECT * FROM atlassian_item_content").fetchone())
        self.assertTrue(migrate_shared_resources(c))
        c.executescript(SCHEMA)
        for table, old in snapshots.items():
            new = [dict(r) for r in c.execute("SELECT * FROM " + table)]
            removed = {"target_kind", "context_document_id", "external_resource_id", "target_key"} if table == "session_reference_evidence" else set()
            for before, after in zip(old, new):
                self.assertEqual({k: after[k] for k in before if k not in removed}, {k: v for k, v in before.items() if k not in removed})
            self.assertEqual(len(old), len(new))
        self.assertEqual(tuple(c.execute("SELECT * FROM external_resource_content").fetchone()), body)
        self.assertEqual(tuple(c.execute("SELECT observed_target_count,retained_target_count FROM session_reference_scans").fetchone()), (2, 2))
        before = list(c.iterdump())
        self.assertFalse(migrate_shared_resources(c))
        self.assertEqual(list(c.iterdump()), before)
        self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
        c.execute("DELETE FROM atlassian_items")
        c.execute("DELETE FROM atlassian_sites")
        self.assertEqual(tuple(c.execute("SELECT * FROM external_resource_content").fetchone()), body)
        self.assertEqual(c.execute("SELECT COUNT(*) FROM session_reference_evidence").fetchone()[0], 3)
        self.assertEqual(c.execute("SELECT note FROM external_resource_notes WHERE external_resource_id=40").fetchone()[0], "Preserve user note")

    def test_failed_migration_rolls_back_every_table_and_caller_can_retry(self):
        c = self.seed_legacy()
        self.addCleanup(c.close)
        before = list(c.iterdump())
        with patch("localbrain.persistence.migrations.resources._migrate_content", side_effect=RuntimeError("synthetic failure")):
            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                migrate_shared_resources(c)
        self.assertEqual(list(c.iterdump()), before)
        self.assertTrue(migrate_shared_resources(c))

    def test_partial_migration_is_stale_until_recollection(self):
        c = self.seed_legacy()
        self.addCleanup(c.close)
        c.execute("UPDATE session_reference_scans SET status='partial', observed_target_count=101, retained_target_count=100")
        migrate_shared_resources(c)
        row = c.execute("SELECT * FROM session_reference_scans").fetchone()
        self.assertEqual((row["status"], row["observed_target_count"], row["retained_target_count"], row["error_code"]), ("error", 101, 2, "resource-identity-migration"))

    def test_startup_creates_private_non_overwriting_backup_before_migration(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            database = root / "synthetic.db"
            self.seed_legacy(str(database)).close()
            config = Settings(data_dir=root, database_path=database, context_root=root / "context", claude_root=root / "claude", codex_root=root / "codex", mcp_call_budget=20)
            with patch("localbrain.persistence.db.settings", config):
                init_db()
                backup = Path(str(database) + BACKUP_SUFFIX)
                content = backup.read_bytes()
                self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
                init_db()
                self.assertEqual(backup.read_bytes(), content)
            with sqlite3.connect(backup) as old:
                self.assertEqual(old.execute("SELECT COUNT(*) FROM atlassian_item_content").fetchone()[0], 1)
            with sqlite3.connect(database) as current:
                self.assertTrue(shared_resource_contract_current(current))
                self.assertEqual(current.execute("PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main()
