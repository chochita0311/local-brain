# FEAT-0028: In-App Schema Explorer

## Metadata

- ID: `feat-0028`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Created: `2026-07-18`
- Updated: `2026-07-19`

## Goal

- Let the owner open `System > Schema`, understand the complete LocalBrain model, move into any of the eight subject areas, and inspect one table's meaning and relationships without leaving the local application or reading raw DDL.

## Acceptance Contract

- The persistent `System` navigation lists `Schema` immediately below `Sources`, uses the next stable navigation position, and marks it current on the canonical `/schema` route.
- `/schema` defaults to the global schema overview and renders the level-zero Mermaid ERD, baseline identity, current object counts, and links to all eight subjects.
- Canonical subject state uses `?area=<subject-id>`. Each valid area shows its focused Mermaid ERD and only its owning table catalogs while retaining visible links to the other subjects.
- Canonical table state uses `?area=<subject-id>&table=<table-name>`. A valid selection makes the table visibly and programmatically current and exposes its complete approved catalog.
- An invalid area falls back to the global overview with bounded feedback. An invalid or mismatched table falls back to the valid selected area without a raw error or false selection.
- Desktop uses an Explorer-style subject rail and fluid main canvas. At compact and narrow widths the subject control enters the document flow as a complete link group; no subject becomes unreachable or requires hover.
- The main canvas presents the focused diagram before the detailed catalog. Global diagrams omit full columns; subject diagrams show only the keys and important relationship fields needed for comprehension.
- Server-rendered subject and table links are fully executable. Mermaid progressively enhances diagram regions and is never the only path to relationship or catalog information.
- Direct entry, refresh, back, and forward restore URL, visible selection, `aria-current` state, focus destination, and document orientation coherently.
- Mermaid loads only through the passed FEAT-0025 local adapter and renders only FEAT-0027 packaged definitions with restrictive security settings.
- A Mermaid load or render failure leaves subject navigation and the complete textual catalog usable and shows a bounded diagram-unavailable state.
- A missing or invalid packaged schema manifest yields an intentional unavailable page without querying runtime rows as fallback.
- The route is read-only and exposes no database rows, private runtime values, SQL console, schema editor, or mutation controls.
- The implementation updates the Design Constitution from seven to eight persistent destinations and records Schema as an Explorer-family surface before adopting the new shell contract.

## Scope Boundary

- In:
  - `System > Schema` navigation item
  - canonical `/schema` route
  - global overview
  - eight subject-area views
  - table catalog detail state
  - `area` and `table` URL normalization
  - local Mermaid rendering from the packaged presentation manifest
  - server-rendered progressive fallback
  - active, invalid, unavailable, and render-failure states
  - responsive Explorer-family layout at supported widths
  - direct entry, history, focus, and no-script continuity
  - Design Constitution, Architecture, and user/developer documentation parity
- Out:
  - schema or row editing
  - SQL execution or a general database browser
  - runtime row, path, Session, document, URL, credential, or artifact display
  - cleanup decision actions, migration controls, or keep/change/remove/defer review UI
  - arbitrary Mermaid input, external editor, CDN, or remote rendering
  - a general frontend framework or unrelated shell redesign
  - schema search, custom diagram authoring, export, or saved layouts

## Surface Lanes

- Contract integration lane:
  - path roots: FEAT-0027 manifest loader, route view model, schema-only privacy boundary
  - dependencies: passed FEAT-0027
  - expected evidence: exact v1 consumption, URL normalization, invalid and unavailable behavior, and no runtime-row access
  - evaluator ownership: `contract`, `functional`
- Backend route lane:
  - path roots: `src/localbrain/main.py`, bounded Schema read-model module, route tests
  - dependencies: contract integration lane
  - expected evidence: global, area, table, invalid, missing-manifest, and direct-entry responses
  - evaluator ownership: `contract`, `functional`
- Frontend surface lane:
  - path roots: `src/localbrain/templates/base.html`, Schema template, `src/localbrain/static/styles.css`, Schema interaction module, FEAT-0025 adapter
  - dependencies: backend route lane
  - expected evidence: persistent navigation, Mermaid rendering, progressive fallback, selection parity, focus, history, and responsive containment
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Docs and design-policy lane:
  - path roots: Design Constitution, Project Architecture, README and Developer Guide where behavior is owned
  - dependencies: frontend surface lane
  - expected evidence: eight-destination navigation, Explorer-family ownership, local asset and route documentation parity
  - evaluator ownership: `contract`, `design`

## Contract Surfaces

- `/schema` HTML route
- `area` and `table` query normalization and canonical state
- `localbrain.schema-presentation.v1` consumer contract
- local Mermaid adapter and packaged asset contract
- server-rendered subject and table link fallback
- `active_page = schema` shell state
- persistent navigation order and Design Constitution ownership
- schema-only privacy and read-only behavior

## Required Evaluators

