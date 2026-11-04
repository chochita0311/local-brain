# Initial State And Transition Audit Plan

## Metadata

- Status: `active` — 1차 조사와 후속 `리뷰대로 정리` 요청의 F1–F6 수정을 완료했다.
  [Audit results](initial-state-and-transition-audit-results.md)가 발견·수정·실제 coverage·잔여 검증을 소유한다.
  전체 native/positive·active 상태 acceptance는 미완료다.
- Created: `2026-11-01`; Updated: `2026-11-02`
- Plan type: 초기 상태·시각적 전환·상호작용 일관성 검토
- Evaluation profile: `frontend-product` — 조사와 범위 한정 수정에 적용.
- Planned surface lane: 공통 UI(`templates/`, `static/`, `desktop/ui/`)에서 설정·첫 실행
  → 핵심 화면 → 개발 웹 순서로 평가. native host(`desktop/src-tauri/`)의 실제 구동 증거는
  별도 수집하고 design·functional·UX 평가에 연결한다. 실행 Run은 아직 선택하지 않았다.
- Owner request: 설정을 열 때 보이는 깜빡임을 확인하고, 개발 중 앱·웹의
  로딩·스켈레톤·값 없음·화면 전환을 반복 검증할 종합 계획을 만든다.
- Authorization: 최초 계획 → `진행` 요청의 조사·기록 → `리뷰대로 정리` 요청의 F1–F6 수정,
  관련 계약·회귀 검사·개발 검증 절차 정리 순서다. PRD/Feature 승인 상태와 배포물은 변경하지 않는다.

## Purpose

화면이 완성된 뒤에는 정상으로 보여도, 진입 직후 빈 선택값·임시 안내·잘못된
빈 상태가 잠깐 나타나거나 본문이 움직일 수 있다. 이 계획은 **첫 표시부터
사용 가능한 상태까지의 과정**을 평가 대상으로 삼는다. 설정 진입을 첫 재현
사례로 사용하고, 같은 문제를 만드는 공통 소유자와 다른 화면을 순서대로 조사한다.

화면마다 스켈레톤을 추가하는 것이 목표는 아니다. 서버가 완성한 HTML,
클라이언트 초기화 전 표시, 의도된 로딩, 실제 데이터 없음, 필터 결과 없음,
읽기 실패를 구별하고 각각의 전환이 자연스럽고 사실에 맞는지 확인한다.

## Baseline

### Existing Evaluation Coverage

기존 규칙에 flickering 검토가 이미 있다. 새 규범을 중복 작성하기보다 다음
규칙을 재현 가능한 시나리오와 시간 순서의 증거로 연결한다.
아래의 shell은 상단·사이드바 등 화면이 바뀌어도 유지되는 공통 영역을 뜻한다.

