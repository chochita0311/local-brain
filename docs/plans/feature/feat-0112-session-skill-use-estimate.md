# FEAT-0112: Session Skill Use Estimate

## Metadata

- ID: `feat-0112`
- Status: `passed`
- Type: `product`
- Parent PRD: [PRD-0005](../prd/prd-0005-workflow-and-skill-intelligence.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `data`, `backend`, `frontend`, `docs`
- Required Evaluators: `contract`, `functional`, `design`, `ux-heuristic`
- Created: `2026-10-03`

## Later Owner Direction

On 2026-10-04 the owner rejected language-bound declarations and approved [FEAT-0113](../feature/feat-0113-skill-reference-session-count.md), counting each skill once per use/reference Session. This completed artifact retains its original evidence and boundary.

## Goal And Owner Boundary

The owner returned the load ranking because inspection reads inflated it. On 2026-10-03 the owner clarified that an approximate measurement of automatic skill use from existing Sessions is sufficient; new activation instrumentation is outside the requested scope. Use native invocation/context evidence and conservative assistant application declarations in Korean and English. A file read alone must not increase the displayed count. Neither a literal user mention nor a declaration detector is a complete measurement of application.

## Acceptance

- Retain existing load evidence. Add bounded declaration evidence only for skill identities established by native loads or completed skill reads within the same Session.
- Include current, future-start and past assistant application declarations, independently of a user's `$` mention. Recognize Korean and English forms, lists and unambiguous plugin aliases; exclude code, quotations, examples, negation and conditional recommendations where recognized.
- Rank native Claude `Skill` calls, Codex generated skill contexts and admitted declarations. Exclude standalone reads. Count a skill once per identifiable request and preserve source provenance, correction, maintenance exclusion and historical retention.
- Apply the same versioned extraction on available historical files and later Session syncs; do not run paid analysis or add runtime hooks.
- Label the existing Insights metric as an estimated use count and briefly explain that automatic uses are included while reads alone are excluded.

## Dependencies And Evidence

[FEAT-0111](feat-0111-automatic-skill-load-observation.md) remains the completed historical load extension and supplies read identities and request grouping. Data/backend precede frontend copy; docs describe the accepted uncertainty. The primary owns implementation and all review roles. Inspect the served ranking and narrow/desktop containment. Automated tests are not requested for this continuation.

## Harness Trace

- Owner direction: the current 2026-10-03 clarification accepts measurement error and asks for automatic use from existing Sessions without a large instrumentation design.
- Spec: [SPEC-0112](../spec/spec-0112-session-skill-use-estimate.md)
- Run: [RUN-139](../run/run-20261003-139-session-skill-use-estimate.md)
- Evaluation: [EVAL-0112](../evaluation/eval-0112-session-skill-use-estimate.md), with explicit partial regression coverage.
