import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.config import Settings
from localbrain.db import init_db
from localbrain.ingest.claude import parse_claude_session
from localbrain.ingest.codex import (
    CODEX_USAGE_CONTRACT_VERSION,
    parse_codex_session,
)
from localbrain.ingest.common import ParsedSession, ParsedUsageFact, stable_id
from localbrain.ingest.scanner import (
    _file_is_current,
    _scan_session_source,
    _store_session,
)
from localbrain.usage import (
    CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID,
    CONTEXT_TIER_CALCULATOR_VERSION,
    DEFAULT_PRICE_SNAPSHOT_ID,
    ensure_default_price_snapshot,
    reconcile_usage_fact_contract,
)


SCHEMA_PATH = Path(__file__).parents[1] / "src" / "localbrain" / "schema.sql"


class UsageContractTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.claude_source_id = self.connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('claude', 'Claude', '/tmp/claude')"
        ).lastrowid
        self.codex_source_id = self.connection.execute(
            "INSERT INTO sources(kind, name, root_path) VALUES ('codex', 'Codex', '/tmp/codex')"
        ).lastrowid

    def tearDown(self):
        self.connection.close()

    def _write_jsonl(self, records, path=None):
        if path is None:
            handle = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
            handle.close()
            path = Path(handle.name)
            self.addCleanup(path.unlink, missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(json.dumps(record) for record in records) + "\n",
            encoding="utf-8",
        )
        return path

    def test_claude_normalizes_cache_components_and_estimated_cost(self):
        path = self._write_jsonl(
            [
                {
                    "type": "assistant",
                    "sessionId": "claude-usage",
                    "uuid": "message-1",
                    "cwd": "/tmp/claude-project",
                    "timestamp": "2026-07-18T01:00:00Z",
                    "message": {
                        "model": "claude-sonnet-4-6",
                        "content": [{"type": "text", "text": "done"}],
                        "usage": {
                            "input_tokens": 100,
                            "output_tokens": 50,
                            "cache_creation_input_tokens": 20,
                            "cache_read_input_tokens": 30,
                        },
                    },
                }
            ]
        )
        parsed = parse_claude_session(path)
        self.assertEqual(len(parsed.usage_facts), 1)
        fact = parsed.usage_facts[0]
        self.assertEqual(
            (
                fact.input_tokens,
                fact.output_tokens,
                fact.cache_write_tokens,
                fact.cache_read_tokens,
                fact.reasoning_tokens,
                fact.total_tokens,
            ),
            (100, 50, 20, 30, None, 200),
        )
        self.assertEqual(fact.capability_state, "complete")

        _store_session(self.connection, self.claude_source_id, "claude", parsed)
        stored = self.connection.execute("SELECT * FROM usage_facts").fetchone()
        self.assertEqual(stored["calculation_state"], "priced")
        self.assertEqual(stored["estimated_cost_usd"], "0.001134000000")
        self.assertEqual(stored["price_snapshot_id"], DEFAULT_PRICE_SNAPSHOT_ID)

    def test_claude_prefers_positive_nested_cache_breakdown_over_zero_aggregate(self):
        path = self._write_jsonl(
            [
                {
                    "type": "assistant",
                    "sessionId": "claude-cache-edge",
                    "uuid": "message-edge",
                    "timestamp": "2026-06-20T01:00:00Z",
                    "message": {
                        "id": "message-edge",
                        "model": "claude-sonnet-4-6",
                        "content": [],
                        "usage": {
                            "input_tokens": 10,
                            "output_tokens": 5,
                            "cache_creation_input_tokens": 0,
                            "cache_creation": {
                                "ephemeral_1h_input_tokens": 27,
                                "ephemeral_5m_input_tokens": 0,
                            },
                            "cache_read_input_tokens": 20,
                        },
                    },
                }
            ]
        )

        fact = parse_claude_session(path).usage_facts[0]

        self.assertEqual(fact.cache_write_tokens, 27)
        self.assertEqual(
            fact.capability["cache_write_source"],
            "nested_preferred_over_zero_aggregate",
        )

    def test_codex_prefers_each_positive_direct_event_without_double_count(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-07-18T02:00:00Z",
                    "payload": {"id": "codex-usage", "cwd": "/tmp/codex-project"},
                },
                {
                    "type": "turn_context",
                    "timestamp": "2026-07-18T02:01:00Z",
                    "payload": {"turn_id": "turn-1", "model": "gpt-5.5"},
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-18T02:02:00Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "last_token_usage": {
                                "input_tokens": 500,
                                "cached_input_tokens": 100,
                                "output_tokens": 100,
                                "reasoning_output_tokens": 40,
                                "total_tokens": 600,
                            },
                            "total_token_usage": {
                                "input_tokens": 500,
                                "cached_input_tokens": 100,
                                "output_tokens": 100,
                                "reasoning_output_tokens": 40,
                                "total_tokens": 600,
                            },
                        },
                    },
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-18T02:03:00Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "last_token_usage": {
                                "input_tokens": 500,
                                "cached_input_tokens": 300,
                                "output_tokens": 100,
                                "reasoning_output_tokens": 40,
                                "total_tokens": 600,
                            },
                            "total_token_usage": {
                                "input_tokens": 2000,
                                "cached_input_tokens": 900,
                                "output_tokens": 500,
                                "reasoning_output_tokens": 180,
                                "total_tokens": 2500,
                            },
                        },
                    },
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-18T02:04:00Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 2000,
                                "cached_input_tokens": 900,
                                "output_tokens": 500,
                                "reasoning_output_tokens": 180,
                                "total_tokens": 2500,
                            }
                        },
                    },
                },
            ]
        )
        parsed = parse_codex_session(path)
        self.assertEqual(len(parsed.usage_facts), 2)
        self.assertTrue(
            all(
                fact.capability["usage_source"] == "last_token_usage"
                for fact in parsed.usage_facts
            )
        )
        self.assertEqual(
            (
                sum(fact.input_tokens or 0 for fact in parsed.usage_facts),
                sum(fact.output_tokens or 0 for fact in parsed.usage_facts),
                sum(fact.cache_read_tokens or 0 for fact in parsed.usage_facts),
                sum(fact.reasoning_tokens or 0 for fact in parsed.usage_facts),
                sum(fact.source_total_tokens or 0 for fact in parsed.usage_facts),
                sum(fact.total_tokens or 0 for fact in parsed.usage_facts),
            ),
            (600, 200, 400, 80, 1200, 1200),
        )

        _store_session(self.connection, self.codex_source_id, "codex", parsed)
        stored = self.connection.execute(
            """
            SELECT COUNT(*) AS facts,
                   SUM(CAST(estimated_cost_usd AS REAL)) AS cost,
                   MIN(normalizer_version) AS min_version,
                   MAX(normalizer_version) AS max_version
            FROM usage_facts
            """
        ).fetchone()
        self.assertEqual(stored["facts"], 2)
        self.assertAlmostEqual(stored["cost"], 0.023)
        self.assertEqual(stored["min_version"], CODEX_USAGE_CONTRACT_VERSION)
        self.assertEqual(stored["max_version"], CODEX_USAGE_CONTRACT_VERSION)

    def test_codex_uses_cumulative_delta_only_when_direct_event_is_absent(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-07-18T02:00:00Z",
                    "payload": {"id": "codex-fallback", "cwd": "/tmp/codex"},
                },
                {
                    "type": "turn_context",
                    "timestamp": "2026-07-18T02:01:00Z",
                    "payload": {"turn_id": "turn-1", "model": "gpt-5.6-sol"},
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-18T02:02:00Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "last_token_usage": {
                                "input_tokens": 100,
                                "cached_input_tokens": 40,
                                "output_tokens": 20,
                                "reasoning_output_tokens": 5,
                                "total_tokens": 120,
                            },
                            "total_token_usage": {
                                "input_tokens": 100,
                                "cached_input_tokens": 40,
                                "output_tokens": 20,
                                "reasoning_output_tokens": 5,
                                "total_tokens": 120,
                            },
                        },
                    },
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-18T02:03:00Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 300,
                                "cached_input_tokens": 150,
                                "output_tokens": 60,
                                "reasoning_output_tokens": 20,
                                "total_tokens": 360,
                            }
                        },
                    },
                },
            ]
        )

        facts = parse_codex_session(path).usage_facts

        self.assertEqual(len(facts), 2)
        fallback = facts[1]
        self.assertEqual(fallback.capability["usage_source"], "cumulative_delta")
        self.assertEqual(
            (
                fallback.input_tokens,
                fallback.output_tokens,
                fallback.cache_read_tokens,
                fallback.reasoning_tokens,
                fallback.total_tokens,
            ),
            (90, 40, 110, 15, 240),
        )

    def test_codex_prices_context_tier_per_event_and_returns_to_base_after_compaction(self):
        def token_event(timestamp, source_input, cached_input, output):
            return {
                "type": "event_msg",
                "timestamp": timestamp,
                "payload": {
                    "type": "token_count",
                    "info": {
                        "last_token_usage": {
                            "input_tokens": source_input,
                            "cached_input_tokens": cached_input,
                            "output_tokens": output,
                            "reasoning_output_tokens": 40,
                            "total_tokens": source_input + output,
                        }
                    },
                },
            }

        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-07-18T02:00:00Z",
                    "payload": {"id": "codex-context-tier", "cwd": "/tmp/codex"},
                },
                {
                    "type": "turn_context",
                    "timestamp": "2026-07-18T02:01:00Z",
                    "payload": {"turn_id": "turn-1", "model": "gpt-5.6-sol"},
                },
                token_event("2026-07-18T02:02:00Z", 272_000, 271_000, 100),
                token_event("2026-07-18T02:03:00Z", 272_001, 271_001, 100),
                token_event("2026-07-18T02:04:00Z", 10_000, 9_000, 100),
            ]
        )

        parsed = parse_codex_session(path)
        _store_session(self.connection, self.codex_source_id, "codex", parsed)
        rows = self.connection.execute(
            """
            SELECT estimated_cost_usd, price_snapshot_id, calculator_version
            FROM usage_facts ORDER BY source_line
            """
        ).fetchall()

        self.assertEqual(
            [row["estimated_cost_usd"] for row in rows],
            ["0.287000000000", "0.571002000000", "0.025000000000"],
        )
        self.assertTrue(
            all(
                row["price_snapshot_id"]
                == CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID
                for row in rows
            )
        )
        self.assertTrue(
            all(
                row["calculator_version"] == CONTEXT_TIER_CALCULATOR_VERSION
                for row in rows
            )
        )

    def test_codex_tiered_snapshot_freezes_every_supported_model_boundary(self):
        ensure_default_price_snapshot(self.connection)
        rows = self.connection.execute(
            """
            SELECT model_name, long_context_threshold_tokens,
                   long_context_input_usd_per_million,
                   long_context_output_usd_per_million,
                   long_context_cache_read_usd_per_million
            FROM usage_model_prices
            WHERE snapshot_id = ?
            ORDER BY model_name
            """,
            (CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID,),
        ).fetchall()

        self.assertEqual(
            {
                row["model_name"]: (
                    row["long_context_threshold_tokens"],
                    row["long_context_input_usd_per_million"],
                    row["long_context_output_usd_per_million"],
                    row["long_context_cache_read_usd_per_million"],
                )
                for row in rows
            },
            {
                "gpt-5.5": (272_000, "25", "112.5", "2.5"),
                "gpt-5.6-luna": (200_000, "4", "18", "0.40"),
                "gpt-5.6-sol": (272_000, "20", "90", "2"),
                "gpt-5.6-terra": (272_000, "10", "45", "1"),
            },
        )

    def test_codex_excludes_initial_subagent_replay_and_keeps_following_delta(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-07-18T02:00:00Z",
                    "payload": {
                        "id": "codex-subagent-replay",
                        "cwd": "/tmp/codex",
                        "forked_from_id": "parent-session",
                        "source": {"subagent": {"kind": "thread_spawn"}},
                    },
                },
                {
                    "type": "turn_context",
                    "timestamp": "2026-07-18T02:01:00Z",
                    "payload": {"turn_id": "turn-1", "model": "gpt-5.6-sol"},
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-18T02:02:00.100Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "last_token_usage": {
                                "input_tokens": 100,
                                "cached_input_tokens": 40,
                                "output_tokens": 20,
                                "reasoning_output_tokens": 5,
                                "total_tokens": 120,
                            },
                            "total_token_usage": {
                                "input_tokens": 100,
                                "cached_input_tokens": 40,
                                "output_tokens": 20,
                                "reasoning_output_tokens": 5,
                                "total_tokens": 120,
                            },
                        },
                    },
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-18T02:02:00.500Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "last_token_usage": {
                                "input_tokens": 200,
                                "cached_input_tokens": 80,
                                "output_tokens": 40,
                                "reasoning_output_tokens": 10,
                                "total_tokens": 240,
                            },
                            "total_token_usage": {
                                "input_tokens": 200,
                                "cached_input_tokens": 80,
                                "output_tokens": 40,
                                "reasoning_output_tokens": 10,
                                "total_tokens": 240,
                            },
                        },
                    },
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-18T02:03:00Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 300,
                                "cached_input_tokens": 120,
                                "output_tokens": 60,
                                "reasoning_output_tokens": 15,
                                "total_tokens": 360,
                            }
                        },
                    },
                },
            ]
        )

        facts = parse_codex_session(path).usage_facts

        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].capability["usage_source"], "cumulative_delta")
        self.assertEqual(
            (
                facts[0].input_tokens,
                facts[0].output_tokens,
                facts[0].cache_read_tokens,
                facts[0].total_tokens,
            ),
            (60, 20, 40, 120),
        )

    def test_codex_auto_review_keeps_raw_model_and_uses_dated_fast_price(self):
        path = self._write_jsonl(
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-07-18T02:00:00Z",
                    "payload": {"id": "codex-auto", "cwd": "/tmp/codex"},
                },
                {
                    "type": "turn_context",
                    "timestamp": "2026-07-18T02:01:00Z",
                    "payload": {
                        "turn_id": "turn-1",
                        "model": "codex-auto-review",
                    },
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-07-18T02:02:00Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "last_token_usage": {
                                "input_tokens": 100,
                                "cached_input_tokens": 40,
                                "output_tokens": 20,
                                "reasoning_output_tokens": 5,
                                "total_tokens": 120,
                            }
                        },
                    },
                },
            ]
        )

        parsed = parse_codex_session(path)
        fact = parsed.usage_facts[0]
        self.assertEqual(fact.raw_model, "codex-auto-review")
        self.assertEqual(fact.normalized_model, "gpt-5.5")
        self.assertEqual(
            fact.capability["model_resolution"], "dated_auto_review_fallback"
        )
        self.assertEqual(
            fact.price_snapshot_id, CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID
        )

        _store_session(self.connection, self.codex_source_id, "codex", parsed)
        stored = self.connection.execute(
            "SELECT raw_model, model_name, price_snapshot_id FROM usage_facts"
        ).fetchone()
        self.assertEqual(stored["raw_model"], "codex-auto-review")
        self.assertEqual(stored["model_name"], "gpt-5.5")
        self.assertEqual(
            stored["price_snapshot_id"], CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID
        )

    def test_contract_repair_applies_explicit_price_snapshot_and_preserves_project(self):
        old_fact = ParsedUsageFact(
            fact_id="old-turn-fact",
            source_record_id="turn-1",
            source_line=10,
            occurred_at="2026-07-18T02:00:00Z",
            raw_model="gpt-5.5",
            input_tokens=100,
            output_tokens=20,
            cache_write_tokens=None,
            cache_read_tokens=80,
            reasoning_tokens=5,
            source_total_tokens=200,
            total_tokens=200,
            total_semantics="legacy-latest-turn",
        )
        parsed = ParsedSession(
            external_id="repair-session",
            source_path="/tmp/repair-session.jsonl",
            cwd_raw="/tmp/original-project",
            git_branch=None,
            title="repair",
            started_at=None,
            ended_at=None,
            last_event_at=None,
            events=[],
            usage_facts=[old_fact],
        )
        _store_session(
            self.connection,
            self.codex_source_id,
            "codex",
            parsed,
            usage_contract_version="codex-latest-turn-v1",
        )
        original = self.connection.execute(
            """
            SELECT price_snapshot_id, project_path_snapshot
            FROM usage_facts WHERE id = 'old-turn-fact'
            """
        ).fetchone()

        parsed.cwd_raw = "/tmp/current-project"
        parsed.usage_facts = [
            ParsedUsageFact(
                fact_id="delta-1",
                source_record_id="line-8",
                source_line=8,
                occurred_at="2026-07-18T01:59:00Z",
                raw_model="gpt-5.5",
                input_tokens=50,
                output_tokens=10,
                cache_write_tokens=None,
                cache_read_tokens=40,
                reasoning_tokens=2,
                source_total_tokens=100,
                total_tokens=100,
                total_semantics="cumulative-delta",
                price_snapshot_id=CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID,
            ),
            ParsedUsageFact(
                fact_id="delta-2",
                source_record_id="line-12",
                source_line=12,
                occurred_at="2026-07-18T02:01:00Z",
                raw_model="gpt-5.5",
                input_tokens=50,
                output_tokens=10,
                cache_write_tokens=None,
                cache_read_tokens=40,
                reasoning_tokens=3,
                source_total_tokens=100,
                total_tokens=100,
                total_semantics="cumulative-delta",
                price_snapshot_id=CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID,
            ),
        ]
        _store_session(
            self.connection,
            self.codex_source_id,
            "codex",
            parsed,
            usage_contract_version=CODEX_USAGE_CONTRACT_VERSION,
        )
        reconcile_usage_fact_contract(
            self.connection,
            self.codex_source_id,
            {"delta-1", "delta-2"},
        )
        rows = self.connection.execute(
            """
            SELECT id, price_snapshot_id, project_path_snapshot, normalizer_version
            FROM usage_facts ORDER BY id
            """
        ).fetchall()

        self.assertEqual([row["id"] for row in rows], ["delta-1", "delta-2"])
        self.assertTrue(
            all(
                row["price_snapshot_id"] == CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID
                for row in rows
            )
        )
        self.assertTrue(
            all(
                row["project_path_snapshot"] == original["project_path_snapshot"]
                for row in rows
            )
        )
        self.assertTrue(
            all(row["normalizer_version"] == CODEX_USAGE_CONTRACT_VERSION for row in rows)
        )
        _store_session(
            self.connection,
            self.codex_source_id,
            "codex",
            parsed,
            usage_contract_version=CODEX_USAGE_CONTRACT_VERSION,
        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM usage_facts").fetchone()[0],
            2,
        )

    def test_failed_contract_repair_rolls_back_the_prior_fact_set(self):
        old_fact = ParsedUsageFact(
            fact_id="retained-old-fact",
            source_record_id="old",
            source_line=1,
            occurred_at=None,
            raw_model="gpt-5.5",
            input_tokens=10,
            output_tokens=5,
            cache_write_tokens=None,
            cache_read_tokens=0,
            reasoning_tokens=1,
            source_total_tokens=15,
            total_tokens=15,
            total_semantics="legacy",
        )
        parsed = ParsedSession(
            external_id="rollback-session",
            source_path="/tmp/rollback-session.jsonl",
            cwd_raw="/tmp",
            git_branch=None,
            title="rollback",
            started_at=None,
            ended_at=None,
            last_event_at=None,
            events=[],
            usage_facts=[old_fact],
        )
        _store_session(
            self.connection,
            self.codex_source_id,
            "codex",
            parsed,
            usage_contract_version="codex-latest-turn-v1",
        )
        parsed.usage_facts = [
            ParsedUsageFact(
                fact_id="new-valid-before-failure",
                source_record_id="new-valid",
                source_line=2,
                occurred_at=None,
                raw_model="gpt-5.5",
                input_tokens=20,
                output_tokens=5,
                cache_write_tokens=None,
                cache_read_tokens=0,
                reasoning_tokens=1,
                source_total_tokens=25,
                total_tokens=25,
                total_semantics="delta",
            ),
            ParsedUsageFact(
                fact_id="new-invalid",
                source_record_id="new-invalid",
                source_line=3,
                occurred_at=None,
                raw_model="gpt-5.5",
                input_tokens=20,
                output_tokens=5,
                cache_write_tokens=None,
                cache_read_tokens=0,
                reasoning_tokens=1,
                source_total_tokens=25,
                total_tokens=25,
                total_semantics="delta",
                aggregation_scope="invalid",
            ),
        ]

        with self.assertRaises(sqlite3.IntegrityError):
            _store_session(
                self.connection,
                self.codex_source_id,
                "codex",
                parsed,
                usage_contract_version=CODEX_USAGE_CONTRACT_VERSION,
            )

        rows = self.connection.execute(
            "SELECT id, normalizer_version FROM usage_facts"
        ).fetchall()
        self.assertEqual(
            [(row["id"], row["normalizer_version"]) for row in rows],
            [("retained-old-fact", "codex-latest-turn-v1")],
        )

    def test_source_file_contract_version_participates_in_freshness(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as handle:
            path = Path(handle.name)
        self.addCleanup(path.unlink, missing_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        stat = path.stat()
        self.connection.execute(
            """
            INSERT INTO source_files(
                source_id, path, size_bytes, mtime_ns, last_scanned_at, status,
                usage_contract_version
            ) VALUES (?, ?, ?, ?, '2026-07-18', 'ok', ?)
            """,
            (
                self.codex_source_id,
                str(path),
                stat.st_size,
                stat.st_mtime_ns,
                "codex-latest-turn-v1",
            ),
        )

        self.assertFalse(
            _file_is_current(
                self.connection,
                self.codex_source_id,
                path,
                CODEX_USAGE_CONTRACT_VERSION,
            )
        )
        self.connection.execute(
            "UPDATE source_files SET usage_contract_version = ? WHERE path = ?",
            (CODEX_USAGE_CONTRACT_VERSION, str(path)),
        )
        self.assertTrue(
            _file_is_current(
                self.connection,
                self.codex_source_id,
                path,
                CODEX_USAGE_CONTRACT_VERSION,
            )
        )

    def test_source_contract_repair_reconciles_union_across_shared_session_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_path = self._write_jsonl(
                [
                    {
                        "type": "assistant",
                        "sessionId": "shared-session",
                        "uuid": "message-one",
                        "timestamp": "2026-07-18T01:00:00Z",
                        "message": {
                            "model": "claude-sonnet-4-6",
                            "content": [],
                            "usage": {
                                "input_tokens": 10,
                                "output_tokens": 5,
                                "cache_creation_input_tokens": 0,
                                "cache_read_input_tokens": 0,
                            },
                        },
                    }
                ],
                root / "first.jsonl",
            )
            self._write_jsonl(
                [
                    {
                        "type": "assistant",
                        "sessionId": "shared-session",
                        "uuid": "message-two",
                        "timestamp": "2026-07-18T01:01:00Z",
                        "message": {
                            "model": "claude-sonnet-4-6",
                            "content": [],
                            "usage": {
                                "input_tokens": 20,
                                "output_tokens": 10,
                                "cache_creation_input_tokens": 0,
                                "cache_read_input_tokens": 0,
                            },
                        },
                    }
                ],
                root / "second.jsonl",
            )

            imported, skipped, failed = _scan_session_source(
                self.connection,
                "claude",
                "Claude",
                root,
                parse_claude_session,
                "claude-test-v1",
            )
            self.assertEqual((imported, skipped, failed), (2, 0, 0))

            parsed = parse_claude_session(first_path)
            parsed.usage_facts.append(
                ParsedUsageFact(
                    fact_id="obsolete-shared-session-fact",
                    source_record_id="obsolete",
                    source_line=99,
                    occurred_at="2026-07-18T01:02:00Z",
                    raw_model="claude-sonnet-4-6",
                    input_tokens=30,
                    output_tokens=10,
                    cache_write_tokens=0,
                    cache_read_tokens=0,
                    reasoning_tokens=None,
                    source_total_tokens=None,
                    total_tokens=40,
                    total_semantics="obsolete-test-contract",
                )
            )
            _store_session(
                self.connection,
                self.claude_source_id,
                "claude",
                parsed,
                usage_contract_version="claude-test-v1",
            )
            self.assertEqual(
                self.connection.execute(
                    "SELECT COUNT(*) FROM usage_facts WHERE source_id = ?",
                    (self.claude_source_id,),
                ).fetchone()[0],
                3,
            )

            imported, skipped, failed = _scan_session_source(
                self.connection,
                "claude",
                "Claude",
                root,
                parse_claude_session,
                "claude-test-v2",
            )
            self.assertEqual((imported, skipped, failed), (2, 0, 0))
            rows = self.connection.execute(
                """
                SELECT source_record_id, normalizer_version
                FROM usage_facts
                WHERE source_id = ?
                ORDER BY source_record_id
                """,
                (self.claude_source_id,),
            ).fetchall()
            self.assertEqual(
                [row["source_record_id"] for row in rows],
                ["message-one", "message-two"],
            )
            self.assertTrue(
                all(row["normalizer_version"] == "claude-test-v2" for row in rows)
            )

            imported, skipped, failed = _scan_session_source(
                self.connection,
                "claude",
                "Claude",
                root,
                parse_claude_session,
                "claude-test-v2",
            )
            self.assertEqual((imported, skipped, failed), (0, 2, 0))

    def test_session_file_appended_during_parse_remains_stale_for_next_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self._write_jsonl(
                [
                    {
                        "type": "assistant",
                        "sessionId": "active-session",
                        "uuid": "first-message",
                        "timestamp": "2026-07-18T01:00:00Z",
                        "message": {
                            "model": "claude-sonnet-4-6",
                            "content": [],
                            "usage": {
                                "input_tokens": 10,
                                "output_tokens": 5,
                            },
                        },
                    }
                ],
                root / "active.jsonl",
            )
            appended = False

            def parse_then_append(active_path):
                nonlocal appended
                parsed = parse_claude_session(active_path)
                if not appended:
                    with active_path.open("a", encoding="utf-8") as stream:
                        stream.write(
                            json.dumps(
                                {
                                    "type": "assistant",
                                    "sessionId": "active-session",
                                    "uuid": "second-message",
                                    "timestamp": "2026-07-18T01:01:00Z",
                                    "message": {
                                        "model": "claude-sonnet-4-6",
                                        "content": [],
                                        "usage": {
                                            "input_tokens": 20,
                                            "output_tokens": 10,
                                        },
                                    },
                                }
                            )
                            + "\n"
                        )
                    appended = True
                return parsed

            imported, skipped, failed = _scan_session_source(
                self.connection,
                "claude",
                "Claude",
                root,
                parse_then_append,
                "claude-active-v1",
            )
            self.assertEqual((imported, skipped, failed), (1, 0, 0))
            self.assertFalse(
                _file_is_current(
                    self.connection,
                    self.claude_source_id,
                    path,
                    "claude-active-v1",
                )
            )

            imported, skipped, failed = _scan_session_source(
                self.connection,
                "claude",
                "Claude",
                root,
                parse_claude_session,
                "claude-active-v1",
            )
            self.assertEqual((imported, skipped, failed), (1, 0, 0))
            self.assertEqual(
                self.connection.execute(
                    "SELECT COUNT(*) FROM usage_facts WHERE source_id = ?",
                    (self.claude_source_id,),
                ).fetchone()[0],
                2,
            )
            self.assertTrue(
                _file_is_current(
                    self.connection,
                    self.claude_source_id,
                    path,
                    "claude-active-v1",
                )
            )

    def test_maintenance_and_subsession_usage_are_stored_and_rescan_is_idempotent(self):
        fact = ParsedUsageFact(
            fact_id=stable_id("usage", "maintenance", "turn-1"),
            source_record_id="turn-1",
            source_line=2,
            occurred_at="2026-07-18T03:00:00Z",
            raw_model="gpt-5.5",
            input_tokens=10,
            output_tokens=5,
            cache_write_tokens=None,
            cache_read_tokens=0,
            reasoning_tokens=2,
            source_total_tokens=15,
            total_tokens=15,
            total_semantics="reasoning_subset_of_output",
        )
        parsed = ParsedSession(
            external_id="maintenance-child",
            source_path="/tmp/maintenance-child.jsonl",
            cwd_raw="/tmp",
            git_branch=None,
            title="LocalBrain maintenance",
            started_at="2026-07-18T03:00:00Z",
            ended_at="2026-07-18T03:01:00Z",
            last_event_at="2026-07-18T03:01:00Z",
            events=[],
            session_class="maintenance",
            index_policy="metadata_only",
            session_role="subsession",
            parent_external_id="parent",
            usage_facts=[fact],
        )
        _store_session(self.connection, self.codex_source_id, "codex", parsed)
        _store_session(self.connection, self.codex_source_id, "codex", parsed)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM usage_facts").fetchone()[0],
            1,
        )
        row = self.connection.execute(
            """
            SELECT s.session_class, s.session_role, u.calculation_state
            FROM usage_facts u JOIN sessions s ON s.id = u.session_id
            """
        ).fetchone()
        self.assertEqual(
            (row["session_class"], row["session_role"], row["calculation_state"]),
            ("maintenance", "subsession", "priced"),
        )

    def test_unknown_and_malformed_usage_never_become_zero_cost(self):
        unknown = ParsedUsageFact(
            fact_id="unknown",
            source_record_id="unknown",
            source_line=1,
            occurred_at=None,
            raw_model="future-model",
            input_tokens=10,
            output_tokens=5,
            cache_write_tokens=None,
            cache_read_tokens=0,
            reasoning_tokens=1,
            source_total_tokens=15,
            total_tokens=15,
            total_semantics="reasoning_subset_of_output",
        )
        malformed = ParsedUsageFact(
            fact_id="malformed",
            source_record_id="malformed",
            source_line=2,
            occurred_at=None,
            raw_model="gpt-5.5",
            input_tokens=None,
            output_tokens=5,
            cache_write_tokens=None,
            cache_read_tokens=0,
            reasoning_tokens=1,
            source_total_tokens=None,
            total_tokens=None,
            total_semantics="unavailable",
            capability_state="malformed",
        )
        parsed = ParsedSession(
            external_id="unavailable",
            source_path="/tmp/unavailable.jsonl",
            cwd_raw="/tmp",
            git_branch=None,
            title="unavailable",
            started_at=None,
            ended_at=None,
            last_event_at=None,
            events=[],
            usage_facts=[unknown, malformed],
        )
        _store_session(self.connection, self.codex_source_id, "codex", parsed)
        rows = {
            row["id"]: row
            for row in self.connection.execute(
                "SELECT id, calculation_state, estimated_cost_usd FROM usage_facts"
            )
        }
        self.assertEqual(rows["unknown"]["calculation_state"], "unpriced")
        self.assertIsNone(rows["unknown"]["estimated_cost_usd"])
        self.assertEqual(rows["malformed"]["calculation_state"], "failed")
        self.assertIsNone(rows["malformed"]["estimated_cost_usd"])

    def test_existing_fact_retains_snapshot_when_default_changes(self):
        fact = ParsedUsageFact(
            fact_id="stable-fact",
            source_record_id="turn-stable",
            source_line=1,
            occurred_at="2026-07-18T04:00:00Z",
            raw_model="gpt-5.5",
            input_tokens=600,
            output_tokens=200,
            cache_write_tokens=None,
            cache_read_tokens=400,
            reasoning_tokens=80,
            source_total_tokens=1200,
            total_tokens=1200,
            total_semantics="reasoning_subset_of_output",
        )
        parsed = ParsedSession(
            external_id="snapshot-session",
            source_path="/tmp/snapshot.jsonl",
            cwd_raw="/tmp",
            git_branch=None,
            title="snapshot",
            started_at=None,
            ended_at=None,
            last_event_at=None,
            events=[],
            usage_facts=[fact],
        )
        _store_session(self.connection, self.codex_source_id, "codex", parsed)
        original = self.connection.execute(
            "SELECT price_snapshot_id, estimated_cost_usd FROM usage_facts"
        ).fetchone()

        with patch("localbrain.usage.DEFAULT_PRICE_SNAPSHOT_ID", "future-snapshot"):
            ensure_default_price_snapshot(self.connection)
            self.connection.execute(
                """
                UPDATE usage_model_prices
                SET input_usd_per_million = '50', output_usd_per_million = '300'
                WHERE snapshot_id = 'future-snapshot' AND model_name = 'gpt-5.5'
                """
            )
            fact.input_tokens = 1200
            fact.output_tokens = 400
            fact.cache_read_tokens = 800
            fact.source_total_tokens = 2400
            fact.total_tokens = 2400
            _store_session(self.connection, self.codex_source_id, "codex", parsed)

        updated = self.connection.execute(
            "SELECT price_snapshot_id, estimated_cost_usd FROM usage_facts"
        ).fetchone()
        self.assertEqual(original["price_snapshot_id"], DEFAULT_PRICE_SNAPSHOT_ID)
        self.assertEqual(updated["price_snapshot_id"], DEFAULT_PRICE_SNAPSHOT_ID)
        self.assertEqual(original["estimated_cost_usd"], "0.009200000000")
        self.assertEqual(updated["estimated_cost_usd"], "0.018400000000")

    def test_upgrade_adds_usage_contract_and_stales_existing_session_sources_once(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_dir = Path(temporary_directory)
            database_path = data_dir / "localbrain.db"
            legacy = sqlite3.connect(str(database_path))
            legacy.executescript(
                """
                CREATE TABLE sources (
                    id INTEGER PRIMARY KEY,
                    kind TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    root_path TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    last_scanned_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE source_files (
                    id INTEGER PRIMARY KEY,
                    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
                    path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    mtime_ns INTEGER NOT NULL,
                    last_scanned_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ok',
                    error TEXT,
                    UNIQUE(source_id, path)
                );
                INSERT INTO sources(kind, name, root_path)
                VALUES ('codex', 'Codex', '/tmp/codex');
                INSERT INTO source_files(
                    source_id, path, size_bytes, mtime_ns, last_scanned_at, status
                ) VALUES (1, '/tmp/codex/session.jsonl', 10, 10, '2026-07-18', 'ok');
                """
            )
            legacy.close()
            settings = Settings(
                data_dir=data_dir,
                database_path=database_path,
                context_root=data_dir / "context",
                claude_root=data_dir / "claude",
                codex_root=data_dir / "codex",
                mcp_call_budget=20,
            )
            with patch("localbrain.db.settings", settings):
                init_db()
                upgraded = sqlite3.connect(str(database_path))
                self.assertEqual(
                    upgraded.execute(
                        "SELECT status FROM source_files"
                    ).fetchone()[0],
                    "stale",
                )
                upgraded.execute("UPDATE source_files SET status = 'ok'")
                upgraded.commit()
                upgraded.close()
                init_db()

            upgraded = sqlite3.connect(str(database_path))
            self.assertEqual(
                upgraded.execute("SELECT status FROM source_files").fetchone()[0],
                "ok",
            )
            self.assertEqual(
                upgraded.execute(
                    "SELECT COUNT(*) FROM usage_price_snapshots"
                ).fetchone()[0],
                3,
            )
            columns = {
                row[1]
                for row in upgraded.execute("PRAGMA table_info(usage_model_prices)")
            }
            self.assertTrue(
                {
                    "long_context_threshold_tokens",
                    "long_context_input_usd_per_million",
                    "long_context_output_usd_per_million",
                    "long_context_cache_write_usd_per_million",
                    "long_context_cache_read_usd_per_million",
                }.issubset(columns)
            )
            upgraded.close()


if __name__ == "__main__":
    unittest.main()
