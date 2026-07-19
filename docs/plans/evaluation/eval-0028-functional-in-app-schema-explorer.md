# EVAL-0028: In-App Schema Explorer — Functional

## Metadata

- ID: `eval-0028-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260718-33`
- Attempt: `1`
- Feature: [feat-0028-in-app-schema-explorer](../feature/feat-0028-in-app-schema-explorer.md)
- Spec: [spec-0028-in-app-schema-explorer](../spec/spec-0028-in-app-schema-explorer.md)
- Execution Profile: `fullstack-product`
- Surface Lane: route states, progressive navigation, Mermaid/fallback, package, regressions, and privacy
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: end-to-end `/schema` behavior and failure continuity.
- Active spec: SPEC-0028 attempt 1.
- Evaluated build or commit: current unstaged implementation, local runtime, and final wheel.

## Checks

- Exercised global, all eight areas, all 21 owned table states, invalid area, invalid/cross-area table, table-without-area, missing manifest, and malformed manifest behavior.
- Patched the normal database connector to raise during route rendering and confirmed `/schema` succeeds without runtime DB access.
- Verified ordinary links, no-script direct table entry, complete textual detail, and fixed non-reflecting correction messages.
- Loaded local Mermaid through the strict adapter and exact packaged JSON-safe definition; confirmed SVG state at 1440/920/700/320.
- Clicked global → area → table through the partial-navigation module and verified atomic region replacement, canonical URL, visible/programmatic current state, detail identity, heading focus, and non-busy settled state.
- Exercised back, forward, rapid consecutive area selection, warm-cache reload, and invalid direct entry; the latest destination won and state/focus restored coherently.
- Blocked the Mermaid adapter request and confirmed bounded unavailable text, nine subject links, and the selected area's table index remained usable.
- Disabled JavaScript and confirmed canonical `source_files` selection, detail, and all subject links remained present.
- Ran schema/document/presentation parity, nine local Mermaid parses, Mermaid current/stale tests, all Python tests, repository privacy, and whitespace checks.
- Built and inspected the final wheel, expanded it outside the repository, removed Node from `PATH`, and rendered a selected installed `/schema` response without docs, DB, or network.

## Evidence

- Schema route/view-model tests: 6 of 6 passed.
- Complete Python suite: 102 of 102 passed.
- Browser QA: every asserted viewport and interaction state passed, including warm-cache, blocked adapter, no-script, rapid input, back/forward, and exact 320 containment.
- Final wheel SHA-256: `be2bc8ca0c193060dc51d1a7b8a58a33f169700fa72ab1b96e7dc130df4c19fa`.
- Privacy check passed for 353 candidate files before evaluation artifacts; final scan is recorded in the Run closure.

## Evidence Gaps

- Hot-swapping code/templates/static files into an already running server is unsupported. Normal upgrades require the bounded server restart that recomputes the static asset version; the post-restart warm-cache revisit passed.
- Acceptance impact: not applicable; mixed-version hot reload is not a supported runtime contract.

## Findings

- No route error, stale request win, focus/history mismatch, inert warm-cache markup, fallback loss, runtime-row access, package omission, privacy issue, or regression remains.

## Regression Notes

- Existing Session, Usage, Context, Workstream, Runner, shell, and schema-presentation suites passed. The local server still has no Node runtime dependency.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: passed attempt 1 after direct browser and installed-package validation covered all blocking runtime states.
