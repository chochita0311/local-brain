# RUN-20260724-63: Schema ERD Orthogonal Routing

## Metadata

- ID: `run-20260724-63`
- Status: `passed`
- Feature: [feat-0056-schema-erd-orthogonal-routing](../feature/feat-0056-schema-erd-orthogonal-routing.md)
- Parent PRD: [prd-0008-connected-atlassian-validation-and-schema-erd-routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Active Spec: [spec-0056-schema-erd-orthogonal-routing](../spec/spec-0056-schema-erd-orthogonal-routing.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal And Selected Loop

- Apply the accepted ELK default without changing Schema content or existing exploration behavior.
- Route: `Orchestrator → Spec Agent → Frontend Builder → Contract Evaluator → Design Evaluator → Functional Evaluator → UX Heuristic Evaluator`.
- Screen Alignment mode: `extend`.

## Delivered Contract

- Pinned the official ELK loader and exact transitive engine in the public-registry lock graph.
- Bundled loader execution locally into the existing Mermaid output.
- Added loader and engine license files plus manifest ownership.
- Marked every global/subject Schema node for ELK while leaving other Mermaid consumers unchanged.
- Added exact ELK → Dagre → text attempt order and bounded visible layout state.
- Preserved the generated Mermaid source, all Schema data, zoom, navigation, focus, scroll, failure, and no-script paths.
- Corrected the prior FEAT-0055 license note: the loader is MIT and elkjs is EPL-2.0.

## Current Artifacts

- Spec: [spec-0056-schema-erd-orthogonal-routing](../spec/spec-0056-schema-erd-orthogonal-routing.md)
- Contract evaluation: [eval-0056-contract-schema-erd-orthogonal-routing](../evaluation/eval-0056-contract-schema-erd-orthogonal-routing.md) — `PASS`
- Design evaluation: [eval-0056-design-schema-erd-orthogonal-routing](../evaluation/eval-0056-design-schema-erd-orthogonal-routing.md) — `PASS`
- Functional evaluation: [eval-0056-functional-schema-erd-orthogonal-routing](../evaluation/eval-0056-functional-schema-erd-orthogonal-routing.md) — `PASS`
- UX heuristic evaluation: [eval-0056-ux-schema-erd-orthogonal-routing](../evaluation/eval-0056-ux-schema-erd-orthogonal-routing.md) — `PASS`
- Fix log: not created

## Verification Evidence

- Mermaid asset build, byte-freshness, deliberate stale-output failure, adapter, zoom-helper, exact attempt-order, installed-package, and license checks passed.
- Generated bundle is `4,961,964` bytes, a `1,516,979` byte (`44.03%`) increase over the accepted baseline and within FEAT-0055's budget.
- `45` focused Schema route, presentation, and UI tests passed after refreshing one stale object-count expectation.
- Browser QA passed at `1440`, `920`, `700`, and `320`: all nine subjects present, ELK rendered, layout label correct, and no document overflow.
- Partial navigation, back/forward, rapid replacement, warm cache, blocked adapter, no-script, and invalid-query paths passed.
- Temporary screenshots were reviewed from `/tmp`; none were tracked.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: accepted ELK policy fully adopted.
  - notes: the reusable browser harness had two stale pre-FEAT-0058 expectations (global-link counting and maintenance object count); both were corrected to current Schema Presentation truth.

## Human Review Outcome

- Decision: automatic sequential approval authorized on `2026-07-24`.
- Returned layer if any: none.
- Follow-up run: FEAT-0059.
