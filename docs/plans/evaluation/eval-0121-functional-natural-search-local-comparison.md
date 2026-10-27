# Functional Evaluation: Local Natural Search Comparison

## Metadata

- ID: `eval-0121-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS WITH SUGGESTIONS`
- Evidence Coverage: `complete`
- Run: [RUN-158](../run/run-20261012-158-natural-search-local-comparison.md)
- Attempt: 1
- Feature: [FEAT-0121](../feature/feat-0121-natural-search-local-comparison.md)
- Spec: [SPEC-0121](../spec/spec-0121-natural-search-local-comparison.md)
- Execution Profile: `infra-devtool`
- Created: `2026-10-12`

## Decision And Scope

Historical baseline: [FEAT-0122](../feature/feat-0122-natural-search-ranking-precision.md)
subsequently changes query-time ordering to cosine with exact-identifier lexical
admission. The measurements below remain the original RRF comparison; do not read
them as measurements of the newer ranking policy.

Adopt Qwen3-Embedding-0.6B plus Korean lexical rank fusion, target512 body tokens,
maximum768, context128, total1024, dimension512, overlap0, float32, batch8 and
cosine cutoff0.45. Preserve the old search. Laya and Qwen Reranker remain optional
development comparisons. No fine-tuning, model-generated summaries or cloud search.
The default is an engineering selection within the approved implementation scope,
not a human review of all personal results or a promise for other machines.

The required full private-index, held-out runtime and installed-package checks
completed. This passes the bounded implementation/comparison contract. Returned
precision and observed ranking noise remain non-blocking improvement candidates;
the common default is not a claim of completed personal relevance calibration.

## Frozen Synthetic Comparison

Measured locally on Apple M4 Max, 64 GiB, MPS. Embedding runtime: Python3.9.6,
PyTorch2.8.0, Transformers4.57.6, Sentence Transformers5.1.2; float32, batch16
for the six-profile comparison. The isolated judge runtime used Python3.11.15,
Laya0.4.4, PyTorch2.8.0 and Transformers4.57.6; batch8, input budget4096.
These runtime versions are evidence, not a change to the recommended Python3.11
installation. Python3.9 LibreSSL and Jinja call-order warnings were visible in
that run; inference was offline and both source and standalone package checks are
reported separately.

