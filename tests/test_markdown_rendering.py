import unittest
from unittest.mock import patch

from markupsafe import Markup

from localbrain.markdown import render_markdown


class MarkdownRenderingTests(unittest.TestCase):
    def test_empty_source_returns_empty_trusted_result(self):
        result = render_markdown("")

        self.assertEqual(result.state, "empty")
        self.assertEqual(result.html, "")
        self.assertIsInstance(result.html, Markup)

    def test_plain_text_and_baseline_blocks_render_deterministically(self):
        source = """# Heading

First line
second line with **strong**, *emphasis*, and `inline`.

- parent
  - child

1. first
2. second

> quoted

| Name | Value |
| --- | --- |
| one | two |

---

[safe](https://example.test/path)
"""

        result = render_markdown(source)

        self.assertEqual(result.state, "ready")
        self.assertIn('<h1 id="heading-heading">Heading</h1>', result.html)
        self.assertIn("First line<br />", result.html)
        self.assertIn("<strong>strong</strong>", result.html)
        self.assertIn("<em>emphasis</em>", result.html)
        self.assertIn("<code>inline</code>", result.html)
        self.assertGreaterEqual(result.html.count("<ul>"), 2)
        self.assertIn("<ol>", result.html)
        self.assertIn("<blockquote>", result.html)
        self.assertIn('<div class="markdown-table-scroll"><table>', result.html)
        self.assertIn("<table>", result.html)
        self.assertIn("</table></div>", result.html)
        self.assertIn("<hr />", result.html)
        self.assertIn('href="https://example.test/path"', result.html)

    def test_source_html_and_unsafe_protocols_remain_inert(self):
        source = (
            '<script>alert("x")</script>\n\n'
            '<a href="https://example.test" onclick="steal()">raw</a>\n\n'
            '[script](javascript:alert(1)) [file](file:///tmp/private)'
        )

        result = render_markdown(source)

        self.assertEqual(result.state, "ready")
        self.assertNotIn("<script>", result.html)
        self.assertNotIn('<a href="https://example.test" onclick=', result.html)
        self.assertNotIn('href="javascript:', result.html)
        self.assertNotIn('href="file:', result.html)
        self.assertIn("&lt;script&gt;", result.html)
        self.assertIn("onclick=&quot;steal()&quot;", result.html)
        self.assertIn("[script]", result.html)

    def test_standard_images_render_as_non_fetching_deferred_markers(self):
        source = (
            '![Architecture **diagram**](https://example.test/private.png "title") '
            '![Local](images/local.png)'
        )

        result = render_markdown(source)

        self.assertEqual(result.state, "ready")
        self.assertEqual(result.html.count('data-markdown-image-deferred="true"'), 2)
        self.assertIn("Architecture diagram", result.html)
        self.assertNotIn("<img", result.html)
        self.assertNotIn("src=", result.html)
        self.assertNotIn("private.png", result.html)

    def test_known_code_language_uses_local_class_highlighting(self):
        result = render_markdown('```python\nprint("hello")\n```')

        self.assertEqual(result.state, "ready")
        self.assertIn('data-language="python"', result.html)
        self.assertIn("Python</figcaption>", result.html)
        self.assertIn('class="language-python"', result.html)
        self.assertIn('<span class="nb">print</span>', result.html)
        self.assertNotIn("style=", result.html)

    def test_unknown_language_falls_back_to_escaped_generic_code(self):
        result = render_markdown('```unknown<script>\n<a>& value\n```')

        self.assertEqual(result.state, "ready")
        self.assertIn("unknown&lt;script&gt;", result.html)
        self.assertIn("&lt;a&gt;&amp; value", result.html)
        self.assertNotIn("<span class=", result.html)

    def test_highlighter_failure_is_local_to_the_code_fence(self):
        with patch(
            "localbrain.markdown._highlight_with_pygments",
            side_effect=RuntimeError("synthetic failure"),
        ):
            result = render_markdown("```python\n<a>& value\n```")

        self.assertEqual(result.state, "ready")
        self.assertIn("&lt;a&gt;&amp; value", result.html)
        self.assertNotIn("synthetic failure", result.html)

    def test_renderer_failure_returns_escaped_full_source(self):
        source = '<script>alert("private")</script>'
        with patch(
            "localbrain.markdown._MARKDOWN.render",
            side_effect=RuntimeError("synthetic failure"),
        ):
            result = render_markdown(source)

        self.assertEqual(result.state, "fallback")
        self.assertIn('class="markdown-render-fallback"', result.html)
        self.assertIn("&lt;script&gt;", result.html)
        self.assertNotIn("<script>", result.html)
        self.assertNotIn("synthetic failure", result.html)

    def test_rendering_preserves_source_and_unicode(self):
        source = "# 제목\n\n경로 `프로젝트/문서.md` and café"
        original = source

        result = render_markdown(source)

        self.assertEqual(source, original)
        self.assertEqual(result.state, "ready")
        self.assertIn("제목", result.html)
        self.assertIn("프로젝트/문서.md", result.html)
        self.assertIn("café", result.html)

    def test_non_string_input_is_a_programmer_error(self):
        with self.assertRaises(TypeError):
            render_markdown(None)


if __name__ == "__main__":
    unittest.main()
