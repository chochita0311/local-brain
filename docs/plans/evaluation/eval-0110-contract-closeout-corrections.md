# EVAL-0110 Contract: Closeout Corrections

## Metadata

- ID: `eval-0110-contract-closeout-corrections`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-137](../run/run-20261002-137-insight-closeout-corrections.md)
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md#approved-closeout-corrections)
- Execution Profile: `fullstack-product`
- Surface Lane: `data`, `backend`, `frontend`
- Created: `2026-10-02`

## Evidence

Five focused pricing tests cover exact GPT-6.1 Sol rates, release-date boundaries, Standard/Fast selection, the 272,000-token boundary, per-request pricing, scoped backfill, retained evidence, repeat startup and the existing Spark proxy. Independent arithmetic verifies the cached-input discount and full-request context multipliers. Comparing every pre-existing price specification against the pre-change source confirms no historical rate or snapshot definition changed.

The Run cost read model uses the stable accounting identity and stored snapshot; it never reprices on GET. Synthetic rendered-route checks cover priced, zero, tiny positive, unknown-price, partial, failed and absent usage, plus a separately labeled CLI amount. Database change counts remain unchanged after reads.

The six old Usage expectations now use dated snapshots and explicit Fast fixtures where Fast behavior is intended. Schema and consumer baselines match 45 objects, 515 columns, 51 indexes and 57 physical/28 application relations. The value registry retains its already-existing 72 families and registers the new presentation consumer. Public citation URLs are pinned individually; private/runtime URLs remain excluded under the updated [schema owner](../../policies/project/schema-presentation.md#privacy-and-packaging).

Real-data application preserved all other usage, historical pricing and product Run rows. It changed only eligible previously unpriced exact-model records, with an owner-only before-image backup and independent per-row arithmetic. A repeat backfill changed zero rows. No schema migration, Session ingestion or provider call was introduced.

## Limits

API-equivalent estimates do not verify provider invoices. Unknown tiers, pre-release dates and insufficient retained components remain unavailable. Those boundaries are intentional and do not block this correction.
