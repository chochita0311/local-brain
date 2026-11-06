# Early-Access Distribution Readiness

## Current Position And Record Scope

현재 전달 계약과 최신 로컬 Mac 빌드·검증은
[Early-Access PRD](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md),
[Mac delivery evaluation](../evaluation/eval-0155-early-access-macos-delivery.md)과
[Shared window toolbar Run](../run/run-20261106-238-shared-window-toolbar.md)이 소유한다.
Mac의 숨김 기능 의존성 정리·한국어 기본/영문 Docs·저장공간 구현 뒤, 공통 언어 메뉴와
연속 뒤로/앞으로·제목 표시줄/아이콘 rail·도움말을 추가 검증하고 canonical 경로로 전달했다.
이 문서는 초기 조사·첫 재빌드와 Windows 예상안을 보존하는 근거이며 현재 바이너리의
식별자 목록을 중복 관리하지 않는다. Windows 이식/실행·수신자·물리 입력·실제 OS IME·
직접 reference-app 비교·공개 서명/공증 수용은 각각 검증된 것으로 올리지 않는다.

## Position And Evidence Limit — 2026-11-05

11월 5일 첫 로컬 checkpoint에서 `dist/LocalBrain-apple-silicon.zip`과 그 아래 앱을
**당시 로컬 소스로 재빌드했다**. 버전은 기존과 같은 `0.0.1`이며 그 빌드 시각은
`2026-11-05T08:20:43.577312+00:00`다. 초기 조사에서 확인한 11월 1일 ZIP과 구분한다.
앱은 여전히 Apple Silicon용 ad-hoc 서명·미공증 테스트본이다. Windows 코드는 이식과
실제 대상 환경 검증이 필요하며, 새 Mac 빌드가 그 지원을 추가하지 않는다.

초기 조사는 소스·기존 배포 파일·현재 계약·공식 배포 문서를 대조했다. 후속 로컬 재빌드와
제한된 실행 확인은 아래 checkpoint가 소유하며 수신자 컴퓨터에서 실행한 결과는 아니다.
제공된 팀별·발표 후기는 로그인 후 읽었지만,
비공개 원문·계정·행사 식별정보·수치를 이 문서에 복사하지 않는다. 사용 의향은 설치나
제품 효과가 검증되었다는 뜻이 아니다. 제안 범위와 승인 전 항목은
[Early-Access PRD](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)가 소유한다.

## Local Rebuild Checkpoint — 2026-11-05

사용자가 현재 로컬 앱 재빌드와 요청 항목의 완료 여부 확인을 요청했다. 이 실행은
기존 소스의 패키징/기동 확인이며, draft Feature의 미구현 동작을 추가한 실행이 아니다.

| Delivered artifact | Recorded result |
| --- | --- |
| 앱/ZIP/체크섬 | `dist/LocalBrain-apple-silicon/LocalBrain.app`, `dist/LocalBrain-apple-silicon.zip`, 대응 `.sha256` 갱신. |
| 버전·빌드 | `0.0.1`; UTC `2026-11-05T08:20:43.577312+00:00`, KST 11월 5일 17:20. |
| 소스 | HEAD `52a99d8`에 로컬 문서/설치 안내 변경을 포함한 dirty checkout. 기록한 package/build 입력 해시는 빌드 중 바뀌지 않았고 선택한 동봉 template/JS/guide bytes는 현재 소스와 일치했다. |
| ZIP | `265,157,383` bytes; SHA-256 `a123f0fb6c1baff9ffbc39021c5a8ab015170e957be93f1a790449f7cfb8d20c`. |
| 빌드 검사 | 기존 PyInstaller/Tauri 빌드, deep/strict 코드 서명, builder private-path scan, ZIP 체크섬/동봉 내용 검사 통과. 최종 dist 이동 뒤 서명과 backend 기동도 재확인. |
| 소스 검사 | Docs 6개 + desktop boundary/build/settings 47개, 총 53개 테스트 통과. 개인정보 검사 통과. |
| 동봉 runtime | 개인 자료와 분리한 임시 데이터/캐시, 모델 다운로드/원본 수집 없이 실행. 인증·실제 desktop edition·여섯 Docs·미제공 경로 차단·격리 경로·선택 asset 일치를 확인했다. 정상 종료했다. |
| WebKit 범위 | 동봉 backend를 별도 비영구 WKWebView에서 확인. 완료된 설정 상태로 `tauri://localhost` → 인증 redirect → 앱 shell·설정 열기/닫기, 새 쿠키와 이전 실행 쿠키 교체의 두 경우 통과. 실제 Tauri 창 조작·수신자 실행의 증거는 아니다. |

