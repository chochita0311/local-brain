"""Explicit public installation and separate verified offline text inference."""

import fcntl
import hashlib
import json
import os
import platform
import stat
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from .session_simulation import atomic_json, now, read_json
from .session_simulation_model import block_network, offline_environment
from .work_reconstruction import ExperimentError, digest, require

MODEL_ID = "Qwen/Qwen3-4B"
REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"
OWNER = "localbrain.work-context-model.v1"
ASSETS = {
    "LICENSE", "config.json", "generation_config.json", "tokenizer.json",
    "tokenizer_config.json", "vocab.json", "merges.txt",
    "model.safetensors.index.json", "model-00001-of-00003.safetensors",
    "model-00002-of-00003.safetensors", "model-00003-of-00003.safetensors",
}
PINNED_HASHES = {
    "model-00001-of-00003.safetensors": "328a91d3122359d5547f9d79521205bc0a46e1f79a792dfe650e99fc2d651223",
    "model-00002-of-00003.safetensors": "6cd087b316306a68c562436b5492edbcf6e16c6dba3a1308279caa5a58e21ca5",
    "model-00003-of-00003.safetensors": "e4bf436957184f4eeb86a80e9db394503f1f56446b2e6b7edeac5b81470f4ca1",
    "tokenizer.json": "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4",
}
MODEL_8B = "Qwen/Qwen3-8B"
REVISION_8B = "b968826d9c46dd6066d109eabc6255188de91218"
PINNED_HASHES_8B = {
    "model-00001-of-00005.safetensors": "31d6a825ae35f11fb85b195b4c42c146c051e446433125a215336abdf95cbf5f",
    "model-00002-of-00005.safetensors": "5991236cea6fe21f3d43cab0f0e84448734fbbe0789816202989f2ddc9d18282",
    "model-00003-of-00005.safetensors": "c5185c4794be2d8a9784d5753c9922db38df478ce11f9ed0b415b7304d896836",
    "model-00004-of-00005.safetensors": "b5ee7de71fbf17db3d5704e0c8f2bc7d005ca9e1d7ca2aeb19827b0cfcaa917a",
    "model-00005-of-00005.safetensors": "20c2d6366ab85c90786ccdd829cd2b9e7d30ef3b2ebbb998280e7e4014b542ff",
    "tokenizer.json": "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4",
}
MODEL_IDS = (MODEL_ID, MODEL_8B)
ASSETS_8B = {name for name in ASSETS if not name.endswith(".safetensors")} | {
    "model-%05d-of-00005.safetensors" % i for i in range(1, 6)}


def model_spec(model_id=MODEL_ID):
    require(isinstance(model_id, str) and model_id in MODEL_IDS, "INVALID_MODEL")
    if model_id == MODEL_8B:
        return {"id": MODEL_8B, "revision": REVISION_8B,
                "assets": ASSETS_8B, "hashes": PINNED_HASHES_8B}
    return {"id": MODEL_ID, "revision": REVISION, "assets": ASSETS, "hashes": PINNED_HASHES}


def safe_root(root):
    root = Path(root)
    repo = Path(__file__).resolve().parents[2]
    require(root.is_absolute() and root == root.resolve() and root != repo
            and repo not in root.parents and root not in repo.parents, "INVALID_MODEL_ROOT")
    require(root.parent.is_dir(), "INVALID_MODEL_ROOT")
    return root


def check_directory(root, model_id=None):
    info = root.stat()
    require(not root.is_symlink() and stat.S_ISDIR(info.st_mode)
            and info.st_uid == os.getuid() and not info.st_mode & 0o077, "UNOWNED_MODEL")
    marker = read_json(root / "owner.json")
    require(isinstance(marker, dict) and marker.get("model") in MODEL_IDS, "UNOWNED_MODEL")
    spec = model_spec(marker["model"])
    require(marker == {"owner": OWNER, "model": spec["id"], "revision": spec["revision"]}, "UNOWNED_MODEL")
    require(model_id is None or model_id == spec["id"], "MODEL_MISMATCH")
    require({p.name for p in root.iterdir()} <= {
        "owner.json", "install.lock", "cache", "model.json", "model.json.pending"
    }, "UNOWNED_MODEL")
    return spec


