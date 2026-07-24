# FEAT-0049: Explicit Atlassian Refresh And Preview

## Metadata

- ID: `feat-0049`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Goal

- Let the user deliberately preview and refresh one Item, one Space, one Thread, one Workstream, or all known Atlassian resources while understanding target scope, freshness, cost-bearing maintenance activity, progress, no-change, and partial failure.

## Acceptance Contract

- Ordinary Atlassian browse, detail entry, local search, Workstream navigation, and page load trigger no remote or model call.
- Refresh can target one Item, one registered Space, one Thread's directly linked Items, one Workstream's direct and Thread-linked Items, or all Atlassian resources already known to LocalBrain.
- Thread and Workstream scopes include only mapped Items. Workstream scope includes its Threads and deduplicates one Item to one execution target.
- All-known scope never means every resource accessible in the company Atlassian estate.
- Workstream and all-known refresh require a local no-remote preview before execution.
- A registered-Space refresh shows its saved coverage and a bounded target or pagination expectation before execution.
- Preview shows target count, service, Source Instance, Site or Space when known, Item identity, coverage, freshness, last successful remote check, last content application, and inclusion checkbox.
- Preview defaults select `unknown`, `due`, `stale`, and previously `unavailable` targets; `current` targets remain visible but unchecked.
- The user can include a current target or exclude another target before starting one FEAT-0045 maintenance Run.
- Item refresh may proceed from its contextual action without a multi-target preview but still identifies Source Instance, coverage, current freshness, and remote-call consequence.
- Run progress and terminal states remain inspectable without clearing current local content.
- Validated results apply through FEAT-0046 idempotently: no-change updates check evidence only, changed content is hash-gated, and failures retain last-known content and local organization.
- Per-target `resolved`, `unchanged`, `changed`, `unavailable`, `not_found`, and `error` outcomes remain distinguishable after a partial Run.
- No refresh generates summaries, Topics, Tags, Workstream relationships, or external writes.
- There is no scheduler, background polling, implicit page-load refresh, or automatic retry loop.

## Scope Boundary

- In:
  - Item, Space, Thread, Workstream, and all-known scope resolution
  - local preview and inclusion selection
  - freshness-aware defaults and timestamps
  - Space coverage and bounded pagination expectation
  - one maintenance Run handoff
  - progress and terminal outcome presentation
  - validated result application and last-known retention
  - retry of explicitly selected failed or unavailable targets
  - responsive, focus, history, and partial-success behavior
- Out:
  - background or scheduled synchronization
  - live remote search
  - automatic refresh from opening related local content
  - all-company enumeration
  - summaries, classifiers, Topics, Tags, or Workstream Suggestions
  - destructive purge
  - external writes
  - general Atlassian browse, detail, and search owned by FEAT-0050

## Surface Lanes

- Scope and preview contract lane:
  - path roots: Atlassian and Workstream scope resolvers, preview query projection, and request models
  - dependencies: FEAT-0046 and FEAT-0048 passed
  - expected evidence: exact Item/Space/Thread/Workstream/all-known target sets, deduplication, freshness-aware defaults, and zero remote preview calls
  - evaluator ownership: `contract`, `functional`
- Run and result lane:
  - path roots: FEAT-0045 Run composition, progress projection, FEAT-0046 result application, and runtime tests
  - dependencies: scope and preview lane plus FEAT-0045 passed
  - expected evidence: selected manifest, read-only execution, no-change, changed, partial, unavailable, cancellation, retry, and last-known preservation
  - evaluator ownership: `contract`, `functional`
- Interaction lane:
  - path roots: Atlassian, Workstream, and Thread contextual actions; preview surface; Run handoff; route-scoped client behavior; styles; browser tests
  - dependencies: scope and Run lanes
  - expected evidence: clear action scope, stable shell, checkbox control, progress, terminal outcomes, focus restoration, back/forward behavior, and responsive containment
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- Refresh scope resolver for Item, Space, Thread, Workstream, and all-known.
- Local preview query and selection payload.
- Freshness-aware default-selection rule.
- FEAT-0045 manifest and Run identity.
- FEAT-0046 result application and retention.
- Progress, partial-success, retry, cancellation, and terminal state projection.
- Contextual action and status scope parity.

## Required Evaluators

- `contract`: scope membership, deduplication, preview no-remote guarantee, manifest/result handoff, freshness, retention, and source ownership.
- `design`: action hierarchy, target density, checkbox and status clarity, progress, partial outcomes, long labels, responsive layout, and shell stability.
- `functional`: every scope, current/stale defaults, selection changes, no-change, changed, partial, unavailable, not-found, invalid result, retry, cancel, history, and zero implicit calls.
- `ux-heuristic`: confidence before spending calls, scope comprehension, action-wall avoidance, partial failure recovery, and Workstream/Thread context continuity.

