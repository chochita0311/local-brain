# SPEC-0100: Source Claim Extraction And Binding Trial

## Metadata

- Status: `approved`
- Feature: [FEAT-0100](../feature/feat-0100-source-claim-extraction-and-binding-trial.md)
- Run: [RUN-112](../run/run-20260923-112-source-claim-extraction-and-binding-trial.md)
- Parent: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, then `infra` integration
- Required Evaluators: `contract`, `functional`
- Attempt: `1`
- Approval basis: owner approved the bounded implementation/trial; this Spec
  translates that boundary without adding a private or product consumer.

## Source Set And Goal

The approved Feature, passed [source-claim contract](../../policies/project/source-claims-and-work-state.md),
`work_state.py`, verified `work_context_model.py` runtime and
`work_context_evaluation.py` evaluation-store rules are the implementation basis.
Original work-context and composition expectations remain unchanged.
Connect two bounded semantic stages to the existing deterministic state algorithm
with honest producer lineage and independently assessed stages.

## Data Lane: Versioned Projection

Keep the entire v1 public contract and results unchanged. Add
`localbrain.source-claim-state.v2` via `project_model_work_state`, sharing v1's
validator/reducer rather than converting model claims into synthetic output.
Source anchors keep v1 source-native identity. Model claim/binding/link identities
include v2 and the actual producer, with no model-provided authority fields.

The v2 packet retains v1 fields and adds `producer` and `interpretations`.
Producer is a strict host-created object: `kind=local-model`, model/revision,
verified asset fingerprint, runtime/generation fingerprints, extraction/binding
prompt fingerprints and adapter version. Interpretation entries identify `claim`,
`basis` (source, opens-obligation, fulfills-obligation), nullable `intent`
(goal/step) and premise claim IDs. Source interpretations have no lifecycle
premises; derived effects identify their actual source premises.

Source claims retain source-attributed authority and original speaker. Lifecycle
effects use model-inferred authority and retain premise IDs. The overall output
is source-reported, `model_admission=false`, with original evidence, inferred
effects and projection digest distinct. No persistent ledger or identity service.

Opening needs an explicit step intention. Fulfillment needs a step intention or
explicit pending claim and an action/outcome from the supported same step or
occurrence. It cannot target an effort. Both premises require supported same-target
bindings. Effect focus is the opening/fulfillment premise's source anchor, with
all other cited premises in context; effective time follows that premise.
All derivation evidence must be visible before the effect can affect a cutoff.
Unresolved/contradicted effects stay in the adapter trace and add a qualification,
not a live state claim. Ordinary v1 state/order/reopen/correction rules remain.

## Adapter Wire Contract

Inputs are synthetic records already carrying native identity, role/speaker,
sequence and assertion time. The host creates revisions and anchors. Imported
text has no runtime instruction authority. Every collection, reference and
string is bounded before processing; use at most 32 extracted claims, 32 targets,
64 bindings/effects/links and 128 source records within v1 packet limits.

Stage A returns exactly `claims` and `no_work`. Each claim has short `id`, `role`,
`span`, `context`, `time`. Roles are goal, step, action, outcome, pending,
completed, cancelled, retraction. They map to v1 kinds/status plus intention
subtype; a source can support multiple roles as separate claims.
Span is exactly `{message, quote, occurrence}`: zero-based occurrence selects an
exact substring, including repeated wording. Host computes code-point offsets;
negative/boolean/overflow occurrence and nonexistent quotes fail, without fuzzy
repair. Context is a bounded list of spans excluding focus. Time is null for
assertion-relative, `unknown`, or `{start,end,evidence}` with exact aware ISO
endpoints literally present in cited evidence. No inferred timezone/relative date.
`no_work` lists explicit spans; all uncovered content remains unresolved.

Stage B receives raw records plus validated Stage A claims and available citation
aliases. Claim IDs cite their focus; `@message-id` cites that whole source record.
The host resolves aliases to source anchors. This reduces repeated locator
serialization without letting the model fabricate source metadata.

Stage B returns exactly:

- `targets`: `{id,kind,parent,label,anchors}`; label is a citation alias, anchors
  are citation aliases, kind effort/step/occurrence. No gold targets in end-to-end.
- `bindings`: `{claim,target,relation,disposition,evidence,continuation}` using
  existing vocabulary; continuation is null or `{left,right_link}` citations.
- `effects`: `{id,kind,obligation,fulfillment,target,disposition,evidence}`;
  kind opens-obligation/fulfills-obligation, fulfillment null only for opening.
- `links`: `{before,after,kind,disposition,evidence}`; endpoints are claim/effect
  aliases and retain v1 link semantics.
- `pair`: null for ordinary histories, otherwise the legacy
  `{relation,evidence,link}` using citation aliases and bilateral source evidence.

Missing/extra fields, bad references, cycles, contradictory supported assignments
or impossible provenance fail atomically. Semantic falsehood that passes shape
validation remains an evaluation failure. No output repair/retry/self-audit.

