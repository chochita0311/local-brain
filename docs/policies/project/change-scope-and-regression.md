# Change Scope And Regression Control

## Ownership

This guide owns LocalBrain's practical controls for preserving existing behavior
while delivering a bounded change. [Execution Loop Governance](../harness/execution-loop-governance.md)
continues to own approval, failure routing and Run lifecycle. Product contracts
remain with their [existing owners](../../README.md#feature-contracts-and-development-operations).
Apply this guide to fixes, feature work and refactors; a nearby file or shared
helper is not authority to change another feature's behavior.

## Establish The Boundary Before Editing

Keep the record proportionate to the work in the existing Run, scoped task record
or session for a small fix; this guide adds no separate artifact or parallel
planning system. Record:

- Requested result, permitted behavior changes and affected producer/consumer
  paths. Identify dependencies needed to deliver that result.
- Existing behavior to preserve, with its current policy, accepted correction
  and relevant test. Read current implementation and contracts; an older plan's
  silence does not reverse a later approved correction.
- Initial Git changes and relevant verification baseline, so concurrent or
  pre-existing edits and failures remain distinguishable from this task.
- The checks that can establish the result and adjacent invariants, including
  the runtime/artifact that the user will actually use.

A minimal change is the smallest complete, coherent result, not the fewest files
or lines. When the result requires dependent updates to consumers, schema,
generators, scripts, fixtures, generated artifacts or owner docs, those edits must
be completed in the same work. Verify the affected producers and consumers; leaving
a required dependent update undone is an incomplete change.

| Situation | Required response |
| --- | --- |
| Necessary dependent edits preserve current contracts. | Make the causally required edits and verify preserved behavior for other consumers. Needing another module or feature is not itself a reason to request permission. |
| Intentional behavior changes across features are already agreed. | Proceed with the coordinated changes and update each changed fact's actual owner. Preserve the other contracts outside that agreed change. |
| An unexpected difference appears on an affected path. | Compare it with current approved intent. If it violates that contract, diagnose the causal path and correct the necessary parts. If it is an already approved intentional change, preserve it. |
| Cause or impact is still unknown. | Separate observed facts, hypotheses, checks and results. Investigate before assigning a cause or selecting a repair. Continue independent work whose contracts and authority are clear; do not implement through consequential ambiguity. |

Honor active lane restrictions and the
[execution loop's decision and return rules](../harness/execution-loop-governance.md#practical-decision-rule).
Ask the user only for a consequential new product, scope, acceptance or ownership
decision that existing authorization does not resolve. Record the consequence and
use that existing routing before implementing the affected change. An already
agreed cross-feature change does not by itself reopen approval.

A symptom observed after a change does not establish causation. Input data,
environment differences or coverage gaps can expose an existing defect even when
no feature changed. Follow the relevant producer/consumer path and check the
inputs, implementation and delivered runtime needed to distinguish explanations.
A reproduced path establishes behavior under the checked conditions; it does not
by itself establish the historical start time or introducing commit.

Keep unrelated improvements as separate proposals. Physical file adjacency or a
shared helper alone does not establish a causal need to include an edit.

## Preserve Contracts Across Shared Code

- Trace a changed shared parser, query, template, asset or migration to its
  callers and stored outputs. Use the narrowest complete change across the
  necessary owning lanes; a presentation correction must not reset ingestion,
  Usage, settings or curated state.
- Retain source identity and provenance, and preserve null/unavailable meaning.
  Do not turn unknown evidence into zero. Keep original source evidence distinct
  from its derived repair lanes; do not rebuild every lane merely to fix one lane.
- Never copy an old file wholesale over current code to restore one behavior.
  A targeted revert is appropriate when it fixes the established cause and
  preserves current contracts and unrelated work. Apply the smallest supported
  correction and inspect the complete resulting diff. Preserve unrelated user
  and concurrent edits.
- Keep provider originals read-only. A missing history report requires comparing
  current files, source registration, stored derived records and native metadata
  before selecting a repair. Inventory container extensions, including supported
  compressed originals such as `.jsonl.zst`; absence of `*.jsonl` alone does not
  establish missing history. Report unreadable or unsupported containers as such
  rather than calling them absent. A metadata row or cumulative counter is not a
  substitute for dated direct usage events. Restore only from identified original
  evidence under the source/recovery contract; a Sync cannot recreate missing bytes.

Follow [Session synchronization](session-ingestion.md#session-synchronization)
for independent Session/Usage/reference repair and numeric revision admission,
and [Usage normalization and repair](usage-and-cost.md#usage-normalization-and-repair)
for frozen price and Project attribution and transactional, idempotent repairs.
A catalog-only price addition does not require a Session/Usage normalizer bump or
forced rescan; use the [pricing repair boundary](usage-and-cost.md#gpt-61-terra-pricing).
[Retained native history and presence](session-ingestion.md#retained-native-history-and-presence)
and [Adapter-specific rules](session-ingestion.md#adapter-specific-rules) own
presence, retention and container replacement. Those owners define exact
eligibility, reconciliation and repair rules. This guide does not independently
change source registration, retention, snapshot or privacy semantics. Explicit
eligibility corrections follow the ingestion owner; Local Context keeps its own
file-deletion boundary.

## Verify The Changed And Preserved Behavior

Select meaningful synthetic regression cases from the changed boundary and its
actual consumers. For ingestion/persistence changes include affected sources,
legacy/current evidence, partial input, failure rollback, retained IDs/snapshots
and a second unchanged synchronization or startup when applicable. For Usage
changes include personal/company source separation, month/date boundaries,
direct maintenance/subsession inclusion, synthetic/replay exclusions, and complete,
partial and unavailable pricing as relevant to the changed path. Reuse existing
checks when they already cover an invariant; do not add tests that merely restate
implementation structure or assert incidental markup.

Run the smallest relevant checks first, then required repository checks. Keep
failures visible and classify whether the task caused them. Apply design and
interaction evaluation when visible behavior is affected; source inspection or a
Python test alone does not verify the rendered route.

Before completion:

1. Inspect all changed paths and substantive diff hunks against the declared
   result and dependencies. Remove task-owned unrelated edits; preserve others'
   changes. Investigate any unexplained regression or broadened behavior before
   declaring success.
2. Update each changed fact's owner and leave earlier execution evidence intact.
   Do not rewrite a settled requirement merely to make a failing test pass.
3. Verify the delivered runtime uses the intended code/assets and persisted
   contract. A passing source checkout does not establish that a running server
   or packaged app loaded it. Rebuild/restart only within the task's authority;
   otherwise report the unapplied delivery step.
4. Report what changed, what evidence passed, what remains unverified, and any
   recovery dependency. Distinguish a restored behavior from an unlocated source
   and a passing evaluation from human acceptance. Remove task-owned scratch.

## Activation And Limits

`AGENTS.md` routes repository work here, so the user need not repeat this guide
with every task. The executing agent applies it at work entry and closeout.
Existing tests provide automated checks for the behavior they exercise; this
document is an operating instruction, not an automatic Git write blocker or proof
that future changes cannot regress. Add a new automated guard only when an
observed failure and a stable contract justify it within an authorized task.
