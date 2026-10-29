# SPEC-0126: Code Learning Contract

## Metadata
- ID: `spec-0126`
- Status: `approved`
- Run: [RUN-164](../run/run-20261017-164-code-learning-contract.md)
- Attempt: 1
- Parent Feature: [FEAT-0126](../feature/feat-0126-code-learning-contract.md)
- Parent PRD: [PRD-0023](../prd/prd-0023-code-and-command-learning.md)
- Surface: docs
- Execution Profile: foundation-contract
- Required Evaluators: contract
- Created: `2026-10-17`
- Updated: `2026-10-17`

## Implementation Goal
Write a bounded additive contract for a manually reviewed code/command lesson.
Version 2 extends the current packet; old normalized JSON and attempts remain
unchanged. The first producer is the existing reviewed import CLI, with material
captured by the curator, not a new all-repository watcher.

## Acceptance Mapping
1. Exact scene evidence and uncertainty → typed command/diff scene and fingerprints.
2. Question depth → concept, understand/predict/transfer, line references and rubric.
3. Selection → one daily scene, explicit deterministic priorities and reason.
4. Learning evidence → delayed unhinted self-report, feedback exposure exclusion,
   optional practice and no mastery/automatic grading claim.
5. Qwen → retrieval of versioned passages, later generation from supplied evidence;
   no weight training, web access, automatic teaching admission or model run.

## Required Evidence And Open Blockers
Contract evaluation is a source-level document review only. No runtime tests are
part of this foundation outcome. Model quality, automatic discovery/freshness,
cross-lesson concept generalization and adaptive interval validation are later
boundaries; they do not block the reviewed reader.

