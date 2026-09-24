# EVAL-0099: Source Claims And Work State — Contract

## Metadata

- ID: `eval-0099-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-111](../run/run-20260923-111-source-claims-and-work-state-projection.md)
- Attempt: `1`
- Feature: [FEAT-0099](../feature/feat-0099-source-claims-and-work-state-projection.md)
- Spec: [SPEC-0099](../spec/spec-0099-source-claims-and-work-state-projection.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `data`
- Created: `2026-09-23`

## Scope And Evidence

Primary-agent review of `work_state.py`, `work_state_cases.py`,
`test_work_state.py`, the Spec and
[implemented contract owner](../../policies/project/source-claims-and-work-state.md).
The candidate is the current uncommitted worktree, not an asserted commit.
All inputs are synthetic; no private source, model, endpoint or production UI
is part of this evidence. Fixture expected states were authored before the reducer;
shared identity helpers derive locators, not expected states.

| Contract surface | Result and direct evidence |
| --- | --- |
| Source/interpretation/state separation | PASS: strict objects, native/revision/offset identity, retained attributed history and explicit test-supplied producer; no user-confirmed authority |
| Compound accounting | PASS: two claims on one span, exact coverage partition and missing-claim rejection; this checks supplied accounting, not language completeness |
| Scope/continuity | PASS: supported same-target only, single supported binding, parent/occurrence separation, bilateral cross-Session evidence; semantics remain an upstream assumption |
| Time and corrections | PASS: assertion/effective/ingestion separation, cutoff admission, source sequence/interval partial order, conflict qualification, exact same-speaker correction/retraction and reopen links |
| Revision/replay | PASS: canonical input/output digests, permutation and ingestion-time invariance, changed source identities, removed/withdrawn support, explicit unresolved provenance |
| Invalid input and bounds | PASS: strict keys/types/enums/limits, fixed codes, no partial output; all collection bounds, malformed field cases, cycles and stale references tested |
| Persistence/consumer ownership | PASS: no schema, filesystem reader, clock, DB, model, network or application import; existing correction ledger and inference APIs unchanged |

## Stale-Assumption Check

Repository searches find no new runtime consumer outside the pure module and its
synthetic tests. The architecture owner links the new non-persistent policy.
Original work-context producers, prompts, RUN-109/RUN-110 expectations, DB/route
code and user-assertion ownership were not changed by this Run. No README setup
change is necessary because no command or user-facing behavior was added.

Review hardened future-effective correction deferral, withheld-interpretation
qualification, cross-target/unbound-retraction visibility and actual left-side
continuation support within the approved contract. One added negative test initially
hit an earlier missing-continuation guard because its setup also changed the first
binding; the fixture was isolated so the intended invalid-left guard is exercised.
Neither the eighteen scenario expectations nor old model-trial expectations changed.

## Limits And Route

No required pure-contract evidence gap remains. Natural-language claim extraction,
truth of supplied bindings, real-corpus usefulness and production identity are
unverified and explicitly outside this Feature. A structurally valid false link
can still yield a wrong reported state; `synthetic-supplied.v1` is not a semantic
certificate. Existing FEAT-0098 admission remains blocked.

Route: `pass`. Functional evaluation owns runtime checks; RUN-111 owns final
catalog/link/privacy evidence and the post-run handoff. No open implementation,
spec or planning defect remains within the approved boundary.
