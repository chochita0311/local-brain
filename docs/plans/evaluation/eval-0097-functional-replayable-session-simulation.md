# EVAL-0097: Replayable Session Simulation — Functional

## Metadata

- ID: `eval-0097-functional`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-113](../run/run-20260923-113-full-history-simulation-replay.md)
- Attempt: `2`
- Feature: [FEAT-0097](../feature/feat-0097-replayable-session-simulation.md)
- Spec: [SPEC-0097](../spec/spec-0097-replayable-session-simulation.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, `infra`
- Created: `2026-09-22`

## Verified Behavior

- Full input beyond prior caps, exact character coverage and token-tail coverage.
- Unchanged replay performs no encoding and retains identical grouping/config.
- Changed source text re-encodes only affected input; title/role changes also
  invalidate affected model inputs. Deleted or reclassified input is removed.
- Interrupted batches retain committed vectors; restart encodes only misses.
- Grouping-only settings reuse vectors. Model changes cannot mix namespaces.
- Explicit force recomputation and corrupt-vector repair work.
- Source changes during inference block publication and preserve prior output.
- Empty/excluded/orphan Sessions remain accounted for; source bytes do not change.
- Owned output, single writer, expiry/purge, fixed-code CLI and stale/abandoned
  status handling pass. Actual graph construction is deterministic on the
  synthetic two-topic example and exposes affinity-only authority.
- Existing local model encodes synthetic Korean/English input with valid vectors.
- Real input preparation and model batches ran. A deliberate real SIGINT and
  restart preserved/reused cached vectors and subsequently committed new batches.

## Commands And Coverage

- `python -B -m unittest discover -s tests -p 'test_session_simulation.py' -q`:
  20 tests pass in the semantic runtime; the ordinary app runtime skips the one
  optional graph test.
- `.venv/bin/python -B -m unittest discover -s tests -q`: 685 tests, OK with that
  one optional skip. The generated schema-audit ledger was refreshed after the
  initial stale-generated-file failure, and the full suite then passed.
- Privacy scanner and generated catalog/audit checks pass; no visible UI changed
  and no browser-verification claim is made.

## Earlier Evidence Gap — RUN-103

The full private embedding/grouping backfill is still active. Observe completed
publication, unchanged real-data replay and a grouping-only variant before
closing the Run. The existing sampled Auto Work screen is not this simulation's
result viewer. No semantic-quality, map usability or production-replacement
claim follows from these technical checks.

## Current Result — RUN-113

All real technical replay checks now pass: zero encoding on unchanged and
grouping-only runs, identical unchanged grouping, identical restored default
grouping, and byte-identical source DB/WAL. An initial inner-community mismatch
was fixed by canonical graph insertion, not by weakening acceptance. Cross-process
hash-seed and nonfinite-distance regressions pass. Full manifest verification is
unchanged by bounded read-ahead (observed 53.536 → 2.362 seconds).
All 23 focused semantic-runtime tests and 945 application tests pass (three
optional skips in the latter); privacy scan passes. UI and meaningful work
organization remain separate downstream acceptance boundaries.
