# EVAL-0047: Bounded Atlassian URL Evidence Extraction — Functional Attempt 1

## Metadata

- ID: `eval-0047-functional-attempt-1`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `FAIL`
- Failure Classification: `implementation bug`
- Run ID: `run-20260723-52`
- Attempt: `1`
- Feature: [feat-0047-bounded-atlassian-url-evidence-extraction](../feature/feat-0047-bounded-atlassian-url-evidence-extraction.md)
- Spec: [spec-0047-bounded-atlassian-url-evidence-extraction](../spec/spec-0047-bounded-atlassian-url-evidence-extraction.md)
- Execution Profile: `foundation-contract`
- Surface Lane: source-backed reconciliation
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Finding

- One normalized Session may be contributed by multiple JSONL files. The initial evidence-scan implementation allowed only one scan row per Session, so the second file replaced the first file's fingerprint and the next unchanged synchronization reparsed both files.
- This contradicted the approved changed-input/idempotency contract but did not change the Feature or Spec boundary.

## Evidence

- Failing regression: `tests.test_usage_contract.UsageContractTests.test_source_contract_repair_reconciles_union_across_shared_session_files`.
- Observed result: `(imported=2, skipped=0, failed=0)` instead of `(0, 2, 0)` on the unchanged post-repair scan.

## Route

- Next action: Fix Agent; make Session evidence scan/sighting identity source-file-aware without weakening Session ownership.
