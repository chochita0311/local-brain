# SPEC-0087: Session Workflow Focus Map

## Metadata

- ID: `spec-0087`
- Status: `approved`
- Run: [RUN-20260914-97](../run/run-20260914-97-session-workflow-focus-map.md)
- Attempt: `1`
- Parent Feature: [FEAT-0087](../feature/feat-0087-session-workflow-focus-map.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `backend/route -> frontend/map -> integration/docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-09-14`
- Updated: `2026-09-14`

## Source Set

- Human approval to execute FEAT-0085 through FEAT-0089 in dependency order.
- Passed FEAT-0085 Episode/direction contract and FEAT-0086 deterministic Focus
  projection.
- Approved FEAT-0087 and the Workflow Map Design Plan.
- Current Session detail, Related Materials, Schema technical canvas, shared
  shell, Design Constitution, Design Evaluation, and Interaction Evaluation.
- `screen-alignment` skill in `extend` mode.

## Implementation Goal

- Add one separate, read-only Session Workflow route that presents the passed
  FEAT-0086 projection as a stable time-directed Episode map, makes every
  relation and evidence admission inspectable, and leaves all existing Session
  reading and organization behavior intact.

## In-Scope Behavior

- Add a narrowly shared workflow eligibility predicate matching FEAT-0086:
  `work`, `primary`, `full`, plus a positive normalized event count, persisted
  Activity Event, or Usage Record. Session detail uses only this predicate to
  decide whether to show one `작업 흐름` link; predicate failure is isolated
  and never blocks the current detail page.
- Add `GET /sessions/{session_id}/workflow`. The controller invokes
  `workflow_focus_projection` once and passes that result to a pure
  presentation adapter. It performs no alternate Session, file, connector,
  model, source-body, or document-body lookup and no write.
- Render `ready` as a selected Episode, bounded topology, honest retained/
  observed totals, and adjacent Trace. Render `missing` with HTTP `404`,
  `ineligible` with HTTP `422`, and unexpected projection failure with HTTP
  `500`; each state has a Sessions or exact Session destination and leaks no
  exception or native source identity.
- The server emits every retained Episode, relation, complete reason list, and
  evidence group in semantic HTML before enhancement. This ordered lineage is
  the no-script, assistive, narrow, and renderer-failure fallback.
- A dedicated controller validates the embedded FEAT-0086 JSON and enhances it
  into one fixed-layout graph. It sorts by observation and stable Episode key,
  assigns `continues` to the current lane and each `branches-from` target to a
  stable next lane, and uses no random value, timer-dependent placement, or
  force simulation.
- Wide layout runs left-to-right across time; compact layout runs top-to-bottom
  with lanes across the secondary axis; narrow layout makes the textual
  lineage primary. Breakpoint changes preserve relation meaning and selection.
- Selecting an Episode retains its coordinates, explicitly labels it selected,
  illuminates its incoming ancestry and outgoing descendants, dims other
  visible context, swaps the adjacent Trace panel, announces the change, and
  pushes `/sessions/{session_id}/workflow` into browser history.
- Back/forward restores an Episode already present in the projection without a
  reload. If history targets an Episode outside the current bounded payload,
  normal navigation loads its canonical projection. Direct entry starts with
  the route-owning Episode selected.
- Each graph edge and Trace relation exposes canonical `continues`,
  `branches from`, or `merged into` text, authority text, direction, and every
  FEAT-0086 reason kind/identity. Edge inspection is reachable by pointer and
  keyboard and never changes durable state.
- A non-selected bounded side branch initially exposes its root and an
  explicit branch disclosure. Expanding it reveals only Episodes already
  present in FEAT-0086; collapsing cannot discard a focused descendant.
- Trace groups evidence by source family. Items retain source cue, evidence
  kind, admission reason, observation/freshness or unavailable state,
  authority, and only the FEAT-0086 safe destination. Evidence never becomes a
  graph node.
- Visible zoom-out, scale/reset, zoom-in, and fit controls operate around a
  stable canvas. Ctrl/Cmd-wheel zooms around the pointer; ordinary wheel and
  trackpad scrolling remain owned by the page or bounded viewport. Controls
  stay disabled until enhancement succeeds.
- Renderer validation/failure opens the textual fallback and preserves Trace.
  `prefers-reduced-motion` removes nonessential transitions. Focus,
  selection, relation, authority, availability, and truncation use text or
  programmatic state in addition to visual treatment.
- An unconnected `ready` result remains a valid one-Episode view with evidence
  and an explicit abstention explanation; it is never called complete.

## Out-Of-Scope Behavior

- Relation, lifecycle, Workstream, Thread, evidence, or source mutation.
- Same/split/merge/close/reopen correction controls; these belong to FEAT-0088
  and FEAT-0089.
- Workstream lens, Atlas, topic terrain, generated intent/outcome/summary,
  embeddings, Qwen, or any remote/model call.
- Projection cache, ingestion, Sync, Refresh, background task, source-file
  read, or redesign of Session detail, Related Materials, or the shell.

## Affected Surfaces

- `src/localbrain/workflow_focus.py`
- `src/localbrain/workflow_map.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/session.html`
- `src/localbrain/templates/session-workflow.html`
- `src/localbrain/static/workflow-map.js`
- `src/localbrain/static/styles.css`
- focused projection-consumer, route, UI, JavaScript, and browser QA tests
- Product, Architecture, Design Constitution, interaction, privacy, plan, and
  harness artifacts where the implemented contract changes an owned fact

## Surface Lanes

- Backend/route:
  - owner: Builder
  - dependency: passed FEAT-0086
  - paths: workflow eligibility, presentation adapter, route, route tests
  - evidence: exact typed states, single producer call, no alternate query or
    write, and Session-entry isolation
  - evaluators: Contract and Functional
- Frontend/map:
  - owner: Builder
  - dependency: stable route payload
  - paths: Session link, workflow template/controller/styles, synthetic QA
  - evidence: deterministic layout, semantic fallback, focus/history/branch/
    zoom behavior, keyboard, reduced motion, and four widths
  - evaluators: Design, Functional, and UX Heuristic
- Integration/docs:
  - owner: Builder
  - dependency: completed backend and frontend lanes
  - paths: existing Session/source destinations, owner docs, regressions
  - evidence: current flows unchanged, privacy, complete suite
  - evaluators: Contract and Functional

## State And Interaction Contract

- Loading: the route HTML is already useful; only local enhancement is marked
  busy and controls remain disabled.
- Connected: selected Episode, directed path, branches, Trace, and totals are
  visible.
- Unconnected: one selected Episode and evidence remain; copy states that no
  supported predecessor or successor was found.
- Partial: observed versus retained Episode, branch, candidate, or evidence
  totals identify bounded omission.
- Stale/unavailable: the item remains in Trace with explicit state text.
- Render failure/no script/narrow: ordered semantic lineage and evidence remain
  the complete navigation path.
- Missing/ineligible/unexpected: bounded status copy and a valid local return
  destination remain; no recovery language implies refresh or lost data.

## Screen-Alignment Consistency List

- Retained structure: persistent shell, Session source/title hierarchy,
  backlink language, native panel headings, status badges, semantic buttons,
  source cues, focus ring, and textual detail lists.
- Retained visual roles: current type scale, spacing, surfaces, borders, radii,
  elevation, source/status vocabulary, `920`/`700` breakpoints, and `320` floor.
- Technical-canvas precedent: Schema zoom group, bounded viewport, modifier-
  wheel ownership, disabled-before-ready controls, and honest fallback.
- Deliberate extension: a fixed workflow flow-spine with Episode cards and an
  adjacent Trace rail inside the existing Explorer family.
- New state projection: `selected`, `related-path`, `dimmed-context`,
  `unconnected`, and `partial` remain derived presentation states, never new
  stored lifecycle values.
- Intentional non-reuse: Mermaid/ELK is not used because Episode selection,
  stable branch disclosure, and invariant coordinates require a small owned
  fixed renderer rather than a diagram-string adapter.

## Contract Surfaces

- Eligibility predicate and additive Session-detail action.
- `GET /sessions/{session_id}/workflow` status codes and local destinations.
- FEAT-0086 payload-only presentation adapter.
- Episode/relation/evidence semantic DOM and serialized data contract.
- Deterministic layout, selection/path, Trace, branch disclosure, history,
  zoom/fit, scroll ownership, fallback, and responsive behavior.

## Required Evaluators

- Contract: dependency, eligibility, route status, single producer, zero
  hidden I/O/write, evidence/authority/reason completeness, owner parity.
- Design: screen-alignment extend consistency, flow-spine hierarchy, source and
  state distinction, controls/fallback, and `1440`/`920`/`700`/`320` renders.
- Functional: route/entry, connected/unconnected/partial/error, selection,
  branch, edge, history, zoom, keyboard, no-script/failure, and regressions.
- UX heuristic: workflow reconstruction, orientation, trust, disclosure,
  scrolling, evidence reachability, and interaction friction.

## Acceptance Mapping

- Python tests cover eligibility, pure adapter, typed HTTP states, payload
  completeness, zero writes, source destinations, and current Session detail.
- Node tests cover stable lanes/coordinates, path selection, branch visibility,
  zoom math, ordinary-wheel ownership, and malformed-payload fallback.
- Synthetic Chrome QA covers direct entry, Episode/edge/branch interaction,
  history, controls, fallback, overflow, and exact four target widths.
- Focused and full suites plus owner checks, privacy, and diff checks cover
  existing Session, Workstream, Context, Atlassian, Schema, Search, and Runner.

## Open Blockers

- None.

## Continuity Notes

- `2026-09-14`: approved for RUN-20260914-97 after FEAT-0085 and FEAT-0086
  passed. Fullstack Product is active with backend/route, frontend/map, and
  integration/docs lanes.
