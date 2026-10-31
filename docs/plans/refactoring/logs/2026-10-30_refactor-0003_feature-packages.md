# REFACTOR-0003 Feature Packages And Delivery Layers

## Log Type

- Type: `Batch`
- Date: `2026-10-30`
- Related track: [Session-Centered Package Boundaries](../refactor-0003-session-centered-package-boundaries.md)
- Scope: 기능별 패키지, HTTP/조회/저장 책임, 공용 자원 경로와 소비자 재연결. 첫 기반/모델 배치 이후의 구조 실행 기록이다.

## Summary

- Goal: `src/localbrain`에 남은 Atlassian·Workstreams·Workflow·Auto Work 및 세션 중심 구현을 기능별 폴더와 실제 책임으로 묶는다.
- Outcome: `Pass` for the package-layout batch; the broader isolation track remains `in-progress` and strict parity remains `Provisional`.
- 첫 실행에서 Step 1–3만 수행한 것은 요청한 폴더/계층 정리를 충분히 수행하지 못한 범위 판단이었다. 사용자의 후속 지적에 따라 실제 기능 패키지와 main/query/resource 분리를 실행했다. 사용자가 나머지 패키지 정리를 보류한 것으로 해석하지 않는다.
- 최상위 Python 파일은 최초 100개 → 기반/모델 배치 후 89개 → 현재 `__init__.py`, `main.py`, `cli.py`, `desktop.py` 4개다. 전체 Python 모듈은 202개이며 줄 수나 파일 수 감소를 품질의 증거로 삼지 않는다.
- Google Drive는 사용자가 보류 수준으로 지정했다. 구현은 유지하고 loopback HTTP 서버가 필요한 전송 검사 11개를 완료 조건에서 제외했다.

## What Changed

### Application And Feature Boundaries

- `main.py`는 `create_app()`의 안정적인 ASGI 진입점이다. `app/application.py`, `app/lifecycle.py`, `app/routes.py`, `app/templating.py`가 앱 생성, 서비스 start/stop, 기존 순서의 라우트 등록, 공통 렌더링을 각각 소유한다.
- 기존 route 함수와 Pydantic 입력 모델은 각 기능의 `web.py`에 둔다. URL/method/name·등록 순서·schema metadata와 decorator의 의미는 명시적 등록으로 유지한다. 새 router framework나 optional import fallback은 만들지 않았다.
- `queries.py`는 아래 소비자별로 분할했다. Workstream 일반 자원 저장은 조직 service에서 분리했고, durable skill 관측 저장과 Insights 랭킹도 분리했다.
- feature service/query/contract가 앱 조립이나 web handler를 import하지 않는 경계를 검사한다. HTTP adapter는 공통 앱 presentation을 사용한다. 모든 기능에 동일한 service/repository 파일 세트를 강제하지 않는다.
- package `__init__.py`에 옛 flat API를 재수출하는 facade를 만들지 않았다. 공개 `python -m localbrain.auto_work`만 `auto_work/__main__.py`에서 명시적으로 유지한다. 앱 CLI, `localbrain.main:app`, frozen worker flags는 유지한다.

| 이전 혼합 책임 | 현재 소유자 |
| --- | --- |
| `main.py` 앱 생성·전역 template·lifespan·route decorator | `main.py` 진입점 + `app/{application,lifecycle,routes,templating,request_guards}.py` |
| `main.py` 화면/API 함수와 입력 모델 | `app/web.py` 및 `sessions`, `sources`, `local_context`, `usage`, `resources`, `workstreams`, `maintenance`, `workflow`, `auto_work`, `atlassian`, `insights`, `natural_search`, `search`, `persistence`의 `web.py` |
| `queries.py` 세션 inventory/chart/detail/events/project | `sessions/queries.py` |
| `queries.py` 문서 조회 / source inventory / 개발 대시보드 집계 | `local_context/queries.py` / `sources/queries.py` / `app/dashboard_queries.py` |
| `queries.py` legacy 검색·FTS 표현식 / pagination | `search/{legacy,lexical}.py` / `foundation/pagination.py` |
| `workstreams.py` 일반 외부/로컬 자원 생성·상세·종류 | `resources/store.py`; 조직 membership·review는 `workstreams/service.py` |
| `workstreams.py` optional 문자열 정리 | 실제 두 소비자가 공유하는 `foundation/text.py`; 기존 null/공백 반환 계약 유지 |
| `session_context.py` 관련 자료 조합 | `resources/related_context.py`; 조직/Atlassian SQL 의존을 가진 명시적 read adapter |
| `skill_observations.py` durable 관측 / Insights 랭킹 | `sessions/skills.py` / `insights/skills.py` |
| `auto_work.py` preview 계산/읽기 / module 명령 | `auto_work/preview.py` / `auto_work/{cli,__main__}.py` |

