# FEAT-0039: Obsidian Syntax And Local Reference Contract

## Metadata

- ID: `feat-0039`
- Status: `passed`
- Type: `foundation`
- Surface: `fullstack`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Extend the shared renderer with one bounded Obsidian-compatible authoring and Local Context reference contract so every visible consumer resolves syntax, links, properties, math, and note embeds consistently without running Obsidian or third-party plugins.

## Acceptance Contract

- The shared renderer supports nested and read-only task lists, strikethrough, highlight, footnotes, hidden comments, wikilinks with aliases and source-local paths, heading and block references, callouts, tags, valid YAML properties, inline and block math, and Markdown note embeds.
- Same-document heading and block references target stable rendered anchors.
- Relative Markdown links and wikilinks resolve only to indexed Documents inside the owning Local Context source.
- Unresolved or ambiguous internal references remain visibly unavailable and do not guess, create, edit, or globally match a Document.
- A consumer without an owning Local Context source, including Session and Subsession messages, keeps source-local references readable but unresolved.
- HTTP and HTTPS links require user activation, receive explicit external-link output, and never prefetch or embed a destination.
- Root-escaping paths, `file` targets, executable protocols, and unsafe schemes remain disabled.
- Markdown note embeds resolve only to eligible Markdown Documents inside the owning source and use deterministic recursion, cycle, missing-target, and failure limits.
- Image and non-Markdown attachment embeds remain deferred and never initiate remote or local attachment loading.
- Plugin code is never loaded or executed; a named third-party plugin syntax requires a later allowlist extension.

## Scope Boundary

- In:
  - approved Obsidian Flavored Markdown authoring allowlist
  - heading and block anchor identity
  - source-scoped Markdown link and wikilink resolution
  - unresolved, ambiguous, external, unsafe, and root-escaping reference behavior
  - valid YAML property separation from body content
  - local inline and block math rendering
  - source-contained Markdown note embeds with finite recursion and cycle protection
  - explicit no-owning-source behavior for Session and Subsession consumers
  - synthetic link graphs and hostile path fixtures
- Out:
  - Obsidian vault integration, backlink indexing, graph view, editor, command palette, or note creation
  - installation or execution of Obsidian or third-party plugins
  - arbitrary unnamed plugin syntax
  - standard images, image embeds, PDFs, audio, video, canvas, or other attachment rendering
  - external network requests or remote embeds
  - page-specific visual composition owned by downstream product Features

## Surface Lanes

- Syntax-extension lane:
  - path roots: shared Markdown owner module and its durable syntax contract documentation
  - dependencies: FEAT-0038 renderer and safety result
  - expected evidence: deterministic output for every approved Obsidian construct without changing the baseline trust contract
  - evaluator ownership: `contract`, `functional`
- Local-reference lane:
  - path roots: Local Context Document lookup or resolver boundary under `src/localbrain/` and synthetic resolver tests
  - dependencies: non-overlapping FOLDERS roots, unique Document paths, and syntax-extension lane
  - expected evidence: source-contained resolution, stable anchors, no-source and unresolved behavior, external-link policy, and embed depth or cycle containment
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- Obsidian syntax allowlist and explicit third-party extension boundary.
- Rendered heading and block anchor identity.
- Owning Local Context source supplied to the reference resolver.
- Relative Markdown, wikilink, alias, unresolved, external, unsafe, and root-escape outcomes.
- Property, math, comment, tag, callout, task, footnote, and highlight output roles.
- Markdown note-embed target eligibility, recursion, cycle, missing, and failure states.
- Image and attachment deferral inherited from FEAT-0038.

## Required Evaluators

- `contract`: syntax allowlist, source ownership, target identity, link safety, no-source behavior, embed bounds, and plugin boundary.
- `functional`: representative syntax, valid and invalid targets, duplicate names, heading and block navigation, root escape, external links, embed cycles, depth limits, missing targets, and image deferral.

## Entry And Exit

- Entry point: the FEAT-0038 renderer receives text plus an optional owning Local Context source and current Document identity.
- Exit or transition behavior: supported syntax becomes safe structured output with deterministic LocalBrain destinations or an explicit unresolved or deferred result.

## State Expectations

- Default: supported Obsidian syntax renders without requiring Obsidian.
- No owning source: source-relative references remain readable and unresolved.
- Missing or ambiguous: the reference is visibly unavailable without target guessing or creation.
- Unsafe: the target is disabled and cannot escape its approved source or execute a protocol.
- Embed cycle or limit: the nested render stops at a bounded fallback without hiding the parent content.
- Success: eligible internal references resolve to stable LocalBrain Document and anchor identities.

## Dependencies

- FEAT-0038 must be `passed` before this Feature enters build.
- The current non-overlapping enabled FOLDERS-root and unique `context_documents.path` contracts remain unchanged.

## Likely Affected Surfaces

- the shared renderer established by FEAT-0038
- Local Context Document lookup or resolver code under `src/localbrain/`
- durable Markdown syntax and link owner documentation under `docs/policies/`
- synthetic Obsidian syntax, link graph, property, math, and note-embed tests under `tests/`

## Pass Or Fail Checks

- Pass if every approved Obsidian construct has deterministic output and source preservation.
- Pass if same-document headings and blocks, source-contained relative links, wikilinks, and aliases resolve to stable targets.
- Pass if unresolved, ambiguous, no-source, root-escaping, `file`, executable, and unsafe references never guess, create, or execute a target.
- Pass if HTTP and HTTPS links require activation and produce no prefetch or embed request.
- Pass if valid Markdown note embeds render within finite limits and cycles, missing targets, images, and attachments end in bounded states.
- Pass if properties remain separate from body content, comments stay hidden, and local math has no external dependency.
- Fail if any consumer needs its own Obsidian parser, reference resolver, plugin behavior, or link-safety rule.

## Regression Surfaces

- FEAT-0038 baseline syntax, sanitizer, source preservation, highlighting, image deferral, and fallback
- Local Context root containment and unique Document identity
- Session or Subsession content without an owning Local Context source
- direct Document routes and browser-safe external navigation

## Harness Trace

- Active spec doc: [spec-0039-obsidian-syntax-and-local-reference-contract](../spec/spec-0039-obsidian-syntax-and-local-reference-contract.md)
- Active run: [run-20260719-44-obsidian-syntax-and-local-reference-contract](../run/run-20260719-44-obsidian-syntax-and-local-reference-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [Contract Attempt 2 — PASS](../evaluation/eval-0039-contract-obsidian-syntax-and-local-reference-contract-attempt-2.md), [Functional Attempt 2 — PASS](../evaluation/eval-0039-functional-obsidian-syntax-and-local-reference-contract.md)
- Latest fix note: [MathML trust boundary](../fix/fix-0039-mathml-trust-boundary.md)

## Continuity Notes

- `2026-07-19`: initial draft separated Obsidian syntax and Local Context reference semantics from the baseline renderer so downstream visible Features do not invent per-screen link or embed behavior.
- `2026-07-19`: FEAT-0038 passed and the owner-authorized sequential workflow activated FEAT-0039 as `run-20260719-44`.
- `2026-07-19`: Attempt 1 exposed an unvalidated MathML element; the targeted Fix added an explicit MathML allowlist and Attempt 2 passed Contract and Functional evaluation with complete evidence.
