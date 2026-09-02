# PRD-0014: Atlassian Explorer And Unified Retrieval

## Metadata

- ID: `prd-0014`
- Status: `passed`
- Boundary State: passed; FEAT-0075 through FEAT-0080 passed
- Owner role: `human`
- Created: `2026-08-29`
- Updated: `2026-08-29`
- User review status: boundary and sequential Feature execution completed
- Approval mode: sequential Feature planning and independent Feature approval

## Request Summary

- Reframe the current mode- and filter-heavy Atlassian inventory as one calm
  Explorer surface organized by Site and Space, with a compact link list and
  an adjacent Item detail region.
- Replace the primary filter stack with one search entry and reversible
  `All / Jira / Wiki` scope, make manual Add a one-URL task, and distinguish a
  local Session/Local Context evidence Sync from explicit remote Refresh.
- Preserve the passed local-first identity, provenance, read-only access, and
  refresh-safety contracts while reviewing any intentional search or
  screen-family changes before implementation.

## Source Set

### Human Direction

- The current `06 Atlassian` screen looks too complex, especially its many
  search dropdowns and the Add flow.
- The preferred direction is a Local Context-like Space structure, a linear
  link list, one Google-like query input with exact and AI retrieval choices,
  and document information on the right.
- Sync should collect Atlassian references mentioned by local Sessions and
  Local Contexts; Add should serve manually entered pages or links.
- Jira and Wiki should be viewable separately or together.
- After reviewing the current rendered behavior and the proposed boundary,
  the owner directed planning to proceed.
- The owner approved the normalized PRD and its recommended defaults on
  `2026-08-29`: formal Explorer classification, `All` as the default service
  scope, one surface-local Atlassian query input, automatic deterministic local
  Sync reconciliation with an outcome summary, exact retrieval before AI, and
  AI retrieval deferred to a separately approved foundation boundary.

### Golden And Rendered Sources

- The current `/atlassian` Browse and Add surfaces, the current Atlassian Item
  detail route, and the current Local Context Explorer are the visual and
  interaction baselines.
- A Chrome DevTools review with synthetic Jira and Confluence records observed:
  - ten visible Atlassian Browse selectors plus simultaneous global and local
    query inputs at the desktop baseline;
  - the first result below the effective `920 x 875` viewport at `y = 881`;
  - the first result at `y = 1546` in the `320 x 900` layout after all ten
    selectors stack into one column;
  - the primary Add URL input at `y = 1149` in the `320 x 900` layout, after
    registered-scope presentation;
  - `view=all` resolving to the Jira inventory rather than a combined scope;
  - Atlassian Item information and local organization on a separate long page
    rather than an in-context detail region.
- The review used temporary local runtime data, retained no screenshots or
  private content, and changed no implementation files.

### Existing Product Boundaries

- [PRD-0007: Atlassian Source Memory And Explicit Refresh](prd-0007-atlassian-source-memory-and-refresh.md)
  owns the passed read-only source memory, evidence, local search, and explicit
  bounded Refresh contracts.
- [PRD-0008: Connected Atlassian Validation And Schema ERD Routing](prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
  owns the passed access-binding, connected discovery, and execution-owner
  distinctions.
- [PRD-0010: Atlassian UI And Interaction Reconciliation](prd-0010-atlassian-ui-and-interaction-reconciliation.md)
  owns incremental reconciliation that preserves the current information
  architecture. It does not own this broader Explorer reframe.
- [Atlassian Explorer Reframe Design Plan](../design/atlassian-explorer-reframe-plan.md)
  retains the completed design batches, wireframes, validation gates, and
  evaluation rationale for this boundary.

### Durable Policies

- [Product Model](../../policies/project/product.md)
- [Atlassian Source Memory](../../policies/project/data-model/atlassian-source-memory.md)
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md)
- [Design Constitution](../../policies/design/design-constitution.md)
- [Design Evaluation](../../policies/design/design-evaluation.md)
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md)

### Current Implementation References

