# REFACTOR-0005: Shared Resource Ownership

## Purpose

세션·Local Context의 참조를 선택 기능에서 분리한다. 사용자가 2026-10-30
지금까지 합의한 설계의 실행을 요청했다. 공용 자원 identity, 기능별 매핑,
선택 연동 없는 기본 수집·읽기, 기존 데이터 보존을 구현한다.

- Status: `completed` — 구현·synthetic 검증과 후속 사용자 요청에 따른 운영 DB 적용·재시작 검증 완료.
- 실행 증거: [공용 자원 소유권 배치](logs/2026-10-30_refactor-0005_shared-resource-ownership.md).
- Baseline: REFACTOR-0004 이후 미커밋 작업 트리. HEAD는
  `6c03265701d0d8b552fc8bb60e346ba1971f4bb3`이고, 실행 전 src/tests/scripts
  파일별 SHA-256 manifest digest는
  `9f97d92586089c8664bad44f6e02d47433e4b387c67dca234c4b78eab6df78c1`이다.
- 이전 소유권 논의: [REFACTOR-0003 인계](refactor-0003-session-centered-package-boundaries.md#local-context-ownership-and-feature-owned-mappings).
- Profile: Fullstack Product. Primary agent가 contract/backend/data/integration/
  frontend/docs 구현·평가를 담당한다. 기존 사용자 변경은 보존한다.

## Refactor Type

`Semantic / Structural`. 기존 동작 보존 배치와 분리한다. 등록 여부에 독립적인
URL 분류와 참조 보존은 의도적 변화이며 strict parity를 주장하지 않는다.

## Scope

- `resources/`: 공통 URL/경로 identity와 기존 문서·로컬 북마크·외부 링크 ID 매핑.
- `sessions/references.py`, 관련 자료: 공통 자원을 향하는 세션별 근거.
- `persistence/`, `schema.sql`: 백업을 동반한 호환 마이그레이션과 재실행 안전성.
- `local_context/`, `ingest/`: 선택 기능의 필수 import/SQL 제거; 앱 조립에서 명시적으로 선택 연동.
- `atlassian/`, `workstreams/`, 앱 조립: 기존 사용자 항목·메모·관계 보존 및 공유 identity 연결.
- 실제 변경 사실을 소유하는 데이터 모델·제품·아키텍처 문서와 생성 메타데이터.
- 후속 요청(2026-10-30): 운영 DB 복사본 검증 후 서버 정상 종료, 복구 사본 확보, 정상 초기화 경로로 마이그레이션, 데이터 보존·무결성 확인 및 서버 재시작.

## Non-Goals

- Workstream·자동 작업·Atlassian 파일럿 전체 삭제 또는 제품 의미 재설계.
- 원격 redirect 확인, 서로 다른 도메인의 동일 숫자 ID 자동 병합, Slack 분류 신설.
- 미등록 로컬 파일 자동 읽기·본문 색인, 사용자 메모 폐기, 원본 파일 변경.
- 커밋·배포. 최초 구현 배치에서 제외했던 서버 재시작·운영 DB 적용은 후속 사용자 요청으로 위 Scope에 포함했다.

## Invariants

- 기존 세션 원문·관측 위치·읽기 결과·시각·사용자 메모·작업 연결을 보존한다.
- 원본 파일은 원래 소유 위치에 남고 문서 본문은 Local Context가 소유한다.
- 공통 identity는 선택 연동·문서 색인 행 삭제만으로 삭제되지 않는다.
- 이미 존재하는 항목의 ID·메모는 매핑을 통해 유지한다. 폴더·저장소를 문서로 위장하지 않는다.
- 같은 연결의 트랜잭션·실패 롤백 경계를 유지하고, 마이그레이션 실패는 복구 가능해야 한다.
- URL 해석은 로컬 순수 함수이며 등록 설정·네트워크에 의존하지 않는다.

## Planned Work

### Step 1 — Shared Identities And Migration

Status: 완료.

- Goal: URL/경로 identity를 중앙화하고 기존 대상과 관계를 보존한다.
- Why this grouping: 세션의 FK를 바꾸기 전에 새 참조 기준과 이행 경로가 필요하다.
- Guardrails: 기존 ID·수동 정보 보존, 실제 삭제·파일 읽기 없음, 도메인 간 추측 병합 없음.
- Targets: shared resource registry, document/local/external bindings, 기존 조직 매핑, migration.
- Validation: fresh/legacy/repeated/failed migration, FK, 동일 경로/URL 재사용, 수동 정보 보존.
- Exit gate: 기본 자원과 참조가 Atlassian Item 삭제 후에도 남는다.

### Step 2 — Feature-Independent Session References

Status: 완료.

- Goal: 세션 관측은 공통 자원만 참조하고 URL 분류는 등록 성공 여부와 독립시킨다.
- Why this grouping: 저장 FK·수집·화면이 같은 관계 의미를 사용해야 한다.
- Guardrails: 근거 순서·100개 상한·partial/stale·unsafe URL 처리, 모호한 힌트는 추측하지 않는다.
- Targets: Session evidence, reconciliation/projection, 관련 자료 template와 Desktop 읽기.
- Validation: 등록 전후/선택 테이블 제거/동일 URL 변형/다른 도메인/문서 삭제·재색인.
- Exit gate: Jira·Confluence URL이 설정 없이 분류되고, 선택 기능 제거가 세션 근거를 삭제하지 않는다.

### Step 3 — Local Context And Ingestion Boundaries

Status: 완료.

- Goal: 기본 문서·세션 수집과 읽기에서 선택 기능의 import/SQL을 없앤다.
- Why this grouping: 매핑 테이블만 분리하고 코드 의존을 남기면 탈부착할 수 없다.
- Guardrails: 현재 앱의 명시적 연동은 adapter로 유지하고, core는 연동 없이 동작한다.
- Targets: ingestion extension contract, Atlassian adapter, app/CLI composition, Local Context document view.
- Validation: 선택 패키지 import 차단 및 테이블 없는 synthetic 수집·읽기, 기존 연동 회귀.
- Exit gate: Local Context가 Workstream·Atlassian 없이 저장·목록·읽기를 완료한다.

## Validation Gates

- 위 Step별 의미 검증, 전체 unittest suite, 실제 schema/init migration 및 기본 route smoke.
- Google Drive PoolTests 11개는 기존 사용자 지시에 따라 제외한다.
- 문서/생성 schema presentation/audit/value registry, privacy와 diff 검사.
- UI 변화는 기존 디자인 토큰·분류·링크·빈 상태와 읽기 흐름을 검증한다.
- 최초 구현 배치는 synthetic DB로 migration/기능 제거를 검증했다. 후속 운영 적용은 실제 DB 복사본 검증과 정지된 DB의 변경 전후 보존 비교, SQLite 무결성·외래키 검사, 재시작 후 route 확인을 통과해야 한다.

## Intentional Deltas

- Session evidence의 선택 Atlassian/색인 Document FK를 안정적인 공용 자원 FK로 교체한다.
- 등록 전후에도 URL의 제품 분류가 같고 기본 URL 열람이 가능해진다.
- 문서 색인이 사라져도 관측 근거는 남고 unavailable로 표시하며 동일 경로 재색인 시 다시 연결한다.
- 원격에서 보관한 본문과 사용자가 작성한 로컬 메모는 선택 Atlassian Item 수명주기에서 분리해 공용 외부 자원 쪽에서 보존한다. 명시적인 전체 자원 purge의 삭제 계약은 유지한다.
- 선택 기능 호출은 앱/CLI 조립의 adapter가 소유한다.

## Risks / Open Questions

- 원본 파일 이동은 같은 내용 해시만으로 자동 병합하지 않는다. 경로가 달라지면 별도 identity다.
- 기존의 모호하거나 안전하지 않은 URL/고아 관계는 원본 메타데이터를 남기고 추측 매칭하지 않는다.
- 미등록 Markdown 파일은 새 참조 대상으로 자동 읽거나 색인하지 않는다. 이미 채택된 동일 원문 위치의 경로 참조는 색인 부재 상태의 재수집에서도 유지하며, 새로운 모호한 경로는 추측하지 않는다.
- 앱 전체에서 파일럿 패키지를 삭제하는 작업은 route/lifecycle/template 등록 정리가 추가로 필요하다. 이번 완료는 기본 수집·읽기와 공용 자원 저장 경계에 한정한다.
- 기존 범용 entity_type/entity_id API는 호환하며 공용 ID로 연결한다. 전체 공개 API 교체는 범위 밖이다.

## Exit Goal

세션·문서·링크의 기본 자원과 관측 근거가 선택 기능과 독립적으로 남고, 기능별
매핑·adapter를 통해 기존 파일럿을 유지하거나 제거할 수 있는 경계가 검증된다.
