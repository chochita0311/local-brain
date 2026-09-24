# EVAL-0100: Source Claim Extraction And Binding Trial — Functional

## Metadata

- ID: `eval-0100-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `FAIL`
- Evidence Coverage: `complete`
- Run: [RUN-112](../run/run-20260923-112-source-claim-extraction-and-binding-trial.md)
- Attempt: `1`
- Feature: [FEAT-0100](../feature/feat-0100-source-claim-extraction-and-binding-trial.md)
- Spec: [SPEC-0100](../spec/spec-0100-source-claim-extraction-and-binding-trial.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, `infra`
- Created: `2026-09-23`

## Measured Candidate

One frozen Qwen3-8B candidate, verified installed assets, MPS/bfloat16/eager,
greedy non-thinking, with unchanged prompts, source/reference cases, scoring and
implementation throughout generation and replay. The original four development
and twelve composition cases remain separate from twelve new claim histories.
These are 28 synthetic engineering controls, not random corpus samples or
independently blinded observations. No population accuracy or statistical
significance is inferred.

| Cohort | Extraction protocol accepted | Conditioned full passes | Conditioned negative / positive passes | End-to-end output |
| --- | --- | --- | --- | --- |
| Original development | 0/4 | 1/4 | 1/2 and 0/2 | 0/4; all prerequisite-skipped |
| Original composition | 0/12 | 1/12 | 1/8 and 0/4 | 0/12; all prerequisite-skipped |
| New claim histories | 0/12 | 1/12 | 1/6 and 0/6 | 0/12; all prerequisite-skipped |

Every stage/cohort gate fails. Extraction is rejected before semantic admission
in all cases: fifteen `INVALID_OUTPUT`, ten `INVALID_ANCHOR`, three
`MISSING_REFERENCE`. These are the first validation failures, not mutually
exclusive underlying defects or a zero-percent semantic-accuracy estimate.
End-to-end binding executes zero calls because all 28 extraction prerequisites
fail; each skip remains in its denominator and stored observation. No gold answers
are substituted to make that pipeline run.

The independent reference-conditioned diagnostic supplies authored correct claims
and target rosters. It produces fifteen structurally valid answers; seven fail
binding evidence, two JSON output, two reference-roster preservation and two
packet vocabulary/shape. Only `dev_unknown`, `proof_unknown_goal_activity` and
`claim_new_occurrence` satisfy every frozen predicate. The three passes demonstrate
neither claim extraction nor target discovery. No positive case fully passes.

## Primary Semantic Review

The primary agent reviewed all 28 extraction and all 28 conditioned raw responses
with their source/reference cases and per-case assessments. Invalid raw text is
diagnostic evidence only: it was not repaired, parsed leniently or admitted.

- Extraction frequently appends invalid closing delimiters, invents generic
  message IDs for paired sources, or uses the message's position as the quote's
  occurrence number. Unique quotes after the first message consequently fail
  exact-span lookup. No first-match fallback masks these mistakes.
- Raw content also promotes thanks, unspecified work, goals explicitly absent
  from the record, and an instruction example into goals. Explicit completion or
  pending status often becomes a goal; negated execution becomes action/outcome;
  cancellation becomes retraction. Fixing JSON alone cannot establish correctness.
- Compound performed-action/result statements lose a predicate, planned actions
  merge into a goal, and source-provided versus unknown effective dates are
  confused. All such errors remain visible even when an earlier format/locator
  failure is the recorded rejection code.
- Conditioned answers copy simple rosters but omit action/result bindings and
  all proposed opening/fulfillment effects. A requested execution is not correctly
  reconciled with its reported failed result; plan-only steps lack their opening
  state. Supplying correct premises does not make state reconstruction reliable.
- Conditioned pair responses abstain despite explicit separate goals or topical
  similarity. Longer-gap continuation responses lack bilateral binding evidence
  or use invalid relation vocabulary. Reopen/correction/dispute responses omit
  required target evidence or supported links. Actual quotes alone do not prove
  those relationships.

The report-bound primary review is explicitly failed. Empty/withheld output makes
the aggregate no-unsafe-closure flags vacuously true, not evidence of a useful safe
pipeline. The all-unresolved baseline fails every cohort gate as required. No
post-answer prompt, reference, threshold, parser, scorer or model change was made.

## Execution, Replay And Coverage

The 56 generation attempts produce 58,349 input and 8,981 output tokens in
771.820904 cumulative launch seconds, including asset verification/preflight/load.
There is no runtime exception, timeout, OOM or output truncation. The longest
generation takes 54.439 seconds; the largest output has 558 tokens. Peak sampled
MPS driver allocation is 22,051,340,288 bytes, not total memory usage. These
measurements do not isolate a model-capacity or hardware cause for the failures.

Actual generation-free replay reuses all 84 observations, including 28 skipped
dependencies. All observation hashes, configuration/development/semantic digests,
cumulative calls/time and token counters match a separately captured pre-replay
snapshot. The failed primary receipt survives. No failure is resampled.
Forty-two new tests pass in both runtimes; full regression runs 942 tests with
zero failures and one existing optional graph skip. The v1 parity check and
[Contract evaluation](eval-0100-contract-source-claim-extraction-and-binding-trial.md)
establish mechanics, not model quality.

Evidence is complete for the approved failed development trial. The conditional
ten-case holdout is ineligible and unconsumed, not independently blinded; private
corpus quality and UI usefulness are outside this evidence. No related model job
or task scratch remains. The owned outside-Git report retains finite evaluation
evidence under the existing 30-day inactive-retention rule, not indefinite storage.

## Disposition

FAIL is the semantic candidate's failed acceptance, not an unfinished calculation
or installation fault. Keep FEAT-0100 and FEAT-0098 admission blocked. Recommend
`planning-review` of the model-to-host output/evidence interface and decomposition
before another bounded candidate: locating source evidence and deciding meaning
need separate error budgets, and serialization success cannot substitute for
meaning. This recommendation is untested, not an approved implementation or a
promise that constrained output, another prompt, a larger model or training fixes
the problem. Do not weaken gates, consume holdout, regenerate the same failures,
start a private job, or replace automation with routine user classification.
