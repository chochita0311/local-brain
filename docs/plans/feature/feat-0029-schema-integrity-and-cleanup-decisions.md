# FEAT-0029: Schema Integrity And Cleanup Decisions

## Metadata

- ID: `feat-0029`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Produce one evidence-backed cleanup decision set for every current table, column, index, and relation so the owner can approve bounded migration Features without guessing about usage, ownership, data loss, or recovery risk.

## Acceptance Contract

- Every effective table, virtual table, column, declared or runtime index, physical relation, and application-enforced polymorphic relation receives exactly one `keep`, `change`, `remove`, or `defer` decision.
- Every decision traces to the owning subject, fresh-schema or migration source, producers, consumers, tests, lifecycle class, authority, rebuildability, deletion effect, and recovery path.
- `change` and `remove` candidates identify the defect, desired contract, affected objects and consumers, migration dependency, preservation requirement, rollback or recovery approach, verification evidence, and risk level.
- `keep` decisions state the evidence that justifies retaining the object rather than relying only on current existence.
- `defer` decisions identify the unresolved dependency or missing evidence and create one canonical Project Backlog item when follow-up remains necessary.
- The audit checks unused fields, duplicated facts, wrong ownership, polymorphic referential gaps, identifier inconsistencies, missing or redundant indexes, timestamp inconsistency, status and type constraints, stable data hidden in JSON, deletion behavior, and fresh-schema versus compatible-migration drift.
- Current code use is treated as evidence, not automatic proof that the current design is correct.
- Source-derived rebuildable data and non-rebuildable user organization or review state are never placed in the same destructive migration boundary without explicit preservation rules.
- Findings remain planning and evaluation artifacts. The durable data-model documents continue to describe current implementation truth and are corrected only when the audit finds a documentation inaccuracy.
- The audit proposes dependency-ordered migration Feature boundaries, but no schema, migration, producer, consumer, query, or UI behavior changes occur in this Feature.
- The human owner reviews the decision set before any migration Feature is created or approved.

## Scope Boundary

- In:
  - effective schema object inventory from FEAT-0027
  - producer, consumer, test, and deletion-path tracing
  - keep, change, remove, or defer classification
  - data authority, lifecycle, rebuildability, and recovery evidence
  - fresh and compatible schema drift analysis
  - migration dependency, preservation, rollback, risk, and verification proposals
  - residual backlog routing
  - proposed domain-sized or dependency-sized migration Feature boundaries
- Out:
  - executing DDL or data migrations
  - changing schemas, indexes, constraints, producers, consumers, queries, or UI
  - deleting runtime data or source files
  - treating current code use as automatic approval
  - implementing deferred ideas
  - presenting cleanup decisions as current schema truth in the Schema Explorer

## Surface Lanes

- Object and consumer evidence lane:
  - path roots: `src/localbrain/schema.sql`, `src/localbrain/db.py`, `src/localbrain/`, tests, FEAT-0026 docs, FEAT-0027 manifest
  - dependencies: passed FEAT-0026 and FEAT-0027
  - expected evidence: exhaustive object, producer, consumer, test, lifecycle, deletion, and recovery map
  - evaluator ownership: `contract`
- Decision classification lane:
  - path roots: active Spec, Run evidence, cleanup decision artifact
  - dependencies: object and consumer evidence lane
  - expected evidence: exactly one supported decision and risk record per audited object
  - evaluator ownership: `contract`
- Migration proposal lane:
  - path roots: cleanup decision artifact, Project Backlog, proposed follow-up boundaries
  - dependencies: decision classification lane
  - expected evidence: dependency-ordered, preservation-safe Feature candidates and explicit deferrals
  - evaluator ownership: `contract`

## Contract Surfaces

- effective schema and presentation manifest parity
- producer and consumer evidence ownership
- keep, change, remove, and defer decision vocabulary
- lifecycle, authority, rebuildability, deletion, and recovery classification
- migration risk, dependency, rollback, and verification proposal shape
- current-truth documentation versus planning-decision ownership
- residual backlog and post-audit Feature creation gate

## Required Evaluators

- `contract`: exhaustive coverage, evidence quality, one-decision invariant, source-of-truth ownership, lifecycle and recovery safety, migration dependency proposals, and absence of runtime change.

