# EVAL-0108 Contract: Decision Threshold

## Metadata

- ID: `eval-0108-contract-decision-threshold`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-131](../run/run-20261001-131-personal-insight-decision-threshold.md)
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `data`
- Created: `2026-10-01`

## Version And Frozen-Input Checks

Core v6 owns the decision between a future reversible trial, an action-dependent evidence request, and no actionable finding. Request-feedback v3 introduces the additional, explicitly limited route through a later concrete correction and corresponding assistant admission; v4 clarifies its existing output-review timing after one observed scope failure. This is a declared admission change under SPEC-0108, followed by a bounded adherence correction. It does not reinterpret historical v2 results as satisfying the new route.

The active package uses core v6/request-feedback v4 and retains report v3, all eleven playbooks, and unchanged versions and digests for the other ten playbooks. Historical core v5 and request-feedback v2/v3 resources remain byte-for-byte unchanged. Historical core v4/v5 still use report v3; core v2/v3 retain report v2 compatibility. No schema or provider behavior was changed.

The real-input manifest is byte-for-byte identical to RUN-130's supplemented condition. No database or additional conversation retrieval occurred. The three historical raw outputs retain their prior hashes. Each attempt's guide bundle, schema, prompts, prompt parts, and relevant code/resource hashes were frozen before execution and checked afterward. Seven producers ran in the first attempt; three new real-input producers ran after the separately declared scope correction. The response schema is unchanged from the baseline. The first attempt's changed Python source is retained as a snapshot, and its guide resources remain intact.

## Output And Regression Checks

- All thirteen raw first outputs validate against their respective manifests and guide bundles: three historical baseline answers, three initial revised real-input answers, four synthetic controls, and three scope-corrected real-input answers.
- The sole new evidence request, in the missing-goal control, targets an omitted, in-range message. It requests no supplied complete message. The validator does not establish the semantic necessity of that request; the functional evaluation owns that judgment.
- The focused personal-insight suite passes 32 tests, including 14 guide checks, after each revision. It covers guide packaging, report validation, execution integration, and usage attribution within the existing synthetic test boundaries.
- New guide-text assertions check the presence of the intended decision and exclusion rules. They are static checks, not proof of model behavior. A test assertion initially mismatched a phrase and was corrected; the initial log note and passing result are retained. Producer answers were never repaired after validation.

## Coverage And Route

Coverage is complete for this bounded version, frozen-value, thirteen-output, and regression check. It does not establish universal invalid-input rejection, semantic usefulness, unchanged behavior across every old package, or a live provider invocation. The [functional evaluation](eval-0108-functional-decision-threshold.md) owns action quality, the preserved initial failure, and both independent reviews.

Private `eval-20261001-131` retains exact packets, first answers, validation, execution receipts, and checks under the [evaluation archive owner](../../policies/project/developer-guide.md#personal-improvement-analysis). Route: `pass` for the bounded contract check.
