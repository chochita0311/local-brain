"""Frozen diagnostic v1; synthetic only, independent of admission/holdout fixtures."""


def message(key, text, role="user", at="2026-02-01T00:00:00Z"):
    return {"id": key, "text": text, "role": role, "at": at}


FIELD_OPTIONS = [
    ("none", "사회적 인사나 감사 등이며 업무 의도나 수행 내용이 전혀 없음"),
    ("intent", "목표, 요청, 계획 또는 아직 수행하지 않은 남은 일"),
    ("activity", "이미 수행했다고 보고한 구현·조사 등의 행동; 완료 검증 결과는 아님"),
    ("outcome", "테스트 통과 같은 결과를 보고함; 보고자의 주장이지 독립적으로 검증된 사실은 아님"),
]
MEMBERSHIP_OPTIONS = [
    ("first", "첫 번째 기존 목표에 기여하는 활동"),
    ("second", "두 번째 기존 목표에 기여하는 활동"),
    ("new", "두 기존 목표와 별개이며 독립적으로 재개할 수 있는 새로운 목표"),
    ("unclear", "어느 목표에 기여하는지 또는 독립적인지 근거가 부족함"),
]
RELATION_OPTIONS = [
    ("unclear", "근거가 부족하여 관계를 판단할 수 없음"),
    ("continue", "같은 목표를 이어간다는 명시적 연결과 양쪽의 호환되는 맥락이 있음"),
    ("related", "관련된 주제이지만 같은 작업의 계속임을 판단할 근거는 없음"),
    ("separate", "독립적이거나 호환되지 않는 서로 다른 목표를 다룸"),
]


CASES = [
    {"id": "field_goal", "family": "field", "options": FIELD_OPTIONS,
     "input": {"messages": [message("m1", "백업 복구에서 파일이 빠지지 않도록 만드는 것이 목표야. 누락 검사를 추가해줘.")],
               "focus": "m1"}, "expected": "intent", "evidence_ids": ["m1"]},
    {"id": "field_mixed_request", "family": "field", "options": FIELD_OPTIONS,
     "input": {"messages": [
         message("m1", "백업 복구의 파일 누락을 고치자."),
         message("m2", "누락 검사를 추가했습니다.", "assistant"),
         message("m3", "별개로 일정 화면의 색 대비를 개선하자. 먼저 색상안을 만들어줘.")],
         "focus": "m3"}, "expected": "intent", "evidence_ids": ["m3"]},
    {"id": "field_activity", "family": "field", "options": FIELD_OPTIONS,
     "input": {"messages": [message("m1", "재시도 간격 계산 함수를 수정했습니다.", "assistant")],
               "focus": "m1"}, "expected": "activity", "evidence_ids": ["m1"]},
    {"id": "field_result", "family": "field", "options": FIELD_OPTIONS,
     "input": {"messages": [message("m1", "복구 누락 검증 테스트 세 개가 모두 통과했습니다.", "assistant")],
               "focus": "m1"}, "expected": "outcome", "evidence_ids": ["m1"]},
    {"id": "field_pending", "family": "field", "options": FIELD_OPTIONS,
     "input": {"messages": [message("m1", "장애 복구 리허설은 아직 실행하지 않았고 다음에 진행해야 합니다.", "assistant")],
               "focus": "m1"}, "expected": "intent", "evidence_ids": ["m1"]},
    {"id": "field_social", "family": "field", "options": FIELD_OPTIONS,
     "input": {"messages": [message("m1", "알겠어, 고마워!")], "focus": "m1"},
     "expected": "none", "evidence_ids": ["m1"]},
    {"id": "membership_followup", "family": "membership", "options": MEMBERSHIP_OPTIONS,
     "input": {"messages": [
         message("g1", "첫 목표는 사진 회전 시 세로 비율이 깨지는 오류를 고치는 것이다."),
         message("g2", "두 번째 목표는 청구서 PDF의 줄 간격을 개선하는 것이다."),
         message("n1", "그 사진 회전 오류 수정에 이어서 세로 비율 회귀 테스트를 하자.")],
         "first_goal": "g1", "second_goal": "g2", "focus": "n1"},
     "expected": "first", "evidence_ids": ["g1", "n1"]},
    {"id": "membership_new_goal", "family": "membership", "options": MEMBERSHIP_OPTIONS,
     "input": {"messages": [
         message("g1", "첫 목표는 배포 시간을 줄이는 것이다. 절차는 guide.md에 있다."),
         message("g2", "두 번째 목표는 설정 화면의 접근성을 높이는 것이다."),
         message("n1", "두 목표와 독립적으로 guide.md의 라이선스 고지를 최신 약관에 맞게 바꾸자.")],
         "first_goal": "g1", "second_goal": "g2", "focus": "n1"},
     "expected": "new", "evidence_ids": ["n1"]},
    {"id": "relation_distant_resume", "family": "relation", "options": RELATION_OPTIONS,
     "input": {"messages": [
         message("a1", "TASK-68의 복구 파일 누락 방지는 구현했고 복원 검증이 남아 있다."),
         message("b1", "몇 달 전에 남긴 TASK-68의 복구 파일 누락 방지 작업을 이어서 복원 검증하자.",
                 at="2026-08-01T00:00:00Z")], "left": "a1", "right": "b1"},
     "expected": "continue", "evidence_ids": ["a1", "b1"]},
    {"id": "relation_shared_file", "family": "relation", "options": RELATION_OPTIONS,
     "input": {"messages": [
         message("a1", "service.toml의 연결 제한을 조정해 과부하를 줄이자."),
         message("b1", "service.toml의 표시 이름을 바꾸자. 과부하 개선과는 별개의 브랜드 변경 작업이야.")],
         "left": "a1", "right": "b1"}, "expected": "separate", "evidence_ids": ["a1", "b1"]},
    {"id": "relation_topic_only", "family": "relation", "options": RELATION_OPTIONS,
     "input": {"messages": [message("a1", "서비스 모니터링에 관한 글을 읽었다."),
                            message("b1", "서비스 모니터링에 관한 발표를 들었다.")],
               "left": "a1", "right": "b1"}, "expected": "related", "evidence_ids": ["a1", "b1"]},
    {"id": "relation_missing_context", "family": "relation", "options": RELATION_OPTIONS,
     "input": {"messages": [message("a1", "나중에 정하자."), message("b1", "그걸 계속하자.")],
               "left": "a1", "right": "b1"}, "expected": "unclear", "evidence_ids": ["a1", "b1"]},
]
