# FEAT-0006: Source And System Inventories

## Metadata

- ID: `feat-0006`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Make Projects, Sources, and Atlassian coherent inventory and availability surfaces that expose location, health, missing state, and connector boundaries without implying unsupported behavior.

## Acceptance Contract

- Projects preserve current path, Git, activity, availability, and detail-navigation meaning.
- Sources preserve source identity, health, scan time, error counts, local database context, and existing scan behavior.
- Atlassian remains an intentional unavailable or planned-state surface for its existing Jira and Confluence views.
- Missing, healthy, error, unavailable, and planned treatments use explicit labels and the correct semantic families.

## Scope Boundary

- In:
  - `/projects`, `/sources`, and `/atlassian`
  - Project rows, source-health rows or cards, scan feedback, view switching, planned-state communication, and responsive presentation
- Out:
  - connector implementation or authentication
  - changes to scan, source, Project, Jira, or Confluence data contracts
  - new health metrics, filters, or source-management actions
  - Local Context source management owned by `feat-0011`

## Contract Surfaces

- `/projects`, `/sources`, and `/atlassian?view=` route contracts
- `POST /api/scan` response and refresh behavior
- current derived source-health rule based on error count

## Required Evaluators

- `design`: inventory hierarchy, path containment, state semantics, planned-state honesty, and responsive rows.
- `functional`: Project links, Atlassian view switching, scan action, refresh, status, and error feedback.
- `ux-heuristic`: availability clarity, source trust, action consequence, and distinction between planned and functional surfaces.

## User-Visible Outcome

- The user can inspect where work occurred, whether local sources are healthy, and which external surface is unavailable without mistaking placeholders for live integrations.

## Entry And Exit

- Entry point: Projects, Sources, or Atlassian from shared navigation.
- Exit or transition behavior: Project rows open the current filtered Sessions view; scan retains its current refresh behavior; Atlassian view switches remain on the planned surface.

## State Expectations

- Default: available Project and healthy Source information is concise and traceable.
- Loading: scan shows an explicit bounded working state.
- Empty: absence of Projects or Sources is distinguished from an error.
- Error: missing paths and source errors keep their reason and relevant metadata visible.
- Success: completed scan feedback precedes the current refresh behavior.

## Dependencies

- `feat-0002` and `feat-0003` must be `passed`.

## Likely Affected Surfaces

- `src/localbrain/templates/projects.html`
- `src/localbrain/templates/sources.html`
- `src/localbrain/templates/atlassian.html`
- Project, Source, planned-state, status, scan-feedback, and responsive selectors in `src/localbrain/static/styles.css`
- scan interaction in `src/localbrain/static/app.js`

## Pass Or Fail Checks

- Pass if long paths, missing paths, health labels, timestamps, and error counts remain contained.
- Pass if healthy and error source labels follow the constitution's derived-state mapping.
- Pass if scan working, success, failure, and refresh behavior remains functional.
- Pass if Atlassian never looks connected or writable when it is not.
- Fail if source or Project data meaning changes for visual convenience.
- Fail if planned controls imply unavailable connector actions.

## Regression Surfaces

- Project-to-Sessions links
- source scan API and refresh flow
- Atlassian `jira` and `confluence` query selection
- shared provenance and status semantics

## Harness Trace

- Active spec doc: [spec-0006-source-system-inventories](../spec/spec-0006-source-system-inventories.md)
- Active run: [run-20260716-06-source-system-inventories](../run/run-20260716-06-source-system-inventories.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0006-ux-system-inventories](../evaluation/eval-0006-ux-system-inventories.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft grouped three smaller inventory surfaces by their shared availability and system-trust purpose.
- `2026-07-16`: executed and passed in `run-20260716-06`.
