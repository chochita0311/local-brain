# run-20261024-189-about-identity-and-version

## Metadata

- Status: `passed`
- Feature: [FEAT-0132](../feature/feat-0132-settings-and-product-navigation.md)
- Active Spec: [SPEC-0132](../spec/spec-0132-settings-and-product-navigation.md)
- Related Spec: [SPEC-0131](../spec/spec-0131-standalone-macos-runtime.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: About presentation; shared version metadata; packaged runtime
- Required evaluations: Contract, Functional, Design, Interaction

## Approved Boundary And Reference

The owner requests a concise About treatment showing v0.0.1 and supplies a
desktop About-dialog screenshot as a directional reference. Apply screen-alignment
adapt under the existing constitution: borrow icon/name/version hierarchy and
spacing, keeping the settings shell and native LocalBrain mark/type/color roles.
The screenshot remains a conversation attachment; do not persist it in the repo,
app, test fixtures or runtime sources. Its licensing text and visual assets are
not product content. No new license/copyright/build claims or copy action.

## Baseline And Contract

The rendered current pane repeats a product sentence, background/quit guidance
and update guidance. Replace those paragraphs with the existing LB mark, name and
version only. The user guide remains the owner of operational guidance. Current
version declarations disagree (Python package constant 0.1.0, distribution/app
metadata 0.2.0); align LocalBrain declarations and lock entries to 0.0.1. Render
About and the FastAPI version from the Python constant. Keep native product ID,
data directories and schemas fixed; changing app version does not migrate data.

## Verification And Delivery

Compare wide/narrow/short renders against the supplied structure and the existing
family, test tab switching/close/focus and general settings regression, inspect
Python/package/Tauri/native-plist version parity and run focused existing tests.
Rebuild the native host and frozen backend offline where caches permit, verify
raw/compressed private paths and signing/ZIP parity, replace the actual app and
verify startup while preserving saved configuration hashes. No model download,
external publication, Git commit or delegation. Remove owned scratch after use;
the user's original attachment is not task-owned scratch and stays untouched.

## Results

- About now contains the existing LB mark, LocalBrain and v0.0.1 only. Shared
  tokens and settings geometry remain. Python/FastAPI/template, project and lock
  metadata, Tauri/native plist and build receipt agree on version 0.0.1. Native
  bundle ID, local data paths, schemas and stored preferences are unchanged.
- 89 focused existing tests and offline lock consistency passed. Chromium passed
  36 checks at wide/narrow dimensions; frozen WKWebView passed 54 at wide/narrow/
  short dimensions. Identity, containment, tabs, close/focus, general controls,
  unchanged preferences and no model action passed. No full-suite rerun.
- Rebuilt the frozen backend offline and the native host against locked crates.
  Missing Rust tooling was installed only in owned scratch with no shell-profile
  changes. Public build-tool/crate downloads occurred; no model download did.
  Reused the dependency notices after proving both lock files differ only in
  LocalBrain's own version. An initial offline notice-generation attempt needed
  an uncached cross-target crate; no dependencies or notice contents were changed.
- Raw/compressed known-private-path inspection, deep strict ad-hoc signature,
  ZIP CRC, internal symlinks and independently extracted inventory parity passed.
  Actual app replacement/relaunch passed six startup/cookie WebKit checks, health,
  served/bundled asset parity and exactly one native instance. All three existing
  configuration hashes remain identical; sync remains 30 minutes and model idle.
- A narrow focus probe initially targeted a hidden entry control; rerunning with
  the supported shared settings event and visible focus anchor passed. The actual
  startup probe initially expected numeric addresses from name-resolving lsof;
  numeric output fixed detection of the already-running healthy backend. Neither
  probe failure was counted as passing product evidence.
- The [functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#about-identity-delivery--2026-10-24-superseded)
  owns artifact identity. [Design/interaction](../evaluation/eval-0139-design-standalone-test-app.md#about-identity--2026-10-24)
  and [contract](../evaluation/eval-0139-contract-standalone-test-app.md#about-and-version-contract--2026-10-24)
  evaluations are scoped passes. Broader native/recipient acceptance remains
  separate. No external publication, Git commit or copied reference image.

## Completion Checks

- Repository privacy passed for 1427 candidate files; 134 local links across ten
  touched documents, catalog freshness and whitespace checks passed. Final
  installed inventory, ZIP/checksum and bundled guide parity passed.
- Three isolated servers and the browser probe were closed. Owned scratch,
  temporary Rust/PyInstaller tooling, caches, extraction and previous-delivery
  backup were removed after process/open-file checks. An unrelated inaccessible
  system mount caused an lsof warning; it was outside the scratch filesystem and
  no open scratch entries or live fixture processes remained. Global Rust home
  directories remain absent. The user's original attachment was preserved.
- Updated app is running. Durable app, ZIP and checksum remain under `dist/`;
  no deliverable depends on temporary evidence or the reference attachment.
