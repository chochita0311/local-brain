# EVAL-0015: Session And Subsession Source Functional

## Metadata

- ID: `eval-0015-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260717-15`
- Attempt: `1`
- Feature: [feat-0015-session-subsession-source-contract](../feature/feat-0015-session-subsession-source-contract.md)
- Spec: [spec-0015-session-subsession-source-contract](../spec/spec-0015-session-subsession-source-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: ingestion identity and consumer exclusion
- Created: `2026-07-17`

## Scope And Checks

- Parsed synthetic Claude primary and subagent JSONL and Codex first-meta parent, subagent, and branch records.
- Stored parent, direct child, grandchild, missing-parent, and cyclic records, then reconciled their local relations.
- Exercised upgraded schema preservation, parent deletion, Search indexing, direct detail eligibility, Dashboard, daily, source, tool, workspace, and Project statistics.
- Seeded a subsession with both a Search row and a confirmed Workstream thread link to prove retrieval still excludes it from candidates and evidence.
- Ran `uv run python -m compileall -q src tests`, the complete 27-test unit suite, `git diff --check`, and the repository privacy check.

## Evidence

- Primary and direct-child relations resolved deterministically; the nested child remained stored but was not displayable at the current one-depth boundary.
- Missing and cyclic parents retained `session_role = 'subsession'` with a null internal parent and returned from no top-level or detail lookup.
- Parent deletion cleared only the internal FK and did not promote the child.
- Only the parent contributed one Session, two events, and one tool use to all tested statistics; child and grandchild values contributed zero.
- Only the parent produced a Search row. A deliberately stale child Search row and confirmed link still yielded no maintenance candidate or evidence artifact.
- The migration removed the workspace branch, preserved workspace identity and its user-curated project link, and marked Claude/Codex files stale for one normal source-backed rescan.
- All 27 tests passed; compile, whitespace, and privacy checks passed.

## Findings And Regression

- No blocking functional defect remains.
- No source JSONL, Git working tree, branch, external system, or runtime user database was mutated during verification.

## Route

- Next action: `pass`
