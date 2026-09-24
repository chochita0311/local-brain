# RUN-20260922-103: Replayable Full-Session Simulation

## Metadata

- Run ID: `run-20260922-103`
- Status: `returned-to-planning`
- Attempt: `1`
- Feature: [FEAT-0097](../feature/feat-0097-replayable-session-simulation.md)
- Spec: [SPEC-0097](../spec/spec-0097-replayable-session-simulation.md)
- PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, `infra`
- Required Evaluators: `contract`, `functional`

## Boundary And Routing

Owner approved a replayable full-Session simulation on 2026-09-22. The earlier
sampled viewer is not changed or represented as full-data output. Existing local
model assets/runtime can be reused without downloading or modifying Foundry.
The primary agent performs sequential contract, build and evaluation work.

## Evidence

- Implemented separate source inventory, content-addressed embedding cache,
  grouping report and fixed-code CLI. The historical 60-Session viewer is not
  changed or mislabeled as the new full-population result.
- `20` synthetic simulation scenarios pass in the installed semantic runtime,
  including actual cosine/Louvain grouping. The ordinary environment skips that
  one optional graph test; `685` full regression tests otherwise pass.
- Actual installed-model smoke passed with synthetic Korean/English text;
  fingerprint verification and offline inference ran without model download.
- The real full-population inventory completed and embedding batches committed.
  The task-owned process was deliberately interrupted with SIGINT, exited with
  the fixed interrupted status, and resumed using existing cache entries. New
  embedding batches committed after resumption. Original data was not edited.
- On 2026-09-22 the first backfill was still running. The 2026-09-23 check
  confirmed complete publication and coverage accounting. Real-data unchanged
  replay and grouping-only replay remain unobserved; their synthetic counterparts
  pass. These live replay checks remain an explicitly deferred acceptance gap.
- The generated planning catalog and schema audit were refreshed; the privacy
  scanner passed. No task scratch is retained. The active checkpoint directory
  is private owner-managed simulation state with 30-day inactivity expiry.
- Private content, labels, detailed counts and machine-specific runtime paths
  are not copied into tracked artifacts.

## Evaluation

- [Contract evaluation](../evaluation/eval-0097-contract-replayable-session-simulation.md):
  PASS for tested boundaries; partial live execution coverage.
- [Functional evaluation](../evaluation/eval-0097-functional-replayable-session-simulation.md):
  PASS for tested behavior; partial live execution coverage.

## Continuation

Historical route at this Run's return to planning: the replay gap below was
subsequently closed by
[RUN-113](run-20260923-113-full-history-simulation-replay.md). FEAT-0097 now passes
its real unchanged/grouping-only replay gate; this Run retains its original
`returned-to-planning` outcome and evidence scope. Current UI/resumption status
belongs to the [design-plan handoff](../design/workflow-map-design-plan.md#handoff-to-next-track).

The 2026-09-23 read-only inspection confirmed complete publication and coverage
accounting. Current input differs by additions only; existing compared content
was unchanged. Private labels/counts were not disclosed. Real unchanged/grouping-only replay remains
unobserved; this return does not turn that gap into a PASS.

After discussing why chunk affinity is not workflow understanding, the owner
selected grounded context inference and explicitly approved its model trial.
[RUN-20260923-104](run-20260923-104-local-work-context-inference.md) became the sole
active execution target at that time. It tests an independent runtime/output contract and
does not consume this report. Preserve existing vectors and full-population
scope. Revisit the remaining live replay checks before a downstream producer
consumes this report; no UI or semantic-quality acceptance is claimed here.

## Remaining Product Boundary

Complete processing is not semantic quality acceptance. The time-oriented map,
supported temporal lineage, naming quality and legacy replacement remain
downstream work. No recurring classification approval is introduced.
