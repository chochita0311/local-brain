# SPEC-0035: Maintenance Session Usage Bridge

## Metadata

- ID: `spec-0035`
- Status: `approved`
- Run ID: `run-20260719-40`
- Attempt: `1`
- Parent Feature: [feat-0035-maintenance-session-usage-bridge](../feature/feat-0035-maintenance-session-usage-bridge.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lanes: schema and migration → Runner producer → consumers → docs and generated artifacts
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Implementation Goal

- Establish one enforced Run-to-Maintenance-Session identity and turn the existing private Runner stream into idempotent, priced Usage Records without making maintenance activity eligible for ordinary work consumers.

## Schema And Migration Contract

1. Fresh DDL adds the two-value CHECKs to `sessions.session_class` and `sessions.index_policy`.
2. `maintenance_run_id` becomes `TEXT UNIQUE REFERENCES maintenance_runs(id) ON DELETE SET NULL` with a table CHECK requiring linked rows to be `maintenance`, `primary`, and `metadata_only`.
3. Startup detects the exact contract from `sqlite_master`. If missing on a file database, it creates and validates a non-overwriting `-pre-maintenance-session-contract-v1.bak` before structural mutation.
4. Preflight rejects unknown/null classification values, unknown/null index policies, duplicate non-null Run IDs, orphan Run IDs, link-shape mismatches, or an unexpected Session column name/type/null/default/key contract. Physical column-order differences created by older additive migrations are accepted.
5. Compatible rebuild uses foreign keys disabled only around one explicit transaction, copies exact ordered Session rows by canonical column name, preserves column metadata, converges physical column order, recreates indexes, reenables foreign keys, and requires `foreign_key_check` plus row equality before success.
6. Repeated startup is a no-op and preserves the first valid backup.

## Producer Contract

- `prepare_run` inserts the ledger row before inserting the linked Session, within the caller's database transaction.
- The Session uses the Claude source identity, deterministic external identity `localbrain-run:<run-id>`, the Run stream path, `session_class=maintenance`, `session_role=primary`, `index_policy=metadata_only`, and the Run ID.
- The producer keeps `--no-session-persistence`; `stream.jsonl` is the only Session/Usage source for an in-app Run and remains an operational artifact for the Run Console.
- Assistant `message.usage` records reuse the canonical Claude normalizer. Duplicate message identities reconcile deterministically.
- Result `modelUsage` or result `usage` is accepted only when no assistant usage record exists. Malformed or unsupported components remain explicit partial/malformed capability evidence rather than zero.
- A missing source timestamp uses the locally observed terminal time and records that fallback in capability metadata.
- Reconciliation stores pricing and attribution through `store_usage_records`, removes obsolete records only within the owning Maintenance Session, and updates Session start/end/last-activity metadata without creating Activity Events or search rows.
- Every terminal state synchronizes available usage. Startup interruption recovery and eligible historical stream-backed Runs use the same idempotent producer.

## Consumer Contract

- Manual marker ingestion retains maintenance classification. It links the Session only when the referenced Run row exists; an unregistered marker remains maintenance with a null physical Run relation.
- Reusing one registered marker for a second Session fails the unique relation rather than selecting or deleting a Session.
- Claude/Codex stale-source deletion and source-level Usage Record repair exclude Sessions with a non-null `maintenance_run_id`.
- Retrieval and manifest consumers continue to admit only primary work Sessions.
- Usage Dashboard rows include every direct non-synthetic Usage Record and count Sessions only when class is work and role is primary; no visible UI change is introduced.

## Backfill Contract

- Startup considers only `maintenance_runs` rows with both `task_type` and `stream_path`.
- It creates or reconciles one Session per eligible Run and parses an existing stream when readable.
- Prepared marker rows without an in-app task/stream remain ledger-only.
- Missing stream files produce a metadata-only Session for a genuine in-app Run but no invented Usage Record.

## Contract Surfaces

- Source of truth: `schema.sql` plus `db.py` compatible repair.
- Producer: `maintenance_usage.py`, Claude stream parser, and `runner.py` lifecycle.
- Consumers: scanner preservation, retrieval/manifest exclusion, Usage Dashboard aggregation.
- Generated output: `schema-presentation.json` derived from fresh and compatible in-memory schema plus Data Model semantics.
- Stale-assumption check: every reference describing `maintenance_run_id` as non-FK or Runner executions as Session-less must be removed from current owner docs.

## Evaluation Focus

- Exact child-row preservation across the parent Session rebuild.
- No backup overwrite, no mutation on invalid preflight, idempotent startup.
- One Run/one Session and no assistant/result double count.
- Failed, cancelled, interrupted, historical, missing-stream, malformed-stream, marker-only, and duplicate-marker states.
- Ordinary scanner repair preservation and Dashboard totals versus Session denominator.

## Open Blockers

- None. The current local database preflight has 171 work/full Sessions, zero linked Sessions, zero orphan/duplicate/mismatched links, six Run rows, and two completed stream-backed in-app Runs.

## Continuity Notes

- `2026-07-19`: Orchestrator selected `foundation-contract` with Contract and Functional evaluation; no frontend/design lane is required.
