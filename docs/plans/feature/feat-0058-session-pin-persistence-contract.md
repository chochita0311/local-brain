# FEAT-0058: Session Pin Persistence Contract

## Metadata

- ID: `feat-0058`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal

- Add one durable, user-owned Session pin contract whose row presence means pinned and whose absence means unpinned, without placing mutable intent in source-derived Session rows.

## Acceptance Contract

- Fresh and compatible databases contain one `session_pins` table with:
  - `session_id` as the primary key and FK to `sessions.id`;
  - `pinned_at` as a required deterministic timestamp;
  - deletion behavior that removes the pin when its owning Session is explicitly deleted.
- The table has no `status`, `active`, or soft-delete column. A row means pinned; unpinning deletes that row.
- Pinning an already pinned Session is idempotent, does not create duplicates, and preserves the existing `pinned_at`.
- Re-pinning after unpin creates a new row and a new `pinned_at` value.
- Eligible rows are persisted, user-visible, primary work Sessions. Maintenance Sessions and Subsessions are rejected in this first contract.
- Normal Claude or Codex rescans, metadata updates, usage repair, and Session detail reads preserve the pin because they preserve the stable Session row.
- Pinning and unpinning do not write Claude JSONL, Codex JSONL, project files, Git, Local Context, or external services.
- A deterministic query can return pinned Sessions with source, title, last activity, workspace/path orientation, existence, and pin time.
- Data-model ownership, recovery, deletion, fresh-schema, and compatible-migration documents are updated in the same boundary.

## Scope Boundary

- In:
  - `session_pins` fresh-schema and compatible migration
  - row-presence state semantics
  - pin, unpin, membership, and pinned-list data operations
  - primary-work Session eligibility
  - rescan, idempotency, deletion, and recovery behavior
  - focused schema and query tests
  - Workspace and Session activity data-model documentation
- Out:
  - pin buttons, routes, panels, or visible copy
  - Subsession or Maintenance Session pinning
  - pin history, inactive rows, undo history, trash, or audit log
  - manual ordering or drag sorting
  - multi-device or cloud synchronization
  - native Claude or Codex resume metadata
  - pinning Workstreams, Documents, Items, or other entities

## Surface Lanes

- Schema lane:
  - path roots: `src/localbrain/schema.sql`, `db.py`, and migration tests
  - dependencies: stable `sessions.id` and current Session deletion contract
  - expected evidence: fresh/compatible parity, FK enforcement, row-presence semantics, and deterministic recovery ownership
  - evaluator ownership: `contract`
- Data-operation lane:
  - path roots: Session query or persistence modules and focused tests
  - dependencies: schema lane
  - expected evidence: eligibility, idempotent pin, delete-on-unpin, re-pin timestamp, list ordering inputs, and rescan preservation
  - evaluator ownership: `contract`, `functional`
- Documentation lane:
  - path roots: Data Model entrance, Workspace and Session activity subject, and FEAT-0057 dictionary references where applicable
  - dependencies: fixed schema and operation contract
  - expected evidence: source-derived versus user-owned state, deletion, backup, and recovery semantics
  - evaluator ownership: `contract`

## Contract Surfaces

- `session_pins(session_id, pinned_at)`.
- FK and delete behavior against `sessions.id`.
- Primary work Session eligibility.
- Pin, unpin, membership, and pinned-list operation behavior.
- Session rescan and explicit deletion behavior.
- Data-model and recovery ownership.

## Entry And Exit

- Entry point: a trusted local product route requests pin or unpin for one Session ID.
- Exit or transition behavior: the one pin row exists or is absent and downstream product queries receive deterministic current state.

## State Expectations

- Unpinned: no row exists.
- Pinned: exactly one row exists with `pinned_at`.
- Repeated pin: remains one row and preserves the original `pinned_at`.
- Ineligible: no row is created and a bounded validation result identifies why.
- Missing Session: no row is created.
- Deleted Session: its pin row is removed by the approved FK behavior.

## Dependencies

- PRD-0009 is `approved`.
- Current Session identity and source-ingestion behavior from PRD-0002 remain stable.
- FEAT-0059 may be planned in parallel but cannot enter product build until FEAT-0058 is `passed`.

## Likely Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/queries.py` or a bounded Session pin persistence module
- `tests/test_schema_migrations.py`
- `tests/test_session_contract.py`
- `tests/test_session_inventory.py`
- Data Model entrance and Workspace and Session activity owner docs

## Pass Or Fail Checks

- Pass if fresh and upgraded databases have the same `session_pins` contract.
- Pass if row existence alone represents state and unpin deletes the row.
- Pass if repeated pin is idempotent and re-pin after unpin creates a new current pin.
- Pass if Maintenance Sessions, Subsessions, and missing IDs cannot be pinned.
- Pass if normal source rescans preserve pins and explicit Session deletion follows documented cascade behavior.
- Pass if pinned-list data is deterministic and contains no source-content copy.
- Fail on a mutable `sessions.is_pinned` field, inactive pin rows, source-file writes, duplicate pins, or rescan loss.

## Regression Surfaces

- PRD-0002 Session identity, primary/Subsession organization, and scanning.
- Session deletion and source reconciliation.
- Fresh schema and compatible migration checks.
- Usage repair and Session detail reads.
- Data-model documentation parity and repository privacy.

## Harness Trace

- Active spec doc: [spec-0058-session-pin-persistence-contract](../spec/spec-0058-session-pin-persistence-contract.md)
- Active run: [run-20260724-61-session-pin-persistence-contract](../run/run-20260724-61-session-pin-persistence-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [eval-0058-contract-session-pin-persistence-contract](../evaluation/eval-0058-contract-session-pin-persistence-contract.md), [eval-0058-functional-session-pin-persistence-contract](../evaluation/eval-0058-functional-session-pin-persistence-contract.md)
- Latest fix note: not created

## Continuity Notes

- `2026-07-24`: initial draft fixed row presence as the pin state, delete-on-unpin behavior, and primary-work-only eligibility without a status column.
- `2026-07-24`: automatic sequential approval entered `run-20260724-61`; additive schema, local pin operations, deterministic listing, Data Model parity, and focused regressions passed.
