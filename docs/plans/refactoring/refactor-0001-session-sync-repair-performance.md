# REFACTOR-0001: Session Sync Repair Performance

## Purpose

Reduce Session synchronization time when a derived-data contract changes while
preserving the current source mirror, normalized data, failure isolation, and
public synchronization contracts. Add bounded live progress through the existing
Sessions feedback surface so an intentional repair does not appear stalled.

## Refactor Type

- Primary type: `Behavioral`
- Supporting type: `Structural`
- Parity target: `Behavior-preserving` for synchronization inputs, persisted
  results, transactions, existing routes, reports, errors, and no-script flow.
- Intentional delta: one additive progress-stream route and live progress copy in
  the existing Sessions result region.
- Compare baseline: repository `HEAD` before this track.
- Baseline pin: `7caa1d67f4b67c642b84bd6cb616246e3ab3597f`.
- Execution profile: `fullstack-product`.
- Surface lanes: data/backend -> API/integration -> frontend -> docs.
- Screen-alignment mode: `extend`.

## Scope

1. Separate Session projection, Usage normalization, and Session-reference
   freshness so one changed contract repairs only its owning derived lane.
2. Preserve compatible databases without forcing an additional full repair when
   their current Usage version already proves the corresponding Session parser
   contract was applied.
3. Reuse one immutable Context-document lookup during a synchronization instead
   of resolving every Markdown candidate against a fresh document query and path
   normalization pass.
4. Batch safe derived-row writes and cache immutable pricing lookups without
   changing row values, order, identity, or rollback behavior.
5. Expose bounded per-source repair reason and file progress through an additive
   stream while retaining the existing JSON and no-script endpoints unchanged.

## Non-Goals

- Changing which native files are Session candidates or when disappeared files
  authorize normalized deletion.
- Changing Claude or Codex parsing, token calculations, price values, Session
  classification rules, reference eligibility, evidence limits, or source health
  vocabulary.
- Repricing historical Usage Records outside the already approved corrective
  normalizer contract.
- Parallel SQLite writers, background durable jobs, cancellation, scheduler
  state, cloud synchronization, or external transmission.
- New visual components, layouts, colors, motion, or a redesign of Sessions.

## Invariants

- Functional: the same source roots and native JSONL produce the same Sessions,
  Activity Events, Usage Records, search rows, evidence rows, parent relations,
  health report, aggregate outcome, and stale-file deletion result as the
  baseline.
- API: `POST /api/sessions/sync`, `POST /sessions/sync`, and `POST /api/scan`
  keep their current request and response behavior.
- Runtime: each registered Session source retains its own SQLite transaction;
  one source failure cannot roll back a completed peer source.
- Failure: a repair failure rolls back every change for that source, retains the
  prior derived record set, records bounded health, and does not advance the
  failed contract version.
- Data: stable source, Session, event, Usage, evidence, pin, Workstream, Thread,
  and checkpoint identities remain unchanged.
- Privacy: progress contains only configured display label, stable source key,
  bounded repair kind, counts, and status; it contains no source path or content.
- UI: one `동기화` action retains disabled/busy/focus/retry behavior, the current
  result family, complete-result reload, partial/failure inspection, and no-script
  fallback.

## Planned Work

### Step 1 - Split Contract Freshness And Repair Lanes

Goal:
- Track Session projection freshness independently and apply Usage-only or
  Reference-only repairs without replacing unrelated derived lanes.

Why this grouping:
- Version selection and write ownership must be established before optimizing
  the work within each lane.

Guardrails:
- Natural file changes still refresh every derived lane.
- Unknown legacy versions still fail safe by reparsing rather than being assumed
  current.
- Source-level Usage union reconciliation and repair rollback remain unchanged.

