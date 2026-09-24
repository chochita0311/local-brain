# FEAT-0093: Workstream Candidate Review And Promotion Contract

## Metadata

- ID: `feat-0093`
- Status: `superseded`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-15`
- Updated: `2026-09-15`

## Supersession Boundary

The owner rejected repeated promotion and per-snapshot membership approval as
the basis of the replacement product. This unexecuted proposal is superseded
by [PRD-0017 replanning](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md#reconciliation-and-approval-state).
The remaining sections preserve the former contract proposal only. A future
foundation must separate automatically maintained inferred flows, optional
durable corrections, and controlled legacy transition; it must not inherit
this proposal's mandatory promotion pipeline.

## Goal

Own explicit candidate review decisions and their promotion into durable
Workstreams, with exact consequences, provenance, conflict handling, and undo.

## Acceptance Contract

- User review state has a dedicated durable local owner, distinct from source
  evidence, ephemeral candidates, existing Suggestions, and global
  `workflow_assertions`. It records stable seed/member evidence keys, reviewed
  revision, action, user authority, time, and supersession/history.
- The inferred baseline remains rebuildable. Candidate decisions survive source
  disappearance and reprocessing as resolved or unresolved user assertions;
  labels or similar replacement candidates cannot silently retarget them.
- Rename changes the review label only. Merge combines explicitly selected
  candidate scopes, retaining each origin and membership reason. Split creates
  two explicit nonempty scopes from selected evidence; a Session can remain in
  both with separate reasons. These actions do not change global Episode edges
  or merge/split existing Workstreams and Threads.
- Ignore hides the reviewed candidate from the default review list and is
  restorable. It is not a rejection/training label, source deletion, or workflow
  closure. Supersession and undo preserve the decision history.
- Promotion requires a current reviewed snapshot, exact destination choice,
  confirmed name/outcome for a new Workstream, and a preview of link additions.
  It is an explicit local transaction, never a consequence of candidate reads,
  correction, similarity, or an existing matching Workstream name.
- New promotion creates an ordinary Workstream using its confirmed name and
  intended outcome in the existing summary field. It creates no default Thread,
  checkpoint, Resource, or maintenance Run. A duplicate name is a conflict that
  requires explicit destination selection or renaming.
- Promotion to an existing Workstream preserves its name, summary, status,
  Threads, checkpoints, and previous links. It adds only the reviewed linkable
  members under existing Workstream link semantics. A Session link does not
  assert that every topic in the Session belongs to that Workstream.
- Existing matching links are reused without rewriting their provenance.
  Non-linkable or unresolved evidence remains in the review snapshot with an
  explicit reason; it cannot cause automatic Resource creation, a blanket
  Project link, or membership expansion. The snapshot retains candidate-specific
  evidence so a Workstream link cannot erase why the member was approved.
- Each promotion receipt owns the exact newly created link identities and its
  reviewed snapshot. Newly inferred members and changed boundaries remain
  pending proposals until the user reviews and explicitly applies another
  snapshot. The producer must not amplify its own promotions as independent
  source evidence.
- Mutation rechecks both candidate and target organization revisions before
  committing. Invalid inputs, stale evidence, duplicate/conflicting actions,
  missing targets, and late failures roll back completely; repeat submission
  cannot create a duplicate Workstream or duplicate active promotion.
- Undo supersedes the current review action and restores only effects still
  owned by that action. It preserves pre-existing links and independent later
  user edits, and rejects an unsafe partial reversal as a conflict. A Workstream
  created by promotion remains user-owned; undo does not delete it automatically.
- Fresh and compatible databases, generated schema/value docs, source-deletion
  behavior, and local privacy contracts agree. No operation writes a source,
  uses a model, retrains from feedback, or accesses an external system.

## Scope Boundary

- In: review/promotion persistence, action semantics, stable references,
  append-only history/supersession, exact previews, transaction ownership,
  idempotency, stale conflicts, owned-effect undo, and read overlays.
- Out: buttons/forms/routes, Workstream Lens, main/supporting path inference,
  Atlas, Thread migration, existing Workstream merge/split/delete, source
  adapters, model feedback, and external operations.

## Contract Surfaces

- Candidate review identity, schema, revision, lifecycle, and effective overlay.
- Preview-to-commit snapshot and existing Workstream/link owner integration.
- Promotion receipt, duplicate submission, undo, conflict, and deletion recovery.
- Generated schema/value/data-model artifacts and privacy owner parity.

## Required Evaluators

- `contract`: exact action semantics, ownership, source retention, revision,
  transaction boundaries, generated owners, and downstream UI readiness.
- `functional`: fresh/compatible schema, all actions, overlapping membership,
  repeat submit, target conflict, rollback, undo, source loss, and rebuild.

## Entry And Exit

- Entry: one explicit action against a reviewed candidate revision; promotion
  also names an exact existing or new destination and link set.
- Exit: one atomic user-owned review/promotion result with history, or a bounded
  conflict/error preserving every previous owner.

## State Expectations

- Inferred: baseline has no durable organization authority.
- Corrected/ignored: user review overlay changes only its named scope.
- Promoted: one reviewed snapshot and its exact effects are recorded.
- Changed/unresolved: later evidence needs review; previous decisions survive.
- Superseded/undone: history remains; only valid active effects apply.
- Conflict/error: no partial write or lost independent edit.

## Dependencies

- FEAT-0090 and FEAT-0091 must pass; their identity/producer shapes are inputs.
- [FEAT-0092](feat-0092-workstream-candidate-evidence-review.md) must pass and its
  separate human usefulness review must accept proceeding before this Feature
  is approved for Spec or build. A failed review may change this proposal.
- Existing Workstream/Thread/Suggestion and Focus assertion contracts remain
  distinct authorities; none is migrated implicitly.

## Likely Affected Surfaces

- A dedicated candidate review/promotion domain owner under `src/localbrain/`.
- `schema.sql`, compatible database upgrade handling, candidate read overlays,
  and explicit Workstream/link integration.
- Generated schema/value/data-model owners and synthetic persistence tests.
- Product, architecture, privacy, and data lifecycle owner sections.

## Pass Or Fail Checks

- Verify exact rename/merge/split/ignore/restore behavior and many-to-many
  evidence without changing any global Focus assertion or existing Thread.
- Verify new and existing destination promotion against independently checked
  before/after records; only previewed writes may occur.
- Verify repeat submission, duplicate name, changed target, source removal,
  failed write, re-resolution, and later-evidence cases atomically.
- Verify undo removes only owned additions, retains independent/pre-existing
  links, preserves the created Workstream, and cannot erase unrelated edits.
- Verify all source, inferred, review, and existing organization owners retain
  provenance; ignored or unviewed candidates never become correctness labels.
- Fail if FEAT-0094 must guess an action's target, consequence, persistence,
  conflict, unresolved-source behavior, or recovery.

## Regression Surfaces

- Workstream/Thread identity, links, checkpoints, Suggestions, and Runs.
- Focus correction ledger and evidence projection.
- Session/source deletion, Atlassian/Local Context retention, and Schema Explorer.

## Harness Trace

- Spec doc: not created; discovery review and Feature approval pending.
- Run: not started.
- Execution profile: `foundation-contract`.
- Latest evaluator reports: none.
- Latest fix note: none.

## Open Review Decisions

- Reconfirm the action set after FEAT-0092's usefulness review.
- Approve or revise the additive promotion boundary: new name/outcome, existing
  destination preservation, exact link additions, separately retained evidence,
  and undo that preserves the Workstream container.

## Continuity Notes

- `2026-09-15`: proposed as a separate durable ownership gate so UI work cannot
  invent promotion, review history, or migration semantics.
- `2026-09-15`: superseded by the automatic-reconstruction replan; mandatory
  per-snapshot promotion is not its normal update model. No Spec, Run, schema,
  persistence code, or evaluation was started.
