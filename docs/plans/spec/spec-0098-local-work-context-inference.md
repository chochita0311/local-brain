# SPEC-0098: Local Work Context Inference

## Metadata

- ID: `spec-0098`
- Status: `approved`
- Run: [RUN-20260923-110](../run/run-20260923-110-work-role-formulation-comparison.md)
- Attempt: `1`
- Parent Feature: [FEAT-0098](../feature/feat-0098-local-work-context-inference.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `infra`, then `data`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-23`

## Implementation Contract

- Model installation accepts only `Qwen/Qwen3-4B` at immutable revision
  `1cfa9a7208912126459214e8b04321603b3df60c`, or the separately approved
  `Qwen/Qwen3-8B` at `b968826d9c46dd6066d109eabc6255188de91218`.
  Download the named safetensors,
  tokenizer/config files and license from the official host without a token.
  Pin public weight hashes, inventory all admitted assets and rehash before use.
  Reject unknown directory ownership and symlink/path escapes. An exclusive
  installer lock protects resumable public cache; publish a manifest atomically.
- Runtime imports the existing optional dependencies lazily. Use eval/inference
  mode, local-files-only, no remote code, offline/telemetry settings and the
  existing outbound-socket guard. Initial mode is non-thinking greedy decoding,
  one packet at a time, 8,192 total input/output tokens, at most 2,048 output
  tokens and a 180-second generation bound; oversized requests fail rather than
  truncate and time/token-stopped output without EOS is rejected. Record the actual
  runtime, dtype and device. Sampling/rounding changes require a new identity.
  A separate non-thinking comparison may use the official recommended
  temperature 0.7/top-p 0.8/top-k 20 settings, with a content-derived fixed seed.
  This is a versioned decoding comparison, not repeated seeds until a case passes;
  no bit-identical fresh generation guarantee is claimed across devices/runtimes.
- Packets contain synthetic or policy-admitted ordered messages with local
  IDs, original roles, dates and text. Message IDs/quotes are data, not tool
  instructions. Extraction outputs `units`, each with nullable `goal`/`target`
  and lists `progress`, `results`, `remaining`. A field is an exact
  `{message, quote}` pair, not a free unsupported summary. Validation adds
  source character offsets, role and date. Semantic entailment still needs
  evaluation; substring validity alone is not truth.
- Pair evaluation receives two separately identified packets. Output relation
  is `continues`, `related`, `independent` or `uncertain`, with quoted evidence
  and an explicit quoted link for `continues`. No gap-based close/reopen or
  structural merge/branch is emitted. A validator enforces shape/grounding;
  quality tests separately judge the relation against fixed expectations.
- All outputs remain `inferred`; assistant results are attributed claims,
  not verified completion. Empty fields/uncertainty are legitimate. Reject
  fabricated IDs/quotes, ambiguous quote locations, output beyond bounds,
  duplicate keys, nonfinite JSON and incomplete generation. No retry repairs
  fabricate a missing field or reinterpret an invalid verdict.
- Freeze development/holdout synthetic cases before the trial. Use development
  cases only for bounded fixes; holdout failures are reported, not used for
  repeated tuning. The gate requires every negative control and at least 80%
  of positive checks. Include mixed goals, implicit follow-up, explicit distant
  resumption, same-topic different goals, negated continuation, missing evidence,
  assistant-only completion, source instruction injection and long-input refusal.
- Evaluation state stays in an explicit private owner directory with 30-day
  inactivity expiry, exclusive writer, atomic per-case checkpoints, input/model/
  prompt fingerprints, interrupt/resume, fixed stdout and a complete/partial
  distinction. Completed fixtures may be safely reused only with identical
  identities; an interrupted/invalid result is not cached as a success.
  No private corpus is opened by this first quality command.

## Acceptance Mapping

Unit tests verify boundaries using synthetic packets and injected runtimes.
Installed-model evaluation proves actual local generation and quality for the
frozen cases only. Report runtime correctness and semantic pass/fail separately.
A failing model gate stops before corpus execution; it is not permission to
download another model or weaken the test. A pass is readiness for the separate
full-history producer, not a claim that actual work flows are reconstructed.

## Approved Same-Model Comparison — 2026-09-23

The owner approved this continuation after RUN-104's non-thinking admission
failure. Freeze the following two candidates before further model generation:

1. `single-thinking`: unchanged v2 extraction/relation prompts with thinking
   enabled; sampled temperature 0.6/top-p 0.95/top-k 20, one content-derived seed.
   Allow 16,384 total tokens and at most 8,192 generated tokens including
   reasoning, with the existing 180-second per-generation bound. Require EOS
   and exactly one Qwen thinking-end marker; decode/store only the final answer.
   Reasoning text is not evidence, a prompt for another stage, or a diagnostic
   artifact. Retain only token counts. These are bounded experimental budgets,
   not a claim to test the model's maximum reasoning capability.
2. `staged-non-thinking`: existing non-thinking sampled decoding and budgets.
   Extraction first inventories exact work anchors across the entire conversation,
   then extracts exactly one unit per validated anchor using the original full
   messages. An anchor may represent a goal or an activity with unknown goal;
   it is not one unit per message. The unit must retain its anchor as evidence.
   Pair inference first selects quoted evidence separately from left and right,
   then judges using the originals and validated selection. The final judgment
   still must itself satisfy bilateral evidence and explicit-link requirements;
   no missing citations are filled in by the harness. All intermediate output
   is inferred and quote-validated; failure aborts the case without repair.

Each candidate runs the existing four development cases once. Do not retune
prompts, seeds or expectations within this comparison. Only a development gate
pass qualifies for holdout. If both qualify, choose fewer generated tokens over
the four cases (tie: single-thinking), rather than load-biased wall time. Freeze
the selection before running its ten untouched holdout cases once. Both split
gates must pass; do not blend their scores to hide a holdout failure. No qualifying
candidate means stop without consuming holdout. No tuning on holdout failures.

Strategy, stage prompts, decoding, budgets and protocol version participate in
cache identity. Aggregate per-stage call/time/token metrics without losing the
failing stage. Use separate explicitly owned evaluation folders for each
candidate/split so old failures remain evidence; each retains the existing
exclusive lock, atomic checkpoints and 30-day inactivity expiry. Case-level
resume can recompute an interrupted staged case, never reuse a partial unit.

Sampling and thinking protocol follow the
[official Qwen3-4B model card](https://huggingface.co/Qwen/Qwen3-4B).

### Runtime Correction Within The Comparison

The first thinking execution repeatedly failed inside token sampling with a
nonfinite/negative-probability error, before any final answer was evaluated.
Do not repair logits or mask invalid probabilities into apparently valid output.
Use the installed library's eager attention on MPS, retaining SDPA elsewhere,
and include this choice in runtime identity. This bypasses a path with a documented
[MPS SDPA correctness issue](https://github.com/pytorch/pytorch/issues/174861)
without updating dependencies or model weights. A small standalone tensor probe
did not reproduce that issue at lengths 1,023–2,048; the exact kernel root cause
is not yet proven by the model error alone. One corrected-runtime pass of the
same two frozen candidates is allowed as an implementation correction, not
prompt/seed/expectation tuning. Preserve pre-correction failure evidence.

## Open Blockers

The owner-approved RUN-109 candidate below is implemented and evaluated, but
fails both development cohorts and primary semantic review. Requests/plans are
misassigned to performed work; topic-only similarity can become continuation
despite same-model audits. This is a planning gap in the inference approach, not
an unfinished calculation. Holdout/private application remain blocked. Preserve
this frozen rejected candidate and earlier evidence; a new bounded approach
requires its own decision. RUN-108's diagnostic PASS does not override this gate.
RUN-110's approved comparison below is now complete and has no open diagnostic
blocker. Direct selection reduces extra roles but introduces omissions, fails
fulfilled-pending reconciliation and leaves false continuity in the unchanged
control pipeline. Model admission remains blocked independently. The subsequent
source-claim/current-state review was approved and implemented separately under
[FEAT-0099/RUN-111](../run/run-20260923-111-source-claims-and-work-state-projection.md).
Its supplied-input foundation passed; the later
[FEAT-0100/RUN-112 adapter trial](../run/run-20260923-112-source-claim-extraction-and-binding-trial.md)
failed semantic admission. That completed review is no longer a pending decision;
none of these results changes this Spec's definitions or admission gates.

## Approved Role Formulation Comparison — RUN-110

Implement a separate synthetic-only comparison, not a new extraction strategy.
Use the installed 8B with RUN-109's fixed MPS/eager/bfloat16/non-thinking/greedy
runtime, 8,192 context, 128 free-output setting and 30-second generation bound.
Keep legacy modules, prompts, identities, expectations and report folders intact.

- Freeze sixteen new focused contexts covering a requested goal, performed
  action, reported success/failure, pending work, planned versus performed checks,
  action-plus-result, action-plus-pending, examples, gratitude, unknown-goal
  activity, interleaved goals and goal-plus-pending. Include the exact same earlier
  pending span followed by completion of its own work versus different work.
- Compare RUN-109's four independent goal/progress/results/remaining questions
  against one direct role-set selection with the same four facet definitions.
  Enumerate every subset plus uncertainty; legitimate compound statements must
  not be forced into one role. Keep the original system prompt, original full
  context and content-derived focused span identical across methods.
- Run canonical and reversed alternative order for both methods. This is a
  bounded two-order sensitivity check, not all permutations or isolated proof
  about wording, tokenizer bias or decoding constraints. Different question shape,
  option count and call count are explicit comparison factors. No order voting.
- Score the assembled four-field set per case/order, not four independent calls
  against one direct call. Missing/invalid/uncertain results cannot become an empty
  set or a success. Report exact matches, extra/missing roles, per-field confusion,
  both-order correctness/stability, paired wins/losses and constant none/all-role/
  uncertain baselines. Small synthetic counts
  do not establish real-work accuracy or statistical significance.
- Run six new relationship controls once through unchanged `infer_evidence`:
  contextless/grounded short resumption, topic-only similarity, shared-file distinct
  goals, long-gap continuity and reused-ID conflict. Keep their original quoted
  outputs/attribution and separate expected labels. They test remaining continuity
  defects; they do not compare a new direct relationship strategy or replace the
  original admission/holdout requirements.
- Freeze one versioned suite/matrix/runtime identity before generation. Record
  actual prompt/template hashes and answer token IDs. Preflight every semantic
  vocabulary with the installed tokenizer before inference; retain the explicit
  32-character/eight-token/EOS contract. Do not store hidden reasoning or repair
  wrong choices. Source roles and exact locators are evidence, not verification.
- Reuse the existing private evaluation owner, writer lock, atomic checkpoints
  and 30-day inactivity expiry. Hash raw observations including relationship
  results; verify/re-score cached observations before replay. Completed successes,
  errors, refusals and wrong answers never regenerate. Changed unexpired config,
  corrupt observations or unclean in-flight state refuse without replacing them.
- Bound the entire comparison to 512 actual choice attempts and 1,200 cumulative
  soft seconds, retaining spent budgets across clean interruption. A focused
  observation has one call; relationship observations retain RUN-109's 96-call /
  120-second case bound. Allow at most two attempts for an incomplete observation;
  reserve before every actual call so an OS kill cannot reset accounting. No
  case/prompt/seed changes after actual answers, and no automatic budget extension.

The CLI accepts only the repository's frozen synthetic suite, selected installed
model and owned output folder, plus a no-model description mode. No private-input,
database, holdout, alternate-device/model or tuning switches. A complete report
is diagnostic evidence only and contains no admission PASS. Review every matched
role result and every relation control before recommending any integration.

## Approved Evidence-First Candidate — RUN-109

Add one opt-in `evidence` strategy on the existing pinned 8B, MPS/eager/bfloat16,
non-thinking greedy runtime. Keep all historical strategies/identities unchanged.
No model or dependency installation, training, private input or UI work.

- Original messages remain the only evidence. Enumerate existing bounded literal
  spans, validate unique quote locations, and identify spans by content-derived
  IDs. Spans are selectable evidence, never automatically work units. Preserve
  full original context and chronology in each semantic decision; no truncation.
- Replace numeric/ordinal answer mappings with explicitly defined semantic
  labels. The evidence strategy explicitly opts into a versioned 32-character
  label bound; legacy codes retain their eight-character default. Keep the same
  character whitelist, eight-token limit and code/EOS grammar, with preflight and
  real-adapter tests. Independently assess goal, reported action, reported outcome and still
  pending work for each span. A statement can support several fields, but a plan
  cannot become performed work and an assistant claim cannot become verification.
  Unresolved field meaning refuses extraction rather than silently dropping it.
- Group goal evidence by pairwise same-outcome judgments over original context.
  Require agreement with every existing goal anchor in the group; contradictory,
  uncertain or multiply matching membership refuses rather than creating a bridge.
  Match activities to explicitly quoted candidate work, not numbered/ordinal
  goals. Unmatched supported activity can retain an unknown goal, never invent one.
- Only model-selected facts populate fields. Choose a stable chronological
  representative for equivalent goal/target evidence; keep all selected list
  fields within the existing eight-item/unit limits. Audit each proposed unit
  against original sources; rejection/uncertainty refuses, not repairs, the unit.
- For relations, select recoverable goal evidence on each side before assessing
  same goal, distinct goals, shared topic or insufficient context. Continuation
  additionally requires compatible scope, a model-selected right-side explicit
  link and a supported final evidence audit. A conversation-level pronoun/link
  without recoverable work goals is insufficient. Non-uncertain output still
  needs model-selected evidence from both sides. Conflicting or absent support
  automatically returns uncertain, with a content-free reason in the trace.
- Code assembles exact citations and derives the verdict from assessed evidence;
  it does not rewrite a wrong free-text answer or invent a missing quotation.
  Test contradictory evidence assessments and audit rejection explicitly. There
  is no free-form label/reason pair to repair; the same-model audit is an inferred
  safeguard, not independent truth. Primary review must inspect every final case
  and the decision trace behind any failure or abstention.
- Bound one case attempt to 32 spans, 96 model calls and 120 soft seconds; each
  generation has a 30-second soft bound and 8,192 context / 128 output settings.
  The finite-choice adapter uses its smaller actual code/EOS token limit. Refuse
  bounds rather than silently lose coverage. A clean interruption permits at
  most one additional attempt for its incomplete case; completed failures do not
  rerun. An unclean in-flight crash refuses automatic resume. No fresh seeds,
  order voting or prompt changes after actual outputs.
- Extend the synthetic evaluator only for this strategy with fingerprinted
  failure-preserving replay and changed-config/corrupt-cache refusal. Keep the
  existing owned/locked/atomic/30-day expiry storage. Preserve original evaluator
  behavior for historical strategies. Separate original development and new
  compositional split gates; one cannot compensate for the other's failure.
- Freeze twelve new compositional cases before inference: six extraction cases
  covering interleaved goals, same-goal phases, plans, unknown-goal activity,
  non-work instruction examples and attributed completed work; six relations
  covering missing versus recoverable context for the same continuation phrase,
  shared artifacts, topic-only similarity, long gaps and incompatible reused IDs.
  Check field-to-goal association, absent/performed state and speaker attribution,
  not only unit counts or a matching keyword. Original four development cases
  and ten holdout cases/expectations remain unchanged.

Run the sixteen development/compositional cases once, no diagnostic re-tuning.
Each split requires all negative controls and at least 80% positives, plus primary
semantic safety review. Only then run the unchanged ten-case holdout once in a
separate owned folder. The CLI must require a complete, identity-matched, re-scored
passing development report before this candidate's holdout; an aggregate or stale
PASS is insufficient. Do not blend all splits into one inference invocation.
Failed development stops before holdout; failed holdout stops without tuning.
The worst-case normal development bound is 1,536 calls / 1,920 soft seconds;
clean interruption allowances are explicit, not retries of completed failures.
No synthetic outcome starts private all-history processing in this Run.

## Approved Protocol Diagnostic — RUN-108

The owner approved the research-proposed controlled diagnostic. Use the existing
pinned 8B model only, MPS eager/bfloat16, non-thinking greedy inference. Preserve
all prior strategies, fixtures, expectations and unconsumed model holdout.

- Add a separate synthetic-only diagnostic command, not another extraction
  strategy or private-data input path. Freeze twelve new cases before generation:
  six focused field decisions (goal, request in mixed context, reported activity,
  reported result, pending work, social acknowledgement), two work-membership
  decisions, and four relationship decisions. These are narrower diagnostic
  decisions, not substitutes for whole-conversation extraction.
- Each question has four fully defined semantic alternatives. Numeric choices
  cross four cyclic option orders with four independent cyclic code mappings
  (16 cells). Constrained semantic-label and unconstrained short-text forms each
  use the four orders (4 cells each). Total: 24 conditions per case, 288 cells.
  Store options as an ordered list and record actual answer/label mappings,
  prompt/template hashes and label token IDs. Do not shuffle source chronology.
- All forms use the same original context, focus/question and alternative
  meanings. Only response representation/requirements and the prescribed
  ordering/mapping differ. Short text asks for a decision, one brief source-based
  explanation and exact evidence; it does not request hidden reasoning. Extra
  explanation/citation work means this is protocol sensitivity, not a pure
  isolated proof about the constraint callback.
- Separate recognized semantic decisions, strict protocol validity, correctness
  and text-quote grounding. Numeric/label cells do not claim citation generation.
  Text citations must reference supplied IDs and unique literal source spans;
  required source sides/focus must be present. Literal grounding is not semantic
  entailment; primary review inspects every distinct short-text response.
  Ambiguous/unrecognized text stays unscored/incorrect automatically, never
  repaired to the expected label. Failed and unknown conditions stay in totals.
- Fix total context/output limits to 4,096/256 tokens, 30 seconds per call, 1,200
  cumulative run seconds and 300 attempted calls including interrupted attempts.
  Time limits are soft checks, not hard OS cancellation guarantees. No source
  truncation, repeated seeds, unplanned prompt variants or automatic retries.
- Reuse the explicit outside-Git evaluation owner/lock/atomic-file/30-day expiry
  contract. Fingerprint model/runtime, cases and expectations, prompts, matrix,
  parser and limits. Refuse a changed configuration in an existing unexpired
  diagnostic folder. Cache every completed observation, including wrong answers,
  invalid protocol and generation refusals. Re-score cached raw observations;
  interrupted in-flight cells alone may rerun within cumulative budgets.
  Persist a pre-call reservation and conservative in-flight time charge so a
  crash cannot reset the budget. Never represent incomplete state as complete.
- Reports explicitly set diagnostic-only scope and model admission false. Report
  all 288 conditions, per-family/form counts, order/code sensitivity by base case,
  generation/format/grounding failures and resources. The 288 correlated
  conditions are twelve base cases, not 288 independent quality samples.
  Complete diagnosis, not a particular model score, is this Run's completion
  criterion; the Feature's broader model-quality gate remains unchanged.

Finish after this one frozen matrix and primary semantic review. The outcome
chooses the next bounded approach recommendation; it does not start a revised
producer, private corpus job, embedding rebuild, UI change or larger-model trial.

## Approved Model-Size Comparison — RUN-106

The owner approved the additional 8B installation after RUN-105's failed quality
gate. Its frozen public asset set contains five safetensor shards plus the same
seven tokenizer/config/license files and index: 16,397,443,036 bytes (16.40 GB /
15.27 GiB). Use a separate owned model directory and the existing content-addressed
cache, not a duplicate copied snapshot. Retain the 4B baseline; no implicit purge,
quantization, dependency upgrade, training or source transmission is authorized.
If the HTTP transfer stalls, the already-installed official Xet downloader may
be selected with a new empty private task-owned transfer directory outside Git.
Set its cache location before library import, disable chunk/shard caches, and
retain completed model blobs. No unknown directory adoption or shared-cache
diagnostic writes. After the installer process exits, remove that exact owned
transfer scratch; keep only the durable model cache and manifest. This changes
transport only, never model assets, inference settings or benchmark expectations.

The install command accepts an explicit allowlisted model ID; default remains
4B for compatibility. Verification/inference resolve only a matching known
owner marker, revision and asset inventory, never arbitrary model IDs or paths.
Explicit model mismatch must fail without changing the existing installation.
Runtime identity uses the verified model, not the historical 4B default.

Run 8B with the same two frozen strategies, sampling, seeds, prompts, MPS eager
attention and token/time limits as RUN-105 attempt 2. Do not edit expectations,
repair output or search seeds. Compare all four development cases once per
strategy. Admit only a candidate passing the fixed development gate AND primary
review of field association, requested versus reported progress, and evidence
entailment. A gate score alone cannot override the previously observed semantic
failure modes. If both qualify, use fewer generated tokens (tie: single-thinking).
Freeze selection before its one execution of the ten untouched holdout cases.
Any holdout or semantic safety failure stops admission; no tuning on those cases.

Keep separate owned candidate/split evaluation state, with the existing replay,
lock and expiry rules. A pass establishes readiness for the separate all-history
producer, not private-corpus quality, stable workflow identity or UI acceptance.

Public size/revision evidence: [official Qwen3-8B files](https://huggingface.co/Qwen/Qwen3-8B/tree/b968826d9c46dd6066d109eabc6255188de91218).

## Approved Source-Selected Extraction — RUN-107

The owner approved improving extraction rather than recalculating embeddings.
Add an opt-in `classified` strategy; preserve both historical strategies and their
identities. This candidate uses the already-installed pinned 8B model with MPS
eager attention and non-thinking greedy choices. No downloads, new dependencies,
training, private execution, vector changes or UI work belong to this Run.

Replace free-form object/quote generation with explicit model choices:

- Deterministically enumerate source sentence/line spans, splitting long spans
  at a whitespace boundary or 600 characters. Preserve exact text, message ID,
  order, role and date; pass the original full packet at every decision. At most
  64 spans per packet; overflow refuses the packet without silent truncation.
  These are evidence candidates, not one work unit per sentence or message.
- For each span choose no work, goal, reported progress, reported result, both
  progress/result, remaining work, goal plus remaining work, or ambiguous/multiple
  work requiring refusal. Requests/plans cannot become performed work. Background,
  acknowledgements and quoted instructions are not automatically work.
- Assign every selected work span to an existing unit or a new unit; uncertainty
  refuses instead of inventing membership. Keep at most eight units. The first
  selected goal anchors its unit; activity without a stated goal keeps goal null.
  Explicit model-selected field kinds populate the same quoted output contract.
  Choose target evidence separately from that unit's assigned spans, or null.
  A span containing inseparable independent outcomes may be refused; this bounded
  candidate is not a claim to solve arbitrary semantic segmentation.
- For pairs, choose the relationship, then explicitly select left/right evidence
  and any required right-side continuation link. Missing evidence fails; the
  program never chooses a citation on the model's behalf. Uncertain can abstain.
- Choices include an abstention/refusal option and use a token-prefix trie over
  bounded answer codes, followed by EOS, through the installed runtime's existing
  constrained-decoding callback. No free-text reasoning or JSON is generated.
  Code serializes the selected original evidence; this is not repair of a failed
  free-form answer. Constrained syntax does not prove semantic correctness.
- Choice code length is at most eight tokens, at most 128 options; generation is
  greedy and non-thinking with at most nine output tokens and the existing
  180-second per-call bound. Packet input still obeys the 8,192-token limit.
  Bound a case to 144 choices and check a 180-second elapsed budget between and
  after calls. One in-flight generation may exceed the case deadline before it
  can be refused; no hard OS-level cancellation guarantee is claimed.
- Version prompts, splitting, field projection, decoder and bounds in strategy
  identity. Keep stage metrics and content-free span/label/unit decision traces.
  Reuse only complete, validated case results; an interrupted case recomputes.

Freeze this candidate before real inference. Execute the original four development
cases once, with the original expectations unchanged. Report execution/grounding
validity and semantic checks separately; review every populated field and goal
association, not just keyword scores. Only a full development and semantic pass
selects this frozen configuration for the ten untouched holdout cases once.
No holdout tuning or seed search. A pass is a synthetic prerequisite only: large
work-area grouping, real-corpus continuity, all-history production and map UI
remain separate work, with no routine per-Session classification task for the owner.

After v1's development-only omissions, one bounded v2 clarification distinguishes
recorded work requests from instructions the analyzer must execute. A same-prompt
unconstrained diagnostic returned the same incorrect none choice. This supports
investigating prompt semantics, not claiming the constraint caused the error.
Preserve v1, keep expectations, model and decoder unchanged, and run v2 development
once in separate state. The original holdout remains unexecuted and untuned.

The two per-span classifier attempts failed. A same-prompt CPU/float32 diagnostic
of the first goal also selected none; do not attribute that omission solely to GPU
math. The third and final bounded development attempt adds `selected`: inventory
independent source-backed goal/activity anchors across the entire conversation,
then select evidence separately for each field of each anchor, with the same
finite-choice decoder and bounds. Unknown fields remain absent; each unit must
retain its selected anchor. Each field selection can stop with none; missing pair
evidence or continuation links fail. Quotes are never selected by the program on
the model's behalf. Keep original packets and other anchors visible to prevent
goal contamination. At most eight units/items; a ninth selection refuses rather
than silently omitting content. Preserve classified v2 and all prior results.
Freeze selected v1 before one development pass and require the same development,
field review and untouched holdout gates. No further blind prompt iterations.

## Continuity Notes

2026-09-23: RUN-104 failed its non-thinking trial. The owner approved RUN-105's
reasoning/staged comparison, retaining expectations and grounding. Attempt 1
encountered a fused-path numerical error; attempt 2 completed on MPS eager
attention without that error, but neither frozen candidate passed quality.
The runtime correction is not a quality pass or permission to run private data.

2026-09-23: RUN-106 installed and verified the separately approved 8B model and
completed both unchanged development comparisons. Thinking passed 1/4 cases and
staging 2/4. Time-limited output, wrong field shape and incomplete grounding were
rejected; staging also misclassified acknowledgement as work. Neither qualified
for holdout, and no private inference ran. Installation success is not admission.

2026-09-23: RUN-107 completed three bounded source-choice attempts. The first two
produced 4/4 valid outputs but only 3/4 and 2/4 content passes. Goal-first selection
passed 3/4; its mixed case fragmented anchors and misassigned fields before failing
anchor preservation. A single CPU reference also omitted a stated goal. Format
constraints alone do not establish semantic quality. Holdout/private work did not
run, and both prior strategies and current failed comparisons remain available.
