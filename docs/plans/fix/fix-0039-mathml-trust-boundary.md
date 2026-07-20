# FIX-0039: MathML Trust Boundary

## Metadata

- ID: `fix-0039-mathml-trust-boundary`
- Status: `complete`
- Run ID: `run-20260719-44`
- Attempt: `2`
- Feature: [feat-0039-obsidian-syntax-and-local-reference-contract](../feature/feat-0039-obsidian-syntax-and-local-reference-contract.md)
- Spec: [spec-0039-obsidian-syntax-and-local-reference-contract](../spec/spec-0039-obsidian-syntax-and-local-reference-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `syntax-extension`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Input Reports

- [Contract evaluation Attempt 1](../evaluation/eval-0039-contract-obsidian-syntax-and-local-reference-contract.md) found a blocking generated-Markup trust defect.

## Fix Scope

- Validate locally generated MathML before it enters trusted renderer output.
- Accept only an explicit presentation MathML element and non-fetching attribute vocabulary.
- Fall back to escaped TeX for malformed XML, foreign or unknown elements, namespaced foreign attributes, event attributes, `href`, `src`, or style-bearing output.
- Add the exact hostile TeX case and validator-failure cases to the focused suite.
- Preserve all already-passing syntax, reference, embed, and FEAT-0038 behaviors.

## Changes Applied

- Added an XML validation gate for generated MathML.
- Allowed only the MathML namespace, an explicit presentation-element set, and explicit non-fetching attributes.
- Routed malformed, foreign, unknown, namespaced-attribute, event, `href`, `src`, and style-bearing output to escaped TeX fallback.
- Added the exact script-shaped converter output and a generated `href` case to the focused functional suite.
- Retained valid inline, fraction, square-root, and matrix MathML output.

## Contract Or Lane Impact

- Contract surfaces touched: local MathML trust boundary only.
- Surface lanes touched: `syntax-extension`.
- Stale-assumption check needed: yes; generated markup must have no other unvalidated producer.

## Remaining Issues

- None. Contract Attempt 2 and Functional Attempt 2 passed.

## Return Decision

- `pass`

## Continuity Notes

- `2026-07-19`: Fix Agent received the exact hostile MathML finding; no planning or spec change is required.
- `2026-07-19`: the bounded allowlist fix passed exact hostile and normal MathML probes, focused and full suites, privacy, and both required re-evaluators.
