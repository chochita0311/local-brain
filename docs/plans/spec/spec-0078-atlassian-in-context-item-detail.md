# SPEC-0078: Atlassian In-Context Item Detail

## Metadata

- ID: `spec-0078`
- Status: `approved`
- Run ID: `run-20260829-88`
- Attempt: `2`
- Parent Feature: [FEAT-0078](../feature/feat-0078-atlassian-in-context-item-detail.md)
- Parent PRD: [PRD-0014](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `preview read-model -> selection/history -> presentation -> docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Source Set

- Human decision: approve the proposed Features sequentially and continue to
  completion.
- Parent Feature and PRD: FEAT-0078 and PRD-0014.
- Passed foundations: FEAT-0075 Explorer/state contract and FEAT-0077 Explorer
  inventory/search.
- Golden runtime sources: current Atlassian full detail, Local Context and
  Schema progressive preview controllers, the FEAT-0077 hierarchy/list, and
  synthetic Atlassian fixtures.
- Durable baselines: Design Constitution, Product Model, Atlassian Source
  Memory, Design Evaluation, and Interaction Evaluation.
- Alignment skill: `screen-alignment` in `extend` mode.

## Implementation Goal

- Add a bounded, read-first Item preview to the current Atlassian Explorer so
  selection, URL/history, list position, focus, and full-detail/Refresh return
  context advance coherently without changing local or remote write behavior.

## In-Scope Behavior

- Add optional URL state `item=<positive local Item ID>` to `/atlassian` browse
  mode. Omission means no selection. Malformed, non-positive, or oversized
  values return one bounded local `400`; a positive unknown ID renders an
  honest missing selection in the detail region.
- Do not accept `item` in setup mode and never auto-select the first result.
- An Item is eligible only when its ID occurs in the current FEAT-0077 result
  list after service, structure, query, archive default, and advanced filters.
  Eligible selection marks exactly one row with `aria-current="true"` and one
  visible selected treatment.
- A known but ineligible Item renders a bounded out-of-scope state with concise
  identity, full-detail fallback, and clear-selection recovery. It does not
  mark a row or silently change query/scope/filter state.
- Preserve the normal row `href` to `/atlassian/items/{id}` as the executable
  no-script/failure fallback. Add a separate same-origin `data` selection URL
  carrying the current browse state plus `item=<id>` for enhancement only.
- Render the same server-authored preview on direct entry, refresh, enhanced
  click, and popstate. Enhanced clicks fetch the selection URL, parse only the
  preview region, and never rebuild the hierarchy or list.
- Enhanced requests send `X-LocalBrain-Partial: atlassian-item-preview` to the
  same selected URL. That response renders only the preview fragment and does
  not call the broad inventory/hierarchy/options projection. Eligibility is
  checked from the selected Item and only its query/filter memberships. Normal
  navigation without the header remains a complete server-rendered page.
- Before partial eligibility, validate any selected Space owner and the
  selected Site's known Item service with targeted structural queries using the
  same FEAT-0077 rules as the complete browse route. A cross-service Site or
  Space URL remains the same bounded local `400`; it must not be downgraded to
  an Item out-of-scope state. The partial path still does not load broad
  inventory, hierarchy, or options.
- Add one dedicated local preview projection. It may read only the selected
  Item and returns:
  - identity, service/type, title/key, Site/Space, canonical URL, coverage,
    freshness, attention, latest attempted check, last successful check, and
    latest outcome. `last_attempted_at` owns the concise `last check` fact;
    `last_successful_at` remains a separate success fact so a newer failed
    attempt cannot be presented as the last check.
  - remote ID/version/update/error plus at most `12` scalar metadata entries.
    Flatten nested maps using `.` between key segments, escaping `\` as `\\`,
    `.` as `\.`, `[` as `\[`, and `]` as `\]`; append zero-based array
    indices as unescaped `[n]`. This makes map segments distinguishable from
    typed array-index segments even when JSON keys contain brackets. Include strings,
    numbers, and booleans; exclude JSON null, empty containers, and the exact
    top-level `title` and `summary` identity fields. Preserve strings, render
    booleans as lowercase `true`/`false`, and render numbers as compact JSON.
    Sort by the full untruncated rendered path before taking the first `12`;
    a JSON tree has one value per full path, so no secondary tie exists. Each
    displayed path is at most `160` and each value at most `240` Unicode code
    points, with independent truncation cues; plus at most `1,200` Unicode code
    points of persisted normalized content
  - at most `600` Unicode code points of local note; Topic and Tag totals plus
    at most the first `30` selected values of each kind ordered by normalized
    name then stable ID, with independent truncation cues. These are preview
    caps and do not change full-detail editing limits.
  - evidence total plus the five newest sightings
  - organization total plus the first five Workstream/Thread memberships in
    current stable order
  - the newest matching refresh Run observed within the latest `200` global
    external-sync Runs ordered by `created_at DESC, id DESC`, tagged
    `history_scope=recent-200` and
    `history_complete=false`; no match is labeled “not found in recent
    history,” never “never refreshed”
- Truncation appends one ellipsis without splitting surrogate pairs; a boolean
  `truncated` cue makes each excerpt honest. The preview never loads editing
  options, all Workstreams, provider capability, source files, Session bodies,
  Document bodies, live remote data/provider reads, or a model. Persisted
  last-known remote metadata and normalized content remain the bounded local
  preview facts defined above.
- Present identity and actions first, then distinct `Remote facts`, `Local
  memory`, `Found in`, `Organization`, and `Refresh history` groups. Empty,
  unavailable, and stale states remain textual and do not collapse authority
  boundaries.
- Preview actions are ordinary links: close/clear selection, external open,
  explicit Refresh preview, and full detail. Local note/classification/link
  editing remains exclusively on full detail.
- Full-detail fallback receives a canonical selected Explorer `return_to`.
  Thread that safe value through full-detail local-edit and relationship
  redirects so a successful or failed local edit does not erase selection.
- Item Refresh receives the same validated selected Explorer `return_to` and
  preserves it through preview, validation failure, execution redirect,
  polling/retry links, and the final return link. This changes navigation only,
  not Refresh eligibility, batching, provider, or execution behavior.

## Selection And History Lifecycle

- Service, structure, query, and advanced-filter transitions omit `item`, reset
  selection, and use the FEAT-0075 result-scroll reset behavior.
- Item selection preserves every browse parameter and current hierarchy/list
  DOM, disclosure state, outer page scroll, and result-list scroll.
- Before each enhanced load, abort the prior `AbortController`, increment a
  request generation, keep the prior stable preview mounted, set its
  `aria-busy=true`, and announce bounded loading.
- Adopt a response only when its generation is still current and its returned
  selected ID agrees with the requested ID. Abort and stale responses produce
  no DOM, selection, title, history, focus, or announcement change.
- After a successful click, replace only the preview region, update row selected
  state, update `document.title`, push one history entry, announce the selected
  identity, and move focus to the preview heading without changing list scroll.
- A same-row click with an already selected Item focuses the current preview
  heading and does not push duplicate history.
- Closing detail loads the canonical unselected Explorer state in place, pushes
  one history entry, clears programmatic selection, and returns focus to the
  previously selected row when it remains available. If missing or out-of-scope
  direct entry has no row anchor, close focuses the results heading instead.
- Back/forward fetches the current `/atlassian` URL without adding history.
  Restored selection focuses its preview heading; restored unselected state
  focuses the previously selected row when available. Initial direct entry does
  not force outer-page scrolling. Wide direct entry leaves normal document
  focus unchanged; compact/narrow direct entry moves focus into the open modal
  sheet so focus cannot remain behind it.
- On a complete server render for an eligible selected Item, including direct
  entry and return from full detail, the result-list scroller moves only as far
  as needed to make the selected row visible (`nearest` block alignment). It
  does not reset the list to the top or move outer-page scroll. Exact same-tab
  list offsets remain ephemeral history state; this nearest-visible anchor is
  the durable URL-only fallback for practical list position.
- In-place selection and history leave the existing compact hierarchy
  disclosure DOM untouched. A new complete render cannot recover an arbitrary
  prior native `<details>` toggle from URL state, so its approved deterministic
  fallback is open when URL structure identifies a Site, Space, or
  Unclassified node and closed at the root. This keeps the selected hierarchy
  orientation immediately reachable without introducing persisted pane state.
- On non-abort row-selection failure, leave the current stable workspace
  untouched and navigate through the row's normal full-detail `href`. On a
  close-link or Escape clear-selection failure, navigate through the ordinary
  canonical clear-selection `href` so the modal has a deterministic exit. On
  popstate failure, reload the server-authored current URL. A live status
  explains only failures that remain on the current page.

## Responsive Presentation Contract

- Wide (`>920px`): use three adjacent regions—hierarchy, independently
  scrollable result list, and independently scrollable read-first detail. The
  unselected detail is a quiet instruction, not an error or empty inventory.
- Compact (`701–920px`): keep the list in document flow and show selected detail
  in a bounded right-side sheet with a local scrim/close destination and its own
  vertical scroll. The hierarchy remains the FEAT-0077 disclosure.
- Narrow (`<=700px`): use the same DOM as a full-width bounded sheet below the
  sticky shell, with close first in focus order. Do not render an empty sheet
  when no Item is selected.
- The compact/narrow sheet is a named modal dialog: while open it traps Tab and
  Shift+Tab, makes the underlying Explorer inert, closes through its explicit
  action or Escape, and restores focus to the selected row or, when no row
  exists, the results heading. At breakpoint
  changes, preserve eligible URL-backed selection; CSS owns geometry while the
  controller normalizes dialog, inert, and focus state. Closing or changing
  width must not make the full-detail fallback unreachable.
- Modal positioning, scrim, inert state, and focus containment activate only
  after the Explorer controller initializes. A no-script direct selected URL
  renders the same selected preview as an in-flow sequential region after the
  list, with ordinary clear-selection and full-detail links; it is not styled
  or announced as an overlay. Normal no-script row activation continues to the
  full-detail `href`.
- Long title, URL, Site, Space, remote scalar, note, evidence identity, and Run
  text wrap or truncate within their semantic owner. No viewport may acquire
  horizontal page overflow.

## Out-Of-Scope Behavior

- Editing local memory/classifications/relationships inside the preview.
- Redesigning hierarchy, list, exact search, service scope, or advanced filters.
- One-URL Add, Connections relocation, local evidence Sync, AI retrieval,
  nested Page/issue hierarchy, remote Refresh execution, schema change, or new
  persisted pane state.
- Loading full Session, Document, source, or remote Item bodies as a side effect
  of selection.

## Affected Surfaces

- `src/localbrain/atlassian_browse.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/atlassian.html`
- a bounded Atlassian preview partial
- `src/localbrain/templates/atlassian-item.html`
- `src/localbrain/templates/atlassian-refresh.html`
- `src/localbrain/static/atlassian.js`
- `src/localbrain/static/styles.css`
- Atlassian preview/route/history/UI/Refresh tests
- Product Model, Design Constitution interaction detail, and Atlassian Source
  Memory where runtime ownership requires parity

## Surface Lanes

- Preview read model:
  - responsibility: one-Item bounded authority projection, caps, and no hidden I/O
  - dependency order: first
  - evaluator ownership: contract, functional
- Selection and history:
  - responsibility: `item` URL state, eligible/out-of-scope/missing states,
    progressive enhancement, stale suppression, focus, scroll, and fallbacks
  - dependency order: after preview projection
  - evaluator ownership: contract, functional, ux-heuristic
- Presentation:
  - responsibility: authority groups, wide adjacent detail, compact/narrow
    sheet, readable states, containment, and accessible selection
  - dependency order: after selection and history
  - evaluator ownership: design, functional, ux-heuristic
- Documentation:
  - responsibility: owner parity without duplicating implementation constants
  - dependency order: after runtime behavior is fixed
  - evaluator ownership: contract

## State And Interaction Contract

- Default: no `item`, no selected row, quiet wide detail; no compact/narrow sheet.
- Loading: prior stable preview and workspace remain visible; only preview busy
  and live status change.
- Selected: URL ID, preview ID, selected row, title, and announcement agree.
- Out of scope: URL ID retained, no row selected, concise known identity and
  recovery shown; scope does not mutate.
- Missing: URL ID retained, no row selected, missing message and clear action.
- Partial/stale/unavailable: identity and available local groups remain; remote
  absence or failure is explicit.
- Failed enhancement: no partial replacement; ordinary full-detail navigation
  remains executable.
- Full detail/Refresh: return path includes the selected Explorer state and is
  revalidated at every server boundary.

## Screen-Alignment Consistency List

- Retained components: shell, page/search/filter regions, hierarchy, result
  rows, native links, semantic buttons/statuses, detail cards, native sheet
  containment, focus ring, and live status.
- Retained visual roles: all current semantic type, spacing, color, border,
  radius, elevation, breakpoint, and scroll tokens.
- Deliberate change: the approved third Explorer region and compact/narrow
  detail sheet are activated; the list and hierarchy are not redesigned.
- Pattern sources: Local Context preview replacement and Schema history/stale
  request handling, adapted to Atlassian authority groups and normal full-detail
  row fallbacks.
- New design-system component: none.

## Contract Surfaces

- URL input/output: optional `item`, canonical selected/clear URLs, and bounded
  local `return_to` on full detail and item Refresh.
- Read projection: one selected Item, bounded metadata/content/note/classification
  values, capped evidence and membership lists, totals, and recent-200 Run
  observation.
- DOM: one stable preview root, one selected row at most, one live status, and
  normal row href plus enhancement-only selection URL.
- JavaScript: same-origin path checks, request abort/generation, partial adopt,
  history, focus, scroll, and full-navigation fallback.
- Data/external boundary: local SQLite reads only; no provider, model, scan,
  capability, Refresh, maintenance, or mutation side effect on selection.

## Required Evaluators

- Contract: query/return-path ownership, bounded read projection, authority
  separation, no hidden I/O, and owner-doc parity.
- Design: screen-alignment extend consistency, three-region balance, sheet,
  scroll ownership, selected/empty/error states, and four-width geometry.
- Functional: direct/click/popstate states, eligibility, stale suppression,
  no-script/failure fallback, full-detail/Refresh return, caps, and regressions.
- UX heuristic: selection orientation, progressive preview, focus/scroll,
  close/back/forward, compact sheet, recovery, and action clarity.

## Acceptance Mapping

- Read-model tests cover exact Item scope, truncation, caps/totals,
  classification, evidence, organization, recent-200 refresh observation, and
  zero live external/provider, source-file, Session/Document body, or
  unbounded source-body reads; only the bounded persisted normalized Item
  content excerpt is allowed.
- Route/template tests cover default, eligible, out-of-scope, missing, malformed,
  selected row, fallback/select URLs, authority groups, and return propagation.
- JavaScript contract and rendered browser checks cover click, repeat, rapid
  sibling selection, close, back/forward, direct entry, focus, scroll,
  disclosure preservation, fetch failure, and stale response rejection.
- Chrome checks at `1440`, `920`, `700`, and `320` cover independent scroll,
  sheet/scrim/close, containment, long content, selection, and no overflow.
- Focused/full tests plus privacy/diff checks cover current full detail, Refresh,
  FEAT-0077 list/search/hierarchy, shell, and no-script regressions.

## Evaluation Focus

- Confirm no selection auto-default and no list/hierarchy replacement.
- Confirm the preview projection avoids full-detail edit options and unbounded
  evidence, membership, Workstream, content, or source reads.
- Confirm rapid selection cannot commit stale DOM/history/focus.
- Confirm row href remains full detail and every return path is local/canonical.
- Confirm compact/narrow modal sheets contain focus, make the background inert,
  close and restore focus correctly, and never hide the normal fallback.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-29`: approved for RUN-88 after FEAT-0077 passed and the owner had
  authorized sequential Feature approval and execution. Read-first/no-default-
  selection decisions are locked.
- `2026-08-29`: returned to draft without implementation after the FEAT-0077
  dependency reopened. It may be re-approved only after RUN-87 Attempt 2 passes.
- `2026-08-29`: re-approved for RUN-88 Attempt 2 after RUN-87 passed. Preview
  classification/metadata/history caps, preview-only partial reads, and modal
  sheet focus ownership are locked with no schema or editing-contract change.
