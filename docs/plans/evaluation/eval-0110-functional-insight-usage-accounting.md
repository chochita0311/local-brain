# EVAL-0110 Functional: Insight Usage Accounting

## Metadata

- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Evidence Coverage: `partial`
- Run: [RUN-125](../run/run-20260928-125-personal-insight-usage-accounting.md)
- Attempt: `1`
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md), usage accounting correction
- Execution Profile: `backend-product`
- Lanes: `data`, `backend`
- Created: `2026-09-28`

## Evidence And Limits

- Synthetic tests cover selected-source/All totals and history, unassigned Project breakdown, ordinary Session/detail/evidence exclusion, inclusive cached input, reasoning, malformed/missing fields, unknown models, aggregate pricing limits, stable replay, native cleanup/repair, legacy recovery, and startup interruption.
- A mocked CLI process exercised the actual asynchronous executor. Invalid report validation and cancellation both retained emitted usage and its estimated cost. Restart recovery made no subprocess call.
- A temporary real HTTP server and isolated headless Chrome rendered $0.78 and 110K tokens for the synthetic Codex source; Project was `Unassigned` and the work-Session count was zero. Sessions exposed no analysis row or detail link, while Insights retained its Run history. All browser requests were reads.
- The bounded 97-test set had 89 passes and eight failures that reproduce from unchanged HEAD: six pricing/snapshot expectations and two schema-presentation expectations. No new regression was found. Data-model, generated-artifact, privacy, and whitespace checks pass.
- No real model execution or private Session transfer occurred. Actual CLI/provider entitlement, emitted usage on early process failure, and report usefulness are unverified. This gap is non-blocking for the local accounting correction and remains a separate owner-started operational check.
