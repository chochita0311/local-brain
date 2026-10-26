# run-20261018-166-local-settings-contract

## Metadata
- Status: `passed`
- Feature: [FEAT-0128](../feature/feat-0128-local-settings-contract.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Active Spec: [SPEC-0128](../spec/spec-0128-local-settings-contract.md)
- Execution Profile: `foundation-contract`
- Required evaluator: Contract

## Selected Loop
Primary agent performs orchestration, specification, contract implementation and review sequentially. No delegated workers. Contract output is the owning policy and common implementation, not a runtime success claim.

## Current Route

`passed`: [contract evaluation](../evaluation/eval-0128-contract-local-settings-contract.md).

## Evaluation Coverage

Foundation contract checks passed. Actual browser/native/runtime evidence belongs
to the [integration evaluation](../evaluation/eval-0139-functional-standalone-test-app.md).

## Owner Correction — 2026-10-19

General preferences now follow the local settings file, with defaults for missing
fields. This supersedes the original general-preference environment precedence.
FEAT/SPEC-0128, the settings policy and the contract evaluation reflect the current
rule. Implementation, shared web/app checks and delivery evidence are recorded in
[C07's Run](run-20261018-172-general-and-project-settings.md#file-owned-general-settings--2026-10-19).

## First-Startup Confirmation — 2026-10-19

The owner confirmed the lifecycle: start a fresh installation with defaults,
create its settings file automatically, then honor the saved file. Inspection
found that the shared `main.lifespan` already does this before serving requests.
The read helper remains read-only. No application behavior or binary was changed.
The settings/storage owners and README now state this lifecycle explicitly.

- Added two regression tests in `tests/test_preferences_startup.py`. Twelve
  independent process startups exercise web and desktop modes: fresh creation,
  unchanged restart, customized restart, partial file, malformed file and future
  schema. They verify schema/all defaults, 0600 file/0700 directory permissions,
  saved precedence despite conflicting retired variables, byte/mtime preservation,
  unknown fields, sync runtime values and readable errors. Both tests passed.
- All 28 existing desktop-settings tests passed; 30 relevant tests passed in total.
- Launched the current distributed frozen backend three times with isolated
  temporary data. Authenticated HTTP checks passed default-file creation before
  settings save/onboarding, empty registrations, API save, restart preservation
  of saved/unknown values, sync runtime values and malformed-file preservation.
  Existing user data and the running user app were untouched. No model download.
- Synthetic processes exited and all task-owned temporary data/logs were removed
  by their scoped cleanup. The existing app/ZIP identity is unchanged; the
  [functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#first-startup-confirmation--2026-10-19)
  records this follow-up against the current artifact.

Contract/runtime PASS for this lifecycle. No new screen, full-suite, other-Mac or
native-shell acceptance result is claimed; broader product acceptance is unchanged.

Final privacy check passed for 1414 candidate files; artifact catalog freshness,
diff whitespace and the unchanged distribution ZIP checksum passed.
