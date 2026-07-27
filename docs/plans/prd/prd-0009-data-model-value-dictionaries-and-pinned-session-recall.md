# PRD-0009: Data Model Value Dictionaries And Pinned Session Recall

## Metadata

- ID: `prd-0009`
- Status: `passed`
- Owner role: `human`
- Created: `2026-07-24`
- Updated: `2026-07-27`
- User review status: `confirmed`
- Approval mode: `strict`
- Canonical passed boundary: this PRD

## Request Summary

- Create subject-owned definitions for database-related bounded values so physical storage tokens, logical meanings, and user-facing terms no longer drift or leak into screens accidentally.
- Let the owner pin important primary work Sessions and replace the generic `최근 컨텍스트` panel on the Sessions inventory with quick access to those pinned Sessions.
- Move context orientation to Session detail, where a right-side rail shows context related to the selected Session through existing local relationships rather than global recency.
- Keep the value-dictionary foundation and Session continuity work as separate Feature lanes under one approved PRD. No lane authorizes Spec or implementation work before its individual Feature is approved.

## Workflow Scope

- Workflow root and current repository: LocalBrain.
- Related repositories: none.
- Value-dictionary scope: the nine subject areas owned by [Data Model](../../policies/project/data-model.md).
- Product surfaces: `/sessions`, `/sessions/{session_id}`, corresponding server read models and local mutation routes, and ordinary screens that consume bounded value families.
- Execution profiles expected after Feature approval:
  - value dictionaries: `Docs Content` plus `Foundation Contract` where automated parity is required;
  - pin persistence and Session surfaces: `Fullstack Product`.

## Source Set

| Source ID | Type | Location | Role | Freshness | Owner or update path |
| --- | --- | --- | --- | --- | --- |
| `human-20260724-value-and-pin-direction` | other | current owner direction summarized in this PRD | primary product direction | current through `2026-07-24` | human PRD review |
| `data-model-entry` | policy | [Data Model](../../policies/project/data-model.md) and its nine subject owner documents | current physical, semantic, lifecycle, and recovery ownership | checked `2026-07-24` | `docs/policies/project/data-model*` |
| `schema-implementation` | repo | `src/localbrain/schema.sql`, `db.py`, and application-enforced value constants | physical and compatible implementation truth | checked `2026-07-24` | current repository code |
| `design-state-contract` | policy | [Design Constitution](../../policies/design/design-constitution.md), [Design Evaluation](../../policies/design/design-evaluation.md), and [Interaction Evaluation](../../policies/experience/interaction-evaluation.md) | presentation, responsive, provenance, and interaction constraints | checked `2026-07-24` | design and experience policy owners |
| `prd-0002` | doc | [Session Browsing And Subsession Organization](prd-0002-session-browsing-and-subsession-organization.md) | passed Sessions inventory/detail and source-neutral hierarchy boundary | checked `2026-07-24` | PRD-0002 and its passed Features |
| `prd-0006` | doc | [Markdown Reading And Context Continuity](prd-0006-markdown-reading-and-context-continuity.md) | passed Session and Local Context reading behavior | checked `2026-07-24` | PRD-0006 and its passed Features |
| `prd-0008` | doc | [Connected Atlassian Validation And Schema ERD Routing](prd-0008-connected-atlassian-validation-and-schema-erd-routing.md) | consumer requirement and source of the value-dictionary split | checked `2026-07-24` | PRD-0008 |
| `sessions-implementation` | repo | `src/localbrain/queries.py`, `workstreams.py`, `main.py`, `templates/sessions.html`, `templates/session.html`, and focused tests | current Sessions behavior | checked `2026-07-24` | current repository code |

## Source Relationships And Truth Rules

- PRD-0009 owns the new cross-subject value-dictionary planning boundary split from PRD-0008. PRD-0008 may consume an approved dictionary but does not author the nine-subject foundation.
- PRD-0009 follows PRD-0002 without reopening its accepted Sessions/Projects navigation, pagination, source filters, primary/subsession organization, or conversation-focused detail behavior.
- PRD-0009 follows PRD-0006 without moving Local Context ownership into Sessions or duplicating document bodies.
- `schema.sql` and compatible startup own physical values and constraints. Subject owner documents own durable meaning. Approved value dictionaries own the physical/logical/presentation mapping; product templates must not parse Markdown at runtime.
- Source-native Claude and Codex files own Session facts. Pin state is local user intent and must not be written into, inferred from, or overwritten by those files.
- Related context on Session detail is a local projection unless a later approved boundary introduces an explicit user-managed relationship. It does not become new source truth merely because it appears near a Session.

