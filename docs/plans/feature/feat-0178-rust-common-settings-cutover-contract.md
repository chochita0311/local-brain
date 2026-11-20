# FEAT-0178: Rust Common Settings Cutover Contract

## Metadata

- ID: `feat-0178`
- Status: `passed`
- Type: `foundation`
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Required Evaluators: contract
- Parent PRD: [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md)
- Created: `2026-11-17`
- Updated: `2026-11-17`
- Approval state: human approved the proposed contract-only boundary with “진행” on 2026-11-17. Spec, contract build and evaluation are authorized; runtime implementation remains a separate product Feature.

## Goal

공통 Rust 실행부가 `settings.toml`의 일반·Terminal 설정을 함께 책임지도록 옮길 때
사용할 **하나의 설정 트랜잭션과 host 연결 계약**을 확정한다. 기존 terminal용
실행파일 탐색과 Python 잠금에 바로 연결하면 생기는 설치·의존성·교착 모호성을
해결하는 첫 Phase3 단위다. 실제 writer 포팅은 이 계약을 통과한 별도 product
Feature가 수행한다.

## Acceptance Contract

1. 현재의 Python generic parser/commit 및 Rust terminal validation 경계와,
   이후 Rust가 소유할 일반·Terminal 설정 해석/검증/정상 저장을 명확히 대응시킨다.
   web·app·CLI host는 같은 업무 규칙을 소비한다. Python 복구 owner의 명시적
   파일 교체는 같은 잠금/lease 아래 유지하며 정상 저장의 별도 fallback으로 쓰지 않는다.
2. 데이터 디렉터리별 thread mutex와 `operations.lock`의 O_NOFOLLOW/nonblocking
   flock, 같은 thread의 중첩 호출을 보존하는 cross-process 규칙을 하나로 선택한다.
   부모가 가진 flock을 자식이 새로 여는 것을 재진입으로 취급하지 않는다.
   외부 잠금이 이미 있는 호출, 수집·source 수정·backup/restore와의 충돌,
   crash/cancel/응답 유실 후 해제·readback 조건이 결정되어야 한다.
   새 manager control 잠금을 설정 저장 중 잡거나 자동 재시도하지 않는다.
3. common `saved/effective/source/revision`과 내부 raw TOML, terminal snapshot 및
   prepare/저장 응답을 보존할 닫힌 호출/오류 계약을 정한다. 알려진 필드는 정확한
   타입으로 검증하고 unknown TOML 날짜/시각·큰 정수·float·중첩 table/array 값을
   실제 Python baseline의 허용/거부와 비교한다. JSON 변환으로 타입·정밀도·값을
   잃거나 현재 거부하던 값을 조용히 저장하지 않는다. 주석 보존은 새 요구로 추가하지 않는다.
4. schema1 및 7개 common 값/default/validation, missing과 invalid, retired raw
   필드, content SHA256 revision, schema/onboarding 직렬화 순서와 private
   temp/fsync/replace/directory-fsync를 보존한다. malformed/unsupported/stale 및
   저장 불가 기존 값은 원본을 보존한 오류다. read는 파일/서비스를 만들지 않고,
   첫 startup의 기본 파일 생성은 기존 초기화 규칙을 따른다.
5. Terminal을 assembly에서 빼거나 Node/launchd/선택형 모델이 없어도 공통 설정을
   사용할 수 있는 runtime 탐색·호출·배포 경계를 고정한다. 현재 macOS source/web,
   설치 wheel과 frozen app의 필요한 실행파일/asset 제공·오류·복귀 조건을 각각
   정한다. foundation이 terminal feature를 import하는 역방향 의존성이나 순환을
   만들지 않는다. core는 Tauri/FastAPI에 종속되지 않는다.
6. 전환 전후 package/protocol/build 식별과 버전 거부/복귀 범위를 정한다.
   runtime 부재나 불일치를 성공/새 설정 초기화로 바꾸지 않는다. 공통 설정 때문에
   Terminal payload/manager를 설치·업데이트하거나 기존 shell 작업을 종료하지 않는다.
   실제 crate/toolchain/MSRV/라이선스 및 새 TOML 의존성은 기존 locks와 공식 버전
   근거로 확인하며, 선언된 MSRV만으로 build 통과를 주장하지 않는다.
7. downstream product Feature의 source-to-target map, 정상/실패/동시성/초기화/
   restart 및 source/wheel/native 검증 기준이 구체적이어야 한다. 계약만 통과한
   결과를 실제 Rust 설정 저장이나 성능 향상으로 보고하지 않는다.

## Scope Boundary

### Inherited Common Values

