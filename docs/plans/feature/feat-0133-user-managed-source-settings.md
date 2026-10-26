# FEAT-0133: 사용자 소스 설정

## Metadata
- ID: `feat-0133`
- Status: `blocked`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md) — C06
- Created: `2026-10-18`
- Updated: `2026-10-24`
- Authorization: 사용자의 현재 PRD 범위 전체 구현 요청. 범위 확대는 별도 검토한다.

## Goal And Acceptance Contract
- AC1: 다중 세션·Context 등록, 실제 읽을 경로 확인, 네이티브 선택/직접 입력.
- AC2: 중복/겹침 차단, 재연결 확인, 해제 후 기록 보존.
- AC3: 현재 provider·label·ID에 따른 목록/대시보드 필터; PDF 기존 범위·선택 Notes.

## Scope Boundary
- In: 위 계약과 PRD의 C06 결과.
- Out: 데이터 물리적 이동, 새 외부 전송, 제품 제외 기능의 설치형 활성화, 유료 배포·자동 업데이트.

## Surface Lanes
- Contract/data: 공통 설정·소스·검색·복구의 값별 정본. Contract 평가 담당은 primary agent.
- Product/runtime: 해당 화면과 backend 또는 macOS 실행부. Functional/Design/Interaction 평가 범위는 실제 변경과 실행 근거로 보고한다.

## Dependencies
- C02 / FEAT-0129, C04 / FEAT-0131, C05 / FEAT-0132

## State And Interaction
- Loading/empty/error/success를 구분한다. 원본·기존 사용자 상태를 실패 시 보존한다.
- 화면 변경은 기존 디자인을 extend하며 입력·조회·읽기 상태와 포커스를 보존한다.

## Contract Surfaces And Regression
- 기존 source/session ID, frozen Usage attribution, 도메인 정본, 설치형 범위, 로컬 데이터 보존.
- 기존 개발판 학습·Workstream 기능의 변경은 이 Feature 범위 밖이다.

## Pass Or Fail Checks
- AC1: 다중 세션·Context 등록, 실제 읽을 경로 확인, 네이티브 선택/직접 입력.
- AC2: 중복/겹침 차단, 재연결 확인, 해제 후 기록 보존.
- AC3: 현재 provider·label·ID에 따른 목록/대시보드 필터; PDF 기존 범위·선택 Notes.
- 각 조건의 코드 검토와 실제 실행 근거를 분리한다. 미실행 검증은 PASS로 간주하지 않는다.

## Harness Trace
- Spec: [SPEC-0133](../spec/spec-0133-user-managed-source-settings.md)
- Run: [run-20261018-171-user-managed-source-settings](../run/run-20261018-171-user-managed-source-settings.md). 검증 결과는 Run과 평가 기록에서 구분한다.

## Continuity Notes
- `2026-10-25`: 사용자가 행 구분을 배경색이 아닌 가는 경계와 그림자로 정정했다. [Run 199](../run/run-20261025-199-settings-row-shadow-lines.md)은 세션·Context 행의 채움색을 제거하고 기존 카드 그림자 역할을 적용한다. 데이터·순서·등록 동작은 유지한다.
- `2026-10-25`: 사용자가 기본 음영, Local Context 목록/추가 분리, 순서 조정과 등록 해제 확인창을 요청했다. [Run 198](../run/run-20261025-198-context-settings-alignment.md)이 공통 행 디자인과 Context 로컬 순서·확인 모달을 구현하고 테스트·브라우저·동봉 WebView·실제 앱 재실행을 검증했다. 정상 문서 수/연결 문구는 설정에서만 생략하고 기존 원본·등록 ID·문서 보존 계약은 유지한다.
- `2026-10-25`: [Run 197](../run/run-20261025-197-profile-settings-presentation.md)은 사용자가 정한 TOML 필드 순서, 점 없는 소스 토글, 색상 태그와 독립적인 드래그 행을 반영했다. 실제 설정 값·배열 순서 보존, 브라우저·동봉 WebKit 검증과 앱·웹 재실행을 확인했다. 기존 숫자 PK·등록·색상·배열 순서의 의미와 전체 수용 한계는 유지한다.
- `2026-10-24`: 사용자가 호환용 문자열 식별자 유지 결정을 정정했다. [Run 196](../run/run-20261024-196-source-primary-key-identity.md)은 숫자 PK만 남기고 중복 컬럼·현재 참조를 제거했다. 기존 기록·설정·동기화 시각 보존과 실제 앱·웹 재실행을 검증했으며, 전체 제품 수용 한계는 유지한다.
- `2026-10-24`: 사용자가 숫자 DB ID를 프로필 식별자로 공유하고 색상 선택과
  TOML 배열 순서에 따른 목록·토글 재정렬을 승인했다. [Run 195](../run/run-20261024-195-generalized-session-profiles.md)가
  기존 기록을 보존하는 설정 이전과 공통 표시를 완료했다. 실제 로컬 데이터의 ID·기록 보존,
  소스 브라우저와 최종 동봉 WebView의 색상·순서·이름 반영을 검증했다. 전체 제품의 수용 한계는 유지한다.
- `2026-10-23`: 사용자가 프로필 설정의 구성·문구를 다듬고 Apple 페이지의 감각을
  적용하도록 요청했다. [Run 186](../run/run-20261023-186-session-source-presentation.md)은
  일반 설정과 최초 설정 세션 단계의 목록·편집 표현을 소유한다. 기존 등록·재연결·해제
  계약과 전체 Feature의 수용 한계는 유지한다.
- `2026-10-18`: C06를 승인된 구현 경계로 구체화했다. foundation의 필드별 계약을 먼저 고정하고 후속 구현은 의존성 순서를 따른다.

## Implementation And Evidence — 2026-10-19

승인된 구현과 로컬 검증을 완료했다. [통합 기능 평가](../evaluation/eval-0139-functional-standalone-test-app.md)와
[계약 평가](../evaluation/eval-0139-contract-standalone-test-app.md)가 자동 검사·브라우저·동봉 앱·실제 모델 실행의
범위를 소유한다. [화면/상호작용 평가](../evaluation/eval-0139-design-standalone-test-app.md)의 실제 WebView 조작 근거와
PRD A12의 팀원 Mac 전달 확인이 남아 있어 전체 제품 수용은 `blocked`로 둔다.
구현 미착수나 새로운 제품 방향 미결정이라는 뜻은 아니다. 원본·설정·기존 개발 작업을
보존했으며, Drive 업로드·팀원 통지·Git 커밋/공개는 수행하지 않았다.
