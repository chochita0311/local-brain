import unittest

from localbrain.markdown_references import (
    MarkdownDocumentReference,
    MarkdownReferenceContext,
    document_anchor_index,
    extract_document_fragment,
)


def document(
    identifier,
    path,
    title,
    body="# Title",
    *,
    root_id=7,
    content_type="text/markdown",
):
    return MarkdownDocumentReference(
        id=identifier,
        context_root_id=root_id,
        relative_path=path,
        title=title,
        body=body,
        content_type=content_type,
    )


class MarkdownReferenceTests(unittest.TestCase):
    def setUp(self):
        self.documents = (
            document(1, "notes/current.md", "Current", "# Current\n\nText ^here"),
            document(2, "guide.md", "Guide", "# Guide\n\n## Part\n\nDetails ^detail"),
            document(3, "one/shared.md", "Shared One"),
            document(4, "two/shared.md", "Shared Two"),
            document(5, "assets/image.png", "Image", "", content_type="image/png"),
        )
        self.context = MarkdownReferenceContext(self.documents, 1)

    def test_context_rejects_mixed_roots_and_missing_current_document(self):
        with self.assertRaises(ValueError):
            MarkdownReferenceContext(
                self.documents + (document(8, "other.md", "Other", root_id=9),),
                1,
            )
        with self.assertRaises(ValueError):
            MarkdownReferenceContext(self.documents, 99)

    def test_relative_and_root_wiki_paths_resolve_inside_one_source(self):
        relative = self.context.resolve("../guide.md#Part", kind="markdown")
        wiki = self.context.resolve("guide#^detail", kind="wiki")

        self.assertEqual(relative.state, "resolved")
        self.assertEqual(relative.href, "/documents/2#heading-part")
        self.assertEqual(wiki.state, "resolved")
        self.assertEqual(wiki.href, "/documents/2#block-detail")

    def test_pathless_ambiguity_missing_fragment_and_root_escape_do_not_guess(self):
        ambiguous = self.context.resolve("shared", kind="wiki")
        missing_fragment = self.context.resolve("guide#Absent", kind="wiki")
        escaped = self.context.resolve("../../secret.md", kind="markdown")
        encoded_escape = self.context.resolve(
            "%2e%2e/%2e%2e/secret.md", kind="markdown"
        )

        self.assertEqual(ambiguous.state, "ambiguous")
        self.assertEqual(missing_fragment.state, "missing")
        self.assertEqual(escaped.state, "unsafe")
        self.assertEqual(encoded_escape.state, "unsafe")

    def test_external_and_unsafe_schemes_are_explicit(self):
        external = self.context.resolve("https://example.test/read", kind="wiki")

        self.assertEqual(external.state, "external")
        self.assertEqual(external.href, "https://example.test/read")
        for target in (
            "file:///tmp/private.md",
            "javascript:alert(1)",
            "obsidian://open?vault=private",
            "/absolute/private.md",
        ):
            with self.subTest(target=target):
                self.assertEqual(self.context.resolve(target).state, "unsafe")

    def test_anchor_index_and_fragment_extraction_are_deterministic(self):
        source = "# Same\n\nFirst\n\n# Same\n\n## Part\n\nBody ^piece\n\n# Next"
        headings, blocks = document_anchor_index(source)

        self.assertEqual(headings["same"], "heading-same")
        self.assertEqual(headings["part"], "heading-part")
        self.assertEqual(blocks["piece"], "block-piece")
        self.assertEqual(
            extract_document_fragment(source, "Part"),
            "## Part\n\nBody ^piece",
        )
        self.assertEqual(extract_document_fragment(source, "^piece"), "Body")


if __name__ == "__main__":
    unittest.main()
