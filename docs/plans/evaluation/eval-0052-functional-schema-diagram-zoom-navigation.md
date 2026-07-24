# EVAL-0052: Schema Diagram Zoom Navigation — Functional

## Metadata

- ID: `eval-0052-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260724-57`
- Attempt: `1`
- Feature: [feat-0052-schema-diagram-zoom-navigation](../feature/feat-0052-schema-diagram-zoom-navigation.md)
- Spec: [spec-0052-schema-diagram-zoom-navigation](../spec/spec-0052-schema-diagram-zoom-navigation.md)
- Execution Profile: `frontend-product`
- Surface Lane: render binding, zoom calculation, scroll ownership, replacement, fallback, and regressions
- Evidence Coverage: `partial`
- Created: `2026-07-24`

## Scope

- Evaluated the route-scoped zoom controller, deterministic calculations, rendered-wrapper boundary, partial-navigation rebind, and existing Schema/Mermaid regressions.

## Checks And Evidence

- The server-rendered global Schema response contains one diagram viewport and the complete disabled zoom control group without opening the runtime database.
- Controls become available only after the strict local Mermaid adapter returns a rendered wrapper; failure leaves them disabled and retains the bounded fallback.
- Scale is clamped to `0.1–3.0`, wheel deltas are bounded, and reset/fit/button paths share one scale application path.
- Deterministic Node assertions pass for lower/upper clamping, zoom-in/zoom-out direction, and pointer-anchored scroll correction.
- The modifier guard returns before `preventDefault()` for ordinary wheel events; only `Ctrl`/`Cmd` wheel reaches zoom handling, with a non-passive listener.
- Zoom changes only the rendered wrapper width and viewport scroll coordinates. It does not call Mermaid again, update query/history state, or write storage.
- Each initial or replacement Schema region invokes setup only after successful rendering; replaced DOM owns new controller state and removes prior node listeners with the outgoing region.
- JavaScript syntax, pinned Mermaid asset freshness, Mermaid asset tests, Schema route/view-model tests, all 260 Python tests, data-model parity, schema-presentation freshness, privacy over 544 candidate files, and diff whitespace pass.

## Evidence Gaps

- The required in-app browser control was unavailable, so no automated pointer wheel/pinch, button click, `requestAnimationFrame` scroll update, or repeated partial-navigation interaction was directly observed in rendered pixels.
- Runtime-independent calculations, event ownership, route markup, rebind source, assets, and complete regressions pass. This report does not claim the unobserved pointer interaction as browser-verified.
- Acceptance impact: non-blocking for source-level functional pass; direct owner use remains the explicit interaction confirmation.

## Findings

- No calculation, modifier interception, persistence, adapter, route, fallback, or regression defect was found in the exercised surfaces.

## Route

- Next action: `pass`; retain one first-use interaction check in the Run.
