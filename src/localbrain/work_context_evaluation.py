"""Resumable synthetic-only model admission; no private source discovery."""

import fcntl
import os
import stat
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path

from .session_simulation import _safe_file, atomic_json, now, read_json
from .work_context import infer, inference_identity, validate_relation, validate_units
from .work_reconstruction import ExperimentError, digest, require, timestamp

OWNER = "localbrain.work-context-evaluation.v1"
FILES = {"owner.json", "writer.lock", "progress.json", "report.json"}


@contextmanager
def evaluation_store(folder):
    folder = Path(folder)
    repo = Path(__file__).resolve().parents[2]
    require(folder.is_absolute() and folder == folder.resolve() and folder != repo
            and repo not in folder.parents and folder not in repo.parents
            and folder.parent.is_dir(), "INVALID_OUTPUT")
    if not folder.exists():
        folder.mkdir(mode=0o700)
        atomic_json(folder / "owner.json", {"owner": OWNER, "expires_at": (now() + timedelta(days=30)).isoformat()})
    info = folder.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and not info.st_mode & 0o077, "UNOWNED_OUTPUT")
    marker = read_json(folder / "owner.json")
    require(marker.get("owner") == OWNER, "UNOWNED_OUTPUT")
    lock = folder / "writer.lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        _safe_file(lock)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ExperimentError("EVALUATION_BUSY") from None
        for path in folder.iterdir():
            if path.name.endswith(".pending") and path.name[:-8] in FILES:
                _safe_file(path)
                path.unlink()
            else:
                require(path.name in FILES, "UNOWNED_OUTPUT")
                _safe_file(path)
        if timestamp(marker["expires_at"]) <= now():
            for name in ("report.json", "progress.json"):
                path = folder / name
                if path.exists():
                    path.unlink()
        atomic_json(folder / "owner.json", {"owner": OWNER, "expires_at": (now() + timedelta(days=30)).isoformat()})
        yield folder
    finally:
        os.close(fd)


def revalidate(case, result):
    def raw(fact):
        return None if fact is None else {"message": fact["message"], "quote": fact["quote"]}

    if case["kind"] == "extract":
        value = {"units": [{"goal": raw(unit["goal"]), "target": raw(unit["target"]),
                            **{field: [raw(f) for f in unit[field]]
                               for field in ("progress", "results", "remaining")}}
                           for unit in result["units"]]}
        validated = validate_units(value, case["packet"]["messages"])
    else:
        value = {"relation": result["relation"], "evidence": [raw(f) for f in result["evidence"]],
                 "link": raw(result["link"])}
        validated = validate_relation(value, **case["packet"])
    require(validated == result, "INVALID_CACHED_RESULT")
    return validated


def observation_hash(item):
    return digest({k: v for k, v in item.items() if k not in {"checks", "passed", "observation_sha256"}})


def validate_observation(case, item, identity):
    require(item.get("key") == digest([identity, case]) and item.get("id") == case["id"]
            and item.get("split") == case["split"] and item.get("negative") == case["negative"]
            and type(item.get("valid")) is bool
            and item.get("observation_sha256") == observation_hash(item), "INVALID_CACHED_RESULT")
    if item["valid"]:
        revalidate(case, item["result"])
    else:
        require(isinstance(item.get("error"), str) and bool(item["error"])
                and isinstance(item.get("invalid_output"), str)
                and len(item["invalid_output"]) <= 24000, "INVALID_CACHED_RESULT")
    return item


def verify_evidence_development(generator, cases, assess, path):
    """Read-only prerequisite; primary semantic review remains an operator gate."""
    path = Path(path)
    require(path.is_absolute() and path == path.resolve() and path.name == "report.json",
            "INVALID_DEVELOPMENT_REPORT")
    info = path.parent.stat()
    require(info.st_uid == os.getuid() and not info.st_mode & 0o077, "INVALID_DEVELOPMENT_REPORT")
    owner = read_json(path.parent / "owner.json")
    require(owner.get("owner") == OWNER and timestamp(owner["expires_at"]) > now(),
            "INVALID_DEVELOPMENT_REPORT")
    report = read_json(path)
    identity = inference_identity(generator.contract, "evidence")
    require(report.get("state") == "complete" and report.get("strategy") == "evidence"
            and report.get("configuration") == digest([identity, cases])
            and report.get("inference") == identity and report.get("synthetic_only") is True
            and report.get("private_corpus_examined") is False
            and report.get("gate_passed") is True, "DEVELOPMENT_GATE_REQUIRED")
    observed = report.get("cases", [])
    require(len(observed) == len(cases) and {i["id"] for i in observed} == {c["id"] for c in cases},
            "DEVELOPMENT_GATE_REQUIRED")
    by_id = {i["id"]: i for i in observed}
    scored = []
    for case in cases:
        item = validate_observation(case, by_id[case["id"]], identity)
        checks = assess(case, item["result"]) if item["valid"] else {"valid_output": False}
        scored.append({**case, "passed": bool(checks) and all(checks.values())})
    require({c["split"] for c in cases} == {"development", "compositional"}, "DEVELOPMENT_GATE_REQUIRED")
    for split in ("development", "compositional"):
        negative = [c for c in scored if c["split"] == split and c["negative"]]
        positive = [c for c in scored if c["split"] == split and not c["negative"]]
        require(negative and positive and all(c["passed"] for c in negative)
                and sum(c["passed"] for c in positive) * 5 >= len(positive) * 4,
                "DEVELOPMENT_GATE_REQUIRED")


