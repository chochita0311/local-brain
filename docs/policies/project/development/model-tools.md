# Local Model Development Tools

These are explicit source-checkout operations. They do not run as an automatic
Session-processing pipeline. The backend, CLI and model runtime are native Rust.

Build or select the native CLI using [the installation guide](../installation-and-storage.md).
Examples in these guides use `./dist/api/bin/localbrain`, produced by the native
web-bundle build. For a source-only CLI, build with
`cargo +1.90.0 build --locked -p localbrain-api --bin localbrain` and substitute
`./target/debug/localbrain`. Do not assume a `localbrain` command or a personal
shell alias is on PATH. Model status, explicit install/verify and registration
use that native executable; the Python compatibility launchers are retired.
See [optional local models](../installation-and-storage.md#optional-local-models)
for pinned assets, offline reuse, model registration and installation boundaries.

Public model weights stay in the shared Hub cache. Model registrations belong
under `<LOCALBRAIN_DATA_DIR>/models/<model-slug>`. Choose a private output
directory outside Git for each invocation and create its parent before passing
an explicit output path. These tools are not invoked by normal application startup.

Python experiment/reference modules, their synthetic suites and historical
search-comparison commands have been retired. There is no current research Python
environment to prepare. Their [complete former procedures](../../../plans/research/retired-python-research-tools.md#shared-model-tools)
are historical records; model assets, a native generator, or these records do not
admit an unavailable experiment or renew its frozen allowance.

## Operations

| Task | Guide and availability |
| --- | --- |
| Inspect/prepare/query native search and check its synthetic contracts | [Native search operations](search-comparisons.md); retired end-to-end comparisons have no current benchmark replacement |
| Prepare/replay full-history affinity | [Native session simulation](session-simulation.md) |
| Inspect quoted-work-context and protocol design | [Retired trial routing](work-context-trials.md); experimental producers unavailable |
| Inspect source-claim extraction/binding design | [Retired trial routing](source-claim-trials.md); synthetic adapter unavailable |
| Inspect bounded reconstruction design and the native sample consumer | [Work reconstruction](work-reconstruction.md); standalone comparison/scoring command unavailable |

## Native Inference Performance

Runtime Python removal is complete. Native inference still has performance work
remaining; a Rust implementation alone does not establish faster model execution.
The old model adapter used PyTorch/Sentence Transformers, while the current
adapter uses Candle with the same pinned weights and explicit numerical/index
compatibility boundaries.

The migration's cached Qwen3-Embedding-0.6B controls contain one timing sample per
operation, device and output dimension, using synthetic text. For example, a
two-window long-input call at1024 output dimensions took0.510s in Python and
0.763s natively on CPU. Short warm-query samples include faster native cells.
These observations identify candidates for repeated profiling, not a measured
all-model or interactive-search latency guarantee. The long-window adapter serves
the affinity/simulation path; normal search uses the separate bounded-input
`encode_search` contract.

First-call fields have different verification boundaries: native includes a
model-load inventory recheck, while the Python oracle substitutes registration
lookup and excludes constructor verification. They are not equivalent cold-start
measurements. Both checked adapters synchronize device work before returning
their vectors; missing synchronization in the outer timer is not evidence of
missing synchronization in inference. Apple Accelerate, length-sorted bounded
batches and narrower tokenizer revalidation are already applied.

Stage timing on warmed synthetic inputs attributes most of the long-input time
to the model forward pass. The encoder reuses admitted token IDs when stripping
leaves the text unchanged. On CPU the causal mask tensor takes ownership of the
buffer it previously copied. These changes preserve token budgets, window
weights, f32 normalization and index identity. See the paired measurements and
search checks in
[Run 261](../../../plans/run/run-20261118-261-python-free-backend.md#embedding-optimization-with-preserved-results).

For further optimization, match verification, device, batch and input
boundaries. Measure warmed execution separately from initial asset loading.
Keep output/rank, cancellation, pinned-asset verification and index identity
checks alongside a proposed change. Do not change dtype, quantize weights, weaken
verification or reuse incompatible vectors just to lower an elapsed value.
See [the migration evaluation](../../../plans/evaluation/eval-0177-python-free-backend.md#model-compatibility-and-evidence-limits)
for the actual numerical scope and unrun large-model/quality limits.
