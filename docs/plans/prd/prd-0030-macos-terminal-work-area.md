# PRD-0030: macOS Terminal Work Area

## Metadata

- ID: `prd-0030`
- Status: `approved`
- Owner role: `human`
- Created: `2026-11-12`
- Updated: `2026-11-12`
- Approval scope: FEAT-0167/0168 contracts passed Run247/248. The latest explicit continuation approves the discussed Terminal rail/groups/tabs/status implementation as FEAT-0169/Run249; native access/bundling and Rust runtime delivery remain separate

## Request Summary

macOS LocalBrain 앱에도 현재 macOS 웹 Terminal과 동등한 작업 영역을 제공한다.
탭·최대 4분할, 기본 작업 폴더/셸, D2Coding 13px, 백그라운드 유지·종료·재연결과
관리 기능을 이어받고, 앱 배포·접근 보호·수명·업데이트 조건을 정한다.

사용자는 [Rust 전환 PRD-0029](prd-0029-rust-core-and-responsive-gui.md)도 함께
검토하도록 확인했다. 두 문서는 연결된 기획이지만 각각 수락한다. 앱 터미널을
추가하기 위해 모든 Python 기능을 먼저 Rust로 이식해야 한다는 의존성은 확정하지
않았다. 초기 요청은 PRD와 open point 의견이었다. 후속 진행 지시로 합의한 제품
방향과 Feature 기획을 승인했고, 이어 생성한 FEAT-0167/0168 완료를 명시적으로
승인했다. 두 foundation 계약은 Run247/248에서 통과했으며 실제 포팅·앱 교체·
새 UI/product 구현의 완료나 자동 승인으로 취급하지 않는다. 이후 사용자가
사이드바 바로 오른쪽의 상하단 영역과 탭을 다시 지목하며 구현을 계속하라고
명시했다. 이 추가 승인으로 [FEAT-0169](../feature/feat-0169-terminal-workspace.md)가
공통 웹 UI의 폴더 그룹·작업 현황·탭·분할과 명시적 shell 상태의 첫 구현을 맡는다.
앱 제공물·접근 보호와 Rust 실행체의 구현/패키지 수락을 이 웹 결과로 대체하지 않는다.

후속 사용자 확인으로 앱은 일상 사용의 최종 대상, 웹은 같은 공통 업무 코드와
기능을 개발 중 확인하는 경로다. 장기 앱/웹 기능 동등성은 PRD-0029가 소유한다.
사용자는 앱 완전 종료 후에도 background terminal을 유지·추적할 수 있는지
질문했고, 후속 답변으로 **앱 종료·잠자기에는 작업 유지, 시스템 종료에는 프로세스
종료**라는 일관된 수명을 선택했다. 앱 Quit은 더 이상 미결정이 아니다. 잠자기는
OS가 보존한 작업을 깨운 뒤 이어 가는 의미이며 그동안 모든 프로그램의 연속 실행을
보장하는 요구는 아니다. 생성·숨김·종료의 표시 방식에 대한 아래 의견은 추천으로 구별한다.

추가 사용자 요청은 Terminal을 **터미널 편의를 위한 전용 작업 공간**으로 구성하는
것이다. 현재 제공한 DOM의 일반 page heading·상시 텍스트 버튼/카드가 차지하는
영역을 줄이고, Herdr의 작업 공간·상단 탭/분할·작업 현황과 iTerm2 같은 상태
기호를 참고한다. 숨긴 터미널의 회수도 유지한다. 다른 Sessions/문서 화면의 일반 앱 UI는 유지한다.
구조·진행/검증은 [Terminal Workspace Design Plan](../design/terminal-workspace-design-plan.md)이
소유한다. 후속 답변으로 **하나의 macOS 앱 창 안에서 여러 탭·탭당 여러 terminal**,
**Workstream/Session과 별개인 폴더별 터미널 작업 그룹**을 선택했다. 기존 최대
4분할은 유지한다. 그룹의 첫 구현과 OSC133 상태 범위는 FEAT-0169의 contract lane에서
고정했으며 OP-08/09는 선택된 범위와 남은 프로그램/native 확장을 구별한다.

## Source Set