## Reconciliation Notes

| Topic | Source claims | Status | Working decision | Follow-up target |
| --- | --- | --- | --- | --- |
| Enum terminology | Physical values such as `selected-content` may be precise for storage but unclear as screen copy. Some complete value families such as a product-safe status vocabulary may already be understandable. | `aligned` | Assign one presentation mode to the complete enum column or bounded value family: `direct`, `logical-label`, or `internal-only`. | value-dictionary Foundation Feature |
| Mapping completeness | Mixing translated and untranslated values inside one family creates inconsistent UI and raw-token fallback. | `aligned` | A logical-label family maps every allowed value and every permitted fallback state; missing mappings fail validation. | dictionary contract and consumer checks |
| Documentation ownership | Current subject documents already own tables, fields, lifecycle, and recovery. Repeating those contracts in one global enum appendix would create drift. | `aligned` | Add one companion value dictionary per existing data-model subject plus a small entry index and reciprocal links. | docs structure Feature |
| Session pin ownership | `sessions` is source-derived, while a pin is non-rebuildable local intent. No existing table owns this state. | `aligned` | Add a separate one-to-one user-owned pin record instead of placing a mutable pin flag in the source-derived Session row. | pin persistence Foundation Feature |
| Recent context placement | `/sessions` currently renders the eight most recently modified Context Documents regardless of the visible Sessions. The owner prefers quick access to chosen Sessions there. | `aligned` | Replace the inventory-side generic recent-document panel with pinned Sessions. Keep Context browsing under its existing owner. | pinned inventory Product Feature |
| Session-row utility geometry | The current Subsession menu is a conditional outer grid column, so rows with and without Subsessions allocate different right-side widths and their dates do not share one stable alignment. Question and event counts also remain detached in the main metadata flow. | `aligned` | Give every eligible Session row one reserved trailing utility layer. Order question count, event count, date, and pin from left to right at its top edge, and conditionally anchor the Subsession control at its bottom edge without changing the layer width. | pinned inventory Product Feature |
| Session-related context | Existing workspace IDs, Workstream/Thread links, and Session-backed Atlassian evidence can explain why context is related without a new relation table. | `aligned` | Build the initial detail rail as a deterministic local projection with visible relationship reasons. No new relationship schema is required for this first boundary. | related-context Product Feature |
| Native Session resume | A pin improves LocalBrain recall, but current implementation truth does not provide a source-neutral action that resumes the native Claude or Codex process. | `aligned` | This PRD guarantees quick access to LocalBrain Session detail and explicitly defers native resume. | separately approved future Feature |

## Schema Impact Decision

- Session pinning requires a schema extension because it is durable, user-curated state that source rescans cannot reconstruct. The approved direction is a separate one-to-one user-owned pin record linked to the stable Session identity.
- The initial Session-detail related-context rail does not require a new relationship schema. It is a read projection over current workspace, Workstream/Thread, and Atlassian Session-evidence relationships.
- A later request for manual Session-to-context curation, accepted inferred relevance, manual pin ordering, or native Claude/Codex resume metadata would require a separate schema and planning decision.

## Product Intent

- Make database state understandable without conflating machine storage tokens with product language.
- Give the owner a stable shortlist of Sessions worth returning to instead of a generic recency feed.
- Put context beside the Session that gives it meaning, with explicit local relationship reasons and no hidden external or model work.
- Preserve source facts, local intent, and derived context as separate owners.

## Confirmed Scope

### Subject-Oriented Value Dictionaries

- Create a value-dictionary entrance under `docs/policies/project/data-model/` and one companion definition document for each of the nine current subject areas:
  - Source registry and scans;
  - Workspace and Session activity;
  - Usage and cost records;
  - Local Context corpus;
  - Work organization and resources;
  - Atlassian source memory;
  - Review and resume continuity;
  - Maintenance execution;
  - Derived retrieval index.
- Keep the existing subject catalog as owner of table, column, lifecycle, deletion, recovery, and relation facts. Each subject catalog links to its companion value dictionary, and the Data Model entry links to the dictionary entrance.
- Inventory database-related bounded value families across:
  - physical `CHECK` vocabularies and boolean-like state fields;
  - application-enforced values stored in database columns;
  - derived values shown as database-backed state even when the label itself is not persisted;
  - versioned manifest or projection values only when a database owner stores or exposes them.
