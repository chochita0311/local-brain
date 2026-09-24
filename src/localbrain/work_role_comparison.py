"""Matched synthetic role formulations; no extractor or model-admission producer."""

import itertools
import json
import time

from .session_simulation import atomic_json, now, read_json
from .work_context import inference_identity
from .work_context_choices import MAX_CODE_TOKENS, SEMANTIC_VERSION, validate_codes
from .work_context_evaluation import OWNER, evaluation_store, revalidate
from .work_context_evidence import (
    FACETS, OPTIONS, PROMPTS, SUPPORT, SYSTEM, evidence_spans, infer_evidence, validate_runtime,
)
from .work_context_staged import stage_metrics
from .work_reconstruction import ExperimentError, digest, require

VERSION = "work-role-formulation-comparison.v1"
LIMITS = {"max_calls": 512, "max_seconds": 1200, "max_attempts_per_observation": 2,
          "max_tokens": 8192, "max_output": 128, "call_seconds": 30}
FIELDS = ("goal", "progress", "results", "remaining")
ROLE_SETS = {"none": ()}
for size in range(1, len(FIELDS) + 1):
    for roles in itertools.combinations(FIELDS, size):
        ROLE_SETS["_".join(roles)] = roles
ROLE_SETS["uncertain"] = None
DIRECT = """Classify the COMPLETE set of semantic roles of the focus itself.
Use the full original conversation, including later completion of the SAME work.
Select exactly the combination that applies: more than one role is allowed,
but a related subject is not sufficient to add a role. Select none if no role
applies, or uncertain if the roles cannot be resolved. Do not classify the whole
conversation or borrow another span's role. The definitions below are the same
definitions used for separate property questions:\n"""


def role_options():
    options = []
    for label, roles in ROLE_SETS.items():
        meaning = ("The role set cannot be resolved from the source" if roles is None else
                   "Exactly these roles: " + (", ".join(roles) or "none") +
                   "; no other role from goal, progress, results, remaining applies")
        options.append({"answer": label, "meaning": meaning})
    validate_codes([o["answer"] for o in options], max_code_chars=32)
    return options


def matrix(cases):
    require(isinstance(cases, list) and 1 <= len(cases) <= 22
            and len({c["id"] for c in cases}) == len(cases), "INVALID_CASES")
    cells = []
    for case in cases:
        require(case["family"] in {"role", "relation"}, "INVALID_CASES")
        packet = case["packet"]
        if case["family"] == "relation":
            require(case["expected"] in {"continues", "related", "independent", "uncertain"}, "INVALID_CASES")
            require(set(packet) == {"left", "right"}, "INVALID_CASES")
            for side in packet:
                evidence_spans(packet[side])
            cells.append({"id": case["id"] + ".control", "case_id": case["id"],
                          "family": "relation", "method": "unchanged-evidence", "packet": packet})
            continue
        require(set(packet) == {"messages"} and isinstance(case["expected"], list)
                and set(case["expected"]) <= set(FIELDS)
                and len(set(case["expected"])) == len(case["expected"]), "INVALID_CASES")
        focused = [s for s in evidence_spans(packet["messages"])
                   if {k: s[k] for k in ("message", "quote")} == case["focus"]]
        require(len(focused) == 1, "INVALID_CASES")
        for order in (0, 1):
            for method in ("properties", "direct"):
                for field in FIELDS if method == "properties" else ("roles",):
                    options = ([{"answer": a, "meaning": m} for a, m in SUPPORT]
                               if method == "properties" else role_options())
                    if order:
                        options.reverse()
                    prompt = (PROMPTS[field] if method == "properties" else DIRECT + "\n".join(
                        f"{name}: {FACETS[name]}" for name in FIELDS))
                    content = prompt + "\nINPUT:\n" + json.dumps(
                        {**packet, "focus": focused[0], "alternatives": options},
                        ensure_ascii=False, sort_keys=True)
                    cells.append({"id": f"{case['id']}.{method}.{order}.{field}",
                                  "case_id": case["id"], "family": "role", "method": method,
                                  "order": order, "field": field, "system": SYSTEM,
                                  "content": content, "options": options})
    return cells