### Module Ownership Map

다음은 84개 이전 모듈의 주 소유 경로다. 위 분할표는 그중 여러 책임을 나눈 모듈의 추가 목적지를 지정한다. 경로는 `src/localbrain/` 기준이다. 기존 `ingest/`, `natural_search/`, `context_search/`, `google_drive/`, `foundation/`, `models/`의 소비 import도 새 소유자에 연결했다.

| 이전 모듈 | 현재 주 소유자 |
| --- | --- |
| `activity.py` | `sessions/activity.py` |
| `app_docs.py` | `app/docs.py` |
| `atlassian.py` | `atlassian/catalog.py` |
| `atlassian_browse.py` | `atlassian/browse.py` |
| `atlassian_evidence.py` | `atlassian/evidence.py` |
| `atlassian_evidence_sync.py` | `atlassian/evidence_sync.py` |
| `atlassian_locators.py` | `atlassian/locators.py` |
| `atlassian_refresh.py` | `atlassian/refresh.py` |
| `atlassian_registration.py` | `atlassian/registration.py` |
| `atlassian_structure_references.py` | `atlassian/structure_references.py` |
| `auto_work.py` | `auto_work/preview.py` |
| `context_sync.py` | `sources/context_sync.py` |
| `contexts.py` | `local_context/service.py` |
| `db.py` | `persistence/db.py` |
| `edition.py` | `app/edition.py` |
| `external_access.py` | `atlassian/access.py` |
| `external_sync.py` | `atlassian/sync.py` |
| `google_drive_web.py` | `google_drive/web.py` |
| `keyword_search.py` | `search/keyword.py` |
| `learning.py` | `learning/service.py` |
| `learning_cli.py` | `learning/cli.py` |
| `learning_web.py` | `learning/web.py` |
| `local_picker.py` | `app/picker.py` |
| `markdown.py` | `rendering/markdown.py` |
| `markdown_references.py` | `local_context/references.py` |
| `official_pricing.py` | `usage/pricing.py` |
| `personal_insight_evidence.py` | `insights/evidence.py` |
| `personal_insight_guidance.py` | `insights/guidance.py` |
| `personal_insight_runs.py` | `insights/runs.py` |
| `personal_insight_usage.py` | `insights/usage.py` |
| `retrieval.py` | `workstreams/retrieval.py` |
| `runner.py` | `maintenance/service.py` |
| `runtime_storage.py` | `persistence/storage.py` |
| `schema_explorer.py` | `persistence/explorer.py` |
| `schema_presentation.py` | `persistence/schema_presentation.py` |
| `session_affinity.py` | `auto_work/affinity.py` |
| `session_chart_preferences.py` | `sessions/chart_preferences.py` |
| `session_context.py` | `resources/related_context.py` |
| `session_pins.py` | `sessions/pins.py` |
| `session_reading.py` | `sessions/reading.py` |
| `session_references.py` | `sessions/references.py` |
| `session_simulation.py` | `auto_work/simulation.py` |
| `session_simulation_cli.py` | `auto_work/simulation_cli.py` |
| `session_simulation_graph.py` | `auto_work/graph.py` |
| `session_sources.py` | `sources/registry.py` |
| `session_sync.py` | `sources/session_sync.py` |
| `settings_web.py` | `app/settings.py` |
| `skill_observations.py` | `sessions/skills.py` |
| `source_identity_migration.py` | `persistence/source_identity_migration.py` |
| `source_profiles.py` | `sources/profiles.py` |
| `source_revision_migration.py` | `persistence/source_revision_migration.py` |
| `source_settings.py` | `sources/settings.py` |
| `source_sync.py` | `sources/sync.py` |
| `storage_layout.py` | `app/storage/layout.py` |
| `storage_recovery.py` | `app/storage/recovery.py` |
| `subagents.py` | `sessions/subagents.py` |
| `usage.py` | `usage/records.py` |
| `usage_queries.py` | `usage/queries.py` |
| `value_registry.py` | `persistence/value_registry.py` |
| `work_claim_assessment.py` | `experiments/claims/assessment.py` |
| `work_claim_trial.py` | `experiments/claims/trial.py` |
| `work_claims.py` | `experiments/claims/contract.py` |
| `work_context.py` | `experiments/context/contract.py` |
| `work_context_classified.py` | `experiments/context/classified.py` |
| `work_context_diagnostic.py` | `experiments/context/diagnostic.py` |
| `work_context_evaluation.py` | `experiments/context/evaluation.py` |
| `work_context_evidence.py` | `experiments/context/evidence.py` |
| `work_context_selected.py` | `experiments/context/selected.py` |
| `work_context_staged.py` | `experiments/context/staged.py` |
| `work_reconstruction.py` | `experiments/reconstruction/contract.py` |
| `work_reconstruction_experiment.py` | `experiments/reconstruction/experiment.py` |
| `work_reconstruction_input.py` | `experiments/reconstruction/input.py` |
| `work_reconstruction_preparation.py` | `experiments/reconstruction/preparation.py` |
| `work_reconstruction_scoring.py` | `experiments/reconstruction/scoring.py` |
| `work_role_comparison.py` | `experiments/context/role_comparison.py` |
| `work_state.py` | `experiments/claims/state.py` |
| `workflow_assertions.py` | `workflow/assertions.py` |
| `workflow_correction.py` | `workflow/correction.py` |
| `workflow_correction_view.py` | `workflow/correction_view.py` |
| `workflow_focus.py` | `workflow/focus.py` |
| `workflow_map.py` | `workflow/map.py` |
| `workflow_projection.py` | `workflow/projection.py` |
| `workstream_candidates.py` | `workflow/candidates.py` |
| `workstreams.py` | `workstreams/service.py` |

