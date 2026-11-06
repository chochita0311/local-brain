# FEAT-0159: Agent-Assisted macOS Trial Build And Install

## Metadata

- ID: `feat-0159`
- Status: `passed`
- Type: `product`
- Surface: `infra`
- Execution Profile: `infra-devtool`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Created: `2026-11-05`
- Updated: `2026-11-05`

## Goal And Acceptance Contract

사용자가 Git 저장소를 clone/pull한 뒤 에이전트에게 Apple Silicon 체험 앱의 로컬
빌드·설치를 요청하고 실제 앱을 실행한다. 도구 준비부터 소스 식별·빌드·설치·첫 사용·
업데이트까지 재현 가능한 한 경로로 제공한다. 앱과 로컬 출력·안내·버전·소스/빌드 출처·
시각·플랫폼·체크섬이 같은 빌드를 가리킨다.

- 기존 개인 데이터/설정/캐시/원본/가중치가 프로그램 ZIP에 들어가지 않는다.
- README 요청문에서 설치 가이드와 기존 개발 가이드의 지원된 native 명령으로 이어진다.
  Git·uv/Python 3.11·Xcode CLI·Rust/Cargo·Node/npm을 확인하고 필요한 도구를 준비한다.
  개발 서버를 켠 사실을 native 앱 설치 성공으로 처리하지 않는다.
- 빌드 시점의 소스와 변경 유무를 정확히 나타내며 미커밋 빌드를 깨끗한 commit 빌드로
  표시하지 않는다. About과 manifests/Info.plist/BUILD-INFO의 앱 버전이 일치한다.
- 로컬 빌드한 앱의 실제 설치/실행 위치를 확인한다. 모델 없는 첫 사용, Docs, 기존
  설정/소스/기록 보존과 완전 종료를 확인한다. 사용자의 첫 설치 재현과 빌드/소스 검사,
  직접 native 조작을 구분하고 못 한 부분은 미검증으로 남긴다.
- 업데이트는 완전 종료 → 로컬 변경을 보존한 소스 갱신 → 재빌드 → 앱 교체 → 기존 자료
  확인이다. `git pull`만으로 frozen 앱이 바뀌었다고 안내하거나 DB/설정을 초기화하지 않는다.
- 현재 서명은 ad-hoc/미공증이다. 일반 보안 설정의 공개 배포 완료나 Apple 제출을
  자동으로 포함하지 않는다. 가입·결제·서명 자격 증명 사용·업로드/공지 권한은 별도다.

## Scope, Dependencies And State

- In: 사용자별 checkout/에이전트 설치 경로·도구 준비·build metadata·패키징·checksum·실제 frozen/native 확인·첫 사용과 업데이트 안내.
- Out: 중앙 빌드/다운로드 채널 선행 구축, 자동 업데이트, 공개 게시, 유료 가입, 공증 제출, Windows 실행 증거 대체.
- Dependencies: FEAT-0155–0158의 Mac 전달 범위와 필요한 검사 완료. 기존 Tauri/PyInstaller 경로를 사용한다.
- Surface lane: infra/runtime; Contract는 provenance/privacy/version, Functional은 실제 전달 파일을 검증한다.
- Contract surfaces: README 요청문·설치/개발 가이드·build command·로컬 app/ZIP·manifest version·BUILD-INFO·checksum·동봉 내용과 업데이트/저장 경계.
- Failure state: 검증/경로/서명 검사 실패 시 성공한 새 전달물로 발표하지 않고 기존 파일의 정체를 보존한다.

## Pass Or Fail And Regression Checks

checkout과 요청문에서 도구/빌드 절차를 재현하고 로컬 출력의 출처·checksum·프로그램-only/
privacy·서명·bundle 경로 검사를 수행한다. 합성 설정으로 frozen backend/실제 앱의
제공 화면·Docs·설정 상태·종료를 확인한다. 다른 체험자의 자기 PC에서 소스 빌드·설치·
첫 사용 결과와 기존 사용자의 재빌드/교체 후 보존을 가능한 근거로 각각 기록한다.
사전 빌드 ZIP 전달을 택할 때의 다운로드/수신자 검사와 공개 배포 수용은 별도다.
파일 생성이나 개발 서버 성공만으로 native 설치·체험자 실행·공개 배포까지 통과하면 실패다.

## Harness Trace

- Spec: [SPEC-0159](../spec/spec-0159-identifiable-macos-trial-build.md).
- Run: [Run235](../run/run-20261105-235-identifiable-macos-trial-build.md).
- Evaluation: [Mac delivery](../evaluation/eval-0155-early-access-macos-delivery.md).
- Execution profile: `infra-devtool`.

## Continuity Notes

- `2026-11-05`: 첫 전달을 중앙 ZIP 다운로드에서 사용자별 Git checkout/에이전트 로컬 빌드·설치로 정정했다. 빌드 식별·자료 보존·실제 앱 검증은 유지하며 유료 가입·서명/공증은 현재 설치의 선행 조건이 아니다. Feature는 검토 전 draft다.

## Execution Authorization

- `2026-11-05`: 사용자가 “모두 반영”을 지시했다. 숨긴 Workflow/Workstream의 내부 의존 경로까지 정리하고, 한국어 기본·영문 전환 Docs, 저장공간 안내, 로컬 재빌드를 실행한다. Windows 실제 실행은 검증 환경이 생긴 뒤 확인한다.

## Local Delivery Outcome

- `2026-11-05`: 승인된 Mac 구현과 로컬 빌드 검증을 마쳤다. [통합 평가](../evaluation/eval-0155-early-access-macos-delivery.md)에 source/browser/frozen/native 증거와 수신자·Windows·공개 서명 미검증을 구분했다. 원격 push는 수행하지 않았다.
