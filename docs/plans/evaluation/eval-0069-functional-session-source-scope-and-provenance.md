# EVAL-0069: Session Source Scope And Provenance — Functional

## Metadata

- ID: `eval-0069-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260802-74`
- Attempt: `1`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Spec: [spec-0069-session-source-scope-and-provenance](../spec/spec-0069-session-source-scope-and-provenance.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Sessions routes, inventory, Project grouping, pin, and detail
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Scope

- Verified aggregate/source counts, old-data inclusion, paging, workspace
  combinations, invalid recovery, provenance, detail return paths, pin and child
  regressions.

## Checks

- Aggregate eligible count equals the sum of dynamic per-source counts.
- `codex-company` returns only company Sessions and `codex` returns only personal
  Sessions even when native IDs and provider kind can match.
- A 2024 company Session is visible while company Maintenance and Subsession rows
  remain outside the headline/list/Project denominator.
- Selected source constrains Projects and workspace-filtered inventory before
  pagination; changing Source links omit page and preserve valid workspace state.
- Unknown Source keys fall back to `전체`; missing workspace IDs are removed while
  a valid Source remains selected.
- Inventory rows, Pinned Sessions, direct children, primary detail, normalized
  child detail, and lazy child detail expose source name and retain list/parent
  orientation.
- Existing 15-item pagination, pinned panel independence, pin mutations,
  conversation filters, Related Context, and synchronization fallback pass.

## Evidence

- Full repository suite: 318 tests passed.
- Route-rendered synthetic company fixtures verify scoped inventory and detail
  links without reading private runtime data.

## Evidence Gaps

- Browser pointer/back-forward observation was unavailable because the Browser
  skill's required in-app control capability was not exposed. GET-state route,
  rendered link, DOM, pin-return, and responsive contracts are covered directly.

## Findings

- None.

## Route

- Next action: `pass`.
