# Terminal Workspace Design Plan

## Metadata

- Status: `increment-complete`
- Parent boundary: [PRD-0030: macOS Terminal Work Area](../prd/prd-0030-macos-terminal-work-area.md)
- Related boundary: [PRD-0029: Rust Core And Responsive GUI](../prd/prd-0029-rust-core-and-responsive-gui.md)
- Created: `2026-11-12`
- Updated: `2026-11-13`
- Persistent-workspace baseline: [Run254/Eval0170](../evaluation/eval-0170-persistent-terminal-workspaces.md) passes the named persistent/mixed-folder workspace correction, compact density, one panel toggle and new-zsh integration: browser95, final319-file package and actual native12. Prior [Run253](../run/run-20261113-253-terminal-everyday-interactions.md) closes technical native-window integration. Native modal AX exposure, native IME, physical/VoiceOver/sleep and human visual acceptance remain unaccepted.
- Latest shared-header correction: [Run255/Eval0171](../evaluation/eval-0171-shared-compact-search-header.md) passes global menu density with121 browser/actual native12 checks. The Codex attached-folder list/primary control remains a proposal.
- Pane action correction: [Run256/Eval0172](../evaluation/eval-0172-terminal-action-hierarchy.md) passes pane-header splits, compact menus and a checked same-panel workspace move: browser118, packaged-host10, actual new native-window13 after owner unlock and final319-file integrity. Earlier IME/AX/physical/platform limits remain explicit.
- Status indicator correction: [Feature176](../feature/feat-0176-terminal-status-indicators.md) unifies icon scale and separates reported command state, current view, hidden work and completion attention. Final view/program separation passes130 browser/15 native checks, with physical limits retained in [Run257](../run/run-20261113-257-terminal-status-indicators.md).
- Prompt/program marks and inline Background: [Feature177](../feature/feat-0177-terminal-activity-and-background-rail.md), approved continuation in [Run258](../run/run-20261114-258-terminal-activity-and-background-rail.md), supersedes the all-open ● legend and hidden modal. Web143/Node78/build11 and packaged-backend10 pass with bundle integrity; the latest actual-window UI gate remains pending in [Eval0174](../evaluation/eval-0174-terminal-activity-and-background-rail.md). The user checkpoints implementation here; earlier native passes do not accept this later UI.
- Proposed execution profile: `fullstack-product`
- Surface lanes: `contract`, `backend`, `frontend`, `integration`, `infra`, `docs`; add `data` only for separately selected persistence

## Purpose

Terminal을 일반 읽기 페이지의 제목·버튼·카드 구조에서 터미널 작업에 집중하는
공간으로 조정한다. 사용자는 iTerm2처럼 상태를 작은 기호로 빠르게 파악하고,
Herdr의 왼쪽 작업 공간·작업 현황과 상단 탭·중앙 분할을 참고하고 숨긴 실행도
쉽게 회수하길 원한다. 후속 답변으로 하나의 macOS 앱 창에서 여러 탭을 사용하고,
Workstream/수집 Session과 별개인 그룹을 두는 방향을 선택했다. 최초 폴더별 그룹은
후속 사용자 요청으로 독립 이름·선택적 기본 폴더·여러 폴더의 탭/pane·빈 그룹
저장으로 변경됐다. Run254가 이 변경의 실행 경계다.
Sessions 등 다른 화면의 일반 앱 구조는 이 변경의 대상이 아니다.

이 계획은 구조·정보 계층·입력/상태 표현의 조정 순서와 검증을 소유한다.
제품 의미·승인·수명·상태 신호와 수락은 PRD-0030, 현재 법칙은 Design Constitution이
소유한다. 새 영구 디자인 체계나 구현 승인으로 취급하지 않는다.

## Plan Type

- Terminal 화면 family의 정보 계층/interaction 재구성.
- 탭·pane·숨긴 항목의 상태 표현 일관성.
- 기존 공통 shell과 Terminal 전용 공간 사이의 scoped design reconciliation.

## Planning Baseline Before Run249

