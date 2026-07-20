# PRD-0002: Session Browsing And Subsession Organization

## Metadata

- ID: `prd-0002`
- Status: `passed`
- Owner role: `human`
- Created: `2026-07-17`
- Updated: `2026-07-19`

## Completion State

- FEAT-0015 through FEAT-0019 are `passed`, and their source contract, navigation, pagination, conversation detail, and Session-only synchronization outcomes remain accepted.
- Human post-run review fixed `Subsession` as the single LocalBrain product term and accepted the completed PRD boundary on `2026-07-19`.
- Contract, functional, local HTTP, compilation, and repository privacy verification passed after the terminology alignment. Browser-only pixel and interaction-state captures that were unavailable in the current control environment remain explicit non-blocking quality backlog rather than unverified pass claims.

## Request Summary

- Consolidate Sessions and Projects under one Sessions navigation destination with a `Sessions | Projects` view switch whose default is Sessions.
- Make the Sessions inventory practical for occasional review through fixed 15-item pagination, concise row metadata, and parent-owned subsession disclosure.
- Present Session and subsession details as conversation reading surfaces by hiding tool-call rows without deleting or reclassifying the stored source events.
- Reconcile the current Claude and Codex subagent exposure difference so source format does not decide whether a child run appears under its parent or as an ordinary top-level Session.
- Exclude subsessions from Workstream Claude maintenance retrieval and organization because these child runs primarily represent cleanup or one-off investigation rather than durable Workstream evidence.
- Store Git branch metadata on the Session that observed it, retain only repository-root identity on the workspace, and remove the obsolete workspace-level branch field and its consumers.

## Source Set

### Human Request

- Keep Sessions as the default view and place Projects in the same menu behind a `Sessions | Projects` segmented switch.
- Use an Atlassian-like two-option control with a visibly sliding selected state.
- Show 15 top-level Sessions per page and add pagination.
- Show a right-edge subsession dropdown only on rows whose Session owns one or more subsessions.
- Remove visible `exec`, `Bash`, `Write`, and other tool-call rows from Session conversation reading surfaces; this is display-only and must not delete the underlying events.
- Keep the `CL` or `CX` provenance mark, remove the redundant visible `Claude` or `Codex` text from Session-row metadata, and show local path, branch when available, question count, and event count.
- Normalize available Claude and Codex branch metadata inside LocalBrain without modifying project files or Git state.
- Explain and correct the current behavior in which Claude subagents are shown under a parent detail while Codex subagents can appear as separate recent Sessions.
- Keep Claude and Codex subsessions out of Workstream Claude Run candidate, evidence, and Suggestion inputs.
- Exclude every Claude and Codex subsession from global Search, Sessions Dashboard, and Session-derived activity statistics while retaining its source-backed data for parent-owned browsing.
- Treat `git_root` as the filesystem root of the Git repository containing a workspace path, store source-observed branches per Session, and remove `workspaces.git_branch` because one workspace path can own Sessions from multiple branches.
- Make the complete LocalBrain ERD and schema easier to inspect, and track wider table cleanup separately from this Session-focused increment.
- Place the `Sessions | Projects` selector directly below the inventory description at the same compact position and geometry as the Atlassian `Jira | Confluence` selector, with a same-row primary `동기화` action that refreshes only Claude and Codex Session sources.

### Golden Sources

- Human direction in this request is the primary source.
- The current Atlassian `Jira | Confluence` segmented control is an interaction reference for the two-view shape only. Its current markup and styling are not acceptance evidence for the requested sliding state.
- [Design Constitution](../../policies/design/design-constitution.md) governs navigation, source provenance, browse density, detail reading, responsive behavior, accessibility, and reduced motion.
- [Design Evaluation](../../policies/design/design-evaluation.md) governs row containment, metadata hierarchy, pagination edges, and rendered viewport evidence.
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md) governs mode changes, pagination continuity, dropdown behavior, focus, and responsive state ownership.

### Supporting Documents

