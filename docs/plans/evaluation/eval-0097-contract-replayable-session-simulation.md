# EVAL-0097: Replayable Session Simulation — Contract

## Metadata

- ID: `eval-0097-contract`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-113](../run/run-20260923-113-full-history-simulation-replay.md)
- Attempt: `2`
- Feature: [FEAT-0097](../feature/feat-0097-replayable-session-simulation.md)
- Spec: [SPEC-0097](../spec/spec-0097-replayable-session-simulation.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, `infra`
- Created: `2026-09-22`

## Findings

- Every stored Session is accounted for, including missing-source, excluded and
  empty Sessions. Synthetic coverage exceeds 60 Sessions, 32 messages and the
  former message-prefix cap. Unknown timestamps do not suppress input.
- Full character coverage and exhaustive token windows are independently
  checked. User/assistant attribution, source hashes and locators remain distinct
  from inferred affinity. No community asserts causality or completion.
- Source is opened read-only, never initialized/migrated. Source bytes remain
  unchanged in synthetic end-to-end runs. Output is a separate private owner;
  unknown directories, symlinks, mismatched DB binding and competing writers fail.
- Content/model/extraction namespaces isolate caches; source changes invalidate
  results and removed/revoked content leaves current inventory/cache. Model
  tampering fails verification before inference. All command output is fixed
  codes unless aggregate reporting is explicitly selected.
- Expiry and purge have exact derived targets and do not remove source data.
  Failed publication preserves a previous report without presenting it as
  current. Status checks expiry, abandonment and source freshness.
- Existing preview caps remain intentionally confined to historical comparator
  modules; the new CLI does not route through those capped contracts. No source
  schema, organization or existing browser behavior changed.

## Earlier Evidence — RUN-103

Twenty new synthetic scenarios pass with the installed semantic runtime; the
full regression suite passes. Real inventory, model execution, committed cache
and interruption/resumption were observed through non-content fixed diagnostics.
The first real full-population report is still computing. Its completed
publication and real-data replay comparisons remain unobserved and prevent
closing the Run. Semantic usefulness is unassessed, not inferred from coverage.

## Current Evidence — RUN-113

The real whole-history report was refreshed incrementally. Actual unchanged and
grouping-only replay both made zero encoding calls; original configuration
restoration reproduced the ordered baseline exactly. Source DB/WAL bytes remained
unchanged. The semantic runtime passes all 23 focused tests; 945 app tests pass
(three optional semantic checks skipped there). The earlier technical evidence
gap is closed, with no semantic-quality or production-replacement claim.
