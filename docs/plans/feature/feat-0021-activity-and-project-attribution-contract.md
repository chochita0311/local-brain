# FEAT-0021: Activity And Project Attribution Contract

## Metadata

- ID: `feat-0021`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Establish reproducible Session-time Project attribution and estimated-activity contracts so historical Project totals remain stable and downstream dashboards distinguish observed span, estimated active time, and Codex longest-running-turn duration.

## Acceptance Contract

- Session-observed source path, `cwd_raw`, and source-backed Git branch remain immutable provenance even when the local path or repository changes later.
- Each usage record stores a Project or workspace attribution snapshot, its resolution basis, and its attribution time when a relation is resolvable.
- Historical Project breakdowns consume the stored snapshot rather than resolving every record against the current workspace path or Git root at query time.
- A later scan may update current workspace metadata such as `exists_now`, display information, canonical path resolution, or a newly discovered Git root without silently changing prior Session attribution or historical Project totals.
- Project-path or Git-root relations first observed after a change apply to new source usage records only. Rebuilding older derived facts reuses their stored attribution snapshot.
- Previously unassigned or differently assigned history remains stable. Automatic historical reconciliation and bulk retroactive reassignment are not introduced.
- Observed Session span remains a separate first-to-last-event metric and is never relabeled as focused or active time.
- Consecutive observed events separated by 30 minutes or less belong to one activity segment; a gap longer than 30 minutes starts a new segment.
- Estimated active time is the sum of bounded segments. An incomplete Session ends at its last observed event rather than the current time.
- Overlapping segments from concurrent Sessions are merged before cross-Session active-time totals are calculated so the same wall-clock interval is counted once.
- Longest active segment is the single longest segment under the same rule. It is labeled as estimated and is not presented as equivalent to Codex's server-supplied longest-running-turn value.
- Time bucketing and comparisons use the configured local timezone and deterministic inclusive boundary rules.

## Scope Boundary

- In:
  - immutable Session-time path and branch provenance
  - Project or workspace attribution snapshot identity, basis, and time
  - current-workspace and later-Git-discovery enrichment boundary
  - rebuild stability for prior attribution
  - observed Session span
  - 30-minute activity-segment construction
  - incomplete-Session ending
  - concurrent-segment overlap merging
  - estimated active time and longest active segment
  - local-time boundary rules
  - synthetic path, Git-init, moved-path, event-gap, incomplete, and overlap evidence
- Out:
  - automatic historical path or repository reconciliation
  - bulk retroactive Project reassignment
  - user-facing reconciliation controls
  - token and price semantics owned by FEAT-0020
  - charts, cards, filters, breakdown tables, or projection UI
  - productivity scoring or Workflow and Skill Intelligence

## Surface Lanes

- Attribution contract lane:
  - path roots: `docs/policies/project/`, `src/localbrain/schema.sql`, `src/localbrain/db.py`
  - dependencies: FEAT-0020's stable usage-record identity
  - expected evidence: immutable observation fields, attribution snapshot shape, current-metadata separation, and compatible migration behavior
  - evaluator ownership: `contract`
- Attribution producer lane:
  - path roots: `src/localbrain/ingest/scanner.py`, Project and workspace resolution modules selected by the Spec
  - dependencies: attribution contract lane
  - expected evidence: original path, late Git initialization, moved or missing path, repeated scan, and rebuild fixtures
  - evaluator ownership: `contract`, `functional`
- Activity calculation lane:
  - path roots: usage and activity modules selected by the Spec, `src/localbrain/queries.py`
  - dependencies: stable event timestamps and Session identity
  - expected evidence: exact threshold, overlap, ongoing Session, timezone, and longest-segment fixtures
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- Session-observed path, source path, Git branch, and timestamp provenance
- current `workspaces.canonical_path`, `workspaces.git_root`, and `exists_now` meaning
- usage-record Project or workspace attribution snapshot shape
- attribution resolution basis, timestamp, rebuild, and unavailable state
- 30-minute segment threshold and boundary comparison
- observed span, estimated active time, merged active time, and longest-active-segment outputs
- local-time conversion and date-boundary behavior
- compatible schema migration and repeated-synchronization behavior

## Required Evaluators

- `contract`: immutable versus current metadata ownership, attribution snapshot shape, rebuild behavior, time semantics, and downstream consumer invariants.
- `functional`: path changes, Git initialization, missing paths, repeated scans, exact gap thresholds, overlapping Sessions, incomplete Sessions, and timezone boundaries.

