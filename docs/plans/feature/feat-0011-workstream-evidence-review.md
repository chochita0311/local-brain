# FEAT-0011: Workstream Evidence Review

## Metadata

- ID: `feat-0011`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Make confirmed Workstream and Thread evidence, Resource linking, and reviewable Suggestions one trustworthy organization surface without confusing inferred relationships with accepted structure.

## Acceptance Contract

- Workstream-level and Thread-level confirmed Resources retain clear ownership, type, relation, destination, and unlink consequence.
- Pending Suggestions remain structurally distinct from confirmed Resources and expose target, origin, rationale, confidence, and review actions.
- Accepted, rejected, restored, and superseded outcomes retain their current reversible behavior and semantic meaning.
- Existing Resource selection, local Resource creation, external reference creation, linking, unlinking, suggestion generation, review, and restore actions remain functional.
- Empty evidence and Suggestion states explain their own absence without appearing to change confirmed organization.

## Scope Boundary

- In:
  - Workstream and Thread linked-Resource regions
  - Resource picker and link form
  - local Resource and external reference creation forms
  - quick Suggestion generation, pending review, excluded history, accept, reject, and restore controls
  - evidence hierarchy, provenance, feedback, long content, and responsive presentation
- Out:
  - Workstream, Thread, and checkpoint core owned by `feat-0010`
  - maintenance Run controls owned by `feat-0013`
  - retrieval, matching, confidence calculation, or Resource data-contract changes
  - new batch review or organization actions

## Contract Surfaces

- current link, local Resource, external Resource, Suggestion generation, and Suggestion action endpoints
- Workstream-level versus Thread-level relationship ownership
- pending, accepted, rejected, restored, and superseded Suggestion semantics
- explicit user acceptance before inferred evidence changes confirmed organization

## Required Evaluators

- `design`: confirmed-versus-inferred separation, provenance, status, action hierarchy, long content, and responsive containment.
- `functional`: link and unlink, Resource creation, Suggestion generation, accept, reject, restore, feedback, reload, and regression.
- `ux-heuristic`: review confidence, consequence clarity, evidence ownership, reversible-action comprehension, and scan friction.

## User-Visible Outcome

- The user can inspect confirmed evidence, add or remove existing relationships deliberately, and review generated Suggestions without mistaking inference for user-confirmed organization.

## Entry And Exit

- Entry point: evidence and Suggestion regions within `/workstreams/{workstream_id}` after the core workspace loads.
- Exit or transition behavior: actions return to the same Workstream with the confirmed or review state visibly updated; Resource links open existing details.

## State Expectations

- Default: confirmed Resources and pending Suggestions occupy distinct labeled structures.
- Loading: Suggestion generation and form submission use bounded working feedback.
- Empty: no confirmed Resources, no pending Suggestions, and no excluded Suggestions are distinct.
- Error: action failures stay with their owning evidence or review region.
- Success: linked, unlinked, created, accepted, rejected, restored, and generated outcomes are visibly reflected.

## Dependencies

- `feat-0001`, `feat-0002`, `feat-0003`, and `feat-0010` must be `passed`.

## Likely Affected Surfaces

- Resource, link-tool, Suggestion, and quick-analysis regions in `src/localbrain/templates/workstream.html`
- linked-Resource, relation, suggestion, provenance, action, form, feedback, and responsive selectors in `src/localbrain/static/styles.css`
- link deletion, API form, Suggestion generation, and Suggestion action interactions in `src/localbrain/static/app.js`

## Pass Or Fail Checks

- Pass if confirmed Resources and inferred Suggestions cannot be mistaken for one another.
- Pass if Workstream and Thread relationship ownership remains visible.
- Pass if every existing add, link, unlink, accept, reject, restore, and generation action retains behavior and consequence.
- Pass if source, target, rationale, confidence, and status remain legible with long content and narrow widths.
- Fail if a Suggestion appears confirmed before explicit acceptance.
- Fail if visual cleanup hides provenance, excluded history, or unavailable evidence.

## Regression Surfaces

- Workstream and Thread Resource links
- local and external Resource creation
- link removal
- Suggestion generation, acceptance, rejection, restoration, refresh, and reversibility
- Resource detail destinations and confirmed organization

## Harness Trace

- Active spec doc: [spec-0011-workstream-evidence-review](../spec/spec-0011-workstream-evidence-review.md)
- Active run: [run-20260716-11-workstream-evidence-review](../run/run-20260716-11-workstream-evidence-review.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0011-ux-evidence-review](../evaluation/eval-0011-ux-evidence-review.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft isolated evidence and Suggestion review from core Workstream structure and maintenance execution.
- `2026-07-16`: executed and passed in `run-20260716-11`.
