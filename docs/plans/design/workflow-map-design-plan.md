# Workflow Map Design Plan

## Metadata

- Status: `active`
- Parent boundary:
  [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md),
  `approved`
- Created: `2026-09-14`
- Updated: `2026-09-15`
- Screen alignment: `reframe`
- Focus implementation alignment: `extend` within the current Session and
  Explorer families
- Planning profile: future `fullstack-product` with separate data/source and
  map-interaction lanes

## Purpose

- Reframe LocalBrain's editor-first Workstream experience into a source-backed,
  time-directed map that reveals how one effort developed, branched, received
  evidence, merged, or ended.
- Reconcile Quartz and Obsidian's approachable graph exploration with
  LocalBrain's stronger requirements for temporal direction, causal
  explanation, source authority, stable spatial memory, and light human
  correction.
- Sequence the design questions so the Focus interaction can be validated
  first, then a reviewable Workstream candidate-discovery boundary can be
  defined before global Atlas density, lens composition, or optional semantic
  terrain increases complexity.

## Plan Type

- Information-hierarchy reconciliation.
- Interaction and navigation consistency.
- Workstream candidate review and eventual workspace composition within the
  existing LocalBrain design system.

## Baseline

### Audited Sources

- [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md):
  approved product boundary and source/episode distinction.
- [Quartz Graph View](https://quartz.jzhao.xyz/features/graph-view): local and
  global graph, one-hop focus, visited state, drag, and zoom.
- [Obsidian Graph View](https://obsidian.md/help/plugins/graph): local depth,
  filters, direction display, force controls, navigation, and chronological
  playback.
- Current `Workstream` detail: editor-first hierarchy of checkpoint, Runner,
  Threads, resources, Suggestions, and manual forms.
- Current primary `Session` detail: readable conversation plus bounded direct
  evidence and explicit-organization rail.
- Current `Schema` Explorer: visible zoom/reset/fit controls, pointer-anchored
  zoom, bounded canvas, deterministic fallback, focus, and history behavior.
- Current Sessions inventory and Project grouping: stable Session identity,
  source cue, branch metadata, activity time, pin, and bounded grouping.

### Constitution And Owner References

- [Design Constitution](../../policies/design/design-constitution.md)
- [Design Document Governance](../../policies/design/design-document-governance.md)
- [Design Evaluation](../../policies/design/design-evaluation.md)
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md)
- [Product Model](../../policies/project/product.md)
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md)

### Source Reconciliation

| Source | Adopt | Adapt | Reject |
| --- | --- | --- | --- |
| Quartz | local/global scope, bounded neighborhood, hover/focus, pan/zoom | local scope becomes lineage plus evidence; global becomes bounded Atlas | degree as workflow importance, force position as meaning, every note as a peer node |
| Obsidian | local depth, filters, direction cue, keyboard navigation, chronological inspection | chronological playback becomes work-history scrubbing only if it improves reconstruction | continuous force motion, link tension as causal strength, flat vault-wide hairball |
| LocalBrain Schema | visible controls, fit/reset, modifier/pinch zoom, bounded overflow, fallback | reuse the interaction contract while selecting a renderer suitable for dynamic focus and branches | treating static Mermaid output as the predetermined Workflow Map renderer |
| Current Workstream | named identity, user authority, evidence review, status context | move editing and correction into contextual secondary surfaces | form completion as the prerequisite for seeing a useful Workstream |
| Current Session detail | Session reading, source provenance, exact evidence reasons | add a workflow entry without contaminating the authoritative related rail | mixing inferred workflow proximity into direct-reference groups |

## Scope

- Define one coherent visual grammar for `flow spine`, `evidence
  constellation`, and optional `topic terrain`.
- Define the semantic zoom relationship among `Atlas`, `Focus`, and `Trace`.
- Make Focus the first validation target: one selected Episode, its supported
  lineage, bounded branch neighborhood, current tips or terminal events, and
  adjacent evidence explanation.
- Define stable selection, expansion, collapse, pan, zoom, fit, reset, direct
  entry, browser history, keyboard focus, reduced motion, and diagram fallback.
- Define how observed, inferred, explicit-organization, and user-confirmed
  relationships remain distinguishable without relying on color alone.
- Define how source identity, freshness, availability, lifecycle, activity,
  and epistemic authority coexist without collapsing into one visual state.
- Plan wide, compact, and narrow transformations at the existing `920` and
  `700` breakpoints and validate the supported `320` floor.
