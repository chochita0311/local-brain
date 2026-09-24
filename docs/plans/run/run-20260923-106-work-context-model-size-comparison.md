# RUN-20260923-106: Work Context Model-Size Comparison

## Metadata

- Run ID: `run-20260923-106`
- Status: `blocked`
- Attempt: `1`
- Feature: [FEAT-0098](../feature/feat-0098-local-work-context-inference.md)
- Spec: [SPEC-0098](../spec/spec-0098-local-work-context-inference.md)
- PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `infra`, then `data`
- Required Evaluators: `contract`, `functional`

## Boundary And Routing

The owner approved installing Qwen3-8B and comparing it against the frozen 4B
trial, while asking about disk cost. The official immutable asset inventory is
16.40 GB; installation retains a single content-addressed copy and preserves 4B.
Disk capacity is checked locally before download; machine-specific inventory
does not belong in this tracked record. This was the sole active Run, with
sequential primary-agent roles and no worker delegation.

Extend the existing installer/verifier to these two pinned models only, preserving
ownership, mismatch refusal and offline inference. Compare the existing two
strategies without prompt/seed/expectation changes, including primary semantic
review before holdout selection. No new corpus, UI, training, quantization,
Foundry dependency changes, organization writes or legacy cleanup.

## Current Route

The installation extension and both development comparisons are complete.
Neither candidate qualifies for holdout; downstream admission remains blocked.
Recommend a bounded extraction/protocol redesign for owner review, not another
automatic model download or weaker grounding. Earlier failures remain historical
evidence; no training, private processing or UI work was performed.

## Installation Transport

The default HTTP download slowed substantially on its last two shards. The
exact task-owned installer process and lock were verified before termination;
completed model blobs and partial downloads were preserved. Resumed using the
already-installed official Xet client, with a new private task-owned temporary
directory for diagnostics and chunk/shard caches disabled. No dependency, model
revision, benchmark setting or private-input boundary changed. That transfer
scratch was removed after the installer exited successfully and its exact owner
and file inventory were checked; it is not durable model storage. Only that
task's public transfer log, owner marker and empty temporary directories were
removed. The baseline 4B installation still verifies unchanged.

Installation completed and verified all 13 pinned assets, totaling
16,397,443,036 logical bytes. Observed allocated disk use rounds to 16.4 GB;
the installed baseline plus 8B rounds to 24.5 GB. Neither model's durable assets
depend on the removed transfer directory.

## Development Observation

The first 8B thinking case hit the unchanged 180-second generation limit before
EOS (1,981 output tokens; approximately 183.5 seconds including load). Its final
answer is unavailable, not a demonstrated wrong semantic answer. Do not extend
the frozen budget or decode truncated reasoning into evidence to obtain a pass.
All remaining cases and the staged candidate completed under the approved limits.

| Candidate | Valid outputs | Automated passes | Negative / positive passes | Generation time / tokens |
| --- | --- | --- | --- | --- |
| 8B single-pass thinking | 1/4 | 1/4 | 1/2 and 0/2 | 270.1 s / 3,293 |
| 8B staged non-thinking | 2/4 | 2/4 | 1/2 and 1/2 | 40.5 s / 540 |

Thinking selected the expected relation labels but cited only the right side
for both pairs; the validator correctly rejected incomplete grounding. The
no-work case abstained correctly. Staging grounded both pair judgments correctly,
but supplied a list instead of the required single evidence object for `goal`
in the first mixed-goal detail and acknowledgement case. Mixed extraction stopped
at that invalid detail; do not claim its second goal was omitted or validated.
Primary semantic review also found that staging treated a simple acknowledgement
as a work goal, independently of its schema error. No invalid output was repaired
or counted as passing, and truncated reasoning was not decoded.

These observations separate time/shape/grounding failures from wrong relationship
labels. The same-condition comparison does not establish an improvement over 4B,
but four fixed cases and one seed per packet are not a general model ranking.
MPS driver allocation peaked at about 17.6 GB and 24.5 GB respectively, not total
system/process RAM or an all-history capacity estimate. No out-of-memory or
invalid-probability exception occurred. The ten holdout cases remain untouched.

## Evaluation And Handoff

- [Contract](../evaluation/eval-0098-contract-local-work-context-inference.md):
  PASS for observed installation, ownership, offline and validation boundaries;
  partial coverage, not semantic model admission.
- [Functional](../evaluation/eval-0098-functional-local-work-context-inference.md):
  FAIL; neither frozen configuration passes the development gate. Whole-history
  inference, stable flow identity and the intended map remain undelivered.
- All 57 work-context tests pass in the optional model runtime; full application
  regression passes 742 tests with one optional graph-dependency skip.
- Rehash verification after inference confirms the 8B assets are unchanged;
  the preserved 4B installation also verifies. No private source was examined.
- Final checks pass: generated catalog currency, the 649-object schema audit,
  repository privacy (958 candidate files) and diff whitespace. No source schema,
  product consumer, embedding or UI changed in this Run.
- Installed models are retained as owned reusable assets. The synthetic reports
  remain purpose-owned evaluation state with the existing 30-day inactivity
  expiry. Transfer scratch is removed; no active generation or download remains.
- Further approach changes need a new bounded decision. Do not extrapolate this
  failure into a requirement for training, a larger model or owner classification
  of every Session. The intended minimum-confirmation product direction stands.
