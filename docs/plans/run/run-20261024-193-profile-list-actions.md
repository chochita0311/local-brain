# run-20261024-193-profile-list-actions

## Metadata

- Status: `passed`
- Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Active Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md#profile-list-actions--2026-10-24)
- Execution Profile: `frontend-product`
- Surface Lanes: profile labels/required markers; list actions/confirmation; editor navigation; packaged UI
- Required evaluations: Contract, Functional, Design, Interaction

## Approved Boundary

The owner requests English Tool/Profile name/Home labels, clearer Session-folder
wording, red required markers, padded Edit/Unregister actions on each profile row,
a confirmation modal for unregistering, and a return to the list when the active
Session sources category is clicked. Use screen-alignment extend within the
existing settings family. Primary owns implementation/evaluation; prior test and
local-app replacement authorization applies.

## Contract And Acceptance

- Use Tool, Profile name, Home, Custom session folder and Session folder. Retain
  the explicit text required marker and actual input validation; Home is required
  only without a custom root. Mark required text using the shared danger tone.
- Registered rows show separate Edit/Unregister controls with normal padding;
  retained unregistered rows offer re-registration, not a redundant removal.
  Move removal out of the editor. Keep readable paths and responsive actions.
- Show the profile name and consequences before any removal request. Cancel is
  initially focused; Cancel/Escape write nothing and restore row focus. Only the
  confirm action submits the captured source identity and revision. Prevent repeat
  submission/dismissal while saving, keep errors in the modal, confirm ambiguous
  outcomes against the registry, and require fresh review after revision conflict.
  Originals and imported records remain governed by the unchanged removal API.
- Clicking Session sources during Add/Edit discards the draft and shows its list,
  including when that category is already selected. Wizard Back still preserves
  drafts, Next saves, Skip does not register. Home/root and Sync behavior remain.
- No backend/schema/usage changes, model downloads or external publication.

## Verification And Delivery

Inspect rendered before/after lists, forms and confirmation at wide/narrow/short
sizes. Use synthetic sources for cancel/Escape, safe focus, confirm, repeat input,
errors, conflicts, lost responses, retained data and wizard continuity. Run focused
checks. Replace signed app/ZIP UI assets, verify actual startup/config preservation
and package identity, then remove owned temporary state.

## Results

- Implemented English labels, truthful red required markers, padded list actions,
  a profile-specific confirmation and same-category draft cancellation. Existing
  Home/root derivation, source identity and backend removal semantics remain.
- 97 focused tests and JS syntax passed. Chromium/source and WKWebView/frozen each
  passed 95 action, failure, geometry/focus and wizard assertions. Chromium also
  checked Enter/Escape input. Native WebView exposed a parent-focus leak; explicit
  inertness fixed it, then all native checks and 53 Chromium layout/focus checks
  passed. This is a product fix, not a weakened focus assertion.
- Synthetic removals preserved imported session/event/source-file rows, identity,
  paths and original files. Initial retention queries were corrected to use
  activity_events and TOML registration state, not nonexistent DB fields/tables.
- Three UI assets updated and the app re-signed; runtime code, dependency locks
  and notices retained. ZIP CRC, signatures, symlinks, extracted inventory and
  changed-text private-path checks passed. Actual replacement/relaunch passed
  six startup checks, health, asset parity and one app/backend instance. Three
  saved configuration hashes are identical; model worker remains idle.
- [Functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#profile-list-actions-delivery--2026-10-24-superseded)
  owns exact artifact identity. [Design/interaction](../evaluation/eval-0139-design-standalone-test-app.md#profile-list-actions--2026-10-24)
  and [contract](../evaluation/eval-0139-contract-standalone-test-app.md#profile-removal-confirmation--2026-10-24)
  are scoped passes. Wider native/accessibility/recipient acceptance is unchanged.
- No model download, external publication, Git commit or delegation.

## Completion Checks

- Final installed inventory, ZIP/checksum and three saved configuration hashes
  match the receipt. The updated app remains running.
- 1124 local links across ten affected documents, catalog freshness and whitespace
  checks passed. Repository privacy passed for 1434 candidate files.
- Closed the task's browser page and stopped both synthetic backends/launchers.
  Removed owned fixtures, probes, compiler cache, extracted/staged apps and the
  previous-delivery backup after checking no active users or open files. The known
  inaccessible system-mount warning was outside the owned tree. Durable outputs
  and evidence do not depend on temporary paths.