- Use synthetic representative histories for all tracked design artifacts and
  evaluation evidence.

## Non-Goals

- Writing Specs, selecting a renderer, or changing schema, queries, routes,
  templates, JavaScript, CSS, or runtime behavior before the selected child
  Feature passes human boundary review.
- Restyling the persistent LocalBrain shell or importing Quartz/Obsidian's
  product chrome, tokens, typography, force settings, or generic graph theme.
- Making visual richness depend on Qwen, embeddings, generated summaries, or
  topic clusters.
- A decorative global graph, freeform whiteboard, manual saved node positions,
  arbitrary relation drawing, or continuous background animation.
- Showing every source record, Activity Event, document, URL, or message as a
  peer node.
- Replacing Session reading, Atlassian Explorer, Local Context Explorer,
  Search, or Schema with the Workflow Map.
- Deciding the migration or removal of existing Threads in this design plan.
- Treating visit frequency, link degree, Session count, token volume, or visual
  centrality as work importance.

## Invariants

- Time has a stable direction and ordinary focus changes do not randomize node
  positions.
- The selected Episode remains the interaction anchor while branches and
  evidence expand around it.
- The map is useful without topic terrain and without any AI capability.
- A source artifact stays subordinate to the workflow line until its approved
  product contract makes it an independent Episode.
- Direct evidence, inferred relation, explicit organization, and user
  confirmation remain structurally and textually distinguishable.
- Main/supporting presentation is relative to the selected Workstream lens and
  never becomes a global ranking of the user's work.
- Quietness and closure are independent. No inactivity treatment may look like
  confirmed completion.
- Source provenance color identifies origin only; selection, confidence,
  lifecycle, and priority retain separate non-color cues.
- Essential actions have visible controls and keyboard paths. Hover, glow,
  animation, wheel gestures, or force motion never carry essential meaning.
- Desktop canvas interaction does not create a nested-scroll trap when the map
  becomes sequential content at compact or narrow widths.
- A textual lineage and evidence path remains available when graphical
  rendering fails or is inappropriate.

## Findings

### F-01: A Document-Link Graph Does Not Explain Work Direction

- Quartz and Obsidian make connection density approachable, but their default
  node/edge model does not distinguish continuation, branch, contribution,
  merge, blockage, supersession, or closure.
- LocalBrain must make direction and relation meaning legible before visual
  density or global coverage.

### F-02: Force Layout Weakens Spatial Memory

- Repulsion and link tension help separate a static note graph but can relocate
  context during expansion and make the same history feel different across
  visits.
- Workflow placement should use a stable time axis and deterministic branch
  lanes. Motion may explain a local expansion but must settle without changing
  the remembered topology.

### F-03: Flat Source Nodes Recreate The Radial-Inventory Problem

- Sessions, Jira, Wiki, Local Contexts, Git, Slack, and Mail carry different
  authority and granularity.
- Treating all records as peer circles produces a source catalog rather than a
  story of work. The selected Episode owns a bounded evidence constellation;
  other artifacts remain collapsed until needed.

### F-04: The Current Workstream Surface Requires Organization Before Value

- Current checkpoint, Thread, link, and editing forms place the maintenance
  burden before the user can observe a coherent flow.
- The target composition leads with the derived story and current tips. Editing
  becomes a contextual correction or durable naming task.

### F-05: Visual Richness Must Come From Work State

- Repeated circles and lines are visually monotonous, but decorative gradients,
  random physics, and constant animation would add spectacle without meaning.
- Temporal distance, branch geometry, activity ticks, terminal markers,
  evidence density, source glyphs, selection depth, and progressive reveal can
  create variation while remaining informative.

### F-06: Global Coverage Needs A Focus Budget

- A complete cross-source graph will grow faster than a single readable
  canvas. Showing it all by default would reproduce the hairball problem even
  with a directional layout.
- Atlas should lead with bounded active/recent tips and named lenses. Focus
  should reveal only the selected lineage and a controlled neighborhood. Trace
  should own the detailed evidence.

## Target Visual Grammar

### Layer 1: Flow Spine

- Horizontal direction represents time at wide viewports; narrow presentation
  may become a top-to-bottom lineage while preserving relation direction.
- A stable trunk expresses the selected lens. Supporting, alternative, blocked,
  superseded, and merged paths use distinct geometry, endpoint markers, and
  readable relation labels rather than color alone.
