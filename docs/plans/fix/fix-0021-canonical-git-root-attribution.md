# FIX-0021: Canonical Git Root Attribution

## Metadata

- ID: `fix-0021-canonical-git-root-attribution`
- Status: `complete`
- Run ID: `run-20260718-21`
- Attempt: `2`
- Feature: [feat-0021-activity-and-project-attribution-contract](../feature/feat-0021-activity-and-project-attribution-contract.md)
- Spec: [spec-0021-activity-and-project-attribution-contract](../spec/spec-0021-activity-and-project-attribution-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: attribution producer
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Input Reports

- Initial Functional evaluation found a synthetic macOS alias mismatch between canonical workspace paths and discovered Git-root snapshots.

## Fix Scope

- Normalize a discovered Git root with the same filesystem resolution used for `workspaces.canonical_path`.

## Changes Applied

- `_find_git_root` now returns `candidate.resolve()`.
- The late-Git-discovery fixture verifies stable `path:` and `git:` keys use one canonical path system while retaining their distinct attribution bases.

## Contract Or Lane Impact

- Contract surfaces touched: current Git-root producer and immutable Project-key input.
- Surface lanes touched: attribution producer only.
- Stale-assumption check needed: yes; existing Project and Session regression tests reran.

## Remaining Issues

- None.

## Return Decision

- `re-evaluate`

## Continuity Notes

- `2026-07-18`: the fix removed `/var` versus `/private/var` key drift without changing historical reconciliation policy.
