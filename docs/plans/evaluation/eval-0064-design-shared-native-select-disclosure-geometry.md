# EVAL-0064: Shared Native Select Disclosure Geometry — Design

## Metadata

- ID: `eval-0064-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS`
- Run ID: `run-20260727-69`
- Attempt: `1`
- Feature: [feat-0064-shared-native-select-disclosure-geometry](../feature/feat-0064-shared-native-select-disclosure-geometry.md)
- Spec: [spec-0064-shared-native-select-disclosure-geometry](../spec/spec-0064-shared-native-select-disclosure-geometry.md)
- Execution Profile: `frontend-product`
- Surface Lane: shared select geometry
- Screen Alignment Mode: `extend`
- Evidence Coverage: `complete`
- Created: `2026-07-27`

## Checks And Evidence

- Chrome DevTools measured all 12 Search selects, 3 visible Atlassian
  discovery selects, and 7 visible Workstream-detail selects.
- Every measured control resolves to `appearance: none`, `padding-right:
  32px`, `background-position: calc(100% - 12px) 50%`, and
  `background-size: 12px 12px`.
- The same geometry remains on the disabled Atlassian connection selector and
  on a focused Workstream selector with the existing focus ring.
- At a `320px` emulated touch viewport, all three surface families retain the
  same geometry and the documents have no horizontal overflow.
- The implementation uses shared LocalBrain spacing roles and introduces no
  page-local arrow offsets.

## Evidence Gaps

- None.

## Findings

- None.

## Route

- Next action: `pass`.
