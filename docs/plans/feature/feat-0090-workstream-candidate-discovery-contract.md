# FEAT-0090: Workstream Candidate Discovery Contract

## Metadata

- ID: `feat-0090`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-15`
- Updated: `2026-09-15`

## Current Applicability

The pure pair contract retains its technical `passed` result. Subsequent owner
review rejected pair-as-workstream granularity and a review/promotion pipeline
as sufficient for the intended automatic replacement. This is retained
implementation evidence and a possible comparator, not the next product's
identity, required admission rule, or a mandate to execute FEAT-0091–0094.
Those dependent proposals are superseded. The revised
[PRD-0017 analysis boundary](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md#reconciliation-and-approval-state)
is approved. [FEAT-0095's bounded comparison](feat-0095-bounded-work-reconstruction-experiment.md)
is implemented and verified through synthetic tests and an unassessed current-data
execution check in RUN-20260915-101. Independent quality assessment remains the
blocker; DB-path and period selection are resolved.

## Goal

Define one provisional Workstream candidate and its evidence-scoped membership
without making a Session, a Focus component, or an inferred label the durable
Workstream identity.

## Acceptance Contract

- A candidate is an ephemeral, versioned descriptor with an opaque stable seed
  key, attributed provisional label, member evidence, observation bounds,
  latest supporting observations, overlap, and coverage diagnostics. Candidate
  identity, membership revision, source freshness, and user authority are
  separate fields.
- The baseline seed is an unordered pair of distinct resolved artifact keys,
  supported together by at least two eligible primary work Sessions. Each
  Session-to-candidate membership cites its own references to both anchors.
  Local Context Documents, resolved Jira/Wiki Items, and already linkable
  Resources use source-specific identity rules; aliases of one artifact cannot
  fill both anchor positions.
- Bare container references, unresolved destinations, failed-read-only
  evidence, and duplicate occurrences do not meet the two-anchor threshold.
  Workspace, Git branch, title wording, recency, and existing organization can
  be context but cannot satisfy a missing anchor. No pre-existing Workstream or
  Thread is required.
- Two candidate seeds can share Sessions or one artifact. They remain distinct
  until explicit review; a shared member or connected Episode path never
  automatically merges them. Duplicate occurrences of the same seed collapse
  deterministically; different seeds remain explainable even if they overlap.
- An eligible Session can contribute to several candidates. Its membership
  means only that the cited portion supports the candidate; other Session
  references, lifecycle, and Focus assertions do not transfer automatically.
- Labels use attributed existing metadata, with deterministic selection and an
  honest fallback when a meaningful name is unavailable. Labels, current local
  row IDs, member order, and later supporting Sessions do not change the stable
  seed identity. A contract/identity change cannot silently retarget a review.
- Source-observed reference time owns the observed span and latest supporting
  observations. Import time and Session end are not candidate progress. Missing
  times remain unknown; a group need not have a causal path or a single tip.
  Outcome, next action, quietness, and explicit closure are not inferred from
  age or invented from titles.
- Candidate output states inferred membership separately from source evidence
  and explicit organization. It retains per-source availability, freshness,
  ambiguity, and partial coverage without treating absence as rejection.
- The contract is pure and has no database, filesystem, connector, model, or
  persistence dependency. It accepts supplied normalized facts and returns
  descriptors/diagnostics. It does not reuse the 24-Episode Focus display bound
  as a discovery rule.
- Baseline limitations are explicit: related efforts without repeated exact
  anchors may be missed, and shared reference pairs may still describe an
  unhelpful or fragmented theme. Passing this contract is not acceptance of
  candidate usefulness.

## Scope Boundary

- In: candidate and anchor identity, membership reasons, authority, observation
  semantics, overlap, deterministic normalization, invalid-input handling,
  revision/rebuild behavior, and bounded serialization.
- Out: database discovery, content extraction, candidate storage, correction or
  promotion persistence, UI, new adapters, Lens, Atlas, Thread migration, and
  any model dependency.

## Contract Surfaces

- Versioned candidate/anchor/member descriptor and safe serialization.
- Source-specific alias resolution and eligibility expectations for producers.
- Stable identity versus revision, label, availability, and observation state.
- Deterministic validation, abstention, overlap, and coverage meanings.

## Required Evaluators

- `contract`: identity, source/derived/user ownership, admission, lifecycle,
  privacy, and downstream producer/consumer completeness.
- `functional`: synthetic positive, negative, many-to-many, alias, ordering,
  missing-time, rebuild, and no-I/O cases for the pure contract.

## Entry And Exit

- Entry: supplied eligible normalized facts, with no selected Session required.
- Exit: validated provisional descriptors or explicit exclusion diagnostics;
  no durable organization or user-visible screen changes.

## State Expectations

- Supported: each retained membership has the required anchor evidence.
- Insufficient/invalid: abstain and retain bounded reason counts.
- Partial/stale/unavailable: label source and coverage state independently.
- Rebuild: unchanged anchors retain identity; removed anchors yield no active
  inferred candidate, without granting deletion authority over future reviews.

## Dependencies

- Passed FEAT-0085 through FEAT-0089 supply compatibility and regression truth.
- The owner approved this Feature boundary on `2026-09-15`.
- The former [FEAT-0091](feat-0091-deterministic-workstream-candidate-projection.md)
  consumer proposal is superseded and must not consume this contract as an
  approved production flow rule.

## Likely Affected Surfaces

- A dedicated pure candidate domain module under `src/localbrain/`.
- Synthetic contract tests and product/architecture/privacy owner sections.
- Existing Episode identity and source reference contracts as dependencies;
  no Workstream/Thread schema change in this Feature.

## Pass Or Fail Checks

- Pass only if the PRD's mixed-Session and cross-workspace positive cases work
  without existing organization or a connected Focus path.
- Pass only if aliases, duplicate evidence, a single hub, broad containers,
  similar titles, and mixed-Session bridges cannot manufacture membership.
- Pass only if label changes, added members, and input reordering preserve seed
  identity while changed membership produces a different revision.
- Pass only if every reason is inspectable and no body, raw path, opaque source
  payload, fabricated outcome, or hidden operation enters the contract.
- Fail if the next producer must guess identity, eligible anchors, overlap,
  unknown-time behavior, authority, or coverage semantics.

## Regression Surfaces

- Session eligibility and source-scoped identity.
- Focus/Trace, global workflow assertions, and Related Materials authority.
- Existing Workstreams, Threads, links, Suggestions, and source operations.

## Harness Trace

- Spec doc: [SPEC-0090](../spec/spec-0090-workstream-candidate-discovery-contract.md).
- Run: [RUN-20260915-100](../run/run-20260915-100-workstream-candidate-discovery-contract.md).
- Execution profile: `foundation-contract`.
- Latest evaluator reports: [Contract PASS](../evaluation/eval-0090-contract-workstream-candidate-discovery-contract.md)
  and [Functional PASS](../evaluation/eval-0090-functional-workstream-candidate-discovery-contract.md),
  both with complete evidence for the pure-contract boundary.
- Latest fix note: none.

## Open Review Decisions

- No unresolved implementation question for the historical pure contract.
  Product-level applicability returned to the revised PRD and then the approved
  FEAT-0095 experiment; the former FEAT-0092 usefulness route is superseded.
  This Feature neither proves automatic grouping nor authorizes that experiment.

## Continuity Notes

- `2026-09-15`: proposed from PRD-0017 product review as the first independent
  candidate foundation. No Spec, Run, implementation, or evaluation is approved.
- `2026-09-15`: owner approved the first baseline and requested execution.
  RUN-20260915-100 starts this Feature only; FEAT-0091 through FEAT-0094 remain
  drafts awaiting their own approval.
- `2026-09-15`: RUN-20260915-100 passed Contract and Functional evaluation with
  33 new contract tests and 584 total tests passing. Candidate discovery and
  usefulness are not claimed; post-run human acceptance remains pending.
- `2026-09-15`: owner returned the product direction to planning and requested
  automatic reconstruction with minimum confirmation. Technical checks remain
  valid for the unchanged pair module; its adequacy as the product's top-level
  unit is rejected, and FEAT-0091 through FEAT-0094 are superseded.
- `2026-09-15`: revised PRD analysis/validation direction approved for planning;
  current routing now points to draft FEAT-0095 boundary review. This Feature's
  technical result and implementation remain unchanged.
- `2026-09-15`: followed FEAT-0095 routing to its implemented, locally unverified
  experiment. This contract is now its comparator, not the replacement work unit.
