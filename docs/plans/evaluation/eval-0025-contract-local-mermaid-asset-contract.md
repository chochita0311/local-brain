# EVAL-0025: Local Mermaid Asset Contract — Contract

## Metadata

- ID: `eval-0025-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-30`
- Attempt: `1`
- Feature: [feat-0025-local-mermaid-asset-contract](../feature/feat-0025-local-mermaid-asset-contract.md)
- Spec: [spec-0025-local-mermaid-asset-contract](../spec/spec-0025-local-mermaid-asset-contract.md)
- Execution Profile: `infra-devtool`
- Surface Lane: dependency contract, asset production, packaging ownership
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: exact local Mermaid dependency, deterministic browser assets, strict LocalBrain adapter, package ownership, and update documentation.
- Active spec: SPEC-0025 attempt 1.
- Evaluated build or commit: current unstaged FEAT-0025 build in the shared workspace.

## Checks

- Inspected `package.json` and the public-registry `package-lock.json` for exact Mermaid 11.16.0, esbuild 0.28.1, Node `>=20`, and absence of machine or corporate registry paths.
- Ran the build, freshness check, and self-test against the committed output set.
- Verified the manifest binds the lockfile digest, exact direct dependency versions and licenses, and every generated output digest.
- Inspected the adapter for one-time initialization, `startOnLoad: false`, `securityLevel: "strict"`, suppressed error rendering, explicit application-owned node selection, and bounded result codes.
- Verified there is no route, page scan, CDN, runtime npm path, imported-content renderer, schema source, or user-input rendering path in this Feature.
- Verified `node_modules`, caches, browser downloads, runtime artifacts, and private data types remain ignored.
- Verified the Developer Guide owns source, version, license, build, check, output, runtime, and update instructions.
- Verified the generated vendor bundle's exact privacy allowlist entry suppresses only local denylist collisions; generic secret, path, email, and Git identity checks still run.

## Evidence

- Environments checked: source inspection, exact npm lockfile installation, deterministic temporary generation, deliberate temporary stale output, Python wheel inventory, and repository privacy scan.
- `npm run check:mermaid` passed against the final generated output.
- `npm run test:mermaid` regenerated in a temporary directory, passed current-output comparison, changed the temporary manifest, and observed the required non-zero stale result.
- The final wheel contains `mermaid-adapter.js`, asset manifest, both direct license files, and the 3,444,998-byte bundled ESM asset under `localbrain/static/`.
- The privacy scanner passed all 316 repository candidates after confirming the only local-denylist collisions in the public bundle were generic library abbreviations.

## Evidence Gaps

- None. Browser placement and on-page diagram behavior are intentionally absent from FEAT-0025 and belong to FEAT-0028.

## Contract Evidence

- Producer surfaces: `package.json`, public `package-lock.json`, and `scripts/build-mermaid-assets.mjs`.
- Consumer surfaces: `src/localbrain/static/mermaid-adapter.js` and later application-owned modules only.
- Schemas, payloads, generated artifacts, commands, routes, config, or policy docs checked: `localbrain.mermaid-assets.v1`, npm build/check/test commands, vendor output directory, ignore rules, wheel contents, privacy scanner, and Developer Guide.
- Stale-assumption check: a modified temporary manifest failed comparison; the current lockfile/output bytes passed.

## Findings

- No blocking or non-blocking contract finding remains.

## Regression Notes

- Existing static asset ownership, package-static inclusion, local runtime boundary, and privacy scanning remain active and passed.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: passed attempt 1 with complete dependency, asset, adapter, package, documentation, and privacy evidence.
