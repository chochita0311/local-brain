# FEAT-0137: 첫 실행 안내

## Metadata
- ID: `feat-0137`
- Status: `blocked`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md) — C10
- Created: `2026-10-18`
- Updated: `2026-10-23`
- Authorization: 사용자의 현재 PRD 범위 전체 구현 요청. 범위 확대는 별도 검토한다.

## Goal And Acceptance Contract
- AC1: 후보 경로는 선택 제안이며 등록 동의 없이 수집하지 않음.
- AC2: 빈 세션/Context·모델 건너뛰기 지원, 첫 가져오기와 주기 실행 중복 방지.
- AC3: 기존 설정·소스·핀·기록 보존, 온보딩 강제 반복 없음.
- AC4: 실제 메인 화면 위의 단계형 설정 창에서 이전·다음·건너뛰기를 제공한다.
  다음은 입력한 소스/문서 경로를 저장하고 오류 시 해당 단계에 머문다. 완료 전
  앱 종료는 미완료 상태를 유지하며, 모델 설치는 명시적 선택만 허용한다.

## Scope Boundary
- In: 위 계약과 PRD의 C10 결과.
- Out: 데이터 물리적 이동, 새 외부 전송, 제품 제외 기능의 설치형 활성화, 유료 배포·자동 업데이트.

## Surface Lanes
- Contract/data: 공통 설정·소스·검색·복구의 값별 정본. Contract 평가 담당은 primary agent.
- Product/runtime: 해당 화면과 backend 또는 macOS 실행부. Functional/Design/Interaction 평가 범위는 실제 변경과 실행 근거로 보고한다.

## Dependencies
- C06 / FEAT-0133, C07 / FEAT-0134, C08 / FEAT-0135, C09 / FEAT-0136, C13 / FEAT-0140

## State And Interaction
- Loading/empty/error/success를 구분한다. 원본·기존 사용자 상태를 실패 시 보존한다.
- 화면 변경은 기존 디자인을 extend하며 입력·조회·읽기 상태와 포커스를 보존한다.

## Contract Surfaces And Regression
- 기존 source/session ID, frozen Usage attribution, 도메인 정본, 설치형 범위, 로컬 데이터 보존.
- 기존 개발판 학습·Workstream 기능의 변경은 이 Feature 범위 밖이다.

## Pass Or Fail Checks
- AC1: 후보 경로는 선택 제안이며 등록 동의 없이 수집하지 않음.
- AC2: 빈 세션/Context·모델 건너뛰기 지원, 첫 가져오기와 주기 실행 중복 방지.
- AC3: 기존 설정·소스·핀·기록 보존, 온보딩 강제 반복 없음.
- AC4: 단계형 모달의 다음 저장·오류 유지·이전·건너뛰기·미완료 재실행과 모델의 명시적 설치를 검증한다.
- 각 조건의 코드 검토와 실제 실행 근거를 분리한다. 미실행 검증은 PASS로 간주하지 않는다.

## Harness Trace
- Spec: [SPEC-0137](../spec/spec-0137-first-run-local-setup.md)
- Run: [run-20261018-175-first-run-local-setup](../run/run-20261018-175-first-run-local-setup.md). 검증 결과는 Run과 평가 기록에서 구분한다.

## Continuity Notes
- `2026-10-23`: 하단 단계 점과 차분한 화면 전환을 요청해
  [Run 185](../run/run-20261023-185-onboarding-visual-refinement.md)에서 기존 디자인
  규칙 안에 Tesla의 상호작용 감각을 적용한다. 네 단계와 저장·건너뛰기 계약은 유지한다.
- `2026-10-23`: 사용자가 단독 안내 페이지를 단계형 모달로 바꾸도록 요청했다.
  [Run 184](../run/run-20261023-184-first-use-overlay-wizard.md)가 이 보정의 구현·검증과
  앱 교체를 소유한다. 전체 Feature의 기존 수용 범위와 미확인 한계는 유지한다.
- `2026-10-18`: C10를 승인된 구현 경계로 구체화했다. foundation의 필드별 계약을 먼저 고정하고 후속 구현은 의존성 순서를 따른다.

## Implementation And Evidence — 2026-10-19

승인된 구현과 로컬 검증을 완료했다. [통합 기능 평가](../evaluation/eval-0139-functional-standalone-test-app.md)와
[계약 평가](../evaluation/eval-0139-contract-standalone-test-app.md)가 자동 검사·브라우저·동봉 앱·실제 모델 실행의
범위를 소유한다. [화면/상호작용 평가](../evaluation/eval-0139-design-standalone-test-app.md)의 실제 WebView 조작 근거와
PRD A12의 팀원 Mac 전달 확인이 남아 있어 전체 제품 수용은 `blocked`로 둔다.
구현 미착수나 새로운 제품 방향 미결정이라는 뜻은 아니다. 원본·설정·기존 개발 작업을
보존했으며, Drive 업로드·팀원 통지·Git 커밋/공개는 수행하지 않았다.
