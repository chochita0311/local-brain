# PRD-0027: Early-Access Distribution And Bilingual App Docs

## Metadata

- ID: `prd-0027`
- Status: `in-loop`
- Owner role: `human`
- Created: `2026-11-05`
- Updated: `2026-11-06`
- Planning role: `PRD Normalizer`
- Approval boundary: 2026-11-05 사용자가 Mac·Windows 동시 제공과 Windows의 선택형
  로컬 AI 검색 포함을 선택했다. Windows 일반 경로·Local Context·모델 설치·저장공간을
  범위에 추가했고, Windows 실행 환경이 없으므로 지금은 예상 동작으로 작성하며 실제
  환경에서 후속 검증하도록 정정했다. 제품 범위가 승인되었고 후속 “모두 반영” 지시로 Mac Feature0155–0159 실행도 승인되었다. Windows는 예상안과 실제 검증의 경계를 유지한다. 이 기록은 Windows 구현·빌드·실행이나 배포 완료를 승인 판정하지 않는다.
  기존 테스트 앱과 Docs의 승인·실행 기록은 각 원래 소유자에 남긴다.
- Initial installation decision: 사용자는 먼저 Git 저장소를 clone/pull한 사람이 자기
  에이전트에게 로컬 빌드·설치를 요청하는 과정을 선택했다. 설치 단계에는 개발 도구가
  필요하며, 설치 후에는 빌드된 앱을 사용한다. 사전 빌드 파일 배포·서명/공증은 첫 체험의
  선행 조건에서 분리한다. Windows는 이 방식에서도 현재 미구현·미검증 상태를 유지한다.

## Request Summary

사용을 희망한 사람들에게 실제로 써 보고 의견을 줄 수 있는 작은 LocalBrain 배포본을
제공한다. 현재 빌드의 최신 여부를 확인하고, 앱에서 접근할 수 없는 기능의 진입점을
감춘다. 앱 내 Docs만 한국어 기본·영문 전환과 간결한 사용 안내로 정리하며,
Windows x86_64 배포 가능성과 일반 다운로드 앱의 설치 조건을 구체화한다.
첫 체험의 설치 경로는 **Git clone/pull → 사용자 에이전트의 로컬 빌드·설치 → 앱 실행**이다.
일반 사용자용 사전 빌드 파일 배포는 후속 단계로 남긴다.

## Source Set

| Source | Authority and limit |
| --- | --- |
| Owner request, 2026-11-05 | 최소한의 사용 가능한 체험 범위, 접근 불가 기능의 숨김, 앱 내 Docs의 한국어 기본·영문 보기, Windows x86_64 가능성 확인. |
| Owner-supplied feedback | 로그인 후 지정된 팀별·발표 후기를 읽었다. 사용 의향과 기대는 실제 설치·사용 성공의 증거가 아니다. 원문·계정·행사 식별정보는 저장소에 복사하지 않는다. |
| [Distribution readiness review](../research/early-access-distribution-readiness.md) | 초기 소스/ZIP 차이와 플랫폼별 제약, 후속 11월 5일 로컬 재빌드 checkpoint를 구분한다. 동봉 backend/격리 WKWebView 확인은 실제 Tauri 조작·수신자·Windows 검증을 대체하지 않는다. |
| [Standalone app PRD](prd-0021-macos-standalone-test-app-and-local-settings.md), [test distribution guide](../../policies/project/standalone-test-app-guide.md) | 현재 Apple Silicon 테스트 앱과 일반 macOS 배포 목표, 서명·공증 및 수신자 검증 경계. |
| [App Docs PRD](prd-0024-deployed-app-docs.md), [In-App Documentation](../../policies/project/app-documentation.md) | 초기 영어 6개 가이드의 내용·경로·패키징 소유권. 이번 Mac 구현으로 한국어 기본·영문 전환이 반영되었으며 현행 계약은 In-App Documentation이 소유한다. |
| [Desktop contract](../../policies/project/desktop-app-and-settings.md), [Feature Availability](../project/feature-availability.md) | 앱의 기존 공개 기능과 중단된 기능의 경계. |
| [Change scope](../../policies/project/change-scope-and-regression.md), [PRD management](../../policies/harness/prd-feature-management.md) | 필요한 종속 변경과 기존 행동 보존, 범위·Feature 승인 및 실행 반환 규칙. |
| [Design Constitution](../../policies/design/design-constitution.md), [Design Evaluation](../../policies/design/design-evaluation.md), [Interaction Evaluation](../../policies/experience/interaction-evaluation.md) | 기존 화면 체계, 가독성·키보드·좁은 화면·상태 전환의 검수 기준. |

