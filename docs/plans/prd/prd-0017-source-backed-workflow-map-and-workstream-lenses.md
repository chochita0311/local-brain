# PRD-0017: Source-Backed Workflow Map And Workstream Lenses

## Metadata

- ID: `prd-0017`
- Status: `approved`
- Boundary State: approved upper boundary; the first dependency-ordered
  delivery chain, FEAT-0085 through FEAT-0089, passed; Workstream candidate
  discovery returned to planning, while Lens, Atlas, topic terrain, and
  optional semantic-model admission remain later review boundaries
- Owner role: `human`
- Created: `2026-09-14`
- Updated: `2026-09-15`
- User review status: the Focus-first chain passed and remains useful as a
  Session Lineage/Focus layer; Workstream candidate discovery returned to
  planning after product review

## Request Summary

- Reconstruct how work moved through time, intent, branches, supporting
  evidence, and outcomes instead of requiring the user to organize every
  source manually inside Workstreams and Threads.
- Make the reconstruction observable and lightly correctable through a stable,
  time-directed workflow map informed by every source LocalBrain can already
  access under its approved local and explicit-remote boundaries.
- Establish a deterministic, model-free baseline before evaluating Qwen or any
  other local semantic model.

## Delivery Boundary And Product Review

### Delivered First Increment

- FEAT-0085 through FEAT-0089 delivered a Session-anchored Episode contract,
  deterministic source-backed Focus projection, stable Focus/Trace map, and
  reversible user boundary corrections.
- This increment is a useful Session Lineage and workflow-evidence layer. It
  remains additive to Sessions and does not replace or migrate existing
  Workstreams, Threads, checkpoints, links, Resources, or Suggestions.

### Product Review Outcome

- The delivered map reconstructs supported relationships between Session
  Episodes, but it does not yet discover the larger Workstream intended by the
  owner, such as one long-running improvement effort spanning many Sessions and
  source families.
- A Session is strong evidence of intent, not the Workstream identity itself.
  One Session may contribute to multiple Workstream candidates, and one
  Workstream candidate may span Sessions, Jira, Wiki, Local Contexts, and later
  approved Slack, Mail, Git, or other source adapters.
- LocalBrain may propose a provisional candidate boundary and label, but only
  explicit user promotion may create or redefine a durable Workstream. The
  user's expected maintenance is review, rename, merge, split, ignore, or
  promotion rather than prerequisite manual organization.

### Awaiting A Later Planning Boundary

- Workstream candidate discovery and review must be planned before a
  Workstream Lens or Atlas product Feature is approved.
- Atlas, topic terrain, non-Session Episode anchors, existing Thread
  coexistence or migration, and optional semantic-model admission remain
  separate later decisions.
- No Feature for those outcomes is approved by this product-review note.

## Source Set

### Human Request

- Work has invisible directional lines similar to Git branches even when it is
  distributed across Sessions, Jira, Wiki, Local Contexts, Git, and later
  Slack, Mail, or other sources.
- Sessions are the strongest initial evidence because they bring user intent,
  investigation, tool use, referenced materials, and decisions together.
- Workstream should become a low-maintenance way to observe and name those
  lines rather than a container whose Threads, checkpoints, and links must all
  be curated manually before it becomes useful.
- The target interaction is a tree-like map: selecting an Episode illuminates
  its lineage and reveals nearby branches and evidence without turning the
  whole corpus into an unstable graph.
- Quartz and Obsidian Graph View are interaction references for local/global
  navigation, focus, pan, and zoom. Their force-directed document-link graph is
  not the target information model.
- The first product boundary must work without Qwen. Optional semantic
  enrichment can be evaluated only after the deterministic baseline is useful
  and measurable.

### Golden Sources

