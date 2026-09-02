# EVAL-0084 Contract: Project-Grouped Pinned Sessions

## Metadata

- ID: `eval-0084-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260902-94`
- Attempt: `1`
- Feature: [FEAT-0084](../feature/feat-0084-project-grouped-pinned-sessions.md)
- Spec: [SPEC-0084](../spec/spec-0084-project-grouped-pinned-sessions.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `Pinned read model; grouped inventory projection; durable owners`
- Evidence Coverage: `complete`
- Created: `2026-09-02`

## Checks And Evidence

- Pin persistence, eligibility, membership, and lifecycle remain unchanged. The query adds only existing `sessions.git_branch` and `workspaces.git_root` fields, and grouping is a request-time projection over the uncapped pin rows.
- Workspace ID is the primary group identity. A missing workspace relation falls back to cwd identity, then one bounded unassigned group, without creating or mutating data.
- Git classification uses the current non-empty workspace `git_root`, not the presence of one Session branch. Group order is Git first, then non-Git, case-insensitive alphabetical label, and stable identity; the existing displayed-activity, pin-time, and Session-ID order is preserved inside each group.
- Product, Design Constitution, PRD-0009, FEAT-0084, and SPEC-0084 describe the same derived grouping and optional Session-owned branch contract. Historical FEAT-0059 artifacts remain unchanged.
- Focused Pinned Sessions and inventory verification passed `65/65`; the full repository suite passed `482/482`. Schema cleanup remained current at `623` objects, Python compilation and `git diff --check` passed, and final repository privacy passed over `843` candidate files.

## Findings

- None.

## Current Route

- Current route: `PASS`.
