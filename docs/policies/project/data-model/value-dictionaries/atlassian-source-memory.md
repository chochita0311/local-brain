<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Atlassian source memory Value Dictionary

Durable table owner: [docs/policies/project/data-model/atlassian-source-memory.md](../atlassian-source-memory.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `atlassian-space.service`

- Physical field or projection: `atlassian_spaces.service`, `atlassian_items.service`, `atlassian_structure_references.service`
- Allowed values: `jira`, `confluence`
- Enforcement: `schema-check`
- Logical axis: Atlassian content service
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 알 수 없는 서비스; `invalid`: reject; `future`: label → 새 서비스
- Producers: `src/localbrain/atlassian.py`, `src/localbrain/atlassian_registration.py`, `src/localbrain/atlassian_structure_references.py`
- Consumers: `src/localbrain/atlassian_browse.py`, `src/localbrain/atlassian_structure_references.py`, `src/localbrain/templates/atlassian.html`, `src/localbrain/templates/atlassian-connections.html`, `src/localbrain/templates/search.html`
- Consequence: Keeps Space, Item, and URL-derived structure-reference identity service-scoped.
- Presentation mode: `logical-label`
- Labels: `jira` → Jira; `confluence` → Confluence
- Help: none
- Visible consumer inventory: `src/localbrain/templates/search.html` (registry-backed)

## `atlassian-structure-reference.kind`

- Physical field or projection: `atlassian_structure_references.reference_kind`
- Allowed values: `jira_project`, `jira_board`, `jira_filter`, `jira_dashboard`, `jira_service_portal`, `jira_service_project`, `confluence_space`
- Enforcement: `schema-check`
- Logical axis: URL-derived Atlassian structure family
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/atlassian_structure_references.py`
- Consumers: `src/localbrain/atlassian_structure_references.py`, `src/localbrain/atlassian_browse.py`
- Consequence: Selects stable semantic identity, family label, and read-only Explorer/Search projection without creating an Item or Space.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `atlassian-space.coverage`

- Physical field or projection: `atlassian_spaces.coverage`
- Allowed values: `selected-content`, `full-content`
- Enforcement: `schema-check`
- Logical axis: Space management coverage
- Default: `selected-content`
- Fallbacks: `null`: reject; `unknown`: label → 범위 알 수 없음; `invalid`: reject; `future`: label → 새 관리 범위
- Producers: `src/localbrain/atlassian_registration.py`
- Consumers: `src/localbrain/atlassian_registration.py`, `src/localbrain/templates/atlassian-connections.html`, `src/localbrain/templates/atlassian-refresh.html`
- Consequence: Selected content limits management to explicitly registered Items; full content permits Space-wide inventory.
- Presentation mode: `logical-label`
- Labels: `selected-content` → 선택한 항목만; `full-content` → Space 전체
- Help: none
- Visible consumer inventory: `src/localbrain/templates/atlassian-connections.html` (registry-backed); `src/localbrain/templates/atlassian-refresh.html` (registry-backed)

## `atlassian-item.type`

- Physical field or projection: `atlassian_items.item_type`
- Allowed values: `jira_issue`, `confluence_page`
- Enforcement: `schema-check`
- Logical axis: Atlassian Item shape
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 알 수 없는 항목; `invalid`: reject; `future`: label → 새 항목 유형
- Producers: `src/localbrain/atlassian.py`
- Consumers: `src/localbrain/atlassian_browse.py`, `src/localbrain/templates/_atlassian-item-preview.html`, `src/localbrain/templates/atlassian-item.html`, `src/localbrain/templates/search.html`
- Consequence: Selects identity validation and detail semantics.
- Presentation mode: `logical-label`
- Labels: `jira_issue` → Jira 티켓; `confluence_page` → Confluence Page
- Help: none
- Visible consumer inventory: `src/localbrain/templates/_atlassian-item-preview.html` (registry-backed); `src/localbrain/templates/atlassian-item.html` (registry-backed); `src/localbrain/templates/search.html` (registry-backed)

## `atlassian-item.coverage`

- Physical field or projection: `atlassian_items.coverage`
- Allowed values: `reference`, `metadata`, `indexed`
- Enforcement: `schema-check`
- Logical axis: locally retained content coverage
- Default: `reference`
- Fallbacks: `null`: reject; `unknown`: label → 범위 알 수 없음; `invalid`: reject; `future`: label → 새 저장 범위
- Producers: `src/localbrain/atlassian.py`
- Consumers: `src/localbrain/atlassian_browse.py`, `src/localbrain/templates/_atlassian-item-preview.html`, `src/localbrain/templates/atlassian.html`, `src/localbrain/templates/atlassian-item.html`, `src/localbrain/templates/atlassian-refresh.html`, `src/localbrain/templates/search.html`
- Consequence: Reference stores identity only, metadata stores bounded fields, indexed also stores approved normalized content.
- Presentation mode: `logical-label`
- Labels: `reference` → 링크만; `metadata` → 기본 정보; `indexed` → 본문 검색 가능
- Help: LocalBrain DB에 보관하는 정보의 범위입니다.
- Visible consumer inventory: `src/localbrain/templates/_atlassian-item-preview.html` (registry-backed); `src/localbrain/templates/atlassian.html` (registry-backed); `src/localbrain/templates/atlassian-item.html` (registry-backed); `src/localbrain/templates/atlassian-refresh.html` (registry-backed); `src/localbrain/templates/search.html` (registry-backed)

## `atlassian-item.attention`

- Physical field or projection: `atlassian_items.attention`
- Allowed values: `normal`, `pinned`, `ignored`, `archived`
- Enforcement: `schema-check`
- Logical axis: owner attention state
- Default: `normal`
- Fallbacks: `null`: reject; `unknown`: label → 상태 알 수 없음; `invalid`: reject; `future`: label → 새 관심 상태
- Producers: `src/localbrain/atlassian_browse.py`
- Consumers: `src/localbrain/atlassian_browse.py`, `src/localbrain/templates/_atlassian-item-preview.html`, `src/localbrain/templates/atlassian.html`, `src/localbrain/templates/atlassian-item.html`, `src/localbrain/templates/search.html`
- Consequence: Pinned sorts first; archived is hidden from ordinary browse unless explicitly requested.
- Presentation mode: `logical-label`
- Labels: `normal` → 일반; `pinned` → 고정됨; `ignored` → 관심 없음; `archived` → 보관됨
- Help: 로컬에서만 관리되는 관심 상태입니다.
- Visible consumer inventory: `src/localbrain/templates/_atlassian-item-preview.html` (registry-backed); `src/localbrain/templates/atlassian.html` (registry-backed); `src/localbrain/templates/atlassian-item.html` (registry-backed); `src/localbrain/templates/search.html` (registry-backed)

## `atlassian-item.url-role`

- Physical field or projection: `atlassian_item_urls.url_role`, `atlassian_structure_reference_urls.url_role`
- Allowed values: `canonical`, `alias`
- Enforcement: `schema-check`
- Logical axis: normalized URL identity role
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/atlassian.py`, `src/localbrain/atlassian_structure_references.py`
- Consumers: `src/localbrain/atlassian.py`, `src/localbrain/atlassian_structure_references.py`
- Consequence: Canonical URL is the stable display target while Item and structure-reference aliases preserve observed identity.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `atlassian-item.remote-outcome`

- Physical field or projection: `atlassian_item_remote_state.last_outcome`
- Allowed values: `resolved`, `unchanged`, `changed`, `unavailable`, `not_found`, `error`
- Enforcement: `schema-check`
- Logical axis: last approved remote read result
- Default: `NULL`
- Fallbacks: `null`: label → 조회 전; `unknown`: label → 결과 알 수 없음; `invalid`: reject; `future`: label → 새 조회 결과
- Producers: `src/localbrain/atlassian.py`, `src/localbrain/external_sync.py`
- Consumers: `src/localbrain/atlassian.py`, `src/localbrain/templates/_atlassian-item-preview.html`, `src/localbrain/templates/atlassian-item.html`, `src/localbrain/templates/atlassian-refresh.html`
- Consequence: Failures retain prior known data and expose a bounded error state.
- Presentation mode: `logical-label`
- Labels: `resolved` → 조회됨; `unchanged` → 변경 없음; `changed` → 변경됨; `unavailable` → 조회 불가; `not_found` → 원격에서 찾을 수 없음; `error` → 조회 오류
- Help: 마지막으로 승인한 원격 조회의 결과입니다.
- Visible consumer inventory: `src/localbrain/templates/_atlassian-item-preview.html` (registry-backed); `src/localbrain/templates/atlassian-item.html` (registry-backed); `src/localbrain/templates/atlassian-refresh.html` (registry-backed)

## `atlassian-item.known-changed`

- Physical field or projection: `atlassian_item_remote_state.known_changed`
- Allowed values: `0`, `1`
- Enforcement: `schema-check`
- Logical axis: known remote change marker
- Default: `0`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/atlassian.py`
- Consumers: `src/localbrain/atlassian.py`
- Consequence: Marks an observed change without replacing local user state.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `atlassian-item.projection-stale`

- Physical field or projection: `atlassian_item_remote_state.projection_stale`
- Allowed values: `0`, `1`
- Enforcement: `schema-check`
- Logical axis: search projection repair marker
- Default: `0`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/atlassian.py`
- Consumers: `src/localbrain/atlassian.py`
- Consequence: Requests deterministic local projection repair.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `atlassian-content.source-format`

- Physical field or projection: `atlassian_item_content.source_format`
- Allowed values: `jira_adf`, `confluence_adf`, `confluence_html`, `confluence_markdown`, `plain_text`
- Enforcement: `schema-check`
- Logical axis: approved source body format
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/atlassian.py`
- Consumers: `src/localbrain/atlassian.py`
- Consequence: Selects the safe normalizer before text is indexed.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `atlassian-classification.kind`

- Physical field or projection: `atlassian_classifications.kind`
- Allowed values: `topic`, `tag`
- Enforcement: `schema-check`
- Logical axis: local classification kind
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: label → 분류; `invalid`: reject; `future`: label → 새 분류
- Producers: `src/localbrain/atlassian_browse.py`
- Consumers: `src/localbrain/atlassian_browse.py`, `src/localbrain/templates/atlassian-item.html`
- Consequence: Topics may carry descriptions; Tags remain name-only.
- Presentation mode: `logical-label`
- Labels: `topic` → Topic; `tag` → Tag
- Help: LocalBrain 안에서만 관리되는 분류입니다.
- Visible consumer inventory: `src/localbrain/templates/atlassian-item.html` (registry-backed)

## `atlassian-evidence-scan.status`

- Physical field or projection: `atlassian_evidence_scans.status`
- Allowed values: `ok`, `error`
- Enforcement: `schema-check`
- Logical axis: local evidence extraction result
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/atlassian_evidence.py`
- Consumers: `src/localbrain/atlassian_evidence.py`
- Consequence: Errors preserve bounded diagnostics without creating unconfirmed Items.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `atlassian-evidence.source-channel`

- Physical field or projection: `atlassian_item_evidence.source_channel`, `atlassian_structure_reference_evidence.source_channel`
- Allowed values: `visible_text`, `approved_tool_result`
- Enforcement: `schema-check`
- Logical axis: evidence provenance channel
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/atlassian_evidence.py`, `src/localbrain/atlassian_structure_references.py`
- Consumers: `src/localbrain/atlassian_evidence.py`, `src/localbrain/atlassian_structure_references.py`
- Consequence: Only visible text and explicitly approved tool results may produce evidence.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## `atlassian-item.freshness`

- Physical field or projection: `projection:atlassian-item.freshness`
- Allowed values: `unknown`, `current`, `due`, `stale`, `unavailable`
- Enforcement: `derived`
- Logical axis: remote memory freshness
- Default: `unknown`
- Fallbacks: `null`: label → 조회 전; `unknown`: label → 조회 전; `invalid`: reject; `future`: label → 새 상태
- Producers: `src/localbrain/atlassian.py`
- Consumers: `src/localbrain/atlassian_browse.py`, `src/localbrain/templates/_atlassian-item-preview.html`, `src/localbrain/templates/atlassian.html`, `src/localbrain/templates/atlassian-item.html`, `src/localbrain/templates/atlassian-refresh.html`, `src/localbrain/templates/search.html`
- Consequence: Due and stale invite an explicit refresh; unavailable retains last-known facts.
- Presentation mode: `logical-label`
- Labels: `unknown` → 조회 전; `current` → 최신; `due` → 조회 권장; `stale` → 다시 조회 필요; `unavailable` → 조회 불가
- Help: 마지막 승인 조회와 서비스별 주기를 기준으로 계산합니다.
- Visible consumer inventory: `src/localbrain/templates/_atlassian-item-preview.html` (registry-backed); `src/localbrain/templates/atlassian.html` (registry-backed); `src/localbrain/templates/atlassian-item.html` (registry-backed); `src/localbrain/templates/atlassian-refresh.html` (registry-backed); `src/localbrain/templates/search.html` (registry-backed)

## Explicit Exclusions

No subject-specific exclusions.
