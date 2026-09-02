# Atlassian Explorer Reframe Design Plan

## Metadata

- Status: `complete`
- Parent boundary: [PRD-0014: Atlassian Explorer And Unified Retrieval](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Created: `2026-08-29`
- Updated: `2026-08-29`
- Review gate: complete; FEAT-0075 through FEAT-0080 passed

## Purpose

- Reconcile the current Atlassian Browse, Add, connected setup, Refresh entry,
  and Item detail surfaces into a simpler find-and-inspect workflow.
- Retain the completed design sequence for hierarchy, interaction state,
  responsive composition, and phased validation without turning the plan into
  durable design law or implementation authority.

## Plan Type

- Information hierarchy reconciliation.
- Interaction consistency and responsive reframe.
- Screen-family alignment with a possible Design Constitution handoff.

## Baseline

### Audited Sources

- Current `/atlassian` Browse at synthetic `1440`, effective `920 x 875`, and
  emulated `320 x 900` viewports.
- Current URL Add and connected discovery entry states at wide and narrow
  viewports.
- Current `/atlassian/items/{id}` full-detail surface.
- Current Local Context source rail, tree, preview, splitter, and responsive
  Explorer behavior.
- Current Sessions Sync toolbar as an interaction reference for one explicit
  local scan action and bounded feedback, not as a semantic replacement for
  Atlassian Refresh.

### Constitution And Evaluation References

- [Design Constitution](../../policies/design/design-constitution.md)
- [Design Evaluation](../../policies/design/design-evaluation.md)
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md)
- [PRD-0010: Atlassian UI And Interaction Reconciliation](../prd/prd-0010-atlassian-ui-and-interaction-reconciliation.md)
- [PRD-0014: Atlassian Explorer And Unified Retrieval](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)

### Rendered Baseline Findings

| Surface | Observed initial-state cost |
| --- | --- |
| Browse at `1440` | ten Atlassian selectors plus simultaneous global and local query inputs; filter form consumes `268px` before results |
| Browse at effective `920 x 875` | ten selectors form five rows and the first Item starts below the viewport at `y = 881` |
| Browse at `320 x 900` | ten selectors form one long column; first Item begins at `y = 1546` |
| Add at `320 x 900` | registered scope precedes the task; URL input begins at `y = 1149`; total document height is `2923px` |
| Item detail at `1440` | remote and local regions are readable but separated from the inventory by a full navigation and expose large empty diagnostic areas for link-only Items |

## Scope

- One Atlassian information hierarchy covering `All`, Jira, and user-facing
  Wiki/Confluence views.
- Site, Space/project, Unclassified, link-list, selection, and detail-region
  composition.
- One visible Atlassian query task, deterministic exact/local mode, and the
  placement of advanced filters.
- Top-level manual Add and local evidence Sync entry points.
- Clear relocation of optional access binding and connected discovery.
- Preservation of explicit remote Refresh and full-detail fallback.
- Wide, compact, and narrow interaction and reading order.
- Empty, partially known, stale, unavailable, error, long-content, and active
  selection states.

## Non-Goals

- Product-wide shell or navigation redesign.
- New visual tokens, type systems, colors, radii, shadows, or unrelated
  component families.
- Atlassian writes, silent background Refresh, or live provider search.
- Treating AI retrieval as a visual toggle without an approved data, privacy,
  evidence, cost, and execution contract.
- Nested Confluence Page or Jira issue trees not owned by the current model.
- Feature, Spec, code, migration, or evaluator work before approval.

## Invariants

- Preserve the LocalBrain shell unless the approved one-search placement needs
  a bounded Atlassian-route handoff; persistent shell geometry must remain
  stable.
- Preserve Site, Space, Item, access-binding, evidence, remote-state/content,
  local-memory, classification, relationship, and Refresh-history ownership.
- Keep remote facts, local memory, source evidence, and maintenance history
  visually and semantically distinct.
- Local Browse, exact search, Add, Sync, detail, and Refresh preview perform no
  implicit external or model work.
- Optional access setup remains secondary and cannot block manual Add or local
  review.
- A selected Item remains directly reachable without JavaScript and through a
  stable URL.
- Responsive simplification removes or relocates secondary structure before
  reducing legibility or touch geometry.
- Tracked evidence uses synthetic names and content.

## Findings

### F-01: Retrieval Starts With Configuration

- Ten equally visible selectors make the user configure the inventory before
  seeing the links they came to retrieve.
- Several axes are valid advanced tools, but their initial visual weight is
  disproportionate to common find-and-inspect work.

### F-02: Query Ownership Is Duplicated

- The shared global query and the Atlassian-local query are simultaneously
  visible while owning different result sets and parameters.
- A reframe must choose one visible query owner rather than restyle both.

### F-03: Add Is Preceded By Inventory And Paired With Setup

- Registered scope appears before the Add task, and optional access settings
  occupy equal space beside the one-URL local action.
- At narrow widths this pushes the primary URL input beyond the first viewport
  and makes optional configuration feel prerequisite-like.

### F-04: Browse And Read Lose Continuity

