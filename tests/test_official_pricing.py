import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.config import Settings
from localbrain.db import init_db
from localbrain.ingest.codex import parse_codex_session
from localbrain.ingest.scanner import _store_session
from localbrain.official_pricing import PRICE_SPECS, UNAVAILABLE_SNAPSHOT_ID, select_snapshot
from localbrain.usage import price_existing_unpriced_sol_6_1_records, price_existing_unpriced_spark_records


SCHEMA = Path(__file__).parents[1] / "src/localbrain/schema.sql"
MODEL = "gpt-6.1-sol"
STANDARD = "official-openai-gpt-6-1-sol-standard-20260929-v1"
FAST = "official-openai-gpt-6-1-sol-fast-20260929-v1"


class OfficialSolPricingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="localbrain-sol-pricing-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.connection = sqlite3.connect(":memory:")
        self.addCleanup(self.connection.close)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA.read_text())
        self.source_id = self.connection.execute(
            "INSERT INTO sources(kind, provider_kind, name, root_path) VALUES ('codex', 'codex', 'Synthetic', ?)",
            (str(self.root),),
        ).lastrowid
        self.sequence = 0

    def store(self, *, tier="standard", model=MODEL, at="2026-09-29T12:00:00Z",
              input_tokens=1000, cached_input=800, output_tokens=100, unavailable=False):
        self.sequence += 1
        external_id = "synthetic-sol-{}".format(self.sequence)
        path = self.root / (external_id + ".jsonl")
        records = [
            {"type": "session_meta", "timestamp": at, "payload": {"id": external_id}},
            {"type": "turn_context", "timestamp": at, "payload": {"turn_id": "turn", "model": model}},
            {"type": "thread_settings_applied", "payload": {"thread_settings": {"service_tier": tier}}},
            {"type": "event_msg", "timestamp": at, "payload": {"type": "token_count", "info": {
                "last_token_usage": {"input_tokens": input_tokens, "cached_input_tokens": cached_input,
                                     "output_tokens": output_tokens, "reasoning_output_tokens": 40,
                                     "total_tokens": input_tokens + output_tokens},
            }}},
        ]
        path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
        parsed = parse_codex_session(path)
        self.assertEqual(len(parsed.usage_records), 1)
        if unavailable:
            parsed.usage_records[0].price_snapshot_id = UNAVAILABLE_SNAPSHOT_ID
        _store_session(self.connection, self.source_id, "codex", parsed)
        return dict(self.connection.execute(
            "SELECT usage_records.* FROM usage_records JOIN sessions ON sessions.id = usage_records.session_id "
            "WHERE sessions.external_id = ?", (external_id,),
        ).fetchone())

    def test_exact_sol_rates_and_release_boundary(self):
        specs = {spec.service_tier: spec for spec in PRICE_SPECS if spec.model == MODEL}
        for tier, expected in (
            ("standard", ("2", "10", "0.10", "4", "15.0", "0.20")),
            ("fast", ("4", "20", "0.20", "8", "30.0", "0.40")),
        ):
            with self.subTest(tier=tier):
                spec = specs[tier]
                self.assertEqual((spec.input_rate, spec.output_rate, spec.cache_read_rate,
                                  spec.long_input_rate, spec.long_output_rate, spec.long_cache_read_rate), expected)
                self.assertEqual(spec.long_context_threshold, 272000)
                self.assertEqual(spec.effective_on, "2026-09-29")
                self.assertEqual(spec.inspected_on, "2026-10-02")
                self.assertIn("https://developers.openai.com/api/docs/models/gpt-6.1-sol", spec.source_ref)
                self.assertIn("https://developers.openai.com/api/docs/changelog", spec.source_ref)
                self.assertEqual(select_snapshot("codex", MODEL, "2026-09-28", tier), UNAVAILABLE_SNAPSHOT_ID)
                self.assertEqual(select_snapshot("codex", "openai/" + MODEL, "2026-09-29", tier), spec.snapshot_id)
        previous = next(spec for spec in PRICE_SPECS if spec.model == "gpt-6-sol" and spec.service_tier == "standard")
        self.assertEqual(previous.cache_read_rate, "0.2")
        self.assertEqual(previous.inspected_on, "2026-09-25")
        self.assertEqual(select_snapshot("codex", MODEL, "2026-10-02", "unknown"), UNAVAILABLE_SNAPSHOT_ID)
        self.assertEqual(select_snapshot("codex", "gpt-6.1-sol-unknown", "2026-10-02"), UNAVAILABLE_SNAPSHOT_ID)

    def test_native_cost_uses_tier_and_each_request_context(self):
        cases = (
            ("standard", 1000, 800, "0.001480000000", STANDARD),
            ("fast", 1000, 800, "0.002960000000", FAST),
            ("standard", 272000, 271000, "0.030100000000", STANDARD),
            ("standard", 272001, 271001, "0.059700200000", STANDARD),
            ("fast", 272000, 271000, "0.060200000000", FAST),
            ("fast", 272001, 271001, "0.119400400000", FAST),
        )
        for tier, tokens, cached, cost, snapshot in cases:
            with self.subTest(tier=tier, tokens=tokens):
                row = self.store(tier=tier, input_tokens=tokens, cached_input=cached)
                self.assertEqual((row["calculation_state"], row["estimated_cost_usd"], row["price_snapshot_id"]),
                                 ("priced", cost, snapshot))
                self.assertEqual(row["input_tokens"], tokens - cached)
                self.assertEqual(row["output_tokens"], 100)
        self.assertEqual(self.store(at="2026-09-28T12:00:00Z")["calculation_state"], "unpriced")

    def test_backfill_is_scoped_idempotent_and_preserves_evidence(self):
        standard = self.store(unavailable=True)
        fast = self.store(tier="fast", unavailable=True, input_tokens=272001, cached_input=271001)
        self.store()
        self.store(at="2026-09-28T12:00:00Z", unavailable=True)
        self.store(model="synthetic-unknown", unavailable=True)
        for capability in ("not-json", "[]", '{"service_tier":"unknown"}'):
            row = self.store(unavailable=True)
            self.connection.execute("UPDATE usage_records SET capability_json = ? WHERE id = ?", (capability, row["id"]))
        aggregate = self.store(unavailable=True, input_tokens=272001, cached_input=271001)
        capability = json.loads(aggregate["capability_json"])
        capability["context_scope"] = "turn_total"
        self.connection.execute("UPDATE usage_records SET capability_json = ? WHERE id = ?", (json.dumps(capability), aggregate["id"]))
        before = {r["id"]: dict(r) for r in self.connection.execute("SELECT * FROM usage_records")}
        self.assertEqual(price_existing_unpriced_sol_6_1_records(self.connection), 2)
        after = {r["id"]: dict(r) for r in self.connection.execute("SELECT * FROM usage_records")}
        changed = {standard["id"]: (STANDARD, "0.001480000000"), fast["id"]: (FAST, "0.119400400000")}
        mutable = {"calculation_state", "estimated_cost_usd", "price_snapshot_id", "calculator_version", "calculated_at"}
        self.assertEqual(before.keys(), after.keys())
        for identity, previous in before.items():
            if identity in changed:
                snapshot, cost = changed[identity]
                self.assertEqual((after[identity]["price_snapshot_id"], after[identity]["estimated_cost_usd"]), (snapshot, cost))
                self.assertEqual(after[identity]["calculation_state"], "priced")
                self.assertEqual({k: v for k, v in previous.items() if k not in mutable},
                                 {k: v for k, v in after[identity].items() if k not in mutable})
            else:
                self.assertEqual(previous, after[identity])
        self.assertEqual(price_existing_unpriced_sol_6_1_records(self.connection), 0)
        self.assertEqual(after, {r["id"]: dict(r) for r in self.connection.execute("SELECT * FROM usage_records")})

    def test_startup_backfills_once_without_overwriting_snapshots(self):
        row = self.store(unavailable=True)
        self.connection.commit()
        data_dir = self.root / "runtime"
        data_dir.mkdir()
        database_path = data_dir / "localbrain.db"
        with sqlite3.connect(database_path) as target:
            self.connection.backup(target)
        settings = Settings(data_dir, database_path, data_dir / "context", data_dir / "claude", data_dir / "codex", 20)
        with patch("localbrain.db.settings", settings):
            init_db()
            with sqlite3.connect(database_path) as connection:
                connection.row_factory = sqlite3.Row
                before = dict(connection.execute("SELECT * FROM usage_records WHERE id = ?", (row["id"],)).fetchone())
                self.assertEqual(before["estimated_cost_usd"], "0.001480000000")
                stamp = connection.execute("SELECT created_at, source_ref FROM usage_price_snapshots WHERE id = ?", (STANDARD,)).fetchone()
                self.assertEqual(stamp["created_at"], "2026-10-02T00:00:00Z")
                self.assertIn("inspected 2026-10-02", stamp["source_ref"])
                connection.execute("UPDATE usage_price_snapshots SET label = 'Retained historical label' WHERE id = ?", (STANDARD,))
            init_db()
            with sqlite3.connect(database_path) as connection:
                connection.row_factory = sqlite3.Row
                after = dict(connection.execute("SELECT * FROM usage_records WHERE id = ?", (row["id"],)).fetchone())
                self.assertEqual(before, after)
                self.assertEqual(connection.execute("SELECT label FROM usage_price_snapshots WHERE id = ?", (STANDARD,)).fetchone()[0], "Retained historical label")

    def test_shared_backfill_keeps_spark_proxy_behavior(self):
        standard = self.store(model="gpt-5.3-codex-spark", unavailable=True)
        fast = self.store(model="gpt-5.3-codex-spark", tier="fast", unavailable=True)
        sol = self.store(unavailable=True)
        self.assertEqual(price_existing_unpriced_spark_records(self.connection), 2)
        for original, cost in ((standard, "0.001890000000"), (fast, "0.003780000000")):
            row = self.connection.execute("SELECT * FROM usage_records WHERE id = ?", (original["id"],)).fetchone()
            self.assertEqual(row["estimated_cost_usd"], cost)
        self.assertEqual(dict(self.connection.execute("SELECT * FROM usage_records WHERE id = ?", (sol["id"],)).fetchone()), sol)
        self.assertEqual(price_existing_unpriced_spark_records(self.connection), 0)


if __name__ == "__main__":
    unittest.main()
