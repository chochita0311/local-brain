# Retired Python Research Tools

Status: **retired; historical procedures only**. The native backend transition
removed the Python research implementations, reference fixtures, benchmark
scripts and compatibility launchers described here. **Every command and setup
procedure in this record is unavailable in the current checkout.** These are
prior procedures, not instructions to recreate the deleted Python package or to
run archived tools. No runnable Python source or fixture is preserved here.

The four operation-guide bodies below are retained in full, followed by the
related former setup, model-role and implementation explanations. Source
locators and SHA-256 identify their pre-retirement text. Heading levels and
relative links are adapted for this archive; procedure conditions, numbers,
limits and qualifications retain their original meaning. References to
“current,” “installed,” or “the command” inside a chapter describe that chapter's
original state. They do not describe an available tool today.

Retirement, reproduction and replay do not reopen paused or rejected candidates,
renew consumed calls or human-review allowances, admit private-source use, or
approve a product/UI transition. The owning Runs and current design/privacy
contracts continue to control those boundaries. Native model installation does
not restore an experiment or grant permission to run it.

Current native operations are [model tools](../../policies/project/development/model-tools.md),
[search](../../policies/project/development/search-comparisons.md) and
[session simulation](../../policies/project/development/session-simulation.md).
The retained design owners are [quoted work context](../../policies/project/work-context-inference.md),
[source claims and reported state](../../policies/project/source-claims-and-work-state.md)
and [work reconstruction](../../policies/project/work-reconstruction.md).

## Archived Chapters