| 출처 | 사용하는 사실 또는 요구 | 한계 |
| --- | --- | --- |
| 사이드바 오른쪽의 상하단·탭을 다시 지목한 최신 진행 지시 | FEAT-0169의 실제 전용 frame·폴더 그룹·현황·탭/분할/숨김 회수 구현 승인. contract lane을 먼저 고정하고 웹에서 검증 | native 입장/동봉 실행체·Rust 포팅·물리 macOS 수락을 웹 UI 구현으로 대체하지 않음 |
| 생성한 Feature들을 끝까지 진행하라는 최신 명시 지시 | FEAT-0167/0168 권장 경계를 승인하고 계약 실행/검증 완료. 동봉/lazy-start·scope·안정 helper/payload·관리 선택을 확정 | 계약 PASS이며 현재 native 제외·앱/코드/서비스·실제 OS/물리 입력 수락은 변경하지 않음 |
| 기획 검토 뒤의 사용자 진행 지시 | 합의한 앱 terminal·수명·폴더 그룹/단일 창·전용 작업 영역 방향에서 다음 작업으로 진행 | 상위 방향/Feature 기획 승인으로 기록. 제공물/scope 권장안·개별 Feature 경계·Spec/배포를 자동 승인하지 않음 |
| 현재 사용자 요청과 제공한 앞선 설명 | 앱에도 웹과 동등한 Terminal, 배포 runtime·인증·종료·앱 검증과 open point 기획 | 붙여 넣은 권장안은 모든 제품 선택을 확정한 답변이 아님 |
| 앱 중심 사용에 대한 앞선 사용자 확인/질문 | Tauri와 업무 코드 분리, 일상 사용은 앱·웹은 개발 확인, 장기 기능 동등성. 처음에는 Cmd+Q 후 background terminal의 생존·추적 가능성을 질문 | 당시 Quit 후 유지는 질문이었다. 그 이후 선택은 다음 행이 소유하며 실행 scope 공유·코드 실행 승인은 별개 |
| 일관된 수명과 표시 방식에 대한 최신 사용자 답변 | 앱 종료/잠자기에는 작업 유지, 시스템 종료에는 프로세스 종료를 선택. 기존 background-send와 첫 생성·숨김/종료의 편의성을 질문 | 수명은 확정 방향이다. 새 터미널을 처음부터 숨겨 생성하거나 ×의 의미를 바꾸라는 지시는 아니며 전체 PRD/구현 승인이 아님 |
| Terminal 전용 UI와 상태 기호 요청, 제공 DOM | 일반 page heading/큰 action 행·카드 표현을 줄이고 왼쪽 작업 공간·숨긴 실행 회수·상단 탭·넓은 terminal canvas, 실행/대기/완료·현재 view/최소화를 기호로 읽는 방향 | 원/마름모/체크는 원하는 표현의 예이며 보편 표준이나 정확한 상태 mapping 승인이 아님 |
| 탭/창과 작업 그룹에 대한 사용자 후속 답변 | 별도의 macOS 앱 창 여러 개가 아니라 하나의 창에서 `+`로 탭을 추가하고 각 탭을 분할. 폴더별 터미널 작업 그룹이며 Workstream/수집 Session과 별개 | 창 범위와 그룹 방향은 선택됐다. ID·cwd 상속·membership·삭제/수명·저장 세부 계약이나 전체 PRD/구현 승인은 아님 |
| Herdr 아래쪽 UI/기능 재확인 요청과 공식 [기본 layout](https://github.com/herdrdev/herdr-app/blob/master/defaults/layouts/main.json), [Agents](https://github.com/herdrdev/herdr-app/blob/master/defaults/mods/agents/main.js), [footer](https://github.com/herdrdev/herdr-app/blob/master/defaults/mods/workspace-chrome/main.js), [status](https://github.com/herdrdev/herdr-app/blob/master/defaults/mods/workspace-status/main.js) | 현재 기본 왼쪽은 Spaces 아래 Agents, 별도 footer는 Settings/Add machine, 창 하단 status는 장비·branch·agent/needs-you 수·palette. Agents는 보고된 작업 상태의 모음 | 공개 master 소스 확인이며 설치 앱 실행/같은 버전·layout의 증거가 아님. 아래쪽=숨긴 터미널 목록이라는 앞선 가정을 정정하며 원격/agent 자동화 전체를 범위로 가져오지 않음 |
| [Design Plan](../design/terminal-workspace-design-plan.md), [iTerm2 Appearance](https://iterm2.com/documentation-one-page.html), [Shell Integration](https://iterm2.com/documentation-shell-integration.html), [Session Status](https://iterm2.com/documentation-session-status.html), [Herdr UI](https://github.com/herdrdev/herdr-app/blob/master/defaults/AGENTS.md) | 배치·status source·상태와 view를 나누는 참고, 단계별 design reconciliation | 공개 source를 확인한 planning 근거다. current main·설치 앱·사용자 관찰의 버전/레이아웃을 같다고 가정하지 않고 runtime 비교/사용성 평가로 확대하지 않음 |
| [기존 PRD-0028](prd-0028-web-terminal-work-area.md), [FEAT-0166](../feature/feat-0166-web-terminal-work-area.md), [SPEC-0166](../spec/spec-0166-web-terminal-work-area.md) | 승인된 첫 웹 전달·탭/종료·CLI·화면 계약 | 첫 전달의 웹 전용 근거. 이후 승인된 네이티브 앱 전달은 현재 Terminal 정책과 Run261을 따른다 |
| [Terminal policy](../../policies/project/terminal.md), [Settings 계약](../../policies/project/desktop-app-and-settings.md), [화면](../../../apps/web/static/terminal.js), [폰트 provenance](../../../apps/web/static/vendor/xterm/fonts/provenance.json) | 현재 웹 사양, 입력/화면 상태·상한·자산·설정 책임 | 초기 PRD의 후일 대체된 설계 제안보다 현재 owner/코드가 우선 |
| [최종 Run246](../run/run-20261112-246-terminal-final-audit.md), [Eval0162](../evaluation/eval-0162-terminal-final-audit.md) | 현재 웹 기술 수락과 실제 PTY·브라우저·독립 WebKit/OS 입력·launchd·자원 검증 | `PASS WITH SUGGESTIONS / partial`. 패키지 앱 Terminal·물리 Safari 반복·VoiceOver·장시간/다른 기기의 합격이 아님 |
| [Desktop/settings](../../policies/project/desktop-app-and-settings.md), [Trial capabilities](../../policies/project/trial-capabilities.md), [Availability](../project/feature-availability.md), [PRD-0021](prd-0021-macos-standalone-test-app-and-local-settings.md), [PRD-0027](prd-0027-early-access-distribution-and-bilingual-docs.md) | 앱 창/종료·인증·제공 범위·설정·배포 승인 맥락 | Terminal 하나의 추가가 다른 미제공/중단 기능을 활성화하지 않음 |
| [앱 상태](../../../apps/api/src/state.rs), [HTTP 경계](../../../apps/api/src/boundary.rs), [터미널 연결](../../../apps/api/src/routes/terminal.rs), [runtime](../../../crates/core/src/backend/terminal), [manager](../../../crates/runtime/engine/manager.cjs) | 웹 전용 설치·기동, per-scope identity, HTTP/WS 검사와 독립 manager의 실제 연결 | 웹용 origin 검사만으로 앱 per-launch 인증이 성립하지 않음 |
| [native host](../../../apps/desktop/src-tauri/src/main.rs), [backend host](../../../apps/api/src), [native packaging](../../../scripts/build-api.py), [Tauri config](../../../apps/desktop/src-tauri/tauri.conf.json), [builder](../../../scripts/build-desktop.py) | 창 닫기는 숨김, Quit은 backend 종료. 네이티브 앱의 기능 포함·패키징·수명 경계 | 이전의 Python 동봉과 웹 전용 범위는 [전환 평가](../evaluation/eval-0177-python-free-backend.md)의 역사적 근거 |
| [Storage](../../policies/project/installation-and-storage.md), [Privacy](../../policies/project/privacy-and-data.md), [App Docs](../../policies/project/app-documentation.md), [Terminal guide](../../../apps/web/content/docs/terminal.md) | runtime/캐시·개인 자료·사용자 안내의 소유권 | 자동 transcript·색인·외부 전송이나 새 credential 저장 권한이 아님 |
| [Design Constitution](../../policies/design/design-constitution.md), [Design Evaluation](../../policies/design/design-evaluation.md), [Interaction Evaluation](../../policies/experience/interaction-evaluation.md) | 화면·입력·반응형·실제 host 평가 기준 | native host를 바꾼 상태는 웹 검증만 재사용할 수 없음 |
| [Tauri sidecar](https://v2.tauri.app/develop/sidecar/), [Node sidecar guide](https://v2.tauri.app/learn/sidecar-nodejs/) | 사용자의 Node/Python 별도 설치 없이 runtime을 동봉할 수 있는 일반 전달 방식 | node-pty 네이티브 모듈·spawn helper·서명·수명·오프라인 동작의 완성 증거가 아님 |
| [Apple per-user launchd 안내](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html) | 앱과 별도 수명인 사용자 관리 프로세스의 OS 기반 참고 | archived 일반 안내다. login 자동 등록이나 root daemon 채택이 아니며 실제 앱 Quit·로그아웃·업데이트 검증을 대신하지 않음 |
| [Apple sleep 상태 보존](https://support.apple.com/en-il/guide/mac-help/mh10328/mac), [sleep/wake 안내](https://developer.apple.com/library/archive/qa/qa1340/_index.html) | 잠자기의 상태 보존과 깨우기, 앱 종료와 OS 잠자기의 구별 | 장비/OS별 실행 증거가 아니며 임의 터미널 작업의 잠자기 중 연속 연산·네트워크 연결 보장을 뜻하지 않음 |

공개 문서 확인일은 `2026-11-12`다. 현재 Tauri lock은 2.12.4, CLI는 2.12.3이며
앱 빌드는 Apple Silicon/macOS 최소 14 선언이다. Intel·Rosetta·다른 OS에서의
지원 완료를 이 문서나 기존 웹 결과로 추론하지 않는다.

## Product Intent

앱에서 Session·문서를 읽다가 같은 창 안의 Terminal로 이동해 작업하고, 다른
화면을 본 뒤에도 실행 중인 작업에 돌아온다. 설치한 앱의 첫 터미널 사용에
개발용 Node/npm/Python 설치를 요구하지 않는 전달을 추천한다. 보기 좋은 기존
GUI·문서 읽기·설정·탐색을 보존하며 터미널이나 AI 사용을 다른 기능의 전제로 만들지 않는다.

설치 앱이 주 사용처이므로 앱을 껐다가 다시 열어도 원래 작업으로 돌아오는
경험을 제공한다. 앱 창·일반 업무 backend와 terminal manager의 수명을 분리하고,
사용자가 명시적으로 실행을 종료할 때 해당 범위를 정리한다. OP-02의 사용자
선택이며, 숨기기 버튼을 눌렀는지와 무관하게 모든 생성된 터미널에 적용한다.

Terminal 안에서는 페이지 제목을 읽는 단계보다 탭을 고르고 분할·입력·숨김·복귀·
종료하는 일이 우선이다. 상태를 compact 기호로 읽되 근거와 자세한 뜻은 필요할 때
확인할 수 있어야 한다. 미열람 출력·연결/입력권·명령/프로그램 상태와 선택된 화면을
한 ‘실행 중’ 표시로 합치지 않는다.

## Current Baseline And Planning Boundary

현재 Terminal은 macOS **웹 전용**이다. native assembly는 모든 optional feature를
제외하고, HTTP route allowlist·frozen 지원 검사·PyInstaller code/data 제외도
있다. 따라서 메뉴만 켜는 변경이 아니다. 완료된 foundation 계약도 그 현재 사실을 뒤집지
않으며, 승인한 후속 Feature가 Terminal에 한정해 admission·package·contract를 바꿔야 한다.

현재 웹은 브라우저 xterm 6과 독립 Node 20+/node-pty 1.1·headless xterm 6 관리자를
사용한다. Python은 HTTP/WS·CLI·setup/launchd 제어와 짧은 프로세스 검사를 맡는다.
관리자는 data 경로에서 계산한 scope와 cache 경로로 식별되며 임시 launchd job이
backend보다 오래 살아 있다. 화면·탭 구성은 manager 메모리에 있고 디스크 기록이 아니다.
terminal과 IPC 연결이 모두 없는 manager는 60초 idle 후 종료할 수 있으며 login
agent나 KeepAlive 자동 재기동을 설치하지 않는다. 이 비기동/idle 경계도 유지 대상이다.

앱 호스트는 이미 Rust/Tauri이며, WebView가 동봉 Python backend의 화면을 연다.
창의 빨간 닫기 버튼은 현재 창을 숨기고 앱을 계속 실행한다. Cmd+Q/명시적 Quit과
호스트 손실은 앱 backend를 종료한다. 터미널 manager를 이 수명과 어떻게 연결할지는
OP-02의 독립 수명으로 정했다. 실제 native 통합은 구현 전이며 개발용 웹과의
manager 공유/분리는 OP-03의 남은 결정이다.

## Confirmed Scope

- macOS 앱 안의 내부 Terminal을 웹과 동등한 사양으로 제공하는 새 범위를 기획한다.
  외부 iTerm2 창을 여는 기능이나 과거 세션 attach를 요청한 것이 아니다.
- 기존 메뉴명 **Terminal**, Sessions 위 위치, 탭·pane의 의미, 설정·명시적 생성,
  배경 유지·종료·재연결 동작을 동등성 기준으로 삼는다.
- 기존 웹에서 확인한 D2Coding 기본 13px와 사용자 셸 설정·한글 입력/단축키·
  클립보드·focus 품질을 앱에서도 이어받는다. TUI로 전체 제품을 대체하지 않는다.
- 앱 제공물·인증/연결·종료/교체 및 실제 패키지 앱 검증을 범위에 포함한다.
- Rust 전환과의 공통 계약·검증 대상은 연결하되 별개의 PRD 승인/수락으로 관리한다.
- Tauri와 분리된 공통 업무 코드, 앱 중심 사용·개발 확인용 웹이라는 사용자 방향을
  따른다. 이번 Terminal 전달이 다른 미편입 기능까지 일괄 활성화하는 것은 아니다.
- **창 닫기·일반 앱 종료·잠자기를 이유로 terminal manager와 관리 중 실행을
  종료하지 않는다.** 앱을 다시 열거나 Mac을 깨우면 실제 생존/종료 상태를
  확인하고 같은 대상에 연결한다. 명시적 pane/탭/서비스 종료와 구별한다.
- 시스템 종료/재부팅 후에는 같은 프로세스·메모리 화면을 복원하지 않으며 명령을
  자동 재실행하지 않는다. 잠자기 중 연속 연산·연결 유지나 임의 프로그램 자체의
  종료 방지는 보장하지 않고 실제 결과를 표시한다.
- 하나의 앱 창에서 폴더별 터미널 작업 그룹 → 여러 탭 → 탭당 최대 4 pane을 사용한다.
  그룹은 Workstream·수집 Session과 별개이며 실제 OS 다중 창을 추가하지 않는다.
- Terminal은 왼쪽 작업 공간·상단 탭/분할과 숨긴 실행 회수를 중심으로 사용 가능한
  영역을 작업에 쓴다. 일반 페이지 제목/큰 action 행·상시 관리 설명의 점유를 줄이며
  다른 앱 화면은 바꾸지 않는다. 빈 상태·설치/오류 복구·종료 확인·접근 가능한 이름은 유지한다.
- 기호/색을 사용해 command/process·activity/attention과 view 상태를 구별한다.
  셸 생존·출력 정지만으로 busy/idle/success를 단정하지 않고 실제 신호와 unknown을 보존한다.

### Existing Parity Baseline

아래는 현재 웹 계약을 앱에 이어받을 기준이다. 새 기능 제안으로 다시 열거나
‘웹과 같음’이라는 표현만으로 세부 실패·상한·출처 조건을 생략하지 않는다.
전체 계약은 [Terminal policy](../../policies/project/terminal.md)가 소유한다.
이 동등성은 실행·입력·수명·상한·실패 의미의 기준이다. 위의 새 UI 요청에 따라
일반 페이지 heading/card 배치는 바뀔 수 있으며 기존 화면 모양의 복제가 수락 조건은 아니다.

| 영역 | 앱에서 유지할 동작과 한계 |
| --- | --- |
| 탭/분할·관리 | 여러 탭, 탭당 최대 4 pane. 2개는 좌우/상하, 3/4개는 2×2. 관리 scope당 종료된 화면을 포함해 최대 32 terminal record. 700px 아래는 선택 pane과 전환 제어로 다른 실행을 유지. 선택·이름·overflow·긴 경로와 종료 대상을 구별 |
| 셸/기본값 | Settings → Terminal의 default cwd/shell. 새 터미널은 검증한 기본값으로 즉시 생성, Split은 클릭한 pane의 cwd/shell을 사용. 저장은 기존 실행을 변경하지 않음. 공통 revision/lock/원자적 writer로 unrelated/unknown 설정 보존. 읽기/저장/빈 화면/상태 조회는 설치·manager·셸을 시작하지 않음 |
| 생성/환경 | 기존 사용자 login/interactive shell·startup file/OMZ를 활용하되 rc를 수정하지 않음. 잘못된 명시 경로/셸은 조용히 대체하지 않음. 응답 손실 재시도는 같은 생성 ID와 launch 값을 유지해 중복 셸을 만들지 않음. Finder 실행의 PATH·locale·ZDOTDIR도 별도 확인 |
| 표시/입력 | 로컬 동봉 D2Coding 1.4.0 Regular/Bold·OFL·출처/지문, 13px·ligature 비활성·양쪽 face 준비 후 측정. 설치된 OS 폰트에 기대지 않음. font 실패는 새 rendering을 막고 reload 경로를 제공하되 작업을 종료하지 않음. Unicode 폭·조합·폰트 coverage·encoding을 구별. Shift+Escape로 메뉴 focus, 제어 중인 pane의 셸 키·IME와 현재 composition 취소/commit 규칙 유지 |
| 닫기/배경 | pane ×는 해당 실행, 탭 ×는 탭 전체 실행을 종료. 별도 Background는 탭/분할과 실행을 유지하며 Management에서 Open으로 같은 대상을 회수. 메뉴 이동/탭 선택/화면 숨김·연결 단절은 프로그램 종료가 아님 |
| 연결/제어권 | 실행 상태와 view 연결 상태를 구별. 한 terminal의 입력/resize 소유자는 만료되는 현재 view 하나. 다른 앱/브라우저 view는 관찰 후 명시적 Takeover. 숨김/손실/제어권 상실은 unsent 입력·조합·queue를 취소하며 재연결 시 재전송하지 않음 |
| 상태 복원 | 살아 있는 manager의 지원 VT buffer/mode/cursor·크기·탭/분할을 checkpoint로 복구. pinned `xterm6-v3` adapter·width/checkpoint/build 호환을 유지하고, 서비스 중지·재부팅 후 레이아웃/작업 자동 복원·명령 replay는 없음. 구버전 view/manager는 호환 거부/명시적 갱신 경로 |
| 종료/손실 | generation·정확한 대상·PID birth/session/ancestry 소유권 확인. TERM/HUP 3초 후 필요 시 KILL과 2초 확인, force도 identity 검사 유지. 실패한 대상은 오류와 재시도 가능 상태로 남음. manager 비정상 손실·unknown을 ‘모두 종료’나 빈 성공으로 표시하지 않음. ancestry와 원래 session 소속을 모두 잃은 의도적 분리 작업은 정리 보장 밖 |
| 갱신 | manager 변경/재시작은 영향을 받는 실행 전부 종료·서비스 중지 확인 후 새 빈 manager. 명령 자동 재실행·runtime 무중단 업데이트 없음. 구버전/불일치는 새 실행을 막되 가능한 진단·명시적 종료 경로 제공 |
| 자원/오류 | 1000행 scrollback, 128KiB delta tail, 1MiB/64KiB output pressure, terminal별 256KiB input budget, input event 64KiB, frame 2MiB, 240×80 상한과 현행 queue/checkpoint budget을 유지. 누락 cue·`checkpoint_limit`·부분 paste 피드백·중단 후 Ctrl+C 확인 경로를 숨기지 않음. row 상한은 모든 engine 메모리의 절대 한도가 아님 |
| 보안/정보 | owner-only local IPC, loopback·HTTP mutation의 exact origin과 WebSocket의 독립 검사. 출력이 clipboard 읽기/쓰기·URL/파일 실행·네트워크 fetch를 유발하지 않음. headless의 단독 query 응답·byte 순서·bracketed paste/비bracketed 여러 줄 확인 유지 |
| 저장/관계 | 입력·출력·transcript·serialized 화면·환경 dump의 디스크 저장/색인·자동 전송 없음. private setup/engine/lock/socket/identity만 cache에 둠. shell 자체 history/log 설정은 유지. runtime ID·탭 ID·수집된 Session ID와 Usage·source pipeline은 서로 구별 |
| CLI | 기존 `lb`와 `localbrain` 호환. terminal list/stop과 service install/status/start/stop/restart의 대상·help·JSON/오류·확인/force 의미 보존. help/list/status는 비기동. 앱-only 사용자의 앱 밖 복구 접근은 OP-04에서 결정 |

### Execution Lifetime And Tab Visibility

현재 구현에서 `새 터미널`은 보이는 새 탭을 만들고 선택해 입력할 수 있게 한다.
manager의 새 탭은 `hidden: false`이며 frontend가 새 탭/pane을 선택한다. 별도
`백그라운드로 보내기`는 탭의 숨김 상태만 바꾸고 같은 실행과 분할을 유지한다.
`열기`는 그 탭을 다시 표시한다. 이 동작은 shell의 `command &`나 `bg`/`fg`처럼
프로그램을 foreground/background job으로 전환하는 기능이 아니다.

**실행은 생성 순간부터 독립 manager 소유, 화면은 기본적으로 표시**한다는 기존
흐름을 유지한다. 숨겨야만 앱 종료 후 생존하는 모드는 두지 않는다. 탭 숨김은
탭 바/화면을 정리하는 선택이며 다음 두 상태 축은 독립적이다.

| 상태 축 | 값과 의미 |
| --- | --- |
| 화면 표시 | 표시 중 / 숨김. 탭 표시와 분할을 다루며 실행을 종료하지 않음 |
| 실행 | 실행 중 / 종료됨 / 미확인. 실제 프로그램/manager 상태이며 숨김으로 변하지 않음 |

표현은 `백그라운드로 보내기`를 **탭 숨기기**, 목록의 `열기`를 **다시 열기**로
명확히 하는 안을 추천한다. 짧은 tooltip/접근 가능한 이름으로 `실행 유지`를
설명하고 기존 ×는 pane/탭의 **종료** 의미를 유지한다. 기본 숨김 생성은 입력·
출력·오류·실제 폴더를 확인하기 어렵고 새 작업의 중복 생성을 유발할 수 있어
기본 흐름으로 권하지 않는다. 자동화 전용 숨김 시작 기능을 이번에 추가하지 않는다.
이 라벨은 제안이며 현재 웹 UI/guide를 이미 바꿨다는 뜻이 아니다.

메뉴 이동·창 닫기·일반 Quit은 view 연결을 해제하는 동작이며 모든 탭에 숨김
flag를 저장하는 동작이 아니다. 다시 연결하면 표시 중이던 탭 목록/분할은 남고,
명시적으로 숨긴 탭은 관리 목록에서 다시 연다. 새 터미널은 숨긴 작업 복귀가
아니라 새 실행이며, 숨기기/다시 열기는 새 실행을 만들지 않는다.

### App-Independent Terminal Ownership — Selected Lifetime Contract

**별도 terminal manager가 PTY·셸/소유 자식과 논리 화면·탭/분할·실행 상태를
계속 소유**한다. 앱은 이 manager에 붙는
표시·제어 클라이언트다. macOS에서는 기존 웹처럼 사용자가 처음 실행할 때
사용자 GUI-domain launchd job으로 시작하는 경로를 검토한다. Tauri에 실행 파일을
동봉하거나 셸을 자식으로 만들었다는 사실만으로 앱 종료 후 생존이 보장되지 않는다.

- **앱이 꺼진 동안:** GUI·일반 업무 backend가 종료돼도 manager와 관리 대상은
  살아 있으며 bounded 출력/VT 상태와 실행·종료 상태를 갱신한다. 앱을 계속
  실행하거나 polling시켜야만 추적되는 구조가 아니다. 작업이 스스로 끝나면
  manager는 종료 상태를 보관한다. 셸 생존을 내부 명령·에이전트의 작업 중/완료로
  추정하지 않으며 전체 출력이나 무제한 완료 이력을 보관하지 않는다.
- **앱 재실행:** 같은 설치/설정 scope의 manager를 조회하고 generation·process
  birth identity·호환 버전을 확인한 뒤 기존 runtime ID와 live checkpoint에
  재연결한다. 명령을 다시 실행하거나 새 셸을 원래 작업으로 표시하지 않는다.
  연결 불가/종료/미확인을 실행 중과 구별한다. PID 목록이나 저장한 기록만으로
  잃은 PTY·화면 상태를 복구할 수 있다고 가정하지 않는다.
- **독립 수명의 제공물:** manager·Node/PTY·engine·프로세스 검사 helper가 앱 없이도
  실행·정리 가능한 경로와 버전을 가져야 한다. 앱의 stdio/parent-lifetime pipe나
  종료 시 정리되는 상태에 의존하지 않는다. 앱 교체/제거·cache 청소가 살아 있는
  runtime을 지우지 않도록 책임과 종료/제거 절차를 OP-02/TF-04에서 잠근다.
- **보존 한계:** 현재와 같이 화면/레이아웃은 manager 메모리에만 둔다. manager
  손실·로그아웃·재부팅 후 같은 프로세스/화면을 되살리는 보장은 없고 명령은 자동
  replay하지 않는다. 단순 앱 crash와 manager 손실은 구별하며 unknown/unclean
  loss를 종료 확인으로 바꾸지 않는다. 기록/IPC가 모두 없는 60초 idle 종료와
  OS 로그인 자동 기동 없음은 유지한다.
- **잠자기/깨우기:** LocalBrain은 잠자기 진입을 이유로 manager·셸을 정리하거나
  앱/terminal 복구를 위해 명령을 재실행하지 않는다. 일반 시스템 잠자기 중에는
  상태 보존과 연속 실행을 구별하고 깨운 후 실제 manager·프로세스·연결·입력권을
  재확인한다. 외부 연결의 timeout/프로그램 자체 종료는 실제 상태로 반영한다.
  잠자기 방지·자동 wake·Power Nap으로 임의 작업의 계속 실행을 보장하는 기능을
  추가하지 않는다.

따라서 앱 Quit과 terminal service stop은 다른 동작이다. 앞선 ‘Quit 때 모두 종료’
추천은 대체됐으며 후속 사용자 답변으로 이 유지 방향을 확정했다. 기존 명시적
개별/탭/전체 종료·서비스 중지는 유지하고, **작업 종료 후 앱 종료** 같은 조합
제어의 필요성과 문구는 OP-04에서 정한다.
manager 업데이트·재시작/현재 승인 범위의 앱 교체는 여전히 영향 실행을 종료하고
중지를 확인해야 한다. 일반 Quit 후 유지가 무중단 업데이트를 뜻하지 않는다.

## Terminal-Purpose Interface And Status

### Workspace Composition

- **왼쪽 위:** 사용자 확인에 따라 폴더별 터미널 작업 그룹을 두고, 선택한 그룹의
  탭으로 이동한다. Workstream·수집 Session·Source를 자동 생성/등록하거나 같은
  ID로 취급하지 않는다. 그룹 ID·cwd 상속·membership·제거/수명·저장은 OP-08의 세부 계약이다.
- **왼쪽 아래 제안:** Herdr의 Agents에 대응하는 `작업 현황`에서 그룹을 가로질러
  확인 필요·진행 중·최근 완료를 실제 신호로 모아 보여 준다. 항목을 선택하면 기존
  대상의 탭을 열고 pane에 focus하며 새 셸을 중복 생성하지 않는다. 숨긴 실행도
  이 목록/필터 또는 명확한 별도 회수 진입에서 다시 열거나 명시적으로 종료할 수 있다.
  Settings와 운영 메뉴는 작은 footer에 둔다. 현황 목록의 정확한 배치·정렬·완료/읽음
  해제는 제안이며 OP-09와 디자인 검토로 고정한다. 숨김은 작업 상태와 별개다.
- **위쪽:** compact 탭 바에 이름·상태·선택·×, `+` 새 terminal, 분할/overflow 진입을 둔다.
  긴 경로·shell·서비스 진단은 tooltip/문맥 정보/설정에서 확인한다. 늘 표시하는
  `Terminal` h1와 별도의 큰 `설정 / 실행 중 / 새 터미널` 행은 기본 작업 chrome에서 걷어 낸다.
- **중앙:** 승인한 pane 한도 안에서 사용 가능한 영역을 terminal에 쓴다. 큰 empty card와
  반복 설명을 상시 두지 않는다. 첫 사용/불가 상태는 그 안에서 하나의 명확한 준비/복구
  동작과 필요한 짧은 설명으로 처리하며 설정·서비스 제어를 기능째 삭제하지 않는다.
- 공통 앱 탐색/Back·focus 복귀는 유지하고 Terminal에만 높이·overflow·rail의 특례를
  검토한다. `<main id="main-content">`·논리 제목·키보드/접근성 이름은 유지한다.
  다른 페이지의 padding·카드·token을 일괄 바꾸거나 웹/앱의 공통 shell을 임의로 제거하지 않는다.

‘여러 창’은 후속 사용자 답변으로 **하나의 macOS 앱 창 안의 여러 탭과 각 탭의
분할**로 확정했다. OS 창 관리를 새로 확장하지 않으며 기존 입력권·실행 한도는 유지한다.

### Herdr Reference And Adoption Boundary

2026-11-12에 확인한 공개 기본 layout의 아래쪽은 단순 숨긴 터미널 목록이 아니라
**Agents 작업 현황**이다. 여러 space의 상태 보고 agent를 우선순위/space별로
모으고 고정·접기·해당 pane 이동을 제공한다. pane 없는 하위 작업은 peek으로
열 수 있다. `working`은 spinner, `blocked`는 Needs you/`!`, `idle`은 빈 원,
`done`은 채운 점이며, done은 사용자가 다른 곳을 보는 동안 끝난 상태이고 확인하면
idle이 된다. 일반 셸 생존이나 직전 명령의 성공과 같은 뜻이 아니다.
근거는 [Agents UI](https://github.com/herdrdev/herdr-app/blob/master/defaults/mods/agents/main.js)와
[공식 설명](https://github.com/herdrdev/herdr-app/blob/master/README.md#find-your-work)이다.

sidebar footer의 Settings/Add machine과 별개로 창 하단 status에는 장비·branch가
있을 때 branch·agent 수/확인 필요 수·command palette가 있다. LocalBrain은
그룹/탭/분할·사실에 근거한 작업 현황·빠른 대상 이동·작은 설정/상태 진입을 참고한다.
원격 장비 추가·agent 실행/하위 agent 오케스트레이션·Files/Changes 에디터와
재부팅 뒤 새 셸 복구는 이번 참고만으로 추가하지 않는다.

Herdr의 `tab.settle`은 이 화면에서 치워도 실행하는 별도 기능이며 현재 shipped
layout은 이를 숨김에 쓰지 않고 탭을 모두 나열한다. `terminal.park`는 pane을
제거하고 keep을 끈다. 이를 LocalBrain의 Hide/Open과 같은 동작으로 복사하지 않는다.
LocalBrain의 숨긴 실행 회수·× 종료·no replay는 기존 의미를 유지한다.
자세한 영역/기능별 적용안은 [디자인 계획](../design/terminal-workspace-design-plan.md#herdr-reference-audit)이 소유한다.

### State Meaning And Evidence

현재 manager의 `state=running`은 관리 셸/PTY의 생존 상태이고 `exitCode`는 그 셸의
종료 결과다. FEAT-0169 이전 frontend의 `실행 중`/`읽기 전용`은 명령의 busy/idle/result를
증명하지 않았다. 첫 구현은 [Terminal policy](../../policies/project/terminal.md#folder-workspace-and-status)의
OSC133 명령 metadata와 별도 연결/입력권을 사용하며 비지원 셸은 unknown을 유지한다.

아래는 **LocalBrain의 제안 기호**이며 iTerm2나 모든 터미널의 표준 대응표가 아니다.
색만으로 구별하지 않고 기호·선택 스타일·tooltip/접근 가능한 이름을 함께 사용한다.

| 상태 축 / 기호 예 | 표시할 의미 | 필요한 근거·금지할 혼동 |
| --- | --- | --- |
| 선택된 탭/pane: 밑줄·테두리 | 현재 선택/입력 대상 | 실제 view 선택/focus. 실행 중/성공 색상으로 선택을 대신하지 않음 |
| `⟳` 작업 중 | 명령 또는 명시적으로 보고된 프로그램 작업이 진행 중 | 명령 시작/미종료 또는 프로그램 보고. 셸이 살아 있음이나 출력이 많다는 사실만으로 판정하지 않음 |
| `◇` 프롬프트 대기 | 셸이 명령을 받을 준비가 됨 | 확인된 prompt 신호. 조용한 장기 명령·TUI 입력 대기를 자동으로 이 상태로 바꾸지 않음 |
| `✓` / `✕` 최근 명령 결과 | 관측한 명령의 성공/비성공 종료 | 해당 명령의 종료/결과. 셸 종료 코드·마지막 출력·전체 workflow/AI 작업 완료와 구별. 알 수 없는 취소/신호 종료를 성공으로 바꾸지 않음 |
| `●` 새 출력 | 현재 view에서 아직 확인하지 않은 출력 | 실제 출력과 해당 view의 읽음/표시 근거. 명령 busy·성공과 독립적이며 선택만으로 미적용 출력까지 읽음 처리하지 않음 |
| `!` 주의/입력 필요 | 프로그램이 알린 사용자 개입 또는 별도 실제 오류 | 출처와 원인 구별. terminal 자체 fault·명령 실패·프로그램의 waiting 보고를 같은 성공/완료로 합치지 않음 |
| `■` terminal 종료 | 관리 대상의 종료가 확인됨 | manager의 확인된 종료. 연결 끊김/앱 최소화/숨김/조용한 출력은 종료가 아님 |
| `?` 확인 불가 | 신호 미지원·오래됨·연결/상태 미확인 | 모른다는 상태 유지. default idle·busy·완료로 대체하지 않음 |

같은 실행이 보이는 탭·pane·왼쪽 작업 현황/숨긴 목록 어디에 있어도 상태의 뜻은 같다.
현재 선택/표시/숨김, 앱 창의 활성/비활성·최소화, 입력권·연결, 작업/명령 상태는
독립적이다. macOS `-` 최소화는 탭 숨기기나 프로세스 종료가 아니다. 최소화·앱
미실행 중에도 manager의 상태는 유지하고 복원 시 실제 신호·화면을 조회한다.
Dock badge·메뉴 막대·OS 알림은 별도 기능이므로 이 요청에서 자동 추가하지 않는다.

명령 상태는 지원되는 shell integration 또는 프로그램의 명시적 보고가 후보이며,
OS foreground process 관찰을 쓰더라도 어느 상태를 확인할 수 있는지 따로 정한다.
provider별 자동 실행·원문 해석/색인·외부 AI 추론을 상태 판정의 전제로 삼지 않는다.
사용자의 shell rc·agent 설정을 몰래 수정하지 않으며 호환·비지원/거부 시 fallback을 제공한다.

기본 생존·선택·숨김·연결/오류는 현재 데이터로 보존한다. prompt/busy/명령 결과와
프로그램의 waiting/done은 OP-09의 source·유효성·우선순위 계약을 해결해 제공해야
하며 모양만 추가하고 해당 요구를 완료했다고 판단하지 않는다. 최근 완료의 유지/해제,
새 명령 시작·읽음·새 generation·늦은 이벤트의 처리도 같은 계약이 소유한다.

## User Flows And App Lifetime

| 상황 | 기대 흐름 | 상태와 검토 경계 |
| --- | --- | --- |
| 처음 앱 Terminal 열기 | 메뉴 → 빈 화면 또는 관리 중인 대상 → New | 미사용/목록 조회는 비기동. 동봉 runtime 추천안에서는 npm 설치 화면 대신 준비 여부·실패 복구를 표시 |
| 새 작업/다중 작업 | 저장된 cwd/shell로 New → 보이는 새 탭 선택 → Split/입력·resize | manager는 생성 순간부터 실행을 소유. 경로/폰트/runtime 준비 실패와 생성 결과 미확인을 구별. partial input을 전체 성공으로 표시하지 않음 |
| Session/문서 읽고 돌아오기 | 다른 메뉴 → Terminal 복귀 | 같은 manager/runtime에 연결. 수집된 과거 대화를 현재 프로세스로 오인하거나 자동 resume하지 않음 |
| 앱 창 닫기·숨김/다시 열기 | 현재 host의 hide → reopen | 실행·탭/분할 유지. 숨긴 view는 detach하여 불필요한 화면 처리를 멈추고 복귀 시 live checkpoint로 연결 |
| pane/탭 ×·숨기기 | ×는 명명한 범위 종료, 별도 숨기기는 실행 유지/목록 복귀 | 현재 Background가 숨기기이며 라벨 명확화를 추천. 종료 실패는 숨김 성공으로 처리하지 않고 새 terminal 생성·shell job-control과도 구별 |
| Cmd+Q/명시적 앱 Quit | 앱 GUI/일반 업무 backend 종료, manager/작업은 유지 | **OP-02 방향 확정**. 탭이 보이거나 숨겨져 있어도 동일하다. 앱이 꺼져도 manager가 상태를 소유하고 재실행 시 같은 대상에 연결하며 실제 앱 검증이 필요 |
| crash/강제 종료·backend 복구 | 연결/실행을 따로 확인 → 살아 있는 대상 재연결 또는 unclean loss 표시 | crash는 사용자 승인 종료가 아니며 자식 전부 종료를 증명하지 않음. 이전 명령 자동 replay 없음 |
| 잠자기/깨우기 | 앱/터미널을 종료하지 않고 상태 유지 → 깨운 뒤 live 상태·전송·입력권 재확인 | **OP-02 방향 확정**. 잠자기 중 연속 연산·외부 연결 유지와 구별하며 실제 종료/연결 실패를 반영. 시스템 종료/재부팅 후 같은 프로세스 보존은 범위 밖 |
| 시스템 종료/재부팅 | OS에 따라 프로세스 종료, 다음 시작에 이전 명령 자동 실행 없음 | 새 셸을 원래 실행으로 표시하거나 memory-only 화면/탭 상태가 복원됐다고 주장하지 않음 |
| 개발용 웹/앱 함께 사용 | 필요할 때 같은 manager 공유 또는 분리된 설치/설정 scope 사용 | **OP-03 미정**. 동시 사용은 필수 제품 흐름이 아님. 공유 선택 시 입력권 인계·버전 거부·다른 view의 변경/종료 영향, 분리 선택 시 목록/종료 scope를 확인 |
| 업데이트/앱 교체 | 영향 범위 확인 → 해당 manager/실행 종료 확인 → 교체 → 새 앱/서비스의 빈 상태 | 앱 payload를 쓰는 helper가 사라지지 않아야 함. 미확인 종료에서 진행 금지. 공유 service라면 웹 작업도 영향 대상이며 OP-03과 함께 결정 |
| 앱/웹이 꺼진 상태에서 복구 | 앱 재기동 또는 승인한 별도 관리 진입으로 조회/종료 | PATH CLI를 자동 설치할지와 앱 없이 남긴 실행의 관리 가능성은 OP-04. 시스템 Node/npm 존재를 전제로 삼지 않는 안 |

일반 창 닫기·메뉴 이동의 유지, ×의 종료, 업데이트의 명시적 전체 종료는 기존
동등성 기준이다. **앱 완전 종료/잠자기 후 유지는 사용자 선택으로 확정**됐고,
개발용 웹과의 실행 공유·배포 방식은 남아 있다. 문서의 확정된 수명과 현재 앱의
미구현 상태, 그 밖의 라벨/조합 제안은 구별한다.

## Uncertainty — Decision Register And Remaining Items

OP-02의 수명 방향은 사용자 답변으로 확정됐다. 생성한 두 Feature를 끝까지
진행하라는 명시적 승인으로 OP-01/03/04/05의 제공물·공유/관리·core 권장안도
[FEAT-0168 runtime 계약](../project/app-independent-terminal-runtime-contract.md)과
[FEAT-0167 core 계약](../project/rust-core-and-host-contract.md)에서 확정했다.
두 Feature는 계약 PASS이며 실제 구현/앱 수락은 별도다. OP-06의 제품 측정/물리
입력·접근성 환경과 budget은 관련 product Feature 승인 전에 잠근다.
확정된 수명을 다시 선택하도록 묻지 않는다.
새 UI의 OP-07은 단일 앱 창으로 결정됐다. OP-08의 최초 폴더별 그룹은
FEAT-0173에서 사용자가 요청한 독립 이름·여러 폴더·빈 그룹 저장 모델로 대체됐다.
FEAT-0169는 첫 웹 구현의 당시 모델과 명령 신호/현황·읽음을 고정한 기록이다.
아래 OP-08/09의 후속 확장은 관련 Feature에서 다룬다. 확정된 창 범위나 그룹 필요성을
다시 선택하도록 묻지 않는다.

| ID | 선택 / 남은 질문 | 결정·근거 / 최초 검토 |
| --- | --- | --- |
| OP-01 | **결정됨: 동봉 + 명시적 첫 사용 때 준비/기동.** 최초 질문: 앱이 필요한 Node/PTY 구성요소를 동봉할지, 별도 설치/첫 사용 다운로드를 요구할지? | **선택된 계약:** Node24.15 arm64/현재 lock engine·Rust helper를 동봉한 verified private payload. 페이지/조회는 비기동, 실제 빌드/ABI/서명/오프라인 첫 사용 증거는 후속 product 의무. **최초 검토 근거:** **동봉 + 첫 명시적 실행 때 manager 기동**을 권한다. 사용자는 Node/npm을 별도로 설치하지 않고 offline으로 첫 셸을 열 수 있다. 앱 용량·라이선스/서명 검증 비용이 늘어난다. 빌드하는 개발자의 Node/npm 필요와 앱 사용자의 runtime 설치를 구별 |
| OP-02 | **결정됨: 앱 종료·잠자기에는 작업 유지, 시스템 종료에는 프로세스 종료** | 사용자 후속 답변으로 일관된 수명을 선택했다. 모든 새 terminal은 생성 순간부터 독립 manager 소유이며 숨기기 여부와 생존을 연결하지 않는다. 일반 Quit과 명시적 개별/탭/전체/서비스 종료를 구별한다. 잠자기 중 연속 연산은 요구하지 않고 깨운 뒤 실제 상태로 재연결한다. 독립 runtime/helper 안정 경로·앱 없는 조회/종료·업데이트/제거 수명·scope·미확인 처리와 안내를 구체화해야 하며 구현/전체 PRD 승인과는 별개 |
| OP-03 | **결정됨: data/cache scope와 호환 버전 기준.** 최초 질문: 개발용 웹과 앱이 같은 manager/터미널 목록을 공유할지? | **선택된 계약:** 현재 root/launchd label 파생식과 full scopeHash를 보존·결합. 동일 호환 scope는 공유, 다른 scope 분리, mismatch/unknown은 무단 교체/새 작업 거부. **최초 검토 근거:** **UI 종류가 아닌 설치/설정 scope와 버전으로 실행 소유 범위를 정하는 안**을 권한다. 웹은 개발 확인 경로이므로 두 제품의 상시 동시 사용이나 강제 분리를 전제로 하지 않는다. 현행 data+cache scope가 같으면 공유하므로 분리도 명시적 변경이다. 공유 시 identity·버전/지문·전역 32개 상한·입력권·전체 종료/교체의 교차 영향을, 분리 시 각 목록/종료 범위를 잠근다. 개발/설치 버전 불일치가 기존 manager를 조용히 교체하거나 중복 시작하게 해서는 안 됨 |
| OP-04 | **결정됨: 안정 cached management launcher.** 최초 질문: 앱만 설치한 사용자가 앱 밖에서 남은 작업을 어떻게 조회·종료할지? | **선택된 계약:** runtimeRoot/localbrain-terminal이 같은 payload/core의 기존 list/stop/service 문법으로 앱 없이 관리. PATH/rc 변경, run/attach 추가 없음. **최초 검토 근거:** **앱 Management + 명시적 앱 동봉 관리 진입점**을 권한다. PATH/기존 `lb`를 조용히 덮어쓰지 않으며 웹용 기존 CLI는 보존한다. OP-02의 유지 결정에 따라 앱이 없어도 사용할 수 있는 관리 경로가 필수. terminal stop과 service stop을 구별 |
| OP-05 | **결정됨: 공통 Rust control/helper와 Node/headless 유지.** 최초 질문: 앱 터미널 최초 전달은 Python backend 통합인지 Rust 코어인지, Node/headless는 유지할지? | **선택된 계약:** FEAT-0167이 첫 Rust slice/host topology를 고정. 앱 접근/그룹/명령상태 foundation과 실제 앱 통합 product는 별도이며 Python/Rust 앱 bridge를 중복 완성하지 않음. **최초 검토 근거:** PRD-0029와 **공통 service/protocol·helper 책임을 먼저 정하고 선택한 코어의 실제 앱에서 검증**하는 안. Node/headless 유지가 첫 동등성의 부담을 줄인다. Rust PTY/VT 재작성은 여기서 자동 승인하지 않으며 Python/Rust 두 통합을 중복 완료 조건으로 두지 않음 |
| OP-06 | **플랫폼 결정 / 실제 제품 수락 범위·수치 남음.** 최초 질문: 지원 환경·한글/접근성과 성능의 앱 수락 범위는? | **선택된 계약:** 첫 대상은 Apple Silicon/macOS14.0+, physical IME/VoiceOver·actual host·native 전체 budget/시험 환경은 관련 product 승인 전에 확정하고 미검증을 구별. **최초 검토 근거:** **현재 Apple Silicon macOS 앱을 첫 대상**, web/독립 WKWebView 결과는 참고로만 권한다. 선언 최소 macOS 14, 실제 시험 OS·장비와 물리 한글 입력·VoiceOver의 수락 포함 여부/미검증 취급, app subtree resource/UI budget을 Feature 전에 고정. Windows·Intel·Rosetta 지원을 자동 추가하지 않음 |
| OP-07 | **결정됨: 하나의 macOS 앱 창 안에서 여러 탭과 탭당 최대 4분할** | 사용자가 Obsidian의 `+` 탭 전환처럼 설명하고 실제 macOS 다중 앱 창은 제외했다. 기존 단일 입력권·관리 scope·수명/상태/읽음과 OS 활성/최소화 검증은 유지하며 새 다중 창 기능은 만들지 않음 |
| OP-08 | **후속 사용자 결정: 폴더와 독립된 이름 있는 영속 작업공간.** | **현재 선택:** [FEAT-0173](../feature/feat-0173-persistent-terminal-workspaces.md)에서 여러 폴더의 탭, 한 탭 안의 여러 폴더 pane, 선택적 기본 cwd, 빈 그룹 유지·이름/기본값 변경·빈 그룹 제거·명시적 탭 이동을 승인했다. app data/백업에 metadata만 저장하고 generation-bound membership은 프로세스 복원·명령 replay와 구별한다. `cd`는 pane cwd만 바꾸며 Project/Source/Workstream/Session ID를 만들거나 암묵 변환하지 않는다. **대체된 최초 계약:** FEAT-0169의 생성 cwd realpath key·고정 root New·pane cwd/shell Split·폴더 열기=첫 terminal·선택 비기동·숨김/종료 retained tab 소속·마지막 tab 제거 시 그룹 제거·memory-only/독립 이름·이동·빈 그룹 저장 제외는 당시 [Run249](../run/run-20261112-249-terminal-workspace.md)의 경계로 보존한다. **최초 검토 질문:** Settings 기본값/그룹 폴더/활성 cwd 상속, `cd`/폴더 이동 정체성·표시, 이름/이동/삭제·종료 범위, 빈 구조와 프로세스/화면 복원의 구별 |
| OP-09 | **첫 웹 구현 결정: OSC133 명령 신호와 로컬 완료 attention.** 프로그램 waiting/done·미열람 출력은 후속 | **선택된 범위:** 기존 연동이 보내는 OSC133 A/B prompt, C running, C 뒤 D completion+0–255/null 결과만 수신. B 뒤 D 취소/중복/잘못된 결과는 완료 증가에서 제외. manager 생존/셸 exitCode와 구별하고 비지원은 unknown. 현재 generation/terminal/completion별 attention은 해당 frame을 실제 paint한 뒤 visible·window focus·pane keyboard focus가 모두 있어야 해제. 탭/pane/아래 현황이 같은 의미를 사용하고 오류/종료 우선, signal 감지를 위한 추가 process polling·자동 rc/agent 설정 변경·출력 의미 추측 없음. 구세대는 기존 build 거부/관리만 허용. **최초 검토 질문:** 명시적 shell/program source, 지원·opt-in/해제·fallback, 상태 우선순위·늦은 이벤트·최근 완료/미열람 출력·읽음·자원 budget. 프로그램별 waiting/done 연동과 실제 native 최소화/OS focus 증거는 이 웹 increment로 완료하지 않음 |

OP-09에서 사용자가 명시적으로 포함한 **새 zsh 자동 연동**은 후속 FEAT-0173에서 전달됐다.
앱 외부의 검증된 전용 시작 파일로 같은 OSC133 parser와 OSC7 cwd를 공급하며,
사용자 rc/alias·기존 훅을 보존하고 이미 실행 중인 셸에는 주입하지 않는다.
당시 문서의 “미보고 상태는 작은 점, 실제 prompt는 빈 원” 설명은 후속
[FEAT-0177](../feature/feat-0177-terminal-activity-and-background-rail.md)의 승인된 표시 규칙으로 대체됐다.
현재 미보고 전경 상태는 실행·대기로 추정하지 않고 표시 공간을 비워 두며,
선택 ✓·숨김 ◇의 우선순위는 별도로 유지한다. 현재 규칙은
[Terminal 상태 계약](../../policies/project/terminal.md#folder-workspace-and-status)이 소유한다.
최초 parser/attention 규칙과 프로그램 waiting/done·미열람 출력·물리 입력의 별도 수락 경계는 유지한다.

### Technical Confirmations

아래는 승인된 제품 방향 안에서 기술 조사로 해결할 항목이다. 결과가 위 선택이나
사용자에게 보이는 동작·수락 범위를 바꾸면 PRD로 되돌린다.

| ID | 확인할 사실/계약 | 완료 근거의 범위 |
| --- | --- | --- |
| TF-01: 제공물 | Node 버전·arm64 ABI와 node-pty `.node`/spawn-helper, manager/headless/checkpoint/lock·브라우저 xterm·D2Coding/OFL·Docs의 버전/지문, license·실행 권한·서명·quarantine·오프라인 준비 | Tauri의 Node sidecar 예시만으로 네이티브 module이나 현재 runtime cache 구성이 전달된다고 보지 않음. 실제 빌드 artifact와 사용자 runtime 없는 기동 조건 확인 |
| TF-02: 프로세스 검사 | 현재 `runtime.py`와 manager가 `sys.executable -S processes.py` 또는 전달받은 Python으로 PID birth/session을 검사. frozen backend는 일반 Python interpreter 진입점이 아님 | 앱이 제공하는 전용 helper/worker mode 또는 Rust 검사 중 선택한 경로로 소유권·종료 확인. backend가 꺼진 동안의 helper 가용성도 OP-02/03과 맞춤. 파일을 동봉했다는 사실만으로 실행 성공을 판정하지 않음 |
| TF-03: 인증/stream | 앱 per-launch secret/cookie와 random loopback port, HTTP admission·exact origin, WebSocket handshake·읽기/입력/resize 접근, CSP의 font/stream·최소 native 권한 | 현행 HTTP middleware는 WS 인증을 대신하지 않는다. 인증 없는/구세대/다른 origin 연결을 runtime 명령 전에 거부. 앱 token을 shell 환경·출력·영속 파일에 전달하지 않음 |
| TF-04: 수명/업데이트 | manager/job/socket·control lock·generation의 소유자, Quit/취소/실패·강제 종료·재연결, `.app` 교체/제거·cache 청소 중 executable/helper/engine의 안정 경로/retention, old/new build 호환과 duplicate start 거부 | 현재 manager 코드 경로는 설치 payload에 의존한다. 선택한 독립 수명 아래 앱/일반 backend가 실제 종료된 동안 같은 manager·셸이 생존하고 다음 앱이 같은 실행에 연결함을 확인. 빈 목록/unknown·backend 종료만으로 모든 terminal이 끝났다고 주장하지 않으며 기존 업데이트의 종료 확인도 생략하지 않음 |
| TF-05: 환경/입력 | Finder/Dock 실행의 default shell·PATH/locale·ZDOTDIR, 실제 앱 IME·조합 중 키/삭제·paste 거부·Ctrl/Cmd·focus 복귀·한글 폭·font load·clipboard·VoiceOver·narrow layout | JavaScript 합성 이벤트, OS 이벤트를 넣은 독립 WebKit, 물리 입력을 한 LocalBrain 패키지 앱의 근거를 구별. 사용자 rc·OS font를 수정하지 않음 |
| TF-06: 자원/기존 기능 | 앱 시작/Terminal 비사용, 0/1/8 shell·4 pane·TUI/flood·실제 hide/reopen·잠자기/복귀·reconnect, Sessions/상세/검색·설정과 기존 GUI 반응 | manager RSS/CPU와 backend·WebView·shell·앱 전체 비용, input-to-paint·제어 p95·장시간 증가를 분리. 기존 웹의 manager 96/160MiB·idle CPU 1% 미만, input p95 150ms/flood control 250ms 미만은 비교 기준이며 native 전체 예산은 별도로 합의 |
| TF-07: 설정/복구/Docs | Terminal settings/Docs admission과 package data, common revision의 충돌·unknown fields 보존, cache clear·backup/restore·scope 분리/공유, CLI 진입과 오프라인 안내 | Terminal 추가만으로 다른 optional feature를 통째로 여는 변경 금지. 실행 중 cache/engine을 일반 캐시 정리로 지우지 않음. backup은 memory-only terminal state를 복원하지 않음 |
| TF-08: 상태 신호 | shell/program/foreground 관찰이 실제로 제공하는 상태와 신뢰 한계, 임시 설치/설정·해제, runtime ID/generation·순서·유효성·명령 결과/agent 보고 구별, manager/API/view handshake | 신호는 bounded metadata이며 clipboard/명령 실행/색인 권한을 주지 않는다. 구버전 manager와 미지원 shell에서 무근거 idle/성공을 표시하지 않고 기존 작업을 명시적 중지 없이 교체하지 않음. 신호 감지를 위한 무거운 idle polling을 추가하지 않고 실제 CPU/update 비용 확인 |
| TF-09: frame/view | Terminal만의 available-height·overflow·rail/상단 탭, shared shell/Back·focus·IME anchor·font 측정과 bounds, host 활성/최소화·read/render ack·attention 보존 | `document.hidden`만으로 OS 최소화를 검증했다고 주장하지 않음. 제목/큰 버튼을 줄여도 accessible name·설치/font/연결/종료 실패와 contextual recovery를 보존. 다른 페이지 token과 현재 terminal 자원/차원 상한은 별도 승인 없이 바꾸지 않음 |
| TF-10: group/view | 선택한 단일 앱 창과 폴더 그룹의 ID·scope·membership·input/view/attention 소유와 수명, narrow 변환·제거/복귀 의미 | 새 영속화를 선택하면 data 계약 필요. 폴더 이동/새 group 생성은 Source 등록·Session/Workstream 조직 변경이나 OS 창 추가를 자동 수행하지 않음 |

## Excluded Scope

- 기존 첫 웹 전달의 승인/평가를 새로 쓰거나 앱 포함이 이미 완료된 것처럼 정책·
  README·사용자 guide를 바꾸는 일. 승인된 구현 시 실제 owner를 함께 갱신한다.
- Windows/PowerShell·Intel/Linux·모바일, SSH/원격 호스트 관리, 외부 iTerm2 창/세션
  attach, 자체 셸·VT 엔진, herdr-core 직접 의존성, IDE/파일 편집기 추가.
- 자동 장기 transcript·입출력/화면 영속화·검색/Usage 편입, 과거 Session/명령 자동
  replay/resume, 미제공 기능 활성화, OS login 자동 기동·무중단 runtime 업데이트.
- 자동 updater·App Store·유료 가입/서명 자격 증명 사용·Apple 제출·공개 배포.
  기존 수동 설치/교체와 서명·공증/수신자 검증 경계는 별도 owner를 유지한다.
- 앱-only CLI의 사용자 PATH 자동 수정, Node/npm/Python의 전역 설치, shell rc·
  OS font 변경, 개발자의 cache/credentials·개인 자료를 앱에 동봉하는 일.

사용자가 terminal에서 실행한 프로그램은 사용자 권한으로 파일·네트워크를 쓴다.
이 로컬 터미널을 OS sandbox나 외부 전송 차단으로 표현하지 않으며, LocalBrain의
자동 전송·수집 권한을 확대하지 않는다.

## Constraints

- **Fullstack Product** 범위이며 `contract`, `backend`, `frontend`, `integration`,
  `infra`, `docs` lane을 가진다. 새 영속 상태를 선택하면 `data` 계약도 확정한다.
  Foundation 수명/인증/제공물 계약과 Product 앱 흐름을 분리해 Feature로 제안한다.
- 디자인·폰트·간결한 제어·상태와 error recovery를 기존 owner에 맞춘다.
  상시 기술 설명이나 별도 dashboard 페이지를 늘리지 않고 terminal 안에서
  사용자가 필요한 동작을 찾을 수 있어야 한다. 제안한 rail의 작업 현황은 이 원칙 안에서 검토한다.
- Terminal 전용 frame은 사용자 요청에 따른 scoped 조정이다. 현재 canvas 높이/일반
  page overflow·chrome와의 reconciliation은 Design Plan이 소유하며 다른 화면 법칙을
  함께 바꾸지 않는다. 영구 디자인 법칙의 변경은 별도로 승인된 owner 갱신으로 넘긴다.
- 실행/화면 상태는 계속 manager가 소유한다. frontend/Rust/backend 교체가 원래
  실행과 새 셸을 혼동하거나 입력을 replay·중복 실행하게 해서는 안 된다.
- 소스·browser·wheel·독립 WKWebView의 검증은 같은 코드가 빌드한 앱에서 실행된
  근거와 구별한다. 최신 웹 Eval0162의 제한을 앱 수락으로 자동 승격하지 않는다.
- 이 PRD는 현재 native exclusion을 해제하지 않는다. 승인/구현 시 Terminal policy,
  architecture·desktop/settings·trial capability·설치/복구·디자인·Docs의 실제
  소유자를 함께 정합화해야 한다. 다른 기능의 제공 경계는 보존한다.

## Acceptance Envelope

| ID | 충족해야 하는 결과 |
| --- | --- |
| A-01 | 실제 빌드된 앱에 Terminal 메뉴·page/API/stream·Settings·조건부 한/영 Docs와 필요한 자산만 제공된다. 기존 app 기능·Docs/Settings·중단 기능·웹/CLI 경계를 보존한다. |
| A-02 | 선택한 제공 방식의 전제 아래 첫 새 셸·오프라인 사용·준비 실패/복구가 동작한다. 동봉안이면 사용자 Node/npm/Python 설치·cache·checkout 없이 가능하고 구성요소 version/지문/ABI·font/license가 build provenance와 일치한다. |
| A-03 | parity 표의 탭/4 pane·32 record·설정/즉시 생성·split 상속·Background/Open/×·반응형·오류/상한이 실제 앱에서 기존 웹 계약과 일치한다. invalid defaults와 생성 응답 손실도 확인한다. |
| A-04 | 같은 앱에서 실제 shell·한글 IME·조합/paste·Ctrl/Cmd·focus·clipboard·font/셀 폭·TUI/대체 화면·resize를 승인 환경으로 확인한다. 물리 입력/VoiceOver/다른 OS가 미검증이면 각각 표시하고 합의한 acceptance를 넘겨 통과시키지 않는다. |
| A-05 | 창 닫기/다시 열기·메뉴 이동·hidden return·backend 재시작·연결 손실·잠자기/깨우기에서 원래 실행과 지원 VT 상태가 선택한 정책대로 유지된다. unsent 입력/명령이 replay되거나 새 셸로 조용히 대체되지 않는다. |
| A-06 | OP-02/03의 Quit·공유/분리·앱 없는 관리·실행 scope 정책을 일관되게 제공한다. 공유 선택이면 웹/앱의 한 입력권과 전역 대상/상한, 분리 선택이면 각 목록·종료 범위를 검증하며 다른 scope 작업을 잘못 종료하지 않는다. |
| A-07 | 정상/강제 종료, old generation·PID 재사용·상태 미확인·helper 실패·부분 종료가 identity-safe하고 실패를 감추지 않는다. 확인 취소·대상 변경/경합과 app Quit/교체 실패 경로가 선택한 계약과 일치한다. |
| A-08 | 교체 전 영향 대상 종료·manager 중지 확인, 새 앱/manager 기동·구버전 거부·실패 복구를 실제 artifact로 확인한다. 사라진 `.app` 경로에 남은 서비스가 의존하지 않고 종료된 명령을 재실행하지 않는다. |
| A-09 | HTTP·WS/채택한 IPC의 앱 인증·origin·local Host·view 권한 검사를 별도로 확인한다. 인증 없는 stream은 상태/출력/입력 전에 거부되고 app secret은 shell로 흘러가지 않으며 출력의 clipboard/실행 부작용은 차단된다. |
| A-10 | 승인 workload/수치에서 전체 자원·입력/제어·기존 GUI 반응성을 충족한다. 비사용 startup·실제 hidden·flood 진행 중 peer/control·재연결을 포함하고 이전 웹 수치를 앱 전체 성능으로 보고하지 않는다. |
| A-11 | private runtime/cache와 memory-only 화면 정책·no transcript/index·기존 Session/Usage/원본 보존을 유지한다. cache 청소/백업·restore가 실행 중 구성요소를 지우거나 terminal state를 복원했다고 오인시키지 않는다. |
| A-12 | 명시적 관리 진입으로 앱-only/웹 사용자 각각 실행·service를 찾고 종료할 수 있다. 상태/list는 비기동이며 기존 `lb`/`localbrain` 의미·실패/확인·사용자 PATH를 보존한다. |
| A-13 | 앱 안내에서 window close·Background·×·Quit·업데이트의 차이, 남은 작업 관리·보관/복구 한계를 이해할 수 있다. 실제 지원/검증 범위를 전달하며 앱 빌드 성공과 사용자·수신자 수락을 구별한다. |
| A-14 | 단순 창 숨김이 아니라 앱/일반 업무 backend의 실제 종료, 별도 manager·셸의 생존과 출력/종료 상태 갱신, 앱 새 실행 후 같은 generation/runtime ID·지원 checkpoint 연결을 검증한다. 명시적으로 숨기지 않은 보이는 탭도 유지된다. 그동안 끝난 실행·manager 손실은 각각 종료/미확인으로 처리하며 저장한 PID만으로 생존을 주장하거나 명령을 replay하지 않는다. |
| A-15 | 새 terminal은 보이는 탭으로 생성·선택되고 Split은 보이는 pane을 추가한다. 숨기기/다시 열기는 같은 ID·실행 수·탭/분할을 유지하며, ×는 기존 범위를 종료한다. 표시/숨김·실행/종료/미확인과 shell job-control을 혼동시키지 않는다. 앱 Quit/재연결이 모든 탭의 hidden flag를 바꾸거나 새 실행을 생성하지 않는다. 라벨 제안의 채택 여부와 관계없이 동일한 동작을 보존한다. |
| A-16 | 실제 앱/manager가 있는 상태에서 일반 잠자기·깨우기 후 같은 실행/화면에 재연결하고 생존·종료·연결 실패/입력권을 구별한다. 앱 종료와 잠자기의 조합에서도 LocalBrain이 작업을 정리/명령 replay하지 않는다. 시스템 종료/재부팅은 이전 프로세스 연속성 요구에서 제외하며 UI 테스트/소스 검사만으로 실제 sleep/wake를 통과했다고 보고하지 않는다. |
| A-17 | Terminal에서 일반 page heading/큰 action·상시 empty/관리 chrome가 작업 공간을 불필요하게 차지하지 않는다. rail/탭/분할·설정/운영·숨김/복귀·생성/종료에 접근하며 main/논리 제목·이름·focus·tooltip·설치/오류·종료 확인을 유지한다. 다른 Sessions/문서/Settings 화면은 보존한다. |
| A-18 | 기호는 승인한 실제 source·유효성·명령/프로그램 범위와 일치한다. 출력 없는 장기 명령·prompt·실패/취소·TUI·미지원/구버전/단절·늦은 이벤트를 구별하고 shell 생존/exitCode나 출력 정지로 busy/idle/result를 날조하지 않는다. 최근 명령 성공을 전체 작업 완료로 표시하지 않는다. |
| A-19 | 선택/focus·표시/숨김·창 활성/최소화, 입력권/연결, 작업 상태와 미열람 출력/완료가 탭·pane·숨긴 목록과 채택한 작업 현황에서 같은 의미를 갖는다. 최소화/숨김/미실행 중 발생한 상태는 승인 조건까지 남고 단순 선택이나 늦은 ack가 미적용 출력을 읽음 처리하지 않는다. 낮은 motion·색 구별 한계·키보드/assistive 경로와 실제 host를 확인한다. |
| A-20 | 선택한 단일 앱 창과 OP-08/FEAT-0173의 이름 있는 작업공간·다른 폴더의 탭/pane·빈 그룹 저장·명시적 이동/제거·ID/수명을 제공한다. 실제 OS 다중 창·Source/Workstream 자동 연결·합의하지 않은 추가 영속 상태를 도입하지 않고 명확한 그룹/탭/pane 종료 영향과 runtime 한도를 유지한다. |

## Candidate Features

아래는 인간 경계 검토를 위한 후보 결과다. ID/Feature 파일·Spec·Run을 생성하거나
승인하지 않으며 표를 병렬 실행 지시나 구현 순서로 취급하지 않는다.
C-01은 [FEAT-0168](../feature/feat-0168-app-independent-terminal-runtime-contract.md)으로
구체화돼 Run248에서 독립 runtime 계약 PASS를 받았다. C-02/C-06/C-08 접근/상태/그룹
중 그룹/명령 signal의 첫 범위와 공통 frame은 [FEAT-0169](../feature/feat-0169-terminal-workspace.md)의 contract→backend→frontend lane으로 고정해 웹에서 구현·검증했다. [Run249](../run/run-20261112-249-terminal-workspace.md)/[Eval0165](../evaluation/eval-0165-terminal-workspace.md)가 실제45 browser/73 Node/1651 Python 및 별도 real PTY 증거와 플랫폼 한계를 소유한다. 앱 접근과 제공물/native product 후보는 별도 경계로 남는다.

| 후보 | 성격 / 제안 profile | 결과·의존성 |
| --- | --- | --- |
| C-01: 앱 실행·수명·scope 계약 | Foundation / foundation-contract | runtime 소유·버전·helper·공유·업데이트·CLI 복구 경계 고정. OP-02의 확정 수명을 구현 계약으로 구체화하며 OP-01/03~05의 남은 선택 필요, Rust PRD의 공통 코어 계약과 교차 참조 |
| C-02: 앱 terminal 접근·프로토콜 계약 | Foundation / foundation-contract | 앱 HTTP/WS/IPC의 인증·origin·lease·checkpoint·호환 거부와 비기동 경계. C-01 의존 |
| C-03: 동봉 앱의 첫 terminal과 전용 frame | Product / fullstack-product | 지원 설치에서 별도 runtime 설치 없이 compact rail/tabs/canvas·설정·첫 셸·font/IME·기존 앱 탐색을 사용. 동봉안·OP-07/08 경계와 C-01/02가 전제이며 상태 source 구현을 흡수하지 않음 |
| C-04: 앱의 다중 작업·숨김·재연결 | Product / fullstack-product | 웹의 실행 계약을 보존한 그룹/탭/분할·Open/Hide/×와 실제 hidden/reopen·single-owner 흐름. C-01/02와 C-03·C-08 의존 |
| C-05: 앱 종료·교체·실패 복구 | Product / fullstack-product | 합의한 Quit/공유 범위·앱 없는 관리·종료 확인·수동 교체를 실제 artifact에서 사용. C-01/02와 앱 동작 의존 |
| C-06: 명령/프로그램 상태 source 계약 | Foundation / foundation-contract | OP-09의 signal·범위·유효성·설정 영향·fallback·순서/attention/해제·자원 계약 고정. shell 생존/셸 종료 결과와 분리하며 기존 rc/개인 원문을 보존 |
| C-07: 상태 기호와 작업 회수 | Product / fullstack-product | 탭/pane/작업 현황·숨긴 목록에서 사실에 맞는 기호·선택·미열람/완료·최소화/복귀와 기존 대상 이동을 읽고 접근 가능한 설명을 사용. C-06과 frame/다중 작업 결과가 전제이며 현황의 정확한 배치는 제안 |
| C-08: terminal 작업 그룹 계약 | Foundation / foundation-contract | 선택한 폴더별 terminal group과 기존 Project/Workstream/Source의 구별, ID·membership·cwd/scope·삭제/수명·저장을 고정. 그룹 필요성은 재선택하지 않으며 세부 계약은 OP-08에 남음 |

별도 OS 다중 창은 사용자 선택으로 제외했다. 위 후보를 근거로 창을 자동 추가하거나
한 product Feature에 해결되지 않은 상태/group foundation 구현을 합치지 않는다.

각 결과에 contract·design·functional·interaction과 packaging/resource·회귀 근거가
필요하다. 새로운 사용자 기능을 만들기 위해 문서/시험만 독립 Feature로 나누지 않는다.

## Continuity Notes

- `2026-11-12` 진행 지시: 합의한 제품 방향과 Feature 기획의 승인으로 반영했다.
  [FEAT-0168](../feature/feat-0168-app-independent-terminal-runtime-contract.md)에
  동봉/lazy-start·기존 data/cache scope·안정 payload/helper·앱 없는 관리와
  Quit/sleep/update의 계약 경계를 구체화했다. FEAT-0167 뒤의 별도 foundation이다.
  앱 접근·폴더 그룹·명령 상태는 후속 독립 foundation으로 남기고 새 Feature를
  자동 승인하지 않았다. 현재 native 제외·코드·사용자 실행은 바꾸지 않았다.

- `2026-11-12`: 기존 웹 전용 첫 전달은 유지한 채 macOS 앱 동등성을 새로운 draft로
  작성했다. 후속 사용자 확인에 따라 Rust 전환 PRD-0029와 연결했다. 동봉·지연 기동,
  Quit 시 종료·웹/앱 실행 scope 분리는 추천이며 사용자 결정이 아니다. 기존 웹의
  완료 결과와 native/물리 입력/장시간 증거 한계를 구별했다. 코드·runtime·현재
  정책·설치 앱은 변경하지 않았고 Feature/Spec/제품 평가를 시작하지 않았다.
- `2026-11-12` 앱 중심 사용과 종료 질문: 공통 업무 코드의 Tauri 분리·앱 중심 일상
  사용·개발 확인용 웹·장기 기능 동등성을 사용자 확인으로 반영했다. 앱 종료 후
  background terminal 유지/추적 가능성 질문에 따라 독립 manager의 소유·재연결·
  제공물 수명과 검증 조건을 보완했다. OP-02의 기존 ‘Quit 때 모두 종료’와 OP-03의
  웹/앱 실행 scope 분리 기본 추천은 각각 Quit 후 유지와 설치/설정·버전 기준 scope
  검토로 대체했다. 질문을 해당 정책의 승인으로 취급하지 않으며 기존 업데이트
  종료·no replay·메모리 보관·비정상 손실 한계와 현재 native 제외는 유지한다.
- `2026-11-12` 수명 선택·표시 설명: 사용자가 일관성을 조건으로 앱 종료/잠자기
  후 작업 유지와 시스템 종료 시 프로세스 종료를 선택했다. OP-02를 미결정에서
  결정 기록으로 전환하고 실제 Quit·sleep/wake 수락 조건을 보완했다. 기존 New는
  보이는 탭 생성, Background는 실행을 유지한 탭 숨김임을 코드/guide로 확인했다.
  생성 순간부터 독립 manager 소유와 표시 상태를 구별하고 현재 생성/종료 의미를
  유지한다. ‘탭 숨기기’/‘다시 열기’ 라벨은 추천이며 코드/UI는 변경하지 않았다.
  전체 PRD/Feature/구현 승인, manager 공유·engine 전환·새 OS 전원 설정은 확정하지 않았다.
- `2026-11-12` Terminal 전용 공간/기호 요청: 사용자가 현재 `main` DOM의 일반
  페이지 표현을 줄이고 Herdr의 작업 공간/숨긴 항목·상단 탭/분할과 iTerm2 같은
  상태 기호를 요청했다. 실행 동등성과 화면 복제를 구별하고 배치·상태 신호·
  최소화/attention·접근성/복구를 PRD에 추가했다. design-plan으로 별도 디자인
  track을 연결했다. OP-07/08 질문은 답변 대기이며 glyph mapping은 제안이다.
  signal 없는 idle/result를 완료로 위장하지 않고 기존 수명·× 종료·no replay·
  native 제외/실제 증거 한계를 유지한다. 코드·정책·설치 앱은 변경하지 않았다.
- `2026-11-12` 후속 답변과 Herdr 재확인: 실제 OS 다중 창은 제외하고 하나의 앱
  창 안의 탭/분할, Workstream/수집 Session과 별개인 폴더별 터미널 작업 그룹을
  사용자 선택으로 반영했다. OP-07과 OP-08의 방향은 답변 대기에서 결정 기록으로
  전환했으며 그룹 세부 계약은 남는다. 공식 현재 기본 layout은 왼쪽 Spaces 아래
  Agents 작업 현황이고 footer와 창 하단 status가 별도임을 확인했다. 앞선 아래쪽=
  숨긴 목록 가정을 정정하고 현황/빠른 이동·별도 숨김 회수를 제안으로 연결했다.
  설치 Herdr UI를 실행한 근거는 아니며 원격/agent 자동화·재부팅 새 셸 복구를
  추가하지 않았다. PRD는 draft이며 구현/정책/설치 앱은 변경하지 않았다.

- `2026-11-12` 두 Feature 완료 지시/계약 전달: 권장 경계가 명시적으로 승인됐다.
  Run247의 core/host 계약 뒤 Run248에서 제공물/scope/helper·앱 없는 관리·Quit/sleep/
  shutdown·업데이트/캐시 정리/손실 미확인 계약을 확정했다. 두 Feature/평가는 계약
  PASS이며 코드·기존 native 제외·사용자 실행·앱 설치는 그대로다. OP-08/09와 실제
  접근/화면/앱 product·물리/native 성능 수락을 완료로 승격하지 않았다.

- `2026-11-12` 실제 UI 계속 진행 지시: FEAT-0169/Spec0169/Run249를 승인한 공통 웹 작업 공간 increment로 개시했다. OP-08의 생성 폴더 그룹과 OP-09의 OSC133/painted focus attention을 먼저 고정하고 실제 UI를 구현한다. 앞선 contract-only 기록은 당시 사실로 보존하며 native/Rust/실제 OS 수락을 웹 증거로 승격하지 않는다.

- `2026-11-12` Run249 technical completion: the common web workspace passed Eval0165 with explicit platform limits. Retry identity, deleted default cwd, menu/input focus, actual rendered completion and delayed HTTP ordering were exercised. Human visual acceptance, native admission/bundling/Rust and actual OS/physical-input acceptance remain separate; this PRD stays approved rather than complete.

- `2026-11-13` disabled New/actual integration: [Run250/Eval0166](../evaluation/eval-0166-terminal-reopen-recovery.md)에서 이전 서비스 불일치 안내·명시적 업데이트·마지막 탭/분할 종료 후 재생성을 검증하고 현재 개발 서버에 반영했다. [Run251](../run/run-20261113-251-rust-terminal-runtime.md)의 Rust Terminal을 [Run252](../run/run-20261113-252-native-terminal-integration.md)의 앱에 통합했다. 최종 동봉319파일 검증과 실제 host7에서 오프라인 생성·HTTP/WS 인증·일반 Quit/앱 경로 제거/재실행 시 동일 실행 유지·명시 종료를 확인했다. Mac 잠금으로 필수 실제 창 닫기/Dock 재열기 수락은 blocked이며 FEAT0171은 approved 상태다. 물리 한글 IME·단축키/클립보드·VoiceOver·실제 sleep·최소 OS/수신자/성능은 미검증이다. [Eval0168](../evaluation/eval-0168-native-terminal-integration.md)은 Herdr 유사점·선택한 차이·OSC7501 미지원과 parser 확인 한계를 소유한다. 사용자 작업·설치 앱은 교체하지 않았다.

- `2026-11-13` 일상 조작 수정 승인: 사용자가 종료 화면 잔류·숨긴 작업의 현황 노출·제목 편집·기본 다이아몬드·탭 drag·개별 종료 확인·작업별 메뉴를 지적하고 기본 terminal 구색의 벤치마킹을 요청했다. [FEAT0172/Run253](../run/run-20261113-253-terminal-everyday-interactions.md)에서 기존 scoped manager API와 payload를 유지하며 공통 UI를 보완한다. 확정된 셸 종료는 코드와 관계없이 제거하고, 백그라운드는 실행을 유지한 별도 목록, 제목은 Sessions식 직접 편집, 순서는 같은 폴더의 private presentation preference로 정한다. 개별 종료는 바로 실행하고 bulk/service 범위 확인은 보존한다. 설치된 Herdr의 전체 동등성이나 타 제품의 보편적 기본값을 주장하지 않는다.

- `2026-11-13` 일상 조작·실제 창 전달: [Eval0169](../evaluation/eval-0169-terminal-everyday-interactions.md)의 공통 브라우저80·최종 앱319파일·실제 native-window10 검증을 통과했다. native 제목 표시줄의 잘못된 높이 selector로 하단이 잘리던 오류를 수정하고, 개발 HTTP 서버만 재시작해 기존4개 실행을 보존했다. 잠금 해제 후 실제 창 닫기/Dock 복귀·Quit/앱 제거/재실행 시 동일 실행·표시 순서가 확인돼 FEAT0171/0172 기술 수락은 passed다. 한글 IME 자동 검사는 일부 자모 중복/ASCII 입력으로 실패했으며 원인과 실제 물리 입력의 올바름은 미확정이다. 이 입력 관찰과 human visual·VoiceOver·실제 sleep·최소 OS·성능 수락은 남아 있으므로 전체 PRD는 approved를 유지한다.
