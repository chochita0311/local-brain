# RUN-20260923-112: Source Claim Extraction And Binding Trial

## Metadata

- Run ID: `run-20260923-112`
- Status: `blocked`
- Attempt: `1`
- Feature: [FEAT-0100](../feature/feat-0100-source-claim-extraction-and-binding-trial.md)
- Spec: [SPEC-0100](../spec/spec-0100-source-claim-extraction-and-binding-trial.md)
- PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, then `infra` integration
- Required Evaluators: `contract`, `functional`

## Approved Boundary And Ownership

The owner approved the proposed adapter implementation and frozen local synthetic
trial. Reuse the passed source-state algorithm and installed 8B, separate literal
claims from model-inferred obligation fulfillment, and distinguish conditioned
diagnostics from end-to-end quality. Original gates/holdout remain unchanged.
No private Session/DB, embeddings, installation/training, UI, schema or legacy
operation is authorized by this Run. The whole-history/map destination remains.

The primary agent performs Orchestrator → Spec → Builder → Contract/Functional
review sequentially. No delegation or new approval per synthetic observation is
required. FEAT-0098's failed semantic producers are not implementation dependencies;
only its verified runtime is reused. No immediate planning/spec blocker was found.

## Execution State

Implementation and 42 new model-free adapter/trial tests pass. All 28 supplied
reference controls pass their separately declared claim/binding/state expectations
and all sixteen original development/composition compatibility checks. These are
reference-supplied results, not successful model extraction.

Frozen before inference:

- Suite/implementation: `157cc18254c3779880665317005201bb1d0f456a704e0a72c8ce79338ba67588`.
- Four original development, twelve unchanged composition and twelve new claim
  histories; at most 84 development calls and 20 conditionally gated holdout calls.
- Fifty-six fixed extraction/conditioned prompts tokenize to 512–2,088 input
  tokens, within the 8,192 combined/2,048 output bound. End-to-end binding input
  also checks its actual generated-claim size at runtime; no such call became
  eligible because all extraction prerequisites failed.
- Prompt count digest: `1f29b2f037631542a609be7554425cf91037cf1a67ac86bf553e6374b12ef92d`;
  template: `41d5929bf73796beb66809ac700b2cf3ff81694f933e5c14d52b7fd6963c947d`.
- Installed 8B assets verify unchanged: `4a3bd61534203bb077e5d04f964eeb71f80c2d71460ca1003440a4483ad4ff7d`.
  Python 3.9.6, Torch 2.8.0, Transformers 4.57.6; MPS/bfloat16/eager,
  greedy non-thinking. Preflight loaded no weights and generated no answers.
- The sandbox does not expose MPS; the approved local GPU runtime was checked
  through escalated execution and is available. No related model/simulation job
  was active before launch. The new `source-claim-v1-trial` namespace under the standard
  LocalBrain runtime owner was used, not any previous report or Foundry state.
- Full regression initially found a stale generated schema reference ledger.
  Its lexical runtime-reference list was regenerated from unchanged manifest/
  decision sources; all 649 schema object decisions and physical schema stay intact.

Pre-generation verification completed: 942 full application tests pass, one
existing optional graph-dependency skip; all 42 new tests also pass in the
installed model runtime. A separate no-generation parity check reconstructed
the prior pure module in memory and first verified its recorded SHA-256
`b67845d95dc0aa4fc0a34aa368af0457f1493f4d7e00c6124367798ede1216f4`.
All eighteen original scenario outputs and ninety input-permutation outputs
match the extended module exactly. This check wrote no file or temporary artifact.

## Completed Trial And Primary Review

The single frozen real-model candidate completed. No candidate, fixture, prompt,
scoring rule or implementation fingerprint changed after launch. Contract checks
PASS; semantic Functional evaluation FAILS. The Run and Feature are blocked on
candidate quality, not waiting for more calculation or Session classification.

| Cohort | Extraction accepted | Conditioned binding fully passes | End-to-end binding attempted |
| --- | --- | --- | --- |
| Original development | 0/4 | 1/4 | 0/4 |
| Original composition | 0/12 | 1/12 | 0/12 |
| New claim histories | 0/12 | 1/12 | 0/12 |

