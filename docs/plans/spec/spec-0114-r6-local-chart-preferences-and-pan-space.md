# SPEC-0114-R6: Local Chart Preferences And Pan Space

## Metadata

- ID: `spec-0114-r6`
- Status: `superseded`
- Run: [RUN-146](../run/run-20261007-146-local-chart-preferences-and-pan-space.md)
- Attempt: `1`
- Parent Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Parent PRD: [PRD-0019](../prd/prd-0019-observed-session-chart.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: `data`, `backend`, `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-07`

## Approved Direction

R7 supersedes this as the active execution spec, retaining the persistence,
space, producer and frozen-surface contracts here and refining wheel input only.
See [SPEC-0114-R7](spec-0114-r7-session-chart-wheel-controls.md).

The owner explicitly selects LocalBrain database persistence after learning that
browser site-data removal loses R5 localStorage choices. The owner also requests
visible-project date boundaries, more symmetric end space and a larger elastic
pan range. This authorizes one preference table and its local write contract;
it does not authorize observation, pin, Workflow Focus or Auto Work mutations.
Use screen-alignment `extend` and the native canvas/pin/control family.

## Persistence Contract

- `session_chart_preferences` stores one current hidden-folder list per logical
  source scope and workspace scope in the private primary SQLite database.
  Empty workspace scope means all workspaces; an empty list means all Projects.
  Keys are recorded folder identities, including the missing-folder empty key.
  Retain absent hidden keys without creating project membership or classifications.
  Scope text has no cascading FK: source/workspace cleanup must not erase intent.
- Ordinary Chart GET reads this preference. Camera/selection/vertical scale remain
  tab navigation state. DB state, including explicit all-selected, takes precedence
  over any browser state and is shared by browsers using the same LocalBrain DB.
  Browser/site-data clearing cannot delete this preference; DB loss requires backup
  recovery or reselection. No cloud sync, account or external service is introduced.
- An absent DB setting permits migration from valid R5 localStorage, then legacy
  tab visibility. Migration uses create-if-absent to avoid overwriting a DB setting
  created meanwhile. Clear the old durable browser key only after successful DB
  confirmation. No stored browser choice means default all, without a guessed write.
- `PUT /sessions/chart/project-visibility` uses validated source/workspace query
  scopes and a bounded same-origin JSON body with `hidden_projects` and optional
  Boolean `only_if_missing`. Strings are bounded, deduplicated and sorted; unknown
  current folders remain permissible preference identities. Normal updates replace
  that one scope only; migration preserves any existing row. Commit precedes success.
- Serialize browser writes, retaining the newest queued choice. Use bounded
  keepalive requests for pending navigation; only confirmed writes are durable,
  and abrupt closure of unconfirmed queued work is not a save receipt. Failed load/save remains usable and
  shows a native contextual retry; never claim a failed save persisted. Migration
  success applies the actual server preference unless newer user intent is queued.

## Camera And Space Contract

- Bounds use only visible dated Sessions, earliest first observation through latest
  observation, plus explicitly loaded activity of a selected visible Session. Hiding
  its Project clears that activity. Time origin remains an internal fixed coordinate.
- Preserve left/right endpoint anchoring when filters change; whole-time fit refits
  the surviving period. A middle camera preserves its time anchor and clamps to the
  new range. Hiding the oldest Project contracts the left end when it owned that
  bound; another visible Session/activity at the same earlier time keeps it.
- Both ends reserve the same native inset: 64px on large plots, capped by 20% of
  usable width and the free space around projected targets on narrow plots. Center
  source circles in 40px targets and account for their projected footprint in fit,
  endpoint limits and initial placement. Guide ends keep the same frame inset.
  The existing reading-scale/one-day cap can leave extra right space for a short
  observed period.
- Blank-drag extension increases from 40px to at most 80px, capped at half the usable
  plot width. Keep the resistance curve and existing damped return; reduced motion
  returns immediately. Transient extension is never saved. Retain compact branches,
  overview fit, point pulling, source cues, pins, exact selection and detail return.

## Lane Order And Evidence

Primary owns each lane without delegation. Establish `data` (`schema.sql`, Data
Model owner, generated Schema presentation) and `backend` (`session_chart_preferences.py`,
Sessions GET/PUT in `main.py`) before publishing the dependent `frontend` assets and
template. `docs` updates product/storage/design/current planning facts in the same Run.
Contract review checks scope, migration precedence, input/error semantics and narrow
DDL ownership before the consumer. Manual browser review covers DB restoration across
browser contexts and site-data clearing, queued saves/retry, visibility endpoints,
both resisted pan ends, symmetric fit space, exact pinned selection and wide/700/320px.
Use synthetic private runtime state for write review; no automated test suite is
added/run. Syntax, documentation/schema generation and privacy checks support only
their scopes. Remove task-owned review data/pages/server at closeout; ordinary app
stays available with the coherent producer/consumer version.

## Open Blockers

None. R5 browser-only/no-SQLite persistence is superseded by the owner's direct
choice. All existing observations and frozen work surfaces retain their boundaries.
