# EVAL-0072: Session Reference Evidence Contract — Contract

## Metadata

- ID: `eval-0072-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260803-82`
- Attempt: `1`
- Feature: [feat-0072-session-reference-evidence-contract](../feature/feat-0072-session-reference-evidence-contract.md)
- Spec: [spec-0072-session-reference-evidence-contract](../spec/spec-0072-session-reference-evidence-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Session reference ownership, persistence, and value contract
- Evidence Coverage: `complete`
- Created: `2026-08-03`

## Checks

- `session_reference_scans` owns one Session's aggregate fingerprint, extractor
  version, complete/partial/error state, observed total, and 100-target bound.
- `session_reference_evidence` owns privacy-minimized target/source-location and
  approved completed-read evidence separately from Activity Event text, shared
  Resource titles/content, remote state, and user organization.
- Target/FK/normalized-destination parity and evidence/outcome/tool-call parity are
  enforced by SQLite; invalid direct rows fail closed.
- Session and target cascades remove only unresolvable derived rows. Evidence
  replacement cannot delete shared Documents, Resources, remote memory, notes,
  classifications, or organization links.
- Fresh and compatible idempotent schema paths converge on 38 ordinary tables,
  48 physical foreign keys, and 37 effective named indexes without rewriting an
  existing Session.
- Workspace And Session Activity is the single owner; Data Model, Architecture,
  Privacy, value dictionaries, Schema presentation, and cleanup audit agree.
- Persisted fields are bounded and cannot retain full messages, opaque tool
  arguments/results, credentials, fragments, unapproved query material, or remote
  content.

## Evidence

- Focused Session reference schema tests: 5 passed.
- Full repository suite: 332 tests passed.
- Data Model, generated value dictionary, Schema presentation, 9 Mermaid diagrams,
  and 572-object cleanup audit checks passed.
- Privacy check passed for 729 candidate files; `git diff --check` passed.

## Findings

- None.

## Route

- Next action: `pass`; FEAT-0073 may enter build.
