# SPEC-0085: Workflow Episode And Direction Contract

## Metadata

- ID: `spec-0085`
- Status: `approved`
- Run: [RUN-20260914-95](../run/run-20260914-95-workflow-episode-and-direction-contract.md)
- Attempt: `1`
- Parent Feature: [FEAT-0085](../feature/feat-0085-workflow-episode-and-direction-contract.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: none
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-14`
- Updated: `2026-09-14`

## Source Set

- Human approval of FEAT-0085 through FEAT-0089 for sequential execution on
  `2026-09-14`.
- Approved PRD-0017 and FEAT-0085.
- Passed FEAT-0066 source identity, FEAT-0071 Session eligibility, and FEAT-0072
  reference-evidence ownership.
- Product, Architecture, Privacy, and Workspace/Session Activity owners.
- Current `activity.parse_timestamp` and immutable descriptor patterns in the
  LocalBrain domain modules.

## Implementation Goal

- Add one pure, dependency-free workflow descriptor module and synthetic tests
  that make Episode identity, observation time, state axes, direction kinds,
  reasons, validation, diagnostics, and deterministic acyclic ordering an
  executable contract without schema or UI changes.

## In-Scope Behavior

- Add `src/localbrain/workflow_projection.py` with
  `WORKFLOW_PROJECTION_VERSION = "localbrain.workflow-projection.v1"`.
- Define frozen descriptors for:
  - `WorkflowEpisode`;
  - `WorkflowRelationReason`;
  - `WorkflowRelation`;
  - `WorkflowDiagnostic`;
  - `NormalizedWorkflowRelations`.
- `workflow_episode_key(source_key, external_id)` validates non-empty text and
  returns `session:` plus a SHA-256 digest of the length-delimited source key
  and external ID. Local row ID, title, path, and provider kind do not affect
  the key.
- `workflow_episode_from_session(row, ...)`:
  - accepts only `session_class=work` and `session_role=primary`;
  - requires positive local Session ID plus non-empty source key/external ID;
  - derives earliest and last observation as the minimum and maximum valid UTC
    timestamps among `started_at`, `first_event_at`, `last_event_at`, and
    `ended_at`;
  - leaves both bounds absent when none parse;
  - exposes the canonical `/sessions/{id}` destination;
  - bounds projected title to `500` code points and explicit intent, outcome,
    and next action to `2,000` each without inventing content;
  - validates non-negative evidence counts and stores them in stable
    case-sensitive key order;
  - validates activity, lifecycle, authority, and closure-reason parity.
- Activity values are `active`, `quiet`, and `unknown`. Lifecycle values are
  `open`, `closed`, and `unknown`. Closure reasons are `completed`,
  `abandoned`, `superseded`, `merged`, and `other`; exactly `closed` requires
  one reason and other lifecycle values prohibit it.
- Authority values are `observed`, `deterministic-candidate`,
  `explicit-organization`, and `user-confirmed`.
- Direction values are exactly `continues`, `branches-from`, and
  `merged-into`.
- Reason values distinguish strong reasons (`direct-source-relation`,
  `shared-reference`, `thread-membership`, `workstream-membership`,
  `user-assertion`) from supporting-only reasons (`same-workspace`,
  `same-git-root`, `same-git-branch`, `lexical-overlap`,
  `temporal-proximity`). Reason identity is non-empty and bounded to `500` code
  points; optional observation time is normalized to UTC.
- `normalize_workflow_relations(relations)` applies stable ordering by source
  observation, target observation, source key, target key, kind, and reason
  tuple. It retains only relations that:
  - use known values and distinct endpoints;
  - have parseable source and target times with target strictly later;
  - carry at least one strong reason;
  - use `user-confirmed` only with `user-assertion` and use
    `explicit-organization` only with Thread or Workstream membership;
  - do not create a directed cycle in the already retained result.
- Every omitted relation produces one deterministic diagnostic with code
  `invalid-value`, `self-edge`, `non-forward-time`, `missing-strong-reason`,
  `authority-reason-mismatch`, or `cycle-omitted` and safe endpoint/kind fields.
- Descriptor `as_dict()` output is JSON-compatible, versioned, deterministic,
  and contains no source messages, document bodies, opaque payloads, or local
  source paths.
- Update the four durable owner documents with the implemented derived-state,
  identity, state, direction, privacy, and non-persistence contract.

## Out-Of-Scope Behavior

- SQLite tables, compatible migration, value-registry or schema-presentation
  generation.
- Projection queries, signal admission, caching, APIs, routes, templates,
  JavaScript, CSS, or visible behavior.
- User assertion persistence, Workstream lens state, source ingestion, remote
  operations, semantic matching, model calls, or Qwen.

## Affected Surfaces

- `src/localbrain/workflow_projection.py`
- `tests/test_workflow_projection_contract.py`
- `docs/policies/project/product.md`
- `docs/policies/project/architecture.md`
- `docs/policies/project/privacy-and-data.md`
- `docs/policies/project/data-model/workspace-and-session-activity.md`
- FEAT-0085, SPEC-0085, RUN-20260914-95, and evaluator artifacts

## State And Interaction Contract

- This Feature has no user interaction.
- Invalid Episode input raises `ValueError` before producing a descriptor.
- Invalid relations are diagnostics in the normalized set so a later bounded
  projection can abstain without failing the selected Episode.
- Session `ended_at` participates only in observation bounds and cannot change
  lifecycle state.

## Data And Contract Assumptions

- `sources.kind` is the stable source key and `sessions.external_id` is stable
  only inside that source.
- `sessions.id` is the current local navigation identity and is intentionally
  excluded from the cross-rebuild Episode key.
- Existing primary-work eligibility remains owned by FEAT-0071. This module
  validates class/role but does not query activity or Usage eligibility.
- UTC normalization reuses `activity.parse_timestamp`; invalid timestamps are
  absent observations rather than exceptions.
- The descriptor module owns no storage and importing it causes no I/O.

## Contract Surfaces

- Producer expectations: later producers supply normalized Session/source
  metadata, explicit state values, bounded evidence counts, and relation
  reasons.
- Consumer expectations: later consumers treat `episode_key` as stable derived
  identity, `session_id` as local navigation, respect separate state axes, and
  show diagnostics/abstention rather than repairing relations.
- Generated artifacts: none.
- Source-of-truth owner: workflow descriptor module plus Product, Architecture,
  Privacy, and Workspace/Session Activity policies.
- Stale-assumption check: search runtime, tests, schema/value generators, and
  current Session/Workstream consumers for any new dependence on an Episode
  table or on Session end as closure; none may be introduced.

## Required Evaluators

- Contract: descriptor/value completeness, identity stability, owner parity,
  privacy, non-persistence, and stale assumptions.
- Functional: key stability, eligibility, bounds, timestamp normalization,
  state parity, all direction kinds, invalid relation diagnostics, cycle
  omission, serialization, import-time no-I/O, and regressions.
- Design: not required; no visible surface changes.
- UX heuristic: not required; no interaction changes.

## Acceptance Mapping

- Stable one-Session Episode identity → key helper and Episode fixture tests.
- Bounded Episode shape and no generated prose → descriptor construction and
  serialization tests.
- Separate time/activity/lifecycle/authority → state-parity and ended-at tests.
- Minimal vocabulary and reason shape → constant and relation fixture tests.
- Weak signals cannot establish direction → strong-reason validation tests.
- Direction, self-edge, cycle, and abstention → normalization diagnostics tests.
- Rebuildable/no persistence/no regressions → source inspection, import test,
  full suite, generated-owner checks, privacy check.

## Evaluation Focus

- Confirm the hash input cannot collide through delimiter ambiguity.
- Confirm deterministic ordering and diagnostics do not depend on input order.
- Confirm no output includes raw external IDs, source paths, body text, or
  arbitrary values outside the approved bounds.
- Confirm owner docs do not imply that the descriptor is persisted or that a
  candidate edge is user-confirmed.

## Open Blockers

- None.

## Continuity Notes

- `2026-09-14`: approved for RUN-20260914-95 after the owner accepted the
  dependency-ordered Feature chain.
