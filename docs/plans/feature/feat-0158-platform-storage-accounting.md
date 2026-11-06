# FEAT-0158: Platform Storage Accounting

## Metadata

- ID: `feat-0158`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Created: `2026-11-05`
- Updated: `2026-11-05`

## Goal And Acceptance Contract

Settings 저장공간이 그 PC의 실제 데이터/설정·앱 캐시·공유 공개 모델 위치와 용량,
해당 저장 볼륨의 여유 공간을 의미에 맞게 보여 준다. Windows 표시는 현재 예상이며
실제 Windows에서 확인할 때까지 구현/실행 증거로 취급하지 않는다.

- OS와 환경 설정을 해석한 실제 위치를 표시한다. Mac 기존 위치와 사용자 지정 경로를
  보존하고 Windows 경로의 구분자·드라이브·공백·한글/UNC 표시로 원래 식별을 바꾸지 않는다.
- 정상 빈/없는 위치와 읽기 불가·부분 측정을 구분한다. 실패를 `0`으로 가장하지 않는다.
  바이트 계산과 단위 표기를 일치시키고 파일 크기와 할당량의 차이를 유지한다.
- 공유 Hub root 전체의 크기는 다른 모델/도구를 포함할 수 있음을 간결하게 설명한다.
  데이터·개인 인덱스·공개 가중치·프로그램/런타임과 추가 임시 공간을 구분한다.
- 저장소에서 에이전트로 빌드할 때 필요한 Python/Node/Rust 환경·의존성/빌드 캐시와
  앱 상태를 구분한다. 현재 앱 저장공간 집계가 checkout이나 시스템 빌드 도구의 공간을
  모두 포함하는 것처럼 설명하거나 이 작업에서 그 캐시를 임의 정리하지 않는다.
- 여유 공간은 실제 위치의 볼륨 기준이다. 데이터와 모델 위치가 다르면 각 대상의
  여유 공간을 구분하고 같은 볼륨의 공간을 중복 합산하지 않는다.
- 기존 캐시 정리의 앱 소유·비활성·재생성 가능 조건을 보존한다. 원본·DB/설정·공유 모델을
  제거하는 버튼이나 암묵적 정리를 추가하지 않는다.

## Scope And Surface Lanes

- In: storage status의 완전/부분/불가 의미, 실제 경로/볼륨/크기와 기존 설정 화면의 표시.
- Out: 저장 위치 이동 UI, 공유 모델 삭제, 전체 디스크 관리, 예시 용량 고정, 원본 재배치.
- Backend lane: filesystem 계측과 오류/볼륨 결과; Contract/Functional 평가.
- Frontend lane: 기존 Settings rows·안내·단위·로딩/오류/복구; Design/Functional/UX 평가.
- Dependencies: FEAT-0155의 경로/소유 계약. Docs의 관리 의미는 FEAT-0157과 같은 사실을 사용한다.
- Contract surfaces: `/api/settings/storage`, 경로 표시·바이트/불가 의미·cache clear의 기존 범위.

## Entry, State And Exit

저장공간 탭을 열면 읽기만 수행한다. 읽는 중·빈 위치·정상 계측·부분 실패·읽기 실패를
구분하고 다시 읽을 수 있어야 한다. 탭 전환이 모델 다운로드·백업·정리를 시작하지 않는다.
캐시 정리는 기존 명시적 동작이며 결과 뒤 새 상태를 읽는다.

## Pass Or Fail And Regression Checks

합성 디렉터리와 volume 응답으로 정상/빈/불가/부분, 같은/다른 볼륨, 환경변수 경로와
단위를 검증하고 실제 Mac Settings의 읽기/재시도/좁은 화면을 확인한다. 소유하지 않은
파일과 공유 가중치를 정리하지 않는 회귀 검증이 필요하다. Windows 경로 문자열 모형은
native filesystem 증거가 아니며 ACL·drive·UNC·모델 볼륨은 FEAT-0160에서 실제 확인한다.

## Harness Trace

- Spec: [SPEC-0158](../spec/spec-0158-platform-storage-accounting.md).
- Run: [Run234](../run/run-20261105-234-platform-storage-accounting.md).
- Evaluation: [Mac delivery](../evaluation/eval-0155-early-access-macos-delivery.md).
- Execution profile: `fullstack-product`.

## Execution Authorization

- `2026-11-05`: 사용자가 “모두 반영”을 지시했다. 숨긴 Workflow/Workstream의 내부 의존 경로까지 정리하고, 한국어 기본·영문 전환 Docs, 저장공간 안내, 로컬 재빌드를 실행한다. Windows 실제 실행은 검증 환경이 생긴 뒤 확인한다.

## Local Delivery Outcome

- `2026-11-05`: 승인된 Mac 구현과 로컬 빌드 검증을 마쳤다. [통합 평가](../evaluation/eval-0155-early-access-macos-delivery.md)에 source/browser/frozen/native 증거와 수신자·Windows·공개 서명 미검증을 구분했다. 원격 push는 수행하지 않았다.
