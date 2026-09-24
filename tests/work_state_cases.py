"""Synthetic supplied semantics, authored before the projector; never model gold."""

import copy
from datetime import datetime, timedelta, timezone

from localbrain.work_state import VERSION, anchor_key, claim_key, text_revision


DEFAULT = object()


class Packet:
    def __init__(self):
        self.value = {"version": VERSION,
                      "snapshot": {"id": "synthetic", "cutoff_at": None, "complete": True},
                      **{name: [] for name in ("records", "anchors", "claims", "targets",
                                               "bindings", "links", "coverage", "gaps")}}
        self.names = {}
        self.goal = self.record("합성 대상 이름: 달력 이동 검증", role="user")
        self.target("effort", kind="effort")
        self.target("check", parent="effort")

    def record(self, text, *, at=DEFAULT, session="s", role="assistant", speaker=None):
        index = len(self.value["records"])
        at = (datetime(2026, 2, 1, tzinfo=timezone.utc) + timedelta(minutes=index)).isoformat() if at is DEFAULT else at
        record = {"id": "r" + str(index), "source": "synthetic", "session": session,
                  "native_id": "m" + str(index), "revision": text_revision(text), "text": text,
                  "role": role, "speaker": speaker or role + "-a", "sequence": index,
                  "asserted_at": at, "ingested_at": None}
        anchor = {"id": anchor_key(record, 0, len(text)), "record": record["id"],
                  "start": 0, "end": len(text), "quote": text}
        self.value["records"].append(record)
        self.value["anchors"].append(anchor)
        self.value["coverage"].append({"record": record["id"], "start": 0, "end": len(text),
                                       "disposition": "no-work", "claims": []})
        return anchor["id"]

    def target(self, key, *, kind="step", parent=None, anchors=None):
        self.value["targets"].append({"id": key, "kind": kind, "parent": parent,
                                      "label": "합성 " + key, "anchors": anchors or [self.goal]})

    def add(self, name, text, status=None, *, kind="state", target="check", focus=None,
            mode="assertion", start=None, end=None, context=None, **record_options):
        focus = focus or self.record(text, **record_options)
        claim = {"kind": kind, "focus": focus, "context": context or [], "meaning": text,
                 "status": status, "effective": {"mode": mode, "start": start, "end": end,
                                                  "evidence": [focus] if mode == "explicit" else []}}
        claim["id"] = claim_key(claim)
        self.names[name] = claim["id"]
        self.value["claims"].append(claim)
        record_id = next(a["record"] for a in self.value["anchors"] if a["id"] == focus)
        segment = next(s for s in self.value["coverage"] if s["record"] == record_id)
        segment["disposition"] = "claims"
        segment["claims"].append(claim["id"])
        if target:
            self.bind(name, target)
        return claim

    def bind(self, name, target, *, disposition="supported", relation="same-target", continuation=None):
        claim = next(c for c in self.value["claims"] if c["id"] == self.names[name])
        owner = next(t for t in self.value["targets"] if t["id"] == target)
        binding = {"id": "b" + str(len(self.value["bindings"])), "claim": claim["id"],
                   "target": target, "relation": relation, "disposition": disposition,
                   "evidence": sorted(set([claim["focus"], *owner["anchors"]])),
                   "continuation": continuation}
        self.value["bindings"].append(binding)
        return binding

    def link(self, before, after, kind="before", disposition="supported"):
        first, last = (next(c for c in self.value["claims"] if c["id"] == self.names[n])
                       for n in (before, after))
        link = {"id": "l" + str(len(self.value["links"])), "before": first["id"],
                "after": last["id"], "kind": kind, "disposition": disposition,
                "evidence": sorted(set([first["focus"], last["focus"]]))}
        self.value["links"].append(link)
        return link


def pending_completed():
    p = Packet()
    p.add("pending", "달력 이동 검증은 아직 하지 않았습니다.", "pending")
    p.add("done", "같은 달력 이동 검증을 완료했습니다.", "completed")
    return p


