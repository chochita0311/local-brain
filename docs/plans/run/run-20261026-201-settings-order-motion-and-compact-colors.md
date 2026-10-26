# run-20261026-201-settings-order-motion-and-compact-colors

## Metadata

- Status: `passed`
- Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Profile: `frontend-product`; screen-alignment mode: `adapt`
- Lanes: shared ordering interaction; compact color menu; browser/WebKit evaluation; asset delivery
- Owner: primary agent

## Approved Correction

The owner reports that the left handles in Session-source and Local Context
settings do not visibly move rows. Replace handle-only native dragging with a
whole-row pointer preview, a visible insertion position, animated neighboring
rows and edge scrolling in the settings pane. Follow the handle/guide interaction
in the [official Notion example](https://www.notion.com/help/columns-headings-and-dividers)
and [editing guide](https://www.notion.com/help/writing-and-editing-basics), while
retaining LocalBrain's white rows, typography, tokens, actions and data ownership.
Keyboard movement remains available and reduced-motion preference suppresses
decorative transitions. Only a completed changed order saves; cancel, interruption,
outside drop and clicks must not write. Preserve revision checks, readback, error
recovery, numeric IDs and current filters.

The color menu keeps vertical choices below its trigger but uses horizontal tag
glyphs, no inter-choice gap and minimal padding. Use a compact 24px fine-pointer
choice height and 32px width; coarse pointers retain larger targets. Keep color
names, selected check, keyboard focus and light dismissal.

## Evaluation Boundary

Compare the rendered baseline with the official reference and revised settings.
Check pointer motion, release, cancellation, edge scroll, keyboard movement,
reduced motion, persistence and failure for both lists. Keep synthetic fixtures
isolated. Validate palette geometry and all choices in wide/narrow/short windows.
Refresh app assets/ZIP/signature/checksum and run startup checks without rebuilding
unchanged backend/native code. Preserve actual settings/data. No model downloads,
publication or unrelated changes; prior native-picker acceptance limits remain.

## Results And Limits

- Shared pointer ordering now lifts the whole row, previews its destination,
  animates neighboring rows and scrolls near pane edges. Changed release saves
  once; click/cancel/interruption/outside release write nothing. Keyboard movement,
  focus, reduced motion, revision/readback and failed-readback restoration remain.
- Horizontal color tags occupy a zero-padding/gap vertical menu, normally 34×146px.
  Fine-pointer choices are 32×24px; coarse pointers retain 40px minimum targets.
  A WebKit grid-height difference found during evaluation is fixed with intrinsic
  height and start alignment, keeping the menu content-sized in both engines.
- Real Chromium pointer drags pass for both lists. Chromium and WKWebView each
  pass 39 scripted checks; the pointer-sequence capture shim is not physical
  native-input evidence. Wide/narrow/short, coarse-pointer and reduced-motion
  checks pass. The 17 profile and 36 desktop-settings/Context-root tests pass;
  the initial module-import invocation was corrected to test discovery.
- Updated only the existing bundle's settings JS/CSS and signature. No backend or
  native rebuild and no dependency/model download. All 69 packaged data assets
  match source; private-path inspection, deep signatures, ZIP CRC and extracted
  inventory match. The archive reader was reused from the existing package cache
  after its absence in the normal development environment was detected.
- Actual app/web serve the revised assets and pass health/settings/Sessions plus
  six WKWebView startup/cookie checks. Simultaneous app/web launch initially left
  the app backend unavailable; relaunch after web readiness recovered it. The
  exact initial cause was not captured by the native shell, so no root-cause fix
  or simultaneous-start acceptance is claimed. Three settings files remain
  byte-identical; one native host/backend and the web server remain running.
- [Design](../evaluation/eval-0139-design-standalone-test-app.md#visible-order-movement-and-compact-colors--2026-10-26),
  [contract](../evaluation/eval-0139-contract-standalone-test-app.md#order-preview-and-persistence--2026-10-26)
  and [delivery](../evaluation/eval-0139-functional-standalone-test-app.md#order-motion-and-compact-colors-delivery--2026-10-26-superseded)
  retain the scoped evidence. Physical Tauri pointer/chooser input, VoiceOver and
  recipient-Mac/broader Feature acceptance remain separate. The prior picker
  question remains unanswered. No commit or publication. Task-owned preview,
  probe, stage/extraction and rollback files are removed at closure.
