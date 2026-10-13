# Contract Evaluation: Natural Search Ranking Precision

## Metadata

- ID: `eval-0122-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-159](../run/run-20261012-159-natural-search-ranking-precision.md)
- Feature: [FEAT-0122](../feature/feat-0122-natural-search-ranking-precision.md)
- Spec: [SPEC-0122](../spec/spec-0122-natural-search-ranking-precision.md)
- Execution Profile: `backend-product`
- Created: `2026-10-12`

## Checked Contracts

- Original query/model instruction, fragment/input identity, normalized vectors,
  source eligibility, current revision and conservative conditions are unchanged.
  No source schema, model asset, document embedding or durable profile migration.
- The `hybrid` command/API name remains accepted. Ordering is now raw cosine,
  with the existing literal single-identifier exception below semantic cutoff.
  `ranking` identifies the policy; it is not shown as user-facing probability.
- Exact candidates and lexical-only candidates now apply the already-computed
  scope/current-revision set before the500-fragment cap using bound parameters.
  Unit coverage has more than500 otherwise higher-ranked excluded fragments.
- Parent score uses the strongest eligible span. Repeated identical fragments
  neither sum scores nor fill three evidence slots. Ties remain parent/fragment
  stable and pagination preserves the same order, query and conditions.
- Evidence addresses, current-generation refusal, no remote fallback, permission
  exclusions and old keyword search retain their contracts. The existing full
  unit/HTTP suite is reused with new bounded ranking tests.
- Historical RRF has a development-only comparator. The deployed application has
  one common policy, no per-user topic table, no hidden private names and no
  automatically collected query history. User-supplied private topic expectations
  and analyst-resolved IDs stay in the existing private Development owner.
- Current policy/architecture/setup docs and PRD decision state supersede RRF
  explicitly; the previous evaluation remains historical evidence with a link.

## Evidence And Limits

Actual Qwen checks use identical synthetic fragments and compare the full engine
order with the independently reconstructed zero-bonus candidate order for all88
queries. The new held-out fixture hash matches the pre-observation frozen source.
Private rank/timing comparisons observed unchanged source/index stamps and zero
document encodings. Runtime results and quality limitations belong to the
[functional report](eval-0122-functional-natural-search-ranking-precision.md).
This pass establishes contract preservation, not perfect semantic relevance.
No new visual/interaction contract or reusable design rule was introduced.
