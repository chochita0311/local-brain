# RUN-20260718-33: In-App Schema Explorer

## Metadata

- ID: `run-20260718-33`
- Status: `passed`
- Feature: [feat-0028-in-app-schema-explorer](../feature/feat-0028-in-app-schema-explorer.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Active Spec: [spec-0028-in-app-schema-explorer](../spec/spec-0028-in-app-schema-explorer.md)
- Attempt: `1`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Alignment Mode: `extend`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Add and validate the read-only `System > Schema` Explorer from the passed v1 package contract without expanding into runtime data or cleanup work.

## Selected Loop

- Feature type: product.
- Surface: fullstack.
- Surface lanes: data/contract → backend route → frontend navigation/rendering → docs/design parity.
- Required evaluators: contract, design, functional, and UX heuristic.
- Current phase: complete.

## Surface Lanes

- Data/contract:
  - roots: schema loader, new read model, tests
  - dependency: passed FEAT-0027
  - evidence: manifest-only normalization and no-DB boundary
  - evaluators: contract, functional
- Backend route:
  - roots: `main.py`, route tests
  - dependency: data/contract
  - evidence: global/area/table/invalid/unavailable HTTP states
  - evaluators: contract, functional
- Frontend navigation/rendering:
  - roots: base/schema templates, CSS, route module, local Mermaid adapter
  - dependency: contract evaluation
  - evidence: ordinary links, local render, history/focus, 1440/920/700/320
  - evaluators: design, functional, UX heuristic
- Docs/design parity:
  - roots: Design Constitution/governance, Architecture, README, Developer Guide
  - dependency: settled frontend
  - evidence: eight-destination and Explorer-family ownership
  - evaluators: contract, design

## Contract Surfaces

- v1 loader consumption, `/schema`, query normalization, active shell state, strict local Mermaid, fallback links/content, history/focus, design-policy and privacy boundaries.

## Invocation Context

- Golden sources: FEAT-0027 manifest, FEAT-0025 adapter, Local Context Explorer, Design Constitution.
- Relevant policies: Architecture, Schema Presentation, Privacy, Design Evaluation, Interaction Evaluation.
- Skill: `screen-alignment` in `extend` mode; current rendered Explorer baseline inspected before edits.

## Current Artifacts

- Spec: [spec-0028-in-app-schema-explorer](../spec/spec-0028-in-app-schema-explorer.md)
- Contract evaluation: [eval-0028-contract-in-app-schema-explorer](../evaluation/eval-0028-contract-in-app-schema-explorer.md)
- Design evaluation: [eval-0028-design-in-app-schema-explorer](../evaluation/eval-0028-design-in-app-schema-explorer.md)
- Functional evaluation: [eval-0028-functional-in-app-schema-explorer](../evaluation/eval-0028-functional-in-app-schema-explorer.md)
- UX heuristic evaluation: [eval-0028-ux-in-app-schema-explorer](../evaluation/eval-0028-ux-in-app-schema-explorer.md)
- Fix log: not created
- Heuristic backlog: not created; no suggestions remain

## Evaluation Coverage

- Contract: `PASS`, complete v1/route/navigation/docs/package/privacy coverage.
- Design: `PASS`, complete shell/Explorer/diagram/catalog/1440/920/700/320 coverage.
- Functional: `PASS`, complete route/history/focus/rapid/warm-cache/failure/no-script/package/regression coverage.
- UX heuristic: `PASS`, no blocking contradiction or residual suggestion.

## Current Route

- Next role: FEAT-0029 planner under the approved sequence.
- Current blocker classification: none.
- In-run route: complete.
- Post-run recommendation: proceed to FEAT-0029; every required evaluator passed.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: complete constitution-preserving Schema Explorer extension
  - notes: Mermaid JSON-safe source transfer and global-canvas readability were corrected before final evaluation; no fix Run was required

## Post-Contract Regression Check

- Needed: yes.
- Result: PASS.
- Notes: schema/data parity, 102 tests, four viewport browser QA, interaction/failure/no-script/warm-cache states, final wheel, privacy, and whitespace passed.

## Human Review Outcome

- Decision: automated Feature boundary passed under the approved sequential workflow.
- Returned layer if any: none.
- Follow-up run: RUN-20260718-34 for FEAT-0029.

## Consistency List

- Structure: keep page heading, metric band, Explorer rail, and one primary technical canvas.
- Responsive: rail becomes in-flow at 920 and sequential at 700; 320 remains usable.
- Type/tone: existing page, section, label, mono, link, and status roles only.
- Shape/depth: existing card/panel border, radius, and low elevation; no new shell styling.
- Interaction: ordinary links first; enhancement owns atomic region replacement, history, focus, and Mermaid only.
- Data density: long identifiers wrap; dense global diagram scrolls internally; detail rows restructure before text shrinks.

## Continuity Notes

- `2026-07-18`: Run initialized after FEAT-0027 passed and the current Local Context Explorer was inspected at the rendered 1440px baseline.
- `2026-07-18`: Run passed after contract, design, functional, and UX heuristic evaluation; no fix route or heuristic backlog was required.
