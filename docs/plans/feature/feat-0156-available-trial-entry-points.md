# FEAT-0156: Available Trial Entry Points

## Metadata

- ID: `feat-0156`
- Status: `passed`
- Type: `product`
- Surface: `mixed`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Created: `2026-11-05`
- Updated: `2026-11-05`

## Goal And Acceptance Contract

체험판에서 보이는 안내와 조작은 실제 제공 중인 화면으로 연결된다. 이미 차단된
`/sources`를 열어 주는 대신 소스 관리에는 기존 Settings를 사용한다.

- 공통 메뉴와 Sessions List·Chart의 관리·동기화 결과·빈 상태·오류/복구 링크를 확인한다.
  현재 확인된 두 `/sources` 진입점을 제거하거나 올바른 설정/상태 진입점으로 바꾼다.
- 성공·부분 실패·전체 실패의 최초 응답과 이후 갱신 안내가 같은 제공 범위를 설명한다.
- 기존 웹 Sources, 데스크톱 경로 차단·인증, 명시적 소스 등록, 동기화·기록 보존은 유지한다.

## Scope And Surface Lanes

- In: 앱에서 도달하는 공통 탐색·Sessions List/Chart·동기화 안내와 설정 진입.
- Out: 새로운 Sources 화면, 수집/저장 의미 변경, 개발/중단 기능 복귀, 전면 재설계.
- Lanes: backend composition and frontend templates/shared settings entry/browser updates; Builder owns implementation, Contract/Design/Functional/UX evaluate the preserved capability boundary and rendered states.
- Dependencies: FEAT-0155의 제공 기능 계약. 기존 Settings의 소스 관리 동작을 재사용한다.
- Contract surfaces: 제공 중인 설정 진입·기존 URL/상태 의미; API/DB 변경은 의도하지 않는다.

## Entry, State And Exit

Sessions/Chart에서 관리 또는 동기화 결과 안내를 사용한다. 설정은 원래 화면 위에서 열리고
닫으면 원래 선택/필터로 돌아간다. 수집 결과의 성공/부분 실패/실패와 자료 없음 상태를
구분한다. 설정을 여는 동작이 원본 등록·수집·모델 작업을 시작하지 않는다.

## Pass Or Fail And Regression Checks

데스크톱 인증을 적용한 합성 runtime에서 List/Chart와 결과 상태를 렌더하고 실제 조작으로
제공 중인 목적지에 도달해야 한다. 키보드·좁은 화면·설정 닫기/복귀를 확인한다. 같은
소스의 개발 웹 링크와 데스크톱 직접 경로 차단도 확인한다. 정적 검색만으로 화면 검증을
대체하지 않는다. Windows 네이티브 증거는 FEAT-0160에서 별도로 확인한다.

## Harness Trace

- Spec: [SPEC-0156](../spec/spec-0156-available-trial-entry-points.md).
- Run: [Run232](../run/run-20261105-232-available-trial-entry-points.md).
- Evaluation: [Mac delivery](../evaluation/eval-0155-early-access-macos-delivery.md).
- Execution profile: `fullstack-product`.

## Execution Authorization

- `2026-11-05`: 사용자가 “모두 반영”을 지시했다. 숨긴 Workflow/Workstream의 내부 의존 경로까지 정리하고, 한국어 기본·영문 전환 Docs, 저장공간 안내, 로컬 재빌드를 실행한다. Windows 실제 실행은 검증 환경이 생긴 뒤 확인한다.

## Approved Dependency Completion

- 데스크톱의 비제공 패키지를 route뿐 아니라 reference callback, background maintenance, startup cache 처리에서도 제외한다. 기존 저장 기록은 보존하고 개발 웹은 기존 기능을 유지한다. 문서 membership, 세션 상세/관련 자료, 이전 search redirect와 동적 갱신도 확인한다.

## Local Delivery Outcome

- `2026-11-05`: 승인된 Mac 구현과 로컬 빌드 검증을 마쳤다. [통합 평가](../evaluation/eval-0155-early-access-macos-delivery.md)에 source/browser/frozen/native 증거와 수신자·Windows·공개 서명 미검증을 구분했다. 원격 push는 수행하지 않았다.
