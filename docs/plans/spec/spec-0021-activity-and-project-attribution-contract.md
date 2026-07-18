# SPEC-0021: Activity And Project Attribution Contract

## Metadata

- ID: `spec-0021`
- Status: `approved`
- Run ID: `run-20260718-21`
- Attempt: `1`
- Parent Feature: [feat-0021-activity-and-project-attribution-contract](../feature/feat-0021-activity-and-project-attribution-contract.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: immutable attribution snapshot → activity segments → aggregate time contract
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Source Set

- Human decisions: use the recommended non-reconciling Project-history behavior, allow later Git discovery only for new facts, and define active segments with a 30-minute inclusive gap.
- Parent Feature, approved PRD-0004, and passed FEAT-0020.
- Current Session, workspace, source path, Git-root, and Activity Event implementation.
- Product Model, Project Architecture, and foundation-contract profile.

## Implementation Goal

- Freeze a Project attribution snapshot when each new usage fact is first persisted and provide deterministic observed-span, estimated-active-time, and longest-active-segment calculations from bounded events.

## In-Scope Behavior

- Add workspace ID, stable project key, display name, canonical path, Git root, attribution basis, and attribution time snapshots to usage facts.
- Resolve new facts from the Session's current workspace row: prefer a currently discovered Git root, otherwise the canonical workspace path, otherwise `unassigned`.
- Preserve every attribution field on conflict even when a Session is rescanned into a changed workspace or a Git root is discovered later.
- Let a new fact in that later scan use the newly current relation.
- Keep current workspace `git_root` synchronized with current filesystem evidence instead of using it as historical provenance.
- Leave legacy or previously unassigned facts unassigned; no migration or rescan performs retroactive reconciliation.
- Build per-Session segments from valid event timestamps sorted in UTC. A gap `<= 30 minutes` extends the segment; a greater gap opens another.
- End every segment at its last observed event, including incomplete Sessions; never extend to now.
- Merge overlapping or touching segments across Sessions before total active seconds and longest active segment are returned.
- Return observed Session span separately as the sum of each Session's first-to-last observed-event span.
- Support optional inclusive-start/exclusive-end clipping and explicit timezone-aware day and Monday-week boundaries.

## Out-Of-Scope Behavior

- Retroactive Project reconciliation, user reassignment controls, current-path lookup in historical queries, Dashboard UI, token pricing changes, productivity scoring, or Codex longest-running-turn ingestion.

## Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/usage.py`
- `src/localbrain/ingest/scanner.py`
- `src/localbrain/activity.py`
- attribution, migration, activity, overlap, and timezone tests
- `docs/policies/project/product.md`
- `docs/policies/project/architecture.md`

## Surface Lanes

- Attribution snapshot:
  - path roots: schema, database migration, usage persistence, scanner workspace resolution
  - dependency order: first
  - implementation responsibility: first-observation snapshot and conflict preservation
  - validation evidence: path, Git-init, moved-path, legacy-unassigned, and repeated-scan fixtures
- Activity segments:
  - path roots: `src/localbrain/activity.py`
  - dependency order: independent after timestamp semantics are fixed
  - implementation responsibility: parsing, segment construction, range clipping, overlap merge, and summary outputs
  - validation evidence: exact threshold, over-threshold, incomplete, overlap, invalid timestamp, and timezone-boundary fixtures
- Contract ownership:
  - path roots: Project Architecture and Product Model
  - dependency order: after names settle
  - implementation responsibility: immutable-versus-current metadata and metric-label rules
  - validation evidence: policy-to-code parity

## State And Interaction Contract

- `git_root`: new fact uses a current Git-root snapshot and a stable `git:<path>` key.
- `workspace_path`: new fact without Git evidence uses a canonical-path snapshot and `path:<path>` key.
- `unassigned`: no project fields are guessed later.
- Existing fact conflict: attribution fields and attribution time never change.
- Activity range uses `[start, end)`; segments are clipped to that interval before merge.
- Invalid or absent event timestamps do not create time and do not make another Session fail.

## Data And Contract Assumptions

- Snapshot workspace ID is a historical scalar rather than a cascading foreign key; name and path snapshots keep it meaningful if current workspace metadata changes.
- Git and path keys are intentionally distinct even when they currently contain the same path, because a later Git relation is a new attribution basis.
- SQLite timestamps remain source strings; activity calculations parse them into aware UTC datetimes and require aware range boundaries.
- Single-event segments have zero observed duration because no focus time beyond the event itself is inferred.
- Local calendar helpers accept an explicit IANA timezone for deterministic tests and consumers.

## Contract Surfaces

- Producer expectations: `_store_session` passes the resolved workspace to usage persistence; first insert freezes its snapshot.
- Consumer expectations: Project usage readers group by stored project key and never join current workspace metadata to redefine history; time readers use activity summary outputs and labels.
- Generated artifacts: attribution columns on `usage_facts` and derived in-memory `ActivitySegment` values.
- Source-of-truth owner: Session source metadata for observed path and branch, current workspace row for first-observation resolution, usage fact for historical attribution, Activity Events for observed time.
- Stale-assumption check: current Project inventory may continue using current workspaces, but historical usage breakdowns may not.

## Required Evaluators

- Contract: snapshot immutability, migration, current-versus-historical ownership, time definitions, and consumer boundaries.
- Functional: Git-init, moved or missing paths, unassigned stability, exact threshold, overlap, clipping, incomplete Session, and timezone boundaries.

## Acceptance Mapping

- Historical Project stability maps to conflict-preserved snapshot columns.
- Late Git discovery maps to current workspace replacement plus old/new fact fixtures.
- No reconciliation maps to legacy/unassigned preservation.
- Active-time semantics map to segment, merge, clipping, and summary functions.
- Honest labels map to distinct summary field names and durable policy language.

## Evaluation Focus

- Verify routine rescan cannot update existing fact snapshot columns.
- Verify current `workspace_id` changes do not act as a historical usage lookup.
- Verify exactly 30 minutes is one segment and 30 minutes plus one second is not.
- Verify overlapping concurrent Sessions contribute one wall-clock interval.
- Verify day and week bounds around UTC/local-date crossover.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-18`: Spec approved under the human's confirmed snapshot, no-reconciliation, and 30-minute activity decisions.
