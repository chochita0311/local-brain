# Feature-Owned Execution And Explicit Application Assembly

## Log Type

- Type: `Batch / Wrap-Up`
- Date: `2026-10-31`
- Related track: [REFACTOR-0003](../refactor-0003-session-centered-package-boundaries.md), Step 5/8/9/11.
- Scope: 사용자 `진행` 지시에 따른 검색 HTTP의 Atlassian 역의존, Maintenance의 기능별 실행 책임, 선택 기능의 앱 조립 분리. Structural / Internal Interface이며 Fullstack Product의 검색·앱 shell·Run/Atlassian 전달 surface를 검증한다.

## Summary

- Goal: 세션 중심 앱의 기본 수집·조회가 파일럿 구현을 요구하지 않도록 하면서 기본 앱의 동작과 실행 이력을 보존한다.
- Outcome: `Pass` for this structural batch and REFACTOR-0003's scoped exit gates. 전체 strict behavioral parity는 `Provisional`이며 병합 판정은 수행하지 않았다.
- 일반 검색은 공용 HTTP 폼 코드를 사용한다. Workstream/Atlassian 작업 실행은 각 기능이 소유하고 공통 Run 상태·취소·중단 복구만 `maintenance/`에 남는다. 앱은 포함된 기능의 route와 시작/종료 처리를 명시적으로 연결한다.
- 작업 복구를 앱 시작에서 호출하던 이유는 이전 프로세스 종료 후 남은 실행 상태를 정리하기 위해서다. 세션 자체의 필수 시작 절차가 아니다. 기존 코드에서 이 복구는 개발 웹에만 있었고 desktop에는 없었다. 해당 edition 조건과 호출 순서를 보존하며 Run 생산 기능이 없는 조립에서는 호출하지 않는다.

## What Changed

| 이전 책임/호출 경로 | 현재 소유자와 연결 |
| --- | --- |
| `natural_search/web.py` → `atlassian/web.py`의 폼 parser/오류 | `app/forms.py`의 bounded URL-encoded form parser/`FormError`; 검색 HTTP는 직접 사용, Atlassian HTTP는 기존 domain 오류로 번역 |
| `maintenance/service.py`의 작업 정의·manifest·preview·Run 준비·목록 | `workstreams/runner.py`; Workstream HTTP가 자기 실행기를 호출 |
| 같은 파일의 Workstream CLI stream/구조화 결과·Suggestion 적용 | `workstreams/runner.py`; 상태·process 추적·terminal write는 공통 runtime에 위임 |
| 같은 파일의 Atlassian 외부 실행·evidence·projection | `atlassian/runner.py`; 기존 외부 read 승인과 projection/terminal update transaction 유지 |
| 같은 파일의 공통 stream helper | `maintenance/streams.py`; structured result 추출과 stderr 소비 |
| Run 조회/출력·task/process 추적·취소·종료·중단 복구 | `maintenance/service.py`; 기능이 선택해 전달한 coroutine을 추적하고 기능 구현을 import하지 않음 |
| `maintenance/web.py`의 Workstream 작업 생성 모델/handler | `workstreams/web.py`; 공통 Run 상세/status/cancel은 `maintenance/web.py` 유지 |
| Atlassian HTTP의 Workstream membership 변경 import | `app/reference_integrations.py`에서 설치한 명시적 add/remove callback; 두 기능이 포함될 때 연결 |
| `app/routes.py`의 선택 기능 import/등록 | 지정된 feature 집합에 따른 명시적 import/route 등록; 기본 집합의 순서 유지 |
| `app/lifecycle.py`의 직접 구현 import | `app/application.py`가 Run runtime, Auto Work preview cache 관리, Context Search factory를 설치; lifecycle은 해당 기여를 호출 |
| navigation과 Atlassian 조직 연결 control | `app/templating.py`의 request별 package 유무와 template 조건; 기존 Auto Work capability guard와 함께 적용 |

