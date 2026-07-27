# EVAL-0056: Schema ERD Orthogonal Routing — Contract

## Metadata

- ID: `eval-0056-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260724-63`
- Attempt: `1`
- Feature: [feat-0056-schema-erd-orthogonal-routing](../feature/feat-0056-schema-erd-orthogonal-routing.md)
- Spec: [spec-0056-schema-erd-orthogonal-routing](../spec/spec-0056-schema-erd-orthogonal-routing.md)
- Execution Profile: `frontend-product`
- Surface Lane: local asset, loader, manifest, license, and fallback ownership
- Evidence Coverage: `complete`
- Created: `2026-07-24`

## Checks And Evidence

- Exact direct loader and Mermaid versions are pinned in manifest and lockfile.
- The lockfile owns exact public-registry integrity for the loader and engine.
- The loader and engine are bundled locally; browser requests contain no CDN or npm path.
- Manifest checksums own every executable and license output.
- MIT and EPL-2.0 license texts are separately retained and installed-package verified.
- Every Schema node requests ELK; non-Schema consumers do not.
- Generated Mermaid definitions and Schema Presentation bytes are unchanged by layout selection.
- Attempt order is exactly ELK, unchanged-source Dagre, then text.

## Evidence Gaps

- None.

## Findings

- None.

## Route

- Next action: `pass`.
