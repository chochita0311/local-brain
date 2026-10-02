# FEAT-0110: Executable Personal Insight Runs

## Metadata

- ID: `feat-0110`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Created: `2026-09-28`
- Updated: `2026-10-02`

## Goal

Replace the Insights analyzer preview with deliberate, executable question and discovery Runs. Preserve one private Markdown report and browsable history per Run while keeping analysis conversations out of work-Session evidence.

## Acceptance Contract

- Insights retains the real skill ranking and offers two live actions: submit a question or discover without one. The page shows the installed Codex CLI's active local profile, selected model, and a token-use / private-content transfer notice before submission.
- A submitted Run freezes bounded primary work Session evidence, guide version, selected runner/model/settings, coverage, and private artifact paths in an independent `personal_insight_runs` row. No Workstream or maintenance Run owns this identity.
- Codex CLI invocation disables model tools and native Session persistence. The model receives only a frozen, bounded manifest and versioned analysis guide. A page visit, sync, or download invokes no model.
- The result is a validated source-backed report with at most three findings or an honest no-finding report. Repeated-pattern findings require references to different Sessions. Unknown evidence IDs or invalid shape fail the Run rather than becoming a report.
- Insights lists retained Runs, status, selected versus eligible source coverage, selected time range and truncation, candidate/type selection explanations, selected and observed model, observed usage when provided, and report. Active Runs can be stopped. A process restart leaves an interrupted terminal state. Reanalysis starts a new Run.
- Observed analysis usage contributes once to Usage & Cost under the selected Codex source. Analysis remains excluded from ordinary Sessions, work activity, search, and future analysis evidence. Cost uses the existing immutable model-price contract and unassigned Project attribution.
- Completed Markdown is rendered with the shared safe renderer and remains downloadable from the private runtime directory without automatic expiry. A changed or missing cited Session is labeled when the report is opened.
- Narrow screens preserve the analyzer, history, report, and skill-ranking reading order through 320px.

## Boundary

- In: versioned first guide and output shape, private Run table/artifacts, bounded evidence selection, selected CLI execution, status/cancel/reconcile, validated report rendering/download, list/detail UI, current-reference check, documentation.
- Out: automatic or scheduled proactive model Runs, conversational continuation into work, local work-file copy, automatic edits, owner review decisions, targeted evidence expansion, precise pre-Run cost estimates, native conversation persistence.

## Decisions

- The current owner request to remove preview copy and make the full visible analyzer executable approves this bounded product increment.
- The owner selected the current Codex Company CLI profile. Resolve `LOCALBRAIN_INSIGHT_CODEX_HOME`, then `CODEX_HOME`, then an existing `~/.codex-company`, then `~/.codex`; the chosen home and model are frozen per Run. Codex defaults to the current Astra model, with an environment override. The CLI-reported model is recorded when available.
- The first release abstains when the bounded excerpt sample cannot support a recurrence claim. It does not expand source reads inside a Run.
- On 2026-09-28 the owner explicitly requested restoration of the PRD's analysis-cost requirement. The original exclusion of Usage projection was a planning gap, not approval to omit analysis costs. [RUN-125](../run/run-20260928-125-personal-insight-usage-accounting.md) implements the correction with the backend-product profile and data/backend lanes.

## Dependency And Trace

- FEAT-0106 owns the skill-ranking surface; FEAT-0107 owns the read-only evidence manifest. RUN-120 originally froze a brief v1 guide within this Feature. After FEAT-0108 passed its independent foundation checks, [RUN-122](../run/run-20260928-122-guided-personal-insight-result-integration.md) connected its selected v2 core/playbooks and result contract to new executable Runs. Existing historical reports are not rewritten.
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Run: [RUN-20260928-120](../run/run-20260928-120-executable-personal-insight-runs.md)
- Guide integration correction: [RUN-20260928-122](../run/run-20260928-122-guided-personal-insight-result-integration.md)
- Historical core-v3 behavior comparison: [RUN-20260928-126](../run/run-20260928-126-personal-insight-guide-behavior.md), a subagent surrogate evaluation rather than product CLI execution.

- The owner's 2026-09-29 continuation approves [RUN-129](../run/run-20260929-129-personal-insight-scope-and-requests.md): integrate core v5/report v3, display actual frozen scope and selection reasons, and render only validated missing-message targets. Model/reasoning options remain deferred.

- RUN-129 passed the integrated scope/request correction with 30 personal-insight regressions, 42 shared UI contract checks, and synthetic browser evidence at 1440px and 320px. Actual paid CLI execution and owner benefit remain outside this implementation review.

