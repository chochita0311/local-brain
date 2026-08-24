# Session Sync Repair Performance Wrap-Up

## Log Type

- Type: `Wrap-Up`
- Date: `2026-08-24`
- Related track:
  [REFACTOR-0001](../refactor-0001-session-sync-repair-performance.md)
- Scope: split repair lanes, request-local caches, batched writes, progress
  feedback, documentation, and validation

## Summary

- Goal:
  - Reduce version-triggered Session synchronization work without changing
    native input authority, normalized identities, retained state, or source
    failure isolation.
- Outcome:
  - `Pass`
- Short conclusion:
  - Session projection, Usage normalization, and generalized references now
    repair independently. A profiled combined repair on a private local database
    copy completed in `15.982s`, compared with the pinned-baseline profile of
    `33.876s`, while processing five more current Codex files.

## What Changed

- Added:
  - nullable `source_files.session_contract_version` with compatible additive
    migration and a compatible current-parser backfill
  - one synchronization-local Context-document path/workspace/name lookup
  - one source-local Usage pricing/calculator cache
  - bounded progress events and additive `POST /api/sessions/sync/stream`
  - repair-lane, cache, progress, stream, migration, and UI-contract tests
- Updated:
  - Session scanning to select Session, Usage, reference, and Atlassian-evidence
    writes independently while retaining all-lane writes for native file changes
  - Usage and Session-reference inserts to use `executemany` inside their
    existing savepoints
  - the existing Sessions result region to show source, repair reason, and
    processed/total counts
  - executable schema owners, generated schema presentation, cleanup audit,
    README, Product, Architecture, and data-model policies
  - one pre-existing Confluence content-contract test to use its execution time
    instead of a fixed freshness date that had aged past the 30-day interval
- Moved/Renamed:
  - None
- Removed:
  - temporary `219 MB` runtime-database profile copy and temporary synthetic
    browser runtime after validation

## Behavior / Parity Notes

- Behavior-preserving intent:
  - Candidate discovery, source ordering, parser inputs, Session/Event/Usage and
    evidence identities, stale-file authority, aggregate reports, JSON API,
    no-script redirect, per-source transactions, and repair rollback retain the
    pinned baseline contract.
- Intentional deltas:
  - Concern-only repair no longer rewrites an unrelated derived lane.
  - One nullable Session freshness column and one additive progress endpoint are
    exposed.
  - Enhanced Sessions feedback shows bounded live progress.
- Important compatibility or contract notes:
  - A null Session version is backfilled without repair only when the current
    Usage version proves that the same parser generation was already applied.
    Unknown or mismatched versions still repair safely.
  - A Session classification/parser contract change also refreshes reference
    eligibility; a Usage-only or reference-only mismatch does not rewrite
    Session/Event/search/Usage lanes it does not own.
- Parity claim status:
  - `Preserved`
- Parity confidence basis:
  - `Strict audit complete`, with the approved additive endpoint/UI and
    concern-only write reductions treated as intentional deltas.
- If `Preserved`, strict baseline audit completed:
  - `Yes`; the additive endpoint/UI and concern-only write reductions remain
    separately identified as intentional deltas.

## Validation

- Baseline or compare target:
  - repository state before the refactor track
- Baseline resolved commit SHA:
  - `7caa1d67f4b67c642b84bd6cb616246e3ab3597f`
- Build / compile:
  - command: `PYTHONPYCACHEPREFIX=/tmp/localbrain-sync-pyc .venv/bin/python -m compileall -q src tests`
  - result: pass
  - command: `node --check src/localbrain/static/app.js`
  - result: pass
- Targeted tests:
  - command: `.venv/bin/python -m unittest tests.test_session_sync tests.test_usage_contract tests.test_session_references tests.test_session_reference_schema tests.test_ui_contract -v`
  - result: `87` tests passed
  - command: `.venv/bin/python -m unittest tests.test_schema_cleanup_audit tests.test_schema_presentation tests.test_data_model_docs -v`
  - result: `18` tests passed
- Full tests:
  - command: `.venv/bin/python -m unittest discover -s tests`
  - result: `371` tests passed
- Schema and privacy:
  - `PRAGMA integrity_check` returned `ok`; `foreign_key_check` returned zero rows
  - Data Model, generated Schema Presentation, and the `577`-object cleanup
    audit are current
  - `./scripts/check-repo-privacy.sh` passed for `753` candidate files
- Runtime / smoke / manual verification:
  - private runtime database and source configuration were copied to `/tmp`;
    the original database was never opened for writes
  - compatibility scan: `0.956s`, `3,694` profiled SQLite calls
  - Usage-only Codex repair: `12.583s`, `5,269` SQLite calls, `388` files
  - combined Session/Usage/reference Codex repair: `15.982s`, `15,205`
    SQLite calls, `388` files
  - pinned-baseline combined repair: `33.876s`, approximately `130,000`
    SQLite calls, `383` files
  - candidate combined elapsed time was approximately `52.8%` lower despite
    five additional current files
  - a synthetic local server and isolated Chrome session exercised 800 Codex
    files at `1440x841` and Chrome's minimum resizable `500x841` viewport
  - the existing button action used the streamed endpoint, showed Usage contract
    repair progress from `0/800` through `800/800`, showed the success result,
    and reloaded `/sessions`; the reloaded button returned to its idle enabled
    state
  - neither viewport introduced document-level horizontal overflow, and Chrome
    reported no console warning or error
  - a synthetic configuration-error retry preserved all 800 Sessions, restored
    the button and focus with an alert result, and completed successfully after
    restoring the temporary configuration

## Risks / Limitations

- Known residual risks:
  - The producer must bump every affected concern version when one parser change
    changes multiple derived lanes.
  - The stream cannot change HTTP status after emitting bytes, so an unexpected
    terminal failure is represented as a bounded NDJSON error event.
- What this log does not prove:
  - It does not promise the same wall-clock time for future source sizes or
    storage hardware.

## Next Action

- Next step:
  - Merge or commit the reviewed implementation when the owner is ready.
- Handoff note:
  - The implementation, automated validation, private-copy profiling, and
    rendered browser interaction checks are complete.
