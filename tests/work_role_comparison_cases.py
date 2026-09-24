"""Fresh synthetic formulation controls; never admission or private source data."""


def message(key, text, role="user", at="2026-02-01T00:00:00Z"):
    return {"id": key, "text": text, "role": role, "at": at}


def role_case(key, text, expected, *, role="assistant", before=(), after=(), contrast=None):
    return {"id": key, "family": "role", "contrast": contrast,
            "packet": {"messages": [*before, message("f", text, role), *after]},
            "focus": {"message": "f", "quote": text}, "expected": expected}


def relation_case(key, left, right, expected):
    return {"id": key, "family": "relation", "packet": {"left": left, "right": right},
            "expected": expected}


CASES = [
    role_case("role_requested_goal", "레코드 가져오기에서 날짜가 하루 밀리는 문제를 고치자.",
              ["goal"], role="user", contrast="import-role"),
    role_case("role_performed_edit", "가져오기 날짜 변환 함수를 수정했습니다.",
              ["progress"], contrast="import-role"),
    role_case("role_reported_success", "날짜 변환 회귀 테스트 네 개가 통과했습니다.",
              ["results"], contrast="import-role"),
    role_case("role_outstanding_check", "가져오기 날짜 검증은 아직 실행하지 않았고 내일 진행할 예정입니다.",
              ["remaining"], contrast="import-role"),
    role_case("role_planned_check", "캐시 무효화 검증을 실행할 예정입니다.",
              ["remaining"], contrast="planned-performed"),
    role_case("role_performed_check", "캐시 무효화 검증을 실행했습니다.",
              ["progress"], contrast="planned-performed"),
    role_case("role_action_and_result", "내보내기 순서 계산을 수정했고 순서 검증 테스트 두 개가 통과했습니다.",
              ["progress", "results"]),
    role_case("role_action_and_pending", "색상 표를 갱신했고 대비 검증은 아직 하지 않았습니다.",
              ["progress", "remaining"]),
    role_case("role_example_only", "실제 작업 요청이 아닌 문장 예시입니다: '썸네일 여백 오류를 고쳐줘'.",
              [], role="user"),
    role_case("role_social_only", "설명 잘 들었어, 정말 고마워!", [], role="user"),
    role_case("role_pending_fulfilled", "달력 넘김 검증은 아직 수행하지 않았습니다.", [],
              after=[message("a", "방금 달력 넘김 검증을 수행했고 모두 통과했습니다.", "assistant")],
              contrast="later-completion-scope"),
    role_case("role_pending_other_completed", "달력 넘김 검증은 아직 수행하지 않았습니다.", ["remaining"],
              after=[message("a", "방금 별개인 연락처 정렬 검증을 수행했고 모두 통과했습니다.", "assistant")],
              contrast="later-completion-scope"),
    role_case("role_unknown_goal_activity", "측정 파일의 레코드 수를 셌습니다.", ["progress"],
              after=[message("a", "그 집계의 목적은 이 대화에 기록되지 않았습니다.", "assistant")]),
    role_case("role_interleaved_request", "별개로 즐겨찾기 메뉴가 화면 밖으로 나가는 오류를 고쳐줘.",
              ["goal"], role="user", before=[
                  message("a", "업로드 진행률이 멈추는 오류를 고치자."),
                  message("b", "진행률 계산 코드를 바꿨고 업로드 검증이 통과했습니다.", "assistant")]),
    role_case("role_goal_and_pending", "검색어의 대소문자에 따라 결과가 달라지는 오류를 없애는 것이 목표이며 배포 검증은 아직 남아 있습니다.",
              ["goal", "remaining"]),
    role_case("role_reported_failure", "교차 실행 검증에서 순서 확인 두 건이 실패했습니다.", ["results"]),
    relation_case("relation_unresolved_referent",
        [message("a1", "여기까지만 이야기하고 다음에 정하자.")],
        [message("b1", "그 이야기를 계속하자.")], "uncertain"),
    relation_case("relation_grounded_referent",
        [message("a1", "로컬 미리듣기에서 소리가 겹쳐 재생되는 오류를 고치자.")],
        [message("b1", "앞서 남긴 작업은 로컬 미리듣기의 겹침 재생 오류를 고치는 것이야."),
         message("b2", "그 이야기를 계속하자.")], "continues"),
    relation_case("relation_topic_without_link",
        [message("a1", "작업 취소 신호에 관한 공개 글을 읽었다.")],
        [message("b1", "작업 취소 신호에 관한 설명을 들었다.")], "related"),
    relation_case("relation_shared_config",
        [message("a1", "options.yaml에서 큐 대기 시간을 줄여 전송 지연을 낮추자.")],
        [message("b1", "options.yaml에서 단축키 이름을 번역하자; 전송 지연 개선과 별개인 표시 작업이다.")],
        "independent"),
    relation_case("relation_distant_link",
        [message("a1", "TASK-74의 첨부 파일 정렬 역전 오류를 고치는 것이 목표이며 경계값 검증이 남았다.")],
        [message("b1", "여섯 달 전 TASK-74의 첨부 파일 정렬 역전 오류 수정을 이어서 경계값을 검증하자.",
                 at="2026-08-01T00:00:00Z")], "continues"),
    relation_case("relation_identifier_conflict",
        [message("a1", "TASK-74는 첨부 파일 정렬 역전 오류를 고치는 작업이다.")],
        [message("b1", "이 팀의 TASK-74는 번호가 같을 뿐 이전 첨부 파일 작업을 이어가는 것이 아니다."),
         message("b2", "이번 목표는 모바일 입력창에서 커서가 사라지는 오류를 고치는 것이다.")],
        "independent"),
]