- Meaningful temporal gaps may appear as compressed breaks or labeled distance;
  they do not imply a workflow ended.
- Activity ticks may summarize bounded source-backed work along a segment, but
  event volume does not change the line into an importance score.

### Layer 2: Evidence Constellation

- Selecting an Episode reveals a bounded ring or adjacent cluster of Session,
  Jira, Wiki, Local Context, Git, and future source artifacts.
- Each artifact keeps its own compact source cue, kind, availability/freshness,
  and reason for appearing. It links to the owning detail surface.
- The constellation expands without moving the selected Episode or rebuilding
  the whole map. Overflow collapses by source group with honest retained totals.

### Layer 3: Topic Terrain

- Topic terrain is an optional soft background region or contour. It may orient
  related paths but does not become a parent, branch, Workstream, or authority.
- The deterministic first boundary may derive only explicit Project, Jira,
  Workstream, or other named areas. If that evidence is weak, the terrain is
  omitted instead of replaced by an invented cluster.
- A later semantic model may propose terrain behind a separate provenance and
  evaluation boundary. The Flow Spine remains unchanged when that capability
  is unavailable.

### Semantic Zoom

| Scale | Primary question | Visible structure | Deferred detail |
| --- | --- | --- | --- |
| Atlas | What work is alive, quiet, or recently closed? | named Workstream lenses, bounded tips, broad branch shape, activity/closure state | individual evidence and most Episode labels |
| Focus | How did this effort reach its current point? | selected Episode, lineage, bounded branches/merges, tips, terminal markers, immediate evidence counts | full source contents and distant unrelated lines |
| Trace | Why is this node or edge here? | intent/outcome fields when supported, source-grouped evidence, relation reasons, freshness, authority, destinations | global topology |

## Target Interaction

### Click-To-Illuminate

1. Single selection locks one Episode as the focus anchor.
2. Its supported ancestors, descendants, and branch/merge path gain primary
   emphasis while unrelated context dims but remains locatable.
3. A bounded evidence constellation and relationship explanation become
   available only after the destination data is ready.
4. Expanding another branch preserves scale, selected position, canvas scroll,
   shell, and browser history orientation.
5. Opening a source destination retains a deterministic return path to the same
   map focus.

### Control Ownership

- Visible `zoom out`, `current scale/reset`, `zoom in`, and `fit` controls follow
  the existing technical-canvas family unless the approved Feature establishes
  a more specific reusable role.
- Modifier-wheel or pinch zoom preserves the pointer neighborhood. Ordinary
  wheel/trackpad motion remains page or bounded-canvas scrolling.
- Selection and correction actions belong to the selected Episode/edge
  inspector, not to ambiguous blank canvas space.
- An inferred relation exposes `inspect reason` before any correction. A user
  action states whether it confirms continuity, creates a split assertion,
  merges into a known line, closes with a reason, or reopens a tip.

## Planned Work

### Batch 1: Source And State Storyboards

- Goal: lock the minimum visual states before selecting a renderer or creating
  a product Feature.
- Why this grouping: source authority, relation authority, activity, lifecycle,
  and selection must remain independent or every later screen will encode
  ambiguous state.
- Guardrails: synthetic data only; no new token, state, route, schema, or
  model assumption.
- Targets: observed origin, open tip, quiet tip, completed tip, merged branch,
  inferred edge, confirmed edge, abstained Session, stale evidence, unavailable
  evidence, and diagram failure.
- Validation: side-by-side information-hierarchy review against the
  constitution and PRD-0017 source map.
- Exit gate: every state can be explained without color, motion, or opening a
  source detail.
- Proposed Feature owners:
  [FEAT-0085](../feature/feat-0085-workflow-episode-and-direction-contract.md)
  and
  [FEAT-0086](../feature/feat-0086-deterministic-cross-source-workflow-projection.md).

### Batch 2: Focus Interaction Prototype

- Implementation state: `passed`. RUN-20260914-97 delivered the deterministic
  Session entry, fixed wide/compact map, narrow and no-script lineage,
  selected-path illumination, bounded branch disclosure, adjacent Trace,
  browser history, and zoom/fit controls. Contract, Design, Functional, and UX
  Heuristic evaluations all passed.

- Goal: validate the tree-like local map and click-to-illuminate behavior on one
  representative branching and merging history.
- Why this grouping: Focus is the smallest surface that can prove the product
  insight before a global Atlas multiplies density.
