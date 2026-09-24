"""Frozen synthetic semantic references for RUN-112; never inferred from answers.

Old source packets/expectations are imported unchanged. These additional reference
annotations belong only to the v2 diagnostic, not to historical trial rescoring.
"""

import copy

from work_context_cases import message
from work_context_evidence_cases import CASES as LEGACY


def span(message_id, quote, occurrence=0):
    return {"message": message_id, "quote": quote, "occurrence": occurrence}


def claim(key, role, message_id, quote, *, context=(), time=None):
    return {"id": key, "role": role, "span": span(message_id, quote),
            "context": list(context), "time": time}


def target(key, citation, kind="effort", parent=None):
    return {"id": key, "kind": kind, "parent": parent, "label": citation, "anchors": [citation]}


def binding(c, t, anchor, continuation=None):
    evidence = sorted({c, anchor, *([continuation["right_link"]] if continuation else [])})
    return {"claim": c, "target": t, "relation": "same-target", "disposition": "supported",
            "evidence": evidence, "continuation": continuation}


def effect(key, obligation, t, fulfillment=None, extra=()):
    return {"id": key, "kind": "opens-obligation" if fulfillment is None else "fulfills-obligation",
            "obligation": obligation, "fulfillment": fulfillment, "target": t,
            "disposition": "supported", "evidence": sorted({obligation, *extra, *([fulfillment] if fulfillment else [])})}


def link(before, after, kind, evidence=None):
    return {"before": before, "after": after, "kind": kind, "disposition": "supported",
            "evidence": evidence or [before, after]}


def annotate(case, claims, targets=(), assignments=(), effects=(), links=(), *, no_work=(), states=None, pair=None):
    case = copy.deepcopy(case)
    case["reference"] = {"extraction": {"claims": claims, "no_work": list(no_work)},
        "binding": {"targets": list(targets), "bindings": list(assignments), "effects": list(effects),
                    "links": list(links), "pair": pair}, "states": states or {t["id"]: "unknown" for t in targets}}
    return case


def ordinary(key, positive, *texts, cutoff=None, times=None):
    messages = [message("m%d" % (i + 1), text, "assistant" if i else "user",
                        at=times[i] if times else "2026-01-%02dT00:00:00Z" % (10 + i))
                for i, text in enumerate(texts)]
    return {"id": key, "kind": "extract", "split": "claim-history", "negative": not positive,
            "packet": {"messages": messages}, "cutoff_at": cutoff}


OLD = {c["id"]: c for c in LEGACY if c["split"] != "holdout"}
REFERENCES = []
REFERENCES.append(annotate(OLD["dev_mixed"], [
    claim("c1", "goal", "a1", "결제 API의 중복 청구를 막는 것이 목표야."),
    claim("c2", "step", "a1", "요청 키 검증을 추가해줘."),
    claim("c3", "action", "a2", "요청 키 검증 코드를 추가했습니다."),
    claim("c4", "pending", "a2", "동시 요청 테스트는 아직 남았습니다."),
    claim("c5", "goal", "a3", "문서 사이트의 검색 UI를 개선하자."),
    claim("c6", "step", "a3", "먼저 검색창 설계만 진행해.")],
    [target("t1", "c1"), target("t2", "c2", "step", "t1"), target("t3", "c4", "step", "t1"),
     target("t4", "c5"), target("t5", "c6", "step", "t4")],
    [binding(c, t, a) for c, t, a in (("c1", "t1", "c1"), ("c2", "t2", "c2"),
        ("c3", "t2", "c2"), ("c4", "t3", "c4"), ("c5", "t4", "c5"), ("c6", "t5", "c6"))],
    [effect("e1", "c2", "t2"), effect("e2", "c2", "t2", "c3"), effect("e3", "c6", "t5")],
    states={"t1": "unknown", "t2": "completed", "t3": "pending", "t4": "unknown", "t5": "pending"}))
REFERENCES.append(annotate(OLD["dev_unknown"], [], no_work=[span("a1", "응, 고마워.")]))

