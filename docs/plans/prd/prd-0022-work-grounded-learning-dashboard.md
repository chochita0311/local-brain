# PRD-0022: Work-Grounded Learning Dashboard

## Metadata

- ID: `prd-0022`
- Status: `approved`
- Owner role: `human`
- Created: `2026-10-16`
- Updated: `2026-10-27`
- Approval boundary: the owner requested a PRD and continued execution for the
  small learning pilot described below. This approves the foundation, curated
  local lessons, review history and learning home. Later model admission and
  automated source collection remain separately bounded candidates.

## Request Summary

Follow-up design: [PRD-0023: Code And Command Learning](prd-0023-code-and-command-learning.md)
records the owner's later request to learn directly from code diffs and commands,
including artifact capture, question production and a code-oriented reader.
Its source contract and manually reviewed code/command reader are approved;
automatic discovery, official-source monitoring and model execution/exposure
remain separately bounded later work. This PRD retains the approved manual
pilot and its implementation/evidence history. Its later automation candidates
should be reconciled through PRD-0023 before an additional implementation
boundary is approved.

내가 실제로 바꾸고 운영한 시스템을 다시 설명하고 판단할 수 있게 돕는다.
AI와 함께 작성한 코드, 설정 변경, 장애 대응, 인증 연동에서 배울 거리를
찾아 매일 조금씩 기술적 이해의 빈틈을 줄이는 것이 첫 목표다. 사용자가
무엇을 모르는지 먼저 목록으로 작성해야 하는 제품이어서는 안 된다.

기존 01 Dashboard를 독립적인 위젯으로 구성하고 학습을 첫 주요 영역으로 둔다.
전체 대시보드의 위젯 목록은 아직 확정하지 않았다. 업무 경험과 연결된
짧은 설명, 스스로 답해 보는 질문, 시간이 지난 뒤의 복습을 하나의 흐름으로
만든다. 보관과 분류에 드는 노력이 학습 자체보다 커지지 않게 한다.

## Source Set

- Human request: 개인 업무와 로컬 세션을 활용한 기술 부채 해소, 기존 홈의
  재구성, 공식 자료의 신뢰성과 최신성, Qwen 연계 가능성, 교육학적 근거를
  종합해 달라는 요청과 이어진 “우선 prd작성하고 계속 진행해봐”.
- Existing product: [Product](../../policies/project/product.md),
  [Natural Language Search](../../policies/project/natural-language-search.md),
  [Privacy](../../policies/project/privacy-and-data.md),
  [Storage](../../policies/project/installation-and-storage.md).
- Local evidence: 개인 업무 기록에는 이미 설정 변경, 장애 원인과 미확인 사항,
  인증 흐름, 직접 작성한 학습 설명이 있다. 개별 원문, 경로, 식별자와 수업은
  private runtime에만 보존한다. 전체 로컬 자료를 조사했다는 주장은 하지 않는다.
