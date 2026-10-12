# EVAL-0114: Observed Session Chart

## Metadata

- ID: `eval-0114`
- Status: `complete`
- Evaluator Types: `contract`, `design`, `functional`, `ux-heuristic`
- Result: `PASS WITH SUGGESTIONS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114](../spec/spec-0114-observed-session-chart.md)
- Run: [RUN-141](../run/run-20261006-141-observed-session-chart.md), attempt `1`
- Execution Profile: `fullstack-product`
- Surface Lanes: `observations`, `frontend`, `docs`
- Created: `2026-10-06`

## Scope And Evidence

The primary performed sequential contract, rendered design, functional and
interaction review under the approved observation-only boundary. Screen-alignment
adapt uses the owner-selected Chochita point/card and camera reference with native
LocalBrain typography, source cues, neutral surfaces and controls. Existing List
and Workflow Focus regions are frozen. No source content, private inventory,
runtime identifiers, local paths or screenshots are persisted in this report.

Code inspection covers both SELECT projections, source/workspace predicates,
timestamp normalization, GET eligibility, the additive display and return query,
sync redirect, browser state validation and owner documentation. The Chart does
not call activity-segment inference, source ingestion, a model or a mutator.

Rendered review used the existing local corpus through a temporary server with
startup disabled, and a separate bounded synthetic SQLite fixture. The latter
contains 21 eligible Sessions across three sources, one undated Session, invalid
metadata with valid Event fallback, an undated Event with valid metadata, an empty
workspace and excluded Maintenance/Subsession rows. Fixture files and review
pages belong to private task scratch and are removed at closeout.

## Contract And Functional Findings

- Complete matching metadata remains available beyond a List page; source scope
  excludes peers and workspace scope is preserved. Invalid source/workspace/page
  repair retains Chart and other valid scope. Synthetic page 2 still contains all
  21 eligible records rather than only its six List rows.
- Activity payload keys are Session ID, ordered timestamp occurrences,
  total/undated Event counts and labeled metadata times. No body or tool payload
  is selected. Synthetic Maintenance, Subsession and missing IDs return 404.
  Event fallback and undated/metadata-only reporting are observed directly.
- Selection opens a preview; keyboard Home/End reaches temporal endpoints,
  whole-period fit retains selection, time navigation changes the window and
  activity reveals observed points. Smaller scales retain readable cue hit areas
  and move long title inspection into the preview.
- Detail's ordinary backlink retains Chart, source and List page. The rendered
  round trip preserves selection, camera center, zoom and vertical position.
  Workflow destination remains the existing unchanged route.
- List's rendered row DOM equals its pre-change baseline. Rows, pagination and
  Pinned Sessions remain present; the existing Sessions/Projects switch remains
  usable. Chart structurally omits the secondary column and fills the primary
  content width.
- Offline activity retrieval keeps detail access, displays retry and contains no
  substituted dots. Restoring connectivity permits the same request to succeed.
  Synthetic empty/unknown-time states preserve scope and navigation. Deliberate
  parser failure and CSP-blocked scripts expose the native List fallback;
  unavailable browser storage still permits selection and preview.

## Design And Interaction Findings

Effective browser viewports of 1440, 700 and 320px show no outer horizontal
overflow. Wide previews float over the canvas; 700/320px previews follow it in
flow. Camera and preview/detail actions remain within the viewport, with 40px
navigation controls. Endpoint focus was corrected so long node labels remain
inside a 320px viewport and clear of the wide preview. The unknown-time message
respects hidden state. Counts distinguish whole scope from the current viewport;
the legend names recent observed time and collision-only vertical placement.

Selection is visible and programmatic, has a live announcement and preserves
layout. Native links keep detail/List escape paths. Vertical controls retain
access when touch scrolling belongs to the document. Reduced-motion styles
disable transitions without changing membership, selection or controls. No
relationship line, duration bar, decorative star field or foreign design token
is introduced.

## Evidence Gaps And Suggestions

- Automated unit/regression suites were not added or run in this turn. JavaScript
  syntax, Python AST parsing, whitespace and repository privacy checks pass.
  This gap is non-blocking for the first inspectable increment: its changed read
  boundary has source review and local rendered evidence; it is not a claim of
  full regression coverage.
- Synchronization POST was not executed to create fresh source changes. Existing
  enhanced reload behavior and the additive no-script display redirect were
  inspected. Scope preservation is observed in the form destination. This gap
  is non-blocking because scan/commit behavior is unchanged.
- Physical touch gestures, exhaustive wheel/drag-device combinations and very
  large inventories are not certified. Native touch page-scroll ownership,
  visible vertical/time controls and fixed hit areas are implemented; required
  narrow viewport containment is directly observed. These limits do not block
  seeing this version. Further device/stress review can be explicitly requested.
- Owner preference and any later work relationship inference remain unassessed.
  Inspect the first Chart before defining another boundary. This is the next
  human review, not an implementation failure or authorization for model work.

## Route

The ordinary local server was restarted with its existing storage after confirming
no running or queued tasks. Its refreshed Chart renders at the existing port
without console errors, the recall column or outer overflow. Only the ordinary
application remains running after task preview cleanup.

`pass` for the scoped first Chart with the evidence limits above. Keep the owner
screen review open. Existing Workflow Focus/Auto Work implementation files and
correction/inference contracts are untouched.
