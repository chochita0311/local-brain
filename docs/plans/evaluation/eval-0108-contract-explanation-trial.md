# EVAL-0108 Contract: Explanation Trial

## Metadata

- ID: `eval-0108-contract-explanation-trial`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-133](../run/run-20261001-133-personal-insight-explanation-trial.md)
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `data`
- Created: `2026-10-01`

## Declared Comparison

The owner explicitly selected a previous real question about analysis execution context. Two fresh producers answer it against the same frozen current-code excerpts and common presentation instructions. One receives only an additional generic before-send response-review instruction derived from RUN-132. No answer-specific hints or expected verdicts are supplied. The usual-answer producer is not prohibited from reviewing its answer normally.

The question, source ranges, full source-file hashes, common task, intervention and condition mapping are frozen before generation. Both producers read their complete assigned packet and save one first answer without reported read/save failures. A separately randomized presentation map gives the reviewer opaque A/B labels. Producer prompts, the condition mapping and primary judgment are withheld from that reviewer.

## Checks

All sixteen checks pass: six current-source hashes, the question/evidence/intervention hashes, exact construction and hashes of both prompts, two nonempty UTF-8 answers, the review packet hash, and both unchanged first-answer hashes. The two tasks differ only by the declared temporary instruction. There is no production result-schema validation because these outputs are ordinary explanatory answers, not Insights report JSON.

No database, product CLI, application implementation, persistent guide or settings are changed. This comparison does not exercise product history, billing, live execution state or the analyst's internal reasoning. No application unit suite or browser check is run for this documentation-only comparison. All producers and the reviewer use fresh contexts and no model override; exact resolved model, effort and seed are unavailable.

Coverage is complete only for the stated input/output integrity checks. The [functional evaluation](eval-0108-functional-explanation-trial.md) owns answer quality and benefit claims. Exact evidence is retained in private `eval-20261001-133` under the existing [archive owner](../../policies/project/developer-guide.md#personal-improvement-analysis).
