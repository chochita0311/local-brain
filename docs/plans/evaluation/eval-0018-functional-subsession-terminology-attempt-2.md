# EVAL-0018: Subsession Terminology Functional Attempt 2

## Metadata

- ID: `eval-0018-functional-subsession-terminology-attempt-2`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260717-18`
- Attempt: `2`
- Feature: [feat-0018-conversation-focused-session-details](../feature/feat-0018-conversation-focused-session-details.md)
- Spec: [spec-0018-conversation-focused-session-details](../spec/spec-0018-conversation-focused-session-details.md)
- Execution Profile: `fullstack-product`
- Surface Lane: detail rendering and lazy route integration
- Created: `2026-07-19`

## Functional Evidence

- Synthetic Sessions, primary detail, and direct-child detail requests returned `200` and rendered only the `Subsession` product label.
- Two sequential Sessions requests retained identical versioned asset URLs, and Session-only synchronization returned `200` against empty synthetic source roots.
- `/sessions/{id}/subagents/{file}` returned `308` to `/sessions/{id}/subsessions/{file}`.
- The complete 142-test suite and Python compilation passed.

## Findings And Regression

- No blocking functional finding. Stored events, parent resolution, source synchronization scope, filters, and normalized child destinations are unchanged.
- Browser-only transient working, failure, focus, and viewport state capture remains explicit non-blocking quality backlog.

## Route

- Next action: `pass`
