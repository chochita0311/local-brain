# EVAL-0080 UX: Atlassian Local Evidence Sync

## Metadata

- ID: `eval-0080-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS`
- Run ID: `run-20260829-90`
- Attempt: `1`
- Feature: [FEAT-0080](../feature/feat-0080-atlassian-local-evidence-sync.md)
- Spec: [SPEC-0080](../spec/spec-0080-atlassian-local-evidence-sync.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `Sync interaction; in-place Explorer continuity`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Checks And Evidence

- Sync is one executable zero-input POST whose only field is the current
  canonical `return_to`. Its visible scope states that it reads persisted
  Session and Local Context URL evidence locally and does not import sources or
  perform remote Refresh work.
- Starting Sync disables and marks only Sync busy. The Explorer, Add, More,
  hierarchy, list, and selected detail remain usable, and completion does not
  move focus unless the approved body-focus fallback is required.
- Real changed completion reported four new Items. Immediate repeat reported
  zero new work as successful completion and exposed Session/Local Context Sync
  plus Add guidance. Partial with one unavailable source and fatal with one
  failed source kept whole-scope retry guidance visible outside the collapsed
  source details.
- A selected offscreen list anchor remained visually fixed when four rows were
  inserted ahead of it; the list offset changed from 0 to 390 only to preserve
  that anchor. Page, preview, and hierarchy scroll, selected Item, URL, history
  length and entry, and replacement-target focus remained stable.
- A forced Explorer GET/fragment-refresh failure retained the report, selection,
  focus, and scroll state, performed no automatic reload, and showed an explicit
  local current-Explorer reload link.
- Concurrent raw and enhanced requests produced one `200` result and one `409`
  busy result. Busy showed no outcome badges, started no Explorer GET, displayed
  no refresh warning, and explained that no new work or remote read began.
- During long Sync plus Add and long Sync plus compact Item preview, the active
  modal kept focus, inert background, body lock, and its close-restoration
  owner. The visible completion updated while the live owner remained deferred;
  closing the modal emitted one completion announcement and restored the Add
  trigger or selected row focus.
- At `920` the Item preview and Add remained bounded right drawers. At `700` and
  `320` the action order, touch targets, full-width sheet geometry, scrolling,
  and zero-overflow behavior remained usable. Escape from Add restored its
  initiating action.
- With JavaScript disabled, POST redirected with `303` to the exact semantic
  Explorer state and verified receipt. Reload issued GET only, did not resubmit,
  and the receipt did not leak into downstream links or the next `return_to`.
- Browser request logs contained only local `POST /atlassian/sync` and the local
  `GET /atlassian` used for the named in-place refresh; no Refresh, provider, or
  remote call occurred. Console inspection was clean, and the sampled mobile
  and desktop Lighthouse runs reported Accessibility `100`.

## Findings

- None.

## Route

- Next action: `pass`
