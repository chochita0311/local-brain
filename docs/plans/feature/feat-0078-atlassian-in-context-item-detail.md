# FEAT-0078: Atlassian In-Context Item Detail

## Metadata

- ID: `feat-0078`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0014: Atlassian Explorer And Unified Retrieval](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Goal

- Let the user inspect a selected Atlassian Item beside the Explorer list
  without losing hierarchy, query, filters, neighboring links, or browser
  history orientation.

## Acceptance Contract

- With no selected Item, the Explorer detail region presents one quiet,
  non-error instruction to select a link and does not auto-select or move the
  user's list position.
- Selecting a list row updates visible selection, programmatic current state,
  the adjacent detail identity, and URL/history as one coherent transition.
- Wide layouts keep hierarchy, list, and detail visible with intentional
  independent scroll ownership. Compact and narrow layouts open detail in a
  reachable side/full-width sheet or equivalent sequential region while the
  underlying list state remains restorable.
- Detail presents concise Item identity, service, Site/Space, canonical URL,
  coverage/freshness, last check, and external-open/Refresh/full-detail
  destinations before secondary diagnostics.
- Remote facts, local memory/classification, Session/Local Context evidence,
  Workstream/Thread organization, and maintenance history remain separate
  authority groups with empty/unavailable/stale/failure truth.
- The in-context region is read-first in this Feature. Existing local editing
  remains available through the full-detail fallback; moving edit forms into
  the pane is not required.
- Clicking through to full detail and returning restores the approved Explorer
  scope, query, filters, selection, and practical list position. In-place
  history preserves the current hierarchy disclosure DOM; a complete return
  render uses the approved URL-derived fallback—open for a Site, Space, or
  Unclassified scope and closed at the root—rather than persisting an arbitrary
  native disclosure toggle.
- Back and forward restore the same selected Item and required hierarchy
  orientation as click-driven selection. Direct entry with an Item identity
  produces the same state when the Item is eligible and an honest unavailable
  state when it is not.
- Rapid consecutive selections cancel or ignore superseded work so an older
  response cannot replace the latest Item. Loading preserves the prior stable
  list and hierarchy rather than clearing the workspace.
- Normal Item links remain valid server-executable fallbacks when JavaScript
  is unavailable or fragment replacement fails.
- Selecting and reading detail performs only bounded local reads and no
  provider, model, capability, scan, Refresh, or maintenance action.

## Scope Boundary

- In:
  - detail read model or fragment/response boundary
  - adjacent wide detail and compact/narrow detail sheet
  - selected row, URL/history, focus, scroll, and stale-response lifecycle
  - concise authority-group presentation and full-detail fallback
  - loading, empty, unavailable, stale, failure, and long-content states
- Out:
  - hierarchy, list, exact search, service scope, or filter redesign owned by
    FEAT-0077
  - local note/classification editing inside the in-context pane
  - one-URL Add, Connections relocation, or local Sync
  - remote Refresh execution changes
  - nested Page/issue hierarchy or AI retrieval

## Surface Lanes

- Detail read-model lane:
  - path roots: Atlassian Item detail projection, route/fragment boundary, and
    focused tests
  - dependencies: passed FEAT-0077 and existing full-detail ownership
  - expected evidence: bounded authority-group data, no hidden work, eligible/
    unavailable identity, and fallback parity
  - evaluator ownership: `contract`, `functional`
- Selection and history lane:
  - path roots: Explorer route state, local interaction controller, async
    replacement, cancellation, focus, and history restoration
  - dependencies: detail read-model lane and FEAT-0075 state contract
  - expected evidence: coherent selected state, rapid-selection safety,
    back/forward/direct entry, and no-script fallback
  - evaluator ownership: `contract`, `functional`, `ux-heuristic`
- Presentation lane:
  - path roots: Explorer/detail templates and semantic-token styles
  - dependencies: selection and history lane
  - expected evidence: authority separation, read-first hierarchy, scroll
    containment, responsive sheet behavior, and long/empty/error states
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: product/design/interaction owner docs
  - dependencies: completed runtime behavior
  - expected evidence: browse-to-preview and fallback parity
  - evaluator ownership: `contract`

## Contract Surfaces

- Item detail fragment or equivalent response shape.
- Selected Item URL/history state.
- Visible/programmatic selection and focus destination.
- Authority-group eligibility and ordering.
- Loading/cancellation/stale-response behavior.
- Full-detail and external destination fallbacks.
- Responsive detail sheet and scroll ownership.

## User-Visible Outcome

- Selecting an Atlassian link reveals its useful information beside or over
  the current Explorer without erasing the user's search and list context.

## Entry And Exit

- Entry point: select an eligible Item row or open an Explorer URL carrying a
  selected Item identity.
- Exit or transition behavior: select another Item, close compact/narrow
  detail, navigate back/forward, open full detail, open Atlassian, or enter
  Refresh preview without losing the approved return context.

## State Expectations

- Default: no selection and a quiet instruction.
- Loading: prior workspace remains stable; detail indicates bounded loading.
- Selected: row, URL, and detail identity agree.
- Empty/partial: known identity and available local facts remain visible;
  missing remote facts do not create a wall of empty diagnostics.
- Unavailable/not found: current scope remains; selection receives truthful
  bounded recovery and full-detail behavior where possible.
- Error: failed replacement cannot overwrite the previous stable detail and
  exposes a normal-link fallback.
- Narrow: detail owns the active sheet/focus state and returns focus to the
  selected row when closed.

## Dependencies

- FEAT-0075 and FEAT-0077 must be `passed` before this Feature enters build.
- Existing full-detail and explicit Refresh routes remain required fallbacks.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- `src/localbrain/atlassian_browse.py`
- `src/localbrain/templates/atlassian.html`
- `src/localbrain/templates/atlassian-item.html` only for shared partials or
  return-state parity
- a bounded Atlassian detail partial if introduced
- `src/localbrain/static/atlassian.js`
- `src/localbrain/static/styles.css`
- Item detail/read-model/route/history/UI tests
- product, design, and interaction owner docs

## Pass Or Fail Checks

- Pass if click, direct entry, refresh, back, and forward produce the same
  eligible selected Item, hierarchy orientation, visible/programmatic state,
  and meaningful focus.
- Pass if hierarchy disclosure, list scroll, query, filters, and pane state
  follow FEAT-0075 through repeated and rapid sibling selection.
- Pass if stale responses cannot overwrite the latest selection and failed
  enhancement leaves a functional normal link.
- Pass if remote, local, evidence, organization, and maintenance authorities
  remain distinct in full, partial, stale, unavailable, and empty data.
- Pass if synthetic `1440`, `920`, `700`, and `320` checks preserve contained
  scrolling, readable list/detail balance, sheet focus, and return behavior.
- Fail on automatic first-row selection, lost list context, false live/remote
  facts, in-pane edit scope, missing or inescapable modal focus containment,
  hidden fallback, or any hidden I/O.

## Regression Surfaces

- FEAT-0077 hierarchy, list, query, filter, and full-detail link behavior.
- Existing Item full-detail local edits, evidence, history, and external links.
- Explicit Refresh preview and return path.
- Local Context browse-to-preview history/focus interaction family.
- Shared shell, keyboard navigation, and repository privacy.

## Harness Trace

- Passed spec doc: [SPEC-0078](../spec/spec-0078-atlassian-in-context-item-detail.md), approved Attempt 2
- Completed run: [RUN-20260829-88](../run/run-20260829-88-atlassian-in-context-item-detail.md), passed Attempt 2
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  [Contract](../evaluation/eval-0078-contract-atlassian-in-context-item-detail.md),
  [Design](../evaluation/eval-0078-design-atlassian-in-context-item-detail.md),
  [Functional](../evaluation/eval-0078-functional-atlassian-in-context-item-detail.md), and
  [UX](../evaluation/eval-0078-ux-atlassian-in-context-item-detail.md), all `PASS`
- Latest fix note: none; evaluator findings were resolved inside Attempt 2

## Resolved Review Decisions

- Keep the pane read-first and retain all local editing on full detail.
- Do not auto-select an Item in the default Explorer state.

## Continuity Notes

- `2026-08-29`: proposed after PRD-0014 approval as a separate lifecycle from
  FEAT-0077 so the inventory remains executable before async detail is added.
- `2026-08-29`: FEAT-0077 passed. The owner's sequential approval activated
  this Feature, resolved both review decisions, and authorized SPEC-0078 and
  RUN-88 as the only current execution target.
- `2026-08-29`: a post-pass FEAT-0077 audit reopened its prerequisite. This
  Feature returned to draft/dependency wait before code build; its reviewed
  draft Spec remains as non-executing preparation.
- `2026-08-29`: RUN-87 Attempt 2 passed and restored the dependency. The owner's
  sequential approval reactivated FEAT-0078; SPEC-0078 resolves bounded preview
  reads, recent-history honesty, classification/metadata caps, and modal focus.
- `2026-08-29`: RUN-88 Attempt 2 passed all four required evaluators, the full
  394-test suite, repository privacy and owner-document checks, JavaScript and
  diff checks, plus synthetic Chrome evidence at `1440`, `920`, `700`, and
  `320`. FEAT-0078 passed and released FEAT-0079.