다음은 새 설정 제안이 아니라 현재 owner의 보존 대상이다. 모든 필드는 누락된
경우에만 default를 적용한다. `saved`와 `effective`는 같은 resolved 값이며
`source`는 `saved` 또는 `default`다.

| Field | Exact validation | Missing-field default |
| --- | --- | --- |
| `startup_screen` | string, `sessions` / `sessions-dashboard` / `context` | `sessions` |
| `timezone` | valid IANA zone string | 시스템 zoneinfo, 유효하지 않으면 `UTC`; process `TZ`와 과거 preference 환경변수는 적용하지 않음 |
| `session_sync_enabled` | boolean | `true` |
| `session_sync_minutes` | `type(value) is int` 및 `10 <= value <= 1440`; bool 거부 | `10` |
| `context_sync_enabled` | boolean | `true` |
| `context_sync_minutes` | `type(value) is int` 및 `10 <= value <= 1440`; bool 거부 | `30` |
| `onboarding_completed` | boolean | `false` |

`schema_version`도 `type(value) is int` 및 `value == 1`이어야 한다. 폐기된
`project_display`/`projects`는 unknown raw로 유지하되 active preferences에서
제외하고 새 update를 거부한다. 잘못된 retired raw 값은 다른 유효한 설정을
막지 않는다. `LOCALBRAIN_PROJECT_DISPLAY`도 무시한다. 기존 preference 환경변수
`LOCALBRAIN_STARTUP_SCREEN`, `LOCALBRAIN_TIMEZONE`,
`LOCALBRAIN_SESSION_SYNC_ENABLED`, `LOCALBRAIN_SESSION_SYNC_MINUTES`는 값이
유효한지와 관계없이 무시한다.
기존 파일은 partial/invalid라도 startup에서 덮어쓰지 않는다. absent-file
startup 생성에만 기존 Session 등록 또는 enabled Context가 있으면 onboarding을
complete로 초기화하고, 새 설치는 incomplete를 유지한다. 일반 read의 생성 부작용은 없다.

### Included And Excluded Work

- In: 현재 `settings.toml` producer/consumer·잠금/복구 경로 조사, 목표 transaction/
  host/오류/value/전달/호환 계약과 검증 사례, 후속 product Feature의 정확한 경계.
- Out: runtime 코드·manifest/lock 변경, 실제 Rust writer 구현, DB/Session/Usage/
  Context migration, `session-sources.toml`·search JSON·model registration 포팅,
  UI 변경, native 기능 편입, 서비스/앱 교체, 개인 자료·모델 다운로드·외부 전송,
  전체 Python 제거, 중단 기능 재개, Windows/Intel/Linux 제공, commit/push/배포.

## Surface Lanes

| Lane | Path roots / dependency | Contract outcome and evaluator |
| --- | --- | --- |
| settings transaction | `foundation/preferences.py`, `operations.py`, `terminal/settings.py`, `app/storage/recovery.py` | 기존/목표 writer·lock·raw value·revision·실패/복구 대응; contract |
| common host and delivery | `terminal/core.py`, `rust/`, `app/`, root CLI/desktop, packaging inputs | Terminal 독립 transport·package 제공·scope/identity·종료/오류; transaction 계약에 의존; contract |
| consumers and handoff | lifecycle/settings/edition/templating, sources sync, Usage, owner docs, related tests | producer→결과→consumer 및 후속 product 검증/회귀표; 앞 두 lane에 의존; contract |

## Contract Surfaces

`settings.toml` schema/value/default/unknown/byte revision, shared lock and recovery
lease, settings/terminal HTTP 결과·오류 및 인증, Python 호환 API/raw 반환,
Rust host framing/runtime discovery/build identity, 최초 생성/읽기/저장/복귀와
schedule/time-zone 적용 시점. 범위 밖 파일은 기존 owner·잠금·serializer를 유지한다.

## Entry, Exit And State Expectations

- Entry: 사람이 이 foundation의 경계를 승인한 뒤 Spec과 contract-only Run 진행.
- Default/empty: 누락 파일은 read-only defaults와 빈 bytes의 SHA256 revision;
  startup만 기존 등록 상태에 따라 onboarding과 기본 파일을 초기화한다.
- Loading/busy: 기존 operation 충돌을 유지하며 별도 worker/manager 기동 없음.
- Error: invalid/version/revision/transport/identity와 응답 유실을 구별한다.
  commit 전 실패는 기존 bytes를 보존한다. commit 여부가 불명확하거나 commit 뒤
  응답을 잃으면 재조회로 판단하며, 저장된 결과를 임의로 되돌리거나 stale patch를
  맹목 재실행하지 않는다.
- Success/exit: writer/lock/value/transport/delivery 선택이 남지 않은 계약과
  downstream product 경계. 실제 포팅/설치/측정 성공은 이 Feature의 결과가 아니다.

