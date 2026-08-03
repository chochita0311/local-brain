# FIX-0068: Claude Session Candidate Discovery

## Metadata

- ID: `fix-0068-claude-session-candidate-discovery`
- Status: `complete`
- Run ID: `run-20260802-79`
- Attempt: `1`
- Feature: [feat-0068-multi-source-session-synchronization-and-health](../feature/feat-0068-multi-source-session-synchronization-and-health.md)
- Spec: [spec-0068-multi-source-session-synchronization-and-health](../spec/spec-0068-multi-source-session-synchronization-and-health.md)
- Execution Profile: `backend-product`
- Surface Lane: Claude discovery and source reconciliation
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Input Reports

- Human runtime inspection found a `subagents/workflows/**/journal.jsonl` file
  represented as a primary work Session with no Activity Events or Usage Records.

## Fix Scope

- Accept Claude JSONL outside the `subagents` internal tree as primary candidates.
- Accept only direct `subagents/*.jsonl` children inside that tree.
- Exclude deeper workflow artifacts before freshness and stale reconciliation.
- Reconcile prior false Session/source-file rows during the next successful scan
  while preserving the original native file.
- Preserve valid primary and direct Subsession behavior; do not change metadata-only
  top-level Session eligibility in this fix.

## Changes Applied

- Added a root-relative Claude path predicate to the provider dispatch contract.
- Filtered candidates before freshness and source-owned stale reconciliation.
- Added a legacy-false-import integration fixture covering primary, direct child,
  nested journal, source-file cleanup, parent continuity, report counts, and
  native-file preservation.
- Updated architecture and Data Model owners and regenerated their schema
  presentation and cleanup-audit derivatives.

## Contract Or Lane Impact

- Contract surfaces touched: Claude candidate selection and source-owned stale
  reconciliation.
- Surface lanes touched: scanner/data and owner docs.
- Stale-assumption check needed: yes; the generic recursive JSONL assumption is
  invalid for Claude's internal `subagents` descendants.

## Remaining Issues

- Metadata-only top-level Claude Session eligibility remains separate.

## Return Decision

- `re-evaluate`

## Continuity Notes

- `2026-08-02`: Fix opened from post-run human review; Feature and Spec boundaries
  remain valid.
- `2026-08-02`: correction passed targeted and full regression, generated owner
  checks, privacy, and diff validation.
