# EVAL-0038: Shared Markdown Rendering And Safety Contract — Functional

## Metadata

- ID: `eval-0038-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260719-43`
- Attempt: `1`
- Feature: [feat-0038-shared-markdown-rendering-and-safety-contract](../feature/feat-0038-shared-markdown-rendering-and-safety-contract.md)
- Spec: [spec-0038-shared-markdown-rendering-and-safety-contract](../spec/spec-0038-shared-markdown-rendering-and-safety-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `runtime-verification`
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated baseline Markdown output, hostile input containment, local highlighting and fallback behavior, image deferral, empty and forced-failure states, source preservation, and repository regressions.

## Checks And Evidence

- Ten synthetic renderer tests passed for empty input; baseline headings, paragraphs, line breaks, emphasis, lists, blockquotes, inline and fenced code, links, tables, and horizontal rules; hostile HTML and protocols; two deferred images; supported and unknown languages; forced highlighter and renderer failure; Unicode; immutable source; and invalid input type.
- Direct adversarial probes rendered raw script-shaped HTML as escaped text, left a `javascript:` Markdown link inert, replaced a remote image with a non-fetching deferred marker, and escaped unknown-language code.
- A supported Python fence produced only local Pygments class markup; a forced highlighter failure retained escaped readable code without failing the document.
- An empty string returned `state=empty`; a forced renderer exception returned the complete escaped source with `state=fallback`.
- The complete repository suite passed 152 tests after the dependency and renderer changes.
- Repository privacy passed 428 candidate files, `git diff --check` passed, and the locked environment reported `markdown-it-py 3.0.0` and `Pygments 2.20.0`.

## Evidence Gaps

- None. Browser rendering is not an acceptance surface for this non-visible foundation Feature.

## Findings

- None.

## Regression Notes

- Existing application startup, ingestion, retrieval, database, task-runner, and server-rendered route tests remained green. No source body, schema, template, or browser asset was changed.

## Route

- Next action: `pass`.
