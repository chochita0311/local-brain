# FEAT-0084: Project-Grouped Pinned Sessions

## Metadata

- ID: `feat-0084`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Created: `2026-09-02`
- Updated: `2026-10-26`

## Goal

- Make the global Pinned Sessions panel easier to scan by grouping pinned Sessions by Project while preserving direct Session recall.

## Acceptance Contract

- The panel groups Sessions by current workspace identity and shows the current home-abbreviated workspace path once as the group heading, falling back to the workspace label when no path exists.
- Git-backed Project groups appear before non-Git path groups. Each section is ordered alphabetically by that displayed heading, case-insensitively with a deterministic identity tie-break. Incrementally refreshed cached display names do not affect that order.
- Sessions inside one Project remain ordered by displayed activity date descending, with existing pin-time and Session-ID tie-breaks.
- Each Session row replaces the repeated workspace line with its Session-owned Git branch when one exists; a branchless row omits that line.
- The global pin count, source cue, activity date, Session destination, uncapped membership, wide internal scroller, narrow document flow, and in-place pin/unpin continuity remain unchanged.

## Scope Boundary

- In:
  - pinned read-model projection of Session branch and workspace Git-root state
  - deterministic Project grouping and ordering
  - grouped panel markup and native shared-token styling
  - focused read-model, template, responsive, and regression evidence
- Out:
  - pin persistence or eligibility changes
  - manual group ordering, collapsing, filtering, or new controls
  - workspace display-name or Git discovery changes
  - changes to the main Session timeline or Session detail

## Surface Lanes

- Read-model lane:
  - path roots: `src/localbrain/session_pins.py`, focused tests
  - dependencies: existing workspace and Session Git metadata
  - expected evidence: Git classification, alphabetical group order, within-group activity order, branch projection, uncapped membership
  - evaluator ownership: `contract`, `functional`
- Presentation lane:
  - path roots: `src/localbrain/templates/sessions.html`, `src/localbrain/static/styles.css`, UI tests
  - dependencies: read-model lane
  - expected evidence: native group hierarchy, optional branch line, source/date retention, bounded scrolling, narrow flow, long-label containment
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: product, design, PRD, Feature, and Spec owner documents
  - dependencies: both implementation lanes
  - expected evidence: current grouping and ordering contract without rewriting FEAT-0059 history
  - evaluator ownership: `contract`

## Contract Surfaces

- The uncapped Pinned Sessions read model and its ordering/grouping projection.
- The Sessions/Projects inventory shared Pinned Sessions panel.
- Workspace `git_root`, workspace display identity, and Session `git_branch` remain existing sources of truth.

## User-Visible Outcome

- Pinned Sessions scan as Git Projects first and other working paths second, with alphabetical Project headings and newest Sessions first inside each heading.

## Entry And Exit

- Entry point: open Sessions or Projects with at least one pinned Session.
- Exit or transition behavior: selecting a pinned row still opens the same Session detail; pin mutations still refresh the panel in place.

## State Expectations

- Populated: one heading per Project followed by its pinned Sessions.
- Branchless: no empty metadata placeholder appears.
- Empty: the existing pin guidance remains unchanged.
- Narrow: groups remain in ordinary document flow without a nested panel scroller.

## Dependencies

- FEAT-0058 and FEAT-0059 are `passed` regression contracts.
- The owner approved the grouping and ordering boundary on `2026-09-02`.

## Likely Affected Surfaces

- `src/localbrain/session_pins.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/sessions.html`
- `src/localbrain/static/styles.css`
- `tests/test_session_pins.py`
- `tests/test_session_pin_ui.py`
- `tests/test_ui_contract.py`
- Pinned Sessions product and design owner docs

## Pass Or Fail Checks

- Pass if Git groups precede non-Git groups and both sections sort alphabetically.
- Pass if Sessions remain newest-first inside each Project with deterministic tie-breaks.
- Pass if the group heading owns Project context and rows show only a non-empty Session branch in the former Project line.
- Pass if source cue, activity date, count, membership, destinations, empty state, scroller, and pin continuity regressions pass.
- Fail on flat activity ordering, branch-based Git classification, duplicate Project labels per row, new collapse/sort controls, or hidden pins.

## Regression Surfaces

- FEAT-0059 global recall, uncapped membership, empty state, panel scroll ownership, responsive flow, and pin mutation continuity.
- FEAT-0069 source cues.
- Sessions/Projects view parity and repository privacy.

## Harness Trace

- Latest ordering correction: [Run 204](../run/run-20261026-204-pin-order-and-palette-focus.md). Earlier grouping and scroll checks below retain their own scope.

- Spec doc: [spec-0084-project-grouped-pinned-sessions](../spec/spec-0084-project-grouped-pinned-sessions.md)
- Run: [run-20261020-181-pinned-scroll-containment](../run/run-20261020-181-pinned-scroll-containment.md) — scoped Frontend correction; the [original grouping Run](../run/run-20260902-94-project-grouped-pinned-sessions.md) retains its fullstack evidence.
- Execution profile: `fullstack-product`
- Latest evaluator report: [Run 181 functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#pinned-scroll-containment-delivery--2026-10-20-superseded-artifact) — scoped scroll-correction `PASS`; [original grouping evaluation](../evaluation/eval-0084-functional-project-grouped-pinned-sessions.md) retains the fullstack evidence.
- Latest fix note: not created

## Continuity Notes

- `2026-09-02`: approved from direct owner direction; clarified Project order as Git first, then non-Git, with alphabetical ordering inside both sections and activity ordering only inside each Project.
- `2026-09-02`: passed with deterministic derived grouping, optional branch metadata, 65 focused and 482 full tests, exact-width synthetic Chrome evidence, and current privacy/schema-cleanup contracts.
- `2026-10-20`: owner-reported blank document scrolling starts the bounded Frontend correction in Run 181. Keep hidden accessibility text inside the Pinned Sessions scroller; preserve grouping, labels, membership and responsive scroll ownership. Required correction evaluations: Functional, Design and Interaction.

- `2026-10-20`: Run 181 passed the scoped scroll correction in web and packaged WebKit. The running app and ZIP were refreshed; fourth-page pin continuity retains the evidence limit recorded in the Run.
- `2026-10-26`: [Run 204](../run/run-20261026-204-pin-order-and-palette-focus.md) restores alphabetical displayed-path ordering when cached workspace names mix legacy and home-abbreviated formats. Eighteen related tests, synthetic route rendering and actual app/web readback pass; saved pins and their timestamps are preserved.
