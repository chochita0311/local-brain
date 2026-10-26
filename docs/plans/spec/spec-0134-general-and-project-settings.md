# SPEC-0134: 일반 설정과 프로젝트 표시

## Metadata

- Status: `approved`
- Parent Feature: [FEAT-0134](../feature/feat-0134-general-and-project-settings.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261020-180-project-copy-removal](../run/run-20261020-180-project-copy-removal.md)
- Follow-up Run: [general-settings copy removal](../run/run-20261018-172-general-and-project-settings.md#apply-timing-copy-removal--2026-10-20)
- Active follow-up: [general-settings autosave](../run/run-20261020-183-general-settings-autosave.md)
- Execution Profile: `fullstack-product`
- Updated: `2026-10-26`

## Implementation Boundary

The [common settings and desktop contract](../../policies/project/desktop-app-and-settings.md)
owns field precedence, source identity, search admission, locking, local recovery and
edition boundaries. This specification applies those rules to this Feature.
The [test-app guide](../../policies/project/standalone-test-app-guide.md) owns delivery and usage.

## Acceptance Mapping

- AC1: 일반의 시작 화면·시간대는 최대 240px·데스크톱 높이 32px 드롭다운이다. 시작 화면은 Sessions Dashboard → Sessions → Local Context 순서이며 기본 선택은 Sessions다. 시간대는 UTC·Asia/Seoul이다. 동기화는 별도 분류에서 세션과 Local Context 각각 10·20·30·60분·끄기 단일 선택기로 제공한다. 기존 저장값과 없는 항목의 기본값(세션 10분, Context 30분)을 보존한다. 프로젝트 표시 및 기준 위치 등록 UI는 없다.
- AC2: 경로는 현재 사용자 홈만 `~`로 축약하는 고정 규칙을 사용한다. 홈 자체는 `~`, 홈 밖은 원래 경로를 유지한다. 표시를 위해 파일시스템 경로를 해석하거나 기준 위치·별칭을 등록하지 않는다. 원본 경로·ID·고정 Usage 귀속은 보존한다. 기존 `project_display`·`projects`와 해당 환경변수는 적용하지 않고, 저장 파일의 기존 값은 보존하며 새 설정 API에서는 받지 않는다.
- AC3: 일반 설정은 로컬 파일을 따르고 없는 항목만 기본값을 사용한다. 환경변수 덮어쓰기와 저장값/적용값 안내를 제거한다. 확정 선택을 즉시 저장하고 실패 시 실제 저장값을 재조회해 복구·재시도한다. 재조회도 실패하면 재로드할 때까지 선택을 비활성화한다. 기존 파일은 보존한다.
- AC4: By Project / Project 명칭을 유지하며 `session_class=work`인 일반 작업과 하위 세션만 프로젝트별로 집계한다. 분석·Maintenance는 Project의 행·합계·비율 분모·정렬·최근 활동·연결에서 제외한다. 전체 사용량·추이·Source/Model 집계와 저장된 귀속·토큰·비용은 보존한다. Git 루트 또는 실행 폴더(`~` 포함) 기준과 실제 미귀속 작업의 `프로젝트 미지정` 표시는 유지한다.

## Work Session Project Scope — 2026-10-20

Owner approved excluding all Maintenance usage from the Project breakdown while retaining
it in overall usage, history and Source/Model. This supersedes the internal-analysis
Project category below. Apply the work-class filter after overall/history aggregation,
before creating any Project group. Full and visible-only projections must agree, with
work subsessions included and only primary work sessions counted as Sessions. Preserve
frozen attribution and every stored usage row. Project shares use only compatible work
usage; unavailable and zero costs keep their existing distinct semantics. The owner
removed the added scope/total paragraph in the 2026-10-20 follow-up: the table directly
follows its heading and controls. Retain the work-specific empty state. Keep By Project /
Project labels and home/folder grouping. Verify tokens/cost, all/exact source, work
subsessions, assigned/unassigned maintenance, unknown work, read-only persistence,
browser containment/navigation and the rebuilt frozen app.

## Unassigned Usage Label Correction — 2026-10-19 (Superseded)

The owner reported the misleading `Unassigned` Project row after the path-display
correction. Fullstack profile; backend read-model, frontend composition and packaged
integration lanes; screen-alignment `extend`, with the existing table and controls.

- Keep every nonempty frozen Project key and its existing label/path behavior.
- Only a `maintenance`, `metadata_only` Session whose external ID equals
  `localbrain-insight:<retained personal_insight_runs.id>` qualifies as app analysis.
  No title, source name, cwd, home path or missing-path inference establishes this.
- Within records with no Project key, present that category as `internal:insights`
  / `앱 내부 분석` and all remaining records as `unassigned` / `프로젝트 미지정`.
  The category key is a read-model value, not a stored Project or workspace ID.
- Apply the same rule to full and visible-only dashboard projections in web and
  desktop. Preserve dates, source/model grouping, totals, shares and work-Session
  counts. Keep Insights hidden in the desktop edition and create no new link.
- Verify mixed known/unknown/internal records, misleading prefixes, owner/class
  boundaries, unchanged frozen rows, switching source/model/project and token/cost,
  narrow/wide table containment and the rebuilt app. Do not migrate user data.

## Fixed Home Display Correction — 2026-10-19

The owner removed the display preference and registered-root concept. This supersedes
the prior home-relative/full-path choice proposal. Fullstack profile, screen-alignment
`extend`; primary agent owns all lanes and review. No independent project registry or
historical reclassification is introduced.

- Contract/backend: one presentation helper shortens only the current home at a path
  component boundary, without resolving symlinks or requiring path existence. Retire
  both preferences and the environment override; preserve legacy raw TOML values as
  inactive unknown fields. Verify boundary cases, settings revision/save compatibility,
  unchanged source/workspace identity and Usage facts with synthetic tests.
- Frontend: remove the project dropdown and root list/actions/controller/styles;
  retain three compact dropdowns, help, explicit Save and failure input retention.
  Apply the common path rule in Sessions, Chart, Dashboard, Context and read-only
  settings path labels; keep actual values in file selection and editing fields.
- Integration: inspect the current and changed synthetic screens at 1100/320 widths,
  exercise save/reopen, keyboard/dismissal and errors, then rebuild and verify the
  frozen app and ZIP. Source/browser, bundled runtime and teammate evidence stay
  distinct. No model download is needed for this correction.

## File-Owned General Settings — 2026-10-19

The owner rejected general-setting environment precedence. This supersedes the
original C01/C07 override contract. Fullstack profile; shared preference/config,
settings frontend and web/packaged integration lanes; screen-alignment `extend`.

- Read general values from `settings.toml`; only missing fields use defaults.
  Ignore all four former preference environment variables, even when malformed.
  Detect the initial timezone from Mac system zoneinfo instead of process `TZ`.
- Keep the API response fields compatible, with equal saved/effective values and
  saved/default provenance only. Preserve validation, unknown fields, version
  refusal, revision conflict checks, private atomic saves and the current file.
- Remove override help, per-field applied-value rows and their JS controller.
  Retain the three compact dropdowns, explicit Save and failure input retention.
- Confirm file values control startup on next launch, timezone on the next view,
  and automatic sync on the next scheduling decision. Web and app share this rule.
- Exercise conflicting/malformed old variables, missing settings, save/reopen,
  new backend startup, scheduler changes and unchanged real files. Rebuild/repackage
  the app; no model download or directory/authentication contract change is needed.

## Failure And Regression

Preserve originals, source/session IDs, frozen Usage attribution, unknown settings and
unrelated development features. General settings use the readback recovery below;
other forms keep entered values and provide retry/recovery.
No implicit model download, external upload, paid signing or data relocation.

## Execution And Evidence

Primary-agent implementation with synthetic unit/integration/browser checks and an
independently launched bundled runtime. Record code, browser, packaged-app and teammate
Mac evidence separately. A build alone does not establish successful execution.
The active Run records observations and unresolved checks; do not infer a pass from this specification.

## Sync Label — 2026-10-19

Frontend profile, general-settings copy lane; screen-alignment `extend`. Use
`동기화` for the field and its status wording. Retain the compact controls, options,
accessible label relationships, schedule semantics, manual action and saved values.
Verify rendered wide/narrow settings and refresh the distributed app assets.

## Apply-Timing Copy Removal — 2026-10-20

Owner follow-up: omit the redundant startup/time-zone application-timing notice.
Frontend profile, general-settings copy lane; screen-alignment `extend`. Remove
the paragraph below the controls and the equivalent sentence in save feedback;
retain `일반 설정을 저장했습니다.` as the success confirmation. Keep explicit Save,
all fields/options/order, time-zone impact help, pending/error behavior and the
existing next-launch/next-render application timing. Verify wide/narrow settings,
save/reopen and source/bundled asset equality, then refresh the app/ZIP.

## General Settings Autosave — 2026-10-20

The owner replaces explicit general Save with persistence on confirmed option
selection and removes the settings sync status/history/manual-action card.
Frontend profile, general-settings interaction lane, screen-alignment `extend`.
This supersedes explicit-Save requirements for these three general controls.

- Persist only the changed preference through the existing local revision-checked
  API. Off keeps the prior interval; selecting an interval enables sync. Same-value
  selection, highlight and Escape do not write. Keep startup/time-zone apply timing,
  control order, labels and menu geometry. Source-registration forms keep Save.
- Permit one general write at a time with brief busy/disabled controls. Closing
  the dialog does not cancel a write; reopening waits for it before reading values.
  Successful saving is quiet and never reloads the page or resets its state.
- On failure reread stored values. Confirm an ambiguous successful write by its
  actual persisted values; otherwise show the stored value and a retryable error.
  If rereading also fails, disable general choices until settings reload succeeds.
  Preserve unknown settings and external edits; do not retry stale revisions blindly.
- Remove the unused sync-card controller, retaining Sessions' existing manual
  action, backend schedule, JSON health state and source/file health tables.
- Verify keyboard/pointer selection, no-op/cancel, save/reopen, delayed and failed
  writes, conflict/readback recovery, ordinary web/frozen rendering and actual
  app replacement with saved files intact. No new history table or model download.

## Compact Shared Controls — 2026-10-23

[Run 187](../run/run-20261023-187-settings-control-consistency.md) applies the owner's
follow-up under Fullstack Product and screen-alignment extend. Its contract,
backend, shared frontend, integration and packaging lanes use the
[common settings owner](../../policies/project/desktop-app-and-settings.md#general-settings-presentation).
This supersedes the preset-sync, 320px and Sessions-first presentation only.
Autosave, revision recovery, private file ownership and default values remain.
Custom minutes must pass integer/range checks before persistence and control
completion-based scheduling in both app and browser. UI validation must also
cover below-trigger tool/kind selectors, uniform controls, source category draft
reset, wizard Back preservation and all affected panes at narrow/short sizes.

<a id="sync-checkbox-and-presets--2026-10-24"></a>

## Sync Checkbox And Presets — 2026-10-24 (Superseded)

[Run 188](../run/run-20261024-188-sync-checkbox-and-presets.md) supersedes the
number-input presentation from Run 187. Use one enable checkbox and a disabled-
when-off 10/20/30/60-minute selector. Remove range/runtime help. Preserve existing
values, autosave/readback and backward-compatible backend validation. Details
belong to the [settings owner](../../policies/project/desktop-app-and-settings.md#general-settings-presentation).

This dated Run 188 presentation is superseded by Run 190–191. The current
[Sync specification](spec-0140-periodic-local-session-sync.md#single-sync-select--2026-10-24)
uses independent Session/Context schedules and one minutes/Off selector per domain.
