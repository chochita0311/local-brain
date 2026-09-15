import json
import unittest

from localbrain.workflow_projection import (
    ACTIVITY_STATES,
    AUTHORITY_STATES,
    CLOSURE_REASONS,
    LIFECYCLE_STATES,
    WORKFLOW_PROJECTION_VERSION,
    WORKFLOW_RELATION_KINDS,
    WorkflowRelation,
    WorkflowRelationReason,
    normalize_workflow_relations,
    workflow_episode_from_session,
    workflow_episode_key,
)


class WorkflowEpisodeContractTests(unittest.TestCase):
    def session(self, **overrides):
        values = {
            "id": 17,
            "source_key": "codex-company",
            "external_id": "native-session-1",
            "session_class": "work",
            "session_role": "primary",
            "title": "Synthetic workflow investigation",
            "started_at": "2026-09-14T10:00:00+09:00",
            "first_event_at": "2026-09-14T01:01:00Z",
            "last_event_at": "2026-09-14T02:30:00Z",
            "ended_at": "2026-09-14T02:20:00Z",
            "workspace_id": 3,
            "workspace_name": "Synthetic Project",
            "git_branch": "feature/workflow-map",
        }
        values.update(overrides)
        return values

    def test_episode_key_is_source_scoped_and_independent_of_local_row(self):
        first = workflow_episode_from_session(self.session())
        same_native = workflow_episode_from_session(
            self.session(id=99, title="Renamed", workspace_id=7)
        )
        another_source = workflow_episode_from_session(
            self.session(source_key="codex")
        )

        self.assertEqual(first.episode_key, same_native.episode_key)
        self.assertNotEqual(first.episode_key, another_source.episode_key)
        self.assertTrue(first.episode_key.startswith("session:"))
        self.assertEqual(len(first.episode_key), len("session:") + 64)

    def test_length_delimited_key_avoids_boundary_collision(self):
        self.assertNotEqual(
            workflow_episode_key("ab", "c"),
            workflow_episode_key("a", "bc"),
        )

    def test_episode_uses_earliest_and_latest_valid_utc_observations(self):
        episode = workflow_episode_from_session(self.session())

        self.assertEqual(episode.observed_start_at, "2026-09-14T01:00:00+00:00")
        self.assertEqual(episode.last_observed_at, "2026-09-14T02:30:00+00:00")
        self.assertEqual(episode.lifecycle_state, "unknown")
        self.assertIsNone(episode.closure_reason)

    def test_invalid_timestamps_remain_absent_without_fabrication(self):
        episode = workflow_episode_from_session(
            self.session(
                started_at="not-a-time",
                first_event_at=None,
                last_event_at=None,
                ended_at="",
            )
        )

        self.assertIsNone(episode.observed_start_at)
        self.assertIsNone(episode.last_observed_at)

    def test_episode_bounds_fields_and_serializes_without_native_identity(self):
        episode = workflow_episode_from_session(
            self.session(title="T" * 700),
            intent="I" * 2_100,
            outcome="O" * 2_100,
            next_action="N" * 2_100,
            evidence_counts={"wiki": 2, "session": 1},
            activity_state="quiet",
            lifecycle_state="open",
        )
        payload = episode.as_dict()

        self.assertEqual(len(episode.display_title), 500)
        self.assertEqual(len(episode.intent), 2_000)
        self.assertEqual(len(episode.outcome), 2_000)
        self.assertEqual(len(episode.next_action), 2_000)
        self.assertEqual(episode.evidence_counts, (("session", 1), ("wiki", 2)))
        self.assertNotIn("external_id", payload)
        self.assertNotIn("source_path", payload)
        json.dumps(payload, sort_keys=True)

    def test_session_end_never_closes_episode(self):
        episode = workflow_episode_from_session(
            self.session(ended_at="2026-09-14T05:00:00Z"),
            activity_state="active",
            lifecycle_state="open",
        )

        self.assertEqual(episode.lifecycle_state, "open")
        self.assertIsNone(episode.closure_reason)
        self.assertEqual(episode.last_observed_at, "2026-09-14T05:00:00+00:00")

    def test_only_primary_work_sessions_are_eligible(self):
        for overrides in (
            {"session_class": "maintenance"},
            {"session_role": "subsession"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    workflow_episode_from_session(self.session(**overrides))

    def test_lifecycle_and_state_parity_is_validated(self):
        closed = workflow_episode_from_session(
            self.session(), lifecycle_state="closed", closure_reason="completed"
        )
        self.assertEqual(closed.closure_reason, "completed")

        for kwargs in (
            {"lifecycle_state": "closed"},
            {"lifecycle_state": "open", "closure_reason": "completed"},
            {"activity_state": "stale"},
            {"authority": "guessed"},
            {"evidence_counts": {"session": -1}},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    workflow_episode_from_session(self.session(), **kwargs)

    def test_contract_vocabularies_are_exact(self):
        self.assertEqual(ACTIVITY_STATES, {"active", "quiet", "unknown"})
        self.assertEqual(LIFECYCLE_STATES, {"open", "closed", "unknown"})
        self.assertEqual(
            CLOSURE_REASONS,
            {"completed", "abandoned", "superseded", "merged", "other"},
        )
        self.assertEqual(
            AUTHORITY_STATES,
            {
                "observed",
                "deterministic-candidate",
                "explicit-organization",
                "user-confirmed",
            },
        )
        self.assertEqual(
            WORKFLOW_RELATION_KINDS,
            {"continues", "branches-from", "merged-into"},
        )


class WorkflowRelationContractTests(unittest.TestCase):
    def relation(
        self,
        source="session:a",
        target="session:b",
        kind="continues",
        authority="deterministic-candidate",
        reasons=None,
        source_at="2026-09-14T01:00:00Z",
        target_at="2026-09-14T02:00:00Z",
    ):
        return WorkflowRelation(
            source_episode_key=source,
            target_episode_key=target,
            kind=kind,
            authority=authority,
            reasons=reasons
            if reasons is not None
            else (
                WorkflowRelationReason("shared-reference", "target:synthetic"),
            ),
            source_observed_at=source_at,
            target_observed_at=target_at,
        )

    def test_all_approved_relation_kinds_are_retained(self):
        relations = [
            self.relation(
                source="session:{}".format(index),
                target="session:{}".format(index + 1),
                kind=kind,
                source_at="2026-09-14T0{}:00:00Z".format(index),
                target_at="2026-09-14T0{}:30:00Z".format(index),
            )
            for index, kind in enumerate(
                ("continues", "branches-from", "merged-into"), start=1
            )
        ]

        normalized = normalize_workflow_relations(reversed(relations))

        self.assertEqual(len(normalized.relations), 3)
        self.assertFalse(normalized.diagnostics)
        self.assertEqual(normalized.projection_version, WORKFLOW_PROJECTION_VERSION)
        json.dumps(normalized.as_dict(), sort_keys=True)

    def test_supporting_signals_alone_do_not_establish_direction(self):
        relation = self.relation(
            reasons=(
                WorkflowRelationReason("same-workspace", "workspace:3"),
                WorkflowRelationReason("temporal-proximity", "within-day"),
            )
        )

        normalized = normalize_workflow_relations([relation])

        self.assertFalse(normalized.relations)
        self.assertEqual(
            [item.code for item in normalized.diagnostics],
            ["missing-strong-reason"],
        )

    def test_self_and_non_forward_edges_are_omitted(self):
        normalized = normalize_workflow_relations(
            [
                self.relation(source="session:a", target="session:a"),
                self.relation(
                    source="session:b",
                    target="session:c",
                    source_at="2026-09-14T03:00:00Z",
                    target_at="2026-09-14T02:00:00Z",
                ),
            ]
        )

        self.assertFalse(normalized.relations)
        self.assertEqual(
            sorted(item.code for item in normalized.diagnostics),
            ["non-forward-time", "self-edge"],
        )

    def test_authority_requires_its_own_reason(self):
        user_relation = self.relation(authority="user-confirmed")
        organization_relation = self.relation(authority="explicit-organization")

        normalized = normalize_workflow_relations(
            [user_relation, organization_relation]
        )

        self.assertFalse(normalized.relations)
        self.assertEqual(
            [item.code for item in normalized.diagnostics],
            ["authority-reason-mismatch", "authority-reason-mismatch"],
        )

    def test_user_and_organization_authority_accept_matching_reasons(self):
        normalized = normalize_workflow_relations(
            [
                self.relation(
                    source="session:a",
                    target="session:b",
                    authority="user-confirmed",
                    reasons=(
                        WorkflowRelationReason("user-assertion", "assertion:1"),
                    ),
                ),
                self.relation(
                    source="session:b",
                    target="session:c",
                    authority="explicit-organization",
                    reasons=(
                        WorkflowRelationReason("thread-membership", "thread:2"),
                    ),
                    source_at="2026-09-14T02:00:00Z",
                    target_at="2026-09-14T03:00:00Z",
                ),
            ]
        )

        self.assertEqual(len(normalized.relations), 2)
        self.assertFalse(normalized.diagnostics)

    def test_cycle_is_omitted_deterministically(self):
        first = self.relation(
            source="session:a",
            target="session:b",
            source_at="2026-09-14T01:00:00Z",
            target_at="2026-09-14T02:00:00Z",
        )
        conflicting = self.relation(
            source="session:b",
            target="session:a",
            source_at="2026-09-14T03:00:00Z",
            target_at="2026-09-14T04:00:00Z",
        )

        forward = normalize_workflow_relations([first, conflicting])
        reversed_input = normalize_workflow_relations([conflicting, first])

        self.assertEqual(forward, reversed_input)
        self.assertEqual(len(forward.relations), 1)
        self.assertEqual(forward.relations[0].source_episode_key, "session:a")
        self.assertEqual(forward.relations[0].target_episode_key, "session:b")
        self.assertEqual(
            [item.code for item in forward.diagnostics], ["cycle-omitted"]
        )

    def test_reason_normalization_is_stable_and_bounded(self):
        relation = self.relation(
            reasons=(
                WorkflowRelationReason(
                    "shared-reference",
                    " target:synthetic ",
                    "2026-09-14T10:00:00+09:00",
                ),
                WorkflowRelationReason("same-git-root", "repo:synthetic"),
                WorkflowRelationReason("same-git-root", "repo:synthetic"),
            )
        )
        normalized = normalize_workflow_relations([relation])

        self.assertEqual(
            normalized.relations[0].reasons,
            (
                WorkflowRelationReason("same-git-root", "repo:synthetic"),
                WorkflowRelationReason(
                    "shared-reference",
                    "target:synthetic",
                    "2026-09-14T01:00:00+00:00",
                ),
            ),
        )

        overlong = self.relation(
            source="session:c",
            target="session:d",
            reasons=(WorkflowRelationReason("shared-reference", "x" * 501),),
        )
        invalid = normalize_workflow_relations([overlong])
        self.assertEqual(
            [item.code for item in invalid.diagnostics], ["invalid-value"]
        )


if __name__ == "__main__":
    unittest.main()
