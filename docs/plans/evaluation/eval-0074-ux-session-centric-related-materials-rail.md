# EVAL-0074: Session-Centric Related Materials Rail — UX Heuristic

## Metadata

- ID: `eval-0074-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS`
- Run ID: `run-20260803-84`
- Attempt: `1`
- Feature: [feat-0074-session-centric-related-materials-rail](../feature/feat-0074-session-centric-related-materials-rail.md)
- Spec: [spec-0074-session-centric-related-materials-rail](../spec/spec-0074-session-centric-related-materials-rail.md)
- Execution Profile: `fullstack-product`
- Surface Lane: relationship comprehension, destination affordance, and disclosure continuity
- Evidence Coverage: `complete`
- Created: `2026-08-03`

## Checks And Evidence

- The rail answers two user questions in order: what this Session itself
  referenced, then what the user explicitly organized with the same work. Ambient
  path similarity no longer competes with those stronger facts.
- `MCP 조회`, `MCP 조회 실패`, visible-message mention, and tool-result evidence
  describe the Session's observation rather than a shared Resource title or
  implied freshness. Failure and unavailability remain textually explicit.
- Only real destinations receive link affordance. Safe external targets open in a
  new context; inactive unsafe/missing rows do not advertise click behavior.
- Each group discloses its own retained remainder. The native summary reads
  `N개 더 보기` while closed and `접기` while open, preserves focus on collapse,
  and does not change the peer group.
- Keyboard focus uses the existing visible focus ring. DOM, focus, and visual
  order remain Session orientation → related materials → conversation when the
  rail enters flow.
- The first visual pass exposed excessive emphasis on neutral evidence labels;
  FIX-0074 reduced them to secondary text without weakening failure meaning.

## Findings

- None after FIX-0074. Exact `대화에서 보기` and Subsession roll-up remain
  explicitly deferred product scope, not heuristic defects.
- No new reusable Interaction Evaluation candidate emerged.

## Route

- Next action: `pass`; all required evaluators are complete.
