# EVAL-0049: Explicit Atlassian Refresh And Preview — UX Heuristic

## Metadata

- ID: `eval-0049-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS`
- Run ID: `run-20260723-54`
- Attempt: `1`
- Feature: [feat-0049-explicit-atlassian-refresh-and-preview](../feature/feat-0049-explicit-atlassian-refresh-and-preview.md)
- Spec: [spec-0049-explicit-atlassian-refresh-and-preview](../spec/spec-0049-explicit-atlassian-refresh-and-preview.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `atlassian-refresh-preview`
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated scope confidence, spend/consequence comprehension, freshness defaults, selection override, unavailable recovery, action density, contextual continuity, no-script behavior, and responsive reachability.

## Checks And Evidence

- The user sees the exact local scope before any remote activity and can distinguish all-known LocalBrain Items from the company Atlassian estate.
- Target checkboxes make freshness defaults reviewable: current is not silently refreshed, while unknown, due, stale, and unavailable remain visible and initially selected.
- Per-target and total remote-read counts make the 20-read ceiling understandable before submission. The one-maintenance-Run label avoids implying one hidden Run per Source Instance.
- Source Instance, Site/Space, coverage, freshness, and timestamps provide enough context to exclude a target without opening another screen.
- The unavailable executor state explains why remote execution is disabled while preserving the complete local preview and navigation back to the originating context.
- Failed/unavailable retry is explicit and selected-only; no automatic retry, scheduler, page-load refresh, or background polling exists.
- At compact widths, the document order remains scope → counts → targets → handoff. Checkboxes, labels, URLs, and actions remain reachable without horizontal page overflow.

## Evidence Gaps

- Live provider latency and a manually induced partial Run were not observed. The resulting status and retry contracts are covered with synthetic runtime evidence.

## Findings

- No blocking hidden cost, scope ambiguity, recovery dead end, or action-wall issue remains.
- No optional heuristic backlog item is required.

## Route

- Next action: release UX Heuristic evaluation and Run acceptance.
