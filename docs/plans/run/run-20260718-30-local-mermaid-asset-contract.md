# RUN-20260718-30: Local Mermaid Asset Contract

## Metadata

- ID: `run-20260718-30`
- Status: `passed`
- Feature: [feat-0025-local-mermaid-asset-contract](../feature/feat-0025-local-mermaid-asset-contract.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Active Spec: [spec-0025-local-mermaid-asset-contract](../spec/spec-0025-local-mermaid-asset-contract.md)
- Attempt: `1`
- Surface: `infra`
- Execution Profile: `infra-devtool`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Establish and verify the reproducible local Mermaid asset and adapter contract without introducing a visible product surface.

## Selected Loop

- Feature type: foundation.
- Surface: infra.
- Surface lanes: dependency contract → asset production → packaging and runtime.
- Required evaluators: contract and functional.
- Current phase: complete.

## Surface Lanes

- Dependency contract:
  - path roots: `package.json`, `package-lock.json`, `.gitignore`
  - dependencies: approved PRD-0003 and SPEC-0025
  - validation evidence: exact versions, clean lockfile install, ignored dependency state
  - evaluator ownership: contract
- Asset production:
  - path roots: `scripts/build-mermaid-assets.mjs`, `src/localbrain/static/vendor/mermaid/`, adapter
  - dependencies: dependency contract
  - validation evidence: deterministic repeat and stale-output failure
  - evaluator ownership: contract, functional
- Packaging and runtime:
  - path roots: wheel, static mount, Developer Guide, tests
  - dependencies: asset production
  - validation evidence: wheel inventory and Python-only static serving
  - evaluator ownership: functional

## Contract Surfaces

- npm dependency and lockfile, generated asset manifest, local ESM bundle, dependency license evidence, adapter API and trust boundary, Python static packaging, build and update documentation.

## Invocation Context

- Golden sources: FEAT-0025, SPEC-0025, current static mount, package build configuration, installed npm distributions.
- Relevant policies: Developer Guide, Privacy And Data Handling, execution-loop governance, infra-devtool profile.
- Optional skills or tools expected: npm clean install and build, uv wheel build, repository privacy scanner.

## Current Artifacts

- Spec: [spec-0025-local-mermaid-asset-contract](../spec/spec-0025-local-mermaid-asset-contract.md)
- Contract evaluation: [eval-0025-contract-local-mermaid-asset-contract](../evaluation/eval-0025-contract-local-mermaid-asset-contract.md)
- Design evaluation: not required
- Functional evaluation: [eval-0025-functional-local-mermaid-asset-contract](../evaluation/eval-0025-functional-local-mermaid-asset-contract.md)
- UX heuristic evaluation: not required
- Fix log: not created
- Heuristic backlog: not required

## Evaluation Coverage

- Contract:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: source, clean npm install, deterministic and stale output, wheel, privacy boundary
  - Unverified claims: none
  - Acceptance impact: not applicable
- Functional:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: clean install, final wheel, isolated Node-free static runtime, full Python regression
  - Unverified claims: none within FEAT-0025 scope
  - Acceptance impact: not applicable

## Current Route

- Next role: human review or FEAT-0026 planner under the approved sequence.
- Current blocker classification: none.
- In-run route: complete.
- Post-run recommendation for human review: proceed to FEAT-0026; both required evaluators passed.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: reproducible local Mermaid browser asset and runtime-independent adapter contract established
  - notes: no fix loop was required

## Post-Contract Regression Check

- Needed: yes.
- Result: PASS.
- Notes: final wheel inventory and isolated static serving passed; all 84 tests and privacy scan passed.

## Human Review Outcome

- Decision: automated feature boundary passed under the previously approved sequential PRD-0003 workflow.
- Returned layer if any: none.
- Follow-up run: RUN-20260718-31 for FEAT-0026.

## Continuity Notes

- `2026-07-18`: run initialized from the approved PRD-0003 sequential workflow request.
- `2026-07-18`: run passed after complete contract and functional evidence; no fix route was required.
