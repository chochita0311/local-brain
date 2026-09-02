# EVAL-0084 UX: Project-Grouped Pinned Sessions

## Metadata

- ID: `eval-0084-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS`
- Run ID: `run-20260902-94`
- Attempt: `1`
- Feature: [FEAT-0084](../feature/feat-0084-project-grouped-pinned-sessions.md)
- Spec: [SPEC-0084](../spec/spec-0084-project-grouped-pinned-sessions.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `Pinned recall scan path and interaction continuity`
- Evidence Coverage: `complete`
- Created: `2026-09-02`

## Checks And Evidence

- The panel now answers “which Project?” once at group level and “which Session/branch/date?” per row, removing repeated workspace copy without hiding source identity or activity.
- Git-first ordering supports the owner's primary project-recall task, while alphabetical ordering makes group position predictable. Session recency remains local to the chosen Project instead of repeatedly moving whole groups.
- No sort control, disclosure, badge, or manual organization state was added. Project headings are noninteractive orientation text and each Session keeps one ordinary detail destination.
- Branch absence is presented as absence, not an empty placeholder or a false non-Git label. Git classification remains independent from branch availability.
- Existing in-place pin mutation continues to replace the whole panel while preserving document scroll, panel scroll, and focus; the mixed-version fallback prevents a transient false-empty panel during a server/template handoff.
- Wide and narrow rendered evidence preserved the approved nested-scroll release at `700px`, full pin reachability, source cues, long-text containment, and the global pin count.

## Findings

- None.

## Current Route

- Current route: `PASS`.
