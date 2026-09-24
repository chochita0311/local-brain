# RUN-20260923-111: Source Claims And Work State Projection

## Metadata

- Run ID: `run-20260923-111`
- Status: `passed`
- Attempt: `1`
- Feature: [FEAT-0099](../feature/feat-0099-source-claims-and-work-state-projection.md)
- Spec: [SPEC-0099](../spec/spec-0099-source-claims-and-work-state-projection.md)
- PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `data`
- Required Evaluators: `contract`, `functional`

## Approved Boundary And Loop

The owner approved implementing the proposed model-free synthetic contract after
the structure review. The primary agent performs Spec → Build → Contract →
Functional review sequentially. This is a pure supplied-evidence projector, not
extraction, model admission, persistent storage, private processing or UI work.
Existing dirty changes and historical trial results are preserved.

## Execution

Spec fixed packet shapes, time/scope/authority rules, bounds, transition semantics
and required scenarios before implementation. Eighteen synthetic packets with
expected states were authored before building the projector. `work_state.py`
now implements pure validation, source/interpretation identity, partial-order
reported-state reduction, reversible claim displacement, cutoff and replay.
The [policy owner](../../policies/project/source-claims-and-work-state.md) documents
the non-persistent boundary; architecture routes to it.

## Evaluation And Regression

- [Contract](../evaluation/eval-0099-contract-source-claims-and-work-state-projection.md):
  `PASS`, complete evidence for this pure contract.
- [Functional](../evaluation/eval-0099-functional-source-claims-and-work-state-projection.md):
  `PASS`, 50 new tests and full application regression of 900 tests, zero failures,
  one existing optional graph-dependency skip. In-run review added edge-case
  protection without changing the eighteen scenario expectations or old trials.
- No new runtime consumer exists: only synthetic fixtures/tests import the module.
  Existing model prompts, tests, source/DB/route code and durable assertions are
  unchanged. No schema/value artifact generation or browser evidence is needed.

## Final Verification And Cleanup

- Final full application regression after code review: 900 tests in 10.832 seconds,
  zero failures, one existing optional graph-dependency skip. Fifty tests cover
  this Feature, including 18 synthetic scenarios and deterministic permutations.
- Catalog build/check pass; all 915 local Markdown links across 14 changed
  documents resolve; privacy scan passes for 988 candidate files. Tracked diff
  and nine newly added file whitespace checks pass.
- Final source SHA-256: `work_state.py`
  `b67845d95dc0aa4fc0a34aa368af0457f1493f4d7e00c6124367798ede1216f4`;
  fixtures `d2e8e6fffad0ac3dedae6e59f970f004475fd41dd59460e2e857f9b3e62330fb`;
  tests `4967fc63094d66d235dc981774f42db46e85eba41abad1dda4ae5a34eb873d52`.
- No task scratch, report cache or persistent projection was created. Exact new-
  module/test bytecode paths are absent in both repository and configured shared
  cache; no shared cache was deleted. Final verification used disabled bytecode
  writes. All test processes completed; no retained temporary artifact or active
  generation remains. Existing user work and finite-lived earlier evaluations
  remain untouched.

## Acceptance Boundary

All contract/functional scenarios and full regression pass. No model, private DB,
network, browser or private runtime was used. Model accuracy, automatic target
identity, all-history reconstruction and the intended map remain unproven.

## Handoff

Run complete; no active calculation. Accept or return this foundation based on
the reported contract, not as automatic grouping/UI acceptance. The next proposed
work is a bounded extraction/binding adapter review: require models to provide
source claims and supported target links, then score those upstream judgments
separately from deterministic projection. This Run does not approve another
model trial or private processing and does not change FEAT-0098 admission.
No routine Session-by-Session approval or new 60-Session processing cap is added.
