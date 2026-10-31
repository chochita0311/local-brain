# Session-Centered Refactoring Review

## Log Type

- Type: `Wrap-Up / Handoff`
- Date: `2026-10-30`
- Related tracks: [REFACTOR-0003](../refactor-0003-session-centered-package-boundaries.md), [REFACTOR-0004](../refactor-0004-direct-session-materials.md), [REFACTOR-0005](../refactor-0005-shared-resource-ownership.md).
- Scope: 사용자가 요청한 subagent 점검. 기능 패키지·계층, 세션 중심 자원 소유권, 선택 기능 제거 영향, 계획의 완료 주장과 실제 검증 범위를 평가한다. 코드 수정·기능 제거·운영 DB 재적용·merge 판단은 수행하지 않는다.
- Method: `refactor-plan`의 구조/의미 변경 구분과 validation gates를 적용했다. 두 `evidence_scout`가 패키지/import 및 자원/SQL/테스트 근거를 독립 수집하고, `bounded_verifier`가 정해진 검사를 실행했다. Primary가 요구사항 해석·설계 판단·근거 대조·최종 결론을 담당했다.

## Summary

- Goal: 폴더 이동을 넘어, 세션·문서·공용 자원을 중심으로 미확정 기능의 변경·제거 영향이 실제로 줄었는지 확인한다.
- Outcome: `Partial` — 핵심 패키지·저장·수집/읽기 경계는 구현됐고, 전체 앱 조립과 남은 기능 간 의존 및 persistence 내부 분리는 잔여다. REFACTOR-0005의 한정된 완료와 REFACTOR-0003 전체 완료를 구별한다.
- 이번 검토 범위에서 새 데이터 손상이나 동작 회귀는 확인하지 않았다. 아래 구조 잔여는 실제 import 경로와 기존 계획으로 확인했으며, 이미 알려진 잔여를 새 회귀로 재분류하지 않는다.

| 사용자 의도 | 판정과 근거 |
| --- | --- |
| 최상위 flat 파일을 기능별 패키지와 필요한 계층으로 정리 | 충족. 같은 Git HEAD의 최상위 Python 100개에서 현재 진입점 4개로 줄었다. 현재 직접 하위 Python 패키지는 24개다. `sessions/queries.py`, `local_context/queries.py`, `sources/queries.py`, 각 `web.py`, `app/application.py`·`routes.py`·`lifecycle.py`가 책임을 나눠 가진다. `tests/test_foundation_models.py:27`이 root 구성을 고정한다. |
| 공통 기반이 파일럿/실험에 종속되지 않음 | foundation/models/references 범위 충족. `tests/test_foundation_models.py:56,103`의 AST 및 격리 import 검사로 기반→기능/DB/web/추론 runtime 의존을 제한한다. 모든 기능 사이의 의존 부재를 증명하는 검사는 아니다. |
| Session이 발견한 URL·Markdown을 공용 자원으로 참조 | 충족. `schema.sql:243–277`, `resources/catalog.py:15–94`, `sessions/references.py:780–811`에 공용 identity, 기존 항목별 binding, Session evidence FK·조회가 있다. URL 분류는 등록 Atlassian 조회를 하지 않는다. |
| Local Context 본문과 선택 기능의 연결 소유권 분리 | 충족. 본문은 Context Document에 남고 연결은 binding을 거친다. 문서 색인 행 삭제 후에도 Session 관측이 남으며 동일 경로 재색인으로 열람을 복구한다. Context root 제거 API는 행 삭제와 달리 비활성화하며, 이때도 열람 가능 여부를 별도로 판단한다. |
| 세션 상세의 재정의 예정인 연결된 작업 제거 | 충족. `resources/related_context.py`, `sessions/web.py`, 관련 template는 직접 발견 자료를 표시하며 조직 관계 조회를 하지 않는다. Workstream/Thread의 기존 데이터는 별도로 보존한다. |
| 파일럿을 빼기 쉬운 앱 전체 경계 | 부분 충족. core 수집·읽기의 선택 의존은 줄었으나 일반 검색 HTTP, Maintenance, 전체 앱 조립 및 migration 내부 소유권에 잔여가 있다. 기능 폴더만 삭제하는 수준의 독립성을 주장하지 않는다. |

## What Changed

- Added: 이 독립 점검 기록과 우선순위별 잔여/exit gate.
- Updated: REFACTOR-0003에 REFACTOR-0005 이후 현재 판정을 추가하고, 이전 진행표·의존 설명은 당시 스냅샷임을 표시했다. 이전 완료 사실과 한계를 삭제하지 않았다.
- Moved/Renamed: 없음.
- Removed: 없음. 앱 코드·기능·운영 데이터는 변경하지 않았다.

