# EVAL-0114-R6: Local Chart Preferences And Pan Space

## Metadata

- ID: `eval-0114-r6`
- Status: `complete`
- Evaluator Types: `contract`, `design`, `functional`, `ux-heuristic`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R6](../spec/spec-0114-r6-local-chart-preferences-and-pan-space.md)
- Run: [RUN-146](../run/run-20261007-146-local-chart-preferences-and-pan-space.md), attempt `1`
- Execution Profile: `fullstack-product`
- Surface Lanes: `data`, `backend`, `frontend`, `docs`
- Created: `2026-10-07`

## Scope And Evidence

Primary performed sequential producer-contract, rendered design, functional and
UX review without delegation. Screen-alignment `extend` retains the current
Chart/control/pin family and constitutional tokens. The owner expressly replaces
R5 browser-only visibility persistence with one private DB preference contract.
Data/schema owners and packaged presentation were established before the backend
restart and dependent frontend publication. Final bounded-input refinements were
source-reviewed and loaded through a second ordinary server restart; its live
OpenAPI confirms the declared workspace integer bounds.

Native browser actions exercised a separate, task-owned synthetic private runtime
DB with 57 eligible Sessions, two sources, recorded-folder/branch metadata, two
pins and one earlier retained activity timestamp. This is manual application
review, not an automated test suite. The temporary server used isolated roots and
disabled startup lifespan to avoid source ingestion. Ordinary application review
confirmed coherent assets and existing List/Chart navigation without real pin or
observation writes. No private source content or screenshots are retained here.

## Contract Findings

- `session_chart_preferences` contains current display intent per logical source
  and workspace scope, with empty workspace meaning all workspaces. Hidden-folder
  keys are sorted/deduplicated, retain absent identities and allow the empty
  missing-folder key. Empty hidden list is authoritative all-selected. There is
  no cascading FK, observation membership, classification or pin mutation.
  The table is user-curated/non-rebuildable: full recovery needs a DB backup or
  reselection, and browser site-data clearing cannot erase a confirmed setting.
- Chart GET reads the scope setting. The bounded local same-origin PUT validates
  JSON/media/body size, admitted fields, key shape/character/count/UTF-8 byte limits,
  SQLite-compatible workspace query range and existing source/workspace scopes.
  DB work runs in the thread pool; commit precedes acknowledgment and its no-store
  response returns the actual stored preference. Normal update replaces one
  current setting; create-if-absent migration preserves a row created meanwhile.
  Invalid-request status branches receive source review, not runtime certification.
- DB state, including all-selected, overrides old browser state. Only an absent,
  available DB setting permits R5 localStorage then tab visibility migration.
  Confirmed server state clears the old durable browser key. Camera, selection,
  vertical scale and List page remain tab state. Only known keys affect display;
  absent hidden keys remain retained. No cloud or external persistence is added.
- Browser saves are serialized, retain the newest pending choice and use bounded
  keepalive requests. Failed load/save preserves in-memory use and exposes actual
  contextual retry. Only confirmed writes are durable; abrupt browser closure
  while newer intent is still queued is not claimed as a successful save.
- Bounds use visible first/latest observations and explicitly loaded activity of
  a visible selection. Hiding its Project clears selection/activity. Filter change
  follows a left/right endpoint camera, refits whole-time fit, or preserves and
  clamps a middle time anchor. Internal time origin remains fixed.
- Targets center source circles in the native 40px hit area. Fit/limits reserve
  the projected target footprint plus a common 64px inset capped by 20% usable
  width and free target space. Guides share that frame end and omit starts beyond
  it. The existing reading-scale/one-day cap can leave additional right space for
  short periods. Blank drag extends toward an 80px limit, capped at half usable
  plot width, with the existing resistance and damped return. Point-pull limits
  remain separate; transient camera extension is never saved.

## Rendered And Functional Findings

- A native checkbox hiding the synthetic oldest Project contracts the first
  visible date and refits the surviving period. At a 939px wide plot, whole fit
  has measured target insets 64.086px/64.007px; after hiding that Project,
  64.109px/64.005px. Guide inset is 64px and source circles are centered. Small
  fractional differences reflect aggregation at the latest member observation.
