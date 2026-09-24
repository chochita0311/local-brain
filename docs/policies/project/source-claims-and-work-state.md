# Source Claims And Work State

## Ownership And Admission Boundary

`work_state.py` owns the pure experimental in-memory source/state contracts.
The unchanged `localbrain.source-claim-state.v1` uses `synthetic-supplied.v1`
interpretations; the separately approved v2 records actual model-producer lineage
and scoped inferred lifecycle effects. Both projection functions remain pure,
with no filesystem, database, clock or model call. The standalone synthetic trial
below is the only v2 adapter consumer, not an application route, persistent ledger,
private source reader or production integration. This policy describes implemented
behavior, not successful model quality or permission to process private sources.

Source anchors establish wording. Claims interpret that wording. Bindings assign
claims to scoped targets. A projection reconciles the **reported** state supported
by those supplied objects. Valid structure/citations do not prove interpretation,
identity or completion. All output retains this distinction and reports
`model_admission: false`.

[Workflow Assertions](data-model/workflow-assertions.md) continues to own durable
user-confirmed Episode corrections. This module neither writes that ledger nor
maps its records to new experimental targets. Imported user utterances remain
source-attributed reports, not interactive product confirmation.

## Public Boundary

This section describes unchanged v1; the model-aware extension is specified below.

- `project_work_state(packet)` returns a new JSON-compatible projection or raises
  `WorkStateError` with a fixed content-free code. It does not mutate input or
  access the filesystem, clock, environment, database, network or a model.
- `text_revision(text)` computes SHA-256 of source UTF-8 text.
- `anchor_key(record, start, end)` includes source/session/native record identity,
  record revision, role/speaker and code-point coordinates. Packet-local aliases,
  labels and ingestion time are not source identity. Repeated wording is resolved
  by coordinates, not guessed occurrence.
- `claim_key(claim)` additionally binds interpretation meaning, kind, status,
  focus/context/effective-time evidence, producer and contract version. It is
  not a production effort identity or a durable correction target.

The exact versioned packet has `version`, `snapshot`, `records`, `anchors`,
`claims`, `targets`, `bindings`, `links`, `coverage`, `gaps`. Every object has
strict keys; unknown extensions require a new reviewed contract. The implementation
validates shapes before returning any projection.

| Object | Required fields and meaning |
| --- | --- |
| Snapshot | `id`, nullable `cutoff_at`, boolean `complete`; selected evidence boundary, not proof of real-world completeness |
| Record | `id`, `source`, `session`, `native_id`, content `revision`, `text`, `role`, `speaker`, source `sequence`, nullable `asserted_at`/`ingested_at`; native identity and sequence unique within source/session |
| Anchor | Derived `id`, `record`, `start`, `end`, exact nonempty `quote` |
| Claim | Derived `id`, `kind`, `focus`, `context`, `meaning`, nullable `status`, `effective`; interpretation supplied, never inferred by the projector |
| Effective time | `mode`, nullable `start`/`end`, `evidence`; assertion-relative, explicitly evidenced interval, or unknown |
| Target | Snapshot-local `id`, `kind`, nullable `parent`, `label`, identity `anchors`; parent hierarchy acyclic and non-propagating |
| Binding | `id`, `claim`, `target`, `relation`, `disposition`, `evidence`, nullable `continuation`; same-target is distinct from contributes/related |
| Continuation | `left` target-side anchors and `right_link` in the claim's Session, included in binding evidence; cross-Session links require a genuinely left-side anchor |
| Link | `id`, `before`, `after`, `kind`, `disposition`, `evidence`; before/reopens/corrects/retracts, with both endpoints cited |
| Coverage segment | `record`, `start`, `end`, `disposition`, `claims`; exactly partitions source text and accounts for every supplied focus claim |
| Gap | `id`, `reason`, `targets`, `obsolete_ids`; empty targets qualify the whole view; obsolete IDs are provenance, not dangling live references |

Roles are `user`/`assistant`. Claim kinds are `intention`, `action`, `outcome`,
`state`, `retraction`. Only state claims carry `pending`, `completed` or
`cancelled`; intention/action/outcome cannot implicitly supply a terminal state.
Targets are `effort`, `step`, `occurrence`; bindings are `same-target`,
`contributes`, `related`. Binding/link dispositions are `supported`, `unresolved`,
`contradicted`. Coverage is `claims`, `no-work`, `unresolved`; explicit claim lists
must match focused claims in the segment, with multiple claims per span allowed.
This accounts for supplied semantics, not all meanings an extractor might miss.