## Behavior / Parity Notes

- Behavior-preserving intent: REFACTOR-0003의 패키지 이동은 구조 변경이다. REFACTOR-0004의 작업 연결 표시 제거와 REFACTOR-0005의 공용 identity/FK·자료 보존은 별도 승인된 의미 변경이다.
- Parity claim status: 전체 트랙은 `Provisional`; 후속 두 배치는 `Intentional deltas present`.
- Parity confidence basis: 이번 검토는 현재 구조/계약 audit와 targeted tests다. 모든 변경의 old/new query·write·output·side effect·failure 경로를 완전히 비교한 strict baseline audit가 아니므로 `Preserved`나 merge-safe로 올리지 않는다.
- 연결 자체가 결함인 것은 아니다. Session의 provider parser 재사용, Local Context의 ingestion observer 계약 호출, 앱의 명시적 기능 등록은 책임에 맞는 의존이다. observer를 통한 Atlassian 연동은 이미 달성한 분리 결과이며 미해결 직접 의존으로 세지 않는다.
- Atlassian Item만 제거할 때와 External Resource 자체를 명시적으로 purge할 때를 구별한다. 전자는 공용 본문·메모·Session 근거를 보존한다. 후자는 기존 계약대로 외부 본문·메모·조직 연결을 삭제하며, 공용 URL identity와 Session 근거는 남긴다. 사용자 소유 자료의 무조건적 삭제 방지를 주장하지 않는다.

## Validation

- Baseline/compare target: 현재 미커밋 작업 트리. HEAD `6c03265701d0d8b552fc8bb60e346ba1971f4bb3`은 초기 구조 기준이며, 단독 diff가 후속 배치의 정확한 기준은 아니다. 각 배치의 이전 manifest와 이행 증거는 기존 로그가 소유한다.
- Review pin: `src/localbrain`, `tests`, `scripts`, `pyproject.toml`, `uv.lock`의 캐시를 제외한 475개 파일별 SHA-256 manifest digest는 `1d3efabf6dac2774bceabbf373ee732dca1d391dd468428ee8fe2aaf9868ff51`. 점검 종료 시 같은 집합·바이트임을 확인했다. 문서 상태 보완은 이 코드 기준에 포함하지 않는다.
- Targeted tests: 격리된 임시 runtime/source/cache 설정에서 `.venv/bin/python -m unittest test_foundation_models test_shared_resources test_reference_urls test_session_references test_session_related_context test_session_reference_schema test_markdown_references` — **72개 통과**. `PYTHONPATH=src:tests`, `PYTHONDONTWRITEBYTECODE=1`. 기존 Starlette TemplateResponse 인자 순서 deprecation warning 1개, 실패 없음.
- Generated contracts: `check-data-model-docs.py`, `build-schema-presentation.py check`, `check-schema-cleanup-audit.py --check` 통과. 현재 ordinary tables 52, FTS5 1, FK 66, effective explicit indexes 51; audit 755 objects(keep 643, defer 112).
- Independent import probe: 각각 새 interpreter에서 MetaPathFinder로 `localbrain.atlassian`과 하위 package를 차단했다. `sessions.references`, `local_context.web`, `ingest.scanner` import 성공. `natural_search.web`, `maintenance.service`, `app.application` import는 차단된 의존으로 실패했다. 이 probe는 import 가능성만 검사하고 서버를 시작하거나 DB를 열지 않았다.
- Existing broader evidence: 직전 배치의 전체 unittest 1,463개, wheel/runtime 검사, 실제 운영 DB 보존·무결성·재시작 검증은 [REFACTOR-0005 실행 기록](2026-10-30_refactor-0005_shared-resource-ownership.md)이 소유한다. 이번 subagent 검토에서 재실행하거나 독립적으로 운영 DB를 재검증한 결과가 아니다.
- Review finish: `git diff --check`, repository privacy 검사 통과. 점검용 manifest와 격리 검증 상태는 종료 시 정리했다.

## Risks / Limitations

### 1. 일반 검색 HTTP가 Atlassian에 의존 — 우선 정리

`natural_search/web.py:9,16`은 `AtlassianRegistrationError`와 `atlassian.web._bounded_urlencoded_form`을 가져온다. 같은 모듈의 `natural_search_page`가 기본 keyword 경로도 제공하므로, Atlassian package가 없으면 검색 화면 모듈 전체가 import되지 않는다. 단순히 Atlassian route 등록을 지우는 것으로 해결되지 않는 기능 간 결합이다. 기존 REFACTOR-0003에 남은 의존으로 기록돼 있었고 이번 차단 probe로 재확인했다.

