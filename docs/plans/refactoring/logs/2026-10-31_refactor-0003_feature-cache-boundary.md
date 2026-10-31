# Optional Feature Cache Boundary And Re-Review

## Log Type

- Type: `Batch / Wrap-Up`
- Date: `2026-10-31`
- Related track: [REFACTOR-0003](../refactor-0003-session-centered-package-boundaries.md), Step 9/11.
- Scope: [completion review R1](2026-10-31_refactor-0003_completion-review.md#r1--common-cache-cleanup-reimports-omitted-auto-work)의 수정과 사용자 요청에 따른 subagent 재리뷰. Fullstack Product의 Settings 캐시 정리, 앱 시작/종료, CLI storage/scan 연결을 다룬다. 화면 디자인·운영 DB·설치 앱 변경은 없다.

## Summary

- Goal: 선택 기능을 앱 조립에서 제외했을 때, 그 기능의 이전 캐시가 남아 있어도 공통 실행·저장소 작업이 제외된 구현을 요구하지 않도록 한다.
- Outcome: `Pass` for this bounded boundary. Auto Work의 캐시 정책과 공통 파일 검사, 앱/CLI 연결을 분리했다. 기존 상태를 남긴 12개 제외 조립 경우에서 공통 Settings 정리와 시작/종료가 통과한다. Auto Work 제외 시 CLI 이관/정리도 해당 캐시를 해석·이동·삭제하지 않는다.
- R1: `closed`. 이전 리뷰의 실패 재현은 유효한 과거 근거로 유지한다. REFACTOR-0003 Step 9/11의 재개 항목을 닫고 구조 트랙을 완료한다. REFACTOR-0004/0005의 공용 자원·Session 참조 소유권 완료 판정은 유지한다.
- 이 구조는 하나의 앱·공유 DB를 사용하는 모듈형 모놀리스다. 패키지와 조립 등록을 함께 제거할 수 있는 경계이며, 누락 import를 자동으로 숨기거나 포함된 기능의 모든 내부 오류를 격리하는 장치는 아니다.

## What Changed

| 이전 소유/호출 | 현재 소유/호출 | 보존 또는 명시된 변화 |
| --- | --- | --- |
| `app/storage/layout.py`의 `_json`, `_tree`, `_unchanged`, `_inactive` | `foundation/files.py`의 `read_owned_json`, `owned_tree`, `ensure_tree_unchanged`, `tree_is_inactive` | 소유권·파일 종류·링크 수·크기·mtime/mode·열린 파일 판정의 본문을 유지한다. |
| 공통 layout의 simulation/preview 판별과 `maintain_derived_cache` | `auto_work/storage.py`의 `LEGACY_CACHE_OWNERS`, `maintain_cache` | 기능별 파일 형식·만료·writer lock·보존 규칙을 기능이 소유한다. |
| 앱 시작의 feature callback과 Settings의 무조건 feature 호출 | `app/application.py`가 포함된 Auto Work callback을 등록하고 lifecycle 및 Settings가 같은 callback을 사용 | 미포함 시 공통 검색 캐시만 처리하며 잔존 feature 파일은 읽지 않는다. |
| CLI storage의 무조건 feature 정책 호출 | `app/features.py`의 기본 기능 집합에 따라 owner/cleanup callback 전달 | 기본 CLI 결과는 유지한다. 미포함 시 feature 이관·정리를 실행하지 않고 `derived_cache` 결과도 제시하지 않는다. |
| CLI simulate 등록과 scan observer의 무조건 포함 | 같은 명시적 기능 집합을 따르는 명령 등록·관측기 연결 | Auto Work 제외 시 simulate 명령을 제공하지 않고 Atlassian 제외 시 scan이 그 관측기를 요구하지 않는다. |
| 명시적 개발 아카이브 이관 중 experiments 구현 import | layout이 기존 v1 디스크 marker와 허용 파일명을 직접 판별 | 과거 파일 형식은 이관 계약이며 실험 inference 구현의 존재와 분리한다. `--include-development` 조건을 유지한다. |

- `migrate_storage`의 내부 API는 `cache_owners`를, `clear_owned_cache`는 `maintain_feature_cache`를 명시적으로 받는다. 운영 소비자는 CLI와 Settings route이며 둘 다 포함된 기능을 전달한다. 기본 인자에서는 기능 상태를 다루지 않는다.
- Architecture, installation/storage, Settings recovery의 소유 문서를 갱신했다. 소스 참조가 달라져 stale 상태였던 schema cleanup ledger를 기존 generator로 재생성했다. schema, schema presentation, audit disposition은 변경하지 않았다.
- 신규/보강 검사는 제외된 캐시 보존, 개발 실험 import 차단, preview 만료와 원본 DB/lock 보존, feature 정리 실패 시 search 재시작, 공통 storage의 절대/상대 import 경계를 다룬다. 기존 behavior assertion은 유지했다.

## Behavior / Parity Notes

- Type: `Structural / Internal Interface`, supporting `Behavioral` correction for previously failing omitted-feature composition.
- Behavior-preserving intent: 기본 기능 집합의 route/응답 계약, cache owner/expiry/lock 검사, 알 수 없거나 사용 중인 파일 보존, 이관 순서·실패 및 검색 서비스 재시작을 유지한다.
- Intentional delta: 기능을 제외한 조립에서 남은 캐시 때문에 공통 Settings/CLI가 실패하던 경로가 성공한다. 제외된 feature 캐시는 그대로 보존하며, 포함되지 않은 작업을 수행했다고 보고하지 않는다. 사용자 설정/toggle이나 자동 plugin discovery를 추가하지 않는다.
- Baseline의 JSON/tree/activity 검사 4개, model owner 검사, cache retirement 총 6개 함수는 이름·import 경로·docstring만 정규화한 AST가 동일했다. 개발 아카이브의 v1 marker/허용 파일 집합도 baseline과 같다. `schema.sql`은 byte 동일하다.
- Default CLI differential: baseline/current 각각 합성 legacy simulation, preview, development archive를 준비해 migration dry-run/apply와 cleanup dry-run/apply를 실행했다. 네 결과의 JSON 집계와 잔존 파일 bytes hash/mtime/permission이 동일했다. 이관은 3개 directory, 만료 정리는 2개 result file이며 marker/lock과 원본 DB를 보존한다. 설치 wheel에서도 같은 기본 CLI 결과를 확인했다.
- Parity claim status: `Provisional` for the whole track. 위 비교는 해당 경로의 증거이며 모든 파일시스템 race, 외부 provider, 가능한 기능 조합에 대한 strict audit나 merge-safe 판정이 아니다.

## Validation

- Compare baseline: 동일 HEAD `6c03265701d0d8b552fc8bb60e346ba1971f4bb3` 위의 수정 전 작업 트리를 별도로 고정했다. 495개 source/tests/scripts/build 파일의 path→SHA-256 manifest digest는 `a2df266bd8ba286c0ef7b63d75ab71a0d41a683fde7921722bf914223dbaf188`이다.
- Final checkpoint: 같은 파일 집합에 신규 모듈 2개를 포함한 497개 manifest digest는 `0e044cafe4824e5972b26181d4f7bb56a411f11ccca56671bf1a904786db7432`다. digest는 path 정렬·compact JSON으로 계산했다. 이번 배치의 source/test 변경은 14개 파일이며 root Python 파일은 진입점 4개다.
- Focused: `test_feature_assembly`, `test_installation_and_storage`, `test_desktop_settings`, `test_auto_work`, `test_foundation_models` 최초 91개 통과. 이후 CLI 연결 보강 후 assembly 4개, 최종 import guard 보강 후 foundation 14개를 다시 통과했다. 이 수치는 전체 suite에 더하지 않는다.
- Full regression: 격리된 `.venv/bin/python` unittest discover에서 1,489개를 찾았다. 사용자가 보류한 `test_google_drive_transport.PoolTests.*` 정확히 11개만 제외해 1,478개 실행했다. 최초 1,477개 pass, generated schema ledger 최신성 1개 fail, error/skip 0이었다. ledger 재생성 뒤 해당 모듈 6개와 generator check가 모두 통과했다. 최종 source 변경은 없고 마지막 정적 검사 보강은 위 foundation 14개로 확인했다.
- Omission runtime: Atlassian, Workstreams, Workflow, Auto Work, Context Search를 각각 또는 전부 제외한 web/desktop 12개 subprocess. 제외 구현 import를 차단하고 과거 simulation/preview를 data/cache 양쪽에 준비했다. 기존 수집·Session/Context/Usage/검색·lifecycle 검사에 실제 ASGI Settings cache-clear, 사용 후 keyword 요청, CLI help/status/migrate/cleanup dry/apply, Atlassian 없는 scan을 추가했다. Auto Work 제외 시 old files의 bytes/mtime/mode가 동일했다. malformed preview도 해석하지 않는다. DB integrity/FK 검사도 유지했다.
- Wheel: 기존 캐시의 Hatchling으로 offline wheel build 후 별도 target에 `uv pip install --offline --no-deps --target` 설치했다. 설치된 경로의 모듈을 사용함을 확인하고 양 edition에서 다섯 기능 전체 제외 probe 및 기본 CLI 비교를 통과했다.
- Frozen: `.venv/bin/python -m PyInstaller desktop/backend.spec`로 실제 backend를 다시 빌드했다. 합성 DB/설정/잔존 캐시로 기본 desktop 구성을 시작해 health/Session/Context/Settings/keyword HTTP 200, Settings 캐시 정리(61,440 bytes), graceful shutdown exit 0을 확인했다. 같은 runtime으로 재시작해 동일 endpoint와 추가 정리 0 bytes, graceful shutdown exit 0을 확인했다. simulation의 만료 result는 제거되고 marker/lock은 남았다.
- Browser: 다섯 기능을 모두 차단한 source web 앱을 별도 loopback 포트에서 실행했다. Chrome의 Settings → 저장공간 → 캐시 정리 버튼으로 성공 메시지를 확인했고 이후 keyword HTTP 200을 확인했다. 종료 후 검색 캐시 제거, feature 캐시 bytes/mtime/mode 보존, 제외 모듈 미로딩을 재확인했다. JS exception은 없고 기존 form id/name 접근성 issue 1건이 관찰됐다. UI 마크업은 변경하지 않았다.
- Fixture/environment corrections: wheel desktop smoke의 첫 실행은 probe와 token이 달라 401이었다. 테스트 token을 맞춘 재실행이 통과했다. source/frozen loopback은 sandbox의 bind 제한 이후 승인된 로컬 실행으로 검증했다. 이들은 제품 수정으로 해결한 실패가 아니다.
- Generated/document gates: data-model docs(ordinary 52 + FTS5 1, FK 66, indexes 51, owners 11), value registry/dictionaries, schema presentation, cleanup audit(755 objects; keep 643/defer 112) 검사와 `git diff --check`를 통과했다. 수정한 owner/plan/log 6개 문서의 local link 246개가 연결된다. Repository privacy 검사도 1,805 candidate files 기준으로 통과했다.
- Cleanup: 검증 서버·backend·browser page를 종료하고 열린 파일이 없음을 확인한 뒤 task 소유 baseline/manifest, build/wheel, 합성 runtime, 로그와 작성 scratch를 모두 제거했다. 추가로 생성된 임시 status 파일도 제거했다. 이 기록은 임시 경로에 의존하지 않는다.

## Subagent Re-Review

- `evidence_scout` — package boundary: 앱/Settings/CLI 호출과 import 경로를 조사했다. R1의 무조건 Auto Work import가 제거됨을 확인했고, 명시적 development migration의 experiments 의존을 추가 발견했다. Primary가 역사적 디스크 계약으로 분리한 후 재조사에서 그 import 경로도 없어졌음을 확인했다.
- `evidence_scout` — cache/persistence evidence: baseline/current의 owner, mtime/mode, inactivity, lock, expiry, unknown-file/refusal, 이동/삭제 순서를 대조해 구체적인 의도 밖 조건 변화를 찾지 못했다. 처음 지적한 기본 CLI integration evidence 부족은 primary의 baseline/current 및 wheel 실험으로 보완했다. 세 기존 테스트 파일의 assertion 비교에서도 삭제/약화를 찾지 못했다.
- `bounded_verifier` — 지정된 전체 suite와 generated checks를 실행하고 stale ledger 1건을 보고했다. Primary가 재생성한 뒤 관련 6개 검사를 다시 통과했다.
- Primary decision: 캐시 책임과 조립의 R1 exit gate를 충족한다. subagent 결과는 위 한정된 근거로 사용했고, 요구 해석·설계·문서 소유·최종 완료 판정은 primary가 수행했다.

## Risks / Limitations

- 포함 여부는 코드의 명시적 조립 경계다. 패키지를 제거할 때 해당 등록/adapter와 assets/tests도 함께 정리한다. 아직 등록된 필수 구현이 임의로 사라진 경우를 자동 우회하지 않는다.
- 다섯 선택 기능의 단독/전체 제외가 검증 범위다. Google Drive 강제 제거, 모든 기능 조합, 포함된 기능의 모든 오류에 대한 장애 격리는 입증하지 않는다. Google Drive transport 11개 보류는 유지한다.
- DB schema/history와 기능 데이터는 보존한다. 기능 코드 제외가 테이블 제거·데이터 폐기를 뜻하지 않는다. 이번 배치에는 운영 DB migration·현재 서버 재시작·native Tauri/WKWebView 교체·provider/model/원격 redirect 실행이 없다.
- 최종 전체 strict parity 및 병합 판단은 별도이며 현재 미커밋 작업 트리의 기존 변경을 포함한 clean merge 판정은 하지 않는다.

## Next Action

이번 구조 트랙의 구현 잔여는 없다. 새로운 기능이 공통 시작/종료·Settings·CLI에
기여할 때 해당 기능의 소유 처리기를 조립하고, 기존 상태를 남긴 제외 검사를
함께 유지한다. 실제 기능/테이블 제거는 해당 데이터 수명과 마이그레이션을 포함한
별도 명시적 변경으로 다룬다.

## Follow-Up — Session Closeout

- Authorization / scope: 사용자가 세션 시작부터 종료까지의 변경·논의·판단·검증을 기존 소유 문서에 통합하고, 독립적인 두 문서 리뷰 후 세션 변경만 커밋·푸시하도록 요청했다. 별도 세션 로그는 만들지 않았다. 아래는 앞선 캐시 배치와 구별되는 종료 검증이다.
- Consolidated ownership: [REFACTOR-0003](../refactor-0003-session-centered-package-boundaries.md)는 패키지·계층·앱 조립과 완료/한계를, [REFACTOR-0004](../refactor-0004-direct-session-materials.md)는 연결된 작업·간접 자료 표시 제거를, [REFACTOR-0005](../refactor-0005-shared-resource-ownership.md)는 공용 identity/매핑과 운영 DB 이행을 소유한다. 동작 보존을 목표로 한 구조 변경과 사용자가 승인한 의미 변경을 합쳐서 parity 보존으로 표시하지 않는다. 현행 책임은 Architecture·Product·주제별 Data Model·storage/recovery/Task Runner 정책과 Session 앱 가이드에 남긴다.
- Independent review: 두 subagent가 각각 `docs-structuring`의 incremental 방식과 `docs-shaping`의 reshape 방식으로 세 계획과 10개 실행 기록 전체, 해당 현행 owner 구간 및 결정적인 코드를 읽었다. 관련 Privacy 계약까지 범위를 넓혔다. 지적을 반영한 구간의 재검토에서 두 reviewer 모두 추가 수정이 필요한 항목을 발견하지 못했다. 과거 runtime의 근거는 실행 기록이며 두 reviewer가 이를 재실행한 것은 아니다. 전체 저장소의 모든 역사 문서·생성 행을 의미 검토했다고 주장하지 않는다.
- Applied corrections: Session 자료의 조직 관계 소비와 삭제된 Item resolver 설명을 바로잡았다. Context ingestion, 검색 HTTP/lifecycle, 공용 자원 identity/CRUD, 기능별 Run/Suggestion, Insights ranking의 소유 위치를 정정했다. Context Root 비활성화와 실제 Document 삭제, 원문 파일 소실과 소유 Session 삭제, scan의 identity 이행 건수/오류 조건을 구분했다. Privacy의 허용 FK를 공용 자원으로 맞추면서 금지 payload와 URL query 예외를 보존했다. 외부 본문과 Atlassian remote-state의 소유 링크를 나눴다. 여섯 신규 자원 catalog는 본문·열 표를 byte 그대로 기존 Catalog 안으로 옮겼다. 이전 인계·위험 문단에는 당시 상태임을 바로 앞에 표시했다. 선택적 새 문서 트리나 문서 전체 재작성은 하지 않았다.
- URL basis: 최초 파서 작성 당시 공식 자료를 읽었는지는 남은 기록만으로 확정하지 않는다. 이번 종료 검토에서 공개 Atlassian 자료를 확인해 [Architecture의 URL 설명](../../../policies/project/architecture.md#package-ownership)에 Jira issue 경로, Cloud page-ID 경로와 제목 없는 예시, Data Center page-ID 형태의 출처를 추가했다. 제목 없는 Cloud 경로 자체를 레거시나 redirect의 증거로 분류하지 않는다. 실제 사용자가 언급한 원격 주소의 존재·접근·redirect 및 다른 도메인 간 동일성은 검증하지 않았다.
- Code review: 세션의 앞선 단계별 코드 리뷰·비교 근거에 더해 공용 resource/binding, Session evidence의 FK·삭제 조건, shared-resource backup/savepoint/backfill/count/payload 이행, ingestion observer transaction 경계, feature callback 및 UI 직접 자료 경로를 재대조했다. 새 차단 결함은 발견하지 않았다. 종료 보완은 문서, 생성 presentation/audit provenance 및 Python 파일 4개의 EOF 빈 줄 정리에 한정되며 Python 실행 동작·DDL·dependency·template/asset은 바꾸지 않았다. EOF 정리는 새 파일까지 스테이징한 뒤 공백 검사에서 발견한 항목으로, 각 파일 끝의 빈 줄만 제거했음을 byte 비교했다.
- Final regression: generated metadata와 EOF 정리 후 격리된 Python 3.11 환경에서 **1,489개 발견, 합의된 Drive PoolTests 11개만 제외, 1,478개 실행·통과, failure/error/skip 0**, 43.226초. 검사 전후 497개 source/tests/scripts/build 파일 manifest가 `8bb857789a1d4e9c724df525690eb10533dc24681c3b183cd0a69e0fa9ad1b11`로 동일했다. EOF 정리 전에도 1,478개가 통과했다. 앞선 1건 ledger 실패와 재검사 기록은 그 배치의 이력으로 보존하며 현재 실패로 남기지 않는다.
- Generated and documentation checks: data-model docs, schema presentation, value registry/11 dictionaries 및 schema cleanup audit가 최신 상태다. Audit는 manifest 지문만 갱신했고 755개 객체의 keep 643/defer 112 결정을 유지했다. Data Model Mermaid 12개를 로컬 bundle로 parse했다. 변경된 Markdown 문서 52개의 로컬 링크 1,244개에서 누락된 파일·anchor가 없었고, 앱 가이드의 절대 route 4개는 파일 링크와 구분했다. 공백 검사와 publication privacy 검사도 통과했다.
- Runtime evidence reuse: 마지막 캐시 배치의 source/wheel/frozen/browser 결과를 유지한다. 그 뒤 Python 실행 동작·schema·template/asset은 바꾸지 않았고, 위 EOF 정리 후 전체 테스트를 다시 실행했다. 종료 때 문서 설명을 반영한 schema presentation JSON은 별도로 생성·검증했다. native Tauri/WKWebView 설치나 외부 provider/model 호출을 새로 실행하지 않았다. 이미 수행한 운영 DB migration과 서버 재시작은 REFACTOR-0005의 후속 운영 적용 기록에 남으며, 이번 closeout에서는 반복하지 않았다.
- Remaining / deferred: Google Drive 전송 11개, 전체 strict parity 판정, 모든 기능 조합, native 설치 전환, 실제 파일럿/테이블 제거와 그 데이터 수명 조치, 원격 redirect·cross-domain alias 확인은 완료로 표시하지 않는다. Slack 분류·임의 Markdown 자동 색인·DB 분할은 이번 구현 범위가 아니며 신규 요구로 확정하지 않았다. 이 종료 시점에는 기존 Starlette TemplateResponse deprecation과 앞선 browser form id/name issue를 남겼다. Starlette 경고는 아래 후속 수정에서 해소했고, Google Drive 입력칸 관련 보완은 사용자의 후속 지시에 따라 보류했다.
- Recovery and temporary state: 운영 migration 복구 사본 `<database>-pre-shared-resources-v1.bak`는 기존 보관 정책을 따르는 복구 자료로 유지했다. 이번 종료 검증의 임시 기준선·검사 로그·작성 초안은 검증과 리뷰 종료 후 해당 경로를 사용하는 열린 파일이 발견되지 않은 상태에서 정리했다. 필수 결과는 위 기록에 남겼으며 보관 중인 session 임시 경로는 없다.
- Publication boundary: 현재 저장소의 세션 변경과 이 종료 보완만 포함한다. 변경 시작 기준은 `6c03265701d0d8b552fc8bb60e346ba1971f4bb3`이며 원격 `origin/master`도 같은 커밋임을 읽기 전용 확인했다. 공개 저장소임을 확인했고 개인 runtime·자료·임시 검증 파일은 게시 대상이 아니다. 실제 commit ID와 push postcondition은 Git 기록과 종료 응답으로 확인한다.

## Follow-Up — TemplateResponse API

- Request / baseline: 사용자는 Google Drive 입력칸 보완은 보류하고, Starlette의 예전 화면 응답 호출 방식을 수정하도록 지시했다. 기준은 종료 커밋 `6c5a6e43fdcdfb49686c46d1c842195138873aa4`다.
- Compatibility basis: 설치된 FastAPI 0.128.8 / Starlette 0.49.3 / Jinja2 3.1.6과 [Starlette 0.49.3 구현](https://github.com/encode/starlette/blob/0.49.3/starlette/templating.py), [FastAPI의 template 안내](https://fastapi.tiangolo.com/advanced/templates/)를 대조했다. `TemplateResponse(request, name, context, ...)`로 호출하며 dependency/lock 버전은 바꾸지 않았다.
- Change: 16개 화면 처리 모듈의 예전 호출 41곳과 테스트의 직접 호출 2곳을 갱신하고, 기존 테스트의 모의 응답 함수 1곳에 Request 인자를 추가했다. 이미 새 방식을 쓰던 Docs/Context Search는 유지했다. 별도 wrapper나 경고 숨김 처리는 추가하지 않았다. Google Drive 코드와 입력칸은 수정하지 않았다.
- Preservation review: 변경 전후 Python AST를 대조해 43개 직접 호출에는 첫 Request 인자만 추가했음을 확인했다. template 이름, context 표현식, 응답 상태와 header는 그대로다. 전체 source/tests의 TemplateResponse 호출에서 예전 형태가 남아 있지 않음을 확인했다. DB·색인된 원문·HTML/CSS/JavaScript·기능 조립은 변경하지 않았다.
- Regression: `starlette.templating`의 `DeprecationWarning`을 오류로 처리하는 filter와 자식 프로세스용 `PYTHONWARNINGS=error::DeprecationWarning:starlette.templating`을 적용했다. 격리된 Python 3.11 환경에서 1,489개를 발견하고 기존 보류 대상 Drive `PoolTests` 11개만 제외한 **1,478개가 통과**했다(failure/error/skip 0, 45.579초). 검사 전후 497개 source/tests/scripts/build 파일 지문은 `be064bc704b2d145e5dbe4c575d496aa72b192243c18f250e59d0368aaf1ad8f`로 동일했다.
- Browser: 정상 lifespan을 실행하는 synthetic 로컬 서버와 격리된 Chrome에서 Settings 화면을 열고, `/settings`, `/sessions`, `/context`, `/schema`, `/natural-search?mode=keyword`의 HTML 응답 200과 제목을 확인했다. Settings 가로 넘침과 브라우저 error/warn은 없었고, 기존 form id/name issue 1건은 유지됐다. 이 서버도 같은 Starlette 경고를 오류로 처리했다. 최초 검증 서버는 lifespan을 꺼 검색 서비스 초기화가 빠져 500이 났으며, 제품 코드 변경 없이 검증 서버의 정상 초기화를 복원한 후 위 결과를 확인했다.
- Scope limits: 운영 DB나 설치된 native 앱을 교체하지 않았다. 이전 구조 트랙의 전체 strict parity·Drive 전송·외부 호출 검증 한계를 이 API 수정으로 해소했다고 주장하지 않는다.
