# RUN-20260928-120: Executable Personal Insight Runs

## Metadata

- ID: `run-20260928-120`
- Status: `passed`
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Active Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-09-28`
- Updated: `2026-09-28`

## Goal And Boundary

Replace the fictional Insights analyzer preview with explicit Codex CLI question and discovery Runs. Keep their evidence, report, and history private and separate from ordinary work Sessions.

## Execution Record

- Data: created an independent `personal_insight_runs` ledger and private one-Run artifact directory. Existing primary-work Session messages are selected with bounded evidence references; analysis Runs do not create Session or Usage rows.
- Backend: added Codex CLI execution through the frozen `CODEX_HOME` profile, Astra default model, high reasoning effort, no model tools, ephemeral native Session, structured-result validation, cancellation, restart interruption, retained Markdown report, and download/status routes. An immediate write transaction prevents duplicate active starts.
- Frontend: replaced disabled preview controls and fictional report with live question/discovery forms, visible profile/model and token notice, Run history, progress, settings, observed usage, report, download, cancellation, and reanalysis.
- Documentation: refreshed the product overview, privacy, architecture, data-model owner, value dictionary, schema presentation, PRD continuity, Feature, and Spec.

## Evaluation Coverage

- [Contract](../evaluation/eval-0110-contract-executable-personal-insight-runs.md): `PASS`, partial evidence. Source and schema inspection covered lifecycle, source admission, private artifacts, citation validation, and analysis exclusion.
- [Design](../evaluation/eval-0110-design-executable-personal-insight-runs.md): `PASS`, partial evidence. A scratch local server rendered the empty state at 1440px and 320px without document overflow. The live report state was not rendered.
- [Functional](../evaluation/eval-0110-functional-executable-personal-insight-runs.md): `PASS`, partial evidence. The read-only route and installed CLI option contract were inspected; no model Run or automated test was executed.
- [UX heuristic](../evaluation/eval-0110-ux-executable-personal-insight-runs.md): `PASS WITH SUGGESTIONS`, partial evidence. History and report state transitions were reviewed in source; direct interaction was limited to the empty state.

## Live Execution Limit

The local browser's analysis-start click was rejected by automatic approval review because it could send private Session excerpts to an external model. The user subsequently selected the current Codex Company CLI profile, which is implemented and shown on the page. This Run did not launch a paid model call or prove the account's Astra entitlement. The owner can start a Run explicitly in Insights and inspect the retained status or failure detail. No provider transmission was performed during implementation review.

## Attempts And Route

- Attempt 1: built the data/backend/frontend increment and rendered a scratch empty state.
- Attempt 2: fixed the Codex Company profile binding, removed the unused Claude choice, made cancellation and actual-model labeling more precise, and re-inspected desktop/mobile layout.
- Route: implementation passes the approved first-increment review scope with a recorded live-provider evidence gap. A real owner-started Run is the next operational observation; it does not require another code change to be available.

## Later Correction

The documentation review found that this product Run had been marked passed before the fuller FEAT-0108 guide and finding contract had been completed. FEAT-0107 and FEAT-0108 subsequently passed synthetic foundation evaluations. [RUN-122](run-20260928-122-guided-personal-insight-result-integration.md) records the post-Run consumer correction, including source-linked report rendering. This historical RUN-120 status remains a first-increment implementation result with partial live-provider coverage, not evidence of an actual personal analysis Run.