Gap reasons are `source-removed`, `source-revised`, `binding-withdrawn`,
`unresolved-identity`, `unresolved-time`, `unresolved-content`. A valid new snapshot
withdraws obsolete live references and records their absence; a malformed packet
that still asserts a live dangling reference is rejected without automatic repair.

## Scope, Time And State

Only a supported same-target binding affects state. There can be at most one such
binding per claim. A parent effort does not complete when a step or occurrence
completes. A failed result is still a result, not an invented retry request.
Completion of test execution does not claim successful validation of the goal.
Cross-Session same-target binding requires supplied bilateral continuation
evidence; matching vocabulary/resources and transitive topics do not create it.

The record's assertion time is distinct from the work's effective time and from
ingestion. Timestamps must be aware ISO values and normalize to UTC within this
packet only. Explicit effective intervals require focus/context citations;
unknown times are not filled with ingestion dates. Ordinary assertion-relative
reports can use reliable same-Session sequence; known, nonoverlapping effective
intervals and supported explicit before-links also establish partial order.
Conflicting dates/sequence or combined chronology cycles qualify the target and
withhold ordering-based resolution. Supplied cyclic/dangling links reject outright.

The cutoff admits records by assertion time; undated records are withheld when
a cutoff exists. Interpretations/bindings/links need all their evidence admitted.
Future context does not leak backward into a historical interpretation. Future
effective statuses remain historical reports but cannot update current state,
including through correction/reopen links. Withheld counts and qualifications
are observable; target labels whose identity evidence is unavailable are omitted.

Supported ordered pending → completed/cancelled advances state without deleting
history. Repeated identical status reports are compatible. Terminal → pending
requires an explicit applicable reopen. Changing terminal meaning requires
correction or intervening supported reopening; there is no latest-wins shortcut.

Same-speaker corrections/retractions displace their exact predecessor on the same
target while retaining both records. Acyclic successor evaluation allows retracting
a correction to restore its predecessor. Cross-speaker attempts remain disputes,
not authoritative overwrites. Missing target support on consequential links is
explicitly qualified rather than silently ignored.

Valid-transition reachability determines the active frontier. A single frontier
meaning gives that reported status, incompatible meanings give `conflicted`, and
no supported state gives `unknown`. `qualified` and sorted `qualifications` expose
incomplete coverage, unknown timing/identity, disputes and other unresolved support
alongside last supported state. They are not numerical confidence estimates.
Consumers must not hide qualifications and present verified completion.

## Output, Replay And Recovery

The output includes snapshot/version/producer, semantic input/output digests,
visible source anchors (including original role/speaker, time and sequence) and
attributed claim history, per-target state/frontier/
assigned/displaced claims and link trace, supplied visible bindings/links, gaps,
unassigned claims and coverage. Authority is `source-reported`; claim history is
`source-attributed`. History ordering is canonical serialization, not event order;
frontier/link/time fields carry the temporal meaning.
Per-target `order_basis` names the observed source-sequence, claim-time and/or
explicit-link inputs; `order_withheld` marks contradictory chronology that was
not used to resolve state. The original coordinates remain available for audit.

Identical packets replay identically without generation. Enumeration order and
ingestion timestamps do not affect semantic output. Unrelated evidence does not
retarget an existing result. A record edit changes anchor/interpretation identity;
source deletion or withdrawn bindings remove dependent support when the caller
supplies the new snapshot. Recalculation uses no previous-state cache or training.
No persistent data or recovery artifact is created. Source revision is not a work
reopen, and snapshot target IDs do not promise cross-regrouping identity.

## Bounds And Rejections

Limits: 128 records / 200,000 source code points; 512 anchors; 256 claims; 64 targets;
512 each bindings, links and coverage segments; 128 gaps. Reference lists allow
32 entries; IDs 128 code points; labels/meanings 1,000; quotes 4,000. Serialized
input is bounded to 2,000,000 bytes, nesting depth 12 and 40,000 visited values.
No silent truncation or partial projection is permitted. Limits bound one contract
packet, not the eventual all-Session processing population.

Diagnostics include shape/type, version, bound, duplicate/native-source, missing
reference, revision/identity/quote, time/evidence, coverage, transition, continuation,
ambiguous-binding and cycle errors. They contain no source wording or identifiers.
The pure consumer cannot reject every semantically false but well-formed binding;
that remains the future producer's separately measured responsibility.

