# run-20261018-172-general-and-project-settings

## Metadata

- Status: `blocked`
- Feature: [FEAT-0134](../feature/feat-0134-general-and-project-settings.md)
- Active Spec: [SPEC-0134](../spec/spec-0134-general-and-project-settings.md)
- Execution Profile: `fullstack-product`
- Required evaluations: Contract, Functional, Design, Interaction

## Selected Loop

The primary agent owns implementation and review. No delegation. User approval covers
implementation and related tests, browser verification and packaged-app execution.

## Current Route

Implementation and available local verification completed on 2026-10-19.
The [functional report](../evaluation/eval-0139-functional-standalone-test-app.md), [contract report](../evaluation/eval-0139-contract-standalone-test-app.md) and
[design/interaction report](../evaluation/eval-0139-design-standalone-test-app.md) record the integration checks for this
Feature and the complete Feature/Spec/Run trace. They distinguish browser evidence,
the actual frozen/native app and real model execution from unobserved native
interactions and the required teammate Mac receipt.

Route: `blocked` for full product acceptance pending those external/manual
observations. The local test artifact is available for owner use. The full suite
has 1,168 passes and four pre-existing learning inventory failures (1,172 total);
no failure is concealed by this route. No upload, teammate message or Git
publication was performed. The 21-commit figure remains an estimate.

## Apply-Timing Copy Removal — 2026-10-20

Approved bounded follow-up: remove the repeated startup/time-zone timing notice
and shorten save feedback to its success confirmation. Frontend profile;
general-settings copy lane; screen-alignment `extend`. Preserve control order,
values, help, explicit Save and actual application timing. Primary owns the
implementation and Functional/Design/Interaction checks; no delegation. Existing
test and browser/app verification authorization applies. Compare synthetic
before/after wide/narrow settings, save/reopen and next-view behavior; update the
two bundled assets, signature, ZIP/checksum and actual app with saved files intact.

