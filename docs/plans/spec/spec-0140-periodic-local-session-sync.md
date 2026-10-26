# SPEC-0140: 공통 10분 세션 동기화

## Metadata

- Status: `approved`
- Parent Feature: [FEAT-0140](../feature/feat-0140-periodic-local-session-sync.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261018-178-periodic-local-session-sync](../run/run-20261018-178-periodic-local-session-sync.md)
- Execution Profile: `fullstack-product`
- Updated: `2026-10-26`

## Implementation Boundary

The [common settings and desktop contract](../../policies/project/desktop-app-and-settings.md)
owns field precedence, source identity, search admission, locking, local recovery and
edition boundaries. This specification applies those rules to this Feature.
The [test-app guide](../../policies/project/standalone-test-app-guide.md) owns delivery and usage.

## Acceptance Mapping

- AC1: 브라우저·배포 앱 공통 백엔드가 동기화를 소유한다. 별도 동기화 분류에서 세션·Local Context 각각 10·20·30·60분·끄기를 선택한다. 없는 항목은 세션 켜짐·10분, Context 켜짐·30분이며 각 완료 시점부터 독립적으로 예약한다. 기존 저장값과 끄기 전 주기를 보존한다.
- AC2: 수동/자동/여러 백엔드 중복 없음; 빈 소스·잠자기·실패·재시작·종료 처리.
- AC3: 설정 영속; 브라우저 종료 무관, 서버 종료 시 중지. 화면 상태와 로컬 최근 성공/오류 기록은 보존하되 설정의 상태·시각·수동 실행 카드는 두지 않는다. Sessions의 기존 수동 동기화는 유지한다. 공통 상태 표시줄·갱신 링크는 두지 않는다.

## Failure And Regression

Preserve originals, source/session IDs, frozen Usage attribution, unknown settings and
unrelated development features. Autosave failures read back the actual saved
preferences and offer retry; failed readback disables choices until reload.
Explicit source-form errors retain entered values for correction.
No implicit model download, external upload, paid signing or data relocation.

## Execution And Evidence

Primary-agent implementation with synthetic unit/integration/browser checks and an
independently launched bundled runtime. Record code, browser, packaged-app and teammate
Mac evidence separately. A build alone does not establish successful execution.
The active Run records observations and unresolved checks; do not infer a pass from this specification.

## Editable Interval — 2026-10-23

[Run 187](../run/run-20261023-187-settings-control-consistency.md) widens the existing
preset validation to whole minutes 10–1440. Existing saved intervals and the
10-minute fresh-install default remain. Off preserves the interval. The common
scheduler already uses minutes arithmetically; acceptance checks custom due-time
boundaries, disabled collection and re-enable behavior without changing locking,
coalescing, completion timing or manual collection.

## Sync Checkbox And Presets — 2026-10-24

[Run 188](../run/run-20261024-188-sync-checkbox-and-presets.md) supersedes the
number-input presentation from Run 187. Use one enable checkbox and a disabled-
when-off 10/20/30/60-minute selector. Remove range/runtime help. Preserve existing
values, autosave/readback and backward-compatible backend validation. Details
belong to the [settings owner](../../policies/project/desktop-app-and-settings.md#general-settings-presentation).

## Independent Source Schedules — 2026-10-24

Owner-approved [Run 190](../run/run-20261024-190-sync-settings-and-context-schedule.md)
extends collection to a separately controlled Local Context schedule and moves
controls into Sync after Search model, before Storage. Session settings/defaults
remain; Context adds enabled/30-minute missing-field defaults with independent
completion state. Both use the shared writer boundary and existing incremental
source adapters. Save controls independently with the current revision/readback
contract. General keeps startup/timezone; Storage remains separate. No status
cards or manual settings actions. Independent AI-index control stays a backlog
TODO; current activated search refresh remains. The Run owns scoped acceptance.

## Single Sync Select — 2026-10-24

Owner-approved [Run 191](../run/run-20261024-191-single-sync-select.md) supersedes
the checkbox-plus-select presentation with one 160px selector per domain:
10/20/30/60 minutes followed by Off. Off preserves saved minutes and updates only
the enabled flag; a numeric choice saves the flag and interval in one revision-
checked patch. Backend fields/defaults/scheduling and independent AI-index deferral
remain unchanged. Preserve legacy values and existing autosave/readback behavior.


## Content-Sized Sync Controls — 2026-10-24

[Run 192](../run/run-20261024-192-home-first-source-editor.md) replaces the fixed
160px Sync width with content-sized geometry (about 79px at the default scale),
allowing longer saved values to expand. Keep five options, selected markers,
below-trigger menus, focus and existing immediate-save behavior.
