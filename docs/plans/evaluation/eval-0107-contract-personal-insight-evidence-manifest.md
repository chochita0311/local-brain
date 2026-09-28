# EVAL-0107: Personal Insight Evidence Contract

## Metadata

- ID: `eval-0107-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-20260927-118](../run/run-20260927-118-personal-insight-evidence-manifest.md)
- Attempt: `1`
- Feature: [FEAT-0107](../feature/feat-0107-personal-insight-evidence-manifest.md)
- Spec: [SPEC-0107](../spec/spec-0107-personal-insight-evidence-manifest.md)
- Execution Profile: `foundation-contract`
- Evidence Coverage: `partial`
- Created: `2026-09-27`

## Scope And Checks

- Inspected the producer API, validation path, SQL source joins, Event selection, versioned return shape, reference review, and project architecture/data/privacy owners.
- The producer only reads the existing `sources`, `sessions`, `activity_events`, and `search_index` structures inside a savepoint. No schema, Run storage, model, network, UI, or Workstream write was added.
- The event reference contains source identity, current Session/Event IDs, role, order, time, full normalized-text digest, bounded excerpt, and a current Session route. Review distinguishes missing and changed references without replacing frozen text.
- The core API and value-shape names are fixed by the active Spec. A future consumer must treat FTS hits as candidates and use `selection_basis`, `lexical_match_state`, and omission reasons before making a relevance claim.

## Evidence And Limits

- Environment: source and owner-document inspection plus Python syntax compilation of the new module. No runtime database or synthetic behavior test was run.
- Producer: `src/localbrain/personal_insight_evidence.py`. Consumer: later PRD-0018 analysis Run; none is installed yet.
- Schema and ownership: existing `schema.sql` keys and Session FTS, `Project Architecture`, `Workspace And Session Activity`, and `Privacy And Data Handling`.
- Stale-assumption risk: the Session FTS body can contain normalized non-message text. The module rereads only eligible message Events and marks lexical overlap at the Event level, so downstream code must not equate an indexed Session hit with a relevant message.
- Unverified contract claims: actual SQLite query behavior, hard-bound outputs on large synthetic data, date/time boundaries, and reference states after re-ingestion. These are required functional evidence; the gap blocks marking FEAT-0107 `passed`.

## Findings And Route

- No static contract defect or unresolved ownership question found.
- Result `PASS` applies to the inspected contract shape only; evidence coverage is partial and does not grant feature acceptance.
- Next route: functional evaluation of the synthetic cases in SPEC-0107, followed by post-contract regression review.

## Continuity Notes

- `2026-09-27`: first static contract review recorded without private Session content or behavioral test execution.
