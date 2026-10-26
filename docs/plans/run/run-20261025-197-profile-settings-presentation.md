# run-20261025-197-profile-settings-presentation

## Metadata

- Status: `passed`
- Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Active Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md#profile-settings-presentation--2026-10-25)
- Profile: `fullstack-product`; screen-alignment mode: `adapt`
- Lanes: configuration serialization; settings rows/color/reorder; shared filters; delivery
- Evaluations: Contract, Design, Functional and Interaction

## Approved Boundary And Comparison

The owner requests Session TOML field order `source_id`, `provider_kind`,
`display_label`, `root`, `color`, with optional fields afterward. Preserve array
order, numeric identities, values and source registration/reconnection rules.
All new writes, bootstrap and v1 upgrade share that serialization; existing local
settings receive a value-preserving formatting update, without a schema migration.

Remove profile-colored dots from Sessions and Session Dashboard source toggles.
Saved names/order and selected scope remain; record/detail/chart cues retain their
colors. Settings use a compact color-only tag trigger and palette, without CX/CL.

The current rendered settings list encloses every row in one rounded border and
uses divider lines; its color trigger repeats the Session badge. Adapt the light
row separation and manipulation cues of the owner's [Notion reference](https://www.notion.com/ko)
without importing its marketing shell or controls. Remove the shared frame, use
independent rows with visible drag handles and an insertion line, and retain
keyboard reorder, accessible color names/selected marks, row actions and focus.
Keep LocalBrain tokens, shell, paths, editor and first-use behavior.

## Verification And Delivery

Use synthetic rendered wide/narrow/short states and existing relevant tests.
Check no toggle dots after initial load, metadata edits and navigation; preserved
record colors; palette open/select/Escape/focus; drag/drop, cancellation and keyboard
reorder; list/filters/TOML order; failure recovery; editor/removal/wizard continuity.
Rebuild offline and verify bundle/code/assets, signatures/archive and local app/web
restart. No model download, publication, Git commit or unrelated cleanup. Existing
native-input, VoiceOver, picker/Notes and recipient-Mac acceptance limits remain.

## Results

- One serializer now orders source_id/provider_kind/display_label/root/color,
  then optional agent_home/enabled, for UI writes, bootstrap and v1 upgrades.
  Synthetic and actual-file comparisons preserve all values and array order;
  the actual formatting operation leaves source DB rows unchanged.
- Removed only the profile-colored toggle dot rule; existing neutral separators,
  names, selection and record colors remain. Settings use color-only tag controls,
  solid swatches with selected marks, unframed rows, independent handles and a
  drop insertion line. Preview does not reorder data; drop or keyboard movement
  saves through the existing revision-checked API. Cancel restores the saved view.
- All 108 relevant source/settings/onboarding/UI tests pass. Source Chromium and
  packaged WKWebView each pass 30 behavior checks and 10 geometry checks at
  1100×800, 320×720 and 700×480. Dashboard order/scope/dot checks and five source
  first-use checks pass. No full-suite rerun or new test files were needed.
- The initial browser dot assertion incorrectly counted existing neutral dividers.
  A WebKit probe also created a non-cancelable Escape event, causing an unintended
  dialog close. Corrected both probes. A trial focus-delay change was reverted;
  the final original focus implementation passes. No unresolved UI failure remains.
- Rebuilt offline with the existing lock, retained native source/notices and checked
  all 104 bundled local modules plus resource parity. Raw/compressed path checks,
  strict ad-hoc signature, ZIP CRC, internal symlinks and extracted distribution
  inventory parity pass. Final actual startup passes six WebKit/cookie checks,
  health, both routes, numeric profiles, 17 top-level served assets, unchanged
  settings values and one native/backend instance. The model worker stays idle.
- The first simultaneous app/web restart left the desktop backend unready. A
  standalone diagnostic exited cleanly after reporting readiness; restarting the
  app after the web server was ready passed. The initial cause was not captured
  by the native shell's discarded stderr; simultaneous startup is not established
  by this delivery. Both actual runtimes are now running from durable locations.
- Owner docs, generated metadata checks, JS syntax, plan catalog, whitespace and
  privacy checks pass. Task-owned test processes, copies, probes and build files
  are removed at closure. No model download, external publication or Git commit.
- [Contract](../evaluation/eval-0139-contract-standalone-test-app.md#profile-field-order-and-presentation--2026-10-25),
  [design/interaction](../evaluation/eval-0139-design-standalone-test-app.md#independent-profile-rows-and-color-tags--2026-10-25)
  and [delivery](../evaluation/eval-0139-functional-standalone-test-app.md#profile-settings-presentation-delivery--2026-10-25-superseded)
  receipts own detailed evidence and artifact identity. Broader native/recipient
  acceptance limits and Feature/PRD acceptance status remain unchanged.
