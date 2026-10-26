# FEAT-0134: 일반 설정과 프로젝트 표시

## Metadata
- ID: `feat-0134`
- Status: `blocked`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md) — C07
- Created: `2026-10-18`
- Updated: `2026-10-26`
- Authorization: 사용자의 현재 PRD 범위 전체 구현 요청. 범위 확대는 별도 검토한다.

## Goal And Acceptance Contract
- AC1: 일반의 시작 화면·시간대는 최대 240px·데스크톱 높이 32px 드롭다운이다. 시작 화면은 Sessions Dashboard → Sessions → Local Context 순서이며 기본 선택은 Sessions다. 시간대는 UTC·Asia/Seoul이다. 동기화는 별도 분류에서 세션과 Local Context 각각 10·20·30·60분·끄기 단일 선택기로 제공한다. 기존 저장값과 없는 항목의 기본값(세션 10분, Context 30분)을 보존한다. 프로젝트 표시 및 기준 위치 등록 UI는 없다.
- AC2: 경로는 현재 사용자 홈만 `~`로 축약하는 고정 규칙을 사용한다. 홈 자체는 `~`, 홈 밖은 원래 경로를 유지한다. 표시를 위해 파일시스템 경로를 해석하거나 기준 위치·별칭을 등록하지 않는다. 원본 경로·ID·고정 Usage 귀속은 보존한다. 기존 `project_display`·`projects`와 해당 환경변수는 적용하지 않고, 저장 파일의 기존 값은 보존하며 새 설정 API에서는 받지 않는다.
- AC3: 일반 설정은 로컬 파일을 따르고 없는 항목만 기본값을 사용한다. 환경변수 덮어쓰기와 저장값/적용값 안내를 제거한다. 일반 옵션은 확정 선택 즉시 변경 항목만 저장하며 별도 저장 버튼을 두지 않는다. 실패 시 실제 저장값을 다시 읽어 표시하고 재시도할 수 있게 한다. 설정의 동기화 상태·시각·수동 버튼 카드는 제거하되 Sessions의 수동 동기화와 로컬 상태 기록은 유지한다.
- AC4: By Project / Project 명칭을 유지하며 `session_class=work`인 일반 작업과 하위 세션만 프로젝트별로 집계한다. 분석·Maintenance는 Project의 행·합계·비율 분모·정렬·최근 활동·연결에서 제외한다. 전체 사용량·추이·Source/Model 집계와 저장된 귀속·토큰·비용은 보존한다. Git 루트 또는 실행 폴더(`~` 포함) 기준과 실제 미귀속 작업의 `프로젝트 미지정` 표시는 유지한다.

## Scope Boundary
- In: 위 계약과 PRD의 C07 결과.
- Out: 데이터 물리적 이동, 새 외부 전송, 제품 제외 기능의 설치형 활성화, 유료 배포·자동 업데이트.

## Surface Lanes
- Contract/data: 공통 설정·소스·검색·복구의 값별 정본. Contract 평가 담당은 primary agent.
- Product/runtime: 해당 화면과 backend 또는 macOS 실행부. Functional/Design/Interaction 평가 범위는 실제 변경과 실행 근거로 보고한다.

## Dependencies
- C01 / FEAT-0128, C05 / FEAT-0132

## State And Interaction
- Loading/empty/error/success를 구분한다. 원본·기존 사용자 상태를 실패 시 보존한다.
- 화면 변경은 기존 디자인을 extend하며 입력·조회·읽기 상태와 포커스를 보존한다.

## Contract Surfaces And Regression
- 기존 source/session ID, frozen Usage attribution, 도메인 정본, 설치형 범위, 로컬 데이터 보존.
- 기존 개발판 학습·Workstream 기능의 변경은 이 Feature 범위 밖이다.

## Pass Or Fail Checks
- AC1: 일반의 시작 화면·시간대는 최대 240px·데스크톱 높이 32px 드롭다운이다. 시작 화면은 Sessions Dashboard → Sessions → Local Context 순서이며 기본 선택은 Sessions다. 시간대는 UTC·Asia/Seoul이다. 동기화는 별도 분류에서 세션과 Local Context 각각 10·20·30·60분·끄기 단일 선택기로 제공한다. 기존 저장값과 없는 항목의 기본값(세션 10분, Context 30분)을 보존한다. 프로젝트 표시 및 기준 위치 등록 UI는 없다.
- AC2: 경로는 현재 사용자 홈만 `~`로 축약하는 고정 규칙을 사용한다. 홈 자체는 `~`, 홈 밖은 원래 경로를 유지한다. 표시를 위해 파일시스템 경로를 해석하거나 기준 위치·별칭을 등록하지 않는다. 원본 경로·ID·고정 Usage 귀속은 보존한다. 기존 `project_display`·`projects`와 해당 환경변수는 적용하지 않고, 저장 파일의 기존 값은 보존하며 새 설정 API에서는 받지 않는다.
- AC3: 일반 설정은 로컬 파일을 따르고 없는 항목만 기본값을 사용한다. 환경변수 덮어쓰기와 저장값/적용값 안내를 제거한다. 확정 선택 즉시 변경 항목만 저장하고, 실패 시 실제 저장값을 다시 읽어 복구한다. 일반 저장 버튼과 동기화 상태 카드는 없으며 소스 폼·Sessions 수동 동기화·로컬 기록은 유지한다.
- AC4: By Project / Project 명칭을 유지하며 `session_class=work`인 일반 작업과 하위 세션만 프로젝트별로 집계한다. 분석·Maintenance는 Project의 행·합계·비율 분모·정렬·최근 활동·연결에서 제외한다. 전체 사용량·추이·Source/Model 집계와 저장된 귀속·토큰·비용은 보존한다. Git 루트 또는 실행 폴더(`~` 포함) 기준과 실제 미귀속 작업의 `프로젝트 미지정` 표시는 유지한다.
- 각 조건의 코드 검토와 실제 실행 근거를 분리한다. 미실행 검증은 PASS로 간주하지 않는다.