## Dependencies

- Approved PRD-0029, passed FEAT-0167 및 Run251의 현재 terminal contract.
- [Phase3 inventory](../project/rust-backend-migration-inventory.md),
  [공통 설정 owner](../../policies/project/desktop-app-and-settings.md#common-settings-contract),
  [공통 writer 전환 경계](../project/rust-core-and-host-contract.md#shared-settings-writer),
  [회귀 관리](../../policies/project/change-scope-and-regression.md).
- Feature177의 실제 native 창 검증과 독립적으로 기획/계약 가능하나 그 gate를
  이 작업으로 닫거나 이전 pass를 재사용해 통과로 표시하지 않는다.

## Likely Affected Surfaces

계약 실행 시 이 Feature의 Spec/Run/contract evaluation 및 기존 core/host 계약을
단계별로 갱신한다. 첫 slice의 역사적 Python writer 사실과 아직 미구현인 목표를
구분한다. 실제 구현은 별도 product Feature에서 architecture/settings/storage/
developer guide·build/wheel/CLI owners와 모든 직접 consumer를 함께 갱신한다.

## Pass Or Fail Checks

1. common·terminal save/read, 첫 startup, native start redirect, templates,
   timezone Dashboard, 두 scheduler와 backup/restore를 추적하면 각 단계의
   actor·lock·입력/출력·write/실패 owner가 하나로 확인된다.
2. type/schema/default/unknown/serialization 표가 실제 기준 코드 및 합성
   경계값을 인용한다. bool 대 integer, missing 대 invalid, 중첩 unknown/date/
   large number, malformed/unsupported, 빈 파일·partial·retired 필드를 구별한다.
3. 두 저장 요청/process 및 이미 잠금이 있는 caller, scan/restore 경쟁, commit 전후
   child crash/응답 유실에서 단일 잠금·해제가 결정돼 있다. commit 전에는 기존
   bytes를 보존하고, commit 여부 불명/이후에는 readback으로 결과를 판단한다.
4. source/wheel/frozen app·Terminal 제외·Node/model 없음·runtime 없음/불일치의
   각 선택과 전달 owner가 명확하고, foundation→terminal import가 필요 없다.
5. 후속 product의 정확한 범위·dependency·실제 artifact/native 검증과 rollback이
   추측 없이 작성 가능하다. material 미결정은 FAIL/기획 반환이며 product로 넘기지 않는다.
6. 현재 단계의 product code/개인 runtime 불변을 확인하고 문서/link/catalog/
   privacy 검사를 통과한다. 미래 runtime 사례를 실행 완료 증거로 쓰지 않는다.

## Regression Surfaces

현재 일반 설정 및 terminal 기본값의 상호 보존, stale revision과 unknown TOML,
첫 startup/onboarding·다음 실행 startup 선택·다음 화면 timezone·다음 schedule
적용과 진행 중 수집 불간섭, source/reconnect/search/model/Context 별도 저장소,
backup/restore/cache/DB lease, base wheel 기동과 Terminal 비설치, 기존 terminal
payload/작업·HTTP/WS 인증·CLI·잠금·수명 및 feature admission.

## Harness Trace

- Active spec doc: [SPEC-0178](../spec/spec-0178-rust-common-settings-cutover-contract.md)
- Active run: [RUN-259](../run/run-20261117-259-rust-common-settings-cutover-contract.md)
- Execution profile: foundation-contract
- Latest evaluator report: [EVAL-0175](../evaluation/eval-0175-rust-common-settings-cutover-contract.md), PASS / complete for the bounded contract
- Latest fix note: none

## Continuity Notes

- `2026-11-17` 계약 완료: Run259/Eval0175에서 writer·상속된 lock descriptor·typed
  codec·독립 common runtime 전달/거부·복귀를 확정했다. Python 문법/OS-zone
  adapter와 명시적 recovery는 유지한다. 실제 port는 별도 draft FEAT-0179의
  승인 대상이며, 이 Feature의 pass는 실제 Rust writer/native/performance pass가 아니다.

- `2026-11-17` 경계 승인: 사용자가 바로 앞의 FEAT-0178 계약 확정 제안에 “진행”으로
  답했다. foundation-contract 실행을 승인한 것으로 반영하고 Run259를 시작한다.
  actual writer/runtime 포팅·앱 교체·배포의 승인은 추가하지 않는다.

- `2026-11-17`: Rust Phase3 재개 요청으로 전체 기능/consumer inventory와 함께
  첫 경계를 제안했다. 기존 terminal control 승인을 common writer 포팅 승인으로
  확대하지 않았다. 사람의 경계 승인 후 contract-only 실행이 다음 단계다.
