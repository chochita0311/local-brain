"""Matched roles, unchanged relationship controls, and bounded failure replay."""

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
from unittest.mock import patch

from localbrain.session_simulation import atomic_json, read_json
from localbrain.work_context_choices import validate_codes
from localbrain.work_context_evidence import PROMPTS, SUPPORT, SYSTEM, evidence_spans
from localbrain.work_context_model import MODEL_8B, generation_settings
from localbrain.work_reconstruction import ExperimentError, digest
from localbrain.work_role_comparison import (
    FIELDS, LIMITS, ROLE_SETS, compare, matrix, observation_hash, preflight_tokenizer,
    role_options, summarize, suite_identity,
)
from work_role_comparison_cases import CASES


class Generator:
    def __init__(self, cases=CASES, behavior="correct"):
        self.cases, self.behavior, self.calls = cases, behavior, 0
        self.last_metrics, self.last_output = {}, ""
        self.contract = {"model": MODEL_8B, "device": "mps", "dtype": "bfloat16",
                         "attention": "eager", "fingerprint": "synthetic",
                         **generation_settings(max_tokens=8192, max_output=128, max_seconds=30)}

    def describe_prompt(self, system, content, codes):
        return {"prompt_sha256": digest([system, content]), "template_sha256": "synthetic",
                "input_tokens": 10, "answer_token_ids": {code: [i] for i, code in enumerate(codes)}}

    def choose(self, system, content, codes, *, max_code_chars=8):
        validate_codes(codes, max_code_chars=max_code_chars)
        self.calls += 1
        self.last_metrics = {"seconds": 1, "input_tokens": 10, "output_tokens": 2}
        if self.behavior == "interrupt_always" or self.behavior == "interrupt" and self.calls == 2:
            raise KeyboardInterrupt()
        if self.behavior == "refuse":
            raise ExperimentError("OUTPUT_TRUNCATED")
        if self.behavior == "invalid":
            return "not-an-offered-label"
        prompt, serialized = content.split("\nINPUT:\n")
        packet = json.loads(serialized)
        self.assert_prompt_codes(packet, codes)
        case = next(c for c in self.cases if all(packet.get(k) == v for k, v in c["packet"].items()))
        if case["family"] == "role":
            if self.behavior == "wrong":
                answer = "supported" if "supported" in codes else "goal_progress_results_remaining"
            elif prompt in [PROMPTS[field] for field in FIELDS]:
                field = next(f for f in FIELDS if PROMPTS[f] == prompt)
                answer = "supported" if field in case["expected"] else "absent"
            else:
                answer = "_".join(f for f in FIELDS if f in case["expected"]) or "none"
        else:
            task = next(k for k, v in PROMPTS.items() if v == prompt)
            expected = case["expected"]
            if task == "basis":
                answer = {"uncertain": "insufficient", "continues": "same_goal", "related": "shared_topic",
                          "independent": "distinct_goals"}[expected]
            elif task == "scope":
                answer = "compatible"
            else:
                answer = "absent" if task == "goal" and expected in {"uncertain", "related"} else "supported"
        self.last_output = answer
        return answer

    @staticmethod
    def assert_prompt_codes(packet, codes):
        assert [o["answer"] for o in packet["alternatives"]] == codes