## Harness Trace
- Spec: [SPEC-0134](../spec/spec-0134-general-and-project-settings.md)
- Run: [run-20261020-180-project-copy-removal](../run/run-20261020-180-project-copy-removal.md). 검증 결과는 Run과 평가 기록에서 구분한다.

## Continuity Notes

- `2026-10-20`: [일반 설정 자동 저장](../run/run-20261020-183-general-settings-autosave.md)으로 명시적 일반 저장 버튼을 대체한다. 소스 등록 폼의 저장, 실제 설정 적용 시점, 동기화 백엔드와 기록 소유는 유지한다.

- `2026-10-20`: [일반 설정 적용 시점 안내 제거](../run/run-20261018-172-general-and-project-settings.md#apply-timing-copy-removal--2026-10-20). 중복 안내와 저장 후 같은 설명을 삭제했다. 실제 적용 시점·저장 방식·선택지 순서는 유지하며 앱/ZIP에도 반영했다.
- `2026-10-18`: C07를 승인된 구현 경계로 구체화했다. foundation의 필드별 계약을 먼저 고정하고 후속 구현은 의존성 순서를 따른다.

## Implementation And Evidence — 2026-10-19

승인된 구현과 로컬 검증을 완료했다. [통합 기능 평가](../evaluation/eval-0139-functional-standalone-test-app.md)와
[계약 평가](../evaluation/eval-0139-contract-standalone-test-app.md)가 자동 검사·브라우저·동봉 앱·실제 모델 실행의
범위를 소유한다. [화면/상호작용 평가](../evaluation/eval-0139-design-standalone-test-app.md)의 실제 WebView 조작 근거와
PRD A12의 팀원 Mac 전달 확인이 남아 있어 전체 제품 수용은 `blocked`로 둔다.
구현 미착수나 새로운 제품 방향 미결정이라는 뜻은 아니다. 원본·설정·기존 개발 작업을
보존했으며, Drive 업로드·팀원 통지·Git 커밋/공개는 수행하지 않았다.

- `2026-10-19` 이전 구현 해석(아래 정정으로 대체): 에이전트가 시작 화면의 펼침 목록을 직접 선택으로, 시간대 직접 입력을 도시·지역 검색 목록으로 바꾸었다. 기존 로컬 저장·환경변수 우선순위·적용 시점을 유지하며 시간대의 실제 영향 범위를 설명한다.

- `2026-10-19` 사용자 정정: 시작 화면은 드롭다운을 복구하고 열린 목록의 하단 정렬을 평가한다. 시간대는 `UTC`와 원래 표기 `Asia/Seoul`만 선택하도록 한다. 이전 직접 선택·도시 검색 UI는 사용자 의도를 잘못 해석한 것이므로 현재 AC1로 대체한다.

- `2026-10-19` 사용자 후속 요청: 프로젝트 표시·자동 동기화도 같은 드롭다운으로 통일하고, 시작 화면부터 네 박스의 가로 폭을 짧게 맞춘다. 저장된 주기·끄기 상태를 먼저 읽은 후 네 선택 표시를 갱신한다. 기존 설정값과 적용 규칙을 유지한다.

- `2026-10-19` 사용자 단순화 정정: 프로젝트 표시 드롭다운·기준 위치 등록 개념을 제거하고 현재 사용자 홈의 `~` 축약을 공통 규칙으로 고정한다. 이전 네 드롭다운·표시 별칭 계약은 현재 AC1/AC2로 대체한다. Fullstack profile의 설정 계약·공통 표시·화면·패키지 lane을 primary가 검증하며 기존 원본·ID·고정 Usage 귀속은 보존한다.

- `2026-10-20` 사용자 승인: Project는 일반 작업과 하위 세션만 집계하고 분석·Maintenance는 전체 사용량에 유지한다. `By Project / Project` 명칭과 `~`를 포함한 경로 기준을 유지한다. 이전 앱 내부 분석 Project 구분을 대체하며 별도 Run에서 검증한다.

- `2026-10-20` 구현·검증 완료: Run 179의 Project 정정은 scoped PASS. 관련 118개 테스트와 웹·동봉 백엔드·실제 앱 확인을 완료했다. 전체 배포 수용의 기존 팀원/native 관찰 경계는 그대로 남는다.

- `2026-10-20` 후속 화면 정정: Project 표 위에 추가한 기준 설명과 별도 합계 문단을 제거한다. 집계와 기존 빈 상태는 유지하며 Run 180에서 확인한다.

- Settings-control follow-up: [Run 187](../run/run-20261023-187-settings-control-consistency.md); prior recipient/native acceptance boundaries remain.