## Product Intent

초기 체험자는 Git 저장소를 받고 에이전트에게 빌드·설치를 요청한다. 에이전트가 현재
OS/CPU와 도구를 확인하고 지원되는 빌드 절차로 앱을 준비해, 사용자가 자기 AI 대화
기록을 연결하고 과거 대화를 찾아 다시 읽게 한다. 설치 시 필요한 Git·에이전트·빌드
도구와, 설치 후 앱 사용에 필요한 조건을 구분한다.

설치된 앱은 소스 checkout이나 수동 개발 서버 없이 실행한다. 처음부터 모델을
내려받거나 제공되지 않는 분석·자동화를 이해할 필요가 없어야 한다. 앱의 화면·Docs·
설치 안내와 로컬 빌드 결과가 같은 기능과 지원 환경을 설명해야 한다.

## Confirmed Scope

- 실제 전달할 빌드와 현재 소스의 일치 여부를 확인한다. 버전 이름만으로 최신이라고
  판단하지 않고 전달 파일을 식별할 수 있는 근거를 남긴다.
- 첫 설치는 clone/pull한 checkout에서 에이전트에게 빌드·설치를 요청하는 경로다.
  README에 요청문과 지원 범위를, 설치/개발 가이드에 도구 준비·빌드·앱 실행·검증·
  업데이트 절차를 둔다. 기존 변경을 보존하고 revision/dirty 상태와 실제 결과를 보고한다.
  개발 웹 서버를 띄운 사실을 데스크톱 앱 설치 성공으로 보고하지 않는다.
- 제공하지 않는 기능은 메뉴뿐 아니라 화면 안의 링크·버튼·동기화 결과·안내에서도
  접근을 유도하지 않는다. 기능을 숨기기 위해 기존 기록이나 등록을 삭제하지 않는다.
  소스 등록·수정은 제공 중인 Settings에서 계속 할 수 있어야 한다.
- 현재 앱에서 가능한 사용을 중심으로 체험 범위를 줄인다. 포함 기능과 플랫폼 목표는
  아래 선정 경계로 확정되었다. Mac 구현·로컬 검증 완료와 Windows 후속 이식·검증은
  구분하며, 두 플랫폼 제공 완료에는 각각의 실제 근거가 필요하다.
- Docs는 앱에 보이는 6개 가이드만 대상으로 한다. 한국어를 기본으로 제공하고 같은
  가이드의 영어 보기로 전환할 수 있게 한다. 짧은 설명·단계·표·목록을 내용에 맞게
  사용하되 필요한 조건과 한계를 삭제하지 않는다.
- Windows x86_64에서 빌드·설치·실행 가능한 범위를 정한다. macOS 전용 기능과
  아직 검증하지 않은 기능을 Windows에서 가능한 것처럼 노출하지 않는다.
- 첫 전달의 목표는 Mac·Windows이며 Windows에도 선택형 로컬 AI 검색을 포함한다.
  Windows의 세션 소스·Local Context·모델 원본·개인 인덱스·데이터·설정·캐시 위치와
  실제 저장공간 표시를 다룬다. Windows 실행 환경이 없는 현재 단계에서는 경로와 동작을
  예상으로 명시하고, Windows에서 빌드·실행한 뒤에만 해당 지원과 전달을 검증 완료로 표시한다.
- 일반 배포를 전제로 설치·첫 실행·종료·수동 교체와 개인 자료 보존을 확인한다.
  현재 내부 테스트 ZIP과 기본 보안 설정에서 열리는 공개 배포본의 차이를 유지한다.
  다만 현재 체험의 설치 수용은 사용자의 로컬 소스 빌드 기준이다. 유료 가입·중앙 배포용
  서명/공증·다운로드 채널 준비를 그 선행 조건으로 요구하지 않는다.

