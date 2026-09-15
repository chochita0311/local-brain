# SPEC-0086: Deterministic Cross-Source Workflow Projection

## Metadata

- ID: `spec-0086`
- Status: `approved`
- Run: [RUN-20260914-96](../run/run-20260914-96-deterministic-cross-source-workflow-projection.md)
- Attempt: `1`
- Parent Feature: [FEAT-0086](../feature/feat-0086-deterministic-cross-source-workflow-projection.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Surface Lane: none
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-14`
- Updated: `2026-09-14`

## Source Set

- Human approval of FEAT-0085 through FEAT-0089 for sequential execution on
  `2026-09-14`.
- Passed FEAT-0085 and approved FEAT-0086.
- Passed Session eligibility/reference and Atlassian local-evidence contracts.
- Current Session Related Materials, Workstream/Thread membership, workspace,
  structure-reference, Product, Architecture, Privacy, and data-model owners.

## Implementation Goal

- Add one local, read-only Focus projection service that turns an eligible
  Session plus exact persisted signals into a stable, bounded Episode tree and
  source-family evidence groups without adding a route, cache, schema object,
  source operation, or model dependency.

## In-Scope Behavior

- Add `src/localbrain/workflow_focus.py` with
  `WORKFLOW_FOCUS_VERSION = "localbrain.workflow-focus.v1"` and frozen,
  JSON-compatible descriptors for evidence items/groups, Episode views, and
  the complete Focus result.
- `workflow_focus_projection(connection, session_id)` accepts a positive local
  Session ID and returns status `ready`, `missing`, or `ineligible`.
  `missing` and `ineligible` return no fabricated Episode; `ready` always
  retains the selected Episode, including a one-node abstained result.
- Eligibility requires `work`, `primary`, and meaningful persisted activity:
  positive normalized event count, an Activity Event, or a Usage Record.
- Load only normalized metadata and evidence columns from SQLite. Episode
  observation instant uses its FEAT-0085 last observation, then start
  observation; missing or equal time never creates a relation.
- Exact user organization for directional classification uses only Session
  links whose `linked_by` is `user`. Thread membership also contributes its
  owning Workstream. Accepted/generated organization may remain visible
  evidence but cannot silently create direction in this baseline.
- Candidate qualification and strength order are:
  1. shared user-linked Thread;
  2. shared direct target plus shared user-linked Workstream;
  3. shared direct target plus the same non-empty Git root and branch;
  4. shared direct target plus the same workspace or non-empty Git root;
  5. shared user-linked Workstream plus the same non-empty Git root.
  Same workspace, root, branch, words, or time alone do not qualify.
- Sort qualified candidates by strength, absolute temporal distance from the
  selected Episode, candidate observation time, and stable Episode key. Record
  the full observed total and admit at most `200` into classification.
- Build `continues` candidates only between adjacent, strictly time-ordered
  Episodes in one exact group: shared Thread; shared target plus Workstream; or
  shared target plus identical non-empty Git root/branch.
- Build `branches-from` only for identical non-empty Git roots with different
  non-empty observed branches plus a shared direct target or user organization
  owner. Choose the nearest earlier qualifying origin. A qualifying different-
  branch relation is more specific than a competing `continues` relation;
  strong-reason priority, temporal distance, and Episode key resolve remaining
  competition. Retain at most one incoming derived relation per Episode.
- Do not emit `merged-into`. FEAT-0085 keeps the value shape available for a
  future direct source relation or FEAT-0088 user assertion.
- Pass candidates through FEAT-0085 normalization. Traverse outward from the
  selected Episode in stable rank order, returning at most `24` Episodes.
  Crossing an outgoing `branches-from` starts one side branch; return at most
  `4` side-branch roots and at most `4` Episodes reached within each side
  branch. Return observed and retained totals for candidates, Episodes, and
  branch roots.
- Every relation reason uses only opaque reference, numeric organization,
  workspace, or hashed Git identity. Raw repository paths and source-native
  Session IDs never enter serialized output.
- Reuse the current bounded Session Related Materials read projection for
  direct and explicit-organization resources, add current user Workstream and
  Thread membership descriptors, direct-child Session descriptors, and
  persisted Atlassian structure-reference descriptors. Do not read source or
  document bodies.
- Group evidence by stable source family, deduplicate by stable evidence key,
  order by admission authority, observation, identity, and key, expose at most
  `5` items per family, and retain per-group observed/retained totals plus
  partial/stale state. Direct-reference, organization, subordinate-Session,
  and structure-reference admissions remain distinguishable.
- Add the direct reference item's first observed time as an additive internal
  projection field so the Focus service does not reopen Activity Events or
  source files.
- Update Product, Architecture, Privacy, Workspace/Session Activity, and Work
  Organization owner documents for the implemented derived read boundary.

## Out-Of-Scope Behavior

- SQLite schema, migration, cache, background work, ingestion, or persistence.
- Route, API, template, CSS, JavaScript, map renderer, or visible action.
- Raw message/document reads, lexical or semantic matching, embeddings, Qwen,
  or any other model call.
- Sync, Refresh, connector, filesystem, source-file, capability, or network
  operation.
- User assertions, corrections, Workstream lens promotion, or Atlas behavior.

## Affected Surfaces

- `src/localbrain/workflow_focus.py`
- additive observation field in `src/localbrain/session_references.py`
- `tests/test_workflow_focus.py`
- Product, Architecture, Privacy, Workspace/Session Activity, and Work
  Organization policy owners
- FEAT-0086, SPEC-0086, RUN-20260914-96, and evaluator artifacts

## State And Interaction Contract

- This Feature has no user interaction.
- `ready` may be connected, unconnected, partial, or stale; these are payload
  facts rather than alternate HTTP behavior.
- Missing or ineligible selections are typed results, not exceptions. Invalid
  non-positive/non-integer input raises `ValueError` before a query.
- Projection exceptions leave SQLite unchanged and create no partial durable
  state.

## Data And Contract Assumptions

- Current Session, reference, organization, Resource, Local Context, and
  Atlassian tables remain the only evidence authorities.
- Existing Related Materials safety and destination logic remains canonical;
  Focus consumes it instead of creating a looser URL/path resolver.
- Workstream/Thread membership is an exact organization signal, not Git
  ancestry. A different observed branch plus shared evidence is still only a
  deterministic candidate.
- Current SQLite state is the complete read snapshot. No freshness check may
  perform external or filesystem work.

## Contract Surfaces

- Focus result status, counts, Episode order, relation order, diagnostics, and
  projection version.
- Exact candidate and relation signal matrix with stable tie-breaks.
- Episode, candidate, branch-root, branch-depth, and evidence-family caps.
- Evidence family, admission reason, authority, observation, destination,
  availability, stale, and partial semantics.
- Zero-write, no-body, no-hidden-I/O read behavior.

## Required Evaluators

- Contract: source admission, direction rules, cap/count truth, reuse boundary,
  privacy, ownership, non-persistence, and FEAT-0087 readiness.
- Functional: positive/negative signal matrix, adjacency, nearest predecessor,
  tie-breaks, all caps, evidence grouping, stale/unavailable, missing/ineligible,
  repeat determinism, JSON serialization, SQL trace with zero writes, and full
  regressions.
- Design: not required; no visible surface changes.
- UX heuristic: not required; no interaction changes.

## Acceptance Mapping

- Always-retained selected Episode and typed errors → selection fixtures.
- Exact cross-source candidates and weak-signal rejection → signal matrix.
- `continues`, `branches-from`, no heuristic merge → relation fixtures.
- Stable bounds and honest totals → 200/24/4/4/5 cap fixtures.
- All sources as evidence, never peer nodes → direct/organization/child/
  structure evidence fixtures.
- Read-only and repeatable → SQLite trace and byte-equivalent semantic output.
- Existing behavior unchanged → focused consumer tests and complete suite.

## Evaluation Focus

- Confirm that one broad Workstream or repository cannot create edges without
  the required second exact signal.
- Confirm that a source artifact never appears in the Episode collection.
- Confirm that raw Git root, source path, source-native ID, body, or opaque
  payload does not survive serialization.
- Confirm FEAT-0087 can render every visible state without issuing another
  domain query or inventing a relation explanation.

## Open Blockers

- None.

## Continuity Notes

- `2026-09-14`: approved for RUN-20260914-96 after FEAT-0085 passed both
  required evaluators.
