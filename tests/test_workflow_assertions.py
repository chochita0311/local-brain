import sqlite3
import unittest
from dataclasses import replace
from pathlib import Path

from localbrain.workflow_assertions import (
    MAX_WORKFLOW_ASSERTION_HISTORY,
    WORKFLOW_ASSERTION_KINDS,
    WORKFLOW_ASSERTION_OVERLAY_VERSION,
    WORKFLOW_ASSERTION_VERSION,
    WorkflowAssertionError,
    apply_workflow_assertion,
    overlay_workflow_assertions,
    undo_workflow_assertion,
    workflow_assertion_history,
    workflow_boundary_key,
)
from localbrain.workflow_focus import workflow_focus_projection
from localbrain.workflow_projection import WorkflowRelation, WorkflowRelationReason


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "src/localbrain/schema.sql").read_text(encoding="utf-8")


class WorkflowAssertionTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA)
        self.connection.executescript(
            """
            INSERT INTO sources(id, kind, provider_kind, name, root_path)
            VALUES (1, 'codex', 'codex', 'Codex', '/synthetic/codex');
            INSERT INTO workspaces(
                id, canonical_path, display_name, git_root, exists_now
            ) VALUES (
                1, '/synthetic/work', 'Synthetic Work', '/synthetic/work', 1
            );
            INSERT INTO workstreams(id, name) VALUES (1, 'Synthetic Flow');
            INSERT INTO threads(id, workstream_id, title)
            VALUES (1, 1, 'Synthetic Thread');
            """
        )

    def tearDown(self):
        self.connection.close()

    def add_session(
        self,
        session_id,
        hour,
        *,
        external_id=None,
        branch="main",
        link=True,
    ):
        observed_at = "2026-09-14T{:02d}:00:00Z".format(hour)
        self.connection.execute(
            """
            INSERT INTO sessions(
                id, source_id, workspace_id, external_id, source_path, cwd_raw,
                git_branch, title, started_at, last_event_at, event_count,
                session_class, session_role, index_policy
            ) VALUES (?, 1, 1, ?, ?, '/synthetic/work', ?, ?, ?, ?, 1,
                      'work', 'primary', 'full')
            """,
            (
                session_id,
                external_id or "native-{}".format(session_id),
                "/synthetic/session-{}.jsonl".format(session_id),
                branch,
                "Session {}".format(session_id),
                observed_at,
                observed_at,
            ),
        )
        if link:
            self.connection.execute(
                """
                INSERT INTO thread_links(
                    thread_id, entity_type, entity_id, linked_by
                ) VALUES (1, 'session', ?, 'user')
                """,
                (str(session_id),),
            )

    def add_chain(self, count=3):
        for offset in range(count):
            self.add_session(10 + offset, offset + 1)

    @staticmethod
    def keys(projection):
        return {
            view.episode.session_id: view.episode.episode_key
            for view in projection.episodes
        }

    def assert_error(self, code, callable_value):
        before = self.connection.execute(
            "SELECT COUNT(*) FROM workflow_assertions"
        ).fetchone()[0]
        with self.assertRaises(WorkflowAssertionError) as caught:
            callable_value()
        self.assertEqual(caught.exception.code, code)
        after = self.connection.execute(
            "SELECT COUNT(*) FROM workflow_assertions"
        ).fetchone()[0]
        self.assertEqual(after, before)

    def apply(self, projection, action, source, target=None, **values):
        return apply_workflow_assertion(
            self.connection,
            projection,
            assertion_kind=action,
            source_episode_key=source,
            target_episode_key=target,
            expected_revision=projection.assertion_revision,
            **values,
        )

    def test_schema_owns_exact_values_indexes_and_non_cascading_session_aids(self):
        columns = {
            row["name"]
            for row in self.connection.execute(
                "PRAGMA table_info(workflow_assertions)"
            )
        }
        self.assertEqual(
            columns,
            {
                "id",
                "boundary_key",
                "boundary_version",
                "boundary_kind",
                "assertion_kind",
                "is_undo",
                "source_episode_key",
                "target_episode_key",
                "source_session_id",
                "target_session_id",
                "before_meaning",
                "after_meaning",
                "before_closure_reason",
                "after_closure_reason",
                "note",
                "authority",
                "contract_version",
                "supersedes_assertion_id",
                "created_at",
            },
        )
        indexes = {
            row["name"]
            for row in self.connection.execute(
                "PRAGMA index_list(workflow_assertions)"
            )
        }
        self.assertTrue(
            {
                "idx_workflow_assertions_source_created",
                "idx_workflow_assertions_target_created",
            }.issubset(indexes)
        )
        foreign_keys = self.connection.execute(
            "PRAGMA foreign_key_list(workflow_assertions)"
        ).fetchall()
        self.assertEqual(len(foreign_keys), 3)
        self.assertEqual(
            sorted((row["table"], row["on_delete"]) for row in foreign_keys),
            [
                ("sessions", "SET NULL"),
                ("sessions", "SET NULL"),
                ("workflow_assertions", "RESTRICT"),
            ],
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO workflow_assertions(
                    boundary_key, boundary_version, boundary_kind,
                    assertion_kind, source_episode_key, target_episode_key,
                    before_meaning, after_meaning, contract_version, created_at
                ) VALUES (?, 1, 'relation', 'same-flow', ?, ?,
                          'relation:absent', 'relation:continues', ?, ?)
                """,
                (
                    "g" * 64,
                    "session:" + "0" * 63 + "g",
                    "session:" + "1" * 64,
                    WORKFLOW_ASSERTION_VERSION,
                    "2026-09-14T00:00:00+00:00",
                ),
            )

    def test_boundary_keys_are_stable_directional_and_length_delimited(self):
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 10)
        keys = self.keys(projection)
        first = workflow_boundary_key("relation", keys[10], keys[11])

        self.assertEqual(first, workflow_boundary_key("relation", keys[10], keys[11]))
        self.assertEqual(len(first), 64)
        self.assertNotEqual(first, workflow_boundary_key("relation", keys[11], keys[10]))
        self.assertNotEqual(first, workflow_boundary_key("lifecycle", keys[10]))

    def test_same_flow_overlays_branch_and_retains_base_reasons(self):
        self.add_session(10, 1, branch="main")
        self.add_session(11, 2, branch="feature/map")
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        self.assertEqual(projection.relations[0].kind, "branches-from")

        result = self.apply(projection, "same-flow", keys[10], keys[11])
        effective = result["projection"]

        self.assertEqual(result["assertion"]["before_meaning"], "relation:branches-from")
        self.assertEqual(effective.relations[0].kind, "continues")
        self.assertEqual(effective.relations[0].authority, "user-confirmed")
        self.assertEqual(effective.relations[0].reasons[0].kind, "user-assertion")
        self.assertEqual(effective.base_relations[0].kind, "branches-from")
        self.assertGreater(len(effective.base_relations[0].reasons), 0)
        self.assertEqual(effective.assertions[0]["resolution"], "applied")

    def test_split_supersedes_same_flow_and_requires_exact_active_version(self):
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        first = self.apply(projection, "same-flow", keys[10], keys[11])
        current = first["projection"]

        self.assert_error(
            "conflict",
            lambda: self.apply(current, "split-here", keys[10], keys[11]),
        )
        second = self.apply(
            current,
            "split-here",
            keys[10],
            keys[11],
            expected_active_assertion_id=first["assertion"]["id"],
        )

        self.assertEqual(second["projection"].relations[0].kind, "branches-from")
        self.assertEqual(second["assertion"]["boundary_version"], 2)
        self.assertEqual(
            second["assertion"]["supersedes_assertion_id"],
            first["assertion"]["id"],
        )
        self.assertEqual(len(second["projection"].assertions), 1)

    def test_merge_is_explicit_and_rejects_merge_before_source(self):
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        merged = self.apply(projection, "merge-into", keys[10], keys[11])
        self.assertEqual(merged["projection"].relations[0].kind, "merged-into")

        current = merged["projection"]
        self.assert_error(
            "merge-before-source",
            lambda: self.apply(current, "merge-into", keys[11], keys[10]),
        )

    def test_close_reopen_and_close_reason_correction_are_append_only(self):
        self.add_chain(3)
        projection = workflow_focus_projection(self.connection, 12)
        keys = self.keys(projection)
        closed = self.apply(
            projection,
            "close",
            keys[12],
            close_reason="completed",
            note="  Shipped locally.  ",
        )
        self.assertEqual(closed["assertion"]["note"], "Shipped locally.")
        self.assertEqual(
            self.keys(closed["projection"]), keys
        )
        closed_episode = next(
            view.episode
            for view in closed["projection"].episodes
            if view.episode.session_id == 12
        )
        self.assertEqual(closed_episode.lifecycle_state, "closed")
        self.assertEqual(closed_episode.closure_reason, "completed")

        corrected = self.apply(
            closed["projection"],
            "close",
            keys[12],
            close_reason="superseded",
            expected_active_assertion_id=closed["assertion"]["id"],
        )
        reopened = self.apply(
            corrected["projection"],
            "reopen",
            keys[12],
            expected_active_assertion_id=corrected["assertion"]["id"],
        )
        reopened_episode = next(
            view.episode
            for view in reopened["projection"].episodes
            if view.episode.session_id == 12
        )
        self.assertEqual(reopened_episode.lifecycle_state, "open")
        self.assertIsNone(reopened_episode.closure_reason)
        history = workflow_assertion_history(
            self.connection, str(reopened["assertion"]["boundary_key"])
        )
        self.assertEqual(history["observed_total"], 3)
        self.assertEqual(history["active_assertion_id"], reopened["assertion"]["id"])

    def test_close_requires_tip_and_reopen_requires_active_user_closure(self):
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 10)
        keys = self.keys(projection)
        self.assert_error(
            "not-tip",
            lambda: self.apply(
                projection, "close", keys[10], close_reason="abandoned"
            ),
        )
        self.assert_error(
            "requires-active-closure",
            lambda: self.apply(projection, "reopen", keys[11]),
        )

    def test_undo_restores_base_then_undoing_reversal_reapplies_assertion(self):
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        split = self.apply(projection, "split-here", keys[10], keys[11])
        self.assertEqual(split["projection"].relations[0].kind, "branches-from")

        undone = undo_workflow_assertion(
            self.connection,
            split["projection"],
            assertion_id=split["assertion"]["id"],
            expected_revision=split["projection"].assertion_revision,
            created_at="2026-09-14T04:00:00Z",
        )
        self.assertTrue(undone["assertion"]["is_undo"])
        self.assertEqual(undone["projection"].relations[0].kind, "continues")
        self.assertEqual(
            undone["projection"].relations[0].authority,
            projection.relations[0].authority,
        )

        redone = undo_workflow_assertion(
            self.connection,
            undone["projection"],
            assertion_id=undone["assertion"]["id"],
            expected_revision=undone["projection"].assertion_revision,
            created_at="2026-09-14T05:00:00Z",
        )
        self.assertEqual(redone["projection"].relations[0].kind, "branches-from")
        self.assertEqual(redone["projection"].relations[0].authority, "user-confirmed")
        history = workflow_assertion_history(
            self.connection, str(redone["assertion"]["boundary_key"])
        )
        self.assertEqual(history["observed_total"], 3)

    def test_only_current_assertion_can_be_undone(self):
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        first = self.apply(projection, "same-flow", keys[10], keys[11])
        second = self.apply(
            first["projection"],
            "split-here",
            keys[10],
            keys[11],
            expected_active_assertion_id=first["assertion"]["id"],
        )
        self.assert_error(
            "assertion-not-active",
            lambda: undo_workflow_assertion(
                self.connection,
                second["projection"],
                assertion_id=first["assertion"]["id"],
                expected_revision=second["projection"].assertion_revision,
            ),
        )

    def test_duplicate_stale_revision_and_missing_endpoints_write_nothing(self):
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        first = self.apply(projection, "same-flow", keys[10], keys[11])
        current = first["projection"]

        self.assert_error(
            "duplicate-active",
            lambda: self.apply(
                current,
                "same-flow",
                keys[10],
                keys[11],
                expected_active_assertion_id=first["assertion"]["id"],
            ),
        )
        self.assert_error(
            "conflict",
            lambda: apply_workflow_assertion(
                self.connection,
                current,
                assertion_kind="split-here",
                source_episode_key=keys[10],
                target_episode_key=keys[11],
                expected_active_assertion_id=first["assertion"]["id"],
                expected_revision=projection.assertion_revision,
            ),
        )
        missing = "session:" + "f" * 64
        self.assert_error(
            "missing-endpoint",
            lambda: self.apply(current, "same-flow", keys[10], missing),
        )

    def test_unrelated_ledger_change_invalidates_stale_projection_revision(self):
        self.add_chain(3)
        stale = workflow_focus_projection(self.connection, 11)
        keys = self.keys(stale)
        changed = self.apply(
            stale,
            "close",
            keys[12],
            close_reason="completed",
        )
        self.assertEqual(changed["projection"].episodes[-1].episode.lifecycle_state, "closed")

        self.assert_error(
            "conflict",
            lambda: self.apply(stale, "same-flow", keys[10], keys[11]),
        )

    def test_unique_chain_write_race_is_reported_as_conflict(self):
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        self.connection.execute(
            """
            CREATE TRIGGER simulate_workflow_assertion_race
            BEFORE INSERT ON workflow_assertions
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'UNIQUE constraint failed: workflow_assertions.boundary_key, workflow_assertions.boundary_version'
                );
            END
            """
        )
        self.assert_error(
            "conflict",
            lambda: self.apply(projection, "same-flow", keys[10], keys[11]),
        )

    def test_self_non_forward_and_cycle_are_rejected_atomically(self):
        self.add_chain(3)
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        self.assert_error(
            "self-relation",
            lambda: self.apply(projection, "same-flow", keys[10], keys[10]),
        )
        self.assert_error(
            "non-forward-time",
            lambda: self.apply(projection, "same-flow", keys[11], keys[10]),
        )

        reverse = WorkflowRelation(
            source_episode_key=keys[11],
            target_episode_key=keys[10],
            kind="continues",
            authority="deterministic-candidate",
            reasons=(
                WorkflowRelationReason(
                    kind="thread-membership", identity="synthetic-thread"
                ),
            ),
            source_observed_at="2026-09-14T02:00:00+00:00",
            target_observed_at="2026-09-14T01:00:00+00:00",
        )
        tampered = replace(
            projection,
            relations=(reverse,),
            base_relations=(),
            assertion_overlay_version=None,
            assertion_revision=None,
        )
        tampered = overlay_workflow_assertions(self.connection, tampered)
        self.assert_error(
            "cycle",
            lambda: self.apply(tampered, "same-flow", keys[10], keys[11]),
        )

    def test_source_deletion_retains_unresolved_assertion_and_reimport_resolves_key(self):
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        applied = self.apply(projection, "same-flow", keys[10], keys[11])
        assertion_id = applied["assertion"]["id"]

        self.connection.execute("DELETE FROM sessions WHERE id = 10")
        retained = self.connection.execute(
            "SELECT * FROM workflow_assertions WHERE id = ?", (assertion_id,)
        ).fetchone()
        self.assertIsNotNone(retained)
        self.assertIsNone(retained["source_session_id"])
        unresolved = workflow_focus_projection(self.connection, 11)
        self.assertEqual(unresolved.assertions[0]["resolution"], "unresolved")
        self.assertEqual(
            unresolved.assertions[0]["resolution_reason"], "missing-endpoint"
        )

        self.add_session(30, 1, external_id="native-10")
        restored = workflow_focus_projection(self.connection, 11)
        self.assertEqual(restored.assertions[0]["resolution"], "applied")
        self.assertEqual(restored.relations[0].authority, "user-confirmed")
        self.assertEqual(
            next(
                view.episode.episode_key
                for view in restored.episodes
                if view.episode.session_id == 30
            ),
            keys[10],
        )

    def test_projection_overlay_is_repeatable_read_only_and_versioned(self):
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        applied = self.apply(projection, "same-flow", keys[10], keys[11])
        self.connection.commit()
        statements = []
        before = self.connection.total_changes
        self.connection.set_trace_callback(statements.append)

        first = workflow_focus_projection(self.connection, 11)
        second = workflow_focus_projection(self.connection, 11)
        self.connection.set_trace_callback(None)

        self.assertEqual(first.assertion_overlay_version, WORKFLOW_ASSERTION_OVERLAY_VERSION)
        self.assertEqual(first.assertion_revision, second.assertion_revision)
        self.assertEqual(first.as_dict(), second.as_dict())
        self.assertEqual(self.connection.total_changes, before)
        self.assertFalse(
            any(
                statement.lstrip().upper().startswith(
                    ("INSERT", "UPDATE", "DELETE", "REPLACE")
                )
                for statement in statements
            )
        )
        self.assertEqual(
            applied["assertion"]["contract_version"], WORKFLOW_ASSERTION_VERSION
        )

    def test_note_bounds_vocabulary_and_insert_failure_preserve_history(self):
        self.assertEqual(
            WORKFLOW_ASSERTION_KINDS,
            {"same-flow", "split-here", "merge-into", "close", "reopen"},
        )
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        self.assert_error(
            "invalid-note",
            lambda: self.apply(
                projection,
                "same-flow",
                keys[10],
                keys[11],
                note="x" * 1001,
            ),
        )

        self.connection.execute(
            """
            CREATE TRIGGER reject_workflow_assertion
            BEFORE INSERT ON workflow_assertions
            BEGIN
                SELECT RAISE(ABORT, 'synthetic assertion failure');
            END
            """
        )
        before = self.connection.execute(
            "SELECT COUNT(*) FROM workflow_assertions"
        ).fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            self.apply(projection, "same-flow", keys[10], keys[11])
        after = self.connection.execute(
            "SELECT COUNT(*) FROM workflow_assertions"
        ).fetchone()[0]
        self.assertEqual(after, before)
        self.assertIsNotNone(
            self.connection.execute("SELECT id FROM sessions WHERE id = 10").fetchone()
        )

    def test_history_is_bounded_honest_and_idempotent_schema_preserves_rows(self):
        self.add_chain(2)
        projection = workflow_focus_projection(self.connection, 11)
        keys = self.keys(projection)
        current = self.apply(projection, "same-flow", keys[10], keys[11])
        for index in range(MAX_WORKFLOW_ASSERTION_HISTORY + 2):
            action = "split-here" if index % 2 == 0 else "same-flow"
            current = self.apply(
                current["projection"],
                action,
                keys[10],
                keys[11],
                expected_active_assertion_id=current["assertion"]["id"],
                created_at="2026-09-15T{:02d}:{:02d}:00Z".format(
                    index // 60, index % 60
                ),
            )
        boundary_key = current["assertion"]["boundary_key"]
        history = workflow_assertion_history(self.connection, boundary_key)
        self.assertEqual(history["observed_total"], 103)
        self.assertEqual(history["retained_total"], 100)
        self.assertTrue(history["partial"])
        self.assertEqual(history["active_assertion_id"], current["assertion"]["id"])

        before = [
            tuple(row)
            for row in self.connection.execute(
                "SELECT * FROM workflow_assertions ORDER BY id"
            )
        ]
        self.connection.executescript(SCHEMA)
        after = [
            tuple(row)
            for row in self.connection.execute(
                "SELECT * FROM workflow_assertions ORDER BY id"
            )
        ]
        self.assertEqual(after, before)
        self.assertEqual(self.connection.execute("PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main()
