"""Synthetic tests for protocol isolation, bounded staging and split admission."""

import json
import sys
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from localbrain.work_context import infer, inference_identity
from localbrain.work_context_evaluation import evaluate
from localbrain.work_context_model import MODEL_ID, REVISION, LocalGenerator, final_token_ids, generation_settings
from localbrain.work_context_staged import INVENTORY
from localbrain.work_reconstruction import ExperimentError
from test_work_context import FakeGenerator, fact, unit
from work_context_cases import message


class RecordingGenerator(FakeGenerator):
    def __init__(self, outputs):
        super().__init__(outputs)
        self.prompts = []

    def generate(self, system, content):
        self.prompts.append((system, content))
        self.last_metrics = {"seconds": 1, "input_tokens": 3, "output_tokens": 2,
                             "max_rss_native": 10, "rss_unit": "bytes"}
        return super().generate(system, content)


class ProtocolTests(unittest.TestCase):
    def test_mps_uses_eager_without_modifying_dependencies_or_assets(self):
        torch = SimpleNamespace(__version__="synthetic", backends=SimpleNamespace(
            mps=SimpleNamespace(is_available=lambda: True)))
        with patch.dict(sys.modules, {"torch": torch, "transformers": SimpleNamespace(__version__="synthetic")}), \
             patch("localbrain.work_context_model.verify", return_value=(Path("/synthetic"), {
                 "fingerprint": "synthetic", "model_id": MODEL_ID, "revision": REVISION})), \
             patch("localbrain.work_context_model.offline_environment"), \
             patch("localbrain.work_context_model.block_network"):
            mps = LocalGenerator(Path("/synthetic"))
            cpu = LocalGenerator(Path("/synthetic"), device="cpu")
        self.assertEqual(mps.contract["attention"], "eager")
        self.assertEqual(cpu.contract["attention"], "sdpa")
        self.assertNotEqual(inference_identity(mps.contract), inference_identity(cpu.contract))

    def test_generator_never_decodes_reasoning_or_truncated_output(self):
        class Tokens(list):
            def __getitem__(self, key):
                result = super().__getitem__(key)
                return Tokens(result) if isinstance(key, slice) else result

            def tolist(self):
                return list(self)

        class Inputs(dict):
            def to(self, device):
                return self

        for completion, expected in (([151667, 11, 151668, 21, 99], "final"),
                                     ([151667, 11, 151668, 21], None), ([151667, 11, 99], None)):
            generator = LocalGenerator.__new__(LocalGenerator)
            generator.contract = {**generation_settings(thinking=True, decoding="sampled"), "device": "cpu"}
            generator._load = lambda: None
            generator.last_output = "stale answer must be cleared"
            generator.tokenizer = Mock()
            generator.tokenizer.return_value = Inputs(input_ids=SimpleNamespace(shape=(1, 3)))
            generator.tokenizer.eos_token_id = 99
            generator.tokenizer.decode.return_value = "final"
            generator.model = SimpleNamespace(generation_config=SimpleNamespace(eos_token_id=[99]),
                                              generate=lambda **_: [Tokens([1, 2, 3] + completion)])
            torch = SimpleNamespace(inference_mode=nullcontext, manual_seed=lambda _: None)
            with patch.dict(sys.modules, {"torch": torch}):
                if expected:
                    self.assertEqual(generator.generate("system", "synthetic"), expected)
                    generator.tokenizer.decode.assert_called_once_with([21, 99], skip_special_tokens=True)
                else:
                    with self.assertRaises(ExperimentError):
                        generator.generate("system", "synthetic")
                    generator.tokenizer.decode.assert_not_called()
                    self.assertEqual(generator.last_output, "")

    def test_thinking_returns_only_final_tokens(self):
        self.assertEqual(final_token_ids([151667, 11, 12, 151668, 21, 99],
                                        thinking=True, eos={99}), ([21, 99], 4))

    def test_missing_duplicate_or_empty_thinking_end_is_rejected(self):
        for tokens in ([11, 99], [151668, 21, 151668, 22, 99], [151668, 99]):
            with self.subTest(tokens=tokens), self.assertRaisesRegex(ExperimentError, "INVALID_THINKING_PROTOCOL"):
                final_token_ids(tokens, thinking=True, eos={99})

    def test_truncated_reasoning_or_answer_is_not_returned(self):
        for tokens in ([], [151667, 12], [12, 151668, 21]):
            with self.assertRaisesRegex(ExperimentError, "OUTPUT_TRUNCATED"):
                final_token_ids(tokens, thinking=True, eos={99})

    def test_non_thinking_cannot_leak_unexpected_reasoning(self):
        self.assertEqual(final_token_ids([21, 99], thinking=False, eos={99}), ([21, 99], 0))
        for token in (151667, 151668):
            with self.assertRaisesRegex(ExperimentError, "INVALID_THINKING_PROTOCOL"):
                final_token_ids([token, 21, 99], thinking=False, eos={99})

    def test_settings_are_bounded_and_identity_separated(self):
        plain = generation_settings(decoding="sampled")
        thinking = generation_settings(thinking=True, decoding="sampled")
        self.assertEqual((plain["max_tokens"], plain["max_output"]), (8192, 2048))
        self.assertEqual((thinking["max_tokens"], thinking["max_output"]), (16384, 8192))
        self.assertEqual(thinking["sampling"]["temperature"], 0.6)
        self.assertNotEqual(inference_identity(plain), inference_identity(thinking))
        for options in ({"thinking": True}, {"thinking": 1}, {"max_tokens": 32768},
                        {"max_output": 8192}, {"max_tokens": 2048, "max_output": 2048}):
            with self.assertRaises(ExperimentError):
                generation_settings(**options)


