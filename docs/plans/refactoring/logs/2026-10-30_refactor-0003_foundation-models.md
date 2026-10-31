# REFACTOR-0003: Foundation And Model Runtime Batch

## Log Type

- Type: `Batch`
- Date: `2026-10-30`
- Related track: [Session-Centered Package Boundaries](../refactor-0003-session-centered-package-boundaries.md)
- Scope: approved Steps 1–3 — baseline capture, shared foundation extraction and model runtime separation.

## Summary

- Goal: 세션·검색의 공용 기반을 Workstreams와 실험 코드에서 분리하여 이후 기능별 구조 정리의 선행 조건을 만든다.
- Outcome: `Pass` for implementation and bounded batch validation; overall strict parity remains `Provisional`.
- 사용자 “진행”을 권장 첫 배치 Step 1–3의 실행 승인으로 적용했다. Step 4–11, 기능 제거, 설치된 앱 교체, 커밋·공개 배포는 수행하지 않았다.
- 후속 지시로 Google Drive 연동도 보류 영역에 포함했다. 로컬 HTTP 서버가 필요한 전송 테스트 11개는 이 배치의 필수 gate에서 제외하며, Drive 개발 재개 시 다시 검증한다. 기존 승인·구현 사실이나 보존할 데이터의 의미를 바꾸지 않는다.
- 최상위 Python 파일은 `__init__.py` 포함 100개에서 89개로 줄었다. 전체 Python 모듈은 새 package initializer와 추출 모듈을 포함해 142개에서 150개가 됐다. 파일 개수보다 실제 의존 방향과 소유권을 기준으로 나눴다.

## What Changed

### Moved/Renamed

경로는 `src/localbrain/` 기준이다. 아래 11개 모듈을 이동하고 실제 consumers, scripts와 test patch/import를 갱신했다.

| Baseline owner | Current owner |
| --- | --- |
| `config.py` | `foundation/config.py` |
| `preferences.py` | `foundation/preferences.py` |
| `local_operations.py` | `foundation/operations.py` |
| `path_display.py` | `foundation/paths.py` |
| `model_cache.py` | `models/cache.py` |
| `model_catalog.py` | `models/catalog.py` |
| `model_installation.py` | `models/installation.py` |
| `model_setup.py` | `models/setup.py` |
| `session_simulation_model.py` | `models/embedding.py` |
| `work_context_model.py` | `models/generation.py` |
| `work_context_choices.py` | `models/choices.py` |

선택지 decoder는 `LocalGenerator.choose`가 직접 사용하므로 모델 기반에 포함했다. 선택지 문법을 제약하는 기능이며 실험의 의미·품질 판정을 옮기거나 승인한 것이 아니다.

### Added / Extracted

| Baseline logical units | Current owner |
| --- | --- |
| `workstreams.utc_now`; `session_simulation.now`; `work_reconstruction.timestamp` | `foundation/clock.py` |
| `work_reconstruction.ExperimentError`, `require` | `foundation/validation.py` |
| `work_reconstruction.digest`, `key`; `session_simulation.sha` | `foundation/fingerprints.py` |
| `session_simulation._safe_file`, `read_json`, `atomic_json` | `foundation/private_json.py` |
| `runtime_storage.StorageError`, `validate_runtime_directory`, `private_directory`, `private_database`, `inactive_files` | `foundation/files.py` |
| `runner.runner_executable` | `foundation/agent_cli.py` |
| `model_cache.hub_cache_root` | `foundation/paths.py` |

18개 기존 정의를 추출했다. `paths.package_boundary`는 모듈 깊이 변경 후에도 기존 package-parent의 저장 거부 범위를 유지하는 계산을 소유한다. `runtime_storage.py`에는 migration backup retirement와 storage accounting을 남겼다. Foundation은 DB·기능·모델 실행·FastAPI를 import하지 않으며, models의 LocalBrain 의존은 foundation과 models 내부로 한정한다.

두 package initializer는 docstring만 갖는다. 전체 모듈을 다시 export하는 facade나 모든 옛 경로의 compatibility shim은 만들지 않았다. 부분 추출의 원래 소비 모듈은 자신이 계속 사용하는 공유 함수를 새 소유자에서 import한다.

### Updated

| Flow | Current wiring and preserved boundary |
| --- | --- |
| Web/CLI → settings/preferences/locks | `foundation`으로 import를 바꿨다. 설정 값·revision·잠금/오류 처리의 기존 구현을 유지한다. |
| Session pins / chart settings → UTC helper | `workstreams` 없이 `foundation.clock`을 사용한다. 기존 query/write는 그대로다. |
| DB initialization / storage recovery → file safety | `foundation.files`를 사용한다. DB transaction·migration backup lifecycle은 기존 소유자에 남긴다. |
| Natural Search → embedding/index metadata | `models.embedding`과 foundation JSON/검증을 사용한다. simulation 알고리즘을 import하지 않는다. |
| Context Search worker → generation | `models.installation`, `models.generation`을 사용한다. 요청 검증·offline 실행·owner-pipe 종료는 유지한다. |
| Settings → model setup subprocess | source는 `-m localbrain.models.setup`; frozen flag `--install-search-model`은 유지하고 desktop entrypoint의 위임만 바꿨다. |
| Explicit simulation/context/claim trials and development scripts | 공용 파일·모델 기반의 새 경로를 사용한다. 실험 알고리즘·실행 조건을 변경하지 않는다. |

