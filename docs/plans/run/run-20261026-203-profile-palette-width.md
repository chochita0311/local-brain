# run-20261026-203-profile-palette-width

## Metadata

- Status: `passed`
- Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md)
- Profile: `frontend-product`; screen-alignment mode: `extend`
- Lanes: palette frame/glyph geometry and hover text; browser/WebKit verification; asset delivery
- Owner: primary agent

## Approved Correction

Remove color-name hover tooltips from dropdown choices, retaining accessible
names. Match the menu frame's left/right edges to the diagonal trigger button's
background rectangle. Match each horizontal tag's painted width and both edges
to the diagonal tag, preserving the left-facing hole, selected fill/outline,
keyboard/focus, compact vertical spacing and saving. In short windows, the menu's
own scrolling must not add a width-changing scrollbar gutter or clip choices.
No ordering, source, data, model or backend/native contract change.

Verify rendered geometry and selection in Chromium and WebKit with synthetic
profiles, refresh app assets/ZIP/signature, preserve actual settings and remove
task-owned temporary artifacts at closure.

## Results

- Menu color-name hover tooltips are removed while accessible names remain.
  Frame edges match the trigger background and both SVG variants share their
  painted x bounds, matching glyph widths and edges without a menu offset.
  Bounded scrolling preserves this geometry without a scrollbar gutter.
- Ten geometry/tooltip/reachability checks pass at four Chromium and three
  WKWebView viewports; ten selection/save/focus/dismissal checks pass in each
  engine. Rendered inspection passes. Backend suites were not repeated for this
  presentation-only correction; broader native/recipient acceptance is unchanged.
- Refreshed only bundled settings JS/CSS and its signature. All 69 source assets
  match; private-path inspection, strict signatures, ZIP CRC and extracted inventory
  pass. App/web routes and assets, six WKWebView startup checks and three saved
  configurations' byte preservation pass. No backend/native compilation, dependency
  or model download. One app/backend and the web server remain running.
- [Design evidence](../evaluation/eval-0139-design-standalone-test-app.md#matching-palette-and-tag-widths--2026-10-26)
  and [delivery identity](../evaluation/eval-0139-functional-standalone-test-app.md#profile-palette-width-delivery--2026-10-26-superseded)
  retain the scoped result. Privacy, JS syntax, whitespace and catalog checks pass.
  No commit or publication. Task-owned preview/probes and staging/extraction/rollback
  copies are removed at closure.
