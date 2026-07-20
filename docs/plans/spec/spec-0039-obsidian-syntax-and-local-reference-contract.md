# SPEC-0039: Obsidian Syntax And Local Reference Contract

## Metadata

- ID: `spec-0039`
- Status: `passed`
- Run ID: `run-20260719-44`
- Attempt: `2`
- Parent Feature: [feat-0039-obsidian-syntax-and-local-reference-contract](../feature/feat-0039-obsidian-syntax-and-local-reference-contract.md)
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Surface: `fullstack`
- Execution Profile: `foundation-contract`
- Surface Lane: `syntax-extension`, then `local-reference`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Source Set

- Human request: support Obsidian-compatible authoring through direct LocalBrain implementation while preserving the existing design constitution and local-only boundary.
- Parent Feature: FEAT-0039 syntax allowlist, source-contained links, anchors, properties, math, and Markdown note embeds.
- Passed dependency: FEAT-0038 shared safe Markdown renderer.
- Golden sources: official Obsidian syntax documentation, official `mdit-py-plugins` documentation, current `context_roots` and `context_documents` schema, and current `/documents/{id}` route identity.
- Relevant policies: Markdown Rendering, Product, Architecture, Privacy And Data Handling, PRD And Feature Management, and Execution Loop Governance.

## Implementation Goal

- Extend `render_markdown` with deterministic Obsidian-compatible tokens and an optional Local Context reference context while retaining the FEAT-0038 source, safety, local-only, and fallback contracts.

## In-Scope Behavior

- Add Python 3.9-compatible bounded dependencies:
  - `mdit-py-plugins>=0.4,<0.5` for disabled task checkboxes, footnotes, and dollar-math tokenization
  - `PyYAML>=6,<7` for safe YAML property parsing
  - `latex2mathml>=3.77,<4` for local MathML generation without browser CDN or executable TeX
- Extend `MarkdownRenderResult` with immutable ordered properties while preserving `html` and the `ready|empty|fallback` state contract.
- Extend `render_markdown` with an optional immutable `MarkdownReferenceContext`; a call without one remains valid and leaves source-local targets visibly unresolved.
- Support nested lists, disabled task checkboxes, strikethrough, `==highlight==`, footnotes, `%%hidden comments%%`, `[[wikilinks|aliases]]`, headings, explicit `^block-id` anchors, `> [!type]` callouts, `#tags`, YAML properties, `$inline$` and `$$block$$` math, and `![[Markdown note embeds]]`.
- Keep valid YAML mapping properties separate from body HTML in the result; invalid or non-mapping front matter remains readable safe body source rather than silently becoming authoritative metadata.
- Convert supported math locally to MathML; conversion failure retains escaped TeX in a semantic math fallback.
- Assign deterministic document-local anchors:
  - headings use normalized `heading-{slug}` IDs and duplicate headings receive deterministic `-2`, `-3`, and later suffixes
  - explicit block IDs use `block-{id}`
- Add an immutable Local Context resolver contract backed by a supplied collection of indexed Documents from exactly one enabled owning `context_root_id`.
- Resolve standard relative Markdown links from the current Document directory only.
- Resolve path-bearing wikilinks from the owning source root; resolve pathless wikilinks only when exactly one source-contained Document matches the case-insensitive title or basename stem.
- Treat absolute paths, normalized root escapes, percent-encoded escapes, `file:`, `obsidian:`, executable protocols, and schemes other than HTTP or HTTPS as unsafe.
- Render HTTP and HTTPS destinations as explicit external anchors with `target=_blank` and `rel="noopener noreferrer external"`; do not fetch, prefetch, inspect, or embed them.
- Verify heading or block fragments against the resolved Document body before producing `/documents/{id}#...`; missing fragments remain unresolved.
- Render eligible `text/markdown` and `text/x-markdown` note embeds inside a bounded semantic container with a maximum nested depth of three Documents and a visited-document cycle guard.
- For a heading embed, render that heading section through the next heading of equal or higher level; for a block embed, render only the paragraph or list line carrying that explicit block ID.
- Keep image-like and non-Markdown attachment embeds as non-fetching deferred markers inherited from FEAT-0038.
- Add a database adapter that creates a resolver context from one selected indexed Document and its owning enabled FOLDERS root; file sources, Apple Notes sources, Sessions, and Subsessions do not gain root-relative resolution in this Feature.
- Add synthetic tests for the full syntax allowlist, aliases, duplicate anchors, relative and wiki paths, ambiguity, missing fragments, no-source behavior, external and unsafe links, percent-encoded root escape, valid and invalid properties, local math/fallback, note embed success, selected section/block, cycle, depth, missing target, and attachment deferral.

## Out-Of-Scope Behavior

- Running Obsidian, installing or executing Obsidian or third-party plugin code, or accepting arbitrary plugin-produced HTML.
- Backlinks, graph data, vault mutation, note creation, editing, command palettes, or global title search across Local Context sources.
- Remote embeds, image display, local attachment reads, PDFs, media, canvas files, or standard Markdown image rendering.
- Page-specific typography, source-tree layout, full-reading layout, Session cards, navigation order, or browser interaction.
- JavaScript math rendering, external fonts, CDNs, browser fetches, or subprocess TeX execution.

## Affected Surfaces

