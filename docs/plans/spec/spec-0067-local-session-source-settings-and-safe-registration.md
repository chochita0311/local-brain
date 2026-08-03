# SPEC-0067: Local Session Source Settings And Safe Registration

## Metadata

- ID: `spec-0067`
- Status: `approved`
- Run ID: `run-20260802-72`
- Attempt: `1`
- Parent Feature: [feat-0067-local-session-source-settings-and-safe-registration](../feature/feat-0067-local-session-source-settings-and-safe-registration.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Surface: `infra`
- Execution Profile: `foundation-contract`
- Surface Lane: private Session-source configuration and safe registry reconciliation
- Required Evaluators: `contract`, `functional`
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Source Set

- Human decisions: keep every local AI Session source in one personal settings
  file beside the database; configuration mistakes must never delete retained
  normalized data.
- Parent Feature FEAT-0067 and PRD-0012.
- Golden sources: FEAT-0066 Source identity contract, current Settings loader,
  Source registry/scanner entry points, README configuration, and privacy policy.

## Implementation Goal

- Add a deterministic private TOML loader and safe registry reconciliation service
  that supplies explicit Claude, personal Codex, and Codex Company registrations
  without granting scan or deletion authority.

## In-Scope Behavior

- `Settings.session_sources_path` resolves to
  `<data_dir>/session-sources.toml`; callers may override it only for isolated
  tests or embedding.
- On the first missing-file load, write `schema_version = 1` and ordered entries
  `claude`, `codex`, `codex-company` atomically with mode `0600`. The first two
  roots use the already resolved compatibility environment values; the third is
  `~/.codex-company/sessions`.
- Established files are parsed with a standards-compliant TOML parser. They must
  contain exactly one supported schema version and a list of tables with
  `source_key`, `display_label`, `provider_kind`, and `root` strings.
- Source keys are bounded lowercase slug identities. Labels and roots are bounded
  non-empty strings. Providers are currently `claude` and `codex`.
- Paths expand `~` and become absolute normalized locators. Missing paths are
  valid registrations with `unavailable` status; existing non-directory or
  unreadable paths are entry-local errors.
- Duplicate source keys are a whole-list identity error. Duplicate normalized
  roots mark every colliding entry invalid so no ambiguous owner is registered.
- Whole-file syntax, top-level schema, or duplicate-key failure returns one
  bounded file error and performs no registry mutation.
- Reconciliation starts only after parsing and identity validation. Valid new
  entries upsert their stable key/provider/label/root even when unavailable.
- Existing key/provider mismatch and occupied root changes are conflicts and do
  not update the row. Root changes are allowed only while the Source owns no
  source files, Sessions, Usage Records, or Context Documents.
- An established Source omitted from the file remains registered and receives a
  `config_missing` result. No Source or descendant deletion occurs.
- Entry order is preserved in the returned contract. Diagnostics contain a stable
  code, bounded human message, optional source key, and settings path, but never
  Session content.
- This Feature exposes configuration and reconciliation services; scanner
  dispatch consumes them in FEAT-0068.

## Out-Of-Scope Behavior

- Scanning the configured entries, reconciling missing JSONL, or changing current
  sync route responses.
- In-app editing, enable/disable, source deletion, purge, root relocation with
  data, archive, or restore.
- Sessions or Usage source controls and provenance presentation.
- Inspecting credentials, Codex accounts, or native authentication state.

## Affected Surfaces

- `src/localbrain/config.py`
- new private Session-source settings module
- Source registry reconciliation service
- runtime dependency/packaging files for TOML on supported Python versions
- README, architecture, privacy/configuration owner docs
- isolated bootstrap, validation, conflict, and retention tests

## State And Interaction Contract

- `bootstrapped`: file written atomically and parsed into three ordered entries.
- `ready`: established file valid; each entry reports `ready` or `unavailable`.
- `entry_error`: valid file but one or more entries are not registrable; unrelated
  valid entries remain eligible for safe registration.
- `file_error`: no entries accepted and no registry mutation.
- `config_missing`: retained registry entry absent from the file; data remains.
- `identity_conflict` or `root_change_conflict`: retained row remains unchanged.

## Data And Contract Assumptions

- The private TOML is user-managed configuration and is not a database backup.
- `sources.id` and descendants remain database authority after initial
  registration; omission is not deletion intent.
- `source_files` or any normalized descendant makes a root occupied.
- File replacement uses a sibling temporary file, flush/fsync, permission set,
  and `os.replace`; an incomplete write cannot become the canonical file.

## Contract Surfaces

- Producer: `load_session_source_settings(Settings)` owns bootstrap, parse,
  validation, status, and diagnostics.
- Consumer: `reconcile_session_source_settings(connection, result)` owns only
  safe registry inserts/presentation updates and conflict reporting.
- Environment boundary: dedicated Claude/Codex variables seed a missing file
  once; existing TOML wins on every later load.
- Privacy boundary: only labels, adapter kinds, and local paths are persisted;
  the file stays under the runtime data directory and outside Git.

## Acceptance Mapping

- One consistent source file → explicit three-entry bootstrap and established-file
  authority.
- Safe mistakes → parse-before-mutation, per-entry outcomes, no implicit delete.
- Existing custom roots → one-time environment seed test.
- Future provider instances → ordered list, stable keys, provider dispatch field.
- Root/provider conflicts → occupied-descendant and immutable-provider tests.

## Evaluation Focus

- Atomic file creation, byte-deterministic repeat load, and mode `0600`.
- Python 3.9+ TOML dependency behavior and duplicate-key rejection.
- No database change on file-level error; no retained-data change for omission or
  conflict.
- Exact status ordering and bounded, content-free diagnostics.
- No tracked machine-specific settings artifact.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-02`: Orchestrator retained the Foundation Contract profile and one
  configuration/registration lane. Scanning and visible health remain FEAT-0068.
