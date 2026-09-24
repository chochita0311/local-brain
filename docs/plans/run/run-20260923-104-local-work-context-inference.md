# RUN-20260923-104: Local Work Context Inference

## Metadata

- Run ID: `run-20260923-104`
- Status: `blocked`
- Attempt: `1`
- Feature: [FEAT-0098](../feature/feat-0098-local-work-context-inference.md)
- Spec: [SPEC-0098](../spec/spec-0098-local-work-context-inference.md)
- PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `infra`, then `data`
- Required Evaluators: `contract`, `functional`

## Boundary And Routing

The owner approved trying the proposed generative model on 2026-09-23.
This was the sole execution target at that approval. The earlier affinity-only Run
had returned to planning following owner review; its completed backfill and then-remaining
live replay gap are retained rather than relabeled as workflow understanding.
This independent admission test does not consume its report or require a new
private-data sample. The primary agent performs sequential roles without workers.

## Current Route

Installation, infrastructure and the bounded development trial are complete.
The model-quality gate failed; corpus application is blocked on a revised
model/extraction approach. The recommended post-run route is planning review,
not further blind prompt retries or another unapproved model download. No
production/UI or legacy changes are part of this Run.

## Development Attempts

- Prompt v1, development split only: negative controls passed; extraction and
  continuation were rejected because scalar goal/target/link strings violated
  the quoted-object schema. The mixed-goal response also omitted an independent
  goal. No holdout/private cases ran. Tightened the prompt's concrete object
  examples and all-goals instruction (v2); validation and expected labels were
  not weakened. This is prompt engineering, not weight training.
- Prompt v2, greedy development split: 3/4 outputs were structurally valid but
  only 2/4 cases passed; the second goal was still missing, and an independent
  pair cited only the right side. No holdout/private cases ran. Rather than more
  prompt edits, compare one fixed, official non-thinking sampling configuration
  on the same development cases. No alternate seeds or relaxed labels are used.
- Prompt v2 with the official non-thinking sampling settings and one fixed
  content-derived seed per packet: 3/4 structurally valid, 2/4 cases pass. The
  omission and grounding failure persist. The development trial stops here;
  holdout and private full-history execution remain unperformed, not passed.

## Evaluation And Handoff

- [Contract](../evaluation/eval-0098-contract-local-work-context-inference.md):
  PASS for observed boundaries, partial evidence.
- [Functional](../evaluation/eval-0098-functional-local-work-context-inference.md):
  FAIL on semantic admission, partial evidence; acceptance impact is blocking.
- The public model remains installed for reuse. The explicit private synthetic
  report/checkpoint retains the final configuration under its 30-day expiry.
  No task scratch remains. A known public-download diagnostic log was removed
  after verifying task ownership and process termination; unrelated shared cache
  files and installed assets were preserved.
- Original sources, Foundry assets and the full-population embedding cache remain
  unchanged. The next private execution must still cover all admitted Sessions,
  not a smaller sample chosen to improve the apparent score.
- The 4B choice was a low-cost first baseline using an existing runtime, not a
  verified quality winner or a hardware memory ceiling. Failure cannot yet be
  assigned exclusively to parameter count rather than this extraction recipe.
