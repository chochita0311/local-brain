# Session Intent And Completion Review

## Log Type

- Type: `Wrap-Up / Handoff`
- Date: `2026-10-31`
- Related tracks: [REFACTOR-0003](../refactor-0003-session-centered-package-boundaries.md), [REFACTOR-0004](../refactor-0004-direct-session-materials.md), [REFACTOR-0005](../refactor-0005-shared-resource-ownership.md).
- Scope: 사용자 요청에 따라 이번 세션의 원래 목적과 중간 합의, 마지막 앱 셸/기능 책임 논의까지 대조하는 재점검. 코드 수정·운영 DB 재적용·서버 전환·기능 제거·병합 판단은 수행하지 않는다.
- Review method: `refactor-plan`의 scope/invariant/ownership/wiring/validation/exit gate 기준. `evidence_scout` 두 작업이 패키지·실행 의존과 자원·SQL·표시 근거를 나눠 조사하고, `bounded_verifier`가 정해진 검사를 실행했다. Primary는 요구사항 해석, 설계·완료 판정, 추가 재현과 기록을 담당했다.

## Summary

- Goal: flat 파일 이동을 넘어 세션 중심 자원 소유권과 기능별 책임이 분리됐고, 미확정 파일럿의 교체·제거 영향을 한정할 수 있는지 확인한다. 하나의 앱과 공유 DB를 사용하는 모듈형 모놀리스가 기준이며 MSA나 별도 DB/배포 단위는 요구사항이 아니다.
- Outcome: `Partial`. 핵심 패키지·공용 자원·세션 읽기·실행기·기본 조립은 충족한다. 기존 Auto Work 캐시가 남은 공통 Settings 정리 경로에 기능 구현 의존이 남아 실제 제외 조립에서 실패했다.
- Correction: 직전 구조 트랙 `completed` 판정을 `in-progress`로 정정하고 Step 9/11을 이 한정된 잔여에 대해 다시 연다. 기존 12개 조립 경우와 전체 테스트의 통과 사실을 취소하는 것은 아니다. 그 검사는 기존 기능 캐시를 남긴 공통 정리 요청을 포함하지 않았다.
- 기본 기능 집합의 실행 회귀나 데이터 손상을 이번 검토에서 발견한 것은 아니다. R1은 선택 기능을 제외하는 경우의 잔존 상태 처리와 책임 분리 문제다.

