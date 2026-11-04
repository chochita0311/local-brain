# Initial State And Transition Audit Results

## Review Boundary

- First audit: `2026-11-01`; repair verification: `2026-11-02`; QA closeout: `2026-11-04`.
- Current status: **F1–F6 source fixes and scoped regressions complete**.
  전체 상태·native acceptance의 통과 판정은 아니다. 기존 배포 앱은 재빌드하지 않았다.
- Parent: [Initial State And Transition Audit Plan](initial-state-and-transition-audit-plan.md).
- Authority: 첫 조사는 계획 작성 뒤 사용자의 `진행` 요청에 따라 수행했으며 당시에는
  제품 코드·평가 정책·배포물을 수정하지 않았다. 후속 `리뷰대로 정리` 요청의 F1–F6
  수정과 검증은 아래 Repair Contract/Verification을 따른다. 새 제품 Feature/Spec/Run
  승인을 만들지 않는다.
- Profile: `frontend-product`. 공통 UI/설정 → 핵심 화면 → 개발 웹의 순서로 관찰하고,
  design·functional·UX 증거를 함께 검토했다. native host는 별도 증거 범위다.

설정의 깜빡임은 Chromium과 격리 WKWebView에서 재현됐다. 그 밖에도 읽기 오류를
빈 상태로 바꾸는 표시, 준비 전 활성화된 모델 버튼, 첫 실행 스크립트 실패 시의
조작 불능, 긴 경로가 있는 좁은 화면의 넘침, 완료 Run에 남는 준비 문구가 확인됐다.
이 문서는 발견·검토 범위·수정 결과와 다음 검토의 소유자다. 현재 동작 계약은 기존 정책이 소유한다.
다음 1차 조사 절은 수정 전 증거이며, 최신 상태는 문서 끝의 수정 검증 절을 따른다.

## Evidence And Environment

| 구분 | 실제 확인한 대상과 조건 |
| --- | --- |
| Source | `b844ce8`, 앱 version `0.0.1`. 시작 시 기존 변경은 앞선 계획·인덱스·백로그 문서뿐이었다 |
| Web | 별도 loopback backend와 독립 Chrome `156` 프로필. 실제 CSS viewport `1440/920/700/320 × 900`, 설정은 추가로 `701×400`, `699×900`. DPR `1` |
| Native engine | 별도 AppKit 창의 비영구 WKWebView, `1440×900`. 합성 desktop backend에 `tauri://localhost` 출발 → 인증 redirect → 실제 `/sessions` 또는 onboarding까지 연결. DOM script 입력이며 실제 Tauri 창의 물리 입력이 아님 |
| Packaged artifact | 기존 test build의 version `0.0.1`, build `2026-11-01T12:08:29Z`. `base.html`, `_settings.html`, `settings.js`, `settings.css`, `app.js`, `session-chart.js`의 SHA-256을 비교해 소스와 같은 bytes임을 확인. 실제 배포 앱 실행·재시작·입력 검증을 대신하지 않음 |
| Data | 합성 등록 프로필 2개, Session 12개와 메시지·Usage, pin 1개, 문서 3개(긴 문서·빈 문서 포함), Workstream/Thread, reviewed-test Lesson, 보존된 Run. 별도로 등록·자료가 없는 fixture. 모델·개인 후보 탐색·주기 수집·외부 호출은 사용하지 않음 |
| Perturbation | `/api/settings`의 응답 보류·실패·partial 응답, 실제 합성 source TOML 파손, PATCH `500ms`, preview `600ms`, Dashboard `450ms`, 선택 JS `800ms` 지연/실패, 설정의 CPU `4×`, reduced motion. 이 수치는 시험 조건이지 합격 임계치가 아님 |
| Collection | navigation 전 주입한 `requestAnimationFrame` 표본, 초기/보류/완료 렌더 캡처, DOM·ARIA·focus·scroll·request 상태·viewport 좌표. rAF 시각은 compositor paint 시각이나 사람이 인지한 지속 시간과 다름 |

화면 순회는 **자료가 있는 fixture 35개 URL × 4개 폭 = 140개**, **빈 fixture 25개
URL × 4개 폭 = 100개**의 관찰이다. 자료가 있는 fixture도 Atlassian·Auto Work·Insights의
결과까지 채운 것은 아니다. 여기에 설정 상태 표본 51개, 전환 상태 표본 28개,
원인 비교 표본 7개, WKWebView 표본 16개를 수집했다. 하나의 전환에서 여러 표본을
읽었으므로 이 수를 서로 독립적인 통과 테스트 수로 해석하지 않는다.

## Findings

높음은 조작 불능이나 상태 오해를 우선 해소해야 하는 경우, 보통은 반복되는 이동·
준비 상태 불일치·특정 데이터/폭의 표시 결함이다. 실제 발생 조건과 증거 범위를 함께 적용한다.

### F1 — 설정 진입에서 빈 선택값과 약 76px 본문 이동

- **Priority / classification:** 보통 / `implementation bug`.
- **Trigger:** `/sessions`의 설정 버튼, 재열기, 직접 `/settings`, Cmd+, reduced
  motion. 정상 속도와 CPU `4×`, 보류 조건을 관찰했다.
