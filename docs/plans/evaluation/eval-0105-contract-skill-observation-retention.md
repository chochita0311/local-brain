# EVAL-0105 Contract: Skill Observation And Retention

## Metadata

- ID: `eval-0105-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-20260928-123](../run/run-20260928-123-skill-observation-retention.md)
- Attempt: `2`
- Feature: [FEAT-0105](../feature/feat-0105-skill-observation-retention.md)
- Spec: [SPEC-0105](../spec/spec-0105-skill-observation-retention.md)
- Execution Profile: `foundation-contract`
- Lane: `data`
- Created: `2026-09-28`

## Evidence And Finding

- `skill_observations` stores bounded native identity, source, name, time, signal kind, and validity state without prompt or skill content. It has no cascading Session or source foreign key. The source-scoped native-event guard prevents replay after name normalization changes.
- Source parser versions trigger Session extraction backfill. The scanner inserts observations in the source transaction and preserves them after normal source disappearance. Maintenance reclassification corrects affected rows; a targeted native-event operation can correct a proven erroneous observation even after its Session disappears. Current-file coverage is separate from an observed zero.
- A fresh schema and a compatible file-database startup expose the ledger and its indexes. The startup case preserved a pre-existing Session row; the schema-doc checker matched all 44 ordinary tables and 51 explicit indexes with their owners.
- Existing Usage Record pricing and first-page Usage & Cost queries remain outside the new ledger path. The owner data-model and product contracts match the implemented correction and retention behavior.

## Limit And Route

Complete coverage applies to the approved, synthetic foundation contract. No private corpus migration or personal-improvement model Run was performed. No unresolved contract blocker remains; route `pass`.