## Selected Trial Boundary And Remaining Feature Review

| Area | Selected trial and remaining target evidence |
| --- | --- |
| 핵심 경험 | Codex·Claude Code 소스를 명시적으로 연결 → 동기화 → Sessions에서 찾아 읽기 → 키워드 검색 → 원래 대화로 돌아가기. |
| 첫 설치 | Git clone/pull → 에이전트의 환경/도구 확인 → 지원 절차로 로컬 빌드 → 앱 설치·실행 → 결과와 미확인 항목 보고. 현재 Mac 빌드 경로를 사용하며 Windows를 성공한 설치로 안내하지 않는다. |
| 기존 앱 화면 | Sessions의 List·Chart·pin·상세·하위 세션, Sessions Dashboard, Local Contexts, Settings·시작 설정·Docs를 유지한다. Local Context 등록은 선택 사항이다. |
| 검색 | 두 플랫폼 모두 키워드는 모델 없이 바로 사용하고 로컬 AI 검색은 사용자가 선택하는 추가 기능으로 포함한다. 다운로드·준비 시간·저장공간과 사용 가능한 상태를 구분한다. Windows에서의 실제 동작은 미검증이다. |
| 제공하지 않는 경험 | 개발용 Dashboard/학습·Workstreams·Auto Work·Atlassian·Insights·Session workflow·Schema와 Sources 전용 화면을 체험 기능으로 안내하지 않는다. 중단된 Context Search·Drive도 복귀시키지 않는다. |
| 문서 | 시작하기, 설정, Sessions Dashboard, Sessions, Local Contexts, 검색의 6개 주제를 유지한다. 전체 앱 UI나 저장소 개발 문서 번역은 포함하지 않는다. |
| 플랫폼 | Mac·Windows 동시 제공이 선택되었다. 현재 Mac만 실행 환경이 있으므로 Windows의 경로·동작은 예상/미검증으로 작성하고 실제 Windows 빌드·실행 확인을 후속 게이트로 둔다. 두 플랫폼 제공 완료에는 각각의 실제 배포물 근거가 필요하다. |
| 경로·저장공간 | 원본 세션/문서는 사용자가 등록한 위치에 둔다. 앱 실행 파일, 데이터/설정, 개인 캐시/검색 인덱스, 공유 모델 가중치를 구분하고 OS·환경변수에 따라 해석한 실제 위치와 용량을 표시한다. Windows의 구체적인 경로는 [조사 문서의 예상안](../research/early-access-distribution-readiness.md#windows-expected-paths-and-storage--not-implemented-or-verified)을 검토 기준으로 삼는다. |

## User Flows

1. 저장소를 clone/pull하고 에이전트에게 빌드·설치를 요청한다. 에이전트가 지원 OS·
   아키텍처·소스 revision/dirty 상태와 필요한 도구를 확인하고 지원되는 절차로 앱을
   빌드·설치·실행한다. 미지원 환경이나 실패는 실제 상태로 보고한다.
2. 시작 설정에서 원하는 소스를 연결하거나 나중에 설정하기를 선택한다. 소스가
   없거나 모델을 설치하지 않은 상태도 정상적인 시작 경로다.
3. Session 소스를 동기화하고 자기 대화를 찾는다. 목록·상세·검색을 오가며 원문을
   읽는다. 일부 소스를 읽지 못하면 다른 소스와 보존된 기록은 계속 확인할 수 있다.
4. 소스 관리가 필요하면 제공되는 Settings로 이동한다. 클릭 이후 미제공 화면의
   오류를 만나는 안내 경로가 없어야 한다.
5. Docs를 열면 한국어 가이드가 나온다. 영어 보기는 같은 주제를 유지하고, 가이드
   이동과 뒤로 가기에서도 선택 언어의 의미가 일관된다. 선택은 Docs URL의 `lang`으로
   유지하며 별도 저장 설정이나 앱 전체 언어 전환을 만들지 않는다. 목차 상단의 공통
   언어 메뉴가 이 Docs 전용 동작을 제공한다.
6. 앱과 같은 자료를 쓰는 별도 backend를 완전히 종료한다. 로컬 변경을 보존하며
   소스를 갱신하고 에이전트에게 재빌드·앱 교체를 요청한 뒤 등록·기록·pin·설정을 이어
   쓴다. `git pull`만으로 빌드된 앱이 업데이트되지는 않는다.

## Excluded Scope

- 클라우드 동기화, 조직 공유, 계정 체계, 외부 AI로 개인 자료 전송.
- 스킬 생성·자동화, 에이전트 실행·자동 선택, 도구 간 자동 맥락 연결, 생성 답변이나
  기존 분석 기능의 재도입. 발표에서 기대한 용도라는 이유만으로 포함하지 않는다.
- 자동 업데이트, 새로운 배포 웹사이트, App Store 등록, macOS Intel·Windows ARM·Linux
  지원. 새 기능 없이 현재 전달 경로의 설명을 맞추는 작업과 구분한다.
- 저장소 전체 문서의 한국어화, 문서 관리 구조 재편, 앱 전체 언어 전환.
- 실제 유료 가입·결제, 서명 자격 증명 사용, Apple 제출, 공개 업로드·공지. 해당 행위는
  별도 권한을 필요로 하며 이 초안으로 수행하지 않는다.
- 데이터 삭제·재수집 강제·기존 소스 해제·저장소 이동을 통한 배포 단순화.
- 첫 체험 전에 중앙 빌드/다운로드 서비스나 공증 완료 배포 파일을 반드시 제공하는 일.
  로컬 builder가 생성하는 앱/ZIP은 유지할 수 있으나 외부 파일 전달이 기본 설치 경로는 아니다.

## Uncertainty

| Item | Current decision and remaining uncertainty |
| --- | --- |
| Windows 실행 환경 | 현재 PC·VM·CI가 없다는 사용자의 확인에 따라 예상안만 기록한다. 실제 Windows 환경에서 검증할 항목을 유지하며 Mac 검사로 대체하지 않는다. |
| Windows 전용 지원 조건 | 최소 Windows 버전·WebView2 준비, 창 닫기와 완전 종료, 저장·복구의 컴퓨터 동일성 및 권한 계약을 Feature 승인 전에 확정한다. Notes·Spotlight PDF는 그대로 이식된다고 약속하지 않는다. |
| Docs 언어 선택 유지 | 초기에는 유지 범위가 제안이었으며, 현재는 선택 없는 진입은 한국어·명시적 선택은 Docs URL에 유지하는 계약으로 구현됐다. 같은 주제 전환·가이드 이동·뒤로 가기를 보존하고, 별도 앱 전체 언어 설정은 추가하지 않는다. [현재 읽기 계약](../../policies/project/app-documentation.md#language-contract)이 상세 동작을 소유한다. |
| 전달 단계 | 현재 선택은 사용자별 Git checkout + 에이전트 로컬 빌드·설치다. ad-hoc 테스트 파일 전달과 서명·공증한 일반 다운로드 배포는 후속/대안 경로다. 유료 가입을 지금의 설치 선행 조건으로 삼지 않으며 로컬 빌드 성공으로 후속 공개 배포까지 완료 처리하지 않는다. |
| 출시 식별 | 소스 commit·dirty 상태·빌드 입력 지문과 시각은 `BUILD-INFO.md`에 기록하도록 구현했다. 다음 공개 버전 번호·지원 OS 조합은 아직 정해야 한다. 모든 산출물의 버전과 체크섬은 실제 전달 파일과 일치해야 하며 [빌드/표시 계약](../../policies/project/desktop-app-and-settings.md#app-information-and-version)을 따른다. |

## Constraints

- 로컬 우선·명시적 소스 등록·원본 읽기 전용·기존 자료 보존을 유지한다. 공유 ZIP에는
  프로그램과 공개 의존성만 포함하고 DB·개인 설정·세션·문서·로그·자격 증명은 넣지 않는다.
- 빌드 환경과 앱 상태의 저장 경계를 구분한다. checkout의 가상 환경·Node 의존성·Cargo
  target·배포 출력은 빌드 자료이며, 개인 DB·설정·인덱스와 공유 가중치를 그 안에 넣지 않는다.
  빌드 도구/캐시 공간은 앱의 Settings 저장공간 수치와 별도로 필요할 수 있다.
- 한국어·영어는 같은 동작을 설명한다. 기본값, 수집·검색 범위와 제외 조건, 준비·실패·재시도,
  비용 추정의 한계, 백업 제외 항목, 동일 설치·동일 컴퓨터·일치 스키마의 복원 자격,
  교체 확인·재시작·실패 복구와 원본/모델 보존 조건을 약화하지 않는다.
- Docs는 고정 등록 경로·공통 Markdown renderer·오프라인 패키지 제공을 유지한다.
  임의 파일 경로나 개발용 API 문서를 사용자 가이드로 열어 주지 않는다.
- macOS 공개 배포는 기존 계약대로 기본 보안 설정에서 실행되어야 한다. 앱별 실행 예외나
  보안 우회를 일반 설치 절차로 요구하지 않는다. 내부 미공증 테스트본의 한계는 명시한다.
- Windows 작업은 기존 macOS 잠금·원자적 저장·복구·프로세스 종료 보장을 보존해야 한다.
  설치 파일이 생성되었다는 사실만으로 해당 보장을 확인했다고 판정하지 않는다.
- 일반적인 Windows 경로는 앱이 임의로 자료를 생성하거나 자동 수집할 권한이 아니다.
  Native Windows와 WSL의 Home·세션·모델 캐시를 혼동하지 않으며, 사용자 지정 경로와
  환경변수의 실제 해석을 표시한다. Mac의 기존 저장 위치를 Windows 준비 때문에 옮기지 않는다.
- 저장공간은 사용자의 실제 값을 읽는다. 예시 수치를 고정하거나 읽기 실패를 0으로
  표시하지 않는다. 공유 Hub 캐시 전체 크기를 LocalBrain 단독 사용량이라고 부르지 않는다.
  남은 공간은 해당 저장 위치의 볼륨 기준으로 설명하고 공유 가중치는 앱 캐시 정리로 지우지 않는다.

## Acceptance Envelope

- 포함 플랫폼·핵심 기능·선택 기능이 확정되고, 화면·Docs·설치 안내가 실제 전달물과 일치한다.
- 새 사용자와 기존 사용자의 대표 경로에서 미제공 기능으로 가는 진입점이 없으며,
  해당 직접 경로의 접근 제한과 기존 기록 보존은 유지된다.
- 여섯 Docs 모두 한국어 최초 표시·동일 주제 영어 전환·내부 링크·뒤로 가기·오프라인
  읽기가 동작한다. 두 언어의 필요한 정보와 조건이 같고, 넓은/좁은 화면과 키보드로 읽을 수 있다.
- 지원되는 환경에서 사용자가 checkout과 에이전트로 도구 준비·빌드·설치·앱 실행을
  재현할 수 있다. 소스 revision/dirty 상태와 성공/실패·미확인 항목을 확인할 수 있다.
- 빌드·설치를 마친 앱에서는 모델·별도 개발 도구 실행·checkout·수동 개발 서버 없이
  연결·동기화·대화 열기·키워드 검색을 할 수 있다.
  선택형 모델 작업은 사용자 동작을 필요로 하며 Docs 읽기나 설정 탐색으로 시작되지 않는다.
- 제공하는 각 플랫폼에서 설치·첫 실행·파일/폴더 선택·완전 종료·재실행·수동 교체 후
  기록/설정 보존을 확인한다. 백업·복구와 선택형 AI는 그 플랫폼에서 제공하는 범위만큼 검증한다.
- 빌드와 전달 파일의 버전·출처·시각·아키텍처·체크섬을 대조할 수 있다. 소스 테스트,
  패키징 성공, 네이티브 실행, 수신자 실행과 공개 서명/공증 검증은 각각 구분해 기록한다.
  현재 경로의 사용자 검증은 그 사용자 PC에서 clone/pull 후 빌드·설치·실행한 결과다.
  사전 빌드 ZIP을 내려받은 수신자 검증은 해당 전달 경로를 사용할 때 별도로 필요하다.
- Native Windows·WSL 원본 위치, 사용자 지정 Home, 비 ASCII/공백/드라이브 경로,
  Local Context 등록, 모델 다운로드/캐시 재사용/인덱스 준비, 저장 볼륨과 오류 상태를
  Windows에서 확인한다. 환경이 없을 때는 이 항목들을 명시적으로 미검증으로 남긴다.

## Candidate Features

최초 작성 당시 아래 목록은 승인 전 후보였으며 Feature 문서나 실행 순서를 확정하지
않았다. 이후 C01–C05는 FEAT-0155–0159로 승인·순차 구현·로컬 검증을 마쳤다.
C06의 FEAT-0160은 Windows 실행 환경을 기다리는 draft/예상안이다. 원래 후보의
목표·의존성을 아래에 보존하며, 현행 상태와 승인·검증 한계는 연결된 Feature와
[Mac delivery](../evaluation/eval-0155-early-access-macos-delivery.md)가 소유한다.

| Candidate | Type / likely profile | Proposed outcome and dependency |
| --- | --- | --- |
| C01 · 플랫폼·저장 계약 | foundation / foundation-contract | [FEAT-0155](../feature/feat-0155-platform-paths-and-capabilities.md): 플랫폼별 제공/미제공, 경로·원본·개인 상태·공유 모델의 소유권과 Windows 검증 경계를 정한다. 다른 후보의 선행 계약이다. |
| C02 · 도달 가능한 앱 안내 | product / frontend-product | [FEAT-0156](../feature/feat-0156-available-trial-entry-points.md): 공통 탐색, Sessions List·Chart, 동기화 결과와 복구 안내가 실제 제공 중인 기능으로 연결된다. |
| C03 · 한국어 기본 Docs | product / fullstack-product, docs-content lane | [FEAT-0157](../feature/feat-0157-bilingual-app-docs.md): 고정 가이드/언어 선택·안전한 링크, 여섯 한국어·영어 본문과 기존 shell의 읽기/전환을 함께 제공한다. |
| C04 · 저장공간의 실제 의미 | product / fullstack-product | [FEAT-0158](../feature/feat-0158-platform-storage-accounting.md): 실제 경로·용량·볼륨 여유 공간·읽기 실패와 공유 모델 범위를 구분한다. Mac 회귀를 확인하고 Windows 검증은 환경 확보 뒤 수행한다. |
| C05 · 에이전트 기반 Mac 로컬 설치 | product / infra-devtool | [FEAT-0159](../feature/feat-0159-identifiable-macos-trial-build.md): clone/pull한 사용자가 에이전트로 도구 준비·식별 가능한 빌드·앱 설치/첫 사용·업데이트를 재현한다. 중앙 ZIP 전달과 공개 서명/제출은 선행 조건이 아니다. |
| C06 · Windows x86_64 체험 앱 | product / fullstack-product, infra-devtool lane | [FEAT-0160](../feature/feat-0160-windows-x64-local-ai-trial.md): 선택형 로컬 AI를 포함하고 같은 저장소/에이전트 설치 흐름을 목표로 한다. 현재는 예상안이며 실제 Windows 이식·로컬 빌드·설치·실행 검증은 환경 확보 뒤 수행한다. |

## Continuity Notes

- `2026-11-05`: 현황과 요청을 분리한 초안 작성. 현재 배포 ZIP은 최신 소스와 다른
  파일을 포함한다. 기존 영어 Docs·Mac 테스트 앱의 승인 및 수신자/공개 배포 미검증
  상태를 보존한다. 기능 축소·Windows 포함 단계·언어 선택 유지 방식은 아직 검토 대상이다.
- `2026-11-05`: 사용자가 Mac·Windows 동시 제공과 Windows 선택형 로컬 AI 포함을
  선택하고 Windows 경로·Local Context·모델 설치·저장공간을 추가했다. 뒤이어 Windows
  실행 환경이 없으므로 예상 동작으로 작성하고 실제 환경에서 후속 검증하도록 정정했다.
  플랫폼/검색 범위는 확정했으며 예상 경로와 Feature 경계 검토를 준비한다. Mac 우선
  권고는 현재 선택을 대체하지 않는다. Windows 구현/배포/검증 완료로 상태를 올리지 않는다.
- `2026-11-05`: 사용자가 첫 체험 설치를 Git clone/pull 후 자신의 에이전트에게 로컬
  빌드·설치를 요청하는 과정으로 선택했다. 설치 시 개발 도구가 필요 없다는 최초 가정과
  중앙 사전 빌드 파일 전달을 첫 경로로 두던 내용을 대체한다. 설치 후 native 앱의 독립
  실행·자료 보존, Mac/Windows와 선택형 AI 목표, Windows 예상/후속 실기 검증은 유지한다.
  기존 일반 다운로드 앱의 서명/공증 목표를 완료하거나 폐기한 것은 아니다.
- `2026-11-05`: 사용자의 로컬 재빌드 요청으로 현재 소스의 Mac `0.0.1` 앱/ZIP을
  `08:20:43 UTC`에 다시 만들었다. 빌드/서명/체크섬, 소스 53개 테스트와 동봉 backend·
  격리 WKWebView 기동을 확인했다. [checkpoint](../research/early-access-distribution-readiness.md#local-rebuild-checkpoint--2026-11-05)가 실제 산출물과 요청별 완료/미완료를 소유한다.
  영어 설치 안내는 반영되었으나 한국어/영문 Docs 전환·Sources 잔여 링크·저장공간 UI는
  미구현이며 Windows는 예상/미검증이다. 이 운영 빌드가 draft Feature 승인·완료나
  실제 Tauri/수신자·공개 배포 수용을 뜻하지 않는다.

## Mac Implementation Delivery — 2026-11-05

사용자가 모든 Mac 작업과 숨김 Workflow/Workstreams 내부 의존 정리를 지시했다.
Feature0155–0159의 순차 구현·검증을 마치고 최신 dirty 소스로 앱을 재빌드했다.
[통합 평가](../evaluation/eval-0155-early-access-macos-delivery.md)가 source/browser/frozen/
실제 Tauri 창·종료와 증거 한계를 기록한다. Windows는 예상 경로·동작 안내만 있으며
실제 Windows 검증은 남아 있다. 이 11월 5일 전달 checkpoint에서는 원격 push와
수신자 사용 후기를 수행하지 않았다. 이후 source publication은 별도 세션 closeout이며
수신자 사용·공개 배포 수용의 근거가 되지 않는다.


## Shared Navigation Refinement — 2026-11-06

Owner approved [FEAT-0161](../feature/feat-0161-app-navigation-history.md): common
chronological Back, stable disabled first-entry slot, retained body titles/search,
and localized Docs contents with the shared language option. [Run237](../run/run-20261106-237-app-navigation-history.md)
records source/browser/native evaluation, latest50 including current, async and
onboarding/evicted-entry repairs, canonical-path rebuild and normal relaunch.
This refinement does not expand the approved trial capabilities, global language,
Windows implementation or public distribution authority. At this refinement
checkpoint, source was local and unpushed; later source publication is separate.
Human/recipient and Windows evidence limits remain open.

## Shared Window Toolbar Refinement — 2026-11-06

Owner approved [FEAT-0162](../feature/feat-0162-shared-window-toolbar.md): Sidebar,
Back, Forward and search share the Mac window titlebar; browser use retains the
page toolbar. Body titles and Docs-only language scope remain. [Run238](../run/run-20261106-238-shared-window-toolbar.md)
records modal/shortcut repairs, source/browser/original frozen and synthetic
actual-host evidence, canonical-path rebuild and relaunch. Physical native
drag/window-button interaction remains a human check. Existing recipient,
Windows and public-distribution limits and local/unpushed status are unchanged.

The owner’s subsequent sidebar refinement retains a compact Google-icon menu rail
and moves its toggle beside the brand. Shared hover/focus hints are anchored to
controls with separate keycaps. Run238’s follow-up records the new canonical
build, small-window/IME routing repairs and unchanged native/recipient limits.