- **Observed:** 첫 열기에서 dropdown 표시값이 비고 비활성 상태가 나온 뒤 저장값으로
  바뀐다. Chromium의 일반 heading Y는 `312.14 → 236`, 격리 WKWebView는
  `312 → 236`이었다. dialog의 `720×560` 외곽은 고정되지만 로딩 안내의 삽입/제거로
  본문은 약 `76px` 이동한다. 재열기에서는 이전 값이 있어도 안내 영역이 재등장한다.
  reduced motion도 이 레이아웃 이동을 제거하지 않는다.
- **Cause / owner:** [settings.js](../../../src/localbrain/static/settings.js)의
  `open()`/`load()`/`renderGeneral()`과
  [settings-message](../../../src/localbrain/static/settings.css).
  값이 준비되기 전에 모달을 열고 본문 앞에 안내를 넣었다가 `render()`에서 제거한다.
- **Repair candidate:** 일반 설정의 준비 상태와 본문 anchor를 함께 다룬다. 이미 읽은 값의
  재사용과 최초 조회의 의도된 표시를 비교하되, pending 저장 대기·오류 안내·진짜 지연을
  보존한다. 로딩 문구만 무조건 숨기거나 고정 대기 시간을 넣는 것으로 끝내지 않는다.
- **Limit:** 이 측정은 창 전체의 백색 flash나 실제 Tauri 창의 동일 증상까지 입증하지 않는다.

### F2 — 프로필 읽기 실패가 카테고리 이동 후 “프로필 없음”으로 바뀜

- **Priority / classification:** 높음 / `implementation bug`.
- **Trigger:** 등록 프로필이 있는 합성 backend의 `session-sources.toml`을 읽을 수 없는
  TOML로 바꾼 뒤 설정을 열고, 세션 소스 카테고리로 이동한다. 별도 partial API 응답으로도 비교했다.
- **Observed:** 첫 화면의 `세션 소스 설정을 읽지 못했습니다. 기존 파일을 확인해 주세요.`가
  카테고리 이동 시 사라진다. 그 자리에 `연결한 프로필이 없습니다`와 프로필 추가 안내가
  나온다. 등록 내용의 부재가 확인된 상황이 아니며, 원래 합성 파일을 복구하면 같은
  프로필을 다시 읽을 수 있다. 실제 등록을 지우는 동작은 일어나지 않았다.
- **Cause / owner:** `render()`가 `session_sources=null`을 빈 목록처럼 렌더링하고,
  `tab()`이 공통 `message`를 지운다. 소유자는
  [settings.js](../../../src/localbrain/static/settings.js)의 조회/목록/오류 상태다.
- **Repair candidate:** 조회 미완료·읽기 실패·확인된 빈 등록을 구별하고, 오류가 다른
  category로 이동했다는 이유로 해제되지 않게 한다. 재조회/파일 수정 후 복구 경로를
  정의하되 기존 등록·revision·source identity는 유지한다.

### F3 — 설정 조회 전·실패 후 검색 모델 동작이 준비된 것처럼 활성화됨

- **Priority / classification:** 보통 / `implementation bug`.
- **Trigger:** 새 page에서 설정 GET을 보류하거나 실패시킨 뒤 검색 모델 카테고리로 이동.
- **Observed:** 로딩/오류 안내가 사라지고 모델 상태와 AI 검색 상태가 비어 있는 동안
  `모델 다운로드`, `AI 검색 준비`, `AI 검색 끄기`가 활성 상태다. 실제 fixture에는 설치된
  모델이 없으며 정상 응답 후에는 `AI 검색 준비`가 비활성화된다. 일반 설정 dropdown은
  조회 중 잠기므로 category 간 준비 상태도 일치하지 않는다.
- **Cause / owner:** [template](../../../src/localbrain/templates/_settings.html)의 초기
  버튼 상태와 `renderModel()`/`pollModel()`/`tab()`의 준비 상태 연결.
- **Repair candidate:** 확인된 모델·검색 상태에 따라 동작 가능 여부를 표시하고, 상태를
  아직 모르는 시간과 실패를 빈 문구로 남기지 않는다. 단순히 버튼을 항상 잠그지 말고
  정상 조회·poll·재조회 후 적절히 복구해야 한다.
- **Limit:** 버튼의 활성 표시만 검증했다. 다운로드·모델 준비·검색 끄기를 실행하지
  않았으므로 실제로 잘못된 작업이 시작됐거나 backend가 검증을 생략했다고 주장하지 않는다.

### F4 — 첫 실행 스크립트 실패 시 마법사 없이 조작 불가 배경만 남음

- **Priority / classification:** 높음 / 초기 asset 실패의 복구 경로에 대한 `spec gap`.
- **Trigger:** 명시적 `/onboarding` 진입에서 `settings.js` 요청을 실패시킨다.
  동일 script를 `800ms` 지연한 경우도 비교했다.
- **Observed:** 실패 후 document는 `complete`지만 dialog는 닫혀 있고 `.app-shell`은
  계속 `inert=true`다. 사용자는 본 화면을 보지만 해당 화면과 설정 버튼을 조작할 수
  없고, 페이지 안에 시작 실패 안내나 재시도 경로가 없다. script 로딩을 허용해
  새로고침하면 마법사가 열린다. 지연만 준 경우에는 배경이 먼저 보이다가 마법사가 나타난다.
