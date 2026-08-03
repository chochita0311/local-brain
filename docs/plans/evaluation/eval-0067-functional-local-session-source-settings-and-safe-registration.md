# EVAL-0067: Local Session Source Settings And Safe Registration — Functional

## Metadata

- ID: `eval-0067-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260802-72`
- Attempt: `1`
- Feature: [feat-0067-local-session-source-settings-and-safe-registration](../feature/feat-0067-local-session-source-settings-and-safe-registration.md)
- Spec: [spec-0067-local-session-source-settings-and-safe-registration](../spec/spec-0067-local-session-source-settings-and-safe-registration.md)
- Execution Profile: `foundation-contract`
- Surface Lane: private Session-source configuration and safe registry reconciliation
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Scope

- Verified first and repeat loading, custom data directory behavior, validation
  states, startup composition, and retained database data under mistakes.

## Checks

- Bootstrap is deterministic, leaves no temporary file, and applies mode `0600`.
- Repeat loading preserves established bytes and roots.
- Malformed files and duplicate source keys yield no registrations or mutations.
- Independently valid entries register when peers are invalid; absent roots have
  an explicit unavailable result.
- Same-key provider changes and occupied root changes retain names, roots, IDs,
  Sessions, and all descendant ownership.
- Omitted Source entries return `config_missing` while remaining in aggregate
  data ownership.
- Application lifespan loads and reconciles the settings after database
  initialization without starting a source scan.

## Evidence

- Focused tests: 8 passed.
- Full suite: 305 passed in 2.066 seconds.
- Existing Starlette template deprecation warning remains unrelated and
  non-blocking.

## Evidence Gaps

- No browser evaluation was required because this Feature intentionally exposes
  no new screen or interaction.

## Findings

- None.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-08-02`: functional evaluation passed attempt 1; scanner dispatch and
  visible source health remain isolated to FEAT-0068.