- [Product Model](../../policies/project/product.md): current Session and Project responsibilities and navigation contract.
- [Project Architecture](../../policies/project/architecture.md): Session ingestion, Claude lazy subagent discovery, normalized events, and package ownership.
- [Claude Task Runner](../../policies/operations/claude-task-runner.md): Workstream maintenance Runs remain separate from ordinary Sessions.
- [Core Work Inventories](../feature/feat-0005-core-work-inventories.md): accepted Sessions inventory behavior and regression surface.
- [Session And Subagent Details](../feature/feat-0008-session-subagent-details.md): accepted Session and Claude subagent detail behavior and regression surface.
- [Data Model Visibility And Schema Cleanup](prd-0003-data-model-visibility-and-schema-cleanup.md): draft follow-up for the complete ERD, table catalog, schema ownership, and cleanup decisions outside this Session-specific change.

### Initial Implementation References

- `src/localbrain/main.py`: Sessions, Projects, Session detail, and the original Claude lazy-child route.
- `src/localbrain/queries.py`: current 100-item recent Session query, workspace metadata, Projects aggregation, and unfiltered event timeline query.
- `src/localbrain/ingest/scanner.py`: all-Codex JSONL collection and explicit Claude `subagents/` exclusion.
- `src/localbrain/ingest/claude.py`: Claude Session and tool-call normalization.
- `src/localbrain/ingest/codex.py`: Codex Session and tool-call normalization.
- `src/localbrain/subagents.py`: Claude-only discovery from the source-native `subagents/` directory.
- `src/localbrain/templates/base.html`: separate Sessions and Projects navigation items.
- `src/localbrain/templates/sessions.html`: Session list, source filters, row metadata, and current lack of pagination or subsession disclosure.
- `src/localbrain/templates/session.html` and the former `subagent.html`: initial tool-call rendering and Claude child-detail presentation.
- `src/localbrain/templates/atlassian.html`: current segmented-control reference.

## Initial Implementation Findings

- Claude and Codex currently follow different child-session policies.
  - Claude JSONL under a `subagents/` directory is excluded from primary Session ingestion and is read lazily from the parent Session's source path.
  - Codex scanning imports every JSONL under the Codex session root as a primary Session.
- Representative current Codex metadata exposes parentage through fields such as `source.subagent`, `parent_thread_id`, and `forked_from_id`, but the current Codex parser does not consume those fields or persist a parent relation.
- Representative Codex metadata also carries Git context, but the current Codex parser does not normalize its branch while the Claude parser reads `gitBranch`.
- The `sessions` table currently has no branch field. Session list, detail, retrieval, Project resource, and maintenance context consumers instead receive `workspaces.git_branch`, so multiple Sessions launched from the same path cannot retain their own historical branches.
- `workspaces.git_root` already represents the filesystem root of the Git repository containing the workspace path. It is repository identity and has no relationship to a branch's base, parent, `main`, or `master` lineage.
- A Codex child identified by source-native subagent metadata could therefore be normalized as a regular `work` Session, receive a fallback title, and appear independently in the Sessions inventory after synchronization.
- The Sessions query currently returns at most 100 `work` Sessions and has no page or offset contract.
- Session and child-detail views initially rendered both conversational messages and normalized `tool_call` events.
- Workstream Claude Task Runner executions use no Session persistence and remain durable `maintenance_runs`; this PRD does not change that boundary.
- Workstream retrieval initially consumed indexed ordinary `work` Sessions. Claude source-native child files were absent because they were lazily excluded, while Codex children could enter the same retrieval path because they were misclassified as ordinary Sessions.

## Product Intent

- Make occasional Session review compact and predictable without turning subsessions into top-level noise.
- Let Projects remain available as a Session-derived browsing mode while reducing persistent navigation clutter.
- Give Claude and Codex the same user-facing parent/subsession organization even though their source formats encode parentage differently.
- Make Session detail primarily useful for rereading the conversation while retaining raw tool activity for provenance, metrics, and future analysis.
- Keep historical branch metadata attached to the Session that observed it instead of allowing later scans from the same workspace path to overwrite its meaning.

## Confirmed Scope

### Sessions And Projects Navigation

- Replace the separate persistent Sessions and Projects destinations with one Sessions destination.
- Provide `Sessions | Projects` as mutually exclusive views inside that destination, with Sessions selected on default entry.
- Give the selected segment a visibly moving indicator while preserving explicit selected semantics and a meaningful state when reduced motion is enabled.
- Preserve direct access to existing Session, Project, and workspace-filtered destinations so existing links do not become dead ends.
- Keep Projects as a Session-derived project/workspace inventory; this increment does not redefine Project ownership or create a new Project data source.
- Place the selector and `동기화` action in one toolbar row immediately below the inventory description. Match the selector's compact geometry and position to the Atlassian inventory selector while retaining the Sessions-specific sliding indicator.
- Style `동기화` with the same primary action contract as the Sources scan button. It incrementally scans only configured Claude and Codex Session sources, while the Sources-wide scan continues to include enabled Local Context sources.

