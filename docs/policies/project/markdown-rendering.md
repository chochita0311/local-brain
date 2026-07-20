# Markdown Rendering Contract

## Purpose

- Own LocalBrain's durable baseline for turning authoritative Markdown-shaped text into safe, ephemeral browser presentation.
- Keep syntax, trust, highlighting, deferral, and fallback behavior consistent across Local Context, Document, Session, and Subsession consumers.

## Ownership

- `src/localbrain/markdown.py` owns the shared renderer implementation.
- Authoritative Document and Activity Event text remains owned by its source record and is never replaced by rendered HTML.
- Rendered HTML is derived runtime presentation. It is not persisted, indexed, or treated as source evidence.
- PRD-0006 and its Features may extend the allowlist, but consumers must not create page-local Markdown parsers or trust rules.

## Baseline Syntax

The shared baseline uses CommonMark parsing with selected GitHub Flavored Markdown behavior:

- headings
- paragraphs and visible source line breaks
- emphasis and strong emphasis
- ordered, unordered, and nested lists
- blockquotes
- inline code
- fenced code blocks with optional language labels
- Markdown links
- basic pipe tables
- horizontal rules

The approved Obsidian-compatible extension adds:

- disabled task checkboxes and nested task lists
- strikethrough, highlight, footnotes, hidden comments, tags, and callouts
- deterministic heading and explicit block anchors
- YAML mapping properties separated from body HTML
- local inline and block MathML with an escaped TeX fallback
- wikilinks, aliases, source-local Markdown links, and Markdown note embeds

This is an explicit LocalBrain syntax allowlist. Obsidian and third-party plugin code is never loaded or executed; a new plugin-specific syntax requires its own reviewed allowlist extension.

## Trust And Source Contract

- Source HTML is disabled and remains escaped text.
- Script-shaped markup, event-handler attributes, executable protocols, `file` links, and unsafe schemes cannot become executable browser output.
- Only LocalBrain-owned renderer rules may produce trusted markup.
- The renderer accepts a string and returns an immutable result containing trusted derived HTML, ordered derived properties, and one state: `ready`, `empty`, or `fallback`.
- An empty string produces empty trusted output without invented body copy.
- A renderer-level failure produces the complete escaped source in a bounded fallback block.
- The renderer does not read a file, open a URL, send a network request, update a source record, or log the body by default.

## Code Highlighting

- Pygments runs locally for an explicit allowlist covering shell, Python, JavaScript, TypeScript, JSON, YAML, SQL, HTML, CSS, Markdown, and diff families.
- Lexer guessing is disabled.
- Missing, text-like, unknown, or failed language handling uses escaped generic code.
- Generated highlighting uses classes rather than inline style values; visible consumer Features own the Design Constitution-compatible presentation.
- Markdown reading uses its own calm dark-surface and syntax-text roles. It does not reuse the near-black Run console surface or status and brand colors as syntax semantics.

## Image Deferral

- Standard Markdown image syntax does not emit an `<img>` element.
- The renderer emits a non-fetching deferred marker with escaped alternative text.
- Local files, remote URLs, and attachments are not resolved or loaded through the baseline renderer.
- Safe image and attachment rendering remains the tracked follow-up under `docs/plans/project/backlog.md#markdown-image-and-attachment-rendering`.

## Local Reference Contract

- Source-local resolution is optional and available only when the consumer supplies one immutable context built from a selected indexed Document and exactly one enabled FOLDERS `context_root_id`.
- Sessions, Subsessions, standalone file sources, and Apple Notes omit this context; their relative links and wikilinks remain readable and explicitly unresolved.
- Standard relative Markdown paths start from the current Document directory. Path-bearing wikilinks start from the owning source root. Pathless wikilinks resolve only when exactly one title or basename stem matches inside that source.
- Absolute paths, root escapes after percent-decoding and normalization, `file:`, `obsidian:`, executable protocols, and schemes other than HTTP or HTTPS are disabled.
- Resolved internal links expose only `/documents/{id}` plus a verified stable heading or block fragment; source filesystem paths do not enter `href` output.
- HTTP and HTTPS links remain activation-only external anchors with `noopener`, `noreferrer`, and `external` relationships. Rendering never fetches or prefetches them.
- Heading anchors use normalized `heading-*` IDs with deterministic duplicate suffixes. Explicit block anchors use normalized `block-*` IDs.

## Properties, Math, And Note Embeds

- Only a valid leading YAML mapping becomes result properties. Invalid or non-mapping front matter stays safe readable body source.
- YAML parsing uses safe loading, performs no object construction outside supported safe types, and never changes the authoritative body.
- TeX-shaped math is converted locally to MathML without a browser CDN, font request, subprocess, or executable TeX. Conversion failure retains escaped source notation.
- A note embed may resolve only to an indexed Markdown Document in the same FOLDERS source.
- Heading embeds stop at the next heading of equal or higher level; block embeds select the line carrying the explicit block ID.
- Nested note rendering stops after three embedded Documents and tracks visited Document IDs to stop cycles.
- Missing, ambiguous, unsafe, cyclic, depth-limited, image, and non-Markdown attachment embeds return bounded readable states without filesystem or network access.

## Consumer Contract

- Consumers pass authoritative text to `render_markdown` and render only its trusted result.
- Visible readers use the shared `.markdown-body` semantic class for prose, headings, code, tables, callouts, footnotes, math, references, embeds, and deferred states; page containers own only composition and scrolling.
- The renderer owns a non-semantic table scroll wrapper so tables retain native table layout, fill the available reading width, and overflow locally when their minimum column geometry exceeds it.
- Consumers may provide page-owned empty or failure copy from the returned state, but they must not reparse the output or mark source text as trusted.
- Consumer CSS may style shared semantic classes under the Design Constitution but must not change syntax, trust, source, or fallback meaning.
- Unsupported syntax stays safe and understandable until an approved Feature extends this allowlist.

## Verification Contract

- Tracked fixtures use synthetic content.
- Contract tests cover every supported baseline and Obsidian-compatible type, raw HTML, unsafe and external links, one-source containment, missing and ambiguous references, root escape, stable fragments, deferred images and attachments, known and unknown languages, local MathML and failure, properties, note embed selection and bounds, renderer failure, empty input, Unicode, and unchanged source.
- Dependency bounds retain the project's declared Python compatibility.