| 출처 | 관찰/요구 | 한계 |
| --- | --- | --- |
| 사용자 제공 `main#main-content` DOM | 큰 Terminal 제목·설정/실행 중/새 터미널 행, 별도 탭 toolbar, empty panel, manager/service dialog 대신 터미널 편의 중심 배치를 요청 | 제공 DOM은 당시 empty/setup 상태이며 실제 geometry·동작의 rendered witness가 아님 |
| [현재 template](https://github.com/chochita0311/local-brain/blob/e6958df0813b8652074c68a73ac61a8b551e59a8/src/localbrain/templates/terminal.html), [CSS](https://github.com/chochita0311/local-brain/blob/e6958df0813b8652074c68a73ac61a8b551e59a8/src/localbrain/static/terminal.css), [frontend](https://github.com/chochita0311/local-brain/blob/e6958df0813b8652074c68a73ac61a8b551e59a8/src/localbrain/static/terminal.js) | page heading/버튼 행, 카드형 pane과 높이 상한, 탭 이름/×, 텍스트 실행/읽기 전용 상태 | 소스 관찰. 새로운 배치의 사용성·실측 화면/성능 평가를 하지 않음 |
| [manager](https://github.com/chochita0311/local-brain/blob/e6958df0813b8652074c68a73ac61a8b551e59a8/src/localbrain/terminal/manager.cjs), [Terminal policy](../../policies/project/terminal.md) | manager 소유 실행·memory-only 화면, `hidden`·lease·실행/종료·오류. `exitCode`는 셸/PTY 종료 값이며 직전 명령의 결과와 다름 | idle/busy·사용자 입력 필요·명령 완료 성공의 현재 구현 증거가 아님 |
| [iTerm2 tabs/appearance](https://iterm2.com/documentation-one-page.html), [Shell Integration](https://iterm2.com/documentation-shell-integration.html), [Session Status](https://iterm2.com/documentation-session-status.html), [Buried Sessions](https://iterm2.com/documentation-buried-sessions.html) | 미열람 출력·출력 활동·종료와 별도의 명령/보고 상태, 창에 없는 실행의 회수 | 기호의 보편 표준이나 iTerm2 실행 검증이 아님. 사용자 제시 원/마름모/체크의 정확한 기존 대응은 확인하지 못함 |
| [Herdr UI guide](https://github.com/herdrdev/herdr-app/blob/master/defaults/AGENTS.md), [README](https://github.com/herdrdev/herdr-app/blob/master/README.md), [기본 layout](https://github.com/herdrdev/herdr-app/blob/master/defaults/layouts/main.json)과 아래 audit의 mods | spaces → tabs → panes, 아래쪽 Agents 작업 현황과 별도 footer/status. 프로그램이 보고하는 상태와 core 실행의 분리 | 2026-11-12 공개 master 소스이며 설치 앱 실행/사용자가 본 버전·layout의 증거가 아님. 현재 shipped layouts는 settle로 탭을 숨기지 않음 |
| 창/그룹에 대한 사용자 후속 답변 | 실제 OS 다중 앱 창 제외, 하나의 창에서 `+` 탭 전환·탭별 여러 terminal. 폴더별 터미널 그룹은 Workstream/Session과 별개 | 방향 선택이며 그룹 ID·cwd 상속·삭제/수명·저장 세부 계약과 전체 PRD/구현 승인은 아님 |

공통 기준은 [Design Constitution](../../policies/design/design-constitution.md#terminal-workspace),
[Navigation](../../policies/project/navigation-and-history.md),
[Design Evaluation](../../policies/design/design-evaluation.md),
[Interaction Evaluation](../../policies/experience/interaction-evaluation.md)이다.
앞선 [웹 Eval0162](../evaluation/eval-0162-terminal-final-audit.md)는 현재 구현의
범위가 한정된 근거이며 새 화면·새 상태·패키지 앱 수락으로 승격하지 않는다.

## Scope

- Terminal 본문에서 일반 페이지 제목/동작 행을 걷어 내고 작업 공간을 우선하는 구성.
- 하나의 앱 창에서 왼쪽 위 이름 있는 작업공간, 위쪽 탭·추가·최대4분할,
  나머지 영역을 사용하는 terminal canvas. 그룹의 현재 계약은 PRD OP-08/FEAT-0173.
- 그룹/탭/pane의 cwd를 분리하고 빈 그룹을 보관한다. Terminal만 검색/행을 조밀하게
  조정하고 펼침/접힘 상태마다 한 개의 panel control을 둔다. 새 zsh의 명령 상태는
  사용자 rc 수정 없이 자동 보고하며 기존 셸에 주입하지 않는다.
- 왼쪽 아래 작업 현황과 숨긴 항목 회수, 작은 설정·운영 footer의 적용안 검토.
  아래쪽 현황의 정확한 배치·정렬·읽음은 제안이며 확인된 기존 동작으로 취급하지 않음.
- 탭/pane/작업 현황·숨긴 목록에서 같은 상태 의미·기호·색·접근 가능한 설명 사용.
- 활성/비활성·표시/숨김·최소화와 실제 작업 상태를 구별하고 상태를 실제 신호에 연결.
- 공통 웹 UI/코어와 실제 Tauri host에서의 입력·focus·viewport·수명 정합성.

## Non-Goals

- Sessions·문서·Settings 등 다른 화면의 재디자인 또는 전체 앱 shell의 자동 변경.
- Herdr core/테마·레이아웃 시스템·원격 기능·agent 자동화·새 에디터 도입.
- 기호를 추가하기 위해 출력 정지/셸 생존을 성공·대기·완료로 분류하는 휴리스틱.
- shell rc/agent 설정의 묵시적 수정, 명령/출력 이력 저장·색인, 모델로 상태 추론.
- 제품 Workstream/Project·수집 Session에 터미널 그룹을 자동 연결하거나 새 Source 등록.
- 사용자 범위에서 제외한 actual OS 다중 창, Dock badge·메뉴 막대 앱·OS 알림·전원 정책을 기본 범위로 추가.

## Invariants

- [PRD-0030의 선택된 수명](../prd/prd-0030-macos-terminal-work-area.md#app-independent-terminal-ownership--selected-lifetime-contract)을 유지한다.
  New는 표시, Hide/Open은 같은 실행, ×는 지정 범위 종료이며 앱 Quit/잠자기는 작업 종료가 아니다.
- 기존 D2Coding13px·로컬 font/OFL·IME/Unicode·input lease·흐름 제어/checkpoint·4 pane/32 record
  및 no replay·오류/미확인·범위 확인을 유지한다. 장식 때문에 터미널 입력을 가로채지 않는다.
- 제목/라벨의 상시 표시를 줄여도 main landmark·논리 제목·tab/pane 이름·tooltip·focus·
  상태/오류 announcement와 실제 종료/복구 접근을 보존한다. 색만으로 의미를 전달하지 않는다.
- 설치·font·연결 실패·종료 실패는 그 상태의 간결한 동작/설명으로 남기며 ‘글자 제거’로 삭제하지 않는다.
- 잠자기/최소화/비활성 창에서 미열람 출력·완료 상태를 자동으로 ‘사용자가 봄’으로 소거하지 않는다.

## Findings

| 관찰/변경 이유 | 조정 방향 | 보존/미결정 |
| --- | --- | --- |
| 현재 일반 page heading과 button row가 독립 작업 면적을 차지 | 상시 제목/큰 버튼 행을 제거하고 탭 바·작업 rail의 icon control로 이동 | 설치/오류/종료 확인과 의미 있는 접근 이름은 유지 |
| 현행 canvas는 `clamp(24rem, calc(100dvh - 16rem), 56rem)` 및 일반 page scroll 계약 | Terminal에 한정해 사용 가능한 높이와 자체 overflow를 우선하는 안 | 현재 token/scroll 법칙의 조정 후보. 다른 페이지/전역 token은 건드리지 않음 |
| 현재 manager는 관리 셸의 생존/종료를 제공하지만 명령 busy/idle/result는 제공하지 않음 | 상태 source/유효성 계약을 먼저 고정하고 기호를 연결 | 상태 신호 없이 ✓·◇를 확정 표시하지 않음 |
| 숨김/최소화/비활성/연결 손실을 한 ‘background’로 묶으면 의미가 달라짐 | view/attention·실행·입력권을 독립적으로 표현 | 실제 OS host 신호와 signal 없는 fallback 필요 |
| 폴더별 그룹과 한 창의 탭/분할은 사용자 답변으로 선택됨 | 그룹 세부 ID·cwd·삭제/수명·저장 계약을 선행 고정 | 실제 OS 다중 창 제외, Project/Workstream/Source와 자동 동일시하지 않음 |
| Herdr 아래쪽을 숨긴 목록으로 추정했으나 실제 기본 구성은 Agents | 작업 상태 모음과 숨긴 실행 회수를 구별해 제안 수정 | 모든 셸의 상태를 자동 검출한다고 주장하거나 Agents 이름/agent 자동화를 통째로 도입하지 않음 |

## Herdr Reference Audit

공식 공개 master의 기본 `main.json`과 연결된 UI mods를 확인했다. 이는 source-only
확인이며 설치 앱을 열거나 사용자가 본 layout/버전을 재현한 평가가 아니다.
아래의 Herdr 동작과 LocalBrain 적용 의견을 구별한다.

| 영역 | Herdr의 UI와 기능 | LocalBrain 적용 의견 / 경계 |
| --- | --- | --- |
| 왼쪽 위 Spaces | 머신/작업 폴더의 space, 그 안의 tabs/panes. 폴더/이름·branch와 선택·이동 진입. [Spaces source](https://github.com/herdrdev/herdr-app/blob/master/defaults/mods/spaces/main.js) | 사용자 확인대로 폴더별 terminal group을 사용. Herdr의 unnamed space 이름/cwd 자동 추종·Git worktree·machine 모델은 자동 채택하지 않음. 현재 Settings 기본 cwd와의 관계는 OP-08 |
| 왼쪽 아래 Agents | 여러 space의 **상태를 보고하는 agent**를 한 목록에 모음. 우선순위 또는 space별 정렬, 고정·접기/개수·해당 pane focus. 하위 작업을 접어서 보고 pane 없는 worker는 peek, 원하면 tab으로 유지. [Agents source](https://github.com/herdrdev/herdr-app/blob/master/defaults/mods/agents/main.js), [설명](https://github.com/herdrdev/herdr-app/blob/master/README.md#find-your-work) | `작업 현황`으로 실제 지원 신호를 가진 terminal 작업을 모아 기존 대상으로 이동하는 패턴 추천. 정확한 list/filter/pin·정렬 범위는 디자인/상태 계약으로 검토. agent 실행·하위 agent 자동화나 별도 peek viewer는 이번 참고만으로 추가하지 않음 |
| Agents 상태 | Working=회전, Blocked=Needs you/`!`, Idle=빈 원, Done=채운 점. 우선순위 blocked > done > working > idle. Done은 다른 곳을 보는 동안 완료됐으며 사용자가 보면 idle. 상태 보고가 없는 agent/이전 버전/tmux 안에서는 목록에 없을 수 있음 | LocalBrain의 최근 명령 결과·프롬프트·프로그램 보고·새 출력과 구별. 단순 셸 생존/출력 침묵을 agent 완료/대기로 분류하지 않음. 같은 그림 복사보다 출처·unknown·우선순위/읽음 계약이 선행 |
| sidebar 맨 아래 footer | Settings와 Add machine, 업데이트 준비 시 Settings 옆 점. 좁은 rail에서 icon/tooltip으로 줄임. [Chrome source](https://github.com/herdrdev/herdr-app/blob/master/defaults/mods/workspace-chrome/main.js) | 설정/운영·숨긴 터미널 회수의 작은 진입을 참고. 원격 machine 추가·OS 알림/업데이트 시스템 전체를 새 범위로 만들지 않음 |
| 상단 탭·중앙 | 현재 space의 탭 전환·`+` 새 작업 메뉴·분할 pane과 focus, 선택적 Files/Changes panel. [Tabs source](https://github.com/herdrdev/herdr-app/blob/master/defaults/mods/tabs/main.js), [기본 layout](https://github.com/herdrdev/herdr-app/blob/master/defaults/layouts/main.json) | 한 앱 창의 여러 탭/탭당 최대 4분할·compact 조작·큰 작업 면적을 채택 방향으로 사용. 파일/변경 에디터·임의 mod panel은 추가하지 않음 |
| 창 하단 가로 status | 현재 장비 또는 This computer, branch가 있으면 표시, agent 수·needs-you 수, 실제 설정된 command palette 키. [Status source](https://github.com/herdrdev/herdr-app/blob/master/defaults/mods/workspace-status/main.js) | 연결·작업 위치·입력권/주의 정보의 간결한 문맥 표시를 검토. Git/remote 정보나 새 command palette를 필수 구현 조건으로 추가하지 않음 |
| 숨김/keep | `tab.settle`은 화면별로 치워도 실행을 유지하지만 현재 shipped layouts는 사용하지 않고 모든 탭을 나열. `terminal.park`는 pane 제거와 keep 해제. keep은 reboot/core crash 뒤 새 셸을 만들 수 있음. [계약](https://github.com/herdrdev/herdr-app/blob/master/defaults/AGENTS.md) | **Agents는 숨긴 터미널 목록이 아님.** LocalBrain Hide/Open은 같은 실행의 표시만 바꾸며 ×는 지정 범위 종료. 재부팅 프로세스/화면 복원·명령 replay·새 셸 자동 생성은 채택하지 않음 |

따라서 아래쪽을 ‘숨긴 항목만 있는 곳’으로 고정한 앞선 가정을 정정한다. 추천은
위쪽 폴더 그룹, 아래쪽 그룹을 가로지르는 작업 현황, 별도의 숨긴 실행 회수와
설정/운영 진입이다. 현황 목록에서 숨긴 작업을 선택하면 기존 탭을 다시 열고
같은 pane으로 이동하며, 숨김 자체를 실행/완료/확인 필요 상태로 취급하지 않는다.

## Proposed Composition

다음은 Run249 이전 단일 앱 창·폴더별 그룹 방향 안의 구조 검토안이다. 당시 그룹 세부 모델과
아래쪽 현황·footer/status의 정확한 배치는 미확정이다.
예제 이름은 합성이며 기호의 제품 의미는 PRD의 상태 source 표를 따른다.

```text
기존 앱 탐색 │ Terminal 전용 작업 rail │ [◇ shell] [⟳ tests] [✓ build] [+] [분할] [⋯]
            │ 위: 작업 공간/폴더       ├──────────────────┬───────────────────┤
            │    demo-a               │                  │                   │
            │    demo-b               │     pane 1       │      pane 2       │
            │                         │                  │                   │
            │ 아래: 작업 현황          ├──────────────────┴───────────────────┤
            │       확인 필요/진행/완료 │ 필요할 때만 경로/연결/입력권/오류     │
            │ footer: 숨긴 항목·설정   │                                       │
```

글로벌 탐색은 기존 접기/복귀 경로를 보존한다. 두 개의 넓은 sidebar를 필수로 늘리지
않도록 Terminal rail 폭/접기/좁은 폭 변환을 검토하며, Terminal 진입만으로 전역
설정·다른 화면의 sidebar 상태를 바꾸지 않는다. pane별 메뉴·×는 대상과 focus를
알 수 있게 작게 유지한다. `main#main-content`와 논리 제목을 삭제하는 안은 아니다.

## Planned Work

아래 batch는 승인 후 경계를 나눌 순서이며 구현 task/Feature 승인이 아니다.

### Batch 1: 상태 신호와 작업 공간 경계

- Goal: 명령·프로세스·출력 활동·attention·view 상태의 source/권한·유효성 및 OP-08의 그룹 세부 계약을 고정한다.
- Why this grouping: 표시 모양보다 상태의 의미와 group/window 소유권이 먼저 정해져야 한다.
- Guardrails: signal 부재=unknown, raw output 보관/의미 추측·사용자 설정 자동 수정·새 기능 몰래 활성화 금지.
- Targets: PRD 상태 표와 OP-08/09, terminal 상태 producer/consumer 계약, 폴더 그룹과 단일 창의 view 경계.
- Validation: 신호 있음/없음·늦음·단절·재연결·새 generation과 조용한 장기 명령/실패/대기 반례를 구분할 수 있는 계약.
- Exit gate: foundation 결과가 구체적이며 사용자 scope·shell integration 방법의 중대 미결정이 downstream에 남지 않음.

### Batch 2: Terminal 전용 frame과 조작 계층

- Goal: 위 제안의 rail/tabs/canvas로 현재 제목/큰 action·카드 chrome를 대체하는 화면 경계를 만든다.
- Why this grouping: 높이·overflow·toolbar·접근성·scope가 같은 화면의 사용 면적과 입력 경로를 함께 결정한다.
- Guardrails: 공통 토큰/다른 화면 불변, 폰트/IME/lease·설치/오류 복구·기존 종료 의미와 전체 수명 보존.
- Targets: Terminal template/CSS/route controller·공통 app-main 경계, Settings/운영의 문맥별 진입.
- Validation: 실제 wide/narrow/320px, 0/1/2/4 pane·긴 탭/경로·overflow·setup/font/network failure·키보드 흐름.
- Exit gate: 상시 일반 페이지 chrome 없이 필수 조작/오류 회복이 가능하고 Terminal 특례가 다른 화면에 전파되지 않음.

### Batch 3: 기호·attention·숨긴 항목의 일관성

- Goal: Batch1의 실제 상태를 탭/pane/rail에서 짧은 기호와 선택 표현으로 연결한다.
- Why this grouping: 같은 실행이 보이는 위치·view 상태에 따라 다른 완료/대기로 보이면 일관성이 깨진다.
- Guardrails: 기호만/색만의 모호함, 무근거 idle/success·상시 animation·출력마다 전체 UI 갱신·앱 재실행 시 명령 replay 금지.
- Targets: 탭/pane 상태·작업 현황/숨긴 목록·기존 대상 이동·tooltip/accessible name, 미열람 출력·완료의 보존/해제와 focus/minimize 처리.
- Validation: 알려진 결과·unknown/old source, 출력 없는 명령·prompt·TUI·명령 실패/취소·숨김/최소화 중 새 상태와 복귀.
- Exit gate: 제안 glyph의 뜻/근거/우선순위·사라지는 조건이 일치하며 observer·느린 연결·새 실행이 이전 상태를 잘못 소비하지 않음.

### Batch 4: 실제 웹·앱과 보존 consumer

- Goal: 선택한 코어/제공물에서 Terminal 편의성과 기존 수명·다른 화면을 함께 수락한다.
- Why this grouping: 웹 DOM·독립 WebKit·실제 패키지 앱과 OS 창 상태의 근거가 서로 다르다.
- Guardrails: 실제 앱/OS 입력·최소화·Quit/sleep와 단순 browser fixture 결과를 합치지 않음. 지원하지 않은 창/장비 범위는 미검증.
- Targets: 실제 개발용 웹·빌드 앱, 상태 source setup/해제·종료/교체, 대표 Sessions/문서/Settings 소비자.
- Validation: contract·design·functional·interaction와 cold/warm·hidden/flood/reconnect·전체 자원/입력 응답의 승인 예산.
- Exit gate: 각 증거의 build/asset/backend/host와 한계가 명확하고 feature 수락·사람의 사용 검토가 기존 owner에서 완료됨.

## Validation Gates

- PRD와 Feature 경계 승인 전에는 이 계획만으로 코드·product evaluation을 시작하지 않는다.
- UI 의미는 [PRD 수락 조건](../prd/prd-0030-macos-terminal-work-area.md#acceptance-envelope)을 사용하며 새 숫자·완료 의미를 plan이 따로 만들지 않는다.
- actual state source와 표시/해제 조건의 양방향 mapping을 검토한다. 특히 output silence≠prompt,
  live shell≠명령 busy, shell exit code≠직전 명령 결과, last success≠현재 작업/agent 완료를 확인한다.
- geometry·가독성·color/focus·IME와 context action은 rendered/실제 host 증거를 사용한다.
  시각 비교는 현재/제안 artifact와 합성 상태를 나란히 보고 수행 범위를 남긴다.
- 성능은 idle CPU·update 빈도·input-to-paint·total subtree cost 및 hidden/flood 동안 제어를 포함한다.
  signal 감지를 위한 과도한 process polling이나 무한 spinner를 새 기본 부하로 만들지 않는다.

## Risks / Open Questions

- OP-07은 결정됨: 한 macOS 앱 창·여러 탭·탭당 최대 4분할. OS 다중 창은 제외한다.
- OP-08의 첫 구현은 탭의 canonical 생성 폴더를 key로 묶고 New=root+설정 shell,
  Split=누른 pane cwd/shell로 고정했다. `cd`는 그룹을 옮기지 않는다. 남은 탭이 없으면
  그룹도 제거하고 빈 구조를 저장하지 않는다. Run253은 탭 이름 직접 편집과 같은
  폴더 안의 표시 순서를 추가한다. 순서는 manager generation에 묶인 private host
  preference이며 독립 영속 폴더 구조나 실행 상태를 만들지 않는다.
- OP-09의 첫 구현은 기존 OSC133 명령 신호, unknown fallback과 generation별
  completion attention이다. rc를 수정하지 않으며 프로그램 waiting/done·출력 읽음은
  추정하지 않는다. native 최소화/실제 window focus/물리 입력은 별도 증거가 필요하다.
- 아래 현황은 모든 그룹의 보이는 탭에 속한 terminal을 오류/새 완료/작업 중/기타 순으로 모으고 정확한
  pane으로 이동한다. 백그라운드 탭은 별도 footer 목록에서 회수·종료한다.
  필터/고정/agent 자동화는 추가하지 않는다. Herdr의 보고 agent만
  나오는 목록과 범용 셸 상태를 혼동하지 않는다.
- 사용자의 실제 전용 frame 구현 지시에 따라 Terminal 한정 viewport/rail/scroll 특례를
  [Constitution](../../policies/design/design-constitution.md#terminal-workspace)에 반영했다.
  다른 화면의 문서 스크롤이나 전역 탐색 접기 상태를 바꾸지 않는다.
- 단일 앱 창에서도 OS minimize/focus·client별 읽음·입력권·창 닫기/Quit 수명은
  실제 host에서 확인하며 기존 4 pane/32 record와 독립 manager 수명을 완화하지 않는다.

## Exit Goal

터미널 작업·상태·회수/종료를 compact rail/tabs/panes로 다루고 실제 근거를 가진
기호를 빠르게 읽을 수 있다. 일반 페이지 chrome는 줄고 필수 복구·접근성·수명은
유지된다. 새 layout과 근거/미검증이 승인된 Feature/Run/Evaluation으로 추적된다.

## Handoff To Next Track

진행 지시를 반영해 [Rust 공통 코어 계약 FEAT-0167](../feature/feat-0167-rust-core-and-host-contract.md)과
[독립 runtime 계약 FEAT-0168](../feature/feat-0168-app-independent-terminal-runtime-contract.md)을
완료했다. 각각 Spec0167/0168, Run247/248와 Eval0163/0164에서 계약 PASS를 받았다.
소유자는 [core/host 계약](../project/rust-core-and-host-contract.md)과
[독립 runtime 계약](../project/app-independent-terminal-runtime-contract.md)이다.
상태/그룹/frame product를 이 계약 Feature에 합치지 않았으며 실제 구현은 별도다.

최신 명시적 UI 계속 진행 지시를 [FEAT-0169](../feature/feat-0169-terminal-workspace.md),
[SPEC-0169](../spec/spec-0169-terminal-workspace.md), [Run249](../run/run-20261112-249-terminal-workspace.md)로
구체화했다. group/status contract lane을 먼저 고정하고 backend→frontend→integration 순으로
공통 웹 frame과 실제 terminal 흐름을 구현한다. 해당 범위의 Constitution·Terminal policy·
양언어 앱 가이드를 함께 갱신한다. 앞의 batch 구분은 초기 검토 순서이며 actual web 구현은
이 Run이 소유한다. Native admission/bundle/Rust와 실제 OS 수락은 다음 전달 경계에 남는다.
사용자 shell 설정이나 실행 중인 실제 manager는 변경하지 않는다.

## Run249 Web Delivery Receipt

[Eval0165](../evaluation/eval-0165-terminal-workspace.md) records contract/design/functional/interaction PASS WITH LIMITS:47 browser,73 Node,1651 Python with33 optional PTY cases separately covered by the67-test/33-real-PTY run. Initial/ready/fault/recovery, wide/920/700/320 layouts, long tabs, groups/four panes, hidden recovery, exact stop and generation reset are verified. The original Herdr audit is structural reference, not pixel matching or installed-app evidence. Native admission/bundling/Rust, physical IME/VoiceOver, actual OS focus/sleep, long-duration performance and human visual acceptance remain separate. No new common design/harness promotion candidate arose.

## Rust And Native Implementation Receipt

[Run250/Eval0166](../evaluation/eval-0166-terminal-reopen-recovery.md) fixes the
disabled-New/version recovery and adds repeated last-close/recreate coverage.
[Run251/Eval0167](../evaluation/eval-0167-rust-terminal-runtime.md) delivers the
shared Rust Terminal control/helper while retaining this HTML/CSS/xterm design.
[Run252/Eval0168](../evaluation/eval-0168-native-terminal-integration.md) delivers
the self-contained app package, authenticated native access and actual Quit/
source-app removal/relaunch retention checks. Final shared-browser54, Node73 and
real Rust/PTY14 pass; scoped native-host7 and319-file artifact checks also pass.
The prior Run249 receipt remains historical, not a claim that those checks ran then.

At the preceding delivery, actual native window close/reopen and physical input
were not accepted: the Mac was locked, so Run252 was blocked while the implementation and
non-UI checks are delivered. Eval0168 owns the detailed Herdr comparison, including
intentional cwd/hide/restart differences and absent OSC7501 compatibility. Human
visual review, physical IME/VoiceOver/sleep and performance remain separate.

## Everyday Interaction Delivery

[Run253/Eval0169](../evaluation/eval-0169-terminal-everyday-interactions.md) delivers
confirmed shell-exit retirement, separate background recovery, Sessions-style
inline title edits, folder-scoped pointer/keyboard/menu order, direct individual
End and per-task menus. The unexplained default diamond becomes a neutral terminal
icon without inventing prompt/success. Existing shell/status/scope contracts stay.

Final shared browser80 and actual native-window10 pass. A native screenshot found
footer/statusbar clipping caused by a wrong titlebar selector; the final app and
geometry witness confirm the repair. This closes the former window block and
passes the technical integration/UI increment, with the same runtime payload and
live user jobs. Native IME automation did not pass: ordinary non-composing jamo or
ASCII appeared in several probes. That unresolved input observation and physical/
human visual/VoiceOver/sleep/minimum-OS/performance readiness remain separate.

## Codex Project Reference — 2026-11-13

The supplied project-edit screenshot, installed Codex26.1106.51428 renderer/
Electron package and [official local-project guide](https://learn.chatgpt.com/docs/projects#use-local-projects-for-folders-and-codebases)
support a named project with multiple attached folders and a primary folder.
This is a static package/UI/documentation comparison; no user project, permission
or conversation was changed and backend removal behavior was not exercised.

- Project identity/name and the ordered `rootPaths` list are separate. The editor
  adds multiple folders, removes a folder from its draft and makes a selected
  folder primary by moving it to the first position. The Primary badge is shown
  only when multiple folders exist. Its picker supports multiple selection.
- The primary folder starts new chats and supplies default Git operations and
  automatic `AGENTS.md`, skills and `config.toml` discovery. Secondary folders
  remain available for file search/read/edit without automatic discovery of
  those project files. Remote projects currently support one folder. These are
  agent-context rules; the sandbox still owns actual command permissions.
- The review pane can select among attached repositories; Last turn aggregates
  them, while PR/worktree actions target the primary repository. See the
  [official review guide](https://learn.chatgpt.com/docs/code-review#review-multiple-repositories).
  Project-removal UI explicitly distinguishes removing app metadata from deleting
  files/chats; this comparison did not execute removal.

Current LocalBrain supports independent named groups, one optional default cwd
and different-folder tabs/panes, but has no registered folder list or primary
switcher. A suitable follow-up is a named Terminal workspace with attached folders
and one default folder, selectable on New/explicit Split. Normal Split still
inherits its pane; `cd` changes only actual cwd. Folder-list edits must not restart
jobs, delete directories, register Sources or imply an AI permission boundary.
This remains a proposed schema/UI extension, not an implemented Feature173 capability.

The user's shared-header correction is separate:
[FEAT0174](../feature/feat-0174-shared-compact-search-header.md) promotes compact
search/header density to every sidebar destination, including both Sessions
screens. Group/task row changes remain scoped to Terminal.


## Pane Action Hierarchy — 2026-11-13

The user's next correction approves [Feature175](../feature/feat-0175-terminal-action-hierarchy.md):
a tab groups terminals, its + creates a tab, and right/down split actions belong
to each pane header with that pane as their source. The pane menu retains the
explicit different-folder action. This supersedes the toolbar split placement
in the earlier proposed composition without changing four-pane layout or process
lifetime. Terminal action rows use shared label type/compact padding for32px
(desktop),40px (narrow). Their former37.6875px height was an implementation drift.
Workspace movement uses one menu panel with checked membership, back, bounded
scrolling and keyboard/dismissal behavior; Settings keeps its existing chooser.
This is independent of the proposed attached-folder registry above.

## iTerm2 Dock Reference — 2026-11-13

The user explicitly points to the installed iTerm2 Dock menu and the distinctions
between work running, resting, hidden and currently viewed. Local3.7.6 inspection
shows bullet/check/diamond marks, with minimized-window flags matching diamonds.
The pinned official [3.7.6 window-controller source](https://github.com/gnachman/iTerm2/blob/7ce456b98db38d3f0bafd70ffec87752e69d5d58/sources/TerminalView/PseudoTerminal.m#L16237)
sets document-edited when a current-tab session has a nontrivial job, excluding
custom-command/SSH profiles; the setting can disable this indicator. AppKit
[updates window-menu edited status](https://developer.apple.com/documentation/appkit/nsapplication/updatewindowsitem(_:)).
A current/minimized mark may visually take precedence over that job marker.
This source/observation comparison is bounded; inactive-app AX main flags and
partly unmatched titles do not independently prove every menu transition.
No raw local title, screenshot or runtime content is placed in tracked docs.

The same Dock rows show two independent values: a window mark in
`AXMenuItemMarkChar` and, in several program titles, a leading braille character.
One checked row also has a braille prefix; bullets occur both with and without
that prefix. Therefore shell/process state cannot replace program activity.
The user's LocalBrain legend is explicit: ✓ current, small filled ● other open
foreground, outlined ◇ hidden/background. This borrows recognizable view cues
without claiming AppKit's edited-job bullet has exactly that product meaning.

Implement that legend independently of shell integration. Separately pass through
the program's reported leading braille title glyph, preserving tab aliases and
in-place frame updates/removal. A group prefers its focused reporting pane,
otherwise the first reporting pane. Shell command descriptions and relevant
result/fault badges remain separate. No inference of agent thinking/waiting from
process liveness, shell running, text or silence. Actual painted input focus
acknowledges completion; inactive selection retains IDs with neutral borders.
The earlier question-mark and neutral-circle proposals were interpretation
errors and are superseded, with their source/results retained as history.

Status updates keep tab buttons and their12rem title-control width stable: a
recorded synthetic pointer sequence showed that clearing a completion badge
could otherwise move × between coordinate lookup and mousedown. Keep ellipsis
inside that fixed title width. The simple unfilled rhombus is geometric; the
shared Material `diamond` gem artwork is not the requested hollow view mark.


## Prompt Marks And Inline Background — 2026-11-14

The user observes that ordinary iTerm prompts do not receive the same filled
mark as a running program, and that a diamond confined to a modal is rarely
visible. Their explicit continuation approves Feature177: same-diameter prompt
◦ / program ● for reported nonselected items, ✓/◇ precedence and independent
program-title braille. Unknown reports stay neutral. A grouped tab uses any
running versus all confirmed prompts, preserving missing-state meaning.

Background becomes a compact expandable rail-footer list. Hidden tabs leave the
strip/task list while their names, workspace/count context, ◇, reported program
and result indications, name-to-restore and whole-tab × stay discoverable inline.
Initial retained work and explicit Hide reveal it; manual collapse survives
polling. Bound scrolling, footer utilities, row focus, narrow restore and exact
process/closure scopes remain acceptance checks. Existing references and earlier
passes retain their historic scope; this correction requires fresh verification.
