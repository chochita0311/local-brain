"""Finite synthetic trial with terminal observation caching, never corpus access."""

import copy
import hashlib
import time
from pathlib import Path

from . import work_state as state
from .session_simulation import atomic_json, now, read_json
from .work_claims import (BIND, EXTRACT, LIMITS, SYSTEM, VERSION, bind_claims, binding_prompt,
                          extract_claims, extraction_prompt, producer, records_for)
from .work_claim_assessment import binding_checks, extraction_checks, gates, legacy_checks
from .work_context_evaluation import evaluation_store
from .work_reconstruction import ExperimentError, require, timestamp

TRIAL = "source-claim-trial.v1"
PINNED = "b968826d9c46dd6066d109eabc6255188de91218"


def implementation_fingerprint():
    base = Path(__file__).parent
    return state._digest({name: hashlib.sha256((base / name).read_bytes()).hexdigest() for name in (
        "work_state.py", "work_claims.py", "work_claim_assessment.py", "work_claim_trial.py",
        "work_context.py", "work_context_model.py", "work_context_evaluation.py")})


def suite_identity(cases, holdout):
    return state._digest([TRIAL, cases, holdout, LIMITS, SYSTEM, EXTRACT, BIND, implementation_fingerprint()])


def preflight_tokenizer(tokenizer, cases, lineage):
    """Tokenize fixed extraction/conditioned prompts without loading weights."""
    counts = []
    for case in cases:
        records = records_for(case)
        gold = extract_claims(records, state._json(case["reference"]["extraction"]), lineage,
                              cutoff=case.get("cutoff_at"))
        prompts = [extraction_prompt(records), binding_prompt(gold, paired=case["kind"] == "relate",
                    reference_targets=case["reference"]["binding"]["targets"])]
        for system, content in prompts:
            rendered = tokenizer.apply_chat_template([{"role": "system", "content": system},
                {"role": "user", "content": content}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
            count = len(tokenizer.encode(rendered))
            require(count + LIMITS["output"] <= LIMITS["tokens"], "CONTEXT_TOO_LARGE")
            counts.append(count)
    return {"prompts": len(counts), "min_tokens": min(counts), "max_tokens": max(counts),
            "template": state._digest(tokenizer.chat_template), "counts_digest": state._digest(counts)}


def unresolved_baseline(cases, lineage, assess):
    rows = []
    empty = {"targets": [], "bindings": [], "effects": [], "links": [], "pair": None}
    for case in cases:
        records = records_for(case)
        a = extract_claims(records, '{"claims":[],"no_work":[]}', lineage, cutoff=case.get("cutoff_at"))
        wire = copy.deepcopy(empty)
        paired = case["kind"] == "relate"
        if paired:
            wire["pair"] = {"relation": "uncertain", "evidence": [], "link": None}
        b = bind_claims(a, state._json(wire), paired=paired)
        gold = extract_claims(records, state._json(case["reference"]["extraction"]), lineage, cutoff=case.get("cutoff_at"))
        wire["targets"] = case["reference"]["binding"]["targets"]
        conditional = bind_claims(gold, state._json(wire), paired=paired, reference_targets=wire["targets"])
        rows.append({"id": case["id"], "split": case["split"], "negative": case["negative"],
            "extraction": extraction_checks(case, a)[0], "conditioned": binding_checks(case, gold, conditional),
            "end_to_end": {**binding_checks(case, a, b), **legacy_checks(case, b, assess)}})
    return gates(rows)


def _hash(value, excluded):
    return state._digest({k: v for k, v in value.items() if k not in excluded})


def _safe_existing(folder):
    folder = Path(folder)
    if folder.exists() and (folder / "owner.json").exists():
        marker = read_json(folder / "owner.json")
        require(timestamp(marker["expires_at"]) > now(), "EVALUATION_EXPIRED")


def _validate_progress(old, configuration):
    require(old.get("trial") == TRIAL and old.get("configuration") == configuration,
            "EVALUATION_CONFIG_MISMATCH")
    require(old.get("checkpoint_hash") == _hash(old, {"checkpoint_hash"}), "INVALID_CHECKPOINT")
    require(old.get("inflight") is None, "EVALUATION_UNCLEAN_INTERRUPTION")
    require(type(old.get("calls")) is int and 0 <= old["calls"] <= LIMITS["calls"]
            and isinstance(old.get("elapsed_seconds"), (int, float)) and old["elapsed_seconds"] >= 0,
            "INVALID_CHECKPOINT")
    keys = set()
    for item in old["observations"]:
        require(item["key"] not in keys and item["observation_hash"] == _hash(item, {"observation_hash"}),
                "INVALID_CACHED_OBSERVATION")
        require(type(item["attempted"]) is bool and type(item["raw"]) is str and len(item["raw"]) <= 24000,
                "INVALID_CACHED_OBSERVATION")
        keys.add(item["key"])
    require(sum(i["attempted"] for i in old["observations"]) == old["calls"], "INVALID_CHECKPOINT")


def _runtime(contract):
    require(contract.get("model") == "Qwen/Qwen3-8B" and contract.get("revision") == PINNED
            and contract.get("device") == "mps" and contract.get("dtype") == "bfloat16"
            and contract.get("attention") == "eager" and contract.get("thinking") is False
            and contract.get("decoding") == "greedy" and contract.get("sampling") is None
            and contract.get("max_tokens") == LIMITS["tokens"]
            and contract.get("max_output") == LIMITS["output"]
            and contract.get("max_seconds") == LIMITS["call_seconds"], "TRIAL_RUNTIME_MISMATCH")


class Observations:
    def __init__(self, generator, progress, folder, replay, initial_seconds, clock):
        self.generator, self.p, self.folder = generator, progress, folder
        self.replay, self.clock, self.started = replay, clock, clock()
        self.base = progress["elapsed_seconds"] + (0 if replay else initial_seconds)
        self.cache = {i["key"]: i for i in progress["observations"]}
        self.reused, self.used = 0, set()

    def save(self):
        if not self.replay:
            self.p["elapsed_seconds"] = round(self.base + max(0, self.clock() - self.started), 6)
        self.p["checkpoint_hash"] = _hash(self.p, {"checkpoint_hash"})
        atomic_json(self.folder / "progress.json", self.p)

    def get(self, case, mode, prompt, *, skipped=None):
        payload = [case["id"], mode, prompt, skipped]
        key = state._digest([self.p["configuration"], payload])
        self.used.add(key)
        if key in self.cache:
            self.reused += 1
            return self.cache[key]
        require(not self.replay, "INCOMPLETE_REPLAY")
        item = {"key": key, "case": case["id"], "mode": mode, "input_digest": state._digest(payload),
                "attempted": False, "raw": "", "error": skipped, "metrics": {}}
        self.save()
        if not skipped and (self.p["calls"] >= LIMITS["calls"] or self.p["elapsed_seconds"] >= LIMITS["seconds"]):
            item["error"] = "TRIAL_BUDGET_EXHAUSTED"
        interrupted = None
        if item["error"] is None:
            self.p["calls"] += 1
            item["attempted"] = True
            self.p["inflight"] = key
            self.save()
            self.generator.last_metrics, self.generator.last_output = {}, ""
            started = self.clock()
            try:
                raw = self.generator.generate(*prompt)
                require(type(raw) is str and 0 < len(raw) <= 24000, "INVALID_OUTPUT")
                item["raw"] = raw
            except (ExperimentError, state.WorkStateError) as error:
                item["error"] = str(error)
                item["raw"] = getattr(self.generator, "last_output", "")[:24000]
            except (KeyboardInterrupt, SystemExit) as error:
                item["error"] = "GENERATION_INTERRUPTED"
                interrupted = error
            except Exception:
                item["error"] = "GENERATION_FAILED"
            item["metrics"] = copy.deepcopy(getattr(self.generator, "last_metrics", {}))
            item["metrics"]["attempt_seconds"] = round(max(0, self.clock() - started), 6)
            if item["metrics"]["attempt_seconds"] > LIMITS["call_seconds"]:
                item["error"] = "GENERATION_TIME_EXCEEDED"
            self.p["inflight"] = None
        item["observation_hash"] = _hash(item, {"observation_hash"})
        self.p["observations"].append(item)
        self.cache[key] = item
        self.save()
        if interrupted:
            raise interrupted
        return item


def _parsed(item, function):
    if item["error"]:
        return None, item["error"]
    try:
        return function(item["raw"]), None
    except (ExperimentError, state.WorkStateError) as error:
        return None, str(error)


def run_trial(generator, cases, holdout, assess, folder, *, replay=False, include_holdout=False,
              initial_seconds=0, clock=time.monotonic):
    _runtime(generator.contract)
    require(cases and len({c["id"] for c in cases + holdout}) == len(cases + holdout), "INVALID_CASES")
    require(all(c["split"] != "holdout" and "reference" in c for c in cases)
            and all(c["split"] == "holdout" and "reference" not in c for c in holdout), "INVALID_CASES")
    lineage = producer(generator.contract)
    configuration = state._digest([suite_identity(cases, holdout), generator.contract])
    _safe_existing(folder)
    with evaluation_store(folder) as folder:
        old = read_json(folder / "progress.json") if (folder / "progress.json").exists() else None
        old_report = read_json(folder / "report.json") if (folder / "report.json").exists() else {}
        if old:
            _validate_progress(old, configuration)
        require(not replay or old is not None, "INCOMPLETE_REPLAY")
        prior_review = old_report.get("primary_review")
        if include_holdout:
            require(prior_review and prior_review.get("passed") is True
                    and prior_review.get("development_digest") == old_report.get("development_digest")
                    and old_report.get("development_gate") is True
                    and old_report.get("configuration") == configuration
                    and prior_review.get("receipt") == _hash(prior_review, {"receipt"}), "DEVELOPMENT_REVIEW_REQUIRED")
        p = old or {"trial": TRIAL, "configuration": configuration, "producer": lineage,
            "started_at": now().isoformat(), "state": "running", "calls": 0,
            "elapsed_seconds": 0, "observations": [], "inflight": None}
        obs = Observations(generator, p, folder, replay, initial_seconds, clock)
        rows, outputs = [], []
        try:
            for case in cases + (holdout if include_holdout else []):
                if case["split"] == "holdout":
                    development_rows = [r for r in rows if r["split"] != "holdout"]
                    checked = gates(development_rows)
                    required_digest = state._digest([configuration, development_rows,
                        [o for o in p["observations"] if o["case"] in {c["id"] for c in cases}]])
                    require(all(v["passed"] for modes in checked.values() for v in modes.values())
                            and required_digest == prior_review["development_digest"], "DEVELOPMENT_REVIEW_REQUIRED")
                records = records_for(case)
                aitem = obs.get(case, "extraction", extraction_prompt(records))
                a, aerror = _parsed(aitem, lambda raw: extract_claims(records, raw, lineage, cutoff=case.get("cutoff_at")))
                row = {"id": case["id"], "split": case["split"], "negative": case["negative"]}
                row["extraction"] = ({"valid_output": False} if a is None else extraction_checks(case, a)[0]
                                     if "reference" in case else {"valid_structure_only": True})
                trace = {"id": case["id"], "extraction_error": aerror,
                         "extraction": None if a is None else a["wire"]}
                paired = case["kind"] == "relate"
                prompt = binding_prompt(a, paired=paired) if a else ["dependency", aitem["key"]]
                bitem = obs.get(case, "end-to-end", prompt, skipped=None if a else "PREREQUISITE_FAILED")
                b, berror = _parsed(bitem, lambda raw: bind_claims(a, raw, paired=paired))
                row["end_to_end"] = {"valid_output": False}
                if b is not None:
                    try:
                        checks = binding_checks(case, a, b) if "reference" in case else {}
                        row["end_to_end"] = {**checks, **legacy_checks(case, b, assess), "valid_output": True}
                    except (ExperimentError, state.WorkStateError) as error:
                        berror = str(error)
                        row["end_to_end"] = {"legacy_valid": False}
                trace.update(end_to_end_error=berror, end_to_end=None if b is None else b["wire"],
                             projection=None if b is None else b["projection"])
                if "reference" in case:
                    ref = case["reference"]
                    gold = extract_claims(records, state._json(ref["extraction"]), lineage, cutoff=case.get("cutoff_at"))
                    roster = ref["binding"]["targets"]
                    citem = obs.get(case, "reference-conditioned", binding_prompt(gold, paired=paired, reference_targets=roster))
                    c, cerror = _parsed(citem, lambda raw: bind_claims(gold, raw, paired=paired, reference_targets=roster))
                    row["conditioned"] = {"valid_output": False} if c is None else binding_checks(case, gold, c)
                    trace.update(conditioned_error=cerror, conditioned=None if c is None else c["wire"])
                rows.append(row); outputs.append(trace)
            require(obs.used == set(obs.cache), "UNEXPECTED_CACHED_OBSERVATION")
            split_gates = gates(rows)
            development_gate = all(v["passed"] for split, modes in split_gates.items() if split != "holdout" for v in modes.values())
            development_digest = state._digest([configuration, [r for r in rows if r["split"] != "holdout"],
                [o for o in p["observations"] if o["case"] in {c["id"] for c in cases}]])
            if include_holdout:
                require(development_gate and development_digest == prior_review["development_digest"], "DEVELOPMENT_REVIEW_REQUIRED")
            semantic = {"configuration": configuration, "rows": rows, "split_gates": split_gates,
                        "observation_hashes": [o["observation_hash"] for o in p["observations"]]}
            semantic_digest = state._digest(semantic)
            p["state"] = "complete"
            obs.save()
            report = {"trial": TRIAL, "state": "complete", "configuration": configuration,
                "suite": suite_identity(cases, holdout), "producer": lineage, "rows": rows,
                "split_gates": split_gates, "development_gate": development_gate,
                "development_digest": development_digest, "semantic_digest": semantic_digest,
                "primary_review": prior_review if prior_review and prior_review["development_digest"] == development_digest else None,
                "holdout_executed": include_holdout, "model_admission": False,
                "synthetic_only": True, "private_corpus_examined": False,
                "calls": p["calls"], "elapsed_seconds": p["elapsed_seconds"],
                "reused_observations": obs.reused, "observations": p["observations"], "outputs": outputs,
                "input_tokens": sum(o["metrics"].get("input_tokens", 0) for o in p["observations"]),
                "output_tokens": sum(o["metrics"].get("output_tokens", 0) for o in p["observations"]),
                "answered_extractions": sum(o["extraction"] is not None for o in outputs),
                "answered_end_to_end": sum(o["end_to_end"] is not None for o in outputs),
                "all_unresolved_baseline": unresolved_baseline(cases, lineage, assess),
                "finished_at": now().isoformat()}
            atomic_json(folder / "report.json", report)
            return report
        except BaseException:
            p["state"] = "interrupted"
            obs.save()
            raise


def record_primary_review(folder, development_digest, *, passed, findings):
    """An explicit primary-agent review receipt; never produced by the model."""
    require(type(passed) is bool and type(findings) is list and all(type(f) is str for f in findings), "INVALID_REVIEW")
    _safe_existing(folder)
    with evaluation_store(folder) as folder:
        report = read_json(folder / "report.json")
        progress = read_json(folder / "progress.json")
        _validate_progress(progress, report["configuration"])
        require(report["trial"] == TRIAL and report["state"] == "complete"
                and development_digest == report["development_digest"], "STALE_REVIEW")
        require(not passed or report["development_gate"] is True, "DEVELOPMENT_GATE_REQUIRED")
        receipt = {"reviewer": "primary-agent", "development_digest": development_digest,
                   "passed": passed, "findings": findings}
        receipt["receipt"] = _hash(receipt, {"receipt"})
        report["primary_review"] = receipt
        atomic_json(folder / "report.json", report)
        return receipt
