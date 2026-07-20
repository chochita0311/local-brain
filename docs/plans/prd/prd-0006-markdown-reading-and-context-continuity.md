# PRD-0006: Markdown Reading And Context Continuity

## Metadata

- ID: `prd-0006`
- Status: `passed`
- Owner role: `human`
- Created: `2026-07-19`
- Updated: `2026-07-20`

## Request Summary

- Improve Markdown reading quality in Local Context document previews, full Document views, and Session conversation bodies while preserving the approved LocalBrain Design Constitution.
- Use a shared CommonMark and GitHub Flavored Markdown baseline with selected Obsidian Flavored Markdown authoring syntax, safe local link resolution, and local-only code highlighting; defer image and attachment rendering to a tracked follow-up.
- Refine Local Context navigation by removing the separators immediately above the FOLDERS and FILES add controls, adding a resizable source-tree and preview split, preserving the current window position across FOLDERS source changes, moving Local Contexts directly after Sessions in the application navigation, and keeping the owning FOLDERS source tree visible in full Document reading.

## Source Set

### Human Request

- Make Markdown documents and Session conversations feel closer to a polished note reader such as the owner-supplied local note viewer or Obsidian without replacing LocalBrain's existing visual system.
- Remove the bar line between the FOLDERS list and `경로 추가`.
- Remove the bar line between the FILES list and `파일 추가`.
- Preserve the current window page position when changing the active FOLDERS source, while starting the destination tree and preview-local state fresh.
- Let the user resize the space between the source tree and Markdown preview by dragging an affordance revealed at the pane boundary.
- Move `Local Contexts` from its current `06` position to immediately after `Sessions`.
- Keep the relevant FOLDERS source tree visible on the left when a document is opened in its full reading view.
- Support the owner-preferred Obsidian-style authoring syntax in the reader without requiring Obsidian or executing third-party plugins.
- Defer Markdown images and attachment embeds to a follow-up TODO.
- Resolve safe internal and external links according to the local-first boundary, use local-only syntax highlighting with a plain-code fallback, and apply Markdown only to visible user and assistant conversation bodies.

### Golden Sources

- [Design Constitution](../../policies/design/design-constitution.md): LocalBrain shell, typography, spacing, color, responsive, detail-reading, explorer, accessibility, and source-provenance contract.
- Current Local Context explorer, full Document detail, and Session detail behavior in LocalBrain.
- Owner-supplied local note-viewer reference: reading hierarchy, bounded line length, Markdown block treatment, code and table containment, and contextual navigation continuity. It is a visual and interaction reference only.
- [Obsidian Flavored Markdown](https://obsidian.md/help/obsidian-flavored-markdown) and [Internal links](https://obsidian.md/help/Linking%20notes%20and%20files/Internal%20links): official syntax references for the approved authoring-compatibility subset.

### Supporting Documents

- [Design Evaluation](../../policies/design/design-evaluation.md): readable geometry, responsive containment, source-use discipline, divider ownership, and rendered evidence requirements.
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md): bounded source-switch scroll continuity, preview continuity, focus, history, pointer and keyboard affordances, and Markdown-link behavior.
- [FEAT-0014 Local Context Explorer](../feature/feat-0014-local-context-explorer.md): existing source rail, source tree, preview selection, source switching, disclosure, scroll, focus, history, and narrow-layout contract.
- [FEAT-0009 Document And Resource Details](../feature/feat-0009-document-resource-details.md): existing full Document route and its prior exclusion of Markdown rendering and a full context explorer tree.
- [PRD-0002 Session Browsing And Subsession Organization](prd-0002-session-browsing-and-subsession-organization.md): current Session and Subsession navigation and detail boundaries.

### Current Implementation References

