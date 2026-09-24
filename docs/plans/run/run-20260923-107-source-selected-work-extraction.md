# RUN-20260923-107: Source-Selected Work Extraction

## Metadata

- Run ID: `run-20260923-107`
- Status: `blocked`
- Attempt: `3`
- Feature: [FEAT-0098](../feature/feat-0098-local-work-context-inference.md)
- Spec: [SPEC-0098](../spec/spec-0098-local-work-context-inference.md)
- PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `infra`, then `data`
- Required Evaluators: `contract`, `functional`

## Boundary And Route

The owner approved the proposed extraction improvement after confirming the
larger destination: full-history semantic retrieval plus work/continuity inference
feeding an inspectable flow map, with minimal routine confirmation. This Run
changes inference mechanics, not embeddings or product scope. Earlier failures
remain evidence. The primary agent performs sequential roles without delegation.

Implement the Spec's source-selected classification/membership strategy and
bounded constrained-choice adapter, then test protocol, grounding, field mapping,
cache invalidation and interrupted cases. Freeze one 8B non-thinking greedy
candidate before its original four development cases. Review fields separately
from automatic counts and keywords. Run the untouched holdout once only if the
candidate qualifies. No blind retries, benchmark weakening or extra model install.

## Evidence Boundary

Development fixtures are assistant-authored synthetic checks, not owner-labeled
real workflows. Format/grounding validity is not semantic accuracy; even a
synthetic pass cannot establish useful work-area clustering or map acceptance.
The existing full-population embedding cache and current UI remain unchanged.
Private source processing, training, production organization and legacy cleanup
are outside this Run. Task scratch must be removed; explicit evaluation state
retains its existing owner and 30-day inactivity expiry.

## Attempt 1 — Source Selection

All four outputs passed structure/grounding, and three passed the frozen content
checks. Both relationship labels were supported bilaterally and acknowledgement
correctly produced no work. Mixed extraction failed: goals and remaining work
were classified as none, leaving one reported activity with an unknown goal.
This is a semantic omission, not a protocol failure or full-corpus quality score.

A single diagnostic of the first synthetic goal, using the same prompt without
the answer-code constraint, also returned the none code. Thus the constraint is
not the demonstrated cause of that selection. The wording of none/actual work
can conflate unperformed requests with non-work; that is a hypothesis, not yet
proven. No diagnostic file or private input was created.

## Attempt 2 — Bounded Development Clarification

Clarify that recorded user requests, goals and plans are work evidence even
though the analyzer must never execute their instructions. None means no work
intent or activity, not merely no performed action. Freeze v2 before execution;
preserve v1's report and unchanged expected answers. This is one development-only
prompt refinement inside the approved extraction improvement, not seed search,
holdout tuning or changing the safety gate. No further blind prompt iteration.

V2 also produced four grounded outputs, but only two content passes: mixed goals
and reported progress were omitted, and an independent pair became uncertain.
A bounded CPU/float32 reference of the same first goal also selected none, matching
MPS/bfloat16; this one observation does not prove device equivalence generally.
No CPU candidate is being silently selected from that diagnostic.

## Attempt 3 — Goal-First Source Selection

Stop revising the per-span classifier. The final bounded development comparison
uses a distinct `selected` strategy: choose independently resumable goal/activity
anchors from the whole conversation first, then explicitly select source spans
for each anchor's fields. This reuses the earlier staged work structure while
removing free-form quote/object generation. Keep classified v2 as a reproducible
failed comparator, not the production default. Freeze selected v1 before its one
development pass; no further automatic approach expansion after this comparison.

The final comparison passed both grounded relationship cases and no-work
abstention. Mixed extraction failed with `MISSING_ANCHOR`. Its decision trace
selected all six sentence spans as independent anchors rather than the two
intended goals, and selected request/goal evidence as reported progress/results.
The sixth unit then omitted its own anchor and the complete case was rejected.
Thus this is not merely a serialization failure: the intermediate model choices
also fragment work and confuse requested versus performed actions. No partial
unit output was published as a successful result or repaired into a pass.

## Comparison Outcome

| Candidate | Valid final outputs | Frozen content checks passed | Main failure | Time / calls |
| --- | --- | --- | --- | --- |
| Per-span classified v1 | 4/4 | 3/4 | Goals and remaining work omitted | 15.2 s / 15 |
| Per-span classified v2 | 4/4 | 2/4 | Goals/progress omitted; independent pair became uncertain | 14.2 s / 13 |
| Goal-first selected v1 | 3/4 | 3/4 | Over-fragmented anchors, wrong field selections, then missing anchor | 93.9 s / 81 |

All are greedy non-thinking 8B on MPS eager. Final output token totals were 30,
26 and 162; driver allocation peaked around 17.8, 17.7 and 17.8 GB respectively,
not total process/system RAM. Times include load and do not measure full-corpus
throughput. No time-limit or out-of-memory failure occurred in these candidates.

Syntax and citation construction are now separated from semantic choices, and
the tested acknowledgement is no longer invented as work. These narrow gains do
not establish reliable extraction: no candidate passes the full development gate
or field-level review. The ten holdout cases remain untouched. No real Session,
embedding, work-area grouping or UI was changed or judged by these synthetic cases.

## Verification And Handoff

- Contract PASS with partial coverage; Functional FAIL on model-quality admission.
- 87 work-context tests pass in both runtimes. Full regression: 772 tests,
  zero failures, one optional graph-dependency skip. The 30 added tests cover
  bounded code decoding, source projection, abstention, explicit citation/link
  selection, mixed-message grouping, missing anchors, overflow and cache identity.
- The 8B model rehashes unchanged after inference. Actual classified v2 replay
  reuses all four valid results without generation and retains its failed gate.
- Privacy check passes for 964 candidate files; the generated catalog, 649-object
  schema audit and diff checks are verified at handoff. No UI surface changed.
- Model outputs remain inferred. This is not an independent real-workflow
  assessment, a general model ranking or permission for broader processing.
- Retain the opt-in strategies and explicitly owned expiring synthetic reports
  for reproducible diagnosis; existing default strategies are unchanged. No
  task scratch, active model job, new dependency or extra model download remains.
- Stop this bounded comparison. Next review must address semantic goal extraction
  and field association; do not keep adjusting the same four cases, weaken
  grounding, silently adopt a candidate or impose per-Session labeling on the
  owner. A different approach requires a separately bounded follow-up decision.
