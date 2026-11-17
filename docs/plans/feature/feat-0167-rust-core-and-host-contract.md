# FEAT-0167: Rust Core And Host Contract

## Metadata

- ID: `feat-0167`
- Status: `passed`
- Type: `foundation`
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Required Evaluators: contract
- Parent PRD: [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md)
- Created: `2026-11-12`
- Updated: `2026-11-12`
- Approval state: human explicitly approved completing both created Features on 2026-11-12; recommended boundary accepted, contract-only execution authorized

## Goal

웹 서버·macOS 앱·CLI가 Tauri에 종속되지 않은 Rust 업무 코어를 사용하는
전환 계약을 고정한다. 첫 포팅 범위·호스트 경계·선택형 runtime·기존 자료의
호환/복귀를 하나의 소유권 계약으로 정해, 후속 구현이 실행 구조를 추측하지 않게 한다.
이 Feature는 포팅 자체나 앱 터미널의 사용자 수락을 완료하는 작업이 아니다.

## Approved Execution Boundary

다음 권장 경계는 `2026-11-12`의 “진행 feature들 생성한거 끝까지” 지시로 승인됐다.
앞선 PRD 작성 시점의 추천과 이번 실행 승인을 구별한다.

| 항목 | 제안 | 이유·영향 |
| --- | --- | --- |
| 첫 Rust 전환 | Terminal의 설정 해석·manager 조회/제어·프로세스 검사·CLI/host 연결을 첫 공통 업무 경계로 삼음. 실제 데이터/설정 writer와 protocol 교체는 후속 product Feature에서 수행 | 앱 terminal을 Python과 Rust로 각각 새로 통합하는 중복을 피하고, Session/Usage/수집 포팅 전에 독립된 수명 경계를 검증 |
| 코어와 host | Rust core가 업무·identity·오류 규칙을 소유. 웹 HTTP, CLI, Tauri는 얇은 adapter. core는 Tauri·WebView·브라우저 타입을 import하지 않음 | 앱은 최종 사용처이고 웹은 같은 기능의 개발 확인 경로. 공통 코드와 같은 실행 프로세스는 구별 |
| 화면/전송 | 기존 HTML/CSS/JavaScript·xterm과 현재 HTTP/WebSocket 소비자 계약을 우선 보존. Jinja를 쓰는 다른 화면은 기존 backend에 남길 수 있음 | GPUI/React 전면 전환이나 앱 전용 IPC 최적화를 1차 전제에 넣지 않음. 현재 Python이 남는 과도기를 명확히 보고 |
| 선택형 runtime | 1차에는 Node/node-pty/headless와 선택형 Python 모델을 유지. 기본 화면/검색에 모델을 필수화하지 않음 | Rust는 먼저 control/업무 경계를 맡음. 순수 Rust 배포·VT 엔진/모델 교체는 별도 결과이며 완료했다고 주장하지 않음 |
| 기존 자료 | DB schema·설정 포맷·ID/원본·Usage 스냅샷·검색/모델 호환 식별 유지. 전환 실패 시 자동 초기화·명령 replay 없이 거부/복귀 | Terminal 첫 전환을 위해 다른 제품 자료를 migration하거나 수집을 다시 하지 않음. 임의 버전 downgrade를 보장하지 않음 |
| 후속 순서 | 이 계약 → [앱 독립 runtime 계약](feat-0168-app-independent-terminal-runtime-contract.md) 및 접근/그룹/상태 foundation → 첫 Rust terminal 흐름과 실제 앱 통합 | 모든 Python 기능의 선행 포팅은 요구하지 않음. 이후 Session/Context/검색 등 공통 기능의 전체 편입 의무는 parent PRD에 남김 |

## Acceptance Contract

- 활성 앱·개발용 웹·CLI의 현재 기능/미편입/중단 경계를 목록화하고 각 업무 owner,
  Rust 전환/유지/후속 포팅 상태를 표시한다. 첫 slice가 장기 동등성을 축소하지 않는다.
- core·web/CLI/Tauri adapter·기존 Python 영역·Node manager·모델 worker의 호출 방향,
  실행 주체, 기동/종료/취소, 설정/자료 writer와 인증 경계를 고정한다.
- 첫 terminal slice의 요청/응답·오류·호환 식별·retry/중복 생성·stream/입력권·
  프로세스 검사에 대해 현재 producer/consumer와 바뀔 owner를 대응시킨다.
- Python web이 공통 Rust 업무를 호출하는 구체적 경로와 Tauri가 같은 규칙을
  소비하는 경로를 선택한다. 두 host의 별도 업무 구현이나 인증 없는 우회 경로를 만들지 않는다.
- schema/설정 revision·lock·원자적 저장·unknown 보존, 기존 서비스가 실행 중일 때의
  version 거부/관리, 전환 전 복구와 실패 후 되돌릴 수 있는 정확한 범위를 정한다.
- 필요한 Rust crate/toolchain/target·빌드/라이선스 조건을 실제 manifests/locks 및
  버전에 맞는 공식 근거로 확인한다. 새 의존성이 기존 host의 MSRV를 만족한다고 추정하지 않는다.
- 성능은 처리·전송·화면과 전체 subtree 비용을 나누는 측정 계약을 정한다.
  현재 terminal의 수치/host 한계와 새로운 앱 전체 예산을 구별하며, 이 계약 단계에서
  측정하지 않은 성능 향상이나 제품 동등성을 보고하지 않는다.

## Scope Boundary

- In: 첫 Rust 업무 범위·package/adapter ownership·호출/전송 topology·runtime 유지·
  호환/거부/복귀·검증 입력 및 후속 product 의존성의 계약.
