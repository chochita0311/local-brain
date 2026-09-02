<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Source registry and scans Value Dictionary

Durable table owner: [docs/policies/project/data-model/source-registry-and-scans.md](../source-registry-and-scans.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `source.kind`

- Physical field or projection: `sources.kind`
- Allowed values: `claude`, `codex`, `codex-company`, `context`
- Enforcement: `application-stored`
- Logical axis: stable local source identity
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 알 수 없는 소스; `invalid`: reject; `future`: label → 새 소스
- Producers: `src/localbrain/ingest/scanner.py`
- Consumers: `src/localbrain/templates/sources.html`, `src/localbrain/templates/sessions.html`, `src/localbrain/templates/session.html`, `src/localbrain/templates/sessions_dashboard.html`, `src/localbrain/templates/search.html`
- Consequence: Selects source ownership, filtering, statistics, and visible provenance independently from provider behavior.
- Presentation mode: `logical-label`
- Labels: `claude` → Claude; `codex` → Codex; `codex-company` → Codex Company; `context` → Local Context
- Help: 어디에서 가져온 기록인지 나타냅니다.
- Visible consumer inventory: `src/localbrain/templates/sources.html` (registry-backed); `src/localbrain/templates/sessions.html` (registry-backed); `src/localbrain/templates/session.html` (registry-backed); `src/localbrain/templates/sessions_dashboard.html` (registry-backed); `src/localbrain/templates/search.html` (registry-backed)

## `source.provider-kind`

- Physical field or projection: `sources.provider_kind`
- Allowed values: `claude`, `codex`, `context`, `unknown`
- Enforcement: `application-stored`
- Logical axis: local source adapter family
- Default: `unknown`
- Fallbacks: `null`: reject; `unknown`: label → 알 수 없는 어댑터; `invalid`: reject; `future`: label → 새 어댑터
- Producers: `src/localbrain/ingest/scanner.py`, `src/localbrain/db.py`
- Consumers: `src/localbrain/ingest/scanner.py`, `src/localbrain/usage_queries.py`, `src/localbrain/main.py`
- Consequence: Selects parser, Usage normalizer, and provider-specific reconciliation without defining user-facing source scope.
- Presentation mode: `logical-label`
- Labels: `claude` → Claude; `codex` → Codex; `context` → Local Context; `unknown` → 알 수 없는 어댑터
- Help: 같은 어댑터를 사용하는 여러 로컬 소스를 구분해 처리합니다.
- Visible consumer inventory: none.

## `source.scan-status`

- Physical field or projection: `sources.last_scan_status`
- Allowed values: `completed`, `empty`, `unavailable`, `configuration_error`, `scan_failed`
- Enforcement: `schema-check`
- Logical axis: latest source synchronization outcome
- Default: `NULL`
- Fallbacks: `null`: label → 동기화 전; `unknown`: label → 상태 확인 필요; `invalid`: reject; `future`: label → 새 상태
- Producers: `src/localbrain/ingest/scanner.py`
- Consumers: `src/localbrain/queries.py`, `src/localbrain/usage_queries.py`, `src/localbrain/templates/sessions.html`, `src/localbrain/templates/sessions_dashboard.html`, `src/localbrain/templates/sources.html`
- Consequence: Distinguishes successful, empty, unavailable, configuration, and scan-failure outcomes without changing retained source ownership.
- Presentation mode: `logical-label`
- Labels: `completed` → 완료; `empty` → 비어 있음; `unavailable` → 경로 확인 필요; `configuration_error` → 설정 확인 필요; `scan_failed` → 동기화 실패
- Help: 마지막 동기화 시도에서 이 소스가 처리된 결과입니다.
- Visible consumer inventory: `src/localbrain/templates/sessions.html` (registry-backed); `src/localbrain/templates/sessions_dashboard.html` (registry-backed); `src/localbrain/templates/sources.html` (registry-backed)

## `source-file.status`

- Physical field or projection: `source_files.status`
- Allowed values: `ok`, `stale`, `error`
- Enforcement: `application-stored`
- Logical axis: last local scan result
- Default: `ok`
- Fallbacks: `null`: reject; `unknown`: label → 상태 확인 필요; `invalid`: reject; `future`: label → 새 상태
- Producers: `src/localbrain/ingest/scanner.py`
- Consumers: `src/localbrain/queries.py`, `src/localbrain/usage_queries.py`
- Consequence: Stale or error rows reduce freshness and require a rescan.
- Presentation mode: `logical-label`
- Labels: `ok` → 최신; `stale` → 다시 동기화 필요; `error` → 동기화 오류
- Help: 로컬 원본을 마지막으로 읽은 결과입니다.
- Visible consumer inventory: `src/localbrain/templates/sessions_dashboard.html` (registry-backed)

## `external-source.provider`

- Physical field or projection: `external_source_instances.provider_kind`
- Allowed values: `mcp_gateway`, `atlassian_cloud`
- Enforcement: `schema-check`
- Logical axis: MCP connection method
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 알 수 없는 연결 방식; `invalid`: reject; `future`: label → 새 연결 방식
- Producers: `src/localbrain/external_access.py`
- Consumers: `src/localbrain/atlassian_registration.py`, `src/localbrain/templates/atlassian-connections.html`
- Consequence: Selects the approved MCP dispatch adapter.
- Presentation mode: `logical-label`
- Labels: `mcp_gateway` → 회사 MCP Gateway; `atlassian_cloud` → 공식 Atlassian MCP
- Help: 같은 사이트도 연결 방식별로 별도 등록됩니다.
- Visible consumer inventory: `src/localbrain/templates/atlassian-connections.html` (registry-backed)

## `external-source.service`

- Physical field or projection: `external_source_instances.service`
- Allowed values: `jira`, `confluence`
- Enforcement: `schema-check`
- Logical axis: Atlassian product service
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 알 수 없는 서비스; `invalid`: reject; `future`: label → 새 서비스
- Producers: `src/localbrain/external_access.py`
- Consumers: `src/localbrain/atlassian_registration.py`, `src/localbrain/templates/atlassian-connections.html`
- Consequence: Limits calls and identities to one Atlassian service.
- Presentation mode: `logical-label`
- Labels: `jira` → Jira; `confluence` → Confluence
- Help: none
- Visible consumer inventory: none.

## `external-source.enabled`

- Physical field or projection: `external_source_instances.enabled`
- Allowed values: `0`, `1`
- Enforcement: `schema-check`
- Logical axis: registered connection availability
- Default: `1`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/external_access.py`
- Consumers: `src/localbrain/atlassian_registration.py`, `src/localbrain/templates/atlassian-connections.html`
- Consequence: Disabled connections cannot authorize external reads.
- Presentation mode: `logical-label`
- Labels: `0` → 사용 안 함; `1` → 사용
- Help: 사용 안 함으로 바꾸면 등록 정보는 유지되고 조회만 막힙니다.
- Visible consumer inventory: `src/localbrain/templates/atlassian-connections.html` (registry-backed)

## `external-capability.availability`

- Physical field or projection: `external_source_capabilities.availability`
- Allowed values: `available`, `unavailable`, `unauthorized`, `error`
- Enforcement: `schema-check`
- Logical axis: last explicit capability inspection
- Default: `NULL`
- Fallbacks: `null`: label → 확인 전; `unknown`: label → 알 수 없음; `invalid`: reject; `future`: label → 새 상태
- Producers: `src/localbrain/external_access.py`
- Consumers: `src/localbrain/external_access.py`, `src/localbrain/atlassian_registration.py`
- Consequence: Only a current available observation can authorize a read.
- Presentation mode: `logical-label`
- Labels: `available` → 사용 가능; `unavailable` → 사용 불가; `unauthorized` → 권한 없음; `error` → 확인 오류
- Help: 마지막 명시적 연결 확인 결과입니다.
- Visible consumer inventory: none.

## `external-capability.state`

- Physical field or projection: `projection:external-capability.state`
- Allowed values: `unknown`, `current`, `stale`, `disabled`, `unavailable`, `unauthorized`, `error`
- Enforcement: `derived`
- Logical axis: usable capability state
- Default: `unknown`
- Fallbacks: `null`: label → 확인 전; `unknown`: label → 확인 전; `invalid`: reject; `future`: label → 새 상태
- Producers: `src/localbrain/external_access.py`
- Consumers: `src/localbrain/atlassian_registration.py`, `src/localbrain/templates/atlassian-connections.html`, `src/localbrain/templates/atlassian-refresh.html`
- Consequence: Combines registration, freshness, and availability before dispatch.
- Presentation mode: `logical-label`
- Labels: `unknown` → 확인 전; `current` → 연결됨; `stale` → 다시 확인 필요; `disabled` → 사용 안 함; `unavailable` → 사용 불가; `unauthorized` → 권한 없음; `error` → 확인 오류
- Help: 현재 조회에 사용할 수 있는 연결인지 나타냅니다.
- Visible consumer inventory: `src/localbrain/templates/atlassian-connections.html` (registry-backed); `src/localbrain/templates/atlassian-refresh.html` (registry-backed)

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `version, fingerprint, error-code, tool-operation, capability JSON fields` | versioned protocol producers | Internal versioned protocol identifiers, not user-visible bounded database state. |
| `identifiers, paths, names, timestamps, hashes, error text, JSON payloads` | owning table producer | Free-form identity, evidence, or content fields are not bounded value families. |