- [Quartz Graph View](https://quartz.jzhao.xyz/features/graph-view): local and
  global graph scope, one-hop neighborhood, hover focus, visited state, drag,
  and zoom reference.
- [Obsidian Graph View](https://obsidian.md/help/plugins/graph): local depth,
  filtering, direction display, force controls, focus, navigation, and
  chronological playback reference.
- The human-defined `flow spine + evidence constellation + topic terrain`
  direction established in the 2026-09-14 planning conversation.

### Supporting Documents

- [Product Model](../../policies/project/product.md): current user-defined
  Workstream/Thread authority, source roles, Session identity, explicit
  organization, and local-first product boundary.
- [Project Architecture](../../policies/project/architecture.md): source
  adapters, normalized evidence, Session reference reconciliation, Local
  Context ingestion, external access, and persistence boundaries.
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md): local
  runtime data, source-specific persistence, explicit external access, and
  private evidence constraints.
- [Design Constitution](../../policies/design/design-constitution.md): current
  Workstream workspace, Explorer, detail/read, technical canvas, provenance,
  responsive, accessibility, and motion law.
- [Design Evaluation](../../policies/design/design-evaluation.md): technical
  canvas controls, relationship explanation, stable selection, containment,
  and rendered-evidence checks.
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md):
  navigation continuity, hierarchical browse-to-preview behavior, contextual
  focus and scroll, input ownership, and stable canvas interaction.
- [Workflow Map Design Plan](../design/workflow-map-design-plan.md): active
  source reconciliation, visual grammar, phased design questions, and
  validation gates for this approved boundary.
- [PRD-0013](prd-0013-session-centric-related-context-evidence.md): passed
  deterministic Session reference evidence and the boundary between direct
  evidence and explicit user organization.
- [PRD-0014](prd-0014-atlassian-explorer-and-unified-retrieval.md) and
  [PRD-0016](prd-0016-atlassian-standard-url-recognition.md): passed local
  Atlassian inventory, evidence Sync, read-only exploration, and structure
  reference behavior.
- [PRD-0005](prd-0005-workflow-and-skill-intelligence.md): sibling draft for
  aggregate workflow patterns and skill intelligence rather than the
  directional personal-work map owned here.

### Current Implementation References

- `src/localbrain/schema.sql`: Sessions, Activity Events, Session reference
  evidence, workspaces, Context Documents, Workstreams, Threads, resources,
  Atlassian Items and structure references, checkpoints, and Runs.
- `src/localbrain/queries.py`: current bounded Session, Project, search,
  reference, and dashboard read models.
- `src/localbrain/workstreams.py`: current deterministic organization
  Suggestions and user-managed Workstream/Thread links.
- `src/localbrain/templates/session.html` and
  `src/localbrain/templates/_session_related_context.html`: Session reading and
  direct-evidence projection.
- `src/localbrain/templates/workstream.html`: current editor-first Workstream,
  Thread, checkpoint, resource, Suggestion, and Run surface.
- `src/localbrain/templates/schema.html` and
  `src/localbrain/static/schema-explorer.js`: current technical-canvas zoom,
  fit, fallback, focus, and route-continuity patterns that may inform but do not
  determine the Workflow Map renderer.

## Product Intent

- Let the user see the story of one effort: where it is first observed, what
  continued, where it branched, which work contributed or merged, what evidence
  accompanied each step, and whether the current tip is open, quiet, or
  explicitly closed.
- Make the projection useful before the user organizes it. Human input should
  correct or promote meaningful boundaries, not unlock the basic map.
- Preserve every source's authority and freshness while presenting one
  coherent directional view across those sources.
- Treat a Workstream as a human-named durable lens over a source-backed
  workflow graph. It remains user-owned and must not be silently created or
  redefined by an inference.
- Treat a generated Workstream candidate as rebuildable inferred state until
  the user explicitly promotes it; candidate discovery may reduce curation but
  never acquires Workstream authority by itself.

## Boundary Decisions For The First Delivery

- The first product entry is an additive action from eligible primary Session
  detail to a separate Focus Map. Existing Session reading and related-material
  behavior remain unchanged.
- Focus is validated before Atlas. The first Feature chain does not add a
  global graph destination or change the Workstream detail hierarchy.
- The deterministic projection is read-only and computed from already
  persisted local evidence. It adds no hidden scan, remote access, Refresh,
  model call, or derived-state persistence.