- The owner's first real question Run exposed a macOS sandboxed CLI-bootstrap defect. [RUN-135](../run/run-20261001-135-personal-insight-cli-startup.md) resolves the launcher target and grants its exact runtime file read access while preserving the analysis boundary. Its [contract](../evaluation/eval-0110-contract-cli-startup.md) and [functional](../evaluation/eval-0110-functional-cli-startup.md) checks cover synthetic regression and the installed CLI's offline startup. A 2026-10-02 owner retry subsequently validated a live no-finding response and generated a report; read-only checks confirmed the visible download action and matching downloaded content. This single execution does not establish recommendation quality, adoption, benefit or provider-confirmed model identity.

## First Increment Closeout Review

This is the initial review record. The same-day owner-approved [closeout corrections](#closeout-corrections) resolve its implementation and regression findings while retaining the evidence below.

The owner's 2026-10-02 pre-handoff review checked the approved first increment against current code, tests, saved product Runs and the active server. This is a Fullstack review of frontend report/history and backend lifecycle/accounting, with no new provider execution. A later owner-started core-v8 question Run now returns one grounded, concrete application handoff; [the guide evaluation](../evaluation/eval-0108-functional-proposal-follow-through.md#subsequent-owner-started-product-observation) owns that behavioral observation and its limits.

- **Working:** both successful product Runs have exactly one priced Usage record under the selected Source, with metadata-only Maintenance parents, no ordinary events or search entries, and unassigned Project attribution. Completed/no-finding reports and downloads remain available; the earlier failed Run retains its error and retry action. No active analysis remains.
- **Regression evidence:** 37 personal-insight tests pass. Across the bounded nine-module-pattern set, 150 tests yield 142 passes and eight failures: six usage pricing/snapshot expectations and two schema-presentation expectations. These match the existing failure classes and test names recorded in [RUN-125](../run/run-20260928-125-personal-insight-usage-accounting.md#verification-and-existing-failures); the earlier Run proved them on unchanged HEAD. This review did not repeat that baseline checkout or run the entire repository suite.
- **Rendered evidence:** an isolated Chrome profile checked completed, no-finding and failed product reports at effective widths 1440px and 320px. Status, history, report presence, evidence links, download/retry affordances and keyboard disclosure work. No POST or nonlocal page request occurred. The 320px containment check fails: a classic 15px scrollbar leaves 305px client width while the shared `html` minimum remains 320px. The same issue occurs on Usage & Cost; 335px viewport / 320px client width passes. This is a shared-shell issue, not a long-report-specific diagnosis.
- **Cost visibility gap:** the stored estimate contributes to Usage & Cost, but selected Run detail only displays a monetary value when the CLI emits `total_cost_usd`. The actual CLI results lack that field. Detail should expose the existing normalized estimate, calculation state and frozen pricing basis, with unavailable states kept explicit.
- **Remaining quality limits:** one useful production question report does not establish broad discovery quality, recommendation stability or actual benefit. Earlier mixed-language/source-wording defects remain preserved evidence. Applying a report and retaining owner feedback are separate from successful analysis execution.

The desktop workflow is usable for a first real-use pass; this review is not an unqualified all-tests/all-viewports pass. The [Insights follow-up](../project/backlog.md#personal-improvement-insights) and [quality backlog](../project/backlog.md#p2---quality-and-distribution) own the remaining tasks. Private closeout diagnostics use `personal-insight-evaluations/review-20261002-closeout` under the established [archive owner](../../policies/project/developer-guide.md#personal-improvement-analysis); they do not alter the closed guide-comparison archive.

## Closeout Corrections

The owner's 2026-10-02 follow-up approves [RUN-137](../run/run-20261002-137-insight-closeout-corrections.md). Run detail now shows its stored estimate and explicit unavailable states, with calculation state and frozen price basis in the existing disclosure. The shared root fits the 320px viewport with a classic scrollbar; Insights, Usage & Cost and Auto Work retain their local scrolling and controls. Eight original stale test expectations and two further consumer-count expectations are reconciled with their owners.

Exact GPT-6.1 Sol has separate dated Standard/Fast price snapshots, including its 5% cached-input rate. Eligible retained unpriced usage was calculated without changing already-priced evidence, other usage, attribution or product Runs. Server restart preserved the existing environment and retained report downloads.

The [contract](../evaluation/eval-0110-contract-closeout-corrections.md), [functional](../evaluation/eval-0110-functional-closeout-corrections.md), [design](../evaluation/eval-0110-design-closeout-corrections.md) and [UX](../evaluation/eval-0110-ux-closeout-corrections.md) evaluations pass with complete coverage of this bounded correction: 216 affected regression tests and 18 report/peer browser combinations, plus expanded price-setting checks. The later [publication review](../run/run-20261002-137-insight-closeout-corrections.md#post-run-publication-review--2026-10-02) records the full repository suite, resolves two additional schema-audit parity failures, and reconciles related document owners. Actual intervention benefit remains unverified; the next-use trial stays in the [backlog](../project/backlog.md#personal-improvement-insights).
