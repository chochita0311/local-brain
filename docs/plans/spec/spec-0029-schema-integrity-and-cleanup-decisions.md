# SPEC-0029: Schema Integrity And Cleanup Decisions

## Metadata

- ID: `spec-0029`
- Status: `approved`
- Run ID: `run-20260718-34`
- Attempt: `1`
- Parent Feature: [feat-0029-schema-integrity-and-cleanup-decisions](../feature/feat-0029-schema-integrity-and-cleanup-decisions.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: object and consumer evidence, decision classification, migration proposal
- Required Evaluators: `contract`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Source Set

- Human request: execute approved PRD-0003 Features step by step and stop cleanup implementation behind explicit owner review.
- Parent feature: FEAT-0029.
- Parent PRD: approved PRD-0003.
- Golden sources: the passed FEAT-0026 Data Model owners, FEAT-0027 presentation manifest, `schema.sql`, compatible structural and data migrations in `db.py`, all producers and consumers under `src/localbrain/`, and synthetic tests.
- Relevant policies or contracts: Data Model, Schema Presentation, Architecture, Privacy And Data Handling, PRD-0002 Session/workspace ownership, passed PRD-0004 usage attribution, and the foundation-contract profile.

## Implementation Goal

- Produce a human-reviewable, machine-checked audit that assigns exactly one supported `keep`, `change`, `remove`, or `defer` outcome to every effective table, virtual table, column, index, physical relation, and documented application relation without changing runtime behavior.

## In-Scope Behavior

- Record source, producer, consumer, test, lifecycle, authority, rebuildability, deletion, and recovery evidence at the owning table boundary and link every child object decision to that evidence.
- Record every effective object in a generated resolved ledger with one disposition, rationale, evidence reference, and risk.
- Check unused fields, duplicated facts, ownership, polymorphic integrity, identifiers, indexes, timestamps, value constraints, JSON structure, deletion behavior, and fresh-versus-compatible drift.
- Give every `change` or `remove` candidate a desired contract, affected consumers, dependency, preservation boundary, rollback/recovery, verification, and risk statement.
- Route unresolved work to one canonical Project Backlog item per defer group.
- Propose dependency-ordered migration boundaries for owner review, but do not create those Features.
- Add an audit checker that fails on object coverage drift, duplicate/missing decisions, unsupported disposition values, missing evidence links, or incomplete candidate safety fields.

## Out-Of-Scope Behavior

- No DDL, compatible migration, runtime schema, producer, consumer, query, route, template, or UI changes. A proven current-truth documentation inaccuracy may be corrected and its derived Schema presentation regenerated without presenting the cleanup disposition as current truth.
- No runtime database access or row inspection.
- No migration Feature creation or implicit owner approval.
- No removal conclusion based only on undocumented purpose or a simple text-search miss.

## Affected Surfaces

- FEAT-0029 Feature, Spec, Run, decision, resolved-ledger, contract-evaluation, and Project Backlog planning documents.
- A repository-only audit checker and its synthetic contract tests.
- Runtime sources and current-truth Data Model documents remain read-only evidence.

## Surface Lanes

- Object and consumer evidence:
  - path roots: schema, migrations, application modules, tests, Data Model docs, presentation manifest
  - dependency order: first
  - implementation responsibility: exhaustive evidence groups and explicit limitations without private-row inspection
  - validation evidence: source references, static consumer traces, test references, and manifest parity
- Decision classification:
  - path roots: audit decision source and resolved object ledger
  - dependency order: after evidence
  - implementation responsibility: one supported disposition per object plus complete safety fields for non-keep outcomes
  - validation evidence: checker coverage report and ledger regeneration parity
- Migration proposal:
  - path roots: audit review summary and Project Backlog
  - dependency order: after classification
  - implementation responsibility: bounded dependency order, preservation rules, explicit owner gate, canonical defer routing
  - validation evidence: contract evaluation and absence of migration/runtime diffs

## State And Interaction Contract

- Current manifest object: resolves to exactly one decision and one owning evidence group.
- Manifest object added, removed, or structurally renamed: audit check fails until the audit is deliberately refreshed.
- `keep`: rationale must establish ownership and required contract, not existence alone.
- `change` or `remove`: complete defect, target, dependency, preservation, recovery, verification, and risk fields are mandatory.
- `defer`: blocker and exactly one canonical backlog owner are mandatory.
- Conflicting or insufficient evidence: resolve to `defer`; never guess.
- Audit completion: produces review candidates only; owner approval is a separate transition.

## Data And Contract Assumptions

- FEAT-0027's validated manifest is the exhaustive object inventory; executable facts still belong to `schema.sql` and `db.py`.
- FEAT-0026 owner docs provide approved semantic and lifecycle evidence; code and tests provide implementation-use evidence.
- A table evidence group may be inherited by its columns, indexes, and relations only when the resolved ledger names that group and the object-specific rationale is retained.
- Static references establish known use, but an apparent absence is insufficient for removal without source authority, migration history, lifecycle, recovery, and regression evidence.
- The audit reads tracked synthetic or source material only and never opens a configured runtime database.

## Contract Surfaces

- Producer expectations: schema/migrations and owner docs expose the complete current inventory and semantics; application modules and tests expose known reads, writes, joins, and deletion paths.
- Consumer expectations: the owner can review decision groups without treating them as executable schema instructions; later planners may create only explicitly approved migration groups.
- Generated artifacts: resolved Markdown object ledger derived from the manifest and explicit audit decisions.
- Source-of-truth owner: audit source owns proposed dispositions; resolved ledger is derived review evidence; Data Model docs continue to own current truth.
- Stale-assumption check: manifest digest and exact set parity, evidence-link validation, source-reference checks, ledger byte parity, and no-runtime-surface diff review.

## Required Evaluators

- Contract: exhaustive object coverage, evidence quality, one-decision invariant, classification safety, current-truth ownership, proposed dependency order, backlog routing, privacy, and absence of runtime change.
- Design: not required; no visible surface changes.
- Functional: not required; no runtime behavior changes.
- UX heuristic: not required.

## Acceptance Mapping

- Exhaustive decision set: manifest-derived checker and resolved object ledger.
- Complete trace: table evidence register plus object-specific decision rows and source references.
- Candidate safety: required change/remove fields validated by the checker.
- Keep justification: object-specific rationale and inherited evidence reference.
- Deferrals: blocker plus canonical backlog item validated and linked.
- Smell coverage: explicit audit dimensions and findings in the decision document.
- Preservation: lifecycle/rebuildability-based boundaries and mandatory recovery fields.
- Current truth separation: audit and ledger stay under `docs/plans/`; policy docs change only for proven inaccuracies.
- Migration proposals: review groups only, no Feature or implementation creation.
- Human gate: Run exits to owner review even if contract evaluation passes.

## Evaluation Focus

- Verify virtual-table shadow objects and implicit SQLite autoindexes are treated according to the approved effective-object boundary, not accidentally confused with separately owned application objects.
- Verify every documented physical and polymorphic relation has one stable identity and disposition.
- Verify apparent unused, redundant, or inconsistent objects are not promoted to destructive work without preservation and recovery evidence.
- Verify PRD-0002 and PRD-0004 contracts and user-curated non-rebuildable state remain protected.

## Open Blockers

- None for the audit. Owner approval remains intentionally required after the contract evaluation passes and before any migration Feature exists.

## Continuity Notes

- `2026-07-18`: approved attempt 1 for an exhaustive, planning-only audit with a machine-resolved object ledger and explicit post-audit owner gate.