- FEAT-0085 fixed the first direction vocabulary as `continues`,
  `branches-from`, and `merged-into`; FEAT-0086 abstains when current evidence
  cannot support one of those relations.
- Durable corrections remain a separate assertion layer owned by FEAT-0088
  and exposed by the passed FEAT-0089 product surface. They do not rewrite the
  initial source observations or deterministic candidate reasons.
- Workstream lens promotion, Atlas, topic terrain, non-Session Episode anchors,
  and semantic-model admission remain later planning decisions informed by
  observed Focus use.

## Approved Upper Product Boundary

The following sections preserve the approved long-term product rules. A
subsection labeled `delivered` describes the passed first increment; a
subsection labeled `later boundary` is compatibility law for future planning,
not a claim about current implementation.

### Delivered: Source-Neutral Evidence Admission

- Every source class already available through LocalBrain's approved runtime
  contracts is eligible to contribute evidence when the active projection has
  a bounded, source-specific admission rule.
- The initial eligible evidence families are:
  - meaningful primary work Sessions from every registered Claude, personal
    Codex, and Codex Company Session source;
  - normalized Session time, Project/workspace identity, Session-owned Git
    branch, Activity Event metadata, and direct Session reference evidence;
  - enabled Local Context Documents and their approved source, path, time,
    workspace, and reference identity;
  - persisted local resources, external resources, Workstream/Thread links,
    checkpoints, and other explicit user-owned organization relevant to the
    selected subject;
  - persisted Atlassian Sites, Jira links, Wiki documents, structure
    references, local evidence, approved cached/indexed content state, and
    freshness already present in LocalBrain;
  - current repository, commit, pull-request, conversation, mail, runtime, or
    other source evidence only after its own approved adapter and persistence
    contract exists.
- `Accessible` means eligible persisted local state or the result of an
  already explicit approved operation. Opening, focusing, filtering, or
  expanding the map performs no hidden source scan, model call, capability
  inspection, connected discovery, remote read, or Refresh.
- Existing explicit Session synchronization, Local Context scanning,
  Atlassian local evidence Sync, Connections, discovery, and Refresh retain
  their separate action, authority, progress, and failure contracts.
- A source record is not automatically a workflow node. Source admission and
  Episode admission are separate decisions so documents and links do not turn
  the map into a radial inventory.
- Source identity, source role, evidence kind, freshness, availability, and
  observation time remain inspectable wherever they affect trust.

### Delivered: Initial Episode And Workflow Projection

- One eligible primary work Session is the initial Episode anchor. Direct
  Subsessions remain subordinate evidence of their eligible parent and do not
  become top-level workflow lines. Maintenance and provider-internal Sessions
  remain outside ordinary workflow projection.
- An Episode is a source-backed observation of intent, subject, action,
  evidence, outcome, and next-action signals. The initial contract may leave
  unsupported fields unknown rather than generating them.
- Direction is time-ordered. A candidate relation must carry one or more
  inspectable reasons such as an explicit reference, Session parentage,
  user-confirmed organization, shared stable external identity, source-observed
  Git identity, or a bounded transition signal.
- Same workspace, directory, repository, lexical wording, or recency may
  support a candidate but never establishes a directional relation by itself.
- The directional vocabulary may include `continues`, `branches-from`,
  `contributes-to`, `merged-into`, `blocks`, `supersedes`, and `parallel-to`.
  The first approved foundation Feature must choose the minimal executable
  subset before a product Feature consumes it.
- Workflow origin distinguishes `earliest observed` from a user-confirmed
  start. New evidence may extend the observed origin backward without rewriting
  a user-confirmed boundary silently.
- Lack of recent activity means `quiet` or `last observed`, never `done`.
  Closure requires explicit completion, merge, abandonment, supersession, or a
  user confirmation and retains the closing reason and evidence.
- Lifecycle, recent activity, and epistemic authority remain separate axes.
  Inferred, directly observed, and user-confirmed state must not collapse into
  one badge or color.

### Later Boundary: Workstream Candidate, Lens, And Branch Semantics

