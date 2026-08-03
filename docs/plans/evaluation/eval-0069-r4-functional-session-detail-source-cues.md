# EVAL-0069-R4: Session Detail Source Cues — Functional

## Metadata

- ID: `eval-0069-r4-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260802-78`
- Attempt: `1`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Spec: [spec-0069-r4-session-detail-source-cues](../spec/spec-0069-r4-session-detail-source-cues.md)
- Execution Profile: `frontend-product`
- Surface Lane: Session and Subsession route rendering
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Checks

- A Codex Company primary Session renders `CC` in its detail heading.
- Its company Subsession renders `CC` in the parent detail row and in its own
  normalized detail heading even though both records use the Codex adapter.
- Personal Codex remains `CX`; list and Pinned source cues still share the same
  macro, configured labels remain available, and no data is mutated.
- Detail conversation, parent/child, source-scope, direct-link, pin, ingestion,
  Usage, and full repository regressions pass.

## Evidence

- Targeted route/detail/UI set: 51 tests passed.
- Full repository suite: 323 tests passed.
- Privacy and diff checks passed.

## Findings

- None.

## Route

- Next action: `pass`.
