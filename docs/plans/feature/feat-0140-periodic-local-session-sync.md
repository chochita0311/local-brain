# FEAT-0140: 공통 10분 세션 동기화

## Metadata
- ID: `feat-0140`
- Status: `blocked`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md) — C13
- Created: `2026-10-18`
- Updated: `2026-10-26`
- Authorization: 사용자의 현재 PRD 범위 전체 구현 요청. 범위 확대는 별도 검토한다.

## Goal And Acceptance Contract
- AC1: 브라우저·배포 앱 공통 백엔드가 동기화를 소유한다. 별도 동기화 분류에서 세션·Local Context 각각 10·20·30·60분·끄기를 선택한다. 없는 항목은 세션 켜짐·10분, Context 켜짐·30분이며 각 완료 시점부터 독립적으로 예약한다. 기존 저장값과 끄기 전 주기를 보존한다.
- AC2: 수동/자동/여러 백엔드 중복 없음; 빈 소스·잠자기·실패·재시작·종료 처리.
- AC3: 설정 영속; 브라우저 종료 무관, 서버 종료 시 중지. 화면 상태와 로컬 최근 성공/오류 기록은 보존하되 설정의 상태·시각·수동 실행 카드는 두지 않는다. Sessions의 기존 수동 동기화는 유지한다. 공통 상태 표시줄·갱신 링크는 두지 않는다.

## Scope Boundary
- In: 위 계약과 PRD의 C13 결과.
- Out: 데이터 물리적 이동, 새 외부 전송, 제품 제외 기능의 설치형 활성화, 유료 배포·자동 업데이트.

## Surface Lanes
- Contract/data: 공통 설정·소스·검색·복구의 값별 정본. Contract 평가 담당은 primary agent.
- Product/runtime: 해당 화면과 backend 또는 macOS 실행부. Functional/Design/Interaction 평가 범위는 실제 변경과 실행 근거로 보고한다.

## Dependencies
- C01 / FEAT-0128, C02 / FEAT-0129, C03 / FEAT-0130, C04 / FEAT-0131, C05 / FEAT-0132, C06 / FEAT-0133

## State And Interaction
- Loading/empty/error/success를 구분한다. 원본·기존 사용자 상태를 실패 시 보존한다.
- 화면 변경은 기존 디자인을 extend하며 입력·조회·읽기 상태와 포커스를 보존한다.

## Contract Surfaces And Regression
- 기존 source/session ID, frozen Usage attribution, 도메인 정본, 설치형 범위, 로컬 데이터 보존.
- 기존 개발판 학습·Workstream 기능의 변경은 이 Feature 범위 밖이다.

## Pass Or Fail Checks
- AC1: 브라우저·배포 앱 공통 백엔드가 동기화를 소유한다. 별도 동기화 분류에서 세션·Local Context 각각 10·20·30·60분·끄기를 선택한다. 없는 항목은 세션 켜짐·10분, Context 켜짐·30분이며 각 완료 시점부터 독립적으로 예약한다. 기존 저장값과 끄기 전 주기를 보존한다.
- AC2: 수동/자동/여러 백엔드 중복 없음; 빈 소스·잠자기·실패·재시작·종료 처리.
- AC3: 설정 영속; 브라우저 종료 무관, 서버 종료 시 중지. 화면 상태와 로컬 최근 성공/오류 기록은 보존하되 설정의 상태·시각·수동 실행 카드는 두지 않는다. Sessions의 기존 수동 동기화는 유지한다. 공통 상태 표시줄·갱신 링크는 두지 않는다.
- 각 조건의 코드 검토와 실제 실행 근거를 분리한다. 미실행 검증은 PASS로 간주하지 않는다.

## Harness Trace
- Spec: [SPEC-0140](../spec/spec-0140-periodic-local-session-sync.md)
- Run: [run-20261018-178-periodic-local-session-sync](../run/run-20261018-178-periodic-local-session-sync.md). 검증 결과는 Run과 평가 기록에서 구분한다.

## Continuity Notes
- `2026-10-18`: C13를 승인된 구현 경계로 구체화했다. foundation의 필드별 계약을 먼저 고정하고 후속 구현은 의존성 순서를 따른다.

## Implementation And Evidence — 2026-10-19

승인된 구현과 로컬 검증을 완료했다. [통합 기능 평가](../evaluation/eval-0139-functional-standalone-test-app.md)와
[계약 평가](../evaluation/eval-0139-contract-standalone-test-app.md)가 자동 검사·브라우저·동봉 앱·실제 모델 실행의
범위를 소유한다. [화면/상호작용 평가](../evaluation/eval-0139-design-standalone-test-app.md)의 실제 WebView 조작 근거와
PRD A12의 팀원 Mac 전달 확인이 남아 있어 전체 제품 수용은 `blocked`로 둔다.
구현 미착수나 새로운 제품 방향 미결정이라는 뜻은 아니다. 원본·설정·기존 개발 작업을
보존했으며, Drive 업로드·팀원 통지·Git 커밋/공개는 수행하지 않았다.

- `2026-10-19` owner-directed display cleanup: remove the common automatic-sync
  status strip and update link; keep the ten-minute schedule, existing manual
  action and settings-owned health. Acceptance wording and the Run were updated.

- Custom-interval follow-up: [Run 187](../run/run-20261023-187-settings-control-consistency.md).

- `2026-10-24`: Owner approved the dedicated Sync tab and independent Session/
  Local Context schedules in [Run 190](../run/run-20261024-190-sync-settings-and-context-schedule.md).
  This explicitly extends the earlier Session-only boundary. AI-index control is
  deferred; wider native/recipient acceptance retains its existing status.
