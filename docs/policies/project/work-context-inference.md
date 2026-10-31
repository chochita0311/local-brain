# Work Context Inference

This contract owns quoted model input/output, generation identity, strategy behavior and synthetic protocol diagnostics. [Model Trial Operations](development/work-context-trials.md) owns invocation; a valid protocol is not semantic model admission.

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

The generator verifies an installed allowlisted model/revision and its assets
before use. `auto` selects MPS when available, otherwise CUDA, otherwise CPU;
explicit `mps`, `cuda` and `cpu` remain available. CPU uses float32, other devices
bfloat16; MPS uses eager attention and other devices use SDPA. Model/revision,
asset fingerprint, device, dtype, attention, Python/Torch/Transformers versions,
generation settings, strategy prompts/projection/bounds and output protocol are
part of the compatible inference identity. Public pinned 4B and 8B installations
retain separate identities; neither a default model label nor cache relocation
can substitute for verified assets.

| Generation setting | Current accepted value |
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

## Implementation Ownership

- `experiments/context/contract.py`, `experiments/context/staged.py`,
  `experiments/context/classified.py`, `experiments/context/selected.py`, and
  `experiments/context/evaluation.py`:
  exact quoted work-unit/pair-relation contracts and synthetic-only admission
  evaluation, using explicit public-model installation and independently verified
  offline generation from `models/generation.py`, with finite decoding from
  `models/choices.py`. The current [quoted work-context contract](#quoted-work-context-model-contract)
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
  `models/cache.py` resolves public pretrained assets in the user-wide Hugging
  Face Hub cache. Installation metadata remains in the explicit private model
  root: the directory owner marker stays v1, while a
  `localbrain.work-context-model.v2` model manifest has a Hub-relative snapshot.
  Legacy v1 manifests remain readable. Verification confines selected assets to
  their model repository and preserves their pinned hashes and inference identity.
  `models/catalog.py` pins the supported public identities and feature requirements;
  `models/installation.py` owns independent LocalBrain embedding setup with a
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
  The opt-in `experiments/context/evidence.py` strategy assesses literal source facets
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


- `experiments/context/diagnostic.py`: opt-in fixed-model synthetic protocol diagnosis,
  separate from extraction/admission and any product producer. Its frozen matrix
  independently controls option order and numeric mapping; label/text responses
  keep the same source context and alternative meanings. Semantic, protocol and
  literal-citation results are distinct. Prompt/template hashes and actual answer
  token IDs make rendering auditable. Completed wrong/invalid/refused observations
  remain cached, changed configurations refuse reuse, and cumulative attempt/time
  budgets survive clean interruption. An unclean in-flight reservation blocks
  automatic restart. Diagnostic completeness never grants model admission.
  No database, holdout, new dependency, model or UI is involved.


- `experiments/context/role_comparison.py`: a separate matched synthetic formulation diagnostic.
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
