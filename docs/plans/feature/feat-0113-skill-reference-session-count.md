# FEAT-0113: Skill Reference Session Count

## Metadata

- ID: `feat-0113`
- Status: `passed`
- Type: `product`
- Parent PRD: [PRD-0005](../prd/prd-0005-workflow-and-skill-intelligence.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `data`, `backend`, `frontend`, `docs`
- Required Evaluators: `contract`, `functional`, `design`, `ux-heuristic`
- Created: `2026-10-04`

## Owner Boundary And Acceptance

The owner rejects language-dependent application declarations and approves a simple use-or-reference Session metric. Count each normalized skill at most once per source and native Session, across requests and evidence types. Admit native invocation/context, completed instruction reads, named references in visible conversation and identifiable executions of scripts belonging to a source-established skill. Match skill identifiers without classifying application wording. Preserve provenance, historical observations, corrections and maintenance exclusion. Missing unsupported evidence is accepted; no activation instrumentation or external analysis is required.

Show the metric as a use/reference Session count within the existing Insights surface. Fullstack data/backend owns extraction and projection; frontend owns labels and units; docs owns the changed contract. Review the actual local application at desktop and narrow widths. Automated tests are not requested.

## Trace

- Replaces the displayed [FEAT-0112](feat-0112-session-skill-use-estimate.md) estimate without rewriting its historical receipt.
- Spec: [SPEC-0113](../spec/spec-0113-skill-reference-session-count.md)
- Run: [RUN-140](../run/run-20261004-140-skill-reference-session-count.md)
- Evaluation: [EVAL-0113](../evaluation/eval-0113-skill-reference-session-count.md), with partial regression coverage.

## Final Verification

The owner subsequently requested full closeout, delegated document reviews and publication. The dated final supplements in [RUN-140](../run/run-20261004-140-skill-reference-session-count.md#final-owner-requested-verification-2026-10-04) and [EVAL-0113](../evaluation/eval-0113-skill-reference-session-count.md#final-verification-supplement-2026-10-04) record the later automated regressions and review evidence without rewriting the initial manual receipt.
