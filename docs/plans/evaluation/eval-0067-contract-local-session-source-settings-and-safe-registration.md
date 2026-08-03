# EVAL-0067: Local Session Source Settings And Safe Registration — Contract

## Metadata

- ID: `eval-0067-contract`
- Status: `complete`
- Evaluator Type: `contract`
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

- Evaluated private TOML ownership, bootstrap, validation vocabulary, environment
  compatibility, safe registration, and non-deletion authority.

## Checks

- A first missing load atomically creates an owner-only `schema_version = 1`
  file beside the database with ordered Claude, Codex, and Codex Company peers.
- Existing effective Claude/Codex roots seed the file once. Established TOML wins
  over later environment changes.
- A standards-compliant parser rejects duplicate TOML keys, syntax failures,
  unsupported versions, and unexpected top-level schema before database mutation.
- Entry-local unsupported providers, non-directory/unreadable roots, and duplicate
  roots remain bounded and do not block unrelated valid registration.
- Missing roots register as unavailable.
- Provider conflict, occupied-root change, and omitted entries preserve Source
  identity, descendants, and prior locators. Root change without descendants
  updates the same Source ID.
- Diagnostics contain bounded application text and local configuration identity,
  never Session content.
- The runtime file is documented as private and outside Git; Python 3.9 uses the
  locked conditional `tomli` dependency.

## Evidence

- Focused configuration suite: 8 tests passed.
- Adjacent synchronization, migration, and Usage suite: 47 tests passed.
- Full repository suite: 305 tests passed in 2.066 seconds.
- Privacy check: passed for 668 candidate files.
- `git diff --check`: passed.

## Evidence Gaps

- Tests use isolated temporary runtime directories rather than the user's real
  data directory. This is deliberate and fully covers file permissions, content,
  registration, and preservation without exposing machine-specific paths.

## Findings

- None.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-08-02`: attempt 1 passed; configuration now provides a deletion-free
  handoff contract for FEAT-0068 synchronization.
