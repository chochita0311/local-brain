# RUN-20260923-109: Evidence-First Work Context

## Metadata

- Run ID: `run-20260923-109`
- Status: `blocked`
- Attempt: `2`
- Feature: [FEAT-0098](../feature/feat-0098-local-work-context-inference.md)
- Spec: [SPEC-0098](../spec/spec-0098-local-work-context-inference.md#approved-evidence-first-candidate--run-109)
- PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `infra`, then `data`
- Required Evaluators: `contract`, `functional`

## Approved Boundary And Route

The owner continued after RUN-108 separated protocol sensitivity from persistent
semantic errors. Implement one evidence-first candidate on the installed 8B:
source-selected goal/field evidence, outcome membership, compatible context and
explicit linkage precede publication. Missing support automatically abstains;
the owner is not made into a per-Session classifier.

The primary agent performs Orchestrator → Spec → Builder → Contract/Functional
review sequentially. No delegation, new dependencies, models, training, private
data access, embeddings, organization writes or UI changes. The larger target
remains all-Session reconstruction and an inspectable workflow map.

## Frozen Evaluation Boundary

Freeze candidate identity and twelve new compositional cases before model calls.
Evaluate those and the unchanged four original development cases once, with
separate split gates and primary source/field/relationship review. Only a passing
development report and semantic review qualify for the ten unchanged holdout
cases, once. No post-output prompt/label tuning or larger-model fallback.

Case bounds, clean interruption allowance, refusal/cache ownership and replay
requirements are owned by the Spec. Retain completed failures without generation
on replay. A diagnostic/harness PASS cannot substitute for extraction admission.

## Execution Evidence

Implementation and 141 work-context tests pass in the application and installed
model runtimes. One test was corrected to snapshot its report digest before
mutating a shared mock contract; persisted evidence was never overwritten.
The previous diagnostic, extraction reports, original fixtures and embedding
state remain intact. No model observation had been generated at this freeze.

Frozen before inference:

- Candidate protocol: `c6c186262ccef4936ddb30a465164b90896a533371f5d2412a11e6be1a22964c`
- Development cases: `2ed9cbd02bac819d14701e3ab7903dedbe8fa9813d80333af753c8caffc8df21`
- Original development: two positive and two negative cases, unchanged.
- New composition: four positive and eight negative cases; six extraction and
  six relation cases. Both cohorts must independently meet their unchanged gates.
- One candidate, 8B/MPS/eager/non-thinking/greedy; no prompt, expectation, scoring,
  semantic-label order or source-selection changes after model outputs.
- No existing model evaluation or simulation process was active before launch.

### Attempt 1 — Pre-Generation Integration Failure

All sixteen cases refused with `INVALID_CHOICES` before model loading/generation:
the legacy finite-code validator allowed only eight characters, while the new
semantic labels include longer words. No model answer or semantic evidence was
produced. The fake generator had not enforced this adapter boundary; its tests
now do. The first report is retained separately, not deleted or overwritten.

### Attempt 2 — Corrected Adapter, Unchanged Semantic Candidate

Add a versioned, explicit 32-character semantic-label option. Preserve the legacy
eight-character default, character whitelist, eight-token limit, exact code/EOS
constraints and all original strategy identities. Actual-adapter tests cover both
paths. Offline tokenizer preflight checks every new label before another trial.
No prompt, label spelling/order, source packet, expectation or scoring was changed.

The corrected candidate protocol is
`f921f6965dc527fd612aedc1290ca7ad7bcc7b02d70f175782f0ac5febb48f49`;
the frozen development-cases digest is unchanged. Use a distinct owned output
folder for this one corrected execution. This is an integration fix before any
model answer, not a second semantic candidate or tuning after poor answers.

## Completed Trial And Review

Tokenizer preflight verified all fifteen distinct labels against the installed
tokenizer: exact round trips, at most three tokens, no weight loading/generation.
The corrected candidate then completed all sixteen cases once. The corrected
configuration is `61db48b0cf0219e6bb9719408cf1d5f87f909f53fa8e3acab6a2799f64117a0f`;
inference identity is `edd1503ce9bd4baf996aa6ad8d4bc4495b33c66ab01951c919176e458d5af717`.
The first pre-generation failure is not scored as model-quality evidence.

| Frozen cohort | Structurally grounded outputs | Content passes | Negative controls | Positive cases | Gate |
| --- | --- | --- | --- | --- | --- |
| Original development | 3/4 | 3/4 | 2/2 | 1/2 | FAIL |
| New composition | 10/12 | 4/12 | 2/8 | 2/4 | FAIL |

The primary agent reviewed every final output and all decision traces. Across
both cohorts, only the no-work case passes extraction (1/8); relationships pass
6/8. These are assistant-authored synthetic cases, not a population accuracy
estimate. Different composition and scoring prevent treating 7/16 as a direct
improvement/regression percentage against RUN-108's focused diagnostic.

- Two mixed-work cases refuse contradictory/multiply matching goal membership.
  This prevents publishing those ambiguous groups, but the underlying decisions
  also label requests and pending work as progress/results. Refusal is not
  successful reconstruction of the two intended efforts.
- The four published extraction cases all have semantic errors: plans and even
  explicitly unperformed actions appear in progress; completed work remains
  pending; a reported action with no recorded goal becomes a goal. The same-model
  unit audit approves these mistakes. Attribution and exact quotes remain intact.
- The non-work example refuses after an audit contradiction; no partial units
  escape. It is still a failed negative control, not the required empty result.
- Shared-file separation, conflicting reused identifiers, grounded short
  resumption and a six-month resumption pass. Contextless continuation is
  incorrectly called related; topic-only activities are incorrectly called
  continuation with a source-valid but semantically unsupported link. Both wrong
  relationships pass the same-model audit. Some correct relations also include
  generic pending/pronoun spans incorrectly selected as concrete goals.

The model's repeated `supported` judgments do not establish the cause. This Run
does not isolate token bias, wording, task decomposition or general model ability.
It does establish that literal grounding and extra same-model audits are
insufficient to admit this candidate. No output was repaired or prompt revised
after generation. Holdout remains untouched; no private Session was opened.

## Runtime, Replay And Verification

- 205 model calls, 113,723 input tokens and 446 output tokens; 171.4 cumulative
  case seconds, including initial model loading. Cases took 2.6–30.2 seconds.
  Peak sampled MPS driver allocation was about 18.7 GB, not total system/process
  RAM. No inference timeout, OOM or malformed semantic label was observed.
- Actual identical-config replay reused all 16 observations, including three
  refusals and six valid-but-wrong outputs, with zero further generation. A second
  replay's before/after hashes, attempt counts and cumulative 205-call accounting
  match exactly. Every case remains at one semantic attempt and both gates fail.
  Existing model assets verify unchanged during replay.
- 142 work-context tests pass in the installed model runtime. Full application
  regression passes 827 tests with one optional graph-dependency skip. Contract,
  failure-preserving cache, corrupt/config mismatch, interruption bounds and
  holdout prerequisites have synthetic regression coverage.
- Final repository/catalog/privacy checks are recorded by the evaluations.
  No UI surface changed. No model generation process or task scratch remains.
  The first integration-failure report and corrected semantic report are explicit
  evaluation evidence outside Git, each owned with 30-day inactivity expiry.

## Disposition And Next Decision

[Contract](../evaluation/eval-0098-contract-local-work-context-inference.md):
PASS, partial coverage. [Functional](../evaluation/eval-0098-functional-local-work-context-inference.md):
FAIL on extraction/relationship admission. The implementation is complete, but
Feature/Run remain blocked on a planning gap in semantic inference. The rejected
candidate remains opt-in for reproducibility; it is not a product default.

Return to a bounded approach decision, not another automatic model run. The next
recommendation is a matched comparison of direct semantic-role classification
against these independent property judgments, using new frozen contrastive
contexts and separate negative controls for work continuity. RUN-108's focused
role results motivate that hypothesis but do not prove it will fix composition.
Do not simply add more same-model approvals, loosen expectations, rerun completed
failures, add training/models, or ask the owner to classify Sessions one by one.
Any new candidate needs its own bounded approval; all-Session reconstruction,
area grouping and the inspectable flow map remain the destination, not completed
work. Existing vectors, source DB, UI and legacy organization are unchanged.