Targets:
- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/ingest/claude.py`
- `src/localbrain/ingest/codex.py`
- `src/localbrain/ingest/scanner.py`
- schema and synchronization tests

Validation:
- Fresh and compatible schema tests.
- Usage-only, Reference-only, Session-only, combined, failed, repeated, and
  active-file repair tests.
- Before/after row projections for Sessions, events, Usage, search, and evidence.

Exit gate:
- Each contract mismatch touches only its owning lane and every baseline failure
  and transaction post-condition remains covered.

### Step 2 - Reuse Lookups And Batch Safe Writes

Goal:
- Remove repeated Context-document scans and reduce SQLite call volume without
  changing resolution or persistence semantics.

Why this grouping:
- These are local implementation optimizations after repair ownership is fixed.

Guardrails:
- Candidate order, ambiguity handling, target limits, evidence keys, first/last
  observation timestamps, pricing snapshots, and attribution snapshots remain
  equivalent.
- Caches live only for one synchronization and contain no durable private data.

Targets:
- `src/localbrain/session_references.py`
- `src/localbrain/usage.py`
- `src/localbrain/ingest/scanner.py`
- reference, Usage, and synchronization tests

Validation:
- Cached versus uncached resolution comparison for absolute, relative,
  workspace-name, ambiguous, missing, and disabled-root cases.
- Row-by-row Usage and reference-evidence comparison.
- Synthetic full-repair profiling against the pinned baseline.

Exit gate:
- Results are equivalent and measured full-repair time and database call volume
  are materially lower on the same synthetic fixture.

### Step 3 - Add Native Progress Feedback

Goal:
- Report repair reason and per-source processed/total counts while a long repair
  is running.

Why this grouping:
- Progress consumes the now-explicit repair plan but does not own synchronization
  semantics.

Guardrails:
- The existing JSON API and no-script POST remain unchanged.
- Progress callback failures never affect scanner success or rollback.
- Client disconnect does not create a partial commit boundary.
- Existing result markup and style family are reused with no layout redesign.

Targets:
- `src/localbrain/ingest/scanner.py`
- `src/localbrain/main.py`
- `src/localbrain/static/app.js`
- API, UI-contract, functional, browser, and interaction tests

Validation:
- Ordered start/plan/progress/source-result/final event coverage.
- Existing JSON response and redirect regression tests.
- Complete, partial, failed, repeat, no-stream fallback, focus, and reload checks.
- Rendered Sessions verification at wide and narrow widths.

Exit gate:
- Long repair progress is legible and bounded while every pre-existing action and
  outcome remains functional.

### Step 4 - Close Parity And Performance Evidence

Goal:
- Decide whether the track is parity-safe and materially faster against the
  immutable baseline.

Why this grouping:
- Tests alone do not prove persistence, side-effect, failure, or performance
  equivalence.

Guardrails:
- No success claim before exact diff, source mapping, query/write/output,
  side-effect, and failure-mode audit is complete.
- Private runtime content stays out of tracked artifacts.

Targets:
- focused and full test suites
- repository privacy check
- temporary synthetic or private local profiling copy
- refactor log and merge-check record

Validation:
- Static syntax/startup, targeted tests, full suite, privacy, SQLite integrity,
  repeat synchronization, rendered route, and browser interaction checks.
- Baseline and candidate full-repair profiles on equivalent inputs.

Exit gate:
- Required checks pass, temporary evidence is removed, and the merge check either
  records strict parity or identifies the exact remaining blocker.

## Validation Gates

- Build or static validation:
  - `.venv/bin/python -m compileall -q src tests`
  - `node --check src/localbrain/static/app.js`
- Tests:
  - focused Session sync, Usage, reference, schema, route, and UI-contract tests
  - `.venv/bin/python -m unittest discover -s tests -v`
- Runtime:
  - temporary-database repeated and forced repair scans
  - SQLite `integrity_check`
  - local server and Sessions browser workflow
- Privacy:
  - `./scripts/check-repo-privacy.sh`
- Parity audit coverage:
  - immutable baseline pinned
  - old-to-new entrypoint and write-path mapping complete
  - query/write/output semantics audited at logic-unit level
  - side effects and failure modes audited explicitly
  - intentional progress delta isolated from parity claims

## Intentional Deltas

- Add a progress-stream API used only by the enhanced Sessions control.
- While running, replace the generic `동기화 중...` status sentence with bounded
  source label, repair reason, and processed/total counts when available.
- Persist one additional nullable `source_files` freshness version for the Session
  projection contract.

## Risks / Open Questions

- A live stream cannot change its HTTP status after bytes have been sent; terminal
  scanner failure must therefore be represented as a bounded terminal event.
- A parser change may affect more than one derived lane. The producer must bump
  every affected version instead of using one broad version as a shortcut.
- Exact speedup depends on source size and current Context-document cardinality;
  acceptance requires measured improvement, not a fixed duration promise.

## Exit Goal

Ordinary and repair synchronization preserve baseline data and failure semantics,
repair only stale derived lanes, provide truthful progress, and show a material
full-repair performance improvement without exposing private runtime content.

## Current Status

- Implementation and automated validation: complete on `2026-08-24`.
- Full suite: `371` tests passed; privacy and schema integrity checks passed.
- Measured combined repair: `15.982s` for `388` Codex files, versus the pinned
  baseline profile of `33.876s` for `383` files.
- Rendered merge evidence: complete at `1440x841` and `500x841`, including the
  streamed success path, configuration-error retry, focus restoration, reload,
  containment, and console checks.
- Evidence:
  - [wrap-up log](logs/2026-08-24_refactor-0001_session-sync-performance.md)
  - [final merge check](logs/2026-08-24_refactor-0001_final-merge-check.md)
