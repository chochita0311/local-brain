# Session Simulation Operations

Use the [shared model-tool prerequisites and private storage rules](model-tools.md) before these operations.

## Operations

The following table describes simulation and work-reconstruction experiments.
Each experimental producer requires its own admission; another model consumer
does not admit a rejected extractor or reconstruction producer. The experimental
model roles remain separate:

| Model | Purpose and availability | Consumer/admission boundary |
| --- | --- | --- |
| Qwen3-Embedding-0.6B | Encode source chunks for similarity-based grouping | Prepared embeddings feed the observation-only map; browsing runs no model |
| Qwen3-4B | Native generation assets; quoted work-context baseline retired | Former trials remain synthetic-only and unavailable; no admitted map or private-history reconstruction consumer |
| Qwen3-8B | Native generation assets; quoted/protocol/source-claim diagnostics retired | No available trial or admitted work extractor/reconstruction producer or generative map |

These are pretrained models, not locally trained weights or LoRA adapters.
The installed 4B/8B assets are reusable independently of the embedding cache and
expiring evaluation reports. The commands below are explicit tools, not an
automatic pipeline for newly imported Sessions.

Build/select the native CLI and explicitly install its optional embedding model, then
prepare the full-history result:

```bash
cargo +1.90.0 build --locked -p localbrain-api --bin localbrain
./target/debug/localbrain models install embedding
./target/debug/localbrain simulate
```

Public model files already in the shared cache are verified and reused. New
metadata belongs to LocalBrain. The [installation guide](../installation-and-storage.md#optional-local-models)
also covers installed-app commands and offline adoption. The full-data,
replayable semantic simulation additionally supports explicit paths:

```bash
./dist/api/bin/localbrain simulate --help
./dist/api/bin/localbrain simulate \
  --database /absolute/private/localbrain.db \
  --output /absolute/private/session-simulation --inventory-only
./dist/api/bin/localbrain simulate \
  --database /absolute/private/localbrain.db \
  --output /absolute/private/session-simulation \
  --model-manifest /absolute/private/models/qwen3-embedding-0-6b/model.json
```

Use the native executable and its installed embedding manifest. The explicit-path
examples use the native web bundle; substitute the just-built
`./target/debug/localbrain` when using the source-only build.
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
An interruption observed before inventory commit rolls back the uncommitted
inventory. During full simulation, the last cancellation check runs after
report staging and before publication. When cancellation occurs after a new
attempt records progress and before publication, the command exits with code
`130` and `--status` reports `SIMULATION_INTERRUPTED`. Cancellation during model
setup can return `130` before a new progress record exists. In that case,
`--status` reflects the saved state. Committed vectors and the preceding
reports remain available for retry. A successful run that has entered
publication finishes with one completion result. Status also recognizes
earlier `MODEL_CANCELLED` records as interrupted runs.
The [current simulation producer contract](../auto-work.md#full-history-simulation-producer)
owns report, source-binding, parameter and lifecycle definitions. `--chunk-chars`
changes the exhaustive window size, `--batch-size` controls committed embedding
batches and `--device` selects `auto`, `cpu`, `mps` or `cuda`. The native CLI's
`--help` lists these controls; `--inventory-only`, `--status` and `--purge` are
mutually exclusive. Inventory/status/purge need no encoder invocation. CLI grouping
uses seed zero; its accepted numeric bounds and defaults are in that contract.
The encoder splits committed batches above 64 rows into smaller inference batches.
With `--inventory-only`, `--show-counts` prints the prepared inventory coverage.
Use [reader states](../auto-work.md#affinity-reader-contract-and-states) to
distinguish missing, busy, stale, expired or invalid preparation from a current
map or an obsolete selection; browsing does not repair or rerun them.
