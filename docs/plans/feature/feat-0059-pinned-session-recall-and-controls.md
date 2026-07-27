# FEAT-0059: Pinned Session Recall And Controls

## Metadata

- ID: `feat-0059`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Created: `2026-07-24`
- Updated: `2026-07-27`

## Goal

- Let the owner pin important primary work Sessions, find them from the Sessions inventory instead of a generic recent-Context panel, and open their LocalBrain detail without row geometry changing when Subsessions exist.

## Acceptance Contract

- `/sessions` removes the generic `최근 컨텍스트` document panel and replaces it with a global owner-curated `Pinned Sessions` panel.
- The panel never fills itself from recency, inferred importance, usage, cost, or generated Suggestions.
- Every pinned entry shows title, Claude or Codex provenance, last activity, and enough workspace/path context to distinguish similar Sessions and links to LocalBrain Session detail.
- The panel exposes all current pins by displayed activity date (`last_event_at`, otherwise `started_at`) descending, with `pinned_at DESC, session_id DESC` tie-breaks. Wide layouts may use a bounded internal scroller, while narrow layouts keep the entries in ordinary document flow; no silent item cap hides an older pin.
- Eligible Session inventory rows and persisted Session detail expose separate pin/unpin controls backed by FEAT-0058.
- Pin and Subsession controls are not nested in the Session destination link and do not navigate to the parent Session when activated.
- Every eligible Session row reserves the same trailing utility geometry. At desktop and laptop widths, question count, event count, date, and pin form one upper row in that left-to-right order, while the optional Subsession trigger anchors at the lower trailing edge without changing upper-row position, title width, or row height.
- Question and event counts no longer remain in the main content metadata line at desktop and laptop widths; Git branch and other content-owned metadata stay with the main Session content.
- Pinned state uses an explicit filled pin glyph, accessible `핀 고정` or `핀 해제` name, and `aria-pressed`; the control keeps a transparent background and invisible border so it follows its owning surface, and color alone is insufficient.
- Pinning and unpinning do not change the button box, utility width, row height, or date alignment.
- At narrow widths the pin remains at the upper trailing edge; question count, event count, and date may enter a wrapping metadata flow but preserve that order, and the optional Subsession trigger remains at the lower trailing edge with the required touch target.
- Pin/unpin preserves source filter, workspace filter, page, Sessions/Projects mode, scroll orientation, and a useful focus target through progressive enhancement and no-script fallback.
- Empty, mutation-error, missing-Session, deleted-Session, and populated pinned states are bounded and do not restore recent Context as fallback.

## Scope Boundary

- In:
  - pin/unpin mutation routes and read-model state
  - Sessions inventory row controls and stable utility layer
  - persisted Session detail pin control
  - Pinned Sessions secondary panel
  - global pinned recall across active source/workspace filters
  - deterministic all-pin ordering and bounded overflow
  - empty, error, unavailable, narrow, keyboard, and no-script behavior
- Out:
  - changing pin persistence beyond FEAT-0058
  - pinning Subsessions or Maintenance Sessions
  - native Claude or Codex process resume
  - automatic or inferred pins
  - drag ordering, folders, labels, or pin history
  - related Context rail owned by FEAT-0060
  - a general pin contract for other entity types

## Surface Lanes

- Mutation and read-model lane:
  - path roots: Session routes, queries, FEAT-0058 operations, and focused tests
  - dependencies: passed FEAT-0058
  - expected evidence: eligibility, pin/unpin result, pinned projection, current list/detail state, error behavior, and local-only execution
  - evaluator ownership: `contract`, `functional`
- Inventory presentation lane:
  - path roots: `templates/sessions.html`, shared styles, Session client behavior, and UI tests
  - dependencies: mutation and read-model lane
  - expected evidence: replaced panel, global recall, stable utility geometry, pin/Subsession click separation, responsive layout, and focus continuity
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Detail-control lane:
  - path roots: Session detail route/template, shared pin component behavior, and focused tests
  - dependencies: mutation and read-model lane
  - expected evidence: consistent current state, accessible action, error feedback, and preserved conversation orientation
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: product, Session behavior, design, interaction, and data-model owner docs
  - dependencies: all product lanes
  - expected evidence: current pin behavior and recovery without duplicating persistence truth
  - evaluator ownership: `contract`

## Contract Surfaces

- FEAT-0058 pin, unpin, eligibility, and pinned-list operations.
- Pin/unpin POST routes and progressive-enhancement response.
- Sessions inventory query state and pinned panel projection.
- Session row destination, pin control, and Subsession trigger click ownership.
- Filter, pagination, mode, scroll, focus, and no-script return state.

