# Work Context Inference

This contract owns the retained quoted input/output, identity, strategy and
synthetic-diagnostic requirements. The Python strategies and trial suites are
retired; no quoted extractor or diagnostic command is currently available.
[Trial status](development/work-context-trials.md) routes the complete historical
procedures. These rules do not admit a model or a private/product consumer.

## Quoted Work-Context Model Contract

The quoted extractor and pair-relation validator consume supplied conversation
packets; they do not discover private input. `extract` accepts exactly
`{"messages": [...]}`; `relate` accepts exactly `{"left": [...], "right": [...]}`.
Each message has exactly `id`, `role`, `at` and `text`: the ID matches
`[A-Za-z0-9_-]{1,64}`, role is `user` or `assistant`, `at` is null or a string,
and text is a nonblank string. Each admitted message collection contains 1–128
messages with unique IDs and at most 40,000 total text characters. A pair must
also satisfy these bounds and ID uniqueness across the combined left/right
collection. Source records are untrusted evidence, never instructions.

The `quoted-work-context.v2` prompt distinguishes independently resumable
outcomes from messages, references and phases: investigation, implementation and
testing of one goal stay together. Requests/plans do not establish completion;
assistant claims are not user confirmation. Unknown fields remain null or empty.

| Wire object | Current contract |
| --- | --- |
| Free-form model response | One JSON object, at most 24,000 characters; duplicate keys, non-finite constants and invalid JSON refuse |
| Evidence | Exactly `message` and `quote`; an admitted message ID and a nonblank exact original substring of 1–600 characters occurring exactly once in that message |
| Extract response | Exactly `units`; at most eight units. Each has exactly `goal`, `target`, `progress`, `results`, `remaining`; goal/target are null or evidence objects, each list has at most eight evidence objects and no repeated `(message,start,end)` span |
| Unit validity | At least one populated field; duplicate grounded unit identities refuse. Grounding adds exact start/end, speaker, time and `source-attributed` authority; unit IDs hash the grounded fields and retain `inferred-work-unit` authority |
| Pair response | Exactly `relation`, `evidence`, `link`; relation is `continues`, `related`, `independent` or `uncertain`, with at most eight distinct grounded evidence spans |
| Pair evidence | Every non-uncertain label cites both conversations. `continues` requires a grounded link in the right conversation whose message is also cited; all other labels require `link=null` |

Continuation semantically requires compatible goals and an explicit right-side
link to earlier work. Shared words, artifacts, repositories or nearby dates are
insufficient; a time gap alone does not disprove continuation. `related` records
a shared topic without established same-goal continuity or distinct outcomes;
`independent` needs distinct goals/targets or an explicit denial; insufficient
evidence remains `uncertain`. Structural quote validation cannot prove these
semantic judgments. Output retains `authority: inferred` and the prompt version.

The following device/dtype/attention and Python-runtime identity rules retain
the retired quoted-research generator's reproduction contract. They do not
describe Candle or an available quoted adapter. That generator verifies an
installed allowlisted model/revision and its assets before use. `auto` selects
MPS when available, otherwise CUDA, otherwise CPU;
explicit `mps`, `cuda` and `cpu` remain available. CPU uses float32, other devices
bfloat16; MPS uses eager attention and other devices use SDPA. Model/revision,
asset fingerprint, device, dtype, attention, Python/Torch/Transformers versions,
generation settings, strategy prompts/projection/bounds and output protocol are
part of the compatible inference identity. Public pinned 4B and 8B installations
retain separate identities; neither a default model label nor cache relocation
can substitute for verified assets.

| Retained research generation setting | Required value |
| --- | --- |
| `thinking` / decoding | Actual boolean; `greedy` or `sampled`, with thinking allowed only with sampled decoding |
| Non-thinking token budgets | Combined default/ceiling 8,192; generated default/ceiling 2,048 |
| Thinking token budgets | Combined default/ceiling 16,384; reasoning-plus-final generated default/ceiling 8,192 |
| Reduced budgets | Actual integers: combined at least 1,024, output at least 128, each within its mode ceiling, and output strictly below combined |
| Call time | Soft generation limit: actual integer 1–180 seconds, default 180; operation-specific smaller limits still apply; no hard preemption of an in-flight model call |
| Sampling | Non-thinking: temperature 0.7/top-p 0.8; thinking: 0.6/0.95; top-k 20 and stable `sha256-system-and-content-prefix32` seed; greedy has no sampling object |
| Output protocol | `qwen-final-only.v1`; reasoning is counted but never decoded or retained, and only the final answer is validated/stored |

