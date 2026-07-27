# SPEC-0058: Session Pin Persistence Contract

## Metadata

- ID: `spec-0058`
- Status: `approved`
- Run ID: `run-20260724-61`
- Attempt: `1`
- Parent Feature: [feat-0058-session-pin-persistence-contract](../feature/feat-0058-session-pin-persistence-contract.md)
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lanes: additive schema → pin operations → migration/recovery docs → parity
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-24`
- Updated: `2026-07-27`

## Source Set

- Human approval on `2026-07-24`: approve and execute both PRDs' Features automatically and sequentially.
- PRD-0009 and FEAT-0058 row-presence direction.
- Current stable `sessions.id`, source-upsert behavior, Data Model ownership, Schema Presentation, and cleanup audit baseline.

## Schema Contract

```sql
CREATE TABLE session_pins (
    session_id INTEGER PRIMARY KEY
        REFERENCES sessions(id) ON DELETE CASCADE,
    pinned_at TEXT NOT NULL
);
```

- A row means pinned; no row means unpinned.
- No status, active, deleted, or history field exists.
- Fresh DDL owns the table. Existing databases receive it when startup reapplies the idempotent schema before compatible migrations.
- `session_id` admits at most one current pin and cascades only when the owning Session is deleted.
- `pinned_at` is the first time of the current pin interval.

## Operation Contract

- `pin_session`:
  - accepts only persisted `work` plus `primary` Sessions;
  - returns `session-not-found`, `maintenance-session-ineligible`, or `subsession-ineligible` without inserting;
  - uses conflict-ignore semantics so repeated pin preserves the original timestamp.
- `unpin_session` deletes only the pin row and reports whether one existed.
- `is_session_pinned` performs one local membership query.
- `list_pinned_sessions`:
  - accepts limits from 1 through 100;
  - returns Session ID/title/activity, source kind/name, cwd/source path, workspace name/path/existence, and pin time;
  - orders by displayed activity (`COALESCE(last_event_at, started_at) DESC`) with `pinned_at DESC, sessions.id DESC` tie-breaks;
  - filters defensively to primary work Sessions.
- Operations mutate SQLite only. They do not commit implicitly or touch native sources, files, Git, Context, models, MCP, or external services.

## Lifecycle And Recovery

- Stable Session updates preserve the child pin row.
- Explicit unpin plus re-pin creates a new current interval and timestamp.
- Session/source deletion cascades the pin because the target can no longer be reopened.
- A source rescan can rebuild the Session but cannot rebuild pin intent. Full recovery requires the LocalBrain database backup.
- `pinned_at` stays under the repository's existing deferred canonical timestamp audit; this Feature does not rewrite timestamps.

## Documentation And Generated Artifacts

- Add `session_pins` to the Workspace and Session activity owner and both ERDs.
- Increase the effective baseline to 35 ordinary tables, 40 physical FKs, 36 presentation objects, and 383 presentation columns.
- Regenerate Schema Presentation and refresh the complete cleanup audit ledger.
- Add row-presence/timestamp to the value-dictionary exclusion ledger because it is not an enum family.

## Verification

```bash
uv run python -m unittest tests.test_session_pins tests.test_schema_migrations tests.test_session_contract tests.test_session_inventory tests.test_ingest_policy tests.test_schema_presentation tests.test_schema_cleanup_audit tests.test_data_model_docs tests.test_value_registry
uv run python scripts/build-data-model-value-dictionaries.py check
uv run python scripts/check-data-model-docs.py
uv run python scripts/build-schema-presentation.py check
uv run python scripts/check-schema-cleanup-audit.py --check
node scripts/check-data-model-mermaid.mjs
```

## Open Blockers

- None. FEAT-0059 may consume this contract.
