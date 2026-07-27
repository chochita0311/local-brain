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
- Producers: `src/localbrain/ingest/scanner.py`, `src/localbrain/runner.py`
- Consumers: `src/localbrain/queries.py`, `src/localbrain/retrieval.py`
- Consequence: Maintenance Sessions are excluded from ordinary user Session surfaces.
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
- Producers: `src/localbrain/ingest/scanner.py`, `src/localbrain/runner.py`
- Consumers: `src/localbrain/retrieval.py`
- Consequence: Metadata-only Sessions never expose conversation content to search.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `activity_events.event_type and activity_events.role` | source parser contracts | Open source-native event vocabulary; not a bounded product family. |
| `session_pins row presence and pinned_at` | session pin persistence | Pin state is represented by row presence and a timestamp, not by a bounded status value. |
| `numeric, range, shape, length, null-correlation, and composite CHECK constraints` | src/localbrain/schema.sql | Structural invariants are documented by table owners but do not define selectable value vocabularies. |
