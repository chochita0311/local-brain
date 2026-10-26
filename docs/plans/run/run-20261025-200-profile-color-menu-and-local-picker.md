# run-20261025-200-profile-color-menu-and-local-picker

## Metadata

- Status: `passed`
- Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Profile: `fullstack-product`; screen-alignment mode: `extend`
- Lanes: local picker contract/backend; settings frontend; native/browser integration; delivery/docs
- Implementation and evaluation owner: primary agent

## Approved Boundary

The owner requests a vertical color menu directly below its tag trigger, using
the same tag shape in each color, with outside-click dismissal. Keep selected
state, accessible color names, keyboard access, saved identity/color/order and
the white independent rows. Compare the current render, implement the component,
then inspect wide, narrow and short layouts plus scrolling/focus transitions.

Home, custom Session folder and Local Context Browse must open a macOS chooser
in both the app and local browser. Choose folders for Home/Session/Context roots
and a file for a Context file. Cancel preserves input; selection only fills the
draft, with existing explicit registration/reconnection authority. Guard duplicate
dialogs and stale editor writes. No upload, model download or source collection
is authorized by browsing alone.

Browser selection uses the local server and a fixed macOS chooser command, with
same-origin POST admission, strict request validation, bounded execution and a
single active chooser per backend. The app uses its native window-owned picker.
Check transport, cancellation, errors, concurrency and unsupported-platform
behavior independently of physical macOS dialog evidence. Do not infer successful
native input from a mocked bridge or generic WKWebView startup.

## Validation And Delivery

Run focused synthetic tests and rendered browser/WebKit interaction checks.
Inspect actual chooser presentation where tooling permits; state any remaining
input-evidence limit. Refresh the local app/ZIP/checksum, verify packaged/source
parity, signatures and startup, and preserve actual configuration/data. Update
owner/evaluation records and remove task-owned scratch after verification.
Broader Feature/recipient-Mac acceptance remains separate.

## Results And Evidence Limits

- Implemented the below-trigger vertical tag menu, selected check, outside-click,
  same-trigger toggle, keyboard/focus and category/anchor dismissal. White rows
  and existing ID/color/order persistence remain. Chromium and WebKit each pass
  26 interaction checks; real Chromium pointer checks additionally cover outside
  dismissal and opening/closing the same trigger. Wide/narrow/short containment
  was inspected at actual CSS viewport sizes.
- Added the local browser chooser route and fixed AppKit helper. Eight focused
  picker tests plus eight onboarding and six desktop-boundary tests pass. They
  cover origin/shape rejection, files/folders, cancellation, timeouts, errors,
  duplicate invocation and non-macOS handling. Native UI uses the installed
  window-owned dialog plugin and surfaces string-valued failures.
- Actual macOS helper probes observe both panel types visible and normal cancel
  code zero. A programmatic OK probe without a valid UI selection returned an
  abort code; the helper now reports abnormal completion as an error rather than
  cancellation. No physical file selection is claimed from that probe. UI result
  injection/native bridge stubs and actual app-button input remain distinct.
- Rebuilt the frozen backend offline, reusing the native shell. All 105 local
  modules and 69 data assets match source. Signatures, private build-path checks,
  ZIP CRC and extracted inventory match. The final bundle and actual app/web
  startup, authentication, changed assets and chooser admission pass. Three saved
  configurations remain byte-identical. App/web remain running from durable paths.
- Catalog, privacy and whitespace checks pass. Synthetic path fixtures use the
  repository's explicit placeholder convention. No model download, source
  registration, publication or commit. Task-owned probes, build and rollback
  copies are removed at closure. The physical Tauri Browse confirmation question
  is unanswered at this record; it is not counted as a pass. Recipient-Mac,
  VoiceOver and broader Feature acceptance retain their existing limits.
- [Contract](../evaluation/eval-0139-contract-standalone-test-app.md#color-menu-and-local-picker--2026-10-25),
  [design](../evaluation/eval-0139-design-standalone-test-app.md#vertical-color-menu-and-browse--2026-10-25)
  and [delivery](../evaluation/eval-0139-functional-standalone-test-app.md#color-menu-and-local-picker-delivery--2026-10-25-superseded)
  retain the scoped receipt without private runtime artifacts.
