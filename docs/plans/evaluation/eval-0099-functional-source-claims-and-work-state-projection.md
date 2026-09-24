# EVAL-0099: Source Claims And Work State — Functional

## Metadata

- ID: `eval-0099-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-111](../run/run-20260923-111-source-claims-and-work-state-projection.md)
- Attempt: `1`
- Feature: [FEAT-0099](../feature/feat-0099-source-claims-and-work-state-projection.md)
- Spec: [SPEC-0099](../spec/spec-0099-source-claims-and-work-state-projection.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `data`
- Created: `2026-09-23`

## Direct Runtime Evidence

Application Python 3.9 environment; synthetic, in-memory packets only:

- `.venv/bin/python -m unittest discover -s tests -p 'test_work_state.py' -v`:
  **50 tests PASS**. Eighteen predeclared scenario packets cover historical pending
  versus current completion, cutoff, sibling/parent separation, execution versus
  result, compound claims, descriptive roles, cancellation, reopening, same/cross-
  speaker correction, correction retraction, unknown/retrospective order, topic/
  unresolved binding and explicit six-month continuation.
- Every scenario replays identically under five seeded array permutations and
  reference-order changes. Input snapshots remain unchanged. Ingestion-time and
  equivalent UTC timestamp spelling changes preserve output/digests. These are
  deterministic invariants, not independent statistical accuracy samples.
- Additional witnesses cover future-effective correction deferral, unavailable
  future context/target labels, partial coverage, unbound retractions, cross-target
  corrections, occurrence names, unsupported terminal changes, source edits/removal,
  binding withdrawal, the full 128-record bound and unrelated append stability.
- Rejection checks exercise every collection bound, malformed field replacements,
  extra authority, bool-as-int, invalid dates/revisions/quotes, coverage omissions,
  duplicate IDs/sequence, ambiguous bindings, cycles and dangling references.
  All errors stay fixed and content-free. File/network operations are patched to
  fail in the no-I/O witness; the pure projection still succeeds.
- `.venv/bin/python -m unittest discover -s tests -q`: **900 tests, zero failures,
  one existing optional graph-dependency skip**, final regression in 10.832 seconds.
  The final run disables bytecode writes and follows the ordering-provenance review.
  The pre-existing Starlette template-call deprecation warning remains unrelated.

## Acceptance And Regression

All five Feature acceptance sections have direct synthetic/runtime evidence.
Historical pending claims are retained, not mislabeled as later actions; only
their supported target advances. Unknowns/disputes remain visible without a
classification queue. Replay changes no weights and depends on no prior cache.

Existing ingestion, workflow projection/corrections, reconstruction, model trial,
simulation, routes and other application tests retain their regression results.
No server or browser verification is required: no screen, route or runtime
consumer was changed. Full regression uses isolated test resources, not the
user's real DB or actual inference weights.

## Findings, Limits And Route

No unresolved defect or required environment gap remains. Route: `pass`.
Coverage is complete **for the pure supplied-evidence contract**, not for automatic
work reconstruction. The test-supplied claims/bindings are not outputs produced
by Qwen; these results do not raise model accuracy, admit private processing,
prove area clustering or deliver the intended map. RUN-111 owns document/privacy
checks and the next separate producer-review boundary.
