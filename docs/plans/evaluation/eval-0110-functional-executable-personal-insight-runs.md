# EVAL-0110 Functional: Executable Personal Insight Runs

## Metadata

- ID: `eval-0110-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Evidence Coverage: `partial`
- Run: [RUN-20260928-120](../run/run-20260928-120-executable-personal-insight-runs.md)
- Attempt: `2`
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Execution Profile: `fullstack-product`
- Lane: `backend`, `frontend`
- Created: `2026-09-28`

## Evidence And Finding

- The scratch Insights GET route rendered without a model call and detected the installed Codex CLI, selected `.codex-company` home, and `gpt-6-astra`. Installed `codex exec --help` confirms the required ephemeral, config, schema, JSON, model, and working-directory options.
- Form actions, list/detail selection, polling, cancellation, download, and new-Run reanalysis have explicit route and state ownership in source. An immediate write transaction serializes active-Run creation; cancellation persists a terminal state even before a queued task begins.
- The actual analysis-start click was rejected by automatic approval review as potential external transmission of private Session excerpts. No paid call, completed report, failure recovery, or file download was observed. No automated test was requested or run.