- For every included column or value family, define:
  - physical field and allowed storage values;
  - persisted, application-enforced, or derived classification;
  - logical axis and meaning;
  - default, null, unknown, invalid, and future-value behavior where applicable;
  - producer, consumer, and enforcement owner;
  - transition or behavioral consequence when it materially affects the user;
  - one presentation mode for the complete family;
  - complete user-facing labels and bounded help copy when the mode requires them;
  - technical-only visibility and diagnostic exceptions where applicable.
- Use exactly one presentation mode per column or bounded value family:
  - `direct`: every allowed value renders directly;
  - `logical-label`: every allowed value renders through an exhaustive logical mapping;
  - `internal-only`: no value from the family appears on ordinary product screens.
- Never mix raw and logical labels within one family. If one allowed value needs interpretation, the complete family uses logical labels.
- Treat important consequence copy separately from the short label. A label does not need to encode destructive effects, remote reads, loss of coverage, or recovery behavior if bounded nearby help text owns that explanation.
- Add deterministic checks that compare covered physical vocabularies and application constants with the dictionary contract and fail on missing logical-label mappings or unintended raw-token fallback.
- Keep physical storage values unchanged unless a later separately approved migration explicitly changes them.

### Pinned Session Persistence

- Support explicit pin and unpin actions for eligible Sessions without modifying Claude JSONL, Codex JSONL, project files, or external tool state.
- Store pin state as separate local user intent rather than a source-derived Session attribute.
- The expected minimal contract is a one-to-one table such as `session_pins` with:
  - `session_id` as primary key and FK to `sessions.id`;
  - `pinned_at` as the current pin-interval timestamp and stable tie-break after displayed Session activity.
- Normal Session rescans and metadata updates preserve a pin because they update the stable Session identity rather than replacing local state.
- Explicit unpin removes only the pin record. It does not delete or edit the Session.
- Explicit source or Session deletion may cascade its pin because no reopenable Session remains. Recovery of current pins requires the LocalBrain database backup; rescanning source files alone cannot reconstruct user intent.
- Pin eligibility is limited to persisted primary work Sessions. Subsessions and Maintenance Sessions remain ineligible.

### Pinned Sessions Inventory

- Remove the generic `최근 컨텍스트` document panel from the Sessions inventory.
- Use that secondary inventory region for a `Pinned Sessions` panel that provides direct access to pinned Session detail.
- The pinned panel is global owner-curated recall, not a recency calculation and not an automatic recommendation.
- Each pinned entry identifies Session title, Claude/Codex provenance, last activity, and enough workspace/path context to distinguish similar titles.
- Expose an accessible pin/unpin control from the Session row or an equally direct inventory affordance and from persisted Session detail.
- On the Sessions inventory, reserve one stable trailing utility layer for every eligible Session row so title and metadata width, date position, and row height do not change according to whether Subsessions exist.
- At desktop and laptop widths, move question and event counts into the utility layer's upper row and order that row as `질문 → 이벤트 → 날짜 → 핀`, with the pin at the outer corner. Keep the Subsession trigger anchored to the lower trailing edge only when children exist.
- The pin control is a separate button rather than part of the Session destination link. The Subsession trigger remains a separate control, and clicking either utility must not navigate to the parent Session.
- Use a pin glyph with an accessible `핀 고정` or `핀 해제` name and `aria-pressed` state. A pinned button uses a stable filled glyph while its transparent hit area follows the owning surface and keeps the same geometry; color alone must not communicate the state.
- Pinning and unpinning must not change the button box, utility-layer width, date alignment, or row height.
- At narrow widths, preserve the same relative placement across rows but simplify before compressing the title. The pin remains at the upper trailing edge; question count, event count, and date may enter a wrapping metadata flow but keep that order, and the Subsession trigger remains at the lower trailing edge with the required touch target.
- Pin/unpin completion preserves the current source filter, workspace filter, page, scroll/focus orientation, and Sessions/Projects inventory mode where applicable.
- The empty state explains how to pin a Session and does not repopulate itself with recent documents or generated suggestions.
- Expose every current pin without a silent item cap. Wide layouts use a `420px` bounded internal scroller, narrow layouts keep pins in ordinary document flow, and ordering follows displayed Session activity with `pinned_at DESC, session_id DESC` tie-breaks.

### Session Detail Related Context

- Add a right-side `Related Context` rail to persisted Session detail and remove global recent-document context from the Sessions inventory.
- Build the initial rail only from current local database relationships and deterministic projections:
  - enabled Local Context Documents resolved to the same `workspace_id`;
  - Documents or Resources sharing an explicit Workstream or Thread membership with the Session;
  - registered Atlassian Items whose existing evidence points to the Session, when such Items are eligible for local display.
