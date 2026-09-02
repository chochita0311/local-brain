# EVAL-0078 UX: Atlassian In-Context Item Detail

## Metadata

- ID: `eval-0078-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS`
- Run ID: `run-20260829-88`
- Attempt: `2`
- Feature: [FEAT-0078](../feature/feat-0078-atlassian-in-context-item-detail.md)
- Spec: [SPEC-0078](../spec/spec-0078-atlassian-in-context-item-detail.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `selection/history; presentation`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Checks And Evidence

- The default Explorer remains list-first and asks for one selection without
  moving scroll or automatically opening the first Item.
- Selection advances row emphasis and `aria-current`, preview identity, page
  title, URL/history, announcement, and meaningful heading focus together.
  The hierarchy and neighboring links remain oriented during repeated and
  rapid sibling selection.
- Wide users retain simultaneous hierarchy/list/detail context. Compact and
  narrow users receive one explicit, escapable detail sheet; Escape and close
  restore focus to the selected row, while a missing direct entry restores the
  results heading.
- Tab and reverse-Tab wrap inside the open sheet. Underlying navigation and
  Explorer content are inert while the sheet owns focus and body scrolling.
- One stable live region remains outside the replaceable/compact-hidden pane,
  so the first selection and every later selection announce bounded loading
  and completion. Programmatic focus escaping the modal is returned inside.
- Full detail and Refresh are ordinary visible links rather than hidden pane
  behavior. Returning from full detail restores the selected Explorer URL and
  makes the row reachable; complete compact renders use the approved
  structure-derived disclosure fallback.
- Loading keeps the last stable workspace, stale responses cannot win, and
  failed enhancement exits through a normal navigation path. Empty, missing,
  out-of-scope, stale, unavailable, and recent-history-limited copy remains
  bounded and truthful.
- Checked `1440`, `920`, `700`, and touch-sized `320` widths had no horizontal
  overflow or clipped essential destination.

## Findings

- None.

## Route

- Next action: `pass`
