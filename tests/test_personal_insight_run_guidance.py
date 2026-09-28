import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from localbrain.personal_insight_guidance import CORE_VERSION, REPORT_VERSION
from localbrain.personal_insight_runs import (
    _render_report,
    _runner_args,
    _validate_result,
    get_insight_run,
    prepare_insight_run,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class PersonalInsightRunGuidanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="localbrain-insight-guidance-")
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        source_id = self.connection.execute(
            "INSERT INTO sources(kind, provider_kind, name, root_path) "
            "VALUES ('codex-company', 'codex', 'Codex Company', '/synthetic')"
        ).lastrowid
        session_id = self.connection.execute(
            "INSERT INTO sessions(source_id, external_id, source_path, title) "
            "VALUES (?, 'session-one', '/synthetic/one.jsonl', 'Synthetic')",
            (source_id,),
        ).lastrowid
        self.connection.execute(
            """INSERT INTO activity_events(
                id, session_id, sequence, occurred_at, event_type, role, text, source_line
            ) VALUES ('event-one', ?, 1, '2026-09-27T12:00:00Z', 'message', 'user',
                      '왜 이 개념을 이해하기 어렵지?', 1)""",
            (session_id,),
        )
        self.settings = SimpleNamespace(
            data_dir=Path(self.directory.name), timezone_name="Asia/Seoul"
        )

    def tearDown(self):
        self.connection.close()
        self.directory.cleanup()

    def test_prepare_freezes_selected_guides_and_report_uses_run_version(self):
        choice = {
            "runner": "codex", "label": "Codex CLI · Synthetic",
            "model": "synthetic-model", "codex_home": self.directory.name,
            "profile": "Synthetic",
        }
        with patch("localbrain.personal_insight_runs.settings", self.settings), patch(
            "localbrain.personal_insight_runs.runner_choices", return_value=[choice]
        ):
            run_id = prepare_insight_run(
                self.connection, mode="ask", question="왜 설명을 다시 물어보지?", runner="codex"
            )
            run = get_insight_run(self.connection, run_id)
            self.assertEqual(run["guide_version"], CORE_VERSION)
            options = json.loads(run["settings_json"])
            self.assertTrue(options["guide"]["playbooks"])
            self.assertEqual(len(options["guide"]["core_sha256"]), 64)
            prompt = Path(run["prompt_path"]).read_text(encoding="utf-8")
            self.assertIn("answer the person's actual question first", prompt)
            self.assertNotIn("# Configurable assistant behavior", prompt)
            args = _runner_args(run, "/synthetic/codex")
            self.assertIn("--output-schema", args)
            schema = json.loads(
                (Path(self.directory.name) / "personal-insight-runs" / run_id / "response-schema.json")
                .read_text(encoding="utf-8")
            )
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(schema["properties"]["result_version"]["enum"], [REPORT_VERSION])

            manifest = json.loads(Path(run["evidence_path"]).read_text(encoding="utf-8"))
            value = {
                "result_version": REPORT_VERSION,
                "title": "추가 근거가 필요한 분석",
                "summary": "현재 발췌만으로 반복 패턴을 확인할 수 없다.",
                "outcome": "needs_evidence",
                "findings": [],
                "no_finding_reason": "",
                "additional_evidence": {
                    "kind": "independent_session",
                    "question": "다른 세션에서도 같은 상황이 있었나요?",
                    "evidence_ids": ["codex-company:event-one"],
                },
                "limits": "현재 근거는 한 세션의 메시지 한 건이다.",
            }
            validated = _validate_result(value, manifest, run)
            report = _render_report(run, manifest, validated)
            self.assertIn(CORE_VERSION, report)
            self.assertIn("필요한 근거", report)
            self.assertIn("별도 세션의 사례", report)

            value["outcome"] = "findings"
            value["additional_evidence"] = {"kind": "none", "question": "", "evidence_ids": []}
            value["findings"] = [{
                "title": "다음 설명 방식 시험",
                "type_id": options["guide"]["playbooks"][0]["id"],
                "owner_goal": "개념 이해",
                "pattern_scope": "single_observation",
                "observation": "설명을 다시 요청했다.",
                "evidence_ids": ["codex-company:event-one"],
                "counterevidence_ids": [],
                "counterexample_status": "not_observed",
                "counterexample_check": "정상적으로 이해한 사례가 있는지 표본을 살펴봤다.",
                "alternative": "정상적인 탐구일 수 있다.",
                "coverage_limit": "대화 전후 맥락이 없다.",
                "action": "짧은 예시를 요청해 본다.",
                "benefit_hypothesis": "개념 적용이 쉬워질 수 있다.",
                "effort_or_tradeoff": "추가 대화가 필요하다.",
                "follow_up": "다른 예시에 적용해 본다.",
                "handoff": {
                    "goal": "개념 이해",
                    "proposed_change": "예시 요청",
                    "scope": "다음 학습 세션",
                    "constraints": "출처를 확인",
                    "first_steps": "예시를 한 개 요청",
                    "success_check": "다른 예시에 적용",
                },
                "outcome_state": "not_confirmed",
            }]
            finding_result = _validate_result(value, manifest, run)
            finding_report = _render_report(run, manifest, finding_result)
            self.assertIn("제안 ID", finding_report)
            self.assertIn("반대 사례를 확인한 방법", finding_report)
            self.assertIn("한 번 관찰", finding_report)
            self.assertIn("/sessions/", finding_report)
            self.assertIn("다음 설명 방식 시험", finding_report)


if __name__ == "__main__":
    unittest.main()
