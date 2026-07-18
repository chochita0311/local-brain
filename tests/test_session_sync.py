import unittest
from unittest.mock import patch

from localbrain.ingest import scanner
from localbrain.main import sync_session_sources, sync_sessions_page


class SessionSyncTests(unittest.TestCase):
    def test_session_scan_report_contains_only_claude_and_codex(self):
        with patch.object(
            scanner,
            "_scan_session_source",
            side_effect=((2, 3, 0), (1, 4, 0)),
        ) as scan_source, patch.object(
            scanner, "_scan_context_documents"
        ) as scan_context:
            report = scanner._scan_session_sources(object())

        self.assertEqual(set(report), {"claude", "codex"})
        self.assertEqual(report["claude"], {"imported": 2, "skipped": 3, "failed": 0})
        self.assertEqual(report["codex"], {"imported": 1, "skipped": 4, "failed": 0})
        self.assertEqual(scan_source.call_count, 2)
        scan_context.assert_not_called()

    def test_sessions_sync_endpoint_uses_session_only_scanner(self):
        expected = {
            "claude": {"imported": 1, "skipped": 0, "failed": 0},
            "codex": {"imported": 0, "skipped": 1, "failed": 0},
        }
        with patch("localbrain.main.scan_session_sources", return_value=expected):
            self.assertEqual(
                sync_session_sources(),
                {"ok": True, "report": expected},
            )

    def test_sessions_sync_form_fallback_preserves_inventory_scope(self):
        with patch("localbrain.main.scan_session_sources") as scan_sources:
            projects = sync_sessions_page(view="projects")
            sessions = sync_sessions_page(
                view="sessions", source="codex", workspace=7, page=3
            )

        self.assertEqual(projects.status_code, 303)
        self.assertEqual(projects.headers["location"], "/projects")
        self.assertEqual(sessions.status_code, 303)
        self.assertEqual(
            sessions.headers["location"],
            "/sessions?source=codex&workspace=7&page=3",
        )
        self.assertEqual(scan_sources.call_count, 2)


if __name__ == "__main__":
    unittest.main()
