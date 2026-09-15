# EVAL-0088 Contract: Workflow Assertion And Correction Contract

## Metadata

- ID: `eval-0088-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-20260914-98](../run/run-20260914-98-workflow-assertion-and-correction-contract.md)
- Attempt: `1`
- Feature: [FEAT-0088](../feature/feat-0088-workflow-assertion-and-correction-contract.md)
- Spec: [SPEC-0088](../spec/spec-0088-workflow-assertion-and-correction-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `stable Episode boundary → assertion ledger → Focus overlay`
- Evidence Coverage: `complete`
- Created: `2026-09-14`

## Checks And Evidence

- `workflow_assertions` is the sole new durable owner. It stores exact stable
  Episode-boundary identity, five assertion kinds, before/after meanings,
  close reasons, bounded notes, user authority, contract version, monotonic
  boundary versions, and append-only supersession without changing Sessions,
  source evidence, candidates, Workstreams, Threads, or Suggestions.
- Stable Episode keys remain authoritative when nullable Session lookup aids
  are deleted with `SET NULL`. The unique self-supersession relation prevents
  chain forks, and ordinary domain actions never update or delete history.
- The mutation boundary recomputes the current overlay immediately before a
  write, checks both projection revision and exact active assertion, validates
  endpoint/time/cycle/tip/action rules, and maps a unique chain race to a
  bounded conflict. Rejection and SQLite failure leave no partial row.
- The effective Focus projection retains complete base relations and reasons,
  base Episode lifecycle, applied or unresolved assertion summaries, and one
  deterministic revision. Missing source evidence does not erase an assertion;
  restoration of the same source-scoped Session identity re-resolves it.
- Product, Architecture, Privacy, Data Model, generated Schema Presentation,
  value registry, and value dictionaries agree on local-only ownership,
  recovery, deletion, exact vocabularies, and the no-model boundary.
- Generated parity reports 42 ordinary tables plus one FTS object, 477
  effective columns, 46 explicit indexes, 57 physical relations, 26
  application relations, and ten subject owners. The cleanup audit resolves
  all 649 objects as `keep=543`, `defer=106`.
- Assertion/Focus/map checks passed `40/40`; schema, value, Mermaid, generated-
  artifact, diff, and privacy checks passed. The complete repository suite
  passed `538/538`, and privacy passed over `880` candidate files.

## Findings

- None.

## Current Route

- Current route: `PASS`; FEAT-0089 may expose the exact assertion operations
  through contextual Focus controls without changing this foundation.
