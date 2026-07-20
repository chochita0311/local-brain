# SPEC-0038: Shared Markdown Rendering And Safety Contract

## Metadata

- ID: `spec-0038`
- Status: `passed`
- Run ID: `run-20260719-43`
- Attempt: `1`
- Parent Feature: [feat-0038-shared-markdown-rendering-and-safety-contract](../feature/feat-0038-shared-markdown-rendering-and-safety-contract.md)
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Surface: `fullstack`
- Execution Profile: `foundation-contract`
- Surface Lane: `renderer-contract`, then `runtime-verification`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Source Set

- Human request: execute the approved PRD-0006 Features sequentially.
- Parent Feature: FEAT-0038 shared renderer, trust, highlighting, image-deferral, and fallback boundary.
- Parent PRD: PRD-0006 CommonMark and GitHub Flavored Markdown reading baseline, local-only behavior, source preservation, and deferred images.
- Golden sources: official `markdown-it-py` usage and security guidance, official Pygments library guidance, and current LocalBrain plain-text consumers.
- Relevant policies or contracts: Privacy And Data Handling, Product Model, Project Architecture, Design Constitution technical-content roles, PRD And Feature Management, and Execution Loop Governance.

## Implementation Goal

- Add one reusable Python renderer that turns an authoritative string into safe derived HTML and an explicit render state without page-specific layout assumptions, source mutation, filesystem reads, or network access.

## In-Scope Behavior

- Add `markdown-it-py>=3,<4` to retain the repository's Python `>=3.9` contract.
- Add `Pygments>=2.17,<3` for local syntax highlighting.
- Provide an immutable `MarkdownRenderResult` with:
  - trusted derived `html` suitable for Jinja consumption without page-local `safe` filters
  - `state` limited to `ready`, `empty`, or `fallback`
- Provide `render_markdown(source)` as the shared entry point.
- Configure the parser from the `commonmark` preset with:
  - source HTML disabled
  - automatic linkification disabled
  - typographic substitution disabled
  - visible soft line breaks enabled to preserve the current technical-note reading expectation
  - the core table rule enabled
- Preserve core headings, paragraphs, emphasis, strong emphasis, ordered and unordered lists including nesting, blockquotes, inline code, fenced code, Markdown links, tables, and horizontal rules.
- Replace every standard Markdown image token with a non-fetching deferred marker containing only escaped, readable alternative text; never emit `<img>` in this Feature.
- Highlight only an explicit local alias allowlist covering shell, Python, JavaScript, TypeScript, JSON, YAML, SQL, HTML, CSS, Markdown, and diff families.
- Render missing, text-like, unknown, or failed language labels as escaped generic code while retaining a readable normalized label when present.
- Use Pygments class output without inline styles and keep the style system outside this foundation Feature.
- Catch renderer-level failure and return an escaped `<pre>` fallback for the full source with `state=fallback`.
- Return empty trusted HTML with `state=empty` for empty input without fabricating body copy.
- Document the durable baseline contract in `docs/policies/project/markdown-rendering.md` for FEAT-0039 and visible consumers to extend.
- Add synthetic tests for every supported baseline block, HTML escaping, unsafe schemes, standard image deferral, highlighting, unknown language, forced highlighter failure, forced renderer failure, empty input, Unicode, and source preservation.

## Out-Of-Scope Behavior

- Obsidian-specific syntax, wikilinks, reference resolution, properties, math, footnotes, callouts, tasks, or note embeds.
- Any visible page or template integration, CSS, code-copy control, editor, outline, or navigation behavior.
- Standard Markdown image rendering, attachment access, remote fetching, or local path resolution.
- External sanitizer, renderer, CDN, font, highlighter asset, browser script, or AI service.
- Persisting rendered HTML or changing Document, Session, Activity Event, search, or schema ownership.
- Guessing a lexer outside the explicit alias allowlist.

## Affected Surfaces

- `pyproject.toml`
- `uv.lock`
- new shared renderer module under `src/localbrain/`
- new [Markdown Rendering Contract](../../policies/project/markdown-rendering.md)
- new synthetic renderer contract tests under `tests/`

## Surface Lanes

