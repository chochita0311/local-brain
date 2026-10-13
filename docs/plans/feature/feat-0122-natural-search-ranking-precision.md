# FEAT-0122: Natural Search Ranking Precision

## Metadata

- ID: `feat-0122`
- Status: `passed`
- Type: `product`
- Surface: `backend`
- Execution Profile: `backend-product`
- Required Evaluators: contract, functional
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Created: `2026-10-12`
- Approval: human requested continued improvement and tests for the precision and homonym findings after reviewing FEAT-0121.

## Goal And Acceptance Contract

Improve the ordering of relevant original sources without requiring another model,
personal training or a full re-embedding. Compare the unchanged baseline with
bounded lexical support that preserves semantic-score differences. Admit a change
only with measured improvement on authored distractor queries, retained recall on
the existing selection set, and an independently frozen follow-up evaluation.
Report remaining homonym and no-answer failures separately from mechanical tests.

## Scope And Contract Surfaces

- In: query-time ranking, source grouping, exact-identifier behavior, reproducible
  synthetic quality comparisons, explicit private spot checks and regression tests.
- Preserve the model/input/index contract, source eligibility and fresh evidence,
  cutoff0.45, original query, conservative conditions, existing keyword search,
  original-source links, storage boundaries and offline operation.
- Out: new UI, implicit recency interpretation, corpus expansion, private project
  names in shared rules, background query collection, remote inference/publication.
- API/schema consumers remain compatible. Changes need no source edits or index
  migration. The parent result retains up to three distinct original evidence spans.

## Evaluation And Trace

The primary agent performs one sequential backend lane. Contract evaluation checks
admission, stable ordering, duplicate evidence, provenance and index compatibility.
Functional evaluation checks synthetic quality, explicit private observations,
warm query cost, relevant unit/HTTP regressions and the running local route.
Prior held-out data are now regression evidence, not an unseen test. A new authored
set is frozen before model observation; private labels remain analyst judgments
unless a user supplies the expectation. No general personal accuracy guarantee.

- Spec: [SPEC-0122](../spec/spec-0122-natural-search-ranking-precision.md)
- Run: [RUN-159](../run/run-20261012-159-natural-search-ranking-precision.md)
- Evaluations: [contract](../evaluation/eval-0122-contract-natural-search-ranking-precision.md)
  PASS; [functional](../evaluation/eval-0122-functional-natural-search-ranking-precision.md)
  PASS WITH SUGGESTIONS. The new authored holdout and existing regression sets
  retain recall; private individual rank changes include regressions. This is a
  bounded technical pass, not the owner's final personal-quality acceptance.