- A Workstream is a user-created or user-promoted named lens over one connected
  part of the workflow graph. The durable user-owned minimum is its name and
  intended outcome; derived activity, tips, branches, and evidence must not
  require repeated form maintenance.
- Before promotion, a candidate may group evidence many-to-many: one Session
  may support more than one candidate and one candidate may span multiple
  Sessions and source families. Candidate membership and labels remain
  inferred, reviewable, and rebuildable.
- `Main` is relative to the selected Workstream outcome: it is the path that
  most directly advances that outcome. A supporting branch contributes an
  independently useful result to that path. A semantically similar but
  causally independent effort remains parallel or outside the lens.
- Main/sub presentation is derived from directional relations and the selected
  lens. It is not a universal property stored on every Episode.
- A brief detour does not automatically become a durable branch. A separately
  resumable direction with an independent next action or completion condition
  may become a branch candidate, and a user may promote it to another
  Workstream.
- Existing Workstreams, Threads, links, checkpoints, and Suggestions remain
  intact throughout the initial read-only projection stage. No migration,
  deletion, automatic reassignment, or Thread semantic change occurs without a
  separately approved boundary.

### Shared Workflow Map Interaction

Focus and Trace are delivered. Atlas and topic terrain clauses preserve the
visual and interaction compatibility required of a later approved Feature.

- The target information model is a directed acyclic graph that may branch and
  merge. The presentation should feel tree-like during local expansion while
  preserving merges that a strict tree cannot represent.
- Time provides a stable primary direction. Layout must not rely on continuous
  force simulation or allow ordinary focus changes to randomize the user's
  spatial memory.
- The target visual grammar has three distinguishable layers:
  - `flow spine`: time-directed Episode lineage, branch, merge, and terminal
    structure;
  - `evidence constellation`: source artifacts revealed around the selected
    Episode without competing with the lineage by default;
  - `topic terrain`: optional, non-authoritative background grouping that never
    defines a branch or Workstream.
- The target navigation model has three semantic scales that may be delivered
  in separate child Features:
  - `Atlas`: active or recently relevant Workstream lenses and tips;
  - `Focus`: one selected Episode or Workstream lineage plus bounded branches;
  - `Trace`: evidence, relation reasons, source state, and destination links for
    one Episode or edge.
- Selecting an Episode keeps its position stable, illuminates its relevant
  lineage, reveals a bounded neighborhood and evidence constellation, dims
  unrelated context without removing orientation, and exposes an adjacent
  explanation of why each visible relation exists.
- Candidate and confirmed relations remain distinguishable without relying on
  color alone. Selection glow or motion may reinforce state but cannot be the
  only carrier of meaning.
- Map controls include visible zoom, fit, and reset behavior plus keyboard and
  non-pointer access. Ordinary page scrolling must not be captured as canvas
  zoom without the approved modifier or pinch interaction.
- A readable list or trace fallback preserves navigation and evidence when the
  diagram is unavailable, reduced, or unsuitable at a narrow viewport.

### Delivered: Bounded User Correction

- The map may offer reviewable corrections such as `same flow`, `split here`,
  `merge into`, `close`, and `reopen` after their ownership and persistence
  contract is approved.
- A correction changes only the user-owned assertion layer. It never rewrites
  source Sessions, documents, external systems, or direct observation evidence.
- User assertions survive rebuilds and model changes, are reversible, retain
  provenance, and do not treat silence, snooze, dismissal, or an unopened
  candidate as a correctness label.
- The initial read-only Focus projection may precede correction persistence if
  the foundation boundary is split, but the PRD is not satisfied until the user
  can inspect and correct consequential branch boundaries without manually
  rebuilding the map.

### Delivered Baseline And Later Optional AI

- The initial workflow projection, Focus map, source explanations, and user
  correction path require no Qwen model, embedding runtime, external model, or
  network enrichment.
- No model is downloaded, installed, started, or invoked as a side effect of
  source ingestion, application startup, map entry, focus, search, or ordinary
  navigation.
