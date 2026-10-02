import json
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from starlette.requests import Request

from localbrain.main import _session_insights_response


class PersonalInsightUIReferenceTests(unittest.TestCase):
    def test_candidate_and_request_anchors_are_rechecked_without_a_model_call(self):
        with tempfile.TemporaryDirectory(prefix="localbrain-insight-ui-") as root:
            root = Path(root)
            events = [{"source_key": "synthetic", "event_id": str(i), "session_id": 7} for i in (1, 2)]
            manifest = {"sessions": [{"session_id": 7, "events": events}]}
            result = {
                "findings": [], "selection_evidence_ids": ["synthetic:1"],
                "additional_evidence": {"evidence_ids": ["synthetic:1", "synthetic:2"]},
            }
            (root / "evidence.json").write_text(json.dumps(manifest))
            (root / "response.json").write_text(json.dumps(result))
            report = "# Saved report\n\n[Session](/sessions/7)\n\n[Unadmitted](/sessions/99)\n"
            (root / "report.md").write_text(report)
            run = {
                "id": "example",
                "status": "no_finding", "report_path": str(root / "report.md"),
                "evidence_path": str(root / "evidence.json"), "response_path": str(root / "response.json"),
                "coverage_json": "{}", "settings_json": "{}", "usage_json": None,
            }

            @contextmanager
            def connection():
                yield object()

            def resolve(_connection, event):
                return {"status": "stale" if event["event_id"] == "1" else "unavailable"}

            with patch("localbrain.main.connect", connection), patch(
                "localbrain.main.skill_insights_data", return_value={}
            ), patch("localbrain.main.list_insight_runs", return_value=[]), patch(
                "localbrain.main.get_insight_run", return_value=run
            ), patch("localbrain.main.insight_usage_cost", return_value=None), patch("localbrain.main.resolve_insight_evidence_reference", side_effect=resolve) as resolver, patch(
                "localbrain.main.insight_runner_choices", return_value=[]
            ), patch("localbrain.main.templates.TemplateResponse", side_effect=lambda _name, context, **kwargs: context), patch(
                "localbrain.personal_insight_runs.prepare_insight_run"
            ) as prepare:
                context = _session_insights_response(Request({"type": "http", "query_string": b""}), selected_id="example")
                self.assertEqual(context["reference_states"], {"current": 0, "stale": 1, "unavailable": 1})
                self.assertEqual(resolver.call_count, 2)
                self.assertIn('href="/sessions/7"', context["report_html"])
                self.assertNotIn('href="/sessions/99"', context["report_html"])
                prepare.assert_not_called()
                self.assertEqual((root / "report.md").read_text(), report)


if __name__ == "__main__":
    unittest.main()
