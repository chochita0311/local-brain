"""Model-free adapter, reference controls and failure-preserving trial tests."""

import copy
import json
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain import work_state as state
from localbrain.session_simulation import atomic_json, read_json
from localbrain.work_claims import (EXTRACT, LIMITS, Anchors, bind_claims, binding_prompt, extract_claims,
                                    extraction_prompt, legacy_units, producer, records_for)
from localbrain.work_claim_assessment import binding_checks, extraction_checks, gates
from localbrain.work_claim_trial import PINNED, record_primary_review, run_trial, suite_identity
from localbrain.work_context_model import generation_settings
from localbrain.work_reconstruction import ExperimentError
from work_claim_cases import CASES, HOLDOUT, annotate, claim, ordinary, span
from work_context_evidence_cases import assess


class Generator:
    def __init__(self, cases=CASES, behavior="correct"):
        self.cases, self.behavior, self.calls = cases, behavior, 0
        self.last_output, self.last_metrics = "", {}
        self.contract = {"model": "Qwen/Qwen3-8B", "revision": PINNED, "fingerprint": "a" * 64,
            "device": "mps", "dtype": "bfloat16", "attention": "eager", "python": "test",
            "torch": "test", "transformers": "test", **generation_settings(max_seconds=60)}

    def generate(self, system, content):
        self.calls += 1
        self.last_metrics = {"input_tokens": 10, "output_tokens": 5, "seconds": 0.1}
        if self.behavior == "replay":
            raise AssertionError("generation during replay")
        if self.behavior == "interrupt" and self.calls == 2:
            raise KeyboardInterrupt()
        if self.behavior == "refuse":
            raise ExperimentError("OUTPUT_TRUNCATED")
        if self.behavior == "invalid":
            return "not JSON"
        payload = json.loads(content.split("INPUT:\n", 1)[1])
        case = next(c for c in self.cases if records_for(c) == payload["records"])
        if self.behavior == "unknown":
            value = {"claims": [], "no_work": []} if content.startswith(EXTRACT) else {
                "targets": payload.get("reference_targets") or [], "bindings": [], "effects": [], "links": [],
                "pair": {"relation": "uncertain", "evidence": [], "link": None} if case["kind"] == "relate" else None}
        else:
            value = case["reference"]["extraction" if content.startswith(EXTRACT) else "binding"]
        self.last_output = json.dumps(value, ensure_ascii=False)
        return self.last_output


def reference(case, lineage=None):
    lineage = lineage or producer(Generator().contract)
    a = extract_claims(records_for(case), state._json(case["reference"]["extraction"]), lineage, cutoff=case.get("cutoff_at"))
    b = bind_claims(a, state._json(case["reference"]["binding"]), paired=case["kind"] == "relate")
    return a, b


def case_named(name):
    return copy.deepcopy(next(c for c in CASES if c["id"] == name))


