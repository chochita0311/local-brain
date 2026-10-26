# run-20261023-187-settings-control-consistency

## Metadata

- Status: `passed`
- Feature: [FEAT-0134](../feature/feat-0134-general-and-project-settings.md)
- Active Spec: [SPEC-0134](../spec/spec-0134-general-and-project-settings.md)
- Related Specs: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md), [SPEC-0140](../spec/spec-0140-periodic-local-session-sync.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: preference contract/backend; shared settings controls and general/source/context/model/storage panes; web/WKWebView integration and packaged delivery
- Required evaluations: Contract, Functional, Design, Interaction

## Approved Boundary

The owner requests compact, consistent controls and typography across settings,
startup options in sidebar order, removal of the redundant timezone sentence,
an editable synchronization interval with an off action, below-trigger source-tool
selection, centered Cancel and a profile list when returning from another category.
Use `screen-alignment` extend under the existing constitution. Keep the approved
source overview, dialog shell, explicit model/download and recovery authority.
The primary owns implementation and evaluation; existing test/app authorization
applies. No delegation, external publication, model download or user-data mutation.

## Consistency And Behavior Contract

- Desktop controls use the shared 32px height; narrow controls retain 40px targets.
  General dropdowns cap at 240px with matching menus below the trigger. Source tool
  and name align in equal columns; button labels center. Shared typography and
  grouped rows replace large repeated context/storage boxes.
- Startup order: Sessions Dashboard, Sessions, Local Context. The saved/default
  Sessions choice remains independent of order. Keep timezone impact help but
  remove the owner-selected sentence.
- Sync accepts integer minutes from 10 through 1440; the existing minimum avoids
  frequent scans and the upper bound is one day. Preserve existing saved values
  and the previously approved fresh-install default of 10 minutes. Commit valid
  input on change/Enter, preserve the saved interval when off, and retain revision
  checks, autosave/readback and completion-based scheduling in web and app.
- Regular settings category departure discards the unsaved source editor and
  returns to its overview. This supersedes Run 186 for category navigation only;
  wizard Back still preserves drafts. Pending source writes lock category changes.
- Context registration, model actions, backup/restore confirmation and cache
  ownership stay explicit. Progressive disclosure preserves operative information.

## Rendered Baseline And Verification Plan

Synthetic Chromium baseline confirms 320×40px general selectors, native tool popup,
40px editor fields, and Cancel without centered flex justification. Verify the
revised shared controls, keyboard menus, source draft lifecycle, valid/invalid
custom intervals, off/on and reload persistence, error/readback behavior, all
settings panes and onboarding at wide/narrow/short sizes in Chromium and WebKit.
Run focused contract tests, rebuild the frozen backend, verify packaged assets,
archive/signature/privacy and actual app startup with saved files preserved.
Remove task-owned temporary artifacts after validation and replacement.

## Results

- Shared desktop controls now use 32px height and 240px general dropdown width;
  narrow controls use 40px. Startup options follow sidebar order, timezone copy
  is shortened, and sync uses direct minutes plus Off/On. Saved 30-minute values
  and the previously approved fresh-install default of 10 minutes are preserved.
- Tool/name controls align, dropdowns open below the trigger and Cancel centers.
  Leaving the source category clears its draft; wizard Back retains it. Context,
  model and storage use common typography, action sizing and compact groups.
  Disclosures retain model-storage and restore information and confirmation.
- 129 focused tests and JavaScript syntax passed. Chromium settings checks passed
  76, source/frozen WebKit checks 114 each, frozen wizard checks 21 and Chromium
  wizard checks seven. Six short-pane menu geometry checks and actual keyboard
  fill/Enter persistence passed. An initial automation selection shortcut failed
  to replace text, causing expected range rejection; corrected input passed.
- Rebuilt the frozen backend offline, reused/re-signed the native host and
  verified private paths, ZIP CRC, extracted inventory, signature and internal
  symlink targets. Actual replacement/relaunch passed six WebKit startup checks,
  authenticated health, served asset parity and one native-instance checks.
  All three user configuration-file hashes remain identical, saved sync is 30,
  onboarding remains complete and no model worker is running. No download,
  external publication or Git commit occurred.
- [Functional artifact](../evaluation/eval-0139-functional-standalone-test-app.md#compact-settings-delivery--2026-10-23-superseded),
  [design/interaction](../evaluation/eval-0139-design-standalone-test-app.md#compact-shared-settings--2026-10-23)
  and [contract](../evaluation/eval-0139-contract-standalone-test-app.md#editable-sync-interval--2026-10-23)
  evaluations record scoped passes. Existing full-product/native/recipient-Mac
  acceptance gaps remain; broader Feature states were not promoted.

## Completion Checks

- Repository privacy passed (1425 candidate files); 263 local links across 15
  documents, artifact catalog freshness and diff whitespace checks passed.
  The link checker initially omitted explicit HTML anchors; checking those
  anchors confirmed the existing backlink was valid.
- All three temporary servers stopped. One initial shutdown wait expired;
  subsequent exact-PID checks confirmed termination before cleanup. No open
  scratch files remained. Task-owned fixtures, probes, build staging, extracted
  archive and previous-delivery backup were removed.
- Durable app/ZIP/checksum remain under `dist/`; the revised app is running.