def suite_identity(cases):
    return digest({"version": VERSION, "choice_protocol": SEMANTIC_VERSION, "limits": LIMITS,
                   "cases": cases, "matrix": matrix(cases), "role_sets": ROLE_SETS,
                   "control_inference": inference_identity({}, "evidence")})


def preflight_tokenizer(tokenizer, cases):
    labels = {o["answer"] for c in matrix(cases) if c["family"] == "role" for o in c["options"]}
    labels.update(label for options in list(OPTIONS.values()) + [SUPPORT] for label, _ in options)
    validate_codes(sorted(labels), max_code_chars=32)
    encoded = {label: tokenizer.encode(label, add_special_tokens=False) for label in sorted(labels)}
    require(all(1 <= len(tokens) <= MAX_CODE_TOKENS
                and tokenizer.decode(tokens, skip_special_tokens=False) == label
                for label, tokens in encoded.items()), "INVALID_CHOICES")
    return encoded


def summarize(cases, cells, observations):
    indexed = {o["id"]: o for o in observations}
    rows = []
    relations = []
    for case in cases:
        selected = [c for c in cells if c["case_id"] == case["id"]]
        if case["family"] == "relation":
            item = indexed.get(selected[0]["id"])
            decision = item["result"]["relation"] if item and not item["error"] else None
            relations.append({"case_id": case["id"], "expected": case["expected"],
                              "decision": decision, "correct": decision == case["expected"],
                              "false_continuation": decision == "continues" and case["expected"] != "continues"})
            continue
        for order in (0, 1):
            for method in ("properties", "direct"):
                group = [c for c in selected if c["method"] == method and c["order"] == order]
                items = [indexed.get(c["id"]) for c in group]
                ready = all(i and not i["error"] and i["output"] in {o["answer"] for o in c["options"]}
                            for c, i in zip(group, items))
                roles = None
                if ready and not any(i["output"] == "uncertain" for i in items):
                    roles = ([c["field"] for c, i in zip(group, items) if i["output"] == "supported"]
                             if method == "properties" else list(ROLE_SETS[items[0]["output"]]))
                expected = case["expected"]
                rows.append({"case_id": case["id"], "method": method, "order": order,
                             "expected": expected, "roles": roles,
                             "correct": roles is not None and set(roles) == set(expected),
                             "extra": sorted(set(roles or []) - set(expected)),
                             "missing": sorted(set(expected) - set(roles or []))})
    methods = {}
    for method in ("properties", "direct"):
        group = [r for r in rows if r["method"] == method]
        pairs = [[r for r in group if r["case_id"] == case["id"]] for case in cases if case["family"] == "role"]
        methods[method] = {
            "total": len(group), "correct": sum(r["correct"] for r in group),
            "unresolved": sum(r["roles"] is None for r in group),
            "extra_roles": sum(len(r["extra"]) for r in group),
            "missing_roles": sum(len(r["missing"]) for r in group),
            "both_orders_correct": sum(all(r["correct"] for r in pair) for pair in pairs),
            "order_sensitive": sum(all(r["roles"] is not None for r in pair)
                                   and pair[0]["roles"] != pair[1]["roles"] for pair in pairs),
            "per_field": {field: {
                "tp": sum(r["roles"] is not None and field in r["roles"] and field in r["expected"] for r in group),
                "fp": sum(r["roles"] is not None and field in r["roles"] and field not in r["expected"] for r in group),
                "fn": sum(r["roles"] is not None and field not in r["roles"] and field in r["expected"] for r in group),
                "tn": sum(r["roles"] is not None and field not in r["roles"] and field not in r["expected"] for r in group),
                "unresolved": sum(r["roles"] is None for r in group)} for field in FIELDS}}
    paired = {"both_correct": 0, "direct_only": 0, "properties_only": 0, "neither": 0}
    for case in (c for c in cases if c["family"] == "role"):
        for order in (0, 1):
            pair = {r["method"]: r["correct"] for r in rows if r["case_id"] == case["id"] and r["order"] == order}
            key = ("both_correct" if all(pair.values()) else "direct_only" if pair["direct"] else
                   "properties_only" if pair["properties"] else "neither")
            paired[key] += 1
    role_cases = [c for c in cases if c["family"] == "role"]
    baselines = {"total": len(role_cases) * 2,
                 "all_none_correct": sum(not c["expected"] for c in role_cases) * 2,
                 "all_roles_correct": sum(set(c["expected"]) == set(FIELDS) for c in role_cases) * 2,
                 "all_uncertain_correct": 0}
    return {"by_method": methods, "paired": paired, "roles": rows, "constant_baselines": baselines,
            "relations": {"total": len(relations), "correct": sum(r["correct"] for r in relations),
                          "false_continuations": sum(r["false_continuation"] for r in relations), "cases": relations}}


