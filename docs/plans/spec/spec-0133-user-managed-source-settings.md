# SPEC-0133: 사용자 소스 설정

## Metadata

- Status: `approved`
- Parent Feature: [FEAT-0133](../feature/feat-0133-user-managed-source-settings.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261018-171-user-managed-source-settings](../run/run-20261018-171-user-managed-source-settings.md)
- Execution Profile: `fullstack-product`
- Updated: `2026-10-26`
- Latest completed follow-up: [Run 204](../run/run-20261026-204-pin-order-and-palette-focus.md)

## Implementation Boundary

The [common settings and desktop contract](../../policies/project/desktop-app-and-settings.md)
owns field precedence, source identity, search admission, locking, local recovery and
edition boundaries. This specification applies those rules to this Feature.
The [test-app guide](../../policies/project/standalone-test-app-guide.md) owns delivery and usage.

## Acceptance Mapping

- AC1: 다중 세션·Context 등록, 실제 읽을 경로 확인, 네이티브 선택/직접 입력.
- AC2: 중복/겹침 차단, 재연결 확인, 해제 후 기록 보존.
- AC3: 현재 provider·label·ID에 따른 목록/대시보드 필터; PDF 기존 범위·선택 Notes.

## Failure And Regression

Preserve originals, source/session IDs, frozen Usage attribution, unknown settings and
unrelated development features. Errors keep entered values and provide retry/recovery.
No implicit model download, external upload, paid signing or data relocation.

## Execution And Evidence

Primary-agent implementation with synthetic unit/integration/browser checks and an
independently launched bundled runtime. Record code, browser, packaged-app and teammate
Mac evidence separately. A build alone does not establish successful execution.
The active Run records observations and unresolved checks; do not infer a pass from this specification.

## Profile Presentation — 2026-10-23

This initial presentation is retained as history. The Home-first and Profile List
Actions follow-ups below supersede its optional-home and editor-owned-removal
choices; Source Primary Key Only supersedes the initially retained namespace.

Refine the shared Session-source setting in regular settings and the first-use
wizard. Present registered/retained profiles as compact rows with names, providers
where needed, actual home-abbreviated Session paths and readable availability.
Keep errors visible. An explicit Add or Edit opens the existing form in the same
pane; removal stays in the editor with its existing consequence/confirmation.

Keep tool, display name, Session folder and optional agent home. The actual folder
to collect remains primary; the optional home is disclosed separately. Discovered
candidates only prefill fields and do not repeat paths already represented in the
registry. Cancellation and leaving the settings category discard that form draft; wizard
Back preserves it (Run 187 supersedes category retention from Run 186). Save success returns to the overview. Validation/API
failure keeps the editor and values, and busy persistence prevents conflicting
form actions. Reconnection still requires explicit same-source confirmation
when its Session folder changes; identity and backend validation are unchanged.

Use existing dialog, type, surface, spacing, control and motion roles. Preserve
the wizard's fixed navigation/dots and Next-save/Skip-without-save behavior. No
new API/storage format, automatic registration, implicit download or foreign
visual theme is introduced.

## Shared Control Follow-up — 2026-10-23

[Run 187](../run/run-20261023-187-settings-control-consistency.md) supersedes profile
category draft retention: leaving the Session-source category closes/discards its
unsaved editor; returning shows the list. Wizard Back still preserves input.
Busy source writes lock category changes. Source tool and name share control
geometry; the tool uses the shared below-trigger menu and remains fixed in Edit.
Cancel is centered. Context uses that selector for kind and compact information
rows. Source registration, reconnection, removal and explicit save authority stay
unchanged. Preserve the accepted source overview.

## Home-First Editor — 2026-10-24

Owner-approved [Run 192](../run/run-20261024-192-home-first-source-editor.md)
replaces the primary Session-folder/optional-home form with an agent-home input
that derives the tool's conventional record folder. A disclosed explicit record
location supports exceptions and preserves all existing roots. The UI submits
the resolved collection path through the unchanged API; no config migration or
whole-home collection is implied. Preserve identity, confirmation, validation,
wizard saves/skips and category draft behavior. The Run owns scoped acceptance.

## Profile List Actions — 2026-10-24

Owner-approved [Run 193](../run/run-20261024-193-profile-list-actions.md) uses
English profile-field labels, red textual required markers, row-level Edit and
Unregister actions, and a reviewable confirmation modal. Reclicking Session sources
returns an open editor to the list; wizard Back retains its existing draft behavior.
This supersedes the earlier editor-only removal placement.
Identity, revisions, home/root mapping and record-preserving removal stay owned by
the existing API. The Run owns failure, focus, responsive and delivery acceptance.

## Compact Profile Controls — 2026-10-24

Owner-approved [Run 194](../run/run-20261024-194-compact-profile-controls.md)
reduces row-button width/type within shared control heights and changes the name
placeholder with the selected Tool. Entered names and existing validation remain.
Label propagation and DB-ID ordering are inspected, not changed by this follow-up.

## Generalized Session Profiles — 2026-10-24

