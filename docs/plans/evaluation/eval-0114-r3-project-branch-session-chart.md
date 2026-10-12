# EVAL-0114-R3: Project And Branch Session Chart

## Metadata

- ID: `eval-0114-r3`
- Status: `complete`
- Evaluator Types: `contract`, `design`, `functional`, `ux-heuristic`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R3](../spec/spec-0114-r3-project-branch-session-chart.md)
- Run: [RUN-143](../run/run-20261006-143-project-branch-session-chart.md), attempt `1`
- Execution Profile: `fullstack-product`
- Surface Lanes: `observations`, `frontend`, `docs`
- Created: `2026-10-06`

## Scope And Evidence

The primary performed sequential contract, rendered design, functional and UX
review of the owner-approved replacement for irregular scatter. Recorded launch
folders define Projects; saved branch names and first retained observations define
rightward layout guides. Screen-alignment adapt uses native LocalBrain tokens,
source cues, shell and controls. No actual Git history or work inference is added.

Review used a task-owned local preview server with startup disabled, separate
browser pages, real mouse/key gestures and temporary numeric DOM instrumentation.
An in-memory synthetic browser inventory supplies eleven fictional records for
same-name folders, master/feature/missing branches, a feature-only folder, plain
folders, home, missing cwd, unknown time and dense mixed-source points. This
fixture exercises the client layout and selection, not backend projection edge
cases. Actual local GET/render evidence covers the additive projection and native
source scope without retaining private contents, paths, counts, IDs or captures.

## Contract Findings

- `session_chart_inventory` remains a primary-work-only, full-scope SELECT with
  existing source/workspace predicates and no body, schema or database mutation.
  Additive fields supply lexical folder identity/name/display path and earliest
  observation. Existing latest valid observation remains the Session point.
- Source review confirms `~` expansion, dot/trailing-separator normalization and
  preservation of separate launch folders without symlink, repository-root or
  Git-history inspection. Earliest/latest valid metadata times are used; only
  absence of all valid metadata times invokes retained Event timestamp fallback.
  The new earliest-time fallback receives source review, not a new backend
  fixture execution. Earlier fallback/eligibility evidence belongs to
  [EVAL-0114](eval-0114-observed-session-chart.md).
- Project rows sort case-insensitively by folder leaf name, then full path, with
  missing cwd last. Full paths distinguish equal labels. Exact stored branch
  names own fixed tracks: observed master wins, otherwise main; neither observed
  means a neutral structural baseline. Pure missing-branch folders use one line;
  mixed folders retain a separate missing-branch track. No Session becomes a
  fabricated master/main record or an inferred work Project.
- Branch curves terminate at their first retained observation and extend right as
  layout guides. The visible legend/help and owner documents distinguish them
  from actual Git forks, merges, duration and Session ancestry. No relationship
  or position is persisted to SQLite.
- Dense same-track points aggregate only by current pixel crowding. Each host
  retains a real latest point's X; adjacent hosts stay at least 40px apart. Exact
  original IDs populate the selector, and visible counts count Sessions rather
  than host buttons. Mixed sources receive a neutral cue rather than one source's
  color. Selection stores the original member ID even when its host differs.
- Home Y is computed once per scoped inventory. Version-three navigation state
  stores time center, scale, camera Y, selection and List page. Source review
  confirms migration retains valid time/scale/selection and discards old scatter
  Y. Current version reload/detail return is directly observed.

## Rendered Design, Functional And UX Findings

- Full-width Chart omits Pinned Sessions and shows a fixed Project axis with
  separate branch labels, native guide lines and compact source circles. Real
  and synthetic layouts show plain, baseline, feature-only and mixed cases;
  synthetic same-name folders stay separate and missing cwd sorts last. Unknown
  time retains its disclosed detail links.
- Every point retains a 40px target. Review found that an expanded selected title
  could cover neighboring targets; the bounded correction moves every caption
  outside its target with pointer events disabled. Final selected and unselected
  target widths are measured at 40px, including dense synthetic selection.
- Dense-point click opens a preview and selector. Choosing an earlier member
  changes the original selection, matching detail destination and pressed host
  membership. Synthetic mixed-source count and selector contain all three
  original records. Actual selected activity retrieval displays retained points
  on its branch track; the activity API remains unchanged.
- Real point dragging displaces the point and only same-track neighbors, with
  vertical resistance below the 8px bound. Guide paths stay fixed. Release
  restores every transform exactly, clears dragging and opens no preview.
  Cancellation, page-hide and reduced-motion ownership remain the reviewed
  handlers from [EVAL-0114-R2](eval-0114-r2-stable-session-constellation.md).
- Real empty-space drag changes the time camera while leaving homes, vertical
  camera and point offsets unchanged. Zoom preserves inspected track homes.
  Vertical controls preserve time center and scale. Native End selects the latest
  exact Session and focuses its track.
- Ordinary detail and its Sessions Chart backlink restore selection, time center,
  scale, camera Y and inspected homes exactly. One host remains pressed and
  contains the restored original selection. Detail's Workflow link retains its
  existing route.
- Effective 1440, 700 and 320px viewports have no outer horizontal overflow and
  keep essential controls inside the viewport. At 700/320px the 96px Project axis
  reserves space for time and the preview follows the canvas. Final assets retain
  40px targets and contained detail/selection actions after the caption correction.
  Mobile viewport emulation does not certify physical touch gestures.
- All-source and Codex Company GET/render preserve source scope and expose the
  new metadata fields. Default List retains its rows, pagination and Pinned
  Sessions, without loading the Chart script. Workflow Focus and Auto Work
  implementation files remain outside this revision. Reviewed application pages
  have no console warnings or errors.
- The ordinary local server was restarted after confirming no queued/running
  Maintenance or Insights work. Its refreshed Chart loads the new projection and
  revision-five assets, native guide layout and full-width composition.

## Evidence Limits And Owner Review

Automated regression suites, physical-device gestures, actual OS motion-setting
changes and large-corpus stress were not run. Reduced-motion behavior retains
the prior controlled media-query branch evidence and current source review; it is
not a fresh OS setting certification. The new lexical path and earliest-time
fallback rules are reviewed in source; the synthetic browser inventory does not
execute those backend rules. Prior empty/read-error/no-script/render/storage
recovery evidence remains in EVAL-0114 with current fallback source review.

These limits do not block the Spec's inspectable local increment. The next human
review concerns Project name order, branch structure and dense-point composition.
It does not authorize actual Git ancestry, work classification, inference or a
resumption of Auto Work.

## Checks And Closeout

JavaScript syntax, Python AST parsing, whitespace and repository privacy checks
pass within their respective scopes. The planning catalog is regenerated and
checked at closeout. No automated test result is claimed.

Task review pages, injected fixtures/instrumentation and the preview server are
removed. No task filesystem scratch was created. The ordinary local application
remains available for owner inspection.

`pass` for the approved Project/branch revision with partial evidence coverage.
