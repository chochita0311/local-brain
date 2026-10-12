# SPEC-0114-R3: Project And Branch Session Chart

## Metadata

- ID: `spec-0114-r3`
- Status: `superseded`
- Run: [RUN-143](../run/run-20261006-143-project-branch-session-chart.md)
- Attempt: `1`
- Parent Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Parent PRD: [PRD-0019](../prd/prd-0019-observed-session-chart.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: `observations`, `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-06`

## Approved Direction

This Spec records the passed Project/branch increment. Owner refinement replaces
its spacing, footer and X-only camera with [SPEC-0114-R4](spec-0114-r4-filtered-session-chart-overview.md);
its observation producer and historical evaluation remain unchanged.

The owner replaces irregular scatter with a Git-like rightward tree per Project.
Recorded launch folder is authoritative for this view, with no actual-work
classification. A clarification explicitly selects saved branch names and first
Session observations; no live Git ancestry or merge scan. Use native LocalBrain
tokens and keep List, Workflow Focus and Auto Work frozen.

## Observation Contract

- Lexically normalize recorded cwd, including local `~`, dot/trailing separators;
  never resolve symlinks, merge Git roots or inspect the filesystem for history.
  Missing cwd has its own last group. Folder leaf name labels the Project;
  home is `~`. Full path remains available to distinguish equal names.
- Add folder identity/name/display-path and earliest valid retained metadata time
  to the existing full-scope metadata projection. Existing latest valid time
  stays the Session point; metadata-invalid Event fallback supplies min/max only
  from timestamp fields. No body reads, cutoff, schema or mutation.
- Rows sort case-insensitively by name and full path, missing path last. Branch
  identity is the exact stored name. Observed master wins baseline, otherwise
  observed main; neither present means neutral structural baseline. Feature
  branches sort by name. Missing branch stays explicitly unlabeled, including
  mixed folders; no missing record becomes a master Session.

## Geometry And Interaction Contract

- Project labels remain in a fixed left axis while time pans on X and projects
  pan on Y. Each Project owns a baseline and fixed branch tracks; pure non-branch
  folders own one straight line. A curve joins the structural baseline to a
  branch's first retained observation and the guide extends right. Guides are
  layout aids, never actual Git forks/merges, work duration or Session ancestry.
- Compute track homes once per identical scoped inventory. Selection, zoom,
  resize and activity read preserve track Y. First entry uses the full period and
  alphabetic top; later camera/selection can restore. Migrating old scatter state
  keeps selected Session/time/scale where valid but discards old Y.
- Compact native source circles retain 40px targets. Screen-overlapping points
  on the same track show exact counts and a native selector for every original
  Session. Only pixel crowding aggregates; no branch/project membership is
  inferred or discarded. Visible counts count Sessions, not aggregate buttons.
- Click selects a preview with recorded metadata and detail; a dense point's
  selector picks another exact Session. Activity GET and detail/back preserve
  established semantics. Empty-space drag, time/vertical controls, zoom, fit,
  selected focus and chronological keyboard navigation remain accessible.
- Keep anchored pulling small enough to stay on its track. Nearby response is
  limited to same-track screen neighbors; guide paths never move. Release returns
  exactly; cancellation/camera/resize/page hide clears capture and offsets. Reduced
  motion omits peer animation and returns immediately. Drag cannot select.
- Retain empty, unknown-time, read-error, no-script, render/storage-failure escape
  routes. Project labels/essential actions stay contained at 1440/700/320px;
  preview remains floating wide and stacked narrow. Use safe text DOM for paths,
  branch labels, titles and selectors; no private content in tracked evidence.

## Surfaces And Evaluation

Primary executes sequentially: `queries.py` projection and owner contracts,
Chart JS/CSS/template, then product/architecture/design/planning documentation.
The data consumer depends on observations. Contract review covers lexical path
identity, timestamp fallback, honest guide meaning and count/selection state;
design/functional/UX review uses real browser Project/branch/plain-row examples,
aggregation, selection/zoom/resize/reload, activity/detail return, drag and narrow
composition. Syntax/AST, whitespace, privacy and generated-catalog checks support
their specific scopes. No automated test addition/run, physical-device or stress
certification is claimed; those limits do not block this inspectable increment.

## Open Blockers

None. The owner selected first-observation branch semantics explicitly. Project
name A–Z with full-path ties is the initial deterministic order for inspection.