- Deduplicate one target reached through multiple reasons and display the strongest or complete bounded reason set, such as `같은 프로젝트`, `같은 Workstream`, `같은 Thread`, or `이 Session에서 참조`.
- Do not use global modification recency as sufficient relatedness.
- Do not start a model call, embedding request, external read, source scan, capability inspection, or maintenance Run when loading Session detail.
- Keep source provenance and unavailable state visible. A related item remains owned by its existing detail route and is not copied into Session storage.
- On compact and narrow viewports, the rail enters document flow after Session identity and orientation and before the conversation; it must not shrink the conversation below a readable width or trap focus.
- The initial rail does not require a new relationship table. If later review requests user-curated related-context membership or inferred relevance acceptance, that is a new schema and planning decision.

## Excluded Scope

- Changing physical enum values, renaming columns, or migrating stored rows merely to improve screen copy.
- A runtime localization framework or translating arbitrary database text.
- Parsing Markdown value dictionaries at request time.
- Allowing one translated value and one raw value from the same column/value family on ordinary screens.
- Pinning Maintenance Sessions, Workstreams, Documents, Atlassian Items, or arbitrary external resources under this Session-specific pin contract.
- Writing pin state to source JSONL, Claude/Codex configuration, Git, project files, or an external service.
- Claiming that opening a LocalBrain Session detail resumes a native Claude or Codex execution.
- Automatically pinning recent, active, expensive, long, or frequently opened Sessions.
- Treating global recent Context Documents as Session-related merely because they were modified recently.
- LLM, embedding, remote-search, or hidden synchronization calls for the detail context rail.
- New user-curated Session-to-context relationships or generated Suggestions in the initial related-context boundary.
- Reopening PRD-0002 pagination, primary/subsession classification, tool-call hiding, Session source normalization, or Sessions/Projects navigation.

## Resolved Decisions And Deferred Scope

No open question remains inside the passed PRD-0009 boundary.

### Value Dictionaries

- The repository-owned package JSON registry is the executable authority. The nine subject dictionaries are generated deterministically from that registry, and runtime templates and request handlers never parse Markdown.
- Relevant boolean-like fields are included when they own a bounded database-backed state. Open or versioned operator protocol fields are excluded explicitly with their owner and reason.
- Every included family uses one complete `direct`, `logical-label`, or `internal-only` policy. Internal protocol values may remain documented for operators while staying absent from ordinary product screens.
- FEAT-0057 established the complete registry, generated dictionaries, and exact consumer inventory. FEAT-0061 then normalized all `72` current ordinary visible-consumer declarations within this PRD.

### Pinned Sessions

- Only persisted primary work Sessions are pinnable. Subsessions and Maintenance Sessions remain ineligible.
- Pinned Sessions is global across active Claude/Codex, workspace, and pagination filters.
- Every current pin remains available. Wide layouts use a `420px` bounded internal scroller, while narrow layouts keep pins in ordinary document flow without a silent item cap.
- Pins are ordered by displayed activity date (`last_event_at`, otherwise `started_at`) descending, with `pinned_at DESC, session_id DESC` tie-breaks. Manual ordering is not part of this boundary.
- “Reopen” means opening the LocalBrain Session detail. Native Claude or Codex process resume remains deferred to a separately approved Feature.

### Related Context

- Relationship precedence is Session evidence, Thread, Workstream, then workspace. One target appears once with its strongest reason and any additional bounded reasons.
- Eligible targets include registered Atlassian Items with Session evidence, Documents or Resources sharing explicit Thread or Workstream membership, and enabled Local Context Documents in the same workspace.
- The projection scans at most `48` candidates from each relationship source family and emits at most `12` deduplicated targets in deterministic order.
- At compact and narrow widths, Related Context enters document flow after Session identity and orientation and before the long conversation.
- Manual Session-to-context relationships, accepted inferred relevance, and user-curated related-context ordering remain deferred to a separately approved Feature.

## Constraints

