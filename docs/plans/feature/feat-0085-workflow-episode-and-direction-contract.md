# FEAT-0085: Workflow Episode And Direction Contract

## Metadata

- ID: `feat-0085`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017: Source-Backed Workflow Map And Workstream Lenses](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-14`
- Updated: `2026-09-14`

## Goal

- Fix the smallest Session-anchored Episode and directional-relation contract
  so a deterministic projection and Focus UI can proceed without guessing what
  a node, edge, time, lifecycle, authority, or abstention means.

## Acceptance Contract

- The initial Episode is a derived projection of exactly one eligible primary
  work Session. Subsessions remain evidence owned by their eligible parent;
  Maintenance and provider-internal Sessions are ineligible.
- Stable Episode identity is the owning Session's stable source key plus native
  external Session ID. The current local `sessions.id` remains a navigation and
  lookup value, not the durable cross-rebuild identity.
- The bounded Episode value shape contains stable identity, local Session
  destination, source provenance, observed start, last observation, display
  title, Project/workspace identity when present, source-observed Git branch
  when present, evidence counts, activity state, lifecycle state, and
  epistemic authority.
- Existing Session title is the initial display authority. Intent, outcome, and
  next action remain absent unless one exact approved user-owned field supplies
  them; the contract never fills missing values from generated prose.
- Observed start and last observation use documented deterministic timestamp
  fallbacks. Session `ended_at` records observation scope and never means the
  workflow is complete.
- Activity uses `active`, `quiet`, or `unknown`. Lifecycle uses `open`,
  `closed`, or `unknown` plus a separate closing reason. Authority uses
  `observed`, `deterministic-candidate`, `explicit-organization`, or
  `user-confirmed`. These axes never collapse into one state.
- The first directional vocabulary is exactly:
  - `continues`: the successor advances the same bounded line;
  - `branches-from`: the successor starts a separately resumable direction
    from an earlier Episode;
  - `merged-into`: the source branch's result rejoins a later Episode.
- `contributes-to`, `blocks`, `supersedes`, and `parallel-to` remain outside
  this Feature. Adding one requires a returned Feature boundary and cannot be
  introduced by the producer or UI alone.
- Every relation is directed from an earlier observation to a later one, uses
  distinct source and destination Episode keys, and carries its kind,
  authority, ordered reason list, observation bounds, and projection version.
  A relation that would create a cycle is omitted with a bounded diagnostic.
- A relation reason identifies an exact signal family and source-backed
  identity without copying Session messages, document bodies, or opaque tool
  payloads. Numeric confidence is not required and cannot replace the reason.
- Same workspace, directory, repository, lexical wording, title tokens, or
  recency alone cannot establish a directional relation.
- Unsupported identity, time, direction, or evidence yields explicit
  abstention. The contract favors a single unconnected Episode over a weak
  edge.
- The Episode graph and deterministic candidate relations are rebuildable
  derived state and are not persisted by this Feature. Future user assertions
  have a separate durable owner under FEAT-0088.
- No existing Session, Activity Event, reference evidence, Workstream, Thread,
  checkpoint, Resource, Suggestion, Atlassian, or Local Context value is
  migrated, rewritten, or deleted.

## Scope Boundary

- In:
  - Episode identity and bounded field shape
  - observed-time fallback and ordering rules
  - activity, lifecycle, and authority axes
  - `continues`, `branches-from`, and `merged-into` semantics
  - relation reason, direction, cycle, version, and abstention rules
  - derived ownership and future assertion-overlay boundary
- Out:
  - cross-source signal admission or candidate-selection algorithm
  - projection queries, caching, persistence, or API routes
  - workflow map, controls, correction UI, Workstream lens, or Atlas
  - new Session parsing, message summarization, embeddings, Qwen, or model work

## Contract Surfaces

- Episode key, navigation identity, and bounded value shape.
- Direction kind, edge direction, reason shape, authority, and projection
  version.
- Observed start, last observation, quietness, closure, and unknown semantics.
- Derived-state ownership, abstention, cycle prevention, and assertion-overlay
  boundary.
- Product, architecture, privacy, and Session activity data-model ownership.

## Required Evaluators

- `contract`: identity, vocabulary, value shape, state separation, ownership,
  privacy, versioning, abstention, and downstream readiness.
- `functional`: deterministic timestamp fallback, value validation, ordering,
  self-edge rejection, and cycle omission using synthetic fixtures.

## User-Visible Outcome

- None required in this Foundation Feature. Existing screens remain unchanged;
  downstream Features gain one trustworthy graph vocabulary.

## Entry And Exit

- Entry point: one already persisted eligible primary work Session supplied by
  a downstream producer.
- Exit or transition behavior: return one validated Episode descriptor and
  zero or more validated relation descriptors, or an explicit abstention that
  FEAT-0086 can consume.

## State Expectations

- Complete: every required identity and time field validates.
- Partial: optional title context, Project, branch, or explicit fields remain
  absent without invented fallback content.
- Quiet: inactivity is visible only on the activity axis.
- Closed: requires a separate supported closing reason; Session end time alone
  is insufficient.
- Abstained: no edge is produced and the reason category is inspectable.
- Invalid/cyclic: the relation is omitted without corrupting other descriptors.

## Dependencies

- PRD-0017 is `approved`.
- Passed FEAT-0066 supplies stable source-key versus provider identity.
- Passed FEAT-0071 supplies meaningful primary work Session eligibility.
- Passed FEAT-0072 supplies direct reference-evidence ownership and privacy
  boundaries; it does not define workflow direction.

## Likely Affected Surfaces

- one workflow projection value/validation owner under `src/localbrain/`
- focused synthetic contract tests under `tests/`
- `docs/policies/project/product.md`
- `docs/policies/project/architecture.md`
- `docs/policies/project/privacy-and-data.md`
- `docs/policies/project/data-model/workspace-and-session-activity.md`
- generated value/schema owners only if the approved implementation introduces
  a persisted value, which this draft explicitly does not propose

## Pass Or Fail Checks

- Pass if one Session maps to one stable Episode key without treating the local
  row ID as rebuild-stable identity.
- Pass if all three relation kinds, edge direction, reason fields, authority,
  version, and abstention have exact validated shapes.
- Pass if timestamp fallbacks are deterministic and Session end never produces
  closure.
- Pass if activity, lifecycle, and authority can vary independently.
- Pass if self-edges, cycles, missing identity, and unsupported evidence omit
  the relation predictably.
- Pass if no message body, document body, opaque payload, model output, or
  existing product record is added to the contract.
- Fail if FEAT-0086 or FEAT-0087 must invent Episode identity, relation meaning,
  state ownership, or fallback behavior.

## Regression Surfaces

- Multi-source Session identity and source provenance.
- Primary, Subsession, Maintenance, and empty-stub eligibility.
- Session reference evidence and Related Materials authority.
- Existing Workstream/Thread organization and Suggestions.
- Repository privacy and generated-owner parity.

## Harness Trace

- Spec doc: [SPEC-0085](../spec/spec-0085-workflow-episode-and-direction-contract.md)
- Run: [RUN-20260914-95](../run/run-20260914-95-workflow-episode-and-direction-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator reports:
  [Contract](../evaluation/eval-0085-contract-workflow-episode-and-direction-contract.md),
  [Functional](../evaluation/eval-0085-functional-workflow-episode-and-direction-contract.md).
- Latest fix note: not created.

## Open Review Decisions

- None. The owner approved the minimal `continues`, `branches-from`, and
  `merged-into` vocabulary and deferred every other relation.

## Continuity Notes

- `2026-09-14`: proposed as the first dependency in the approved PRD-0017
  chain. It is planning-only and changes no runtime behavior until the human
  owner approves this Feature boundary.
- `2026-09-14`: owner approved FEAT-0085 through FEAT-0089 for sequential
  execution. FEAT-0085 entered RUN-20260914-95 as the only in-loop Feature.
- `2026-09-14`: passed RUN-20260914-95 with the pure versioned Episode and
  direction contract, `16/16` focused and `498/498` complete tests, current
  generated schema owners, and no route, database, or existing-screen change.