### Session Pagination

- Show 15 top-level Sessions per page.
- Provide LIMIT/OFFSET pagination that communicates the current page through compact numbered destinations with ellipses and retains previous/next movement without requiring a page-size selector.
- Preserve the active Claude or Codex source filter and selected Project/workspace scope while paging.
- Reset to a valid page when a view or filter change makes the current page invalid.
- Keep pagination usable on short final pages and supported narrow viewports. Desktop shows at most seven page tokens; the narrow layout shows at most five.

### Cross-Source Parent And Subsession Organization

- Define one source-neutral parent/subsession relationship that can be populated from Claude directory structure and Codex session metadata.
- Sessions with a valid parent relation must not appear as independent top-level rows in the default Sessions inventory.
- A top-level Session row exposes a right-edge dropdown trigger only when one or more subsessions are available.
- The dropdown provides direct access to the available child records while retaining clear parent orientation.
- A parent Session detail retains a Subsessions section as a second access path to available children in addition to the inventory-row dropdown.
- The inventory dropdown and the parent-detail Subsessions section expose only direct children of a top-level Session. Deeper descendants remain source-backed subsessions but are not flattened or exposed on current user-facing Session surfaces.
- Synchronization must reconcile already imported Codex child records into the parent/subsession presentation without deleting the authoritative source JSONL.
- A subsession whose parent cannot be resolved because the parent is missing, unavailable, or not imported is preserved as source evidence but is not exposed on user-facing Session surfaces.
- Claude and Codex retain their provenance even when both use the same parent/subsession interaction pattern.

### Session Row Information

- Retain the compact visible `CL` or `CX` source mark.
- Remove the redundant visible source-name text from the Session row metadata.
- Preserve an accessible full source name so source identity is not conveyed only by abbreviation or color.
- Show the local working path, branch when available, question count, event count, and last-activity time in a stable row hierarchy.
- Read the row branch only from the Session-level branch contract defined below.
- Keep missing-path state explicit rather than replacing the historical path with an empty value.

### Session Branch Ownership And Workspace Cleanup

- Keep `workspaces.canonical_path` as the normalized working-directory identity and `workspaces.git_root` as the filesystem root of the containing Git repository.
- Add nullable `sessions.git_branch` as the only persisted branch value used to describe an individual Session.
- Claude produces the last non-empty top-level `gitBranch` observed in that Session file. Codex produces `payload.git.branch` from the primary first `session_meta` identity record and does not adopt branch data from later embedded historical metadata.
- Normalize both source values as trimmed strings, convert an empty value to `NULL`, and do not infer a missing historical branch from the repository's current checkout, workspace state, `main`, or `master`.
- Remove `workspaces.git_branch` from the canonical and migrated runtime schema. Remove it from Project, retrieval, Task Runner, manifest, and resource payload consumers rather than keeping a deprecated compatibility field.
- Existing Session rows acquire branch data only by reprocessing their authoritative Claude or Codex JSONL. A missing or unavailable source leaves the Session branch `NULL`; the previous workspace value must not be copied into Sessions because it cannot identify which Session observed that branch.
- The migration must preserve workspace IDs, `git_root`, Session-to-workspace mappings, user-curated links, and other workspace consumers while removing the obsolete column.
- Projects may continue to identify Git-backed workspaces through `git_root`, but they do not present a workspace branch as though it were current or historically representative.
- This is a LocalBrain-only schema and read-model change. It must not run branch-changing Git commands or modify `.git`, project files, Claude state, or Codex state.

### Conversation-Focused Detail

- Primary Session and subsession detail timelines show human or parent-agent messages and assistant or child-agent messages in source order.
- Normalized tool-call rows, including Codex execution tools and Claude tools such as `Bash` and `Write`, are not rendered in the conversation timeline.
- Tool-call events remain stored and available to non-presentation consumers; their ingestion, source identity, and raw provenance are not deleted by this display change.
- Question and event counts continue to describe the normalized Session record rather than only the currently visible message rows.
- Parent, back, Workstream membership, direct-detail, and source-provenance context remain available.

