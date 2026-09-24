# FEAT-0098: Local Work Context Inference

## Metadata

- ID: `feat-0098`
- Status: `blocked`
- Type: `foundation`
- Surface: `mixed` (`infra`, `data`)
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-23`
- Updated: `2026-09-23`
- User review status: owner approved the proposed Qwen3-4B installation and
  grounded context/continuity trial, with synthetic evaluation before all-data
  application. No additional per-membership approval is introduced.
  After the initial failed trial, the owner approved continuing with the same
  installed model's reasoning mode and staged extraction on 2026-09-23.
  The owner then approved installing Qwen3-8B and comparing it against the same
  frozen checks, with disk usage disclosed before installation.
  After reviewing what the tests measure, the owner approved improving extraction
  on the installed models while preserving embeddings and the whole-history/map
  destination. RUN-107 owns this bounded inference-only continuation.
  Following the literature review, the owner approved continuing with its
  fixed-model protocol diagnostic. RUN-108 diagnoses answer-format/order/code
  sensitivity on synthetic evidence only; it cannot grant model admission.
  The owner then approved the evidence-first extraction/relationship follow-up
  in RUN-109: one frozen candidate on the installed 8B, with new compositional
  development controls and unchanged original admission requirements.
  After that candidate failed, the owner approved RUN-110's matched direct-role
  versus independent-property comparison, with separate unchanged relationship
  controls. This diagnostic approval does not admit a new extraction producer.
  The owner subsequently approved reviewing source assertions versus current
  work state. That planning review is complete; its separate FEAT-0099 foundation
  was subsequently approved and passed under RUN-111. It does not approve another
  model trial or this Feature's private application.

## Goal

Establish whether the approved local generative model can extract source-backed
work units and distinguish explicit continuation from topical similarity.
Fix the model-admission, structured-output and abstention contracts before a
private all-history producer or product consumer depends on these inferences.

## Acceptance Contract

1. Install only pinned public Qwen3-4B or the separately approved Qwen3-8B assets into an explicitly selected,
   owned model directory outside Git. Do not open private sources or send
   credentials during installation. Verify asset inventories and weights.
2. Load only verified local safetensors with remote code and network disabled.
   Run inference, never training. Record model/runtime/prompt identities and
   actual duration/token/resource evidence. Keep existing Foundry assets intact.
3. Extract separate work units from ordered conversational evidence with goal,
   target, progress, result and remaining-work fields. Every nonempty field
   carries an exact source quote/locator and original speaker; absent fields
   remain absent. Supplied source instructions have no tool or policy authority.
4. Classify only the supplied relationship pair, separating continuation,
   topic-related, independent and uncertain. Continuation requires explicit
   cited linkage and compatible context, not shared terms or elapsed time.
   No model output becomes owner confirmation or a source fact.
5. Fail closed on invalid JSON, fabricated quotes/IDs, excessive input/output,
   unsupported claims or truncated generation. Fixed diagnostics must not leak
   private prompts or model output. No silent input truncation or repair that
   changes semantic output into a passing result.
6. Freeze synthetic positive and negative cases before real generation. Report
   quality separately from infrastructure correctness. All negative controls
   and at least 80% of positive checks must pass before private application;
   any failed safety control blocks whole-corpus execution. Model choice remains
   experimental even after a synthetic pass.

## Scope Boundary

In: explicit model installer/verifier, offline local generator, quoted work-unit
and pair-relation contracts, synthetic quality harness, tests and measured trial.

Out: training, models beyond these two pinned candidates, hosted inference, edits to Foundry, private
corpus execution before the gate, automatic source ingestion, production flow
identity, map/UI replacement, existing Workstream writes and legacy deletion.
The downstream corpus producer must preserve full coverage, cache/version and
resume semantics; this evaluation does not replace that implementation.

## Surface Lanes

- Infra: `scripts/`, `src/localbrain/work_context_model.py`; public installation
  and verified offline inference first, owned by the primary agent.
- Data: `src/localbrain/work_context.py`, synthetic fixtures and tests; bounded
  evidence/output contracts consume the runtime. Contract and Functional check
  both lanes. No delegation is required.

## Dependencies And Regression Surfaces

Existing optional PyTorch/Transformers runtime; source-neutral utilities only.
FEAT-0097's private report is not consumed and its remaining live replay checks
are not a dependency of this independent model-admission test. Original source
DB, cached vectors, old previews and organization behavior remain unchanged.

## Harness Trace

- Spec: [SPEC-0098](../spec/spec-0098-local-work-context-inference.md)
- Current Run: [RUN-20260923-110](../run/run-20260923-110-work-role-formulation-comparison.md)
- Evidence-first trial: [RUN-20260923-109](../run/run-20260923-109-evidence-first-work-context.md)
- Protocol diagnostic: [RUN-20260923-108](../run/run-20260923-108-work-context-protocol-diagnostic.md)
- Source-selected comparison: [RUN-20260923-107](../run/run-20260923-107-source-selected-work-extraction.md)
- Model-size comparison: [RUN-20260923-106](../run/run-20260923-106-work-context-model-size-comparison.md)
- Same-model comparison: [RUN-20260923-105](../run/run-20260923-105-work-context-strategy-comparison.md)
- Initial trial: [RUN-20260923-104](../run/run-20260923-104-local-work-context-inference.md)
- Checks: asset tampering, unsafe ownership, network isolation, inference-only
  loading, bounded output, exact evidence, role attribution, unknowns, mixed
  sessions, topic-only false continuity, long-gap continuity, contradictions,
  untrusted source instructions, interrupted evaluation and deterministic cases.

## Trial Outcome

Current outcome: RUN-110's matched comparison and replay are complete. Direct
role sets are correct in 15/32 order conditions versus 8/32 for independent
questions, but only 6/16 contexts are correct in both orders, compound actions
are omitted, and fulfilled work stays pending. Unchanged relationship controls
pass 5/6 with a topic-only false continuation. Diagnostic PASS does not establish
model admission. The subsequent structure review is complete and proposes
[FEAT-0099](feat-0099-source-claims-and-work-state-projection.md), a separate
model-free source-claim/state-projection foundation. That separately approved
implementation now passes RUN-111, using supplied synthetic claims/bindings only.
This Feature remains blocked, with no automatic prompt/model trial or private run.
The owner then requested its adapter review, which produced the separate
[FEAT-0100](feat-0100-source-claim-extraction-and-binding-trial.md) with one
model-aware extraction/binding candidate with separate upstream and end-to-end
gates, preserving this Feature's original development/composition/holdout checks.
The owner subsequently approved its implementation/trial under RUN-112, now
completed with contract/replay PASS but semantic Functional FAIL: all 28
extractions are protocol-rejected, conditioned binding fully passes only 3/28,
and all end-to-end calls are prerequisite-skipped. That separate Feature and
this admission remain blocked. Holdout/private/UI are untouched; no automatic
new candidate follows. RUN-112 owns detailed evidence and its review handoff.

RUN-109's evidence-first implementation and replay pass their
contract, but model admission fails. Original development passes 3/4; twelve new
compositional cases pass 4/12 (0/6 extraction, 4/6 relationships). Requests/plans
still become performed work, completed work stays pending, and topic similarity
can become false continuation even after same-model auditing. Both cohort gates
fail; holdout and private corpus remain untouched. The bounded trial is complete,
with no active generation or task scratch. Its detailed
[Functional evaluation](../evaluation/eval-0098-functional-local-work-context-inference.md#evidence-first-candidate--run-109)
owns the RUN-109 decision; subsequent outcomes are recorded above, and the
earlier trials below remain historical evidence.

Pinned installation, offline generation and contract/replay tests pass. The
initial non-thinking trial passed 2/4 development cases. The approved same-model
comparison is now complete: after bypassing a fused MPS numerical failure,
single-pass thinking passes 3/4 automated cases and staged non-thinking passes
2/4. Both find two goals, but thinking still lacks valid paired evidence and
misplaces a request as progress; staging loses remaining work, mixes activities
across goals and invents work from an acknowledgement. Neither passes admission.

Holdout and private corpus execution did not run. Contract PASS and regression
tests do not override this blocked admission. That same-model comparison changed
no weights, expectations, seeds or final evidence requirements. It demonstrates
that extraction strategy matters but does not establish that model size alone
causes the remaining errors. A separately bounded model/approach comparison is
the next planning decision, not automatic training or full-history execution.
That approved Qwen3-8B comparison is now complete under RUN-106. The additional
model occupies about 16.4 GB (both installations: 24.5 GB). Thinking passes 1/4
development cases: one time-limit refusal, two one-sided evidence refusals and
one correct abstention. Staging passes 2/4: both relation judgments are grounded,
but extraction violates the goal-field shape and invents work from acknowledgement.
No candidate qualifies for holdout or private execution. These fixed-condition
results do not establish a general model-size ranking or justify more downloads.
The recommended next decision is a bounded extraction/protocol redesign, keeping
the existing safety criteria and no routine per-Session confirmation burden.

That approved redesign completed under RUN-107: constrained source choices avoid
free-form shape errors, but classified v1/v2 pass only 3/4 and 2/4 content cases;
goal-first selection passes 3/4 and rejects mixed extraction after over-fragmented
anchors and invalid field associations. CPU reference agrees with one omission,
so that case is not explained solely by GPU execution. No candidate qualifies for
holdout or private application. Original embeddings and UI remain unchanged;
another bounded approach decision is needed, not automatic larger-model testing.

- [Contract evaluation](../evaluation/eval-0098-contract-local-work-context-inference.md)
- [Functional evaluation](../evaluation/eval-0098-functional-local-work-context-inference.md)

## Research Follow-Up — 2026-09-23

The owner-requested
[method review](../research/workflow-reconstruction-method-review.md)
is complete. It proposes isolating semantic judgment from answer-code/order
sensitivity before another approach comparison. The one CPU and unconstrained
diagnostic do not establish that these protocol confounders are absent. This
does not erase the observed semantic failures or qualify a candidate.

The review also proposes evaluating work relationships, area clustering and
presentation separately. Those are planning recommendations, not a bypass of
this Feature's extraction/grounding requirements. At review completion no new
Run, holdout/private generation or model installation had been started.
The subsequent owner continuation approved RUN-108's diagnostic, not a new
extraction recipe or holdout/private execution. Model-quality admission remains
blocked after the diagnostic completes successfully. All 288 conditions ran and
replay reused them without further generation. Numeric order/code sensitivity
appears in seven of twelve base cases; semantic labels improve aggregate results
but still falsely infer continuity when no work goal can be recovered. The
[current Functional evaluation](../evaluation/eval-0098-functional-local-work-context-inference.md#protocol-diagnostic--run-108)
separates semantic, format and citation findings. Its diagnostic-only PASS does
not replace any earlier admission FAIL.

The diagnostic's next bounded recommendation was evidence-first extraction/relationship work
on the installed 8B: require recoverable goal/scope and compatible context for
continuation, keep citations source-selected and automatically abstain on missing
support. Preserve the unchanged extraction gate; freeze new compositional controls
before another trial rather than tune repeatedly against the diagnostic. No
private generation, new model, training, vector rebuild or UI change is approved
by this diagnosis. No active computation or task scratch remains.

The subsequent owner continuation approved RUN-109's bounded implementation and
synthetic evaluation, not private application. Its evidence-first candidate must
retain outcome-level grouping, original speaker attribution, automatic abstention
and no routine owner confirmation. Both original development and new composition
gates plus primary semantic review must pass before the existing holdout is run
once. No new model, training, private corpus, embedding or UI change is in scope.

That candidate is now rejected for admission. Literal citations and additional
same-model checks did not fix semantic role or relationship errors. The next
proposed decision is a matched comparison of direct semantic-role classification
and independent property judgments on new frozen contrasts, retaining separate
continuity controls and all existing admission gates. RUN-108 motivates that
hypothesis but does not prove it. No new candidate, download, training or private
execution is authorized by the completed failure; per-Session owner labeling is
not the fallback. Reopen on approval of a new bounded approach, not by replaying
completed failures until an answer changes.

The owner has now approved that bounded comparison under RUN-110. It freezes
sixteen new role contexts and six separate relationship controls, preserves
multi-role statements and source attribution, and compares canonical/reversed
orders without picking the favorable one. No private producer, holdout run or
product integration is authorized by diagnostic completion.

RUN-110 is now complete with no active generation or task scratch. Its
[current Functional evaluation](../evaluation/eval-0098-functional-local-work-context-inference.md#role-formulation-comparison--run-110)
records both the reduction in over-assignment and the new omissions; neither
answer format is qualified. Stop the current prompt/choice-variant sequence.
The next proposed planning review should separate what a source asserted at its
event time from the current state of the same supported effort, preserving
compound-claim coverage and unresolved identity. That hypothesis requires its
own contract review; it does not reinterpret failed tests as success or authorize
private inference, new training/models, UI work or routine Session labeling.

That owner-approved planning review is now complete. FEAT-0099 keeps historical
claims, target/occurrence identity, supported ordering and current reported state
separate from the user-confirmed correction ledger. Its proposed pure consumer
uses supplied synthetic claims/bindings; it cannot establish that a model can
extract or link them correctly. Existing fixtures, field semantics, admission
failures and holdout are unchanged. Any later extraction adapter requires a
separate bounded review; passing the new deterministic contract would not unblock
this Feature or authorize all-history generation. RUN-111 now passes the approved
pure implementation (50 tests, full 900-test regression with one optional skip).
It introduces no new extraction recipe, model result or product consumer.