## User-Visible Outcome

- This foundation Feature changes no screen. It gives the owner a reviewable basis for deciding which cleanup migrations, if any, should be planned next.

## Entry And Exit

- Entry point: the approved baseline, schema presentation manifest, and implementation consumer inventory.
- Exit or transition behavior: the human owner approves, rejects, defers, or regroups migration candidates; only approved groups may become FEAT-0030 or later migration Features.

## State Expectations

- Keep: object remains current with supported ownership and consumer evidence.
- Change: desired replacement contract, migration path, and preservation risk are explicit.
- Remove: absence of required ownership is proven and deletion or recovery safety is explicit.
- Defer: missing evidence or dependency is named and routed to one canonical backlog item.
- Conflicting evidence: decision remains `defer`; the audit does not guess.
- Documentation error: current-truth docs are corrected without silently changing runtime behavior.
- Success: every audited object has exactly one supported disposition and every migration candidate is bounded enough for human review.

## Dependencies

- FEAT-0026 is `passed`.
- FEAT-0027 is `passed`.
- FEAT-0028 is not a data-contract dependency; it may be completed first for the approved user workflow sequence.

## Likely Affected Surfaces

- `src/localbrain/schema.sql` and `src/localbrain/db.py` as read-only evidence
- producers and consumers under `src/localbrain/` as read-only evidence
- synthetic tests as read-only or bounded evidence helpers
- `docs/policies/project/data-model.md` and subject docs for current-truth corrections only
- active Spec, Run, and evaluation artifacts
- `docs/plans/project/backlog.md` for explicit deferrals

## Pass Or Fail Checks

- Pass if every effective table, virtual table, column, index, physical relation, and polymorphic relation has exactly one keep, change, remove, or defer decision.
- Pass if every decision names its owner, evidence, producers, consumers, lifecycle, authority, rebuildability, deletion effect, and recovery path.
- Pass if every change or removal proposal defines desired contract, dependency, preservation, rollback or recovery, verification, and risk.
- Pass if non-rebuildable user state cannot be destroyed by an ungrouped or unsupported candidate.
- Pass if fresh-schema and compatible-migration drift is either resolved as documentation inaccuracy or classified for later work.
- Pass if each defer outcome has one named blocker and canonical backlog owner.
- Pass if proposed migration Features are dependency-ordered and small enough for separate approval and execution loops.
- Pass if repository diff proves no runtime schema, migration, producer, consumer, route, or UI change occurred.
- Fail if an object is marked removable only because its purpose is undocumented or a simple text search found no consumer.
- Fail if a migration Feature is created before the owner reviews the audit decision set.

## Regression Surfaces

- approved PRD-0002 Session and workspace ownership
- passed PRD-0004 usage, cost, and Project attribution contracts
- data-model current-truth documentation
- Schema Explorer current-state presentation
- user-curated Workstream, Thread, checkpoint, Resource, and Suggestion data
- repository privacy and no-runtime-data inspection boundary

## Harness Trace

- Active spec doc: [spec-0029-schema-integrity-and-cleanup-decisions](../spec/spec-0029-schema-integrity-and-cleanup-decisions.md)
- Active run: [run-20260718-34-schema-integrity-and-cleanup-decisions](../run/run-20260718-34-schema-integrity-and-cleanup-decisions.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [eval-0029-contract-schema-integrity-and-cleanup-decisions](../evaluation/eval-0029-contract-schema-integrity-and-cleanup-decisions.md) (`PASS`)
- Latest fix note: not created

## Continuity Notes

- `2026-07-18`: initial draft kept evidence-backed cleanup decisions separate from both baseline documentation and unknown future migration Features.
- `2026-07-18`: entered the approved execution loop as a planning-only audit; runtime schema and migration changes remain prohibited until the owner reviews the resulting decision groups.
- `2026-07-18`: passed with 329 resolved objects (`keep 259`, `change 9`, `remove 4`, `defer 57`), five bounded candidate groups, two canonical deferrals, corrected legacy-upgrade truth, complete Contract evidence, and no migration Feature creation. Candidate approval remains with the human owner.
