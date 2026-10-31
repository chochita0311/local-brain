# Shared Resource Ownership And Optional Reference Adapters

## Log Type

- Type: `Batch / Wrap-Up`
- Date: `2026-10-30`
- Related track: [REFACTOR-0005](../refactor-0005-shared-resource-ownership.md)
- Scope: 사용자가 합의한 Session 중심 공용 자원·Local Context 소유권과 기능별 매핑 구현.
- Profile: Fullstack Product. 변경 표면은 Session 관련 자료와 Document/로컬 자원 읽기이며 기존 layout·tokens·접근성 규칙을 사용한다.

## Summary

- Goal: 기본 자료와 Session 발견 근거가 Atlassian·Workstream 등 선택 기능의 수명주기에 종속되지 않게 한다.
- Outcome: `Pass` — 계획의 세 단계 구현과 아래 범위의 검증 완료.
- 공용 자원 식별자와 문서·북마크·외부 링크 매핑을 추가하고, Session evidence의 Atlassian/Document 직접 FK를 공용 자원 FK로 교체했다. 문서 본문은 Local Context가 계속 소유한다.
- 최초 구현 배치에서는 운영 DB 마이그레이션·수집·서버 재시작·커밋·배포를 직접 실행하지 않았다. 이후 사용자의 즉시 적용 요청으로 운영 DB 마이그레이션과 서버 재시작을 실행했다. 아래 후속 운영 적용 기록이 현재 적용 상태를 소유한다.

## What Changed

- Added: `resources/catalog.py`의 공용 URL/path/note identity 및 기존 ID 바인딩; `persistence/resource_migration.py`의 복구 사본·원자적 이행; `ingest/extensions.py`의 기본값이 빈 선택 observer 계약; `app/reference_integrations.py`의 앱·CLI·백그라운드 조립과 선택 읽기 callback.
- Updated: Session 수집/근거/관련 자료, Local Context 수집·삭제·읽기, Workstream/Thread outgoing link의 `resource_id`, 선택 소비자인 Workflow·Auto Work reconstruction·Atlassian의 SQL. 공용 코드가 선택 기능을 import하지 않는다.
- Moved/Renamed: `atlassian_item_content` → `external_resource_content`, `atlassian_item_local_state` → `external_resource_notes`. 두 테이블의 FK는 공용 외부 메타데이터를 향한다. 본문·메모·해시·시각·기존 ID는 그대로 복사한다. 조직에 자료를 등록/연결하는 HTTP 처리는 `workstreams/resource_web.py`가 소유한다.
- Removed: `atlassian/session_references.py` 등록 항목 resolver, Session 근거의 `target_kind`·Document/Atlassian target FK, Desktop의 내부 Atlassian 경로 변환. 제품 분류와 안전한 외부 URL 열기는 등록 여부와 독립적이다.
- Documentation: 제품·아키텍처·주제별 데이터 모델·값 사전·계획 인계와 생성 manifest/audit을 갱신했다. 현재 스키마는 ordinary table 52개 + FTS5 1개, FK 66개, effective named index 51개다. 기존 defer 판정 112개를 유지하고 새/변경 소유권을 명시하여 audit 755개 객체를 설명한다.

## Behavior / Parity Notes

