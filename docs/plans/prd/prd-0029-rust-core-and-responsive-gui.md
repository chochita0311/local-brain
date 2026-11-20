# PRD-0029: Rust Core And Responsive GUI

## Metadata

- ID: `prd-0029`
- Status: `approved`
- Owner role: `human`
- Created: `2026-11-12`
- Updated: `2026-11-19`
- Approval scope: human initially approved completing FEAT-0167/0168; their contracts passed Run247/248. The later explicit full-backend/layout approval selects FEAT-0180/Spec0180/Run261 for implementation and delegated verification. Live user-app replacement and publication remain separate.
- Common-settings approval: FEAT-0178 contract-only boundary approved on `2026-11-17`; Run259/Eval0175 passed. User approved implementation FEAT-0179 on `2026-11-18`; Run260/Eval0176 pass the bounded settings increment, with remaining Python/Node, latency and platform/physical limits explicit.
- Final backend target: user clarified on `2026-11-18` that completion means removing Python from the backend; retained Python in passed slices is intermediate. [Runtime exit conditions and approved app layout](../project/python-free-backend-target.md) own the current target.

## Request Summary

LocalBrain의 Python 백엔드를 Rust 중심 실행 구조로 전환하는 제품 경계를 정한다.
2026-11-18 사용자는 완료 목표가 **백엔드에서 Python을 제거하는 것**임을
명시했다. HTTP/CLI·템플릿 실행·TOML/시간대 adapter·선택형 모델 worker에 Python이
남아 있으면 전체 전환은 미완료다. 기존 first-slice의 Python 유지 결정은 과도기
경계로 보존하며 최종 예외로 해석하지 않는다. 개발·검증용 Python 도구와 legacy
비교 fixture는 배포 백엔드 runtime과 구별한다.
사용자는 macOS 앱 터미널과 함께 PRD 작성을 요청했고, 후속 답변으로 두 주제를
함께 검토하도록 확인했다. 이어서 Herdr 등의 UI 기술, 웹·앱 반응성, 전환 시
호환 요소를 질문하며 사람이 보기 좋은 화면도 필요하다고 명시했다.

후속 사용자 확인으로 **일상 사용의 최종 대상은 앱**, 웹은 같은 화면·기능을
개발 중 확인하는 경로로 정리했다. 장기 제품 경계는 앱과 개발용 웹의 기능
동등성이며, 업무 코드를 Tauri와 분리해 공통 Rust 코드로 사용하는 구조는
확인되었다. 웹을 별도의 최종 사용 제품으로 유지할 의무를 추가하지 않는다.
현재 앱에 빠진 기능의 편입 목록·순서와 중단 기능의 복귀는 별도 승인 경계다.

따라서 목표는 언어 변경과 함께 **기존 자료·기능을 이어 쓰며 보기 좋고 빠르게
조작하는 GUI**다. TUI로의 제품 전환을 요구하지 않는다. Rust 코어, 화면 기술,
선택형 모델과 터미널 엔진의 언어는 서로 다른 결정이다. 사용자가 생성한
FEAT-0167/0168의 완료를 명시적으로 승인했고 두 계약 결과가 Run247/248에서
통과했다. 첫 terminal control·host/worker·호환/복귀의 선택은 확정됐으며 실제
포팅·화면/앱 통합·성능 시험·배포 완료와 구별한다.

## Source Set