- Added: 내부 `create_app(feature_packages=...)` 조립 인자와 의미 있는 form/실행/제외 조립 검사. 허용 feature 이름을 명시하고 잘못된 이름은 거절한다. 기본 entrypoint의 feature 집합은 그대로다.
- Updated: 호출자·테스트 patch target·architecture/runner 문서·값 registry와 생성 사전·schema cleanup audit의 소스 참조. cleanup disposition은 keep 643/defer 112, 총 755 objects를 유지한다.
- Removed: 일반 검색의 Atlassian import, 공통 Run runtime의 Workstream/Atlassian 구현 import, 기능 없는 조립에 대한 강제 route/lifecycle import. ImportError 무시, 제품 toggle, plugin registry, 광범위한 호환 facade는 추가하지 않았다.

## Behavior / Parity Notes

- 기본 web/desktop의 입력·응답·route 순서, startup/shutdown 순서, schema와 기존 실행 이력 의미를 유지하는 구조 변경이다. 실제 기능 제거와 데이터 재설계는 범위 밖이다.
- 폼은 기존 UTF-8, media type 처리, 최대 160 KiB와 128 fields의 inclusive 한도, 빈 값 보존과 scalar의 마지막 값 선택을 유지한다. Atlassian의 `item_id`/`topic_id`만 list로 받는 정책은 Atlassian adapter가 지정한다. 공용 내부 오류 타입은 달라졌지만 각 HTTP 오류 메시지/status와 Atlassian 오류 code/type은 유지했다.
- 공통 `start_run(run_id, execution)`은 전달받은 coroutine을 `asyncio.Task`로 추적한다. Workstream/Atlassian 공개 실행 함수가 자신의 coroutine을 선택한다. 기존 process cleanup·cancel·failed/interrupted terminal 처리와 native Session 동기화 순서를 유지한다.
- 시작 복구의 대상은 `status IN ('queued', 'running', 'cancelling') AND task_type IS NOT NULL AND stream_path IS NOT NULL`인 Run이다. 같은 transaction에서 `interrupted`, `pid=NULL`, 완료/갱신 시각, 기존 오류 문구를 기록한 뒤 해당 runner의 native Session을 동기화한다. 작업을 다시 실행하지 않는다. 개발 웹에서만 호출하고 desktop의 기존 미호출 조건을 유지한다.
- Workstream 결과의 pending Suggestion 생성/이전 pending 처리와 실패 시 rollback, Atlassian evidence/projection과 terminal Run의 원자성, 외부 read 승인 조건을 보존한다. common runtime에 SQL transaction을 재조립하거나 새 retry 정책을 넣지 않았다.
- `maintenance.service.get_run`의 기존 Workstream 이름 표시용 LEFT JOIN과 FK/schema는 유지했다. 선택 구현을 import하지 않는 것은 관련 table 삭제가 가능하다는 뜻이 아니다. 실제 삭제 시 보존할 실행 이력과 join/FK 이행을 별도로 결정한다.
- legacy `/search`는 Atlassian 자료를 합치는 별도 경로여서 Atlassian이 포함될 때만 등록된다. 일반 keyword/AI `/natural-search`는 core에 남는다. 미탑재 fixture에서 관련 route/nav/control이 없는 것은 명시적 조립 결과이며 기본 앱의 노출 변경이 아니다.
- Intentional deltas: 내부 module/import 위치, 공통 실행기의 coroutine 인자, 중립 form 오류와 명시적 feature 조립 인자. 제품 설정·기본 동작·DDL·외부 실행 권한의 의도적 변경은 없다.
- Parity claim status: 검사한 기본 실행 흐름의 보존 근거를 확보했지만 전체 트랙은 `Provisional`. 모든 실사용 중단 지점·원격 제공자·native 사용자 경로를 포괄한 strict audit는 아니다.

## Validation