- `src/localbrain/templates/atlassian.html`
- `src/localbrain/templates/atlassian-item.html`
- `src/localbrain/templates/atlassian-refresh.html`
- `src/localbrain/templates/context.html`
- `src/localbrain/static/atlassian.js`
- `src/localbrain/static/app.js`
- `src/localbrain/static/styles.css`
- `src/localbrain/main.py`
- `src/localbrain/atlassian_browse.py`
- `src/localbrain/atlassian_evidence.py`
- `src/localbrain/atlassian_registration.py`
- `src/localbrain/atlassian_refresh.py`
- `src/localbrain/queries.py`
- `src/localbrain/schema.sql`

## Product Intent

- Make the common Atlassian task `find a known link, inspect its context, and
  continue work` possible from one stable surface.
- Lead with recognizable Site and Space organization instead of requiring the
  user to compose ten independent filter dimensions before seeing results.
- Keep local evidence collection, manual registration, and remote refresh as
  separate actions whose labels and consequences remain truthful.
- Preserve advanced organization and diagnostic capability without giving it
  the same initial visual weight as search, selection, and reading.

## Confirmed Scope

### Explorer Information Architecture

- Replace the primary `Browser / Add` mode composition with one Atlassian work
  surface and top-level `Sync` and `Add` actions.
- Provide reversible `All / Jira / Wiki` service scope. `Wiki` is a display
  label for persisted `confluence` records; the stored service vocabulary is
  not renamed.
- Present a left hierarchy grouped by Service when needed, then Site, then
  Space or Jira project. Items with no persisted Space appear under an
  explicit `Unclassified` group rather than disappearing.
- Present the selected hierarchy scope as a compact center link list with
  stable title or key, service, Site or Space, coverage/freshness cues when
  useful, and source provenance without card-level repetition.
- Present the selected Item in an adjacent right detail region. Keep remote
  facts, local notes/classification, evidence, and Refresh history visibly
  separate by authority and expose diagnostics progressively.
- Preserve a full-detail destination as a direct-link and no-script fallback
  even when the ordinary interaction replaces only the detail region.
- Preserve selected service, hierarchy scope, query, Item identity, and
  intentional pane state through URL/history behavior so back, forward,
  refresh, and direct entry restore understandable orientation.
- The first increment groups by Site and Space only. It does not claim a
  canonical nested Confluence Page tree that the current model does not own.

### One Primary Atlassian Search

- Show exactly one visible query input for the Atlassian retrieval task rather
  than simultaneous shell-global and Atlassian-local query inputs.
- Provide a deterministic exact/local retrieval path that does not call a
  model. The implementation must define genuine phrase, identifier, and field
  matching semantics instead of relabeling the current token-AND FTS as
  `exact`.
- Keep the current independent axes such as Site, Space, freshness, attention,
  Topic, Tag, and Workstream available only where they remain useful, behind
  one bounded Filters disclosure or contextual chips rather than ten visible
  selectors in the initial state.
- Treat AI retrieval as an explicit opt-in mode and a separate contract. It
  cannot call a model, transmit local content, or present generated results
  until the model path, admitted inputs, evidence, privacy, availability,
  cost, and failure behavior are approved through a foundation Feature.

### Manual Add

- `Add` opens a focused modal, drawer, or equivalent bounded first state with
  one required Atlassian URL.
- Infer Jira versus Confluence, normalized Site, and Issue/Page/Project/Space
  identity locally from the URL while preserving current validation and
  idempotent registration behavior.
- Keep Item and Space URL registration local-only. Provider, connection
  reference, capability, runner, and remote access are not required fields or
  adjacent primary-task content.
- Move optional access binding and connected discovery to a clearly named
  secondary Connections or maintenance destination without deleting those
  existing capabilities.

### Local Evidence Sync And Explicit Refresh

- `Sync` is an explicit local action that scans eligible primary work Sessions
  and enabled Local Context Documents for recognized configured Atlassian
  URLs, reconciles deterministic Item evidence, and reports new, reused,
  skipped, and unavailable outcomes.
- Sync stores only the bounded URL, identity observations, and provenance
  already allowed by the Atlassian evidence contract. It does not copy Session
  or Document bodies into Atlassian ownership and performs no remote or model
  call.
