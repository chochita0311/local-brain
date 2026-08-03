# SPEC-0066: Local AI Source Identity Contract

## Metadata

- ID: `spec-0066`
- Status: `approved`
- Run ID: `run-20260802-71`
- Attempt: `1`
- Parent Feature: [feat-0066-local-ai-source-identity-contract](../feature/feat-0066-local-ai-source-identity-contract.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: Source registry identity and provider semantics
- Required Evaluators: `contract`, `functional`
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Source Set

- Human request: model personal Codex and Codex Company as independent statistics
  while reusing the Codex parser and Usage normalizer.
- Parent feature: FEAT-0066.
- Parent PRD: PRD-0012.
- Golden sources: current Source DDL/migrations, scanner, Session and Usage
  ownership, generated schema/value artifacts, and passed FEAT-0065 evidence.
- Relevant policies or contracts: Source Registry And Scans, Workspace And Session
  Activity, Usage Records, Architecture, Privacy And Data Handling, and Execution
  Loop Governance.

## Implementation Goal

- Preserve the physical `sources.kind` column as the stable source-key field and
  add one required `sources.provider_kind` field so provider-specific behavior no
  longer depends on the source key.

## In-Scope Behavior

- Fresh DDL adds bounded non-empty `provider_kind` beside unique `kind`. Its
  `unknown` database default is a compatibility fallback for direct legacy-style
  inserts; every application Source producer supplies an explicit provider kind.
  `kind` remains the physical stable source key for compatible consumers.
- Compatible startup makes a verified database backup, rebuilds only `sources`
  when required, preserves all row IDs/values and child foreign keys, and derives
  existing provider kinds from source keys (`claude`, `codex`, `context`, or the
  existing key for an unknown legacy source).
- Source upsert requires explicit source key and provider kind. Reusing a key with
  a different provider kind raises an identity conflict before label/root update.
- Scanner/session storage receives both dimensions. Search and user provenance
  store stable source key; parser, normalizer fallback, Claude parent fallback,
  and contract-staleness behavior consume provider kind.
- Query projections may retain the compatibility name `source_kind` where current
  screens expect it, but its value is the stable source key. Provider-semantic
  consumers receive an explicit `provider_kind` projection.
- Usage's Claude synthetic exclusion uses provider kind. Source selection and
  source breakdown remain source-key based.
- Existing direct test fixtures are updated to provide provider kind explicitly.
- Data Model, value dictionary, schema presentation, cleanup ledger, and current
  architecture wording describe both dimensions without introducing Codex Company
  scanning or UI early.

## Out-Of-Scope Behavior

- Renaming the physical `sources.kind` column.
- Session-source TOML, Codex Company registration/scanning, source health fields,
  or source removal/root relocation.
- Sessions tabs, provenance presentation changes, synchronization result UI, or
  Usage Dashboard controls.
- Parser, token, price, Maintenance, pin, or stale-JSONL semantic changes.

## Affected Surfaces

- `src/localbrain/schema.sql`, `db.py`, `ingest/scanner.py`
- provider-sensitive Session and Usage consumers
- Source query projections and direct fixtures
- source registry Data Model/value/schema/audit artifacts
- schema, migration, scan, Session, Usage, and regression tests

## State And Interaction Contract

- Fresh: every inserted Source has explicit stable key/provider kind.
- Compatible migration: exact retained Source and descendant identity survives.
- Repeat startup: no schema or data change.
- Identity conflict: existing key/provider mismatch raises and does not update root
  or label.
- Failure: rebuild rolls back and the verified pre-migration backup remains.
- User-visible screens: unchanged during this Foundation Feature.

## Data And Contract Assumptions

- `sources.kind` is now documented as stable source key despite its legacy
  physical name.
- `sources.provider_kind` is required, non-empty, and adapter-semantic; `unknown`
  is reserved for non-production compatibility rows and is never emitted by the
  registered-source producer.
- `sources.id` remains the only physical parent identity for Session, source-file,
  Usage, and Context descendants.
- `UNIQUE(sessions.source_id, sessions.external_id)` already supplies the required
  same-native-ID isolation.
- Current Source rows are `claude`, `codex`, and optional `context`; unknown legacy
  keys safely map their provider kind to the same value.

## Contract Surfaces

- Producer expectations: scanner upsert supplies both stable key and provider kind
  and rejects provider mutation under an occupied key.
- Consumer expectations: filters/provenance use source key; adapter semantics use
  provider kind; compatibility projections are explicit.
- Generated artifacts: Data Model value registry and Schema presentation regenerate
  from updated owner docs/schema.
- Source-of-truth owner: Source Registry And Scans Data Model plus fresh DDL and
  compatible migration implementation.
- Stale-assumption check: search runtime, tests, scripts, generated artifacts, and
  current docs for provider behavior still inferred solely from `sources.kind`.

## Required Evaluators

- Contract: exact fresh/upgraded schema, backup, retained rows/relations,
  producer/consumer dimension ownership, generated-artifact freshness.
- Design: not required; no visible surface change.
- Functional: fresh/repeat/legacy startup, current Claude/Codex/Context scans,
  identity conflict, Session/Usage behavior, and full regression suite.
- UX heuristic: not required.

## Acceptance Mapping

- Separate identity/provider → `kind` stable-key contract plus required
  `provider_kind` and explicit scanner API.
- Preserve existing data → backup-backed exact table rebuild and relation/ID tests.
- Same Codex parser, separate source ownership → scanner arguments and current
  composite Session uniqueness test with two source IDs.
- Correct consumer dimension → provider-sensitive targeted tests and stale search.
- Downstream readiness → explicit projections and updated owner/generated docs.

## Evaluation Focus

- Exact SQLite foreign-key preservation across the Source table rebuild.
- No provider mismatch silently updates an occupied source.
- No current provider-specific condition remains keyed only on source identity.
- Generated Data Model artifacts match the owner schema.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-02`: Orchestrator selected one Foundation Contract lane with Contract
  and Functional evaluation. The physical legacy `kind` name is retained as the
  stable source key to minimize compatible migration and consumer churn.