- `src/localbrain/templates/context.html`: FOLDERS and FILES source groups, add controls, source tree, document preview, and full-view entry.
- `src/localbrain/templates/document.html`: current full Document metadata and plain-text body.
- `src/localbrain/templates/session.html`: current plain-text Session message bodies and existing role and timestamp presentation.
- `src/localbrain/templates/base.html`: current navigation order, with Sessions at `04`, Atlassian at `05`, and Local Contexts at `06`.
- `src/localbrain/static/styles.css`: current add-control separators, fixed explorer columns, reading surfaces, and responsive pane stacking.
- `src/localbrain/static/app.js`: same-source preview selection, source-tree disclosure, selected-item reveal, focus, history, and source-switch navigation behavior.
- `src/localbrain/main.py` and `src/localbrain/contexts.py`: Local Context source selection, source-tree construction, document membership validation, and full Document route data.

## Current Findings

- Local Context previews, full Document bodies, and Session message bodies currently preserve whitespace as plain text; they do not share a rendered Markdown reading contract.
- The Local Context explorer already separates source inventory, source tree, and document preview, but the tree and preview widths are fixed.
- The separators the owner wants removed belong to the FOLDERS and FILES add-control containers. The boundary between the FOLDERS and FILES groups is a separate structural divider and is not part of this request.
- Same-source document selection keeps the tree mounted, reveals the selected item, preserves disclosure and local navigation continuity, and updates browser history. FOLDERS source changes use normal navigation, retain only the current window page position, and start the destination tree, preview, disclosure, and splitter state fresh.
- The full Document route currently has no owning Local Context source or source-tree context even when the document was opened from a FOLDERS source.
- Local Context rejects overlapping enabled FOLDERS roots, including registering a child folder below an existing root or a parent folder above one. It also rejects adding an individual FILE already covered by an enabled FOLDERS root, and each indexed Document path is unique. A Document therefore has one owning Local Context source under the current contract.
- At `700px` and below, the explorer already becomes a sequential tree-then-preview layout. A pointer-driven resize mode would not be useful in that narrow composition.
- The owner-supplied note viewer demonstrates useful reading patterns, but its colors, fonts, branded components, note outline rail, and application shell are not LocalBrain requirements.
- Obsidian's official Markdown contract combines CommonMark, GitHub Flavored Markdown, and Obsidian-specific extensions. LocalBrain can consume the approved syntax without becoming an Obsidian vault, plugin runtime, or editor.

## Product Intent

- Make imported Markdown and Markdown-shaped conversation text comfortable to scan and read for sustained work without losing source identity, navigation context, or LocalBrain's established visual character.
- Let users allocate horizontal space between navigation and reading according to the current document while retaining a predictable responsive fallback.
- Preserve orientation when moving between a FOLDERS source tree, a document preview, and a full Document view, including direct entry and browser navigation.

## Confirmed Scope

### Shared Markdown Reading Contract

- Establish one shared, explicit Markdown presentation contract for:
  - Local Context document previews
  - full Document reading views
  - textual user and assistant message bodies in Session and Subsession detail
- Preserve the stored source body unchanged. Rendering is a presentation concern and must not rewrite imported Documents or Session events.
- Plain text without Markdown markers remains readable and does not require a separate mode switch.
- Support a practical baseline for technical and note content, including:
  - headings
  - paragraphs and line breaks
  - emphasis and strong emphasis
  - ordered and unordered lists
  - blockquotes
  - inline code
  - fenced code blocks with an optional language label
  - links
  - basic pipe tables
  - horizontal rules
- Use CommonMark and GitHub Flavored Markdown semantics as the interoperability baseline and additionally support the following Obsidian Flavored Markdown authoring constructs:
  - nested lists
  - read-only task lists
  - strikethrough and highlight
  - footnotes
  - comments that remain in source but do not appear as body content
  - wikilinks, optional display aliases, and source-local folder paths
  - links to headings and stable heading anchors
  - block identifiers and block references
  - callouts
  - tags
  - YAML frontmatter properties presented separately from body content when valid
  - inline and block math
  - Markdown note embeds with bounded recursion and cycle protection