- PRD-0009 and all five child Features are `passed`; later changes require their own approved boundary.
- Feature planning begins only after PRD approval, and only one approved Feature enters execution at a time unless the owner later authorizes otherwise.
- Value dictionaries are durable policies, not one-time audit output. Every later bounded-value change updates its subject dictionary in the same approved implementation boundary.
- Existing data-model subject ownership and generated Schema presentation remain authoritative in their current roles; the dictionary layer must link rather than duplicate full table catalogs.
- Pin persistence is non-rebuildable local intent and must remain outside source-derived Session fields.
- Related context is local-only and deterministic in the initial boundary.
- Visible Session changes use the `Fullstack Product` profile with explicit lanes for pin contract/migration, inventory controls and panel, detail related-context read model, responsive presentation, and interaction continuity.
- Required visible evaluation includes Design, Functional, and UX Heuristic review; the pin contract and value-dictionary parity require Contract evaluation.
- Supported widths remain `1440`, `920`, `700`, and `320`, with synthetic tracked evidence and no private Session titles, paths, or content.

## Acceptance Envelope

- The nine data-model subjects each have one linked value dictionary with explicit ownership and no duplicated table catalog.
- Every in-scope bounded value family records its physical values, logical meaning, enforcement class, complete presentation policy, fallback, and important consequence.
- A `logical-label` family has complete labels for all allowed states, and automated checks fail on dictionary drift or a consumer raw-token fallback.
- Existing physical storage and compatible migration behavior remain unchanged unless a later approved Feature explicitly owns a schema delta.
- Eligible Session pin/unpin state persists across restart and normal source rescans without modifying source files.
- Pin state uses a separate user-owned one-to-one record; removal affects only that record and Session deletion has a documented effect.
- `/sessions` replaces the generic recent Context panel with deterministic pinned Session recall and provides usable empty, populated, filtered, pagination, error, and narrow states.
- Session rows with and without Subsessions keep the same trailing utility geometry at each supported width. At desktop and laptop widths, `질문 → 이벤트 → 날짜 → 핀` forms one aligned upper row and available Subsession triggers occupy the lower trailing edge without moving the upper metadata.
- Pinned and unpinned controls remain distinguishable without color alone, expose correct accessible name and pressed state, and do not navigate to the Session or shift row geometry when activated.
- `/sessions/{session_id}` exposes pin state and a related-context rail that explains each deterministic relationship without triggering an external, model, embedding, scan, or maintenance action.
- Global recency alone does not make a document related to a Session.
- Existing Session source filters, workspace filters, pagination, Sessions/Projects mode, parent/subsession organization, conversation reading, Workstream membership, and no-script navigation remain usable.
- Required contract, design, functional, UX, schema, privacy, and full-regression evidence passes for the later approved child Features.

## Implemented Features

The approved PRD was executed through these passed child Features:

1. [FEAT-0057: Data Model Value Dictionary Baseline](../feature/feat-0057-data-model-value-dictionary-baseline.md) (`passed`) — established the nine subject dictionaries, executable registry, and parity contract.
2. [FEAT-0058: Session Pin Persistence Contract](../feature/feat-0058-session-pin-persistence-contract.md) (`passed`) — added row-presence pin ownership without a status column.
3. [FEAT-0059: Pinned Session Recall And Controls](../feature/feat-0059-pinned-session-recall-and-controls.md) (`passed`) — replaced generic recent Context with pinned recall and stable row/detail controls.
4. [FEAT-0060: Session Related Context Rail](../feature/feat-0060-session-related-context-rail.md) (`passed`) — added deterministic local related context to primary Session detail without a new relationship schema.
5. [FEAT-0061: Bounded-Value Consumer Normalization](../feature/feat-0061-bounded-value-consumer-normalization.md) (`passed`) — migrated all declared ordinary visible consumers to the approved complete-family presentation policies.

All five child Features passed in dependency order. FEAT-0061 covers `40` logical-label families and the current `72` ordinary consumer declarations as one bounded loop; no Feature split was required.

## Closure Evidence

- RUN-20260724-60, RUN-20260724-61, RUN-20260724-64, RUN-20260724-65, and RUN-20260724-66 passed in dependency order.
- The executable registry owns `54` bounded families across nine generated subject dictionaries: `40` complete logical-label families and `14` internal-only families.
- Session pins persist as user-owned row presence, and Pinned Sessions plus primary Session detail controls preserve source files, filters, pagination, focus, and row geometry.
- Session inventory metadata keeps `질문 → 이벤트 → 날짜 → 핀` in its upper utility order and optional Subsessions at the lower trailing edge.
- Related Context remains deterministic, local-only, relationship-explained, bounded, failure-isolated, and absent from Subsession detail.
- The final `288`-test repository suite, value-dictionary/Data Model/Schema checks, supported-width browser evidence, and repository privacy inspection passed on `2026-07-27`.
- The owner directly verified the post-closure PRD-0009 Sessions inventory and primary Session-detail visual refinements in the local browser on `2026-07-27`, closing the recorded browser-control availability gap for those refinements.

