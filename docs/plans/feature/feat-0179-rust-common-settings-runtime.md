# FEAT-0179: Rust Common Settings Runtime

## Metadata

- ID: `feat-0179`
- Status: `passed`
- Type: `product`
- Surface: `mixed`
- Execution Profile: `backend-product`
- Required Evaluators: contract, functional
- Parent PRD: [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md)
- Created: `2026-11-17`
- Updated: `2026-11-18`
- Approval state: human approved this implementation boundary with “진행” on 2026-11-18 after the explicit FEAT-0179 implementation proposal. Spec/build/evaluation are authorized; installed-app/service replacement and publication remain excluded.

## Goal And User-Visible Outcome

현재 macOS 앱·개발용 웹에서 일반 설정과 Terminal 기본값을 읽고 저장하면,
공통 Rust 업무 규칙과 하나의 정상 저장 경로가 기존 값·unknown 설정·동시 수정
처리를 보존한다. 새 설정은 기존 시점에 적용되고, Terminal이 설치되지 않은
기본 웹/wheel에서도 일반 설정을 사용할 수 있다.

첫 구현 대상은 Apple Silicon/macOS14다. 기존 GUI·HTTP/CLI host와 Python의
TOML 문법 codec·OS 시간대 조회는 유지한다. 정상 설정 규칙·병합·revision 검사·
파일 commit은 Rust로 옮긴다. 전체 Python 설정/백엔드 제거를 완료하는 범위가 아니다.

## Acceptance Contract

1. [확정된 전환 계약](../project/rust-common-settings-cutover-contract.md)을 구현한다.
   일반/Terminal 설정은 같은 core의 semantic/commit 경로를 사용하고, 정상 저장을
   Python으로 우회하는 fallback은 없다. 명시적 recovery 교체와 다른 파일을 쓰는
   serializer/atomic helper 소비자는 기존 owner·잠금 아래 유지한다.
2. schema1, 7개 common 값/default/타입·오류 우선순위·unknown/retired 값·정렬·
   SHA256 revision·private atomic save와 최초 생성/읽기/재시작을 보존한다.
   bool/int, 큰 정수, float overflow/nonfinite/signed zero, 날짜/시각·offset/정밀도,
   중첩 table/array 및 읽기 가능/저장 거부 입력을 실제 old/new 경로로 비교한다.
3. 부모의 같은 mutex/flock descriptor를 전달하고, outer-lock 재진입과 경쟁 요청,
   수집/source/backup/restore serialization, child/codec 종료·응답 유실·commit 전후
   실패를 검증한다. Child close는 부모 잠금을 해제하지 않는다. 기존 일반 save의
   lock 밖 readback과 Terminal save의 lock 안 readback을 유지한다.
4. Terminal assembly/Node/launchd/model/cache 없이 common runtime을 제공한다.
   source·설치 wheel·frozen app은 검증된 executable/receipt/capabilities를 사용한다.
   Foundation의 terminal import, PATH/브라우저 지정 실행파일, silent 구버전 fallback,
   Terminal payload 설치·교체·실행 중 작업 종료를 만들지 않는다.
5. 새 common transport의 **40초 operation deadline**, runtime 부재/버전·hash·
   target 불일치503 및 startup write 전 거부를 구현·검증한다. 이는 새 내부 실패
   경계이며 성공한 saved/default 값으로 숨기지 않는다. 기존 malformed preferences
   오류와 Settings 복구는 구별한다. 무관한 CLI에는 전역 preflight를 추가하지 않는다.
6. 기존 설정 UI/API·auth·네이티브 token/origin·초기 설정·두 scheduler·Dashboard
   timezone·template 소비자가 같은 동작을 보인다. 기본값 저장이 기존 terminal
   job/workspace, source/DB/model 상태를 변경하지 않는다.
7. 실제 source/wheel/native 빌드와 합성 데이터의 저장·재열기·재시작을 확인한다.
   플랫폼 wheel tag와 final signed binary/source 지문을 검증하고, 최소 compiler
   미검증 등 남은 gate를 실제 검증 범위와 분리한다. 실행 비용/지연은 측정하며
   Rust라는 이유로 개선이나 전체 동등성을 선언하지 않는다.

## Scope Boundary

- In: 공통 runtime/codec channel, settings Rust rules/transaction, host lease
  전달과 facades, 직접 연결된 startup/error/consumer wiring, common executable
  source builder·Hatch wheel hook·frozen resource/signing/receipt, 회귀 검증·owner docs.
- Retained: Python syntax codec/OS zone provider·HTTP/CLI/Jinja hosts·선택형 모델,
  Node PTY/VT, 명시적 Python restore copier, 다른 파일을 쓰는 shared helpers.
- Out: DB/schema/Session/Usage/Context ingestion·다른 설정 저장소 포팅, UI framework/
  모델/VT 교체, native 기능 편입, 중단 기능 재개, 데이터 이동/초기화, Windows/
  Intel/Linux 신규 제공, 사용자 terminal 입력/종료/재시작, 설치 앱 교체·서비스
  업데이트·배포·commit/push. 기존 미대상 설치와 사용자 자료를 자동 변경하지 않는다.

## Surface Lanes

| Lane | Path roots / order | Owner and evidence |
| --- | --- | --- |
| core/transaction | `rust/`, `foundation/operations.py`, codec/transport; first | Builder; locked core tests, exact differential values/errors/bytes, real inherited-fd/concurrency/failure witnesses; contract/functional |
| adapters/consumers | preferences/terminal settings, app startup/settings/edition/templates consumers, sources sync, Usage; after core | Builder; same public APIs, startup/readback/time-zone/schedule and isolated browser/native settings behavior; contract/functional |
| packaging/docs | common builder/Hatch metadata, backend spec/desktop resources/build identity, owners/guides; after compatible core/bridge | Builder; source/wheel/frozen inclusion, no terminal prerequisites, final artifact/target/identity and owner checks; contract/functional |