- Native 739px blank drags at the fitted ends produce approximately +72.186px
  and -72.186px transient travel with exact zero final displacement on release.
  A controlled reduced-motion query returns to zero in the first released frame.
  These are browser-pointer/controlled-branch observations, not physical-device
  or OS-setting certification.
- A fresh isolated browser context restores the saved hidden Project. Clearing
  its localStorage/sessionStorage and reloading retains the DB choice. A distinct
  localhost origin reads the same DB state, and restarting the synthetic app
  process retains it. This proves server persistence and fresh-context restoration;
  the Chrome process itself was not restarted.
- Three native checkbox changes during one deliberately delayed save maintain
  at most one in-flight request and coalesce to two actual writes, with the final
  DB hidden list matching the newest UI choice. A controlled fetch failure leaves
  the previous DB state unchanged, retains the changed in-memory selection and
  shows the save error. Native retry confirms the new choice and clears the error.
- Valid browser visibility migrates into an absent source/workspace DB setting,
  ahead of stale tab hiding. A temporarily absent hidden key survives a subsequent
  native all-current-Projects selection. Explicit empty browser visibility migrates
  as all-selected, and a confirmed empty DB setting then overrides stale hidden
  browser values on reload. Scope-specific rows preserve the separate All/source/
  workspace choices.
- One corrupt synthetic preference causes a truthful load error with a usable
  Chart and default/fallback visibility; it never triggers automatic migration.
  After repairing only that synthetic row, native reload retry restores availability
  and removes the error. Native earlier activity selection renders its retained
  timestamp; hiding its Project clears that activity and exposes the honest empty
  filtered scope without deleting Sessions.
- Native aggregate selection retains the static pin cue even when the host is
  unpinned. Choosing its pinned original member shows exact status and its own
  detail URL. Native synthetic detail entry and Chart backlink restore that
  member, pin status and Project choice. No pin control was activated.
- At effective 700px, the 559px plot retains approximately 64px end insets. At
  320px, a 179px plot adapts to approximately 35.8px per end. Menus stay inside the
  window, essential actions remain 40px high, all visible Project headings fit
  and outer horizontal overflow is absent. With the menu closed, native whole
  fit brings the 540px canvas inside the 960px window. Preview remains in flow on
  narrow screens; wide reading preview uses its reserved plot width.
- The ordinary application uses the final Chart asset revision and DB producer,
  preserves existing visibility and retains its full-width Chart. Native List
  entry still renders rows, pin controls and Pinned Sessions recall; native Chart
  return restores the view with no outer overflow or console warnings/errors.
  Existing observation producer, Workflow Focus and stopped Auto Work remain
  outside this revision's changes.

## Checks And Evidence Limits

Python AST parse, JavaScript syntax, whitespace/privacy checks, Data Model ownership
validation and packaged Schema generation/check pass for their scopes. Schema
presentation has 45 ordinary tables, one FTS object, 519 effective columns, 57
physical FKs, 51 explicitly named indexes and ten subjects. Existing static-check
expectations were updated for the added table; no automated behavior tests were
added or run. Plan artifact catalog is regenerated from current owner artifacts.

Coverage is partial. API malformed-request status branches, rare/extreme timestamp
ranges, abrupt close with unconfirmed queued writes, cross-tab live synchronization,
physical touch/trackpad, actual OS reduced-motion setting, browser-process restart
and stress/fault injection beyond the described controlled states are unproven.
A menu-covered fit attempt was repeated with the disclosure closed. An extra
synthetic navigation attempted after deliberate preview-server shutdown received
connection refusal; List/Chart return was subsequently rechecked on the active
ordinary app. These review-sequence issues are not product defects.

## Cleanup And Owner Review

Task-owned review server, synthetic DB/configuration, private notes/draft,
review pages and instrumentation are removed after review; the ordinary app and
owner inspection page remain available. No commits, staging, external writes or
new approval gates were introduced. Owner review now covers DB-backed Project
visibility, contracting date ends, breathing room and elastic pan travel. Existing
work relationship inference remains a separately approved future boundary.
