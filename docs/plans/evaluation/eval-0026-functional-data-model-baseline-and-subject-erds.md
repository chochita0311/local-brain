# EVAL-0026: Data Model Baseline And Subject ERDs — Functional

## Metadata

- ID: `eval-0026-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260718-31`
- Attempt: `1`
- Feature: [feat-0026-data-model-baseline-and-subject-erds](../feature/feat-0026-data-model-baseline-and-subject-erds.md)
- Spec: [spec-0026-data-model-baseline-and-subject-erds](../spec/spec-0026-data-model-baseline-and-subject-erds.md)
- Execution Profile: `docs-content`
- Surface Lane: parity, links, local Mermaid parse/render, regression and privacy
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: navigable, locally renderable, schema-only data-model baseline.
- Active spec: SPEC-0026 attempt 1.
- Evaluated build or commit: current unstaged FEAT-0026 documents and checks in the shared workspace.

## Checks

- Ran the deterministic data-model document checker directly and through the new Python unit test.
- Parsed exactly nine Markdown Mermaid blocks with the pinned local Mermaid 11.16.0 bundle.
- Generated an ignored schema-only QA preview using the shipped strict adapter and served it only on `127.0.0.1`.
- Rendered all nine ERDs sequentially in local headless Chrome and inspected the full contact sheet, a 2400-pixel global view, and a focused FTS view.
- Verified `9 / 9` render status, visible entity fields, solid/dotted relation distinction, focused subject separation, and horizontal containment for the dense global map.
- Ran Mermaid asset freshness, the complete Python suite, repository privacy scan, link validation, and whitespace checks.

## Evidence

- Environments checked: in-memory SQLite, Node/local Mermaid parser, local Chrome SVG rendering, source link resolver, full unit suite, and repository privacy scan.
- Local parser: 9 of 9 diagrams passed.
- Local Chrome: 9 of 9 diagrams rendered through `mermaid-adapter.js`; the global map and all eight subject cards appeared in the schema-only contact sheet.
- All 85 Python tests passed, including the persistent schema-doc parity test.
- Privacy check passed for 333 candidate files; `git diff --check` passed.
- Preview HTML stayed under ignored `.cache/`; screenshots stayed under `/tmp` and were not added to the repository.

## Evidence Gaps

- The in-app Browser plugin interface required by the available browser skill was not exposed in this session. Local headless Chrome rendered the same local adapter and assets as the bounded fallback.
- Acceptance impact: not applicable; actual SVG output and readability were directly inspected, and this Feature has no product route.

## Findings

- No invalid link, parser failure, render failure, overflow loss, privacy issue, or runtime regression remains.

## Regression Notes

- Mermaid assets stayed current; existing 84 application tests plus the new parity test passed. No runtime database or user row was opened.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: passed attempt 1 with complete automated parity and direct local rendered-output evidence.
