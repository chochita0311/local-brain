# RUN-20260724-60: Data Model Value Dictionary Baseline

## Metadata

- ID: `run-20260724-60`
- Status: `passed`
- Feature: [feat-0057-data-model-value-dictionary-baseline](../feature/feat-0057-data-model-value-dictionary-baseline.md)
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Active Spec: [spec-0057-data-model-value-dictionary-baseline](../spec/spec-0057-data-model-value-dictionary-baseline.md)
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal And Selected Loop

- Establish a complete executable value contract before changing any visible consumer.
- Route: `Orchestrator → Spec Agent → contract Builder → Contract Evaluator → Functional Evaluator`.

## Delivered Baseline

- Nine subject owners and nine generated subject dictionaries.
- `54` included families and `10` explicit exclusion groups.
- Every physical SQLite `IN(...)` vocabulary is owned exactly once and matches the registry.
- Ten relevant boolean-like fields are included.
- Required application-stored and derived inventories are checked.
- Visible families use complete logical labels; technical families are wholly `internal-only`.
- Current visible consumers are declared as `pending-normalization`, preserving FEAT-0061 as a separate product boundary.
- Runtime lookup reads package JSON, rejects internal families, and never parses Markdown.

## Current Artifacts

- Spec: [spec-0057-data-model-value-dictionary-baseline](../spec/spec-0057-data-model-value-dictionary-baseline.md)
- Contract evaluation: [eval-0057-contract-data-model-value-dictionary-baseline](../evaluation/eval-0057-contract-data-model-value-dictionary-baseline.md) — `PASS`
- Functional evaluation: [eval-0057-functional-data-model-value-dictionary-baseline](../evaluation/eval-0057-functional-data-model-value-dictionary-baseline.md) — `PASS`
- Fix log: not created

## Evaluation Coverage

- Contract: complete physical, stored, boolean, derived, exclusion, mode, mapping, navigation, and ownership coverage.
- Functional: complete loader, fallback, generated-byte, drift-failure, consumer-declaration, Data Model, Schema Presentation, and Mermaid regression coverage.

## Verification Evidence

- `15` focused value-registry, Data Model, and Schema Presentation tests passed.
- Value-registry build check passed.
- Data Model parity passed with 34 ordinary tables, one FTS5 object, 39 physical FKs, 33 explicit indexes, and nine subject owners.
- Schema Presentation was regenerated after subject-document source hashes changed and then passed freshness.
- All nine Data Model Mermaid definitions parsed.
- `schema.sql` and `db.py` remained unchanged.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: executable registry and generated dictionaries delivered without a physical data-model change.
  - notes: one expected Schema Presentation stale result was resolved by rebuilding its documentation-derived manifest.

## Post-Contract Regression Check

- Needed: yes.
- Result: passed.
- Notes: schema presentation and Mermaid parse checks confirm the new reciprocal links did not invalidate the existing read-only Schema contract.

## Human Review Outcome

- Decision: automatic sequential approval authorized on `2026-07-24`.
- Returned layer if any: none.
- Follow-up run: FEAT-0058.

## Continuity Notes

- `2026-07-24`: selected generated Markdown as the readable projection so registry and documentation cannot become independent mapping authorities.
