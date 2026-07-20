# EVAL-0038: Shared Markdown Rendering And Safety Contract — Contract

## Metadata

- ID: `eval-0038-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260719-43`
- Attempt: `1`
- Feature: [feat-0038-shared-markdown-rendering-and-safety-contract](../feature/feat-0038-shared-markdown-rendering-and-safety-contract.md)
- Spec: [spec-0038-shared-markdown-rendering-and-safety-contract](../spec/spec-0038-shared-markdown-rendering-and-safety-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `renderer-contract`
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated only the shared renderer result shape, source-of-truth ownership, dependency bounds, baseline syntax, trust boundary, explicit highlighting allowlist, image deferral, and bounded fallback required by FEAT-0038 and SPEC-0038.

## Checks And Evidence

- `src/localbrain/markdown.py` is the sole producer and exposes one immutable `MarkdownRenderResult` plus one `render_markdown(source)` entry point without importing routes, templates, Sessions, Documents, or page layout.
- `docs/policies/project/markdown-rendering.md` owns the durable baseline and identifies source text as authoritative while rendered HTML remains ephemeral and unindexed.
- `markdown-it-py>=3,<4` and `Pygments>=2.17,<3` are declared and locked; `uv lock --check` resolved the dependency graph without changes.
- CommonMark HTML is disabled, unsafe Markdown protocols remain inert text, and every LocalBrain-owned interpolation path escapes labels, alternative text, code, and fallback source.
- Highlighting selects only the explicit local alias map, produces class-based output without inline styles, and uses escaped generic code for missing, unknown, or failed lexers.
- Standard Markdown images produce a non-fetching deferred span without `<img>`, `src`, filesystem access, or network access.
- The result contract distinguishes `ready`, `empty`, and full-render `fallback`; fence-level highlighting failure stays bounded to generic code.
- A stale-assumption search found no page consumer, second Markdown parser, persisted-rendered-HTML path, template `safe` filter, external highlighting asset, or fetch-capable image output introduced by this Feature.

## Contract Evidence

- Producer surfaces: `src/localbrain/markdown.py`, `pyproject.toml`, and `uv.lock`.
- Consumer surfaces: synthetic renderer tests and the future-consumer boundary documented in the Markdown owner policy; no visible consumer opts in during this foundation Feature.
- Artifacts checked: immutable result type, parser configuration, language alias map, image renderer, fallback renderer, dependency lock, architecture package map, and Markdown owner policy.
- Stale-assumption check: repository search for `render_markdown`, renderer result ownership, image deferral, dependency use, and unsafe consumer patterns found no conflicting implementation.

## Evidence Gaps

- None. Visible template consumption and Obsidian reference behavior are explicitly owned by later PRD-0006 Features.

## Findings

- None.

## Regression Notes

- Dependency lock, diff whitespace, privacy, focused renderer tests, and the complete repository suite passed.

## Route

- Next action: `pass`.
