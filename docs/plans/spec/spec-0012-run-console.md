# SPEC-0012: Run Console

## Metadata

- ID: `spec-0012`
- Status: `approved`
- Run ID: `run-20260716-12`
- Attempt: `1`
- Parent Feature: [feat-0012-run-console](../feature/feat-0012-run-console.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: Run lifecycle and console
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Constitution Run mapping, Run GET/poll/cancel contracts, and current lifecycle vocabulary.

## Implementation Goal

- Make Run status, control, metadata, output, error, evidence, and artifacts readable together while retaining exact polling and cancellation behavior.

## In-Scope Behavior

- Map prepared neutral, queued info, running brand, cancelling/interrupted warning, cancelled neutral, completed success, and failed danger.
- Keep metadata and cancellation outside the independently scrollable dark technical console.
- Preserve active polling for queued/running/cancelling only and existing cancel endpoint behavior.

## Out-Of-Scope Behavior

- Execution semantics, persistence, retry, output search, artifacts, retrieval, or MCP changes.

## Affected Surfaces

- `run.html`, Run selectors in `styles.css`, polling and cancellation in `app.js`, and UI contract tests.

## State And Interaction Contract

- Status and error regions are live; polling retains prior output and stops on every terminal state.
- Long output and errors wrap inside bounded regions and never widen the page.

## Acceptance Mapping

- Exact state mapping maps to reusable `.run-status` selectors.
- Lifecycle behavior maps to the active status set and cancel handler.
- Technical hierarchy maps to metadata above console and artifacts below it.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved before Workstream maintenance consumes the status contract.
