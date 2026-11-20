# Native Natural-Language Search Operations

Use the [native CLI prerequisites and private storage rules](model-tools.md).
The examples use the built `./dist/api/bin/localbrain`; a source-only
`cargo +1.90.0 build --locked -p localbrain-api --bin localbrain` produces
`./target/debug/localbrain`, which can replace that path.

## Operations

The native product uses its verified pinned Qwen3-Embedding-0.6B assets.
Install or adopt those assets explicitly through the
[optional-model operations](../installation-and-storage.md#optional-local-models)
before preparing an index. Status and query do not select a Python backend.
The [search contract](../natural-language-search.md) owns eligibility, the saved
profile, ranking, index compatibility and reader states.

```bash
./dist/api/bin/localbrain search status
./dist/api/bin/localbrain search prepare --device cpu --target 512 --dimension 512 --overlap 0 --cutoff 0.45 --batch-size 8
./dist/api/bin/localbrain search query "find related work" --mode hybrid --limit 20
```

Preparation is an explicit model/index operation over configured eligible local
sources; do not run it without selecting the intended data/cache roots and model
assets. `--rebuild` explicitly rebuilds the owned index. `--device` accepts
`auto`, `cpu` or `mps` for search preparation. These commands do not download an
unselected model, change source organization, or authorize private benchmark
collection. Index status, stale evidence and cancellation retain the search
contract's separate meanings.

The current default is the original/focused dual-view cosine mean with admission
from either view at the saved cutoff (default 0.45); `dense` is the original-query
baseline. Exact single identifiers retain their separately explained lexical
admission. The saved body target is 512 Qwen tokens, the selected vectors have
512 dimensions, and overlap defaults to zero; dimensions are not token budgets.
Qwen3-Reranker-0.6B, Laya and 4B/8B generation comparisons are not this product path.

## Current Synthetic Checks

The ordinary native fixtures use synthetic encoders or frozen JSON observations;
they need no public weights, private corpus or model inference:

```bash
cargo +1.90.0 test -p localbrain-core --test native_search --test native_search_grammar --test native_search_legacy --locked
```

`crates/core/tests/native_search.rs` covers source policy, exhaustive chunking,
index reuse/interruption/locking, stale evidence, exact-identifier admission and
service lifecycle. `native_search_grammar.rs` covers frozen query/scope/focus and
safe-return projections. `native_search_legacy.rs` covers legacy mixed-result and
source-eligibility behavior. Profile and retrieval owners are
`crates/core/src/backend/search/molecules.rs`, `retrieval.rs`, `source.rs` and
`index.rs`. These checks establish their bounded contracts, not real-model
semantic quality or end-to-end latency.

## Retired Comparison Procedures

The Python engine benchmarks, judge/pipeline comparators, comparison-model setup
and their reference fixtures have been removed. There is no native end-to-end
replacement benchmark in this guide. The
[complete historical procedures](../../../plans/research/retired-python-research-tools.md#search-comparisons)
retain their fixture/selection identities, pinned runtime setup, grids, thresholds,
quality-versus-latency distinctions and cleanup rules; all old commands there are
unavailable.

A future comparison still needs independently declared labels, a selection frozen
before a fresh holdout is observed, and explicit public-synthetic versus private
full-index scope. An already observed holdout is regression evidence. Quality
vector reuse does not measure fresh-encoding latency. GPU timings require
sequential jobs, completed device work and matched verification/device/batch/input
boundaries. No such measurement is established by the native fixture tests.