The later application environment repair is recorded in
[RUN-160](../run/run-20261013-160-general-work-search.md#session-closeout--2026-10-13).
It does not change these historical measurements or establish that the isolated
comparison environment is still present.

Public authored V2 fixture: 72 parents in 12 topic families; 27 queries,
23 with relevant parents and 4 deliberately without answers. Multiple answers,
Korean paraphrases, English/code identifiers, document/session filters, distractors
and long-tail evidence are represented. The schema/condition suite separately
covers calendar, ambiguity, negation, changing sources and Unicode spans.
The selection set is not a blind test. The separate holdout below uses different
source/topic families after freezing the default; it is also authored, not user
judgments or a general Korean benchmark.

Fixture SHA256: `ac6321c2d4d9b1776334c8ca7fe513b8b600f33e87ce1c6f421d7d2a198a5c1d`.
Earlier exploratory V1 runs are not mixed into the V2 quality tables.

| Model | Pinned revision | Role |
| --- | --- | --- |
| Qwen/Qwen3-Embedding-0.6B | `b22da495047858cce924d27d76261e96be6febc0` | Offline document/query embeddings |
| convaiinnovations/laya-multilingual | `e4e9ddf21a7b1903b7acffd8814ad4307bf63a67` | Boolean relevance judgment |
| Qwen/Qwen3-Reranker-0.6B | `e61197ed45024b0ed8a2d74b80b4d909f1255473` | Yes/no relevance reranking |

Every checkpoint file is hash-verified; exact manifests remain in the private
Development archive. Upstream definitions: [Qwen embedding model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B),
[Qwen reranker model card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B),
[Laya source](https://github.com/NandhaKishorM/laya) and
[multilingual checkpoint](https://huggingface.co/convaiinnovations/laya-multilingual).
No upstream latency or Korean quality number is presented as a local observation.

## Retrieval And Cutoff

Recall@10 measures how many expected parents appear in the first ten. Hit@10 asks
whether at least one appears; nDCG@10 accounts for order. Precision uses the number
actually returned up to ten, with empty results counted as zero; its macro average
also includes the four no-answer queries. Recall/Hit/nDCG and answerable-empty use
only answerable queries; false-positive uses only the four no-answer cases. Thus
0% false-positive here means 0/4, not a universal negative-detection guarantee.

| Method, target512/dim512 | Recall@10 | Hit@10 | nDCG@10 | Returned precision | Answerable empty | No-answer FP |
| --- | --- | --- | --- | --- | --- | --- |
| Existing keyword | 13.04% | 17.39% | 14.21% | 14.81% | 82.61% | 0.00% |
| New lexical | 56.34% | 91.30% | 60.81% | 42.59% | 4.35% | 0.00% |
| Dense, cutoff0 | 91.30% | 100.00% | 91.12% | 43.33% | 0.00% | 100.00% |
| Dense, cutoff0.45 | 82.61% | 91.30% | 83.73% | 54.96% | 4.35% | 0.00% |
| Hybrid, cutoff0 | 75.91% | 95.65% | 78.65% | 35.56% | 0.00% | 100.00% |
| Hybrid, cutoff0.45 | 83.33% | 95.65% | 84.39% | 56.81% | 0.00% | 0.00% |
| Hybrid, cutoff0.7 | 14.49% | 21.74% | 16.36% | 18.52% | 78.26% | 0.00% |

The 0.7 trial drops most answerable results. The chosen 0.45 preserves useful recall
on this set; raw cosine is not a probability. Exact single Latin identifiers have
an explicit lexical admission path. RRF fusion scores are never compared with0.45.
Uncut dense retrieval has higher recall but returns results for every no-answer
query. The chosen hybrid balances this observation; it is not the highest score
on every metric or profile.

## Molecule Size And Dimensions

| Body target | Dimension | Fragments | SQLite bytes | Hybrid0.45 Recall@10 | nDCG@10 |
| --- | --- | --- | --- | --- | --- |
| 256 | 1024 | 288 | 1,351,680 | 78.99% | 79.87% |
| 256 | 512 | 288 | 1,318,912 | 87.68% | 88.40% |
| 512 | 1024 | 168 | 1,454,080 | 78.99% | 80.26% |
| 512 | 512 | 168 | 1,417,216 | 83.33% | 84.39% |
| 768 | 1024 | 144 | 1,347,584 | 78.99% | 79.42% |
| 768 | 512 | 144 | 1,310,720 | 86.96% | 87.83% |

The 256 target produces more fragments; 768 embeds longer passages. Both score
above512 on this small set. Retain512 as the middle input/cost profile, rather than
claim it is optimal. Dimension1024 does not improve this fixture at the same raw
cutoff and doubles vector payload; score distributions vary with dimension, so this
is not proof that1024 is generally worse. Both dimensions were evaluated using
1024-dimensional outputs followed by Matryoshka prefix truncation and renormalization.
The table's total SQLite size includes text/FTS and duplicate-vector reuse; it does
not scale exactly with dimension or fragment count. Cross-profile cache reuse makes
those preparation times unsuitable as independent throughput claims.

## Same Candidates, Additional Judges

For each query, both judges receive the same frozen title plus strongest passage
per parent. Hybrid and lexical candidate sets are separate, with K10/20/50.
Candidates use retrieval cutoff0 so a judge can remove weak candidates. A judge
cannot recover a missing parent, and a single candidate passage can miss a parent's
other relevant evidence. Both models rejected truncation and produced zero
truncated inputs in these admitted trials.

| Candidate path | K | Candidate recall | Laya Recall@10, cutoff0 / 0.5 | Qwen Reranker Recall@10, cutoff0 / 0.5 | Laya judge p50/p95 ms | Reranker judge p50/p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| hybrid | 10 | 75.91% | 75.91% / 27.17% | 75.91% / 51.27% | 195.36 / 287.29 | 683.12 / 1056.12 |
| hybrid | 20 | 86.23% | 65.76% / 30.07% | 84.24% / 51.27% | 417.80 / 521.28 | 1770.00 / 2339.15 |
| hybrid | 50 | 100.00% | 54.89% / 28.62% | 96.20% / 61.05% | 945.48 / 1051.74 | 4997.21 / 6373.07 |
| lexical | 10 | 56.34% | 56.34% / 22.10% | 56.34% / 41.85% | 105.47 / 204.23 | 550.99 / 1054.80 |
| lexical | 20 | 57.79% | 54.89% / 22.83% | 55.62% / 42.57% | 94.27 / 412.38 | 539.81 / 2543.59 |
| lexical | 50 | 58.51% | 55.62% / 22.83% | 55.62% / 42.57% | 94.01 / 727.39 | 536.57 / 4457.45 |

Laya does not establish a useful default-path gain here: hybridK20 plus threshold0.5
has Recall30.07%, nDCG31.98% and false positives on3/4 no-answer queries. The English
wording of the fixed relevance instruction and the title+one-passage representation
are part of this trial; different training/prompt/candidate choices were not proven.
Qwen RerankerK50 with no cutoff reaches Recall96.20% and nDCG97.14%, but accepts all
four no-answer queries and adds seconds. With threshold0.5 its recall is61.05%.
This is evidence of ranking value with a latency/cutoff tradeoff, not a blanket
claim that reranking is inaccurate. Neither judge is required by the product.

The default Laya MPS autocast attempt produced non-finite scores and was rejected.
Its admitted run explicitly uses full float32. Default Qwen MPS SDPA also produced
non-finite scores in an exploratory attempt; its admitted run uses eager attention
in float32. Failed attempts remain recorded separately, not counted as valid quality
samples. These observations concern these runtime settings, not every platform.

## Latency And Memory

Embedding cold load in the V2 comparison:4.421s. Warm uncached query+dot p50/p95:
41.61/57.80ms; retrieval total42.56/59.37ms on the72-parent fixture, 36 calls
(12 queries repeated three times), measured at cutoff0.55. This is a small-corpus
baseline, not the full private-index latency or an exact cutoff0.45 measurement.
Accuracy-loop cached encodings are excluded from these timings. No result cache
is enabled in the product.

Full pipelines below perform actual retrieval and local resident-judge pipe round
trips: K20, candidate cutoff0, judgment threshold0.5, 27 queries repeated twice
(54 samples per mode), no query cache. They are not estimates made by adding
separate percentile values.

| Pipeline | Recall@10 | End-to-end p50/p95 ms | Retrieval p50/p95 ms | Judge p50/p95 ms |
| --- | --- | --- | --- | --- |
| hybrid + laya | 30.07% | 668.64 / 915.75 | 33.53 / 74.40 | 625.08 / 875.74 |
| lexical + laya | 22.83% | 136.81 / 678.42 | 0.70 / 2.38 | 136.00 / 675.53 |
| hybrid + reranker | 51.27% | 2535.96 / 3376.01 | 54.30 / 95.73 | 2486.16 / 3319.80 |
| lexical + reranker | 42.57% | 495.10 / 2437.45 | 0.81 / 2.64 | 494.20 / 2434.54 |

The model processes have different startup/allocator conditions; report individual
judge times separately from combined-path times. Peak process RSS was3.67GiB for
the six-profile embedding comparison,2.55GiB for the Laya judge, and3.74GiB for the
Qwen reranker judge. These are per-process measurements, not the sum or peak RAM
of both resident models together; MPS driver allocations are retained in raw reports.
Laya public assets add678,201,614bytes; reranker adds1,207,471,291bytes. Neither is
needed for installed natural search, which shares the existing embedding asset.

A separate64-input bulk trial used approximately512-token inputs. Float32 batch8,
16,32,64 achieved8.90,7.22,5.26,5.15vectors/s; float16 achieved9.58,9.62,9.15,8.71.
The limited float16 improvement and altered vectors did not justify a dtype change;
float32 batch8 minimizes the measured batching cost and foreground waiting interval.
This is one synthetic throughput trial, with retained allocator state across batch
sizes. Its driver-memory samples are not independent per-batch peaks.

## Held-Out Default And Runtime Refresh

The separate authored holdout contains24 parents from8 different topic families,
10 answerable queries and3 no-answer queries. The selected512/512/0.45 profile was
frozen before this run and was not tuned after observing the result. Fixture SHA256:
`2ea131a6404fc73bb15830559e90f8bbf0530409403f4f8ef96d9c63ff85c05a`.

| Frozen holdout method | Recall@10 | Hit@10 | nDCG@10 | Returned precision | Answerable empty | No-answer FP |
| --- | --- | --- | --- | --- | --- | --- |
| Existing keyword | 0.00% | 0.00% | 0.00% | 0.00% | 100.00% | 0.00% |
| Selected hybrid | 96.67% | 100.00% | 88.02% | 29.05% | 0.00% | 0.00% |

The no-answer result is0/3. Precision uses the same macro definition as above,
including empty no-answer cases; it is not private-corpus accuracy. The low
returned precision shows that successful recall does not make every returned
parent useful. Bicycle repair and missing rain-sensor records had weaker ordering
(nDCG0.55 and0.48); the latter missed one of three expected parents in the top ten.
The existing keyword result concerns these paraphrased sentences, not all keyword
use. Keep these limitations visible instead of retuning against this holdout.

Warm uncached idle search p50/p95 was21.80/35.45ms over26 calls. An unchanged
refresh took0.011s, reused40 fragments and encoded none. After changing one
synthetic parent, its stale evidence disappeared immediately; an actual background
refresh encoded46 new inputs and reused39 in3.597s. Seven foreground queries during
that refresh measured532.11/591.65ms p50/p95. This exercises the shared encoder and
splitter tokenizer separation with real MPS inference, but seven calls are a small
contention sample, not a latency guarantee. The final generation became complete.

## Full Private Corpus And Integrated Checks

The full eligible private index completed. Every indexed parent revision matches
the normalized snapshot; every original block's fragment ranges are contiguous,
have exact original text and reach the final character. The complete character
sum also matches. Excluded/empty/unreadable source counts are retained separately.
This verifies coverage and provenance, not semantic correctness of every result.

The private receipt separates cold model load, first matrix/source load, eight
new warm queries, eighteen repeats without result caching, and six actual ASGI
page-render requests with a resident encoder. An unchanged full-corpus refresh
encoded nothing and preserved the generation. A separate full-size cache probe
changed only one synthetic timestamp in the frozen source snapshot, reused all
vectors and published a new generation; canonical sources were not changed.
Its duration is a vector-reuse rebuild cost, not full re-embedding throughput.

Disk measurement includes logical/allocated active files, managed generation
peak and a10ms sampled combined peak including newly opened SQLite temporary
workspace files. File identities are deduplicated; existing process handles are
excluded from the extra-workspace count. This is a sampled lower bound for the
probe's files, not whole-machine/APFS snapshot usage. The initial preparation's
separate200ms managed-folder peak excludes temporary files outside that folder.
The [storage owner](../../policies/project/installation-and-storage.md#natural-language-search-storage)
explains the additional SQLite workspace allowance. Peak process RSS and MPS
driver allocation are separate observations, not additive total machine RAM.

Initial-index wall time includes recorded pauses for model comparisons, one
interrupted/resumed preparation and both batch8 and batch16 segments. The report
retains those events and elapsed time after subtracting explicit pauses; neither
is a clean benchmark of the final batch8 default. Long complete bodies make first
preparation expensive. Ordinary unchanged refresh does not repeat that work.

Private aggregate receipts, method snapshots and explicit diagnostic queries
remain under the configured Development owner at `natural-search/`; they do not
become tracked fixtures. Analyst spot checks observed useful semantic matches as
well as homonym and lexical-ranking noise. No user-reviewed private relevance
labels are available, so individual corpus quality is not certified.

Completed integrated checks:

- Full regression: 1,106 tests passed in the final21.956s run (the earlier pass
  took55.562s while initial indexing was active); 30 engine/HTTP natural-search
  checks are included. Deterministic encoders establish contracts, not model quality.
- Synthetic browser: preparation/ready, result→Session event and document
  evidence→reader→same results, history, explicit/ambiguous independent filters,
  original search and Atlassian's local-query exception. Widths320/700/920/1440
  have no horizontal overflow. Composition-Enter is prevented and status polling
  preserves unsent input, focus, result content and the open coverage disclosure.
  No final console errors or warnings; physical OS IME typing was not automated.
- Independent Python3.11 base-only installed wheel: natural/old search and the
  new script return200; explicit preparation redirects and reports model-missing.
  Torch is absent and imports resolve to site-packages outside the source checkout.
- The same independent wheel with the local-models extra passed actual MPS
  inference: a fresh authored corpus of two Sessions and one Context document
  returned the intended app Session/document and excluded the unrelated Session.
  Assets were registered offline. Runtime: Python3.11.15, PyTorch2.8.0,
  Transformers4.57.6, Sentence Transformers5.1.2, NumPy2.4.6. This is a second
  installed-runtime smoke, not a full repetition of quality scores under NumPy2.
- Wheel contains all ten search modules and three dedicated UI resources; its
  178 application resource files match the current source bytes. Wheel/source
  archive inspection found no DB, SQLite, JSONL, log or model-weight payloads.
- JavaScript syntax, generated schema references, value dictionaries, plan catalog,
  whitespace and privacy checks passed. No commit, push or release was performed.

## Reproduction And Evidence Ownership

The comparison checkpoints were downloaded separately into the same user-level
public Hub cache as the embedding checkpoint. Each model had its own pinned
weights; sharing a cache did not make them one model. Comparison Python packages
were isolated from the app runtime. These setup observations do not establish
that the historical comparison environment is still present.

[Developer Guide](../../policies/project/developer-guide.md#natural-language-search-comparisons)
provides exact scripts, pinned optional runtime setup, asset preparation and fresh
private output requirements. Source scripts and authored fixtures are public;
actual private inputs, titles, result texts, paths, DBs, vectors and raw machine
inventory are not part of this report or distribution. Benchmark output directories
are deliberate private development evidence, not ordinary application startup state.
Transient build/browser/scratch resources are removed at closeout.

## Evidence Gaps And Route

No required implementation/comparison receipt is missing. Route: pass with
non-blocking quality suggestions. Improve precision and homonym ordering only
against an explicitly reviewed future query set; preserve the current holdout as
already observed evidence. Do not silently tune to private project names or collect
background queries. Practical misses/false positives can reopen the ranking/cutoff
decision in PRD-0020; no threshold settings UI is added here.

Personal human ground-truth quality, other Macs/Windows and physical OS IME typing
remain outside this measured claim. No new reusable design/interaction evaluation
rule was required beyond the existing search, focus, state and return contracts.
