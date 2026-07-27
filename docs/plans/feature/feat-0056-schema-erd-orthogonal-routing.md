# FEAT-0056: Schema ERD Orthogonal Routing

## Metadata

- ID: `feat-0056`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0008-connected-atlassian-validation-and-schema-erd-routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal

- Apply the accepted FEAT-0055 Mermaid ELK policy so dense Schema ERD relationships are easier to trace while preserving the existing Schema Explorer, zoom controls, offline assets, and textual fallback.

## Acceptance Contract

- This Feature enters Spec work only if FEAT-0055 passes with ELK adoption accepted and an exact default or bounded selector policy.
- Every in-scope global or subject ERD uses the accepted layout policy and keeps Mermaid as the diagram renderer.
- If FEAT-0055 selects a visible layout control, its labels, active state, keyboard behavior, URL or non-persistence behavior, and narrow layout are explicit and do not compete with zoom controls.
- If FEAT-0055 selects an internal default, no unnecessary user control is added.
- Packaged ELK assets, loader registration, versions, licenses, manifest, and stale checks follow the accepted foundation contract and require no CDN or runtime network access.
- Render or layout-loader failure preserves the generated source, bounded unavailable state, and textual Schema catalog.
- Global and subject selection, partial navigation, history, focus, zoom percentage, fit/reset, modifier-wheel behavior, ordinary scrolling, and replacement binding remain usable.
- Orthogonal routing does not change database schema, generated table/relation content, user data, or saved layout state.

## Scope Boundary

- In:
  - accepted ELK loader and local packaged assets
  - accepted global, subject, density, default, or selector policy
  - any approved visible layout-control interaction
  - rendering, failure, zoom, navigation, and responsive integration
  - local asset, manifest, license, and freshness updates
- Out:
  - adopting a policy not selected by FEAT-0055
  - replacing Mermaid
  - manual layout, drag, waypoints, export, fullscreen, or saved diagram preference unless FEAT-0055 explicitly requires one bounded persisted choice
  - database or generated ER source changes
  - SVG path rewriting or Mermaid patching

## Surface Lanes

- Asset and loader lane:
  - path roots: package manifest/lock, Mermaid build scripts, vendor assets, license manifest, and `mermaid-adapter.js`
  - dependencies: accepted FEAT-0055 package contract
  - expected evidence: deterministic offline build, current manifest, loader registration, and bounded failure
  - evaluator ownership: `contract`, `functional`
- Schema presentation lane:
  - path roots: `schema.html`, `schema-explorer.js`, shared Schema styles, and UI contract tests
  - dependencies: asset and loader lane plus passed FEAT-0052
  - expected evidence: accepted layout policy, control semantics when applicable, zoom/navigation continuity, and supported-width containment
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: Schema presentation policy, data-model entrance, README/package documentation, and privacy checks
  - dependencies: completed product lanes
  - expected evidence: current asset and fallback ownership without duplicating generated Schema truth
  - evaluator ownership: `contract`

## Contract Surfaces

- FEAT-0055 accepted routing and package contract.
- Mermaid adapter loader registration.
- Local asset manifest, licenses, and stale checks.
- Schema Explorer layout state when a visible selector is approved.
- FEAT-0052 zoom and replacement-binding contract.
- Generated Mermaid source and textual fallback ownership.

## User-Visible Outcome

- The owner can trace dense Schema relationships through the accepted orthogonal routing without losing navigation, zoom, labels, markers, or a usable fallback.

## Entry And Exit

- Entry point: open `/schema` on any global or in-scope subject diagram.
- Exit or transition behavior: navigate, zoom, fit, reset, optionally switch an approved layout mode, or fall back to the textual catalog without losing Schema orientation.

## State Expectations

- Default: the accepted FEAT-0055 layout policy is active and legible.
- Loading: existing bounded Mermaid loading behavior remains intentional.
- Unavailable: layout or renderer failure exposes the textual fallback without dead controls.
- Error: no raw loader error, path data, or broken empty panel leaks to the user.
- Success: the diagram renders with accepted routing and all existing Schema interactions remain operational.

## Dependencies

- PRD-0008 is `approved`.
- FEAT-0055 must be `passed` with adoption accepted before this Feature may be approved.
- FEAT-0052 remains `passed`.
- If FEAT-0055 rejects ELK, mark this Feature `superseded` without creating a Spec or Run.

## Likely Affected Surfaces

- `package.json` and package lock
- `scripts/build-mermaid-assets.mjs`
- `scripts/test-mermaid-assets.mjs`
- `src/localbrain/static/vendor/mermaid/`
- `src/localbrain/static/mermaid-adapter.js`
- `src/localbrain/static/schema-explorer.js`
- `src/localbrain/templates/schema.html`
- `src/localbrain/static/styles.css`
- Schema asset, UI, route, and privacy tests
- Schema presentation and package documentation

## Pass Or Fail Checks

- Pass if every in-scope diagram follows the exact FEAT-0055 policy.
- Pass if relationship labels, markers, nodes, zoom, fit/reset, ordinary scrolling, partial navigation, history, and focus remain intact.
- Pass if visible layout selection exists only when approved and remains operable at `1440`, `920`, `700`, and `320`.
- Pass if packaged assets are deterministic, pinned, licensed, offline, and freshness-checked.
- Pass if loader/render failure leaves a usable textual catalog and unavailable state.
- Fail on CDN access, patched Mermaid, SVG rewriting, schema-content drift, stale controls, or a layout choice not approved by FEAT-0055.

## Regression Surfaces

- PRD-0003 and FEAT-0028 Schema Explorer.
- FEAT-0052 Schema zoom navigation.
- Data-model subject links, table selection, history, focus, and no-script behavior.
- Local asset packaging and repository privacy.

## Harness Trace

- Active spec doc: [spec-0056-schema-erd-orthogonal-routing](../spec/spec-0056-schema-erd-orthogonal-routing.md)
- Active run: [run-20260724-63-schema-erd-orthogonal-routing](../run/run-20260724-63-schema-erd-orthogonal-routing.md)
- Execution profile: `frontend-product`
- Latest evaluator reports: [contract](../evaluation/eval-0056-contract-schema-erd-orthogonal-routing.md), [design](../evaluation/eval-0056-design-schema-erd-orthogonal-routing.md), [functional](../evaluation/eval-0056-functional-schema-erd-orthogonal-routing.md), and [UX heuristic](../evaluation/eval-0056-ux-schema-erd-orthogonal-routing.md)
- Latest fix note: not created

## Open Review Decisions

- None. FEAT-0055 selected ELK for every Schema ERD, no selector, one Dagre retry, then textual fallback.

## Continuity Notes

- `2026-07-24`: initial draft created as a conditional product Feature that cannot proceed unless the separate ELK foundation contract accepts adoption.
- `2026-07-24`: human owner authorized automatic sequential approval and execution.
- `2026-07-24`: run `run-20260724-63` packaged the accepted ELK loader, applied it to every Schema ERD, and passed asset, route, four-width browser, navigation, failure, and no-script checks.
