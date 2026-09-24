# FEAT-0100: Source Claim Extraction And Binding Trial

## Metadata

- ID: `feat-0100`
- Status: `blocked`
- Type: `foundation`
- Surface: `mixed` (`data`, `infra`)
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-23`
- Updated: `2026-09-23`
- User review status: after reviewing this boundary, the owner approved adapter
  implementation and the bounded synthetic trial on `2026-09-23`. RUN-112 owns
  the completed trial: contract PASS, semantic Functional FAIL. No further
  candidate, private processing or UI work is authorized by that approval.

## Goal And Parent Direction

Test whether separating source interpretation, work identity and state calculation
improves reconstruction on frozen synthetic histories. Connect a local model to
[FEAT-0099's pure projector](feat-0099-source-claims-and-work-state-projection.md)
without claiming that a correct projector repairs wrong upstream judgments.

The parent destination remains automatic, whole-history work areas and subordinate
outcome-oriented efforts, with temporal links and an inspectable flow map. This
Feature tests one necessary producer contract, not area clustering or the map.
Neither a sentence nor a Session becomes a work area; unresolved material does
not become a routine owner classification queue.

## Evidence And Design Decision

RUN-109 and RUN-110 expose omitted compound claims, fulfilled work left pending
and false continuity. RUN-111 passes state calculation given supplied claims and
bindings, not their discovery. This motivates a testable separation, not a proven
quality improvement or a new model-size claim.

At review entry, the `work_state.py` contract hardcoded the producer as
`synthetic-supplied.v1`. Feeding model output into v1 unchanged would misstate
provenance. The adapter therefore requires a model-aware contract extension as
part of this same bounded foundation. A report wrapper alone is insufficient.

## Acceptance Contract

### 1. Host-Owned Sources, Model-Owned Interpretations

The host admits a bounded, ordered synthetic source snapshot. Source namespace,
native message identity, revision, original speaker/role, source sequence and
assertion timestamps come from that input, never from model-generated metadata.
Source text is evidence, not instructions to the runtime; the model has no tools.

Stage A extracts atomic source claims: goal/step intentions, performed actions,
observed outcomes, explicit scoped status and retractions. Preserve the difference
between a desired outcome and a planned step. Compound text can support multiple
claims, and a claim may require contextual antecedents in other source spans.
Later results cannot be attributed to an earlier quote. Unknown goals remain
unknown without discarding supported activity.

The model selects exact source spans and semantic roles. The host resolves and
validates their locators against the original records. Ambiguous repeated quotes,
fabricated text/IDs, invalid offsets and missing antecedents are not repaired by
first-match or fuzzy matching. Source labels use cited wording rather than
inventing a descriptive goal to fill an empty field.

Coverage distinguishes claims, explicitly identified no-work text and unresolved
text. Unselected text defaults to unresolved, not no-work. A complete mechanical
partition does not establish semantic recall; omitted expected predicates are
separate evaluation failures. No silent input truncation is allowed.

### 2. Bind At The Obligation's Scope

Stage B receives the original source and Stage A's claims. It proposes a
snapshot-scoped roster of outcome-oriented efforts, subordinate steps and
occurrences, then supported/unresolved/contradicted bindings and relations.
The end-to-end path receives no reference target roster, expected number of
efforts, reference labels or correct links. One claim/Session does not imply one
target. A broad goal and its steps can belong together; unknown activity can
remain unassigned without a fabricated parent.

- Same-target identity is distinct from contribution and topical relationship.
  Shared files, IDs, embeddings or repository membership do not establish it.
- Cross-Session continuation requires compatible goal/scope and explicit cited
  linkage on both sides. A long time gap neither forbids nor proves continuation.
- Repeated checks and attempts retain occurrence distinctions. Uncertain scope
  withholds closure; subordinate completion never closes its parent implicitly.
- Reopening, correction, retraction and cancellation require their own cited
  evidence and preserve attribution. Source text from a user is not a product
  user-confirmed correction. The passed projector's order/conflict rules remain.
- The legacy pair vocabulary remains continuation, related, independent or
  uncertain. Absence of a continuation link alone cannot prove independence.
  Pair judgments must cite the corresponding source evidence; they are assessed
  separately from bindings and cannot silently override a contradictory binding.

### 3. Make Fulfillment An Explicit Inference

A report that tests passed is an outcome, not an assertion that the whole effort
is finished. Nevertheless, it may fulfill an earlier obligation to run those
same tests. Stage B may propose a separate **lifecycle judgment**, with the exact
obligation, occurrence, action/outcome and supporting source anchors:

- `opens-obligation`: an explicit requested/planned step supports pending status
  for that step; a broad desired goal alone does not create a pending task.
- `fulfills-obligation`: reported execution/result fulfills that specific step.
  A failed test can finish a test-execution obligation without achieving a
  passing-test requirement, requesting a retry or completing a parent effort.

These are model-inferred judgments, not literal source statements. The host
assembles their proposed state effects only after structural validation and
retains their derivation separately from the source claims. A model-inferred
effect cannot be relabeled as explicit completion. Source-level action/outcome
claims keep their original meaning and speaker. The semantic evaluation checks
the fulfillment judgment itself, not merely its resulting status.

This first adapter permits inferred opening/fulfillment only for cited, explicit
step obligations with supported same-target/occurrence binding. Effort-level
terminal state requires an explicit scoped source status. No all-children-done,
generic outcome-to-completed, role-priority or latest-wins rule is introduced.
Missing identity, premise or chronology leaves the judgment unresolved and the
last supported state qualified. Cancellation is not completion.

Effective dates require unambiguous source evidence. The host validates any
proposed explicit interval; relative or timezone-ambiguous wording remains
unknown rather than borrowing ingestion time. Assertion time and evidence cutoff
remain host-owned. The deterministic projector, not another model summarization
pass, computes the supported reported state and its history.

### 4. Version Provenance Without Rewriting The Passed Baseline

Introduce a separately versioned model-aware packet/projection contract. Existing
v1 synthetic packets, public calls, identities, tests and outputs remain unchanged.
Preserve the source-anchor identity scheme: changing the model or prompt cannot
change the identity of the same native source span.

Model-derived interpretation, binding and lifecycle-effect identities include
their actual producer lineage: verified model revision/assets, runtime and
generation configuration, stage prompt/protocol and adapter/contract version.
The host computes this lineage; the model cannot declare itself admitted or
synthetic-supplied. Projection identity includes its input dependencies and
projector version. Both direct interpretations and inferred lifecycle effects
remain unverified; the projection is reported state, never verified reality.

Keep v1 ordering, conflict, cutoff, correction, source-revision and invalidation
semantics. Extend provenance and effect validation only; no independent new state
algorithm, persistent identity service or workflow-assertion ledger is introduced.
Structural validity does not prove correct semantic interpretation or equality.

## Assessment Boundary

Freeze source cases, reference annotations, scoring/alignment rules, prompts,
schemas, model/configuration fingerprints and numerical limits before generation.
Reference annotations are synthetic test judgments, not real-work ground truth.

| Path | Supplied input and model work | What it establishes |
| --- | --- | --- |
| Deterministic control | Reference claims, targets, bindings and effects → projector; no model | Contract/projection regression only |
| Extraction | Raw source → Stage A | Claim coverage, meaning, scope, attribution and span correctness |
| Reference-conditioned binding | Raw source plus reference claims and target roster → Stage B | Binding/lifecycle quality given correct premises; explicitly not end-to-end discovery |
| End to end | Raw source → cached Stage A → Stage B discovers targets/bindings/effects → projector | Actual reconstruction, including target discovery and upstream omissions |

Do not inject reference claims/targets into the end-to-end path or rerun Stage A
to obtain a more favorable input. Report target discovery separately: a difference
between reference-conditioned and end-to-end results does not isolate claim
extraction alone, because the former also supplies the target roster.

Assess exact predicate coverage and role purity, false joins/splits, target and
occurrence scope, continuation evidence, lifecycle judgments, reported state,
unresolved/conflicting material and abstention. Align candidates to reference
evidence/scope through frozen rules, not generated display-name equality. A
correct final status with wrong or missing premises fails. Refusing everything
cannot pass: show answered coverage, omissions and an all-unresolved baseline.

The adapter also projects the original quoted work-unit fields and pair relations
for unchanged FEAT-0098 development/composition/holdout checks. Historical pending
claims stay in history but leave current `remaining` only after supported
fulfillment/cancellation. Goals, progress and results keep their existing role
meaning and original attribution. An unbound pending claim cannot disappear just
because it lacks a target. Unsupported activity remains visible without a goal.
No original fixture, expected answer, negative flag or scoring rule is weakened.
Primary semantic review supplements existing automated checks; keyword matches
and counts alone are not enough.

### Frozen Cohorts And Limits

Use one candidate on the already installed, verified Qwen3-8B revision from
[SPEC-0098](../spec/spec-0098-local-work-context-inference.md). Keep offline MPS,
bfloat16, eager attention, non-thinking greedy generation. No download, alternate
model, temperature search, fine-tuning or same-model approval/repair loop.
Use bounded JSON generation plus strict validation, not a claim that the existing
runtime guarantees grammar-constrained JSON. Invalid/truncated output stays failed.

- Development: the unchanged original four cases and RUN-109's twelve composition
  cases, plus twelve separately frozen source-claim histories. These are 28 case
  blocks, with at most three generation calls each: extraction, end-to-end binding
  and reference-conditioned binding (84 calls maximum).
- The new twelve histories form six positive/negative contrasts: compound
  performed claims versus plans; same-step fulfillment versus another check;
  explicit reopening versus a new occurrence; supported long-gap continuation
  versus topic-only overlap; scoped correction/cancellation versus unresolved
  cross-speaker dispute; supported retrospective order versus insufficient time
  or future-only support. Detailed wording and annotations freeze in the approved
  Spec before implementation evaluation. Existing fixtures remain regression data,
  not newly independent evidence.
- All deterministic checks must pass. Extraction, conditioned binding and
  end-to-end results are separate gates: in each applicable cohort, every negative
  control and at least 80% of positive case blocks must pass, plus primary semantic
  review. Any fabricated attribution, unsupported closure or false continuation
  blocks admission, including when it appears inside a positive case. Omitted
  cases, invalid output and runtime refusals are not dropped from denominators.
- Only if all development/composition/new-history gates and legacy compatibility
  pass may the same frozen candidate consume the original ten holdout cases once,
  end to end only (at most 20 additional calls). Their original all-negative/
  80%-positive gate and primary semantic review remain. Definitions exist in the
  repository: call this unconsumed holdout, not independently blinded evidence.
- Total ceiling: 104 generation calls, 8,192 input-plus-output tokens per call,
  at most 2,048 generated tokens per call, 60-second soft generation limit and a
  120-minute run launch budget including load/validation. Do not launch after the
  budget expires. Record overruns and fail expired observations; these are not a
  hard process-kill guarantee. Resume cannot reset budgets or retry completed
  failures. A dependent call with invalid prerequisites is skipped with a reason,
  never supplied reference answers instead.

Case/history blocks, not individual claims, correlated order permutations or
reference-conditioned calls, are the reporting units. Paired contrasts and reused
development cases are not independently sampled corpus observations. Report counts
and per-case failures without population accuracy or statistical-significance
claims. Pure deterministic permutation/cutoff/revision checks need no extra model
calls. This is a bounded engineering trial, not proof of general corpus quality.

## Replay, Runtime State And Failure

Use the existing local evaluation-store ownership, atomic-write and 30-day
inactive-retention rules in `work_context_evaluation.py`, with a separate trial
namespace and an exact owned path recorded before execution. Reports stay outside
Git. This is evaluation evidence, not a production source/state database.

Cache stage observations with source, prompt, model/configuration and contract
fingerprints, actual attempts/tokens/time and validation disposition. Keep failed,
invalid, abstained and successful observations. Reference-conditioned and
end-to-end contexts cannot share a cache key. Changed scoring may replay stored
output but cannot silently trigger new generation. Interrupted/in-flight calls
must remain visible; resume only missing, safely resumable observations under the
same frozen budget, never favorable resampling.

Entry is a frozen synthetic suite and verified local assets. Running/progress,
complete, blocked-quality, invalid-input and interrupted states are explicit in
the CLI/report, with content-free diagnostics by default. Empty evidence produces
no invented work. Zero-generation replay must reproduce semantic results and
failure records. No server, background product job or interactive UI is added.

## Scope, Lanes And Implementation Order

The primary agent owns both lanes and integration; no delegation is required.

1. **Data:** versioned producer/effect extension of `work_state.py`, adapter
   validation and compatibility projection; preserve all v1 tests/results.
2. **Data + infra:** staged adapter using `work_context_model.py` and a separate
   bounded trial/report entry point reusing evaluation-store safety. No parallel
   runtime, installer, source ingestion or new database.
3. **Verification:** new synthetic fixtures and tests, frozen candidate execution,
   failure-preserving replay and separately reported Contract/Functional results.
   Update the source-claim policy and FEAT-0098 admission owner only when supported
   by actual approved implementation/evidence.

Likely affected surfaces: `src/localbrain/work_state.py`, new source-claim adapter
and trial modules, a local evaluation script, synthetic tests, the source-claim
policy and this Feature's future Spec/Run/Evaluations. There is no frontend lane.

Dependencies: FEAT-0099's passed pure contract and FEAT-0098's verified local
runtime, not acceptance of its failed semantic producers. No private simulation
report or live DB is needed. Original Runs and observed failures remain unchanged.

Out: private Session/DB reads, all-corpus jobs, embeddings, training/downloads,
Foundry changes, production effort identity/correction remapping, area clustering,
graph layouts/UI, endpoints/RAG, source/schema/organization writes, migrations and
legacy deletion. No new 60-Session cap or per-Session confirmation is introduced.

## Exit And Human Review Boundary

The owner approval covers this single implementation plus the frozen synthetic
trial and conditionally gated holdout, not an open-ended prompt search or
annotation of the owner's work. SPEC-0100 fixes the schema/fixture details within
this contract; a material scope/acceptance change must return to review before
execution.

Contract PASS and semantic PASS are separate. A working adapter with failing
semantic gates leaves the Feature/admission blocked, with failures reported and
no automatic next prompt variant. If the same candidate passes all original and
new gates including holdout, record its bounded admission with FEAT-0098 without
erasing earlier failed Runs. Even then, private whole-history reconstruction and
map integration require their own implementation/quality boundary; they do not
start as a side effect of this trial.

## Trial Outcome — 2026-09-23

RUN-112 completed the adapter and the one frozen trial, but the model candidate
failed acceptance. All 28 extraction responses were rejected by protocol/source
validation; no end-to-end binding call became eligible. Correct reference claims
and targets supplied to the independent binding diagnostic yield only 3/28 full
passes. These are not general semantic-accuracy estimates. All cohort gates fail;
the original holdout stays unconsumed and FEAT-0098 admission stays blocked.

The technical contract, 42 new tests, v1 exact-output parity and zero-generation
replay pass. Full regression runs 942 tests with no failures and one optional
skip. All 84 stored observations and counters survive replay without another
model call. Raw responses also show semantic errors; JSON repair alone is not a
demonstrated fix. No prompt/fixture/scorer change or favorable retry was made.

No private source, embeddings, UI, schema or organization changed. The subsequent
owner-requested output/evidence-interface review produced the
[relation-first inspection plan](../design/workflow-map-design-plan.md#relation-first-inspection-track):
then-draft FEAT-0101/0102 for whole-history affinity inspection and independent
draft FEAT-0103 for one direct-context relation trial. FEAT-0101 subsequently
passed; the delivered FEAT-0102 geometry was superseded by FEAT-0104/RUN-117.
FEAT-0103 remains unexecuted. Those separate inspection outcomes do not
change this Feature's failure, consume holdout, approve another candidate or
delegate classification to the owner. The larger flow-map objective remains
outstanding; similarity inspection is not complete work reconstruction.

## Harness Trace

- Spec: [SPEC-0100](../spec/spec-0100-source-claim-extraction-and-binding-trial.md).
- Run: [RUN-112](../run/run-20260923-112-source-claim-extraction-and-binding-trial.md).
- Evaluations: [Contract PASS](../evaluation/eval-0100-contract-source-claim-extraction-and-binding-trial.md),
  [Functional FAIL](../evaluation/eval-0100-functional-source-claim-extraction-and-binding-trial.md).