- Do not treat arbitrary third-party Obsidian plugin syntax as automatically supported. A named plugin's source syntax requires a separately reviewed extension to this allowlist; LocalBrain never loads or executes Obsidian plugin code.
- Defer standard Markdown images and Obsidian image or non-Markdown attachment embeds to the tracked image-rendering TODO. Unsupported image syntax remains safe and understandable without initiating a network request.
- Resolve links according to the following contract:
  - same-document heading and block links move to the stable rendered target
  - relative Markdown links and Obsidian wikilinks resolve only to indexed Documents inside the owning Local Context source and open in the appropriate LocalBrain Document surface
  - unresolved internal links remain visibly unavailable without guessing a target or creating a file
  - Session or Subsession references without an owning Local Context source remain readable but unresolved rather than using an ambiguous global match
  - HTTP and HTTPS links open only after user activation, use explicit external-link treatment, and do not prefetch or embed the destination
  - `file` targets, root-escaping relative paths, executable protocols, and unsafe schemes remain disabled
- Provide local-only syntax highlighting for an approved set of common technical languages. The exact language allowlist belongs to Feature and Spec work, and every unsupported or failed grammar falls back to the readable generic code-block treatment without changing source text.
- Use LocalBrain typography, spacing, colors, radii, borders, focus treatment, and content-width tokens. The external references contribute reading principles, not a replacement theme.
- Bound long-form reading width even when the surrounding explorer or full-view workspace is wide.
- Keep long URLs, paths, headings, table cells, and code contained. Tables and code may scroll within their own region rather than forcing the entire page wider.
- Keep source metadata, message role, timestamp, Session identity, and Document provenance visually distinct from rendered body content.
- Escape or sanitize unsafe markup and unsafe link targets before content reaches an executable browser context. Markdown rendering must not turn imported local text into script execution.
- Preserve usable focus-visible links and a logical reading order. Link meaning must not depend on color alone.
- Define deterministic empty, unreadable, and render-failure fallback states that retain access to the original plain text when it can be shown safely.

### Local Context Reading And Explorer Refinement

- Apply the shared Markdown contract to the selected Document preview without changing source-tree membership or selection semantics.
- Remove the decorative separator immediately above `경로 추가` in the FOLDERS group.
- Remove the decorative separator immediately above `파일 추가` in the FILES group.
- Preserve the separate FOLDERS-versus-FILES group boundary and the current add-control labels, scope, and behavior.
- Add an adjustable boundary between the source tree and Markdown preview in the side-by-side explorer layout:
  - the boundary communicates resize availability on pointer hover and keyboard focus
  - pointer drag changes the two pane widths continuously within safe minimum and maximum bounds
  - when the separator has keyboard focus, directional keys provide the equivalent resize operation without requiring a separate visible control
  - resizing does not select tree items, highlight body text, or lose the active document
  - the reading pane never becomes narrower than a usable technical-reading surface
- Derive the default, minimum, maximum, and keyboard-step geometry from the Design Constitution's explorer, reading-width, compact, and narrow-layout rules during Feature and Spec work rather than introducing a separate PRD-level sizing system.
- Keep the adjusted width only for the lifetime of the current Local Context screen instance:
  - same-screen source and Document selection retain the adjusted width
  - reload or a new Local Context entry starts at the default width
  - leaving for another LocalBrain screen or full Document view and later returning starts at the default width
  - merely changing focus to another browser tab without leaving the Local Context screen does not reset the width
- Do not persist the adjusted width across screen entries and do not provide a reset button, menu, or dedicated reset gesture.
- At the narrow breakpoint, remove or disable the resize interaction and retain the approved sequential source-tree then preview composition.
- Keep same-source document selection continuity from FEAT-0014: expanded ancestors, tree scroll, selected-item visibility, focus, browser history, and stable shell state remain intentional.
- Keep FOLDERS source switching as a new-scope transition while preserving the current `window.scrollY`. The destination does not inherit the previous source's tree scroll, preview scroll, disclosure state, selection, or adjusted splitter width.

### Context-Aware Full Document Reading

