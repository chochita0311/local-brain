<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Maintenance execution Value Dictionary

Durable table owner: [docs/policies/project/data-model/maintenance-execution.md](../maintenance-execution.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `maintenance.runner`

- Physical field or projection: `maintenance_runs.runner`
- Allowed values: `claude`, `codex`
- Enforcement: `application-stored`
- Logical axis: maintenance model runner
- Default: `claude`
- Fallbacks: `null`: reject; `unknown`: label → 알 수 없는 Runner; `invalid`: reject; `future`: label → 새 Runner
- Producers: `src/localbrain/runner.py`, `src/localbrain/external_sync.py`
- Consumers: `src/localbrain/runner.py`, `src/localbrain/templates/run.html`, `src/localbrain/templates/_atlassian-item-preview.html`, `src/localbrain/templates/atlassian-connections.html`, `src/localbrain/templates/atlassian-item.html`, `src/localbrain/templates/atlassian-refresh.html`
- Consequence: Selects the local CLI invocation contract.
- Presentation mode: `logical-label`
- Labels: `claude` → Claude; `codex` → Codex
- Help: 로컬 유지관리 실행에 사용한 도구입니다.
- Visible consumer inventory: `src/localbrain/templates/run.html` (registry-backed); `src/localbrain/templates/_atlassian-item-preview.html` (registry-backed); `src/localbrain/templates/atlassian-connections.html` (registry-backed); `src/localbrain/templates/atlassian-item.html` (registry-backed); `src/localbrain/templates/atlassian-refresh.html` (registry-backed)

## `maintenance.task-type`

- Physical field or projection: `maintenance_runs.task_type`
- Allowed values: `organize_resources`, `checkpoint_draft`, `priority_review`, `external_source_sync`
- Enforcement: `application-stored`
- Logical axis: maintenance task contract
- Default: `NULL`
- Fallbacks: `null`: label → 일반 유지관리; `unknown`: label → 알 수 없는 작업; `invalid`: reject; `future`: label → 새 작업
- Producers: `src/localbrain/runner.py`, `src/localbrain/external_sync.py`
- Consumers: `src/localbrain/runner.py`, `src/localbrain/templates/run.html`, `src/localbrain/templates/workstream.html`
- Consequence: Selects prompt, result schema, and execution boundary.
- Presentation mode: `logical-label`
- Labels: `organize_resources` → 자원 연결 정리; `checkpoint_draft` → Checkpoint 초안; `priority_review` → 우선순위 검토; `external_source_sync` → 외부 소스 동기화
- Help: none
- Visible consumer inventory: `src/localbrain/templates/run.html` (registry-backed); `src/localbrain/templates/workstream.html` (registry-backed)

## `maintenance.status`

- Physical field or projection: `maintenance_runs.status`
- Allowed values: `prepared`, `queued`, `running`, `cancelling`, `cancelled`, `completed`, `partial`, `failed`, `interrupted`
- Enforcement: `application-stored`
- Logical axis: maintenance run lifecycle
- Default: `prepared`
- Fallbacks: `null`: reject; `unknown`: label → 상태 알 수 없음; `invalid`: reject; `future`: label → 새 실행 상태
- Producers: `src/localbrain/runner.py`, `src/localbrain/external_sync.py`
- Consumers: `src/localbrain/runner.py`, `src/localbrain/templates/run.html`, `src/localbrain/templates/workstream.html`, `src/localbrain/templates/_atlassian-item-preview.html`, `src/localbrain/templates/atlassian-connections.html`, `src/localbrain/templates/atlassian-item.html`, `src/localbrain/templates/atlassian-refresh.html`
- Consequence: Controls polling, cancellation, finalization, and retained evidence.
- Presentation mode: `logical-label`
- Labels: `prepared` → 준비됨; `queued` → 대기 중; `running` → 실행 중; `cancelling` → 중지 중; `cancelled` → 중지됨; `completed` → 완료; `partial` → 일부 완료; `failed` → 실패; `interrupted` → 중단됨
- Help: 로컬 유지관리 실행의 현재 또는 최종 상태입니다.
- Visible consumer inventory: `src/localbrain/templates/run.html` (registry-backed); `src/localbrain/templates/workstream.html` (registry-backed); `src/localbrain/templates/_atlassian-item-preview.html` (registry-backed); `src/localbrain/templates/atlassian-connections.html` (registry-backed); `src/localbrain/templates/atlassian-item.html` (registry-backed); `src/localbrain/templates/atlassian-refresh.html` (registry-backed)

## `maintenance.refresh-suggestions`

- Physical field or projection: `maintenance_runs.refresh_suggestions`
- Allowed values: `0`, `1`
- Enforcement: `boolean-like`
- Logical axis: suggestion refresh request
- Default: `0`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/runner.py`
- Consumers: `src/localbrain/runner.py`
- Consequence: Controls whether a Run may supersede matching pending Suggestions.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `maintenance.mcp-budget-exceeded`

- Physical field or projection: `maintenance_runs.mcp_budget_exceeded`
- Allowed values: `0`, `1`
- Enforcement: `boolean-like`
- Logical axis: external read budget result
- Default: `0`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/external_sync.py`
- Consumers: `src/localbrain/runner.py`, `src/localbrain/templates/run.html`
- Consequence: Stops additional approved MCP calls while retaining partial results.
- Presentation mode: `logical-label`
- Labels: `0` → 예산 내; `1` → 호출 예산 초과
- Help: 승인된 실행의 MCP 호출 상한을 넘었는지 나타냅니다.
- Visible consumer inventory: `src/localbrain/templates/run.html` (registry-backed)

## `external-sync.scope-kind`

- Physical field or projection: `external_sync_runs.requested_scope_kind`
- Allowed values: `item`, `space`, `thread`, `workstream`, `all_known`
- Enforcement: `schema-check`
- Logical axis: approved external read scope
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 범위 알 수 없음; `invalid`: reject; `future`: label → 새 조회 범위
- Producers: `src/localbrain/external_sync.py`
- Consumers: `src/localbrain/external_sync.py`, `src/localbrain/templates/atlassian-refresh.html`
- Consequence: Bounds target selection before any external read.
- Presentation mode: `logical-label`
- Labels: `item` → 선택한 항목; `space` → Space; `thread` → Thread; `workstream` → Workstream; `all_known` → 등록된 전체 항목
- Help: 이번 실행에서 조회하도록 승인한 범위입니다.
- Visible consumer inventory: `src/localbrain/templates/atlassian-refresh.html` (registry-backed)

## `external-sync.service`

- Physical field or projection: `external_sync_runs.service`
- Allowed values: `jira`, `confluence`
- Enforcement: `application-stored`
- Logical axis: external synchronization service
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 알 수 없는 서비스; `invalid`: reject; `future`: label → 새 서비스
- Producers: `src/localbrain/external_sync.py`
- Consumers: `src/localbrain/external_sync.py`, `src/localbrain/templates/atlassian-refresh.html`
- Consequence: Keeps the approved manifest bound to one service.
- Presentation mode: `logical-label`
- Labels: `jira` → Jira; `confluence` → Confluence
- Help: none
- Visible consumer inventory: `src/localbrain/templates/atlassian-refresh.html` (registry-backed)

## `external-sync.outcome`

- Physical field or projection: `projection:external-sync.target-outcome`
- Allowed values: `resolved`, `unchanged`, `changed`, `unavailable`, `not_found`, `error`
- Enforcement: `manifest-derived`
- Logical axis: per-target external read result
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 결과 알 수 없음; `invalid`: reject; `future`: label → 새 조회 결과
- Producers: `src/localbrain/external_sync.py`
- Consumers: `src/localbrain/external_sync.py`, `src/localbrain/templates/atlassian-refresh.html`
- Consequence: Determines partial versus completed Run status and per-target retained evidence.
- Presentation mode: `logical-label`
- Labels: `resolved` → 조회됨; `unchanged` → 변경 없음; `changed` → 변경됨; `unavailable` → 조회 불가; `not_found` → 원격에서 찾을 수 없음; `error` → 조회 오류
- Help: 각 대상의 승인된 원격 조회 결과입니다.
- Visible consumer inventory: `src/localbrain/templates/atlassian-refresh.html` (registry-backed)

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `external_sync_runs.source_kind and manifest locator/coverage vocabularies` | external synchronization protocol | Extensible protocol fields are validated by versioned manifests and are not one database presentation axis. |