### Package Data, Tests And Owner Documents

- `schema.sql`, schema/value JSON, templates/static, app guide와 versioned insight guide는 원래 package data 위치에 둔다. 깊이에 의존하던 경로를 `foundation.paths.package_root()`로 연결하고 기존 private-data 거부 경계는 별도 `package_boundary()`로 유지했다.
- migration의 schema 읽기, 백업 schema digest, Docs/Insights content와 trial source fingerprint의 대상 파일을 확인했다. 외부 모델 ID·revision·asset hash·manifest schema와 공개 cache 소유 규칙은 변경하지 않았다.
- source/test/script import, 내부 patch 위치, 직접 실행하는 Python 문자열을 실제 소유 모듈에 맞췄다. `localbrain.db` 데이터 파일명은 유지한다. HTTP 테스트의 DB fixture는 handler와 공용 template context processor 각각에 주입한다.
- 새 경계 검사 3개는 최상위 진입점 소유, feature logic→app/web 역의존 금지, 선택 기능을 차단한 새 interpreter의 핵심 Session/resource import다. 기존 source/wheel/frozen path 검사에는 package-data 위치 검증을 추가했다.
- Architecture와 현재 owner 문서·명령 참조, Data Model source digest, value registry와 생성 dictionary, schema presentation, 현재 schema audit digest/ledger를 갱신했다. 이전 계획/실행 이력은 현재 경로로 덮어쓰지 않았다. DDL과 schema audit의 결정은 바꾸지 않았다.

## Behavior / Parity Notes

- Behavior-preserving intent: 수집·조회·저장·검색·조직 검토·오류/취소·worker·startup/shutdown의 기존 동작을 구조 이동으로 보존한다. SQL, schema bytes, transaction 경계와 명시적 외부 접근의 승인 조건은 재설계하지 않았다.
- Intentional structural/interface deltas: 내부 Python import 및 정의의 `__module__`, 소스 경로와 소스 바이트에 결합된 지문은 이동 결과를 따른다. Claims trial의 구현 fingerprint는 실제 새 source 경로를 사용하므로 이전 소스에 결합된 결과는 같은 구현으로 취급하지 않는다. 이는 모델 cache의 ID/version 변경이 아니다. 조사 범위에 모듈 경로를 저장한 pickle/type 복원 소비자는 없었다.
- 2,175개 기존 top-level 함수/클래스/상수 정의를 새 소유자와 대응했다. import·모듈/파일 경로·HTTP decorator 이동을 정규화하면 2,169개가 AST로 같고 누락은 없다. 나머지 6개는 Docs/백업 schema/trial의 package-root 경로, template package root, `app = create_app()` 조립으로 직접 검토했다. 함수 내부 SQL·조건·순서·catch/write 본문도 이 비교 범위에 포함한다.
- 경로 정규화가 저장 owner/version 문자열 변경을 가리지 않도록 정의 안의 실제 string literal도 별도로 비교했다. 변경은 Claims trial의 구현 fingerprint가 읽는 6개 source 경로뿐이며, 저장 owner/version·SQL·모델 identity 문자열은 같았다.
- 초기 검사에서 옛 patch/파일 경로, 분리된 template DB fixture, 생성 provenance와 migration schema 경로식, 실행 문자열 변환 오류를 발견해 수정했다. 최종 검증은 수정된 코드 기준이다.
- Parity claim status: `Provisional`.
- Parity confidence basis: structural declaration comparison + wiring comparison + synthetic regression/runtime/build evidence. 모든 실제 외부 호출·모델 실행·native interaction과 선택 기능 없는 전체 앱 흐름의 strict audit를 완료한 것은 아니다.