- When a Document belonging to a FOLDERS Local Context source opens in full view, show that source's tree on the left and the selected Document reading surface on the right.
- Resolve the full-view tree from the Document's single owning FOLDERS source. Preserve the current non-overlapping-root and unique-Document-path contract rather than introducing source selection or duplicate Document identities.
- Expand the selected Document's required ancestors, expose its current state, and keep the selected item visible in the source tree on direct entry, refresh, and in-app entry.
- Keep the full-view reading column bounded and allow the source tree to scroll independently when needed.
- Preserve the full Document URL as a direct, refresh-safe destination. Users must not need to enter through the Local Context explorer first to recover the owning tree context.
- Selecting another Document from the full-view source tree keeps the user in full-view reading mode, replaces the right-hand Document with the new selection, updates the full Document URL and selected tree state, and preserves meaningful browser back and forward navigation.
- For a Document owned only by FILES, Apple Notes, or another non-FOLDERS source, retain the bounded full reading layout without an empty tree. Keep its source identity and Local Contexts return path available in the existing metadata and navigation area.
- Preserve a clear return path to Local Contexts and consistent source and Document identity.
- Collapse the full-view tree and reading surface into an intentional sequential composition when the supported width cannot retain a readable two-pane layout.

### Session And Subsession Conversation Reading

- Apply the shared Markdown contract to textual user and assistant messages in Session and Subsession detail.
- Do not newly apply Markdown rendering to system, source-specific, tool, or other structural events; retain their existing visibility and presentation contract.
- Preserve existing message order, role differentiation, timestamps, source identity, and omission rules for content that is not currently part of the visible conversation.
- Keep each message body readable within its existing conversation hierarchy; Markdown styling must not make every message appear like a separate unrelated document.
- Ensure long code, tables, URLs, and mixed Korean and English text remain contained at every supported width.

### Navigation Order

- Place Local Contexts immediately after Sessions in the main navigation.
- Renumber the affected product destinations so the sequence becomes:
  - `04 Sessions`
  - `05 Local Contexts`
  - `06 Atlassian`
- Preserve the existing destinations, active-state behavior, and remaining `07 Sources` and `08 Schema` order.

### Design And Evaluation Boundary

- Expected execution profile: `Fullstack Product`.
- Affected surface lanes:
  - shared Markdown rendering and safety contract
  - Local Context explorer and resizable split panel
  - context-aware full Document reading
  - Session and Subsession conversation reading
  - persistent application navigation order
- The Design Constitution remains the compatibility baseline. The follow-up may add durable semantic reading roles without replacing the shell, global theme, or existing visual language.
- Visible child Features require Contract, Design, Functional, and UX Heuristic evaluation as applicable.

## Excluded Scope

- Replacing the Design Constitution, LocalBrain shell, global theme, typography family, brand color system, or navigation model.
- Copying the owner-supplied viewer or Obsidian theme exactly, importing their CSS, or treating either product as a runtime dependency. Official Obsidian Flavored Markdown syntax is a bounded authoring-compatibility target, not a visual or runtime dependency.
- An Obsidian vault connector, plugin installation or execution, arbitrary third-party plugin syntax, backlink index, graph view, editor, live-edit preview, command palette, or note-management behavior.
- Editing, formatting, or rewriting Document and Session source text.
- A new outline or table-of-contents rail, previous or next note navigation, copy actions, sharing, bookmarking, or note metadata model solely because they exist in a reference viewer.
- Markdown image or non-Markdown attachment rendering in this delivery, automatic remote image loading, network enrichment, external Markdown rendering, external fonts, external syntax-highlighting assets, or an external AI service.
- Persisting an adjusted source-tree width across Local Context screen entries or providing a default-width reset button, menu, or dedicated reset gesture.
- Showing an empty source-tree column or inventing a folder hierarchy for FILES, Apple Notes, or another non-FOLDERS Document.
- Allowing overlapping enabled FOLDERS roots, duplicating one physical Document across multiple Local Context source identities, or adding a source chooser to solve a state the current source contract rejects.
- Changes to FOLDERS or FILES add, remove, indexing, health, or source-membership behavior beyond the requested separator presentation.
- Removing the structural separator between the FOLDERS and FILES source groups.
- Carrying one source's tree scroll, preview scroll, disclosure state, selection, or splitter width into another source.
- New Session event types, parser behavior, tool-result visibility, conversation summarization, or Session organization changes.
- Spec, schema, route, template, style, script, or implementation work before one draft Feature is reviewed and approved as the active execution target.

## Uncertainty