### Workstream Maintenance Isolation

- Claude and Codex subsessions are excluded from Workstream Claude Run candidate retrieval, candidate counts, evidence materialization, context manifests, and generated Resource Suggestions.
- A parent Session remains eligible under the existing Workstream retrieval rules, but its child subsession content is not merged into or attributed to that parent for maintenance analysis.
- Parentless subsessions are subject to the same exclusion even though they are already hidden from user-facing Session surfaces.
- This exclusion changes only LocalBrain classification and downstream consumption; it does not delete source JSONL or modify external Claude, Codex, project, or Git state.

### Global Search And Statistics Isolation

- Claude and Codex subsessions do not produce global Search results.
- Sessions Dashboard totals, recent activity, daily activity, source activity, tool counts, workspace and Project activity aggregates, context-switch counts, and other Session-derived statistics count only primary Sessions.
- Subsession events and metadata remain stored and readable through the approved parent-owned direct-child surfaces; exclusion from Search and statistics is not source deletion.
- Existing user-confirmed links to a Session identity remain intact even if a rescan reclassifies that Session as a subsession.

## Excluded Scope

- Including Workstream maintenance Runs in the ordinary Sessions inventory.
- Using subsession content as Workstream Claude maintenance evidence, candidates, or Suggestion input.
- Deleting tool-call events, tool names, source JSONL, Run artifacts, or indexed provenance.
- Modifying a source repository, working tree, branch, Git configuration, or external Claude or Codex state while reading branch metadata.
- Hiding user or assistant message content merely because it discusses or reports tool use.
- Adding infinite scroll, configurable page size, bulk Session actions, new Session sorting, or Session editing.
- Redefining Projects as user-managed Workstreams or introducing a new Project persistence model.
- Inferring or periodically refreshing a workspace's current branch after `workspaces.git_branch` is removed.
- The repository-wide ERD, table catalog, or schema cleanup beyond the Session/workspace branch ownership change; that boundary is tracked in [PRD-0003](prd-0003-data-model-visibility-and-schema-cleanup.md).
- New external connectors, external writes, semantic ranking, Session summarization, or AI-generated Session classification.
- Scanning Local Context folders, files, or Apple Notes from the Sessions inventory action.
- Flattened or recursive exposure of subsessions deeper than one direct-child level.
- User-facing inventory, dropdown, or detail access for a subsession whose parent cannot be resolved.
- Spec, implementation, feature execution, or evaluation before this PRD boundary is approved.

## Resolved Product Terminology

- `Subsession` is the single source-neutral LocalBrain product term for a child Session in schema values, domain contracts, UI labels, routes, and product-facing implementation names.
- Source-native `subagent` identifiers remain only where LocalBrain must read or preserve upstream Claude or Codex formats, including Claude's `subagents/` directory and Codex `source.subagent` metadata.
- Agent-orchestration prompts may still use `subagent` when they refer to an agent process rather than a LocalBrain Session record; that source-operation term is not a product label.

## Constraints

- Explicit human direction supersedes the current durable eight-destination navigation wording, but approval of this PRD must be followed by aligned Product Model and Design Constitution contracts in the owning execution boundary.
- Original Claude and Codex JSONL remains the authoritative Session source.
- `src/localbrain/schema.sql` and compatible migrations remain implementation truth. Removing `workspaces.git_branch` must preserve non-rebuildable user organization that references workspace IDs.
- Parent/subsession inference must use source evidence and preserve provenance; a title, zero-question count, or timing similarity alone is insufficient to establish parentage.
- Every Workstream Claude maintenance consumer of ordinary Sessions must apply the source-neutral subsession exclusion rather than relying on Claude-specific directory behavior.
- Existing accepted Workstream links, Search links, Session detail URLs, Project-to-Session filters, and source filters are regression surfaces.
- The visible `CL` and `CX` marks remain provenance cues only and must retain an accessible full label.
- Pagination, segmented view changes, and dropdown disclosure must be keyboard reachable, focus-visible, and compatible with the supported `1440`, `920`, `700`, and `320` viewport boundaries.
- The sliding indicator is nonessential motion and must resolve to a static but explicit selected state under `prefers-reduced-motion`.
- Tracked tests, fixtures, and rendered evidence use synthetic Session, path, branch, and subsession data.
- The likely execution profile is `fullstack-product` for coupled ingestion, query, route, and visible interaction changes. Candidate child features may use a smaller profile when their boundary is independently evaluable.
- Relevant execution lanes are the parent/subsession contract, ingestion and reconciliation, Session read models and routes, persistent navigation, Session inventory, Session and subsession detail, and durable owner documentation.
- Required evaluation across the complete increment includes Contract, Design, Functional, and UX Heuristic review plus Interaction Evaluation for pagination, view switching, dropdown disclosure, focus, history, and responsive state ownership.