- Renderer contract:
  - path roots: `pyproject.toml`, `uv.lock`, shared renderer module, Markdown owner policy
  - dependency order: first
  - implementation responsibility: dependency bounds, result shape, parser configuration, safe render rules, highlight allowlist, deferred image output, and fallback ownership
  - validation evidence: direct contract tests and dependency metadata
- Runtime verification:
  - path roots: renderer tests under `tests/`
  - dependency order: after renderer contract
  - implementation responsibility: exercise supported, hostile, malformed, deferred, error, empty, and immutable-source cases
  - validation evidence: targeted unittest command followed by the full suite and privacy check

## State And Interaction Contract

- `ready`: non-empty source completed through the configured renderer, including documents containing unsupported syntax that remains safe text.
- `empty`: the source is empty and the result contains no invented copy.
- `fallback`: an internal parser or renderer failure occurred and the complete source is HTML-escaped inside one bounded fallback block.
- A fenced-code highlight failure is local to that fence and uses generic code; it does not change the whole result to `fallback`.
- Standard Markdown image syntax is a `ready` render containing a deferred marker, never a load attempt.
- Rendering has no interaction, persistence, file-read, or network side effect.

## Data And Contract Assumptions

- Input is a Python `str`; empty string is valid.
- The input string and every authoritative database or source record remain unchanged.
- `MarkdownRenderResult.html` is the only trusted derived value. Source text must never be marked trusted.
- All generated tags and attributes come from the renderer or LocalBrain-owned rules; user-provided HTML remains escaped text.
- Markdown-it link validation remains a baseline guard; FEAT-0039 owns the stricter internal and external navigation contract before visible consumers ship.
- No rendered output is persisted or indexed.

## Contract Surfaces

- Producer expectations:
  - consumers provide authoritative text only and do not pre-mark it as trusted HTML
  - later FEAT-0039 may supply bounded rendering context without changing this result ownership
- Consumer expectations:
  - consumers branch on `state` only for their own empty or fallback presentation
  - consumers render only the returned trusted `html` and never apply a second Markdown parser
- Generated artifacts:
  - HTML is derived, ephemeral, safe-by-contract presentation output
  - Pygments CSS is not generated or committed in this Feature
- Source-of-truth owner:
  - original Document or Activity Event text remains authoritative
  - `docs/policies/project/markdown-rendering.md` owns the durable supported baseline and safety rule
- Stale-assumption check:
  - search for page-local Markdown renderers, unsafe filters, `<img>` output, raw HTML enablement, external highlighting assets, and consumers that might persist output

## Required Evaluators

- Contract:
  - verify result shape, source ownership, dependency bounds, parser configuration, trust policy, allowlists, deferral, fallback, and owner documentation
- Design:
  - not required because no visible consumer or CSS is changed
- Functional:
  - execute targeted and full tests for baseline rendering, hostile inputs, highlighting, failures, images, empty state, Unicode, and unchanged source
- UX heuristic:
  - not required because no interactive surface is changed

## Acceptance Mapping

- Shared renderer ownership maps to one module, one result type, one entry function, and one policy owner.
- Baseline syntax maps to parser fixtures covering every confirmed block and inline type.
- Source preservation maps to immutable-string and no-persistence tests.
- HTML and link safety maps to hostile HTML, attribute, and protocol fixtures with no executable output.
- Local highlighting maps to explicit aliases, Pygments class output, no inline styles, and generic unknown or failure fallback.
- Image deferral maps to representative standard image inputs with no `<img>`, source path read, or network behavior.
- Empty and renderer failure map to explicit `empty` and `fallback` results.
- Reusability maps to no import from templates, routes, Session, Context, or Document presentation modules.

## Evaluation Focus

- Confirm `commonmark` is not used with its unsafe default HTML behavior.
- Confirm every interpolated language label, alt text, and fallback source is escaped.
- Confirm highlighted output is produced only for the explicit alias allowlist and never through automatic lexer guessing.
- Confirm the image renderer cannot emit a fetch-capable element.
- Confirm exceptions do not leak raw source into logs and do not partially mark source as trusted.
- Confirm the repository still supports Python 3.9 through dependency bounds.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-19`: Attempt 1 Spec selected safe-by-default `markdown-it-py` configuration, explicit local Pygments aliases, non-fetching image deferral, and an immutable derived result without visible consumer work.
- `2026-07-19`: Attempt 1 implementation passed focused and full regression tests plus complete Contract and Functional evaluation.
