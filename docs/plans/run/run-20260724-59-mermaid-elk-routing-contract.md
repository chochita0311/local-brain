# RUN-20260724-59: Mermaid ELK Routing Contract

## Metadata

- ID: `run-20260724-59`
- Status: `passed`
- Feature: [feat-0055-mermaid-elk-routing-contract](../feature/feat-0055-mermaid-elk-routing-contract.md)
- Parent PRD: [prd-0008-connected-atlassian-validation-and-schema-erd-routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Active Spec: [spec-0055-mermaid-elk-routing-contract](../spec/spec-0055-mermaid-elk-routing-contract.md)
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `design`, `functional`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal And Selected Loop

- Compare the official ELK candidate without changing product runtime assets, then publish one executable adoption contract.
- Route: `Orchestrator → Spec Agent → comparison Builder → Contract Evaluator → Design Evaluator → Functional Evaluator`.

## Decision

- `ACCEPT`: use `@mermaid-js/layout-elk@0.2.2` as the single default for every Schema ERD.
- Scope: Schema global and all subject diagrams only.
- Shape: rounded orthogonal routing is accepted; no sharp-corner promise.
- Interaction: no layout selector; existing zoom and scroll remain.
- Failure: one Dagre retry, then the existing textual fallback.

## Comparison Summary

| Diagram | Dagre viewBox | ELK viewBox | Dagre → ELK render at 1440 |
| --- | --- | --- | --- |
| global | `7884 × 1321` | `4987 × 2018` | `147.6 ms → 189.3 ms` |
| sparse subject | `1174 × 751` | `912 × 771` | `19.5 ms → 22.1 ms` |
| dense subject | `3483 × 1314` | `2857 × 1394` | `34.9 ms → 52.6 ms` |

- Global width decreased about `36.8%`; dense-subject width decreased about `18.0%`.
- ELK trades additional vertical depth for clearer layer grouping and right-angle-based traceability.
- Relationship viewBox, paths, line positions, and text were repeat-stable for both engines. Mermaid's randomized decorative entity-border paths were not treated as relationship-layout nondeterminism.
- Global source contains 63 relations and ELK emitted 63 relationship paths; sparse and dense counts also matched their sources.
- `1440`, `920`, `700`, and `320` comparison pages had no page-level overflow. At narrow widths each diagram retained local horizontal scroll.
- Labels, entity rows, physical/application line styles, and cardinality markers remained legible in reviewed temporary captures.

## Package Evidence

- Minimal product-form bundle:
  - Mermaid baseline: `3,444,998` bytes
  - Mermaid plus registered ELK: `4,961,977` bytes
  - delta: `1,516,979` bytes, `44.03%`
- The delta passes the accepted `<2 MiB` and `<50%` budget.
- All observed ELK render durations pass the global `<250 ms` and subject `<100 ms` budgets.
- Direct package, ELK engine, and license inputs are locally bundleable and require no runtime network request.

## Current Artifacts

- Spec: [spec-0055-mermaid-elk-routing-contract](../spec/spec-0055-mermaid-elk-routing-contract.md)
- Contract evaluation: [eval-0055-contract-mermaid-elk-routing-contract](../evaluation/eval-0055-contract-mermaid-elk-routing-contract.md) — `PASS`
- Design evaluation: [eval-0055-design-mermaid-elk-routing-contract](../evaluation/eval-0055-design-mermaid-elk-routing-contract.md) — `PASS`
- Functional evaluation: [eval-0055-functional-mermaid-elk-routing-contract](../evaluation/eval-0055-functional-mermaid-elk-routing-contract.md) — `PASS`
- Fix log: not created

## Evaluation Coverage

- Contract: complete; version, loader API, license, offline, bundle, manifest, freshness, and fallback ownership fixed.
- Design: complete for the synthetic comparison; all required density and width samples were rendered and locally reviewed.
- Functional: complete for the candidate contract; parse/render, relation counts, repeat geometry, duration, containment, current asset checks, and textual fallback ownership passed.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: ELK accepted with a Schema-only single default and bounded fallback.
  - notes: no package, lockfile, adapter, runtime asset, database, or generated Schema source changed in this decision Run.

## Post-Contract Regression Check

- Needed: yes.
- Result: passed.
- Notes: current Mermaid asset freshness, asset contract tests, and all nine data-model Mermaid parses passed while the product remained on Dagre.

## Human Review Outcome

- Decision: automatic sequential approval authorized on `2026-07-24`; rendered comparison supports acceptance.
- Returned layer if any: none.
- Follow-up run: FEAT-0056.

## Continuity Notes

- `2026-07-24`: temporary screenshots and metrics remained outside the repository; tracked evidence contains only aggregate synthetic measurements.