| 세션에서 합의한 목적 | 현재 판정과 근거 |
| --- | --- |
| 최상위 flat 파일 정리와 기능 내부의 필요한 계층 분리 | 충족. root Python은 `__init__`, `main`, `cli`, `desktop` 4개이며 기존 100개와 구별된다. `web`/`queries`/`store`, 공용 foundation/models, persistence bootstrap/migrations의 소유자가 나뉜다. root 전체 재수출 facade로 대체하지 않았다. |
| 공용 자원과 세션별 발견 매핑 | 충족. `reference_resources`가 URL/path identity를 소유하고 `session_reference_evidence`가 Session과 자원 및 관측 위치를 연결한다. 여러 세션이 같은 자원을 참조해도 근거는 세션별로 유지된다. |
| Atlassian 탭/설정에 독립적인 URL 분류 | 충족. 공용 `references/`에서 로컬 URL 문법을 해석한다. 등록 없이 Jira/Confluence를 구분하고 title 없는 `/wiki/spaces/TEAM/pages/123`와 같은 도메인의 legacy page URL을 같은 identity로 묶는다. 다른 도메인의 숫자 ID를 추측 병합하지 않는다. Slack 분류와 실제 redirect 확인은 구현 범위가 아니다. |
| Local Context 본문·목록과 선택 기능의 매핑 분리 | 충족. `context_documents`가 본문·path·relative_path를 보유하고 문서 tree는 상대 경로에서 구성한다. `local_resources`는 별도 파일/폴더/저장소 경로 북마크이며 본문 색인이 아니다. 각 binding은 공용 path identity를 공유할 수 있고 수동 메타데이터를 덮어쓰지 않는다. 색인 행이 없어져도 Session 근거는 남고 동일 경로 재색인으로 열람 연결을 복구한다. |
| 세션에서 직접 발견한 관련 자료와 연결된 작업 제거 | 충족. 직접 근거만 읽어 단일 `direct` 자료 그룹을 표시한다. 연결된 작업 strip과 조직 기반 간접 자료 조회는 제거됐고 Workstream/Thread 데이터는 보존한다. 별도의 선택적 작업 흐름 화면 링크까지 제거한 것은 아니다. |
| 앱 셸은 연결, 기능 패키지는 자기 실행 책임 | 기본 범위 충족. 메뉴·route·callback·lifecycle 조립은 앱, 업무 실행은 기능이 소유한다. 공통 Run 상태는 기능의 coroutine을 추적하고 Workstream/Atlassian 실행 구현을 import하지 않는다. Run 중단 복구는 실행 기능이 포함된 개발 웹에서만 호출하며 desktop 미호출 조건을 유지한다. |
| 일반 검색의 기능 독립성 | 충족. 일반 keyword/AI HTTP 폼은 `app/forms.py`를 사용한다. Atlassian 결과를 합치는 legacy `/search`는 별도 기능 기여로 남고 일반 검색과 구별된다. |
| 파일럿 제거 시 공통 기능과 기존 자료의 처리 | 부분 충족. 다섯 파일럿 각각 및 전부를 제외한 양 edition의 수집·기본 읽기·시작/종료는 통과한다. 공통 Settings 캐시 정리는 기존 Auto Work 상태가 있을 때 제외한 구현을 다시 요구한다(R1). |
| 저장 책임·마이그레이션·기존 데이터 보존 | scoped 근거 충족. 연결/transaction, bootstrap, 주제별 migration, 복구 작업/HTTP가 분리됐다. REFACTOR-0005의 운영 적용과 보존·무결성·재시작 증거는 이전 실행 기록이 소유한다. 이번에는 운영 DB를 재열거나 재적용하지 않았다. |

## What Changed

- Added: 이 재점검 기록과 R1의 재현·수정 경계·검증 조건.
- Updated: REFACTOR-0003 현재 상태와 Step 9/11, plans index. 오래된 Session→Atlassian FK 설명은 해당 문단 바로 옆에 최초 계획 당시 사실임을 표시하고 현재 공용 자원 FK로 교체됐음을 적었다. REFACTOR-0005 운영 적용의 기존 완료 사실도 index에 명확히 반영했다.
- Moved/Renamed / Removed: 없음. 앱 코드·테스트·schema·설정과 실제 사용자 데이터는 변경하지 않았다. 이전 배치의 실행 log를 사후 수정하지 않았다.

## Behavior / Parity Notes

- REFACTOR-0003은 Structural / Internal Interface, 연결된 작업 제거와 공용 identity/FK 이행은 각각 승인된 REFACTOR-0004/0005의 Behavioral / Semantic 변경이다. 서로의 parity 증거로 소급하지 않는다.
- Parity claim status: 전체 strict parity는 `Provisional`; semantic 배치는 `Intentional deltas present`. 이번 검토는 현행 책임·의존·행동 확인이며 모든 old/new write/output/side-effect/failure 경로의 strict audit나 merge 승인이 아니다.
- 현재 코드가 이전 최종 source checkpoint와 같음을 확인했기 때문에 기존 full suite·wheel·frozen/browser 결과는 같은 코드의 기존 증거로 인용한다. 이번 subagent가 해당 빌드나 전체 suite를 새로 실행했다고 주장하지 않는다.
- 공유 DB의 교차 FK나 명시적인 기능 간 매핑은 그 자체로 설계 위반이 아니다. `sessions.maintenance_run_id`와 Run 표시용 Workstream join은 보존된 실행 이력 계약이다. Workflow의 Workstream/Thread 조회와 Atlassian의 조직 범위 refresh도 해당 선택 기능의 기능적 관계다. 실제 table 제거 때 함께 판단할 지점이며 Session URL의 Atlassian 직접 FK가 남아 있다는 뜻은 아니다.
- 공용 Settings의 cache-clear가 제외한 Auto Work 구현을 불러오는 것은 위의 저장 이력 계약과 구별한다. 선택 기능 집합을 이미 받는 앱의 공통 작업 경로가 같은 제외 조건을 따르지 않는 재현 가능한 문제다.

