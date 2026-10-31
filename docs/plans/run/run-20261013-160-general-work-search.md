# RUN-160: General Work Search

## Metadata

- ID: `run-20261013-160`
- Status: `passed`
- Feature: [FEAT-0123](../feature/feat-0123-general-work-search.md)
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Active Spec: [SPEC-0123](../spec/spec-0123-general-work-search.md)
- Execution Profile: `backend-product`
- Required Evaluators: contract, functional
- Created: `2026-10-13`

## Scope And Route

The owner clarified useful retrieval over perfect classification, then requested
improvement across work domains. During the feature implementation, primary owned
the sequential diagnosis, authored comparison, implementation and
contract/functional review without delegation. The
existing source, storage, offline, original-query and evidence contracts apply.

Author new development and holdout data before model observation, compare bounded
query representations, freeze one choice, then evaluate holdout and private local
observations. Preserve measured regressions. Development evidence belongs to the
existing private archive under `natural-search/general-v1`; remove task-owned
scratch after archiving receipts.

## Outcome And Verification

- Adopt `semantic-dual-view-v3`: one foreground batch for the original query and
  a conservative focused view when applicable; equal mean ordering, union cosine
  admission at0.45. Dense mode remains the original-query baseline. Existing
  document/model identity and exact-identifier behavior remain compatible.
- Load excerpt text only for the current page after ranking/counting all parents.
- Authored comparison:135 queries across six sets. New broad development Hit@1
  improves5/7→6/7, while its Recall@10 falls78.57→75.00%; no blanket gain claimed.
  Existing sets retain recall, one improves. New holdout ordering/recall is unchanged.
  Selection and labels were frozen before its first observation. Rejected prompt
  variants and individual regressions remain in the functional report/private evidence.
- Final publication checking found a generic authored development term colliding
  with the local name denylist. Reworded that one source and reran the comparison;
  labels and holdout content stayed fixed. The functional report records both
  fixture hashes and final measurements. No scanner/allowlist policy was weakened.
- Private observations:10 general work queries; warm alternating baseline/current
  timing,30 samples per method. Median78.98→88.48ms and p95 98.21→131.63ms.
  Zero document encodings; source/index stamps unchanged during comparison.
- Natural-search unit/HTTP39 checks pass. Final full regression1,115 tests,21.909s, OK.
  Earlier failures exposed the one-syllable focus guard, a displaced assertion in
  the test edit and a stale generated schema-use ledger. Fixed these and reran.
  The ledger writer retained703 objects and unchanged keep/defer decisions.
- The historical precision comparator still reproduces its88-query RRF/v2 results.
- Restarted the idle local server and checked the actual browser form,10 query
  routes/current first-result IDs, document filtering/evidence, Session event
  anchor/return link, old search200 and no alerts, overflow or console warnings/errors.
  These checks establish integration, not10/10 human relevance accuracy.
- [Contract](../evaluation/eval-0123-contract-general-work-search.md): PASS.
  [Functional](../evaluation/eval-0123-functional-general-work-search.md): PASS WITH
  SUGGESTIONS. No UI redesign or independent package rebuild; previous installation
  evidence remains historical. No reusable design/interaction policy candidate.
- Privacy check passed for1,291 candidate files; plan catalog, schema-use ledger
  and whitespace checks are current. Verified33 archived evidence files and
  removed the task-owned temporary directory. The intended local server remains
  running with search state `ready`.

## Review Boundary

The implementation is available in the existing parallel search UI. Evaluate the
value of broader results by useful top sources, coverage and exploration burden;
do not use zero false positives as a closure condition. Some ambiguous questions
and individual regressions remain. Reopen ranking/model choices when repeated
real usage demonstrates a concrete burden, with new frozen comparisons and cost
measurements. Private analyst observations are not a complete human relevance set.
No new approval is required to use the current implementation. No commit or
publication had been performed at that feature-completion boundary. The later
documentation, runtime and publication request is recorded below.

