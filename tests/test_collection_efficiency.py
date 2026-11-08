import sqlite3
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from itertools import count
from pathlib import Path
from unittest.mock import patch

from localbrain.ingest.sync import contexts
from localbrain.natural_search import index
from localbrain.natural_search.molecules import Profile
from localbrain.natural_search.source import read_sources
from localbrain.usage.records import store_usage_records
from natural_search_fixtures import ContractEncoder, fixture
from test_activity_attribution import parsed_session, usage_record
from localbrain.ingest.sync.session_store import _store_session


class CollectionEfficiencyTests(unittest.TestCase):
    def test_context_walk_preserves_markdown_set_without_entering_excluded_trees(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("a.md", "visible/deep.md", "visible/upper.MD", ".hidden/a.md", "visible/.inner/a.md", "node_modules/a.md", "build/deep/b.md"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic")
            (root / "linked.md").symlink_to(root / "a.md")
            (root / "linked-dir").symlink_to(root / "visible", target_is_directory=True)
            (root / "directory.md").mkdir()
            expected = sorted(path for path in root.rglob("*.md") if not any(
                part.startswith(".") or part in contexts.IGNORED_CONTEXT_DIRECTORIES for part in path.relative_to(root).parts
            ))
            visited = []
            scandir = contexts.os.scandir
            def observe(path):
                visited.append(Path(path))
                return scandir(path)
            with patch.object(contexts.os, "scandir", observe):
                self.assertEqual(sorted(contexts._context_paths(root)), expected)
            self.assertNotIn(root / "node_modules", visited)
            self.assertNotIn(root / "build", visited)
            self.assertNotIn(root / ".hidden", visited)
            self.assertNotIn(root / "linked-dir", visited)
            with patch.object(contexts.control, "_check_scan_cancelled", side_effect=InterruptedError):
                with self.assertRaises(InterruptedError):
                    list(contexts._context_paths(root))

    def test_context_walk_preserves_rglob_scan_failure_behavior(self):
        for failure in ("removed", "replaced", "permission", "io"):
            results = []
            for baseline in (True, False):
                with self.subTest(failure=failure, baseline=baseline), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    (root / "surviving.md").write_text("synthetic")
                    queued = root / "queued"
                    queued.mkdir()
                    scandir = contexts.os.scandir
                    def race(path):
                        if Path(path) == queued:
                            if failure == "permission":
                                raise PermissionError(13, "synthetic denied")
                            if failure == "io":
                                raise OSError(5, "synthetic read failure")
                            queued.rmdir()
                            if failure == "replaced":
                                queued.write_text("no longer a directory")
                        return scandir(path)
                    with patch.object(contexts.os, "scandir", race):
                        try:
                            paths = root.rglob("*.md") if baseline else contexts._context_paths(root)
                            results.append((sorted(path.name for path in paths), None))
                        except OSError as error:
                            results.append((None, type(error)))
            self.assertEqual(results[0], results[1], failure)

    def test_usage_attribution_queries_once_per_store_and_keeps_record_times(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = fixture(temporary)
            with sqlite3.connect(config.database_path) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute("INSERT INTO workspaces(id,canonical_path,display_name,exists_now) VALUES (1,'/synthetic/work','Work',1)")
                source = parsed_session("batch", "/synthetic/work", [])
                _store_session(connection, 1, source)
                ident = connection.execute("SELECT id FROM sessions WHERE external_id='batch'").fetchone()[0]
                records = [usage_record(str(n)) for n in range(30)]
                statements = []
                connection.set_trace_callback(statements.append)
                times = ((datetime(2026, 11, 7, tzinfo=timezone.utc) + timedelta(seconds=n)).isoformat() for n in count())
                with patch("localbrain.usage.records.utc_now", side_effect=times):
                    store_usage_records(connection, 1, ident, records, workspace_id=1)
                workspace_queries = [sql for sql in statements if "FROM WORKSPACES WHERE ID" in " ".join(sql.upper().split())]
                self.assertEqual(len(workspace_queries), 1)
                old = [dict(row) for row in connection.execute("SELECT * FROM usage_records WHERE session_id=? ORDER BY id", (ident,))]
                self.assertEqual(len({row["attributed_at"] for row in old}), 30)
                connection.execute("UPDATE workspaces SET git_root='/synthetic/work' WHERE id=1")
                store_usage_records(connection, 1, ident, [*records, usage_record("new")], workspace_id=1)
                after = [dict(row) for row in connection.execute("SELECT * FROM usage_records WHERE session_id=? AND source_record_id<>'new' ORDER BY id", (ident,))]
                # Reconciliation updates imported_at; the observed attribution,
                # IDs, prices and native usage facts remain frozen.
                self.assertEqual(
                    [{key: value for key, value in row.items() if key != "imported_at"} for row in after],
                    [{key: value for key, value in row.items() if key != "imported_at"} for row in old],
                )
                self.assertEqual(connection.execute("SELECT attribution_basis FROM usage_records WHERE source_record_id='new'").fetchone()[0], "git_root")

    def test_index_batches_prior_vectors_and_preserves_fragments_terms_and_blobs(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = fixture(temporary)
            profile = Profile()
            encoder = ContractEncoder(config, profile)
            encoder.batch_size = 16
            with sqlite3.connect(config.database_path) as connection:
                connection.execute("UPDATE context_documents SET body=? WHERE id=1", ("앱 반복 근거. " * 1800,))
            first = index.prepare(config, encoder, profile)
            def contents():
                with index.open_index(index.folder(config) / "index.sqlite3") as connection:
                    return {table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1")] for table in ("fragments", "vectors", "terms")}
            before = contents()
            sources, coverage = read_sources(config)
            changed = [replace(source, timestamp="2026-11-07T00:00:00Z") for source in sources]
            statements = []
            connect = sqlite3.connect
            def traced(*args, **kwargs):
                connection = connect(*args, **kwargs)
                connection.set_trace_callback(statements.append)
                return connection
            with patch.object(index, "read_sources", return_value=(changed, coverage)), patch.object(index.sqlite3, "connect", traced):
                second = index.prepare(config, encoder, profile)
            self.assertGreater(first["fragments"], 16)
            self.assertEqual(second["encoded"], 0)
            self.assertEqual(second["reused"], first["fragments"])
            self.assertEqual(contents(), before)
            vector_reads = [sql for sql in statements if sql.upper().startswith("SELECT") and "FROM vectors" in sql]
            self.assertLess(len(vector_reads), first["fragments"] / 2)
            self.assertTrue(any("input_hash IN" in sql for sql in vector_reads))
            self.assertFalse(any("SELECT 1 FROM vectors WHERE" in sql for sql in vector_reads))