- No PRD-level product boundary remains open from the owner's review of items 1 through 12.
- Child Feature and Spec work still chooses the local renderer and highlighter mechanism, exact highlighted-language allowlist, Design Constitution-compatible callout, property, math, and unresolved-link presentation, and deterministic parser limits for note-embed recursion and pathological input. These are implementation and evaluation decisions within the confirmed boundary rather than permission to add syntax or external dependencies.
- Support for a specific third-party Obsidian plugin syntax requires the owner to name that plugin and approve its syntax contract; no unnamed plugin compatibility is implied by this PRD.

These items may remain open while the PRD is `draft`, but each material interaction or content-contract decision must be resolved before its dependent Feature is approved for Spec handoff.

## User-Visible Flows And Interaction Expectations

### Read A Markdown Document In Local Contexts

- The user selects a FOLDERS source and a Markdown Document from its tree.
- The preview presents a clear heading, paragraph, list, quote, table, link, and code hierarchy while the source tree retains selection and disclosure context.
- Choosing a sibling Document changes only the intended preview state and does not unexpectedly rebuild or reposition stable navigation.
- Wikilinks, heading and block references, callouts, task lists, highlights, footnotes, properties, math, and bounded Markdown note embeds read consistently with the approved Obsidian-compatible authoring contract.
- Image and attachment syntax remains a safe deferred state and never triggers automatic remote loading.

### Adjust The Explorer Split

- The user moves the pointer to the boundary between the source tree and preview and sees a resize affordance only on the interactive boundary.
- Dragging or using the keyboard changes the source-tree width within safe bounds while the selected Document and its reading position remain stable.
- The adjusted width remains while the current Local Context screen stays active, but reload, new entry, or leaving for another LocalBrain screen and returning restores the Design Constitution-derived default without requiring a reset control.
- Entering the narrow layout removes the unsupported side-by-side resize mode and leaves both tree and content reachable in sequential order.

### Change FOLDERS Sources

- The user changes from one FOLDERS source to another after scrolling within the original tree or preview.
- The destination retains the user's current window page position but starts with fresh tree and preview-local scroll, disclosure, selection, and splitter state.
- Returning through browser history restores the approved source, selection, disclosure, and focus orientation rather than an arbitrary mixed state.

### Open A Full Document With Context

- The user opens a FOLDERS Document in full view or enters its URL directly.
- The owning source tree appears on the left with the Document selected and visible; the Markdown body appears in a bounded reading column on the right.
- Selecting another tree Document replaces the reading body while remaining in full-view mode and synchronizes the URL, selection, and browser history.
- Refresh and browser back or forward retain correct source and Document orientation without requiring a prior explorer visit.
- A non-FOLDERS Document keeps the bounded full reading layout and source metadata without reserving an empty source-tree column.

### Read A Session Conversation

- The user opens a Session or Subsession containing plain text and Markdown-shaped messages.
- Plain messages remain natural, while headings, lists, links, tables, quotes, inline code, and fenced code become easier to scan inside the conversation.
- Role, timestamp, message order, and Session context remain clearer than the Markdown decoration.
- Only user and assistant bodies receive Markdown rendering; structural, system, source-specific, and tool-event behavior remains unchanged.

### Recover From Unreadable Content

- Unsupported or malformed Markdown does not execute markup, break the shell, or erase the underlying source text.
- The surface shows an intentional fallback and retains enough source and Document or Session identity for the user to understand what failed.

## Constraints

- Explicit human direction and the approved PRD boundary govern scope.
- The LocalBrain Design Constitution owns visual and responsive decisions; reference apps supply reading ideas only.
- Document and Session source data remain authoritative and unchanged. Rendered Markdown is derived presentation.
- Imported local content is not trusted as executable HTML. Rendering and links require an approved safety contract.
- The application remains local-first and must not fetch content, renderers, fonts, images, or highlighting assets from the network without separate approval.
- CommonMark, GitHub Flavored Markdown, and the approved Obsidian syntax subset are content contracts, not permission to install or execute Obsidian or third-party plugins.
- Direct entry, refresh, browser back and forward, source selection, tree disclosure, local scroll, page scroll, focus, and selected state are one interaction contract, not independent finishing details.
- The supported viewport floor remains `320px`; representative evaluation widths are `1440`, `920`, `700`, and `320`.
- Desktop resize behavior must degrade structurally before the reading typography is compressed.
- Keyboard focus remains visible, the separator follows accessible resize semantics, and interaction does not depend on hover alone.
- Tracked tests, screenshots, examples, and evaluation artifacts use synthetic Markdown and synthetic paths.
- The likely execution order begins with a foundation contract for shared Markdown safety and semantics, followed by bounded visible Features that consume it.
- Execution followed the repository approval gates with one active Feature at a time; each Feature now has an approved Spec, passed Run, and complete required evaluator evidence.