- Remote `Refresh` remains a separately named, explicit preview and execution
  path over existing local Items. Its access readiness, selection, call
  accounting, per-target outcomes, and maximum batch limits remain visible.
- Connected candidate discovery remains remote maintenance and must not be
  presented as local Sync or manual Add.

### Responsive Composition

- Wide layouts use a stable hierarchy/list/detail composition with independent
  reading-region scroll ownership where needed.
- Compact layouts may collapse the hierarchy into a scoped drawer or
  disclosure while keeping the list visible and preserving selection.
- Narrow layouts are list-first. Hierarchy and detail open as explicit sheets
  or sequential destinations, and advanced filters never form a required
  ten-control stack before results.
- Breakpoint transitions normalize any pane or mode state that is not
  supported at the destination width and preserve focus, history, and current
  Item orientation.

## Excluded Scope

- Atlassian write operations, ticket or Page mutation, comments, transitions,
  or attachment upload.
- Silent or background remote refresh, live provider search on each keystroke,
  or an unreviewed expansion of approved MCP operations.
- Mandatory external AI, embeddings, network enrichment, or transmission of
  local queries, content, notes, evidence, or results to an unapproved model.
- Copying complete Session, Local Context, Jira, or Confluence source bodies
  into a new Sync evidence owner.
- A canonical nested Confluence Page hierarchy, Jira issue hierarchy, or new
  containment schema in the first Explorer increment.
- Renaming persisted `confluence` service values to `wiki`.
- A broad LocalBrain shell, navigation, typography, token, or unrelated screen
  redesign beyond the approved single-search ownership needed on Atlassian.
- Removing current advanced classification, access management, discovery, or
  full-detail capabilities without an explicit replacement or deferral.
- Specs, code changes, migrations, or evaluator work before a child Feature is
  separately approved.

## Resolved Decisions And Compatibility Direction

- This is a new upper planning boundary, not an additional observation under
  PRD-0010. PRD-0010 remains the historical owner of its passed incremental
  work; PRD-0014 owns the approved Explorer reframe.
- Atlassian formally moves to the durable `Explorer` family. A foundation
  Feature must update the Design Constitution and product interaction contract
  before dependent visible Features enter build.
- `All` is the default service scope. Jira and user-facing Wiki remain explicit
  reversible scopes and direct URLs preserve an explicit service choice.
- One surface-local Atlassian query input owns retrieval. The shared topbar
  query is not simultaneously visible on the Atlassian route, while the shell
  handoff must preserve stable geometry and navigation continuity.
- Local Sync automatically reconciles deterministic eligible findings and
  reports new, reused, skipped, and unavailable outcomes without a per-link
  confirmation step.
- Deterministic exact retrieval precedes AI. AI retrieval is deferred and has
  no active child Feature until a later human decision activates its separate
  foundation boundary.
- Local Sync, manual Add, connected discovery, and remote Refresh are four
  distinct consequences and must not share one ambiguous action label.
- `Wiki` is user-facing terminology only; internal service identity remains
  Jira or Confluence.
- Space-less Items remain valid and visible under `Unclassified`.
- Remote and local authority regions remain separate even when they share one
  detail pane.
- Existing Item, Site, Space, access-binding, evidence, local classification,
  relationship, content, and Refresh history survive the presentation
  reframe.

## Uncertainty

- If AI retrieval is activated later, define ranked links versus an answer, admitted
  local fields and bodies, model/provider, local versus external execution,
  user confirmation, evidence links, cost visibility, caching, cancellation,
  and unavailable/failure behavior.
- Review real usage evidence before deciding which advanced filters remain,
  become contextual chips, or are retired.

The completed child Features resolved exact semantics, Connections placement,
detail editing, and the current bounded advanced-filter behavior. AI details
remain deferred and have no execution authority.

## User-Visible Flows And Interaction Expectations

### Find And Inspect A Known Item

- The user chooses `All`, `Jira`, or `Wiki`, optionally chooses a Site or
  Space, enters one query, and sees links without first traversing advanced
  filters.
- Selecting a link updates the adjacent detail region and URL/history state
  without losing hierarchy disclosure, list scroll, or query orientation.

### Add A Known URL

