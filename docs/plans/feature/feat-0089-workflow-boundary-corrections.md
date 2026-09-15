# FEAT-0089: Workflow Boundary Corrections

## Metadata

- ID: `feat-0089`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0017: Source-Backed Workflow Map And Workstream Lenses](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-14`
- Updated: `2026-09-14`

## Goal

- Let the user correct a consequential Focus boundary through a few contextual
  actions while preserving map orientation, source history, reversibility, and
  all existing product behavior.

## Acceptance Contract

- The FEAT-0087 Trace inspector exposes only actions valid for the selected
  Episode, edge, and current FEAT-0088 effective assertion state.
- The action set is `같은 흐름`, `여기서 분기`, `여기로 병합`, `종료`, and
  `다시 열기`; the current active user assertion also exposes one bounded
  `되돌리기` action when FEAT-0088 permits it.
- Selecting an action first shows its exact before/after relation or lifecycle
  consequence, affected Episode titles, authority change, and whether a prior
  assertion will be superseded. No correction is committed by selection alone.
- `같은 흐름`, `여기서 분기`, and `여기로 병합` require explicit source and
  destination Episodes. `종료` requires one FEAT-0088 close reason and allows a
  bounded optional note. `다시 열기` targets the current active closure.
- Successful submit changes only the FEAT-0088 assertion layer and reprojects
  the bounded local map. It never changes Session content, direct evidence,
  Workstream/Thread links, external sources, or the deterministic candidate's
  retained reasons.
- After success, the same selected Episode, scale, pan/scroll position, expanded
  branches, evidence disclosure, outer page scroll, and meaningful keyboard
  focus remain stable. The changed edge or tip and its user-confirmed authority
  receive the primary feedback.
- Failure preserves the prior graph and all interaction state, places a clear
  recovery message beside the owning action, and never falls back to a hidden
  refresh or optimistic durable state.
- Undo and reopen explain which assertion they supersede and restore the prior
  effective boundary without erasing history. Repeated actions do not create
  duplicate active assertions.
- Candidate, explicit-organization, and user-confirmed states remain
  distinguishable structurally and textually without color alone. Trace keeps
  the original reasons available after correction.
- Correction controls are keyboard-operable, screen-reader-labeled, usable
  with reduced motion, and transformed into ordinary sequential forms at narrow
  widths without a nested-scroll trap.
- Direct entry, browser back/forward, opening evidence, returning, and a
  concurrent stale-projection response preserve an understandable recovery path
  and never strand the user in an obsolete modal or disabled canvas.
- No correction invokes Qwen, embeddings, a model, source ingestion, connector
  discovery, capability inspection, Atlassian Sync/Refresh, remote reads,
  external writes, Git mutation, or background learning.
- Workstream naming/promotion, lens membership, Atlas, topic terrain, automatic
  correction, and using dismiss/silence as labels remain outside this Feature.

## Scope Boundary

- In:
  - valid action availability in the selected Focus Trace inspector
  - before/after consequence preview and confirmation
  - same-flow, split, merge, close, reopen, and bounded undo submission
  - success, failure, conflict/stale, feedback, and projection refresh behavior
  - focus, history, keyboard, scroll, pan/scale, expansion, and responsive
    continuity
- Out:
  - assertion identity/schema or semantics owned by FEAT-0088
  - Workstream lens promotion, main/supporting designation, Thread migration,
    or Atlas
  - bulk graph editing, arbitrary edge drawing, drag-to-connect, or freeform
    layout
  - model feedback, semantic learning, source mutation, or external operations

## Surface Lanes

- Assertion API lane:
  - path roots: workflow assertion routes/controllers, FEAT-0088 domain owner,
    request validation, transaction and integration tests
  - dependencies: passed FEAT-0088 contract
  - expected evidence: exact payloads, allowed actions, atomic conflict/error,
    effective projection, undo/reopen, and zero external I/O
  - evaluator ownership: `contract`, `functional`
- Focus interaction lane:
  - path roots: workflow Trace inspector, consequence preview, form/controller,
    feedback, semantic styles, browser tests
  - dependencies: stable assertion API and passed FEAT-0087 map
  - expected evidence: contextual availability, confirmation clarity, stable
    focus/viewport/history/scroll, accessibility, and four widths
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Regression/owner lane:
  - path roots: Session, Workstream, Local Context, Atlassian, navigation,
    data-model, generated-artifact, and privacy checks
  - dependencies: both implementation lanes
  - expected evidence: assertions are the only changed durable owner
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- Correction action request/response and FEAT-0088 assertion mapping.
- Action availability, before/after preview, confirmation, conflict, error, and
  feedback states.
- Reprojection and preservation of focus, scale, pan/scroll, expansion, browser
  history, and keyboard focus.
- Trace authority/reason disclosure and source mutation exclusion.

## Required Evaluators

- `contract`: action-to-assertion mapping, mutation ownership, route/payload,
  stale/conflict, undo, source safety, and no-external-I/O boundaries.
- `design`: action hierarchy, consequence preview, authority distinction,
  feedback, responsive composition, and four-width containment.
- `functional`: every action, validation, success, failure, stale state, repeat,
  undo/reopen, focus/history/scroll preservation, and regressions.
- `ux-heuristic`: consequence comprehension, correction effort, error recovery,
  keyboard flow, and confidence in candidate versus confirmed state.

## User-Visible Outcome

- The user can correct whether work continued, branched, merged, closed, or
  reopened without manually recreating a Workstream or losing the evidence and
  map position that motivated the decision.

## Entry And Exit

- Entry point: a valid selected Episode or relation in the Session Workflow
  Focus Trace inspector.
- Exit or transition behavior: confirm one correction and remain on the same
  focused map with the effective result visible, cancel with no change, or
  recover from a local validation/conflict error in place.

## State Expectations

- Default: only valid contextual actions are offered.
- Preview: exact consequence and affected endpoints are visible; no write yet.
- Working: only the owning action group is disabled and progress is bounded.
- Success: asserted boundary and authority update without orientation loss.
- Conflict/stale: prior projection remains and an explicit reload/review path is
  offered.
- Error: no optimistic state survives and retry remains local.
- Narrow/no-script: sequential forms preserve the same consequence and result
  contract.

## Dependencies

- FEAT-0087 and FEAT-0088 must be `passed` before this Feature enters build.
- Passed FEAT-0087 evidence must confirm that the proposed actions fit the
  bounded Focus interaction without broad graph editing.
- Existing form, feedback, browser-history, and technical-canvas interaction
  contracts remain implementation baselines.

## Likely Affected Surfaces

- workflow assertion API routes and controllers
- FEAT-0088 assertion and FEAT-0086 projection overlay owners
- FEAT-0087 workflow template, Trace partials, controller, and semantic styles
- focused API, interaction, browser-history, responsive, no-script, and
  regression tests
- product, architecture, privacy, design, and interaction owner docs as needed

## Pass Or Fail Checks

- Pass if each contextual action previews and commits exactly one FEAT-0088
  meaning and invalid actions never appear enabled.
- Pass if correction success changes only assertion state and leaves original
  candidate/source reasons inspectable.
- Pass if failure, conflict, cancel, repeat, undo, and reopen preserve the prior
  durable and visible state correctly.
- Pass if selected Episode, focus, scale, pan/scroll, branches, history, and
  meaningful keyboard focus remain stable after every result.
- Pass if controls and feedback work at `1440`, `920`, `700`, and `320`, with
  keyboard, reduced motion, and no-script paths.
- Pass if Session, Workstream, Local Context, Atlassian, Search, Schema, and
  Runner regressions remain unchanged and no excluded external/model operation
  occurs.
- Fail if correction requires arbitrary canvas editing, silently rewrites a
  deterministic candidate, or treats inactivity/dismissal as completion.

## Regression Surfaces

- FEAT-0087 read-only Focus entry, topology, evidence, fallback, and navigation.
- FEAT-0088 assertion identity, history, conflict, and undo.
- Session detail, Related Materials, and source destinations.
- Workstream/Thread/checkpoint/Resource/Suggestion behavior.
- Atlassian and Local Context local/remote action separation.
- Shell, forms, responsive interaction, generated owners, and privacy.

## Harness Trace

- Spec doc: [SPEC-0089](../spec/spec-0089-workflow-boundary-corrections.md).
- Run: [RUN-20260914-99](../run/run-20260914-99-workflow-boundary-corrections.md).
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  [contract](../evaluation/eval-0089-contract-workflow-boundary-corrections.md),
  [design](../evaluation/eval-0089-design-workflow-boundary-corrections.md),
  [functional](../evaluation/eval-0089-functional-workflow-boundary-corrections.md),
  and [UX heuristic](../evaluation/eval-0089-ux-workflow-boundary-corrections.md).
- Latest fix note:
  [FIX-0089](../fix/fix-0089-workflow-correction-restoration-snapshot.md).

## Open Review Decisions

- None. The owner approved the contextual action set. Workstream promotion and
  Atlas remain intentionally outside this correction loop.

## Continuity Notes

- `2026-09-14`: proposed as the final Feature in the first PRD-0017 chain. It
  remains queued behind read-only Focus validation and the durable assertion
  foundation.
- `2026-09-14`: owner approved sequential execution. FEAT-0089 remains queued
  behind passed FEAT-0087 and FEAT-0088.
- `2026-09-14`: FEAT-0088 passed; RUN-20260914-99 entered Build under the
  Fullstack Product profile with Assertion API, Focus interaction, and
  regression/owner lanes.
- `2026-09-14`: all four required evaluators passed. Contextual preview,
  append-only correction, stable orientation restoration, failure/no-script
  recovery, four-width containment, and the model-free boundary passed after
  one focused orientation-restoration fix; the approved FEAT-0085 through
  FEAT-0089 chain is complete.