def observation_hash(item):
    return digest({k: v for k, v in item.items() if k != "sha256"})


class Meter:
    """Reserve every actual choice; the original inference pipeline stays unchanged."""

    def __init__(self, generator, progress, path):
        self.generator, self.progress, self.path = generator, progress, path
        self.contract = generator.contract
        self.last_metrics, self.last_output, self.audit, self.calls = {}, "", [], []
        self.elapsed_before, self.started = progress["elapsed_seconds"], time.monotonic()

    def elapsed(self):
        return self.elapsed_before + time.monotonic() - self.started

    def choose(self, system, content, codes, *, max_code_chars=32):
        require(self.progress["attempted_calls"] < LIMITS["max_calls"]
                and self.elapsed() < LIMITS["max_seconds"], "COMPARISON_BUDGET_EXHAUSTED")
        self.progress.update(attempted_calls=self.progress["attempted_calls"] + 1,
                             elapsed_seconds=LIMITS["max_seconds"])
        atomic_json(self.path, self.progress)
        self.generator.last_metrics, self.generator.last_output = {}, ""
        self.last_metrics, self.last_output = {}, ""
        try:
            self.audit.append(self.generator.describe_prompt(system, content, codes))
            answer = self.generator.choose(system, content, codes, max_code_chars=max_code_chars)
            require(answer in codes, "INVALID_CHOICE_OUTPUT")
            require(self.elapsed() < LIMITS["max_seconds"], "COMPARISON_BUDGET_EXHAUSTED")
            return answer
        finally:
            self.last_metrics = dict(self.generator.last_metrics)
            self.last_output = self.generator.last_output
            self.calls.append(dict(self.last_metrics))
            self.progress["elapsed_seconds"] = self.elapsed()
            atomic_json(self.path, self.progress)