## User-Visible Outcome

- This foundation Feature does not introduce a new screen. It prevents Project history from changing silently and gives later activity metrics one honest, reproducible definition.

## Entry And Exit

- Entry point: first normalization of a source usage record and calculation of Session-derived time metrics.
- Exit or transition behavior: downstream readers receive a stable attribution snapshot and deterministic activity outputs with explicit unavailable states where evidence is insufficient.

## State Expectations

- Attributed: a record keeps its Session-time Project or workspace snapshot and resolution basis.
- Unassigned: missing evidence remains explicit rather than using a later current-path guess.
- Git discovered later: current workspace metadata is enriched, but older attribution remains unchanged.
- Path missing or moved: historical source path remains inspectable and the prior attribution snapshot survives.
- Activity gap at 30 minutes: events remain in one segment.
- Activity gap over 30 minutes: a new segment begins.
- Incomplete Session: the last observed event closes the final bounded segment.
- Concurrent Sessions: overlapping wall-clock intervals contribute once to aggregate active time.

## Dependencies

- PRD-0004 was `approved` during execution and is now `passed`.
- FEAT-0020 must pass so attribution attaches to a stable usage-record identity and downstream usage consumers do not guess.
- FEAT-0022 and FEAT-0023 must not enter Spec work until this Feature's attribution and activity contracts are passed.

## Likely Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/ingest/scanner.py`
- `src/localbrain/queries.py`
- usage, attribution, and activity modules selected by the Spec
- schema, migration, attribution, workspace, activity, and time-boundary tests
- `docs/policies/project/product.md`
- `docs/policies/project/architecture.md`

## Pass Or Fail Checks

- Pass if every attributed usage fixture retains the observed path and a reproducible attribution snapshot with basis and time.
- Pass if adding `.git`, discovering a Git root, moving a path, or changing current workspace metadata does not change prior Project totals.
- Pass if records first observed after a relation change can use the new relation without rewriting older records.
- Pass if a derived-data rebuild reuses historical attribution rather than current-path lookup.
- Pass if previously unassigned records remain unassigned without an explicitly approved reconciliation action.
- Pass if event gaps of exactly 30 minutes remain in one segment and gaps greater than 30 minutes start another.
- Pass if incomplete Sessions end at their last event and concurrent overlap is counted once.
- Pass if observed span, estimated active time, and longest active segment remain distinct outputs.
- Pass if the UI-facing label contract cannot equate longest active segment with Codex longest-running-turn duration.
- Pass if local-time day and week boundaries are deterministic in synthetic tests.
- Fail if a routine scan silently reassigns historical Project ownership or if active time is calculated from an unbounded first-to-last Session span.

## Regression Surfaces

- Session and workspace identity, source paths, `git_branch`, `git_root`, and `exists_now`
- historical missing-path presentation
- Project inventory and Session-to-Project navigation
- Claude and Codex repeat scanning and source non-mutation
- primary, maintenance, and subsession identity
- current Session-derived counts and activity queries
- local-only privacy and no-external-write boundaries

## Feature Review Questions

- None at the product boundary. The Spec must choose the physical snapshot representation and migration strategy without introducing automatic historical reconciliation.

## Harness Trace

- Active spec doc: [spec-0021-activity-and-project-attribution-contract](../spec/spec-0021-activity-and-project-attribution-contract.md)
- Active run: [run-20260718-21-activity-and-project-attribution-contract](../run/run-20260718-21-activity-and-project-attribution-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [eval-0021-functional-activity-and-project-attribution-contract](../evaluation/eval-0021-functional-activity-and-project-attribution-contract.md)
- Latest fix note: [fix-0021-canonical-git-root-attribution](../fix/fix-0021-canonical-git-root-attribution.md)

## Continuity Notes

- `2026-07-18`: initial draft separated immutable Session attribution and 30-minute activity semantics from token pricing and visible dashboard composition.
- `2026-07-18`: FEAT-0020 passed and the human owner's sequential execution instruction moved this Feature into `in-loop` with no unresolved product choice.
- `2026-07-18`: initial Functional evaluation found macOS path-alias drift in Git-root keys; FIX-0021 canonicalized the producer.
- `2026-07-18`: Contract and Functional re-evaluation passed with 60 tests and complete attribution, migration, activity, overlap, and timezone evidence; FEAT-0022 may proceed.
