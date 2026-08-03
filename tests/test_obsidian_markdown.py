import unittest
from unittest.mock import patch

from localbrain.markdown import render_markdown
from localbrain.markdown_references import (
    MarkdownDocumentReference,
    MarkdownReferenceContext,
)


def document(
    identifier,
    path,
    title,
    body,
    *,
    content_type="text/markdown",
):
    return MarkdownDocumentReference(
        id=identifier,
        context_root_id=11,
        relative_path=path,
        title=title,
        body=body,
        content_type=content_type,
    )


class ObsidianMarkdownTests(unittest.TestCase):
    def test_supported_authoring_syntax_is_safe_and_read_only(self):
        source = """- [ ] open
  - [x] done

~~removed~~ ==important== #local/tag [^note]

%% hidden text %%visible and `%%code%%`

> [!warning] Read first
> Callout **body**

[^note]: Footnote
"""
        result = render_markdown(source)

        self.assertEqual(result.state, "ready")
        self.assertEqual(result.html.count('type="checkbox"'), 2)
        self.assertEqual(result.html.count('disabled="disabled"'), 2)
        self.assertIn("<s>removed</s>", result.html)
        self.assertIn("<mark>important</mark>", result.html)
        self.assertIn('data-tag="local/tag"', result.html)
        self.assertIn('class="markdown-callout markdown-callout-warning"', result.html)
        self.assertIn('class="markdown-callout-title">Read first', result.html)
        self.assertIn('class="footnotes"', result.html)
        self.assertNotIn("hidden text", result.html)
        self.assertIn("%%code%%", result.html)

    def test_valid_properties_are_separate_and_invalid_yaml_stays_readable(self):
        valid = render_markdown(
            "---\ntitle: Demo\ntags: [one, two]\npublished: true\n---\n# Body"
        )

        self.assertEqual(
            [(item.name, item.value) for item in valid.properties],
            [("title", "Demo"), ("tags", "[one, two]"), ("published", "true")],
        )
        self.assertNotIn("title: Demo", valid.html)
        self.assertIn("Body", valid.html)

        invalid = render_markdown("---\ntitle: [broken\n---\nBody")
        self.assertEqual(invalid.properties, ())
        self.assertIn("title: [broken", invalid.html)
        self.assertIn("Body", invalid.html)

    def test_math_uses_local_mathml_and_has_an_escaped_failure_state(self):
        result = render_markdown("Inline $x^2$ and block:\n\n$$\\frac{1}{2}$$")

        self.assertIn("<math", result.html)
        self.assertIn('display="inline"', result.html)
        self.assertIn('display="block"', result.html)
        self.assertNotIn("script", result.html)

        with patch(
            "localbrain.markdown.latex_to_mathml",
            side_effect=ValueError("synthetic failure"),
        ):
            fallback = render_markdown("$<tag>$")
        self.assertIn("markdown-math-fallback", fallback.html)
        self.assertIn("&lt;tag&gt;", fallback.html)
        self.assertNotIn("synthetic failure", fallback.html)

        hostile = render_markdown(r"$\text{<script>alert(1)</script>}$")
        self.assertIn("markdown-math-fallback", hostile.html)
        self.assertNotIn("<script>", hostile.html)
        self.assertIn("&lt;script&gt;", hostile.html)

        with patch(
            "localbrain.markdown.latex_to_mathml",
            return_value=(
                '<math xmlns="http://www.w3.org/1998/Math/MathML" '
                'display="inline" href="file:///tmp/private"><mi>x</mi></math>'
            ),
        ):
            unsafe_attribute = render_markdown("$x$")
        self.assertIn("markdown-math-fallback", unsafe_attribute.html)
        self.assertNotIn("file:///tmp/private", unsafe_attribute.html)

    def test_inline_math_does_not_consume_multiline_java_stack_names(self):
        source = (
            "at io.grpc.ClientCallImpl$ClientStreamListenerImpl$1StreamClosed."
            "runInternal(ClientCallImpl.java:744)\n"
            "at io.grpc.ClientCallImpl$ClientStreamListenerImpl$1StreamClosed."
            "runInContext(ClientCallImpl.java:723)"
        )

        result = render_markdown(source)

        self.assertNotIn("markdown-math", result.html)
        self.assertIn("ClientStreamListenerImpl$1StreamClosed", result.html)
        self.assertEqual(result.html.count("<br />"), 1)

    def test_inline_math_requires_a_same_line_closing_delimiter(self):
        result = render_markdown("Inline $x^2$ remains math.\nBroken $x +\ny$ stays text.")

        self.assertEqual(result.html.count("markdown-math"), 1)
        self.assertIn("Broken $x +", result.html)
        self.assertIn("y$ stays text.", result.html)

        block = render_markdown("$$\n\\frac{1}{2}\n$$")
        self.assertIn('display="block"', block.html)

    def test_duplicate_headings_blocks_and_same_document_links_are_stable(self):
        result = render_markdown(
            "# Same\n\n# Same\n\nParagraph ^piece\n\n"
            "[[#Same|wiki]] [markdown](#^piece)"
        )

        self.assertIn('id="heading-same"', result.html)
        self.assertIn('id="heading-same-2"', result.html)
        self.assertIn('id="block-piece"', result.html)
        self.assertIn('href="#heading-same">wiki</a>', result.html)
        self.assertIn('href="#block-piece"', result.html)
        self.assertNotIn("^piece", result.html)

    def test_source_scoped_links_cover_resolved_unavailable_external_and_unsafe(self):
        documents = (
            document(1, "notes/current.md", "Current", "# Current"),
            document(2, "guide.md", "Guide", "# Guide\n\n## Part"),
            document(3, "one/shared.md", "Shared One", "# Shared"),
            document(4, "two/shared.md", "Shared Two", "# Shared"),
        )
        context = MarkdownReferenceContext(documents, 1)
        result = render_markdown(
            "[[guide#Part|Guide part]] [[shared]] [[missing]] "
            "[relative](../guide.md#Part) [outside](../../private.md) "
            "[external](https://example.test/read) [file](file:///tmp/private)",
            reference_context=context,
        )

        self.assertIn('href="/documents/2#heading-part">Guide part', result.html)
        self.assertIn('href="/documents/2#heading-part"', result.html)
        self.assertIn('data-reference-state="ambiguous">shared', result.html)
        self.assertIn('data-reference-state="missing">missing', result.html)
        self.assertIn('data-reference-state="unsafe">outside', result.html)
        self.assertIn('data-reference-state="external"', result.html)
        self.assertIn('rel="noopener noreferrer external"', result.html)
        self.assertNotIn('href="file:', result.html)
        self.assertNotIn("prefetch", result.html)

        no_source = render_markdown("[[guide]] [relative](guide.md)")
        self.assertEqual(no_source.html.count('data-reference-state="no-source"'), 2)

    def test_markdown_note_embeds_select_fragments_and_bound_cycles_and_depth(self):
        documents = (
            document(1, "root.md", "Root", "# Root"),
            document(
                2,
                "target.md",
                "Target",
                "# Target\n\n## Part\n\nSelected ^piece\n\n## Other\n\nNot selected",
            ),
            document(3, "cycle-a.md", "Cycle A", "![[Cycle B]]"),
            document(4, "cycle-b.md", "Cycle B", "![[Cycle A]]"),
            document(5, "depth-a.md", "Depth A", "![[Depth B]]"),
            document(6, "depth-b.md", "Depth B", "![[Depth C]]"),
            document(7, "depth-c.md", "Depth C", "![[Depth D]]"),
            document(8, "depth-d.md", "Depth D", "![[Target]]"),
            document(9, "assets/photo.png", "Photo", "", content_type="image/png"),
        )
        context = MarkdownReferenceContext(documents, 1)

        selected = render_markdown("![[Target#Part]]", reference_context=context)
        self.assertIn('class="markdown-note-embed"', selected.html)
        self.assertIn("Selected", selected.html)
        self.assertNotIn("Not selected", selected.html)

        block = render_markdown("![[Target#^piece]]", reference_context=context)
        self.assertIn("Selected", block.html)
        self.assertNotIn("## Part", block.html)

        cycle = render_markdown("![[Cycle A]]", reference_context=context)
        self.assertIn('data-reference-state="cycle"', cycle.html)

        depth = render_markdown("![[Depth A]]", reference_context=context)
        self.assertIn('data-reference-state="depth-limit"', depth.html)

        attachment = render_markdown(
            "![[assets/photo.png]]", reference_context=context
        )
        self.assertIn("Attachment deferred", attachment.html)
        self.assertNotIn("<img", attachment.html)
        self.assertNotIn("src=", attachment.html)


if __name__ == "__main__":
    unittest.main()
