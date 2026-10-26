# SPEC-0135: 모델 없는 통합 검색

## Metadata

- Status: `approved`
- Parent Feature: [FEAT-0135](../feature/feat-0135-model-optional-keyword-search.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261018-173-model-optional-keyword-search](../run/run-20261018-173-model-optional-keyword-search.md)
- Execution Profile: `fullstack-product`
- Updated: `2026-10-18`

## Implementation Boundary

The [common settings and desktop contract](../../policies/project/desktop-app-and-settings.md)
owns field precedence, source identity, search admission, locking, local recovery and
edition boundaries. This specification applies those rules to this Feature.
The [test-app guide](../../policies/project/standalone-test-app-guide.md) owns delivery and usage.

## Acceptance Mapping

- AC1: 공유 검색 입력에서 기본 키워드/AI 모드 명시적 선택.
- AC2: 세션/Context 허용 범위와 안전한 원문·복귀 동작 유지.
- AC3: 미설치·오류 때 기본 검색 가능; 정상 AI 0건에서 자동 전환 없음.

## Failure And Regression

Preserve originals, source/session IDs, frozen Usage attribution, unknown settings and
unrelated development features. Errors keep entered values and provide retry/recovery.
No implicit model download, external upload, paid signing or data relocation.

## Execution And Evidence

Primary-agent implementation with synthetic unit/integration/browser checks and an
independently launched bundled runtime. Record code, browser, packaged-app and teammate
Mac evidence separately. A build alone does not establish successful execution.
The active Run records observations and unresolved checks; do not infer a pass from this specification.
