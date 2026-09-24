"""Synthetic full-history, replay and invalidation scenarios; no private data."""

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from localbrain.session_simulation import (
    inventory, owned_store, read_json, sha, simulate,
)
from localbrain.session_simulation_model import verified_assets, windows
from localbrain.work_reconstruction import ExperimentError, digest


def seed(path, count=3):
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE sources(id INTEGER PRIMARY KEY,kind TEXT);
            INSERT INTO sources VALUES(1,'synthetic');
            CREATE TABLE sessions(id INTEGER PRIMARY KEY,source_id INTEGER,external_id TEXT,
                title TEXT,session_class TEXT,session_role TEXT,index_policy TEXT);
            CREATE TABLE activity_events(id TEXT PRIMARY KEY,session_id INTEGER,sequence INTEGER,
                occurred_at TEXT,event_type TEXT,role TEXT,text TEXT);
        """)
        for index in range(count):
            db.execute("INSERT INTO sessions VALUES (?,1,?,?,'work','primary','full')",
                       (index + 1, "synthetic-{}".format(index), "합성 업무 {}".format(index)))
            db.execute("INSERT INTO activity_events VALUES (?,?,1,?,'message','user',?)",
                       ("event-{}".format(index), index + 1, "2026-01-01T00:00:00Z", "합성 데이터 품질을 검증합니다. {}".format(index)))


class Encoder:
    contract = {"model_id": "synthetic-test-only", "dimension": 3, "version": 1}

    def __init__(self, fail_after=None, mutate=None):
        self.calls, self.texts = 0, []
        self.fail_after, self.mutate = fail_after, mutate

    def encode(self, texts):
        if self.fail_after is not None and self.calls >= self.fail_after:
            raise KeyboardInterrupt()
        self.calls += 1
        self.texts.extend(texts)
        if self.mutate:
            self.mutate()
            self.mutate = None
        return [[1.0, (int(sha(text)[:4], 16) % 7) / 10, 0.2] for text in texts]


def grouping(vectors, parameters):
    return {"engine": "synthetic-test-only", "members": sorted(vectors), "parameters": parameters}


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="localbrain-simulation-test-", dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.database, self.output = self.root / "source.db", self.root / "simulation"
        seed(self.database)

    def run_sim(self, encoder=None, **kwargs):
        return simulate(self.database, self.output, encoder or Encoder(), grouper=grouping, **kwargs)

    def edit(self, sql, parameters=()):
        with sqlite3.connect(self.database) as db:
            db.execute(sql, parameters)

    def test_full_population_messages_long_tails_and_unknown_dates(self):
        self.database.unlink()
        seed(self.database, 75)
        for index in range(40):
            self.edit("INSERT INTO activity_events VALUES (?,1,?,NULL,'message','assistant',?)",
                      ("extra-{}".format(index), index + 2, "분석 결과 " * 800 + "마지막 근거"))
        expected = sqlite3.connect(self.database)
        chars = expected.execute("SELECT sum(length(text)) FROM activity_events").fetchone()[0]
        expected.close()
        report = self.run_sim()
        coverage = report["manifest"]["coverage"]
        self.assertEqual(coverage["total_sessions"], 75)
        self.assertEqual(coverage["eligible_sessions"], 75)
        self.assertEqual(coverage["message_events"], 115)
        self.assertEqual(coverage["unknown_date_events"], 40)
        self.assertEqual(coverage["admitted_characters"], chars)
        self.assertEqual(sum(c["end"] - c["start"] for c in report["chunks"]), chars)
        self.assertFalse(report["manifest"]["sampled"])

    def test_replay_reuses_all_and_preserves_source_bytes(self):
        before = self.database.read_bytes()
        first = self.run_sim()
        encoder = Encoder()
        second = self.run_sim(encoder)
        self.assertEqual(encoder.calls, 0)
        self.assertEqual(second["cache"]["reused"], first["cache"]["total"])
        self.assertTrue(second["comparison"]["same_grouping"])
        self.assertTrue(second["comparison"]["same_configuration"])
        self.assertEqual(self.database.read_bytes(), before)

    def test_read_ahead_boundary_preserves_every_character_and_old_fingerprint(self):
        text = "합성 경계 검증 " * 18000 + "마지막 근거"
        self.edit("UPDATE activity_events SET text=? WHERE id='event-0'", (text,))
        chunks = []
        manifest = inventory(self.database, 1800,
                             lambda kind, value: chunks.append(value) if kind == 'chunk' and value['event_id'] == 'event-0' else None)
        self.assertEqual(sum(c['end'] - c['start'] for c in chunks), len(text))
        for chunk in chunks:
            self.assertEqual(chunk['content_hash'], sha(text[chunk['start']:chunk['end']]))
        self.assertEqual(manifest['coverage']['chunks'], len(chunks) + 2)

    def test_changed_record_reencodes_only_affected_input(self):
        self.run_sim()
        self.edit("UPDATE activity_events SET text='변경된 합성 근거' WHERE id='event-1'")
        encoder = Encoder()
        result = self.run_sim(encoder)
        self.assertEqual(len(encoder.texts), 1)
        self.assertEqual(result["cache"]["reused"], 2)
        self.assertFalse(result["comparison"]["same_input"])

    def test_deleted_and_revoked_inputs_are_removed_from_current_cache(self):
        first = self.run_sim()
        self.edit("DELETE FROM activity_events WHERE session_id=1")
        self.edit("UPDATE sessions SET index_policy='metadata_only' WHERE id=2")
        result = self.run_sim()
        self.assertEqual(result["cache"]["total"], 1)
        self.assertEqual(result["cache"]["encoded"], 0)
        self.assertEqual(result["manifest"]["coverage"]["sessions_without_text"], 1)
        self.assertEqual(result["manifest"]["coverage"]["excluded-metadata-only_sessions"], 1)
        with sqlite3.connect(self.output / "state.sqlite3") as state:
            self.assertEqual(state.execute("SELECT count(*) FROM embeddings").fetchone()[0], 1)
        self.assertNotEqual(first["manifest"], result["manifest"])

    def test_interrupted_batch_resumes(self):
        with self.assertRaises(KeyboardInterrupt):
            self.run_sim(Encoder(fail_after=1), batch_size=1)
        self.assertEqual(read_json(self.output / "progress.json")["state"], "interrupted")
        result = self.run_sim()
        self.assertEqual(result["cache"], {"reused": 1, "encoded": 2, "total": 3})

    def test_grouping_only_change_does_not_reembed(self):
        self.run_sim()
        encoder = Encoder()
        result = self.run_sim(encoder, parameters={"synthetic_resolution": 2})
        self.assertEqual(encoder.calls, 0)
        self.assertTrue(result["comparison"]["same_input"])
        self.assertFalse(result["comparison"]["same_configuration"])

    def test_model_change_uses_separate_namespace(self):
        self.run_sim()
        encoder = Encoder()
        encoder.contract = {**encoder.contract, "version": 2}
        result = self.run_sim(encoder)
        self.assertEqual(result["cache"]["reused"], 0)
        self.assertEqual(result["cache"]["encoded"], 3)

    def test_forced_recalculation_and_corrupt_cache_repair(self):
        self.run_sim()
        self.assertEqual(self.run_sim(force=True)["cache"]["encoded"], 3)
        with sqlite3.connect(self.output / "state.sqlite3") as db:
            db.execute("UPDATE embeddings SET vector=x'00' WHERE input_hash=(SELECT min(input_hash) FROM embeddings)")
        self.assertEqual(self.run_sim()["cache"]["encoded"], 1)

    def test_source_changes_during_encoding_do_not_publish(self):
        self.run_sim()
        old = (self.output / "report.json").read_bytes()
        self.edit("INSERT INTO activity_events VALUES ('new',1,2,NULL,'message','user','new evidence')")
        encoder = Encoder(mutate=lambda: self.edit("UPDATE activity_events SET text='changed during inference' WHERE id='new'"))
        with self.assertRaisesRegex(ExperimentError, "SOURCE_CHANGED"):
            self.run_sim(encoder)
        self.assertEqual((self.output / "report.json").read_bytes(), old)
        self.assertEqual(read_json(self.output / "progress.json")["state"], "failed")

    def test_exclusions_do_not_read_bodies_and_empty_sessions_are_counted(self):
        self.edit("UPDATE sessions SET session_class='maintenance' WHERE id=1")
        self.edit("UPDATE sessions SET session_role='subsession' WHERE id=2")
        self.edit("DELETE FROM activity_events WHERE session_id=3")
        result = self.run_sim()
        self.assertEqual(result["chunks"], [])
        self.assertEqual(result["manifest"]["coverage"]["total_sessions"], 3)
        self.assertEqual(result["manifest"]["coverage"]["sessions_without_text"], 1)

    def test_orphan_session_is_accounted_without_body_read(self):
        self.edit("UPDATE sessions SET source_id=999 WHERE id=1")
        report = self.run_sim()
        self.assertEqual(report["manifest"]["coverage"]["total_sessions"], 3)
        self.assertEqual(report["manifest"]["coverage"]["excluded-missing-source_sessions"], 1)
        self.assertEqual(report["cache"]["total"], 2)

    def test_input_manifest_changes_on_title_or_role(self):
        original = inventory(self.database, 1800)
        self.edit("UPDATE sessions SET title='다른 합성 업무' WHERE id=1")
        self.assertNotEqual(original, inventory(self.database, 1800))
        first = self.run_sim()
        self.edit("UPDATE activity_events SET role='assistant' WHERE session_id=1")
        second = self.run_sim()
        self.assertEqual(second["cache"]["encoded"], 1)
        self.assertNotEqual(first["manifest"], second["manifest"])

    def test_unknown_output_and_symlinks_are_refused(self):
        self.output.mkdir(mode=0o700)
        with self.assertRaises(ExperimentError):
            self.run_sim()
        self.output.rmdir()
        self.run_sim()
        (self.output / "state.sqlite3").unlink()
        (self.output / "state.sqlite3").symlink_to(self.database)
        with self.assertRaises(ExperimentError):
            self.run_sim()

    def test_wrong_database_binding_and_concurrent_writer_fail(self):
        self.run_sim()
        other = self.root / "other.db"
        seed(other)
        with self.assertRaises(ExperimentError):
            with owned_store(self.output, other):
                pass
        with owned_store(self.output, self.database):
            with self.assertRaisesRegex(ExperimentError, "SIMULATION_BUSY"):
                self.run_sim()

    def test_expiry_purge_and_original_preservation(self):
        self.run_sim()
        marker = read_json(self.output / "owner.json")
        marker["expires_at"] = "2000-01-01T00:00:00Z"
        (self.output / "owner.json").write_text(json.dumps(marker))
        self.assertEqual(self.run_sim()["cache"]["reused"], 0)
        original = self.database.read_bytes()
        with owned_store(self.output, self.database, purge=True):
            pass
        self.assertEqual({p.name for p in self.output.iterdir()}, {"owner.json", "writer.lock"})
        self.assertEqual(self.database.read_bytes(), original)

    def test_exhaustive_token_windows(self):
        class Tokenizer:
            def encode(self, text, **kwargs):
                return [0] * (len(text) + 2)
        text = "합성 긴 메시지 " * 900 + "최종 근거"
        result = list(windows(text, Tokenizer(), 128))
        self.assertEqual("".join(part for part, _ in result), text)
        self.assertTrue(all(weight <= 128 for _, weight in result))

    def test_cli_inventory_and_status_disclose_only_fixed_codes(self):
        script = Path(__file__).resolve().parents[1] / "scripts/simulate-work-sessions.py"
        command = [sys.executable, "-B", str(script), "--database", str(self.database), "--output", str(self.output)]
        before = self.database.read_bytes()
        result = subprocess.run(command + ["--inventory-only"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, "SIMULATION_PREPARED\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(subprocess.run(command + ["--status"], capture_output=True, text=True).stdout, "SIMULATION_PREPARED\n")
        self.assertEqual(subprocess.run(command, capture_output=True, text=True).stdout, "EXPLICIT_MODEL_REQUIRED\n")
        self.assertEqual(self.database.read_bytes(), before)

    def test_cli_detects_abandoned_progress_and_stale_complete_output(self):
        self.run_sim()
        script = Path(__file__).resolve().parents[1] / "scripts/simulate-work-sessions.py"
        command = [sys.executable, "-B", str(script), "--database", str(self.database), "--output", str(self.output), "--status"]
        self.assertEqual(subprocess.run(command, capture_output=True, text=True).stdout, "SIMULATION_COMPLETE\n")
        self.edit("UPDATE activity_events SET text='새 합성 내용' WHERE id='event-1'")
        self.assertEqual(subprocess.run(command, capture_output=True, text=True).stdout, "SOURCE_CHANGED\n")
        progress = read_json(self.output / "progress.json")
        progress["state"] = "embedding"
        (self.output / "progress.json").write_text(json.dumps(progress))
        self.assertEqual(subprocess.run(command, capture_output=True, text=True).stdout, "SIMULATION_INTERRUPTED\n")

    def test_asset_fingerprint_rejects_tampering(self):
        import hashlib
        root = self.root / "semantic"
        snapshot = root / "models" / "synthetic" / "snapshot"
        snapshot.mkdir(parents=True)
        files = []
        for name in ("config.json", "model.safetensors", "tokenizer.json"):
            content = "synthetic-asset-" + name
            (snapshot / name).write_text(content)
            files.append({"path": name, "size": len(content), "sha256": sha(content)})
        fingerprint = hashlib.sha256((json.dumps(files, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()).hexdigest()
        manifest = snapshot.parent / "model.json"
        manifest.write_text(json.dumps({"schema": "foundry.semantic-model/v1", "snapshot": "models/synthetic/snapshot",
                                       "files": files, "fingerprint": fingerprint, "model_id": "synthetic",
                                       "resolved_revision": "synthetic-revision"}))
        self.assertEqual(verified_assets(manifest)[0], snapshot)
        (snapshot / "model.safetensors").write_text("tampered")
        with self.assertRaisesRegex(ExperimentError, "MODEL_ASSETS_CHANGED"):
            verified_assets(manifest)

    @unittest.skipUnless(all(importlib.util.find_spec(m) for m in ("numpy", "sklearn", "networkx")), "optional semantic runtime")
    def test_actual_graph_determinism_and_two_resolutions(self):
        from localbrain.session_simulation_graph import group_vectors
        vectors = {"a": [1., 0., 0.], "b": [0.99, 0.01, 0.], "c": [0., 1., 0.], "d": [0., 0.99, 0.01]}
        params = {"neighbors": 2, "similarity": 0.8, "area_resolution": 0.6, "work_resolution": 1.2, "seed": 0}
        first = group_vectors(vectors, params)
        self.assertEqual(first, group_vectors(dict(reversed(list(vectors.items()))), params))
        self.assertEqual(sorted(a["members"] for a in first["areas"]), [["a", "b"], ["c", "d"]])
        self.assertEqual(first["authority"], "inferred-affinity-only")
        self.assertEqual(group_vectors({}, params)["node_count"], 0)

    @unittest.skipUnless(all(importlib.util.find_spec(m) for m in ("numpy", "sklearn", "networkx")), "optional semantic runtime")
    def test_graph_is_identical_across_process_hash_seeds(self):
        code = """