- Qwen or another local embedding, reranking, or generative model may later be
  evaluated as a replaceable enhancement for missing semantic-neighbor
  candidates, topic terrain, concise Episode fields, or human-readable labels.
- Optional model output remains inferred, derived, versioned, rebuildable, and
  unable to create Workstreams, confirm relations, close workflows, or alter
  source authority silently.
- Model admission requires a separate approved planning boundary and a matched
  comparison against the deterministic baseline using explicit user feedback,
  resource cost, latency, stability, and correction burden.

## User-Visible Flows And Interaction Expectations

Status labels below distinguish the passed first increment from later product
flows that remain unimplemented.

### Delivered: Open A Workflow From A Session

- The user opens an eligible primary Session and chooses its workflow view.
- LocalBrain focuses the matching Episode, shows the bounded predecessor and
  successor lineage it can support, and abstains visibly when no reliable edge
  is available.
- Selecting an edge or nearby artifact explains the relation and opens the
  existing source detail without losing map orientation.

### Later Boundary: Discover, Promote, And Explore A Workstream Lens

- LocalBrain presents a provisional Workstream candidate with its source-backed
  reason, extent, evidence coverage, and uncertainty before any durable
  Workstream is created or changed.
- The user may rename, merge, split, ignore, or promote the candidate. After
  promotion, the user opens the Workstream and sees its observed origin, main
  path, bounded branches, current tips, quiet segments, terminal events, and
  evidence coverage without completing a checkpoint or manually attaching
  every source.
- Expanding one branch preserves the selected node, scale, surrounding
  orientation, and browser history behavior.

### Delivered: Inspect Evidence Across Sources

- The user selects an Episode or relation and sees source-grouped evidence with
  role, observation time, freshness, availability, and the exact reason it was
  admitted.
- Session, Jira link, Wiki document, Local Context Document, Git identity, and
  future source families keep distinct source cues and destination behavior.
- Unavailable or stale evidence remains visible with its last-known status and
  does not disappear or appear current.

### Delivered: Correct A Consequential Boundary

- The user can confirm continuity, split a line, merge a branch, close a tip,
  or reopen a closed path through one bounded action whose consequence is clear
  before submission.
- The current focus, outer and nested scroll, filters, and meaningful keyboard
  focus remain stable after the correction.
- Failure preserves the prior projection and places recovery feedback beside
  the owning action.

### Delivered: Use The Product Without A Model

- The same map entry, lineage, source evidence, fallback, and correction
  workflow remain available when no local model is installed.
- Optional semantic features, if admitted later, identify their unavailable or
  stale state without making the deterministic map look incomplete or broken.

## Excluded Scope

- Qwen installation, model download, embedding generation, vector storage,
  reranking, generative summarization, fine-tuning, or model-provider UI in the
  initial child Feature chain.
- Automatic semantic linking across the whole corpus before a deterministic
  baseline and explicit evaluation contract pass.
- Implementing Slack, Mail, hosted Git, pull-request, runtime-log, or other new
  source adapters in this PRD. The projection contract remains extensible to
  them after their own approved source boundary exists.
- Background remote reads, automatic capability checks, broad connector
  discovery, or implicit Atlassian Refresh from map loading or interaction.
- External writes, source-file writes, Jira/Wiki mutation, Git mutation, or
  messages sent to Slack, Mail, or another destination.
- Treating every Document, Jira Item, URL, message, commit, or Activity Event as
  a top-level Episode merely because it is available.
- Freeform node positioning, saved personal canvas layout, arbitrary edge
  drawing, decorative physics, or a continuously animated force graph.
- Silent migration, deletion, merge, split, or reassignment of existing
  Workstreams, Threads, checkpoints, links, Resources, or Suggestions.
- Productivity scoring, attention ranking presented as value, employee
  evaluation, or claims that activity volume represents outcome quality.
- Native packaging, cloud synchronization, multi-user collaboration, or mobile
  product expansion.
- Feature, Spec, schema, query, route, template, JavaScript, CSS, or runtime
  implementation before this PRD and each child Feature pass their human
  approval gates.

## Uncertainty

