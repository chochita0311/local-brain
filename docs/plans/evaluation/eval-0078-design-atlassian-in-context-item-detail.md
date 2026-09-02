# EVAL-0078 Design: Atlassian In-Context Item Detail

## Metadata

- ID: `eval-0078-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run ID: `run-20260829-88`
- Attempt: `2`
- Feature: [FEAT-0078](../feature/feat-0078-atlassian-in-context-item-detail.md)
- Spec: [SPEC-0078](../spec/spec-0078-atlassian-in-context-item-detail.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `presentation`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Checks And Evidence

- `screen-alignment` was applied in `extend` mode. The implementation extends
  the existing Atlassian hierarchy/list shell and Local Context/Schema
  progressive-preview family without introducing a private shell, token set,
  breakpoint, or foreign editable-detail pattern.
- At `1440x900`, Chrome rendered hierarchy, inventory, and read-first detail as
  three adjacent regions. The result list and detail own independent bounded
  scroll, while the page remains horizontally contained.
- At `920x900`, detail becomes a bounded right sheet over the still-mounted
  list. At `700x800` and `320x800`, it becomes a full-width sheet below the
  persistent shell. Long mixed-script title/domain content wrapped without
  viewport overflow at every checked width.
- The sheet has a programmatic dialog name, explicit close, modal semantics,
  underlying inert state, visible focus, and contained tab order. The
  non-script direct-entry state remains an in-flow sequential region rather
  than pretending to be an interactive overlay.
- Identity and actions lead; Remote facts, Local memory, Found in,
  Organization, and Refresh history remain visually distinct read-only
  authority groups. Editing controls remain on full detail.
- A reference-only Item reduces absent remote diagnostics to one truthful last-
  check fact and one metadata-empty message instead of rendering repeated
  unknown cells. Canonical URL remains visible and wraps within its fact cell.
- Lighthouse on the selected mobile state reported Accessibility `100` and
  Best Practices `100`. A final clean navigation reported no browser console
  messages.

## Findings

- None.

## Route

- Next action: `pass`
