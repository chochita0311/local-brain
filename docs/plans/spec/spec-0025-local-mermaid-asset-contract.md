# SPEC-0025: Local Mermaid Asset Contract

## Metadata

- ID: `spec-0025`
- Status: `approved`
- Run ID: `run-20260718-30`
- Attempt: `1`
- Parent Feature: [feat-0025-local-mermaid-asset-contract](../feature/feat-0025-local-mermaid-asset-contract.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `infra`
- Execution Profile: `infra-devtool`
- Surface Lane: dependency contract, asset production, packaging and runtime
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Source Set

- Human request: include Mermaid as a proper LocalBrain web-app library and use it later for subject-oriented Schema views.
- Parent feature: FEAT-0025.
- Parent PRD: approved PRD-0003.
- Golden sources: repository package configuration, static asset serving, Python package build output, and Mermaid's installed npm distribution.
- Relevant policies or contracts: Developer Guide, Privacy And Data Handling, execution-loop governance, and the `infra-devtool` profile.

## Implementation Goal

- Produce a version-pinned, deterministic Mermaid browser bundle and a narrow LocalBrain adapter that are committed with LocalBrain, included in its wheel, and usable without Node, npm, a CDN, or network access at application runtime.

## In-Scope Behavior

- Add a private repository-owned `package.json` with Node `>=20`, exact Mermaid `11.16.0`, exact esbuild `0.28.1`, deterministic build/check scripts, and a committed npm lockfile.
- Add a bounded Node build script that bundles the installed Mermaid ESM entry into `src/localbrain/static/vendor/mermaid/mermaid.esm.min.js`, writes reviewed dependency license evidence, and emits a manifest containing the dependency version, lockfile digest, and output digest.
- Make `npm run check:mermaid` rebuild in a temporary directory and fail when any committed generated output differs or is missing.
- Keep dependency directories, npm caches, temporary build output, and browser test downloads ignored.
- Add a LocalBrain-owned ES module adapter that initializes Mermaid once with `securityLevel: "strict"`, disables automatic page scanning, accepts only explicitly marked application-owned nodes, and returns a bounded success or failure result.
- Include the generated vendor directory and adapter in the Python wheel through the existing package-static ownership.
- Document build prerequisites, dependency source and license, commands, output ownership, update procedure, freshness verification, and the runtime no-Node/no-network boundary.

## Out-Of-Scope Behavior

- Do not add a `/schema` route, navigation item, template, data-model document, ERD source, schema introspection, or presentation manifest.
- Do not add a general frontend framework, application-wide bundler, CDN fallback, remote editor, telemetry, or runtime npm invocation.
- Do not render imported, persisted, query-provided, or user-authored Mermaid text.

## Affected Surfaces

- `package.json`, `package-lock.json`, `.gitignore`
- `scripts/build-mermaid-assets.mjs`
- `src/localbrain/static/vendor/mermaid/`
- `src/localbrain/static/mermaid-adapter.js`
- `docs/policies/project/developer-guide.md`
- focused asset-contract tests and Python package build evidence

## Surface Lanes

- Dependency contract lane:
  - path roots: package manifest, lockfile, ignore rules
  - dependency order: first
  - implementation responsibility: exact build-only toolchain and untracked dependency state
  - validation evidence: clean `npm ci`, lockfile inspection, ignore checks
- Asset production lane:
  - path roots: build script, generated vendor directory, adapter
  - dependency order: after dependency install
  - implementation responsibility: deterministic local output and strict render boundary
  - validation evidence: two identical builds, freshness failure against a changed copy, static source inspection
- Packaging and runtime lane:
  - path roots: Python package config, Developer Guide, wheel and local server
  - dependency order: after generated assets exist
  - implementation responsibility: packaged offline availability without Node
  - validation evidence: wheel inventory, Python-only route/static checks, existing test suite

## State And Interaction Contract

- Clean checkout: `npm ci` installs the exact lockfile graph and `npm run build:mermaid` creates the reviewed output set.
- Current checkout: `npm run check:mermaid` exits successfully without modifying committed outputs.
- Missing or stale output: the check exits non-zero and identifies rebuild as the remedy.
- Installed application: static assets load from LocalBrain's `/static` mount without Node or external requests.
- Adapter idle: no document scan or render occurs at module import.
- Adapter success: one app-owned node with a non-empty source from its trusted application markup receives sanitized Mermaid SVG and an explicit success result.
- Adapter rejection/failure: an unowned node, missing source, or Mermaid error yields a bounded error result; the adapter does not expose library-generated diagnostic HTML as page content.

## Data And Contract Assumptions

- Mermaid source is authored and reviewed in LocalBrain-owned templates or modules only; no runtime row, imported content, request input, or arbitrary user text is eligible.
- The checked-in bundle is generated output. `package.json`, `package-lock.json`, and the build script own regeneration; the generated manifest proves their correspondence.
- npm is a build-time input only. End users running an installed wheel do not need it.
- Mermaid and esbuild are MIT-licensed; license files retained with the generated output are review evidence, not a replacement for the lockfile.

## Contract Surfaces

- Producer expectations: npm lockfile plus the build script produce the complete vendor output set deterministically.
- Consumer expectations: later LocalBrain-owned screens import only `mermaid-adapter.js`; they do not import npm paths or accept arbitrary source.
- Generated artifacts: bundled ESM file, Mermaid license, esbuild license, and asset manifest under `src/localbrain/static/vendor/mermaid/`.
- Source-of-truth owner: `package.json`, `package-lock.json`, and `scripts/build-mermaid-assets.mjs`.
- Stale-assumption check: the check script compares freshly generated bytes and manifest digests against every committed generated artifact.

## Required Evaluators

- Contract: exact dependency ownership, lockfile, source/license evidence, generated-output parity, strict adapter boundary, ignored artifacts, and documentation ownership.
- Design: not required; no visible surface changes.
- Functional: clean install, repeated deterministic build, deliberate stale-copy failure, wheel inclusion, Python-only static serving, and existing regression checks.
- UX heuristic: not required; no visible surface changes.

## Acceptance Mapping

- Exact dependency and lockfile: private package manifest plus `package-lock.json`.
- Reproducible commands: `npm ci`, `npm run build:mermaid`, and `npm run check:mermaid`.
- Packaged local assets: generated vendor directory verified in a built wheel.
- Ignored build state: `.gitignore` entries plus repository candidate inspection.
- Runtime independence: application imports no Node process and serves only committed static bytes.
- Strict adapter: explicit marker/source boundary, one-time strict initialization, manual render API, bounded result.
- No arbitrary source: adapter eligibility contract and focused source tests.
- Documentation: Developer Guide Mermaid asset section.
- Freshness: lockfile/output digest manifest plus clean regeneration comparison.
- Regression: privacy check, JavaScript syntax checks, Python tests, and static route check.

## Evaluation Focus

- Confirm the build does not encode machine paths, timestamps, remote URLs, or non-deterministic banners.
- Confirm every generated output is accounted for and a lockfile-only change makes the freshness check fail.
- Confirm the adapter cannot be called on an unmarked node and no automatic Mermaid scan is enabled.
- Confirm the wheel contains the bundle, notices, manifest, and adapter while excluding `node_modules`.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-18`: approved for attempt 1 after the human owner approved step-by-step execution of PRD-0003 Features.
- `2026-07-18`: pinned Mermaid 11.16.0 and esbuild 0.28.1 from configured npm registry metadata; both are build-time dependencies only.
