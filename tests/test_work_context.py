"""Offline synthetic safety, evidence and replay contracts. No model download."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localbrain.session_simulation import atomic_json, read_json
from localbrain.work_context import (
    ground, infer, messages_by_id, strict_json, validate_relation, validate_units,
)
from localbrain.work_context_evaluation import evaluate, evaluation_store
from localbrain.work_context_model import ASSETS, REVISION, file_inventory, installation, verify
from localbrain.work_reconstruction import ExperimentError, digest
from work_context_cases import CASES, assess, message


def fact(key="a1", quote="중복 청구"):
    return {"message": key, "quote": quote}


def unit(goal=None):
    return {"goal": goal or fact(), "target": None, "progress": [], "results": [], "remaining": []}


class FakeGenerator:
    contract = {"model": "synthetic-only", "version": 1}
    last_metrics = {"seconds": 0}

    def __init__(self, outputs, fail_after=None):
        self.outputs = outputs
        self.calls = 0
        self.fail_after = fail_after

    def generate(self, system, content):
        if self.calls == self.fail_after:
            raise KeyboardInterrupt()
        value = self.outputs[self.calls % len(self.outputs)]
        self.calls += 1
        return json.dumps(value, ensure_ascii=False)


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.messages = [message("a1", "중복 청구를 막자."), message("a2", "테스트 통과", "assistant")]

    def test_exact_source_offsets_and_original_role(self):
        value = ground(fact("a2", "테스트 통과"), messages_by_id(self.messages))
        self.assertEqual((value["start"], value["end"]), (0, 6))
        self.assertEqual(value["role"], "assistant")
        self.assertEqual(value["authority"], "source-attributed")

    def test_unknown_and_invented_quotes_fail_closed(self):
        for value in (fact("missing"), fact(quote="없는 내용"), fact(quote="")):
            with self.subTest(value=value), self.assertRaises(ExperimentError):
                ground(value, messages_by_id(self.messages))

    def test_ambiguous_quote_is_rejected(self):
        with self.assertRaises(ExperimentError):
            ground(fact(quote="중복"), messages_by_id([message("a1", "중복과 중복")]))

    def test_absent_fields_stay_absent_and_inferred(self):
        result = validate_units({"units": [unit()]}, self.messages)
        self.assertIsNone(result["units"][0]["target"])
        self.assertEqual(result["units"][0]["results"], [])
        self.assertEqual(result["authority"], "inferred")

    def test_duplicate_units_and_evidence_are_rejected(self):
        for values in ({"units": [unit(), unit()]},
                       {"units": [{**unit(), "results": [fact(), fact()]}]}):
            with self.assertRaises(ExperimentError):
                validate_units(values, self.messages)

    def test_no_work_is_valid_empty_output(self):
        self.assertEqual(validate_units({"units": []}, self.messages)["units"], [])

    def test_invalid_json_and_extra_keys_are_rejected(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '[]', '```json\n{}\n```', '{', 'x' * 24001):
            with self.subTest(raw=raw[:40]), self.assertRaises(ExperimentError):
                strict_json(raw)
        with self.assertRaises(ExperimentError):
            validate_units({"units": [], "authority": "confirmed"}, self.messages)

    def test_long_input_and_duplicate_ids_are_not_truncated(self):
        for values in ([message("a1", "a" * 40001)], self.messages + self.messages):
            with self.assertRaises(ExperimentError):
                messages_by_id(values)

    def test_source_tool_and_system_roles_not_admitted(self):
        for role in ("system", "tool"):
            with self.assertRaises(ExperimentError):
                messages_by_id([message("a1", "untrusted", role)])

    def test_continuation_requires_right_link_and_both_sides(self):
        left = [message("a1", "이전 작업")]
        right = [message("b1", "이전 작업 재개")]
        valid = {"relation": "continues", "evidence": [fact("a1", "이전 작업"), fact("b1", "이전 작업 재개")],
                 "link": fact("b1", "재개")}
        self.assertEqual(validate_relation(valid, left, right)["relation"], "continues")
        for changed in ({"link": None}, {"link": fact("a1", "작업")}, {"evidence": [fact("b1", "재개")]}):
            with self.assertRaises(ExperimentError):
                validate_relation({**valid, **changed}, left, right)

    def test_topic_relation_cannot_claim_link(self):
        with self.assertRaises(ExperimentError):
            validate_relation({"relation": "related", "evidence": [], "link": fact()},
                              self.messages[:1], self.messages[1:])

    def test_unknown_relation_can_abstain(self):
        result = validate_relation({"relation": "uncertain", "evidence": [], "link": None},
                                   self.messages[:1], self.messages[1:])
        self.assertEqual(result["authority"], "inferred")

    def test_inference_validates_before_and_after_model(self):
        generator = FakeGenerator([{"units": [unit()]}])
        self.assertEqual(len(infer(generator, "extract", {"messages": self.messages})["units"]), 1)
        with self.assertRaises(ExperimentError):
            infer(generator, "extract", {"messages": []})
        self.assertEqual(generator.calls, 1)

    def test_frozen_cases_have_both_splits_and_negative_controls(self):
        self.assertEqual({c["split"] for c in CASES}, {"development", "holdout"})
        self.assertEqual(len({c["id"] for c in CASES}), len(CASES))
        for case in CASES:
            messages = case["packet"].get("messages") or case["packet"]["left"] + case["packet"]["right"]
            messages_by_id(messages)

    def test_cli_argument_errors_emit_only_fixed_codes(self):
        root = Path(__file__).resolve().parents[1]
        for name in ("install-work-context-model.py", "evaluate-work-context-model.py"):
            result = subprocess.run([sys.executable, "-B", str(root / "scripts" / name),
                                     "--unknown", "synthetic-private-sentinel"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "INVALID_ARGUMENTS\n")
            self.assertEqual(result.stderr, "")


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="work-context-tests-", dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.folder = self.root / "evaluation"
        self.cases = [{"id": "positive", "kind": "extract", "split": "development", "negative": False,
                       "packet": {"messages": [message("a1", "合成")]}},
                      {"id": "negative", "kind": "extract", "split": "development", "negative": True,
                       "packet": {"messages": [message("a1", "合成")]} }]
        self.assess = lambda case, result: {"empty": not result["units"]}

    def run_eval(self, generator=None, **kwargs):
        return evaluate(generator or FakeGenerator([{"units": []}]), self.cases, self.assess,
                        kwargs.get("folder", self.folder))

    def test_unchanged_replay_uses_validated_checkpoint(self):
        self.assertTrue(self.run_eval()["gate_passed"])
        generator = FakeGenerator([])
        result = self.run_eval(generator)
        self.assertEqual(generator.calls, 0)
        self.assertEqual(result["reused"], 2)

    def test_interrupt_resume_keeps_only_committed_cases(self):
        with self.assertRaises(KeyboardInterrupt):
            self.run_eval(FakeGenerator([{"units": []}], fail_after=1))
        self.assertEqual(read_json(self.folder / "progress.json")["state"], "interrupted")
        generator = FakeGenerator([{"units": []}])
        self.assertTrue(self.run_eval(generator)["gate_passed"])
        self.assertEqual(generator.calls, 1)

    def test_changed_model_does_not_reuse_output(self):
        self.run_eval()
        generator = FakeGenerator([{"units": []}])
        generator.contract = {"model": "synthetic-only", "version": 2}
        self.assertEqual(self.run_eval(generator)["reused"], 0)

    def test_invalid_output_fails_gate_and_is_not_reused(self):
        result = self.run_eval(FakeGenerator([{"wrong": []}]))
        self.assertFalse(result["gate_passed"])
        self.assertEqual(result["negative_passed"], 0)
        generator = FakeGenerator([{"units": []}])
        self.assertTrue(self.run_eval(generator)["gate_passed"])
        self.assertEqual(generator.calls, 2)

    def test_cached_role_tampering_causes_recalculation(self):
        output = {"units": [unit({"message": "a1", "quote": "合成"})]}
        self.run_eval(FakeGenerator([output]))
        progress = read_json(self.folder / "progress.json")
        progress["cases"][0]["result"]["units"][0]["goal"]["role"] = "assistant"
        atomic_json(self.folder / "progress.json", progress)
        generator = FakeGenerator([output])
        self.run_eval(generator)
        self.assertEqual(generator.calls, 1)

    def test_expires_and_recalculates_derived_state(self):
        self.run_eval()
        marker = read_json(self.folder / "owner.json")
        atomic_json(self.folder / "owner.json", {**marker, "expires_at": "2020-01-01T00:00:00Z"})
        self.assertEqual(self.run_eval()["reused"], 0)

    def test_unowned_output_and_symlink_are_rejected(self):
        unknown = self.root / "unknown"
        unknown.mkdir(mode=0o700)
        with self.assertRaises(ExperimentError):
            self.run_eval(folder=unknown)
        self.run_eval()
        link = self.root / "link"
        link.symlink_to(self.folder, target_is_directory=True)
        with self.assertRaises(ExperimentError):
            self.run_eval(folder=link)

    def test_writer_lock_blocks_concurrent_evaluation(self):
        with evaluation_store(self.folder), self.assertRaisesRegex(ExperimentError, "EVALUATION_BUSY"):
            self.run_eval()

    def test_gate_failure_preserves_full_case_accounting(self):
        result = self.run_eval(FakeGenerator([{"units": []}, {"units": [unit({"message": "a1", "quote": "合成"})]}]))
        self.assertFalse(result["gate_passed"])
        self.assertEqual(len(result["cases"]), 2)
        self.assertFalse(result["private_corpus_examined"])


class ModelSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="work-model-test-", dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "model"

    def test_unknown_installation_is_not_adopted(self):
        self.root.mkdir(mode=0o700)
        with self.assertRaises(ExperimentError):
            with installation(self.root):
                self.fail("adopted unknown folder")

    def test_installation_lock_is_exclusive(self):
        with installation(self.root), self.assertRaisesRegex(ExperimentError, "MODEL_BUSY"):
            with installation(self.root):
                pass

    def test_asset_inventory_rejects_escape_and_tampering(self):
        with installation(self.root):
            snapshot = self.root / "cache" / REVISION
            snapshot.mkdir(parents=True)
            for name in ASSETS:
                (snapshot / name).write_text("synthetic")
            (snapshot / "config.json").write_text(json.dumps({"model_type": "qwen3"}))
            (snapshot / "model.safetensors.index.json").write_text(json.dumps({
                "weight_map": {str(i): n for i, n in enumerate(sorted(ASSETS)) if n.endswith(".safetensors")}}))
            with patch("localbrain.work_context_model.PINNED_HASHES", {}):
                files = file_inventory(snapshot, self.root)
                from localbrain.work_context_model import MODEL_ID, OWNER
                manifest = {"owner": OWNER, "model_id": MODEL_ID, "revision": REVISION,
                            "snapshot": str(snapshot.relative_to(self.root)), "files": files,
                            "fingerprint": digest(files)}
                atomic_json(self.root / "model.json", manifest)
                verify(self.root)
                (snapshot / "config.json").write_text(json.dumps({"model_type": "qwen3", "changed": True}))
                with self.assertRaisesRegex(ExperimentError, "MODEL_ASSETS_CHANGED"):
                    verify(self.root)
                (snapshot / "LICENSE").unlink()
                (snapshot / "LICENSE").symlink_to(Path(__file__).resolve())
                with self.assertRaisesRegex(ExperimentError, "INVALID_MODEL"):
                    file_inventory(snapshot, self.root)

    def test_offline_guard_blocks_outbound_socket_in_isolated_process(self):
        script = """
import socket
from localbrain.session_simulation_model import block_network
from localbrain.work_reconstruction import ExperimentError
block_network()
try:
    socket.socket().connect(('127.0.0.1', 9))
except ExperimentError as error:
    assert str(error) == 'NETWORK_DISABLED'
else:
    raise AssertionError('network allowed')
"""
        result = subprocess.run([sys.executable, "-B", "-c", script], capture_output=True,
                                env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")})
        self.assertEqual(result.returncode, 0, result.stderr.decode())


if __name__ == "__main__":
    unittest.main()