def evaluate(generator, cases, assess, folder, *, strategy="single"):
    require(cases and len({case["id"] for case in cases}) == len(cases), "INVALID_CASES")
    identity = inference_identity(generator.contract, strategy)
    config = digest([identity, cases])
    terminal_cache = strategy == "evidence"
    with evaluation_store(folder) as folder:
        old = read_json(folder / "progress.json") if (folder / "progress.json").exists() else {}
        if terminal_cache and old:
            require(old.get("configuration") == config, "EVALUATION_CONFIG_MISMATCH")
            require(old.get("inflight") is None, "EVALUATION_UNCLEAN_INTERRUPTION")
            require(len({i["key"] for i in old["cases"]}) == len(old["cases"]), "INVALID_CACHED_RESULT")
            planned = {c["id"]: c for c in cases}
            for item in old["cases"]:
                require(item["id"] in planned, "INVALID_CACHED_RESULT")
                validate_observation(planned[item["id"]], item, identity)
        cache = {item["key"]: item for item in old.get("cases", [])} if old.get("configuration") == config else {}
        progress = {"owner": OWNER, "state": "running", "configuration": config,
                    "inference": identity, "strategy": strategy, "model": generator.contract, "cases": [],
                    "started_at": now().isoformat(), "synthetic_only": True, "reused": 0}
        if strategy in {"classified", "selected", "evidence"}:
            if terminal_cache:
                from .work_context_evidence import CONTRACT
                attempts = old.get("case_attempts", {})
                require(isinstance(attempts, dict) and all(
                    key in {c["id"] for c in cases} and type(value) is int
                    and 1 <= value <= CONTRACT["max_case_attempts"] for key, value in attempts.items()),
                    "INVALID_CACHED_RESULT")
                require(all(item["id"] in attempts for item in cache.values()), "INVALID_CACHED_RESULT")
                progress.update(inflight=None, case_attempts=attempts)
            elif strategy == "selected":
                from .work_context_selected import CONTRACT
            else:
                from .work_context_classified import CONTRACT
            from .work_context_choices import MAX_CODE_TOKENS, MAX_OPTIONS
            # The adapter's free-generation defaults are not this strategy's limits.
            progress["strategy_contract"] = {
                **CONTRACT, "generation_method": "choose", "max_options": MAX_OPTIONS,
                "max_output_tokens_per_choice": MAX_CODE_TOKENS + 1}
        atomic_json(folder / "progress.json", progress)
        try:
            for case in cases:
                key = digest([identity, case])
                progress["current_case"] = case["id"]
                atomic_json(folder / "progress.json", progress)
                item = cache.get(key)
                if item and item.get("valid") and not terminal_cache:
                    try:
                        result = revalidate(case, item["result"])
                    except (ExperimentError, KeyError, TypeError, ValueError):
                        item = None
                if not item or (not item.get("valid") and not terminal_cache):
                    if terminal_cache:
                        attempts = progress["case_attempts"]
                        require(attempts.get(case["id"], 0) < CONTRACT["max_case_attempts"],
                                "CASE_ATTEMPTS_EXHAUSTED")
                        attempts[case["id"]] = attempts.get(case["id"], 0) + 1
                        progress["inflight"] = case["id"]
                        atomic_json(folder / "progress.json", progress)
                    item = {"key": key, "id": case["id"], "split": case["split"],
                            "negative": case["negative"], "valid": False}
                    if terminal_cache:
                        generator.last_output, generator.last_metrics = "", {}
                    try:
                        result = infer(generator, case["kind"], case["packet"], strategy=strategy)
                        item.update(valid=True, result=result)
                    except ExperimentError as error:
                        item["error"] = str(error)
                        # Local synthetic diagnosis only; never printed by the CLI.
                        item["invalid_output"] = getattr(generator, "last_output", "")[:24000]
                    item["metrics"] = dict(getattr(generator, "last_metrics", {}))
                    if terminal_cache:
                        item["observation_sha256"] = observation_hash(item)
                        progress["inflight"] = None
                else:
                    progress["reused"] += 1
                item["checks"] = assess(case, item["result"]) if item["valid"] else {"valid_output": False}
                item["passed"] = all(item["checks"].values())
                progress["cases"].append(item)
                progress["updated_at"] = now().isoformat()
                atomic_json(folder / "progress.json", progress)
            negative = [case for case in progress["cases"] if case["negative"]]
            positive = [case for case in progress["cases"] if not case["negative"]]
            require(negative and positive, "INVALID_CASES")
            split_gates = {}
            for split in sorted({case["split"] for case in cases}):
                split_negative = [c for c in negative if c["split"] == split]
                split_positive = [c for c in positive if c["split"] == split]
                require(split_negative and split_positive, "INVALID_CASES")
                split_gates[split] = (all(c["passed"] for c in split_negative)
                                     and sum(c["passed"] for c in split_positive) * 5 >= len(split_positive) * 4)
            gate = all(split_gates.values())
            report = {**progress, "state": "complete", "finished_at": now().isoformat(),
                      "gate_passed": gate, "split_gates": split_gates,
                      "quality_scope": "fixed-synthetic-cases-only",
                      "case_splits": sorted({case["split"] for case in cases}),
                      "private_corpus_examined": False,
                      "negative_passed": sum(c["passed"] for c in negative), "negative_total": len(negative),
                      "positive_passed": sum(c["passed"] for c in positive), "positive_total": len(positive)}
            atomic_json(folder / "report.json", report)
            progress.update(state="complete", gate_passed=gate, finished_at=report["finished_at"])
            atomic_json(folder / "progress.json", progress)
            return report
        except BaseException as error:
            progress.update(state="interrupted" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "failed",
                            error=str(error) if isinstance(error, ExperimentError) else "EVALUATION_FAILED")
            if terminal_cache:
                # A caught termination is a clean interruption. An OS kill leaves
                # the on-disk in-flight reservation intact and cannot reset limits.
                progress["inflight"] = None
            atomic_json(folder / "progress.json", progress)
            raise