- Baseline: HEAD `6c03265701d0d8b552fc8bb60e346ba1971f4bb3` 위 Step 10 이후의 미커밋 작업 트리. src/tests/scripts 및 pyproject/lock 488개 파일의 path→SHA-256 manifest digest는 `c4efd0167969ac2b3212f40159d0c835d32672d4797f6c48232075dce79ae12f`다. 기존 작업을 immutable 비교본으로 보존했고 HEAD diff 전체를 이 배치로 간주하지 않았다.
- Final source checkpoint: 같은 범위 495개 파일의 manifest digest `a2df266bd8ba286c0ef7b63d75ab71a0d41a683fde7921722bf914223dbaf188`. 두 digest는 경로순 mapping을 `json.dumps(..., sort_keys=True, separators=(',', ':'))`로 직렬화한 SHA-256이다. 이번 source/test/registry 변경은 25개 파일이며 docs/generated 변경은 별도다. 커밋된 checkpoint는 아니다.
- Source comparison: 이동한 함수 39개에서 common runtime qualification과 기존 `_execute_run`의 feature branch 분리만 정규화하면 AST가 일치한다. 이 범위의 SQL·분기·write·오류·결과·transaction 본문이 일치하며 `schema.sql` bytes도 동일하다. 내부 `start_run` 인터페이스와 앱 조립은 별도 동작 검사로 확인했다.
- Focused: form/runner/Atlassian/external sync 등 70개, 이어 추가 실행·조립·Auto Work·schema audit 관련 32개 통과. Workstream fake CLI의 실제 coroutine 실행은 완료 결과·pending Suggestion을 확인하고, 적용 중 실패는 queue rollback·failed terminal·task/process cleanup을 확인한다.
- Full suite: `.venv/bin/python`에서 `unittest.defaultTestLoader.discover('tests')` 결과를 실행했다. 사용자 보류 대상 `test_google_drive_transport.PoolTests.*`가 정확히 11개인지 확인해 제외한 **1,473개 통과**, failure/error/skip 0. 실행 환경은 private synthetic runtime과 offline model 설정을 사용했다.
- 새 조립 검사: `test_feature_assembly`는 Atlassian, Workstreams, Workflow, Auto Work, Context Search를 각각 제외하고 전부 제외하는 6가지 경우를 web/desktop에서 실행한다(**12개 subprocess subcase**). `feature_assembly_probe.py`는 제외된 구현의 import를 실제로 차단하고 lifespan, 명시적 Codex source 등록·수집, Local Context 등록·수집, Session URL evidence, Usage/keyword 및 기본 요청, 준비/취소 오류, 숨겨진 navigation, 중단 복구의 대상 조건과 desktop 미호출, DB integrity/FK를 검증한다.
- 초기 검사에서 기존 Auto Work capability guard를 package 유무로 덮어쓴 문제와 이동 전 audit 소스 참조를 발견했다. capability와 package 조건을 분리하고 ledger를 재생성한 뒤 위 full suite를 통과했다. 조립 fixture의 누락 source 등록과 desktop OpenAPI 기대값도 실제 기존 계약에 맞춰 수정했으며 제품 계약을 완화하지 않았다.
- 최종 privacy 검사에서는 새 synthetic fixture의 Atlassian 호스트 표기가 금지 URL 패턴에 걸렸다. 같은 Confluence 경로 인식 계약을 검사하는 예약 도메인 `example.test`로 바꾸고 전체 suite와 privacy 검사를 다시 실행했다. 실제 사용자 데이터는 fixture에 사용하지 않았다.
- Default runtime comparison: baseline/current 각각 독립 synthetic runtime에서 실제 lifespan 시작·종료를 실행했다. web/desktop 각각 ordered HTTP route **113개**(static mount 포함 114개), **16개 HTTP 응답**의 status/header/body를 비교했다. health·Sessions·Context·Usage·keyword/AI·Settings/storage·OpenAPI·Workstream·Atlassian·missing Run·잘못된 form 경로가 일치했다. runtime path, static asset mtime query, 가용 디스크 공간만 정규화하고 content-length는 경로 정규화 때문에 제외했다.
- Wheel: 기존 로컬 build dependency cache로 wheel을 만들고 설치 layout에서 source checkout을 import 경로에서 제외했다. 모든 Python/package resource bytes가 최종 source와 같고 실제 lifespan 및 위 16개 요청을 검증했다. storage 응답의 `data_bytes`는 실행 중 SQLite 공유 메모리 파일 때문에 baseline보다 32,768 bytes 컸다. 종료 후 파일 목록·크기, DB 184 pages/0 freelist와 integrity가 일치함을 확인하고 wheel 비교에서는 이 한 필드만 추가 제외했다. 그 외 route/status/header/body 비교는 통과했다.
- Frozen backend: `.venv/bin/python -m PyInstaller desktop/backend.spec --noconfirm`을 별도 build/cache/dist 경로로 실행해 실제 배포용 Python backend를 빌드했다. synthetic runtime에서 최초 실행과 기존 상태를 유지한 재실행 각각 7개 요청을 통과했고 settings bytes 보존, token 진입과 `/desktop/shutdown`, process exit 0을 확인했다. source 서버의 성공을 frozen 검증으로 대신하지 않았다.
- Browser: source 서버에서 검색 입력 후 Enter·query/result 경로, 비활성 AI GET, 잘못된 검색 POST의 422, Atlassian 미지원 URL의 inline 오류와 입력 보존을 확인했다. 실제 frozen backend에서도 token/cookie 진입, Session 목록, Session/Document keyword 결과, desktop의 파일럿 navigation 부재를 확인했다. 두 화면에서 가로 overflow가 없었다. Chrome DevTools 자동화와 오류 응답 fetch probe를 사용했으며 native WKWebView나 물리 입력을 검사한 것은 아니다.
- Docs/generated: `check-data-model-docs.py`, `build-data-model-value-dictionaries.py check`, `build-schema-presentation.py check`, `check-schema-cleanup-audit.py --check`, 변경된 Python 파일 22개의 Python 3.9 AST 검사, owner 문서 링크 검사, `git diff --check` 및 신규 파일을 포함한 whitespace 검사를 통과했다. `check-repo-privacy.sh`도 1,801 candidate files에서 통과했다. schema presentation manifest digest는 `6f0fbea1fabeb9e03fe580baf2c1a4f9652789423e174a261808467f186eea1a`로 유지한다.

