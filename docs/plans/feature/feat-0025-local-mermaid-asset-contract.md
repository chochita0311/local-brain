# FEAT-0025: Local Mermaid Asset Contract

## Metadata

- ID: `feat-0025`
- Status: `passed`
- Type: `foundation`
- Surface: `infra`
- Execution Profile: `infra-devtool`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Establish one reproducible, version-pinned, locally served Mermaid dependency and asset contract so documentation and later product surfaces can render approved diagrams without a CDN, global package, Node runtime, or external service.

## Acceptance Contract

- Mermaid is declared as an exact project dependency in a repository-owned JavaScript package manifest with a committed lockfile.
- A clean supported developer environment can install with the lockfile, build or copy the approved distribution, and verify the output through documented deterministic commands.
- Browser assets required by Mermaid are emitted under `src/localbrain/static/vendor/mermaid/` and are included in an installed LocalBrain package.
- `node_modules`, package-manager caches, temporary build output, and downloaded browser binaries remain untracked.
- The Python application and installed `localbrain` command do not require Node.js, npm, a CDN, or network access at runtime.
- A small LocalBrain-owned browser adapter initializes Mermaid once through the supported API, uses restrictive security settings, renders only explicitly selected application-owned nodes, and reports bounded render failures to its caller.
- Imported documents, Session content, runtime rows, query parameters, and arbitrary user text cannot become executable Mermaid source.
- The dependency version, distribution source, license, build command, output path, and update procedure are documented in the Developer Guide.
- A deterministic freshness check fails when the manifest or lockfile and the packaged Mermaid assets no longer correspond.
- Existing locally served CSS, JavaScript, asset versioning, privacy scanning, server startup, and package installation remain intact.

## Scope Boundary

- In:
  - repository-owned JavaScript package manifest and lockfile
  - exact Mermaid dependency and supported Node build-time range
  - deterministic local asset build or copy command
  - `src/localbrain/static/vendor/mermaid/` output contract
  - reusable LocalBrain Mermaid browser adapter
  - strict rendering input boundary and bounded failure contract
  - wheel or installed-package asset inclusion
  - dependency license and update documentation
  - stale-asset and clean-install verification
- Out:
  - `/schema` route, navigation, templates, or visual layout
  - data-model documents or actual ERD definitions
  - schema introspection or presentation-manifest generation
  - CDN loading, remote editors, telemetry, or external rendering
  - a general frontend framework, development server, or application-wide bundler migration
  - requiring Node.js on an end-user machine at application runtime

## Surface Lanes

- Dependency contract lane:
  - path roots: JavaScript package manifest, lockfile, `.gitignore`, dependency policy
  - dependencies: approved PRD-0003
  - expected evidence: exact version, lockfile reproducibility, ignored caches, source and license ownership
  - evaluator ownership: `contract`
- Asset production lane:
  - path roots: build scripts, `src/localbrain/static/vendor/mermaid/`, LocalBrain browser adapter
  - dependencies: dependency contract lane
  - expected evidence: clean install, deterministic output, strict initialization, and stale-output failure
  - evaluator ownership: `contract`, `functional`
- Packaging and runtime lane:
  - path roots: `pyproject.toml`, package build configuration, Developer Guide, package tests
  - dependencies: asset production lane
  - expected evidence: built package contains assets and runs without Node or network access
  - evaluator ownership: `functional`

## Contract Surfaces

- JavaScript dependency manifest and lockfile ownership
- supported build-time Node and package-manager assumptions
- Mermaid version and local distribution source
- deterministic build, check, and update commands
- `src/localbrain/static/vendor/mermaid/` generated-output ownership
- browser adapter initialization, security, input, success, and failure behavior
- Python package static-asset inclusion
- local-only runtime and no-CDN boundary

## Required Evaluators

- `contract`: dependency, lockfile, generated asset, security, source, license, packaging, and ownership parity.
- `functional`: clean install, repeated build, stale asset, installed package, offline runtime, and existing asset regression behavior.

## User-Visible Outcome

- This foundation Feature adds no route. It ensures later Mermaid-backed surfaces load from LocalBrain itself and remain available offline.

## Entry And Exit

- Entry point: documented dependency installation, asset build, and asset freshness commands.
- Exit or transition behavior: FEAT-0026 may validate Mermaid documents locally, and FEAT-0028 may consume the packaged browser adapter without choosing another dependency path.

## State Expectations

- Clean checkout: the lockfile installs the exact supported dependency set.
- Current assets: the freshness check passes without rewriting files.
- Stale assets: the check fails with a bounded instruction to rebuild.
- Missing build-time Node: dependency commands fail clearly; the installed Python app remains runnable.
- Runtime offline: packaged Mermaid assets load without a network request.
- Render failure: the adapter exposes a bounded failure result without replacing the page with raw library output.
- Success: dependency metadata, generated assets, license evidence, and installed-package contents agree.

## Dependencies

- PRD-0003 is `approved`.
- No data-model baseline or product route is required to establish this asset contract.

## Likely Affected Surfaces

- `package.json`
- package-manager lockfile
- `.gitignore`
- bounded asset build and verification scripts
- `src/localbrain/static/vendor/mermaid/`
- a LocalBrain-owned Mermaid adapter under `src/localbrain/static/`
- `pyproject.toml` or package asset configuration when required
- `docs/policies/project/developer-guide.md`
- dependency, asset, package, and offline-runtime tests

## Pass Or Fail Checks

- Pass if a clean lockfile install and two repeated asset builds produce the same reviewed output.
- Pass if a manifest, lockfile, or generated-asset mismatch makes the freshness check fail.
- Pass if the built Python package contains all Mermaid runtime assets and starts with Node unavailable and network disabled.
- Pass if the browser adapter uses the supported Mermaid initialization and render APIs with restrictive security settings.
- Pass if only application-owned diagram nodes are accepted and arbitrary source inputs have no rendering path.
- Pass if Mermaid source, version, license, build, output, and update ownership are documented.
- Pass if existing `app.js`, CSS, favicon, asset versioning, and routes continue loading normally.
- Fail if any application page needs a CDN, global npm package, Node runtime, or external renderer.
- Fail if `node_modules`, caches, private artifacts, or unreviewed downloaded binaries enter Git.

## Regression Surfaces

- Python-only LocalBrain runtime and CLI startup
- FastAPI static file serving and asset cache versioning
- current server-rendered pages and `app.js` bindings
- source distribution and wheel contents
- privacy scanner and ignored runtime-artifact boundary

## Harness Trace

- Active spec doc: [spec-0025-local-mermaid-asset-contract](../spec/spec-0025-local-mermaid-asset-contract.md)
- Active run: [run-20260718-30-local-mermaid-asset-contract](../run/run-20260718-30-local-mermaid-asset-contract.md)
- Execution profile: `infra-devtool`
- Latest evaluator report: [contract](../evaluation/eval-0025-contract-local-mermaid-asset-contract.md), [functional](../evaluation/eval-0025-functional-local-mermaid-asset-contract.md)
- Latest fix note: not created

## Continuity Notes

- `2026-07-18`: initial draft separated reproducible local Mermaid dependency and packaging ownership from data-model content and the later Schema Explorer product surface.
- `2026-07-18`: human owner approved sequential execution of PRD-0003 Features; FEAT-0025 entered the loop under SPEC-0025 and RUN-20260718-30.
- `2026-07-18`: passed attempt 1 with exact public lockfile dependencies, deterministic and stale-asset checks, strict owned-node adapter, final wheel inclusion, isolated Python-only static serving, 84 passing tests, and a passing privacy scan.
