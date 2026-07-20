# EVAL-0039: Obsidian Syntax And Local Reference Contract — Contract Attempt 1

## Metadata

- ID: `eval-0039-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `FAIL`
- Run ID: `run-20260719-44`
- Attempt: `1`
- Feature: [feat-0039-obsidian-syntax-and-local-reference-contract](../feature/feat-0039-obsidian-syntax-and-local-reference-contract.md)
- Spec: [spec-0039-obsidian-syntax-and-local-reference-contract](../spec/spec-0039-obsidian-syntax-and-local-reference-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `syntax-extension`
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated the approved syntax extension trust boundary, with emphasis on generated MathML because it becomes trusted derived markup.

## Checks And Evidence

- Dependency bounds, HTML-disabled Markdown, source-scoped links, attachment deferral, one-root resolver construction, and bounded note recursion matched SPEC-0039 in source inspection and focused tests.
- A direct hostile TeX probe rendered `\\text{<script>}` through `latex2mathml`; the converter returned a literal `<script>` child inside trusted MathML output.
- The source parser's HTML-disabled rule did not protect this path because the markup was generated after Markdown parsing and inserted as trusted renderer output.

## Contract Evidence

- Producer surfaces: `src/localbrain/markdown.py` local MathML callback and `latex2mathml 3.78.1` output.
- Consumer surfaces: shared trusted `MarkdownRenderResult.html` for all later Local Context, Document, and Session consumers.
- Artifacts checked: dependency lock, renderer callback, hostile runtime output, and FEAT-0038 safety contract.
- Stale-assumption check: the implementation assumed library-generated MathML was safe without validating its element or attribute vocabulary.

## Evidence Gaps

- None for the blocking finding.

## Findings

- Severity: blocking.
- Classification: `implementation bug`.
- Description: hostile TeX can introduce a non-MathML `<script>` element into trusted derived output.
- Evidence: direct render output contained `<mtext><script></mtext>`.
- Fix hint: parse generated XML, accept only an explicit MathML presentation element and attribute allowlist, and fall back to escaped TeX whenever validation fails.

## Regression Notes

- The focused 23-test and full 163-test suites passed before this direct hostile probe, showing the missing adversarial fixture rather than a test-reported failure.

## Route

- Next action: `fix`.
