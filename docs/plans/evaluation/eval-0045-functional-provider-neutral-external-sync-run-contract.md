# EVAL-0045: Provider-Neutral External Sync Run Contract — Functional

## Metadata

- ID: `eval-0045-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260723-50`
- Attempt: `2`
- Feature: [feat-0045-provider-neutral-external-sync-run-contract](../feature/feat-0045-provider-neutral-external-sync-run-contract.md)
- Spec: [spec-0045-provider-neutral-external-sync-run-contract](../spec/spec-0045-provider-neutral-external-sync-run-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: preparation and authorization → Claude/Codex runtime → terminal recovery and regression
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated preparation, compatible startup, policy and envelope rejection, source-fact validation, Claude/Codex parity, no-change, partial and total provider failure, invalid model output, missing executor, cancellation, restart, generated artifacts, privacy, and complete regressions.

## Checks And Evidence

- Fourteen focused external-sync tests passed. They cover atomic parent/projection creation, non-external absence, compatible startup, Source Instance deletion with retained Run history, rollback and artifact cleanup, current-policy enforcement, envelope drift, source-fact allowlists, metadata coverage, host-computed hashes, safe errors, model/fact separation, deterministic statuses, command restriction, synthetic Claude and Codex completion, unchanged results, partial and all-failed results, missing executor, invalid model output, cancellation, and selected-runner restart reconciliation.
- Synthetic Claude and Codex process adapters consumed the same logical manifest and returned the same structured summary shape. No external source fact depended on runner-authored prose.
- Mixed target outcomes persisted `partial`; all unsuccessful targets persisted `failed`; successful unchanged targets persisted `completed` without inventing changed content.
- Direct manifest or envelope drift, stale capability, denied operations, invalid facts, missing executor, and invalid model output failed closed with bounded application errors.
- Existing parser, Session, Usage, retrieval, checkpoint, Workstream, Runner, schema-migration, and UI regressions passed in the complete repository suite.
- Schema owner parity, deterministic presentation, the 364-object cleanup ledger, nine Mermaid diagrams, repository privacy, Python compilation, and whitespace checks passed.

## Evidence

- Environments checked: fresh and upgraded SQLite, temporary private Run roots, synthetic read executors, synthetic Claude and Codex subprocesses, cancellation and startup reconciliation, generated artifacts, and the complete local suite.
- The complete Python suite passed 204 tests.

## Evidence Gaps

- None for the approved synthetic foundation contract.
- Live company Gateway transport, live Jira or Confluence content, real model billing, Item persistence, and UI behavior were not exercised because FEAT-0045 does not own those outcomes.

## Findings

- None remaining.

## Regression Notes

- Existing non-external maintenance tasks retain their Claude-only execution behavior. One pre-existing Starlette template deprecation warning remains unrelated and non-blocking.

## Route

- Next action: `pass` and return FEAT-0045 to the Orchestrator for human acceptance; keep FEAT-0046 draft until separately approved.
