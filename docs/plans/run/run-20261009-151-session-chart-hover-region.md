# RUN-151: Session Chart Hover Region

## Metadata

- ID: `run-20261009-151`
- Status: `passed`
- Attempt: `1`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R11](../spec/spec-0114-r11-session-chart-hover-region.md)
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-09`

## Direction And Ownership

Owner requests continuity when moving from a Session node into its temporary
description. Primary performs orchestration, spec, implementation and evaluators
sequentially using screen-alignment `extend`. R10's pointer-inert card and immediate
node exit are replaced within the existing Chart; producers and work scopes remain.

## Progress

- Source and ordinary-page review show immediate node-exit dismissal and
  `pointer-events: none` on the temporary card.
- Approved R11 defines node/card/passage hover ownership, native exit grace and
  pointer/focus reading without pinning or canvas input interception.
- The hover controller now checks node/card bounds and the convex facing-edge
  passage. One native 120ms exit timer is cancelled on reentry and all transient
  cancellation paths. No input overlay intercepts the gap.
- Temporary cards support pointer/focus reading and local scrolling. Mouse text
  clicks do not hold selection or retain it after pointer exit; Escape releases
  keyboard reading. New metadata resets local scroll, while active-item return
  keeps it. Original held actions remain separate.
- Ordinary runtime loads JS `-19` and CSS `-15`. Left/right passages at 1440px and
  narrow above passage at 320px remain open through rest/card entry/return. Native
  local PageDown scrolling, keyboard/Escape, blank and held/repeat release pass
  scoped review. Drag produces no held selection or residual displacement.

## Review Boundary

Review node/card passage and leave, local card reading, keyboard, selection and
drag separation. Original metadata, held activity and geometry retain meaning;
broader device/producer claims require separate evidence.

## Result And Closeout

- Result: `PASS`, partial evidence coverage, attempt `1`.
- Evaluation: [EVAL-0114-R11](../evaluation/eval-0114-r11-session-chart-hover-region.md).
- Native passage witnesses and programmatic focus are distinguished from source
  review and physical-device evidence. Narrow below placement, exact timer trace,
  nonzero-scroll retargeting on the final build, touch/wheel/stress and unchanged
  producers retain partial or inherited evidence; their non-blocking impact is
  recorded. R7 physical wheel review remains open. No behavior tests or scripted
  regression suite are added or run.
- README, product/architecture, design owners and planning routing are updated.
  Syntax, whitespace and privacy checks pass; planning-catalog generation/check
  completes document closeout. Final ordinary-page console contains no warning/
  error, and refreshed 1440px Chart has closed descriptions and no review marker.
- Exact task-owned source snapshots and passage witnesses are removed. No new
  process, exported screenshot, external write, staging, commit or backend restart
  is retained or required. Ordinary app and browser remain available.
