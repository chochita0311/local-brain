"""Whole-conversation selection retains explicit provenance and abstention."""

import unittest
from unittest.mock import patch

from localbrain.work_context import infer, inference_identity
from localbrain.work_reconstruction import ExperimentError
from test_work_context_classified import ChoiceGenerator
from work_context_cases import message


class SelectedTests(unittest.TestCase):
    def setUp(self):
        self.messages = [message("a", "청구 개선. 별개 검색 개선."),
                         message("b", "청구 코드를 수정하고 확인했다. 동시 검증은 남았다.", "assistant")]

    def extract(self, answers, messages=None):
        generator = ChoiceGenerator(answers)
        result = infer(generator, "extract", {"messages": messages or self.messages}, strategy="selected")
        return result, generator

    def test_two_anchors_in_one_message_and_goal_specific_fields(self):
        result, generator = self.extract([1, 1, 0, 1, 1, 3, 0, 3, 0, 4, 0, 2, 2, 0, 0, 0])
        self.assertEqual(len(result["units"]), 2)
        first, second = result["units"]
        self.assertEqual(first["goal"]["quote"], "청구 개선.")
        self.assertEqual(first["results"][0]["role"], "assistant")
        self.assertEqual(first["remaining"][0]["quote"], "동시 검증은 남았다.")
        self.assertEqual(second["goal"]["quote"], "별개 검색 개선.")
        self.assertEqual(second["progress"], [])
        self.assertEqual(generator.last_metrics["calls"], 16)
        self.assertTrue(all("동시 검증은 남았다" in call[1] for call in generator.calls))

    def test_no_work_stops_at_inventory(self):
        result, generator = self.extract([0], [message("a", "감사합니다.")])
        self.assertEqual(result["units"], [])
        self.assertEqual(len(generator.calls), 1)

    def test_missing_anchor_is_not_filled_in_by_projection(self):
        with self.assertRaisesRegex(ExperimentError, "MISSING_ANCHOR"):
            self.extract([1, 0, 0, 0, 0, 0, 0])

    def test_activity_anchor_need_not_invent_a_goal(self):
        result, _ = self.extract([1, 0, 0, 0, 1, 0, 0, 0],
                                 [message("a", "기록을 읽었다.", "assistant")])
        self.assertIsNone(result["units"][0]["goal"])
        self.assertEqual(result["units"][0]["progress"][0]["quote"], "기록을 읽었다.")

    def test_ninth_anchor_and_ambiguous_span_refuse(self):
        with self.assertRaisesRegex(ExperimentError, "TOO_MANY_WORK_UNITS"):
            self.extract([1] * 9, [message("a", " ".join("작업%d." % i for i in range(9)))])
        with self.assertRaisesRegex(ExperimentError, "AMBIGUOUS_WORK_SPAN"):
            self.extract([5])

    def test_ambiguous_quote_refuses_before_details(self):
        generator = ChoiceGenerator([1])
        with self.assertRaisesRegex(ExperimentError, "INVALID_EVIDENCE"):
            infer(generator, "extract", {"messages": [message("a", "작업. 작업.")]}, strategy="selected")
        self.assertEqual(len(generator.calls), 1)

    def test_ninth_field_item_refuses_instead_of_truncating(self):
        messages = [message("a", " ".join("기록%d." % i for i in range(10)))]
        with self.assertRaisesRegex(ExperimentError, "TOO_MANY_FIELD_ITEMS"):
            self.extract([1, 0, 1, 0] + [1] * 9, messages)

    def test_pair_missing_citation_or_link_never_gets_repaired(self):
        packet = {"left": [message("a", "작업 목표.")], "right": [message("b", "그 작업 재개.")]}
        for answers, error in (([3, 0], "MISSING_PAIR_EVIDENCE"),
                               ([1, 1, 1, 0], "MISSING_CONTINUATION_LINK")):
            with self.assertRaisesRegex(ExperimentError, error):
                infer(ChoiceGenerator(answers), "relate", packet, strategy="selected")
        result = infer(ChoiceGenerator([1, 1, 1, 1]), "relate", packet, strategy="selected")
        self.assertEqual(len(result["evidence"]), 2)
        self.assertEqual(result["link"]["message"], "b")

    def test_source_selection_identity_is_distinct_and_prompt_sensitive(self):
        baseline = inference_identity({}, "selected")
        self.assertNotEqual(baseline, inference_identity({}, "classified"))
        with patch("localbrain.work_context_selected.PROMPTS", ["changed"]):
            self.assertNotEqual(baseline, inference_identity({}, "selected"))


if __name__ == "__main__":
    unittest.main()
