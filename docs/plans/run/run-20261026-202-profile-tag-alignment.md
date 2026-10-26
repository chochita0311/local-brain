# run-20261026-202-profile-tag-alignment

## Metadata

- Status: `passed`
- Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md)
- Profile: `frontend-product`; screen-alignment mode: `extend`
- Lanes: profile tag glyph/anchor/selection; browser/WebKit checks; asset delivery
- Owner: primary agent

## Approved Correction

Restore the original diagonal tag in each profile row. Only menu choices use
horizontal tags, with their point and hole on the left. Align the visible left
edge of every menu glyph with the visible left edge of its diagonal trigger,
including compact/coarse-pointer layouts. Replace the selected check with a
profile-colored outline and quiet fill, retaining accessible radio selection,
keyboard/focus, dismissal, saving and existing compact dimensions. No source,
data, ordering, synchronization or native/backend contract change.

Inspect the rendered baseline, verify geometry and selection in Chromium and
WKWebView with synthetic profiles, then refresh the app assets and delivery ZIP.
Preserve actual settings and remove task-owned temporary artifacts at closure.

## Results

- The row tag is diagonal; menu tags point left with the hole on that side.
  Painted glyph edges align within 0.2px across checked layouts. Selection uses
  profile fill/outline without a check column, preserving separate keyboard focus.
- Chromium and macOS WKWebView each pass 22 geometry/selection/save/dismissal
  checks. Seven responsive geometry/reachability checks pass in three Chromium
  viewports (including coarse pointer) and two additional WebKit viewports.
  Real Chromium trigger input and rendered before/after comparison pass.
  Existing backend tests were not repeated for this presentation-only correction.
- Updated JS/CSS in the existing app without backend/native compilation or
  dependency/model download. All 69 packaged data assets match source. Private
  build-path checks, signatures, ZIP CRC and extracted inventory parity pass.
  Actual app/web route and asset checks, six WKWebView startup checks and saved
  configuration byte preservation pass after sequential restart.
- [Design evidence](../evaluation/eval-0139-design-standalone-test-app.md#profile-tag-alignment--2026-10-26)
  and [delivery identity](../evaluation/eval-0139-functional-standalone-test-app.md#profile-tag-alignment-delivery--2026-10-26-superseded)
  retain this scoped receipt. JS syntax, privacy, whitespace and catalog checks
  pass. No commit/publication; physical native input and broader Feature acceptance
  retain prior limits. Task-owned server, probes and release/rollback copies are
  removed at closure; final app/web remain running.
