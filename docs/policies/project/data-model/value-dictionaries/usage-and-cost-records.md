<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Usage and cost records Value Dictionary

Durable table owner: [docs/policies/project/data-model/usage-and-cost-records.md](../usage-and-cost-records.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `usage.aggregation-scope`

- Physical field or projection: `usage_records.aggregation_scope`
- Allowed values: `direct`, `includes_children`
- Enforcement: `schema-check`
- Logical axis: token aggregation boundary
- Default: `direct`
- Fallbacks: `null`: reject; `unknown`: label → 범위 알 수 없음; `invalid`: reject; `future`: label → 새 집계 범위
- Producers: `src/localbrain/ingest/claude.py`, `src/localbrain/ingest/codex.py`
- Consumers: `src/localbrain/usage_queries.py`
- Consequence: Prevents child-token double counting.
- Presentation mode: `logical-label`
- Labels: `direct` → 이 Session만; `includes_children` → 하위 Session 포함
- Help: 토큰 합계에 포함된 Session 범위입니다.
- Visible consumer inventory: `src/localbrain/templates/sessions_dashboard.html` (registry-backed)

## `usage.capability-state`

- Physical field or projection: `usage_records.capability_state`
- Allowed values: `complete`, `partial`, `malformed`
- Enforcement: `schema-check`
- Logical axis: source usage completeness
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 확인 필요; `invalid`: reject; `future`: label → 새 상태
- Producers: `src/localbrain/ingest/claude.py`, `src/localbrain/ingest/codex.py`
- Consumers: `src/localbrain/usage_queries.py`
- Consequence: Incomplete or malformed facts reduce coverage confidence.
- Presentation mode: `logical-label`
- Labels: `complete` → 완전함; `partial` → 일부만 있음; `malformed` → 형식 오류
- Help: 원본 사용량 필드가 계산에 충분한지 나타냅니다.
- Visible consumer inventory: `src/localbrain/templates/sessions_dashboard.html` (registry-backed)

## `usage.calculation-state`

- Physical field or projection: `usage_records.calculation_state`
- Allowed values: `priced`, `unpriced`, `partial`, `failed`
- Enforcement: `schema-check`
- Logical axis: estimated cost calculation
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 계산 상태 알 수 없음; `invalid`: reject; `future`: label → 새 계산 상태
- Producers: `src/localbrain/usage.py`
- Consumers: `src/localbrain/usage_queries.py`, `src/localbrain/templates/sessions_dashboard.html`
- Consequence: Only priced records contribute an estimated cost value.
- Presentation mode: `logical-label`
- Labels: `priced` → 비용 계산됨; `unpriced` → 가격 정보 없음; `partial` → 일부만 계산됨; `failed` → 계산 실패
- Help: 비용은 실제 청구액이 아닌 현재 가격표 기반 추정치입니다.
- Visible consumer inventory: `src/localbrain/templates/sessions_dashboard.html` (registry-backed)

## `usage.attribution-basis`

- Physical field or projection: `usage_records.attribution_basis`
- Allowed values: `git_root`, `workspace_path`, `unassigned`
- Enforcement: `schema-check`
- Logical axis: Project attribution evidence
- Default: `unassigned`
- Fallbacks: `null`: reject; `unknown`: label → 근거 알 수 없음; `invalid`: reject; `future`: label → 새 귀속 근거
- Producers: `src/localbrain/db.py`
- Consumers: `src/localbrain/usage_queries.py`
- Consequence: Explains how an immutable usage snapshot was assigned to a Project.
- Presentation mode: `logical-label`
- Labels: `git_root` → Git 루트 일치; `workspace_path` → 작업 경로 일치; `unassigned` → Project 미지정
- Help: 사용량을 Project에 연결한 근거입니다.
- Visible consumer inventory: `src/localbrain/templates/sessions_dashboard.html` (registry-backed)

## `usage.freshness`

- Physical field or projection: `projection:usage.freshness`
- Allowed values: `current`, `stale`, `error`, `not_synchronized`
- Enforcement: `derived`
- Logical axis: usage source freshness
- Default: `not_synchronized`
- Fallbacks: `null`: label → 동기화 전; `unknown`: label → 상태 알 수 없음; `invalid`: reject; `future`: label → 새 상태
- Producers: `src/localbrain/usage_queries.py`
- Consumers: `src/localbrain/templates/sessions_dashboard.html`
- Consequence: Stale or error state keeps prior estimates visible with a warning.
- Presentation mode: `logical-label`
- Labels: `current` → 최신; `stale` → 다시 동기화 필요; `error` → 동기화 오류; `not_synchronized` → 동기화 전
- Help: 사용량 원본의 최근 동기화 상태입니다.
- Visible consumer inventory: `src/localbrain/templates/sessions_dashboard.html` (registry-backed)

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `models, calculator versions, total_semantics, numeric coverage states` | usage calculators and price snapshots | Versioned identifiers, source semantics, or numeric facts rather than closed presentation families. |
