import copy
import hashlib
import json
import random
import unittest
from unittest.mock import patch

from localbrain.work_state import (
    PRODUCER, VERSION, WorkStateError, anchor_key, claim_key, project_work_state, text_revision,
)
from work_state_cases import Packet, pending_completed, scenarios


def view(result, target="check"):
    return next(t for t in result["targets"] if t["id"] == target)


class WorkStateTests(unittest.TestCase):
    def test_frozen_scenarios(self):
        cases = scenarios()
        self.assertEqual(len(cases), 18)
        for name, packet, expected in cases:
            with self.subTest(name=name):
                result = project_work_state(packet.value)
                for target, status in expected.items():
                    self.assertEqual(view(result, target)["state"], status)
                self.assertFalse(result["model_admission"])
                self.assertEqual(result["producer"], PRODUCER)

    def test_historical_pending_retained_without_borrowing_later_action(self):
        p = pending_completed()
        result = project_work_state(p.value)
        self.assertEqual(len(result["history"]), 2)
        earlier = next(c for c in result["history"] if c["id"] == p.names["pending"])
        self.assertEqual(earlier["status"], "pending")
        self.assertEqual(earlier["kind"], "state")
        self.assertEqual(view(result)["frontier"], [p.names["done"]])
        self.assertFalse(view(result)["qualified"])
        self.assertEqual(view(result)["displaced"], [])  # advancement is not retraction
        anchor = next(a for a in result["anchors"] if a["id"] == earlier["focus"])
        self.assertEqual(anchor["sequence"], 1)
        self.assertEqual(anchor["role"], earlier["role"])
        self.assertEqual(anchor["asserted_at"], earlier["asserted_at"])

    def test_compound_claims_share_source_without_duplicate_efforts(self):
        _, p, _ = next(c for c in scenarios() if c[0] == "compound-pending")
        result = project_work_state(p.value)
        self.assertEqual(len(result["history"]), 2)
        self.assertEqual(len({c["focus"] for c in result["history"]}), 1)
        self.assertEqual(len(result["targets"]), 2)  # supplied effort and substep only
        segment = next(s for s in result["coverage"]["segments"] if s["claims"])
        self.assertEqual(len(segment["claims"]), 2)

    def test_no_work_empty_input_is_valid_and_not_admission(self):
        packet = Packet().value
        for name in ("records", "anchors", "claims", "targets", "bindings", "links", "coverage", "gaps"):
            packet[name] = []
        result = project_work_state(packet)
        self.assertEqual(result["history"], [])
        self.assertEqual(result["targets"], [])
        self.assertFalse(result["model_admission"])

    def test_enumeration_permutations_replay_identically_without_mutation(self):
        for name, p, _ in scenarios():
            before = copy.deepcopy(p.value)
            expected = project_work_state(p.value)
            self.assertEqual(p.value, before)
            for seed in range(5):
                altered = copy.deepcopy(p.value)
                rng = random.Random(seed)
                for value in altered.values():
                    if isinstance(value, list):
                        rng.shuffle(value)
                for section, fields in (("claims", ["context"]), ("bindings", ["evidence"]),
                                        ("links", ["evidence"]), ("coverage", ["claims"]),
                                        ("targets", ["anchors"])):
                    for item in altered[section]:
                        for field in fields:
                            rng.shuffle(item[field])
                with self.subTest(name=name, seed=seed):
                    self.assertEqual(project_work_state(altered), expected)

    def test_ingestion_time_and_utc_spelling_do_not_change_semantic_result(self):
        p = pending_completed()
        original = project_work_state(p.value)
        for record in p.value["records"]:
            record["ingested_at"] = "2026-09-01T00:00:00Z"
            record["asserted_at"] = record["asserted_at"].replace("+00:00", "Z")
        self.assertEqual(project_work_state(p.value), original)

    def test_no_io_model_or_environment_needed(self):
        p = pending_completed()
        with patch("builtins.open", side_effect=AssertionError("unexpected I/O")), \
                patch("socket.socket", side_effect=AssertionError("unexpected network")):
            self.assertEqual(view(project_work_state(p.value))["state"], "completed")

    def test_unrelated_append_leaves_existing_target_projection_unchanged(self):
        p = pending_completed()
        original = project_work_state(p.value)
        p.target("other", kind="occurrence")
        p.add("other-work", "別の点検を完了しました。", "completed", target="other")
        result = project_work_state(p.value)
        for key in ("check", "effort"):
            self.assertEqual(view(result, key), view(original, key))
        self.assertNotEqual(result["digest"], original["digest"])

    def test_repeated_name_does_not_bind_or_close_other_occurrence(self):
        p = Packet()
        p.target("run-a", kind="occurrence", parent="check")
        p.target("run-b", kind="occurrence", parent="check")
        p.value["targets"][-1]["label"] = p.value["targets"][-2]["label"]
        p.add("a", "点検は未完了です。", "pending", target="run-a")
        p.add("b", "点検は完了です。", "completed", target="run-b")
        result = project_work_state(p.value)
        self.assertEqual(view(result, "run-a")["state"], "pending")
        self.assertEqual(view(result, "run-b")["state"], "completed")
        self.assertEqual(view(result)["state"], "unknown")

    def test_descriptive_outcome_never_implicitly_closes(self):
        p = Packet()
        p.add("pending", "点検はまだです。", "pending")
        p.add("result", "テストがすべて通りました。", kind="outcome")
        self.assertEqual(view(project_work_state(p.value))["state"], "pending")

    def test_contribution_to_effort_is_not_fulfillment(self):
        p = pending_completed()
        p.bind("done", "effort", relation="contributes")
        result = project_work_state(p.value)
        self.assertEqual(view(result, "effort")["state"], "unknown")
        self.assertEqual(view(result)["state"], "completed")

    def test_unknown_binding_qualifies_last_supported_completion(self):
        p = pending_completed()
        p.add("uncertain", "未完了の検証があります。", "pending", target=None)
        p.bind("uncertain", "check", disposition="unresolved")
        result = view(project_work_state(p.value))
        self.assertEqual(result["state"], "completed")
        self.assertTrue(result["qualified"])
        self.assertIn("unresolved-binding", result["qualifications"])

    def test_incomplete_snapshot_and_unresolved_coverage_stay_visible(self):
        p = pending_completed()
        p.value["snapshot"]["complete"] = False
        a = p.record("解釈できない記録")
        p.value["coverage"][-1]["disposition"] = "unresolved"
        result = project_work_state(p.value)
        self.assertTrue(view(result)["qualified"])
        self.assertEqual(set(result["coverage"]["qualifications"]), {"incomplete-snapshot", "unresolved-content"})
        self.assertIn(a, {v["id"] for v in result["anchors"]})

    def test_later_context_binding_and_target_do_not_leak_across_cutoff(self):
        p = pending_completed()
        late = p.record("秘密の将来ラベルと訂正", at="2026-03-01T00:00:00Z")
        p.target("future", anchors=[late])
        p.value["snapshot"]["cutoff_at"] = "2026-02-01T00:01:30Z"
        result = project_work_state(p.value)
        self.assertNotIn("秘密の将来", json.dumps(result, ensure_ascii=False))
        self.assertEqual(view(result)["state"], "pending")
        self.assertNotIn(p.names["done"], {c["id"] for c in result["history"]})
        self.assertEqual(result["coverage"]["withheld_targets"], 1)

    def test_later_context_withholds_earlier_interpretation(self):
        p = Packet()
        early = p.record("それは終わりました。")
        late = p.record("それは別の点検の意味でした。", at="2026-03-01T00:00:00Z")
        p.add("contextual", "別の点検完了", "completed", focus=early, context=[late])
        p.value["snapshot"]["cutoff_at"] = "2026-02-10T00:00:00Z"
        result = project_work_state(p.value)
        self.assertEqual(result["history"], [])
        self.assertEqual(result["coverage"]["withheld_claims"], 1)
        self.assertEqual(sum(s["withheld_claim_count"] for s in result["coverage"]["segments"]), 1)
        self.assertIn("withheld-interpretation", view(result)["qualifications"])

    def test_missing_assertion_date_with_cutoff_is_not_admitted(self):
        p = Packet()
        p.add("undated", "完了しました。", "completed", at=None)
        p.value["snapshot"]["cutoff_at"] = "2026-02-10T00:00:00Z"
        result = project_work_state(p.value)
        self.assertEqual(view(result)["state"], "unknown")
        self.assertTrue(view(result)["qualified"])
        self.assertIn("unknown-cutoff-time", result["coverage"]["qualifications"])

    def test_equal_timestamp_uses_explicit_source_sequence_not_array_order(self):
        p = Packet()
        p.add("p", "まだです。", "pending", at="2026-02-01T00:00:00Z")
        p.add("c", "今完了です。", "completed", at="2026-02-01T00:00:00Z")
        result = view(project_work_state(p.value))
        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["order_basis"], ["source-sequence"])
        self.assertFalse(result["order_withheld"])

    def test_conflicting_source_date_and_sequence_is_not_latest_wins(self):
        p = Packet()
        p.add("p", "まだです。", "pending", at="2026-02-03T00:00:00Z")
        p.add("c", "完了です。", "completed", at="2026-02-02T00:00:00Z")
        result = view(project_work_state(p.value))
        self.assertEqual(result["state"], "conflicted")
        self.assertIn("chronology-conflict", result["qualifications"])

    def test_explicit_link_can_order_unknown_effective_time(self):
        p = Packet()
        p.add("p", "まだでした。", "pending", at=None, mode="unknown")
        p.add("c", "その後完了しました。", "completed", at=None, mode="unknown")
        p.link("p", "c")
        result = view(project_work_state(p.value))
        self.assertEqual(result["state"], "completed")
        self.assertTrue(result["links"][0]["applied"])

    def test_overlapping_effective_intervals_do_not_invent_order(self):
        p = Packet()
        for name, status in (("p", "pending"), ("c", "completed")):
            p.add(name, name + "と報告", status, mode="explicit",
                  start="2026-01-01T00:00:00Z", end="2026-01-03T00:00:00Z")
        self.assertEqual(view(project_work_state(p.value))["state"], "conflicted")

    def test_cancel_then_complete_needs_reopen_or_correction(self):
        p = Packet()
        p.add("cancel", "取消です。", "cancelled")
        p.add("done", "完了です。", "completed")
        self.assertEqual(view(project_work_state(p.value))["state"], "conflicted")

    def test_reopen_then_complete_and_cancelled_reopen(self):
        for terminal in ("completed", "cancelled"):
            p = Packet()
            p.add("old", "以前の状態", terminal)
            p.add("again", "明示的に再開します。", "pending")
            p.link("old", "again", "reopens")
            self.assertEqual(view(project_work_state(p.value))["state"], "pending")
            p.add("done", "再開した点検を完了しました。", "completed")
            self.assertEqual(view(project_work_state(p.value))["state"], "completed")

    def test_correction_history_and_retraction_chain_are_not_deleted(self):
        _, p, _ = next(c for c in scenarios() if c[0] == "retract-correction-restores-prior-report")
        result = project_work_state(p.value)
        self.assertEqual(len(result["history"]), 4)
        self.assertEqual(view(result)["displaced"], [p.names["correction"]])
        self.assertEqual(view(result)["state"], "completed")

    def test_cross_speaker_retraction_cannot_erase_completion(self):
        p = pending_completed()
        p.add("withdraw", "以前の完了報告を撤回します。", kind="retraction", role="user")
        p.link("done", "withdraw", "retracts")
        result = view(project_work_state(p.value))
        self.assertEqual(result["state"], "completed")
        self.assertIn("cross-speaker-dispute", result["qualifications"])
        self.assertEqual(result["displaced"], [])
        self.assertNotIn("explicit-link", result["order_basis"])

    def test_explicit_future_effective_state_is_not_current(self):
        p = Packet()
        p.add("p", "まだです。", "pending")
        p.add("future", "将来状態の報告", "completed", mode="explicit",
              start="2026-03-01T00:00:00Z", end="2026-03-01T00:00:00Z")
        p.value["snapshot"]["cutoff_at"] = "2026-02-10T00:00:00Z"
        result = view(project_work_state(p.value))
        self.assertEqual(result["state"], "pending")
        self.assertIn("future-effective-state", result["qualifications"])

    def test_source_removal_withdraws_completion_and_keeps_gap_provenance(self):
        p = pending_completed()
        original = project_work_state(p.value)
        obsolete = p.names["done"]
        for section in ("records", "anchors", "claims", "bindings", "coverage"):
            p.value[section].pop()
        p.value["gaps"].append({"id": "removed", "reason": "source-removed", "targets": ["check"],
                                "obsolete_ids": [obsolete]})
        result = project_work_state(p.value)
        self.assertEqual(view(result)["state"], "pending")
        self.assertIn("source-removed", view(result)["qualifications"])
        self.assertNotEqual(original["digest"], result["digest"])
        self.assertEqual(view(result, "effort"), view(original, "effort"))

    def test_future_effective_correction_does_not_displace_present_state(self):
        p = pending_completed()
        p.add("future", "来月の訂正状態", "pending", mode="explicit",
              start="2026-03-01T00:00:00Z", end="2026-03-01T00:00:00Z")
        p.link("done", "future", "corrects")
        p.value["snapshot"]["cutoff_at"] = "2026-02-10T00:00:00Z"
        result = view(project_work_state(p.value))
        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["displaced"], [])
        self.assertFalse(result["links"][0]["applied"])

    def test_cross_target_correction_is_unresolved_not_applied(self):
        p = pending_completed()
        p.target("other", kind="occurrence")
        p.add("other", "別の作業は未完了です。", "pending", target="other")
        p.link("done", "other", "corrects")
        result = project_work_state(p.value)
        self.assertEqual(view(result)["state"], "completed")
        self.assertEqual(view(result)["displaced"], [])
        self.assertIn("unresolved-link-scope", view(result)["qualifications"])
        self.assertIn("unresolved-link-scope", view(result, "other")["qualifications"])

    def test_unbound_retraction_cannot_hide_behind_completed_status(self):
        p = pending_completed()
        p.add("retract", "以前の報告を撤回します。", kind="retraction", target=None)
        result = view(project_work_state(p.value))
        self.assertEqual(result["state"], "completed")
        self.assertIn("unbound-retraction", result["qualifications"])

    def test_revised_source_can_be_rebound_only_with_new_anchor_and_claim(self):
        p = pending_completed()
        old_claim = p.names["done"]
        old_anchor = p.value["anchors"][-1]["id"]
        record = p.value["records"][-1]
        record["text"] = record["text"].replace("완료", "취소")
        record["revision"] = text_revision(record["text"])
        anchor = p.value["anchors"][-1]
        anchor.update(id=anchor_key(record, 0, len(record["text"])), quote=record["text"])
        claim = p.value["claims"][-1]
        claim.update(focus=anchor["id"], status="cancelled", meaning=record["text"])
        claim["id"] = claim_key(claim)
        binding = p.value["bindings"][-1]
        binding.update(claim=claim["id"], evidence=[anchor["id"] if a == old_anchor else a for a in binding["evidence"]])
        p.value["coverage"][-1]["claims"] = [claim["id"]]
        p.value["gaps"].append({"id": "revised", "reason": "source-revised", "targets": ["check"],
                                "obsolete_ids": [old_claim]})
        result = project_work_state(p.value)
        self.assertEqual(view(result)["state"], "cancelled")
        self.assertNotIn(old_claim, {c["id"] for c in result["history"]})
        self.assertNotEqual(old_anchor, anchor["id"])

    def test_full_record_bound_is_supported(self):
        p = Packet()
        for index in range(127):
            p.record("合成文脈 " + str(index))
        self.assertEqual(project_work_state(p.value)["coverage"]["records"], 128)

    def test_withdrawn_binding_does_not_retain_stale_completed_state(self):
        p = pending_completed()
        p.value["bindings"].pop()
        p.value["gaps"].append({"id": "revoked", "reason": "binding-withdrawn", "targets": ["check"],
                                "obsolete_ids": ["b1"]})
        result = project_work_state(p.value)
        self.assertEqual(view(result)["state"], "pending")
        self.assertIn(p.names["done"], result["unassigned_claims"])
        self.assertTrue(view(result)["qualified"])

    def test_anchor_identity_uses_revision_native_scope_and_offsets_not_alias(self):
        p = pending_completed()
        record = copy.deepcopy(p.value["records"][-1])
        old = anchor_key(record, 0, len(record["text"]))
        record["id"] = "another-alias"
        record["ingested_at"] = "2026-09-01T00:00:00Z"
        self.assertEqual(anchor_key(record, 0, len(record["text"])), old)
        record["text"] = record["text"].replace("완료", "취소")
        record["revision"] = text_revision(record["text"])
        self.assertNotEqual(anchor_key(record, 0, len(record["text"])), old)
        for field in ("source", "session", "native_id", "speaker", "role"):
            changed = {**record, field: "changed"}
            self.assertNotEqual(anchor_key(changed, 0, len(changed["text"])), anchor_key(record, 0, len(record["text"])))

    def test_known_text_revision_and_changed_interpretation_identity(self):
        self.assertEqual(text_revision("abc"), hashlib.sha256(b"abc").hexdigest())
        c = pending_completed().value["claims"][-1]
        self.assertEqual(claim_key(c), c["id"])
        self.assertNotEqual(claim_key({**c, "status": "cancelled"}), c["id"])

    def test_attribution_is_reported_not_user_confirmation(self):
        p = Packet()
        p.add("user", "終わりました。", "completed", role="user")
        result = project_work_state(p.value)
        self.assertEqual(result["history"][0]["role"], "user")
        self.assertEqual(result["history"][0]["authority"], "source-attributed")
        self.assertEqual(view(result)["authority"], "source-reported")
        self.assertNotIn("user-confirmed", json.dumps(result))

    def test_semantically_false_but_structural_binding_is_not_certified(self):
        p = pending_completed()
        p.value["targets"][0]["label"] = "Label supplied by test, not inferred identity"
        result = project_work_state(p.value)
        self.assertEqual(result["producer"], "synthetic-supplied.v1")
        self.assertFalse(result["model_admission"])
        # No natural-language checker is hidden in the pure consumer.