- The user opens Add, pastes one Jira or Confluence URL, reviews the locally
  inferred identity, and registers or reuses it without configuring remote
  access.
- Validation failure preserves the URL and creates no partial Site, Space, or
  Item rows.

### Collect Locally Mentioned Links

- The user starts Sync, understands that it scans eligible local Sessions and
  Local Context Documents, and receives a bounded outcome summary without an
  external read.
- Each collected Item can explain where it was discovered without exposing or
  duplicating source text.

### Refresh Remote Information

- From a selected Item or explicit multi-item scope, the user enters the
  existing Refresh preview, sees readiness, selected targets, and read budget,
  and explicitly starts the bounded maintenance Run.
- Missing access never blocks local browse, Add, Sync, notes, classification,
  or evidence review.

## Constraints

- PRD-0007 and PRD-0008 remain passed baselines except where a later approved
  foundation Feature explicitly amends search/model or presentation-family
  policy.
- Until that amendment passes, Atlassian search, Browse, Add, Sync, detail, and
  Refresh preview remain local-only and send nothing to Atlassian or an AI
  service.
- The Design Constitution remains durable authority. The completed design plan
  records the accepted reframe but cannot create new visual law.
- The likely execution profile is `fullstack-product`, with explicit lanes for
  design-family and state contracts, read models and route state, Explorer
  presentation, local evidence Sync, Add/Connections separation, and optional
  AI retrieval.
- Foundation and product outcomes must be separate Features when policy,
  privacy, evidence, data ownership, or state contracts must pass first.
- Visible Features require Contract, Design, Functional, and UX Heuristic
  evaluation as applicable, including `1440`, `920`, `700`, and `320` widths;
  long content; empty, unavailable, stale, failed, and active states; keyboard
  and focus behavior; and back/forward/direct-entry continuity.
- Tracked tests, documentation, wireframes, and screenshots use synthetic data.
- Each completed child Feature received separate approval before its Spec,
  implementation, and evaluator loop. PRD completion does not authorize the
  deferred AI candidates.

## Acceptance Envelope

- The initial Atlassian surface exposes one query input, service scope, one
  bounded Filters entry, Sync, and Add without a ten-selector pre-result stack.
- `All`, Jira, and Wiki scopes return the correct persisted service set and
  preserve truthful URL/history state.
- Site/Space/Unclassified grouping never hides a valid Item, and repeated keys
  remain distinguishable by Site and service.
- Wide selection updates an adjacent detail region while preserving hierarchy,
  list, focus, and history continuity; compact and narrow layouts provide an
  equivalent reachable flow without hidden unsupported state.
- Manual Add requires one URL and succeeds locally without Provider, access
  binding, capability, runner, or remote lookup.
- Local Sync performs no external or model call, retains only bounded evidence,
  and reports its effective scope and per-class outcomes.
- Refresh remains an explicit preview and bounded execution path and cannot be
  mistaken for local Sync.
- Exact/local retrieval is deterministic and testable. AI retrieval remains
  unavailable until its foundation contract is approved and passed, and then
  presents source evidence, execution boundary, cost/availability, and failure
  truthfully.
- Current identity, evidence, local-memory, relationship, content, and Refresh
  history remain intact through the reframe.
- Synthetic browser evidence demonstrates that primary results are not pushed
  below an always-expanded advanced-filter stack at supported widths.

## Candidate Features

- [FEAT-0075: Atlassian Explorer Family And State Contract](../feature/feat-0075-atlassian-explorer-family-and-state-contract.md)
  (`foundation`, `foundation-contract`): update durable family ownership and
  lock one-search, service, hierarchy, selection, URL/history, action, and
  responsive-state contracts.
- [FEAT-0076: Atlassian Exact Retrieval Contract](../feature/feat-0076-atlassian-exact-retrieval-contract.md)
  (`foundation`, `foundation-contract`): define and implement deterministic
  local exact matching and combined-service eligibility without model or
  remote work.
- [FEAT-0077: Atlassian Explorer Inventory And Search](../feature/feat-0077-atlassian-explorer-inventory-and-search.md)
  (`product`, `fullstack-product`): deliver the responsive Site/Space hierarchy,
  compact links, `All / Jira / Wiki`, one query input, and bounded advanced
  filters while retaining full-detail navigation.
