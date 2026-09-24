import copy
import unittest

from localbrain.work_reconstruction import (
    ExperimentError, reconstruct, metadata_baseline, metadata_view, digest,
)
from localbrain.work_reconstruction_scoring import compare_snapshot, score, stability
from work_reconstruction_cases import (
    LANGUAGE_CASES, bind_expectations, goal, long_history, member, record, snapshot,
)


class WorkReconstructionTests(unittest.TestCase):
    def test_natural_language_and_supplied_paraphrases(self):
        for text, subject, change in LANGUAGE_CASES:
            with self.subTest(text=text):
                result = reconstruct(snapshot([record("r", text)]))
                self.assertEqual(len(result["flows"]), 1)
                flow = result["flows"][0]
                self.assertEqual((flow["subject"], flow["change"]), (subject, change))
                self.assertEqual(flow["members"][0]["record_key"], "r")
                self.assertEqual(flow["authority"], "inferred")
                claim = flow["members"][0]
                self.assertEqual(claim["wording_authority"], "observed")
                self.assertTrue(all(e["authority"] == "observed" for e in claim["field_evidence"].values()))

    def test_unrecognized_and_negated_intent_abstains(self):
        for text in ("Continue.", "진행하자", "checkout handbook", "Do not enable audit logging.",
                     "https://example.test/goal", "We discussed checkout latency."):
            with self.subTest(text=text):
                result = reconstruct(snapshot([record("r", text)]))
                self.assertEqual(result["flows"], [])
                self.assertTrue(result["unassigned"])

    def test_multiline_markdown_and_decimal_completion_keep_exact_offsets(self):
        row = record("r", "- Fix parsing\n- Reduce latency until p95 is below 2.5 seconds.")
        result = reconstruct(snapshot([row]))
        self.assertEqual(len(result["flows"]), 2)
        for flow in result["flows"]:
            claim = flow["members"][0]
            self.assertEqual(row["text"][claim["start"]:claim["end"]], claim["wording"])

    def test_phases_remain_subordinate_across_48_sessions(self):
        data, expected = long_history()
        report = compare_snapshot(data, bind_expectations(data, expected))
        self.assertEqual(len(report["text"]["flows"]), 10)
        self.assertEqual(report["text_scores"]["goal_coverage"], {"numerator": 10, "denominator": 10})
        self.assertEqual(report["text_scores"]["quality"], "pass")
        self.assertEqual(report["viability"], "unverified")
        large = max(report["text"]["flows"], key=lambda f: len(f["members"]))
        self.assertEqual(len(large["members"]), 30)
        self.assertEqual({m["phase"] for m in large["members"]}, {"investigation", "implementation", "verification"})

    def test_mixed_session_preserves_scoped_outcomes(self):
        row = record("mixed", "Enable audit logging. Disable public indexing.")
        data = snapshot([row])
        result = reconstruct(data)
        self.assertEqual(len(result["flows"]), 2)
        spans = [f["members"][0] for f in result["flows"]]
        self.assertNotEqual(spans[0]["statement_key"], spans[1]["statement_key"])
        self.assertTrue(all(s["record_key"] == "mixed" for s in spans))

    def test_opposite_actions_and_completion_conditions_do_not_merge(self):
        data = snapshot([record("a", "Reduce cache capacity."), record("b", "Increase cache capacity."),
                         record("c", "Reduce checkout latency until p95 is below 2 seconds."),
                         record("d", "Reduce checkout latency until p95 is below 5 seconds.")])
        self.assertEqual(len(reconstruct(data)["flows"]), 4)

    def test_same_goal_without_completion_does_not_bridge_conflicting_conditions(self):
        data = snapshot([record("a", "Reduce latency until p95 is below 2 seconds."),
                         record("b", "Reduce latency until p95 is below 5 seconds."),
                         record("c", "Reduce latency.")])
        result = reconstruct(data)
        self.assertEqual(len(result["flows"]), 2)
        self.assertTrue(result["unassigned"])

    def test_order_replay_unrelated_append_and_late_source_are_stable(self):
        data, _ = long_history()
        first = reconstruct(data)
        shuffled = copy.deepcopy(data)
        shuffled["records"].reverse()
        shuffled["sessions"].reverse()
        self.assertEqual(first, reconstruct(shuffled))
        extended = copy.deepcopy(data)
        extended["records"].append(record("other", "Add keyboard navigation.", 1,
                                          at="2029-12-31T23:59:59Z"))
        retained = stability(first, reconstruct(extended))
        self.assertEqual(retained["identities"], {"numerator": 10, "denominator": 10})
        self.assertEqual(retained["assignments"], {"numerator": 48, "denominator": 48})
        self.assertEqual(retained["label_changes"], 0)

    def test_cross_source_long_effort_survives_changing_workspaces_and_references(self):
        from localbrain.workstream_candidates import candidate_artifact_key
        from localbrain.workflow_projection import workflow_episode_key
        data, _ = long_history()
        original = reconstruct(data)
        for s in data["sessions"]:
            s["source_key"] = "synthetic-{}".format(s["id"] % 3)
            s["workspace_id"] = s["id"] % 4 + 1
            identity = "document-{}".format(s["id"])
            data["artifacts"].append({"kind": "context-document", "source_scope": "synthetic", "source_identity": identity,
                                      "identity_state": "resolved", "enabled": True, "is_container": False,
                                      "availability": "available", "freshness": "stale"})
            data["references"].append({"episode_key": workflow_episode_key(s["source_key"], s["external_id"]),
                                       "artifact_key": candidate_artifact_key("context-document", "synthetic", identity),
                                       "reference_identity": str(s["id"]), "evidence_kind": "user_mention",
                                       "read_outcome": None, "observed_at": "2030-01-01T00:00:00Z"})
        self.assertEqual(original, reconstruct(data))
        self.assertEqual(metadata_baseline(metadata_view(data))["flows"], [])

    def test_title_and_resource_changes_do_not_define_flow_identity(self):
        data = snapshot([record("a", "Fix document parsing.")])
        first = reconstruct(data)
        data["sessions"][0]["title"] = "Renamed document and workspace"
        self.assertEqual(first, reconstruct(data))

    def test_removed_source_has_no_fabricated_closure(self):
        data = snapshot([record("a", "Fix document parsing."), record("b", "Fix document parsing.", 2)])
        first = reconstruct(data)
        data["records"].pop()
        second = reconstruct(data)
        self.assertEqual(first["flows"][0]["flow_id"], second["flows"][0]["flow_id"])
        self.assertNotEqual(first["flows"][0]["revision"], second["flows"][0]["revision"])
        self.assertEqual(second["flows"][0]["lifecycle"], "unknown")

    def test_exact_corrections_survive_missing_source_without_expansion(self):
        data = snapshot([record("a", "Fix parsing."), record("b", "Fix parsing.", 2)])
        first = reconstruct(data)
        key = first["flows"][0]["members"][0]["statement_key"]
        correction = {"id": "synthetic-correction", "statement_keys": [key], "label": "Separate investigation"}
        revised = reconstruct(data, [correction])
        self.assertEqual(len(revised["flows"]), 2)
        self.assertEqual(revised["corrections"][0]["active_count"], 1)
        data["records"].append(record("new", "Fix parsing.", 2))
        continued = reconstruct(data, [correction])
        corrected = next(f for f in continued["flows"] if f["user_label"])
        self.assertEqual([m["statement_key"] for m in corrected["members"]], [key])
        data["records"] = []
        lost = reconstruct(data, [correction])
        self.assertEqual(lost["corrections"][0]["active_count"], 0)
        self.assertEqual(lost["corrections"][0]["statement_keys"], [key])

    def test_organization_is_optional_and_separate(self):
        data = snapshot([record("a", "Fix parsing."), record("owner", "Improve indexing.", None,
                           kind="organization", role="owner")])
        self.assertEqual(len(reconstruct(data)["flows"]), 2)
        self.assertEqual(len(reconstruct(data, include_organization=False)["flows"]), 1)

    def test_equal_length_source_edit_cannot_retarget_an_exact_correction(self):
        data = snapshot([record("r", "Fix parsing.")])
        statement = reconstruct(data)["flows"][0]["members"][0]["statement_key"]
        correction = {"id": "synthetic", "statement_keys": [statement], "label": "Parsing fix"}
        data["records"][0]["text"] = "Fix caching."
        revised = reconstruct(data, [correction])
        self.assertEqual(revised["corrections"][0]["active_count"], 0)
        self.assertEqual(revised["flows"][0]["subject"], "caching")
        self.assertIsNone(revised["flows"][0]["user_label"])

    def test_ineligible_sessions_never_supply_body_evidence(self):
        for field, value in (("session_class", "maintenance"), ("session_role", "subsession"),
                             ("index_policy", "metadata_only")):
            data = snapshot([record("r", "Fix parsing.")])
            data["sessions"][0][field] = value
            text = reconstruct(data)
            metadata = metadata_baseline(metadata_view(data))
            self.assertEqual(text["flows"], [])
            self.assertEqual(text["coverage"], {"complete": False, "unexamined": 1})
            self.assertEqual(text["coverage"], metadata["coverage"])

    def test_unknown_record_fields_duplicate_keys_and_limits_fail(self):
        variants = []
        a = snapshot([record("r", "Fix parsing.")]); a["records"][0]["expected_group"] = "gold"; variants.append(a)
        a = snapshot([record("r", "Fix parsing."), record("r", "Fix parsing.")]); variants.append(a)
        a = snapshot([record("r", "x" * 4001)]); variants.append(a)
        a = snapshot([record(str(n), "Fix parsing.", n+1) for n in range(61)]); variants.append(a)
        for data in variants:
            with self.subTest(data_digest=digest(data)), self.assertRaises(ExperimentError):
                reconstruct(data)

    def test_shared_ten_artifacts_yield_45_baseline_pairs_but_one_text_flow(self):
        from localbrain.workstream_candidates import candidate_artifact_key
        from localbrain.workflow_projection import workflow_episode_key
        rows = [record("a", "Improve session synchronization.", 1), record("b", "Improve session synchronization.", 2)]
        data = snapshot(rows)
        data["artifacts"] = [{"kind": "context-document", "source_scope": "synthetic", "source_identity": str(n),
                              "identity_state": "resolved", "enabled": True, "is_container": False,
                              "availability": "available", "freshness": "current"} for n in range(10)]
        data["references"] = [{"episode_key": workflow_episode_key("synthetic", str(s)),
                               "artifact_key": candidate_artifact_key("context-document", "synthetic", str(a)),
                               "reference_identity": "{}:{}".format(s, a), "evidence_kind": "user_mention",
                               "read_outcome": None, "observed_at": "2030-01-01T00:00:00Z"}
                              for s in (1, 2) for a in range(10)]
        self.assertEqual(len(metadata_baseline(metadata_view(data))["flows"]), 45)
        self.assertEqual(len(reconstruct(data)["flows"]), 1)

    def test_metadata_arm_rejects_text_snapshot(self):
        data = snapshot([record("r", "Fix parsing.")])
        with self.assertRaises(ExperimentError):
            metadata_baseline(data)
        self.assertNotIn("Fix parsing", str(metadata_view(data)))

    def test_remaining_snapshot_and_pair_caps_fail_without_prefix_results(self):
        from localbrain.workstream_candidates import candidate_artifact_key
        from localbrain.workflow_projection import workflow_episode_key
        variants = [snapshot([record(str(i), "x", 1) for i in range(201)]),
                    snapshot([record(str(i), "x" * 4000, 1) for i in range(9)])]
        for field, count in (("artifacts", 2001), ("references", 12001), ("organization_links", 201)):
            data = snapshot([record("r", "Fix parsing.")]); data[field] = [{}] * count; variants.append(data)
        for data in variants:
            with self.assertRaises(ExperimentError): reconstruct(data)
        data = snapshot([record("a", "Fix parsing.", 1), record("b", "Fix parsing.", 2)])
        data["artifacts"] = [{"kind": "context-document", "source_scope": "synthetic", "source_identity": str(i),
                              "identity_state": "resolved", "enabled": True, "is_container": False,
                              "availability": "available", "freshness": "current"} for i in range(92)]
        data["references"] = [{"episode_key": workflow_episode_key("synthetic", str(s)),
                               "artifact_key": candidate_artifact_key("context-document", "synthetic", str(i)),
                               "reference_identity": "{}:{}".format(s, i), "evidence_kind": "user_mention",
                               "read_outcome": None, "observed_at": "2030-01-01T00:00:00Z"}
                              for s in (1, 2) for i in range(92)]
        with self.assertRaisesRegex(ExperimentError, "BASELINE_LIMIT"):
            metadata_baseline(metadata_view(data))

    def test_pure_arms_do_not_access_sources_network_processes_or_database(self):
        from unittest.mock import patch
        import localbrain.workstream_candidates  # Preload existing pure dependencies.
        data = snapshot([record("r", "Fix parsing.")])
        with patch("builtins.open", side_effect=AssertionError("file access")), \
             patch("sqlite3.connect", side_effect=AssertionError("database access")), \
             patch("socket.socket", side_effect=AssertionError("network access")), \
             patch("subprocess.Popen", side_effect=AssertionError("process launch")):
            reconstruct(data)
            metadata_baseline(metadata_view(data))

    def test_reported_outcome_remains_attributed_without_closing_flow(self):
        data = snapshot([record("r", "Completed: fix parsing.", role="assistant")])
        flow = reconstruct(data)["flows"][0]
        self.assertEqual(flow["lifecycle"], "unknown")
        self.assertEqual(flow["members"][0]["role"], "assistant")
        self.assertIsNotNone(flow["members"][0]["outcome"])


