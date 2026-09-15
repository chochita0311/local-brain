# SPEC-0088: Workflow Assertion And Correction Contract

## Metadata

- ID: `spec-0088`
- Status: `approved`
- Run: [RUN-20260914-98](../run/run-20260914-98-workflow-assertion-and-correction-contract.md)
- Attempt: `1`
- Parent Feature: [FEAT-0088](../feature/feat-0088-workflow-assertion-and-correction-contract.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-14`
- Updated: `2026-09-14`

## Source Set

- Human approval to execute FEAT-0085 through FEAT-0089 in dependency order.
- Passed FEAT-0085 Episode/direction contract, FEAT-0086 Focus projection, and
  FEAT-0087 read-only map.
- Approved FEAT-0088, current schema/migration conventions, Data Model and value
  dictionaries, Privacy, Product, and Architecture owners.

## Implementation Goal

- Add one local, append-only, user-owned workflow assertion ledger and a
  deterministic overlay API so FEAT-0089 can preview, commit, undo, and explain
  corrections without modifying source evidence or current organization.

## Persistence Contract

- `workflow_assertions` is the only new durable owner. It stores a local row ID,
  deterministic 64-character boundary key, positive boundary version,
  `relation` or `lifecycle` boundary kind, one of the exact five assertion
  kinds, an `is_undo` bit, stable source/optional target Episode keys, nullable
  Session lookup aids, canonical before/after meanings, before/after closure
  reasons, optional normalized note of at most 1,000 code points,
  `user-confirmed` authority, exact v1 contract version, optional superseded
  assertion, and explicit UTC creation time.
- Relation meanings are exactly `relation:absent`, `relation:continues`,
  `relation:branches-from`, and `relation:merged-into`. Lifecycle meanings are
  exactly `lifecycle:unknown`, `lifecycle:open`, and `lifecycle:closed`.
- `same-flow`, `split-here`, and `merge-into` own relation boundaries. `close`
  and `reopen` own lifecycle boundaries. Closure reasons are present if and
  only if their corresponding meaning is closed and use the FEAT-0085 five
  values.
- `UNIQUE(boundary_key, boundary_version)` and unique nullable
  `supersedes_assertion_id` prevent chain forks. The supersession FK is
  `RESTRICT`; Session lookup aids are `SET NULL`, so deleting a source Session
  never deletes or rewrites assertion history.
- Ordinary application behavior never updates or deletes an assertion. A new
  action or undo appends one next-version row whose `supersedes_assertion_id`
  names the previously active row when one exists.

## Mutation Contract

- `apply_workflow_assertion` receives a current ready Focus projection, exact
  action/endpoints, optional close reason/note, expected active assertion ID,
  and expected projection revision. It opens a bounded savepoint, performs
  validation, appends exactly one row, and returns the new effective projection;
  callers own the outer commit.
- A relation action resolves both Episode keys from the passed projection and
  verifies strict forward observed time. Self-edge, missing endpoint,
  time-reversed relation, merge-before-source, and a path from target back to
  source fail before insertion.
- `split-here` requires the current effective pair to be `continues`. `close`
  requires a current tip. `reopen` requires the current active user closure.
  Unsupported reason/note/action shapes fail before insertion.
- An exact active repeat returns `duplicate-active`. A different active state
  requires the caller's exact active assertion ID and becomes the next
  superseding row; missing or mismatched optimistic state returns `conflict`.
- `undo_workflow_assertion` accepts only the current active row in its chain and
  appends a row with the same five-value assertion kind, `is_undo = 1`, and its
  before/after values reversed. Undoing an undo follows the same rule and is a
  deterministic redo without deleting history.
- Every domain rejection exposes a bounded stable code and leaves both history
  and the passed projection unchanged. SQLite constraint or insertion failure
  rolls back the function-owned savepoint.

## Overlay And Read Contract

- `workflow_focus_projection` builds the same FEAT-0086 base first, then applies
  active relevant assertions through `localbrain.workflow-assertion-overlay.v1`.
  Missing and ineligible projections do not query or apply assertions.
- The effective relation set replaces or removes only the asserted source/
  target pair. A user relation has `user-confirmed` authority and one
  `user-assertion` reason. The complete unmodified candidate relation set stays
  in `base_relations`, and active assertion summaries name their base/effective
  meanings so later Trace can explain both layers.
- Active lifecycle assertions change only the effective Episode lifecycle and
  retain a `base_episode_lifecycle` snapshot. They never infer completion from
  Session end, age, quietness, or absence.
- Active assertions with a missing endpoint, invalidated time order, or a cycle
  after source reconstruction remain in the ledger and appear as unresolved
  overlay summaries. They do not silently apply, disappear, or rewrite their
  original meaning.
- The overlay exposes a deterministic revision derived from base Episode/time,
  base relation, and active assertion identities. Mutation compares it before
  writing, allowing FEAT-0089 to reject a stale client projection locally.
- `workflow_assertion_history` returns a chronological, bounded chain with
  observed/retained totals and active state. No history read opens source files,
  calls a connector/model, or mutates state.

## Fresh And Compatible Database Contract

- Fresh DDL and normal idempotent schema application create the same table,
  constraints, two Episode-key lookup indexes, and self/Session foreign keys.
  No retained row in another table is rewritten and no backup-only table repair
  is required for this additive owner.
- Data Model ownership, global and subject ERDs, value registry/dictionaries,
  Schema Presentation, schema cleanup decisions, Product, Architecture, and
  Privacy are updated in the same Run.

## Out Of Scope

- Routes, forms, buttons, dialogs, visible correction copy, or map-controller
  mutation; FEAT-0089 owns those surfaces.
- Workstream/Thread migration or lens membership, source/Git/external mutation,
  automatic correction, Qwen, embeddings, model calls, or learning.

## Acceptance Mapping

- Schema tests cover fresh/compatible creation, exact values, shape constraints,
  indexes, FK deletion effects, and generated-owner parity.
- Domain tests cover create/repeat/correction, split, merge, close/reopen, undo,
  stale revision, missing endpoint, time order, cycle, tip, rollback, and note
  bounds.
- Overlay tests cover precedence, retained base reasons, unresolved source,
  rebuild/re-resolution, lifecycle, deterministic revision, and zero writes.
- Full regression, schema/data/value generation, privacy, and diff checks cover
  current Session, Workstream, source, and technical surfaces.

## Open Blockers

- None.

## Continuity Notes

- `2026-09-14`: approved for RUN-20260914-98 after FEAT-0087 passed. Foundation
  Contract is active; no visible surface or model dependency is included.