- [FEAT-0078: Atlassian In-Context Item Detail](../feature/feat-0078-atlassian-in-context-item-detail.md)
  (`product`, `fullstack-product`): add adjacent Item detail, selection/history
  continuity, progressive authority regions, and full-detail fallback.
- [FEAT-0079: Atlassian Manual Add And Connections Separation](../feature/feat-0079-atlassian-manual-add-and-connections-separation.md)
  (`product`, `fullstack-product`): provide the one-URL Add first state and
  relocate optional access binding and connected discovery.
- [FEAT-0080: Atlassian Local Evidence Sync](../feature/feat-0080-atlassian-local-evidence-sync.md)
  (`product`, `fullstack-product`): expose automatic deterministic local
  Session/Local Context evidence reconciliation with bounded progress,
  provenance, and outcome feedback while preserving explicit remote Refresh.
- `Atlassian AI Retrieval Contract` (`foundation`, deferred candidate): define
  model, privacy, admitted data, evidence, cost, lifecycle, and fallback before
  any AI query can execute.
- `Atlassian AI Retrieval Experience` (`product`, deferred candidate): expose
  the approved opt-in AI mode only after its foundation contract passes.

The owner authorized sequential Feature approval and execution. FEAT-0075
through FEAT-0080 passed. AI
candidates remain in this PRD only and have no Feature document or execution
authority.

## Source Map

| Source | Priority | Contribution | Boundary |
| --- | --- | --- | --- |
| Human direction | primary | Explorer hierarchy, one search, right detail, local Sync, manual Add, and separate/combined service views | does not authorize implementation, external AI, remote writes, or unbounded source copying |
| Rendered current Atlassian screens | primary evidence | control density, result displacement, Add sequencing, separate detail route, and missing combined scope | current behavior is evidence, not the target contract |
| Local Context Explorer | golden family reference | stable source hierarchy, tree/list orientation, progressive preview, responsive collapse, and history continuity | document tree semantics do not automatically become Atlassian containment |
| PRD-0007 and PRD-0008 | passed contract | identity, evidence, registration, access, discovery, explicit Refresh, and read-only boundaries | AI retrieval and the Explorer reframe require new approved scope |
| PRD-0010 | sibling planning history | passed incremental Add/access reconciliation and current-IA regression expectations | does not own this upper reframe |
| Design and interaction policies | durable contract | authority separation, readable density, family governance, pane continuity, responsive state, and preflight behavior | do not decide open search, AI, or Sync product semantics |
| Current code and schema | implementation truth | available fields, nullable Space, service vocabulary, query behavior, evidence scanner, and full detail content | omissions do not authorize invented hierarchy or AI behavior |

## Continuity Notes

- `2026-08-29`: created the draft from the owner's Atlassian simplification
  direction, synthetic Chrome DevTools review, current implementation, passed
  Atlassian contracts, Local Context Explorer reference, and durable design,
  interaction, privacy, and workflow policies.
- `2026-08-29`: separated local evidence Sync, one-URL Add, connected remote
  discovery, and explicit Refresh; kept AI retrieval, one-search ownership,
  exact semantics, and durable screen-family classification open for human
  review.
- `2026-08-29`: the owner approved the PRD with formal Explorer classification,
  `All` default scope, one surface-local query input, automatic deterministic
  local Sync, exact-first sequencing, and AI retrieval deferred to a separate
  later foundation.
- `2026-08-29`: FEAT-0075 through FEAT-0077 passed under the approved sequence;
  FEAT-0078 is the sole active Feature and FEAT-0079/0080 remain queued behind
  it.
- `2026-08-29`: FEAT-0078 and FEAT-0079 passed their full execution loops;
  FEAT-0080 became the sole active Feature under the approved sequence.
- `2026-08-29`: FEAT-0080 passed RUN-90 Attempt 1 with contract, design,
  functional, and UX evaluation. All six approved Features are passed, so
  PRD-0014 is complete; AI retrieval remains deferred without execution
  authority.
