# SPEC-0132: 설정 창과 제품 탐색

## Metadata

- Status: `approved`
- Parent Feature: [FEAT-0132](../feature/feat-0132-settings-and-product-navigation.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261018-170-settings-and-product-navigation](../run/run-20261018-170-settings-and-product-navigation.md)
- Execution Profile: `frontend-product`
- Updated: `2026-10-19`

## Implementation Boundary

The [common settings and desktop contract](../../policies/project/desktop-app-and-settings.md)
owns field precedence, source identity, search admission, locking, local recovery and
edition boundaries. This specification applies those rules to this Feature.
The [test-app guide](../../policies/project/standalone-test-app-guide.md) owns delivery and usage.

## Acceptance Mapping

- AC1: 하단 설정·Cmd+,·분류형 모달; Escape/포커스 복귀/좁은 창.
- AC2: 세 영역을 설치형 탐색으로 노출, 개발판 기능 보존.
- AC3: 기존 토큰·폼·오류 표현을 사용.

## Failure And Regression

Preserve originals, source/session IDs, frozen Usage attribution, unknown settings and
unrelated development features. Errors keep entered values and provide retry/recovery.
No implicit model download, external upload, paid signing or data relocation.

## Execution And Evidence

Primary-agent implementation with synthetic unit/integration/browser checks and an
independently launched bundled runtime. Record code, browser, packaged-app and teammate
Mac evidence separately. A build alone does not establish successful execution.
The active Run records observations and unresolved checks; do not infer a pass from this specification.

## Compact Settings Dialog — 2026-10-19

Owner correction: the current settings window feels too large. Frontend profile;
settings-shell geometry and interaction lanes; screen-alignment `extend`.
Use the existing constitution's compact dialog rule: maximum 720 by 560px at the
default scale, 160px desktop navigation, reduced spacing from existing roles,
fixed header/close action and content-owned vertical scrolling. Fit smaller
viewports and use the shared 700px horizontal-navigation breakpoint. Start each
selected category at the top while retaining pending field values. Preserve all
tabs, dropdown placement/options, readable text sizes, explicit save and error
recovery. Bring save/error feedback into view in the scrolling body. Verify
wide/narrow/short renders, every tab, end-of-content reachability,
menu containment, close/focus restoration, pending/save/reopen and packaged assets.

## About Identity And Initial Version — 2026-10-24

[Run 189](../run/run-20261024-189-about-identity-and-version.md) applies the owner's
About-dialog reference under screen-alignment adapt. Fullstack Product lanes:
concise identity/version UI, shared application version and packaged runtime.
Show the LocalBrain mark/name and v0.0.1; operational paragraphs remain in their
user-guide owner. Do not copy reference image assets, license data or invented
build information. About/FastAPI/package/native versions must agree while bundle
ID, runtime stores and schemas stay fixed. Verify rendered wide/narrow/short
states and actual rebuilt app startup; do not infer native parity from HTML alone.

## Dedicated Sync Category — 2026-10-24

Owner-approved [Run 190](../run/run-20261024-190-sync-settings-and-context-schedule.md)
places Sync after Search model and before Storage. General retains startup/timezone;
Storage remains separate. Reuse the current compact controls for independent Session
and Local Context schedules, preserving autosave, keyboard/focus, error readback and
wizard isolation. AI-index independent control remains deferred in the backlog.
The [source schedule spec](spec-0140-periodic-local-session-sync.md#independent-source-schedules--2026-10-24)
owns the backend extension.
