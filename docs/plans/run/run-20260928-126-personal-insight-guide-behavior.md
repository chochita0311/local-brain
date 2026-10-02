# RUN-20260928-126: Personal Insight Guide Behavior

## Metadata

- ID: `run-20260928-126`
- Status: `passed`
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Consumer: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Active Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`, with `docs-content` for guide refinement
- Surface: `data`, executable guide content
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-28`
- Updated: `2026-09-29`

## Goal And Authorization

The owner requested three independent subagent analyses, independent advice-quality evaluation, evidence-led guide corrections, and three comparable analyses after correction. This extends the earlier synthetic checks to model behavior with a frozen private evidence sample. It authorizes bounded guide refinement; applying the generated personal recommendations remains a separate ordinary work task.

## Comparison Contract

- Freeze the product's current `discover` manifest, selected guide bundle, exact prompt, and result schema before the first producer. Keep private evidence and generated advice outside Git.
- Give each producer a fresh context with the same input, schema, inherited model binding, and file-transfer wrapper. Producers receive neither earlier answers nor the evaluation rubric or proposed correction.
- Use subagents as an analysis-engine surrogate. This does not establish actual CLI isolation, billing, end-to-end Run execution, or equivalence to the configured product model. Sampling settings and a seed are not exposed by the subagent interface.
- Have separate evaluation subagents inspect admitted evidence and produced claims. The primary agent owns final interpretation, correction scope, persistence, and integration.
- Compare supported observations and proposed actions separately from wording and category labels. Three samples per revision can reveal variation; they cannot establish long-term stability or improvement in the owner's work.

## Predeclared Success Checks

1. The unchanged product validator admits the result, including citations, recurrence scope, selected categories, bounded evidence requests, and unconfirmed outcomes.
2. Evidence supports the claimed goal and friction. Healthy iteration, assistant mistakes, source instructions, and analysis-generated material are not diagnosed as a user's defect.
3. Counterexample checks and coverage limits are concrete and honest. Missing context can produce abstention or a bounded evidence request.
4. Suggestions are small, actionable, reversible, and tied to an owner-checkable follow-up, with a plausible benefit and stated effort. Repeating an already visible practice is not automatically a new improvement.
5. Revised guidance preserves valid findings and honest no-finding outcomes. A justified abstention is successful behavior, not a lower-yield failure.

## Execution Record

- Captured the active core v2, selected v1 playbooks, product schema, and private evidence before edits. Three fresh producers returned bounded evidence requests. Independent content review accepted the reasoning; the product validator rejected one output because it cited six references where the hidden limit was five.
- Added core v3 with the existing output limits and updated the active loader. Historical core v2, all earlier core rules, selected playbooks, report shape, and validator are preserved. Three new producers on unchanged evidence all passed validation and again requested missing evidence. A separate reviewer rated two PASS and one PASS WITH SUGGESTIONS for requesting more supporting material than initially necessary.
- Before and after the correction, synthetic supported-opportunity and normal-work controls retained a small actionable trial and honest no-finding outcome respectively. The primary agent reviewed these controls. All planned cases completed; no producer output was manually repaired.
- Six main outputs had different wording but substantially shared the candidate and cautious conclusion. Revised runs used the same source anchors; their follow-up paths varied. No general stability or actual owner benefit is established by this sample.
- Documentation work used incremental ownership review and minimal reshaping. Instructions remain in the executable package; the consumer specification now points to that owner, and the Developer Guide identifies private evaluation retention separately from product history.

## Evaluation And Follow-Up

- [Contract](../evaluation/eval-0108-contract-guide-behavior.md): `PASS` for the observed output-limit correction and version integration.
- [Functional](../evaluation/eval-0108-functional-guide-behavior.md): `PASS WITH SUGGESTIONS`, partial evidence beyond the completed surrogate cases. The focused personal-insight suite passes 25 tests.
- The additional-document request in one output is a non-blocking opportunity to reduce user effort. It remains frozen evidence, not a reason to add a general guide restriction.
- Missing neighboring context and post-change outcomes are consistent with the stated abstentions; this comparison did not establish their causal contribution. Targeted evidence expansion and admission review remain investigation candidates under the PRD's existing future scope. [RUN-127](run-20260929-127-personal-insight-context-comparison.md) compares bounded neighboring context while preserving the guide and category selection.
- No product CLI analysis, actual Run history row, owner intervention, or confirmed personal improvement was produced by this experiment. Product execution, billing, broad category coverage, and long-term model behavior remain outside this evidence.

## Evidence And Retention

Private inputs, outputs, and detailed comparisons belong in the local runtime data area. Only sanitized contract and behavior conclusions belong in tracked evaluation documents. Task staging files are removed after their durable copies and checks are complete.

The private archive was copied and verified before the task-owned staging directory was removed. No temporary artifact remains required by the completed evaluation.
