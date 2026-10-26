# SPEC-0138: 로컬 저장소 확인과 복구

## Metadata

- Status: `approved`
- Parent Feature: [FEAT-0138](../feature/feat-0138-local-storage-recovery.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261018-176-local-storage-recovery](../run/run-20261018-176-local-storage-recovery.md)
- Execution Profile: `fullstack-product`
- Updated: `2026-10-18`

## Implementation Boundary

The [common settings and desktop contract](../../policies/project/desktop-app-and-settings.md)
owns field precedence, source identity, search admission, locking, local recovery and
edition boundaries. This specification applies those rules to this Feature.
The [test-app guide](../../policies/project/standalone-test-app-guide.md) owns delivery and usage.

## Acceptance Mapping

- AC1: 저장 위치·용량과 백업 포함/제외 표시.
- AC2: SQLite 일관된 백업, 같은 Mac 복원 검증·실패 복구, 명시적 재시작.
- AC3: 소유·비활성 확인한 파생 캐시만 정리; 원본·공유 모델 삭제 없음.

## Failure And Regression

Preserve originals, source/session IDs, frozen Usage attribution, unknown settings and
unrelated development features. Errors keep entered values and provide retry/recovery.
No implicit model download, external upload, paid signing or data relocation.

## Execution And Evidence

Primary-agent implementation with synthetic unit/integration/browser checks and an
independently launched bundled runtime. Record code, browser, packaged-app and teammate
Mac evidence separately. A build alone does not establish successful execution.
The active Run records observations and unresolved checks; do not infer a pass from this specification.