The host generates producer-bound IDs, coverage partitions and supported effect
claims, validates the v2 packet, then computes state. Overlapping focus spans
use merged coverage intervals; any internal uncovered text remains separately
unresolved when representable, otherwise the merged interval adds an unresolved
gap. No-work overlapping a claim is contradictory input, not an override.

## Legacy Compatibility And Assessment

Produce legacy units from model-discovered effort roots and their descendants.
Goals are source goal claims only; actions/outcomes map to progress/results.
Pending claims and explicit steps map to remaining unless supported terminal
state or correction removes that obligation. Parent completion never hides a
child's pending claim. Unbound activity/pending remains visible as unknown-goal
units. Original quote/role attribution is validated through existing validators.
Pair judgments use the original pair validator, preserving its evidence semantics.
Contradictory continuation/binding evidence fails rather than choosing a winner.

Reference fixtures are authored before real model execution in a separate test
module. Each case freezes expected claim role/source spans, target scope and
grouping, binding/effect/link judgments, pair meaning and projected state. Exact
span inclusion permits bounded surrounding grammatical context but cannot hide
extra semantic predicates/roles. Match claims one-to-one by role/source/predicate;
match targets by frozen source scope and membership, never their generated name.
Use full primary semantic review in addition to automated checks, including every
extra claim, missed clause and effect premise. Original legacy checks also run.

The four paths and cohort/call/token/time gates are exactly those in FEAT-0100.
New source-claim cases: twelve histories in six predefined positive/negative
contrasts. Original development four plus composition twelve remain separate
cohorts; conditional original holdout ten is end-to-end only. Reference-conditioned
binding receives gold claims and target roster, is labeled accordingly and cannot
feed the end-to-end cache. Invalid extraction skips dependent binding, not the
independent reference-conditioned diagnostic. Denominators retain failed/skipped
cases. All-unresolved baseline and answered coverage are reported.

Freeze source/reference suite and adapter/scorer implementation fingerprints,
rendered stage prompts and verified generator settings before real generation.
No post-answer tuning. A framework defect may be fixed without generation and
replayed only if it does not change the frozen semantic candidate; otherwise
record the defect and return rather than silently generate a second candidate.
Definitions in the repository do not constitute independently blinded holdout.

## Infra Lane: Bounded Trial And Replay

One verified installed Qwen3-8B, MPS/bfloat16/eager, greedy non-thinking.
Bounds: 104 calls total, 8,192 total tokens, 2,048 output tokens, 60 seconds soft
per generation, 7,200 seconds cumulative active-run launch budget. Include
load/verification/preflight time; do not count idle time between clean resumes.
Oversized prompts refuse; there is no truncation. Expired calls fail even with
parseable answers. Meter actual attempts/tokens/time and reserve before calling.

Use a new owned outside-Git evaluation directory under the existing 30-day
inactive-retention contract. Store finite-lived owner/progress/report files only.
Every stage observation hashes its exact mode, prompt, input, producer and raw
outcome/metrics. Record failures, refusals, invalid outputs and skipped dependencies.
Persist call/time reservations before model entry; dirty in-flight interruption
blocks automatic retry. Clean resume executes only missing observations, never
completed wrong answers; scoring changes cannot resample outputs.

CLI offers describe, run and generation-free replay. It accepts only the fixed
synthetic suite, never DB/source paths. Default stdout is aggregate/content-free;
full synthetic evidence stays in the local owned report. Replay revalidates raw
observations, dependencies, budgets and configuration before recomputing scores.
Holdout requires the exact completed development report, all automated gates and
a separately recorded primary semantic review receipt bound to that report.
There is no implicit private job even after admission.

## Acceptance Mapping And Verification

1. Provenance/version: v1 regression byte-for-byte; changed producer changes
   interpretation IDs but not source anchors; forged lineage/derived support fails.
2. Extraction/binding: compound clauses, source edits, repeated/Unicode quotes,
   unknown/no-work and role attribution; missed clauses fail semantic scoring.
3. Lifecycle: same-step versus sibling/parent closure, failed execution versus
   achieved result, recurrence, reopening, cancellation, disputes and cutoff.
4. Trial safety: frozen shape/limits, offline runtime, no private reader, gate
   and holdout lock, failure-preserving replay, tamper/config mismatch, budgets,
   clean/dirty interruptions and no fake passed result from a constant abstainer.
5. Regression: relevant work-state/work-context tests, full application tests,
   catalog/privacy/links/whitespace and producer/consumer stale-assumption scan.

No frontend, schema migration, embedding, training, installation, source ingest,
production organization, correction remap or legacy deletion is included. Required
evaluations separate Contract result from semantic Functional result and coverage.

## Open Blockers

None at Spec handoff. RUN-112 subsequently completed implementation and the frozen
trial: contract checks pass, model-quality gates fail. That measured outcome is
owned by the Run/Feature, not a retroactive change to this approved contract.
The conditional holdout is ineligible; a revised candidate needs a separately
reviewed boundary, not an automatic implementation retry.