## Session Closeout — 2026-10-13

### Authorized Scope And Documentation Owners

The owner requested a complete session reconciliation, independent subagent
reviews with `docs-structuring` and `docs-shaping`, verification, commit and push.
The closeout uses the `docs-content` profile: preserve the existing documentation
tree and apply bounded corrections and explanations. Public code, common
contracts and authored synthetic fixtures are eligible for publication; personal
queries, source contents, indexes, model files and raw private observations are
outside that boundary. This does not resume the stopped workflow-map work or
publish a distribution release.

| Session topic | Durable or historical owner |
| --- | --- |
| Original research, hidden molecularization, full eligible corpus, parallel input and approved scope | [PRD-0020](../prd/prd-0020-local-natural-language-search.md) |
| Source exclusions, fragment budgets/pointers, model roles, query conditions, current ranking and refresh flows | [Natural-Language Search](../../policies/project/natural-language-search.md) |
| Shared public checkpoints, durable app data, private rebuildable index and Python environment repair | [Installation And Local Storage](../../policies/project/installation-and-storage.md) |
| Reproducible comparison environments, commands and private loader metadata | [Developer Guide](../../policies/project/development/search-comparisons.md#operations) |
| Original model/profile/size/cutoff comparisons, local resources and first independent installation | [FEAT-0121 evaluation](../evaluation/eval-0121-functional-natural-search-local-comparison.md) |
| RRF → v2 cosine and v2 → v3 original/focused-view comparisons, regressions and evidence limits | [FEAT-0122 evaluation](../evaluation/eval-0122-functional-natural-search-ranking-precision.md), [FEAT-0123 evaluation](../evaluation/eval-0123-functional-general-work-search.md) |
| Optional reopening after recurring real-use burden | [Backlog](../project/backlog.md#p1---sessions-and-retrieval) and PRD decisions |

The current baseline can close for local use. Remaining ambiguity, broad-topic
coverage gaps and individual rank regressions are optional follow-up work when
real use repeatedly fails to surface useful sources or creates an exploration
or latency burden. Perfect classification and zero no-answer false positives
are not completion criteria. No private training, automatic query collection,
additional default model or settings screen was introduced during closeout.

### Model And Environment Clarifications

- Personal eligible bodies were input locally to **Qwen3-Embedding-0.6B** to
  compute vectors. Pretrained contextual similarity plus bounded source context,
  condition rules and query/ranking changes explain the search behavior. This
  was inference, not private fine-tuning, a new classifier or whole-corpus reasoning.
- Laya multilingual and Qwen3-Reranker-0.6B were separately downloaded and tested;
  their retained pinned checkpoints share the public Hub cache with the embedding
  assets. They retain separate weights and are absent from the default search
  path. The app environment has no Laya package. Qwen3-4B/8B are separate generation
  experiments. A checkpoint-presence check does not establish that the historical
  isolated judge environment is still installed; its current location was not
  established. The reproducible setup remains in the Developer Guide.
- The application `.venv` was migrated from Python 3.9.6/LibreSSL 2.8.3 with
  urllib3 2.6.3 to uv-managed Python 3.11.15/OpenSSL 3.5.7 with urllib3 2.8.0.
  A candidate environment was checked before replacing it. The frozen lockfile,
  package manifest and existing launch alias were unchanged, as were public
  weights and the private search index. The exact prior server process was
  stopped after checking for active work; that migration did not restart it.
  Server availability is runtime state, not a durable promise of this record.
- At migration time, all 53 packages passed dependency checking; app/model imports
  and an offline synthetic Qwen query ran without SSL warnings. The MPS output
  was finite, normalized and shaped `1 × 512`. Those were bounded smoke checks,
  not a full-suite or retrieval-quality rerun. Normal Uvicorn startup/access
  logs are distinct from the old LibreSSL warning; changing Python did not
  suppress them or edit the launch alias.
- Historical FEAT-0121–0123 embedding benchmarks remain Python 3.9.6 measurements.
  The new environment does not retroactively change their latency or quality
  results. Only the checks explicitly recorded below were repeated for closeout.

### Closeout Verification

- Current source-checkout runtime: Python 3.11.15, OpenSSL 3.5.7, urllib3 2.8.0.
- `uv pip check --python .venv/bin/python --no-cache`: all 53 packages compatible.
- `.venv/bin/python -m unittest discover -s tests -v`: **1,115 tests passed in
  24.033 seconds**, with no failures, errors or skips. This verifies the automated
  contracts under the new interpreter; it is separate from real-model relevance
  and browser performance measurements.
- Built the latest wheel offline and installed its `local-models` extra into a
  fresh Python 3.11.15 environment outside the checkout. It resolved 53 packages,
  including PyTorch 2.8.0, Transformers 4.57.6, Sentence Transformers 5.1.2 and
  NumPy 2.4.6; this installed environment is distinct from the source lockfile
  environment. No release artifact was published.
- The installed-wheel smoke used only three authored parents and existing public
  embedding assets registered offline. Separate CPU-fallback and MPS executions
  both prepared the full synthetic index, returned the two expected related
  Session/Document parents, excluded the distractor and reported no partial
  coverage. The sandboxed attempt selected CPU; an execution with hardware
  access confirmed MPS. These are installation/inference checks, not new
  multi-domain quality scores or latency benchmarks.
- Started that installed application on a separate loopback port with its
  synthetic DB. In a browser, submitted the natural-search form, checked both
  independent header forms, two expected results, document evidence and return
  query/page/anchor, the exact Session message anchor and return query, old
  search HTTP 200, and packaged JS/CSS HTTP 200. The actual narrow viewport was
  500px and retained both inputs without horizontal overflow. No alert or
  browser console warning/error appeared. Physical IME and the historical
  private-query quality checks were not repeated. The temporary server was
  stopped after verification.
- JavaScript syntax checks passed for `natural-search.js` and `app.js`.
  Data-model documentation matches 45 ordinary tables, one FTS5 object,
  57 physical foreign keys, 51 explicit indexes and 10 subject owners.
- Two independent read-only subagents applied the requested documentation skills.
  The structure review covered all 44 selected PRD/Feature/Spec/Run/evaluation
  artifacts, the search owner and affected entrance/owner passages. Its final
  check found no missing paths or anchors among 1,543 relative links and 79
  anchors across 59 documents. Other document bodies and the generated schema
  ledger were inventoried, not given a full semantic review.
- The meaning review covered the nine core source documents and affected plans
  summaries. It checked preserved measures and qualifications, model/input roles,
  historical versus current runtimes and closure boundaries. Together, the two
  documentation reviews led to
  explicit RRF/v2 succession, completed downstream links, updated publication
  scope, the search-policy entrance, a repaired design-history table row and
  base-only-safe SSL troubleshooting. Primary retained final source-of-truth,
  evidence and publication responsibility; these reviews did not independently
  execute model evaluations or grant implementation approval.
- Repository privacy checking passed for 1,291 candidate files. The plan catalog
  is current; the schema-use ledger retains 703 objects with 591 keep and 112
  defer decisions. Whitespace checks passed. These publication checks do not
  turn synthetic or analyst observations into complete human relevance labels.
- Staging included newly added files in the whitespace check and exposed six
  redundant final blank lines. Removed only those lines; Python AST comparison
  confirmed identical code and the four measured quality fixtures stayed
  byte-identical. The shared synthetic test helper's file hash changes with its
  final newline, without changing its authored data. The final full-suite rerun
  passed **1,115 tests in 19.752 seconds**, again with no failures, errors or skips.
  Rebuilt and reinstalled the final wheel; its offline MPS search smoke also
  passed with the same three authored parents and two expected matches.

The existing evaluation archives retain the original private model/quality
evidence. This closeout records its bounded results here, with no durable
reference depending on a temporary build, environment, browser state or log path.