| 기존 소유자 | 이미 요구하는 것 | 이 계획에서 구체화할 검사 |
| --- | --- | --- |
| [Design Constitution: 상태](../../policies/design/design-constitution.md#derived-and-transient-ui-states), [로딩](../../policies/design/design-constitution.md#empty-loading-error-and-working-states), [접근성](../../policies/design/design-constitution.md#12-accessibility-and-interaction-rules) | 로딩은 소유 영역 안의 muted skeleton 또는 progress, 스켈레톤은 최종 형태와 유사하고 reduced motion에서 pulse하지 않음. 작업 중은 명시적 상태이며 공유 motion token으로 애니메이션 가능; reduced motion에서는 정적 표시·즉시 전환. 빈 상태는 중립적·간결한 설명과 한 가지 관련 회복 경로(주동작 최대 1개), 오류는 입력·가능한 회복 경로 보존. 공통 shell은 안정적이며 평상시 전환에 빈 화면·구현 중간 상태가 번쩍이지 않음 | 정상·지연·실패에서 표시의 의미와 영역, 모션 축소, 본문과 shell 좌표를 함께 확인 |
| [Design Evaluation: shell handoff](../../policies/design/design-evaluation.md#shell-handoff-visual-continuity) | outgoing → mid-handoff → incoming → settled를 따로 관찰. 상단·사이드바·action/search 공간이 의도 없이 움직이거나 사라지지 않음. 숨기는 컨트롤의 공간은 보존하거나 의도적으로 전환 | 최종 화면 캡처에 더해 초기·중간 프레임과 지속 영역의 위치 비교 |
| [Design Evaluation: first state](../../policies/design/design-evaluation.md#first-state-surface-separation), [Interaction Evaluation: first state](../../policies/experience/interaction-evaluation.md#first-state-isolation-and-handoff) | handoff 전까지 첫 진입 화면이 주 화면으로 읽힘. 뒤 화면을 mounted 상태로 둘 수 있지만 시각적으로 경쟁하거나 상호작용을 빼앗지 않음. 비활성 화면의 포인터·키보드·접근성 접근 차단을 `inert`/focus/ARIA 등으로 확인하며 시각적 overlay만으로는 충분하지 않음. 경로 해석·첫 화면 해제·목적지 표시가 일관되고 전환 중 첫 화면이 재등장하지 않음 | 초기·중간·handoff, 첫 설치·기존 설치, 직접 URL·shell 이동, 넓고 좁은 화면에서 실제 활성 영역 확인 |
| [Interaction Evaluation: stability](../../policies/experience/interaction-evaluation.md#interaction-stability), [staged timing](../../policies/experience/interaction-evaluation.md#staged-handoff-timing) | 불필요한 깜빡임을 피할 만큼 목적지가 준비되면 전환하고, flicker·placeholder-only 상태·내부 경로·로딩 골격·임시 문구의 불필요한 노출을 피함. 먼저 비우기보다 atomic swap·캐시·prefetch를 우선 검토. outgoing/incoming/shell 타이밍과 목적지 컨트롤 등장 순서, early/middle/late 프레임을 확인. warming을 사용한다면 cold·완료 전 클릭·warm 재방문과 지연/실패 asset을 비교하며 warming은 이동의 필수 조건이 아님 | 실제 클릭 경로와 준비 완료 조건을 기록하고, 빠른 로컬 응답에서도 중간 상태가 노출되는지 확인 |
| [Interaction Evaluation: disclosure readiness](../../policies/experience/interaction-evaluation.md#data-ready-disclosure-gate) | hover/focus CSS가 데이터를 받기 전에 async menu의 placeholder·loading copy·내부 skeleton을 열지 않도록 readiness를 명시. 승인된 의도적 loading menu가 아니라면 pending 동안 닫힘. 지연·실패 fetch와 최종 unavailable 표시가 의도된 영역 안에 있는지 확인 | 초기 로딩뿐 아니라 준비 전 메뉴 진입도 검사 |

[Rendered evidence](../../policies/design/design-evaluation.md#rendered-state-and-viewport-evidence)와
[공통 소유자 검증](../../policies/design/design-evaluation.md#shared-owner-and-propagation-evidence)은
정확한 route·영역·scroll owner, 실제 viewport, 합성 콘텐츠, 미관측 범위의 명시를
요구한다. 최종 스크린샷이나 소스 검사만으로 순간 전환을 통과 처리하지 않는다.

### Implementation And Existing Work

다음은 `2026-11-01` 조사 시작 당시의 소스·검증 체계다. 후속 변경은 결과 문서의
[Repair Contract](initial-state-and-transition-audit-results.md#repair-contract--2026-11-02)와 수정 검증을 따른다.

- [아키텍처](../../policies/project/architecture.md)는 Jinja2 서버 렌더링과 작은
  JSON 상호작용을 사용한다. 조회한 자체 관리 template/static 소스에서 공통
  `skeleton` 구현은 찾지 못했다. 이름 검색만으로 모든 중간 표시가 없다고 판단하지 않는다.
- [설정 코드](../../../src/localbrain/static/settings.js)의 `open()`은
  `showModal()` → category 선택 → 로딩 안내 → `load()` 순서다. `load()`는 진행 중인
  일반 설정 저장을 기다린 뒤 `/api/settings`를 읽고 값과 목록을 렌더링한다.
  [로딩 안내](../../../src/localbrain/templates/_settings.html)는 본문 위에 있으며,
  [CSS](../../../src/localbrain/static/settings.css)는 비어 있으면 숨긴다.
- [기존 UI contract tests](../../../tests/test_ui_contract.py)는 설정의 구조·저장·복구·
  크기·스크롤 계약 등을 검사하지만, 브라우저의 순간 paint를 입증하지 않는다.
  [기존 native 설정 평가](../evaluation/eval-0139-design-standalone-test-app.md)는
  여러 개별 전달 범위의 증거다. 이를 전체 설정 진입 프레임의 통과로 확대하지 않는다.
- [Browser QA scripts](../../../scripts/qa-workflow-map-browser.mjs) 등은 특정 기능의
  CDP 검증 패턴을 제공한다. [package scripts](../../../package.json)에는 앱 전체의
  초기/전환 상태를 검사하는 공통 명령이 없다.
- [Quality backlog](../project/backlog.md#p2---quality-and-distribution)에
  `1440/920/700/320` 합성 graphical state matrix와 접근성 검토가 미완료로 남아 있다.
  이 계획은 그 작업의 초기 상태·시간 순서 검증을 구체화한다.
- 현재 [다른 design tracks](../README.md)는 학습·Atlassian·workflow 등의 개별 범위다.
  이 문서는 공통 초기/전환 검토를 소유하며 그 트랙의 승인·중단 상태를 바꾸지 않는다.

### Preliminary Runtime Observation — 2026-11-01

소스 기준 `b844ce8`, Chrome `156`, 실제 CSS viewport `1440×875`, DPR `2`에서
개인 데이터와 분리한 일회성 web backend의 `/sessions`를 관찰했다.
합성 설정은 `startup_screen=context`, `timezone=UTC`, onboarding 완료,
등록 소스 없음·동기화 꺼짐·모델 없음이다. 개인 프로필 후보 탐색은 fixture에서
빈 목록으로 대체했고, 제품의 설정 JS/CSS/template은 그대로 사용했다.
rAF는 브라우저의 `requestAnimationFrame`으로, 다음 그리기 전의 렌더링 상태를 표본으로 읽었다.

| 관찰 | 확인한 결과 | 증거의 한계 |
| --- | --- | --- |
| 브라우저 자동화의 실제 pointer click으로 첫 설정 열기, 지연 주입 없음 | 클릭 기준 첫 rAF 표본 약 `6.5ms`: 로딩 안내, 비활성 dropdown 두 개의 표시값이 빈 문자열, 일반 heading Y=`299.6484`. 약 `22.6ms`: 안내 제거, `Local Context`/`UTC`, 활성화, heading Y=`223.5`. 본문 약 `76.15px` 상승 | rAF 표본 시각은 정확한 compositor paint 시각이나 사용자가 인지한 지속 시간이 아님 |
| 저장값을 이미 읽은 뒤 script click으로 재열기 5회, 지연 주입 없음 | 4회에서 같은 로딩 안내와 약 `76.15px` 이동이 rAF에 잡힘. 나머지 1회는 완료 상태만 표본에 잡힘. 캐시된 표시값이 있어도 안내 영역은 재등장 가능 | 1회 미포착은 결함 부재의 증거가 아님. 반복 입력은 물리적 사용자 입력이 아님 |
| `/api/settings`를 브라우저에서 일시 보류한 재열기 후 해제 | 보류 중/해제 후 화면을 직접 렌더링 캡처로 비교. 안내 영역이 본문을 밀었다가 사라지는 관계와 dropdown 비활성→활성 확인 | 보류는 모양을 확인하기 위한 통제 조건이며 실제 지연 시간의 측정치가 아님 |

따라서 **조사 당시 소스의 web 설정에는 깜빡임으로 느낄 수 있는 짧은 빈 값과 본문
이동이 실제로 있다.** 관측한 이동은 안내 영역의 삽입/제거와 일치한다.
dialog 자체는 두 상태 모두 `720×560`, 동일 위치를 유지했다.
이 확인이 창 전체의 백색 flash, 설치된 Tauri 앱의 동일 원인, 다른 화면의 정상 여부,
결함 도입 시점까지 입증하지는 않는다. 해당 브라우저 관찰 중 console error/warning은 없었다.

## Scope And Non-Goals

검토 대상은 현재 제공되는 앱·개발 웹의 화면이다. 먼저 shared shell과 설정·첫 실행,
Sessions/Projects/List/Chart, Session/Subsession 읽기, Sessions Dashboard,
Local Context/문서 preview, keyword/AI 검색, Docs를 조사한다. 그 다음 개발 웹에
노출되는 Dashboard/학습 reader, Workstreams/Thread/Suggestion, Sources, Atlassian,
Schema, Run/Insights, Auto Work 및 연결된 기존 workflow 읽기 화면까지 목록화한다.
전체 route 목록은 [application assembly](../../../src/localbrain/app/routes.py),
[Settings](../../../src/localbrain/app/settings.py), Docs/learning route 등록과 실제
navigation을 대조해 확정한다. 목록·링크로 빠진 화면이 없도록 하되 유사 route는
공통 패턴 대표와 고유 상태로 묶고 제외 이유를 기록한다.

현재 기본 앱·웹에서 중단된 Context Search와 Google Drive는
[feature availability](../project/feature-availability.md)를 따른다. 기존 모델·연결이
있어도 category/route/job이 다시 나타나지 않는 경계만 확인하고 활성화하지 않는다.
workflow 검토도 기존 읽기/표시 증거에 한정하며 중단된 계산·추출 트랙을 재개하지 않는다.

1차 조사에는 제품 수정, 공통 skeleton framework 도입, 모션/토큰 재설계, 모델 다운로드,
실제 소스 수집·외부 읽기/쓰기·추론, 앱 rebuild/교체/배포를 실행하지 않는다.
당시 QA 도구와 정책 보완은 제안이었다. 후속 수정에서는 F1–F6과 그 회귀 도구·소유 계약만
보완했다. 반복 명령은 아래 절에 명시하며 공통 skeleton framework·모션 재설계는 도입하지 않았다.

## Invariants

- [설정 계약](../../policies/project/desktop-app-and-settings.md)을 유지한다. 일반 설정의
  autosave는 조용히 완료되고 강제 reload하지 않는다. 닫아도 저장은 계속되며 재열기는
  진행 중 저장을 기다린다. source form은 명시적 Save, category 이탈/재클릭은 해당
  미저장 editor를 버리고, wizard Back은 draft를 보존하며 Skip은 등록하지 않는다.
- 보통 web 진입에 onboarding을 강제하지 않는다. 명시적 `/onboarding`은 두 edition에서
  동작하며 native 첫 실행은 실제 saved startup surface 위에서 열린다. 배경은 초기
  markup부터 inert, 전환 중 두 panel은 격리, 완료 후 heading focus를 유지한다.
- 빠른 정상 이동의 불필요한 flash와 필요한 장시간 로딩을 구별한다. 실제 기다림과
  실패를 숨기거나, 안정적으로 보이게 하려고 응답·오류를 버리거나 근거 없는 고정 대기를 넣지 않는다.
- `0`, 미조회, 자료 없음, 필터 불일치, unavailable, error를 같은 값으로 취급하지 않는다.
  이전 값 유지 시 그 값이 현재 범위와 맞는지도 확인한다.
- query/filter/selection/disclosure/pane 크기/전체 및 내부 scroll은 각 소유자 계약대로
  유지 또는 reset한다. 고장 난 focus·binding·뒤로가기와 stale response를 자연스러운
  애니메이션으로 덮지 않는다. 새 입력·이동·reset·exit는 이전 motion/응답을 정리해야 한다.
- 현재 모달의 이름·focus trap·close·trigger focus 복귀, 오류 시 입력/회복, 키보드 접근,
  reduced motion, `320px` 최소 지원 폭과 공유 breakpoint를 보존한다.
- 실제 개인 DB·설정·소스·모델·캐시와 실행 중인 사용자의 서버를 변경하지 않는다.
  test fixtures와 캡처는 합성 자료로 만들고 모든 runtime은 저장소 밖에 둔다.

## Findings And Audit Candidates

아래는 계획 수립 시점의 최소 재현과 소스 후보다. 후속 실제 판정과 host별 증거는
[Audit results](initial-state-and-transition-audit-results.md)가 소유한다.

| 항목 | 현재 판정 | 다음 조사 |
| --- | --- | --- |
| 설정 로딩 안내의 삽입/제거와 첫 진입 빈 선택값 | 위 조건에서 재현 | 모든 설정 category, shortcut, `/settings`, 재열기 및 native host에서 같은 소유자를 확인 |
| Chart의 fallback→explorer handoff | 소스상 후보. [_session_chart.html](../../../src/localbrain/templates/_session_chart.html)은 fallback을 먼저 표시하고 explorer를 숨김. [JS](../../../src/localbrain/static/session-chart.js)가 렌더링 후 전환 | 정상 cold paint에서 실패처럼 읽히는 안내가 먼저 보이는지, JS 지연/실패 때 유효한 fallback인지 분리 |
| 시각·profile 등 초기 HTML의 클라이언트 보정 | 소스상 후보. [app.js](../../../src/localbrain/static/app.js)는 시각을 포맷하고 [profiles.js](../../../src/localbrain/static/profiles.js)는 표시값/순서를 갱신 | 원시 timestamp·기본 label·폭/순서 변화의 노출 여부. 최종 값의 정확성과 별개로 검사 |
| Context preview·Dashboard 등의 부분 갱신 | 소스상 기존 content를 유지하고 교체하는 경로 있음. 전환 품질 미평가 | 빠른 연속 선택, 응답 역전, 실패 fallback, shell/scroll/focus 유지와 재바인딩 |
| native startup→인증 redirect→저장된 화면/onboarding | [startup 화면](../../../desktop/ui/index.html)과 [native host](../../../desktop/src-tauri/src/main.rs)에 별도 handoff 존재. 이번 runtime 미검증 | cold/retained launch, retry, 자산 준비와 첫 의미 있는 화면까지의 전체 과정 |
| 빈 상태와 조회 실패의 혼동 | 미확인 후보. 설정 `render()`는 `session_sources`가 없을 때도 빈 목록 안내를 만들 수 있음 | 합성 partial/error 응답에서 실제 빈 등록과 읽기 실패를 혼동하는지 확인 |

후보를 확정 결함으로 승격하려면 실제 route와 입력·데이터·응답 순서를 재현해야 한다.
공통 소유자 결함은 보고된 사례와 대표 consumer를 함께 검사하고 파급 범위 및
기존 열린 화면의 reload/asset 갱신 필요 여부를 기록한다.

## State And Transition Matrix

상태의 명칭은 검사용 분류이며 새 persisted domain state가 아니다. 각 화면에
해당하는 행과 기존 계약을 연결하고, 불가능한 조합은 이유와 함께 제외한다.

| 검사용 상태/조건 | 기대하는 의미와 관찰 지점 |
| --- | --- |
| 미조회·client 초기화 전 | 저장값을 아직 모르는 상태. 가짜 기본값·최종 empty/error를 확정적으로 보이지 않는지 |
| 실제 대기·skeleton/progress | 필요한 영역 안의 의도된 표시, 최종 형태/공간, shell 유지, 상태 안내와 올바른 disabled/`aria-busy` |
| 정상·일부 누락 | 값 있는 화면, 긴 제목/경로/혼합 언어, 일부 속성만 없음. 누락을 `0`으로 만들거나 전체 화면을 empty로 만들지 않는지 |
| 진짜 empty | 미등록 소스·수집 0건·빈 문서·미선택 preview를 각각 구별하고 해당 회복 동작이 맞는지 |
| 필터/검색 0건 | 전체 자료 없음과 구별. 적용 조건·query를 보존하고 올바른 reset/recovery가 있는지 |
| unavailable·stale·error | 파일/권한/모델 미준비·연결 불가·설정 읽기 실패·부분 응답을 빈 결과나 최신 성공으로 바꾸지 않는지 |
| 저장/작업 pending→성공·실패·불확실→복구 | confirmation과 readback, 입력 보존, retry, 중복 방지. absent/명시적 empty/마이그레이션/복구된 선호를 구별하고 약속된 scope/lifetime 뒤에도 값 확인 |
| 빠른 정상 전환 | 첫 표시·early/middle/late·settled에서 flash, 불필요 placeholder, 이중 화면, 위치/크기 변화 |
| 지연·실패·응답 역전·취소 | 오래된 응답/완료 callback이 최신 화면을 덮지 않는지. 기다리는 중 닫기·재열기·이동·reset과 최종 회복 |
| 직접 진입·새로고침·뒤로/앞으로·재방문 | URL·선택·ancestor disclosure·현재 위치·각 scroll/focus와 활성 surface의 일관성 |
| reduced motion·키보드·폭 전환 | 비필수 이동/pulse 제거 후 목적지·선택·사용 가능성 유지. 뒤 화면 격리와 열린 메뉴/모달의 focus·containment |

환경은 full Cartesian product 대신 위험 기준으로 배정한다.

- 모든 현재 화면 family: 정상 populated/empty 초기 진입과 대표 전환, desktop/narrow.
- 설정/첫 실행/shell/Chart/부분 갱신: cold cache·warm 재방문·준비 전 클릭,
  API와 CSS/JS/font 지연 또는 실패, CPU slowdown, 연속 입력/취소/역전까지 심화.
  초안 지연 조건 `0/200/1000ms`, CPU `1×/4×`는 시험 입력이며 합격 수치가 아니다.
  cold는 캐시 없는 첫 방문, warm은 캐시를 사용할 수 있는 재방문으로 구분한다.
- 기본 viewport 폭 `1440/920/700/320`, settings breakpoint 양옆 `699/701`,
  낮은 높이 `400px`를 위험 화면에 추가한다. 실제 inner size·DPR·zoom·document
  client/scroll width를 기록한다. 최소 폭에서는 공간을 차지하는 scrollbar와
  열린 disclosure도 확인하고, overflow를 숨겨 합격시키지 않는다.
- web Chromium, 격리 WKWebView, 실제 packaged Tauri를 별개 결과로 기록한다.
  첫 설치·retained launch, 서비스/앱 재시작을 구별한다. 새 browser context는
  browser process 또는 앱 restart의 대체 증거가 아니다.

## Planned Work

### Batch 0 — 대상과 재현 환경 고정

- Goal / grouping: 출처·배포물·화면 목록이 다른 상태에서 비교하지 않도록 기반을 고정.
- Targets: route/navigation inventory, shared templates/assets, synthetic DB/settings,
  desktop version/revision/backend 및 suspended feature 경계.
- Guardrails: 현재 사용자 runtime과 분리. 실제 앱이 소스보다 이전 버전이면 그 차이를
  기록하고 rebuild나 동일 원인을 가정하지 않는다. 숨긴 기능은 기존 positive 저장 상태가
  있어도 제외되는지 확인하며, 빈 fixture만으로 억제 경계의 통과를 주장하지 않는다.
- Validation: synthetic fixture별 상태, source/served asset/build 식별, route-family 목록과
  대표/고유 상태/제외 사유. 기존 소스·데이터 retained 상태도 소유 계층에서 확인.
- Exit gate: 조사할 각 화면·host·상태와 증거 위치가 명시되고 예기치 않은 실제 읽기/실행 없음.

### Batch 1 — 설정 진입과 첫 실행

- Goal / grouping: 확인한 짧은 본문 이동과 같은 modal/초기화 경로를 우선 조사.
- Targets: sidebar 설정, Cmd/Ctrl+, native menu, 직접 `/settings`, 모든 category,
  source/context editor, 모델·storage의 lazy 표시, `/onboarding`, startup handoff.
- Guardrails: 저장·draft·onboarding·native 인증 계약 유지. 모델/OS 권한 작업은 fixture 또는
  기존 상태로 검사하며 실제 다운로드·등록·권한 요청을 시작하지 않는다.
- Validation: 첫 열기/재열기/닫기 중 응답/저장 pending, 정상·지연·설정 partial/error,
  첫 paint·본문 좌표·선택값·focus·배경 격리, 넓고 좁은 화면/reduced motion.
- Exit gate: 증상의 발생 조건·소유자·native 재현 여부 또는 미검증 범위가 분리되고,
  수정 방향별 계약 영향이 설명됨. 이 gate는 수정 시작 승인이 아니다.

### Batch 2 — 핵심 읽기·탐색 화면

- Goal / grouping: 공통 shell을 공유하는 일상 경로에서 초기 표시와 부분 교체를 조사.
- Targets: Sessions/Projects/List/Chart/detail/subsession/pin·copy,
  Sessions Dashboard scope/metric/date, Local Context tree/preview/document,
  keyword/AI search 및 evidence, Docs의 코드·표·diagram.
- Guardrails: 읽기를 Sync·모델 준비·추론으로 바꾸지 않는다. 실제 zero/unknown/empty,
  검색 mode와 적용 조건, source identity와 retained 상태를 유지한다.
- Validation: matrix 적용, pointer/keyboard, 직접 진입/history, 긴 자료, Chart fallback,
  preview 연속 선택·역전, 모델 미준비/실패, rich content·font 지연, shell/scroll/focus.
- Exit gate: 모든 핵심 family의 상태·전환 coverage가 채워지고 공통 원인과 개별 예외가 구별됨.

### Batch 3 — 개발 웹의 나머지 화면

- Goal / grouping: 배포 앱에 없는 화면도 공통 구현의 누락 consumer로 남기지 않음.
- Targets: Dashboard/학습, Workstreams/Thread/Suggestion, Sources, Atlassian,
  Schema, Auto Work, 기존 workflow 읽기, Run/Insights의 보존된 결과/진행 상태.
- Guardrails: 새 모델/agent job·외부 호출 없이 합성 결과·read-only fixture 사용.
  중단된 제품 트랙과 실패 trial의 재시도 권한을 새로 만들지 않는다.
- Validation: 각 family의 정상·empty·unavailable/error·active 상태와 대표 이동을
  넓은/좁은 화면에서 검사. 특유한 transition은 심화 조건에 추가.
- Exit gate: 현재 제공되는 화면 목록의 미검토 항목이 없거나 명시적 보류 이유·다음 소유자가 있음.

### Batch 4 — 개발 중 반복 가능한 절차와 수정 후보 반환

- Goal / grouping: 일회성 눈검사 결과를 다음 UI 변경에서 재사용 가능한 절차로 연결.
- Targets: 아래 개발 루틴, fixture/시나리오 registry, 증거 receipt 형식, 기존 evaluator 연계.
- Guardrails: 1차 조사에서는 QA 도구나 정책을 구현/변경하지 않았다. frame snapshot을
  곧바로 모든 화면의 고정 screenshot test나 임의의 ms 임계치로 만들지 않는다.
- Validation: 한 사람이 같은 fixture/조건/동작으로 같은 판정 근거를 얻는지 검토.
  자동 판정과 사람이 모션의 자연스러움을 보는 부분, host별 미검증을 구분.
- Exit gate: 재현 가능한 결함 목록·우선순위·소유자·수정 후보와 반복 검사 제안이 준비됨.

수정 후보의 우선순위는 잘못된 상태/값 전달·조작 불능·focus 격리 실패를 가장 먼저,
반복되는 flash·본문/컨트롤 이동·이중 화면을 다음으로, 미세한 타이밍 차이를 그 뒤로
정한다. 발생 빈도·영향 범위·회복 가능성과 실제 host 증거를 함께 보고 조정한다.

## Proposed Development Verification Process

F1–F6의 반복 명령은 `node scripts/qa-ui-states-browser.mjs`로 제공한다.
[Developer Guide](../../policies/project/developer-guide.md#verification)가 실행 조건·격리·정리를 소유한다.
이 명령은 아래 전체 matrix의 일부를 고정한 회귀 검사다. frontend 평가자는 시나리오와 최종 의미를 소유하고, native 호스트 증거는
별도 검증으로 남긴다. backend/data의 동시 변경이 필요한 수정은 승인 경계를 정한 뒤
`fullstack-product` 및 contract lane 필요성을 다시 판단한다.

1. **상태를 선택해 실행:** 격리 backend에서 populated/empty/partial/unavailable/error와
   초기/기존 선호 fixture를 고른다. 데이터·캐시·공유 모델 위치와 source discovery를
   모두 분리하고, source/asset/build/host를 기록한다.
2. **진입부터 관측:** 첫 navigation 전에 계측과 filmstrip/video를 시작한다. 실제
   click/keyboard, 직접 URL, reload/history를 수행한다. 보통 속도와 통제 지연/실패를
   따로 실행하며, cache hint·download 완료만으로 rendered/interactive ready를 판단하지 않는다.
3. **시간 순서로 판정:** 동작 시작·request 시작/완료·첫 의미 있는 content·interactive
   ready·settled와 early/middle/late frame을 연결한다. DOM/ARIA/focus/scroll/bindings,
   shell/dialog/heading/control 좌표와 visible text를 캡처와 대조한다. CLS 등 page 지표는
   보조로 쓰며 사용자 입력 직후 이동이나 짧은 flash의 부재를 점수만으로 단정하지 않는다.
4. **증거와 발견 기록:** route·trigger·fixture·expected/observed sequence·재현 횟수·host/
   input mechanism·viewport·지연/cache/CPU·source/assets/build·소유자/파급 consumer·영향·
   evidence locator·한계·다음 검증을 남긴다. 실제 app·격리 WKWebView·browser, script event·
   automation input·physical input을 구분한다. `trusted` event만으로 physical input이라 하지 않는다.
5. **변경 때 재실행:** 관련 UI 변경은 보고 사례와 공통 consumer의 짧은 smoke를,
   shell/shared initializer 변경은 핵심 family matrix를 선택한다. native 변경은 실제
   packaged host까지 반복한다. 안정된 계약이 있는 재현 결함만 의미 있는 regression guard로 만든다.
6. **종료와 보존:** task-owned 임시 runtime/trace/profile/capture를 프로세스 종료 후 정리한다.
   장기 증거가 필요하면 기존 Run/evaluation의 명시적 비공개 owner로 옮겨 참조를 갱신한다.
   durable plan·평가 결과가 삭제할 임시 경로에 의존하지 않도록 한다.

자동 검사 후보는 로딩과 empty/error의 의미, stale response 차단, 최종 binding·선택·focus,
의도하지 않은 anchor 이동이다. 화면이 번쩍이거나 모션이 끊기는 인상, 두 layer의 경쟁,
잠깐 나타난 문구의 오해는 원속도와 느린 재생의 시각 검토를 함께 요구한다.

## Validation Gates And Handoff

- **Coverage:** route inventory의 각 family를 matrix와 연결하고 실제 검사/미검증/해당 없음의
  이유를 표시한다. `rendered pass`와 전체 제품·native acceptance를 분리한다.
- **Design:** 초기·중간·완료 화면에서 shell·modal·최종 content geometry와 토큰/가독성을
  확인한다. 공통 소유자의 보고 사례와 대표 peer도 검사한다.
- **Functional:** 값/URL/상태 의미, 입력 보존·저장/readback·retry, rapid input/cancel/역전,
  focus/scroll/history·binding, 의도된 fallback과 최신 목적지를 검증한다.
- **UX:** ordinary transition의 flash·불필요 scaffolding·잘못된 empty/error 문구,
  orientation 상실·조작 전에 움직이는 control을 검사한다. 장시간 대기의 정직한 안내와
  접근성을 단순한 깜빡임 제거보다 약화시키지 않는다.
- **Evidence:** source inspection만 한 후보, 통제 지연에서만 확인한 현상, 정상 속도 재현,
  native 미확인을 구분한다. 캡처할 수 없는 상태는 unverified이며 정적 test 통과로 대체하지 않는다.
- **Routing:** 기존 계약 위반은 `implementation bug`, 준비/실패/전환 조건이 빠졌으면
  `spec gap`, 제품 flow/승인 경계가 잘못됐으면 `planning gap`으로 반환한다.
  실제 수정은 별도 요청과 적용 가능한 기존 승인 경계에 따라 진행한다.
- **Policy ownership:** 반복 가능한 평가 누락이 실제 증거로 확인되면 Design Evaluation은
  시각 frame/geometry, Interaction Evaluation은 상태/전환/복구, functional role은
  동작 검증에 연결한다. 보편적 법칙으로 확정되지 않은 일정·수치·screen 예외는 이 계획에 둔다.

## Risks / Open Questions

- 사용자 증상이 어떤 설치 앱 build·입력 경로에서 발생했는지는 아직 고정하지 않았다.
  web 재현은 초기 원인 후보를 좁히지만 native 동일성을 대신하지 않는다.
- 짧은 상태는 도구가 settled DOM을 기다리거나 느린 screenshot만 찍으면 놓친다.
  반대로 지연 주입은 평소 안 보이는 상태를 과장하므로 정상 속도 증거와 분리한다.
- source/asset version과 실행 중 backend가 다르면 결과가 달라질 수 있다.
  active runtime의 업데이트/재시작 전후 경계를 확인하거나 필요한 bounded restart를 기록한다.
- 설정은 서버가 읽은 초기 값과 header 진행 표시로 정리했다. 다른 화면의 로딩 노출 지연,
  최소 표시 시간, 이전 값 유지, skeleton 사용 여부는 아직 결정하지 않았다.
  실제 latency·회복·접근성 증거로 비교한 뒤, user-visible behavior가 바뀌면 해당 소유자의
  결정/승인 경계에서 정한다. 임의의 `100ms` 등 단일 수치를 전 앱의 합격 기준으로 삼지 않는다.
- 실제 OS 권한창·VoiceOver·physical native input·recipient Mac까지 필요한 경우의
  증거는 별도 일정과 범위가 필요하다. scripted/browser 결과를 그 통과로 확대하지 않는다.

## Exit Goal

설정 증상은 실제 원인/발생 조건/host 한계까지 설명되고, 현재 화면 family의 초기·빈 값·
대기·실패·전환 검토 범위가 빠짐없이 추적되어야 한다. 결과물은 재현 가능한 발견 목록,
공통 소유자별 수정 후보, 개발 시 반복할 검사 절차와 증거 한계다.

계획 수립 당시 반환물은 draft 계획과 설정의 최소 재현이었다. 후속 `진행` 요청으로
Batch 0의 대상 확인, Batch 1의 설정/첫 실행 심화, Batch 2–3의 화면 순회와 대표 전환,
Batch 4의 반복 검증 방향을 1차 조사했다. 실제 결과와 잔여 positive/active/native
검증은 [Audit results](initial-state-and-transition-audit-results.md)에 기록한다.
이를 앱 전반의 무결함 판정이나 수정·정책 변경 승인으로 취급하지 않는다.

후속 `리뷰대로 정리` 요청으로 확인된 F1–F6을 수정하고, 초기 HTML·상태별 출력의
Python 검사와 격리 합성 browser 회귀 명령을 남겼다. 전체 Python suite와 Chromium,
격리 WKWebView의 범위 한정 결과는 결과 문서의 최신 검증 절을 따른다. 실제 Tauri,
Chart/시각 보정 후보와 남은 positive/active 상태는 이 트랙의 다음 검토 경계다.