- **Cause / owner:** [base.html](../../../src/localbrain/templates/base.html)의 초기
  배경 격리와 deferred [settings.js](../../../src/localbrain/static/settings.js)의 modal 초기화.
  배경 격리 자체는 올바르다. JS 준비/실패 시 첫 활성 surface의 표시·복구가 별도 필요하다.
- **Repair candidate:** backend startup 오류, settings API 오류와 client asset 실패를
  구별해 첫 표시/재시도 계약을 보완한다. 마법사 초기화 전에 배경의 `inert`만 제거하는
  방식은 승인된 상호작용 격리를 깨므로 사용하지 않는다.
- **Limit:** web의 명시적 setup route에서의 통제 실패 재현이다. 실제 Tauri startup의
  asset 실패·재시도까지 검증한 것은 아니다. 정상 속도에서 이 배경 노출이 반드시
  눈에 띈다는 판정도 하지 않는다.

### F5 — 긴 Pinned 경로가 320px Sessions 목록을 480px로 넓힘

- **Priority / classification:** 보통 / `implementation bug`.
- **Trigger:** 긴 absolute workspace path를 가진 pin이 있는 `/sessions`, 폭 `320px`.
- **Observed:** document `clientWidth=320`, `scrollWidth=480`. Pinned Sessions의
  패널 폭이 약 `466px`까지 커진다. 다른 데이터를 유지하고 합성 workspace path만
  `/synthetic/a`로 줄이면 `scrollWidth=320`으로 돌아온다. 빈 fixture에서는 발생하지 않았다.
- **Cause / owner:** [Pinned list와 좁은 레이아웃](../../../src/localbrain/static/styles.css)의
  intrinsic width와 [경로 heading](../../../src/localbrain/templates/sessions.html).
  heading의 ellipsis만으로 부모 grid의 최소 너비를 제한하지 못한다.
- **Repair candidate:** 긴 경로를 수용하는 부모/자식의 containment와 scroll 소유자를
  함께 검토한다. 경로 표시·pin·원본 접근성을 지우거나 문서 overflow를 잘라내지 않는다.
- **Limit:** Chromium의 해당 fixture/폭에서 확인했다. 동일 좁은 WKWebView 상태는 미검증이다.

### F6 — 완료된 Run의 출력 파일이 없으면 “실행 준비 중”으로 표시됨

- **Priority / classification:** 보통 / `implementation bug`.
- **Trigger:** 유효한 `organize_resources` 유형의 보존된 완료 Run이 있지만 result
  파일이 없고 stderr 출력도 없는 합성 상태. 실제 agent job은 시작하지 않는다.
- **Observed:** `/runs/synthetic-completed`의 상태 배지는 `완료`인데 console은
  `Claude 실행을 준비하고 있습니다.`로 표시된다. `1440px`와 `320px`에서 동일했다.
- **Cause / owner:** [read_run_output()](../../../src/localbrain/maintenance/service.py)가
  빈 문자열을 반환하고 [run.html](../../../src/localbrain/templates/run.html)이 Run의
  lifecycle과 무관하게 빈 출력에 준비 문구를 사용한다.
- **Repair candidate:** queued/running의 출력 대기와 완료·실패 후 출력 없음/유실을
  구별한다. 이 표시 수정으로 job을 재실행하거나 보존된 Run 상태를 바꾸지 않는다.

## Delayed-Asset Observations Requiring Design Judgment

다음 두 항목은 통제한 JS 지연에서 재현했다. 정상 속도의 네 폭 순회에서는 초기
안내/원시 시각이 잡히지 않았으므로 평상시에도 보이는 확정 flicker로 확대하지 않는다.

| 항목 | 관찰과 보존해야 할 경계 |
| --- | --- |
| Chart 초기 handoff | `session-chart.js` `800ms` 지연 시 `시간 차트를 불러오지 못하면…` 안내와 List 링크가 먼저 보이고, 이후 explorer로 바뀐다. script 실패에서는 안내·List 링크가 계속 남는다. 실패 복구는 유효하므로 fallback을 무조건 숨기는 수정은 부적절하다. 초기 대기의 어조·공간과 실제 실패를 어떻게 구별할지 검토 |
| 시각 표시 보정 | `app.js` `800ms` 지연 시 Session의 ISO UTC 문자열이 먼저 보이고, 로딩 후 한국어 시각으로 바뀐다. 값의 최종 정확성과 초기 표시 폭/형식의 일관성을 분리해 검토. 서버 표현과 클라이언트 보정의 소유자를 정할 후보 |

## Behavior Confirmed In The Checked Cases

- Context preview는 지연 중 이전 문서를 유지했다. 두 번째 문서 응답을 `600ms`
  늦춘 뒤 세 번째 문서를 선택해도 최종 preview/URL/current가 세 번째에 일치했고,
  원래 tree DOM을 유지했다. 뒤로가기는 첫 문서로 돌아왔다.
- Sessions Dashboard의 metric 전환은 대기 중 기존 내용을 유지하고 교체했다.
  관찰한 document scroll은 `124 → 124`, 최종 metric은 Cost였다.
- 일반 설정의 `500ms` 저장 중 닫기/재열기에서도 선택값과 최종 파일 readback이
  일치했다. 이것은 단일 pending write 사례이며 모든 conflict/실패 조합의 통과가 아니다.
