# EVAL-0025: Local Mermaid Asset Contract — Functional

## Metadata

- ID: `eval-0025-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260718-30`
- Attempt: `1`
- Feature: [feat-0025-local-mermaid-asset-contract](../feature/feat-0025-local-mermaid-asset-contract.md)
- Spec: [spec-0025-local-mermaid-asset-contract](../spec/spec-0025-local-mermaid-asset-contract.md)
- Execution Profile: `infra-devtool`
- Surface Lane: clean install, deterministic assets, installed runtime, regressions
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: Local Mermaid asset installation, build, freshness, packaging, and offline Python runtime behavior.
- Active spec: SPEC-0025 attempt 1.
- Evaluated build or commit: current unstaged FEAT-0025 build in the shared workspace.

## Checks

- Ran `npm ci --no-audit --registry=https://registry.npmjs.org` from the committed lockfile and installed 113 packages successfully.
- Ran the final build, freshness check, JavaScript syntax checks, and temporary stale-output self-test.
- Built the source distribution and wheel with the documented system-certificate option and inspected the wheel inventory.
- Expanded the final wheel into an isolated directory and requested the bundle, manifest, and adapter through `StaticFiles` with Node absent from `PATH`.
- Ran the complete Python unit suite, repository privacy scan, diff whitespace check, and ignore checks.

## Evidence

- Environments checked: clean npm install, repeated local Node build, temporary stale fixture, final Python wheel, isolated installed-package static runtime, and full repository test environment.
- Clean npm installation, asset freshness, self-test, and JavaScript syntax checks passed.
- The installed package returned all three requested static resources with HTTP 200 and validated the expected manifest schema and strict adapter source without Node in `PATH` or a network request.
- All 84 Python tests passed.
- Privacy check passed for 316 candidate files; `git diff --check` and ignored-dependency checks passed.

## Evidence Gaps

- No Schema page exists in this Feature, so an in-app visual render was not applicable. FEAT-0028 owns browser-rendered diagram and failure-state evidence.
- Acceptance impact: not applicable.

## Findings

- No functional blocker or regression remains.

## Regression Notes

- Existing application tests, static files, Python-only runtime, wheel contents, and privacy boundaries passed.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: passed attempt 1 after clean installation, deterministic/stale checks, final wheel verification, isolated static serving, and full regression.
