# SPEC-0121: Natural Search Local Comparison

## Metadata

- ID: `spec-0121`
- Status: `approved`
- Run: [RUN-158](../run/run-20261012-158-natural-search-local-comparison.md)
- Attempt: 1
- Feature: [FEAT-0121](../feature/feat-0121-natural-search-local-comparison.md)
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Execution Profile: `infra-devtool`
- Required Evaluators: contract, functional
- Created: `2026-10-12`

## Goal And Fixed Comparison Boundary

Measure the actual approved retrieval path on this Apple Silicon Mac. Product
and UI contracts have passed synthetic checks. Do not infer Korean quality from
them. Public authored fixtures, scripts and aggregate conclusions belong in Git;
private corpus measurements and any private review remain in the configured
Development archive. Shared pretrained weights stay in the public Hub cache.

## Work And Ownership

- Add a reproducible synthetic benchmark corpus/query/relevance manifest with
  multiple relevant parents, Korean paraphrases, English/code identifiers,
  explicit/ambiguous conditions, distractors, no-answer and long-tail evidence.
- Run Qwen embeddings at target256/512/768 and dimension512/1024. Truncation of
  normalized full-dimension vectors followed by renormalization is valid only
  for the pinned Matryoshka model; record this reuse in comparison evidence.
- Report old keyword search, new lexical, dense and hybrid at cutoffs including
  0.7. Metrics: parent Recall@10, Hit@10, nDCG@10, returned precision, answerable
  empty rate and no-answer false positive. Candidate limits are separate.
- Compare multilingual Laya and Qwen Reranker on identical frozen text candidates;
  also report lexical+Laya candidate recall and full path latency. Test K10/20/50.
  Use installed public checkpoints without personal fine-tuning. Record exact
  revisions, runtime, device, dtype, input budget and truncation/rejection counts.
- Additional model dependencies live in an isolated development environment;
  do not silently upgrade the app runtime. Install only public packages/assets.
  Model inference is offline. An unavailable model gets a bounded evidence gap,
  not invented accuracy or a win for another model.
- Finish the complete eligible private index, record full/allocated/peak generation
  bytes and process memory, validate unchanged-input reuse and current-source
  exclusions. Private titles and snippets stay out of tracked reports.
- Measure cold load, warm new/repeat queries, candidate retrieval/reranking and
  end-to-end search separately. Synchronize completed MPS work. Pause task-owned
  preparation for uncontended model measurements and report the pause separately
  from initial-index wall time. Resume it and measure foreground/background contention.
- Select and document a common internal default from observed recall/cost tradeoffs;
  retain a truthful empirical limitation for untested personal corpora.
- Finish full regression, generated-owner consistency, privacy and standalone
  package/resource checks. No commit, push or public release is included.

## Reporting And Exit

Publish reproducible synthetic aggregate evidence and exact commands; keep private
measurement receipts under their durable private owner. Distinguish completed
contract tests, actual-model observations, source coverage and any remaining
quality/resource limitations. A failed model candidate can be rejected while the
working retrieval configuration passes; missing necessary evidence remains open.
