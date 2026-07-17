# FEAT-0014: Local Context Explorer

## Metadata

- ID: `feat-0014`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Give Local Contexts one coherent explorer that preserves source selection, tree orientation, document preview, source management, health, unavailable evidence, and sequential narrow-layout use.

## Acceptance Contract

- Folder, file, and Apple Notes sources remain distinguishable and selectable with visible path, count, and health context.
- Source tree, selected document, preview, and full-document destination preserve one understandable selection model.
- Pending, ready, unreadable, error, and missing states use the constitution's labels, semantic families, reason, and recovery context.
- Add and remove actions retain their current consequences, including the promise that original files and Apple Notes are not deleted.
- Compact and narrow transformations preserve source, tree, and preview order without trapping controls in an unsupported mode.

## Scope Boundary

- In:
  - `/context`
  - source groups and management, tree, document selection, preview, health, empty, error, missing, unreadable, and responsive sequential presentation
- Out:
  - scanning, extraction, Apple Notes Automation, source-registration, or deletion behavior changes
  - new source types, lazy loading, pagination, or in-source search
  - full Document detail owned by `feat-0009`

## Contract Surfaces

- `/context?root=&document=` route and selection behavior
- existing context-root, file-source, Apple Notes, and delete API contracts
- Local Context and source-file state vocabularies
- original-source preservation on index removal

## Required Evaluators

- `design`: rail, tree, preview, selection, status, path, empty/error, and responsive containment.
- `functional`: source and document selection, tree disclosure, add/remove forms, full-document link, direct query entry, and responsive control state.
- `ux-heuristic`: orientation, destructive-action clarity, long-tree friction, source health comprehension, and sequential narrow flow.

## User-Visible Outcome

- The user can select a source, navigate its tree, preview evidence, open full content, and manage indexing without losing location or misunderstanding source availability and deletion scope.

## Entry And Exit

- Entry point: Local Contexts navigation, Search or Workstream Document link, or direct `/context` query URL.
- Exit or transition behavior: selection updates the intended source or document; full-document opens the current detail route; removal returns to a valid explorer state.

## State Expectations

- Default: selected source, selected tree item, preview identity, and health are mutually consistent.
- Loading: pending source state is explicit and bounded to the explorer.
- Empty: no sources, empty source, and no selected document are distinct.
- Error: error, unreadable, and missing states preserve reason and available recovery context.
- Success: added or selected source becomes the clear active context; removal confirms index-only scope through existing consequence language.

## Dependencies

- `feat-0002` and `feat-0003` must be `passed`.

## Likely Affected Surfaces

- `src/localbrain/templates/context.html`
- source rail, tree, preview, source management, status, path, empty/error, and responsive selectors in `src/localbrain/static/styles.css`
- source add and delete interactions in `src/localbrain/static/app.js`

## Pass Or Fail Checks

- Pass if source, tree, and preview selection remain synchronized on direct and link-driven entry.
- Pass if pending, ready, unreadable, error, and missing states follow the durable mapping and remain labeled.
- Pass if add and remove actions retain current behavior and consequence language.
- Pass if narrow mode presents source, tree, and preview sequentially with every essential action reachable.
- Fail if hiding a responsive control leaves an unsupported active state.
- Fail if source removal appears to delete the original file or Apple Note.

## Regression Surfaces

- context query selection and direct links
- folder, file, and Apple Notes source forms
- source removal and original-content preservation message
- tree disclosure, preview, and full-document navigation
- Local Context state mapping

## Harness Trace

- Active spec doc: [spec-0014-local-context-explorer](../spec/spec-0014-local-context-explorer.md)
- Active run: [run-20260716-14-local-context-explorer](../run/run-20260716-14-local-context-explorer.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0014-ux-context-explorer-attempt-3](../evaluation/eval-0014-ux-context-explorer-attempt-3.md)
- Latest fix note: [fix-0014-context-explorer-continuity](../fix/fix-0014-context-explorer-continuity.md)

## Continuity Notes

- `2026-07-16`: initial draft retained the explorer as one specialized Feature because source, tree, and preview state must be evaluated together.
- `2026-07-16`: executed and passed as the final sequential Feature run.
- `2026-07-16`: live Chrome re-evaluation invalidated the earlier pass. Hierarchical document selection rebuilds the tree and loses disclosure, scroll, visible selection, and focus context; Feature returned to `in-loop` as an `implementation bug`.
- `2026-07-16`: targeted Fix Agent work and Chrome Attempt 3 passed; preview-only selection now preserves tree disclosure, scroll, focus, history, and accessible current state.