- 설정을 연 뒤 실제 CDP Tab 입력 15회가 모달 안에 머물렀고 Escape 후 설정 trigger로
  focus가 돌아왔다. 검토한 설정 category는 `920/701/700/699/320px`에서 문서 가로 넘침이 없었다.
  `701×400`의 낮은 높이도 관찰했다. 모든 좁은 expanded menu의 통과를 뜻하지 않는다.
- 첫 실행의 배경은 처음부터 inert였다. Chromium·격리 WKWebView에서 전환 중 양쪽
  panel은 inert이고 outgoing은 `aria-hidden=true`, 완료 후 새 heading focus를 확인했다.
  Back의 미저장 draft가 유지됐고 Skip/종료 후 등록 소스는 0개였다. Chromium의
  reduced-motion 단계 전환은 running animation 0개로 목적지와 focus를 유지했다.
- 위 결과는 각 기재된 route·fixture·입력·host의 증거다. 프로그램 실행 여부·화면 존재·
  정적 검사 성공을 전체 전환 품질이나 physical/native acceptance로 바꾸지 않는다.

## Screen Coverage And Remaining Evidence

기본 순회는 각 행의 진입·최종 렌더·문서 overflow·Runtime exception을 확인했다.
상태별 깊은 상호작용은 앞 절에 명시한 것만 검증했으며, 행 전체의 모든 기능 통과가 아니다.

| Family / sampled URLs | 확인한 상태 | 남은 주요 증거 |
| --- | --- | --- |
| Settings, `/settings`, `/onboarding` | 첫 열기/재열기/shortcut, 7 categories, 실제 source 읽기 오류, API 보류/실패, 모델 준비 전, 저장 중 재열기, wizard와 focus | 실제 Tauri menu/shortcut/재시작, preference conflict·복구 전 조합, narrow expanded menus, Notes/OS chooser, VoiceOver |
| `/sessions`, `?display=chart`, `/projects` | 12 Session과 pin·긴 제목/경로, 등록 없음, 4개 폭, chart 준비/JS 실패 fallback, CPU4 설정 진입 | 실제 sync의 working/success/failure 전환, 모든 chart input·camera 복귀, 풍부한 subsession 분기 |
| `/sessions/1`, `/sessions/1/workflow` | 합성 메시지와 메타데이터, 기존 workflow 읽기/부족 상태, 4개 폭 | positive Subsession route, copy outcome 전체 시간 순서, 재구성/추출·관계 변경은 미실행 |
| `/sessions-dashboard` | Usage 있음/없음, 4개 폭, Cost 부분 전환·지연·scroll | 모든 source/date/interval 조합·역전·실패/취소 |
| `/context`, `?root=1&document=1`, `?root=1&document=3`, `/documents/1`, `/documents/3` | 등록 없음·긴/빈 문서, 4개 폭, preview 지연/연속 선택/취소된 응답/history | source 권한/실제 파일 유실의 전 조합, 원문 삭제 동작·실제 Notes 미실행 |
| `/natural-search?mode=keyword&q=Synthetic`, `q=NoMatch000`, `mode=ai&q=Synthetic` | 키워드 결과 있음/없음, AI 비활성·미준비, 4개 폭 | 실제 ready/partial/failed index·generation의 전환과 evidence 상세. 모델을 실행하지 않아 미검증 |
| `/help`, `/help/{settings,sessions,sessions-dashboard,local-contexts,search}` | 여섯 bundled guide, 4개 폭, code/table 읽기 | 모든 rich-content 최대 길이·접근성 조합 |
| `/`, `/learning`, `/learning/1`, `/learning/1/note` | 합성 v1 Lesson과 빈 목록, 4개 폭 | 최신 article/scene layout의 positive fixture, 답변·복습 상태는 미실행 |
| `/workstreams`, `/workstreams/1`, `/sources` | 합성 Workstream/Thread와 source, 빈 상태, 4개 폭 | Suggestion accept/reject·Thread 편집·수집 상태 전환 미실행 |
| `/atlassian`, `/atlassian/add`, `/atlassian/connections`, `/atlassian/refresh` | 로컬 미등록/첫 입력 surface, 4개 폭 | 등록된 tree/item/reference의 positive 상태·preview race·접근 오류; 외부 읽기/등록 미실행 |
| `/schema`, `/auto-work`, `/sessions-dashboard/insights` | schema와 미준비/결과 없음 상태, 4개 폭 | Auto Work/Insight의 positive·busy/failed 결과 fixture. 새 계산·분석·추론은 미실행 |
| `/runs/synthetic-completed` | 보존된 Run과 완료 후 출력 없음, 4개 폭의 기본 순회 및 유효 task 유형의 1440/320 재확인 | 실제 running/cancel/error와 결과 artifact 재사용 전체 흐름 |
| Suspended Context Search / Drive | 기존 feature-assembly test로 default web/desktop의 제외·보존 경계 재검증 | 정지한 기능을 활성화하지 않음. 해당 화면 품질 평가는 대상 밖 |

OpenAPI/Swagger, static/API endpoints, 데이터에 없는 ID의 detail URL은 별도 제품
화면으로 순회하지 않았다. 같은 template의 route는 위 대표와 고유 상태로 묶었다.
이미 보류된 기능/추론/배포 acceptance를 이 조사로 재개하거나 승인하지 않는다.