## Validation

- Baseline / review pin: 현재 미커밋 작업 트리. HEAD `6c03265701d0d8b552fc8bb60e346ba1971f4bb3`, source/tests/scripts/pyproject/lock 495개 파일의 path→SHA-256 compact sorted JSON digest `a2df266bd8ba286c0ef7b63d75ab71a0d41a683fde7921722bf914223dbaf188`. 직전 [앱 조립 기록](2026-10-31_refactor-0003_feature-assembly.md)의 최종 checkpoint와 일치한다. 문서 리뷰 변경은 이 코드 기준에 포함하지 않는다.
- Independent targeted tests: `.venv/bin/python -m unittest -v test_feature_assembly test_foundation_models test_reference_urls test_shared_resources test_session_related_context test_session_references test_session_reference_schema test_workstream_runner` — **76개 통과**, 6.876초. `test_feature_assembly` 안의 **12개 subprocess 조립 경우**를 포함한다. 이 경우 수를 unittest test 수에 더하지 않는다.
- Test environment: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=src:tests`, `LOCALBRAIN_EDITION=web`; data/cache/development/source/model cache를 private synthetic 경로로 격리하고 model offline 설정을 적용했다. 조립 검사는 자기 subprocess에서 web/desktop을 각각 설정한다.
- Generated contracts: data-model docs, value dictionaries, schema presentation, cleanup audit의 check 모드와 `git diff --check` 모두 통과했다. ordinary tables 52, FTS5 1, physical FK 66, explicit indexes 51, subject owners 11; audit 755 objects(keep 643/defer 112)를 유지한다.
- Source evidence: 패키지 root/entrypoint, 함수 내부 import와 조건부 조립, route/nav/lifecycle, 공용 URL/path identity, DB FK와 binding, Session 관련 자료 producer→handler→template, migration 소유권과 테스트의 실제 검증 범위를 대조했다. 외부 저장소의 내부 import 소비자까지 조사한 것은 아니다.
- Root additional probe — R1: `auto_work`를 제외한 `create_app`에 해당 package import를 차단했다. 실제 `/api/settings/cache/clear` route handler에 같은 앱의 Request를 전달했을 때 빈 캐시는 `{"removed_bytes": 0}`으로 성공했다. 이어 합성 `session-simulation` 캐시를 만들자 `ModuleNotFoundError`가 발생했다. 네 파일은 보존됐고 search.start는 두 호출 모두 실행됐다. 실제 HTTP socket이나 live user cache를 사용한 결과가 아니라 동일 endpoint handler의 합성 재현이다.
- Root additional probe — explicit purge: 기존 in-memory fixture에서 `bind_external_link(40)`와 Session reference를 만든 뒤 `purge_atlassian_item(40)`를 실행했다. External Resource와 그 binding은 삭제됐고 `reference_resources` 및 `session_reference_evidence`의 전체 행은 동일하게 남았으며 FK 검사가 통과했다. 기존 영구 테스트에서 직접 단언하지 않던 이 경로를 이번 리뷰에서 확인했으며 새 회귀 테스트 파일을 추가한 것은 아니다.
- Existing broader evidence: 이전 전체 **1,473개 통과**, source/wheel 응답 비교, 실제 frozen backend 시작·종료·재시작과 Chrome 검증은 직전 실행 기록을 따른다. 이전 운영 DB migration은 REFACTOR-0005 기록을 따른다. 모두 이번 재점검의 신규 실행 수치와 구별한다.
- Review finish: 코드 checkpoint 495개 파일의 동일성을 다시 확인했다. 문서 링크·whitespace·`git diff --check`와 repository privacy 검사(1,802 candidate files)를 통과했다. 검증 프로세스가 종료되고 열린 파일이 없음을 확인한 뒤 review manifest·probe·synthetic runtime·로그·작성 scratch를 모두 제거했다. 이 기록은 임시 경로에 의존하지 않는다.

## Risks / Limitations

### R1 — Common Cache Cleanup Reimports Omitted Auto Work

- Status: `open`, 우선 보완할 구조 경계 1건. 기본 앱의 회귀로 분류하지 않는다.
- Call path: `app/storage/web.py:84`의 cache-clear → `app/storage/recovery.py:264`의 `clear_owned_cache` → 같은 파일 `:297`의 무조건적인 `maintain_derived_cache` → `app/storage/layout.py:180`의 Auto Work simulation import.
- Trigger: Auto Work가 미탑재이고 과거 `<cache>/session-simulation` 폴더가 남아 있다. 빈 캐시에서는 해당 branch를 지나지 않으므로 기본 조립 검사가 이 결합을 드러내지 못했다. `auto-work-preview`도 같은 함수의 `:193`에서 feature parser를 import하지만 이번 직접 재현은 simulation 분기다.
- Impact: 기능을 뺀 앱에서 공통 Settings 캐시 정리가 실패한다. search 재시작의 `finally`와 기존 캐시 보존은 동작한다. 공통 검색 캐시가 이미 삭제된 뒤 feature 정리에서 실패할 수도 있는 순서이나 그 부분 삭제 시나리오는 이번 재현에서 실행하지 않았다.
- Why this matters: `app/application.py`가 시작 시 preview cleanup을 feature 조건에 따라 연결해도 Settings의 후속 동작에는 그 조건이 적용되지 않는다. feature 소유 만료·해석 정책이 `app/storage/layout.py`에 남고 CLI storage 작업도 이를 직접 사용한다. 기능이 자기 상태를 책임지고 앱이 연결한다는 세션 합의를 이 경로에도 적용해야 한다.
- Bounded next change: Auto Work 캐시 해석·만료 정책을 feature 소유자로 응집하고 공통 파일 안전성과 앱/CLI 연결을 분리한다. 공통 캐시 정리는 명시적으로 포함된 handler를 호출하며, 미탑재 기능의 잔존 자료 처리 정책을 정의한다. 기본 앱의 기존 정리 동작과 ownership/lock/unknown-file/symlink 보호를 보존하고 임의 파일 삭제나 포괄적 ImportError 무시로 해결하지 않는다.
- Exit gate: 기존 simulation/preview 캐시가 있는 web/desktop의 미탑재 조립에서 공통 캐시 정리가 성공하고 feature 구현을 import하지 않는다. 잔존 파일의 지정 보존 정책, 기본 앱 만료 정리, busy/unowned/symlink 거부, search 재시작, Settings/CLI 연결을 검증한다.

### Scope And Evidence Limits

- Google Drive 전송 `PoolTests` 11개는 사용자의 보류 지시를 유지했다. Drive의 강제 제거 가능성이나 모든 외부 connector의 독립성을 이번 5개 feature 조립 검사로 주장하지 않는다.
- 실제 기능/테이블 삭제, 모든 feature 조합, native Tauri/WKWebView, 외부 provider·모델 실행/품질, 원격 redirect는 이번 리뷰 범위 밖이다. 운영 DB·실행 중 서버·설치된 앱에 새 작업을 하지 않았다.
- 공용 identity 보존과 본문·메모 보존은 삭제 종류를 구별한다. Atlassian 등록 행만 제거하면 공용 payload가 남는다. 명시적인 전체 External Resource purge는 기존 계약대로 payload와 조직 연결을 지우되 Session의 URL identity·근거는 남긴다.
- 새 파일럿 채택·Slack 분류 구현·미등록 Markdown 자동 읽기·DB 분할은 승인된 정리 요구가 아니다. 이를 미완료 목록에 임의로 추가하지 않는다.

## Next Action

REFACTOR-0004/0005와 이미 확인한 core 자원·조회·기본 조립의 완료 범위는 유지한다.
REFACTOR-0003 Step 9/11에서 R1의 feature 캐시 책임·공통 호출 경계와 기존 상태 검증을
닫는다. 이것이 이번 목적의 남은 구현 범위다. 기존 기록의 strict parity와 Drive/native
검증 한계는 별도로 유지하며, 한 경로를 고쳤다는 이유로 merge-safe를 선언하지 않는다.