- Guardrails: deterministic synthetic projection; fixed node positions; bounded
  neighborhood; no topic terrain or correction persistence required.
- Targets: selected Episode, lineage, collapsed branch counts, evidence
  constellation, relation inspector, pan/zoom/fit/reset, direct entry, return,
  and textual fallback.
- Validation: wide/narrow rendered comparison, keyboard traversal, reduced
  motion, pointer-anchor preservation, branch expansion stability, and source
  explanation review.
- Exit gate: the user can answer what led here, what diverged, what remains
  open, and why each visible relation exists without reading full Sessions.
- Proposed Feature owner:
  [FEAT-0087](../feature/feat-0087-session-workflow-focus-map.md).

### Batch 3A: Workflow Boundary Correction

- Implementation state: `passed`. RUN-20260914-98 delivered the
  append-only assertion foundation and RUN-20260914-99 delivered contextual
  preview, correction, undo/reopen, stable orientation restoration, inline
  recovery, no-script forms, and four-width containment. Contract, Design,
  Functional, and UX Heuristic evaluations passed.

- Goal: place bounded same/split/merge/close/reopen correction into the Focus
  experience without returning to an editor-first form wall.
- Why this grouping: product controls must consume an approved user-assertion
  contract and should not be simulated as visual behavior before their
  consequences are known.
- Guardrails: corrections never rewrite source evidence; one primary action per
  action group; failure preserves prior map state; existing organization stays
  visible during any migration period.
- Targets: inspector actions, consequence preview, confirmation/provenance cue,
  undo/reopen, focus/scroll preservation, and current Workstream regression
  safety.
- Validation: normal/failure/no-script paths, direct source return, repeated
  corrections, stale projection handling, and existing Workstream regressions.
- Exit gate: consequential boundaries can be corrected in a few contextual
  actions without manually recreating the graph.
- Proposed correction owners:
  [FEAT-0088](../feature/feat-0088-workflow-assertion-and-correction-contract.md)
  and
  [FEAT-0089](../feature/feat-0089-workflow-boundary-corrections.md).

### Batch 3B: Workstream Candidate And Lens Composition

- Planning state: `product-review return`. The delivered Session Lineage/Focus
  remains useful, but it is not the intended cross-Session Workstream
  discovery experience and does not complete this batch.
- Goal: present provisional many-to-many Workstream candidates across admitted
  source evidence, then let the user rename, merge, split, ignore, or promote a
  candidate before opening it as a durable lens.
- Why this grouping: candidate discovery must remain visibly inferred and
  rebuildable, while promotion and the resulting Workstream remain explicit
  user authority.
- Guardrails: a Session is evidence rather than Workstream identity; no silent
  Workstream creation or migration; current Workstreams and Threads coexist;
  no Qwen or other model dependency in the first baseline.
- Targets: candidate identity and evidence, many-to-many Session/source
  membership, review and promotion, current Workstream coexistence, and Focus
  handoff after promotion.
- Validation: representative cross-Session/source histories, false grouping and
  missed grouping review, rename/merge/split/ignore/promotion consequences, and
  existing Workstream regressions.
- Exit gate: the user can recognize and promote a larger effort without first
  organizing every Session and artifact manually.
- Feature owner: not yet proposed; requires a returned PRD-0017 planning
  boundary and human approval.

### Batch 4: Atlas And Trace Reconciliation

- Goal: extend the validated Focus grammar into an overview and detailed source
  explanation without creating three unrelated screen families.
- Why this grouping: global density and detailed evidence have opposite
  information pressures and should consume a proven middle scale.
- Guardrails: Atlas is bounded to meaningful named/active/recent context; Trace
  keeps source authorities separate; persistent shell remains unchanged.
- Targets: Atlas tips and lenses, Focus handoff, Trace inspector/full detail,
  filters, browser history, empty state, and unavailable source combinations.
- Validation: multi-scale navigation continuity, direct entry, back/forward,
  long histories, long labels, and source-family combinations.
- Exit gate: Atlas → Focus → Trace and the return path feel like one continuous
  product rather than dashboard, graph, and detail fragments.

### Batch 5: Optional Terrain Evaluation

- Goal: determine whether a topic background improves orientation after the
  deterministic map is already useful.
- Why this grouping: semantic terrain should solve an observed navigation gap,
  not justify a model dependency or add visual novelty.
- Guardrails: no model admission inside this design batch; explicit deterministic
  areas first; terrain never changes flow relations or user assertions.
