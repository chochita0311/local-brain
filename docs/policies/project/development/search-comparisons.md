# Natural-Language Search Comparisons

Use the [shared model-tool prerequisites and private storage rules](model-tools.md) before these operations.

## Operations

The product uses only the existing `local-models` extra and verified
Qwen3-Embedding-0.6B checkpoint for natural search. Qwen3-Reranker-0.6B is a
separate candidate scorer; Qwen3-4B/8B generation trials do not run in this path.
The [search contract](../natural-language-search.md) owns the current default;
public synthetic comparisons and private full-index measurements have distinct
evidence scope. No private corpus is required to reproduce the public comparison.
Use fresh private output directories for each command. Run GPU measurements
sequentially without another model job; timings include completed MPS work.

```bash
uv run --no-sync python scripts/benchmark-natural-search.py --device mps --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/retrieval"
uv run --no-sync python scripts/benchmark-search-runtime.py --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/runtime"
uv run --no-sync python scripts/benchmark-search-throughput.py --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/throughput"
```

The first command compares 256/512/768 body targets, 512/1024 dimensions, lexical,
dense and hybrid retrieval including cutoff 0.7. It reuses full-dimension model
outputs for the pinned model's Matryoshka prefix comparison; accuracy-loop query
caching is disabled for latency. The runtime command evaluates the frozen default
on separate authored topic families, then measures unchanged/incremental refresh
and foreground searches during actual model preparation. The optional throughput
command compares batch sizes and float16 explicitly; it does not alter app settings.

Current `hybrid` uses the original query and a conservative topic/action
view, orders by their mean cosine and retains exact-identifier lexical admission.
These commands use the current implementation. `dense` remains the original-query
baseline. The dedicated precision comparator reconstructs the RRF and
single-view cosine orderings on identical fragment scores, using dense mode plus
unchanged hybrid admission for single identifiers:

```bash
uv run --no-sync python scripts/benchmark-search-precision.py --device mps --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/precision"
```

This compares the fixed0/0.03/0.05/0.08 lexical-bonus grid on authored development
and prior selection cases, then the frozen zero-bonus choice against the historical
baseline on the fixed observed and holdout topic cohorts. It caches query vectors only
for quality comparison and makes no query-latency claim. Synthetic indexes live
in task-owned temporary directories and are removed automatically. The fresh
private output retains fixture hashes, runtime and complete per-query judgments;
these are authored labels, not private human ground truth.

The general-work comparator covers broad purposes, conversational descriptions,
ambiguous terms and multiple relevant activities across work domains:

```bash
uv run --no-sync python scripts/benchmark-search-general.py --stage development --device mps --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/general-development"
uv run --no-sync python scripts/benchmark-search-general.py --stage holdout --selected equal --device mps --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/general-holdout"
```

Freeze the selection after development and before observing a fresh holdout.
The shipped holdout is now observed regression evidence, not an unseen test for
future tuning. `equal` is the admitted default: original/focused cosine mean,
with admission from either view. The script checks comparator/engine agreement
and reports per-query/category metrics, including topic coverage for broad queries.
It reuses vectors only for quality comparison; measure latency with fresh encoding.

Laya and Qwen Reranker are optional development-only dependencies. Create a separate
Python 3.11 environment outside the repository; do not replace the application's
runtime. The frozen reproduction configuration uses `laya==0.4.4`, `torch==2.8.0`,
`transformers==4.57.6`, `huggingface-hub==0.36.2`, `numpy==1.26.4` and
`truststore==0.10.4`. The following setup downloads only pinned public assets into
the shared Hub cache and writes a local hash manifest; `--offline` reuses existing
assets. This explicit setup is the only network stage.

The paths below describe a reproducible environment to create, not an inventory
claim that a previous comparison environment is still installed. Shared public
checkpoint retention and private comparison-runtime retention are independent.

```bash
uv venv --python 3.11 "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/runtime-judge"
uv pip install --system-certs --python "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/runtime-judge/bin/python" laya==0.4.4 torch==2.8.0 transformers==4.57.6 huggingface-hub==0.36.2 numpy==1.26.4 truststore==0.10.4
"$HOME/Library/Application Support/LocalBrain-Development/search-comparison/runtime-judge/bin/python" scripts/prepare-search-comparison-models.py --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/assets"
```

Use that environment's Python to run `scripts/benchmark-search-judges.py` with
`--assets <assets>/assets.json --candidates <retrieval>/candidates.json
--output <fresh-private-output> --role laya --device mps --laya-fp32`; repeat with
`--role reranker` and omit `--laya-fp32`. Both score the same frozen parent texts
at K10/20/50. Full-path measurement uses the application Python and
`scripts/benchmark-search-pipeline.py --assets <assets>/assets.json
--output <fresh-private-output> --judge-python <runtime-judge>/bin/python
--role laya` (then `--role reranker`). This measures retrieval and the resident
judge through local pipes, not an external service. Full-path trials use K20,
retrieval cutoff0 and judge threshold0.5; their scores have a different contract
from the product's cosine cutoff0.45.

A checkpoint/runtime producing non-finite scores fails that attempt. Use
`--laya-fp32` to disable Laya's MPS autocast explicitly; the Qwen Reranker uses float32
and eager attention. Reports record these conditions, input budgets and truncation
refusal. Laya's loader adaptation copies only metadata into its private evaluation
owner and links immutable public weights; shared downloaded files stay unchanged.

`tests/standalone_natural_search.py --output <fresh-private-output>` is an
explicit real-model smoke for the installed wheel environment. Run it with the
installed environment's Python from outside the checkout, after adding the
`local-models` extra and caching the public embedding checkpoint. It uses the
installed schema/code, registers assets offline, builds only its authored Session
and Context data and asserts actual semantic matches. It refuses an existing
output or an editable source import. It is separate from ordinary unit discovery.

No script writes personal content to Git, collects background query history or
changes source organization. Development archives are deliberate evidence owners;
retire their reports, synthetic DBs and isolated runtimes explicitly when no longer
needed. Shared public checkpoints have a separate lifecycle.
