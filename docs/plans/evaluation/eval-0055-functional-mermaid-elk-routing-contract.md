# EVAL-0055: Mermaid ELK Routing Contract — Functional

## Metadata

- ID: `eval-0055-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260724-59`
- Attempt: `1`
- Feature: [feat-0055-mermaid-elk-routing-contract](../feature/feat-0055-mermaid-elk-routing-contract.md)
- Spec: [spec-0055-mermaid-elk-routing-contract](../spec/spec-0055-mermaid-elk-routing-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: render success, geometry, performance, containment, and regression
- Evidence Coverage: `complete`
- Created: `2026-07-24`

## Checks And Evidence

- Dagre and ELK rendered the same current global, sparse, and dense definitions successfully.
- ELK relationship counts match source counts for all three examples; labels, markers, and solid/dashed relation roles remain present.
- Repeated viewBox, relationship paths, line positions, and texts are stable for both layouts.
- The measured bundle and render durations pass the fixed downstream budgets.
- All four widths remain page-contained; diagram-local overflow remains available at narrow widths.
- Current product assets remained byte-current, their contract tests passed, and all nine data-model Mermaid definitions parsed with the current bundle.
- The comparison did not alter package metadata, product assets, adapter behavior, generated Schema data, database state, or user data.

## Evidence Gaps

- The ELK-then-Dagre product retry is a downstream implementation requirement and is not claimed as already delivered.
- Acceptance impact: not applicable to this decision Feature; FEAT-0056 owns that behavior.

## Findings

- None.

## Regression Notes

- `npm run check:mermaid`, `npm run test:mermaid`, and `node scripts/check-data-model-mermaid.mjs` passed.

## Route

- Next action: `pass`.
