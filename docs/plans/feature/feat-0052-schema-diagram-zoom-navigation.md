# FEAT-0052: Schema Diagram Zoom Navigation

## Metadata

- ID: `feat-0052`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal

- Let the owner enlarge dense global and subject Mermaid ERDs in place without losing the existing contained-scroll behavior or Schema Explorer orientation.

## Acceptance Contract

- Every successfully rendered Schema diagram exposes visible zoom-out, current-percentage/reset, zoom-in, and fit controls inside the relationship-map panel.
- `Ctrl` or `Cmd` plus mouse wheel, and browser-normalized trackpad pinch, zoom around the pointer position.
- An unmodified wheel keeps ordinary vertical or horizontal scrolling and is never intercepted for zoom.
- Zoom remains bounded from `10%` through `300%`; controls expose disabled limits and an accurate visible percentage.
- `100%` restores the existing baseline diagram size. `맞춤` reduces the diagram only as needed to fit the current viewport width.
- A newly rendered global or subject diagram starts at `100%`; partial Schema navigation rebinds controls to the replacement diagram without stale listeners or state.
- Zoom changes only local SVG presentation and scroll position. It does not regenerate Mermaid, alter the packaged schema definition, update URL state, or persist user data.
- Mermaid load or render failure leaves controls unavailable and preserves the existing bounded textual fallback.
- Existing selection, history, focus, responsive containment, local asset, no-script, and privacy contracts remain intact.

## Scope Boundary

- In:
  - visible diagram zoom controls
  - modifier-plus-wheel and pinch zoom
  - pointer-centered scroll correction
  - `100%` reset and width fit
  - rerender/replacement binding
  - responsive control containment
- Out:
  - drag-to-pan, minimap, saved zoom, URL zoom parameters, export, fullscreen, or diagram editing
  - relationship-line shape changes
  - Mermaid bundle patching or custom ER renderer
  - schema presentation or database changes

## Surface Lanes

- Schema Explorer interaction lane:
  - path roots: `schema.html`, `schema-explorer.js`, `styles.css`, UI contract tests
  - dependencies: passed FEAT-0028 and pinned Mermaid 11.16.0
  - expected evidence: control semantics, modifier filtering, pointer-centered scaling, limits, fit/reset, rerender binding, compact containment
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable trace lane:
  - path roots: PRD-0003, FEAT/SPEC/RUN-0052, Schema presentation policy or README only when user-facing behavior requires it
  - dependencies: settled interaction
  - expected evidence: scope and unsupported straight-edge boundary remain explicit
  - evaluator ownership: `functional`

## Contract Surfaces

- `/schema` relationship-map markup
- route-scoped `schema-explorer.js`
- strict local Mermaid rendered-wrapper contract
- existing `.schema-diagram-scroll` containment

## User-Visible Outcome

- Dense ERDs can be enlarged under the pointer while ordinary scrolling and the complete textual Schema catalog remain available.

## State Expectations

- Default: rendered diagram at `100%`.
- Zoomed: percentage and disabled limit states are current.
- Fit: diagram width is no larger than the visible scroll viewport.
- Replacement: new diagram receives one fresh control binding at `100%`.
- Failure: fallback remains; zoom controls are disabled.
- Narrow: controls wrap inside the panel heading and remain touch reachable.

## Dependencies

- FEAT-0025, FEAT-0027, and FEAT-0028 are `passed`.

## Pass Or Fail Checks

- Pass if modifier-wheel/pinch zooms and plain wheel remains unhandled.
- Pass if pointer-centered zoom preserves the same visual neighborhood within normal rounding tolerance.
- Pass if buttons, percentage, bounds, reset, and fit agree after repeated actions.
- Pass if partial area/table navigation produces exactly one functional binding on the replacement diagram.
- Pass if render failure, no-script navigation, text catalogs, and existing history/focus behavior remain usable.
- Pass if controls and diagram remain contained at `1440`, `920`, `700`, and `320`.
- Fail if the feature mutates Mermaid source, steals ordinary scrolling, adds remote assets, or claims straight ER edges that the pinned renderer does not support.

## Regression Surfaces

- FEAT-0025 local Mermaid asset and strict adapter
- FEAT-0028 Schema selection, history, focus, fallback, and containment
- shared Explorer and compact control families
- static asset freshness and repository privacy

## Harness Trace

- Active spec: [spec-0052-schema-diagram-zoom-navigation](../spec/spec-0052-schema-diagram-zoom-navigation.md)
- Active run: [run-20260724-57-schema-diagram-zoom-navigation](../run/run-20260724-57-schema-diagram-zoom-navigation.md)
- Latest evaluations:
  - [design](../evaluation/eval-0052-design-schema-diagram-zoom-navigation.md) — `PASS WITH SUGGESTIONS`
  - [functional](../evaluation/eval-0052-functional-schema-diagram-zoom-navigation.md) — `PASS`
  - [ux heuristic](../evaluation/eval-0052-ux-schema-diagram-zoom-navigation.md) — `PASS`

## Open Review Decisions

- None. The owner approved modifier-wheel zoom on `2026-07-24`.

## Continuity Notes

- `2026-07-24`: first-use Schema review found that growing ERDs remained contained but became too small for efficient inspection.
- `2026-07-24`: Mermaid 11.16.0 ER edges are emitted with a hard-coded `basis` curve; public `flowchart.curve` configuration does not govern ER diagrams, so straight-edge work is excluded from this zoom Feature.
- `2026-07-24`: Attempt 1 passed pinned-asset checks, deterministic zoom calculations, Schema route/UI tests, the complete 260-test suite, data-model/schema-presentation parity, and privacy over 544 candidate files. Direct rendered modifier-wheel replay remains a non-blocking owner check.