- `work_claim_trial.implementation_fingerprint`가 이동한 `models/generation.py`를 읽도록 수정했다. 이전 경로를 그대로 읽던 첫 검증 실패를 해결했다.
- `db.py` import 변경에 맞춰 Data Model의 소스 digest, packaged schema presentation, schema audit의 manifest digest와 ledger를 갱신했다. 생성물의 차이는 baseline source SHA 두 개뿐이며 table/column/index/relation 의미와 audit disposition은 같았다.
- [Architecture](../../../policies/project/architecture.md)의 현재 package ownership, refactor plan과 plans index를 갱신했다. 최초 조사 기준과 이전 트랙의 완료 이력은 보존했다.
- `tests/test_foundation_models.py`에 7개 경계/실패 검증을 추가했다: 함수 내부까지 포함한 의존 방향, 새 interpreter의 import 격리, 세 가지 설치 layout의 저장 경계, source/frozen worker 명령, atomic JSON 실패·pending 충돌·symlink/hardlink/권한 거부.

### Removed

옮긴 11개 root 모듈과 원래 파일에 있던 추출 정의를 제거했다. 제품 기능·데이터·모델·테스트는 삭제하지 않았다.

## Behavior / Parity Notes

- Behavior-preserving intent: URL/응답, 설정, SQL/DDL, transaction, UTC와 hash의 서로 다른 출력 의미, 파일 권한/소유권/링크/pending 조건, 모델 pins와 cache/manifest 형식, 취소/종료를 유지한다.
- Intentional structural/interface deltas: 내부 import와 source-worker module 경로, 내부 예외 타입의 `__module__`, 소스 바이트에 결합된 검증 지문이 새 위치를 따른다. `ExperimentError`와 `StorageError`는 각각 하나의 새 정의를 공유하며 타입 계층·메시지·catch 의미를 유지한다. 모듈 경로를 저장한 pickle/type 역직렬화 소비자는 조사 범위에서 발견되지 않았다.
- Source-bound trial note: 기존 구현 변경 감지 계약에 따라 `work_claim_trial`의 implementation fingerprint와 configuration identity는 바뀐다. 이전 trial을 재개하면 `EVALUATION_CONFIG_MISMATCH`로 거부될 수 있다. 이전 관측을 새 구현의 평가로 재사용하거나 사용자 모델 자산 identity를 바꾸는 조치는 하지 않았다.
- Parity claim status: `Provisional`.
- Parity confidence basis: `Partial audit` plus regression, packaging and bounded runtime evidence. `Preserved` 또는 merge-safe 판정은 하지 않는다.

기준의 142개 Python 모듈과 추출한 18개 정의를 비교했다. import 문, module docstring, 선언한 모듈 문자열 치환, 두 package-root 표현식, trial의 이동 파일 경로를 제외한 AST는 모두 일치했다. 따라서 비교 대상의 SQL 조건/값, 반환 필드, 분기, 호출 순서, transaction 및 실패 처리 구현에는 추가 차이가 없었다. Import 자체의 의존 방향·소유자는 별도 경계 테스트와 실제 import/worker 기동으로 확인했다. 이 비교가 모든 동적 효과나 실제 모델 실행을 증명하지는 않는다.

114개 route의 path/method/name/schema admission, OpenAPI와 middleware 등록은 기준과 일치했다. exception handler key는 기존 `PreferencesError`와 `OperationBusy`의 새 module 경로만 달랐다. Settings 오류 처리의 테스트는 유지했다.

## Validation

### Baseline / identity

- Planning baseline: `df1d61e526b769fc4d708f8d980419427aae8472`.
- Execution baseline: `6c03265701d0d8b552fc8bb60e346ba1971f4bb3`; 두 기준 사이 source/test/build 변경 없음.
- 검증 대상: 위 commit에 이 배치의 미커밋 작업 트리 변경을 더한 상태. 신규 commit의 검증 또는 merge 판정으로 표현하지 않는다.
- 150개 Python source inventory SHA-256: `f11fccdd23717d84ddce22e860aa4a85c9621e2896d2a4b2e94b6020a5f6dcd1`. 정렬한 `src/localbrain/...py:파일 SHA-256` 행과 마지막 newline을 해시했다.

### Tests / static checks

