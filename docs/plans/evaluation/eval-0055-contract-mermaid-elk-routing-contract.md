# EVAL-0055: Mermaid ELK Routing Contract — Contract

## Metadata

- ID: `eval-0055-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260724-59`
- Attempt: `1`
- Feature: [feat-0055-mermaid-elk-routing-contract](../feature/feat-0055-mermaid-elk-routing-contract.md)
- Spec: [spec-0055-mermaid-elk-routing-contract](../spec/spec-0055-mermaid-elk-routing-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: official loader, package, asset, license, offline, and fallback policy
- Evidence Coverage: `complete`
- Created: `2026-07-24`

## Checks And Evidence

- Mermaid `11.16.0` exposes `registerLayoutLoaders`, accepts `layout: elk`, and documents ELK as the supported complex-diagram alternative.
- `@mermaid-js/layout-elk@0.2.2` is the official MIT-licensed package, accepts Mermaid `^11.0.2`, develops against `^11.16.0`, exports loader definitions, and uses EPL-2.0-licensed `elkjs`.
- The candidate bundles under the current esbuild/browser target with no CDN or runtime network dependency.
- The exact package/lock, manifest dependencies/checksums, license outputs, freshness behavior, and atomic replacement requirements are fixed for FEAT-0056.
- Generated Schema source and data-model ownership remain unchanged.
- Failure ownership is explicit: ELK, one Dagre retry, then text.

## Evidence Gaps

- None for the adoption contract. Product artifact hashes and installed-output verification belong to FEAT-0056 after implementation.

## Findings

- None.

## Route

- Next action: `pass`.
