# RUN-20260929-128: Personal Insight Selection Contract

## Metadata

- ID: `run-20260929-128`
- Status: `passed`
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Active Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`
- Surface: `data`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-29`
- Current Phase: post-run review complete

## Approved Boundary

The owner explicitly continued the three corrections identified after RUN-127: explain reviewed scope and candidate choice, avoid requesting supplied evidence, and choose a type from the actual work goal rather than source vocabulary. Model/reasoning options remain deferred.

Implement core v5/report v3, the full bounded type catalogue, request-feedback v2's narrowly scoped response-review trial, strict indexed conversation requests, selection/type explanations, and frozen-version compatibility. Keep historical guides intact. The primary owns architecture and integration; fresh subagents evaluate bounded outputs under the owner's existing evaluation authorization.

## Checks And Exit

- Synthetic contract regressions cover malformed targets, supplied/truncated/missing messages, all categories, explicit bounds, and legacy v2 acceptance.
- Repeat fresh guide analyses on frozen controls with expectations withheld; inspect usefulness, non-blaming type fit, successful clarification, and duplicate requests. Treat structural and semantic acceptance separately.
- Pass the foundation contract before the dependent FEAT-0110 renderer/UI change. Preserve private evaluation outputs under the existing runtime evaluation owner; clean exact staging after verified preservation.

## Result

- Core v4/report v3 passed strict contract tests and nine control outputs across three fresh rounds. A separate reviewer found the trials/abstentions grounded, with one minor criterion-timing imprecision.
- Two fresh analyses of the same new production-sized frozen sample selected different episodes and both requested omitted context. Their targets were valid; one used raw indices as prose message numbers. Core v5 preserves v4 and adds one rule reserving display numbering for the product.
- A third fresh real-sample analysis with core v5 used no prose message numbers, requested only three genuinely omitted messages, and passed a bounded independent follow-up review. This is one follow-up observation, not a reliability estimate.
- [Contract](../evaluation/eval-0108-contract-selection-contract.md): `PASS`. [Functional](../evaluation/eval-0108-functional-selection-contract.md): `PASS WITH SUGGESTIONS`, partial evidence. The primary accepts the bounded correction; real useful discovery and owner benefit remain unproved. The earlier RUN-127 failure and intermediate numbering defect remain recorded.
- Twelve guide tests pass within the 30 personal-insight regressions. The private `eval-20260929-128` archive owns exact inputs, outputs, validation, and reviews; tracked artifacts contain sanitized findings only. RUN-129 consumes this accepted contract.
