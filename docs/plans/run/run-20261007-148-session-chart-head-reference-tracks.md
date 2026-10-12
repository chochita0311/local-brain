# RUN-148: Session Chart HEAD Reference Tracks

## Metadata

- ID: `run-20261007-148`
- Status: `passed`
- Attempt: `1`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R8](../spec/spec-0114-r8-session-chart-head-reference-tracks.md)
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-07`

## Direction And Ownership

Owner approves correcting the HEAD/missing layout split and synthetic empty
baseline. Primary owns orchestration, spec, implementation, integration and
sequential contract/design/functional/UX review. Source metadata, producer,
preferences, List and existing work surfaces retain their boundaries.

## Progress

- Existing Chart treats every nonempty branch value as named, so exact HEAD
  activates branch mode without master/main and creates a zero-Session baseline.
- Original branch metadata remains valid evidence of the recorded values; the
  error is their branch-layout eligibility, not ingestion loss.
- Approved R8 Spec limits normalization to layout and defines one line for
  HEAD/missing-only folders, preserving named branches and metadata inspection.
- One shared layout resolver excludes exact HEAD in both branch-set construction
  and Session assignment. Raw metadata and all established producers are unchanged.
- The ordinary app loads JS suffix `-13`; the reported folder's original Sessions
  render one home row/straight guide, and selection retains original HEAD metadata.
  Adjacent named branches and wide/700/320px composition retain existing controls.

## Review Boundary

Review the reported folder's single line and access to its original Sessions.
Rendered observation supports that folder; source review covers other metadata
combinations without claiming broad automated or physical-device verification.

## Result And Closeout

- Result: `PASS`, partial evidence coverage, attempt `1`.
- Evaluation: [EVAL-0114-R8](../evaluation/eval-0114-r8-session-chart-head-reference-tracks.md).
- Rendered observation supports the reported mixed HEAD/missing case and metadata
  access. Other combinations receive source review; automated regression, device,
  historical Git status and unchanged interaction/persistence contracts are unclaimed.
- Syntax, whitespace, privacy and generated planning-catalog checks pass. Current
  README, product, design and planning owners are synchronized. The unused exact
  task-owned scratch directory is removed. No new process, exported screenshot,
  staging, commit, external write or backend restart is needed.
