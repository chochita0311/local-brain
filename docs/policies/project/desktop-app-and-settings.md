# Desktop App And Common Local Settings

## Purpose And Scope

This contract defines the local settings shared by the web and desktop editions,
source identity and lifecycle, collection schedules, search availability, desktop
runtime boundaries and same-Mac recovery. Implementation status and unverified
behavior are recorded separately in Feature and Run evidence.

## Common Settings Contract

- `settings.toml` in the resolved local data directory is schema version 1.
- The settings service owns `startup_screen` (`sessions`, `sessions-dashboard`,
  `context`), `timezone` (IANA zone),
  `session_sync_enabled` (boolean), `session_sync_minutes` (integer, 10–1440 minutes),
  `context_sync_enabled` (boolean), `context_sync_minutes` (integer, 10–1440 minutes),
  and `onboarding_completed` (boolean).
- Defaults: Sessions, system time zone, Session sync enabled every 10 minutes,
  Context sync enabled every 30 minutes, and onboarding incomplete. Existing explicit values of supported settings win.
- First backend startup, in both app and web editions, creates `settings.toml`
  with schema 1 and all defaults if the file is absent, before serving requests.
  Users do not need to save the settings screen or finish onboarding to create it.
  An existing installation with registered Session or enabled Context sources
  starts with onboarding complete; a fresh installation keeps it incomplete.
  Later startups preserve an existing file, including partial or invalid files;
  missing fields use defaults in memory without rewriting it. Reading preferences
  alone has no file-creation side effect. Private atomic writes and revision
  checks also apply to the initial creation.
- General preferences use the local file, with defaults only for missing fields.
  `LOCALBRAIN_STARTUP_SCREEN`, `LOCALBRAIN_TIMEZONE`, `LOCALBRAIN_SESSION_SYNC_ENABLED`
  and `LOCALBRAIN_SESSION_SYNC_MINUTES` are ignored, including invalid old values.
  The initial time-zone default comes from the Mac's zoneinfo setting, then UTC;
  process `TZ` does not select this preference. No existing file is rewritten on read.
- The existing API shape remains compatible: `saved` and `effective` carry the same
  file/default values; `source` is only `saved` or `default`. This is one resolved
  value set, not independently configurable layers. Runtime directory selection
  and per-launch authentication remain separate from general user preferences.
- Reads preserve unknown fields at a known version. Unsupported versions and
  malformed files are reported without overwriting them. Writes validate the
  complete result, use an expected content revision, a local exclusive lock and
  same-directory atomic replacement with private file permissions.
- Startup choice applies at next app launch. Time zone applies
  on the next rendered view; schedule changes apply to the next scheduling
  decision, without interrupting an active collection.
- Paths use a fixed home-abbreviation rule, with no display preference or
  registered display roots. Only the current home and its descendants at a path
  component boundary are shortened: home itself is `~`, children are `~/…`,
  paths outside home retain their original form. Display does not resolve
  symlinks, require an existing folder or replace missing paths with a home.
  Actual stored paths, source/session/workspace identity and frozen Usage
  attribution remain unchanged. Project grouping retains its existing meaning.
- Retired `project_display` and `projects` values are preserved as inactive raw
  TOML fields on later saves, but are omitted from active preferences and rejected
  in new API updates. `LOCALBRAIN_PROJECT_DISPLAY` is ignored. Fresh settings do
  not create these fields; malformed legacy field values do not block otherwise
  valid settings. Invalid TOML/unsupported versions still use the normal errors.
- Session TOML, search JSON and Context DB remain their domain owners. Rebuildable
  sync health lives in `session-sync-state.json` and `context-sync-state.json` beside
  the settings, with independent completion clocks. Health-only
  writes do not change the database stamp used by search indexing. Each file
  retains the latest domain run state, not an append-only history. The next due
  time is computed from completion and the saved interval. The DB's `sources`
  owns per-source latest attempt/success/status/error; `source_files` owns the
  latest per-file scan state. There is no dedicated overall sync-history table.
  Data-directory relocation is excluded.

