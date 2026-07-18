# EVAL-0023: Usage Breakdown And Trust Contract

## Metadata

- ID: `eval-0023-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-23`
- Attempt: `1`
- Feature: [feat-0023-usage-breakdown-and-trust](../feature/feat-0023-usage-breakdown-and-trust.md)
- Spec: [spec-0023-usage-breakdown-and-trust](../spec/spec-0023-usage-breakdown-and-trust.md)
- Execution Profile: `fullstack-product`
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Checks

- Verified `breakdown=source|model|project` normalization and preservation across every FEAT-0022 scope control.
- Verified compatible token and priced-cost denominators, group shares, primary-work Session counts, last activity, raw-model traceability, and eight-row initial disclosure.
- Verified Project grouping consumes immutable fact snapshots and current workspace data only enables a browse link.
- Verified Source, Model, Project, Unknown model, Unassigned, partial price, stale, error, and retained-valid-data states.
- Verified trust ownership for last healthy source evidence, selected source coverage, calculation state, last calculation, and immutable price labels.

## Evidence

- Synthetic fixtures reconcile Codex 510 and Claude 170 tokens to the selected 680-token total and 75/25 percent shares.
- An aliased raw model remains inspectable under its normalized model group.
- A current workspace rename did not alter the historical `Original name` Project group.
- Ten added model identities produced eight primary rows and a bounded overflow disclosure.
- A synthetic source-file error retained usage, reported error state, and preserved the prior healthy timestamp without exposing the raw error.
- All 68 tests, compilation, diff, and repository privacy checks passed.

## Findings

- No remaining grouping, denominator, provenance, or trust-state contract defect was found.

## Route

- Next action: `pass`
