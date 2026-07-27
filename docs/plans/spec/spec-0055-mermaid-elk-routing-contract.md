# SPEC-0055: Mermaid ELK Routing Contract

## Metadata

- ID: `spec-0055`
- Status: `approved`
- Run ID: `run-20260724-59`
- Attempt: `1`
- Parent Feature: [feat-0055-mermaid-elk-routing-contract](../feature/feat-0055-mermaid-elk-routing-contract.md)
- Parent PRD: [prd-0008-connected-atlassian-validation-and-schema-erd-routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Surface Lanes: official package contract → isolated visual comparison → adoption decision
- Required Evaluators: `contract`, `design`, `functional`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Source Set

- Human approval on `2026-07-24`: approve and execute both PRDs' Features automatically and sequentially.
- Mermaid `11.16.0`, the current LocalBrain adapter/build/manifest, passed FEAT-0052, and current generated Schema sources.
- Official Mermaid [ER layout](https://mermaid.js.org/syntax/entityRelationshipDiagram.html#layout), [layout catalog](https://mermaid.js.org/config/layouts.html), and [`registerLayoutLoaders`](https://mermaid.js.org/config/setup/mermaid/interfaces/Mermaid.html#registerlayoutloaders) documentation.
- Official `@mermaid-js/layout-elk` `0.2.2` package metadata, README, source bundle, and MIT license.

## Implementation Goal

- Decide whether the official ELK loader is acceptable and remove every routing-policy choice from downstream FEAT-0056.

## Comparison Matrix

- Sources:
  - current global Schema ERD
  - sparse `local-context-corpus` subject ERD
  - dense `atlassian-source-memory` subject ERD
- Layouts: current Dagre and `elk` from `@mermaid-js/layout-elk@0.2.2`.
- Widths: `1440`, `920`, `700`, and `320`.
- Evidence: local headless Chrome render, relationship geometry, viewBox, labels/markers, repeat stability, containment, render duration, minimum product bundle, license, offline and failure paths.
- Synthetic screenshots and summary stay in `/tmp`; no image or generated payload is tracked.

## Accepted Routing Contract

1. Adopt ELK for every Schema global and subject ERD.
2. Keep a single default; do not add a layout selector or URL/persistence state.
3. Rounded right-angle routes are accepted. Sharp corners are not required.
4. Keep generated Mermaid definitions unchanged.
5. Mark only Schema-owned Mermaid nodes for ELK; other LocalBrain Mermaid consumers retain their existing layout.
6. Register the official layout loaders through `mermaid.registerLayoutLoaders(elkLayouts)`.
7. Render the Schema source with `layout: elk` as adapter-owned transient configuration.
8. If that render fails, retry the same source once with Dagre. If Dagre also fails, retain the existing textual fallback and disabled zoom controls.
9. FEAT-0052 zoom, fit, replacement, history, focus, and scroll contracts operate over whichever SVG succeeds and do not rerun layout.

## Package And Asset Contract

- Exact direct versions:
  - `mermaid@11.16.0`
  - `@mermaid-js/layout-elk@0.2.2`
- Compatibility evidence:
  - package peer dependency: `mermaid ^11.0.2`
  - package development contract: `mermaid ^11.16.0`
- Transitive ELK engine: `elkjs ^0.9.3`.
- The layout package is MIT-licensed; the `elkjs` engine is EPL-2.0.
- FEAT-0056 must:
  - pin the direct package and lockfile;
  - bundle all executable code locally with no runtime CDN or network request;
  - extend manifest dependency and checksum ownership;
  - retain the layout package and ELK engine license texts;
  - fail freshness checks on missing, extra, or byte-stale assets;
  - keep the existing Mermaid bundle until the replacement set passes checks atomically.
- Accepted budget:
  - minimum bundled JavaScript increase below `2 MiB` and `50%`;
  - global ELK render below `250 ms` in the comparison harness;
  - representative subject ELK render below `100 ms`.

## State And Interaction Contract

- Default: Schema requests ELK.
- ELK success: render, then bind existing zoom.
- ELK failure/Dagre success: expose a bounded fallback state while keeping the diagram usable.
- Double failure: existing text catalog remains authoritative.
- Replacement: each selected Schema region repeats the same ELK-then-Dagre policy and begins zoom at `100%`.
- Narrow widths: the page remains contained; diagram-local horizontal scrolling remains available.

## Acceptance Mapping

- Like-for-like source comparison → three current Schema definitions under two layouts.
- Four-width evidence → local Chrome matrix with no page overflow.
- Traceability/shape/crossings → reviewed temporary global, sparse, and dense captures.
- Determinism → repeat-stable viewBox, relationship paths, lines, and text; randomized decorative table-border paths are excluded from layout identity for both engines.
- Package/offline/license → exact versions, bundle delta, manifest requirements, MIT loader text, and EPL-2.0 engine text.
- Fallback → one Dagre retry, then text.
- Adoption choice → all Schema ERDs, one ELK default, no selector.

## Open Blockers

- None. FEAT-0056 is unblocked.

## Continuity Notes

- `2026-07-24`: Context7 documentation lookup failed twice at the network boundary; the same official Mermaid pages and locally installed pinned package source were used as the documented fallback.
