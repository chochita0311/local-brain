# SPEC-0056: Schema ERD Orthogonal Routing

## Metadata

- ID: `spec-0056`
- Status: `approved`
- Run ID: `run-20260724-63`
- Attempt: `1`
- Parent Feature: [feat-0056-schema-erd-orthogonal-routing](../feature/feat-0056-schema-erd-orthogonal-routing.md)
- Parent PRD: [prd-0008-connected-atlassian-validation-and-schema-erd-routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lanes: asset/loader → Schema presentation → durable package contract
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Source Set

- Human approval on `2026-07-24`: execute both approved PRDs' Features automatically and sequentially.
- Passed FEAT-0055 accepted routing/package contract.
- Passed FEAT-0052 zoom, partial-navigation, focus, scroll, and textual-fallback behavior.
- Current package-owned Schema Presentation and nine Data Model ERD definitions.
- Screen Alignment mode: `extend`; no component or composition redesign.

## Asset Contract

- Pin direct `@mermaid-js/layout-elk@0.2.2` with `mermaid@11.16.0`.
- Lock transitive `elkjs@0.9.3`.
- Bundle Mermaid and the official loader definitions into the existing local ESM output; no runtime CDN, npm, or network import is allowed.
- Manifest exact versions, lock digest, licenses, and checksums for:
  - Mermaid: MIT;
  - layout loader: MIT;
  - elkjs: EPL-2.0;
  - esbuild: MIT.
- Freshness fails for missing, extra, or byte-stale outputs.

## Rendering Contract

- Register `elkLayouts` once before Mermaid initialization.
- Only Schema-owned nodes opt in through `data-localbrain-mermaid-layout="elk"`.
- Add transient frontmatter requesting ELK at render time; do not alter generated manifest Mermaid text.
- Attempt order is exactly:
  1. ELK source wrapper;
  2. unchanged source with Dagre;
  3. bounded textual fallback.
- ELK success reports `data-schema-layout-state="elk"` and `직각 관계 배치`.
- Dagre success reports `data-schema-layout-state="dagre"` and `기본 관계 배치`.
- Double failure disables zoom and preserves subject/table links plus the textual catalog.

## Interaction And Presentation

- No layout selector, URL parameter, or persisted preference is added.
- Existing `100%`, zoom in/out, reset, fit, modifier-wheel, ordinary scroll, history, partial replacement, focus, and rapid-selection behavior operates over whichever SVG succeeds.
- Supported widths are `1440`, `920`, `700`, and `320`; document overflow is prohibited while diagram-local scrolling remains allowed.
- Schema contents, relations, source definitions, database schema, and runtime data are unchanged.

## Verification

```bash
npm run check:mermaid
npm run test:mermaid
uv run python scripts/verify-installed-mermaid-assets.py
uv run python -m unittest tests.test_schema_explorer tests.test_ui_contract tests.test_schema_presentation -v
node scripts/qa-schema-explorer-browser.mjs <local-url> <temporary-output-dir>
```

## Open Blockers

- None.
