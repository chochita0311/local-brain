# FEAT-0097: Replayable Full-Session Simulation

## Metadata

- ID: `feat-0097`
- Status: `passed`
- Type: `foundation`
- Surface: `mixed` (`data`, `infra`)
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-22`
- Updated: `2026-09-23`
- User review status: owner explicitly requested execution of the discussed
  recalculable simulation using all stored Sessions rather than 60 examples.

## Goal

Establish an executable, local-only whole-Session simulation whose input,
embedding and grouping stages can be independently replayed. It is not a
production Workstream replacement or a semantic-quality acceptance claim.

## Acceptance Contract

1. Enumerate every stored Session in one read-only SQLite snapshot. Analyze all
   nonempty user/assistant message text in eligible primary/full work Sessions;
   there is no Session, message-count or prefix sampling cap. Account separately
   for excluded Sessions, non-message events, empty text and unknown dates.
2. Preserve source locators, attribution and exact content hashes. Chunking
   covers every admitted character; model token windows cover every token.
   A mixed Session may contribute chunks to multiple experimental groups.
3. Use explicitly selected, verified, already-local model assets offline. Do
   not download, train, write Foundry state or send private material externally.
   Cache keys include text, model/runtime and chunking identities.
4. Commit embedding progress in batches. An interrupted run resumes with valid
   cache entries; unchanged replay performs no new encoding. Source changes
   invalidate affected inputs; grouping-only changes reuse compatible vectors;
   model changes cannot reuse incompatible vectors.
5. A private report accounts for all current input and distinguishes complete
   processing from unassessed semantic quality. Communities at two resolutions
   are affinity candidates, not proven work identities or causal lineage.
   Replays have deterministic input/configuration identities and comparison
   metrics; they never train from their own inferred output.
6. Single-writer locking, safe owned output, atomic report replacement, explicit
   source revalidation, finite cache/report retention and source nonmutation
   are verified. Prior valid results survive a failed run, but are not described
   as the current result. Excluded/removed source entries leave the current
   simulation and their unused derived caches are pruned.

## Scope Boundary

In: CLI, private simulation SQLite/cache/report, local embedding adapter,
two-resolution semantic grouping, replay/repair tests, current-data execution.

Out: model training/download, new source registration, document-body expansion,
external connectors, new map UI, changes to `/auto-work`'s historical sampled
viewer, production identity/correction ledger, migration and legacy cleanup.
The report is a downstream consumer contract; it is not a new product screen.

## Surface Lanes

- Data: input inventory and cache ownership; precedes model and grouping work.
- Infra: explicit CLI and local runtime adapter; consumes the data contract.
- Primary agent owns both lanes; Contract and Functional evaluate both.

## Dependencies And Regression Surfaces

- Existing Session privacy/eligibility contract and read-only database helper.
- Optional existing local Sentence Transformers runtime and model assets.
- FEAT-0095/0096 remain unchanged model-free sampled comparators.
- All original Session, Workstream and Thread records remain untouched.

## Harness Trace

- Spec: [SPEC-0097](../spec/spec-0097-replayable-session-simulation.md)
- Run: [RUN-20260922-103](../run/run-20260922-103-replayable-session-simulation.md)
- Required checks: full coverage beyond 60 Sessions/32 messages/1,000 chars;
  replay, interruption, changed input, removed/revoked source, grouping change,
  model isolation, source immutability, output ownership and offline execution.
- Evaluation: [Contract](../evaluation/eval-0097-contract-replayable-session-simulation.md),
  [Functional](../evaluation/eval-0097-functional-replayable-session-simulation.md).

## Continuity Notes

- `2026-09-23`: [RUN-113](../run/run-20260923-113-full-history-simulation-replay.md)
  closed the real replay gap: unchanged and grouping-only runs used zero encoder
  calls, restored grouping matched exactly, and original DB/WAL bytes stayed
  unchanged. Ordered graph insertion fixes cross-process community instability.
  Technical acceptance is complete; semantic usefulness remains unassessed.

- `2026-09-23`: the relation-first review proposed
  [FEAT-0101](feat-0101-full-history-affinity-inspection-contract.md) as the next
  whole-history consumer foundation. It explicitly depends on completing this
  Feature's real unchanged/grouping-only replay evidence and source freshness
  checks. Planning performed neither check; this Feature is not newly passed.
- `2026-09-23`: full backfill publication and coverage accounting were verified;
  later source additions make the report stale, without detected changes to its
  existing content. The owner selected the independent context-model trial next.
  The Run returned to planning and this boundary remains approved for remaining
  real replay verification, not actively executing or passed. Cached vectors
  remained intact; the next execution at that time was FEAT-0098.
- `2026-09-22`: implementation and synthetic replay verification pass. The
  private full-population inventory completed, installed-model inference began,
  and actual interruption/resumption reused saved vectors and committed further
  batches. The first full embedding/grouping backfill is still running. Do not
  mark this Feature passed or claim real-data quality/completion yet.
