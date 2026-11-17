# FEAT-0168: App-Independent Terminal Runtime Contract

## Metadata

- ID: `feat-0168`
- Status: `passed`
- Type: `foundation`
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Required Evaluators: contract
- Parent PRD: [PRD-0030](../prd/prd-0030-macos-terminal-work-area.md)
- Created: `2026-11-12`
- Updated: `2026-11-12`
- Approval state: human explicitly approved completing both created Features on 2026-11-12; recommended boundary accepted, contract-only execution authorized

## Goal

앱·일반 backend가 종료되어도 terminal 실행을 소유하고, 같은 실행을 다시 찾고
명시적으로 끝낼 수 있는 **독립 runtime의 소유·제공물 수명 계약**을 고정한다.
확정된 Quit/잠자기 유지와 시스템 종료 시 종료를 실제 제공물/identity/관리 경로로
연결한다. 앱 화면·stream 인증·그룹·상태 기호는 별도 결과다.

## Approved Execution Boundary

| 항목 | 제안 | 보존·영향 |
| --- | --- | --- |
| 제공 방식 | macOS Apple Silicon 앱에 Node/PTY·manager·headless/font/license 및 선택한 검사 helper를 동봉. 명시적 첫 terminal/Start 때만 manager 시작 | 사용자 Node/npm 설치·첫 사용 download 불필요, offline 준비. 용량·ABI·서명/라이선스 검증이 늘어남. 빌드 개발 도구는 별개 |
| 실행 소유 | 현재 transient 사용자 launchd manager가 모든 terminal을 생성 순간부터 소유. 앱 창 닫기/Cmd+Q·backend 종료·잠자기는 manager/job 종료 사유가 아님 | New는 표시/선택, Hide/Open은 같은 실행의 표시만 변경. ×·개별/탭/전체/service 종료만 해당 scope를 명시적으로 끝냄 |
| scope | 현재 data/cache scope와 호환 가능한 버전이면 개발 웹/앱이 같은 manager를 발견. 다른 scope는 분리, mismatch는 새 작업을 거부하고 기존 실행의 명시적 관리를 허용 | UI 종류별 강제 분리나 자동 서비스 교체를 도입하지 않음. 단일 입력권·전역 32 record·전체 종료의 영향 범위를 표시 |
| 안정 제공물 | manager와 helper/engine은 실행 중 `.app`/checkout 교체로 사라지지 않는 private runtime payload 경로를 사용. manifest/지문·권한과 실제 실행 경로를 결합 | cache라고 실행 중 payload를 청소하지 않음. 같은 manager가 쓰는 버전을 제자리 덮어쓰지 않고 업데이트는 기존 영향 실행 종료/중지 확인 후 수행 |
| 검사 helper | frozen Python을 일반 interpreter로 부르지 않는 전용 helper 진입을 정의. FEAT-0167의 Rust 공통 경계와 맞춰 프로세스 identity/종료 검사를 제공 | Python/Node의 현행 birth/session/ancestry 판정과 unknown 실패를 보존. 파일을 함께 넣었다는 사실만으로 helper 가용성을 판정하지 않음 |
| 앱 없는 관리 | 앱 동봉의 명시적 관리 진입점으로 남은 실행/서비스를 조회·종료. 기존 `lb`/`localbrain` 의미·사용자 PATH는 보존 | 조회는 비기동, PID만으로 생존/소유를 단정하지 않음. 제거/경로 손실 중 수동 관리·미확인 결과를 안내 |

위 권장 경계는 `2026-11-12`의 “진행 feature들 생성한거 끝까지” 지시로 승인됐다.
앞선 PRD 작성 시점의 추천과 이번 실행 승인을 구별한다. 제품 수명 자체는 재선택하지 않는다.

## Acceptance Contract

- 일반 Quit/창 닫기·잠자기·명시적 stop·backend/manager crash·shutdown/reboot·
  앱 교체/제거 각각의 소유자와 상태 전이를 고정한다. 잠자기 동안 연속 연산/네트워크를
  보장하지 않고, wake/relaunch 때 실제 생존·종료·미확인과 연결/입력권을 다시 확인한다.
