# FEAT-0099: Source Claims And Work State Projection

## Metadata

- ID: `feat-0099`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-23`
- Updated: `2026-09-23`
- User review status: after reviewing the proposed boundary, the owner approved
  the model-free, synthetic-only implementation on `2026-09-23`. RUN-111 owns
  this execution; model trials, private processing and product integration remain out.

## Goal

Define and exercise a pure, replayable contract that preserves **what a source
claimed at the time** separately from **the work state supported by those claims
in a selected evidence snapshot**. Resolve how a later completion can remove a
specific pending item from the current view without erasing the earlier record,
closing unrelated work, or promoting a speaker's report into verified truth.

This is a representation/projection foundation, not a natural-language extractor,
an identity-discovery algorithm, a new persistent ledger or model admission.

## Why A Separate Feature

[RUN-110](../run/run-20260923-110-work-role-formulation-comparison.md) found both
compound-claim omissions and historical pending work left in current remaining
work. In `work_context_evidence.py`, progress/results describe the focus's report,
while remaining work is explicitly evaluated at the end of the conversation.
The model currently has to extract a claim and reconcile later events together.
Separating those responsibilities is a testable design hypothesis, not proof
that this mixture caused all failures or that a deterministic reducer can repair
incorrect extraction or same-work judgments.

The existing
[workflow assertion ledger](../../policies/project/data-model/workflow-assertions.md)
is exclusively user-confirmed correction history. Its authority, storage and
Session-Episode targets are unsuitable for model-derived source claims. Existing
quoted work-unit IDs are output-content digests, not durable effort identities.
This Feature therefore introduces a separate experimental contract without
reinterpreting either owner or declaring one Session to be one effort.

## Acceptance Contract

### 1. Separate Evidence, Interpretation, Binding And Projection

| Object | Meaning and authority | Required provenance |
| --- | --- | --- |
| Source anchor | A span in one admitted source record; evidence of wording, not truth of the reported work | Source-scoped native identity, record revision, exact offsets/quote, original speaker and source order/time |
| Source claim | An interpretation of that span: intention, performed action, observed outcome or explicit scoped status | Anchor(s), contextual antecedents when needed, interpretation version and source-attributed/inferred authority |
| Target binding | A proposed assignment to a particular effort, subtask or occurrence, distinct from contribution or topical similarity | Target scope, supporting anchors, supported/unresolved/contradicted disposition and producer identity |
| State projection | The reported status supported for a bound target in a particular snapshot | Contributing and displaced claims, binding/ordering basis, unresolved/conflicting inputs and projection version |

All four are distinct objects even if represented in one bounded packet. An
exact quote validates a locator; it does not prove its interpretation, binding
or truth. No source speaker, including a user speaking inside an imported record,
becomes a product `user-confirmed` correction merely by being quoted.

The first implementation consumes **synthetic, explicitly supplied claims and
bindings**. Test-supplied semantic judgments must be labeled as such, never
presented as an automatically achieved extraction/identity capability. The pure
consumer validates structure, provenance and consistency; a structurally valid
but semantically false binding is still an upstream quality failure it cannot
universally detect.

### 2. Preserve Compound And Historical Claims

- A source span can support multiple claims; a claim can need multiple spans
  for a predicate and its antecedent. Splitting a compound statement preserves
  its parent source and every represented clause. There is no one-sentence,
  one-claim, one-Session or one-claim/one-flow rule.
- An intention is not a performed action; a performed action is not an observed
  outcome. A failed test is an outcome, not automatically a new request to fix or
  retry it. Illustrative/meta text and acknowledgements supply no work claim by
  default. Unknown goals do not invalidate a supported activity report.
- The historical claim “this check is not done yet” retains that meaning after
  a later completion. Later events must not add their actions/results to the
  earlier quote or reclassify that quote as if it reported completion.
- In the supplied synthetic packet, each expected claim and each unresolved
  source segment is accounted for. This validates representation capacity and
  omission reporting, not automatic detection of every clause in arbitrary text.
- A later extractor must report omitted/unresolved material separately from
  no-work text. Unknown material does not become a new effort or owner review
  request merely because it cannot be assigned.

### 3. Reconcile Only A Supported Target At The Right Granularity

- The target is an explicitly scoped work obligation or outcome and, where
  relevant, its occurrence/attempt. A file, repository, ticket, label, embedding
  neighbor or area membership is not sufficient target identity.
- “Contributes to this effort” is not “fulfills this obligation.” Completion
  affects only its supported target. A finished edit, completed test execution
  and achieved overall outcome are different scopes. No implicit upward closure
  or default all-children-done rule closes an effort.
- A cross-Session binding must preserve FEAT-0098's compatible-goal and explicit
  continuation-evidence requirements. This Feature accepts test-supplied binding
  evidence only; it adds no implicit-continuity producer or transitive grouping.
- Repeated daily checks, retries, branches and different revisions cannot be
  collapsed by a matching name. If their occurrence identity is unresolved,
  retain them as unresolved contributions instead of applying a completion.
- Projection status is `unknown`, `pending`, `completed`, `cancelled` or
  `conflicted`, always qualified as **reported**, not independently verified.
  A supported explicit reopening returns the same target to `pending` while
  retaining its earlier completion and the reopening reason/evidence.
- Descriptive intentions/actions/results alone do not force a terminal state.
  An explicit outstanding/planned step can support pending status at its own
  scope; a broad desired goal alone does not manufacture a separate pending
  item. An outcome changes status only with a supported fulfillment claim at
  the relevant scope. Cancelling work is not completing it.

### 4. Use Evidence Order, Not Ingestion Order Or Latest-Wins

- Distinguish assertion time (when the source said it), claimed effective time
  (when the work reportedly happened, if stated), source sequence and ingestion/
  computation time. Unknown effective dates remain unknown. A new import is not
  a new work event.
- A projection identifies its evidence snapshot and cutoff. It may describe
  the latest supported **recorded** state, not all work that actually happened
  or a guarantee that the corpus is complete. Later evidence cannot leak into
  a historical snapshot that did not contain it.
- Order ordinary pending-then-completed reports using supported work chronology;
  source sequence can order utterance-relative statements in the same context.
  Missing/equal timestamps, retrospective reports or conflicting dates must
  not acquire an invented total order. An explicit supported relation can
  establish order even when exact dates are unavailable; array order, ingestion
  time and lexical ID sorting cannot.
- Compatible ordered pending → completion is a state transition, not a
  contradiction. A later pending statement after completion needs evidence of
  reopening, correction or a new occurrence; recency alone does not select one.
  Incompatible maximal claims on the same target yield `conflicted`. Missing
  identity/order yields unresolved evidence and a qualified/unknown state, not
  silent “last writer wins.”
- Correction/retraction explicitly targets the claim it displaces and preserves
  both versions. An assistant cannot gain owner-confirmed authority, and a
  later speaker cannot silently erase another speaker's contradictory report.
  Unresolved disputes remain inspectable, not settled by role priority or a
  same-model self-audit. Cyclic or dangling correction/ordering references fail
  validation without a partial projection.
- If a potentially state-changing claim lacks sufficient binding/order, the
  output must expose that gap alongside any last supported status. Consumers
  cannot present an unqualified current completion while hiding that uncertainty.

### 5. Replay And Revision Without Training Or New Persistence

- Anchor identity includes source scope, record identity/revision and exact
  source coordinates. Interpretation identity additionally includes its meaning
  and producer/contract version. Presentation names and local SQLite row IDs
  are not durable identities.
- Unchanged packet/configuration yields identical semantic output and digest;
  input enumeration changes do not change supported chronology or the answer.
  Unrelated appended evidence cannot retarget or close existing work.
- A changed record, removed anchor, changed interpretation, or revoked binding
  invalidates dependent projection support. Recompute from the admitted snapshot
  rather than retaining a stale completed state. An equal-length source edit
  cannot inherit the old claim's identity. Source revision is not a work reopen.
- Snapshot replacement is explicit input, not an automatic source scan. The
  caller supplies a new well-formed packet with withdrawn support removed from
  live claims/bindings and its absence recorded as unresolved provenance. An
  obsolete ID in an unresolved record is not an effective graph edge. A packet
  still asserting a valid link to a missing anchor fails validation; the pure
  projector does not silently repair it or read an older source elsewhere.
- Experimental targets are snapshot-scoped. This Feature does not promise
  production effort identity across regrouping or migrate durable corrections
  onto those targets. That remains a later ownership/update contract.
- No database, report cache, model, filesystem source reader or product route
  is added. The module is a pure bounded packet validator/projector. Fixed
  numeric packet limits belong to its approved Spec before implementation;
  overflow refuses explicitly, never silently truncates evidence.

## Scope Boundary

In: one versioned in-memory source-claim/binding/state contract; pure validation
and deterministic projection over supplied synthetic evidence; invariant tests;
an owner contract document after approval. The primary agent owns the data lane
and integration; no delegation is required.

Out: natural-language clause extraction, new prompt/model trials, model training
or downloads, holdout consumption, private Session/DB access, corpus backfill,
embedding changes, automatic effort/area discovery, persistent state or schema
migration, legacy deletion, user-correction remapping, CLI/server integration,
map/UI work and endpoint/RAG work.

## Pass Or Fail Checks

Freeze synthetic packets and expectations before implementation evaluation.
All deterministic contract checks must pass; there is no partial percentage gate
that hides a failed closure, attribution or source-revision invariant.

| Supplied synthetic history/control | Required projection or invariant |
| --- | --- |
| Pending check, then supported completion of that same check | Earlier pending claim retained; current reported completion with both supports |
| Same history viewed before completion was available | Pending; no future-result leakage |
| Pending check, then completion of a different check in the same file/effort | Original check stays pending; no sibling/parent closure |
| Completed test execution, failed result, no retry request | Execution may be complete; failed outcome retained; no invented next action or effort completion |
| “Edited X and test Y passed” / “Edited X and test Y is still pending” | Both claims represented with their own meanings and linked original context |
| Plan/request, example-only text, social reply, activity with unknown goal | No invented performed work, goal, result or status |
| Explicit same-target reopen / cancellation / targeted correction | Distinct reported transitions, with prior claims retained and attribution visible |
| Reused name, shared resource or topic-only match | No implicit target binding, work merge or completion |
| Compatible explicit continuation after a long gap | Time gap alone neither severs the supplied identity nor closes work |
| Retrospective report, equal/missing times, opposing reports without resolution | Supported partial order only; unresolved/conflicted state, no arbitrary latest-wins |
| Reordered enumeration or late ingestion of an already dated event | Same projection for the same admitted evidence and supported order |
| Unrelated append, source edit/deletion, revoked link, identical replay | Unaffected targets stable; changed dependencies recomputed; no stale terminal state |
| Invalid/cyclic/dangling references, bad offsets/revision, excessive packet | Fixed rejection; no partial output, inferred repair or fallback source read |

Passing demonstrates correct handling **given the supplied claims and links**.
It does not measure extraction/identity accuracy, corpus coverage or end-user
usefulness. A fake semantic binding must remain recognizable as a test input,
not be advertised as something the structural validator has proven true.

## Dependencies And Regression Surfaces

- PRD-0017's approved reconstruction direction supplies the parent scope.
  RUN-110 supplies motivation, not admitted model output.
- FEAT-0098 remains blocked. This pure contract can be tested without an admitted
  extractor; any later model adapter/private producer still needs its own
  approved boundary and unchanged admission requirements.
- Do not modify or rescore original work-context, RUN-109 or RUN-110 fixtures.
  New source-claim semantics get a separate version and test suite. A later
  adapter must preserve current-field meaning: fulfilled historical pending
  claims may remain in history but not in current `remaining`; later actions
  cannot be attributed to earlier quotes. No compatibility adapter is built here.
- Existing workflow assertions, Episode projection, Workstreams/Threads,
  source ingestion, embedding caches and `/auto-work` remain untouched.
- Preserve all-Session processing as the downstream destination. Synthetic
  contract packets are not a new 60-Session production limit or a manual queue.

## Implemented Surfaces

- `src/localbrain/work_state.py`, `tests/work_state_cases.py` and
  `tests/test_work_state.py`.
- `docs/policies/project/source-claims-and-work-state.md`, linked from architecture;
  no physical table/value registry.
- This Feature's approved Spec, passed Run and complete Contract/Functional evaluations.

## Entry, Exit And Review Boundary

Entry: a bounded synthetic source snapshot plus explicit claims, target bindings
and ordering/correction evidence. Exit: a deterministic reported-state projection
with traceable history and unresolved inputs, or an atomic validation rejection.
Empty valid evidence yields no invented work. No loading/background/interactive
state is introduced by this pure data Feature.

The owner approved this **model-free, synthetic-only contract implementation**.
No field-by-field or Session-by-Session judgment is requested. The passed pure
contract makes later extraction errors distinguishable from projection errors;
it does not admit a model or automatically start private reconstruction.
The subsequent separate adapter review produced
[FEAT-0100](feat-0100-source-claim-extraction-and-binding-trial.md), subsequently
approved separately under RUN-112: model-aware provenance and a frozen
extraction/binding trial, not execution authorization from this PASS. That trial
is now implemented but quality-blocked; contract/replay success did not establish
correct extraction or binding. Area grouping and the inspectable map remain
downstream, not abandoned.

## Harness Trace

- Spec: [SPEC-0099](../spec/spec-0099-source-claims-and-work-state-projection.md).
- Run: [RUN-111](../run/run-20260923-111-source-claims-and-work-state-projection.md).
- Evaluations: [Contract](../evaluation/eval-0099-contract-source-claims-and-work-state-projection.md)
  and [Functional](../evaluation/eval-0099-functional-source-claims-and-work-state-projection.md)
  `PASS`, complete evidence for the pure synthetic contract, not model admission.
- Research rationale: [method review](../research/workflow-reconstruction-method-review.md#source-claimcurrent-state-review--completed-planning-only).
- Continuity: `2026-09-23` — completed the owner-approved structure review and
  proposed this isolated foundation. No code, tests, model, source data, UI or
  existing policy semantics changed during planning.
- `2026-09-23`: owner approved the isolated implementation boundary; entered
  RUN-111 under the Foundation Contract profile, data lane only.
- `2026-09-23`: implemented `work_state.py` and its non-persistent contract.
  Eighteen synthetic scenarios, 50 tests, permutation/revision replay and full
  900-test regression pass (one existing optional graph skip). Original model
  gates remain blocked; no private source, model, UI or persistence was added.