## Acceptance Envelope

- Local Context preview, full Document view, and visible Session or Subsession text use one documented Markdown semantics and safety contract rather than three divergent renderers.
- Representative plain text and Markdown render with clear, LocalBrain-compatible hierarchy for headings, paragraphs, emphasis, lists, quotes, inline code, fenced code, links, tables, and horizontal rules.
- Representative Obsidian-compatible syntax renders deterministically for nested and task lists, strikethrough, highlight, footnotes, comments, wikilinks and aliases, heading and block references, callouts, tags, properties, math, and bounded Markdown note embeds.
- Stored Document and Session bodies remain byte-for-byte authoritative and are not rewritten by presentation.
- Raw HTML, script-shaped content, event handlers, and unsafe links cannot execute through the Markdown surface; malformed input has an intentional readable fallback.
- Relative Markdown links and wikilinks cannot escape their owning Local Context source, unresolved targets do not create or guess Documents, HTTP and HTTPS destinations require user activation without prefetch, and unsafe or local-file schemes remain disabled.
- Code highlighting uses only local assets and falls back to readable generic code for unknown languages or highlighting failures.
- Markdown reading code uses dedicated neutral reading surfaces and a calm syntax palette rather than Run-console, brand, status, or provenance semantics.
- Standard Markdown images and Obsidian image or attachment embeds remain outside this delivery and are tracked as a follow-up without automatic network access.
- Long code, tables, URLs, paths, headings, and mixed-script text remain contained at `1440`, `920`, `700`, and `320` widths.
- FOLDERS `경로 추가` and FILES `파일 추가` no longer have a separator immediately above them, while the FOLDERS and FILES group boundary remains visible and add behavior remains unchanged.
- At supported side-by-side widths, pointer and keyboard users can resize the tree and preview within approved bounds without losing selection, focus, tree disclosure, or reading position.
- The adjusted width persists only within the active Local Context screen instance; reload, new entry, or leaving and returning restores the approved default, while a browser-tab focus change alone does not reset it.
- No persistent preference or dedicated default-width reset control is introduced.
- At narrow width, the unsupported resize affordance is absent and the source tree and preview remain reachable in sequential order.
- Same-source Document selection preserves its approved tree and history continuity. Switching FOLDERS sources preserves only the current window page position while resetting destination-local tree, preview, disclosure, selection, and splitter state.
- A FOLDERS Document full-view URL resolves its owning source tree on direct entry and refresh, reveals the selected Document, and preserves a readable body column; selecting another tree Document stays in full-view mode and synchronizes the body, URL, selection, and history.
- The full-view source tree relies on the existing non-overlapping FOLDERS-root and unique Document-path contract; it does not create duplicate Document identities or a source-selection step.
- A FILES, Apple Notes, or other non-FOLDERS Document retains a bounded full reading layout, source identity, and return path without an empty tree column.
- Session and Subsession Markdown applies only to visible user and assistant bodies and does not obscure role, timestamp, order, source identity, or existing structural-event boundaries.
- Main navigation presents `04 Sessions`, `05 Local Contexts`, `06 Atlassian`, `07 Sources`, and `08 Schema` with unchanged destinations and active-state semantics.
- Synthetic unit, route, template, interaction, responsive, accessibility, and browser evidence covers plain text, every confirmed Markdown and Obsidian syntax type, valid and unresolved internal links, external and unsafe links, image and attachment deferral, highlight fallback, note-embed cycles and depth limits, unsafe input, malformed input, empty content, deep trees, long paths, source switching after scroll, same-source selection, direct full-view entry, refresh, history, pointer drag, keyboard resize, and narrow-layout transitions.
- Required Contract, Design, Functional, and UX Heuristic evaluations pass with rendered evidence for the approved visible Features.

