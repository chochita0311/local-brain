"""Deterministic controls and failure-preserving replay, without loading a model."""

import copy
import io
import json
import runpy
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from localbrain.session_simulation import atomic_json, read_json
from localbrain.work_context_diagnostic import LIMITS, assess, diagnose, matrix, summarize, suite_identity
from localbrain.work_context_model import LocalGenerator, MODEL_8B, generation_settings
from localbrain.work_reconstruction import ExperimentError, digest
from work_context_diagnostic_cases import CASES


class Generator:
    def __init__(self, cases=CASES, behavior="correct"):
        self.cases, self.behavior, self.calls = cases, behavior, 0
        self.last_metrics, self.last_output = {}, ""
        self.contract = {"model": MODEL_8B, "device": "mps", "dtype": "bfloat16",
                         "attention": "eager", "fingerprint": "synthetic",
                         **generation_settings(max_tokens=4096, max_output=256, max_seconds=30)}

    def describe_prompt(self, system, content, codes):
        return {"prompt_sha256": digest([system, content]), "template_sha256": "synthetic",
                "input_tokens": 10, "answer_token_ids": {code: [i] for i, code in enumerate(codes)}}

    def answer(self, content):
        self.calls += 1
        if self.behavior == "interrupt" and self.calls == 2:
            raise KeyboardInterrupt()
        if self.behavior == "refuse":
            raise ExperimentError("OUTPUT_TRUNCATED")
        self.last_metrics = {"seconds": 1, "input_tokens": 10, "output_tokens": 2}
        packet = json.loads(content)
        case = next(c for c in self.cases if c["input"] == packet["context"])
        selected = next(o for o in packet["alternatives"] if o["label"] == case["expected"])
        return case, selected

    def choose(self, system, content, codes):
        return self.answer(content)[1]["answer"]

    def generate(self, system, content):
        case, selected = self.answer(content)
        messages = {m["id"]: m["text"] for m in case["input"]["messages"]}
        return "\n".join(["Decision: " + selected["label"], "Reason: 기록된 문장에 근거합니다."] + [
            "Evidence: " + key + " | " + messages[key] for key in case["evidence_ids"]])