def scenarios():
    """Exact states are declared here, independently of projection output."""
    cases = []

    def case(name, p, expected):
        cases.append((name, copy.deepcopy(p), expected))

    p = pending_completed()
    case("same-check-completion", p, {"check": "completed", "effort": "unknown"})
    p = pending_completed()
    p.value["snapshot"]["cutoff_at"] = "2026-02-01T00:01:30Z"
    case("historical-cutoff", p, {"check": "pending", "effort": "unknown"})
    p = Packet()
    p.target("sibling", parent="effort")
    p.add("pending", "달력 이동 검증은 아직입니다.", "pending")
    p.add("done", "메뉴 검증을 완료했습니다.", "completed", target="sibling")
    case("sibling-does-not-close", p, {"check": "pending", "sibling": "completed", "effort": "unknown"})
    p = Packet()
    p.add("execution", "검증 실행을 마쳤습니다.", "completed")
    p.add("failure", "검증에서 두 항목이 실패했습니다.", kind="outcome")
    case("execution-versus-success", p, {"check": "completed", "effort": "unknown"})
    for status in ("completed", "pending"):
        p = Packet()
        focus = p.record("계산식을 수정했고 검증은 " + ("완료했습니다." if status == "completed" else "아직입니다."))
        p.add("action", "계산식을 수정했습니다.", kind="action", focus=focus, target="effort")
        p.add("status", "검증 상태 보고", status, focus=focus)
        case("compound-" + status, p, {"check": status, "effort": "unknown"})
    p = Packet()
    p.add("plan", "검증할 계획입니다.", kind="intention")
    p.add("activity", "레코드 수를 셌습니다.", kind="action", target=None)
    p.record("실제 요청이 아닌 예시: 고쳐줘")
    p.record("고마워")
    case("descriptive-roles-do-not-invent-status", p, {"check": "unknown", "effort": "unknown"})
    p = pending_completed()
    p.add("again", "같은 검증을 다시 열어 확인하겠습니다.", "pending")
    p.link("done", "again", "reopens")
    case("explicit-reopen", p, {"check": "pending"})
    p = Packet()
    p.add("pending", "검증이 남았습니다.", "pending")
    p.add("cancel", "이 검증은 취소합니다.", "cancelled")
    case("cancel-is-not-complete", p, {"check": "cancelled"})
    p = pending_completed()
    p.add("correction", "완료 보고를 정정합니다. 아직 미완료입니다.", "pending")
    p.link("done", "correction", "corrects")
    case("explicit-correction", p, {"check": "pending"})
    p.add("withdraw", "방금 정정을 철회합니다.", kind="retraction")
    p.link("correction", "withdraw", "retracts")
    case("retract-correction-restores-prior-report", p, {"check": "completed"})
    p = pending_completed()
    p.add("pending2", "まだ未完了です。", "pending")
    case("no-implicit-reopen", p, {"check": "conflicted"})
    p = Packet()
    p.add("done", "完了しました。", "completed")
    p.add("correction", "未完了です。前の報告を訂正します。", "pending", role="user")
    p.link("done", "correction", "corrects")
    case("cross-speaker-dispute", p, {"check": "conflicted"})
    p = Packet()
    p.add("pending", "まだです。", "pending", session="s", at=None, mode="unknown")
    p.add("done", "完了です。", "completed", session="s", at=None, mode="unknown")
    case("unknown-order", p, {"check": "conflicted"})
    p = Packet()
    p.add("pending", "今は未完了です。", "pending")
    p.add("past", "先週完了しました。", "completed", mode="explicit",
          start="2026-01-25T00:00:00Z", end="2026-01-25T00:00:00Z")
    case("retrospective-is-not-new-completion", p, {"check": "conflicted"})
    p = pending_completed()
    p.value["bindings"][-1]["relation"] = "related"
    case("topic-does-not-fulfill", p, {"check": "pending"})
    p = pending_completed()
    p.value["bindings"][-1]["disposition"] = "unresolved"
    case("unresolved-binding", p, {"check": "pending"})
    p = Packet()
    p.add("pending", "달력 이동 검증은 남았습니다.", "pending")
    done = p.add("done", "여섯 달 전 달력 이동 검증을 이어서 완료했습니다.", "completed",
                 session="later", at="2026-08-01T00:00:00Z", target=None)
    p.bind("done", "check", continuation={"left": [p.goal], "right_link": done["focus"]})
    case("long-gap-explicit-continuation", p, {"check": "completed"})
    return cases