# Paired references freeze semantic claims as well as the unchanged relation.
PAIR_DATA = {
    "dev_resume": ([claim("c1", "goal", "a1", "TASK-17의 목표는 데이터 중복 수집 방지다."),
                    claim("c2", "step", "a1", "검증은 다음에 하자."),
                    claim("c3", "step", "b1", "지난 TASK-17의 데이터 중복 수집 방지 작업을 이어서 검증하자.")], "continues"),
    "dev_distinct": ([claim("c1", "goal", "a1", "로그인 API의 응답 속도를 개선하자."),
                      claim("c2", "goal", "b1", "로그인 API에서 비밀번호 정책을 강화하자.")], "independent"),
    "proof_contextless_resume": ([], "uncertain"),
    "proof_grounded_short_resume": ([claim("c1", "goal", "a1", "관측표의 시차 변환 오류를 고치자."),
        claim("c2", "pending", "a1", "변환식 검증이 남았어."),
        claim("c3", "goal", "b1", "지난 논의의 작업은 관측표의 시차 변환 오류를 고치는 것이었고"),
        claim("c4", "pending", "b1", "변환식 검증이 남았어."),
        claim("c5", "step", "b2", "그 일 계속하자.", context=[span("b1", "지난 논의의 작업은 관측표의 시차 변환 오류를 고치는 것이었고 변환식 검증이 남았어.")])], "continues"),
    "proof_shared_file_distinct": ([claim("c1", "goal", "a1", "runtime.cfg에서 추적 로그 보관량을 줄여 디스크 쓰기를 낮추자."),
        claim("c2", "goal", "b1", "runtime.cfg에서 날짜 표시를 현지화하자.")], "independent"),
    "proof_topic_not_identity": ([claim("c1", "action", "a1", "요청 속도 제한에 관한 공개 글을 읽었다."),
        claim("c2", "action", "b1", "요청 속도 제한에 관한 발표 메모를 정리했다.")], "related"),
    "proof_long_gap": ([claim("c1", "goal", "a1", "TASK-83의 목표는 알림 재전송 시 중복 발송을 없애는 것이다."),
        claim("c2", "pending", "a1", "재전송 검증은 남아 있다."),
        claim("c3", "step", "b1", "여섯 달 전 TASK-83의 중복 알림 방지 작업을 이어서 남은 재전송 검증을 하자.")], "continues"),
    "proof_reused_id_conflict": ([claim("c1", "goal", "a1", "TASK-91은 데스크톱 전송 대기열의 순서 오류를 고치는 작업이다."),
        claim("c2", "goal", "b2", "이번 목표는 모바일 화면의 토스트 알림이 가려지는 문제를 해결하는 것이다.")], "independent"),
}
for key, (claims, relation) in PAIR_DATA.items():
    case = OLD[key]
    left = "@" + case["packet"]["left"][0]["id"]
    right = "@" + case["packet"]["right"][-1]["id"]
    proof = {"left": ["c1"], "right_link": right}
    ts, bs, es, states = [], [], [], {}
    if relation == "continues":
        ts = [target("t1", "c1"), target("t2", "c2", "step", "t1")]
        bs = [binding("c1", "t1", "c1"), binding("c2", "t2", "c2")]
        states = {"t1": "unknown", "t2": "pending"}
        for c in claims[2:]:
            t = "t1" if c["role"] == "goal" else "t2"
            anchor = "c1" if t == "t1" else "c2"
            bs.append(binding(c["id"], t, anchor, {"left": [anchor], "right_link": right}))
        if claims[1]["role"] == "step":
            es.append(effect("e1", "c2", "t2"))
        for c in claims[2:]:
            if c["role"] == "step":
                es.append(effect("e" + c["id"], c["id"], "t2", extra=("c2", right)))
    elif claims:
        ts = [target("t1", "c1", "effort" if claims[0]["role"] == "goal" else "occurrence"),
              target("t2", "c2", "effort" if claims[1]["role"] == "goal" else "occurrence")]
        bs = [binding("c1", "t1", "c1"), binding("c2", "t2", "c2")]
    pair = {"relation": relation, "evidence": [] if relation == "uncertain" else sorted({left, right, "@" + case["packet"]["right"][0]["id"]}),
            "link": right if relation == "continues" else None}
    REFERENCES.append(annotate(case, claims, ts, bs, es, states=states or None, pair=pair))