## User-Visible Outcome

- The owner can mark a primary work Session, see it in a stable Pinned Sessions panel, and reopen its LocalBrain detail without searching through recent activity.

## Entry And Exit

- Entry point: use the pin control on a Session row or Session detail.
- Exit or transition behavior: the current page retains orientation, the control exposes the new state, and the Pinned Sessions panel adds or removes the Session deterministically.

## State Expectations

- Unpinned: outlined or otherwise explicit inactive pin control; Session absent from the pinned panel.
- Pinned: pressed control with an explicit filled glyph and no independent square background; Session present in displayed-activity order.
- Empty: explains how to pin a Session and contains no recent or inferred substitute.
- Error: current pin state remains truthful and feedback stays adjacent to the action.
- Missing/deleted: stale panel entry is not rendered as reopenable.
- Narrow: essential pin and Subsession actions remain reachable without title or date overlap.

## Dependencies

- PRD-0009 is `approved`.
- FEAT-0058 must be `passed` before this Feature enters build.
- PRD-0002 Session inventory/detail and PRD-0006 Session reading behavior remain passed regression contracts.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- `src/localbrain/queries.py`
- `src/localbrain/templates/sessions.html`
- `src/localbrain/templates/session.html`
- `src/localbrain/static/app.js`
- `src/localbrain/static/styles.css`
- Session inventory, detail, UI contract, route, and migration integration tests
- product, interaction, and Data Model owner docs

## Pass Or Fail Checks

- Pass if pin/unpin from inventory and detail updates one FEAT-0058 row and preserves current page orientation.
- Pass if Pinned Sessions replaces recent Context and is never auto-populated.
- Pass if pinned entries remain global and clearly identify source, activity, and workspace/path.
- Pass if rows with and without Subsessions align `질문 → 이벤트 → 날짜 → 핀` and the optional lower Subsession trigger according to the approved utility layer at `1440`, `920`, `700`, and `320`.
- Pass if pin state remains perceivable without color and exposes correct label, pressed state, focus, and touch geometry.
- Pass if clicking pin or Subsession never navigates to the parent Session.
- Pass if no-script actions remain executable and mutation errors do not lie about state.
- Fail on recent-document fallback, layout shift, nested interactive controls, filtered-away global pins, automatic pinning, or source-file writes.

## Regression Surfaces

- PRD-0002 pagination, filters, Sessions/Projects mode, primary/Subsession grouping, and Session-only sync.
- PRD-0006 conversation reading and navigation continuity.
- Existing Subsession disclosure positioning and interaction binding.
- Sessions Dashboard and Projects inventory.
- Responsive shell and repository privacy.

## Harness Trace

- Active spec doc: [spec-0059-pinned-session-recall-and-controls](../spec/spec-0059-pinned-session-recall-and-controls.md)
- Active run: [run-20260724-64](../run/run-20260724-64-pinned-session-recall-and-controls.md)
- Execution profile: `fullstack-product`
- Latest evaluator report: [eval-0059-ux-pinned-session-recall-and-controls](../evaluation/eval-0059-ux-pinned-session-recall-and-controls.md) — `PASS`
- Latest fix note: not created

## Closed Review Decisions

- Wide layouts start the panel's internal scroller at `420px`; narrow layouts expose all pins in ordinary document flow.
- The final panel title is `Pinned Sessions`, matching the approved product term.
- `2026-07-27`: owner follow-up removed the visible pin-button outline while preserving its hit-area geometry, reduced each pinned entry's source/date metadata row to the date because the source icon already carries identity, and changed enhanced pin mutations to update in place without moving document or panel scroll.
- `2026-07-27`: owner follow-up changed Pinned Sessions to displayed-activity-date descending order and removed the pin button's independent square background so pressed state does not recolor it and row hover remains visually continuous.
- `2026-07-27`: owner follow-up fixed stable left starts for the question and event columns across Session rows and kept an already pinned glyph blue on hover.
- `2026-07-27`: owner follow-up removed the repeated `Subsession` role label from each Subsession dropdown entry; the dropdown heading already establishes that context, so entries retain only question and event counts.

## Continuity Notes

- `2026-07-24`: initial draft replaced recent Context with user-curated recall and fixed one trailing utility layer for date, pin, and optional Subsession controls.
- `2026-07-24`: moved question and event counts immediately left of the date in the upper utility row while retaining the pin at the outer upper corner and Subsession at the lower trailing edge.
- `2026-07-24`: passed Run 64 with uncapped global recall, inventory/detail controls, safe return targets, visible error recovery, stable row utility geometry, and synthetic browser evidence at `1440`, `920`, `700`, and `320`.
