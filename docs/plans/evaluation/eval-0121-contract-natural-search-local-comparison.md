# Contract Evaluation: Local Natural Search Comparison

## Metadata

- ID: `eval-0121-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-158](../run/run-20261012-158-natural-search-local-comparison.md)
- Attempt: 1
- Feature: [FEAT-0121](../feature/feat-0121-natural-search-local-comparison.md)
- Spec: [SPEC-0121](../spec/spec-0121-natural-search-local-comparison.md)
- Execution Profile: `infra-devtool`
- Created: `2026-10-12`

## Scope And Contract Evidence

The producer surfaces are the authored benchmark and holdout fixtures, pinned
offline asset loader, retrieval benchmark, isolated judge benchmark, full pipeline
benchmark, refresh/contention measurement and standalone installed-wheel smoke.
Consumers are the selected common profile, installation/development instructions,
private evidence archive and [functional report](eval-0121-functional-natural-search-local-comparison.md).
The evaluated build is the uncommitted working tree for RUN-158; no release or
remote publication is part of this evaluation.

Inspected contracts:

- Corpus and provenance remain owned by the normalized application sources. The
  private search SQLite is rebuildable and introduces no primary DB schema.
  Settings and model registration remain durable; public pretrained assets remain
  shared. No private corpus, query results or learned adapter enters fixtures.
- Input/profile identity includes model revision and asset fingerprint, tokenizer,
  runtime/device/dtype, split/input versions, dimension and query instruction.
  Matryoshka prefix reuse is recorded explicitly in dimension comparisons; mixed
  incompatible indexes are rejected. The final default remains frozen for holdout.
- Old keyword, new lexical, dense and hybrid use the same authored expected parent
  identities. Cutoff, candidate recall, ranking, no-answer behavior and returned
  precision have separate definitions. Cosine cutoff is not applied to RRF scores
  or described as probability. A topK candidate limit is not a corpus limit.
- Both judges consume identical frozen candidate text within each candidate path.
  Full pipeline latency is measured end to end rather than inferred by adding
  independently measured percentiles. Non-finite attempts are rejected; admitted
  dtype/attention/input budgets and zero truncation are reported.
- Optional Laya/reranker dependencies are isolated from the app. Hash verification
  after comparisons confirmed shared public checkpoint assets were unchanged.
  A private compatibility copy absorbs Laya tokenizer metadata changes.
- The installed default depends on Qwen embeddings and local lexical retrieval.
  It contains no personal-project lookup table, implicit model download, external
  inference, generated document hierarchy or automatic source reorganization.

## Checks And Regression Boundaries

The integrated deterministic/HTTP suite contains 30 natural-search checks, covering
complete original spans, permission/revision invalidation, shared-input reuse,
bounded cached replay, interruption, unchanged snapshots, malformed settings,
corrupt-vector recovery, external writer status, empty-corpus model avoidance,
splitter/query tokenizer separation, clear and ambiguous independent conditions,
query error state and original search input preservation. These checks establish
behavioral contracts; actual Korean model observations belong to the functional
report. The full suite passed 1,106 tests before evidence closeout.

The rendered synthetic UI extends the shared Search family. Existing search,
source Sync, document/Session reading and return paths were exercised separately.
Independent base-only Python3.11 wheel checks passed, including absent-model
presentation and packaged routes/assets. All178 packaged application resource
files match current source bytes; the wheel has ten search modules and three
dedicated UI resources. Distribution inspection found no private database, logs
or model weights. Schema references, value dictionaries, JavaScript syntax and
privacy checks passed. The same installed wheel with optional local-model
dependencies also passed offline MPS inference against a fresh authored corpus.
Python3.9 source-runtime quality measurements and Python3.11 installed-runtime
smoke evidence remain separate.

## Evidence Gaps And Route

The full-index coverage/resource receipt, frozen holdout/contention receipt and
independent installed-wheel real-model receipt completed. Exact full-body ranges
and current source revisions were checked; unchanged preparation preserved its
generation and performed no embedding. The isolated full-size rebuild probe reused
vectors without modifying canonical sources. Its sampled peak includes observed
SQLite workspace; timings and memory/disk scopes are explicitly bounded.

Route: pass. The functional report records non-blocking returned-precision and
ranking limitations instead of treating source coverage as a quality judgment.
Personal human relevance labels, other devices and Windows distribution remain
outside this acceptance boundary. No publication or acceptance of unmeasured
personal quality is implied.
