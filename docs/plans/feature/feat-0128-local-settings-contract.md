# FEAT-0128: 공통 로컬 설정 계약

## Metadata
- ID: `feat-0128`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md) — C01
- Created: `2026-10-18`
- Updated: `2026-10-18`
- Authorization: 사용자의 현재 PRD 범위 전체 구현 요청. 범위 확대는 별도 검토한다.

## Goal And Acceptance Contract
- AC1: TOML schema 1; 로컬 파일의 원자적 저장·revision 충돌·0600 권한.
- AC2: 일반 설정은 로컬 설정 파일의 값을 사용하고 없는 항목만 기본값으로 채운다. 환경변수로 일반 설정을 덮어쓰지 않으며 기존 파일·알 수 없는 필드·버전 오류 보존 계약을 유지한다.
- AC3: 시작 화면은 다음 시작, 시간대·표시·동기화 설정은 즉시 다음 동작에 적용. 기존 도메인 정본과 데이터 위치 보존.

## Scope Boundary
- In: 위 계약과 PRD의 C01 결과.
- Out: 데이터 물리적 이동, 새 외부 전송, 제품 제외 기능의 설치형 활성화, 유료 배포·자동 업데이트.

## Surface Lanes
- Contract/data: 공통 설정·소스·검색·복구의 값별 정본. Contract 평가 담당은 primary agent.
- Product/runtime: 해당 화면과 backend 또는 macOS 실행부. Functional/Design/Interaction 평가 범위는 실제 변경과 실행 근거로 보고한다.

## Dependencies
- 없음

## State And Interaction
- Loading/empty/error/success를 구분한다. 원본·기존 사용자 상태를 실패 시 보존한다.
- 화면 변경은 기존 디자인을 extend하며 입력·조회·읽기 상태와 포커스를 보존한다.

## Contract Surfaces And Regression
- 기존 source/session ID, frozen Usage attribution, 도메인 정본, 설치형 범위, 로컬 데이터 보존.
- 기존 개발판 학습·Workstream 기능의 변경은 이 Feature 범위 밖이다.

## Pass Or Fail Checks
- AC1: TOML schema 1; 로컬 파일의 원자적 저장·revision 충돌·0600 권한.
- AC2: 일반 설정은 로컬 설정 파일의 값을 사용하고 없는 항목만 기본값으로 채운다. 환경변수로 일반 설정을 덮어쓰지 않으며 기존 파일·알 수 없는 필드·버전 오류 보존 계약을 유지한다.
- AC3: 시작 화면은 다음 시작, 시간대·표시·동기화 설정은 즉시 다음 동작에 적용. 기존 도메인 정본과 데이터 위치 보존.
- 각 조건의 코드 검토와 실제 실행 근거를 분리한다. 미실행 검증은 PASS로 간주하지 않는다.

## Harness Trace
- Spec: [SPEC-0128](../spec/spec-0128-local-settings-contract.md)
- Run: [run-20261018-166-local-settings-contract](../run/run-20261018-166-local-settings-contract.md). 검증 결과는 Run과 평가 기록에서 구분한다.

## Continuity Notes
- `2026-10-18`: C01를 승인된 구현 경계로 구체화했다. foundation의 필드별 계약을 먼저 고정하고 후속 구현은 의존성 순서를 따른다.

- `2026-10-18`: [Contract evaluation](../evaluation/eval-0128-contract-local-settings-contract.md) passed; runtime evidence remains separately scoped.
