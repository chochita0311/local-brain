import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

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
            "VALUES ('codex-company', 'codex', 'Codex Company', ?)",
            (str(Path(self.directory.name) / "sessions"),),
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

    def test_runner_resolves_launcher_and_grants_only_runtime_file_read(self):
        choice = {
            "runner": "codex", "model": "synthetic-model",
            "codex_home": self.directory.name, "profile": "Synthetic",
        }
        install = Path(self.directory.name) / 'release "quoted" 한글'
        install.mkdir()
        binary = install / "codex"
        binary.write_text("synthetic executable placeholder")
        launcher = Path(self.directory.name) / "launcher"
        launcher.symlink_to(binary)
        with patch("localbrain.personal_insight_runs.settings", self.settings), patch(
            "localbrain.personal_insight_runs.runner_choices", return_value=[choice]
        ):
            run_id = prepare_insight_run(
                self.connection, mode="ask", question="설명 개선", runner="codex"
            )
            run = get_insight_run(self.connection, run_id)
            options = json.loads(run["settings_json"])
            self.assertEqual(options["policy_version"], "personal-insight-cli-v3-bootstrap")
            self.assertEqual(options["filesystem_access"], "run-artifacts-and-cli-read-only")
            for selected in (launcher, binary):
                with self.subTest(selected=selected.name):
                    args = _runner_args(run, str(selected))
                    self.assertEqual(args[0], str(binary.resolve()))
                    filesystem = next(arg for arg in args if arg.startswith("permissions.external-sync.filesystem="))
                    rules = tomllib.loads(filesystem)["permissions"]["external-sync"]["filesystem"]
                    self.assertEqual(rules, {
                        ":minimal": "read", ":workspace_roots": {".": "read"},
                        str(binary.resolve()): "read",
                    })
                    self.assertIn("permissions.external-sync.network.enabled=false", args)
                    self.assertIn('web_search="disabled"', args)
                    self.assertIn("--ephemeral", args)
                    self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", args)

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
            self.assertEqual(options["usage_source_key"], "codex-company")
            self.assertEqual(options["service_tier"], "standard")
            self.assertTrue(options["guide"]["playbooks"])
            self.assertEqual(len(options["guide"]["core_sha256"]), 64)
            prompt = Path(run["prompt_path"]).read_text(encoding="utf-8")
            self.assertIn("answer the person's actual question first", prompt)
            self.assertIn("# Configurable assistant behavior", prompt)
            self.assertIn('"message_index":0', prompt)
            self.assertIn('"message_count":1', prompt)
            args = _runner_args(run, "/synthetic/codex")
            self.assertIn("--output-schema", args)
            self.assertIn("--ephemeral", args)
            self.assertIn('service_tier="default"', args)
            self.assertEqual(args[args.index("-C") + 1], str(Path(run["stream_path"]).parent))
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
                "selection_reason": "이해 목표와 질문을 살펴보았다.",
                "selection_evidence_ids": ["codex-company:event-one"],
                "outcome": "needs_evidence",
                "findings": [],
                "no_finding_reason": "한 번의 질문은 정상적인 학습일 수 있다.",
                "additional_evidence": {
                    "kind": "independent_session",
                    "question": "다른 세션에서도 같은 상황이 있었나요?",
                    "evidence_ids": ["codex-company:event-one"],
                    "message_requests": [],
                },
                "limits": "현재 근거는 한 세션의 메시지 한 건이다.",
            }
            validated = _validate_result(value, manifest, run)
            report = _render_report(run, manifest, validated)
            self.assertIn(CORE_VERSION, report)
            self.assertIn("필요한 근거", report)
            self.assertIn("별도 세션의 사례", report)

            value["outcome"] = "findings"
            value["additional_evidence"] = {"kind": "none", "question": "", "evidence_ids": [], "message_requests": []}
            value["findings"] = [{
                "title": "다음 설명 방식 시험",
                "type_id": "learning_explanation",
                "type_reason": "설명 이해가 목표이며 설정에 대한 근거는 없다.",
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
            self.assertIn("이번에 살펴본 범위", finding_report)
            self.assertIn("이 후보를 살펴본 이유", finding_report)
            self.assertIn("이 유형을 고른 이유", finding_report)
            self.assertIn("확인 가능한 업무 세션 1개 중 1개", finding_report)
            self.assertIn("일부만 제공된 메시지: 0개", finding_report)

            value.update(outcome="needs_evidence", findings=[])
            manifest["sessions"][0]["message_count"] = 2
            value["additional_evidence"] = {
                "kind": "conversation_neighbors", "question": "이미 받은 질문을 다시 보내세요: UnwantedDuplicateRequest",
                "evidence_ids": ["codex-company:event-one"],
                "message_requests": [{"anchor_evidence_id": "codex-company:event-one", "message_index": 1}],
            }
            missing_report = _render_report(run, manifest, _validate_result(value, manifest, run))
            self.assertIn("범위 내 2번째 메시지의 전문", missing_report)
            self.assertIn("위치를 찾을 기준: 1번째 메시지", missing_report)
            self.assertNotIn("UnwantedDuplicateRequest", missing_report)
            self.assertIn(value["no_finding_reason"], missing_report)
            value["additional_evidence"]["message_requests"][0]["message_index"] = 0
            with self.assertRaisesRegex(ValueError, "이미 전문이 제공된 메시지"):
                _validate_result(value, manifest, run)
            value["additional_evidence"]["message_requests"][0]["message_index"] = 1

            # Frozen current schemas may not be silently overwritten on launch.
            schema_file = Path(run["stream_path"]).parent / "response-schema.json"
            schema_file.write_text('{}')
            with self.assertRaises(ValueError):
                _runner_args(run, "/synthetic/codex")
            schema_file.unlink()
            # Historical core v3 maps to its v2 schema, rather than the active schema.
            options["guide"]["core_version"] = "personal-improvement-core-v3"
            del options["guide"]["report_version"]
            run["settings_json"] = json.dumps(options)
            run["guide_version"] = "personal-improvement-core-v3"
            _runner_args(run, "/synthetic/codex")
            schema = json.loads(schema_file.read_text())
            self.assertEqual(schema["properties"]["result_version"]["enum"], ["personal-improvement-report-v2"])
            value["result_version"] = "personal-improvement-report-v2"
            del value["selection_reason"], value["selection_evidence_ids"]
            del value["additional_evidence"]["message_requests"]
            _validate_result(value, manifest, run)
            # Legacy reports still use their original free-text request rendering.
            legacy_report = _render_report(run, manifest, _validate_result(value, manifest, run))
            self.assertIn("UnwantedDuplicateRequest", legacy_report)


if __name__ == "__main__":
    unittest.main()
