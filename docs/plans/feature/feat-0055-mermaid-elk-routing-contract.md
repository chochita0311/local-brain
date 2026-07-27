# FEAT-0055: Mermaid ELK Routing Contract

## Metadata

- ID: `feat-0055`
- Status: `passed`
- Type: `foundation`
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `design`, `functional`
- Parent PRD: [prd-0008-connected-atlassian-validation-and-schema-erd-routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal

- Resolve whether Mermaid's official ELK layout path is an acceptable, locally packageable routing contract for LocalBrain Schema ERDs and fix the exact default, coverage, fallback, and asset consequences before product adoption.

## Acceptance Contract

- Current Mermaid 11.16 Dagre output and one compatible pinned `@mermaid-js/layout-elk` candidate are compared from the same generated Schema sources.
- The comparison covers the global ERD and representative sparse and dense subject ERDs at `1440`, `920`, `700`, and `320`.
- Evidence evaluates relationship traceability, orthogonal shape, corner treatment, crossings, node placement, labels, cardinality markers, determinism, render time, bundle size, zoom behavior, and textual fallback.
- The candidate uses Mermaid's official external-layout loader contract and does not patch Mermaid, rewrite SVG paths, or introduce a runtime network dependency.
- The Feature closes with one explicit decision:
  - accept ELK with an exact default or bounded selector policy and diagram coverage;
  - or reject ELK and retain Dagre with recorded evidence.
- If accepted, the contract fixes compatible versions, local build inputs, manifest and license ownership, freshness checks, loader failure behavior, and the adoption requirements for FEAT-0056.
- If rejected, no ELK runtime asset, dependency, control, or partial adapter path remains in the product.
- No database, generated ER source, relation ownership, Schema navigation, or user data changes occur.

## Scope Boundary

- In:
  - official Mermaid ELK compatibility and loader contract
  - deterministic visual comparison matrix
  - sharp versus rounded orthogonal evidence
  - default, selector, or rejection decision
  - global versus subject diagram coverage decision
  - package size, render performance, license, offline, and freshness evidence
  - failure and Dagre or textual fallback policy
- Out:
  - product rollout of an accepted policy
  - replacing Mermaid
  - manual node placement, drag editing, waypoints, export, or full authoring
  - Mermaid bundle patching or post-render SVG path rewriting
  - changing generated ERD content or database relations

## Surface Lanes

- Layout comparison lane:
  - path roots: current generated Schema sources, temporary isolated comparison harness, and synthetic rendered evidence
  - dependencies: pinned Mermaid 11.16 and passed FEAT-0052
  - expected evidence: like-for-like Dagre/ELK diagrams across approved density and viewport samples
  - evaluator ownership: `design`, `functional`
- Package contract lane:
  - path roots: `package.json`, lockfile, Mermaid build scripts, local asset manifest, licenses, and asset tests
  - dependencies: an ELK candidate that passes compatibility comparison
  - expected evidence: exact version, bundle delta, license, offline loader, deterministic build, and stale-asset behavior
  - evaluator ownership: `contract`, `functional`
- Decision lane:
  - path roots: Spec, Run, and evaluation artifacts plus affected durable Schema presentation policy
  - dependencies: both evidence lanes
  - expected evidence: one accepted or rejected policy with no unresolved downstream routing choice
  - evaluator ownership: `contract`, `design`

## Contract Surfaces

- `package.json` and the package lock.
- `scripts/build-mermaid-assets.mjs` and Mermaid asset checks.
- Local Mermaid asset manifest, licenses, and freshness contract.
- `src/localbrain/static/mermaid-adapter.js`.
- Generated Schema Mermaid source and textual fallback ownership.
- FEAT-0052 zoom and rerender integration.

## Entry And Exit

- Entry point: run the approved isolated Dagre/ELK comparison against current generated Schema sources.
- Exit or transition behavior: publish one accepted or rejected routing contract. Only an accepted contract unblocks FEAT-0056.

## State Expectations

- Default: the product remains on current Dagre assets while evaluation is incomplete.
- Candidate unavailable: retain Dagre and record the package or compatibility limitation.
- Render failure: retain source and textual fallback; do not classify an incomplete render as accepted.
- Accepted: exact policy and package contract are fixed for downstream Spec work.
- Rejected: current runtime remains unchanged and the reason is durable.

## Dependencies

- PRD-0008 is `approved`.
- PRD-0003 and FEAT-0052 remain `passed`.
- The human owner must review the rendered comparison before an acceptance decision becomes executable.

## Likely Affected Surfaces

- `package.json`
- package lock
- `scripts/build-mermaid-assets.mjs`
- `scripts/test-mermaid-assets.mjs`
- `src/localbrain/static/mermaid-adapter.js`
- `src/localbrain/static/schema-explorer.js`
- Schema presentation policy and focused asset/UI tests
- synthetic rendered comparison evidence

## Pass Or Fail Checks

- Pass if Dagre and ELK are compared from identical Schema source at all required density and viewport samples.
- Pass if labels, markers, node containment, determinism, zoom, navigation, failure fallback, bundle, license, and performance are evaluated.
- Pass if one exact accepted or rejected contract is recorded and downstream FEAT-0056 requires no routing-policy guess.
- Pass if accepted assets can be pinned, built, checked, licensed, and served entirely offline.
- Fail if the decision relies on a Flowchart-only curve setting, patched Mermaid, SVG rewriting, CDN use, private data, or incomplete visual evidence.

## Regression Surfaces

- PRD-0003 Schema ownership and generated presentation.
- FEAT-0052 zoom, fit, wheel, partial navigation, and fallback behavior.
- Local asset packaging, license accounting, and privacy checks.
- No-script textual Schema catalog.

## Harness Trace

- Active spec: [spec-0055-mermaid-elk-routing-contract](../spec/spec-0055-mermaid-elk-routing-contract.md)
- Active run: [run-20260724-59-mermaid-elk-routing-contract](../run/run-20260724-59-mermaid-elk-routing-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluations:
  - [contract](../evaluation/eval-0055-contract-mermaid-elk-routing-contract.md) — `PASS`
  - [design](../evaluation/eval-0055-design-mermaid-elk-routing-contract.md) — `PASS`
  - [functional](../evaluation/eval-0055-functional-mermaid-elk-routing-contract.md) — `PASS`
- Latest fix note: not created

## Open Review Decisions

- None. ELK `0.2.2` is accepted for every Schema ERD as one default; rounded right-angle routes are accepted; FEAT-0056 must provide one Dagre retry and then textual fallback.

## Continuity Notes

- `2026-07-24`: initial draft made the visual and packaging decision a prerequisite contract so product adoption cannot guess whether ELK is a default, option, or rejected candidate.
- `2026-07-24`: Attempt 1 accepted the official ELK path after global, sparse, and dense comparisons at `1440`, `920`, `700`, and `320`. The minimum product bundle delta was `1,516,979` bytes (`44.03%`), measured durations passed the fixed budgets, and FEAT-0056 was unblocked.
