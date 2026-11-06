# FEAT-0155: Platform Paths And Capabilities

## Metadata

- ID: `feat-0155`
- Status: `passed`
- Type: `foundation`
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Created: `2026-11-05`
- Updated: `2026-11-05`

## Goal And Acceptance Contract

Mac·Windows 체험판의 제공 기능, 원본과 앱 상태의 소유권, 플랫폼별 경로와 검증 상태를
하나의 명확한 계약으로 정한다. 현재 Mac 동작과 Windows 예상안을 구분하며 Windows
실행 환경이 없다는 이유로 예상안을 이미 구현·검증한 계약으로 표현하지 않는다.

- 공통 공개 기능은 Sessions·Sessions Dashboard·선택형 Local Context·키워드/선택형
  로컬 AI 검색·설정·온보딩·Docs다. 중단/개발 기능과 직접 경로 제한을 유지한다.
- 첫 설치는 사용자의 Git clone/pull 후 에이전트 로컬 빌드·설치다. 빌드 도구가 필요한
  설치 단계와 checkout/수동 개발 서버 없이 쓰는 native 앱 실행을 구분한다. 이 흐름이
  미지원 Windows를 동작하게 만들거나 개발 웹 기능을 체험판에 추가하지 않는다.
- Native Windows의 제안은 `%LOCALAPPDATA%\LocalBrain\Data`와
  `%LOCALAPPDATA%\LocalBrain\Cache`다. 공유 Hub 캐시·원본·앱 실행 파일을 구분한다.
  Mac 경로와 명시적 환경/등록 경로를 보존한다.
- Codex/Claude Home과 세션 폴더, Native Windows와 WSL의 Home·UNC 위치를 구분한다.
  후보 발견은 등록/수집 권한이 아니며 Local Context 원본을 앱 저장소로 이동하지 않는다.
- 잠금·원자적 저장·권한·복구·프로세스 수명의 Windows 요구 조건과 제공하지 않는
  Notes/Spotlight PDF 조작을 정의한다. Windows 구현·설치·AI 실행의 증거는 후속 검증이다.

## Scope, Dependencies And Contract Surfaces

- In: 현재 계약과 [예상 경로/저장 검토](../research/early-access-distribution-readiness.md#windows-expected-paths-and-storage--not-implemented-or-verified)를 대조해 각 사실의 소유자를 정하고 필요한 플랫폼 계약을 작성한다.
- Out: 런타임 이식 구현, Windows 지원 완료 판정, 모델 다운로드·원본 수집, 기존 데이터 이동.
- Dependencies: 승인된 PRD-0027. 실행 Feature 검토에 앞서 플랫폼/저장 계약을 확정한다.
- Contract surfaces: 제공 기능·OS 경로·소스 등록·모델/인덱스 저장·파일 권한/잠금·복원 자격.
- Surface lanes: 계약 단일 lane; Primary/Contract Evaluator가 소유권과 모호성 해소를 확인한다.

## Pass Or Fail And Regression Checks

모든 위치/기능에 현재·제안·미제공·미검증 상태와 소유자가 있고, 후속 Feature가 기본값이나
보존/거부 조건을 추측하지 않아야 한다. 기존 Mac 저장·소스 ID/기록·원본 보호·공유 모델
보존·같은 설치/컴퓨터/스키마 복원 조건을 약화하면 실패다. 실제 Windows 동작이 확인되지
않았다는 한계는 계약 정리 통과와 별도로 남긴다.

## Harness Trace

- Spec: [SPEC-0155](../spec/spec-0155-platform-paths-and-capabilities.md).
- Run: [Run231](../run/run-20261105-231-platform-paths-and-capabilities.md).
- Evaluation: [Mac delivery](../evaluation/eval-0155-early-access-macos-delivery.md).
- Execution profile: `foundation-contract`.

## Continuity Notes

- `2026-11-05`: Mac·Windows와 Windows 선택형 AI가 선택된 뒤 작성. Windows 경로/동작은 예상으로 기록하고 실제 환경에서 검증한다는 사용자 정정을 보존한다.
- `2026-11-05`: 첫 체험을 사용자별 Git/에이전트 로컬 빌드·설치로 정정. 빌드 입력/도구와 앱 runtime의 경계를 추가하고 Windows 미검증을 유지한다.

## Execution Authorization

- `2026-11-05`: 사용자가 “모두 반영”을 지시했다. 숨긴 Workflow/Workstream의 내부 의존 경로까지 정리하고, 한국어 기본·영문 전환 Docs, 저장공간 안내, 로컬 재빌드를 실행한다. Windows 실제 실행은 검증 환경이 생긴 뒤 확인한다.

## Local Delivery Outcome

- `2026-11-05`: 승인된 Mac 구현과 로컬 빌드 검증을 마쳤다. [통합 평가](../evaluation/eval-0155-early-access-macos-delivery.md)에 source/browser/frozen/native 증거와 수신자·Windows·공개 서명 미검증을 구분했다. 원격 push는 수행하지 않았다.
