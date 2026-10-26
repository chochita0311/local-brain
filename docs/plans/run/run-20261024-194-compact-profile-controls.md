# run-20261024-194-compact-profile-controls

## Metadata

- Status: `passed`
- Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Active Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md#compact-profile-controls--2026-10-24)
- Execution Profile: `frontend-product`
- Surface Lanes: source-row controls; provider-dependent name placeholder; label/order inspection; packaged UI
- Required evaluations: Design, Functional, Interaction

## Approved Boundary

The owner requests smaller Edit/Unregister buttons and a Profile name placeholder
matching Codex or Claude Code. Retain Tool to distinguish the provider application
from sessions/agents. Explain current label propagation, ordering and persisted
source identity from implementation evidence; no new ordering contract is requested.
Use screen-alignment extend under the existing settings family.

## Acceptance And Verification

- Reduce row-button visual width/type using existing spacing/type roles; preserve
  desktop/narrow minimum heights, confirmation, focus and separate action targets.
- Empty Profile name hints follow the selected provider. Never overwrite entered
  or saved names; preserve required validation, draft detection and wizard behavior.
- Verify source labels reach both filter surfaces after loading the page, source
  IDs/providers remain stable, and reordering TOML does not change DB-ID ordering.
  Use synthetic fixtures for mutations, with read-only inspection of local metadata.
- Inspect baseline/final wide/narrow renders and browser interaction, then bundled
  WebView and startup. Preserve configuration and update signed local app/ZIP.
  No backend/schema change, model download, external publication or Git commit.

## Results

- Reduced row typography from 13px to 12px and inline padding from 16px to 8px,
  retaining shared 32/40px heights. Desktop Edit/Unregister widths are about 39/63px
  versus 56/82px before. Codex/Claude Code placeholders follow the selected provider;
  typed/saved names and validation remain unchanged.
- 91 focused tests and JS syntax passed. Chromium/source and WKWebView/frozen each
  passed 83 assertions at wide/narrow/short sizes. Real synthetic rename saves
  propagate to both filters on load, preserve identity/provider/root and keep DB-ID
  order even with reversed TOML. Source metadata/history inspection explains the
  existing provider/key/display-name separation without mutating private data.
- Three UI assets replaced; locks, notices and runtime code unchanged. Signature,
  archive CRC/extraction/inventory, private-path text checks and six actual startup
  checks passed. Three saved configuration hashes preserved; one app/backend runs.
- [Functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#compact-profile-controls-delivery--2026-10-24-superseded)
  owns package identity. [Design/interaction](../evaluation/eval-0139-design-standalone-test-app.md#compact-profile-controls--2026-10-24)
  is a scoped pass. No backend/schema changes, model download, publication, commit
  or delegation. Wider native/accessibility/recipient acceptance is unchanged.

## Completion Checks

- Installed app inventory and ZIP/checksum match the receipt; final saved
  configuration hashes are preserved and the updated app remains running.
- 1113 local links across eight affected documents, catalog freshness and whitespace
  checks passed. Repository privacy passed for 1435 candidate files.
- Closed the task browser page, stopped both synthetic backends/launchers and
  removed owned fixtures, probes, compiler cache, staged/extracted copies and old
  delivery backup after checking no active use/open files. The known inaccessible
  system mount warning was outside the owned tree. No durable output depends on
  removed temporary paths.