- Targets: no-terrain baseline, explicit-area terrain, ambiguous overlap,
  unavailable semantic capability, and candidate provenance.
- Validation: compare orientation, false grouping, label burden, visual noise,
  runtime cost, and correction burden against the same frozen histories.
- Exit gate: either terrain earns a later bounded model evaluation or the
  product records that Flow Spine and evidence are sufficient.

## Validation Gates

- PRD-0017 approval and the FEAT-0085 through FEAT-0089 first chain are
  satisfied. Any later Workstream candidate, Lens, Atlas, terrain, or model
  Feature still requires its own human boundary approval before a design batch
  becomes implementation input.
- Required foundation Features pass before product prototypes expose data or
  correction behavior that depends on them.
- Visual review compares Quartz/Obsidian reference contributions without
  importing their graph semantics or appearance as product law.
- Wide and responsive evidence covers `1440`, `920`, `700`, and `320`, plus
  long Korean/English/mixed labels and representative large bounded histories.
- Selection, focus, browser history, canvas scroll, expansion, and return state
  remain stable across click, keyboard, direct entry, back/forward, and
  breakpoint changes.
- Visible zoom/reset/fit and keyboard access pass; modifier/pinch zoom does not
  steal ordinary page scroll.
- Reduced motion retains all relation, selection, lifecycle, and expansion
  meaning.
- Direct, inferred, explicit-organization, and user-confirmed relations remain
  distinguishable without color alone and include an inspectable reason.
- Stale, unavailable, abstained, empty, error, render-failure, and no-script
  states preserve a usable source-backed path.
- No tracked artifact contains private runtime titles, paths, ticket keys,
  excerpts, source inventories, or screenshots.

## Risks / Open Questions

- A time-directed layout may still become too wide for long Workstreams; the
  compression and branch-budget rules remain open.
- The passed Focus uses a fixed route-scoped DOM/SVG renderer. Whether a later
  Workstream Lens or Atlas can extend it while preserving stable incremental
  layout remains open and belongs to that future interaction contract.
- Atlas can become an activity dashboard or importance ranking if its admission
  rule is not bounded to user-owned lenses and honest recency/lifecycle state.
- Evidence constellations can reproduce the hairball if source grouping,
  disclosure, and retained-total budgets are not explicit.
- A visual `main` line may appear globally authoritative unless the selected
  Workstream lens and outcome remain continuously visible.
- Existing Workstream forms and the new map may duplicate authority during a
  migration period; coexistence and eventual Thread treatment require human
  product review.
- Topic terrain may be unnecessary, visually noisy, or mistaken for confirmed
  organization. It remains optional and follows Focus validation.
- Workstream lens coexistence and eventual Thread treatment still require
  repeated real-use evidence; the correction controls and their assertion
  lifecycle, rebuild, conflict, undo, and deletion contracts are now passed.

## Exit Goal

- One approved, evidence-backed visual and interaction grammar allows a user to
  enter from a Session or Workstream, see a stable directional story, illuminate
  its local lineage, inspect cross-source evidence, and understand open, quiet,
  merged, or closed outcomes without a model or a manually maintained graph.

## Handoff To Next Track

- FEAT-0085 through FEAT-0089 and their dependency-ordered Runs are complete.
  Product review retains their deterministic Focus and correction path as a
  subordinate Session Lineage/Trace layer. The next planning step is
  Workstream candidate discovery and review before a Lens or Atlas Feature.
- Keep Atlas, topic terrain, and optional semantic-model admission outside
  implementation until that evidence identifies a concrete navigation gap.
- Reusable user-confirmed structure and contextual-correction law is promoted
  to the Design Constitution; unresolved multi-scale choices remain in this
  plan.

## Continuity Notes

- `2026-09-14`: activated after PRD-0017 approval. Linked the dependency-ordered
  FEAT-0085 through FEAT-0089 proposals and retained renderer, Atlas, lens, and
  optional-terrain decisions outside the first Feature review.
- `2026-09-14`: Batch 2 Focus and the correction portion of Batch 3 passed
  FEAT-0085 through FEAT-0089. Workstream Lens, Atlas, and optional terrain stay
  active planning questions rather than implied implementation work.
- `2026-09-15`: owner review classified the delivered Session graph as useful
  but insufficient for the intended Workstream replacement. Batch 3 was split
  so completed correction no longer shares status with the returned Workstream
  candidate and Lens planning boundary.