- 앱/업무 backend가 없는 동안 manager·프로세스 검사·종료/상태 관리를 실행할
  executable/helper·정적 payload와 private 경로/권한/버전/retention을 명시한다.
- 현재 data/cache scope·launchd domain/label·socket/control lock·manager generation·
  PID birth/session/descendant identity와 payload fingerprint의 관계를 고정한다.
  old/new 개발/설치본의 동시 시작·거부/관리와 destructive confirmation snapshot을 보존한다.
- manager만의 생존과 개별 terminal/job 생존을 구별한다. 실패한 종료는 기록/오류를
  남기며, empty list·backend 종료·연결 단절·저장 PID를 종료/생존의 증거로 삼지 않는다.
- 업데이트/재시작은 영향 실행을 종료하고 중지 확인 후 수행한다. 일반 Quit 후 유지가
  무중단 교체나 강제 종료 성공을 뜻하지 않는다. 앱 삭제 때의 남은 실행·payload
  회수와 캐시/backup/restore의 제외를 정의한다.
- VT 화면/명령·입출력·환경·credential을 영속화/색인하지 않는다. shutdown/reboot 후
  같은 프로세스/화면·새 셸 재생성·명령 replay를 제공하지 않는다.

## Scope Boundary

- In: 독립 실행 owner·runtime scope/identity·version/payload/helper·Start/stop/
  Quit/sleep/reconnect/update/remove·앱 없는 관리 계약과 합성 실패/경합 검증표.
- Out: 실행 코드/실제 package build·사용자 서비스 제어·앱 설치/교체·기존 실행 종료,
  로그인 agent·root daemon·remote·자동 updater·공개 배포·화면/탭 그룹·새 상태 신호·
  앱 HTTP/WS 인증 구현. 후자의 별도 foundation은 parent C-02가 소유한다.

## Surface Lanes

| Lane | 참고 path roots | 책임·의존성 | 평가 |
| --- | --- | --- | --- |
| contract/backend | terminal/runtime.py, processes.py, manager.cjs, ownership.cjs | 현재 identity/stop/소유와 선택된 Rust helper/control의 계약 대응. FEAT-0167 의존 | contract |
| data/contract | private runtime scope/identity/manifest/use-lease/loss metadata | cache metadata의 단일 소유·schema·원자적 변경·backup 제외를 고정. DB/원본/VT 영속화 없음 | contract |
| integration/infra | desktop/src-tauri, desktop/backend.spec, scripts/build-desktop.py, CLI | host와 독립 payload의 경로·기동·Quit/교체·관리 진입점. 현재 제외는 구현 전 유지 | contract |
| docs | terminal/desktop/storage/privacy/installation owners와 parent PRD | 대상 수명·runtime 청소/복구·사용자 안내와 실제 수락 한계 | contract |

## Contract Surfaces

manifest/지문·runtime 경로/소유·프로세스 검사 I/O·manager protocol·generation/control
lock·launchd 수명·CLI exit/error·scoped termination confirmation·업데이트/캐시 정리.
Host admission·browser stream·input lease는 기존 계약을 보존하고 별도 접근 foundation과 연결한다.

## Entry, Exit And State Expectations

- Entry: 이 Feature의 경계 승인과 [FEAT-0167](feat-0167-rust-core-and-host-contract.md)의
  runtime/host 계약 승인 후 Spec 구체화. 구현을 시작하는 후속 product는 해당 foundation PASS가 필요.
- Default/empty: 조회/설정/화면 진입은 service·engine·shell을 설치/시작하지 않음.
  terminal record/IPC가 없을 때만 기존 idle60s 종료를 유지.
- Live/hidden: 표시 여부·앱 생존과 manager 소유는 독립. 같은 ID/generation/checkpoint로 재연결.
- Error: stale/unknown/mismatch·helper 실패·부분 종료·PID 재사용은 구별하고 scope 밖 프로세스를 보호.
- Exit: 실제 앱 통합 Spec이 runtime 소유·경로·복귀/종료/업데이트를 다시 선택하지 않아도 되는 계약.

