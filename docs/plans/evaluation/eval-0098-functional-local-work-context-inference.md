# EVAL-0098: Local Work Context Inference — Functional

## Metadata

- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`
- Run: [RUN-20260923-110](../run/run-20260923-110-work-role-formulation-comparison.md)
- Attempt: `1`
- Feature: [FEAT-0098](../feature/feat-0098-local-work-context-inference.md)
- Spec: [SPEC-0098](../spec/spec-0098-local-work-context-inference.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `infra`, `data`
- Evaluator: `functional`
- Date: `2026-09-23`

## Role Formulation Comparison — RUN-110

Current PASS covers the approved diagnostic's execution, scoring, preservation
and replay. It is not a semantic model-quality PASS; Feature admission remains
blocked. All 166 frozen observations complete once (198 actual choice calls),
with unchanged weights, prompts, source packets, expectations and prior fixtures.

| Matched role measure | Independent questions | Direct role set |
| --- | --- | --- |
| Exact role sets, canonical order | 2/16 | 6/16 |
| Exact role sets, reversed order | 6/16 | 9/16 |
| Correct in both orders | 2/16 cases | 6/16 cases |
| Extra role assignments | 42 | 16 |
| Missing role assignments | 0 | 9 |
| Recognized set changes across order | 11 cases | 6 cases |

The direct example-only case additionally changes from uncertainty to none,
separate from its six recognized-set changes. Paired conditions are 6 both-correct,
9 direct-only, 2 properties-only and 15 neither. All-none scores 6/32; all-role
and all-uncertain baselines score 0/32. Missing/invalid/uncertain output never
becomes an empty-set success. These counts cover sixteen synthetic contexts,
not 32 independent samples. No statistical significance or real-work accuracy
claim is made. Question structure, vocabulary size and number of calls differ;
the experiment does not isolate one causal wording/token/constraint effect.

### Primary Semantic Review

All 64 assembled role-set results, their underlying 160 choices, and all six
relationship controls were reviewed. Exact source focus and speaker attribution
are preserved; no expected answer enters prompts and no result is repaired.

- Direct selection improves the single requested goal, reported success and
  performed-check cases, but both compound action/result and action/pending
  statements lose the action. A planned test can become performed action/goal;
  a failed outcome becomes remaining work. The simpler answer is not universally
  better: two matched conditions are correct only under independent questions.
- Both methods fail the same-work later-completion contrast: the old unperformed
  statement remains pending despite explicit subsequent success, or inherits
  later performed/result claims. The different-work completion contrast shows why
  merely deleting all earlier pending text on any later success would be wrong.
- Three of nine stable recognized direct cases are wrong, as are three of five
  stable property cases. Thus agreement under reversal is not a truth criterion.
  No order voting, intersection, favorable-order selection or new abstention rule
  is silently substituted for the frozen outputs.
- Relationship controls pass 5/6 final labels. Topic-only reading/listening still
  becomes continuation with a source-valid but semantically unsupported right
  link, approved by the same-model audit. The contextless case abstains only after
  missing left evidence; its preceding distinct-goals decision is wrong. The
  grounded short case also misidentifies a pronoun-only focus as a concrete goal.
  These intermediate errors remain visible even when the final label passes.

### Runtime, Coverage And Route

The run uses 113,301 input tokens, 470 output tokens and 179.1 cumulative seconds
including model load and audit/checkpoint work, excluding initial verification/
preflight. All 198 prompt-token counts match generation (361–1,342); the longest
generation is 2.08 seconds. Sampled MPS driver allocation peaks around 23.0 GB,
not total system/process RAM. No malformed label, refusal, timeout or OOM occurs.

Actual replay reuses 166/166 observations with zero new generation and identical
observation/summary hashes, cumulative calls/time and one-attempt counters. Assets
verify unchanged. All 165 relevant tests pass in the installed model runtime;
the full application suite runs 850 tests with zero failures and one optional skip.
Privacy scanning (979 files), generated catalog, 912 local links and diff checks pass.
Storage/corruption/interruption/budget paths have injected regression evidence,
not claims that real crashes or maximum-context tests were performed here.

This establishes a narrow over-assignment/omission tradeoff, not a qualified
extractor. Stop repeating prompt/choice variants. Recommend a bounded contract
review separating event-time source assertions from current-state reconciliation,
with compound-claim coverage and supported target identity. That is a hypothesis,
not an implemented fix, permission to relabel old tests or approval to change the
existing field semantics. Original holdout/private corpus, embeddings, UI and
legacy data remain untouched. No active model job or task scratch remains.

## Evidence-First Candidate — RUN-109

RUN-109's historical FAIL is semantic admission, not a failed installation or unfinished
calculation. All sixteen frozen cases completed on the installed 8B. The initial
adapter failure occurred before any generation; its corrected 32-character
semantic-label opt-in changed no prompt, source, label order or expected answer.

| Cohort | Grounded output | Content passes | Negative passes | Positive passes | Gate |
| --- | --- | --- | --- | --- | --- |
| Original development | 3/4 | 3/4 | 2/2 | 1/2 | FAIL |
| New composition | 10/12 | 4/12 | 2/8 | 2/4 | FAIL |

### Primary Semantic Review

Every output and decision trace was reviewed. The compositional scorer checks
field coverage **and** purity: adding unrelated or wrong-role evidence cannot
pass merely because a required keyword is also present. Original cases and
expectations remain unchanged. No score or answer was repaired after observation.

- Both mixed-work cases refuse inconsistent/multiple goal membership. Their
  traces classify requests and unfinished tasks as performed actions/results;
  refusing an ambiguous merge is narrower than successfully reconstructing work.
- Same-outcome phases produce one unit, but requests, edits and unperformed
  verification spill across progress, results and remaining-work fields. Correct
  grouping/count alone is insufficient.
- The plan-only case puts a future test and an explicit statement that no work
  has been performed into progress. The completed-work case leaves the original
  request and reported success pending. A goal-less logged activity is incorrectly
  promoted to a concrete goal. All four published extraction cases pass their
  same-model audit despite these errors; exact speaker/source attribution survives.
- The instruction/example case refuses a contradicted proposed unit. No partial
  units publish, but this does not meet its required no-work empty output.
- Grounded short and six-month resumptions pass, as do shared-file independent
  goals and a reused identifier with conflicting scope. The correct relationships
  sometimes retain generic pending/pronoun spans as supposedly concrete goals,
  an additional intermediate error not captured by the final relation label.
- Contextless continuation becomes `related` instead of `uncertain`. Two activities
  sharing only a topic become `continues`, with an actual source quote wrongly
  selected as an explicit continuation link. Both pass the same-model relation
  audit. Thus no safeguard against all false merges is established.

Across both cohorts extraction passes 1/8 (only no-work abstention) and relations
6/8. New composition passes no extraction case (0/6) and four relations (4/6).
These small assistant-authored controls are not random real-work samples or a
statistical accuracy estimate. Different contexts and scoring do not identify a
causal regression from RUN-108's focused role questions. Widespread `supported`
answers suggest a calibration/decomposition issue to investigate, not a proven
token, hardware or model-capacity cause. Same-model auditing is not independent
validation, as this trial concretely demonstrates.

### Verification And Route

The run uses 205 calls, 446 output tokens and 171.4 cumulative case seconds,
including load. Peak sampled MPS driver allocation is about 18.7 GB, not total
RAM; no OOM, generation timeout or invalid label occurs. All fifteen semantic
labels round-trip with the installed tokenizer and use at most three tokens.
Actual same-config replay retains all 16 completed observations with zero new
generation, matching hashes and one attempt per case, including wrong/refused
results. The failed gate is unchanged. Model assets re-verify unchanged.

142 work-context tests pass in the model runtime; full application regression
passes 827 tests with one optional graph skip. These establish mechanics, not
model usefulness. Privacy scanning (974 files), catalog, 903 local links and
diff-whitespace checks pass. Holdout is not run because both development cohorts fail.
There is no private-source producer, model install/training, embedding rebuild,
organization mutation or UI change. Evaluation evidence retains its finite owner
and expiry; no task scratch or model job remains.

Return FEAT-0098 to a bounded approach decision. Recommend a matched, fresh-case
comparison of direct semantic-role decisions versus independent property checks,
with separate unsupported-continuity controls. That is an untested hypothesis,
not a promise of improvement. The owner subsequently approved and completed
that diagnostic under RUN-110 above. Do not stack more same-model
audits, weaken gates, substitute another model, or add routine user classification.
The whole-history flow-map goal remains outstanding.

## Protocol Diagnostic — RUN-108

RUN-108's historical PASS means the frozen diagnostic, preservation, scoring and replay work
correctly. It is **not** a model-quality PASS. FEAT-0098's extraction admission
remains blocked by the previous trials. This matrix contains twelve new synthetic
base cases, not real workflows or 288 independent accuracy samples.

All 288 conditions completed once on the unchanged installed 8B/MPS/eager runtime.
No generation refusal, unrecognized decision, missing cell, prompt/expectation
revision or scoring repair occurred. Correctness below is the frozen semantic
decision only; format and citation requirements are separate.

| Response form | Correct semantic decisions | Strict protocol valid | Literal citation grounding |
| --- | --- | --- | --- |
| Numeric choice | 142/192 | 192/192 | Not requested |
| Semantic-label choice | 40/48 | 48/48 | Not requested |
| Short decision/explanation/evidence | 37/48 | 8/48 | 11/48 |

| Case family | Numeric | Semantic label | Short text |
| --- | --- | --- | --- |
| Six focused field decisions | 90/96 | 23/24 | 22/24 |
| Two goal-membership decisions | 23/32 | 7/8 | 6/8 |
| Four temporal/work relationships | 29/64 | 10/16 | 9/16 |

### Interpretation And Primary Semantic Review

The primary agent reviewed all 48 short-text observations (46 distinct
case/answer texts), plus every label result and numeric decision grid.

- Numeric answers change under fixed-order code changes **and** fixed-code
  order changes in seven of twelve base cases: reported activity, gratitude,
  both membership cases, shared-file separation, topic-only relatedness and
  contextless continuation. These are observed sensitivity, not proof of one
  universal first-option cause. Numeric code counts are 65/40/47/40 and displayed
  position counts 59/49/47/37; the model is not simply always selecting zero/first.
- Explicit goal, mixed-context request, reported test result, pending work and
  explicitly identified six-month resumption are correct under all 24 conditions
  each. This narrow success does not establish multi-goal extraction or explain
  every RUN-107 omission: prompts, focused questions and contexts differ.
- Semantic labels improve the aggregate count but remain order-sensitive in
  reported activity, existing-goal membership and topic-only relation. An action
  becomes intent in one order; membership follows the wrong goal in one order.
  Ordinal `first`/`second` goal labels can also be confounded with presentation
  order; that interpretation is a hypothesis, not an isolated causal finding.
- Contextless continuation is wrong under all four label and all four text
  conditions; numeric answers are correct only once in sixteen. The model treats
  a vague conversation-level "continue that" as sufficient work-goal continuity,
  even though no goal/scope can be recovered. All four text answers omit the
  left-side citation. This is a semantic/grounding defect, not merely an output
  serialization problem.
- Topic-only similarity produces two false continuations and one uncertain
  answer among four text conditions. Label choices avoid false continuation in
  this case but abstain twice instead of identifying topical relatedness.
- Two text outputs contradict their own brief reason: gratitude is labeled
  intent while its reason says there is no work; one membership answer selects
  the second goal while its reason describes the first and excludes the second.
  Another gratitude answer invents a request/plan. These disagreements remain
  failures, not manually repaired decisions.
- The strict format/citation counts must not be described as 40 semantic errors
  or 37 fabricated quotations. Forty texts have nonconforming declaration-line
  spacing; 28 add outer quotation marks and 13 have trailing citation spaces
  (overlapping counts). Seven omit a required source side/goal. A post-hoc,
  read-only literal check found no quoted content mismatch after removing only
  those presentation decorations, but **did not change any frozen score** and
  cannot supply missing evidence or make the relationship claim true.

The cyclic controls balance option position/code for each meaning, not every
possible permutation. Text also requests explanation/evidence, and two semantic
labels tokenize to two tokens rather than one. Therefore this is a protocol
sensitivity diagnosis, not a pure constraint-mask ablation or proof of a general
model ranking. No binomial confidence interval or significance claim treats the
correlated conditions as independent. Higher aggregate label counts cannot hide
the failed abstention/false-continuation controls.

### Runtime, Regression And Route

The frozen run used 288 calls, 3,523 generated tokens and 364.5 cumulative seconds,
including model loading but excluding asset verification. Sampled MPS driver
allocation peaked near 22.6 GB, not total process/system RAM. The longest
generation was 8.33 seconds; no OOM, truncation or timeout was observed.
Recorded input tokens match actual generation in all 288 cells (342–586 tokens).
Actual same-config replay reuses every observation with zero further generation,
unchanged observation/summary digests and unchanged call/time accounting. Asset
verification passes again. Interrupted/budget/corruption paths are synthetic test
evidence. Tests pass: 108 in both runtimes, 793 full regression with one optional
skip, privacy scanner on 970 candidate files, catalog/links/diff checks.

The then-recommended route was one evidence-first extraction/relationship redesign
using existing weights, with recoverable goal/scope plus compatible context
required before work continuation. Separate source identity/citation assembly
from semantic decisions; include explicit label/reason disagreement checks and
abstain without routine user confirmation when support is missing. Preserve all
original extraction gates, freeze new compositional development controls rather
than repeatedly tuning these twelve cases, and run untouched holdout only after
its prerequisites pass. RUN-109 subsequently implemented that recommendation;
its failed admission above supersedes this historical next-step proposal.
Private corpus, embeddings, UI, production organization and training are unchanged.

## Initial Trial — RUN-104

All examples below are synthetic fixtures, not the user's corpus. Expected
labels were fixed before generation; no expectation or validator was relaxed.

| Development configuration | Valid outputs | Passing cases | Blocking observation |
| --- | --- | --- | --- |
| Prompt v1, non-thinking greedy | 2/4 | 2/4 | Scalar goal/target/link rather than evidence objects; second independent goal omitted |
| Prompt v2, non-thinking greedy | 3/4 | 2/4 | Second independent goal still omitted; independent pair cites right side only |
| Prompt v2, official non-thinking sampling settings, one fixed per-packet seed | 3/4 | 2/4 | Same omission and one-sided evidence; no improvement in admission score |

The final configuration passed explicit distant continuation and no-work
abstention. It recovered only the first of two independent goals in the mixed
conversation. For the independent pair, the label itself was correct but its
one-sided evidence violated the required grounding contract. Do not describe
that grounding failure as a demonstrated false merge.

The final quality gate fails both its all-negative-control requirement (1/2)
and positive-case requirement (1/2, below 80%). Holdout cases were not consumed
for tuning or presented as passed; private whole-history generation did not run.
This is evidence against this model/prompt/decoding combination, not proof that
all 4B models, another extraction strategy or reasoning mode must fail.

## Initial Runtime Evidence

- Official model installation and local MPS inference succeeded without training
  or source transmission. Both greedy and explicitly versioned sampled decoding
  ran. Existing vectors and source data were not modified.
- In the final run, the short synthetic cases took about 0.6–9.4 seconds each,
  with the first case including model load. Sampled MPS driver allocation reached
  about 9.6 GB. This is not total process/system RAM or a full-history performance
  prediction. No out-of-memory failure was observed.
- 28 new tests and the 713-test full regression pass (one optional graph skip;
  all 20 simulation tests pass separately in the model runtime). These prove
  infrastructure behavior, not model quality.

## Finding And Route

Blocking: the current inference recipe is not admitted for private full-history
application. Classification: `planning gap` in the model/extraction approach,
not a hidden source-admission or memory failure. Do not add a routine approval
queue, silently drop the second goal, relax grounding, or install another model.
The owner approved RUN-105's same-model comparison and then RUN-106's 8B comparison
below. Both fail admission. Any further approach change requires its own bounded
decision before corpus use; these failures authorize no additional model download.

## Same-Model Comparison — RUN-105

The original v2 prompts, stage prompts, seed rules, expectations and final
evidence validators were frozen before this comparison. Both corrected-runtime
candidates ran all four development cases, with no holdout-based tuning.

| Configuration | Valid outputs | Automated passes | Gate |
| --- | --- | --- | --- |
| Thinking, fused MPS attention | Unavailable | Unscored | Runtime failed before the first final answer |
| Staged non-thinking, fused MPS attention | 4/4 | 3/4 | FAIL: acknowledgement misclassified as work |
| Thinking, eager MPS attention | 3/4 | 3/4 | FAIL: independent pair has one-sided evidence and a non-null continuation link |
| Staged non-thinking, eager MPS attention | 4/4 | 2/4 | FAIL: remaining work omitted; acknowledgement misclassified as work |

The attention correction followed a repeated invalid-probability exception in
the original thinking runtime. No invalid logits were sanitized and no weights,
dependencies, source packets, prompts or expected labels changed. Eager attention
completed both candidates; the exact low-level cause is not established by a
small standalone tensor probe, which did not reproduce the exception. This
distinguishes an execution failure from a semantic model failure.

Primary semantic review of the final answers found additional errors beyond
the fixed automated score: staging attached payment-work progress to the search-UI
goal; thinking placed a request to design a search box in reported progress.
These are synthetic examples. Exact quote validity does not make either field
semantically correct. No failed field was manually repaired into a success.

With eager attention, thinking took 109.8 seconds and 2,034 generated tokens over
four cases; staging took 37.9 seconds and 632 tokens across nine stage calls.
These totals include each process's initial model load. Observed MPS driver
allocation peaks were approximately 9.4 GB and 17.4 GB respectively, not total
system/process RAM. Reasoning tokens were counted but never decoded or retained.
No out-of-memory exception occurred and no corpus-throughput claim is made.

Neither candidate passes all negative controls, so none was selected for the ten
untouched holdout cases. The full private corpus, map UI and existing embeddings
remain unchanged. This proves a bounded failure, not that size alone explains it.

## Verification And Coverage

- RUN-105's 47 work-context tests passed in both the application and optional model
  runtimes; its full suite passed 732 tests. RUN-106's 57 work-context tests pass in
  the optional model runtime, and the full application suite passes 742 tests
  with one optional graph skip.
- Installed weights verify unchanged after inference. Actual identical-config
  staged replay reuses all four validated results without regeneration and
  preserves the failed gate; a completed/valid cache is not a semantic pass.
- Source/prompt/strategy invalidation, interrupted stages, exclusive ownership,
  protocol parsing and split-isolated gates have synthetic test coverage.
- Holdout, private corpus integration, large-window throughput and UI evidence
  are unobserved. The failed development gate blocks broader admission; narrower
  infrastructure PASS does not override it.

## Model-Size Comparison — RUN-106

The pinned 8B installation completed and its 13 admitted assets were verified.
It occupies approximately 16.4 GB allocated disk; retaining both baselines uses
about 24.5 GB. No training, dependency change or private input was involved.
Both candidates used RUN-105's corrected MPS eager runtime and unchanged prompts,
stage logic, sampling, per-packet seed rule, token/time budgets and expectations.

| 8B configuration | Valid outputs | Automated passes | Blocking observation |
| --- | --- | --- | --- |
| Single-pass thinking | 1/4 | 1/4 | Mixed goal request timed out; both relation answers cited only the right packet |
| Staged non-thinking | 2/4 | 2/4 | Extraction returned a list instead of one evidence object for `goal`; acknowledgement was also treated as work |

For thinking, the mixed case generated 1,981 tokens without EOS before the
180-second limit (183.5 seconds including load); its final answer is unavailable,
not demonstrated semantically wrong. The two relation labels were correct but
their grounding was incomplete. The no-work case correctly returned no units.
For staging, both relation answers passed with bilateral evidence and appropriate
links. The mixed case stopped at the first invalid detail, so its second goal's
extraction/association is unscored, not an observed omission. The acknowledgement
was explicitly proposed as a work goal, a semantic error beyond its shape failure.
These findings come from final synthetic outputs, not retained reasoning traces.

Thinking took 270.1 seconds and 3,293 output tokens over four cases; staging took
40.5 seconds and 540 tokens across eight stage calls. Times include each process's
initial model load; invalid stages stop early, so faster totals do not prove more
efficient complete extraction. Peak MPS driver allocations were about 17.6 GB and
24.5 GB, not total process/system memory. No out-of-memory or invalid-probability
exception was observed. Post-inference asset verification passed unchanged.

Neither candidate meets the fixed development gate or qualifies for the ten
untouched holdout cases. No configuration was selected and no private corpus ran.
The four-case comparison does not establish a general model ranking or prove that
another larger model is needed. It does show that size alone did not resolve this
recipe's protocol, grounding and abstention failures. Recommended next review:
bounded extraction/protocol redesign, without relaxing semantic acceptance,
automatic further downloads or routine user classification of Sessions.

## Source-Selected Extraction — RUN-107

The owner approved improving extraction after clarifying that earlier scores
were assistant-authored synthetic checks, not real-workflow accuracy. The original
four development expectations and ten unexecuted holdout cases are unchanged.
The installed 8B was used without training, download, dependency or vector changes.

| Candidate | Valid final outputs | Content-case passes | Observed limitation |
| --- | --- | --- | --- |
| Per-span classified v1 | 4/4 | 3/4 | Goals and remaining work discarded as non-work; only an activity remained |
| Per-span classified v2 | 4/4 | 2/4 | Goals/progress discarded; independent relationship changed to uncertain |
| Goal-first selected v1 | 3/4 | 3/4 | Six anchors for two goals; wrong field selections; last unit omitted its anchor |

Source-choice constraints remove free-form JSON/quote writing, but cannot make
the chosen categories/memberships true. In all three trials the acknowledgement
produced no work, a narrow observed improvement over earlier staged trials. V1 and
goal-first selection also grounded both pair judgments correctly. These successes
are not enough for admission, because mixed extraction still fails.

A single unconstrained v1 diagnostic returned the same incorrect none code for
the first stated goal. A v2 CPU/float32 reference likewise returned none, matching
MPS/bfloat16 on that case. Neither diagnostic establishes a general causal
explanation or device equivalence; they do not justify attributing the omission
solely to constrained decoding or the earlier GPU numerical issue.

Primary review of the final goal-first decision trace found all six source spans
selected as independent work anchors, then requests and goal statements selected
as reported progress/results. Its final `MISSING_ANCHOR` refusal therefore must
not be presented as a harmless shape error or a near-complete extraction. Invalid
partial units were not published, repaired or counted as semantic successes.

The candidates took 15.2, 14.2 and 93.9 seconds, with 15/13/81 calls and 30/26/162
generated code/EOS tokens respectively. Load is included; these are not complete
extraction throughput estimates, especially when a case fails. MPS driver peaks
were about 17.8/17.7/17.8 GB, not total process/system RAM. No OOM or timeout was
observed in these three candidates. 8B assets rehash unchanged after inference.

None qualifies for holdout or private processing. Classification: `planning gap`
in the admitted extraction approach, not a hidden corpus or memory failure.
Stop after the bounded attempts; a next approach requires a separately scoped
follow-up decision. Do not silently adopt a candidate, weaken the unchanged
expectations or keep searching prompts against the same four cases. Full-history
grouping and the intended map UI remain outstanding, with embeddings preserved.

Verification: 87 work-context tests pass in both runtimes; all 772 regression
tests execute with zero failures and one optional skip. Actual classified v2
replay reuses four validated results with no generation and keeps the failed gate.
These are infrastructure checks, not an independent semantic-quality evaluation.

## Continuity Notes

2026-09-23: preserved the initial RUN-104 evidence while updating the current
evaluation to RUN-105. Its runtime correction succeeds in completing the trial,
but both frozen candidates fail quality. Recommended route remains planning
review of the model/approach, not blind retries or relaxed acceptance.

2026-09-23: RUN-106's approved 8B comparison completed but
also fails admission; the prior 4B results remain historical evidence. Private
whole-history processing and UI integration stay blocked, with no active job.

2026-09-23: current evaluation is RUN-107. Source-selection mechanics improve
structural control, but all bounded candidates still fail semantic admission.
Holdout and private inputs remain untouched; no generation or download is running.

2026-09-23: current evaluation advances to RUN-108's narrower protocol-diagnostic
scope. That functional scope passes, while previous model-admission FAILs remain
valid. The diagnosis establishes mixed protocol sensitivity and semantic errors,
not an accepted extractor. No holdout/private job or UI change followed.