class AdapterTests(unittest.TestCase):
    def test_all_frozen_references_states_and_unchanged_legacy_checks(self):
        self.assertEqual(len(CASES), 28)
        self.assertEqual(len(HOLDOUT), 10)
        for case in CASES:
            with self.subTest(case=case["id"]):
                a, b = reference(case)
                self.assertTrue(all(binding_checks(case, a, b).values()))
                if "expect" in case:
                    self.assertTrue(all(assess(case, b["pair"] if case["kind"] == "relate" else legacy_units(b)).values()))

    def test_no_reference_answers_or_roster_in_end_to_end_prompt(self):
        case = CASES[0]
        a, _ = reference(case)
        x = json.loads(extraction_prompt(records_for(case))[1].split("INPUT:\n")[1])
        self.assertEqual(set(x), {"records"})
        for mode in (None, case["reference"]["binding"]["targets"]):
            p = json.loads(binding_prompt(a, reference_targets=mode)[1].split("INPUT:\n")[1])
            self.assertEqual(p["reference_targets"], mode)
            self.assertNotIn("expect", p)
            self.assertNotIn("states", p)
            self.assertNotIn(case["id"], json.dumps(p))

    def test_producer_changes_claims_not_source_anchors(self):
        p = producer(Generator().contract)
        a, b = reference(CASES[0], p)
        p["extraction"] = "f" * 64
        other, changed = reference(CASES[0], p)
        self.assertEqual(a["packet"]["anchors"], other["packet"]["anchors"])
        self.assertNotEqual(a["aliases"], other["aliases"])
        self.assertNotEqual(b["packet"]["bindings"], changed["packet"]["bindings"])
        self.assertNotEqual(b["projection"]["digest"], changed["projection"]["digest"])

    def test_literal_and_inferred_completion_authority_remain_separate(self):
        _, b = reference(case_named("claim_fulfillment_same"))
        history = b["projection"]["history"]
        self.assertTrue(all(c["authority"] == "model-inferred" for c in history if c["interpretation"]["basis"] != "source"))
        self.assertTrue(all(c["authority"] == "source-attributed" for c in history if c["interpretation"]["basis"] == "source"))
        self.assertFalse(b["projection"]["model_admission"])
        self.assertNotIn("synthetic-supplied", state._json(b))

    def test_effect_cannot_complete_an_effort(self):
        c = case_named("claim_fulfillment_same")
        c["reference"]["binding"]["targets"][0]["kind"] = "effort"
        with self.assertRaisesRegex(state.WorkStateError, "INVALID_DERIVATION"):
            reference(c)

    def test_effect_needs_same_target_premises(self):
        c = case_named("claim_fulfillment_same")
        c["reference"]["binding"]["bindings"][1]["relation"] = "contributes"
        with self.assertRaisesRegex(state.WorkStateError, "INVALID_DERIVATION"):
            reference(c)

    def test_sibling_completion_preserves_original_pending_and_failed_outcome(self):
        for key, expected in (("claim_fulfillment_same", ["completed"]), ("claim_fulfillment_sibling", ["pending", "unknown"])):
            _, b = reference(case_named(key))
            self.assertEqual(sorted(t["state"] for t in b["projection"]["targets"]), expected)
        _, b = reference(case_named("claim_fulfillment_same"))
        self.assertTrue(any(c["kind"] == "outcome" and "실패" in c["meaning"] for c in b["projection"]["history"]))

    def test_cutoff_withholds_completion_but_retains_pending(self):
        c = case_named("claim_fulfillment_same")
        c["cutoff_at"] = "2026-01-10T12:00:00Z"
        _, b = reference(c)
        self.assertEqual(b["projection"]["targets"][0]["state"], "pending")
        self.assertFalse(any(x["interpretation"]["basis"] == "fulfills-obligation" for x in b["projection"]["history"]))

    def test_unresolved_effect_qualifies_without_closing(self):
        c = case_named("claim_fulfillment_same")
        c["reference"]["binding"]["effects"][-1]["disposition"] = "unresolved"
        _, b = reference(c)
        t = b["projection"]["targets"][0]
        self.assertEqual(t["state"], "pending")
        self.assertIn("unresolved-identity", t["qualifications"])

    def test_no_work_cannot_overlap_claim(self):
        c = CASES[0]
        raw = copy.deepcopy(c["reference"]["extraction"])
        raw["no_work"] = [raw["claims"][0]["span"]]
        with self.assertRaisesRegex(state.WorkStateError, "CONTRADICTORY_COVERAGE"):
            extract_claims(records_for(c), state._json(raw), producer(Generator().contract))

    def test_unselected_text_is_unresolved_not_no_work(self):
        a = extract_claims(records_for(CASES[0]), '{"claims":[],"no_work":[]}', producer(Generator().contract))
        self.assertTrue(all(s["disposition"] == "unresolved" for s in a["packet"]["coverage"]))

    def test_repeated_unicode_quote_uses_explicit_occurrence(self):
        c = annotate(ordinary("unicode", True, "검사 ✅ 끝. 검사 ✅ 끝."), [])
        records = records_for(c)
        pool = Anchors(records)
        a = pool.span(span("m1", "검사 ✅ 끝", 1))
        self.assertEqual(pool.values[a]["start"], 8)
        for occurrence in (-1, True, 2, 1001):
            with self.assertRaises(state.WorkStateError):
                pool.span(span("m1", "검사 ✅ 끝", occurrence))

    def test_fabricated_quote_and_extra_fields_refuse(self):
        for change in ("quote", "authority", "role"):
            c = CASES[0]; value = copy.deepcopy(c["reference"]["extraction"])
            if change == "quote":
                value["claims"][0]["span"]["quote"] = "fabricated-not-source"
            else:
                value["claims"][0][change] = "user-confirmed"
            with self.assertRaises((ExperimentError, state.WorkStateError)):
                extract_claims(records_for(c), state._json(value), producer(Generator().contract))

    def test_no_relative_date_or_timezone_invention(self):
        c = case_named("claim_time_unknown")
        c["reference"]["extraction"]["claims"][-1]["time"] = {
            "start": "2026-01-01T00:00:00Z", "end": "2026-01-01T00:00:00Z", "evidence": []}
        with self.assertRaisesRegex(state.WorkStateError, "INVALID_TIME_EVIDENCE"):
            reference(c)

    def test_producer_and_origin_forgery_rejected(self):
        _, b = reference(CASES[0])
        for mutation in ("producer", "origin", "identity"):
            p = copy.deepcopy(b["packet"])
            if mutation == "producer":
                p["producer"]["kind"] = "synthetic-supplied.v1"
            elif mutation == "origin":
                p["interpretations"][0]["intent"] = {}
            else:
                p["bindings"][0]["id"] = "binding:forged"
            with self.assertRaises(state.WorkStateError):
                state.project_model_work_state(p)

    def test_v2_replay_permutation_ingestion_and_no_input_mutation(self):
        _, b = reference(CASES[0]); before = copy.deepcopy(b["packet"])
        self.assertEqual(state.project_model_work_state(before), b["projection"])
        p = copy.deepcopy(before)
        for value in p.values():
            if isinstance(value, list):
                value.reverse()
        for r in p["records"]:
            r["ingested_at"] = "2026-09-23T00:00:00Z"
        self.assertEqual(state.project_model_work_state(p), b["projection"])
        self.assertEqual(before, b["packet"])

    def test_edit_changes_anchors_and_old_revision_refuses(self):
        _, b = reference(CASES[0]); p = copy.deepcopy(b["packet"])
        p["records"][0]["text"] += "!"
        with self.assertRaisesRegex(state.WorkStateError, "REVISION_MISMATCH"):
            state.project_model_work_state(p)

    def test_cyclic_target_and_missing_link_endpoint_refuse(self):
        for mutation in ("parent", "endpoint"):
            c = case_named("claim_reopen")
            if mutation == "parent":
                c["reference"]["binding"]["targets"][0]["parent"] = "t1"
            else:
                c["reference"]["binding"]["links"][0]["after"] = "missing"
            with self.assertRaises(state.WorkStateError):
                reference(c)

    def test_conditioned_roster_cannot_be_changed(self):
        a, b = reference(CASES[0])
        roster = copy.deepcopy(b["wire"]["targets"])
        roster[0]["kind"] = "occurrence"
        with self.assertRaisesRegex(state.WorkStateError, "REFERENCE_ROSTER_CHANGED"):
            bind_claims(a, state._json(b["wire"]), reference_targets=roster)

    def test_pair_cannot_contradict_supported_continuation(self):
        c = case_named("dev_resume")
        c["reference"]["binding"]["pair"].update(relation="related", link=None)
        with self.assertRaisesRegex(state.WorkStateError, "PAIR_BINDING_CONFLICT"):
            reference(c)

    def test_compound_omission_and_wrong_role_fail_independent_of_final_state(self):
        c = case_named("claim_compound_performed")
        a, b = reference(c)
        a["wire"]["claims"].pop()
        self.assertFalse(extraction_checks(c, a)[0]["claim_coverage"])
        a, b = reference(c)
        a["wire"]["claims"][-1]["role"] = "step"
        self.assertFalse(binding_checks(c, a, b)["claim_purity"])

    def test_positive_safety_failure_cannot_hide_in_eighty_percent_gate(self):
        rows = [{"split": "test", "negative": False, "extraction": {"coverage": True},
                 "conditioned": {"safe_terminal_scope": i != 0},
                 "end_to_end": {"safe_terminal_scope": i != 0}} for i in range(5)]
        rows += [{"split": "test", "negative": True, "extraction": {"coverage": True},
                  "conditioned": {"safe_terminal_scope": True}, "end_to_end": {"safe_terminal_scope": True}}]
        self.assertFalse(gates(rows)["test"]["end_to_end"]["passed"])

    def test_empty_and_oversized_input_remain_bounded(self):
        a = extract_claims([], '{"claims":[],"no_work":[]}', producer(Generator().contract))
        self.assertEqual(a["packet"]["claims"], [])
        raw = copy.deepcopy(CASES[0]["reference"]["extraction"])
        raw["claims"] *= 20
        with self.assertRaisesRegex(state.WorkStateError, "ADAPTER_LIMIT"):
            extract_claims(records_for(CASES[0]), state._json(raw), producer(Generator().contract))

    def test_no_filesystem_or_old_state_read_during_v2_replay(self):
        _, b = reference(CASES[0])
        with patch("builtins.open", side_effect=AssertionError("unexpected IO")):
            self.assertEqual(state.project_model_work_state(b["packet"]), b["projection"])

    def test_unbound_pending_remains_in_legacy_view(self):
        c = case_named("claim_fulfillment_sibling")
        c["reference"]["binding"]["bindings"] = []
        c["reference"]["binding"]["effects"] = []
        _, b = reference(c)
        self.assertTrue(any(u["remaining"] for u in legacy_units(b)["units"]))

    def test_raw_json_duplicate_key_and_deep_input_refuse(self):
        for raw in ('{"claims":[],"claims":[],"no_work":[]}', '{"claims":' + '[' * 20 + ']' * 20 + ',"no_work":[]}'):
            with self.assertRaises((ExperimentError, state.WorkStateError)):
                extract_claims(records_for(CASES[0]), raw, producer(Generator().contract))


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="localbrain-claim-tests-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name).resolve() / "trial"
        self.cases = CASES[:2]

    def run_trial(self, generator, **kwargs):
        return run_trial(generator, self.cases, [], assess, self.folder, **kwargs)

    def test_complete_reference_double_is_not_model_admission(self):
        g = Generator()
        r = run_trial(g, CASES, HOLDOUT, assess, self.folder)
        self.assertEqual(g.calls, 84)
        self.assertTrue(r["development_gate"])
        self.assertFalse(r["model_admission"])
        self.assertFalse(r["holdout_executed"])
        self.assertTrue(all(all(v["passed"] for v in split.values()) for split in r["split_gates"].values()))

    def test_zero_generation_replay_preserves_all_observations(self):
        first = self.run_trial(Generator())
        g = Generator(behavior="replay")
        second = self.run_trial(g, replay=True)
        self.assertEqual(g.calls, 0)
        self.assertEqual(first["semantic_digest"], second["semantic_digest"])
        self.assertEqual(second["reused_observations"], 6)
        self.assertEqual(first["elapsed_seconds"], second["elapsed_seconds"])

    def test_wrong_answers_retained_and_constant_abstention_does_not_pass(self):
        r = self.run_trial(Generator(behavior="unknown"))
        self.assertFalse(r["development_gate"])
        g = Generator(behavior="replay")
        again = self.run_trial(g, replay=True)
        self.assertEqual(r["semantic_digest"], again["semantic_digest"])
        self.assertEqual(g.calls, 0)

    def test_refusals_and_invalid_json_preserved_with_dependency_skips(self):
        for behavior in ("refuse", "invalid"):
            with self.subTest(behavior=behavior):
                self.folder = self.folder.parent / behavior
                r = self.run_trial(Generator(behavior=behavior))
                self.assertEqual(r["calls"], 4)
                self.assertEqual(len(r["observations"]), 6)
                self.assertFalse(r["development_gate"])
                self.assertEqual(self.run_trial(Generator(behavior="replay"), replay=True)["semantic_digest"], r["semantic_digest"])

    def test_clean_interrupt_consumes_attempt_and_never_retries_it(self):
        g = Generator(behavior="interrupt")
        with self.assertRaises(KeyboardInterrupt):
            self.run_trial(g)
        p = read_json(self.folder / "progress.json")
        self.assertIsNone(p["inflight"])
        self.assertEqual(p["calls"], 2)
        second = Generator()
        r = self.run_trial(second)
        self.assertEqual(second.calls, 4)
        self.assertEqual(r["calls"], 6)
        self.assertEqual(r["observations"][1]["error"], "GENERATION_INTERRUPTED")

    def test_dirty_inflight_refuses(self):
        self.run_trial(Generator())
        p = read_json(self.folder / "progress.json")
        p["inflight"] = "reserved"
        p["checkpoint_hash"] = state._digest({k: v for k, v in p.items() if k != "checkpoint_hash"})
        atomic_json(self.folder / "progress.json", p)
        with self.assertRaisesRegex(ExperimentError, "UNCLEAN_INTERRUPTION"):
            self.run_trial(Generator())

    def test_tampered_observation_or_budget_refuses_before_generation(self):
        self.run_trial(Generator())
        for key in ("calls", "raw"):
            p = read_json(self.folder / "progress.json")
            if key == "calls":
                p["calls"] = 0
            else:
                p["observations"][0]["raw"] = "changed"
            atomic_json(self.folder / "progress.json", p)
            g = Generator()
            with self.assertRaisesRegex(ExperimentError, "INVALID_CHECKPOINT"):
                self.run_trial(g)
            self.assertEqual(g.calls, 0)

    def test_configuration_changes_refuse_without_overwriting(self):
        self.run_trial(Generator())
        original = (self.folder / "progress.json").read_bytes()
        cases = copy.deepcopy(self.cases)
        cases[0]["reference"]["states"] = {}
        with self.assertRaisesRegex(ExperimentError, "CONFIG_MISMATCH"):
            run_trial(Generator(), cases, [], assess, self.folder)
        self.assertEqual((self.folder / "progress.json").read_bytes(), original)

    def test_call_and_time_budget_preserve_refusals_on_resume(self):
        with patch.dict(LIMITS, {"calls": 1}):
            r = self.run_trial(Generator())
            self.assertEqual(r["calls"], 1)
            self.assertFalse(r["development_gate"])
            self.assertEqual(self.run_trial(Generator(behavior="replay"), replay=True)["calls"], 1)
        self.folder = self.folder.parent / "time"
        r = self.run_trial(Generator(), initial_seconds=7201)
        self.assertEqual(r["calls"], 0)
        self.assertTrue(all(o["error"] for o in r["observations"]))

    def test_missing_replay_does_not_generate(self):
        g = Generator()
        with self.assertRaisesRegex(ExperimentError, "INCOMPLETE_REPLAY"):
            self.run_trial(g, replay=True)
        self.assertEqual(g.calls, 0)

    def test_holdout_blocked_without_exact_primary_review(self):
        self.run_trial(Generator())
        g = Generator()
        with self.assertRaisesRegex(ExperimentError, "DEVELOPMENT_REVIEW_REQUIRED"):
            self.run_trial(g, include_holdout=True)
        self.assertEqual(g.calls, 0)

    def test_failed_report_cannot_receive_passing_review(self):
        r = self.run_trial(Generator(behavior="unknown"))
        with self.assertRaisesRegex(ExperimentError, "DEVELOPMENT_GATE_REQUIRED"):
            record_primary_review(self.folder, r["development_digest"], passed=True, findings=[])
        receipt = record_primary_review(self.folder, r["development_digest"], passed=False, findings=["missing-claims"])
        self.assertFalse(receipt["passed"])
        with self.assertRaisesRegex(ExperimentError, "STALE_REVIEW"):
            record_primary_review(self.folder, "old", passed=False, findings=[])

    def test_primary_review_survives_generation_free_replay(self):
        r = self.run_trial(Generator())
        receipt = record_primary_review(self.folder, r["development_digest"], passed=True, findings=[])
        second = self.run_trial(Generator(behavior="replay"), replay=True)
        self.assertEqual(second["primary_review"], receipt)

    def test_expired_trial_refuses_instead_of_resetting_budget(self):
        self.run_trial(Generator())
        owner = read_json(self.folder / "owner.json")
        owner["expires_at"] = "2020-01-01T00:00:00Z"
        atomic_json(self.folder / "owner.json", owner)
        with self.assertRaisesRegex(ExperimentError, "EVALUATION_EXPIRED"):
            self.run_trial(Generator())

    def test_bad_runtime_and_private_cli_arguments_refuse(self):
        g = Generator(); g.contract["thinking"] = True
        with self.assertRaisesRegex(ExperimentError, "TRIAL_RUNTIME_MISMATCH"):
            self.run_trial(g)
        namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/evaluate-source-claims.py"))
        with patch("builtins.print"):
            self.assertEqual(namespace["main"](["--database", "/private/source"]), 2)
            self.assertEqual(namespace["main"](["--describe"]), 0)

    def test_identity_covers_reference_expectations_and_implementation(self):
        before = suite_identity(CASES, HOLDOUT)
        cases = copy.deepcopy(CASES); cases[0]["reference"]["states"] = {}
        self.assertNotEqual(before, suite_identity(cases, HOLDOUT))
        with patch("localbrain.work_claim_trial.implementation_fingerprint", return_value="changed"):
            self.assertNotEqual(before, suite_identity(CASES, HOLDOUT))


if __name__ == "__main__":
    unittest.main()
