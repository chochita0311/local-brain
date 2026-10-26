# EVAL-0139: Standalone Integration Contracts

## Metadata

- ID: `eval-0139`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-177](../run/run-20261018-177-standalone-test-app-delivery.md)
- Feature: [FEAT-0139](../feature/feat-0139-standalone-test-app-delivery.md)
- Spec: [SPEC-0139](../spec/spec-0139-standalone-test-app-delivery.md)
- Execution Profile: `infra-devtool`, with Fullstack dependencies
- Surface Lane: settings/source/search/storage/runtime integration
- Evidence Coverage: `complete` for inspected contracts, not runtime admission
- Created: `2026-10-18`

## Initial Integration Checks — 2026-10-18

The initial checks below and their mixed-workspace failures are dated evidence.
[Current closeout verification](eval-0139-functional-standalone-test-app.md#session-closeout--2026-10-26)
records the separated source candidate and remaining native/distribution limits.

## Checks

Reviewed value owners, revisions, schema versions, file-owned general preferences, source
identity, original-read boundaries, reconnect recovery, disabled-source eligibility,
completion-based scheduling, process lock ownership, model installation/cancellation,
backup/restore publication and cache ownership against FEAT-0128–0140. Startup and
shutdown preserve the exclusion of unfinished products. The frozen executable
selects desktop admission independently of mutable settings. The app authenticates
its loopback window and bounds native commands; imported Markdown keeps its safe
rendering contract. Program distribution includes no private runtime store.

Domain stores stay separate: preferences TOML, Session TOML, search JSON and
Context DB. Rebuildable overall sync health has its own local JSON so health-only
writes cannot change the primary DB stamp. Existing source health remains in its
own table, and unchanged search sources reuse index vectors.

Existing Session/source IDs, pins, provenance, Chart choices and frozen Usage
attribution remain intact. There is no remote inference fallback, automatic model
download, new blanket network policy, app encryption, data relocation or updater.

## Stale-Assumption Review

README, installation/storage, common settings, developer/source registry, product,
architecture, natural search, PRD and planning status owners were updated. Tests
were revised only where the approved keyword/source/sync/display contract changed.
Pre-existing learning/schema work remains preserved, including its four failing
inventory checks. The [functional receipt](eval-0139-functional-standalone-test-app.md)
owns exact checks and limits.

## Route

`pass` for the integration contract. Complete distribution acceptance remains
blocked by the separately recorded native/teammate evidence gaps.

## Fixed Home Display Contract — 2026-10-19

C07 now removes `project_display`, `projects` and `LOCALBRAIN_PROJECT_DISPLAY`
from active behavior. Old TOML fields are preserved as inactive unknown values;
new writes reject them and malformed retired values do not block valid fields.
The shared formatter uses current-home component boundaries without filesystem
resolution; raw paths, stable IDs and frozen Usage grouping remain untouched.
Source/Context registration still owns collection scope. Source editing keeps the
actual path while read-only labels abbreviate home. The scanner's fixed Projects
label root was removed; no historical reclassification was added.

Synthetic boundary/legacy-save/rejection tests and the final 173-test integration
run passed, with the access-time-only initial failure/reruns recorded in C07.
The published app exposes the new active preference shape, and existing user
settings/source-file hashes were unchanged. Contract PASS remains scoped to
these inspected rules; broader runtime and recipient evidence is separate.


## Unassigned Usage Display Contract — 2026-10-19 (Superseded)

Scoped PASS: the dashboard keeps stored Project snapshots immutable and distinguishes
only the read-model categories within records without a Project key. `앱 내부 분석`
requires the retained analysis Run identity and a metadata-only Maintenance Session;
ordinary unknowns remain `프로젝트 미지정`. Nonempty Project keys take precedence.
Full and visible-only projections share the rule. Source/model grouping, compatible
token/cost totals, shares, work-Session eligibility and desktop Insights exclusion
are preserved. No schema or user-data migration was performed.

The 99-test related run covers mixed categories and each provenance boundary;
actual retained Usage rows and settings/source-file hashes were unchanged after
app replacement. The functional receipt owns the new artifact and runtime limits.

## File-Owned General Preferences Contract — 2026-10-19

Scoped PASS: general preferences follow `settings.toml`, using defaults only for
missing fields. Conflicting or invalid former general-preference environment
variables cannot change the value or block reading the file. Initial time zone
comes from system zoneinfo, with UTC fallback, independently of process `TZ`.
Runtime directories, desktop authentication and domain stores retain their owners.
The API response shape is compatible: `saved` equals `effective`, and each source
is `saved` or `default`. No independent applied-value branch remains.

Schema validation, unknown-field preservation, atomic private publication,
revision conflict handling and apply timing remain. Settings UI has one value per
control and no override explanation. The 131 related tests passed; source and
frozen-backend restarts retained saved startup/time-zone/sync values despite
conflicting environment variables. The actual updated app retained identical
settings/source-file hashes. The functional receipt records delivery and limits.

## Work Session Project Contract — 2026-10-20

Scoped PASS for [Run 179](../run/run-20261020-179-work-session-project-usage.md).
A single work-class predicate is applied after overall/history accumulation and
before Project groups, compatible denominator, ordering, last activity or evidence.
Work subsessions are included; Session counts remain primary-work counts. All
Maintenance is excluded regardless of attribution, owner, external-ID prefix or
index policy. Source/Model, summary, MTD/projection and freshness are preserved.
Full/visible tests cover source scopes, tokens/cost/shares, assigned/unassigned
Maintenance, unknown work, home identity, zero/unpriced costs and unchanged stored
Usage rows. No migration, inferred Project reassignment or hidden Insights activation.
The existing immutable Git/path snapshot identity contract remains in force.

## Portable Python Metadata Contract — 2026-10-20

Scoped PASS for [Run 182](../run/run-20261020-182-portable-python-build-metadata.md).
The build-only pre-find hook supplies sanitized sysconfig code before PyInstaller
analysis caches it. Interpreter installation paths resolve from the frozen
runtime's `sys.prefix`; application data continues to resolve from the current
user's home. No recipient Python installation or assumed username is introduced.
The builder's interpreter and domain settings remain untouched.

The rebuilt archive has 20 changed path fields and 937 unchanged metadata fields;
all 100 LocalBrain code modules match the previous archive. Packaging rejects
known builder home, checkout and temporary-build paths in raw assets, links,
compressed Python constants/filenames, nested stdlib ZIP and gzip contents.
Inspection does not execute bundled code and errors identify the artifact or
module without echoing the private value. The former app fails the guard; the
new distribution passes. The guard is scoped to known build paths, not a general
proof that arbitrary content is non-sensitive.

Tests cover two synthetic runtime locations, prefix boundaries, unchanged flags,
unknown-path rejection, nested constants/filenames, chunk boundaries and archive
inspection without execution. Frozen relocation and actual saved-file hash
preservation passed. The [functional receipt](eval-0139-functional-standalone-test-app.md#portable-python-metadata-delivery--2026-10-20-superseded-artifact)
owns exact delivery checks and their limits; recipient-Mac acceptance remains open.

## General Settings Autosave Contract — 2026-10-20

Scoped PASS for [Run 183](../run/run-20261020-183-general-settings-autosave.md).
The existing preference API, revision, local file owner, atomic permissions,
unknown-field preservation and apply timing remain. Each confirmed general
selection patches only its field or sync pair; off preserves the interval.
Writes are serialized by briefly disabling general choices. Reopening waits
for an active save and ignores superseded loads. No-op/highlight/Escape do not
write; source forms retain explicit Save.

Failure reads back authoritative values, preserving external edits and detecting
a committed write with a lost response. Failed readback disables general choices
until a successful reload. The general sync-card controller is removed without
changing Sessions' manual action, scheduler, latest JSON health or source/file
health tables. No new history store or migration. Tests and web/frozen checks
cover these boundaries; overall standalone acceptance remains separate.

## First-Use Overlay Wizard Contract — 2026-10-23

Scoped PASS for [Run 184](../run/run-20261023-184-first-use-overlay-wizard.md).
The redirect selects the saved startup route; malformed preferences retain the
settings recovery route. Desktop incomplete state and explicit web setup open a
shared modal over the real main surface. Normal web entry remains unchanged.
The wizard reuses existing source/context/model services, validates and saves
pending paths on Next, and does not install models on navigation or completion.
Skip does not publish drafts; Back retains them; registration and completion have
separate persistence. Completion uses a fresh revision and confirms an ambiguous
write before dismissing. Failure keeps the modal and incomplete state; process
restart preserves prior registrations and the saved completion flag.

The two inactive Project keys were removed only from the owner's requested local
file, preserving the manually false completion flag and other values. Fresh-file
and unknown-field compatibility rules are unchanged. Tests, synthetic WebKit
runs, fresh frozen processes and real app read-only startup checks support this
bounded correction. Broader feature acceptance, physical native interactions and
recipient delivery remain at their previously recorded limits.

## Editable Sync Interval — 2026-10-23

**Scoped PASS.** [Run 187](../run/run-20261023-187-settings-control-consistency.md)
changes the preference validator from three presets to integer minutes 10–1440.
The saved/default owner, schema version, revision checks, private atomic writes,
unknown-field preservation and common scheduler are unchanged. The existing
10-minute fresh-install default and all old valid saved intervals remain valid.
Turning off preserves minutes; UI commits on change/Enter rather than keystrokes.

New tests verify 10/17/45/1440 round trips, rejection of out-of-range, fractional,
boolean, string and null input without modifying the file, due-time boundaries
for 17 minutes, completion-based next run, disabled collection and re-enable.
Existing concurrency, source lifecycle, desktop boundary and recovery tests are
included in the 129-test run. Browser/frozen-runtime tests confirm custom values
reach the same API, conflict readback and ambiguous-write confirmation. No DB or
source identity migration, data relocation or model/network authority change.

## About And Version Contract — 2026-10-24

**Scoped PASS** for [Run 189](../run/run-20261024-189-about-identity-and-version.md).
About and FastAPI now read the Python version constant; project/distribution,
lock entries, desktop package and Tauri/native metadata all identify 0.0.1.
The build receipt reads the actual app plist. Dependency lock comparisons confirm
that only the two LocalBrain package versions changed, with no dependency upgrade.
Bundle identifier, runtime storage resolution, settings schema and domain schemas
are independent of release version and remain unchanged. Three actual saved
configuration hashes were preserved across replacement and startup.

Existing focused tests, source-version checks, frozen About rendering, native
plist/binary rebuild and actual startup support this boundary. No data migration,
model action, extra network authority or copied reference content was introduced.
The functional receipt owns delivery checks and the unchanged broader limits.

## Independent Source Schedules — 2026-10-24

**Scoped PASS** for [Run 190](../run/run-20261024-190-sync-settings-and-context-schedule.md).
Context adds enabled/30-minute missing-field defaults to the existing local schema-1
preference file. Session defaults and saved values remain; unknown keys, revision
checks, atomic private writes and no environment override remain. Each schedule
has an independent completion/health JSON file and uses the existing common writer
lock, including across backends. Busy collection retains one pending manual request
until a completion in its own domain satisfies it; another domain cannot discard it.

The Context-only scanner reuses existing registered enabled folder/file/Notes
adapters and health tables, without Session scans or DB schema changes. Cancellation
rolls back the Context transaction; enumeration and Notes iteration check shutdown,
and the Notes subprocess is killed/drained on cancellation or its 120-second limit.
Model installation and activated index refresh retain their existing authorities.
Independent AI-index controls are explicitly deferred in the project backlog.

132 focused tests cover defaults/restart, legacy files, independent clocks, intervals,
off/on, locks, duplicate suppression, incremental update/delete, stable identity,
partial failure, cancellation and bounded Notes failure. Real source/frozen scheduler
checks each passed eight assertions for disabled collection, resume, periodic changes,
completion timing, retained identity, no Session scan and idle model. Notes process
tests use mocks; they do not establish real Notes permission behavior. No full-suite
or wider native/recipient acceptance claim is made.


## Home-First Source Payload — 2026-10-24

**Scoped PASS** for [Run 192](../run/run-20261024-192-home-first-source-editor.md).
The UI derives an explicit record root from agent home or uses a custom override,
then submits the existing source API payload. TOML/schema, registry identity,
revision locking, overlap checks and source reconnection evidence stay owned by
the unchanged backend. No home/config/credential scan is introduced. Conventional
legacy roots can prefill a home; custom and home-less roots are retained. Editor
initial values determine draft changes so an unchanged wizard step does not save
merely because its displayed fields differ from stored root representation.

Focused source/settings tests and real synthetic source/frozen API writes verify
both providers, invalid/duplicate rejection, root preservation, confirmed relocation
with stable source ID, and no writes on cancel or unchanged wizard Next. Native
picker calls were stubbed and are not an OS-permission acceptance. The final app
preserves all three existing configuration hashes; source settings migrate only
through a subsequent explicit user save, not through startup or editor opening.


## Profile Removal Confirmation — 2026-10-24

**Scoped PASS** for [Run 193](../run/run-20261024-193-profile-list-actions.md).
The list confirmation captures source key and revision before any write. Only
Confirm submits the existing removal API; opening, Cancel/Escape and draft exit
do not. Busy state prevents duplicate requests and dismissal. Failed responses
remain visible; readback resolves a successful removal with a lost response, and
changed registry revisions require fresh review before retry. No schema, source
identity, Home/root mapping, backend removal or collection authority changes.

Existing focused tests and synthetic source/frozen API writes verify retained
session/event/source-file rows, stable source identity/path and original files.
Registration state remains in session-sources.toml; unregistered rows can reconnect
through the existing API. Two preliminary retention probes were corrected from a
nonexistent message table/DB-enabled column to activity_events and TOML. The final
checks pass. Actual app replacement preserves all three saved configuration hashes.

## Generalized Session Profile Contract — 2026-10-24

**Scoped PASS** for [Run 195](../run/run-20261024-195-generalized-session-profiles.md).
Version-2 Session TOML, public APIs and new filters share the existing numeric
`sources.id`. Provider, editable label/color, Home/collection root and array order
have separate duties. No extra random identity is created. The old `sources.kind`
remains internal to reproduce historical event/usage keys and resolve old links;
new profiles derive that namespace from their numeric PK. Separate numeric and
legacy lookup maps prevent collisions with numeric historical namespaces.

Valid v1 configuration migrates with existing IDs and former visible order/colors.
TOML is authoritative: DB color/order columns are projections, missing v2 color
uses the provider default and settings reload/collection applies valid manual
edits. Invalid files and conflicting identities/roots are preserved with an error.
Allocation reserves configured IDs before assigning a new PK and rejects unsafe,
duplicate or conflicting identities; it does not silently re-key records. Provider
wrappers now scan all configured matching profiles, including numeric namespaces.

Metadata and order writes share the process lock, revision validation, atomic
configuration replacement and transactional DB boundary. Reorder requires the
complete configured ID set. Failures, including after file replacement, restore
the prior owned state; ambiguous responses are read back before retry. A changed
collection root retains same-source evidence/confirmation requirements. Home-only
changes with an unchanged explicit root affect metadata alone. Unregister retains
the source ID, transcripts, history and usage. Backup validation accepts both
supported Session configuration versions.

Nine focused behavior tests and synthetic browser/frozen checks establish migration,
reingestion identity, frozen usage/pins, multiple same-provider profiles, restored
IDs, manual projection, invalid values, conflict and disk-failure recovery. Actual
local migration preserves every compared record row and source identity, passes
DB integrity/foreign-key checks and leaves general/search settings byte-identical.
This is a local identity/presentation migration, with no original-file relocation,
new external authority, model download or unfinished-feature activation. The
[functional receipt](eval-0139-functional-standalone-test-app.md#generalized-session-profiles-delivery--2026-10-24-superseded)
owns final delivery identity, baseline test failures and broader acceptance limits.

## Source Primary Key Only Contract — 2026-10-24

**Scoped PASS** for [Run 196](../run/run-20261024-196-source-primary-key-identity.md).
This supersedes Run 195's retained compatibility namespace. `sources.id` alone
identifies a profile. `provider_kind` chooses the provider; `name`/display label,
Home/root, color/order and health keep their separate duties. The redundant
`sources.kind`, live alias lookup and current profile `source_key` fields are
removed without introducing a substitute string ID or alias table.

One-time startup upgrades valid v1 files and dependent skill source FKs, chart
scopes, workflow boundaries, analysis usage settings and cached sync reports.
The upgrade is backup-backed and verifies foreign keys before committing; failure
rolls back DB and attempted file writes while preserving concurrent edits.
Interrupted reconnect recovery runs first. Invalid/conflicting v1 identities,
unexpected schema columns/triggers and ambiguous numeric chart aliases stop rather
than reassign data. FTS provider classification comes from each owning entity.
Cached report clocks, outcomes and counts remain unchanged.

Source/session PKs and all record counts remain; existing event/usage opaque IDs
are retained through their native unique-key match during re-ingestion. Skill
evidence uses a physical source FK with NO ACTION deletion semantics. No original
transcript changes, root relocation, new external authority or unfinished-feature
activation occurs. Current report citations resolve event/session PKs; completed
report artifacts remain frozen historical evidence, without a live alias resolver.

All 17 focused profile tests and the final 61-test profile/scheduler/desktop group
pass. Synthetic migration tests, source/packaged WebKit and a private actual-data
copy establish dependent-reference conversion, same-provider separation, rollback,
re-ingestion, repeat-startup idempotency and presentation continuity. Actual migration
under exclusive runtime ownership preserves source fields, table counts, unaffected
rows and the three configuration files; sync report reference-only changes preserve
their clocks/counts. Integrity and foreign-key checks pass before app/web restart.
The [functional receipt](eval-0139-functional-standalone-test-app.md#source-primary-key-only-delivery--2026-10-24-superseded)
owns final artifacts, the four existing full-suite failures and acceptance limits.

## Profile Field Order And Presentation — 2026-10-25

**Scoped PASS** for [Run 197](../run/run-20261025-197-profile-settings-presentation.md).
Session TOML writes share source_id/provider_kind/display_label/root/color order,
then optional agent_home/enabled. This changes serialization readability, not
schema version, identity, values or array-order authority. Bootstrap, v1 upgrade
and UI mutations use the same serializer. Unsupported entries still follow the
existing validation/error path; names, roots and registration rules are unchanged.

Color-only settings controls and textual source toggles retain existing numeric
IDs and revision-checked writes. Drag preview only marks the candidate boundary;
drop and keyboard reorder persist the same complete configured-ID permutation.
Cancelled drags, rejected writes, editor exits and removal cancellation preserve
the saved state. Names, selection and record cue colors remain shared.

108 existing tests, synthetic source/frozen API and rendered interactions pass.
Field-order witnesses cover UI mutation, optional values, bootstrap and v1 upgrade.
Actual file formatting under exclusive runtime ownership preserves parsed values,
array order and source rows; general/search files remain byte-identical. No schema
migration, new collection authority, original-file change or model download.
The [delivery receipt](eval-0139-functional-standalone-test-app.md#profile-settings-presentation-delivery--2026-10-25-superseded)
owns runtime observations and acceptance limits.

## Context Order And Safe Removal — 2026-10-25

[Run 198](../run/run-20261025-198-context-settings-alignment.md) adds nullable,
nonnegative `context_roots.display_order` with an additive compatible migration.
Existing rows retain default ordering; a complete numeric-ID permutation is
saved only when the submitted previous ordered active IDs still match, under
the local writer lock and an immediate SQLite transaction. IDs, paths, documents
and scan timestamps are not ordering fields. New unset roots follow positioned
ones; re-registration retains the saved position. Explorer type groups remain.

**Scoped PASS:** persistence across reopening, default/migrated ordering, repeat
migration, source/document identity and scan-state preservation, append/restore,
and stale/incomplete/duplicate/disabled/invalid-ID rejection. HTTP validation also
rejects booleans and strings. Settings and explorer use one named app confirmation;
Cancel/Escape do not call removal, and confirmed removal keeps the existing
soft-disable/index-cleanup contract. Actual upgrade preserves settings bytes,
Context registrations, document IDs and default order; DB integrity passes.

The existing data-model documentation checker still reports omitted learning
ownership and stale table/FK/index counts. These predate this additive-column
change; the schema presentation/value generators and scoped behavior checks pass.
This is not a clean full-suite or broader Feature acceptance claim.
## Color Menu And Local Picker — 2026-10-25

[Run 200](../run/run-20261025-200-profile-color-menu-and-local-picker.md) changes
presentation and explicit chooser admission, without changing registry identity,
registration/save authority, source paths, source order, storage schema or sync.

- Browser `POST /api/settings/choose-path` admits only a matching loopback Origin,
  JSON content type and exactly one boolean `directory`. Missing/foreign origins,
  cross-site requests, extra fields, malformed/oversized JSON and invalid types
  fail before a chooser starts. The existing app-token boundary remains in force.
- A fixed AppKit chooser runs in its own local process. No request supplies script
  or shell text; only the file/folder mode varies. It exposes hidden folders,
  returns one selected path or explicit cancellation, and performs no import/write.
  A backend lock rejects overlapping dialogs. Timeout, unsupported platform,
  process failure, abnormal modal completion and invalid output produce bounded
  errors without raw process output. The lock is released after failure.
- The native frontend invokes the installed dialog plugin's `open` command, which
  attaches to the calling window in the [versioned native implementation](https://raw.githubusercontent.com/tauri-apps/plugins-workspace/dialog-v2.8.3/plugins/dialog/src/commands.rs).
  Existing native permissions/shell are reused; no new native permission or Rust
  build is claimed. String-valued native errors are now shown in settings.
- UI selection fills the intended draft; cancellation preserves it. Pending
  pickers disable conflicting fields, navigation, dismissal and save/skip actions.
  Source reconnection, explicit registration, first-use and local-only boundaries
  remain unchanged. Native bridge result tests are stubs, separately identified
  from actual macOS chooser presentation/cancellation and app startup checks.

Scoped contract checks pass. Actual physical Tauri chooser input remains a human
verification boundary; broader Feature/recipient-Mac acceptance is unchanged.

## Order Preview And Persistence — 2026-10-26

[Run 201](../run/run-20261026-201-settings-order-motion-and-compact-colors.md)
changes shared frontend ordering and palette geometry only. Preview rearranges
visible rows without writing; an inside-pane completed changed drop writes once.
Clicks, Escape, pointer cancellation/capture loss and outside drops restore the
original order without writing. Keyboard movement previews and saves the same
permutation. Existing revision/expected-order validation and readback remain;
when both save and readback fail, the UI returns to its last confirmed order.
Numeric IDs, profile TOML order, Context DB order, source paths, filters, sync,
registration authority and original data are unchanged.

**Scoped PASS:** 39 scripted checks in Chromium and 39 in WKWebView, with real
Chromium drag input separately observed for both lists. The 17 profile tests and
36 desktop-settings/Context-root tests pass. An initial direct module invocation
could not import a sibling test fixture; using the configured discovery form
resolved that test-launch issue. No new backend behavior or full-suite result is
claimed. Native input and broader acceptance limits remain separate.
