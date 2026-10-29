<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Personal learning Value Dictionary

Durable table owner: [docs/policies/project/data-model/personal-learning.md](../personal-learning.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `learning.outcome`

- Physical field or projection: `learning_attempts.outcome`
- Allowed values: `pending`, `read`, `again`, `partial`, `recalled`
- Enforcement: `schema-check`
- Logical axis: Personal learning outcome
- Default: `pending`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/templates/learning-reader.html`, `src/localbrain/learning.py`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `pending` → 자기 평가 전; `read` → 설명 읽음; `again` → 다시 보기; `partial` → 일부 설명 가능; `recalled` → 스스로 설명 가능
- Help: 검토한 수업과 개인 학습 기록의 상태입니다.
- Visible consumer inventory: `src/localbrain/learning.py` (registry-backed)

## `learning.confidence`

- Physical field or projection: `learning_attempts.confidence`
- Allowed values: `low`, `medium`, `high`
- Enforcement: `schema-check`
- Logical axis: Personal learning confidence
- Default: `NULL`
- Fallbacks: `null`: label → 확신 평가 없음 · 설명 읽기; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/templates/learning-reader.html`, `src/localbrain/learning.py`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `low` → 확신이 낮아요; `medium` → 어느 정도 확신해요; `high` → 확신해요
- Help: 검토한 수업과 개인 학습 기록의 상태입니다.
- Visible consumer inventory: `src/localbrain/learning.py` (registry-backed)

## `learning.hint-used`

- Physical field or projection: `learning_attempts.hint_used`
- Allowed values: `0`, `1`
- Enforcement: `schema-check`
- Logical axis: Personal learning hint-used
- Default: `0`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/templates/learning-reader.html`, `src/localbrain/learning.py`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `0` → 도움 사용 기록 없음; `1` → 도움 사용 기록 있음
- Help: 검토한 수업과 개인 학습 기록의 상태입니다.
- Visible consumer inventory: `src/localbrain/templates/learning-reader.html` (registry-backed)

## `learning.hidden`

- Physical field or projection: `learning_visibility.hidden`
- Allowed values: `0`, `1`
- Enforcement: `schema-check`
- Logical axis: Personal learning hidden
- Default: `0`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/templates/learning-library.html`, `src/localbrain/learning.py`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `0` → 목록에 표시; `1` → 목록에서 숨김
- Help: 검토한 수업과 개인 학습 기록의 상태입니다.
- Visible consumer inventory: `src/localbrain/templates/learning-library.html` (registry-backed)

## `learning.version-status`

- Physical field or projection: `learning_lessons.packet_json.version_status`
- Allowed values: `matched`, `unverified`
- Enforcement: `application-stored`
- Logical axis: Personal learning version-status
- Default: `unverified`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/templates/learning-article.html`, `src/localbrain/learning.py`, `src/localbrain/templates/learning-library.html`, `src/localbrain/templates/learning-reader.html`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `matched` → 업무와 자료의 적용 버전을 대조함; `unverified` → 업무와 자료의 버전 일치 여부 미확인
- Help: 검토한 수업과 개인 학습 기록의 상태입니다.
- Visible consumer inventory: `src/localbrain/templates/learning-article.html` (registry-backed); `src/localbrain/templates/learning-library.html` (registry-backed); `src/localbrain/templates/learning-reader.html` (registry-backed)

## `learning.source-kind`

- Physical field or projection: `learning_lessons.packet_json.sources.kind`
- Allowed values: `work`, `official`
- Enforcement: `application-stored`
- Logical axis: Personal learning source-kind
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/learning.py`, `src/localbrain/templates/learning-library.html`, `src/localbrain/templates/learning-reader.html`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `work` → 업무 기록; `official` → 공식 자료
- Help: 검토한 수업과 개인 학습 기록의 상태입니다.
- Visible consumer inventory: `src/localbrain/templates/learning-library.html` (registry-backed); `src/localbrain/templates/learning-reader.html` (registry-backed)

## `learning.question-kind`

- Physical field or projection: `learning_lessons.packet_json.questions.kind`
- Allowed values: `recall`, `apply`
- Enforcement: `application-stored`
- Logical axis: Personal learning question-kind
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/templates/learning-reader.html`, `src/localbrain/learning.py`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `recall` → 내 말로 떠올리기; `apply` → 조건을 바꿔 생각하기
- Help: 검토한 수업과 개인 학습 기록의 상태입니다.
- Visible consumer inventory: `src/localbrain/templates/learning-reader.html` (registry-backed)

## `learning.reviewer`

- Physical field or projection: `learning_lessons.packet_json.reviewed_by`
- Allowed values: `owner`, `assistant`, `unspecified`
- Enforcement: `application-stored`
- Logical axis: Declared lesson reviewer
- Default: `unspecified`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/templates/learning-article.html`, `src/localbrain/templates/learning-library.html`, `src/localbrain/templates/learning-reader.html`
- Consequence: Assistant review does not imply owner confirmation or verified correctness.
- Presentation mode: `logical-label`
- Labels: `owner` → 사용자가 근거를 검토한 수업; `assistant` → 작성 도우미가 근거를 대조한 수업 · 사용자 검토 전; `unspecified` → 수업 검토 주체 미기록
- Help: 수업 작성 때 근거를 확인한 주체의 선언입니다.
- Visible consumer inventory: `src/localbrain/templates/learning-article.html` (registry-backed); `src/localbrain/templates/learning-library.html` (registry-backed); `src/localbrain/templates/learning-reader.html` (registry-backed)

## `learning.scene-kind`

- Physical field or projection: `learning_lessons.packet_json.scene.kind`
- Allowed values: `command`, `diff`
- Enforcement: `application-stored`
- Logical axis: Code learning scene-kind
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/learning.py`, `src/localbrain/templates/learning-library.html`, `src/localbrain/templates/learning-scene.html`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `command` → 명령; `diff` → 코드 변경
- Help: 검토한 코드·명령 자료와 질문의 역할을 구분합니다.
- Visible consumer inventory: `src/localbrain/templates/learning-library.html` (registry-backed); `src/localbrain/templates/learning-scene.html` (registry-backed)

## `learning.scene-origin`

- Physical field or projection: `learning_lessons.packet_json.scene.origin`
- Allowed values: `source`, `synthetic`
- Enforcement: `application-stored`
- Logical axis: Code learning scene-origin
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/learning.py`, `src/localbrain/templates/learning-article.html`, `src/localbrain/templates/learning-library.html`, `src/localbrain/templates/learning-scene.html`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `source` → 실제 업무에서 보존한 자료; `synthetic` → 학습을 위해 만든 가상 예시
- Help: 검토한 코드·명령 자료와 질문의 역할을 구분합니다.
- Visible consumer inventory: `src/localbrain/templates/learning-article.html` (registry-backed); `src/localbrain/templates/learning-library.html` (registry-backed); `src/localbrain/templates/learning-scene.html` (registry-backed)

## `learning.execution`

- Physical field or projection: `learning_lessons.packet_json.scene.execution`
- Allowed values: `suggested`, `reported`, `executed`, `observed`
- Enforcement: `application-stored`
- Logical axis: Code learning execution
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/learning.py`, `src/localbrain/templates/learning-scene.html`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `suggested` → 제안된 명령 · 실행 미확인; `reported` → 업무 기록의 실행 보고; `executed` → 실행 기록 있음 · 결과 별도 확인; `observed` → 결과 기록 함께 보존
- Help: 검토한 코드·명령 자료와 질문의 역할을 구분합니다.
- Visible consumer inventory: `src/localbrain/templates/learning-scene.html` (registry-backed)

## `learning.git-state`

- Physical field or projection: `learning_lessons.packet_json.scene.git_state`
- Allowed values: `committed`, `staged`, `unstaged`, `mixed`
- Enforcement: `application-stored`
- Logical axis: Code learning git-state
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/learning.py`, `src/localbrain/templates/learning-scene.html`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `committed` → 고정 commit 사이의 변경; `staged` → staged 변경; `unstaged` → unstaged 변경; `mixed` → staged·unstaged를 포함한 변경
- Help: 검토한 코드·명령 자료와 질문의 역할을 구분합니다.
- Visible consumer inventory: `src/localbrain/templates/learning-scene.html` (registry-backed)

## `learning.depth`

- Physical field or projection: `learning_lessons.packet_json.questions.depth`
- Allowed values: `understand`, `predict`, `transfer`
- Enforcement: `application-stored`
- Logical axis: Code learning depth
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/learning.py`, `src/localbrain/templates/learning-library.html`, `src/localbrain/templates/learning-reader.html`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `logical-label`
- Labels: `understand` → 역할·흐름 이해; `predict` → 결과 예측; `transfer` → 조건 변경 적용
- Help: 검토한 코드·명령 자료와 질문의 역할을 구분합니다.
- Visible consumer inventory: `src/localbrain/templates/learning-library.html` (registry-backed); `src/localbrain/templates/learning-reader.html` (registry-backed)

## `learning.selection-signal`

- Physical field or projection: `learning_lessons.packet_json.selection.signal`
- Allowed values: `requested`, `recurring`, `recent`, `general`
- Enforcement: `application-stored`
- Logical axis: Code learning selection-signal
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/learning.py`
- Consumers: `src/localbrain/learning.py`
- Consequence: Self-reported evidence and reviewed source scope; never objective mastery or automatic currentness.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `stable keys, fingerprints, date/time values, answer lengths and correlated null checks` | src/localbrain/schema.sql | Structural or unbounded evidence, not selectable value vocabularies. |