| 출처 | 사용하는 사실 또는 요구 | 근거 한계 |
| --- | --- | --- |
| `2026-11-18` 완료 목표 정정과 구조 질문 | backend Python 제거가 최종 목표이며 설정 성능 퇴행을 해결해야 함. `apps/api`·`apps/web` 같은 역할 분리를 제안 | 폴더 이전·전체 native backend·성능 개선을 이미 수행한 사실이 아님. 실행 도구/legacy fixture와 backend runtime을 구별하고 UI/VT·자료 계약을 유지 |
| 최초 생성한 Feature들을 끝까지 진행하라는 명시 지시 | FEAT-0167/0168의 권장 경계와 계약 실행을 승인. Run247/248에서 first slice/host/runtime/helper/관리 계약 완료 | 실제 Rust 포팅·화면/앱 통합·사용자 서비스 제어·배포를 수행한 사실은 아니며 후속 product 경계는 별도 |
| 기획 검토 뒤의 사용자 진행 지시 | 합의한 공통 Rust 코어·앱 중심 GUI와 앱 터미널 방향에서 다음 작업으로 진행 | 상위 방향/Feature 기획 승인으로 기록. 새 first-slice/runtime 권장안·개별 Feature 경계·배포를 자동 승인하지 않음 |
| 최초 사용자 요청과 후속 답변 | Rust 전환과 macOS 앱 터미널의 공동 기획, GUI 품질·반응성·호환 검토. 공통 업무 코드의 Tauri 분리 확인, 앱 중심 일상 사용·개발 확인용 웹·장기 기능 동등성. 후속으로 일관된 앱 종료/잠자기 후 terminal 유지와 시스템 종료 시 프로세스 종료를 선택 | 모든 실행 구성요소의 Rust 재작성이나 UI 프레임워크·전송·manager 공유를 선택한 것은 아님. terminal 수명 결정과 표시/숨김 UX 추천은 PRD-0030이 소유 |
| 최초 Python 구현과 당시 `pyproject.toml` | 당시 Python/FastAPI·Jinja2, SQLite/FTS5, 도메인·수집·검색·모델 책임 | 현재 제품 package는 제거됨. 원본 고정 baseline과 Run261 대응표로 추적하며 당시 소스만으로 Rust 동등 구현이나 성능 향상을 입증하지 않음 |
| [현재 Architecture](../../policies/project/architecture.md), [Rust workspace](../../../Cargo.toml) | 현재 Rust/Axum·MiniJinja와 native 저장·수집·검색·모델 책임 | 실제 행동·배포·성능 검증은 Run261에서 별도로 확인 |
| [Tauri manifest](../../../apps/desktop/src-tauri/Cargo.toml), [lock](../../../apps/desktop/src-tauri/Cargo.lock), [config](../../../apps/desktop/src-tauri/tauri.conf.json), [호스트](../../../apps/desktop/src-tauri/src/main.rs), [빌드](../../../scripts/build-desktop.py) | 기존 Rust Tauri의 앱 수명·번들 경계. 당시 동봉 Python 백엔드는 Run261의 native backend로 대체 | 선언된 최소 OS와 실제 검증 환경을 구별해야 함 |
| [Desktop/settings](../../policies/project/desktop-app-and-settings.md), [Storage](../../policies/project/installation-and-storage.md), [Data model](../../policies/project/data-model.md) | 현재 데이터·설정·복구·인증·설치 계약 | 새 스키마나 교차 버전 복원을 승인하지 않음 |
| [Session ingestion](../../policies/project/session-ingestion.md), [Usage](../../policies/project/usage-and-cost.md), [Search](../../policies/project/natural-language-search.md), [Privacy](../../policies/project/privacy-and-data.md) | 원본 보존·수집 의미, 비용 스냅샷, 검색 적격성·모델·외부 전송 경계 | 언어 전환을 이유로 계약을 축소할 수 없음 |
| [Trial capabilities](../../policies/project/trial-capabilities.md), [Availability](../project/feature-availability.md), [PRD-0027](prd-0027-early-access-distribution-and-bilingual-docs.md) | 웹/앱의 서로 다른 제공 범위, 중단 기능, 별도 Windows 전달 경계 | Rust 전환이 기능 재개나 Windows 포팅 완료를 뜻하지 않음 |
| [Design Constitution](../../policies/design/design-constitution.md), [Navigation](../../policies/project/navigation-and-history.md), [Design Evaluation](../../policies/design/design-evaluation.md), [Interaction Evaluation](../../policies/experience/interaction-evaluation.md) | 디자인·키보드·상태·탐색 및 실제 host 검증 기준 | 새 화면 디자인이나 UI 라이브러리 선택의 승인이 아님 |
| [Terminal](../../policies/project/terminal.md), [앱 터미널 PRD-0030](prd-0030-macos-terminal-work-area.md) | Node/headless 화면 상태와 Rust 전환의 경계, 앱 통합 요구 | 터미널 엔진을 Rust로 다시 만들겠다는 요구가 아님 |
| [Herdr 고정 manifest](https://github.com/herdrdev/herdr-app/blob/7fe7ac34fef8a3ee76cb5d2f17bc8d6331e50bd8/Cargo.toml), [UI 안내](https://github.com/herdrdev/herdr-app/blob/7fe7ac34fef8a3ee76cb5d2f17bc8d6331e50bd8/defaults/AGENTS.md) | GPUI 계열 Rust GUI, Ghostty 연동과 JavaScript 패널 구성의 참고 | LocalBrain과 같은 기술·성능을 요구하지 않으며 출시 바이너리와 동일한 빌드라고 가정하지 않음 |
| [Orca 공개 manifest](https://github.com/stablyai/orca/blob/main/package.json) | 2026-11-12 확인한 Electron·React·TypeScript·Tailwind UI의 참고 | 변하는 main 기준이며 앞선 고정 Orca revision 또는 설치 앱의 증거가 아님 |
| [Tauri process model](https://v2.tauri.app/concept/process-model/), [GPUI](https://github.com/zed-industries/zed/blob/main/crates/gpui/README.md) | WebView GUI와 GPU 기반 Rust GUI의 기술적 차이 | 일반 구조 설명이며 LocalBrain에서의 비교 실행은 없음 |

## Product Intent

사용자는 앱이나 웹에서 기존 Session과 문서를 찾고 읽으며 터미널 작업으로 이어
갈 수 있어야 한다. 수집·검색·파일 처리가 진행돼도 입력·스크롤·메뉴 전환이
불필요하게 멈추지 않고, 진행·실패·취소와 현재 자료의 상태가 명확해야 한다.
타이포그래피·정보 계층·긴 글 읽기·탐색·접근성을 성능과 함께 유지한다.

일상 사용과 최종 수락의 중심은 설치 앱이다. 개발용 웹에서도 같은 업무 코드와
화면을 확인할 수 있어야 하며, 장기적으로 웹에서만 가능한 제품 기능을 앱에
빠진 채 남기지 않는다. 웹/앱을 항상 동시에 실행하거나 서로 다른 업무 구현을
유지할 의무는 없다. 과도기의 실제 기능 차이와 미편입 항목은 명시한다.

Rust 전환의 기대 효과는 실행 구성·자원 관리·처리 경로 개선의 **검증 대상**이다.
[Run261/Eval0177](../evaluation/eval-0177-python-free-backend.md)에서 최종 배포본의
네 가지 HTTP 지연을 같은 조건으로 비교했고 모두 개선됐다. 메모리·앱 크기·물리
입력·전체 시작 비용의 전후 개선까지 판정한 것은 아니다. 화면의 JavaScript·레이아웃,
SQL, 디스크 I/O, 모델 추론, 전달량이 병목이면 백엔드 언어 변경만으로 해결되지 않는다.

TUI는 터미널의 글자 칸으로 만드는 조작 화면이고, GUI는 창·글꼴·목록·버튼·이미지
등을 자유롭게 배치하는 화면이다. GUI 안에 terminal을 두고 그 안에서 TUI 프로그램을
실행할 수 있다. Herdr의 데스크톱 GUI와 별도의 terminal/TUI client도 구별해야 한다.
제품 전체를 TUI로 바꾸는 선택과 backend 언어 선택은 연결된 의무가 아니다.

## Current Baseline And Meaning Of The Transition

다음 표의 현재 상태와 제안은 PRD 착수 시점의 baseline이다. 현재 구현·검증 상태는
[Eval0177](../evaluation/eval-0177-python-free-backend.md)과 아키텍처가 소유한다.

| 부분 | 현재 상태 | 전환 경계의 제안 |
| --- | --- | --- |
| macOS 창과 호스트 | 이미 Rust/Tauri. lock 기준 Tauri 2.12.4, CLI 2.12.3. 현재 빌드는 Apple Silicon, 선언 최소 macOS 14 | 호스트를 새로 만드는 대신 Rust 코어와 실행·종료 책임을 연결 |
| HTTP·업무 처리·CLI | Python/FastAPI, 수집·질의·설정·복구·스케줄과 `lb`/`localbrain` | 공통 업무 코어를 Rust가 소유하고 웹·앱·CLI가 같은 규칙을 소비하는 방향 |
| 화면 | Jinja2가 HTML을 만들고 CSS/JavaScript가 표시·상호작용을 담당. 앱도 이 화면을 WebView로 표시 | 기존 GUI·디자인·브라우저 사용을 우선 보존. Jinja2의 템플릿·컨텍스트·필터 역할을 대체할 선택은 OP-02 |
| DB·설정·검색 인덱스 | SQLite/FTS5, private TOML·JSON·캐시, 소유자별 복구와 호환 식별 | 언어와 분리된 현재 계약을 보존. Rust 도입을 이유로 DB 엔진이나 포맷을 함께 바꾸지 않는 안 |
| 선택형 로컬 모델 | Python의 Torch·Transformers·Sentence Transformers와 pinned 모델/토크나이저·인덱스 | 별도 Python worker 유지와 Rust 추론 전환은 OP-03. 키워드 검색에 모델을 필수화하지 않음 |
| 터미널 | Python 제어/bridge·프로세스 검사 + 독립 Node/node-pty·headless xterm + 브라우저 xterm | Rust로 제어 경계를 옮겨도 Node/headless가 자동 제거되지는 않음. 엔진 교체 여부는 OP-04 |

이 표는 PRD 착수 시점의 baseline이며 이후 Terminal/설정의 실제 전환은 각 Run과
[현재 아키텍처](../../policies/project/architecture.md)가 소유한다. 전환 설계를 승인한 표가 아니다. Python 모델을
남기는 선택은 ‘Python 완전 제거’와 다르고, Node 터미널을 남기는 선택은 ‘모든
runtime을 Rust 하나로 통합’과 다르다. 완료 보고도 이 차이를 명시해야 한다.

## Confirmed Scope

- 최종 backend는 Python interpreter/helper/모델 worker 없이 실행·배포한다.
  기존 기능·자료·권한·호환 조건을 보존하며, Python 제거를 기능 삭제로 대신하지 않는다.
  사용자 승인 `apps/api`·`apps/web`·`apps/desktop`과 shared `crates` 구조 및
  [전환 목표](../project/python-free-backend-target.md)는 Run261에서 구현했다.
  실제 디렉터리·native runtime·배포본·검증 결과는 Eval0177이 소유하며, 최초
  제안 단계의 설명과 현재 실행 완료를 구분한다.
- Rust 백엔드 전환과 앱 터미널을 함께 기획하되 각 PRD의 수락·승인을 구별한다.
- **업무 코드는 Tauri에 종속시키지 않고 웹 서버·앱이 공통 Rust 코드로 사용한다.**
  앱은 일상 사용 대상, 웹은 개발 확인 경로이며 장기 기능 동등성을 전달 목표로 둔다.
- 기존 개인 자료·출처·사용자 확정 상태를 유지하는 호환 전환을 요구한다. 재수집·
  데이터 삭제·초기화를 언어 전환의 기본 경로로 삼지 않는다.
- GUI의 가독성과 조작성을 보존하면서 웹·앱 반응성 개선을 검토한다. Rust 또는
  TUI라는 이유만으로 가벼움·사용성·동등성을 통과했다고 판단하지 않는다.
- 승인된 각 전환 범위 밖에서는 현재 웹·앱의 기능 제공 경계와 외부 읽기/실행
  권한을 유지한다. 장기 기능 동등성은 현재의 앱 제외를 이미 해제했다는 뜻이
  아니며, 중단 기능 재개·개인 자료 외부 처리·새 에이전트 자동 실행의 승인이 아니다.
- 변경 대상의 처리 시간과 사용자가 느끼는 화면 지연, 전체 실행 자원 비용을
  분리해 판단하고 실제 배포 앱·브라우저에서 확인할 수 있는 수락 조건을 정한다.
- 앱 종료/잠자기 후 terminal 작업 유지와 시스템 종료 시 프로세스 종료라는 사용자
  선택을 따른다. 독립 manager와 표시/숨김·명시적 종료의 경계는 PRD-0030이 소유한다.
  이 수명 선택 자체가 전체 PRD/Feature/구현 승인이나 잠자기 중 연속 연산 보장을 뜻하지 않는다.

## Proposed Boundary For Human Review

**Tauri와 분리된 공통 Rust 업무 코드**는 사용자 확인 사항이다. 기존 Tauri/WebView
GUI 유지와 필요할 때만 동작하는 선택형 worker는 추천안이다. 개발용 웹은
HTTP/API, 앱은 승인된 host 연결을 통해 같은 업무 규칙을 사용한다.
앱이 HTTP를 유지할지 전용 IPC를 사용할지는 OP-05에서 정하며, Tauri IPC를 쓴다는
이유만으로 더 빠르거나 웹에서도 같은 전송을 사용할 수 있다고 가정하지 않는다.

이 안의 backend 대상은 HTTP/CLI 경계와 설정·수집·저장·조회·검색 조정·서비스 수명이다.
첫 전환의 활성 기능 목록과 제외된 기능의 포팅 시점은 OP-01의 승인 대상이다.
기존 Python 구현 전체를 지웠다는 사실로 완료를 정의하지 않는다.
반대로 backend runtime에 Python을 유지한 채 공통 Rust 모듈을 호출하는 상태도
최종 완료가 아니다. Python 없는 전달·실행과 기존 동작 보존을 모두 확인한다.

### GUI Responsiveness And Compatibility

| 경계 | 맞춰야 하는 관계와 기대 |
| --- | --- |
| 화면 생성 | HTML 구조·템플릿 컨텍스트·필터·URL·정적 자산·안전한 Markdown/수식/도표 렌더링을 보존. Rust 템플릿 또는 API 기반 화면은 별도 선택이며 React/Svelte/Rust UI 재작성은 필수 조건이 아님 |
| 요청/응답 | 필드 이름·ID·형식·정렬·페이지·시간대, null/unknown 의미, 상태 코드·오류·확인/취소·재시도·중복 생성 방지 의미를 기존 소비자와 맞춤. Python의 정수 ID를 JS로 전달할 때 표현 범위도 확인 |
| 오래 걸리는 작업 | 수집·모델·큰 파일/검색이 화면 및 제어 경로를 막지 않음. 진행/취소/실패를 보이고, 취소·이전 요청의 늦은 응답이 새 화면 상태를 덮어쓰지 않음 |
| 화면 갱신 | 영향받은 영역과 표시할 양을 통제. 긴 대화/목록의 전체 DOM·Markdown 반복 처리, polling·재구독, 터미널 flood가 실제 병목인지 측정하고 보존할 검색·선택·스크롤·읽기 문맥 안에서 개선 |
| 웹/앱 전달 | 같은 업무 결과와 frontend 계약, 각 host의 인증·권한·오류 경계를 보존. 터미널 byte 순서·역압·입력권·checkpoint 호환을 전송 최적화 때문에 바꾸지 않음 |
| 시각/입력 | 기존 디자인 토큰·타이포그래피·레이아웃·320px 필수 조작·focus·Back/Forward·설정 초안·Docs 언어를 유지. 터미널의 한글 IME·셀 폭·단축키·클립보드는 앱에서도 별도 검증 |

목록 가상화·worker·전송 배치·GPU 터미널 렌더러는 원인이 확인됐을 때 선택할
수단이지 이번 PRD가 일괄 도입하는 기능이 아니다. 현재 보이지 않는 내용도
찾기·선택·접근성·스크롤 복원에 필요할 수 있으므로 렌더링량 축소만으로 동등성을
판정하지 않는다. Rust/Wasm으로 화면 코드를 작성하더라도 WebView의 DOM을 그리는
방식이면 브라우저 렌더링 비용은 별도로 남는다.

### Data And Behavior To Preserve

| 소유 영역 | 보존할 불변 조건 |
| --- | --- |
| Source·Session | 등록/해제와 삭제 구별, source/Session/event ID·출처·parser revision, 일반/하위/maintenance 구분, 읽기·pin·제목·보존 이력과 `.jsonl.zst`를 포함한 현재 입력 지원 |
| Usage | 원본 사용량·귀속·날짜 경계·null 의미와 immutable 비용 스냅샷. 언어 전환으로 과거 금액을 다시 가격 매기지 않음 |
| 자료/조직 | Document·공유 resource ID·관계·사용자 승인·checkpoint·Suggestion 상태. 미제공 기능의 기존 자료도 보존하며 기능이 다시 활성화된 것으로 취급하지 않음 |
| 검색/모델 | FTS·적격 source/본문·정확 식별자·필터·원문 주소와 누락 의미, 모델 revision/파일 지문·입력/토크나이저·차원·정규화·인덱스 호환. 다른 모델/런타임을 같은 결과라고 가정하지 않음 |
| 저장/설정 | 기존 data/cache/공유 weight 분리와 private 권한, unknown 설정·revision/동시 수정 거부·원자적 저장·파일 잠금·migration/복구 순서. 원본·개인 자료를 저장소나 배포물에 넣지 않음 |
| 실행/인증 | loopback·앱 per-launch 인증·origin·WebSocket의 별도 접근 검사, task 취소·자식 정리·비정상 종료, CLI help/옵션/JSON/stdout/stderr/exit status 및 `lb`/`localbrain` 호환 |

전체 세부 계약은 표의 복제가 아니라 Source Set의 각 canonical owner를 따른다.
기존 Python 경로가 해당 계약을 위반하는 사실을 발견하면 그대로 복제할지 임의로
바꾸지 않고, [회귀 관리](../../policies/project/change-scope-and-regression.md)의
기존 결함·새 의미 변경 구분에 따라 처리한다.

## Excluded Scope

- 승인되지 않은 Feature에서 Spec·실제 포팅·benchmark·기존 사용자 데이터 migration,
  설치 앱 교체·commit/push를 시작하는 일. 첫 계약 단계에서는 두 foundation까지만 완료했다.
  이후 포팅과 앱 통합은 승인된 Feature별로 진행했으며, 현재 완료 범위는
  [전환 계획](../refactoring/refactor-0006-rust-core-transition.md)에 기록한다.
- TUI로 제품을 대체하거나 디자인을 제거하는 일, Rust 전환을 이유로 UI 전면 재작성·
  새 프레임워크·DB·모델·터미널 엔진을 자동 채택하는 일. UI 전면 전환은 OP-02의 별도 경계다.
- 클라우드/다중 사용자·자동 외부 AI·원격 실행·개인 자료 전송 확대, 중단 기능 재개.
- Windows/Intel/Linux 제공을 이 전환의 완료 사실로 주장하는 일. 기존 Windows
  계획은 별도 전달 의무와 미검증 상태를 유지하며 취소되거나 자동 충족되지 않는다.
- 모든 Python/Node 도구·과거 실험·개발 script의 즉시 제거, 완전한 호환이나 성능
  배수를 근거 없이 약속하는 일, 무중단 runtime 교체.

## Uncertainty — Decisions And Recommendations

사용자가 두 Feature의 권장 경계를 승인했고 FEAT-0167/0168 계약이 통과했다.
OP-01~05/08의 **첫 전환 범위**와 runtime/host/호환 선택은 아래 결정 기록과
[공통 코어 계약](../project/rust-core-and-host-contract.md)이 소유한다.
이를 미결정으로 다시 묻지 않는다. 전체 이후 포팅 목록/별도 제품 수락과 native
측정 수치는 해당 product Feature 승인 전에 고정하며, 계약 PASS로 구현을 대체하지 않는다.

아래 표의 **1차 결정**은 통과한 첫 slice의 경계다. 2026-11-18 사용자가 명시한
최종 Python 제거 목표에 따라 OP-02/03/05의 Python host·문법·모델 실행 유지는
과도기 상태로 한정한다. 기존 화면·HTTP/WS·모델 자료의 호환 의무는 유지하되
최종 backend runtime에서 Python 실행을 계속 허용한 것으로 읽지 않는다.

| ID | 선택 / 남은 질문 | 결정·근거 / 최초 검토 |
| --- | --- | --- |
| OP-01 | **1차 결정됨: Terminal control부터 공통 Rust로 전환.** 최초 질문: 앱/개발용 웹의 장기 기능 동등성 안에서 첫 Rust 전달의 기능 집합과 앱 미편입 기능의 편입 순서는? 제외·중단 기능/실험까지 모든 Python 제품 코드의 이식도 포함하는가? | **선택된 계약:** 첫 slice는 terminal 설정 해석/검증·manager 제어·검사·host/CLI/stream. 나머지 admitted 기능의 장기 동등성/후속 포팅과 중단 기능 제외는 유지. **최초 검토 근거:** **공통 제품 기능 목록과 현재 앱의 차이를 명시하고 첫 공통 코어 경계를 잠그는 안**을 권한다. 앱 중심·장기 기능 동등성은 확인됐으며 미결정으로 되돌리지 않는다. 제외 코드·자료는 보존하되 자동 삭제/재개하지 않는다. 저장소 전체 언어 통일은 추가 범위·검증 비용을 별도로 정해야 함 |
| OP-02 | **1차 결정됨: 기존 Tauri/HTML/CSS/JavaScript 유지.** 최초 질문: 기존 GUI를 유지할지, React/Svelte 등으로 재구성할지, Herdr처럼 GPUI 계열 네이티브 GUI까지 전환할지? | **선택된 계약:** 기존 Jinja host와 frontend HTTP/WS를 보존하며 GPUI/React 전면 재작성은 하지 않음. **최초 검토 근거:** **Tauri와 기존 화면/디자인 유지 + 측정된 UI 병목 개선**을 첫안으로 권한다. GPUI는 HTML/CSS·xterm 표시를 그대로 쓰는 전환이 아니며 웹/앱 화면 공유, 문서 렌더링·IME·접근성·디자인 재현을 다시 확보해야 한다. Rust GUI도 보기 좋게 만들 수 있으나 더 빠르다는 비교 근거는 아직 없음 |
| OP-03 | **1차 결정됨: 선택형 Python 모델 유지.** 최초 질문: 선택형 AI 검색의 Python worker를 남길 수 있는가, Python 없는 배포가 필수인가? | **선택된 계약:** 기본 흐름과 모델 실행을 독립 유지. 순수 Rust 추론/모델 교체나 기존 worker 분리 완료를 뜻하지 않음. **최초 검토 근거:** **기존 모델 계약의 worker를 선택형으로 유지**하는 안을 권한다. 모델 없는 기본 흐름은 독립시킨다. 완전 제거가 목적이면 추론/토크나이저·MPS/CPU·순위 품질·인덱스 재사용/재생성·용량을 별도 비교해야 하며 기존 worker가 이미 독립 완료된 것으로 가정하지 않음 |
| OP-04 | **1차 결정됨: Node/headless 유지.** 최초 질문: 터미널의 Node/headless까지 Rust로 바꿔야 하는가? | **선택된 계약:** Rust가 control/helper/host 경계를 맡고 기존 PTY/VT/checkpoint는 유지. **최초 검토 근거:** **첫안은 유지**, Rust는 control/bridge·배포 책임을 담당하도록 권한다. 현재 xterm checkpoint는 pinned private 상태를 포함하므로 PTY만 Rust로 바꾸는 것으로 재연결 동등성이 성립하지 않는다. 엔진 교체는 VT·Unicode·색상 응답·흐름 제어·IME와 총 자원의 독립 검증 경계 |
| OP-05 | **1차 결정됨: GUI HTTP/WS + 내부 로컬 실행 파일.** 최초 질문: 개발용 웹과 앱은 HTTP를 공유할지, 앱만 IPC로 연결할지? | **선택된 계약:** 두 GUI는 같은 Python HTTP adapter를 통해 Rust binary의 control/stream을 사용. Native 관리와 CLI도 같은 binary/core 사용. **최초 검토 근거:** **초기에는 현재 frontend 전송을 우선 보존**하는 안. Tauri와 분리된 공통 업무 코드는 확인됐으며 전송 선택과 별개다. 실제 병목이 전달 경로라면 앱 IPC/stream을 비교하되 업무 규칙을 복제하거나 개발 확인용 웹을 제거하지 않음. 같은 구현 사용과 같은 실행 프로세스 공유를 구별 |
| OP-06 | **순서 결정됨: 계약 후 별도 기반·제품 결과.** 최초 질문: Rust 전환과 앱 터미널의 최초 전달 순서는? | **선택된 계약:** 두 계약은 통과. 접근/그룹/명령상태 foundation과 첫 Rust terminal/실제 앱 product가 후속이며 모든 Python 포팅을 선행시키지 않음. **최초 검토 근거:** **공통 수명·프로토콜 계약을 먼저 잠그고 최종 앱은 선택된 코어로 검증**하는 안. 앱 터미널을 위해 모든 Python 기능 포팅을 강제 선행하지 않되 Python/Rust 두 앱 bridge를 각각 완성하는 중복도 피한다. ‘같이 기획’은 병렬 구현 승인이나 일정 확정이 아님 |
| OP-07 | **우선순위 결정 / native 제품 수치 남음.** 최초 질문: 성공 우선순위는 startup/용량, 평소 메모리·CPU, 검색/수집 시간, UI 체감 중 무엇인가? | **선택된 계약:** GUI 반응성·호환과 전체 비용을 함께 측정. 기존 web gates와 새로운 native total budget을 구별하며 product 승인 전 실제 baseline/수치 고정. **최초 검토 근거:** **GUI 반응성·호환을 필수 조건으로 두고 실제 비용을 함께 측정**하는 안. 현재 코드/실행본·장비·corpus·cold/warm baseline을 고정하고 숫자를 Feature 승인 전에 정한다. Python 제거율이나 API 시간만으로 화면 개선을 판정하지 않음 |
| OP-08 | **1차 결정됨: 기존 schema/format/IDs 유지.** 최초 질문: 구버전과의 DB/설정 호환 및 실패 후 복귀 범위는? | **선택된 계약:** 기존 Python common settings writer와 단일 lock/revision 유지. 영향 terminal의 명시적 stop 후 기록된 호환 버전으로 rollback, arbitrary downgrade/메모리 상태 복원 아님. **최초 검토 근거:** **초기에는 동일 schema/포맷 유지와 전환 전 복구 가능 상태**를 권한다. 새 schema가 필요하면 migration·동시 구버전 기동 거부·백업 적격성과 복귀 조건을 따로 승인한다. 현행 같은 설치/컴퓨터/schema 복원 계약은 임의 버전 downgrade를 보장하지 않음 |

### Technical Confirmations Before Feature Approval

- Rust HTTP/template/SQLite·잠금·파일/Markdown·압축/parser 라이브러리와 버전·라이선스·
  실제 지원 OS를 확인한다. 현재 Rust `rust-version` 선언만으로 새 의존성이 호환된다고 보지 않는다.
- Python의 문자열/정수·Unicode·datetime·JSON·TOML·정규식·SQL·transaction·lock 의미와
  Rust 소비자의 차이, 모델/외부 도구 IPC·오류·취소·프로세스 소유자를 확인한다.
- UI 측정은 요청 대기/처리/전송·parse/DOM·layout/paint를 구별한다. 긴 대화·목록,
  검색·Sync 중 조작, 터미널 0/1/8·4 pane·hidden/flood/reconnect를 포함한 대표 조건에서
  input-to-paint와 route 전환 p50/p95, main-thread 정체, idle 비용과 전체 subtree RSS를 본다.
  backend·WebView/브라우저·manager·shell·선택 모델 비용을 분리하고 공유 메모리를 단순 합산하지 않는다.
- 기존 Python test 수를 Rust 완료 기준으로 복사하지 않는다. 합성 동일 입력에서 정규화·
  DB/설정·API/CLI 결과와 실패·반복 실행을 비교하고 실제 GUI 상태·배포물 동작을 확인할 근거를 정한다.

## Constraints

- 상세 구현 순서·crate 설계·코드 task·평가 결과는 이 PRD가 소유하지 않는다.
  승인 후 Foundation 계약과 Product 결과를 분리해 Feature를 제안한다.
- 표면은 `contract`, `backend`, `data`, `frontend`, `integration`, `infra`, `docs`다.
  사용자 화면/동작이 연결되는 Feature는 **Fullstack Product**, 독립 계약은
  **Foundation Contract**로 선언하고 실제 lane/의존성과 평가 소유자를 확정한다.
- [Design Evaluation](../../policies/design/design-evaluation.md)과 functional/interaction
  검증은 빌드된 앱·브라우저에서 필요한 상태와 host를 대상으로 수행해야 한다.
  화면을 유지하는 전환에도 초기·로딩·실패·회복·focus·history의 동등성이 필요하다.
- 사용자 원본을 수정하거나 허가 없이 재수집·외부 전송하지 않는다. 비교 자료·test는
  합성이며 private corpus/실험 자료는 기존 private 소유자에 둔다.
- 이전 웹 terminal 검증은 Rust 코어 또는 새 앱의 합격 증거가 아니다. 모델 실행을
  유지하면 그 용량/시작 비용도 별도 남으므로 단일 작은 실행 파일을 약속하지 않는다.

## Acceptance Envelope

| ID | 충족해야 하는 결과 |
| --- | --- |
| A-01 | 승인된 전환 대상 목록과 runtime별 언어·소유자가 명확하며, 실제 웹·앱·CLI가 선택된 Rust 코어를 사용한다. Python/Node를 남긴 부분·미포팅 영역을 완료 보고에 구별한다. |
| A-02 | 합성 기존 설치를 이어 열어 IDs·자료·Usage 스냅샷·pin/관계·설정·출처를 보존하고 재실행·반복 Sync가 중복/삭제를 만들지 않는다. 미제공 기능은 자료와 실행 비활성 상태를 함께 보존한다. |
| A-03 | 승인 기능의 정상·empty/unknown·부분 실패·취소·재시도·중복/경합·재시작 결과와 API/CLI의 계약이 기존 소비자 및 owner 요구와 일치한다. 성공 경로만 비교한 것을 전체 동등성으로 보고하지 않는다. |
| A-04 | 기존 디자인과 가독성, 메뉴·Settings·Docs·Back/Forward·focus·스크롤·좁은 화면이 실제 host에서 유지된다. 수집/검색/터미널 출력 중에도 승인된 반응성 수치와 진행/취소 조작을 충족한다. |
| A-05 | 승인 baseline과 동일 장비·입력·build 조건에서 startup/총 자원/작업 시간/UI 지연을 비교한다. 개선·동등·악화를 항목별로 보고하고 합의한 비회귀 조건을 충족한다. 비교 전 ‘Rust라서 빠름’ 판정을 금지한다. |
| A-06 | 기존 schema·설정·파일 잠금·복구 자격과 실패 원자성을 보존한다. 다른 형식을 채택했다면 승인된 호환/거부·복귀 조건을 실제로 확인하고 개인 DB나 원본을 초기화하지 않는다. |
| A-07 | 앱 인증·HTTP/stream/IPC·네이티브 권한·자식 정리와 privacy 경계가 동등하다. 모델 없는 사용, worker 실패/취소, 미사용 터미널의 비기동을 구별해 검증한다. |
| A-08 | 실제 빌드/설치된 앱과 웹/CLI 배포물, 라이선스·자산·버전/지문·업데이트 후 기동을 확인한다. 컴파일이나 소스 tests 통과를 installed-app/다른 기기/Windows·물리 입력 수락으로 확대하지 않는다. |
| A-09 | 앱 터미널은 PRD-0030의 별도 수락을 충족한다. Rust 전환 완료나 그 반대 하나만으로 다른 PRD가 충족됐다고 판정하지 않는다. |
| A-10 | 설치 앱과 개발용 웹이 Tauri에 종속되지 않은 공통 업무 코드를 사용한다. 승인된 공통 기능 목록의 앱/웹 차이·미편입 상태를 명시하고 장기 동등성에서 빠진 기능을 조용히 제외하지 않는다. 웹 개발 확인을 앱의 실제 수락 증거로 대신하지 않는다. |
| A-11 | 최종 backend와 배포물의 Python interpreter/helper/model-worker 의존이0이며, Python 없는 환경에서 앱·웹·CLI의 실제 기능을 검증한다. 일반 요청은 상주 Rust backend에서 공통 업무 함수를 직접 호출한다. 설정 호출의 측정된 성능 퇴행은 해결하고 동일 자료·부하에서 전후 지연을 비교하며, 부분 이전이나 컴파일 성공을 전체 완료로 보고하지 않는다. |

## Candidate Features

인간의 경계 검토를 위한 결과 후보이며 Feature ID/파일·승인·구현 일정이 아니다.
첫 대상 목록과 runtime 선택이 정해지면 한 loop 크기로 다시 나눈다.
C-01은 [FEAT-0167](../feature/feat-0167-rust-core-and-host-contract.md)으로 구체화돼
Run247에서 계약 PASS를 받았다. 아래 나머지 후보는 아직 Feature/실행 승인이 아니며
첫 Rust product도 이 계약을 소비하는 별도 경계가 필요하다.

| 후보 | 성격 / 제안 profile | 결과와 의존성 |
| --- | --- | --- |
| C-01: 공통 실행·호환·복귀 계약 | Foundation / foundation-contract | 웹·앱·CLI의 Rust 코어 대상, format/API·프로세스·worker·버전·복귀 책임이 고정됨. OP-01~05/08 선택이 전제 |
| C-02: 기존 자료를 잇는 저장·수집 계약 | Foundation / foundation-contract | source/revision·IDs·transaction·잠금·재시도·index 호환이 현재 owner와 일치하는 독립 계약. C-01 의존 |
| C-03: Rust 코어를 통한 기존 사용자 흐름 | Product / fullstack-product | 승인 기능을 웹·앱·CLI에서 같은 자료/결과로 이어 사용. C-01/02 및 필요한 모델 계약이 전제이며 승인 목록에 따라 분할 |
| C-04: 선택형 모델 실행 경계 | Foundation / foundation-contract | 유지 또는 교체를 선택한 추론·인덱스/출처·취소·비기동·오류 계약이 고정됨. 모델 변경 자체의 품질 수락을 생략하지 않음 |
| C-05: 기존 GUI의 반응성 보존과 개선 | Product / fullstack-product | 확인된 병목과 합의한 budget 아래에서 읽기·탐색·입력이 계속 사용 가능. UI 재작성 결정과 구별 |
| C-06: 호환 배포·전환·복구 경험 | Product / fullstack-product | 실제 앱/웹/CLI 설치·업데이트와 기존 자료 연결·실패 복귀 결과가 일치. Terminal 앱 통합은 PRD-0030 후보와 중복 소유하지 않음 |

문서·성능·호환/회귀 검증은 각 결과의 전달 조건이다. 확인만을 위한 별도 제품
기능을 만들거나 이 표를 실행 순서로 취급하지 않는다.

## Continuity Notes

- `2026-11-19` 전체 backend 구현·전달 완료: 사용자 승인
  [FEAT-0180/Run261](../run/run-20261118-261-python-free-backend.md)이
  [Eval0177](../evaluation/eval-0177-python-free-backend.md) PASS를 받았다.
  apps/api·web·desktop 및 crates 구조, native host/CLI/codec/저장·수집·검색·모델과
  Python 제품249모듈·PyInstaller/bridge retirement를 완료했다. 실제 Rust 1.90
  412개/실패0, 앱·웹·CLI/Python 차단 환경, 실제 창16·브라우저26·저장 실패6검사와
  서브에이전트 독립 검토가 통과했다. 같은 조건의 최종 HTTP 네 항목 모두 순수
  Python과 중간 전환본보다 빨랐다. 원래 POSIX fsync 동작을 보존해 설정 저장
  퇴행을 해결했으며 검증용 Python·독립 Node는 제품 backend Python과 구별한다.
  전체 strict parity, macOS14 실기기/Windows·물리 입력·장시간/자원·대형 모델 품질과
  별도 Feature177 수락은 남은 증거 한계다. 이 결과가 상위 PRD 전체 수락이나
  설치 앱·사용자 자료·서비스 교체/Git publication을 뜻하지 않는다.

- `2026-11-18` 완료 범위 정정: 사용자는 backend Python 제거가 목표이며 부분
  이전으로 전체 완료를 대신할 수 없다고 명확히 했다. 공통 설정의 측정된 성능
  저하도 해결 대상이다. Python host/codec/model 유지 문구는 첫 slice의 실제
  과도기 상태로 한정한다. [현재 목표와 권장 apps 구조](../project/python-free-backend-target.md)를
  추가했으며, 기존 통과 기록은 부분 결과로 보존한다. 폴더 이동·새 Rust host 및
  성능 개선이 완료됐다는 주장은 하지 않는다.

- `2026-11-18` 공통 설정 구현: 승인된 [FEAT-0179/Run260](../run/run-20261118-260-rust-common-settings-runtime.md)은
  [Eval0176](../evaluation/eval-0176-rust-common-settings-runtime.md) 계약·기능 PASS다.
  Rust가 공통/Terminal 정상 설정 규칙·병합·revision·commit을 소유하고, 독립
  common 실행파일을 source·platform wheel·최종 서명 앱에 전달했다. 실제 앱
  설정 저장·재열기·Quit/재시작까지 확인했다. 문법/OS-zone·기존 Python host와
  Node는 유지한다. 표본 읽기/저장은 기존 Python보다 느리며 최소 compiler/OS,
  물리 입력·장기 검증, 나머지 backend와 Terminal177 별도 수락은 남는다.
  설치 앱/사용자 서비스 교체나 Git publication은 수행하지 않았다.

- `2026-11-17` 공통 설정 계약 실행: 사용자의 후속 “진행”으로 FEAT-0178을 승인하고
  Spec0178/Run259/Eval0175에서 계약 PASS를 받았다. Rust가 known-value 규칙·
  병합·정상 commit을 소유하며, 부모 lock descriptor를 상속하고 Python 문법/
  OS-zone adapter를 명시적으로 유지한다. 독립 common runtime 전달/호환·거부도
  확정했다. 실제 포팅은 새 [FEAT-0179](../feature/feat-0179-rust-common-settings-runtime.md)
  초안으로 분리했으며 아직 승인/코드 변경은 없다. 전체 backend 및 Terminal177
  native 수락은 완료하지 않았다.

- `2026-11-17` Phase3 기획 재개: 사용자가 refactor에 반영된 나머지 Rust 전환을
  계속하도록 요청했다. [기능·consumer inventory](../project/rust-backend-migration-inventory.md)와
  의존 순서를 작성하고 [FEAT-0178 공통 설정 전환 계약](../feature/feat-0178-rust-common-settings-cutover-contract.md)을
  첫 foundation으로 제안했다. 새 Feature는 draft이며 경계 승인은 아직 없다.
  Spec/Run/실제 포팅은 시작하지 않았고, 기존 Terminal Rust 전달과 나머지 Python
  기능군의 이관 의무를 구별한다. 최신 Feature177의 실제 창 검증은 기존 owner에 남는다.

- `2026-11-12` 진행 지시: 합의한 제품 방향과 Feature 기획의 승인으로 반영했다.
  [FEAT-0167](../feature/feat-0167-rust-core-and-host-contract.md)에 첫 terminal control
  slice·GUI/전송 유지·Node/선택형 Python 유지·호환/복귀의 권장 경계를 구체화했다.
  선택 전체나 새 Feature 경계를 자동 승인하지 않았으며 Spec·코드·Run은 시작하지 않았다.

- `2026-11-12`: 사용자 확인으로 Rust 전환과 앱 터미널의 공동 기획을 분리된 PRD로
  작성했다. UI 기술/호환/반응성과 GUI 품질에 대한 후속 질문을 요구에 반영했다.
  Tauri/WebView 유지와 선택형 Python 모델·Node 터미널 존치는 추천안이며 미승인이다.
  기존 정책·기능 제공 상태·runtime을 변경하지 않았고 Feature/Spec/실행 Run을 시작하지 않았다.
- `2026-11-12` 앱 중심 방향 확인: 사용자가 Tauri와 업무 코드 분리에 동의하고,
  장기적으로 앱과 웹의 기능을 같게 하며 일상 사용은 앱, 현재 웹은 개발 확인
  경로라고 설명했다. 이를 확정된 제품 방향으로 추가했다. 독립 웹 제품을 병행
  운영한다는 전제는 두지 않는다. 첫 편입 목록·전송·runtime·Quit/공유 정책과
  전체 PRD 승인은 미결정이며 현재 제공 경계·코드는 변경하지 않았다.
- `2026-11-12` terminal 수명 선택: 사용자가 일관성을 조건으로 앱 종료/잠자기 후
  작업 유지와 시스템 종료 시 프로세스 종료를 선택했다. 앞선 Quit 미결정 상태는
  PRD-0030의 결정 기록으로 대체한다. 생성 순간의 독립 실행과 보이는/숨긴 탭의
  구별, 실제 Quit·sleep/wake 검증 조건은 그 PRD에 반영했다. 라벨은 추천이며
  manager 공유·runtime 전환·전체 구현 승인은 추가하지 않았다.

- `2026-11-12` 두 Feature 완료 지시/계약 전달: 사용자가 권장 경계의 완료를 명시적으로
  승인했다. FEAT-0167/0168, Spec0167/0168, Run247/248와 Eval0163/0164에서 공통 core/host·
  단일 settings writer·wire/stream·runtime payload/helper/수명/관리 계약을 확정했다.
  최초 추천은 위의 선택된 1차 계약으로 전환했다. 실제 Rust crate/포팅·DB/UI/native
  구현·사용자 service·배포는 변경하지 않았고 전체 PRD를 완료로 표시하지 않았다.

- `2026-11-13` 실제 이식/앱 통합 지시: [FEAT0170/Run251](../run/run-20261113-251-rust-terminal-runtime.md)에서 Terminal 제어·설정 검증·payload/IPC/stream·고정 process helper를 Rust로 전환했다. Python은 HTTP/WS/CLI·단일 TOML writer, Node는 PTY/VT를 유지하며 전체 Python 제거는 하지 않았다. [Eval0167](../evaluation/eval-0167-rust-terminal-runtime.md)의 실행 증거와 남은 기능군을 Refactor0006에 반영했다. [Run252/Eval0168](../evaluation/eval-0168-native-terminal-integration.md)의 앱·payload·실제 host 검증은 전달됐지만 Mac 잠금으로 실제 창 조작 수락은 blocked다. 이전 계약 당시 미구현 기록은 당시 사실로 보존하며 전체 PRD는 완료가 아니다.

- `2026-11-13` 공통 조작·native 창 후속 수락: [Run253/Eval0169](../evaluation/eval-0169-terminal-everyday-interactions.md)에서 runtime payload를 유지한 UI 보완과 실제 창10 검증으로 앞선 잠금 경계를 닫았다. Python의 나머지 기능군은 그대로이며 전체 Rust parity나 속도 향상은 주장하지 않는다. Native IME 자동 검사는 통과하지 못했고 물리 입력·플랫폼/수신자/성능 수락은 별도로 남는다.