REFERENCES.append(annotate(OLD["proof_interleaved"], [
    claim("c1", "goal", "m1", "대기열에서 빈 메시지를 중복 처리하는 오류를 없애자."),
    claim("c2", "goal", "m2", "인쇄 화면의 머리글이 잘리는 문제를 해결하는 것이다."),
    claim("c3", "action", "m3", "빈 메시지 중복 처리를 막는 대기열 필터를 추가했습니다."),
    claim("c4", "outcome", "m4", "인쇄 화면 머리글 회귀 테스트가 통과했습니다."),
    claim("c5", "pending", "m5", "대기열 변경의 동시 실행 검증은 아직 남았어.")],
    [target("t1", "c1"), target("t2", "c2"), target("t3", "c5", "step", "t1")],
    [binding(c, t, a) for c, t, a in (("c1", "t1", "c1"), ("c2", "t2", "c2"),
        ("c3", "t1", "c1"), ("c4", "t2", "c2"), ("c5", "t3", "c5"))],
    states={"t1": "unknown", "t2": "unknown", "t3": "pending"}))
REFERENCES.append(annotate(OLD["proof_same_outcome_phases"], [
    claim("c1", "goal", "m1", "사용자 동기화에서 중복 행이 생기는 문제를 해결하자."),
    claim("c2", "step", "m2", "같은 중복 행 방지 목표를 위해 배치의 멱등 처리를 추가해줘."),
    claim("c3", "action", "m3", "배치 키 중복 검사 코드를 추가했습니다."),
    claim("c4", "pending", "m4", "이 동기화 변경의 재실행 검증은 아직 하지 않았습니다.")],
    [target("t1", "c1"), target("t2", "c2", "step", "t1"), target("t3", "c4", "step", "t1")],
    [binding(c, t, a) for c, t, a in (("c1", "t1", "c1"), ("c2", "t2", "c2"), ("c3", "t2", "c2"), ("c4", "t3", "c4"))],
    [effect("e1", "c2", "t2"), effect("e2", "c2", "t2", "c3")], states={"t1": "unknown", "t2": "completed", "t3": "pending"}))
REFERENCES.append(annotate(OLD["proof_plan_only"], [
    claim("c1", "goal", "m1", "압축 파일 미리보기가 닫히는 오류를 수정해줘."),
    claim("c2", "step", "m2", "그 미리보기 오류의 재현 테스트를 실행할 예정입니다.", context=[span("m1", "압축 파일 미리보기가 닫히는 오류를 수정해줘.")]),
    claim("c3", "pending", "m2", "아직 수정이나 검증을 수행하지 않았습니다.")],
    [target("t1", "c1"), target("t2", "c2", "step", "t1"), target("t3", "c3", "step", "t1")],
    [binding("c1", "t1", "c1"), binding("c2", "t2", "c2"), binding("c3", "t3", "c3")],
    [effect("e1", "c2", "t2")], states={"t1": "unknown", "t2": "pending", "t3": "pending"}))
REFERENCES.append(annotate(OLD["proof_unknown_goal_activity"], [
    claim("c1", "action", "m1", "로그에서 오류 행 수를 세었습니다.")],
    [target("t1", "c1", "occurrence")], [binding("c1", "t1", "c1")]))
REFERENCES.append(annotate(OLD["proof_example_not_work"], [], no_work=[
    span(m["id"], m["text"]) for m in OLD["proof_example_not_work"]["packet"]["messages"]]))