@contextmanager
def installation(root, model_id=MODEL_ID):
    spec = model_spec(model_id)
    root = safe_root(root)
    if not root.exists():
        root.mkdir(mode=0o700)
        atomic_json(root / "owner.json", {"owner": OWNER, "model": spec["id"], "revision": spec["revision"]})
    check_directory(root, model_id)
    lock = root / "install.lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        require(os.fstat(fd).st_nlink == 1, "UNOWNED_MODEL")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ExperimentError("MODEL_BUSY") from None
        pending = root / "model.json.pending"
        if pending.exists() or pending.is_symlink():
            require(not pending.is_symlink() and pending.is_file()
                    and pending.stat().st_nlink == 1 and pending.stat().st_uid == os.getuid(), "UNOWNED_MODEL")
            pending.unlink()
        yield root
    finally:
        os.close(fd)


def file_inventory(snapshot, root, model_id=MODEL_ID):
    spec = model_spec(model_id)
    require(snapshot.is_dir() and root in snapshot.resolve().parents, "INVALID_MODEL")
    require({p.name for p in snapshot.iterdir()} == spec["assets"], "INVALID_MODEL")
    files = []
    for name in sorted(spec["assets"]):
        path = snapshot / name
        require(path.is_file() and root in path.resolve().parents, "INVALID_MODEL")
        hasher = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
        sha = hasher.hexdigest()
        require(name not in spec["hashes"] or spec["hashes"][name] == sha, "MODEL_ASSETS_CHANGED")
        files.append({"path": name, "size": path.stat().st_size, "sha256": sha})
    config = json.loads((snapshot / "config.json").read_text())
    require(config.get("model_type") == "qwen3" and "auto_map" not in config, "INVALID_MODEL")
    index = json.loads((snapshot / "model.safetensors.index.json").read_text())
    require(set(index.get("weight_map", {}).values()) == {
        name for name in spec["assets"] if name.endswith(".safetensors")}, "INVALID_MODEL")
    return files


def configure_transfer(transfer_cache=None):
    """Xet is opt-in and never writes its diagnostics into the shared cache."""
    require("huggingface_hub" not in sys.modules and "hf_xet" not in sys.modules,
            "TRANSFER_ALREADY_INITIALIZED")
    if transfer_cache is None:
        os.environ["HF_HUB_DISABLE_XET"] = "1"
        return
    folder = safe_root(transfer_cache)
    info = folder.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and not info.st_mode & 0o077 and not any(folder.iterdir()), "UNOWNED_TRANSFER_CACHE")
    atomic_json(folder / "owner.json", {"owner": "localbrain.work-context-transfer.v1"})
    os.environ["HF_HUB_DISABLE_XET"] = "0"
    os.environ["HF_XET_CACHE"] = str(folder)
    os.environ["HF_XET_CHUNK_CACHE_SIZE_BYTES"] = "0"
    os.environ["HF_XET_SHARD_CACHE_SIZE_LIMIT"] = "0"


def install(root, model_id=MODEL_ID, *, transfer_cache=None):
    """Only public model assets; no database, private packet or source argument."""
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    spec = model_spec(model_id)
    with installation(root, model_id) as root:
        if (root / "model.json").exists():
            return verify(root, model_id)[1]
        cache = root / "cache"
        require(not cache.is_symlink(), "UNOWNED_MODEL")
        cache.mkdir(mode=0o700, exist_ok=True)
        # All cache entries are installation-owned, but reject pre-planted escapes.
        for path in cache.rglob("*"):
            require(root in path.resolve().parents, "UNOWNED_MODEL")
        configure_transfer(transfer_cache)
        from huggingface_hub import snapshot_download
        snapshot = Path(snapshot_download(repo_id=spec["id"], revision=spec["revision"],
                        cache_dir=cache, allow_patterns=sorted(spec["assets"]),
                        endpoint="https://huggingface.co", token=False, max_workers=3)).resolve()
        require(snapshot.name == spec["revision"], "INVALID_MODEL")
        files = file_inventory(snapshot, root, model_id)
        manifest = {"owner": OWNER, "model_id": spec["id"], "revision": spec["revision"],
                    "snapshot": str(snapshot.relative_to(root)), "files": files,
                    "fingerprint": digest(files), "installed_at": now().isoformat()}
        atomic_json(root / "model.json", manifest)
        return manifest


def verify(root, model_id=None):
    root = safe_root(root)
    spec = check_directory(root, model_id)
    manifest = read_json(root / "model.json")
    require(manifest.get("owner") == OWNER and manifest.get("model_id") == spec["id"]
            and manifest.get("revision") == spec["revision"], "INVALID_MODEL")
    snapshot = (root / manifest["snapshot"]).resolve()
    require(snapshot.name == spec["revision"] and root in snapshot.parents, "INVALID_MODEL")
    files = file_inventory(snapshot, root, spec["id"])
    require(files == manifest.get("files") and digest(files) == manifest.get("fingerprint"),
            "MODEL_ASSETS_CHANGED")
    return snapshot, manifest


