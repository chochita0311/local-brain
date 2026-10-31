# REFACTOR-0004: Direct Session Materials

## Purpose

세션 상세에서 재정의 예정인 ‘연결된 작업’을 제거한다. 사용자가 2026-10-30
직접 요청한 범위이며, 세션에서 실제 발견한 Markdown·URL과 읽기 근거는 유지한다.
이전 [패키지 구조 트랙](refactor-0003-session-centered-package-boundaries.md)의
동작 보존 배치와 구분한다.

- Status: 이 한정 범위 구현·검증 완료. 배포·merge 판단은 수행하지 않았다.
- Baseline: REFACTOR-0003 URL 경계 배치 이후의 미커밋 작업 트리.
  Git HEAD는 `6c03265701d0d8b552fc8bb60e346ba1971f4bb3`이지만 이 변경의
  비교 기준 전체를 나타내지는 않는다. 대상 코드·템플릿·CSS·테스트 7파일의
  수정 전 경로→SHA-256 manifest digest는
  `81f794d51e90e41c9fd93c86457f0c47ff93a0eff85e91074fb8dfb5763de9f3`이다.
- Profile: Fullstack Product. 단일 primary agent가 구현과 평가를 담당한다.

## Refactor Type

`Semantic / Behavioral`. 간접 자료와 작업 연결 표시를 의도적으로 제거한다.
Strict behavioral parity를 주장하지 않는다.

## Scope

| Lane | 대상과 의존 | 검증 |
| --- | --- | --- |
| contract / backend | `resources/related_context.py`, `sessions/web.py`, `app/edition.py`: 직접 참조만 반환하고 조직 조회 제거 | 조직 테이블 읽기를 금지한 synthetic projection/route 검사 |
| frontend | Session 상세 템플릿 2개, 관련 자료 전용 CSS: 제거된 필드·표시 정리 | 실제 렌더링, 링크·대화·빈 상태·반응형 확인 |
| docs | 제품·아키텍처·데이터 모델·앱 사용 가이드 | 현행 계약, 생성 메타데이터 검사 |

## Non-Goals

- Workstream/Thread 기능·저장 관계·테이블 삭제.
- 범용 공용 자원 테이블, Atlassian FK 마이그레이션, URL 분류 변경.
- Local Context 외 임의 Markdown 읽기·자동 등록, 원본 파일 이동·삭제.
- 운영 DB 수정·재수집, 배포·커밋·실행 중 앱 재시작.

## Invariants

- 직접 URL/Markdown/등록 Atlassian 참조의 근거·표시 identity·순서·안전한 링크 처리 유지.
- 관측 총수와 100개 보존 상한, stale/partial/error 의미 유지.
- Session 대화, 자식 세션 진입·상위 세션 복귀, pin 동작 유지.
- 조회는 기존 DB 근거만 읽고 파일·원격·모델 실행이나 관계 쓰기를 시작하지 않는다.
- 기존 Workstream/Thread 관계와 Local Context 문서 목록을 보존한다.

## Planned Work

### Step 1 — Remove Organization From Session Detail

- Goal: 상단 작업 연결과 관련 자료의 간접 그룹·조직 배지를 제거한다.
- Why this grouping: 같은 화면에 두 번 노출되는 조직 관계와 그 생산 SQL을 함께 제거해야 세션 조회 경계가 분리된다.
- Guardrails: 직접 근거·실제 관계 데이터·다른 화면은 유지한다.
- Targets: Scope 표의 생산자→라우트→템플릿→문서.
- Validation: 조직 읽기 금지, 직접 자료 유지, 무근거 빈 상태, 오류 시 대화 유지, 관련 테스트와 브라우저 확인.
- Exit gate: 조직 자료만 있는 세션은 빈 참조 목록을 보이며, 직접 자료가 있는 세션은 조직 조회 없이 정상 렌더링된다. 잔여 검증 한계를 기록한다.

## Validation Gates

- 관련 Session/참조/Workstream/desktop 테스트와 전체 unittest suite.
- 사용자 합의대로 Google Drive `PoolTests`의 loopback 11개는 제외한다.
- 데이터 모델 문서·생성 presentation·audit 및 repository privacy 검사.
- 브라우저에서 세션 상세의 제거 결과·참조 링크·대화 순서와 실제 viewport 확인.
- 변경한 앱 모듈의 syntax/import, 삭제 코드 소비자 잔여 검색.

## Intentional Deltas

- 관련 자료는 `direct` 그룹만 반환한다. 조직 후보 SQL, 중복 관계 병합, 조직 전용 경고·0개 제목·배지를 제거한다.
- Session 상세의 membership 조회·상단 표시를 제거한다.
- 내부 projection의 미사용 `workspace_id` 인자와 조직 병합용 `dedupe_key`/`organization` 필드를 제거한다. 모든 소스 소비자를 갱신한다.
- 관계만 있고 직접 근거가 없는 경우 이전 자료 목록 대신 기존 빈 상태를 표시한다.

## Risks / Open Questions

아래 저장소 설명은 이 배치 완료 당시의 경계다. 기존 Atlassian FK와 분리된
문서/북마크 identity는 후속 [REFACTOR-0005](refactor-0005-shared-resource-ownership.md)에서
공용 identity·매핑으로 이행했다. 이를 이 UI 배치의 동작 보존 증거로 소급하지 않는다.

- 등록 Atlassian 항목의 메타데이터 조회와 기존 FK는 여전히 남아 있다. 이 변경은 Atlassian 탈부착 완료 증거가 아니다.
- Markdown은 이미 Local Context DB 문서 목록으로 존재한다. 폴더 트리는 상대 경로에서 재구성하며, 별도 범용 자원 목록·모든 로컬 파일 목록을 의미하지 않는다.
- `local_resources`의 별도 경로 등록은 본문을 색인하지 않는다. Markdown 문서 목록과 같은 identity로 자동 통합되어 있지 않다.
- 실행 중 앱이 이전 모듈을 유지하면 브라우저 증거와 새 코드 검사 범위를 구분한다.

## Exit Goal

세션 상세가 직접 발견한 자료만 펼치며, 조직 기능의 기존 사용자 데이터를 보존한
상태에서 해당 조회 결합이 사라진다. 실행 결과는
[검증 기록](logs/2026-10-30_refactor-0004_direct-session-materials.md)에 남긴다.
