"""Evidence-first boundaries, attribution, non-bridging membership and replay."""

import copy
import io
import json
import runpy
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from localbrain.session_simulation import atomic_json, now, read_json
from localbrain.work_context import infer, inference_identity, validate_relation, validate_units
from localbrain.work_context_evaluation import evaluate, verify_evidence_development
from localbrain.work_context_choices import ChoiceTrie, validate_codes
from localbrain.work_context_evidence import CONTRACT, PROMPTS, evidence_spans
from localbrain.work_reconstruction import ExperimentError, digest
from work_context_cases import CASES as ORIGINAL_CASES, assess as original_assess, message
from work_context_evidence_cases import CASES, COMPOSITIONAL_CASES, assess


class Generator:
    def __init__(self, rules=None):
        self.contract = {**CONTRACT, "fingerprint": "synthetic"}
        self.rules, self.calls = rules or {}, []
        self.last_output, self.last_metrics = "", {}

    def choose(self, system, content, codes, *, max_code_chars=8):
        validate_codes(codes, max_code_chars=max_code_chars)
        task = next(k for k, prompt in PROMPTS.items() if content.startswith(prompt + "\nINPUT:\n"))
        data = json.loads(content.split("\nINPUT:\n", 1)[1])
        focus = data.get("focus", {}).get("quote", "")
        self.calls.append((task, data, codes))
        rule = self.rules.get((task, focus), self.rules.get(task))
        defaults = {"goal_match": "different", "membership": "unrelated", "basis": "insufficient",
                    "scope": "compatible", "target": "supported",
                    "unit_audit": "supported", "relation_audit": "supported"}
        answer = rule(data) if callable(rule) else rule if rule is not None else defaults.get(task, "absent")
        self.last_metrics = {"seconds": 0.001, "input_tokens": 20, "output_tokens": 3}
        self.last_output = answer
        return answer


