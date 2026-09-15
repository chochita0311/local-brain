import hashlib
import json
import sqlite3
import unittest
from pathlib import Path

from localbrain.workflow_focus import (
    MAX_WORKFLOW_BRANCH_EPISODES,
    MAX_WORKFLOW_BRANCH_ROOTS,
    MAX_WORKFLOW_CANDIDATES,
    MAX_WORKFLOW_EPISODES,
    MAX_WORKFLOW_EVIDENCE_PER_FAMILY,
    WORKFLOW_FOCUS_VERSION,
    workflow_focus_projection,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "src/localbrain/schema.sql").read_text(encoding="utf-8")


class WorkflowFocusTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA)
        self.connection.executemany(
            """
            INSERT INTO sources(id, kind, provider_kind, name, root_path)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                (1, "codex", "codex", "Codex", "/synthetic/codex"),
                (2, "claude", "claude", "Claude", "/synthetic/claude"),
                (3, "context", "context", "Context", "/synthetic/context"),
            ),
        )
        self.connection.executemany(
            """
            INSERT INTO workspaces(
                id, canonical_path, display_name, git_root, exists_now
            ) VALUES (?, ?, ?, ?, 1)
            """,
            (
                (1, "/private/work-one", "Work One", "/private/repo-secret"),
                (2, "/private/work-two", "Work Two", "/private/repo-secret"),
                (3, "/private/unrelated", "Unrelated", "/private/other"),
            ),
        )

    def tearDown(self):
        self.connection.close()

    def add_session(
        self,
        session_id,
        *,
        source_id=1,
        workspace_id=1,
        external_id=None,
        title=None,
        observed_at=None,
        branch="main",
        session_class="work",
        session_role="primary",
        parent_session_id=None,
        event_count=1,
        index_policy="full",
        source_path=None,
    ):
        external_id = external_id or "native-{}".format(session_id)
        observed_at = observed_at or "2026-09-14T{:02d}:00:00Z".format(
            session_id % 24
        )
        self.connection.execute(
            """
            INSERT INTO sessions(
                id, source_id, workspace_id, external_id, source_path, cwd_raw,
                git_branch, title, started_at, last_event_at, event_count,
                session_class, session_role, parent_session_id, index_policy
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                source_id,
                workspace_id,
                external_id,
                source_path or "/private/source-{}.jsonl".format(session_id),
                "/private/work-one",
                branch,
                title or "Session {}".format(session_id),
                observed_at,
                observed_at,
                event_count,
                session_class,
                session_role,
                parent_session_id,
                index_policy,
            ),
        )

    def add_workstream(self, workstream_id=1, name="Synthetic Workflow"):
        self.connection.execute(
            "INSERT INTO workstreams(id, name) VALUES (?, ?)",
            (workstream_id, name),
        )

    def add_thread(self, thread_id=1, workstream_id=1, title="Synthetic Thread"):
        self.connection.execute(
            "INSERT INTO threads(id, workstream_id, title) VALUES (?, ?, ?)",
            (thread_id, workstream_id, title),
        )

    def link_session_to_thread(self, session_id, thread_id=1, linked_by="user"):
        self.connection.execute(
            """
            INSERT INTO thread_links(
                thread_id, entity_type, entity_id, linked_by
            ) VALUES (?, 'session', ?, ?)
            """,
            (thread_id, str(session_id), linked_by),
        )

    def link_session_to_workstream(
        self, session_id, workstream_id=1, linked_by="user"
    ):
        self.connection.execute(
            """
            INSERT INTO workstream_links(
                workstream_id, entity_type, entity_id, linked_by
            ) VALUES (?, 'session', ?, ?)
            """,
            (workstream_id, str(session_id), linked_by),
        )

    def add_reference(
        self,
        session_id,
        target_key="url:shared",
        *,
        line=1,
        observed_at=None,
        target_kind="url",
        context_document_id=None,
        identity="https://example.test/shared",
    ):
        observed_at = observed_at or "2026-09-14T01:30:00Z"
        normalized_url = (
            None
            if target_kind == "context_document"
            else "https://example.test/shared"
        )
        evidence_key = hashlib.sha256(
            "{}:{}:{}:{}".format(
                session_id, target_key, line, target_kind
            ).encode("utf-8")
        ).hexdigest()
        self.connection.execute(
            """
            INSERT INTO session_reference_evidence(
                session_id, source_path, source_event_id, source_line,
                evidence_ordinal, target_kind, target_key,
                context_document_id, evidence_kind, observed_identity,
                normalized_url, observed_at, extractor_version, evidence_key,
                first_observed_at, last_observed_at
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, 'user_mention', ?, ?, ?,
                      'synthetic-v1', ?, ?, ?)
            """,
            (
                session_id,
                "/private/source-{}.jsonl".format(session_id),
                "event-{}-{}".format(session_id, line),
                line,
                target_kind,
                target_key,
                context_document_id,
                identity,
                normalized_url,
                observed_at,
                evidence_key,
                observed_at,
                observed_at,
            ),
        )

    def episode_by_session(self, projection):
        return {
            item.episode.session_id: item for item in projection.episodes
        }

    def test_missing_ineligible_and_invalid_selection_are_typed(self):
        self.add_session(10, session_class="maintenance")
        self.add_session(11, event_count=0)
        self.add_session(
            12, session_role="subsession", parent_session_id=11
        )

        self.assertEqual(
            workflow_focus_projection(self.connection, 99).status, "missing"
        )
        for session_id in (10, 11, 12):
            with self.subTest(session_id=session_id):
                result = workflow_focus_projection(self.connection, session_id)
                self.assertEqual(result.status, "ineligible")
                self.assertFalse(result.episodes)
        for invalid in (0, -1, True, "10"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    workflow_focus_projection(self.connection, invalid)

    def test_unconnected_selected_episode_is_always_retained(self):
        self.add_session(20, source_id=2, external_id="claude-anchor")

        result = workflow_focus_projection(self.connection, 20)

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.projection_version, WORKFLOW_FOCUS_VERSION)
        self.assertEqual(result.episode_retained_total, 1)
        self.assertEqual(result.episode_observed_total, 1)
        self.assertEqual(result.episodes[0].episode.session_id, 20)
        self.assertFalse(result.relations)

    def test_episode_query_uses_chronological_first_event_across_offsets(self):
        self.add_session(20, observed_at="2026-09-14T06:00:00Z", event_count=2)
        self.connection.executemany(
            """
            INSERT INTO activity_events(
                id, session_id, sequence, occurred_at, event_type, source_line
            ) VALUES (?, 20, ?, ?, 'message', ?)
            """,
            (
                ("event-later", 1, "2026-09-14T00:15:00-05:00", 1),
                ("event-earlier", 2, "2026-09-14T04:00:00Z", 2),
            ),
        )

        result = workflow_focus_projection(self.connection, 20)

        self.assertEqual(
            result.episodes[0].episode.observed_start_at,
            "2026-09-14T04:00:00+00:00",
        )

    def test_workspace_root_branch_and_time_alone_do_not_create_a_candidate(self):
        self.add_session(20, observed_at="2026-09-14T01:00:00Z")
        self.add_session(21, observed_at="2026-09-14T02:00:00Z")

        result = workflow_focus_projection(self.connection, 20)

        self.assertEqual(result.candidate_observed_total, 0)
        self.assertEqual(result.episode_retained_total, 1)
        self.assertFalse(result.relations)

    def test_shared_user_thread_emits_only_adjacent_continuations(self):
        self.add_workstream()
        self.add_thread()
        for session_id, hour, source_id in ((20, 1, 1), (21, 2, 2), (22, 3, 1)):
            self.add_session(
                session_id,
                source_id=source_id,
                observed_at="2026-09-14T0{}:00:00Z".format(hour),
            )
            self.link_session_to_thread(session_id)

        result = workflow_focus_projection(self.connection, 21)

        self.assertEqual(result.candidate_observed_total, 2)
        self.assertEqual(
            [relation.kind for relation in result.relations],
            ["continues", "continues"],
        )
        self.assertEqual(
            [
                (relation.source_observed_at, relation.target_observed_at)
                for relation in result.relations
            ],
            [
                (
                    "2026-09-14T01:00:00+00:00",
                    "2026-09-14T02:00:00+00:00",
                ),
                (
                    "2026-09-14T02:00:00+00:00",
                    "2026-09-14T03:00:00+00:00",
                ),
            ],
        )
        self.assertTrue(
            all(
                relation.reasons[0].kind == "thread-membership"
                for relation in result.relations
            )
        )

    def test_generated_membership_does_not_establish_direction(self):
        self.add_workstream()
        self.add_thread()
        self.add_session(20)
        self.add_session(21, observed_at="2026-09-14T02:00:00Z")
        self.link_session_to_thread(20, linked_by="suggestion")
        self.link_session_to_thread(21, linked_by="suggestion")

        result = workflow_focus_projection(self.connection, 20)

        self.assertEqual(result.candidate_observed_total, 0)
        self.assertFalse(result.relations)

    def test_shared_reference_and_workstream_emit_continuation(self):
        self.add_workstream()
        for session_id, hour, workspace_id in ((20, 1, 1), (21, 2, 3)):
            self.add_session(
                session_id,
                workspace_id=workspace_id,
                observed_at="2026-09-14T0{}:00:00Z".format(hour),
            )
            self.link_session_to_workstream(session_id)
            self.add_reference(session_id)

        result = workflow_focus_projection(self.connection, 20)

        self.assertEqual(len(result.relations), 1)
        relation = result.relations[0]
        self.assertEqual(relation.kind, "continues")
        self.assertEqual(
            {reason.kind for reason in relation.reasons},
            {"shared-reference", "workstream-membership"},
        )

    def test_different_branches_emit_nearest_earlier_branch_candidate(self):
        for session_id, hour, branch in (
            (20, 1, "main"),
            (21, 2, "main"),
            (22, 3, "feature/map"),
        ):
            self.add_session(
                session_id,
                observed_at="2026-09-14T0{}:00:00Z".format(hour),
                branch=branch,
            )
            self.add_reference(session_id)

        result = workflow_focus_projection(self.connection, 22)
        sessions = self.episode_by_session(result)
        relation = next(
            item for item in result.relations if item.kind == "branches-from"
        )

        self.assertEqual(sessions[21].episode.episode_key, relation.source_episode_key)
        self.assertEqual(sessions[22].episode.episode_key, relation.target_episode_key)
        self.assertEqual(relation.authority, "deterministic-candidate")
        self.assertIn("shared-reference", {item.kind for item in relation.reasons})
        self.assertIn("same-git-root", {item.kind for item in relation.reasons})

    def test_return_to_main_never_infers_merged_into(self):
        for session_id, hour, branch in (
            (20, 1, "main"),
            (21, 2, "feature/map"),
            (22, 3, "main"),
        ):
            self.add_session(
                session_id,
                observed_at="2026-09-14T0{}:00:00Z".format(hour),
                branch=branch,
            )
            self.add_reference(session_id)

        result = workflow_focus_projection(self.connection, 21)

        self.assertNotIn("merged-into", {item.kind for item in result.relations})

    def test_candidate_episode_and_branch_bounds_report_honest_totals(self):
        self.add_workstream()
        self.add_thread()
        self.add_session(1000, observed_at="2026-09-01T00:00:00Z")
        self.link_session_to_thread(1000)
        for offset in range(MAX_WORKFLOW_CANDIDATES + 5):
            session_id = 1100 + offset
            day = 1 + (offset // 20)
            hour = 1 + (offset % 20)
            self.add_session(
                session_id,
                observed_at="2026-09-{:02d}T{:02d}:00:00Z".format(day, hour),
            )
            self.link_session_to_thread(session_id)

        result = workflow_focus_projection(self.connection, 1000)

        self.assertEqual(
            result.candidate_observed_total, MAX_WORKFLOW_CANDIDATES + 5
        )
        self.assertEqual(result.candidate_retained_total, MAX_WORKFLOW_CANDIDATES)
        self.assertLessEqual(result.episode_retained_total, MAX_WORKFLOW_EPISODES)
        self.assertGreater(result.episode_observed_total, result.episode_retained_total)

    def test_side_branch_roots_and_branch_episode_counts_are_bounded(self):
        self.add_session(20, observed_at="2026-09-14T00:00:00Z", branch="main")
        self.add_reference(20)
        next_id = 30
        for branch_number in range(MAX_WORKFLOW_BRANCH_ROOTS + 2):
            main_hour = 1 + (branch_number * 2)
            self.add_session(
                next_id,
                observed_at="2026-09-14T{:02d}:00:00Z".format(main_hour),
                branch="main",
            )
            self.add_reference(next_id)
            next_id += 1
            for position in range(MAX_WORKFLOW_BRANCH_EPISODES + 2):
                self.add_session(
                    next_id,
                    observed_at="2026-09-14T{:02d}:{:02d}:00Z".format(
                        main_hour, 5 * (position + 1)
                    ),
                    branch="feature/{}".format(branch_number),
                )
                self.add_reference(next_id)
                next_id += 1

        result = workflow_focus_projection(self.connection, 20)
        branch_counts = {}
        for view in result.episodes:
            branch = view.episode.git_branch
            if branch and branch.startswith("feature/"):
                branch_counts[branch] = branch_counts.get(branch, 0) + 1

        self.assertGreater(result.branch_root_observed_total, MAX_WORKFLOW_BRANCH_ROOTS)
        self.assertEqual(result.branch_root_retained_total, MAX_WORKFLOW_BRANCH_ROOTS)
        self.assertLessEqual(len(branch_counts), MAX_WORKFLOW_BRANCH_ROOTS)
        self.assertTrue(
            all(count <= MAX_WORKFLOW_BRANCH_EPISODES for count in branch_counts.values())
        )

    def test_evidence_is_grouped_bounded_and_never_becomes_peer_episodes(self):
        self.add_session(20, title="Anchor")
        self.connection.execute(
            """
            INSERT INTO context_roots(
                id, path, label, readable, status, enabled
            ) VALUES (1, '/synthetic/context', 'Context', 1, 'ready', 1)
            """
        )
        for index in range(MAX_WORKFLOW_EVIDENCE_PER_FAMILY + 2):
            document_id = 100 + index
            self.connection.execute(
                """
                INSERT INTO context_documents(
                    id, source_id, context_root_id, workspace_id, path,
                    relative_path, title, body, size_bytes, mtime_ns,
                    content_hash
                ) VALUES (?, 3, 1, 1, ?, ?, ?, 'private body', 12, ?, ?)
                """,
                (
                    document_id,
                    "/synthetic/context/doc-{}.md".format(index),
                    "doc-{}.md".format(index),
                    "Document {}".format(index),
                    index + 1,
                    "hash-{}".format(index),
                ),
            )
            self.add_reference(
                20,
                "document:{}".format(document_id),
                line=index + 1,
                target_kind="context_document",
                context_document_id=document_id,
                identity="Document {}".format(index),
            )
        self.add_workstream()
        self.add_thread()
        self.link_session_to_thread(20)
        for child_index in range(MAX_WORKFLOW_EVIDENCE_PER_FAMILY + 2):
            self.add_session(
                200 + child_index,
                session_role="subsession",
                parent_session_id=20,
                title="Child {}".format(child_index),
            )
        self.connection.executescript(
            """
            INSERT INTO atlassian_sites(
                id, normalized_domain, canonical_base_url
            ) VALUES (1, 'jira.example.test', 'https://jira.example.test');
            INSERT INTO atlassian_structure_references(
                id, site_id, service, reference_kind, reference_identity
            ) VALUES (1, 1, 'jira', 'jira_project', 'SYN');
            INSERT INTO session_reference_scans(
                session_id, source_fingerprint, extractor_version, status,
                observed_target_count, retained_target_count, scanned_at
            ) VALUES (
                20,
                'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                'synthetic-v1', 'partial', 101, 100,
                '2026-09-14T05:00:00Z'
            );
            INSERT INTO atlassian_structure_reference_evidence(
                reference_id, session_id, source_path, source_channel,
                source_event_id, source_line, url_ordinal, safe_locator_url,
                observed_at, extractor_version, evidence_key,
                first_observed_at, last_observed_at
            ) VALUES (
                1, 20, '/private/source-20.jsonl', 'visible_text',
                'structure-event', 99, 1,
                'https://jira.example.test/projects/SYN',
                '2026-09-14T04:00:00Z', 'synthetic-v1',
                'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
                '2026-09-14T04:00:00Z', '2026-09-14T04:00:00Z'
            );
            """
        )

        result = workflow_focus_projection(self.connection, 20)
        view = result.episodes[0]
        groups = {group.source_family: group for group in view.evidence_groups}

        self.assertEqual(len(result.episodes), 1)
        self.assertEqual(len(groups["local-context"].items), 5)
        self.assertEqual(groups["local-context"].retained_total, 7)
        self.assertTrue(groups["local-context"].partial)
        self.assertEqual(
            groups["local-context"].items[0].observed_at,
            "2026-09-14T01:30:00+00:00",
        )
        self.assertEqual(len(groups["session"].items), 5)
        self.assertEqual(groups["session"].retained_total, 7)
        self.assertTrue(groups["session"].partial)
        self.assertEqual(groups["atlassian"].items[0].evidence_kind, "structure-reference")
        self.assertIn("organization", groups)
        self.assertTrue(view.evidence_partial)

    def test_stale_reference_state_is_retained_without_refresh(self):
        self.add_session(20)
        self.connection.execute(
            """
            INSERT INTO context_roots(id, path, label)
            VALUES (1, '/synthetic/context', 'Context')
            """
        )
        self.connection.execute(
            """
            INSERT INTO context_documents(
                id, source_id, context_root_id, workspace_id, path,
                relative_path, title, body, size_bytes, mtime_ns, content_hash
            ) VALUES (
                100, 3, 1, 1, '/synthetic/context/stale.md', 'stale.md',
                'Stale document', 'body', 4, 1, 'stale-hash'
            )
            """
        )
        self.add_reference(
            20,
            "document:100",
            target_kind="context_document",
            context_document_id=100,
            identity="Stale document",
        )
        self.connection.execute(
            """
            INSERT INTO session_reference_scans(
                session_id, source_fingerprint, extractor_version, status,
                observed_target_count, retained_target_count, error_code,
                scanned_at
            ) VALUES (?, ?, 'synthetic-v1', 'error', 1, 1,
                      'synthetic-error', '2026-09-14T05:00:00Z')
            """,
            (20, "c" * 64),
        )

        result = workflow_focus_projection(self.connection, 20)
        group = next(
            item
            for item in result.episodes[0].evidence_groups
            if item.source_family == "local-context"
        )

        self.assertTrue(group.stale)
        self.assertEqual(group.items[0].availability, "stale")

    def test_projection_is_repeatable_json_compatible_and_executes_zero_writes(self):
        self.add_session(
            20,
            external_id="native-secret-id",
            source_path="/private/source-secret.jsonl",
            observed_at="2026-09-14T01:00:00Z",
        )
        self.add_session(21, observed_at="2026-09-14T02:00:00Z")
        self.add_reference(20)
        self.add_reference(21)
        before = self.connection.total_changes
        statements = []
        self.connection.set_trace_callback(statements.append)

        first = workflow_focus_projection(self.connection, 20)
        second = workflow_focus_projection(self.connection, 20)
        self.connection.set_trace_callback(None)
        first_json = json.dumps(first.as_dict(), sort_keys=True)
        second_json = json.dumps(second.as_dict(), sort_keys=True)

        self.assertEqual(first_json, second_json)
        self.assertEqual(self.connection.total_changes, before)
        forbidden = ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER")
        self.assertFalse(
            [
                statement
                for statement in statements
                if statement.lstrip().upper().startswith(forbidden)
            ]
        )
        self.assertNotIn("native-secret-id", first_json)
        self.assertNotIn("/private/source-secret.jsonl", first_json)
        self.assertNotIn("/private/repo-secret", first_json)


if __name__ == "__main__":
    unittest.main()
