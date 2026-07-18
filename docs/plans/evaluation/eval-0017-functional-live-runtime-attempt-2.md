# EVAL-0017: Paginated Session Inventory Functional Attempt 2

## Metadata

- ID: `eval-0017-functional-attempt-2`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260717-17`
- Attempt: `2`
- Feature: [feat-0017-paginated-session-inventory](../feature/feat-0017-paginated-session-inventory.md)
- Spec: [spec-0017-paginated-session-inventory](../spec/spec-0017-paginated-session-inventory.md)
- Fix: [fix-0017-live-runtime-pagination-context](../fix/fix-0017-live-runtime-pagination-context.md)
- Execution Profile: `fullstack-product`
- Surface Lane: actual local route, migration, and template integration
- Created: `2026-07-17`

## Failure Reproduction

- The actual `127.0.0.1:8000` process returned `500` from `/sessions` with Jinja `pagination is undefined`.
- Inspection confirmed a pre-change Python process and pre-migration database were serving a newly auto-reloaded template.

## Re-evaluation Evidence

- Before restart, the compatibility fallback restored `/sessions` to `200` with the prior route context instead of rendering an error or hiding both inventory panels.
- After controlled restart, the actual database contained `sessions.git_branch`, `session_role`, `parent_external_id`, and `parent_session_id`; `workspaces.git_branch` was absent.
- Actual `/sessions` rendered exactly 20 primary Sessions with a valid multi-page summary.
- Actual `/sessions?page=2` rendered 20 rows, retained previous and next navigation, and had no horizontal overflow.
- Actual `/projects` rendered the populated Projects state without an error or overflow.
- An actual Session detail rendered message rows, zero visible tool rows, and the `원본 이벤트` label without returning indexed text to the evaluation log.
- Post-migration source synchronization completed with no failed Claude, Codex, or Local Context import. Source-backed subsessions disappeared from top-level counts and populated conditional direct-child dropdowns.
- An actual dropdown child opened a valid child detail with parent orientation; its parent detail retained the Subagents section and both timelines rendered zero tool rows.
- The restarted server produced `200` for the verified Sessions, pagination, Project, and Session-detail routes.

## Automated Evidence

- The new pre-restart context regression passed.
- The complete 38-test suite, JavaScript syntax, Jinja parsing, repository diff check, and privacy check passed.

## Findings And Regression

- No remaining blocking functional finding.
- Initial synthetic-server evidence was insufficient for the mixed-version deployment state; actual-runtime verification is now recorded as required evidence for this Run.

## Route

- Next action: `pass`
