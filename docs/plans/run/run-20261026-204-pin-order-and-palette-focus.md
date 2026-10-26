# run-20261026-204-pin-order-and-palette-focus

## Metadata

- Status: `passed`
- Feature: [FEAT-0084](../feature/feat-0084-project-grouped-pinned-sessions.md), [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Specs: [SPEC-0084](../spec/spec-0084-project-grouped-pinned-sessions.md), [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md)
- Profile: `fullstack-product`; screen-alignment mode: `extend`
- Lanes: pinned-group read model; settings palette focus/selection; browser/WebKit verification; offline app delivery
- Owner: primary agent

## Correction Boundary

The user reports reordered pinned projects and inconsistent selected-color line
weight when opening consecutive profile palettes in the app versus the web.
The existing contract remains Git groups first, then alphabetical displayed
headings, with activity ordering inside each group. Home-path generalization left
older cached workspace names alongside newer home-abbreviated names: the heading
renderer uses the path while sorting still uses the mixed cache. Sort against the
displayed path, falling back to the label only when no path exists. Preserve pins,
source order, source identities and imported records.

Reproduce sequential pointer opening in Chromium and native WKWebView before
changing the palette. Preserve selected-color semantics, distinct keyboard focus,
tag/frame geometry, dismissal and saving. Classify the reported line-weight
difference as focus/selection border strength, not a layout redesign.

Use synthetic fixtures for screenshots and tests. Read actual runtime state only
to confirm sorting and saved-state preservation. Rebuild the frozen Python backend
offline, reuse the unchanged native shell, verify and replace the local app/ZIP.
No model download, dependency upgrade, commit or publication. Broader Feature and
recipient acceptance remain unchanged. Remove task-owned temporary artifacts at
closure.

## Results

- Group sorting now uses the rendered current path instead of mixed cached names.
  The new mixed-format regression and related pin behavior/template suites pass:
  18 tests. A synthetic browser route shows two Git groups alphabetically before
  a non-Git group. Actual app/web route readback confirms the reported first group
  is restored. No database migration or record rewrite was needed.
- Trusted AppKit pointer events delivered to an isolated WKWebView reproduce the
  reported thick line: SVG hits add a 2px keyboard outline and 3px shadow over the
  1px selected border; button-edge hits do not. Decorative SVGs now pass hits to
  the button. A scoped keyboard flag also retains the shared focus ring when
  WebKit fails to recognize a scripted arrow-key focus move after pointer opening.
  Nine repeated center/edge opens, two keyboard focus states and save/reopen pass.
  Chromium passes sequential profile opens, keyboard/pointer switching, dismissal,
  frame alignment and accessible-name/tooltip checks. Rendered comparison passes.
- Frozen backend rebuilt offline using locked cached dependencies; native shell
  reused. All 105 bundled Python modules and 69 data assets match source. Strict
  signatures, private-path inspection, archive CRC and extracted inventory pass.
  Actual app/web route/asset checks and six WebKit startup checks pass. Three saved
  configuration files and pin membership/timestamps remain identical.
- [Design evidence](../evaluation/eval-0139-design-standalone-test-app.md#palette-pointer-and-keyboard-focus--2026-10-26)
  and [current delivery identity](../evaluation/eval-0139-functional-standalone-test-app.md#pin-order-and-palette-focus-delivery--2026-10-26-current)
  retain the scoped result. JS syntax, whitespace, privacy and artifact-catalog
  checks pass. No model download, commit or publication. Task-owned previews,
  probes, build environment/cache, staging/extraction and rollback copies are
  removed at closure; the refreshed app/backend and web server remain running.

## Evidence Limits

This proves the bounded correction. Native pointer evidence uses events sent to
the probe's own AppKit window, without Accessibility or system capture changes;
it is not physical mouse input into Tauri. The initial probe accidentally hit
overlapping choices and changed synthetic colors; the corrected sequence closes
each menu by an outside click before opening the next. A later probe needed to
wait for its window to become active; the completed sequence passed. Actual user
profiles were never changed. Existing VoiceOver, native-picker confirmation and
recipient-Mac acceptance limits remain separate.