## Verification And Development Direction

- `python -m unittest discover -s tests -p test_ui_contract.py -v`: **45 passed**.
- `python -m unittest discover -s tests -p test_feature_assembly.py -v`: **5 passed**.
- Web 순회의 240 관찰은 모두 HTTP 200으로 렌더됐다. 수집한 application Runtime
  exception은 없었다. 의도적으로 실패시킨 asset/network 요청은 정상 네트워크로 간주하지 않는다.
- 위 검사는 F1–F6이 남아 있는 소스에서도 통과한다. 정적 UI 계약·route 조합의 성공만으로
  초기 프레임·준비 상태·오류 의미가 검증되는 것은 아니라는 실제 근거다.
- 전체 Python suite는 실행하지 않았다. 제품 수정이 없는 조사이며 source 계약 검사와
  실제 browser/native-engine 관찰을 수행했다. 실제 Tauri·개인 데이터·외부 서비스의
  검증은 위 한계대로 남긴다.

개발 절차는 계획의 **합성 상태 선택 → navigation 전 기록 → 정상/지연/실패 분리 →
값·focus·scroll·history·binding 검증**을 유지한다. 이번 관찰은 다음 보완을 우선한다.

1. ready를 기다린 screenshot 외에, 첫 DOM/asset 초기화부터의 중간 상태를 반드시 채집한다.
   정상 속도에서 포착하지 못한 현상과 통제 지연에서만 나온 현상을 따로 기록한다.
2. 확인된 empty와 조회 실패, 모델 미준비, 완료 후 artifact 없음에 서로 다른 fixture와
   기대 문구/동작을 둔다. API 성공 여부만 확인하지 말고 category 이동 후의 표시도 검사한다.
3. 빈 fixture만 보지 않고 pin·긴 경로·실제 retained 상태가 있는 positive 사례를 넣는다.
   `scrollWidth`와 `clientWidth`, 실제 패널 경계를 함께 본다.
4. 상태·선택·최종 binding 등의 안정된 계약은 자동 guard 후보로 삼고, 자연스러운
   움직임/두 layer의 경쟁은 원속도·느린 재생의 시각 검토를 병행한다. 보편적 ms 기준이나
   모든 화면에 skeleton을 추가하는 규칙은 아직 채택하지 않는다.

이번에 사용한 계측·fixture·캡처 도구는 일회성 진단이다. 저장소의 새 QA 명령이나
정책 변경으로 설치하지 않았다. 장기적으로 실행할 공통 도구의 구현은 별도 작업이다.
임시 결과의 핵심 조건·수치·관찰은 이 문서에 옮겼으며, raw capture 경로를 durable
참조로 삼지 않는다. task-owned 서버·브라우저·WKWebView는 종료했고 임시 자료·진단
스크립트·probe binary·module cache는 삭제했다.

## First-Audit Review Boundary — 2026-11-01

우선 수정 후보는 **설정의 조회/실패/준비 상태(F1–F3)**, **첫 실행 asset 실패 복구(F4)**,
**긴 pin 경로 containment(F5)**, **Run 출력 없음의 의미(F6)**로 나눈다.
F4는 먼저 첫 활성 surface와 retry의 동작 계약을 정해야 한다. Chart fallback과
시각 보정은 정상 cold 환경의 추가 관찰 및 표현 방식 결정 뒤 별도로 판단한다.

이 조사로 구현을 시작하지 않는다. 다음 구현 요청에서는 이 발견을 해당 기존 계약과
승인 경계에 연결하고, 보고 사례·대표 consumer·실제 전달 host의 회귀 검사를 포함한다.
실제 Tauri의 입력/시작 전환과 위 표의 positive/active 상태가 확인되기 전에는
앱 전반이 자연스럽다는 최종 판정을 내리지 않는다.

## Repair Contract — 2026-11-02

사용자의 `리뷰대로 정리` 요청으로 F1–F6의 수정을 진행한다. 앞선 조사 기록은 당시의
증거로 유지한다. 이번 수정은 `frontend-product`/screen-alignment `extend`이며,
설정 UI → 첫 실행의 표시·복구 → Pinned containment와 Run 표시 순서로 처리한다.
기존 제품 경계 안의 보정이며 Feature/PRD의 승인·수락 상태를 새로 만들지 않는다.

- F1: 서버가 읽은 일반/동기화 값으로 초기 control을 채우고, 조회 진행은 고정 header
  안에 표시한다. 본문 앞에 로딩 box를 넣지 않는다. 재열기와 pending save 대기에서도
  본문 anchor·저장값·오류 안내를 보존한다.
- F2–F3: 읽기 오류는 category 이동으로 지우지 않고 재조회 경로를 둔다. `null`인
  profile registry를 empty로 해석하지 않는다. 모델과 검색의 확인된 상태에 따라
  버튼을 활성화하고, 초기/실패/회복·poll·연속 요청에서도 같은 준비 조건을 적용한다.
- F4의 spec 보완: setup 요청에는 JS 실행 전부터 서버가 렌더링한 준비 surface와
  현재 URL을 다시 여는 링크를 제공한다. 이 surface는 settings geometry/tokens를
  사용하고 배경은 계속 inert다. 실제 modal이 첫 step을 소유하면 준비 surface를
  제거한다. script가 실패해도 링크는 동작하며, setup/현재 범위를 보존한다.
  설정 완료 저장·skip·native 인증·일반 web의 비강제 onboarding은 유지한다.
