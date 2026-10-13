# RUN-158: Natural Search Local Comparison

## Metadata

- ID: `run-20261012-158`
- Status: `passed`
- Feature: [FEAT-0121](../feature/feat-0121-natural-search-local-comparison.md)
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Active Spec: [SPEC-0121](../spec/spec-0121-natural-search-local-comparison.md)
- Execution Profile: `infra-devtool`
- Required Evaluators: contract, functional
- Created: `2026-10-12`

## Selected Loop

Attempt 1. Primary prepares authored fixtures and pinned local measurement tools,
executes comparisons and validates integrated behavior. Actual private full-index
preparation started during engine work and completed locally. No delegated workers.

## Evaluation And Outcome

- [Contract](../evaluation/eval-0121-contract-natural-search-local-comparison.md): PASS.
- [Functional](../evaluation/eval-0121-functional-natural-search-local-comparison.md):
  PASS WITH SUGGESTIONS, complete evidence for this bounded comparison.
- Compared old keyword, lexical, Qwen dense/hybrid, six size/dimension profiles,
  cosine cutoffs including0.7, identical-candidate multilingual Laya/Qwen Reranker
  and actual combined pipelines. The admitted default is512-token bodies,
  dimension512, overlap0, float32 batch8, hybrid cosine cutoff0.45.
- Completed full eligible private indexing and exact original-character coverage;
  measured cold/warm/ASGI latency, unchanged reuse and a separate full-size
  generation rebuild including sampled SQLite workspace. Private raw evidence,
  diagnostic queries and method snapshots stay under the Development owner.
- Frozen authored holdout, actual foreground/background MPS contention, full
  1,106-test regression, rendered synthetic UI and independent installed-wheel
  checks (both base-only and actual local-model inference) passed their checks.
- Corrected tokenizer state sharing, bounded cached replay, clear/ambiguous
  independent conditions, empty-corpus loading, coverage accounting and query
  failure presentation during integration. Rejected non-finite judge attempts
  and recorded admitted float32/eager conditions separately.

## Limits, Review And Route

Returned precision and some homonym/lexical ordering remain quality improvement
candidates. The held-out result was not used to retune the frozen default; private
spot checks are analyst observations, not human labels. No whole-corpus semantic
quality guarantee, other-device validation or Windows release is implied.

No additional reusable design/interaction rule was identified beyond existing
policies. The approved implementation and test work is complete. Human review can
use the parallel inputs to identify concrete misses/false positives before a new
ranking/cutoff change; this technical pass does not assert that review occurred.
No commit, push or publication was performed.
