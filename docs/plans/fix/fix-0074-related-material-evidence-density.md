# FIX-0074: Related Material Evidence Density

## Metadata

- ID: `fix-0074`
- Status: `complete`
- Run ID: `run-20260803-84`
- Attempt: `1`
- Feature: [feat-0074-session-centric-related-materials-rail](../feature/feat-0074-session-centric-related-materials-rail.md)
- Spec: [spec-0074-session-centric-related-materials-rail](../spec/spec-0074-session-centric-related-materials-rail.md)
- Finding Type: `implementation bug`
- Created: `2026-08-03`

## Finding

- Synthetic rendered evaluation showed ordinary mention evidence as repeated
  brand-colored pills. The labels were truthful, but the repeated emphasis kept
  the visual noise that FEAT-0074 was intended to remove and made neutral
  mentions read too close to status alerts.

## Bounded Fix

- Kept every approved evidence label and count unchanged.
- Replaced ordinary evidence pills with compact secondary inline text separated
  by a quiet divider.
- Retained explicit danger-colored text only for `MCP 조회 실패`; state remains
  readable without depending on color.
- Changed no group, ordering, count, destination, disclosure, persistence,
  extraction, or synchronization behavior.

## Re-Evaluation

- Headless Chrome checks passed again at `1440`, `920`, `700`, and `320` with no
  document, related-item, or long-conversation overflow.
- Both groups still show 10 initial rows and 3 retained rows behind independent
  disclosures in the synthetic 13-plus-13 fixture.
- Expand/collapse copy changes between `3개 더 보기` and `접기`; focus remains on
  the owning `summary` and the peer disclosure remains closed.
- Full repository suite and privacy/contract checks passed after the fix.

## Route

- Return to Design, Functional, and UX Heuristic evaluation.