- `pyproject.toml` and `uv.lock`
- `src/localbrain/markdown.py`
- a new source-scoped resolver module under `src/localbrain/`
- a small resolver-context adapter in `src/localbrain/contexts.py`
- [Markdown Rendering Contract](../../policies/project/markdown-rendering.md)
- synthetic Markdown and resolver tests under `tests/`

## Surface Lanes

- Syntax extension:
  - path roots: dependency metadata, shared renderer, Markdown owner policy, syntax tests
  - dependency order: first
  - responsibility: token allowlist, properties, anchors, MathML, safe generated HTML, baseline regression
  - evaluator ownership: `contract`, `functional`
- Local reference:
  - path roots: resolver module, `contexts.py` adapter, link and embed tests
  - dependency order: after syntax extension
  - responsibility: one-source containment, deterministic lookup, no-source and ambiguity states, route identity, fragments, recursion and cycle bounds
  - evaluator ownership: `contract`, `functional`

## State And Interaction Contract

- Resolved internal link: normal anchor to `/documents/{id}` plus an optional verified fragment.
- External link: activation-only HTTP or HTTPS anchor identified as external; no prefetch or embed behavior.
- No source, missing, ambiguous, or unsafe link: readable non-anchor output with an explicit state class and `data-reference-state`.
- Eligible note embed: semantic nested article with source identity and bounded recursively rendered content.
- Missing, ambiguous, unsafe, cyclic, or depth-limited note embed: readable bounded placeholder that does not hide parent content.
- Attachment embed: deferred non-fetching marker regardless of local-looking or remote-looking target.
- Valid properties: immutable ordered result metadata; not part of body HTML.
- Invalid properties: safe readable body content and empty property metadata.
- Comment: omitted from rendered output while the authoritative source remains unchanged.

## Data And Contract Assumptions

- Enabled FOLDERS roots remain non-overlapping and `context_documents.path` remains unique.
- A reference context contains Documents from one and only one `context_root_id`; construction rejects mixed-root collections.
- `relative_path` values are source-relative POSIX paths and resolver normalization never touches the filesystem.
- A Document route ID is the only generated internal destination identity; source paths never appear in an `href`.
- Rendered HTML, MathML, properties, resolution output, and embedded output remain derived and unpersisted.
- All source bodies and link graphs used in tests are synthetic.

## Contract Surfaces

- Producer expectations: downstream Local Context consumers provide a resolver context built for the selected indexed Document; Session and Subsession consumers omit it.
- Consumer expectations: consumers render the shared result and do not add a second wikilink parser, path resolver, math engine, or plugin runtime.
- Route contract: resolved internal links target current LocalBrain `/documents/{id}` routes with verified stable fragments.
- Source-of-truth contract: source body and indexed Document rows remain authoritative; properties and embedded output are derived views.
- Stale-assumption check: search for page-local relative-link handling, global title lookup, raw `file:` anchors, remote math or plugin assets, arbitrary `safe` filters, and recursive rendering without bounds.

## Required Evaluators

- Contract: verify syntax allowlist, immutable result compatibility, one-source resolver construction, route identity, link safety, dependency bounds, derived-output ownership, plugin boundary, recursion and cycle limits.
- Functional: exercise every named syntax and reference state, hostile paths and schemes, property and math failure, embeds, FEAT-0038 regression, full suite, privacy, and diff checks.
- Design and UX: not required because no visible consumer or browser interaction changes in this foundation Feature.

## Acceptance Mapping

- Obsidian authoring allowlist maps to deterministic syntax fixtures and no plugin execution path.
- Stable heading and block navigation maps to anchor extraction, duplicate suffixing, fragment verification, and internal route output.
- Root-contained resolution maps to one-root context validation, POSIX-only normalization, relative versus wiki lookup rules, and explicit no-source/missing/ambiguous/unsafe states.
- External navigation maps to HTTP/HTTPS-only activation anchors with no request-producing elements.
- Properties and math map to safe YAML metadata plus local MathML and fallback fixtures.
- Note embeds map to Markdown-only eligibility, selected section/block extraction, maximum depth three, visited-ID cycle guard, and bounded failure markers.
- Deferred attachments map to no `<img>`, `<iframe>`, `<object>`, `<video>`, `<audio>`, `src`, or local file access.

## Evaluation Focus

- Confirm mixed roots cannot enter one resolver and ambiguous pathless names never resolve by ordering.
- Confirm percent-decoding occurs before root-escape and scheme checks.
- Confirm generated internal destinations contain only LocalBrain route IDs and stable fragments.
- Confirm MathML is generated locally and hostile TeX cannot inject HTML or executable attributes.
- Confirm plugin-produced tokens do not re-enable arbitrary source HTML.
- Confirm nested renders carry the same source trust contract and terminate at cycles or depth three.
- Confirm all FEAT-0038 fixtures still pass unchanged.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-19`: Attempt 1 fixed a one-FOLDERS-root resolver, explicit ambiguous and no-source states, source-relative versus root-relative rules, local MathML, separate properties, and bounded Markdown-only note embeds.
- `2026-07-19`: Contract evaluation routed Attempt 1 to a targeted Fix after hostile TeX exposed an unvalidated non-MathML element in converter output; Attempt 2 retains the same approved boundary and requires an explicit MathML allowlist.
- `2026-07-19`: Attempt 2 passed after generated MathML validation and exact hostile regression coverage; no approved scope or resolution rule changed.
