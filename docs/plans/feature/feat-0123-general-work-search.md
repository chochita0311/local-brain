# FEAT-0123: General Work Search

## Metadata

- ID: `feat-0123`
- Status: `passed`
- Type: `product`
- Surface: `backend`
- Execution Profile: `backend-product`
- Required Evaluators: contract, functional
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Created: `2026-10-13`
- Approval: the owner requested overall improvement as a general work search engine, continuing the approved implementation and local testing boundary.

## Goal And Boundary

Improve useful top results and coverage across work domains: implementation,
delivery, data, user interfaces, operations and documentation as well as security.
Evaluate broad purposes, unnamed projects, conversational requests and ambiguous
terms together. Zero false positives and perfect classification are not goals.

Compare the current cosine ranking with bounded query-time representations that
retain the original query and add a conservative topic-focused view. If admitted,
use common language rules rather than private names, topic synonym dictionaries,
personal training or hidden project/recency filters. Preserve original conditions,
source eligibility, provenance, index compatibility and the keyword search.

No new UI, corpus, cloud service, implicit download, mandatory additional model,
query logging or publication. A ranking change must earn its query-time cost.
Keep broad retrieval available; do not remove sources merely to improve precision.

## Evaluation

One sequential backend lane, owned by the primary agent. Author development and
separate held-out multi-domain fixtures before observing model results. Freeze the
selected method before opening the new holdout. Existing sets are regression data.
Report useful Hit@1/3/10, Recall@10, nDCG@10, topic coverage for broad queries,
per-query regressions and warm latency. Private observations use the existing local
Development archive and distinguish analyst judgments from user expectations.
Mechanical checks do not establish model quality. No personal accuracy guarantee.

- Spec: [SPEC-0123](../spec/spec-0123-general-work-search.md)
- Run: [RUN-160](../run/run-20261013-160-general-work-search.md)
- Evaluations: [contract](../evaluation/eval-0123-contract-general-work-search.md)
  PASS; [functional](../evaluation/eval-0123-functional-general-work-search.md)
  PASS WITH SUGGESTIONS. First-result usefulness improves on broad development
  queries; some recall/order regressions and unchanged held-out quality remain
  explicit. This is a bounded implementation pass, not universal personal quality.