class ReconstructionScoringTests(unittest.TestCase):
    def test_duplicate_assignments_cannot_dilute_errors(self):
        data, expected = long_history()
        output = reconstruct(data)
        flow = output["flows"][0]
        flow["members"].append(copy.deepcopy(flow["members"][0]))
        with self.assertRaises(ExperimentError): score(output, expected)

    def test_any_incompatible_merge_fails_even_below_error_percentage_budget(self):
        data, expected = long_history()
        output = reconstruct(data)
        long = max(output["flows"], key=lambda f: len(f["members"]))
        other = next(f for f in output["flows"] if f is not long)
        long["members"].append(copy.deepcopy(other["members"][0]))
        measured = score(output, expected)
        self.assertEqual(measured["incompatible_outcome_merges"], 1)
        self.assertFalse(measured["gates"]["incompatible_outcomes"])
        self.assertEqual(measured["quality"], "fail")

    def test_positive_and_negative_expectations_cannot_contradict(self):
        data, expected = long_history()
        expected["negative"] = [member(data["records"][0])]
        with self.assertRaises(ExperimentError):
            compare_snapshot(data, bind_expectations(data, expected))

    def test_missing_expectations_zero_denominators_do_not_pass(self):
        data = snapshot([record("r", "Fix parsing.")])
        expected = bind_expectations(data, {"version": 1, "groups": [], "negative": [], "unresolved": 1})
        result = compare_snapshot(data, expected)
        self.assertEqual(result["text_scores"]["quality"], "insufficient")

    def test_missing_label_assessment_is_not_correction_free(self):
        data, expected = long_history()
        for item in expected["groups"]:
            item["acceptable_labels"] = None
        result = compare_snapshot(data, bind_expectations(data, expected))
        self.assertEqual(result["text_scores"]["correction_free"]["numerator"], 0)
        self.assertEqual(result["text_scores"]["quality"], "insufficient")

    def test_expectation_digest_prevents_resampling(self):
        data, expected = long_history()
        bound = bind_expectations(data, expected)
        data["records"][0]["text"] = "Fix another outcome."
        with self.assertRaises(ExperimentError):
            compare_snapshot(data, bound)

    def test_wrong_group_and_fragments_are_not_hidden(self):
        data, expected = long_history()
        output = reconstruct(data)
        original = output["flows"][0]
        fragment = copy.deepcopy(original)
        fragment["flow_id"] += "-fragment"
        fragment["members"] = original["members"][:1]
        original["members"] = original["members"][1:]
        output["flows"].append(fragment)
        measured = score(output, expected)
        self.assertEqual(measured["excess_groups"], 1)
        self.assertLess(measured["correction_free"]["numerator"], 10)

    def test_partial_coverage_prevents_success(self):
        data, expected = long_history()
        data["coverage"] = {"complete": False, "unexamined": 1}
        result = compare_snapshot(data, bind_expectations(data, expected))
        self.assertEqual(result["text_scores"]["quality"], "insufficient")

    def test_no_fixed_global_cluster_count(self):
        data = snapshot([record(str(i), "Improve component {}.".format(i), i+1) for i in range(30)])
        self.assertEqual(len(reconstruct(data)["flows"]), 30)


if __name__ == "__main__":
    unittest.main()