class StagedTests(unittest.TestCase):
    def setUp(self):
        # Two goals in one message and a follow-up in another: never 1:1 mapping.
        self.messages = [message("a1", "중복 청구를 막자. 별도로 검색 개선."),
                         message("a2", "청구 수정 완료. 동시 테스트는 남음.", "assistant")]

    def test_two_goals_in_one_message_keep_followup_and_source_roles(self):
        a, b = fact(), fact("a1", "검색 개선")
        first = {**unit(a), "results": [fact("a2", "청구 수정 완료")],
                 "remaining": [fact("a2", "동시 테스트는 남음")]}
        generator = RecordingGenerator([{"anchors": [a, b]}, {"units": [first]}, {"units": [unit(b)]}])
        result = infer(generator, "extract", {"messages": self.messages}, strategy="staged")
        self.assertEqual(len(result["units"]), 2)
        self.assertEqual(result["units"][0]["results"][0]["role"], "assistant")
        self.assertEqual(generator.last_metrics["calls"], 3)
        self.assertEqual(generator.last_metrics["output_tokens"], 6)
        self.assertEqual(generator.last_metrics["seconds"], 3)
        for _, prompt in generator.prompts:
            self.assertIn("청구 수정 완료", prompt)

    def test_no_work_stops_after_inventory(self):
        generator = RecordingGenerator([{"anchors": []}])
        result = infer(generator, "extract", {"messages": self.messages}, strategy="staged")
        self.assertEqual(result["units"], [])
        self.assertEqual(generator.calls, 1)

    def test_unknown_goal_can_keep_activity_anchor_without_invention(self):
        a = fact("a2", "청구 수정 완료")
        output = {"goal": None, "target": None, "progress": [a], "results": [], "remaining": []}
        result = infer(RecordingGenerator([{"anchors": [a]}, {"units": [output]}]),
                       "extract", {"messages": self.messages}, strategy="staged")
        self.assertIsNone(result["units"][0]["goal"])

    def test_fabricated_duplicate_or_oversized_inventory_stops_before_detail(self):
        for anchors in ([fact("absent")], [fact(), fact()], [fact()] * 9):
            generator = RecordingGenerator([{"anchors": anchors}])
            with self.assertRaises(ExperimentError):
                infer(generator, "extract", {"messages": self.messages}, strategy="staged")
            self.assertEqual(generator.calls, 1)

    def test_detail_cannot_erase_anchor_or_merge_unrelated_units(self):
        for output in ({"units": [unit(fact("a1", "검색 개선"))]}, {"units": []},
                       {"units": [unit(), unit(fact("a1", "검색 개선"))]}):
            generator = RecordingGenerator([{"anchors": [fact()]}, output])
            with self.assertRaises(ExperimentError):
                infer(generator, "extract", {"messages": self.messages}, strategy="staged")
            self.assertEqual(generator.last_metrics["stages"][-1]["stage"], "detail-1")

    def test_pair_selection_must_belong_to_named_side(self):
        packet = {"left": self.messages[:1], "right": self.messages[1:]}
        generator = RecordingGenerator([{"left": [fact("a2", "청구 수정 완료")], "right": []}])
        with self.assertRaises(ExperimentError):
            infer(generator, "relate", packet, strategy="staged")
        self.assertEqual(generator.calls, 1)

    def test_pair_evidence_is_not_automatically_filled_into_verdict(self):
        a, b = fact(), fact("a2", "청구 수정 완료")
        generator = RecordingGenerator([{"left": [a], "right": [b]},
                    {"relation": "independent", "evidence": [b], "link": None}])
        with self.assertRaisesRegex(ExperimentError, "INVALID_EVIDENCE"):
            infer(generator, "relate", {"left": self.messages[:1], "right": self.messages[1:]}, strategy="staged")
        self.assertEqual(generator.last_metrics["calls"], 2)

    def test_strategy_and_stage_prompt_changes_invalidate_identity(self):
        baseline = inference_identity({}, "staged")
        self.assertNotEqual(baseline, inference_identity({}, "single"))
        with patch("localbrain.work_context_staged.PROMPTS", [INVENTORY + "changed"]):
            self.assertNotEqual(baseline, inference_identity({}, "staged"))

    def test_invalid_packet_or_strategy_never_calls_model(self):
        generator = RecordingGenerator([])
        for strategy, packet in (("unknown", {"messages": self.messages}), ("staged", {"messages": []})):
            with self.assertRaises(ExperimentError):
                infer(generator, "extract", packet, strategy=strategy)
        self.assertEqual(generator.calls, 0)


class StrategyEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="context-strategy-test-", dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name).resolve() / "evaluation"
        self.cases = [{"id": str(i), "kind": "extract", "split": "development", "negative": bool(i),
                       "packet": {"messages": [message("a1", "합성")]}} for i in range(2)]

    def test_staged_checkpoint_reuse_and_strategy_invalidation(self):
        assessor = lambda case, result: {"empty": not result["units"]}
        generator = RecordingGenerator([{"anchors": []}])
        evaluate(generator, self.cases, assessor, self.folder, strategy="staged")
        resumed = RecordingGenerator([])
        result = evaluate(resumed, self.cases, assessor, self.folder, strategy="staged")
        self.assertEqual(result["reused"], 2)
        self.assertEqual(resumed.calls, 0)
        changed = RecordingGenerator([{"units": []}])
        result = evaluate(changed, self.cases, assessor, self.folder)
        self.assertEqual(result["reused"], 0)

    def test_interrupted_stage_is_not_cached_as_complete_case(self):
        generator = FakeGenerator([{"anchors": [fact("a1", "합성")]}], fail_after=1)
        with self.assertRaises(KeyboardInterrupt):
            evaluate(generator, self.cases, lambda *_: {}, self.folder, strategy="staged")
        resumed = RecordingGenerator([{"anchors": []}])
        result = evaluate(resumed, self.cases, lambda *_: {"valid": True}, self.folder, strategy="staged")
        self.assertEqual(result["reused"], 0)
        self.assertEqual(resumed.calls, 2)

    def test_combined_split_score_cannot_hide_failed_split(self):
        cases = self.cases + [{**self.cases[0], "id": "holdout-" + str(i), "split": "holdout",
                               "negative": i == 9} for i in range(10)]
        result = evaluate(RecordingGenerator([{"units": []}]), cases,
                          lambda case, _: {"expected": case["id"] != "0"}, self.folder)
        self.assertEqual(result["positive_passed"], 9)
        self.assertEqual(result["positive_total"], 10)
        self.assertEqual(result["split_gates"], {"development": False, "holdout": True})
        self.assertFalse(result["gate_passed"])


if __name__ == "__main__":
    unittest.main()