import json, random
from localbrain.session_simulation_graph import group_vectors
from localbrain.work_reconstruction import digest
rng = random.Random(17)
vectors = {'node-'+str(i): [float(i//20 == j) + rng.random()*0.4 for j in range(5)] for i in range(100)}
params = {'neighbors': 8, 'similarity': 0.6, 'area_resolution': 0.6, 'work_resolution': 1.2, 'seed': 0}
print(digest(group_vectors(vectors, params)))
"""
        outputs = []
        for seed_value in ("1", "2", "97"):
            result = subprocess.run([sys.executable, "-B", "-c", code],
                                    env={**os.environ, "PYTHONHASHSEED": seed_value},
                                    capture_output=True, text=True, check=True)
            outputs.append(result.stdout)
        self.assertEqual(len(set(outputs)), 1)

    @unittest.skipUnless(all(importlib.util.find_spec(m) for m in ("numpy", "sklearn", "networkx")), "optional semantic runtime")
    def test_nonfinite_neighbor_distance_fails_closed(self):
        import numpy as np
        from unittest.mock import patch
        from localbrain.session_simulation_graph import group_vectors
        params = {"neighbors": 1, "similarity": 0.65, "area_resolution": 0.6,
                  "work_resolution": 1.2, "seed": 0}
        with patch('sklearn.neighbors.NearestNeighbors.kneighbors',
                   return_value=(np.array([[0., np.nan], [0., 1.]]), np.array([[0, 1], [1, 0]]))):
            with self.assertRaisesRegex(ExperimentError, 'INVALID_SIMILARITY'):
                group_vectors({'a': [1., 0.], 'b': [0., 1.]}, params)


if __name__ == "__main__":
    unittest.main()
