# EVAL-0073: Deterministic Session Reference Capture And Reconciliation — Functional

## Metadata

- ID: `eval-0073-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260803-83`
- Attempt: `1`
- Feature: [feat-0073-deterministic-session-reference-capture-and-reconciliation](../feature/feat-0073-deterministic-session-reference-capture-and-reconciliation.md)
- Spec: [spec-0073-deterministic-session-reference-capture-and-reconciliation](../spec/spec-0073-deterministic-session-reference-capture-and-reconciliation.md)
- Execution Profile: `foundation-contract`
- Surface Lane: local Session synchronization and bounded detail read model
- Evidence Coverage: `complete`
- Created: `2026-08-03`

## Checks

- Claude and Codex fixtures preserve user/assistant mention roles and native
  event/call identity. A matching non-error structured result yields success, an
  explicit error yields failure, and missing or unstructured output yields no
  false read evidence.
- Safe generic URL normalization, configured Jira Item reuse, exact absolute and
  cwd-relative Markdown, unique workspace basename, ambiguous basename, missing
  target, and credential-bearing URL cases behave deterministically.
- Repeated reconciliation does not inflate locations. Completed read evidence is
  retained before ordinary mentions, at most 100 targets survive, and each target
  retains at most 50 normalized locations while observed totals remain visible.
- Two JSONL files mapped to one native Session produce one aggregate partial
  state. Changing one path reparses the current sibling set; removing one path
  retains and recomputes the Session, while removing the final accepted path
  deletes only the source-owned Session/evidence projection.
- Personal and Company Codex Sessions sharing one native ID keep independent
  reference URLs and deletion scope.
- Compatible startup preserves prior Source File fields, adds null mapping/version
  fields plus FK/index, and passes foreign-key validation. Existing Usage contract
  repair and meaningful-Session reconciliation remain green.
- Session reference projection succeeds while `Path.open` is forced to fail,
  proving detail-time source-file independence.

## Evidence

- Focused reference and regression set: 53 tests passed.
- Full repository suite: 343 tests passed.
- Data Model, generated-schema, value-registry, cleanup-audit, Mermaid, privacy,
  and whitespace checks passed.

## Findings

- None.

## Route

- Next action: `pass`; FEAT-0074 may enter its approved visible-product loop.
