# FEAT-0067: Local Session Source Settings And Safe Registration

## Metadata

- ID: `feat-0067`
- Status: `passed`
- Type: `foundation`
- Surface: `infra`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Goal

- Make one private TOML file beside the LocalBrain database the authoritative
  local AI Session-source list, with compatible bootstrap and validation rules
  that cannot turn a configuration mistake into Session deletion.

## Acceptance Contract

- The canonical settings locator is
  `<LOCALBRAIN_DATA_DIR>/session-sources.toml`; the default resolves to
  `~/Library/Application Support/LocalBrain/session-sources.toml` beside
  `localbrain.db` and remains outside the repository.
- The versioned TOML contract contains `schema_version = 1` and one
  `[[session_sources]]` entry per source. Each entry owns `source_key`,
  `display_label`, `provider_kind`, and `root`.
- The initial file contains explicit peer entries for Claude, personal Codex, and
  Codex Company. No one of those roots remains an implicit registration outside
  the file after compatible bootstrap.
- When the file is first absent, LocalBrain creates it atomically. Existing
  effective `LOCALBRAIN_CLAUDE_ROOT` and `LOCALBRAIN_CODEX_ROOT` values seed their
  entries during that one compatibility bootstrap; Codex Company receives
  `~/.codex-company/sessions`. Once the file exists, the dedicated Claude/Codex
  root variables no longer override it. `LOCALBRAIN_DATA_DIR` continues to locate
  both database and settings.
- Parsing and identity validation finish before any registry mutation or stale
  reconciliation. Whole-file syntax or schema failure starts no Session-source
  scan and retains the last accepted registry and all normalized data.
- Entry-local validation produces bounded diagnostics. A missing, non-directory,
  unreadable, duplicate, or unsupported-provider root entry cannot delete prior
  data or prevent independently valid entries from being represented.
- Removing an accepted entry from the file is not a source deletion command. The
  prior registry row and normalized data remain visible and included in aggregate
  reads with a configuration-error state; no scan runs for that entry.
- Changing provider kind under an accepted source key is an identity conflict.
  Changing the root of an accepted source that already owns normalized data is a
  non-destructive root-change conflict in this Feature; explicit relocation or
  destructive source removal remains separate future work.
- A valid new entry may be registered even when its root is currently absent; it
  becomes unavailable rather than disabled and owns no deletion authority until
  its accepted root is present and successfully scanned.
- The settings file stores no credentials, account identifiers, Session content,
  or repository-tracked machine paths.

## Scope Boundary

- In:
  - versioned TOML shape, loader, validation, bounded diagnostics, and atomic
    bootstrap
  - one-time compatibility import from the two current dedicated root variables
  - explicit Claude, Codex, and Codex Company entries
  - registration reconciliation against FEAT-0066 stable source identity
  - missing-entry, duplicate-root, provider-conflict, and root-change safeguards
  - last-accepted registration preservation under invalid configuration
  - synthetic configuration and privacy tests and owner documentation
- Out:
  - in-app source registration or enable/disable controls
  - source deletion, data purge, root-relocation confirmation, archive, or restore
  - scanning Codex Company JSONL or displaying synchronization results
  - Sessions tabs, source provenance UI, or Usage source controls
  - credentials, native account discovery, or authentication inspection

## Contract Surfaces

- `<LOCALBRAIN_DATA_DIR>/session-sources.toml`
- runtime settings loader and compatibility bootstrap
- source-entry value shape and validation result vocabulary
- accepted Source registry reconciliation and identity-conflict behavior
- dedicated Session-root environment-variable compatibility boundary
- non-destructive configuration failure and deletion-authority boundary

## Required Evaluators

- `contract`: file ownership and shape, single-source-of-truth behavior,
  compatibility migration, validation vocabulary, and non-destructive conflicts.
- `functional`: first bootstrap, repeated startup, custom data directory, valid and
  malformed files, duplicate/missing roots, omitted entries, root changes, and
  preservation of existing data.

## User-Visible Outcome

- None required as a screen change. A local owner can inspect and edit one private
  file, while later Product Features can expose its bounded status safely.

## Entry And Exit

- Entry point: application startup or Session-source synchronization requests the
  local Session-source registry.
- Exit or transition behavior: downstream synchronization receives either a
  validated source list with per-entry status or a bounded whole-file error; it
  never receives ambiguous deletion authority.

## State Expectations

- Missing before first bootstrap: create the explicit three-entry file atomically.
- Valid: return ordered validated entries and reconcile presentation safely.
- New root unavailable: retain the registration with unavailable state and no
  imported descendants.
- Malformed whole file: keep last-accepted registry and data; return one actionable
  error with safe file and line context when available.
- Invalid entry: identify the entry when possible, preserve its prior accepted
  state, and allow unrelated valid entries to proceed later.
- Removed entry or changed occupied root: report configuration conflict, keep data,
  and grant no stale-input deletion authority.

## Dependencies

- [FEAT-0066](feat-0066-local-ai-source-identity-contract.md) must be `passed`
  before build.

## Likely Affected Surfaces

- `src/localbrain/config.py`
- a bounded local Session-source settings and validation module
- Source registry reconciliation services
- startup and Session-scan entry points
- README setup and runtime configuration documentation
- privacy, source registry, and architecture owner docs
- configuration, bootstrap, migration, and failure-preservation tests

## Pass Or Fail Checks

- Pass if a fresh or existing runtime produces one explicit private three-entry
  TOML file beside its database without committing a machine path.
- Pass if one-time root-variable migration preserves current custom Claude and
  personal Codex locators and subsequent variable changes cannot override the
  existing file.
- Pass if syntax, schema, duplicate-key, duplicate-root, unsupported-provider,
  missing-root, unreadable-root, omitted-entry, and occupied-root-change cases
  return deterministic bounded states.
- Pass if none of those error cases deletes or rewrites Source IDs, Sessions,
  Usage Records, pins, links, source-file evidence, or search projection.
- Pass if valid entry ordering remains deterministic for downstream controls.
- Fail on silent fallback after a malformed established file, partial bootstrap,
  implicit source registration outside the file, or configuration-driven purge.

## Regression Surfaces

- custom `LOCALBRAIN_DATA_DIR` runtimes
- existing Claude and personal Codex custom-root installations
- Local Context and MCP settings that remain outside this file
- startup database migration and repeated initialization
- source-mirror JSONL deletion under an unchanged accepted root
- tracked-artifact and private-runtime-data boundaries

## Harness Trace

- Active spec doc: [spec-0067-local-session-source-settings-and-safe-registration](../spec/spec-0067-local-session-source-settings-and-safe-registration.md)
- Active run: [run-20260802-72-local-session-source-settings-and-safe-registration](../run/run-20260802-72-local-session-source-settings-and-safe-registration.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [contract](../evaluation/eval-0067-contract-local-session-source-settings-and-safe-registration.md), [functional](../evaluation/eval-0067-functional-local-session-source-settings-and-safe-registration.md)
- Latest fix note: none

## Continuity Notes

- `2026-08-02`: proposed after the owner selected the database directory for the
  private file and confirmed that malformed configuration or path mistakes must
  not authorize normalized-data deletion.
- `2026-08-02`: human owner approved this Feature boundary and its dependency on
  passed FEAT-0066.
- `2026-08-02`: RUN-20260802-72 entered the Foundation Contract execution loop.
- `2026-08-02`: attempt 1 passed Contract and Functional evaluation with 305
  repository tests and privacy validation.
