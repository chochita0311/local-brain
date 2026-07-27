<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Work organization and resources Value Dictionary

Durable table owner: [docs/policies/project/data-model/work-organization-and-resources.md](../work-organization-and-resources.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `workstream.status`

- Physical field or projection: `workstreams.status`
- Allowed values: `active`, `paused`, `done`, `archived`
- Enforcement: `application-stored`
- Logical axis: Workstream lifecycle
- Default: `active`
- Fallbacks: `null`: reject; `unknown`: label → 상태 알 수 없음; `invalid`: reject; `future`: label → 새 상태
- Producers: `src/localbrain/workstreams.py`
- Consumers: `src/localbrain/workstreams.py`, `src/localbrain/templates/dashboard.html`, `src/localbrain/templates/workstreams.html`, `src/localbrain/templates/workstream.html`
- Consequence: Affects active sorting and review visibility but does not delete links.
- Presentation mode: `logical-label`
- Labels: `active` → 진행 중; `paused` → 잠시 멈춤; `done` → 완료; `archived` → 보관됨
- Help: Workstream의 현재 진행 상태입니다.
- Visible consumer inventory: `src/localbrain/templates/dashboard.html` (registry-backed); `src/localbrain/templates/workstreams.html` (registry-backed); `src/localbrain/templates/workstream.html` (registry-backed)

## `thread.status`

- Physical field or projection: `threads.status`
- Allowed values: `active`, `blocked`, `paused`, `done`
- Enforcement: `application-stored`
- Logical axis: Thread lifecycle
- Default: `active`
- Fallbacks: `null`: reject; `unknown`: label → 상태 알 수 없음; `invalid`: reject; `future`: label → 새 상태
- Producers: `src/localbrain/workstreams.py`
- Consumers: `src/localbrain/workstreams.py`, `src/localbrain/templates/dashboard.html`
- Consequence: Controls priority and blocked-work visibility without removing evidence.
- Presentation mode: `logical-label`
- Labels: `active` → 진행 중; `blocked` → 막힘; `paused` → 잠시 멈춤; `done` → 완료
- Help: Thread의 현재 진행 상태입니다.
- Visible consumer inventory: `src/localbrain/templates/dashboard.html` (registry-backed); `src/localbrain/templates/workstream.html` (registry-backed)

## `organization-link.entity-type`

- Physical field or projection: `workstream_links.entity_type`, `thread_links.entity_type`
- Allowed values: `session`, `document`, `project`, `external`, `local`
- Enforcement: `application-stored`
- Logical axis: polymorphic linked resource
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 알 수 없는 자원; `invalid`: reject; `future`: label → 새 자원 유형
- Producers: `src/localbrain/workstreams.py`
- Consumers: `src/localbrain/workstreams.py`, `src/localbrain/templates/workstream.html`
- Consequence: Selects the target table for application-enforced links.
- Presentation mode: `logical-label`
- Labels: `session` → Session; `document` → Local Context 문서; `project` → Project; `external` → 외부 자원; `local` → 로컬 자원
- Help: Workstream 또는 Thread에 연결된 자원 유형입니다.
- Visible consumer inventory: `src/localbrain/templates/workstream.html` (registry-backed)

## `external-resource.type`

- Physical field or projection: `external_resources.resource_type`
- Allowed values: `jira`, `wiki`, `slack`, `git`, `document`, `url`
- Enforcement: `application-stored`
- Logical axis: external resource family
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 기타 외부 자원; `invalid`: reject; `future`: label → 새 외부 자원
- Producers: `src/localbrain/workstreams.py`, `src/localbrain/atlassian.py`
- Consumers: `src/localbrain/workstreams.py`, `src/localbrain/templates/workstream.html`
- Consequence: Selects detail routing and resource labeling.
- Presentation mode: `logical-label`
- Labels: `jira` → Jira; `wiki` → Wiki; `slack` → Slack; `git` → Git; `document` → 외부 문서; `url` → 웹 링크
- Help: none
- Visible consumer inventory: `src/localbrain/templates/workstream.html` (registry-backed)

## `local-resource.type`

- Physical field or projection: `local_resources.resource_type`
- Allowed values: `repository`, `directory`, `file`, `path`
- Enforcement: `application-stored`
- Logical axis: local resource shape
- Default: `path`
- Fallbacks: `null`: reject; `unknown`: label → 로컬 경로; `invalid`: reject; `future`: label → 새 로컬 자원
- Producers: `src/localbrain/workstreams.py`
- Consumers: `src/localbrain/workstreams.py`, `src/localbrain/templates/local_resource.html`
- Consequence: Controls local resource iconography and path behavior.
- Presentation mode: `logical-label`
- Labels: `repository` → 로컬 Repository; `directory` → 로컬 폴더; `file` → 로컬 파일; `path` → 로컬 경로
- Help: none
- Visible consumer inventory: `src/localbrain/templates/local_resource.html` (registry-backed); `src/localbrain/templates/workstream.html` (registry-backed)

## `local-resource.exists-now`

- Physical field or projection: `local_resources.exists_now`
- Allowed values: `0`, `1`
- Enforcement: `boolean-like`
- Logical axis: current local target existence
- Default: `0`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/workstreams.py`
- Consumers: `src/localbrain/retrieval.py`, `src/localbrain/templates/local_resource.html`
- Consequence: Missing resources remain as historical references but cannot be opened.
- Presentation mode: `logical-label`
- Labels: `0` → 현재 경로 없음; `1` → 현재 경로 있음
- Help: 마지막 확인 시점의 로컬 경로 존재 여부입니다.
- Visible consumer inventory: `src/localbrain/templates/local_resource.html` (registry-backed)

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `*.relation_type, *.source_role, *.linked_by, local_resources.discovered_by` | provenance and relationship producers | Open provenance or semantic relationship strings; validation is contextual rather than one closed family. |