Scoped Functional/Design/Interaction PASS. The [functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#apply-timing-copy-removal-delivery--2026-10-20-superseded-artifact)
owns the delivered artifact and [design/interaction receipt](../evaluation/eval-0139-design-standalone-test-app.md#apply-timing-copy-removal--2026-10-20)
owns the rendered checks. 72 UI/settings tests and JavaScript syntax passed. Four
before/after frozen WebKit cases at 1100/320 widths each passed 16 checks, including
explicit Save, saved confirmation, reopen, focus, contained menus and unchanged
current-view/next-view timing. Before/after synthetic captures were inspected.

The temporary probe first failed compilation because its Swift string contained
JavaScript Unicode escapes; correcting the fixture resolved it. Its initial
narrow focus check incorrectly clicked a hidden desktop gear. The corrected
narrow check uses the existing settings keyboard shortcut from a visible input;
the final old/new checks pass without changing product navigation behavior.

The actual app/ZIP were replaced and the app reopened. Authenticated health/settings,
served copy/assets and six startup WebKit checks passed; three settings/source/search
files retained their hashes. Backend code is unchanged; only two bundled assets
and signatures were refreshed. ZIP CRC, every distribution file, extracted app
inventory/signature and known private build-path inspection passed. No model
download or publication. Broader native/recipient acceptance remains separate.

Completion checks: repository privacy passed for 1,420 candidate files; diff
whitespace, catalog freshness and 114 planning links/anchors passed. Final
installed inventory/signature, ZIP/checksum, one running native app and unchanged
saved-file hashes passed. After verifying no active use, all owned temporary
tools, screenshots, synthetic data, caches, extracted builds and recovery copies
were removed. The updated app remains running with durable outputs in `dist/`.

## Prior General Settings Interpretation — 2026-10-19 (Superseded)

The owner reported the startup dropdown covering neighboring fields, requested
selectable time zones and asked what the time zone changes. Frontend profile,
general-settings lane, screen-alignment `extend` mode: retain the settings shell,
form ownership and explicit Save while changing only the two controls and help.

- Startup is a three-choice radio group. Time zones use an inline disclosure,
  city/region search and a bounded native list; opening it moves later fields
  downward instead of overlaying them. Common city labels are localized, offsets
  come from the runtime's current zone rules, and values remain named IANA zones.
- A local browser zone catalog supplies the choices, with current/system/UTC and
  common-zone fallback. Existing saved aliases remain selectable. Search filters
  do not change the pending value; no-match and save failure retain entered values.
- Source review establishes the existing time-zone impact: Session/conversation
  times, chart labels, settings sync times and Usage date ranges/calendar buckets.
  Source timestamps, usage facts/attribution, Mac clock and sync duration remain.
- Related checks: 43 UI contract tests, 20 settings/lifecycle tests and 15 Usage
  dashboard tests passed. The added UTC/Seoul midnight-boundary test confirms the
  daily bucket changes while the stored Usage row values remain identical. JavaScript syntax and diff whitespace passed.

The full repository suite was not rerun for this asset-only change. Previous
full-suite failures and broader native/teammate acceptance remain separately
recorded in the integration evaluation.

### Rendered And Packaged Checks

- Original WKWebView settings showed the startup select and free-text time zone.
  The final frozen app passed 16 interaction/layout checks at requested widths
  1100 and 320, including explicit pending selection, Korean/English search,
  no-match preservation, Escape, real API save and a completed fresh reload of
  the settings dialog. Before/after screenshots were inspected locally.
- Eight compatibility/error checks passed with the zone-enumeration API hidden:
  a saved `US/Pacific` alias remains selected; common local choices remain;
  country search works; synthetic save failure leaves the selected input intact
  and the server's prior preference unchanged. Keyboard semantics use native
  radio/list controls; the Escape handler was exercised with a synthetic key event.
- The actual app was gracefully replaced and relaunched. Authenticated local
  responses confirm health, current radio/list markup and fresh settings script.
  User settings were not modified by the synthetic checks. Only the three
  template/assets were replaced, followed by ad-hoc signing; no models downloaded.
- The current ZIP checksum and extraction checks belong to the integration
  evaluation. Broader native hardware/teammate acceptance gaps remain open.

## Dropdown Correction — 2026-10-19

The owner clarified that the startup control must remain a dropdown, with the
opened menu directly below the displayed field. The previous radio/search UI
was an agent interpretation error; its passing checks did not establish this
requested result. Current scope: Frontend profile, general-settings lane,
screen-alignment `extend` within the existing control and form visual system.

- Restored a compact startup dropdown for the existing three destinations.
  Time zone offers only literal `UTC` and `Asia/Seoul`; removed city search and
  radio choices. Menu width matches its trigger, with a four-pixel semantic
  spacing token below it; the selected control stays visible regardless of
  which option is selected. The downward disclosure cue remains stable.
- Retained explicit Save, saved/effective distinction, failure input retention,
  existing IANA values until replaced and the original application timing.
  Keyboard handling follows the select-only combobox pattern: arrows/Home/End,
  typeahead, Enter/Space/Tab selection and Escape cancellation. Outside pointer
  interaction, settings tab changes and dialog closure dismiss open menus.
- 43 UI contract, 20 desktop settings and 15 Usage dashboard tests passed.
  JavaScript syntax passed. The full suite was not rerun for this asset update.
- The actual frozen backend served synthetic data to WKWebView at measured
  1100 and 320 CSS-pixel widths. Four runs (both menus open at both widths)
  passed 24 checks each. Checks include all startup choices, below-trigger
  placement, matching width, visibility/containment, one open menu, selection,
  keyboard event handling, Escape, outside dismissal, explicit API persistence,
  dialog reopen, simulated save failure and preservation of a stored Europe/Paris
  value without adding a third selectable zone. Expanded screenshots were
  inspected; the menu is a normal dropdown overlay beneath its own control.
- Keyboard events were scripted in the native WebView; this is not a VoiceOver
  or physical keyboard acceptance claim. No real user preference was changed
  by the synthetic checks. The integration evaluation owns delivery identity
  and the separately outstanding native-control/teammate evidence.

## Four Compact Dropdowns — 2026-10-19

Owner follow-up: apply the same dropdown presentation to Project display and
Automatic sync, and shorten all four selection boxes from Startup through Sync.
Frontend/general-settings lane, screen-alignment `extend`; reuse the existing
component, menu placement, type, focus, spacing and selection treatment.

- Replaced the remaining two native selects with the existing dropdown markup
  and controller. Options and submitted field names/values stay the same.
- One semantic width role caps all four controls at 320px at the default scale,
  with available-width containment on narrow screens. The menus match each
  control; explanatory text retains its readable form width.
- Moved dropdown refresh after loading the saved sync interval/on-off value,
  so a stored 30/60-minute or off preference displays correctly on first open
  and after reopening. Explicit save and next-decision scheduling remain.
- 43 UI contract, 20 desktop settings and 24 session-sync tests passed (87 total).
  JavaScript syntax passed. No full-suite rerun is claimed.
- Six frozen-backend/WKWebView runs passed 22 checks each at measured 1100/320
  widths. Closed screens and open Project display/Sync menus were inspected.
  All four menu geometries, equal compact widths, original options, every
  selection, Escape, scripted keyboard choice, one open menu, outside dismissal,
  pending values, actual API save/reopen, off preserving the saved interval,
  re-enable and simulated save-failure retention passed. No pane overflow.
- The synthetic fixture started with absolute paths and 60-minute sync to
  exercise non-default labels. Fixture writes never touched user preferences.
  Scripted key events are not a physical keyboard or VoiceOver acceptance test.
  Current delivery identity is recorded in the functional integration evaluation.

## Fixed Home Display — 2026-10-19

The owner removed the display-choice and display-root concepts. This supersedes
the four-control/root-alias behavior above. Fullstack profile; contract/backend,
frontend and packaged integration lanes; primary agent implementation and review;
screen-alignment `extend`. Existing shell, type, spacing, menu geometry and Save
behavior were retained. The original synthetic screen was inspected before edits.

- One path-label helper shortens only the current home at a component boundary;
  it does not resolve symlinks or require the path to exist. Home is `~`; outside
  paths retain their form. Sessions/list/pins/detail, Chart, Dashboard, Context
  and read-only settings labels share it. Editing uses the original source path.
- Removed the project dropdown, root editor, controller and styles, both active
  preference keys and the environment override. Old raw TOML values stay inactive
  and survive subsequent saves; fresh settings omit them and new API writes are
  rejected. Workspace naming no longer assumes a `Projects` parent. Original
  IDs/paths and frozen Usage grouping remain. Unassigned-category redesign is
  outside this correction. General settings now have three compact dropdowns.
- Final combined relevant run: **173 tests passed**, covering settings, UI,
  Session inventory/Chart/pins, Context, Usage persistence/dashboard, internal
  usage, ingestion, sync and desktop boundary. First combined regression had
  one `st_atime`-only file comparison failure; the unchanged 24-test sync module
  and combined rerun passed. After explicit synthetic-home placeholders were
  applied for the privacy checker, all 25 settings tests passed again. No full
  suite or optional model execution rerun is claimed.
- Five synthetic WKWebView runs each passed **23 behavior/layout conditions plus
  width measurements**: source desktop mode at 1100/320, normal web mode at 1100,
  rebuilt frozen backend at 1100/320. Actual control widths were 320px/253px.
  Removal, pending/save/reopen, keyboard choice, Escape, outside/tab dismissal,
  saved off/interval retention, simulated save failure and original source editing
  passed. Session labels used `~/…`; existing `Projects` path no longer read `.`.
  Closed screens and the narrow frozen Sync menu were visually inspected.
- Initial UI probe failures were fixture defects: synthetic Escape lacked
  `cancelable`, and turning on sync removed seeded rows with no native files.
  Corrected cancelable events and synthetic native source files produced the
  passing results. These failures were not hidden by loosening geometry checks.
- Rebuilt the Python backend/resources with PyInstaller 6.22.3 and reused the
  unchanged Tauri host, then re-signed ad hoc. Full Tauri build could not find
  cargo; this correction required no native-source change. All tools came from
  the existing local caches and no model weights were downloaded.
- Updated app/ZIP published locally. The running native app passed authenticated
  health/settings, removed controls, three-control markup and fresh JS/CSS checks.
  Existing user settings and source-registration file hashes stayed identical.
  ZIP CRC, byte/mode/symlink and metadata comparisons passed; the extracted app
  passed deep strict codesign verification. Delivery identity belongs to the
  latest functional integration receipt.

Scripted events are not physical-keyboard/VoiceOver evidence. Wider native and
teammate acceptance gaps remain recorded separately; this correction does not
change the blocked whole-product route or authorize upload/publication.

Temporary synthetic servers were stopped. Task-owned build tools, npm staging,
fixtures, screenshots, extracted/recovery copies and private scratch were removed.
The published app remains running from `dist`; final deep strict codesign and
ZIP checksum checks passed after cleanup.

## Unassigned Usage Labels — 2026-10-19

Owner follow-up: the Sessions Dashboard Project row still read `Unassigned` after
the home-display correction. The earlier exclusion of this label correction is
superseded by this follow-up; logical Project unification and historical assignment
changes remain separate. Fullstack profile, backend read-model, frontend composition
and packaged integration lanes; screen-alignment `extend`; primary agent ownership.

- Preserved each nonempty frozen Project key. For missing keys, an exact retained
  `personal_insight_runs` owner plus `maintenance` / `metadata_only` Session identifies
  `앱 내부 분석` (`internal:insights`). Other records display `프로젝트 미지정`.
  The category exists only in the query result; no schema, saved attribution,
  source/model grouping, token/cost values or primary-work Session rule changed.
- Used the existing table, controls, path formatter and hidden-Insights boundary.
  A title, source name, cwd or matching prefix without its owner is insufficient.
  No artificial project, workspace or internal-analysis navigation link was added.
- **99 related tests passed** across Usage dashboard/persistence, internal analysis,
  activity attribution, UI contracts and desktop boundary. Tests include mixed
  actual/internal/unknown categories, owner/class/policy rejection, full/visible-only
  equivalence, both metrics, source/model totals, shares and read-only row preservation.
  The focused 10-test internal-usage module also passed. No full-suite rerun.
- Two pre-change synthetic WKWebView baselines at measured 1100/320 CSS pixels
  reproduced the combined `Unassigned` row. Six post-change runs at both widths
  (source desktop mode, ordinary web, rebuilt frozen backend) each passed 16 checks:
  labels, home path, group counts, dates, source/model/project and token/cost switches,
  exact source filtering, stable totals/shell, containment and no fake Project link.
  Before/after wide/narrow screenshots were inspected. Narrow tables retain their
  existing horizontal scroller; the page itself does not overflow.
- Rebuilt Python/resources with PyInstaller 6.22.3, reused the existing Tauri host
  and re-signed. ZIP CRC and every packaged file byte/mode/link matched the staged
  distribution; extracted-app deep strict codesign passed. Bundled templates/assets
  match source and contain no runtime database, JSONL or logs. No model download.
- Replaced the local app/ZIP and relaunched. Authenticated health, new Project label
  and current asset bytes passed. Existing settings/source-file hashes and retained
  previously-unassigned Usage rows were identical across the update. Synthetic
  servers were stopped; real user preferences were not used for test mutations.
- Privacy check passed for 1413 candidate files, artifact catalog is current, changed
  owner-document local links and `git diff --check` passed. Current delivery identity
  is in the [functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#project-usage-label-delivery--2026-10-19-previous).

Contract/design/functional acceptance passes for this correction. Other-Mac and
broader native acceptance remain open; no Drive upload, teammate notification or
Git publication occurred. Temporary build tools, fixtures, probes, screenshots and recovery/extracted copies were removed after verification.

Task-owned temporary artifacts are removed and all synthetic servers have exited.
The updated app remains running from `dist`; final deep strict codesign and ZIP
checksum verification passed.

## File-Owned General Settings — 2026-10-19

Owner correction: general settings should simply follow their local settings file.
This supersedes C01/C07's environment-override behavior. Fullstack profile;
shared-preferences/configuration, frontend and web/package integration lanes;
screen-alignment `extend`; primary-agent implementation and semantic review.

- General preferences now read `settings.toml`, using defaults for absent fields.
  All four former preference environment variables are ignored, including invalid
  values. Initial time zone uses system zoneinfo with UTC fallback, not process
  `TZ`. Runtime directory/authentication configuration and domain stores retain
  their existing ownership. No user data migration is needed.
- Kept the compatible API fields: `saved` and `effective` contain the same values,
  with source `saved` or `default`. Unknown TOML fields, schema errors, revision
  conflicts, atomic private writes and apply timing retain their contracts.
- General help now reads `설정은 이 Mac에 저장됩니다.`. Removed override/split-value
  rows and their controller. The three compact dropdowns, options, time-zone help,
  explicit Save, error retention and fixed home-path display remain.
- **131 related tests passed** across desktop settings, UI contracts, Session sync,
  Usage dashboard, desktop boundary, activity attribution and Session sources.
  The focused 28 settings tests also passed. Added coverage for conflicting and
  malformed legacy variables, absent-file defaults/system time zone and actual
  sync scheduling from file values. JavaScript syntax passed. No full-suite rerun.
- Two original frozen-backend WKWebView baselines passed eight expected-old checks
  each. Six final runs passed 20 checks each at measured 1100/320 widths: source
  desktop mode, ordinary web and rebuilt frozen backend. Checked file values,
  startup route, runtime sync, removed copy, compact menu geometry, pending edits,
  save/reopen, next-view time zone, off retaining the interval, simulated 409 input
  retention, retry, restored values, Escape and containment. Before/after screens
  were inspected. All test writes used private synthetic data.
- Source and frozen backends were separately restarted after saving Dashboard,
  Asia/Seoul and 30-minute sync. Each retained the saved values and unknown field,
  used the saved startup route/time zone/runtime sync, and ignored conflicting
  environment variables. No model weights were downloaded.
- Rebuilt Python/resources with PyInstaller 6.22.3, reused the existing Tauri host
  and re-signed ad hoc. ZIP CRC, every file byte/mode/link, bundled-source equality
  and extracted-app deep strict codesign checks passed. LocalBrain resources
  contain no runtime database, JSONL or logs.
- Replaced the local app/ZIP and relaunched. Authenticated health, current settings
  markup/assets, identical saved/effective values and source classifications passed.
  Real settings and Session-source file hashes and saved preferences were unchanged.
  Final installed-app deep strict signature and ZIP checksum checks passed.

Scoped contract/design/functional PASS. The full Tauri host was reused because no
native code changed; this is not a new Rust build. Physical keyboard/VoiceOver,
other-Mac, minimum-OS, optional-model and broad native acceptance were not rerun.
The product's remaining acceptance gaps are unchanged. No Drive upload, teammate
message or Git publication occurred. Current artifact identity is in the
[functional receipt](../evaluation/eval-0139-functional-standalone-test-app.md#file-preferences-delivery--2026-10-19-previous).

Privacy check passed for 1413 candidate files; catalog freshness, JavaScript syntax,
diff whitespace and 234 local link targets across 16 changed owner documents passed.
All synthetic servers exited. Task-owned tools, fixtures, probes, screenshots,
frozen/extracted builds and recovery copies were removed after confirming no
process still used them. The updated native app remains running from `dist`.

## Sync Wording — 2026-10-19

Owner request: remove `자동` from the settings term. Frontend profile, general
settings copy lane, screen-alignment `extend`. The field reads `동기화`; idle
status reads `<minutes>분 간격 동기화` or `동기화 꺼짐`. The template and controller
own this text. Options, accessible label associations, layout/CSS, stored settings,
completion-based scheduling and the explicit manual action retain their behavior.

The focused general-settings UI contract test and JavaScript syntax check passed.
One original-build baseline at 1100px and two updated-build WKWebView runs at
1100/320px passed 11 checks each: label, enabled/off/running/changed-interval status,
manual-action availability, pending value, options, menu placement/width, containment
and unchanged API preferences. Before/after wide and updated narrow captures were
inspected. The first probe failed because its async script returned an unsupported
Promise to native evaluation; returning `void` fixed that probe without changing
product code or weakening checks. All runtime fixtures were synthetic.

The current app's external template/JavaScript resources are the delivery inputs;
Python and Rust code require no rebuild for this wording change. Delivery identity
and actual-app verification belong to the functional integration receipt.

The app/ZIP were replaced locally after re-signing and archive/extraction checks.
The reopened native app passed authenticated health, exact label/current JavaScript
and unchanged real saved preferences/settings-source file hashes. The unchanged
backend and updated artifact identity are in the
[wording delivery receipt](../evaluation/eval-0139-functional-standalone-test-app.md#sync-label-delivery--2026-10-19-previous).

Privacy check passed for 1414 candidate files; catalog, diff whitespace, installed
app signature and ZIP checksum checks passed. All synthetic processes exited and
task-owned probes, data, screenshots, staged/extracted builds and recovery copies
were removed after an active-use check. The updated app remains running.

## Successor Project Scope — 2026-10-20

The owner replaced the internal-analysis Project category with work-only composition
and kept By Project / Project labels. [Run 179](run-20261020-179-work-session-project-usage.md)
executes the corrected [SPEC-0134](../spec/spec-0134-general-and-project-settings.md).
Earlier evidence here remains historical; overall/native/recipient acceptance gaps
retain their recorded scope.