- Parity claim status: `Intentional deltas present`.
- Baseline: REFACTOR-0004 이후 미커밋 작업 트리. HEAD `6c03265701d0d8b552fc8bb60e346ba1971f4bb3` 단독 diff가 아니며, 실행 전 src/tests/scripts manifest digest는 `9f97d92586089c8664bad44f6e02d47433e4b387c67dca234c4b78eab6df78c1`이다. 다른 미커밋 변경은 보존했다.
- 보존 계약: 원문 위치·관측 identity·읽기 결과·timestamp·사용자 제목/메모·조직 link ID를 유지한다. 마이그레이션의 evidence key/ID는 유지하며 target binding/key만 공용 기준으로 바꾼다. 이후 v4 수집은 기존 deterministic 교체 절차를 사용한다. 실패 시 savepoint rollback, 이전 유효 근거와 error/stale 상태를 유지한다.
- 의도적 변경: 등록되지 않은 Jira/Confluence도 같은 제품 분류·공용 identity를 사용한다. 도메인 간 ID를 합치거나 redirect를 조회하지 않는다. bare ID는 공용 URL이 하나로 결정될 때만 허용하며, 후보 목록 뒤쪽의 URL도 모호성 판단에 포함한다.
- 문서 색인을 지우면 binding만 제거되고 Session 근거·자원·수동 북마크 메모는 남는다. 동일 원문 위치의 기존 경로 참조는 색인 부재 상태의 재수집에서도 유지한다. 같은 경로 재색인은 새 Document ID로 열람을 복구한다. 미등록 파일을 새로 읽거나 자동 색인하지 않는다.
- Atlassian 확장 행 제거는 공용 본문·메모·Session 근거를 삭제하지 않는다. 명시적인 전체 External Resource purge는 기존 삭제 계약대로 본문·메모·조직 관계를 지우며, 이 동작을 기능 분리와 혼동하지 않는다. 공유 URL identity와 Session 근거는 남는다.
- 완료된 scan의 target 수는 합쳐진 공용 identity 기준으로 재계산한다. 기존 partial set의 전체 집합은 복원할 수 없으므로 원래 observed 수를 유지하고 재수집 필요 error로 표시한다.
- observer는 호출자의 connection/transaction을 사용하며 원격 호출·독립 commit을 하지 않는다. 앱 요청과 worker thread 진입 내부, CLI scan에 명시적으로 설치한다. 기본 수집은 observer 없이 동작한다.
- 전체 앱의 모든 의존에 대한 strict parity 또는 자동 기능 제거 가능성을 주장하지 않는다.

## Validation

- 전체 unittest: `unittest.defaultTestLoader.discover('tests')`에서 사용자 보류 대상 `test_google_drive_transport.PoolTests.*`가 정확히 11개인지 확인하고 제외 — **1,463개 통과**, 30.056초. 마지막 테스트 import 정리와 문서 보완 후 schema/resource/reference/value 관련 **83개**를 다시 실행해 통과했다.
- 새 소유권/마이그레이션 검사 12개: 동일 경로의 Document/북마크와 조직 매핑, 서로 다른 Session의 URL 재사용, Cloud titleless/legacy Confluence 경로, 다른 도메인·bare ID 모호성, 문서 삭제·재수집·재색인, 미등록 파일 읽기 금지, 선택 테이블 제거 후 실제 folder scan·문서 읽기, 선택 패키지 import 차단, observer rollback/reset, 이전 DDL migration·재실행·실패 복구·partial scan·0600 non-overwriting backup.
- 기존 연동/선택 소비자 집중 검사 166개 통과. 추가 schema/reference/Atlassian 본문·메모/표시 검사를 포함한 76개 집중 검사도 통과했다.
- Runtime: 모든 data/cache/development/source 경로를 격리한 synthetic 환경에서 실제 FastAPI lifespan 시작·종료. Workstream/Workflow/search 읽기 callback을 끈 실제 앱 ASGI 요청 `/sessions/100`, `/documents/100` 모두 200. 새 Jira·Confluence·Markdown·URL 그룹, 비활성 Document, 대화와 안전 외부 목적지를 확인했다. 실제 사용자 source나 provider는 호출하지 않았다.
- Browser: 위 synthetic route 응답을 로컬 정적 artifact로 열어 현행 CSS와 렌더링했다. 1440×900에서 두 열, 820×900에서 568px rail이 대화보다 앞에 오는 단일 흐름과 가로 넘침 부재를 확인했다. 참조 5개 중 유효 링크 4개만 focus 가능하고 삭제된 문서는 `열 수 없음`이며 외부 링크는 `noopener noreferrer external`을 유지한다. Socket 기반 live route/browser 왕복이나 원격 목적지 접근을 검증한 것은 아니다.
- Packaging: 네트워크 없이 기존 로컬 build dependency cache를 읽어 wheel 생성. 새 catalog/migration/observer/composition/HTTP 모듈 포함과 삭제된 resolver 부재 확인. 저장 경계를 침범하지 않는 임시 설치 layout에서 source checkout import를 제외하고 앱 114개 route import, fresh DB 초기화, 공용 contract 및 FK 검사를 통과했다. Frozen/Tauri 바이너리는 재빌드하지 않았다.
- 생성/문서: `check-data-model-docs.py`, `build-schema-presentation.py check`, `check-schema-cleanup-audit.py --check`, `check-data-model-mermaid.mjs` 통과. `git diff --check`, privacy 검사(1,778 candidate files), 전체 앱/테스트 Python AST 파싱도 통과했다.
- 기존 Starlette TemplateResponse 인자 순서 deprecation warning은 남아 있으며 이 배치에서 별도 framework 변경을 하지 않았다.

## Risks / Limitations

