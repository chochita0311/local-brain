# Session Simulation Operations

Use the [shared model-tool prerequisites and private storage rules](model-tools.md) before these operations.

## Operations

The following table describes simulation and work-reconstruction experiments. [Context Search](../context-search.md) separately admits local4B/8B read-only questions; that approval does not admit a rejected work extractor or reconstruction producer. The experimental model roles remain separate:

| Model | Current purpose | Consumer/admission boundary |
| --- | --- | --- |
| Qwen3-Embedding-0.6B | Encode source chunks for similarity-based grouping | Prepared embeddings feed the observation-only map; browsing runs no model |
| Qwen3-4B | Explicit quoted work-context and relationship inference baseline | Synthetic-only quoted trials; no admitted map or private-history reconstruction consumer |
| Qwen3-8B | Explicit quoted work-context, protocol and source-claim diagnostics | No admitted work extractor/reconstruction producer or generative map |

These are pretrained models, not locally trained weights or LoRA adapters.
The installed 4B/8B assets are reusable independently of the embedding cache and
expiring evaluation reports. The commands below are explicit tools, not an
automatic pipeline for newly imported Sessions.

Install LocalBrain's optional runtime and embedding model, then explicitly
prepare the full-history result:

```bash
uv sync --python 3.11 --extra local-models --frozen
uv run --no-sync localbrain models install embedding
uv run --no-sync localbrain simulate
```

Public model files already in the shared cache are verified and reused. New
metadata belongs to LocalBrain. The [installation guide](../installation-and-storage.md#optional-local-models)
also covers installed-app commands and offline adoption. The full-data,
replayable semantic simulation additionally supports explicit paths:

```bash
uv run --no-sync python scripts/simulate-work-sessions.py --help
uv run --no-sync python scripts/simulate-work-sessions.py \
  --database /absolute/private/localbrain.db \
  --output /absolute/private/session-simulation --inventory-only
uv run --no-sync python scripts/simulate-work-sessions.py \
  --database /absolute/private/localbrain.db \
  --output /absolute/private/session-simulation \
  --model-manifest /absolute/private/models/qwen3-embedding-0-6b/model.json
```

Use LocalBrain's `local-models` environment and its installed embedding manifest.
Set the same `HF_HUB_CACHE` as the installer when using a non-default cache.
The simulation reads verified installed assets and keeps private embeddings in
its output directory. All eligible stored primary-work Session messages are
processed, with no 60-Session, 32-message or prefix sampling cap.
Excluded and empty Sessions are accounted
for. Original data is unchanged. `/auto-work` reads the prepared full-history
result; the separate sampled comparator is explicitly `mode=sample`.

Repeat the same command to resume or reuse cached embeddings. Change
`--neighbors`, `--similarity`, `--area-resolution` or `--work-resolution` to rerun
grouping with compatible vectors. `--force-reembed` explicitly recomputes
embeddings. Source/model/chunking changes are fingerprinted; a concurrent source
change prevents publication. `--status` reports a fixed state code;
`--show-counts` explicitly exposes aggregate progress. Private `report.json`
contains coverage, source locators, communities and replay comparison, not a
semantic-quality verdict or a finished workflow map. Results expire after 30
inactive days; `--purge` removes the owned derived state, never source data.
The [current simulation producer contract](../auto-work.md#full-history-simulation-producer)
owns report, source-binding, parameter and lifecycle definitions. `--chunk-chars`
changes the exhaustive window size, `--batch-size` controls committed embedding
batches and `--device` selects `auto`, `cpu`, `mps` or `cuda`. The script's
`--help` lists these controls; `--inventory-only`, `--status` and `--purge` are
mutually exclusive. Inventory/status/purge need no encoder invocation. CLI grouping
uses seed zero; its accepted numeric bounds and defaults are in that contract.
Use [reader states](../auto-work.md#affinity-reader-contract-and-states) to
distinguish missing, busy, stale, expired or invalid preparation from a current
map or an obsolete selection; browsing does not repair or rerun them.
