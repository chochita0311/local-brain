# EVAL-0049: Explicit Atlassian Refresh And Preview — Functional

## Metadata

- ID: `eval-0049-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260723-54`
- Attempt: `1`
- Feature: [feat-0049-explicit-atlassian-refresh-and-preview](../feature/feat-0049-explicit-atlassian-refresh-and-preview.md)
- Spec: [spec-0049-explicit-atlassian-refresh-and-preview](../spec/spec-0049-explicit-atlassian-refresh-and-preview.md)
- Execution Profile: `fullstack-product`
- Surface Lane: scope/query → start route → Runner → result application → responsive client
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated scope resolution, selection defaults, 20-read enforcement, mixed and single-source Runs, request plans, no-script behavior, unavailable executor, result validation/application, Confluence catalog, polling, generated artifacts, and complete regressions.

## Checks And Evidence

- Eight focused refresh tests cover Workstream/Thread deduplication, unknown/current/due/unavailable defaults, the 20-read boundary, mixed-source one-Run projection, single-source compatibility, reference persistence, invalid mapping rollback, Confluence catalog pagination/stub creation, local preview, unavailable executor recovery, and end-to-end Runner application.
- The route preserves repeated Item selections under bounded form parsing, requires an injected executor and supported runner before preparation, and returns a selected error state rather than silently queuing work.
- JavaScript changes only local selected count/read math and polls an explicitly selected active local Run. It never performs provider access or starts a Run on load.
- Runner integration verifies two authorized Jira reads, host/model authority separation, terminal `completed` state, remote identity binding, deterministic ADF normalization, and Item application in the terminal transaction.
- Existing FEAT-0045 external-sync, FEAT-0046 Atlassian, FEAT-0048 registration, Workstream, Session exclusion, Usage, UI, migration, and schema tests remain green.
- The complete suite passed 250 tests. Privacy, JavaScript syntax, data-model ownership, nine Mermaid diagrams, schema presentation, the 491-object cleanup audit, and diff whitespace checks passed.

## Evidence Gaps

- No live Gateway or company data was used. Approved dispatch behavior and failure states use synthetic Source Instances and provider results.

## Findings

- None.

## Regression Notes

- One pre-existing Starlette `TemplateResponse` deprecation warning remains unrelated and non-blocking.

## Route

- Next action: release Functional evaluation for FEAT-0049.