class MatrixTests(unittest.TestCase):
    def test_fixed_twelve_cases_and_288_cells(self):
        cells = matrix(CASES)
        self.assertEqual(len(CASES), 12)
        self.assertEqual(len(cells), 288)
        self.assertEqual(len({c["id"] for c in cells}), 288)
        self.assertEqual(Counter(c["form"] for c in cells), {"numeric": 192, "label": 48, "text": 48})
        self.assertEqual(Counter(c["family"] for c in CASES), {"field": 6, "membership": 2, "relation": 4})

    def test_position_and_code_are_independently_balanced(self):
        for case in CASES:
            numeric = [c for c in matrix([case]) if c["form"] == "numeric"]
            for label, _ in case["options"]:
                pairs = [(i, option["answer"]) for cell in numeric
                         for i, option in enumerate(cell["options"]) if option["label"] == label]
                self.assertEqual(set(pairs), {(i, str(j)) for i in range(4) for j in range(4)})
                self.assertEqual(len(pairs), 16)

    def test_source_context_and_options_do_not_leak_expected_answers(self):
        cases = {case["id"]: case for case in CASES}
        for cell in matrix(CASES):
            packet = json.loads(cell["content"])
            self.assertEqual(set(packet), {"context", "alternatives"})
            self.assertEqual(packet["context"], cases[cell["case_id"]]["input"])
            self.assertEqual(packet["alternatives"], cell["options"])
            self.assertNotIn(cell["case_id"], cell["content"])
            self.assertNotIn("expected", packet)
            self.assertIsInstance(packet["alternatives"], list)

    def test_identity_covers_expected_prompt_and_matrix_changes(self):
        initial = suite_identity(CASES)
        changed = copy.deepcopy(CASES)
        changed[0]["expected"] = "none"
        self.assertNotEqual(initial, suite_identity(changed))
        with patch.dict("localbrain.work_context_diagnostic.FORMATS", {"text": "changed prompt"}):
            self.assertNotEqual(initial, suite_identity(CASES))
        self.assertEqual(initial, suite_identity(CASES))

    def test_semantic_protocol_and_grounding_are_separate(self):
        case = CASES[0]
        cell = next(c for c in matrix([case]) if c["form"] == "text")
        text = Generator([case]).generate(cell["system"], cell["content"])
        score = assess(case, cell, text)
        self.assertTrue(score["correct"] and score["protocol_valid"] and score["quote_grounded"])
        alternate = assess(case, cell, text.replace("Decision:", "Answer:"))
        self.assertTrue(alternate["correct"] and alternate["quote_grounded"])
        self.assertFalse(alternate["protocol_valid"])
        wrong_quote = assess(case, cell, text.replace("Evidence: m1 |", "Evidence: missing |"))
        self.assertTrue(wrong_quote["correct"] and wrong_quote["protocol_valid"])
        self.assertFalse(wrong_quote["quote_grounded"])

    def test_ambiguous_text_is_not_repaired_to_expected_answer(self):
        case = CASES[0]
        cell = next(c for c in matrix([case]) if c["form"] == "text")
        for output in ("intent or none", "Decision: intent\nDecision: none", "Decision: invented"):
            score = assess(case, cell, output)
            self.assertIsNone(score["decision"])
            self.assertFalse(score["correct"])

    def test_pair_requires_both_sides_and_unambiguous_exact_quotes(self):
        case = CASES[8]
        cell = next(c for c in matrix([case]) if c["form"] == "text")
        text = Generator([case]).generate(cell["system"], cell["content"])
        self.assertTrue(assess(case, cell, text)["quote_grounded"])
        self.assertFalse(assess(case, cell, "\n".join(text.splitlines()[:-1]))["quote_grounded"])
        self.assertFalse(assess(case, cell, text + "\n" + text.splitlines()[-1])["quote_grounded"])
        self.assertFalse(assess(case, cell, text.replace("구현했고", "발명했고"))["quote_grounded"])

    def test_constant_code_and_position_bias_are_distinguishable(self):
        case = CASES[0]
        cells = matrix([case])
        for rule, order_sensitive, code_sensitive in ((lambda c: "0", False, True),
                (lambda c: c["options"][0]["answer"], True, False)):
            observations = [{"id": c["id"], "output": rule(c), "error": None}
                            for c in cells if c["form"] == "numeric"]
            summary = summarize([case], cells, observations)
            result = summary["by_case"][case["id"]]
            self.assertEqual(result["order_sensitive"], order_sensitive)
            self.assertEqual(result["code_sensitive"], code_sensitive)
            self.assertEqual(result["by_form"]["numeric"]["correct"], 4)
            self.assertEqual(result["by_form"]["text"]["observed"], 0)

    def test_runtime_time_bound_keeps_default_unchanged(self):
        self.assertEqual(generation_settings()["max_seconds"], 180)
        self.assertEqual(generation_settings(max_seconds=30)["max_seconds"], 30)
        for value in (0, 181, True, 1.5):
            with self.assertRaisesRegex(ExperimentError, "INVALID_MODEL_CONFIG"):
                generation_settings(max_seconds=value)

    def test_runtime_audit_records_rendered_prompt_and_code_tokens(self):
        generator = LocalGenerator.__new__(LocalGenerator)
        generator._load = Mock()
        generator.contract = {"thinking": False}
        generator.tokenizer = SimpleNamespace(chat_template="frozen-template",
            apply_chat_template=Mock(return_value="rendered"), encode=lambda text, **_: list(text.encode()))
        result = generator.describe_prompt("system", "content", ["0", "intent"])
        self.assertEqual(result["prompt_sha256"], digest("rendered"))
        self.assertEqual(result["answer_token_ids"]["intent"], list(b"intent"))
        self.assertEqual(result["input_tokens"], 8)
        generator.tokenizer.apply_chat_template.assert_called_once_with(
            [{"role": "system", "content": "system"}, {"role": "user", "content": "content"}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False)


class StoreTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="work-protocol-test-", dir="/private/tmp")
        self.addCleanup(temp.cleanup)
        self.output = Path(temp.name).resolve() / "diagnostic"
        self.cases = CASES[:1]

    def test_complete_report_is_diagnostic_not_model_admission_and_replays(self):
        first = Generator(self.cases)
        report = diagnose(first, self.cases, self.output)
        self.assertEqual(first.calls, 24)
        self.assertEqual(report["state"], "complete")
        self.assertFalse(report["model_admission"] or report["private_corpus_examined"])
        self.assertNotIn("gate_passed", report)
        self.assertEqual(report["summary"]["by_form"]["numeric"]["correct"], 16)
        second = Generator(self.cases)
        replay = diagnose(second, self.cases, self.output)
        self.assertEqual(second.calls, 0)
        self.assertEqual(replay["reused"], 24)
        self.assertEqual(replay["observations"], report["observations"])
        self.assertEqual(replay["summary"], report["summary"])

    def test_generation_refusals_are_preserved_not_retried(self):
        first = Generator(self.cases, "refuse")
        report = diagnose(first, self.cases, self.output)
        self.assertEqual(report["summary"]["by_form"]["numeric"]["generation_ok"], 0)
        second = Generator(self.cases)
        replay = diagnose(second, self.cases, self.output)
        self.assertEqual(second.calls, 0)
        self.assertEqual(replay["summary"], report["summary"])

    def test_unrecognized_text_is_cached_without_repair_or_second_generation(self):
        first = Generator(self.cases)
        with patch.object(first, "generate", return_value="an ambiguous synthetic answer"):
            report = diagnose(first, self.cases, self.output)
        text = report["summary"]["by_form"]["text"]
        self.assertEqual((text["observed"], text["recognized"], text["correct"]), (4, 0, 0))
        second = Generator(self.cases)
        replay = diagnose(second, self.cases, self.output)
        self.assertEqual(second.calls, 0)
        self.assertEqual(replay["summary"], report["summary"])

    def test_clean_interruption_retains_reservation_and_resumes_only_missing_cells(self):
        first = Generator(self.cases, "interrupt")
        with self.assertRaises(KeyboardInterrupt):
            diagnose(first, self.cases, self.output)
        progress = read_json(self.output / "progress.json")
        self.assertEqual(progress["state"], "interrupted")
        self.assertEqual(progress["attempted_calls"], 2)
        self.assertEqual(len(progress["observations"]), 1)
        self.assertIsNone(progress["inflight"])
        second = Generator(self.cases)
        report = diagnose(second, self.cases, self.output)
        self.assertEqual(second.calls, 23)
        self.assertEqual(report["attempted_calls"], 25)
        self.assertEqual(report["reused"], 1)
        self.assertNotIn("error", report)
        self.assertNotIn("error", read_json(self.output / "progress.json"))

    def test_changed_cases_or_runtime_refuse_without_overwriting_observations(self):
        original = diagnose(Generator(self.cases), self.cases, self.output)
        changed = copy.deepcopy(self.cases)
        changed[0]["expected"] = "none"
        for cases, runtime in ((changed, Generator(changed)), (self.cases, Generator(self.cases))):
            if cases is self.cases:
                runtime.contract["fingerprint"] = "different"
            with self.assertRaisesRegex(ExperimentError, "DIAGNOSTIC_CONFIG_MISMATCH"):
                diagnose(runtime, cases, self.output)
            self.assertEqual(runtime.calls, 0)
            self.assertEqual(digest(read_json(self.output / "report.json")), digest(original))

    def test_corrupt_observation_is_not_silently_recomputed(self):
        diagnose(Generator(self.cases), self.cases, self.output)
        progress = read_json(self.output / "progress.json")
        progress["observations"][0]["output"] = "tampered"
        atomic_json(self.output / "progress.json", progress)
        generator = Generator(self.cases)
        with self.assertRaisesRegex(ExperimentError, "INVALID_CACHED_DIAGNOSTIC"):
            diagnose(generator, self.cases, self.output)
        self.assertEqual(generator.calls, 0)

    def test_hard_crash_does_not_reset_unknown_inflight_budget(self):
        diagnose(Generator(self.cases), self.cases, self.output)
        progress = read_json(self.output / "progress.json")
        progress.update(inflight="unfinished", elapsed_seconds=LIMITS["max_seconds"])
        atomic_json(self.output / "progress.json", progress)
        generator = Generator(self.cases)
        with self.assertRaisesRegex(ExperimentError, "DIAGNOSTIC_UNCLEAN_INTERRUPTION"):
            diagnose(generator, self.cases, self.output)
        self.assertEqual(generator.calls, 0)

    def test_elapsed_budget_is_enforced_after_a_call_and_on_resume(self):
        generator = Generator(self.cases)
        with patch.dict(LIMITS, {"max_seconds": 1}), patch(
                "localbrain.work_context_diagnostic.time.monotonic", side_effect=[0, 2]):
            with self.assertRaisesRegex(ExperimentError, "DIAGNOSTIC_BUDGET_EXHAUSTED"):
                diagnose(generator, self.cases, self.output)
            self.assertEqual(generator.calls, 1)
            progress = read_json(self.output / "progress.json")
            self.assertEqual(progress["state"], "budget-exhausted")
            self.assertEqual(len(progress["observations"]), 1)
            self.assertFalse((self.output / "report.json").exists())
            second = Generator(self.cases)
            with self.assertRaisesRegex(ExperimentError, "DIAGNOSTIC_BUDGET_EXHAUSTED"):
                diagnose(second, self.cases, self.output)
            self.assertEqual(second.calls, 0)

    def test_call_budget_stops_without_declaring_completion(self):
        with patch.dict(LIMITS, {"max_calls": 1}):
            generator = Generator(self.cases)
            with self.assertRaisesRegex(ExperimentError, "DIAGNOSTIC_BUDGET_EXHAUSTED"):
                diagnose(generator, self.cases, self.output)
            self.assertEqual(generator.calls, 1)
            self.assertFalse((self.output / "report.json").exists())

    def test_other_model_or_decoding_is_not_an_implicit_comparison(self):
        for change in ({"model": "Qwen/Qwen3-4B"}, {"decoding": "sampled"}, {"device": "cpu"}):
            generator = Generator(self.cases)
            generator.contract.update(change)
            with self.assertRaisesRegex(ExperimentError, "INVALID_DIAGNOSTIC_RUNTIME"):
                diagnose(generator, self.cases, self.output)
        self.assertFalse(self.output.exists())

    def test_cli_description_runs_without_model_and_rejects_private_inputs(self):
        script = Path(__file__).resolve().parents[1] / "scripts/diagnose-work-context-protocol.py"
        main = runpy.run_path(str(script))["main"]
        with redirect_stdout(io.StringIO()) as captured:
            self.assertEqual(main(["--describe"]), 0)
        self.assertEqual(json.loads(captured.getvalue())["conditions"], 288)
        with redirect_stdout(io.StringIO()) as captured:
            self.assertEqual(main(["--database", "/synthetic/private.db"]), 2)
        self.assertNotIn("private.db", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
