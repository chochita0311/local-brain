# FEAT-0094: Workstream Candidate Correction And Promotion

## Metadata

- ID: `feat-0094`
- Status: `superseded`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-15`
- Updated: `2026-09-15`

## Supersession Boundary

The owner requested replacement of the manual Workstream/Thread experience,
with correction as an exception rather than promotion as the normal route.
This unexecuted proposal is superseded by
[PRD-0017 replanning](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md#reconciliation-and-approval-state).
The remaining sections are historical proposal content, not an active UI
contract. A later automatic overview/detail and transition boundary must own
the replacement; these forms must not be built as a prerequisite.

## Goal

Let the user correct and promote an inspected candidate with a small number of
explicit decisions, without manually recreating its evidence links.

## Acceptance Contract

- The passed FEAT-0092 review surface exposes only actions valid under the
  passed [FEAT-0093](feat-0093-workstream-candidate-review-and-promotion-contract.md)
  contract: rename, merge, split, ignore/restore, promote, and current-action
  undo. Selecting or previewing an action performs no write.
- A rename preserves evidence; merge names the candidate scopes being combined;
  split shows the two resulting evidence scopes. Preview preserves overlapping
  Session membership and makes clear which candidate boundary changes.
- Ignore removes the candidate from the default review list with a visible
  restore path. It never suggests completion or source deletion.
- Promotion asks for an existing destination or a new Workstream. New name and
  outcome are prefilled only from the reviewed candidate and remain editable;
  an unknown required value is explained beside the field. Existing destination
  selection shows its identity and current organization before submission.
- One preview shows the reviewed scope, exact new links, reused links,
  unresolved/non-linkable evidence, and where the result will appear. The user
  can adjust eligible selections before confirming; manual recreation of each
  valid link is not required.
- Submit maps exactly to FEAT-0093's current-revision transaction. Success shows
  the accepted snapshot and a destination link; cancel, failure, stale revision,
  and duplicate-name conflict retain inputs and recoverable candidate context.
  Retry cannot create a duplicate Workstream or promotion.
- The Workstream destination exposes a bounded read-only promotion summary and
  a return link to its reviewed evidence without rearranging existing Threads,
  checkpoints, resources, Suggestions, or Runs. This is a review receipt, not a
  Workstream Lens, branch hierarchy, or Atlas.
- Undo explains the exact owned effects it will reverse and that the Workstream
  container remains. Independent edits and pre-existing links remain protected;
  a conflict offers a review path instead of a partial optimistic result.
- Corrections preserve selected evidence, list position, disclosure, form
  values on failure, and meaningful keyboard focus. When a merge/split/ignore
  changes the selected candidate, the result has one explicit destination and
  the return path stays clear through browser history.
- All forms have executable narrow/no-script paths and fit the existing
  [Design Constitution](../../policies/design/design-constitution.md). Actions
  use normal contextual forms and readable consequences, with no canvas gesture
  requirement, model setup, or remote operation.

## Scope Boundary

- In: contextual candidate forms, exact previews, validation/submission,
  result/undo/restore feedback, and a minimal Workstream promotion summary.
- Out: new persistence semantics, automatic membership updates, existing
  Workstream merge/split/delete, Thread migration, Lens, Atlas, graph changes,
  semantic extraction, models, and external operations.

## Surface Lanes

- Mutation integration: candidate action routes/controllers under
  `src/localbrain/`; Builder consumes passed FEAT-0093 first. Contract and
  Functional own payload, transaction mapping, stale/repeat/error evidence.
- Candidate interaction: review templates, route-scoped assets, and semantic
  styles; Builder depends on the action contract. Design, Functional, and
  UX Heuristic own previews, selection, focus, responsive, and no-script checks.
- Destination/return: Workstream detail's bounded promotion summary and return
  navigation; Builder consumes the promotion receipt. Design and Functional
  own hierarchy preservation and round-trip evidence; Contract checks ownership.

## Contract Surfaces

- Action availability and exact preview/submit mapping to FEAT-0093.
- Candidate/target revision, form recovery, undo, and promotion result.
- Workstream summary and evidence-review return behavior.

## Required Evaluators

- `contract`: mutation ownership, exact reviewed scope, stale/repeat behavior,
  source safety, and Workstream compatibility.
- `design`: hierarchy, consequence visibility, authority cues, and containment
  through [Design Evaluation](../../policies/design/design-evaluation.md).
- `functional`: every action, failure/cancel/retry, source/destination round
  trips, no-script, and focus/history continuity through
  [Interaction Evaluation](../../policies/experience/interaction-evaluation.md).
- `ux-heuristic`: review effort, scope comprehension, name/outcome confirmation,
  destination clarity, and confidence in undo/recovery.

## User-Visible Outcome

The user can turn a useful proposal into a named Workstream, or correct its
boundary first, while retaining the evidence that justified the decision.

## Entry And Exit

- Entry: an inspected candidate or its retained review/promotion record.
- Exit: the corrected candidate, restored review list, or explicitly opened
  Workstream destination with a return path to the accepted evidence.

## State Expectations

- Preview: scope, destination, and exact consequences before any write.
- Working: only the owning action becomes busy.
- Success: confirmed effect and next destination are visible.
- Conflict/error: prior durable state and user inputs remain recoverable.
- Ignored/undone: the result and permitted restoration are understandable.
- Narrow/no-script: same action authority and recovery semantics.

## Dependencies

- FEAT-0092 and its human usefulness review must pass.
- FEAT-0093 must be approved before Spec and passed before build.
- Human approval of this product boundary remains required after those gates.

## Likely Affected Surfaces

- Candidate review routes, templates, form/controller, and scoped styles.
- Workstream detail promotion summary and review return link.
- Synthetic route/browser tests and product/architecture/design owner docs.

## Pass Or Fail Checks

- Preview and submit every permitted action, including overlapping Sessions,
  new/existing destinations, reused links, and unresolved evidence.
- Verify cancel, stale candidate, changed target, duplicate name, repeat submit,
  rollback, restore, and undo match the passed contract exactly.
- Verify long mixed-language content, keyboard, reduced motion, no-script, and
  `1440`/`920`/`700`/`320` widths with actual rendered interactions.
- Confirm selection, focus, page/list position, and history after every result
  and candidate-to-Workstream-to-review round trip.
- Fail if promotion requires manual linking of every already supported member,
  silently accepts later members, changes Threads, or starts excluded I/O.

## Regression Surfaces

- FEAT-0092 read-only review and FEAT-0093 durable history.
- Existing Workstream/Thread/checkpoint/resource/Suggestion/Run behavior.
- Sessions, Focus corrections, Local Contexts, Atlassian, shell, and privacy.

## Harness Trace

- Spec doc: not created; prerequisite and Feature approval pending.
- Run: not started.
- Execution profile: `fullstack-product`.
- Latest evaluator reports: none.
- Latest fix note: none.

## Open Review Decisions

- Confirm the contextual action set and Workstream summary placement after
  the discovery usefulness review and promotion contract are accepted.
- Lens and Atlas remain later product choices even after this Feature passes.

## Continuity Notes

- `2026-09-15`: proposed as the product consumer of a separately approved
  review/promotion contract, with existing Workstream hierarchy retained.
- `2026-09-15`: superseded by the automatic overview/detail and controlled
  transition direction. No Spec, Run, UI, or evaluation was started.
