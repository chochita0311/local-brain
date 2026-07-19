# PRD-0001: LocalBrain UI Design-System Realignment

## Metadata

- ID: `prd-0001`
- Status: `passed`
- Owner role: `human`
- Created: `2026-07-16`
- Updated: `2026-07-17`

## Request Summary

- Realign the current LocalBrain web UI with the repository's design system across all existing screen families.
- Preserve existing product behavior while verifying the renewed UI against the durable design, interaction, functional, accessibility, responsive, and privacy contracts.

## Source Set

### Human Request

- Renew the current LocalBrain UI according to the current design system.
- Confirm that the result follows the repository's general Design Evaluation and Interaction Evaluation guidance.
- Begin with a bounded PRD before Feature, Spec, or implementation work.

### Golden Sources

- [Creative Design Brief](../../../DESIGN.md): visual north star, source interpretation, and creative rationale
- [Design Constitution](../../policies/design/design-constitution.md): durable implementation and evaluation contract
- [Design Evaluation](../../policies/design/design-evaluation.md): reusable visual and screen-surface checks
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md): reusable interaction continuity and state-transition checks

### Supporting Documents

- [Design Document Governance](../../policies/design/design-document-governance.md): design-document hierarchy and conflict resolution
- [Product Model](../../policies/project/product.md): product entities, organization, and user-facing behavior
- [Project Architecture](../../policies/project/architecture.md): current runtime and frontend boundary
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md): local-data and tracked-evidence constraints
- [Agent Workflow](../../agents/flows/workflow.md): PRD approval and downstream execution gates
- [PRD And Feature Management](../../policies/harness/prd-feature-management.md): artifact ownership, status, and change control

### Current Implementation References

- [Application routes](../../../src/localbrain/main.py): current route and behavior inventory
- [Shared shell](../../../src/localbrain/templates/base.html): persistent navigation, header, global search, and content boundary
- [Screen templates](../../../src/localbrain/templates/): current screen structure and user-visible states
- [Styles](../../../src/localbrain/static/styles.css): current palette, geometry, layout, component, and responsive implementation
- [Browser interactions](../../../src/localbrain/static/app.js): current forms, destructive actions, Suggestions, scans, and Run controls

The implementation audit covers the current route, template, CSS, and browser-interaction source. The completed run set also includes isolated local-server rendering evidence for the primary HTML routes, automated UI contract checks, and functional regression tests. The required browser controller was unavailable during the earlier runs, so their uncollected graphical evidence remained explicit. Live Chrome evidence was later collected for the Local Context explorer, invalidated its initial pass, and drove the completed Fix loop; broader screen-family captures remain a transparent nonblocking follow-up rather than claimed evidence.

## Product Intent

- Make LocalBrain feel like one calm, precise, evidence-rich professional workspace rather than a collection of individually styled screens.
- Let the user move between overview, browse, detail, Workstream, explorer, and Run surfaces without losing shell orientation, state meaning, provenance, or action confidence.
- Apply the current design system without changing LocalBrain's product model, inventing unavailable behavior, or hiding technical and provenance information that users need to trust the workspace.

## Confirmed Scope

### Shared System Alignment

- Align the persistent shell, navigation, workspace header, global search, page rhythm, typography, surfaces, actions, forms, badges, lists, cards, panels, tables, technical content, and feedback states with the Design Constitution.
- Replace page-local or legacy visual values with the constitution's primitive-to-semantic token model and reusable component roles.
- Preserve the eight stable navigation destinations and current route ownership.
- Preserve the desktop-first shell geometry and the constitution's `920px`, `700px`, and `320px` responsive boundaries.
- Keep the existing FastAPI, Jinja2, CSS, and small JavaScript interaction architecture.

### Screen Families

- Renew every current route within its existing durable screen family:
  - overview and dashboard: Dashboard and Sessions Dashboard
  - browse and inventory: Workstreams, Sessions, Projects, Sources, Atlassian, and Search
  - detail and read: Session, subagent, Document, and local Resource
  - Workstream workspace: Workstream detail and its Thread, checkpoint, Resource, Suggestion, and maintenance controls
  - explorer: Local Contexts source rail, tree, preview, and source-management states
  - Run and console: maintenance Run status, output, cancellation, errors, and artifacts
- Treat the Atlassian route as an intentional unavailable or planned-state surface; visual renewal must not imply implemented connector behavior.

### State And Trust Alignment

- Render all current Workstream, Thread, Suggestion, Run, Local Context, source-health, and local-resource states through the constitution's semantic families and explicit text labels.
- Keep imported, inferred, user-confirmed, rejected, unavailable, missing, unreadable, stale, and error information distinguishable without relying on color alone.
- Preserve source identity, timestamps, evidence, local paths, validation results, and action consequences wherever they affect trust or recovery.
- Cover realistic long titles, paths, URLs, excerpts, generated summaries, mixed Korean and English, empty collections, validation failures, loading, working, cancellation, and terminal states.