## Dependencies

FEAT-0167의 first slice·host/helper contract는 Run247에서 선행 완료됐다. 현재 웹의 실행 의미는
[Terminal policy](../../policies/project/terminal.md)와 [FEAT-0166](feat-0166-web-terminal-work-area.md)을
참조한다. 현재 웹 PASS를 앱/OS별 수락으로 재사용하지 않는다.
앱 첫 셸 product는 이 계약 외에 parent C-02 접근 계약, 그룹/상태 product는 각각
C-08/C-06 foundation을 필요로 한다. 이를 이 Feature가 흡수하지 않는다.

## Likely Affected Surfaces

현재 terminal runtime/manager/helper·desktop assembly/build/Quit·앱-only 관리 진입과
설정/storage/cache/Docs의 owner. 이 단계는 계약이며 현재 native 제공을 활성화하지 않는다.

## Pass Or Fail Checks

1. 앱/업무 backend가 없는 상태에도 manager와 검사/관리 경로가 `.app`/checkout에
   의존하지 않는 실행 경로·지문·권한으로 추적된다. frozen helper의 interpreter 오용이 없다.
2. data/cache 동일·상이·version mismatch·동시 Start·PID reuse·helper unknown·종료
   경합·부분 실패별 결과와 확인 scope가 명확하고 자동 교체/광역 종료가 없다.
3. 정상/강제 Quit·sleep/wake·crash·reboot·cache clear·업데이트/제거의 전이 표가
   실제 liveness/unknown·유지/종료·no replay와 모순되지 않는다.
4. 앱-only 사용자도 PATH 수정 없이 조회/종료를 수행할 관리 계약이 있고 조회는 비기동이다.
5. 실제 package/native/OS/물리 입력 수락에서 해야 할 검증과 현재 source-only 한계를
   별도로 명시한다. 계약 검토만으로 실제 앱 PASS를 보고하면 FAIL이다.
6. scope·제공물·수명/상태·관리 경로의 blocking ambiguity가 남으면 parent/Feature 검토로 반환한다.

## Regression Surfaces

탭당4 pane·scope당32 record, memory-only VT·no replay, single input lease·checkpoint,
Unicode/D2Coding13px·IME·흐름 제어, New/Hide/Open/×, identity-safe stop·업데이트 종료,
기존 Python/CLI·개인 자료/원본·앱 인증·중단/제외 기능·전역 PATH/rc 불변.

## Harness Trace

- Active spec: [SPEC-0168](../spec/spec-0168-app-independent-terminal-runtime-contract.md)
- Active run: [RUN-248](../run/run-20261112-248-app-independent-terminal-runtime-contract.md)
- Execution profile: foundation-contract
- Latest evaluator report: [EVAL-0164](../evaluation/eval-0164-app-independent-terminal-runtime-contract.md), PASS / complete for the bounded contract
- Latest fix note: none

## Continuity Notes

- `2026-11-12` 계약 완료: Run248/Eval0164에서 scope/payload/helper·앱 없는 관리·
  모든 선택된 수명·버전/정리/손실 상태를 확정했다.
  [계약 owner](../project/app-independent-terminal-runtime-contract.md)가 후속 입력이다.
  실제 실행 파일/앱·OS 수명/성능 검증이나 전체 PRD 완료로 보고하지 않는다.

- `2026-11-12` 경계 승인/착수: 사용자가 생성한 두 Feature의 완료를 명시적으로
  지시했다. 먼저 FEAT-0167의 Run247 계약 PASS를 확인하고 Run248에서 독립 수명/
  제공물 계약을 진행한다. 앱 접근/그룹/상태 product 구현이나 사용자 실행 제어는 추가하지 않는다.

- `2026-11-12`: 진행 지시 후 PRD-0030 C-01을 독립 수명/제공물 계약으로 구체화했다.
  현재 frozen helper와 `.app` 의존 경로의 한계, 선택된 Quit/sleep 유지와 업데이트 종료를
  연결했다. 제공물/scope/관리 권장안은 이번 경계 검토 대상이며 코드·service는 바꾸지 않았다.