- A compact inventory row navigates to a separate long detail page, so query,
  filter, list scroll, and neighboring Items are no longer visible.
- The current detail content is reusable, but its default hierarchy should be
  condensed inside an adjacent region with progressive full detail.

### F-05: Action Labels Mix Different Consequences

- Local evidence scan, manual URL registration, connected discovery, and
  remote Refresh have different I/O and persistence consequences.
- They need distinct owners and labels even when all remain reachable from the
  Atlassian surface.

### F-06: The Requested Family Differs From The Durable Classification

- The requested Site/Space/list/detail behavior follows the existing Explorer
  interaction family, while the Design Constitution currently classifies
  Atlassian as Browse and inventory.
- The owner approved formal Explorer reclassification. FEAT-0075 must update
  the Design Constitution and state contract before dependent visible Features
  enter build.

## Target Interaction Model

### Wide Wireframe

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ [All] [Jira] [Wiki]  [ Search Atlassian…                    ] [Exact]     │
│                                                     [Filters] [Sync] [+Add]│
├────────────────┬────────────────────────────┬─────────────────────────────┤
│ Site / Space   │ Links                      │ Document information        │
│                │                            │                             │
│ Jira           │ ALPHA-202                  │ ALPHA-202                   │
│  jira.test     │ ALPHA-101                  │ Jira · jira.test · ALPHA    │
│   ALPHA        │                            │ URL / provenance / freshness│
│                │                            │ remote facts                │
│ Wiki           │ Release plan               │ local note and organization │
│  wiki.test     │ API migration              │ evidence and Refresh        │
│   TEAM         │                            │ [Full detail] [Open source] │
│ Unclassified   │                            │                             │
└────────────────┴────────────────────────────┴─────────────────────────────┘
```

### Compact And Narrow Model

| Width state | Hierarchy | List | Detail | Advanced filters |
| --- | --- | --- | --- | --- |
| Wide | persistent left rail | persistent center region | persistent right region | bounded disclosure/drawer |
| Compact | scoped drawer or collapsible rail | primary persistent region | side sheet or sequential region | drawer |
| Narrow | top scope action and explicit hierarchy sheet | first content destination | full-width sheet or fallback route | sheet; never an expanded pre-result stack |

### State Ownership

- Service scope owns the eligible Jira/Confluence population.
- Site/Space selection owns a structural subset and does not silently add
  hidden query filters.
- Query mode and query text own retrieval within the active structural scope.
- Item selection owns the detail region and current Item URL/history state.
- Pane disclosure and geometry are user-owned presentation state and should
  survive Item replacement where the destination width supports them.
- Sync, Add, connected discovery, and Refresh each own independent progress,
  errors, recovery, and completion feedback.

## Planned Work

### Batch 1: Establish Explorer Family And State Ownership

- Goal: make the approved Explorer classification and state model durable.
- Why this grouping: family ownership, surface-local query placement, default
  `All` scope, hierarchy, selection, URL/history, actions, and breakpoints are
  one prerequisite interaction contract.
- Guardrails: contract and policy only; no product UI or runtime behavior.
- Targets: [FEAT-0075](../feature/feat-0075-atlassian-explorer-family-and-state-contract.md),
  Design Constitution, Product Model, and state-owner documentation.
- Validation: contract cross-check, stale-assumption inventory, and downstream
  readiness review.
- Exit gate: product Features can proceed without guessing about family or
  state ownership.

### Batch 2: Establish Deterministic Exact Retrieval

- Goal: replace the misleading token-AND approximation with one testable local
  exact retrieval contract.
- Why this grouping: identifier, phrase, field, service, filter, ordering, and
  empty-query behavior must be stable before the visible search depends on it.
- Guardrails: local-only; no model, provider call, UI, or AI placeholder.
- Targets: [FEAT-0076](../feature/feat-0076-atlassian-exact-retrieval-contract.md),
  query/read-model contracts, tests, and owner docs.
- Validation: synthetic exact identifier and phrase matrix, combined-service
  eligibility, deterministic order, and current-query regression.
- Exit gate: the Explorer search Spec can consume one unambiguous read model.

### Batch 3: Deliver Explorer Inventory And Search

- Goal: make Site/Space scope, compact links, `All / Jira / Wiki`, one query,
  and progressive filters the primary Atlassian retrieval surface.
- Why this grouping: hierarchy and retrieval controls jointly own the visible
  eligible set and initial information hierarchy.
- Guardrails: current full-detail route remains the executable destination;
  no adjacent async detail replacement yet.
- Targets: [FEAT-0077](../feature/feat-0077-atlassian-explorer-inventory-and-search.md),
  responsive hierarchy/list surface, service scope, query, and Filters sheet.
- Validation: initial result reachability, scope/query/filter state, long and
  empty lists, keyboard, direct URL, history, and supported widths.
- Exit gate: common find work no longer traverses an always-expanded selector
  matrix.

### Batch 4: Add In-Context Item Detail

- Goal: inspect an Item without losing hierarchy, query, or neighboring links.
- Why this grouping: detail fragments, async replacement, selected state,
  history, focus, stale-response handling, and responsive sheets share one
  interaction lifecycle.
- Guardrails: full-detail/no-script link remains; authority regions stay
  separate; no invented nested hierarchy.
- Targets: [FEAT-0078](../feature/feat-0078-atlassian-in-context-item-detail.md),
  adjacent detail region, progressive local controls, and fallback route.
- Validation: deep and rapid selection, list scroll, focus, back/forward,
  direct entry, long/empty/unavailable detail, and breakpoint transitions.
- Exit gate: wide, compact, and narrow users can inspect and return without
  losing orientation.

### Batch 5: Separate Manual Add And Connections

- Goal: make one-URL local Add the only primary registration task and relocate
  optional access and connected discovery.
- Why this grouping: Add and remote setup share current markup but have
  different prerequisites and consequences.
- Guardrails: URL Add remains local-only and executable with zero access;
  connected discovery remains explicit remote maintenance.
- Targets: [FEAT-0079](../feature/feat-0079-atlassian-manual-add-and-connections-separation.md),
  focused Add first state and secondary Connections destination.
- Validation: valid/reused/invalid URLs, zero access, optional later binding,
  discovery readiness, focus return, responsive order, and no-script fallback.
- Exit gate: optional remote setup cannot visually or functionally block Add.

### Batch 6: Expose Local Evidence Sync

- Goal: give deterministic Session/Local Context evidence reconciliation one
  visible local action and honest outcome summary.
- Why this grouping: scan scope, automatic reconciliation, progress, outcome,
  provenance, and Refresh separation form one user task.
- Guardrails: no remote/model call, no source-body copying, and no per-link
  confirmation for deterministic eligible findings.
- Targets: [FEAT-0080](../feature/feat-0080-atlassian-local-evidence-sync.md),
  local action, bounded status, outcome categories, and recovery.
- Validation: new/reused/skipped/unavailable/failed outcomes, repeat idempotency,
  zero results, source eligibility, narrow feedback, and Refresh non-execution.
- Exit gate: the user can collect mentioned links without confusing Sync with
  remote Refresh.

### Later Batch: Admit AI Retrieval Only Through Its Own Contract

- Goal: add AI retrieval only if a reviewed foundation makes its execution and
  evidence boundary safe and useful.
- Why this grouping: model selection, data admission, evidence, cost, latency,
  cancellation, caching, and failure are a new product contract rather than a
  visual search variant.
- Guardrails: default local exact retrieval remains usable; no unapproved
  transmission; generated results never hide provenance or remote freshness.
- Targets: foundation contract first, then the opt-in interaction and states.
- Validation: consent, admitted input inspection, evidence navigation,
  unavailable model, cancellation, timeout, partial evidence, cost visibility,
  and deterministic-search fallback.
- Exit gate: AI mode can be independently disabled without breaking the
  primary Explorer retrieval workflow.

## Validation Gates

- Human PRD approval precedes Feature creation; human Feature approval precedes
  Spec or implementation.
- The chosen family aligns with the current Design Constitution or updates it
  with a governance version entry before dependent visible implementation.
- Browser evidence uses effective `1440`, `920`, `700`, and `320` viewports and
  synthetic content.
- The initial Browse state has one visible query input and no permanently
  expanded ten-selector matrix before results.
- Design review covers hierarchy, authority separation, scroll containment,
  selection, long labels, empty/error states, and shell continuity.
- Functional review covers service/scope/query eligibility, Add identity,
  local Sync reconciliation, Refresh separation, URL/history, direct entry,
  and no-script paths.
- Interaction review covers browse-to-preview continuity, focus and scroll,
  rapid selection, stale response suppression, breakpoint state normalization,
  preflight, optional setup, and one execution path per action.
- Privacy and contract review proves that no local query or content reaches an
  external or AI service without a separately approved boundary.

## Risks / Open Questions

- AI result form, model path, admitted content, evidence, and cost.

The completed child Features resolved exact matching, Connections placement,
detail editing, and the current bounded filters. AI remains a deferred
candidate and requires a separately approved Feature before any further design
or execution.

## Exit Goal

- Atlassian reads as one deliberate retrieval workspace: one search task,
  recognizable Site/Space organization, compact links, continuous detail, and
  clearly separated Add, local Sync, connected discovery, and remote Refresh.
- Common find-and-inspect work starts before advanced configuration at every
  supported viewport, while provenance, unavailable state, advanced local
  organization, and explicit remote safety remain inspectable.

## Handoff To Next Track

- PRD-0014 and its approved sequential execution are complete. FEAT-0075
  through FEAT-0080 passed. At this plan's `2026-08-29` closure no follow-on
  Atlassian Feature was active; the later completed [PRD-0015](../prd/prd-0015-atlassian-site-first-url-organization.md)
  and its [completed design plan](atlassian-site-first-hierarchy-plan.md) own
  the subsequent domain-first follow-up without rewriting this completed
  baseline.
- FEAT-0075 promoted the approved durable screen-family change to the Design
  Constitution; phased UI sequencing and rollout evidence remain in this plan.
- Specs, code, migrations, and evaluation artifacts remain owned by each
  Feature loop rather than this design plan.