## Validation

### Baseline And Final Source

- HEAD: `6c03265701d0d8b552fc8bb60e346ba1971f4bb3`.
- 비교 대상은 HEAD만이 아니라 그 위의 첫 기반/모델 배치 미커밋 결과다. 시작 전 150개 Python 파일 inventory가 앞 배치의 검증 지문 `f11fccdd23717d84ddce22e860aa4a85c9621e2896d2a4b2e94b6020a5f6dcd1`과 같음을 확인했다.
- 최종 202개 Python 파일 inventory SHA-256: `4a45727e605f06c90da6ad2df3aa706fc7006172fd576b6dbb49b35689eeac0a`.
- inventory는 정렬한 `src/localbrain/...py:파일 SHA-256` 행과 마지막 newline의 SHA-256이다. 앞 배치와 이번 변경은 미커밋 상태이며 사용자 설치 앱이나 runtime DB를 교체하지 않았다.

### Tests And Static Checks

- 기존 Python 3.11.15 `.venv`로 전체 `unittest discover`를 실행했다. `test_google_drive_transport.PoolTests.`의 정확히 11개만 사용자 보류에 따라 제외했고 **1,443개가 통과**했다. 소스/세션/참조/Usage, query/HTTP, 검색, Workstreams/Workflow/Atlassian, migrations/storage/recovery와 모델/실험 계약 검사를 포함한다.
- 재현 시 먼저 `LOCALBRAIN_DATA_DIR`, `LOCALBRAIN_CACHE_DIR`, `TMPDIR`을 독립된 task-owned 임시 디렉터리로 지정한다. 테스트 선택은 다음과 같다.

```python
import unittest

suite = unittest.defaultTestLoader.discover("tests")
def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item
all_cases = list(cases(suite))
deferred = [test for test in all_cases
            if test.id().startswith("test_google_drive_transport.PoolTests.")]
assert len(deferred) == 11
result = unittest.TextTestRunner(verbosity=2).run(
    unittest.TestSuite(test for test in all_cases if test not in deferred))
raise SystemExit(not result.wasSuccessful())
```

- 별도 새 interpreter import 검사는 핵심 Session activity/query/reading/pins/chart/skills/subsessions, resource store, Local Context query/reference와 source profiles에서 Workstreams·Workflow·Auto Work·Atlassian·Experiments·Insights·Context Search·Drive 및 inference runtime을 차단하고 통과했다. 전체 수집/lifespan을 선택 기능 없이 실행했다는 뜻은 아니다.
- 최종 source에서 기존 **114개 route의 순서·method·name·schema 노출, OpenAPI, exception handler 및 middleware 등록이 비교 기준과 동일**했다.
- 실행 Python/JS/shell/build 소비자의 이전 module 문자열을 점검했고, 유지하는 package/module 명령과 DB filename 외의 미해결 옛 참조는 발견하지 않았다.
- Data Model/value dictionaries/schema presentation/cleanup-audit 검사는 전체 테스트에서 통과했다. `schema.sql` bytes는 동일하며 49개 table(FTS 포함), 543개 column, 52개 explicit index, 59개 physical relation, 29개 application relation과 audit 620 keep/112 defer를 유지한다.
- `git diff --check`와 `./scripts/check-repo-privacy.sh`: 통과. private stage와 build/synthetic runtime은 Git 대상에서 제외했다.

### Wheel, Runtime And Frozen Backend

