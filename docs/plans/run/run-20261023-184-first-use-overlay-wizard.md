# run-20261023-184-first-use-overlay-wizard

## Metadata

- Status: `passed`
- Feature: [FEAT-0137](../feature/feat-0137-first-run-local-setup.md)
- Active Spec: [SPEC-0137](../spec/spec-0137-first-run-local-setup.md#first-use-overlay-wizard--2026-10-23)
- Execution Profile: `fullstack-product`
- Surface Lanes: backend entry, shared settings interaction, packaged delivery
- Required evaluations: Contract, Functional, Design, Interaction

## Approved Boundary

The owner requested removal of the two inactive Project settings from their local
file and a conventional first-use wizard over the main application window.
Existing implementation and related test/browser/app verification authorization
applies. Primary owns orchestration, specification, implementation and evaluation;
screen-alignment `extend`, no delegation. Broader recipient-Mac acceptance remains
separate from this bounded correction.

The local preference cleanup removes only the two retired keys and preserves the
owner's incomplete-onboarding flag and every other value. No generic migration
or unrelated user-data cleanup is introduced.

## Consistency And Interaction Plan

- Replace the standalone card grid with a compact modal above the actual saved
  startup surface. Use the existing dialog, typography, spacing, surfaces and
  control family; isolate background pointer/keyboard interaction.
- Present Welcome, Session sources, Local Context and Search as sequential steps.
  Keep progress and Previous/Next/Skip actions stable outside the scroll pane.
- Reuse the settings forms and their existing owners; allow empty/skipped steps.
  Next saves a pending source/path before advancing; validation/API failure stays
  on that step with entered values. Back preserves drafts. Explicit skip does not
  register a draft or install a model.
- Completion or an explicit Later action records completion with revision checks
  and returns to the chosen startup screen. Closing the app before completion
  preserves incomplete state; registered sources remain saved. Model installation
  requires its existing explicit action and is mocked/offline in this evaluation.
- Regular settings retain their categories, compact geometry and general autosave.

## Verification Plan

Capture the old frozen onboarding and settings family with synthetic data before
editing. Verify web and frozen runtime at wide/narrow widths, all steps, keyboard,
modal isolation, pending-form saves, skip/back, errors, completion/relaunch and
existing settings regressions. Update the app/ZIP/checksum; re-open the real app
without completing the owner's onboarding or starting a download. Record the
native/backend/browser scope separately and remove owned temporary evidence.

## Results

- Removed only the owner's inactive `project_display` and `projects` fields;
  preserved the manually false completion flag and all other values. Existing
  compatibility handling of old fields for other installations is unchanged.
- Replaced the standalone cards with the shared four-step modal above the saved
  startup surface. Next validates/saves pending source/document inputs, Back
  preserves drafts and Skip leaves them unregistered. Failure remains in place;
  explicit completion/Later persists through the revision-checked settings API.
- 119 focused tests and JavaScript syntax passed. Three original frozen views
  passed 18 baseline checks; fourteen source/frozen layout cases passed 224
  checks; eighteen behavioral cases passed 194 checks (four ordinary-web cases
  used the source server). Tests use synthetic paths and offline/mocked model
  requests. Two fresh final-backend processes preserve incomplete/completed
  state and saved registrations and passed twelve startup checks in total.
- Rebuilt the backend offline, reused the native shell, re-signed and replaced
  app/ZIP/checksum. The actual app is running with the new wizard. Six read-only
  startup checks, health, source/asset parity and unchanged hashes for three
  saved files passed; onboarding was false at replacement and model installation
  was idle. A later final check observed only completion changing to true; the
  intervening action was not observed and this newer value was preserved.
- Scoped [functional delivery](../evaluation/eval-0139-functional-standalone-test-app.md#first-use-overlay-wizard-delivery--2026-10-23-superseded-artifact),
  [design/interaction](../evaluation/eval-0139-design-standalone-test-app.md#first-use-overlay-wizard--2026-10-23)
  and [contract](../evaluation/eval-0139-contract-standalone-test-app.md#first-use-overlay-wizard-contract--2026-10-23)
  evaluations passed. Broader standalone/native/recipient acceptance remains
  separate; no full-suite rerun, model download or external publication.

## Completion Checks

- Repository privacy check passed for 1422 candidate files; `git diff --check`
  passed. Checked 227 local links/anchors across twelve changed documents.
- Final installed inventory/checksum, deep strict signature and source/guide
  parity passed. Both session/search configuration files and all general values
  except the later completion transition remain unchanged; one native app is
  running. Retired keys remain absent.
- Removed all task-owned probes, synthetic data, captures, build/cache/staging
  outputs and previous-delivery recovery copies after confirming no open files.
  App, ZIP and checksum remain in `dist/`; no temporary dependency remains.
