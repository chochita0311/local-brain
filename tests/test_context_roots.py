import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from markupsafe import Markup

from localbrain.contexts import (
    add_apple_notes_source,
    add_context_file,
    add_context_root,
    build_markdown_reference_context,
    context_document_reader,
    context_document_preview,
    context_source_tree,
    list_context_sources,
    list_context_roots,
    remove_context_root,
)
from localbrain.ingest.scanner import scan_context_root
from localbrain.markdown import MarkdownProperty, MarkdownRenderResult
from localbrain.queries import context_documents, document_detail


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class ContextRootTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.db_path = Path(handle.name)
        self.root_parent = tempfile.TemporaryDirectory()
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    def tearDown(self):
        self.connection.close()
        self.root_parent.cleanup()
        self.db_path.unlink(missing_ok=True)

    def test_roots_can_be_added_scanned_removed_and_restored(self):
        root = Path(self.root_parent.name) / "sample-project"
        nested = root / "work" / "search"
        nested.mkdir(parents=True)
        document_path = nested / "implementation.md"
        document_path.write_text("# 검색 필터 implementation\nDetails", encoding="utf-8")

        root_id = add_context_root(self.connection, str(root))
        self.assertEqual(scan_context_root(self.connection, root_id, force=True), (1, 0, 0))
        roots = list_context_roots(self.connection)
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0]["document_count"], 1)
        document = context_documents(self.connection, root_id)[0]
        self.assertEqual(document["relative_path"], "work/search/implementation.md")
        document_id = document["id"]
        reference_context = build_markdown_reference_context(
            self.connection, document_id
        )
        self.assertIsNotNone(reference_context)
        self.assertEqual(reference_context.current_document_id, document_id)
        self.assertEqual(len(reference_context.documents), 1)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM search_index WHERE entity_type = 'document'"
            ).fetchone()[0],
            1,
        )
        tree = context_source_tree(self.connection, root_id)
        self.assertEqual(tree[0]["name"], "work")
        self.assertEqual(
            tree[0]["children"][0]["children"][0]["name"],
            "implementation.md",
        )

        with self.assertRaises(ValueError):
            add_context_root(self.connection, str(nested))

        remove_context_root(self.connection, root_id)
        self.assertEqual(list_context_roots(self.connection), [])
        self.assertEqual(context_documents(self.connection), [])
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM context_documents WHERE id = ?", (document_id,)
            ).fetchone()[0],
            1,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM search_index WHERE entity_type = 'document'"
            ).fetchone()[0],
            0,
        )
        disabled_reader = context_document_reader(
            self.connection,
            document_detail(self.connection, document_id),
        )
        self.assertFalse(disabled_reader["has_context_tree"])
        self.assertIsNone(disabled_reader["context_source"])
        self.assertEqual(disabled_reader["context_tree"], [])
        self.assertEqual(disabled_reader["return_href"], "/context")

        restored_id = add_context_root(self.connection, str(root))
        self.assertEqual(restored_id, root_id)
        self.assertEqual(scan_context_root(self.connection, root_id, force=True), (1, 0, 0))
        restored_document = context_documents(self.connection, root_id)[0]
        self.assertEqual(restored_document["id"], document_id)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM search_index WHERE entity_type = 'document'"
            ).fetchone()[0],
            1,
        )

    def test_direct_files_and_apple_notes_are_distinct_sources(self):
        text_path = Path(self.root_parent.name) / "handover.txt"
        text_path.write_text("Handover facts", encoding="utf-8")
        file_id = add_context_file(self.connection, str(text_path))
        self.assertEqual(scan_context_root(self.connection, file_id, force=True), (1, 0, 0))
        file_source = next(
            item for item in list_context_sources(self.connection)
            if item["id"] == file_id
        )
        self.assertEqual(file_source["source_type"], "file")
        self.assertEqual(file_source["status"], "ready")
        document = context_documents(self.connection, file_id)[0]
        self.assertEqual(document["relative_path"], "handover.txt")
        self.assertIsNone(
            build_markdown_reference_context(self.connection, document["id"])
        )

        binary_path = Path(self.root_parent.name) / "archive.bin"
        binary_path.write_bytes(b"\x00\x01\x02")
        binary_id = add_context_file(self.connection, str(binary_path))
        self.assertEqual(scan_context_root(self.connection, binary_id, force=True), (0, 0, 0))
        binary_source = next(
            item for item in list_context_sources(self.connection)
            if item["id"] == binary_id
        )
        self.assertEqual(binary_source["status"], "unreadable")
        self.assertEqual(context_documents(self.connection, binary_id), [])

        notes_id = add_apple_notes_source(self.connection)
        notes_source = next(
            item for item in list_context_sources(self.connection)
            if item["id"] == notes_id
        )
        self.assertEqual(notes_source["source_type"], "apple_notes")
        self.assertEqual(notes_source["display_path"], "Notes.app")

    def test_folder_preview_resolves_locally_while_file_preview_has_no_source(self):
        root = Path(self.root_parent.name) / "linked-notes"
        notes = root / "notes"
        notes.mkdir(parents=True)
        (notes / "current.md").write_text(
            "# Current\n\n[[Guide#Part|continue]]",
            encoding="utf-8",
        )
        (root / "guide.md").write_text(
            "# Guide\n\n## Part\n\nDetails",
            encoding="utf-8",
        )
        root_id = add_context_root(self.connection, str(root))
        self.assertEqual(scan_context_root(self.connection, root_id, force=True), (2, 0, 0))
        documents = context_documents(self.connection, root_id)
        current = next(
            item for item in documents if item["relative_path"] == "notes/current.md"
        )
        guide = next(
            item for item in documents if item["relative_path"] == "guide.md"
        )

        preview = context_document_preview(
            self.connection,
            document_detail(self.connection, current["id"]),
        )

        self.assertEqual(preview["body"], "# Current\n\n[[Guide#Part|continue]]")
        self.assertEqual(preview["render_state"], "ready")
        self.assertIn(
            'href="/documents/{}#heading-part">continue'.format(guide["id"]),
            preview["rendered_body"],
        )
        reader = context_document_reader(
            self.connection,
            document_detail(self.connection, current["id"]),
        )
        self.assertTrue(reader["has_context_tree"])
        self.assertEqual(reader["context_source"]["source_type"], "folder")
        self.assertEqual(reader["context_source"]["document_count"], 2)
        self.assertEqual(
            reader["return_href"],
            "/context?root={}&document={}".format(root_id, current["id"]),
        )
        selected_branch = next(
            node for node in reader["context_tree"]
            if node["kind"] == "directory" and node["contains_selected"]
        )
        selected_leaf = next(
            node for node in selected_branch["children"]
            if node["kind"] == "document" and node["contains_selected"]
        )
        self.assertEqual(selected_leaf["id"], current["id"])

        standalone = Path(self.root_parent.name) / "standalone.md"
        standalone.write_text("[[Guide]]", encoding="utf-8")
        file_id = add_context_file(self.connection, str(standalone))
        self.assertEqual(scan_context_root(self.connection, file_id, force=True), (1, 0, 0))
        file_document = context_documents(self.connection, file_id)[0]
        file_preview = context_document_preview(
            self.connection,
            document_detail(self.connection, file_document["id"]),
        )
        self.assertIn(
            'data-reference-state="no-source"', file_preview["rendered_body"]
        )
        file_reader = context_document_reader(
            self.connection,
            document_detail(self.connection, file_document["id"]),
        )
        self.assertFalse(file_reader["has_context_tree"])
        self.assertEqual(file_reader["context_tree"], [])
        self.assertEqual(file_reader["context_source"]["source_type"], "file")

        empty_document = dict(document_detail(self.connection, current["id"]))
        empty_document["body"] = ""
        empty_preview = context_document_preview(self.connection, empty_document)
        self.assertEqual(empty_preview["render_state"], "empty")
        self.assertEqual(empty_preview["rendered_body"], "")

        with patch(
            "localbrain.contexts.render_markdown",
            return_value=MarkdownRenderResult(
                html=Markup('<pre class="markdown-render-fallback">source</pre>'),
                state="fallback",
                properties=(MarkdownProperty("status", "draft"),),
            ),
        ):
            fallback_preview = context_document_preview(
                self.connection,
                document_detail(self.connection, current["id"]),
            )
        self.assertEqual(fallback_preview["render_state"], "fallback")
        self.assertEqual(fallback_preview["render_properties"][0].name, "status")
        self.assertIn("markdown-render-fallback", fallback_preview["rendered_body"])


if __name__ == "__main__":
    unittest.main()