## Verification Owner

[FEAT-0099](../../plans/feature/feat-0099-source-claims-and-work-state-projection.md)
and [RUN-111](../../plans/run/run-20260923-111-source-claims-and-work-state-projection.md)
own the supplied-claim implementation/evaluation evidence. The fixture suite
declares expected states independently of the reducer. The separately approved
model adapter is described below; private all-history use, production storage/
identity and map integration remain separate work. Passing the pure contract
does not change FEAT-0098's failed admission results.

## Model-Aware V2 And Synthetic Adapter

`project_model_work_state(packet)` validates `localbrain.source-claim-state.v2`
then shares the exact v1 state reducer. The v1 public call, key functions and
defaults remain unchanged. The v2 packet adds `producer` and `interpretations`;
it does not turn model output into a synthetic v1 result and relabel a wrapper.

The host records verified model/revision/assets and runtime, generation,
extraction/binding prompt and adapter fingerprints. Source anchors retain v1
native-span identity independently of that producer. `model_claim_key` includes
the interpretation and actual producer; `model_edge_key` likewise binds proposed
bindings and links to their producer. These are experimental snapshot identities,
not a production effort/correction migration contract.

Each interpretation has a claim ID, source/opening/fulfillment basis, optional
goal/step intent subtype and ordered premise IDs. Source claims keep original
source-attributed authority. Derived lifecycle claims use `model-inferred`
authority with explicit source premises; neither becomes verified completion or
user-confirmed authority. Model admission remains false in the pure projection.

Opening requires a source step intention. Fulfillment requires a step intention
or explicit pending claim and a reported action/outcome, all supported as the
same step/occurrence. The host preserves the focus premise's effective time and
all premise/context/binding support, so future evidence cannot leak backward.
An inferred effect cannot close an effort; explicit source status and normal
v1 transition/conflict rules still apply. A failed test execution can fulfill an
execution obligation, but whether it truly does so is an upstream semantic
judgment, not proven by this structural check. Missing support rejects the effect;
unresolved/contradicted judgments remain visible without creating live state.

`work_claims.py` implements the separately invoked two-stage adapter:

1. Extract atomic source roles and exact quoted spans, with explicit occurrence
   for repeated wording. The host owns offsets, revision, attribution and source
   time. Unselected text is unresolved, not no-work; coverage is not proof of recall.
2. Propose effort/step/occurrence targets, scoped bindings, lifecycle judgments,
   ordering/correction links and optional paired-context relationships. Short
   citation aliases resolve only to original spans or original whole messages.
3. Compile validated v2 input and project state; emit legacy work-unit/pair views
   for unchanged quality checks. Unbound pending work remains visible; child
   completion does not close its parent. No model summary replaces the reducer.

Strict JSON validation does not guarantee model output grammar or semantic truth.
Invalid or truncated outputs fail without quote repair, retries or self-approval.
Whole-input bounds remain explicit; an adapter packet is not a corpus-size cap.

`work_claim_assessment.py` and `work_claim_trial.py` own frozen synthetic comparison
and failure-preserving replay. Reference-conditioned binding receives correct
claims/targets and is labeled conditional evidence; end-to-end generation receives
neither. Expected claims, grouping, effects and states are independently declared
synthetic references, not private-work ground truth. A correct final status with
wrong premises still fails, and terminal-scope/continuation safety failures cannot
hide in the positive percentage threshold. Primary semantic review remains required.

The CLI accepts only the fixed synthetic suite and verified installed 8B assets.
Completed wrong/invalid/refused observations are retained in a separately owned
finite-lived evaluation namespace outside Git. Config or cache mismatch refuses;
clean resumes generate only missing observations within cumulative limits, while
unknown in-flight state blocks automatic retry. Expired trials cannot silently
reset the same Run's budget. Replay revalidates stored raw outcomes without model
generation. Conditional holdout requires the same revalidated development report
and a report-bound primary review receipt. There is no automatic private consumer.

[FEAT-0100](../../plans/feature/feat-0100-source-claim-extraction-and-binding-trial.md),
[SPEC-0100](../../plans/spec/spec-0100-source-claim-extraction-and-binding-trial.md)
and [RUN-112](../../plans/run/run-20260923-112-source-claim-extraction-and-binding-trial.md)
own the numerical trial limits and measured quality outcome. That outcome must
not be inferred from this implementation policy.