### Interaction And Accessibility Alignment

- Preserve shell and navigation continuity during route and local-state changes.
- Keep active controls bound and usable after rerenders, reload-triggering actions, filtering, Suggestion review, Run polling, and responsive transformations.
- Provide intentional, bounded feedback for pending, success, error, destructive, unavailable, and recovery states.
- Preserve query, filter, selection, and navigation context where the current route contract supports it; reset state explicitly when scope changes make preservation misleading.
- Make essential actions keyboard reachable, expose visible focus, maintain logical focus order, and prevent hover-only access to required behavior.
- Meet WCAG AA contrast, reduced-motion, semantic labeling, content containment, and narrow-control-size requirements from the Design Constitution.

### Evaluation Coverage

- Apply Design Evaluation, Functional Evaluation, and UX Heuristic Evaluation to every user-visible child Feature.
- Apply Interaction Evaluation to route continuity, view changes, forms, disclosure, filtering, selection, destructive actions, Run transitions, and responsive state ownership.
- Evaluate each affected surface at representative desktop, compact, narrow, long-content, empty, failure, and active-interaction states.
- Classify failures as implementation bug, spec gap, or planning gap and return them to the owning layer instead of expanding scope during fixes.

## Excluded Scope

- New product capabilities, entities, routes, connector behavior, write integrations, or autonomous AI actions.
- Backend, database, retrieval, ingestion, Task Runner, or API behavior changes unless a later approved child Feature proves that a narrowly scoped contract correction is required.
- Changes to the Workstream, Thread, checkpoint, Resource, Suggestion, Session, Local Context, or Run information models.
- Replacing the existing navigation destinations or Workstream-first hierarchy with a different information architecture.
- Treating the upstream Figma source as a direct screen specification or importing commerce, loyalty, marketing, or unsupported Qoo10 patterns.
- Creating or modifying Figma files, production deployment, native macOS packaging, external asset delivery, or a separate design workflow.
- Broad copywriting, localization, or content-strategy revision beyond labels and feedback needed to make current behavior clear and accessible.
- Redesigning the Design Constitution by implication. Durable design-law changes require an explicit constitution update and governance version entry.
- Creating Feature, Spec, Run, evaluation, or implementation artifacts before this PRD boundary is approved.

## Uncertainty And Resolution

- Resolved by `feat-0001`: Claude and Codex use dedicated accessible provenance roles, while unknown sources use a labeled neutral fallback. Provenance never carries status meaning.
- Deferred, nonblocking follow-up: graphical browser captures were not available for every screen family in this run set. The active [Project Backlog](../project/backlog.md) records a future synthetic evidence matrix covering desktop, compact, narrow, long-content, empty, error, and active interaction states without storing private runtime content in Git.
- Resolved by the child Specs: current full-page reload behavior remains part of the observable contract and was preserved.
- Resolved by screen-family evaluation: differences required by product responsibility were retained; raw color and state drift were migrated to the Constitution's semantic system.

The remaining graphical review item stays explicit as future regression work and is not treated as evidence already collected or as a blocker for this accepted increment.

## User-Visible Flows And Interaction Expectations

### Shared Navigation And Search

- The user can identify the current destination, move among all eight navigation destinations, and use global search without losing shell orientation.
- Compact and narrow transformations keep every destination and essential action reachable.
- Direct route entry and list-to-detail entry provide compatible active navigation and parent context.

### Browse, Filter, And Read

- Lists and inventories remain scannable with realistic content length, preserve meaningful filters, and distinguish no-data from no-match states.
- Detail and reading surfaces keep source metadata, provenance, return paths, and readable line length while containing long technical content.
- Returning from detail or changing browse scope behaves intentionally rather than appearing to reset because of visual flicker or leaked intermediate state.

### Workstream Organization

- Workstream identity and status lead the page; Threads, checkpoint state, linked Resources, Suggestions, and Runs follow in that responsibility order.
- User-confirmed organization remains visually distinct from inferred Suggestions.
- Create, edit, link, unlink, accept, reject, restore, and maintenance actions retain their current consequences and provide visible bounded feedback.

### Local Context Exploration

- Source selection, tree location, document selection, preview, full-document access, and source health remain understandable as the explorer collapses across breakpoints.
- Pending, ready, unreadable, error, and missing states keep their reason and recovery context visible.
- Removing an indexed source continues to state that the original file or Apple Note is not deleted.

### Maintenance Runs

- Prepared, queued, running, cancelling, cancelled, completed, failed, and interrupted states remain distinguishable throughout the Run lifecycle.
- Status and cancellation remain available outside long output, while output keeps an independently scrollable technical reading region.
- Polling, cancellation, terminal results, errors, and artifacts update without losing the meaning or interaction ownership of the active controls.

