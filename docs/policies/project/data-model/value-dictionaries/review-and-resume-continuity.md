<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Review and resume continuity Value Dictionary

Durable table owner: [docs/policies/project/data-model/review-and-resume-continuity.md](../review-and-resume-continuity.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `suggestion.type`

- Physical field or projection: `suggestions.suggestion_type`
- Allowed values: `link`, `resource_link`, `checkpoint_draft`
- Enforcement: `application-stored`
- Logical axis: reviewable suggestion operation
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/workstreams.py`, `src/localbrain/runner.py`
- Consumers: `src/localbrain/workstreams.py`
- Consequence: Selects the explicit acceptance operation; no suggestion changes organization silently.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `suggestion.target`

- Physical field or projection: `suggestions.target_type`
- Allowed values: `workstream`, `thread`
- Enforcement: `application-stored`
- Logical axis: suggestion review owner
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/workstreams.py`, `src/localbrain/runner.py`
- Consumers: `src/localbrain/workstreams.py`
- Consequence: Resolves the application-enforced review target.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `suggestion.status`

- Physical field or projection: `suggestions.status`
- Allowed values: `pending`, `accepted`, `rejected`, `superseded`
- Enforcement: `application-stored`
- Logical axis: suggestion review lifecycle
- Default: `pending`
- Fallbacks: `null`: reject; `unknown`: label → 상태 알 수 없음; `invalid`: reject; `future`: label → 새 검토 상태
- Producers: `src/localbrain/workstreams.py`
- Consumers: `src/localbrain/workstreams.py`, `src/localbrain/templates/workstream.html`
- Consequence: Only acceptance may apply a reviewable suggestion.
- Presentation mode: `logical-label`
- Labels: `pending` → 검토 대기; `accepted` → 수락됨; `rejected` → 거절됨; `superseded` → 새 제안으로 대체됨
- Help: 제안의 검토 결과이며 자동 적용 상태가 아닙니다.
- Visible consumer inventory: `src/localbrain/templates/workstream.html` (registry-backed)

## `checkpoint-reference.entity-type`

- Physical field or projection: `checkpoint_resource_refs.entity_type`
- Allowed values: `session`, `document`, `project`, `external`, `local`
- Enforcement: `application-stored`
- Logical axis: snapshot reference target
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/workstreams.py`
- Consumers: `src/localbrain/workstreams.py`
- Consequence: Preserves the referenced resource set captured at confirmation time.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `checkpoint text sections and relation_type` | checkpoint writer | User or model-authored content and open relation semantics are not enums. |