- F5: 긴 pin 경로가 부모 grid를 넓히지 않도록 owning track의 최소 크기를 제한한다.
  전체 문서를 잘라내거나 경로·접근성 설명·pin을 제거하지 않는다.
- F6: 초기 HTML과 polling이 같은 Run 상태별 빈 출력 문구를 사용한다. 원문 output과
  lifecycle은 보존하며, 빈 출력을 이유로 job을 재실행하지 않는다.
- 검증: 합성 backend의 cold/warm/보류/실제 source 오류/asset 실패/retry,
  pending save·rapid response·모달 focus·wizard draft/reduced motion,
  `1440/920/700/320` 및 낮은 설정 창에서 확인한다. 의미 있는 자동 회귀 검사를
  남기고 기존 관련 검사·전체 Python suite·privacy 검사를 수행한다.
- 제외: Chart fallback·시각 보정 후보의 재설계, 실제 모델/agent/외부 작업,
  중단 기능 재개, 사용자 runtime 수정, 앱 rebuild/배포. 실제 Tauri의 추가 증거는
  별도로 남기며 source/격리 WKWebView 확인을 배포 앱 검증으로 확대하지 않는다.

수정과 재검증 결과는 이 절 아래에 기록한다.

## Repair Verification — 2026-11-02

F1–F6을 소유 구현에서 수정했다. 설정의 기존 크기·토큰·autosave·명시적 source Save와
wizard draft 계약을 유지하고, F4의 준비/실패 복구를
[Settings contract](../../policies/project/desktop-app-and-settings.md#first-use-setup)와
[Design Constitution](../../policies/design/design-constitution.md#dialogs-and-drawers)에 반영했다.
PRD/Feature의 승인·native acceptance를 변경하지 않는다.

| 항목 | 수정된 동작과 확인한 증거 |
| --- | --- |
| F1 | 초기 HTML의 일반/동기화 hidden value와 표시값을 서버 선호값으로 채웠다. 진행 표시는 고정 header에 둔다. Chromium의 보류→완료 첫 열기 15개 rAF 표본에서 heading Y=`236`으로 유지되고 표시값은 처음부터 `Local Context`/`Europe/Paris`였다. warm reopen, Cmd+, CPU `4×` + reduced motion에서도 anchor가 유지됐다. WKWebView의 first/warm 합계 24개 표본도 Y=`236`, 빈 label 0개였다. 이 표본 수는 paint 수나 인지 시간의 측정이 아니다. |
| F2 | 읽기 issue와 일시적 action 메시지를 분리해 category 이동에도 오류를 유지한다. `session_sources=null`은 읽기 실패로 표시하고 등록/수정 조작을 잠근다. 실제 합성 source TOML 파손 → 세션 category 이동 → 파일 복구 → 다시 불러오기로 기존 프로필 1개와 오류 해제를 확인했다. |
| F3 | 초기 HTML부터 모델 버튼을 잠그고 상태 문구를 제공한다. 확인된 모델·검색 상태와 진행 중 action에 따라 다시 계산한다. 최초 API 보류/실패/retry, 주기 조회 실패 후 잠금과 다음 정상 poll의 활성 회복을 확인했다. 조회 버전으로 오래된 결과의 덮어쓰기를 제한했다. ready는 합성 응답이며 실제 모델 다운로드·준비·검색 끄기는 실행하지 않았다. 역전 응답의 모든 조합은 검증하지 않았다. |
| F4 | JS 이전부터 같은 settings frame의 준비 surface와 현재 URL의 일반 reload 링크가 보인다. `settings.js` 실패 시 배경은 inert, 실제 modal은 닫힌 상태이며 링크는 setup/source 범위를 보존한다. script 허용 후 실제 링크 입력으로 modal이 열리고 준비 surface를 제거했다. wizard Back의 source draft와 reduced-motion 전환·배경 격리를 재확인했다. WKWebView도 `320px`에서 asset 차단/허용 후 복구·새 heading focus를 확인했다. |
| F5 | Pinned list와 content, 좁은 secondary grid의 최소 track 크기를 제한했다. 긴 합성 workspace 경로에서 `1440/920/700/320`의 문서 넘침과 패널 경계를 확인했다. `320px`의 document `scrollWidth=320`이며 패널도 viewport 안에 머문다. WKWebView `320px`도 문서 넘침이 없었다. 원문 경로·pin·accessibility label은 유지했다. |
| F6 | 공유 helper가 prepared/queued/running·cancelling/terminal의 빈 출력 문구를 만들고 초기 HTML과 status API가 이를 함께 쓴다. 9개 lifecycle 상태의 일치와 상태 불변을 확인했다. browser에서 queued→completed 시 준비 문구가 해제됐고, 실제 출력이 이미 표시된 뒤 빈 terminal 응답이 와도 기존 출력이 유지됐다. job을 재실행하지 않았다. |

### Executed Checks And Their Limits

- Source는 `b844ce8` 위의 이번 working-tree 변경, 앱 version `0.0.1`이다.
  별도 합성 web backend가 checkout의 template/static을 제공했다. Chromium은 캐시를
  끄고 새 profile에서 실행했다. 기존 `.app`의 bundled assets를 갱신한 검사가 아니다.
- `uv run python -m unittest discover -s tests -v`: **1,524 passed**.
  새 `test_ui_state_rendering.py`의 4개 검사는 초기 custom preference 값/잠금,
  setup URL 보존/격리, 9개 Run lifecycle의 HTML/API 일치, 실제 원문의 literal 표시를 검증한다.
- 첫 full-suite 실행에서는 Pinned CSS 선언 전체를 문자 비교하던 기존 검사와, 변경하지
  않은 Session 원본의 `st_atime` 차이 검사가 실패했다. 전자는 padding 소유 계약을
  그대로 확인하도록 기존 assertion을 조정했다. 후자는 관련 코드·테스트를 수정하지
  않았고 focused Session sync 27개와 최종 full-suite에서 통과했다. 최초의 일시 실패를
  숨기거나 UI 수정으로 ingestion 회귀를 고쳤다고 해석하지 않는다.
- `node scripts/qa-ui-states-browser.mjs`: **PASS**, 62개 assertion.
  Node `24.15.0`, Chrome `156`, macOS `26.5.1`, Python `3.11.15`에서 실행했다.
  이 수는 반복 focus 입력·폭별 containment도 포함하므로 62개 독립 사용자 시나리오나
  전 앱 통과 수가 아니다. `1440/920/700/320×900`, 추가 `701×400`에서 확인했다.
  펼친 preference 메뉴/메뉴 Escape, dialog Escape의 trigger focus 복귀, 낮은 창의
  본문 마지막 도움말 접근을 포함하며 application Runtime exception은 0개였다.
- WKWebView의 별도 비영구 AppKit 창은 **4개 사례 PASS**다. 위 first/warm frame,
  `320px` 긴 pin/설정, setup asset 실패, 복구된 wizard의 격리·focus를 확인했다.
  이번 probe는 합성 **web backend**와 DOM script 입력을 사용했다. 첫 조사 때의
  desktop 인증 handshake 재검증이나 실제 Tauri·OS menu·물리 입력·VoiceOver가 아니다.
- `node --check`의 settings.js/app.js/새 QA script와 repository privacy 검사,
  `git diff --check`가 통과했다. 정적 검사만으로 전환 품질을 판정하지 않았다.
- 설정의 pending/오류와 첫 실행 실패 capture를 실제로 비교했다. 준비 surface는
  기존 settings geometry/scrim/type token을 사용하며, 새 색·모션·breakpoint를 도입하지 않았다.
  새 준비 표시가 창 전체의 백색 flash를 해결했다거나 모든 중간 paint가 자연스럽다고 확대하지 않는다.

### Repeatable Development Check

[Browser command](../../../scripts/qa-ui-states-browser.mjs)와
[synthetic backend](../../../tests/ui_state_fixture.py)를 저장소에 남겼다.
[Developer Guide](../../policies/project/developer-guide.md#verification)가 실제 실행 조건,
격리된 runtime/profile, 출력 보존과 정리 절차를 소유한다. bundled
[Settings guide](../../../src/localbrain/content/docs/settings.md)에는 읽기/모델 상태 실패와
재조회 절차를 반영했다. 공통 skeleton framework나 모든 화면의 고정 screenshot 체계는 아니다.

개발 때 관련 변경의 안정된 계약은 이 명령으로 반복하고, 새로운 화면·지연·오류 상태는
상위 계획의 matrix에 추가한다. 최종 화면만 기다리지 않고 navigation 전 계측을 시작하며,
정상·통제 지연·실패를 구별하고 값·focus·scroll·history·binding과 시각 흐름을 함께 본다.

### Remaining Review Boundary

- **기존 앱에 반영하려면 별도 rebuild/교체·재시작 검증이 필요하다.** 이번 요청에서는
  `.app`/ZIP을 변경하거나 배포하지 않았다. 소스 서버의 결과를 설치 앱 결과로 해석하지 않는다.
- Chart 초기 fallback과 ISO→지역 시각 보정은 앞선 관찰·표현 결정 대상으로 남는다.
  첫 조사에서 남긴 positive/active 모델·Atlassian·Auto Work·Insights 등의 coverage도 유지한다.
- 실제 Tauri first/retained launch·menu/shortcut·native chooser·접근성과 역전 응답/저장
  conflict의 전 조합은 미검증이다. 이 6개 수정으로 broader graphical matrix를 완료하지 않는다.
- 이번 task의 합성 backend·Chrome·WKWebView를 종료하고 runtime/profile/captures,
  진단 script·probe binary·module cache와 task-owned WebKit rule을 정리했다. 관찰의
  핵심 수치·조건은 위에 남기며 durable 링크는 임시 결과 경로에 의존하지 않는다.

## QA Closeout — 2026-11-04

세션 마무리 검토에서 재열기 anchor 검사가 표본 0개나 1개로도 통과할 수 있던
oracle 결함을 보완했다. 이것은 과거 UI 재발이나 과거 실행의 표본 누락을 입증하지
않는다. 고정된 계측 종료 시간 대신 해당 관찰을 명시적으로 종료하고, 첫 열기와
CPU4 단축키의 보류·완료 단계가 실제 표본에 모두 나타나야 비교한다. 재열기도
복수 표본과 완료 단계 관찰을 기다린다. 세 경로의 표본을 JSON report에 보존한다.
여기서 재열기는 네트워크 캐시를 끈 같은 페이지에서 이미 읽은 설정 상태를 재사용하는
검사이며, 계획의 캐시 사용 재방문은 별도 조건이다.

- 보완된 합성 Chromium 회귀 명령: **62개 assertion PASS**, application Runtime
  exception 0개. 첫 열기 10개(보류 8·완료 2), 재열기 2개(보류 1·완료 1),
  CPU4 + reduced-motion 단축키 3개(보류 2·완료 1)에서 각 heading Y의 범위는 `0px`였다.
  각 표본의 시각은 서로 다르며, 표본 수는 독립 시나리오·paint 수나 인지 시간 측정이 아니다.
- 현재 전체 Python suite: **1,524 passed**. 최초 기본 sandbox 실행은 uv 공유 캐시
  접근과 합성 backend의 loopback bind가 차단되어 시작하지 못했다. 같은 기존 캐시와
  분리된 합성 backend를 허용된 실행 환경에서 사용해 위 검사를 완료했다.
- 이번 QA 보완은 기존 합성 backend·프로필·개인 데이터 격리 경계를 유지한다.
  실제 Tauri, WKWebView의 새 실행, 설치 앱 rebuild나 앞 절의 남은 positive/active
  matrix 검증을 수행한 것은 아니다. 공통 지침의 효과 비교도 수행하지 않았다.

코드 검토에서 F3의 의존성 결합 두 가지를 추가로 재현하고 수정했다. 검색 상태 응답만
보류해도 일반·동기화·source·Context와 독립 모델 다운로드가 잠겼고, Storage 조회 중
Search로 이동하면 확인된 모델의 취소도 잠겼다. 설정 응답은 검색 상태와 독립적으로
반영하고, 모델 명령의 진행 상태는 다른 설정 작업과 분리했다. 검색 준비가 실제로
필요한 버튼과 모델 명령끼리의 중복 조작은 계속 제한하며 응답 버전 검사를 유지한다.
실제 모델 작업은 실행하지 않았다.

- 수정 전 합성 browser에서 두 선택 지연 사례의 실패를 각각 확인했다.
  수정 후에는 동일한 두 조건을 반복 가능한 QA 명령에 포함해 **66개 assertion PASS**,
  Runtime exception 0개를 확인했다. 첫 열기 9개(보류 7·완료 2), 같은 페이지 재열기
  2개(보류 1·완료 1), CPU4 단축키 3개(보류 2·완료 1)의 heading Y 범위는 각각 `0px`였다.
  앞서 기록한 62개 검사와 표본은 그 이전 실행이며 이번 수치로 소급 대체하지 않는다.
- 검색 상태만 보류하는 동안 확인된 일반·동기화·source·Context·모델 다운로드는
  사용 가능했고, 검색 준비 버튼은 잠긴 상태였다가 해당 응답 후 활성화됐다.
  Storage 응답 보류 중에도 합성 active-download의 취소 버튼은 보이고 사용 가능했다.
  모든 역전 응답·generation 모델·실제 다운로드의 검증으로 확대하지 않는다.

동일 원인의 후속 consumer도 확인했다. 검색 요청의 진행 상태를 일반 설정 읽기와
분리해, 응답 대기를 실패 문구나 불필요한 retry로 표시하지 않는다. 모델 명령의
확인 응답 뒤에는 background 조회가 끝나기 전에도 확인된 취소를 사용할 수 있다.
모델 poll 실패는 검색 응답이 보류돼 있어도 모델 조작을 즉시 잠그고 다음 정상 poll로
회복한다. 모델 명령의 busy는 그 명령의 응답까지이며, 모델·검색 읽기는 각각의
응답과 버전으로 반영한다.

- 최종 후보에서 **Python 1,524개 PASS**, 합성 Chromium **70개 assertion PASS**,
  Runtime exception 0개를 재확인했다. 첫 열기 10개(보류 8·완료 2), 같은 페이지
  재열기 2개(보류 1·완료 1), CPU4 단축키 3개(보류 1·완료 2)의 Y 범위는 각각 `0px`였다.
- 검색만 보류했을 때는 확인 중 문구와 숨겨진 retry, 합성 모델 명령의 확인 뒤에는
  검색 갱신 대기 중에도 사용 가능한 취소를 관찰했다. 모델 poll의 독립 실패·회복도
  확인했다. 모델 명령은 browser에서 합성 응답으로 가로채 실제 backend job을 만들지 않았다.
- 실제 세 anchor assertion에 빈/단일 표본, 필요한 단계 누락, 위치 이동, 정상 보존의
  양성·음성 입력을 넣은 별도 14개 oracle 검사가 통과했다. 이 수는 70개 browser assertion에
  포함되지 않으며 실제 paint·모든 상태/응답 순서·native·generation 모델을 검증하지 않는다.
- 다음 poll 회차를 예약하는 기존 제어는 검색 응답 종료도 기다린다. 이번 수정은
  시작된 읽기 응답의 개별 반영과 확인된 모델 명령의 조작 가능성을 검증한 범위다.
  끝나지 않는 검색 요청에서 poll 스케줄 자체를 분리하는 변경은 수행하지 않았다.