## Acceptance Envelope

- Persistent navigation has one Sessions destination, and entering it without an explicit mode opens Sessions rather than Projects.
- `Sessions | Projects` exposes visible and programmatic selection parity, a sliding selected indicator in normal motion settings, and a stable static selected state under reduced motion.
- The selector sits immediately below the Sessions description with the compact Atlassian selector geometry, and a same-row primary `동기화` action incrementally refreshes Claude and Codex Sessions without scanning Local Context sources.
- The Sessions inventory returns at most 15 top-level rows per page and supports repeatable numbered, previous, and next navigation while preserving source and workspace scope.
- Valid direct Claude and Codex child records are reachable from their top-level parent row and no longer appear as ordinary independent top-level rows solely because their source formats differ.
- Only direct children of a top-level Session appear in its dropdown and retained detail Subsessions section; deeper descendants are preserved but absent from current user-facing Session lookup and presentation.
- A subsession without a resolvable parent is absent from Session inventories, parent dropdowns, and user-facing Session detail access while its authoritative source remains untouched.
- Rows without subsessions do not expose an empty or disabled dropdown trigger.
- The subsession dropdown is keyboard reachable, dismisses intentionally, does not conflict with the row's Session-detail destination, keeps its outer border and radius intact when the child list scrolls, and remains usable at supported narrow widths.
- Opening a parent Session detail continues to expose its Subsessions section so direct detail entry does not depend on having visited the inventory dropdown first.
- Session rows show the requested path, optional branch, question count, event count, and last activity without duplicating the visible Claude or Codex name next to an already present provenance mark.
- When Claude or Codex source metadata provides a branch, LocalBrain persists and presents it from `sessions.git_branch` without mutating the source project or Git state.
- `workspaces.git_root` remains the containing repository's filesystem root, while `workspaces.git_branch` is absent from both the canonical schema and upgraded runtime databases and from Project, retrieval, Task Runner, manifest, and resource payloads.
- Existing branch values are rebuilt only from authoritative Session source metadata; a workspace-level value is never copied or used as a Session fallback.
- Assistive technology can still determine the full source identity for every Session row.
- Session and subsession conversation timelines omit normalized tool-call rows while preserving message order, parent context, navigation, stored event counts, and the underlying raw events.
- Workstream Claude Runs receive no subsession candidates, counts, evidence files, manifest resources, or Suggestions, and eligible parent Sessions do not inherit child content implicitly.
- Global Search and every Session-derived Dashboard or activity statistic exclude subsessions from both sources without deleting their stored events or source identity.
- Existing direct links, filters, Workstream memberships, Projects aggregation, Search destinations, maintenance Run exclusion, and missing-path treatment continue to work.
- Synthetic browser evidence for FEAT-0015 through FEAT-0018 covers default, filtered, paged, short-final-page, no-results, parent-with-children, parent-without-children, open-dropdown, missing-path, long-path, and conversation-with-tool-events states at the required viewport boundaries.
- Repository privacy checks and the relevant parser, ingestion, query, route, and UI contract tests pass; FEAT-0019's unavailable rendered evidence remains explicit and was accepted by the human owner as a non-blocking quality-evidence limit.

## Candidate Features