## First-Use Setup

- Incomplete desktop onboarding opens the shared settings dialog as a wizard
  above the actual saved startup surface. `/onboarding` redirects to that surface
  with an explicit setup request; the request is removed from the displayed URL.
  Ordinary web pages do not force the wizard; the explicit route works in both
  editions. Invalid preferences retain the normal settings recovery route.
- Welcome, Session sources, Local Context and Search are sequential steps with
  four small progress dots below a fixed Previous/Next/Skip footer. Dots identify
  the current step without bypassing save/skip actions. A quiet header and shared
  surface/type tokens keep the setup in the settings family. Step changes use a
  short crossfade and small directional offset; reduced motion swaps immediately.
  Both panels are inert during the transition and duplicate moves are disabled.
  The background is
  inert from initial markup and the native modal contains keyboard focus.
  Each step focuses its heading and starts at the top of its scroll pane.
- Existing source/context/model controls are reused. Next saves pending source
  or document inputs before advancing; validation or API failures retain inputs
  and the current step. Back retains drafts. Skip does not register a draft.
  Empty sources and model-free search are valid; no step navigation downloads
  or prepares a model. The existing explicit model actions retain that authority.
- Welcome links to the bundled English Getting Started guide. Docs pages do not
  auto-open onboarding over their content; reading the guide does not complete
  setup or register sources. Explicit setup requests and ordinary startup keep
  the existing completion behavior. [In-App Documentation](app-documentation.md)
  owns the reader, route and packaging contract.
- Final Next/Skip or explicit Set up later (also Escape) saves
  `onboarding_completed = true` with a fresh revision, then opens the saved
  startup surface. A failed completion keeps the modal open; an ambiguous write
  is accepted only after readback confirms completion. Quitting the app before
  that action leaves onboarding incomplete and preserves registrations already
  saved. Initial settings-load failure offers retry; regular settings keep their
  existing categories and general autosave.

## General Settings Presentation