- [Retired Search Comparison Procedures](#search-comparisons)
- [Retired Work Context Trial Procedures](#work-context-trials)
- [Retired Source Claim Trial Procedures](#source-claim-trials)
- [Retired Work Reconstruction Procedures](#work-reconstruction)
- [Former Shared Research Setup](#shared-model-tools)
- [Former Simulation And Research Model Roles](#simulation-model-roles)
- [Retired Quoted Context Implementation](#work-context-implementation)
- [Retired Reconstruction Implementation](#reconstruction-implementation)
- [Retired Claim And State Implementation](#source-claim-implementation)

<a id="search-comparisons"></a>

## Retired Search Comparison Procedures

Original source: `docs/policies/project/development/search-comparisons.md`; complete original document SHA-256: `6cb14249afd9c69807546fb72729233fad0d6c0633640d285dd97fea15c3620a`.

Historical and unavailable: all operations in this chapter retain their original restrictions; none authorizes a current execution.

<a id="search-comparisons-natural-language-search-comparisons"></a>

### Natural-Language Search Comparisons

Use the [shared model-tool prerequisites and private storage rules](#shared-model-tools) before these operations.

<a id="search-comparisons-operations"></a>

#### Operations

Set `LOCALBRAIN_REFERENCE_ROOT` to a separately prepared frozen Python checkout
before running the six historical engine benchmarks below. Use that checkout's
matching Python environment; no reference is chosen automatically. This preserves
the original comparison procedures and labels without retaining a Python backend
in the current application. These commands do not measure current native latency.

The native product uses its bundled Rust model runtime and verified
Qwen3-Embedding-0.6B checkpoint for natural search. Qwen3-Reranker-0.6B is a
separate candidate scorer; Qwen3-4B/8B generation trials do not run in this path.
The [search contract](../../policies/project/natural-language-search.md) owns the current default;
public synthetic comparisons and private full-index measurements have distinct
evidence scope. No private corpus is required to reproduce the public comparison.
Use fresh private output directories for each command. Run GPU measurements
sequentially without another model job; timings include completed MPS work.

```bash
python3 scripts/benchmark-natural-search.py --device mps --output "/absolute/private/search-comparison/retrieval"
python3 scripts/benchmark-search-runtime.py --output "/absolute/private/search-comparison/runtime"
python3 scripts/benchmark-search-throughput.py --output "/absolute/private/search-comparison/throughput"
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
These historical commands use the explicitly selected frozen Python reference engine. Native runtime/behavior evidence is recorded separately. `dense` remains the original-query
baseline. The dedicated precision comparator reconstructs the RRF and
single-view cosine orderings on identical fragment scores, using dense mode plus
unchanged hybrid admission for single identifiers:

```bash
python3 scripts/benchmark-search-precision.py --device mps --output "/absolute/private/search-comparison/precision"
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
python3 scripts/benchmark-search-general.py --stage development --device mps --output "/absolute/private/search-comparison/general-development"
python3 scripts/benchmark-search-general.py --stage holdout --selected equal --device mps --output "/absolute/private/search-comparison/general-holdout"
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
uv venv --python 3.11 "/absolute/private/search-comparison/runtime-judge"
uv pip install --system-certs --python "/absolute/private/search-comparison/runtime-judge/bin/python" laya==0.4.4 torch==2.8.0 transformers==4.57.6 huggingface-hub==0.36.2 numpy==1.26.4 truststore==0.10.4
"/absolute/private/search-comparison/runtime-judge/bin/python" scripts/prepare-search-comparison-models.py --output "/absolute/private/search-comparison/assets"
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
changes source organization. Clean up task-owned outputs, synthetic DBs and
isolated runtimes once their purpose ends; retained evidence needs an explicit
private owner outside Git. Shared public checkpoints have a separate lifecycle.

<a id="work-context-trials"></a>

## Retired Work Context Trial Procedures

Original source: `docs/policies/project/development/work-context-trials.md`; complete original document SHA-256: `18134e1fcba66645b1f288b4cf44aa1b593d50038f70c128a59034656f88b3ef`.

Historical and unavailable: all operations in this chapter retain their original restrictions; none authorizes a current execution.

<a id="work-context-trials-work-context-trial-operations"></a>

### Work Context Trial Operations

Use the [shared model-tool prerequisites and private storage rules](#shared-model-tools) before these operations.

<a id="work-context-trials-operations"></a>

#### Operations

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
python3 scripts/install-work-context-model.py --root /absolute/private/models/qwen3-4b
python3 scripts/install-work-context-model.py --root /absolute/private/models/qwen3-4b --verify
python3 scripts/install-work-context-model.py --model Qwen/Qwen3-8B --root /absolute/private/models/qwen3-8b
python3 scripts/evaluate-work-context-model.py \
  --model-root /absolute/private/models/qwen3-4b \
  --output /absolute/private/evaluation-output --split development
```

The default installation remains 4B. `--verify` and evaluation infer the model
only from its allowlisted ownership/revision and verified manifest; they do not
discover arbitrary models. Reusing a model folder for a different model is
rejected. `--root` / `--model-root` selects LocalBrain's private metadata folder
(`owner.json`, `install.lock`, `model.json`); new v2 model manifests refer to the
shared cache. Existing v1 app-local installations remain readable. Model snapshots
link to public blobs within their model repository; the 4B baseline is not
automatically removed, and no app cleanup purges shared weights.

The [shared cache configuration](../../policies/project/installation-and-storage.md#storage-ownership-and-configuration)
owns cache precedence and relocation settings. Use the same cache setting across
consumers. A cache relocation with
unchanged assets/runtime does not require re-embedding.

Private databases, generated embeddings, prompts, reports and inference caches
remain project-owned. Future LoRA adapters/checkpoints belong in a durable private
project directory with backups, their base model ID/revision and training
configuration. A merged model is likewise a derived artifact and must not replace
shared pretrained weights. This storage contract adds no training behavior.

The native installer uses certificate-verified, resumable HTTPS without a Python
or Xet client. The compatibility `--xet-cache /absolute/new-empty-private-dir`
flag retains the original private, empty-directory admission and ownership marker,
only when a missing public asset actually needs transfer and after taking the
model registration lease. A complete cached snapshot or verify does not touch it.
It does not enable the historical Xet transport. Remove only that owned directory
after the installer exits; it is not model storage and no durable output depends
on it. The retained Python comparison fixture keeps its historical Xet behavior
inside its separately selected research environment.

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
[context-inference contract](../../policies/project/work-context-inference.md#quoted-work-context-model-contract)
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
python3 scripts/evaluate-work-context-model.py \
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
reset a budget or authorize another model run. The [evidence-first Run](../run/run-20260923-109-evidence-first-work-context.md#retained-admission-disposition)
records that candidate's unchanged disposition.

The separate protocol diagnostic investigates answer-format, option-order and
answer-code sensitivity on twelve fixed synthetic cases. It does not consume the
admission holdout or open private Sessions:

```bash
python3 scripts/diagnose-work-context-protocol.py --describe
python3 scripts/diagnose-work-context-protocol.py \
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
python3 scripts/compare-work-role-formulations.py --describe
python3 scripts/compare-work-role-formulations.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/evaluation-output
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

<a id="source-claim-trials"></a>

## Retired Source Claim Trial Procedures

Original source: `docs/policies/project/development/source-claim-trials.md`; complete original document SHA-256: `7982f414115950a70c9326c00f3b78f6cc26eced9090eaa0141f7638614ab608`.

Historical and unavailable: all operations in this chapter retain their original restrictions; none authorizes a current execution.

<a id="source-claim-trials-source-claim-trial-operations"></a>

### Source Claim Trial Operations

Use the [shared model-tool prerequisites and private storage rules](#shared-model-tools) before these operations.

<a id="source-claim-trials-operations"></a>

#### Operations

The separate [source-claim adapter](../../policies/project/source-claims-and-work-state.md#model-aware-v2-and-synthetic-adapter)
extracts historical claims, proposes scoped work bindings and lifecycle effects,
then computes reported state with a pure deterministic projector. Model-inferred
fulfillment is distinct from a source explicitly reporting completion. A completed
check does not complete its parent effort.

```bash
python3 scripts/evaluate-source-claims.py --describe
python3 scripts/evaluate-source-claims.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/evaluation-output
python3 scripts/evaluate-source-claims.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/evaluation-output --replay
```

Use the existing compatible model runtime. This is one frozen 8B/MPS-eager,
non-thinking candidate, not training or a new model installation. Twenty-eight
synthetic development histories allow at most 84 generation calls; the original
ten holdout cases allow 20 additional calls only after all development gates and
a report-bound primary semantic review. `--holdout` cannot bypass that gate.
Each call is bounded to 8,192 combined/2,048 generated tokens and 60 soft seconds.
The whole candidate allows at most 104 generation calls, including the gated
holdout allowance, and a 120-minute cumulative active-run launch gate, including model load,
verification and preflight. Reservations and elapsed time survive clean resume;
these ceilings are not a fresh allowance for a closed or exhausted candidate.
Input is never truncated.

Reference-conditioned binding receives correct claims/targets for diagnosis;
end-to-end generation must discover them from raw source. Neither technical tests
nor conditional results establish extraction quality. Completed failures replay
without generation. The owned report uses the existing 30-day inactivity rule;
changed config, corrupt/unclean state and expired trial budgets refuse reuse.
No private input argument, all-Session job, server/UI update or organization write
is added. The [owning trial Run](../run/run-20260923-112-source-claim-extraction-and-binding-trial.md#retained-admission-disposition)
owns the frozen candidate's admission and consumed allowance. A replay or
documentation cleanup does not reopen a candidate, renew consumed calls or reset
its budget. Any new generation must remain within an existing, unexhausted
approval. This
command is an evaluation tool, not an admitted work extractor.

<a id="work-reconstruction"></a>

## Retired Work Reconstruction Procedures

Original source: `docs/policies/project/development/work-reconstruction.md`; complete original document SHA-256: `6a89db99a95f4befd428d743e49927681cb6d4896e48a12a269c65fe4c2002f0`.

Historical and unavailable: all operations in this chapter retain their original restrictions; none authorizes a current execution.

<a id="work-reconstruction-work-reconstruction-operations"></a>

### Work Reconstruction Operations

Use the [shared model-tool prerequisites and private storage rules](#shared-model-tools) before these operations.

<a id="work-reconstruction-operations"></a>

#### Operations

An isolated non-model tool compares reference-pair grouping with explicit
Korean/English goal extraction. It does not replace the current Workstream UI
or change its data. Inspect its options without opening runtime storage:

```bash
python3 scripts/experiment-work-reconstruction.py --help
```

Execution accepts an explicit supplied fixture or an existing database plus a
frozen selection manifest. After selecting an existing database and through-time,
`--prepare-through <UTC> --unassessed` can prepare a deterministic bounded sample
and check execution without an answer key. It covers the selected population's
whole existing time range, not every record, and reports omissions explicitly.
Scored quality still requires separate source-bound expectations. Results need
a new private output directory outside the repository and an owner/expiry;
default output contains status codes only. No private database is opened by
default, and predictions never become the answer key. The current
[Work Reconstruction contract](../../policies/project/work-reconstruction.md#isolated-work-reconstruction-experiment)
owns the wire shapes, caps, source permissions and assessment boundaries; the
invocation and file shapes below describe this command.
Synthetic correctness is not evidence that real work is reconstructed usefully.

<a id="work-reconstruction-model-free-invocation-and-files"></a>

##### Model-Free Invocation And Files

Choose exactly one input mode. All paths below are explicit local paths; use a
new absolute output directory with an existing canonical nonsymlink parent
outside the repository. Set `RECONSTRUCTION_EXPIRES_AT` to an explicit future
aware ISO timestamp before a supplied-fixture or preparation invocation.

```bash
python3 scripts/experiment-work-reconstruction.py \
  --fixture /absolute/private/fixture.json \
  --expectations /absolute/private/expectations.json \
  --output-dir /absolute/private/new-fixture-result \
  --owner reconstruction-review --expires-at "$RECONSTRUCTION_EXPIRES_AT"

python3 scripts/experiment-work-reconstruction.py \
  --database /absolute/private/localbrain.db \
  --manifest /absolute/private/selection.json \
  --expectations /absolute/private/expectations.json \
  --output-dir /absolute/private/new-scored-result

python3 scripts/experiment-work-reconstruction.py \
  --database /absolute/private/localbrain.db \
  --prepare-through '2026-09-15T00:00:00+00:00' --unassessed \
  --output-dir /absolute/private/new-unassessed-result \
  --owner reconstruction-review --expires-at "$RECONSTRUCTION_EXPIRES_AT"
```

The preparation cutoff is an explicit scope choice, not a default or permission
to open another database. Preparation requires database mode, `--unassessed`,
and no manifest or expectations. Other database runs require a manifest;
supplied-fixture and scored database runs require an independent expectations
file. The selected manifest supplies database-mode owner/expiry. Fixture and
preparation modes require explicit owner/expiry arguments. Expiry must be later
than the current time, and preparation also requires expiry after its cutoff.
No invocation creates missing database/schema/source state.

| File | Current shape and validation |
| --- | --- |
| Supplied fixture | Exactly `{"version":1,"snapshots":[...]}`; 1–12 distinct named snapshots obey the [current snapshot contract](../../policies/project/work-reconstruction.md#reconstruction-input-and-bounds) |
| Private selection | Exactly `version`, `source_ids`, `start`, `end`, `snapshots`, `owner`, `expires_at`; version 1, ordered snapshot cutoffs, one bounded hash-verified selection per record and the source/permission predicates in [Reconstruction Input And Bounds](../../policies/project/work-reconstruction.md#reconstruction-input-and-bounds) |
| Expectations | Exactly `{"version":1,"snapshots":{"snapshot-name":...}}`; names exactly match all supplied snapshots. Each version-1 answer key binds `snapshot_digest` and independently supplies `groups`, `negative`, `unresolved`; group/member/label bounds and contradictory-span refusal are in [assessment](../../policies/project/work-reconstruction.md#reconstruction-output-and-assessment) |
| Result | One new `comparison.json`, encoded at most 10 MiB, wrapped as `owner`, `expires_at`, `report`; directory mode 0700/file mode 0600. Existing output is never replaced; a failed write removes only paths created by that invocation |

JSON inputs must be existing nonsymlink files no larger than 10 MiB; duplicate
keys, non-finite constants, malformed data and hard-bound overflow refuse.
Answer keys are validated against every frozen snapshot before either arm runs.
The command compares text and metadata with/without organization, checks
unchanged replay, and records scores, source/expectation digests, resource
measurements and chronological stability. Results include `technical`,
`input_kind`, `private_quality`, `viability`, `snapshots`, `history`, `sample`,
`required_review`, `admission_resources` and `assessment`; preparation adds its
frozen `input_manifest` and omission/sample metadata. `assessment: unassessed`
retains unknown expectations and cannot pass quality; fixture execution cannot
establish private quality. `viability` remains `unverified` even after technical
success. The [finite human-review allowance](../../policies/project/privacy-and-data.md#local-persistence)
is separate and is never renewed by these commands.

Each admission, extraction, comparator or scoring worker has a 120-second wall
limit and 512-MiB peak-RSS bound, with monitor availability checked fail-closed;
cancellation/failure terminates and reaps only its task-owned worker. The command
opens no native file, source parser, connector or model. It adds no background
retention scheduler or full database copy. Owner-managed expiry cleanup remains
required for retained results. Standard output is only `EXPERIMENT_RECORDED`
(exit 0), `EXPERIMENT_FAILED` (exit 2), or `EXPERIMENT_CANCELLED` (exit 130).
Only explicit `--share-summary` replaces the success code with the non-identifying
`technical`/`private_quality`/`viability` summary; private payloads never print.

<a id="shared-model-tools"></a>

## Former Shared Research Setup

Original source: `docs/policies/project/development/model-tools.md`; complete original document SHA-256: `350eee3609fa402490bc4c198653bcbc79e1a435bee008b5e6ba3dd31b035ca2`.

Historical and unavailable: all operations in this chapter retain their original restrictions; none authorizes a current execution.

<a id="shared-model-tools-local-model-development-tools"></a>

### Local Model Development Tools

These are explicit source-checkout operations. They do not run as an automatic Session-processing pipeline.

The product backend and its model runtime are native Rust. Build or select the
native CLI using [the installation guide](../../policies/project/installation-and-storage.md).
The simulation and model-registration script entrypoints are standard-library
launchers for that binary; `LOCALBRAIN_EXECUTABLE` can select its absolute path.

Paused Python research comparisons use the narrow unshipped source fixture in
`tests/reference/`. If explicitly authorized to run them, prepare a separate
Python3.11 environment, install `tests/reference/requirements-model-comparison.txt`
and place that environment's `bin` first on the current shell's PATH. These
commands do not install Python into the product. Six historical search-engine
benchmarks additionally require `LOCALBRAIN_REFERENCE_ROOT` naming a separately
prepared frozen Python checkout and its matching environment; they refuse missing
inputs instead of selecting a backend fallback. See the
[reference boundary](#retired-python-research-tools) (former source:
`tests/reference/README.md`, retired with the fixture tree).

Public model weights stay in the shared Hub cache. Model registrations belong
under `<LOCALBRAIN_DATA_DIR>/models/<model-slug>`. Choose a private output
directory outside Git for each invocation and create its parent before passing
an explicit output path. These source-checkout tools are not invoked by normal
application startup.

<a id="shared-model-tools-operations"></a>

#### Operations

| Task | Guide |
| --- | --- |
| Compare search ranking and runtime | [Search comparisons](#search-comparisons) |
| Prepare/replay full-history affinity | [Session simulation](../../policies/project/development/session-simulation.md) |
| Run quoted work-context and protocol diagnostics | [Work context trials](#work-context-trials) |
| Run source-claim extraction/binding diagnostics | [Source claim trials](#source-claim-trials) |
| Run the bounded model-free comparator | [Work reconstruction](#work-reconstruction) |

<a id="simulation-model-roles"></a>

## Former Simulation And Research Model Roles

Original source: `docs/policies/project/development/session-simulation.md`; complete original document SHA-256: `3724eb56b53cefc5c1c1053c09c1c4e2bee7061ddaac4129ed4931a928b03e0d`.

Historical and unavailable: all operations in this chapter retain their original restrictions; none authorizes a current execution.


The following table describes simulation and work-reconstruction experiments.
Each experimental producer requires its own admission; another model consumer
does not admit a rejected extractor or reconstruction producer. The experimental
model roles remain separate:

| Model | Current purpose | Consumer/admission boundary |
| --- | --- | --- |
| Qwen3-Embedding-0.6B | Encode source chunks for similarity-based grouping | Prepared embeddings feed the observation-only map; browsing runs no model |
| Qwen3-4B | Explicit quoted work-context and relationship inference baseline | Synthetic-only quoted trials; no admitted map or private-history reconstruction consumer |
| Qwen3-8B | Explicit quoted work-context, protocol and source-claim diagnostics | No admitted work extractor/reconstruction producer or generative map |

These are pretrained models, not locally trained weights or LoRA adapters.
The installed 4B/8B assets are reusable independently of the embedding cache and
expiring evaluation reports. The commands below are explicit tools, not an
automatic pipeline for newly imported Sessions.

<a id="work-context-implementation"></a>

## Retired Quoted Context Implementation

Original source: `docs/policies/project/work-context-inference.md`; complete original document SHA-256: `590d838215b77a8172f3e4891df975fa32e40d843b370fb7a16be0bcd320b415`.

Historical and unavailable: all operations in this chapter retain their original restrictions; none authorizes a current execution.

<a id="work-context-implementation-implementation-ownership"></a>

#### Implementation Ownership

- `tests/reference/python/localbrain/experiments/context/contract.py`, `tests/reference/python/localbrain/experiments/context/staged.py`,
  `tests/reference/python/localbrain/experiments/context/classified.py`, `tests/reference/python/localbrain/experiments/context/selected.py`, and
  `tests/reference/python/localbrain/experiments/context/evaluation.py`:
  exact quoted work-unit/pair-relation contracts and synthetic-only admission
  evaluation, using explicit public-model installation and independently verified
  offline generation from `tests/reference/python/localbrain/models/generation.py`, with finite decoding from
  `tests/reference/python/localbrain/models/choices.py`. The current [quoted work-context contract](../../policies/project/work-context-inference.md#quoted-work-context-model-contract)
  owns the model, packet, generation and output boundaries. The evaluation opens no source
  DB and introduces no product consumer, training, organization write or automatic
  inference. Quoted fields retain role and locator; validity is not entailment.
  Staged inference validates intermediate source quotes and keeps full original
  context; it never fills missing output evidence. Thinking-mode protocol strips
  reasoning before decoding/storage. Strategy/stage/runtime identities separate
  caches; development and holdout gates are independent.
  MPS generation uses eager attention; the attention implementation is part of
  the runtime fingerprint.
  The installer admits only the allowlisted pinned 4B/8B catalog. Verification
  resolves the owner and model-specific assets, and inference identity uses that
  verified model; a 4B default must not label an 8B result.
  `tests/reference/python/localbrain/models/cache.py` resolves public pretrained assets in the user-wide Hugging
  Face Hub cache. Installation metadata remains in the explicit private model
  root: the directory owner marker stays v1, while a
  `localbrain.work-context-model.v2` model manifest has a Hub-relative snapshot.
  Legacy v1 manifests remain readable. Verification confines selected assets to
  their model repository and preserves their pinned hashes and inference identity.
  `tests/reference/python/localbrain/models/catalog.py` pins the supported public identities and feature requirements;
  `crates/models/src/assets.rs` owns independent LocalBrain embedding setup with a
  `localbrain.semantic-model/v1` Hub-relative manifest. The embedding adapter
  also accepts compatible older app-local and Hub-relative snapshot manifests.
  Private vectors and outputs remain in LocalBrain's runtime storage.
  App cleanup never owns deletion of shared public weights.
  Future trained adapters/checkpoints require separate durable project storage
  under the privacy policy.
  The opt-in classified strategy separates model-selected source roles and work
  membership from serialization. Its finite answer-code decoder constrains syntax,
  not truth; source spans are not work-unit boundaries. Original context and
  explicit model-selected citations feed the existing quote validators. Unknown
  membership, ambiguous spans and packet/case bounds fail without source loss
  being disguised as complete reconstruction. No private producer consumes it yet.
  The separate selected strategy chooses whole-conversation anchors before their
  field evidence through the same bounded decoder; it preserves anchors without
  silently filling missing citations or changing the classified comparator.
  The opt-in `tests/reference/python/localbrain/experiments/context/evidence.py` strategy assesses literal source facets
  before grouping independently resumable outcomes. Pairwise anchor/membership
  checks refuse ambiguous bridges; unit audits inspect proposed fields against
  original records. Continuation requires model-selected goal support,
  compatible scope and explicit linkage, with automatic uncertainty on support
  the model judges missing or conflicting. This does not guarantee recognition
  of semantic errors. Only model-selected facts are serialized. Its semantic
  label decoder explicitly admits up to 32 characters while legacy default codes
  remain bounded to eight; both keep the eight-token/EOS grammar.
  Evidence evaluation has failure-preserving, hashed terminal observations,
  changed-config/corrupt-cache refusal and bounded incomplete-case retries.
  Original development and compositional gates are separate. Holdout requires a
  complete identity-matched report whose observations/split scores are revalidated;
  primary semantic review remains required. No product consumer is admitted by
  valid syntax, automatic withholding or same-model auditing alone.


- `tests/reference/python/localbrain/experiments/context/diagnostic.py`: opt-in fixed-model synthetic protocol diagnosis,
  separate from extraction/admission and any product producer. Its frozen matrix
  independently controls option order and numeric mapping; label/text responses
  keep the same source context and alternative meanings. Semantic, protocol and
  literal-citation results are distinct. Prompt/template hashes and actual answer
  token IDs make rendering auditable. Completed wrong/invalid/refused observations
  remain cached, changed configurations refuse reuse, and cumulative attempt/time
  budgets survive clean interruption. An unclean in-flight reservation blocks
  automatic restart. Diagnostic completeness never grants model admission.
  No database, holdout, new dependency, model or UI is involved.


- `tests/reference/python/localbrain/experiments/context/role_comparison.py`: a separate matched synthetic formulation diagnostic.
  It reuses unchanged evidence-first facet definitions and relation inference,
  contrasting independent questions with one complete role-set decision. Compound
  roles, identical focused spans with different later context, and canonical/
  reversed option orders remain explicit. Scoring compares role sets per context,
  not incompatible raw call counts; relationship controls are scored separately.
  An execution meter wraps existing `choose` without changing the decoder or
  existing strategies. Every choice reserves cumulative call/time accounting;
  incomplete observations have bounded attempts, while completed refusals/errors
  are hashed and replayed. Existing private evaluation storage ownership applies.
  Prompt/template/token audits are synthetic diagnostics, not private-source
  discovery, model admission, training or a product producer.

<a id="reconstruction-implementation"></a>

## Retired Reconstruction Implementation

Original source: `docs/policies/project/work-reconstruction.md`; complete original document SHA-256: `dac4de2adadf0f433f252906915b7c31f30acf15934d5d7f976efde6dbe5354d`.

Historical and unavailable: all operations in this chapter retain their original restrictions; none authorizes a current execution.

<a id="reconstruction-implementation-implementation-ownership"></a>

#### Implementation Ownership

- `tests/reference/python/localbrain/experiments/reconstruction/contract.py`: isolated experimental text extraction,
  semantic grouping, exact synthetic corrections, and metadata-only comparator

- `tests/reference/python/localbrain/experiments/reconstruction/scoring.py`: independent expectation
  validation, integer quality measures, and identity/assignment replay measures

- `tests/reference/python/localbrain/experiments/reconstruction/input.py`: explicit manifest validation and
  bounded read-only access to already-indexed selected records

- `tests/reference/python/localbrain/experiments/reconstruction/preparation.py`: explicitly invoked,
  prediction-independent chronological sampling, frozen manifests, omission
  accounting, and unknown-assessment placeholders; no independent answer key

- `tests/reference/python/localbrain/experiments/reconstruction/experiment.py` and
  `scripts/experiment-work-reconstruction.py`: opt-in local comparison command,
  supervised resource bounds, and private owner/expiry-bound result publication

<a id="source-claim-implementation"></a>

## Retired Claim And State Implementation

Original source: `docs/policies/project/source-claims-and-work-state.md`; complete original document SHA-256: `2d46ba2ad1095832c353ed1e42cf7dd266efd48ddaeed883718c3f09070f143d`.

Historical and unavailable: all operations in this chapter retain their original restrictions; none authorizes a current execution.

<a id="source-claim-implementation-implementation-ownership"></a>

#### Implementation Ownership

- `tests/reference/python/localbrain/experiments/claims/state.py`: pure source-claim/reported-state projection: unchanged
  synthetic-supplied v1 plus model-aware v2 provenance/lifecycle effects, governed
  by [Source Claims And Work State](../../policies/project/source-claims-and-work-state.md).
  Separates exact anchors, attributed interpretations, scoped target bindings and
  current state; preserves historical pending claims, partial order, corrections,
  unresolved support and replay identities. The projector has no source reader,
  model call, persistent ledger, automatic target discovery or product consumer.
  It cannot certify the truth of a supplied interpretation or unblock admission.

- `tests/reference/python/localbrain/experiments/claims/contract.py`, `tests/reference/python/localbrain/experiments/claims/assessment.py`, `tests/reference/python/localbrain/experiments/claims/trial.py`: separately
  invoked synthetic-only extraction/binding adapter, conditional versus end-to-end
  scoring and bounded failure-preserving evaluation. No private or UI consumer.
  This adapter invokes the installed generative model during explicit trials;
  it is separate from the pure state projector and the affinity-map producer.