- [FEAT-0015: Session And Subsession Source Contract](../feature/feat-0015-session-subsession-source-contract.md) (`foundation`, `passed`): define and persist source-neutral parentage, reconciliation, Workstream-maintenance exclusion, per-Session branch ownership, and removal of the obsolete workspace branch field.
- [FEAT-0016: Sessions And Projects Navigation](../feature/feat-0016-sessions-projects-navigation.md) (`product`, `passed`): consolidate Sessions and Projects navigation with Sessions as the default and an accessible sliding view switch.
- [FEAT-0017: Paginated Session Inventory](../feature/feat-0017-paginated-session-inventory.md) (`product`, `passed`): add 15-item Session pagination, concise row metadata, and conditional parent-row subsession disclosure.
- [FEAT-0018: Conversation-Focused Session Details](../feature/feat-0018-conversation-focused-session-details.md) (`product`, `passed`): make Session and subsession details conversation-focused while preserving stored tool events and relationship navigation.
- [FEAT-0019: Session Inventory Sync Toolbar](../feature/feat-0019-session-inventory-sync-toolbar.md) (`product`, `passed`): align the combined inventory toolbar with the Atlassian selector and add a Session-only synchronization action.

All five linked Features completed their Specs, Runs, and automated verification. Features 0015 through 0018 include synthetic browser evidence; Feature 0019 records the current environment's rendered-browser evidence gap explicitly. Human post-run review accepted the completed run set and the PRD is `passed`.

### Accepted Post-Run Evidence Boundary

- FEAT-0019's direct rendered checks at 1440, 700, and 320px for selector geometry, same-row containment, and the Session-only source-status summary remain a quality-evidence gap rather than a known implementation defect.
- Synthetic warm-revisit HTTP verification confirmed stable versioned assets, a successful Session-only synchronization response, and the canonical Subsession terminology. Browser-only working, success, failure, and focus-state capture remains unavailable in the current control environment.
- The human owner accepted these explicit non-blocking evidence limits and closed PRD-0002. They remain in the project quality backlog for later browser regression coverage.
- Complete ERD visibility and wider approved cleanup passed separately under PRD-0003 and are not part of this PRD's acceptance boundary.

Executed order:

1. `feat-0015` fixes the source-neutral Session/subsession and branch contract required by later consumers.
2. `feat-0016` establishes the combined Sessions destination independently of the data contract.
3. `feat-0017` consumes both passed prerequisites for pagination, row metadata, and subsession disclosure.
4. `feat-0018` consumes valid child destinations and narrows detail presentation to conversation messages.
5. `feat-0019` refines the combined inventory toolbar and separates Session-only synchronization from the wider Sources scan.

The Features ran sequentially as authorized by the human owner.

## Related Data Model Planning

- This PRD owns the concrete `workspaces.git_branch` removal and `sessions.git_branch` addition because they are required for accurate Session browsing.
- [PRD-0003: Data Model Visibility And Schema Cleanup](prd-0003-data-model-visibility-and-schema-cleanup.md) owns the complete ERD, subject-area table catalog, rebuildability and authority classification, and any wider cleanup decisions.
- The split keeps this approved Session increment executable without silently authorizing unrelated table migrations. Findings from PRD-0003 may become later Features only after separate human boundary review.

## Source Map

| Source | Priority | Contribution | Boundary |
| --- | --- | --- | --- |
| Human request | primary | navigation consolidation, default view, Session-only synchronization, 15-item pagination, responsive numbered reach, row metadata, subsession dropdown, conversation-only display, non-exposure of parentless subsessions, Workstream maintenance exclusion, and Session-owned branch data | wider schema cleanup remains a separate planning boundary |
| Current Claude and Codex source metadata | primary implementation evidence | proves that Claude directory structure and Codex parent metadata can identify source-backed child relationships | private source content and machine-specific paths are not copied into this PRD |
| Current LocalBrain code and schema | primary compatibility evidence | owns existing ingestion, Session identity, query, route, event, and maintenance Run behavior | current asymmetry is evidence, not the desired product contract |
| Product Model and Project Architecture | durable supporting contract | owns entity responsibility, source authority, Workstream separation, and existing lazy Claude Subsession compatibility policy | navigation and source-neutral Subsession wording require an approved downstream contract update |
| Design Constitution | primary design contract | owns provenance, navigation, density, responsive, accessibility, and reduced-motion behavior | does not decide parent identity or pagination query semantics |
| Design and Interaction Evaluation | supporting evaluation contract | owns pagination, disclosure, focus, transition, containment, and viewport checks | does not invent product scope or implementation mechanism |
| Accepted Features 0005 and 0008 | regression evidence | owns the prior Sessions inventory and Session/Subsession detail behavior that this increment intentionally revises | passed presentation decisions do not prevent a newly approved product change |
| Claude Task Runner policy | durable exclusion contract | confirms Workstream maintenance Runs remain outside ordinary Sessions | does not govern normal Claude or Codex parent/subsession ingestion |

