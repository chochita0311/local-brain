# EVAL-0139: Settings And Shared Product Surfaces

## Metadata

- ID: `eval-0139`
- Status: `complete`
- Evaluator Type: `design`
- Result: `FAIL` for complete native acceptance; rendered browser checks passed
- Run: [RUN-177](../run/run-20261018-177-standalone-test-app-delivery.md)
- Feature: [FEAT-0139](../feature/feat-0139-standalone-test-app-delivery.md), integrating FEAT-0132–0138/0140
- Spec: [SPEC-0139](../spec/spec-0139-standalone-test-app-delivery.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: browser UI and interaction; native shell evidence separately bounded
- Evidence Coverage: `partial`
- Created: `2026-10-18`

## Current Reading Scope — 2026-10-26

The initial Design/Interaction Review below records the 2026-10-18 implementation.
Later dated receipts supersede its optional-home, saved/effective-value and status-card
presentation. Current rules belong to the settings policy and constitution; the
[session closeout](eval-0139-functional-standalone-test-app.md#session-closeout--2026-10-26)
records the latest source checks and independent documentation reviews. Historical
rendered evidence does not establish physical native input or recipient acceptance.

## Design Review

Applied `screen-alignment` in **extend** mode. The repository constitution and
existing shell/form tokens own typography, neutral surfaces, borders, focus and
spacing. ChatGPT-like categories inform the settings layout; no unrelated visual
system or exact screenshot parity was claimed.

Checked rendered settings at 1280 and 390 pixels and geometric containment at
320/390/1280. The wide category rail becomes a horizontally scrollable tab strip;
body scrolling stays inside the modal. Long synthetic paths stay within fields
and cards. Source/error/model/storage categories retain the same component family
as the existing Sessions/Context shell. Loading, successful data load, validation
failure, empty registration and missing-model entry were inspected. No outer
horizontal overflow or JavaScript page error occurred in the checked routes.

## Interaction Review

- Gear and browser shortcut open the categorized modal; Escape closes it and
  browser dialog focus returns to the trigger.
- Failed overlapping-source submission retains inputs. Editing/registration
  always distinguishes actual Session root from the optional agent home.
- Background sync preserves the typed search value and active input; explicit
  refresh retains the current URL scope. General settings show persisted/effective
  values and application timing, plus recent attempt/success/next sync state.
- Keyword result → original evidence → results retains the query and mode.
- List, Chart, Projects, Dashboard, Context and both search modes were revisited
  after saved Project and time-zone changes, at wide and narrow browser widths.

## Evidence Limits And Route

Browser evidence uses synthetic data and the same packaged templates/assets. A
visible native Tauri window and its lifecycle were observed, but macOS did not
permit app-window capture or Accessibility automation. Native menu shortcuts,
red-close/Dock restoration and file choosers still need direct owner/recipient
confirmation. Browser evidence does not substitute for those native interactions.
Complete UI acceptance remains open under PRD A04/A06/A12. The
[functional receipt](eval-0139-functional-standalone-test-app.md) owns the full
runtime matrix and the teammate handoff boundary. Temporary screenshots are not
published or retained as product assets.

## Startup Repair Evidence — 2026-10-19

[FIX-0131](../fix/fix-0131-desktop-startup-cookie.md) adds a directly rendered
WKWebView snapshot of synthetic onboarding and scripted settings open/close,
after reproducing the initial first-page authentication failure. The original
system screen-capture limit remains, but the WebView's own snapshot API supplies
this bounded rendering evidence. The owner also confirmed the actual repaired
Tauri app shows its normal screen. Native choosers, menu/close/Dock interactions
and recipient permissions retain their separate evidence gaps.

## Common Sync Strip Removal — 2026-10-19

User-directed Frontend/common-shell cleanup, screen-alignment `extend` mode.
The shared strip and update link were removed without replacement chrome.
Synthetic WKWebView snapshots of Sessions (requested 1100/320 widths), Sessions
Dashboard and Context show the header adjoining the main content without the
old strip's empty band. Navigation/search and the Sessions manual button remain.
Twelve rendered/API/interaction checks passed per run, including running and
completed controls in the open settings dialog with synthetic sync responses.
Query input survives status updates. The [Run](../run/run-20261018-178-periodic-local-session-sync.md)
records test scopes and the packaged asset update. These observations establish
this narrow display change, not the remaining native-control or teammate gaps.

## Prior General Settings Interpretation — 2026-10-19 (Superseded)

The previous agent interpretation used Frontend/general-settings refinement, screen-alignment `extend`.
The startup field now has three visible radio choices. The time-zone disclosure
uses a searchable native list in normal form flow; neighboring fields move down
instead of being covered, and short result sets shrink the list to two rows.
The current selection and the effect on displayed times/calendar grouping remain
visible. Existing shell, Save ownership and environment overrides are retained.

Synthetic WKWebView comparisons at requested 1100/320 widths passed sixteen
checks each, including neighbor geometry, containment, pending-value preservation,
selection, save and completed dialog reload. Eight fallback/error checks also
passed. Expanded and closed states were inspected locally. The
[general-settings Run](../run/run-20261018-172-general-and-project-settings.md)
records input, API and keyboard-evidence limits. The actual packaged app was
restarted and its current markup/assets confirmed over authenticated loopback;
this does not add a teammate or native file-chooser acceptance receipt.

## Corrected Dropdown Evaluation — 2026-10-19

The owner wanted the original startup dropdown restored and its expanded menu
placed below the displayed control. The prior radio/search implementation was
an interpretation failure; its geometry checks do not satisfy that request.
Current Frontend/general-settings evaluation keeps the dropdown interaction and
limits time-zone choices to the literal `UTC` and `Asia/Seoul` values.

Four synthetic WKWebView runs against the frozen app backend passed 24 checks
each at measured 1100/320 widths, with both startup and time-zone menus captured
open. All startup selections keep the menu below its trigger, separated by the
existing four-pixel compact spacing token, with equal width and an unobscured
trigger. Snapshots confirm stable downward cues, selected checkmarks, readable
options, menu containment and no horizontal overflow. Following fields may sit
behind the ordinary dropdown overlay; the owning selected control remains visible.

Selection closes the menu. Only one menu opens at a time. Escape cancels;
outside interaction and dialog closure dismiss. Scripted arrows/Home/End,
typeahead, Enter/Space/Tab, API save/reopen, simulated failure retention and
preserving an existing non-listed IANA value passed. Saved/effective precedence
and application timing are unchanged. The UI contract test now checks the
requested dropdown structure rather than the superseded radio/search design.

Keyboard semantics were checked against the
[W3C select-only combobox guidance](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-select-only/).
Native WebView scripted events and screenshots do not establish VoiceOver,
physical keyboard or unrelated native-shell acceptance. This narrow correction
passes its design/interaction checks; broader native/teammate gaps remain as
recorded above. The reusable requested-control preservation rule is in
[Design Evaluation](../../policies/design/design-evaluation.md#requested-control-preservation).

## Four Compact General-Settings Controls — 2026-10-19

Frontend/general-settings, screen-alignment `extend`: Project display and
Automatic sync now use the same dropdown as Startup and Time zone. The four
boxes share a compact maximum of 320px at the default scale, shrinking within
narrow panes. The previous full-width controls and two different menu types are
replaced; surrounding labels/help and the settings shell retain their roles.

Six synthetic WKWebView runs passed 22 checks each at measured 1100/320 widths.
Closed screens and both newly converted menus were visually inspected. Every
option in all four controls retains below-trigger/equal-width placement and an
unobscured trigger. Long relative-path wording fits, selection checkmarks and
arrows remain aligned, and open/closed states have no horizontal overflow.
Selection dismissal, Escape, scripted keyboard choice, one-open-menu behavior,
API save/reopen, non-default/off labels, off retaining the interval, re-enable
and simulated save-failure retention passed. The shared controller is reused;
keyboard and wider native acceptance limits remain as recorded above.

## Fixed Home Display Presentation — 2026-10-19

User correction: remove the Project display field and display-root editor; home
abbreviation is a shared rule. Fullstack/general-settings and path-label lanes,
screen-alignment `extend`. Compared original/current synthetic WKWebView renders
and preserved the settings shell, tokens, title hierarchy, controls and spacing.
The deletion leaves Startup, Time zone and Automatic sync, with 320px wide controls
and 253px actual widths in the 320px viewport. No replacement path preference or
configuration explanation was inserted into the product flow.

Five source/web/frozen runs each passed 23 behavior/layout conditions and recorded
widths. Menu placement/matching width, containment, single menu, keyboard event
choice, Escape/outside/tab dismissal, pending/save/reopen, off retaining interval,
failure input retention and original source editing passed. Closed wide/narrow
views and the narrow frozen Sync menu were visually inspected. Path shortening
retains its suffix and distinct folders; no information is inferred from missing
paths. Read-only path labels and actual editing values remain distinct.

Fixture corrections, rebuilt backend and live native verification are recorded
in C07 and the functional receipt. No new design drift or interaction defect
remains in this checked correction. Scripted events are not physical-keyboard or
VoiceOver validation; the wider native/teammate acceptance limits remain open.


## Project Composition Labels — 2026-10-19

Scoped PASS; Fullstack read-model/composition/integration lanes, screen-alignment
`extend`. The existing Project table now distinguishes `앱 내부 분석` from
`프로젝트 미지정`; actual paths retain home abbreviation. Template, controls, type,
spacing and styling were reused. Source/model views do not show Project categories.

Two original-build and six post-change synthetic WKWebView runs at measured
1100/320 CSS-pixel widths each passed 16 conditions appropriate to their baseline
or corrected expectation. Source/model/project, exact source and token/cost switches
preserved dates, summary and shell. Wide/narrow before/after captures were inspected;
labels fit the existing identity column, and narrow overflow stays inside the table
scroller. No fake project action or hidden-Insights navigation was introduced.
This evidence does not establish physical-input or other-Mac acceptance.

## File-Owned General Settings Presentation — 2026-10-19

Scoped PASS; Fullstack shared-preferences, frontend and web/package integration
lanes, screen-alignment `extend`. The owner's latest correction supersedes earlier
claims here that environment precedence remains. The help now reads only
`설정은 이 Mac에 저장됩니다.`; per-field saved/applied-value rows were removed.
Startup, Time zone and Automatic sync retain their existing compact dropdowns,
options, below-trigger menus, Save action, shell, typography and spacing.

Two original frozen-backend baselines reproduced the old override presentation.
Six final source-desktop/ordinary-web/frozen-backend WKWebView runs at measured
1100/320 CSS-pixel widths passed 20 conditions each. They cover initial file values,
removed copy, matching menu geometry, pending/save/reopen, runtime sync changes,
next-view time-zone application, off preserving the interval, conflict-error input
retention, retry, Escape and page/panel containment. Wide/narrow before-and-after
captures were inspected; the shorter help and absent extra rows preserve hierarchy
without introducing new controls. Final frozen captures were also inspected with
the pane scrolled to its top.

The actual app's settings markup and served assets match the corrected source.
Scripted events do not establish physical-keyboard or VoiceOver acceptance; other
native and teammate evidence gaps retain their prior status.

## Sync Wording — 2026-10-19

Scoped PASS; Frontend/general-settings copy lane, screen-alignment `extend`.
The owner-selected `동기화` replaces `자동 동기화` in the field and its interval/off
status. Existing controls, choices, help, accessible names, spacing and CSS remain.
One original baseline and two updated WKWebView runs passed 11 checks each at
1100 / 1100,320px. Wide before/after and narrow after screenshots were inspected:
the shorter label fits the same hierarchy, controls remain contained and menus
retain below-trigger matching-width geometry. Running status, explicit manual
action availability, pending values and API settings were preserved. No new
physical-keyboard, VoiceOver or other-Mac acceptance is implied.

## Compact Settings Dialog — 2026-10-19

Scoped PASS; Frontend/settings-shell geometry and interaction lanes,
screen-alignment `extend`. The owner's size correction reduces the maximum from
992×800 to 720×560 CSS pixels, with a 160px desktop category rail. Existing type,
control sizes, colors, radius, elevation and dropdown options remain. Reduced
spacing uses existing roles; the 700px breakpoint matches the shared shell.
Header/close stays fixed, content scrolls, category changes start at the top without
clearing pending values, and save/error feedback is made visible.

One baseline and five final WKWebView runs provide before/after evidence: frozen
backend at 1440×900, 900×450, 700×650 and 320×650; ordinary web at 1100×800. Each final
run passed 23 conditions including all six categories, scroll containment, bottom
reachability, menu bounds, pending/save/reopen, focus return and error/retry. The
wide before/after, short, breakpoint, narrow and source-web screenshots were
inspected. Text remains legible and aligned, and the smaller surface avoids the
previous excess space without discarding controls or help.

The [settings-shell Run](../run/run-20261018-170-settings-and-product-navigation.md#compact-settings-dialog--2026-10-19)
records the feedback correction and probe adjustments. Scripted events and
synthetic WKWebView screenshots do not establish physical input, VoiceOver or
other-Mac acceptance; those wider evidence limits remain unchanged.

## Work Session Project Scope — 2026-10-20

Scoped Design/Interaction PASS for [Run 179](../run/run-20261020-179-work-session-project-usage.md).
Fullstack profile; backend membership, frontend copy and package lanes. Applied
screen-alignment `extend` against the constitution and existing composition table.
The shell, controls, table columns, disclosure and By Project / Project labels stay.
One Project-only sentence explains ordinary work plus subsessions and shows its
compatible metric total; a Maintenance-only selection has a work-specific empty
state while overall usage remains visible. Existing caption/color/panel spacing
roles provide the treatment; no new visual component or reusable law is needed.

Synthetic old-app baseline at 1100/320, ordinary web at 1100/320 and updated frozen
backend at 1440/920/700/320 were rendered. Each updated run passed 18 checks for
scope/name/content, Cost/Tokens, Source/Model, source-only Maintenance, date retention,
settings open/close, return to All and containment. Wide/narrow captures were
inspected; the existing narrow table scroll remains inside its panel. State changes
use the existing GET/Ajax controls, focus restoration and live announcement.
This is scripted WKWebView evidence, not physical keyboard, VoiceOver or all native
controls. Broader recipient/native evidence remains separately unresolved.

## Project Notice Removal — 2026-10-20

Scoped Design/Interaction PASS for [Run 180](../run/run-20261020-180-project-copy-removal.md).
Frontend profile, Project composition copy lane, screen-alignment `extend`. The owner
removed the explanatory paragraph and separate total added in Run 179. The heading
and existing Source/Model/Project controls now directly precede the table, matching
the existing composition family. Removed the paragraph's unused spacing/style rule.
Membership, labels, row values, shares, disclosure and empty state are retained.

Original frozen baseline at 1100/320 and updated ordinary web/frozen backend at
1100/320 passed eight checks each: notice state, adjacency, names, Project values,
overall totals, containment, scope switching and settings open/close. Baseline and
updated wide/narrow captures were inspected. This is scripted WKWebView evidence;
physical-input, VoiceOver and broader native/recipient acceptance remain separate.


## Pinned Scroll Containment — 2026-10-20

[Run 181](../run/run-20261020-181-pinned-scroll-containment.md), Frontend profile,
Pinned Sessions scroll-containment lane, screen-alignment `extend`.
**Design/Interaction result: PASS for this correction; coverage: scoped.**

The original frozen long-pin fixture scrolls into a completely blank viewport
below the shell. The corrected screen ends at the visible content plus its
existing page inset. The scroller's containing block is the only styling change;
no labels, rows, controls, spacing tokens, fonts or data projections were removed.
Wide nested scrolling and narrow document flow retain all 47 synthetic pins.
Before/after wide and corrected short-main/narrow snapshots were inspected.

Nine ordinary-web/frozen WebKit cases cover 1280/920/700/320px with empty, short
and overflowing panels, short/long primary lists, bounded document and panel
scrolling, last-pin reachability, label retention, inventory switching and
settings. Seven first-page cases cover in-place pin refresh and scroll/focus
continuity. The functional receipt records exploratory fourth-page pin timeouts;
those do not establish paginated pin continuity. Scripted scrolling is not a
physical-input or VoiceOver check. Actual running-backend bounds and artifact
identity are in the [functional receipt](eval-0139-functional-standalone-test-app.md#pinned-scroll-containment-delivery--2026-10-20-superseded-artifact).

## Apply-Timing Copy Removal — 2026-10-20

Scoped Design/Interaction PASS for the [general-settings follow-up](../run/run-20261018-172-general-and-project-settings.md#apply-timing-copy-removal--2026-10-20).
Frontend profile, copy lane, screen-alignment `extend`. Remove the redundant
timing paragraph and shorten success feedback. Existing three controls, order,
labels, time-zone impact help, geometry, tokens and explicit Save remain. The
removed paragraph's space closes naturally; no CSS or screen-shell change.

Original and revised synthetic settings at 1100/320 widths were rendered and
captures inspected. Each of four cases passed 16 checks covering copy, menu
containment/selection, pending values before Save, saved/reopened values,
close/focus, retained help/order, viewport containment and unchanged active-view
versus next-view time-zone timing. Narrow focus uses the existing keyboard
shortcut from a visible input; physical keys and VoiceOver were not evaluated.
The actual restarted backend served the new markup/script and passed the six
startup checks. The [functional receipt](eval-0139-functional-standalone-test-app.md#apply-timing-copy-removal-delivery--2026-10-20-superseded-artifact)
owns the artifact identity and broader evidence limits.

## General Settings Autosave — 2026-10-20

Scoped Design/Interaction PASS for [Run 183](../run/run-20261020-183-general-settings-autosave.md).
Frontend profile, general-settings interaction lane, screen-alignment `extend`.
The separate general Save button and sync status/timestamp/manual-action card
are removed. Three compact choices, order, help, shell, tokens and source-form
Save remain. Committed choices save quietly; failed saves explain stored-value
recovery. Busy choices cannot race or steal focus from another active category.

Original frozen wide/narrow cases passed five baseline checks each. Four updated
ordinary-web/frozen cases at 1100/320 widths each passed 34 checks: pointer and
keyboard save, highlight/Escape/no-op, matching dropdown geometry, single-field
patching, sync off/interval retention, busy state, close/reopen, ordinary failure,
revision conflict, ambiguous response and failed-readback recovery, focus and
viewport containment. Active-view time zone/navigation remain unchanged while
the next view uses the saved zone. Before/after synthetic captures were inspected.
Scripted keyboard checks do not establish physical-input or VoiceOver acceptance.

## First-Use Overlay Wizard — 2026-10-23

Scoped Design/Interaction PASS for [Run 184](../run/run-20261023-184-first-use-overlay-wizard.md),
Fullstack profile, `screen-alignment` extend. The old frozen welcome page and
settings dialog were captured before editing. Synthetic current welcome, source
and search renders were compared with that family at 1100/320 widths. The actual
startup surface stays behind the centered 720×560 maximum dialog; existing
surface, scrim, typography, spacing, control and responsive tokens are reused.
The category rail becomes four numbered steps, with a stable footer and a
scrolling content pane. Narrow progress labels stack beneath their numbers.

The source/frozen layout probes passed 224 assertions: modal/background isolation,
step heading focus and current-step semantics, viewport/scroll bounds, visible
footer, actual main content and optional empty/model-free state. Behavioral
probes cover Back draft retention, Next save/validation, explicit Skip/Later,
completion persistence/conflict/readback, load retry and general-settings
regressions. A final review fixed Next after choosing a previously removed source;
source and frozen behavioral reruns confirm re-registration. Loading disables
step transitions, errors keep the entered data and current step, and the final
handoff refreshes the chosen startup surface.

Scripted clicks, focus attempts and a dispatched cancel event verify browser
behavior; they do not establish physical Tab/Escape, VoiceOver or native picker
operation. Existing broader native/recipient acceptance stays separate. The
[functional receipt](eval-0139-functional-standalone-test-app.md#first-use-overlay-wizard-delivery--2026-10-23-superseded-artifact)
owns counts, final app/ZIP identity and startup evidence. No new visual debt was
introduced in this scoped comparison; inherited family details outside the wizard
were preserved.

## Onboarding Visual Refinement — 2026-10-23

Scoped Design/Interaction PASS for [Run 185](../run/run-20261023-185-onboarding-visual-refinement.md),
Frontend profile, `screen-alignment` adapt. Rendered Tesla hero/carousel controls,
the existing wizard and regular settings were compared. The direction is quiet
hierarchy, bottom progress and coherent motion; LocalBrain's 720×560 maximum,
neutral surface, SF-oriented type, warm primary action, radii and spacing remain
authoritative. Four real steps use four bottom indicators with accessible names
and shape/tone for the active step. They do not bypass save/skip actions.

The header loses its heavy separator and top numbered strip. Welcome content is
centered with a larger existing brand mark; source fields use two columns at
desktop width and one on narrow screens. Redundant empty-list/form titles are
hidden only in onboarding; existing entries, field labels, candidates, help,
errors and model actions remain. Regular settings retain their categories and
autosave. A discovered CSS conflict that exposed the hidden reconnect checkbox
on new sources was corrected in the shared form rule.

Transitions crossfade over the shared 240ms overlay duration with a 16px spacing-
token offset. The outgoing pane preserves its scrolled position; both panes are
inert during handoff, navigation is disabled, and focus moves to the incoming
heading afterward. Reduced motion swaps immediately. At 320px, the old final
button label wrapped the footer; the concise `시작하기` label fixes this observed
failure. The corrected footer stayed stable across all four steps.

Source and packaged WKWebView each passed 43 checks at 1100×800, 320×720 and
700×480 (258 checks combined). Chromium passed 43 normal-motion and 33 reduced-
motion checks. These cover geometry, current-step/focus semantics, isolation,
scroll/overflow, intermediate crossfade frames, duplicate moves, draft retention
and no model side effects. Separate browser behavior checks confirm failed source
validation retains input, Next saves real synthetic source/document registrations,
failed completion keeps the modal open and ambiguous successful completion is
confirmed by readback. Settings autosave and below-control dropdown placement
remain operational. Browser-driven Tab/Shift+Tab and Escape checks exercise the
native dialog; an initial assumption of one-key Tab wrapping at browser chrome
was not counted as a product failure or passing containment assertion.

Actual views were inspected at wide/narrow sizes. This is a directional adaptation,
not Tesla pixel matching. No external image/font/theme or auto-advance is imported.
Physical native input, VoiceOver, Notes permission dialogs, Finder pickers and
recipient-Mac acceptance retain their previous limits. The functional receipt
owns final artifact identity, running-app checks and saved-file preservation in
the [delivery section for that revision](eval-0139-functional-standalone-test-app.md#onboarding-visual-refinement-delivery--2026-10-23-superseded-artifact).

## Session Profile Presentation — 2026-10-23

Scoped Design/Interaction PASS for [Run 186](../run/run-20261023-186-session-source-presentation.md),
Frontend profile, `screen-alignment` adapt. Inspected the actual Apple iPhone Duo
page, including its short section hierarchy, generous spacing, grouped surfaces
and a detail disclosure opened from a named feature. Compared the existing
synthetic three-profile setting with the revised overview, editor and first-use
Session step. The reference supplies hierarchy and progressive detail; existing
LocalBrain dialog bounds, fonts, controls, surfaces, spacing and four-dot wizard
navigation remain authoritative. No promotional imagery, pill buttons or new
visual theme is imported.

The overview now groups compact name/path rows with one Edit entry each. Add is
separate; repeated healthy `ready` text and the introductory paragraph are removed.
Provider labels appear when they add information to a custom profile name.
Unavailable/configuration/scan errors and unregistered retained profiles remain
visible. The editor prioritizes tool, required name and Session folder. Optional
agent home is disclosed separately; collection scope/original preservation is
explained beside the Session path. Removal lives in Edit with its existing
consequence confirmation. Candidates do not repeat represented paths and remain
prefill-only. Cancel replaces Input reset with an explicit return to the overview.

Source WKWebView passed 100 layout checks across 1100×800, 320×720 and 700×480;
packaged WKWebView passed 161 checks across regular settings and onboarding at
the same dimensions. Chromium passed 67 wide/narrow layout checks. Synthetic
variants cover three profiles, empty/discovery state, long names/paths, warnings,
scan errors and retained registrations. Three ordinary-length profiles fit the
wide initial viewport; long data can scroll within the bounded pane. Add/Edit,
advanced details, Save and the last profile remain reachable; focus returns to
the source entry or overview after Cancel/Save. The wizard footer remains stable.

Two browser behavior runs (Chromium/source and WKWebView/frozen) each passed 30
checks using actual synthetic source mutations: required/invalid/overlapping
paths, retained drafts/errors, busy exclusion, add/rename, confirmed reconnection,
removal cancel/accept and stable-ID re-registration. Eight Chromium wizard checks
confirm Back draft retention, Skip without registration, Next save/advance,
cleared editor, stable footer, heading focus and no model activity. Additional
browser checks cover general autosave, resetting confirmation when its target
changes, and Enter/Tab keyboard interaction.

An initial CSS name collision exposed unrelated path/status styling; the new
component classes were isolated before final evaluation. The first native probe
returned a Promise type unsupported by its evaluation bridge; adding a void
result fixed the probe and the rerun passed. Neither was counted as passing
evidence. Discovered candidates and displayed home paths use synthetic fixtures
in the frozen browser probes; source mutations still reach the actual backend.
Physical native input, VoiceOver, Finder pickers and recipient-Mac acceptance
retain their existing limits. The functional receipt owns final delivery identity
and real configuration preservation in the
[current delivery section](eval-0139-functional-standalone-test-app.md#session-profile-presentation-delivery--2026-10-23-superseded).

## Compact Shared Settings — 2026-10-23

**Scoped PASS**, Fullstack Product; `screen-alignment` extend.
[Run 187](../run/run-20261023-187-settings-control-consistency.md) records the
rendered baseline and consistency list. Existing constitution, current source
list and dialog family govern; no new external visual system is imported.

- Startup options match sidebar order while preserving the saved choice. General
  selectors shrink from 320×40 to 240×32px on desktop; narrow controls use 40px.
  Input/action type, spacing and border/radius roles stay shared. The selected
  timezone sentence is removed while impact help remains.
- Tool and profile-name controls match size and alignment. Tool/Context selectors
  open below their triggers, including short-window scroll adjustment. Action
  text is centered. Source category navigation returns to the list; wizard Back
  retains drafts and form authority remains explicit.
- Context and storage use grouped rows with quieter path/size metadata. Model
  information/actions are grouped; restore and model storage details use
  disclosures. Required restore consequences, source ownership and model download
  authority remain available at the action. No large full-width submit bars.
- Inspected synthetic general, editor, Context, model and storage renders, plus
  wide/narrow/short Chromium and WKWebView geometry and interactions. General
  dropdowns, source fields, buttons, long synthetic paths, scrolling, restore
  confirmation, keyboard Enter and wizard Back/Skip passed their scoped checks.
  No horizontal overflow or menu clipping in those cases. Original host and
  navigation geometry remain stable; wider product/native accessibility and
  recipient-Mac acceptance are not implied by this pass.

Exact validation and delivered artifact identity belong to the
[current functional receipt](eval-0139-functional-standalone-test-app.md#compact-settings-delivery--2026-10-23-superseded).

## Sync Checkbox And Presets — 2026-10-24

**Scoped PASS**, Frontend Product, screen-alignment extend.
[Run 188](../run/run-20261024-188-sync-checkbox-and-presets.md) uses a checkbox for
the single enabled flag and the existing compact selector for 10/20/30/60 minutes.
The enabled label is clickable; the unchecked selector stays visible and disabled
with its saved value. The range/runtime sentence and former input/button are gone.
Other general controls and the settings shell retain their geometry and behavior.

Rendered wide/narrow Chromium and wide/narrow/short WKWebView checks confirmed
240px maximum width, 32/40px controls, readable checkbox/selection, menu visibility
below the trigger, keyboard selection/Escape and no horizontal overflow. All four
choices persisted as numbers. Disabled and failed-save states remained truthful;
no automatic replacement of legacy values. The existing shared component and
native checkbox introduce no separate design system. Exact checks and artifact
identity belong to the [functional receipt](eval-0139-functional-standalone-test-app.md#sync-checkbox-delivery--2026-10-24-superseded).

## About Identity — 2026-10-24

**Scoped PASS**, Fullstack Product, screen-alignment adapt.
[Run 189](../run/run-20261024-189-about-identity-and-version.md) uses the supplied
desktop dialog only for icon/name/version hierarchy. Existing LocalBrain mark,
type, color and spacing tokens govern; no reference image, license text or foreign
branding is copied. Operational paragraphs are removed; the user guide retains
that guidance. The shared compact settings shell and navigation remain unchanged.

Inspected wide/narrow renders and 36 Chromium plus 54 frozen WKWebView checks
at wide/narrow/short sizes. The 64px mark sits beside the name and quieter v0.0.1;
no horizontal overflow or clipped identity. Tab switching, close/focus and reopen
remain functional. General synchronization controls and saved values are retained.
A probe's hidden narrow-screen trigger was corrected without a product change.
Broader native/accessibility/recipient acceptance is not implied. Exact artifact
identity belongs to the [functional receipt](eval-0139-functional-standalone-test-app.md#about-identity-delivery--2026-10-24-superseded).

## Dedicated Sync Category — 2026-10-24

**Scoped PASS**, Fullstack Product, screen-alignment extend.
[Run 190](../run/run-20261024-190-sync-settings-and-context-schedule.md) moves
scheduling from General into Sync after Search model and before Storage. Session
and Local Context use matching labeled fieldsets, Use checkboxes and 10/20/30/60
selectors. The unchanged shell, type/spacing roles, 240px maximum control width,
32px desktop and 40px narrow heights govern both groups. No status/time card,
manual settings action or deferred AI-index placeholder is exposed.

Chromium/source and WKWebView/frozen each passed 117 checks at 1100×800, 320×720
and 700×480. Presets persist independently; off preserves minutes and disables
the menu, legacy custom values remain visible, errors restore stored values and
lost-response saves are confirmed. Category order, tab transitions, menus below
their triggers, containment, close/focus and reopening passed. Seven additional
Chromium wizard checks confirm hidden settings navigation/Sync, background isolation,
step progression and no model action. Rendered wide and short layouts were inspected.

The first native probe used non-cancelable synthetic Escape events, which could
close the dialog despite the menu handler. Realistic cancelable events passed;
no production keyboard behavior was changed for that probe. Physical native input,
VoiceOver, Notes permission dialogs and recipient-Mac acceptance remain outside
this scoped pass. The functional receipt owns final delivery identity.


## Single Sync Select — 2026-10-24

**Scoped PASS**, Frontend Product, screen-alignment extend.
[Run 191](../run/run-20261024-191-single-sync-select.md) removes each Use checkbox
and adds Off after 10/20/30/60 in the shared below-trigger selector. Each Sync
control/menu is 160px maximum with existing 32px desktop/40px narrow height,
font, disclosure and selected checkmark. General remains 240px maximum. The shell,
category order and source editor are retained; source helper text no longer
suggests collecting primary sessions only.

Rendered baseline/final wide and narrow panes were inspected. Chromium/source
and frozen WKWebView each passed 156 wide/narrow/short checks for selection,
autosave, atomic resume, independent groups, disabled-on-write, legacy values,
failed/lost-response saves, keyboard/Escape, focus, reopen and containment.
Off stays selectable so the user can resume through the same control. No model,
status card or deferred AI-index control is added. Home-first registration remains
a proposed follow-up. Physical input and broader accessibility/recipient acceptance
retain their limits. The [functional receipt](eval-0139-functional-standalone-test-app.md#single-sync-select-delivery--2026-10-24-superseded)
owns exact artifact identity and test scope.


## Home-First Source Editor — 2026-10-24

**Scoped PASS**, Frontend Product, screen-alignment extend.
[Run 192](../run/run-20261024-192-home-first-source-editor.md) keeps the profile
list and form family while promoting agent home, showing a short derived-path
readout and disclosing custom record locations. Existing overrides open visibly;
reset returns to the default path explicitly. Redundant source-only explanations
are removed. Sync width follows label/disclosure/marker content (about 79px),
retaining 32px desktop and 40px narrow controls and matching below-trigger menus.

Rendered baseline/final wide and narrow views and 156 checks in each browser/runtime
confirmed field alignment, path wrapping, menu containment, independent Sync saves,
error retention, safe legacy/custom paths, draft reset, reconnection and wizard
continuity. A saved 1440-minute label expands without wrapping. The same tokens,
settings shell, category order and source overview remain. Physical native input,
VoiceOver and real picker dialogs remain outside this scoped pass. Exact delivery
identity and probe corrections belong to the [functional receipt](eval-0139-functional-standalone-test-app.md#home-first-source-delivery--2026-10-24-superseded).


## Profile List Actions — 2026-10-24

**Scoped PASS**, Frontend Product, screen-alignment extend.
[Run 193](../run/run-20261024-193-profile-list-actions.md) retains the settings
family and source overview while using English field labels and red textual
required markers. Home's marker follows actual optionality under a custom root.
Each registered row has padded Edit/Unregister buttons, with actions below identity
on narrow screens. The editor no longer contains removal.

The compact confirmation names the profile and explains retained records. Cancel
owns initial focus; Cancel/Escape writes nothing, Confirm binds the reviewed source
and revision, busy actions prevent duplicates, and errors stay in the modal.
Explicit parent inertness fixes a reproduced WKWebView focus escape. Close returns
focus to the source action, including the replacement re-registration button.
Same-tab selection discards Add/Edit drafts; wizard Back/Next/Skip keep their
established behavior. Shared colors, typography, 16px inline padding, 32/40px
control heights and responsive containment passed rendered and measured checks.

The [functional receipt](eval-0139-functional-standalone-test-app.md#profile-list-actions-delivery--2026-10-24-superseded)
owns exact checks and artifact identity. Physical native input, VoiceOver, real
picker/Notes permissions and recipient-Mac acceptance remain outside this pass.


## Compact Profile Controls — 2026-10-24

**Scoped PASS**, Frontend Product, screen-alignment extend.
[Run 194](../run/run-20261024-194-compact-profile-controls.md) uses existing label
and control-gap roles to reduce row action widths while retaining shared heights,
separate targets, focus, confirmation and narrow stacking. Profile name hints follow
the selected tool without changing user input, persisted names or required checks.
Rendered baseline/final comparison and 83 source/frozen assertions per runtime
support width reduction, responsive containment, provider switching, label saving
across filters, same-tab reset and confirmation/cancel focus. At this Run, ordering
still followed DB IDs; Run 195 below supersedes that behavior with TOML-array order.
The [functional receipt](eval-0139-functional-standalone-test-app.md#compact-profile-controls-delivery--2026-10-24-superseded)
owns final artifact identity and wider native/accessibility evidence limits.

## Generalized Session Profiles — 2026-10-24

**Scoped PASS**, Fullstack Product, screen-alignment extend.
[Run 195](../run/run-20261024-195-generalized-session-profiles.md) keeps the settings
shell, compact actions, row typography and responsive layout. A small handle owns
reordering; the existing provider badge opens a six-color palette below the row.
Provider still determines CX/CL, while profile color uses shared semantic surface
and foreground tokens. Selected marks, accessible names and focus make color
selection usable beyond color alone. No ID-management form is added.

Drag/drop or Up/Down on the focused handle saves TOML-array order. All stays first;
both profile filter surfaces share the saved order, name and color. Rerendering
returns focus to the initiating handle/color control and retains the selected
profile. Chart metadata/cues update without resetting the selected session or
camera; mixed-profile stacks remain neutral. Revision conflicts restore saved
presentation, and a lost successful response is read back without duplicate writes.
The existing editor reset and named removal confirmation remain functional.

Source Chromium checks cover these interactions, chart selection, dashboard scope
and detail cues. The final frozen WKWebView passes 24 interaction assertions and
11 geometry assertions at each of 1100×800, 320×720 and 700×480. Inspected baseline
and final renders support visual continuity; measurements confirm below-trigger
palette placement, containment, reachable content, usable targets and Escape/focus.
A reproduced color-trigger focus loss was fixed before the final passing runs.
The [functional receipt](eval-0139-functional-standalone-test-app.md#generalized-session-profiles-delivery--2026-10-24-superseded)
owns the artifact and actual startup evidence. Physical native drag/key input,
VoiceOver, real picker/Notes permissions and recipient-Mac acceptance remain outside
this scoped pass; scripted WebView events do not establish those broader claims.

## Independent Profile Rows And Color Tags — 2026-10-25

**Scoped PASS** for [Run 197](../run/run-20261025-197-profile-settings-presentation.md),
using screen-alignment `adapt` and the Fullstack profile. The rendered current
screen had one rounded enclosure/shared dividers and Session-style CX/CL buttons.
The owner's [Notion reference](https://www.notion.com/ko) provides direction for
light, independently movable rows; LocalBrain retains its shell, tokens, data
and supported controls. No marketing layout or external assets are imported.

The source list now has no enclosing border/radius, an 8px row gap, quiet row
hover/focus surfaces, visible grab handles and a 2px insertion line. No DOM order
change occurs until drop. Settings color buttons use an accessible color-only tag
glyph; six solid swatches retain names and a selected check. The provider letters
and colors remain on record cues, while source filter toggles retain names and
neutral separators without profile dots. Existing compact actions, editor,
confirmation, focus and first-use controls retain their meaning.

Source Chromium and packaged WKWebView each pass 30 behavior checks and 30 geometry
checks: ten at each of 1100×800, 320×720 and 700×480. Actual inner widths were
verified; Chrome's native window initially stopped at 500px, so the 320px pass
uses viewport emulation. Wide, palette-open and narrow renders were inspected.
Containment, readable long paths, 32px/40px targets, below-row palettes, selected
marks, scroll reach and focus all pass; reduced-motion narrow Chrome also passes.
Dashboard order/scope/dot checks and five source first-use checks pass.

Early probe failures came from counting neutral dividers as dots, checking dialog
close before its close event, and sending a non-cancelable synthetic Escape that
WebKit applied to the settings dialog. The probes were corrected. A trial focus
delay was reverted; the original production focus path passes in the final app.
No new reusable evaluation rule is proposed; existing affordance, containment and
state-continuity guidance covers this pass. Physical native drag/key input,
VoiceOver, real picker/Notes permissions and recipient-Mac acceptance remain
outside this scoped evidence. [Delivery](eval-0139-functional-standalone-test-app.md#profile-settings-presentation-delivery--2026-10-25-superseded)
owns final artifact and actual runtime checks.

## Resting Rows And Context Alignment — 2026-10-25

[Run 198](../run/run-20261025-198-context-settings-alignment.md), `extend` mode,
uses the existing Session row family for Context settings: subtle resting fill
and border, separated rows, stronger hover/focus feedback, handles and insertion
markers, compact named actions, primary name/path hierarchy and visible errors.
Routine counts/healthy status are omitted only in settings. Add opens its own
in-pane editor, retaining explicit folder/file and optional Notes registration.

**Scoped PASS:** rendered before/after inspection of Session/Context rows and the
Context editor; 13 geometry checks each at 1100×800, 320×720 and 700×480 in both
Chromium and packaged WKWebView. Pane containment, row separation, control bounds,
32px/40px targets, below-trigger menu placement and confirmation containment pass.
25 scripted interaction checks in each engine cover add/cancel/tab reset, reorder
preview/drop/cancel/keyboard/save/conflict, focus, confirmation cancel/confirm/error,
and retained Session color/reorder controls. The source explorer's named modal,
Cancel and focus return pass; first-use Back retains its draft and Skip registers
nothing. Synthetic Notes registration hides its duplicate Add action and exposes
an access error without invoking the Notes adapter.

A geometry probe initially compared a focused row with resting rows as if their
fills must match; it was corrected to account for the intended interaction state.
No production styling change was needed for that probe. Real native drag/key input,
VoiceOver and actual Notes/picker permissions remain outside this scoped evidence.

## White Rows And Shadow Lines — 2026-10-25

[Run 199](../run/run-20261025-199-settings-row-shadow-lines.md) corrects the owner's
intended meaning of row separation. The previous tinted surface is replaced by
white/default surface, the existing subtle border and resting card shadow. Whole-row
hover/focus/drag tints are removed; control focus and drag insertion/opacity remain.
The visible white cards and quiet boundaries in the [Notion reference](https://www.notion.com/ko)
are directional input, under the LocalBrain component rules.

**Scoped PASS:** rendered synthetic before/after Session and Context comparisons;
eight style/state/geometry checks covering white resting rows, shadow, focus, drag
insertion and stable geometry; both lists contained at 320×720 and 700×480 as well
as the wide 1100×800 inspection. Computed resting shadow is the existing 0/1/2px
5% black role. Row dimensions, gaps and controls are unchanged. No new behavior
tests or full-suite rerun were needed for the CSS-only correction. Existing broader
native-input/accessibility/product acceptance limits are unchanged.
## Vertical Color Menu And Browse — 2026-10-25

[Run 200](../run/run-20261025-200-profile-color-menu-and-local-picker.md) uses
screen-alignment `extend` under the shared settings constitution. The rendered
baseline exposed a horizontal strip of solid squares below an expanded profile
row and no outside dismissal. The corrected component places six copies of the
trigger's tag icon vertically beneath it, changing only the profile color and
adding the existing selected check. White rows, type, spacing, actions, focus
roles and the surrounding settings shell retain their current family.

Rendered Chromium inspection covers 1100×800, 320×720 and 700×480 CSS viewports;
viewport emulation verifies the actual narrow width rather than the browser
window's minimum resize width. The menu has a compact 72px width, below-trigger
placement and its own bounded scrolling, without widening the document. A low
anchor can scroll into view before opening. No external design system or new
color/type token is introduced.

Real pointer checks verify outside-click dismissal and same-trigger open/close.
The latter exposed native popover dismissal before the click handler; associating
the trigger with `popovertarget` and owning its toggle fixes that interaction.
Chromium and WebKit each pass 26 synthetic interaction checks: vertical tag shape,
selection, focus, Down/Home/End, Escape/Tab/category dismissal, persistence and
the picker draft/busy/error flows. Choice results and native calls in those UI
checks are controlled stubs; they do not establish physical OS dialog input.

macOS helper probes separately observe visible folder/file panels and normal
cancel responses. Actual app-button/OS input and VoiceOver remain outside the
automated design claim. The owner was asked to confirm the replaced app's Browse
button; no unanswered question is counted as a pass. Temporary visual/probe
artifacts are removed at closure.

## Visible Order Movement And Compact Colors — 2026-10-26

[Run 201](../run/run-20261026-201-settings-order-motion-and-compact-colors.md)
uses screen-alignment `adapt`. The rendered baseline and official Notion
[block movement example](https://www.notion.com/help/columns-headings-and-dividers)
establish the mismatch: a left grip and saved ordering did not give useful
whole-row movement or neighboring-position feedback. The shared Session/Context
control now lifts the row, shows its insertion slot, animates neighboring rows
and scrolls the settings pane near an edge. White surfaces, existing row geometry,
type, actions and actual source data retain their owners. Motion uses shared
duration/easing roles; reduced-motion preference suppresses transitions.

The palette keeps a vertical list but uses horizontal tags, zero padding/gap and
32×24px fine-pointer choices. Its default outer size is 34×146px, replacing the
previous 72px-wide menu. Coarse-pointer choices remain 40×40px. The selected check,
accessible color names, focus and below-trigger placement remain. WebKit initially
stretched the grid to its maximum available height; explicit intrinsic height and
start alignment fix that observed difference, without a browser-specific override.

**Scoped PASS:** real Chromium pointer drags move and save both source lists;
captured drag frames show a whole-row preview, slot and active neighbor animations.
Chromium and macOS WKWebView each pass 39 scripted interaction checks covering
preview, edge scroll, one-save release, keyboard movement, focus, cancellation,
failed write/readback recovery and compact palette access. Scripted pointer
sequences use a bounded capture shim; real Chromium input is separate evidence.
Chromium rendering/geometry covers 1100×800, 560×620, 720×400 and 320×720 touch
viewports, plus a 720×300 bounded-menu scroll check. Reduced motion produces zero
row animations. No horizontal overflow was observed in these checks.

This establishes the scoped interaction/render correction, not physical Tauri
pointer input, VoiceOver or recipient-Mac acceptance. The prior native-picker
confirmation remains unanswered. Task-owned visual/probe artifacts are removed
at closure.

## Profile Tag Alignment — 2026-10-26

[Run 202](../run/run-20261026-202-profile-tag-alignment.md), frontend-product and
screen-alignment `extend`, corrects the owner's glyph/alignment clarification.
Profile rows restore the original diagonal tag. Menu choices alone use horizontal
tags with the point/hole on the left. Their painted left edges align with the
trigger glyph, including differing SVG insets and narrow/touch control widths.
The check column is removed; a profile-colored outline and quiet fill mark the
selected choice while accessible radio state and keyboard focus remain separate.
Existing 34×146px default menu geometry, zero gap/padding, dismissal and save
behavior remain.

**Scoped PASS:** rendered before/after inspection and real Chromium trigger input;
22 scripted geometry/selection/save/focus/dismissal checks in Chromium and 22 in
macOS WKWebView. Chromium also passes seven geometry/reachability checks at each
of 560×620, 320×720 touch and 720×300; WebKit passes the same seven at 320×720 and
720×300 with its fine pointer. Painted-edge differences stay below 0.2px. No new
backend behavior or broader native-input acceptance is claimed. Existing backend
tests were not repeated for this bounded presentation change.

## Matching Palette And Tag Widths — 2026-10-26

[Run 203](../run/run-20261026-203-profile-palette-width.md) applies the owner's
further width clarification under frontend-product/screen-alignment `extend`.
The menu frame now matches both edges of the trigger background, replacing the
previous content-sized frame. Horizontal and diagonal SVG silhouettes share the
same painted x bounds, giving equal widths and edges without an offset applied
to the menu. Menu color-name `title` tooltips are removed; accessible labels,
radio state and selected fill/outline remain. A height-limited menu still scrolls,
without a scrollbar gutter changing its width or obscuring its tags.

**Scoped PASS:** rendered comparison and ten geometry/tooltip/reachability checks
at each of four Chromium viewports (1100×800, 560×620, 320×720 coarse pointer,
720×300) and three WKWebView viewports (1100×800, 320×720, 720×300). Both menu-frame
and painted-glyph edges match within 0.2px. Ten selection/save/keyboard/focus/
dismissal checks pass in each engine. No backend contract changed; its suites
were not repeated. Native physical-input and broader acceptance limits remain.

## Palette Pointer And Keyboard Focus — 2026-10-26

[Run 204](../run/run-20261026-204-pin-order-and-palette-focus.md) uses
fullstack-product/screen-alignment `extend` for the pinned read model and this
bounded palette correction. Native AppKit events sent to an isolated WKWebView
reproduce inconsistent focus rings when the pointer hits the decorative SVG.
Later sequential opens show a 2px outline and 3px focus shadow over the selected
1px border; hitting the button edge instead avoids that ring. This agrees with
the [WebKit SVG-descendant focus report](https://commits.webkit.org/311768@main).

Decorative SVGs now pass hits to the owning button. The selected outline/fill
remain unchanged; native keyboard focus remains distinct. A scoped flag applies
the shared focus tokens during keyboard navigation because this WebKit also
retains pointer styling during an arrow-key scripted focus move. Opening by
pointer clears the flag; no global focus suppression or layout change is used.

**Scoped PASS:** nine native pointer opens across three synthetic profiles
(two center-click cycles and one edge-click cycle), keyboard arrow movement and
keyboard reopening, save/readback/reopening, and unchanged frame edges. All
pointer opens retain the 1px selected border without a focus outline or shadow;
keyboard movement keeps a visible ring. Chromium verifies sequential profile
opens, mixed pointer/keyboard input, Escape/focus return, frame alignment and
accessible names without choice tooltips. Rendered inspection includes Chromium's
narrow layout and 1100×800 layout, plus the native probe window. No physical mouse
input into the actual Tauri window, VoiceOver or recipient-Mac acceptance is
claimed. Pin rendering and delivery evidence are recorded in the functional
receipt. All visual probes and synthetic data are removed at closure.
