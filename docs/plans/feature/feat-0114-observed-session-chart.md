# FEAT-0114: Observed Session Chart

## Metadata

- ID: `feat-0114`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `frontend-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0019](../prd/prd-0019-observed-session-chart.md)
- Created: `2026-10-06`
- Updated: `2026-10-12`

## Owner Boundary And Goal

The owner requested PRD creation and continued execution of the already clarified boundary. Deliver one inference-free Chart inside Sessions while preserving the existing List and Session Workflow Focus. No separate review or classification queue is required before seeing the first screen.

## Acceptance Contract

1. `List/Chart` replaces the redundant inventory heading/copy with two segments and no separator. The shared source header uses `All` and the Dashboard's adjacent-unselected separator rule. Default List, rows, ordering, pagination, source scopes, pins and child disclosures retain their behavior.
2. Chart fills the main content width with no Pinned Sessions column. Its source/workspace denominator matches List across all pages and ages.
3. A Session point uses valid observed time on X and an exact recorded-folder Project row on Y. Rows sort case-insensitively by folder name, full path for ties, missing path last. Exact `HEAD` is a checkout reference, excluded from branch names only in layout. Folders with only HEAD/missing values use one line with no empty baseline. Named branches form stable subtracks with observed master/main as baseline, or a neutral baseline when named branches exist but neither is observed. HEAD/missing records in mixed named-branch folders share one unassigned track and are never relabeled master/main. Original metadata remains visible and unchanged. Guides begin at first retained metadata observation, using retained Event timestamps only when no valid metadata time exists, and never claim Git ancestry, merge, duration or work identity. Unknown times remain accessible.
4. Selecting a Session exposes its original metadata and exact retained activity timestamps without Event text or opaque payloads. Gaps, counts and closure are not inferred.
5. A checkbox Project filter in the Chart toolbar's left position controls local visibility and closes hidden-row gaps, without changing List or recorded membership. Confirmed visibility persists in the private LocalBrain DB per source/workspace, restores across browsers using that DB and survives browser site-data removal; tab camera/selection/vertical scale remains separate. DB state, including all-selected, overrides browser state. Valid browser choices migrate only into an absent DB setting, and failure exposes contextual retry while retaining in-memory use. Absent hidden-folder keys remain retained. Date range and directional toolbar buttons are omitted while axis dates, drag and keys remain. Footer counts/legend/help are removed. Reading tracks use compact spacing and 40px targets; ordinary zoom also compresses vertical geometry to fit all selected Projects and time in one overview. Cmd/Ctrl+Shift-wheel changes time spacing alone while preserving vertical state; Shift-wheel pans from either input axis within the visible time bounds. Choosing an overview Project/Session restores reading scale. Dense points retain exact-count selection. Existing pins use a static native halo/icon, with any-pinned aggregate marking and exact-member selector/preview status; no pin mutation is introduced. Time bounds include only visible observations and selected visible activity. Filter changes follow an endpoint camera, refit whole-time fit or preserve a bounded middle time anchor. Centered targets have balanced 64px end insets, capped for narrow usable space, with at most 80px blank-drag extension capped at half usable width and spring return; reduced motion returns immediately. The existing reading-scale cap may underfill a short period. Point pulling remains same-track and transient. Detail return retains Chart/scope/camera/selection/Project visibility/vertical scale; stale state recovers honestly.
6. Empty, unknown-time, activity-error, no-script and render-failure states retain List/detail access. Desktop, compact and 320px have no outer overflow or hidden essential actions.
7. Existing `/sessions/{id}/workflow`, its implementation files, correction semantics and Auto Work remain outside this feature.
8. Branch labels remain present as the Chart zooms out and scale with row geometry. Project-name typography scales too so its heading does not cover compressed branches. Reading tokens, fixed axis width/insets, full-name titles, selected meaning and existing focus are preserved. Whole-fit text may be tiny; no label cutoff is introduced. Time-only zoom keeps label size. Session-caption/path/held-preview compaction retains its existing policy.
9. Hover/keyboard focus shows original metadata temporarily and uses stronger native information-surface/border feedback. Node, card and facing-edge passage share hover ownership; leaving both pointer and keyboard focus closes it after native 120ms grace, with reentry cancellation. Temporary cards support text reading/selection, local scrolling and keyboard focus without narrow reflow or selection actions. Mouse text clicks do not hold selection; new descriptions start at the top. The passage has no invisible hit overlay, so blank click/drag remain available, including clearing temporary-only hover. Node activation holds selection with exact-member/activity/detail access; same aggregate, blank canvas, close or Escape releases it. Other hover adds an independent transient card while held selection/activity stay in place. Hover changes no projection, fetch or persisted state and stays at reading size in overview. Cancellation clears hover and pending exits. Held wide panes shift time only when needed to keep repeat activation reachable. Stationary-pointer reprojection after release does not reopen another card. Actual pointer movement resumes hover, and drag remains distinct from activation. Source/pin/metadata contracts remain.

## Scope Boundary

The owner requests R11 continuity from Session node to temporary description.
Node/card/passage share hover ownership, with native exit grace and readable,
focusable card input. This replaces R10's immediate exit and pointer-inert card.
Held selection, metadata, activity, projection, persistence and producer boundaries
remain; temporary input does not add selection actions or invisible hit overlays.

- In: the bounded inventory Chart, additive read-only activity projection, one scoped visibility preference table and bounded local save API, view continuity and owner documentation.
- Out: inference, model work, source parsing/Sync or Git-history reads on browse, other schema changes, persisted work classification, Workflow Focus/Auto Work changes, decorative reference styling.

## Surface Lanes

The current R11 revision uses `frontend` and `docs` under `frontend-product`.
The established observation, pin and R6 database-preference producers are frozen.
The data/backend lanes below describe established R6 ownership, not new R11 work.

- `data`: one dedicated Chart preference table; Data Model owner and generated
  schema presentation stay synchronized. No observation or organization DDL changes.
- `backend`: scoped GET preference and bounded same-origin PUT with commit-before-
  acknowledgment, migration precedence and explicit errors; no ingestion/pin writes.

- `observations`: `queries.py`; additive lexical folder identity/name/label and first observed time from retained metadata. Primary implements before the consumer; contract and functional review. No filesystem Git lookup, body read or mutation.
- `frontend`: Chart assets/template; project A–Z axis, recorded branch guides, native point/count selection, bounded track feedback and existing navigation/fallback/return. Depends on observations and the R6 preference producer; primary owns sequential contract, design, functional and UX review. R11 joins node/card hover ownership and supports temporary reading input while preserving held selection, drag/pan, metadata and exact-member access.
- `docs`: product, architecture, design owners and current planning routing; no private content or unrelated track change.

The first and third Runs used `fullstack-product`; the second, fourth and fifth owner-approved Runs use `frontend-product`, with `frontend` and `docs` lanes. R5 projects already-loaded all-pin identities in the template; the observation producer is unchanged. R6 explicitly expands only the visibility persistence contract and camera space. R7 returns to frontend/docs for bounded wheel input and independent time zoom; those established producers remain frozen.
R8 retains frontend/docs for the HEAD display correction only.
R9 retains frontend/docs for branch-label continuity through zoom-out.
R10 retains frontend/docs for hover and held-description interaction.
R11 retains frontend/docs for continuous node/card hover ownership and reading.

## Contract Surfaces

- Existing `/sessions` default and source/workspace/page behavior.
- Additive `display=list|chart` view state and a primary-work-only activity GET; no mutation or body content.
- Existing normalized source cues, Session identities, timestamps and safe local destinations.
- Dedicated `session_chart_preferences` scoped user intent and `PUT /sessions/chart/project-visibility`; bounded payload, DB precedence, create-if-absent migration and truthful failure/retry.

## Entry, Exit And States

Entry is Sessions' local List/Chart switch. Hover/focus gives a temporary description maintained across node/card/passage; leaving pointer and keyboard focus closes it after grace. Node activation holds a small preview whose detail link opens the ordinary Session. Same-node/blank/close/Escape releases it. The Chart backlink and browser Back restore scope-specific state. Empty/unknown-time/error states disclose their actual meaning and link to existing List; invalid/stale selection does not invent replacement activity.

## Dependencies And Regression Surfaces

Existing inventory/source contracts, pins, Session detail and design constitution. No unpassed foundation or Auto Work dependency. Regressions cover List pagination, source/workspace filters, sync view preservation, Projects navigation and untouched Workflow Focus.

## Pass Or Fail Checks

- Read projections match inventory totals beyond one List page and preserve source/workspace exclusions.
- Activity GET returns ordered valid timestamps and honest undated counts, rejects non-primary/non-work/missing Sessions, and does not return bodies or write SQLite.
- Browser evidence covers full width without the recall column, stable selection, navigation/zoom, activity rendering and detail/back at desktop and 320px.
- Empty/unknown-time/error/no-script recovery remains usable; browser errors and outer overflow are absent.
- Changed file review confirms Workflow Focus and Auto Work files are untouched.

## Harness Trace

- Current Spec: [SPEC-0114-R11](../spec/spec-0114-r11-session-chart-hover-region.md)
- Current Run: [RUN-151](../run/run-20261009-151-session-chart-hover-region.md)
- Current Evaluation: [EVAL-0114-R11](../evaluation/eval-0114-r11-session-chart-hover-region.md), `PASS`, partial evidence coverage.
- Previous hover revision: [RUN-150](../run/run-20261008-150-session-chart-hover-preview.md), [EVAL-0114-R10](../evaluation/eval-0114-r10-session-chart-hover-preview.md), `PASS`, partial evidence coverage.
- Previous label revision: [RUN-149](../run/run-20261007-149-session-chart-scaled-branch-labels.md), [EVAL-0114-R9](../evaluation/eval-0114-r9-session-chart-scaled-branch-labels.md), `PASS`, partial evidence coverage.
- Previous HEAD revision: [RUN-148](../run/run-20261007-148-session-chart-head-reference-tracks.md), [EVAL-0114-R8](../evaluation/eval-0114-r8-session-chart-head-reference-tracks.md), `PASS`, partial evidence coverage.
- Previous wheel revision: [RUN-147](../run/run-20261007-147-session-chart-wheel-controls.md), [EVAL-0114-R7](../evaluation/eval-0114-r7-session-chart-wheel-controls.md), `PASS`, partial evidence coverage.
- Previous persistence/space revision: [RUN-146](../run/run-20261007-146-local-chart-preferences-and-pan-space.md), [EVAL-0114-R6](../evaluation/eval-0114-r6-local-chart-preferences-and-pan-space.md), `PASS`, partial evidence coverage.
- Previous toolbar/pin revision: [RUN-145](../run/run-20261007-145-session-chart-controls-and-pins.md), [EVAL-0114-R5](../evaluation/eval-0114-r5-session-chart-controls-and-pins.md), `PASS`, partial evidence coverage.
- Previous filtering/overview revision: [RUN-144](../run/run-20261006-144-filtered-session-chart-overview.md), [EVAL-0114-R4](../evaluation/eval-0114-r4-filtered-session-chart-overview.md), `PASS`, partial evidence coverage.
- Previous Project/branch revision: [RUN-143](../run/run-20261006-143-project-branch-session-chart.md), [EVAL-0114-R3](../evaluation/eval-0114-r3-project-branch-session-chart.md), `PASS`, partial evidence coverage.
- Previous revision: [RUN-142](../run/run-20261006-142-stable-session-constellation.md), [EVAL-0114-R2](../evaluation/eval-0114-r2-stable-session-constellation.md), `PASS`, partial evidence coverage.
- First increment: [RUN-141](../run/run-20261006-141-observed-session-chart.md), [EVAL-0114](../evaluation/eval-0114-observed-session-chart.md), `PASS WITH SUGGESTIONS`, partial evidence coverage.

## Continuity Notes

- `2026-10-12`: Owner says the delivered Chart can wrap up the first phase. The initial review compared eleven completed evaluation records with the shared design/interaction owners and proposed four additional topics and three refinements; that review itself did not authorize a shared-package change. The owner then explicitly requested subagent implementation, shaping of both policies, whole-repository documentation review, verification and commit/push. The seven criteria were adopted in ai-assets [commit 3dfcc36](https://github.com/chochita0311/ai-assets/commit/3dfcc36bd91e6f2c2461fe91d8f387dfca2ca17b); the requested LocalBrain documentation review and verification are complete. The first-phase implementation remains passed with recorded partial evidence; physical wheel coverage and other unobserved environments retain their limits. Further product changes require a new boundary.

- `2026-10-12`: Closeout covers all 960 repository documents, preserving historical results and approval boundaries while correcting owner references, current producer predicates and dated handoffs. The 1,076-test Python suite passes, including 13 added metadata/preference tests; the existing seven Workflow-map tests, Mermaid asset contracts, schema/data-model generators, catalog, local links, syntax and privacy checks pass. The supervisor load smoke test now uses a fresh interpreter after its forked child exited with signal 11 only in the aggregate runner; production limits and behavior are unchanged. Synthetic browser checks at 1440px and 320px confirm all eight Projects and 48 Session identities in whole fit, scaled branch labels, one HEAD/missing-only line, aggregate/member pin status, independent held/hover state, repeat/blank/Escape release, right and below card passages, above-card placement, local PageDown scrolling and reset to zero for new metadata. Project choices survive reload and a controlled synthetic app-process restart. This evidence does not certify a browser-process restart, physical wheel input, every device or stress conditions; the eleven original evaluation records retain their partial coverage.

- `2026-10-09`: R11 is available on the ordinary app with JS `-19` and CSS `-15`. Node/card/passages retain metadata through pointer reading; 1440px left/right and 320px above-passage observation, mouse-card/blank release, keyboard/Escape, local PageDown scrolling and held/repeat selection pass scoped review. Temporary reading does not change projection or held state. Final source resets new metadata scroll and clears pending exit callbacks; broader device, below-placement and producer evidence remains partial. Owner review concerns node-to-card continuity, and R7 physical wheel review stays open. Task-owned review state is removed; no new process/backend restart is required.

- `2026-10-09`: Owner reports temporary description closing when moving into it and requests a maintained hover region. Reopened for R11 frontend/docs: node/card/passage ownership replaces immediate exit, and the temporary card supports pointer/focus reading with no held-selection or producer change. No external/data/work write is authorized.

- `2026-10-08`: R10 is available on the ordinary app with JS `-16` and CSS `-14`. Native pointer/keyboard/drag and bounded aggregate-member observation confirm temporary metadata, held selection, repeat/blank/close/Escape release and hover recovery after stationary-pointer reprojection. Overview and 1440/320px composition preserve target visibility and narrow held-pane flow. Other hover does not replace the held Session; loaded-activity preservation is source-reviewed rather than rerun. Static checks pass, no task-owned review debris remains, and no new process/backend restart is required. Owner screen review concerns hover emphasis and hold/release; R7 physical wheel review remains open.

- `2026-10-08`: Owner requests transient Session hover descriptions and stronger hover color, with click holding the description and repeat/blank click releasing it. Reopened for R10 frontend/docs. Hover must not reserve new camera space, fetch activity, persist state or replace held selection; native preview metadata rendering is shared and exact-member access remains. No producer or work-surface change is authorized.

- `2026-10-07`: R9 is available on the ordinary app with JS suffix `-14` and CSS suffix `-12`. Half-scale and whole-fit retain proportional branch/Project names; scaled heading measurement keeps room for the first branch. 1440/320px rendered observation and Project focus back to native reading typography pass scoped review. Tiny fit text is intentional; broad scale/device/input/persistence evidence is not claimed. No review debris remains. Next owner review is label continuity during zoom-out; R7 device review remains open.

- `2026-10-07`: Owner requests retaining branches during zoom-out by scaling them. The rendered old Chart keeps guides but drops every branch label below a five-sixths vertical scale. Reopened for R9 frontend/docs to remove that cutoff and scale axis typography/branch geometry; Project names must not occlude the compressed labels. Data and frozen work boundaries remain.

- `2026-10-07`: R8 is available on the ordinary app with JS suffix `-13`. The reported folder's original Sessions occupy one root/home row and straight guide, with raw HEAD still shown in original metadata and exact-member selection. Wide/700/320px rendered inspection is contained. Other branch combinations receive source review, not fixture or broad regression certification. Existing work and producer boundaries remain. Next owner review is the corrected one-line grouping; R7 device review stays open.

- `2026-10-07`: Owner approves correcting the synthetic empty baseline and HEAD/missing split. Reopened for R8 frontend/docs. Exact HEAD is excluded only from layout branch names; raw records and source parsers are unchanged. No filesystem Git lookup or work inference is introduced.

- `2026-10-07`: R7 is available on the ordinary app with suffix `-12`. Native browser input reproduces the old horizontal Shift failure and confirms both repaired input forms, independent time zoom, pointer anchoring, bounded endpoints and preserved vertical state through reload/resize. Selection, wide/narrow geometry and native List/Chart return pass scoped review. Controlled input does not certify the owner's physical-device cause. Temporary review state is removed; next owner review is the two gestures on their device.

- `2026-10-07`: Owner reports Shift-wheel does not move and explicitly approves verification plus Cmd+Shift-wheel horizontal spacing control. Reopened for R7 frontend/docs. The current handler reads only deltaY when Shift is active; the investigation must distinguish input compatibility from an already fitted or bounded time axis. No backend or work-surface mutation is authorized.

- `2026-10-07`: R6 is available on the ordinary application. Confirmed DB visibility restores across fresh contexts/origins and synthetic app restart, with migration/empty precedence, latest serialized saves and genuine retry. Visible-only date bounds, centered adaptive insets and both native resisted returns pass scoped review; 1440/700/320px and exact pinned-member detail return remain usable. Syntax/schema/privacy checks pass; automated/device/stress coverage is unclaimed. Task-owned review state is removed. Owner review now covers saved filtering, end space and tension.

- `2026-10-07`: Owner explicitly selects local DB preference persistence after the browser-site-data limit is explained, and requests contracting visible-project bounds plus wider balanced space and pan tension. Reopened for R6 data/backend/frontend/docs lanes; only a dedicated preference schema and local choice writes expand the boundary.
- `2026-10-07`: Toolbar/pin refinement is available on the ordinary application. Native filter/pin selection, fresh-document visibility, exact aggregate/member pin truth, controlled migration/storage denial, List/source/detail continuity and 1440/700/320px composition pass scoped review. Browser-process restart, OS/device and automated/stress coverage remain unclaimed. Next owner review covers toolbar placement and pin legibility.
- `2026-10-07`: Owner requests replacing toolbar date navigation with the Project filter, removing directional buttons, preserving visibility after browser close, native pin cues and revised source/view separators. Reopened for approved R5 frontend/docs work; existing producer and workflow boundaries remain.
- `2026-10-06`: Owner requests Project checkbox visibility, removal of footer annotations, compact branch spacing, resisted endpoint panning and a whole-chart overview. Reopened for the bounded frontend revision under the existing observation-only and frozen-surface boundaries.
- `2026-10-06`: Refined Chart is available on the ordinary server. Native filtering, two-axis overview, reading focus, resisted endpoint return, activity/detail continuity and wide/narrow containment pass scoped review. Resolved typography measurement fixes the final overview label. A controlled media query exercises reduced-motion camera return; automated suites, OS/physical-device and stress certification remain unclaimed. Next owner review covers filtering, overview legibility and tension.

- `2026-10-06`: Boundary locked by the owner's instruction to write the PRD and proceed with the clarified first Chart.
- `2026-10-06`: First Chart implemented and available on the existing local
  server. Rendered review covers wide/narrow composition, List preservation,
  scoped detail return and recovery states. Automated regression and physical
  gesture/stress coverage are not claimed. Owner inspection and any later
  inference decision remain open under the evaluation's non-blocking limits.
- `2026-10-06`: Owner review approved replacing collision rows with stable irregular placement and anchored elastic dragging. Reopened this Feature for the approved frontend revision; no inference or backend expansion is authorized.
- `2026-10-06`: Revised Chart implemented. Actual drag/release, click separation, cancellation, idle stop, fixed homes, activity/detail return and responsive composition pass scoped review. Reduced motion uses a controlled media-query branch check; automated regression, physical-device/OS-setting and stress coverage remain unclaimed. Next owner review concerns density and tension.
- `2026-10-06`: Owner review replaces irregular geometry with folder Project rows and recorded-branch guides; the owner explicitly selects first Session observation rather than live Git ancestry. Reopened for the bounded fullstack revision. Existing List/Workflow Focus/Auto Work remain frozen.
- `2026-10-06`: Project/branch Chart is available on the ordinary local server. Native dragging, dense selection, fixed homes, activity/detail return and 1440/700/320px composition pass scoped review. New projection edge rules receive source review; synthetic client fixtures do not establish backend execution. Automated suites, physical-device/OS settings and stress remain unclaimed. Owner review now covers Project order, branch structure and density.
