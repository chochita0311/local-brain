<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Workspace and Session activity Value Dictionary

Durable table owner: [docs/policies/project/data-model/workspace-and-session-activity.md](../workspace-and-session-activity.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `workspace.exists-now`

- Physical field or projection: `workspaces.exists_now`
- Allowed values: `0`, `1`
- Enforcement: `boolean-like`
- Logical axis: current local path existence
- Default: `0`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/ingest/scanner.py`
- Consumers: `src/localbrain/queries.py`, `src/localbrain/templates/sessions.html`, `src/localbrain/templates/session.html`
- Consequence: Missing paths remain historical but cannot be opened locally.
- Presentation mode: `logical-label`
- Labels: `0` → 현재 경로 없음; `1` → 현재 경로 있음
- Help: 마지막 스캔 시점의 로컬 경로 존재 여부입니다.
- Visible consumer inventory: `src/localbrain/templates/sessions.html` (registry-backed); `src/localbrain/templates/session.html` (registry-backed)

## `session.class`

- Physical field or projection: `sessions.session_class`
- Allowed values: `work`, `maintenance`
- Enforcement: `schema-check`
- Logical axis: session ownership class
- Default: `work`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/ingest/codex.py`, `src/localbrain/ingest/scanner.py`, `src/localbrain/runner.py`
- Consumers: `src/localbrain/queries.py`, `src/localbrain/retrieval.py`
- Consequence: Maintenance Sessions, including recognized provider-internal helpers, are excluded from ordinary user Session surfaces.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `session.role`

- Physical field or projection: `sessions.session_role`
- Allowed values: `primary`, `subsession`
- Enforcement: `schema-check`
- Logical axis: session hierarchy role
- Default: `primary`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/ingest/claude.py`, `src/localbrain/ingest/codex.py`
- Consumers: `src/localbrain/queries.py`, `src/localbrain/templates/sessions.html`, `src/localbrain/templates/session.html`, `src/localbrain/templates/subsession.html`
- Consequence: Controls top-level inventory placement and Subsession navigation.
- Presentation mode: `logical-label`
- Labels: `primary` → Session; `subsession` → Subsession
- Help: 원본 대화 계층에서의 역할입니다.
- Visible consumer inventory: `src/localbrain/templates/sessions.html` (registry-backed); `src/localbrain/templates/session.html` (registry-backed); `src/localbrain/templates/subsession.html` (registry-backed)

## `session.index-policy`

- Physical field or projection: `sessions.index_policy`
- Allowed values: `full`, `metadata_only`
- Enforcement: `schema-check`
- Logical axis: search indexing policy
- Default: `full`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/ingest/codex.py`, `src/localbrain/ingest/scanner.py`, `src/localbrain/runner.py`
- Consumers: `src/localbrain/retrieval.py`
- Consequence: Metadata-only Sessions never expose conversation content to search.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `session-reference-scan.status`

- Physical field or projection: `session_reference_scans.status`
- Allowed values: `ok`, `partial`, `error`
- Enforcement: `schema-check`
- Logical axis: Session reference reconciliation state
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/ingest/scanner.py`
- Consumers: `src/localbrain/queries.py`
- Consequence: Distinguishes complete, safety-bounded, and stale-after-error reference evidence.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `session-reference.target-kind`

- Physical field or projection: `session_reference_evidence.target_kind`
- Allowed values: `url`, `context_document`, `atlassian_item`
- Enforcement: `schema-check`
- Logical axis: Session reference target family
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/ingest/scanner.py`
- Consumers: `src/localbrain/queries.py`
- Consequence: Selects generic URL, exact Context Document, or configured Atlassian Item identity.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `session-reference.evidence-kind`

- Physical field or projection: `session_reference_evidence.evidence_kind`
- Allowed values: `user_mention`, `assistant_mention`, `tool_result`, `resource_read`
- Enforcement: `schema-check`
- Logical axis: Session reference evidence provenance
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 참조 근거 알 수 없음; `invalid`: reject; `future`: label → 새 참조 근거
- Producers: `src/localbrain/ingest/scanner.py`
- Consumers: `src/localbrain/queries.py`
- Consequence: Explains whether the Session mentioned, observed, or read the target.
- Presentation mode: `logical-label`
- Labels: `user_mention` → 사용자 메시지에서 언급; `assistant_mention` → Agent 응답에서 언급; `tool_result` → 도구 결과에서 확인; `resource_read` → MCP 조회
- Help: 이 세션에서 해당 자료를 확인한 근거입니다.
- Visible consumer inventory: none.

## `session-reference.read-outcome`

- Physical field or projection: `session_reference_evidence.read_outcome`
- Allowed values: `success`, `failure`
- Enforcement: `schema-check`
- Logical axis: completed approved resource read outcome
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 조회 결과 알 수 없음; `invalid`: reject; `future`: label → 새 조회 결과
- Producers: `src/localbrain/ingest/scanner.py`
- Consumers: `src/localbrain/queries.py`
- Consequence: A success requires one matched completed non-error call; failure never implies remote content or freshness.
- Presentation mode: `logical-label`
- Labels: `success` → MCP 조회; `failure` → MCP 조회 실패
- Help: 승인된 MCP 조회 시도의 완료 결과입니다.
- Visible consumer inventory: none.

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `activity_events.event_type and activity_events.role` | source parser contracts | Open source-native event vocabulary; not a bounded product family. |
| `session_pins row presence and pinned_at` | session pin persistence | Pin state is represented by row presence and a timestamp, not by a bounded status value. |
| `numeric, range, shape, length, null-correlation, and composite CHECK constraints` | src/localbrain/schema.sql | Structural invariants are documented by table owners but do not define selectable value vocabularies. |
