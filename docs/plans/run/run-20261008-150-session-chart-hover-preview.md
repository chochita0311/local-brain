# RUN-150: Session Chart Hover Preview

## Metadata

- ID: `run-20261008-150`
- Status: `passed`
- Attempt: `1`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R10](../spec/spec-0114-r10-session-chart-hover-preview.md)
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-08`

## Direction And Ownership

Owner requests transient hover descriptions and clearer native hover feedback,
with held descriptions toggled by node/blank click. Primary owns orchestration,
spec, implementation, integration and sequential evaluator review. Existing data,
work and visibility-persistence boundaries remain.

## Progress

- Before R10, Chart had faint CSS hover and a native title; its metadata preview
  required selection, and repeated node click never cleared the selection.
- Approved R10 Spec separates hover from held selection and reuses the preview
  without new camera reservation, activity loading or pointer-stealing geometry.
- A separate transient instance of the native metadata card overlays beside the
  hovered/focused node or above/below in narrow space. It strips held actions,
  preserves overlap/pin metadata and leaves held selection/activity/layout intact.
- Activation holds the original selection; repeat aggregate/blank/close/Escape
  releases it. Wide held panes move X only when needed to keep repeat activation
  reachable. A cursor guard fixes immediate hover reopening under a stationary
  pointer after dismissal; deliberate movement resumes hover.
- Native info surface/border, focus-width border and card elevation strengthen
  hover/focus while source and pin cues retain meaning. Duplicate native title
  tooltips are removed. Ordinary reload loads JS `-16` and CSS `-14`.
- Native pointer/keyboard/drag, bounded exact-member selection, overview and
  1440/320px observation pass scoped review. The reprojection finding was corrected
  before final observation; separate transient composition avoids hover reflow.

## Review Boundary

Review transient description/color, hold and repeat/blank dismissal, original
aggregate members and stable camera. Hover is presentation state only; broader
device and unchanged producer claims require their own evidence.

## Result And Closeout

- Result: `PASS`, partial evidence coverage, attempt `1`.
- Evaluation: [EVAL-0114-R10](../evaluation/eval-0114-r10-session-chart-hover-preview.md).
- Source review preserves activity and producer boundaries; loaded activity,
  detail/back, persistence, alternate devices/engines and unchanged wheel/tension
  paths are not rerun. R7 physical wheel review remains open. No behavior tests
  or scripted regression suite are added or run.
- README, product/architecture, design owners and current planning routing are
  updated. Syntax, whitespace and privacy checks pass; the planning catalog is
  regenerated and checked as the final documentation step. Scoped ordinary-page
  console review contains no error/warning.
- Exact task-owned before-source snapshots are removed. No new process, exported
  screenshot, external write, staging, commit or backend restart is retained or
  required. The ordinary app and released-description 1440px inspection page remain.