- Out: 실제 포팅/DB migration·전체 Python 제거·새 UI framework/모델/VT engine·
  앱 설치/서비스 교체·성능 benchmark·개인 corpus 이용·중단 기능 복귀·배포/publication.

## Surface Lanes

| Lane | 참고 path roots | 책임·의존성 | 평가 |
| --- | --- | --- | --- |
| contract | 이 Feature, parent PRD, architecture/terminal/settings/storage owners | 전환 범위·상태/형식·ownership·호환/복귀와 후속 계약 | contract |
| backend/integration | src/localbrain/terminal, app, cli.py, desktop.py; desktop/src-tauri | 실제 현재 호출 경로와 얇은 host adapter의 목표 경계. 이 단계에서는 코드 불변 | contract |
| infra/docs | pyproject.toml, desktop manifests/locks/backend.spec, scripts/build-desktop.py | 실제 runtime/빌드 제약과 후속 artifact 검증·owner 갱신 목록 | contract |

## Contract Surfaces

설정/DB writer·runtime identity·manager wire·HTTP/WS·CLI/stdout/stderr/exit status·
app per-launch admission·artifact/version compatibility. Terminal의 세부 독립 수명은
FEAT-0168, 앱 접근/그룹/명령 상태의 별도 foundation은 PRD-0030에서 소유한다.

## Entry, Exit And State Expectations

- Entry: 사람이 위 권장 경계와 이 Feature의 계약 결과를 승인한 뒤 Spec에서 구체화.
- Default/empty: 필요한 구성요소·모델·service가 없음을 명시. 조회/화면 진입은 설치/기동하지 않음.
- Error: 미지원 버전·owner/설정/프로세스 미확인은 실패/미확인으로 남김. 새 초기화·성공값으로 대체하지 않음.
- Exit: 후속 Spec이 first slice·호출 방식·writer·거부/복귀를 다시 선택하지 않아도 되는 계약.
  미해결 선택은 parent/Feature 검토로 반환하며 product에 넘기지 않음.

## Dependencies

상위 제품 방향과 구체적 권장 경계 승인은 `2026-11-12` 지시로 충족됐다.
현재 owner/source가 입력이다. FEAT-0168은 별도 후속 foundation이며
이 Feature가 앱 수명/인증/그룹/상태 계약을 대신 완료하지 않는다.

## Likely Affected Surfaces

첫 계약은 해당 Spec과 전환 계약 owner에 남긴다. 실제 구현 시 architecture·
설치/storage·terminal·desktop/settings·availability·Docs·build/CLI owner를
동시에 정합화할 목록을 포함한다. 현재 Python/웹 전용 정책을 완료된 Rust/앱으로 쓰지 않는다.

## Pass Or Fail Checks

1. 첫 slice와 전체 후속 기능 목록·제외/중단 상태 및 각 writer/adapter owner가 명확하다.
2. 웹·앱·CLI의 대표 정상/실패 호출을 따라가면 공통 Rust 업무 owner가 하나이며,
   core에 Tauri 의존성이 없고 다른 기능은 기존 계약을 유지한다.
3. lock/revision 충돌·구버전 manager·helper 실패·생성 응답 손실·취소·새 generation의
   결과와 복귀 조건을 합성 사례로 구분한다. 개인 자료·실제 실행은 조작하지 않는다.
4. 공식 버전 근거/actual lock 및 계약의 미검증·추후 성능/제품 수락 범위가 명시된다.
5. OP-01~05/08의 first-slice 결정이 잠기고 후속 구현자가 새 product 선택을 할 필요가 없다.
   unresolved가 남으면 계약 FAIL/계획 반환이며 통과로 넘기지 않는다.

## Regression Surfaces

기존 Session/Usage/Context/검색·동기화·설정과 private storage·CLI, terminal 폰트/IME·
lease/checkpoint/흐름 제어·32 record/4 pane·Hide/Open/×·no replay·업데이트 종료 확인.
기존 웹 평가를 실제 앱·전체 Rust 수락으로 승격하지 않는다.

## Harness Trace

- Active spec: [SPEC-0167](../spec/spec-0167-rust-core-and-host-contract.md)
- Active run: [RUN-247](../run/run-20261112-247-rust-core-and-host-contract.md)
- Execution profile: foundation-contract
- Latest evaluator report: [EVAL-0163](../evaluation/eval-0163-rust-core-and-host-contract.md), PASS / complete for the bounded contract
- Latest fix note: none

## Continuity Notes

- `2026-11-12` 계약 완료: Run247/Eval0163에서 core/host·settings writer·wire/stream·
  호환/복귀·의존성/측정 계약을 확정했다. [계약 owner](../project/rust-core-and-host-contract.md)와
  [전환 계획](../refactoring/refactor-0006-rust-core-transition.md)이 후속 입력이다.
  기술적 계약 PASS이며 실제 Rust 포팅/앱/성능 PASS나 전체 PRD 완료는 아니다.

- `2026-11-12` 경계 승인: 사용자가 생성한 두 Feature의 완료를 명시적으로 지시했다.
  권장 경계를 승인하고 Run247에서 계약 산출물·검증을 진행한다. 포팅/앱 설치/서비스
  제어는 이 Feature의 제외 범위이며 이번 승인으로 자동 추가하지 않는다.

- `2026-11-12`: 사용자의 진행 지시 후 parent의 공통 코어 후보 C-01을 첫 검토 단위로
  구체화했다. 권장 first slice/runtime/host 선택은 이 Feature에서 검토하며 자동 승인하지
  않았다. Spec·코드·Run·사용자 runtime·배포는 시작하지 않았다.
