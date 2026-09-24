"""Synthetic source-choice contracts; passing grammar is not semantic quality."""

import tempfile
import sys
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from localbrain.work_context import infer, inference_identity
from localbrain.work_context_choices import ChoiceTrie, validate_codes
from localbrain.work_context_classified import CONTRACT, source_spans
from localbrain.work_context_evaluation import evaluate
from localbrain.work_context_model import LocalGenerator, generation_settings
from localbrain.work_reconstruction import ExperimentError
from work_context_cases import message


class ChoiceGenerator:
    contract = {"model": "synthetic", "thinking": False, "decoding": "greedy"}

    def __init__(self, answers):
        self.answers = iter(answers)
        self.calls = []
        self.last_output = ""
        self.last_metrics = {}

    def choose(self, system, content, codes):
        self.calls.append((system, content, codes))
        answer = next(self.answers)
        if isinstance(answer, BaseException):
            raise answer
        self.last_output = str(answer)
        self.last_metrics = {"seconds": 1, "input_tokens": 30, "output_tokens": 2}
        return self.last_output


class ChoiceTrieTests(unittest.TestCase):
    def test_codes_are_bounded_before_model_loading_or_tokenization(self):
        for codes in (None, [], [["not-a-code"]], ["0", "0"], ["a" * 10000],
                      [str(i) for i in range(129)]):
            with self.assertRaisesRegex(ExperimentError, "INVALID_CHOICES"):
                validate_codes(codes)

    def test_prefix_alternatives_and_eos_are_exact(self):
        trie = ChoiceTrie({"a": [1], "ab": [1, 2], "b": [3]}, {99})
        self.assertEqual(trie.allowed([]), [1, 3])
        self.assertEqual(trie.allowed([1]), [2, 99])
        self.assertEqual(trie.allowed([1, 2]), [99])
        self.assertEqual(trie.max_output, 3)
        self.assertEqual(trie.answer([1, 99]), "a")
        self.assertEqual(trie.answer([1, 2, 99]), "ab")

    def test_unoffered_or_incomplete_answer_is_rejected(self):
        trie = ChoiceTrie({"answer": [1, 2]}, {99})
        for tokens in ([], [1, 2], [1, 99], [5, 99], [1, 2, 99, 99]):
            with self.subTest(tokens=tokens), self.assertRaises(ExperimentError):
                trie.answer(tokens)

    def test_invalid_or_colliding_choices_are_rejected(self):
        for encoded in ({}, {"a": []}, {"a": [99]}, {"a": [1] * 9},
                        {"a": [1], "b": [1]}, {"unbounded-code": [1]},
                        {str(i): [i + 1000] for i in range(129)}):
            with self.subTest(encoded=encoded), self.assertRaises(ExperimentError):
                ChoiceTrie(encoded, {99})

    def test_real_adapter_constrains_every_token_and_requires_eos(self):
        class Tokens(list):
            def __getitem__(self, key):
                result = super().__getitem__(key)
                return Tokens(result) if isinstance(key, slice) else result

            def tolist(self):
                return list(self)

        class Inputs(dict):
            def to(self, device):
                return self

        variants = [(codes, limit, completion, error)
                    for codes, limit in ((["0", "1"], 8), (["absent", "supported"], 32))
                    for completion, error in (([12, 99], None), ([12], "OUTPUT_TRUNCATED"),
                                              ([13, 99], "INVALID_CHOICE_OUTPUT"))]
        for codes, limit, completion, error in variants:
            generator = LocalGenerator.__new__(LocalGenerator)
            generator.contract = {**generation_settings(), "device": "cpu"}
            generator._load = lambda: None
            generator.tokenizer = Mock()
            generator.tokenizer.encode.side_effect = lambda code, **_: [11 if code == codes[0] else 12]
            generator.tokenizer.decode.side_effect = lambda tokens, **_: codes[0] if tokens == [11] else codes[1]
            generator.tokenizer.return_value = Inputs(input_ids=SimpleNamespace(shape=(1, 3)))
            generator.tokenizer.eos_token_id = 99

            def generate(**kwargs):
                self.assertFalse(kwargs["do_sample"])
                self.assertEqual(kwargs["max_new_tokens"], 2)
                allowed = kwargs["prefix_allowed_tokens_fn"]
                self.assertEqual(allowed(0, Tokens([1, 2, 3])), [11, 12])
                self.assertEqual(allowed(0, Tokens([1, 2, 3, 12])), [99])
                return [Tokens([1, 2, 3] + completion)]

            generator.model = SimpleNamespace(generation_config=SimpleNamespace(eos_token_id=[99]), generate=generate)
            with patch.dict(sys.modules, {"torch": SimpleNamespace(inference_mode=nullcontext)}):
                options = {} if limit == 8 else {"max_code_chars": limit}
                if error:
                    with self.assertRaisesRegex(ExperimentError, error):
                        generator.choose("system", "synthetic", codes, **options)
                    self.assertEqual(generator.last_output, "")
                else:
                    self.assertEqual(generator.choose("system", "synthetic", codes, **options), codes[1])
            # Only the caller-supplied code vocabulary is decoded, never model reasoning.
            self.assertEqual(generator.tokenizer.decode.call_count, 2)