- Validate whether the proposed `continues`, `branches-from`, and
  `merged-into` vocabulary is sufficient after representative Focus histories;
  `contributes-to`, `blocks`, `supersedes`, and `parallel-to` remain deferred.
- Validate whether FEAT-0086's exact-signal combinations produce enough useful
  edges without turning workspace, branch, lexical, or recency similarity into
  false causality.
- Validate whether the bounded deterministic Episode fields are sufficient or
  whether later explicit extraction is worth its privacy and correction cost.
- Reconsider on-demand projection ownership only if measured local reads miss
  the approved interaction budget. Caching or incremental persistence requires
  a returned Feature boundary rather than an implementation shortcut.
- Decide whether non-Session events can become independent Episodes in a later
  phase and what source capability proves an intent-changing event rather than
  ordinary evidence.
- Resolve the long-term role of existing Threads: retain them as explicit
  organization, reinterpret them only through a reviewed migration, or
  eventually supersede their current UI. This is not decided by the initial
  read-only projection.
- Define branch display budgets, collapse rules, temporal compression, label
  density, and direct-entry restoration for large histories.
- Select and benchmark a renderer and layout approach only after the approved
  graph and interaction contracts are fixed. Existing Mermaid/ELK behavior is
  reference evidence, not an automatic implementation choice.
- Decide the minimum explicit user feedback sample and success criteria that
  would justify opening a later semantic-model evaluation.

These bounded items do not change the approved upper boundary. FEAT-0085 and
FEAT-0086 own the first vocabulary and projection decisions; FEAT-0088 owns
correction persistence. A dependent Feature remains unapprovable until its
required foundation boundary passes review and execution gates.

## Constraints

- Explicit human direction and this approved PRD boundary govern scope.
- Existing user-defined Workstream and Thread semantics remain durable product
  law until an approved contract change updates their owner policies.
- Source content, derived evidence, inferred relations, and user assertions
  remain distinct owners with explicit lifecycle and deletion behavior.
- The current Session-related rail remains deterministic direct evidence and
  explicit organization. Workflow candidates must not be inserted into that
  authoritative rail as if they were direct references.
- Local-first privacy and source persistence modes apply independently to each
  admitted evidence family.
- The deterministic core must remain useful when every optional AI capability
  is absent, unavailable, stale, or removed.
- Future foundation work is expected to use `foundation-contract` and product
  work `fullstack-product`. Data/source, projection, and map UI lanes must be
  split when they can pass independently.
- Visible Features require Design, Functional, and UX Heuristic evaluation;
  source, relation, route, and persistence changes also require Contract
  evaluation.
- Rendered validation must cover representative `1440`, `920`, `700`, and
  `320` widths, long mixed-language titles, large bounded neighborhoods,
  empty/abstained state, stale/unavailable evidence, keyboard focus, reduced
  motion, and diagram failure fallback.
- Tracked fixtures, screenshots, plans, and evaluation artifacts use only
  synthetic data.
- Proposed child Features remain planning-only while `draft`. Spec work,
  implementation, and evaluation wait for human approval of the selected
  Feature boundary.

## Acceptance Envelope

### Passed First-Chain Acceptance

- A user can enter a workflow projection from an approved surface and
  understand the selected Episode's observed lineage, current tip or terminal
  status, and evidence without reading every full Session.
- The initial projection works with no installed or running AI model and emits
  no hidden model, network, connector, scan, capability, or Refresh operation.
- Every visible relation states an inspectable reason and distinguishes direct
  observation, deterministic inference, explicit organization, and
  user-confirmed assertion.
- All currently admitted source families can contribute through a bounded
  source-role contract without becoming interchangeable nodes or losing
  freshness and availability.
- Primary Sessions anchor the initial Episode projection; Subsessions and
  maintenance activity retain their existing exclusion and subordinate
  boundaries.
- Observed origin, last observation, activity quietness, and explicit closure
  remain distinct. Inactivity alone never closes a workflow.
- Selecting, expanding, navigating, and returning preserve stable spatial and
  browser orientation. The map does not depend on continuous force motion.