All 28 extraction responses were rejected: fifteen invalid JSON outputs, ten
invalid exact-span occurrences and three nonexistent source references. These
are first rejection categories, not 28 measured semantic errors. Every dependent
end-to-end call was recorded as `PREREQUISITE_FAILED`, without generation or
reference substitution. The independent conditioned diagnostic still ran for all
28 cases: fifteen structurally valid answers, three full reference passes. It
supplies correct claims **and** targets, so does not demonstrate their discovery.

The primary agent reviewed every raw extraction and conditioned response against
the frozen source/reference cases and scores. In addition to serialization and
locator failures, responses treat thanks and explicit completed/pending statements
as goals, omit compound predicates and confuse planned with performed work.
Conditioned responses omit required opening/fulfillment judgments and binding
evidence; explicit distinctness/topic relationships often become uncertain.
No case-specific repair or favorable retry was performed. See the
[Functional evaluation](../evaluation/eval-0100-functional-source-claim-extraction-and-binding-trial.md)
for the complete failure classification and interpretation limits.

All three stages fail every cohort gate. The all-unresolved baseline also fails
every gate. No accepted unsafe closure is not a safety success when every
end-to-end answer is withheld. The original ten-case holdout remains unconsumed
and ineligible, not independently blinded. Private whole-history processing,
embeddings, UI, source/schema/organization changes and legacy deletion did not run.

## Runtime And Failure-Preserving Replay

- 56 actual generation attempts, 84 stored observations: 28 extraction, 28
  conditioned and 28 skipped dependencies. No generation timeout, OOM, truncation
  or runtime exception occurred; structural/semantic rejections remain failures.
- 58,349 input tokens, 8,981 output tokens; 771.820904 cumulative launch seconds
  including asset verification, preflight and load. Longest generation 54.439
  seconds; largest answer 558 tokens. Sampled MPS driver allocation peaked at
  22,051,340,288 bytes, not total system RAM.
- Configuration: `1693361ab6b82a3fb4c53117a877fe67063b78510b4d48ba1ce9cc0f266e2ebf`.
- Development digest: `47b61581b25d613d6488dd968a9f6357372212384e08e79a75bd49c6447dd267`.
- Semantic digest: `3d0a251650163bdaa88808af9058e648fdbdccc6e3f0cdf0202cd31c91a82c54`.
- Failed primary review receipt: `0bbbfa02a85954866ececcd24a97a96dd5c1405e1445b5fe6099c95b7043bf79`.
- Actual `--replay` reused all 84 observations with zero new generation. The
  pre-replay snapshot and replay have identical configuration, development and
  semantic digests, every observation hash, cumulative calls/time and token
  counters. The failed review receipt and all rejected/skipped results survive.
- No related model job or task-owned scratch remains. The outside-Git owned
  report is finite-lived evaluation evidence under the existing 30-day inactive
  retention/expiry contract, not a new permanent source database.

## Evaluations And Handoff

Final verification after the trial and owner-document updates: full regression
runs 942 tests in 12.194 seconds with zero failures and one existing optional skip;
privacy scanning passes 999 candidate files. Generated catalog/schema audit are
current. All 1,629 local Markdown links (683 fragments) across eighteen affected
documents resolve; full-file whitespace checks on 25 owned files and tracked diff
checks pass. Producer/consumer searches find only the isolated CLI and synthetic
test consumers, not an application route or background job. No temporary path
is referenced as a durable owner.

- [Contract](../evaluation/eval-0100-contract-source-claim-extraction-and-binding-trial.md):
  PASS, complete evidence for the implemented bounded contract, not model quality.
- [Functional](../evaluation/eval-0100-functional-source-claim-extraction-and-binding-trial.md):
  FAIL, complete evidence for this required development trial; the conditional
  holdout is correctly withheld, not a missing execution obligation.

The adapter and replay mechanism are implemented; the candidate cannot drive
the product. FEAT-0098 admission remains blocked. Recommend a planning review
of the model-to-host output/evidence interface and semantic decomposition using
these frozen failures before approving another candidate. This is not evidence
that more memory, a larger model, training or JSON repair would fix interpretation.
No next prompt trial or new model is launched automatically, and the user is not
asked to classify individual Sessions. Whole-history areas/efforts and the
inspectable temporal map remain the product destination. SPEC-0100 stays approved;
a materially changed candidate requires its own reviewed boundary.
