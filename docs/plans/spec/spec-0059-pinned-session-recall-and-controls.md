# SPEC-0059: Pinned Session Recall And Controls

## Metadata

- ID: `spec-0059`
- Status: `approved`
- Run ID: `run-20260724-64`
- Attempt: `1`
- Parent Feature: [feat-0059-pinned-session-recall-and-controls](../feature/feat-0059-pinned-session-recall-and-controls.md)
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: pin read model → mutation continuity → inventory recall and controls → detail control
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-24`
- Updated: `2026-07-27`

## Source Set

- Human approval on `2026-07-24`: execute both approved PRDs' Features automatically and sequentially.
- Passed FEAT-0058 pin persistence, PRD-0002 Session inventory/detail, and PRD-0006 Session reading contracts.
- Current Sessions queries, routes, templates, styles, and Subsession behavior.
- Design Constitution, Design Evaluation, and Interaction Evaluation using the Fullstack Product profile.
- Screen Alignment mode: `extend`; the repository constitution is the target and no durable Figma file key is owned by the source set.

## Read-Model Contract

- Session inventory and persisted primary detail project `session_pins.pinned_at` with a left join.
- The global recall projection returns every eligible current pin, without a product item cap, by displayed activity (`COALESCE(last_event_at, started_at) DESC`) with `pinned_at DESC, sessions.id DESC` tie-breaks.
- Pinned entries include title, source kind/name, last activity, cwd/source path, and current workspace orientation.
- Active source, workspace, and page filters affect inventory rows only; they never filter the `Pinned Sessions` panel.
- Missing or deleted Sessions disappear through the physical FK lifecycle and are never emitted as reopenable panel entries.

## Mutation Contract

- `POST /sessions/{id}/pin` delegates to FEAT-0058 eligibility and idempotency.
- `POST /sessions/{id}/unpin` deletes only the current pin row and remains a safe no-op if the row is already absent.
- Both routes parse one bounded local form body and accept a return target only when it is `/sessions`, `/projects`, or one persisted Session detail path.
- External, malformed, and unsupported return targets fall back to `/sessions`; pin error codes are bounded and do not echo source content.
- Successful and failed redirects append `#session-pin-{id}`. Native fragment orientation works without script; the shared client updates return state from the current browser URL and restores focus to the changed control.
- Storage errors leave state truthful and render an adjacent control-owned alert. Missing and ineligible targets render a bounded page notice.
- Mutations write SQLite only. They never edit source files, Context, Git, models, MCP, or external systems.

## Inventory Presentation Contract

- Replace `최근 컨텍스트` with `Pinned Sessions`.
- Wide layouts cap panel height at `420px` and scroll internally; widths at or below the existing narrow breakpoint keep all entries in ordinary document flow.
- Every eligible row reserves the same utility geometry.
- Desktop and laptop upper order is `질문 → 이벤트 → 날짜 → 핀`; question and event use stable left-aligned columns across rows, and the optional Subsession trigger occupies the lower trailing edge.
- Narrow rows keep the pin at the upper trailing edge, preserve question/event/date DOM order while allowing wrap, and position optional Subsessions at the lower trailing edge.
- Pin and Subsession controls are siblings of, never descendants of, the Session destination link.
- Inactive and active pin states keep the same control box and transparent background, following the owning row or detail surface. Active state combines `aria-pressed`, changed label, and a filled pin shape without adding an independent square surface.
- Hover emphasis applies only to an inactive pin. An active pin keeps its information color while hovered.

## Detail Contract

- Persisted primary work Session detail exposes the same pin form and current state.
- Subsession detail exposes no pin form and retains parent orientation and conversation behavior.
- Pin focus margin keeps the post-mutation target below the sticky workspace header.

## Verification

```bash
uv run python -m unittest tests.test_session_pins tests.test_session_inventory tests.test_session_pin_ui tests.test_ui_contract -v
```

- Render a synthetic local database at `1440`, `920`, `700`, and emulated `320`.
- Compare rows with and without Subsessions, upper metadata order, pin corners, row heights, panel overflow, document overflow, accessible state, filter-global recall, pin/unpin focus, and detail eligibility.
- Confirm only localhost document/static requests and no console errors.

## Open Blockers

- None.
