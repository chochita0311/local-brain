# SPEC-0112: Session Skill Use Estimate

## Metadata

- ID: `spec-0112`
- Status: `approved`
- Feature: [FEAT-0112](../feature/feat-0112-session-skill-use-estimate.md)
- Parent PRD: [PRD-0005](../prd/prd-0005-workflow-and-skill-intelligence.md)
- Run: [RUN-139](../run/run-20261003-139-session-skill-use-estimate.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: `data`, `backend`, `frontend`, `docs`
- Created: `2026-10-03`

## Later Owner Direction

On 2026-10-04 the owner rejected language-bound declarations and approved [FEAT-0113](../feature/feat-0113-skill-reference-session-count.md), counting each skill once per use/reference Session. This completed artifact retains its original evidence and boundary.

## Bounded Extraction

Extend the existing collector after normalized message deduplication. Skill identities come from the Session's native invocation/context and successful read observations; current installed skills are not historical authority. An assistant's visible message can supply `claude_skill_declaration` or `codex_skill_declaration` when a named skill and a recognized application statement occur together. Known plugin names may use an unambiguous short alias. Strip fenced code and block quotes, bound sentence matching, and reject recognized examples, hypothetical recommendations and negated usage. Support Korean use/apply/follow wording and English first-person or sentence-initial use/apply/follow forms. Start declarations count; the result remains a heuristic estimate.

Keep a declaration's native source message identity when present, otherwise use the existing deterministic normalized message event identity. Prefix declaration identity to distinguish it from tool/context evidence; include skill identity because one message can apply multiple skills. Preserve source line, time, locator and the same native/fallback request scope as load observations. Never store message text in the ledger.

## Persistence And Ranking

Add two signal values to the existing ledger through its row-preserving migration; add no columns, tables, routes or host telemetry. Preserve all prior observations and their validity. Extend only Session extraction versions, so available files backfill once and subsequent syncs are incremental without Usage price recomputation.

The ranking admits `claude_skill_tool`, `codex_skill_context` and the two declaration kinds. Read-only rows remain evidence but contribute no use. Group once per source, native Session, known request and normalized skill; unknown scopes retain event identity. Latest-use time comes only from admitted use evidence. GET remains a database projection, independent of transcript parsing and paid insight analysis.

## Visible Contract And Review

Use estimated-use language in the current Insights column. Explain automatic use, read exclusion and request deduplication briefly. Preserve its layout, controls, navigation and typography. Apply the Fullstack profile with data/backend first and frontend/docs second. Review contract preservation and actual served output; do not add or run automated tests without an owner request.

## Limits

Silent automatic application without native activation evidence or a recognized declaration can be missed. Statements can be mistaken for application, and unsupported languages/forms may be missed. These are accepted estimate limits. Activation instrumentation and external classification are excluded.

## Open Blockers

- None for the owner's clarified estimate boundary.
