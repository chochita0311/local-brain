# FEAT-0130: 모델 선택 검색 계약

## Metadata
- ID: `feat-0130`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md) — C03
- Created: `2026-10-18`
- Updated: `2026-10-18`
- Authorization: 사용자의 현재 PRD 범위 전체 구현 요청. 범위 확대는 별도 검토한다.

## Goal And Acceptance Contract
- AC1: 기존 FTS5 AND 토큰 검색을 모델 없이 제공.
- AC2: 자연어 검색의 유효 원문 허용 조건을 키워드 결과에도 적용.
- AC3: 사용자 질의 유지; 준비·실패·0건 구분; 모델 자동 설치/원격 fallback 없음.

## Scope Boundary
- In: 위 계약과 PRD의 C03 결과.
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
- AC1: 기존 FTS5 AND 토큰 검색을 모델 없이 제공.
- AC2: 자연어 검색의 유효 원문 허용 조건을 키워드 결과에도 적용.
- AC3: 사용자 질의 유지; 준비·실패·0건 구분; 모델 자동 설치/원격 fallback 없음.
- 각 조건의 코드 검토와 실제 실행 근거를 분리한다. 미실행 검증은 PASS로 간주하지 않는다.

## Harness Trace
- Spec: [SPEC-0130](../spec/spec-0130-search-availability-contract.md)
- Run: [run-20261018-168-search-availability-contract](../run/run-20261018-168-search-availability-contract.md). 검증 결과는 Run과 평가 기록에서 구분한다.

## Continuity Notes
- `2026-10-18`: C03를 승인된 구현 경계로 구체화했다. foundation의 필드별 계약을 먼저 고정하고 후속 구현은 의존성 순서를 따른다.

- `2026-10-18`: [Contract evaluation](../evaluation/eval-0130-contract-search-availability-contract.md) passed; runtime evidence remains separately scoped.
