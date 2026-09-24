# EVAL-0101: Full-History Affinity Inspection — Contract

- ID: `eval-0101-contract`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `complete`
- Feature: [FEAT-0101](../feature/feat-0101-full-history-affinity-inspection-contract.md)
- Spec: [SPEC-0101](../spec/spec-0101-full-history-affinity-inspection-contract.md)
- Run: [RUN-114](../run/run-20260923-114-full-history-affinity-inspection.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, `infra`
- Attempt: `1`
- Created: `2026-09-23`

The read adapter preserves the single finite simulation owner and source binding,
uses shared locking without renewal/deletion, validates full-population freshness,
and exposes only snapshot-scoped inferred affinity. All duplicate occurrences and
multi-group Sessions remain reachable. Exact evidence independently verifies
identity, eligibility, role, time, offsets and revision. Corrupt, expired, changed
and missing source states fail closed. No model, source ingestion, new persistence
or organization writes exist in the consumer. Thirteen synthetic tests and an
actual readiness/exact-evidence probe pass. RUN-113 closes actual replay and
source-byte immutability. No semantic-quality or UI acceptance is implied.