## Contract Surfaces

설정 TOML schema/order/unknown values and content revision; inherited operations
lease and recovery transaction; closed preferences/callback protocol/identity;
existing public settings/terminal HTTP and CLI outputs/errors/auth; platform wheel
tag and common binary receipt; app/startup/schedule/readback timing. The owning
contract defines the exact predicates, stages and stop/refusal outcomes.

## Entry, Exit And State Expectations

- Entry: human approves this product boundary after FEAT-0178 passes; then its
  own Spec/Run may start. It does not borrow the contract-only Run as a code Run.
- Default/empty: read-only defaults, no data/cache/service creation; existing
  startup-only initialization remains.
- Loading/busy: preserve existing nonblocking busy/error/retry behavior and
  settings readiness. A dead/missing executable is not healthy preferences.
- Error: invalid/stale/unsupported refuses without publication; post-rename or
  lost-response uncertainty requires readback, without stale replay/rollback.
- Success: general/Terminal settings remain consistent after app/web readback
  and restart. Notification/timing and running collection/terminal jobs are preserved.
- Exit: bounded executable evidence and recorded residual Python/Node/platform/
  native limitations; no whole-backend or whole-PRD completion implied.

## Dependencies

- [FEAT-0178](feat-0178-rust-common-settings-cutover-contract.md) must be `passed`,
  with [EVAL-0175](../evaluation/eval-0175-rust-common-settings-cutover-contract.md)
  and the selected contract as inputs before this product enters build.
- Existing Rust terminal/core and settings/storage/auth contracts remain; Node
  runtime readiness is not a common-settings prerequisite.
- Latest Terminal177 native-window evidence is separately pending; do not waive
  it or use a new settings pass to accept its UI packet.

## Likely Affected Surfaces

`foundation/` preferences/operations/new neutral Rust bridge and codec extraction;
`terminal/settings.py` and current core validation; Rust library/runtime;
app startup/settings/edition/error adapters and necessary direct consumers;
source/common/frozen packaging scripts and manifests; relevant meaningful
tests/isolated QA; architecture/settings/storage/developer/README/app guides,
transition/inventory/catalog. Preserve unrelated pre-existing changes.

## Pass Or Fail Checks

1. Freeze old/new actual code/locks/config/guidance and compare all contract flows,
   including query/write/output/error/effects/nesting/readback, with independent
   data/concurrency omission review and renewed witnesses after repairs.
2. Existing relevant tests and new meaningful cases pass exact values/types/
   serializer bytes and rejection/error priority. Include malformed, absent,
   empty, partial, future schema and unchanged second startup/sync consumers.
3. Competing real processes/threads and outer caller retain one lock through
   callback/worker lifetimes; pre/postcommit/timeout/reply-loss cases distinguish
   old-byte preservation from successful/unknown publication and safe retry.
4. Isolated source and installed platform wheel start/read/save/restart with
   Terminal omitted, no Node/model requirement and correct common binary identity;
   missing/mismatched/unsupported runtime refuses before startup writes. Unrelated
   CLI commands preserve their contracts.
5. Final built arm64 app's actual packaged backend and native Settings save/reopen
   use the reviewed binary/assets, preserve auth and other consumers, and report
   actual UI/OS evidence limits separately. No installed-app replacement follows
   automatically from building/testing the artifact.
6. Configured Rust/Python/asset/build and privacy checks appropriate to the changed
   paths pass. Report measured cold/warm call/render costs and minimum compiler/
   platform gaps; source tests alone do not pass artifact/native/whole-app parity.

## Regression Surfaces

All contract consumer-map rows, source/Session/Usage/model/index identities and
immutable snapshots, source/search/model/Context separate stores, backup/restore/
cache and helper consumers, optional feature exclusion, existing terminal
manager/leases/checkpoints/IME/status/workspaces and live jobs, native lifecycle,
CLI, first-use/settings presentation/readiness and original privacy boundaries.

## Harness Trace

- Active spec doc: [SPEC-0179](../spec/spec-0179-rust-common-settings-runtime.md)
- Active run: [RUN-260](../run/run-20261118-260-rust-common-settings-runtime.md)
- Execution profile: backend-product
- Latest evaluator report: [EVAL-0176](../evaluation/eval-0176-rust-common-settings-runtime.md), contract/functional PASS for this product; platform/physical/whole-backend limits remain
- Latest fix note: none

## Continuity Notes

- `2026-11-18`: Run260/Eval0176에서 공통 설정 구현을 통과했다. Rust 정상 저장과
  source·설치 wheel·최종 서명 앱의 실제 General/Terminal 저장·재열기·재시작을
  확인했다. Python 1,731개 실행(49개 선택형 skip), Rust11개, 차등277개,
  브라우저70개 검사가 통과했다. 프로세스 호출 비용으로 표본 읽기/저장은 기존보다
  느리다. Python 문법/OS-zone/host와 Node는 유지하며, 전체 backend·최소 버전·
  물리 입력·Terminal177의 별도 창 수락 및 사용자 앱 설치는 완료 범위가 아니다.

- `2026-11-18`: 사용자 승인으로 Spec0179/Run260의 실제 구현을 시작한다. 기존
  계약-only 승인과 구별하며, 사용자 앱·Terminal 서비스 교체/종료나 publication은 포함하지 않는다.

- `2026-11-17`: downstream product proposal prepared from Run259's bounded
  contract evaluation. Retained codec/platform dependencies and new40-second/
  unavailable-runtime failure boundary are explicit for human review. No code,
  new product Spec/Run, user runtime or deployment is started by this draft.