def compare(generator, cases, folder):
    validate_runtime(generator)
    cells, suite = matrix(cases), suite_identity(cases)
    config = digest([suite, generator.contract])
    with evaluation_store(folder) as folder:
        path = folder / "progress.json"
        old = read_json(path) if path.exists() else None
        if old is not None:
            require(old.get("comparison") == VERSION and old.get("configuration") == config,
                    "COMPARISON_CONFIG_MISMATCH")
            require(old.get("inflight") is None, "COMPARISON_UNCLEAN_INTERRUPTION")
        progress = old if old is not None else {
            "owner": OWNER, "comparison": VERSION, "configuration": config, "suite": suite,
            "model": generator.contract, "limits": dict(LIMITS), "started_at": now().isoformat(),
            "synthetic_only": True, "model_admission": False, "private_corpus_examined": False,
            "quality_scope": "matched-formulation-diagnostic-only", "observations": [],
            "attempted_calls": 0, "elapsed_seconds": 0.0, "inflight": None, "attempts": {}}
        planned = {c["id"]: c for c in cells}
        observed, attempts = progress["observations"], progress["attempts"]
        require(isinstance(observed, list) and len({i["id"] for i in observed}) == len(observed)
                and all(i["id"] in planned and isinstance(i["output"], str) and len(i["output"]) <= 24000
                        and (i["error"] is None or isinstance(i["error"], str))
                        and i["sha256"] == observation_hash(i) for i in observed), "INVALID_CACHED_COMPARISON")
        require(isinstance(attempts, dict) and all(k in planned and type(v) is int
                and 1 <= v <= LIMITS["max_attempts_per_observation"] for k, v in attempts.items())
                and all(i["id"] in attempts for i in observed), "INVALID_CACHED_COMPARISON")
        require(type(progress["attempted_calls"]) is int
                and len(observed) <= progress["attempted_calls"] <= LIMITS["max_calls"]
                and type(progress["elapsed_seconds"]) in {int, float}
                and 0 <= progress["elapsed_seconds"] < float("inf"), "INVALID_CACHED_COMPARISON")
        for item in observed:
            cell = planned[item["id"]]
            if cell["family"] == "relation" and item["error"] is None:
                revalidate({"kind": "relation", "packet": cell["packet"]}, item["result"])
        cache = {i["id"] for i in observed}
        if progress["elapsed_seconds"] >= LIMITS["max_seconds"] or progress.get("state") == "budget-exhausted":
            raise ExperimentError("COMPARISON_BUDGET_EXHAUSTED")
        progress.update(state="running", reused=len(cache))
        atomic_json(path, progress)
        for cell in cells:
            if cell["id"] in cache:
                continue
            if (progress["attempted_calls"] >= LIMITS["max_calls"]
                    or progress["elapsed_seconds"] >= LIMITS["max_seconds"]):
                progress.update(state="budget-exhausted")
                atomic_json(path, progress)
                raise ExperimentError("COMPARISON_BUDGET_EXHAUSTED")
            if attempts.get(cell["id"], 0) >= LIMITS["max_attempts_per_observation"]:
                progress.update(state="attempts-exhausted")
                atomic_json(path, progress)
                raise ExperimentError("OBSERVATION_ATTEMPTS_EXHAUSTED")
            attempts[cell["id"]] = attempts.get(cell["id"], 0) + 1
            progress.update(inflight=cell["id"], current_observation=cell["id"])
            atomic_json(path, progress)
            meter = Meter(generator, progress, path)
            item = {"id": cell["id"], "output": "", "error": None, "result": None}
            try:
                if cell["family"] == "relation":
                    item["result"] = infer_evidence(meter, "relation", cell["packet"])
                else:
                    item["output"] = meter.choose(cell["system"], cell["content"],
                                                  [o["answer"] for o in cell["options"]])
            except ExperimentError as error:
                if str(error) == "COMPARISON_BUDGET_EXHAUSTED":
                    progress.update(state="budget-exhausted", inflight=None,
                                    elapsed_seconds=meter.elapsed(), updated_at=now().isoformat())
                    atomic_json(path, progress)
                    raise
                item.update(error=str(error), output="", result=None)
            except BaseException as error:
                progress.update(state="interrupted" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "failed",
                                inflight=None, elapsed_seconds=meter.elapsed(), updated_at=now().isoformat())
                atomic_json(path, progress)
                raise
            item.update(metrics={**stage_metrics(meter.calls), "case_seconds": round(
                meter.elapsed() - meter.elapsed_before, 3)}, audit=meter.audit,
                decisions=meter.last_metrics.get("decisions", []))
            item["sha256"] = observation_hash(item)
            observed.append(item)
            progress.update(inflight=None, elapsed_seconds=meter.elapsed(), updated_at=now().isoformat())
            atomic_json(path, progress)
            if progress["elapsed_seconds"] >= LIMITS["max_seconds"] or item["error"] == "COMPARISON_BUDGET_EXHAUSTED":
                progress.update(state="budget-exhausted")
                atomic_json(path, progress)
                raise ExperimentError("COMPARISON_BUDGET_EXHAUSTED")
        report = {**progress, "state": "complete", "finished_at": now().isoformat(),
                  "cases": cases, "matrix": cells, "summary": summarize(cases, cells, observed)}
        atomic_json(folder / "report.json", report)
        progress.update(state="complete", finished_at=report["finished_at"])
        atomic_json(path, progress)
        return report