| Check | Result and scope |
| --- | --- |
| Baseline `.venv/bin/python -m unittest discover -s tests -v` with `PYTHONPATH=src` | 실행 1,433개 통과. `PoolTests.setUpClass`의 loopback bind 제한으로 Drive 전송 11개 미실행; command exit 1. |
| 수정 후 같은 full discovery | 실행 1,440개 통과. 동일한 Drive 11개 미실행; command exit 1. 사용자의 보류 지시로 이 11개는 현재 gate에서 제외했다. |
| `PYTHONPATH=src:tests .venv/bin/python -m unittest test_foundation_models test_work_claims test_data_model_docs test_schema_cleanup_audit test_schema_presentation -v` | 67개 통과. 공유 경계, 이동 파일 지문, 생성물 동기화를 포함한다. |
| 최종 작업 트리 discovery에서 명시적으로 유예한 `test_google_drive_transport.PoolTests.*`만 제외 | 11개 제외를 assert한 뒤 나머지 1,440개를 재실행해 모두 통과; command exit 0. 유예를 위해 테스트 파일을 수정하지 않고 실행 목록만 선택했다. |
| Python 3.9 syntax parse | 150개 앱 모듈 통과; 실제 테스트 interpreter는 Python 3.11.15. |
| Data Model / schema presentation / audit | 관련 테스트 통과. 732개 audit object의 keep 620 / defer 112 / change 0 / remove 0 유지. |
| `git diff --check`, repository privacy | 통과. 최종 문서 포함 privacy 1,623개 후보와 상대 링크 201개를 확인했다. |

기본 `uv run`은 dependency refresh 중 PyPI TLS 신뢰 오류로 테스트 전에 실패했다. 기존 `.venv`를 사용했고 버전 변경이나 인증서 검증 우회는 하지 않았다. sandbox 밖 full test 실행의 자동 승인 검토는 두 번 시간 초과됐다. sandbox 안의 테스트 결과와 미실행 범위를 위와 같이 분리했다.

### Packaging / runtime smoke

- 기존 cache의 Hatchling 1.27.0으로 wheel을 생성하고 `uv pip install --offline --no-deps --target ...`으로 task-owned 설치 경로에 설치했다. dependency upgrade/download는 없었다. 설치된 150개 Python 파일은 현재 source와 byte-for-byte 일치하며 실제 CLI entrypoint의 `--help`가 성공했다.
- Wheel SHA-256: `bcb08138a59d00dadb6507502514560ba6dffdce3ef6c2ceb0fa3e2d44431b7d`.
- 기준 source, 변경 source, 설치 wheel에서 각각 독립 synthetic runtime의 실제 lifespan을 시작하고 종료했다. 인프로세스 ASGI 요청 `/api/health`, `/sessions`, keyword `/natural-search`, `/api/settings`, `/help`, `/static/styles.css`가 모두 200이었다. Synthetic FTS 결과의 identity·title·excerpt·score·URL·anchor가 일치했다. runtime별 경로 필드는 비교에서 제외했다. 모델 라이브러리의 실제 import를 금지한 상태에서 검증했다.
- 실제 `desktop/backend.spec`로 PyInstaller 6.22.3 backend 빌드가 성공했다. 새 foundation/model 모듈 17개가 bundled PYZ에 포함됐다.
- 실제 frozen executable에서 설치 worker의 잘못된 model key와 bundle 내부 runtime 경로를 거부했다. 후자의 디렉터리는 생성되지 않았다. Context Search worker는 빈 isolated Hub에서 offline `MODEL_NOT_CACHED`를 반환했고, 부모 pipe 종료 시 SIGTERM으로 0.001초 내 종료했다.
- `source / installed wheel / frozen` layout의 package-parent 거부 경계를 새 테스트로 확인하고, 실제 wheel runtime 및 frozen worker에서도 파일 경계 경로를 실행했다.

## Risks / Limitations

- Drive 전송 11개는 통과 판정이 아니라 명시적으로 유예한 검증이다. 연동 작업 재개 시 loopback 허용 환경에서 실행한다.
- ASGI 검증은 실제 TCP 서버·브라우저 검증이 아니다. Frozen 증거도 worker 실행 범위이며 native window, 전체 frozen HTTP app, recipient, 실제 모델 추론/성능 또는 live provider 검증을 뜻하지 않는다.
- 사용자 DB·설정·원본·모델 자산은 사용하거나 이전하지 않았다. 설치된 앱과 기존 서버는 교체하지 않았다. 모델 품질·제품 채택·미완성 기능 보완을 검증하지 않았다.
- `main.py`, `queries.py`, `db.py` 및 기능 간 SQL/조립 의존은 후속 단계에 남아 있다. 이번 배치로 모든 기능이 제거 가능한 상태가 되었다고 주장하지 않는다.
- Full strict audit와 merge 판정은 별도 checkpoint에 남긴다. 재현 가능한 검증 범위와 알려진 제외 조건을 인계하며 완전한 동작 동등성으로 확대하지 않는다.

## Next Action

- 다음 후보는 Step 4의 source registry/sync → Session 읽기·근거 → Local Context/Usage 응집화다. 각 배치를 별도로 검토하고, 기존 Workstream/Atlassian adapter 의존은 이후 단계까지 명시적으로 추적한다.
- Google Drive 보류와 전송 검증 유예를 후속 우선순위에 반영한다. 공통 foundation/models 분리를 되돌릴 이유로 삼지 않는다.
- Handoff: 현재 코드·소유 문서·테스트·이 기록이 인계물이다. task-owned 임시 build/runtime/diagnostic 자료는 검증 종료 후 제거하며 durable 문서는 임시 경로에 의존하지 않는다.
