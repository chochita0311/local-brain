# EVAL-0074: Session-Centric Related Materials Rail — Functional

## Metadata

- ID: `eval-0074-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260803-84`
- Attempt: `1`
- Feature: [feat-0074-session-centric-related-materials-rail](../feature/feat-0074-session-centric-related-materials-rail.md)
- Spec: [spec-0074-session-centric-related-materials-rail](../spec/spec-0074-session-centric-related-materials-rail.md)
- Execution Profile: `fullstack-product`
- Surface Lane: local read model, primary route, template states, and disclosure
- Evidence Coverage: `complete`
- Created: `2026-08-03`

## Checks And Evidence

- Direct Jira success, failure-only read, tool-result observation, user mention,
  Agent mention, exact Markdown, and safe generic URL states project truthfully.
  Shared Resource titles never replace observed Session identity.
- Explicit Thread resources sort before Workstream resources. Same-workspace-only,
  disabled, unrelated, recent, malformed, and unresolved targets do not enter as
  successful related materials; bounded unavailable copy remains truthful.
- Jira and generic URL query variants deduplicate under direct evidence. A target
  shared with organization appears once and retains secondary organization text.
- Twelve direct and thirteen organization targets produce independent 10-row
  initial lists and 2/3-row disclosures. A 101-target direct set produces 100
  retained rows plus the exact observed-total partial message.
- Unsafe external and missing local targets remain present with `열 수 없음` or
  `경로 없음`. Safe external links own `noopener noreferrer external`.
- Projection failure returns HTTP 200, keeps the conversation, and shows a local
  rail error. Persisted Subsession detail has no rail, and detail projection opens
  no source or Document file.
- Headless Chrome verified both 13-item groups, independent disclosure, expanded
  and collapsed copy, focus preservation, peer-state isolation, and zero page,
  row, or long-conversation overflow at all four required widths.

## Evidence

- Focused Session related-material/reference set: 22 tests passed.
- Full repository suite: 350 tests passed.
- Rendered Chrome matrix: `1440`, `920`, `700`, and `320` passed before and after
  the bounded visual-density fix.
- Schema/data-model/audit/Mermaid/privacy/diff checks passed.

## Findings

- None after FIX-0074.

## Route

- Next action: `pass`; UX Heuristic evaluation may close the run.
