# FEAT-0092: Workstream Candidate Evidence Review

## Metadata

- ID: `feat-0092`
- Status: `superseded`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-15`
- Updated: `2026-09-15`

## Supersession Boundary

The owner requires automatically usable work flows rather than a candidate
inbox requiring review before value. Extraction quality must be validated
before new UI work. This unexecuted proposal is superseded by
[PRD-0017 replanning](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md#reconciliation-and-approval-state).
The remaining sections are historical proposal content, not an active design
or execution contract. Evidence inspection remains a useful requirement but
must serve the replacement's automatic primary experience.

## Goal

Let the user inspect proposed higher-level work themes, their extent, and the
evidence for including each Session before deciding whether discovery is useful.

## Acceptance Contract

- An additive `작업 후보` entry from the Workstreams inventory opens a local
  candidate list and evidence review surface. Existing Workstreams remain
  directly accessible, and no new global Atlas destination is introduced.
- Initial inspection needs no selected Session, manually created Workstream,
  Thread assignment, model, or remote connection. It consumes only the passed
  [FEAT-0091](feat-0091-deterministic-workstream-candidate-projection.md) result.
- A candidate first shows its provisional name, supporting source families,
  supported observation span, latest supporting observations, and an explicit
  inferred boundary. It does not claim a known outcome, next action, single
  causal tip, or completion when those facts are unavailable.
- Selecting it reveals exact membership reasons and evidence, overlap with
  other candidates, and source availability/freshness. A mixed Session can be
  shown in two candidates without importing all its content into either one.
- Scope and processing coverage remain visible. Empty complete results,
  unexamined/limited scope, missing evidence, and a local read error have
  different explanations; a partial result cannot say there are no other work
  themes. Pagination follows the producer's revision and coverage contract.
- Existing safe Session, Local Context, and Atlassian destinations remain
  available. A supporting Session can open its existing Focus/Trace view and
  return to the candidate selection and prior list position.
- Selection, URL/history state, filters, evidence disclosure, and focus agree
  through list selection, direct entry, back/forward, reload, and source change.
  Unsupported old selection produces a clear local return path.
- This stage is read-only. It offers evidence inspection and existing source
  navigation; consequential candidate actions arrive through FEAT-0094 after
  their separate persistence contract passes.
- The surface extends the current Browse/Explorer families under the
  [Design Constitution](../../policies/design/design-constitution.md).
  It retains shell navigation, semantic tokens, non-color-only authority cues,
  normal reading order, and sequential narrow/no-script access. It introduces
  no graph renderer or page-specific design system.

## Scope Boundary

- In: candidate entry/list/detail, reasons, overlap, coverage, source links,
  stable navigation, empty/error states, and usefulness review evidence.
- Out: candidate mutation, promotion, Workstream/Thread changes, model setup,
  new source operations, graph extension, Lens, Atlas, or topic terrain.

## Surface Lanes

- Read integration: candidate routes/presentation adapters under
  `src/localbrain/`; Builder consumes passed FEAT-0091 first. Contract and
  Functional own payload, coverage, error, and no-write evidence.
- Review interaction: templates, route-scoped assets, and shared semantic styles;
  Builder depends on the read adapter. Design, Functional, and UX Heuristic own
  rendered list/detail, source navigation, focus, and responsive evidence.
- Regression/owners: tests and product/architecture/design owner sections;
  Builder integrates both lanes. Contract and Functional own source-safety and
  existing Workstream/Session compatibility checks.

## Contract Surfaces

- Local read route, candidate identity/revision, selection, and coverage.
- Browse/detail/source return behavior and unknown/partial state semantics.

## Required Evaluators

- `contract`: read-only route, producer parity, scope, authority, and privacy.
- `design`: hierarchy, long labels, containment, and existing screen-family fit
  using [Design Evaluation](../../policies/design/design-evaluation.md).
- `functional`: supported/empty/partial/error cases, paging, direct entry,
  history, keyboard/no-script, and source-return continuity using
  [Interaction Evaluation](../../policies/experience/interaction-evaluation.md).
- `ux-heuristic`: whether users can explain why a candidate exists, distinguish
  unknown facts, and identify an incorrect or fragmented boundary.

## User-Visible Outcome

The user can assess a proposed work theme without reading every Session or
first organizing its resources by hand.

## Entry And Exit

- Entry: Workstreams inventory or direct candidate review URL.
- Exit: another candidate, an existing source/Focus detail, or Workstreams;
  selection and the return path retain meaningful context.

## State Expectations

- Ready/selected: candidate identity and its source-backed reasons agree.
- Empty/partial/unavailable: distinct explanations preserve local navigation.
- Changed revision/error: stale controls cannot imply a current result; offer
  a bounded explicit retry while preserving recoverable inspection state.
- Narrow/no-script: the same evidence and source destinations remain usable.

## Dependencies

- FEAT-0090 and FEAT-0091 must be approved before Spec and passed before build.
- Passed Focus/Trace is a source-navigation dependency, not a discovery owner.
- Human approval of this Feature and its usefulness review protocol is needed
  before execution. Passing UI evaluation alone does not approve FEAT-0093.

## Likely Affected Surfaces

- Workstreams inventory entry, candidate route and presentation adapter.
- Candidate list/detail templates and bounded route-scoped interaction assets.
- Synthetic route/browser checks and applicable product/design owner docs.

## Pass Or Fail Checks

- Exercise every PRD candidate case through the actual review surface.
- Verify long mixed-language labels and positive, overlapping, empty, partial,
  stale, error, and no-script states at `1440`, `920`, `700`, and `320` widths.
- Verify source/Focus round trips, keyboard focus, reduced motion, paging,
  direct entry, and browser history; no inaccessible desktop-only controls.
- Fail if opening or inspecting a candidate mutates state, reads a source body,
  starts hidden source/model work, or presents inferred membership as confirmed.

### Separate Product Usefulness Review

- Before execution, freeze an owner-selected sample of known larger efforts
  and difficult mixed/parallel cases, expected membership, and an agreed
  acceptable correction burden. Use synthetic fixtures for tracked evidence;
  any approved private review stays local and outside Git.
- Compare expected efforts found/missed, unrelated memberships, duplicate or
  fragmented proposals, label edits, and required merge/split decisions.
- A sample composed only of repeated pairs already chosen by the algorithm is
  insufficient. Include genuine effort-level expectations and negative cases.
- Record implementation pass separately from the human usefulness decision.
  Unsatisfactory discovery returns PRD planning before FEAT-0093 execution or
  Lens/Atlas approval. Missing semantic evidence does not admit Qwen by default.

## Regression Surfaces

- Workstreams inventory/detail and existing Thread organization.
- Sessions, Focus/Trace, Related Materials, Local Contexts, and Atlassian.
- Shared shell, forms, reading/navigation behavior, and privacy.

## Harness Trace

- Spec doc: not created; prerequisite and Feature approval pending.
- Run: not started.
- Execution profile: `fullstack-product`.
- Latest evaluator reports: none; product usefulness is unassessed.
- Latest fix note: none.

## Open Review Decisions

- Confirm the additive Workstreams entry and list/detail review boundary.
- Freeze representative efforts and usefulness thresholds before approving
  this Feature. That review setup is not required to start FEAT-0090 planning.

## Continuity Notes

- `2026-09-15`: proposed as the first visible candidate increment, with a
  distinct human usefulness review before durable promotion work.
- `2026-09-15`: superseded by the owner-requested automatic-reconstruction
  replan. No Spec, Run, UI, or product evaluation was started.