The owner approves [Run 195](../run/run-20261024-195-generalized-session-profiles.md):
reuse numeric source PKs in configuration and public controls, configure colors
per profile, and make TOML array order govern settings and both filter surfaces.
This supersedes the prior fixed-color and DB-ID presentation order. Existing
record identity, frozen usage, pins and custom roots must survive migration.
Legacy ingestion namespaces are compatibility-only; no extra UUID is introduced.
The Run fixes palette, persistence/recovery, reordering and cross-surface checks.

## Source Primary Key Only — 2026-10-24

The owner explicitly rejects the retained string namespace. [Run 196](../run/run-20261024-196-source-primary-key-identity.md)
removes `sources.kind` and live old-key resolution after migrating dependent
references. The existing numeric PK alone identifies a profile; provider and label
keep their independent roles. Preserve source/session IDs, recorded usage and
evidence, pins, roots and presentation. Do not add a replacement identifier or
alias store. One-time upgrade code may read the old shape solely to migrate it.

## Profile Settings Presentation — 2026-10-25

The owner approves [Run 197](../run/run-20261025-197-profile-settings-presentation.md):
serialize each Session entry in source_id/provider_kind/display_label/root/color
order, then optional fields, without changing values or array order. Remove colored
dots only from source toggles. Settings show a color-only tag/palette and separate
draggable rows with an insertion indicator instead of one shared rounded frame.
Retain saved IDs, names, colors, order, record cues, keyboard/focus behavior,
registration/reconnection, editor and first-use authority. This corrects Run 195's
presentation while retaining Run 196's sole-PK contract.

## Context Settings Alignment — 2026-10-25

The owner approves [Run 198](../run/run-20261025-198-context-settings-alignment.md):
quiet resting surfaces for independent Session/Context rows; Context list/editor
separation; names/paths/actions without routine counts or ready text; persistent
Context reorder; and named in-app unregister confirmation. Context order belongs
to its existing SQLite registry, with a nullable nonnegative display_order and
legacy ordering for unset rows. Compare the submitted previous ordered IDs before
saving a complete permutation atomically; stale writes must not overwrite another
window's changes. Settings uses the full order; explorer groups keep their current
Folder/File boundary and apply that order within each group. New unpositioned rows
follow positioned ones. Re-registering a retained row preserves its saved position.

Context Add opens the same pane's editor; Cancel, leaving or reclicking the category
returns to its list and clears unsaved input. Wizard Back keeps the draft; Next
saves pending input and Skip does not. Folder/file and optional Apple Notes remain
explicit actions. Unregister uses a shared app dialog from settings and explorer;
Cancel/Escape write nothing, busy submission blocks dismissal, errors stay visible,
and dismissal returns focus. Original data and stored IDs retain existing semantics.

## Settings Row Shadow Lines — 2026-10-25

The owner corrects Run 198's tinted rows in
[Run 199](../run/run-20261025-199-settings-row-shadow-lines.md). Session and Context
rows use the default white surface with a subtle edge and resting shadow; idle,
hover, focus-within and drag do not tint the whole row. Keep control-level focus,
color palettes, spacing, independent-row shape, drag opacity/insertion cues and
all existing actions/data contracts. This is a presentation-only correction.

## Color Menu And Local Picker — 2026-10-25

The owner approves [Run 200](../run/run-20261025-200-profile-color-menu-and-local-picker.md):
open a vertical, color-only tag menu beneath its trigger and dismiss it on outside
interaction. Browse opens a macOS folder/file chooser in both the native app and
the local browser, filling the draft without saving or collecting. Preserve cancel,
busy, error, focus and first-use behavior. The Run owns the local-origin admission,
integration and scoped verification boundary.

## Visible Order Movement And Compact Colors — 2026-10-26

[Run 201](../run/run-20261026-201-settings-order-motion-and-compact-colors.md) makes
Session/Context ordering visible while dragging, with neighboring-row motion,
an insertion position and edge scrolling. Preserve commit-on-release, cancellation,
keyboard, reduced-motion and existing revision/readback semantics. Color choices
use horizontal tags and compact fine-pointer targets with minimal spacing. This
supersedes the previous menu dimensions and handle-only drag feedback.

## Trigger And Menu Tag Alignment — 2026-10-26

[Run 202](../run/run-20261026-202-profile-tag-alignment.md) restores the original
diagonal row tag while menu choices use horizontal tags with the hole on the left.
Align their visible left edges, and indicate the selected choice with a quiet
profile-colored fill/outline instead of a check. Preserve existing menu sizing,
accessibility, saving and ordering behavior.

## Palette And Glyph Width — 2026-10-26

[Run 203](../run/run-20261026-203-profile-palette-width.md) removes menu color-name
tooltips, matches the menu frame to both edges of its trigger background, and
matches horizontal/diagonal painted tag widths. Accessible names and existing
selection/saving remain; bounded scrolling must preserve that width in short windows.

## Pointer And Keyboard Focus — 2026-10-26

[Run 204](../run/run-20261026-204-pin-order-and-palette-focus.md) corrects the
selected-color emphasis after sequential pointer activation. Compare glyph-center
and surrounding-button hits, dismissal, peer switching, keyboard navigation and
save/reopen. Selected state retains its own border/fill; pointer focus must not
add stale keyboard emphasis, and genuine keyboard navigation retains visible
focus. Preserve tag/frame geometry, accessible radio state, order and saved data.
The isolated AppKit/WKWebView probe and actual Tauri physical input remain
different evidence; retain the Run's limits.