- 기존 캐시의 Hatchling으로 wheel을 만들고 `uv pip install --offline --no-deps --target <isolated-site-packages>`로 설치했다. 설치된 202개 Python 파일과 schema/registry package data는 source bytes와 같았다. 의존성 업그레이드나 모델 다운로드는 없었다.
- 설치 wheel의 CLI `--help`와 유지한 `python -m localbrain.auto_work --help`도 성공했다.
- Wheel SHA-256: `14629e3d2240aff511a3db15e37be9c201fbfcbc0266cb9f4aa0330d95f570a2`.
- 기준 source, 변경 source, 설치 wheel 각각에서 개발/데스크톱 두 edition의 실제 lifespan을 시작하고 종료했다. 모델 모듈의 실제 import를 차단한 채 각각 16개 ASGI 요청을 실행했다: health, Session 목록/Chart/상세, Usage Dashboard, Context/Document, keyword search, settings, Docs, static CSS, Workstreams, Atlassian, Auto Work, Schema, Workflow.
- 개발 edition의 요청은 200, 데스크톱에서 기존 제외 대상 5개는 404였고 나머지는 200이었다. 모든 status·header·body를 기준과 비교했다. 독립 runtime의 경로, static asset mtime query 및 synthetic seed의 DB-default 생성/갱신 시각 3필드만 정규화했으며 그 외 응답은 동일했다. 각 source/wheel 당 32개 응답 비교다.
- 실제 `desktop/backend.spec`의 PyInstaller 6.22.3 backend 빌드가 성공했다. PYZ의 재배치된 앱 조립·feature·worker 21개 표본을 확인했고 schema/JSON·templates/static·Docs/Insights guide 109개 resource가 source bytes와 같았다.
- 실제 frozen `--install-search-model`은 잘못된 key와 bundle 내부 runtime 경로를 `{"phase":"failed"}`, exit 1로 거부했고 data directory를 만들지 않았다.
- 실제 frozen Context Search worker는 빈 독립 Hub cache와 offline 설정에서 `loading → MODEL_NOT_CACHED`를 반환했다. owner stdin EOF 후 exit -15로 종료했다. 모델을 받거나 실제 추론하지 않았다.
- frozen backend의 실제 HTTP 시작도 시도했으나 sandbox가 `127.0.0.1` bind를 `PermissionError: Operation not permitted`로 거부했다. full frozen HTTP/browser/native window 검증은 완료하지 못했다. 위 ASGI/worker 검증과 구별한다.

## Risks / Limitations

- `resources/related_context.py`는 Session reference와 Workstream/Thread/Atlassian 테이블을 조합한다. 일반 resource store의 독립성과 이 adapter의 SQL 의존은 다르다.
- `sessions/references.py`, `ingest/sync/`, `local_context/service.py`는 현재 transaction 안에서 Atlassian evidence 구현을 호출한다. Maintenance의 조직/외부 task 연결과 Natural Search의 Atlassian form/error 공유도 남아 있다. 이를 분리할 때는 호출 순서·동일 connection·실패 의미를 다시 비교해야 한다.
- `persistence/db.py` 내부 bootstrap/migration 순서와 `app/storage/recovery.py`의 작업/HTTP 추가 분리는 아직 수행하지 않았다. 패키지 귀속 완료를 이 내부 정리의 완료로 표시하지 않는다.
- 기본 Session/resource import는 선택 기능 없이 통과했지만, 기능 하나를 제외한 전체 source ingestion/lifespan 조립은 검증하지 않았다. 기능 제거에는 해당 route/lifecycle 연결, templates/static, FK/data 보존 조치가 더 필요하다.
- 제품 기능의 유지/제거·품질 승인, 실제 외부 서비스 동작, 실제 모델 품질/성능, native window 검증이나 merge-safe 판단을 이 기록으로 대체하지 않는다. Drive 11개 검사는 사용자 지정 유예다.

## Next Action

- 패키지 재배치 배치는 완료했다. 다음 구조 작업은 새 flat 모듈을 추가하는 대신 현재 owner 안에서 진행한다.
- 트랙의 잔여 작업은 transaction을 보존하는 Atlassian/Maintenance 연결 분리, persistence 내부 책임 분리, 선택 기능 없는 전체 조립 검증이다. 실제 기능 삭제는 별도 제품 결정과 데이터 보존 범위를 필요로 한다.
- 임시 snapshot·build·synthetic runtime·검사 파일은 검증과 모든 소비 프로세스 종료 후 제거했다. 지속되는 사실과 검증 범위는 이 기록과 Architecture/활성 계획이 소유하며 임시 경로에 의존하지 않는다.
