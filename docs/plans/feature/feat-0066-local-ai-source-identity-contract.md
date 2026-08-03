# FEAT-0066: Local AI Source Identity Contract

## Metadata

- ID: `feat-0066`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Goal

- Establish one stable local AI source identity independent from its parser and
  Usage-normalization provider kind, so personal Codex and Codex Company can share
  the Codex adapter without sharing statistics or normalized ownership.

## Acceptance Contract

- The Source registry owns a stable unique source key separately from provider
  kind, display label, root locator, and operational scan state.
- The initial local AI identities are `claude`/`claude`, `codex`/`codex`, and
  `codex-company`/`codex`, expressed as source-key/provider-kind pairs.
- Existing Claude, personal Codex, and Local Context registry IDs remain stable
  through compatible migration. Their source files, Sessions, Activity Events,
  Usage Records, pins, search projection, and user-curated relationships are not
  deleted, duplicated, or renumbered.
- Session and Usage ownership continues to use `sources.id`; native Session IDs
  are unique only within that source parent, so the same Codex external ID can
  coexist under personal and company sources.
- Parser, Usage normalizer, Maintenance child handling, and other
  provider-semantic consumers use provider kind. Filtering, provenance,
  source-attributed statistics, and direct-link scope use stable source key.
- Display-label changes do not change source identity. Reusing an existing source
  key with another provider kind is an identity conflict.
- Existing current screens remain behaviorally compatible until their dependent
  Product Features consume the new source-key projections.

## Scope Boundary

- In:
  - fresh Source registry identity shape and compatible schema migration
  - stable migration mapping for existing `claude`, `codex`, and `context` rows
  - explicit provider-kind ownership for parser- and normalization-dependent code
  - source-key projections for downstream filtering, provenance, and Usage work
  - source-scoped Session, parent, source-file, Usage, and stale-reconciliation
    invariants
  - current Data Model, value dictionary, schema presentation, and privacy-safe
    synthetic migration evidence
- Out:
  - the local Session source settings file
  - adding or scanning the Codex Company root
  - synchronization result UI, source tabs, or Usage controls
  - source removal, disabling, purge, archive, root relocation, or restore
  - changes to `context_roots.enabled` or
    `external_source_instances.enabled`

## Contract Surfaces

- `sources` fresh and compatible schema
- Source registry insert, update, and lookup interfaces
- `sessions.source_id`, `source_files.source_id`, and
  `usage_records.source_id` ownership
- provider-semantic parser, Usage, Maintenance, Runner, and Workstream consumers
- source-identity query, search, provenance, and filter projections
- Data Model owner and derived value/schema/audit artifacts

## Required Evaluators

- `contract`: identity/provider separation, migration parity, immutable-key rules,
  descendant preservation, and producer/consumer ownership.
- `functional`: fresh startup, compatible repeat startup, current Claude/Codex and
  Context scans, same-native-ID isolation, and existing route/query regressions.

## User-Visible Outcome

- None required in this Foundation Feature. Existing Claude and Codex labels and
  behavior remain unchanged while downstream work gains distinct source identity.

## Entry And Exit

- Entry point: application startup or an existing source registry upsert on a
  fresh or compatible database.
- Exit or transition behavior: downstream settings and synchronization Specs can
  register multiple instances of one provider without redefining identity.

## State Expectations

- Default: each retained registry row has one stable source key and one provider
  kind.
- Migration: existing IDs and all descendants remain attached to the same row.
- Conflict: an existing key cannot silently change provider kind.
- Error: migration failure rolls back without partial identity or descendant
  changes.
- Success: current consumers use the correct identity or provider dimension and
  no stale `sources.kind` assumption remains where the distinction matters.

## Dependencies

- PRD-0012 is `approved`.
- [FEAT-0065](feat-0065-session-source-enabled-field-removal.md) is `passed`.

## Likely Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/ingest/scanner.py`
- `src/localbrain/usage.py`
- Session, Usage, activity, retrieval, pin, Workstream, Runner, and source
  inventory query modules
- source registry and schema/value documentation and generated artifacts
- schema migration, ingestion, query, usage, and regression tests

## Pass Or Fail Checks

- Pass if fresh and upgraded databases expose separate stable source-key and
  provider-kind values without changing any retained Source ID or descendant.
- Pass if personal and company Codex identities can own the same native external
  Session ID without collision while both dispatch to the Codex provider adapter.
- Pass if parser- and Maintenance-specific behavior follows provider kind while
  provenance and selection follow source key.
- Pass if existing Claude, personal Codex, Context, Session, Usage, pin, search,
  Workstream, Thread, checkpoint, and route tests remain compatible.
- Pass if a stale-assumption search and generated-artifact checks find no consumer
  that still conflates source identity and provider behavior.
- Fail on Source ID churn, descendant loss, global external-ID uniqueness,
  Context/external enablement changes, or visible Product behavior added early.

## Regression Surfaces

- Claude and personal Codex ingestion and parent reconciliation
- Local Context scanning and source ownership
- Maintenance Session classification and Runner source selection
- Session pin, search, retrieval, Workstream, Thread, and checkpoint relations
- Usage attribution, price snapshots, and dashboard query compatibility
- schema generation, startup migration, and repository privacy

## Harness Trace

- Active spec doc: [spec-0066-local-ai-source-identity-contract](../spec/spec-0066-local-ai-source-identity-contract.md)
- Active run: [run-20260802-71-local-ai-source-identity-contract](../run/run-20260802-71-local-ai-source-identity-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [contract](../evaluation/eval-0066-contract-local-ai-source-identity-contract.md), [functional](../evaluation/eval-0066-functional-local-ai-source-identity-contract.md)
- Latest fix note: none

## Continuity Notes

- `2026-08-02`: proposed after FEAT-0065 passed. Kept settings-file lifecycle and
  user-visible synchronization outside this loop so the registry migration has
  one contract outcome.
- `2026-08-02`: human owner approved this Feature boundary and sequential
  execution before Spec generation.
- `2026-08-02`: RUN-20260802-71 entered the Foundation Contract execution loop.
- `2026-08-02`: attempt 1 passed Contract and Functional evaluation with 297
  repository tests and privacy validation.
