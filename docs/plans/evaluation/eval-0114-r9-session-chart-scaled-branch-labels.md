# EVAL-0114-R9: Session Chart Scaled Branch Labels

## Metadata

- ID: `eval-0114-r9`
- Status: `complete`
- Evaluator Types: `contract`, `design`, `functional`, `ux-heuristic`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R9](../spec/spec-0114-r9-session-chart-scaled-branch-labels.md)
- Run: [RUN-149](../run/run-20261007-149-session-chart-scaled-branch-labels.md), attempt `1`
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Created: `2026-10-07`

## Scope And Evidence

Primary performed sequential contract, rendered design, functional and UX review
using screen-alignment `extend`. Observed the ordinary Chart before and after a
cache-bypassing reload, using its existing zoom-out, whole-fit and Project-focus
controls. Controls were activated in the page; this is rendered browser inspection,
not a physical-device run or scripted regression suite. Inspected computed font,
height, padding, label titles and heading separation, and reviewed inline rendered
views at 1440/320px. No private record names, paths, screenshots or payloads are
persisted here. No fixture, process or filesystem scratch was created.

## Contract Review

- Removed only the scale condition around branch-label creation. Existing track
  viewport culling remains. Labels retain full text/title, ellipsis, selected
  class and recorded meaning, including R8 HEAD handling.
- Branch caption font, box height and vertical padding multiply existing native
  tokens by rowScale. At reading scale, they remain 11px, 40px and 8px respectively.
  Fixed axis width/horizontal insets and existing compact overrides are unchanged.
- Project-name font scales its original 13px token by rowScale. Removing the fixed
  overview-caption override lets the existing resolved line-height measurement
  fit the heading without covering the first branch. Project paths remain omitted
  in overview. No new minimum-font or scale cutoff is introduced.
- Names follow vertical projection, so the unchanged time-only zoom handler
  keeps their size. Guide coordinates, track membership/order, observation times,
  camera, exact-member selection, pin states, data and preference producers are
  unchanged. No List body, backend/schema or existing work-surface change belongs
  to this revision; only its Chart stylesheet reference changes in sessions.html.
- The ordinary running app loads JS suffix `-14` and CSS suffix `-12`. Owner
  documents replace the old overview branch-label omission policy consistently.

## Rendered Results

- Before editing, zoom-out to rowScale 0.5 retained branch guides but created no
  branch labels. After reload at 0.5, named labels remain in the rendered axis:
  font 5.5px, box 20px and vertical padding 4px; Project names are 6.5px.
- Whole-diagram fit retains branch and Project names. Computed sizes track the
  actual fitted rowScale, including small caption sizes. The reviewed full-fit
  heading boxes do not overlap their visible branch-label boxes, and every
  nonempty branch label retains its complete title.
- At 320px, fitted names remain present without outer horizontal overflow or
  render failure. Existing Project focus returns to rowScale 1, with 11px branch
  captions, 40px branch boxes, 8px vertical padding and 13px Project names.
  Reading guides, selected pin cues and native compact axis composition remain.
- At 1440px, half-scale and whole-fit rendered views remain contained. The
  ordinary inspection viewport is restored to 1440px at closeout.

## Design And UX Review

The owner chose continuous size reduction instead of removing branch labels.
Whole-fit text can be tiny; existing visible zoom and Project/Session focus are
the reading recovery controls. Full-name titles and original metadata preserve
inspection. No new control, color, token or helper prose is introduced. Existing
canvas projection, scope and freshness evaluation rules cover this correction;
no new reusable evaluation rule is proposed.

## Evidence Gaps And Acceptance Impact

- Full-fit glyphs are not claimed to be readable at ordinary reading size; they
  are intentionally proportional to the map and recover through focus. This is
  the explicit owner-requested behavior and is non-blocking for the bounded scope.
- 700px, exhaustive intermediate scales, alternate fonts/engines and stress are
  not separately rerun. Non-blocking: wide/320px projection and reading recovery
  are observed; the unchanged responsive inset layer remains inherited evidence.
- Cmd/Ctrl wheel gestures, touch, reduced motion, detail/back, source/workspace,
  activity and preference persistence are not rerun. Their unchanged handlers
  and producers retain previous evidence, not new certification. R7 physical
  wheel-gesture review remains open.
- No behavior tests or scripted regression suite are added or run. Static checks
  establish only their own syntax/document/privacy scope.

## Static Checks

- `node --check src/localbrain/static/session-chart.js`: pass.
- `git diff --check`: pass.
- `scripts/build-plan-artifact-catalog.py build` and `check`: catalog current.
- `scripts/check-repo-privacy.sh`: pass, 1209 candidate files.
- Ordinary-page console review: no error/warning after scoped observation.

## Route And Closeout

- Route: `pass`; no open blocking finding.
- Owner review concerns labels shrinking continuously while zooming out. Existing
  work/inference boundaries retain their approvals; no new decision is required.
- No task-owned process, file, exported screenshot or temporary directory is
  retained. Ordinary app and refreshed inspection page remain available; no
  backend restart, external write, staging or commit is needed.