## Constraints

- Explicit human direction and the approved PRD boundary govern scope.
- Product policy and current code own behavior; the Design Constitution owns presentation of approved behavior.
- Design Evaluation and Interaction Evaluation provide reusable checks but do not invent scope or override the constitution.
- Components consume semantic tokens only. Missing reusable roles must be resolved at the design-contract layer before component-local values are introduced.
- Current domain states must not be renamed, merged, or invented for visual convenience.
- No screen may hide provenance, errors, unavailable evidence, or destructive consequences to appear simpler.
- No external CDN, font service, telemetry service, or unapproved external AI service may be introduced.
- Tracked examples, screenshots, fixtures, and evaluation artifacts must use synthetic data and pass repository privacy checks.
- Existing routes, forms, API calls, keyboard behavior, and user-visible workflows are regression surfaces.
- The PRD remained `draft` until the human owner accepted its boundary, remained `approved` during execution, and moved to `passed` after post-run human review accepted the completed run set.

## Acceptance Envelope

This PRD is satisfied only through approved child Features that collectively meet all of the following conditions:

### System And Visual Coherence

- Every current user-visible route is assigned to and renewed within one of the six durable screen families.
- Shared shell, typography, spacing, shape, elevation, action hierarchy, component states, and responsive behavior are recognizably one system.
- Component selectors consume semantic roles rather than raw colors, spacing, radii, shadows, motion, or private breakpoints.
- Any necessary durable design-system addition is approved through Design Document Governance before dependent UI work passes.

### State, Content, And Responsive Integrity

- All current persisted and derived visible states use the constitution's semantic mapping and readable labels.
- Long content, mixed scripts, empty states, loading or working states, validation failures, missing or unreadable sources, and terminal Run states remain contained and actionable where recovery exists.
- At widths above `920px`, from `701px` through `920px`, at `700px` and below, and down to `320px`, navigation, primary actions, state meaning, and readable content remain available.
- Narrow layouts simplify structure before reducing type, and essential controls meet the narrow minimum interaction size.

### Interaction And Accessibility Integrity

- Shared shell and navigation remain stable through route changes; normal flows do not expose blank, debug, placeholder-only, or raw intermediate states.
- Search, filters, detail entry and return, source selection, form submission, destructive confirmation, Suggestion review, and Run controls preserve intentional state ownership and active bindings.
- Keyboard order, visible focus, accessible names, status semantics, reduced motion, and contrast satisfy the durable accessibility contract.
- No essential behavior depends only on hover, color, animation, or an unavailable wide-screen control.

### Regression And Evidence

- Existing route contracts, product behavior, and API consequences continue to pass functional evaluation and automated tests.
- Each child Feature records available rendered-route, DOM, CSS, interaction-contract, and test evidence; graphical browser evidence is required when the configured controller is available and otherwise remains an explicit post-run review item.
- Design Evaluation has no unresolved blocking mismatch within the approved Feature boundary.
- Interaction and functional evaluation have no unresolved blocking continuity, binding, state, workflow, or regression failure.
- UX heuristic findings are either resolved when blocking or recorded as non-blocking suggestions without silently expanding scope.
- Repository privacy checks pass, and no tracked evidence contains private runtime data, local credentials, or unapproved machine-specific context.

## Executed Features

- [FEAT-0001: Source Provenance Design Contract](../feature/feat-0001-source-provenance-design-contract.md) (`foundation`): define source identity as a semantic provenance role that remains separate from status meaning.
- [FEAT-0002: Semantic UI Token Foundation](../feature/feat-0002-semantic-ui-token-foundation.md) (`foundation`): establish the implementation token invariant consumed by all renewed surfaces.
- [FEAT-0003: Shared Shell And Global Navigation](../feature/feat-0003-shared-shell-navigation.md) (`product`): renew the persistent shell, destination navigation, header, and global search.
- [FEAT-0004: Overview Dashboards](../feature/feat-0004-overview-dashboards.md) (`product`): renew Dashboard and Sessions Dashboard as traceable overview surfaces.
- [FEAT-0005: Core Work Inventories](../feature/feat-0005-core-work-inventories.md) (`product`): renew Workstreams and Sessions browse surfaces.
- [FEAT-0006: Source And System Inventories](../feature/feat-0006-source-system-inventories.md) (`product`): renew Projects, Sources, and the unavailable Atlassian surface.
- [FEAT-0007: Search Experience](../feature/feat-0007-search-experience.md) (`product`): renew global and page search entry, results, and no-match behavior.
- [FEAT-0008: Session And Subagent Details](../feature/feat-0008-session-subagent-details.md) (`product`): renew AI-session reading and subagent detail surfaces.
- [FEAT-0009: Document And Resource Details](../feature/feat-0009-document-resource-details.md) (`product`): renew local Document and Resource reading surfaces.
- [FEAT-0010: Workstream Core Workspace](../feature/feat-0010-workstream-core-workspace.md) (`product`): renew Workstream identity, Threads, editing, and checkpoint recovery context.
- [FEAT-0011: Workstream Evidence Review](../feature/feat-0011-workstream-evidence-review.md) (`product`): renew confirmed Resources, linking, and reviewable Suggestions.
- [FEAT-0012: Run Console](../feature/feat-0012-run-console.md) (`product`): renew Run lifecycle, cancellation, output, error, and artifact presentation.
- [FEAT-0013: Workstream Maintenance](../feature/feat-0013-workstream-maintenance.md) (`product`): renewed the Workstream Run launcher and Run history; FEAT-0036 later retired its separate maintenance-marker controls.
- [FEAT-0014: Local Context Explorer](../feature/feat-0014-local-context-explorer.md) (`product`): renew source management, tree navigation, preview, and source-health states.