def final_token_ids(tokens, *, thinking, eos):
    """Parse the pinned Qwen protocol without decoding or retaining reasoning."""
    require(tokens and tokens[-1] in eos, "OUTPUT_TRUNCATED")
    if thinking:
        require(tokens.count(151668) == 1, "INVALID_THINKING_PROTOCOL")
        boundary = tokens.index(151668) + 1
        require(boundary < len(tokens) - 1, "INVALID_THINKING_PROTOCOL")
        return tokens[boundary:], boundary
    require(151668 not in tokens and 151667 not in tokens, "INVALID_THINKING_PROTOCOL")
    return tokens, 0


def generation_settings(*, thinking=False, decoding="greedy", max_tokens=None, max_output=None,
                        max_seconds=180):
    require(type(thinking) is bool and decoding in {"greedy", "sampled"}
            and (not thinking or decoding == "sampled"), "INVALID_MODEL_CONFIG")
    token_bound, output_bound = (16384, 8192) if thinking else (8192, 2048)
    max_tokens = token_bound if max_tokens is None else max_tokens
    max_output = output_bound if max_output is None else max_output
    require(type(max_tokens) is int and type(max_output) is int
            and 1024 <= max_tokens <= token_bound and 128 <= max_output <= output_bound
            and max_output < max_tokens and type(max_seconds) is int
            and 1 <= max_seconds <= 180, "INVALID_MODEL_CONFIG")
    return {"thinking": thinking, "decoding": decoding,
            "sampling": None if decoding == "greedy" else {
                "temperature": 0.6 if thinking else 0.7,
                "top_p": 0.95 if thinking else 0.8, "top_k": 20,
                "seed": "sha256-system-and-content-prefix32"},
            "max_tokens": max_tokens, "max_output": max_output, "max_seconds": max_seconds,
            "output_protocol": "qwen-final-only.v1"}