- A user can inspect and reversibly correct consequential flow boundaries
  without modifying source evidence or manually reconstructing all links.
- Diagram failure, narrow layout, reduced motion, keyboard navigation, stale or
  unavailable evidence, and a genuinely unconnected Session retain a usable
  textual path.
- Existing Workstream, Thread, Session, Search, Atlassian, Local Context,
  Schema, Suggestion, and Run behavior remains unchanged until an approved
  child Feature explicitly names its regression boundary.

### Remaining Product Acceptance

- LocalBrain can present reviewable Workstream candidates that span multiple
  Sessions and admitted source families without treating a Session, shared
  workspace, lexical similarity, or recency as sufficient Workstream identity.
- Candidate labels and memberships remain inferred and rebuildable until the
  user explicitly promotes, renames, merges, splits, or ignores them.
- Main and supporting presentation is relative to a selected Workstream lens
  and does not create a universal hierarchy across the whole corpus.
- Atlas, Focus, and Trace use one coherent visual grammar and preserve the
  persistent LocalBrain shell when their separately approved Features are
  delivered.

## Delivered First Chain

- [FEAT-0085: Workflow Episode And Direction Contract](../feature/feat-0085-workflow-episode-and-direction-contract.md)
  (`passed`, foundation): define the Session-anchored Episode identity, minimal
  direction vocabulary, time/lifecycle/activity/authority axes, reason shape,
  abstention, and rebuild semantics.
- [FEAT-0086: Deterministic Cross-Source Workflow Projection](../feature/feat-0086-deterministic-cross-source-workflow-projection.md)
  (`passed`, foundation): produce a bounded, on-demand, read-only projection
  from current persisted Session, Project/Git, Local Context, Resource,
  organization, and Atlassian evidence without hidden source operations.
- [FEAT-0087: Session Workflow Focus Map](../feature/feat-0087-session-workflow-focus-map.md)
  (`passed`, product): add the separate Session-detail Focus entry, stable
  time-directed map, click-to-illuminate behavior, evidence constellation,
  relation explanation, controls, and textual fallback.
- [FEAT-0088: Workflow Assertion And Correction Contract](../feature/feat-0088-workflow-assertion-and-correction-contract.md)
  (`passed`, foundation): define a durable, reversible user assertion layer
  separately from source observations and deterministic candidates.
- [FEAT-0089: Workflow Boundary Corrections](../feature/feat-0089-workflow-boundary-corrections.md)
  (`passed`, product): expose same-flow, split, merge, close, reopen, and undo
  actions without losing focus or source history.

## Future Candidate Increments

- `Workstream Candidate Discovery And Review` (`foundation + product`): define
  provisional many-to-many candidate identity and evidence, produce bounded
  candidates from the currently admitted sources, and let the user rename,
  merge, split, ignore, or promote them. Its exact Feature decomposition and
  acceptance remain pending product planning and human approval.
- `Workstream Lens And Atlas` (`product`, fullstack): open a promoted meaningful
  line as a named Workstream lens and present bounded active/recent tips at the
  Atlas scale after candidate discovery, review, and current Thread coexistence
  are resolved. This remains a PRD candidate rather than an approved Feature.
- `Optional Semantic Enrichment Admission` (`deferred foundation candidate`):
  compare a replaceable local semantic capability with the deterministic
  baseline only after Workstream candidate evaluation produces usable feedback
  about missed or incorrect semantic groupings.

The human owner accepted this PRD boundary and FEAT-0085 through FEAT-0089 for
sequential execution on `2026-09-14`. Foundation contracts must pass before
product Features build against their data, relation, or assertion semantics.

## Source Map

