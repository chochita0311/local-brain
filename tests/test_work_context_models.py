"""Two pinned public models, never arbitrary model discovery or replacement."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from localbrain.session_simulation import atomic_json, read_json
from localbrain.work_context import inference_identity
from localbrain.work_context_model import (MODEL_ID, MODEL_8B, OWNER, LocalGenerator,
                                          check_directory, configure_transfer, file_inventory, installation,
                                          model_spec, verify)
from localbrain.work_reconstruction import ExperimentError, digest


class PinnedModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="context-models-test-", dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "model"

    def synthetic_installation(self, model_id):
        spec = model_spec(model_id)
        with installation(self.root, model_id):
            snapshot = self.root / "cache" / spec["revision"]
            snapshot.mkdir(parents=True)
            for name in spec["assets"]:
                (snapshot / name).write_text("synthetic")
            (snapshot / "config.json").write_text(json.dumps({"model_type": "qwen3"}))
            (snapshot / "model.safetensors.index.json").write_text(json.dumps({"weight_map": {
                str(i): name for i, name in enumerate(sorted(spec["assets"])) if name.endswith(".safetensors")}}))
            files = file_inventory(snapshot, self.root, model_id)
            atomic_json(self.root / "model.json", {"owner": OWNER, "model_id": model_id,
                "revision": spec["revision"], "snapshot": str(snapshot.relative_to(self.root)),
                "files": files, "fingerprint": digest(files)})
            return snapshot

    def test_exact_models_and_shard_counts_are_pinned(self):
        for model_id, count in ((MODEL_ID, 3), (MODEL_8B, 5)):
            spec = model_spec(model_id)
            shards = {n for n in spec["assets"] if n.endswith(".safetensors")}
            self.assertEqual(len(shards), count)
            self.assertTrue(shards <= spec["hashes"].keys())
            self.assertEqual(len(spec["revision"]), 40)
            self.assertTrue(all(len(h) == 64 for h in spec["hashes"].values()))
        self.assertNotEqual(model_spec()["revision"], model_spec(MODEL_8B)["revision"])

    def test_transfer_cache_is_explicit_empty_and_bounded(self):
        folder = self.root.parent / "transfer"
        folder.mkdir(mode=0o700)
        with patch.dict(os.environ):
            configure_transfer()
            self.assertEqual(os.environ["HF_HUB_DISABLE_XET"], "1")
            configure_transfer(folder)
            self.assertEqual(os.environ["HF_XET_CACHE"], str(folder))
            self.assertEqual(os.environ["HF_HUB_DISABLE_XET"], "0")
            self.assertEqual(os.environ["HF_XET_CHUNK_CACHE_SIZE_BYTES"], "0")
            self.assertEqual(read_json(folder / "owner.json")["owner"], "localbrain.work-context-transfer.v1")
            with self.assertRaisesRegex(ExperimentError, "UNOWNED_TRANSFER_CACHE"):
                configure_transfer(folder)

    def test_transfer_cannot_silently_use_already_initialized_shared_cache(self):
        with patch.dict(sys.modules, {"huggingface_hub": SimpleNamespace()}), \
             self.assertRaisesRegex(ExperimentError, "TRANSFER_ALREADY_INITIALIZED"):
            configure_transfer()

    def test_unapproved_model_never_creates_directory(self):
        for model_id in ("Qwen/unapproved", "../outside", None):
            with self.assertRaises(ExperimentError):
                with installation(self.root, model_id):
                    self.fail("unapproved model")
        self.assertFalse(self.root.exists())

    def test_explicit_model_mismatch_preserves_existing_owner(self):
        with installation(self.root):
            marker = read_json(self.root / "owner.json")
        with self.assertRaisesRegex(ExperimentError, "MODEL_MISMATCH"):
            with installation(self.root, MODEL_8B):
                self.fail("replaced existing model")
        self.assertEqual(read_json(self.root / "owner.json"), marker)

    def test_8b_auto_verification_and_explicit_mismatch(self):
        with patch("localbrain.work_context_model.PINNED_HASHES_8B", {}):
            self.synthetic_installation(MODEL_8B)
            self.assertEqual(verify(self.root)[1]["model_id"], MODEL_8B)
            self.assertEqual(verify(self.root, MODEL_8B)[1]["revision"], model_spec(MODEL_8B)["revision"])
            with self.assertRaisesRegex(ExperimentError, "MODEL_MISMATCH"):
                verify(self.root, MODEL_ID)

    def test_8b_hash_and_manifest_tampering_are_rejected(self):
        with patch("localbrain.work_context_model.PINNED_HASHES_8B", {}):
            snapshot = self.synthetic_installation(MODEL_8B)
            (snapshot / "tokenizer.json").write_text("changed synthetic")
            with self.assertRaisesRegex(ExperimentError, "MODEL_ASSETS_CHANGED"):
                verify(self.root)
        with self.assertRaisesRegex(ExperimentError, "MODEL_ASSETS_CHANGED"):
            file_inventory(snapshot, self.root, MODEL_8B)

    def test_owner_cannot_switch_to_unknown_or_unpinned_revision(self):
        with installation(self.root, MODEL_8B):
            marker = read_json(self.root / "owner.json")
        for changes in ({"model": "unknown"}, {"revision": "unpinned"}, {"extra": True}):
            atomic_json(self.root / "owner.json", {**marker, **changes})
            with self.assertRaises(ExperimentError):
                check_directory(self.root)

    def test_manifest_must_agree_with_owner_model(self):
        with patch("localbrain.work_context_model.PINNED_HASHES_8B", {}):
            self.synthetic_installation(MODEL_8B)
            manifest = read_json(self.root / "model.json")
            atomic_json(self.root / "model.json", {**manifest, "model_id": MODEL_ID})
            with self.assertRaisesRegex(ExperimentError, "INVALID_MODEL"):
                verify(self.root)

    def test_generator_identity_uses_verified_model_not_default(self):
        torch = SimpleNamespace(__version__="synthetic")
        contracts = []
        for model_id in (MODEL_ID, MODEL_8B):
            spec = model_spec(model_id)
            manifest = {"model_id": model_id, "revision": spec["revision"], "fingerprint": "synthetic"}
            with patch.dict(sys.modules, {"torch": torch, "transformers": SimpleNamespace(__version__="synthetic")}), \
                 patch("localbrain.work_context_model.verify", return_value=(Path("/synthetic"), manifest)), \
                 patch("localbrain.work_context_model.offline_environment"), \
                 patch("localbrain.work_context_model.block_network"):
                generator = LocalGenerator(Path("/synthetic"), device="cpu")
            self.assertEqual(generator.contract["model"], model_id)
            self.assertEqual(generator.contract["revision"], spec["revision"])
            contracts.append(generator.contract)
        self.assertNotEqual(inference_identity(contracts[0]), inference_identity(contracts[1]))


if __name__ == "__main__":
    unittest.main()