REFERENCES.append(annotate(OLD["proof_completed_claim"], [
    claim("c1", "goal", "m1", "프로필 이미지의 종횡비가 깨지는 오류를 수정하자."),
    claim("c2", "action", "m2", "종횡비 검사를 수정했고"),
    claim("c3", "outcome", "m2", "회귀 테스트 두 개가 통과했습니다.")],
    [target("t1", "c1")], [binding("c1", "t1", "c1"), binding("c2", "t1", "c1"), binding("c3", "t1", "c1")]))

NEW = []
for positive, text in ((True, "색상 변환을 수정했고 샘플 검사가 통과했습니다."),
                       (False, "색상 변환을 수정하고 샘플 검사를 실행할 예정입니다.")):
    case = ordinary("claim_compound_" + ("performed" if positive else "plan"), positive,
                    "이미지의 잘못된 색상을 바로잡자.", text)
    cs = [claim("c1", "goal", "m1", "이미지의 잘못된 색상을 바로잡자.")]
    cs += ([claim("c2", "action", "m2", "색상 변환을 수정했고"), claim("c3", "outcome", "m2", "샘플 검사가 통과했습니다.")]
           if positive else [claim("c2", "step", "m2", "색상 변환을 수정하고", context=[span("m2", text)]),
                             claim("c3", "step", "m2", "샘플 검사를 실행할 예정입니다.")])
    ts = [target("t1", "c1")]
    bs = [binding("c1", "t1", "c1")]
    es, states = [], {"t1": "unknown"}
    if positive:
        bs += [binding("c2", "t1", "c1"), binding("c3", "t1", "c1")]
    else:
        ts += [target("t2", "c2", "step", "t1"), target("t3", "c3", "step", "t1")]
        bs += [binding("c2", "t2", "c2"), binding("c3", "t3", "c3")]
        es = [effect("e1", "c2", "t2"), effect("e2", "c3", "t3")]
        states.update(t2="pending", t3="pending")
    NEW.append(annotate(case, cs, ts, bs, es, states=states))
for same in (True, False):
    result = "호환성 검사 A의 결과가 실패로 나왔습니다." if same else "별개인 부하 검사 B를 실행했습니다."
    case = ordinary("claim_fulfillment_" + ("same" if same else "sibling"), same,
                    "호환성 검사 A를 한 번 실행해줘. 성공 여부와 무관하게 실행 결과만 필요해.", result)
    cs = [claim("c1", "step", "m1", "호환성 검사 A를 한 번 실행해줘."),
          claim("c2", "outcome" if same else "action", "m2", result)]
    ts = [target("t1", "c1", "step")]
    if not same:
        ts += [target("t2", "c2", "occurrence")]
    bs = [binding("c1", "t1", "c1"), binding("c2", "t1" if same else "t2", "c1" if same else "c2")]
    es = [effect("e1", "c1", "t1")]
    if same:
        es += [effect("e2", "c1", "t1", "c2")]
    NEW.append(annotate(case, cs, ts, bs, es,
                        states={"t1": "completed"} if same else {"t1": "pending", "t2": "unknown"}))
for reopen in (True, False):
    first = "월요일 백업 검사는 완료했습니다."
    last = "같은 월요일 백업 검사를 명시적으로 재개합니다. 그 검사는 다시 미완료 상태입니다." if reopen else "화요일 백업 검사는 아직 하지 않았습니다. 월요일 검사와는 별개 회차입니다."
    case = ordinary("claim_" + ("reopen" if reopen else "new_occurrence"), reopen, first, last)
    cs = [claim("c1", "completed", "m1", first), claim("c2", "pending", "m2", last)]
    ts = [target("t1", "c1", "occurrence")]
    if not reopen:
        ts += [target("t2", "c2", "occurrence")]
    bs = [binding("c1", "t1", "c1"), binding("c2", "t1" if reopen else "t2", "c1" if reopen else "c2")]
    NEW.append(annotate(case, cs, ts, bs, links=[link("c1", "c2", "reopens")] if reopen else [],
                       states={"t1": "pending"} if reopen else {"t1": "completed", "t2": "pending"}))
