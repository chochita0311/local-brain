# PRD-0019: Observed Session Chart

## Metadata

- ID: `prd-0019`
- Status: `approved`
- Owner role: `human`
- Created: `2026-10-06`
- Updated: `2026-10-12`

## Request Summary

Sessions에서 `List/Chart`를 전환해 전체 세션 기록을 시간에 따라 탐색한다. 첫 Chart는 추론을 넣지 않고 관측된 시각과 원래 세션을 보여줘, 실제 화면을 본 뒤 필요한 추론을 판단할 수 있게 한다.

## Source Set

- Human request: 기존 List 보존, Chart의 Pinned Sessions 열 제거와 전체 본문 폭 사용, 기존 `작업 흐름` 보존, 자동 작업 제외, 추론 없는 첫 화면을 확인한 뒤 다음 방향 결정. 2026-10-06에 PRD 작성과 이 범위의 진행을 명시적으로 요청했다.
- Directional reference: 사용자가 지목한 Chochita Archive의 Andromeda collection. 점과 작은 카드, 선택 강조, 선택 고정, 화면 이동과 확대·축소의 형식만 참고한다.
- Interaction reference: 앞선 버전에서 사용자가 승인한 Obsidian Graph view의 장력 느낌. 현재 버전은 사용자가 다시 지정한 실행 폴더별 행과 브랜치 가지를 우선하며, 당김은 해당 가지 안의 작은 임시 움직임으로 제한한다.
- Design authority: [Design Constitution](../../policies/design/design-constitution.md), [Design Evaluation](../../policies/design/design-evaluation.md), [Interaction Evaluation](../../policies/experience/interaction-evaluation.md).
- Product and implementation: [Session inventory](../../policies/project/product.md#application-navigation-and-session-inventory), `sessions.html`, `queries.py`, Session 상세의 기존 navigation 상태.

## Product Intent

최근 목록에서 세션 하나를 찾는 방식에 시간 기반의 넓은 관찰 화면을 더한다. 실행 경로와 브랜치는 과거 관측값으로 읽으며, 같은 업무나 프로젝트를 뜻하는 분류로 사용하지 않는다. 세션 상세로 진입하고 돌아왔을 때 탐색 위치를 잃지 않는다.

## Confirmed Scope

- `세션 타임라인`과 `가장 최근 활동 기준` 설명 자리를 구분선 없는 두 칸 `List/Chart` 전환으로 바꾼다. 소스 필터의 전체 이름은 `All`로, 선택되지 않은 인접 소스 사이 구분선은 Sessions Dashboard와 동일하게 맞춘다. List의 행, 정렬, 페이지, 소스 범위, 핀, Subsession 동작을 보존한다.
- Chart는 같은 소스·workspace 조건에 맞는 모든 기본 작업 세션을 대상으로 한다. List의 현재 페이지나 연령 제한으로 차트를 자르지 않는다.
- Chart에서는 오른쪽 Pinned Sessions 및 그 열의 공간을 제거해 전체 본문 폭을 사용한다. 선택 정보는 떠 있는 작은 카드로 제공하며 좁은 화면에서는 차트 아래에 배치한다.
- 세션 노드에 마우스를 올리거나 키보드로 초점을 주면 원래 소스·제목·관측 시각·실행 경로·기록된 브랜치·핀 상태와 겹친 세션 수를 임시 설명으로 표시한다. 노드·설명 상자·둘 사이의 마주 보는 면을 잇는 이동 구간을 하나의 호버 영역으로 유지하며, 그 영역과 키보드 초점에서 벗어나면 기존 120ms 상태 반응 시간 후 닫는다. 재진입하면 닫기를 취소한다. 기존 정보 색상으로 호버 배경·테두리를 강화하되 소스 색·핀 표시는 유지한다. 노드 클릭·탭·키보드 활성화는 설명을 선택 상태로 고정하며 같은 노드 재활성화나 빈 캔버스 클릭, 닫기, Escape로 해제한다. 다른 노드의 임시 설명은 고정 설명과 활동을 바꾸지 않는다. 임시 카드는 좁은 화면에서도 레이아웃을 밀지 않고 노드 옆 또는 위아래에 표시한다. 상자 안에서는 글 선택·로컬 스크롤과 키보드 초점을 지원하고 Escape로 닫는다. 글 클릭은 세션을 고정하지 않으며 새 설명은 내부 스크롤을 맨 위로 돌린다. 이동 구간에 보이지 않는 입력 영역을 깔지 않아 빈 캔버스 클릭·드래그는 유지하고, 빈 클릭은 고정된 세션이 없어도 임시 설명을 닫는다. 모든 취소 경로에서 지연 콜백도 정리한다. 겹친 점의 정확한 세션 선택·활동·상세 동작은 고정 설명에서 제공한다. 호버는 카메라·배율·저장 상태를 바꾸거나 활동을 조회하지 않는다. 축소된 화면에서도 임시 설명은 읽기 크기로 표시하며 활성화하면 기존 읽기 확대를 유지한다. 넓은 고정 카드가 클릭한 점을 가리는 경우에만 시간 위치를 조정해 재클릭이 가능하게 한다. 해제 직후 정지한 포인터 밑에 다른 점이 놓여도 설명을 다시 열지 않으며 실제 포인터 이동 후 호버를 재개한다. 드래그와 클릭은 구분한다.
- 각 세션의 최근 관측 시각을 가로축에 놓고, 세로축은 세션에 기록된 실행 폴더 하나를 한 프로젝트 행으로 사용한다. 폴더는 문자열 정규화만 하며 Git root, 제목, 실제 작업 내용으로 합치지 않는다. 프로젝트명 대소문자 무시 순, 같은 이름은 전체 경로 순으로 고정하고 경로 없는 행은 마지막에 둔다. 같은 표시 프로젝트 집합에서는 기준 좌표를 유지하고, 확대·축소는 화면 투영 배율을 바꾼다. 프로젝트를 숨기면 남은 행의 빈 공간을 접는다.
- 폴더 안에서 세션에 기록된 브랜치명으로 가지를 나눈다. 정확한 `HEAD` 값은 체크아웃 참조이므로 가지 이름에서 제외하며 원본 메타데이터에는 그대로 보존한다. `HEAD`와 브랜치 미기록만 있는 폴더는 빈 기준선이나 별도 가지 없이 한 줄로 표시한다. 실제 브랜치명이 관측되면 master를 기준으로, 없으면 main을 기준으로 사용한다. 실제 브랜치명은 있지만 둘 다 없으면 중립 기준선이며 브랜치를 만들어 기록하지 않는다. 나머지 가지는 브랜치명 순이다. 이름 있는 브랜치와 섞인 `HEAD`·미기록 세션은 같은 브랜치 없음 줄로 접근 가능하게 하며 master/main으로 배정하지 않는다. 현재 폴더의 Git 상태를 조회하거나 과거 상태를 추론하지 않는다.
- 각 가지는 해당 브랜치 세션들의 가장 이른 유효 메타데이터 관측 시각에서 시작한다. 유효한 메타데이터 시각이 하나도 없는 세션은 저장된 Event 시각을 사용한다. 사용자가 명시적으로 선택한 세션 관측도이며 실제 Git 분기·병합 이력을 뜻하지 않는다. 가지 선은 배치 가이드로서 연속 작업 시간, 세션 간 계보, 완료나 병합을 나타내지 않는다. 시각을 확인할 수 없는 세션은 별도로 접근 가능하게 한다.
- 점을 당기면 해당 가지 안에서 작은 저항감과 주변 점 반응을 보이고 놓으면 기준점으로 복귀한다. 당기는 동안 기준 시각 위치를 표시하며 임시 움직임은 관계·배치 저장·관측 시각 변경을 만들지 않는다. 동작 줄이기 설정에서는 주변 반응과 복귀 애니메이션을 생략한다. 같은 가지에서 화면상 겹친 점은 개수와 선택 목록으로 모든 원래 세션에 접근하게 한다.
- 선택한 세션의 저장된 Event 시각들을 확인할 수 있다. 관측 공백은 연속 작업 시간이나 휴식으로, 세션 종료는 업무 완료로 해석하지 않는다.
- 프로젝트 체크박스 필터는 도표 위 도구 모음 왼쪽의 기존 날짜 이동 자리에 두며 개별 표시·숨김과 전체 선택을 제공한다. 소스·워크스페이스별 표시 선택은 LocalBrain의 private DB에 저장하고 같은 DB를 사용하는 브라우저들에서 복원한다. 브라우저 사이트 데이터 삭제로는 확인된 선택이 사라지지 않으며 DB 손실은 백업 복구나 재선택이 필요하다. DB 설정이 없을 때 기존 브라우저 선택, 다음으로 탭 표시 상태를 create-if-absent 방식으로 이전한다. DB의 전체 선택도 오래된 브라우저 숨김보다 우선한다. 잠시 사라진 숨김 폴더 키는 보존한다. 화면 위치·선택 세션·세로 배율은 탭 상태로 남고, 표시 설정의 조회·저장 실패에는 실제 재시도 경로를 보이며 필터는 계속 동작한다. 필터는 로컬 표시 상태이며 기록 삭제·분류나 기존 List 필터 변경이 아니다. 숨긴 프로젝트의 선택과 활동은 해제하고 상세 복귀에는 표시 선택도 유지한다.
- Chart에서 기존 핀 상태를 소스 색과 구분되는 정적인 테두리·광륜과 기존 핀 모양으로 표시한다. 겹친 점은 하나라도 핀이 있으면 표시하고 접근 가능한 이름에 핀 개수를 포함한다. 선택 목록과 미리보기는 각 원래 세션의 실제 핀 상태를 표시하며 날짜 없는 핀 세션도 접근 가능하다. 핀 상태를 새로 변경하는 동작은 추가하지 않는다.
- 하단의 전체·현재 화면·프로젝트 개수, 정렬·첫 관측 설명과 조작 안내를 제거한다. 날짜 없는 세션과 조회 오류의 실제 복구 경로는 유지한다.
- 브랜치 줄과 프로젝트 머리 영역의 간격을 줄인다. 기본 확대·축소는 시간과 세로 투영 모두에 적용하고 전체 보기는 선택된 프로젝트와 전체 관측 기간을 캔버스 안에 맞춘다. Cmd/Ctrl+Shift 스크롤은 마우스 시점을 기준으로 가로 시간축만 조절하며 세로 배율·위치를 유지한다. Shift 스크롤은 가로 이동이고, 세로 휠 입력과 이미 가로로 전달된 입력을 모두 지원한다. 화면 안에 전 기간이 맞춰졌거나 날짜 끝에서는 이동이 제한된다. 작은 개요에서도 브랜치 글자는 숨기지 않고 세로 배율에 맞춰 글자·행 높이·세로 여백을 함께 줄인다. 프로젝트 이름도 같은 배율로 줄여 첫 브랜치를 덮지 않으며, 고정 축 폭·가로 여백·읽기 크기의 토큰·전체 이름 title은 유지한다. 전체 보기의 글자는 작아질 수 있지만 임의의 생략 기준은 넣지 않는다. 프로젝트 경로·혼잡한 세션 제목·고정 미리보기의 기존 생략 정책은 유지하며 프로젝트나 세션을 선택하면 읽기 크기로 돌아온다. 가로 전용 줌은 글자 크기를 바꾸지 않는다. 색에만 의존하지 않는 선택과 키보드 접근을 유지한다.
- 가로 이동의 경계는 표시된 프로젝트들의 첫·마지막 관측 시각과 선택해 불러온 활동 시각으로 계산한다. 가장 오래된 프로젝트를 숨기면 다른 표시 관측이 그 경계를 유지하지 않는 한 왼쪽 시작점이 당겨진다. 끝에 붙은 카메라는 새 끝점에, 전체 시간 보기는 새 기간에 맞추며 중간 카메라는 시점을 보존하고 새 범위 안으로 제한한다. 양끝은 가운데 정렬된 40px 대상의 폭까지 고려해 같은 64px 여백을 예약하며 좁은 화면에서는 사용 가능한 폭의 20%와 대상 주변 공간으로 제한한다. 기존 읽기 배율 상한 때문에 짧은 기간은 오른쪽에 더 남을 수 있다. 가지 끝도 화면 여백을 유지한다. 빈 곳 드래그는 최대 80px, 좁으면 사용 가능한 폭의 절반까지 더 늘어나며 끝에서 저항을 주고 놓으면 범위 안으로 복귀한다. 동작 줄이기에서는 즉시 복귀한다. 도구 모음의 날짜 범위와 좌우·상하 이동 버튼은 제거하고, 시간 축 날짜·드래그·키보드 탐색·확대 축소·전체 보기·선택 이동과 원래 상세 진입·복귀를 유지한다.
- LocalBrain의 shell, 디자인 토큰, 소스 표시를 사용한다. 참고 화면의 배경·색·폰트·장식과 가상 내용은 가져오지 않는다.
- 스크립트 실패·미사용, 빈 범위, 시각 없음, 활동 조회 실패, 사라진 세션에서도 기존 List와 상세로의 접근을 유지한다.

## Excluded Scope

- Session 상세의 `작업 흐름` route, Episode·관계·Trace·교정 동작 변경.
- 자동 작업 재개, 유사 묶음, 모델 실행, embedding, 작업 구간 분석, 세션 간 후속·분기·병합 관계 생성.
- 경로·브랜치·제목·참조자료를 사용한 업무 소속 추론 또는 새로운 사용자 조직.
- 원본 세션 파일, 저장된 메타데이터, Workstream/Thread 및 기존 관측 기록의 수정. Schema 변경은 사용자가 추가 승인한 프로젝트 표시 설정 전용 테이블에 한정한다.
- 클라우드 전송, 새 외부 dependency, 브라우저 방문에 따른 수집·동기화.

## Uncertainty

첫 화면을 본 뒤 어떤 연결·분류·작업 구간 분석이 유용한지 결정한다. 이 항목은 후속 범위이며 첫 Chart를 막지 않는다. 단일 세션에 여러 작업이 섞여 있거나 서로 다른 실행 위치에서 같은 목표를 다뤘다는 이유로 첫 버전이 관계를 만들어서는 안 된다.

## Constraints

- 관측 시각과 실제 업무의 진행·완료 상태를 분리한다.
- 선택한 프로젝트의 화면 밖 세션을 임의의 상한으로 제외하지 않는다. 프로젝트 숨김은 사용자의 표시 선택이며 기록 삭제나 업무 추론을 만들지 않는다.
- 카메라·선택 세션·세로 배율은 브라우저 탐색 상태다. 프로젝트 숨김은 독립된 로컬 DB 표시 설정으로만 저장하며 새로운 업무 identity나 관측·분류 기록을 만들지 않는다. 저장 응답 전에 닫힌 화면의 미확인 선택까지 저장됐다고 주장하지 않는다.
- private runtime 내용, 실제 세션 제목·경로·스크린샷은 tracked 산출물에 넣지 않는다. 검증 산출물은 task-owned 임시 위치에 두고 종료 시 정리한다.

## Acceptance Envelope

R11 replaces immediate node exit and pointer-inert cards with continuous node,
card and facing-edge passage ownership. Pointer reading, local scrolling and
keyboard focus keep the temporary description available; leaving both owners
closes it after native grace, and reentry cancels that exit. Card input does not
hold selection or intercept blank canvas gestures. New descriptions reset their
internal scroll. Cancellation clears pending callbacks.

R10 adds temporary original-metadata hover/focus descriptions and stronger native
hover feedback. Activation holds selection; same-node or blank activation releases
it. Another transient description leaves the held card/activity in place. Hover
never changes projection or saved selection and remains available in overview.
Narrow cards overlay without reflow; stationary-pointer reprojection does not
immediately reopen a dismissed description. Exact-member access stays in the held
preview. Producer, metadata and frozen work boundaries remain.

R9 retains branch labels at every vertical projection scale, shrinking their
typography/boxes and Project-name typography with the rows. It replaces the
previous branch-label omission policy; existing focus restores reading scale.

The owner-approved R8 correction excludes exact `HEAD` from branch names only
in Chart layout. HEAD-only, missing-only and mixed HEAD/missing folders share one
line without an empty baseline. Named-branch folders retain their established
guides, with HEAD/missing on one unassigned track. Original branch metadata remains
visible and unchanged; no current or historical repository state is inferred.

The owner-approved R7 input refinement retains Cmd/Ctrl-wheel and visible
buttons as whole-chart zoom, accepts both Shift-wheel input forms for horizontal
movement, and adds Cmd/Ctrl+Shift-wheel horizontal-only zoom. Vertical scale and
position remain stable during that gesture; existing visible-time bounds and
tab navigation restoration apply.

List의 기존 사용 방식과 작업 흐름이 보존되며, Chart는 전체 폭에서 모든 일치 세션의 관측 시각을 탐색하게 한다. 선택·활동 시점·상세 복귀가 동작하고 날짜 없음과 오류가 접근을 막지 않는다. 어떤 세션 간 업무 관계도 추론하지 않으며 desktop 및 320px에서 native 디자인과 접근을 유지한다.

## Candidate Features

- [FEAT-0114: Observed Session Chart](../feature/feat-0114-observed-session-chart.md): 기존 inventory 안의 List/Chart 전환, 관측 시각, 선택 활동과 상세 복귀.

## Continuity Notes

- `2026-10-12`: 사용자는 현재 구현까지를 1차 작업의 마무리 지점으로 보고, 이번 세션의 UI·UX 평가에서 공통화할 요소를 ai-assets 기준으로 검토하도록 요청했다. 첫 검토는 제안 단계였으며 공통 패키지 변경을 승인하지 않았다. 이후 사용자가 subagent 반영, 두 정책의 구성 검토, 저장소 전체 문서 검토·확인·commit·push를 명시적으로 요청해 신규 기준 4개와 기존 기준 보강 3개가 ai-assets [커밋 3dfcc36](https://github.com/chochita0311/ai-assets/commit/3dfcc36bd91e6f2c2461fe91d8f387dfca2ca17b)에 반영·게시됐다. LocalBrain 문서 960개의 전체 내용 검토와 현재 구현의 마무리 확인도 완료했다. 구현·평가 기록의 부분 증거 범위와 후속 화면·추론 작업의 별도 승인 경계는 유지한다.

- `2026-10-09`: 사용자는 노드에서 설명 상자로 이동하면 바로 닫히는 동작을 지적하고 호버 유지 영역을 요청했다. [SPEC-0114-R11](../spec/spec-0114-r11-session-chart-hover-region.md)와 [RUN-151](../run/run-20261009-151-session-chart-hover-region.md)로 노드·상자·이동 구간의 연속 영역과 짧은 닫기 유예를 적용한다. 상자의 읽기·내부 스크롤·키보드 초점은 허용하며 세션 고정과 캔버스 조작은 분리한다. 관측·저장·기존 작업 경계는 유지한다.

- `2026-10-08`: 사용자는 노드 호버 설명과 더 선명한 강조, 클릭 고정 및 같은 노드·빈 곳 클릭 해제를 요청했다. [SPEC-0114-R10](../spec/spec-0114-r10-session-chart-hover-preview.md)와 [RUN-150](../run/run-20261008-150-session-chart-hover-preview.md)로 표시 상호작용만 확장했다. [EVAL-0114-R10](../evaluation/eval-0114-r10-session-chart-hover-preview.md)에 포인터·키보드·겹친 세션, 1440/320px 및 축소 상태의 제한된 브라우저 관찰을 기록한다. 기존 List·작업 흐름과 중단된 자동 작업, 관측 데이터·프로젝트 저장 경계는 유지하며 R7 실제 기기 휠 확인은 남는다.

- `2026-10-07`: R9를 현재 앱에 반영했다. [EVAL-0114-R9](../evaluation/eval-0114-r9-session-chart-scaled-branch-labels.md)에 50% 축소·전체 보기의 글자 유지와 비례 축소, 머리 영역과 브랜치 분리, 1440/320px 및 읽기 크기 복귀 관찰을 기록했다. 전체 보기의 작은 글자는 의도한 축소 결과이며 기존 확대·프로젝트 선택으로 읽기 크기를 회복한다. 자동 회귀나 기기·다른 배율 전체의 검증은 주장하지 않는다.

- `2026-10-07`: 사용자는 축소 중 사라지는 브랜치 표시를 함께 축소하도록 요청했다. [SPEC-0114-R9](../spec/spec-0114-r9-session-chart-scaled-branch-labels.md)와 [RUN-149](../run/run-20261007-149-session-chart-scaled-branch-labels.md)로 브랜치 글자 생략 조건을 없애고 행·글자 크기를 함께 조정한다. 프로젝트 이름도 함께 줄여 브랜치를 덮지 않도록 하며 데이터·R8 HEAD 규칙과 기존 작업 경계는 유지한다.

- `2026-10-07`: R8 표시 규칙을 현재 앱에 반영했다. [EVAL-0114-R8](../evaluation/eval-0114-r8-session-chart-head-reference-tracks.md)에 보고된 폴더의 한 줄·원래 세션 접근·원본 HEAD 표시와 1440/700/320px 관찰을 기록했다. 다른 메타데이터 조합은 소스 검토 범위이며 자동 회귀나 과거 Git 상태의 증거로 주장하지 않는다. 다음 사용자 검토는 수정된 줄 구성이며 R7의 실제 기기 확인은 계속 남는다.

- `2026-10-07`: 사용자는 `HEAD`와 미기록으로만 구성된 폴더에 빈 기준선까지 생성된 표시 오류의 정정을 승인했다. [SPEC-0114-R8](../spec/spec-0114-r8-session-chart-head-reference-tracks.md)와 [RUN-148](../run/run-20261007-148-session-chart-head-reference-tracks.md)로 `HEAD`를 가지 이름에서 제외하고 해당 폴더를 한 줄로 모은다. 실제 브랜치가 있는 폴더의 관측 가지와 원본 메타데이터·기존 작업 경계를 유지한다.

- `2026-10-07`: R7 단축키를 현재 앱에 반영했다. [EVAL-0114-R7](../evaluation/eval-0114-r7-session-chart-wheel-controls.md)에 가로 Shift 입력이 무시되던 이전 경로의 재현, 두 입력 형태의 이동, 가로 줌의 세로 위치·배율 유지, 새로고침·폭 변경·List 복귀와 700/320px 확인을 기록했다. 실제 마우스·OS 변환의 원인 확정은 아닌 브라우저 입력 검증이며, 다음 사용자 확인은 본인 기기의 두 조작이다.

- `2026-10-07`: 사용자는 Shift 스크롤이 동작하지 않는다고 보고한 뒤 확인과 Cmd+Shift 스크롤의 가로 간격 조절을 명시적으로 승인했다. [SPEC-0114-R7](../spec/spec-0114-r7-session-chart-wheel-controls.md)와 [RUN-147](../run/run-20261007-147-session-chart-wheel-controls.md)로 두 휠 입력 형태를 지원하고 세로 배율·위치를 유지하는 가로 줌을 진행한다. 기존 Cmd 스크롤·버튼의 전체 줌과 저장·관측·작업 경계는 유지한다.

- `2026-10-07`: 브라우저 사이트 데이터를 지우면 선택이 사라진다는 설명 후 사용자가 LocalBrain 자체 DB 저장을 승인했다. 표시된 프로젝트의 관측 시각으로 경계를 좁히는 동작을 유지하며 양끝 여백과 장력 구간도 늘린다. [SPEC-0114-R6](../spec/spec-0114-r6-local-chart-preferences-and-pan-space.md)와 [RUN-146](../run/run-20261007-146-local-chart-preferences-and-pan-space.md)로 전용 표시 설정 테이블·로컬 저장 API·화면의 승인된 확장을 진행한다.
- `2026-10-07`: 도구 모음·핀 표시 수정을 기존 로컬 Chart에 반영했다. [EVAL-0114-R5](../evaluation/eval-0114-r5-session-chart-controls-and-pins.md)에 새 문서의 프로젝트 선택 복원, 기존 핀 표시와 겹친 점의 개별 핀 상태, 제어된 이전·저장 차단, List·소스·상세 복귀와 1440/700/320px 확인을 기록했다. 실제 브라우저 프로세스 재시작·OS·기기·자동 회귀 검증은 주장하지 않는다. 다음 사용자 검토는 도구 모음 배치와 핀 가독성이다.
- `2026-10-07`: 사용자는 프로젝트 필터를 날짜 이동 자리로 옮기고 방향 버튼과 날짜 범위를 없애며, 종료 후 표시 선택 기억, Chart 핀 표시와 토글 구분선 수정을 요청했다. [SPEC-0114-R5](../spec/spec-0114-r5-session-chart-controls-and-pins.md)와 [RUN-145](../run/run-20261007-145-session-chart-controls-and-pins.md)로 승인된 프런트엔드 범위를 진행한다. 기존 sessionStorage 선택은 탭에 한정됐으므로 영구 브라우저 선택과 구분해 이전한다. 기존 관측·List 행·작업 흐름·자동 작업 경계는 유지한다.
- `2026-10-06`: 사용자는 하단 개수·정렬 설명·조작 안내 제거, 체크박스 프로젝트 필터, 날짜 끝의 장력 제한, 좁은 브랜치 간격과 세로까지 축소되는 전체 보기를 요청했다. [SPEC-0114-R4](../spec/spec-0114-r4-filtered-session-chart-overview.md)와 [RUN-144](../run/run-20261006-144-filtered-session-chart-overview.md)로 승인된 프런트엔드 수정 범위를 진행한다. 고정 세로 간격과 시간만 축소하는 이전 동작을 대체하며 관측 데이터 계약과 List·작업 흐름·자동 작업 경계는 유지한다.
- `2026-10-06`: 필터·개요 보기 수정을 기존 로컬 Chart에 반영했다. [EVAL-0114-R4](../evaluation/eval-0114-r4-filtered-session-chart-overview.md)에 프로젝트 숨김·전체 선택, 전체 높이 축소, 작은 점·프로젝트의 읽기 크기 복귀, 날짜 양 끝의 실제 드래그·복귀와 상세 상태 복원을 기록했다. 1440/700/320px 화면과 축소된 마지막 라벨의 잘림을 확인·수정했다. 자동 회귀와 실제 기기·OS·대규모 검증은 주장하지 않으며 다음 사용자 검토는 필터 접근·개요 가독성·장력이다.

- `2026-10-06`: 앞선 구성 논의의 경계에 대해 사용자가 PRD 작성과 진행을 명시적으로 승인했다. 구현 및 로컬 검증까지 진행하며, 실제 화면 검토에서 후속 추론을 결정한다. 자동 작업의 중단 상태와 기존 작업 흐름의 승인 범위는 변경하지 않는다.
- `2026-10-06`: 첫 Chart를 구현해 기존 로컬 서버에 반영했다.
  [EVAL-0114](../evaluation/eval-0114-observed-session-chart.md)에 실제 화면과
  복귀·오류 안내 확인, 자동 회귀 및 기기 조작 검증의 미실행 범위를 기록했다.
  사용자 화면 검토와 후속 추론 범위 결정은 남아 있다.
- `2026-10-06`: 첫 화면 검토 후 사용자가 시간 가로축, 고정된 불규칙 세로 배치와 점을 당겼다 제자리로 돌아오는 상호작용을 승인했다. [SPEC-0114-R2](../spec/spec-0114-r2-stable-session-constellation.md)와 [RUN-142](../run/run-20261006-142-stable-session-constellation.md)로 이 변경을 진행한다. 첫 실행의 관측 데이터 계약과 List/Workflow Focus 보존 경계는 계속 적용한다.
- `2026-10-06`: 고정 불규칙 배치와 장력 상호작용을 로컬 Chart에 반영했다. [EVAL-0114-R2](../evaluation/eval-0114-r2-stable-session-constellation.md)에 실제 드래그·복귀, 위치 보존, 활동·상세 복귀와 화면 폭 확인을 기록했다. 밀도와 장력의 사용자 검토가 다음 단계이며, 실제 OS 설정·터치 기기와 자동 회귀 검증은 완료로 주장하지 않는다.
- `2026-10-06`: 사용자는 불규칙 배치가 너무 무질서하다고 평가하고 실행 폴더별 프로젝트 행, master 기준 오른쪽 브랜치 가지와 브랜치 없는 폴더의 한 줄 표시를 요청했다. 추가 답변으로 저장된 브랜치명과 첫 세션 관측 기준을 명시적으로 선택했다. [SPEC-0114-R3](../spec/spec-0114-r3-project-branch-session-chart.md)와 [RUN-143](../run/run-20261006-143-project-branch-session-chart.md)로 현재 방향을 대체한다. 실제 Git 이력 조회와 업무 추론은 추가하지 않는다.
- `2026-10-06`: 프로젝트·브랜치 Chart를 기존 로컬 서버에 반영했다. [EVAL-0114-R3](../evaluation/eval-0114-r3-project-branch-session-chart.md)에 실제 드래그·겹친 세션 선택·활동·상세 복귀와 1440/700/320px 확인을 기록했다. 새 정본 경로와 최초 시각의 예외 처리는 소스 검토 범위이며, 브라우저의 합성 데이터 확인을 백엔드 실행 검증으로 주장하지 않는다. 사용자 검토는 프로젝트 순서·가지 구성·밀도이며 기존 List·작업 흐름과 자동 작업 중단 범위는 유지한다.
