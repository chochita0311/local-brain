# EVAL-0084 Functional: Project-Grouped Pinned Sessions

## Metadata

- ID: `eval-0084-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260902-94`
- Attempt: `1`
- Feature: [FEAT-0084](../feature/feat-0084-project-grouped-pinned-sessions.md)
- Spec: [SPEC-0084](../spec/spec-0084-project-grouped-pinned-sessions.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `Pinned read model → Sessions/Projects inventory presentation`
- Evidence Coverage: `complete`
- Created: `2026-09-02`

## Checks And Evidence

- A focused interleaved fixture proved that a newer non-Git Session does not move its group above Git Projects, labels sort case-insensitively, and noncontiguous activity rows reassemble newest-first inside their workspace group.
- Query tests prove branch and workspace Git-root projection, eligibility, idempotent pinning, deletion cascade, activity tie-breaks, and the uncapped 101-pin consumer remain intact.
- Template tests prove Project names appear once as headings, a non-empty branch replaces the old Project row, branchless Sessions render no branch node, source cues and dates remain present, and total count still reflects Sessions rather than groups.
- Sessions and Projects routes both produce the grouped panel. A pre-restart route context that lacks the new grouped projection retains the old flat pin rows instead of presenting a false empty state.
- Synthetic browser evidence rendered all eight pins and five groups at `1440`, `920`, `700`, and `320`; the non-Git group had zero branch nodes and every row retained its Session detail destination.
- Focused verification passed `65/65`; the full repository suite passed `482/482`. The only output was the pre-existing Starlette `TemplateResponse` deprecation warning.

## Findings

- None.

## Route

- Next action: `pass`.
