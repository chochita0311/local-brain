# EVAL-0114-R7: Session Chart Wheel Controls

## Metadata

- ID: `eval-0114-r7`
- Status: `complete`
- Evaluator Types: `contract`, `design`, `functional`, `ux-heuristic`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R7](../spec/spec-0114-r7-session-chart-wheel-controls.md)
- Run: [RUN-147](../run/run-20261007-147-session-chart-wheel-controls.md), attempt `1`
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Created: `2026-10-07`

## Scope And Evidence

Primary performed sequential contract, rendered design, functional and interaction
review without delegation, using screen-alignment `extend`. A private task-owned
fixture rendered the native Chart template/CSS with 96 synthetic Sessions, eight
launch folders, three recorded branches per folder and two pins. Its local server
served a retained before-edit script and then the changed script. Separate owned
Chrome 152 processes received native browser-protocol wheel/click input; reported
wheel events were trusted and their modifier/axis values were inspected. Two
line/page cases used synthetic DOM WheelEvents and are identified below.

Thirty bounded fixture cases and seven ordinary-app cases were inspected and
their numeric invariants checked. Wide/700/320px geometry and wide/320px rendered
screenshots were reviewed. The ordinary running application loaded JS asset
suffix `-12`, exercised both input forms and native List/Chart return, and retained
camera state. Its owner inspection page was refreshed to the new binding.
This establishes browser-level behavior, not physical mouse/trackpad or OS input
conversion. Review-harness setup corrections were rerun; only final inspected
event flags and rendered-target runs support the findings. No private runtime
content or screenshots are included in this document.

## Contract Review

- Shift-wheel now uses deltaX or deltaY rather than discarding horizontal input.
  The larger absolute component supplies signed movement; equal magnitudes use
  deltaY, and components are never added. Existing pixel/line/page normalization
  remains. Plain wheel retains separate X/Y movement and document ownership when
  the Chart cannot move. Modifier zoom keeps the existing curve and bounds.
- Cmd/Ctrl-wheel, plus/minus buttons and keyboard plus/minus retain whole-chart
  zoom. Cmd/Ctrl+Shift-wheel changes time scale only, preserving rowScale, vertical
  camera, target projection, selection and preview mode. The existing renderer
  refreshes aggregate selection after changed X spacing. Pointer time remains
  anchored unless existing visible-time bounds clamp it.
- Only the time-fitted resize branch changes its Y behavior: it no longer resets
  an independently scrolled Project axis. Initial unsaved positioning and explicit
  whole-diagram fit still reset as specified; tab X/Y serialization is unchanged.
- R6 visible-time bounds, projected targets/insets, selected-activity extents,
  maximum scale and drag-only spring behavior remain the shared owners. Backend,
  schema, observations, DB visibility, pins, Workflow Focus and Auto Work have no
  R7 edits. Preference/relationship writes were not exercised by these input checks.
- Template JS suffix `-12` loads on the active app and again after native display
  navigation. Existing CSS and data producers remain compatible. README, product,
  design and current planning owners describe the same shortcut contract.

## Functional Results

- Before editing, native Shift `(deltaX=80, deltaY=0)` produced no movement; native
  `(0,80)` moved 80px. This reproduces one compatibility failure path, not the
  exact physical-device cause reported by the owner.
- After editing, either form moves approximately 80px, and either negative form
  moves -80px, with unchanged Y scale/camera. Diagonal `(20,80)` and `(80,20)` each
  move 80px once. Synthetic line `(0,5,mode=1)` moves 80px; synthetic page
  `(1,0,mode=2)` moves the 498px fixture plot height.
- Cmd+Shift down/up changes X by approximately 0.4493/2.2255 for 80-unit input,
  accepts horizontal deltas and preserves Y at reading and overview scales.
  Ctrl+Shift receives the same horizontal behavior. Unclamped modifier examples
  preserve pointer time within 0.001ms floating-point tolerance.
- A reading-scale vertical camera at 180px remains 180px during time-only fit,
  fresh-document reload and a 1440-to-700px resize. Explicit whole fit resets Y to
  zero and projects all eight folders into the fixture canvas.
- Right/left endpoint wheel input and whole-time-fit horizontal movement remain
  bounded, with no movement or consumed wheel when no pan is possible. X zoom
  stops at the current fit minimum and 0.01 maximum, preserving Y. Existing Cmd
  whole zoom still changes vertical projection.
- Native reading selection retains the same exact synthetic Session and visible
  preview after time-only zoom. At 700/320px, modifier zoom preserves fitted Y
  geometry and produces no outer horizontal overflow. Reviewed native controls,
  Project labels, guides and pin cues retain their family and compact overview.
- Ordinary app input checks reproduce both Shift forms and time-only zoom with
  stable Y. Native List/Chart navigation keeps independent scale/camera state and
  loads the changed script; List rows remain present. Final runs have no browser
  exceptions. The owner's ordinary inspection page loads the new version.

## Design And UX Review

No new colors, geometry tokens, visible instructions or navigation controls are
introduced. Whole-chart controls remain the discoverable overview baseline;
the requested time-only gesture supplements them and is documented as application
behavior. No new blocking consistency or interaction issue was found. No new
reusable evaluation rule is proposed; existing canvas input/freshness/continuity
checks cover this revision.

## Evidence Gaps And Acceptance Impact

- Physical mouse/trackpad, OS Shift-axis conversion, natural-scroll preferences
  and another browser engine remain unverified. Non-blocking under R7's explicit
  controlled-browser scope; owner review on their device remains due. The exact
  original device cause is not certified.
- Source/workspace variants, loaded activity extremes, long-session stress,
  touch and reduced-motion OS settings were not rerun. Non-blocking: their shared
  producer/bounds/spring contracts are unchanged and broader prior evidence is
  retained, not reclassified as new runtime verification.
- No repository behavior-test suite was added or run. Scoped scripted browser
  input checks and numeric assertions support only the recorded cases. Syntax,
  whitespace, privacy and generated planning-catalog checks support their scopes.

## Static Checks

- `node --check src/localbrain/static/session-chart.js`: pass.
- `git diff --check`: pass.
- `scripts/build-plan-artifact-catalog.py build` and `check`: catalog current.
- `scripts/check-repo-privacy.sh`: pass, 1203 candidate files.

## Route And Closeout

- Route: `pass`; no open blocking finding.
- Review the two wheel gestures on the owner's device; whole-time fit naturally
  has no horizontal pan distance. Further interaction/inference work requires its
  own approved boundary.
- Task-owned browser processes/server, fixture, screenshots, profiles and review
  output are removed at closeout. The ordinary app and refreshed inspection page
  remain available. No commit, staging, external write or backend restart is required.