## Risks / Limitations

- Google Drive의 위 11개 전송 검사는 사용자의 보류 지시대로 실행하지 않았다. 다른 Drive 검사는 full suite에 포함했으며 구현·오류 처리를 축소하지 않았다.
- 미탑재 조립은 기존 schema를 유지한 synthetic fixture다. 모든 feature 조합, feature table 삭제, 구버전 앱과 새 DB의 조합을 증명하지 않는다. 운영 DB 변경·실제 서버 재시작·기능 활성화·커밋·배포는 하지 않았다.
- wheel/frozen Python backend를 검증했지만 Tauri 앱 전체 재빌드·설치, native WKWebView, 실제 원격 제공자/AI 모델 실행·품질·성능은 검증하지 않았다. 기존 설치된 앱에 이번 코드가 적용됐다는 주장이 아니다.
- temporary baseline·DB·wheel·frozen build·검증 로그는 작업 소유 임시 자료로 모두 제거했다. 전용 서버와 browser page를 종료하고 열린 파일이 없음을 확인한 뒤 정리했다. 남는 기록은 이 synthetic 조건·결과와 추적 가능한 소스/테스트이며 durable 문서는 임시 경로에 의존하지 않는다.

## Next Action

REFACTOR-0003의 구조·조립 범위를 완료로 닫는다. 실제 기능의 유지/교체/제거는
패키지, 지정 route/lifecycle/observer, 자산·테스트, 보존할 데이터와 migration 소유자를
함께 선택하는 후속 제품 결정이다. 기존 Run 이력 schema와 설치된 앱의 rollout은
이번 완료와 구별한다. 이번 코드 이동 때문에 운영 DB를 다시 마이그레이션할 필요는 없다.