요청 항목의 **이 초기 빌드 시점 상태**는 다음과 같다. 재빌드 성공을 전체 배포 준비
완료로 해석하지 않는다. 아래 미구현 관찰과 Feature draft는 당시 상태이며, 후속 Mac
구현 결과와 최신 전달은 위의 현재 소유 기록에서 확인한다.

| Requested outcome | Actual state at this build |
| --- | --- |
| Git/에이전트 로컬 설치 안내 | README 요청문, 도구/빌드/설치·기동 확인/업데이트와 저장 경계 가이드는 반영됨. 앱의 영어 Getting Started에도 진입·재빌드 안내가 동봉됨. |
| 앱 Docs 한국어 기본·영문 보기·간결한 재구성 | 미구현. 현재 동봉 Docs는 영어 여섯 가이드이며 언어 전환이 없다. 이번 본문 수정은 설치/업데이트 안내뿐이다. |
| 미제공 기능 진입점 정리 | desktop 메뉴/직접 경로 차단은 기존에 있음. Sessions 관리/Chart 동기화 안내의 `/sources` 링크 두 곳은 아직 미수정. |
| 저장공간 표시 개선 | 미구현. 공유 Hub 전체 합계·데이터 볼륨의 여유 공간·부분 읽기/단위 표시의 기존 동작을 유지함. |
| Windows 일반 경로·모델/문서/저장 위치 안내 | 예상 경로와 제안, Native/WSL 구분 및 후속 실기 검사 항목을 문서화함. 현재 Windows 기본값이 구현되었다는 뜻이 아님. |
| Windows x86_64·선택형 로컬 AI 실행 | 미구현/미검증. 현재 빌더와 Unix 의존성의 이식, 실제 Windows 빌드·설치·실행은 남아 있음. |

소스 빌드의 다른 사용자 재현, 실제 Tauri 창의 첫 사용/교체·사용자 입력, optional AI의
이번 빌드 실제 설치/검색, Windows 및 서명·공증 공개 배포 수용은 이 checkpoint로
통과 처리하지 않는다. 기존 Feature들은 draft 상태를 유지한다.

## Selected Initial Installation — Agent-Assisted Source Build

사용자는 먼저 Git 저장소를 clone/pull한 사람이 자신의 에이전트에게 로컬 빌드·설치를
요청하는 과정을 선택했다. 중앙에서 만든 ZIP/설치 파일을 받는 흐름을 첫 체험의 전제로
삼지 않는다. 사용자별 소스 빌드도 실제 앱이 실행되는지와 어떤 소스에서 만들었는지
확인해야 한다. 설치 시 빌드 도구가 필요한 사람과, 완성된 앱을 실행하는 사람의 조건은
구분한다. 이 선택은 나중의 일반 다운로드 배포 목표를 완료하거나 폐기하지 않는다.