- `contract`: manifest consumption, route/query shape, source-of-truth ownership, local asset, privacy, and docs parity.
- `design`: shared shell, Explorer hierarchy, subject rail, diagram and catalog containment, long technical values, and `1440`, `920`, `700`, and `320` rendering.
- `functional`: global, eight areas, table detail, invalid state, direct entry, history, no-script, render failure, missing manifest, and warm-cache asset behavior.
- `ux-heuristic`: subject and table orientation, diagram-to-catalog comprehension, focus, link affordance, and narrow-screen friction.

## User-Visible Outcome

- The owner can open Schema from the System navigation and move from the global ERD into any subject area and table catalog while staying oriented in the LocalBrain shell.

## Entry And Exit

- Entry point: `System > Schema`, `/schema`, or a canonical area and table URL.
- Exit or transition behavior: subject and table changes remain within `/schema`; ordinary shell navigation leaves the surface without changing schema state elsewhere.

## State Expectations

- Default: global overview with eight subject links and no table selected.
- Area selected: matching subject navigation and ERD are current; unrelated table details are absent.
- Table selected: the owning area and table are visibly and programmatically current and the complete table catalog is reachable.
- Invalid area: global overview plus bounded correction feedback.
- Invalid table: valid area remains current with bounded table feedback and no false detail.
- Mermaid loading: textual content is already present; no blank-page intermediate state.
- Mermaid failure: diagram unavailable message appears inside the diagram panel while links and catalogs remain usable.
- Manifest unavailable: bounded unavailable page; no runtime database fallback.
- Narrow viewport: all subjects, diagrams, catalogs, and shell destinations remain reachable at 320px.
- Success: URL, visible selection, accessibility state, diagram, and catalog agree.

## Dependencies

- FEAT-0025 is `passed`.
- FEAT-0026 is `passed`.
- FEAT-0027 is `passed`.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- bounded Schema read-model or presentation consumer module
- `src/localbrain/templates/base.html`
- new Schema template
- `src/localbrain/static/styles.css`
- route-scoped Schema JavaScript and FEAT-0025 Mermaid adapter
- route, manifest integration, no-row, and browser interaction tests
- `docs/policies/design/design-constitution.md`
- `docs/policies/project/architecture.md`
- `README.md` or Developer Guide if user-visible run behavior changes

## Pass Or Fail Checks

- Pass if `Schema` appears immediately below `Sources`, `/schema` marks it current, and all existing destinations retain their routes and shell geometry.
- Pass if global, every subject, and every table state is reachable through ordinary links with JavaScript disabled.
- Pass if valid `area` and `table` state produces matching URL, visible selection, `aria-current`, diagram, and catalog.
- Pass if invalid parameters fall back exactly as contracted without a server error or false current state.
- Pass if direct entry, refresh, back, and forward restore selection, focus, and orientation.
- Pass if Mermaid and network failure leave the textual catalog usable and if a stale client asset cannot leave new markup inert after a warm-cache revisit.
- Pass if rendered evidence at `1440`, `920`, `700`, and `320` contains long identifiers, all navigation, diagrams, and catalog content without overlap or clipping.
- Pass if the route and manifest contain no runtime row or machine-specific private value and expose no mutation control.
- Pass if Design Constitution, Architecture, and route behavior agree.
- Fail if the application maintains a second hand-authored ERD or fetches Mermaid or diagram content externally.

## Regression Surfaces

- persistent shell navigation, active states, compact and narrow navigation
- global search and all existing routes
- locally served CSS, JavaScript, asset freshness, and offline startup
- Local Context Explorer responsive and interaction patterns
- schema presentation manifest and data-model document parity
- repository privacy and no-runtime-row boundary

## Harness Trace

- Active spec doc: [spec-0028-in-app-schema-explorer](../spec/spec-0028-in-app-schema-explorer.md)
- Active run: [run-20260718-33-in-app-schema-explorer](../run/run-20260718-33-in-app-schema-explorer.md)
- Execution profile: `fullstack-product`
- Latest evaluator report: [contract](../evaluation/eval-0028-contract-in-app-schema-explorer.md), [design](../evaluation/eval-0028-design-in-app-schema-explorer.md), [functional](../evaluation/eval-0028-functional-in-app-schema-explorer.md), [UX heuristic](../evaluation/eval-0028-ux-in-app-schema-explorer.md)
- Latest fix note: [fix-0028-schema-selection-scroll-targets](../fix/fix-0028-schema-selection-scroll-targets.md)

## Continuity Notes

- `2026-07-18`: initial draft fixed the user-visible outcome at `System > Schema`, a global default, eight URL-addressable subjects, table detail, and progressive local Mermaid rendering.
- `2026-07-18`: entered the sequential loop after FEAT-0027 passed; `screen-alignment` extend mode fixes the existing Explorer shell, token, responsive, and real-content constraints for SPEC-0028.
- `2026-07-18`: passed attempt 1 with manifest-only `/schema`, eight subject areas and 21 table states, strict local Mermaid, ordinary-link fallback, coherent history/focus, exact 1440/920/700/320 containment, 102 passing tests, and installed-wheel evidence.
- `2026-07-19`: human review found that area and object selections shared the page heading as one scroll destination; FIX-0028 split them into relationship-map and table-detail targets without expanding feature scope.
