<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Workflow assertions Value Dictionary

Durable table owner: [docs/policies/project/data-model/workflow-assertions.md](../workflow-assertions.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `workflow-assertion.boundary-kind`

- Physical field or projection: `workflow_assertions.boundary_kind`
- Allowed values: `relation`, `lifecycle`
- Enforcement: `schema-check`
- Logical axis: asserted workflow boundary family
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/workflow_assertions.py`
- Consumers: `src/localbrain/workflow_assertions.py`, `src/localbrain/workflow_correction_view.py`
- Consequence: Selects Episode-pair relation validation or one-Episode lifecycle validation.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `workflow-assertion.kind`

- Physical field or projection: `workflow_assertions.assertion_kind`
- Allowed values: `same-flow`, `split-here`, `merge-into`, `close`, `reopen`
- Enforcement: `schema-check`
- Logical axis: user workflow correction action
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/workflow_assertions.py`
- Consumers: `src/localbrain/workflow_assertions.py`, `src/localbrain/workflow_correction.py`, `src/localbrain/workflow_correction_view.py`
- Consequence: Determines the exact relation or lifecycle transition recorded in one append-only assertion.
- Presentation mode: `logical-label`
- Labels: `same-flow` → 같은 흐름; `split-here` → 여기서 분기; `merge-into` → 여기로 병합; `close` → 종료; `reopen` → 다시 열기
- Help: 사용자가 확인한 업무 흐름의 관계 또는 종료 경계를 나타냅니다.
- Visible consumer inventory: `src/localbrain/workflow_correction_view.py` (registry-backed)

## `workflow-assertion.undo`

- Physical field or projection: `workflow_assertions.is_undo`
- Allowed values: `0`, `1`
- Enforcement: `boolean-like`
- Logical axis: assertion reversal marker
- Default: `0`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/workflow_assertions.py`
- Consumers: `src/localbrain/workflow_assertions.py`, `src/localbrain/workflow_correction_view.py`
- Consequence: Marks a superseding row as an explicit reversal while retaining the original five-value assertion kind.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `workflow-assertion.meaning`

- Physical field or projection: `workflow_assertions.before_meaning`, `workflow_assertions.after_meaning`
- Allowed values: `relation:absent`, `relation:continues`, `relation:branches-from`, `relation:merged-into`, `lifecycle:unknown`, `lifecycle:open`, `lifecycle:closed`
- Enforcement: `schema-check`
- Logical axis: canonical workflow boundary meaning
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/workflow_assertions.py`
- Consumers: `src/localbrain/workflow_assertions.py`, `src/localbrain/workflow_correction_view.py`
- Consequence: Makes every assertion and reversal replayable without reinterpreting its original before/after state.
- Presentation mode: `logical-label`
- Labels: `relation:absent` → 관계 없음; `relation:continues` → 이어짐; `relation:branches-from` → 분기; `relation:merged-into` → 병합; `lifecycle:unknown` → 종료 여부 미확인; `lifecycle:open` → 열림; `lifecycle:closed` → 종료
- Help: 교정 전과 후의 정확한 업무 경계를 비교합니다.
- Visible consumer inventory: `src/localbrain/workflow_correction_view.py` (registry-backed)

## `workflow-assertion.closure-reason`

- Physical field or projection: `workflow_assertions.before_closure_reason`, `workflow_assertions.after_closure_reason`
- Allowed values: `completed`, `abandoned`, `superseded`, `merged`, `other`
- Enforcement: `schema-check`
- Logical axis: explicit closure reason
- Default: `NULL`
- Fallbacks: `null`: label → 종료 사유 없음; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/workflow_assertions.py`
- Consumers: `src/localbrain/workflow_assertions.py`, `src/localbrain/workflow_correction.py`, `src/localbrain/workflow_correction_view.py`
- Consequence: Qualifies only a closed before/after lifecycle meaning and never derives closure from inactivity.
- Presentation mode: `logical-label`
- Labels: `completed` → 완료; `abandoned` → 중단; `superseded` → 다른 흐름으로 대체; `merged` → 병합됨; `other` → 기타
- Help: 사용자가 직접 확인한 종료 이유입니다.
- Visible consumer inventory: `src/localbrain/workflow_correction_view.py` (registry-backed)

## `workflow-assertion.authority`

- Physical field or projection: `workflow_assertions.authority`
- Allowed values: `user-confirmed`
- Enforcement: `schema-check`
- Logical axis: workflow assertion authority
- Default: `user-confirmed`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/workflow_assertions.py`
- Consumers: `src/localbrain/workflow_assertions.py`, `src/localbrain/workflow_correction_view.py`
- Consequence: Keeps durable user correction distinct from observation, deterministic candidacy, and organization evidence.
- Presentation mode: `logical-label`
- Labels: `user-confirmed` → 사용자 확인
- Help: 사용자가 직접 확인하거나 되돌린 경계입니다.
- Visible consumer inventory: `src/localbrain/workflow_correction_view.py` (registry-backed)

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `identity keys, lookup IDs, note, timestamps, version, and positive sequence` | workflow assertion contract | Stable identities, bounded user text, chronology, version evidence, and structural sequence are not selectable state vocabularies. |
