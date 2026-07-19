# EVAL-0035: Maintenance Session Usage Bridge — Contract

> Historical evidence only: human review later invalidated the stream-backed producer assumption. FEAT-0036/RUN-41 supersede that producer contract while retaining the schema-constraint evidence.

## Metadata

- ID: `eval-0035-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260719-40`
- Attempt: `1`
- Feature: [feat-0035-maintenance-session-usage-bridge](../feature/feat-0035-maintenance-session-usage-bridge.md)
- Spec: [spec-0035-maintenance-session-usage-bridge](../spec/spec-0035-maintenance-session-usage-bridge.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Session schema and migration → Runner producer → consumers → current-truth artifacts
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated the approved one-Run/one-Maintenance-Session identity, Session classification constraints, stream Usage producer, and work-consumer exclusion boundary. The separate compatible `maintenance_runs.workstream_id` repair remains outside this Feature.

## Checks And Evidence

- Fresh DDL and compatible repair enforce `work | maintenance`, `full | metadata_only`, a nullable `ON DELETE SET NULL` Run FK, one non-null Run link, and the primary metadata-only linked-row shape.
- Legacy fixtures refuse invalid class/policy values, orphan and duplicate Run links, invalid linked-row shape, and unexpected column metadata before rebuilding. Valid rows and dependent Activity Event and Usage Record rows remain exact; older additive column order converges by name without value coercion.
- The migration backup is created before structural change, passes `quick_check`, is never overwritten, and repeated startup is idempotent.
- Runner preparation creates exactly one linked Maintenance Session. Assistant usage wins over final-result aggregates; result model usage is a bounded fallback; completed, failed, cancelled, interrupted, historical, missing, and malformed stream states are covered without invented counters.
- Scanner and source-level Usage repair preserve Runner-owned rows. Activity Events and search rows remain empty, retrieval admits only primary work Sessions, and Dashboard totals include direct Maintenance Usage while the primary-work Session denominator excludes it.
- Data Model ownership now reports 20 physical foreign keys. The deterministic Schema presentation and 329-object cleanup ledger are current at `keep 272`, `change 2`, `remove 0`, `defer 55`.

## Actual Runtime Evidence

- Preflight found 171 valid work Sessions, 11,734 Usage Records, six Run rows, two in-app Run identities, and zero invalid, duplicate, orphan, or mismatched links.
- Startup created and validated the non-overwriting Maintenance Session contract backup. After migration there are 173 Sessions: the original 171 work Sessions plus two linked metadata-only Maintenance Sessions.
- Bidirectional comparison against the backup found zero differences across the original Session rows and zero Activity Event differences. `foreign_key_check` returned zero errors and both databases passed `quick_check`.
- The two historical Run paths no longer have stream files or parent artifact directories. The producer therefore created metadata-only Sessions but correctly left Usage Records at 11,734 instead of inventing historical token data.

## Evidence Gaps

- No retained historical Runner stream remained for an actual-runtime token backfill. This is bounded missing-source state, not contract failure; synthetic assistant/result streams cover normalization, pricing, Dashboard eligibility, and idempotency.

## Findings

- None.

## Route

- Next action: `pass` and request human owner acceptance.