## User-Visible Outcome

- The user can see exactly which known Atlassian resources will be checked, adjust the selection, run one explicit maintenance refresh, and understand what changed without losing prior usable context.

## Entry And Exit

- Entry point: contextual refresh from an Item, Space, Thread, Workstream, or the Atlassian inventory.
- Exit or transition behavior: single-target actions return to their owning context; multi-target preview starts one Run and returns or links to refreshed context while preserving a reviewable terminal summary.

## State Expectations

- Default: scope summary and local freshness are visible before execution.
- Preview: selected and unselected targets remain editable with no external activity.
- Running: current local content remains readable and the Run owns progress.
- No change: check time advances without body or FTS rewrite.
- Partial: each target keeps its own terminal outcome and retry eligibility.
- Unavailable or not found: last-known content remains visible and labeled.
- Cancelled or interrupted: observed outcomes and Usage remain; unprocessed targets do not appear successful.
- Success: validated changed targets update once and the user returns with preserved orientation.

## Dependencies

- FEAT-0044, FEAT-0045, FEAT-0046, and FEAT-0048 must be `passed`.
- Workstream and Thread link contracts remain authoritative for mapped scope.
- FEAT-0047 may supply discovered Items but is not required for refresh correctness.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- `src/localbrain/runner.py`
- FEAT-0046 Atlassian domain/query/result-application modules
- `src/localbrain/workstreams.py`
- `src/localbrain/templates/atlassian.html`
- `src/localbrain/templates/workstream.html`
- refresh preview and Run status templates or partials
- `src/localbrain/static/styles.css`
- route-scoped interaction code under `src/localbrain/static/`
- Runner, Workstream, scope, query, route, interaction, responsive, and partial-failure tests
- Product, maintenance, privacy, and external-source owner documentation

## Pass Or Fail Checks

- Pass if every scope resolves exactly the approved known Items and deduplicates Workstream plus Thread links.
- Pass if preview performs zero remote calls and exposes count, selection, freshness, coverage, and timestamps.
- Pass if default selections match the PRD and users can override them before execution.
- Pass if one selected manifest starts one read-only maintenance Run and progress remains attributable.
- Pass if no-change, changed, partial, unavailable, not-found, cancellation, retry, and invalid-result paths preserve last-known and local state correctly.
- Pass if ordinary page loads, search, browsing, and Workstream navigation produce zero external and zero synchronization-model calls.
- Pass if long target sets and states remain usable at `1440`, `920`, `700`, and `320`.
- Fail on hidden refresh, all-company enumeration, duplicate execution, local-state loss, unvalidated content application, action/status scope mismatch, or write-tool access.

## Regression Surfaces

- Existing Workstream, Thread, Resource, checkpoint, and maintenance Run behavior.
- FEAT-0048 registration and Source Instance orientation.
- Existing Runner console, cancellation, Usage, and Session exclusion.
- Shared shell, browser history, focus, and responsive navigation.
- Search and local content availability during provider failure.

## Harness Trace

- Active spec doc: [spec-0049-explicit-atlassian-refresh-and-preview](../spec/spec-0049-explicit-atlassian-refresh-and-preview.md)
- Active run: [run-20260723-54-explicit-atlassian-refresh-and-preview](../run/run-20260723-54-explicit-atlassian-refresh-and-preview.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  - [contract](../evaluation/eval-0049-contract-explicit-atlassian-refresh-and-preview.md)
  - [design](../evaluation/eval-0049-design-explicit-atlassian-refresh-and-preview.md)
  - [functional](../evaluation/eval-0049-functional-explicit-atlassian-refresh-and-preview.md)
  - [ux-heuristic](../evaluation/eval-0049-ux-explicit-atlassian-refresh-and-preview.md)
- Latest fix note: not created

## Open Review Decisions

- None. Thread uses the lightweight local preview. The product batch is capped at 20 calculated provider requests within the existing 500-target foundation ceiling. Jira Space refresh resolves known selected Items only; Confluence exposes one explicit regular-Page catalog page of at most 200 results and later explicit body batches.

## Continuity Notes

- `2026-07-23`: initial draft kept all refresh scopes in one product Feature because they share one target-selection, preview, maintenance handoff, result-application, and failure-recovery workflow.
- `2026-07-23`: owner-approved sequential execution and recommended decisions advanced the Feature to RUN-20260723-54. SPEC-0049 also resolves the existing one-Source FEAT-0045 envelope mismatch through additive per-target Source Instance authorization so one mixed Workstream/all-known action remains one inspectable maintenance Run.
- `2026-07-23`: attempt 1 passed all four required evaluations with an exact local preview, 20-read hard product batch, one mixed-instance Run, atomic host-validated application, bounded Confluence catalog expansion, responsive UI, and 250 passing regressions.
