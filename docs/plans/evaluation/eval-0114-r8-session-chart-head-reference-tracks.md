# EVAL-0114-R8: Session Chart HEAD Reference Tracks

## Metadata

- ID: `eval-0114-r8`
- Status: `complete`
- Evaluator Types: `contract`, `design`, `functional`, `ux-heuristic`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R8](../spec/spec-0114-r8-session-chart-head-reference-tracks.md)
- Run: [RUN-148](../run/run-20261007-148-session-chart-head-reference-tracks.md), attempt `1`
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Created: `2026-10-07`

## Scope And Evidence

Primary performed sequential source contract, rendered design, functional and UX
review using screen-alignment `extend`. Read the existing ordinary Chart before
and after a cache-bypassing reload. Inspected track keys, projected rows, original
metadata and guide geometry for the reported folder. Activated existing Project
focus, Session selection and selection-focus controls in the page; this is browser
inspection, not native physical-device input or a scripted regression suite.
Reviewed rendered 1440/700/320px composition. No private Session titles, paths,
screenshots or source content are persisted in this report.

## Contract Review

- One layout-only resolver maps exact case-sensitive `HEAD` to null. Both the
  branch set and Session-to-track assignment use it, preventing inconsistent
  grouping. Raw `git_branch` is neither overwritten nor persisted differently.
- HEAD-only, missing-only and mixed HEAD/missing sets become one null branch,
  so the existing root mapping contains all their Sessions without extra rows.
- Named branch sets retain observed master, otherwise main as baseline, or the
  established neutral guide if neither is observed. HEAD/missing share the same
  unassigned track in mixed named-branch folders; they are not relabeled main.
  Other names, including case distinctions, are unchanged. These combinations
  were reviewed in source, not executed as synthetic fixtures.
- Folder identity, first-observation times, ordering, aggregate selection, pin
  eligibility, activity, camera bounds, preference writes and wheel controls have
  no changes. No source parser, backend, schema, Workflow Focus or Auto Work edit
  belongs to R8. The rule does not establish present or historic repository state.
- Template JS suffix `-13` loads in the ordinary app. CSS and data payload are
  unchanged. README, product, design and planning owners describe the same rule.

## Rendered Results

- Before the correction, the reported folder rendered separate HEAD/missing
  Session tracks and an empty neutral baseline. After reload, every original
  Session is accounted for on one root track and one home row; its reading view
  shows one straight guide without a branch curve or extra baseline row.
- Same-track overlap exposes the existing exact-member selector. Selecting an
  original HEAD record retains `HEAD` in the metadata preview and links to that
  same original Session detail. No original branch values or identities change.
- Adjacent named-branch folders retain their master, feature and unassigned
  rows in the reviewed view. Reading focus still reveals the corrected single
  line; no color, token, control or extra legend is introduced.
- At 700/320px the preview stays in normal flow and the chart is contained without
  outer horizontal overflow. At 1440px it uses the existing wide composition.
  The reviewed page has no console error/warning and the render fallback stays
  hidden. The ordinary inspection viewport is restored to 1440px.

## Design And UX Review

The correction removes unjustified visual branching while keeping original
metadata inspectable. Existing presentation-eligibility and scope/provenance rules
cover this failure; no new reusable evaluation rule is proposed. No new blocking
design or interaction finding was observed in the bounded review.

## Evidence Gaps And Acceptance Impact

- HEAD-only, missing-only, main-only and other mixed combinations receive source
  review, not synthetic runtime fixtures. Non-blocking for this small shared
  resolver: the reported mixed HEAD/missing case is observed in the running app
  and named-folder composition is inspected. Broad data coverage is unclaimed.
- Detail/back navigation, source/workspace variants, preference persistence,
  activity loading, reduced motion, touch, wheel gestures and stress are not rerun.
  Their unchanged producers and handlers retain prior evidence, not new runtime
  certification. R7 physical-device wheel review remains open.
- No repository behavior tests or scripted regression suite are added or run.
  Syntax and document/privacy checks support only their static scopes.

## Static Checks

- `node --check src/localbrain/static/session-chart.js`: pass.
- `git diff --check`: pass.
- `scripts/build-plan-artifact-catalog.py build` and `check`: catalog current.
- `scripts/check-repo-privacy.sh`: pass, 1206 candidate files.

## Route And Closeout

- Route: `pass`; no open blocking finding.
- Owner inspection concerns the corrected one-line grouping. Further repository
  classification or relationship inference requires its own approved boundary.
- Screenshot export to the private scratch path was unavailable under the browser
  tool's workspace restriction; inline rendered views supplied design evidence.
  No exported screenshot, fixture or new server/browser process is retained.
  The unused exact task-owned scratch directory is removed at closeout.