class InferenceTests(unittest.TestCase):
    def extract(self, messages, rules):
        generator = Generator(rules)
        return infer(generator, "extract", {"messages": messages}, strategy="evidence"), generator

    def test_interleaved_goals_keep_fields_and_attribution(self):
        messages = [message("a", "Goal A."), message("b", "Goal B."),
                    message("c", "Action A.", "assistant"), message("d", "Result B.", "assistant"),
                    message("e", "Pending A.")]

        def membership(data):
            group = data["candidate_work"][0]["quote"]
            return "contributes" if data["focus"]["quote"].split()[-1] == group.split()[-1] else "unrelated"

        rules = {("goal", "Goal A."): "supported", ("goal", "Goal B."): "supported",
                 ("progress", "Action A."): "supported", ("results", "Result B."): "supported",
                 ("remaining", "Pending A."): "supported", "membership": membership}
        result, generator = self.extract(messages, rules)
        first, second = result["units"]
        self.assertEqual(first["goal"]["message"], "a")
        self.assertEqual([f["message"] for f in first["progress"]], ["c"])
        self.assertEqual([f["message"] for f in first["remaining"]], ["e"])
        self.assertEqual(first["results"], [])
        self.assertEqual(second["goal"]["message"], "b")
        self.assertEqual(second["results"][0]["role"], "assistant")
        self.assertEqual(second["results"][0]["authority"], "source-attributed")
        self.assertTrue(all(data["messages"] == messages for _, data, _ in generator.calls))
        self.assertTrue(all(not code.isdecimal() for _, _, codes in generator.calls for code in codes))

    def test_same_goal_phases_do_not_become_one_unit_per_span(self):
        result, _ = self.extract([message("a", "Goal A. Goal B.")],
            {"goal": "supported", "goal_match": "same"})
        self.assertEqual(len(result["units"]), 1)
        self.assertEqual(result["units"][0]["goal"]["quote"], "Goal A.")

    def test_nontransitive_goal_bridge_refuses(self):
        def compare(data):
            return "different" if (data["anchor"]["quote"], data["focus"]["quote"]) == ("G2.", "G3.") else "same"
        with self.assertRaisesRegex(ExperimentError, "UNCERTAIN_WORK_MEMBERSHIP"):
            self.extract([message("a", "G1. G2. G3.")], {"goal": "supported", "goal_match": compare})

    def test_two_matching_goal_groups_refuse_instead_of_first_wins(self):
        def compare(data):
            return "same" if data["focus"]["quote"] == "G3." else "different"
        with self.assertRaisesRegex(ExperimentError, "UNCERTAIN_WORK_MEMBERSHIP"):
            self.extract([message("a", "G1. G2. G3.")], {"goal": "supported", "goal_match": compare})

    def test_ambiguous_activity_membership_refuses(self):
        with self.assertRaisesRegex(ExperimentError, "UNCERTAIN_WORK_MEMBERSHIP"):
            self.extract([message("a", "G1. G2. Act.")], {
                ("goal", "G1."): "supported", ("goal", "G2."): "supported",
                ("progress", "Act."): "supported", "membership": "contributes"})

    def test_activity_can_retain_unknown_goal_and_target(self):
        result, _ = self.extract([message("a", "Act.", "assistant")],
                                {"progress": "supported", "target": "uncertain"})
        unit = result["units"][0]
        self.assertIsNone(unit["goal"])
        self.assertIsNone(unit["target"])
        self.assertEqual(unit["progress"][0]["quote"], "Act.")

    def test_no_work_is_empty_but_uncertain_field_is_not_empty_success(self):
        result, _ = self.extract([message("a", "Thanks.")], {})
        self.assertEqual(result["units"], [])
        with self.assertRaisesRegex(ExperimentError, "UNCERTAIN_WORK_FIELD"):
            self.extract([message("a", "Thanks.")], {"goal": "uncertain"})

    def test_unit_audit_rejection_or_disagreement_never_repairs_fields(self):
        for answer in ("contradicted", "uncertain"):
            with self.assertRaisesRegex(ExperimentError, "UNSUPPORTED_WORK_UNIT"):
                self.extract([message("a", "Future work.")], {"progress": "supported", "unit_audit": answer})

    def test_invalid_answer_is_not_retried_and_failing_call_is_recorded(self):
        generator = Generator({"goal": "invented"})
        with self.assertRaisesRegex(ExperimentError, "INVALID_CHOICE_OUTPUT"):
            infer(generator, "extract", {"messages": [message("a", "Goal.")]}, strategy="evidence")
        self.assertEqual(len(generator.calls), 1)
        self.assertEqual(generator.last_metrics["calls"], 1)

    def pair(self, rules):
        packet = {"left": [message("a", "Left goal.")], "right": [message("b", "Right link.")]}
        generator = Generator(rules)
        result = infer(generator, "relate", packet, strategy="evidence")
        return result, generator

    def test_continuation_requires_goals_scope_link_and_audit(self):
        result, generator = self.pair({"goal": "supported", "basis": "same_goal", "link": "supported"})
        self.assertEqual(result["relation"], "continues")
        self.assertEqual({f["message"] for f in result["evidence"]}, {"a", "b"})
        self.assertEqual(result["link"]["message"], "b")
        self.assertIn("relation_audit", [task for task, _, _ in generator.calls])

    def test_no_goal_blocks_a_spurious_same_work_answer(self):
        result, generator = self.pair({"basis": "same_goal", "link": "supported"})
        self.assertEqual(result["relation"], "uncertain")
        self.assertEqual(result["evidence"], [])
        self.assertEqual(generator.last_metrics["decisions"][-1]["reason"], "missing-goal-support")
        self.assertNotIn("link", [task for task, _, _ in generator.calls])

    def test_incompatible_scope_or_missing_link_abstains(self):
        for override in ({"scope": "incompatible"}, {"scope": "unknown"}, {"link": "absent"}):
            result, _ = self.pair({"goal": "supported", "basis": "same_goal", "link": "supported", **override})
            self.assertEqual(result["relation"], "uncertain")
            self.assertIsNone(result["link"])

    def test_topic_or_independence_requires_bilateral_selected_evidence(self):
        for basis, expected in (("shared_topic", "related"), ("distinct_goals", "independent")):
            result, _ = self.pair({"basis": basis, "pair_evidence": "supported"})
            self.assertEqual(result["relation"], expected)
            result, _ = self.pair({"basis": basis, "pair_evidence": lambda d:
                                  "supported" if d["side"] == "left" else "absent"})
            self.assertEqual(result["relation"], "uncertain")

    def test_contradictory_relation_assessments_withhold_not_force_a_verdict(self):
        result, generator = self.pair({"basis": "shared_topic", "pair_evidence": "supported",
                                       "relation_audit": "contradicted"})
        self.assertEqual(result["relation"], "uncertain")
        self.assertEqual(generator.last_metrics["decisions"][-1]["reason"], "unsupported-relation-audit")

    def test_span_identity_is_content_derived_and_ambiguous_quotes_refuse(self):
        spans = evidence_spans([message("a", "One. Two.")])
        extended = evidence_spans([message("a", "One. Two."), message("b", "Three.")])
        self.assertEqual(spans, extended[:2])
        self.assertTrue(all(s["id"].startswith("s_") for s in spans))
        generator = Generator()
        with self.assertRaisesRegex(ExperimentError, "INVALID_EVIDENCE"):
            infer(generator, "extract", {"messages": [message("a", "Same. Same.")]}, strategy="evidence")
        self.assertEqual(generator.calls, [])

    def test_span_unit_and_item_limits_do_not_truncate(self):
        with self.assertRaisesRegex(ExperimentError, "CONTEXT_TOO_LARGE"):
            self.extract([message("a", " ".join("Work%d." % i for i in range(33)))], {})
        with self.assertRaisesRegex(ExperimentError, "TOO_MANY_WORK_UNITS"):
            self.extract([message("a", " ".join("Goal%d." % i for i in range(9)))], {"goal": "supported"})
        with self.assertRaisesRegex(ExperimentError, "INVALID_OUTPUT"):
            self.extract([message("a", " ".join("Act%d." % i for i in range(9)))],
                         {"progress": "supported", "membership": "contributes"})

    def test_case_call_and_post_call_time_bounds(self):
        generator = Generator()
        with patch.dict(CONTRACT, {"max_calls": 1}):
            with self.assertRaisesRegex(ExperimentError, "CASE_BUDGET_EXCEEDED"):
                infer(generator, "extract", {"messages": [message("a", "Work.")]}, strategy="evidence")
        self.assertEqual(len(generator.calls), 1)
        generator = Generator()
        with patch("localbrain.work_context_evidence.time.monotonic", side_effect=lambda: 121 if generator.calls else 0):
            with self.assertRaisesRegex(ExperimentError, "CASE_BUDGET_EXCEEDED"):
                infer(generator, "extract", {"messages": [message("a", "Work.")]}, strategy="evidence")

    def test_fixed_runtime_and_identity_include_all_protocol_parts(self):
        for key, wrong in (("model", "other"), ("device", "cpu"), ("thinking", True), ("max_seconds", 180)):
            generator = Generator()
            generator.contract[key] = wrong
            with self.assertRaisesRegex(ExperimentError, "INVALID_EVIDENCE_RUNTIME"):
                infer(generator, "extract", {"messages": [message("a", "Work.")]}, strategy="evidence")
            self.assertEqual(generator.calls, [])
        base = inference_identity({}, "evidence")
        self.assertNotEqual(base, inference_identity({}, "selected"))
        with patch.dict(PROMPTS, {"goal": "changed"}):
            self.assertNotEqual(base, inference_identity({}, "evidence"))

    def test_long_semantic_labels_are_explicit_opt_in_and_still_token_bounded(self):
        with self.assertRaisesRegex(ExperimentError, "INVALID_CHOICES"):
            validate_codes(["supported"])
        validate_codes(["supported", "distinct_goals"], max_code_chars=32)
        trie = ChoiceTrie({"supported": [1, 2], "distinct_goals": [3]}, {9}, max_code_chars=32)
        self.assertEqual(trie.answer([1, 2, 9]), "supported")
        for label in ("x" * 33, "not a label", "outside/label"):
            with self.assertRaisesRegex(ExperimentError, "INVALID_CHOICES"):
                validate_codes([label], max_code_chars=32)
        with self.assertRaisesRegex(ExperimentError, "INVALID_CHOICES"):
            ChoiceTrie({"supported": list(range(1, 10))}, {99}, max_code_chars=32)
        for limit in (True, 1000, 9):
            with self.assertRaisesRegex(ExperimentError, "INVALID_CHOICES"):
                validate_codes(["yes"], max_code_chars=limit)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="work-evidence-test-", dir="/private/tmp")
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name).resolve() / "evaluation"
        self.generator = Generator()
        self.cases = [{"id": "%s-%s" % (split, negative), "split": split, "negative": negative,
            "kind": "extract", "packet": {"messages": [message("a", "Synthetic.")]}, "expect": {"units": 0}}
            for split in ("development", "compositional") for negative in (False, True)]
        self.result = validate_units({"units": []}, self.cases[0]["packet"]["messages"])

    def run_evaluation(self, effect=None, cases=None):
        with patch("localbrain.work_context_evaluation.infer", return_value=self.result, side_effect=effect) as call:
            report = evaluate(self.generator, cases or self.cases, original_assess, self.folder, strategy="evidence")
        return report, call

    def test_actual_results_replay_without_generation_or_observation_change(self):
        first, _ = self.run_evaluation()
        replay, call = self.run_evaluation()
        call.assert_not_called()
        self.assertEqual(replay["reused"], 4)
        self.assertEqual(replay["cases"], first["cases"])
        self.assertEqual(replay["case_attempts"], first["case_attempts"])

    def test_completed_refusals_and_semantic_failures_are_terminal(self):
        first, _ = self.run_evaluation(ExperimentError("UNSUPPORTED_WORK_UNIT"))
        replay, call = self.run_evaluation()
        call.assert_not_called()
        self.assertEqual(first["cases"], replay["cases"])
        self.assertFalse(replay["gate_passed"])

    def test_valid_but_wrong_output_is_not_retried(self):
        cases = copy.deepcopy(self.cases)
        cases[0]["expect"]["units"] = 1
        first, _ = self.run_evaluation(cases=cases)
        replay, call = self.run_evaluation(cases=cases)
        call.assert_not_called()
        self.assertTrue(replay["cases"][0]["valid"])
        self.assertFalse(replay["cases"][0]["passed"])
        self.assertEqual(first["cases"], replay["cases"])

    def test_changed_configuration_and_corruption_fail_without_replacement(self):
        original, _ = self.run_evaluation()
        original_hash = digest(original)
        self.generator.contract["fingerprint"] = "changed"
        with self.assertRaisesRegex(ExperimentError, "EVALUATION_CONFIG_MISMATCH"):
            self.run_evaluation()
        self.assertEqual(digest(read_json(self.folder / "report.json")), original_hash)
        self.generator.contract["fingerprint"] = "synthetic"
        progress = read_json(self.folder / "progress.json")
        progress["cases"][0]["metrics"]["output_tokens"] = 999
        atomic_json(self.folder / "progress.json", progress)
        with self.assertRaisesRegex(ExperimentError, "INVALID_CACHED_RESULT"):
            self.run_evaluation()

    def test_clean_interruption_resumes_only_missing_case_with_attempt_limit(self):
        with self.assertRaises(KeyboardInterrupt):
            self.run_evaluation([self.result, KeyboardInterrupt()])
        progress = read_json(self.folder / "progress.json")
        self.assertEqual(len(progress["cases"]), 1)
        self.assertIsNone(progress["inflight"])
        replay, call = self.run_evaluation()
        self.assertEqual(call.call_count, 3)
        self.assertEqual(replay["reused"], 1)
        self.assertEqual(replay["case_attempts"][self.cases[1]["id"]], 2)

    def test_repeated_interruption_cannot_reset_attempt_budget(self):
        for _ in range(2):
            with self.assertRaises(KeyboardInterrupt):
                self.run_evaluation(KeyboardInterrupt())
        with self.assertRaisesRegex(ExperimentError, "CASE_ATTEMPTS_EXHAUSTED"):
            self.run_evaluation()

    def test_unclean_interruption_refuses_even_with_completed_cache(self):
        self.run_evaluation()
        progress = read_json(self.folder / "progress.json")
        progress["inflight"] = self.cases[0]["id"]
        atomic_json(self.folder / "progress.json", progress)
        with self.assertRaisesRegex(ExperimentError, "EVALUATION_UNCLEAN_INTERRUPTION"):
            self.run_evaluation()

    def test_holdout_requires_both_revalidated_development_gates(self):
        report, _ = self.run_evaluation()
        verify_evidence_development(self.generator, self.cases, original_assess, self.folder / "report.json")
        report["cases"][0]["result"]["authority"] = "confirmed"
        atomic_json(self.folder / "report.json", report)
        with self.assertRaisesRegex(ExperimentError, "INVALID_CACHED_RESULT"):
            verify_evidence_development(self.generator, self.cases, original_assess, self.folder / "report.json")

    def test_forged_aggregate_pass_does_not_hide_a_failed_split(self):
        cases = copy.deepcopy(self.cases)
        cases[0]["expect"]["units"] = 1
        report, _ = self.run_evaluation(cases=cases)
        self.assertFalse(report["split_gates"]["development"])
        self.assertTrue(report["split_gates"]["compositional"])
        report["gate_passed"] = True
        atomic_json(self.folder / "report.json", report)
        with self.assertRaisesRegex(ExperimentError, "DEVELOPMENT_GATE_REQUIRED"):
            verify_evidence_development(self.generator, cases, original_assess, self.folder / "report.json")

    def test_expired_or_mismatched_development_evidence_refuses(self):
        self.run_evaluation()
        self.generator.contract["fingerprint"] = "changed"
        with self.assertRaisesRegex(ExperimentError, "DEVELOPMENT_GATE_REQUIRED"):
            verify_evidence_development(self.generator, self.cases, original_assess, self.folder / "report.json")
        self.generator.contract["fingerprint"] = "synthetic"
        owner = read_json(self.folder / "owner.json")
        owner["expires_at"] = (now() - timedelta(days=1)).isoformat()
        atomic_json(self.folder / "owner.json", owner)
        with self.assertRaisesRegex(ExperimentError, "INVALID_DEVELOPMENT_REPORT"):
            verify_evidence_development(self.generator, self.cases, original_assess, self.folder / "report.json")


