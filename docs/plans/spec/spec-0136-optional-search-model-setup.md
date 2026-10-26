# SPEC-0136: 선택형 검색 모델 설치

## Metadata

- Status: `approved`
- Parent Feature: [FEAT-0136](../feature/feat-0136-optional-search-model-setup.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261018-174-optional-search-model-setup](../run/run-20261018-174-optional-search-model-setup.md)
- Execution Profile: `fullstack-product`
- Updated: `2026-10-18`

## Implementation Boundary

The [common settings and desktop contract](../../policies/project/desktop-app-and-settings.md)
owns field precedence, source identity, search admission, locking, local recovery and
edition boundaries. This specification applies those rules to this Feature.
The [test-app guide](../../policies/project/standalone-test-app-guide.md) owns delivery and usage.

## Acceptance Mapping

- AC1: 공개 embedding 자산만 명시적 설치, 기존 pinned 검증/캐시 재사용.
- AC2: 설치·검증·인덱싱·준비·실패·취소/재시도/재개 상태 구분.
- AC3: 앱 종료 시 작업 정리, 설정 창 닫기는 진행 유지, 기본 검색 계속 사용.

## Failure And Regression

Preserve originals, source/session IDs, frozen Usage attribution, unknown settings and
unrelated development features. Errors keep entered values and provide retry/recovery.
No implicit model download, external upload, paid signing or data relocation.

## Execution And Evidence

Primary-agent implementation with synthetic unit/integration/browser checks and an
independently launched bundled runtime. Record code, browser, packaged-app and teammate
Mac evidence separately. A build alone does not establish successful execution.
The active Run records observations and unresolved checks; do not infer a pass from this specification.
