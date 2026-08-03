# EVAL-0069-R2: Session List Source Cues — Functional

## Metadata

- ID: `eval-0069-r2-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260802-76`
- Attempt: `1`
- Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Spec: [spec-0069-r2-session-list-source-cues](../spec/spec-0069-r2-session-list-source-cues.md)
- Execution Profile: `frontend-product`
- Surface Lane: Sessions rendered inventory and regressions
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Scope

- Verified positive source rendering, accessible source identity, retained recovery
  labels, and unchanged Session inventory interactions and data scope.

## Checks

- Synthetic Claude, personal Codex, and Codex Company primary rows render `CL`,
  `CX`, and `CC` respectively.
- Personal and company Codex remain distinct even though both carry
  `provider_kind = codex`.
- Ordinary cards contain no visible `session-provenance` element and retain the
  configured source name in screen-reader text.
- Pinned Session provenance and Subsession source text remain present.
- Row destinations, utility-layer isolation, pin controls, Subsession disclosure,
  source controls, pagination, source/workspace scope, and detail behavior pass
  the targeted and complete regression suites.

## Evidence

- Session inventory, contract, pin, and UI regression set: 53 passed in 0.318s.
- Full repository suite: 322 passed in 2.396s.
- Privacy check: passed for 694 candidate files.

## Evidence Gaps

- None for the behavior changed by this Run. Browser pixel and pointer evidence is
  owned by the Design and UX reports and does not change the server-rendered cue
  or link behavior evaluated here.

## Findings

- None.

## Route

- Next action: `pass`.
