import asyncio
import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, patch

from localbrain.external_access import (
    record_capability_observation,
    register_source_instance,
)
from localbrain.config import settings
from localbrain.db import init_db
from localbrain.external_sync import (
    MANIFEST_SCHEMA,
    MODEL_RESULT_SCHEMA_VERSION,
    RESULT_SCHEMA_VERSION,
    ExternalSyncError,
    assemble_external_sync_result,
    build_external_sync_manifest,
    collect_external_sync_evidence,
    derive_run_status,
    load_external_sync_manifest,
    prepare_external_sync_run,
    validate_provider_result,
)
from localbrain.runner import (
    _execute_run,
    cancel_run,
    external_runner_command_args,
    reconcile_interrupted_runs,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class _FakeStream:
    def __init__(self, lines):
        self.lines = [
            line if isinstance(line, bytes) else line.encode("utf-8")
            for line in lines
        ]

    async def readline(self):
        if not self.lines:
            return b""
        return self.lines.pop(0)


class _FakeStdin:
    def __init__(self):
        self.value = b""

    def write(self, value):
        self.value += value

    async def drain(self):
        return None

    def close(self):
        return None


class _FakeProcess:
    def __init__(self, stdout_lines, return_code=0):
        self.pid = 43210
        self.stdin = _FakeStdin()
        self.stdout = _FakeStream(stdout_lines)
        self.stderr = _FakeStream([])
        self._return_code = return_code
        self.returncode = None

    async def wait(self):
        self.returncode = self._return_code
        return self.returncode

    def terminate(self):
        self.returncode = -15


class ExternalSyncTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.db_path = Path(handle.name)
        self.run_root = Path(tempfile.mkdtemp())
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.connection.execute(
            "INSERT INTO workstreams(name) VALUES ('Synthetic workstream')"
        )
        self.instance = register_source_instance(
            self.connection,
            instance_key="synthetic-jira-primary",
            provider_kind="mcp_gateway",
            service="jira",
            display_name="Synthetic Jira",
            config_ref="synthetic-jira",
        )
        record_capability_observation(
            self.connection,
            self.instance["id"],
            availability="available",
            operations=("jira.search_metadata", "jira.read_description"),
            schema_fingerprint="a" * 64,
        )
        self.connection.commit()

    def tearDown(self):
        self.connection.close()
        for path in sorted(self.run_root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            else:
                path.rmdir()
        self.run_root.rmdir()
        self.db_path.unlink(missing_ok=True)

    def target(self, suffix="1", *, coverage=None):
        return {
            "target_id": "target-{}".format(suffix),
            "locator": {
                "kind": "url",
                "value": "https://synthetic.invalid/browse/SYN-{}".format(suffix),
            },
            "coverage": coverage or ["metadata"],
            "field_allowlist": ["key", "summary"],
            "known": {
                "remote_version": "1",
                "remote_updated_at": "2026-07-23T00:00:00Z",
                "content_hash": None,
            },
            "requests": [
                {
                    "request_id": "request-{}".format(suffix),
                    "logical_operation": "jira.search_metadata",
                    "arguments": {
                        "jql": 'key = "SYN-{}"'.format(suffix),
                        "fields": ["key", "summary"],
                        "limit": 1,
                    },
                }
            ],
        }

    @contextmanager
    def transaction_context(self):
        try:
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def runner_patches(self):
        return (
            patch("localbrain.runner.connect", return_value=self.connection),
            patch(
                "localbrain.runner.transaction",
                side_effect=lambda: self.transaction_context(),
            ),
        )

    def test_preparation_atomically_creates_query_projection(self):
        run_id = prepare_external_sync_run(
            self.connection,
            runner="claude",
            source_instance_id=self.instance["id"],
            source_kind="atlassian",
            scope_kind="workstream",
            targets=[self.target()],
            workstream_id=1,
            call_budget=2,
            run_root=self.run_root,
        )
        run = self.connection.execute(
            "SELECT * FROM maintenance_runs WHERE id = ?", (run_id,)
        ).fetchone()
        envelope = self.connection.execute(
            "SELECT * FROM external_sync_runs WHERE maintenance_run_id = ?",
            (run_id,),
        ).fetchone()
        manifest = json.loads(
            Path(run["manifest_path"]).read_text(encoding="utf-8")
        )

        self.assertEqual(run["task_type"], "external_source_sync")
        self.assertEqual(run["runner"], "claude")
        self.assertEqual(run["status"], "queued")
        self.assertEqual(manifest["schema"], MANIFEST_SCHEMA)
        self.assertEqual(envelope["source_instance_id"], self.instance["id"])
        self.assertEqual(envelope["source_kind"], "atlassian")
        self.assertEqual(envelope["service"], "jira")
        self.assertEqual(envelope["requested_scope_kind"], "workstream")
        self.assertEqual(envelope["selected_target_count"], 1)
        self.assertEqual(envelope["manifest_schema_version"], MANIFEST_SCHEMA)
        self.assertNotIn("targets", dict(envelope))
        self.assertNotIn("arguments", dict(envelope))

        self.connection.execute(
            """
            INSERT INTO maintenance_runs(id, task_type, runner)
            VALUES ('lb-ordinary', 'organize_resources', 'claude')
            """
        )
        self.assertIsNone(
            self.connection.execute(
                """
                SELECT * FROM external_sync_runs
                WHERE maintenance_run_id = 'lb-ordinary'
                """
            ).fetchone()
        )

    def test_compatible_startup_adds_extension_without_rewriting_runs(self):
        self.connection.execute(
            """
            INSERT INTO maintenance_runs(id, task_type, runner, status, summary)
            VALUES (
                'lb-existing', 'organize_resources', 'claude',
                'completed', 'retained'
            )
            """
        )
        self.connection.execute("DROP TABLE external_sync_runs")
        self.connection.commit()
        self.connection.close()
        runtime_settings = replace(
            settings,
            data_dir=self.db_path.parent,
            database_path=self.db_path,
        )
        with patch("localbrain.db.settings", runtime_settings):
            init_db()
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

        retained = self.connection.execute(
            "SELECT status, summary FROM maintenance_runs WHERE id = 'lb-existing'"
        ).fetchone()
        self.assertEqual(tuple(retained), ("completed", "retained"))
        foreign_keys = {
            (row["from"], row["table"], row["on_delete"])
            for row in self.connection.execute(
                "PRAGMA foreign_key_list(external_sync_runs)"
            )
        }
        self.assertEqual(
            foreign_keys,
            {
                ("maintenance_run_id", "maintenance_runs", "CASCADE"),
                (
                    "source_instance_id",
                    "external_source_instances",
                    "SET NULL",
                ),
            },
        )

    def test_source_deletion_retains_envelope_and_run_history(self):
        run_id = prepare_external_sync_run(
            self.connection,
            runner="codex",
            source_instance_id=self.instance["id"],
            source_kind="atlassian",
            scope_kind="item",
            targets=[self.target()],
            run_root=self.run_root,
        )
        self.connection.execute(
            "DELETE FROM external_source_instances WHERE id = ?",
            (self.instance["id"],),
        )
        envelope = self.connection.execute(
            "SELECT * FROM external_sync_runs WHERE maintenance_run_id = ?",
            (run_id,),
        ).fetchone()
        self.assertIsNotNone(envelope)
        self.assertIsNone(envelope["source_instance_id"])
        self.assertIsNotNone(
            self.connection.execute(
                "SELECT * FROM maintenance_runs WHERE id = ?", (run_id,)
            ).fetchone()
        )

    def test_invalid_parent_relation_rolls_back_rows_and_artifacts(self):
        with self.assertRaises(sqlite3.IntegrityError):
            prepare_external_sync_run(
                self.connection,
                runner="claude",
                source_instance_id=self.instance["id"],
                source_kind="atlassian",
                scope_kind="workstream",
                targets=[self.target()],
                workstream_id=999,
                run_root=self.run_root,
            )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM maintenance_runs"
            ).fetchone()[0],
            0,
        )
        self.assertEqual(list(self.run_root.iterdir()), [])

    def test_manifest_requires_current_policy_and_bounded_authorized_reads(self):
        overbroad_target = self.target()
        overbroad_target["field_allowlist"] = ["summary"]
        with self.assertRaises(ExternalSyncError) as overbroad:
            build_external_sync_manifest(
                self.connection,
                run_id="lb-synthetic",
                runner="claude",
                source_instance_id=self.instance["id"],
                source_kind="atlassian",
                scope_kind="item",
                targets=[overbroad_target],
                call_budget=1,
            )
        self.assertEqual(overbroad.exception.code, "invalid-manifest")

        with self.assertRaises(ExternalSyncError) as denied:
            build_external_sync_manifest(
                self.connection,
                run_id="lb-synthetic",
                runner="claude",
                source_instance_id=self.instance["id"],
                source_kind="atlassian",
                scope_kind="item",
                targets=[
                    {
                        **self.target(),
                        "requests": [
                            {
                                "request_id": "write-1",
                                "logical_operation": "jira.create_issue",
                                "arguments": {"summary": "No"},
                            }
                        ],
                    }
                ],
                call_budget=1,
            )
        self.assertEqual(denied.exception.code, "operation-not-allowed")

        self.connection.execute(
            """
            UPDATE external_source_capabilities
            SET invalidated_at = '2026-07-23T01:00:00Z'
            WHERE source_instance_id = ?
            """,
            (self.instance["id"],),
        )
        with self.assertRaises(ExternalSyncError) as stale:
            build_external_sync_manifest(
                self.connection,
                run_id="lb-synthetic",
                runner="claude",
                source_instance_id=self.instance["id"],
                source_kind="atlassian",
                scope_kind="item",
                targets=[self.target()],
                call_budget=1,
            )
        self.assertEqual(stale.exception.code, "capability-not-current")

    def test_envelope_manifest_mismatch_fails_closed(self):
        run_id = prepare_external_sync_run(
            self.connection,
            runner="claude",
            source_instance_id=self.instance["id"],
            source_kind="atlassian",
            scope_kind="item",
            targets=[self.target()],
            run_root=self.run_root,
        )
        self.connection.execute(
            """
            UPDATE external_sync_runs SET selected_target_count = 9
            WHERE maintenance_run_id = ?
            """,
            (run_id,),
        )
        run = self.connection.execute(
            "SELECT * FROM maintenance_runs WHERE id = ?", (run_id,)
        ).fetchone()
        with self.assertRaises(ExternalSyncError) as mismatch:
            load_external_sync_manifest(self.connection, run)
        self.assertEqual(
            mismatch.exception.code, "external-sync-envelope-mismatch"
        )

    def test_provider_facts_are_allowlisted_and_content_hash_is_host_computed(self):
        request = {
            "request_id": "content-1",
            "logical_operation": "jira.read_description",
            "arguments": {"issue_key": "SYN-1"},
        }
        result = validate_provider_result(
            {
                "outcome": "changed",
                "identity": {"remote_id": "10001"},
                "metadata": {"key": "SYN-1", "summary": "Synthetic"},
                "content": {"description": "Local-only synthetic body"},
                "remote_version": "2",
                "remote_updated_at": "2026-07-23T02:00:00Z",
            },
            request=request,
            coverage=["metadata", "content"],
            field_allowlist=["key", "summary"],
        )
        expected_hash = hashlib.sha256(
            b'{"description":"Local-only synthetic body"}'
        ).hexdigest()
        self.assertEqual(result["content_hash"], expected_hash)

        with self.assertRaises(ExternalSyncError) as extra:
            validate_provider_result(
                {
                    "outcome": "resolved",
                    "metadata": {"comment": "must not pass"},
                },
                request=request,
                coverage=["metadata"],
                field_allowlist=["key", "summary"],
            )
        self.assertEqual(extra.exception.code, "invalid-provider-result")

        with self.assertRaises(ExternalSyncError) as request_wider_than_target:
            validate_provider_result(
                {
                    "outcome": "resolved",
                    "metadata": {"key": "SYN-1"},
                },
                request=request,
                coverage=["metadata"],
                field_allowlist=["summary"],
            )
        self.assertEqual(
            request_wider_than_target.exception.code,
            "invalid-provider-result",
        )

        with self.assertRaises(ExternalSyncError) as uncovered:
            validate_provider_result(
                {
                    "outcome": "resolved",
                    "metadata": {"summary": "must not pass"},
                },
                request=request,
                coverage=["content"],
                field_allowlist=[],
            )
        self.assertEqual(
            uncovered.exception.code,
            "invalid-provider-result",
        )

        safe_error = validate_provider_result(
            {
                "outcome": "error",
                "error": {
                    "code": "provider-error",
                    "message": "raw provider detail must not persist",
                },
            },
            request=request,
            coverage=["metadata", "content"],
            field_allowlist=["key", "summary"],
        )
        self.assertEqual(
            safe_error["error"]["message"],
            "Approved external read failed.",
        )

    def test_evidence_and_model_summary_have_separate_authority(self):
        manifest, dispatches = build_external_sync_manifest(
            self.connection,
            run_id="lb-synthetic",
            runner="claude",
            source_instance_id=self.instance["id"],
            source_kind="atlassian",
            scope_kind="item",
            targets=[self.target()],
            call_budget=1,
        )

        async def executor(_dispatch):
            return {
                "outcome": "resolved",
                "identity": {"remote_id": "10001"},
                "metadata": {"key": "SYN-1", "summary": "Source fact"},
            }

        targets, calls = asyncio.run(
            collect_external_sync_evidence(manifest, dispatches, executor)
        )
        final = assemble_external_sync_result(
            manifest,
            targets,
            {
                "schema": MODEL_RESULT_SCHEMA_VERSION,
                "run_id": "lb-synthetic",
                "summary": "Model presentation only",
            },
        )
        self.assertEqual(final["schema"], RESULT_SCHEMA_VERSION)
        self.assertEqual(
            final["targets"][0]["requests"][0]["metadata"]["summary"],
            "Source fact",
        )
        self.assertEqual(final["summary"], "Model presentation only")
        self.assertNotIn("arguments", calls[0])
        self.assertEqual(calls[0]["tool_name"], "mcp_gateway.gateway_dispatch")

        with self.assertRaises(ExternalSyncError):
            assemble_external_sync_result(
                manifest,
                targets,
                {
                    "schema": MODEL_RESULT_SCHEMA_VERSION,
                    "run_id": "lb-synthetic",
                    "summary": "Attempt",
                    "metadata": {"summary": "invented"},
                },
            )

    def test_terminal_status_derivation_distinguishes_partial_and_failed(self):
        self.assertEqual(
            derive_run_status([{"outcome": "resolved"}, {"outcome": "unchanged"}]),
            "completed",
        )
        self.assertEqual(
            derive_run_status([{"outcome": "resolved"}, {"outcome": "error"}]),
            "partial",
        )
        self.assertEqual(
            derive_run_status([{"outcome": "unavailable"}]),
            "failed",
        )

    def test_runner_commands_remove_broad_external_tools_for_both_runners(self):
        claude = external_runner_command_args(
            "claude", "/synthetic/claude", self.run_root
        )
        self.assertIn("--strict-mcp-config", claude)
        self.assertEqual(claude[claude.index("--tools") + 1], "")
        self.assertNotIn("--no-session-persistence", claude)

        codex = external_runner_command_args(
            "codex", "/synthetic/codex", self.run_root
        )
        self.assertEqual(codex[:2], ["/synthetic/codex", "exec"])
        self.assertIn("--ignore-user-config", codex)
        self.assertIn('default_permissions="external-sync"', codex)
        self.assertIn(
            "permissions.external-sync.network.enabled=false",
            codex,
        )
        self.assertIn('web_search="disabled"', codex)
        self.assertNotIn("--ephemeral", codex)

    def test_synthetic_runtime_completes_through_claude_and_codex(self):
        for runner_kind in ("claude", "codex"):
            with self.subTest(runner=runner_kind):
                run_id = prepare_external_sync_run(
                    self.connection,
                    runner=runner_kind,
                    source_instance_id=self.instance["id"],
                    source_kind="atlassian",
                    scope_kind="item",
                    targets=[self.target(runner_kind)],
                    run_root=self.run_root,
                )
                model_result = {
                    "schema": MODEL_RESULT_SCHEMA_VERSION,
                    "run_id": run_id,
                    "summary": "{} synthetic summary".format(runner_kind),
                }

                async def executor(_dispatch):
                    return {
                        "outcome": "unchanged",
                        "identity": {"remote_id": "10001"},
                        "metadata": {
                            "key": "SYN-1",
                            "summary": "Synthetic",
                        },
                        "remote_version": "1",
                    }

                async def create_process(*arguments, **_kwargs):
                    if runner_kind == "codex":
                        output_index = arguments.index("--output-last-message") + 1
                        Path(arguments[output_index]).write_text(
                            json.dumps(model_result),
                            encoding="utf-8",
                        )
                        lines = [
                            json.dumps({"type": "item.completed"}) + "\n"
                        ]
                    else:
                        lines = [
                            json.dumps(
                                {
                                    "type": "result",
                                    "structured_output": model_result,
                                }
                            )
                            + "\n"
                        ]
                    return _FakeProcess(lines)

                connect_patch, transaction_patch = self.runner_patches()
                with connect_patch, transaction_patch, patch(
                    "localbrain.runner.runner_executable",
                    return_value="/synthetic/runner",
                ), patch(
                    "localbrain.runner.asyncio.create_subprocess_exec",
                    side_effect=create_process,
                ), patch(
                    "localbrain.runner._sync_native_runner_sessions",
                    return_value=True,
                ) as session_sync:
                    asyncio.run(_execute_run(run_id, executor))

                run = self.connection.execute(
                    "SELECT * FROM maintenance_runs WHERE id = ?", (run_id,)
                ).fetchone()
                result = json.loads(run["structured_result_json"])
                calls = json.loads(run["mcp_tool_calls_json"])
                self.assertEqual(run["status"], "completed")
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["summary"], model_result["summary"])
                self.assertEqual(result["targets"][0]["outcome"], "unchanged")
                self.assertEqual(run["mcp_calls_used"], 1)
                self.assertNotIn("arguments", calls[0])
                session_sync.assert_called_once_with(runner_kind)

    def test_runtime_persists_partial_and_all_failed_source_results(self):
        scenarios = (
            (
                "partial",
                [self.target("partial-one"), self.target("partial-two")],
                ["resolved", "unavailable"],
            ),
            (
                "failed",
                [self.target("failed-one")],
                ["not_found"],
            ),
        )
        for expected_status, targets, outcomes in scenarios:
            with self.subTest(status=expected_status):
                run_id = prepare_external_sync_run(
                    self.connection,
                    runner="claude",
                    source_instance_id=self.instance["id"],
                    source_kind="atlassian",
                    scope_kind="all_known",
                    targets=targets,
                    run_root=self.run_root,
                )
                model_result = {
                    "schema": MODEL_RESULT_SCHEMA_VERSION,
                    "run_id": run_id,
                    "summary": "{} synthetic summary".format(expected_status),
                }
                remaining = list(outcomes)

                async def executor(_dispatch):
                    outcome = remaining.pop(0)
                    if outcome in {"resolved", "unchanged", "changed"}:
                        return {
                            "outcome": outcome,
                            "metadata": {
                                "key": "SYN-1",
                                "summary": "Synthetic",
                            },
                        }
                    return {
                        "outcome": outcome,
                        "error": {
                            "code": outcome.replace("_", "-"),
                            "message": "Synthetic bounded failure.",
                        },
                    }

                async def create_process(*_arguments, **_kwargs):
                    return _FakeProcess(
                        [
                            json.dumps(
                                {
                                    "type": "result",
                                    "structured_output": model_result,
                                }
                            )
                            + "\n"
                        ]
                    )

                connect_patch, transaction_patch = self.runner_patches()
                with connect_patch, transaction_patch, patch(
                    "localbrain.runner.runner_executable",
                    return_value="/synthetic/claude",
                ), patch(
                    "localbrain.runner.asyncio.create_subprocess_exec",
                    side_effect=create_process,
                ), patch(
                    "localbrain.runner._sync_native_runner_sessions",
                    return_value=True,
                ):
                    asyncio.run(_execute_run(run_id, executor))

                run = self.connection.execute(
                    "SELECT * FROM maintenance_runs WHERE id = ?", (run_id,)
                ).fetchone()
                result = json.loads(run["structured_result_json"])
                self.assertEqual(run["status"], expected_status)
                self.assertEqual(result["status"], expected_status)
                self.assertEqual(
                    [target["outcome"] for target in result["targets"]],
                    outcomes,
                )

    def test_missing_executor_and_invalid_model_result_fail_closed(self):
        run_id = prepare_external_sync_run(
            self.connection,
            runner="codex",
            source_instance_id=self.instance["id"],
            source_kind="atlassian",
            scope_kind="item",
            targets=[self.target()],
            run_root=self.run_root,
        )
        connect_patch, transaction_patch = self.runner_patches()
        with connect_patch, transaction_patch, patch(
            "localbrain.runner.asyncio.create_subprocess_exec",
            new_callable=AsyncMock,
        ) as create_process, patch(
            "localbrain.runner._sync_native_runner_sessions",
            return_value=True,
        ):
            asyncio.run(_execute_run(run_id))
        run = self.connection.execute(
            "SELECT * FROM maintenance_runs WHERE id = ?", (run_id,)
        ).fetchone()
        self.assertEqual(run["status"], "failed")
        self.assertIn("approved read executor", run["error"])
        create_process.assert_not_awaited()

        invalid_id = prepare_external_sync_run(
            self.connection,
            runner="claude",
            source_instance_id=self.instance["id"],
            source_kind="atlassian",
            scope_kind="item",
            targets=[self.target("invalid-model")],
            run_root=self.run_root,
        )

        async def executor(_dispatch):
            return {
                "outcome": "resolved",
                "metadata": {"key": "SYN-1", "summary": "Synthetic"},
            }

        async def invalid_process(*_arguments, **_kwargs):
            return _FakeProcess(
                [
                    json.dumps(
                        {
                            "type": "result",
                            "structured_output": {
                                "schema": MODEL_RESULT_SCHEMA_VERSION,
                                "run_id": invalid_id,
                                "summary": "Attempted summary",
                                "metadata": {"summary": "invented"},
                            },
                        }
                    )
                    + "\n"
                ]
            )

        connect_patch, transaction_patch = self.runner_patches()
        with connect_patch, transaction_patch, patch(
            "localbrain.runner.runner_executable",
            return_value="/synthetic/claude",
        ), patch(
            "localbrain.runner.asyncio.create_subprocess_exec",
            side_effect=invalid_process,
        ), patch(
            "localbrain.runner._sync_native_runner_sessions",
            return_value=True,
        ):
            asyncio.run(_execute_run(invalid_id, executor))
        invalid_run = self.connection.execute(
            "SELECT * FROM maintenance_runs WHERE id = ?", (invalid_id,)
        ).fetchone()
        self.assertEqual(invalid_run["status"], "failed")
        self.assertIsNone(invalid_run["structured_result_json"])
        self.assertIn("unsupported fields", invalid_run["error"])
        self.assertTrue(
            (Path(invalid_run["manifest_path"]).parent / "evidence.json").is_file()
        )

    def test_cancel_and_restart_recovery_use_selected_runner(self):
        cancel_id = prepare_external_sync_run(
            self.connection,
            runner="codex",
            source_instance_id=self.instance["id"],
            source_kind="atlassian",
            scope_kind="item",
            targets=[self.target("cancel")],
            run_root=self.run_root,
        )
        connect_patch, transaction_patch = self.runner_patches()
        with connect_patch, transaction_patch, patch(
            "localbrain.runner._sync_native_runner_sessions",
            return_value=True,
        ) as session_sync:
            self.assertTrue(asyncio.run(cancel_run(cancel_id)))
        self.assertEqual(
            self.connection.execute(
                "SELECT status FROM maintenance_runs WHERE id = ?", (cancel_id,)
            ).fetchone()["status"],
            "cancelled",
        )
        session_sync.assert_called_once_with("codex")

        interrupted_id = prepare_external_sync_run(
            self.connection,
            runner="codex",
            source_instance_id=self.instance["id"],
            source_kind="atlassian",
            scope_kind="item",
            targets=[self.target("restart")],
            run_root=self.run_root,
        )
        self.connection.execute(
            "UPDATE maintenance_runs SET status = 'running' WHERE id = ?",
            (interrupted_id,),
        )
        self.connection.commit()
        connect_patch, transaction_patch = self.runner_patches()
        with connect_patch, transaction_patch, patch(
            "localbrain.runner._sync_native_runner_sessions",
            return_value=True,
        ) as session_sync:
            self.assertEqual(reconcile_interrupted_runs(), 1)
        self.assertEqual(
            self.connection.execute(
                "SELECT status FROM maintenance_runs WHERE id = ?",
                (interrupted_id,),
            ).fetchone()["status"],
            "interrupted",
        )
        session_sync.assert_called_once_with("codex")


if __name__ == "__main__":
    unittest.main()
