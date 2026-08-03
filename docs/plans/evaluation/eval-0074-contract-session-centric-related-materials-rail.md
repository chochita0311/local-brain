# EVAL-0074: Session-Centric Related Materials Rail — Contract

## Metadata

- ID: `eval-0074-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260803-84`
- Attempt: `1`
- Feature: [feat-0074-session-centric-related-materials-rail](../feature/feat-0074-session-centric-related-materials-rail.md)
- Spec: [spec-0074-session-centric-related-materials-rail](../spec/spec-0074-session-centric-related-materials-rail.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Session reference projection → explicit organization projection → primary detail route
- Evidence Coverage: `complete`
- Created: `2026-08-03`

## Checks

- The read model exposes only `이 세션의 참조` and `연결된 작업`. The former
  consumes FEAT-0073 rows; the latter reads Documents and Resources that share an
  explicit Thread or Workstream with the Session.
- The former same-workspace query and reason vocabulary are absent. Same-workspace
  and globally recent Documents produce an empty projection unless direct
  evidence or a curated organization relation exists.
- Session-observed identity remains primary. Equivalent Jira rows ignore shared
  bootstrap title history, and generic URL query/fragment variants deduplicate
  under the normalized direct destination.
- Completed success suppresses failure-only evidence for the same target. The
  five approved Korean evidence labels map exactly to normalized kind/outcome;
  failed-only reads remain explicit.
- Stable target precedence removes a direct target from the organization group
  while retaining bounded Thread/Workstream context on the direct row.
- Groups own independent totals, first-10 slices, overflow rows, and partial
  states. A 101-target direct fixture reports 101 observed, 100 retained, and
  explicit partial copy.
- Owned Document, Atlassian, local Resource, and safe HTTP(S) destinations remain
  intact. Unsafe or missing targets remain visible and inactive with text.
- Only primary Session detail loads the rail. Projection exceptions are isolated
  from conversation rendering, Subsession detail has no rail, and `Path.open`
  failure proves the request performs no Session/Document file read.
- Product, Architecture, Local Context, organization, Session activity, design,
  interaction, and README owners now describe the same contract. Generated
  schema presentation and the 576-object cleanup ledger are current.

## Evidence

- Focused Session related-material/reference set: 22 tests passed.
- Full repository suite: 350 tests passed.
- Data Model owner check, schema presentation, cleanup audit, Mermaid, privacy
  for 738 candidate files, and diff validation passed.

## Findings

- None.

## Route

- Next action: `pass`; visible evaluators may complete the run.
