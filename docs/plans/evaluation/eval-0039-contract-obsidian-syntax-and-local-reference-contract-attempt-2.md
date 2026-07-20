# EVAL-0039: Obsidian Syntax And Local Reference Contract — Contract Attempt 2

## Metadata

- ID: `eval-0039-contract-attempt-2`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260719-44`
- Attempt: `2`
- Feature: [feat-0039-obsidian-syntax-and-local-reference-contract](../feature/feat-0039-obsidian-syntax-and-local-reference-contract.md)
- Spec: [spec-0039-obsidian-syntax-and-local-reference-contract](../spec/spec-0039-obsidian-syntax-and-local-reference-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `syntax-extension`, `local-reference`
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Re-evaluated the Attempt 1 MathML finding and all approved syntax, source ownership, one-root reference, route identity, external-link, embed-bound, and plugin-boundary contracts.

## Checks And Evidence

- Generated MathML is parsed as XML and admitted only when every node belongs to the MathML namespace, every local element is in an explicit presentation allowlist, and every attribute is in an explicit non-fetching allowlist.
- The exact `\\text{<script>}` input now yields escaped TeX fallback without a `<script>` node; generated `href`, namespaced, event, style, source, malformed, foreign, or unknown output takes the same fail-closed route.
- Valid inline, fraction, square-root, and matrix inputs retain local MathML output and require no CDN, browser script, subprocess, or network request.
- `MarkdownRenderResult` remains immutable and backwards compatible while adding ordered derived properties and an optional reference context.
- Valid YAML mappings use safe loading and remain separate from body HTML; invalid mappings remain safe readable source.
- `MarkdownReferenceContext` rejects mixed roots and missing current Documents. Its database adapter admits only an enabled `source_type='folder'` root and includes only Documents with the same `context_root_id`.
- Relative Markdown paths resolve from the current Document directory; path-bearing wikilinks resolve from the source root; pathless names require exactly one title or basename match.
- Percent-decoded root escapes, absolute paths, and non-HTTP schemes fail closed. Internal destinations contain only `/documents/{id}` plus a verified generated fragment.
- HTTP and HTTPS links emit activation-only external anchors with `noopener noreferrer external`; no render path imports a network client or produces prefetch markup.
- Markdown note embeds enforce same-root resolution, Markdown content types, section or block selection, three-Document depth, visited-ID cycle protection, and deferred attachment output.
- No Obsidian executable, third-party plugin loader, raw source HTML path, persisted render output, or cross-source global lookup was introduced.

## Contract Evidence

- Producer surfaces: `markdown.py`, `markdown_references.py`, `contexts.py`, dependency metadata, and the Markdown Rendering owner policy.
- Consumer surfaces: shared trusted result contract plus synthetic Local Context, no-source Session-like, and nested Document fixtures.
- Artifacts checked: syntax rules, safe property extraction, MathML validator, anchor index, resolver context, FOLDERS adapter, note extraction, dependency lock, architecture map, and owner policy.
- Stale-assumption check: repository search found no alternative Markdown parser, remote math runtime, page-local path resolver, fetch-capable embed, or unvalidated generated-markup producer in FEAT-0039 scope.

## Evidence Gaps

- None. Visible page consumption remains explicitly owned by FEAT-0041 through FEAT-0043.

## Findings

- None. The blocking Attempt 1 implementation bug is fixed and directly covered.

## Regression Notes

- Dependency lock, focused 23-test suite, complete 163-test suite, privacy, and diff checks passed after the fix.

## Route

- Next action: `pass`.