Tokenization never truncates: rendered input tokens plus the reserved
`max_output` must not exceed `max_tokens`, otherwise generation refuses with
`CONTEXT_TOO_LARGE`. Constrained choice reserves its finite code/EOS grammar
instead. A free-form response must finish with EOS; missing EOS is
`OUTPUT_TRUNCATED`. Thinking output requires exactly one closing `</think>`
token and at least one final-answer token before EOS; non-thinking output refuses
thinking delimiters. Reasoning token IDs are counted without decoding them.
These checks enforce protocol and bounds, not semantic truth.

`single`, `staged`, `classified`, `selected` and `evidence` keep separate
fingerprints and failure behavior. Source-choice modes serialize only explicitly
model-selected original quotes, never repair missing citations or turn syntax
into truth. Their packet/case bounds and protocol/admission operations are in the
[Developer Guide](development/work-context-trials.md#operations). No quoted
strategy is admitted to a private-history or product reconstruction consumer.

## Retained Strategy And Diagnostic Requirements

Any reintroduced quoted strategy must retain role/locator attribution; valid
quotes are not entailment. Staged inference validates intermediate original
quotes and keeps the full original context without filling missing evidence.
Strategy/stage/runtime cache identities and independent development/holdout
gates remain separate. A verified 4B default cannot label an 8B result.

Classified source roles and work membership remain separate from serialization;
source spans are not work-unit boundaries. Unknown membership, ambiguous spans
and packet/case overflow refuse without disguising lost source as complete
reconstruction. Selected mode chooses whole-conversation anchors before field
evidence and preserves them without supplying missing citations or changing the
classified comparator. The finite decoder constrains syntax, not truth.

Evidence-first assessment examines literal facets before grouping independently
resumable outcomes. Pairwise anchor/membership checks refuse ambiguous bridges;
unit audits compare proposed fields with original records. Continuation requires
model-selected goal support, compatible scope and explicit linkage. Missing or
conflicting support judged by the model withholds a relation; this cannot
guarantee recognition of semantic mistakes. Only model-selected facts serialize.
Semantic-label codes admit 32 characters, legacy codes eight, both with the
same eight-token/EOS grammar. Hashed terminal failures remain replayable;
changed configurations/corrupt caches refuse and incomplete-case retries stay
bounded. Original development/compositional gates are independent. Holdout needs
a complete identity-matched report with revalidated observations/split scores
and primary semantic review; syntax, withholding or same-model audits do not
admit a product consumer.

Protocol diagnosis remains separate from extraction/admission. A frozen matrix
must independently control option order/numeric mapping while label/text
responses retain the same original context and alternatives. Semantic, protocol
and literal-citation results stay distinct. Prompt/template hashes and actual
answer token IDs remain auditable. Completed wrong/invalid/refused observations
replay; configuration changes refuse; cumulative calls/time survive clean
interruption and unknown in-flight reservations block restart. Completeness
admits no model, database, holdout, new dependency or UI use.

Matched role-formulation diagnosis compares independent questions with a
complete role-set choice on identical focused spans, including changed later
context, compound roles and canonical/reversed options. Score role sets per
context, not incompatible raw call counts; score relationship controls
separately. A meter may wrap the unchanged `choose` decoder without changing
existing strategies: every choice reserves cumulative calls/time, incomplete
observations have bounded attempts and completed errors/refusals are hashed and
replayed under the existing private owner/lock/expiry rules. These are synthetic
diagnostics, never training, private-source discovery or model admission.

## Implementation Ownership

`crates/models/src/` owns current native pinned assets, tokenization, generation
and finite-choice primitives; `crates/core/src/backend/models/` owns application
model setup. Neither provides the retired quoted strategies or trial consumers.
The retained installation contract admits only the allowlisted pinned 4B/8B
catalog. Verification resolves the owner and model-specific assets; a default
4B label cannot identify an 8B result. The directory owner marker stays v1;
`localbrain.work-context-model.v2` uses a Hub-relative snapshot and legacy v1
app-local manifests remain readable. Selected assets remain confined to their
model repository with pinned hashes and inference identity preserved.
`crates/models/src/assets.rs` owns independent embedding setup with a
`localbrain.semantic-model/v1` Hub-relative manifest and compatible older
app-local/Hub-relative snapshot manifests. Private vectors and outputs keep
LocalBrain's runtime owner. Public pretrained assets remain in the shared Hub
cache and app cleanup never deletes shared weights. Future trained
adapters/checkpoints need separate durable project storage and backups under
the privacy policy.

The [former implementation explanation](../../plans/research/retired-python-research-tools.md#work-context-implementation)
retains exact retired source ownership, model-manifest generations and strategy
mechanics. No unavailable Python module is a current implementation owner.
