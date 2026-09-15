# RUN-20260914-99: Workflow Boundary Corrections

## Metadata

- ID: `run-20260914-99`
- Status: `passed`
- Feature: [FEAT-0089](../feature/feat-0089-workflow-boundary-corrections.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Active Spec: [SPEC-0089](../spec/spec-0089-workflow-boundary-corrections.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-09-14`
- Updated: `2026-09-15`

## Goal

- Deliver contextual preview, commit, recovery, and undo controls on the passed
  Session Workflow Focus surface while preserving orientation and every source
  boundary.

## Selected Loop

- Feature type: `product`
- Surface: local assertion POST, Focus Trace forms, route-scoped controller,
  semantic styles, and synthetic rendered evidence
- Surface lanes: Assertion API; Focus interaction; regression/owner
- Required evaluators: Contract, Design, Functional, UX Heuristic
- Current phase: Complete
- Screen alignment mode: `extend`

## Contract Surfaces

- Exact contextual action previews; strict request/response; atomic FEAT-0088
  mapping; fixed success/conflict/error feedback; one-shot orientation restore;
  no-script/narrow accessibility; retained candidate reasons; no external/model
  operation.

## Invocation Context

- Golden sources: approved PRD-0017, passed FEAT-0087 and FEAT-0088, approved
  FEAT-0089 and SPEC-0089.
- Relevant policies: Design Constitution, Design Evaluation, Interaction
  Evaluation, Product, Architecture, Privacy, Data Model, and value registry.
- Applied skill: `screen-alignment`, `extend` mode, current Workflow Focus and
  Trace as primary visual sources.

## Current Artifacts

- Spec: [SPEC-0089](../spec/spec-0089-workflow-boundary-corrections.md)
- Contract evaluation:
  [EVAL-0089 Contract](../evaluation/eval-0089-contract-workflow-boundary-corrections.md).
- Design evaluation:
  [EVAL-0089 Design](../evaluation/eval-0089-design-workflow-boundary-corrections.md).
- Functional evaluation:
  [EVAL-0089 Functional](../evaluation/eval-0089-functional-workflow-boundary-corrections.md).
- UX heuristic evaluation:
  [EVAL-0089 UX](../evaluation/eval-0089-ux-workflow-boundary-corrections.md).
- Fix log:
  [FIX-0089](../fix/fix-0089-workflow-correction-restoration-snapshot.md).
- Heuristic backlog: create only for non-blocking findings.

## Evaluation Coverage

- Contract: `PASS`; strict request shape, transaction ownership, exact action
  mapping, stale conflict, rollback, no-external-I/O, and owner parity passed.
- Design: `PASS`; Trace-local action hierarchy, structural authority cues, and
  `1440`/`920`/`700`/`320` rendered containment passed.
- Functional: `PASS`; all actions, undo/reopen, cancel, failure, no-script,
  history, focus, disclosure, viewport, and regression behavior passed.
- UX heuristic: `PASS`; consequence comprehension, provenance trust, stable
  orientation, keyboard flow, and local recovery passed.

## Current Route

- Next role: Product/Orchestrator for a bounded Workstream Candidate Discovery
  planning decision under PRD-0017
- Current blocker classification: none
- In-run route: complete
- Post-run product review: retain the delivered deterministic Focus and
  correction path as a useful Session Lineage layer; do not treat it as the
  Workstream replacement. Define candidate discovery and review before deciding
  any later Workstream Lens, Atlas, topic-terrain, or optional-model boundary.

## Attempts

- Attempt 1:
  - status: returned to fix
  - outcome: repeated Chrome evaluation exposed intermittent map-pan drift on
    correction success because the restoration snapshot was captured after the
    asynchronous request.
  - notes: assertion, API, responsive, no-script, and regression contracts
    passed; only enhanced orientation restoration returned to the frontend lane.
- Attempt 2:
  - status: passed
  - outcome: snapshot ownership moved to submit start, focus precedes
    next-frame coordinates, and all four evaluators passed.
  - notes: the full browser scenario passed twice consecutively after the
    focused fix; no product or persistence boundary changed.

## Post-Contract Regression Check

- Needed: yes
- Result: passed
- Notes: complete `551/551` Python suite, `7/7` controller tests, `39/39`
  focused Python checks, four-width Chrome QA, schema/value/audit parity, and
  existing Session, Focus fallback, Workstream, Atlassian, Local Context,
  Search, Schema, and Runner coverage passed.

## Human Review Outcome

- Decision: on `2026-09-15`, the owner accepted the delivered Focus and
  correction chain as a useful Session-level lineage surface while clarifying
  that the intended Workstream value is discovery of larger work directions
  from all available evidence.
- Returned layer if any: PRD-0017 product planning, for a bounded Workstream
  Candidate Discovery and Review definition. The passed Run itself remains
  closed and no implementation Feature was reopened.
- Follow-up run: none.

## Continuity Notes

- `2026-09-14`: RUN-99 initialized with FEAT-0089 as the only in-loop Feature.
- `2026-09-14`: all four evaluators passed. The Run delivered contextual local
  corrections with stable orientation and no Qwen, source, external, or
  Workstream mutation.
- `2026-09-14`: repeated QA returned map-pan restoration to one focused fix;
  Attempt 2 froze state at submit start and passed repeated rendered checks.
- `2026-09-15`: post-run product review retained Session Workflow Focus as a
  subordinate evidence-navigation layer and returned the larger Workstream
  Candidate Discovery boundary to planning. Lens, Atlas, topic terrain, and
  Qwen remain unapproved later options.