- 첫 진입과 복사 가능한 에이전트 요청문: [README](../../../README.md#install-from-source-with-an-agent).
- 도구 준비·기존 로컬 변경 보존·native 빌드/설치/첫 사용·결과 보고·업데이트:
  [Agent-Assisted Local Build](../../policies/project/installation-and-storage.md#agent-assisted-local-build).
- 현재 실행 가능한 native 빌드 경로는 Apple Silicon macOS다. Windows는 이 방식에서도
  이식·실제 대상 빌드/설치/AI 실행을 확인하기 전까지 예상/미검증으로 남는다.
- 빌드 환경/의존성/출력 공간과 개인 runtime 상태를 구분한다. source pull이나 개발 서버
  재시작이 이미 만들어진 frozen 앱을 바꾸지 않으며, 업데이트는 종료·소스 갱신·재빌드·
  앱 교체 후 기존 자료 확인이다. 공유 모델 다운로드는 빌드와 별도 선택이다.

아래 기존 ZIP 조사는 당시 산출물과 현재 소스의 차이에 대한 근거로 유지한다. 첫 체험을
위해 그 ZIP을 먼저 업로드하거나 유료 가입/Apple 제출을 할 필요가 있다는 뜻은 아니다.

## Initial Artifact And Source Comparison

아래 표는 **재빌드 전 11월 1일 산출물**을 최초 조사한 결과다. 각 빌드의 checkpoint를
구분해 읽는다. 현재 dist와 전달 상태는 문서 상단의 최신 소유 기록을 따른다.

| Check | Observation | Meaning |
| --- | --- | --- |
| 기존 BUILD-INFO | `0.0.1`, `2026-11-01T12:08:29.826422+00:00` | 한국 시각 11월 1일 21:08 빌드다. |
| 조사 시작 소스 | `52a99d8`; 제품 수정 `5514b70`은 11월 5일 | 설정 읽기/준비·초기 화면 상태 수정이 기존 ZIP보다 나중이다. |
| 기능 중단 변경 | `b844ce8`, 11월 1일 22:33 KST | Context Search·Drive의 기본 제공 중단도 빌드 시각 이후다. 현재 소스의 범위로 새 배포물을 확인해야 한다. |
| 실제 파일 비교 | 번들의 `templates/base.html`, `static/settings.js`, `static/app.js`가 현재 파일과 다름 | 날짜 추정 외에도 전달 파일의 차이를 확인했다. |
| 같은 비교 표본 | `templates/sessions.html`, `content/docs/getting-started.md`는 같음 | 비교한 일부 파일이 같다고 전체 배포물이 최신인 것은 아니다. |
| 파일 크기 | ZIP `265,155,858` bytes, 앱 일반 파일 합계 `856,075,864` bytes | 약 253 MiB 다운로드·816 MiB 앱이다. 모델 가중치와 개인 인덱스 공간은 별도다. |
| 출처 식별 | BUILD-INFO에 소스 commit이 없고 버전은 `0.0.1` | 정확한 빌드 commit을 버전/시각만으로 확정할 수 없다. |

앱 소스 수정이나 개발 서버 재시작은 이미 빌드된 앱의 Python backend를 바꾸지 않는다.
새 배포물은 소스·버전·빌드 시각·플랫폼·체크섬으로 구분하고 그 파일로 검증하는 것이
필요하다. 버전 일치의 현행 소유자는 [App Information And Version](../../policies/project/desktop-app-and-settings.md#app-information-and-version)이다.

## Unavailable Routes And Remaining Entry Points

초기 조사 시점의 `app/edition.py`는 데스크톱의 `/sources` 접근을 차단하고
`templates/base.html`은 Sources 메뉴를 숨겼지만, 다음 두 화면 내부 진입점은 남아 있었다.
이후 FEAT-0156에서 두 안내를 Settings로 연결하고 숨김 패키지의 간접 의존성도
정리했다. [현재 제공 경계](../../policies/project/trial-capabilities.md)는 저장 기록 보존과
웹 기능 유지 조건을 함께 소유한다. 아래 표는 당시 관찰과 필요한 교정의 근거다.

| Producer | Remaining destination | Proposed correction |
| --- | --- | --- |
| `templates/sessions.html`, 수집 소스의 관리 링크 | `/sources` | 앱에서 제공 중인 Session Sources 설정으로 연결한다. |
| 같은 템플릿, Chart의 동기화 결과 안내 | `/sources` | 실제 제공하는 동기화 상태/설정 안내로 바꾼다. 성공·부분 실패·전체 실패 상태를 구분한다. |

메뉴 숨김과 직접 경로 제한은 이미 있는 제품 계약이다. 전체 수정 범위는 공통 메뉴뿐 아니라
화면 내부 링크, 최초/갱신 결과, 빈 상태, 오류/복구와 Docs의 연결까지 확인해야 한다.
개발 웹의 Sources와 소스 등록/동기화 기능을 함께 제거할 근거는 없다.
현재 API 경계와 명시적 등록·보존 조건을 유지한다.

패키지 앱은 자체 backend를 시작해 `127.0.0.1`의 가용 포트와 실행별 인증으로 연결한다.
개발용 `http://127.0.0.1:8000`과 앱의 제공 화면은 다르다. 일반 사용자는 개발 서버를
직접 띄우거나 고정 포트를 입력할 필요가 없다.

## Small Useful Trial

선정된 체험은 대화 연결·동기화·찾기·다시 읽기와 모델 없는 키워드 검색을 중심으로 한다.
Mac은 이 로컬 구현을 제공하며, Mac·Windows 모두 선택형 로컬 AI를 포함한다는 목표와
Windows 실제 이식·검증 대기는 구분한다. 현재 포함/제외 화면은
[PRD의 선정 경계](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md#selected-trial-boundary-and-remaining-feature-review)를 따른다.

### Initial Trial Proposal — 2026-11-05

권장하는 중심 과제는 **자기 대화를 연결하고, 과거 답변을 찾아 다시 읽기**다.
현재 앱의 Sessions·Dashboard·Local Contexts·Settings·Docs와 모델 없는 키워드 검색을
이 과제에 맞춰 안내하고, 기존 AI 검색은 명시적으로 선택하는 추가 경험으로 두는 안이다.
화면을 더 없애거나 기존 AI를 제거하는 것은 아직 결정되지 않았다. 후속 선택으로
Mac·Windows 모두 선택형 로컬 AI 검색을 제공하는 목표가 확정되었다.

추가적인 자동화·스킬 분석·도구 간 자동 맥락 연결·조직 공유 기대가 현재 체험판의
제공 기능으로 오인되지 않게 해야 한다. 그런 기대는 별도 후속 제품 판단이지 기존
중단 기능을 다시 활성화할 권한이 아니다. 성능과 유용성은 수신자의 첫 사용에서 확인한다.

## Bilingual In-App Docs

초기 조사에서는 `app/docs.py`, `content/docs/`, `templates/app-docs.html`이 영어 6개
가이드만 제공했다. 현재는 같은 여섯 주제의 한국어 기본·영문 본문을 함께 동봉하며
Docs 목차의 공통 언어 메뉴로 같은 주제를 전환한다.
대상은 `/help`의 시작하기와 설정·Sessions Dashboard·Sessions·Local Contexts·검색이다.
FastAPI의 `/docs`나 저장소의 정책/계획 문서를 번역 대상으로 포함하지 않는다.

요청된 한국어 최초 기본값과 같은 가이드의 영어 보기는 구현되었다. 이후 내용 수정도
짧은 도입, 실행 순서, 설정/한계 표와 필요한 링크를 사용하되 다음을 보존해야 한다.

- 실제 UI 이름, 기본값, 적용 시점, 명시적 등록/동기화/모델 작업의 차이.
- 검색 대상·제외 조건, 자동 준비와 수동 재시도, 설치/인덱스/사용 가능 상태의 차이.
- 알려지지 않은 사용량/비용과 추정의 한계, 원본·소스·가져온 기록의 서로 다른 보존 조건.
- 백업 포함/제외 항목, 동일 설치·동일 컴퓨터·일치 스키마의 복원 자격,
  교체 확인과 재시작, 실패 복구와 원본/가중치 보존.

초기에는 선택 언어의 가이드 이동·뒤로 가기·새 실행에서의 유지 범위를 정해야 했다.
현재는 Docs URL에 선택을 유지하고 선택 없는 진입은 한국어로 여는 계약이며,
별도 저장 설정이나 앱 전체 언어 전환은 만들지 않는다.
공통 renderer, 안전한 고정 경로, 오프라인 패키징과 기존 읽기 UI를 유지한다.
현행 내용 소유권은 [In-App Documentation](../../policies/project/app-documentation.md)에 남는다.

## Windows x86_64 Feasibility

Tauri는 Windows 설치물을 만들 수 있다. 다만 이 앱의 현재 문제는 설치물 형식 이전의
실행 의존성이다. 아래는 소스에서 확인한 이식 경계이며 Windows에서 실행해 확인한 결과는 아니다.

| Boundary | Current evidence | Necessary product decision or preservation |
| --- | --- | --- |
| 빌드 | `scripts/build-desktop.py`가 Darwin·arm64·Python 3.11만 허용; Tauri target과 PyInstaller spec도 arm64 | Windows x64 Python backend와 `x86_64-pc-windows-msvc` 앱을 실제 Windows 환경에서 준비·검증한다. |
| 잠금/프로세스 | `foundation/operations.py`, `app/storage/recovery.py`, `natural_search/index.py`, `models/installation.py` 등의 무조건 `fcntl` import | Windows에서도 동시 수집·설정 저장·복구·모델 작업의 배제와 종료 보장을 유지해야 한다. |
| 개인 저장 | `os.getuid`, `os.fchmod`, Unix 소유/권한 검사, `~/Library/...` 기본 경로 | Windows 사용자별 저장 경로·접근 권한·원자적 저장과 복구 계약이 필요하다. |
| 네이티브 shell | 확장자 없는 backend 경로, Mac 중심 메뉴·숨김·재열기 | `.exe` 실행, 창/앱 종료, 재실행과 파일 선택을 Windows에서 검증해야 한다. |
| 문서/플랫폼 | Apple Notes는 `osascript`, PDF 본문은 `mdls`; 시간대 기본값도 Mac 기준 | 이식되지 않은 Notes·Spotlight PDF 조작과 안내를 숨기고 시간대/경로 의미를 보장한다. 새 PDF 엔진은 별도 범위다. |
| 선택형 AI | 현재 spec은 모델 실행 라이브러리를 동봉; 공개 가중치는 별도 다운로드 | 후속 사용자 선택으로 Windows도 선택형 로컬 AI를 포함한다. 실제 Windows 모델 호환·설치 크기·성능은 미검증이다. |

Windows 파일만 생성하는 설정 추가를 지원 완료로 취급하면 안 된다.
[PyInstaller 공식 설명](https://pyinstaller.org/en/stable/operating-mode.html)은 backend를
대상 OS·Python·아키텍처에서 묶도록 설명한다.
[Tauri 공식 Windows 안내](https://v2.tauri.app/distribute/windows-installer/)는 MSI의
Windows 빌드와 NSIS 교차 빌드의 제약을 구분하며, VM/CI 등의 Windows 환경을 우선한다.
따라서 Windows x64 runner/VM에서 backend와 앱을 함께 만드는 경로를 권장한다.
현재 저장소에는 이 경로로 만든 설치물이나 수신자 실행 증거가 없다.

## Windows Expected Paths And Storage — Not Implemented Or Verified

사용자는 Mac·Windows 동시 제공과 Windows의 선택형 로컬 AI 검색을 선택했다.
이어 현재 Windows 실행 환경이 없으므로 **예상 동작으로 작성하고 실제 Windows에서
후속 검증**하도록 정정했다. 아래 Windows LocalBrain 경로는 구현 전 제안이며,
기존 앱이 이미 이 위치를 사용한다는 뜻이 아니다. 세션/Hub의 일반 경로는 공식 자료와
현재 수집·모델 코드로 확인했지만 실제 사용자 PC의 위치는 등록/환경 설정에 따라 다르다.

| Purpose | Current macOS default | Expected native Windows default / proposal |
| --- | --- | --- |
| 앱 데이터·설정 | `~/Library/Application Support/LocalBrain` | 제안: `%LOCALAPPDATA%\LocalBrain\Data` |
| 앱 개인 캐시·검색 인덱스 | `~/Library/Caches/LocalBrain`; 검색은 그 아래 `natural-search` | 제안: `%LOCALAPPDATA%\LocalBrain\Cache`; 검색은 그 아래 `natural-search` |
| 공유 공개 모델 가중치 | `~/.cache/huggingface/hub` | 기본 환경에서 예상: `%USERPROFILE%\.cache\huggingface\hub` |
| 앱의 모델 등록 메타데이터 | 데이터 아래 `models/qwen3-embedding-0-6b`; 기존 설치는 허용된 legacy 위치 유지 | 제안: 데이터 아래 `models\qwen3-embedding-0-6b`; 가중치 자체와 구분 |
| Codex 세션 원본 | 기본 Home의 `~/.codex/sessions` | 기본 Home의 `%USERPROFILE%\.codex\sessions` 예상; 별도 Home이면 `<CODEX_HOME>\sessions` |
| Claude Code 세션 원본 | 기본 Home의 `~/.claude/projects` | 기본 Home의 `%USERPROFILE%\.claude\projects`; `CLAUDE_CONFIG_DIR` 설정 시 그 아래 `projects` |
| Local Context 원본 | 사용자가 등록한 폴더·파일 | 사용자가 등록한 실제 폴더·파일. Documents를 반드시 선택하거나 원본을 AppData로 복사하는 규칙은 없다. |
| 앱 프로그램·AI 실행 라이브러리 | 내려받아 둔 `.app` 내부 | 향후 설치 경로의 프로그램/backend 내부. 모델 가중치·개인 인덱스와 별도이며 설치 크기는 미측정이다. |

`%LOCALAPPDATA%`는 보통 `%USERPROFILE%\AppData\Local`이며 사용자별 Local 폴더라는
점은 [Microsoft Known Folder 정의](https://learn.microsoft.com/en-us/windows/win32/shell/knownfolderid)로 확인했다.
그 아래 `LocalBrain\Data`와 `LocalBrain\Cache`는 LocalBrain이 선택할 **제안값**이다.
문자열 예시를 그대로 저장하지 않고 실제 사용자/OS 위치를 해석해야 한다. 데이터와 캐시는
분리하되 기존 Mac 위치와 사용자 지정 `LOCALBRAIN_DATA_DIR`·`LOCALBRAIN_CACHE_DIR`을 보존한다.

Codex의 [rollout 소유자](https://github.com/openai/codex/blob/main/codex-rs/rollout/src/lib.rs)와
[설정 소유자](https://github.com/openai/codex/blob/main/codex-rs/core/src/config/mod.rs),
Claude의 [Windows Home·transcript 설명](https://code.claude.com/docs/en/claude-directory)을
기준으로 세션 원본과 Home을 구분한다. 현재 LocalBrain 후보 탐지는 기본 Home만 확인하며,
사용자 지정 Home·세션 폴더는 명시적으로 등록한다. 후보 탐지로 수집을 시작하지 않는다.

모델 캐시는 프로젝트가 사용하는
[huggingface_hub v0.36.0 상수](https://github.com/huggingface/huggingface_hub/blob/v0.36.0/src/huggingface_hub/constants.py)를
기준으로 한다. `HF_HUB_CACHE`, `HF_HOME`, 기존 `HUGGINGFACE_HUB_CACHE`와 `XDG_CACHE_HOME`을
포함한 실제 설정을 해석한다. 앱 화면에는 해석한 실제 경로를 보여 주고 기본 예시로 덮어쓰지
않는다. 실행 라이브러리는 프로그램, 공개 가중치는 Hub, 모델 등록은 데이터, 개인 임베딩
인덱스는 앱 캐시에 속한다. 선택 모델은 Qwen3-Embedding-0.6B이며 가중치 약 1.21 GB 외에
실행 라이브러리·다운로드 임시 작업·인덱스 공간이 더 필요하다. Windows 총 설치 크기는 미검증이다.

### Native Windows And WSL

WSL에서 실행한 Codex/Claude의 `~`는 Linux Home이다. Windows Home의 `.codex`·`.claude`와
같은 위치로 취급하지 않는다. Windows에서의 예상 원본 접근 예시는
`\\wsl.localhost\<distro>\home\<linux-user>\.codex\sessions`와 그에 대응하는
`.claude\projects`다. Linux 내부의 모델 캐시도 기본적으로 별도다.
[Microsoft WSL interop 안내](https://learn.microsoft.com/en-us/windows/dev-environment/wsl-interop)는
이 UNC 접근 방식을 설명하지만, LocalBrain의 WSL 수집·동기화·파일 선택·성능까지 입증하지는
않는다. 배포판 접근 상태와 사용자 권한을 실제 환경에서 확인하고, 이를 자동 등록하거나
WSL의 원본/모델을 임의 이동·복제하지 않는다. Windows 앱의 DB와 private 캐시를 WSL
원본 폴더에 두는 제안도 아니다.

### Storage Meaning And Current Gaps

현재 `/api/settings/storage`는 데이터·개인 캐시·공유 Hub root의 일반 파일 크기를 각각
합산한다. 공유 Hub root는 다른 프로그램과 다른 모델도 포함할 수 있어 해당 수치를
LocalBrain의 단독 모델 사용량이라고 해석하면 안 된다. 앱 캐시 정리는 기존 계약대로
앱이 소유하는 재생성 가능 캐시만 다루고 공유 가중치·원본·DB/설정을 지우지 않는다.

Mac의 FEAT-0158은 읽기 실패·부분 측정·없는 위치를 구분하고 GiB 표시와 위치별 볼륨의
여유 공간을 제공하도록 아래 초기 미비점을 교정했다. 논리적 일반 파일 바이트와 실제
할당량은 다르며, 공유 Hub 전체를 앱 단독 사용량으로 부르거나 앱 캐시 정리로 공유
가중치를 지우지 않는다. 실제 설정 경로·측정 상태는
[현재 저장 계약](../../policies/project/installation-and-storage.md)이 소유한다.
Windows 경로·권한·볼륨·표시·복구의 실제 검증은 계속 후속 항목이다.

#### Initial Storage Gaps — 2026-11-05

아래는 초기 구현에서 확인한 후속 항목과 교정 요구다. 당시 함수·수치·실패 의미의
관찰을 보존하며 현재 Mac 구현의 미비점으로 다시 해석하지 않는다:

- `_size`는 읽기 실패 파일을 건너뛰고, 없는 root/심볼릭 링크 root를 0으로 처리한다.
  표시된 크기가 완전한 측정인지 구분할 정보가 없다. 예상안은 정상 빈 위치와
  읽기 불가/부분 측정을 구분하고 실패를 0으로 표시하지 않는 것이다.
- 여유 공간은 현재 `shutil.disk_usage(data_dir).free` 하나다. 모델 캐시가 다른 드라이브에
  있으면 모델 다운로드의 여유 공간을 설명하지 못한다. 각 위치의 볼륨을 확인하고
  같은 볼륨의 여유 공간을 중복 합산하지 않는 안내가 필요하다.
- 현재 표시는 `1024 ** 3`으로 나눈 값에 `GB`를 붙인다. 계산 단위와 표기를 일치시켜야
  한다. 파일 바이트 합계와 파일 시스템의 실제 할당량도 같은 수치라고 약속하지 않는다.
- 사용자 홈 약식 표시는 현재 `/` 경계만 처리한다. Windows의 구분자·드라이브·공백·한글·UNC
  경로에서도 실제 경로와 식별을 바꾸지 않고 읽기 좋은 표시를 해야 한다.
- 설치 파일/프로그램 용량, DB·설정, 앱 캐시, 공유 가중치와 별도 다운로드·인덱스 임시 공간을
  구분한다. 앱 삭제/교체만으로 외부 데이터나 공유 모델이 함께 삭제된다고 안내하지 않는다.

사용자가 제시한 용량은 그 사용자 Mac의 예시 상태다. 고정 숫자나 Windows 예상 용량으로
복사하지 않는다. Docs는 저장 위치와 관리 결과를 설명하고 실제 경로·크기·여유 공간은
해당 PC의 Settings에서 확인하게 한다.

### Windows Validation Still Required

현재는 아래 항목의 예상 동작과 검증 경계만 정리했다. Windows 통과 결과는 없다.

| Check later on Windows | Evidence required before claiming support |
| --- | --- |
| 경로·원본 등록 | Native/WSL, 기본/사용자 지정 Home, 한글·공백·다른 드라이브·UNC, 선택한 Local Context만 읽기, 원본 보존. |
| 설치·수명 | Python 없는 PC에서 설치·WebView2·첫 실행·파일 선택·완전 종료·재실행과 backend 종료. |
| 선택형 로컬 AI | 명시적 모델 다운로드·검증·등록·캐시 재사용·인덱싱·검색·취소·재시도, CPU 실행과 실제 메모리/시간/설치 크기. |
| 저장공간 | 실제 세 위치·다른 드라이브의 여유 공간·없는 위치·권한 실패·부분 측정·공유 캐시 범위·안전한 앱 캐시 정리. |
| 쓰기/복구 보존 | 설정 충돌, 동시 프로세스, 잠금, 원자적 저장, 같은 설치/컴퓨터/스키마 복원과 실패 롤백, 앱 교체 뒤 기록/설정 보존. |

## Downloaded Mac Apps And Apple Registration

Rectangle의 [공식 배포 사이트](https://rectangleapp.com/)는 설치할 macOS 앱을 제공한다.
앱 프로그램이 사용자의 컴퓨터에서 실행되므로 수신자의 개발 환경이나 서버 실행이 필요하지
않다. LocalBrain도 Tauri shell과 동봉 Python backend로 같은 사용자 경험을 제공할 수 있다.

개발자의 Apple 등록은 배포물의 개발자 신원 서명과 공증에 관한 것이다. 다운로드한 각
사용자에게 개발자 계정이나 기기별 개발 등록을 요구하는 절차가 아니다.
[Apple Developer ID 안내](https://developer.apple.com/developer-id/)에 따라 Developer ID로
서명하고 Apple 공증 및 티켓 첨부를 준비할 수 있다. App Store 입점과는 다른 경로다.
[Program 가격](https://developer.apple.com/programs/whats-included/)은 연 99 USD 또는
제공되는 현지 통화 금액이다. 프로그램에 가입하지 않아도 로컬 개발·테스트 파일 준비는
계속할 수 있지만, 현재 ad-hoc ZIP을 서명/공증 완료 공개 배포본으로 부를 수는 없다.

일반 macOS 배포의 현행 수용 기준은
[Public Distribution Goal](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md#public-distribution-goal--2026-10-20)이다.
실제 가입·결제·자격 증명 사용·Apple 업로드·외부 전달을 이번 조사에서 수행하지 않았다.

## Review Boundary

사용자는 Mac·Windows 동시 제공, Windows의 선택형 로컬 AI 포함을 선택했다. 현재
Windows 환경이 없어 예상 경로·동작과 후속 검증을 구분하는 것이 이 단계의 경계다.
첫 설치 경로는 Git clone/pull 후 에이전트에게 로컬 빌드·설치를 요청하는 것으로 정정되었다.
중앙 ZIP 전달이나 유료 서명/공증을 지금의 설치 선행 조건으로 삼지 않는다.
Mac 우선이라는 최초 권고를 현재 선택으로 남기지 않는다. Mac의 도달 불가 진입점,
한국어/영어 Docs와 저장공간은 FEAT-0155–0159로 검토·승인·구현했고 로컬 전달을
검증했다. 새 빌드와 후속 탐색/툴바 검증은 현재 Run 기록을 따른다. Windows 구현/준비와
실제 설치·AI 실행 검증은 각각 별도로 상태를 기록한다.

초기 조사에서 남았던 Mac Feature 경계는 후속 승인·실행으로 정해졌다. Windows
FEAT-0160과 세부 플랫폼 계약·실제 환경 검증은 여전히 후속 검토 대상이다.
소스 검증·빌드 성공·네이티브 실행·체험자의 자기 PC에서의 소스 빌드/설치·공개 서명/공증은
각각 다른 증거다. 사전 빌드 파일을 전달할 때는 다운로드 수신자 검증도 별도로 필요하며,
어느 하나의 성공으로 나머지를 완료 처리하지 않는다.

## Mac Implementation Delivery — 2026-11-05

이 절은 초기 점검·첫 로컬 재빌드 뒤에 수행한 **11월 5일 Mac 구현 전달 결과**다.
그 뒤의 공통 언어 메뉴·내비게이션·툴바와 현재 canonical 빌드·검증은 문서 상단의
소유 기록을 따른다. 아래 수치와 publication 상태는 이 전달 시점의 역사적 근거다.

| Item | Local result at the Nov5 delivery |
| --- | --- |
| 숨긴 기능 | Desktop에서 Workstreams/Workflow/Auto Work/Atlassian의 assembly·callback·startup work를 제외. 기록은 보존하며 웹은 유지. Sources 진입은 설정으로 연결. |
| Docs | 기존 6개 주제의 한국어 기본·영문 전환, 오프라인 본문·목차·내부 링크·뒤로 가기 구현. |
| 저장공간 | 실제 위치·논리적 파일 크기·GiB·부분/불가·볼륨별 여유 공간과 공유 모델 범위 구현. |
| Mac 빌드 | v0.0.1, 2026-11-05 18:08 KST, dirty HEAD52a99d8, canonical dist 반영. BUILD-INFO에 소스 fingerprint; 검증 전 이전 출력을 지우지 않음. |
| 검증 | [통합 평가](../evaluation/eval-0155-early-access-macos-delivery.md): Python1,534, desktop Chrome69/web70, frozen40+relocated38, isolated WK2 및 실제 Tauri 창/인증/Quit/자식 종료 통과. |
| 남은 경계 | 로컬 미커밋·미push. 수신자 체험, Windows port/실행/AI, 공개 서명·공증은 통과하지 않음. Windows 예상 경로는 위 절 유지. |

이전 실패한 QA 관찰은 macOS 별칭 경로·숫자 포트 검출·스크롤바 폭 가정을 바로잡아
재검증했다. 실제 모델 다운로드나 개인 원본 수집은 수행하지 않았다.