공통 HTTP 폼 해석을 중립적인 web 지원 코드로 옮기되 현재 content-type, 160 KiB 본문 한도, UTF-8 오류, 128개 필드 상한, 빈 값·중복 값 처리 및 endpoint별 422 응답을 보존해야 한다. Atlassian의 반복 필드(`item_id`, `topic_id`) 규칙을 일반 검색의 새 제품 계약으로 고정하지 않는다. Exit gate는 Atlassian import 차단 상태에서 keyword/AI 검색 HTTP import와 해당 폼 정상·실패 경로 통과다.

### 2. 전체 앱 시작에서 선택 기능을 제외하는 연결부 미완료

`app/lifecycle.py:11 → maintenance/service.py:13–27 → atlassian.refresh/sync, workstreams.retrieval/service`가 이어진다. `app/application.py:17–32`, `app/routes.py:3–18`, `app/lifecycle.py:60–75`도 선택 route/service를 항상 조립한다. 현재 full app의 동작 오류가 아니라, 기능 제거 시 정리할 범위가 core 밖의 한 연결부에 아직 충분히 모이지 않은 상태다.

기존 수집 observer와 읽기 callback 분리는 유지하고, Maintenance의 조직/외부 작업 adapter와 앱의 기능별 등록·시작·종료를 명시적으로 나누는 것이 다음 범위다. 사용자용 toggle이나 generic plugin framework를 새로 도입할 필요는 없다. Exit gate는 기존 schema를 유지한 synthetic fixture에서 각 파일럿 import를 차단하고 Session/Context/Usage/keyword 요청, 수집, lifespan 시작·종료를 함께 검증하는 것이다. 현재 import/module 검사와 optional-table 제거 후 특정 core 흐름 검사는 이 gate 전체를 대체하지 않는다.

### 3. Persistence 내부 책임 분리 잔여

`persistence/db.py`는 2,002줄이며 연결/transaction, 순서 있는 bootstrap, source identity·Atlassian access·usage·maintenance migration, index 수선을 함께 소유한다. 줄 수가 아니라 서로 다른 변경 이유와 복구 조건이 한 모듈에 모인 점이 잔여다. 새 shared-resource migration은 별도 파일로 분리했지만 원래 Step 10 전체를 마친 것은 아니다. `app/storage/recovery.py:307`도 복구 작업 구현과 HTTP 등록을 같은 파일에서 제공한다.

후속 정리는 기존 persistence owner 내부에서 migration 책임을 나누고 bootstrap 순서·backup/rollback·public connect/init/transaction 계약을 고정하는 범위여야 한다. 외부 부가 테이블 삭제나 DB 재설계와 섞지 않는다. Exit gate는 기존/fresh/실패/retry 초기화와 backup, storage route의 보존 검사다.

### 검증 한계

- optional-table 제거 검사는 직접 Context scan·참조 저장/읽기의 synthetic 경로다. 선택 package가 없는 전체 앱 시작을 검사하지 않는다. 기존 `web.py` 예외를 둔 AST guard도 위 검색 HTTP 역의존을 막지 못한다.
- migration rollback 검사는 한 failure hook과 retry를 포함하지만 모든 중단 지점/비정상 중간 schema를 증명하지 않는다. current-contract 검사도 전체 DDL 동등성 검사는 아니다. 이번에 손상된 실제 schema나 복구 실패를 관측한 것은 아니다.
- non-overwriting migration backup의 재사용은 최초 사본을 보존하는 계약이다. 기존 사본의 최신성까지 보장하지 않는다. 직전 운영 적용은 별도로 정지 DB와 생성된 사본의 일치를 확인했다.
- Google Drive 전송 11개는 사용자 보류를 유지했다. 이번에 전체 suite, 실제 provider, native/Tauri 재빌드, remote redirect 또는 모델 품질을 재검증하지 않았다.
- 공유 URL의 도메인 간 자동 병합, 미등록 Markdown 자동 읽기, 파일럿 제품 채택·삭제는 승인된 정리 범위가 아니다.

## Next Action

REFACTOR-0005의 공용 자원 경계는 완료 상태를 유지한다. REFACTOR-0003은
`in-progress`를 유지한다. 위 1 → 2 → 3의 후속 범위와 exit gate는
[현재 계획](../refactor-0003-session-centered-package-boundaries.md#current-review-after-refactor-0005)에 반영했다.
legacy `/search`의 `search/legacy.py:43` Atlassian 결합은 개발용 검색 공급자 연결로
추적하되, 현재 기본 keyword 검색의 공용 폼 역의존과 혼동하지 않는다.
작업별 exit gate가 충족되기 전에는 전체 탈부착 완료나 strict parity를 선언하지 않는다.
