# Work Context Trial Operations

Use the [shared model-tool prerequisites and private storage rules](model-tools.md) before these operations.

## Operations

The separate generative experiment uses the allowlisted pinned `Qwen/Qwen3-4B`
and `Qwen/Qwen3-8B` models to extract quoted work units
and assess explicit continuation. It does not train the model or replace the
embedding cache. Installation is an explicit public download (about 8.1 GB for
4B or an additional 16.4 GB / 15.3 GiB for 8B; about 24.5 GB for both);
choose a new dedicated installation-metadata folder outside the repository with
an existing parent. Public weights use the user-level Hugging Face Hub cache,
normally `~/.cache/huggingface/hub`.
Use LocalBrain's optional `local-models` environment. Installed applications can
use `localbrain models install 4b` or `8b` with default private metadata locations;
the source scripts also accept explicit roots:

```bash
uv run --no-sync python scripts/install-work-context-model.py --root /absolute/private/models/qwen3-4b
uv run --no-sync python scripts/install-work-context-model.py --root /absolute/private/models/qwen3-4b --verify
uv run --no-sync python scripts/install-work-context-model.py --model Qwen/Qwen3-8B --root /absolute/private/models/qwen3-8b
uv run --no-sync python scripts/evaluate-work-context-model.py \
  --model-root /absolute/private/models/qwen3-4b \
  --output /absolute/private/work-context-evaluation --split development
```

The default installation remains 4B. `--verify` and evaluation infer the model
only from its allowlisted ownership/revision and verified manifest; they do not
discover arbitrary models. Reusing a model folder for a different model is
rejected. `--root` / `--model-root` selects LocalBrain's private metadata folder
(`owner.json`, `install.lock`, `model.json`); new v2 model manifests refer to the
shared cache. Existing v1 app-local installations remain readable. Model snapshots
link to public blobs within their model repository; the 4B baseline is not
automatically removed, and no app cleanup purges shared weights.