class LocalGenerator:
    def __init__(self, root, *, device="auto", max_tokens=None, max_output=None,
                 decoding="greedy", thinking=False, max_seconds=180):
        settings = generation_settings(thinking=thinking, decoding=decoding,
                                       max_tokens=max_tokens, max_output=max_output,
                                       max_seconds=max_seconds)
        require(device in {"auto", "mps", "cpu", "cuda"}, "INVALID_DEVICE")
        offline_environment()
        block_network()
        snapshot, manifest = verify(root)
        import torch
        import transformers
        if device == "auto":
            device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
        self.contract = {"model": manifest["model_id"], "revision": manifest["revision"],
                         "fingerprint": manifest["fingerprint"], "device": device,
                         "dtype": "float32" if device == "cpu" else "bfloat16",
                         # Fused MPS decoding produced invalid probabilities in the trial.
                         "attention": "eager" if device == "mps" else "sdpa",
                         **settings,
                         "python": platform.python_version(),
                         "torch": torch.__version__, "transformers": transformers.__version__}
        self.snapshot, self.model, self.tokenizer = snapshot, None, None
        self.last_metrics = {}
        self.last_output = ""

    def _load(self):
        if self.model is not None:
            return
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.snapshot), local_files_only=True,
                                                      trust_remote_code=False, token=False)
        require(self.tokenizer.convert_tokens_to_ids("</think>") == 151668
                and self.tokenizer.convert_tokens_to_ids("<think>") == 151667, "INVALID_MODEL")
        dtype = torch.float32 if self.contract["device"] == "cpu" else torch.bfloat16
        self.model = AutoModelForCausalLM.from_pretrained(str(self.snapshot), local_files_only=True,
                        trust_remote_code=False, token=False, use_safetensors=True,
                        torch_dtype=dtype, attn_implementation=self.contract["attention"]).to(self.contract["device"])
        self.model.eval()
        self.model.generation_config.temperature = None
        self.model.generation_config.top_p = None
        self.model.generation_config.top_k = None

    def describe_prompt(self, system, content, codes):
        """Audit the actual rendering/tokenization without disclosing prompt text."""
        self._load()
        prompt = self.tokenizer.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": content}],
            tokenize=False, add_generation_prompt=True, enable_thinking=self.contract["thinking"])
        return {"prompt_sha256": digest(prompt),
                "template_sha256": digest(self.tokenizer.chat_template),
                "input_tokens": len(self.tokenizer.encode(prompt)),
                "answer_token_ids": {code: self.tokenizer.encode(code, add_special_tokens=False)
                                     for code in codes}}

    def generate(self, system, content):
        import resource
        import torch
        started = time.monotonic()
        self.last_output, self.last_metrics = "", {}
        self._load()
        messages = [{"role": "system", "content": system}, {"role": "user", "content": content}]
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False,
                    add_generation_prompt=True, enable_thinking=self.contract["thinking"])
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=False)
        length = inputs["input_ids"].shape[1]
        require(length + self.contract["max_output"] <= self.contract["max_tokens"], "CONTEXT_TOO_LARGE")
        inputs = inputs.to(self.contract["device"])
        options = {"do_sample": False}
        if self.contract["decoding"] == "sampled":
            torch.manual_seed(int(digest([system, content])[:8], 16))
            options = {"do_sample": True, **{key: self.contract["sampling"][key]
                                            for key in ("temperature", "top_p", "top_k")}}
        with torch.inference_mode():
            generated = self.model.generate(**inputs, **options,
                            max_new_tokens=self.contract["max_output"],
                            max_time=self.contract["max_seconds"],
                            pad_token_id=self.tokenizer.eos_token_id)
        tokens = generated[0][length:]
        eos = self.model.generation_config.eos_token_id
        eos = {eos} if isinstance(eos, int) else set(eos or [])
        self.last_metrics = {"seconds": round(time.monotonic() - started, 3),
                             "input_tokens": length, "output_tokens": len(tokens),
                             "max_rss_native": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                             "rss_unit": "bytes" if platform.system() == "Darwin" else "KiB"}
        if self.contract["device"] == "mps":
            self.last_metrics["mps_driver_bytes"] = torch.mps.driver_allocated_memory()
        answer, reasoning_tokens = final_token_ids(tokens.tolist(), thinking=self.contract["thinking"], eos=eos)
        self.last_metrics.update(reasoning_tokens=reasoning_tokens, final_tokens=len(answer))
        self.last_output = self.tokenizer.decode(answer, skip_special_tokens=True).strip()
        return self.last_output

    def choose(self, system, content, codes, *, max_code_chars=8):
        """Greedy constrained code + EOS; serialization is owned by the caller."""
        import resource
        import torch
        from .work_context_choices import ChoiceTrie, validate_codes

        self.last_output, self.last_metrics = "", {}
        require(not self.contract["thinking"] and self.contract["decoding"] == "greedy",
                "INVALID_MODEL_CONFIG")
        validate_codes(codes, max_code_chars=max_code_chars)
        started = time.monotonic()
        self._load()
        eos = self.model.generation_config.eos_token_id
        eos = {eos} if isinstance(eos, int) else set(eos or [])
        trie = ChoiceTrie({code: self.tokenizer.encode(code, add_special_tokens=False)
                           for code in codes}, eos, max_code_chars=max_code_chars)
        for code in codes:
            require(self.tokenizer.decode(self.tokenizer.encode(code, add_special_tokens=False),
                                          skip_special_tokens=False) == code, "INVALID_CHOICES")
        prompt = self.tokenizer.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": content}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False)
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=False)
        length = inputs["input_ids"].shape[1]
        require(length + trie.max_output <= self.contract["max_tokens"], "CONTEXT_TOO_LARGE")
        inputs = inputs.to(self.contract["device"])

        def allowed(batch_id, tokens):
            require(batch_id == 0, "INVALID_CHOICES")
            return trie.allowed(tokens[length:].tolist())

        with torch.inference_mode():
            generated = self.model.generate(
                **inputs, do_sample=False, max_new_tokens=trie.max_output,
                max_time=self.contract["max_seconds"], prefix_allowed_tokens_fn=allowed,
                pad_token_id=self.tokenizer.eos_token_id)
        tokens = generated[0][length:].tolist()
        self.last_metrics = {
            "seconds": round(time.monotonic() - started, 3), "input_tokens": length,
            "output_tokens": len(tokens), "reasoning_tokens": 0, "final_tokens": len(tokens),
            "max_rss_native": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "rss_unit": "bytes" if platform.system() == "Darwin" else "KiB"}
        if self.contract["device"] == "mps":
            self.last_metrics["mps_driver_bytes"] = torch.mps.driver_allocated_memory()
        self.last_output = trie.answer(tokens)
        return self.last_output
