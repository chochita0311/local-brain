# FEAT-0160: Windows x64 Local AI Trial

## Metadata

- ID: `feat-0160`
- Status: `draft`
- Type: `product`
- Surface: `mixed`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Created: `2026-11-05`
- Updated: `2026-11-05`
- Environment limit: 현재 Windows PC/VM/CI 없음. 이 단계는 예상 동작/준비 기록이며 실제 Windows 검증은 미실시.

## Goal And Acceptance Contract

Windows x86_64에서도 개인 세션·문서를 연결하고 모델 없는 키워드 검색과 선택형 로컬
AI 검색을 사용하는 설치 앱을 제공한다. 현재 Windows 환경이 없으므로 아래는 목표와
예상 동작이다. 실제 빌드/설치/실행 전에는 Windows 지원 완료로 표시하지 않는다.

첫 설치 목표는 Mac과 같은 Git checkout → 에이전트의 로컬 빌드·설치 → 앱 실행이다.
현재 Windows 이식이나 지원된 빌드 명령이 생긴 것은 아니며, 에이전트가 있다는 이유로
Mac 빌더를 그대로 실행해 성공한다고 안내하지 않는다. 중앙 사전 빌드 파일 배포는
지금의 설치 선행 조건이 아니다.

- Native Windows/명시적 WSL 원본, Local Context 등록, 데이터/캐시/공유 모델의 실제
  경로와 사용자 권한을 처리한다. 기본 경로와 환경변수·사용자 지정 Home을 구분한다.
- Unix 전용 import/잠금·소유권/원자적 저장·경로·시간대·프로세스/`.exe` 실행을 이식하고
  Mac의 기존 계약과 소스 ID·원본·기록 보존을 유지한다. Windows 전용 미제공 조작은 숨긴다.
- 앱에 Python/AI 실행 라이브러리를 포함하되 모델 다운로드는 명시적이다. 다운로드,
  검증·등록·인덱싱·검색·취소·실패/재시도와 모델 없는 시작을 제공한다.
- 프로그램 설치, WebView2, 파일 선택, 창/완전 종료와 backend 수명, 교체 후 기록/설정
  보존을 실제 Windows에서 확인한다. 최소 OS와 실제 설치/모델 메모리·크기는 검증 때 명시한다.

## Scope And Surface Lanes

- In: 선택형 로컬 AI를 포함한 현재 공개 핵심 기능의 Windows 경로·runtime·설치·안내.
- Out: Windows ARM, Linux 앱, 자동 업데이트, GPU/CUDA 필수화, Notes/Spotlight PDF의 무검증 제공, 클라우드 서비스.
- Platform/backend lane: 파일·잠금·저장·모델·수명; Contract/Functional 평가. FEAT-0155가 선행한다.
- Frontend/content lane: 실제 Windows에서 제공하는 기능·경로·Storage·Docs/파일 선택; Design/Functional/UX 평가.
- Infra lane: 대상 OS의 Python backend·Tauri x64 installer·출처/체크섬; Contract/Functional 평가.
- Dependencies: FEAT-0155–0158의 계약/공통 기능. 실제 빌드·실행 평가에는 Windows 환경이 필요하다.
- Contract surfaces: platform storage/locks, source/model paths, packaging and native lifecycle; Windows 변경이 Mac 기본값·복구 자격을 바꾸지 않는다.

## State Expectations And Evidence Boundary

소스/모델 없음은 정상 시작 경로다. 모델은 준비/다운로드/인덱싱/사용 가능/실패/취소를
구분한다. 경로 읽기 불가·부분 상태·동시 작업·용량 부족은 명시적 실패이며 기존 기록과
완성된 인덱스를 보존한다. 제공하지 않는 Mac 조작을 클릭할 수 있는 상태로 남기지 않는다.

지금은 예상 경로와 동작, 이식 경계·후속 검사만 작성한다는 사용자 지시를 따른다.
Mac의 모의 경로/정적 검사 또는 installer 설정 추가는 Windows native 실행 증거가 아니다.

## Pass Or Fail And Regression Checks

[Windows 후속 검사표](../research/early-access-distribution-readiness.md#windows-validation-still-required)의
경로/등록·설치/수명·선택형 AI·저장공간·쓰기/복구 항목을 실제 Windows에서 확인한다.
빌드 환경이 없으면 관련 Evidence Coverage는 `unavailable`/`unverified`로 남기고 feature를
통과/배포 완료로 올리지 않는다. 같은 수정 뒤 Mac 동작과 원본/기록/모델 보호의 회귀도 확인한다.

## Harness Trace

- Active spec/run/evaluation/fix: none; Feature boundary review required.
- Execution profile: `fullstack-product`; actual Windows validation awaits the target environment.

## Continuity Notes

- `2026-11-05`: Git 저장소를 받은 체험자의 에이전트 로컬 빌드·설치를 첫 경로로 반영했다. Windows의 경로·AI 포함 목표와 미구현/미검증·후속 실제 환경 검사는 유지한다.
