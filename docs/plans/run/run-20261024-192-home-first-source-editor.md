# run-20261024-192-home-first-source-editor

## Metadata

- Status: `passed`
- Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Related Feature: [FEAT-0140](../feature/feat-0140-periodic-local-session-sync.md)
- Active Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md#home-first-editor--2026-10-24)
- Execution Profile: `frontend-product`
- Surface Lanes: source editor and wizard; source-path payload; Sync geometry; packaged UI
- Required evaluations: Contract, Functional, Design, Interaction

## Approved Boundary

The owner approves the previously proposed home-first Session source form and
requests a much narrower Sync selector. Use screen-alignment extend within the
current settings shell. Primary owns the bounded implementation and evaluation.
Existing test and local-app replacement authorization applies.

## Contract And Acceptance

- Basic registration accepts tool, name and agent home. Derive `sessions` for
  Codex or `projects` for Claude, and submit that explicit root through the existing
  API. Advanced record-location override supports relocated/copied transcripts.
  Home selection never authorizes scanning credentials or the entire home.
- Existing roots remain authoritative: infer a display home from a conventional
  root when absent; disclose and retain nonstandard roots, including home-less
  registrations. Opening, canceling or tab changes must not persist anything.
  Changing homes updates the derived path, while an explicit override stays fixed.
  Reconnection confirmation and backend identity/overlap validation remain intact.
- Keep provider/source identity fixed for Edit, draft reset on category exit,
  wizard Back retention, Next-save and Skip-without-save, error retention and locks.
  Replace redundant folder explanations with a concise derived-path readout.
- Sync remains 10/20/30/60/Off with immediate atomic saves. Size controls to the
  selection, disclosure and selected marker; preserve readable legacy values,
  below-trigger menus, focus and responsive containment.
- No backend/schema/default/collection/usage change, model download or publication.

## Verification And Delivery

Inspect rendered baseline and final wide/narrow/short views. Exercise real synthetic
registration for both tools, custom/legacy roots, defaults, reconnection, errors,
pickers, wizard and tab transitions; verify compact Sync geometry and saving.
Run focused existing checks. Update/re-sign bundled UI, verify archive/extraction
and actual startup with saved configuration hashes preserved. Remove owned scratch.

## Results

- Implemented home-first input with provider-derived record roots and an advanced
  override/default-reset action. Preserved legacy/custom/home-less targets, source
  identity, reconnection, validation, draft reset and wizard save/skip behavior.
  Sync now fits its content, about 79px at the default scale, with longer legacy
  labels allowed to expand. Backend/storage/collection and usage rules are unchanged.
- 97 focused tests and JS syntax passed. Chromium/source and WKWebView/frozen each
  passed 156 checks for source registration, geometry/Sync at three sizes and wizard
  behavior. Additional Chromium legacy-1440 display and idle-model checks passed.
  Picker bridge tests are stubbed; physical native picker/permission tests were not
  run. One wizard probe needed to await Edit's busy state before clicking Next;
  corrected checks passed without an application change.
- Three UI assets updated; frozen/native code, dependency locks and notices retained.
  Changed-text private-path checks, strict ad-hoc signatures, ZIP CRC, internal
  symlinks and independently extracted inventory parity passed. Run 190 owns the
  unchanged runtime's raw/compressed private-path checks.
- Actual app replacement/relaunch passed six WebKit startup/cookie checks, health,
  asset parity and one app/backend instance. Three configuration hashes are
  identical and model activity is idle. No download, publication, commit or delegation.
- [Functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#home-first-source-delivery--2026-10-24-superseded)
  owns exact delivery identity. [Design/interaction](../evaluation/eval-0139-design-standalone-test-app.md#home-first-source-editor--2026-10-24)
  and [contract](../evaluation/eval-0139-contract-standalone-test-app.md#home-first-source-payload--2026-10-24)
  are scoped passes; broader native/accessibility/recipient acceptance is unchanged.

## Completion Checks

- Final installed inventory, ZIP/checksum and three configuration hashes match the
  receipt. The updated app remains running with the original registered paths.
- Local link checks passed for 1168 links across 12 affected documents. Catalog
  freshness and whitespace checks passed; privacy passed for 1433 candidate files.
- Both synthetic backends stopped and the last browser tab was reset to blank.
  Owned fixtures, probes, compiler cache, staged/extracted apps and previous-delivery
  backup were removed after checking stopped processes and no open files. The
  inaccessible system-mount warning was outside the owned scratch tree. No durable
  output depends on temporary paths.
