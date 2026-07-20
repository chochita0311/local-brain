# EVAL-0040: Local Context Navigation Order — Functional

## Metadata

- ID: `eval-0040-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260719-45`
- Attempt: `1`
- Feature: [feat-0040-local-context-navigation-order](../feature/feat-0040-local-context-navigation-order.md)
- Spec: [spec-0040-local-context-navigation-order](../spec/spec-0040-local-context-navigation-order.md)
- Execution Profile: `frontend-product`
- Surface Lane: `shared-shell-navigation`
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated DOM and sequential keyboard order, number-label parity, existing destinations, active mappings, current-state cardinality, narrow reachability contract, and repository regressions.

## Checks And Evidence

- A deterministic template test asserted ordered source positions and matching symbols for all five destinations.
- The same test rendered `base.html` through Jinja for `sessions`, `context`, `atlassian`, `sources`, and `schema`; each state produced exactly one active `.lnb-item`, the expected unchanged href, and one `aria-current=page`.
- Sequential keyboard order matches DOM order because all destinations remain ordinary anchors and no `tabindex` was added.
- Narrow navigation retains horizontal overflow and non-shrinking anchor rules, so all unchanged destinations remain keyboard- and scroll-reachable.
- The active synthetic local runtime returned `/context` with the exact ordered labels and one active `/context` anchor.
- All 24 UI contract tests and the complete 164-test repository suite passed.
- Privacy passed 441 candidate files and `git diff --check` passed.

## Evidence Gaps

- None for functional route, DOM, active-state, or reachability contracts. Pixel-level viewport presentation belongs to the Design report's explicitly non-blocking evidence gap.

## Findings

- None.

## Regression Notes

- Destination hrefs, Jinja conditions, label copy, groups, skip link, global search, and content routes remain unchanged.

## Route

- Next action: `pass`.
