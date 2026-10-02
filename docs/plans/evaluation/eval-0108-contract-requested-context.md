# EVAL-0108 Contract: Requested Context

## Metadata

- ID: `eval-0108-contract-requested-context`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-130](../run/run-20260929-130-personal-insight-requested-context.md)
- Feature: [FEAT-0108](../feature/feat-0108-personal-improvement-guide-and-finding-contract.md)
- Spec: [SPEC-0108](../spec/spec-0108-personal-improvement-guide-and-finding-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `data`
- Created: `2026-09-29`

## Frozen Input And Output Checks

The primary preserved the preceding core-v5 evaluation's original manifest, guide bundle, response schema, and prompt byte-for-byte as condition A. Condition B retains every original excerpt and session ordering, adds exactly the three omitted messages requested by the preceding report, and adjusts coverage and explicit supplement provenance. Both conditions retain discovery intent, core v5/report v3, and the same eleven playbooks.

Before admitting the supplement, a read-only database transaction confirmed source eligibility, the frozen cutoff, the target's eligible message count, and the original anchors' identities, roles, sequence, timestamps, and text revisions. Requested positions were omitted and in range. Each added message fits the initial excerpt-length limit; total excerpts and characters remain within the initial global caps. Six supplied messages in one Session exceed the initial three-message selector, so B is explicitly an experimental supplement, not a newly accepted production selection policy.

Three fresh producers per condition produced six raw first answers. All six pass `validate_guided_result` against their corresponding frozen manifest and bundle. Every indexed request identifies an admitted, omitted position; none re-requests any of the supplied complete messages. All packet hashes and prompt-part concatenations still match after execution. Raw answers were retained without validation-driven repair.

## Limits And Route

Coverage is complete for these frozen-value and six-output checks. Formerly omitted messages have no text revisions in the original archive: their newly frozen text was read at evaluation time under the original event-time cutoff, while historical revision equality is established only for the original anchors. This limits historical reconstruction without changing the admitted supplement.

This does not establish semantic usefulness, all possible invalid-input handling, production retrieval, a provider CLI run, or owner benefit. Application behavior and guide resources were unchanged; this pass uses the existing validator rather than rerunning unrelated unit or browser suites. The functional evaluation owns the independent content review. Route: `pass` for this bounded contract check.