class FixtureAndCliTests(unittest.TestCase):
    def test_fixed_new_cases_do_not_replace_original_or_holdout(self):
        self.assertEqual(CASES[:len(ORIGINAL_CASES)], ORIGINAL_CASES)
        self.assertEqual(len(COMPOSITIONAL_CASES), 12)
        self.assertEqual(sum(c["kind"] == "extract" for c in COMPOSITIONAL_CASES), 6)
        self.assertEqual(sum(c["negative"] for c in COMPOSITIONAL_CASES), 8)
        self.assertEqual(len([c for c in CASES if c["split"] == "holdout"]), 10)
        for c in CASES:
            self.assertNotIn("expect", c["packet"])

    def test_field_coverage_and_purity_detect_cross_goal_contamination(self):
        case = COMPOSITIONAL_CASES[0]
        messages = case["packet"]["messages"]
        facts = {m["id"]: {"message": m["id"], "quote": m["text"]} for m in messages}
        result = validate_units({"units": [
            {"goal": facts["m1"], "target": facts["m1"], "progress": [facts["m3"]],
             "results": [], "remaining": [facts["m5"]]},
            {"goal": facts["m2"], "target": facts["m2"], "progress": [],
             "results": [facts["m4"]], "remaining": []}]}, messages)
        self.assertTrue(all(assess(case, result).values()))
        result["units"][0]["results"] = result["units"][1]["results"]
        result["units"][1]["results"] = []
        checks = assess(case, result)
        self.assertFalse(checks["unit_0_results_purity"])
        self.assertFalse(checks["unit_1_results_coverage"])

    def test_all_abstain_cannot_pass_the_compositional_safety_controls(self):
        cases = [c for c in COMPOSITIONAL_CASES if c["kind"] == "relate"]
        passes = [all(assess(c, validate_relation({"relation": "uncertain", "evidence": [], "link": None},
                                                 **c["packet"])).values()) for c in cases]
        self.assertEqual(sum(passes), 1)

    def test_cli_rejects_unbounded_or_ungated_new_candidate_modes_before_model_load(self):
        main = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/evaluate-work-context-model.py"))["main"]
        base = ["--model-root", "/synthetic/model", "--output", "/synthetic/output", "--strategy", "evidence"]
        for extra in (["--split", "all"], ["--split", "holdout"], ["--thinking"], ["--device", "cpu"],
                      ["--development-report", "/synthetic/report.json"], ["--database", "/private/secret"]):
            with redirect_stdout(io.StringIO()) as out, patch("localbrain.work_context_model.LocalGenerator") as model:
                self.assertEqual(main(base + extra), 2)
            model.assert_not_called()
            self.assertNotIn("secret", out.getvalue())

    def test_cli_development_includes_both_frozen_splits(self):
        main = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/evaluate-work-context-model.py"))["main"]
        evaluate_mock = Mock(return_value={"gate_passed": False})
        with patch.dict(main.__globals__, {"evaluate": evaluate_mock}), patch(
                "localbrain.work_context_model.LocalGenerator", return_value=Generator()), redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--model-root", "/synthetic/model", "--output", "/synthetic/output",
                                   "--strategy", "evidence"]), 3)
        cases = evaluate_mock.call_args.args[1]
        self.assertEqual(len(cases), 16)
        self.assertEqual({c["split"] for c in cases}, {"development", "compositional"})


if __name__ == "__main__":
    unittest.main()
