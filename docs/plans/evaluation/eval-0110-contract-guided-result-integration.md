# EVAL-0110 Contract: Guided Result Integration

## Metadata

- ID: `eval-0110-contract-guided-result`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete` for the synthetic integration contract
- Run: [RUN-20260928-122](../run/run-20260928-122-guided-personal-insight-result-integration.md)
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Execution Profile: `fullstack-product`
- Lane: `data`, `backend`
- Created: `2026-09-28`

## Evidence And Finding

- Inspected the new guide package, `prepare_insight_run`, per-Run schema generation, result validation, private artifact writes, and report rendering. Version and digest provenance are frozen before launch; the exact selected guide text remains in the private prompt. The v1 resource is historical and is not read by new Runs.
- The validator permits only selected type IDs and frozen evidence IDs, requires a documented disconfirming check, rejects overlapping support and counterexample references, and requires two distinct Sessions for recurrence. It assigns a deterministic ID to an exact accepted finding value and never marks an outcome owner-confirmed.
- The report renderer receives only an exact set of `/sessions/{positive integer}` links from the frozen manifest. The shared renderer defaults to unresolved local links for other consumers and rejects arbitrary route allowlist entries. The report and validated JSON stay under the private Run artifact root; only Markdown is a user-facing download.
- The table shape and independent Run identity are unchanged. A `needs_evidence` result is a terminal `no_finding` row with a distinct evidence request in the report; this limitation is explicit and no new status or migration is claimed.

## Limit

No model response, provider entitlement, or private Session corpus was observed. The contract inspection establishes the local acceptance and provenance boundary, not semantic accuracy of generated suggestions.
