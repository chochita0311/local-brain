# FEAT-0071: Meaningful Session Eligibility And Empty Stub Reconciliation

## Metadata

- ID: `feat-0071`
- Status: `passed`
- Type: `product`
- Surface: `backend`
- Execution Profile: `backend-product`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Created: `2026-08-03`
- Updated: `2026-08-03`

## Goal

- Keep accepted native JSONL that contains only metadata and no observable Session
  activity out of normalized Session data, and reconcile any prior empty stub
  during successful synchronization without deleting the native file.

## Acceptance Contract

- A parsed local AI Session is meaningful when it contains at least one normalized
  Activity Event or at least one direct Usage Record.
- Metadata, title, name, timestamp, cwd, branch, or native identity alone does not
  make a Session meaningful.
- New empty stubs create no Session, Activity Event, Usage Record, search row,
  Atlassian evidence projection, pin, or tracked Session-source file row.
- A successful readable-source sync removes an existing empty normalized Session
  and its owned projections plus its source-file evidence. The native JSONL stays
  untouched and is inspected again on later syncs.
- If that JSONL later gains an Event or Usage Record, the next sync imports it as
  a normal Session.
- Existing meaningful primary, Subsession, Maintenance, tool-only, and usage-only
  records remain eligible. Source unavailability or configuration failure remains
  non-destructive.
- Session inventory, Projects, Usage-linked Session counts, source health, and
  tracked-file counts derive naturally from the reconciled normalized state.

## Scope Boundary

- In:
  - provider-neutral post-parse meaningful-Session eligibility
  - one-time repair of current empty full-index Session rows
  - source-file, search, evidence, child, Usage, and pin lifecycle cleanup through
    existing ownership boundaries
  - native-file preservation and later-growth re-import
  - synthetic and private read-only/runtime verification
- Out:
  - non-Session path discovery already corrected by FIX-0068
  - native Claude/Codex deletion or retention configuration
  - archive, tombstone, restore, warning, or pin override behavior
  - Session list layout, source cues, controls, or detail presentation
  - changing what parser record types become Activity Events or Usage Records

## Contract Surfaces

- `ParsedSession.events` and `ParsedSession.usage_records` eligibility boundary
- source-file freshness and one-time repair detection
- normalized Session/source-path deletion ownership
- source sync report eligible/tracked counts

## Required Evaluators

- `contract`: eligibility definition, source/non-source distinction, ownership,
  deletion authority, original-file preservation, and owner-doc alignment.
- `functional`: new stub, existing stub, repeated sync, later file growth,
  meaningful primary/child/Maintenance/tool/usage preservation, unavailable-root
  retention, and full regressions.

## Pass Or Fail Checks

- Pass if an existing metadata-only Session disappears after successful sync while
  its JSONL remains, then reappears when meaningful source content is appended.
- Pass if a new metadata-only file never creates Session or source-file state.
- Pass if meaningful Event-only or Usage-only files remain imported.
- Pass if unavailable/configuration failure cannot invoke this cleanup.
- Fail on UI-only hiding, raw-file deletion, provider-specific divergence, or
  removal of a meaningful Session.

## Harness Trace

- Active spec: [spec-0071-meaningful-session-eligibility-and-empty-stub-reconciliation](../spec/spec-0071-meaningful-session-eligibility-and-empty-stub-reconciliation.md)
- Active run: [run-20260803-80-meaningful-session-eligibility-and-empty-stub-reconciliation](../run/run-20260803-80-meaningful-session-eligibility-and-empty-stub-reconciliation.md)
- Latest evaluator reports:
  - [Contract](../evaluation/eval-0071-contract-meaningful-session-eligibility-and-empty-stub-reconciliation.md): `PASS`
  - [Functional](../evaluation/eval-0071-functional-meaningful-session-eligibility-and-empty-stub-reconciliation.md): `PASS`
- Latest fix note: none

## Continuity Notes

- `2026-08-03`: owner distinguished a valid top-level metadata stub from the
  workflow-journal discovery bug, then approved sync-time normalized cleanup when
  both Events and Usage are absent.
- `2026-08-03`: RUN-20260803-80 passed with 326 repository tests and actual
  Claude cleanup/idempotence evidence; Sessions 137 and 209 are removed from the
  runtime DB while both native files remain.
