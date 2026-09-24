# SPEC-0099: Source Claims And Work State Projection

## Metadata

- ID: `spec-0099`
- Status: `approved`
- Run: [RUN-111](../run/run-20260923-111-source-claims-and-work-state-projection.md)
- Attempt: `1`
- Parent Feature: [FEAT-0099](../feature/feat-0099-source-claims-and-work-state-projection.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-23`
- Updated: `2026-09-23`

## Source Set And Scope

The owner approved FEAT-0099's proposed pure synthetic implementation after its
structure review. The Feature acceptance contract, RUN-110's preserved failure
evidence, current quote validation and user-confirmed assertion ownership are
the source set. Implement `work_state.py`, synthetic fixtures/tests and a separate
non-persistent policy owner. No existing extraction fixture, prompt, schema,
source reader, route, model or production consumer changes.

## Packet Contract

`project_work_state(packet)` validates one exact-shape JSON-compatible packet
and returns a new deterministic projection, or raises `WorkStateError` with only
a fixed error code. No input mutation, source I/O, clock, random state, model or
database dependency. Version is `localbrain.source-claim-state.v1`; producer is
explicitly `synthetic-supplied.v1` (not a model or owner-confirmed authority).

Packet keys are `version`, `snapshot`, `records`, `anchors`, `claims`, `targets`,
`bindings`, `links`, `coverage`, `gaps`:

- Snapshot: `id`, nullable aware `cutoff_at`, boolean `complete`.
- Record: packet-local `id`, source scope `source`, native `session` and
  `native_id`, SHA-256 text `revision`, `text`, `role` (`user`/`assistant`),
  explicit `speaker`, nonnegative source `sequence`, nullable aware `asserted_at`
  and `ingested_at`. Native identity and sequence are unique within source/session.
- Anchor: derived `id`, `record`, code-point `start`/`end`, exact nonempty `quote`.
  Identity includes native source coordinates, revision, role/speaker and offsets,
  not packet record aliases or ingestion time. Repeated wording is disambiguated
  by offsets, not forbidden or guessed.
- Claim: derived `id`, `kind` (`intention`, `action`, `outcome`, `state`,
  `retraction`), `focus` anchor, `context` anchors, bounded `meaning`, nullable
  `status` and `effective`. Only state claims carry `pending`/`completed`/
  `cancelled`; other kinds cannot carry status. Producer/version are fixed by
  the packet contract and included in interpretation identity.
- Effective time: `mode` (`assertion`, `explicit`, `unknown`), nullable `start`/
  `end`, and `evidence` anchors. Explicit mode requires an ordered aware interval
  and cited focus/context evidence. Other modes have null interval and no time
  evidence. Assertion mode uses the focus record's source time/sequence, not
  ingestion time; unknown mode cannot borrow them as work chronology.
- Target: snapshot-local `id`, `kind` (`effort`, `step`, `occurrence`), nullable
  `parent`, `label`, nonempty `anchors`. Parent hierarchy must be acyclic. It is
  descriptive only, with no upward completion propagation.
- Binding: `id`, `claim`, `target`, `relation` (`same-target`, `contributes`,
  `related`), `disposition` (`supported`, `unresolved`, `contradicted`), nonempty
  `evidence` anchors and nullable `continuation`. At most one supported same-target
  binding per claim. Only supported same-target bindings can affect state.
  Binding evidence includes claim focus and a target anchor. A supported same-target
  cross-Session binding requires `continuation: {left, right_link}`: nonempty left
  anchors on target side and a cited right-side explicit-link anchor in the claim's
  Session. Structure/quotes are checked; semantic truth remains supplied, not proven.
- Link: `id`, `before`/`after` claim IDs, `kind` (`before`, `reopens`, `corrects`,
  `retracts`), `disposition`, nonempty `evidence` anchors. All references resolve
  and all supplied directed links are acyclic, including unresolved ones. Evidence
  includes both endpoints' focus and at least one after-side anchor. Specialized
  links affect only the same supported target. Reopen links connect terminal
  status to pending; retractions end at a retraction claim. Corrects/retracts
  displace only the same speaker's claims; cross-speaker disputes remain qualified.
- Coverage: per-record `{record,start,end,disposition,claims}` intervals that
  exactly partition the record text without gaps/overlap. Disposition is `claims`,
  `no-work`, or `unresolved`. Claim coverage lists exactly all claims whose focus
  lies wholly within the interval; multiple roles can share the same focus.
  This checks accounting of supplied claims, not detection of missing language.
- Gaps: `{id,reason,targets,obsolete_ids}`. Reasons are `source-removed`,
  `source-revised`, `binding-withdrawn`, `unresolved-identity`, `unresolved-time`,
  `unresolved-content`. Target IDs, if any, resolve; an empty target list qualifies
  the whole projection. Obsolete IDs are provenance only, not live graph edges.

Freeze bounds: 128 records, 200,000 total text code points; 512 anchors; 256 claims;
64 targets; 512 each bindings, links and coverage segments; 128 gaps. IDs up to
128 characters, labels/meanings up to 1,000, quotes up to 4,000; reference lists
up to 32; serialized packet up to 2,000,000 bytes and nested depth up to 12.
Reject non-JSON, wrong/extra keys, bool-as-int, nonfinite numbers, invalid time,
unknown vocabulary, duplicates, bad revision/offset and overflow with fixed codes.
Aware timestamps normalize to UTC; this does not migrate repository timestamps.

## Projection Algorithm

1. Validate the entire packet atomically; compute stable source/interpretation
   identities and canonical ordering for sets. Ignore ingestion time for semantic
   replay. Source enumeration and input array order never imply chronology.
2. Apply the snapshot cutoff to asserted time, not effective time. Records with
   missing assertion time are withheld when a cutoff is specified. Claims require
   all focus/context/time anchors visible; targets require all identity anchors;
   bindings/links require all supporting evidence. Withheld counts and unresolved
   coverage remain explicit. Do not include future quotes/labels in history.
3. Retain every visible claim's attribution, meaning, anchors and time mode.
   Bind supported claims to exact targets; retain related/contribution/uncertain
   bindings without applying them as status. Unbound or ambiguously bound state
   evidence and applicable gaps qualify last supported state, never auto-create work.
4. Establish partial work order from nonoverlapping known effective intervals,
   assertion-mode source sequence within one Session, and supported explicit
   links. Conflicting source dates/order become a chronology issue, not arbitrary
   ordering. Explicit links that contradict known order cannot settle state.
   Future effective status at a cutoff is retained in history but deferred.
5. Same-speaker supported corrections/retractions displace their exact earlier
   claim only with compatible order and same target. Resolve acyclic chains from
   successors backwards: retracting a correction reactivates its predecessor.
   Keep active/displaced history and reasons. Cross-speaker replacement attempts
   remain evidence of a dispute, never automatic truth or user-confirmed authority.
6. On active state claims, normal ordered transitions are same-status repetition,
   pending → completed and pending → cancelled. Terminal → pending requires an
   applicable explicit reopen link. Other terminal changes require correction or
   an intervening supported reopening; no latest-wins. Reachability through these
   valid transitions determines the frontier. One frontier status gives that
   reported status; incompatible frontier statuses give `conflicted`; no frontier
   gives `unknown`. Missing chronology is visible when it prevents reconciliation.
7. Return snapshot/version/producer, semantic input and output digests, visible
   anchored history, coverage and gaps, plus per-target reported state, frontier,
   all assigned claims, displaced claims, applicable link trace and qualification
   reasons. `qualified` flags incomplete/uncertain/conflicting support; it is not
   a calibrated confidence. Authority is always `source-reported`, with
   `model_admission: false`. All-abstain/empty is not extraction success.

Caller-explicit revision replaces the whole packet: remove obsolete live claims/
bindings/links and add gap provenance. Dangling live references still reject;
no automatic stale-source repair or persistent history ledger is introduced.

## Acceptance Mapping And Evaluation

Feature clauses 1–2: strict provenance/shape, attribution, compound-focus coverage,
descriptive-role neutrality and no mutation/I/O tests. Clause 3: sibling/parent/
occurrence separation, no topic join, long-gap cited binding and transition tests.
Clause 4: before/after cutoff, equal/missing/retrospective dates, order conflicts,
reopen, cancellation, same/cross-speaker correction and chain reversal tests.
Clause 5: all array permutations, ingestion-time change, identical replay,
unrelated append, equal-length edit/removal/withdrawn support and bounds rejection.

Fixture packets and expected states are authored before the implementation and
remain separate from its helper-generated IDs. They establish exact contract
semantics, not language-model or real-world accuracy. All checks are required.
Contract review inspects implementation, public helper/output shapes, policy and
likely consumers. Functional review runs focused tests then full application
regression. Catalog/link/privacy/whitespace checks accompany owner updates.

## Open Blockers

None for the approved pure contract. Natural-language interpretation, production
identity/persistence, admitted extraction and private/UI consumers remain excluded,
not assumptions to fill during this Run.
