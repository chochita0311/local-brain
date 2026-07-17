import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
STYLES = ROOT / "src" / "localbrain" / "static" / "styles.css"
SCRIPT = ROOT / "src" / "localbrain" / "static" / "app.js"
BASE = ROOT / "src" / "localbrain" / "templates" / "base.html"
CONTEXT = ROOT / "src" / "localbrain" / "templates" / "context.html"


class UiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.styles = STYLES.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.base = BASE.read_text(encoding="utf-8")
        cls.context = CONTEXT.read_text(encoding="utf-8")

    def test_component_rules_do_not_use_raw_colors(self):
        token_end = self.styles.index("\n}\n\n* { box-sizing")
        component_rules = self.styles[token_end:]
        self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", component_rules))
        self.assertIsNone(re.search(r"rgba?\(", component_rules))

    def test_component_rules_consume_semantic_design_roles(self):
        token_end = self.styles.index("\n}\n\n* { box-sizing")
        component_rules = self.styles[token_end:]
        primitive_reference = re.compile(
            r"var\(--(?:color-[^)]+|font-[^)]+|size-[^)]+|weight-[^)]+|"
            r"line-[^)]+|space-\d+|radius-\d+|radius-full|stroke-[^)]+|"
            r"shadow-[^)]+|duration-[^)]+|ease-[^)]+|opacity-[^)]+)\)"
        )
        raw_spacing = re.compile(
            r"(?<![-\w])(?:margin|padding|gap|top|right|bottom|left)"
            r"(?:-[a-z]+)?\s*:[^;}]*?\b-?\d+px\b"
        )
        self.assertIsNone(primitive_reference.search(component_rules))
        self.assertIsNone(raw_spacing.search(component_rules))

        for property_name in (
            "font-size",
            "font-weight",
            "font-family",
            "line-height",
            "border-radius",
            "box-shadow",
        ):
            values = re.findall(
                rf"{property_name}\s*:\s*([^;}}]+)", component_rules
            )
            for value in values:
                self.assertTrue(
                    value.strip().startswith(("var(", "inherit", "none")),
                    f"{property_name} uses a non-semantic value: {value}",
                )
        self.assertIsNone(re.search(r"(?:transition|animation)[^;]*\b\d+m?s\b", component_rules))

    def test_semantic_foundation_includes_provenance_and_responsive_contracts(self):
        for token in (
            "--surface-source-claude",
            "--surface-source-codex",
            "--text-source-claude",
            "--text-source-codex",
            "--shell-sidebar-width: 220px",
            "--shell-sidebar-width-compact: 188px",
            "--breakpoint-compact: 920px",
            "--breakpoint-narrow: 700px",
            "--viewport-min-width: 320px",
        ):
            self.assertIn(token, self.styles)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.styles)

    def test_status_families_remain_semantically_distinct(self):
        expected_rules = (
            ".source-status.pending { color: var(--text-info);",
            ".source-status.missing { color: var(--text-warning);",
            ".status-badge.blocked { color: var(--text-danger);",
            ".run-status.running { color: var(--text-brand);",
            ".run-status.completed { color: var(--text-success);",
            ".run-status.failed { color: var(--text-danger);",
            ".result-type.claude { color: var(--text-source-claude);",
            ".result-type.codex { color: var(--text-source-codex);",
        )
        for rule in expected_rules:
            self.assertIn(rule, self.styles)

    def test_shared_shell_exposes_keyboard_and_current_location_contracts(self):
        self.assertIn('class="skip-link" href="#main-content"', self.base)
        self.assertIn('id="main-content" tabindex="-1"', self.base)
        self.assertIn('aria-current="page"', self.base)
        self.assertIn('data-toast-region aria-live="polite"', self.base)

    def test_interaction_feedback_is_bounded_and_run_polling_is_active_only(self):
        self.assertNotIn("window.alert", self.script)
        self.assertIn("function showNotice", self.script)
        self.assertIn(
            'const activeStatuses = new Set(["queued", "running", "cancelling"]);',
            self.script,
        )

    def test_context_preview_updates_without_rebuilding_the_source_tree(self):
        for marker in (
            "data-context-explorer",
            "data-context-source-id",
            "data-context-document-link",
            "data-context-preview",
            "data-context-preview-status",
            'aria-current="page"',
        ):
            self.assertIn(marker, self.context)

        for behavior in (
            'treePane.addEventListener("click"',
            "new DOMParser()",
            "currentPreview.replaceWith(adoptedPreview)",
            "window.history.pushState",
            'window.addEventListener("popstate"',
            "AbortController",
            'link.setAttribute("aria-current", "page")',
            "selectedLink.focus({ preventScroll: true })",
        ):
            self.assertIn(behavior, self.script)

        self.assertIn(
            ".source-tree-document > a { height: auto; min-height: var(--control-min-height-touch); }",
            self.styles,
        )


if __name__ == "__main__":
    unittest.main()