- Directional references: [GeekNews](https://news.hada.io/)의 짧고 유한한 목록,
  [Geoffrey Litt의 학습 프롬프트](https://gist.github.com/geoffreylitt/a29df1b5f9865506e8952488eac3d524)의
  배경 설명·직관·코드 연결·질문 구성. 화면 복제나 고정된 객관식 비율의 근거는 아니다.
- Dashboard composition: 2026-10-17 사용자는
  [Refero의 Qatchup 화면](https://styles.refero.design/style/1b010453-80df-406a-8b1a-72630c4a5165)을
  참고한 위젯형 구성을 요청했다. 독립적인 카드와 여백을 참고하고 색·글꼴·버튼·
  모서리는 LocalBrain 디자인을 사용한다. 드래그·크기 조절·개인별 배치 저장은
  이 요청으로 확정된 동작이 아니다.
- Learning evidence: [Karpicke and Blunt, 2011](https://learninglab.psych.purdue.edu/downloads/2011/2011_Karpicke_Blunt_Science.pdf),
  [Cepeda et al., 2008](https://journals.sagepub.com/doi/10.1111/j.1467-9280.2008.02209.x),
  [Chi et al., 1994](https://onlinelibrary.wiley.com/doi/10.1207/s15516709cog1803_3),
  [Butler, 2010](https://pubmed.ncbi.nlm.nih.gov/20804289/).
  회상·간격을 둔 복습·자기 설명·다른 상황에 적용하기의 설계 근거다.
  이 연구들이 이 제품이나 개발자의 업무 성과를 검증했다는 뜻은 아니다.
- Design authority: [Design Constitution](../../policies/design/design-constitution.md).
  새 홈의 정보 우선순위를 승인된 예외로 반영하고 기존 shell·토큰·읽기 방식은 따른다.

## Product Intent

학습의 기본 단위는 기술명이나 문서 전체가 아니라 **내 업무의 한 판단과
그 판단을 설명하는 개념**이다. 예를 들어 배포 전략의 보장 범위, DB 저장과
메시지 처리 위치의 관계, 브라우저 인증과 서버 간 인증의 차이를 다룬다.

업무의 관측 기록은 “왜 이 주제가 나와 관계있는가”를 설명한다. 공식 자료는
“이 동작을 무엇으로 확인했는가”를 설명한다. 사용자의 답변은 “지금 어떤
설명을 스스로 할 수 있었는가”를 보여 준다. 세 종류의 근거를 서로 대체하지 않는다.
업무에서 사용했다는 사실이나 AI가 작성한 결과만으로 무지·숙련을 판정하지 않는다.

## Confirmed Scope

### 1. 첫 학습 시범

- 배포 전략, 메시지 처리, 인증 흐름의 세 사례로 시작할 수 있게 한다.
  첫 수업은 근거를 확인해 구성하며 특정 회사·프로젝트를 앱 코드에 넣지 않는다.
  작성 도우미가 검토한 수업과 사용자가 검토한 수업을 구분해 표시한다.
- 초기 주제와 질문은 작성 도우미가 사용자의 예시와 일부 업무 기록을 바탕으로
  수동 선정한 시범이다. 사용자가 커리큘럼을 직접 확정했거나, 전체 업무를 분석해
  이해도 부족을 진단한 결과로 표현하지 않는다. 첫 노출 순서는 가져온 순서이며
  개인의 학습 필요도를 계산한 순위가 아니다.
- 각 사례는 업무 맥락, 하나의 핵심 개념, 짧은 설명, 조건과 예외, 원본 자료,
  회상과 상황 적용 질문을 포함한다. 초기 목표는 총 8–12개 질문이다.
- 기본 제안량은 하루 새 수업 1개와 복습 최대 2개, 약 5–10분이다.
  이는 조절할 초기 가설이며 개인에게 검증된 최적량이 아니다.
- 사용자는 목록에서 다른 수업을 직접 읽을 수 있다. 자동 제안량을 소진하면
  새 항목으로 계속 채우지 않고 오늘의 끝을 보여 준다. 연속 출석이나 빚처럼
  늘어나는 밀린 문제 수로 학습을 압박하지 않는다.

### 2. 답하기와 설명 읽기

- 먼저 짧은 질문에 자신의 말로 답하고 확신 정도를 기록할 수 있다.
  답을 모르면 힌트를 보거나 설명부터 읽는 선택도 제공한다.
- 제출 후 기준 설명과 조건·예외를 보여 주고, 사용자가 자신의 답을 비교해
  다시 보기 / 일부 설명 가능 / 스스로 설명 가능을 선택한다.
- 첫 버전은 이 선택을 **자기 평가**로 저장한다. 자동 채점, 객관적 정답률,
  개념별 숙련도 백분율로 표시하지 않는다.
- 읽기, 힌트를 본 답변, 독립적으로 시도한 답변을 구분한다. 읽기만 한 기록은
  회상 성공이 아니다. 건너뛰거나 숨긴 항목은 오답이 아니다.
- 이후에는 원래 상황의 재질문과 조건을 바꾼 적용 질문을 섞는다.
  객관식은 오해를 구분할 때 쓰는 후속 선택지이며 초기 필수 형식은 아니다.

### 3. 복습과 개인화

- 복습 시점은 실제 답변·읽기·자기 평가와 연결한다. 일정은 설명 가능한
  단순 규칙으로 시작하고 과학적으로 최적화되었다고 주장하지 않는다.
- 하루에 반복 클릭해도 복습 간격이나 이해 상태가 부풀지 않게 한다.
  수정된 수업은 별도 판본으로 기록하고 이전 판본의 답변을 덮어쓰지 않는다.
- 잠시 미루기, 목록에서 숨기기와 복원하기를 지원한다. 답변과 공개 여부는
  로컬 DB에 남아 브라우저 데이터 삭제와 무관하게 유지된다.
- 질문의 “왜 나에게”에는 구체적 업무 근거가 있어야 한다. 이미 있는 학습
  노트도 활용하며, 읽은 적이 없거나 모른다고 단정하지 않는다.

### 4. 근거와 문서의 시점

- 모든 수업은 업무 근거와 공식 근거를 구분해 보존한다. 원문 위치, 확인 시점,
  내용 지문, 적용 버전과 적용 범위, 수업 판본을 추적할 수 있어야 한다.
- 현재 최신 문서와 그 당시 사용한 버전을 구분한다. 버전을 모르면 미확인으로
  표시하고 현재 운영 환경에도 적용된다고 단정하지 않는다.
- 공식 문서는 필요한 절과 중요한 전제·예외를 보존한다. 전체 사이트를 미리
  복제하거나 문맥 없는 문장만 대량 적재하는 방식은 첫 범위가 아니다.
- 첫 버전은 확인한 원문과 날짜를 보여 주며 자동 최신화를 약속하지 않는다.
  이후 자동 재확인에서는 내용이 바뀐 수업을 재검토 대상으로 만들고 과거
  답변 당시의 근거를 보존해야 한다. 단순 접근 성공은 내용 검증이 아니다.
- 근거 부족·버전 불일치·불확실한 장애 원인은 그대로 표시한다. 생성 모델의
  자연스러운 설명으로 확인되지 않은 사실을 채우지 않는다.

### 5. Dashboard

- 01 Dashboard는 오늘의 배움, 복습, 최근 업무, 선택된 수업의 근거를 독립적인
  위젯으로 배치한다. 학습은 이 구성의 첫 주요 기능이며 다른 위젯은 실제 필요에
  따라 후속 선정한다. 첫 배치는 고정형이며 좁은 화면에서는 한 열로 이어진다.
  Workstream·Thread는 기존 전용 화면에서 계속 접근한다.
- 학습 목록과 수업 상세는 실제 데이터에 연결한다. 빈 상태에서는 아직 수업이
  없다는 사실과 실제 제공되는 준비 경로를 표시한다.
- 수업에서는 출처를 확인하고 답변·설명·자기 평가·복습 시점을 이어서 볼 수
  있어야 한다. 별도 분류 큐를 매일 정리해야만 학습할 수 있게 만들지 않는다.
- 학습 목록에서 검토 주체, 버전 불확실성, 연결된 자료와 확인일, 현재 수업
  준비·갱신 방법을 찾을 수 있게 한다. 출처 목록이 자동 수집·자동 최신화를
  제공하는 관리 화면처럼 보이지 않아야 한다.
- 기존 Sessions Dashboard, 세션 탐색, 자연어 검색, Local Context는 유지한다.
  GeekNews의 밀도와 빠른 진입을 참고하되 앱의 색·간격·타이포그래피를 사용한다.

## Later Candidates

1. **업무 근거에서 후보 찾기:** 승인된 로컬 소스의 실제 변경·판단·반복 질문을
   근거로 학습 후보를 만든다. 임베딩 유사도는 검색 신호이며 이해도 판정이 아니다.
   같은 개념의 중복을 줄이고 사용자의 관심·미루기·답변 근거를 반영한다.
   후보에는 어떤 업무 때문에 제안했는지, 연결한 개념, 작성 주체와 검토 상태를
   남긴다. 사용자는 관심 없음·이미 설명 가능·나중에 보기로 방향을 조정할 수
   있어야 한다. 일상 학습 전에 모든 후보를 수동 분류하게 만들지 않는다.
2. **공식 자료 수집과 재확인:** 버전에 맞는 공식 자료를 좁게 가져와 원문과
   확인 이력을 보존한다. 공개 URL 조회에 개인 업무 내용·검색어를 전송하지 않는다.
   업무 자료의 허용 범위와 공식 자료 목록을 구분한 학습 재료 관리가 먼저 필요하다.
   공식 자료는 소유 기관·원문 URL·적용 버전·절 위치·수집/검토 시각·내용 지문과
   연결된 수업/질문을 추적한다. 버전별 필요한 절을 보존하고 원문 변경 시 영향받는
   수업을 재검토 대상으로 만든다. 최신판과 실제 사용 버전은 별도로 추적하며,
   변경된 답을 과거 학습 기록에 소급하지 않는다. 현재는 수업별 묶음으로만 저장하며
   통합 원천 관리 화면과 재확인 작업은 구현되지 않았다.
3. **로컬 Qwen 설명·출제:** 기존 embedding 모델과 생성 모델의 역할을 분리한다.
   출처 충실성, 예외 보존, 버전 일치, 잘못된 문제·채점 비율, 지연과 메모리를
   공개·합성 사례에서 먼저 확인한다. 기존 관계 추론 실패를 해소했다고 간주하거나
   중단된 자동 작업을 재개하지 않는다. 사용자에게 그럴듯한 오답을 가르치는
   비용을 고려해 품질이 낮으면 검토 가능한 후보 생성으로만 제한한다.
4. **학습 효과 확인:** 약 2주 사용 후 설명 없이 다시 설명하는 능력과 새로운
   상황 판단, 잘못된 확신 감소, 부담을 확인한다. 더 많은 퀴즈를 푼 횟수만으로
   기술 부채 감소를 주장하지 않는다. 실사용 기간이 지나기 전 효과는 미확인이다.

## Excluded Scope

- 전 로컬 저장소의 상시 감시, 외부 AI/embedding 필수화, 클라우드 동기화,
  외부로 개인 세션·답변·회사 자료 전송.
- 기존 Workstream 관계의 자동 변경, 중단된 workflow-map/Auto Work 재개.
- 전체 기술 분야의 완성된 커리큘럼, 공식 자격 판정, 숙련도 점수·순위·출석 경쟁.
- 첫 버전의 자동 사실 판정, 자동 자유서술 채점, 학습 모델의 개인 답변 재학습.
- 설치형 Mac 앱·배포 결정. 별도로 승인된 [PRD-0021](prd-0021-macos-standalone-test-app-and-local-settings.md)이
  이 범위를 소유하며, 네이티브·수신자 배포 수용 근거가 남아 `blocked`인 상태를 유지한다.

## Constraints

- Durable lessons, source snapshots, answers and scheduling choices belong to the
  private application database. Rebuildable retrieval caches remain separate.
- Importing revised content is explicit and idempotent. Existing attempts retain
  their exact question, lesson and source revision. Failed imports are atomic.
- Routes use the existing local application shell and local mutation boundary.
  Source links and lesson text cannot introduce executable markup or arbitrary
  file reads. Browser reads do not trigger external collection or generation.
- Shared documentation, examples and evaluation artifacts use synthetic content.
- Profile: foundation contract first, then Fullstack Product with data/backend and
  home/reader surface lanes. One bounded Feature/Run is active at a time.

## Acceptance Envelope

1. A reviewed local lesson can connect a work observation to official evidence
   without copying private content into the repository or requiring a model.
2. The home proposes a finite daily selection; the reader supports independent
   answer and confidence, explanation-first reading, feedback and self-assessment.
3. Learning records survive reload and are tied to immutable lesson revisions.
   Reading, skipped work and self-reported recall have distinct meanings.
4. Review scheduling is visible and reproducible; source age, version uncertainty
   and revision changes are not presented as current verified knowledge.
5. Existing work navigation remains accessible. Empty, invalid input, missing
   source and save failure states are understandable and recoverable.
6. Functional/design evidence and longer-term learning benefit are reported
   separately. Implementation alone does not pass the effectiveness criterion.

## Candidate Features

- `FEAT-0124`: learning evidence, source and revision contracts; prerequisite for
  all persistence and product work.
- `FEAT-0125`: reviewed lesson intake, local attempts and finite learning home;
  Fullstack Product, dependent on FEAT-0124.
- Automated candidates above need their own bounded Features and admission
  evidence; they are not implicit jobs started by opening the dashboard.

## Uncertainty And Review

The initial question count, daily load, intervals and reading/answer balance are
pilot defaults. Their adjustment does not imply that learning effectiveness has
been established. Source-fetch policy, generator model/resource budget and
semantic quality thresholds must be resolved before activating automated lessons.
The first implementation can proceed with reviewed local material independently.

## Documentation Index Reconciliation — 2026-10-31

The following preserves the detailed navigation snapshot relocated from the
Plans Index. Its dated execution/approval facts and evidence limits remain with
this owning record and its linked artifacts; it is not a new execution grant or
an update to unrelated acceptance. Current definitions remain in policy owners.

### Boundary And Delivery Context

- [PRD-0022: Work-Grounded Learning Dashboard](prd-0022-work-grounded-learning-dashboard.md)
  is approved for the reviewed-content pilot and continued implementation.
  [FEAT-0124](../feature/feat-0124-learning-evidence-contract.md) fixes the evidence,
  revision and learning-state contract; [FEAT-0125](../feature/feat-0125-reviewed-learning-home.md)
  delivered the original local intake, attempts, reviews and learning home under
  [RUN-163](../run/run-20261017-163-reviewed-learning-home.md), now returned to planning
  for PRD-0023. Its preserved records/contracts are reused; its functional evidence
  gap is not closed by the successor. Automatic source
  retrieval/generation and learning benefit remain separate, unproven boundaries.