## Candidate Features

- [FEAT-0038 Shared Markdown Rendering And Safety Contract](../feature/feat-0038-shared-markdown-rendering-and-safety-contract.md) (`foundation`, `fullstack`): establish the source-preserving CommonMark and GitHub Flavored Markdown renderer, sanitization, local code highlighting, image deferral, and deterministic fallback contract.
- [FEAT-0039 Obsidian Syntax And Local Reference Contract](../feature/feat-0039-obsidian-syntax-and-local-reference-contract.md) (`foundation`, `fullstack`): extend the shared renderer with the approved Obsidian authoring allowlist, source-scoped link resolution, safe external links, properties, math, and bounded Markdown note embeds.
- [FEAT-0040 Local Context Navigation Order](../feature/feat-0040-local-context-navigation-order.md) (`product`, `frontend`): move and renumber Local Contexts immediately after Sessions while preserving every destination and active-state behavior.
- [FEAT-0041 Local Context Markdown Preview And Resizable Explorer](../feature/feat-0041-local-context-markdown-preview-and-resizable-explorer.md) (`product`, `fullstack`): consume the shared renderer in the preview, remove add-control separators, provide accessible page-local pane resizing, and preserve source and preview continuity.
- [FEAT-0042 Context-Aware Full Document Reading](../feature/feat-0042-context-aware-full-document-reading.md) (`product`, `fullstack`): resolve a FOLDERS Document's owning source tree on direct entry and preserve full-view reading while users select sibling Documents.
- [FEAT-0043 Session Markdown Conversation Reading](../feature/feat-0043-session-markdown-conversation-reading.md) (`product`, `fullstack`): apply the shared contract only to visible user and assistant message bodies without changing conversation structure or stored events.
- [`Markdown Image And Attachment Rendering`](../project/backlog.md#markdown-image-and-attachment-rendering) (`product`, deferred TODO): safely resolve source-contained images and attachments after the core text, link, and Obsidian syntax contract stabilizes.

The human owner approved this PRD boundary by requesting Feature creation on `2026-07-19`. FEAT-0038 through FEAT-0043 passed sequential Feature-boundary review, implementation, and evaluation. The image and attachment TODO remains a separate backlog item and did not receive an execution Feature in this increment.

### Recommended Feature Order

1. FEAT-0038 fixes the shared baseline renderer, trust, highlighting, image-deferral, and fallback contract.
2. FEAT-0039 fixes the Obsidian syntax, source-local reference, properties, math, and bounded note-embed contract on top of FEAT-0038.
3. FEAT-0040 applies the independent shared-shell navigation reorder and may be selected earlier after Feature review because it has no renderer dependency.
4. FEAT-0041 consumes both foundation contracts in the Local Context preview and establishes the updated explorer tree and reading presentation.
5. FEAT-0042 reuses FEAT-0041's current tree and reading presentation in context-aware full Document mode.
6. FEAT-0043 consumes the two foundation contracts in Session and Subsession conversation bodies and may proceed after FEAT-0039 independently of FEAT-0041 and FEAT-0042.

No decomposition uncertainty blocks Feature review. Only one Feature should become the active approved execution target at a time unless the human owner explicitly changes the execution policy.

## Source Map

| Source | Priority | Contribution | Boundary |
| --- | --- | --- | --- |
| Human request | primary | Markdown and Obsidian-compatible authoring syntax, reading polish, two add-control separator removals, resizable tree and preview, source-switch scroll preservation, navigation reorder, FOLDERS tree in full view, safe links, local highlighting, user and assistant rendering, and image deferral | does not authorize editing, a new theme, plugin execution, arbitrary unnamed plugin syntax, or unrelated source behavior |
| Design Constitution | governing | LocalBrain visual language, reading width, explorer composition, shell continuity, accessibility, responsive behavior, content containment, and dedicated Markdown reading-code semantics | durable visual changes are recorded in the constitution rather than owned by this PRD |
| Current LocalBrain implementation | implementation truth | existing source groups, source-switch full navigation with bounded window-scroll continuity, same-source preview continuity, non-overlapping FOLDERS roots, unique Document paths, full Document route, conversation structure, and navigation order | implementation gaps do not decide unresolved product behavior |
| FEAT-0014 | inherited behavior | source-tree selection, disclosure, scroll, focus, history, preview updates, and narrow sequential explorer | new work must not regress its continuity contract |
| FEAT-0009 | inherited behavior | existing full Document destination and metadata | its prior Markdown and context-tree exclusions are extended only through this PRD |
| Owner-supplied local note viewer | primary visual reference | readable line length, typographic hierarchy, contained code and tables, link affordance, and contextual reading navigation | no exact theme, shell, custom syntax, assets, data, or runtime dependency transfers |
| Official Obsidian Markdown documentation | syntax authority | CommonMark and GitHub Flavored Markdown baseline plus wikilinks, embeds, block references, footnotes, comments, strikethrough, highlights, tasks, callouts, and related Obsidian authoring conventions | no theme, vault integration, plugin runtime, arbitrary third-party plugin syntax, editor, or image delivery is implied |
| Design and Interaction Evaluation | governing evaluation | divider ownership, source-use discipline, bounded source-switch scroll continuity, preview continuity, link behavior, focus, history, and rendered evidence | supplies geometry, accessibility, and evidence criteria without authorizing external assets or broader product behavior |

## Continuity Notes

- `2026-07-19`: created the initial draft from the owner's Markdown reading, Local Context explorer, full Document context, and navigation-order request.
- `2026-07-19`: declared `Fullstack Product` as the expected execution profile and identified shared rendering, explorer, full Document, Session conversation, and navigation lanes while keeping the Design Constitution unchanged.
- `2026-07-19`: initially preserved FEAT-0014's same-source preview continuity and the then-approved scroll reset when changing FOLDERS sources.
- `2026-07-19`: treated the owner-supplied local note viewer as a reading reference and later approved official Obsidian Flavored Markdown as a bounded authoring-syntax target while excluding theme copying, vault integration, plugin execution, arbitrary plugin syntax, and external dependencies.
- `2026-07-19`: resolved split behavior to current-screen-only width retention with Design Constitution-derived geometry, keyboard separator operation, and no reset control; resolved full-view tree selection to remain in full-view mode with synchronized body, URL, selection, and history.
- `2026-07-19`: resolved non-FOLDERS full view to retain the bounded reading layout without an empty tree and confirmed that the existing overlap rejection and unique Document-path contract gives each Document one owning Local Context source.
- `2026-07-19`: approved the CommonMark and GitHub Flavored Markdown baseline, the documented Obsidian authoring subset, safe source-local and external link behavior, local-only highlighting with fallback, and Markdown rendering for user and assistant message bodies only.
- `2026-07-19`: deferred Markdown images and non-Markdown attachment embeds to the project backlog and left specific third-party plugin syntax subject to a named, separately approved extension contract.
- `2026-07-19`: human review approved the resolved PRD boundary and requested Feature creation; status moved to `approved`, FEAT-0038 through FEAT-0043 were proposed for boundary review, and image or attachment rendering remained backlog-only.
- `2026-07-20`: FEAT-0038 through FEAT-0043 and Runs 43 through 48 passed in sequence. Chrome MCP completed the remaining FEAT-0041, FEAT-0042, and FEAT-0043 rendered evidence; the final repository suite passed 170 tests, and PRD-0006 moved to `passed` with image and attachment rendering still deferred.
- `2026-07-20`: owner post-pass review superseded the FOLDERS source-switch reset with window-position continuity, requested closed unselected root branches, and identified shared table-fill and code-tone defects. [FIX-0006](../fix/fix-0006-context-reading-follow-up.md) corrected and revalidated those surfaces without reopening the passed Feature sequence.
- `2026-07-20`: documentation review clarified that the disclosure contract applies to every FOLDERS root and that the shared table wrapper and reading-code semantics apply to every Markdown consumer, not only the Documents used as browser evidence.
