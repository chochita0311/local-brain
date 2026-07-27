# RUN-20260724-64: Pinned Session Recall And Controls

## Metadata

- ID: `run-20260724-64`
- Status: `passed`
- Feature: [feat-0059-pinned-session-recall-and-controls](../feature/feat-0059-pinned-session-recall-and-controls.md)
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Active Spec: [spec-0059-pinned-session-recall-and-controls](../spec/spec-0059-pinned-session-recall-and-controls.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal And Selected Loop

- Replace generic recent Context with owner-curated Session recall and add stable inventory/detail pin controls over FEAT-0058.
- Route: `Orchestrator → Spec Agent → Fullstack Builder → Contract Evaluator → Design Evaluator → Functional Evaluator → UX Heuristic Evaluator`.
- Screen Alignment mode: `extend`.

## Delivered Contract

- Added an uncapped global pinned projection while preserving FEAT-0058's bounded internal query.
- Projected current pin state into Session inventory and persisted detail.
- Added safe local pin/unpin POST routes with filter/page/mode return continuity, bounded errors, fragment orientation, and focus restoration.
- Replaced `최근 컨텍스트` with a complete `Pinned Sessions` panel.
- Moved question and event counts into one stable trailing utility layer before date and pin.
- Anchored optional Subsessions at the lower trailing edge without nesting either control in the Session link.
- Added primary detail pin control while keeping Subsessions ineligible.
- Updated product overview, durable navigation behavior, and pin consumer ownership.

## Current Artifacts

- Spec: [spec-0059-pinned-session-recall-and-controls](../spec/spec-0059-pinned-session-recall-and-controls.md)
- Contract evaluation: [eval-0059-contract-pinned-session-recall-and-controls](../evaluation/eval-0059-contract-pinned-session-recall-and-controls.md) — `PASS`
- Design evaluation: [eval-0059-design-pinned-session-recall-and-controls](../evaluation/eval-0059-design-pinned-session-recall-and-controls.md) — `PASS`
- Functional evaluation: [eval-0059-functional-pinned-session-recall-and-controls](../evaluation/eval-0059-functional-pinned-session-recall-and-controls.md) — `PASS`
- UX heuristic evaluation: [eval-0059-ux-pinned-session-recall-and-controls](../evaluation/eval-0059-ux-pinned-session-recall-and-controls.md) — `PASS`
- Fix log: not created

## Verification Evidence

- `46` focused pin, inventory, pin UI, and shared UI-contract tests passed.
- The uncapped query returned `101` synthetic pins, proving the product projection does not hide older pins.
- Browser checks passed at `1440`, `920`, `700`, and emulated `320` with no document overflow.
- At wide widths, compared rows kept equal `113px` rendered heights and aligned upper utilities. At `320`, rows with and without Subsessions both rendered at `171px`.
- Wide panel height stopped at `420px` while its synthetic content scrolled; narrow layouts reported `max-height: none` and ordinary flow.
- A Claude-filtered inventory showed `9` rows and all `12` global pins.
- Browser pin/unpin preserved `source=claude&page=1`, changed label/pressed/panel state, and restored focus below the sticky header.
- Primary detail rendered one pin control; the persisted Subsession rendered none.
- Only localhost document and static requests appeared, with no console warning or error.
- Browser evidence used a temporary synthetic database; no real runtime Session or pin was read or changed.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: complete pinned recall and controls delivered.
  - notes: visual QA first exposed narrow row-height drift and a fragment target under the sticky header; lower Subsession positioning and pin scroll margin closed both before evaluation.

## Human Review Outcome

- Decision: automatic sequential approval authorized on `2026-07-24`.
- Returned layer if any: none.
- Follow-up run: FEAT-0060.
