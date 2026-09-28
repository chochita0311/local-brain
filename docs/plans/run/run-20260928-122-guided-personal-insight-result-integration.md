# RUN-20260928-122: Guided Personal Insight Result Integration

## Metadata

- ID: `run-20260928-122`
- Status: `passed`
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Active Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md), post-Run guide integration
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Lanes: `data`, `backend`, rendered report presentation
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-09-28`
- Updated: `2026-09-28`

## Goal And Boundary

Connect the already delivered analysis-only Run lifecycle to the independently passed FEAT-0108 guide and finding contract before any real personal analysis Run. This is an implementation Run record, not a model analysis Run. Preserve the previous v1 guide as historical evidence and leave earlier completed reports untouched.

## Execution Record

- New Runs select at most four versioned playbooks with the owner's question first. Run settings freeze the core and selected playbook versions, SHA-256 digests, and routing reason; the private prompt freezes their exact text.
- The per-Run output schema and local validation now accept up to three findings, an honest no-finding outcome, or a bounded request for additional evidence. A finding includes an explicit disconfirming check, source IDs, uncertainty, a small action, follow-up, and a separate-work-Session handoff. Invalid citations, overlapping support and counterexample IDs, and one-Session recurrence fail validation.
- Locally generated Markdown uses the frozen guide version and plain Korean labels. The shared renderer activates only exact Session links admitted by that Run's frozen evidence manifest; source-authored Markdown keeps its established unresolved-link behavior.
- Synthetic evidence, guide, renderer, and consumer checks passed. A private temporary server with only synthetic Sessions rendered a completed report in Chrome at 1440px and emulated 320px: both stayed within the document width and both evidence links resolved to their admitted Session routes. The temporary server and fixture were removed after review.

## Evaluation And Limit

- [Contract](../evaluation/eval-0110-contract-guided-result-integration.md): `PASS` for version, citation, artifact, and local-link boundaries.
- [Design](../evaluation/eval-0110-design-guided-result-integration.md): `PASS` for the synthetic rendered report at wide and narrow widths.
- [Functional](../evaluation/eval-0110-functional-guided-result-integration.md): `PASS` for focused synthetic behavior and report-link checks.
- [UX heuristic](../evaluation/eval-0110-ux-guided-result-integration.md): `PASS WITH SUGGESTIONS` for report scanability, source trace, and outcome language.
- No Codex CLI analysis process, external model request, private Session analysis, or owner-confirmed improvement occurred. The owner deferred the actual analysis Run and related provider/quality checks to the next session. Real-model compliance and advice quality remain unobserved. The additional-evidence outcome currently shares the `no_finding` terminal status, with its distinct need explained inside the report; a separate history badge would require a later product decision.
- This session's documentation review clarified the v2 core guide's recurring-claim citation instruction after the checks above: use admitted event IDs from two distinct Sessions. The revised prompt text has not been rechecked. Recheck the focused guide/validator behavior before the deferred actual analysis Run.
