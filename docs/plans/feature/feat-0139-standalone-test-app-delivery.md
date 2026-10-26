# FEAT-0139: 독립 테스트 앱 전달

## Metadata
- ID: `feat-0139`
- Status: `blocked`
- Type: `product`
- Surface: `infra`
- Execution Profile: `infra-devtool`
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md) — C12
- Created: `2026-10-18`
- Updated: `2026-10-20`
- Authorization: 사용자의 현재 PRD 범위 전체 구현 요청. 범위 확대는 별도 검토한다.

## Goal And Acceptance Contract
- AC1: 개인 자료 없는 Apple Silicon .app ZIP, ad-hoc 서명·수동 교체 안내.
- AC2: 로컬 패키지 실행 근거와 다운로드한 팀원 Mac 실행 근거 구분.
- AC3: 확인한 환경·지원 한계·모델/인덱스 별도 공간 기록.

## Scope Boundary
- In: 위 계약과 PRD의 C12 결과.
- Out: 데이터 물리적 이동, 새 외부 전송, 제품 제외 기능의 설치형 활성화, 유료 배포·자동 업데이트.

## Surface Lanes
- Contract/data: 공통 설정·소스·검색·복구의 값별 정본. Contract 평가 담당은 primary agent.
- Product/runtime: 해당 화면과 backend 또는 macOS 실행부. Functional/Design/Interaction 평가 범위는 실제 변경과 실행 근거로 보고한다.

## Dependencies
- C04 / FEAT-0131, C05 / FEAT-0132, C06 / FEAT-0133, C07 / FEAT-0134, C08 / FEAT-0135, C09 / FEAT-0136, C10 / FEAT-0137, C11 / FEAT-0138, C13 / FEAT-0140

## State And Interaction
- Loading/empty/error/success를 구분한다. 원본·기존 사용자 상태를 실패 시 보존한다.
- 화면 변경은 기존 디자인을 extend하며 입력·조회·읽기 상태와 포커스를 보존한다.

## Contract Surfaces And Regression
- 기존 source/session ID, frozen Usage attribution, 도메인 정본, 설치형 범위, 로컬 데이터 보존.
- 기존 개발판 학습·Workstream 기능의 변경은 이 Feature 범위 밖이다.

## Pass Or Fail Checks
- AC1: 개인 자료 없는 Apple Silicon .app ZIP, ad-hoc 서명·수동 교체 안내.
- AC2: 로컬 패키지 실행 근거와 다운로드한 팀원 Mac 실행 근거 구분.
- AC3: 확인한 환경·지원 한계·모델/인덱스 별도 공간 기록.
- 각 조건의 코드 검토와 실제 실행 근거를 분리한다. 미실행 검증은 PASS로 간주하지 않는다.

## Harness Trace
- Spec: [SPEC-0139](../spec/spec-0139-standalone-test-app-delivery.md)
- Run: [run-20261018-177-standalone-test-app-delivery](../run/run-20261018-177-standalone-test-app-delivery.md). 검증 결과는 Run과 평가 기록에서 구분한다.

## Continuity Notes
- `2026-10-18`: C12를 승인된 구현 경계로 구체화했다. foundation의 필드별 계약을 먼저 고정하고 후속 구현은 의존성 순서를 따른다.

## Implementation And Evidence — 2026-10-19

승인된 구현과 로컬 검증을 완료했다. [통합 기능 평가](../evaluation/eval-0139-functional-standalone-test-app.md)와
[계약 평가](../evaluation/eval-0139-contract-standalone-test-app.md)가 자동 검사·브라우저·동봉 앱·실제 모델 실행의
범위를 소유한다. [화면/상호작용 평가](../evaluation/eval-0139-design-standalone-test-app.md)의 실제 WebView 조작 근거와
PRD A12의 팀원 Mac 전달 확인이 남아 있어 전체 제품 수용은 `blocked`로 둔다.
구현 미착수나 새로운 제품 방향 미결정이라는 뜻은 아니다. 원본·설정·기존 개발 작업을
보존했으며, Drive 업로드·팀원 통지·Git 커밋/공개는 수행하지 않았다.

- `2026-10-19`: [시작 인증 수정](../fix/fix-0131-desktop-startup-cookie.md)에서 초기 전달본의 첫 화면 401/한글 깨짐을 재현하고 수정했다. 같은 경로의 앱/ZIP을 교체하며 WKWebView의 실제 본문과 인증 API 검증을 추가했다. 원본 창/프로세스 관측을 첫 화면 성공으로 확대하지 않는다.
- `2026-10-20`: [Python 빌드 경로 제거](../run/run-20261020-182-portable-python-build-metadata.md)에서 압축된 인터프리터 메타데이터의 개인 설치 경로 20개 필드를 실행 중인 번들 위치 기준으로 바꿨다. 재발 방지 검사, 관련 테스트 42개, 이동한 런타임 실행, 새 앱/ZIP 무결성 및 실제 앱 재시작을 확인했다. 사용자 설정 3개 파일은 보존했다. 다른 Mac 실행과 전체 제품 수용의 남은 조건은 그대로다.