- 최초 배치의 migration 증거는 합성 legacy/fresh DB 검증이었다. 후속 운영 적용에서 실제 DB 복사본과 운영 DB의 보존·무결성 검증을 추가했다. 경로 충돌·알 수 없는 구형 schema·본문 충돌은 추측 복구하지 않고 rollback한다.
- 명시적인 기능 전체 제거에는 해당 앱 route/lifecycle/template/assets 등록 정리가 추가로 필요하다. 이번 경계는 공용 자원과 core 수집·읽기다. Workstream·자동 작업·Atlassian·Context Search의 제품 유지 여부를 확정하지 않았다.
- Google Drive loopback 전송 11개는 사용자 지시에 따라 계속 보류했다. 라이브 provider, 수동 Session 재수집, 원격 redirect 또는 cross-domain alias 확인은 하지 않았다. 운영 적용 이후 기존 설정의 백그라운드 서비스는 정상 시작했다.
- 작업용 baseline·synthetic DB·wheel·렌더링 파일은 종료 전에 제거하며 durable 문서는 임시 경로에 의존하지 않는다.

## Next Action

공용 자원·관측·기능별 매핑 경계를 이 배치의 완료 기준으로 유지한다. 파일럿을
제거하기로 결정하면 해당 기능의 앱 조립 등록과 선택 부가 상태만 별도 범위에서
정리한다. 기본 Document/공용 자원/Session 근거를 그 제거에 포함하지 않는다.

## Follow-Up — Operational Migration

- Type: `Runtime / Migration`, Date: `2026-10-30`, Outcome: `Pass`.
- Authorization: 최초 구현 완료 후 사용자가 운영 DB에 지금 마이그레이션하라고 명시적으로 요청했다. 해당 요청으로 계획의 운영 적용·재시작 범위를 갱신했다.
- Rehearsal: 실제 SQLite DB를 backup API로 일관된 비공개 복사본에 복제하고 정상 `init_db()` 경로를 적용했다. 예정된 binding/key/scan-count 변경을 제외한 기존 54개 테이블의 열별 투영에 대해 행 수와 SHA-256을 비교했으며 모두 일치했다. 외부 본문·메모 테이블은 이름 변경 후 같은 열로 비교했다.
- Live execution: 기존 서버의 실행 환경을 메모리에서 보존하고 SIGTERM으로 정상 종료했다. 배타적 backend lease와 operation lock 안에서 정지 DB 기준선을 만들고 `<database>-pre-shared-resources-v1.bak` 복구 사본을 생성했다. 사본의 0600 권한과 기준선 일치를 확인한 뒤 같은 초기화 경로로 적용했다.
- Preservation: 운영 DB도 동일한 54개 테이블 투영 비교를 통과했다. 기존 Session·Document·External Resource·참조 근거·조직 연결의 행과 보존 대상 필드가 일치했고, Document 매핑 누락 및 근거의 공용 identity 불일치가 없었다. scan 상태·건수 변화도 계획된 이행 규칙과 일치했다.
- Integrity: `PRAGMA integrity_check = ok`, `foreign_key_check` 오류 없음, 공용 자원 contract 통과. Session evidence의 FK 대상은 `sessions`와 `reference_resources`뿐이다.
- Runtime: 원래 환경과 loopback 주소로 서버를 재시작했다. 영구 로그는 만들지 않았고 URL access logging을 비활성화했다. `/api/health`, 기존 Session 상세, `/context`가 모두 HTTP 200으로 응답했다.
- Browser: 실제 Session 상세에서 Confluence·Jira·Markdown·URL 분류와 기존 Confluence 링크의 표시, HTTPS 목적지, `noopener noreferrer external`, 가로 넘침 부재를 확인했다. 원격 링크는 열지 않았으며 다른 도메인 alias나 redirect를 검증한 것은 아니다.
- Recovery / cleanup: 복구 사본은 [기존 migration backup 수명주기](../../../policies/project/installation-and-storage.md#bounded-recovery-and-cleanup)에 따른다. 검증용 DB·스크립트·집계 결과는 작업용 임시 디렉터리에서만 사용하고 종료 시 제거했다. 실행 중인 서버는 임시 파일에 의존하지 않는다.
- Verification boundary: 이 후속 작업은 앱 코드 변경 없이 이미 통과한 migration을 운영에 적용했다. 전체 테스트를 반복하지 않았으며 기존 Google Drive 보류 범위와 파일럿 기능 유지 여부는 바꾸지 않았다.