- The settings dialog is capped at 720 by 560px at the default scale and shrinks
  within the viewport. Its 160px desktop category rail becomes a horizontal row
  at 700px. Header/close stay visible; the content pane owns vertical scrolling.
  Switching categories reveals the new pane's top. Leaving the Session-source
  category closes its editor and discards unsaved inputs; general choices use autosave and
  stored-value recovery below. Errors scroll into view; general saves stay quiet.
  Geometry and typography follow the [Design Constitution](../design/design-constitution.md#dialogs-and-drawers).
- Startup is a dropdown ordered Sessions Dashboard, Sessions, Local Context,
  matching the sidebar. Ordering does not change the default/saved Sessions choice.
  Its menu opens directly below the displayed control, with matching width and
  a stable downward cue; selecting an item closes the menu.
- Time zone uses the same dropdown with exactly `UTC` and `Asia/Seoul` (KST).
  Display these literal names. There is no city search or expanded zone catalog.
  A previously stored different valid zone stays displayed and is preserved
  until explicitly replaced; it does not add a third selectable option.
- General dropdowns cap at 240px, shrinking within
  narrow panes. Menus match their trigger width and open below it. Desktop form
  fields and action buttons share the 32px control height and centered action
  labels; narrow panes use 40px touch controls. Helper text retains its wider
  reading measure. Source tool/name columns share equal control dimensions;
  source tool and Context kind reuse the below-trigger selector and keyboard
  behavior. Existing source identity locks the tool in Edit.
- Context and storage use compact grouped information rows, consistent headings,
  path type and secondary metadata. Model download/status stays in one quiet
  group; preparation requires an installed model, cancellation appears during
  downloading/preparation, and an already disabled AI search cannot be disabled
  again. Model storage details and backup restoration use disclosures. All model
  actions and backup/restore/cache operations retain explicit invocation and
  existing consequences; collapsed restore still requires its ZIP and replacement
  confirmation. Browsing settings never downloads a model.
- There is no project-display dropdown, display-root list or root-add action.
  Sessions, Chart, Dashboard, Context and read-only settings path labels use the
  common home formatter. Path editing/selection retains the actual registered
  value; source registration remains independent of display. A workspace at
  `~/Projects` displays `~/Projects` rather than `.`. No historical Usage
  reassignment is performed. Dashboard Project
  composition includes work Sessions and work subsessions; it excludes all analysis
  and Maintenance records from rows, total and shares. Overall usage/history and
  Source/Model keep their usage. Preserve By Project / Project labels, Git/folder
  grouping including home, unknown-work `프로젝트 미지정`, and hidden desktop Insights.
  The [Usage contract](data-model/usage-and-cost-records.md#usage_records) owns membership.
- Keyboard users can open, navigate and choose an option; Escape dismisses
  without changing the value. Only one menu opens at a time. Dismiss on outside
  interaction, tab change and dialog close; keep the trigger and menu visible
  within the settings scroll area. General options persist on confirmed selection;
  highlighting, Escape and selecting the current value do not save. Source forms
  retain explicit Save. General saves patch only the selected field
  with the existing revision; Sync uses that same autosave/readback boundary.
  Turning either source schedule off preserves its interval.
  General help says only `설정은 이 Mac에 저장됩니다.`; no override explanation or
  saved-versus-applied value rows are shown.
- General choices briefly disable during one local write so requests do not race.
  Closing does not cancel the write; reopening waits before loading preferences.
  Success is quiet, with no Save button, success notice or forced page reload.
  Failed saves reread the file: use actual stored values, confirm an ambiguous
  successful write by value, otherwise show a retryable error. If readback fails,
  disable choices until a successful settings reload. Preserve concurrent edits
  and unknown settings. Keep time-zone impact help without application-timing
  notices; startup still applies on next launch and time zone on the next view.
- The time-zone preference controls Session/activity/conversation timestamps,
  Session chart date labels and the Sessions Dashboard's
  local date range and day/week/month grouping. Crossing a date boundary can
  change which period contains a usage record. It does not rewrite original
  timestamps, Usage facts or source attribution, change the Mac clock, or change
  the saved elapsed synchronization interval. Page displays apply on the
  next navigation/reload; startup choice still applies on app relaunch.

## App Information And Version

- About shows the existing LocalBrain mark, product name and `v` plus the running
  application version. Keep it concise. [Getting Started](../../../src/localbrain/content/docs/getting-started.md)
  owns quitting and updates; [Settings](../../../src/localbrain/content/docs/settings.md#synchronization)
  owns background synchronization. Artifact-specific launch and distribution checks
  remain in the [test distribution guide](standalone-test-app-guide.md). Do not add
  invented build, copyright or license claims from a reference screen.
- The initial application release version is `0.0.1`. The Python constant owns
  About and FastAPI version rendering; Python distribution/lock, desktop package/
  lock, Cargo package/lock and Tauri configuration declare the same release.
  Delivered native Info.plist and BUILD-INFO version must match. Dependency
  versions, bundle identifier, storage locations and data schemas are independent.

## Source Lifecycle Contract

- A numeric profile ID identifies imported records; provider selects the parser. Label, agent home
  and session root are separate values. Codex proposes `<home>/sessions`, Claude
  proposes `<home>/projects`; users can select a different session directory.
- Fresh installations have no implicitly registered Session or Context folders.
  Existing configuration and registrations survive upgrades. Candidate detection
  is read-only and never registers or scans an agent home itself.
- Reject duplicate or overlapping canonical session roots. A saved unavailable
  source retains its registration and data. Editing the label preserves identity.
- Reconnect requires explicit same-source confirmation, a readable new directory
  and evidence that existing relative Session files are present there. Preserve
  IDs and remap indexed file locations in one coordinated operation. Failure
  keeps the old registration; no source file is moved or modified.
- Removing a registration retains its identity with `enabled = false` in the Session
  TOML and stops collection and excludes it from ordinary search;
  imported records remain available through existing source-based browsing. Explicit
  re-registration reuses that identity; manually missing config entries still report
  configuration problems. Disabled sources do not make every scheduled scan fail.
  Successful collection at a readable root keeps the existing mirror policy for
  disappeared native files; this is not permanent source archiving.
- Collection, source mutation and restore share a data-directory process lock.
  Automatic/manual collection coalesces; multiple tabs or backends cannot run
  concurrent scans of the same store. Runtime state is not a second settings store.

## Session Profile Presentation

- Settings and the first-use Session step share a compact profile overview and
  one editor. Rows show the saved name, provider when it differs from that name,
  and the home-abbreviated Session folder. Healthy `ready` machine text is omitted;
  unavailable/configuration/scan errors and retained-but-unregistered state remain
  readable. Normal availability does not imply a successful synchronization.
- Profile names come from `display_label`, reconciled into `sources.name`. The
  settings list and Sessions / Session Dashboard filters follow the TOML array
  order. Saved name, color and order changes update the open page immediately,
  retaining the selected numeric profile ID; All remains first. Provider remains
  distinct from the profile ID and display name.
- Add/Edit opens in the same pane with Tool, Profile name and Home. The name
  placeholder uses Codex or Claude Code for the selected tool and does not
  overwrite entered/saved names or satisfy required validation.
  Required fields show red “필수” text alongside native validation; Home's marker disappears
  when an explicit custom root makes it optional. Derive `sessions`
  under a Codex home or `projects` under a Claude home and show the resulting record
  location. Submit that explicit root through the existing API; only records under
  that root are collected, not the full home or its credentials/settings.
- “Custom session folder” discloses a “Session folder” override and folder picker.
  The derived-path readout also uses “Session folder”. An override stays fixed
  when Home changes. “기본 폴더 사용” clears it and
  resumes derivation. Home is required only when there is no explicit record root.
  Tool and stored source identity stay fixed during editing.
- Preserve existing roots. A home-less conventional root can prefill its parent
  without writing anything; nonstandard roots are disclosed and retained, including
  registrations without a home. Opening/canceling does not migrate configuration.
  A derived or custom target change still needs same-source reconnection approval.
- Candidate suggestions only fill the editor. Paths already represented by the
  same provider/root pair are omitted; empty suggestions are hidden. Backend
  canonical duplicate/overlap checks remain authoritative, including aliases.
- Save returns to the overview; validation/API failure retains the editor and
  values. Busy writes disable fields, conflicting form actions and category changes.
  Cancel, leaving the category or clicking Session sources again clears the draft
  and returns to the overview; wizard Back preserves it. Wizard Next still saves pending input and Skip leaves it unregistered.
- Same-source confirmation appears when the edited Session folder differs from
  its stored or home-abbreviated path; changing the target resets that confirmation.
  Backend identity/evidence checks own acceptance.
- Each registered profile row has separate compact Edit and Unregister buttons,
  using label-sized text and control-gap inline padding with shared minimum heights.
  Unregister opens a named confirmation modal with Cancel initially focused;
  the underlying settings dialog is inert until confirmation closes.
  Its message explains exclusion from collection/ordinary search and preservation
  of imported records/originals. Cancel/Escape write nothing and return row focus.
  Confirm submits the captured identity/revision; busy state blocks repeated
  submission/dismissal. Errors remain in the modal; a lost response is checked
  against the registry, while a changed revision requires canceling and reviewing
  the updated list. Retained unregistered rows offer re-registration with the same
  source ID. No removal action remains inside Edit.

## Local Context Settings Presentation

### Supported Material And Permissions

Folder sources collect supported Markdown documents. Individual text and Markdown
files can be registered separately. PDF bodies require text supplied by macOS
Spotlight; no OCR or separate PDF engine is included. Missing read permission or
an unsupported file produces a source/readability state while other sources
remain usable. Apple Notes is optional and requires macOS Automation permission.

### Local File And Folder Selection

Browse opens a macOS chooser for Session Home, a custom Session folder and Local
Context. Home/Session/Context roots choose one folder; a Context file chooses one
file. The native app uses its dialog plugin, attached to the invoking window. The
local browser calls a same-origin POST endpoint, which runs a fixed AppKit chooser
on the Mac hosting the local server. It needs no Finder automation, uploads or
third-party service. Hidden folders are visible in the browser chooser so agent
homes can be selected. Other server platforms retain direct path entry with a
clear unsupported-chooser error.

The browser endpoint requires an exact local Origin and JSON with only a boolean
`directory`; it accepts no script or arbitrary command. One chooser per backend is
admitted, with a five-minute execution bound. Errors do not expose process output.
While a chooser is pending, fields, category changes, dismissal and conflicting
actions are unavailable. Cancel keeps the draft; a selection fills the intended
field only. Registration, collection, reconnection and first-use Next/Skip retain
their existing explicit authority. Picking does not persist a path independently.

### Context Rows And Editor

- Session and Context settings share independent white rows with subtle borders and
  resting shadows, control-level focus feedback, a drag handle and insertion marker.
  Dragging lifts the whole row, previews its slot with animated neighboring rows,
  and scrolls the pane near its edges. Release saves a changed order once;
  Escape, interruption and release outside the pane restore the original order
  without saving. Keyboard arrows preview and save the same order. Reduced-motion
  preference suppresses transitions; failed readback restores the last confirmed
  presentation. Focus returns to the moved handle.
  Hover/focus/drag do not tint the entire row.
  Context rows prioritize saved labels and home-abbreviated paths, with compact
  Unregister actions. Routine document counts and ready text are omitted in settings;
  pending, missing, unreadable and error states remain. Explorer counts are unchanged.
- Add opens a separate editor in the same pane. Cancel, leaving or reclicking the
  Context category clears its draft and returns to the overview; wizard Back retains
  it, Next saves pending input, and Skip does not. Folder/file registration and
  optional Apple Notes remain explicit. Notes addition is hidden once registered.
- Context order is stored only in `context_roots.display_order` in the local DB.
  Drag/drop or keyboard arrows autosave a complete numeric-ID permutation, compared
  with the previous ordered active IDs under the local writer lock/transaction.
  Stale or invalid changes are rejected and the UI reloads saved order. Existing
  default ordering is retained until changed; new unset roots follow positioned
  roots. Re-registering a retained root preserves its saved position. The explorer
  retains Folder/File groups and follows saved relative order within each group.
- Settings and explorer unregister open a named app modal with Cancel initially
  focused. Cancel/Escape write nothing; busy submission blocks repeat/dismissal;
  errors stay in the modal, and a lost response is checked against current sources.
  Removal excludes the root from sync/search/browsing and clears its existing derived
  index/evidence, preserving the disabled registry, imported documents and originals.
  Re-registration uses the same root ID. The actual file/Notes source is never deleted.

## Synchronization Presentation

- Settings order is General, Session sources, Local Context, Search model, Sync,
  Storage, About. General contains startup/timezone. Source categories own which
  locations to read; Sync owns when. Storage remains a separate category.
- Sync contains Session and Local Context groups. Each has one content-sized dropdown (about 79px at the default scale):
  10/20/30/60 minutes, then Off. Off saves only enabled=false, preserving the interval
  and imported records. Choosing minutes atomically saves enabled=true and the
  interval for that group. Each selection autosaves; the other group is unchanged.
  Existing valid custom intervals remain displayed until explicitly replaced;
  integer 10–1440 validation remains compatible. No timestamp/history card,
  manual settings button, range/runtime help or AI-index placeholder is shown.
- Session defaults/saved values remain; Context defaults to enabled every 30
  minutes. Missing fields use defaults without rewriting an existing file.
  Both app and web backend run the same services while alive. Each next run is
  measured from its own completion. Sleep/restart coalesces overdue work, not a
  replay of missed intervals. Empty registries do not start collection.
- Collect only enabled registered sources through existing adapters. Context
  reuses folder/file/Apple Notes scope and macOS permission boundaries. Originals
  stay read-only. Neither schedule changes originals, refreshes Git or external
  services, or starts an agent task. Folder/file scans reuse unchanged entries;
  Notes retains its existing snapshot reader. One local writer lock excludes
  concurrent collection/settings/recovery writers across domains and backends.
  A busy writer retains one pending manual request until its own domain completion
  satisfies it. Context cancellation rolls back its transaction; directory/note
  iteration checks cancellation and the Notes reader subprocess is stopped on exit.
- Health files retain the latest separate outcomes; source/file/root health stays
  in the existing DB tables. Failed collection preserves imported records and the
  latest successful collection time. No new data root or DB schema. AI-index
  scheduling has no independent controls; enabled search still observes normalized DB
  changes and does not download a model implicitly.
- The common shell has no sync-status strip or updated-records link. Sessions
  retains its manual sync button and running state. Background completion preserves
  the current page, filters, focus and scroll; navigation/reload displays new data.

## Search Availability Contract

- The shared search entry exposes explicit keyword and AI modes. Keyword mode
  reuses the legacy FTS5 token AND query; it does not require model installation.
- Both modes admit only eligible work Sessions and enabled/readable registered
  Context, excluding runtime/private derived folders and unregistered sources.
- AI mode distinguishes disabled, missing assets/runtime, preparing, ready,
  partial and failed. A visible keyword action preserves the query. Zero AI
  results never silently select another mode. Downloads require a user action.
- Source-health writes alone must not trigger full embedding generation. Existing
  input hashes, contract compatibility and incremental reuse remain authoritative.

## Runtime And Product Boundary

- Common web execution and the Tauri app use the same settings and periodic sync.
  Closing a browser does not stop its independent server; stopping that server
  stops scheduling. The packaged app owns its backend, closes windows without
  quitting, and shuts down the backend on explicit app quit.
- The packaged edition exposes Sessions, Sessions Dashboard, Context, search,
  onboarding, settings and bundled Docs. Dashboard/learning, Workstreams, Auto Work, Atlassian,
  Insights, Session workflow and Schema cannot be enabled by user settings or
  direct HTTP access. The normal development web edition keeps its other routes.
- The desktop server binds loopback on an available port, authenticates its
  window with a per-launch secret and rejects cross-origin mutations. Native
  commands expose only explicit path selection and approved app actions.
- The initial `tauri://localhost` → loopback handshake sets an HttpOnly,
  `SameSite=Lax` session cookie before redirecting to the saved start page.
  `Strict` prevents WKWebView from sending that cookie on this initial
  cross-scheme top-level redirect. Lax preserves the first GET while token,
  loopback and mutation-origin checks remain required. The handshake is not
  cached and sends no referrer; boundary JSON errors explicitly declare UTF-8.
- No autostart, background daemon, cloud sync, app encryption, paid signing or
  automatic updater is introduced. Program ZIPs contain no personal runtime data.
- Frozen Python installation metadata resolves against the running bundled
  interpreter prefix. Build-time user-home and checkout paths must not remain
  in shipped metadata, including compressed Python constants. Packaging checks
  raw files and compressed Python/stdlib archives before creating the ZIP.
  This does not change application data/settings ownership under each user's home.
- On macOS/Python 3.10+, the dedicated UI model-download worker uses the OS trust
  store through truststore, while retaining TLS certificate verification. This
  honors locally trusted managed-network certificates without bundling a company
  certificate or disabling HTTPS checks. The worker owns the early application-level
  initialization recommended by [truststore](https://truststore.readthedocs.io/en/stable/).
  A parent-lifetime pipe ends the download worker if the backend exits or crashes.

## Local Recovery

- Backups contain a consistent SQLite snapshot and app-owned settings/model
  registration metadata. They exclude external originals, Hub weights, caches,
  credentials and logs. Restore validates archive paths, ownership/schema and DB
  integrity and the application schema fingerprint before replacing state under the shared operation lock.
- Restore is same-Mac recovery, with a recovery copy and rollback on failure.
  A restart reopens restored state. Cache cleanup is explicit, limited to owned
  inactive derived data and must never follow symlinks into external content.

## Generalized Session Profiles

- Version-2 `session-sources.toml` uses the existing numeric `sources.id` as
  `source_id`. The file has `schema_version = 2`; each array entry contains
  `source_id`, `provider_kind`, `display_label`, `root`, a palette `color`, and
  optional `agent_home`/`enabled`. Writers keep those fields in that order for
  readability; field order has no semantic effect. IDs are positive JavaScript-safe integers.
- Valid v1 files migrate locally with existing IDs and the former visible DB-ID
  order retained. Provider defaults are green for Codex and orange for Claude;
  the legacy blue profile keeps blue. Invalid or conflicting files are preserved.
  This migration does not move files or re-key events, usage, pins or attribution.
- TOML array order is authoritative after migration. The DB caches color/order in
  `profile_color`/`profile_position`; omitted retained profiles follow configured
  ones. A missing v2 color uses the provider default, never a previously cached DB
  color. Reloading settings or the next collection applies valid manual edits.
- Name, color and order are editable presentation. Provider determines CX/CL;
  `sources.id` is the sole profile identifier. `sources.kind` is removed; there is
  no replacement string key or alias table. Source filter toggles show the saved
  names without color dots; record cues retain their colors. Filters and settings use numeric IDs;
  obsolete alias links fall back to the unfiltered scope.
- Startup migrates retained skill source references, chart scopes, workflow
  boundaries and analysis usage settings in one verified, backup-backed DB
  transaction. A failed migration rolls back the DB and attempted TOML/report
  upgrades, while preserving any concurrent file edits. Cached sync reports also
  move to source PKs while preserving their completion clocks, outcome and counts.
  Interrupted reconnects are recovered first; unexpected schemas or
  conflicting v1 identities stop the upgrade without discarding evidence.
- Event and Usage PKs are opaque record identities. Re-ingestion finds retained
  rows by their native unique keys and preserves those PKs; newly observed rows
  are scoped by numeric source ID. Frozen report artifacts remain historical;
  their cited events resolve through event/session PKs, not profile aliases.
- Settings use diagonal color-only tag buttons and a six-choice vertical menu
  directly below the trigger. Menu tags are horizontal with the point and hole on
  the left; their painted widths and both edges match the trigger glyph. The menu
  frame matches both edges of the trigger background (32px wide by default, 40px
  in narrow layouts); choices fill its inner width. Heights remain 24px for fine
  pointers and 40px for coarse pointers, without padding or inter-choice gap.
  Height sizes to content in Chromium and WebKit. Short windows retain scrolling
  without a width-consuming scrollbar gutter. Outside interaction,
  Escape, category change and anchor scrolling close it; its own scroll area
  keeps choices reachable in short viewports. Up/Down and Home/End move focus,
  Escape returns focus, and a selection closes the menu. Choices retain
  accessible color names and radio selection without menu hover tooltips. A profile-colored outline and quiet
  fill mark the selected color without a check column; keyboard focus remains
  separate from selection. Separate rows have no shared
  enclosing frame; both source lists use the shared whole-row movement described
  above. Dragging the handle or pressing Up/Down while it is focused saves list order. Saves validate the
  revision and complete configured ID set; readback resolves ambiguous responses.
  Names/colors/order update the current page without changing its selected ID.
- Collection-root changes use the existing same-source reconnect check. A Home
  edit with an unchanged explicit Session folder changes metadata only. Removing
  registration retains the ID/history; it does not delete transcripts or usage.