class MatrixTests(unittest.TestCase):
    def test_frozen_shape_and_complete_role_subsets(self):
        cells = matrix(CASES)
        self.assertEqual(Counter(c["family"] for c in CASES), {"role": 16, "relation": 6})
        self.assertEqual(len(cells), 166)
        self.assertEqual(Counter(c["method"] for c in cells),
                         {"properties": 128, "direct": 32, "unchanged-evidence": 6})
        self.assertEqual(len({c["id"] for c in cells}), 166)
        self.assertEqual(len(role_options()), 17)
        self.assertIn(("progress", "results"), ROLE_SETS.values())
        self.assertIn(("progress", "remaining"), ROLE_SETS.values())

    def test_matched_context_definitions_and_no_expected_answer_leak(self):
        for cell in matrix(CASES):
            if cell["family"] != "role":
                continue
            case = next(c for c in CASES if c["id"] == cell["case_id"])
            prompt, payload = cell["content"].split("\nINPUT:\n")
            data = json.loads(payload)
            self.assertEqual(set(data), {"messages", "focus", "alternatives"})
            self.assertEqual(data["messages"], case["packet"]["messages"])
            self.assertEqual(cell["system"], SYSTEM)
            self.assertNotIn(case["id"], cell["content"])
            self.assertEqual(data["alternatives"], cell["options"])
            self.assertIn(data["focus"], evidence_spans(case["packet"]["messages"]))
            if cell["method"] == "properties":
                self.assertEqual(prompt, PROMPTS[cell["field"]])
                if cell["order"] == 0:
                    self.assertEqual(cell["options"], [{"answer": a, "meaning": m} for a, m in SUPPORT])
            else:
                for field in FIELDS:
                    self.assertIn(PROMPTS[field], prompt)

    def test_reversal_changes_only_alternative_order(self):
        cells = matrix(CASES[:1])
        for method in ("direct", "properties"):
            for field in ("roles",) if method == "direct" else FIELDS:
                a, b = [c for c in cells if c["method"] == method and c["field"] == field]
                self.assertEqual(a["options"], list(reversed(b["options"])))
                x, y = [json.loads(c["content"].split("\nINPUT:\n")[1]) for c in (a, b)]
                x.pop("alternatives")
                y.pop("alternatives")
                self.assertEqual(x, y)

    def test_same_pending_focus_with_different_completion_scopes(self):
        a, b = CASES[10:12]
        self.assertEqual(a["focus"], b["focus"])
        self.assertEqual(a["expected"], [])
        self.assertEqual(b["expected"], ["remaining"])
        self.assertNotEqual(a["packet"], b["packet"])

    def test_identity_covers_expected_data_prompts_limits_and_control_pipeline(self):
        before = suite_identity(CASES)
        cases = copy.deepcopy(CASES)
        cases[0]["expected"] = []
        self.assertNotEqual(before, suite_identity(cases))
        with patch("localbrain.work_role_comparison.DIRECT", "new question"):
            self.assertNotEqual(before, suite_identity(CASES))
        with patch.dict(PROMPTS, {"scope": "changed relation premise"}):
            self.assertNotEqual(before, suite_identity(CASES))
        self.assertEqual(before, suite_identity(CASES))

    def test_invalid_focus_and_cases_fail_before_runtime(self):
        for change in ({"focus": {"message": "missing", "quote": "not there"}},
                       {"expected": ["made_up"]}, {"expected": ["goal", "goal"]}):
            with self.assertRaisesRegex(ExperimentError, "INVALID_CASES"):
                matrix([{**CASES[0], **change}])

    def test_tokenizer_preflight_checks_every_label_without_generation(self):
        vocabulary = {}

        def encode(text, **kwargs):
            vocabulary.setdefault(text, len(vocabulary) + 1)
            return [vocabulary[text]]

        tokenizer = SimpleNamespace(encode=encode, decode=lambda tokens, **kwargs:
                                    next(k for k, v in vocabulary.items() if v == tokens[0]))
        encoded = preflight_tokenizer(tokenizer, CASES)
        self.assertIn("goal_progress_results_remaining", encoded)
        self.assertIn("distinct_goals", encoded)
        self.assertIn("contradicted", encoded)
        with self.assertRaisesRegex(ExperimentError, "INVALID_CHOICES"):
            preflight_tokenizer(SimpleNamespace(encode=lambda *a, **k: list(range(9)), decode=lambda *a, **k: "bad"), CASES)

    def test_missing_uncertain_and_invalid_do_not_pass_as_empty_roles(self):
        case = CASES[9]
        cells = matrix([case])
        for output, error in (("uncertain", None), ("invalid", None), ("none", "refusal")):
            observations = [{"id": c["id"], "output": output, "error": error} for c in cells]
            summary = summarize([case], cells, observations)
            for method in ("properties", "direct"):
                self.assertEqual(summary["by_method"][method]["correct"], 0)
                self.assertEqual(summary["by_method"][method]["unresolved"], 2)
        self.assertEqual(summarize([case], cells, [])["paired"]["neither"], 2)

    def test_extra_roles_and_order_disagreements_remain_visible(self):
        case = CASES[0]
        cells = matrix([case])
        observations = []
        for cell in cells:
            output = ("goal" if cell["order"] == 0 else "goal_progress") if cell["method"] == "direct" else "supported"
            observations.append({"id": cell["id"], "output": output, "error": None})
        result = summarize([case], cells, observations)
        self.assertEqual(result["by_method"]["direct"]["correct"], 1)
        self.assertEqual(result["by_method"]["direct"]["order_sensitive"], 1)
        self.assertEqual(result["by_method"]["direct"]["both_orders_correct"], 0)
        self.assertEqual(result["by_method"]["properties"]["extra_roles"], 6)
        self.assertEqual(result["paired"], {"both_correct": 0, "direct_only": 1, "properties_only": 0, "neither": 1})

    def test_constant_abstention_and_empty_roles_are_not_composition_success(self):
        result = summarize(CASES, matrix(CASES), [])
        self.assertEqual(result["constant_baselines"], {
            "total": 32, "all_none_correct": 6, "all_roles_correct": 0, "all_uncertain_correct": 0})


class StoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="role-formulation-test-", dir="/private/tmp")
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name).resolve() / "comparison"
        self.cases = CASES[:1]

    def test_full_correct_synthetic_harness_and_separate_control_results(self):
        generator = Generator()
        result = compare(generator, CASES, self.output)
        self.assertEqual(len(result["observations"]), 166)
        self.assertEqual(result["attempted_calls"], generator.calls)
        self.assertFalse(result["model_admission"] or result["private_corpus_examined"])
        self.assertNotIn("gate_passed", result)
        for method in ("properties", "direct"):
            self.assertEqual(result["summary"]["by_method"][method]["correct"], 32)
        self.assertEqual(result["summary"]["relations"]["correct"], 6)
        self.assertEqual(result["summary"]["relations"]["false_continuations"], 0)
        for item in result["observations"]:
            self.assertEqual(len(item["audit"]), item["metrics"]["calls"])
        relation = result["observations"][-1]["result"]
        self.assertEqual({f["role"] for f in relation["evidence"]}, {"user"})

    def test_wrong_refused_and_invalid_observations_are_reused_without_calls(self):
        for behavior in ("correct", "wrong", "refuse", "invalid"):
            folder = self.output.parent / behavior
            first = compare(Generator(self.cases, behavior), self.cases, folder)
            generator = Generator(self.cases)
            replay = compare(generator, self.cases, folder)
            self.assertEqual(generator.calls, 0)
            self.assertEqual(replay["reused"], 10)
            for key in ("observations", "summary", "attempted_calls", "elapsed_seconds", "attempts"):
                self.assertEqual(first[key], replay[key])
            if behavior != "correct":
                self.assertEqual(replay["summary"]["by_method"]["properties"]["correct"], 0)

    def test_clean_interrupt_retains_spent_calls_and_only_resumes_missing(self):
        with self.assertRaises(KeyboardInterrupt):
            compare(Generator(self.cases, "interrupt"), self.cases, self.output)
        progress = read_json(self.output / "progress.json")
        self.assertEqual(progress["attempted_calls"], 2)
        self.assertEqual(len(progress["observations"]), 1)
        self.assertIsNone(progress["inflight"])
        generator = Generator(self.cases)
        result = compare(generator, self.cases, self.output)
        self.assertEqual((generator.calls, result["attempted_calls"], result["reused"]), (9, 11, 1))

    def test_incomplete_observation_has_at_most_two_attempts(self):
        for _ in range(2):
            with self.assertRaises(KeyboardInterrupt):
                compare(Generator(self.cases, "interrupt_always"), self.cases, self.output)
        generator = Generator(self.cases)
        with self.assertRaisesRegex(ExperimentError, "OBSERVATION_ATTEMPTS_EXHAUSTED"):
            compare(generator, self.cases, self.output)
        self.assertEqual(generator.calls, 0)
        self.assertEqual(read_json(self.output / "progress.json")["state"], "attempts-exhausted")

    def test_unchanged_control_pipeline_is_metered_and_invalid_result_is_not_repaired(self):
        cases = [CASES[-1]]
        generator = Generator(cases)
        result = compare(generator, cases, self.output)
        self.assertGreater(generator.calls, 1)
        self.assertEqual(result["attempted_calls"], generator.calls)
        self.assertTrue(result["observations"][0]["decisions"])
        other = self.output.parent / "refused-control"
        result = compare(Generator(cases, "refuse"), cases, other)
        self.assertEqual(result["summary"]["relations"]["correct"], 0)
        self.assertIsNone(result["observations"][0]["result"])

    def test_control_quotes_revalidate_even_if_a_corrupt_result_hash_is_rewritten(self):
        cases = [CASES[-1]]
        compare(Generator(cases), cases, self.output)
        progress = read_json(self.output / "progress.json")
        item = progress["observations"][0]
        item["result"]["evidence"][0]["quote"] = "invented evidence"
        item["sha256"] = observation_hash(item)
        atomic_json(self.output / "progress.json", progress)
        with self.assertRaises(ExperimentError):
            compare(Generator(cases), cases, self.output)

    def test_cumulative_call_limit_cannot_reset_on_resume(self):
        with patch.dict(LIMITS, {"max_calls": 1}):
            with self.assertRaisesRegex(ExperimentError, "COMPARISON_BUDGET_EXHAUSTED"):
                compare(Generator(self.cases), self.cases, self.output)
            self.assertFalse((self.output / "report.json").exists())
            generator = Generator(self.cases)
            with self.assertRaisesRegex(ExperimentError, "COMPARISON_BUDGET_EXHAUSTED"):
                compare(generator, self.cases, self.output)
            self.assertEqual(generator.calls, 0)

    def test_budget_before_first_call_does_not_manufacture_a_terminal_observation(self):
        with patch.dict(LIMITS, {"max_seconds": 1}), patch(
                "localbrain.work_role_comparison.time.monotonic", side_effect=[0, 2, 3]):
            with self.assertRaisesRegex(ExperimentError, "COMPARISON_BUDGET_EXHAUSTED"):
                compare(Generator(self.cases), self.cases, self.output)
        progress = read_json(self.output / "progress.json")
        self.assertEqual(progress["state"], "budget-exhausted")
        self.assertEqual(progress["attempted_calls"], 0)
        self.assertEqual(progress["observations"], [])

    def test_budget_reservation_exists_during_actual_choice(self):
        generator = Generator(self.cases)
        original = generator.choose

        def inspected(*args, **kwargs):
            progress = read_json(self.output / "progress.json")
            self.assertIsNotNone(progress["inflight"])
            self.assertEqual(progress["elapsed_seconds"], LIMITS["max_seconds"])
            return original(*args, **kwargs)

        with patch.object(generator, "choose", side_effect=inspected):
            compare(generator, self.cases, self.output)

    def test_runtime_or_case_changes_refuse_without_replacing_old_report(self):
        original = compare(Generator(self.cases), self.cases, self.output)
        before = digest(original)
        for kind in ("case", "runtime"):
            cases = copy.deepcopy(self.cases)
            if kind == "case":
                cases[0]["expected"] = []
            generator = Generator(cases)
            if kind == "runtime":
                generator.contract["fingerprint"] = "changed"
            with self.assertRaisesRegex(ExperimentError, "COMPARISON_CONFIG_MISMATCH"):
                compare(generator, cases, self.output)
            self.assertEqual(generator.calls, 0)
            self.assertEqual(digest(read_json(self.output / "report.json")), before)

    def test_corrupt_and_unclean_progress_refuse_before_generation(self):
        for failure in ("hash", "inflight", "attempts"):
            folder = self.output.parent / failure
            compare(Generator(self.cases), self.cases, folder)
            progress = read_json(folder / "progress.json")
            if failure == "hash":
                progress["observations"][0]["output"] = "changed"
            elif failure == "inflight":
                progress["inflight"] = "unknown-duration"
            else:
                progress["attempts"][matrix(self.cases)[0]["id"]] = 3
            atomic_json(folder / "progress.json", progress)
            generator = Generator(self.cases)
            with self.assertRaises(ExperimentError):
                compare(generator, self.cases, folder)
            self.assertEqual(generator.calls, 0)

    def test_other_models_devices_and_decoding_fail_before_output_creation(self):
        for change in ({"model": "Qwen/Qwen3-4B"}, {"device": "cpu"}, {"decoding": "sampled"}, {"thinking": True}):
            generator = Generator(self.cases)
            generator.contract.update(change)
            with self.assertRaisesRegex(ExperimentError, "INVALID_EVIDENCE_RUNTIME"):
                compare(generator, self.cases, self.output)
        self.assertFalse(self.output.exists())

    def test_cli_description_is_model_free_and_has_no_private_or_tuning_flags(self):
        path = Path(__file__).resolve().parents[1] / "scripts/compare-work-role-formulations.py"
        main = runpy.run_path(str(path))["main"]
        with redirect_stdout(io.StringIO()) as captured:
            self.assertEqual(main(["--describe"]), 0)
        self.assertEqual(json.loads(captured.getvalue())["observations"], 166)
        for flag in ("--database", "--input", "--split", "--device", "--strategy", "--thinking"):
            with redirect_stdout(io.StringIO()) as captured:
                self.assertEqual(main([flag, "private-sentinel"]), 2)
            self.assertNotIn("private-sentinel", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
