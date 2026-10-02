# EVAL-0110 Contract: Scope And Requests

## Metadata

- ID: `eval-0110-contract-scope-and-requests`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-129](../run/run-20260929-129-personal-insight-scope-and-requests.md)
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `data, backend`
- Created: `2026-09-29`

## Contract Evidence

- Evidence v1 adds scoped eligible-message count/positions and truncated-excerpt totals without changing source eligibility, ordering, or limits. The prompt projects those values and excerpt completeness.
- Preparation freezes report v3 and its schema. Launch detects a changed schema; historical core v2/v3 resolves to report v2. Existing reports remain saved artifacts.
- Candidate/type reasons and scope are generated from validated values and frozen coverage. Conversation request instructions use validated positions and quoted anchors; the unconstrained resend question is not rendered. Supplied-message rejection produces an understandable failed-Run reason and no automatic retry.
- Selected candidate/request citations are rechecked alongside finding/counterevidence references. Only admitted local Session destinations become active links.
- Source inspection and the 30 focused personal-insight tests cover evidence, guidance, consumer rendering, stale-reference projection, and failure/cancellation usage retention. The 42 shared UI contract tests also pass.

## Boundaries And Route

No database migration, new model call, follow-up evidence fetch, pricing rule, source classification change, or execution-option control was introduced by RUN-129. The existing CLI usage-before-validation path is preserved. Contract coverage is complete for these producer/consumer boundaries; route: `pass`. Model semantics remain covered by the separate foundation functional report.
