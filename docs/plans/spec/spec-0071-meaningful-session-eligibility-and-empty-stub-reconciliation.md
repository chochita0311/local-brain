# SPEC-0071: Meaningful Session Eligibility And Empty Stub Reconciliation

## Metadata

- ID: `spec-0071`
- Status: `approved`
- Run ID: `run-20260803-80`
- Attempt: `1`
- Parent Feature: [feat-0071-meaningful-session-eligibility-and-empty-stub-reconciliation](../feature/feat-0071-meaningful-session-eligibility-and-empty-stub-reconciliation.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Surface: `backend`
- Execution Profile: `backend-product`
- Surface Lanes: eligibility → reconciliation → owner docs
- Required Evaluators: `contract`, `functional`
- Created: `2026-08-03`
- Updated: `2026-08-03`

## Implementation Goal

- Evaluate meaningful eligibility after provider parsing but before normalized
  storage, while repairing legacy empty rows without weakening current source
  transaction, freshness, Usage-union, or unavailable-root contracts.

## In-Scope Behavior

- A shared predicate returns eligible when `parsed.events` or
  `parsed.usage_records` is non-empty.
- An existing `index_policy = full` Session with zero stored Events and no Usage
  triggers one source-level eligibility repair pass so current sibling files are
  reparsed before an ambiguous shared native identity can be removed.
- Parsed empty candidates are not stored and are collected for end-of-source
  reconciliation after successful file handling.
- Reconciliation removes candidate-path evidence and source-file state, then
  removes the matching Session only when its final normalized row still has zero
  Events and no Usage. Search removal precedes Session deletion; physically owned
  rows cascade while a Session self-reference follows its existing `SET NULL`
  contract.
- Ignored empty files are not persisted as current source files, so they are
  inspected again on later syncs and become importable after file growth.
- Contract-repair failure rolls back the source and does not apply empty-stub
  cleanup from an unsuccessful replacement.

## Out-Of-Scope Behavior

- Provider parser record mappings, Usage normalization, path candidate discovery,
  schema additions, UI filtering, raw-source deletion, and retention controls.

## Acceptance Mapping

- Current metadata-only stub → full repair, normalized removal, raw preservation.
- Repeated unchanged stub → no normalized row, no tracked row, no failure.
- Appended message/usage → normal import on next sync.
- Shared identity safety → final-row meaningful check after sibling reparsing.
- Maintenance/tool/usage-only preservation → pre-store parsed evidence predicate.
- Unavailable/config failure → scanner never enters cleanup transaction.

## Evaluation Focus

- No meaningful Session is lost through path or external-ID ambiguity.
- Cleanup leaves no search, source-file, or evidence residue.
- Report counts and empty/completed source status remain truthful.
- Native file bytes and timestamps are never changed by LocalBrain.

## Open Blockers

- None.
