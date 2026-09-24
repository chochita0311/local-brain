import copy
import itertools
import json
import random
import subprocess
import sys
import unittest

from localbrain.workstream_candidates import (
    MAX_ARTIFACTS,
    MAX_LATEST_SAMPLES,
    MAX_MEMBERSHIPS,
    MAX_OVERLAP_SAMPLES,
    MAX_PAIRS,
    MAX_REFERENCES,
    MAX_REFERENCE_SAMPLES,
    MAX_SESSIONS,
    CandidateCoverage,
    CandidateLimitError,
    candidate_artifact_from_record,
    candidate_artifact_key,
    candidate_reference_from_record,
    candidate_session_from_record,
    normalize_workstream_candidates,
    workstream_candidate_key,
)
from localbrain.workflow_projection import workflow_episode_key


class WorkstreamCandidateContractTests(unittest.TestCase):
    def artifact(self, identity="goal.md", **overrides):
        row = {
            "kind": "context-document",
            "source_scope": "synthetic-context",
            "source_identity": identity,
            "title": "Synthetic improvement effort",
            "identity_state": "resolved",
            "enabled": True,
            "is_container": False,
            "availability": "available",
            "freshness": "current",
        }
        row.update(overrides)
        return row

    def session(self, number=1, **overrides):
        row = {
            "id": number,
            "source_key": "synthetic-codex",
            "external_id": "native-session-{}".format(number),
            "session_class": "work",
            "session_role": "primary",
            "index_policy": "full",
            "event_count": 2,
            "title": "Synthetic task {}".format(number),
            "workspace_id": number,
            "ended_at": "2030-01-01T00:00:00Z",
        }
        row.update(overrides)
        return row

    def artifact_key(self, row):
        return candidate_artifact_key(row["kind"], row["source_scope"], row["source_identity"])

    def reference(self, session, artifact, occurrence="event-1:1", **overrides):
        row = {
            "episode_key": workflow_episode_key(session["source_key"], session["external_id"]),
            "artifact_key": self.artifact_key(artifact),
            "reference_identity": occurrence,
            "evidence_kind": "user_mention",
            "read_outcome": None,
            "observed_at": "2026-09-14T01:00:00Z",
        }
        row.update(overrides)
        return row

    def fixture(self, session_count=2):
        artifacts = [self.artifact(), self.artifact("42", kind="wiki-item", source_scope="example.test", title="Synthetic design")]
        sessions = [self.session(number) for number in range(1, session_count + 1)]
        references = [self.reference(session, artifact) for session in sessions for artifact in artifacts]
        pairs = [tuple(self.artifact_key(artifact) for artifact in artifacts)]
        return artifacts, sessions, references, pairs

    def candidate(self, data=None):
        result = normalize_workstream_candidates(*(data or self.fixture()))
        self.assertEqual(len(result.candidates), 1)
        return result.candidates[0]

    def codes(self, result):
        return {diagnostic.code: diagnostic.count for diagnostic in result.diagnostics}

    def test_candidate_spans_sources_workspaces_and_more_than_focus_limit(self):
        data = self.fixture(26)
        for index, session in enumerate(data[1]):
            session["source_key"] = ("synthetic-claude", "synthetic-codex", "synthetic-company")[index % 3]
        data = (data[0], data[1], [self.reference(s, a) for s in data[1] for a in data[0]], data[3])
        candidate = self.candidate(data)
        self.assertEqual(len(candidate.members), 26)
        self.assertEqual({a.kind for a in candidate.anchors}, {"context-document", "wiki-item"})
        self.assertEqual(len({member.session.source_key for member in candidate.members}), 3)

    def test_keys_are_scoped_length_delimited_and_pair_order_independent(self):
        first = candidate_artifact_key("context-document", "ab", "c")
        second = candidate_artifact_key("context-document", "a", "bc")
        self.assertNotEqual(first, second)
        self.assertNotEqual(first, candidate_artifact_key("wiki-item", "ab", "c"))
        self.assertEqual(workstream_candidate_key(first, second), workstream_candidate_key(second, first))
        with self.assertRaises(ValueError):
            workstream_candidate_key(first, first)

    def test_same_native_session_id_in_two_sources_remains_two_members(self):
        artifacts, sessions, refs, pairs = self.fixture()
        sessions[1].update(
            source_key="synthetic-claude", external_id=sessions[0]["external_id"]
        )
        refs = [self.reference(s, a) for s in sessions for a in artifacts]
        candidate = self.candidate((artifacts, sessions, refs, pairs))
        self.assertEqual(len({m.session.episode_key for m in candidate.members}), 2)

    def test_local_ids_titles_and_source_state_do_not_redefine_membership(self):
        data = self.fixture()
        before = normalize_workstream_candidates(*data)
        changed = copy.deepcopy(data)
        changed[0][0].update(title="Renamed effort", id=999, availability="missing", freshness="stale")
        for session in changed[1]:
            session.update(id=session["id"] + 100, title="Renamed task", workspace_id=999)
        after = normalize_workstream_candidates(*changed)
        self.assertEqual(before.candidates[0].candidate_key, after.candidates[0].candidate_key)
        self.assertEqual(before.candidates[0].membership_revision, after.candidates[0].membership_revision)
        self.assertNotEqual(before.revision, after.revision)
        self.assertEqual(after.candidates[0].label, "Renamed effort")
        self.assertTrue(all(m.session.session_id > 100 for m in after.candidates[0].members))

    def test_adding_member_changes_revision_without_changing_seed(self):
        before = self.candidate(self.fixture(2))
        after = self.candidate(self.fixture(3))
        self.assertEqual(before.candidate_key, after.candidate_key)
        self.assertNotEqual(before.membership_revision, after.membership_revision)

    def test_one_session_cannot_become_two_by_duplication(self):
        artifacts, sessions, refs, pairs = self.fixture(1)
        result = normalize_workstream_candidates(artifacts, sessions * 8, refs * 8, pairs * 8)
        self.assertFalse(result.candidates)
        self.assertEqual(self.codes(result), {"insufficient-sessions": 1})

    def test_aliases_and_duplicate_occurrences_do_not_add_anchor_or_support(self):
        artifacts, sessions, refs, pairs = self.fixture()
        alias = dict(artifacts[0], id=999, alias_url="https://example.test/alternate")
        result = normalize_workstream_candidates(artifacts + [alias], sessions * 2, refs * 3, pairs + [pairs[0][::-1]])
        self.assertEqual(result, normalize_workstream_candidates(artifacts, sessions, refs, pairs))
        self.assertTrue(all(s.reference_count == 1 for m in result.candidates[0].members for s in m.supports))
        same_anchor = normalize_workstream_candidates(artifacts + [alias], sessions, refs, [(pairs[0][0], self.artifact_key(alias))])
        self.assertFalse(same_anchor.candidates)
        self.assertIn("invalid-pair", self.codes(same_anchor))

    def test_each_session_must_support_both_anchors(self):
        artifacts, sessions, refs, pairs = self.fixture()
        result = normalize_workstream_candidates(artifacts, sessions, [refs[0], refs[3]], pairs)
        self.assertFalse(result.candidates)
        self.assertIn("insufficient-sessions", self.codes(result))

    def test_mixed_session_has_separate_membership_reasons(self):
        artifacts, sessions, refs, pairs = self.fixture(3)
        artifacts += [self.artifact("other-goal.md"), self.artifact("other-design.md")]
        refs = [self.reference(s, a) for s in sessions[:2] for a in artifacts[:2]]
        refs += [self.reference(s, a) for s in (sessions[0], sessions[2]) for a in artifacts[2:]]
        pairs += [tuple(self.artifact_key(a) for a in artifacts[2:])]
        result = normalize_workstream_candidates(artifacts, sessions, refs, pairs)
        self.assertEqual(len(result.candidates), 2)
        mixed_key = workflow_episode_key(sessions[0]["source_key"], sessions[0]["external_id"])
        for candidate in result.candidates:
            self.assertIn(mixed_key, {m.session.episode_key for m in candidate.members})
            allowed = {a.artifact_key for a in candidate.anchors}
            self.assertEqual({s.artifact_key for m in candidate.members for s in m.supports}, allowed)
            self.assertEqual(candidate.overlaps[0].shared_session_count, 1)
            self.assertEqual(candidate.overlaps[0].shared_artifact_count, 0)

    def test_shared_anchor_does_not_transitively_merge_or_invent_pairs(self):
        artifacts, sessions, refs, pairs = self.fixture(3)
        artifacts.append(self.artifact("parallel.md"))
        refs = [self.reference(s, a) for s in sessions[:2] for a in artifacts[:2]]
        refs += [self.reference(s, a) for s in sessions[1:] for a in (artifacts[0], artifacts[2])]
        other_pair = (self.artifact_key(artifacts[0]), self.artifact_key(artifacts[2]))
        result = normalize_workstream_candidates(artifacts, sessions, refs, pairs + [other_pair])
        self.assertEqual(len(result.candidates), 2)
        self.assertTrue(all(len(c.members) == 2 for c in result.candidates))
        self.assertTrue(all(c.overlaps[0].shared_artifact_count == 1 for c in result.candidates))
        selected_only = normalize_workstream_candidates(artifacts, sessions, refs, pairs)
        self.assertEqual(len(selected_only.candidates), 1)

    def test_weak_signals_and_explicit_organization_cannot_supply_an_anchor(self):
        artifacts, sessions, refs, pairs = self.fixture()
        for signal in ("same-workspace", "same-git-branch", "lexical-overlap", "temporal-proximity", "workstream-membership", "user-assertion"):
            with self.subTest(signal=signal):
                weak = [dict(ref, evidence_kind=signal) for ref in refs]
                result = normalize_workstream_candidates(artifacts, sessions, weak, pairs)
                self.assertFalse(result.candidates)
                self.assertEqual(self.codes(result)["invalid-reference"], 4)

    def test_failed_or_unconfirmed_reads_cannot_supply_membership(self):
        artifacts, sessions, refs, pairs = self.fixture()
        for kind, outcome in itertools.product(("resource_read", "tool_result"), (None, "failure", "success")):
            with self.subTest(kind=kind, outcome=outcome):
                read_refs = [dict(ref, evidence_kind=kind, read_outcome=outcome) for ref in refs]
                result = normalize_workstream_candidates(artifacts, sessions, read_refs, pairs)
                self.assertEqual(bool(result.candidates), outcome == "success")
                if outcome != "success":
                    self.assertEqual(self.codes(result)["weak-reference"], 4)

    def test_session_eligibility_is_strict_and_usage_can_prove_meaningful(self):
        for override in ({"session_class": "maintenance"}, {"session_role": "subsession"}, {"index_policy": "metadata-only"}, {"event_count": 0}, {"has_usage_records": "true"}, {"id": True}, {"event_count": True}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                candidate_session_from_record(self.session(**override))
        for flag in ("has_usage_records", "has_activity_events"):
            session = candidate_session_from_record(self.session(event_count=0, **{flag: True}))
            self.assertEqual(session.session_id, 1)

    def test_excluded_artifacts_never_qualify_a_pair(self):
        for override, diagnostic in (({"enabled": False}, "disabled-artifact"), ({"identity_state": "unresolved"}, "unresolved-artifact"), ({"identity_state": "ambiguous"}, "ambiguous-artifact"), ({"is_container": True}, "container-artifact")):
            with self.subTest(override=override):
                data = self.fixture()
                data[0][0].update(override)
                result = normalize_workstream_candidates(*data)
                self.assertFalse(result.candidates)
                self.assertIn(diagnostic, self.codes(result))

    def test_stale_and_unavailable_retained_artifacts_remain_labeled(self):
        data = self.fixture()
        data[0][0].update(availability="unavailable", freshness="stale")
        candidate = self.candidate(data)
        anchor = next(a for a in candidate.anchors if a.kind == "context-document")
        self.assertEqual((anchor.availability, anchor.freshness), ("unavailable", "stale"))

    def test_source_loss_abstains_and_restoration_recovers_original_key(self):
        data = self.fixture()
        before = self.candidate(data)
        missing = normalize_workstream_candidates(data[0][1:], *data[1:])
        self.assertFalse(missing.candidates)
        self.assertIn("missing-pair-anchor", self.codes(missing))
        self.assertEqual(self.candidate(data), before)

    def test_reference_times_own_progress_and_session_end_never_closes(self):
        data = self.fixture()
        data[2][0]["observed_at"] = "2026-09-14T10:00:00+09:00"
        data[2][-1]["observed_at"] = "2026-09-15T03:00:00Z"
        for row in data[2]:
            row["imported_at"] = "2040-01-01T00:00:00Z"
        candidate = self.candidate(data)
        self.assertEqual(candidate.observed_start_at, "2026-09-14T01:00:00.000000+00:00")
        self.assertEqual(candidate.last_observed_at, "2026-09-15T03:00:00.000000+00:00")
        self.assertEqual(candidate.latest_observation_count, 1)
        self.assertEqual(candidate.authority, "deterministic-candidate")
        self.assertEqual((candidate.lifecycle_state, candidate.activity_state), ("unknown", "unknown"))
        self.assertIsNone(candidate.outcome)
        self.assertIsNone(candidate.next_action)
        self.assertIsNone(candidate.closure_reason)

    def test_invalid_missing_and_overflowing_times_remain_unknown(self):
        data = self.fixture()
        for row, value in zip(data[2], (None, "bad-time", "", "0001-01-01T00:00:00+01:00")):
            row["observed_at"] = value
        candidate = self.candidate(data)
        self.assertIsNone(candidate.observed_start_at)
        self.assertIsNone(candidate.last_observed_at)
        self.assertEqual(candidate.unknown_time_count, 4)
        self.assertEqual(candidate.latest_observations, ())

    def test_reference_samples_keep_full_counts_bounds_and_revision(self):
        artifacts, sessions, refs, pairs = self.fixture()
        refs = [self.reference(s, a, "event-{}".format(i), observed_at="2026-09-{:02d}T01:00:00Z".format(i + 1)) for s in sessions for a in artifacts for i in range(8)]
        candidate = self.candidate((artifacts, sessions, refs, pairs))
        for member in candidate.members:
            for support in member.supports:
                self.assertEqual(support.reference_count, 8)
                self.assertEqual(len(support.references), MAX_REFERENCE_SAMPLES)
                self.assertEqual(support.observed_start_at, "2026-09-01T01:00:00.000000+00:00")
                self.assertEqual(support.references[0].observed_at, "2026-09-08T01:00:00.000000+00:00")
        refs[0]["observed_at"] = "2026-08-01T01:00:00Z"
        changed = self.candidate((artifacts, sessions, refs, pairs))
        self.assertNotEqual(candidate.membership_revision, changed.membership_revision)
        self.assertEqual(candidate.candidate_key, changed.candidate_key)

    def test_latest_reference_ties_are_bounded_with_total(self):
        candidate = self.candidate(self.fixture(6))
        self.assertEqual(candidate.latest_observation_count, 12)
        self.assertEqual(len(candidate.latest_observations), MAX_LATEST_SAMPLES)

    def test_overlaps_have_bounded_samples_and_full_count(self):
        artifacts = [self.artifact("anchor-{}.md".format(i)) for i in range(23)]
        sessions = [self.session(1), self.session(2)]
        refs = [self.reference(s, a) for s in sessions for a in artifacts]
        pairs = [(self.artifact_key(artifacts[0]), self.artifact_key(a)) for a in artifacts[1:]]
        result = normalize_workstream_candidates(artifacts, sessions, refs, pairs)
        self.assertEqual(len(result.candidates), 22)
        for candidate in result.candidates:
            self.assertEqual(candidate.overlap_count, 21)
            self.assertEqual(len(candidate.overlaps), MAX_OVERLAP_SAMPLES)

    def test_labels_are_attributed_bounded_and_have_honest_fallback(self):
        data = self.fixture()
        data[0][0]["title"] = "한" * 700
        candidate = self.candidate(data)
        self.assertEqual(len(candidate.label), 500)
        self.assertEqual(candidate.label_authority, "source-metadata")
        self.assertEqual(candidate.label_artifact_key, self.artifact_key(data[0][0]))
        data[0][0]["title"] = None
        self.assertEqual(self.candidate(data).label, "Synthetic design")
        data[0][1]["title"] = "  "
        fallback = self.candidate(data)
        self.assertEqual(fallback.label, "Unnamed work candidate")
        self.assertEqual(fallback.label_authority, "fallback")
        self.assertIsNone(fallback.label_artifact_key)

    def test_conflicting_artifact_session_or_reference_is_not_chosen_by_order(self):
        for collection, field, value, diagnostic in ((0, "freshness", "stale", "conflicting-artifact"), (1, "id", 999, "conflicting-session"), (2, "observed_at", "2020-01-01T00:00:00Z", "conflicting-reference")):
            with self.subTest(collection=collection):
                data = self.fixture()
                data[collection].append(dict(data[collection][0], **{field: value}))
                forward = normalize_workstream_candidates(*data)
                backward = normalize_workstream_candidates(*(list(reversed(rows)) for rows in data))
                self.assertEqual(forward, backward)
                self.assertFalse(forward.candidates)
                self.assertEqual(self.codes(forward)[diagnostic], 1)

    def test_permutations_of_all_inputs_produce_identical_results(self):
        data = self.fixture(5)
        expected = normalize_workstream_candidates(*data)
        rng = random.Random(42)
        for _ in range(12):
            shuffled = copy.deepcopy(data)
            for rows in shuffled:
                rng.shuffle(rows)
            shuffled[3][0] = shuffled[3][0][::-1]
            self.assertEqual(normalize_workstream_candidates(*shuffled), expected)

    def test_unrelated_references_and_session_metadata_do_not_change_candidate(self):
        data = self.fixture()
        before = self.candidate(data)
        data[0].append(self.artifact("unrelated.md"))
        data[2].append(self.reference(data[1][0], data[0][-1], observed_at="2050-01-01T00:00:00Z"))
        data[1][0].update(ended_at="2050-01-01T00:00:00Z", intent="Different effort", current_goal="Not this candidate")
        self.assertEqual(self.candidate(data), before)

    def test_unknown_or_complete_coverage_never_implies_whole_corpus(self):
        default = normalize_workstream_candidates([], [], [], [])
        self.assertFalse(default.coverage.complete)
        self.assertIsNone(default.coverage.unexamined_session_count)
        complete = normalize_workstream_candidates([], [], [], [], coverage=CandidateCoverage(True, 0))
        self.assertTrue(complete.coverage.complete)
        self.assertEqual(complete.scope, "supplied-facts")
        self.assertNotEqual(default.revision, complete.revision)
        partial = normalize_workstream_candidates(*self.fixture(), coverage=CandidateCoverage(False, 25))
        self.assertTrue(partial.candidates)
        self.assertEqual(partial.coverage.unexamined_session_count, 25)
        for args in ((True, None), (True, 1), (False, -1), (False, True), ("true", 0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                CandidateCoverage(*args)

    def test_malformed_facts_and_missing_endpoints_are_bounded_diagnostics(self):
        data = self.fixture()
        data[0].append({"source_identity": "sensitive-invalid-artifact"})
        data[1].append("sensitive-invalid-session")
        data[2].append(dict(data[2][0], episode_key="session:" + "0" * 64))
        data[2].append(dict(data[2][0], artifact_key="artifact:" + "1" * 64))
        data[3].append(("sensitive-invalid-key", "bad"))
        result = normalize_workstream_candidates(*data)
        self.assertEqual(len(result.candidates), 1)
        codes = self.codes(result)
        for expected in ("invalid-artifact", "invalid-session", "missing-session", "missing-artifact", "invalid-pair"):
            self.assertIn(expected, codes)
        self.assertNotIn("sensitive-invalid", json.dumps(result.as_dict()))

    def test_input_limits_stop_after_limit_plus_one_without_prefix_success(self):
        for index, limit in enumerate((MAX_ARTIFACTS, MAX_SESSIONS, MAX_REFERENCES, MAX_PAIRS)):
            with self.subTest(index=index):
                consumed = []
                def rows():
                    for number in range(limit + 10):
                        consumed.append(number)
                        yield {}
                data = list(self.fixture())
                data[index] = rows()
                with self.assertRaises(CandidateLimitError):
                    normalize_workstream_candidates(*data)
                self.assertEqual(len(consumed), limit + 1)

    def test_output_membership_limit_is_explicit(self):
        data = self.fixture(MAX_MEMBERSHIPS // 2 + 1)
        data[0].append(self.artifact("second-effort.md"))
        data[2].extend(self.reference(s, data[0][-1]) for s in data[1])
        data[3].append((self.artifact_key(data[0][0]), self.artifact_key(data[0][-1])))
        with self.assertRaises(CandidateLimitError):
            normalize_workstream_candidates(*data)

    def test_serialization_excludes_native_identities_bodies_paths_and_payloads(self):
        data = self.fixture()
        sensitive = {
            "body": "SYNTHETIC-BODY-MUST-NOT-COPY",
            "source_path": "/synthetic/private/source.jsonl",
            "payload": {"token": "SYNTHETIC-TOKEN-MUST-NOT-COPY"},
            "source_native_id": "SYNTHETIC-NATIVE-MUST-NOT-COPY",
        }
        for rows in data[:3]:
            for row in rows:
                row.update(sensitive)
        encoded = json.dumps(normalize_workstream_candidates(*data).as_dict())
        for value in ("SYNTHETIC-BODY", "/synthetic/private", "SYNTHETIC-TOKEN", "SYNTHETIC-NATIVE", "native-session-1", "goal.md", "event-1:1"):
            self.assertNotIn(value, encoded)
        for field in ("body", "source_path", "payload", "source_identity", "external_id", "reference_identity"):
            self.assertNotIn('"{}":'.format(field), encoded)

    def test_normalization_does_not_mutate_supplied_facts(self):
        data = self.fixture()
        original = copy.deepcopy(data)
        normalize_workstream_candidates(*data)
        self.assertEqual(data, original)

    def test_invalid_identity_flags_and_read_values_raise_fixed_errors(self):
        for field, value in (("enabled", "yes"), ("identity_state", []), ("is_container", 1), ("freshness", "secret-invalid-state"), ("source_identity", "x" * 4097), ("source_scope", "scope\nsecret")):
            with self.subTest(field=field), self.assertRaises(ValueError) as raised:
                candidate_artifact_from_record(self.artifact(**{field: value}))
            self.assertNotIn("secret", str(raised.exception))
        ref = self.fixture()[2][0]
        with self.assertRaises(ValueError):
            candidate_reference_from_record(dict(ref, read_outcome="unsupported"))

    def test_module_initialization_and_normalization_do_no_application_io(self):
        script = """
import builtins
import json
import pathlib
import socket
import sqlite3
import subprocess
import sys
from unittest.mock import patch
from localbrain import activity, workflow_projection
def forbidden(*args, **kwargs):
    raise AssertionError('unexpected application I/O')
with patch.object(builtins, 'open', forbidden), patch.object(pathlib.Path, 'open', forbidden), patch.object(pathlib.Path, 'read_text', forbidden), patch.object(sqlite3, 'connect', forbidden), patch.object(socket, 'socket', forbidden), patch.object(subprocess, 'Popen', forbidden):
    from localbrain.workstream_candidates import normalize_workstream_candidates
    result = normalize_workstream_candidates([], [], [], [])
    assert not result.candidates
    assert result.as_dict()['scope'] == 'supplied-facts'
    populated = normalize_workstream_candidates(*json.loads(sys.argv[1]))
    assert len(populated.as_dict()['candidates']) == 1
"""
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, json.dumps(self.fixture())],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
