# FEAT-0086: Deterministic Cross-Source Workflow Projection

## Metadata

- ID: `feat-0086`
- Status: `passed`
- Type: `foundation`
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017: Source-Backed Workflow Map And Workstream Lenses](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-14`
- Updated: `2026-09-14`

## Goal

- Produce one bounded, deterministic, read-only Focus projection from current
  persisted LocalBrain evidence so the Session Workflow Map has useful
  cross-source lineage and honest abstention without hidden I/O or AI.

## Acceptance Contract

- Projection starts from one FEAT-0085-eligible primary work Session and returns
  its Episode even when no relation is supportable.
- The projection is computed on demand from the current SQLite state. This
  Feature adds no Episode cache, relation table, background job, startup work,
  ingestion hook, or write during a read.
- Candidate Episode discovery uses only exact persisted joins:
  - shared user-linked Thread;
  - shared user-linked Workstream plus another exact signal;
  - shared direct Session reference target plus the same Project/workspace or
    source-observed Git root;
  - the same non-empty Git root and branch plus a shared direct target or
    explicit organization owner.
- Same workspace, Git root, branch, title tokens, full-text similarity, or time
  proximity alone never enters the graph. No message or document body is read
  to compensate for missing normalized evidence.
- Candidate Sessions are ordered by exact-signal strength, temporal distance
  from the selected Episode, observation time, and stable Episode key. At most
  `200` candidates enter relation classification.
- `continues` is emitted only between adjacent time-ordered Episodes in one
  qualifying exact-signal set: shared Thread, or shared direct target combined
  with the same Workstream or same non-empty Git root/branch.
- `branches-from` is emitted only when two Sessions share one exact direct
  target or explicit Thread/Workstream owner, share one non-empty Git root, and
  have different non-empty source-observed branches. The nearest earlier
  qualifying Episode is the branch origin. The edge remains visibly a
  deterministic candidate rather than a confirmed Git ancestry claim.
- `merged-into` is not inferred from a later return to `main`, `master`, or any
  other branch name. The value remains available in the read-model contract for
  future direct evidence or FEAT-0088 user assertions.
- When several candidate edges compete for one slot, the projection uses the
  documented signal priority and stable tie-breaks. It never chooses by random
  layout, opaque score, or model output.
- The returned Focus neighborhood contains at most `24` Episodes, at most `4`
  visible side-branch roots, and at most `4` Episodes on one side branch. Every
  omitted set reports a retained and observed total so the UI never implies
  completeness.
- Cross-source evidence attaches to an Episode only through:
  - its normalized direct Session reference projection;
  - its own Project/workspace and Git identity;
  - its exact Workstream or Thread membership and resources owned by that same
    explicit organization context;
  - persisted Atlassian Item or structure-reference evidence already connected
    to that Session or organization context;
  - eligible Local Context Documents already directly referenced or explicitly
    organized.
- Subsessions may contribute a bounded count and destination beneath their
  parent Episode but never become peer Episodes. Ambient Documents, Jira/Wiki
  records, URLs, Activity Events, and Resources do not become top-level nodes.
- Evidence is grouped by source family with at most `5` expanded items per
  family plus retained and observed totals. Source identity, evidence kind,
  freshness/availability, observation time, destination, and admission reason
  remain inspectable.
- Stale or unavailable persisted evidence remains last-known evidence with its
  state. A projection read does not refresh, remove, or imply current access.
- Opening or recomputing the projection performs no source synchronization,
  filesystem scan, source-file parse, full-message read, connector discovery,
  capability inspection, Atlassian Sync/Refresh, remote read, model call, or
  mutation of any existing product record.
- Repeating the same read against unchanged SQLite state returns identical
  Episode membership, relations, reasons, bounds, and ordering.

## Scope Boundary

- In:
  - selected-Session eligibility and exact candidate discovery
  - deterministic `continues` and `branches-from` emission
  - future-compatible `merged-into` read shape without heuristic emission
  - bounded cross-source evidence admission and grouping
  - stable ordering, truncation totals, stale/unavailable state, and abstention
  - local read-only projection service and synthetic fixtures
- Out:
  - Episode or relation persistence, caching, incremental maintenance, or jobs
  - message/document semantic analysis, lexical fallback, embeddings, or Qwen
  - Session-detail action, map route, template, renderer, controls, or styling
  - durable user assertions, correction actions, Workstream lens, or Atlas
  - source ingestion, external adapters, remote reads, Sync, or Refresh

## Surface Lanes

- Candidate and relation lane:
  - path roots: new workflow projection/query owner under `src/localbrain/`
  - dependencies: passed FEAT-0085 descriptor contract
  - expected evidence: exact-signal matrix, weak-signal rejection, ordering,
    bounds, cycles, repeat reads, and abstention
  - evaluator ownership: `contract`, `functional`
- Evidence admission lane:
  - path roots: workflow projection owner and current Session reference,
    Workstream, Local Context, and Atlassian read-model consumers
  - dependencies: existing normalized evidence contracts
  - expected evidence: direct versus organized grouping, source state, totals,
    destinations, subordinate Subsessions, and zero peer artifact nodes
  - evaluator ownership: `contract`, `functional`
- Regression/owner lane:
  - path roots: focused tests and affected product, architecture, privacy, and
    data-model owners
  - dependencies: both read lanes
  - expected evidence: zero writes/hidden I/O and current-flow compatibility
  - evaluator ownership: `contract`

## Contract Surfaces

- Focus projection service input and versioned FEAT-0085 output.
- Exact-signal admission and relation-emission matrix.
- Candidate, Episode, branch, and evidence caps plus observed/retained totals.
- Source-family evidence grouping, destination, freshness, and reason shape.
- Read-only query, no-body-parse, no-hidden-I/O, and deterministic ordering
  guarantees.

## Required Evaluators

- `contract`: source admission, relation rules, bound semantics, read-only
  ownership, provenance, privacy, and downstream route readiness.
- `functional`: positive and negative signal matrices, ordering, truncation,
  stale/unavailable evidence, repeat reads, zero writes, and regressions.

## User-Visible Outcome

- None required in this Foundation Feature. It supplies the bounded local
  projection consumed later by FEAT-0087.

## Entry And Exit

- Entry point: an eligible persisted primary Session ID.
- Exit or transition behavior: return one deterministic bounded Focus payload,
  including a single-node abstained payload when no edge is supportable; an
  ineligible or missing Session returns a typed not-found/ineligible result.

## State Expectations

- Connected: supported predecessor, successor, or branch candidates and reasons
  are present.
- Unconnected: selected Episode and its own evidence remain available.
- Partial: caps report observed and retained totals.
- Stale/unavailable: last-known evidence remains labeled and no refresh occurs.
- Ineligible/missing: no projection is fabricated.
- Error: the read fails without writes or partial durable state.

## Dependencies

- FEAT-0085 must be `passed` before this Feature enters build.
- Passed FEAT-0072 and FEAT-0073 own direct Session reference evidence.
- Passed FEAT-0080 through FEAT-0083 own persisted Atlassian local evidence and
  structure-reference boundaries.
- Current Workstream, Thread, checkpoint, and Resource links remain explicit
  organization evidence, not workflow-direction authority.

## Likely Affected Surfaces

- a new workflow projection/query module under `src/localbrain/`
- bounded consumers of `src/localbrain/session_references.py`
- bounded consumers of `src/localbrain/workstreams.py`
- current Session, Local Context, workspace/Git, and Atlassian query owners
- focused workflow-projection and zero-write tests under `tests/`
- affected product, architecture, privacy, and data-model owner docs

## Pass Or Fail Checks

- Pass if exact qualifying evidence produces stable `continues` or
  `branches-from` candidates with inspectable ordered reasons.
- Pass if each isolated weak signal—workspace, Git root, branch, words, or
  recency—produces no edge.
- Pass if the same unchanged database produces byte-equivalent semantic output
  order and the graph remains acyclic.
- Pass if all Episode/branch/evidence caps expose honest omitted totals.
- Pass if direct and explicit-organization evidence remain distinguishable and
  source artifacts never become peer Episodes.
- Pass if single-node, partial, stale, unavailable, ineligible, and error paths
  are deterministic.
- Pass if projection reads execute zero writes and trigger none of the excluded
  scans, source parsing, external operations, or model work.
- Fail if FEAT-0087 must query raw source content, infer relation meaning, or
  invent source state to render the Focus view.

## Regression Surfaces

- Session synchronization, eligibility, inventory, detail, and pin behavior.
- Session direct-reference capture and Related Materials rail.
- Local Context scanning and document reading.
- Workstream/Thread links, checkpoints, Resources, and Suggestions.
- Atlassian Sync, Explorer, Add, Connections, and explicit Refresh.
- Search, Schema Explorer, Task Runner, database integrity, and privacy.

## Harness Trace

- Spec doc: [SPEC-0086](../spec/spec-0086-deterministic-cross-source-workflow-projection.md).
- Run: [RUN-20260914-96](../run/run-20260914-96-deterministic-cross-source-workflow-projection.md).
- Execution profile: `foundation-contract`
- Latest evaluator reports:
  [Contract](../evaluation/eval-0086-contract-deterministic-cross-source-workflow-projection.md),
  [Functional](../evaluation/eval-0086-functional-deterministic-cross-source-workflow-projection.md).
- Latest fix note: not created.

## Open Review Decisions

- None. The owner approved the sparse exact-signal matrix and hard bounds, and
  the Feature passed after FEAT-0085. Its projection remains the deterministic
  baseline consumed by the Session Focus surface.

## Continuity Notes

- `2026-09-14`: proposed behind FEAT-0085. The on-demand, no-persistence
  boundary is intended to prove usefulness without changing ingestion, schema,
  Sessions, or other current product behavior.
- `2026-09-14`: owner approved sequential execution. FEAT-0086 remains queued
  and must not enter build before FEAT-0085 passes.
- `2026-09-14`: FEAT-0085 passed Contract and Functional evaluation; FEAT-0086
  entered RUN-20260914-96 as the only in-loop Feature.
- `2026-09-14`: passed RUN-20260914-96 with the read-only exact-signal Focus
  projection, `14/14` focused and `512/512` complete tests, zero traced writes,
  and current generated/privacy owners.
