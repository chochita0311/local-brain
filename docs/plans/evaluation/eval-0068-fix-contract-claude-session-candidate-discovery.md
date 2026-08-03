# EVAL-0068 FIX: Claude Session Candidate Discovery — Contract

## Metadata

- ID: `eval-0068-fix-contract-claude-session-candidate-discovery`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260802-79`
- Attempt: `1`
- Feature: [feat-0068-multi-source-session-synchronization-and-health](../feature/feat-0068-multi-source-session-synchronization-and-health.md)
- Spec: [spec-0068-multi-source-session-synchronization-and-health](../spec/spec-0068-multi-source-session-synchronization-and-health.md)
- Execution Profile: `backend-product`
- Surface Lane: Claude discovery and source-owned reconciliation
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Checks

- Provider-specific candidate filtering applies only to the Claude adapter;
  personal and company Codex discovery remain unchanged.
- The filter is evaluated relative to the configured root, accepts paths outside
  the native `subagents` tree and direct `subagents/*.jsonl` children, and rejects
  deeper internal descendants such as workflow journals.
- Filtering occurs before freshness and stale reconciliation, so previously
  normalized false Sessions and source-file evidence leave the valid set during a
  successful scan while the native file remains untouched.
- Missing or invalid roots still skip the scan and retain normalized data under
  the existing safe-registration contract.
- Architecture, Session lifecycle, source-file ownership, generated schema
  presentation, and cleanup-audit evidence are current.

## Evidence

- Targeted scanner/parser/ingest set: 22 tests passed.
- Full repository suite: 324 tests passed.
- Schema presentation, Data Model docs, and 531-object cleanup audit checks passed.
- Privacy and diff checks passed.

## Findings

- None.

## Route

- Next action: `pass`.
