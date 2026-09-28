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
- Updated: `2026-09-28`

## Goal

Replace the Insights analyzer preview with deliberate, executable question and discovery Runs. Preserve one private Markdown report and browsable history per Run while keeping analysis conversations out of work-Session evidence.

## Acceptance Contract

- Insights retains the real skill ranking and offers two live actions: submit a question or discover without one. The page shows the installed Codex CLI's active local profile, selected model, and a token-use / private-content transfer notice before submission.
- A submitted Run freezes bounded primary work Session evidence, guide version, selected runner/model/settings, coverage, and private artifact paths in an independent `personal_insight_runs` row. No Workstream or maintenance Run owns this identity.
- Codex CLI invocation disables model tools and native Session persistence. The model receives only a frozen, bounded manifest and versioned analysis guide. A page visit, sync, or download invokes no model.
- The result is a validated source-backed report with at most three findings or an honest no-finding report. Repeated-pattern findings require references to different Sessions. Unknown evidence IDs or invalid shape fail the Run rather than becoming a report.
- Insights lists retained Runs, status, source coverage, selected and observed model, observed usage when provided, and report. Active Runs can be stopped. A process restart leaves an interrupted terminal state. Reanalysis starts a new Run.
- Completed Markdown is rendered with the shared safe renderer and remains downloadable from the private runtime directory without automatic expiry. A changed or missing cited Session is labeled when the report is opened.
- Narrow screens preserve the analyzer, history, report, and skill-ranking reading order through 320px.

## Boundary

- In: versioned first guide and output shape, private Run table/artifacts, bounded evidence selection, selected CLI execution, status/cancel/reconcile, validated report rendering/download, list/detail UI, current-reference check, documentation.
- Out: automatic or scheduled proactive model Runs, conversational continuation into work, local work-file copy, automatic edits, owner review decisions, targeted evidence expansion, precise pre-Run cost estimates, native Session/Usage projection for the analysis conversation.

## Decisions

- The current owner request to remove preview copy and make the full visible analyzer executable approves this bounded product increment.
- The owner selected the current Codex Company CLI profile. Resolve `LOCALBRAIN_INSIGHT_CODEX_HOME`, then `CODEX_HOME`, then an existing `~/.codex-company`, then `~/.codex`; the chosen home and model are frozen per Run. Codex defaults to the current Astra model, with an environment override. The CLI-reported model is recorded when available.
- The first release abstains when the bounded excerpt sample cannot support a recurrence claim. It does not expand source reads inside a Run.

## Dependency And Trace

- FEAT-0106 owns the skill-ranking surface; FEAT-0107 owns the read-only evidence manifest. RUN-120 originally froze a brief v1 guide within this Feature. After FEAT-0108 passed its independent foundation checks, [RUN-122](../run/run-20260928-122-guided-personal-insight-result-integration.md) connected its selected v2 core/playbooks and result contract to new executable Runs. Existing historical reports are not rewritten.
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Run: [RUN-20260928-120](../run/run-20260928-120-executable-personal-insight-runs.md)
- Guide integration correction: [RUN-20260928-122](../run/run-20260928-122-guided-personal-insight-result-integration.md)
