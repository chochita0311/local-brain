# SPEC-0131: Tauri 독립 실행 앱

## Metadata

- Status: `approved`
- Parent Feature: [FEAT-0131](../feature/feat-0131-standalone-macos-runtime.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261018-169-standalone-macos-runtime](../run/run-20261018-169-standalone-macos-runtime.md)
- Execution Profile: `fullstack-product`
- Updated: `2026-10-18`

## Implementation Boundary

The [common settings and desktop contract](../../policies/project/desktop-app-and-settings.md)
owns field precedence, source identity, search admission, locking, local recovery and
edition boundaries. This specification applies those rules to this Feature.
The [test-app guide](../../policies/project/standalone-test-app-guide.md) owns delivery and usage.

## Acceptance Mapping

- AC1: Apple Silicon .app에 Python과 검색 의존성을 포함.
- AC2: loopback 임의 포트·실행별 인증·준비/오류·단일 인스턴스·창 복원·정상 종료.
- AC3: 설치형 기능은 실행부에서 고정하며 제외 메뉴/API/복구 작업 차단.

## Failure And Regression

Preserve originals, source/session IDs, frozen Usage attribution, unknown settings and
unrelated development features. Errors keep entered values and provide retry/recovery.
No implicit model download, external upload, paid signing or data relocation.

## Execution And Evidence

Primary-agent implementation with synthetic unit/integration/browser checks and an
independently launched bundled runtime. Record code, browser, packaged-app and teammate
Mac evidence separately. A build alone does not establish successful execution.
The active Run records observations and unresolved checks; do not infer a pass from this specification.
