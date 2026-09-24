"""Verified existing model assets, exhaustive token windows, offline inference."""

import hashlib
import json
import os
import platform
import socket
import sys
from pathlib import Path

from .work_reconstruction import require


def offline_environment():
    for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "DO_NOT_TRACK"):
        os.environ[name] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"


def block_network():
    """Defense in depth for Python clients, not an OS-level network sandbox."""
    original = socket.socket.connect
    original_ex = socket.socket.connect_ex
    original_send = socket.socket.sendto

    def connect(instance, address):
        require(instance.family not in (socket.AF_INET, socket.AF_INET6), "NETWORK_DISABLED")
        return original(instance, address)

    def connect_ex(instance, address):
        require(instance.family not in (socket.AF_INET, socket.AF_INET6), "NETWORK_DISABLED")
        return original_ex(instance, address)

    def sendto(instance, *args):
        require(instance.family not in (socket.AF_INET, socket.AF_INET6), "NETWORK_DISABLED")
        return original_send(instance, *args)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.socket.sendto = sendto


def verified_assets(manifest_path):
    path = Path(manifest_path)
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), "INVALID_MODEL")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(value.get("schema") == "foundry.semantic-model/v1", "INVALID_MODEL")
    root = path.parent.parent.parent.resolve()
    snapshot = (root / value["snapshot"]).resolve()
    require(root in snapshot.parents and snapshot.is_dir(), "INVALID_MODEL")
    files = []
    for item in sorted(snapshot.rglob("*")):
        if not item.is_file():
            continue
        require(root in item.resolve().parents, "INVALID_MODEL")
        hasher = hashlib.sha256()
        with item.open("rb") as handle:
            for part in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(part)
        files.append({"path": item.relative_to(snapshot).as_posix(), "size": item.stat().st_size,
                      "sha256": hasher.hexdigest()})
    fingerprint = hashlib.sha256((json.dumps(files, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()).hexdigest()
    require(files == value["files"] and fingerprint == value["fingerprint"], "MODEL_ASSETS_CHANGED")
    require(all((snapshot / name).is_file() for name in ("config.json", "tokenizer.json", "model.safetensors")), "INVALID_MODEL")
    return snapshot, {k: value[k] for k in ("model_id", "resolved_revision", "fingerprint")}


def windows(text, tokenizer, max_tokens):
    """Split original characters until every encoded window fits, losing no tail."""
    tokens = tokenizer.encode(text, add_special_tokens=True, truncation=False, verbose=False)
    if len(tokens) <= max_tokens:
        yield text, max(1, len(tokens))
    else:
        require(len(text) > 1, "TOKEN_WINDOW_UNAVAILABLE")
        middle = len(text) // 2
        yield from windows(text[:middle], tokenizer, max_tokens)
        yield from windows(text[middle:], tokenizer, max_tokens)


class LocalEncoder:
    def __init__(self, manifest, *, device="auto", dimension=512, max_tokens=1024, batch_size=4):
        offline_environment()
        snapshot, identity = verified_assets(manifest)
        import sentence_transformers
        import torch
        import transformers

        require(device in {"auto", "cpu", "mps", "cuda"}, "INVALID_DEVICE")
        require(32 <= dimension <= 1024 and 128 <= max_tokens <= 8192 and 1 <= batch_size <= 64, "INVALID_MODEL_CONFIG")
        if device == "auto":
            device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
        self.contract = {**identity, "dimension": dimension, "max_tokens": max_tokens,
                         "token_windows": "exhaustive-character-bisection.v1", "device": device,
                         "runtime": {"python": platform.python_version(), "byteorder": sys.byteorder,
                                     "sentence_transformers": sentence_transformers.__version__,
                                     "torch": torch.__version__, "transformers": transformers.__version__}}
        self.dimension, self.max_tokens, self.batch_size = dimension, max_tokens, batch_size
        self.snapshot, self.device, self.model = snapshot, device, None

    def _load(self):
        if self.model is not None:
            return
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(
            str(self.snapshot), device=self.device, local_files_only=True, trust_remote_code=False,
            truncate_dim=self.dimension, token=False,
            model_kwargs={"use_safetensors": True})
        self.model.max_seq_length = self.max_tokens
        self.model.default_prompt_name = None
        self.model.eval()

    def encode(self, texts):
        import numpy as np

        self._load()
        values = [np.zeros(self.dimension, dtype=np.float64) for _ in texts]
        pending, owners = [], []

        def flush():
            if not pending:
                return
            encoded = self.model.encode(pending, batch_size=self.batch_size, prompt="",
                                        convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
            for vector, (index, weight) in zip(encoded, owners):
                values[index] += vector * weight
            pending.clear()
            owners.clear()

        for index, text in enumerate(texts):
            for part, weight in windows(text, self.model.tokenizer, self.max_tokens):
                pending.append(part)
                owners.append((index, weight))
                if len(pending) >= self.batch_size:
                    flush()
        flush()
        return [value.tolist() for value in values]
