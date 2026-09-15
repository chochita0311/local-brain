# FEAT-0088: Workflow Assertion And Correction Contract

## Metadata

- ID: `feat-0088`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017: Source-Backed Workflow Map And Workstream Lenses](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-14`
- Updated: `2026-09-14`

## Goal

- Establish one durable, reversible user assertion layer for consequential
  workflow boundaries without rewriting source evidence, deterministic
  candidates, existing Workstream organization, or external systems.

## Acceptance Contract

- User correction is stored in a dedicated local assertion owner, separate
  from Sessions, Activity Events, derived reference evidence, deterministic
  relation candidates, Workstream/Thread links, and Suggestions.
- Assertions target FEAT-0085 stable Episode keys rather than transient local
  row IDs. A current `sessions.id` may be retained only as a resolvable lookup
  aid and cannot be the sole durable identity.
- The initial assertion vocabulary is exactly:
  - `same-flow`: assert `continues` from one earlier Episode to one later
    Episode;
  - `split-here`: replace one selected `continues` boundary with
    `branches-from` while retaining the earlier Episode as the branch origin;
  - `merge-into`: assert `merged-into` from one earlier branch Episode to one
    later destination Episode;
  - `close`: close one selected tip with an explicit reason;
  - `reopen`: supersede the active closure on one selected tip.
- `close` reasons are `completed`, `abandoned`, `superseded`, `merged`, or
  `other`. Quietness, age, Session end, dismissal, and lack of use never create
  or imply a close assertion.
- Every assertion records its stable target identity, assertion kind, before
  and after meaning, optional bounded user note, creation time, user authority,
  contract version, and the assertion it supersedes when applicable.
- Assertion history is append-only for ordinary product actions. Correction,
  reopen, and undo create a new superseding record rather than overwriting or
  deleting the earlier assertion.
- Undo is allowed only for the current active assertion in the selected
  boundary chain. It creates an explicit superseding reversal and restores the
  prior effective projection deterministically.
- Self-relations, time-reversed edges, cycles, merge-before-source, duplicate
  active assertions, missing endpoints, and contradictory unsuperseded
  assertions are rejected atomically with no partial record.
- The effective projection applies active user assertions after the source and
  deterministic-candidate layers. User assertions control the presented
  boundary but never delete the underlying candidate or its reasons; Trace can
  still explain both.
- A missing or temporarily unresolvable source Episode leaves its assertion
  retained and explicitly unresolved. Source deletion, rescan, parser change,
  projection rebuild, or future model replacement cannot silently cascade or
  reinterpret user-owned correction history.
- Existing Workstream and Thread records are not assertion storage and are not
  migrated in this Feature. A later Workstream lens contract may reference
  active assertions without changing their global Episode-to-Episode meaning.
- Assertion mutation is local-only and user-initiated. It performs no source
  file write, Git operation, Jira/Wiki mutation, external message, connector
  call, Refresh, model call, or background retraining.
- Fresh and compatible databases converge on the same constraints, indexes,
  lifecycle, generated schema presentation, value registry, deletion/recovery
  rules, and privacy contract without altering existing records.

## Scope Boundary

- In:
  - stable assertion identity and dedicated persistence ownership
  - same-flow, split-here, merge-into, close, and reopen meanings
  - close reasons, append-only supersession, effective state, and undo
  - validation, conflict, cycle, missing-source, deletion, and rebuild behavior
  - projection-overlay read contract and schema/data-model documentation
- Out:
  - correction buttons, forms, dialogs, map interaction, or product copy
  - Workstream lens membership, main/supporting derivation, Thread migration,
    or Atlas
  - automatic acceptance/rejection, feedback learning, embeddings, or Qwen
  - source, Git, Atlassian, Slack, Mail, or other external mutation

## Contract Surfaces

- Durable workflow assertion identity, value shape, indexes, and uniqueness.
- Assertion kind, closure reason, before/after meaning, supersession, and
  effective-state rules.
- Stable Episode-key resolution and unresolved-source lifecycle.
- Atomic validation, cycle prevention, conflict behavior, undo, and recovery.
- Projection overlay producer/consumer contract and separation from source,
  derived, explicit-organization, and Suggestion owners.

## Required Evaluators

- `contract`: schema, identity, vocabulary, ownership, lifecycle, deletion,
  recovery, privacy, projection precedence, generated owners, and downstream
  readiness.
- `functional`: fresh/compatible migration, create, repeat, conflict, cycle,
  close/reopen, undo, missing source, rebuild, rollback, and zero-external-I/O
  behavior with synthetic data.

## User-Visible Outcome

- None required in this Foundation Feature. Current maps remain read-only until
  FEAT-0089 consumes the passed assertion contract.

## Entry And Exit

- Entry point: one validated user-requested correction against a current
  FEAT-0085 projection boundary.
- Exit or transition behavior: atomically append one assertion and return the
  new effective boundary, or reject the request while preserving the prior
  projection and assertion history.

## State Expectations

- Active: latest valid assertion determines the effective selected boundary.
- Superseded: historical assertion remains inspectable but has no current
  projection authority.
- Reopened/undone: a new record restores the prior effective state.
- Unresolved source: assertion remains durable and visibly non-applicable until
  its Episode key resolves again.
- Conflict/invalid/cyclic: no write occurs.
- Error: transaction rollback preserves prior effective state and history.

## Dependencies

- FEAT-0085 and FEAT-0086 must be `passed` before this Feature enters build.
- FEAT-0087 must pass read-only Focus evaluation before this Feature enters
  build, so the durable action set consumes a proven interaction contract.
- Current Workstream/Thread/Suggestion contracts remain regression owners, not
  storage for workflow assertions.

## Likely Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- a dedicated workflow assertion domain module under `src/localbrain/`
- FEAT-0086 projection overlay boundary
- `src/localbrain/schema-presentation.json`
- `src/localbrain/value-registry.json`
- schema/value generators and integrity, migration, projection, privacy tests
- product, architecture, privacy, and Session activity data-model owner docs

## Pass Or Fail Checks

- Pass if every assertion has one stable owner and survives projection rebuild,
  parser/version change, missing source rows, and future optional model removal.
- Pass if all five actions and five close reasons have exact, non-overlapping
  meanings and deterministic effective-state behavior.
- Pass if supersession and undo retain history while restoring the expected
  prior boundary.
- Pass if invalid time order, self-edge, cycle, duplicate, conflict, and missing
  endpoint writes fail atomically.
- Pass if underlying source evidence and deterministic candidate reasons remain
  inspectable after an assertion changes presentation.
- Pass if fresh and compatible schema, generated artifacts, deletion/recovery,
  and privacy contracts agree.
- Fail if FEAT-0089 must guess assertion identity, consequence, undo, error, or
  source-deletion behavior.

## Regression Surfaces

- Session/source identity, synchronization, and deletion reconciliation.
- Session reference evidence and deterministic workflow projection.
- Workstream/Thread links, checkpoints, Resources, and Suggestions.
- Atlassian and Local Context persistence and explicit operations.
- Schema Explorer, generated data-model/value artifacts, and privacy.

## Harness Trace

- Spec doc: [SPEC-0088](../spec/spec-0088-workflow-assertion-and-correction-contract.md).
- Run: [RUN-20260914-98](../run/run-20260914-98-workflow-assertion-and-correction-contract.md).
- Execution profile: `foundation-contract`
- Latest evaluator reports:
  [Contract](../evaluation/eval-0088-contract-workflow-assertion-and-correction-contract.md)
  and
  [Functional](../evaluation/eval-0088-functional-workflow-assertion-and-correction-contract.md),
  both `PASS`.
- Latest fix note: not created.

## Open Review Decisions

- None. The owner approved the append-only supersession model and exact
  five-action vocabulary. The Feature entered execution after FEAT-0087 passed
  and now supplies the passed assertion foundation consumed by FEAT-0089.

## Continuity Notes

- `2026-09-14`: proposed as a later foundation gate so correction remains
  reversible and source-safe without delaying the first read-only Focus Map.
- `2026-09-14`: owner approved sequential execution. FEAT-0088 remains queued
  and cannot enter build until FEAT-0085 through FEAT-0087 pass.
- `2026-09-14`: FEAT-0085 through FEAT-0087 passed; RUN-20260914-98 entered
  Build under the Foundation Contract profile.
- `2026-09-14`: the append-only ledger, fresh revision check, projection
  overlay, deletion/re-resolution behavior, generated owners, 538-test full
  regression, and privacy gates passed; FEAT-0089 is unblocked.
