# SPEC-0052: Schema Diagram Zoom Navigation

## Metadata

- ID: `spec-0052`
- Status: `approved`
- Run ID: `run-20260724-57`
- Attempt: `1`
- Parent Feature: [feat-0052-schema-diagram-zoom-navigation](../feature/feat-0052-schema-diagram-zoom-navigation.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: Schema relationship-map controls and interaction
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Alignment Mode: `extend`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Source Set

- Human approval on `2026-07-24`: add modifier-plus-wheel zoom to increasingly dense Mermaid Schema ERDs.
- Passed FEAT-0025 and FEAT-0028.
- Current template, CSS containment, route-scoped replacement module, strict Mermaid adapter, Design Constitution, Design Evaluation, and Interaction Evaluation.
- Pinned local Mermaid `11.16.0` type definitions and ER renderer source.

## Implementation Goal

- Add bounded progressive zoom over the already rendered local SVG without changing the Mermaid source, adapter trust boundary, Schema read model, or ordinary-scroll contract.

## In-Scope Behavior

1. Add one compact control group to the relationship-map heading:
   - zoom out
   - current percentage, which also resets to `100%`
   - zoom in
   - width fit
2. Keep controls disabled until the local Mermaid render succeeds.
3. After render, capture the existing rendered wrapper width as the `100%` baseline and bind one local zoom controller.
4. Apply scale by changing the rendered wrapper's explicit pixel width; keep SVG width at `100%` and height automatic.
5. Bound scale to `0.1–3.0`.
6. For buttons, zoom around the center of the visible viewport.
7. For `Ctrl`/`Cmd` plus wheel or browser-normalized pinch:
   - prevent the modifier event
   - calculate a continuous multiplicative scale from `deltaY`
   - keep the content coordinate under the pointer stable by correcting `scrollLeft` and `scrollTop`
8. Do not prevent or reinterpret unmodified wheel events.
9. `100%` restores scale `1`.
10. `맞춤` applies `min(1, available viewport width / baseline width)`, within the global bounds.
11. Re-run setup after every successful initial or replacement Mermaid render. A replacement begins at `100%`.
12. Preserve ordinary links, history, focus, fallback, and no-script behavior.

## Out-Of-Scope Behavior

- Relationship edge geometry, `flowchart.curve`, ELK installation, Mermaid bundle patches, SVG path rewriting, custom renderer, saved state, URL state, drag pan, export, and fullscreen.

## Interaction Contract

- Plain wheel: browser owns scrolling.
- Modifier wheel/pinch: diagram owns bounded zoom.
- Buttons: keyboard and pointer executable with visible focus; minus/plus disable at bounds.
- Current percentage: always names current scale and resets to baseline when activated.
- Fit: horizontal width fit only; it does not promise that every label is readable without later zoom.
- Render unavailable: controls stay disabled and existing fallback text is authoritative.
- Area/table navigation: replacement is atomic, then Mermaid renders, then zoom controls bind, then existing focus behavior continues.

## Alignment Contract

- Mode: `extend`.
- Reuse the panel heading, secondary-control, border, radius, focus, type, spacing, and narrow touch roles.
- Keep the relation legend and zoom group as separate compact regions inside one wrapping heading-action area.
- Do not change the diagram canvas size at `100%`.
- At `700px` and below, the heading action area aligns left and the controls remain contained without shrinking text below approved roles.

## Contract Surfaces

- Template data attributes for controls and the scroll viewport.
- `renderSchemaDiagrams()` successful-render handoff.
- Per-render controller state stored only on the new DOM nodes.
- Existing strict `data-localbrain-mermaid="owned"` rendered wrapper.

## Acceptance Mapping

- Visible controls → template and UI contract markers.
- Modifier filtering and pointer anchoring → extracted deterministic helper tests plus browser/runtime evidence where available.
- Limits, reset, fit, and disabled state → helper/controller tests and source checks.
- Rerender binding → existing partial-navigation path invokes setup after each render.
- Containment → semantic CSS and supported-width evidence.

## Evaluation Focus

- Verify plain wheel is never prevented.
- Verify rapid pinch deltas remain smooth and bounded.
- Verify pointer neighborhood and viewport center remain stable after scale.
- Verify no duplicate listener after repeated subject/table replacement.
- Verify output/labels and disabled states remain accurate.
- Verify render failure and no-JavaScript paths are unchanged.

## Open Blockers

- None. Straight ER relationship edges are unsupported by the pinned renderer's public configuration and are explicitly outside this Feature.
