# FEAT-0064: Shared Native Select Disclosure Geometry

## Metadata

- ID: `feat-0064`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0011-shared-native-select-control-geometry](../prd/prd-0011-shared-native-select-control-geometry.md)
- Created: `2026-07-27`
- Updated: `2026-07-27`

## Goal

- Give every current native select one shared disclosure inset and protected
  trailing-text space without changing native behavior.

## Acceptance Contract

- Atlassian, Workstream, and Search native selects share one indicator geometry.
- Long selected labels cannot render beneath the indicator.
- Focus, disabled, invalid, narrow, and touch states keep the same alignment.
- Keyboard, mouse, native form submission, and no-script behavior stay intact.

## Scope Boundary

- In: shared select tokens/styles, current native-select consumers, responsive
  and rendered verification.
- Out: custom menus, `details`, comboboxes, option vocabularies, and form-flow
  changes.

## Surface Lanes

- Shared primitive lane: `src/localbrain/static/styles.css`.
- Consumer lane: Atlassian, Workstream, and Search templates and rendered
  routes.

## Dependencies

- FEAT-0063 passes first so its revised Atlassian controls are included in the
  final shared adoption check.

## Pass Or Fail Checks

- Pass if computed indicator/trailing geometry is shared across every current
  native select and long labels remain protected at all supported widths.
- Fail on page-local arrow offsets, doubled indicators, semantic regression, or
  clipped selected text.

## Regression Surfaces

- Every current native `<select>` form submission and responsive layout.

## Harness Trace

- Active spec doc: [spec-0064-shared-native-select-disclosure-geometry](../spec/spec-0064-shared-native-select-disclosure-geometry.md)
- Active run: [run-20260727-69-shared-native-select-disclosure-geometry](../run/run-20260727-69-shared-native-select-disclosure-geometry.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [design](../evaluation/eval-0064-design-shared-native-select-disclosure-geometry.md), [functional](../evaluation/eval-0064-functional-shared-native-select-disclosure-geometry.md), [UX heuristic](../evaluation/eval-0064-ux-shared-native-select-disclosure-geometry.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-27`: approved for sequential execution after FEAT-0063.
- `2026-07-27`: shared inset, indicator-size, and trailing-text-reserve tokens
  plus the native-select rule and static consumer contract test are staged.
  The Feature remains `approved` and cannot enter its formal loop until
  FEAT-0063 receives required rendered Design evidence.
- `2026-07-27`: after FEAT-0063 passed, Chrome DevTools confirmed one computed
  geometry across Atlassian, Workstream, and Search at desktop and `320px`
  touch widths. Automated and rendered evaluation passed.