## Drift Watchlist

- New schema columns, `CHECK` values, application constants, and derived states added before the dictionary baseline.
- Differences between fresh `schema.sql`, compatible `db.py`, runtime-only enforcement, and generated Schema presentation.
- Session identity preservation and deletion behavior during scanner reconciliation.
- Sessions inventory pagination, filters, secondary-column geometry, and narrow responsive ordering.
- Context Document workspace attribution, Workstream/Thread membership resolution, and Atlassian Session evidence availability.
- Any native Claude or Codex resume capability introduced before Feature planning.

## Regression And Maintenance Targets

- `docs/policies/project/data-model.md` and all nine subject owner documents.
- `src/localbrain/schema.sql`, `db.py`, bounded-value constants, schema-presentation builders, and current data-model checks.
- PRD-0002, PRD-0006, their passed Session/reading Features, and current evaluations.
- `src/localbrain/queries.py`, `workstreams.py`, `main.py`, `templates/sessions.html`, `templates/session.html`, Session assets, and focused tests.
- Design Constitution, Design Evaluation, Interaction Evaluation, privacy policy, and developer verification guidance.

## Source Sync Status

- Sources checked this session: owner direction, current 34-table plus FTS5 Data Model entry and nine subject owners, fresh Session schema, current recent-document query and Sessions templates/routes, current workspace and Workstream/Thread relationships, PRD-0002, PRD-0006, PRD-0008, and visible-surface policies.
- Source deltas: the value-dictionary boundary moved from PRD-0008 to PRD-0009; pinned Session recall and Session-scoped related context are added as independent lanes.
- External recheck needed: `no` for PRD review. No external or model call is needed to plan or implement the initial local-only boundaries.

## Closure Handoff

- No child Feature remains active.
- New bounded physical values or visible consumers must update the executable registry and generated subject dictionary in the same approved boundary.
- A future native Claude/Codex resume action, manual pin ordering, or user-curated related-context relationship requires a new planned Feature.
- Existing Session pin, row geometry, related-context, and complete-family vocabulary behavior are regression surfaces.

## Continuity Notes

- `2026-07-24`: created PRD-0009 by splitting the nine-subject physical/logical/UI value-dictionary boundary from PRD-0008 at the owner's direction.
- `2026-07-24`: added pinned Session recall, replacement of the Sessions inventory's generic recent Context panel, and a Session-detail related-context rail.
- `2026-07-24`: current schema review found that pin persistence needs a new user-owned one-to-one record, while the initial related-context rail can use existing workspace, Workstream/Thread, and Atlassian evidence relations without a new relationship table.
- `2026-07-24`: fixed the Sessions inventory row composition around one reserved trailing utility layer: date and pin align at the upper edge, the optional Subsession trigger anchors at the lower edge, and pin state uses glyph plus tonal treatment without shifting card geometry.
- `2026-07-24`: the owner approved PRD-0009 and requested Feature decomposition. FEAT-0057 through FEAT-0061 were created as draft value-dictionary, pin persistence, pinned recall, related-context, and visible-consumer boundaries.
- `2026-07-24`: refined FEAT-0059 row metadata so question count and event count move immediately left of the date in the upper utility row; the pin remains the outer upper control and Subsession remains lower trailing.
- `2026-07-24`: FEAT-0059 passed with the `Pinned Sessions` title, a `420px` wide-layout scroller threshold, all-pin ordering, stable row controls, and inventory/detail pin mutation continuity.
- `2026-07-24`: FEAT-0060 passed with deterministic local relationship precedence, a `12`-item display cap, `48` candidates per source family, visible resolved-unavailable states, and responsive Session-detail placement.
- `2026-07-27`: FEAT-0061 and repository-wide closure verification passed. PRD-0009 is the canonical completed boundary for value dictionaries, Session pin persistence and recall, Session row geometry, and local related-context presentation.
- `2026-07-27`: post-closure owner refinement orders Pinned Sessions by displayed activity date descending and removes the pin control's independent square background so pressed state does not recolor it and row hover remains continuous.
- `2026-07-27`: post-closure Local Context review removed redundant source-type, readability, and enabled labels from every source-list row while keeping selected-source status visible.
- `2026-07-27`: the owner directly verified the final local UI refinements; the prior browser-control availability gap is closed, and the former open-question section now records resolved decisions plus explicitly deferred follow-up scope.
