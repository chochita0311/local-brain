# SPEC-0028: In-App Schema Explorer

## Metadata

- ID: `spec-0028`
- Status: `approved`
- Run ID: `run-20260718-33`
- Attempt: `1`
- Parent Feature: [feat-0028-in-app-schema-explorer](../feature/feat-0028-in-app-schema-explorer.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lane: data/contract, backend route, frontend navigation/rendering, docs/design parity
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Alignment Mode: `extend`
- Created: `2026-07-18`
- Updated: `2026-07-19`

## Source Set

- Human request: include Mermaid in LocalBrain and expose schema by subject under `System > Schema`.
- Parent feature: FEAT-0028.
- Parent PRD: approved PRD-0003.
- Contract source: passed FEAT-0027 loader and package manifest; passed FEAT-0025 strict local Mermaid adapter.
- Visual source: Design Constitution and the rendered Local Context Explorer family at the current 1440px baseline.
- Evaluation sources: Design Evaluation, Interaction Evaluation, fullstack-product profile, and screen-alignment extend method/checklist.

## Implementation Goal

- Add a read-only, URL-addressable Schema Explorer that consumes only the packaged v1 manifest, fits the existing Explorer family, progressively renders local Mermaid, and remains fully navigable and understandable as server-rendered HTML.

## In-Scope Behavior

- Add a pure `schema_explorer` read model that accepts `area` and `table`, calls only `load_schema_presentation()`, and returns bounded global, area, table, invalid, or unavailable state.
- Normalize an unknown area to global with fixed feedback. Normalize a missing, unknown, or cross-area table to the valid area without table detail and with fixed feedback. Never echo invalid raw query text.
- Add `GET /schema` with `active_page="schema"`; do not open SQLite or repository documents.
- Add `Schema` immediately after `Sources` as stable destination `08`.
- Render baseline identity and counts, one global diagram and eight subject links by default, one focused diagram and only its table index in area state, and the complete selected-table catalog in table state.
- Include purpose/authority, lifecycle/rebuildability, producers, consumers, deletion, recovery, DDL ownership, columns, constraints, indexes, physical relations, and application relations in table detail.
- Keep diagram source in application-owned `text/plain` nodes accepted by the strict adapter. A static bounded fallback message remains if JavaScript or Mermaid fails.
- Add a route-scoped ES module that intercepts only unmodified same-origin `/schema` links, aborts stale requests, replaces only the Schema region, updates history/title, restores visible/programmatic selection, focuses and scrolls to the relationship-map heading after a model-area selection or the selected table-detail heading after an owned-object selection, announces state, and reruns the local adapter. On failure it executes the ordinary destination.
- On direct area/table entry, focus the matching contextual heading without forcing a scroll or changing the canonical query. On back/forward, reload the selected Schema region and restore the same contextual focus and nearest reachable document orientation.
- Update durable navigation and Explorer-family policy, governance version log, Architecture, README, and Developer Guide.

## Out-Of-Scope Behavior

- No DB rows, runtime paths, document bodies, external URL fetch, schema search, export, SQL, editing, cleanup decisions, partial API, framework, CDN, arbitrary Mermaid, or shell redesign.

## Surface Lanes

- Data/contract lane:
  - path roots: `src/localbrain/schema_explorer.py`, FEAT-0027 loader and manifest, contract tests
  - dependency order: first
  - responsibility: exact v1 consumption, state normalization, relation/table view model, unavailable boundary
  - evidence: pure tests with a positive manifest and missing/invalid loader states; no DB access
  - evaluator: contract, functional
- Backend route lane:
  - path roots: `src/localbrain/main.py`, route tests
  - dependency order: after data/contract
  - responsibility: canonical HTML route and active shell state
  - evidence: global, all areas, table, invalid and unavailable responses
  - evaluator: contract, functional
- Frontend navigation/rendering lane:
  - path roots: `base.html`, `schema.html`, `styles.css`, `schema-explorer.js`, local Mermaid adapter
  - dependency order: after route contract passes
  - responsibility: shell navigation, Explorer hierarchy, progressive diagram, selection/history/focus, responsive containment
  - evidence: source tests plus browser states at 1440, 920, 700, and 320
  - evaluator: design, functional, ux-heuristic
- Docs/design parity lane:
  - path roots: Design Constitution, design governance, Architecture, README, Developer Guide
  - dependency order: after frontend contract stabilizes
  - responsibility: eight destinations, Schema in Explorer family, route/asset/use ownership
  - evidence: docs inspection and link/privacy checks
  - evaluator: contract, design

## Alignment Contract

- Mode: `extend`; no exact target replaces LocalBrain's constitution.
- Preserve the current shell, sticky header, page heading rhythm, metric band, 260px Explorer rail role, low-elevation panel language, technical mono roles, and ordinary link affordances.
- At 920px the subject rail becomes a complete two-column in-flow group; at 700px it becomes a one-column sequential region and touch controls keep the constitution minimum.
- The diagram is a bounded technical panel before catalog content. Dense global rendering may scroll inside the panel; it must not widen the page.
- Table and relation content wraps long identifiers. Columns restructure into labeled rows at the narrow breakpoint instead of shrinking body text.
- No raw component colors, spacing, type, radius, shadow, motion, or private breakpoints.

## State And Interaction Contract

- `/schema`: global heading, baseline summary, global Mermaid source, eight subject links; no table current.
- `?area=<valid>`: subject link has `aria-current="page"`, focused source and table index match the area.
- `?area=<valid>&table=<owned>`: area and table links are current; complete detail is present.
- Invalid area: global state and fixed info feedback.
- Invalid/mismatched table: valid area state and fixed info feedback; no false detail.
- Manifest unavailable/invalid: active shell plus an intentional unavailable panel; no subject/diagram/detail controls and no fallback introspection.
- Mermaid pending, module failure, or render failure: a fixed textual diagram-unavailable message stays inside the panel and the complete relevant text/link surface remains executable.
- Link enhancement: outgoing content remains until incoming HTML exists; replacement is atomic. Superseded requests cannot win.
- History/direct entry: URL, heading, selection, `aria-current`, diagram and table detail converge before focus is placed on the matching relationship-map or table-detail heading. User-initiated and history selections scroll that heading below the sticky shell, or to the nearest reachable position when the document ends first; direct entry does not force document scroll.

## Data And Contract Assumptions

- Manifest data is trusted application-authored package data after loader validation, but Jinja escaping remains enabled.
- Subject and table order stays exactly as packaged.
- Table detail relationships are read-model projections of physical/application arrays and do not mutate the manifest.
- Route rendering does not need or receive a database connection.

## Contract Surfaces

- Producer: `localbrain.schema-presentation.v1` and bounded loader.
- Consumer: `schema_explorer.py`, `/schema`, Schema template, strict Mermaid adapter.
- Query contract: optional `area` and `table`; ordinary GET links are canonical and executable.
- Asset contract: locally served versioned module and pinned Mermaid bundle only.
- Privacy contract: schema and approved semantics only; no runtime DB or imported content.
- Stale-assumption check: FEAT-0027 check, Mermaid asset check, route/view-model tests, template marker tests, browser render and wheel inspection.

## Required Evaluators

- Contract: manifest-only source, normalization, route/query, navigation/policy ownership, privacy, package assets.
- Design: Explorer-family fidelity, shell stability, hierarchy, long technical content, diagram and catalog containment at 1440/920/700/320.
- Functional: all server states, executable no-script links, local Mermaid success/failure, direct entry, history/focus, warm-cache asset version, regressions.
- UX heuristic: global-to-area-to-table orientation, link/current clarity, diagram-to-text comprehension, keyboard and narrow-screen friction.

## Acceptance Mapping

- Navigation and active shell: base template and route response tests.
- Global/eight areas/table detail: pure read-model and route matrix plus browser evidence.
- Invalid/unavailable: bounded fixtures and rendered states.
- Local progressive Mermaid: strict adapter invocation and failure fallback evidence.
- History/focus/no-script: ordinary href inspection and browser navigation tests.
- Responsive and long values: 1440/920/700/320 rendered captures and overflow/geometry checks.
- Docs: constitution eight-destination and Explorer update plus governance v6, Architecture/README/Developer Guide links.

## Evaluation Focus

- Ensure dense global ERD remains readable via contained internal scrolling and does not compress the whole page.
- Ensure subject and table selection agree visibly and programmatically after partial replacement, direct entry, and history restoration.
- Ensure every table detail field is present without inventing fields outside the v1 manifest.
- Ensure module/asset/missing-manifest failures never remove executable navigation or textual explanation.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-18`: approved attempt 1 with screen-alignment `extend` authority and ordered contract → route → frontend → docs lanes.
- `2026-07-19`: clarified the existing destination-focus contract after human review: model-area changes target the relationship map, owned-object changes target table detail, and direct entry preserves its initial document position.
