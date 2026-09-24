# RUN-20260923-105: Work Context Strategy Comparison

## Metadata

- Run ID: `run-20260923-105`
- Status: `blocked`
- Attempt: `2`
- Feature: [FEAT-0098](../feature/feat-0098-local-work-context-inference.md)
- Spec: [SPEC-0098](../spec/spec-0098-local-work-context-inference.md)
- PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `infra`, then `data`
- Required Evaluators: `contract`, `functional`

## Boundary And Route

The owner approved the proposed same-model reasoning/staged comparison after
[RUN-104](run-20260923-104-local-work-context-inference.md) reported a failed
development gate. This was the sole execution target. Its prior failures remain valid
historical evidence, not silently replaced by the new trial. The primary agent
performs sequential implementation, Contract and Functional roles locally.

Implement thinking protocol and staged inference under the updated Spec; compare
the two frozen configurations on development and select at most one for untouched
holdout. No download, dependency changes, training, private corpus, UI changes,
organization writes or legacy cleanup. Passing this bounded admission trial only
readies the separate full-history producer; it does not deliver the workflow map.

## Attempt 1 — Fused Attention

Thinking stopped in sampling with a nonfinite/negative-probability RuntimeError;
bounded identical-configuration diagnostics reproduced it, with no final result
or holdout inspection. This is an execution failure, not a scored semantic failure.
Staged non-thinking completed: 4/4 structurally valid, 3/4 automated checks passed,
but acknowledgement was invented as work. Primary semantic review additionally
found progress from the first goal assigned to the second goal. Thus the automated
mixed-goal score alone overstates semantic correctness. Holdout remains untouched.

## Attempt 2 — Runtime Correction

Use existing eager attention on MPS to bypass the suspect fused decode path,
recording the new runtime identity. A small standalone attention probe did not
reproduce the model's failure; the public issue supports the bypass, not a proven
exact root cause. Re-run each frozen candidate once under this corrected runtime.
No prompt, seed, expected label, quote validator, dependency or model change.
Both the original failed trial and this numerical correction remain in history.

The corrected runtime completed both candidates without the numerical exception:

| Candidate | Structurally valid | Automated passes | Negative / positive passes | Generation time / tokens |
| --- | --- | --- | --- | --- |
| Single-pass thinking | 3/4 | 3/4 | 1/2 and 2/2 | 109.8 s / 2,034 |
| Staged non-thinking | 4/4 | 2/4 | 1/2 and 1/2 | 37.9 s / 632 |

The thinking response again cites only the right side of an independent pair
and supplies a non-null continuation link for that label. Primary review also
finds a requested action misclassified as reported progress. Staging identifies
both goals and grounds the independent pair, but omits remaining work, mixes one
goal's activities into another and treats an acknowledgement as a work goal.
The fixed automated checks do not cover every field-level semantic error; these
additional failures are recorded without changing the benchmark expectations.

Neither candidate qualifies for holdout selection. The ten holdout cases and
private corpus remain untouched. A fresh model-weight hash verification passes.

## Evaluation And Handoff

- [Contract](../evaluation/eval-0098-contract-local-work-context-inference.md):
  PASS for observed boundaries, partial coverage.
- [Functional](../evaluation/eval-0098-functional-local-work-context-inference.md):
  FAIL on model-quality admission, partial coverage, blocking downstream use.
- The 47 work-context tests pass in both runtimes; full regression passes 732
  tests with one optional graph-dependency skip. No UI surface changed.
- An identical-config staged replay reuses all four validated results without
  regeneration and correctly retains the failed quality gate.
- Repository privacy, generated plan catalog, schema-audit currency and diff
  whitespace checks pass. Runtime/CLI/docs were checked for stale strategy,
  protocol, identity and split-gate assumptions; unrelated worktree edits remain.
- Current status is blocked on the failed model-quality gate; recommend planning
  review for a bounded next model/approach comparison. Do not reinterpret this
  as proof that every 4B model fails, or that a larger model will necessarily pass.
- Installed model and explicitly owned synthetic evaluation checkpoints are
  retained for reproducible comparison under their existing ownership/expiry
  policy. No task-owned scratch remains; diagnostic commands wrote no files.
  Sources, Foundry assets, embeddings and existing product UI are unchanged.