for continues in (True, False):
    left = "분석표의 시간대 계산 오류를 고치는 것이 목표다."
    right = "여덟 달 전 분석표의 시간대 계산 오류 수정 작업을 이어서 마무리하자." if continues else "분석표의 시간대에 관한 기술 글을 읽었습니다."
    case = {"id": "claim_gap_" + ("continues" if continues else "topic"), "kind": "relate", "split": "claim-history", "negative": not continues,
            "packet": {"left": [message("a1", left)], "right": [message("b1", right, at="2026-09-10T00:00:00Z")]}}
    cs = [claim("c1", "goal", "a1", left), claim("c2", "goal" if continues else "action", "b1", right)]
    ts = [target("t1", "c1")]
    if not continues:
        ts += [target("t2", "c2", "occurrence")]
    bs = [binding("c1", "t1", "c1"), binding("c2", "t1" if continues else "t2", "c1" if continues else "c2",
                {"left": ["c1"], "right_link": "@b1"} if continues else None)]
    NEW.append(annotate(case, cs, ts, bs, pair={"relation": "continues" if continues else "related",
        "evidence": ["@a1", "@b1"], "link": "@b1" if continues else None}))
for correct in (True, False):
    case = ordinary("claim_" + ("cancel_correction" if correct else "speaker_dispute"), correct,
                    "인덱스 점검은 완료했습니다.", "앞서 완료라고 한 보고를 정정합니다. 인덱스 점검은 취소했습니다.")
    if correct:
        case["packet"]["messages"][0]["role"] = "assistant"
    cs = [claim("c1", "completed", "m1", "인덱스 점검은 완료했습니다."),
          claim("c2", "cancelled", "m2", "앞서 완료라고 한 보고를 정정합니다. 인덱스 점검은 취소했습니다.")]
    NEW.append(annotate(case, cs, [target("t1", "c1", "step")],
                       [binding("c1", "t1", "c1"), binding("c2", "t1", "c1")],
                       links=[link("c1", "c2", "corrects")], states={"t1": "cancelled" if correct else "conflicted"}))
for dated in (True, False):
    first = "복원 검사는 미완료입니다."
    last = "복원 검사는 2026-01-11T00:00:00Z에 완료했습니다." if dated else "복원 검사는 언젠가 완료했습니다. 정확한 완료일은 모릅니다."
    case = ordinary("claim_time_" + ("ordered" if dated else "unknown"), dated, first, last)
    effective = {"start": "2026-01-11T00:00:00Z", "end": "2026-01-11T00:00:00Z",
                 "evidence": [span("m2", last)]} if dated else "unknown"
    cs = [claim("c1", "pending", "m1", first), claim("c2", "completed", "m2", last, time=effective)]
    NEW.append(annotate(case, cs, [target("t1", "c1", "step")],
                       [binding("c1", "t1", "c1"), binding("c2", "t1", "c1")],
                       states={"t1": "completed" if dated else "conflicted"}))

CASES = REFERENCES + NEW
# An action/result without an explicit step obligation contributes to the broad
# goal; it is not itself the identity or fulfillment of that entire effort.
for case in CASES:
    ref = case["reference"]
    roles = {c["id"]: c["role"] for c in ref["extraction"]["claims"]}
    kinds = {t["id"]: t["kind"] for t in ref["binding"]["targets"]}
    for b in ref["binding"]["bindings"]:
        if kinds[b["target"]] == "effort" and roles[b["claim"]] in {"action", "outcome"}:
            b["relation"] = "contributes"
HOLDOUT = [copy.deepcopy(c) for c in LEGACY if c["split"] == "holdout"]
assert len(REFERENCES) == 16 and len(NEW) == 12 and len(CASES) == 28 and len(HOLDOUT) == 10
assert {c["id"] for c in REFERENCES} == set(OLD)
