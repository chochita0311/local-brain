# FEAT-0087: Session Workflow Focus Map

## Metadata

- ID: `feat-0087`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0017: Source-Backed Workflow Map And Workstream Lenses](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-14`
- Updated: `2026-09-14`

## Goal

- Let the user open a separate, stable Focus Map from an eligible Session and
  understand what likely led to it, what continued or branched, and which
  cross-source evidence supports each visible connection.

## Acceptance Contract

- Eligible primary Session detail exposes one additive `작업 흐름` action.
  Existing conversation reading, pinning, metadata, Subsession disclosure, and
  Related Materials remain in their current hierarchy and behavior.
- The action opens `GET /sessions/{session_id}/workflow`. Subsessions,
  Maintenance Sessions, missing Sessions, and provider-internal records do not
  gain a misleading workflow action or projection.
- The route consumes only the passed FEAT-0086 payload. It performs no fallback
  query against source files, Session messages, Documents, connectors, or model
  services and issues no write.
- The selected Session Episode is the initial focus anchor. A horizontal time
  axis and deterministic branch lanes form the wide `flow spine`; at compact
  and narrow widths the same direction becomes a top-to-bottom lineage without
  changing relation meaning.
- The layout uses no continuous force simulation. Repeated entry with unchanged
  data produces the same node order and branch placement.
- Selecting an Episode illuminates its supported ancestor, descendant, branch,
  and merge path; dims unrelated visible context without hiding orientation;
  keeps the selected node in place; and reveals its bounded evidence
  constellation and adjacent Trace inspector.
- Selecting another Episode updates browser history to that Session's canonical
  workflow route. Back, forward, direct entry, and return from an existing
  source destination restore the same focused Episode without returning the
  user to the Sessions inventory first.
- Each visible edge states `continues`, `branches from`, or `merged into`, marks
  deterministic candidate versus future user confirmation without color alone,
  and exposes the complete FEAT-0086 reason list.
- Evidence remains grouped by source family. Each item shows its source cue,
  kind, observation/freshness or unavailable state, reason for inclusion, and
  existing safe destination. Expanded evidence does not move the selected
  Episode or turn artifacts into peer flow nodes.
- An unconnected Session is a valid single-Episode Focus state with its own
  evidence and an honest explanation that no supported predecessor or
  successor was found. It is not presented as an error or completed workflow.
- Visible controls provide zoom out, current scale/reset, zoom in, and fit.
  Modifier-wheel or pinch may zoom around the pointer; ordinary wheel and
  trackpad movement retain page or bounded-canvas scrolling ownership.
- Pointer, keyboard, and non-pointer paths can select Episodes, inspect edges,
  expand a bounded branch, open evidence, fit/reset the map, and return.
  Selection, relation, lifecycle, and truncation meaning never depends on hover,
  glow, animation, or color alone.
- Reduced motion preserves all meaning. The graphical surface has a readable
  server-rendered lineage/evidence fallback for no-script, renderer failure,
  narrow layout, and assistive navigation.
- Loading, partial, unconnected, stale/unavailable evidence, render-failure,
  ineligible, not-found, and unexpected-error states retain a clear Session
  destination and never imply a source refresh or lost evidence.
- The first Focus Map is read-only. It contains no same/split/merge/close/reopen
  action, Workstream promotion, Atlas, topic terrain, Qwen, embeddings, or
  generated summary.

## Scope Boundary

- In:
  - additive eligible-Session workflow action
  - separate Session Workflow route and Focus read model handoff
  - deterministic flow-spine and evidence-constellation presentation
  - click-to-illuminate selection and bounded branch disclosure
  - Trace inspector with relation reasons and source evidence
  - zoom, reset, fit, keyboard, browser history, responsive, reduced-motion,
    no-script, and renderer-failure behavior
- Out:
  - mutation, user correction, Workstream naming/promotion, lens, or Atlas
  - projection caching, ingestion, background work, source refresh, or remote I/O
  - semantic similarity, topic terrain, Qwen, embeddings, or summaries
  - redesign of Session detail, Related Materials, Workstream, or the shell

## Surface Lanes

- Backend/route lane:
  - path roots: workflow route/controller, FEAT-0086 projection consumer, route
    and integration tests
  - dependencies: passed FEAT-0086 payload
  - expected evidence: eligibility, canonical entry, local-only read, error,
    direct entry, history destination, and zero-write behavior
  - evaluator ownership: `contract`, `functional`
- Frontend/map lane:
  - path roots: Session detail action, workflow template/partials, dedicated
    map controller, shared semantic styles, synthetic fixtures
  - dependencies: stable route payload
  - expected evidence: flow/evidence/Trace hierarchy, deterministic placement,
    focus stability, controls, fallback, accessibility, and four widths
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Integration/regression lane:
  - path roots: Session, Workstream, Local Context, Atlassian, navigation, and
    privacy regression tests and owner docs
  - dependencies: both implementation lanes
  - expected evidence: source destinations and current flows remain unchanged
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- `GET /sessions/{session_id}/workflow` and eligible Session-detail entry.
- FEAT-0086 payload consumption with no alternate producer.
- Episode/edge/evidence DOM semantics and text fallback.
- Focus selection, canonical history, direct entry, destination return, and
  branch-expansion state.
- Canvas input ownership, visible controls, deterministic layout, and responsive
  transformation.

## Required Evaluators

- `contract`: route, projection, eligibility, source destination, local-only
  read, browser-state, and fallback contracts.
- `design`: source/authority semantics, hierarchy, stable time direction,
  technical-canvas controls, evidence containment, and `1440`/`920`/`700`/`320`
  rendering.
- `functional`: entry, selection, expansion, controls, back/forward, direct
  entry, error/fallback, keyboard, no-script, and current-flow regressions.
- `ux-heuristic`: reconstruction clarity, relation trust, branch orientation,
  evidence disclosure, scroll ownership, and interaction friction.

## User-Visible Outcome

- From a Session, the user can open a calm directional map, follow its supported
  local workflow line, inspect why a connection exists, and reach the original
  evidence without manually building a Workstream first.

## Entry And Exit

- Entry point: `작업 흐름` on eligible primary Session detail or a direct
  `/sessions/{session_id}/workflow` URL.
- Exit or transition behavior: open another Episode's canonical Focus route,
  open an existing source detail and return through browser history, or return
  to the owning Session detail with focus preserved.

## State Expectations

- Default: selected Episode, supported lineage, bounded branches, evidence
  counts, and Trace inspector are legible.
- Loading: only local projection/render preparation owns bounded progress; no
  connector or model language appears.
- Unconnected: one Episode and its evidence remain useful.
- Partial: collapsed node/branch/evidence totals state what is omitted.
- Stale/unavailable: last-known evidence remains visibly qualified.
- Error/render failure: textual lineage/evidence and Session return remain.
- Success: focus, history, source destination, and spatial orientation are
  stable through repeated interaction.

## Dependencies

- FEAT-0085 and FEAT-0086 must be `passed` before this Feature enters build.
- The Workflow Map Design Plan remains the active design-sequencing owner.
- Existing Schema Explorer controls are interaction precedent, not a mandated
  renderer or reusable component without implementation review.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- FEAT-0086 workflow projection owner
- `src/localbrain/templates/session.html`
- a dedicated workflow template and bounded partials under
  `src/localbrain/templates/`
- a dedicated workflow controller under `src/localbrain/static/`
- `src/localbrain/static/styles.css`
- route, projection-consumer, UI-contract, interaction, and browser tests
- product, architecture, design, interaction, and privacy owner docs as needed

## Pass Or Fail Checks

- Pass if eligible Session detail adds one separate Focus entry while every
  existing Session behavior remains unchanged.
- Pass if unchanged input yields stable topology and selection does not
  randomize or relocate the selected Episode.
- Pass if the user can answer what led here, what continued or branched, and
  why each visible edge exists without opening full Session contents.
- Pass if unconnected and truncated histories are honest, navigable states.
- Pass if edge authority, lifecycle, selection, source, and availability remain
  distinguishable without color or motion alone.
- Pass if controls, keyboard, reduced motion, no-script/failure fallback,
  browser history, source return, and all four target widths work.
- Pass if route entry, focus, expansion, and evidence inspection trigger no
  write, source scan, remote read, Sync/Refresh, capability check, or model call.
- Fail on a force-directed hairball, flat peer source nodes, hidden truncation,
  or contamination of the authoritative Related Materials rail.

## Regression Surfaces

- Sessions and Projects inventories, pins, synchronization, and source cues.
- Primary Session conversation, metadata, Subsessions, and Related Materials.
- Workstream/Thread/checkpoint/Resource/Suggestion behavior.
- Local Context and Atlassian Explorer/detail/Sync/Connections/Refresh flows.
- Search, Schema technical canvas, Task Runner, shell navigation, and privacy.

## Harness Trace

- Spec doc: [SPEC-0087](../spec/spec-0087-session-workflow-focus-map.md).
- Run: [RUN-20260914-97](../run/run-20260914-97-session-workflow-focus-map.md).
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  [contract](../evaluation/eval-0087-contract-session-workflow-focus-map.md),
  [design](../evaluation/eval-0087-design-session-workflow-focus-map.md),
  [functional](../evaluation/eval-0087-functional-session-workflow-focus-map.md),
  and [UX heuristic](../evaluation/eval-0087-ux-session-workflow-focus-map.md).
- Latest fix note: not created.

## Open Review Decisions

- None. The owner approved the separate Session route and read-only Focus
  boundary. SPEC-0087 selected the fixed route-scoped DOM/SVG renderer, and the
  rendered interaction and fallback evidence passed.

## Continuity Notes

- `2026-09-14`: proposed as the first user-visible PRD-0017 slice. It is
  additive to Session detail, uses the Fullstack Product profile with explicit
  backend/frontend/integration lanes, and remains planning-only.
- `2026-09-14`: owner approved sequential execution. FEAT-0087 remains queued
  behind passed FEAT-0085 and FEAT-0086 foundation Features.
- `2026-09-14`: FEAT-0085 and FEAT-0086 passed; RUN-20260914-97 entered Build
  under the Fullstack Product profile and `screen-alignment` extend mode.
- `2026-09-14`: all four required evaluators passed. The separate route retains
  deterministic fixed layout, complete textual fallback, source-backed Trace,
  zero writes, no model dependency, and the unchanged Session reading surface.
