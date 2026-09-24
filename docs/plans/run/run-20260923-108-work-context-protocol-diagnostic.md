# RUN-20260923-108: Work Context Protocol Diagnostic

## Metadata

- Run ID: `run-20260923-108`
- Status: `passed`
- Attempt: `1`
- Feature: [FEAT-0098](../feature/feat-0098-local-work-context-inference.md)
- Spec: [SPEC-0098](../spec/spec-0098-local-work-context-inference.md#approved-protocol-diagnostic--run-108)
- PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `infra`, then `data`
- Required Evaluators: `contract`, `functional`

## Boundary And Role Route

The owner continued after the [method review](../research/workflow-reconstruction-method-review.md),
approving its fixed-model synthetic protocol diagnostic. The primary agent owns
Orchestrator → Spec → Builder → Contract/Functional review sequentially, without
delegation. No UI lane or design/interaction evaluation is required.

Model-quality admission remains blocked; this Run's result describes diagnostic
coverage, never a replacement quality gate. Read no private Session or source DB.
Use only the existing pinned 8B installation/runtime and preserve other projects.

## Frozen Comparison

Twelve synthetic base cases, each with four alternatives and 24 conditions:
16 numeric choices (order × code mapping), four semantic-label choices, four
unconstrained short-text responses. Preserve semantic alternatives and original
context across conditions. No holdout consumption or original-fixture changes.
Record the suite/configuration fingerprint before inference and every completed
observation, including failure; reuse it without generation on replay.

Limits: 288 cells, at most 300 attempted calls, 1,200 cumulative seconds,
4,096 context / 256 output tokens, 30 soft seconds per generation. No new model,
training, protocol tuning after outputs, private backfill, embedding or UI work.

## Acceptance And Evidence Required

- Deterministic full matrix and independent order/code controls verified by tests.
- Semantic/protocol/citation scoring remains separate and does not read expected
  answers into prompts; source/role/focus remain intact.
- Safe owned output, same-config replay, interruption/budget accounting and
  changed-config refusal verified; all completed failures retained.
- Actual fixed-model matrix and all distinct short-text responses inspected.
- Existing inference regressions and repository privacy checks pass.
- Report diagnostic completeness separately from unresolved extraction quality;
  preserve previous failures and return a bounded next-step recommendation.

## Execution Evidence

The implementation's 108 work-context tests pass in the application and installed
Foundry tool environments. A test assertion was corrected to compare canonical
JSON values (tuple/list round-tripping), without changing model expectations.
The original admission fixtures and all previous strategies remain unchanged.

Frozen before inference:

- Suite: `fd3d4521e43a5a779576ffee353fb75c628af48e9ac39cb7c34224c94cd81443`
- Source: `tests/work_context_diagnostic_cases.py`; 12 cases / 288 conditions.
- Default production generation settings remain unchanged; the diagnostic alone
  requests the shorter bound and records actual template/prompt/token metadata.
- Completed failures are replayable observations, not retry candidates. A clean
  interruption can resume; an unclean in-flight crash refuses automatic reuse of
  an unknowable time budget. No model output had been generated at this freeze.

The first process stopped before creating diagnostic state: the Foundry checkout
environment lacks PyTorch. The existing installed Foundry tool environment was
resolved from its launcher; PyTorch 2.8.0 and Transformers 4.57.6 match prior
synthetic reports. No dependency was installed. This startup failure produced no
model observations and is not semantic evidence.

Review also corrected a replay-report metadata defect: after a clean interrupted
run resumes successfully, its obsolete top-level interruption error must not
remain in the completed report. The interruption/replay test covers both files.
This changes no model prompt, parser, expected answer, matrix or fingerprint.

## Completed Observation And Replay

All 288 conditions completed once, with no generation refusals, missing answers
or automatic retries. Inference/audit time was 364.5 seconds, with 3,523 generated
tokens; the longest generation call was 8.33 seconds. Model loading is included
in the cumulative time, asset verification is not. The sampled MPS driver
allocation peak was about 22.6 GB, not total process/system RAM. No OOM or timeout
was observed; these short cases do not measure full-history throughput.

The actual tokenizer audit records 288 distinct rendered-prompt hashes, one
template hash, and no input-token mismatch against generation (342–586 tokens).
Numeric answers are single tokens; semantic `unclear` and `separate` are two
tokens. Representation/tokenization remain part of this protocol comparison,
not a pure isolated causal test of the constraint callback.

The primary agent inspected all 48 short-text observations, comprising 46 distinct
case/answer texts. Scoring stayed frozen. The
[Functional evaluation](../evaluation/eval-0098-functional-local-work-context-inference.md#protocol-diagnostic--run-108)
owns the complete form/family counts and semantic/format findings. Seven of the
twelve cases changed semantic decisions under independently varied numeric
mapping and display order. Meaning labels improved the aggregate result but did
not resolve unsupported continuation or order sensitivity.

An actual same-configuration replay reused all 288 observations, including wrong
and format-invalid answers. Attempt count remains 288 and elapsed budget is
unchanged; observation and summary digests match the first completed report.
The replay constructor also verified the installed 8B assets again, unchanged.
No model generation or download is left running.

## Verification And Scope Result

- PASS: 108 work-context tests in both application and installed model runtimes.
- PASS: full application regression, 793 tests with one optional dependency skip.
- PASS: privacy scanner, 970 candidate files; diff whitespace, generated planning
  catalog and touched-document local link checks.
- PASS: independent matrix controls, no expected-answer prompt leakage, separate
  semantic/format/citation scoring, fixed bounds, owned storage and failure reuse.
  Interruptions, corrupt/mismatched caches and budget exhaustion have synthetic
  test evidence; this real run observed complete execution and zero-call replay.
- Required [Contract](../evaluation/eval-0098-contract-local-work-context-inference.md)
  and [Functional](../evaluation/eval-0098-functional-local-work-context-inference.md)
  evaluations pass the diagnostic scope, with partial Feature coverage. Previous
  extraction admission failures are not superseded by this narrower PASS.
- The CLI, runtime defaults, fixtures, README, architecture/privacy owners and
  planning projections were checked for stale assumptions. Original extraction
  strategies/expectations, holdout, private sources, embeddings and UI are unchanged.
- No task-owned scratch remains. Explicit synthetic evaluation state is a
  purpose-owned result under the existing 30-day inactivity-expiry contract,
  not a dependency on a temporary path.

## Next Boundary

RUN-108 passes because its frozen diagnosis is complete; FEAT-0098 remains
admission-blocked. The next recommendation is one bounded, evidence-first
extraction/relationship redesign on the same installed 8B, not more model-size
search or repeated order voting. Require recoverable goal/context evidence and
compatible scope before claiming work continuation; a deictic conversation link
alone is insufficient. Unknown relationships should abstain automatically, not
become a routine owner review queue. Keep semantic labels, original source
identity and citation assembly separate, and test label/reason disagreement.

A follow-up must distinguish contextless continuation from the same words with
a recoverable goal, shared topics/files from shared work, and mixed goals with
correctly attributed activities. Freeze new compositional development controls
before inference, retain original checks as regressions and consume the existing
holdout only after admission prerequisites pass. This is a recommendation for
the next bounded decision, not an implemented producer or permission for private
all-Session processing. Whole-history reconstruction and the intended map remain
the destination; this diagnostic does not change embeddings, UI or legacy data.
