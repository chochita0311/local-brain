# RUN-159: Natural Search Ranking Precision

## Metadata

- ID: `run-20261012-159`
- Status: `passed`
- Feature: [FEAT-0122](../feature/feat-0122-natural-search-ranking-precision.md)
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Active Spec: [SPEC-0122](../spec/spec-0122-natural-search-ranking-precision.md)
- Execution Profile: `backend-product`
- Required Evaluators: contract, functional
- Created: `2026-10-12`

## Selected Loop

The human requested precision improvement following the completed comparison.
Primary performs diagnosis, freezes authored examples, compares candidates, then
implements/evaluates an admitted ranking change. No delegation. The previous
comparison remains historical evidence; this is a new bounded execution pass.

## Evidence Ownership And Current Route

Synthetic fixtures and aggregate report belong in the repository. Explicit private
observations and runtime receipts belong in the existing Development archive under
`natural-search/precision-v1`. Temporary indexes and task-owned scratch were removed
after the measurement receipts and final verification logs were preserved. The
intended local application server remains running. No commit or publication.

## Outcome And Evaluation

- [Contract](../evaluation/eval-0122-contract-natural-search-ranking-precision.md):
  PASS, complete evidence for the bounded ranking/compatibility contract.
- [Functional](../evaluation/eval-0122-functional-natural-search-ranking-precision.md):
  PASS WITH SUGGESTIONS. Compared 88 authored queries across development, previous
  selection, previous observed holdout and a newly frozen holdout. The selected
  policy improves aggregate ordering and retains recall on each set; individual
  synthetic/private regressions and no-answer errors remain explicit.
- Replace RRF with cosine ordering plus the original exact-identifier admission.
  Keep model, source/input identity and cutoff 0.45. Filter before the lexical 500
  candidate cap. No new model or document re-embedding; private comparison observes
  unchanged original DB/index stamps and zero document encodings.
- Private comparison: seven explicit queries, 21 warm uncached calls per mode,
  alternating order. The new median/p95 are shorter. User topic expectations are
  recorded separately from analyst-resolved representative source IDs. No complete
  private human relevance set is claimed.
- Final full regression: 1,110 tests, 21.098s, OK; 34 natural-search unit/HTTP checks.
  A new test initially used an unsuitable unknown-query vector from the fake
  encoder; the test now fixes the orthogonal vector explicitly. The final full run follows the correction.
- Restarted the idle local server with the existing environment and loopback port;
  canonical data/index remain in their existing owners. Browser form submission,
  current order, explicit kind filters, no error/overflow, source anchor/return
  link and old search200 all verified. No console errors/warnings.
- Repository privacy check passed for 1,283 candidate files; whitespace passed
  and the generated plan catalog is current. No independent package rebuild was needed or claimed for this
  query-time-only change. Previous package evidence remains historical.

## Review And Remaining Route

The authorized implementation/comparison work is complete. Broad-topic coverage,
real homonym false positives and individual rank regressions remain improvement
candidates; do not present the aggregate pass as universal Korean/personal accuracy.
Further query reformulation or an additional candidate judge needs a new measured
comparison with latency, missed-source and no-answer effects. No new UI, automatic
feedback collection or personal training has been introduced. No reusable design
or interaction policy candidate arose. Human relevance review can continue in the
parallel search UI; no new approval is needed to use the implemented search.