The [shared cache configuration](../installation-and-storage.md#storage-ownership-and-configuration)
owns cache precedence and relocation settings. Use the same cache setting across
consumers. A cache relocation with
unchanged assets/runtime does not require re-embedding.

Private databases, generated embeddings, prompts, reports and inference caches
remain project-owned. Future LoRA adapters/checkpoints belong in a durable private
project directory with backups, their base model ID/revision and training
configuration. A merged model is likewise a derived artifact and must not replace
shared pretrained weights. This storage contract adds no training behavior.

HTTP transfer is the default. An optional `--xet-cache /absolute/new-empty-private-dir`
uses an already-installed official Xet downloader with task-scoped diagnostics and
chunk/shard caches disabled. Remove only that owned transfer directory after the
installer process exits; it is not model storage and no durable output depends on it.

`--decoding sampled` selects the separately fingerprinted official non-thinking
sampling settings with a stable per-packet seed; the default is greedy.
Add `--thinking` with sampled decoding for the official reasoning-mode settings
and a bounded 8,192-token reasoning-plus-answer budget. Only the final answer is
decoded/stored; reasoning is counted, not retained. `--strategy staged` first
inventories source-backed work anchors or pair evidence, then extracts/judges
against the original messages. The default `single` strategy is one pass.
The opt-in `--strategy classified --decoding greedy` instead asks the model to
select source roles, work membership, targets and relationship evidence using
bounded answer codes. It requires non-thinking greedy decoding. A token-prefix
constraint enforces codes plus EOS; code serializes the selected original quotes,
never repairs a failed free-form answer or chooses missing citations. A well-formed
choice can still be semantically wrong. This experimental strategy refuses more
than 64 sentence/line spans, ambiguous multi-goal spans, excess output or uncertain
membership; it does not silently truncate inputs or declare one unit per sentence.
`--strategy selected --decoding greedy` uses the same code decoder but selects
whole-conversation work anchors first, then selects each anchor's field evidence.
It preserves the anchor and rejects a ninth unit/item instead of truncating.
These two source-choice variants are experimental alternatives, not admitted automatic workflow producers.
All original messages remain in each decision's context. The case budget is 144
choices/180 seconds, checked between and after calls rather than hard cancellation
of an in-flight model call. Strategy prompts/projection/bounds govern cache identity.
MPS uses the installed library's eager attention; this requires no dependency
update or changed weights.
Use distinct owned output folders for candidate/split comparisons; changing
configuration in one folder replaces that folder's previous evaluation state
for single/staged/classified/selected (the evidence strategy below refuses it).
After selecting a frozen development-passing configuration, `--split holdout`
runs the untouched cases. `--split all` runs both splits, but each split must
pass independently; do not tune on holdout failures. The command opens no private
source DB. It runs the installed model
offline and records per-case checkpoints, evidence validation, quality failures
and timing in an owned private report; repeating the same configuration reuses
validated results. Evaluation state expires after 30 inactive days. Installed
public model assets are separately owned and retained for reuse, not deleted
with an expired evaluation. A completed evaluation is not a passing quality
gate; a development-only pass is not a holdout pass. Whole-history inference and
UI integration remain unadmitted. The current
[context-inference contract](../work-context-inference.md#quoted-work-context-model-contract)
owns packet/output shapes, generation bounds and model identity.

`--strategy evidence` is a separate, opt-in 8B/MPS-eager/non-thinking/greedy
candidate. It assesses source-backed goals/actions/results/pending work before
grouping, and requires recoverable goals, compatible scope and a selected link
before continuing work. Model judgments of missing/conflicting support
automatically withhold the relationship; this does not create an owner
confirmation queue or guarantee that semantic mistakes are recognized.
Semantic labels use an explicit
32-character bound with the same eight-token/EOS limit; older codes keep their
eight-character default. Source citations are assembled from selected originals,
not generated or repaired quotations. Same-model audits remain inferred safeguards,
not proof of semantic correctness.

```bash
uv run --no-sync python scripts/evaluate-work-context-model.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/evidence-development \
  --strategy evidence --split development
```

This runs the fixed four-case development cohort and twelve-case compositional
cohort, with independent gates. It does not rerun the 288-cell diagnostic or
read private Sessions. Case attempts are bounded to 32 spans, 96 choices and 120
soft seconds (30 per generation). Same-config replay retains completed failures
as well as successes; changed configurations and corrupt cached observations
refuse without replacement. A clean interruption allows at most one additional
attempt for its incomplete case; an unclean in-flight crash refuses automatic
resume. Existing storage ownership, writer lock and 30-day expiry still apply.

Only after both development gates **and primary semantic review** pass may this
candidate run `--split holdout` once, in a separate output folder, with
`--development-report /absolute/private/evidence-development/report.json`.
The command revalidates the report's identity, observations and both split scores;
an aggregate PASS is insufficient. `--split all` is refused for this strategy.
Neither this candidate nor its gate starts private backfill or changes the UI.
A frozen candidate's approval, consumed allowance and admission disposition
remain with its owning Run. Reproduction and replay never renew consumed attempts,
reset a budget or authorize another model run. The [evidence-first Run](../../../plans/run/run-20260923-109-evidence-first-work-context.md#retained-admission-disposition)
records that candidate's unchanged disposition.

The separate protocol diagnostic investigates answer-format, option-order and
answer-code sensitivity on twelve fixed synthetic cases. It does not consume the
admission holdout or open private Sessions:

```bash
uv run --no-sync python scripts/diagnose-work-context-protocol.py --describe
uv run --no-sync python scripts/diagnose-work-context-protocol.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/work-context-protocol-diagnostic
```

This fixed 8B/MPS-eager comparison has 288 conditions, a 300-attempt/1,200-second
cumulative budget and 30-second soft generation limits. It compares numeric
choices, semantic-label choices and short text; meaning, format and literal
grounding are scored separately. The twelve cases, not the correlated conditions,
are the evidence units. Completion never means model admission. Results retain
the evaluation owner/lock/30-day expiry rules above. Unlike the
single/staged/classified/selected admission strategies,
diagnostic replay reuses completed wrong/invalid/refused observations too, and a
changed configuration refuses an unexpired folder instead of replacing evidence.
Clean interruption can resume missing observations within cumulative bounds;
an unclean in-flight crash refuses automatic restart because elapsed time is
unknown. No default strategy, model weights or embedding vectors are changed.

A separate matched formulation comparison tests sixteen fixed focused contexts
with independent property questions versus direct selection of the complete role
set. Both use the same source and facet definitions, with canonical/reversed
option orders. Compound action/result statements can keep both roles. Six separate
controls run the unchanged evidence-first relationship pipeline; better role
classification alone does not establish correct work continuity.

```bash
uv run --no-sync python scripts/compare-work-role-formulations.py --describe
uv run --no-sync python scripts/compare-work-role-formulations.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/work-role-comparison
```

The command accepts no private input or tuning/holdout options. It preflights the
semantic vocabulary, uses the installed 8B offline, and reports 166 observations
(160 focused choices plus six multi-call controls). The whole comparison has a
512-choice-attempt/1,200-soft-second budget and at most two attempts for an
incomplete observation. Completed wrong/refused answers replay without generation;
changed configurations, corrupt records and unclean in-flight state refuse.
It shares the existing evaluation owner/lock/atomic/30-day expiry contract.
Exact role-set matches, extra/missing roles, order changes and relationship errors
are separate findings, never an automatic extraction admission or UI update.