class ClassifiedTests(unittest.TestCase):
    def extract(self, messages, answers):
        generator = ChoiceGenerator(answers)
        result = infer(generator, "extract", {"messages": messages}, strategy="classified")
        return result, generator

    def test_two_goals_in_one_message_join_followup_from_another(self):
        messages = [message("a", "중복 청구를 막자. 별도로 검색을 개선하자."),
                    message("b", "청구 코드를 수정했고 확인을 마쳤다. 동시 요청 검증은 남았다.", "assistant")]
        result, generator = self.extract(messages, [1, 1, 0, 4, 1, 5, 1, 1, 1])
        self.assertEqual(len(result["units"]), 2)
        first, second = result["units"]
        self.assertIn("청구", first["goal"]["quote"])
        self.assertIn("검색", second["goal"]["quote"])
        self.assertEqual(first["results"][0]["role"], "assistant")
        self.assertEqual(first["remaining"][0]["quote"], "동시 요청 검증은 남았다.")
        self.assertEqual(second["progress"], [])
        self.assertEqual(generator.last_metrics["calls"], 9)
        self.assertTrue(all("동시 요청 검증은 남았다" in call[1] for call in generator.calls))

    def test_abstention_is_a_model_decision_not_a_keyword_filter(self):
        messages = [message("a", "고마워.")]
        result, generator = self.extract(messages, [0])
        self.assertEqual(result["units"], [])
        self.assertEqual(len(generator.calls), 1)
        # Deliberately wrong selection stays visible for semantic evaluation.
        incorrect, _ = self.extract(messages, [1, 0])
        self.assertEqual(len(incorrect["units"]), 1)

    def test_request_never_becomes_progress_through_projection(self):
        result, _ = self.extract([message("a", "배너 문구를 수정해줘.")], [6, 0])
        unit = result["units"][0]
        self.assertEqual(unit["progress"], [])
        self.assertEqual(unit["results"], [])
        self.assertEqual(unit["remaining"][0]["quote"], unit["goal"]["quote"])

    def test_activity_without_stated_goal_stays_unknown(self):
        result, _ = self.extract([message("a", "오류 로그를 읽었습니다.", "assistant")], [2, 0])
        self.assertIsNone(result["units"][0]["goal"])
        self.assertEqual(result["units"][0]["progress"][0]["role"], "assistant")

    def test_wrong_membership_is_not_silently_repaired(self):
        messages = [message("a", "화면을 개선하자. 별도로 백업을 추가하자."),
                    message("b", "화면을 수정했다.", "assistant")]
        result, _ = self.extract(messages, [1, 1, 0, 2, 2, 0, 0])
        self.assertEqual(result["units"][0]["progress"], [])
        self.assertIn("화면", result["units"][1]["progress"][0]["quote"])

    def test_ambiguous_span_or_membership_refuses(self):
        for answers in ([7], [1, 2, 2]):
            with self.subTest(answers=answers), self.assertRaises(ExperimentError):
                self.extract([message("a", "작업을 시작하자. 로그를 읽었다.")], answers)

    def test_unknown_choice_and_incompatible_decoding_refuse(self):
        generator = ChoiceGenerator(["not-offered"])
        with self.assertRaisesRegex(ExperimentError, "INVALID_CHOICE_OUTPUT"):
            infer(generator, "extract", {"messages": [message("a", "자료")]}, strategy="classified")
        generator.contract = {"thinking": True, "decoding": "sampled"}
        with self.assertRaisesRegex(ExperimentError, "INVALID_MODEL_CONFIG"):
            infer(generator, "extract", {"messages": [message("a", "자료")]}, strategy="classified")

    def test_spans_preserve_text_without_splitting_file_names(self):
        messages = [message("a", "  config.yaml 수정.\n 다음 단계? 긴문장 " + "가" * 605)]
        spans = source_spans(messages)
        self.assertEqual(spans[0]["quote"], "config.yaml 수정.")
        self.assertTrue(all(span["quote"] in messages[0]["text"] and len(span["quote"]) <= 600 for span in spans))
        self.assertEqual("".join(s["quote"] for s in spans).replace(" ", ""),
                         messages[0]["text"].replace(" ", "").replace("\n", ""))

    def test_excessive_spans_refuse_before_inference(self):
        generator = ChoiceGenerator([])
        with self.assertRaisesRegex(ExperimentError, "CONTEXT_TOO_LARGE"):
            infer(generator, "extract", {"messages": [message("a", "자료. " * 65)]}, strategy="classified")
        self.assertEqual(generator.calls, [])

    def test_repeated_nonwork_is_allowed_but_ambiguous_work_quote_refuses(self):
        result, _ = self.extract([message("a", "네. 네.")], [0, 0])
        self.assertEqual(result["units"], [])
        with self.assertRaisesRegex(ExperimentError, "INVALID_EVIDENCE"):
            self.extract([message("a", "네. 네.")], [1])

    def test_case_deadline_prevents_further_calls(self):
        generator = ChoiceGenerator([0])
        with patch("localbrain.work_context_classified.time.monotonic", side_effect=[0, 181]), \
             self.assertRaisesRegex(ExperimentError, "CASE_BUDGET_EXCEEDED"):
            infer(generator, "extract", {"messages": [message("a", "자료")]}, strategy="classified")
        self.assertEqual(generator.calls, [])

    def test_relation_requires_explicitly_selected_bilateral_evidence(self):
        packet = {"left": [message("a", "고객 화면 수정.")],
                  "right": [message("b", "독립적인 알림 작업.")]}
        for answers in ([3, 0], [3, 1, 0]):
            with self.assertRaisesRegex(ExperimentError, "MISSING_PAIR_EVIDENCE"):
                infer(ChoiceGenerator(answers), "relate", packet, strategy="classified")
        result = infer(ChoiceGenerator([3, 1, 1]), "relate", packet, strategy="classified")
        self.assertEqual({item["message"] for item in result["evidence"]}, {"a", "b"})
        self.assertIsNone(result["link"])

    def test_continuation_requires_separately_selected_right_link(self):
        packet = {"left": [message("a", "이전 작업.")], "right": [message("b", "그 작업을 재개하자.")]}
        with self.assertRaisesRegex(ExperimentError, "MISSING_CONTINUATION_LINK"):
            infer(ChoiceGenerator([1, 1, 1, 0]), "relate", packet, strategy="classified")
        result = infer(ChoiceGenerator([1, 1, 1, 1]), "relate", packet, strategy="classified")
        self.assertEqual(len(result["evidence"]), 2)
        self.assertEqual(result["link"]["message"], "b")

    def test_uncertain_relation_abstains_without_invented_quotes(self):
        generator = ChoiceGenerator([0])
        result = infer(generator, "relate", {"left": [message("a", "자료")],
                       "right": [message("b", "그것")]}, strategy="classified")
        self.assertEqual(result["relation"], "uncertain")
        self.assertEqual(result["evidence"], [])
        self.assertEqual(len(generator.calls), 1)

    def test_prompts_and_choice_bounds_participate_in_cache_identity(self):
        baseline = inference_identity({}, "classified")
        for strategy in ("single", "staged"):
            self.assertNotEqual(baseline, inference_identity({}, strategy))
        with patch("localbrain.work_context_classified.CONTRACT", {**CONTRACT, "max_spans": 32}):
            self.assertNotEqual(baseline, inference_identity({}, "classified"))
        with patch("localbrain.work_context_classified.PROMPTS", ["changed"]):
            self.assertNotEqual(baseline, inference_identity({}, "classified"))

    def test_complete_cases_reuse_but_interrupted_case_recomputes(self):
        cases = [{"id": str(i), "kind": "extract", "split": "development", "negative": bool(i),
                  "packet": {"messages": [message("a", "합성") ]}} for i in range(2)]
        with tempfile.TemporaryDirectory(prefix="work-choice-test-", dir="/private/tmp") as folder:
            output = Path(folder).resolve() / "evaluation"
            assessor = lambda *_: {"synthetic": True}
            with self.assertRaises(KeyboardInterrupt):
                evaluate(ChoiceGenerator([KeyboardInterrupt()]), cases, assessor, output, strategy="classified")
            first = evaluate(ChoiceGenerator([0, 0]), cases, assessor, output, strategy="classified")
            self.assertEqual(first["reused"], 0)
            self.assertEqual(first["strategy_contract"]["generation_method"], "choose")
            self.assertEqual(first["strategy_contract"]["max_output_tokens_per_choice"], 9)
            cached = ChoiceGenerator([])
            second = evaluate(cached, cases, assessor, output, strategy="classified")
            self.assertEqual(second["reused"], 2)
            self.assertEqual(cached.calls, [])


if __name__ == "__main__":
    unittest.main()
