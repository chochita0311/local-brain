# EVAL-0021: Activity And Project Attribution Contract

## Metadata

- ID: `eval-0021-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-21`
- Attempt: `2`
- Feature: [feat-0021-activity-and-project-attribution-contract](../feature/feat-0021-activity-and-project-attribution-contract.md)
- Spec: [spec-0021-activity-and-project-attribution-contract](../spec/spec-0021-activity-and-project-attribution-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: immutable attribution snapshot and activity-time ownership
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: first-observation Project snapshots and bounded activity semantics.
- Active spec: SPEC-0021.
- Evaluated build: current working tree after FIX-0021.

## Checks

- Inspected usage-fact snapshot shape, conflict-update exclusions, workspace-current metadata, migration, and no-reconciliation behavior.
- Inspected path and Git-key canonicalization and first-observation basis selection.
- Inspected Activity Event authority, inclusive 30-minute threshold, last-event ending, `[start, end)` clipping, overlap merge, and distinct metric outputs.
- Inspected explicit IANA timezone configuration and Product Model/Project Architecture parity.

## Evidence

- Fresh schema stores workspace ID, stable key, name, path, Git root, basis, and attribution time without a cascading workspace foreign key.
- Upsert never updates attribution columns. Path → Git → path transitions changed only facts first observed in each state.
- A previously unassigned fact stayed unassigned after a workspace path became available; the new fact used the new path snapshot.
- Legacy usage facts migrated to explicit `unassigned` with their original import time and no retroactive Project guess.
- Activity outputs are named `observed_session_span_seconds`, `estimated_active_seconds`, and `longest_active_segment_seconds`; no Codex running-turn equivalence exists.
- The 60-test suite, isolated Python compilation, diff check, and privacy check passed.

## Evidence Gaps

- None for the foundation contract.

## Contract Evidence

- Producer surfaces: workspace resolution, Session storage, usage persistence, Activity Event timestamps.
- Consumer surfaces: future usage Project read models and activity summaries; existing current Project inventory remains independent.
- Schemas, payloads, generated artifacts, commands, routes, config, or policy docs checked: `usage_facts`, `activity.py`, `LOCALBRAIN_TIMEZONE`, Project Architecture, Product Model, Developer Guide.
- Stale-assumption check: current-workspace joins remain appropriate for current Project browsing but are explicitly prohibited for historical usage grouping.

## Findings

- No remaining contract defect, spec gap, or planning gap after FIX-0021.

## Regression Notes

- Current Session, Project inventory, usage pricing, source synchronization, retrieval, runner, and UI-contract suites passed.

## Route

- Next action: `pass`

## Continuity Notes

- `2026-07-18`: Attempt 2 passed after canonicalizing Git-root producer output.