Recommended dependency order:

1. `feat-0001` closes the remaining provenance-role contract.
2. `feat-0002` establishes the shared implementation token invariant.
3. `feat-0003` establishes the persistent shell and global navigation baseline.
4. `feat-0004` through `feat-0009` renew bounded overview, browse, search, and read surfaces.
5. `feat-0010` and `feat-0011` renew Workstream structure and evidence review as separate outcomes.
6. `feat-0012` establishes reusable Run lifecycle presentation before `feat-0013` renews Workstream maintenance controls.
7. `feat-0014` renews the structurally specialized explorer.

Only one Feature should be approved and placed `in-loop` at a time unless the human owner explicitly authorizes parallel execution.

## Source Map

| Source | Priority | Contribution | Boundary |
|---|---|---|---|
| Human request | primary | overall UI renewal and evaluation intent | does not approve Feature or implementation boundaries automatically |
| Design Constitution | primary | durable visual, responsive, state, component, accessibility, and implementation law | does not define sequencing or new product behavior |
| Current LocalBrain code | primary compatibility evidence | implemented routes, states, controls, and behavior | legacy visual values are not automatically preserved as design law |
| Creative Design Brief | supporting | tone, composition, and source rationale | does not override the constitution |
| Design Evaluation | supporting | reusable visual review risks | does not invent requirements |
| Interaction Evaluation | supporting | reusable continuity and state-transition checks | does not redefine product flow |
| Product, architecture, and privacy policies | supporting | entity, runtime, local-first, and evidence constraints | remain durable owners of their respective contracts |
| Runtime rendering evidence | supporting evidence | isolated local HTTP rendering, DOM contracts, tests, and future graphical captures | must not introduce private tracked content or silently redefine scope |

## Execution Outcome

- All fourteen child Features were executed sequentially in dependency order and are `passed`.
- `feat-0001` established the provenance contract; `feat-0002` implemented the semantic foundation; `feat-0003` through `feat-0014` aligned their current screen families.
- Required Contract, Design, Functional, and UX Heuristic reports were created for each applicable run.
- `feat-0014` completed a targeted Fix Agent loop after live Chrome evidence invalidated its first pass. Attempt 3 now preserves tree disclosure, scroll, focus, history, selected visibility, and accessible current state while replacing only the preview.
- Local Context Chrome evidence covers `1440`, `920`, `700`, and `320`; responsive containment, narrow target geometry, and Lighthouse accessibility `100` passed.
- Post-run human review accepted the complete run set. The PRD and all fourteen child Features are `passed`; broader synthetic graphical regression coverage remains deferred and nonblocking.

## Continuity Notes

- `2026-07-16`: created the initial draft from the human request, the reconciled design system, evaluation policies, and the current route, template, CSS, and browser-interaction implementation.
- `2026-07-16`: stopped at the PRD review gate; no Feature, Spec, evaluation report, or implementation work was created.
- `2026-07-16`: human direction to begin Feature decomposition accepted the PRD boundary; status changed to `approved` and fourteen draft Feature proposals were linked for Feature review.
- `2026-07-16`: human direction authorized sequential execution of all child Features; Specs, Runs, implementation, and required evaluator reports were completed through `run-20260716-14`.
- `2026-07-16`: user-requested Chrome re-evaluation invalidated the initial Local Context explorer pass and reopened only `feat-0014` and `run-20260716-14`; the PRD boundary and active Spec remain valid.
- `2026-07-16`: Local Context Fix Agent work and Attempt 3 live evaluations passed; all fourteen Features returned to automated `passed` status.
- `2026-07-17`: human review accepted the complete run set and closed this PRD as `passed`; remaining synthetic graphical regression suggestions were deferred as nonblocking follow-up work.