## Continuity Notes

- `2026-07-17`: created the initial draft from the human request, current Session and Project UI, accepted Session inventory/detail Features, source adapters, representative Codex metadata structure, and the durable design and interaction contracts.
- `2026-07-17`: recorded the Claude/Codex exposure difference as a source-contract gap rather than treating it as a presentation-only defect.
- `2026-07-17`: human review resolved orphan handling: subsessions without a resolvable parent remain untouched at the source but are not exposed on user-facing Session surfaces.
- `2026-07-17`: human review excluded every subsession from Workstream Claude maintenance candidates, evidence, manifests, and Suggestions without merging child content into the parent Session.
- `2026-07-17`: human review approved read-only Claude and Codex branch normalization inside LocalBrain; project files and Git state remain outside the mutation boundary.
- `2026-07-17`: human direction approved this PRD boundary and requested all candidate Feature documents; status changed to `approved` and Features 0015 through 0018 were created as drafts.
- `2026-07-17`: human Feature review retained the parent Session detail Subagents section as a second child-access path alongside the inventory-row dropdown.
- `2026-07-17`: human runtime review refined FEAT-0017 with compact numbered pagination, an inner-scrolling subsession list that preserves the overlay boundary, and one continuous row hover state across the Session link and disclosure cell.
- `2026-07-17`: human runtime review changed the default page size to 15 and capped numbered pagination at seven desktop tokens and five narrow-screen tokens.
- `2026-07-17`: human review fixed branch ownership: retain `workspaces.git_root`, add source-backed `sessions.git_branch`, physically remove `workspaces.git_branch` and its consumers, and never backfill Sessions from the ambiguous workspace value.
- `2026-07-17`: human review limited subsession presentation to one direct-child depth; deeper source hierarchy remains preserved but is not flattened or exposed in current Session UI.
- `2026-07-17`: human review excluded every Claude and Codex subsession from global Search and all Session-derived Dashboard and activity statistics while preserving source-backed child data.
- `2026-07-17`: separated complete ERD visibility and wider table cleanup into linked draft PRD-0003 so this Session-focused boundary does not authorize unrelated schema refactoring.
- `2026-07-17`: stopped at Feature boundary review; no Spec, code, schema, route, Run, or runtime behavior was changed.
- `2026-07-17`: human direction authorized sequential execution; FEAT-0015 through FEAT-0018 completed in order and are `passed` with source contract, navigation, inventory, and detail evidence.
- `2026-07-17`: actual `:8000` evidence invalidated FEAT-0017 Attempt 1 because the long-running process mixed old Python context with the new template. FIX-0017 added transition-safe defaults, the actual server and database were backed up and migrated, and Attempt 2 passed with real page 1/page 2, Projects, and Session-detail checks.
- `2026-07-17`: the complete 38-test suite, JavaScript and template checks, Python compilation, repository privacy check, synthetic 1440/920/700/320 evidence, and actual-runtime checks passed. PRD status remains `approved` pending post-run human review.
- `2026-07-18`: human direction added the compact inventory-toolbar alignment and Session-only `동기화` action; FEAT-0019 implemented the scoped endpoint while preserving the wider Sources scan.
- `2026-07-18`: the Sessions source-status summary was narrowed to Claude and Codex and the database-path annotation was removed; automated coverage reached 47 tests, while direct FEAT-0019 rendered and warm-cache interaction evidence remains open for post-run review.
- `2026-07-18`: removed the resolved selector route/enhancement question from uncertainty; direct links, progressive enhancement, history behavior, selected semantics, and reduced-motion handling are now implementation decisions owned by FEAT-0016 and FEAT-0019. Source-neutral `Subsession` versus `Subagent` product terminology remains open.
- `2026-07-19`: human review selected `Subsession` as LocalBrain's single product term. Source-native `subagent` names remain only at upstream format and agent-orchestration boundaries.
- `2026-07-19`: 142 tests, Python compilation, repository privacy verification, synthetic parent/child HTTP rendering, stable versioned warm-revisit assets, Session-only synchronization, and the legacy-route redirect passed. The human owner accepted the explicit browser-only evidence limit and closed the PRD as `passed`.
