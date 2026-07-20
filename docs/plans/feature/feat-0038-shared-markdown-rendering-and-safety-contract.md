# FEAT-0038: Shared Markdown Rendering And Safety Contract

## Metadata

- ID: `feat-0038`
- Status: `passed`
- Type: `foundation`
- Surface: `fullstack`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Establish one source-preserving, local-only Markdown rendering and safety contract that downstream Local Context, Document, and Session Features can consume without independently choosing syntax, trust, highlighting, or fallback behavior.

## Acceptance Contract

- One shared renderer owns plain text, CommonMark, and GitHub Flavored Markdown presentation for every downstream consumer.
- Rendering never rewrites the authoritative Document or Session body.
- Headings, paragraphs and line breaks, emphasis, lists, blockquotes, inline code, fenced code with optional language labels, links, basic pipe tables, and horizontal rules produce deterministic safe output.
- Raw HTML, script-shaped input, event handlers, executable protocols, and unsafe URL schemes cannot execute through rendered output.
- Syntax highlighting uses only local code and assets, supports an explicit language allowlist, and falls back to readable generic code when a grammar is absent or fails.
- Standard Markdown images remain deferred and cannot cause network or filesystem access through this contract.
- Empty, malformed, unsupported, and renderer-failure inputs have deterministic safe states that retain access to readable source text when possible.
- The renderer result and trust boundary are reusable without importing page-specific layout, role, source-tree, or navigation assumptions.

## Scope Boundary

- In:
  - shared renderer ownership and reusable input/output contract
  - CommonMark and GitHub Flavored Markdown baseline syntax
  - source-body immutability
  - raw-HTML and unsafe-link handling
  - local-only code highlighting, language allowlist, and generic fallback
  - image-syntax deferral without automatic loading
  - empty, malformed, unsupported, and failure behavior
  - synthetic contract fixtures for supported and hostile inputs
- Out:
  - Obsidian-specific syntax, source-relative resolution, wikilinks, properties, math, or note embeds owned by FEAT-0039
  - page-specific typography, CSS, responsive layout, source tree, conversation cards, or navigation
  - Markdown images or attachment rendering
  - external renderers, CDNs, fonts, highlighting assets, AI services, or network enrichment
  - editing or rewriting source content

## Surface Lanes

- Renderer contract lane:
  - path roots: shared Markdown owner module under `src/localbrain/`, dependency declaration when required, and the durable owner documentation selected by the Spec
  - dependencies: approved PRD-0006 syntax and safety boundary
  - expected evidence: one explicit input/output shape, syntax allowlist, source-immutability rule, trust boundary, and deterministic fallback model
  - evaluator ownership: `contract`
- Runtime verification lane:
  - path roots: shared renderer tests under `tests/`
  - dependencies: renderer contract lane
  - expected evidence: safe deterministic output for representative plain, Markdown, code, table, malformed, hostile, image, empty, and unknown-language fixtures
  - evaluator ownership: `functional`

## Contract Surfaces

- Shared Markdown renderer entry and result shape.
- Supported CommonMark and GitHub Flavored Markdown allowlist.
- Authoritative source input versus derived rendered output ownership.
- Raw HTML, protocol, attribute, and escaping or sanitization policy.
- Local syntax-highlighting language selection and generic fallback.
- Image deferral, empty input, malformed input, and render-failure states.

## Required Evaluators

- `contract`: shared ownership, supported syntax, derived-output status, trust boundary, fallback, highlighting, and downstream-consumer readiness.
- `functional`: deterministic rendering, hostile-input containment, source preservation, local-only behavior, image deferral, and generic fallbacks.

## Entry And Exit

- Entry point: a downstream consumer submits authoritative plain or Markdown-shaped text and bounded rendering context.
- Exit or transition behavior: the renderer returns deterministic safe derived output or a bounded fallback without mutating the input or initiating external access.

## State Expectations

- Default: valid plain text or supported Markdown returns safe structured output.
- Empty: empty input returns a neutral empty result rather than fabricated content.
- Unsupported: unsupported syntax remains safe and understandable without execution.
- Error: parser or highlighter failure produces a readable generic fallback and an inspectable local failure state without exposing source content in logs by default.
- Success: consumers receive one reusable result governed by the same syntax and safety contract.

## Dependencies

- PRD-0006 must remain `approved` with its syntax, safety, image-deferral, and local-only boundaries unchanged.

## Likely Affected Surfaces

- a shared renderer module under `src/localbrain/`
- `pyproject.toml` and the lockfile only if approved local runtime packages are required
- durable Markdown rendering owner documentation under `docs/policies/`
- synthetic renderer and safety tests under `tests/`

## Pass Or Fail Checks

- Pass if one documented renderer contract covers every confirmed baseline syntax type and plain text.
- Pass if representative raw HTML, event attributes, script-shaped input, unsafe schemes, and malformed links cannot execute.
- Pass if source text remains unchanged before and after every render path.
- Pass if supported code uses only local highlighting and unknown or failed languages retain readable generic code.
- Pass if standard image syntax performs no filesystem or network loading and has a deterministic deferred presentation result.
- Pass if empty, malformed, unsupported, and forced-failure fixtures return bounded results without crashing consumers.
- Fail if downstream Features must choose their own sanitizer, baseline syntax, trust policy, highlighting fallback, or image behavior.

## Regression Surfaces

- authoritative `context_documents.body` and Activity Event message text
- existing plain-text rendering expectations before downstream consumers opt in
- application startup without network access
- privacy-safe logging and tracked synthetic fixtures

## Harness Trace

- Active spec doc: [spec-0038-shared-markdown-rendering-and-safety-contract](../spec/spec-0038-shared-markdown-rendering-and-safety-contract.md)
- Active run: [run-20260719-43-shared-markdown-rendering-and-safety-contract](../run/run-20260719-43-shared-markdown-rendering-and-safety-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [contract](../evaluation/eval-0038-contract-shared-markdown-rendering-and-safety-contract.md), [functional](../evaluation/eval-0038-functional-shared-markdown-rendering-and-safety-contract.md)
- Latest fix note:

## Continuity Notes

- `2026-07-19`: initial draft split the common renderer, trust boundary, highlighting, and fallback contract from Obsidian reference resolution and from all visible consumer Features.
- `2026-07-19`: the human owner approved sequential PRD-0006 execution; FEAT-0038 entered `run-20260719-43` first under the `foundation-contract` profile.
- `2026-07-19`: Attempt 1 passed Contract and Functional evaluation with complete evidence; the shared safe renderer is ready for FEAT-0039 and visible consumers.