| Source | Priority | Contribution | Boundary |
| --- | --- | --- | --- |
| Human direction | primary | directional work model, Session-first anchor, all-source evidence, low-maintenance Workstream lens, click-to-illuminate map, and model-free first boundary | does not approve a particular schema, renderer, route, migration, or AI runtime |
| Quartz Graph View | golden interaction reference | local/global scope, one-hop focus, visited cue, pan, drag, and zoom | document-link and force-layout semantics do not define workflow direction or LocalBrain product behavior |
| Obsidian Graph View | golden interaction reference | local depth, filters, direction option, force controls, navigation, and chronological playback | vault graph, link count, and force settings do not define Episodes, branches, outcomes, or source authority |
| Product, architecture, privacy, design, and interaction policies | durable contract | user authority, source roles, local-first access, provenance, screen families, state, responsive, accessibility, and interaction boundaries | current Workstream/Thread law changes only after approval and owner-policy updates |
| PRD-0013 and Session reference implementation | passed evidence baseline | source-neutral direct Session references and exact evidence reasons | semantic or workflow proximity must remain separate from the authoritative related-material rail |
| Passed Atlassian planning and implementation | source authority and current behavior | stored Jira/Wiki identity, local evidence, structure references, freshness, explicit Sync/Connections/Refresh separation | map entry performs no remote read or implicit refresh and does not rewrite Atlassian ownership |
| Current Workstream implementation | implementation truth | existing manual Threads, checkpoints, links, Suggestions, and Runs | evidence of current state, not authority to preserve editor-first UX after an approved reframe |
| PRD-0005 | sibling draft | aggregate repeated workflow, topic, error, and skill insight questions | does not own the per-effort directional graph or map interaction defined here |
| Optional future models | deferred supporting source | possible semantic neighbors, terrain, summaries, and labels | no initial dependency, no organization authority, and no admission without separate evaluation and approval |

## Continuity Notes

- `2026-09-14`: created the draft from the owner's Git-branch-like workflow
  model, Session-first evidence insight, all-accessible-source clarification,
  Qwen-free baseline decision, and Quartz/Obsidian interaction references.
- `2026-09-14`: separated source admission from Episode admission so adding
  Jira, Wiki, Local Contexts, Git, Slack, Mail, or another source does not turn
  the workflow map into a flat radial inventory.
- `2026-09-14`: kept existing Workstream/Thread state intact and made their
  long-term migration an explicit human decision rather than an implication of
  the new map.
- `2026-09-14`: stopped at PRD review. No Feature, Spec, schema, route, model,
  or implementation work is authorized by this draft.
- `2026-09-14`: owner continued from the PRD review boundary, approving a
  Session-detail, Focus-first, deterministic and read-only product direction.
  FEAT-0085 through FEAT-0089 were proposed in dependency order; all remain
  `draft`, so no Spec or implementation work is authorized yet.
- `2026-09-14`: owner approved the five proposed Feature boundaries for
  sequential execution. FEAT-0085 entered the loop; later Features remain
  dependency-gated.
- `2026-09-14`: FEAT-0085 passed its pure contract and regression gates;
  FEAT-0086 entered RUN-20260914-96 to build the first exact-signal read model.
- `2026-09-14`: FEAT-0086 passed its read-only signal, bound, evidence, and
  regression gates; the next dependency is the visible FEAT-0087 Focus map.
- `2026-09-14`: FEAT-0087 passed its route, fixed-layout interaction,
  four-width rendering, fallback, accessibility, and regression gates;
  FEAT-0088 is now the next assertion-foundation dependency.
- `2026-09-14`: FEAT-0088 passed its append-only assertion, projection overlay,
  recovery, generated-owner, and regression gates; FEAT-0089 entered the final
  product loop.
- `2026-09-14`: FEAT-0089 passed contextual correction, stable-orientation,
  four-width, no-script, source-safety, and regression gates. The approved
  FEAT-0085 through FEAT-0089 chain is complete without Qwen; this PRD remains
  open at product review for real-use evidence before a Workstream Lens, Atlas,
  topic-terrain, or optional-model Feature is proposed.
- `2026-09-15`: owner product review retained the delivered Session graph as a
  useful Session Lineage/Focus and Trace layer, but rejected treating it as the
  intended Workstream replacement. The next planning question is reviewable
  Workstream candidate discovery across Sessions and admitted source families;
  no later Feature, migration, Atlas, or Qwen boundary was approved by this
  review.
