# SPEC-0122: Natural Search Ranking Precision

## Metadata

- ID: `spec-0122`
- Status: `approved`
- Run: [RUN-159](../run/run-20261012-159-natural-search-ranking-precision.md)
- Attempt: 1
- Feature: [FEAT-0122](../feature/feat-0122-natural-search-ranking-precision.md)
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Execution Profile: `backend-product`
- Required Evaluators: contract, functional
- Created: `2026-10-12`

## Implementation And Measurement Boundary

This is the historical v2 contract. [SPEC-0123](spec-0123-general-work-search.md)
subsequently adds the conservative focused view to the preserved original query
and supersedes the original-only hybrid ordering below. The [search policy](../../policies/project/natural-language-search.md)
owns the current default; v2 remains a frozen comparison baseline.

The existing equal-weight fragment RRF discards cosine distance. In a large corpus,
one parent's numerous fragments also consume ranks before parent grouping. Test a
query-time alternative that keeps cosine as the main score and gives lexical matches
a small bounded bonus; compare a small fixed parameter grid, then freeze one common
choice before evaluating new held-out topics. Keep the old algorithm in the
development comparator, not as an installed compatibility toggle.

Author development fixtures with ambiguous terms, keyword inventories, paraphrases,
mixed languages, original-source filters, no-answer cases and legitimate requests
for lists. Author a separate held-out set before running the model. Freeze expected
parent labels and fixture hashes; do not relabel a model error into a success.
Report Hit@1/3/10, nDCG@10, Recall@10, returned precision and no-answer false positives.
Keep empty/no-answer denominators explicit. Compare the prior selection and observed
holdout as regression sets, retaining all raw per-query results privately.

## Invariants And Tests

- Dense cosine still controls semantic admission; lexical bonus is not probability
  and does not silently lower cutoff. Exact single Latin identifiers retain their
  explicit admission reason even when below semantic cutoff.
- Strong semantic evidence cannot be displaced by unlimited repeated weak lexical
  evidence. Parent score uses the best eligible span; duplicates do not sum scores.
- Kind/date/exclusion filters and source revision checks apply before delivered
  results. A cache-compatible rank-only update must encode no documents.
- No hard-coded private topic names, personal labels in tracked fixtures, new model,
  source edits or query logging. Private supplied expectations are a separate local
  spot check, not a new shared language rule or exhaustive human ground truth.
- Preserve URL shape, fields, pagination, evidence addresses and original search.
- Include deterministic boundary tests plus actual offline Qwen comparisons and
  warm timing. The selected change must retain selection-set Recall@10 and Hit@10
  within two percentage points and improve development-set ordering; otherwise
  keep the current app default and report the rejected experiment.

## Decision Record

Before observing the new holdout, freeze `semantic-cosine-exact-v2`: zero lexical
ranking bonus, cosine ordering, unchanged0.45 admission and exact single-identifier
lexical admission. The fixed bonus grid0/0.03/0.05/0.08 showed no benefit over zero
on the authored development set; zero also had the best prior-selection recall
and nDCG. The `hybrid` CLI/API name remains compatible and now means semantic
ordering with the lexical exact-identifier admission path. Lexical-only comparison
continues to use BM25. Filter lexical candidates before the500-fragment cap, so
excluded/stale parents cannot displace admissible exact evidence.

Keep the original query unchanged in model input. Exploratory shorter-wording
private probes are observations, not a query rewriting rule. Some private expected
sources move down while others move up; this change cannot claim complete topic
understanding or improved ranking for every original source.

Holdout results must be reported even if unfavorable; they cannot be used for
another tuning pass while still called held-out. No UI/design change is planned.
