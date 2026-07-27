<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Local Context corpus Value Dictionary

Durable table owner: [docs/policies/project/data-model/local-context-corpus.md](../local-context-corpus.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `context-root.source-type`

- Physical field or projection: `context_roots.source_type`
- Allowed values: `folder`, `file`, `apple_notes`
- Enforcement: `application-stored`
- Logical axis: Local Context source shape
- Default: `folder`
- Fallbacks: `null`: reject; `unknown`: label → 알 수 없는 유형; `invalid`: reject; `future`: label → 새 유형
- Producers: `src/localbrain/contexts.py`
- Consumers: `src/localbrain/contexts.py`
- Consequence: Selects the local reader and lifecycle behavior.
- Presentation mode: `logical-label`
- Labels: `folder` → 폴더; `file` → 파일; `apple_notes` → Apple Notes
- Help: Local Context를 가져오는 원본 유형입니다.
- Visible consumer inventory: none.

## `context-root.readable`

- Physical field or projection: `context_roots.readable`
- Allowed values: `0`, `1`
- Enforcement: `boolean-like`
- Logical axis: local read permission
- Default: `1`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/contexts.py`
- Consumers: `src/localbrain/contexts.py`, `src/localbrain/templates/context.html`
- Consequence: Unreadable roots are retained but cannot be scanned.
- Presentation mode: `logical-label`
- Labels: `0` → 읽을 수 없음; `1` → 읽을 수 있음
- Help: LocalBrain이 현재 원본을 읽을 수 있는지 나타냅니다.
- Visible consumer inventory: none.

## `context-root.status`

- Physical field or projection: `context_roots.status`
- Allowed values: `pending`, `ready`, `unreadable`, `error`, `missing`
- Enforcement: `application-stored`
- Logical axis: Local Context root state
- Default: `ready`
- Fallbacks: `null`: reject; `unknown`: label → 상태 알 수 없음; `invalid`: reject; `future`: label → 새 상태
- Producers: `src/localbrain/contexts.py`, `src/localbrain/ingest/scanner.py`
- Consumers: `src/localbrain/contexts.py`, `src/localbrain/templates/context.html`
- Consequence: Only ready readable roots participate in ordinary scans.
- Presentation mode: `logical-label`
- Labels: `pending` → 확인 중; `ready` → 사용 가능; `unreadable` → 읽기 권한 없음; `error` → 확인 오류; `missing` → 원본 없음
- Help: Local Context 원본의 현재 사용 가능 상태입니다.
- Visible consumer inventory: `src/localbrain/templates/context.html` (registry-backed)

## `context-root.enabled`

- Physical field or projection: `context_roots.enabled`
- Allowed values: `0`, `1`
- Enforcement: `boolean-like`
- Logical axis: Local Context scan participation
- Default: `1`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/contexts.py`
- Consumers: `src/localbrain/contexts.py`
- Consequence: Disabling removes the root from scans without deleting the original files.
- Presentation mode: `logical-label`
- Labels: `0` → 사용 안 함; `1` → 사용
- Help: 사용 안 함으로 바꾸면 로컬 원본은 삭제하지 않습니다.
- Visible consumer inventory: none.

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `context_documents.content_type` | content ingestion | Open MIME vocabulary rather than a closed product state. |
