# EVAL-0085 Contract: Workflow Episode And Direction Contract

## Metadata

- ID: `eval-0085-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-20260914-95](../run/run-20260914-95-workflow-episode-and-direction-contract.md)
- Attempt: `1`
- Feature: [FEAT-0085](../feature/feat-0085-workflow-episode-and-direction-contract.md)
- Spec: [SPEC-0085](../spec/spec-0085-workflow-episode-and-direction-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `Pure Episode and direction descriptors; durable owners`
- Evidence Coverage: `complete`
- Created: `2026-09-14`

## Checks And Evidence

- `workflow_projection.py` supplies one versioned pure boundary for Episode,
  reason, relation, diagnostic, and normalized-relation values. It adds no
  route, persistence owner, migration, value-registry family, or import-time
  external operation.
- Episode identity is the SHA-256 digest of a length-delimited stable source key
  and native Session ID. Local row ID affects only the Session destination;
  title, workspace, provider, and path do not affect rebuild identity, and the
  serialized descriptor excludes the native ID and source path.
- Eligibility remains primary-work-only, Subsessions remain subordinate, and
  observation, activity, lifecycle, closure reason, and authority remain
  independent. `ended_at` may extend observation time but cannot close work.
- Direction is limited to `continues`, `branches-from`, and `merged-into`.
  Strict forward time, a strong reason, authority/reason parity, self-edge
  rejection, and deterministic cycle omission enforce the approved abstention
  boundary. Workspace, Git, lexical, and temporal proximity remain
  supporting-only signals.
- Product, Architecture, Privacy, and Workspace/Session Activity owners match
  the executable contract. The regenerated Schema Presentation and 623-object
  cleanup audit are current without a physical-schema change.
- Focused verification passed `16/16`; the complete suite passed `498/498`.
  Data-model ownership, repository privacy over `854` candidate files, and
  `git diff --check` also passed.

## Findings

- None.

## Current Route

- Current route: `PASS`; FEAT-0086 may consume this contract.
