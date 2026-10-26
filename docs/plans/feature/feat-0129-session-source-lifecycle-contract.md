# FEAT-0129: 사용자 세션 소스와 수집 소유 계약

## Metadata
- ID: `feat-0129`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md) — C02
- Created: `2026-10-18`
- Updated: `2026-10-26`
- Authorization: 사용자의 현재 PRD 범위 전체 구현 요청. 범위 확대는 별도 검토한다.

## Goal And Acceptance Contract
- AC1: 기존 숫자 `sources.id`를 유일한 프로필 식별자로 사용하고 provider·표시 이름·에이전트 홈·실제 세션 root를 구분한다. 런타임 문자열 키·별도 alias 저장소는 두지 않는다.
- AC2: 추가·수정·명시적 같은 소스 재연결·해제. 해제 기록 보존/기본 검색 제외, 기존 목록의 보존 기록 조회 유지.
- AC3: 설정·수집·복원은 같은 로컬 잠금으로 조정; 실패는 원본·기존 기록 보존.

## Scope Boundary
- In: 위 계약과 PRD의 C02 결과.
- Out: 데이터 물리적 이동, 새 외부 전송, 제품 제외 기능의 설치형 활성화, 유료 배포·자동 업데이트.

## Surface Lanes
- Contract/data: 공통 설정·소스·검색·복구의 값별 정본. Contract 평가 담당은 primary agent.
- Product/runtime: 해당 화면과 backend 또는 macOS 실행부. Functional/Design/Interaction 평가 범위는 실제 변경과 실행 근거로 보고한다.

## Dependencies
- C01 / FEAT-0128

## State And Interaction
- Loading/empty/error/success를 구분한다. 원본·기존 사용자 상태를 실패 시 보존한다.
- 화면 변경은 기존 디자인을 extend하며 입력·조회·읽기 상태와 포커스를 보존한다.

## Contract Surfaces And Regression
- 기존 source/session ID, frozen Usage attribution, 도메인 정본, 설치형 범위, 로컬 데이터 보존.
- 기존 개발판 학습·Workstream 기능의 변경은 이 Feature 범위 밖이다.

## Pass Or Fail Checks
- AC1: 기존 숫자 `sources.id`를 유일한 프로필 식별자로 사용하고 provider·표시 이름·에이전트 홈·실제 세션 root를 구분한다. 런타임 문자열 키·별도 alias 저장소는 두지 않는다.
- AC2: 추가·수정·명시적 같은 소스 재연결·해제. 해제 기록 보존/기본 검색 제외, 기존 목록의 보존 기록 조회 유지.
- AC3: 설정·수집·복원은 같은 로컬 잠금으로 조정; 실패는 원본·기존 기록 보존.
- 각 조건의 코드 검토와 실제 실행 근거를 분리한다. 미실행 검증은 PASS로 간주하지 않는다.

## Harness Trace
- Spec: [SPEC-0129](../spec/spec-0129-session-source-lifecycle-contract.md)
- Run: [run-20261018-167-session-source-lifecycle-contract](../run/run-20261018-167-session-source-lifecycle-contract.md). 검증 결과는 Run과 평가 기록에서 구분한다.

## Continuity Notes
- `2026-10-24`: 초기 숫자 프로필 제안은 문자열 namespace를 내부 호환용으로 남겼으나, 사용자가 이를 제거하도록 정정했다. 최종 [PK-only 계약](../spec/spec-0133-user-managed-source-settings.md#source-primary-key-only--2026-10-24)과 [Run 196](../run/run-20261024-196-source-primary-key-identity.md)이 AC1을 대체한다. 일회성 이전만 옛 형식을 읽고, 기존 Source/Session/Event/Usage PK·원본·귀속·수명주기 계약을 보존한다.
- `2026-10-18`: C02를 승인된 구현 경계로 구체화했다. foundation의 필드별 계약을 먼저 고정하고 후속 구현은 의존성 순서를 따른다.

- `2026-10-18`: [Contract evaluation](../evaluation/eval-0129-contract-session-source-lifecycle-contract.md) passed; runtime evidence remains separately scoped.
