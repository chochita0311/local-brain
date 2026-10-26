# run-20261020-179-work-session-project-usage

## Metadata

- Status: `passed`
- Feature: [FEAT-0134](../feature/feat-0134-general-and-project-settings.md)
- Active Spec: [SPEC-0134](../spec/spec-0134-general-and-project-settings.md)
- Execution Profile: `fullstack-product`
- Required evaluations: Contract, Functional, Design, Interaction

## Authorized Boundary

Owner approved work-only Project usage and retaining By Project / Project names.
Primary owns backend read model, frontend copy, documentation and packaged integration;
no delegation. Existing authorization includes related tests and browser/app verification.
Screen-alignment `extend`: preserve shell, table, controls, tokens and disclosure.
Git roots and execution folders including home remain valid Project identities.

## Implementation And Verification Plan

- Filter Project membership by work class after overall/history aggregation; include
  work subsessions and exclude every Maintenance record, including assigned records.
- Preserve stored usage/attribution, overall totals/history/projection and Source/Model.
- Explain Project subset and work-specific empty state in the existing panel.
- Check full/visible parity, cost/tokens, source scopes, shares, ordering, activity,
  frozen identity, unknown work, zero/unpriced states and unchanged stored rows.
- Compare synthetic rendered baseline and updated web/frozen UI, including narrow
  containment, scope switching and only-maintenance empty state.
- Rebuild/sign/package and verify actual native startup with saved preferences intact.

## Route

Scoped correction passed. The Feature remains blocked only for separately recorded
broader native, minimum-OS and teammate-Mac distribution acceptance. This Run makes
no new completeness claim for those observations.

## Results

- Contract/Functional/Design/Interaction: scoped PASS. [Functional delivery and
  artifact identity](../evaluation/eval-0139-functional-standalone-test-app.md#work-session-project-delivery--2026-10-20-previous),
  [contract](../evaluation/eval-0139-contract-standalone-test-app.md#work-session-project-contract--2026-10-20)
  and [design/interaction](../evaluation/eval-0139-design-standalone-test-app.md#work-session-project-scope--2026-10-20)
  own detailed evidence and its limits.
- 118 related tests passed. Web at 1100/320 and the rebuilt frozen backend at
  1440/920/700/320 each passed 18 scripted checks. Captures were inspected.
- Full/visible read models agree on work-only membership and denominator. Assigned
  Maintenance is excluded too; ordinary unknown work and home/folder identity remain.
  Zero/unpriced work costs remain distinct. Overall/history/MTD/projection/freshness
  and Source/Model remain unchanged. Stored Usage rows are unchanged by reads.
- Actual running app was gracefully replaced and reopened. Authenticated health,
  updated Project HTML and matching shared/settings assets passed. Existing settings
  and source-registry hashes are unchanged; every retained usage attribution/token/
  cost/snapshot fingerprint matches the pre-replacement read-only baseline, with
  no additional observations during the comparison.
- App signature, ZIP CRC, app file bytes/modes/links and separately extracted
  inventory/signature passed. App and ZIP remain under their existing dist paths.
- Original local `.venv` lacks PyInstaller; cached `uv run --offline --no-sync --with
  pyinstaller==6.22.3` supplied the build tool without model/network downloads. The
  first copy failed on Finder metadata and was replaced by a fresh owned staging
  copy; an intervening check correctly rejected the old backend. Final frozen
  checks used verified current files. The packaging probe reads CFBundleExecutable
  instead of assuming the display name is the executable filename.
- Full-suite, optional-model, physical-input/VoiceOver, minimum-OS and other-Mac
  checks were not repeated. Earlier evidence/failures remain separately recorded.
  No Git commit, publication, Drive upload or teammate message was performed.

## Completion Checks

Privacy check passed for 1,415 candidate files; diff whitespace, schema presentation,
plan catalog freshness and changed owner-document local link targets passed.
Final installed-app deep strict signature and sibling ZIP checksum passed.
After confirming no active process used the task directory, all task-owned fixtures,
tools, snapshots, build/extraction outputs, private comparison snapshots and recovery
copies were removed. Durable outputs remain in dist; the updated app was reopened.

## Subsequent Copy Correction

The owner removed the added scope/total paragraph after this Run. [Run 180](run-20261020-180-project-copy-removal.md) records that frontend-only correction. Membership and denominator decisions remain in force; this Run's screenshots/copy evidence are historical.
