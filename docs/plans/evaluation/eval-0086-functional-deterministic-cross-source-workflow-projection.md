# EVAL-0086 Functional: Deterministic Cross-Source Workflow Projection

## Metadata

- ID: `eval-0086-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run: [RUN-20260914-96](../run/run-20260914-96-deterministic-cross-source-workflow-projection.md)
- Attempt: `1`
- Feature: [FEAT-0086](../feature/feat-0086-deterministic-cross-source-workflow-projection.md)
- Spec: [SPEC-0086](../spec/spec-0086-deterministic-cross-source-workflow-projection.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `SQLite signals → bounded Episode/evidence payload`
- Evidence Coverage: `complete`
- Created: `2026-09-14`

## Checks And Evidence

- Missing, Maintenance, Subsession, metadata-only, and zero-activity selections
  return typed empty results; an eligible unconnected selection returns exactly
  one navigable Episode.
- Cross-source Session fixtures prove shared user Thread and shared reference
  plus Workstream produce adjacent continuations. Suggestion-owned membership
  and isolated workspace/root/branch/time overlap produce no candidates.
- Different observed branches with the same root and reference select the
  nearest earlier branch origin and retain deterministic-candidate authority.
  A later Session on `main` produces no `merged-into` relation.
- A 205-peer fixture proves the 200-candidate bound and honest total; graph
  fixtures prove the 24-Episode, four-branch-root, and four-Episodes-per-branch
  limits. Seven-item fixtures prove five-item evidence disclosure with retained
  totals for Local Context and Subsession families.
- Evidence fixtures project direct Local Context, user organization,
  Subsession, and Atlassian structure-reference sources beneath one Episode,
  retain first-observed UTC time, and preserve stale reference state without a
  refresh.
- Repeated projections serialize identically, execute no write statement, leave
  `connection.total_changes` unchanged, and exclude fixture-native IDs and
  private source/repository paths. Offset-aware event ordering uses chronological
  SQLite Julian time rather than lexical timestamp order.
- Focused tests passed `14/14`; the full suite passed `512/512`. The only output
  was the pre-existing Starlette `TemplateResponse` deprecation warning.

## Findings

- None.

## Route

- Next action: `pass`.