class WorkStateRejectionTests(unittest.TestCase):
    def rejects(self, mutate, expected=None):
        p = pending_completed().value
        mutate(p)
        before = copy.deepcopy(p)
        with self.assertRaises(WorkStateError) as raised:
            project_work_state(p)
        if expected:
            self.assertEqual(str(raised.exception), expected)
        self.assertRegex(str(raised.exception), r"^[A-Z_]+$")
        self.assertEqual(p, before)

    def test_wrong_version_or_authority_cannot_enter(self):
        self.rejects(lambda p: p.update(version="other"), "VERSION_MISMATCH")
        self.rejects(lambda p: p.update(authority="user-confirmed"))
        self.rejects(lambda p: p["claims"][0].update(authority="verified"))

    def test_invalid_roles_statuses_and_bool_offsets(self):
        for mutate in (
            lambda p: p["records"][0].update(role="system"),
            lambda p: p["claims"][0].update(status="verified"),
            lambda p: p["claims"][0].update(kind="action"),
            lambda p: p["anchors"][0].update(start=True),
            lambda p: p["records"][0].update(sequence=True),
            lambda p: p["snapshot"].update(complete=1),
            lambda p: p["claims"][0].update(focus=[]),
        ):
            self.rejects(mutate)

    def test_fabricated_quotes_revision_and_stale_identity(self):
        self.rejects(lambda p: p["anchors"][0].update(quote="not the source"), "INVALID_ANCHOR")
        self.rejects(lambda p: p["records"][0].update(text="equal or different edit"), "REVISION_MISMATCH")
        self.rejects(lambda p: p["claims"][0].update(meaning="changed interpretation"), "IDENTITY_MISMATCH")

    def test_duplicate_identity_native_sequence_or_references(self):
        self.rejects(lambda p: p["claims"].append(copy.deepcopy(p["claims"][0])), "DUPLICATE_ID")
        self.rejects(lambda p: p["records"][1].update(sequence=p["records"][0]["sequence"]), "DUPLICATE_SOURCE")
        self.rejects(lambda p: p["bindings"][0]["evidence"].append(p["bindings"][0]["evidence"][0]), "DUPLICATE_REFERENCE")

    def test_dangling_anchor_claim_target_and_gap_target(self):
        for mutate in (
            lambda p: p["anchors"][0].update(record="gone"),
            lambda p: p["bindings"][0].update(claim="gone"),
            lambda p: p["bindings"][0].update(target="gone"),
            lambda p: p["targets"][0].update(parent="gone"),
            lambda p: p["gaps"].append({"id": "g", "reason": "source-removed", "targets": ["gone"], "obsolete_ids": []}),
        ):
            self.rejects(mutate, "MISSING_REFERENCE")

    def test_missing_compound_claim_and_gapped_overlapping_coverage(self):
        self.rejects(lambda p: p["coverage"].pop(), "INVALID_COVERAGE")
        self.rejects(lambda p: p["coverage"][0].update(start=1), "INVALID_COVERAGE")
        self.rejects(lambda p: p["coverage"].append(copy.deepcopy(p["coverage"][0])), "INVALID_COVERAGE")
        self.rejects(lambda p: p["coverage"][-1].update(claims=[]), "INVALID_COVERAGE")

    def test_ambiguous_supported_binding_and_cyclic_hierarchy(self):
        def ambiguous(p):
            p["bindings"].append({**p["bindings"][0], "id": "duplicate-scope", "target": "effort"})
        self.rejects(ambiguous, "AMBIGUOUS_BINDING")
        self.rejects(lambda p: p["targets"][0].update(parent="check"), "CYCLIC_REFERENCE")

    def test_cyclic_dangling_and_invalid_special_links(self):
        p = pending_completed()
        p.link("pending", "done")
        p.link("done", "pending", disposition="unresolved")
        with self.assertRaisesRegex(WorkStateError, "CYCLIC_REFERENCE"):
            project_work_state(p.value)
        p.value["links"].pop()
        p.value["links"][0]["kind"] = "reopens"
        with self.assertRaisesRegex(WorkStateError, "INVALID_TRANSITION"):
            project_work_state(p.value)
        p.value["links"][0]["before"] = "gone"
        with self.assertRaisesRegex(WorkStateError, "MISSING_REFERENCE"):
            project_work_state(p.value)

    def test_cross_session_binding_requires_bilateral_explicit_link(self):
        _, p, _ = next(c for c in scenarios() if c[0] == "long-gap-explicit-continuation")
        p.value["bindings"][-1]["continuation"] = None
        with self.assertRaisesRegex(WorkStateError, "MISSING_CONTINUATION"):
            project_work_state(p.value)
        p.value["bindings"][-1]["continuation"] = {"left": [p.goal], "right_link": p.goal}
        with self.assertRaisesRegex(WorkStateError, "INVALID_CONTINUATION"):
            project_work_state(p.value)

    def test_mixed_target_anchors_cannot_fake_left_side_of_continuation(self):
        _, p, _ = next(c for c in scenarios() if c[0] == "long-gap-explicit-continuation")
        right = p.value["bindings"][-1]["continuation"]["right_link"]
        p.value["targets"][-1]["anchors"].append(right)
        p.value["bindings"][0]["disposition"] = "unresolved"
        p.value["bindings"][-1]["continuation"]["left"] = [right]
        with self.assertRaisesRegex(WorkStateError, "INVALID_CONTINUATION"):
            project_work_state(p.value)

    def test_naive_invalid_and_reversed_time(self):
        for timestamp in ("2026-02-01", "2026-02-01T00:00:00", "2026-02-31T00:00:00Z", 42):
            self.rejects(lambda p: p["records"][0].update(asserted_at=timestamp), "INVALID_TIME")
        self.rejects(lambda p: p["claims"][0]["effective"].update(mode="explicit", start="2026-02-02T00:00:00Z",
                                                                               end="2026-02-01T00:00:00Z"), "INVALID_TIME")

    def test_excess_count_text_nesting_and_non_json_reject_without_raw_error(self):
        self.rejects(lambda p: p.update(records=p["records"] * 44), "PACKET_LIMIT")
        self.rejects(lambda p: p["records"][0].update(text="x" * 200001), "PACKET_LIMIT")
        self.rejects(lambda p: p["snapshot"].update(id=float("nan")))
        self.rejects(lambda p: p["snapshot"].update(id=b"sentinel"))
        nested = "secret-sentinel"
        for _ in range(14):
            nested = [nested]
        self.rejects(lambda p: p["snapshot"].update(id=nested), "PACKET_LIMIT")

    def test_every_collection_bound_is_enforced_before_processing(self):
        from localbrain.work_state import LIMITS
        for field, limit in LIMITS.items():
            with self.subTest(field=field):
                self.rejects(lambda p: p.update({field: [{}] * (limit + 1)}), "PACKET_LIMIT")

    def test_malformed_field_fuzz_never_leaks_python_errors(self):
        base = pending_completed().value
        paths = [(section, index, field) for section in ("records", "anchors", "claims", "targets", "bindings", "coverage")
                 for index, row in enumerate(base[section]) for field in row]
        for section, index, field in paths:
            for replacement in (None, True, -1, [], {}, "synthetic-invalid"):
                p = copy.deepcopy(base)
                p[section][index][field] = replacement
                try:
                    project_work_state(p)
                except WorkStateError as error:
                    self.assertRegex(str(error), r"^[A-Z_]+$")
                except Exception as error:
                    self.fail("Raw error at %s/%s/%s: %s" % (section, index, field, type(error).__name__))


if __name__ == "__main__":
    unittest.main()
